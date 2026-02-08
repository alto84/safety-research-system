"""
Unit tests for src/models/model_validation.py

Tests the calibration check, Brier score, and coverage probability functions
that form the model validation framework.
"""

import math

import pytest

from src.models.model_validation import (
    brier_score,
    calibration_check,
    coverage_probability,
)


# ============================================================================
# calibration_check()
# ============================================================================


class TestCalibrationCheck:
    """Tests for the calibration diagnostic function."""

    def test_perfect_calibration(self):
        """When predictions exactly match observations, calibration error should
        be zero (or very close to it)."""
        predicted = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        observed = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = calibration_check(predicted, observed, n_bins=10)
        assert result["calibration_error"] < 0.01

    def test_terrible_calibration(self):
        """When predictions are all 0 but all outcomes are 1, error should be large."""
        predicted = [0.05] * 20
        observed = [1.0] * 20
        result = calibration_check(predicted, observed, n_bins=5)
        assert result["calibration_error"] > 0.5

    def test_returns_expected_keys(self):
        """Result should contain bins, calibration_error, n_bins_populated, n_total."""
        result = calibration_check([0.5, 0.6], [0, 1], n_bins=5)
        assert "bins" in result
        assert "calibration_error" in result
        assert "n_bins_populated" in result
        assert "n_total" in result

    def test_n_total_matches_input(self):
        """n_total should equal the length of the input lists."""
        predicted = [0.1, 0.2, 0.3, 0.4, 0.5]
        observed = [0, 0, 1, 0, 1]
        result = calibration_check(predicted, observed, n_bins=5)
        assert result["n_total"] == 5

    def test_bins_populated_leq_n_bins(self):
        """Number of populated bins should not exceed n_bins."""
        predicted = [0.1, 0.2, 0.3, 0.4, 0.5]
        observed = [0, 0, 1, 0, 1]
        result = calibration_check(predicted, observed, n_bins=10)
        assert result["n_bins_populated"] <= 10

    def test_mismatched_lengths_raises_valueerror(self):
        """Inputs of different lengths should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            calibration_check([0.1, 0.2], [0])

    def test_empty_inputs_raises_valueerror(self):
        """Empty inputs should raise ValueError."""
        with pytest.raises(ValueError, match="At least one"):
            calibration_check([], [])

    def test_single_observation(self):
        """Should handle a single observation without error."""
        result = calibration_check([0.5], [1.0], n_bins=10)
        assert result["n_total"] == 1

    def test_calibration_error_nonnegative(self):
        """Calibration error should always be non-negative."""
        predicted = [0.1, 0.3, 0.5, 0.7, 0.9]
        observed = [0, 0, 1, 1, 1]
        result = calibration_check(predicted, observed)
        assert result["calibration_error"] >= 0.0

    def test_bin_entries_have_required_keys(self):
        """Each bin should have bin_center, mean_predicted, mean_observed, and n."""
        predicted = [0.1, 0.3, 0.5, 0.7, 0.9]
        observed = [0, 0, 1, 1, 1]
        result = calibration_check(predicted, observed, n_bins=5)
        for b in result["bins"]:
            assert "bin_center" in b
            assert "mean_predicted" in b
            assert "mean_observed" in b
            assert "n" in b

    def test_all_predictions_in_same_bin(self):
        """When all predictions fall in the same bin, only 1 bin should be populated."""
        predicted = [0.51, 0.52, 0.53, 0.54, 0.55]
        observed = [0, 1, 0, 1, 1]
        result = calibration_check(predicted, observed, n_bins=10)
        assert result["n_bins_populated"] == 1


# ============================================================================
# brier_score()
# ============================================================================


class TestBrierScore:
    """Tests for the Brier score (mean squared prediction error)."""

    def test_perfect_predictions_score_zero(self):
        """Perfect binary predictions should yield a Brier score of 0."""
        predictions = [0.0, 0.0, 1.0, 1.0]
        outcomes = [0, 0, 1, 1]
        result = brier_score(predictions, outcomes)
        assert result["brier_score"] == pytest.approx(0.0, abs=1e-6)

    def test_worst_predictions_score_one(self):
        """Maximally wrong predictions should yield a Brier score of 1."""
        predictions = [1.0, 1.0, 0.0, 0.0]
        outcomes = [0, 0, 1, 1]
        result = brier_score(predictions, outcomes)
        assert result["brier_score"] == pytest.approx(1.0, abs=1e-6)

    def test_known_value(self):
        """Manual calculation: predictions [0.2, 0.8], outcomes [0, 1].
        BS = ((0.2-0)^2 + (0.8-1)^2) / 2 = (0.04 + 0.04) / 2 = 0.04."""
        result = brier_score([0.2, 0.8], [0, 1])
        assert result["brier_score"] == pytest.approx(0.04, abs=1e-6)

    def test_returns_expected_keys(self):
        """Result should contain brier_score, reference_score, brier_skill_score,
        n, base_rate, interpretation."""
        result = brier_score([0.5, 0.5], [0, 1])
        assert "brier_score" in result
        assert "reference_score" in result
        assert "brier_skill_score" in result
        assert "n" in result
        assert "base_rate" in result
        assert "interpretation" in result

    def test_reference_score_is_base_rate_variance(self):
        """Reference score should be p*(1-p) where p = base rate."""
        predictions = [0.3, 0.4, 0.5]
        outcomes = [0, 0, 1]  # base rate = 1/3
        result = brier_score(predictions, outcomes)
        base = 1 / 3
        expected_ref = base * (1 - base)
        assert result["reference_score"] == pytest.approx(expected_ref, abs=1e-4)

    def test_brier_skill_score_perfect(self):
        """Perfect predictions should give skill score = 1."""
        result = brier_score([0.0, 1.0, 0.0, 1.0], [0, 1, 0, 1])
        assert result["brier_skill_score"] == pytest.approx(1.0, abs=1e-6)

    def test_brier_skill_score_no_skill(self):
        """Predicting the base rate for everyone should give skill = 0."""
        outcomes = [0, 0, 0, 1, 1]  # base rate = 0.4
        predictions = [0.4, 0.4, 0.4, 0.4, 0.4]
        result = brier_score(predictions, outcomes)
        assert abs(result["brier_skill_score"]) < 0.01

    def test_mismatched_lengths_raises_valueerror(self):
        """Inputs of different lengths should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            brier_score([0.5], [0, 1])

    def test_empty_inputs_raises_valueerror(self):
        """Empty inputs should raise ValueError."""
        with pytest.raises(ValueError, match="At least one"):
            brier_score([], [])

    def test_brier_score_bounded_0_1(self):
        """Brier score should be between 0 and 1 for valid inputs."""
        predictions = [0.1, 0.4, 0.6, 0.9, 0.3]
        outcomes = [0, 0, 1, 1, 0]
        result = brier_score(predictions, outcomes)
        assert 0.0 <= result["brier_score"] <= 1.0

    def test_interpretation_excellent(self):
        """Near-perfect predictions should yield 'Excellent calibration'."""
        result = brier_score([0.01, 0.01, 0.99, 0.99], [0, 0, 1, 1])
        assert "Excellent" in result["interpretation"]

    def test_interpretation_poor(self):
        """Bad predictions should yield a poor calibration interpretation."""
        result = brier_score([0.8, 0.8, 0.2, 0.2], [0, 0, 1, 1])
        assert "Poor" in result["interpretation"] or "poor" in result["interpretation"]

    def test_all_zero_outcomes(self):
        """With all zero outcomes, reference_score should be 0."""
        result = brier_score([0.1, 0.2, 0.3], [0, 0, 0])
        assert result["reference_score"] == pytest.approx(0.0, abs=1e-6)
        assert result["base_rate"] == pytest.approx(0.0, abs=1e-6)


