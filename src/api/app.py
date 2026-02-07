"""
FastAPI prediction server for the Predictive Safety Platform.

Provides REST endpoints for:
    - Individual biomarker score computation (EASIX, HScore, CAR-HEMATOTOX)
    - Full ensemble prediction for a patient
    - Batch prediction for multiple patients
    - Patient risk timeline retrieval
    - Model status and health checks
    - Real-time WebSocket monitoring

The individual score endpoints (``/api/v1/scores/*``) use only the
deterministic biomarker formulas and require no ML models or SafetyEngine
initialization. The ``/api/v1/predict`` endpoint uses the full ensemble
runner and, when available, the SafetyEngine for foundation-model-augmented
predictions.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.middleware import (
    APIKeyMiddleware,
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
    RequestTimingMiddleware,
)
from src.api.schemas import (
    AlertDetail,
    BatchPredictionRequest,
    BatchPredictionResponse,
    ErrorResponse,
    HealthResponse,
    LayerDetail,
    ModelInfo,
    ModelStatusResponse,
    PatientDataRequest,
    PredictionResponse,
    ScoreDetail,
    ScoreResponse,
    TimelinePoint,
    TimelineResponse,
)
from src.models.biomarker_scores import (
    EASIX,
    CARHematotox,
    HScore,
    RiskLevel,
    ScoringResult,
    ValidationError,
)
from src.models.ensemble_runner import BiomarkerEnsembleRunner

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------

_start_time: float = 0.0
_ensemble_runner = BiomarkerEnsembleRunner()

# Reusable model instances for individual score endpoints
_easix_model = EASIX()
_hscore_model = HScore()
_car_hematotox_model = CARHematotox()

# In-memory stores (replace with database in production)
_patient_timelines: dict[str, list[dict[str, Any]]] = defaultdict(list)
_model_last_run: dict[str, datetime] = {}

# WebSocket connections for real-time monitoring
_ws_connections: dict[str, list[WebSocket]] = defaultdict(list)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    global _start_time
    _start_time = time.monotonic()
    logger.info("Safety Prediction API starting up")
    yield
    logger.info("Safety Prediction API shutting down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Predictive Safety Platform API",
    description=(
        "Clinical decision support for cell therapy adverse event risk assessment. "
        "Provides deterministic biomarker scoring based on published formulas (EASIX, "
        "HScore, CAR-HEMATOTOX, Teachey, Hay) and ensemble risk stratification for "
        "CRS, ICANS, and HLH. Not a substitute for clinical judgment."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Prediction",
            "description": "Full ensemble prediction endpoints for patient risk assessment.",
        },
        {
            "name": "Individual Scores",
            "description": "Compute individual biomarker scores (EASIX, HScore, CAR-HEMATOTOX). "
            "These endpoints use only deterministic formulas and require no ML models.",
        },
        {
            "name": "Timeline",
            "description": "Patient risk timeline endpoints.",
        },
        {
            "name": "Models",
            "description": "Model status and availability.",
        },
        {
            "name": "System",
            "description": "Health check and system status.",
        },
        {
            "name": "WebSocket",
            "description": "Real-time patient monitoring via WebSocket.",
        },
    ],
)


# ---------------------------------------------------------------------------
# Static files and clinical dashboard
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/clinical", include_in_schema=False)
async def clinical_dashboard():
    """Redirect to the clinical dashboard."""
    return RedirectResponse(url="/static/index.html")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to clinical dashboard."""
    return RedirectResponse(url="/static/index.html")


# ---------------------------------------------------------------------------
# Middleware (order matters: outermost first)
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Error handling wraps everything
app.add_middleware(ErrorHandlingMiddleware)
# Rate limiting
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
# API key auth
app.add_middleware(APIKeyMiddleware)
# Request timing and ID (innermost -- runs first)
app.add_middleware(RequestTimingMiddleware)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_request_id(request) -> str:
    """Extract request ID from request state or generate one."""
    return getattr(getattr(request, "state", None), "request_id", str(uuid.uuid4()))


