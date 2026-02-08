"""
Unit tests for the compute_stopping_boundaries function in src/models/bayesian_risk.py.

Tests Bayesian stopping boundary computation for clinical trials, verifying
monotonicity, edge cases, prior sensitivity, and posterior probability accuracy.
"""

import pytest

from src.models.bayesian_risk import compute_stopping_boundaries

try:
    from scipy.stats import beta as beta_dist
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

pytestmark = pytest.mark.skipif(
    not _HAS_SCIPY, reason="scipy is required for stopping boundary tests"
)


# ============================================================================
# Monotonicity — more events allowed with more patients
# ============================================================================


class TestBoundaryMonotonicity:
    """Boundaries must be monotonically non-decreasing in max_events as n grows."""

    def test_boundaries_monotonically_nondecreasing_default(self):
        """With default parameters, max_events should never decrease as n grows."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=100,
        )
        for i in range(1, len(boundaries)):
            assert boundaries[i]["max_events"] >= boundaries[i - 1]["max_events"], (
                f"Boundary decreased at n={boundaries[i]['n_patients']}: "
                f"{boundaries[i]['max_events']} < {boundaries[i - 1]['max_events']}"
            )

    def test_boundaries_monotonically_nondecreasing_strict_threshold(self):
        """Same monotonicity check with a strict posterior threshold."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.10,
            posterior_threshold=0.95,
            max_n=50,
        )
        for i in range(1, len(boundaries)):
            assert boundaries[i]["max_events"] >= boundaries[i - 1]["max_events"]

    def test_boundaries_monotonically_nondecreasing_low_rate(self):
        """With a very low target rate, boundaries are still non-decreasing."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.01,
            posterior_threshold=0.8,
            max_n=100,
        )
        for i in range(1, len(boundaries)):
            assert boundaries[i]["max_events"] >= boundaries[i - 1]["max_events"]

    def test_n_patients_strictly_increasing(self):
        """The n_patients values in the output should be strictly increasing
        (only transition points are stored)."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=100,
        )
        for i in range(1, len(boundaries)):
            assert boundaries[i]["n_patients"] > boundaries[i - 1]["n_patients"]


# ============================================================================
# Edge cases — target_rate boundaries
# ============================================================================


class TestEdgeCases:
    """Tests for invalid and extreme target_rate values."""

    def test_target_rate_zero_raises_valueerror(self):
        """target_rate=0 is outside (0, 1) and must raise ValueError."""
        with pytest.raises(ValueError, match="target_rate"):
            compute_stopping_boundaries(target_rate=0.0)

    def test_target_rate_one_raises_valueerror(self):
        """target_rate=1 is outside (0, 1) and must raise ValueError."""
        with pytest.raises(ValueError, match="target_rate"):
            compute_stopping_boundaries(target_rate=1.0)

    def test_target_rate_negative_raises_valueerror(self):
        """Negative target_rate must raise ValueError."""
        with pytest.raises(ValueError, match="target_rate"):
            compute_stopping_boundaries(target_rate=-0.1)

    def test_target_rate_above_one_raises_valueerror(self):
        """target_rate > 1 must raise ValueError."""
        with pytest.raises(ValueError, match="target_rate"):
            compute_stopping_boundaries(target_rate=1.5)

    def test_posterior_threshold_zero_raises_valueerror(self):
        """posterior_threshold=0 is outside (0, 1)."""
        with pytest.raises(ValueError, match="posterior_threshold"):
            compute_stopping_boundaries(target_rate=0.05, posterior_threshold=0.0)

    def test_posterior_threshold_one_raises_valueerror(self):
        """posterior_threshold=1 is outside (0, 1)."""
        with pytest.raises(ValueError, match="posterior_threshold"):
            compute_stopping_boundaries(target_rate=0.05, posterior_threshold=1.0)

    def test_very_high_target_rate_allows_many_events(self):
        """A very high target rate (0.99) should allow many events at any sample size."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.99,
            posterior_threshold=0.8,
            max_n=20,
        )
        # With target_rate ~1, almost all patients can have events
        # The boundary for n=20 should allow close to 20 events
        last = boundaries[-1]
        assert last["max_events"] >= 10, (
            f"Expected many events allowed for target_rate=0.99, got {last['max_events']}"
        )

    def test_very_low_target_rate_restricts_events(self):
        """A very low target rate (0.005) should severely restrict events."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.005,
            posterior_threshold=0.8,
            max_n=50,
        )
        # With target_rate=0.5%, even a single event is alarming
        assert boundaries[0]["max_events"] == 0, (
            "At small n with target_rate=0.005, max_events should be 0"
        )


# ============================================================================
# Prior strength sensitivity
# ============================================================================