# ============================================================================
# coverage_probability()
# ============================================================================


class TestCoverageProbability:
    """Tests for the confidence interval coverage assessment."""

    def test_all_covered(self):
        """When all true rates fall within their CIs, coverage should be 1.0."""
        ci_list = [(1.0, 5.0), (2.0, 8.0), (0.5, 3.0)]
        true_rates = [3.0, 5.0, 1.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == pytest.approx(1.0, abs=1e-6)

    def test_none_covered(self):
        """When no true rates fall within their CIs, coverage should be 0.0."""
        ci_list = [(1.0, 2.0), (3.0, 4.0), (5.0, 6.0)]
        true_rates = [10.0, 10.0, 10.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == pytest.approx(0.0, abs=1e-6)

    def test_half_covered(self):
        """When half are covered, coverage should be 0.5."""
        ci_list = [(1.0, 5.0), (1.0, 5.0)]
        true_rates = [3.0, 10.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == pytest.approx(0.5, abs=1e-6)

    def test_returns_expected_keys(self):
        """Result should contain coverage_probability, n_covered, n_total,
        mean_ci_width, details, assessment."""
        result = coverage_probability([(1.0, 5.0)], [3.0])
        assert "coverage_probability" in result
        assert "n_covered" in result
        assert "n_total" in result
        assert "mean_ci_width" in result
        assert "details" in result
        assert "assessment" in result

    def test_n_covered_matches(self):
        """n_covered should match the count of true rates within CIs."""
        ci_list = [(0.0, 5.0), (0.0, 5.0), (0.0, 5.0)]
        true_rates = [3.0, 6.0, 4.0]  # 2 covered
        result = coverage_probability(ci_list, true_rates)
        assert result["n_covered"] == 2

    def test_n_total_matches_input(self):
        """n_total should match the input length."""
        ci_list = [(0.0, 5.0), (0.0, 5.0)]
        true_rates = [3.0, 4.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["n_total"] == 2

    def test_mean_ci_width_correct(self):
        """mean_ci_width should be the average of (ci_high - ci_low)."""
        ci_list = [(0.0, 10.0), (2.0, 8.0)]  # widths: 10, 6
        true_rates = [5.0, 5.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["mean_ci_width"] == pytest.approx(8.0, abs=0.01)

    def test_details_length_matches(self):
        """details list should have the same length as input."""
        ci_list = [(0.0, 5.0), (2.0, 8.0), (3.0, 9.0)]
        true_rates = [3.0, 5.0, 10.0]
        result = coverage_probability(ci_list, true_rates)
        assert len(result["details"]) == 3

    def test_details_have_required_keys(self):
        """Each detail entry should have ci_low, ci_high, true_rate, covered."""
        result = coverage_probability([(0.0, 5.0)], [3.0])
        detail = result["details"][0]
        assert "ci_low" in detail
        assert "ci_high" in detail
        assert "true_rate" in detail
        assert "covered" in detail

    def test_boundary_value_covered(self):
        """True rate exactly at CI boundary should be counted as covered."""
        result = coverage_probability([(1.0, 5.0)], [5.0])
        assert result["coverage_probability"] == pytest.approx(1.0, abs=1e-6)

    def test_mismatched_lengths_raises_valueerror(self):
        """Inputs of different lengths should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            coverage_probability([(0.0, 5.0)], [3.0, 4.0])

    def test_empty_inputs_raises_valueerror(self):
        """Empty inputs should raise ValueError."""
        with pytest.raises(ValueError, match="At least one"):
            coverage_probability([], [])

    def test_assessment_consistent_with_95pct(self):
        """When coverage is close to 95%, assessment should say consistent."""
        # Build a scenario where 19 out of 20 are covered (95%)
        ci_list = [(0.0, 10.0)] * 19 + [(0.0, 10.0)]
        true_rates = [5.0] * 19 + [15.0]  # 19 covered, 1 not
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == pytest.approx(0.95, abs=0.01)
        assert "95%" in result["assessment"] or "Consistent" in result["assessment"]

    def test_under_coverage_assessment(self):
        """When coverage is well below 95%, assessment should mention under-coverage."""
        # Only 5 out of 20 covered = 25%
        ci_list = [(0.0, 1.0)] * 20
        true_rates = [0.5] * 5 + [5.0] * 15
        result = coverage_probability(ci_list, true_rates)
        assert "nder" in result["assessment"].lower() or "narrow" in result["assessment"].lower()

    def test_over_coverage_assessment(self):
        """When coverage is 100% with many observations, assessment should
        mention over-coverage."""
        ci_list = [(0.0, 100.0)] * 40
        true_rates = [50.0] * 40
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == pytest.approx(1.0, abs=1e-6)
        assert "ver" in result["assessment"].lower() or "wide" in result["assessment"].lower()
