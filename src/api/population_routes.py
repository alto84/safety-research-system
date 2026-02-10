"""
Population-level API routes for Bayesian risk estimation, mitigation modeling,
evidence accrual, clinical trials, FAERS signal detection, and knowledge graph
queries.

These endpoints complement the patient-level biomarker scoring endpoints by
providing population-level context: What is the baseline risk for CAR-T AEs
in autoimmune indications?  How does that risk change with mitigation strategies?
How does uncertainty narrow as trial evidence accrues?

The knowledge graph endpoints expose mechanistic biology data: signaling pathways,
mechanism chains, molecular targets, cell types, and PubMed references.
"""

from __future__ import annotations

import json
import logging
import pathlib
import time as _time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import (
    ArchitectureResponse,
    BayesianPosteriorRequest,
    BayesianPosteriorResponse,
    CorrelationDetail,
    DependencyEdge,
    EligibilityCriteriaResponse,
    EligibilityCriterion,
    EndpointInfo,
    EvidenceAccrualPoint,
    EvidenceAccrualResponse,
    FAERSSignalResponse,
    FAERSSummaryResponse,
    KnowledgeActivationState,
    KnowledgeCellTypeListResponse,
    KnowledgeCellTypeResponse,
    KnowledgeMechanismListResponse,
    KnowledgeMechanismResponse,
    KnowledgeMechanismStep,
    KnowledgeModulatorResponse,
    KnowledgeOverviewResponse,
    KnowledgePathwayEdge,
    KnowledgePathwayListResponse,
    KnowledgePathwayNode,
    KnowledgePathwayResponse,
    KnowledgePathwayStep,
    KnowledgeReferenceListResponse,
    KnowledgeReferenceResponse,
    KnowledgeTargetListResponse,
    KnowledgeTargetResponse,
    MitigationAnalysisRequest,
    MitigationAnalysisResponse,
    ModuleInfo,
    MonitoringActivity,
    MonitoringScheduleResponse,
    PopulationRiskResponse,
    PosteriorEstimateResponse,
    PublicationAERateRow,
    PublicationAnalysisResponse,
    PublicationCrossValidation,
    PublicationDemographicRow,
    PublicationEvidenceAccrualPoint,
    PublicationFigureResponse,
    PublicationForestPlotData,
    PublicationHeterogeneity,
    PublicationModelResult,
    PublicationPairwiseComparison,
    PublicationPriorComparison,
    PublicationReference,
    PublicationStudyData,
    RegistryModelInfo,
    SampleSizeResponse,
    SampleSizeScenario,
    StoppingBoundary,
    StoppingRule,
    StoppingRulesResponse,
    SystemHealthInfo,
    TestSummary,
    TherapyListItem,
    TherapyListResponse,
    TrialSummaryResponse,
    ClinicalBriefing,
    ClinicalBriefingSection,
    NarrativeRequest,
    NarrativeResponse,
    NarrativeSection,
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
    combine_correlated_rr,
    combine_multiple_rrs,
    get_mitigation_correlation,
    monte_carlo_mitigated_risk,
)
from src.models.faers_signal import get_faers_signals
from src.data.faers_cache import get_faers_comparison
from data.sle_cart_studies import (
    ADVERSE_EVENT_RATES,
    CLINICAL_TRIALS,
    get_comparison_chart_data,
    get_sle_baseline_risk,
    get_trial_summary,
)
from data.cell_therapy_registry import THERAPY_TYPES
from src.models.model_registry import MODEL_REGISTRY as _mr
from src.data.knowledge.pathways import PATHWAY_REGISTRY
from src.data.knowledge.mechanisms import MECHANISM_REGISTRY
from src.data.knowledge.molecular_targets import (
    MOLECULAR_TARGET_REGISTRY,
    get_druggable_targets,
)
from src.data.knowledge.cell_types import CELL_TYPE_REGISTRY
from src.data.knowledge.references import REFERENCES
from src.api.narrative_engine import generate_narrative, generate_briefing
from src.data.ctgov_cache import (
    get_summary as get_ctgov_summary,
    get_trial_summaries as get_ctgov_trial_summaries,
    AE_TERM_MAP as CTGOV_AE_TERM_MAP,
)
from src.models.signal_triangulation import triangulate_signals
from src.data.pharma_org import (
    ORG_ROLES,
    PIPELINE_STAGES,
    REGULATORY_MAP,
    SKILL_LIBRARY,
    get_quality_metrics,
    get_role,
    get_role_skills,
)

# Pharma simulation module — may not exist yet (built in parallel).
# We always define the callable names so that mock.patch works in tests.
try:
    from src.data.pharma_simulation import (
        run_simulation as _run_simulation,
        get_simulation_status as _get_simulation_status,
        get_role_deliverables as _get_role_deliverables,
        get_activity_log as _get_activity_log,
        get_delegation_tree as _get_delegation_tree,
    )
    _SIMULATION_AVAILABLE = True
except ImportError:
    _SIMULATION_AVAILABLE = False

    def _run_simulation() -> dict:  # type: ignore[misc]
        return {}

    def _get_simulation_status() -> dict:  # type: ignore[misc]
        return {}

    def _get_role_deliverables(role_id: str) -> list:  # type: ignore[misc]
        return []

    def _get_activity_log(limit: int = 50) -> list:  # type: ignore[misc]
        return []

    def _get_delegation_tree() -> dict:  # type: ignore[misc]
        return {}

logger = logging.getLogger(__name__)

router = APIRouter()


