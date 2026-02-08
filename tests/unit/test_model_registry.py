"""
Unit tests for src/models/model_registry.py and src/models/model_validation.py

Covers all 7 registered risk models with boundary conditions, edge cases,
and cross-model consistency checks.  Also tests the validation framework
functions.
"""

import math
import pytest

from src.models.model_registry import (
    MODEL_REGISTRY,
    RiskModel,
    bayesian_beta_binomial,
    compare_models,
    empirical_bayes,
    estimate_risk,
    frequentist_exact,
    kaplan_meier,
    list_models,
    predictive_posterior,
    random_effects_meta,
    wilson_score,
)
from src.models.model_validation import (
    brier_score,
    calibration_check,
    coverage_probability,
    leave_one_out_cv,
    model_comparison,
    sequential_prediction_test,
)


# ===========================================================================
# Helpers
# ===========================================================================

STANDARD_DATA = {"events": 2, "n": 47}
ZERO_EVENTS = {"events": 0, "n": 50}
ALL_EVENTS = {"events": 50, "n": 50}
SINGLE_PATIENT = {"events": 0, "n": 1}


def _check_result_schema(result: dict) -> None:
    """Assert the standardised result dict has all required keys."""
    assert "estimate_pct" in result
    assert "ci_low_pct" in result
    assert "ci_high_pct" in result
    assert "ci_width_pct" in result
    assert "method" in result
    assert "n_patients" in result
    assert "n_events" in result
    assert "metadata" in result
    assert isinstance(result["metadata"], dict)


def _check_bounds(result: dict) -> None:
    """Assert percentage bounds are reasonable."""
    assert result["ci_low_pct"] >= 0.0
    assert result["ci_high_pct"] <= 100.0
    assert result["ci_low_pct"] <= result["ci_high_pct"]
    assert result["ci_width_pct"] >= 0.0


# ===========================================================================
# Registry structure tests
# ===========================================================================


class TestModelRegistry:
    """Tests for the registry itself."""

    def test_registry_has_7_models(self):
        assert len(MODEL_REGISTRY) == 7

    def test_all_entries_are_risk_models(self):
        for model in MODEL_REGISTRY.values():
            assert isinstance(model, RiskModel)

    def test_all_ids_match_keys(self):
        for key, model in MODEL_REGISTRY.items():
            assert model.id == key

    def test_all_have_nonempty_descriptions(self):
        for model in MODEL_REGISTRY.values():
            assert len(model.description) > 10

    def test_all_have_nonempty_suitable_for(self):
        for model in MODEL_REGISTRY.values():
            assert len(model.suitable_for) > 0

    def test_all_have_callable_compute_fn(self):
        for model in MODEL_REGISTRY.values():
            assert callable(model.compute_fn)

    def test_list_models_returns_all(self):
        models = list_models()
        assert len(models) == 7
        ids = {m["id"] for m in models}
        assert ids == set(MODEL_REGISTRY.keys())


# ===========================================================================
# estimate_risk() and compare_models()
# ===========================================================================


class TestEstimateRisk:
    """Tests for the unified estimate_risk interface."""

    def test_unknown_model_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown model"):
            estimate_risk("nonexistent_model", STANDARD_DATA)

    def test_missing_required_keys_raises_value_error(self):
        with pytest.raises(ValueError, match="missing"):
            estimate_risk("bayesian_beta_binomial", {"events": 2})

    def test_known_model_returns_result(self):
        result = estimate_risk("bayesian_beta_binomial", STANDARD_DATA)
        _check_result_schema(result)
        _check_bounds(result)

    def test_compare_models_runs_compatible_models(self):
        comparison = compare_models(STANDARD_DATA)
        # Should run at least the 3 single-study models
        assert "bayesian_beta_binomial" in comparison["results"]
        assert "frequentist_exact" in comparison["results"]
        assert "wilson_score" in comparison["results"]
        assert len(comparison["summary"]) >= 3

    def test_compare_models_reports_errors_for_incompatible(self):
        comparison = compare_models(STANDARD_DATA)
        # Meta-analysis requires "studies", not "events"/"n"
        assert "random_effects_meta" in comparison["errors"]

    def test_compare_models_specific_ids(self):
        comparison = compare_models(
            STANDARD_DATA,
            model_ids=["bayesian_beta_binomial", "frequentist_exact"],
        )
        assert len(comparison["results"]) == 2
        assert len(comparison["errors"]) == 0


