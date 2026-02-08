"""
Unit tests for src/models/bayesian_risk.py

Tests the Beta-Binomial posterior computation, evidence accrual pipeline,
prior constants, and the study timeline data.
"""

import pytest

from src.models.bayesian_risk import (
    CRS_PRIOR,
    ICAHS_PRIOR,
    ICANS_PRIOR,
    STUDY_TIMELINE,
    PriorSpec,
    compute_evidence_accrual,
    compute_posterior,
)


# ============================================================================
# compute_posterior()
# ============================================================================


class TestComputePosterior:
    """Tests for the single-timepoint Beta-Binomial posterior update."""

    def test_zero_events_lowers_posterior_mean(self):
        """With zero events observed, the posterior mean should be pulled
        below the prior mean because the data is entirely non-events."""
        prior = PriorSpec(alpha=1.0, beta=1.0, source_description="Uniform prior")
        # Prior mean = 1/(1+1) = 50%
        result = compute_posterior(prior, events=0, n=10)
        # Posterior alpha=1, beta=11 => mean=1/12 ~ 8.3%
        assert result.mean < 50.0

    def test_all_events_gives_high_posterior_mean(self):
        """When every patient has an event, posterior mean should be high."""
        prior = PriorSpec(alpha=1.0, beta=1.0, source_description="Uniform prior")
        result = compute_posterior(prior, events=10, n=10)
        # Posterior alpha=11, beta=1 => mean=11/12 ~ 91.7%
        assert result.mean > 80.0

    def test_events_greater_than_n_raises_valueerror(self):
        """events > n is logically impossible and must raise."""
        with pytest.raises(ValueError, match="cannot exceed"):
            compute_posterior(CRS_PRIOR, events=50, n=10)

    def test_negative_events_raises_valueerror(self):
        """Negative event counts are invalid."""
        with pytest.raises(ValueError, match="non-negative"):
            compute_posterior(CRS_PRIOR, events=-1, n=10)

    def test_negative_n_raises_valueerror(self):
        """Negative patient count is invalid."""
        with pytest.raises(ValueError, match="non-negative"):
            compute_posterior(CRS_PRIOR, events=0, n=-5)

    def test_known_values_crs_prior(self):
        """With CRS_PRIOR (0.21, 1.29) and 1 event in 47 patients,
        the posterior parameters should be alpha=1.21, beta=47.29."""
        result = compute_posterior(CRS_PRIOR, events=1, n=47)
        assert result.alpha == pytest.approx(1.21, abs=0.01)
        assert result.beta == pytest.approx(47.29, abs=0.01)

    def test_ci_within_0_100(self):
        """Credible interval bounds must lie within [0, 100] percent."""
        result = compute_posterior(CRS_PRIOR, events=1, n=47)
        assert result.ci_low >= 0.0
        assert result.ci_high <= 100.0

    def test_ci_brackets_mean(self):
        """The CI low should be below the mean and CI high above it."""
        result = compute_posterior(CRS_PRIOR, events=1, n=47)
        assert result.ci_low < result.mean
        assert result.ci_high > result.mean

    def test_ci_width_is_positive(self):
        """CI width should always be positive."""
        result = compute_posterior(CRS_PRIOR, events=1, n=47)
        assert result.ci_width > 0.0

    def test_zero_events_zero_patients(self):
        """Edge case: 0 events in 0 patients should return the prior itself."""
        result = compute_posterior(CRS_PRIOR, events=0, n=0)
        # Posterior alpha = prior alpha, posterior beta = prior beta
        assert result.alpha == pytest.approx(CRS_PRIOR.alpha, abs=0.01)
        assert result.beta == pytest.approx(CRS_PRIOR.beta, abs=0.01)

    def test_n_patients_and_n_events_recorded(self):
        """The posterior estimate should record the input n and events."""
        result = compute_posterior(CRS_PRIOR, events=3, n=50)
        assert result.n_patients == 50
        assert result.n_events == 3

    def test_larger_sample_narrows_ci(self):
        """A larger sample should produce a narrower CI than a smaller one,
        given the same event rate."""
        small = compute_posterior(CRS_PRIOR, events=1, n=10)
        large = compute_posterior(CRS_PRIOR, events=10, n=100)
        assert large.ci_width < small.ci_width


# ============================================================================
# compute_evidence_accrual()
# ============================================================================


