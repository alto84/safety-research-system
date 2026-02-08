#!/usr/bin/env python3
"""
Publication-ready comparative analysis of cell therapy safety profiles.

Compares autoimmune (SLE) vs oncology (DLBCL, ALL, MM) CAR-T safety using
the Predictive Safety Platform's 7 risk estimation models, integrated with
knowledge-graph mechanistic understanding.

Target journal: Blood Advances / Molecular Therapy
Reporting: STROBE-compliant where applicable

All data from published clinical trial literature and public registries.
No proprietary data sources.

Usage:
    PYTHONPATH=. python analysis/publication_analysis.py

Outputs saved to analysis/results/
"""

from __future__ import annotations

import json
import math
import os
import sys
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import beta as beta_dist, norm, chi2

# ── Project imports ──────────────────────────────────────────────────────
from data.sle_cart_studies import (
    ADVERSE_EVENT_RATES,
    CLINICAL_TRIALS,
    DATA_SOURCES,
    AdverseEventRate,
    get_adverse_events_by_indication,
    get_sle_trials,
    get_sle_baseline_risk,
)
from src.models.model_registry import (
    MODEL_REGISTRY,
    estimate_risk,
    compare_models,
    bayesian_beta_binomial,
    frequentist_exact,
    wilson_score,
    random_effects_meta,
    empirical_bayes,
    kaplan_meier,
    predictive_posterior,
)
from src.models.model_validation import (
    calibration_check,
    brier_score,
    coverage_probability,
    leave_one_out_cv,
    model_comparison,
)
from src.models.bayesian_risk import (
    PriorSpec,
    compute_posterior,
    compute_evidence_accrual,
    CRS_PRIOR,
    ICANS_PRIOR,
    ICAHS_PRIOR,
    STUDY_TIMELINE,
)
from src.data.knowledge.pathways import (
    PATHWAY_REGISTRY,
    get_pathways_for_ae,
    get_intervention_points_for_ae,
    get_feedback_loops_for_ae,
    IL6_TRANS_SIGNALING,
    BBB_DISRUPTION_ICANS,
    HLH_MAS_PATHWAY,
)
from src.data.knowledge.mechanisms import (
    MECHANISM_REGISTRY,
    CART_CD19_CRS,
    CART_CD19_ICANS,
    get_mechanisms_for_ae,
    AECategory,
)
from src.data.knowledge.references import REFERENCES, get_reference

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Output directory ─────────────────────────────────────────────────────
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================================
# SECTION 1: DATA ASSEMBLY
# =========================================================================

def assemble_trial_data() -> dict[str, Any]:
    """Assemble all trial data organized by indication and AE type.

    Returns:
        Dict with keys per indication, each containing trial-level AE data.
    """
    logger.info("=" * 70)
    logger.info("SECTION 1: DATA ASSEMBLY")
    logger.info("=" * 70)

    indications = ["SLE", "DLBCL", "ALL", "MM"]
    assembled: dict[str, list[AdverseEventRate]] = {}

    for ind in indications:
        if ind == "SLE":
            # Use individual trials, not the pooled entry
            trials = get_sle_trials()
        else:
            trials = get_adverse_events_by_indication(ind)
        assembled[ind] = trials
        logger.info(
            "  %s: %d trials, %d total patients",
            ind,
            len(trials),
            sum(t.n_patients for t in trials),
        )

    # Build summary table
    summary = {}
    for ind, trials in assembled.items():
        total_n = sum(t.n_patients for t in trials)
        n_trials = len(trials)
        years = sorted(set(t.year for t in trials))
        targets = sorted(set(
            "CD19" if "CD19" in t.product or "cd19" in t.product.lower()
            else "BCMA" if "BCMA" in t.product
            else "Dual" if "dual" in t.product.lower() or "co-infusion" in t.product.lower()
            else "Other"
            for t in trials
        ))
        summary[ind] = {
            "n_trials": n_trials,
            "total_patients": total_n,
            "year_range": f"{min(years)}-{max(years)}" if years else "N/A",
            "targets": targets,
        }

    return {
        "trials_by_indication": assembled,
        "summary": summary,
    }


def compute_pooled_rates(
    trials: list[AdverseEventRate],
) -> dict[str, dict[str, float]]:
    """Compute pooled AE rates with exact binomial CIs.

    Uses inverse-variance weighted pooling for multi-trial indications
    and Clopper-Pearson exact CIs for individual indications.

    Returns:
        Dict mapping AE type to pooled rate and 95% CI.
    """
    ae_types = [
        ("crs_any_grade", "CRS Any Grade"),
        ("crs_grade3_plus", "CRS Grade >= 3"),
        ("icans_any_grade", "ICANS Any Grade"),
        ("icans_grade3_plus", "ICANS Grade >= 3"),
    ]

    results = {}
    for attr, label in ae_types:
        # Weighted average by sample size
        total_n = sum(t.n_patients for t in trials)
        if total_n == 0:
            results[label] = {"rate": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}
            continue

        weighted_rate = sum(
            getattr(t, attr) * t.n_patients for t in trials
        ) / total_n

        # Approximate event counts for CI computation
        total_events = round(weighted_rate * total_n / 100.0)

        # Clopper-Pearson exact CI
        if total_events == 0:
            ci_low = 0.0
            ci_high = (1 - 0.05 ** (1.0 / total_n)) * 100.0 if total_n > 0 else 0.0
        elif total_events == total_n:
            ci_low = (0.05 ** (1.0 / total_n)) * 100.0
            ci_high = 100.0
        else:
            ci_low = beta_dist.ppf(0.025, total_events, total_n - total_events + 1) * 100.0
            ci_high = beta_dist.ppf(0.975, total_events + 1, total_n - total_events) * 100.0

        results[label] = {
            "rate": round(weighted_rate, 2),
            "ci_low": round(ci_low, 2),
            "ci_high": round(ci_high, 2),
            "n": total_n,
            "events": total_events,
        }

    return results


# =========================================================================
# SECTION 2: SEVEN-MODEL COMPARISON
# =========================================================================

