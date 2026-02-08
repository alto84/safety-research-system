"""
Population-level API routes for Bayesian risk estimation, mitigation modeling,
evidence accrual, clinical trials, and FAERS signal detection.

These endpoints complement the patient-level biomarker scoring endpoints by
providing population-level context: What is the baseline risk for CAR-T AEs
in autoimmune indications?  How does that risk change with mitigation strategies?
How does uncertainty narrow as trial evidence accrues?
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    BayesianPosteriorRequest,
    BayesianPosteriorResponse,
    CorrelationDetail,
    EvidenceAccrualPoint,
    EvidenceAccrualResponse,
    FAERSSignalResponse,
    FAERSSummaryResponse,
    MitigationAnalysisRequest,
    MitigationAnalysisResponse,
    PopulationRiskResponse,
    PosteriorEstimateResponse,
    TrialSummaryResponse,
)
from src.models.bayesian_risk import (
    CRS_PRIOR,
    ICAHS_PRIOR,
    ICANS_PRIOR,
    STUDY_TIMELINE,
    compute_evidence_accrual,
    compute_posterior,
)
from src.models.mitigation_model import (
    MITIGATION_STRATEGIES,
    calculate_mitigated_risk,
    combine_multiple_rrs,
    get_mitigation_correlation,
    monte_carlo_mitigated_risk,
)
from src.models.faers_signal import get_faers_signals
from data.sle_cart_studies import (
    CLINICAL_TRIALS,
    get_comparison_chart_data,
    get_sle_baseline_risk,
    get_trial_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Map AE names to priors
_PRIOR_MAP = {
    "CRS": CRS_PRIOR,
    "ICANS": ICANS_PRIOR,
    "ICAHS": ICAHS_PRIOR,
}

# Map AE names to event fields in the timeline
_EVENT_FIELD_MAP = {
    "CRS": "crs_grade3plus_events",
    "ICANS": "icans_grade3plus_events",
}


# ---------------------------------------------------------------------------
# GET /api/v1/population/risk -- SLE baseline risk summary
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/population/risk",
    response_model=PopulationRiskResponse,
    tags=["Population"],
    summary="SLE CAR-T baseline risk summary",
    description=(
        "Returns the pooled baseline risk estimates for Grade 3+ CRS, ICANS, "
        "ICAHS, and LICATS from published SLE CAR-T studies (n=47). Includes "
        "default mitigated risk estimates using tocilizumab + corticosteroids."
    ),
)
async def population_risk() -> PopulationRiskResponse:
    """Return population-level risk summary for SLE CAR-T."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    baseline = get_sle_baseline_risk()

    # Compute mitigated risks using default mitigation combo
    default_mitigations = ["tocilizumab", "corticosteroids"]
    crs_baseline = baseline["crs_grade3_plus"]["estimate"] / 100.0
    icans_baseline = baseline["icans_grade3_plus"]["estimate"] / 100.0

    mitigated = calculate_mitigated_risk(
        baseline_crs=crs_baseline,
        baseline_icans=icans_baseline,
        selected_ids=default_mitigations,
    )

    mitigated_risks = {}
    for ae_type in ["crs", "icans"]:
        result = mitigated[ae_type]
        mitigated_risks[ae_type] = {
            "mitigated_risk_pct": round(result.mitigated_risk * 100, 2),
            "combined_rr": round(result.combined_rr, 4),
            "mitigations_applied": result.selected_mitigations,
        }

    return PopulationRiskResponse(
        request_id=request_id,
        timestamp=now,
        indication="SLE",
        n_patients_pooled=47,
        baseline_risks=baseline,
        mitigated_risks=mitigated_risks,
        default_mitigations=default_mitigations,
        evidence_grade="Low (small sample, early-phase trials)",
    )


