"""
Model validation framework for risk estimation models.

Provides tools to assess the quality and reliability of adverse event rate
estimates produced by the model registry.  Includes calibration diagnostics,
scoring rules, coverage analysis, cross-validation, and head-to-head model
comparison.

All functions operate on standardised result dicts as produced by
``model_registry.estimate_risk()``.
"""

from __future__ import annotations

import math
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. Calibration check
# ---------------------------------------------------------------------------

def calibration_check(
    predicted_rates: list[float],
    observed_rates: list[float],
    n_bins: int = 10,
) -> dict[str, Any]:
    """Produce calibration-plot data (predicted vs observed in bins).

    Divides predictions into equal-width bins and computes the mean predicted
    and mean observed rate in each bin.  Perfect calibration yields points on
    the identity line.

    Args:
        predicted_rates: Predicted probabilities (0-1 scale).
        observed_rates: Observed binary outcomes (0 or 1) or proportions.
        n_bins: Number of calibration bins.

    Returns:
        Dict with:
            - bins: list[dict] with bin_center, mean_predicted, mean_observed, n
            - calibration_error: mean absolute difference across bins
            - n_total: total observations
    """
    if len(predicted_rates) != len(observed_rates):
        raise ValueError(
            "predicted_rates and observed_rates must have the same length"
        )

    n = len(predicted_rates)
    if n == 0:
        raise ValueError("At least one observation is required")

    # Sort into bins by predicted rate
    bin_width = 1.0 / n_bins
    bins = []
    abs_errors = []

    for i in range(n_bins):
        lo = i * bin_width
        hi = (i + 1) * bin_width if i < n_bins - 1 else 1.0 + 1e-9

        in_bin_pred = []
        in_bin_obs = []
        for p, o in zip(predicted_rates, observed_rates):
            if lo <= p < hi:
                in_bin_pred.append(p)
                in_bin_obs.append(o)

        if in_bin_pred:
            mean_pred = sum(in_bin_pred) / len(in_bin_pred)
            mean_obs = sum(in_bin_obs) / len(in_bin_obs)
            abs_errors.append(abs(mean_pred - mean_obs))
            bins.append({
                "bin_center": round(lo + bin_width / 2, 4),
                "mean_predicted": round(mean_pred, 6),
                "mean_observed": round(mean_obs, 6),
                "n": len(in_bin_pred),
            })

    calibration_error = (
        sum(abs_errors) / len(abs_errors) if abs_errors else 0.0
    )

    return {
        "bins": bins,
        "calibration_error": round(calibration_error, 6),
        "n_bins_populated": len(bins),
        "n_total": n,
    }


# ---------------------------------------------------------------------------
# 2. Brier score
# ---------------------------------------------------------------------------

def brier_score(
    predictions: list[float],
    outcomes: list[int | float],
) -> dict[str, Any]:
    """Compute the Brier score (mean squared prediction error).

    The Brier score ranges from 0 (perfect) to 1 (worst).  A naive
    predictor using the base rate has a Brier score equal to p*(1-p).

    Args:
        predictions: Predicted probabilities (0-1 scale).
        outcomes: Binary outcomes (0 or 1).

    Returns:
        Dict with brier_score, reference_score (naive base-rate), and skill.
    """
    if len(predictions) != len(outcomes):
        raise ValueError(
            "predictions and outcomes must have the same length"
        )
    n = len(predictions)
    if n == 0:
        raise ValueError("At least one observation is required")

    bs = sum((p - o) ** 2 for p, o in zip(predictions, outcomes)) / n

    # Reference: predict the base rate for every observation
    base_rate = sum(outcomes) / n
    ref_score = base_rate * (1 - base_rate)

    # Brier skill score: 1 - BS/BS_ref (1 = perfect, 0 = no skill, <0 = worse)
    skill = 1 - bs / ref_score if ref_score > 0 else 0.0

    return {
        "brier_score": round(bs, 6),
        "reference_score": round(ref_score, 6),
        "brier_skill_score": round(skill, 6),
        "n": n,
        "base_rate": round(base_rate, 6),
        "interpretation": _interpret_brier(bs),
    }


def _interpret_brier(bs: float) -> str:
    """Human-readable interpretation of the Brier score."""
    if bs < 0.05:
        return "Excellent calibration"
    elif bs < 0.10:
        return "Good calibration"
    elif bs < 0.20:
        return "Moderate calibration"
    elif bs < 0.30:
        return "Poor calibration"
    else:
        return "Very poor calibration"


# ---------------------------------------------------------------------------
# 3. Coverage probability
# ---------------------------------------------------------------------------