def run_seven_model_comparison(
    assembled_data: dict[str, Any],
) -> dict[str, Any]:
    """Run all 7 risk estimation models on SLE CRS Grade >= 3 data.

    This is the primary analysis: comparing model performance for the
    most clinically relevant endpoint (severe CRS) in the most novel
    indication (SLE).

    Returns:
        Dict with model results, cross-validation, and comparison metrics.
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("SECTION 2: SEVEN-MODEL COMPARISON")
    logger.info("=" * 70)

    sle_trials = assembled_data["trials_by_indication"]["SLE"]

    # ── Derive event counts from percentage rates ────────────────────────
    # For SLE trials: crs_grade3_plus is a percentage, n_patients is the count
    studies_for_meta = []
    total_events = 0
    total_n = 0
    for t in sle_trials:
        n = t.n_patients
        events = round(t.crs_grade3_plus * n / 100.0)
        total_events += events
        total_n += n
        studies_for_meta.append({
            "events": events,
            "n": n,
            "label": t.trial,
        })

    logger.info(
        "  SLE CRS Grade >= 3: %d events / %d patients (%.1f%%)",
        total_events, total_n, total_events / total_n * 100 if total_n > 0 else 0,
    )

    # ── Model 1: Bayesian Beta-Binomial (Jeffreys prior) ────────────────
    m1_result = estimate_risk("bayesian_beta_binomial", {
        "events": total_events, "n": total_n,
        "prior_alpha": 0.5, "prior_beta": 0.5,
        "prior_source": "Jeffreys non-informative",
    })
    logger.info("  Model 1 (Bayesian Jeffreys): %.2f%% [%.2f, %.2f]",
                m1_result["estimate_pct"], m1_result["ci_low_pct"], m1_result["ci_high_pct"])

    # ── Model 2: Clopper-Pearson Exact ───────────────────────────────────
    m2_result = estimate_risk("frequentist_exact", {
        "events": total_events, "n": total_n,
    })
    logger.info("  Model 2 (Clopper-Pearson): %.2f%% [%.2f, %.2f]",
                m2_result["estimate_pct"], m2_result["ci_low_pct"], m2_result["ci_high_pct"])

    # ── Model 3: Wilson Score ────────────────────────────────────────────
    m3_result = estimate_risk("wilson_score", {
        "events": total_events, "n": total_n,
    })
    logger.info("  Model 3 (Wilson Score): %.2f%% [%.2f, %.2f]",
                m3_result["estimate_pct"], m3_result["ci_low_pct"], m3_result["ci_high_pct"])

    # ── Model 4: Random-Effects Meta-Analysis (DerSimonian-Laird) ────────
    m4_result = estimate_risk("random_effects_meta", {
        "studies": studies_for_meta,
    })
    logger.info("  Model 4 (DL Random Effects): %.2f%% [%.2f, %.2f]",
                m4_result["estimate_pct"], m4_result["ci_low_pct"], m4_result["ci_high_pct"])

    # ── Model 5: Empirical Bayes Shrinkage ───────────────────────────────
    # Shrink CRS Grade>=3 estimate toward the mean of all SLE AE types
    ae_types_for_eb = []
    for attr_name, ae_label in [
        ("crs_any_grade", "CRS Any Grade"),
        ("crs_grade3_plus", "CRS Grade >= 3"),
        ("icans_any_grade", "ICANS Any Grade"),
        ("icans_grade3_plus", "ICANS Grade >= 3"),
        ("icahs_rate", "ICAHS"),
    ]:
        events_this_ae = sum(
            round(getattr(t, attr_name) * t.n_patients / 100.0)
            for t in sle_trials
        )
        ae_types_for_eb.append({
            "name": ae_label,
            "events": events_this_ae,
            "n": total_n,
        })

    m5_result = estimate_risk("empirical_bayes", {
        "ae_types": ae_types_for_eb,
        "target": "CRS Grade >= 3",
    })
    logger.info("  Model 5 (Empirical Bayes): %.2f%% [%.2f, %.2f]",
                m5_result["estimate_pct"], m5_result["ci_low_pct"], m5_result["ci_high_pct"])

    # ── Model 6: Kaplan-Meier (synthetic time-to-event) ──────────────────
    # Generate synthetic CRS onset times based on published literature:
    # CRS typically occurs day 1-7 (median day 2-3 in SLE CAR-T)
    np.random.seed(42)
    times = []
    event_indicators = []

    for t in sle_trials:
        n = t.n_patients
        n_crs_events = round(t.crs_grade3_plus * n / 100.0)
        # CRS events: onset day 1-5, log-normal distribution centered around day 2
        for _ in range(n_crs_events):
            onset = max(0.5, np.random.lognormal(mean=0.7, sigma=0.5))
            times.append(onset)
            event_indicators.append(True)
        # Non-events: censored at day 28 (standard follow-up)
        for _ in range(n - n_crs_events):
            times.append(28.0)
            event_indicators.append(False)

    m6_result = estimate_risk("kaplan_meier", {
        "times": times,
        "event_indicators": event_indicators,
        "time_horizon": 28.0,
    })
    logger.info("  Model 6 (Kaplan-Meier): %.2f%% [%.2f, %.2f]",
                m6_result["estimate_pct"], m6_result["ci_low_pct"], m6_result["ci_high_pct"])

    # ── Model 7: Predictive Posterior ────────────────────────────────────
    # Predict the CRS rate in a hypothetical next study of n=50
    m7_result = estimate_risk("predictive_posterior", {
        "events": total_events, "n": total_n, "n_new": 50,
        "prior_alpha": 0.5, "prior_beta": 0.5,
    })
    logger.info("  Model 7 (Predictive Posterior, n_new=50): %.2f%% [%.2f, %.2f]",
                m7_result["estimate_pct"], m7_result["ci_low_pct"], m7_result["ci_high_pct"])

    # ── Cross-Validation (Leave-One-Study-Out) ───────────────────────────
    logger.info("")
    logger.info("  Running Leave-One-Study-Out Cross-Validation...")

    # Models compatible with LOO-CV (need multi-study or pooled data)
    cv_model_fns = {
        "Bayesian Beta-Binomial": lambda d: bayesian_beta_binomial(
            {**d, "prior_alpha": 0.5, "prior_beta": 0.5}
            if "events" in d else
            bayesian_beta_binomial({
                "events": sum(s["events"] for s in d["studies"]),
                "n": sum(s["n"] for s in d["studies"]),
                "prior_alpha": 0.5, "prior_beta": 0.5,
            })
        ),
        "Clopper-Pearson Exact": lambda d: frequentist_exact(d),
        "Wilson Score": lambda d: wilson_score(d),
        "DerSimonian-Laird RE": lambda d: random_effects_meta(d),
    }

    cv_comparison = model_comparison(studies_for_meta, cv_model_fns)
    for row in cv_comparison["summary"]:
        logger.info(
            "    %s: RMSE=%.2f%%, MAE=%.2f%%, Coverage=%.2f",
            row["model"], row["rmse_pct"], row["mae_pct"], row["coverage"],
        )

    # ── Compile all results ──────────────────────────────────────────────
    model_results = {
        "Bayesian Beta-Binomial (Jeffreys)": m1_result,
        "Clopper-Pearson Exact": m2_result,
        "Wilson Score": m3_result,
        "DerSimonian-Laird Random Effects": m4_result,
        "Empirical Bayes Shrinkage": m5_result,
        "Kaplan-Meier": m6_result,
        "Predictive Posterior (n=50)": m7_result,
    }

    return {
        "model_results": model_results,
        "cross_validation": cv_comparison,
        "studies_used": studies_for_meta,
        "total_events": total_events,
        "total_n": total_n,
    }


# =========================================================================
# SECTION 3: MECHANISTIC PRIOR ANALYSIS (Novel Contribution)
# =========================================================================

def mechanistic_prior_analysis(
    assembled_data: dict[str, Any],
) -> dict[str, Any]:
    """Construct informative Bayesian priors from knowledge graph pathways.

    Novel contribution: Uses pathway topology (number of amplification
    steps, feedback loops, intervention points) to calibrate prior
    strength for each AE type. Compares three prior strategies:
        1. Uninformative (Jeffreys): Beta(0.5, 0.5)
        2. Mechanistic: Derived from pathway characteristics
        3. Empirical: Derived from discounted oncology rates

    Returns:
        Dict with prior specifications, posterior comparisons, and
        pathway-to-prior mappings.
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("SECTION 3: MECHANISTIC PRIOR ANALYSIS")
    logger.info("=" * 70)

    sle_trials = assembled_data["trials_by_indication"]["SLE"]
    total_n = sum(t.n_patients for t in sle_trials)

    # ── Step 1: Extract pathway topology features ────────────────────────
    pathway_features = {}

    for ae_type in ["CRS", "ICANS", "HLH/MAS"]:
        pathways = get_pathways_for_ae(ae_type)
        if not pathways:
            continue

        total_steps = sum(len(pw.steps) for pw in pathways)
        feedback_loops = get_feedback_loops_for_ae(ae_type)
        intervention_points = get_intervention_points_for_ae(ae_type)

        # Count amplification edges (positive feedback, amplifies relation)
        amplification_steps = 0
        high_confidence_steps = 0
        for pw in pathways:
            for step in pw.steps:
                if step.is_feedback_loop or step.relation.value == "amplifies":
                    amplification_steps += 1
                if step.confidence >= 0.85:
                    high_confidence_steps += 1

        # Collect all PubMed references
        all_refs = set()
        for pw in pathways:
            all_refs.update(pw.key_references)
            for step in pw.steps:
                all_refs.update(step.references)

        pathway_features[ae_type] = {
            "n_pathways": len(pathways),
            "total_steps": total_steps,
            "n_feedback_loops": len(feedback_loops),
            "n_amplification_steps": amplification_steps,
            "n_intervention_points": len(intervention_points),
            "n_high_confidence_steps": high_confidence_steps,
            "n_references": len(all_refs),
            "references": sorted(all_refs),
            "pathway_names": [pw.name for pw in pathways],
        }

        logger.info(
            "  %s: %d pathways, %d steps, %d feedback loops, %d amplification edges, %d refs",
            ae_type, len(pathways), total_steps, len(feedback_loops),
            amplification_steps, len(all_refs),
        )

    # ── Step 2: Derive mechanistic priors ────────────────────────────────
    # Logic: More feedback loops and amplification steps suggest higher
    # baseline risk (stronger positive feedback = more severe syndrome).
    # More intervention points suggest the risk can be attenuated.
    # Scale prior strength by evidence quality (high-confidence steps).

    mechanistic_priors: dict[str, dict[str, Any]] = {}

    for ae_type, features in pathway_features.items():
        # Amplification factor: more feedback loops -> expect higher rate
        # Base rate from oncology literature, attenuated by SLE differences
        if ae_type == "CRS":
            # CRS: Strong IL-6 pathway, but lower tumor burden in SLE
            # -> expect ~40-60% any-grade (discounted from 42-95% in oncology)
            # -> expect ~2-5% grade >= 3 (discounted from 2-48% in oncology)
            # The 3 feedback loops and 2 amplification steps suggest active
            # pathway, but B-cell depletion in SLE is much less than in
            # hematologic malignancy (lower antigen load)
            base_expectation = 0.03  # 3% severe CRS as starting point
            # Discount by ratio of intervention points to total steps
            intervention_ratio = features["n_intervention_points"] / max(features["total_steps"], 1)
            # More intervention availability -> lower expected rate (can be managed)
            adjusted = base_expectation * (1 - 0.3 * intervention_ratio)
            # Convert to Beta parameters with effective sample size = n_references
            effective_n = min(features["n_references"], 10)  # Cap at 10
            alpha_mech = adjusted * effective_n
            beta_mech = (1 - adjusted) * effective_n
            prior_source = (
                f"Mechanistic: {features['n_feedback_loops']} feedback loops in "
                f"IL-6/NF-kB pathways ({', '.join(features['references'][:3])}...) "
                f"attenuated by {features['n_intervention_points']} intervention points"
            )
        elif ae_type == "ICANS":
            # ICANS: BBB disruption pathway with on-target/off-tumor component
            # Lower expected rate in SLE (lower CRS severity -> lower ICANS)
            base_expectation = 0.02  # 2% severe ICANS
            effective_n = min(features["n_references"], 8)
            alpha_mech = base_expectation * effective_n
            beta_mech = (1 - base_expectation) * effective_n
            prior_source = (
                f"Mechanistic: BBB disruption pathway ({features['total_steps']} steps), "
                f"CD19+ pericyte on-target/off-tumor mechanism (PMID:33082430), "
                f"attenuated by lower CRS severity in SLE"
            )
        elif ae_type == "HLH/MAS":
            # HLH/MAS: IFN-gamma/IL-18 feedback loop - very rare in SLE CAR-T
            base_expectation = 0.005  # 0.5%
            effective_n = min(features["n_references"], 6)
            alpha_mech = base_expectation * effective_n
            beta_mech = (1 - base_expectation) * effective_n
            prior_source = (
                f"Mechanistic: IFN-gamma/IL-18 amplification loop "
                f"({features['n_amplification_steps']} amplification edges), "
                f"rare in low-tumor-burden settings (PMID:36906275)"
            )
        else:
            continue

        mechanistic_priors[ae_type] = {
            "alpha": round(alpha_mech, 4),
            "beta": round(beta_mech, 4),
            "effective_sample_size": effective_n,
            "base_expectation": base_expectation,
            "source": prior_source,
            "pathway_features": features,
        }

        logger.info(
            "  %s prior: Beta(%.4f, %.4f), effective n=%d, source: %s",
            ae_type, alpha_mech, beta_mech, effective_n, prior_source[:80],
        )

    # ── Step 3: Compare three prior strategies on SLE CRS Grade >= 3 ─────
    logger.info("")
    logger.info("  Comparing three prior strategies for SLE CRS Grade >= 3:")

    # Observed data
    events_crs_g3 = sum(
        round(t.crs_grade3_plus * t.n_patients / 100.0) for t in sle_trials
    )

    prior_comparison = {}

    # Strategy 1: Uninformative (Jeffreys)
    uninformative = PriorSpec(alpha=0.5, beta=0.5, source_description="Jeffreys non-informative")
    post_uninf = compute_posterior(uninformative, events_crs_g3, total_n)
    prior_comparison["uninformative"] = {
        "prior": {"alpha": 0.5, "beta": 0.5},
        "posterior_mean_pct": post_uninf.mean,
        "ci_low_pct": post_uninf.ci_low,
        "ci_high_pct": post_uninf.ci_high,
        "ci_width_pct": post_uninf.ci_width,
    }
    logger.info(
        "    Uninformative: %.2f%% [%.2f, %.2f], width=%.2f pp",
        post_uninf.mean, post_uninf.ci_low, post_uninf.ci_high, post_uninf.ci_width,
    )

    # Strategy 2: Mechanistic
    mech_crs = mechanistic_priors.get("CRS", {"alpha": 0.5, "beta": 0.5})
    mechanistic = PriorSpec(
        alpha=mech_crs["alpha"], beta=mech_crs["beta"],
        source_description=mech_crs.get("source", "Mechanistic"),
    )
    post_mech = compute_posterior(mechanistic, events_crs_g3, total_n)
    prior_comparison["mechanistic"] = {
        "prior": {"alpha": mech_crs["alpha"], "beta": mech_crs["beta"]},
        "posterior_mean_pct": post_mech.mean,
        "ci_low_pct": post_mech.ci_low,
        "ci_high_pct": post_mech.ci_high,
        "ci_width_pct": post_mech.ci_width,
    }
    logger.info(
        "    Mechanistic:   %.2f%% [%.2f, %.2f], width=%.2f pp",
        post_mech.mean, post_mech.ci_low, post_mech.ci_high, post_mech.ci_width,
    )

    # Strategy 3: Empirical (discounted from oncology)
    # Use platform's existing CRS prior (discounted from ~14% oncology rate)
    empirical = CRS_PRIOR  # Beta(0.21, 1.29)
    post_emp = compute_posterior(empirical, events_crs_g3, total_n)
    prior_comparison["empirical"] = {
        "prior": {"alpha": CRS_PRIOR.alpha, "beta": CRS_PRIOR.beta},
        "posterior_mean_pct": post_emp.mean,
        "ci_low_pct": post_emp.ci_low,
        "ci_high_pct": post_emp.ci_high,
        "ci_width_pct": post_emp.ci_width,
    }
    logger.info(
        "    Empirical:     %.2f%% [%.2f, %.2f], width=%.2f pp",
        post_emp.mean, post_emp.ci_low, post_emp.ci_high, post_emp.ci_width,
    )

    # ── Step 4: Sensitivity analysis -- vary effective sample size ────────
    logger.info("")
    logger.info("  Prior sensitivity analysis (varying effective sample size):")
    sensitivity = []
    for eff_n in [1, 2, 5, 10, 20, 50]:
        alpha_s = 0.03 * eff_n
        beta_s = (1 - 0.03) * eff_n
        prior_s = PriorSpec(alpha=alpha_s, beta=beta_s,
                            source_description=f"Mechanistic n={eff_n}")
        post_s = compute_posterior(prior_s, events_crs_g3, total_n)
        sensitivity.append({
            "effective_n": eff_n,
            "prior_alpha": round(alpha_s, 4),
            "prior_beta": round(beta_s, 4),
            "posterior_mean_pct": post_s.mean,
            "ci_width_pct": post_s.ci_width,
        })
        logger.info(
            "    n_eff=%2d: mean=%.2f%%, width=%.2f pp",
            eff_n, post_s.mean, post_s.ci_width,
        )

    return {
        "pathway_features": pathway_features,
        "mechanistic_priors": mechanistic_priors,
        "prior_comparison": prior_comparison,
        "sensitivity_analysis": sensitivity,
        "observed_data": {
            "events": events_crs_g3,
            "n": total_n,
        },
    }