def _scoring_result_to_detail(result: ScoringResult) -> ScoreDetail:
    """Convert a ScoringResult dataclass to a ScoreDetail response model."""
    return ScoreDetail(
        model_name=result.model_name,
        score=result.score,
        risk_level=result.risk_level.value if result.risk_level is not None else None,
        confidence=result.confidence,
        contributing_factors=result.contributing_factors,
        warnings=result.warnings,
        errors=result.errors,
        citation=result.citation,
        metadata=result.metadata,
    )


# Field-name mapping from Pydantic schema names to the standardised keys
# expected by the biomarker scoring models.
_LAB_KEY_MAP: dict[str, str] = {
    "ldh": "ldh_u_per_l",
    "creatinine": "creatinine_mg_dl",
    "platelets": "platelets_per_nl",
    "crp": "crp_mg_l",
    "ferritin": "ferritin_ng_ml",
    "triglycerides": "triglycerides_mmol_l",
    "fibrinogen": "fibrinogen_g_l",
    "ast": "ast_u_per_l",
    "anc": "anc_10e9_per_l",
    "hemoglobin": "hemoglobin_g_dl",
    "ifn_gamma": "ifn_gamma_pg_ml",
    "il13": "il13_pg_ml",
    "mip1_alpha": "mip1_alpha_pg_ml",
    "mcp1": "mcp1_pg_ml",
    "il6": "il6_pg_ml",
    "tnf_alpha": "tnf_alpha_pg_ml",
}

_VITAL_KEY_MAP: dict[str, str] = {
    "temperature": "temperature_c",
    "max_temperature_day1": "max_temperature_day1_c",
    "heart_rate": "heart_rate_bpm",
    "systolic_bp": "systolic_bp_mmhg",
    "diastolic_bp": "diastolic_bp_mmhg",
    "spo2": "spo2_pct",
    "respiratory_rate": "respiratory_rate_bpm",
}

_CLINICAL_KEY_MAP: dict[str, str] = {
    "organomegaly": "organomegaly",
    "cytopenias": "cytopenias_lineages",
    "hemophagocytosis": "hemophagocytosis_on_bm",
    "immunosuppression": "known_immunosuppression",
    "disease_burden": "disease_burden",
    "prior_therapies": "prior_therapies",
}

_PRODUCT_KEY_MAP: dict[str, str] = {
    "hours_since_infusion": "hours_since_infusion",
    "dose": "dose",
    "product_name": "product_name",
}


def _build_patient_data(request: PatientDataRequest) -> dict[str, Any]:
    """Flatten all patient data sections into a single dict with standardised keys.

    The biomarker scoring models expect a flat ``dict[str, Any]`` keyed by
    names like ``ldh_u_per_l``, ``temperature_c``, etc. This function maps
    from the Pydantic schema field names to those standardised keys and
    discards any ``None`` values.
    """
    patient_data: dict[str, Any] = {}

    # Labs
    for schema_key, model_key in _LAB_KEY_MAP.items():
        value = getattr(request.labs, schema_key, None)
        if value is not None:
            patient_data[model_key] = value

    # CRP needs a special case: the schema has crp in mg/L, but some models
    # use crp_mg_dl.  Provide both so models can pick whichever they need.
    crp_value = getattr(request.labs, "crp", None)
    if crp_value is not None:
        patient_data["crp_mg_l"] = crp_value
        # mg/L -> mg/dL: divide by 10
        patient_data["crp_mg_dl"] = crp_value / 10.0

    # Vitals
    for schema_key, model_key in _VITAL_KEY_MAP.items():
        value = getattr(request.vitals, schema_key, None)
        if value is not None:
            patient_data[model_key] = value

    # Clinical context
    clinical = request.clinical
    if clinical.organomegaly == 0:
        patient_data["organomegaly"] = "none"
    elif clinical.organomegaly == 1:
        patient_data["organomegaly"] = "hepatomegaly"
    else:
        patient_data["organomegaly"] = "both"

    patient_data["cytopenias_lineages"] = clinical.cytopenias
    patient_data["hemophagocytosis_on_bm"] = clinical.hemophagocytosis
    patient_data["known_immunosuppression"] = clinical.immunosuppression
    patient_data["disease_burden"] = clinical.disease_burden
    patient_data["prior_therapies"] = clinical.prior_therapies

    # Product info
    product = request.product
    if product.hours_since_infusion > 0:
        patient_data["hours_since_infusion"] = product.hours_since_infusion
    if product.dose > 0:
        patient_data["dose"] = product.dose
    if product.product_name:
        patient_data["product_name"] = product.product_name

    # Demographics
    demographics = request.demographics
    if demographics.age_years is not None:
        patient_data["age_years"] = demographics.age_years
    if demographics.weight_kg is not None:
        patient_data["weight_kg"] = demographics.weight_kg
    if demographics.bsa_m2 is not None:
        patient_data["bsa_m2"] = demographics.bsa_m2

    return patient_data


