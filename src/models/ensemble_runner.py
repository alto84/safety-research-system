"""
Biomarker scoring ensemble runner.

Runs all applicable clinical scoring models against a single patient's data
and produces a layered, combined risk assessment.  The layering reflects
data availability:

    Layer 0 (Always Available -- standard clinical labs):
        EASIX, Modified EASIX, Pre-Modified EASIX, HScore, CAR-HEMATOTOX

    Layer 1 (When Cytokines / Early Biomarkers Available):
        Teachey 3-Cytokine Model, Hay Binary Classifier

Each model is instantiated and called via its ``.score(patient_data)``
method, where ``patient_data`` is a flat ``dict[str, Any]`` keyed by
standardised field names (e.g. ``ldh_u_per_l``, ``temperature_c``).

The runner determines which models can produce a result based on the
patient data keys, runs them, and aggregates the outputs into a single
``EnsembleResult`` with per-model breakdowns and a combined risk level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.models.biomarker_scores import (
    EASIX,
    CARHematotox,
    HayBinaryClassifier,
    HScore,
    ModifiedEASIX,
    PreModifiedEASIX,
    RiskLevel,
    ScoringResult,
    TeacheyCytokineModel,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LayerResult:
    """Aggregated result for one ensemble layer.

    Attributes:
        layer: Layer number (0 or 1).
        layer_name: Human-readable layer name.
        models_run: Names of models that were successfully scored.
        models_skipped: Names of models skipped (insufficient data).
        models_failed: Names of models that raised errors.
        scores: ScoringResult for each successful model.
        layer_risk_level: Maximum risk level across models in this layer
            (conservative aggregation).
        layer_confidence: Mean confidence of successful models (0.0-1.0).
    """

    layer: int
    layer_name: str
    models_run: list[str] = field(default_factory=list)
    models_skipped: list[str] = field(default_factory=list)
    models_failed: list[str] = field(default_factory=list)
    scores: list[ScoringResult] = field(default_factory=list)
    layer_risk_level: RiskLevel | None = None
    layer_confidence: float = 0.0


@dataclass
class EnsembleResult:
    """Combined output from the biomarker scoring ensemble.

    Attributes:
        patient_data_keys: The set of keys found in the input data.
        layers: Per-layer aggregated results.
        all_scores: Flat list of every valid ScoringResult.
        overall_risk_level: Highest risk level across all layers.
        overall_confidence: Mean confidence across all valid models.
        model_count_run: Total models that produced a valid score.
        model_count_skipped: Total models skipped (missing data).
        model_count_failed: Total models that errored.
        high_risk_models: Names of models that returned HIGH risk.
        warnings: Ensemble-level warnings (e.g. conflicting risk levels).
        timestamp: When the ensemble was run.
    """

    patient_data_keys: set[str]
    layers: list[LayerResult]
    all_scores: list[ScoringResult]
    overall_risk_level: RiskLevel | None
    overall_confidence: float
    model_count_run: int
    model_count_skipped: int
    model_count_failed: int
    high_risk_models: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def get_result(self, model_name: str) -> ScoringResult | None:
        """Look up a specific model's ScoringResult by name."""
        for s in self.all_scores:
            if s.model_name == model_name:
                return s
        return None

    @property
    def risk_summary(self) -> dict[str, str]:
        """Return ``{model_name: risk_level}`` for all valid models."""
        summary: dict[str, str] = {}
        for s in self.all_scores:
            if s.is_valid:
                rl = s.risk_level
                summary[s.model_name] = rl.value if rl is not None else "unknown"
        return summary


# ---------------------------------------------------------------------------
# Risk-level ordering utility
# ---------------------------------------------------------------------------

_RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
}


def _max_risk(levels: list[RiskLevel]) -> RiskLevel | None:
    """Return the highest risk level from a list, or None if empty."""
    if not levels:
        return None
    return max(levels, key=lambda rl: _RISK_ORDER.get(rl, 0))


# ---------------------------------------------------------------------------
# Ensemble runner
# ---------------------------------------------------------------------------

