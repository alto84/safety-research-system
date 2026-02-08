"""
Unit tests for src/models/faers_signal.py

Tests the pure-computation functions: PRR, ROR, EBGM, and signal classification.
Does NOT test the async openFDA API integration (that belongs in integration tests).
"""

import math

import pytest

from src.models.faers_signal import (
    classify_signal,
    compute_ebgm,
    compute_prr,
    compute_ror,
)


# ============================================================================
# compute_prr()
# ============================================================================


class TestComputePRR:
    """Tests for the Proportional Reporting Ratio computation."""

    def test_known_2x2_table(self):
        """Verify PRR with a known 2x2 table.

        a=50, b=950, c=200, d=18800
        rate_drug = 50/1000 = 0.05
        rate_other = 200/19000 ~ 0.01053
        PRR = 0.05 / 0.01053 ~ 4.75
        """
        prr, ci_low, ci_high = compute_prr(a=50, b=950, c=200, d=18800)
        assert prr == pytest.approx(4.75, rel=0.01)
        assert ci_low > 0.0
        assert ci_high > prr

    def test_zero_denominator_returns_zeros(self):
        """When (a+b)=0 or (c+d)=0, should return (0, 0, 0)."""
        assert compute_prr(0, 0, 100, 1000) == (0.0, 0.0, 0.0)
        assert compute_prr(10, 90, 0, 0) == (0.0, 0.0, 0.0)

    def test_c_is_zero_returns_zeros(self):
        """When c=0, the comparator rate is 0 and PRR is undefined."""
        assert compute_prr(10, 90, 0, 10000) == (0.0, 0.0, 0.0)

    def test_prr_greater_than_1_for_disproportionate(self):
        """When the drug has higher AE reporting rate, PRR should exceed 1."""
        prr, _, _ = compute_prr(a=100, b=900, c=50, d=19000)
        assert prr > 1.0

    def test_prr_less_than_1_when_drug_rate_lower(self):
        """When the drug has a lower reporting rate, PRR < 1."""
        prr, _, _ = compute_prr(a=5, b=995, c=200, d=18800)
        assert prr < 1.0

    def test_ci_lower_is_less_than_ci_upper(self):
        """CI lower bound should be less than upper bound."""
        prr, ci_low, ci_high = compute_prr(a=30, b=970, c=100, d=18900)
        assert ci_low < ci_high

    def test_a_zero_gives_prr_zero(self):
        """If a=0 (no drug-AE reports), PRR should be 0 or return zeros."""
        prr, ci_low, ci_high = compute_prr(a=0, b=1000, c=100, d=18900)
        # rate_drug = 0, so prr = 0
        assert prr == pytest.approx(0.0)

    def test_large_a_gives_large_prr(self):
        """When a is large relative to the expected count, PRR should be large."""
        prr, _, _ = compute_prr(a=500, b=500, c=10, d=19000)
        assert prr > 10.0


# ============================================================================
# compute_ror()
# ============================================================================


class TestComputeROR:
    """Tests for the Reporting Odds Ratio computation."""

    def test_known_values(self):
        """Verify ROR with a known 2x2 table.

        a=50, b=950, c=200, d=18800
        ROR = (50 * 18800) / (950 * 200) = 940000 / 190000 ~ 4.947
        """
        ror, ci_low, ci_high = compute_ror(a=50, b=950, c=200, d=18800)
        assert ror == pytest.approx(4.947, rel=0.01)

    def test_ci_computation(self):
        """CI should bracket the point estimate."""
        ror, ci_low, ci_high = compute_ror(a=50, b=950, c=200, d=18800)
        assert ci_low < ror < ci_high

    def test_b_zero_returns_zeros(self):
        """When b=0, ROR is undefined."""
        assert compute_ror(10, 0, 100, 1000) == (0.0, 0.0, 0.0)

    def test_c_zero_returns_zeros(self):
        """When c=0, ROR is undefined."""
        assert compute_ror(10, 90, 0, 1000) == (0.0, 0.0, 0.0)

    def test_ror_greater_than_1_for_signal(self):
        """ROR > 1 when the drug-AE pair is over-represented."""
        ror, _, _ = compute_ror(a=100, b=900, c=50, d=19000)
        assert ror > 1.0

    def test_d_zero_gives_ror_zero_or_zeros(self):
        """When d=0, either ROR is 0 or we get (0, 0, 0) due to log issue."""
        ror, ci_low, ci_high = compute_ror(a=10, b=90, c=100, d=0)
        # a*d = 0, so ror = 0
        assert ror == pytest.approx(0.0)

    def test_ci_width_decreases_with_more_data(self):
        """Larger counts should produce narrower CIs."""
        _, ci_low_small, ci_high_small = compute_ror(a=5, b=95, c=20, d=1880)
        _, ci_low_large, ci_high_large = compute_ror(a=50, b=950, c=200, d=18800)
        width_small = math.log(ci_high_small) - math.log(ci_low_small)
        width_large = math.log(ci_high_large) - math.log(ci_low_large)
        assert width_large < width_small


# ============================================================================
# compute_ebgm()
# ============================================================================


