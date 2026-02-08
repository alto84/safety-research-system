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
# H3 fix: Unified AE validation set across all schemas
# ---------------------------------------------------------------------------

VALID_ADVERSE_EVENTS = {"CRS", "ICANS", "HLH", "ICAHS", "LICATS"}


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

    age_years: int | None = Field(None, description="Patient age in years", ge=0, le=150)
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
            for ae in v:
                if ae.upper() not in VALID_ADVERSE_EVENTS:
                    raise ValueError(
                        f"Invalid adverse event '{ae}'. Must be one of: {VALID_ADVERSE_EVENTS}"
                    )
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
        v_upper = v.upper()
        if v_upper not in VALID_ADVERSE_EVENTS:
            raise ValueError(
                f"Invalid adverse event '{v}'. Must be one of: {VALID_ADVERSE_EVENTS}"
            )
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
    prior_alpha: float = Field(gt=0)
    prior_beta: float = Field(gt=0)
    posterior_alpha: float = Field(gt=0)
    posterior_beta: float = Field(gt=0)
    n_patients: int = Field(ge=1, description="Total patients observed (positive)")
    n_events: int = Field(ge=0, description="Observed events (non-negative)")
    mean_pct: float = Field(description="Posterior mean as percentage", ge=0.0, le=100.0)
    ci_low_pct: float = Field(description="95% credible interval lower bound (%)", ge=0.0, le=100.0)
    ci_high_pct: float = Field(description="95% credible interval upper bound (%)", ge=0.0, le=100.0)
    ci_width_pct: float = Field(description="Width of 95% credible interval (pp)", ge=0.0)

    # H3 fix: Validate confidence interval ordering (lower < upper)
    @model_validator(mode="after")
    def ci_lower_le_upper(self) -> "PosteriorEstimateResponse":
        if self.ci_low_pct > self.ci_high_pct:
            raise ValueError(
                f"CI lower bound ({self.ci_low_pct}) must be <= upper bound ({self.ci_high_pct})"
            )
        return self


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
    rho: float = Field(ge=0.0, le=1.0, description="Correlation coefficient in [0, 1]")
    naive_rr: float = Field(ge=0.0)
    corrected_rr: float = Field(ge=0.0)


class MitigationAnalysisResponse(BaseModel):
    """Response for correlated mitigation analysis."""

    request_id: str
    timestamp: datetime
    target_ae: str
    baseline_risk_pct: float = Field(ge=0.0, le=100.0)
    mitigated_risk_pct: float = Field(ge=0.0, le=100.0)
    mitigated_risk_ci_low_pct: float = Field(ge=0.0, le=100.0)
    mitigated_risk_ci_high_pct: float = Field(ge=0.0, le=100.0)
    combined_rr: float = Field(ge=0.0, description="Combined relative risk (0-1 = protective)")
    naive_multiplicative_rr: float = Field(ge=0.0)
    correction_factor: float = Field(
        description="Ratio of corrected RR to naive RR (>1 means less benefit than naive)",
    )
    mitigations_applied: list[str]
    correlations_applied: list[CorrelationDetail]

    # H3 fix: Validate CI ordering for mitigated risk
    @model_validator(mode="after")
    def mitigated_ci_ordering(self) -> "MitigationAnalysisResponse":
        if self.mitigated_risk_ci_low_pct > self.mitigated_risk_ci_high_pct:
            raise ValueError(
                f"Mitigated risk CI lower ({self.mitigated_risk_ci_low_pct}) "
                f"must be <= upper ({self.mitigated_risk_ci_high_pct})"
            )
        return self


class EvidenceAccrualPoint(BaseModel):
    """Single timepoint in the evidence accrual timeline."""

    label: str
    year: int
    quarter: str
    n_cumulative_patients: int = Field(ge=1, description="Cumulative patient count (positive)")
    is_projected: bool
    crs_mean_pct: float = Field(ge=0.0, le=100.0)
    crs_ci_low_pct: float = Field(ge=0.0, le=100.0)
    crs_ci_high_pct: float = Field(ge=0.0, le=100.0)
    crs_ci_width_pct: float = Field(ge=0.0)
    icans_mean_pct: float = Field(ge=0.0, le=100.0)
    icans_ci_low_pct: float = Field(ge=0.0, le=100.0)
    icans_ci_high_pct: float = Field(ge=0.0, le=100.0)
    icans_ci_width_pct: float = Field(ge=0.0)


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
    n_patients_pooled: int = Field(ge=1, description="Pooled sample size (positive)")
    baseline_risks: dict[str, dict[str, Any]]
    mitigated_risks: dict[str, dict[str, Any]]
    default_mitigations: list[str]
    evidence_grade: str