# ===========================================================================
# 1. Bayesian Beta-Binomial
# ===========================================================================


class TestBayesianBetaBinomial:
    """Tests for the Bayesian Beta-Binomial model."""

    def test_standard_case(self):
        result = bayesian_beta_binomial(STANDARD_DATA)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Bayesian Beta-Binomial"

    def test_zero_events(self):
        result = bayesian_beta_binomial(ZERO_EVENTS)
        assert result["estimate_pct"] < 5.0  # Should be low with Jeffreys prior
        assert result["ci_low_pct"] >= 0.0

    def test_all_events(self):
        result = bayesian_beta_binomial(ALL_EVENTS)
        assert result["estimate_pct"] > 90.0

    def test_single_patient_no_event(self):
        result = bayesian_beta_binomial(SINGLE_PATIENT)
        _check_bounds(result)

    def test_custom_prior(self):
        data = {"events": 2, "n": 47, "prior_alpha": 0.21, "prior_beta": 1.29}
        result = bayesian_beta_binomial(data)
        assert result["metadata"]["prior_alpha"] == 0.21
        assert result["metadata"]["prior_beta"] == 1.29

    def test_jeffreys_prior_default(self):
        result = bayesian_beta_binomial(STANDARD_DATA)
        assert result["metadata"]["prior_alpha"] == 0.5
        assert result["metadata"]["prior_beta"] == 0.5

    def test_zero_n_returns_prior(self):
        result = bayesian_beta_binomial({"events": 0, "n": 0})
        # With n=0, posterior = prior, so mean = alpha/(alpha+beta)
        assert result["estimate_pct"] == pytest.approx(50.0, abs=1.0)

    def test_events_exceeding_n_raises(self):
        with pytest.raises(ValueError):
            bayesian_beta_binomial({"events": 10, "n": 5})


# ===========================================================================
# 2. Frequentist Exact (Clopper-Pearson)
# ===========================================================================


class TestFrequentistExact:
    """Tests for the Clopper-Pearson exact CI."""

    def test_standard_case(self):
        result = frequentist_exact(STANDARD_DATA)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Clopper-Pearson Exact"

    def test_zero_events_ci_includes_zero(self):
        result = frequentist_exact(ZERO_EVENTS)
        assert result["ci_low_pct"] == 0.0
        assert result["estimate_pct"] == 0.0

    def test_all_events_ci_includes_100(self):
        result = frequentist_exact(ALL_EVENTS)
        assert result["ci_high_pct"] == 100.0
        assert result["estimate_pct"] == 100.0

    def test_zero_n(self):
        result = frequentist_exact({"events": 0, "n": 0})
        assert result["estimate_pct"] == 0.0
        assert result["ci_low_pct"] == 0.0
        assert result["ci_high_pct"] == 100.0

    def test_single_event(self):
        result = frequentist_exact({"events": 1, "n": 10})
        assert 0.0 < result["ci_low_pct"] < result["estimate_pct"]
        assert result["estimate_pct"] < result["ci_high_pct"] < 100.0

    def test_conservative_coverage(self):
        """Clopper-Pearson is known to be conservative (wide intervals)."""
        cp = frequentist_exact(STANDARD_DATA)
        ws = wilson_score(STANDARD_DATA)
        # CP intervals should generally be at least as wide as Wilson
        assert cp["ci_width_pct"] >= ws["ci_width_pct"] - 1.0  # Allow small tolerance

    def test_custom_alpha(self):
        result_90 = frequentist_exact({"events": 2, "n": 47, "alpha": 0.10})
        result_95 = frequentist_exact({"events": 2, "n": 47, "alpha": 0.05})
        # 90% CI should be narrower than 95% CI
        assert result_90["ci_width_pct"] < result_95["ci_width_pct"]


# ===========================================================================
# 3. Wilson Score
# ===========================================================================


