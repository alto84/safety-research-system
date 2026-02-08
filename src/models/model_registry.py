"""
Model registry for population-level adverse event risk estimation.

Provides a unified interface to multiple statistical approaches for estimating
the true rate of serious adverse events in cell therapy populations.  Each model
returns a standardised result dict so callers can compare methods side by side.

Registered models:
    1. bayesian_beta_binomial  — conjugate Beta-Binomial with informative priors
    2. frequentist_exact       — Clopper-Pearson exact binomial CI
    3. wilson_score            — Wilson score interval (better coverage at small n)
    4. random_effects_meta     — DerSimonian-Laird random-effects meta-analysis
    5. empirical_bayes         — shrinkage estimator borrowing across AE types
    6. kaplan_meier            — non-parametric time-to-event estimate
    7. predictive_posterior    — predict rate in the *next* study, not just current

All percentage outputs are on the 0-100 scale for clinical readability.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable

from scipy.stats import beta as beta_dist
from scipy.stats import binom, norm

from src.models.bayesian_risk import PriorSpec, compute_posterior

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardised result type
# ---------------------------------------------------------------------------

def _result(
    estimate_pct: float,
    ci_low_pct: float,
    ci_high_pct: float,
    method: str,
    n_patients: int,
    n_events: int,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical result dict shared by every model."""
    return {
        "estimate_pct": round(estimate_pct, 4),
        "ci_low_pct": round(max(ci_low_pct, 0.0), 4),
        "ci_high_pct": round(min(ci_high_pct, 100.0), 4),
        "ci_width_pct": round(
            min(ci_high_pct, 100.0) - max(ci_low_pct, 0.0), 4
        ),
        "method": method,
        "n_patients": n_patients,
        "n_events": n_events,
        "metadata": metadata or {},
    }


# ---------------------------------------------------------------------------
# 1. Bayesian Beta-Binomial  (wraps existing compute_posterior)
# ---------------------------------------------------------------------------

def bayesian_beta_binomial(data: dict[str, Any]) -> dict[str, Any]:
    """Bayesian Beta-Binomial conjugate model.

    Suitable for small samples with informative priors.  Supports sequential
    updating as new data accrues.

    Required data keys:
        events (int): Number of adverse events observed.
        n (int): Total number of patients.

    Optional data keys:
        prior_alpha (float): Beta prior alpha.  Default 0.5 (Jeffreys).
        prior_beta (float): Beta prior beta.  Default 0.5 (Jeffreys).
        prior_source (str): Description of the prior.
    """
    events = data["events"]
    n = data["n"]
    alpha = data.get("prior_alpha", 0.5)
    beta_param = data.get("prior_beta", 0.5)
    source = data.get("prior_source", "Jeffreys non-informative")

    prior = PriorSpec(alpha=alpha, beta=beta_param, source_description=source)
    post = compute_posterior(prior, events, n)

    return _result(
        estimate_pct=post.mean,
        ci_low_pct=post.ci_low,
        ci_high_pct=post.ci_high,
        method="Bayesian Beta-Binomial",
        n_patients=n,
        n_events=events,
        metadata={
            "posterior_alpha": post.alpha,
            "posterior_beta": post.beta,
            "prior_alpha": alpha,
            "prior_beta": beta_param,
            "prior_source": source,
            "credible_interval_level": 0.95,
        },
    )


# ---------------------------------------------------------------------------
# 2. Frequentist exact binomial (Clopper-Pearson)
# ---------------------------------------------------------------------------