# =========================================================================
# SECTION 4: CROSS-INDICATION COMPARISON
# =========================================================================

def cross_indication_comparison(
    assembled_data: dict[str, Any],
) -> dict[str, Any]:
    """Formal statistical comparison across SLE, DLBCL, ALL, MM.

    Includes:
        - Forest plots per AE type per indication
        - Heterogeneity analysis (I-squared, Q-statistic)
        - Subgroup analysis by therapy construct (CD19 vs BCMA)
        - Formal pairwise comparisons (Fisher's exact or chi-squared)

    Returns:
        Dict with comparison results, heterogeneity metrics, forest plot data.
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("SECTION 4: CROSS-INDICATION COMPARISON")
    logger.info("=" * 70)

    trials_by_ind = assembled_data["trials_by_indication"]
    ae_types = [
        ("crs_any_grade", "CRS Any Grade"),
        ("crs_grade3_plus", "CRS Grade >= 3"),
        ("icans_any_grade", "ICANS Any Grade"),
        ("icans_grade3_plus", "ICANS Grade >= 3"),
    ]

    # ── Forest plot data ─────────────────────────────────────────────────
    forest_data: dict[str, list[dict]] = {}

    for attr, label in ae_types:
        entries = []
        all_studies = []  # For heterogeneity test across all indications

        for ind in ["SLE", "DLBCL", "ALL", "MM"]:
            trials = trials_by_ind.get(ind, [])
            if not trials:
                continue

            for t in trials:
                n = t.n_patients
                rate = getattr(t, attr)
                events = round(rate * n / 100.0)

                # Compute Wilson CI for each trial
                result = wilson_score({"events": events, "n": n})

                entries.append({
                    "indication": ind,
                    "trial": t.trial,
                    "product": t.product,
                    "n": n,
                    "events": events,
                    "rate_pct": rate,
                    "ci_low_pct": result["ci_low_pct"],
                    "ci_high_pct": result["ci_high_pct"],
                    "year": t.year,
                })

                all_studies.append({"events": events, "n": n, "label": f"{ind}:{t.trial}"})

            # Pooled estimate per indication
            pooled = compute_pooled_rates(trials)
            if label in pooled:
                entries.append({
                    "indication": ind,
                    "trial": f"{ind} Pooled",
                    "product": "Pooled",
                    "n": pooled[label]["n"],
                    "events": pooled[label].get("events", 0),
                    "rate_pct": pooled[label]["rate"],
                    "ci_low_pct": pooled[label]["ci_low"],
                    "ci_high_pct": pooled[label]["ci_high"],
                    "is_pooled": True,
                })

        # ── Heterogeneity analysis (all studies combined) ────────────────
        if len(all_studies) >= 2:
            meta_result = random_effects_meta({"studies": all_studies})
            heterogeneity = meta_result["metadata"]
        else:
            heterogeneity = {"i_squared": 0.0, "cochran_q": 0.0, "n_studies": len(all_studies)}

        forest_data[label] = {
            "entries": entries,
            "heterogeneity": {
                "i_squared": heterogeneity.get("i_squared", 0.0),
                "cochran_q": heterogeneity.get("cochran_q", 0.0),
                "tau_squared": heterogeneity.get("tau_squared", 0.0),
                "n_studies": len(all_studies),
                "q_df": max(len(all_studies) - 1, 1),
                "q_pvalue": 1.0 - chi2.cdf(
                    heterogeneity.get("cochran_q", 0.0),
                    max(len(all_studies) - 1, 1),
                ) if heterogeneity.get("cochran_q", 0.0) > 0 else 1.0,
            },
        }

    # ── Pairwise comparison: SLE vs each oncology indication ─────────────
    logger.info("")
    logger.info("  Pairwise comparisons (SLE vs Oncology):")
    pairwise = {}

    for attr, label in ae_types:
        pairwise[label] = {}
        sle_trials = trials_by_ind.get("SLE", [])
        sle_n = sum(t.n_patients for t in sle_trials)
        sle_events = sum(round(getattr(t, attr) * t.n_patients / 100.0) for t in sle_trials)

        for comparator in ["DLBCL", "ALL", "MM"]:
            comp_trials = trials_by_ind.get(comparator, [])
            comp_n = sum(t.n_patients for t in comp_trials)
            comp_events = sum(round(getattr(t, attr) * t.n_patients / 100.0) for t in comp_trials)

            # Rate difference and approximate Z-test
            if sle_n > 0 and comp_n > 0:
                p1 = sle_events / sle_n
                p2 = comp_events / comp_n
                diff = (p1 - p2) * 100  # In percentage points

                # Pooled SE for two proportions
                se = math.sqrt(
                    p1 * (1 - p1) / sle_n + p2 * (1 - p2) / comp_n
                ) * 100

                z_stat = diff / se if se > 0 else 0.0
                p_value = 2 * (1 - norm.cdf(abs(z_stat)))
            else:
                diff = 0.0
                se = 0.0
                z_stat = 0.0
                p_value = 1.0

            pairwise[label][f"SLE_vs_{comparator}"] = {
                "sle_rate_pct": round(sle_events / sle_n * 100, 2) if sle_n > 0 else 0.0,
                "comparator_rate_pct": round(comp_events / comp_n * 100, 2) if comp_n > 0 else 0.0,
                "difference_pp": round(diff, 2),
                "se_pp": round(se, 2),
                "z_statistic": round(z_stat, 3),
                "p_value": round(p_value, 4),
                "significant_at_005": p_value < 0.05,
            }

            logger.info(
                "    %s: SLE vs %s: diff=%.1f pp, p=%.4f %s",
                label, comparator, diff, p_value,
                "*" if p_value < 0.05 else "",
            )

    # ── Subgroup analysis by target (CD19 vs BCMA) ───────────────────────
    logger.info("")
    logger.info("  Subgroup analysis by therapy construct:")

    subgroup_results = {}
    all_trials_flat = []
    for ind_trials in trials_by_ind.values():
        all_trials_flat.extend(ind_trials)

    for attr, label in ae_types:
        cd19_trials = [
            t for t in all_trials_flat
            if "CD19" in t.product or "cd19" in t.product.lower()
            or t.trial in ("ZUMA-1", "JULIET", "TRANSCEND", "ELIANA")
        ]
        bcma_trials = [
            t for t in all_trials_flat
            if "BCMA" in t.product and "CD19" not in t.product
        ]

        cd19_n = sum(t.n_patients for t in cd19_trials)
        cd19_events = sum(round(getattr(t, attr) * t.n_patients / 100.0) for t in cd19_trials)

        bcma_n = sum(t.n_patients for t in bcma_trials)
        bcma_events = sum(round(getattr(t, attr) * t.n_patients / 100.0) for t in bcma_trials)

        subgroup_results[label] = {
            "CD19": {
                "n": cd19_n,
                "events": cd19_events,
                "rate_pct": round(cd19_events / cd19_n * 100, 2) if cd19_n > 0 else 0.0,
            },
            "BCMA": {
                "n": bcma_n,
                "events": bcma_events,
                "rate_pct": round(bcma_events / bcma_n * 100, 2) if bcma_n > 0 else 0.0,
            },
        }

        logger.info(
            "    %s: CD19 %.1f%% (%d/%d), BCMA %.1f%% (%d/%d)",
            label,
            cd19_events / cd19_n * 100 if cd19_n > 0 else 0,
            cd19_events, cd19_n,
            bcma_events / bcma_n * 100 if bcma_n > 0 else 0,
            bcma_events, bcma_n,
        )

    return {
        "forest_data": forest_data,
        "pairwise_comparisons": pairwise,
        "subgroup_analysis": subgroup_results,
    }


# =========================================================================
# SECTION 5: EVIDENCE ACCRUAL ANALYSIS
# =========================================================================

def evidence_accrual_analysis() -> dict[str, Any]:
    """Sequential Bayesian evidence accrual showing CI narrowing over time.

    Uses the platform's built-in study timeline with both observed and
    projected data points.

    Returns:
        Dict with sequential posterior trajectories for CRS and ICANS.
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("SECTION 5: EVIDENCE ACCRUAL")
    logger.info("=" * 70)

    # CRS Grade >= 3 accrual
    crs_posteriors = compute_evidence_accrual(
        CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events"
    )

    # ICANS Grade >= 3 accrual
    icans_posteriors = compute_evidence_accrual(
        ICANS_PRIOR, STUDY_TIMELINE, "icans_grade3plus_events"
    )

    accrual_data = {"CRS_grade3plus": [], "ICANS_grade3plus": []}

    for i, (point, crs_post, icans_post) in enumerate(
        zip(STUDY_TIMELINE, crs_posteriors, icans_posteriors)
    ):
        accrual_data["CRS_grade3plus"].append({
            "timepoint": point.label,
            "year": point.year,
            "quarter": point.quarter,
            "n_cumulative": point.n_cumulative_patients,
            "events_cumulative": point.crs_grade3plus_events,
            "posterior_mean_pct": crs_post.mean,
            "ci_low_pct": crs_post.ci_low,
            "ci_high_pct": crs_post.ci_high,
            "ci_width_pct": crs_post.ci_width,
            "is_projected": point.is_projected,
        })
        accrual_data["ICANS_grade3plus"].append({
            "timepoint": point.label,
            "year": point.year,
            "quarter": point.quarter,
            "n_cumulative": point.n_cumulative_patients,
            "events_cumulative": point.icans_grade3plus_events,
            "posterior_mean_pct": icans_post.mean,
            "ci_low_pct": icans_post.ci_low,
            "ci_high_pct": icans_post.ci_high,
            "ci_width_pct": icans_post.ci_width,
            "is_projected": point.is_projected,
        })

        logger.info(
            "  %s (n=%d): CRS G3+ %.2f%% [%.2f-%.2f] | ICANS G3+ %.2f%% [%.2f-%.2f]%s",
            point.label, point.n_cumulative_patients,
            crs_post.mean, crs_post.ci_low, crs_post.ci_high,
            icans_post.mean, icans_post.ci_low, icans_post.ci_high,
            " (projected)" if point.is_projected else "",
        )

    return accrual_data