# ---------------------------------------------------------------------------
# POST /api/v1/population/bayesian -- Custom Bayesian posterior
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/population/bayesian",
    response_model=BayesianPosteriorResponse,
    tags=["Population"],
    summary="Compute Bayesian posterior for AE rate",
    description=(
        "Computes a Beta-Binomial posterior for a specified adverse event, "
        "given observed events and total patients. Uses informative priors "
        "derived from discounted oncology CAR-T data by default."
    ),
)
async def bayesian_posterior(
    request: BayesianPosteriorRequest,
) -> BayesianPosteriorResponse:
    """Compute Bayesian posterior estimate."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    prior = _PRIOR_MAP.get(request.adverse_event)
    if prior is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown adverse event '{request.adverse_event}'. "
                   f"Valid: {list(_PRIOR_MAP.keys())}",
        )

    try:
        estimate = compute_posterior(
            prior=prior,
            events=request.n_events,
            n=request.n_patients,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return BayesianPosteriorResponse(
        request_id=request_id,
        timestamp=now,
        estimate=PosteriorEstimateResponse(
            adverse_event=request.adverse_event,
            prior_alpha=prior.alpha,
            prior_beta=prior.beta,
            posterior_alpha=estimate.alpha,
            posterior_beta=estimate.beta,
            n_patients=estimate.n_patients,
            n_events=estimate.n_events,
            mean_pct=estimate.mean,
            ci_low_pct=estimate.ci_low,
            ci_high_pct=estimate.ci_high,
            ci_width_pct=estimate.ci_width,
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/population/mitigations -- Correlated mitigation analysis
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/population/mitigations",
    response_model=MitigationAnalysisResponse,
    tags=["Population"],
    summary="Correlated mitigation risk analysis",
    description=(
        "Computes the combined risk reduction from selected mitigation strategies, "
        "accounting for mechanistic correlations between interventions. Uses Monte "
        "Carlo simulation for uncertainty propagation."
    ),
)
async def mitigation_analysis(
    request: MitigationAnalysisRequest,
) -> MitigationAnalysisResponse:
    """Run correlated mitigation combination analysis."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Validate mitigation IDs
    unknown = [
        mid for mid in request.selected_mitigations
        if mid not in MITIGATION_STRATEGIES
    ]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown mitigation IDs: {unknown}. "
                   f"Valid: {list(MITIGATION_STRATEGIES.keys())}",
        )

    # Get baseline risk and prior for target AE
    baseline_risk_data = get_sle_baseline_risk()
    target_key = f"{request.target_ae.lower()}_grade3_plus"
    if target_key not in baseline_risk_data:
        target_key = request.target_ae.lower()
    if target_key not in baseline_risk_data:
        raise HTTPException(
            status_code=400,
            detail=f"No baseline data for AE '{request.target_ae}'",
        )

    baseline_pct = baseline_risk_data[target_key]["estimate"]
    baseline_risk = baseline_pct / 100.0

    # Filter mitigations that target this AE
    target_ae_upper = request.target_ae.upper()
    applicable_ids = []
    applicable_rrs = []
    for mid in request.selected_mitigations:
        strategy = MITIGATION_STRATEGIES[mid]
        if target_ae_upper in strategy.target_aes:
            applicable_ids.append(mid)
            applicable_rrs.append(strategy.relative_risk)

    if not applicable_ids:
        return MitigationAnalysisResponse(
            request_id=request_id,
            timestamp=now,
            target_ae=request.target_ae,
            baseline_risk_pct=baseline_pct,
            mitigated_risk_pct=baseline_pct,
            mitigated_risk_ci_low_pct=baseline_pct,
            mitigated_risk_ci_high_pct=baseline_pct,
            combined_rr=1.0,
            naive_multiplicative_rr=1.0,
            correction_factor=1.0,
            mitigations_applied=[],
            correlations_applied=[],
        )

    # Compute naive multiplicative RR
    naive_rr = 1.0
    for rr in applicable_rrs:
        naive_rr *= rr

    # Compute correlated combined RR
    combined_rr = combine_multiple_rrs(applicable_ids, applicable_rrs)

    # Build correlation details
    correlations = []
    for i in range(len(applicable_ids)):
        for j in range(i + 1, len(applicable_ids)):
            rho = get_mitigation_correlation(applicable_ids[i], applicable_ids[j])
            if rho > 0.0:
                # Compute what this pair alone would give
                from src.models.mitigation_model import combine_correlated_rr
                pair_naive = applicable_rrs[i] * applicable_rrs[j]
                pair_corrected = combine_correlated_rr(
                    applicable_rrs[i], applicable_rrs[j], rho,
                )
                correlations.append(CorrelationDetail(
                    mitigation_a=applicable_ids[i],
                    mitigation_b=applicable_ids[j],
                    rho=rho,
                    naive_rr=round(pair_naive, 4),
                    corrected_rr=round(pair_corrected, 4),
                ))

    # Monte Carlo for uncertainty
    prior = _PRIOR_MAP.get(target_ae_upper, CRS_PRIOR)
    mc_result = monte_carlo_mitigated_risk(
        baseline_alpha=prior.alpha + 1,  # Use current posterior
        baseline_beta=prior.beta + 46,   # n=47, 1 event for CRS
        mitigation_ids=applicable_ids,
        n_samples=request.n_monte_carlo_samples,
        seed=42,
    )

    mitigated_risk = baseline_risk * combined_rr
    correction_factor = combined_rr / naive_rr if naive_rr > 0 else 1.0

    return MitigationAnalysisResponse(
        request_id=request_id,
        timestamp=now,
        target_ae=request.target_ae,
        baseline_risk_pct=round(baseline_pct, 2),
        mitigated_risk_pct=round(mitigated_risk * 100, 4),
        mitigated_risk_ci_low_pct=round(mc_result["p2_5"] * 100, 4),
        mitigated_risk_ci_high_pct=round(mc_result["p97_5"] * 100, 4),
        combined_rr=round(combined_rr, 4),
        naive_multiplicative_rr=round(naive_rr, 4),
        correction_factor=round(correction_factor, 4),
        mitigations_applied=applicable_ids,
        correlations_applied=correlations,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/population/evidence-accrual -- Evidence accrual timeline
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/population/evidence-accrual",
    response_model=EvidenceAccrualResponse,
    tags=["Population"],
    summary="Evidence accrual timeline",
    description=(
        "Returns the sequential Bayesian evidence accrual curve showing how "
        "credible intervals narrow as SLE CAR-T trial data accumulates over time."
    ),
)
async def evidence_accrual() -> EvidenceAccrualResponse:
    """Compute evidence accrual timeline for CRS and ICANS."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Compute CRS and ICANS accrual
    crs_posteriors = compute_evidence_accrual(
        CRS_PRIOR, STUDY_TIMELINE, "crs_grade3plus_events",
    )
    icans_posteriors = compute_evidence_accrual(
        ICANS_PRIOR, STUDY_TIMELINE, "icans_grade3plus_events",
    )

    timeline_points = []
    for i, point in enumerate(STUDY_TIMELINE):
        crs = crs_posteriors[i]
        icans = icans_posteriors[i]
        timeline_points.append(EvidenceAccrualPoint(
            label=point.label,
            year=point.year,
            quarter=point.quarter,
            n_cumulative_patients=point.n_cumulative_patients,
            is_projected=point.is_projected,
            crs_mean_pct=crs.mean,
            crs_ci_low_pct=crs.ci_low,
            crs_ci_high_pct=crs.ci_high,
            crs_ci_width_pct=crs.ci_width,
            icans_mean_pct=icans.mean,
            icans_ci_low_pct=icans.ci_low,
            icans_ci_high_pct=icans.ci_high,
            icans_ci_width_pct=icans.ci_width,
        ))

    # Current (last observed) and projected (last overall) CI widths
    last_observed_idx = max(
        i for i, p in enumerate(STUDY_TIMELINE) if not p.is_projected
    )
    current_width = crs_posteriors[last_observed_idx].ci_width
    projected_width = crs_posteriors[-1].ci_width
    narrowing = (
        (current_width - projected_width) / current_width * 100
        if current_width > 0 else 0.0
    )

    return EvidenceAccrualResponse(
        request_id=request_id,
        timestamp=now,
        timeline=timeline_points,
        current_ci_width_crs_pct=round(current_width, 2),
        projected_ci_width_crs_pct=round(projected_width, 2),
        ci_narrowing_pct=round(narrowing, 1),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/population/trials -- Clinical trial registry
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/population/trials",
    response_model=TrialSummaryResponse,
    tags=["Population"],
    summary="CAR-T clinical trial registry",
    description=(
        "Returns a summary of CAR-T clinical trials in autoimmune and oncology "
        "indications, with enrollment and status data from ClinicalTrials.gov."
    ),
)
async def trial_registry(
    indication: str | None = Query(
        None, description="Filter by indication (e.g. SLE, DLBCL)",
    ),
) -> TrialSummaryResponse:
    """Return clinical trial summary with optional indication filter."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    summary = get_trial_summary()

    # Build trial list
    trials = []
    for t in CLINICAL_TRIALS:
        if indication and indication.upper() not in t.indication.upper():
            continue
        trials.append({
            "name": t.name,
            "sponsor": t.sponsor,
            "nct_id": t.nct_id,
            "phase": t.phase,
            "target": t.target,
            "indication": t.indication,
            "enrollment": t.enrollment,
            "status": t.status,
        })

    # Recompute counts if filtered
    if indication:
        recruiting = sum(1 for t in trials if t["status"] == "Recruiting")
        active = sum(1 for t in trials if t["status"] == "Active")
        completed = sum(1 for t in trials if t["status"] == "Completed")
        not_yet = sum(1 for t in trials if t["status"] == "Not yet recruiting")
    else:
        recruiting = summary["recruiting"]
        active = summary["active"]
        completed = summary["completed"]
        not_yet = summary["not_yet_recruiting"]

    return TrialSummaryResponse(
        request_id=request_id,
        timestamp=now,
        recruiting=recruiting,
        active=active,
        completed=completed,
        not_yet_recruiting=not_yet,
        total=len(trials),
        trials=trials,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/signals/faers -- FAERS signal detection
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/signals/faers",
    response_model=FAERSSummaryResponse,
    tags=["Signals"],
    summary="FAERS signal detection for CAR-T products",
    description=(
        "Queries the FDA Adverse Event Reporting System via openFDA and computes "
        "disproportionality metrics (PRR, ROR, EBGM) for approved CAR-T products. "
        "Note: Queries the live openFDA API and may take 30-60 seconds."
    ),
)
async def faers_signals(
    products: str | None = Query(
        None,
        description="Comma-separated product names (e.g. 'KYMRIAH,YESCARTA'). "
                    "Defaults to all known CAR-T products.",
    ),
) -> FAERSSummaryResponse:
    """Run FAERS signal detection for CAR-T products."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    product_list = None
    if products:
        product_list = [p.strip() for p in products.split(",") if p.strip()]

    try:
        summary = await get_faers_signals(products=product_list)
    except Exception as exc:
        logger.exception("FAERS signal detection failed")
        raise HTTPException(
            status_code=502,
            detail=f"FAERS query failed: {exc}",
        )

    signals = []
    for s in summary.signals:
        signals.append(FAERSSignalResponse(
            product=s.product,
            adverse_event=s.adverse_event,
            n_cases=s.n_cases,
            prr=s.prr,
            prr_ci_low=s.prr_ci_low,
            prr_ci_high=s.prr_ci_high,
            ror=s.ror,
            ror_ci_low=s.ror_ci_low,
            ror_ci_high=s.ror_ci_high,
            ebgm=s.ebgm,
            ebgm05=s.ebgm05,
            is_signal=s.is_signal,
            signal_strength=s.signal_strength,
        ))

    return FAERSSummaryResponse(
        request_id=request_id,
        timestamp=now,
        products_queried=summary.products_queried,
        total_reports=summary.total_reports,
        signals_detected=summary.signals_detected,
        strong_signals=summary.strong_signals,
        signals=signals,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/population/mitigations/strategies -- List available mitigations
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/population/mitigations/strategies",
    tags=["Population"],
    summary="List available mitigation strategies",
    description="Returns all available mitigation strategies with their parameters.",
)
async def list_mitigations() -> dict:
    """Return all mitigation strategy metadata."""
    strategies = []
    for mid, strategy in MITIGATION_STRATEGIES.items():
        strategies.append({
            "id": strategy.id,
            "name": strategy.name,
            "mechanism": strategy.mechanism,
            "target_aes": strategy.target_aes,
            "relative_risk": strategy.relative_risk,
            "confidence_interval": list(strategy.confidence_interval),
            "evidence_level": strategy.evidence_level,
            "dosing": strategy.dosing,
            "timing": strategy.timing,
            "limitations": strategy.limitations,
            "references": strategy.references,
        })

    return {
        "strategies": strategies,
        "total": len(strategies),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/population/comparison -- Cross-indication AE comparison
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/population/comparison",
    tags=["Population"],
    summary="Cross-indication AE rate comparison",
    description=(
        "Returns adverse event rates for SLE vs oncology CAR-T products "
        "for forest plot / comparison chart visualization."
    ),
)
async def ae_comparison() -> dict:
    """Return cross-indication adverse event comparison data."""
    return {
        "comparison_data": get_comparison_chart_data(),
        "note": "SLE data from pooled analysis (n=47); oncology from pivotal trials",
    }
