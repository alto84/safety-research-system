"""
Tests for PromptRouter — complexity scoring, model selection, and latency filtering.

The PromptRouter is responsible for directing clinical safety queries to the
optimal foundation model endpoint based on query complexity, domain fit,
latency constraints, and cost tier.
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

# Import shared fixtures and types via conftest
from tests.conftest import (
    SafetyQuery,
    ModelEndpoint,
    Urgency,
    CostTier,
)


# ---------------------------------------------------------------------------
# PromptRouter implementation under test (minimal reference implementation)
# ---------------------------------------------------------------------------

class PromptRouter:
    """Routes clinical safety queries to optimal model endpoints.

    This is the reference implementation used for testing. The production
    implementation lives in src/engine/orchestrator/router.py.
    """

    # Domain benchmark scores: (model_id -> domain -> score)
    # Higher is better. Updated from evaluation framework.
    DEFAULT_BENCHMARKS = {
        "claude-opus-4": {"crs": 0.92, "icans": 0.88, "hlh": 0.85},
        "gpt-5.2": {"crs": 0.87, "icans": 0.84, "hlh": 0.82},
        "gemini-3": {"crs": 0.83, "icans": 0.80, "hlh": 0.78},
    }

    # Complexity thresholds
    COMPLEXITY_KEYWORDS_HIGH = [
        "mechanistic", "pathway", "trans-signaling", "amplification",
        "intervention timing", "cascade", "grade 3+", "grade 4",
    ]
    COMPLEXITY_KEYWORDS_MEDIUM = [
        "trajectory", "kinetics", "longitudinal", "re-evaluate", "updated",
    ]

    def __init__(self, available_models: list[ModelEndpoint], benchmarks: dict = None):
        self.available_models = {m.model_id: m for m in available_models}
        self.benchmarks = benchmarks or self.DEFAULT_BENCHMARKS

    def assess_complexity(self, query: SafetyQuery) -> str:
        """Score query complexity as 'low', 'medium', or 'high'."""
        text_lower = query.query_text.lower()

        high_hits = sum(1 for kw in self.COMPLEXITY_KEYWORDS_HIGH if kw in text_lower)
        if high_hits >= 2 or query.cost_tier == CostTier.HIGH:
            return "high"

        med_hits = sum(1 for kw in self.COMPLEXITY_KEYWORDS_MEDIUM if kw in text_lower)
        if med_hits >= 1 or query.cost_tier == CostTier.MEDIUM:
            return "medium"

        return "low"

    def domain_benchmark(self, model_id: str, domain: str) -> float:
        """Return benchmark score for a model on a given domain."""
        return self.benchmarks.get(model_id, {}).get(domain, 0.0)

    def filter_by_latency(self, candidates: dict, max_ms: int) -> dict:
        """Remove models that cannot meet the latency requirement."""
        return {
            model_id: score
            for model_id, score in candidates.items()
            if self.available_models[model_id].max_latency_ms <= max_ms
        }

    def select_optimal(self, candidates: dict, complexity: str, cost_tier: CostTier) -> ModelEndpoint:
        """Select the best model from candidates given constraints."""
        if not candidates:
            raise ValueError("No candidate models available after filtering.")

        if complexity == "high":
            # Prefer highest domain score regardless of cost
            best_id = max(candidates, key=candidates.get)
        elif complexity == "low" and cost_tier == CostTier.LOW:
            # Prefer cheapest model that meets minimum quality
            min_quality = 0.75
            affordable = {
                mid: score for mid, score in candidates.items()
                if score >= min_quality
            }
            if affordable:
                best_id = min(
                    affordable,
                    key=lambda mid: self.available_models[mid].cost_per_1k_tokens,
                )
            else:
                best_id = max(candidates, key=candidates.get)
        else:
            # Medium: balance quality and cost
            best_id = max(candidates, key=candidates.get)

        return self.available_models[best_id]

    def route(self, query: SafetyQuery) -> ModelEndpoint:
        """Main routing entry point."""
        complexity = self.assess_complexity(query)

        domain_scores = {
            model_id: self.domain_benchmark(model_id, query.domain)
            for model_id in self.available_models
        }

        if query.urgency == Urgency.REALTIME:
            candidates = self.filter_by_latency(domain_scores, max_ms=10000)
        elif query.urgency == Urgency.NEAR_REALTIME:
            candidates = self.filter_by_latency(domain_scores, max_ms=15000)
        else:
            candidates = domain_scores

        return self.select_optimal(candidates, complexity, query.cost_tier)


# ===========================================================================
# Tests
# ===========================================================================

class TestComplexityScoring:
    """Tests for PromptRouter.assess_complexity."""

    def test_simple_screening_is_low_complexity(self, all_endpoints, simple_screening_query):
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(simple_screening_query) == "low"

    def test_mechanistic_query_is_high_complexity(self, all_endpoints, complex_mechanistic_query):
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(complex_mechanistic_query) == "high"

    def test_monitoring_update_is_medium_complexity(self, all_endpoints, realtime_monitoring_query):
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(realtime_monitoring_query) == "medium"

    def test_high_cost_tier_forces_high_complexity(self, all_endpoints):
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="Simple question",
            cost_tier=CostTier.HIGH,
        )
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(query) == "high"

    def test_multiple_high_keywords_trigger_high(self, all_endpoints):
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="Analyze the mechanistic pathway for Grade 3+ CRS cascade.",
            cost_tier=CostTier.LOW,
        )
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(query) == "high"

    def test_single_high_keyword_not_enough_for_high(self, all_endpoints):
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="What is the mechanistic basis?",
            cost_tier=CostTier.LOW,
        )
        router = PromptRouter(all_endpoints)
        # Only 1 high keyword + low cost tier -> not high
        assert router.assess_complexity(query) in ("low", "medium")

    def test_empty_query_text_is_low(self, all_endpoints):
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="",
            cost_tier=CostTier.LOW,
        )
        router = PromptRouter(all_endpoints)
        assert router.assess_complexity(query) == "low"


class TestDomainBenchmark:
    """Tests for domain benchmark lookup."""

    def test_known_model_known_domain(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        assert router.domain_benchmark("claude-opus-4", "crs") == 0.92

    def test_unknown_model_returns_zero(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        assert router.domain_benchmark("unknown-model", "crs") == 0.0

    def test_unknown_domain_returns_zero(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        assert router.domain_benchmark("claude-opus-4", "unknown_domain") == 0.0

    def test_claude_highest_for_crs(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        scores = {m.model_id: router.domain_benchmark(m.model_id, "crs") for m in all_endpoints}
        best = max(scores, key=scores.get)
        assert best == "claude-opus-4"


class TestLatencyFiltering:
    """Tests for latency-aware candidate filtering."""

    def test_realtime_filters_slow_models(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        domain_scores = {"claude-opus-4": 0.92, "gpt-5.2": 0.87, "gemini-3": 0.83}

        # Claude max_latency_ms=15000, exceeds 10000 threshold
        filtered = router.filter_by_latency(domain_scores, max_ms=10000)
        assert "claude-opus-4" not in filtered
        assert "gpt-5.2" in filtered
        assert "gemini-3" in filtered

    def test_batch_includes_all_models(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        domain_scores = {"claude-opus-4": 0.92, "gpt-5.2": 0.87, "gemini-3": 0.83}

        # Very high threshold includes everything
        filtered = router.filter_by_latency(domain_scores, max_ms=30000)
        assert len(filtered) == 3

    def test_very_tight_latency_may_exclude_all(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        domain_scores = {"claude-opus-4": 0.92, "gpt-5.2": 0.87, "gemini-3": 0.83}

        filtered = router.filter_by_latency(domain_scores, max_ms=1000)
        assert len(filtered) == 0


class TestModelSelection:
    """Tests for optimal model selection."""

    def test_high_complexity_selects_best_quality(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        candidates = {"claude-opus-4": 0.92, "gpt-5.2": 0.87, "gemini-3": 0.83}
        result = router.select_optimal(candidates, "high", CostTier.HIGH)
        assert result.model_id == "claude-opus-4"

    def test_low_complexity_low_cost_selects_cheapest_qualified(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        candidates = {"claude-opus-4": 0.92, "gpt-5.2": 0.87, "gemini-3": 0.83}
        result = router.select_optimal(candidates, "low", CostTier.LOW)
        # Gemini is cheapest (0.008/1k tokens) and score 0.83 > 0.75 threshold
        assert result.model_id == "gemini-3"

    def test_no_candidates_raises(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        with pytest.raises(ValueError, match="No candidate models"):
            router.select_optimal({}, "medium", CostTier.MEDIUM)

    def test_medium_complexity_selects_best_quality(self, all_endpoints):
        router = PromptRouter(all_endpoints)
        candidates = {"gpt-5.2": 0.87, "gemini-3": 0.83}
        result = router.select_optimal(candidates, "medium", CostTier.MEDIUM)
        assert result.model_id == "gpt-5.2"


class TestEndToEndRouting:
    """Integration-style tests for the full route() method."""

    def test_simple_batch_query_routes_to_cheapest(self, all_endpoints, simple_screening_query):
        router = PromptRouter(all_endpoints)
        result = router.route(simple_screening_query)
        assert result.model_id == "gemini-3"

    def test_complex_realtime_query_excludes_slow_models(self, all_endpoints, complex_mechanistic_query):
        router = PromptRouter(all_endpoints)
        result = router.route(complex_mechanistic_query)
        # Claude is filtered out (15000ms > 10000ms threshold)
        # GPT-5.2 is next best for CRS
        assert result.model_id == "gpt-5.2"

    def test_complex_batch_query_selects_claude(self, all_endpoints):
        """When latency is not a constraint, Claude should win on CRS domain score."""
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="Full mechanistic pathway analysis for Grade 3+ CRS cascade.",
            urgency=Urgency.BATCH,
            cost_tier=CostTier.HIGH,
        )
        router = PromptRouter(all_endpoints)
        result = router.route(query)
        assert result.model_id == "claude-opus-4"

    def test_single_model_always_selected(self, claude_endpoint):
        """With only one model available, it must always be selected."""
        router = PromptRouter([claude_endpoint])
        query = SafetyQuery(
            patient_id="TEST",
            domain="crs",
            query_text="Basic CRS screening.",
            urgency=Urgency.BATCH,
            cost_tier=CostTier.LOW,
        )
        result = router.route(query)
        assert result.model_id == "claude-opus-4"

    def test_hlh_domain_routing(self, all_endpoints):
        """Verify routing works for non-CRS domains."""
        query = SafetyQuery(
            patient_id="TEST",
            domain="hlh",
            query_text="Assess HLH risk based on ferritin trajectory.",
            urgency=Urgency.BATCH,
            cost_tier=CostTier.MEDIUM,
        )
        router = PromptRouter(all_endpoints)
        result = router.route(query)
        # Claude has highest HLH score (0.85)
        assert result.model_id == "claude-opus-4"