class TestWilsonScore:
    """Tests for the Wilson score interval."""

    def test_standard_case(self):
        result = wilson_score(STANDARD_DATA)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Wilson Score"

    def test_zero_events(self):
        result = wilson_score(ZERO_EVENTS)
        # Wilson still gives a nonzero estimate (centre is adjusted)
        assert result["estimate_pct"] > 0.0
        assert result["ci_low_pct"] >= 0.0

    def test_all_events(self):
        result = wilson_score(ALL_EVENTS)
        # Wilson still gives an estimate below 100%
        assert result["estimate_pct"] < 100.0
        assert result["ci_high_pct"] <= 100.0

    def test_zero_n(self):
        result = wilson_score({"events": 0, "n": 0})
        assert result["n_patients"] == 0

    def test_large_n_converges_to_proportion(self):
        result = wilson_score({"events": 100, "n": 1000})
        assert result["estimate_pct"] == pytest.approx(10.0, abs=1.0)

    def test_continuity_correction(self):
        data_cc = {"events": 2, "n": 47, "continuity_correction": True}
        result_cc = wilson_score(data_cc)
        result_no = wilson_score(STANDARD_DATA)
        _check_bounds(result_cc)
        # CC interval should be at least as wide
        assert result_cc["ci_width_pct"] >= result_no["ci_width_pct"] - 0.1

    def test_ci_brackets_estimate(self):
        result = wilson_score({"events": 5, "n": 100})
        assert result["ci_low_pct"] < result["estimate_pct"]
        assert result["ci_high_pct"] > result["estimate_pct"]


# ===========================================================================
# 4. Random-Effects Meta-Analysis
# ===========================================================================


class TestRandomEffectsMeta:
    """Tests for the DerSimonian-Laird random-effects model."""

    @pytest.fixture
    def three_studies(self):
        return {
            "studies": [
                {"events": 0, "n": 5, "label": "Mackensen"},
                {"events": 1, "n": 20, "label": "Muller"},
                {"events": 1, "n": 37, "label": "Jin"},
            ]
        }

    @pytest.fixture
    def homogeneous_studies(self):
        return {
            "studies": [
                {"events": 5, "n": 100, "label": "A"},
                {"events": 6, "n": 120, "label": "B"},
                {"events": 4, "n": 80, "label": "C"},
            ]
        }

    def test_standard_case(self, three_studies):
        result = random_effects_meta(three_studies)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "DerSimonian-Laird Random Effects"

    def test_single_study_falls_back(self):
        data = {"studies": [{"events": 2, "n": 47}]}
        result = random_effects_meta(data)
        # Should fall back to exact binomial
        assert result["method"] == "Clopper-Pearson Exact"

    def test_empty_studies_raises(self):
        with pytest.raises(ValueError, match="At least one study"):
            random_effects_meta({"studies": []})

    def test_metadata_has_heterogeneity(self, three_studies):
        result = random_effects_meta(three_studies)
        assert "tau_squared" in result["metadata"]
        assert "i_squared" in result["metadata"]
        assert "cochran_q" in result["metadata"]

    def test_i_squared_between_0_and_1(self, three_studies):
        result = random_effects_meta(three_studies)
        assert 0.0 <= result["metadata"]["i_squared"] <= 1.0

    def test_homogeneous_studies_low_heterogeneity(self, homogeneous_studies):
        result = random_effects_meta(homogeneous_studies)
        # With similar rates, tau-squared should be near 0
        assert result["metadata"]["tau_squared"] < 0.1

    def test_study_weights_sum_to_one(self, three_studies):
        result = random_effects_meta(three_studies)
        weights = result["metadata"]["study_weights"]
        assert sum(weights) == pytest.approx(1.0, abs=0.01)

    def test_two_studies_works(self):
        data = {
            "studies": [
                {"events": 1, "n": 20},
                {"events": 2, "n": 30},
            ]
        }
        result = random_effects_meta(data)
        _check_result_schema(result)
        _check_bounds(result)

    def test_zero_events_all_studies(self):
        data = {
            "studies": [
                {"events": 0, "n": 10},
                {"events": 0, "n": 20},
                {"events": 0, "n": 30},
            ]
        }
        result = random_effects_meta(data)
        assert result["estimate_pct"] < 5.0  # Very low with all zeros


# ===========================================================================
# 5. Empirical Bayes Shrinkage
# ===========================================================================