class FAERSSignalResponse(BaseModel):
    """Single FAERS signal."""

    product: str
    adverse_event: str
    n_cases: int = Field(ge=0, description="Event count (non-negative)")
    prr: float = Field(ge=0.0)
    prr_ci_low: float = Field(ge=0.0)
    prr_ci_high: float = Field(ge=0.0)
    ror: float = Field(ge=0.0)
    ror_ci_low: float = Field(ge=0.0)
    ror_ci_high: float = Field(ge=0.0)
    ebgm: float = Field(ge=0.0)
    ebgm05: float = Field(ge=0.0)
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


# ---------------------------------------------------------------------------
# CDP/CSP schemas
# ---------------------------------------------------------------------------

class MonitoringActivity(BaseModel):
    """Single monitoring window in a CDP monitoring schedule."""

    time_window: str
    days: str
    activities: list[str]
    frequency: str
    rationale: str


class MonitoringScheduleResponse(BaseModel):
    """Response for CDP monitoring schedule."""

    therapy_type: str
    schedule: list[MonitoringActivity]


class EligibilityCriterion(BaseModel):
    """Single inclusion or exclusion criterion."""

    criterion: str
    rationale: str
    category: str


class EligibilityCriteriaResponse(BaseModel):
    """Response for CDP eligibility criteria."""

    therapy_type: str
    inclusion: list[EligibilityCriterion]
    exclusion: list[EligibilityCriterion]


class StoppingBoundary(BaseModel):
    """A single boundary point in a stopping rule."""

    n_patients: int
    max_events: int


class StoppingRule(BaseModel):
    """Bayesian stopping rule for a specific AE type."""

    ae_type: str
    target_rate_pct: float
    posterior_threshold: float
    description: str
    boundaries: list[StoppingBoundary]


class StoppingRulesResponse(BaseModel):
    """Response for CDP stopping rules."""

    therapy_type: str
    rules: list[StoppingRule]


class SampleSizeScenario(BaseModel):
    """A single sample size scenario."""

    target_precision: str
    estimated_n: int
    current_n: int
    additional_needed: int
    notes: str


class SampleSizeResponse(BaseModel):
    """Response for CDP sample size considerations."""

    therapy_type: str
    scenarios: list[SampleSizeScenario]


# ---------------------------------------------------------------------------
# Therapy selector schemas
# ---------------------------------------------------------------------------

class TherapyListItem(BaseModel):
    """Single therapy type in the therapy list."""

    id: str
    name: str
    category: str
    data_available: bool


class TherapyListResponse(BaseModel):
    """Response for therapy type listing."""

    therapies: list[TherapyListItem]


# ---------------------------------------------------------------------------
# System architecture schemas
# ---------------------------------------------------------------------------

class ModuleInfo(BaseModel):
    """Metadata for a single source module."""

    name: str
    path: str
    description: str
    public_functions: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    lines_of_code: int = 0


class DependencyEdge(BaseModel):
    """A directed dependency from one module to another."""

    source: str
    target: str
    import_names: list[str] = Field(default_factory=list)


class EndpointInfo(BaseModel):
    """Metadata for a single API endpoint."""

    method: str
    path: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    request_schema: str | None = None
    response_schema: str | None = None


class RegistryModelInfo(BaseModel):
    """Metadata for a model in the model registry."""

    id: str
    name: str
    description: str
    suitable_for: list[str] = Field(default_factory=list)
    requires: list[str] = Field(default_factory=list)


class TestSummary(BaseModel):
    """Summary of test coverage."""

    total_tests: int
    test_files: int
    unit_tests: int
    integration_tests: int
    other_tests: int


class SystemHealthInfo(BaseModel):
    """System health snapshot."""

    models_loaded: int
    api_version: str
    uptime_seconds: float
    test_count: int
    total_endpoints: int
    total_modules: int


