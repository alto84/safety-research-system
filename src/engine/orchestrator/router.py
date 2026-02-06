"""
Prompt router for multi-model orchestration.

Routes patient safety queries to the optimal foundation model(s) based on
query complexity, clinical domain, latency requirements, and model capabilities.
Supports routing to multiple models for ensemble prediction.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model capability descriptors
# ---------------------------------------------------------------------------

class QueryComplexity(Enum):
    """Complexity classification of a safety prediction query."""

    SIMPLE = "simple"           # Single biomarker threshold check
    MODERATE = "moderate"       # Multi-biomarker pattern with temporal context
    COMPLEX = "complex"         # Multi-pathway reasoning with mechanistic validation
    EXPERT = "expert"           # Novel mechanism hypothesis generation


class ClinicalDomain(Enum):
    """Clinical domain of the query."""

    CYTOKINE_KINETICS = "cytokine_kinetics"
    NEUROTOXICITY = "neurotoxicity"
    HEMOPHAGOCYTIC = "hemophagocytic"
    COAGULOPATHY = "coagulopathy"
    GENERAL_SAFETY = "general_safety"


@dataclass(frozen=True)
class ModelCapability:
    """Describes a foundation model's capabilities and constraints.

    Attributes:
        model_id: Unique identifier for the model.
        provider: The model provider (e.g. ``'openai'``, ``'anthropic'``).
        max_complexity: Highest query complexity this model handles well.
        clinical_domains: Domains this model excels in.
        avg_latency_ms: Expected average latency in milliseconds.
        max_tokens: Maximum context window size.
        cost_per_1k_tokens: Cost in USD per 1000 tokens.
        supports_structured_output: Whether the model reliably outputs JSON.
        reliability_score: Historical reliability (0.0 - 1.0).
    """

    model_id: str
    provider: str
    max_complexity: QueryComplexity
    clinical_domains: frozenset[ClinicalDomain]
    avg_latency_ms: int
    max_tokens: int
    cost_per_1k_tokens: float
    supports_structured_output: bool = True
    reliability_score: float = 0.95


@dataclass
class RoutingDecision:
    """The router's decision about which models to invoke.

    Attributes:
        primary_model: The main model to use.
        ensemble_models: Additional models for ensemble (may be empty).
        complexity: Assessed query complexity.
        domain: Assessed clinical domain.
        rationale: Human-readable explanation of the routing decision.
        estimated_latency_ms: Expected total latency.
    """

    primary_model: ModelCapability
    ensemble_models: list[ModelCapability] = field(default_factory=list)
    complexity: QueryComplexity = QueryComplexity.MODERATE
    domain: ClinicalDomain = ClinicalDomain.GENERAL_SAFETY
    rationale: str = ""
    estimated_latency_ms: int = 0

    @property
    def all_models(self) -> list[ModelCapability]:
        """Return the primary model plus any ensemble models."""
        return [self.primary_model] + self.ensemble_models


@dataclass
class SafetyQuery:
    """A structured safety prediction query.

    Attributes:
        patient_id: The patient being analyzed.
        query_text: The natural-language query or structured request.
        biomarker_count: Number of biomarkers available.
        hours_since_infusion: Temporal context.
        requires_mechanistic_reasoning: Whether KG reasoning is needed.
        latency_budget_ms: Maximum acceptable latency.
        adverse_events: Which adverse events to predict.
        context: Additional structured context.
    """

    patient_id: str
    query_text: str
    biomarker_count: int = 0
    hours_since_infusion: float = 0.0
    requires_mechanistic_reasoning: bool = False
    latency_budget_ms: int = 5000
    adverse_events: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Model backend protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class ModelBackend(Protocol):
    """Protocol for a foundation model API backend.

    Implementations must provide async inference and health checking.
    """

    async def predict(
        self,
        prompt: str,
        model_id: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """Run inference against a model.

        Args:
            prompt: The formatted prompt.
            model_id: Which model to invoke.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.

        Returns:
            Raw model response dict.
        """
        ...

    async def health_check(self, model_id: str) -> bool:
        """Check if a model endpoint is healthy.

        Args:
            model_id: The model to check.

        Returns:
            True if healthy and accepting requests.
        """
        ...


# ---------------------------------------------------------------------------
# PromptRouter
# ---------------------------------------------------------------------------

class PromptRouter:
    """Routes safety queries to optimal foundation models.

    The routing algorithm considers:
        1. Query complexity (more complex -> more capable model)
        2. Clinical domain (specialized models for neuro, HLH, etc.)
        3. Latency budget (fast models for real-time monitoring)
        4. Cost optimization (cheaper models for simple queries)
        5. Reliability (prefer models with high historical reliability)
        6. Ensemble value (route to multiple models when disagreement is likely)

    Usage::

        router = PromptRouter()
        router.register_model(gpt4_capability)
        router.register_model(claude_capability)
        decision = router.route(query)
    """

    # Complexity ordering for comparison
    _COMPLEXITY_ORDER = {
        QueryComplexity.SIMPLE: 0,
        QueryComplexity.MODERATE: 1,
        QueryComplexity.COMPLEX: 2,
        QueryComplexity.EXPERT: 3,
    }

    def __init__(
        self,
        ensemble_threshold: QueryComplexity = QueryComplexity.COMPLEX,
        max_ensemble_size: int = 3,
    ) -> None:
        """Initialize the prompt router.

        Args:
            ensemble_threshold: Minimum complexity level that triggers
                multi-model ensemble routing.
            max_ensemble_size: Maximum number of models in an ensemble.
        """
        self._models: dict[str, ModelCapability] = {}
        self._ensemble_threshold = ensemble_threshold
        self._max_ensemble_size = max_ensemble_size
        self._model_health: dict[str, bool] = {}

    def register_model(self, capability: ModelCapability) -> None:
        """Register a model's capabilities with the router.

        Args:
            capability: The ModelCapability descriptor.
        """
        self._models[capability.model_id] = capability
        self._model_health[capability.model_id] = True
        logger.info(
            "Registered model '%s' (provider=%s, complexity=%s, latency=%dms)",
            capability.model_id, capability.provider,
            capability.max_complexity.value, capability.avg_latency_ms,
        )

    def update_model_health(self, model_id: str, healthy: bool) -> None:
        """Update the health status of a model.

        Args:
            model_id: The model to update.
            healthy: Whether the model is healthy.
        """
        self._model_health[model_id] = healthy

    def route(self, query: SafetyQuery) -> RoutingDecision:
        """Route a safety query to the optimal model(s).

        Args:
            query: The structured safety query.

        Returns:
            A RoutingDecision specifying which models to invoke.

        Raises:
            RuntimeError: If no eligible models are available.
        """
        complexity = self._assess_complexity(query)
        domain = self._assess_domain(query)

        # Filter to eligible models (healthy, capable, within latency budget)
        eligible = self._filter_eligible(query, complexity)

        if not eligible:
            raise RuntimeError(
                f"No eligible models for query (complexity={complexity.value}, "
                f"domain={domain.value}, latency_budget={query.latency_budget_ms}ms)"
            )

        # Score and rank eligible models
        ranked = self._rank_models(eligible, complexity, domain, query)

        primary = ranked[0]
        ensemble_models: list[ModelCapability] = []

        # Determine if ensemble is warranted
        should_ensemble = (
            self._COMPLEXITY_ORDER[complexity]
            >= self._COMPLEXITY_ORDER[self._ensemble_threshold]
        )

        if should_ensemble and len(ranked) > 1:
            # Select diverse ensemble members (different providers preferred)
            used_providers = {primary.provider}
            for model in ranked[1:]:
                if len(ensemble_models) >= self._max_ensemble_size - 1:
                    break
                # Prefer diversity; accept same provider if no alternative
                if model.provider not in used_providers or len(ranked) <= 2:
                    ensemble_models.append(model)
                    used_providers.add(model.provider)

        # Estimate total latency
        if ensemble_models:
            # Parallel execution: latency = max of all models
            estimated_latency = max(
                m.avg_latency_ms for m in [primary] + ensemble_models
            )
        else:
            estimated_latency = primary.avg_latency_ms

        rationale = self._build_rationale(
            primary, ensemble_models, complexity, domain, query,
        )

        decision = RoutingDecision(
            primary_model=primary,
            ensemble_models=ensemble_models,
            complexity=complexity,
            domain=domain,
            rationale=rationale,
            estimated_latency_ms=estimated_latency,
        )

        logger.info(
            "Routed query for patient %s: primary=%s, ensemble=%s, complexity=%s",
            query.patient_id, primary.model_id,
            [m.model_id for m in ensemble_models], complexity.value,
        )

        return decision

    # ------------------------------------------------------------------
    # Complexity and domain assessment
    # ------------------------------------------------------------------

    def _assess_complexity(self, query: SafetyQuery) -> QueryComplexity:
        """Assess the complexity of a safety query.

        Heuristics:
            - Few biomarkers + no mechanistic reasoning = SIMPLE
            - Multiple biomarkers + temporal context = MODERATE
            - Mechanistic reasoning required = COMPLEX
            - Novel hypothesis generation = EXPERT
        """
        if query.requires_mechanistic_reasoning:
            if "hypothesis" in query.query_text.lower() or "novel" in query.query_text.lower():
                return QueryComplexity.EXPERT
            return QueryComplexity.COMPLEX

        if query.biomarker_count >= 5 and query.hours_since_infusion > 0:
            return QueryComplexity.MODERATE

        if query.biomarker_count <= 2:
            return QueryComplexity.SIMPLE

        return QueryComplexity.MODERATE

    def _assess_domain(self, query: SafetyQuery) -> ClinicalDomain:
        """Assess which clinical domain a query falls into."""
        ae_set = set(query.adverse_events)

        if "ICANS" in ae_set or "icans" in query.query_text.lower():
            return ClinicalDomain.NEUROTOXICITY
        if "HLH" in ae_set or "hlh" in query.query_text.lower():
            return ClinicalDomain.HEMOPHAGOCYTIC
        if "coagulopathy" in query.query_text.lower() or "dic" in query.query_text.lower():
            return ClinicalDomain.COAGULOPATHY
        if "CRS" in ae_set or "cytokine" in query.query_text.lower():
            return ClinicalDomain.CYTOKINE_KINETICS

        return ClinicalDomain.GENERAL_SAFETY

    # ------------------------------------------------------------------
    # Model filtering and ranking
    # ------------------------------------------------------------------

    def _filter_eligible(
        self,
        query: SafetyQuery,
        complexity: QueryComplexity,
    ) -> list[ModelCapability]:
        """Filter models to those eligible for this query."""
        eligible: list[ModelCapability] = []
        for model_id, model in self._models.items():
            # Must be healthy
            if not self._model_health.get(model_id, False):
                continue
            # Must handle the complexity level
            if self._COMPLEXITY_ORDER[model.max_complexity] < self._COMPLEXITY_ORDER[complexity]:
                continue
            # Must fit latency budget (with 20% margin)
            if model.avg_latency_ms > query.latency_budget_ms * 1.2:
                continue
            eligible.append(model)
        return eligible

    def _rank_models(
        self,
        models: list[ModelCapability],
        complexity: QueryComplexity,
        domain: ClinicalDomain,
        query: SafetyQuery,
    ) -> list[ModelCapability]:
        """Rank eligible models by suitability score.

        Scoring factors:
            - Domain match bonus (+0.3 if model excels in the query domain)
            - Reliability score (weighted 0.25)
            - Cost efficiency (weighted 0.15, inverted for cheaper = better)
            - Latency headroom (weighted 0.10)
            - Structured output support (weighted 0.20 for complex queries)
        """
        def _score(model: ModelCapability) -> float:
            score = 0.0

            # Domain match
            if domain in model.clinical_domains:
                score += 0.30

            # Reliability
            score += model.reliability_score * 0.25

            # Cost efficiency (lower cost = higher score, normalized)
            max_cost = max(m.cost_per_1k_tokens for m in models) or 1.0
            cost_efficiency = 1.0 - (model.cost_per_1k_tokens / max_cost)
            score += cost_efficiency * 0.15

            # Latency headroom
            latency_ratio = model.avg_latency_ms / max(query.latency_budget_ms, 1)
            latency_score = max(0.0, 1.0 - latency_ratio)
            score += latency_score * 0.10

            # Structured output support (important for complex queries)
            if model.supports_structured_output:
                importance = 0.20 if self._COMPLEXITY_ORDER[complexity] >= 2 else 0.10
                score += importance

            return score

        return sorted(models, key=_score, reverse=True)

    def _build_rationale(
        self,
        primary: ModelCapability,
        ensemble: list[ModelCapability],
        complexity: QueryComplexity,
        domain: ClinicalDomain,
        query: SafetyQuery,
    ) -> str:
        """Build a human-readable explanation of the routing decision."""
        parts = [
            f"Query complexity: {complexity.value}",
            f"Clinical domain: {domain.value}",
            f"Primary model: {primary.model_id} ({primary.provider})",
        ]
        if ensemble:
            parts.append(
                f"Ensemble models: {', '.join(m.model_id for m in ensemble)}"
            )
            parts.append(
                f"Ensemble triggered by complexity >= {self._ensemble_threshold.value}"
            )
        if domain in primary.clinical_domains:
            parts.append(f"{primary.model_id} has domain expertise in {domain.value}")

        return "; ".join(parts)

    def format_prompt(
        self,
        query: SafetyQuery,
        model: ModelCapability,
        system_context: str = "",
    ) -> str:
        """Format a safety query into a model-specific prompt.

        Args:
            query: The safety query to format.
            model: The target model (for format preferences).
            system_context: Additional system-level context.

        Returns:
            The formatted prompt string.
        """
        sections = []

        if system_context:
            sections.append(f"SYSTEM CONTEXT:\n{system_context}")

        sections.append(
            "TASK: Predict adverse event risk for a cell therapy patient. "
            "Return a structured JSON response with risk_score (0.0-1.0), "
            "confidence (0.0-1.0), adverse_event, reasoning, and key_drivers."
        )

        sections.append(f"PATIENT ID: {query.patient_id}")
        sections.append(f"HOURS SINCE INFUSION: {query.hours_since_infusion}")
        sections.append(f"ADVERSE EVENTS TO ASSESS: {', '.join(query.adverse_events)}")

        if query.context:
            context_lines = [f"  {k}: {v}" for k, v in query.context.items()]
            sections.append("CLINICAL CONTEXT:\n" + "\n".join(context_lines))

        sections.append(f"QUERY: {query.query_text}")

        return "\n\n".join(sections)