class TestEmpiricalBayes:
    """Tests for the empirical Bayes shrinkage estimator."""

    @pytest.fixture
    def ae_data(self):
        return {
            "ae_types": [
                {"name": "CRS", "events": 2, "n": 47},
                {"name": "ICANS", "events": 0, "n": 47},
                {"name": "ICAHS", "events": 1, "n": 47},
            ],
            "target": "CRS",
        }

    def test_standard_case(self, ae_data):
        result = empirical_bayes(ae_data)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Empirical Bayes Shrinkage"

    def test_shrinkage_towards_grand_mean(self, ae_data):
        result = empirical_bayes(ae_data)
        raw_rate = 2 / 47 * 100
        grand_mean = ((2 + 0 + 1) / (47 * 3)) * 100
        # Shrunk estimate should be between raw rate and grand mean
        estimate = result["estimate_pct"]
        lo = min(raw_rate, grand_mean)
        hi = max(raw_rate, grand_mean)
        assert lo - 0.5 <= estimate <= hi + 0.5

    def test_unknown_target_raises(self):
        data = {
            "ae_types": [{"name": "CRS", "events": 2, "n": 47}],
            "target": "NONEXISTENT",
        }
        with pytest.raises(ValueError, match="not found"):
            empirical_bayes(data)

    def test_empty_ae_types_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            empirical_bayes({"ae_types": [], "target": "CRS"})

    def test_single_ae_type(self):
        data = {
            "ae_types": [{"name": "CRS", "events": 2, "n": 47}],
            "target": "CRS",
        }
        result = empirical_bayes(data)
        _check_result_schema(result)

    def test_metadata_has_shrinkage_factor(self, ae_data):
        result = empirical_bayes(ae_data)
        assert "shrinkage_factor" in result["metadata"]
        assert 0.0 <= result["metadata"]["shrinkage_factor"] <= 1.0

    def test_identical_rates_no_shrinkage(self):
        data = {
            "ae_types": [
                {"name": "A", "events": 5, "n": 100},
                {"name": "B", "events": 5, "n": 100},
                {"name": "C", "events": 5, "n": 100},
            ],
            "target": "A",
        }
        result = empirical_bayes(data)
        # When all rates are identical, estimate should be very close to raw
        assert result["estimate_pct"] == pytest.approx(5.0, abs=0.5)

    def test_manual_prior_weight(self):
        data = {
            "ae_types": [
                {"name": "CRS", "events": 10, "n": 100},
                {"name": "ICANS", "events": 0, "n": 100},
            ],
            "target": "CRS",
            "prior_weight": 0.5,
        }
        result = empirical_bayes(data)
        assert result["metadata"]["shrinkage_factor"] == 0.5


# ===========================================================================
# 6. Kaplan-Meier
# ===========================================================================


class TestKaplanMeier:
    """Tests for the Kaplan-Meier cumulative incidence estimator."""

    @pytest.fixture
    def standard_km_data(self):
        return {
            "times": [3, 7, 14, 21, 28, 30, 30, 30, 30, 30],
            "event_indicators": [True, True, True, False, False, False, False, False, False, False],
            "time_horizon": 30,
        }

    def test_standard_case(self, standard_km_data):
        result = kaplan_meier(standard_km_data)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Kaplan-Meier"

    def test_no_events_gives_zero_incidence(self):
        data = {
            "times": [10, 20, 30, 40, 50],
            "event_indicators": [False, False, False, False, False],
        }
        result = kaplan_meier(data)
        assert result["estimate_pct"] == 0.0

    def test_all_events_gives_100_incidence(self):
        data = {
            "times": [1, 2, 3, 4, 5],
            "event_indicators": [True, True, True, True, True],
        }
        result = kaplan_meier(data)
        assert result["estimate_pct"] == 100.0

    def test_empty_data_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            kaplan_meier({"times": [], "event_indicators": []})

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            kaplan_meier({"times": [1, 2, 3], "event_indicators": [True, False]})

    def test_early_horizon_gives_lower_incidence(self, standard_km_data):
        early = dict(standard_km_data)
        early["time_horizon"] = 5
        result_early = kaplan_meier(early)
        result_late = kaplan_meier(standard_km_data)
        assert result_early["estimate_pct"] <= result_late["estimate_pct"]

    def test_single_patient_event(self):
        data = {"times": [5], "event_indicators": [True]}
        result = kaplan_meier(data)
        assert result["estimate_pct"] == 100.0
        assert result["n_patients"] == 1
        assert result["n_events"] == 1

    def test_single_patient_censored(self):
        data = {"times": [5], "event_indicators": [False]}
        result = kaplan_meier(data)
        assert result["estimate_pct"] == 0.0

    def test_n_censored_in_metadata(self, standard_km_data):
        result = kaplan_meier(standard_km_data)
        assert "n_censored" in result["metadata"]
        assert result["metadata"]["n_censored"] == 7


# ===========================================================================
# 7. Predictive Posterior
# ===========================================================================