class TestComputeEBGM:
    """Tests for the Empirical Bayesian Geometric Mean (MGPS) computation."""

    def test_known_signal(self):
        """When observed >> expected, EBGM should be well above 1."""
        ebgm, ebgm05 = compute_ebgm(observed=50, expected=5.0)
        assert ebgm > 2.0

    def test_no_signal(self):
        """When observed ~ expected, EBGM should be near 1."""
        ebgm, ebgm05 = compute_ebgm(observed=10, expected=10.0)
        # EBGM is shrunk toward the prior, so it should be roughly near 1
        assert 0.5 < ebgm < 5.0

    def test_zero_expected_returns_zeros(self):
        """Expected=0 makes computation undefined."""
        assert compute_ebgm(observed=10, expected=0.0) == (0.0, 0.0)

    def test_negative_expected_returns_zeros(self):
        assert compute_ebgm(observed=10, expected=-5.0) == (0.0, 0.0)

    def test_negative_observed_returns_zeros(self):
        assert compute_ebgm(observed=-1, expected=5.0) == (0.0, 0.0)

    def test_zero_observed(self):
        """With 0 observed events, EBGM should be very low."""
        ebgm, ebgm05 = compute_ebgm(observed=0, expected=5.0)
        assert ebgm < 1.0

    def test_ebgm05_less_than_or_equal_to_ebgm(self):
        """EBGM05 (5th percentile) should generally be <= EBGM (geometric mean)."""
        ebgm, ebgm05 = compute_ebgm(observed=50, expected=5.0)
        assert ebgm05 <= ebgm

    def test_strong_signal_gives_high_ebgm(self):
        """A very strong signal (large observed/expected ratio) should give a high EBGM."""
        ebgm, ebgm05 = compute_ebgm(observed=100, expected=2.0)
        assert ebgm > 10.0
        assert ebgm05 > 1.0


# ============================================================================
# classify_signal()
# ============================================================================


class TestClassifySignal:
    """Tests for the tiered signal classification."""

    def test_strong_signal(self):
        """All criteria met: PRR>=2, PRR CI_low>1, n>=3, EBGM05>=2."""
        is_signal, strength = classify_signal(
            prr=5.0,
            prr_ci_low=2.5,
            ror=6.0,
            ror_ci_low=3.0,
            ebgm05=3.0,
            n_cases=10,
        )
        assert is_signal is True
        assert strength == "strong"

    def test_moderate_signal(self):
        """PRR>=2 and ROR CI_low>1 and n>=3, but EBGM05<2."""
        is_signal, strength = classify_signal(
            prr=3.0,
            prr_ci_low=1.5,
            ror=3.5,
            ror_ci_low=1.8,
            ebgm05=1.5,
            n_cases=5,
        )
        assert is_signal is True
        assert strength == "moderate"

    def test_weak_signal_from_prr(self):
        """PRR >= 1.5 but nothing else qualifies for moderate or strong."""
        is_signal, strength = classify_signal(
            prr=1.8,
            prr_ci_low=0.8,
            ror=1.5,
            ror_ci_low=0.7,
            ebgm05=0.5,
            n_cases=2,
        )
        assert is_signal is True
        assert strength == "weak"

    def test_weak_signal_from_ebgm05(self):
        """EBGM05 >= 1.0 but PRR < 1.5 should still be weak."""
        is_signal, strength = classify_signal(
            prr=1.2,
            prr_ci_low=0.6,
            ror=1.3,
            ror_ci_low=0.5,
            ebgm05=1.2,
            n_cases=2,
        )
        assert is_signal is True
        assert strength == "weak"

    def test_no_signal(self):
        """Below all thresholds."""
        is_signal, strength = classify_signal(
            prr=1.0,
            prr_ci_low=0.5,
            ror=1.1,
            ror_ci_low=0.4,
            ebgm05=0.5,
            n_cases=1,
        )
        assert is_signal is False
        assert strength == "none"

    def test_strong_requires_n_cases_ge_3(self):
        """Even with high PRR and EBGM, n_cases < 3 should not be strong."""
        is_signal, strength = classify_signal(
            prr=5.0,
            prr_ci_low=2.0,
            ror=6.0,
            ror_ci_low=2.5,
            ebgm05=3.0,
            n_cases=2,
        )
        # With n_cases=2, it cannot be strong (needs >=3).
        # It could still be weak because PRR>=1.5 or EBGM05>=1.
        assert strength != "strong"

    def test_moderate_requires_prr_ge_2(self):
        """PRR < 2 should prevent classification as moderate."""
        is_signal, strength = classify_signal(
            prr=1.8,
            prr_ci_low=1.5,
            ror=2.0,
            ror_ci_low=1.5,
            ebgm05=1.5,
            n_cases=5,
        )
        # PRR=1.8 < 2.0, so not moderate. But PRR>=1.5 => weak.
        assert strength == "weak"

    def test_all_zeros_is_no_signal(self):
        """All zeros should be classified as no signal."""
        is_signal, strength = classify_signal(
            prr=0.0,
            prr_ci_low=0.0,
            ror=0.0,
            ror_ci_low=0.0,
            ebgm05=0.0,
            n_cases=0,
        )
        assert is_signal is False
        assert strength == "none"