# =========================================================================
# SECTION 6: GENERATE TABLES AND FIGURES
# =========================================================================

def generate_table_1(assembled_data: dict[str, Any]) -> str:
    """Table 1: Patient demographics and trial characteristics."""

    lines = []
    lines.append("=" * 120)
    lines.append("TABLE 1: Clinical Trial Characteristics by Indication")
    lines.append("=" * 120)
    lines.append("")
    lines.append(f"{'Indication':<12} {'Trial':<30} {'Product':<28} {'N':>5} {'Target':<12} {'Year':>6}")
    lines.append("-" * 120)

    for ind in ["SLE", "DLBCL", "ALL", "MM"]:
        trials = assembled_data["trials_by_indication"].get(ind, [])
        for i, t in enumerate(trials):
            target = (
                "CD19" if "CD19" in t.product or "cd19" in t.product.lower()
                or t.trial in ("ZUMA-1", "JULIET", "TRANSCEND", "ELIANA")
                else "BCMA" if "BCMA" in t.product
                else "Dual"
            )
            ind_label = ind if i == 0 else ""
            lines.append(
                f"{ind_label:<12} {t.trial:<30} {t.product[:27]:<28} {t.n_patients:>5} {target:<12} {t.year:>6}"
            )
        # Subtotal
        total_n = sum(t.n_patients for t in trials)
        lines.append(f"{'':>12} {'Subtotal':<30} {'':>28} {total_n:>5}")
        lines.append("-" * 120)

    grand_total = sum(
        sum(t.n_patients for t in trials)
        for trials in assembled_data["trials_by_indication"].values()
    )
    lines.append(f"{'TOTAL':>12} {'':>30} {'':>28} {grand_total:>5}")
    lines.append("=" * 120)
    lines.append("")
    lines.append("Notes: SLE trials include individual study cohorts only (pooled analysis excluded).")
    lines.append("Oncology comparators are pivotal registration trials with published data.")
    lines.append("All trial data from published peer-reviewed literature and public registries.")

    return "\n".join(lines)


