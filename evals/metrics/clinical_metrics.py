"""
Custom clinical metrics for PSP evaluation.

Metrics designed for graded adverse event prediction in cell therapy:
- AUROC for graded severity events (ordinal, not binary)
- Net Reclassification Improvement (NRI)
- Calibration error (Expected Calibration Error)
- Onset timing MAE (mean absolute error for time-to-event)
- Brier score for probabilistic calibration
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class GradedOutcome:
    """A single patient's actual outcome with severity grade."""
    patient_id: str
    event_occurred: bool
    severity_grade: int  # 0 = no event, 1-4 = CRS/ICANS grades
    onset_hours: Optional[float] = None  # Hours post-infusion, None if no event


@dataclass
class GradedPrediction:
    """A single patient's predicted outcome."""
    patient_id: str
    risk_score: float  # 0.0 - 1.0 predicted probability
    predicted_grade_distribution: dict  # {0: p, 1: p, 2: p, 3: p, 4: p}
    predicted_onset_hours: Optional[float] = None


@dataclass
class EvalResult:
    """Result of running an evaluation metric."""
    metric_name: str
    value: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    n_samples: int = 0
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


# ---------------------------------------------------------------------------
# AUROC for Graded Events
# ---------------------------------------------------------------------------

def auroc_graded(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
    severity_threshold: int = 3,
) -> EvalResult:
    """Compute AUROC for detecting events at or above a severity threshold.

    For CRS, the primary metric is AUROC for Grade 3+ events (severe CRS).

    Args:
        outcomes: Actual patient outcomes with severity grades.
        predictions: Predicted risk scores.
        severity_threshold: Grade threshold for positive class (default: Grade 3+).

    Returns:
        EvalResult with AUROC value.
    """
    if len(outcomes) != len(predictions):
        raise ValueError("outcomes and predictions must have the same length.")

    # Build paired (label, score) list
    pairs = []
    pred_map = {p.patient_id: p for p in predictions}
    for outcome in outcomes:
        pred = pred_map.get(outcome.patient_id)
        if pred is None:
            continue
        label = 1 if (outcome.event_occurred and outcome.severity_grade >= severity_threshold) else 0
        pairs.append((label, pred.risk_score))

    if not pairs:
        return EvalResult("auroc_graded", 0.0, n_samples=0)

    n_pos = sum(1 for l, _ in pairs if l == 1)
    n_neg = sum(1 for l, _ in pairs if l == 0)

    if n_pos == 0 or n_neg == 0:
        return EvalResult(
            "auroc_graded", 0.5, n_samples=len(pairs),
            details={"warning": "Only one class present, AUROC undefined. Returning 0.5."},
        )

    # Mann-Whitney U statistic for AUROC
    # Sort by score descending
    pairs.sort(key=lambda x: x[1], reverse=True)

    tp = 0
    fp = 0
    tp_prev = 0
    fp_prev = 0
    auc = 0.0
    score_prev = float("inf")

    for label, score in pairs:
        if score != score_prev:
            auc += _trapezoid_area(fp, fp_prev, tp, tp_prev)
            score_prev = score
            tp_prev = tp
            fp_prev = fp
        if label == 1:
            tp += 1
        else:
            fp += 1

    auc += _trapezoid_area(fp, fp_prev, tp, tp_prev)

    if tp * fp == 0:
        auroc = 0.5
    else:
        auroc = auc / (tp * fp)

    return EvalResult(
        "auroc_graded",
        round(auroc, 4),
        n_samples=len(pairs),
        details={"n_positive": n_pos, "n_negative": n_neg, "severity_threshold": severity_threshold},
    )


def _trapezoid_area(x1: int, x2: int, y1: int, y2: int) -> float:
    """Area under the trapezoid for ROC computation."""
    return abs(x1 - x2) * (y1 + y2) / 2.0


# ---------------------------------------------------------------------------
# Net Reclassification Improvement (NRI)
# ---------------------------------------------------------------------------