def _extract_contributing_factors(scores: list[ScoringResult]) -> list[str]:
    """Extract the top contributing factors from scoring results."""
    factors: list[str] = []
    for score in scores:
        if score.is_valid and score.risk_level is not None:
            risk_val = score.risk_level.value
            if risk_val in ("high",):
                score_str = f"{score.score:.2f}" if score.score is not None else "N/A"
                factors.append(
                    f"{score.model_name}: {risk_val} risk (score={score_str})"
                )
            # Highlight major contributing factors from each model
            for factor_name, factor_value in score.contributing_factors.items():
                if isinstance(factor_value, dict) and "points" in factor_value:
                    # HScore / CAR-HEMATOTOX style: {"value": X, "points": Y}
                    if factor_value.get("points", 0) > 0:
                        factors.append(
                            f"{score.model_name}/{factor_name}: "
                            f"{factor_value['value']} (+{factor_value['points']} pts)"
                        )
                elif isinstance(factor_value, (int, float)) and factor_value > 0:
                    factors.append(
                        f"{score.model_name}/{factor_name}: {factor_value}"
                    )
    return factors[:15]  # Limit to top 15


def _compute_composite_score(all_scores: list[ScoringResult]) -> float:
    """Compute a composite score (0.0-1.0) from individual model scores.

    Uses a simple confidence-weighted average of normalised scores. Each
    model's score is normalised to a 0.0-1.0 range using model-specific
    logic, then combined.
    """
    if not all_scores:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0

    for s in all_scores:
        if not s.is_valid or s.score is None:
            continue

        # Normalise each model's score to 0.0-1.0
        normalised = _normalise_score(s.model_name, s.score)
        weighted_sum += normalised * s.confidence
        weight_total += s.confidence

    if weight_total == 0.0:
        return 0.0

    return round(weighted_sum / weight_total, 4)


def _normalise_score(model_name: str, score: float) -> float:
    """Normalise a model score to the 0.0-1.0 range."""
    import math

    if model_name == "EASIX":
        # EASIX typical range: 0-50+, log-transform and clip
        return min(1.0, max(0.0, math.log1p(score) / math.log1p(50.0)))
    elif model_name in ("Modified_EASIX", "Pre_Modified_EASIX"):
        return min(1.0, max(0.0, math.log1p(score) / math.log1p(100.0)))
    elif model_name == "HScore":
        # HScore range: 0-337
        return min(1.0, max(0.0, score / 337.0))
    elif model_name == "CAR_HEMATOTOX":
        # CAR-HEMATOTOX range: 0-10
        return min(1.0, max(0.0, score / 10.0))
    elif model_name == "Teachey_Cytokine_3var":
        # Already a probability 0-1
        return min(1.0, max(0.0, score))
    elif model_name == "Hay_Binary_Classifier":
        # 0 or 1
        return min(1.0, max(0.0, score))
    else:
        # Unknown model; assume 0-1 range
        return min(1.0, max(0.0, score))