def frequentist_exact(data: dict[str, Any]) -> dict[str, Any]:
    """Clopper-Pearson exact binomial confidence interval.

    Conservative (guaranteed coverage >= nominal) but can be wide for small
    samples.  The gold standard for regulatory submissions.

    Required data keys:
        events (int): Number of adverse events observed.
        n (int): Total number of patients.

    Optional data keys:
        alpha (float): Significance level.  Default 0.05 (95% CI).
    """
    events = data["events"]
    n = data["n"]
    alpha = data.get("alpha", 0.05)

    if n == 0:
        return _result(
            estimate_pct=0.0,
            ci_low_pct=0.0,
            ci_high_pct=100.0,
            method="Clopper-Pearson Exact",
            n_patients=0,
            n_events=0,
            metadata={"alpha": alpha, "note": "n=0, no data"},
        )

    p_hat = events / n

    # Clopper-Pearson uses the Beta distribution relationship:
    #   Lower bound = Beta(alpha/2;  x,   n-x+1)
    #   Upper bound = Beta(1-alpha/2; x+1, n-x)
    if events == 0:
        ci_low = 0.0
    else:
        ci_low = beta_dist.ppf(alpha / 2, events, n - events + 1)

    if events == n:
        ci_high = 1.0
    else:
        ci_high = beta_dist.ppf(1 - alpha / 2, events + 1, n - events)

    return _result(
        estimate_pct=p_hat * 100.0,
        ci_low_pct=ci_low * 100.0,
        ci_high_pct=ci_high * 100.0,
        method="Clopper-Pearson Exact",
        n_patients=n,
        n_events=events,
        metadata={
            "alpha": alpha,
            "confidence_level": 1 - alpha,
            "coverage_guarantee": "exact (conservative)",
        },
    )


# ---------------------------------------------------------------------------
# 3. Wilson score interval
# ---------------------------------------------------------------------------

def wilson_score(data: dict[str, Any]) -> dict[str, Any]:
    """Wilson score confidence interval for a binomial proportion.

    Better coverage properties than Wald for small n and proportions near
    0 or 1.  Recommended by Agresti & Coull (1998) for routine use.

    Required data keys:
        events (int): Number of adverse events observed.
        n (int): Total number of patients.

    Optional data keys:
        alpha (float): Significance level.  Default 0.05 (95% CI).
        continuity_correction (bool): Apply continuity correction.  Default False.
    """
    events = data["events"]
    n = data["n"]
    alpha = data.get("alpha", 0.05)
    cc = data.get("continuity_correction", False)

    if n == 0:
        return _result(
            estimate_pct=0.0,
            ci_low_pct=0.0,
            ci_high_pct=100.0,
            method="Wilson Score",
            n_patients=0,
            n_events=0,
            metadata={"alpha": alpha, "note": "n=0, no data"},
        )

    p_hat = events / n
    z = norm.ppf(1 - alpha / 2)
    z2 = z * z

    # Wilson score formula (see Agresti & Coull 1998)
    denominator = 1 + z2 / n
    centre = (p_hat + z2 / (2 * n)) / denominator
    margin = (z / denominator) * math.sqrt(
        p_hat * (1 - p_hat) / n + z2 / (4 * n * n)
    )

    if cc:
        # Continuity-corrected Wilson interval (Newcombe 1998)
        margin_cc = (z / denominator) * math.sqrt(
            p_hat * (1 - p_hat) / n + z2 / (4 * n * n)
        ) + 1 / (2 * n * denominator)
        ci_low = max(0.0, centre - margin_cc)
        ci_high = min(1.0, centre + margin_cc)
    else:
        ci_low = max(0.0, centre - margin)
        ci_high = min(1.0, centre + margin)

    return _result(
        estimate_pct=centre * 100.0,
        ci_low_pct=ci_low * 100.0,
        ci_high_pct=ci_high * 100.0,
        method="Wilson Score",
        n_patients=n,
        n_events=events,
        metadata={
            "alpha": alpha,
            "z_critical": round(z, 4),
            "continuity_correction": cc,
            "point_estimate_pct": round(p_hat * 100.0, 4),
        },
    )


# ---------------------------------------------------------------------------
# 4. Random-effects meta-analysis (DerSimonian-Laird)
# ---------------------------------------------------------------------------

