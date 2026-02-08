"""
Unit tests for src/models/mitigation_model.py

Tests the correlated RR combination formula, multi-strategy greedy combination,
correlation lookups, Monte Carlo simulation, high-level mitigated risk
calculation, and the mitigation strategy registry.
"""

import pytest

from src.models.mitigation_model import (
    MITIGATION_STRATEGIES,
    MitigationResult,
    calculate_mitigated_risk,
    combine_correlated_rr,
    combine_multiple_rrs,
    get_mitigation_correlation,
    monte_carlo_mitigated_risk,
)


# ============================================================================
# combine_correlated_rr()
# ============================================================================


class TestCombineCorrelatedRR:
    """Tests for the pairwise geometric interpolation formula."""

    def test_rho_zero_is_multiplicative(self):
        """rho=0 (independent) should give purely multiplicative combination."""
        rr_a, rr_b = 0.5, 0.4
        result = combine_correlated_rr(rr_a, rr_b, rho=0.0)
        assert result == pytest.approx(rr_a * rr_b, rel=1e-9)

    def test_rho_one_is_min(self):
        """rho=1 (fully redundant) should give min(rr_a, rr_b)."""
        rr_a, rr_b = 0.5, 0.4
        result = combine_correlated_rr(rr_a, rr_b, rho=1.0)
        assert result == pytest.approx(min(rr_a, rr_b), rel=1e-9)

    def test_intermediate_rho_is_between_multiplicative_and_min(self):
        """For 0 < rho < 1, result should be between multiplicative and min."""
        rr_a, rr_b = 0.5, 0.4
        multiplicative = rr_a * rr_b  # 0.20
        floor = min(rr_a, rr_b)       # 0.40

        result = combine_correlated_rr(rr_a, rr_b, rho=0.5)
        assert multiplicative < result < floor

    def test_negative_rr_a_raises_valueerror(self):
        """Negative relative risk for mitigation A should raise."""
        with pytest.raises(ValueError, match="non-negative"):
            combine_correlated_rr(-0.1, 0.5, rho=0.3)

    def test_negative_rr_b_raises_valueerror(self):
        """Negative relative risk for mitigation B should raise."""
        with pytest.raises(ValueError, match="non-negative"):
            combine_correlated_rr(0.5, -0.2, rho=0.3)

    def test_rho_below_zero_raises_valueerror(self):
        """rho < 0 is outside the valid range."""
        with pytest.raises(ValueError, match="rho"):
            combine_correlated_rr(0.5, 0.4, rho=-0.1)

    def test_rho_above_one_raises_valueerror(self):
        """rho > 1 is outside the valid range."""
        with pytest.raises(ValueError, match="rho"):
            combine_correlated_rr(0.5, 0.4, rho=1.1)

    def test_identical_rr_values(self):
        """With identical RRs, rho=0 gives rr^2 and rho=1 gives rr."""
        rr = 0.6
        assert combine_correlated_rr(rr, rr, rho=0.0) == pytest.approx(rr * rr, rel=1e-9)
        assert combine_correlated_rr(rr, rr, rho=1.0) == pytest.approx(rr, rel=1e-9)

    def test_rr_of_one_is_neutral(self):
        """A mitigation with RR=1 (no effect) should not change the other."""
        result = combine_correlated_rr(0.5, 1.0, rho=0.0)
        assert result == pytest.approx(0.5, rel=1e-9)


# ============================================================================
# combine_multiple_rrs()
# ============================================================================


