"""Cross-source signal triangulation: FAERS vs ClinicalTrials.gov.

Compares spontaneous FAERS reporting rates with controlled clinical trial
AE rates from ClinicalTrials.gov to identify divergences that may warrant
further investigation.

Important caveats:
- FAERS rates are spontaneous reporting rates (voluntary), not true incidence
- CT.gov rates are from controlled trials with specific eligibility criteria
- Direct comparison has inherent limitations (different populations, reporting biases)
- Divergence flags are hypothesis-generating, not confirmatory
"""

from __future__ import annotations

from src.data.faers_cache import get_faers_comparison
from src.data.ctgov_cache import get_trial_summaries


# Map FAERS comparison keys to CT.gov AE type keys
_FAERS_TO_CTGOV_MAP: dict[str, str | None] = {
    "crs_comparison": "crs",
    "neurotoxicity_comparison": "icans",
    "infection_comparison": "infections",
    "cytopenia_comparison": "cytopenias",
}

# Human-readable labels for AE types
_AE_LABELS: dict[str, str] = {
    "crs": "Cytokine Release Syndrome",
    "icans": "ICANS / Neurotoxicity",
    "infections": "Infections",
    "cytopenias": "Cytopenias",
}

_METHODOLOGY = (
    "This analysis cross-references FAERS spontaneous reporting rates with "
    "enrollment-weighted average AE rates from ClinicalTrials.gov trials. "
    "Divergence is computed as (FAERS rate - trial rate) / trial rate * 100. "
    "Flags: 'aligned' (<25% absolute divergence), 'moderate' (25-75%), "
    "'significant' (>75%). FAERS rates reflect voluntary adverse event reporting "
    "and are NOT true incidence rates. Clinical trial rates come from controlled "
    "studies with specific eligibility criteria. Direct comparison has inherent "
    "limitations including different patient populations, indication mix, "
    "reporting biases, and denominator differences. Divergence flags are "
    "hypothesis-generating signals, not confirmatory findings."
)

_CAVEATS = [
    "FAERS spontaneous reporting rates are not true incidence rates; "
    "under-reporting and stimulated reporting can distort results.",
    "Clinical trial populations differ from real-world FAERS reporters "
    "(age, comorbidities, indication, line of therapy).",
    "FAERS denominators are total reports per product, not patient counts; "
    "trial denominators are enrolled patients.",
    "Mortality has no direct CT.gov equivalent in this dataset and is "
    "excluded from triangulation.",
    "Divergence thresholds (25%, 75%) are exploratory and have not been "
    "validated against external benchmarks.",
]


def _compute_weighted_trial_rate(
    trials: list[dict], ae_type: str,
) -> dict[str, float]:
    """Compute enrollment-weighted mean AE rate across trials.

    Returns dict with ``weighted_rate_pct``, ``total_enrollment``, and
    ``trials_with_data``.
    """
    total_weight = 0
    weighted_sum = 0.0
    trials_with_data = 0

    for trial in trials:
        enrollment = trial.get("enrollment", 0)
        if enrollment <= 0:
            continue
        ae_rates = trial.get("ae_rates", {})
        ae_info = ae_rates.get(ae_type, {})
        rate = ae_info.get("rate_pct", 0.0)
        # Only count trials that actually reported this AE type
        at_risk = ae_info.get("at_risk", 0)
        if at_risk > 0:
            weighted_sum += rate * enrollment
            total_weight += enrollment
            trials_with_data += 1

    if total_weight == 0:
        return {
            "weighted_rate_pct": 0.0,
            "total_enrollment": 0,
            "trials_with_data": 0,
        }

    return {
        "weighted_rate_pct": round(weighted_sum / total_weight, 2),
        "total_enrollment": total_weight,
        "trials_with_data": trials_with_data,
    }


