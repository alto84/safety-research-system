"""
Bayesian Beta-Binomial risk model for population-level SAE estimation in SLE CAR-T.

Implements a conjugate Beta-Binomial framework for estimating the true population
rate of immunologic serious adverse events (CRS, ICANS, ICAHS) in autoimmune
CAR-T therapy.  Informative priors are derived from discounted oncology CAR-T
incidence data, and posteriors are updated sequentially as new trial evidence
accrues.

Key capabilities:
    1. Single-timepoint posterior estimation from a Beta prior + observed events.
    2. Sequential evidence accrual across a projected clinical trial timeline,
       producing a trajectory of narrowing credible intervals.

All results are reported as percentages (0-100 scale) for clinical readability.

Priors:
    CRS:   Beta(0.21, 1.29) -- discounted from ~14% oncology rate
    ICANS: Beta(0.14, 1.03) -- discounted from ~12% oncology rate
    ICAHS: Beta(0.5,  0.5)  -- Jeffreys non-informative (novel SAE)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

try:
    from scipy.stats import beta as beta_dist
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PriorSpec:
    """Beta distribution prior specification.

    Attributes:
        alpha: Alpha (shape1) parameter of the Beta distribution.
        beta: Beta (shape2) parameter of the Beta distribution.
        source_description: Human-readable provenance of the prior choice.
    """

    alpha: float
    beta: float
    source_description: str


@dataclass
class PosteriorEstimate:
    """Result of a Beta-Binomial posterior update.

    All rate values (mean, ci_low, ci_high) are expressed as percentages
    (0-100 scale) for clinical readability.

    Attributes:
        mean: Posterior mean rate (%).
        ci_low: Lower bound of 95% credible interval (%).
        ci_high: Upper bound of 95% credible interval (%).
        ci_width: Width of the 95% credible interval (percentage points).
        alpha: Posterior alpha parameter.
        beta: Posterior beta parameter.
        n_patients: Total patients in the observed sample.
        n_events: Total events observed.
    """

    mean: float
    ci_low: float
    ci_high: float
    ci_width: float
    alpha: float
    beta: float
    n_patients: int
    n_events: int


@dataclass
class StudyDataPoint:
    """A single timepoint in the evidence accrual timeline.

    Represents one publication or trial readout contributing new patient-level
    safety data.

    Attributes:
        label: Short citation or study name.
        year: Calendar year of the data readout.
        quarter: Quarter label (e.g. "Q4 2022") for timeline display.
        n_new_patients: Number of new patients added at this timepoint.
        n_cumulative_patients: Running total of patients across all timepoints.
        crs_grade3plus_events: Grade >= 3 CRS events observed at this timepoint.
        icans_grade3plus_events: Grade >= 3 ICANS events observed at this timepoint.
        is_projected: True if this timepoint is a future projection rather than
            published data.
    """

    label: str
    year: int
    quarter: str
    n_new_patients: int
    n_cumulative_patients: int
    crs_grade3plus_events: int
    icans_grade3plus_events: int
    is_projected: bool = False


# ---------------------------------------------------------------------------
# Key constants -- informative priors
#
# Prior Elicitation Methodology
# =============================
# The Beta priors below encode pre-data beliefs about the true population rate
# of each adverse event in autoimmune-indication CAR-T therapy.  Each prior is
# a Beta(alpha, beta) distribution, where:
#
#   - Prior mean          = alpha / (alpha + beta)
#   - Effective sample size = alpha + beta  (pseudo-observations informing the prior)
#   - Variance decreases as the effective sample size grows.
#
# For CRS and ICANS, priors were *discounted* from oncology CAR-T incidence
# data.  The discount reflects the substantially lower AE rates observed in
# autoimmune indications (lower tumor burden -> lower antigen load -> less
# T-cell activation -> fewer cytokines).  The discounting procedure:
#   1. Obtain a weighted-average oncology rate from pivotal trials
#      (ZUMA-1, JULIET, TRANSCEND, ELIANA, KarMMa, CARTITUDE-1;
#       see data/sle_cart_studies.py for individual trial data).
#   2. Apply a 10x discount factor to the oncology rate, reflecting
#      the clinical observation that autoimmune CRS/ICANS rates are
#      roughly an order of magnitude lower than oncology rates (e.g.,
#      SLE pooled Grade 3+ CRS ~2% vs. oncology 2-48%).
#   3. Choose alpha and beta so that the prior mean matches the
#      discounted rate and the effective sample size is small (~1.5),
#      keeping the prior weakly informative so that even a small
#      number of real observations will dominate the posterior.
#
# For ICAHS, no oncology comparator data exists (ICAHS is a novel
# autoimmune-specific toxicity), so a Jeffreys non-informative prior
# Beta(0.5, 0.5) is used, which is the standard objective prior for
# binomial proportions (Jeffreys, 1961).
#
# References:
#   - Neelapu SS et al. N Engl J Med 2017 (ZUMA-1, axi-cel CRS rates)
#   - Schuster SJ et al. N Engl J Med 2019 (JULIET, tisa-cel CRS rates)
#   - Abramson JS et al. Lancet 2020 (TRANSCEND, liso-cel CRS rates)
#   - Maude SL et al. N Engl J Med 2018 (ELIANA, tisa-cel ALL CRS rates)
#   - Munshi NC et al. N Engl J Med 2021 (KarMMa, ide-cel CRS rates)
#   - Berdeja JG et al. Lancet 2021 (CARTITUDE-1, cilta-cel CRS rates)
#   - Mackensen A et al. Nat Med 2022 (SLE CAR-T, first autoimmune data)
#   - Jeffreys H. Theory of Probability, 3rd ed. Oxford, 1961.
# ---------------------------------------------------------------------------

CRS_PRIOR = PriorSpec(
    alpha=0.21,
    beta=1.29,
    source_description="Discounted oncology ~14%",
)
"""Beta prior for CRS (Cytokine Release Syndrome) Grade 3+ rate.

