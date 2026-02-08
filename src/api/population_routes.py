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
    EligibilityCriteriaResponse,
    EligibilityCriterion,
    EvidenceAccrualPoint,
    EvidenceAccrualResponse,
    FAERSSignalResponse,
    FAERSSummaryResponse,
    MitigationAnalysisRequest,
    MitigationAnalysisResponse,
    MonitoringActivity,
    MonitoringScheduleResponse,
    PopulationRiskResponse,
    PosteriorEstimateResponse,
    SampleSizeResponse,
    SampleSizeScenario,
    StoppingBoundary,
    StoppingRule,
    StoppingRulesResponse,
    TherapyListItem,
    TherapyListResponse,
    TrialSummaryResponse,
)
from src.models.bayesian_risk import (
    CRS_PRIOR,
    ICAHS_PRIOR,
    ICANS_PRIOR,
    STUDY_TIMELINE,
    compute_evidence_accrual,
    compute_posterior,
    compute_stopping_boundaries,
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
from data.cell_therapy_registry import THERAPY_TYPES

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


# ---------------------------------------------------------------------------
# GET /api/v1/therapies -- Available therapy types
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/therapies",
    response_model=TherapyListResponse,
    tags=["Population"],
    summary="List available therapy types",
    description=(
        "Returns all cell/gene therapy types from the registry with their "
        "category and data availability status."
    ),
)
async def list_therapies() -> TherapyListResponse:
    """Return available therapy types from the cell therapy registry."""
    # Therapy types with SLE-specific clinical data available
    _DATA_AVAILABLE_IDS = {"cart_cd19"}

    therapies = []
    for tid, therapy in THERAPY_TYPES.items():
        therapies.append(TherapyListItem(
            id=tid,
            name=therapy.name,
            category=therapy.category,
            data_available=tid in _DATA_AVAILABLE_IDS,
        ))

    return TherapyListResponse(therapies=therapies)