def net_reclassification_improvement(
    outcomes: list[GradedOutcome],
    old_predictions: list[GradedPrediction],
    new_predictions: list[GradedPrediction],
    risk_thresholds: tuple = (0.20, 0.50),
) -> EvalResult:
    """Compute category-based NRI comparing old vs new model predictions.

    Risk categories defined by thresholds: low (< t1), medium (t1 - t2), high (>= t2).

    Positive NRI means the new model improves classification.
    """
    if len(outcomes) != len(old_predictions) or len(outcomes) != len(new_predictions):
        raise ValueError("All input lists must have the same length.")

    old_map = {p.patient_id: p for p in old_predictions}
    new_map = {p.patient_id: p for p in new_predictions}

    def categorize(score: float) -> int:
        if score < risk_thresholds[0]:
            return 0  # Low
        elif score < risk_thresholds[1]:
            return 1  # Medium
        return 2  # High

    events_up = 0
    events_down = 0
    events_total = 0
    nonevents_up = 0
    nonevents_down = 0
    nonevents_total = 0

    for outcome in outcomes:
        old_pred = old_map.get(outcome.patient_id)
        new_pred = new_map.get(outcome.patient_id)
        if old_pred is None or new_pred is None:
            continue

        old_cat = categorize(old_pred.risk_score)
        new_cat = categorize(new_pred.risk_score)

        if outcome.event_occurred:
            events_total += 1
            if new_cat > old_cat:
                events_up += 1  # Correctly moved up
            elif new_cat < old_cat:
                events_down += 1  # Incorrectly moved down
        else:
            nonevents_total += 1
            if new_cat > old_cat:
                nonevents_up += 1  # Incorrectly moved up
            elif new_cat < old_cat:
                nonevents_down += 1  # Correctly moved down

    nri_events = (events_up - events_down) / events_total if events_total > 0 else 0.0
    nri_nonevents = (nonevents_down - nonevents_up) / nonevents_total if nonevents_total > 0 else 0.0
    nri = nri_events + nri_nonevents

    return EvalResult(
        "nri",
        round(nri, 4),
        n_samples=events_total + nonevents_total,
        details={
            "nri_events": round(nri_events, 4),
            "nri_nonevents": round(nri_nonevents, 4),
            "events_reclassified_up": events_up,
            "events_reclassified_down": events_down,
            "nonevents_reclassified_up": nonevents_up,
            "nonevents_reclassified_down": nonevents_down,
        },
    )


# ---------------------------------------------------------------------------
# Expected Calibration Error (ECE)
# ---------------------------------------------------------------------------

def expected_calibration_error(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
    n_bins: int = 10,
) -> EvalResult:
    """Compute Expected Calibration Error.

    ECE measures how well predicted probabilities match observed frequencies.
    Lower is better. Target: < 0.15.

    Bins predictions by risk score, then compares average predicted probability
    to actual event rate in each bin.
    """
    if len(outcomes) != len(predictions):
        raise ValueError("outcomes and predictions must have the same length.")

    pred_map = {p.patient_id: p for p in predictions}
    pairs = []
    for outcome in outcomes:
        pred = pred_map.get(outcome.patient_id)
        if pred:
            pairs.append((1 if outcome.event_occurred else 0, pred.risk_score))

    if not pairs:
        return EvalResult("ece", 0.0, n_samples=0)

    # Sort into bins
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0
    bin_details = []

    for i in range(n_bins):
        lo = bin_boundaries[i]
        hi = bin_boundaries[i + 1]
        bin_pairs = [(label, score) for label, score in pairs if lo <= score < hi]
        if not bin_pairs:
            continue

        avg_predicted = sum(s for _, s in bin_pairs) / len(bin_pairs)
        avg_actual = sum(l for l, _ in bin_pairs) / len(bin_pairs)
        bin_weight = len(bin_pairs) / len(pairs)
        ece += bin_weight * abs(avg_predicted - avg_actual)

        bin_details.append({
            "bin": f"[{lo:.1f}, {hi:.1f})",
            "count": len(bin_pairs),
            "avg_predicted": round(avg_predicted, 4),
            "avg_actual": round(avg_actual, 4),
        })

    return EvalResult(
        "ece",
        round(ece, 4),
        n_samples=len(pairs),
        details={"bins": bin_details},
    )