class TestPredictivePosterior:
    """Tests for the Bayesian predictive posterior model."""

    def test_standard_case(self):
        data = {"events": 2, "n": 47, "n_new": 50}
        result = predictive_posterior(data)
        _check_result_schema(result)
        _check_bounds(result)
        assert result["method"] == "Bayesian Predictive Posterior"

    def test_prediction_wider_than_posterior(self):
        """Predictive interval should be wider than the posterior CI
        because it accounts for sampling variability in the new study."""
        post_data = {"events": 2, "n": 47}
        pred_data = {"events": 2, "n": 47, "n_new": 47}
        posterior = bayesian_beta_binomial(post_data)
        predictive = predictive_posterior(pred_data)
        assert predictive["ci_width_pct"] >= posterior["ci_width_pct"]

    def test_zero_events_observed(self):
        data = {"events": 0, "n": 50, "n_new": 50}
        result = predictive_posterior(data)
        _check_bounds(result)
        assert result["estimate_pct"] < 10.0

    def test_all_events_observed(self):
        data = {"events": 50, "n": 50, "n_new": 50}
        result = predictive_posterior(data)
        _check_bounds(result)
        assert result["estimate_pct"] > 80.0

    def test_small_n_new(self):
        data = {"events": 2, "n": 47, "n_new": 5}
        result = predictive_posterior(data)
        _check_result_schema(result)

    def test_large_n_new(self):
        data = {"events": 2, "n": 47, "n_new": 200}
        result = predictive_posterior(data)
        _check_result_schema(result)

    def test_n_new_in_metadata(self):
        data = {"events": 2, "n": 47, "n_new": 100}
        result = predictive_posterior(data)
        assert result["metadata"]["n_new"] == 100

    def test_prediction_interval_events_in_metadata(self):
        data = {"events": 2, "n": 47, "n_new": 50}
        result = predictive_posterior(data)
        interval = result["metadata"]["prediction_interval_events"]
        assert isinstance(interval, tuple)
        assert interval[0] >= 0
        assert interval[1] <= 50


# ===========================================================================
# Cross-model consistency tests
# ===========================================================================


class TestCrossModelConsistency:
    """Tests verifying that different models produce broadly consistent results."""

    def test_all_single_study_models_agree_direction(self):
        """All models should agree that 0 events -> low rate, all events -> high."""
        for mid in ["bayesian_beta_binomial", "frequentist_exact", "wilson_score"]:
            low = estimate_risk(mid, ZERO_EVENTS)
            high = estimate_risk(mid, ALL_EVENTS)
            assert low["estimate_pct"] < high["estimate_pct"]

    def test_larger_sample_narrows_ci_for_all_models(self):
        small = {"events": 1, "n": 10}
        large = {"events": 10, "n": 100}
        for mid in ["bayesian_beta_binomial", "frequentist_exact", "wilson_score"]:
            r_small = estimate_risk(mid, small)
            r_large = estimate_risk(mid, large)
            assert r_large["ci_width_pct"] < r_small["ci_width_pct"]

    def test_estimates_within_reasonable_range(self):
        """All methods on the same data should give estimates within ~10pp."""
        estimates = []
        for mid in ["bayesian_beta_binomial", "frequentist_exact", "wilson_score"]:
            r = estimate_risk(mid, STANDARD_DATA)
            estimates.append(r["estimate_pct"])
        spread = max(estimates) - min(estimates)
        assert spread < 10.0  # Within 10 percentage points


# ===========================================================================
# Model Validation Framework
# ===========================================================================


class TestCalibrationCheck:
    """Tests for calibration_check()."""

    def test_perfect_calibration(self):
        predicted = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        observed = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        result = calibration_check(predicted, observed, n_bins=5)
        assert result["calibration_error"] < 0.05

    def test_bad_calibration(self):
        predicted = [0.1, 0.2, 0.3, 0.4, 0.5]
        observed = [0.9, 0.8, 0.7, 0.6, 0.5]
        result = calibration_check(predicted, observed, n_bins=5)
        assert result["calibration_error"] > 0.1

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            calibration_check([0.1, 0.2], [0.1])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            calibration_check([], [])


class TestBrierScore:
    """Tests for brier_score()."""

    def test_perfect_predictions(self):
        result = brier_score([1.0, 0.0, 1.0, 0.0], [1, 0, 1, 0])
        assert result["brier_score"] == 0.0

    def test_worst_predictions(self):
        result = brier_score([0.0, 1.0, 0.0, 1.0], [1, 0, 1, 0])
        assert result["brier_score"] == 1.0

    def test_constant_prediction(self):
        result = brier_score([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 0])
        assert result["brier_score"] == 0.25

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError):
            brier_score([0.5], [1, 0])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            brier_score([], [])

    def test_skill_score_positive_for_good_model(self):
        result = brier_score([0.9, 0.1, 0.8, 0.2], [1, 0, 1, 0])
        assert result["brier_skill_score"] > 0

    def test_interpretation_present(self):
        result = brier_score([0.5, 0.5], [1, 0])
        assert "interpretation" in result


