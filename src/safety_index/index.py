"""
Core Safety Index dataclasses and computation logic.

The Safety Index is a normalized composite score (0.0 to 1.0) where:
    0.0 - 0.3  = low risk
    0.3 - 0.6  = moderate risk
    0.6 - 0.8  = high risk
    0.8 - 1.0  = critical risk

It aggregates four signal domains:
    1. Biomarker domain   - cytokine levels, acute phase reactants, organ function
    2. Pathway domain     - knowledge graph pathway activation scores
    3. Model domain       - foundation model predictions and confidence
    4. Clinical domain    - patient history, disease burden, comorbidities
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RiskCategory(Enum):
    """Risk stratification category derived from the Safety Index."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AdverseEventType(Enum):
    """Adverse event types tracked by the Safety Index."""

    CRS = "CRS"
    ICANS = "ICANS"
    HLH = "HLH"


@dataclass
class DomainScore:
    """A score from one of the four signal domains.

    Attributes:
        domain: Which signal domain produced this score.
        score: Normalized value in [0.0, 1.0].
        confidence: How confident we are in this domain's signal (0.0 - 1.0).
        components: Named sub-scores contributing to this domain.
        timestamp: When this score was computed.
    """

    domain: str
    score: float
    confidence: float
    components: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        self.score = max(0.0, min(1.0, self.score))
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class SafetyIndex:
    """Patient-level composite Safety Index for a single adverse event type.

    The final score is a confidence-weighted average of domain scores, with
    optional temporal decay weighting for time-series data.

    Attributes:
        patient_id: Unique patient identifier.
        adverse_event: Which adverse event this index covers.
        composite_score: The final aggregated score (0.0 - 1.0).
        risk_category: Derived risk stratification.
        domain_scores: Individual domain contributions.
        trend: Rate of change per hour (positive = worsening).
        hours_since_infusion: Time since cell therapy infusion.
        prediction_horizon_hours: How far ahead this score predicts.
        model_agreement: Inter-model agreement (1.0 = unanimous).
        timestamp: When this index was computed.
        metadata: Additional context (model versions, data sources, etc.).
    """

    patient_id: str
    adverse_event: AdverseEventType
    composite_score: float
    risk_category: RiskCategory
    domain_scores: list[DomainScore]
    trend: float = 0.0
    hours_since_infusion: float = 0.0
    prediction_horizon_hours: float = 24.0
    model_agreement: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.composite_score = max(0.0, min(1.0, self.composite_score))

    @staticmethod
    def categorize(score: float) -> RiskCategory:
        """Map a numeric score to a risk category.

        Args:
            score: The composite Safety Index score (0.0 - 1.0).

        Returns:
            The corresponding RiskCategory.
        """
        if score < 0.3:
            return RiskCategory.LOW
        elif score < 0.6:
            return RiskCategory.MODERATE
        elif score < 0.8:
            return RiskCategory.HIGH
        else:
            return RiskCategory.CRITICAL

    @staticmethod
    def compute_composite(
        domain_scores: list[DomainScore],
        domain_weights: dict[str, float] | None = None,
    ) -> float:
        """Compute the confidence-weighted composite score.

        Each domain's contribution is weighted by both its assigned importance
        weight and its own confidence. This naturally down-weights domains with
        uncertain or missing data.

        Args:
            domain_scores: The individual domain scores.
            domain_weights: Explicit importance weights per domain name.
                Defaults to equal weighting.

        Returns:
            The composite score in [0.0, 1.0].
        """
        if not domain_scores:
            return 0.0

        default_weights = {
            "biomarker": 0.30,
            "pathway": 0.25,
            "model": 0.25,
            "clinical": 0.20,
        }
        weights = domain_weights or default_weights

        weighted_sum = 0.0
        weight_total = 0.0

        for ds in domain_scores:
            w = weights.get(ds.domain, 1.0 / len(domain_scores))
            effective_weight = w * ds.confidence
            weighted_sum += ds.score * effective_weight
            weight_total += effective_weight

        if weight_total == 0.0:
            return 0.0

        return max(0.0, min(1.0, weighted_sum / weight_total))

    @staticmethod
    def compute_trend(
        current_score: float,
        previous_scores: list[tuple[float, float]],
    ) -> float:
        """Compute rate-of-change trend using exponential weighting.

        Uses the most recent scores to estimate the direction and speed of
        change. Positive values indicate worsening risk.

        Args:
            current_score: The most recent composite score.
            previous_scores: List of ``(score, hours_ago)`` tuples, ordered
                oldest to most recent.

        Returns:
            Rate of change per hour. Positive = worsening.
        """
        if not previous_scores:
            return 0.0

        # Use exponentially-weighted linear regression
        decay_rate = 0.1  # weight halves roughly every 7 hours
        n = len(previous_scores) + 1
        all_points = previous_scores + [(current_score, 0.0)]

        sum_w = 0.0
        sum_wt = 0.0
        sum_ws = 0.0
        sum_wtt = 0.0
        sum_wts = 0.0

        for score, hours_ago in all_points:
            t = -hours_ago  # negative = in the past
            w = math.exp(-decay_rate * hours_ago)
            sum_w += w
            sum_wt += w * t
            sum_ws += w * score
            sum_wtt += w * t * t
            sum_wts += w * t * score

        denom = sum_w * sum_wtt - sum_wt * sum_wt
        if abs(denom) < 1e-12:
            return 0.0

        slope = (sum_w * sum_wts - sum_wt * sum_ws) / denom
        return slope


@dataclass
class PopulationSafetyIndex:
    """Aggregated Safety Index across a patient population (trial or portfolio).

    Attributes:
        population_id: Trial ID or portfolio identifier.
        population_size: Number of patients in the cohort.
        adverse_event: Which adverse event this covers.
        mean_score: Mean composite score across the population.
        median_score: Median composite score.
        std_score: Standard deviation of scores.
        high_risk_count: Patients with score >= 0.6.
        critical_risk_count: Patients with score >= 0.8.
        risk_distribution: Counts by risk category.
        top_risk_drivers: Most common elevated domain scores.
        timestamp: When this was computed.
        metadata: Additional context.
    """

    population_id: str
    population_size: int
    adverse_event: AdverseEventType
    mean_score: float
    median_score: float
    std_score: float
    high_risk_count: int
    critical_risk_count: int
    risk_distribution: dict[RiskCategory, int]
    top_risk_drivers: list[tuple[str, float]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
