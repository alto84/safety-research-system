"""
Ensemble aggregator for multi-model prediction combining.

Combines predictions from multiple foundation models into a single calibrated
prediction with uncertainty quantification. Detects model disagreement and
flags cases where models diverge significantly.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.engine.orchestrator.normalizer import SafetyPrediction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ensemble result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DisagreementReport:
    """Report on disagreement between model predictions.

    Attributes:
        is_disagreement: Whether significant disagreement was detected.
        disagreement_score: Quantified disagreement (0.0 = unanimous, 1.0 = max).
        max_divergence: Largest pairwise score difference.
        divergent_pair: The two models with the largest divergence.
        analysis: Human-readable disagreement analysis.
    """

    is_disagreement: bool
    disagreement_score: float
    max_divergence: float
    divergent_pair: tuple[str, str] = ("", "")
    analysis: str = ""


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics for the ensemble.

    Attributes:
        mean_confidence: Average model confidence.
        confidence_spread: Spread (range) of model confidences.
        calibration_adjustment: Multiplicative adjustment applied to confidence.
        effective_confidence: Final calibrated confidence.
    """

    mean_confidence: float
    confidence_spread: float
    calibration_adjustment: float
    effective_confidence: float


@dataclass
class EnsemblePrediction:
    """Aggregated prediction from the ensemble.

    Attributes:
        patient_id: The patient being assessed.
        adverse_event: The adverse event type.
        risk_score: Aggregated risk score (0.0 - 1.0).
        confidence: Calibrated confidence (0.0 - 1.0).
        uncertainty_lower: Lower bound of the prediction interval.
        uncertainty_upper: Upper bound of the prediction interval.
        individual_predictions: The input predictions from each model.
        disagreement: Disagreement analysis report.
        calibration: Calibration metrics.
        aggregation_method: Which aggregation method was used.
        reasoning_summary: Combined reasoning from all models.
        combined_key_drivers: Union of key drivers across models.
        timestamp: When the ensemble was computed.
    """

    patient_id: str
    adverse_event: str
    risk_score: float
    confidence: float
    uncertainty_lower: float
    uncertainty_upper: float
    individual_predictions: list[SafetyPrediction]
    disagreement: DisagreementReport
    calibration: CalibrationMetrics
    aggregation_method: str = "confidence_weighted"
    reasoning_summary: str = ""
    combined_key_drivers: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def model_agreement(self) -> float:
        """Return inter-model agreement (1.0 = unanimous)."""
        return 1.0 - self.disagreement.disagreement_score

    def to_model_prediction_dict(self) -> dict[str, Any]:
        """Convert to the dict format expected by PatientRiskScorer."""
        return {
            "score": self.risk_score,
            "confidence": self.confidence,
            "model_name": "ensemble",
        }


# ---------------------------------------------------------------------------
# Ensemble aggregator
# ---------------------------------------------------------------------------