def random_effects_meta(data: dict[str, Any]) -> dict[str, Any]:
    """DerSimonian-Laird random-effects meta-analysis.

    Pools effect estimates from multiple studies while allowing for
    between-study heterogeneity.  Uses the Freeman-Tukey double arcsine
    transformation for proportions to stabilise the variance.

    Required data keys:
        studies (list[dict]): Each study dict must have:
            - events (int)
            - n (int)
            - label (str, optional)
    """
    studies = data["studies"]
    k = len(studies)

    if k == 0:
        raise ValueError("At least one study is required for meta-analysis")

    if k == 1:
        # Fall back to single-study exact estimate
        s = studies[0]
        return frequentist_exact({"events": s["events"], "n": s["n"]})

    # Freeman-Tukey double arcsine transformation for proportions
    # y_i = arcsin(sqrt(x_i / (n_i+1))) + arcsin(sqrt((x_i+1) / (n_i+1)))
    # var_i = 1 / (n_i + 0.5)
    ys = []
    ws = []
    study_labels = []
    total_events = 0
    total_n = 0

    for s in studies:
        ei = s["events"]
        ni = s["n"]
        total_events += ei
        total_n += ni
        study_labels.append(s.get("label", f"Study (n={ni})"))

        yi = math.asin(math.sqrt(ei / (ni + 1))) + math.asin(
            math.sqrt((ei + 1) / (ni + 1))
        )
        vi = 1.0 / (ni + 0.5)
        wi = 1.0 / vi

        ys.append(yi)
        ws.append(wi)

    # Fixed-effects pooled estimate
    w_sum = sum(ws)
    theta_fe = sum(w * y for w, y in zip(ws, ys)) / w_sum

    # Cochran's Q statistic
    q = sum(w * (y - theta_fe) ** 2 for w, y in zip(ws, ys))

    # DerSimonian-Laird tau-squared estimate
    c = w_sum - sum(w * w for w in ws) / w_sum
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0

    # Random-effects weights
    ws_re = [1.0 / (1.0 / w + tau2) for w in ws]
    w_re_sum = sum(ws_re)
    theta_re = sum(w * y for w, y in zip(ws_re, ys)) / w_re_sum

    se_re = math.sqrt(1.0 / w_re_sum)
    z_crit = norm.ppf(0.975)

    theta_low = theta_re - z_crit * se_re
    theta_high = theta_re + z_crit * se_re

    # Back-transform from double arcsine to proportion
    # Inverse: p = (sin(theta/2))^2
    def back_transform(t: float) -> float:
        return max(0.0, min(1.0, (math.sin(t / 2)) ** 2))

    pooled = back_transform(theta_re)
    ci_low = back_transform(theta_low)
    ci_high = back_transform(theta_high)

    # I-squared heterogeneity
    i_squared = max(0.0, (q - (k - 1)) / q) if q > 0 else 0.0

    return _result(
        estimate_pct=pooled * 100.0,
        ci_low_pct=ci_low * 100.0,
        ci_high_pct=ci_high * 100.0,
        method="DerSimonian-Laird Random Effects",
        n_patients=total_n,
        n_events=total_events,
        metadata={
            "n_studies": k,
            "tau_squared": round(tau2, 6),
            "cochran_q": round(q, 4),
            "i_squared": round(i_squared, 4),
            "study_labels": study_labels,
            "study_weights": [round(w / w_re_sum, 4) for w in ws_re],
            "transformation": "Freeman-Tukey double arcsine",
        },
    )


# ---------------------------------------------------------------------------
# 5. Empirical Bayes shrinkage
# ---------------------------------------------------------------------------