class ArchitectureResponse(BaseModel):
    """Full system architecture response."""

    request_id: str
    timestamp: datetime
    modules: list[ModuleInfo]
    dependencies: list[DependencyEdge]
    endpoints: list[EndpointInfo]
    registry_models: list[RegistryModelInfo]
    test_summary: TestSummary
    system_health: SystemHealthInfo


# ---------------------------------------------------------------------------
# Knowledge graph schemas
# ---------------------------------------------------------------------------

class KnowledgePathwayStep(BaseModel):
    """A single directed step in a signaling pathway."""

    source: str
    target: str
    relation: str
    mechanism: str
    confidence: float
    temporal_window: str
    is_feedback_loop: bool = False
    intervention_point: bool = False
    intervention_agents: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class KnowledgePathwayNode(BaseModel):
    """A node in the pathway graph."""

    id: str
    label: str
    node_type: str = "molecule"


class KnowledgePathwayEdge(BaseModel):
    """A directed edge in the pathway graph."""

    source: str
    target: str
    relation: str
    mechanism: str
    confidence: float
    is_feedback_loop: bool = False
    intervention_point: bool = False
    references: list[str] = Field(default_factory=list)


class KnowledgePathwayResponse(BaseModel):
    """A signaling pathway as a directed graph."""

    pathway_id: str
    name: str
    description: str
    nodes: list[KnowledgePathwayNode] = Field(default_factory=list)
    edges: list[KnowledgePathwayEdge] = Field(default_factory=list)
    steps: list[KnowledgePathwayStep] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    exit_points: list[str] = Field(default_factory=list)
    feedback_loops: list[str] = Field(default_factory=list)
    intervention_summary: str = ""
    ae_outcomes: list[str] = Field(default_factory=list)
    key_references: list[str] = Field(default_factory=list)


class KnowledgePathwayListResponse(BaseModel):
    """List of all pathways."""

    request_id: str
    timestamp: datetime
    pathways: list[KnowledgePathwayResponse]
    total: int


class KnowledgeMechanismStep(BaseModel):
    """A single step in an AE mechanism chain."""

    step_number: int
    entity: str
    action: str
    detail: str
    temporal_onset: str = ""
    biomarkers: list[str] = Field(default_factory=list)
    is_branching_point: bool = False
    branches: list[str] = Field(default_factory=list)
    is_intervention_point: bool = False
    interventions: list[str] = Field(default_factory=list)


class KnowledgeMechanismResponse(BaseModel):
    """A complete mechanism chain from therapy to adverse event."""

    mechanism_id: str
    therapy_modality: str
    ae_category: str
    name: str
    description: str
    steps: list[KnowledgeMechanismStep] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    severity_determinants: list[str] = Field(default_factory=list)
    typical_onset: str = ""
    typical_duration: str = ""
    incidence_range: str = ""
    mortality_rate: str = ""
    key_references: list[str] = Field(default_factory=list)


class KnowledgeMechanismListResponse(BaseModel):
    """List of all mechanism chains."""

    request_id: str
    timestamp: datetime
    mechanisms: list[KnowledgeMechanismResponse]
    total: int


class KnowledgeModulatorResponse(BaseModel):
    """A drug that modulates a molecular target."""

    name: str
    mechanism: str
    status: str
    route: str = ""
    dose: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class KnowledgeTargetResponse(BaseModel):
    """A molecular target in the knowledge graph."""

    target_id: str
    name: str
    gene_symbol: str
    category: str
    pathways: list[str] = Field(default_factory=list)
    normal_range: str = ""
    ae_range: str = ""
    clinical_relevance: str = ""
    modulators: list[KnowledgeModulatorResponse] = Field(default_factory=list)
    upstream_of: list[str] = Field(default_factory=list)
    downstream_of: list[str] = Field(default_factory=list)
    biomarker_utility: str = ""
    references: list[str] = Field(default_factory=list)


class KnowledgeTargetListResponse(BaseModel):
    """List of all molecular targets."""

    request_id: str
    timestamp: datetime
    targets: list[KnowledgeTargetResponse]
    total: int


class KnowledgeActivationState(BaseModel):
    """An activation state of a cell type."""

    name: str
    description: str
    triggers: list[str] = Field(default_factory=list)
    secreted_factors: list[str] = Field(default_factory=list)
    surface_markers: list[str] = Field(default_factory=list)
    functional_outcome: str = ""
    references: list[str] = Field(default_factory=list)