class TestCombineMultipleRRs:
    """Tests for the greedy multi-strategy RR combination."""

    def test_single_strategy_returns_unchanged(self):
        """A single strategy should return its RR as-is."""
        result = combine_multiple_rrs(["tocilizumab"], [0.45])
        assert result == pytest.approx(0.45, rel=1e-9)

    def test_two_uncorrelated_strategies_multiplicative(self):
        """Two strategies with no known correlation should combine multiplicatively."""
        # dose-reduction and lymphodepletion-modification have no entry
        # in the correlation matrix, so rho=0.
        result = combine_multiple_rrs(
            ["dose-reduction", "lymphodepletion-modification"],
            [0.15, 0.85],
        )
        expected = 0.15 * 0.85
        assert result == pytest.approx(expected, rel=1e-6)

    def test_two_correlated_strategies_greater_than_multiplicative(self):
        """With rho > 0, the combined RR should be larger (less effective)
        than the purely multiplicative combination."""
        ids = ["anakinra", "tocilizumab"]  # rho = 0.4
        rrs = [0.65, 0.45]
        result = combine_multiple_rrs(ids, rrs)
        multiplicative = 0.65 * 0.45
        assert result > multiplicative

    def test_empty_lists_raise_valueerror(self):
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError, match="At least one"):
            combine_multiple_rrs([], [])

    def test_mismatched_lengths_raise_valueerror(self):
        """Mismatched list lengths should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            combine_multiple_rrs(["a", "b"], [0.5])

    def test_three_strategies_combined(self):
        """Combining three strategies should produce a value between 0 and 1."""
        ids = ["tocilizumab", "corticosteroids", "anakinra"]
        rrs = [0.45, 0.55, 0.65]
        result = combine_multiple_rrs(ids, rrs)
        assert 0.0 < result < 1.0

    def test_result_less_than_or_equal_to_all_individual_rrs(self):
        """The combined RR should never exceed the minimum individual RR
        (at worst, all mitigations are fully redundant)."""
        ids = ["tocilizumab", "anakinra"]
        rrs = [0.45, 0.65]
        result = combine_multiple_rrs(ids, rrs)
        assert result <= min(rrs) + 1e-9  # small tolerance for float math


# ============================================================================
# get_mitigation_correlation()
# ============================================================================


class TestGetMitigationCorrelation:
    """Tests for the correlation lookup function."""

    def test_known_pair_anakinra_tocilizumab(self):
        """Known pair should return the expected correlation value."""
        assert get_mitigation_correlation("anakinra", "tocilizumab") == pytest.approx(0.4)

    def test_known_pair_corticosteroids_tocilizumab(self):
        assert get_mitigation_correlation("corticosteroids", "tocilizumab") == pytest.approx(0.5)

    def test_known_pair_anakinra_corticosteroids(self):
        assert get_mitigation_correlation("anakinra", "corticosteroids") == pytest.approx(0.3)

    def test_unknown_pair_returns_zero(self):
        """Unknown pairs (independent mechanisms) should return 0.0."""
        assert get_mitigation_correlation("dose-reduction", "tocilizumab") == 0.0

    def test_order_does_not_matter(self):
        """Correlation lookup should be symmetric."""
        assert get_mitigation_correlation("anakinra", "tocilizumab") == (
            get_mitigation_correlation("tocilizumab", "anakinra")
        )

    def test_completely_unknown_ids_return_zero(self):
        """IDs not in the registry at all should return 0.0."""
        assert get_mitigation_correlation("unknown_drug_a", "unknown_drug_b") == 0.0


# ============================================================================
# monte_carlo_mitigated_risk()
# ============================================================================


class TestMonteCarloMitigatedRisk:
    """Tests for the Monte Carlo simulation of mitigated risk."""

    def test_returns_expected_keys(self):
        """Result dict should have the expected keys."""
        result = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=1000,
            seed=42,
        )
        for key in ("mean", "p2_5", "p97_5", "median", "n_samples"):
            assert key in result

    def test_mean_close_to_analytical(self):
        """MC mean should be close to the analytical estimate (within 2pp
        for 5000 samples).

        Analytical: baseline_mean * combined_rr
        baseline_mean = 1.21 / (1.21 + 47.29) = 0.02494
        combined_rr for tocilizumab alone = 0.45
        expected mitigated risk ~ 0.01122
        """
        result = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=5000,
            seed=42,
        )
        analytical_approx = (1.21 / (1.21 + 47.29)) * 0.45
        assert abs(result["mean"] - analytical_approx) < 0.02  # within 2pp

    def test_ci_brackets_mean(self):
        """The 95% interval should bracket the mean."""
        result = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=5000,
            seed=42,
        )
        assert result["p2_5"] <= result["mean"]
        assert result["p97_5"] >= result["mean"]

    def test_seed_reproducibility(self):
        """Same seed should produce identical results."""
        kwargs = dict(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=2000,
            seed=12345,
        )
        r1 = monte_carlo_mitigated_risk(**kwargs)
        r2 = monte_carlo_mitigated_risk(**kwargs)
        assert r1["mean"] == r2["mean"]
        assert r1["median"] == r2["median"]

    def test_different_seeds_produce_different_results(self):
        """Different seeds should (almost certainly) produce different means."""
        base = dict(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=2000,
        )
        r1 = monte_carlo_mitigated_risk(**base, seed=1)
        r2 = monte_carlo_mitigated_risk(**base, seed=999)
        assert r1["mean"] != r2["mean"]

    def test_multiple_mitigations_lower_risk(self):
        """Adding more mitigations should generally lower the mean risk."""
        single = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=5000,
            seed=42,
        )
        double = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab", "dose-reduction"],
            n_samples=5000,
            seed=42,
        )
        assert double["mean"] < single["mean"]

    def test_all_values_non_negative(self):
        """All output values should be non-negative."""
        result = monte_carlo_mitigated_risk(
            baseline_alpha=1.21,
            baseline_beta=47.29,
            mitigation_ids=["tocilizumab"],
            n_samples=1000,
            seed=42,
        )
        assert result["mean"] >= 0.0
        assert result["p2_5"] >= 0.0
        assert result["p97_5"] >= 0.0
        assert result["median"] >= 0.0


# ============================================================================
# calculate_mitigated_risk()
# ============================================================================


class TestCalculateMitigatedRisk:
    """Tests for the high-level convenience function."""

    def test_returns_crs_and_icans_keys(self):
        """Result must contain 'crs' and 'icans' keys."""
        result = calculate_mitigated_risk(
            baseline_crs=0.021,
            baseline_icans=0.015,
            selected_ids=["tocilizumab"],
        )
        assert "crs" in result
        assert "icans" in result

    def test_mitigated_risk_less_than_baseline(self):
        """Mitigated risk should be less than or equal to baseline risk."""
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["tocilizumab", "corticosteroids"],
        )
        assert result["crs"].mitigated_risk <= result["crs"].baseline_risk
        assert result["icans"].mitigated_risk <= result["icans"].baseline_risk

    def test_selected_mitigations_reflected(self):
        """The CRS result should list tocilizumab (which targets CRS)
        and the ICANS result should list corticosteroids (which targets ICANS)."""
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["tocilizumab", "corticosteroids"],
        )
        assert "tocilizumab" in result["crs"].selected_mitigations
        assert "corticosteroids" in result["icans"].selected_mitigations

    def test_no_applicable_mitigations_returns_baseline(self):
        """If no selected mitigations target a given AE, the mitigated risk
        should equal the baseline."""
        # corticosteroids only targets ICANS, not CRS
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["corticosteroids"],
        )
        assert result["crs"].mitigated_risk == pytest.approx(0.14, rel=1e-9)
        assert result["crs"].combined_rr == pytest.approx(1.0, rel=1e-9)

    def test_anakinra_targets_both_crs_and_icans(self):
        """Anakinra targets both CRS and ICANS, so it should appear in both results."""
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["anakinra"],
        )
        assert "anakinra" in result["crs"].selected_mitigations
        assert "anakinra" in result["icans"].selected_mitigations

    def test_result_types_are_mitigation_result(self):
        """CRS and ICANS results should be MitigationResult instances."""
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["tocilizumab"],
        )
        assert isinstance(result["crs"], MitigationResult)
        assert isinstance(result["icans"], MitigationResult)

    def test_returns_selected_strategies_list(self):
        """Result should include the full strategy objects."""
        result = calculate_mitigated_risk(
            baseline_crs=0.14,
            baseline_icans=0.12,
            selected_ids=["tocilizumab", "corticosteroids"],
        )
        assert "selected_strategies" in result
        assert len(result["selected_strategies"]) == 2


# ============================================================================
# MITIGATION_STRATEGIES registry
# ============================================================================


class TestMitigationStrategies:
    """Tests for the mitigation strategy registry."""

    def test_five_strategies_present(self):
        assert len(MITIGATION_STRATEGIES) == 5

    def test_expected_ids(self):
        expected = {
            "tocilizumab",
            "corticosteroids",
            "anakinra",
            "dose-reduction",
            "lymphodepletion-modification",
        }
        assert set(MITIGATION_STRATEGIES.keys()) == expected

    @pytest.mark.parametrize("strategy_id", list(MITIGATION_STRATEGIES.keys()))
    def test_has_required_fields(self, strategy_id):
        """Each strategy must have id, name, mechanism, target_aes,
        relative_risk, confidence_interval, evidence_level."""
        s = MITIGATION_STRATEGIES[strategy_id]
        assert s.id == strategy_id
        assert isinstance(s.name, str) and len(s.name) > 0
        assert isinstance(s.mechanism, str) and len(s.mechanism) > 0
        assert isinstance(s.target_aes, list) and len(s.target_aes) > 0
        assert isinstance(s.relative_risk, float)
        assert isinstance(s.confidence_interval, tuple) and len(s.confidence_interval) == 2
        assert isinstance(s.evidence_level, str)

    @pytest.mark.parametrize("strategy_id", list(MITIGATION_STRATEGIES.keys()))
    def test_rr_between_0_and_1(self, strategy_id):
        """All relative risks should be in (0, 1] for protective strategies."""
        s = MITIGATION_STRATEGIES[strategy_id]
        assert 0.0 < s.relative_risk <= 1.0

    @pytest.mark.parametrize("strategy_id", list(MITIGATION_STRATEGIES.keys()))
    def test_evidence_level_is_valid(self, strategy_id):
        """Evidence level must be one of the allowed strings."""
        valid_levels = {"Strong", "Moderate", "Limited"}
        s = MITIGATION_STRATEGIES[strategy_id]
        assert s.evidence_level in valid_levels

    @pytest.mark.parametrize("strategy_id", list(MITIGATION_STRATEGIES.keys()))
    def test_ci_low_less_than_ci_high(self, strategy_id):
        """CI lower bound must be less than upper bound."""
        s = MITIGATION_STRATEGIES[strategy_id]
        assert s.confidence_interval[0] < s.confidence_interval[1]

    @pytest.mark.parametrize("strategy_id", list(MITIGATION_STRATEGIES.keys()))
    def test_rr_within_ci(self, strategy_id):
        """Point estimate of RR should be within its CI."""
        s = MITIGATION_STRATEGIES[strategy_id]
        assert s.confidence_interval[0] <= s.relative_risk <= s.confidence_interval[1]