def empirical_bayes(data: dict[str, Any]) -> dict[str, Any]:
    """Empirical Bayes shrinkage estimator for multiple AE types.

    Borrows strength across adverse event types by shrinking each
    type's estimate towards the grand mean.  Useful when some AE types
    have very few events and would otherwise have unreliable raw rates.

    The shrinkage factor B_i for each type is:
        B_i = sigma2_within_i / (sigma2_within_i + tau2)

    where tau2 is the between-type variance estimated from the data.

    Required data keys:
        ae_types (list[dict]): Each dict must have:
            - name (str): AE type name
            - events (int)
            - n (int)
        target (str): Name of the AE type to report.

    Optional data keys:
        prior_weight (float): Weight on the grand mean (0=no shrinkage).
            If not provided, computed from data via method-of-moments.
    """
    ae_types = data["ae_types"]
    target_name = data["target"]

    if len(ae_types) == 0:
        raise ValueError("At least one AE type is required")

    # Compute raw rates and within-type variance
    raw_rates = []
    within_vars = []
    for ae in ae_types:
        ei = ae["events"]
        ni = ae["n"]
        pi = ei / ni if ni > 0 else 0.0
        vi = pi * (1 - pi) / ni if ni > 0 else 0.0
        raw_rates.append(pi)
        within_vars.append(vi)

    # Grand mean (unweighted)
    grand_mean = sum(raw_rates) / len(raw_rates) if raw_rates else 0.0

    # Estimate between-type variance (tau2) via method-of-moments
    k = len(ae_types)
    if k > 1:
        mean_within_var = sum(within_vars) / k
        # Variance of the raw rates
        var_of_rates = sum((r - grand_mean) ** 2 for r in raw_rates) / (k - 1)
        tau2 = max(0.0, var_of_rates - mean_within_var)
    else:
        tau2 = 0.0

    # Allow override (reserved for future manual shrinkage control)
    # if "prior_weight" in data:
    #     B = data["prior_weight"]

    # Find target AE type and compute shrunken estimate
    target_idx = None
    for i, ae in enumerate(ae_types):
        if ae["name"] == target_name:
            target_idx = i
            break

    if target_idx is None:
        raise ValueError(
            f"Target AE type '{target_name}' not found in ae_types"
        )

    target_ae = ae_types[target_idx]
    target_raw = raw_rates[target_idx]
    target_var = within_vars[target_idx]
    target_n = target_ae["n"]
    target_events = target_ae["events"]

    # Shrinkage factor: proportion of variance that is within-type
    if "prior_weight" in data:
        b_i = data["prior_weight"]
    elif (target_var + tau2) > 0:
        b_i = target_var / (target_var + tau2)
    else:
        b_i = 0.0  # No shrinkage when variance is zero

    # Shrunk estimate: weighted average of raw rate and grand mean
    shrunk = (1 - b_i) * target_raw + b_i * grand_mean

    # Approximate CI for the shrunk estimate
    # Var(shrunk) ~ (1 - B)^2 * Var(raw) + B^2 * Var(grand mean)
    var_grand_mean = (
        sum((r - grand_mean) ** 2 for r in raw_rates) / (k * (k - 1))
        if k > 1
        else target_var
    )
    shrunk_var = ((1 - b_i) ** 2) * target_var + (b_i ** 2) * var_grand_mean
    shrunk_se = math.sqrt(shrunk_var) if shrunk_var > 0 else 0.0
    z_crit = norm.ppf(0.975)

    ci_low = shrunk - z_crit * shrunk_se
    ci_high = shrunk + z_crit * shrunk_se

    return _result(
        estimate_pct=shrunk * 100.0,
        ci_low_pct=ci_low * 100.0,
        ci_high_pct=ci_high * 100.0,
        method="Empirical Bayes Shrinkage",
        n_patients=target_n,
        n_events=target_events,
        metadata={
            "target_ae": target_name,
            "raw_rate_pct": round(target_raw * 100.0, 4),
            "grand_mean_pct": round(grand_mean * 100.0, 4),
            "shrinkage_factor": round(b_i, 4),
            "tau_squared": round(tau2, 6),
            "n_ae_types": k,
            "all_rates_pct": {
                ae["name"]: round(r * 100.0, 4)
                for ae, r in zip(ae_types, raw_rates)
            },
        },
    )


# ---------------------------------------------------------------------------
# 6. Kaplan-Meier time-to-event
# ---------------------------------------------------------------------------