class BiomarkerEnsembleRunner:
    """Runs all applicable biomarker scoring models and combines results.

    The runner uses a two-layer architecture:

    **Layer 0 -- Standard Labs (Always Available)**
        These models use routine clinical chemistry, haematology, and
        acute-phase-reactant results that are available for every patient.

        - EASIX
        - Modified EASIX
        - Pre-Modified EASIX
        - HScore
        - CAR-HEMATOTOX

    **Layer 1 -- Cytokine Panel (When Available)**
        These models require specialised cytokine / chemokine assay results
        that may not be measured on all patients.

        - Teachey 3-Cytokine Model
        - Hay Binary Classifier

    Usage::

        runner = BiomarkerEnsembleRunner()
        result = runner.run({
            "ldh_u_per_l": 450,
            "creatinine_mg_dl": 1.2,
            "platelets_per_nl": 120,
            "ferritin_ng_ml": 3500,
            "temperature_c": 39.8,
            ...
        })
        print(result.overall_risk_level)
        print(result.risk_summary)
    """

    def __init__(self) -> None:
        """Instantiate all scoring model objects."""
        self._easix = EASIX()
        self._modified_easix = ModifiedEASIX()
        self._pre_modified_easix = PreModifiedEASIX()
        self._hscore = HScore()
        self._car_hematotox = CARHematotox()
        self._teachey = TeacheyCytokineModel()
        self._hay = HayBinaryClassifier()

    def run(self, patient_data: dict[str, Any]) -> EnsembleResult:
        """Run all applicable scoring models against patient data.

        Args:
            patient_data: Flat dict of patient laboratory values, vitals,
                and clinical observations.  Keys should match the documented
                field names in each model class's docstring (e.g.
                ``ldh_u_per_l``, ``temperature_c``, ``ferritin_ng_ml``).

        Returns:
            An EnsembleResult with per-model and per-layer breakdowns and
            an overall risk assessment.
        """
        data_keys = set(patient_data.keys())

        # ---- Layer 0: Always Available (standard clinical labs) ----
        layer0 = self._run_layer_0(patient_data)

        # ---- Layer 1: Cytokine Panel (when available) ----
        layer1 = self._run_layer_1(patient_data)

        layers = [layer0, layer1]

        # ---- Flat list of all valid scores ----
        all_scores: list[ScoringResult] = []
        for layer in layers:
            all_scores.extend(layer.scores)

        # ---- Aggregate overall risk ----
        all_risk_levels: list[RiskLevel] = []
        confidences: list[float] = []
        high_risk_models: list[str] = []

        for s in all_scores:
            if s.is_valid and s.risk_level is not None:
                all_risk_levels.append(s.risk_level)
                if s.risk_level == RiskLevel.HIGH:
                    high_risk_models.append(s.model_name)
            if s.is_valid:
                confidences.append(s.confidence)

        overall_risk = _max_risk(all_risk_levels)
        overall_confidence = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        total_run = sum(len(lr.models_run) for lr in layers)
        total_skipped = sum(len(lr.models_skipped) for lr in layers)
        total_failed = sum(len(lr.models_failed) for lr in layers)

        # ---- Ensemble-level warnings ----
        ensemble_warnings: list[str] = []

        if total_run == 0:
            ensemble_warnings.append(
                "No scoring models produced a valid result. Check input data."
            )

        # Risk discordance
        if all_risk_levels:
            unique_levels = set(all_risk_levels)
            if len(unique_levels) > 1 and RiskLevel.HIGH in unique_levels:
                low_models = [
                    s.model_name
                    for s in all_scores
                    if s.is_valid and s.risk_level == RiskLevel.LOW
                ]
                if low_models:
                    ensemble_warnings.append(
                        "Risk discordance: some models report HIGH while "
                        f"{', '.join(low_models)} report LOW. "
                        "Clinical review recommended."
                    )

        return EnsembleResult(
            patient_data_keys=data_keys,
            layers=layers,
            all_scores=all_scores,
            overall_risk_level=overall_risk,
            overall_confidence=round(overall_confidence, 3),
            model_count_run=total_run,
            model_count_skipped=total_skipped,
            model_count_failed=total_failed,
            high_risk_models=high_risk_models,
            warnings=ensemble_warnings,
        )

    # ------------------------------------------------------------------
    # Layer runners
    # ------------------------------------------------------------------

    def _run_layer_0(self, patient_data: dict[str, Any]) -> LayerResult:
        """Run Layer 0 models (standard labs, always attempted).

        Models: EASIX, Modified EASIX, Pre-Modified EASIX, HScore,
        CAR-HEMATOTOX.
        """
        layer = LayerResult(layer=0, layer_name="Standard Labs")

        models = [
            (self._easix, "EASIX"),
            (self._modified_easix, "Modified_EASIX"),
            (self._pre_modified_easix, "Pre_Modified_EASIX"),
            (self._hscore, "HScore"),
            (self._car_hematotox, "CAR_HEMATOTOX"),
        ]

        self._score_models(models, patient_data, layer)
        self._aggregate_layer(layer)
        return layer

    def _run_layer_1(self, patient_data: dict[str, Any]) -> LayerResult:
        """Run Layer 1 models (cytokine / early biomarker panel).

        Models: Teachey 3-Cytokine Model, Hay Binary Classifier.
        """
        layer = LayerResult(layer=1, layer_name="Cytokine Panel")

        models = [
            (self._teachey, "Teachey_Cytokine_3var"),
            (self._hay, "Hay_Binary_Classifier"),
        ]

        self._score_models(models, patient_data, layer)
        self._aggregate_layer(layer)
        return layer

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_models(
        models: list[tuple[Any, str]],
        patient_data: dict[str, Any],
        layer: LayerResult,
    ) -> None:
        """Score a list of models, categorising each as run/skipped/failed."""
        for model, name in models:
            try:
                result = model.score(patient_data)
            except Exception:
                logger.exception("Model %s raised an unexpected exception", name)
                layer.models_failed.append(name)
                continue

            if result.is_valid:
                layer.scores.append(result)
                layer.models_run.append(name)
            else:
                # Distinguish "missing data" (skip) from other errors (fail)
                is_missing_data = any(
                    "Missing required" in e or "Insufficient data" in e
                    for e in result.errors
                )
                if is_missing_data:
                    layer.models_skipped.append(name)
                elif result.errors:
                    layer.models_failed.append(name)
                else:
                    # Score is None but no errors -- treat as skipped
                    layer.models_skipped.append(name)

    @staticmethod
    def _aggregate_layer(layer: LayerResult) -> None:
        """Compute layer-level risk and confidence from individual scores."""
        if not layer.scores:
            layer.layer_risk_level = None
            layer.layer_confidence = 0.0
            return

        risk_levels: list[RiskLevel] = []
        confidences: list[float] = []

        for s in layer.scores:
            if s.is_valid and s.risk_level is not None:
                risk_levels.append(s.risk_level)
            if s.is_valid:
                confidences.append(s.confidence)

        layer.layer_risk_level = _max_risk(risk_levels)
        layer.layer_confidence = (
            round(sum(confidences) / len(confidences), 3)
            if confidences
            else 0.0
        )