class TestComputeEvidenceAccrual:
    """Tests for the sequential evidence accrual function."""

    def test_returns_same_length_as_timeline(self):
        """Output list should have one entry per timeline point."""
        posteriors = compute_evidence_accrual(
            CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events"
        )
        assert len(posteriors) == len(STUDY_TIMELINE)

    def test_ci_width_generally_decreases(self):
        """As cumulative patient count grows, CI width should generally
        decrease (uncertainty narrows)."""
        posteriors = compute_evidence_accrual(
            CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events"
        )
        # Compare first and last -- last should be narrower
        assert posteriors[-1].ci_width < posteriors[0].ci_width

    def test_first_timepoint_uses_first_study_data(self):
        """The first posterior should use only the first study's data."""
        posteriors = compute_evidence_accrual(
            CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events"
        )
        first = posteriors[0]
        first_study = STUDY_TIMELINE[0]

        # First study: n=5, crs_events=0
        assert first.n_patients == first_study.n_cumulative_patients
        assert first.n_events == first_study.crs_grade3plus_events

    def test_invalid_event_field_raises_attributeerror(self):
        """An invalid field name should raise AttributeError."""
        with pytest.raises(AttributeError):
            compute_evidence_accrual(
                CRS_PRIOR, STUDY_TIMELINE, "nonexistent_field"
            )

    def test_icans_accrual_works(self):
        """Evidence accrual should also work for ICANS events."""
        posteriors = compute_evidence_accrual(
            ICANS_PRIOR, STUDY_TIMELINE, "icans_grade3plus_events"
        )
        assert len(posteriors) == len(STUDY_TIMELINE)

    def test_posteriors_are_posteriorestimate_objects(self):
        """Every element in the returned list should have expected attributes."""
        posteriors = compute_evidence_accrual(
            CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events"
        )
        for p in posteriors:
            assert hasattr(p, "mean")
            assert hasattr(p, "ci_low")
            assert hasattr(p, "ci_high")
            assert hasattr(p, "alpha")
            assert hasattr(p, "beta")


# ============================================================================
# Prior constants
# ============================================================================


class TestPriorConstants:
    """Tests for the informative prior specifications."""

    @pytest.mark.parametrize("prior", [CRS_PRIOR, ICANS_PRIOR, ICAHS_PRIOR])
    def test_alpha_is_positive(self, prior):
        assert prior.alpha > 0.0

    @pytest.mark.parametrize("prior", [CRS_PRIOR, ICANS_PRIOR, ICAHS_PRIOR])
    def test_beta_is_positive(self, prior):
        assert prior.beta > 0.0

    @pytest.mark.parametrize("prior", [CRS_PRIOR, ICANS_PRIOR, ICAHS_PRIOR])
    def test_source_description_is_nonempty(self, prior):
        assert isinstance(prior.source_description, str)
        assert len(prior.source_description) > 0

    def test_crs_prior_values(self):
        """CRS prior should be Beta(0.21, 1.29)."""
        assert CRS_PRIOR.alpha == pytest.approx(0.21)
        assert CRS_PRIOR.beta == pytest.approx(1.29)

    def test_icans_prior_values(self):
        """ICANS prior should be Beta(0.14, 1.03)."""
        assert ICANS_PRIOR.alpha == pytest.approx(0.14)
        assert ICANS_PRIOR.beta == pytest.approx(1.03)

    def test_icahs_prior_is_jeffreys(self):
        """ICAHS prior should be Jeffreys non-informative Beta(0.5, 0.5)."""
        assert ICAHS_PRIOR.alpha == pytest.approx(0.5)
        assert ICAHS_PRIOR.beta == pytest.approx(0.5)


# ============================================================================
# STUDY_TIMELINE
# ============================================================================


class TestStudyTimeline:
    """Tests for the embedded evidence accrual timeline."""

    def test_has_7_entries(self):
        assert len(STUDY_TIMELINE) == 7

    def test_cumulative_patients_monotonically_increasing(self):
        """Cumulative patient counts must strictly increase."""
        for i in range(1, len(STUDY_TIMELINE)):
            assert (
                STUDY_TIMELINE[i].n_cumulative_patients
                > STUDY_TIMELINE[i - 1].n_cumulative_patients
            )

    def test_first_4_are_observed(self):
        """The first 4 timepoints should be observed (not projected)."""
        for point in STUDY_TIMELINE[:4]:
            assert point.is_projected is False, (
                f"{point.label} should be observed but is_projected=True"
            )

    def test_last_3_are_projected(self):
        """The last 3 timepoints should be projected."""
        for point in STUDY_TIMELINE[4:]:
            assert point.is_projected is True, (
                f"{point.label} should be projected but is_projected=False"
            )

    def test_all_have_labels(self):
        """Every timeline entry should have a non-empty label."""
        for point in STUDY_TIMELINE:
            assert isinstance(point.label, str)
            assert len(point.label) > 0

    def test_all_have_positive_new_patients(self):
        """Every entry should contribute at least 1 new patient."""
        for point in STUDY_TIMELINE:
            assert point.n_new_patients > 0

    def test_cumulative_equals_running_sum(self):
        """Cumulative patients should equal the running sum of new patients."""
        running = 0
        for point in STUDY_TIMELINE:
            running += point.n_new_patients
            assert point.n_cumulative_patients == running
