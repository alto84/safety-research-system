"""
Patient-level risk scoring engine.

Computes the Safety Index for an individual patient by:
    1. Scoring biomarker trajectories against known thresholds
    2. Querying the knowledge graph for pathway activation
    3. Incorporating foundation model predictions
    4. Adjusting for clinical context (disease burden, comorbidities)
    5. Computing the trend (rate of change)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.data.graph.knowledge_graph import KnowledgeGraph
from src.data.graph.schema import EdgeType, NodeType
from src.safety_index.index import (
    AdverseEventType,
    DomainScore,
    RiskCategory,
    SafetyIndex,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Reference ranges and thresholds
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BiomarkerThreshold:
    """Threshold definitions for a single biomarker.

    Attributes:
        biomarker_id: Knowledge graph node ID (e.g. ``'CYTOKINE:IL6'``).
        unit: Measurement unit.
        normal_upper: Upper limit of normal.
        grade1_threshold: Threshold suggesting Grade 1 toxicity.
        grade2_threshold: Threshold suggesting Grade 2 toxicity.
        grade3_threshold: Threshold suggesting Grade >= 3 toxicity.
        rate_of_change_critical: Change per hour that is alarming.
    """

    biomarker_id: str
    unit: str
    normal_upper: float
    grade1_threshold: float
    grade2_threshold: float
    grade3_threshold: float
    rate_of_change_critical: float = 0.0


# Evidence-based thresholds (Teachey et al. 2016, Lee et al. 2019)
CRS_BIOMARKER_THRESHOLDS: list[BiomarkerThreshold] = [
    BiomarkerThreshold("CYTOKINE:IL6", "pg/mL", 7.0, 50.0, 500.0, 5000.0, 100.0),
    BiomarkerThreshold("CYTOKINE:IFN_GAMMA", "pg/mL", 15.6, 100.0, 1000.0, 10000.0, 200.0),
    BiomarkerThreshold("CYTOKINE:TNF_ALPHA", "pg/mL", 8.1, 25.0, 100.0, 1000.0, 50.0),
    BiomarkerThreshold("BIOMARKER:CRP", "mg/L", 10.0, 50.0, 150.0, 300.0, 20.0),
    BiomarkerThreshold("BIOMARKER:FERRITIN", "ng/mL", 300.0, 1000.0, 5000.0, 10000.0, 500.0),
]

ICANS_BIOMARKER_THRESHOLDS: list[BiomarkerThreshold] = [
    BiomarkerThreshold("CYTOKINE:IL6", "pg/mL", 7.0, 100.0, 1000.0, 10000.0, 200.0),
    BiomarkerThreshold("PROTEIN:ANG2", "pg/mL", 2000.0, 5000.0, 10000.0, 20000.0, 1000.0),
    BiomarkerThreshold("PROTEIN:VWF", "%", 150.0, 250.0, 400.0, 600.0, 30.0),
]

HLH_BIOMARKER_THRESHOLDS: list[BiomarkerThreshold] = [
    BiomarkerThreshold("BIOMARKER:FERRITIN", "ng/mL", 300.0, 3000.0, 10000.0, 50000.0, 1000.0),
    BiomarkerThreshold("BIOMARKER:D_DIMER", "mg/L", 0.5, 2.0, 5.0, 10.0, 1.0),
    BiomarkerThreshold("BIOMARKER:FIBRINOGEN", "mg/dL", 200.0, 150.0, 100.0, 50.0, -20.0),
    BiomarkerThreshold("CYTOKINE:IL18", "pg/mL", 500.0, 2000.0, 5000.0, 15000.0, 500.0),
    BiomarkerThreshold("BIOMARKER:SCD25", "U/mL", 1000.0, 5000.0, 10000.0, 20000.0, 2000.0),
]

_THRESHOLDS_BY_AE: dict[AdverseEventType, list[BiomarkerThreshold]] = {
    AdverseEventType.CRS: CRS_BIOMARKER_THRESHOLDS,
    AdverseEventType.ICANS: ICANS_BIOMARKER_THRESHOLDS,
    AdverseEventType.HLH: HLH_BIOMARKER_THRESHOLDS,
}


@dataclass
class PatientData:
    """Input data for a single patient at a point in time.

    Attributes:
        patient_id: Unique patient identifier.
        hours_since_infusion: Hours elapsed since cell therapy infusion.
        biomarkers: Current biomarker values keyed by graph node ID.
        biomarker_history: Previous biomarker values as
            ``{node_id: [(value, hours_ago), ...]}``.
        disease_burden: Tumor burden category (0.0=none, 1.0=very high).
        prior_therapies: Number of prior lines of therapy.
        age_years: Patient age in years.
        comorbidities: List of relevant comorbidity codes.
        car_t_product: Name of the CAR-T product.
        car_t_dose: Infused dose (cells/kg or total cells).
        previous_safety_indices: List of ``(score, hours_ago)`` from prior
            Safety Index computations for trend analysis.
        additional_context: Free-form clinical context.
    """

    patient_id: str
    hours_since_infusion: float
    biomarkers: dict[str, float] = field(default_factory=dict)
    biomarker_history: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    disease_burden: float = 0.5
    prior_therapies: int = 3
    age_years: int = 60
    comorbidities: list[str] = field(default_factory=list)
    car_t_product: str = ""
    car_t_dose: float = 0.0
    previous_safety_indices: list[tuple[float, float]] = field(default_factory=list)
    additional_context: dict[str, Any] = field(default_factory=dict)


class PatientRiskScorer:
    """Computes the patient-level Safety Index.

    Integrates biomarker data, knowledge graph pathway activation, model
    predictions, and clinical context into a composite risk score.

    Usage::

        scorer = PatientRiskScorer(knowledge_graph=kg)
        index = scorer.compute(patient_data, AdverseEventType.CRS,
                               model_predictions=model_preds)
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        domain_weights: dict[str, float] | None = None,
    ) -> None:
        """Initialize the risk scorer.

        Args:
            knowledge_graph: The loaded biological knowledge graph.
            domain_weights: Optional override for domain importance weights.
        """
        self._kg = knowledge_graph
        self._domain_weights = domain_weights or {
            "biomarker": 0.30,
            "pathway": 0.25,
            "model": 0.25,
            "clinical": 0.20,
        }

    def compute(
        self,
        patient: PatientData,
        adverse_event: AdverseEventType,
        model_predictions: list[dict[str, float]] | None = None,
    ) -> SafetyIndex:
        """Compute the Safety Index for a patient and adverse event type.

        Args:
            patient: The patient data snapshot.
            adverse_event: Which adverse event to score.
            model_predictions: Optional list of model prediction dicts, each
                containing at minimum ``{'score': float, 'confidence': float}``.

        Returns:
            A fully populated SafetyIndex dataclass.
        """
        logger.info(
            "Computing %s Safety Index for patient %s (%.1fh post-infusion)",
            adverse_event.value, patient.patient_id, patient.hours_since_infusion,
        )

        # Score each domain
        biomarker_domain = self._score_biomarker_domain(patient, adverse_event)
        pathway_domain = self._score_pathway_domain(patient, adverse_event)
        model_domain = self._score_model_domain(model_predictions)
        clinical_domain = self._score_clinical_domain(patient, adverse_event)

        domain_scores = [biomarker_domain, pathway_domain, model_domain, clinical_domain]

        # Composite score
        composite = SafetyIndex.compute_composite(domain_scores, self._domain_weights)

        # Trend
        trend = SafetyIndex.compute_trend(composite, patient.previous_safety_indices)

        # Model agreement
        model_agreement = 1.0
        if model_predictions and len(model_predictions) > 1:
            scores = [p["score"] for p in model_predictions if "score" in p]
            if scores:
                mean = sum(scores) / len(scores)
                variance = sum((s - mean) ** 2 for s in scores) / len(scores)
                model_agreement = max(0.0, 1.0 - math.sqrt(variance) * 2)

        return SafetyIndex(
            patient_id=patient.patient_id,
            adverse_event=adverse_event,
            composite_score=composite,
            risk_category=SafetyIndex.categorize(composite),
            domain_scores=domain_scores,
            trend=trend,
            hours_since_infusion=patient.hours_since_infusion,
            prediction_horizon_hours=24.0,
            model_agreement=model_agreement,
            metadata={
                "car_t_product": patient.car_t_product,
                "domain_weights": self._domain_weights,
            },
        )

    # ------------------------------------------------------------------
    # Domain scoring
    # ------------------------------------------------------------------

    def _score_biomarker_domain(
        self,
        patient: PatientData,
        adverse_event: AdverseEventType,
    ) -> DomainScore:
        """Score the biomarker domain based on current levels and trajectories.

        Each biomarker is scored as a fraction of its grade thresholds, then
        combined with rate-of-change signals.
        """
        thresholds = _THRESHOLDS_BY_AE.get(adverse_event, [])
        if not thresholds:
            return DomainScore(domain="biomarker", score=0.0, confidence=0.0)

        component_scores: dict[str, float] = {}
        values_found = 0

        for thresh in thresholds:
            value = patient.biomarkers.get(thresh.biomarker_id)
            if value is None:
                continue
            values_found += 1

            # Score based on position between thresholds
            if thresh.grade3_threshold > thresh.normal_upper:
                # Normal biomarker (higher = worse, e.g. IL-6)
                if value <= thresh.normal_upper:
                    level_score = 0.0
                elif value <= thresh.grade1_threshold:
                    level_score = 0.2 * (value - thresh.normal_upper) / (
                        thresh.grade1_threshold - thresh.normal_upper
                    )
                elif value <= thresh.grade2_threshold:
                    level_score = 0.2 + 0.3 * (value - thresh.grade1_threshold) / (
                        thresh.grade2_threshold - thresh.grade1_threshold
                    )
                elif value <= thresh.grade3_threshold:
                    level_score = 0.5 + 0.3 * (value - thresh.grade2_threshold) / (
                        thresh.grade3_threshold - thresh.grade2_threshold
                    )
                else:
                    # Beyond grade 3 threshold
                    excess = (value - thresh.grade3_threshold) / thresh.grade3_threshold
                    level_score = min(1.0, 0.8 + 0.2 * excess)
            else:
                # Inverted biomarker (lower = worse, e.g. fibrinogen)
                if value >= thresh.normal_upper:
                    level_score = 0.0
                elif value >= thresh.grade1_threshold:
                    level_score = 0.2 * (thresh.normal_upper - value) / (
                        thresh.normal_upper - thresh.grade1_threshold
                    )
                elif value >= thresh.grade2_threshold:
                    level_score = 0.2 + 0.3 * (thresh.grade1_threshold - value) / (
                        thresh.grade1_threshold - thresh.grade2_threshold
                    )
                elif value >= thresh.grade3_threshold:
                    level_score = 0.5 + 0.3 * (thresh.grade2_threshold - value) / (
                        thresh.grade2_threshold - thresh.grade3_threshold
                    )
                else:
                    level_score = min(1.0, 0.8 + 0.2)

            # Rate-of-change bonus
            roc_score = 0.0
            history = patient.biomarker_history.get(thresh.biomarker_id, [])
            if history and thresh.rate_of_change_critical != 0:
                most_recent_val, hours_ago = history[-1]
                if hours_ago > 0:
                    rate = (value - most_recent_val) / hours_ago
                    roc_score = min(0.2, abs(rate / thresh.rate_of_change_critical) * 0.2)

            component_scores[thresh.biomarker_id] = min(1.0, level_score + roc_score)

        if not component_scores:
            return DomainScore(domain="biomarker", score=0.0, confidence=0.0)

        # Confidence scales with data completeness
        confidence = min(1.0, values_found / max(1, len(thresholds)))

        # Aggregate: use max of top 2 components + mean of rest
        sorted_scores = sorted(component_scores.values(), reverse=True)
        if len(sorted_scores) >= 2:
            top_contribution = (sorted_scores[0] + sorted_scores[1]) / 2 * 0.6
            rest_contribution = (
                sum(sorted_scores[2:]) / max(1, len(sorted_scores) - 2) * 0.4
                if len(sorted_scores) > 2 else 0.0
            )
            aggregate = top_contribution + rest_contribution
        else:
            aggregate = sorted_scores[0]

        return DomainScore(
            domain="biomarker",
            score=min(1.0, aggregate),
            confidence=confidence,
            components=component_scores,
        )

    def _score_pathway_domain(
        self,
        patient: PatientData,
        adverse_event: AdverseEventType,
    ) -> DomainScore:
        """Score pathway activation using the knowledge graph.

        Maps the patient's elevated biomarkers to knowledge graph nodes, then
        checks which pathways are activated and how strongly they connect to
        the adverse event.
        """
        ae_node_id = f"AE:{adverse_event.value}"
        component_scores: dict[str, float] = {}

        # Find upstream causes of the adverse event
        upstream = self._kg.get_upstream_causes(ae_node_id, max_depth=4)
        if not upstream:
            return DomainScore(
                domain="pathway", score=0.0, confidence=0.3,
                components={"note": 0.0},
            )

        # Check which upstream entities have elevated patient biomarkers
        activated_weight = 0.0
        total_weight = 0.0

        for node, weight in upstream:
            total_weight += weight
            value = patient.biomarkers.get(node.node_id)
            if value is not None:
                # Check if this value is elevated
                normal_range = node.properties.get("normal_range_pg_ml") or \
                    node.properties.get("normal_range_ng_ml") or \
                    node.properties.get("normal_range_mg_l")
                if normal_range and value > normal_range[1]:
                    fold_change = value / max(normal_range[1], 1e-9)
                    activation = min(1.0, math.log2(max(1.0, fold_change)) / 5.0)
                    activated_weight += weight * activation
                    component_scores[node.node_id] = activation

        score = activated_weight / total_weight if total_weight > 0 else 0.0
        confidence = min(1.0, len(component_scores) / max(1, min(5, len(upstream))))

        return DomainScore(
            domain="pathway",
            score=min(1.0, score),
            confidence=confidence,
            components=component_scores,
        )

    def _score_model_domain(
        self,
        model_predictions: list[dict[str, float]] | None,
    ) -> DomainScore:
        """Score the model prediction domain.

        Aggregates predictions from multiple foundation models with
        confidence weighting.
        """
        if not model_predictions:
            return DomainScore(domain="model", score=0.0, confidence=0.0)

        components: dict[str, float] = {}
        weighted_sum = 0.0
        weight_total = 0.0

        for i, pred in enumerate(model_predictions):
            score = pred.get("score", 0.0)
            confidence = pred.get("confidence", 0.5)
            model_name = pred.get("model_name", f"model_{i}")

            weighted_sum += score * confidence
            weight_total += confidence
            components[str(model_name)] = score

        aggregate = weighted_sum / weight_total if weight_total > 0 else 0.0
        avg_confidence = weight_total / len(model_predictions)

        return DomainScore(
            domain="model",
            score=min(1.0, aggregate),
            confidence=avg_confidence,
            components=components,
        )

    def _score_clinical_domain(
        self,
        patient: PatientData,
        adverse_event: AdverseEventType,
    ) -> DomainScore:
        """Score clinical risk factors.

        Integrates disease burden, prior therapy lines, age, comorbidities,
        and temporal context.
        """
        components: dict[str, float] = {}

        # Disease burden (higher = higher risk)
        components["disease_burden"] = patient.disease_burden

        # Prior therapies (more = higher risk, saturates at ~6 lines)
        components["prior_therapies"] = min(1.0, patient.prior_therapies / 6.0)

        # Age factor (risk increases >60, accelerates >70)
        if patient.age_years < 50:
            age_score = 0.1
        elif patient.age_years < 60:
            age_score = 0.2
        elif patient.age_years < 70:
            age_score = 0.4
        else:
            age_score = 0.6
        components["age"] = age_score

        # Comorbidity burden
        comorbidity_score = min(1.0, len(patient.comorbidities) * 0.15)
        components["comorbidities"] = comorbidity_score

        # Temporal risk (CRS peaks days 1-7, ICANS peaks days 3-10)
        temporal_risk = self._temporal_risk_curve(
            patient.hours_since_infusion, adverse_event,
        )
        components["temporal_risk"] = temporal_risk

        # Weighted combination
        weights = {
            "disease_burden": 0.25,
            "prior_therapies": 0.15,
            "age": 0.15,
            "comorbidities": 0.15,
            "temporal_risk": 0.30,
        }
        aggregate = sum(
            components[k] * weights.get(k, 0.2) for k in components
        )

        return DomainScore(
            domain="clinical",
            score=min(1.0, aggregate),
            confidence=0.85,  # clinical data is generally reliable
            components=components,
        )

    @staticmethod
    def _temporal_risk_curve(
        hours_since_infusion: float,
        adverse_event: AdverseEventType,
    ) -> float:
        """Compute temporal risk based on known onset kinetics.

        Returns a value 0.0-1.0 representing where the patient is relative
        to the expected peak risk window.
        """
        # Peak risk windows in hours
        peak_windows = {
            AdverseEventType.CRS: (24.0, 168.0),      # Day 1-7
            AdverseEventType.ICANS: (72.0, 240.0),     # Day 3-10
            AdverseEventType.HLH: (72.0, 336.0),       # Day 3-14
        }
        peak_start, peak_end = peak_windows.get(adverse_event, (24.0, 168.0))

        if hours_since_infusion < 0:
            return 0.1  # pre-infusion baseline
        elif hours_since_infusion < peak_start:
            # Rising risk approaching peak window
            return 0.2 + 0.5 * (hours_since_infusion / peak_start)
        elif hours_since_infusion <= peak_end:
            # Inside peak window
            midpoint = (peak_start + peak_end) / 2
            distance_from_mid = abs(hours_since_infusion - midpoint) / (
                (peak_end - peak_start) / 2
            )
            return 0.7 + 0.3 * (1.0 - distance_from_mid)
        else:
            # Past peak, declining risk
            hours_past_peak = hours_since_infusion - peak_end
            decay = math.exp(-0.01 * hours_past_peak)
            return 0.3 * decay