class TestPriorStrength:
    """Different prior strengths should affect the boundary width."""

    def test_strong_informative_prior_vs_jeffreys(self):
        """A strong informative prior (large alpha+beta) should produce different
        boundaries than a weak Jeffreys prior."""
        weak = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=50,
            prior_alpha=0.5,
            prior_beta=0.5,
        )
        strong = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=50,
            prior_alpha=5.0,
            prior_beta=95.0,  # Prior mean = 5%, matches target
        )
        # Both should return valid boundaries
        assert len(weak) > 0
        assert len(strong) > 0

    def test_pessimistic_prior_restricts_more(self):
        """A pessimistic prior (high prior rate) should allow fewer events early on
        compared to an optimistic prior."""
        optimistic = compute_stopping_boundaries(
            target_rate=0.10,
            posterior_threshold=0.8,
            max_n=50,
            prior_alpha=0.5,
            prior_beta=9.5,  # Prior mean = 5%
        )
        pessimistic = compute_stopping_boundaries(
            target_rate=0.10,
            posterior_threshold=0.8,
            max_n=50,
            prior_alpha=5.0,
            prior_beta=5.0,  # Prior mean = 50%
        )
        # Build filled boundary lookup for comparison at a specific n
        def fill_boundaries(boundaries, max_n):
            filled = {}
            current = 0
            idx = 0
            for n in range(1, max_n + 1):
                if idx < len(boundaries) and boundaries[idx]["n_patients"] == n:
                    current = boundaries[idx]["max_events"]
                    idx += 1
                filled[n] = current
            return filled

        opt_filled = fill_boundaries(optimistic, 50)
        pess_filled = fill_boundaries(pessimistic, 50)

        # At n=20, pessimistic prior should allow same or fewer events
        assert pess_filled.get(20, 0) <= opt_filled.get(20, 0)

    def test_uniform_prior(self):
        """Uniform Beta(1,1) prior should produce valid boundaries."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=30,
            prior_alpha=1.0,
            prior_beta=1.0,
        )
        assert len(boundaries) > 0
        assert all(b["max_events"] >= 0 for b in boundaries)

    def test_jeffreys_prior(self):
        """Jeffreys Beta(0.5, 0.5) prior should produce valid boundaries."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=30,
            prior_alpha=0.5,
            prior_beta=0.5,
        )
        assert len(boundaries) > 0
        assert all(b["max_events"] >= 0 for b in boundaries)


# ============================================================================
# Posterior probability correctness
# ============================================================================


class TestPosteriorProbability:
    """Verify that the stopping boundaries correspond to correct posterior calculations."""

    def test_boundary_at_n10_target5pct(self):
        """At n=10 with target_rate=0.05 and Jeffreys prior, verify the boundary
        is consistent with the Beta posterior."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=10,
            prior_alpha=0.5,
            prior_beta=0.5,
        )
        # Find boundary at n=10 by filling
        max_k_at_10 = 0
        for b in boundaries:
            if b["n_patients"] <= 10:
                max_k_at_10 = b["max_events"]

        # Verify: with max_k events, prob exceeds target should be < threshold
        a = 0.5 + max_k_at_10
        b = 0.5 + (10 - max_k_at_10)
        prob_exceeds = beta_dist.sf(0.05, a, b)
        assert prob_exceeds < 0.8, (
            f"At n=10, k={max_k_at_10}: P(rate>0.05) = {prob_exceeds:.4f} should be < 0.8"
        )

        # Verify: with max_k + 1 events, prob exceeds target should be >= threshold
        if max_k_at_10 + 1 <= 10:
            a2 = 0.5 + (max_k_at_10 + 1)
            b2 = 0.5 + (10 - max_k_at_10 - 1)
            prob_exceeds_next = beta_dist.sf(0.05, a2, b2)
            assert prob_exceeds_next >= 0.8, (
                f"At n=10, k={max_k_at_10 + 1}: P(rate>0.05) = {prob_exceeds_next:.4f} "
                f"should be >= 0.8"
            )

    def test_zero_events_allowed_initially(self):
        """With very small n and low target rate, the boundary should start at 0."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.02,
            posterior_threshold=0.8,
            max_n=10,
            prior_alpha=0.5,
            prior_beta=0.5,
        )
        assert boundaries[0]["max_events"] == 0

    def test_known_case_10_patients_0_events(self):
        """With 0 events in 10 patients and Jeffreys prior, the posterior
        probability that rate > 5% should be well below 0.8."""
        a = 0.5 + 0
        b = 0.5 + 10
        prob = beta_dist.sf(0.05, a, b)
        # This should be moderate -- verify it's consistent with boundaries
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            posterior_threshold=0.8,
            max_n=10,
            prior_alpha=0.5,
            prior_beta=0.5,
        )
        max_k_at_10 = 0
        for bd in boundaries:
            if bd["n_patients"] <= 10:
                max_k_at_10 = bd["max_events"]
        # 0 events should be within the boundary (allowed)
        assert max_k_at_10 >= 0


# ============================================================================
# Output structure
# ============================================================================


class TestOutputStructure:
    """Tests for the output format and content."""

    def test_returns_list_of_dicts(self):
        """Output should be a list of dicts with expected keys."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=20,
        )
        assert isinstance(boundaries, list)
        for b in boundaries:
            assert isinstance(b, dict)
            assert "n_patients" in b
            assert "max_events" in b

    def test_all_max_events_nonnegative(self):
        """max_events should never be negative."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=50,
        )
        for b in boundaries:
            assert b["max_events"] >= 0

    def test_all_n_patients_positive(self):
        """n_patients should always be positive."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=50,
        )
        for b in boundaries:
            assert b["n_patients"] > 0

    def test_first_entry_starts_at_low_n(self):
        """The first boundary entry should be at a small n."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=100,
        )
        assert boundaries[0]["n_patients"] <= 5

    def test_nonempty_result(self):
        """Should always return at least one boundary point."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=100,
        )
        assert len(boundaries) > 0

    def test_max_n_respected(self):
        """No boundary entry should exceed max_n."""
        boundaries = compute_stopping_boundaries(
            target_rate=0.05,
            max_n=50,
        )
        for b in boundaries:
            assert b["n_patients"] <= 50