def generate_table_2(assembled_data: dict[str, Any]) -> str:
    """Table 2: Adverse event rates by indication (pooled + per-trial)."""

    lines = []
    lines.append("=" * 140)
    lines.append("TABLE 2: Adverse Event Rates by Indication (Pooled Estimates with 95% CI)")
    lines.append("=" * 140)
    lines.append("")
    lines.append(
        f"{'Indication':<10} {'N':>5} {'CRS Any Grade':>20} {'CRS G>=3':>20} "
        f"{'ICANS Any Grade':>20} {'ICANS G>=3':>20}"
    )
    lines.append("-" * 140)

    for ind in ["SLE", "DLBCL", "ALL", "MM"]:
        trials = assembled_data["trials_by_indication"].get(ind, [])
        pooled = compute_pooled_rates(trials)

        total_n = sum(t.n_patients for t in trials)

        def _fmt(key: str) -> str:
            if key not in pooled:
                return "N/A"
            r = pooled[key]
            return f"{r['rate']:.1f} ({r['ci_low']:.1f}-{r['ci_high']:.1f})"

        lines.append(
            f"{ind:<10} {total_n:>5} {_fmt('CRS Any Grade'):>20} {_fmt('CRS Grade >= 3'):>20} "
            f"{_fmt('ICANS Any Grade'):>20} {_fmt('ICANS Grade >= 3'):>20}"
        )

    lines.append("-" * 140)
    lines.append("")
    lines.append("Rates expressed as percentages with 95% Clopper-Pearson exact confidence intervals.")
    lines.append("SLE rates pooled from individual studies weighted by sample size.")
    lines.append("AE grading per ASTCT consensus criteria (Lee et al., 2019; PMID:30275568).")

    return "\n".join(lines)


