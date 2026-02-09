"""ClinicalTrials.gov AE data loader and normalizer.

Loads pre-extracted adverse event data from ``analysis/results/ct_gov_ae_data.json``
and provides normalized trial summaries with computed AE rates for CRS, ICANS,
cytopenias, infections, and HLH.
"""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Any

logger = logging.getLogger(__name__)

# Path to the pre-extracted CT.gov data
_DATA_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "analysis"
    / "results"
    / "ct_gov_ae_data.json"
)

# ---------------------------------------------------------------------------
# AE term normalization map
# ---------------------------------------------------------------------------

AE_TERM_MAP: dict[str, list[str]] = {
    "crs": [
        "cytokine release syndrome",
        "cytokine release",
        "crs",
        "cytokine storm",
    ],
    "icans": [
        "neurotoxicity",
        "icans",
        "encephalopathy",
        "immune effector cell-associated neurotoxicity",
        "confused state",
        "aphasia",
        "tremor",
    ],
    "cytopenias": [
        "neutropenia",
        "thrombocytopenia",
        "anemia",
        "pancytopenia",
        "leukopenia",
        "lymphopenia",
        "febrile neutropenia",
    ],
    "infections": [
        "infection",
        "pneumonia",
        "sepsis",
        "bacteremia",
        "fungal infection",
        "viral infection",
    ],
    "hlh": [
        "hemophagocytic lymphohistiocytosis",
        "macrophage activation syndrome",
        "hlh",
        "mas",
    ],
}


def normalize_ae_term(term: str) -> str | None:
    """Map a raw AE term to a canonical category using substring matching.

    Returns the canonical category name (e.g. ``"crs"``) or ``None`` if the
    term does not match any known category.
    """
    lower = term.lower().strip()
    for category, patterns in AE_TERM_MAP.items():
        for pattern in patterns:
            if pattern in lower:
                return category
    return None


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_CACHE: dict[str, Any] | None = None


def _load_data() -> dict[str, Any]:
    """Load and cache the CT.gov JSON data."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    if not _DATA_PATH.is_file():
        logger.warning("CT.gov data file not found: %s", _DATA_PATH)
        _CACHE = {"metadata": {}, "summary": {}, "trial_details": []}
        return _CACHE

    with open(_DATA_PATH, encoding="utf-8") as f:
        _CACHE = json.load(f)
    return _CACHE


def get_summary() -> dict[str, Any]:
    """Return the top-level summary from the CT.gov data."""
    data = _load_data()
    return dict(data.get("summary", {}))


# ---------------------------------------------------------------------------
# AE rate computation
# ---------------------------------------------------------------------------


def _compute_ae_rate(
    events: list[dict[str, Any]], category: str
) -> dict[str, int | float]:
    """Compute the AE rate for a given category across event entries.

    Scans all events, finds those whose term matches the category via
    :func:`normalize_ae_term`, and returns the maximum affected/at_risk
    across all matching stats groups.

    Returns a dict with ``affected``, ``at_risk``, and ``rate_pct``.
    """
    max_affected = 0
    max_at_risk = 0

    for event in events:
        term = event.get("term", "")
        if normalize_ae_term(term) != category:
            continue
        for stat in event.get("stats", []):
            affected = stat.get("num_affected", 0)
            at_risk = stat.get("num_at_risk", 0)
            if affected > max_affected:
                max_affected = affected
                max_at_risk = at_risk
            elif affected == max_affected and at_risk > max_at_risk:
                max_at_risk = at_risk

    rate_pct = round(max_affected / max_at_risk * 100, 1) if max_at_risk > 0 else 0.0
    return {
        "affected": max_affected,
        "at_risk": max_at_risk,
        "rate_pct": rate_pct,
    }


def _build_trial_summary(trial: dict[str, Any]) -> dict[str, Any]:
    """Build a normalized trial summary with computed AE rates."""
    ae = trial.get("adverse_events", {})
    all_events = ae.get("serious_events", []) + ae.get("other_events", [])

    ae_rates: dict[str, dict[str, int | float]] = {}
    for category in AE_TERM_MAP:
        ae_rates[category] = _compute_ae_rate(all_events, category)

    return {
        "nct_id": trial.get("nct_id", ""),
        "title": trial.get("title", ""),
        "phase": trial.get("phase", ""),
        "enrollment": trial.get("enrollment", 0),
        "conditions": trial.get("conditions", []),
        "interventions": trial.get("interventions", []),
        "ae_rates": ae_rates,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_trial_summaries(
    *,
    min_enrollment: int = 0,
) -> list[dict[str, Any]]:
    """Return normalized trial summaries with AE rates.

    Parameters
    ----------
    min_enrollment:
        Only include trials with enrollment >= this value.
    """
    data = _load_data()
    trials = data.get("trial_details", [])
    summaries = [_build_trial_summary(t) for t in trials]
    if min_enrollment > 0:
        summaries = [s for s in summaries if s["enrollment"] >= min_enrollment]
    return summaries


def get_trial_ae_rates(
    ae_type: str = "crs",
    *,
    min_enrollment: int = 0,
) -> list[dict[str, Any]]:
    """Return trial summaries filtered to include a specific AE type's rates.

    Parameters
    ----------
    ae_type:
        One of the keys in :data:`AE_TERM_MAP` (e.g. ``"crs"``, ``"icans"``).
    min_enrollment:
        Only include trials with enrollment >= this value.
    """
    ae_type = ae_type.lower().strip()
    if ae_type not in AE_TERM_MAP:
        return []

    summaries = get_trial_summaries(min_enrollment=min_enrollment)
    result = []
    for s in summaries:
        rate_info = s["ae_rates"].get(ae_type, {})
        result.append({
            "nct_id": s["nct_id"],
            "title": s["title"],
            "phase": s["phase"],
            "enrollment": s["enrollment"],
            "conditions": s["conditions"],
            "ae_type": ae_type,
            "affected": rate_info.get("affected", 0),
            "at_risk": rate_info.get("at_risk", 0),
            "rate_pct": rate_info.get("rate_pct", 0.0),
        })
    return result
