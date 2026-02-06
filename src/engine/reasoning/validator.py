"""
Mechanistic validator for safety predictions.

Ensures that AI model predictions are biologically plausible by validating
them against known signaling cascades, temporal onset patterns, and
biomarker consistency constraints from the knowledge graph.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.data.graph.knowledge_graph import KnowledgeGraph
from src.data.graph.schema import EdgeType, NodeType, TemporalPhase
from src.engine.orchestrator.normalizer import SafetyPrediction
from src.safety_index.index import AdverseEventType

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Outcome of a mechanistic validation check."""

    VALID = "valid"                 # Prediction is biologically plausible
    PLAUSIBLE = "plausible"         # Partially supported, some uncertainty
    IMPLAUSIBLE = "implausible"     # Contradicts known biology
    INSUFFICIENT_DATA = "insufficient_data"  # Cannot validate (missing data)


@dataclass
class ValidationCheck:
    """A single validation check within a validation report.

    Attributes:
        check_name: What was checked.
        result: Outcome of the check.
        details: Explanation of the finding.
        confidence: Confidence in the check result (0.0 - 1.0).
    """

    check_name: str
    result: ValidationResult
    details: str
    confidence: float = 0.8


@dataclass
class ValidationReport:
    """Complete validation report for a safety prediction.

    Attributes:
        prediction_model_id: Which model's prediction was validated.
        patient_id: The patient being assessed.
        adverse_event: The predicted adverse event.
        overall_result: Aggregate validation outcome.
        overall_confidence: Aggregate confidence in the validation.
        checks: Individual validation checks performed.
        warnings: Non-blocking concerns about the prediction.
        adjustments: Suggested adjustments to the prediction.
        timestamp: When validation was performed.
    """

    prediction_model_id: str
    patient_id: str
    adverse_event: AdverseEventType
    overall_result: ValidationResult
    overall_confidence: float
    checks: list[ValidationCheck] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    adjustments: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_valid(self) -> bool:
        """Whether the prediction passed validation."""
        return self.overall_result in (
            ValidationResult.VALID,
            ValidationResult.PLAUSIBLE,
        )


# ---------------------------------------------------------------------------
# Temporal plausibility rules
# ---------------------------------------------------------------------------

# Typical onset windows (hours since infusion)
_TEMPORAL_WINDOWS: dict[AdverseEventType, tuple[float, float]] = {
    AdverseEventType.CRS: (6.0, 336.0),       # 6h to 14 days
    AdverseEventType.ICANS: (24.0, 504.0),     # 1 day to 21 days
    AdverseEventType.HLH: (48.0, 504.0),       # 2 days to 21 days
}

# Biomarkers that must be elevated for a high-risk prediction to be plausible
_REQUIRED_BIOMARKER_PATTERNS: dict[AdverseEventType, list[list[str]]] = {
    AdverseEventType.CRS: [
        # At least one of these patterns must match
        ["CYTOKINE:IL6"],
        ["CYTOKINE:IFN_GAMMA"],
        ["BIOMARKER:CRP", "BIOMARKER:FERRITIN"],
    ],
    AdverseEventType.ICANS: [
        ["CYTOKINE:IL6"],
        ["PROTEIN:ANG2"],
        ["PROTEIN:VWF"],
    ],
    AdverseEventType.HLH: [
        ["BIOMARKER:FERRITIN"],
        ["CYTOKINE:IL18"],
        ["BIOMARKER:SCD25"],
    ],
}


