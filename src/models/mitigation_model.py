"""
Correlated mitigation combination model for CAR-T adverse event risk reduction.

Implements a geometric interpolation formula for combining correlated risk
reduction strategies, plus Monte Carlo simulation for propagating uncertainty
through the mitigation pipeline.

The core insight is that when two mitigations share a biological mechanism
(e.g. anakinra and tocilizumab both targeting IL-6/IL-1 inflammatory
cascades), their combined effect is less than the naive multiplicative
product.  The correlation-adjusted formula smoothly interpolates between:

    rho = 0  -->  fully multiplicative (independent mechanisms)
    rho = 1  -->  min(RR_a, RR_b)    (fully redundant mechanisms)

Key capabilities:
    1. Pairwise correlated relative-risk combination.
    2. Greedy multi-strategy combination (most-correlated pair first).
    3. Monte Carlo uncertainty propagation from Beta baseline + LogNormal RR.
    4. High-level convenience function for CRS + ICANS mitigated estimates.

Mitigation strategies:
    - tocilizumab:                  Anti-IL-6R, targets CRS
    - corticosteroids:              Broad anti-inflammatory, targets ICANS
    - anakinra:                     IL-1 blockade, targets CRS + ICANS
    - dose-reduction:               Lower CAR-T dose, targets CRS + ICANS + ICAHS
    - lymphodepletion-modification: Altered conditioning, targets CRS
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MitigationStrategy:
    """A single risk-mitigation intervention.

    Attributes:
        id: Short unique identifier (e.g. "tocilizumab").
        name: Human-readable name.
        mechanism: Brief description of the pharmacological mechanism.
        target_aes: List of adverse event types this strategy mitigates
            (e.g. ["CRS"], ["CRS", "ICANS"]).
        relative_risk: Point estimate of the relative risk (0-1 = protective,
            >1 = harmful).
        confidence_interval: 95% CI for the relative risk as (lower, upper).
        evidence_level: Strength of supporting evidence ("Strong", "Moderate",
            "Limited").
        dosing: Recommended dosing regimen.
        timing: When the intervention should be administered relative to
            CAR-T infusion.
        limitations: Known caveats or limitations of the evidence.
        references: Literature citations supporting the RR estimate.
    """

    id: str
    name: str
    mechanism: str
    target_aes: list[str]
    relative_risk: float
    confidence_interval: tuple[float, float]
    evidence_level: str
    dosing: str
    timing: str
    limitations: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class MitigationResult:
    """Output from a correlated mitigation combination calculation.

    Attributes:
        baseline_risk: The unmitigated baseline risk (as a proportion, 0-1).
        mitigated_risk: The risk after applying all selected mitigations.
        combined_rr: The combined relative risk from all mitigations.
        selected_mitigations: IDs of the mitigations that were applied.
        correlations_applied: Log of pairwise correlation adjustments made
            during the greedy combination process.
    """

    baseline_risk: float
    mitigated_risk: float
    combined_rr: float
    selected_mitigations: list[str]
    correlations_applied: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mitigation correlation matrix
# ---------------------------------------------------------------------------

MITIGATION_CORRELATIONS: dict[tuple[str, str], float] = {
    ("anakinra", "corticosteroids"): 0.3,
    ("anakinra", "tocilizumab"): 0.4,
    ("corticosteroids", "tocilizumab"): 0.5,
}


# ---------------------------------------------------------------------------
# Mitigation strategy registry
# ---------------------------------------------------------------------------

MITIGATION_STRATEGIES: dict[str, MitigationStrategy] = {
    "tocilizumab": MitigationStrategy(
        id="tocilizumab",
        name="Tocilizumab (Anti-IL-6R)",
        mechanism="IL-6 receptor blockade; reduces CRS severity by interrupting "
                  "the IL-6 amplification loop",
        target_aes=["CRS"],
        relative_risk=0.45,
        confidence_interval=(0.30, 0.65),
        evidence_level="Strong",
        dosing="8 mg/kg IV (max 800 mg), up to 3 doses",
        timing="At onset of Grade >= 2 CRS or prophylactically in high-risk patients",
        limitations=[
            "RR derived from oncology CAR-T CRS management; autoimmune CAR-T "
            "CRS is generally milder and may respond differently",
            "May mask early CRS symptoms",
            "Limited efficacy for ICANS",
            "Transient elevation of serum IL-6 after administration",
        ],
        references=[
            "Le RQ et al. FDA approval summary: tocilizumab for CRS. Clin Cancer Res 2018",
            "Kadauke S et al. Risk-adapted preemptive tocilizumab. Blood Adv 2024",
        ],
    ),
    "corticosteroids": MitigationStrategy(
        id="corticosteroids",
        name="Corticosteroids",
        mechanism="Broad immunosuppression via glucocorticoid receptor activation; "
                  "suppresses T-cell activation and cytokine production",
        target_aes=["ICANS"],
        relative_risk=0.55,
        confidence_interval=(0.35, 0.75),
        evidence_level="Moderate",
        dosing="Dexamethasone 10 mg IV q6h or methylprednisolone 1-2 mg/kg/day",
        timing="At onset of Grade >= 2 ICANS; taper over 3-7 days",
        limitations=[
            "RR from therapeutic use in oncology ICANS; prophylactic corticosteroid "
            "use in autoimmune CAR-T is unproven and may interfere with engraftment",
            "May reduce CAR-T efficacy and persistence",
            "Risk of opportunistic infections",
            "Dose-dependent side effects with prolonged use",
        ],
        references=[
            "Lee DW et al. ASTCT consensus grading for CRS and ICANS. Biol Blood Marrow Transplant 2019",
            "Sterner RM et al. GM-CSF inhibition reduces CRS. Blood 2019",
        ],
    ),
    "anakinra": MitigationStrategy(
        id="anakinra",
        name="Anakinra (IL-1 Receptor Antagonist)",
        mechanism="IL-1 receptor blockade; attenuates macrophage activation and "
                  "downstream inflammatory cascades without directly suppressing "
                  "T-cell function",
        target_aes=["CRS", "ICANS"],
        relative_risk=0.65,
        confidence_interval=(0.45, 0.85),
        evidence_level="Limited",
        dosing="100 mg SC daily or 200-400 mg IV for severe cases",
        timing="Prophylactically from Day 0 or at CRS onset",
        limitations=[
            "RR estimate extrapolated from preclinical models and case series; "
            "no randomized CAR-T trial data available",
            "Limited Phase 3 data in CAR-T setting",
            "Injection site reactions with SC administration",
            "Short half-life requires daily dosing",
        ],
        references=[
            "Norelli M et al. Monocyte-derived IL-1 and IL-6 are differentially required for CRS. Nat Med 2018",
            "Sterner RM et al. GM-CSF inhibition reduces CRS. Blood 2019",
        ],
    ),
    "dose-reduction": MitigationStrategy(
        id="dose-reduction",
        name="CAR-T Dose Reduction",
        mechanism="Lower effector cell dose reduces peak cytokine release and "
                  "total inflammatory burden",
        target_aes=["CRS", "ICANS", "ICAHS"],
        relative_risk=0.15,
        confidence_interval=(0.08, 0.30),
        evidence_level="Strong",
        dosing="Reduced from standard 1e8 to 1e6-1e7 CAR-T cells",
        timing="At manufacturing / infusion",
        limitations=[
            "Potential reduction in efficacy and depth of B-cell depletion",
            "Optimal dose for autoimmune indications still under investigation",
            "May require re-dosing if response is insufficient",
        ],
        references=[
            "Mackensen A et al. Anti-CD19 CAR T cells for refractory SLE. Nat Med 2022",
            "Muller F et al. CD19-targeted CAR T cells in refractory antisynthetase syndrome. NEJM 2024",
        ],
    ),
    "lymphodepletion-modification": MitigationStrategy(
        id="lymphodepletion-modification",
        name="Lymphodepletion Modification",
        mechanism="Reduced-intensity conditioning (e.g. fludarabine dose reduction "
                  "or omission) lowers baseline inflammation before CAR-T infusion",
        target_aes=["CRS"],
        relative_risk=0.85,
        confidence_interval=(0.65, 1.05),
        evidence_level="Limited",
        dosing="Reduced fludarabine (e.g. 90 mg/m2 vs 120 mg/m2) or "
               "cyclophosphamide monotherapy",
        timing="Lymphodepletion window (Days -5 to -2)",
        limitations=[
            "May reduce CAR-T expansion and engraftment",
            "Optimal LD regimen for autoimmune CAR-T not established",
            "Confidence interval crosses 1.0 (uncertain benefit)",
        ],
        references=[
            "Turtle CJ et al. Immunotherapy of NHL with CD19 CAR-T. JCI 2016",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Correlation lookup
# ---------------------------------------------------------------------------

def get_mitigation_correlation(id_a: str, id_b: str) -> float:
    """Look up the pairwise correlation between two mitigations.

    The correlation matrix is keyed by sorted tuples, so the order of
    arguments does not matter.  Returns 0.0 (independent) for pairs not
    in the matrix.

    Args:
        id_a: Mitigation ID.
        id_b: Mitigation ID.

    Returns:
        Correlation coefficient in [0, 1].  0.0 means independent mechanisms;
        1.0 means fully redundant mechanisms.
    """
    key = tuple(sorted((id_a, id_b)))
    return MITIGATION_CORRELATIONS.get(key, 0.0)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Correlated RR combination
# ---------------------------------------------------------------------------

def combine_correlated_rr(rr_a: float, rr_b: float, rho: float) -> float:
    """Combine two relative risks using the geometric interpolation formula.

    The formula smoothly interpolates between multiplicative independence
    and full redundancy::

        combined = (rr_a * rr_b)^(1 - rho) * min(rr_a, rr_b)^rho

    At rho=0 (independent): combined = rr_a * rr_b  (multiplicative)
    At rho=1 (redundant):   combined = min(rr_a, rr_b)

    Args:
        rr_a: Relative risk of mitigation A.
        rr_b: Relative risk of mitigation B.
        rho: Correlation coefficient in [0, 1].

    Returns:
        Combined relative risk.

    Raises:
        ValueError: If rr_a or rr_b is negative, or rho is outside [0, 1].
    """
    if rr_a < 0.0 or rr_b < 0.0:
        raise ValueError(
            f"Relative risks must be non-negative: rr_a={rr_a}, rr_b={rr_b}"
        )
    if not (0.0 <= rho <= 1.0):
        raise ValueError(f"Correlation rho must be in [0, 1]: rho={rho}")

    multiplicative = rr_a * rr_b
    floor = min(rr_a, rr_b)

    return (multiplicative ** (1.0 - rho)) * (floor ** rho)


def combine_multiple_rrs(
    mitigation_ids: list[str],
    rrs: list[float],
) -> float:
    """Combine multiple relative risks using greedy pairwise correlation.

    Algorithm:
        1. Build a pool of (id, rr) pairs.
        2. Find the most-correlated pair in the pool.
        3. Combine that pair using the geometric interpolation formula.
        4. Replace the pair with a single synthetic entry.
        5. Repeat until one entry remains.

    Args:
        mitigation_ids: List of mitigation IDs (parallel to rrs).
        rrs: List of relative risk values (parallel to mitigation_ids).

    Returns:
        The final combined relative risk.

    Raises:
        ValueError: If the lists are empty or have different lengths.
    """
    if len(mitigation_ids) != len(rrs):
        raise ValueError(
            f"mitigation_ids ({len(mitigation_ids)}) and rrs ({len(rrs)}) "
            "must have the same length"
        )
    if len(mitigation_ids) == 0:
        raise ValueError("At least one mitigation must be provided")

    if len(mitigation_ids) == 1:
        return rrs[0]

    # Working pool: list of (id, rr)
    pool: list[tuple[str, float]] = list(zip(mitigation_ids, rrs))

    while len(pool) > 1:
        # Find the most-correlated pair
        best_i, best_j = 0, 1
        best_rho = get_mitigation_correlation(pool[0][0], pool[1][0])

        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                rho = get_mitigation_correlation(pool[i][0], pool[j][0])
                if rho > best_rho:
                    best_i, best_j = i, j
                    best_rho = rho

        # Combine the best pair
        id_a, rr_a = pool[best_i]
        id_b, rr_b = pool[best_j]
        combined_rr = combine_correlated_rr(rr_a, rr_b, best_rho)

        logger.debug(
            "Combining %s (RR=%.3f) + %s (RR=%.3f), rho=%.2f -> RR=%.4f",
            id_a, rr_a, id_b, rr_b, best_rho, combined_rr,
        )

        # Remove the pair (higher index first to preserve lower index)
        for idx in sorted([best_i, best_j], reverse=True):
            pool.pop(idx)

        # Insert the combined entry with a synthetic ID
        synthetic_id = f"{id_a}+{id_b}"
        pool.append((synthetic_id, combined_rr))

    return pool[0][1]


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------

def monte_carlo_mitigated_risk(
    baseline_alpha: float,
    baseline_beta: float,
    mitigation_ids: list[str],
    n_samples: int = 10_000,
    seed: int | None = None,
) -> dict[str, float]:
    """Monte Carlo simulation of mitigated risk with uncertainty propagation.

    Procedure for each sample:
        1. Draw baseline risk from Beta(alpha, beta).
        2. For each mitigation, draw RR from LogNormal(log(RR), SE) where
           SE is derived from the 95% CI of the published RR estimate.
        3. Combine the sampled RRs using greedy correlated combination.
        4. Compute mitigated risk = baseline * combined_rr.

    Args:
        baseline_alpha: Alpha parameter of the Beta baseline distribution.
        baseline_beta: Beta parameter of the Beta baseline distribution.
        mitigation_ids: List of mitigation strategy IDs to apply.
        n_samples: Number of Monte Carlo samples.
        seed: Optional random seed for reproducibility.

    Returns:
        Dict with keys:
            - "median": Median mitigated risk (proportion, 0-1).
            - "p2_5": 2.5th percentile (lower bound of 95% interval).
            - "p97_5": 97.5th percentile (upper bound of 95% interval).
            - "mean": Mean mitigated risk.
            - "n_samples": Number of samples used.
    """
    rng = random.Random(seed)

    # Pre-compute LogNormal parameters for each mitigation
    log_params: list[tuple[float, float]] = []  # (mu, sigma)
    for mid in mitigation_ids:
        strategy = MITIGATION_STRATEGIES[mid]
        rr = strategy.relative_risk
        ci_low, ci_high = strategy.confidence_interval

        # Derive SE from 95% CI: SE ~ (log(ci_high) - log(ci_low)) / (2 * 1.96)
        log_mu = math.log(rr)
        log_se = (math.log(ci_high) - math.log(ci_low)) / (2.0 * 1.96)
        log_params.append((log_mu, log_se))

    mitigated_samples: list[float] = []

    for _ in range(n_samples):
        # 1. Sample baseline from Beta
        baseline = _sample_beta(rng, baseline_alpha, baseline_beta)

        # 2. Sample RR for each mitigation from LogNormal
        sampled_rrs: list[float] = []
        for log_mu, log_se in log_params:
            log_rr = rng.gauss(log_mu, log_se)
            sampled_rrs.append(math.exp(log_rr))

        # 3. Combine using correlated pairwise
        combined_rr = combine_multiple_rrs(mitigation_ids, sampled_rrs)

        # 4. Mitigated risk
        mitigated = baseline * combined_rr
        mitigated_samples.append(min(mitigated, 1.0))

    # Sort for percentile computation
    mitigated_samples.sort()

    idx_2_5 = int(n_samples * 0.025)
    idx_50 = int(n_samples * 0.50)
    idx_97_5 = int(n_samples * 0.975)

    return {
        "median": mitigated_samples[idx_50],
        "p2_5": mitigated_samples[idx_2_5],
        "p97_5": mitigated_samples[idx_97_5],
        "mean": sum(mitigated_samples) / len(mitigated_samples),
        "n_samples": n_samples,
    }


def _sample_beta(rng: random.Random, alpha: float, beta: float) -> float:
    """Sample from Beta(alpha, beta) using the gamma-ratio method.

    Python's ``random.betavariate`` is available but we use the rng instance
    for reproducibility.

    Args:
        rng: Seeded Random instance.
        alpha: Alpha shape parameter (> 0).
        beta: Beta shape parameter (> 0).

    Returns:
        A sample in [0, 1].
    """
    x = rng.gammavariate(alpha, 1.0)
    y = rng.gammavariate(beta, 1.0)
    if x + y == 0:
        return 0.5
    return x / (x + y)


# ---------------------------------------------------------------------------
# High-level convenience function
# ---------------------------------------------------------------------------

def calculate_mitigated_risk(
    baseline_crs: float,
    baseline_icans: float,
    selected_ids: list[str],
) -> dict[str, Any]:
    """Calculate mitigated risk estimates for CRS and ICANS.

    Filters the selected mitigation strategies by their target adverse events,
    computes the deterministic combined RR for each AE type, and returns
    mitigated risk estimates.

    Args:
        baseline_crs: Baseline CRS risk (proportion, 0-1).
        baseline_icans: Baseline ICANS risk (proportion, 0-1).
        selected_ids: List of mitigation strategy IDs to apply.

    Returns:
        Dict with structure::

            {
                "crs": MitigationResult,
                "icans": MitigationResult,
                "selected_strategies": [MitigationStrategy, ...],
            }
    """
    strategies = [MITIGATION_STRATEGIES[mid] for mid in selected_ids]

    results: dict[str, Any] = {
        "selected_strategies": strategies,
    }

    for ae_type, baseline in [("crs", baseline_crs), ("icans", baseline_icans)]:
        ae_upper = ae_type.upper()

        # Filter mitigations that target this AE type
        applicable_ids: list[str] = []
        applicable_rrs: list[float] = []

        for mid in selected_ids:
            strategy = MITIGATION_STRATEGIES[mid]
            if ae_upper in strategy.target_aes:
                applicable_ids.append(mid)
                applicable_rrs.append(strategy.relative_risk)

        if not applicable_ids:
            results[ae_type] = MitigationResult(
                baseline_risk=baseline,
                mitigated_risk=baseline,
                combined_rr=1.0,
                selected_mitigations=[],
                correlations_applied=[],
            )
            continue

        # Combine with correlation adjustment
        correlations_log: list[dict[str, Any]] = []

        if len(applicable_ids) == 1:
            combined_rr = applicable_rrs[0]
        else:
            # Log the correlations that will be applied
            for i in range(len(applicable_ids)):
                for j in range(i + 1, len(applicable_ids)):
                    rho = get_mitigation_correlation(
                        applicable_ids[i], applicable_ids[j],
                    )
                    if rho > 0.0:
                        correlations_log.append({
                            "pair": (applicable_ids[i], applicable_ids[j]),
                            "rho": rho,
                        })

            combined_rr = combine_multiple_rrs(applicable_ids, applicable_rrs)

        mitigated_risk = baseline * combined_rr

        results[ae_type] = MitigationResult(
            baseline_risk=baseline,
            mitigated_risk=min(mitigated_risk, 1.0),
            combined_rr=combined_rr,
            selected_mitigations=applicable_ids,
            correlations_applied=correlations_log,
        )

    return results
