"""
Fairness metrics for PSP evaluation.

Ensures the platform produces equitable predictions across demographic subgroups:
- Equalized odds (equal TPR and FPR across groups)
- Demographic parity (equal positive prediction rates)
- Calibration across subgroups (predictions equally well-calibrated)

Target: < 5% disparity across demographic groups.
"""

from dataclasses import dataclass, field
from typing import Optional

from evals.metrics.clinical_metrics import GradedOutcome, GradedPrediction, EvalResult


@dataclass
class SubgroupLabel:
    """Assigns a patient to a demographic subgroup for fairness analysis."""
    patient_id: str
    group_name: str  # e.g., "age_65_plus", "male", "black", "hispanic"


# ---------------------------------------------------------------------------
# Equalized Odds
# ---------------------------------------------------------------------------

def equalized_odds(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
    subgroups: list[SubgroupLabel],
    threshold: float = 0.50,
    severity_threshold: int = 3,
) -> EvalResult:
    """Compute equalized odds disparity across demographic subgroups.

    Equalized odds requires that TPR and FPR are equal across groups.
    Returns the maximum disparity (max group TPR - min group TPR, same for FPR).

    Args:
        outcomes: Actual outcomes.
        predictions: Predicted risk scores.
        subgroups: Group labels for each patient.
        threshold: Risk score threshold for positive prediction.
        severity_threshold: Grade threshold for positive outcome class.
    """
    pred_map = {p.patient_id: p for p in predictions}
    outcome_map = {o.patient_id: o for o in outcomes}
    group_map = {s.patient_id: s.group_name for s in subgroups}

    # Collect per-group stats
    group_stats: dict[str, dict] = {}

    for pid, group in group_map.items():
        outcome = outcome_map.get(pid)
        pred = pred_map.get(pid)
        if outcome is None or pred is None:
            continue

        if group not in group_stats:
            group_stats[group] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

        actual_positive = outcome.event_occurred and outcome.severity_grade >= severity_threshold
        predicted_positive = pred.risk_score >= threshold

        stats = group_stats[group]
        if actual_positive and predicted_positive:
            stats["tp"] += 1
        elif actual_positive and not predicted_positive:
            stats["fn"] += 1
        elif not actual_positive and predicted_positive:
            stats["fp"] += 1
        else:
            stats["tn"] += 1

    # Compute TPR and FPR per group
    group_tpr = {}
    group_fpr = {}
    for group, stats in group_stats.items():
        pos = stats["tp"] + stats["fn"]
        neg = stats["fp"] + stats["tn"]
        group_tpr[group] = stats["tp"] / pos if pos > 0 else 0.0
        group_fpr[group] = stats["fp"] / neg if neg > 0 else 0.0

    if not group_tpr:
        return EvalResult("equalized_odds", 0.0, n_samples=0)

    tpr_disparity = max(group_tpr.values()) - min(group_tpr.values())
    fpr_disparity = max(group_fpr.values()) - min(group_fpr.values())
    max_disparity = max(tpr_disparity, fpr_disparity)

    return EvalResult(
        "equalized_odds",
        round(max_disparity, 4),
        n_samples=sum(sum(s.values()) for s in group_stats.values()),
        details={
            "group_tpr": {g: round(v, 4) for g, v in group_tpr.items()},
            "group_fpr": {g: round(v, 4) for g, v in group_fpr.items()},
            "tpr_disparity": round(tpr_disparity, 4),
            "fpr_disparity": round(fpr_disparity, 4),
        },
    )


# ---------------------------------------------------------------------------
# Demographic Parity
# ---------------------------------------------------------------------------

def demographic_parity(
    predictions: list[GradedPrediction],
    subgroups: list[SubgroupLabel],
    threshold: float = 0.50,
) -> EvalResult:
    """Compute demographic parity disparity across subgroups.

    Demographic parity requires that the positive prediction rate is equal
    across groups: P(predicted_positive | group_A) = P(predicted_positive | group_B).

    Returns the max disparity in positive prediction rates.
    """
    pred_map = {p.patient_id: p for p in predictions}
    group_map = {s.patient_id: s.group_name for s in subgroups}

    group_counts: dict[str, dict] = {}

    for pid, group in group_map.items():
        pred = pred_map.get(pid)
        if pred is None:
            continue
        if group not in group_counts:
            group_counts[group] = {"positive": 0, "total": 0}
        group_counts[group]["total"] += 1
        if pred.risk_score >= threshold:
            group_counts[group]["positive"] += 1

    group_rates = {}
    for group, counts in group_counts.items():
        group_rates[group] = counts["positive"] / counts["total"] if counts["total"] > 0 else 0.0

    if not group_rates:
        return EvalResult("demographic_parity", 0.0, n_samples=0)

    disparity = max(group_rates.values()) - min(group_rates.values())

    return EvalResult(
        "demographic_parity",
        round(disparity, 4),
        n_samples=sum(c["total"] for c in group_counts.values()),
        details={"group_positive_rates": {g: round(v, 4) for g, v in group_rates.items()}},
    )


# ---------------------------------------------------------------------------
# Calibration Across Subgroups
# ---------------------------------------------------------------------------

def calibration_by_subgroup(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
    subgroups: list[SubgroupLabel],
    n_bins: int = 5,
) -> EvalResult:
    """Compute Expected Calibration Error (ECE) per subgroup.

    Returns the max ECE disparity across groups. Target: < 5% disparity.
    """
    pred_map = {p.patient_id: p for p in predictions}
    outcome_map = {o.patient_id: o for o in outcomes}
    group_map = {s.patient_id: s.group_name for s in subgroups}

    # Organize by group
    group_data: dict[str, list] = {}
    for pid, group in group_map.items():
        outcome = outcome_map.get(pid)
        pred = pred_map.get(pid)
        if outcome is None or pred is None:
            continue
        if group not in group_data:
            group_data[group] = []
        actual = 1 if outcome.event_occurred else 0
        group_data[group].append((actual, pred.risk_score))

    # Compute ECE per group
    group_ece = {}
    for group, pairs in group_data.items():
        if not pairs:
            group_ece[group] = 0.0
            continue

        bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
        ece = 0.0
        for i in range(n_bins):
            lo = bin_boundaries[i]
            hi = bin_boundaries[i + 1]
            bin_pairs = [(l, s) for l, s in pairs if lo <= s < hi]
            if not bin_pairs:
                continue
            avg_pred = sum(s for _, s in bin_pairs) / len(bin_pairs)
            avg_actual = sum(l for l, _ in bin_pairs) / len(bin_pairs)
            ece += (len(bin_pairs) / len(pairs)) * abs(avg_pred - avg_actual)

        group_ece[group] = round(ece, 4)

    if not group_ece:
        return EvalResult("calibration_by_subgroup", 0.0, n_samples=0)

    max_ece = max(group_ece.values())
    min_ece = min(group_ece.values())
    disparity = max_ece - min_ece

    return EvalResult(
        "calibration_by_subgroup",
        round(disparity, 4),
        n_samples=sum(len(pairs) for pairs in group_data.values()),
        details={
            "group_ece": group_ece,
            "max_ece": max_ece,
            "min_ece": min_ece,
        },
    )