# ---------------------------------------------------------------------------
# GET /api/v1/cdp/monitoring-schedule -- Suggested monitoring schedule
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/cdp/monitoring-schedule",
    response_model=MonitoringScheduleResponse,
    tags=["Population"],
    summary="CDP monitoring schedule",
    description=(
        "Returns a suggested monitoring schedule based on AE onset profiles "
        "for the specified therapy type. Default is CAR-T CD19 in SLE."
    ),
)
async def cdp_monitoring_schedule(
    therapy_type: str = Query(
        "car-t-cd19-sle",
        description="Therapy type identifier (e.g. 'car-t-cd19-sle')",
    ),
) -> MonitoringScheduleResponse:
    """Return suggested monitoring schedule based on AE onset timing."""
    schedule = [
        MonitoringActivity(
            time_window="Pre-infusion",
            days="D-7 to D-1",
            activities=[
                "Baseline CBC",
                "CRP",
                "Ferritin",
                "IL-6",
                "Cardiac assessment",
                "Neurological assessment",
            ],
            frequency="Once",
            rationale="Establish baseline for post-infusion monitoring",
        ),
        MonitoringActivity(
            time_window="Acute (D0-D3)",
            days="D0 to D3",
            activities=[
                "CRS grading (ASTCT)",
                "Vitals q4h",
                "CRP/Ferritin daily",
                "ICE assessment q12h",
            ],
            frequency="Per protocol",
            rationale="Peak CRS onset window",
        ),
        MonitoringActivity(
            time_window="Early post-infusion (D4-D14)",
            days="D4 to D14",
            activities=[
                "CRS grading daily",
                "ICE assessment daily",
                "CBC with differential q2d",
                "CRP q2d",
                "Ferritin q2d",
                "LDH",
                "Fibrinogen",
            ],
            frequency="Daily to q2d",
            rationale="Continued CRS/ICANS monitoring; onset of delayed neurotoxicity",
        ),
        MonitoringActivity(
            time_window="Post-acute (D15-D28)",
            days="D15 to D28",
            activities=[
                "CBC with differential twice weekly",
                "CRP weekly",
                "Immunoglobulin levels",
                "B-cell counts (CD19+)",
                "Infection surveillance",
            ],
            frequency="Twice weekly to weekly",
            rationale="Prolonged cytopenia monitoring; B-cell aplasia onset",
        ),
        MonitoringActivity(
            time_window="Recovery (D29-D90)",
            days="D29 to D90",
            activities=[
                "CBC weekly then biweekly",
                "Immunoglobulin levels monthly",
                "B-cell recovery assessment",
                "SLE disease activity (SLEDAI-2K)",
                "Complement (C3/C4)",
                "Anti-dsDNA antibodies",
            ],
            frequency="Weekly to monthly",
            rationale="Hematologic recovery; early efficacy assessment; infection risk",
        ),
        MonitoringActivity(
            time_window="Long-term (D91-Y1)",
            days="D91 to Y1",
            activities=[
                "CBC monthly",
                "Immunoglobulin levels monthly",
                "SLE disease activity quarterly",
                "IVIG requirement assessment",
                "Secondary malignancy screening",
                "T-cell subset analysis",
            ],
            frequency="Monthly to quarterly",
            rationale="Long-term safety; B-cell reconstitution; sustained remission",
        ),
        MonitoringActivity(
            time_window="Extended follow-up (Y1-Y5)",
            days="Y1 to Y5",
            activities=[
                "CBC quarterly",
                "Immunoglobulin levels quarterly",
                "SLE disease activity biannually",
                "Secondary malignancy screening annually",
                "Replication-competent lentivirus (RCL) testing annually",
            ],
            frequency="Quarterly to annually",
            rationale="FDA-required long-term follow-up; secondary malignancy surveillance",
        ),
    ]

    return MonitoringScheduleResponse(
        therapy_type=therapy_type,
        schedule=schedule,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/cdp/eligibility-criteria -- Suggested inclusion/exclusion
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/cdp/eligibility-criteria",
    response_model=EligibilityCriteriaResponse,
    tags=["Population"],
    summary="CDP eligibility criteria",
    description=(
        "Returns suggested inclusion and exclusion criteria for a cell therapy "
        "clinical development plan."
    ),
)
async def cdp_eligibility_criteria(
    therapy_type: str = Query(
        "car-t-cd19-sle",
        description="Therapy type identifier (e.g. 'car-t-cd19-sle')",
    ),
) -> EligibilityCriteriaResponse:
    """Return suggested inclusion/exclusion criteria."""
    inclusion = [
        EligibilityCriterion(
            criterion="Age >= 18 years",
            rationale="Adult population for initial safety assessment",
            category="Demographics",
        ),
        EligibilityCriterion(
            criterion="Confirmed SLE diagnosis (ACR/EULAR 2019 criteria)",
            rationale="Target population definition",
            category="Disease",
        ),
        EligibilityCriterion(
            criterion="Active disease (SLEDAI-2K >= 6) despite standard of care",
            rationale="Refractory population with unmet medical need",
            category="Disease",
        ),
        EligibilityCriterion(
            criterion="Failed >= 2 prior standard therapies",
            rationale="Ensure adequate prior treatment before cell therapy",
            category="Treatment History",
        ),
        EligibilityCriterion(
            criterion="Positive anti-dsDNA antibodies or low complement",
            rationale="Serologically active disease confirmation",
            category="Disease",
        ),
        EligibilityCriterion(
            criterion="ECOG performance status 0-1",
            rationale="Adequate functional status for lymphodepletion and CAR-T infusion",
            category="General Health",
        ),
        EligibilityCriterion(
            criterion="Adequate organ function (hepatic, renal, pulmonary)",
            rationale="Tolerate lymphodepletion conditioning and potential CRS",
            category="Organ Function",
        ),
        EligibilityCriterion(
            criterion="LVEF >= 45% by echocardiography",
            rationale="Cardiac reserve for CRS-related hemodynamic stress",
            category="Cardiac",
        ),
    ]

    exclusion = [
        EligibilityCriterion(
            criterion="Active uncontrolled infection",
            rationale="Lymphodepletion increases infection risk",
            category="Safety",
        ),
        EligibilityCriterion(
            criterion="Prior Grade >= 3 CRS with any CAR-T product",
            rationale="Elevated re-treatment risk",
            category="Safety",
        ),
        EligibilityCriterion(
            criterion="LVEF < 45%",
            rationale="CRS-related hemodynamic stress risk",
            category="Cardiac",
        ),
        EligibilityCriterion(
            criterion="Active CNS lupus or history of seizures within 12 months",
            rationale="Increased ICANS risk with baseline neurological involvement",
            category="Neurological",
        ),
        EligibilityCriterion(
            criterion="Active or prior malignancy within 5 years (except non-melanoma skin cancer)",
            rationale="Secondary malignancy concern with gene-modified cells",
            category="Safety",
        ),
        EligibilityCriterion(
            criterion="HIV, active HBV, or active HCV infection",
            rationale="Immunosuppression risk with lymphodepletion; viral reactivation concern",
            category="Infections",
        ),
        EligibilityCriterion(
            criterion="Prior allogeneic stem cell transplant",
            rationale="Altered immune reconstitution and GVHD risk",
            category="Treatment History",
        ),
        EligibilityCriterion(
            criterion="eGFR < 30 mL/min/1.73m2 or dialysis-dependent",
            rationale="Impaired drug clearance; tocilizumab and conditioning agent handling",
            category="Renal",
        ),
        EligibilityCriterion(
            criterion="Pregnancy or breastfeeding",
            rationale="Unknown teratogenic risk of gene-modified cells",
            category="Reproductive",
        ),
        EligibilityCriterion(
            criterion="Live vaccine within 4 weeks of lymphodepletion",
            rationale="Risk of vaccine-strain infection during immunosuppression",
            category="Safety",
        ),
    ]

    return EligibilityCriteriaResponse(
        therapy_type=therapy_type,
        inclusion=inclusion,
        exclusion=exclusion,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/cdp/stopping-rules -- Bayesian stopping rule boundaries
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/cdp/stopping-rules",
    response_model=StoppingRulesResponse,
    tags=["Population"],
    summary="CDP Bayesian stopping rules",
    description=(
        "Returns Bayesian stopping rule boundaries for key adverse events. "
        "For each AE type, provides the maximum number of events tolerable "
        "at each sample size before enrollment should be paused."
    ),
)
async def cdp_stopping_rules(
    therapy_type: str = Query(
        "car-t-cd19-sle",
        description="Therapy type identifier (e.g. 'car-t-cd19-sle')",
    ),
) -> StoppingRulesResponse:
    """Return Bayesian stopping rule boundaries for key AEs."""
    ae_configs = [
        {
            "ae_type": "CRS Grade 3+",
            "target_rate": 0.05,
            "threshold": 0.8,
            "description": (
                "Pause enrollment if posterior probability that CRS G3+ "
                "rate > 5% exceeds 0.8"
            ),
        },
        {
            "ae_type": "ICANS Grade 3+",
            "target_rate": 0.05,
            "threshold": 0.8,
            "description": (
                "Pause enrollment if posterior probability that ICANS G3+ "
                "rate > 5% exceeds 0.8"
            ),
        },
        {
            "ae_type": "ICAHS Grade 3+",
            "target_rate": 0.03,
            "threshold": 0.8,
            "description": (
                "Pause enrollment if posterior probability that ICAHS G3+ "
                "rate > 3% exceeds 0.8"
            ),
        },
    ]

    # Key sample sizes to report
    key_ns = [10, 20, 30, 50, 75, 100]

    rules = []
    for cfg in ae_configs:
        all_boundaries = compute_stopping_boundaries(
            target_rate=cfg["target_rate"],
            posterior_threshold=cfg["threshold"],
            max_n=100,
            prior_alpha=0.5,
            prior_beta=0.5,
        )

        # Build a lookup from full boundaries
        boundary_lookup: dict[int, int] = {}
        last_max = 0
        for bd in all_boundaries:
            last_max = bd["max_events"]
            boundary_lookup[bd["n_patients"]] = last_max
        # Fill in intermediate values
        current_max = 0
        filled: dict[int, int] = {}
        for n in range(1, 101):
            if n in boundary_lookup:
                current_max = boundary_lookup[n]
            filled[n] = current_max

        # Extract boundaries at key sample sizes
        compact_boundaries = [
            StoppingBoundary(n_patients=n, max_events=filled.get(n, 0))
            for n in key_ns
        ]

        rules.append(StoppingRule(
            ae_type=cfg["ae_type"],
            target_rate_pct=cfg["target_rate"] * 100,
            posterior_threshold=cfg["threshold"],
            description=cfg["description"],
            boundaries=compact_boundaries,
        ))

    return StoppingRulesResponse(
        therapy_type=therapy_type,
        rules=rules,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/cdp/sample-size -- Sample size considerations
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/cdp/sample-size",
    response_model=SampleSizeResponse,
    tags=["Population"],
    summary="CDP sample size considerations",
    description=(
        "Returns sample size scenarios for key precision targets, showing "
        "how many additional patients are needed to achieve target CI widths."
    ),
)
async def cdp_sample_size(
    therapy_type: str = Query(
        "car-t-cd19-sle",
        description="Therapy type identifier (e.g. 'car-t-cd19-sle')",
    ),
) -> SampleSizeResponse:
    """Return sample size considerations for the therapy type."""
    current_n = 47  # Current pooled SLE data

    scenarios = [
        SampleSizeScenario(
            target_precision="CI width < 10%",
            estimated_n=60,
            current_n=current_n,
            additional_needed=max(0, 60 - current_n),
            notes=(
                "For CRS G3+ rate estimation with 95% CI width under "
                "10 percentage points"
            ),
        ),
        SampleSizeScenario(
            target_precision="CI width < 7%",
            estimated_n=120,
            current_n=current_n,
            additional_needed=max(0, 120 - current_n),
            notes=(
                "For CRS G3+ rate estimation with 95% CI width under "
                "7 percentage points, enabling regulatory-grade precision"
            ),
        ),
        SampleSizeScenario(
            target_precision="CI width < 5%",
            estimated_n=200,
            current_n=current_n,
            additional_needed=max(0, 200 - current_n),
            notes=(
                "For CRS G3+ rate estimation with 95% CI width under "
                "5 percentage points, suitable for label claim"
            ),
        ),
        SampleSizeScenario(
            target_precision="Detect 3% rate with 80% power",
            estimated_n=150,
            current_n=current_n,
            additional_needed=max(0, 150 - current_n),
            notes=(
                "Power to detect a 3% AE rate as significantly different "
                "from zero using one-sided exact binomial test at alpha=0.05"
            ),
        ),
        SampleSizeScenario(
            target_precision="Rule of 3: exclude 5% rate",
            estimated_n=60,
            current_n=current_n,
            additional_needed=max(0, 60 - current_n),
            notes=(
                "If 0 events in 60 patients, upper 95% CI bound is ~5% "
                "(rule of 3: 3/n), sufficient to exclude a 5% rate"
            ),
        ),
    ]

    return SampleSizeResponse(
        therapy_type=therapy_type,
        scenarios=scenarios,
    )