def _count_tests() -> tuple[int, int, int, int]:
    """Dynamically count test functions and files in the tests/ directory.

    Scans ``tests/`` for ``test_*.py`` files and counts functions whose names
    start with ``test_``.  Categorizes by subdirectory: ``tests/unit/`` and
    ``tests/integration/``.

    Returns:
        Tuple of (total_tests, test_files, unit_tests, integration_tests).
        Returns (0, 0, 0, 0) on any error.
    """
    try:
        tests_dir = pathlib.Path(__file__).resolve().parents[2] / "tests"
        if not tests_dir.is_dir():
            return (0, 0, 0, 0)

        total = 0
        file_count = 0
        unit = 0
        integration = 0

        for tf in tests_dir.rglob("test_*.py"):
            file_count += 1
            count_in_file = 0
            try:
                text = tf.read_text(encoding="utf-8")
                count_in_file = sum(
                    1 for line in text.splitlines()
                    if line.strip().startswith("def test_")
                )
            except Exception:
                continue
            total += count_in_file
            rel = tf.relative_to(tests_dir).parts
            if rel and rel[0] == "unit":
                unit += count_in_file
            elif rel and rel[0] == "integration":
                integration += count_in_file

        return (total, file_count, unit, integration)
    except Exception:
        return (0, 0, 0, 0)

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
    now = datetime.now(timezone.utc)

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

    # H9 fix: Derive n_patients_pooled dynamically from pooled data entry
    n_pooled = ADVERSE_EVENT_RATES[0].n_patients  # Pooled SLE entry

    return PopulationRiskResponse(
        request_id=request_id,
        timestamp=now,
        indication="SLE",
        n_patients_pooled=n_pooled,
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
    now = datetime.now(timezone.utc)

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
    now = datetime.now(timezone.utc)

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
    # Derive posterior parameters dynamically from actual pooled baseline data
    # for the target AE, using the rate fields from the pooled SLE entry.
    prior = _PRIOR_MAP.get(target_ae_upper, CRS_PRIOR)
    _pooled = ADVERSE_EVENT_RATES[0]  # Pooled SLE entry
    _n_total = _pooled.n_patients

    # Map AE type -> rate field on the pooled AdverseEventRate record.
    # Events are derived from (rate_pct / 100) * n_patients, rounded to the
    # nearest integer, so they stay in sync with the curated data rather
    # than being hardcoded constants.
    _ae_rate_field_map: dict[str, str] = {
        "CRS": "crs_grade3_plus",
        "ICANS": "icans_grade3_plus",
        "ICAHS": "icahs_rate",
    }
    _rate_field = _ae_rate_field_map.get(target_ae_upper, "crs_grade3_plus")
    _rate_pct = getattr(_pooled, _rate_field, 0.0)
    _n_events = round(_rate_pct / 100.0 * _n_total)
    mc_result = monte_carlo_mitigated_risk(
        baseline_alpha=prior.alpha + _n_events,
        baseline_beta=prior.beta + (_n_total - _n_events),
        mitigation_ids=applicable_ids,
        n_samples=request.n_monte_carlo_samples,
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
    now = datetime.now(timezone.utc)

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
    now = datetime.now(timezone.utc)

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
    now = datetime.now(timezone.utc)

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
# GET /api/v1/signals/faers/comparison -- Cached FAERS product comparison
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/signals/faers/comparison",
    tags=["Signals"],
    summary="Pre-computed FAERS product comparison across CAR-T products",
    description=(
        "Returns cached FAERS product comparison data extracted from openFDA. "
        "Includes product profiles, report counts, top adverse events, and "
        "cross-product comparison rates for CRS, neurotoxicity, mortality, "
        "infections, and cytopenias."
    ),
)
async def faers_comparison() -> dict:
    """Return pre-computed FAERS product comparison data."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        data = get_faers_comparison()
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="FAERS comparison data file not found.",
        )
    except Exception as exc:
        logger.exception("Failed to load FAERS comparison data")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAERS comparison data: {exc}",
        )

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "product_profiles": data.get("product_profiles", {}),
        "comparison": data.get("comparison", {}),
        "metadata": data.get("metadata", {}),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/signals/triangulation -- Cross-source signal triangulation
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/signals/triangulation",
    tags=["Signals"],
    summary="Cross-source signal triangulation (FAERS vs ClinicalTrials.gov)",
    description=(
        "Compares FAERS spontaneous reporting rates with enrollment-weighted "
        "clinical trial AE rates from ClinicalTrials.gov. Flags divergences "
        "as aligned (<25%), moderate (25-75%), or significant (>75%). "
        "These flags are hypothesis-generating, not confirmatory."
    ),
)
async def signal_triangulation(
    ae_type: str | None = Query(
        None,
        description="Filter by AE type: crs, icans, infections, cytopenias. "
                    "Omit for all types.",
    ),
) -> dict:
    """Cross-reference FAERS and CT.gov AE rates."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        result = triangulate_signals(ae_type=ae_type)
    except Exception as exc:
        logger.exception("Signal triangulation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Signal triangulation failed: {exc}",
        )

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "signals": result["signals"],
        "summary": result["summary"],
        "methodology": result["methodology"],
        "caveats": result["caveats"],
    }


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
    # Build trial-level CRS/ICANS rate summaries from CT.gov data
    trial_summaries = get_ctgov_trial_summaries()
    trial_level = []
    for t in trial_summaries:
        rates = t.get("ae_rates", {})
        trial_level.append({
            "nct_id": t["nct_id"],
            "title": t["title"],
            "phase": t["phase"],
            "enrollment": t["enrollment"],
            "crs_rate_pct": rates.get("crs", {}).get("rate_pct", 0.0),
            "icans_rate_pct": rates.get("icans", {}).get("rate_pct", 0.0),
        })
    return {
        "comparison_data": get_comparison_chart_data(),
        "note": "SLE data from pooled analysis (n=47); oncology from pivotal trials",
        "trial_level_data": trial_level,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/trials/ae-data -- CT.gov trial-level AE data
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/trials/ae-data",
    tags=["Population"],
    summary="ClinicalTrials.gov adverse event data",
    description=(
        "Returns pre-extracted adverse event data from 47 completed CAR-T "
        "trials on ClinicalTrials.gov with computed CRS, ICANS, cytopenia, "
        "and infection rates."
    ),
)
async def trials_ae_data(
    ae_type: str | None = Query(
        default=None,
        description="Filter to a specific AE category (crs, icans, cytopenias, infections, hlh)",
    ),
    min_enrollment: int = Query(
        default=0,
        ge=0,
        description="Minimum trial enrollment to include",
    ),
) -> dict:
    """Return CT.gov trial AE data with optional filtering."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    summaries = get_ctgov_trial_summaries(min_enrollment=min_enrollment)
    ctgov_summary = get_ctgov_summary()

    # If ae_type specified, validate and filter to non-zero rates
    if ae_type is not None:
        ae_key = ae_type.lower().strip()
        if ae_key not in CTGOV_AE_TERM_MAP:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown ae_type '{ae_type}'. "
                       f"Valid: {list(CTGOV_AE_TERM_MAP.keys())}",
            )
        filtered = []
        for s in summaries:
            rate_info = s["ae_rates"].get(ae_key, {})
            if rate_info.get("affected", 0) > 0:
                filtered.append(s)
        summaries = filtered

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "total_trials": len(summaries),
        "summary": {
            "unique_serious_event_types": ctgov_summary.get("unique_serious_event_types", 0),
            "unique_other_event_types": ctgov_summary.get("unique_other_event_types", 0),
        },
        "trials": summaries,
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
    # H9 fix: Derive current_n dynamically from pooled data instead of hardcoding
    current_n = ADVERSE_EVENT_RATES[0].n_patients

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


# ===========================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ===========================================================================

def _classify_node_type(entity: str) -> str:
    """Classify a pathway node entity into a visual type category.

    This function uses keyword-based heuristics to assign a visual category
    to each node in a signaling pathway graph.  The categories drive
    dashboard rendering (icon shape, color) and are not used for any
    quantitative analysis.

    Heuristic approach:
        The entity name is checked against ordered keyword lists for each
        category: cell, receptor, kinase, process, biomarker.  The first
        matching category wins; if nothing matches the default is "cytokine".

    Known limitations:
        - Order-dependent: An entity matching keywords in multiple categories
          is assigned to whichever category appears first in the if-chain.
          For example, "STAT3_phosphorylation" would be classified as
          "kinase" (matching "STAT") rather than "process" (matching
          "phosphorylation") because the kinase check precedes the process
          check.
        - Fragile with new entities: Adding new pathway nodes requires
          verifying that existing keyword lists produce the correct
          classification.  There is no validation or unit test coverage
          for classification correctness.
        - Ideally, the node type should be stored as a field in the pathway
          data structure (``PathwayStep``) rather than inferred at render
          time from the entity name.  This is tracked as a future
          improvement (see team-of-critics-review.md, item M9).

    Args:
        entity: The pathway node entity name (e.g. "IL-6", "macrophage",
            "NF-kB_activation").

    Returns:
        One of: "cell", "receptor", "kinase", "process", "biomarker",
        or "cytokine" (default).
    """
    entity_lower = entity.lower()
    # Cells
    cell_keywords = [
        "cell", "monocyte", "macrophage", "neutrophil", "astrocyte",
        "pericyte", "endothelial", "nk_cell", "dendritic",
    ]
    if any(kw in entity_lower for kw in cell_keywords):
        return "cell"
    # Receptors and signaling
    receptor_keywords = [
        "receptor", "gp130", "tie2", "tnfr", "ifngr", "il-6r",
        "sil-6r", "nmda", "dimer",
    ]
    if any(kw in entity_lower for kw in receptor_keywords):
        return "receptor"
    # Kinases / transcription factors
    kinase_keywords = [
        "jak", "stat", "nf-kb", "nfkb", "kinase",
    ]
    if any(kw in entity_lower for kw in kinase_keywords):
        return "kinase"
    # Processes / clinical outcomes
    process_keywords = [
        "crs", "icans", "hlh", "mas", "coagulopathy",
        "hemophagocytosis", "permeability", "infiltration",
        "excitotoxicity", "expansion", "recruitment", "lysis",
        "gene", "transcrib", "apoptosis", "leak",
    ]
    if any(kw in entity_lower for kw in process_keywords):
        return "process"
    # Biomarkers
    biomarker_keywords = ["crp", "ferritin", "easix"]
    if any(kw in entity_lower for kw in biomarker_keywords):
        return "biomarker"
    # Default: cytokine / molecule
    return "cytokine"


def _pathway_to_response(pw) -> KnowledgePathwayResponse:
    """Convert a SignalingPathway dataclass to a KnowledgePathwayResponse."""
    # Build unique nodes from step sources and targets
    node_set: dict[str, str] = {}
    edges = []
    steps = []
    for step in pw.steps:
        if step.source not in node_set:
            node_set[step.source] = _classify_node_type(step.source)
        if step.target not in node_set:
            node_set[step.target] = _classify_node_type(step.target)
        edges.append(KnowledgePathwayEdge(
            source=step.source,
            target=step.target,
            relation=step.relation.value,
            mechanism=step.mechanism,
            confidence=step.confidence,
            is_feedback_loop=step.is_feedback_loop,
            intervention_point=step.intervention_point,
            references=list(step.references),
        ))
        steps.append(KnowledgePathwayStep(
            source=step.source,
            target=step.target,
            relation=step.relation.value,
            mechanism=step.mechanism,
            confidence=step.confidence,
            temporal_window=step.temporal_window.value,
            is_feedback_loop=step.is_feedback_loop,
            intervention_point=step.intervention_point,
            intervention_agents=list(step.intervention_agents),
            references=list(step.references),
        ))
    nodes = [
        KnowledgePathwayNode(id=name, label=name.replace("_", " "), node_type=ntype)
        for name, ntype in node_set.items()
    ]
    return KnowledgePathwayResponse(
        pathway_id=pw.pathway_id,
        name=pw.name,
        description=pw.description,
        nodes=nodes,
        edges=edges,
        steps=steps,
        entry_points=pw.entry_points,
        exit_points=pw.exit_points,
        feedback_loops=pw.feedback_loops,
        intervention_summary=pw.intervention_summary,
        ae_outcomes=pw.ae_outcomes,
        key_references=pw.key_references,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/pathways -- All signaling pathways
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/pathways",
    response_model=KnowledgePathwayListResponse,
    tags=["Knowledge"],
    summary="All signaling pathways as directed graphs",
    description=(
        "Returns all signaling pathways in the knowledge graph as directed "
        "graphs with nodes, edges, feedback loops, and intervention points."
    ),
)
async def knowledge_pathways() -> KnowledgePathwayListResponse:
    """Return all signaling pathways as directed graph data."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    pathways = [_pathway_to_response(pw) for pw in PATHWAY_REGISTRY.values()]
    return KnowledgePathwayListResponse(
        request_id=request_id,
        timestamp=now,
        pathways=pathways,
        total=len(pathways),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/pathways/{pathway_id} -- Single pathway detail
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/pathways/{pathway_id}",
    response_model=KnowledgePathwayResponse,
    tags=["Knowledge"],
    summary="Single pathway detail",
    description="Returns a single signaling pathway by ID with full graph data.",
)
async def knowledge_pathway_detail(pathway_id: str) -> KnowledgePathwayResponse:
    """Return a single pathway by ID."""
    # Support both "PW:IL6_TRANS_SIGNALING" and "IL6_TRANS_SIGNALING" forms
    lookup_id = pathway_id if pathway_id.startswith("PW:") else f"PW:{pathway_id}"
    pw = PATHWAY_REGISTRY.get(lookup_id)
    if pw is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pathway '{pathway_id}' not found. "
                   f"Available: {list(PATHWAY_REGISTRY.keys())}",
        )
    return _pathway_to_response(pw)


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/mechanisms -- All mechanism chains
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/mechanisms",
    response_model=KnowledgeMechanismListResponse,
    tags=["Knowledge"],
    summary="All AE mechanism chains",
    description=(
        "Returns all therapy-to-AE mechanism chains with steps, risk factors, "
        "branching points, and intervention opportunities."
    ),
)
async def knowledge_mechanisms() -> KnowledgeMechanismListResponse:
    """Return all mechanism chains."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    mechanisms = []
    for mech in MECHANISM_REGISTRY.values():
        steps = [
            KnowledgeMechanismStep(
                step_number=s.step_number,
                entity=s.entity,
                action=s.action,
                detail=s.detail,
                temporal_onset=s.temporal_onset,
                biomarkers=list(s.biomarkers),
                is_branching_point=s.is_branching_point,
                branches=list(s.branches),
                is_intervention_point=s.is_intervention_point,
                interventions=list(s.interventions),
            )
            for s in mech.steps
        ]
        mechanisms.append(KnowledgeMechanismResponse(
            mechanism_id=mech.mechanism_id,
            therapy_modality=mech.therapy_modality.value,
            ae_category=mech.ae_category.value,
            name=mech.name,
            description=mech.description,
            steps=steps,
            risk_factors=mech.risk_factors,
            severity_determinants=mech.severity_determinants,
            typical_onset=mech.typical_onset,
            typical_duration=mech.typical_duration,
            incidence_range=mech.incidence_range,
            mortality_rate=mech.mortality_rate,
            key_references=mech.key_references,
        ))

    return KnowledgeMechanismListResponse(
        request_id=request_id,
        timestamp=now,
        mechanisms=mechanisms,
        total=len(mechanisms),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/targets -- Molecular targets
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/targets",
    response_model=KnowledgeTargetListResponse,
    tags=["Knowledge"],
    summary="Molecular targets with modulators",
    description=(
        "Returns all molecular targets involved in cell therapy AE "
        "pathophysiology, including drugs/agents that modulate each target."
    ),
)
async def knowledge_targets() -> KnowledgeTargetListResponse:
    """Return all molecular targets."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    targets = []
    for t in MOLECULAR_TARGET_REGISTRY.values():
        modulators = [
            KnowledgeModulatorResponse(
                name=m.name,
                mechanism=m.mechanism,
                status=m.status.value,
                route=m.route,
                dose=m.dose,
                evidence_refs=list(m.evidence_refs),
            )
            for m in t.modulators
        ]
        targets.append(KnowledgeTargetResponse(
            target_id=t.target_id,
            name=t.name,
            gene_symbol=t.gene_symbol,
            category=t.category.value,
            pathways=list(t.pathways),
            normal_range=t.normal_range,
            ae_range=t.ae_range,
            clinical_relevance=t.clinical_relevance,
            modulators=modulators,
            upstream_of=list(t.upstream_of),
            downstream_of=list(t.downstream_of),
            biomarker_utility=t.biomarker_utility,
            references=list(t.references),
        ))

    return KnowledgeTargetListResponse(
        request_id=request_id,
        timestamp=now,
        targets=targets,
        total=len(targets),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/cells -- Cell type data
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/cells",
    response_model=KnowledgeCellTypeListResponse,
    tags=["Knowledge"],
    summary="Cell type data",
    description=(
        "Returns all cell populations involved in cell therapy AE pathogenesis, "
        "including activation states, surface markers, and roles in each AE type."
    ),
)
async def knowledge_cells() -> KnowledgeCellTypeListResponse:
    """Return all cell type definitions."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    cell_types = []
    for ct in CELL_TYPE_REGISTRY.values():
        states = [
            KnowledgeActivationState(
                name=s.name,
                description=s.description,
                triggers=list(s.triggers),
                secreted_factors=list(s.secreted_factors),
                surface_markers=list(s.surface_markers),
                functional_outcome=s.functional_outcome,
                references=list(s.references),
            )
            for s in ct.activation_states
        ]
        cell_types.append(KnowledgeCellTypeResponse(
            cell_id=ct.cell_id,
            name=ct.name,
            lineage=ct.lineage,
            tissue=ct.tissue,
            surface_markers=list(ct.surface_markers),
            activation_states=states,
            roles_in_ae=ct.roles_in_ae,
            secreted_factors_baseline=list(ct.secreted_factors_baseline),
            references=list(ct.references),
        ))

    return KnowledgeCellTypeListResponse(
        request_id=request_id,
        timestamp=now,
        cell_types=cell_types,
        total=len(cell_types),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/references -- Full citation database
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/references",
    response_model=KnowledgeReferenceListResponse,
    tags=["Knowledge"],
    summary="Full citation database",
    description=(
        "Returns all 22 PubMed references supporting the knowledge graph, "
        "with authors, journals, key findings, and evidence grades."
    ),
)
async def knowledge_references() -> KnowledgeReferenceListResponse:
    """Return the full reference database."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    refs = [
        KnowledgeReferenceResponse(
            pmid=r.pmid,
            first_author=r.first_author,
            year=r.year,
            journal=r.journal,
            title=r.title,
            doi=r.doi,
            key_finding=r.key_finding,
            evidence_grade=r.evidence_grade,
            tags=list(r.tags),
        )
        for r in REFERENCES.values()
    ]

    return KnowledgeReferenceListResponse(
        request_id=request_id,
        timestamp=now,
        references=refs,
        total=len(refs),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/knowledge/overview -- Summary stats
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/knowledge/overview",
    response_model=KnowledgeOverviewResponse,
    tags=["Knowledge"],
    summary="Knowledge graph overview",
    description=(
        "Returns summary statistics across the entire knowledge graph: "
        "counts of pathways, mechanisms, targets, cell types, and references."
    ),
)
async def knowledge_overview() -> KnowledgeOverviewResponse:
    """Return summary statistics for the knowledge graph."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    total_steps = sum(len(pw.steps) for pw in PATHWAY_REGISTRY.values())
    ae_types = set()
    for pw in PATHWAY_REGISTRY.values():
        ae_types.update(pw.ae_outcomes)
    for mech in MECHANISM_REGISTRY.values():
        ae_types.add(mech.ae_category.value)

    therapy_types = set()
    for mech in MECHANISM_REGISTRY.values():
        therapy_types.add(mech.therapy_modality.value)

    return KnowledgeOverviewResponse(
        request_id=request_id,
        timestamp=now,
        pathway_count=len(PATHWAY_REGISTRY),
        pathway_names=[pw.name for pw in PATHWAY_REGISTRY.values()],
        total_pathway_steps=total_steps,
        mechanism_count=len(MECHANISM_REGISTRY),
        mechanism_names=[m.name for m in MECHANISM_REGISTRY.values()],
        target_count=len(MOLECULAR_TARGET_REGISTRY),
        druggable_target_count=len(get_druggable_targets()),
        cell_type_count=len(CELL_TYPE_REGISTRY),
        reference_count=len(REFERENCES),
        ae_types_covered=sorted(ae_types),
        therapy_types_covered=sorted(therapy_types),
    )


# ===========================================================================
# PUBLICATION ANALYSIS ENDPOINTS
# ===========================================================================

# Locate the analysis results JSON once at module load
_ANALYSIS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "analysis"
_RESULTS_DIR = _ANALYSIS_DIR / "results"
_ANALYSIS_JSON_PATH = _RESULTS_DIR / "analysis_results.json"

# Cache loaded analysis data
_analysis_cache: dict[str, Any] | None = None


def _load_analysis_json() -> dict[str, Any]:
    """Load and cache the analysis_results.json file."""
    global _analysis_cache
    if _analysis_cache is not None:
        return _analysis_cache
    if not _ANALYSIS_JSON_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Analysis results not found at {_ANALYSIS_JSON_PATH}",
        )
    with open(_ANALYSIS_JSON_PATH, "r", encoding="utf-8") as f:
        _analysis_cache = json.load(f)
    return _analysis_cache


def _build_demographics() -> list[PublicationDemographicRow]:
    """Build demographics table rows from the analysis data."""
    return [
        PublicationDemographicRow(indication="SLE", trial="Mackensen et al. 2022", product="Anti-CD19 CAR-T (MB-CART19)", n=5, target="CD19", year=2022),
        PublicationDemographicRow(indication="SLE", trial="Muller et al. 2024", product="Anti-CD19 CAR-T", n=15, target="CD19", year=2024),
        PublicationDemographicRow(indication="SLE", trial="CASTLE 2025", product="Anti-CD19 CAR-T (YTB323)", n=8, target="CD19", year=2025),
        PublicationDemographicRow(indication="SLE", trial="BCMA-CD19 cCAR SLE", product="BCMA-CD19 cCAR", n=7, target="CD19", year=2024),
        PublicationDemographicRow(indication="SLE", trial="Co-infusion SLE", product="CD19/BCMA co-infusion", n=6, target="CD19", year=2024),
        PublicationDemographicRow(indication="SLE", trial="Cabaletta RESET-SLE", product="CABA-201 (desar-cel)", n=4, target="Dual", year=2024),
        PublicationDemographicRow(indication="SLE", trial="BMS Breakfree-1", product="Anti-CD19 CAR-T", n=2, target="CD19", year=2025),
        PublicationDemographicRow(indication="DLBCL", trial="ZUMA-1", product="Axi-cel (Yescarta)", n=101, target="CD19", year=2017),
        PublicationDemographicRow(indication="DLBCL", trial="JULIET", product="Tisa-cel (Kymriah)", n=111, target="CD19", year=2019),
        PublicationDemographicRow(indication="DLBCL", trial="TRANSCEND", product="Liso-cel (Breyanzi)", n=269, target="CD19", year=2020),
        PublicationDemographicRow(indication="ALL", trial="ELIANA", product="Tisa-cel (Kymriah)", n=75, target="CD19", year=2018),
        PublicationDemographicRow(indication="MM", trial="KarMMa", product="Ide-cel (Abecma)", n=128, target="Dual", year=2021),
        PublicationDemographicRow(indication="MM", trial="CARTITUDE-1", product="Cilta-cel (Carvykti)", n=97, target="Dual", year=2021),
    ]


def _build_ae_rates() -> list[PublicationAERateRow]:
    """Build AE rates table rows."""
    return [
        PublicationAERateRow(indication="SLE", n=47, crs_any="55.2 (40.1-69.8)", crs_g3="0.0 (0.0-6.2)", icans_any="0.0 (0.0-6.2)", icans_g3="0.0 (0.0-6.2)"),
        PublicationAERateRow(indication="DLBCL", n=481, crs_any="56.4 (51.8-60.8)", crs_g3="7.1 (4.9-9.7)", icans_any="35.1 (30.9-39.6)", icans_g3="14.2 (11.2-17.6)"),
        PublicationAERateRow(indication="ALL", n=75, crs_any="77.0 (66.2-86.2)", crs_g3="48.0 (36.3-59.9)", icans_any="40.0 (28.9-52.0)", icans_g3="13.0 (6.6-23.2)"),
        PublicationAERateRow(indication="MM", n=225, crs_any="91.6 (87.1-94.8)", crs_g3="5.7 (3.1-9.7)", icans_any="31.8 (26.0-38.5)", icans_g3="6.6 (3.8-10.8)"),
    ]


def _build_limitations() -> list[str]:
    """Return the list of analysis limitations."""
    return [
        "Small sample sizes in SLE trials (n=2-15 per study)",
        "Early-phase data; mature follow-up not yet available",
        "Heterogeneous CAR-T constructs across SLE trials",
        "No head-to-head randomized comparisons across indications",
        "Oncology comparator data from different eras (2017-2021 vs 2022-2025)",
        "CRS/ICANS grading may not be fully comparable across institutions",
        "Kaplan-Meier analysis uses synthetic onset times (not individual patient data)",
        "Publication bias cannot be fully assessed with available studies",
    ]


def _build_forest_plot_data(ae_type: str, data: dict) -> list[PublicationForestPlotData]:
    """Build forest plot data for a given AE type."""
    if ae_type == "crs_any":
        groups = [
            PublicationForestPlotData(indication="SLE", studies=[
                PublicationStudyData(name="Mackensen et al. 2022", rate_pct=60.0, ci_low_pct=23.1, ci_high_pct=88.2, n=5, events=3),
                PublicationStudyData(name="Muller et al. 2024", rate_pct=53.0, ci_low_pct=30.1, ci_high_pct=75.2, n=15, events=8),
                PublicationStudyData(name="CASTLE 2025", rate_pct=50.0, ci_low_pct=21.5, ci_high_pct=78.5, n=8, events=4),
                PublicationStudyData(name="BCMA-CD19 cCAR SLE", rate_pct=57.0, ci_low_pct=25.0, ci_high_pct=84.2, n=7, events=4),
                PublicationStudyData(name="Co-infusion SLE", rate_pct=67.0, ci_low_pct=30.0, ci_high_pct=90.3, n=6, events=4),
                PublicationStudyData(name="Cabaletta RESET-SLE", rate_pct=50.0, ci_low_pct=15.0, ci_high_pct=85.0, n=4, events=2),
                PublicationStudyData(name="BMS Breakfree-1", rate_pct=50.0, ci_low_pct=9.5, ci_high_pct=90.5, n=2, events=1),
                PublicationStudyData(name="SLE Pooled", rate_pct=55.2, ci_low_pct=40.1, ci_high_pct=69.8, n=47, events=26, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="DLBCL", studies=[
                PublicationStudyData(name="ZUMA-1", rate_pct=93.0, ci_low_pct=86.4, ci_high_pct=96.6, n=101, events=94),
                PublicationStudyData(name="JULIET", rate_pct=58.0, ci_low_pct=48.4, ci_high_pct=66.4, n=111, events=64),
                PublicationStudyData(name="TRANSCEND", rate_pct=42.0, ci_low_pct=36.3, ci_high_pct=48.0, n=269, events=113),
                PublicationStudyData(name="DLBCL Pooled", rate_pct=56.4, ci_low_pct=51.8, ci_high_pct=60.8, n=481, events=271, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="ALL", studies=[
                PublicationStudyData(name="ELIANA", rate_pct=77.0, ci_low_pct=66.7, ci_high_pct=85.3, n=75, events=58),
                PublicationStudyData(name="ALL Pooled", rate_pct=77.0, ci_low_pct=66.2, ci_high_pct=86.2, n=75, events=58, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="MM", studies=[
                PublicationStudyData(name="KarMMa", rate_pct=89.0, ci_low_pct=82.5, ci_high_pct=93.4, n=128, events=114),
                PublicationStudyData(name="CARTITUDE-1", rate_pct=95.0, ci_low_pct=88.5, ci_high_pct=97.8, n=97, events=92),
                PublicationStudyData(name="MM Pooled", rate_pct=91.6, ci_low_pct=87.1, ci_high_pct=94.8, n=225, events=206, is_pooled=True),
            ]),
        ]
    elif ae_type == "crs_g3":
        groups = [
            PublicationForestPlotData(indication="SLE", studies=[
                PublicationStudyData(name="Mackensen et al. 2022", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=43.4, n=5, events=0),
                PublicationStudyData(name="Muller et al. 2024", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=20.4, n=15, events=0),
                PublicationStudyData(name="CASTLE 2025", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=32.4, n=8, events=0),
                PublicationStudyData(name="BCMA-CD19 cCAR SLE", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=35.4, n=7, events=0),
                PublicationStudyData(name="Co-infusion SLE", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=39.0, n=6, events=0),
                PublicationStudyData(name="Cabaletta RESET-SLE", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=49.0, n=4, events=0),
                PublicationStudyData(name="BMS Breakfree-1", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=65.8, n=2, events=0),
                PublicationStudyData(name="SLE Pooled", rate_pct=0.0, ci_low_pct=0.0, ci_high_pct=6.2, n=47, events=0, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="DLBCL", studies=[
                PublicationStudyData(name="ZUMA-1", rate_pct=13.0, ci_low_pct=7.7, ci_high_pct=20.8, n=101, events=13),
                PublicationStudyData(name="JULIET", rate_pct=14.0, ci_low_pct=9.1, ci_high_pct=22.1, n=111, events=16),
                PublicationStudyData(name="TRANSCEND", rate_pct=2.0, ci_low_pct=0.8, ci_high_pct=4.3, n=269, events=5),
                PublicationStudyData(name="DLBCL Pooled", rate_pct=7.1, ci_low_pct=4.9, ci_high_pct=9.7, n=481, events=34, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="ALL", studies=[
                PublicationStudyData(name="ELIANA", rate_pct=48.0, ci_low_pct=37.1, ci_high_pct=59.1, n=75, events=36),
                PublicationStudyData(name="ALL Pooled", rate_pct=48.0, ci_low_pct=36.3, ci_high_pct=59.9, n=75, events=36, is_pooled=True),
            ]),
            PublicationForestPlotData(indication="MM", studies=[
                PublicationStudyData(name="KarMMa", rate_pct=7.0, ci_low_pct=3.7, ci_high_pct=12.8, n=128, events=9),
                PublicationStudyData(name="CARTITUDE-1", rate_pct=4.0, ci_low_pct=1.6, ci_high_pct=10.1, n=97, events=4),
                PublicationStudyData(name="MM Pooled", rate_pct=5.7, ci_low_pct=3.1, ci_high_pct=9.7, n=225, events=13, is_pooled=True),
            ]),
        ]
    else:
        groups = []
    return groups


@router.get(
    "/api/v1/publication/analysis",
    response_model=PublicationAnalysisResponse,
    tags=["Publication"],
    summary="Publication analysis results",
    description=(
        "Returns the complete publication analysis results including model "
        "comparisons, cross-validation, prior comparison, evidence accrual, "
        "pairwise comparisons, demographics, AE rates, and references."
    ),
)
async def publication_analysis() -> PublicationAnalysisResponse:
    """Return full publication analysis results."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    data = _load_analysis_json()

    # Model results
    model_results = []
    method_types = {
        "Bayesian Beta-Binomial (Jeffreys)": "Bayesian",
        "Clopper-Pearson Exact": "Frequentist",
        "Wilson Score": "Frequentist",
        "DerSimonian-Laird Random Effects": "Meta-analytic",
        "Empirical Bayes Shrinkage": "Empirical Bayes",
        "Kaplan-Meier": "Time-to-event",
        "Predictive Posterior (n=50)": "Bayesian predictive",
    }
    for model_name, mr in data["model_results"].items():
        model_results.append(PublicationModelResult(
            model_name=model_name,
            estimate_pct=round(mr["estimate_pct"], 2),
            ci_low_pct=round(mr["ci_low_pct"], 2),
            ci_high_pct=round(mr["ci_high_pct"], 2),
            ci_width_pct=round(mr["ci_width_pct"], 2),
            method_type=method_types.get(model_name, mr.get("method", "Unknown")),
        ))

    # Cross-validation
    cross_validation = [
        PublicationCrossValidation(
            model=cv["model"],
            rmse_pct=round(cv["rmse_pct"], 2),
            mae_pct=round(cv["mae_pct"], 2),
            coverage=cv["coverage"],
            n_folds=cv["n_folds"],
        )
        for cv in data["cross_validation_summary"]
    ]

    # Prior comparison
    prior_comparison = []
    for strategy, pc in data["prior_comparison"].items():
        prior_comparison.append(PublicationPriorComparison(
            strategy=strategy,
            prior_alpha=round(pc["prior"]["alpha"], 4),
            prior_beta=round(pc["prior"]["beta"], 4),
            posterior_mean_pct=round(pc["posterior_mean_pct"], 4),
            ci_low_pct=round(pc["ci_low_pct"], 4),
            ci_high_pct=round(pc["ci_high_pct"], 4),
            ci_width_pct=round(pc["ci_width_pct"], 4),
        ))

    # Pairwise comparisons
    pairwise = []
    for ae_type, comparisons in data["pairwise_comparisons"].items():
        for comp_name, comp in comparisons.items():
            pairwise.append(PublicationPairwiseComparison(
                comparison=comp_name,
                ae_type=ae_type,
                sle_rate_pct=comp["sle_rate_pct"],
                comparator_rate_pct=comp["comparator_rate_pct"],
                difference_pp=comp["difference_pp"],
                p_value=comp["p_value"],
                significant=comp["significant_at_005"] == "True",
            ))

    # Heterogeneity
    heterogeneity = []
    for ae_type, het in data["heterogeneity"].items():
        heterogeneity.append(PublicationHeterogeneity(
            ae_type=ae_type,
            i_squared=round(het["i_squared"], 4),
            cochran_q=round(het["cochran_q"], 2),
            tau_squared=round(het["tau_squared"], 6),
            n_studies=het["n_studies"],
            q_pvalue=het["q_pvalue"],
        ))

    # Evidence accrual
    ea_crs = [
        PublicationEvidenceAccrualPoint(
            timepoint=p["timepoint"], year=p["year"],
            n_cumulative=p["n_cumulative"], events_cumulative=p["events_cumulative"],
            posterior_mean_pct=round(p["posterior_mean_pct"], 4),
            ci_low_pct=round(p["ci_low_pct"], 4),
            ci_high_pct=round(p["ci_high_pct"], 4),
            ci_width_pct=round(p["ci_width_pct"], 4),
            is_projected=p["is_projected"],
        )
        for p in data["evidence_accrual"]["CRS_grade3plus"]
    ]
    ea_icans = [
        PublicationEvidenceAccrualPoint(
            timepoint=p["timepoint"], year=p["year"],
            n_cumulative=p["n_cumulative"], events_cumulative=p["events_cumulative"],
            posterior_mean_pct=round(p["posterior_mean_pct"], 4),
            ci_low_pct=round(p["ci_low_pct"], 4),
            ci_high_pct=round(p["ci_high_pct"], 4),
            ci_width_pct=round(p["ci_width_pct"], 4),
            is_projected=p["is_projected"],
        )
        for p in data["evidence_accrual"]["ICANS_grade3plus"]
    ]

    # References
    references = [
        PublicationReference(pmid="22158166", citation="Di Stasi et al., N Engl J Med 2011"),
        PublicationReference(pmid="25389405", citation="Di Stasi et al., Front Pharmacol 2014"),
        PublicationReference(pmid="27455965", citation="Teachey et al., Cancer Discov 2016"),
        PublicationReference(pmid="28854140", citation="Fitzgerald et al., Crit Care Med 2017"),
        PublicationReference(pmid="29025771", citation="Gust et al., Cancer Discov 2017"),
        PublicationReference(pmid="29084955", citation="Neelapu et al., Nat Rev Clin Oncol 2018"),
        PublicationReference(pmid="29643511", citation="Giavridis et al., Nat Med 2018"),
        PublicationReference(pmid="29643512", citation="Norelli et al., Nat Med 2018"),
        PublicationReference(pmid="30154262", citation="Santomasso et al., Cancer Discov 2018"),
        PublicationReference(pmid="30275568", citation="Lee et al., Biol Blood Marrow Transplant 2019"),
        PublicationReference(pmid="30442748", citation="Frey et al., Blood Adv 2019"),
        PublicationReference(pmid="31204436", citation="Gust et al., Blood Adv 2019"),
        PublicationReference(pmid="32433173", citation="Liu et al., N Engl J Med 2020"),
        PublicationReference(pmid="32666058", citation="Le et al., Drug Des Devel Ther 2020"),
        PublicationReference(pmid="33082430", citation="Parker et al., Blood 2020"),
        PublicationReference(pmid="33168950", citation="Kang et al., Leukemia 2021"),
        PublicationReference(pmid="34263927", citation="Lichtenstein et al., J Clin Invest 2021"),
        PublicationReference(pmid="34265098", citation="Sandler et al., Leuk Lymphoma 2021"),
        PublicationReference(pmid="36906275", citation="Hines et al., Transplant Cell Ther 2023"),
        PublicationReference(pmid="37271625", citation="Strati et al., Blood Adv 2023"),
        PublicationReference(pmid="37798640", citation="Morris et al., Int J Mol Sci 2024"),
        PublicationReference(pmid="37828045", citation="Sterner et al., Cell Rep Med 2023"),
        PublicationReference(pmid="38123583", citation="Butt et al., Nat Commun 2024"),
        PublicationReference(pmid="38368579", citation="Zhang et al., Exp Hematol Oncol 2024"),
        PublicationReference(pmid="39134524", citation="Khurana et al., Blood Cancer J 2024"),
        PublicationReference(pmid="39256221", citation="Luft et al., Blood 2024"),
        PublicationReference(pmid="39277881", citation="Tomasik et al., Arch Immunol Ther Exp 2024"),
        PublicationReference(pmid="39338775", citation="Chen et al., J Hematol Oncol 2024"),
        PublicationReference(pmid="39352714", citation="Liu et al., J Transl Med 2024"),
    ]

    key_findings = {
        "sle_crs_any_pct": 55.2,
        "sle_crs_g3_pct": 0.0,
        "sle_icans_any_pct": 0.0,
        "sle_icans_g3_pct": 0.0,
        "sle_n_patients": 47,
        "sle_n_trials": 7,
        "total_patients": 828,
        "total_studies": 13,
        "crs_g3_bayesian_estimate": 1.04,
        "crs_g3_bayesian_ci": [0.0, 5.18],
        "mechanistic_ci_narrowing_pct": 36.9,
        "model_agreement": "All 7 models converge on low severe CRS rate (1-4%)",
    }

    return PublicationAnalysisResponse(
        request_id=request_id,
        timestamp=now,
        data_summary=data["data_summary"],
        model_results=model_results,
        cross_validation=cross_validation,
        prior_comparison=prior_comparison,
        pairwise_comparisons=pairwise,
        heterogeneity=heterogeneity,
        ae_rates=_build_ae_rates(),
        demographics=_build_demographics(),
        evidence_accrual_crs=ea_crs,
        evidence_accrual_icans=ea_icans,
        limitations=_build_limitations(),
        references=references,
        key_findings=key_findings,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/publication/figures/{figure_name} -- Figure data
# ---------------------------------------------------------------------------

_VALID_FIGURES = {
    "forest_crs_any": "Figure 1: Forest Plot of CRS Any Grade Rates",
    "forest_crs_g3": "Figure 1b: Forest Plot of CRS Grade >= 3 Rates",
    "evidence_accrual": "Figure 2: Evidence Accrual Curve",
    "prior_comparison": "Figure 3: Mechanistic vs Uninformative Prior Comparison",
    "calibration": "Figure 4: Model Calibration Comparison (LOO-CV)",
}


@router.get(
    "/api/v1/publication/figures/{figure_name}",
    response_model=PublicationFigureResponse,
    tags=["Publication"],
    summary="Publication figure data",
    description=(
        "Returns structured data for a specific publication figure. "
        "Valid figure names: forest_crs_any, forest_crs_g3, evidence_accrual, "
        "prior_comparison, calibration."
    ),
)
async def publication_figure(figure_name: str) -> PublicationFigureResponse:
    """Return data for a specific publication figure."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if figure_name not in _VALID_FIGURES:
        raise HTTPException(
            status_code=404,
            detail=f"Figure '{figure_name}' not found. "
                   f"Valid figures: {list(_VALID_FIGURES.keys())}",
        )

    data = _load_analysis_json()
    figure_title = _VALID_FIGURES[figure_name]

    if figure_name in ("forest_crs_any", "forest_crs_g3"):
        ae_type = "crs_any" if figure_name == "forest_crs_any" else "crs_g3"
        figure_data = [g.model_dump() for g in _build_forest_plot_data(ae_type, data)]
    elif figure_name == "evidence_accrual":
        figure_data = {
            "CRS_grade3plus": data["evidence_accrual"]["CRS_grade3plus"],
            "ICANS_grade3plus": data["evidence_accrual"]["ICANS_grade3plus"],
        }
    elif figure_name == "prior_comparison":
        figure_data = data["prior_comparison"]
    elif figure_name == "calibration":
        figure_data = data["cross_validation_summary"]
    else:
        figure_data = {}

    return PublicationFigureResponse(
        request_id=request_id,
        timestamp=now,
        figure_name=figure_name,
        figure_title=figure_title,
        data=figure_data,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/system/architecture -- System architecture metadata
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/system/architecture",
    response_model=ArchitectureResponse,
    tags=["System"],
    summary="System architecture metadata",
    description=(
        "Returns structured metadata about the platform's architecture: "
        "source modules, dependency graph, API endpoints, model registry, "
        "test summary, and system health."
    ),
)
async def system_architecture() -> ArchitectureResponse:
    """Return system architecture as structured data for visualization."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # --- Modules ---
    modules = [
        ModuleInfo(
            name="bayesian_risk",
            path="src/models/bayesian_risk.py",
            description="Beta-Binomial posteriors, evidence accrual, stopping boundaries",
            public_functions=[
                "compute_posterior", "compute_evidence_accrual",
                "compute_stopping_boundaries",
            ],
            classes=["PriorSpec", "PosteriorEstimate", "StudyDataPoint"],
            lines_of_code=378,
        ),
        ModuleInfo(
            name="mitigation_model",
            path="src/models/mitigation_model.py",
            description="Correlated RR combination, Monte Carlo uncertainty propagation",
            public_functions=[
                "combine_correlated_rr", "combine_multiple_rrs",
                "monte_carlo_mitigated_risk", "calculate_mitigated_risk",
                "get_mitigation_correlation",
            ],
            classes=["MitigationStrategy", "MitigationResult"],
            lines_of_code=545,
        ),
        ModuleInfo(
            name="faers_signal",
            path="src/models/faers_signal.py",
            description="FAERS disproportionality analysis (PRR, ROR, EBGM) via openFDA",
            public_functions=[
                "compute_prr", "compute_ror", "compute_ebgm",
                "classify_signal", "get_faers_signals", "get_faers_summary",
            ],
            classes=["FAERSSignal", "FAERSSummary"],
            lines_of_code=935,
        ),
        ModuleInfo(
            name="model_registry",
            path="src/models/model_registry.py",
            description="7-model risk estimation registry with unified interface",
            public_functions=[
                "estimate_risk", "compare_models", "list_models",
                "bayesian_beta_binomial", "frequentist_exact",
                "wilson_score", "random_effects_meta",
                "empirical_bayes", "kaplan_meier", "predictive_posterior",
            ],
            classes=["RiskModel"],
            lines_of_code=917,
        ),
        ModuleInfo(
            name="model_validation",
            path="src/models/model_validation.py",
            description="Calibration diagnostics, scoring rules, coverage, cross-validation",
            public_functions=[
                "calibration_check", "brier_score", "coverage_probability",
                "leave_one_out_cv", "model_comparison",
                "sequential_prediction_test",
            ],
            classes=[],
            lines_of_code=480,
        ),
        ModuleInfo(
            name="biomarker_scores",
            path="src/models/biomarker_scores.py",
            description="Deterministic clinical scoring models (EASIX, HScore, CAR-HEMATOTOX, etc.)",
            public_functions=[],
            classes=[
                "EASIX", "ModifiedEASIX", "PreModifiedEASIX",
                "HScore", "CARHematotox",
                "TeacheyCytokineModel", "HayBinaryClassifier",
                "RiskLevel", "ScoringResult",
            ],
            lines_of_code=1444,
        ),
        ModuleInfo(
            name="ensemble_runner",
            path="src/models/ensemble_runner.py",
            description="Two-layer biomarker scoring ensemble with risk aggregation",
            public_functions=[],
            classes=["BiomarkerEnsembleRunner", "EnsembleResult", "LayerResult"],
            lines_of_code=378,
        ),
        ModuleInfo(
            name="app",
            path="src/api/app.py",
            description="FastAPI application with patient-level endpoints",
            public_functions=[
                "predict", "predict_batch", "get_timeline",
                "get_model_status", "compute_easix", "compute_hscore",
                "compute_car_hematotox", "health_check",
            ],
            classes=[],
            lines_of_code=1096,
        ),
        ModuleInfo(
            name="population_routes",
            path="src/api/population_routes.py",
            description="Population-level API routes (Bayesian, mitigation, trials, FAERS, CDP)",
            public_functions=[
                "population_risk", "bayesian_posterior",
                "mitigation_analysis", "evidence_accrual",
                "trial_registry", "faers_signals",
                "list_mitigations", "ae_comparison",
                "list_therapies", "cdp_monitoring_schedule",
                "cdp_eligibility_criteria", "cdp_stopping_rules",
                "cdp_sample_size", "system_architecture",
            ],
            classes=[],
            lines_of_code=1100,
        ),
        ModuleInfo(
            name="schemas",
            path="src/api/schemas.py",
            description="Pydantic request/response models for all API endpoints",
            public_functions=[],
            classes=[
                "LabValues", "VitalSigns", "Demographics",
                "ClinicalContext", "ProductInfo", "PatientDataRequest",
                "BatchPredictionRequest", "ScoreDetail", "LayerDetail",
                "PredictionResponse", "BatchPredictionResponse",
                "TimelinePoint", "TimelineResponse", "ModelInfo",
                "ModelStatusResponse", "ScoreResponse", "ErrorResponse",
                "HealthResponse", "BayesianPosteriorRequest",
                "PosteriorEstimateResponse", "BayesianPosteriorResponse",
                "MitigationAnalysisRequest", "MitigationAnalysisResponse",
                "EvidenceAccrualResponse", "TrialSummaryResponse",
                "PopulationRiskResponse", "FAERSSummaryResponse",
                "ArchitectureResponse",
            ],
            lines_of_code=650,
        ),
        ModuleInfo(
            name="middleware",
            path="src/api/middleware.py",
            description="Request timing, API key auth, rate limiting, error handling",
            public_functions=[],
            classes=[
                "RequestTimingMiddleware", "APIKeyMiddleware",
                "RateLimitMiddleware", "ErrorHandlingMiddleware",
            ],
            lines_of_code=257,
        ),
        ModuleInfo(
            name="knowledge_graph",
            path="src/data/graph/knowledge_graph.py",
            description="In-memory biological pathway graph with optional Neo4j backend",
            public_functions=[],
            classes=["KnowledgeGraph"],
            lines_of_code=400,
        ),
        ModuleInfo(
            name="sle_cart_studies",
            path="data/sle_cart_studies.py",
            description="Curated SLE CAR-T clinical trial data and AE rates",
            public_functions=[
                "get_sle_baseline_risk", "get_trial_summary",
                "get_comparison_chart_data",
            ],
            classes=[],
            lines_of_code=400,
        ),
        ModuleInfo(
            name="cell_therapy_registry",
            path="data/cell_therapy_registry.py",
            description="Cell therapy type registry and AE taxonomy",
            public_functions=[],
            classes=["TherapyType", "AETaxonomy"],
            lines_of_code=300,
        ),
    ]

    # --- Dependencies (adjacency list) ---
    dependencies = [
        DependencyEdge(
            source="app", target="schemas",
            import_names=["PatientDataRequest", "PredictionResponse", "HealthResponse"],
        ),
        DependencyEdge(
            source="app", target="biomarker_scores",
            import_names=["EASIX", "HScore", "CARHematotox", "RiskLevel"],
        ),
        DependencyEdge(
            source="app", target="ensemble_runner",
            import_names=["BiomarkerEnsembleRunner"],
        ),
        DependencyEdge(
            source="app", target="middleware",
            import_names=["APIKeyMiddleware", "RateLimitMiddleware",
                          "RequestTimingMiddleware", "ErrorHandlingMiddleware"],
        ),
        DependencyEdge(
            source="app", target="population_routes",
            import_names=["router"],
        ),
        DependencyEdge(
            source="population_routes", target="schemas",
            import_names=["BayesianPosteriorRequest", "MitigationAnalysisRequest",
                          "ArchitectureResponse"],
        ),
        DependencyEdge(
            source="population_routes", target="bayesian_risk",
            import_names=["compute_posterior", "compute_evidence_accrual",
                          "CRS_PRIOR", "ICANS_PRIOR"],
        ),
        DependencyEdge(
            source="population_routes", target="mitigation_model",
            import_names=["MITIGATION_STRATEGIES", "calculate_mitigated_risk",
                          "combine_multiple_rrs"],
        ),
        DependencyEdge(
            source="population_routes", target="faers_signal",
            import_names=["get_faers_signals"],
        ),
        DependencyEdge(
            source="population_routes", target="sle_cart_studies",
            import_names=["CLINICAL_TRIALS", "get_sle_baseline_risk",
                          "get_trial_summary"],
        ),
        DependencyEdge(
            source="population_routes", target="cell_therapy_registry",
            import_names=["THERAPY_TYPES"],
        ),
        DependencyEdge(
            source="ensemble_runner", target="biomarker_scores",
            import_names=["EASIX", "ModifiedEASIX", "HScore", "CARHematotox",
                          "TeacheyCytokineModel", "HayBinaryClassifier"],
        ),
        DependencyEdge(
            source="model_registry", target="bayesian_risk",
            import_names=["PriorSpec", "compute_posterior"],
        ),
    ]

    # --- Endpoints ---
    endpoints = [
        EndpointInfo(
            method="POST", path="/api/v1/predict",
            summary="Run ensemble prediction for a patient",
            tags=["Prediction"],
            request_schema="PatientDataRequest",
            response_schema="PredictionResponse",
        ),
        EndpointInfo(
            method="POST", path="/api/v1/predict/batch",
            summary="Batch prediction for multiple patients",
            tags=["Prediction"],
            request_schema="BatchPredictionRequest",
            response_schema="BatchPredictionResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/patient/{patient_id}/timeline",
            summary="Get risk timeline for a patient",
            tags=["Timeline"],
            response_schema="TimelineResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/models/status",
            summary="Model availability and status",
            tags=["Models"],
            response_schema="ModelStatusResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/scores/easix",
            summary="Compute EASIX score",
            tags=["Individual Scores"],
            response_schema="ScoreResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/scores/hscore",
            summary="Compute HScore",
            tags=["Individual Scores"],
            response_schema="ScoreResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/scores/car-hematotox",
            summary="Compute CAR-HEMATOTOX score",
            tags=["Individual Scores"],
            response_schema="ScoreResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/health",
            summary="Health check",
            tags=["System"],
            response_schema="HealthResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/population/risk",
            summary="SLE CAR-T baseline risk summary",
            tags=["Population"],
            response_schema="PopulationRiskResponse",
        ),
        EndpointInfo(
            method="POST", path="/api/v1/population/bayesian",
            summary="Compute Bayesian posterior for AE rate",
            tags=["Population"],
            request_schema="BayesianPosteriorRequest",
            response_schema="BayesianPosteriorResponse",
        ),
        EndpointInfo(
            method="POST", path="/api/v1/population/mitigations",
            summary="Correlated mitigation risk analysis",
            tags=["Population"],
            request_schema="MitigationAnalysisRequest",
            response_schema="MitigationAnalysisResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/population/evidence-accrual",
            summary="Evidence accrual timeline",
            tags=["Population"],
            response_schema="EvidenceAccrualResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/population/trials",
            summary="CAR-T clinical trial registry",
            tags=["Population"],
            response_schema="TrialSummaryResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/signals/faers",
            summary="FAERS signal detection for CAR-T products",
            tags=["Signals"],
            response_schema="FAERSSummaryResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/signals/faers/comparison",
            summary="Pre-computed FAERS product comparison",
            tags=["Signals"],
        ),
        EndpointInfo(
            method="GET", path="/api/v1/population/mitigations/strategies",
            summary="List available mitigation strategies",
            tags=["Population"],
        ),
        EndpointInfo(
            method="GET", path="/api/v1/population/comparison",
            summary="Cross-indication AE rate comparison",
            tags=["Population"],
        ),
        EndpointInfo(
            method="GET", path="/api/v1/therapies",
            summary="List available therapy types",
            tags=["Population"],
            response_schema="TherapyListResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/cdp/monitoring-schedule",
            summary="CDP monitoring schedule",
            tags=["Population"],
            response_schema="MonitoringScheduleResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/cdp/eligibility-criteria",
            summary="CDP eligibility criteria",
            tags=["Population"],
            response_schema="EligibilityCriteriaResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/cdp/stopping-rules",
            summary="CDP Bayesian stopping rules",
            tags=["Population"],
            response_schema="StoppingRulesResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/cdp/sample-size",
            summary="CDP sample size considerations",
            tags=["Population"],
            response_schema="SampleSizeResponse",
        ),
        EndpointInfo(
            method="GET", path="/api/v1/system/architecture",
            summary="System architecture metadata",
            tags=["System"],
            response_schema="ArchitectureResponse",
        ),
        EndpointInfo(
            method="WS", path="/ws/monitor/{patient_id}",
            summary="Real-time patient monitoring via WebSocket",
            tags=["WebSocket"],
        ),
    ]

    # --- Registry models ---
    registry_models = [
        RegistryModelInfo(
            id=m.id,
            name=m.name,
            description=m.description,
            suitable_for=m.suitable_for,
            requires=m.requires,
        )
        for m in _mr.values()
    ]

    # --- Test summary ---
    # H9 fix: Dynamically discover test counts from the filesystem rather
    # than hardcoding stale values.  Falls back to 0 on error.
    _test_total, _test_files, _unit, _integ = _count_tests()
    test_summary = TestSummary(
        total_tests=_test_total,
        test_files=_test_files,
        unit_tests=_unit,
        integration_tests=_integ,
        other_tests=max(0, _test_total - _unit - _integ),
    )

    # --- System health ---
    # NOTE: This import must remain in-function to avoid a circular import.
    # app.py imports population_routes (for the router), so importing app
    # at module level here would create a cycle.
    from src.api.app import _start_time  # noqa: E402 — circular import guard
    uptime = _time.monotonic() - _start_time if _start_time > 0 else 0.0

    system_health = SystemHealthInfo(
        models_loaded=7,
        api_version="0.1.0",
        uptime_seconds=round(uptime, 2),
        test_count=_test_total,
        total_endpoints=len(endpoints),
        total_modules=len(modules),
    )

    return ArchitectureResponse(
        request_id=request_id,
        timestamp=now,
        modules=modules,
        dependencies=dependencies,
        endpoints=endpoints,
        registry_models=registry_models,
        test_summary=test_summary,
        system_health=system_health,
    )


# ===========================================================================
# NARRATIVE GENERATION ENDPOINTS
# ===========================================================================

# ---------------------------------------------------------------------------
# POST /api/v1/narratives/generate -- Generate structured narrative
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/narratives/generate",
    response_model=NarrativeResponse,
    tags=["Narratives"],
    summary="Generate clinical narrative for a patient",
    description=(
        "Generates a structured clinical narrative for a patient based on risk "
        "scores, knowledge graph pathways, mechanism chains, and population "
        "context. Currently uses template-based generation with a clear "
        "interface for future Claude AI integration."
    ),
)
async def generate_narrative_endpoint(
    request: NarrativeRequest,
) -> NarrativeResponse:
    """Generate a structured clinical narrative."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        result = generate_narrative(
            patient_id=request.patient_id,
            therapy_type=request.therapy_type,
            ae_types=request.ae_types,
            include_mechanisms=request.include_mechanisms,
            include_monitoring=request.include_monitoring,
            risk_scores=request.risk_scores,
            lab_values=request.lab_values,
        )
    except Exception as exc:
        logger.exception("Narrative generation failed for patient %s", request.patient_id)
        raise HTTPException(
            status_code=500,
            detail=f"Narrative generation failed: {exc}",
        )

    sections = [
        NarrativeSection(**s) for s in result.get("sections", [])
    ]

    return NarrativeResponse(
        request_id=request_id,
        timestamp=now,
        patient_id=request.patient_id,
        executive_summary=result["executive_summary"],
        risk_narrative=result["risk_narrative"],
        mechanistic_context=result["mechanistic_context"],
        recommended_monitoring=result["recommended_monitoring"],
        references=result["references"],
        sections=sections,
        generation_method="template_rules_v1",
    )


# ---------------------------------------------------------------------------
# GET /api/v1/narratives/patient/{patient_id}/briefing -- Clinical briefing
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/narratives/patient/{patient_id}/briefing",
    response_model=ClinicalBriefing,
    tags=["Narratives"],
    summary="Generate comprehensive clinical briefing",
    description=(
        "Generates a comprehensive clinical briefing for a specific patient, "
        "combining risk assessment, mechanistic context, population data, "
        "intervention opportunities, timing expectations, and monitoring "
        "recommendations into a single document."
    ),
)
async def generate_briefing_endpoint(
    patient_id: str,
    therapy_type: str = Query(
        "CAR-T (CD19)",
        description="Therapy modality (e.g. 'CAR-T (CD19)', 'TCR-T', 'CAR-NK')",
    ),
) -> ClinicalBriefing:
    """Generate a comprehensive clinical briefing for a patient."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    try:
        result = generate_briefing(
            patient_id=patient_id,
            therapy_type=therapy_type,
        )
    except Exception as exc:
        logger.exception("Briefing generation failed for patient %s", patient_id)
        raise HTTPException(
            status_code=500,
            detail=f"Briefing generation failed: {exc}",
        )

    sections = [
        ClinicalBriefingSection(**s) for s in result.get("sections", [])
    ]

    return ClinicalBriefing(
        request_id=request_id,
        timestamp=now,
        patient_id=result["patient_id"],
        therapy_type=result["therapy_type"],
        briefing_title=result["briefing_title"],
        risk_level=result["risk_level"],
        composite_score=result.get("composite_score"),
        sections=sections,
        intervention_points=result.get("intervention_points", []),
        timing_expectations=result.get("timing_expectations", {}),
        key_references=result.get("key_references", []),
        generation_method="template_rules_v1",
    )


