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
# ---------------------------------------------------------------------------

CRS_PRIOR = PriorSpec(
    alpha=0.21,
    beta=1.29,
    source_description="Discounted oncology ~14%",
)

ICANS_PRIOR = PriorSpec(
    alpha=0.14,
    beta=1.03,
    source_description="Discounted oncology ~12%",
)

ICAHS_PRIOR = PriorSpec(
    alpha=0.5,
    beta=0.5,
    source_description="Jeffreys non-informative",
)


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