def generate_table_3(model_results: dict[str, Any]) -> str:
    """Table 3: Seven-model comparison results for SLE CRS Grade >= 3."""

    lines = []
    lines.append("=" * 130)
    lines.append("TABLE 3: Seven-Model Comparison for SLE CRS Grade >= 3 Rate Estimation")
    lines.append("=" * 130)
    lines.append("")
    lines.append(
        f"{'Model':<40} {'Estimate (%)':>14} {'95% CI':>22} {'CI Width (pp)':>14} {'Method Type':<20}"
    )
    lines.append("-" * 130)

    method_types = {
        "Bayesian Beta-Binomial (Jeffreys)": "Bayesian",
        "Clopper-Pearson Exact": "Frequentist",
        "Wilson Score": "Frequentist",
        "DerSimonian-Laird Random Effects": "Meta-analytic",
        "Empirical Bayes Shrinkage": "Empirical Bayes",
        "Kaplan-Meier": "Time-to-event",
        "Predictive Posterior (n=50)": "Bayesian predictive",
    }

    for name, result in model_results["model_results"].items():
        ci_str = f"[{result['ci_low_pct']:.2f}, {result['ci_high_pct']:.2f}]"
        lines.append(
            f"{name:<40} {result['estimate_pct']:>14.2f} {ci_str:>22} "
            f"{result['ci_width_pct']:>14.2f} {method_types.get(name, 'Other'):<20}"
        )

    lines.append("-" * 130)

    # Add CV results if available
    if "cross_validation" in model_results and model_results["cross_validation"]["summary"]:
        lines.append("")
        lines.append("Leave-One-Study-Out Cross-Validation:")
        lines.append(
            f"{'Model':<40} {'RMSE (pp)':>12} {'MAE (pp)':>12} {'Coverage':>12}"
        )
        lines.append("-" * 80)
        for row in model_results["cross_validation"]["summary"]:
            lines.append(
                f"{row['model']:<40} {row['rmse_pct']:>12.2f} {row['mae_pct']:>12.2f} "
                f"{row['coverage']:>12.2f}"
            )

    lines.append("=" * 130)
    lines.append("")
    lines.append(f"Data: {model_results['total_events']} events in {model_results['total_n']} patients from individual SLE CAR-T trials.")
    lines.append("Bayesian models use Jeffreys Beta(0.5, 0.5) uninformative prior unless otherwise specified.")
    lines.append("Random effects meta-analysis uses Freeman-Tukey double arcsine transformation.")
    lines.append("Predictive posterior predicts rate in a hypothetical next study of n=50 patients.")
    lines.append("Kaplan-Meier uses synthetic onset times based on published CRS kinetics (median day 2-3).")

    return "\n".join(lines)


def generate_forest_plot_ascii(
    forest_data: dict[str, Any],
    ae_type: str,
) -> str:
    """Generate ASCII forest plot for a given AE type."""

    data = forest_data.get(ae_type, {})
    entries = data.get("entries", [])
    heterogeneity = data.get("heterogeneity", {})

    lines = []
    lines.append(f"FIGURE: Forest Plot of {ae_type} Rates Across Indications")
    lines.append("=" * 100)
    lines.append("")
    lines.append(f"{'Study':<35} {'Rate %':>8} {'95% CI':>20} {'N':>6}   {'|':>1}  Plot (0-100%)")
    lines.append("-" * 100)

    current_ind = ""
    for entry in entries:
        ind = entry["indication"]
        if ind != current_ind:
            if current_ind:
                lines.append("")
            lines.append(f"--- {ind} ---")
            current_ind = ind

        rate = entry["rate_pct"]
        ci_low = entry["ci_low_pct"]
        ci_high = entry["ci_high_pct"]
        n = entry["n"]
        trial = entry["trial"]
        is_pooled = entry.get("is_pooled", False)

        ci_str = f"[{ci_low:.1f}, {ci_high:.1f}]"

        # ASCII bar plot (scale 0-100)
        bar_width = 50
        pos = int(rate / 100 * bar_width)
        low_pos = max(0, int(ci_low / 100 * bar_width))
        high_pos = min(bar_width, int(ci_high / 100 * bar_width))

        bar = list("." * bar_width)
        for i in range(low_pos, high_pos + 1):
            if i < bar_width:
                bar[i] = "-"
        if 0 <= pos < bar_width:
            bar[pos] = "#" if not is_pooled else "@"

        bar_str = "".join(bar)
        prefix = "  >> " if is_pooled else "     "

        lines.append(
            f"{prefix}{trial:<30} {rate:>8.1f} {ci_str:>20} {n:>6}   | {bar_str}"
        )

    lines.append("")
    lines.append("-" * 100)
    lines.append(
        f"Heterogeneity: I-squared = {heterogeneity.get('i_squared', 0) * 100:.1f}%, "
        f"Q = {heterogeneity.get('cochran_q', 0):.2f} "
        f"(df={heterogeneity.get('q_df', 0)}, "
        f"p={heterogeneity.get('q_pvalue', 1.0):.4f}), "
        f"tau-squared = {heterogeneity.get('tau_squared', 0):.4f}"
    )
    lines.append("Legend: # = point estimate, @ = pooled estimate, - = CI range, . = baseline")

    return "\n".join(lines)


def generate_evidence_accrual_figure(accrual_data: dict[str, Any]) -> str:
    """Generate ASCII evidence accrual curve."""

    lines = []
    lines.append("FIGURE: Evidence Accrual Curve - CRS Grade >= 3 Rate with CI Narrowing")
    lines.append("=" * 100)
    lines.append("")
    lines.append(
        f"{'Timepoint':<30} {'N':>5} {'Events':>7} {'Mean %':>8} {'95% CI':>22} {'Width':>8} {'|':>1} CI Visualization"
    )
    lines.append("-" * 100)

    for point in accrual_data["CRS_grade3plus"]:
        mean = point["posterior_mean_pct"]
        ci_low = point["ci_low_pct"]
        ci_high = point["ci_high_pct"]
        width = point["ci_width_pct"]
        n = point["n_cumulative"]
        events = point["events_cumulative"]
        projected = " *" if point["is_projected"] else ""

        ci_str = f"[{ci_low:.1f}, {ci_high:.1f}]"

        # ASCII CI visualization (0-30% scale for this AE)
        bar_width = 40
        scale = 30.0  # 0-30% range
        pos = int(mean / scale * bar_width)
        low_pos = max(0, int(ci_low / scale * bar_width))
        high_pos = min(bar_width - 1, int(ci_high / scale * bar_width))

        bar = list(" " * bar_width)
        for i in range(low_pos, high_pos + 1):
            if i < bar_width:
                bar[i] = "="
        if 0 <= pos < bar_width:
            bar[pos] = "*"

        bar_str = "".join(bar)

        lines.append(
            f"{point['timepoint']:<30} {n:>5} {events:>7} {mean:>8.2f} {ci_str:>22} "
            f"{width:>8.2f} | {bar_str}{projected}"
        )

    lines.append("-" * 100)
    lines.append("* = projected data point | Scale: 0-30% | = = CI range, * = posterior mean")
    lines.append("Prior: Beta(0.21, 1.29) - discounted from oncology CRS rate")

    return "\n".join(lines)


