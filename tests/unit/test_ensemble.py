"""
Tests for EnsembleAggregator — weighted averaging, disagreement detection,
and Platt calibration.

The EnsembleAggregator combines predictions from multiple foundation models
into a single calibrated risk assessment with uncertainty quantification.
"""

import pytest
import math
from datetime import timedelta
from dataclasses import dataclass

from tests.conftest import SafetyPrediction, AggregatedRisk, TokenCount


# ---------------------------------------------------------------------------
# EnsembleAggregator reference implementation
# ---------------------------------------------------------------------------

class EnsembleAggregator:
    """Combines multi-model predictions with calibrated uncertainty."""

    # Default model weights from eval performance
    DEFAULT_WEIGHTS = {
        "claude-opus-4": 0.45,
        "gpt-5.2": 0.30,
        "gemini-3": 0.25,
    }

    def __init__(
        self,
        model_weights: dict = None,
        disagreement_threshold: float = 0.25,
        platt_a: float = -1.0,
        platt_b: float = 0.0,
    ):
        self.model_weights = model_weights or self.DEFAULT_WEIGHTS
        self.disagreement_threshold = disagreement_threshold
        # Platt scaling parameters: P(y=1|s) = 1 / (1 + exp(A*s + B))
        self.platt_a = platt_a
        self.platt_b = platt_b

    def get_model_weights(self, predictions: list[SafetyPrediction]) -> dict:
        """Return normalized weights for the models present in predictions."""
        present = {p.model_id for p in predictions}
        raw = {mid: w for mid, w in self.model_weights.items() if mid in present}
        # Also handle unknown models with equal fallback weight
        for p in predictions:
            if p.model_id not in raw:
                raw[p.model_id] = 1.0 / len(predictions)
        total = sum(raw.values())
        if total == 0:
            return {mid: 1.0 / len(raw) for mid in raw}
        return {mid: w / total for mid, w in raw.items()}

    def weighted_average(self, predictions: list[SafetyPrediction], weights: dict) -> float:
        """Compute weighted average risk score."""
        score = sum(p.risk_score * weights.get(p.model_id, 0) for p in predictions)
        return score

    def disagreement_score(self, predictions: list[SafetyPrediction]) -> float:
        """Measure disagreement as max pairwise difference in risk scores."""
        if len(predictions) < 2:
            return 0.0
        scores = [p.risk_score for p in predictions]
        return max(scores) - min(scores)

    def analyze_disagreement(self, predictions: list[SafetyPrediction]) -> str:
        """Produce human-readable disagreement analysis."""
        sorted_preds = sorted(predictions, key=lambda p: p.risk_score, reverse=True)
        lines = []
        for p in sorted_preds:
            lines.append(f"{p.model_id}: risk={p.risk_score:.2f}, confidence={p.confidence:.2f}")
        score_range = sorted_preds[0].risk_score - sorted_preds[-1].risk_score
        lines.append(f"Score range: {score_range:.2f} (threshold: {self.disagreement_threshold:.2f})")
        return "; ".join(lines)

    def platt_calibrate(self, score: float) -> float:
        """Apply Platt scaling to calibrate the ensemble score."""
        calibrated = 1.0 / (1.0 + math.exp(self.platt_a * score + self.platt_b))
        return max(0.0, min(1.0, calibrated))

    def confidence_interval(self, predictions: list[SafetyPrediction], weights: dict) -> tuple:
        """Compute 95% CI from model spread (simplified: weighted mean +/- 1.96 * weighted std)."""
        if len(predictions) < 2:
            mean = predictions[0].risk_score if predictions else 0.5
            return (max(0.0, mean - 0.1), min(1.0, mean + 0.1))

        mean = self.weighted_average(predictions, weights)
        variance = sum(
            weights.get(p.model_id, 0) * (p.risk_score - mean) ** 2
            for p in predictions
        )
        std = math.sqrt(variance)
        margin = 1.96 * std
        return (max(0.0, mean - margin), min(1.0, mean + margin))

    def attribution(self, predictions: list[SafetyPrediction], weights: dict) -> dict:
        """Return each model's contribution to the final score."""
        return {
            p.model_id: round(weights.get(p.model_id, 0), 4)
            for p in predictions
        }

    def aggregate(self, predictions: list[SafetyPrediction]) -> AggregatedRisk:
        """Main aggregation entry point."""
        if not predictions:
            raise ValueError("Cannot aggregate empty predictions list.")

        weights = self.get_model_weights(predictions)

        # Detect disagreement
        d_score = self.disagreement_score(predictions)
        if d_score > self.disagreement_threshold:
            # Still compute a score, but flag for review
            ensemble_score = self.weighted_average(predictions, weights)
            calibrated = self.platt_calibrate(ensemble_score)
            ci = self.confidence_interval(predictions, weights)
            return AggregatedRisk(
                risk_score=calibrated,
                confidence_interval=ci,
                contributing_models=self.attribution(predictions, weights),
                requires_human_review=True,
                disagreement_analysis=self.analyze_disagreement(predictions),
                disagreement_score=d_score,
            )

        # Normal aggregation
        ensemble_score = self.weighted_average(predictions, weights)
        calibrated = self.platt_calibrate(ensemble_score)
        ci = self.confidence_interval(predictions, weights)

        return AggregatedRisk(
            risk_score=calibrated,
            confidence_interval=ci,
            contributing_models=self.attribution(predictions, weights),
            requires_human_review=False,
            disagreement_score=d_score,
        )