def _risk_level_to_string(risk: RiskLevel | None) -> str:
    """Convert a RiskLevel enum to a string, defaulting to 'unknown'."""
    if risk is None:
        return "unknown"
    return risk.value


async def _notify_ws_clients(patient_id: str, data: dict[str, Any]) -> None:
    """Send a JSON update to all WebSocket clients monitoring a patient."""
    connections = _ws_connections.get(patient_id, [])
    dead: list[WebSocket] = []
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    # Clean up disconnected clients
    for ws in dead:
        connections.remove(ws)


# ---------------------------------------------------------------------------
# POST /api/v1/predict -- Full ensemble prediction
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Run prediction for a patient",
    description=(
        "Runs all applicable biomarker scoring models and produces an ensemble "
        "risk prediction. Returns individual model scores, layer results, "
        "composite score, alerts, and contributing factors."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def predict(
    request: PatientDataRequest,
    raw_request: Any = None,
) -> PredictionResponse:
    """Run full ensemble prediction for a patient."""
    request_id = str(uuid.uuid4())

    # Build a flat patient_data dict with standardised keys
    patient_data = _build_patient_data(request)

    # Run the ensemble
    try:
        ensemble_result = _ensemble_runner.run(patient_data)
    except Exception as exc:
        logger.exception("Ensemble prediction failed for patient %s", request.patient_id)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        )

    # Update last-run times
    for score in ensemble_result.all_scores:
        _model_last_run[score.model_name] = datetime.utcnow()

    # Build layer details
    layer_details = []
    for layer in ensemble_result.layers:
        layer_details.append(LayerDetail(
            layer_name=layer.layer_name,
            layer_score=_compute_composite_score(layer.scores),
            layer_confidence=layer.layer_confidence,
            models_run=layer.models_run,
            models_skipped=layer.models_skipped,
            models_failed=layer.models_failed,
            scores=[_scoring_result_to_detail(s) for s in layer.scores],
        ))

    # Build individual score details
    individual_scores = [
        _scoring_result_to_detail(s) for s in ensemble_result.all_scores
    ]

    # Compute composite score from all valid results
    composite_score = _compute_composite_score(ensemble_result.all_scores)

    # Extract contributing factors
    contributing_factors = _extract_contributing_factors(ensemble_result.all_scores)

    # Overall risk level as a string
    risk_level_str = _risk_level_to_string(ensemble_result.overall_risk_level)

    # Data completeness: ratio of models that ran vs total models
    total_models = (
        ensemble_result.model_count_run
        + ensemble_result.model_count_skipped
        + ensemble_result.model_count_failed
    )
    data_completeness = (
        ensemble_result.model_count_run / total_models if total_models > 0 else 0.0
    )

    now = datetime.utcnow()

    # Build model_scores dict for timeline
    model_scores: dict[str, float] = {}
    for s in ensemble_result.all_scores:
        if s.is_valid and s.score is not None:
            model_scores[s.model_name] = _normalise_score(s.model_name, s.score)

    # Store in timeline
    timeline_point = {
        "timestamp": now.isoformat(),
        "composite_score": composite_score,
        "risk_level": risk_level_str,
        "hours_since_infusion": request.product.hours_since_infusion,
        "model_scores": model_scores,
    }
    _patient_timelines[request.patient_id].append(timeline_point)

    # Notify WebSocket clients
    ws_payload = {
        "type": "prediction_update",
        "patient_id": request.patient_id,
        "composite_score": composite_score,
        "risk_level": risk_level_str,
        "timestamp": now.isoformat(),
        "models_run": ensemble_result.model_count_run,
    }
    await _notify_ws_clients(request.patient_id, ws_payload)

    return PredictionResponse(
        request_id=request_id,
        timestamp=now,
        patient_id=request.patient_id,
        composite_score=composite_score,
        risk_level=risk_level_str,
        data_completeness=round(data_completeness, 3),
        models_run=ensemble_result.model_count_run,
        layers=layer_details,
        individual_scores=individual_scores,
        alerts=[],  # Alerts generated by AlertEngine if SafetyEngine is initialized
        contributing_factors=contributing_factors,
        metadata={
            "ensemble_method": "layered_biomarker",
            "overall_confidence": ensemble_result.overall_confidence,
            "high_risk_models": ensemble_result.high_risk_models,
            "ensemble_warnings": ensemble_result.warnings,
        },
    )