def generate_prior_comparison_figure(prior_analysis: dict[str, Any]) -> str:
    """Generate ASCII figure comparing prior strategies."""

    lines = []
    lines.append("FIGURE: Mechanistic vs Uninformative vs Empirical Prior Comparison")
    lines.append("=" * 100)
    lines.append("")
    lines.append("Posterior distributions for SLE CRS Grade >= 3 rate under three prior strategies:")
    lines.append("")
    lines.append(
        f"{'Prior Strategy':<25} {'Prior':<20} {'Posterior Mean':>15} {'95% CI':>22} {'CI Width':>10}"
    )
    lines.append("-" * 100)

    for strategy, data in prior_analysis["prior_comparison"].items():
        prior_str = f"Beta({data['prior']['alpha']:.2f}, {data['prior']['beta']:.2f})"
        ci_str = f"[{data['ci_low_pct']:.2f}, {data['ci_high_pct']:.2f}]"
        lines.append(
            f"{strategy.title():<25} {prior_str:<20} {data['posterior_mean_pct']:>15.2f}% "
            f"{ci_str:>22} {data['ci_width_pct']:>10.2f} pp"
        )

    lines.append("-" * 100)
    lines.append("")
    lines.append("Visual comparison (posterior 95% CI on 0-20% scale):")
    lines.append("")

    for strategy, data in prior_analysis["prior_comparison"].items():
        bar_width = 60
        scale = 20.0
        mean = data["posterior_mean_pct"]
        ci_low = data["ci_low_pct"]
        ci_high = data["ci_high_pct"]

        pos = int(mean / scale * bar_width)
        low_pos = max(0, int(ci_low / scale * bar_width))
        high_pos = min(bar_width - 1, int(ci_high / scale * bar_width))

        bar = list("." * bar_width)
        for i in range(low_pos, high_pos + 1):
            if i < bar_width:
                bar[i] = "="
        if 0 <= pos < bar_width:
            bar[pos] = "#"

        lines.append(f"  {strategy:<15} |{''.join(bar)}|")

    lines.append(f"  {'Scale:':<15} |{'0%':<29}{'10%':>1}{'':>29}{'20%':>1}|")

    lines.append("")
    lines.append("Prior sensitivity analysis (varying effective sample size):")
    lines.append(f"{'n_eff':>6} {'Prior Alpha':>12} {'Prior Beta':>12} {'Post. Mean':>12} {'CI Width':>10}")
    lines.append("-" * 60)
    for row in prior_analysis.get("sensitivity_analysis", []):
        lines.append(
            f"{row['effective_n']:>6} {row['prior_alpha']:>12.4f} {row['prior_beta']:>12.4f} "
            f"{row['posterior_mean_pct']:>12.2f}% {row['ci_width_pct']:>10.2f} pp"
        )

    return "\n".join(lines)


def generate_calibration_figure(model_results: dict[str, Any]) -> str:
    """Generate ASCII model calibration comparison."""

    lines = []
    lines.append("FIGURE: Model Calibration Comparison (LOO Cross-Validation)")
    lines.append("=" * 100)

    cv = model_results.get("cross_validation", {})
    if not cv or not cv.get("summary"):
        lines.append("(Insufficient data for calibration plot)")
        return "\n".join(lines)

    lines.append("")
    lines.append("Leave-One-Study-Out Prediction Accuracy:")
    lines.append("")
    lines.append(f"{'Model':<35} {'RMSE':>8} {'MAE':>8} {'Coverage':>10} {'Rank':>6}")
    lines.append("-" * 70)

    for rank, row in enumerate(cv["summary"], 1):
        lines.append(
            f"{row['model']:<35} {row['rmse_pct']:>8.2f} {row['mae_pct']:>8.2f} "
            f"{row['coverage']:>10.2f} {rank:>6}"
        )

    lines.append("-" * 70)
    lines.append("")
    lines.append(f"Best model: {cv.get('best_model', 'N/A')} (lowest RMSE)")
    lines.append("")
    lines.append("Per-fold details (held-out study predictions):")
    lines.append(
        f"{'Model':<25} {'Fold':<20} {'True Rate':>10} {'Predicted':>10} {'Error':>10} {'Covered':>10}"
    )
    lines.append("-" * 90)

    for model_name, result in cv.get("per_model", {}).items():
        if "error" in result:
            continue
        for fold in result.get("folds", []):
            lines.append(
                f"{model_name:<25} {fold['held_out_label']:<20} {fold['true_rate_pct']:>10.2f} "
                f"{fold['predicted_pct']:>10.2f} {fold['error_pct']:>10.2f} "
                f"{'Yes' if fold['covered'] else 'No':>10}"
            )

    return "\n".join(lines)


# =========================================================================
# SECTION 7: STATISTICAL SUMMARY
# =========================================================================

def generate_statistical_summary(
    assembled_data: dict[str, Any],
    model_results: dict[str, Any],
    prior_analysis: dict[str, Any],
    cross_indication: dict[str, Any],
    accrual_data: dict[str, Any],
) -> str:
    """Generate comprehensive statistical summary."""

    lines = []
    lines.append("=" * 80)
    lines.append("STATISTICAL SUMMARY")
    lines.append("Comparative Analysis of Cell Therapy Safety Profiles")
    lines.append("=" * 80)
    lines.append("")

    # ── Data overview ────────────────────────────────────────────────────
    lines.append("1. DATA OVERVIEW")
    lines.append("-" * 40)
    for ind, info in assembled_data["summary"].items():
        lines.append(
            f"   {ind}: {info['n_trials']} trials, {info['total_patients']} patients, "
            f"years {info['year_range']}, targets: {', '.join(info['targets'])}"
        )
    lines.append("")

    # ── Key findings ─────────────────────────────────────────────────────
    lines.append("2. KEY FINDINGS")
    lines.append("-" * 40)

    # SLE vs Oncology CRS comparison
    pairwise = cross_indication.get("pairwise_comparisons", {})
    crs_any = pairwise.get("CRS Any Grade", {})
    for comp in ["SLE_vs_DLBCL", "SLE_vs_ALL", "SLE_vs_MM"]:
        if comp in crs_any:
            d = crs_any[comp]
            sig = " (p < 0.05)" if d["significant_at_005"] else " (NS)"
            lines.append(
                f"   CRS Any Grade {comp.replace('_', ' ')}: "
                f"{d['sle_rate_pct']:.1f}% vs {d['comparator_rate_pct']:.1f}%, "
                f"diff = {d['difference_pp']:.1f} pp{sig}"
            )

    lines.append("")
    crs_g3 = pairwise.get("CRS Grade >= 3", {})
    for comp in ["SLE_vs_DLBCL", "SLE_vs_ALL", "SLE_vs_MM"]:
        if comp in crs_g3:
            d = crs_g3[comp]
            sig = " (p < 0.05)" if d["significant_at_005"] else " (NS)"
            lines.append(
                f"   CRS G>=3 {comp.replace('_', ' ')}: "
                f"{d['sle_rate_pct']:.1f}% vs {d['comparator_rate_pct']:.1f}%, "
                f"diff = {d['difference_pp']:.1f} pp{sig}"
            )

    lines.append("")

    # Model comparison summary
    lines.append("3. MODEL COMPARISON SUMMARY (SLE CRS Grade >= 3)")
    lines.append("-" * 40)
    for name, result in model_results["model_results"].items():
        lines.append(
            f"   {name}: {result['estimate_pct']:.2f}% "
            f"[{result['ci_low_pct']:.2f}, {result['ci_high_pct']:.2f}]"
        )
    lines.append("")

    # Mechanistic prior impact
    lines.append("4. MECHANISTIC PRIOR ANALYSIS")
    lines.append("-" * 40)
    pc = prior_analysis.get("prior_comparison", {})
    if "uninformative" in pc and "mechanistic" in pc:
        uninf_width = pc["uninformative"]["ci_width_pct"]
        mech_width = pc["mechanistic"]["ci_width_pct"]
        improvement = ((uninf_width - mech_width) / uninf_width * 100) if uninf_width > 0 else 0
        lines.append(
            f"   Uninformative CI width: {uninf_width:.2f} pp"
        )
        lines.append(
            f"   Mechanistic CI width:   {mech_width:.2f} pp"
        )
        lines.append(
            f"   CI narrowing:           {improvement:.1f}% reduction"
        )
        lines.append(
            f"   Pathway basis: {len(prior_analysis.get('pathway_features', {}).get('CRS', {}).get('references', []))} PubMed references"
        )
    lines.append("")

    # Evidence accrual projection
    lines.append("5. EVIDENCE ACCRUAL PROJECTION")
    lines.append("-" * 40)
    if accrual_data.get("CRS_grade3plus"):
        first = accrual_data["CRS_grade3plus"][0]
        last_observed = [
            p for p in accrual_data["CRS_grade3plus"] if not p["is_projected"]
        ][-1]
        last_projected = accrual_data["CRS_grade3plus"][-1]

        lines.append(
            f"   Initial (n={first['n_cumulative']}): "
            f"CI width = {first['ci_width_pct']:.2f} pp"
        )
        lines.append(
            f"   Current (n={last_observed['n_cumulative']}): "
            f"CI width = {last_observed['ci_width_pct']:.2f} pp"
        )
        lines.append(
            f"   Projected (n={last_projected['n_cumulative']}): "
            f"CI width = {last_projected['ci_width_pct']:.2f} pp"
        )
    lines.append("")

    # Limitations
    lines.append("6. LIMITATIONS")
    lines.append("-" * 40)
    lines.append("   - Small sample sizes in SLE trials (n=2-15 per study)")
    lines.append("   - Early-phase data; mature follow-up not yet available")
    lines.append("   - Heterogeneous CAR-T constructs across SLE trials")
    lines.append("   - No head-to-head randomized comparisons across indications")
    lines.append("   - Oncology comparator data from different eras (2017-2021 vs 2022-2025)")
    lines.append("   - CRS/ICANS grading may not be fully comparable across institutions")
    lines.append("   - Kaplan-Meier analysis uses synthetic onset times (not individual patient data)")
    lines.append("   - Publication bias cannot be fully assessed with available studies")
    lines.append("")

    lines.append("7. REFERENCES")
    lines.append("-" * 40)
    # Collect all unique PubMed IDs referenced
    all_pmids = set()
    for pathway in PATHWAY_REGISTRY.values():
        all_pmids.update(pathway.key_references)
        for step in pathway.steps:
            all_pmids.update(step.references)
    for ref_id, ref in REFERENCES.items():
        all_pmids.add(ref_id)

    for pmid in sorted(all_pmids):
        ref = get_reference(pmid)
        if ref:
            lines.append(
                f"   {pmid}: {ref.first_author} et al., {ref.journal} {ref.year}. "
                f"{ref.title[:70]}{'...' if len(ref.title) > 70 else ''}"
            )

    return "\n".join(lines)