# ===========================================================================
# Pharma company simulation endpoints
# ===========================================================================


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/org -- Full org hierarchy
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/org",
    tags=["Pharma"],
    summary="Full organizational hierarchy",
    description=(
        "Returns the complete pharmaceutical company organizational "
        "hierarchy with roles, responsibilities, regulatory frameworks, "
        "skills, and current status."
    ),
)
async def pharma_org() -> dict:
    """Return the full org hierarchy."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "roles": ORG_ROLES,
        "total_roles": len(ORG_ROLES),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/pipeline -- Clinical pipeline stages
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/pipeline",
    tags=["Pharma"],
    summary="Clinical pipeline stages",
    description=(
        "Returns the clinical development pipeline from preclinical through "
        "approval, including stage owners, status, dates, and applicable "
        "regulatory frameworks."
    ),
)
async def pharma_pipeline() -> dict:
    """Return the clinical pipeline stages."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Compute summary counts
    statuses = {}
    for stage in PIPELINE_STAGES:
        s = stage["status"]
        statuses[s] = statuses.get(s, 0) + 1

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "stages": PIPELINE_STAGES,
        "total_stages": len(PIPELINE_STAGES),
        "status_summary": statuses,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/regulatory-map -- All regulatory frameworks
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/regulatory-map",
    tags=["Pharma"],
    summary="Regulatory framework mapping",
    description=(
        "Returns all regulatory frameworks (ICH, FDA CFR, CIOMS, EU GMP, etc.) "
        "referenced by the organizational roles and pipeline stages, with "
        "titles, categories, URLs, and descriptions."
    ),
)
async def pharma_regulatory_map() -> dict:
    """Return the full regulatory framework mapping."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Count by category
    categories: dict[str, int] = {}
    for entry in REGULATORY_MAP.values():
        cat = entry["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "frameworks": REGULATORY_MAP,
        "total_frameworks": len(REGULATORY_MAP),
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/quality-metrics -- Quality metrics
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/quality-metrics",
    tags=["Pharma"],
    summary="Quality metrics dashboard",
    description=(
        "Returns simulated quality metrics including deviations, CAPAs, "
        "audit findings, training compliance, and batch manufacturing data."
    ),
)
async def pharma_quality_metrics() -> dict:
    """Return simulated quality metrics."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "metrics": get_quality_metrics(),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/role/{role_id} -- Single role detail
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/role/{role_id}",
    tags=["Pharma"],
    summary="Get details for a specific role",
    description=(
        "Returns full details for a single organizational role including "
        "title, manager, responsibilities, regulatory frameworks, skills, "
        "and current task."
    ),
)
async def pharma_role_detail(role_id: str) -> dict:
    """Return details for a specific role."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    role = get_role(role_id)
    if role is None:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found. "
                   f"Valid role IDs: {sorted(ORG_ROLES.keys())}",
        )

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "role": role,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/role/{role_id}/skills -- Skills for a role
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/role/{role_id}/skills",
    tags=["Pharma"],
    summary="Get skills for a specific role",
    description=(
        "Returns the skill library entries assigned to a specific "
        "organizational role, with skill names, categories, and descriptions."
    ),
)
async def pharma_role_skills(role_id: str) -> dict:
    """Return skills for a specific role."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    skills = get_role_skills(role_id)
    if skills is None:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found. "
                   f"Valid role IDs: {sorted(ORG_ROLES.keys())}",
        )

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "role_id": role_id,
        "skills": skills,
        "total_skills": len(skills),
    }