Parameters:
    alpha = 0.21, beta = 1.29
    Prior mean = 0.21 / (0.21 + 1.29) = 14.0%
    Effective sample size = 0.21 + 1.29 = 1.5 pseudo-patients

Derivation:
    Weighted-average Grade 3+ CRS rate across oncology pivotal trials
    (ZUMA-1 13%, JULIET 14%, TRANSCEND 2%, ELIANA 48%, KarMMa 7%,
    CARTITUDE-1 4%) is approximately 14%.  The effective sample size of
    1.5 makes the prior weakly informative: even 5-10 real patients will
    dominate the posterior.  The 14% mean will be pulled sharply downward
    once the ~2% observed autoimmune rate enters the likelihood.
"""

ICANS_PRIOR = PriorSpec(
    alpha=0.14,
    beta=1.03,
    source_description="Discounted oncology ~12%",
)
"""Beta prior for ICANS (Immune Effector Cell-Associated Neurotoxicity
Syndrome) Grade 3+ rate.

Parameters:
    alpha = 0.14, beta = 1.03
    Prior mean = 0.14 / (0.14 + 1.03) = 12.0%
    Effective sample size = 0.14 + 1.03 = 1.17 pseudo-patients

Derivation:
    Weighted-average Grade 3+ ICANS rate across oncology pivotal trials
    (ZUMA-1 28%, JULIET 12%, TRANSCEND 10%, ELIANA 13%, KarMMa 4%,
    CARTITUDE-1 10%) is approximately 12%.  Effective sample size of
    ~1.2 makes this even weaker than the CRS prior, reflecting greater
    uncertainty about ICANS rates in autoimmune indications.  Early SLE
    data show 0% Grade 3+ ICANS (0/47 patients).
"""

ICAHS_PRIOR = PriorSpec(
    alpha=0.5,
    beta=0.5,
    source_description="Jeffreys non-informative",
)
"""Beta prior for ICAHS (Immune Effector Cell-Associated Hematotoxicity
Syndrome) rate.

Parameters:
    alpha = 0.5, beta = 0.5
    Prior mean = 50% (maximally uncertain)
    Effective sample size = 1.0 pseudo-patient

Derivation:
    Jeffreys non-informative prior, Beta(0.5, 0.5).  Used because ICAHS
    is a novel adverse event category specific to autoimmune CAR-T therapy
    with no oncology comparator data available for prior elicitation.
    The Jeffreys prior is the standard objective prior for binomial
    proportions (Jeffreys, 1961) and is invariant under reparametrization.
    Any observed data will immediately dominate this prior.
