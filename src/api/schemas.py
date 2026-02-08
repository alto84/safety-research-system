"""
Pydantic request/response schemas for the prediction API.

All request models include field-level validation with clinically meaningful
constraints. All response models include ``timestamp`` and ``request_id``
fields for traceability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import math

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class LabValues(BaseModel):
    """Laboratory values for biomarker scoring.

    All fields are optional; models that require specific inputs will be
    skipped if those inputs are missing.
    """

    # Endothelial / general
    ldh: float | None = Field(None, description="Lactate dehydrogenase (U/L)", ge=0)
    creatinine: float | None = Field(None, description="Serum creatinine (mg/dL)", ge=0)
    platelets: float | None = Field(None, description="Platelet count (10^9/L)", ge=0)
    crp: float | None = Field(None, description="C-reactive protein (mg/L)", ge=0)
    ferritin: float | None = Field(None, description="Serum ferritin (ng/mL)", ge=0)

    # Inflammatory / HLH
    triglycerides: float | None = Field(None, description="Fasting triglycerides (mmol/L)", ge=0)
    fibrinogen: float | None = Field(None, description="Fibrinogen (g/L)", ge=0)
    ast: float | None = Field(None, description="Aspartate aminotransferase (U/L)", ge=0)

    # Hematologic
    anc: float | None = Field(None, description="Absolute neutrophil count (10^9/L)", ge=0)
    hemoglobin: float | None = Field(None, description="Hemoglobin (g/dL)", ge=0)

    # Cytokines
    ifn_gamma: float | None = Field(None, description="IFN-gamma (pg/mL)", ge=0)
    il13: float | None = Field(None, description="IL-13 (pg/mL)", ge=0)
    mip1_alpha: float | None = Field(None, description="MIP-1alpha (pg/mL)", ge=0)
    mcp1: float | None = Field(None, description="MCP-1 / monocyte chemotactic protein-1 (pg/mL)", ge=0)
    il6: float | None = Field(None, description="IL-6 (pg/mL)", ge=0)
    tnf_alpha: float | None = Field(None, description="TNF-alpha (pg/mL)", ge=0)

    @model_validator(mode="after")
    def reject_inf_nan(self) -> "LabValues":
        for field_name in self.model_fields:
            val = getattr(self, field_name)
            if isinstance(val, float) and (math.isinf(val) or math.isnan(val)):
                raise ValueError(f"{field_name} must be a finite number, got {val}")
        return self


class VitalSigns(BaseModel):
    """Patient vital signs."""

    temperature: float | None = Field(None, description="Current temperature (Celsius)", ge=30.0, le=45.0)
    max_temperature_day1: float | None = Field(
        None, description="Maximum temperature on day 1 post-infusion (Celsius)", ge=30.0, le=45.0,
    )
    heart_rate: float | None = Field(None, description="Heart rate (bpm)", ge=0, le=300)
    systolic_bp: float | None = Field(None, description="Systolic blood pressure (mmHg)", ge=0, le=300)
    diastolic_bp: float | None = Field(None, description="Diastolic blood pressure (mmHg)", ge=0, le=200)
    spo2: float | None = Field(None, description="Oxygen saturation (%)", ge=0, le=100)
    respiratory_rate: float | None = Field(None, description="Respiratory rate (breaths/min)", ge=0, le=80)


class Demographics(BaseModel):
    """Patient demographics."""

    age_years: int | None = Field(None, description="Patient age in years", ge=0, le=120)
    weight_kg: float | None = Field(None, description="Weight in kg", ge=0)
    bsa_m2: float | None = Field(None, description="Body surface area (m^2)", ge=0)


class ClinicalContext(BaseModel):
    """Clinical context for scoring models."""

    organomegaly: int = Field(0, description="0=none, 1=hepato- or spleno-, 2=both", ge=0, le=2)
    cytopenias: int = Field(0, description="Number of cytopenia lineages (0-3)", ge=0, le=3)
    hemophagocytosis: bool = Field(False, description="Hemophagocytosis on bone marrow biopsy")
    immunosuppression: bool = Field(False, description="Known immunosuppression")
    disease_burden: float = Field(0.5, description="Tumor burden (0.0=none, 1.0=very high)", ge=0, le=1)
    prior_therapies: int = Field(0, description="Number of prior lines of therapy", ge=0)
    comorbidities: list[str] = Field(default_factory=list, description="Comorbidity codes")


class ProductInfo(BaseModel):
    """CAR-T product information."""

    product_name: str = Field("", description="Name of the CAR-T product")
    dose: float = Field(0.0, description="Infused dose (cells/kg or total cells)", ge=0)
    hours_since_infusion: float = Field(0.0, description="Hours since cell therapy infusion", ge=0)


class PatientDataRequest(BaseModel):
    """Full patient data request for prediction.

    Combines labs, vitals, demographics, clinical context, and product info.
    All sections are optional; the system will run whatever models are
    supported by the available data.
    """

    patient_id: str = Field(..., description="Unique patient identifier", min_length=1)
    labs: LabValues = Field(default_factory=LabValues)
    vitals: VitalSigns = Field(default_factory=VitalSigns)
    demographics: Demographics = Field(default_factory=Demographics)
    clinical: ClinicalContext = Field(default_factory=ClinicalContext)
    product: ProductInfo = Field(default_factory=ProductInfo)
    adverse_events: list[str] | None = Field(
        None,
        description="Which adverse events to assess (CRS, ICANS, HLH). Defaults to all.",
    )

    @field_validator("adverse_events")
    @classmethod
    def validate_adverse_events(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            valid = {"CRS", "ICANS", "HLH"}
            for ae in v:
                if ae.upper() not in valid:
                    raise ValueError(f"Invalid adverse event '{ae}'. Must be one of: {valid}")
        return v


class BatchPredictionRequest(BaseModel):
    """Batch prediction request for multiple patients."""

    patients: list[PatientDataRequest] = Field(
        ..., description="List of patient data requests", min_length=1, max_length=100,
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ScoreDetail(BaseModel):
    """Individual scoring model result.

    Mirrors the ``ScoringResult`` dataclass from ``biomarker_scores``.
    """

    model_name: str
    score: float | None = None
    risk_level: str | None = None
    confidence: float = 0.0
    contributing_factors: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    citation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class LayerDetail(BaseModel):
    """Scoring layer result."""

    layer_name: str
    layer_score: float
    layer_confidence: float
    models_run: list[str] = Field(default_factory=list)
    models_skipped: list[str] = Field(default_factory=list)
    models_failed: list[str] = Field(default_factory=list)
    scores: list[ScoreDetail] = Field(default_factory=list)


class AlertDetail(BaseModel):
    """Safety alert in the response."""

    alert_id: str
    severity: str
    alert_type: str
    title: str
    message: str
    recommended_actions: list[str] = Field(default_factory=list)


class PredictionResponse(BaseModel):
    """Full prediction response for a single patient."""

    request_id: str
    timestamp: datetime
    patient_id: str
    composite_score: float
    risk_level: str
    data_completeness: float
    models_run: int
    layers: list[LayerDetail] = Field(default_factory=list)
    individual_scores: list[ScoreDetail] = Field(default_factory=list)
    alerts: list[AlertDetail] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""

    request_id: str
    timestamp: datetime
    predictions: list[PredictionResponse]
    total_patients: int
    successful: int
    failed: int
    errors: list[dict[str, str]] = Field(default_factory=list)


class TimelinePoint(BaseModel):
    """Single point in a risk timeline."""

    timestamp: datetime
    composite_score: float
    risk_level: str
    hours_since_infusion: float
    model_scores: dict[str, float] = Field(default_factory=dict)
    alerts: list[AlertDetail] = Field(default_factory=list)


class TimelineResponse(BaseModel):
    """Risk timeline for a patient."""

    request_id: str
    timestamp: datetime
    patient_id: str
    timeline: list[TimelinePoint] = Field(default_factory=list)
    current_risk_level: str = "unknown"
    trend: str = "stable"
    trend_value: float = 0.0


class ModelInfo(BaseModel):
    """Information about a single scoring model."""

    name: str
    version: str = "1.0.0"
    status: str = "available"
    last_run: datetime | None = None
    description: str = ""
    required_inputs: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class ModelStatusResponse(BaseModel):
    """Status of all available models."""

    request_id: str
    timestamp: datetime
    models: list[ModelInfo]
    total_available: int
    engine_initialized: bool = False


class ScoreResponse(BaseModel):
    """Response for individual score endpoints."""

    request_id: str
    timestamp: datetime
    score: ScoreDetail
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standard error response."""

    request_id: str
    timestamp: datetime
    error: str
    detail: str = ""
    status_code: int = 500


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    uptime_seconds: float
    timestamp: datetime
    models_available: int
    engine_initialized: bool


