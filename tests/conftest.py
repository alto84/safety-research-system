"""
Shared fixtures for PSP test suite.

Provides realistic mock data for:
- Patients at low/medium/high CRS risk
- Foundation model responses (Claude, GPT, Gemini)
- Knowledge graph pathway data
- Safety Index outputs
- Ensemble aggregation results
"""

import pytest
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from unittest.mock import MagicMock, AsyncMock
import uuid


# ---------------------------------------------------------------------------
# Enums and lightweight domain types used across tests
# ---------------------------------------------------------------------------

class Urgency(Enum):
    REALTIME = "realtime"
    NEAR_REALTIME = "near_realtime"
    BATCH = "batch"


class CostTier(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertLevel(Enum):
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


class EvidenceStrength(Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    LIMITED = "limited"


# ---------------------------------------------------------------------------
# Data classes mirroring the PSP specification
# ---------------------------------------------------------------------------

@dataclass
class TokenCount:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class SafetyQuery:
    patient_id: str
    domain: str  # "crs", "icans", "hlh"
    query_text: str
    urgency: Urgency = Urgency.BATCH
    cost_tier: CostTier = CostTier.MEDIUM
    features: dict = field(default_factory=dict)


@dataclass
class ModelEndpoint:
    model_id: str
    provider: str  # "claude", "gpt", "gemini"
    version: str
    max_latency_ms: int = 30000
    cost_per_1k_tokens: float = 0.01


@dataclass
class SafetyPrediction:
    risk_score: float
    confidence: float
    severity_distribution: dict
    time_horizon: timedelta
    mechanistic_rationale: str
    pathway_references: list
    evidence_sources: list
    model_id: str
    latency_ms: int
    token_usage: TokenCount = field(default_factory=TokenCount)


@dataclass
class EventRisk:
    probability: float
    severity_distribution: dict
    expected_onset: timedelta
    onset_ci: tuple
    mechanistic_path: list


@dataclass
class AggregatedRisk:
    risk_score: float = 0.0
    confidence_interval: tuple = (0.0, 0.0)
    contributing_models: dict = field(default_factory=dict)
    requires_human_review: bool = False
    disagreement_analysis: Optional[str] = None
    disagreement_score: float = 0.0


@dataclass
class SafetyIndex:
    overall_risk: float
    crs_risk: EventRisk
    icans_risk: EventRisk
    hlh_risk: EventRisk
    risk_trajectory: list
    peak_risk_time: timedelta
    primary_mechanism: str
    contributing_pathways: list
    key_biomarkers: list
    confidence_interval: tuple
    model_agreement: float
    evidence_strength: str
    monitoring_protocol: str
    intervention_readiness: str
    prediction_id: str
    timestamp: datetime
    model_versions: dict
    graph_version: str


@dataclass
class AuditRecord:
    prediction_id: str
    timestamp: datetime
    patient_id: str
    input_features: dict
    graph_snapshot_version: str
    model_versions: dict
    prompt_router_decision: dict
    raw_model_outputs: list
    ensemble_weights: dict
    calibration_params: dict
    final_prediction: AggregatedRisk
    mechanistic_explanation: str
    pathway_trace: list
    confidence_interval: tuple
    disagreement_score: float
    similar_historical_outcomes: list


@dataclass
class Alert:
    level: AlertLevel
    patient_id: str
    message: str
    prediction: AggregatedRisk
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


@dataclass
class RiskTrajectory:
    """Historical risk readings for a patient."""
    timestamps: list
    scores: list
    acceleration: float = 0.0  # Rate-of-change of risk score


@dataclass
class PatientData:
    """Full patient data bundle used as input to the PSP engine."""
    patient_id: str
    demographics: dict
    baseline_labs: dict
    treatment: dict
    longitudinal_labs: list  # list of dicts with timestamp + values
    genomic_features: dict
    comorbidities: list
    risk_label: str  # "low", "medium", "high" -- for test assertions


# ---------------------------------------------------------------------------
# Knowledge graph node/edge types for testing
# ---------------------------------------------------------------------------

@dataclass
class KGNode:
    node_id: str
    node_type: str  # Gene, Protein, Cytokine, Pathway, Adverse_Event, etc.
    properties: dict = field(default_factory=dict)


@dataclass
class KGEdge:
    source_id: str
    target_id: str
    edge_type: str  # ACTIVATES, PRODUCES, TRIGGERS, etc.
    properties: dict = field(default_factory=dict)


# ===========================================================================
# FIXTURES
# ===========================================================================

# ---------------------------------------------------------------------------
# Model endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def claude_endpoint():
    return ModelEndpoint(
        model_id="claude-opus-4",
        provider="claude",
        version="4.0",
        max_latency_ms=15000,
        cost_per_1k_tokens=0.015,
    )


@pytest.fixture
def gpt_endpoint():
    return ModelEndpoint(
        model_id="gpt-5.2",
        provider="gpt",
        version="5.2",
        max_latency_ms=10000,
        cost_per_1k_tokens=0.012,
    )


@pytest.fixture
def gemini_endpoint():
    return ModelEndpoint(
        model_id="gemini-3",
        provider="gemini",
        version="3.0",
        max_latency_ms=8000,
        cost_per_1k_tokens=0.008,
    )


@pytest.fixture
def all_endpoints(claude_endpoint, gpt_endpoint, gemini_endpoint):
    return [claude_endpoint, gpt_endpoint, gemini_endpoint]


# ---------------------------------------------------------------------------
# Patient fixtures at different CRS risk levels
# ---------------------------------------------------------------------------

@pytest.fixture
def low_risk_patient():
    """Low CRS risk: low tumor burden, normal baseline cytokines, no risk factors."""
    return PatientData(
        patient_id="PSP-TEST-LOW-001",
        demographics={"age": 45, "sex": "F", "bmi": 24.1, "race": "white"},
        baseline_labs={
            "crp_mg_l": 3.2,           # Normal (<10)
            "ferritin_ng_ml": 120.0,    # Normal (20-200)
            "il6_pg_ml": 2.1,           # Normal (<7)
            "ldh_u_l": 180.0,           # Normal (140-280)
            "fibrinogen_mg_dl": 290.0,  # Normal (200-400)
            "il10_pg_ml": 1.5,
            "ifn_gamma_pg_ml": 3.0,
            "tnf_alpha_pg_ml": 4.5,
            "wbc_k_ul": 6.8,
            "platelets_k_ul": 210.0,
        },
        treatment={
            "product": "axi-cel",
            "dose_cells": 2e6,  # cells/kg
            "bridging_therapy": "none",
            "lymphodepletion": "flu_cy",
        },
        longitudinal_labs=[
            {
                "hours_post_infusion": 0,
                "il6_pg_ml": 2.1,
                "ifn_gamma_pg_ml": 3.0,
                "crp_mg_l": 3.2,
                "ferritin_ng_ml": 120.0,
                "temperature_c": 36.8,
            },
            {
                "hours_post_infusion": 24,
                "il6_pg_ml": 8.5,
                "ifn_gamma_pg_ml": 12.0,
                "crp_mg_l": 15.0,
                "ferritin_ng_ml": 180.0,
                "temperature_c": 37.2,
            },
            {
                "hours_post_infusion": 48,
                "il6_pg_ml": 12.0,
                "ifn_gamma_pg_ml": 18.0,
                "crp_mg_l": 22.0,
                "ferritin_ng_ml": 210.0,
                "temperature_c": 37.5,
            },
        ],
        genomic_features={
            "hla_type": "A*02:01",
            "il6_polymorphism": "GG",  # Wild type
            "tnf_alpha_polymorphism": "GG",
        },
        comorbidities=[],
        risk_label="low",
    )


@pytest.fixture
def medium_risk_patient():
    """Medium CRS risk: moderate tumor burden, mildly elevated cytokines."""
    return PatientData(
        patient_id="PSP-TEST-MED-001",
        demographics={"age": 62, "sex": "M", "bmi": 29.3, "race": "black"},
        baseline_labs={
            "crp_mg_l": 18.5,          # Mildly elevated
            "ferritin_ng_ml": 450.0,    # Elevated
            "il6_pg_ml": 12.3,          # Elevated (>7)
            "ldh_u_l": 380.0,           # Elevated (>280)
            "fibrinogen_mg_dl": 480.0,  # Mildly elevated
            "il10_pg_ml": 4.8,
            "ifn_gamma_pg_ml": 15.0,
            "tnf_alpha_pg_ml": 12.0,
            "wbc_k_ul": 3.2,           # Leukopenic
            "platelets_k_ul": 95.0,    # Low
        },
        treatment={
            "product": "tisa-cel",
            "dose_cells": 3.5e6,
            "bridging_therapy": "dexamethasone",
            "lymphodepletion": "flu_cy",
        },
        longitudinal_labs=[
            {
                "hours_post_infusion": 0,
                "il6_pg_ml": 12.3,
                "ifn_gamma_pg_ml": 15.0,
                "crp_mg_l": 18.5,
                "ferritin_ng_ml": 450.0,
                "temperature_c": 37.0,
            },
            {
                "hours_post_infusion": 24,
                "il6_pg_ml": 85.0,
                "ifn_gamma_pg_ml": 120.0,
                "crp_mg_l": 65.0,
                "ferritin_ng_ml": 1200.0,
                "temperature_c": 38.5,
            },
            {
                "hours_post_infusion": 48,
                "il6_pg_ml": 250.0,
                "ifn_gamma_pg_ml": 380.0,
                "crp_mg_l": 120.0,
                "ferritin_ng_ml": 2800.0,
                "temperature_c": 39.2,
            },
        ],
        genomic_features={
            "hla_type": "A*03:01",
            "il6_polymorphism": "GC",  # Heterozygous
            "tnf_alpha_polymorphism": "GA",
        },
        comorbidities=["hypertension", "prior_crs_grade1"],
        risk_label="medium",
    )


@pytest.fixture
def high_risk_patient():
    """High CRS risk: high tumor burden, markedly elevated baseline cytokines, prior CRS."""
    return PatientData(
        patient_id="PSP-TEST-HIGH-001",
        demographics={"age": 71, "sex": "M", "bmi": 32.0, "race": "asian"},
        baseline_labs={
            "crp_mg_l": 85.0,           # Markedly elevated
            "ferritin_ng_ml": 2200.0,    # Markedly elevated
            "il6_pg_ml": 48.0,           # Markedly elevated
            "ldh_u_l": 620.0,            # Markedly elevated
            "fibrinogen_mg_dl": 680.0,   # Elevated
            "il10_pg_ml": 22.0,
            "ifn_gamma_pg_ml": 55.0,
            "tnf_alpha_pg_ml": 38.0,
            "wbc_k_ul": 1.8,            # Severely leukopenic
            "platelets_k_ul": 45.0,     # Thrombocytopenic
        },
        treatment={
            "product": "axi-cel",
            "dose_cells": 5e6,
            "bridging_therapy": "bendamustine",
            "lymphodepletion": "flu_cy_high",
        },
        longitudinal_labs=[
            {
                "hours_post_infusion": 0,
                "il6_pg_ml": 48.0,
                "ifn_gamma_pg_ml": 55.0,
                "crp_mg_l": 85.0,
                "ferritin_ng_ml": 2200.0,
                "temperature_c": 37.4,
            },
            {
                "hours_post_infusion": 12,
                "il6_pg_ml": 520.0,
                "ifn_gamma_pg_ml": 680.0,
                "crp_mg_l": 180.0,
                "ferritin_ng_ml": 5500.0,
                "temperature_c": 39.8,
            },
            {
                "hours_post_infusion": 24,
                "il6_pg_ml": 2800.0,
                "ifn_gamma_pg_ml": 1500.0,
                "crp_mg_l": 320.0,
                "ferritin_ng_ml": 12000.0,
                "temperature_c": 40.2,
            },
            {
                "hours_post_infusion": 48,
                "il6_pg_ml": 5200.0,
                "ifn_gamma_pg_ml": 2100.0,
                "crp_mg_l": 410.0,
                "ferritin_ng_ml": 18000.0,
                "temperature_c": 40.5,
            },
        ],
        genomic_features={
            "hla_type": "B*46:01",
            "il6_polymorphism": "CC",  # Homozygous variant -- higher IL-6 expression
            "tnf_alpha_polymorphism": "AA",
        },
        comorbidities=[
            "diabetes_type2",
            "prior_crs_grade3",
            "cardiac_arrhythmia",
            "renal_impairment_moderate",
        ],
        risk_label="high",
    )


# ---------------------------------------------------------------------------
# Mock model responses
# ---------------------------------------------------------------------------

@pytest.fixture
def claude_crs_prediction_low():
    """Claude prediction for a low-risk patient."""
    return SafetyPrediction(
        risk_score=0.12,
        confidence=0.88,
        severity_distribution={
            "grade_1": 0.70,
            "grade_2": 0.20,
            "grade_3": 0.08,
            "grade_4": 0.02,
        },
        time_horizon=timedelta(hours=72),
        mechanistic_rationale=(
            "Low baseline IL-6 and CRP suggest minimal pre-existing inflammatory "
            "activation. Normal ferritin and LDH indicate low tumor burden. The "
            "IL-6 trajectory post-infusion shows modest rise consistent with "
            "Grade 1 CRS. No amplification loop activation predicted."
        ),
        pathway_references=["pathway:crs_grade1_self_limiting"],
        evidence_sources=["baseline_il6", "baseline_crp", "tumor_burden_low"],
        model_id="claude-opus-4",
        latency_ms=3200,
        token_usage=TokenCount(prompt_tokens=2800, completion_tokens=450, total_tokens=3250),
    )


@pytest.fixture
def gpt_crs_prediction_low():
    """GPT prediction for a low-risk patient."""
    return SafetyPrediction(
        risk_score=0.15,
        confidence=0.82,
        severity_distribution={
            "grade_1": 0.65,
            "grade_2": 0.25,
            "grade_3": 0.08,
            "grade_4": 0.02,
        },
        time_horizon=timedelta(hours=60),
        mechanistic_rationale=(
            "Based on feature analysis: baseline inflammatory markers within "
            "normal range, no high-risk genomic variants detected. Predicted "
            "mild cytokine elevation without endothelial activation cascade."
        ),
        pathway_references=["pathway:crs_grade1_self_limiting"],
        evidence_sources=["baseline_labs_normal", "genomic_low_risk"],
        model_id="gpt-5.2",
        latency_ms=1800,
        token_usage=TokenCount(prompt_tokens=2400, completion_tokens=380, total_tokens=2780),
    )


@pytest.fixture
def gemini_crs_prediction_low():
    """Gemini prediction for a low-risk patient."""
    return SafetyPrediction(
        risk_score=0.10,
        confidence=0.85,
        severity_distribution={
            "grade_1": 0.75,
            "grade_2": 0.18,
            "grade_3": 0.05,
            "grade_4": 0.02,
        },
        time_horizon=timedelta(hours=68),
        mechanistic_rationale=(
            "Multi-modal analysis: labs normal, no high-risk phenotype. "
            "Low probability of IL-6 trans-signaling activation."
        ),
        pathway_references=["pathway:crs_grade1_self_limiting"],
        evidence_sources=["baseline_il6", "cytokine_kinetics_mild"],
        model_id="gemini-3",
        latency_ms=1500,
        token_usage=TokenCount(prompt_tokens=2200, completion_tokens=300, total_tokens=2500),
    )


@pytest.fixture
def claude_crs_prediction_high():
    """Claude prediction for a high-risk patient."""
    return SafetyPrediction(
        risk_score=0.82,
        confidence=0.91,
        severity_distribution={
            "grade_1": 0.05,
            "grade_2": 0.15,
            "grade_3": 0.45,
            "grade_4": 0.35,
        },
        time_horizon=timedelta(hours=36),
        mechanistic_rationale=(
            "Markedly elevated baseline IL-6 (48 pg/mL) and ferritin (2200 ng/mL) "
            "indicate high pre-existing inflammatory burden. Explosive IL-6 rise "
            "to 520 pg/mL within 12h post-infusion strongly suggests activation "
            "of the IL-6 trans-signaling amplification loop via sIL-6R. Prior "
            "Grade 3 CRS history and CC genotype at IL-6 locus compound risk. "
            "Endothelial activation and vascular leak highly probable."
        ),
        pathway_references=[
            "pathway:il6_trans_signaling",
            "pathway:endothelial_activation",
            "pathway:macrophage_activation_syndrome",
        ],
        evidence_sources=[
            "baseline_il6_critical",
            "ferritin_critical",
            "il6_kinetics_explosive",
            "prior_crs_grade3",
            "il6_polymorphism_CC",
        ],
        model_id="claude-opus-4",
        latency_ms=4500,
        token_usage=TokenCount(prompt_tokens=3500, completion_tokens=620, total_tokens=4120),
    )


@pytest.fixture
def gpt_crs_prediction_high():
    """GPT prediction for a high-risk patient."""
    return SafetyPrediction(
        risk_score=0.78,
        confidence=0.87,
        severity_distribution={
            "grade_1": 0.05,
            "grade_2": 0.18,
            "grade_3": 0.42,
            "grade_4": 0.35,
        },
        time_horizon=timedelta(hours=30),
        mechanistic_rationale=(
            "High tumor burden markers (LDH 620, ferritin 2200) combined with "
            "rapid cytokine rise pattern predict severe CRS. IL-6 doubling time "
            "<6h is consistent with amplification loop engagement."
        ),
        pathway_references=[
            "pathway:il6_trans_signaling",
            "pathway:endothelial_activation",
        ],
        evidence_sources=[
            "ldh_elevated",
            "ferritin_critical",
            "il6_doubling_time_short",
        ],
        model_id="gpt-5.2",
        latency_ms=2200,
        token_usage=TokenCount(prompt_tokens=3000, completion_tokens=420, total_tokens=3420),
    )


@pytest.fixture
def gemini_crs_prediction_high():
    """Gemini prediction for a high-risk patient."""
    return SafetyPrediction(
        risk_score=0.75,
        confidence=0.83,
        severity_distribution={
            "grade_1": 0.08,
            "grade_2": 0.17,
            "grade_3": 0.40,
            "grade_4": 0.35,
        },
        time_horizon=timedelta(hours=42),
        mechanistic_rationale=(
            "Multi-modal risk assessment: extremely elevated baseline inflammatory "
            "markers, aggressive cytokine kinetics, genomic susceptibility profile."
        ),
        pathway_references=[
            "pathway:il6_trans_signaling",
            "pathway:macrophage_activation_syndrome",
        ],
        evidence_sources=[
            "baseline_il6_critical",
            "cytokine_kinetics_explosive",
            "genomic_risk_high",
        ],
        model_id="gemini-3",
        latency_ms=1800,
        token_usage=TokenCount(prompt_tokens=2800, completion_tokens=350, total_tokens=3150),
    )


@pytest.fixture
def disagreeing_predictions():
    """Model predictions that substantially disagree -- should trigger human review."""
    return [
        SafetyPrediction(
            risk_score=0.85,
            confidence=0.90,
            severity_distribution={"grade_1": 0.05, "grade_2": 0.10, "grade_3": 0.50, "grade_4": 0.35},
            time_horizon=timedelta(hours=24),
            mechanistic_rationale="Explosive cytokine cascade predicted.",
            pathway_references=["pathway:il6_trans_signaling"],
            evidence_sources=["il6_critical"],
            model_id="claude-opus-4",
            latency_ms=3500,
        ),
        SafetyPrediction(
            risk_score=0.30,
            confidence=0.75,
            severity_distribution={"grade_1": 0.45, "grade_2": 0.35, "grade_3": 0.15, "grade_4": 0.05},
            time_horizon=timedelta(hours=72),
            mechanistic_rationale="Moderate inflammatory response expected.",
            pathway_references=["pathway:crs_grade1_self_limiting"],
            evidence_sources=["baseline_labs"],
            model_id="gpt-5.2",
            latency_ms=1900,
        ),
        SafetyPrediction(
            risk_score=0.42,
            confidence=0.60,
            severity_distribution={"grade_1": 0.30, "grade_2": 0.35, "grade_3": 0.25, "grade_4": 0.10},
            time_horizon=timedelta(hours=48),
            mechanistic_rationale="Uncertain trajectory; mixed signals.",
            pathway_references=["pathway:crs_mixed"],
            evidence_sources=["mixed_signals"],
            model_id="gemini-3",
            latency_ms=1600,
        ),
    ]


# ---------------------------------------------------------------------------
# Ensemble / Aggregated Risk fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def low_risk_aggregated():
    return AggregatedRisk(
        risk_score=0.12,
        confidence_interval=(0.06, 0.20),
        contributing_models={"claude-opus-4": 0.45, "gpt-5.2": 0.30, "gemini-3": 0.25},
        requires_human_review=False,
        disagreement_score=0.04,
    )


@pytest.fixture
def high_risk_aggregated():
    return AggregatedRisk(
        risk_score=0.79,
        confidence_interval=(0.70, 0.88),
        contributing_models={"claude-opus-4": 0.45, "gpt-5.2": 0.30, "gemini-3": 0.25},
        requires_human_review=False,
        disagreement_score=0.06,
    )


@pytest.fixture
def review_required_aggregated():
    return AggregatedRisk(
        risk_score=0.52,
        confidence_interval=(0.28, 0.76),
        contributing_models={"claude-opus-4": 0.45, "gpt-5.2": 0.30, "gemini-3": 0.25},
        requires_human_review=True,
        disagreement_analysis="Claude predicts Grade 3+ (0.85) while GPT predicts Grade 1 (0.30). "
                              "55-point risk score divergence exceeds review threshold.",
        disagreement_score=0.55,
    )


# ---------------------------------------------------------------------------
# Knowledge graph fixtures (CRS pathway)
# ---------------------------------------------------------------------------

@pytest.fixture
def crs_pathway_nodes():
    """Core nodes for the CRS mechanistic pathway."""
    return [
        KGNode("node:cart_cell", "Cell_Type", {"name": "CAR-T Cell", "lineage": "T_lymphocyte"}),
        KGNode("node:t_cell_expansion", "Pathway", {"name": "T Cell Expansion", "trigger": "antigen_recognition"}),
        KGNode("node:ifn_gamma", "Cytokine", {"name": "IFN-gamma", "normal_range_pg_ml": (0, 15)}),
        KGNode("node:macrophage", "Cell_Type", {"name": "Macrophage", "lineage": "myeloid"}),
        KGNode("node:macrophage_activation", "Pathway", {"name": "Macrophage Activation"}),
        KGNode("node:il6", "Cytokine", {"name": "IL-6", "normal_range_pg_ml": (0, 7)}),
        KGNode("node:sil6r", "Receptor", {"name": "sIL-6R", "signaling": "trans"}),
        KGNode("node:endothelial_activation", "Pathway", {"name": "Endothelial Activation"}),
        KGNode("node:vascular_leak", "Adverse_Event", {"meddra_term": "Capillary leak syndrome", "severity_grades": [1, 2, 3, 4]}),
        KGNode("node:crs", "Adverse_Event", {"meddra_term": "Cytokine release syndrome", "severity_grades": [1, 2, 3, 4]}),
        KGNode("node:tocilizumab", "Drug", {"name": "Tocilizumab", "target": "IL-6R", "mechanism": "receptor_blockade"}),
        KGNode("node:ferritin", "Biomarker", {"name": "Ferritin", "measurement_type": "serum", "prognostic_value": "high"}),
        KGNode("node:crp", "Biomarker", {"name": "CRP", "measurement_type": "serum", "prognostic_value": "moderate"}),
    ]


@pytest.fixture
def crs_pathway_edges():
    """Edges forming the CRS cascade."""
    return [
        KGEdge("node:cart_cell", "node:t_cell_expansion", "ACTIVATES", {"weight": 0.95, "evidence_count": 120}),
        KGEdge("node:t_cell_expansion", "node:ifn_gamma", "PRODUCES", {"conditions": "antigen_encounter", "rate": "high"}),
        KGEdge("node:ifn_gamma", "node:macrophage_activation", "ACTIVATES", {"weight": 0.90, "evidence_count": 85}),
        KGEdge("node:macrophage_activation", "node:il6", "PRODUCES", {"conditions": "ifn_gamma_stimulation", "rate": "very_high"}),
        KGEdge("node:il6", "node:sil6r", "BINDS", {"affinity": "high", "signaling_type": "trans"}),
        KGEdge("node:sil6r", "node:endothelial_activation", "ACTIVATES", {"weight": 0.85, "evidence_count": 45}),
        KGEdge("node:endothelial_activation", "node:il6", "PRODUCES", {"amplification_factor": 3.5, "delay_hours": 4}),
        KGEdge("node:endothelial_activation", "node:vascular_leak", "TRIGGERS", {"threshold": "severe", "time_to_onset_hours": 8}),
        KGEdge("node:vascular_leak", "node:crs", "MANIFESTS_AS", {"grade": "3+"}),
        KGEdge("node:tocilizumab", "node:sil6r", "INHIBITS", {"ic50_nm": 2.5, "selectivity": "high"}),
        KGEdge("node:ferritin", "node:crs", "CORRELATES_WITH", {"correlation": 0.72, "p_value": 0.001}),
        KGEdge("node:crp", "node:crs", "CORRELATES_WITH", {"correlation": 0.58, "p_value": 0.005}),
    ]


# ---------------------------------------------------------------------------
# Safety Index fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def low_risk_safety_index():
    return SafetyIndex(
        overall_risk=0.12,
        crs_risk=EventRisk(
            probability=0.10,
            severity_distribution={"grade_1": 0.70, "grade_2": 0.20, "grade_3": 0.08, "grade_4": 0.02},
            expected_onset=timedelta(hours=48),
            onset_ci=(timedelta(hours=24), timedelta(hours=96)),
            mechanistic_path=["node:cart_cell", "node:t_cell_expansion", "node:ifn_gamma"],
        ),
        icans_risk=EventRisk(
            probability=0.05,
            severity_distribution={"grade_1": 0.80, "grade_2": 0.15, "grade_3": 0.04, "grade_4": 0.01},
            expected_onset=timedelta(hours=120),
            onset_ci=(timedelta(hours=72), timedelta(hours=168)),
            mechanistic_path=["node:bbb_disruption"],
        ),
        hlh_risk=EventRisk(
            probability=0.02,
            severity_distribution={"grade_1": 0.0, "grade_2": 0.0, "grade_3": 0.60, "grade_4": 0.40},
            expected_onset=timedelta(hours=168),
            onset_ci=(timedelta(hours=96), timedelta(hours=240)),
            mechanistic_path=["node:macrophage_activation", "node:hlh_cascade"],
        ),
        risk_trajectory=[0.08, 0.10, 0.12, 0.11, 0.09, 0.07],
        peak_risk_time=timedelta(hours=48),
        primary_mechanism="Self-limiting T-cell expansion with controlled cytokine release",
        contributing_pathways=["pathway:crs_grade1_self_limiting"],
        key_biomarkers=["il6_baseline_low", "ferritin_normal", "crp_normal", "ldh_normal", "tumor_burden_low"],
        confidence_interval=(0.06, 0.20),
        model_agreement=0.92,
        evidence_strength="strong",
        monitoring_protocol="Standard q12h vitals and daily cytokine panel",
        intervention_readiness="Tocilizumab available per institutional protocol",
        prediction_id=str(uuid.uuid4()),
        timestamp=datetime(2026, 2, 6, 10, 0, 0),
        model_versions={"claude-opus-4": "4.0", "gpt-5.2": "5.2", "gemini-3": "3.0"},
        graph_version="kg-v1.2.0",
    )


@pytest.fixture
def high_risk_safety_index():
    return SafetyIndex(
        overall_risk=0.82,
        crs_risk=EventRisk(
            probability=0.79,
            severity_distribution={"grade_1": 0.05, "grade_2": 0.15, "grade_3": 0.45, "grade_4": 0.35},
            expected_onset=timedelta(hours=18),
            onset_ci=(timedelta(hours=8), timedelta(hours=36)),
            mechanistic_path=[
                "node:cart_cell",
                "node:t_cell_expansion",
                "node:ifn_gamma",
                "node:macrophage_activation",
                "node:il6",
                "node:sil6r",
                "node:endothelial_activation",
                "node:vascular_leak",
                "node:crs",
            ],
        ),
        icans_risk=EventRisk(
            probability=0.45,
            severity_distribution={"grade_1": 0.20, "grade_2": 0.30, "grade_3": 0.35, "grade_4": 0.15},
            expected_onset=timedelta(hours=96),
            onset_ci=(timedelta(hours=48), timedelta(hours=168)),
            mechanistic_path=["node:bbb_disruption", "node:neurotoxicity_cascade"],
        ),
        hlh_risk=EventRisk(
            probability=0.25,
            severity_distribution={"grade_1": 0.0, "grade_2": 0.0, "grade_3": 0.55, "grade_4": 0.45},
            expected_onset=timedelta(hours=72),
            onset_ci=(timedelta(hours=48), timedelta(hours=120)),
            mechanistic_path=["node:macrophage_activation", "node:hlh_cascade"],
        ),
        risk_trajectory=[0.45, 0.62, 0.78, 0.85, 0.82, 0.75],
        peak_risk_time=timedelta(hours=36),
        primary_mechanism="IL-6 trans-signaling amplification loop with endothelial activation",
        contributing_pathways=[
            "pathway:il6_trans_signaling",
            "pathway:endothelial_activation",
            "pathway:macrophage_activation_syndrome",
        ],
        key_biomarkers=[
            "il6_baseline_critical",
            "ferritin_critical",
            "il6_kinetics_explosive",
            "prior_crs_grade3",
            "il6_polymorphism_CC",
        ],
        confidence_interval=(0.70, 0.90),
        model_agreement=0.88,
        evidence_strength="strong",
        monitoring_protocol="Continuous vitals, q4h cytokine panel, ICU standby",
        intervention_readiness="Tocilizumab and dexamethasone at bedside, vasopressor access",
        prediction_id=str(uuid.uuid4()),
        timestamp=datetime(2026, 2, 6, 10, 0, 0),
        model_versions={"claude-opus-4": "4.0", "gpt-5.2": "5.2", "gemini-3": "3.0"},
        graph_version="kg-v1.2.0",
    )


# ---------------------------------------------------------------------------
# Audit record fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_audit_record(high_risk_patient, high_risk_aggregated):
    return AuditRecord(
        prediction_id=str(uuid.uuid4()),
        timestamp=datetime(2026, 2, 6, 10, 0, 0),
        patient_id="PSP-TEST-HIGH-001",
        input_features=high_risk_patient.baseline_labs,
        graph_snapshot_version="kg-v1.2.0",
        model_versions={"claude-opus-4": "4.0", "gpt-5.2": "5.2", "gemini-3": "3.0"},
        prompt_router_decision={"selected": "claude-opus-4", "reason": "high_complexity_mechanistic_query"},
        raw_model_outputs=["<raw claude response>", "<raw gpt response>", "<raw gemini response>"],
        ensemble_weights={"claude-opus-4": 0.45, "gpt-5.2": 0.30, "gemini-3": 0.25},
        calibration_params={"platt_a": -1.2, "platt_b": 0.3},
        final_prediction=high_risk_aggregated,
        mechanistic_explanation="IL-6 trans-signaling amplification loop with endothelial activation",
        pathway_trace=["node:cart_cell", "node:il6", "node:sil6r", "node:endothelial_activation", "node:crs"],
        confidence_interval=(0.70, 0.88),
        disagreement_score=0.06,
        similar_historical_outcomes=[
            {"patient_id": "HIST-001", "outcome": "CRS Grade 3", "similarity": 0.91},
            {"patient_id": "HIST-002", "outcome": "CRS Grade 4", "similarity": 0.87},
        ],
    )


# ---------------------------------------------------------------------------
# Risk trajectory fixture for alert testing
# ---------------------------------------------------------------------------

@pytest.fixture
def stable_low_trajectory():
    return RiskTrajectory(
        timestamps=[datetime(2026, 2, 6, h, 0, 0) for h in range(0, 12)],
        scores=[0.10, 0.11, 0.10, 0.12, 0.11, 0.10, 0.10, 0.11, 0.12, 0.11, 0.10, 0.10],
        acceleration=0.001,
    )


@pytest.fixture
def rapidly_rising_trajectory():
    return RiskTrajectory(
        timestamps=[datetime(2026, 2, 6, h, 0, 0) for h in range(0, 12)],
        scores=[0.20, 0.25, 0.32, 0.40, 0.50, 0.58, 0.65, 0.72, 0.78, 0.82, 0.85, 0.87],
        acceleration=0.06,  # ~6% per hour
    )


# ---------------------------------------------------------------------------
# Safety query fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def simple_screening_query():
    return SafetyQuery(
        patient_id="PSP-TEST-LOW-001",
        domain="crs",
        query_text="Assess CRS risk based on baseline labs for pre-screening.",
        urgency=Urgency.BATCH,
        cost_tier=CostTier.LOW,
        features={"baseline_only": True},
    )


@pytest.fixture
def complex_mechanistic_query():
    return SafetyQuery(
        patient_id="PSP-TEST-HIGH-001",
        domain="crs",
        query_text=(
            "Patient shows explosive IL-6 rise (48 -> 520 -> 2800 pg/mL over 24h) "
            "with concurrent ferritin > 12000 ng/mL. Assess probability and timing "
            "of Grade 3+ CRS via IL-6 trans-signaling pathway analysis. Include "
            "mechanistic reasoning for tocilizumab intervention timing."
        ),
        urgency=Urgency.REALTIME,
        cost_tier=CostTier.HIGH,
        features={"longitudinal": True, "mechanistic_depth": "full"},
    )


@pytest.fixture
def realtime_monitoring_query():
    return SafetyQuery(
        patient_id="PSP-TEST-MED-001",
        domain="crs",
        query_text="Updated cytokine panel received. Re-evaluate CRS risk trajectory.",
        urgency=Urgency.REALTIME,
        cost_tier=CostTier.MEDIUM,
        features={"longitudinal": True},
    )