# ---------------------------------------------------------------------------
# POST /api/v1/predict/batch -- Batch prediction
# ---------------------------------------------------------------------------

@app.post(
    "/api/v1/predict/batch",
    response_model=BatchPredictionResponse,
    tags=["Prediction"],
    summary="Batch prediction for multiple patients",
    description="Runs ensemble prediction for up to 100 patients in a single request.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input data"},
    },
)
async def predict_batch(
    batch_request: BatchPredictionRequest,
) -> BatchPredictionResponse:
    """Run predictions for multiple patients."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    predictions: list[PredictionResponse] = []
    errors: list[dict[str, str]] = []
    successful = 0
    failed = 0

    for patient_request in batch_request.patients:
        try:
            result = await predict(patient_request)
            predictions.append(result)
            successful += 1
        except Exception as exc:
            failed += 1
            errors.append({
                "patient_id": patient_request.patient_id,
                "error": str(exc),
            })
            logger.error(
                "Batch prediction failed for patient %s: %s",
                patient_request.patient_id,
                exc,
            )

    return BatchPredictionResponse(
        request_id=request_id,
        timestamp=now,
        predictions=predictions,
        total_patients=len(batch_request.patients),
        successful=successful,
        failed=failed,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/patient/{patient_id}/timeline -- Risk timeline
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/patient/{patient_id}/timeline",
    response_model=TimelineResponse,
    tags=["Timeline"],
    summary="Get risk timeline for a patient",
    description="Returns the time-series of risk scores over the monitoring period.",
    responses={
        404: {"model": ErrorResponse, "description": "Patient not found"},
    },
)
async def get_timeline(patient_id: str) -> TimelineResponse:
    """Retrieve the risk score timeline for a patient."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    timeline_data = _patient_timelines.get(patient_id, [])
    if not timeline_data:
        raise HTTPException(
            status_code=404,
            detail=f"No timeline data for patient '{patient_id}'. Run a prediction first.",
        )

    points = []
    for point in timeline_data:
        points.append(TimelinePoint(
            timestamp=datetime.fromisoformat(point["timestamp"]),
            composite_score=point["composite_score"],
            risk_level=point["risk_level"],
            hours_since_infusion=point.get("hours_since_infusion", 0.0),
            model_scores=point.get("model_scores", {}),
        ))

    # Compute trend from last two points
    trend = "stable"
    trend_value = 0.0
    if len(points) >= 2:
        delta = points[-1].composite_score - points[-2].composite_score
        trend_value = delta
        if delta > 0.05:
            trend = "worsening"
        elif delta < -0.05:
            trend = "improving"

    current_risk = points[-1].risk_level if points else "unknown"

    return TimelineResponse(
        request_id=request_id,
        timestamp=now,
        patient_id=patient_id,
        timeline=points,
        current_risk_level=current_risk,
        trend=trend,
        trend_value=trend_value,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/models/status -- Model availability
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/models/status",
    response_model=ModelStatusResponse,
    tags=["Models"],
    summary="Model availability and status",
    description="Returns which scoring models are loaded, their versions, and last run time.",
)
async def get_model_status() -> ModelStatusResponse:
    """Return status of all scoring models."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()

    models = [
        ModelInfo(
            name="EASIX",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("EASIX"),
            description="Endothelial Activation and Stress Index",
            required_inputs=["ldh_u_per_l", "creatinine_mg_dl", "platelets_per_nl"],
            references=["Pennisi et al. Blood Adv 2021", "Korell et al. J Cancer Res Clin Oncol 2022"],
        ),
        ModelInfo(
            name="Modified_EASIX",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("Modified_EASIX"),
            description="Modified EASIX for CRS prediction (CRP replaces creatinine)",
            required_inputs=["ldh_u_per_l", "crp_mg_dl", "platelets_per_nl"],
            references=["Pennisi et al. Blood Adv 2021", "Korell et al. J Cancer Res Clin Oncol 2022"],
        ),
        ModelInfo(
            name="Pre_Modified_EASIX",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("Pre_Modified_EASIX"),
            description="Pre-lymphodepletion Modified EASIX",
            required_inputs=["ldh_u_per_l", "crp_mg_dl", "platelets_per_nl"],
            references=["Korell et al. J Cancer Res Clin Oncol 2022"],
        ),
        ModelInfo(
            name="HScore",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("HScore"),
            description="Hemophagocytic Syndrome Score for HLH probability",
            required_inputs=[
                "temperature_c", "organomegaly", "cytopenias_lineages",
                "ferritin_ng_ml", "triglycerides_mmol_l", "fibrinogen_g_l",
                "ast_u_per_l", "hemophagocytosis_on_bm", "known_immunosuppression",
            ],
            references=["Fardet et al. Arthritis Rheumatol 2014;66(9):2613-2620"],
        ),
        ModelInfo(
            name="CAR_HEMATOTOX",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("CAR_HEMATOTOX"),
            description="CAR-HEMATOTOX score for prolonged cytopenia risk",
            required_inputs=[
                "anc_10e9_per_l", "hemoglobin_g_dl", "platelets_per_nl",
                "crp_mg_l", "ferritin_ng_ml",
            ],
            references=["Rejeski et al. Blood 2021;138(24):2499-2513"],
        ),
        ModelInfo(
            name="Teachey_Cytokine_3var",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("Teachey_Cytokine_3var"),
            description="3-cytokine logistic regression for severe CRS prediction",
            required_inputs=["ifn_gamma_pg_ml", "sgp130_ng_ml", "il1ra_pg_ml"],
            references=["Teachey et al. Cancer Discov 2016;6(6):664-679"],
        ),
        ModelInfo(
            name="Hay_Binary_Classifier",
            version="1.0.0",
            status="available",
            last_run=_model_last_run.get("Hay_Binary_Classifier"),
            description="Early CRS binary screen using day 1 fever and MCP-1",
            required_inputs=["temperature_c", "mcp1_pg_ml"],
            references=["Hay et al. Blood 2017;130(21):2295-2306"],
        ),
    ]

    return ModelStatusResponse(
        request_id=request_id,
        timestamp=now,
        models=models,
        total_available=len(models),
        engine_initialized=False,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/scores/easix -- Individual EASIX score
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/scores/easix",
    response_model=ScoreResponse,
    tags=["Individual Scores"],
    summary="Compute EASIX score",
    description=(
        "Compute the Endothelial Activation and Stress Index. "
        "Formula: EASIX = (LDH x Creatinine) / Platelets. "
        "Reference: Pennisi et al. Blood Adv 2021; Korell et al. 2022."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input parameters"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def compute_easix(
    ldh: float = Query(..., description="LDH in U/L", gt=0),
    creatinine: float = Query(..., description="Creatinine in mg/dL", gt=0),
    platelets: float = Query(..., description="Platelets in 10^9/L", gt=0),
) -> ScoreResponse:
    """Compute EASIX score from query parameters."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()
    endpoint_warnings: list[str] = []

    # Warn on unusual values
    if ldh > 2000:
        endpoint_warnings.append(f"LDH={ldh} U/L is unusually high; verify value")
    if creatinine > 10:
        endpoint_warnings.append(f"Creatinine={creatinine} mg/dL is unusually high; verify value")
    if platelets < 10:
        endpoint_warnings.append(f"Platelets={platelets} is critically low")

    # Build patient_data dict with standardised keys
    patient_data = {
        "ldh_u_per_l": ldh,
        "creatinine_mg_dl": creatinine,
        "platelets_per_nl": platelets,
    }

    result = _easix_model.score(patient_data)

    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "Scoring failed",
        )

    _model_last_run["EASIX"] = now

    return ScoreResponse(
        request_id=request_id,
        timestamp=now,
        score=_scoring_result_to_detail(result),
        warnings=endpoint_warnings + result.warnings,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/scores/hscore -- Individual HScore
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/scores/hscore",
    response_model=ScoreResponse,
    tags=["Individual Scores"],
    summary="Compute HScore",
    description=(
        "Compute the Hemophagocytic Syndrome Score. Returns the HScore "
        "and the HLH probability. Reference: Fardet et al. 2014."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input parameters"},
    },
)
async def compute_hscore(
    temperature: float = Query(..., description="Max temperature in Celsius", ge=30.0, le=45.0),
    organomegaly: int = Query(..., description="0=none, 1=hepato- or spleno-, 2=both", ge=0, le=2),
    cytopenias: int = Query(..., description="Number of lineages (0-3)", ge=0, le=3),
    ferritin: float = Query(..., description="Ferritin in ng/mL", ge=0),
    triglycerides: float = Query(..., description="Triglycerides in mmol/L", ge=0),
    fibrinogen: float = Query(..., description="Fibrinogen in g/L", ge=0),
    ast: float = Query(..., description="AST in U/L", ge=0),
    hemophagocytosis: bool = Query(..., description="Hemophagocytosis on biopsy"),
    immunosuppression: bool = Query(..., description="Known immunosuppression"),
) -> ScoreResponse:
    """Compute HScore from query parameters."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()
    endpoint_warnings: list[str] = []

    if ferritin > 50000:
        endpoint_warnings.append(f"Ferritin={ferritin} ng/mL is extremely elevated")
    if fibrinogen < 1.0:
        endpoint_warnings.append(f"Fibrinogen={fibrinogen} g/L suggests consumptive coagulopathy")

    # Map organomegaly integer to string expected by HScore model
    organo_map = {0: "none", 1: "hepatomegaly", 2: "both"}
    organo_str = organo_map.get(organomegaly, "none")

    # Build patient_data dict with standardised keys
    patient_data: dict[str, Any] = {
        "temperature_c": temperature,
        "organomegaly": organo_str,
        "cytopenias_lineages": cytopenias,
        "ferritin_ng_ml": ferritin,
        "triglycerides_mmol_l": triglycerides,
        "fibrinogen_g_l": fibrinogen,
        "ast_u_per_l": ast,
        "hemophagocytosis_on_bm": hemophagocytosis,
        "known_immunosuppression": immunosuppression,
    }

    result = _hscore_model.score(patient_data)

    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "Scoring failed",
        )

    _model_last_run["HScore"] = now

    return ScoreResponse(
        request_id=request_id,
        timestamp=now,
        score=_scoring_result_to_detail(result),
        warnings=endpoint_warnings + result.warnings,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/scores/car-hematotox -- Individual CAR-HEMATOTOX
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/scores/car-hematotox",
    response_model=ScoreResponse,
    tags=["Individual Scores"],
    summary="Compute CAR-HEMATOTOX score",
    description=(
        "Compute the CAR-HEMATOTOX score for predicting prolonged cytopenias. "
        "Score range: 0-10, high risk >= 3. Reference: Rejeski et al. 2021."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input parameters"},
    },
)
async def compute_car_hematotox(
    anc: float = Query(..., description="ANC in 10^9/L", ge=0),
    hemoglobin: float = Query(..., description="Hemoglobin in g/dL", ge=0),
    platelets: float = Query(..., description="Platelets in 10^9/L", ge=0),
    crp: float = Query(..., description="CRP in mg/L", ge=0),
    ferritin: float = Query(..., description="Ferritin in ng/mL", ge=0),
) -> ScoreResponse:
    """Compute CAR-HEMATOTOX score from query parameters."""
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()
    endpoint_warnings: list[str] = []

    if anc == 0:
        endpoint_warnings.append("ANC=0: patient is severely neutropenic")
    if hemoglobin < 7:
        endpoint_warnings.append(f"Hemoglobin={hemoglobin} g/dL: consider transfusion")

    # Build patient_data dict with standardised keys
    patient_data = {
        "anc_10e9_per_l": anc,
        "hemoglobin_g_dl": hemoglobin,
        "platelets_per_nl": platelets,
        "crp_mg_l": crp,
        "ferritin_ng_ml": ferritin,
    }

    result = _car_hematotox_model.score(patient_data)

    if not result.is_valid:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "Scoring failed",
        )

    _model_last_run["CAR_HEMATOTOX"] = now

    return ScoreResponse(
        request_id=request_id,
        timestamp=now,
        score=_scoring_result_to_detail(result),
        warnings=endpoint_warnings + result.warnings,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/health -- Health check
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Returns server health status, version, and uptime.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime_seconds=time.monotonic() - _start_time,
        timestamp=datetime.utcnow(),
        models_available=7,
        engine_initialized=False,
    )


# ---------------------------------------------------------------------------
# WebSocket /ws/monitor/{patient_id} -- Real-time monitoring
# ---------------------------------------------------------------------------

@app.websocket("/ws/monitor/{patient_id}")
async def websocket_monitor(websocket: WebSocket, patient_id: str):
    """Real-time risk monitoring via WebSocket.

    Clients connect to receive JSON updates whenever a new prediction is
    computed for the specified patient. The server also sends periodic
    heartbeat messages.

    Message format (server -> client):
        {
            "type": "prediction_update" | "heartbeat" | "connected",
            "patient_id": "...",
            "composite_score": 0.45,
            "risk_level": "moderate",
            "timestamp": "2025-01-15T10:30:00",
            ...
        }

    The client can send JSON messages to request on-demand predictions:
        {
            "type": "request_update",
            "patient_id": "..."
        }
    """
    await websocket.accept()
    _ws_connections[patient_id].append(websocket)

    logger.info("WebSocket client connected for patient %s", patient_id)

    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "patient_id": patient_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"Monitoring patient {patient_id}. You will receive updates on new predictions.",
    })

    try:
        while True:
            # Wait for client messages or send heartbeat
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "request_update":
                    # Send latest timeline point if available
                    timeline = _patient_timelines.get(patient_id, [])
                    if timeline:
                        latest = timeline[-1]
                        await websocket.send_json({
                            "type": "latest_status",
                            "patient_id": patient_id,
                            "composite_score": latest["composite_score"],
                            "risk_level": latest["risk_level"],
                            "timestamp": latest["timestamp"],
                        })
                    else:
                        await websocket.send_json({
                            "type": "no_data",
                            "patient_id": patient_id,
                            "message": "No predictions available yet for this patient.",
                            "timestamp": datetime.utcnow().isoformat(),
                        })

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({
                    "type": "heartbeat",
                    "patient_id": patient_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for patient %s", patient_id)
    except Exception as exc:
        logger.error("WebSocket error for patient %s: %s", patient_id, exc)
    finally:
        if websocket in _ws_connections.get(patient_id, []):
            _ws_connections[patient_id].remove(websocket)