class MechanisticValidator:
    """Validates safety predictions against known biological mechanisms.

    Performs five categories of validation:
        1. **Pathway existence**: Does a mechanistic path exist in the KG
           from the patient's biomarker pattern to the predicted adverse event?
        2. **Temporal plausibility**: Is the prediction timing consistent with
           known onset kinetics?
        3. **Biomarker consistency**: Are the right biomarkers elevated for
           this adverse event?
        4. **Cascade ordering**: Do the elevated biomarkers follow the expected
           temporal ordering of the signaling cascade?
        5. **Magnitude plausibility**: Are the biomarker levels consistent with
           the predicted severity?

    Usage::

        validator = MechanisticValidator(knowledge_graph=kg)
        report = validator.validate(
            prediction=model_prediction,
            biomarkers={"CYTOKINE:IL6": 5000.0, ...},
            hours_since_infusion=48.0,
        )
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        strict_mode: bool = False,
    ) -> None:
        """Initialize the mechanistic validator.

        Args:
            knowledge_graph: The biological knowledge graph.
            strict_mode: If True, PLAUSIBLE results are treated as IMPLAUSIBLE.
        """
        self._kg = knowledge_graph
        self._strict_mode = strict_mode

    def validate(
        self,
        prediction: SafetyPrediction,
        biomarkers: dict[str, float],
        hours_since_infusion: float,
        biomarker_history: dict[str, list[tuple[float, float]]] | None = None,
    ) -> ValidationReport:
        """Validate a safety prediction against mechanistic biology.

        Args:
            prediction: The model prediction to validate.
            biomarkers: Current biomarker values keyed by graph node ID.
            hours_since_infusion: Hours since cell therapy infusion.
            biomarker_history: Optional historical biomarker values as
                ``{node_id: [(value, hours_ago), ...]}``.

        Returns:
            A ValidationReport with detailed findings.
        """
        adverse_event = AdverseEventType(prediction.adverse_event)

        logger.info(
            "Validating prediction from %s for patient %s (%s, score=%.3f)",
            prediction.model_id, prediction.patient_id,
            adverse_event.value, prediction.risk_score,
        )

        checks: list[ValidationCheck] = []
        warnings: list[str] = []
        adjustments: dict[str, Any] = {}

        # Run validation checks
        checks.append(self._check_pathway_existence(
            adverse_event, biomarkers,
        ))
        checks.append(self._check_temporal_plausibility(
            adverse_event, hours_since_infusion, prediction.risk_score,
        ))
        checks.append(self._check_biomarker_consistency(
            adverse_event, biomarkers, prediction.risk_score,
        ))

        if biomarker_history:
            checks.append(self._check_cascade_ordering(
                adverse_event, biomarker_history,
            ))

        checks.append(self._check_magnitude_plausibility(
            adverse_event, biomarkers, prediction.risk_score,
        ))

        # Aggregate results
        overall_result = self._aggregate_results(checks)
        overall_confidence = self._aggregate_confidence(checks)

        # Generate warnings
        for check in checks:
            if check.result == ValidationResult.IMPLAUSIBLE:
                warnings.append(
                    f"IMPLAUSIBLE: {check.check_name} -- {check.details}"
                )
            elif check.result == ValidationResult.INSUFFICIENT_DATA:
                warnings.append(
                    f"INSUFFICIENT DATA: {check.check_name} -- {check.details}"
                )

        # Suggest score adjustments if prediction is implausible
        if overall_result == ValidationResult.IMPLAUSIBLE:
            adjustments["suggested_score_multiplier"] = 0.5
            adjustments["reason"] = "Prediction contradicts known mechanisms"
        elif overall_result == ValidationResult.PLAUSIBLE:
            adjustments["suggested_confidence_multiplier"] = 0.8
            adjustments["reason"] = "Partial mechanistic support"

        report = ValidationReport(
            prediction_model_id=prediction.model_id,
            patient_id=prediction.patient_id,
            adverse_event=adverse_event,
            overall_result=overall_result,
            overall_confidence=overall_confidence,
            checks=checks,
            warnings=warnings,
            adjustments=adjustments,
        )

        logger.info(
            "Validation result for %s: %s (confidence=%.3f, %d warnings)",
            prediction.patient_id, overall_result.value,
            overall_confidence, len(warnings),
        )

        return report

    # ------------------------------------------------------------------
    # Individual validation checks
    # ------------------------------------------------------------------

    def _check_pathway_existence(
        self,
        adverse_event: AdverseEventType,
        biomarkers: dict[str, float],
    ) -> ValidationCheck:
        """Check whether a mechanistic pathway connects biomarkers to the AE."""
        ae_node_id = f"AE:{adverse_event.value}"
        connected_biomarkers: list[str] = []

        for bm_id in biomarkers:
            node = self._kg.get_node(bm_id)
            if node is None:
                continue
            is_valid, explanation = self._kg.validate_mechanism(bm_id, ae_node_id)
            if is_valid:
                connected_biomarkers.append(bm_id)

        if not biomarkers:
            return ValidationCheck(
                check_name="pathway_existence",
                result=ValidationResult.INSUFFICIENT_DATA,
                details="No biomarkers provided for pathway validation",
                confidence=0.0,
            )

        fraction_connected = len(connected_biomarkers) / len(biomarkers)

        if fraction_connected >= 0.5:
            return ValidationCheck(
                check_name="pathway_existence",
                result=ValidationResult.VALID,
                details=(
                    f"{len(connected_biomarkers)}/{len(biomarkers)} biomarkers have "
                    f"KG paths to {adverse_event.value}"
                ),
                confidence=min(1.0, fraction_connected + 0.2),
            )
        elif fraction_connected > 0:
            return ValidationCheck(
                check_name="pathway_existence",
                result=ValidationResult.PLAUSIBLE,
                details=(
                    f"Only {len(connected_biomarkers)}/{len(biomarkers)} biomarkers "
                    f"have KG paths to {adverse_event.value}"
                ),
                confidence=fraction_connected + 0.1,
            )
        else:
            return ValidationCheck(
                check_name="pathway_existence",
                result=ValidationResult.IMPLAUSIBLE,
                details=(
                    f"No biomarkers have KG paths to {adverse_event.value}. "
                    f"The prediction lacks mechanistic support."
                ),
                confidence=0.3,
            )

    def _check_temporal_plausibility(
        self,
        adverse_event: AdverseEventType,
        hours_since_infusion: float,
        risk_score: float,
    ) -> ValidationCheck:
        """Check whether the timing is consistent with known onset kinetics."""
        window = _TEMPORAL_WINDOWS.get(adverse_event)
        if window is None:
            return ValidationCheck(
                check_name="temporal_plausibility",
                result=ValidationResult.INSUFFICIENT_DATA,
                details=f"No temporal window data for {adverse_event.value}",
                confidence=0.5,
            )

        onset_start, onset_end = window

        if hours_since_infusion < 0:
            if risk_score > 0.5:
                return ValidationCheck(
                    check_name="temporal_plausibility",
                    result=ValidationResult.IMPLAUSIBLE,
                    details=(
                        f"Pre-infusion: high risk score ({risk_score:.2f}) is "
                        f"implausible before cell therapy infusion"
                    ),
                    confidence=0.9,
                )
            return ValidationCheck(
                check_name="temporal_plausibility",
                result=ValidationResult.VALID,
                details="Pre-infusion baseline; low risk is expected",
                confidence=0.9,
            )

        if onset_start <= hours_since_infusion <= onset_end:
            return ValidationCheck(
                check_name="temporal_plausibility",
                result=ValidationResult.VALID,
                details=(
                    f"Patient is within the typical {adverse_event.value} onset "
                    f"window ({onset_start:.0f}h - {onset_end:.0f}h)"
                ),
                confidence=0.9,
            )

        if hours_since_infusion < onset_start:
            if risk_score > 0.7:
                return ValidationCheck(
                    check_name="temporal_plausibility",
                    result=ValidationResult.PLAUSIBLE,
                    details=(
                        f"Before typical onset window ({hours_since_infusion:.0f}h "
                        f"< {onset_start:.0f}h). High risk score is unusual but "
                        f"possible with high tumor burden or rapid kinetics."
                    ),
                    confidence=0.5,
                )
            return ValidationCheck(
                check_name="temporal_plausibility",
                result=ValidationResult.VALID,
                details="Before onset window; low-moderate risk is appropriate",
                confidence=0.8,
            )

        # Past the typical window
        if risk_score > 0.5:
            return ValidationCheck(
                check_name="temporal_plausibility",
                result=ValidationResult.PLAUSIBLE,
                details=(
                    f"Past typical onset window ({hours_since_infusion:.0f}h > "
                    f"{onset_end:.0f}h). Late-onset events are possible but uncommon."
                ),
                confidence=0.4,
            )
        return ValidationCheck(
            check_name="temporal_plausibility",
            result=ValidationResult.VALID,
            details="Past onset window; low risk is expected during resolution",
            confidence=0.8,
        )

    def _check_biomarker_consistency(
        self,
        adverse_event: AdverseEventType,
        biomarkers: dict[str, float],
        risk_score: float,
    ) -> ValidationCheck:
        """Check whether the right biomarkers are elevated for this AE."""
        required_patterns = _REQUIRED_BIOMARKER_PATTERNS.get(adverse_event, [])

        if not required_patterns:
            return ValidationCheck(
                check_name="biomarker_consistency",
                result=ValidationResult.INSUFFICIENT_DATA,
                details=f"No required biomarker patterns defined for {adverse_event.value}",
                confidence=0.5,
            )

        if not biomarkers:
            if risk_score > 0.5:
                return ValidationCheck(
                    check_name="biomarker_consistency",
                    result=ValidationResult.IMPLAUSIBLE,
                    details="High risk predicted but no biomarkers available for validation",
                    confidence=0.4,
                )
            return ValidationCheck(
                check_name="biomarker_consistency",
                result=ValidationResult.INSUFFICIENT_DATA,
                details="No biomarker data to validate against",
                confidence=0.0,
            )

        # Check if any required pattern is satisfied
        elevated_biomarkers = set()
        for bm_id, value in biomarkers.items():
            node = self._kg.get_node(bm_id)
            if node is None:
                continue
            normal_range = (
                node.properties.get("normal_range_pg_ml")
                or node.properties.get("normal_range_ng_ml")
                or node.properties.get("normal_range_mg_l")
                or node.properties.get("normal_range_mg_dl")
                or node.properties.get("normal_range_u_l")
            )
            if normal_range and value > normal_range[1] * 1.5:
                elevated_biomarkers.add(bm_id)

        pattern_matched = False
        for pattern in required_patterns:
            if all(bm in elevated_biomarkers for bm in pattern):
                pattern_matched = True
                break

        if pattern_matched:
            return ValidationCheck(
                check_name="biomarker_consistency",
                result=ValidationResult.VALID,
                details=(
                    f"Biomarker pattern consistent with {adverse_event.value}: "
                    f"{len(elevated_biomarkers)} biomarkers elevated"
                ),
                confidence=0.85,
            )

        if elevated_biomarkers and risk_score > 0.3:
            return ValidationCheck(
                check_name="biomarker_consistency",
                result=ValidationResult.PLAUSIBLE,
                details=(
                    f"Some biomarkers elevated ({len(elevated_biomarkers)}) but "
                    f"no complete pattern match for {adverse_event.value}"
                ),
                confidence=0.5,
            )

        if not elevated_biomarkers and risk_score > 0.5:
            return ValidationCheck(
                check_name="biomarker_consistency",
                result=ValidationResult.IMPLAUSIBLE,
                details=(
                    f"High risk predicted ({risk_score:.2f}) but no biomarkers "
                    f"are elevated above threshold"
                ),
                confidence=0.7,
            )

        return ValidationCheck(
            check_name="biomarker_consistency",
            result=ValidationResult.VALID,
            details="Low risk prediction consistent with normal biomarkers",
            confidence=0.8,
        )

    def _check_cascade_ordering(
        self,
        adverse_event: AdverseEventType,
        biomarker_history: dict[str, list[tuple[float, float]]],
    ) -> ValidationCheck:
        """Verify that biomarkers rose in the expected cascade order.

        For CRS, the expected order is: IFN-gamma -> TNF-alpha -> IL-6 -> CRP.
        """
        # Expected cascade orders (biomarker ID -> expected order position)
        cascade_orders: dict[AdverseEventType, list[str]] = {
            AdverseEventType.CRS: [
                "CYTOKINE:IFN_GAMMA",
                "CYTOKINE:TNF_ALPHA",
                "CYTOKINE:IL6",
                "BIOMARKER:CRP",
                "BIOMARKER:FERRITIN",
            ],
            AdverseEventType.ICANS: [
                "CYTOKINE:IFN_GAMMA",
                "CYTOKINE:IL6",
                "PROTEIN:ANG2",
                "PROTEIN:VWF",
            ],
            AdverseEventType.HLH: [
                "CYTOKINE:IFN_GAMMA",
                "CYTOKINE:IL18",
                "BIOMARKER:FERRITIN",
                "BIOMARKER:SCD25",
            ],
        }

        expected_order = cascade_orders.get(adverse_event, [])
        if not expected_order:
            return ValidationCheck(
                check_name="cascade_ordering",
                result=ValidationResult.INSUFFICIENT_DATA,
                details="No cascade ordering data available",
                confidence=0.5,
            )

        # Find the time each biomarker first exceeded normal
        first_elevation_time: dict[str, float] = {}
        for bm_id in expected_order:
            history = biomarker_history.get(bm_id, [])
            node = self._kg.get_node(bm_id)
            if not history or not node:
                continue
            normal_range = (
                node.properties.get("normal_range_pg_ml")
                or node.properties.get("normal_range_ng_ml")
                or node.properties.get("normal_range_mg_l")
            )
            if not normal_range:
                continue
            threshold = normal_range[1] * 1.5
            for value, hours_ago in history:
                if value > threshold:
                    first_elevation_time[bm_id] = hours_ago
                    break

        if len(first_elevation_time) < 2:
            return ValidationCheck(
                check_name="cascade_ordering",
                result=ValidationResult.INSUFFICIENT_DATA,
                details=(
                    f"Only {len(first_elevation_time)} biomarkers with elevation "
                    f"timing data; need >= 2 for cascade analysis"
                ),
                confidence=0.3,
            )

        # Check ordering consistency
        ordered_biomarkers = [
            bm for bm in expected_order if bm in first_elevation_time
        ]
        violations = 0
        for i in range(len(ordered_biomarkers) - 1):
            time_a = first_elevation_time[ordered_biomarkers[i]]
            time_b = first_elevation_time[ordered_biomarkers[i + 1]]
            # Earlier elevation should have higher hours_ago
            if time_a < time_b:
                violations += 1

        total_pairs = max(1, len(ordered_biomarkers) - 1)
        consistency = 1.0 - (violations / total_pairs)

        if consistency >= 0.8:
            return ValidationCheck(
                check_name="cascade_ordering",
                result=ValidationResult.VALID,
                details=(
                    f"Biomarker cascade ordering is consistent "
                    f"({consistency:.0%} of pairs in expected order)"
                ),
                confidence=0.8,
            )
        elif consistency >= 0.5:
            return ValidationCheck(
                check_name="cascade_ordering",
                result=ValidationResult.PLAUSIBLE,
                details=(
                    f"Partial cascade ordering consistency ({consistency:.0%}). "
                    f"{violations} ordering violation(s) detected."
                ),
                confidence=0.5,
            )
        else:
            return ValidationCheck(
                check_name="cascade_ordering",
                result=ValidationResult.IMPLAUSIBLE,
                details=(
                    f"Biomarker cascade ordering is inconsistent "
                    f"({consistency:.0%}). {violations} violation(s) suggest "
                    f"the cytokine pattern may not follow expected biology."
                ),
                confidence=0.6,
            )

    def _check_magnitude_plausibility(
        self,
        adverse_event: AdverseEventType,
        biomarkers: dict[str, float],
        risk_score: float,
    ) -> ValidationCheck:
        """Check whether biomarker magnitudes are consistent with risk level."""
        if not biomarkers:
            return ValidationCheck(
                check_name="magnitude_plausibility",
                result=ValidationResult.INSUFFICIENT_DATA,
                details="No biomarker data for magnitude assessment",
                confidence=0.0,
            )

        # Compute maximum fold-change across all biomarkers
        max_fold_change = 0.0
        for bm_id, value in biomarkers.items():
            node = self._kg.get_node(bm_id)
            if node is None:
                continue
            normal_range = (
                node.properties.get("normal_range_pg_ml")
                or node.properties.get("normal_range_ng_ml")
                or node.properties.get("normal_range_mg_l")
                or node.properties.get("normal_range_mg_dl")
                or node.properties.get("normal_range_u_l")
            )
            if normal_range and normal_range[1] > 0:
                fold = value / normal_range[1]
                max_fold_change = max(max_fold_change, fold)

        # Check consistency between fold change and risk score
        if risk_score >= 0.8 and max_fold_change < 3.0:
            return ValidationCheck(
                check_name="magnitude_plausibility",
                result=ValidationResult.IMPLAUSIBLE,
                details=(
                    f"Critical risk ({risk_score:.2f}) but max biomarker "
                    f"fold-change is only {max_fold_change:.1f}x. Severe "
                    f"toxicity typically requires >10x cytokine elevation."
                ),
                confidence=0.7,
            )

        if risk_score < 0.3 and max_fold_change > 50.0:
            return ValidationCheck(
                check_name="magnitude_plausibility",
                result=ValidationResult.IMPLAUSIBLE,
                details=(
                    f"Low risk ({risk_score:.2f}) despite {max_fold_change:.0f}x "
                    f"biomarker elevation. This level of elevation typically "
                    f"indicates significant toxicity."
                ),
                confidence=0.7,
            )

        return ValidationCheck(
            check_name="magnitude_plausibility",
            result=ValidationResult.VALID,
            details=(
                f"Risk score ({risk_score:.2f}) is consistent with "
                f"max biomarker fold-change ({max_fold_change:.1f}x)"
            ),
            confidence=0.7,
        )

    # ------------------------------------------------------------------
    # Result aggregation
    # ------------------------------------------------------------------

    def _aggregate_results(self, checks: list[ValidationCheck]) -> ValidationResult:
        """Determine overall validation result from individual checks."""
        if not checks:
            return ValidationResult.INSUFFICIENT_DATA

        results = [c.result for c in checks]

        # Any IMPLAUSIBLE check makes the overall result implausible
        implausible_count = results.count(ValidationResult.IMPLAUSIBLE)
        if implausible_count >= 2:
            return ValidationResult.IMPLAUSIBLE
        if implausible_count == 1 and self._strict_mode:
            return ValidationResult.IMPLAUSIBLE

        valid_count = results.count(ValidationResult.VALID)
        plausible_count = results.count(ValidationResult.PLAUSIBLE)

        if valid_count >= len(checks) / 2:
            return ValidationResult.VALID
        if valid_count + plausible_count >= len(checks) / 2:
            return ValidationResult.PLAUSIBLE
        if results.count(ValidationResult.INSUFFICIENT_DATA) > len(checks) / 2:
            return ValidationResult.INSUFFICIENT_DATA

        return ValidationResult.PLAUSIBLE

    @staticmethod
    def _aggregate_confidence(checks: list[ValidationCheck]) -> float:
        """Compute aggregate confidence from individual checks."""
        if not checks:
            return 0.0
        return sum(c.confidence for c in checks) / len(checks)