def coverage_probability(
    ci_list: list[tuple[float, float]],
    true_rates: list[float],
) -> dict[str, Any]:
    """Assess whether confidence intervals contain the true rates.

    For each pair of (CI, true_rate), checks if true_rate falls within
    the interval.  Reports the empirical coverage probability, which
    should be close to the nominal level (e.g. 95%).

    Args:
        ci_list: List of (ci_low, ci_high) tuples (percentage scale).
        true_rates: Corresponding true rates (percentage scale).

    Returns:
        Dict with coverage probability, per-instance details, and diagnostics.
    """
    if len(ci_list) != len(true_rates):
        raise ValueError(
            "ci_list and true_rates must have the same length"
        )
    n = len(ci_list)
    if n == 0:
        raise ValueError("At least one CI is required")

    covered = 0
    details = []
    widths = []

    for (lo, hi), truth in zip(ci_list, true_rates):
        is_covered = lo <= truth <= hi
        if is_covered:
            covered += 1
        widths.append(hi - lo)
        details.append({
            "ci_low": round(lo, 4),
            "ci_high": round(hi, 4),
            "true_rate": round(truth, 4),
            "covered": is_covered,
        })

    empirical_coverage = covered / n
    mean_width = sum(widths) / n

    return {
        "coverage_probability": round(empirical_coverage, 4),
        "n_covered": covered,
        "n_total": n,
        "mean_ci_width": round(mean_width, 4),
        "details": details,
        "assessment": _assess_coverage(empirical_coverage, n),
    }


def _assess_coverage(coverage: float, n: int) -> str:
    """Assess whether coverage is consistent with nominal 95%."""
    # Standard error of coverage estimate
    se = math.sqrt(0.95 * 0.05 / n) if n > 0 else 0.0
    if abs(coverage - 0.95) < 2 * se:
        return "Consistent with 95% nominal coverage"
    elif coverage < 0.95:
        return "Under-coverage (intervals too narrow)"
    else:
        return "Over-coverage (intervals too wide / conservative)"


# ---------------------------------------------------------------------------
# 4. Leave-one-out cross-validation
# ---------------------------------------------------------------------------