def kaplan_meier(data: dict[str, Any]) -> dict[str, Any]:
    """Kaplan-Meier non-parametric survival / time-to-event estimate.

    Estimates the cumulative incidence of an adverse event at a given time
    horizon when individual onset timing data is available.  Uses the
    standard product-limit estimator and Greenwood's formula for the
    variance.

    Required data keys:
        times (list[float]): Event or censoring times for each patient.
        event_indicators (list[bool]): True if the patient had the event,
            False if censored.  Uses a distinct key name to avoid collision
            with the integer ``events`` key used by other models.

    Optional data keys:
        time_horizon (float): Time at which to report cumulative incidence.
            Default: max(times).
        alpha (float): Significance level.  Default 0.05.
    """
    times = data["times"]
    observed = data["event_indicators"]
    alpha = data.get("alpha", 0.05)

    n_total = len(times)
    if n_total == 0:
        raise ValueError("At least one observation is required")

    if len(observed) != n_total:
        raise ValueError("times and events must have the same length")

    time_horizon = data.get("time_horizon", max(times))

    # Build the ordered event table
    # Combine and sort by time
    records = sorted(zip(times, observed), key=lambda x: x[0])

    # Distinct event times
    distinct_times: list[float] = sorted(set(t for t, e in records if e))

    n_events_total = sum(1 for _, e in records if e)
    at_risk = n_total
    survival = 1.0
    greenwood_sum = 0.0
    cum_incidence_at_horizon = 0.0
    variance_at_horizon = 0.0
    last_survival = 1.0

    event_table = []

    for t in distinct_times:
        # Remove censored before or at this time
        censored_before = sum(
            1 for ti, ei in records if not ei and ti < t
        )
        # Simple approach: count at risk and events at each distinct time
        # At risk: those with time >= t
        at_risk = sum(1 for ti, _ in records if ti >= t)
        events_at_t = sum(1 for ti, ei in records if ti == t and ei)

        if at_risk > 0 and events_at_t > 0:
            survival *= (1 - events_at_t / at_risk)
            if at_risk > events_at_t:
                greenwood_sum += events_at_t / (
                    at_risk * (at_risk - events_at_t)
                )

        event_table.append({
            "time": t,
            "at_risk": at_risk,
            "events": events_at_t,
            "survival": round(survival, 6),
        })

        if t <= time_horizon:
            cum_incidence_at_horizon = 1 - survival
            variance_at_horizon = (survival ** 2) * greenwood_sum

    # If no events before horizon, cumulative incidence is 0
    if not distinct_times or distinct_times[0] > time_horizon:
        cum_incidence_at_horizon = 0.0
        variance_at_horizon = 0.0

    se = math.sqrt(variance_at_horizon) if variance_at_horizon > 0 else 0.0
    z_crit = norm.ppf(1 - alpha / 2)

    # CI on cumulative incidence
    ci_low = cum_incidence_at_horizon - z_crit * se
    ci_high = cum_incidence_at_horizon + z_crit * se

    return _result(
        estimate_pct=cum_incidence_at_horizon * 100.0,
        ci_low_pct=ci_low * 100.0,
        ci_high_pct=ci_high * 100.0,
        method="Kaplan-Meier",
        n_patients=n_total,
        n_events=n_events_total,
        metadata={
            "time_horizon": time_horizon,
            "median_survival": _km_median(event_table),
            "n_censored": n_total - n_events_total,
            "event_table": event_table[:20],  # Cap for readability
            "greenwood_se": round(se, 6),
        },
    )


def _km_median(event_table: list[dict]) -> float | None:
    """Extract median survival time from KM event table."""
    for row in event_table:
        if row["survival"] <= 0.5:
            return row["time"]
    return None


# ---------------------------------------------------------------------------
# 7. Predictive posterior
# ---------------------------------------------------------------------------

