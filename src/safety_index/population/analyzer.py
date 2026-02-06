"""
Population-level risk analysis for clinical trials and drug portfolios.

Aggregates patient-level Safety Indices to produce trial-level and
portfolio-level risk assessments, including risk distribution analysis,
subgroup stratification, and early stopping signal detection.
"""

from __future__ import annotations

import logging
import math
import statistics
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.safety_index.index import (
    AdverseEventType,
    PopulationSafetyIndex,
    RiskCategory,
    SafetyIndex,
)

logger = logging.getLogger(__name__)


@dataclass
class SubgroupAnalysis:
    """Risk analysis for a patient subgroup.

    Attributes:
        subgroup_name: Human-readable subgroup label.
        subgroup_criteria: How the subgroup was defined.
        patient_count: Number of patients in the subgroup.
        mean_score: Mean Safety Index score.
        high_risk_fraction: Fraction of patients in high or critical risk.
        relative_risk: Risk relative to the overall population (>1 = higher).
    """

    subgroup_name: str
    subgroup_criteria: dict[str, Any]
    patient_count: int
    mean_score: float
    high_risk_fraction: float
    relative_risk: float


@dataclass
class EarlyStoppingSignal:
    """Signal that a trial may need safety-related early stopping.

    Attributes:
        signal_type: Category of the signal (rate, trend, severity).
        description: Human-readable description.
        severity: How concerning this signal is (0.0 - 1.0).
        affected_patients: Number of patients contributing to the signal.
        recommendation: Suggested action.
    """

    signal_type: str
    description: str
    severity: float
    affected_patients: int
    recommendation: str