def leave_one_out_cv(
    studies: list[dict[str, Any]],
    model_fn: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Leave-one-out cross-validation for study-level predictions.

    For each study, fits the model on all OTHER studies and predicts
    the held-out study's rate.  Reports prediction errors and coverage.

    Args:
        studies: List of study dicts, each with at least 'events' and 'n'.
        model_fn: A function that takes a data dict (with 'studies' key for
            meta-analysis or 'events'/'n' for single-study models) and
            returns a standardised result dict.

    Returns:
        Dict with per-fold results, RMSE, MAE, and coverage.
    """
    k = len(studies)
    if k < 2:
        raise ValueError("At least 2 studies are required for LOO-CV")

    fold_results = []
    errors = []
    ci_list = []
    true_rates = []

    for i in range(k):
        held_out = studies[i]
        training = [s for j, s in enumerate(studies) if j != i]

        # True rate of the held-out study
        true_rate_pct = (
            (held_out["events"] / held_out["n"]) * 100.0
            if held_out["n"] > 0
            else 0.0
        )

        # Build data for the model function
        # Try meta-analysis first (multi-study), fall back to pooled single
        try:
            data = {"studies": training}
            result = model_fn(data)
        except (ValueError, KeyError, TypeError):
            # Fall back to pooled counts
            pooled_events = sum(s["events"] for s in training)
            pooled_n = sum(s["n"] for s in training)
            data = {"events": pooled_events, "n": pooled_n}
            try:
                result = model_fn(data)
            except Exception as exc:
                logger.warning("LOO fold %d failed: %s", i, exc)
                continue

        pred_rate_pct = result["estimate_pct"]
        error = pred_rate_pct - true_rate_pct
        errors.append(error)
        ci_list.append((result["ci_low_pct"], result["ci_high_pct"]))
        true_rates.append(true_rate_pct)

        fold_results.append({
            "fold": i,
            "held_out_label": held_out.get("label", f"Study {i}"),
            "true_rate_pct": round(true_rate_pct, 4),
            "predicted_pct": round(pred_rate_pct, 4),
            "error_pct": round(error, 4),
            "ci_low_pct": round(result["ci_low_pct"], 4),
            "ci_high_pct": round(result["ci_high_pct"], 4),
            "covered": (
                result["ci_low_pct"] <= true_rate_pct <= result["ci_high_pct"]
            ),
        })

    n_folds = len(errors)
    if n_folds == 0:
        return {
            "folds": [],
            "rmse_pct": float("nan"),
            "mae_pct": float("nan"),
            "coverage": float("nan"),
            "n_folds": 0,
        }

    rmse = math.sqrt(sum(e ** 2 for e in errors) / n_folds)
    mae = sum(abs(e) for e in errors) / n_folds
    coverage = coverage_probability(ci_list, true_rates)

    return {
        "folds": fold_results,
        "rmse_pct": round(rmse, 4),
        "mae_pct": round(mae, 4),
        "coverage": coverage["coverage_probability"],
        "n_folds": n_folds,
    }


# ---------------------------------------------------------------------------
# 5. Model comparison
# ---------------------------------------------------------------------------

def model_comparison(
    studies: list[dict[str, Any]],
    model_fns: dict[str, Callable[[dict[str, Any]], dict[str, Any]]],
) -> dict[str, Any]:
    """Head-to-head comparison of multiple models via LOO cross-validation.

    Runs leave_one_out_cv for each model function and compiles a comparison
    table with RMSE, MAE, and coverage.

    Args:
        studies: List of study dicts.
        model_fns: Dict mapping model name to model function.

    Returns:
        Dict with per-model results and a ranked summary table.
    """
    results = {}
    summary = []

    for name, fn in model_fns.items():
        try:
            cv_result = leave_one_out_cv(studies, fn)
            results[name] = cv_result
            summary.append({
                "model": name,
                "rmse_pct": cv_result["rmse_pct"],
                "mae_pct": cv_result["mae_pct"],
                "coverage": cv_result["coverage"],
                "n_folds": cv_result["n_folds"],
            })
        except Exception as exc:
            results[name] = {"error": str(exc)}
            logger.warning("Model '%s' comparison failed: %s", name, exc)

    # Sort by RMSE ascending
    summary.sort(key=lambda x: x.get("rmse_pct", float("inf")))

    return {
        "per_model": results,
        "summary": summary,
        "best_model": summary[0]["model"] if summary else None,
    }


# ---------------------------------------------------------------------------
# 6. Sequential prediction test
# ---------------------------------------------------------------------------

def sequential_prediction_test(
    timeline: list[dict[str, Any]],
    model_fn: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Predict each timepoint from all preceding timepoints.

    At each timepoint t, fits the model on timepoints 0..t-1 and predicts
    the rate at timepoint t.  Measures how well the model tracks the
    evolving data.

    Args:
        timeline: Ordered list of study dicts, each with 'events' and 'n'.
            These are assumed to be incremental (non-cumulative).
        model_fn: Model function to test.

    Returns:
        Dict with per-step predictions, cumulative error, and trend.
    """
    if len(timeline) < 2:
        raise ValueError(
            "At least 2 timepoints are required for sequential prediction"
        )

    steps = []
    errors = []

    for t in range(1, len(timeline)):
        history = timeline[:t]
        current = timeline[t]

        true_rate_pct = (
            (current["events"] / current["n"]) * 100.0
            if current["n"] > 0
            else 0.0
        )

        # Try multi-study format
        try:
            data = {"studies": history}
            result = model_fn(data)
        except (ValueError, KeyError, TypeError):
            # Fall back to pooled
            pooled_events = sum(s["events"] for s in history)
            pooled_n = sum(s["n"] for s in history)
            data = {"events": pooled_events, "n": pooled_n}
            try:
                result = model_fn(data)
            except Exception as exc:
                logger.warning("Sequential step %d failed: %s", t, exc)
                continue

        pred_rate_pct = result["estimate_pct"]
        error = pred_rate_pct - true_rate_pct
        errors.append(error)

        steps.append({
            "step": t,
            "label": current.get("label", f"T{t}"),
            "n_history_studies": len(history),
            "true_rate_pct": round(true_rate_pct, 4),
            "predicted_pct": round(pred_rate_pct, 4),
            "error_pct": round(error, 4),
            "ci_low_pct": round(result["ci_low_pct"], 4),
            "ci_high_pct": round(result["ci_high_pct"], 4),
            "covered": (
                result["ci_low_pct"] <= true_rate_pct <= result["ci_high_pct"]
            ),
        })

    n_steps = len(errors)
    if n_steps == 0:
        return {
            "steps": [],
            "rmse_pct": float("nan"),
            "mae_pct": float("nan"),
            "n_steps": 0,
        }

    rmse = math.sqrt(sum(e ** 2 for e in errors) / n_steps)
    mae = sum(abs(e) for e in errors) / n_steps

    # Is the error decreasing over time? (negative slope = improving)
    if n_steps >= 2:
        abs_errors = [abs(e) for e in errors]
        x_mean = (n_steps - 1) / 2.0
        y_mean = sum(abs_errors) / n_steps
        cov = sum(
            (i - x_mean) * (ae - y_mean)
            for i, ae in enumerate(abs_errors)
        )
        var_x = sum((i - x_mean) ** 2 for i in range(n_steps))
        trend_slope = cov / var_x if var_x > 0 else 0.0
    else:
        trend_slope = 0.0

    return {
        "steps": steps,
        "rmse_pct": round(rmse, 4),
        "mae_pct": round(mae, 4),
        "n_steps": n_steps,
        "error_trend_slope": round(trend_slope, 6),
        "improving": trend_slope < 0,
    }