class KnowledgeCellTypeResponse(BaseModel):
    """A cell type involved in AE pathogenesis."""

    cell_id: str
    name: str
    lineage: str
    tissue: str
    surface_markers: list[str] = Field(default_factory=list)
    activation_states: list[KnowledgeActivationState] = Field(default_factory=list)
    roles_in_ae: dict[str, str] = Field(default_factory=dict)
    secreted_factors_baseline: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class KnowledgeCellTypeListResponse(BaseModel):
    """List of all cell types."""

    request_id: str
    timestamp: datetime
    cell_types: list[KnowledgeCellTypeResponse]
    total: int


class KnowledgeReferenceResponse(BaseModel):
    """A peer-reviewed publication."""

    pmid: str
    first_author: str
    year: int
    journal: str
    title: str
    doi: str
    key_finding: str
    evidence_grade: str
    tags: list[str] = Field(default_factory=list)


class KnowledgeReferenceListResponse(BaseModel):
    """Full citation database."""

    request_id: str
    timestamp: datetime
    references: list[KnowledgeReferenceResponse]
    total: int


class KnowledgeOverviewResponse(BaseModel):
    """Summary statistics across the knowledge graph."""

    request_id: str
    timestamp: datetime
    pathway_count: int
    pathway_names: list[str]
    total_pathway_steps: int
    mechanism_count: int
    mechanism_names: list[str]
    target_count: int
    druggable_target_count: int
    cell_type_count: int
    reference_count: int
    ae_types_covered: list[str]
    therapy_types_covered: list[str]


# ---------------------------------------------------------------------------
# Publication analysis schemas
# ---------------------------------------------------------------------------

class PublicationStudyData(BaseModel):
    """Data for a single study in a forest plot."""

    name: str
    rate_pct: float
    ci_low_pct: float
    ci_high_pct: float
    n: int
    events: int = 0
    weight: float = 0.0
    is_pooled: bool = False


class PublicationForestPlotData(BaseModel):
    """Forest plot data for one indication group."""

    indication: str
    studies: list[PublicationStudyData]


class PublicationModelResult(BaseModel):
    """Result from a single risk estimation model."""

    model_name: str
    estimate_pct: float
    ci_low_pct: float
    ci_high_pct: float
    ci_width_pct: float
    method_type: str


class PublicationCrossValidation(BaseModel):
    """Cross-validation result for a single model."""

    model: str
    rmse_pct: float
    mae_pct: float
    coverage: float
    n_folds: int


class PublicationPriorComparison(BaseModel):
    """Prior comparison entry."""

    strategy: str
    prior_alpha: float
    prior_beta: float
    posterior_mean_pct: float
    ci_low_pct: float
    ci_high_pct: float
    ci_width_pct: float


class PublicationEvidenceAccrualPoint(BaseModel):
    """A single timepoint in the publication evidence accrual."""

    timepoint: str
    year: int
    n_cumulative: int
    events_cumulative: int
    posterior_mean_pct: float
    ci_low_pct: float
    ci_high_pct: float
    ci_width_pct: float
    is_projected: bool


class PublicationAERateRow(BaseModel):
    """A row in the AE rates comparison table."""

    indication: str
    n: int
    crs_any: str
    crs_g3: str
    icans_any: str
    icans_g3: str


class PublicationDemographicRow(BaseModel):
    """A row in the demographics table."""

    indication: str
    trial: str
    product: str
    n: int
    target: str
    year: int


class PublicationPairwiseComparison(BaseModel):
    """A pairwise statistical comparison."""

    comparison: str
    ae_type: str
    sle_rate_pct: float
    comparator_rate_pct: float
    difference_pp: float
    p_value: float
    significant: bool


class PublicationHeterogeneity(BaseModel):
    """Heterogeneity statistics for one AE type."""

    ae_type: str
    i_squared: float
    cochran_q: float
    tau_squared: float
    n_studies: int
    q_pvalue: float


class PublicationReference(BaseModel):
    """A reference from the analysis."""

    pmid: str
    citation: str