def predictive_posterior(data: dict[str, Any]) -> dict[str, Any]:
    """Bayesian predictive posterior for rate in the NEXT study.

    Instead of estimating the current population rate, this predicts what
    rate we would observe in a *new* study of a given size.  This accounts
    for both parameter uncertainty and sampling variability, giving wider
    (and more honest) intervals than a simple posterior CI.

    The predictive distribution for y_new events in n_new patients is
    Beta-Binomial(n_new, alpha_post, beta_post).  We compute the
    predictive mean and an equal-tailed 95% prediction interval by
    enumerating or approximating the Beta-Binomial PMF.

    Required data keys:
        events (int): Events observed so far.
        n (int): Patients observed so far.
        n_new (int): Size of the next study to predict.

    Optional data keys:
        prior_alpha (float): Beta prior alpha.  Default 0.5.
        prior_beta (float): Beta prior beta.  Default 0.5.
        alpha (float): Significance level.  Default 0.05.
    """
    events = data["events"]
    n = data["n"]
    n_new = data["n_new"]
    alpha_prior = data.get("prior_alpha", 0.5)
    beta_prior = data.get("prior_beta", 0.5)
    alpha_level = data.get("alpha", 0.05)

    # Posterior parameters
    a_post = alpha_prior + events
    b_post = beta_prior + (n - events)

    # Predictive mean: E[y/n_new] = a_post / (a_post + b_post)
    pred_mean = a_post / (a_post + b_post)

    # Compute the Beta-Binomial PMF for y = 0, 1, ..., n_new
    # P(Y=y) = C(n_new,y) * B(a_post+y, b_post+n_new-y) / B(a_post, b_post)
    # Use log-space to avoid overflow
    from scipy.special import betaln, gammaln

    log_pmf = []
    for y in range(n_new + 1):
        log_p = (
            gammaln(n_new + 1)
            - gammaln(y + 1)
            - gammaln(n_new - y + 1)
            + betaln(a_post + y, b_post + n_new - y)
            - betaln(a_post, b_post)
        )
        log_pmf.append(log_p)

    # Convert to probabilities
    max_log = max(log_pmf)
    pmf = [math.exp(lp - max_log) for lp in log_pmf]
    total = sum(pmf)
    pmf = [p / total for p in pmf]

    # CDF for prediction interval
    cdf = []
    cumul = 0.0
    for p in pmf:
        cumul += p
        cdf.append(cumul)

    # Equal-tailed prediction interval
    pred_low_y = 0
    pred_high_y = n_new
    for y, c in enumerate(cdf):
        if c >= alpha_level / 2:
            pred_low_y = y
            break
    for y in range(n_new, -1, -1):
        if cdf[y] <= 1 - alpha_level / 2:
            pred_high_y = y + 1 if y < n_new else n_new
            break

    # Predictive variance
    pred_var = (
        n_new * a_post * b_post * (a_post + b_post + n_new)
        / ((a_post + b_post) ** 2 * (a_post + b_post + 1))
    )

    return _result(
        estimate_pct=pred_mean * 100.0,
        ci_low_pct=(pred_low_y / n_new) * 100.0,
        ci_high_pct=(pred_high_y / n_new) * 100.0,
        method="Bayesian Predictive Posterior",
        n_patients=n,
        n_events=events,
        metadata={
            "n_new": n_new,
            "posterior_alpha": round(a_post, 4),
            "posterior_beta": round(b_post, 4),
            "predictive_mean_events": round(pred_mean * n_new, 2),
            "predictive_sd_events": round(math.sqrt(pred_var), 2),
            "prediction_interval_events": (pred_low_y, pred_high_y),
            "interval_type": "equal-tailed prediction interval",
            "note": "Predicts rate in next study, not current population",
        },
    )


# ---------------------------------------------------------------------------
# Model registry data structure
# ---------------------------------------------------------------------------

@dataclass
class RiskModel:
    """Metadata and compute function for a registered risk model.

    Attributes:
        id: Unique string identifier.
        name: Human-readable model name.
        description: One-line description of what the model does.
        suitable_for: Contexts where this model is appropriate.
        requires: Data keys the compute function needs.
        compute_fn: Callable that takes a data dict and returns a result dict.
    """

    id: str
    name: str
    description: str
    suitable_for: list[str]
    requires: list[str]
    compute_fn: Callable[[dict[str, Any]], dict[str, Any]]


MODEL_REGISTRY: dict[str, RiskModel] = {
    "bayesian_beta_binomial": RiskModel(
        id="bayesian_beta_binomial",
        name="Bayesian Beta-Binomial",
        description=(
            "Conjugate Beta-Binomial model with informative priors for "
            "sequential updating as trial data accrues"
        ),
        suitable_for=["small_sample", "sequential_updating", "informative_prior"],
        requires=["events", "n"],
        compute_fn=bayesian_beta_binomial,
    ),
    "frequentist_exact": RiskModel(
        id="frequentist_exact",
        name="Clopper-Pearson Exact",
        description=(
            "Exact binomial CI with guaranteed coverage; conservative but "
            "widely accepted for regulatory submissions"
        ),
        suitable_for=["small_sample", "regulatory", "exact_coverage"],
        requires=["events", "n"],
        compute_fn=frequentist_exact,
    ),
    "wilson_score": RiskModel(
        id="wilson_score",
        name="Wilson Score Interval",
        description=(
            "Wilson score CI with better coverage than Wald; recommended "
            "for small n and proportions near 0 or 1"
        ),
        suitable_for=["small_sample", "routine_estimation", "near_boundary"],
        requires=["events", "n"],
        compute_fn=wilson_score,
    ),
    "random_effects_meta": RiskModel(
        id="random_effects_meta",
        name="DerSimonian-Laird Random Effects",
        description=(
            "Random-effects meta-analysis pooling across studies with "
            "between-study heterogeneity via DerSimonian-Laird"
        ),
        suitable_for=["meta_analysis", "multi_study", "heterogeneity"],
        requires=["studies"],
        compute_fn=random_effects_meta,
    ),
    "empirical_bayes": RiskModel(
        id="empirical_bayes",
        name="Empirical Bayes Shrinkage",
        description=(
            "Shrinkage estimator that borrows strength across AE types; "
            "stabilises estimates when some types have few events"
        ),
        suitable_for=["multiple_ae_types", "small_sample", "borrowing_strength"],
        requires=["ae_types", "target"],
        compute_fn=empirical_bayes,
    ),
    "kaplan_meier": RiskModel(
        id="kaplan_meier",
        name="Kaplan-Meier Cumulative Incidence",
        description=(
            "Non-parametric time-to-event estimator using the product-limit "
            "formula with Greenwood variance"
        ),
        suitable_for=["time_to_event", "censored_data", "onset_timing"],
        requires=["times", "event_indicators"],
        compute_fn=kaplan_meier,
    ),
    "predictive_posterior": RiskModel(
        id="predictive_posterior",
        name="Bayesian Predictive Posterior",
        description=(
            "Predicts the AE rate in the NEXT study, accounting for both "
            "parameter uncertainty and sampling variability"
        ),
        suitable_for=["prediction", "trial_planning", "sequential_updating"],
        requires=["events", "n", "n_new"],
        compute_fn=predictive_posterior,
    ),
}