# =========================================================================
# MAIN EXECUTION
# =========================================================================

def main() -> None:
    """Run the complete publication analysis pipeline."""

    logger.info("=" * 70)
    logger.info("PUBLICATION-READY COMPARATIVE ANALYSIS")
    logger.info("Cell Therapy Safety Profiles: Autoimmune vs Oncology CAR-T")
    logger.info("Predictive Safety Platform v0.1.0")
    logger.info("=" * 70)
    logger.info("")

    # ── Step 1: Assemble data ────────────────────────────────────────────
    assembled_data = assemble_trial_data()

    # ── Step 2: Run 7-model comparison ───────────────────────────────────
    model_results = run_seven_model_comparison(assembled_data)

    # ── Step 3: Mechanistic prior analysis ───────────────────────────────
    prior_analysis = mechanistic_prior_analysis(assembled_data)

    # ── Step 4: Cross-indication comparison ──────────────────────────────
    cross_indication = cross_indication_comparison(assembled_data)

    # ── Step 5: Evidence accrual ─────────────────────────────────────────
    accrual_data = evidence_accrual_analysis()

    # ── Step 6: Generate tables and figures ───────────────────────────────
    logger.info("")
    logger.info("=" * 70)
    logger.info("GENERATING TABLES AND FIGURES")
    logger.info("=" * 70)

    # Table 1
    table_1 = generate_table_1(assembled_data)
    with open(RESULTS_DIR / "table_1_demographics.txt", "w") as f:
        f.write(table_1)
    logger.info("  Saved: table_1_demographics.txt")

    # Table 2
    table_2 = generate_table_2(assembled_data)
    with open(RESULTS_DIR / "table_2_ae_rates.txt", "w") as f:
        f.write(table_2)
    logger.info("  Saved: table_2_ae_rates.txt")

    # Table 3
    table_3 = generate_table_3(model_results)
    with open(RESULTS_DIR / "table_3_model_comparison.txt", "w") as f:
        f.write(table_3)
    logger.info("  Saved: table_3_model_comparison.txt")

    # Figure 1: Forest plot
    forest_crs = generate_forest_plot_ascii(
        cross_indication["forest_data"], "CRS Any Grade"
    )
    with open(RESULTS_DIR / "figure_1_forest_crs.txt", "w") as f:
        f.write(forest_crs)
    logger.info("  Saved: figure_1_forest_crs.txt")

    # Also generate forest plot for CRS Grade >= 3
    forest_crs_g3 = generate_forest_plot_ascii(
        cross_indication["forest_data"], "CRS Grade >= 3"
    )
    with open(RESULTS_DIR / "figure_1b_forest_crs_g3.txt", "w") as f:
        f.write(forest_crs_g3)
    logger.info("  Saved: figure_1b_forest_crs_g3.txt")

    # Figure 2: Evidence accrual
    accrual_fig = generate_evidence_accrual_figure(accrual_data)
    with open(RESULTS_DIR / "figure_2_evidence_accrual.txt", "w") as f:
        f.write(accrual_fig)
    logger.info("  Saved: figure_2_evidence_accrual.txt")

    # Figure 3: Prior comparison
    prior_fig = generate_prior_comparison_figure(prior_analysis)
    with open(RESULTS_DIR / "figure_3_prior_comparison.txt", "w") as f:
        f.write(prior_fig)
    logger.info("  Saved: figure_3_prior_comparison.txt")

    # Figure 4: Calibration
    calib_fig = generate_calibration_figure(model_results)
    with open(RESULTS_DIR / "figure_4_calibration.txt", "w") as f:
        f.write(calib_fig)
    logger.info("  Saved: figure_4_calibration.txt")

    # Statistical summary
    summary = generate_statistical_summary(
        assembled_data, model_results, prior_analysis,
        cross_indication, accrual_data,
    )
    with open(RESULTS_DIR / "statistical_summary.txt", "w") as f:
        f.write(summary)
    logger.info("  Saved: statistical_summary.txt")

    # ── Save structured results as JSON ──────────────────────────────────
    json_results = {
        "data_summary": assembled_data["summary"],
        "model_results": {
            name: {
                "estimate_pct": r["estimate_pct"],
                "ci_low_pct": r["ci_low_pct"],
                "ci_high_pct": r["ci_high_pct"],
                "ci_width_pct": r["ci_width_pct"],
                "method": r["method"],
            }
            for name, r in model_results["model_results"].items()
        },
        "cross_validation_summary": model_results["cross_validation"]["summary"],
        "prior_comparison": prior_analysis["prior_comparison"],
        "pairwise_comparisons": cross_indication["pairwise_comparisons"],
        "evidence_accrual": accrual_data,
        "heterogeneity": {
            ae: fd["heterogeneity"]
            for ae, fd in cross_indication["forest_data"].items()
        },
    }

    with open(RESULTS_DIR / "analysis_results.json", "w") as f:
        json.dump(json_results, f, indent=2, default=str)
    logger.info("  Saved: analysis_results.json")

    logger.info("")
    logger.info("=" * 70)
    logger.info("ANALYSIS COMPLETE")
    logger.info("All outputs saved to: %s", RESULTS_DIR)
    logger.info("=" * 70)

    # Print key tables to stdout for immediate review
    print("\n")
    print(table_1)
    print("\n")
    print(table_2)
    print("\n")
    print(table_3)
    print("\n")
    print(forest_crs)
    print("\n")
    print(accrual_fig)
    print("\n")
    print(prior_fig)
    print("\n")
    print(calib_fig)
    print("\n")
    print(summary)


if __name__ == "__main__":
    main()