class PublicationAnalysisResponse(BaseModel):
    """Full publication analysis response."""

    request_id: str
    timestamp: datetime
    data_summary: dict[str, Any]
    model_results: list[PublicationModelResult]
    cross_validation: list[PublicationCrossValidation]
    prior_comparison: list[PublicationPriorComparison]
    pairwise_comparisons: list[PublicationPairwiseComparison]
    heterogeneity: list[PublicationHeterogeneity]
    ae_rates: list[PublicationAERateRow]
    demographics: list[PublicationDemographicRow]
    evidence_accrual_crs: list[PublicationEvidenceAccrualPoint]
    evidence_accrual_icans: list[PublicationEvidenceAccrualPoint]
    limitations: list[str]
    references: list[PublicationReference]
    key_findings: dict[str, Any]


class PublicationFigureResponse(BaseModel):
    """Response for a specific publication figure's data."""

    request_id: str
    timestamp: datetime
    figure_name: str
    figure_title: str
    data: Any


# ---------------------------------------------------------------------------
# Narrative generation schemas
# ---------------------------------------------------------------------------

class NarrativeRequest(BaseModel):
    """Request for AI narrative generation.

    Specifies which patient to generate a narrative for and optional context
    to focus the narrative on specific adverse events or scores.
    """

    patient_id: str = Field(
        ..., description="Patient identifier", min_length=1,
    )
    therapy_type: str = Field(
        "CAR-T (CD19)",
        description="Therapy modality (e.g. 'CAR-T (CD19)', 'TCR-T', 'CAR-NK')",
    )
    ae_types: list[str] = Field(
        default_factory=lambda: ["CRS", "ICANS"],
        description="Adverse event types to include in narrative",
    )
    include_mechanisms: bool = Field(
        True, description="Include mechanistic pathway context",
    )
    include_monitoring: bool = Field(
        True, description="Include recommended monitoring schedule",
    )
    risk_scores: dict[str, Any] | None = Field(
        None, description="Pre-computed risk scores to interpret (from /predict)",
    )
    lab_values: dict[str, float] | None = Field(
        None, description="Current lab values for context",
    )


class NarrativeSection(BaseModel):
    """A single section within a generated narrative."""

    title: str
    content: str
    references: list[str] = Field(default_factory=list)


class NarrativeResponse(BaseModel):
    """Response containing a structured clinical narrative.

    Generated from template-based rules with a clear interface for future
    Claude API integration. Each section can be independently reviewed.
    """

    request_id: str
    timestamp: datetime
    patient_id: str
    executive_summary: str = Field(
        description="1-2 paragraph high-level summary of the patient's risk profile",
    )
    risk_narrative: str = Field(
        description="Detailed interpretation of risk scores in clinical context",
    )
    mechanistic_context: str = Field(
        description="Biological mechanism chains relevant to this patient's therapy",
    )
    recommended_monitoring: str = Field(
        description="Monitoring recommendations based on risk profile and AE timing",
    )
    references: list[str] = Field(
        default_factory=list,
        description="PubMed citations supporting the narrative",
    )
    sections: list[NarrativeSection] = Field(
        default_factory=list,
        description="Additional structured sections",
    )
    generation_method: str = Field(
        "template_rules_v1",
        description="How the narrative was generated (template_rules_v1 or claude_api)",
    )
    disclaimer: str = Field(
        default="AI-generated interpretation. Not a substitute for clinical judgment.",
    )


class ClinicalBriefingSection(BaseModel):
    """A section within a clinical briefing document."""

    heading: str
    body: str
    data_points: dict[str, Any] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)


class ClinicalBriefing(BaseModel):
    """Comprehensive clinical briefing for a specific patient.

    Combines risk assessment, mechanistic context, population-level data,
    and monitoring recommendations into a single briefing document suitable
    for clinical team review.
    """

    request_id: str
    timestamp: datetime
    patient_id: str
    therapy_type: str
    briefing_title: str
    risk_level: str
    composite_score: float | None = None
    sections: list[ClinicalBriefingSection] = Field(default_factory=list)
    intervention_points: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Druggable targets and intervention opportunities",
    )
    timing_expectations: dict[str, str] = Field(
        default_factory=dict,
        description="Expected AE onset timing for each AE type",
    )
    key_references: list[str] = Field(default_factory=list)
    generation_method: str = "template_rules_v1"
    disclaimer: str = Field(
        default="AI-generated interpretation. Not a substitute for clinical judgment.",
    )