# ---------------------------------------------------------------------------
# Population-level risk schemas
# ---------------------------------------------------------------------------

class BayesianPosteriorRequest(BaseModel):
    """Request for Bayesian posterior computation."""

    adverse_event: str = Field(
        ..., description="Adverse event type: CRS, ICANS, or ICAHS",
    )
    n_events: int = Field(..., description="Number of observed events", ge=0)
    n_patients: int = Field(..., description="Total patients observed", ge=1)
    use_informative_prior: bool = Field(
        True, description="Use informative prior from discounted oncology data",
    )

    @field_validator("adverse_event")
    @classmethod
    def validate_ae(cls, v: str) -> str:
        valid = {"CRS", "ICANS", "ICAHS"}
        v_upper = v.upper()
        if v_upper not in valid:
            raise ValueError(f"Invalid adverse event '{v}'. Must be one of: {valid}")
        return v_upper

    @model_validator(mode="after")
    def events_le_patients(self) -> "BayesianPosteriorRequest":
        if self.n_events > self.n_patients:
            raise ValueError(
                f"n_events ({self.n_events}) cannot exceed "
                f"n_patients ({self.n_patients})"
            )
        return self


class PosteriorEstimateResponse(BaseModel):
    """Bayesian posterior estimate."""

    adverse_event: str
    prior_alpha: float
    prior_beta: float
    posterior_alpha: float
    posterior_beta: float
    n_patients: int
    n_events: int
    mean_pct: float = Field(description="Posterior mean as percentage")
    ci_low_pct: float = Field(description="95% credible interval lower bound (%)")
    ci_high_pct: float = Field(description="95% credible interval upper bound (%)")
    ci_width_pct: float = Field(description="Width of 95% credible interval (pp)")