class PopulationRiskAnalyzer:
    """Analyzes Safety Index data across patient populations.

    Provides trial-level aggregate metrics, subgroup stratification, trend
    detection, and early stopping signal generation.

    Usage::

        analyzer = PopulationRiskAnalyzer()
        pop_index = analyzer.compute_population_index(
            indices, "TRIAL-001", AdverseEventType.CRS
        )
        signals = analyzer.detect_early_stopping_signals(indices)
    """

    def __init__(
        self,
        high_risk_threshold: float = 0.6,
        critical_risk_threshold: float = 0.8,
        early_stopping_rate_threshold: float = 0.20,
        early_stopping_severity_threshold: float = 0.85,
    ) -> None:
        """Initialize the population risk analyzer.

        Args:
            high_risk_threshold: Score threshold for high-risk classification.
            critical_risk_threshold: Score threshold for critical-risk.
            early_stopping_rate_threshold: Fraction of high-risk patients that
                triggers an early stopping signal.
            early_stopping_severity_threshold: Individual score that triggers
                a severity-based signal.
        """
        self._high_threshold = high_risk_threshold
        self._critical_threshold = critical_risk_threshold
        self._stop_rate_threshold = early_stopping_rate_threshold
        self._stop_severity_threshold = early_stopping_severity_threshold

    def compute_population_index(
        self,
        patient_indices: list[SafetyIndex],
        population_id: str,
        adverse_event: AdverseEventType,
    ) -> PopulationSafetyIndex:
        """Compute aggregate population-level Safety Index.

        Args:
            patient_indices: List of patient-level SafetyIndex objects.
            population_id: Identifier for the trial or cohort.
            adverse_event: Which adverse event to analyze.

        Returns:
            PopulationSafetyIndex with aggregate metrics.

        Raises:
            ValueError: If no patient indices are provided.
        """
        if not patient_indices:
            raise ValueError("Cannot compute population index with no patients")

        # Filter to matching adverse event
        relevant = [
            idx for idx in patient_indices
            if idx.adverse_event == adverse_event
        ]
        if not relevant:
            raise ValueError(
                f"No patient indices for adverse event {adverse_event.value}"
            )

        scores = [idx.composite_score for idx in relevant]
        n = len(scores)

        mean_score = statistics.mean(scores)
        median_score = statistics.median(scores)
        std_score = statistics.stdev(scores) if n > 1 else 0.0

        high_risk_count = sum(1 for s in scores if s >= self._high_threshold)
        critical_risk_count = sum(1 for s in scores if s >= self._critical_threshold)

        # Risk distribution
        categories = [SafetyIndex.categorize(s) for s in scores]
        risk_distribution = dict(Counter(categories))

        # Top risk drivers (aggregate domain scores)
        driver_totals: dict[str, float] = {}
        driver_counts: dict[str, int] = {}
        for idx in relevant:
            for ds in idx.domain_scores:
                driver_totals[ds.domain] = driver_totals.get(ds.domain, 0.0) + ds.score
                driver_counts[ds.domain] = driver_counts.get(ds.domain, 0) + 1

        top_drivers = [
            (domain, driver_totals[domain] / driver_counts[domain])
            for domain in driver_totals
        ]
        top_drivers.sort(key=lambda x: x[1], reverse=True)

        logger.info(
            "Population index for %s (%s): n=%d, mean=%.3f, high_risk=%d, critical=%d",
            population_id, adverse_event.value, n, mean_score,
            high_risk_count, critical_risk_count,
        )

        return PopulationSafetyIndex(
            population_id=population_id,
            population_size=n,
            adverse_event=adverse_event,
            mean_score=mean_score,
            median_score=median_score,
            std_score=std_score,
            high_risk_count=high_risk_count,
            critical_risk_count=critical_risk_count,
            risk_distribution=risk_distribution,
            top_risk_drivers=top_drivers,
        )

    def stratify_subgroups(
        self,
        patient_indices: list[SafetyIndex],
        patient_metadata: dict[str, dict[str, Any]],
        stratify_by: str,
    ) -> list[SubgroupAnalysis]:
        """Stratify population risk by a patient attribute.

        Args:
            patient_indices: Patient-level Safety Indices.
            patient_metadata: Dict mapping patient_id to metadata dicts.
            stratify_by: The metadata key to stratify on (e.g. ``'age_group'``,
                ``'disease_burden_category'``, ``'car_t_product'``).

        Returns:
            List of SubgroupAnalysis objects, one per subgroup.
        """
        # Group patients by the stratification attribute
        groups: dict[str, list[float]] = {}
        for idx in patient_indices:
            meta = patient_metadata.get(idx.patient_id, {})
            group_value = str(meta.get(stratify_by, "unknown"))
            groups.setdefault(group_value, []).append(idx.composite_score)

        overall_mean = statistics.mean(
            [idx.composite_score for idx in patient_indices]
        ) if patient_indices else 0.0

        results: list[SubgroupAnalysis] = []
        for group_name, scores in sorted(groups.items()):
            group_mean = statistics.mean(scores)
            high_risk_frac = sum(1 for s in scores if s >= self._high_threshold) / len(scores)
            relative_risk = group_mean / overall_mean if overall_mean > 0 else 1.0

            results.append(SubgroupAnalysis(
                subgroup_name=f"{stratify_by}={group_name}",
                subgroup_criteria={stratify_by: group_name},
                patient_count=len(scores),
                mean_score=group_mean,
                high_risk_fraction=high_risk_frac,
                relative_risk=relative_risk,
            ))

        return results

    def detect_early_stopping_signals(
        self,
        patient_indices: list[SafetyIndex],
    ) -> list[EarlyStoppingSignal]:
        """Detect signals that may warrant trial early stopping.

        Checks three categories of signals:
            1. **Rate**: Fraction of high-risk patients exceeds threshold.
            2. **Severity**: Any individual patient has extremely high risk.
            3. **Trend**: Population-level risk is accelerating.

        Args:
            patient_indices: Current patient Safety Indices.

        Returns:
            List of EarlyStoppingSignal objects (empty if no signals).
        """
        signals: list[EarlyStoppingSignal] = []
        if not patient_indices:
            return signals

        scores = [idx.composite_score for idx in patient_indices]
        n = len(scores)

        # 1. Rate-based signal
        high_risk_count = sum(1 for s in scores if s >= self._high_threshold)
        high_risk_rate = high_risk_count / n

        if high_risk_rate >= self._stop_rate_threshold:
            signals.append(EarlyStoppingSignal(
                signal_type="rate",
                description=(
                    f"{high_risk_count}/{n} patients ({high_risk_rate:.0%}) have "
                    f"Safety Index >= {self._high_threshold}"
                ),
                severity=min(1.0, high_risk_rate / self._stop_rate_threshold),
                affected_patients=high_risk_count,
                recommendation=(
                    "Convene Data Safety Monitoring Board (DSMB) for review. "
                    "Consider dose modification or enrollment pause."
                ),
            ))

        # 2. Severity-based signal
        critical_patients = [
            idx for idx in patient_indices
            if idx.composite_score >= self._stop_severity_threshold
        ]
        if critical_patients:
            worst = max(critical_patients, key=lambda x: x.composite_score)
            signals.append(EarlyStoppingSignal(
                signal_type="severity",
                description=(
                    f"{len(critical_patients)} patient(s) with Safety Index >= "
                    f"{self._stop_severity_threshold}. Worst: "
                    f"{worst.patient_id} at {worst.composite_score:.3f}"
                ),
                severity=worst.composite_score,
                affected_patients=len(critical_patients),
                recommendation=(
                    "Immediate clinical review of critical-risk patients. "
                    "Evaluate need for intervention escalation."
                ),
            ))

        # 3. Trend-based signal (population-level worsening)
        worsening = [idx for idx in patient_indices if idx.trend > 0.01]
        if len(worsening) > n * 0.3:
            avg_trend = statistics.mean([idx.trend for idx in worsening])
            signals.append(EarlyStoppingSignal(
                signal_type="trend",
                description=(
                    f"{len(worsening)}/{n} patients ({len(worsening)/n:.0%}) show "
                    f"worsening trend (avg +{avg_trend:.4f}/hr)"
                ),
                severity=min(1.0, len(worsening) / n),
                affected_patients=len(worsening),
                recommendation=(
                    "Increase monitoring frequency. Review biomarker trajectories "
                    "for accelerating cytokine release patterns."
                ),
            ))

        return signals

    def compute_portfolio_risk(
        self,
        trial_indices: dict[str, list[SafetyIndex]],
        adverse_event: AdverseEventType,
    ) -> dict[str, PopulationSafetyIndex]:
        """Compute risk across multiple trials in a portfolio.

        Args:
            trial_indices: Dict mapping trial ID to patient Safety Indices.
            adverse_event: Which adverse event to analyze.

        Returns:
            Dict mapping trial ID to PopulationSafetyIndex.
        """
        results: dict[str, PopulationSafetyIndex] = {}
        for trial_id, indices in trial_indices.items():
            try:
                results[trial_id] = self.compute_population_index(
                    indices, trial_id, adverse_event,
                )
            except ValueError as e:
                logger.warning("Skipping trial %s: %s", trial_id, e)
        return results