def _compute_divergence(
    faers_rate: float, trial_rate: float,
) -> dict[str, float | str]:
    """Compute divergence between FAERS and trial rates.

    Returns dict with ``divergence_pct``, ``direction``, and ``flag``.
    """
    if trial_rate == 0:
        # Cannot compute meaningful divergence when trial rate is zero
        if faers_rate > 0:
            return {
                "divergence_pct": float("inf"),
                "direction": "faers_higher",
                "flag": "significant",
            }
        return {
            "divergence_pct": 0.0,
            "direction": "aligned",
            "flag": "aligned",
        }

    divergence_pct = round((faers_rate - trial_rate) / trial_rate * 100, 1)
    abs_div = abs(divergence_pct)

    if faers_rate > trial_rate:
        direction = "faers_higher"
    elif faers_rate < trial_rate:
        direction = "trial_higher"
    else:
        direction = "aligned"

    if abs_div < 25:
        flag = "aligned"
    elif abs_div < 75:
        flag = "moderate"
    else:
        flag = "significant"

    return {
        "divergence_pct": divergence_pct,
        "direction": direction,
        "flag": flag,
    }


def triangulate_signals(ae_type: str | None = None) -> dict:
    """Compare FAERS reporting rates with clinical trial rates.

    Parameters
    ----------
    ae_type:
        Optional filter: one of ``"crs"``, ``"icans"``, ``"infections"``,
        ``"cytopenias"``.  If ``None``, analyzes all mapped AE types.

    Returns
    -------
    dict with:
        - ``signals``: list of per-product-per-AE signal dicts
        - ``summary``: counts of total signals, flagged, AE types analyzed
        - ``methodology``: explanation of approach
        - ``caveats``: list of limitation strings
    """
    faers_data = get_faers_comparison()
    comparison = faers_data.get("comparison", {})
    total_reports = comparison.get("total_reports_by_product", {})

    trials = get_trial_summaries()

    # Determine which AE types to analyze
    if ae_type:
        ae_type = ae_type.lower().strip()
        # Find the FAERS key for this ae_type
        matching = {
            k: v for k, v in _FAERS_TO_CTGOV_MAP.items()
            if v == ae_type
        }
        if not matching:
            return {
                "signals": [],
                "summary": {
                    "total_signals": 0,
                    "flagged_count": 0,
                    "ae_types_analyzed": [],
                },
                "methodology": _METHODOLOGY,
                "caveats": _CAVEATS,
            }
        ae_map = matching
    else:
        ae_map = _FAERS_TO_CTGOV_MAP

    signals = []
    ae_types_analyzed = []

    for faers_key, ctgov_key in ae_map.items():
        if ctgov_key is None:
            continue

        ae_types_analyzed.append(ctgov_key)

        # Compute enrollment-weighted trial rate
        trial_info = _compute_weighted_trial_rate(trials, ctgov_key)
        trial_rate = trial_info["weighted_rate_pct"]

        # Get FAERS rates per product
        faers_ae_data = comparison.get(faers_key, {})

        for product, product_data in faers_ae_data.items():
            faers_rate = product_data.get("rate_pct", 0.0)
            faers_count = product_data.get("count", 0)
            product_total = total_reports.get(product, 0)

            div = _compute_divergence(faers_rate, trial_rate)

            # Confidence level based on data volume
            if faers_count >= 100 and trial_info["trials_with_data"] >= 5:
                confidence_level = "high"
            elif faers_count >= 20 and trial_info["trials_with_data"] >= 2:
                confidence_level = "moderate"
            else:
                confidence_level = "low"

            signals.append({
                "ae_type": ctgov_key,
                "ae_label": _AE_LABELS.get(ctgov_key, ctgov_key),
                "product": product,
                "faers_rate_pct": faers_rate,
                "faers_count": faers_count,
                "faers_total_reports": product_total,
                "trial_rate_pct": trial_rate,
                "trial_enrollment": trial_info["total_enrollment"],
                "trials_with_data": trial_info["trials_with_data"],
                "divergence_pct": div["divergence_pct"],
                "direction": div["direction"],
                "flag": div["flag"],
                "confidence_level": confidence_level,
            })

    flagged = [s for s in signals if s["flag"] != "aligned"]

    return {
        "signals": signals,
        "summary": {
            "total_signals": len(signals),
            "flagged_count": len(flagged),
            "significant_count": sum(
                1 for s in signals if s["flag"] == "significant"
            ),
            "moderate_count": sum(
                1 for s in signals if s["flag"] == "moderate"
            ),
            "aligned_count": sum(
                1 for s in signals if s["flag"] == "aligned"
            ),
            "ae_types_analyzed": ae_types_analyzed,
        },
        "methodology": _METHODOLOGY,
        "caveats": _CAVEATS,
    }