class EnsembleAggregator:
    """Combines multi-model predictions with calibrated uncertainty.

    Supports three aggregation strategies:
        1. **Confidence-weighted mean** (default): Each model's prediction
           is weighted by its confidence. Robust for most cases.
        2. **Median**: Robust to outlier predictions. Used when high
           disagreement is detected.
        3. **Conservative max**: Takes the highest risk score. Used in
           safety-critical contexts where missing a true positive is costly.

    Usage::

        aggregator = EnsembleAggregator()
        ensemble_pred = aggregator.aggregate(predictions)
    """

    def __init__(
        self,
        disagreement_threshold: float = 0.25,
        fallback_to_median_on_disagreement: bool = True,
        confidence_floor: float = 0.1,
        historical_calibration: dict[str, float] | None = None,
    ) -> None:
        """Initialize the ensemble aggregator.

        Args:
            disagreement_threshold: Score difference that triggers disagreement.
            fallback_to_median_on_disagreement: If True, switch to median
                aggregation when disagreement exceeds threshold.
            confidence_floor: Minimum confidence to assign (prevents zero).
            historical_calibration: Optional dict mapping ``model_id`` to a
                calibration multiplier learned from historical data.
        """
        self._disagreement_threshold = disagreement_threshold
        self._fallback_to_median = fallback_to_median_on_disagreement
        self._confidence_floor = confidence_floor
        self._historical_calibration = historical_calibration or {}

    def aggregate(
        self,
        predictions: list[SafetyPrediction],
        method: str | None = None,
    ) -> EnsemblePrediction:
        """Aggregate multiple model predictions into one ensemble prediction.

        Args:
            predictions: SafetyPrediction objects from individual models.
            method: Override aggregation method. One of ``'confidence_weighted'``,
                ``'median'``, ``'conservative_max'``. If ``None``, auto-selects.

        Returns:
            An EnsemblePrediction with aggregated scores and uncertainty.

        Raises:
            ValueError: If predictions list is empty.
        """
        if not predictions:
            raise ValueError("Cannot aggregate empty prediction list")

        if len(predictions) == 1:
            return self._single_model_result(predictions[0])

        # Detect disagreement
        disagreement = self._detect_disagreement(predictions)

        # Select aggregation method
        if method is None:
            if disagreement.is_disagreement and self._fallback_to_median:
                method = "median"
                logger.info("Disagreement detected (%.3f); falling back to median",
                            disagreement.disagreement_score)
            else:
                method = "confidence_weighted"

        # Apply historical calibration to confidences
        calibrated = self._apply_calibration(predictions)

        # Aggregate
        if method == "median":
            risk_score = self._aggregate_median(calibrated)
        elif method == "conservative_max":
            risk_score = self._aggregate_conservative_max(calibrated)
        else:
            risk_score = self._aggregate_confidence_weighted(calibrated)

        # Compute uncertainty interval
        lower, upper = self._compute_uncertainty(calibrated, disagreement)

        # Compute calibrated confidence
        cal_metrics = self._compute_calibration_metrics(calibrated, disagreement)

        # Merge reasoning and key drivers
        reasoning_summary = self._merge_reasoning(predictions)
        combined_drivers = self._merge_key_drivers(predictions)

        patient_id = predictions[0].patient_id
        adverse_event = predictions[0].adverse_event

        ensemble = EnsemblePrediction(
            patient_id=patient_id,
            adverse_event=adverse_event,
            risk_score=risk_score,
            confidence=cal_metrics.effective_confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            individual_predictions=predictions,
            disagreement=disagreement,
            calibration=cal_metrics,
            aggregation_method=method,
            reasoning_summary=reasoning_summary,
            combined_key_drivers=combined_drivers,
        )

        logger.info(
            "Ensemble for patient %s (%s): score=%.3f [%.3f, %.3f], "
            "confidence=%.3f, agreement=%.3f, method=%s",
            patient_id, adverse_event, risk_score, lower, upper,
            cal_metrics.effective_confidence, ensemble.model_agreement, method,
        )

        return ensemble

    # ------------------------------------------------------------------
    # Aggregation methods
    # ------------------------------------------------------------------

    def _aggregate_confidence_weighted(
        self,
        predictions: list[SafetyPrediction],
    ) -> float:
        """Confidence-weighted mean of risk scores."""
        weighted_sum = 0.0
        weight_total = 0.0
        for pred in predictions:
            w = max(pred.confidence, self._confidence_floor)
            weighted_sum += pred.risk_score * w
            weight_total += w
        return weighted_sum / weight_total if weight_total > 0 else 0.0

    def _aggregate_median(
        self,
        predictions: list[SafetyPrediction],
    ) -> float:
        """Median of risk scores (robust to outliers)."""
        return statistics.median([p.risk_score for p in predictions])

    def _aggregate_conservative_max(
        self,
        predictions: list[SafetyPrediction],
    ) -> float:
        """Maximum risk score (conservative for safety-critical decisions)."""
        return max(p.risk_score for p in predictions)

    # ------------------------------------------------------------------
    # Disagreement detection
    # ------------------------------------------------------------------

    def _detect_disagreement(
        self,
        predictions: list[SafetyPrediction],
    ) -> DisagreementReport:
        """Detect and quantify disagreement between model predictions."""
        scores = [p.risk_score for p in predictions]
        n = len(scores)

        if n < 2:
            return DisagreementReport(
                is_disagreement=False,
                disagreement_score=0.0,
                max_divergence=0.0,
            )

        # Pairwise divergence
        max_divergence = 0.0
        divergent_pair = ("", "")

        for i in range(n):
            for j in range(i + 1, n):
                diff = abs(scores[i] - scores[j])
                if diff > max_divergence:
                    max_divergence = diff
                    divergent_pair = (
                        predictions[i].model_id,
                        predictions[j].model_id,
                    )

        # Overall disagreement score: normalized standard deviation
        std_dev = statistics.stdev(scores) if n > 1 else 0.0
        # Normalize: std of 0.5 in [0,1] range would be extreme disagreement
        disagreement_score = min(1.0, std_dev * 2.0)

        is_disagreement = max_divergence > self._disagreement_threshold

        # Build analysis
        analysis_parts = [
            f"Score range: [{min(scores):.3f}, {max(scores):.3f}]",
            f"Std dev: {std_dev:.3f}",
            f"Max divergence: {max_divergence:.3f} ({divergent_pair[0]} vs {divergent_pair[1]})",
        ]
        if is_disagreement:
            analysis_parts.append(
                f"DISAGREEMENT DETECTED: exceeds threshold {self._disagreement_threshold}"
            )

        return DisagreementReport(
            is_disagreement=is_disagreement,
            disagreement_score=disagreement_score,
            max_divergence=max_divergence,
            divergent_pair=divergent_pair,
            analysis="; ".join(analysis_parts),
        )

    # ------------------------------------------------------------------
    # Uncertainty and calibration
    # ------------------------------------------------------------------

    def _compute_uncertainty(
        self,
        predictions: list[SafetyPrediction],
        disagreement: DisagreementReport,
    ) -> tuple[float, float]:
        """Compute prediction uncertainty interval.

        Uses the spread of predictions plus a calibration term based on
        model confidence to produce a credible interval.

        Returns:
            Tuple of (lower_bound, upper_bound), both in [0.0, 1.0].
        """
        scores = [p.risk_score for p in predictions]
        confidences = [p.confidence for p in predictions]

        mean_score = statistics.mean(scores)
        std_score = statistics.stdev(scores) if len(scores) > 1 else 0.1
        avg_confidence = statistics.mean(confidences)

        # Wider interval when confidence is low or disagreement is high
        uncertainty_factor = 1.5 * (1.0 - avg_confidence) + disagreement.disagreement_score

        half_width = std_score * (1.0 + uncertainty_factor)

        lower = max(0.0, mean_score - half_width)
        upper = min(1.0, mean_score + half_width)

        return lower, upper

    def _compute_calibration_metrics(
        self,
        predictions: list[SafetyPrediction],
        disagreement: DisagreementReport,
    ) -> CalibrationMetrics:
        """Compute calibrated confidence for the ensemble."""
        confidences = [p.confidence for p in predictions]
        mean_conf = statistics.mean(confidences)
        conf_spread = max(confidences) - min(confidences)

        # Reduce confidence when models disagree
        disagreement_penalty = disagreement.disagreement_score * 0.3

        # Reduce confidence when individual models are uncertain
        uncertainty_penalty = (1.0 - mean_conf) * 0.2

        adjustment = max(0.5, 1.0 - disagreement_penalty - uncertainty_penalty)
        effective = max(self._confidence_floor, mean_conf * adjustment)

        return CalibrationMetrics(
            mean_confidence=mean_conf,
            confidence_spread=conf_spread,
            calibration_adjustment=adjustment,
            effective_confidence=effective,
        )

    def _apply_calibration(
        self,
        predictions: list[SafetyPrediction],
    ) -> list[SafetyPrediction]:
        """Apply historical calibration adjustments to model confidences.

        Does not mutate the input predictions; returns new objects if
        calibration data is available.
        """
        if not self._historical_calibration:
            return predictions

        calibrated: list[SafetyPrediction] = []
        for pred in predictions:
            multiplier = self._historical_calibration.get(pred.model_id, 1.0)
            if multiplier != 1.0:
                calibrated.append(SafetyPrediction(
                    model_id=pred.model_id,
                    patient_id=pred.patient_id,
                    adverse_event=pred.adverse_event,
                    risk_score=pred.risk_score,
                    confidence=max(
                        self._confidence_floor,
                        min(1.0, pred.confidence * multiplier),
                    ),
                    reasoning=pred.reasoning,
                    key_drivers=pred.key_drivers,
                    raw_response=pred.raw_response,
                    latency_ms=pred.latency_ms,
                    tokens_used=pred.tokens_used,
                    timestamp=pred.timestamp,
                    metadata={**pred.metadata, "calibration_applied": multiplier},
                ))
            else:
                calibrated.append(pred)
        return calibrated

    # ------------------------------------------------------------------
    # Reasoning merge
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_reasoning(predictions: list[SafetyPrediction]) -> str:
        """Merge reasoning from multiple models into a summary."""
        parts: list[str] = []
        for pred in predictions:
            if pred.reasoning:
                truncated = pred.reasoning[:500]
                parts.append(f"[{pred.model_id}] {truncated}")
        return "\n\n".join(parts)

    @staticmethod
    def _merge_key_drivers(predictions: list[SafetyPrediction]) -> list[str]:
        """Combine key drivers from all models, preserving order by frequency."""
        driver_count: dict[str, int] = {}
        for pred in predictions:
            for driver in pred.key_drivers:
                driver_count[driver] = driver_count.get(driver, 0) + 1
        # Sort by frequency, then alphabetically
        return sorted(driver_count, key=lambda d: (-driver_count[d], d))

    # ------------------------------------------------------------------
    # Single-model fallback
    # ------------------------------------------------------------------

    def _single_model_result(self, pred: SafetyPrediction) -> EnsemblePrediction:
        """Wrap a single prediction as an ensemble result."""
        # Apply wider uncertainty for single model
        half_width = 0.15 * (1.0 - pred.confidence)
        lower = max(0.0, pred.risk_score - half_width)
        upper = min(1.0, pred.risk_score + half_width)

        return EnsemblePrediction(
            patient_id=pred.patient_id,
            adverse_event=pred.adverse_event,
            risk_score=pred.risk_score,
            confidence=pred.confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            individual_predictions=[pred],
            disagreement=DisagreementReport(
                is_disagreement=False,
                disagreement_score=0.0,
                max_divergence=0.0,
            ),
            calibration=CalibrationMetrics(
                mean_confidence=pred.confidence,
                confidence_spread=0.0,
                calibration_adjustment=1.0,
                effective_confidence=pred.confidence,
            ),
            aggregation_method="single_model",
            reasoning_summary=pred.reasoning,
            combined_key_drivers=pred.key_drivers,
        )