# ---------------------------------------------------------------------------
# Unified interface functions
# ---------------------------------------------------------------------------

def estimate_risk(model_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Run a single model from the registry.

    Args:
        model_id: Key in MODEL_REGISTRY.
        data: Data dict with keys required by the chosen model.

    Returns:
        Standardised result dict.

    Raises:
        KeyError: If model_id is not in the registry.
        ValueError: If required data keys are missing.
    """
    if model_id not in MODEL_REGISTRY:
        raise KeyError(
            f"Unknown model '{model_id}'. "
            f"Available: {list(MODEL_REGISTRY.keys())}"
        )

    model = MODEL_REGISTRY[model_id]

    # Validate required keys
    missing = [k for k in model.requires if k not in data]
    if missing:
        raise ValueError(
            f"Model '{model_id}' requires keys {model.requires}, "
            f"but {missing} are missing from data"
        )

    return model.compute_fn(data)


def compare_models(
    data: dict[str, Any],
    model_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run multiple models on the same data and return a comparison table.

    Only models whose required keys are present in ``data`` will be run.
    Models that fail are reported with error messages rather than raising.

    Args:
        data: Data dict.  Models whose required keys are present will be run.
        model_ids: Specific models to compare.  If None, all compatible
            models are attempted.

    Returns:
        Dict with keys:
            - results: dict[model_id, result_dict]
            - errors: dict[model_id, error_message]
            - summary: list of dicts for tabular display
    """
    if model_ids is None:
        model_ids = list(MODEL_REGISTRY.keys())

    results: dict[str, dict[str, Any]] = {}
    errors: dict[str, str] = {}
    summary: list[dict[str, Any]] = []

    for mid in model_ids:
        if mid not in MODEL_REGISTRY:
            errors[mid] = f"Unknown model '{mid}'"
            continue

        model = MODEL_REGISTRY[mid]
        missing = [k for k in model.requires if k not in data]
        if missing:
            errors[mid] = f"Missing required keys: {missing}"
            continue

        try:
            result = model.compute_fn(data)
            results[mid] = result
            summary.append({
                "model": mid,
                "name": model.name,
                "estimate_pct": result["estimate_pct"],
                "ci_low_pct": result["ci_low_pct"],
                "ci_high_pct": result["ci_high_pct"],
                "ci_width_pct": result["ci_width_pct"],
            })
        except Exception as exc:
            errors[mid] = str(exc)
            logger.warning("Model '%s' failed: %s", mid, exc)

    return {
        "results": results,
        "errors": errors,
        "summary": summary,
    }


def list_models() -> list[dict[str, Any]]:
    """Return a list of all registered models with metadata."""
    return [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "suitable_for": m.suitable_for,
            "requires": m.requires,
        }
        for m in MODEL_REGISTRY.values()
    ]