"""


# ---------------------------------------------------------------------------
# Embedded evidence accrual timeline
# ---------------------------------------------------------------------------

STUDY_TIMELINE: list[StudyDataPoint] = [
    StudyDataPoint(
        "Mackensen et al.", 2022, "Q4 2022",
        n_new_patients=5, n_cumulative_patients=5,
        crs_grade3plus_events=0, icans_grade3plus_events=0,
    ),
    StudyDataPoint(
        "Muller et al.", 2024, "Q1 2024",
        n_new_patients=15, n_cumulative_patients=20,
        crs_grade3plus_events=0, icans_grade3plus_events=0,
    ),
    StudyDataPoint(
        "Jin / Co-infusion / Cabaletta", 2024, "Q3 2024",
        n_new_patients=17, n_cumulative_patients=37,
        crs_grade3plus_events=1, icans_grade3plus_events=0,
    ),
    StudyDataPoint(
        "CASTLE / BMS / Expanded", 2025, "Q1 2025",
        n_new_patients=10, n_cumulative_patients=47,
        crs_grade3plus_events=1, icans_grade3plus_events=0,
    ),
    StudyDataPoint(
        "CASTLE Ph2 interim", 2026, "Q3 2026",
        n_new_patients=30, n_cumulative_patients=77,
        crs_grade3plus_events=2, icans_grade3plus_events=1,
        is_projected=True,
    ),
    StudyDataPoint(
        "RESET-SLE Ph2", 2027, "Q1 2027",
        n_new_patients=50, n_cumulative_patients=127,
        crs_grade3plus_events=3, icans_grade3plus_events=1,
        is_projected=True,
    ),
    StudyDataPoint(
        "Pooled Ph2 data", 2028, "Q1 2028",
        n_new_patients=73, n_cumulative_patients=200,
        crs_grade3plus_events=4, icans_grade3plus_events=2,
        is_projected=True,
    ),
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def compute_posterior(
    prior: PriorSpec,
    events: int,
    n: int,
) -> PosteriorEstimate:
    """Compute the Beta posterior and normal-approximation 95% credible interval.

    Given a Beta(alpha, beta) prior and observed data (events out of n patients),
    the conjugate posterior is Beta(alpha + events, beta + n - events).

    The 95% credible interval uses a normal approximation:
        mean +/- 1.96 * sqrt(variance)
    clipped to the [0, 1] probability simplex, then scaled to percentages.

    Args:
        prior: Beta prior specification.
        events: Number of SAE events observed.
        n: Total number of patients in the sample.

    Returns:
        PosteriorEstimate with mean and CI in percentage units.

    Raises:
        ValueError: If events > n or either is negative.
    """
    if events < 0 or n < 0:
        raise ValueError(
            f"events ({events}) and n ({n}) must be non-negative"
        )
    if events > n:
        raise ValueError(
            f"events ({events}) cannot exceed n ({n})"
        )

    a = prior.alpha + events
    b = prior.beta + (n - events)

    mean = a / (a + b)

    if _HAS_SCIPY:
        # Exact Beta quantiles (preferred over normal approximation)
        ci_low = beta_dist.ppf(0.025, a, b)
        ci_high = beta_dist.ppf(0.975, a, b)
    else:
        # Fallback: normal approximation (less accurate for small samples)
        variance = (a * b) / ((a + b) ** 2 * (a + b + 1))
        std = math.sqrt(variance)
        ci_low = max(0.0, mean - 1.96 * std)
        ci_high = min(1.0, mean + 1.96 * std)

    # Convert to percentages
    mean_pct = mean * 100.0
    ci_low_pct = ci_low * 100.0
    ci_high_pct = ci_high * 100.0
    ci_width_pct = ci_high_pct - ci_low_pct

    return PosteriorEstimate(
        mean=round(mean_pct, 4),
        ci_low=round(ci_low_pct, 4),
        ci_high=round(ci_high_pct, 4),
        ci_width=round(ci_width_pct, 4),
        alpha=round(a, 4),
        beta=round(b, 4),
        n_patients=n,
        n_events=events,
    )


def compute_evidence_accrual(
    prior: PriorSpec,
    timeline: list[StudyDataPoint],
    event_field: str,
) -> list[PosteriorEstimate]:
    """Compute sequential posteriors across an evidence accrual timeline.

    At each timepoint the cumulative patient count and cumulative event count
    are used to update the prior, producing a trajectory of posterior estimates
    that shows how uncertainty narrows as data accrues.

    Args:
        prior: Beta prior specification (starting point).
        timeline: Ordered list of StudyDataPoints.  Must have monotonically
            increasing cumulative patient counts.
        event_field: Name of the StudyDataPoint attribute to use as the event
            count.  Typically ``"crs_grade3plus_events"`` or
            ``"icans_grade3plus_events"``.

    Returns:
        List of PosteriorEstimate, one per timepoint, in the same order as
        the input timeline.

    Raises:
        AttributeError: If event_field is not a valid StudyDataPoint attribute.
    """
    posteriors: list[PosteriorEstimate] = []

    for point in timeline:
        # Events in the timeline data are already cumulative
        cumulative_events = getattr(point, event_field)

        posterior = compute_posterior(
            prior=prior,
            events=cumulative_events,
            n=point.n_cumulative_patients,
        )
        posteriors.append(posterior)

        logger.debug(
            "Evidence accrual [%s]: n=%d, events=%d, mean=%.2f%%, "
            "CI=[%.2f%%, %.2f%%]%s",
            point.label,
            point.n_cumulative_patients,
            cumulative_events,
            posterior.mean,
            posterior.ci_low,
            posterior.ci_high,
            " (projected)" if point.is_projected else "",
        )

    return posteriors


def compute_stopping_boundaries(
    target_rate: float,
    posterior_threshold: float = 0.8,
    max_n: int = 100,
    prior_alpha: float = 0.5,
    prior_beta: float = 0.5,
) -> list[dict]:
    """Compute Bayesian stopping boundaries for a clinical trial.

    For each sample size n from 1 to max_n, finds the maximum number of
    events k such that the posterior probability that the true rate exceeds
    target_rate remains below posterior_threshold.  When the number of
    observed events exceeds the boundary, enrollment should be paused.

    Uses the Beta posterior: after observing k events in n patients with a
    Beta(prior_alpha, prior_beta) prior, the posterior is
    Beta(prior_alpha + k, prior_beta + n - k).  The probability that the
    rate exceeds target_rate is 1 - CDF(target_rate) = SF(target_rate).

    Args:
        target_rate: Maximum tolerable AE rate (as a proportion, 0-1).
        posterior_threshold: Posterior probability threshold above which to
            stop.  Default 0.8.
        max_n: Maximum sample size to compute boundaries for.
        prior_alpha: Beta prior alpha parameter.
        prior_beta: Beta prior beta parameter.

    Returns:
        List of dicts with keys ``n_patients`` and ``max_events``.  Only
        sample sizes where the boundary changes are included to keep the
        output compact.
    """
    if not _HAS_SCIPY:
        raise RuntimeError(
            "scipy is required for compute_stopping_boundaries"
        )

    if not (0 < target_rate < 1):
        raise ValueError(f"target_rate must be in (0, 1), got {target_rate}")
    if not (0 < posterior_threshold < 1):
        raise ValueError(
            f"posterior_threshold must be in (0, 1), got {posterior_threshold}"
        )

    boundaries: list[dict] = []
    prev_max_k: int | None = None

    for n in range(1, max_n + 1):
        max_k = -1  # Start with no events allowed
        for k in range(n + 1):
            # Posterior: Beta(prior_alpha + k, prior_beta + n - k)
            a = prior_alpha + k
            b = prior_beta + (n - k)
            # P(rate > target_rate | data) = sf(target_rate, a, b)
            prob_exceeds = beta_dist.sf(target_rate, a, b)
            if prob_exceeds < posterior_threshold:
                max_k = k
            else:
                break

        # Only record when boundary changes (or at key sample sizes)
        if max_k != prev_max_k:
            boundaries.append({
                "n_patients": n,
                "max_events": max(max_k, 0),
            })
            prev_max_k = max_k

    return boundaries