class TestCoverageProbability:
    """Tests for coverage_probability()."""

    def test_all_covered(self):
        ci_list = [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0)]
        true_rates = [5.0, 5.0, 5.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == 1.0

    def test_none_covered(self):
        ci_list = [(0.0, 1.0), (0.0, 1.0), (0.0, 1.0)]
        true_rates = [50.0, 50.0, 50.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == 0.0

    def test_partial_coverage(self):
        ci_list = [(0.0, 10.0), (0.0, 1.0)]
        true_rates = [5.0, 50.0]
        result = coverage_probability(ci_list, true_rates)
        assert result["coverage_probability"] == 0.5

    def test_mismatched_raises(self):
        with pytest.raises(ValueError):
            coverage_probability([(0, 1)], [1, 2])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            coverage_probability([], [])

    def test_assessment_present(self):
        result = coverage_probability([(0, 10)], [5.0])
        assert "assessment" in result


class TestLeaveOneOutCV:
    """Tests for leave_one_out_cv()."""

    @pytest.fixture
    def five_studies(self):
        return [
            {"events": 0, "n": 10, "label": "A"},
            {"events": 1, "n": 20, "label": "B"},
            {"events": 2, "n": 30, "label": "C"},
            {"events": 1, "n": 25, "label": "D"},
            {"events": 3, "n": 50, "label": "E"},
        ]

    def test_basic_cv(self, five_studies):
        result = leave_one_out_cv(five_studies, random_effects_meta)
        assert result["n_folds"] == 5
        assert "rmse_pct" in result
        assert "mae_pct" in result

    def test_insufficient_studies_raises(self):
        with pytest.raises(ValueError, match="At least 2"):
            leave_one_out_cv(
                [{"events": 1, "n": 10}], random_effects_meta
            )

    def test_with_single_study_model(self, five_studies):
        result = leave_one_out_cv(five_studies, frequentist_exact)
        assert result["n_folds"] == 5


class TestModelComparison:
    """Tests for model_comparison()."""

    @pytest.fixture
    def comparison_studies(self):
        return [
            {"events": 0, "n": 10, "label": "A"},
            {"events": 1, "n": 20, "label": "B"},
            {"events": 2, "n": 30, "label": "C"},
            {"events": 1, "n": 25, "label": "D"},
        ]

    def test_basic_comparison(self, comparison_studies):
        model_fns = {
            "meta": random_effects_meta,
            "exact": frequentist_exact,
        }
        result = model_comparison(comparison_studies, model_fns)
        assert "summary" in result
        assert len(result["summary"]) == 2
        assert result["best_model"] is not None

    def test_summary_sorted_by_rmse(self, comparison_studies):
        model_fns = {
            "meta": random_effects_meta,
            "exact": frequentist_exact,
        }
        result = model_comparison(comparison_studies, model_fns)
        rmses = [s["rmse_pct"] for s in result["summary"]]
        assert rmses == sorted(rmses)


class TestSequentialPredictionTest:
    """Tests for sequential_prediction_test()."""

    @pytest.fixture
    def timeline(self):
        return [
            {"events": 0, "n": 5, "label": "T1"},
            {"events": 0, "n": 15, "label": "T2"},
            {"events": 1, "n": 12, "label": "T3"},
            {"events": 1, "n": 10, "label": "T4"},
            {"events": 2, "n": 30, "label": "T5"},
        ]

    def test_basic_sequential(self, timeline):
        result = sequential_prediction_test(timeline, frequentist_exact)
        assert result["n_steps"] == 4  # predict from T2..T5
        assert "rmse_pct" in result
        assert "improving" in result

    def test_insufficient_timepoints_raises(self):
        with pytest.raises(ValueError, match="At least 2"):
            sequential_prediction_test(
                [{"events": 1, "n": 10}], frequentist_exact
            )

    def test_steps_have_expected_fields(self, timeline):
        result = sequential_prediction_test(timeline, frequentist_exact)
        for step in result["steps"]:
            assert "true_rate_pct" in step
            assert "predicted_pct" in step
            assert "covered" in step