# ===========================================================================
# Pharma Simulation Endpoints
# ===========================================================================


def _simulation_not_available_response() -> dict:
    """Standard response when the simulation module is not yet available."""
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "unavailable",
        "message": (
            "Simulation module (src/data/pharma_simulation.py) is not yet "
            "available. It is being built in parallel."
        ),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/simulation/run -- Run full simulation
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/simulation/run",
    tags=["Pharma Simulation"],
    summary="Run full pharma company simulation",
    description=(
        "Executes the full pharmaceutical company simulation, running all "
        "agent roles through their delegation and deliverable workflow. "
        "Returns comprehensive results including deliverables, activity log, "
        "and delegation tree."
    ),
)
async def run_pharma_simulation() -> dict:
    """Run the full pharma company simulation."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if not _SIMULATION_AVAILABLE:
        return _simulation_not_available_response()

    try:
        result = _run_simulation()
    except Exception as exc:
        logger.exception("Simulation run failed")
        raise HTTPException(
            status_code=500,
            detail=f"Simulation run failed: {exc}",
        ) from exc

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        **result,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/simulation/status -- Simulation status summary
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/simulation/status",
    tags=["Pharma Simulation"],
    summary="Get simulation status summary",
    description=(
        "Returns a summary of the current simulation state including "
        "role counts, deliverable counts, completion percentages, and "
        "overall health indicators."
    ),
)
async def get_simulation_status() -> dict:
    """Get current simulation status summary."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if not _SIMULATION_AVAILABLE:
        return _simulation_not_available_response()

    try:
        status = _get_simulation_status()
    except Exception as exc:
        logger.exception("Failed to get simulation status")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get simulation status: {exc}",
        ) from exc

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        **status,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/simulation/log -- Activity log
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/simulation/log",
    tags=["Pharma Simulation"],
    summary="Get simulation activity log",
    description=(
        "Returns the activity log for the simulation, showing delegation "
        "events, deliverable completions, and status changes. Supports a "
        "limit parameter to control how many entries are returned."
    ),
)
async def get_simulation_log(
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of log entries to return (1-1000).",
    ),
) -> dict:
    """Get activity log entries."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if not _SIMULATION_AVAILABLE:
        return _simulation_not_available_response()

    try:
        entries = _get_activity_log(limit=limit)
    except Exception as exc:
        logger.exception("Failed to get simulation activity log")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get simulation activity log: {exc}",
        ) from exc

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "entries": entries,
        "total_entries": len(entries),
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/simulation/deliverables/{role_id} -- Role deliverables
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/simulation/deliverables/{role_id}",
    tags=["Pharma Simulation"],
    summary="Get deliverables for a specific role",
    description=(
        "Returns the list of deliverables produced by or assigned to the "
        "specified organizational role, including status, timestamps, and "
        "delegation chain information."
    ),
)
async def get_role_deliverables_endpoint(role_id: str) -> dict:
    """Get deliverables for a specific role."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if not _SIMULATION_AVAILABLE:
        return _simulation_not_available_response()

    # Validate role_id against known org roles first
    if role_id not in ORG_ROLES:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found. "
                   f"Valid role IDs: {sorted(ORG_ROLES.keys())}",
        )

    try:
        deliverables = _get_role_deliverables(role_id)
    except Exception as exc:
        logger.exception("Failed to get deliverables for role '%s'", role_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deliverables for role '{role_id}': {exc}",
        ) from exc

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        "role_id": role_id,
        "deliverables": deliverables,
        "total_deliverables": len(deliverables),
    }


# ---------------------------------------------------------------------------
# GET /api/v1/pharma/simulation/tree -- Delegation tree
# ---------------------------------------------------------------------------

@router.get(
    "/api/v1/pharma/simulation/tree",
    tags=["Pharma Simulation"],
    summary="Get delegation tree",
    description=(
        "Returns the full delegation tree showing which roles delegated "
        "what tasks to which subordinate roles, forming a hierarchical "
        "view of the simulation's task breakdown."
    ),
)
async def get_delegation_tree_endpoint() -> dict:
    """Get the delegation tree showing who delegated what to whom."""
    request_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if not _SIMULATION_AVAILABLE:
        return _simulation_not_available_response()

    try:
        tree = _get_delegation_tree()
    except Exception as exc:
        logger.exception("Failed to get delegation tree")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get delegation tree: {exc}",
        ) from exc

    return {
        "request_id": request_id,
        "timestamp": now.isoformat(),
        **tree,
    }