# ---------------------------------------------------------------------------
# Brier Score
# ---------------------------------------------------------------------------

def brier_score(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
) -> EvalResult:
    """Compute Brier score (mean squared error of probability predictions).

    Brier = (1/N) * sum((predicted - actual)^2)
    Range: 0 (perfect) to 1 (worst). Target: < 0.15.
    """
    pred_map = {p.patient_id: p for p in predictions}
    errors_sq = []

    for outcome in outcomes:
        pred = pred_map.get(outcome.patient_id)
        if pred is None:
            continue
        actual = 1.0 if outcome.event_occurred else 0.0
        errors_sq.append((pred.risk_score - actual) ** 2)

    if not errors_sq:
        return EvalResult("brier_score", 0.0, n_samples=0)

    bs = sum(errors_sq) / len(errors_sq)
    return EvalResult("brier_score", round(bs, 4), n_samples=len(errors_sq))


# ---------------------------------------------------------------------------
# Onset Timing MAE
# ---------------------------------------------------------------------------

def onset_timing_mae(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
) -> EvalResult:
    """Compute Mean Absolute Error for onset timing predictions.

    Only evaluated for patients who actually experienced an event.
    Target: MAE < 12 hours.
    """
    pred_map = {p.patient_id: p for p in predictions}
    errors = []

    for outcome in outcomes:
        if not outcome.event_occurred or outcome.onset_hours is None:
            continue
        pred = pred_map.get(outcome.patient_id)
        if pred is None or pred.predicted_onset_hours is None:
            continue
        errors.append(abs(outcome.onset_hours - pred.predicted_onset_hours))

    if not errors:
        return EvalResult("onset_timing_mae", 0.0, n_samples=0, details={"warning": "No events with timing data."})

    mae = sum(errors) / len(errors)
    return EvalResult(
        "onset_timing_mae",
        round(mae, 2),
        n_samples=len(errors),
        details={"median_ae": round(sorted(errors)[len(errors) // 2], 2)},
    )


# ---------------------------------------------------------------------------
# Sensitivity at Fixed Specificity
# ---------------------------------------------------------------------------

def sensitivity_at_specificity(
    outcomes: list[GradedOutcome],
    predictions: list[GradedPrediction],
    target_specificity: float = 0.90,
    severity_threshold: int = 3,
) -> EvalResult:
    """Compute sensitivity (true positive rate) at a given specificity level.

    Target: sensitivity > 0.70 at 90% specificity for Grade 3+ events.
    """
    pred_map = {p.patient_id: p for p in predictions}
    pairs = []
    for outcome in outcomes:
        pred = pred_map.get(outcome.patient_id)
        if pred is None:
            continue
        label = 1 if (outcome.event_occurred and outcome.severity_grade >= severity_threshold) else 0
        pairs.append((label, pred.risk_score))

    if not pairs:
        return EvalResult("sensitivity_at_specificity", 0.0, n_samples=0)

    n_neg = sum(1 for l, _ in pairs if l == 0)
    if n_neg == 0:
        return EvalResult("sensitivity_at_specificity", 1.0, n_samples=len(pairs))

    # Find threshold that achieves target specificity
    pairs.sort(key=lambda x: x[1])
    # Specificity = TN / (TN + FP). At threshold t, negatives below t are TN.
    thresholds = sorted(set(s for _, s in pairs))

    best_sensitivity = 0.0
    for t in thresholds:
        tn = sum(1 for l, s in pairs if l == 0 and s < t)
        fp = sum(1 for l, s in pairs if l == 0 and s >= t)
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0
        if spec >= target_specificity:
            tp = sum(1 for l, s in pairs if l == 1 and s >= t)
            fn = sum(1 for l, s in pairs if l == 1 and s < t)
            sens = tp / (tp + fn) if (tp + fn) > 0 else 0
            best_sensitivity = max(best_sensitivity, sens)

    return EvalResult(
        "sensitivity_at_specificity",
        round(best_sensitivity, 4),
        n_samples=len(pairs),
        details={"target_specificity": target_specificity, "severity_threshold": severity_threshold},
    )