class BayesianPosteriorResponse(BaseModel):
    """Response for Bayesian posterior computation."""

    request_id: str
    timestamp: datetime
    estimate: PosteriorEstimateResponse


class MitigationAnalysisRequest(BaseModel):
    """Request for correlated mitigation analysis."""

    selected_mitigations: list[str] = Field(
        ..., description="List of mitigation IDs to apply",
        min_length=1,
    )
    target_ae: str = Field(
        "CRS", description="Target adverse event: CRS, ICANS, or ICAHS",
    )
    n_monte_carlo_samples: int = Field(
        5000, description="Number of Monte Carlo samples", ge=100, le=100000,
    )


class CorrelationDetail(BaseModel):
    """Detail about a pairwise correlation applied."""

    mitigation_a: str
    mitigation_b: str
    rho: float
    naive_rr: float
    corrected_rr: float


class MitigationAnalysisResponse(BaseModel):
    """Response for correlated mitigation analysis."""

    request_id: str
    timestamp: datetime
    target_ae: str
    baseline_risk_pct: float
    mitigated_risk_pct: float
    mitigated_risk_ci_low_pct: float
    mitigated_risk_ci_high_pct: float
    combined_rr: float
    naive_multiplicative_rr: float
    correction_factor: float = Field(
        description="Ratio of corrected RR to naive RR (>1 means less benefit than naive)",
    )
    mitigations_applied: list[str]
    correlations_applied: list[CorrelationDetail]


class EvidenceAccrualPoint(BaseModel):
    """Single timepoint in the evidence accrual timeline."""

    label: str
    year: int
    quarter: str
    n_cumulative_patients: int
    is_projected: bool
    crs_mean_pct: float
    crs_ci_low_pct: float
    crs_ci_high_pct: float
    crs_ci_width_pct: float
    icans_mean_pct: float
    icans_ci_low_pct: float
    icans_ci_high_pct: float
    icans_ci_width_pct: float


class EvidenceAccrualResponse(BaseModel):
    """Response for evidence accrual timeline."""

    request_id: str
    timestamp: datetime
    timeline: list[EvidenceAccrualPoint]
    current_ci_width_crs_pct: float
    projected_ci_width_crs_pct: float
    ci_narrowing_pct: float


class TrialSummaryResponse(BaseModel):
    """Response for clinical trial summary."""

    request_id: str
    timestamp: datetime
    recruiting: int
    active: int
    completed: int
    not_yet_recruiting: int
    total: int
    trials: list[dict[str, Any]]


class PopulationRiskResponse(BaseModel):
    """Population-level risk summary for SLE CAR-T."""

    request_id: str
    timestamp: datetime
    indication: str
    n_patients_pooled: int
    baseline_risks: dict[str, dict[str, Any]]
    mitigated_risks: dict[str, dict[str, Any]]
    default_mitigations: list[str]
    evidence_grade: str


class FAERSSignalResponse(BaseModel):
    """Single FAERS signal."""

    product: str
    adverse_event: str
    n_cases: int
    prr: float
    prr_ci_low: float
    prr_ci_high: float
    ror: float
    ror_ci_low: float
    ror_ci_high: float
    ebgm: float
    ebgm05: float
    is_signal: bool
    signal_strength: str


class FAERSSummaryResponse(BaseModel):
    """Response for FAERS signal detection."""

    request_id: str
    timestamp: datetime
    products_queried: list[str]
    total_reports: int
    signals_detected: int
    strong_signals: int
    signals: list[FAERSSignalResponse]