# ===========================================================================
# Tests
# ===========================================================================

@pytest.fixture
def aggregator():
    return EnsembleAggregator()


@pytest.fixture
def identity_calibration_aggregator():
    """Aggregator whose Platt scaling is approximately identity for mid-range scores."""
    # With a=0, b=0: platt(s) = 1/(1+exp(0)) = 0.5 for all s.
    # We want near-identity. Use a=-4, b=2: maps ~[0,1] through sigmoid.
    return EnsembleAggregator(platt_a=-4.0, platt_b=2.0)


class TestWeightComputation:
    """Tests for get_model_weights."""

    def test_default_weights_normalized(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        weights = aggregator.get_model_weights(preds)
        assert abs(sum(weights.values()) - 1.0) < 1e-9
        assert weights["claude-opus-4"] > weights["gpt-5.2"] > weights["gemini-3"]

    def test_single_model_gets_full_weight(self, aggregator, claude_crs_prediction_low):
        weights = aggregator.get_model_weights([claude_crs_prediction_low])
        assert weights["claude-opus-4"] == pytest.approx(1.0)

    def test_unknown_model_gets_fallback_weight(self, aggregator):
        unknown = SafetyPrediction(
            risk_score=0.5, confidence=0.7,
            severity_distribution={"grade_1": 0.25, "grade_2": 0.25, "grade_3": 0.25, "grade_4": 0.25},
            time_horizon=timedelta(hours=48),
            mechanistic_rationale="test",
            pathway_references=[], evidence_sources=[],
            model_id="llama-4", latency_ms=2000,
        )
        weights = aggregator.get_model_weights([unknown])
        assert "llama-4" in weights
        assert weights["llama-4"] == pytest.approx(1.0)


class TestWeightedAverage:
    """Tests for weighted_average computation."""

    def test_agreeing_models_produce_similar_score(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        weights = aggregator.get_model_weights(preds)
        avg = aggregator.weighted_average(preds, weights)
        # All scores are 0.10-0.15, weighted avg should be in that range
        assert 0.08 <= avg <= 0.18

    def test_high_risk_models_produce_high_score(self, aggregator, claude_crs_prediction_high, gpt_crs_prediction_high, gemini_crs_prediction_high):
        preds = [claude_crs_prediction_high, gpt_crs_prediction_high, gemini_crs_prediction_high]
        weights = aggregator.get_model_weights(preds)
        avg = aggregator.weighted_average(preds, weights)
        assert avg > 0.70

    def test_single_model_weighted_average_equals_score(self, aggregator, claude_crs_prediction_low):
        weights = aggregator.get_model_weights([claude_crs_prediction_low])
        avg = aggregator.weighted_average([claude_crs_prediction_low], weights)
        assert avg == pytest.approx(claude_crs_prediction_low.risk_score, abs=1e-9)


class TestDisagreementDetection:
    """Tests for disagreement_score and analyze_disagreement."""

    def test_agreeing_models_low_disagreement(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        d_score = aggregator.disagreement_score(preds)
        assert d_score < aggregator.disagreement_threshold

    def test_disagreeing_models_high_score(self, aggregator, disagreeing_predictions):
        d_score = aggregator.disagreement_score(disagreeing_predictions)
        assert d_score > aggregator.disagreement_threshold
        # 0.85 - 0.30 = 0.55
        assert d_score == pytest.approx(0.55)

    def test_single_prediction_zero_disagreement(self, aggregator, claude_crs_prediction_low):
        assert aggregator.disagreement_score([claude_crs_prediction_low]) == 0.0

    def test_disagreement_analysis_includes_all_models(self, aggregator, disagreeing_predictions):
        analysis = aggregator.analyze_disagreement(disagreeing_predictions)
        assert "claude-opus-4" in analysis
        assert "gpt-5.2" in analysis
        assert "gemini-3" in analysis


class TestPlattCalibration:
    """Tests for Platt scaling calibration."""

    def test_calibrated_score_in_valid_range(self, aggregator):
        for score in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
            calibrated = aggregator.platt_calibrate(score)
            assert 0.0 <= calibrated <= 1.0

    def test_monotonicity_with_negative_a(self):
        """With negative platt_a, higher raw scores should yield higher calibrated scores."""
        agg = EnsembleAggregator(platt_a=-3.0, platt_b=1.5)
        prev = 0.0
        for s in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
            cal = agg.platt_calibrate(s)
            assert cal >= prev
            prev = cal

    def test_identity_params_give_constant(self):
        """With a=0, b=0, calibration is constant 0.5."""
        agg = EnsembleAggregator(platt_a=0.0, platt_b=0.0)
        assert agg.platt_calibrate(0.1) == pytest.approx(0.5)
        assert agg.platt_calibrate(0.9) == pytest.approx(0.5)


class TestConfidenceInterval:
    """Tests for confidence_interval computation."""

    def test_ci_contains_mean(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        weights = aggregator.get_model_weights(preds)
        mean = aggregator.weighted_average(preds, weights)
        ci = aggregator.confidence_interval(preds, weights)
        assert ci[0] <= mean <= ci[1]

    def test_ci_bounds_valid(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        weights = aggregator.get_model_weights(preds)
        ci = aggregator.confidence_interval(preds, weights)
        assert 0.0 <= ci[0] <= ci[1] <= 1.0

    def test_single_model_narrow_ci(self, aggregator, claude_crs_prediction_low):
        weights = aggregator.get_model_weights([claude_crs_prediction_low])
        ci = aggregator.confidence_interval([claude_crs_prediction_low], weights)
        # Single model: default +/- 0.1
        assert ci[1] - ci[0] <= 0.25

    def test_disagreeing_models_wide_ci(self, aggregator, disagreeing_predictions):
        weights = aggregator.get_model_weights(disagreeing_predictions)
        ci = aggregator.confidence_interval(disagreeing_predictions, weights)
        # High disagreement should widen the CI
        assert ci[1] - ci[0] > 0.20


class TestFullAggregation:
    """Tests for the complete aggregate() method."""

    def test_agreeing_low_risk_not_flagged(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        result = aggregator.aggregate(preds)
        assert not result.requires_human_review
        assert result.risk_score > 0.0
        assert result.risk_score < 1.0
        assert result.confidence_interval[0] <= result.confidence_interval[1]

    def test_disagreeing_predictions_flagged(self, aggregator, disagreeing_predictions):
        result = aggregator.aggregate(disagreeing_predictions)
        assert result.requires_human_review
        assert result.disagreement_analysis is not None
        assert result.disagreement_score > aggregator.disagreement_threshold

    def test_high_risk_consensus_produces_high_score(self, identity_calibration_aggregator, claude_crs_prediction_high, gpt_crs_prediction_high, gemini_crs_prediction_high):
        preds = [claude_crs_prediction_high, gpt_crs_prediction_high, gemini_crs_prediction_high]
        result = identity_calibration_aggregator.aggregate(preds)
        # With near-identity calibration, high raw scores should stay high
        assert result.risk_score > 0.60

    def test_empty_predictions_raises(self, aggregator):
        with pytest.raises(ValueError, match="empty"):
            aggregator.aggregate([])

    def test_contributing_models_all_present(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        result = aggregator.aggregate(preds)
        assert "claude-opus-4" in result.contributing_models
        assert "gpt-5.2" in result.contributing_models
        assert "gemini-3" in result.contributing_models

    def test_weights_sum_to_one_in_output(self, aggregator, claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low):
        preds = [claude_crs_prediction_low, gpt_crs_prediction_low, gemini_crs_prediction_low]
        result = aggregator.aggregate(preds)
        assert abs(sum(result.contributing_models.values()) - 1.0) < 0.01
