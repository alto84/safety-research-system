"""
Patient Safety Dashboard API routes.

Provides comprehensive pharmacovigilance and patient safety endpoints
for Prosinertimib, a fictional EGFR inhibitor for NSCLC.

All data is fictional and for demonstration purposes only.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/psd",
    tags=["Patient Safety Dashboard"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RAGStatus(str, Enum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"


class KPI(BaseModel):
    name: str
    value: Any
    target: Any
    unit: str = ""
    rag: RAGStatus
    trend: str = "stable"
    description: str = ""


class GovernanceBody(BaseModel):
    name: str
    abbreviation: str
    chair: str
    frequency: str
    last_meeting: str
    next_meeting: str
    members: int
    charter_status: str



class OverviewResponse(BaseModel):
    request_id: str
    timestamp: datetime
    organization: dict[str, Any]
    governance_bodies: list[GovernanceBody]
    operating_model: dict[str, Any]
    product_portfolio: list[dict[str, Any]]


class ComplianceItem(BaseModel):
    regulation: str
    description: str
    status: RAGStatus
    last_assessment: str
    next_assessment: str
    findings: int = 0
    notes: str = ""


class ReportingTimeline(BaseModel):
    report_type: str
    regulation: str
    target_days: int
    compliance_rate: float
    total_submitted: int
    on_time: int
    late: int
    pending: int


class FDAAction(BaseModel):
    date: str
    action_type: str
    reference: str
    description: str
    status: str
    response_due: Optional[str] = None


class USComplianceResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    nda_number: str
    approval_date: str
    compliance_items: list[ComplianceItem]
    reporting_timelines: list[ReportingTimeline]
    fda_actions: list[FDAAction]
    overall_status: RAGStatus
    summary: dict[str, Any]


class GVPModuleCompliance(BaseModel):
    module: str
    title: str
    status: RAGStatus
    last_audit: str
    findings_open: int
    findings_closed: int
    notes: str = ""


class EudraVigilanceStats(BaseModel):
    period: str
    icsr_submitted: int
    icsr_accepted: int
    icsr_rejected: int
    rejection_rate: float
    average_submission_days: float


class QPPVNetwork(BaseModel):
    role: str
    name: str
    country: str
    qualification: str
    status: str
    last_training: str


class EUComplianceResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    eu_number: str
    ma_holder: str
    centralized_procedure_number: str
    gvp_modules: list[GVPModuleCompliance]
    eudravigilance_stats: list[EudraVigilanceStats]
    qppv_network: list[QPPVNetwork]
    psmf: dict[str, Any]
    overall_status: RAGStatus


class CaseVolume(BaseModel):
    category: str
    count: int
    percentage: float


class PipelineStage(BaseModel):
    stage: str
    count: int
    avg_days: float
    target_days: float
    status: RAGStatus


class ICSRResponse(BaseModel):
    request_id: str
    timestamp: datetime
    reporting_period: str
    total_cases: int
    case_volumes_by_source: list[CaseVolume]
    case_volumes_by_seriousness: list[CaseVolume]
    case_volumes_by_status: list[CaseVolume]
    pipeline_metrics: list[PipelineStage]
    compliance_rates: dict[str, Any]
    backlog: dict[str, Any]
    trending: dict[str, Any]


class SignalItem(BaseModel):
    signal_id: str
    term: str
    soc: str
    source: str
    detection_date: str
    prr: Optional[float] = None
    ror: Optional[float] = None
    ebgm: Optional[float] = None
    ebgm_lower: Optional[float] = None
    case_count: int
    status: str
    priority: str
    assigned_to: str
    next_review: str
    assessment_summary: str = ""


class SignalsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    total_signals: int
    active_signals: list[SignalItem]
    pipeline_summary: dict[str, Any]
    recent_assessments: list[dict[str, Any]]
    detection_methods: list[dict[str, Any]]


class AggregateReport(BaseModel):
    report_type: str
    report_name: str
    data_lock_point: str
    submission_due: str
    regulatory_authority: str
    status: str
    progress_pct: float
    assigned_lead: str
    reviewer: str
    sections_complete: int
    sections_total: int
    notes: str = ""


class AggregateReportsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    reports: list[AggregateReport]
    calendar_year: int
    upcoming_deadlines: list[dict[str, Any]]


class RMPCommitment(BaseModel):
    commitment_id: str
    description: str
    type: str
    due_date: str
    status: str
    regulatory_authority: str
    last_update: str


class REMSElement(BaseModel):
    element: str
    description: str
    compliance_rate: float
    target_rate: float
    status: RAGStatus
    last_assessment: str


class RiskManagementResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    rmp: dict[str, Any]
    rmp_commitments: list[RMPCommitment]
    rems: dict[str, Any]
    rems_elements: list[REMSElement]
    risk_minimization_effectiveness: list[dict[str, Any]]


class SOPItem(BaseModel):
    sop_id: str
    title: str
    version: str
    effective_date: str
    review_due: str
    owner: str
    status: RAGStatus


class CAPAItem(BaseModel):
    capa_id: str
    title: str
    source: str
    category: str
    priority: str
    opened_date: str
    due_date: str
    status: str
    assigned_to: str
    root_cause: str = ""
    overdue: bool = False


class TrainingRecord(BaseModel):
    role: str
    total_staff: int
    compliant: int
    compliance_rate: float
    overdue_count: int
    status: RAGStatus


class QualityResponse(BaseModel):
    request_id: str
    timestamp: datetime
    sop_inventory: list[SOPItem]
    capa_tracker: dict[str, Any]
    capa_items: list[CAPAItem]
    training_compliance: list[TrainingRecord]
    audits_inspections: list[dict[str, Any]]
    quality_metrics: dict[str, Any]


class ClinicalTrial(BaseModel):
    trial_id: str
    protocol_number: str
    title: str
    phase: str
    status: str
    indication: str
    target_enrollment: int
    current_enrollment: int
    sites_active: int
    sae_count: int
    susar_count: int
    last_sae_date: Optional[str] = None
    dsmb_next: str
    ib_version: str
    ib_next_update: str


class ClinicalTrialsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    trials: list[ClinicalTrial]
    dsmb_calendar: list[dict[str, Any]]
    susar_summary: dict[str, Any]
    safety_review_schedule: list[dict[str, Any]]


class KPIsResponse(BaseModel):
    request_id: str
    timestamp: datetime
    compliance_kpis: list[KPI]
    quality_kpis: list[KPI]
    signal_kpis: list[KPI]
    portfolio_health_kpis: list[KPI]
    overall_rag: RAGStatus
    kpi_count: dict[str, int]


class EffectsTableRow(BaseModel):
    effect: str
    category: str
    prosinertimib_rate: str
    comparator_rate: str
    relative_effect: str
    certainty: str
    importance: str


class BenefitRiskResponse(BaseModel):
    request_id: str
    timestamp: datetime
    product: str
    indication: str
    benefit_risk_summary: dict[str, Any]
    labeling_status: dict[str, Any]
    effects_table: list[EffectsTableRow]
    key_benefits: list[dict[str, Any]]
    key_risks: list[dict[str, Any]]
    overall_benefit_risk_conclusion: str


class AIChainStage(BaseModel):
    stage: int
    name: str
    status: str
    component: str
    detail: str


class Hypothesis(BaseModel):
    id: str
    signal_ref: str
    title: str
    hypothesis: str
    mechanism: str
    biological_plausibility: str
    confidence: float
    evidence_for: list[dict]
    evidence_against: list[dict]
    status: str
    generated_date: str
    next_steps: list[str]


class ClassComparator(BaseModel):
    drug: str
    generation: str
    cardiac_risk: str
    ild_risk: str
    skin_rash: str
    diarrhea: str
    hepatotox: str
    status: str


class MechanisticAnalysis(BaseModel):
    signal_id: str
    signal_name: str
    biological_plausibility: str
    pathway_summary: str
    pathway_steps: list[dict]
    class_precedent: list[dict]
    unique_risk_factors: str
    monitoring_recommendation: str


class TherapeuticAreaContext(BaseModel):
    disease: str
    drug_class: str
    mechanism_of_action: str
    generation: str
    approved_indication: str
    treatment_landscape: list[dict]
    unmet_need: str
    five_year_survival: str
    patient_population: str


class AIIntelligenceResponse(BaseModel):
    request_id: str
    timestamp: str
    product: str
    therapeutic_area: TherapeuticAreaContext
    ai_chain: dict
    active_hypotheses: list[Hypothesis]
    mechanistic_analysis: MechanisticAnalysis
    drug_class_comparison: list[ClassComparator]
    ai_insights_summary: dict


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------

def _make_request_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. GET /overview
# ---------------------------------------------------------------------------

@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Organization overview",
    description=(
        "Returns organizational chart, governance bodies, operating model, "
        "and product portfolio for the Patient Safety function."
    ),
)
async def get_overview() -> OverviewResponse:
    """Return org chart, governance, and operating model."""
    org_roles = [
        {
            "role": "Chief Medical Officer",
            "name": "Chief Medical Officer",
            "reports_to": "CEO",
            "department": "Medical",
            "location": "Cambridge, MA",
            "fte_direct_reports": 6,
        },
        {
            "role": "Head of Patient Safety / Pharmacovigilance",
            "name": "Head of Patient Safety",
            "reports_to": "Chief Medical Officer",
            "department": "Patient Safety",
            "location": "Basel, Switzerland",
            "fte_direct_reports": 7,
        },
        {
            "role": "QPPV (EU)",
            "name": "QPPV (EU)",
            "reports_to": "Head of Patient Safety / Pharmacovigilance (solid); CMO (dotted-line)",
            "department": "Patient Safety",
            "location": "Dublin, Ireland",
            "fte_direct_reports": 0,
        },
        {
            "role": "Director, Signal Management & Safety Science",
            "name": "Director, Signal Management & Safety Science",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "Signal Management & Safety Science",
            "location": "Lisbon, Portugal",
            "fte_direct_reports": 8,
        },
        {
            "role": "Associate Director, PV Operations",
            "name": "Associate Director, PV Operations",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "PV Operations",
            "location": "Bangalore, India",
            "fte_direct_reports": 45,
        },
        {
            "role": "Director, Risk Management & Epidemiology",
            "name": "Director, Risk Management & Epidemiology",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "Risk Management & Epidemiology",
            "location": "Cambridge, MA",
            "fte_direct_reports": 6,
        },
        {
            "role": "Associate Director, Aggregate Reporting",
            "name": "Associate Director, Aggregate Reporting",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "Aggregate Reporting",
            "location": "Tokyo, Japan",
            "fte_direct_reports": 4,
        },
        {
            "role": "Manager, PV Quality & Compliance",
            "name": "Manager, PV Quality & Compliance",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "PV Quality & Compliance",
            "location": "Dublin, Ireland",
            "fte_direct_reports": 5,
        },
        {
            "role": "Therapeutic Area Head, Oncology",
            "name": "Therapeutic Area Head, Oncology",
            "reports_to": "Head of Patient Safety / Pharmacovigilance",
            "department": "Patient Safety — Oncology",
            "location": "Cambridge, MA",
            "fte_direct_reports": 3,
        },
        {
            "role": "VP Regulatory Affairs",
            "name": "VP Regulatory Affairs",
            "reports_to": "Chief Medical Officer",
            "department": "Regulatory Affairs",
            "location": "Washington, DC",
            "fte_direct_reports": 12,
            "cross_functional": True,
        },
        {
            "role": "VP Clinical Operations",
            "name": "VP Clinical Operations",
            "reports_to": "Chief Medical Officer",
            "department": "Clinical Operations",
            "location": "Philadelphia, PA",
            "fte_direct_reports": 30,
            "cross_functional": True,
        },
        {
            "role": "Head of Biostatistics",
            "name": "Head of Biostatistics",
            "reports_to": "Chief Medical Officer",
            "department": "Biostatistics",
            "location": "Research Triangle Park, NC",
            "fte_direct_reports": 15,
            "cross_functional": True,
        },
    ]

    governance_bodies = [
        GovernanceBody(
            name="Safety Management Team",
            abbreviation="SMT",
            chair="Head of Patient Safety / Pharmacovigilance",
            frequency="Monthly (weekly during active enrollment)",
            last_meeting="2026-02-20",
            next_meeting="2026-03-20",
            members=8,
            charter_status="Approved (v3.1, 2025-09-15)",
        ),
        GovernanceBody(
            name="Safety Review Committee",
            abbreviation="SRC",
            chair="Chief Medical Officer",
            frequency="Quarterly",
            last_meeting="2026-02-15",
            next_meeting="2026-03-15",
            members=18,
            charter_status="Approved (v2.4, 2025-06-01)",
        ),
        GovernanceBody(
            name="Risk Management Committee",
            abbreviation="RMC",
            chair="Director, Risk Management & Epidemiology",
            frequency="Quarterly",
            last_meeting="2026-01-22",
            next_meeting="2026-04-22",
            members=10,
            charter_status="Approved (v1.8, 2025-11-30)",
        ),
    ]

    operating_model = {
        "model_type": "Hybrid (In-house + CRO)",
        "pv_vendor": "SafetyFirst Ltd",
        "safety_database": "Oracle Argus Safety 8.4",
        "signal_detection_tool": "Empirica Signal 9.1",
        "medical_coding": "MedDRA v27.0",
        "drug_coding": "WHODrug Global B3 March 2026",
        "case_processing_locations": [
            {"location": "Bangalore, India", "function": "Case intake, data entry, MedDRA coding", "fte": 30},
            {"location": "Dublin, Ireland", "function": "Case quality review, medical assessment", "fte": 8},
            {"location": "Basel, Switzerland", "function": "Medical review, signal assessment", "fte": 4},
        ],
        "total_pv_fte": 42,
        "outsourced_pct": 57,
    }

    product_portfolio = [
        {
            "product": "Prosinertimib",
            "inn": "prosinertimib",
            "molecule_type": "Small molecule",
            "mechanism": "EGFR tyrosine kinase inhibitor (3rd generation, CNS-penetrant)",
            "therapeutic_area": "Oncology",
            "indication_approved": "First-line treatment of locally advanced or metastatic NSCLC with EGFR exon 19 deletion or exon 21 L858R mutation",
            "nda_approval": "2024-03-15",
            "eu_ma_approval": "2024-06-22",
            "formulations": ["150 mg film-coated tablet", "100 mg film-coated tablet"],
            "global_markets": 38,
            "estimated_patients_exposed": 24500,
            "lifecycle_status": "Post-approval / Active clinical development",
        },
    ]

    return OverviewResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        organization={
            "company": "Meridian Therapeutics, Inc.",
            "pv_department": "Global Patient Safety",
            "head_office": "Cambridge, MA, USA",
            "roles": org_roles,
            "total_fte": 73,
        },
        governance_bodies=governance_bodies,
        operating_model=operating_model,
        product_portfolio=product_portfolio,
    )


# ---------------------------------------------------------------------------
# 2. GET /compliance/us
# ---------------------------------------------------------------------------

@router.get(
    "/compliance/us",
    response_model=USComplianceResponse,
    summary="US regulatory compliance",
    description="Returns compliance status for US pharmacovigilance regulations.",
)
async def get_us_compliance() -> USComplianceResponse:
    """US regulatory compliance status."""
    compliance_items = [
        ComplianceItem(
            regulation="21 CFR 312.32",
            description="IND Safety Reporting (Investigational drugs)",
            status=RAGStatus.GREEN,
            last_assessment="2026-01-15",
            next_assessment="2026-07-15",
            findings=0,
            notes="All IND safety reports submitted within 15-day and 7-day windows. No FDA queries pending.",
        ),
        ComplianceItem(
            regulation="21 CFR 314.80",
            description="Postmarketing Reporting of AEs (NDA products)",
            status=RAGStatus.GREEN,
            last_assessment="2026-01-15",
            next_assessment="2026-07-15",
            findings=1,
            notes="One minor finding: two 15-day reports submitted at Day 14 with incomplete narrative. Corrected within 24 hours.",
        ),
        ComplianceItem(
            regulation="21 CFR 600.80",
            description="Postmarketing Reporting of AEs (Biologics)",
            status=RAGStatus.GREEN,
            last_assessment="2026-01-15",
            next_assessment="2026-07-15",
            findings=0,
            notes="Not directly applicable (small molecule), but BLA pathway elements tracked for combination studies.",
        ),
        ComplianceItem(
            regulation="21 CFR Part 11",
            description="Electronic Records, Electronic Signatures",
            status=RAGStatus.GREEN,
            last_assessment="2025-11-01",
            next_assessment="2026-05-01",
            findings=0,
            notes="Argus Safety validated; audit trail enabled; 21 CFR Part 11 assessment current.",
        ),
        ComplianceItem(
            regulation="FDA REMS",
            description="Risk Evaluation and Mitigation Strategy",
            status=RAGStatus.AMBER,
            last_assessment="2026-02-01",
            next_assessment="2026-08-01",
            findings=2,
            notes="REMS Medication Guide distribution tracking shows 94.2% coverage (target 98%). Improvement plan in place.",
        ),
        ComplianceItem(
            regulation="FDA FAERS Reporting",
            description="FAERS electronic submission compliance",
            status=RAGStatus.GREEN,
            last_assessment="2026-02-15",
            next_assessment="2026-08-15",
            findings=0,
            notes="100% electronic submission via FAERS. E2B(R3) format validated. No ACKs pending.",
        ),
    ]

    reporting_timelines = [
        ReportingTimeline(
            report_type="7-day IND Alert Report",
            regulation="21 CFR 312.32(c)(2)",
            target_days=7,
            compliance_rate=100.0,
            total_submitted=3,
            on_time=3,
            late=0,
            pending=0,
        ),
        ReportingTimeline(
            report_type="15-day IND Safety Report",
            regulation="21 CFR 312.32(c)(1)",
            target_days=15,
            compliance_rate=100.0,
            total_submitted=18,
            on_time=18,
            late=0,
            pending=1,
        ),
        ReportingTimeline(
            report_type="15-day Expedited AE Report (NDA)",
            regulation="21 CFR 314.80(c)(1)",
            target_days=15,
            compliance_rate=97.8,
            total_submitted=89,
            on_time=87,
            late=2,
            pending=3,
        ),
        ReportingTimeline(
            report_type="Periodic AE Report (NDA)",
            regulation="21 CFR 314.80(c)(2)",
            target_days=90,
            compliance_rate=100.0,
            total_submitted=4,
            on_time=4,
            late=0,
            pending=0,
        ),
        ReportingTimeline(
            report_type="Annual IND Report",
            regulation="21 CFR 312.33",
            target_days=365,
            compliance_rate=100.0,
            total_submitted=2,
            on_time=2,
            late=0,
            pending=0,
        ),
    ]

    fda_actions = [
        FDAAction(
            date="2025-12-10",
            action_type="Safety Labeling Change",
            reference="NDA 217834-S003",
            description="FDA requested update to WARNINGS section for ILD risk: addition of Grade 3/4 monitoring recommendations.",
            status="Completed",
            response_due=None,
        ),
        FDAAction(
            date="2026-01-18",
            action_type="Information Request",
            reference="IR-2026-0142",
            description="FDA DMEPA request for cumulative cardiac safety data including QTc sub-study results.",
            status="Response submitted",
            response_due="2026-02-18",
        ),
        FDAAction(
            date="2026-02-22",
            action_type="REMS Assessment",
            reference="REMS-2026-A1",
            description="Scheduled REMS assessment: review of Medication Guide distribution and ILD awareness metrics.",
            status="In progress",
            response_due="2026-04-22",
        ),
    ]

    return USComplianceResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        nda_number="NDA 217834",
        approval_date="2024-03-15",
        compliance_items=compliance_items,
        reporting_timelines=reporting_timelines,
        fda_actions=fda_actions,
        overall_status=RAGStatus.GREEN,
        summary={
            "total_regulations_tracked": 6,
            "green": 5,
            "amber": 1,
            "red": 0,
            "next_fda_action_due": "2026-04-22",
            "period": "2025-Q4 to 2026-Q1",
        },
    )


# ---------------------------------------------------------------------------
# 3. GET /compliance/eu
# ---------------------------------------------------------------------------

@router.get(
    "/compliance/eu",
    response_model=EUComplianceResponse,
    summary="EU regulatory compliance",
    description="Returns GVP module compliance, EudraVigilance stats, and QPPV/LPPV network status.",
)
async def get_eu_compliance() -> EUComplianceResponse:
    """EU regulatory compliance status."""
    gvp_modules = [
        GVPModuleCompliance(
            module="GVP Module I",
            title="PV Systems and Quality Systems",
            status=RAGStatus.GREEN,
            last_audit="2025-10-15",
            findings_open=0,
            findings_closed=3,
            notes="PSMF up to date. Last internal audit found 3 minor documentation gaps, all resolved.",
        ),
        GVPModuleCompliance(
            module="GVP Module VI",
            title="Collection, Management, and Submission of ICSRs",
            status=RAGStatus.GREEN,
            last_audit="2025-11-20",
            findings_open=0,
            findings_closed=1,
            notes="E2B(R3) submissions to EudraVigilance compliant. 99.1% acceptance rate.",
        ),
        GVPModuleCompliance(
            module="GVP Module VII",
            title="Periodic Safety Update Report (PSUR/PBRER)",
            status=RAGStatus.GREEN,
            last_audit="2025-09-01",
            findings_open=0,
            findings_closed=0,
            notes="PBRER #2 submitted on time (DLP 2025-12-22). PRAC assessment favorable.",
        ),
        GVPModuleCompliance(
            module="GVP Module VIII",
            title="Post-authorisation Safety Studies (PASS)",
            status=RAGStatus.GREEN,
            last_audit="2025-12-01",
            findings_open=0,
            findings_closed=0,
            notes="PASS protocol registered in EU PAS Register. Enrollment on track (n=1,200 of 3,000 target).",
        ),
        GVPModuleCompliance(
            module="GVP Module IX",
            title="Signal Management",
            status=RAGStatus.AMBER,
            last_audit="2026-01-10",
            findings_open=1,
            findings_closed=2,
            notes="One open finding: cardiac signal evaluation timeline exceeded 60-day target by 8 days. CAPA opened.",
        ),
        GVPModuleCompliance(
            module="GVP Module X",
            title="Additional Monitoring",
            status=RAGStatus.GREEN,
            last_audit="2025-08-15",
            findings_open=0,
            findings_closed=0,
            notes="Black triangle symbol maintained. Additional monitoring measures in SmPC Section 4.8.",
        ),
        GVPModuleCompliance(
            module="GVP Module XII",
            title="Risk Management Systems",
            status=RAGStatus.GREEN,
            last_audit="2025-10-20",
            findings_open=0,
            findings_closed=1,
            notes="EU-RMP version 3.1 approved by PRAC. All additional risk minimization measures active.",
        ),
        GVPModuleCompliance(
            module="GVP Module XVI",
            title="Risk Minimisation Measures",
            status=RAGStatus.GREEN,
            last_audit="2025-12-15",
            findings_open=0,
            findings_closed=0,
            notes="HCP educational materials distributed to 96% of prescribers. Patient alert card compliance 91%.",
        ),
    ]

    ev_stats = [
        EudraVigilanceStats(
            period="2025-Q4",
            icsr_submitted=312,
            icsr_accepted=309,
            icsr_rejected=3,
            rejection_rate=0.96,
            average_submission_days=4.2,
        ),
        EudraVigilanceStats(
            period="2026-Q1 (to date)",
            icsr_submitted=198,
            icsr_accepted=196,
            icsr_rejected=2,
            rejection_rate=1.01,
            average_submission_days=3.8,
        ),
    ]

    qppv_network = [
        QPPVNetwork(
            role="QPPV (EU)",
            name="QPPV (EU)",
            country="Ireland",
            qualification="MD, PhD Pharmacology, FESC",
            status="Active",
            last_training="2025-11-15",
        ),
        QPPVNetwork(
            role="Deputy EU QPPV",
            name="Deputy EU QPPV",
            country="Germany",
            qualification="MD, MSc Pharmacoepidemiology",
            status="Active",
            last_training="2025-12-01",
        ),
        QPPVNetwork(
            role="LPPV - France",
            name="LPPV France",
            country="France",
            qualification="PharmD, DES Pharmacologie",
            status="Active",
            last_training="2026-01-10",
        ),
        QPPVNetwork(
            role="LPPV - Germany",
            name="LPPV Germany",
            country="Germany",
            qualification="MD, Facharzt Klinische Pharmakologie",
            status="Active",
            last_training="2025-11-20",
        ),
        QPPVNetwork(
            role="LPPV - Spain",
            name="LPPV Spain",
            country="Spain",
            qualification="PharmD, MSc Clinical Research",
            status="Active",
            last_training="2026-01-05",
        ),
        QPPVNetwork(
            role="LPPV - Italy",
            name="LPPV Italy",
            country="Italy",
            qualification="MD, Specialista in Farmacologia",
            status="Active",
            last_training="2025-12-15",
        ),
        QPPVNetwork(
            role="LPPV - UK",
            name="LPPV United Kingdom",
            country="United Kingdom",
            qualification="MBBS, MSc Pharmacovigilance",
            status="Active",
            last_training="2026-02-01",
        ),
    ]

    psmf = {
        "psmf_version": "3.2",
        "psmf_location": "Basel, Switzerland",
        "last_update": "2026-01-31",
        "next_review": "2026-07-31",
        "status": "Current",
        "annexes_count": 14,
        "qppv_statement_date": "2026-01-31",
        "deposited_with_ema": True,
        "key_sections": [
            {"section": "QPPV details", "status": "Current"},
            {"section": "PV system description", "status": "Current"},
            {"section": "Contractual arrangements", "status": "Current"},
            {"section": "Computerized systems", "status": "Current"},
            {"section": "Quality system documentation", "status": "Current"},
            {"section": "Product/substance list", "status": "Updated 2026-01-31"},
        ],
    }

    return EUComplianceResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        eu_number="EU/1/24/1892/001-004",
        ma_holder="Meridian Therapeutics Europe GmbH",
        centralized_procedure_number="EMEA/H/C/006234",
        gvp_modules=gvp_modules,
        eudravigilance_stats=ev_stats,
        qppv_network=qppv_network,
        psmf=psmf,
        overall_status=RAGStatus.GREEN,
    )


# ---------------------------------------------------------------------------
# 4. GET /icsr
# ---------------------------------------------------------------------------

@router.get(
    "/icsr",
    response_model=ICSRResponse,
    summary="ICSR case processing metrics",
    description="Returns ICSR volumes, pipeline metrics, compliance rates, and backlog data.",
)
async def get_icsr_metrics() -> ICSRResponse:
    """ICSR case processing metrics."""
    by_source = [
        CaseVolume(category="Spontaneous (HCP)", count=412, percentage=34.2),
        CaseVolume(category="Spontaneous (Consumer)", count=189, percentage=15.7),
        CaseVolume(category="Clinical Trial (PROSPER-1)", count=203, percentage=16.9),
        CaseVolume(category="Clinical Trial (PROSPER-2)", count=87, percentage=7.2),
        CaseVolume(category="Clinical Trial (PROSPER-3)", count=34, percentage=2.8),
        CaseVolume(category="Literature", count=56, percentage=4.7),
        CaseVolume(category="Regulatory Authority", count=28, percentage=2.3),
        CaseVolume(category="Patient Support Program", count=112, percentage=9.3),
        CaseVolume(category="Solicited (PASS)", count=72, percentage=6.0),
        CaseVolume(category="Other", count=11, percentage=0.9),
    ]

    by_seriousness = [
        CaseVolume(category="Serious - Fatal", count=12, percentage=1.0),
        CaseVolume(category="Serious - Life-threatening", count=34, percentage=2.8),
        CaseVolume(category="Serious - Hospitalization", count=187, percentage=15.5),
        CaseVolume(category="Serious - Disability", count=23, percentage=1.9),
        CaseVolume(category="Serious - Other medically important", count=156, percentage=13.0),
        CaseVolume(category="Non-serious", count=792, percentage=65.8),
    ]

    by_status = [
        CaseVolume(category="Submitted", count=1089, percentage=90.5),
        CaseVolume(category="In medical review", count=42, percentage=3.5),
        CaseVolume(category="In data entry", count=28, percentage=2.3),
        CaseVolume(category="Quality check", count=19, percentage=1.6),
        CaseVolume(category="Awaiting follow-up", count=18, percentage=1.5),
        CaseVolume(category="On hold (query)", count=8, percentage=0.6),
    ]

    pipeline = [
        PipelineStage(
            stage="Intake / Triage",
            count=28,
            avg_days=0.8,
            target_days=1.0,
            status=RAGStatus.GREEN,
        ),
        PipelineStage(
            stage="Data Entry",
            count=28,
            avg_days=2.1,
            target_days=3.0,
            status=RAGStatus.GREEN,
        ),
        PipelineStage(
            stage="MedDRA Coding",
            count=15,
            avg_days=1.2,
            target_days=2.0,
            status=RAGStatus.GREEN,
        ),
        PipelineStage(
            stage="Medical Review",
            count=42,
            avg_days=3.4,
            target_days=3.0,
            status=RAGStatus.AMBER,
        ),
        PipelineStage(
            stage="Quality Check",
            count=19,
            avg_days=1.1,
            target_days=2.0,
            status=RAGStatus.GREEN,
        ),
        PipelineStage(
            stage="Regulatory Submission",
            count=12,
            avg_days=1.5,
            target_days=2.0,
            status=RAGStatus.GREEN,
        ),
    ]

    compliance_rates = {
        "15_day_expedited": {
            "target": 100.0,
            "actual": 97.8,
            "status": "amber",
            "detail": "87 of 89 expedited reports submitted within 15 calendar days. "
                      "2 late reports due to follow-up data received at Day 13 requiring re-assessment.",
        },
        "90_day_periodic": {
            "target": 100.0,
            "actual": 100.0,
            "status": "green",
            "detail": "All 4 periodic reports submitted within 90-day window.",
        },
        "7_day_fatal_unexpected": {
            "target": 100.0,
            "actual": 100.0,
            "status": "green",
            "detail": "3 of 3 fatal/life-threatening unexpected reports submitted within 7 calendar days.",
        },
        "eudravigilance_15_day": {
            "target": 100.0,
            "actual": 99.1,
            "status": "green",
            "detail": "505 of 510 EU-sourced serious reports submitted to EudraVigilance within 15 days.",
        },
    }

    backlog = {
        "total_open_cases": 115,
        "overdue_cases": 7,
        "oldest_overdue_days": 4,
        "overdue_by_priority": {
            "expedited": 2,
            "non_expedited_serious": 3,
            "non_serious": 2,
        },
        "backlog_trend": "decreasing",
        "backlog_7d_ago": 132,
        "backlog_30d_ago": 148,
    }

    trending = {
        "monthly_intake": [
            {"month": "2025-10", "cases": 195},
            {"month": "2025-11", "cases": 208},
            {"month": "2025-12", "cases": 221},
            {"month": "2026-01", "cases": 234},
            {"month": "2026-02", "cases": 246},
        ],
        "intake_trend": "increasing",
        "growth_rate_pct": 5.1,
        "projected_next_month": 258,
        "capacity_utilization_pct": 82,
        "capacity_status": "adequate",
    }

    return ICSRResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        reporting_period="2025-10-01 to 2026-03-05",
        total_cases=1204,
        case_volumes_by_source=by_source,
        case_volumes_by_seriousness=by_seriousness,
        case_volumes_by_status=by_status,
        pipeline_metrics=pipeline,
        compliance_rates=compliance_rates,
        backlog=backlog,
        trending=trending,
    )


# ---------------------------------------------------------------------------
# 5. GET /signals
# ---------------------------------------------------------------------------

@router.get(
    "/signals",
    response_model=SignalsResponse,
    summary="Signal detection status",
    description="Returns active signals with disproportionality scores, pipeline, and assessments.",
)
async def get_signals() -> SignalsResponse:
    """Signal detection status and pipeline."""
    active_signals = [
        SignalItem(
            signal_id="SIG-2026-001",
            term="Cardiac failure",
            soc="Cardiac disorders",
            source="FAERS disproportionality + spontaneous cluster",
            detection_date="2026-01-08",
            prr=2.84,
            ror=3.12,
            ebgm=2.41,
            ebgm_lower=1.68,
            case_count=14,
            status="Under evaluation",
            priority="High",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="2026-03-15",
            assessment_summary=(
                "Signal detected from FAERS disproportionality analysis and confirmed by "
                "internal spontaneous case review. 14 cases of cardiac failure (8 serious, "
                "2 with fatal outcome) identified. Confounders under assessment: prior "
                "anthracycline exposure (5/14), pre-existing cardiac disease (3/14), concurrent "
                "pembrolizumab (6/14). Dedicated cardiac safety review requested for SRC."
            ),
        ),
        SignalItem(
            signal_id="SIG-2025-014",
            term="Interstitial lung disease",
            soc="Respiratory, thoracic and mediastinal disorders",
            source="Clinical trial + spontaneous",
            detection_date="2025-06-15",
            prr=4.21,
            ror=4.58,
            ebgm=3.87,
            ebgm_lower=2.94,
            case_count=47,
            status="Ongoing monitoring (labeled risk)",
            priority="Medium",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="2026-03-22",
            assessment_summary=(
                "ILD is an important identified risk in the RMP. Currently labeled in Section 4.4 "
                "and 4.8 of SmPC. Incidence in clinical trials: 3.2% (all grades), 1.1% (Grade 3+). "
                "Post-marketing reporting rate consistent with clinical trial data. No new signal; "
                "continued routine monitoring."
            ),
        ),
        SignalItem(
            signal_id="SIG-2025-019",
            term="Drug-induced liver injury",
            soc="Hepatobiliary disorders",
            source="Literature case series",
            detection_date="2025-09-28",
            prr=1.92,
            ror=2.05,
            ebgm=1.74,
            ebgm_lower=1.12,
            case_count=9,
            status="Under evaluation",
            priority="Medium",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="2026-03-20",
            assessment_summary=(
                "Hepatotoxicity is an important potential risk. 9 post-marketing cases of elevated "
                "ALT/AST > 5x ULN identified, 3 meeting Hy's Law criteria. Literature case series "
                "(Nakamura et al. 2025, J Hepatol) reported 4 cases with rechallenge data in 2. "
                "Mechanism under investigation (CYP3A4 reactive metabolite hypothesis). DILI expert "
                "panel consultation scheduled."
            ),
        ),
        SignalItem(
            signal_id="SIG-2026-003",
            term="QT prolongation",
            soc="Cardiac disorders",
            source="Clinical trial ECG sub-study",
            detection_date="2026-02-01",
            prr=1.45,
            ror=1.52,
            ebgm=1.31,
            ebgm_lower=0.88,
            case_count=6,
            status="Under evaluation",
            priority="Medium",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="2026-04-01",
            assessment_summary=(
                "QT prolongation is an important potential risk. Dedicated TQT-like ECG analysis "
                "from PROSPER-1 shows mean QTcF increase of 8.2 ms at Cmax (upper bound CI: 12.4 ms). "
                "6 post-marketing cases of QTc > 500 ms reported, all in patients with concurrent "
                "risk factors (hypokalemia, other QT-prolonging drugs). Concentration-QTc analysis "
                "being updated with expanded dataset."
            ),
        ),
        SignalItem(
            signal_id="SIG-2025-022",
            term="Severe cutaneous adverse reaction",
            soc="Skin and subcutaneous tissue disorders",
            source="Spontaneous reports",
            detection_date="2025-11-12",
            prr=1.78,
            ror=1.85,
            ebgm=1.56,
            ebgm_lower=0.94,
            case_count=5,
            status="Closed - Refuted",
            priority="Low",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="N/A",
            assessment_summary=(
                "Initial cluster of 5 reports of severe rash (2 coded as SJS, 3 as DRESS). "
                "Detailed case review by dermatology expert panel concluded: 0/2 SJS cases met "
                "Bastuji-Garin diagnostic criteria; 0/3 DRESS cases met RegiSCAR criteria. "
                "All cases reclassified as severe acneiform rash (expected EGFR class effect). "
                "Signal refuted; no labeling change required. Closed by SMT 2026-01-22."
            ),
        ),
        SignalItem(
            signal_id="SIG-2025-008",
            term="Severe cutaneous reactions (acneiform rash)",
            soc="Skin and subcutaneous tissue disorders",
            source="Post-marketing spontaneous",
            detection_date="2025-03-18",
            prr=3.45,
            ror=3.72,
            ebgm=3.11,
            ebgm_lower=2.15,
            case_count=34,
            status="Closed - Validated (added to label)",
            priority="Low",
            assigned_to="Director, Signal Management & Safety Science",
            next_review="N/A",
            assessment_summary=(
                "Signal validated. Grade 3+ acneiform rash confirmed as important identified risk "
                "per RMP v3.0. Label updated (SmPC 4.4, 4.8; USPI Section 5.4). Risk minimization "
                "measures include patient alert card with skin care recommendations and dose "
                "modification guidance. Dermatology referral protocol added to PROSPER protocols."
            ),
        ),
    ]

    pipeline_summary = {
        "new_signals_ytd": 3,
        "under_evaluation": 3,
        "ongoing_monitoring": 1,
        "closed_validated": 1,
        "closed_refuted": 1,
        "average_evaluation_days": 52,
        "target_evaluation_days": 60,
    }

    recent_assessments = [
        {
            "signal_id": "SIG-2025-022",
            "term": "Severe cutaneous adverse reaction",
            "assessment_date": "2026-01-22",
            "outcome": "Refuted",
            "decision_body": "SMT",
            "rationale": "Expert panel review: no cases met diagnostic criteria for SJS or DRESS.",
        },
        {
            "signal_id": "SIG-2025-014",
            "term": "Interstitial lung disease",
            "assessment_date": "2026-02-20",
            "outcome": "Ongoing monitoring",
            "decision_body": "SMT",
            "rationale": "Reporting rate stable and consistent with labeled risk. No new risk minimization needed.",
        },
        {
            "signal_id": "SIG-2026-001",
            "term": "Cardiac failure",
            "assessment_date": "2026-02-20",
            "outcome": "Escalated to SRC",
            "decision_body": "SMT",
            "rationale": "Disproportionality confirmed. Confounding assessment ongoing. Cardiac safety review requested.",
        },
    ]

    detection_methods = [
        {
            "method": "FAERS Disproportionality (PRR/ROR)",
            "frequency": "Monthly",
            "last_run": "2026-02-28",
            "next_run": "2026-03-31",
            "thresholds": {"prr": 2.0, "chi_squared": 4.0, "case_count_min": 3},
        },
        {
            "method": "MGPS (Empirica Signal / EBGM)",
            "frequency": "Quarterly",
            "last_run": "2025-12-31",
            "next_run": "2026-03-31",
            "thresholds": {"ebgm05": 1.0, "n_min": 3},
        },
        {
            "method": "Clinical Trial Cumulative Review",
            "frequency": "Biweekly (per protocol)",
            "last_run": "2026-02-28",
            "next_run": "2026-03-14",
            "thresholds": {"descriptive": "MedDRA PT-level review of all SAEs and AESIs"},
        },
        {
            "method": "Literature Surveillance",
            "frequency": "Weekly",
            "last_run": "2026-03-03",
            "next_run": "2026-03-10",
            "thresholds": {"descriptive": "PubMed/Embase search strategy with 42 search terms"},
        },
    ]

    return SignalsResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        total_signals=6,
        active_signals=active_signals,
        pipeline_summary=pipeline_summary,
        recent_assessments=recent_assessments,
        detection_methods=detection_methods,
    )


# ---------------------------------------------------------------------------
# 6. GET /aggregate-reports
# ---------------------------------------------------------------------------

@router.get(
    "/aggregate-reports",
    response_model=AggregateReportsResponse,
    summary="Aggregate reporting calendar",
    description="Returns PBRER, DSUR, and PADER schedules with status and progress.",
)
async def get_aggregate_reports() -> AggregateReportsResponse:
    """Aggregate report calendar and status."""
    reports = [
        AggregateReport(
            report_type="PBRER",
            report_name="Prosinertimib PBRER #3",
            data_lock_point="2026-06-22",
            submission_due="2026-09-22",
            regulatory_authority="EMA (via PSUR Repository)",
            status="Drafting",
            progress_pct=15.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="Head of Patient Safety / Pharmacovigilance",
            sections_complete=2,
            sections_total=16,
            notes="DLP aligned with EU MA anniversary. Sections 1-2 (Introduction, Worldwide MA status) complete.",
        ),
        AggregateReport(
            report_type="PBRER",
            report_name="Prosinertimib PBRER #2",
            data_lock_point="2025-12-22",
            submission_due="2026-03-22",
            regulatory_authority="EMA (via PSUR Repository)",
            status="Final QC",
            progress_pct=95.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="Head of Patient Safety / Pharmacovigilance",
            sections_complete=15,
            sections_total=16,
            notes="Under final medical review. Section 16 (Overall B-R assessment) pending CMO sign-off.",
        ),
        AggregateReport(
            report_type="DSUR",
            report_name="PROSPER-1 DSUR #3",
            data_lock_point="2026-03-15",
            submission_due="2026-05-15",
            regulatory_authority="FDA + EMA + Health Canada",
            status="Planning",
            progress_pct=5.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="VP Clinical Operations",
            sections_complete=0,
            sections_total=12,
            notes="DIBD anniversary March 15. Shell document prepared. Safety data extraction scheduled.",
        ),
        AggregateReport(
            report_type="DSUR",
            report_name="PROSPER-2 DSUR #2",
            data_lock_point="2026-05-01",
            submission_due="2026-07-01",
            regulatory_authority="FDA + EMA",
            status="Not started",
            progress_pct=0.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="VP Clinical Operations",
            sections_complete=0,
            sections_total=12,
            notes="DIBD anniversary May 1.",
        ),
        AggregateReport(
            report_type="DSUR",
            report_name="PROSPER-3 DSUR #1",
            data_lock_point="2026-08-10",
            submission_due="2026-10-10",
            regulatory_authority="FDA",
            status="Not started",
            progress_pct=0.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="VP Clinical Operations",
            sections_complete=0,
            sections_total=12,
            notes="First DSUR for Phase I study. DIBD anniversary August 10.",
        ),
        AggregateReport(
            report_type="PADER",
            report_name="Prosinertimib US PADER #2",
            data_lock_point="2026-03-15",
            submission_due="2026-06-15",
            regulatory_authority="FDA",
            status="Planning",
            progress_pct=5.0,
            assigned_lead="Associate Director, Aggregate Reporting",
            reviewer="VP Regulatory Affairs",
            sections_complete=0,
            sections_total=8,
            notes="Post-approval periodic AE report, NDA anniversary date.",
        ),
    ]

    upcoming_deadlines = [
        {"report": "PBRER #2", "due": "2026-03-22", "days_remaining": 17, "priority": "high"},
        {"report": "PROSPER-1 DSUR #3", "due": "2026-05-15", "days_remaining": 71, "priority": "medium"},
        {"report": "US PADER #2", "due": "2026-06-15", "days_remaining": 102, "priority": "medium"},
        {"report": "PROSPER-2 DSUR #2", "due": "2026-07-01", "days_remaining": 118, "priority": "low"},
        {"report": "PBRER #3", "due": "2026-09-22", "days_remaining": 201, "priority": "low"},
        {"report": "PROSPER-3 DSUR #1", "due": "2026-10-10", "days_remaining": 219, "priority": "low"},
    ]

    return AggregateReportsResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        reports=reports,
        calendar_year=2026,
        upcoming_deadlines=upcoming_deadlines,
    )


# ---------------------------------------------------------------------------
# 7. GET /risk-management
# ---------------------------------------------------------------------------

@router.get(
    "/risk-management",
    response_model=RiskManagementResponse,
    summary="Risk management status",
    description="Returns RMP status, commitments, REMS compliance, and risk minimization effectiveness.",
)
async def get_risk_management() -> RiskManagementResponse:
    """Risk management data."""
    rmp = {
        "version": "3.1",
        "approval_date": "2025-10-15",
        "last_update": "2025-10-15",
        "next_update_trigger": "PBRER #3 submission or significant new safety information",
        "important_identified_risks": [
            {
                "risk": "Interstitial lung disease (ILD) / Pneumonitis",
                "incidence_clinical_trials": "3.2% (all grades), 1.1% (Grade 3+)",
                "incidence_post_marketing": "Reporting rate 1.8 per 1000 patient-years",
                "risk_minimization": [
                    "SmPC Section 4.4 warning",
                    "Patient alert card",
                    "HCP educational materials",
                    "REMS Medication Guide (US)",
                ],
            },
            {
                "risk": "Severe diarrhea (Grade 3+)",
                "incidence_clinical_trials": "8.4% (Grade 3+)",
                "incidence_post_marketing": "Reporting rate 5.2 per 1000 patient-years",
                "risk_minimization": [
                    "SmPC Section 4.2 dose modification guidance",
                    "SmPC Section 4.4 warning",
                    "Patient information leaflet",
                ],
            },
            {
                "risk": "Severe skin reactions (acneiform rash, paronychia)",
                "incidence_clinical_trials": "12.1% (Grade 3+)",
                "incidence_post_marketing": "Reporting rate 8.7 per 1000 patient-years",
                "risk_minimization": [
                    "SmPC Section 4.2 dose modification guidance",
                    "SmPC Section 4.4 warning",
                    "Dermatology referral recommendations in SmPC",
                ],
            },
        ],
        "important_potential_risks": [
            {
                "risk": "Hepatotoxicity (Drug-induced liver injury)",
                "basis": "9 post-marketing cases, 3 meeting Hy's Law criteria. Mechanistic plausibility (CYP3A4 metabolism).",
                "pharmacovigilance_activities": [
                    "Enhanced follow-up for hepatic events",
                    "Targeted FAERS monitoring",
                    "DILI expert panel consultation",
                ],
            },
            {
                "risk": "QT prolongation / Cardiac arrhythmia",
                "basis": "Mean QTcF increase 8.2 ms at Cmax. 6 post-marketing cases of QTc > 500 ms (all with confounders).",
                "pharmacovigilance_activities": [
                    "Concentration-QTc analysis from PROSPER-1 ECG sub-study",
                    "Enhanced follow-up for cardiac events",
                    "Ongoing cardiac signal evaluation (SIG-2026-001, SIG-2026-003)",
                ],
            },
        ],
        "missing_information": [
            {
                "item": "Use in severe hepatic impairment (Child-Pugh C)",
                "plan": "PK study in hepatic impairment populations (Study PROS-HEP-01) planned Q3 2026.",
            },
            {
                "item": "Use in pregnancy and lactation",
                "plan": "Preclinical reproductive toxicology complete (embryofetal toxicity demonstrated in rabbits). "
                        "Pregnancy registry (PROS-PREG-01) active since 2024-09-01. 12 prospective enrollees to date.",
            },
            {
                "item": "Long-term safety beyond 24 months",
                "plan": "PROSPER-1 long-term follow-up extension ongoing. PASS study (PROS-PASS-01) enrolling.",
            },
        ],
    }

    rmp_commitments = [
        RMPCommitment(
            commitment_id="RMP-C01",
            description="Post-authorization safety study (PASS) to characterize ILD incidence and risk factors",
            type="PASS (non-interventional)",
            due_date="Interim report: 2027-06-22; Final: 2029-06-22",
            status="Enrolling (1,200 of 3,000 target)",
            regulatory_authority="EMA (PRAC condition)",
            last_update="2026-02-15",
        ),
        RMPCommitment(
            commitment_id="RMP-C02",
            description="Hepatic impairment PK study (Child-Pugh A, B, C)",
            type="Clinical pharmacology study",
            due_date="2027-03-15",
            status="Protocol finalization",
            regulatory_authority="EMA + FDA",
            last_update="2026-01-30",
        ),
        RMPCommitment(
            commitment_id="RMP-C03",
            description="Pregnancy registry to monitor outcomes in exposed pregnancies",
            type="Pregnancy registry (non-interventional)",
            due_date="Annual reports; Final 2030-03-15",
            status="Active (12 prospective enrollees)",
            regulatory_authority="FDA (PMR) + EMA",
            last_update="2026-02-28",
        ),
        RMPCommitment(
            commitment_id="RMP-C04",
            description="HCP educational materials effectiveness survey",
            type="Risk minimization effectiveness evaluation",
            due_date="2026-12-22",
            status="Survey design complete; IRB approval pending",
            regulatory_authority="EMA (PRAC)",
            last_update="2026-02-10",
        ),
        RMPCommitment(
            commitment_id="RMP-C05",
            description="Concentration-QTc analysis with expanded dataset from PROSPER-1",
            type="Clinical pharmacology analysis",
            due_date="2026-09-15",
            status="Data collection ongoing",
            regulatory_authority="FDA",
            last_update="2026-02-20",
        ),
    ]

    rems = {
        "rems_name": "Prosinertimib REMS",
        "rems_type": "Medication Guide",
        "approval_date": "2024-03-15",
        "last_assessment": "2025-09-15",
        "next_assessment": "2026-03-15",
        "reason": "ILD risk: ensure patients are informed about symptoms and when to seek medical attention",
        "timetable_version": "2.0",
        "status": "Active",
        "overall_compliance": 94.2,
        "target_compliance": 98.0,
        "compliance_status": "amber",
    }

    rems_elements = [
        REMSElement(
            element="Medication Guide distribution",
            description="Medication Guide dispensed with each prescription fill",
            compliance_rate=94.2,
            target_rate=98.0,
            status=RAGStatus.AMBER,
            last_assessment="2026-02-01",
        ),
        REMSElement(
            element="REMS website maintenance",
            description="www.prosinertimib-rems.com updated with current materials",
            compliance_rate=100.0,
            target_rate=100.0,
            status=RAGStatus.GREEN,
            last_assessment="2026-02-15",
        ),
        REMSElement(
            element="REMS assessment reporting",
            description="Periodic assessment to FDA DRISK",
            compliance_rate=100.0,
            target_rate=100.0,
            status=RAGStatus.GREEN,
            last_assessment="2025-09-15",
        ),
    ]

    risk_minimization_effectiveness = [
        {
            "measure": "SmPC ILD warning",
            "indicator": "HCP awareness of ILD risk",
            "assessment_method": "HCP survey (n=450)",
            "result": "89% of oncologists aware of ILD monitoring requirements",
            "target": "85%",
            "status": "green",
            "assessment_date": "2025-11-15",
        },
        {
            "measure": "Patient alert card",
            "indicator": "Patient awareness of ILD symptoms",
            "assessment_method": "Patient survey (n=310)",
            "result": "76% of patients could identify ILD symptoms to report",
            "target": "80%",
            "status": "amber",
            "assessment_date": "2025-11-15",
        },
        {
            "measure": "Dermatology referral guidance",
            "indicator": "Dermatology referral rate for Grade 2+ rash",
            "assessment_method": "Claims data analysis",
            "result": "62% referral rate (up from 45% pre-guidance)",
            "target": "70%",
            "status": "amber",
            "assessment_date": "2025-12-01",
        },
        {
            "measure": "Dose modification for diarrhea",
            "indicator": "Appropriate dose reduction for Grade 3 diarrhea",
            "assessment_method": "Pharmacy claims + EMR data",
            "result": "91% of Grade 3 diarrhea episodes had appropriate dose modification",
            "target": "90%",
            "status": "green",
            "assessment_date": "2025-12-01",
        },
    ]

    return RiskManagementResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        rmp=rmp,
        rmp_commitments=rmp_commitments,
        rems=rems,
        rems_elements=rems_elements,
        risk_minimization_effectiveness=risk_minimization_effectiveness,
    )


# ---------------------------------------------------------------------------
# 8. GET /quality
# ---------------------------------------------------------------------------

@router.get(
    "/quality",
    response_model=QualityResponse,
    summary="Quality system metrics",
    description="Returns SOP inventory, CAPA tracker, training compliance, and audit calendar.",
)
async def get_quality() -> QualityResponse:
    """Quality system data."""
    sop_inventory = [
        SOPItem(sop_id="PV-SOP-001", title="Individual Case Safety Report Processing", version="5.2",
                effective_date="2025-06-15", review_due="2026-06-15", owner="Associate Director, PV Operations",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-002", title="Signal Detection and Management", version="4.0",
                effective_date="2025-09-01", review_due="2026-09-01", owner="Director, Signal Management & Safety Science",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-003", title="Periodic Safety Update Report (PBRER/PSUR) Preparation", version="3.1",
                effective_date="2025-03-15", review_due="2026-03-15", owner="Associate Director, Aggregate Reporting",
                status=RAGStatus.AMBER),
        SOPItem(sop_id="PV-SOP-004", title="Risk Management Plan Development and Maintenance", version="2.3",
                effective_date="2025-07-01", review_due="2026-07-01", owner="Director, Risk Management & Epidemiology",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-005", title="REMS Administration and Compliance", version="1.4",
                effective_date="2025-04-15", review_due="2026-04-15", owner="VP Regulatory Affairs",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-006", title="Expedited Regulatory Reporting", version="4.1",
                effective_date="2025-08-01", review_due="2026-08-01", owner="Associate Director, PV Operations",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-007", title="Literature Surveillance for Safety Data", version="3.0",
                effective_date="2025-05-01", review_due="2026-05-01", owner="Director, Signal Management & Safety Science",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-008", title="Medical Review of ICSRs", version="2.2",
                effective_date="2025-10-15", review_due="2026-10-15", owner="Head of Patient Safety / Pharmacovigilance",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-009", title="Pharmacovigilance Agreements Management", version="2.0",
                effective_date="2025-01-15", review_due="2026-01-15", owner="Manager, PV Quality & Compliance",
                status=RAGStatus.RED),
        SOPItem(sop_id="PV-SOP-010", title="CAPA Management for PV Deviations", version="1.3",
                effective_date="2025-11-01", review_due="2026-11-01", owner="Manager, PV Quality & Compliance",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-011", title="PV System Master File (PSMF) Maintenance", version="2.1",
                effective_date="2025-06-01", review_due="2026-06-01", owner="Manager, PV Quality & Compliance",
                status=RAGStatus.GREEN),
        SOPItem(sop_id="PV-SOP-012", title="PV Training Program and Competency Assessment", version="1.5",
                effective_date="2025-09-15", review_due="2026-09-15", owner="Manager, PV Quality & Compliance",
                status=RAGStatus.GREEN),
    ]

    capa_items = [
        CAPAItem(
            capa_id="CAPA-2025-018",
            title="Late 15-day expedited reports (2 cases in Q4 2025)",
            source="Self-identified (compliance review)",
            category="Process Deviation",
            priority="High",
            opened_date="2025-11-05",
            due_date="2026-02-05",
            status="Overdue - Effectiveness check pending",
            assigned_to="Associate Director, PV Operations",
            root_cause="Follow-up data received at Day 13 triggered re-assessment, causing cascade delay in medical review queue.",
            overdue=True,
        ),
        CAPAItem(
            capa_id="CAPA-2026-001",
            title="Cardiac signal evaluation exceeded 60-day target",
            source="GVP Module IX audit finding",
            category="Process Deviation",
            priority="Medium",
            opened_date="2026-01-15",
            due_date="2026-04-15",
            status="Corrective action in progress",
            assigned_to="Director, Signal Management & Safety Science",
            root_cause="Resource constraint: signal team lead on extended medical leave during evaluation period. No backup assigned.",
        ),
        CAPAItem(
            capa_id="CAPA-2026-003",
            title="PV-SOP-009 overdue for periodic review",
            source="QMS review",
            category="Document Control",
            priority="Low",
            opened_date="2026-02-01",
            due_date="2026-03-31",
            status="In progress",
            assigned_to="Manager, PV Quality & Compliance",
            root_cause="SOP owner transition: previous owner left company 2025-12-31. New owner assigned 2026-01-15.",
        ),
        CAPAItem(
            capa_id="CAPA-2025-015",
            title="EudraVigilance rejection rate > 1% in Q3 2025",
            source="Self-identified (metrics review)",
            category="Data Quality",
            priority="Medium",
            opened_date="2025-10-15",
            due_date="2025-12-15",
            status="Closed - Effective",
            assigned_to="Associate Director, PV Operations",
            root_cause="E2B(R3) mapping error for reporter qualification field introduced during system upgrade.",
        ),
        CAPAItem(
            capa_id="CAPA-2026-004",
            title="Patient alert card awareness below 80% target",
            source="Risk minimization effectiveness survey",
            category="Risk Minimization",
            priority="Medium",
            opened_date="2026-02-15",
            due_date="2026-06-15",
            status="Investigation phase",
            assigned_to="Director, Risk Management & Epidemiology",
            root_cause="Under investigation. Preliminary analysis suggests card language at too high a reading level.",
        ),
        CAPAItem(
            capa_id="CAPA-2025-020",
            title="Missing follow-up data for 3 ILD cases",
            source="Self-identified (case review)",
            category="Data Quality",
            priority="High",
            opened_date="2025-12-01",
            due_date="2026-01-31",
            status="Closed - Effective",
            assigned_to="Director, Risk Management & Epidemiology",
            root_cause="Follow-up request template missing pulmonary-specific questions. Template updated.",
        ),
        CAPAItem(
            capa_id="CAPA-2025-021",
            title="Training completion gap for new PV associates",
            source="Audit finding",
            category="Training",
            priority="Medium",
            opened_date="2025-11-15",
            due_date="2026-01-15",
            status="Closed - Effective",
            assigned_to="Manager, PV Quality & Compliance",
            root_cause="Onboarding checklist did not include GVP Module VI training. Checklist updated.",
        ),
    ]

    capa_tracker = {
        "total_open": 4,
        "total_closed_ytd": 3,
        "overdue": 1,
        "by_source": {
            "Self-identified": 1,
            "Audit finding": 1,
            "QMS review": 1,
            "Survey": 1,
        },
        "by_priority": {"high": 1, "medium": 2, "low": 1},
        "average_closure_days": 68,
        "target_closure_days": 90,
    }

    training_compliance = [
        TrainingRecord(role="Medical Reviewers", total_staff=8, compliant=8, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
        TrainingRecord(role="Case Processors", total_staff=30, compliant=28, compliance_rate=93.3,
                       overdue_count=2, status=RAGStatus.AMBER),
        TrainingRecord(role="Signal Analysts", total_staff=8, compliant=8, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
        TrainingRecord(role="Aggregate Report Writers", total_staff=4, compliant=4, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
        TrainingRecord(role="Quality Specialists", total_staff=5, compliant=5, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
        TrainingRecord(role="PV Leadership", total_staff=5, compliant=5, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
        TrainingRecord(role="Regulatory Affairs (PV)", total_staff=6, compliant=5, compliance_rate=83.3,
                       overdue_count=1, status=RAGStatus.AMBER),
        TrainingRecord(role="Clinical Operations (Safety)", total_staff=7, compliant=7, compliance_rate=100.0,
                       overdue_count=0, status=RAGStatus.GREEN),
    ]

    audits_inspections = [
        {
            "type": "Internal Audit",
            "scope": "ICSR processing and expedited reporting",
            "date": "2025-11-20",
            "lead": "Manager, PV Quality & Compliance",
            "status": "Completed",
            "findings_critical": 0,
            "findings_major": 1,
            "findings_minor": 3,
            "capa_raised": 1,
            "next_scheduled": "2026-05-20",
        },
        {
            "type": "Internal Audit",
            "scope": "Signal detection and management",
            "date": "2026-01-10",
            "lead": "Manager, PV Quality & Compliance",
            "status": "Completed",
            "findings_critical": 0,
            "findings_major": 1,
            "findings_minor": 2,
            "capa_raised": 1,
            "next_scheduled": "2026-07-10",
        },
        {
            "type": "Vendor Audit",
            "scope": "SafetyFirst Ltd (CRO) - case processing operations",
            "date": "2025-09-15",
            "lead": "Manager, PV Quality & Compliance + Associate Director, PV Operations",
            "status": "Completed",
            "findings_critical": 0,
            "findings_major": 0,
            "findings_minor": 4,
            "capa_raised": 0,
            "next_scheduled": "2026-09-15",
        },
        {
            "type": "Regulatory Inspection",
            "scope": "EMA GVP Inspection (Article 111 routine)",
            "date": "2026-06-15",
            "lead": "EMA Inspectorate",
            "status": "Scheduled",
            "findings_critical": None,
            "findings_major": None,
            "findings_minor": None,
            "capa_raised": None,
            "next_scheduled": "TBD",
        },
        {
            "type": "Regulatory Inspection",
            "scope": "FDA CDER BPCA (pharmacovigilance inspection)",
            "date": "2026-10-01",
            "lead": "FDA OSE/OPV",
            "status": "Anticipated (not yet confirmed)",
            "findings_critical": None,
            "findings_major": None,
            "findings_minor": None,
            "capa_raised": None,
            "next_scheduled": "TBD",
        },
    ]

    quality_metrics = {
        "sop_total": 12,
        "sop_current": 11,
        "sop_overdue": 1,
        "capa_open": 4,
        "capa_overdue": 1,
        "training_overall_compliance": 96.0,
        "training_target": 95.0,
        "deviations_ytd": 6,
        "inspection_readiness_score": 87,
        "inspection_readiness_target": 90,
    }

    return QualityResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        sop_inventory=sop_inventory,
        capa_tracker=capa_tracker,
        capa_items=capa_items,
        training_compliance=training_compliance,
        audits_inspections=audits_inspections,
        quality_metrics=quality_metrics,
    )


# ---------------------------------------------------------------------------
# 9. GET /clinical-trials
# ---------------------------------------------------------------------------

@router.get(
    "/clinical-trials",
    response_model=ClinicalTrialsResponse,
    summary="Clinical trial safety data",
    description="Returns active trials with SAE/SUSAR counts, DSMB calendar, and IB status.",
)
async def get_clinical_trials() -> ClinicalTrialsResponse:
    """Clinical trial safety overview."""
    trials = [
        ClinicalTrial(
            trial_id="NCT05123456",
            protocol_number="PROSPER-1",
            title="A Randomized, Double-Blind, Phase III Study of Prosinertimib Plus Pembrolizumab "
                  "Versus Pembrolizumab Plus Placebo in Previously Untreated Patients With Locally "
                  "Advanced or Metastatic NSCLC Harboring EGFR Mutations",
            phase="Phase III",
            status="Active, not recruiting",
            indication="First-line EGFR-mutant NSCLC",
            target_enrollment=680,
            current_enrollment=680,
            sites_active=142,
            sae_count=187,
            susar_count=14,
            last_sae_date="2026-02-28",
            dsmb_next="2026-04-12",
            ib_version="8.0 (2025-12-15)",
            ib_next_update="2026-06-15",
        ),
        ClinicalTrial(
            trial_id="NCT05234567",
            protocol_number="PROSPER-2",
            title="A Single-Arm, Open-Label, Phase II Study of Prosinertimib Monotherapy in Patients "
                  "With EGFR-Mutant NSCLC Who Have Progressed on Prior EGFR TKI Therapy",
            phase="Phase II",
            status="Recruiting",
            indication="Second-line EGFR-mutant NSCLC",
            target_enrollment=210,
            current_enrollment=156,
            sites_active=68,
            sae_count=34,
            susar_count=5,
            last_sae_date="2026-03-01",
            dsmb_next="2026-05-20",
            ib_version="8.0 (2025-12-15)",
            ib_next_update="2026-06-15",
        ),
        ClinicalTrial(
            trial_id="NCT05345678",
            protocol_number="PROSPER-3",
            title="A Phase I, Open-Label, Dose-Escalation and Expansion Study of Prosinertimib "
                  "in Patients With EGFR-Positive Advanced Solid Tumors",
            phase="Phase I",
            status="Recruiting",
            indication="EGFR+ advanced solid tumors",
            target_enrollment=90,
            current_enrollment=52,
            sites_active=12,
            sae_count=11,
            susar_count=3,
            last_sae_date="2026-02-14",
            dsmb_next="2026-06-10",
            ib_version="8.0 (2025-12-15)",
            ib_next_update="2026-06-15",
        ),
    ]

    dsmb_calendar = [
        {
            "trial": "PROSPER-1",
            "meeting_type": "Scheduled interim review",
            "date": "2026-04-12",
            "agenda": "Efficacy interim analysis (2nd planned), cumulative safety review, cardiac safety update",
            "chair": "Independent Chair",
            "status": "Confirmed",
        },
        {
            "trial": "PROSPER-2",
            "meeting_type": "Scheduled safety review",
            "date": "2026-05-20",
            "agenda": "Cumulative safety review, enrollment milestone (75% target), SAE review",
            "chair": "Independent Chair",
            "status": "Confirmed",
        },
        {
            "trial": "PROSPER-3",
            "meeting_type": "Dose escalation review",
            "date": "2026-06-10",
            "agenda": "Cohort 6 (200 mg) safety data, dose-limiting toxicity review, expansion cohort recommendation",
            "chair": "Independent Chair",
            "status": "Tentative",
        },
        {
            "trial": "PROSPER-1",
            "meeting_type": "Ad-hoc cardiac safety review",
            "date": "2026-03-15",
            "agenda": "Review of cardiac signal (SIG-2026-001), unblinded cardiac event analysis",
            "chair": "Independent Chair",
            "status": "Requested by SMT",
        },
    ]

    susar_summary = {
        "total_susars_cumulative": 22,
        "total_susars_ytd": 6,
        "susars_by_soc": [
            {"soc": "Respiratory, thoracic and mediastinal disorders", "count": 8, "primary_pt": "Interstitial lung disease"},
            {"soc": "Cardiac disorders", "count": 5, "primary_pt": "Cardiac failure"},
            {"soc": "Hepatobiliary disorders", "count": 4, "primary_pt": "Drug-induced liver injury"},
            {"soc": "Gastrointestinal disorders", "count": 3, "primary_pt": "Diarrhoea haemorrhagic"},
            {"soc": "Infections and infestations", "count": 2, "primary_pt": "Pneumonia"},
        ],
        "susars_by_outcome": {
            "fatal": 3,
            "not_recovered": 4,
            "recovering": 6,
            "recovered": 8,
            "unknown": 1,
        },
        "7_day_compliance": 100.0,
        "15_day_compliance": 100.0,
    }

    safety_review_schedule = [
        {
            "review_type": "Investigator safety letter",
            "trigger": "New important safety information",
            "last_issued": "2025-12-20",
            "subject": "Updated ILD monitoring recommendations (Grade 3/4)",
            "next_planned": "As needed",
        },
        {
            "review_type": "IB update",
            "trigger": "Scheduled (annual) + significant new data",
            "last_issued": "2025-12-15 (v8.0)",
            "subject": "Updated cardiac safety, hepatotoxicity, and ILD sections",
            "next_planned": "2026-06-15 (v9.0)",
        },
        {
            "review_type": "Protocol amendment (safety)",
            "trigger": "DSMB recommendation",
            "last_issued": "2025-10-01 (PROSPER-1 Amendment 4)",
            "subject": "Added mandatory ECG monitoring schedule, cardiac exclusion criteria tightened",
            "next_planned": "Pending DSMB ad-hoc review outcome",
        },
    ]

    return ClinicalTrialsResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        trials=trials,
        dsmb_calendar=dsmb_calendar,
        susar_summary=susar_summary,
        safety_review_schedule=safety_review_schedule,
    )


# ---------------------------------------------------------------------------
# 10. GET /kpis
# ---------------------------------------------------------------------------

@router.get(
    "/kpis",
    response_model=KPIsResponse,
    summary="All KPIs with RAG status",
    description="Returns compliance, quality, signal, and portfolio health KPIs.",
)
async def get_kpis() -> KPIsResponse:
    """All KPIs with RAG status."""
    compliance_kpis = [
        KPI(name="15-day expedited reporting compliance (US)",
            value=97.8, target=100.0, unit="%", rag=RAGStatus.AMBER,
            trend="stable", description="Percentage of 15-day expedited reports submitted on time"),
        KPI(name="15-day expedited reporting compliance (EU)",
            value=99.1, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="improving", description="Percentage of EudraVigilance submissions within 15 days"),
        KPI(name="7-day IND alert reporting compliance",
            value=100.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="Percentage of 7-day alert reports submitted on time"),
        KPI(name="REMS Medication Guide distribution",
            value=94.2, target=98.0, unit="%", rag=RAGStatus.AMBER,
            trend="improving", description="Percentage of prescriptions dispensed with Medication Guide"),
        KPI(name="EudraVigilance acceptance rate",
            value=99.0, target=98.0, unit="%", rag=RAGStatus.GREEN,
            trend="improving", description="Percentage of E2B(R3) submissions accepted by EudraVigilance"),
        KPI(name="Aggregate reports submitted on time",
            value=100.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="PBRER, DSUR, PADER submitted before regulatory deadline"),
    ]

    quality_kpis = [
        KPI(name="SOP currency rate",
            value=91.7, target=100.0, unit="%", rag=RAGStatus.AMBER,
            trend="stable", description="Percentage of SOPs within periodic review date"),
        KPI(name="CAPA closure on time",
            value=75.0, target=90.0, unit="%", rag=RAGStatus.RED,
            trend="declining", description="Percentage of CAPAs closed within target timeframe"),
        KPI(name="Training compliance (overall)",
            value=96.0, target=95.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="Percentage of PV staff with current training"),
        KPI(name="PV deviation rate",
            value=0.5, target=1.0, unit="per 100 cases", rag=RAGStatus.GREEN,
            trend="improving", description="Process deviations per 100 cases processed"),
        KPI(name="Inspection readiness score",
            value=87.0, target=90.0, unit="points", rag=RAGStatus.AMBER,
            trend="improving", description="Composite readiness score based on internal audit metrics"),
    ]

    signal_kpis = [
        KPI(name="Signal evaluation cycle time",
            value=52.0, target=60.0, unit="days", rag=RAGStatus.GREEN,
            trend="stable", description="Average days from signal detection to initial assessment completion"),
        KPI(name="Open signals under evaluation",
            value=3, target="<=5", unit="signals", rag=RAGStatus.GREEN,
            trend="stable", description="Number of signals actively under evaluation"),
        KPI(name="Signal detection currency",
            value=100.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="Percentage of scheduled signal detection activities completed on time"),
        KPI(name="Literature surveillance timeliness",
            value=100.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="Weekly literature searches completed within 2 business days"),
    ]

    portfolio_health_kpis = [
        KPI(name="Benefit-risk assessment status",
            value="Favorable", target="Favorable", unit="", rag=RAGStatus.GREEN,
            trend="stable", description="Overall B-R conclusion per most recent PBRER"),
        KPI(name="RMP commitment completion",
            value=20.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="on track", description="Percentage of RMP commitments completed or on schedule"),
        KPI(name="Active regulatory queries",
            value=1, target=0, unit="queries", rag=RAGStatus.AMBER,
            trend="stable", description="Number of open regulatory authority information requests"),
        KPI(name="Labeling currency (CCDS vs local labels)",
            value=95.0, target=100.0, unit="%", rag=RAGStatus.GREEN,
            trend="stable", description="Percentage of local labels aligned with current CCDS"),
        KPI(name="Patient exposure (cumulative post-marketing)",
            value=24500, target="N/A", unit="patients", rag=RAGStatus.GREEN,
            trend="increasing", description="Estimated cumulative patient exposure since launch"),
    ]

    # Count RAGs
    all_kpis = compliance_kpis + quality_kpis + signal_kpis + portfolio_health_kpis
    rag_counts = {"green": 0, "amber": 0, "red": 0}
    for kpi in all_kpis:
        rag_counts[kpi.rag.value] += 1

    # Overall RAG: red if any red, amber if any amber, else green
    if rag_counts["red"] > 0:
        overall = RAGStatus.AMBER  # overall amber because red KPIs exist but are not critical safety
    elif rag_counts["amber"] > 0:
        overall = RAGStatus.AMBER
    else:
        overall = RAGStatus.GREEN

    return KPIsResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        compliance_kpis=compliance_kpis,
        quality_kpis=quality_kpis,
        signal_kpis=signal_kpis,
        portfolio_health_kpis=portfolio_health_kpis,
        overall_rag=overall,
        kpi_count=rag_counts,
    )


# ---------------------------------------------------------------------------
# 11. GET /benefit-risk
# ---------------------------------------------------------------------------

@router.get(
    "/benefit-risk",
    response_model=BenefitRiskResponse,
    summary="Benefit-risk assessment and safety science",
    description="Returns benefit-risk summary, labeling status, and effects table for Prosinertimib.",
)
async def get_benefit_risk() -> BenefitRiskResponse:
    """Benefit-risk assessment and labeling status."""
    benefit_risk_summary = {
        "framework": "EMA Benefit-Risk Methodology (PrOACT-URL)",
        "last_assessment_date": "2025-12-22",
        "assessment_source": "PBRER #2 (DLP 2025-12-22)",
        "conclusion": "Favorable",
        "summary": (
            "The benefit-risk balance of prosinertimib remains favorable in the approved indication "
            "(first-line treatment of locally advanced or metastatic NSCLC with EGFR exon 19 deletion "
            "or exon 21 L858R mutation). The primary efficacy benefit (median PFS: 18.7 months vs "
            "12.4 months with comparator; HR 0.58, 95% CI 0.47-0.72) is substantial and clinically "
            "meaningful. The safety profile is consistent with the EGFR TKI class, with ILD as the "
            "most important identified risk. The emerging cardiac signal requires further evaluation "
            "but does not alter the overall favorable benefit-risk conclusion at this time. The RMP "
            "and REMS adequately address the identified and potential risks."
        ),
        "next_assessment": "PBRER #3 (DLP 2026-06-22)",
        "key_uncertainties": [
            "Cardiac safety signal under evaluation (SIG-2026-001)",
            "Hepatotoxicity signal under evaluation (SIG-2025-019)",
            "Long-term safety beyond 24 months",
            "Safety in severe hepatic impairment (no clinical data)",
            "Reproductive toxicity in humans (animal data only)",
        ],
    }

    labeling_status = {
        "ccds": {
            "version": "4.0",
            "effective_date": "2025-12-20",
            "last_update_reason": "Addition of Grade 3/4 ILD monitoring recommendations and cardiac monitoring language",
            "next_review": "2026-06-22 (aligned with PBRER #3)",
        },
        "uspi": {
            "version": "NDA 217834 Label Revision 3",
            "effective_date": "2025-12-20",
            "sections_updated": [
                "WARNINGS AND PRECAUTIONS (5.1 ILD, 5.4 QT Prolongation)",
                "ADVERSE REACTIONS (6.1 Clinical Trial Experience - updated Table 2)",
            ],
            "pending_updates": "Potential cardiac warning update pending SRC recommendation",
        },
        "smpc": {
            "version": "SmPC Variation Type II (No. 2025/0034)",
            "effective_date": "2025-12-20",
            "sections_updated": [
                "4.2 Posology - dose modification for Grade 3+ ILD",
                "4.4 Special warnings - ILD monitoring, cardiac monitoring",
                "4.8 Undesirable effects - updated frequency tables",
            ],
            "pending_updates": "Cardiac safety text update under PRAC review",
        },
        "alignment_status": {
            "ccds_to_uspi": "Aligned (as of 2025-12-20)",
            "ccds_to_smpc": "Aligned (as of 2025-12-20)",
            "local_labels_aligned": "36 of 38 markets (95%)",
            "pending_local_updates": ["Japan (PMDA review)", "South Korea (MFDS review)"],
        },
    }

    effects_table = [
        EffectsTableRow(
            effect="Progression-free survival",
            category="Benefit",
            prosinertimib_rate="Median 18.7 months",
            comparator_rate="Median 12.4 months",
            relative_effect="HR 0.58 (95% CI 0.47-0.72)",
            certainty="High",
            importance="Critical",
        ),
        EffectsTableRow(
            effect="Overall survival",
            category="Benefit",
            prosinertimib_rate="Median 32.1 months",
            comparator_rate="Median 26.8 months",
            relative_effect="HR 0.74 (95% CI 0.59-0.93)",
            certainty="High",
            importance="Critical",
        ),
        EffectsTableRow(
            effect="Objective response rate",
            category="Benefit",
            prosinertimib_rate="71.2%",
            comparator_rate="52.8%",
            relative_effect="Difference: +18.4% (95% CI 11.2-25.6)",
            certainty="High",
            importance="Important",
        ),
        EffectsTableRow(
            effect="CNS response rate (brain metastases)",
            category="Benefit",
            prosinertimib_rate="64.3%",
            comparator_rate="22.1%",
            relative_effect="Difference: +42.2% (95% CI 28.4-56.0)",
            certainty="Moderate",
            importance="Important",
        ),
        EffectsTableRow(
            effect="Interstitial lung disease (all grades)",
            category="Risk (Important identified)",
            prosinertimib_rate="3.2%",
            comparator_rate="0.9%",
            relative_effect="RR 3.56 (95% CI 1.52-8.34)",
            certainty="Moderate",
            importance="Critical",
        ),
        EffectsTableRow(
            effect="Interstitial lung disease (Grade 3+)",
            category="Risk (Important identified)",
            prosinertimib_rate="1.1%",
            comparator_rate="0.3%",
            relative_effect="RR 3.67 (95% CI 0.77-17.5)",
            certainty="Low",
            importance="Critical",
        ),
        EffectsTableRow(
            effect="Diarrhea (Grade 3+)",
            category="Risk (Important identified)",
            prosinertimib_rate="8.4%",
            comparator_rate="2.1%",
            relative_effect="RR 4.00 (95% CI 2.22-7.21)",
            certainty="High",
            importance="Important",
        ),
        EffectsTableRow(
            effect="Rash/Dermatitis acneiform (Grade 3+)",
            category="Risk (Important identified)",
            prosinertimib_rate="12.1%",
            comparator_rate="1.5%",
            relative_effect="RR 8.07 (95% CI 4.04-16.1)",
            certainty="High",
            importance="Important",
        ),
        EffectsTableRow(
            effect="Hepatotoxicity (ALT/AST > 5x ULN)",
            category="Risk (Important potential)",
            prosinertimib_rate="2.8%",
            comparator_rate="1.2%",
            relative_effect="RR 2.33 (95% CI 0.98-5.56)",
            certainty="Low",
            importance="Important",
        ),
        EffectsTableRow(
            effect="QTc prolongation (> 60 ms increase from baseline)",
            category="Risk (Important potential)",
            prosinertimib_rate="1.5%",
            comparator_rate="0.6%",
            relative_effect="RR 2.50 (95% CI 0.72-8.67)",
            certainty="Low",
            importance="Important",
        ),
        EffectsTableRow(
            effect="Hypertension (Grade 3+)",
            category="Risk",
            prosinertimib_rate="5.2%",
            comparator_rate="3.8%",
            relative_effect="RR 1.37 (95% CI 0.82-2.29)",
            certainty="Moderate",
            importance="Moderate",
        ),
        EffectsTableRow(
            effect="Treatment discontinuation due to AE",
            category="Tolerability",
            prosinertimib_rate="11.8%",
            comparator_rate="6.2%",
            relative_effect="RR 1.90 (95% CI 1.32-2.74)",
            certainty="High",
            importance="Important",
        ),
    ]

    key_benefits = [
        {
            "benefit": "Superior PFS vs standard of care",
            "magnitude": "6.3-month improvement in median PFS (HR 0.58)",
            "certainty": "High (Phase III, randomized, double-blind)",
            "clinical_significance": (
                "Clinically meaningful delay in disease progression. Exceeds pre-specified "
                "non-inferiority and superiority boundaries."
            ),
        },
        {
            "benefit": "CNS activity (brain metastases)",
            "magnitude": "42% absolute improvement in intracranial response rate",
            "certainty": "Moderate (exploratory endpoint, n=84)",
            "clinical_significance": (
                "Addresses major unmet need: brain metastases occur in 25-40% of EGFR-mutant NSCLC. "
                "Third-generation EGFR TKI with demonstrated CNS penetration."
            ),
        },
        {
            "benefit": "Overall survival improvement",
            "magnitude": "5.3-month improvement in median OS (HR 0.74)",
            "certainty": "High (pre-specified secondary endpoint, statistically significant)",
            "clinical_significance": "Meaningful survival benefit with manageable safety profile.",
        },
    ]

    key_risks = [
        {
            "risk": "Interstitial lung disease / Pneumonitis",
            "frequency": "3.2% all grades, 1.1% Grade 3+",
            "severity": "Potentially fatal (3 deaths in clinical program)",
            "manageability": (
                "Manageable with early detection and intervention. CT monitoring recommended. "
                "Dose interruption/discontinuation per SmPC. Corticosteroid treatment effective in most cases."
            ),
            "risk_minimization": "REMS Medication Guide, patient alert card, HCP educational materials",
        },
        {
            "risk": "Cardiac events (emerging signal)",
            "frequency": "Under evaluation (14 post-marketing cases)",
            "severity": "Serious (2 fatal outcomes reported)",
            "manageability": (
                "Under evaluation. ECG monitoring added to protocol. Cardiac exclusion criteria tightened. "
                "DSMB ad-hoc review requested."
            ),
            "risk_minimization": "ECG monitoring per SmPC, cardiac risk factor screening",
        },
        {
            "risk": "Severe diarrhea",
            "frequency": "8.4% Grade 3+",
            "severity": "Manageable; rarely life-threatening",
            "manageability": (
                "Well-characterized EGFR class effect. Early loperamide initiation effective. "
                "Dose modification guidance in SmPC."
            ),
            "risk_minimization": "SmPC dose modification table, patient counseling",
        },
    ]

    return BenefitRiskResponse(
        request_id=_make_request_id(),
        timestamp=_now(),
        product="Prosinertimib",
        indication="First-line locally advanced or metastatic NSCLC with EGFR exon 19 deletion or exon 21 L858R mutation",
        benefit_risk_summary=benefit_risk_summary,
        labeling_status=labeling_status,
        effects_table=effects_table,
        key_benefits=key_benefits,
        key_risks=key_risks,
        overall_benefit_risk_conclusion=(
            "The benefit-risk balance of prosinertimib remains favorable. The substantial PFS and OS "
            "benefits, combined with meaningful CNS activity, outweigh the identified risks when "
            "appropriate risk minimization measures are in place. The emerging cardiac signal requires "
            "continued close monitoring but does not alter the overall favorable conclusion at this time. "
            "This assessment will be updated in PBRER #3 (DLP 2026-06-22) with additional cardiac safety data."
        ),
    )


# ---------------------------------------------------------------------------
# 12. GET /ai-intelligence
# ---------------------------------------------------------------------------

@router.get(
    "/ai-intelligence",
    response_model=AIIntelligenceResponse,
    summary="AI-native safety intelligence",
    description=(
        "Returns AI-native safety intelligence data for the Prosinertimib PV dashboard. "
        "Demonstrates the AI-native paradigm: hypothesis-driven safety science with "
        "mechanistic reasoning."
    ),
)
async def get_ai_intelligence() -> AIIntelligenceResponse:
    """AI-native safety intelligence with hypothesis-driven mechanistic reasoning."""

    therapeutic_area = TherapeuticAreaContext(
        disease="Non-Small Cell Lung Cancer (NSCLC) — EGFR-mutant",
        drug_class="EGFR Tyrosine Kinase Inhibitor",
        mechanism_of_action=(
            "Selective, irreversible inhibitor of EGFR (including T790M, C797S resistance mutations)"
        ),
        generation="3rd generation",
        approved_indication="2nd-line+ EGFR-mutant NSCLC after progression on prior EGFR TKI",
        treatment_landscape=[
            {"line": "1L", "standard": "Osimertinib (TAGRISSO)", "rationale": "FLAURA trial, OS 38.6 months"},
            {"line": "2L (T790M+)", "standard": "Prosinertimib", "rationale": "PROSPER-1 trial, ORR 58%, mPFS 11.2 months"},
            {"line": "2L (T790M-)", "standard": "Platinum-based chemotherapy ± pembrolizumab", "rationale": "Standard of care for T790M-negative progression"},
            {"line": "3L+", "standard": "Clinical trials, docetaxel, or BSC", "rationale": "Limited options after 2nd-line progression"},
        ],
        unmet_need=(
            "Patients progressing on osimertinib with C797S resistance mutation. No approved targeted "
            "therapy exists. CNS-penetrant options urgently needed — 25-40% of patients develop brain metastases."
        ),
        five_year_survival="30-40% for EGFR+ NSCLC with sequential TKI therapy",
        patient_population="Median age 62, 60% female, 30% never-smokers, ECOG PS 0-1",
    )

    ai_chain = {
        "description": "6-stage AI safety intelligence pipeline applied to cardiac signal SIG-2026-001",
        "stages": [
            AIChainStage(
                stage=1,
                name="Foundation Model",
                status="active",
                component="Claude Opus",
                detail=(
                    "Analyzing 14 cardiac AE narratives, 847 class-effect literature references, "
                    "6 EGFR TKI product labels"
                ),
            ).model_dump(),
            AIChainStage(
                stage=2,
                name="Agent Harness",
                status="active",
                component="Iterative mechanistic reasoning",
                detail=(
                    "3 hypothesis cycles, cross-referencing kinase selectivity data with cardiac "
                    "tissue expression profiles"
                ),
            ).model_dump(),
            AIChainStage(
                stage=3,
                name="Governance/SOPs",
                status="complete",
                component="Regulatory framework alignment",
                detail=(
                    "GVP Module IX signal evaluation criteria, PV-SOP-007 signal detection, "
                    "ASTCT grading criteria, ICH E2C(R2) Section 16"
                ),
            ).model_dump(),
            AIChainStage(
                stage=4,
                name="Data Integration",
                status="complete",
                component="Multi-source data fusion",
                detail=(
                    "Oracle Argus Safety 8.4 (14 cardiac cases), FAERS (EGFR TKI class query, "
                    "2,847 cardiac events), PubMed (23 relevant publications)"
                ),
            ).model_dump(),
            AIChainStage(
                stage=5,
                name="Workflow",
                status="pending",
                component="Escalation pathway",
                detail="Signal Management Review Meeting → SMT → SRC escalation pathway",
            ).model_dump(),
            AIChainStage(
                stage=6,
                name="Validation",
                status="pending",
                component="Human-in-the-loop review",
                detail="Medical reviewer verification, QPPV sign-off, CMO benefit-risk review",
            ).model_dump(),
        ],
    }

    active_hypotheses = [
        Hypothesis(
            id="HYP-2026-001",
            signal_ref="SIG-2026-001",
            title="HER2/ErbB2 off-target inhibition driving cardiac failure",
            hypothesis=(
                "Prosinertimib's C797S-targeting selectivity profile may result in off-target inhibition "
                "of the HER2/ErbB4 neuregulin-1 signaling pathway in cardiomyocytes, impairing "
                "stress-response cardioprotection and leading to clinical heart failure in susceptible patients."
            ),
            mechanism=(
                "EGFR/HER2 heterodimerization → neuregulin-1 (NRG-1) signaling → PI3K/Akt survival "
                "pathway in cardiomyocytes → impaired response to hemodynamic stress → myocardial dysfunction"
            ),
            biological_plausibility="High",
            confidence=0.72,
            evidence_for=[
                {
                    "source": "Crone et al., 2002",
                    "finding": "Cardiac-specific ErbB2 knockout mice develop dilated cardiomyopathy",
                    "pmid": "12015981",
                },
                {
                    "source": "Ozcelik et al., 2002",
                    "finding": "ErbB2 conditional deletion causes dilated cardiomyopathy in mice",
                    "pmid": "12015982",
                },
                {
                    "source": "FAERS class analysis",
                    "finding": (
                        "247 cardiac failure reports across EGFR TKI class (2015-2025), "
                        "ROR 1.8 (95% CI 1.4-2.3)"
                    ),
                    "pmid": "",
                },
                {
                    "source": "Prosinertimib kinase panel",
                    "finding": (
                        "IC50 for ErbB2: 84 nM (vs EGFR: 1.2 nM) — 70x selectivity, but clinically "
                        "relevant at therapeutic concentrations"
                    ),
                    "pmid": "",
                },
            ],
            evidence_against=[
                {
                    "source": "PROSPER-1 Phase III",
                    "finding": (
                        "No significant LVEF decline vs chemotherapy at 12-month analysis "
                        "(mean change -2.1% vs -1.8%)"
                    ),
                    "pmid": "",
                },
                {
                    "source": "Clinical profile",
                    "finding": "6 of 14 cases had pre-existing cardiovascular comorbidities",
                    "pmid": "",
                },
            ],
            status="Under Investigation",
            generated_date="2026-02-28",
            next_steps=[
                "Retrospective echocardiography analysis across PROSPER trials",
                "Request troponin T substudy in PROSPER-3",
                "FDA FAERS deep-dive: cardiac events by EGFR TKI generation",
            ],
        ),
        Hypothesis(
            id="HYP-2026-002",
            signal_ref="SIG-2026-002",
            title="EGFR-dependent alveolar repair inhibition as ILD mechanism",
            hypothesis=(
                "EGFR signaling is critical for type II pneumocyte proliferation and alveolar repair. "
                "Prosinertimib's potent EGFR inhibition may impair the lung's repair response to "
                "subclinical injury, leading to progressive interstitial inflammation."
            ),
            mechanism=(
                "EGFR on type II pneumocytes → proliferation/repair signaling → TGF-β pathway "
                "modulation → impaired alveolar repair → progressive interstitial fibrosis"
            ),
            biological_plausibility="High",
            confidence=0.81,
            evidence_for=[
                {
                    "source": "Suzuki et al., 2003",
                    "finding": (
                        "EGFR ligands promote type II pneumocyte proliferation; EGFR inhibition "
                        "delays alveolar repair"
                    ),
                    "pmid": "12626338",
                },
                {
                    "source": "EGFR TKI class data",
                    "finding": (
                        "ILD is a recognized class effect: gefitinib 1-4%, osimertinib 3-4%, "
                        "erlotinib 1-3%"
                    ),
                    "pmid": "",
                },
                {
                    "source": "Japanese PMS data",
                    "finding": (
                        "Higher ILD rates in Japanese population (5-10%) suggesting genetic susceptibility"
                    ),
                    "pmid": "15818571",
                },
            ],
            evidence_against=[
                {
                    "source": "PROSPER-1",
                    "finding": "ILD rate (2.8%) within expected range for 3rd-gen EGFR TKIs",
                    "pmid": "",
                },
            ],
            status="Under Investigation",
            generated_date="2026-01-15",
            next_steps=[
                "Monitor ILD case accrual rate vs osimertinib benchmark",
                "Evaluate HRCT patterns for drug-induced vs disease progression",
            ],
        ),
        Hypothesis(
            id="HYP-2026-003",
            signal_ref="SIG-2025-019",
            title="CYP3A4-mediated reactive metabolite hepatotoxicity",
            hypothesis=(
                "Prosinertimib's pyrimidine core undergoes CYP3A4-mediated bioactivation to a reactive "
                "quinone-imine intermediate, which depletes glutathione and causes dose-dependent "
                "hepatocellular injury, particularly in patients with CYP3A4 ultra-rapid metabolizer phenotype."
            ),
            mechanism=(
                "Prosinertimib → CYP3A4 bioactivation → reactive quinone-imine → glutathione depletion → "
                "mitochondrial dysfunction → hepatocyte apoptosis → ALT/AST elevation → Hy's Law cases"
            ),
            biological_plausibility="Medium",
            confidence=0.58,
            evidence_for=[
                {
                    "source": "In vitro metabolism study",
                    "finding": (
                        "Reactive metabolite detected in human hepatocyte incubations with GSH trapping"
                    ),
                    "pmid": "",
                },
                {
                    "source": "Clinical data",
                    "finding": (
                        "3 Hy's Law cases, all on concomitant CYP3A4 inhibitors "
                        "(2 ketoconazole, 1 voriconazole)"
                    ),
                    "pmid": "",
                },
            ],
            evidence_against=[
                {
                    "source": "PROSPER-1",
                    "finding": "Overall ALT elevation rate (22%) similar to osimertinib (25%)",
                    "pmid": "",
                },
                {
                    "source": "Population PK",
                    "finding": "No clear dose-exposure-hepatotoxicity relationship identified",
                    "pmid": "",
                },
            ],
            status="Under Investigation",
            generated_date="2025-12-10",
            next_steps=[
                "CYP3A4 genotyping in hepatotoxicity cases",
                "Drug interaction protocol amendment for PROSPER-3",
            ],
        ),
    ]

    mechanistic_analysis = MechanisticAnalysis(
        signal_id="SIG-2026-001",
        signal_name="Cardiac failure cluster",
        biological_plausibility="High",
        pathway_summary=(
            "EGFR/HER2 heterodimerization → neuregulin-1 (NRG-1) signaling → PI3K/Akt survival "
            "pathway in cardiomyocytes → impaired response to hemodynamic stress → myocardial dysfunction"
        ),
        pathway_steps=[
            {"step": 1, "entity": "Prosinertimib", "action": "inhibits", "detail": "EGFR (IC50 1.2 nM) and off-target HER2/ErbB2 (IC50 84 nM)"},
            {"step": 2, "entity": "HER2/ErbB4", "action": "disrupted", "detail": "Neuregulin-1 (NRG-1) cardioprotective signaling blocked"},
            {"step": 3, "entity": "PI3K/Akt pathway", "action": "suppressed", "detail": "Cardiomyocyte survival signaling impaired"},
            {"step": 4, "entity": "Cardiomyocytes", "action": "vulnerable", "detail": "Impaired stress-response → susceptibility to hemodynamic injury"},
            {"step": 5, "entity": "Clinical outcome", "action": "manifests as", "detail": "Heart failure (NYHA Class II-IV), LVEF decline, cardiac biomarker elevation"},
        ],
        class_precedent=[
            {"drug": "Trastuzumab", "finding": "HER2 blockade causes reversible cardiomyopathy in 2-7% of patients", "pmid": "11673345"},
            {"drug": "Lapatinib", "finding": "Dual EGFR/HER2 inhibitor: 1.6% LVEF decline, generally reversible", "pmid": "17192538"},
            {"drug": "Osimertinib", "finding": "QTc prolongation and LVEF decline reported; FDA label includes cardiac monitoring", "pmid": "29596029"},
        ],
        unique_risk_factors=(
            "Prosinertimib's irreversible binding mechanism may cause prolonged HER2 inhibition compared to "
            "reversible EGFR TKIs, potentially increasing cardiac risk duration. C797S-targeting moiety may "
            "enhance off-target cardiac kinase inhibition."
        ),
        monitoring_recommendation=(
            "Baseline and q12w echocardiography, troponin T at baseline and Cycles 1-4, BNP/NT-proBNP "
            "monitoring, cardiac risk factor assessment at screening. Hold for LVEF <50% or >10% absolute decline."
        ),
    )

    drug_class_comparison = [
        ClassComparator(drug="Erlotinib", generation="1st generation", cardiac_risk="Low", ild_risk="1-3%", skin_rash="75%", diarrhea="55%", hepatotox="5%", status="Approved"),
        ClassComparator(drug="Gefitinib", generation="1st generation", cardiac_risk="Low", ild_risk="1-4%", skin_rash="50%", diarrhea="45%", hepatotox="10%", status="Approved"),
        ClassComparator(drug="Afatinib", generation="2nd generation", cardiac_risk="Low-Moderate", ild_risk="1%", skin_rash="90%", diarrhea="96%", hepatotox="8%", status="Approved"),
        ClassComparator(drug="Osimertinib", generation="3rd generation", cardiac_risk="Moderate (QTc, LVEF)", ild_risk="3-4%", skin_rash="40%", diarrhea="48%", hepatotox="25%", status="Approved"),
        ClassComparator(drug="Prosinertimib", generation="3rd generation", cardiac_risk="Under evaluation", ild_risk="2.8%", skin_rash="45%", diarrhea="42%", hepatotox="22%", status="Approved"),
    ]

    ai_insights_summary = {
        "total_hypotheses": 3,
        "confirmed": 0,
        "under_investigation": 3,
        "refuted": 0,
        "avg_confidence": 0.70,
        "literature_references_analyzed": 847,
        "class_effect_signals_monitored": 6,
        "ai_chain_status": "Active — processing SIG-2026-001 cardiac failure cluster",
    }

    return AIIntelligenceResponse(
        request_id=_make_request_id(),
        timestamp=_now().isoformat(),
        product="Prosinertimib",
        therapeutic_area=therapeutic_area,
        ai_chain=ai_chain,
        active_hypotheses=active_hypotheses,
        mechanistic_analysis=mechanistic_analysis,
        drug_class_comparison=drug_class_comparison,
        ai_insights_summary=ai_insights_summary,
    )


# ---------------------------------------------------------------------------
# Chat endpoint — models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    context: Optional[str] = None


class ChatSource(BaseModel):
    type: str  # "knowledge_graph", "signal_data", "literature", "clinical_data", "regulatory"
    reference: str
    detail: str


class ChatResponse(BaseModel):
    request_id: str
    timestamp: str
    question: str
    answer: str
    sources: list[ChatSource]
    confidence: float
    follow_up_questions: list[str]


# ---------------------------------------------------------------------------
# Chat endpoint — response logic
# ---------------------------------------------------------------------------

def _chat_respond(question: str) -> tuple[str, list[dict], float, list[str]]:
    """Return (answer, sources, confidence, follow_ups) based on keyword matching."""

    q = question

    # Pattern 1: cardiac / heart failure / cardiac failure / HER2
    if re.search(r"cardiac|heart\s*failure|cardiac\s*failure|HER2", q, re.IGNORECASE):
        answer = (
            "The cardiac failure cluster (SIG-2026-001, 14 cases) has high biological "
            "plausibility for an off-target HER2/ErbB2 mechanism. Prosinertimib\u2019s "
            "selectivity profile shows an IC50 of 84\u202fnM for ErbB2 \u2014 70x less potent "
            "than its EGFR binding (1.2\u202fnM), but potentially clinically relevant at "
            "steady-state therapeutic concentrations.\n\n"
            "The proposed mechanism: EGFR/HER2 heterodimerization in cardiomyocytes "
            "activates neuregulin-1 (NRG-1) signaling through the PI3K/Akt survival "
            "pathway. Inhibition of this pathway impairs the heart\u2019s stress-response "
            "cardioprotection, potentially leading to myocardial dysfunction under "
            "hemodynamic stress.\n\n"
            "This is consistent with class precedent: lapatinib (dual EGFR/HER2 "
            "inhibitor) shows 1.6% cardiac events; osimertinib causes QTc prolongation "
            "and LVEF decrease of 3-4%; trastuzumab (pure HER2) causes cardiomyopathy "
            "in 2-7% of patients.\n\n"
            "Next steps: retrospective echocardiography analysis across PROSPER trials, "
            "troponin T substudy in PROSPER-3, and FAERS deep-dive on cardiac events by "
            "EGFR TKI generation."
        )
        sources = [
            {"type": "knowledge_graph", "reference": "EGFR/HER2 pathway", "detail": "NRG-1 \u2192 ErbB2/ErbB4 \u2192 PI3K/Akt cardioprotection"},
            {"type": "signal_data", "reference": "SIG-2026-001", "detail": "14 cases, 3 Grade 3+, PRR 2.34"},
            {"type": "literature", "reference": "PMID:12015981 (Crone et al., 2002)", "detail": "ErbB2 knockout mice develop dilated cardiomyopathy"},
            {"type": "literature", "reference": "PMID:28841389", "detail": "Osimertinib cardiac safety: QTc and LVEF data"},
        ]
        confidence = 0.82
        follow_ups = [
            "How does the cardiac risk compare to osimertinib?",
            "What monitoring protocol is recommended?",
            "Should we update the Risk Management Plan?",
        ]
        return answer, sources, confidence, follow_ups

    # Pattern 2: compare.*osimertinib / osimertinib.*compare / class comparison
    if re.search(r"compare.*osimertinib|osimertinib.*compare|class\s*comparison", q, re.IGNORECASE):
        answer = (
            "Prosinertimib\u2019s safety profile is broadly consistent with the "
            "3rd-generation EGFR TKI class, with some notable differences compared "
            "to osimertinib:\n\n"
            "**Cardiac risk:** Osimertinib has established QTc prolongation (mean "
            "16ms) and LVEF decrease (3-4%). Prosinertimib\u2019s cardiac signal (14 "
            "cases, 1.7% incidence) is under active evaluation \u2014 the mechanism may "
            "differ (heart failure vs conduction abnormality).\n\n"
            "**ILD/Pneumonitis:** Prosinertimib 2.8% vs osimertinib 3-4%. Within "
            "expected class range.\n\n"
            "**Skin rash:** Prosinertimib 45% vs osimertinib 40%. Class effect "
            "correlated with efficacy.\n\n"
            "**Diarrhea:** Prosinertimib 42% vs osimertinib 48%. Lower rate may "
            "reflect selectivity profile.\n\n"
            "**Hepatotoxicity:** Prosinertimib 22% vs osimertinib 25%. Both within "
            "class norms, but 3 Hy\u2019s Law cases with Prosinertimib warrant monitoring.\n\n"
            "Overall, Prosinertimib\u2019s benefit-risk remains favorable in its approved "
            "2L+ setting where osimertinib has already failed."
        )
        sources = [
            {"type": "clinical_data", "reference": "PROSPER-1 trial", "detail": "Phase III safety data, N=412"},
            {"type": "clinical_data", "reference": "FLAURA trial (osimertinib)", "detail": "Comparator safety reference"},
            {"type": "signal_data", "reference": "Drug class comparison", "detail": "5-drug EGFR TKI safety matrix"},
        ]
        confidence = 0.88
        follow_ups = [
            "What about the cardiac mechanism difference?",
            "How does ILD compare across the class?",
            "What\u2019s Prosinertimib\u2019s efficacy advantage?",
        ]
        return answer, sources, confidence, follow_ups

    # Pattern 3: ILD / pneumonitis / interstitial lung
    if re.search(r"ILD|pneumonitis|interstitial\s*lung", q, re.IGNORECASE):
        answer = (
            "ILD/pneumonitis is a well-characterized EGFR TKI class effect. "
            "Prosinertimib\u2019s ILD rate of 2.8% (PROSPER-1) is within the expected "
            "range for 3rd-generation agents.\n\n"
            "The proposed mechanism (HYP-2026-002, confidence 81%): EGFR signaling "
            "is critical for type II pneumocyte proliferation and alveolar epithelial "
            "repair. Potent EGFR inhibition impairs the lung\u2019s ability to repair "
            "subclinical injury, leading to progressive interstitial inflammation "
            "and fibrosis.\n\n"
            "Key evidence: Suzuki et al. (2003, PMID:12626338) demonstrated that "
            "EGFR ligands promote type II pneumocyte proliferation, and EGFR "
            "inhibition delays alveolar repair in animal models. Japanese "
            "post-marketing surveillance data shows higher ILD rates (5-10%) in "
            "the Japanese population, suggesting genetic susceptibility factors.\n\n"
            "Class comparison: erlotinib 1-3%, gefitinib 1-4% (up to 10% in Japan), "
            "afatinib 1%, osimertinib 3-4%. Prosinertimib appears to sit within the "
            "3rd-generation range.\n\n"
            "Monitoring: HRCT at baseline, respiratory symptom questionnaire at each "
            "visit, immediate drug hold and pulmonology referral for any suspected ILD."
        )
        sources = [
            {"type": "knowledge_graph", "reference": "EGFR/Type II pneumocyte pathway", "detail": "EGFR \u2192 alveolar repair \u2192 TGF-\u03b2 modulation"},
            {"type": "literature", "reference": "PMID:12626338 (Suzuki et al., 2003)", "detail": "EGFR ligands promote pneumocyte proliferation"},
            {"type": "literature", "reference": "PMID:15818571", "detail": "Japanese post-marketing ILD surveillance data"},
            {"type": "signal_data", "reference": "SIG-2026-002", "detail": "ILD signal, 23 cases, PRR 1.89"},
        ]
        confidence = 0.85
        follow_ups = [
            "Are there genetic risk factors for ILD?",
            "How does the ILD compare to gefitinib in Japan?",
            "What\u2019s the ILD management protocol?",
        ]
        return answer, sources, confidence, follow_ups

    # Pattern 4: benefit-risk / risk-benefit
    if re.search(r"benefit.?risk|risk.?benefit", q, re.IGNORECASE):
        answer = (
            "The integrated benefit-risk assessment for Prosinertimib remains "
            "**favorable** in its approved indication (2L+ EGFR-mutant NSCLC after "
            "prior EGFR TKI).\n\n"
            "**Benefits:**\n"
            "\u2022 ORR 58% vs 22% with chemotherapy (PROSPER-1)\n"
            "\u2022 Median PFS 11.2 months vs 5.4 months (HR 0.46, p<0.001)\n"
            "\u2022 CNS response rate 42% in patients with brain metastases\n"
            "\u2022 Addresses C797S resistance mutation \u2014 no other approved targeted therapy\n\n"
            "**Risks:**\n"
            "\u2022 Cardiac failure signal (1.7%, under evaluation \u2014 SIG-2026-001)\n"
            "\u2022 ILD/pneumonitis (2.8%, within class range)\n"
            "\u2022 Hepatotoxicity (22%, 3 Hy\u2019s Law cases \u2014 CYP3A4 interaction suspected)\n"
            "\u2022 Class effects: rash 45%, diarrhea 42%\n\n"
            "**Risk management:**\n"
            "\u2022 REMS program with cardiac monitoring requirements\n"
            "\u2022 RMP with ILD as important identified risk\n"
            "\u2022 Hepatic monitoring protocol with CYP3A4 inhibitor contraindication\n\n"
            "**Unmet need context:** For patients progressing on osimertinib with "
            "C797S mutation, no approved targeted therapy exists. The alternative is "
            "cytotoxic chemotherapy with significantly inferior outcomes. This "
            "substantial unmet need supports a favorable benefit-risk conclusion with "
            "appropriate risk mitigation."
        )
        sources = [
            {"type": "clinical_data", "reference": "PROSPER-1 trial", "detail": "ORR 58%, mPFS 11.2 months, HR 0.46"},
            {"type": "regulatory", "reference": "ICH E2C(R2) Section 18", "detail": "Integrated benefit-risk methodology"},
            {"type": "signal_data", "reference": "Cumulative safety data", "detail": "N=1,247 patients exposed across development program"},
            {"type": "knowledge_graph", "reference": "NSCLC treatment landscape", "detail": "No approved C797S-targeting therapy available"},
        ]
        confidence = 0.90
        follow_ups = [
            "What would change the benefit-risk assessment?",
            "How does the cardiac signal affect the profile?",
            "What are the REMS requirements?",
        ]
        return answer, sources, confidence, follow_ups

    # Pattern 5: monitoring / protocol / what should we monitor
    if re.search(r"monitoring|protocol|what\s+should\s+we\s+monitor", q, re.IGNORECASE):
        answer = (
            "Based on the current safety profile and active signals, the recommended "
            "monitoring protocol for Prosinertimib includes:\n\n"
            "**Cardiac (per SIG-2026-001):**\n"
            "\u2022 Baseline ECG and echocardiography (LVEF) before treatment initiation\n"
            "\u2022 ECG at Day 14 and monthly for first 3 months\n"
            "\u2022 LVEF assessment at 3 and 6 months, then every 6 months\n"
            "\u2022 Troponin monitoring if cardiac symptoms develop\n"
            "\u2022 Hold therapy for LVEF decrease >10% from baseline or below 50%\n\n"
            "**Pulmonary (ILD risk):**\n"
            "\u2022 Baseline HRCT\n"
            "\u2022 Respiratory symptom assessment at each visit\n"
            "\u2022 Immediate drug hold for any new/worsening respiratory symptoms\n"
            "\u2022 Urgent pulmonology referral for suspected ILD\n\n"
            "**Hepatic (per SIG-2025-019):**\n"
            "\u2022 LFTs at baseline, every 2 weeks for first 2 months, then monthly\n"
            "\u2022 Contraindicate concomitant strong CYP3A4 inhibitors\n"
            "\u2022 Hold for ALT/AST >5x ULN; discontinue for Hy\u2019s Law criteria\n\n"
            "**Standard EGFR TKI monitoring:**\n"
            "\u2022 Dermatologic assessment (rash management per MASCC guidelines)\n"
            "\u2022 GI symptom management (diarrhea protocol with loperamide)\n"
            "\u2022 Ophthalmologic referral if visual changes"
        )
        sources = [
            {"type": "regulatory", "reference": "REMS protocol", "detail": "Cardiac monitoring requirements"},
            {"type": "signal_data", "reference": "SIG-2026-001, SIG-2026-002, SIG-2025-019", "detail": "Active signals driving monitoring requirements"},
            {"type": "clinical_data", "reference": "PROSPER-1 protocol", "detail": "Baseline and on-treatment assessment schedule"},
        ]
        confidence = 0.87
        follow_ups = [
            "What triggers a dose modification?",
            "How does this compare to osimertinib\u2019s monitoring?",
            "What biomarkers should we track?",
        ]
        return answer, sources, confidence, follow_ups

    # Default fallback
    answer = (
        "I can help with questions about Prosinertimib\u2019s safety profile, including:\n\n"
        "\u2022 **Signal analysis** \u2014 cardiac failure mechanism, ILD, hepatotoxicity\n"
        "\u2022 **Class comparison** \u2014 how Prosinertimib compares to other EGFR TKIs\n"
        "\u2022 **Benefit-risk** \u2014 current assessment with efficacy and safety data\n"
        "\u2022 **Monitoring** \u2014 recommended protocols for active safety signals\n"
        "\u2022 **Mechanisms** \u2014 biological pathways connecting drug action to adverse events\n\n"
        "Try asking: \"Why might Prosinertimib cause cardiac failure?\" or "
        "\"How does the cardiac risk compare to osimertinib?\""
    )
    sources: list[dict] = []
    confidence = 0.5
    follow_ups = [
        "What is the cardiac failure mechanism?",
        "How does Prosinertimib compare to osimertinib?",
        "What is the current benefit-risk assessment?",
        "What monitoring protocol is recommended?",
    ]
    return answer, sources, confidence, follow_ups


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    answer, sources, confidence, follow_ups = _chat_respond(request.question)
    return ChatResponse(
        request_id=_make_request_id(),
        timestamp=_now().isoformat(),
        question=request.question,
        answer=answer,
        sources=[ChatSource(**s) for s in sources],
        confidence=confidence,
        follow_up_questions=follow_ups,
    )




# ---------------------------------------------------------------------------
# Detail models
# ---------------------------------------------------------------------------

class DetailSection(BaseModel):
    """A section within a detail response."""
    heading: str
    content: Any  # str, list[str], dict, list[dict]
    detail_type: str = "text"  # text, table, timeline, reference_list, key_value_pairs


class DetailResponse(BaseModel):
    """Response for the detail endpoint — deepening data for dashboard items."""
    request_id: str
    timestamp: str
    item_type: str
    item_id: str
    title: str
    summary: str
    sections: list[DetailSection]
    regulatory_references: list[Any] = []
    related_items: list[Any] = []
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Detail data store
# ---------------------------------------------------------------------------

_DETAIL_DATA: dict[tuple[str, str], dict] = {

    # -----------------------------------------------------------------------
    # SIGNALS, RISKS, DRUG CLASSES
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # SIGNAL: SIG-2026-001 — Cardiac Failure
    # -----------------------------------------------------------------------
    ("signal", "SIG-2026-001"): {
        "title": "SIG-2026-001: Prosinertimib \u2014 Cardiac Failure",
        "summary": (
            "A post-marketing signal of cardiac failure detected via disproportionality "
            "analysis. PRR 2.84 (95% CI: 1.92\u20134.21), ROR 3.12 (95% CI: 2.08\u20134.68), "
            "EBGM 2.41 (EB05: 1.67). Based on 14 spontaneous reports including 3 fatal "
            "outcomes. EGFR TKI class effect comparison shows osimertinib cardiac failure "
            "rate of 4.3% vs 1.8% for comparator TKIs (JACC CardioOncology). "
            "Median onset 3.2 months."
        ),
        "sections": [
            {
                "heading": "Case Series Summary",
                "detail_type": "text",
                "content": (
                    "14 spontaneous reports received: 8 cardiac failure, 3 LVEF decrease, "
                    "2 cardiomyopathy, 1 cardiac arrest. Outcomes: 3 fatal (21.4%), "
                    "6 hospitalized (42.9%), 5 non-serious. Median patient age 67 years "
                    "(range 52\u201381). Gender: 71% male (10/14), 29% female (4/14). "
                    "All patients had NSCLC with EGFR-activating mutations. "
                    "Pre-existing cardiac risk factors present in 9/14 patients (64%)."
                ),
            },
            {
                "heading": "Disproportionality Analysis",
                "detail_type": "table",
                "content": [
                    {"Metric": "PRR", "Value": "2.84", "95% CI": "1.92\u20134.21", "Threshold": ">2.0", "Met": "Yes"},
                    {"Metric": "ROR", "Value": "3.12", "95% CI": "2.08\u20134.68", "Threshold": ">2.0", "Met": "Yes"},
                    {"Metric": "EBGM", "Value": "2.41", "EB05": "1.67", "Threshold": "EB05 >1.0", "Met": "Yes"},
                    {"Metric": "Chi-squared", "Value": "18.7", "p-value": "<0.001", "Threshold": ">4.0", "Met": "Yes"},
                    {"Metric": "Evans criteria", "Value": "All 3 met", "95% CI": "\u2014", "Threshold": "3/3", "Met": "Yes"},
                ],
            },
            {
                "heading": "Class Effect Analysis",
                "detail_type": "table",
                "content": [
                    {"Drug": "Osimertinib", "Cardiomyopathy Rate": "2.6%", "Fatal Cardiac": "0.1%", "Mean LVEF Decrease": "22 pp", "Median Onset": "4.2 months", "Mechanism": "Kv11.1/hERG inhibition"},
                    {"Drug": "Erlotinib", "Cardiomyopathy Rate": "0.3%", "Fatal Cardiac": "<0.1%", "Mean LVEF Decrease": "N/A", "Median Onset": "N/A", "Mechanism": "Minimal cardiac signal"},
                    {"Drug": "Gefitinib", "Cardiomyopathy Rate": "0.2%", "Fatal Cardiac": "<0.1%", "Mean LVEF Decrease": "N/A", "Median Onset": "N/A", "Mechanism": "Minimal cardiac signal"},
                    {"Drug": "Afatinib", "Cardiomyopathy Rate": "0.8%", "Fatal Cardiac": "<0.1%", "Mean LVEF Decrease": "5 pp", "Median Onset": "6.1 months", "Mechanism": "Pan-HER inhibition"},
                    {"Drug": "Prosinertimib", "Cardiomyopathy Rate": "1.8%*", "Fatal Cardiac": "0.2%*", "Mean LVEF Decrease": "15 pp*", "Median Onset": "3.2 months", "Mechanism": "Under evaluation"},
                ],
            },
            {
                "heading": "Temporal Pattern",
                "detail_type": "text",
                "content": (
                    "Onset range: 1.5\u20138.2 months from treatment initiation. "
                    "Median time to onset: 3.2 months. 70% of cases (10/14) occurred within "
                    "the first 6 months of treatment. Two late-onset cases at 7.4 and 8.2 months "
                    "both had concurrent cardiotoxic chemotherapy history. Dose relationship: "
                    "12/14 cases on standard 80 mg dose, 2 on dose-reduced 40 mg."
                ),
            },
            {
                "heading": "Action Timeline",
                "detail_type": "timeline",
                "content": [
                    {"date": "2025-11-15", "event": "Signal detected via automated disproportionality screening"},
                    {"date": "2025-12-01", "event": "Signal validation completed \u2014 confirmed as valid signal"},
                    {"date": "2026-01-15", "event": "Case series review completed by signal management team"},
                    {"date": "2026-02-01", "event": "PRAC notification submitted per GVP Module IX"},
                    {"date": "2026-03-01", "event": "Current status: under evaluation \u2014 cumulative review ongoing"},
                ],
            },
            {
                "heading": "Monitoring Recommendations",
                "detail_type": "text",
                "content": [
                    "Baseline LVEF assessment (echocardiography) for patients with pre-existing cardiac risk factors",
                    "ECG at baseline, Week 4, and every 3 months thereafter",
                    "Report any new-onset dyspnea, peripheral edema, or unexplained fatigue",
                    "Consider cardiology referral for patients with LVEF <50% at baseline",
                    "Withhold treatment if LVEF decreases by \u226510 percentage points below baseline to <50%",
                    "Permanently discontinue if symptomatic heart failure develops",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "GVP IX.C.2.3", "title": "Signal Validation Criteria", "description": "Requirements for confirming a detected signal including statistical thresholds and clinical review"},
            {"code": "ICH E2C(R2) \u00a716", "title": "Signal Management in PBRER", "description": "Signal tracking and management within the Periodic Benefit-Risk Evaluation Report framework"},
            {"code": "21 CFR 314.80(c)(1)", "title": "15-Day Alert Reports", "description": "FDA requirement for expedited reporting of serious and unexpected adverse drug experiences"},
        ],
        "regulatory_references_extra": [],
        "related_items": [
            {"item_type": "risk", "item_id": "qt-prolongation", "label": "QT Prolongation Risk", "relationship": "shared cardiac mechanism"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class effect comparison"},
            {"item_type": "signal", "item_id": "SIG-2026-003", "label": "QT Prolongation Signal", "relationship": "related cardiac signal"},
        ],
        "metadata": {"detection_method": "disproportionality", "status": "under_evaluation", "priority": "high"},
    },

    # -----------------------------------------------------------------------
    # SIGNAL: SIG-2025-019 — Hepatotoxicity
    # -----------------------------------------------------------------------
    ("signal", "SIG-2025-019"): {
        "title": "SIG-2025-019: Prosinertimib \u2014 Hepatotoxicity",
        "summary": (
            "Monitoring signal for hepatotoxicity. ALT >3x ULN in 8.2% of treated patients. "
            "Two potential Hy\u2019s Law cases identified (ALT >3x ULN + bilirubin >2x ULN "
            "without elevated ALP). DILI Network classification: hepatocellular pattern."
        ),
        "sections": [
            {
                "heading": "Hy\u2019s Law Assessment",
                "detail_type": "text",
                "content": (
                    "2 potential Hy\u2019s Law cases out of 1,247 exposed patients (0.16%). "
                    "Case A: 58-year-old female, ALT 8.2x ULN, total bilirubin 3.1x ULN, "
                    "onset Day 42 of treatment. No alternative etiology identified. Resolved "
                    "14 days after drug discontinuation. "
                    "Case B: 71-year-old male, ALT 5.7x ULN, total bilirubin 2.4x ULN, "
                    "onset Day 28 of treatment. Concurrent statin use (potential confound). "
                    "Resolved 21 days after discontinuation. "
                    "Both cases meet FDA Hy\u2019s Law criteria: ALT >3x ULN + TBL >2x ULN + "
                    "no cholestatic component (ALP <2x ULN). "
                    "Estimated risk of fatal DILI with 2 Hy\u2019s Law cases: ~10% mortality rate "
                    "if drug is not withdrawn (FDA Guidance 2009)."
                ),
            },
            {
                "heading": "Hepatotoxicity Rates by Severity",
                "detail_type": "table",
                "content": [
                    {"ALT Elevation": ">1\u20133x ULN", "Incidence": "18.4%", "N": "230/1,247", "Action": "Monitor, continue treatment"},
                    {"ALT Elevation": ">3\u20135x ULN", "Incidence": "5.8%", "N": "72/1,247", "Action": "Withhold, recheck in 1 week"},
                    {"ALT Elevation": ">5\u201310x ULN", "Incidence": "1.9%", "N": "24/1,247", "Action": "Withhold, hepatology consult"},
                    {"ALT Elevation": ">10x ULN", "Incidence": "0.5%", "N": "6/1,247", "Action": "Permanently discontinue"},
                ],
            },
            {
                "heading": "EGFR TKI Class Comparison \u2014 Hepatotoxicity",
                "detail_type": "table",
                "content": [
                    {"Drug": "Gefitinib", "Hepatotox Risk": "Highest", "RR vs Placebo": "8.38", "ALT >5x ULN": "7\u201312%", "Fatal DILI": "Rare"},
                    {"Drug": "Erlotinib", "Hepatotox Risk": "Moderate\u2013High", "RR vs Placebo": "3.2\u20135.1", "ALT >5x ULN": "4\u20138%", "Fatal DILI": "Rare"},
                    {"Drug": "Afatinib", "Hepatotox Risk": "Moderate", "RR vs Placebo": "2.1", "ALT >5x ULN": "2\u20134%", "Fatal DILI": "Very rare"},
                    {"Drug": "Osimertinib", "Hepatotox Risk": "Low\u2013Moderate", "RR vs Placebo": "1.8", "ALT >5x ULN": "1\u20133%", "Fatal DILI": "Very rare"},
                    {"Drug": "Prosinertimib", "Hepatotox Risk": "Moderate", "RR vs Placebo": "3.0*", "ALT >5x ULN": "2.4%", "Fatal DILI": "0/1,247"},
                ],
            },
            {
                "heading": "Monitoring Protocol",
                "detail_type": "text",
                "content": [
                    "Baseline LFTs (ALT, AST, total bilirubin, ALP) before treatment initiation",
                    "Recheck LFTs at Week 2\u20133 of treatment",
                    "Then every 2\u20133 months during treatment, or more frequently if clinically indicated",
                    "Withhold treatment if ALT >5x ULN; recheck weekly",
                    "Resume at reduced dose if ALT returns to <3x ULN within 3 weeks",
                    "Permanently discontinue if no improvement within 3 weeks or if Hy\u2019s Law criteria met",
                ],
            },
            {
                "heading": "CTCAE v5.0 Hepatotoxicity Grading",
                "detail_type": "key_value_pairs",
                "content": {
                    "Grade 1": "ALT 1\u20133x ULN \u2014 asymptomatic, monitoring only",
                    "Grade 2": "ALT 3\u20135x ULN \u2014 symptomatic, withhold drug",
                    "Grade 3": "ALT 5\u201320x ULN \u2014 hospitalization may be required",
                    "Grade 4": "ALT >20x ULN \u2014 life-threatening, urgent intervention",
                },
            },
        ],
        "regulatory_references": [
            {"code": "FDA DILI Guidance 2009", "title": "Drug-Induced Liver Injury: Premarketing Clinical Evaluation", "description": "FDA guidance on assessing hepatotoxicity risk including Hy\u2019s Law criteria and trial monitoring"},
            {"code": "ICH E2A", "title": "Clinical Safety Data Management: Definitions and Standards", "description": "Definitions of serious adverse events including hepatic failure as a life-threatening condition"},
            {"code": "LiverTox/NCBI", "title": "LiverTox: Erlotinib Entry", "description": "National Library of Medicine resource for DILI patterns across EGFR TKI class"},
        ],
        "related_items": [
            {"item_type": "risk", "item_id": "hepatotox", "label": "Hepatotoxicity Risk Management", "relationship": "risk management plan"},
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "concurrent active signal"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class hepatotoxicity data"},
        ],
        "metadata": {"detection_method": "clinical_trial_monitoring", "status": "monitoring", "priority": "high"},
    },

    # -----------------------------------------------------------------------
    # SIGNAL: SIG-2025-014 — ILD/Pneumonitis
    # -----------------------------------------------------------------------
    ("signal", "SIG-2025-014"): {
        "title": "SIG-2025-014: Prosinertimib \u2014 Interstitial Lung Disease / Pneumonitis",
        "summary": (
            "Ongoing monitoring for interstitial lung disease, a known EGFR TKI class "
            "effect and labeled risk. ILD causes 58% of all EGFR TKI treatment-related "
            "deaths (PMC7829873). Prosinertimib observed rate: 3.8% all-grade, 1.2% "
            "Grade 3+, 0.4% fatal."
        ),
        "sections": [
            {
                "heading": "Class-Wide ILD Rates",
                "detail_type": "table",
                "content": [
                    {"Drug": "Erlotinib", "ILD Rate (Global)": "1\u20135%", "ILD Rate (Japan)": "3\u20136%", "Fatal ILD": "0.1\u20130.3%", "Generation": "1st"},
                    {"Drug": "Gefitinib", "ILD Rate (Global)": "1\u20134%", "ILD Rate (Japan)": "Up to 4%", "Fatal ILD": "0.3\u20131.6%", "Generation": "1st"},
                    {"Drug": "Afatinib", "ILD Rate (Global)": "1\u20133%", "ILD Rate (Japan)": "4\u20136%", "Fatal ILD": "0.1\u20130.4%", "Generation": "2nd"},
                    {"Drug": "Osimertinib", "ILD Rate (Global)": "4%", "ILD Rate (Japan)": "12.3%", "Fatal ILD": "0.4%", "Generation": "3rd"},
                    {"Drug": "Dacomitinib", "ILD Rate (Global)": "2\u20133%", "ILD Rate (Japan)": "5\u20137%", "Fatal ILD": "0.2%", "Generation": "2nd"},
                    {"Drug": "Prosinertimib", "ILD Rate (Global)": "3.8%", "ILD Rate (Japan)": "TBD*", "Fatal ILD": "0.4%", "Generation": "3rd"},
                ],
            },
            {
                "heading": "Geographic Variation",
                "detail_type": "text",
                "content": (
                    "Japanese patients show 2\u20133x higher ILD rates across all EGFR TKIs. "
                    "Genetic and environmental factors are implicated, including HLA subtypes "
                    "and higher prevalence of pre-existing ILD. Osimertinib Japan subpopulation: "
                    "12.3% vs 4% international rate. The gefitinib crisis in Japan (2002\u20132005) "
                    "led to 588 ILD cases and 204 deaths (PMC4155619), prompting stricter "
                    "labeling and monitoring requirements. Prosinertimib Japan clinical program "
                    "includes mandatory CT screening and pulmonologist consultation."
                ),
            },
            {
                "heading": "Management Algorithm",
                "detail_type": "text",
                "content": [
                    "1. Withhold TKI immediately upon any suspicion of ILD",
                    "2. Obtain HRCT (high-resolution CT) of chest for confirmation",
                    "3. Permanently discontinue TKI if ILD is confirmed (Grade 2+)",
                    "4. Initiate methylprednisolone 1\u20132 mg/kg IV for Grade 3\u20134",
                    "5. Oral prednisone taper over 4\u20136 weeks for Grade 2",
                    "6. Rechallenge with alternative TKI: 13.6% recurrence rate (use with caution)",
                    "7. Consider empiric antibiotics to cover concurrent infection",
                ],
            },
            {
                "heading": "CTCAE v5.0 ILD/Pneumonitis Grading",
                "detail_type": "key_value_pairs",
                "content": {
                    "Grade 1": "Asymptomatic \u2014 radiographic findings only, clinical observation",
                    "Grade 2": "Symptomatic \u2014 limiting instrumental ADL, medical intervention indicated",
                    "Grade 3": "Severe symptoms \u2014 limiting self-care ADL, oxygen indicated",
                    "Grade 4": "Life-threatening \u2014 respiratory compromise requiring urgent intervention (ventilator)",
                    "Grade 5": "Death \u2014 treatment-related mortality",
                },
            },
            {
                "heading": "Risk Factors for ILD",
                "detail_type": "text",
                "content": [
                    "Age >65 years (OR 2.1 for Grade 3+ ILD)",
                    "Japanese ethnicity (OR 2.8 across all EGFR TKIs)",
                    "Pre-existing pulmonary disease (COPD, pulmonary fibrosis)",
                    "Smoking history (current or former, >10 pack-years)",
                    "Concurrent or prior thoracic radiation therapy",
                    "Poor performance status (ECOG PS \u22652)",
                    "Prior treatment with other pneumotoxic agents (bleomycin, amiodarone)",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "GVP Module IX", "title": "Signal Management", "description": "EU guidelines for signal detection, validation, and assessment of ILD as a known class effect"},
            {"code": "TAGRISSO FDA Label \u00a75.1", "title": "Warnings \u2014 Interstitial Lung Disease/Pneumonitis", "description": "Osimertinib FDA label ILD warning serving as class reference for 3rd-gen EGFR TKIs"},
            {"code": "PMC7829873", "title": "ILD and EGFR TKI Treatment-Related Deaths", "description": "ILD accounts for 58% of all EGFR TKI treatment-related deaths \u2014 key epidemiological reference"},
            {"code": "PMC4155619", "title": "Gefitinib and Fatal ILD in Japan", "description": "Post-marketing surveillance data from the gefitinib crisis (588 ILD cases, 204 deaths)"},
        ],
        "related_items": [
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class ILD data"},
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "concurrent active signal"},
            {"item_type": "risk", "item_id": "ild", "label": "ILD Risk Management", "relationship": "risk management plan"},
        ],
        "metadata": {"detection_method": "known_class_effect", "status": "monitoring", "priority": "high"},
    },

    # -----------------------------------------------------------------------
    # SIGNAL: SIG-2026-003 — QT Prolongation
    # -----------------------------------------------------------------------
    ("signal", "SIG-2026-003"): {
        "title": "SIG-2026-003: Prosinertimib \u2014 QT Prolongation",
        "summary": (
            "Signal from ECG sub-study showing QTc prolongation. Osimertinib (class "
            "reference) shows mean QTcF change of 16.2 msec at steady state, QTc \u2265500 "
            "msec in 0.7%. Prosinertimib TQT study: mean 12.8 msec (upper 90% CI: "
            "14.3 msec)."
        ),
        "sections": [
            {
                "heading": "TQT Study Results",
                "detail_type": "key_value_pairs",
                "content": {
                    "Mean \u0394QTcF (Prosinertimib)": "12.8 msec at steady state",
                    "Upper bound 90% CI": "14.3 msec (exceeds 10 msec threshold)",
                    "QTc \u2265500 msec": "0.5% of subjects (3/600)",
                    "QTc change >60 msec": "1.2% of subjects (7/600)",
                    "Positive control (moxifloxacin)": "Assay sensitivity confirmed (\u039412.1 msec)",
                },
            },
            {
                "heading": "Concentration\u2013QTc Modeling",
                "detail_type": "text",
                "content": (
                    "Linear mixed-effects model demonstrates a concentration-dependent "
                    "relationship between prosinertimib plasma concentration and \u0394QTcF. "
                    "Slope: 0.0032 msec per ng/mL (95% CI: 0.0024\u20130.0040). At Cmax "
                    "steady state (median 4,200 ng/mL), predicted mean \u0394QTcF = 13.4 msec. "
                    "Implications: dose-dependent risk mandates caution with dose escalation "
                    "and drug interactions that increase prosinertimib exposure (CYP3A4 "
                    "inhibitors may increase Cmax by 40\u201360%, potentially pushing \u0394QTcF "
                    "to ~19\u201321 msec)."
                ),
            },
            {
                "heading": "ECG Monitoring Schedule",
                "detail_type": "text",
                "content": [
                    "Baseline 12-lead ECG (triplicate) before first dose",
                    "Day 15 ECG (triplicate) \u2014 early steady-state assessment",
                    "Monthly ECGs for first 3 months of treatment",
                    "Then every 3 months during continued treatment",
                    "Additional ECG required if dose is increased or CYP3A4 inhibitor is added",
                    "Withhold if QTc >500 msec on 2 or more ECGs",
                    "Resume at reduced dose (40 mg) when QTc <481 msec",
                    "Permanently discontinue if QTc >500 msec recurs at reduced dose",
                ],
            },
            {
                "heading": "Mechanism of QT Prolongation",
                "detail_type": "text",
                "content": (
                    "Prosinertimib inhibits Kv11.1 (hERG) potassium channels, which mediate "
                    "the rapid component of the delayed rectifier potassium current (IKr). "
                    "In vitro IC50: 8.2 \u03bcM (approximately 12x the unbound Cmax at therapeutic "
                    "dose). This provides a moderate safety margin. Osimertinib IC50 for hERG: "
                    "4.6 \u03bcM (~6x unbound Cmax), correlating with its larger clinical QTc effect. "
                    "The hERG/Cmax ratio is a key predictor of clinical QT liability."
                ),
            },
            {
                "heading": "EGFR TKI Comparator QTc Data",
                "detail_type": "table",
                "content": [
                    {"Drug": "Osimertinib", "Mean \u0394QTcF": "16.2 msec", "QTc \u2265500 msec": "0.7%", "hERG IC50": "4.6 \u03bcM", "Clinical Significance": "High \u2014 label warning"},
                    {"Drug": "Vandetanib", "Mean \u0394QTcF": "35.0 msec", "QTc \u2265500 msec": "4.3%", "hERG IC50": "0.8 \u03bcM", "Clinical Significance": "Very high \u2014 REMS required"},
                    {"Drug": "Erlotinib", "Mean \u0394QTcF": "5.2 msec", "QTc \u2265500 msec": "<0.1%", "hERG IC50": ">30 \u03bcM", "Clinical Significance": "Low"},
                    {"Drug": "Gefitinib", "Mean \u0394QTcF": "4.8 msec", "QTc \u2265500 msec": "<0.1%", "hERG IC50": ">30 \u03bcM", "Clinical Significance": "Low"},
                    {"Drug": "Afatinib", "Mean \u0394QTcF": "3.1 msec", "QTc \u2265500 msec": "<0.1%", "hERG IC50": ">50 \u03bcM", "Clinical Significance": "Minimal"},
                    {"Drug": "Dacomitinib", "Mean \u0394QTcF": "2.8 msec", "QTc \u2265500 msec": "<0.1%", "hERG IC50": ">50 \u03bcM", "Clinical Significance": "Minimal"},
                    {"Drug": "Prosinertimib", "Mean \u0394QTcF": "12.8 msec", "QTc \u2265500 msec": "0.5%", "hERG IC50": "8.2 \u03bcM", "Clinical Significance": "Moderate \u2014 monitoring required"},
                ],
            },
        ],
        "regulatory_references": [
            {"code": "ICH E14", "title": "Clinical Evaluation of QT/QTc Interval Prolongation", "description": "Guideline for thorough QT study design, analysis, and interpretation of QTc data"},
            {"code": "FDA QT Guidance 2005", "title": "Guidance for Industry: E14 Q&A", "description": "FDA implementation guidance for ICH E14 including concentration\u2013QTc analysis requirements"},
            {"code": "ICH S7B", "title": "Nonclinical Evaluation of the Potential for Delayed Ventricular Repolarization", "description": "hERG assay and in vivo QT assessment requirements for drug development"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "related cardiac signal"},
            {"item_type": "risk", "item_id": "qt-prolongation", "label": "QT Prolongation Risk Management", "relationship": "risk management plan"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class cardiac comparison"},
        ],
        "metadata": {"detection_method": "ecg_sub_study", "status": "under_evaluation", "priority": "medium"},
    },

    # -----------------------------------------------------------------------
    # SIGNAL: SIG-2025-008 — Severe Cutaneous Reactions (closed)
    # -----------------------------------------------------------------------
    ("signal", "SIG-2025-008"): {
        "title": "SIG-2025-008: Prosinertimib \u2014 Severe Cutaneous Reactions (Closed)",
        "summary": (
            "Signal closed after label update. Acneiform rash in 42% of patients "
            "(Grade 3: 3.8%). Severe cutaneous reactions (SJS/TEN-like) in 0.3%. "
            "Added to SmPC Section 4.8 and FDA label Warnings and Precautions."
        ),
        "sections": [
            {
                "heading": "Resolution Timeline",
                "detail_type": "timeline",
                "content": [
                    {"date": "2025-03-10", "event": "Signal detected \u2014 disproportionality analysis flagged severe skin reactions"},
                    {"date": "2025-05-15", "event": "Signal validation completed \u2014 confirmed as valid, 4 SJS/TEN-like cases identified"},
                    {"date": "2025-07-20", "event": "Label update approved by CHMP and FDA simultaneously"},
                    {"date": "2025-08-01", "event": "SmPC Section 4.8 and USPI Warnings & Precautions updated"},
                    {"date": "2025-08-15", "event": "Signal closed \u2014 risk adequately communicated in product labeling"},
                ],
            },
            {
                "heading": "Rash\u2013Efficacy Correlation",
                "detail_type": "text",
                "content": (
                    "Severity of acneiform skin toxicity positively correlates with treatment "
                    "response across EGFR inhibitors \u2014 patients who develop Grade 2+ rash "
                    "show significantly longer PFS and OS compared to those without rash. "
                    "This has been validated across erlotinib (HR 0.37 for OS in rash vs no-rash), "
                    "gefitinib, afatinib, and cetuximab. Rash serves as a surrogate marker for "
                    "adequate EGFR pathway inhibition in skin keratinocytes. "
                    "Prosinertimib data consistent: median PFS 14.2 months in patients with "
                    "Grade 2+ rash vs 8.7 months without rash (HR 0.52, p=0.003)."
                ),
            },
            {
                "heading": "Management Ladder",
                "detail_type": "text",
                "content": [
                    "Grade 1: Moisturizer + broad-spectrum sunscreen (SPF 30+) + topical hydrocortisone 1%",
                    "Grade 2: Add topical clindamycin 1% gel + oral doxycycline 100 mg BID + consider dose maintenance",
                    "Grade 3: Dose reduction by one level + systemic corticosteroids (prednisone 0.5 mg/kg) + dermatology referral",
                    "SJS/TEN suspected: Immediately discontinue drug, hospitalize, dermatology/burn unit consultation",
                ],
            },
            {
                "heading": "EGFR TKI Class Skin Toxicity Rates",
                "detail_type": "table",
                "content": [
                    {"Drug": "Afatinib", "Any Grade Rash": "69\u201389%", "Grade 3+ Rash": "9\u201316%", "Paronychia": "33\u201357%", "Stomatitis": "30\u201370%"},
                    {"Drug": "Dacomitinib", "Any Grade Rash": ">80%", "Grade 3+ Rash": "10\u201315%", "Paronychia": "50\u201363%", "Stomatitis": "40\u201371%"},
                    {"Drug": "Erlotinib", "Any Grade Rash": "37\u201376%", "Grade 3+ Rash": "3\u20139%", "Paronychia": "4\u201316%", "Stomatitis": "3\u20139%"},
                    {"Drug": "Gefitinib", "Any Grade Rash": "37\u201354%", "Grade 3+ Rash": "3\u20138%", "Paronychia": "2\u20137%", "Stomatitis": "3\u20136%"},
                    {"Drug": "Osimertinib", "Any Grade Rash": "20\u201340%", "Grade 3+ Rash": "<5%", "Paronychia": "25\u201335%", "Stomatitis": "10\u201315%"},
                    {"Drug": "Prosinertimib", "Any Grade Rash": "42%", "Grade 3+ Rash": "3.8%", "Paronychia": "18%", "Stomatitis": "12%"},
                ],
            },
            {
                "heading": "Prophylactic Strategies",
                "detail_type": "text",
                "content": (
                    "The STEPP trial demonstrated that prophylactic skin treatment with "
                    "moisturizer + sunscreen + topical corticosteroid + oral doxycycline "
                    "reduced Grade 2+ skin toxicity from 62% to 33% in patients receiving "
                    "EGFR TKIs. This prophylactic approach is now recommended in ESMO and "
                    "NCCN guidelines for all patients initiating EGFR TKI therapy. "
                    "Prosinertimib prescribing information includes recommendation for "
                    "prophylactic doxycycline consideration in high-risk patients."
                ),
            },
        ],
        "regulatory_references": [
            {"code": "SmPC \u00a74.8", "title": "Undesirable Effects \u2014 Updated August 2025", "description": "Skin and subcutaneous disorders section updated with SJS/TEN-like reactions at frequency 'rare'"},
            {"code": "USPI W&P", "title": "Warnings and Precautions \u2014 Dermatologic Reactions", "description": "FDA label updated with severe cutaneous adverse reaction warning and management guidance"},
            {"code": "STEPP Trial", "title": "Skin Toxicity Evaluation Protocol with Panitumumab (adapted)", "description": "Landmark trial demonstrating benefit of prophylactic skin care for EGFR inhibitor skin toxicity"},
        ],
        "related_items": [
            {"item_type": "risk", "item_id": "skin-tox", "label": "Skin Toxicity Risk Management", "relationship": "risk management plan"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class skin toxicity data"},
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "other active signal"},
        ],
        "metadata": {"detection_method": "disproportionality", "status": "closed", "priority": "resolved"},
    },

    # -----------------------------------------------------------------------
    # RISK: ILD/Pneumonitis
    # -----------------------------------------------------------------------
    ("risk", "ild"): {
        "title": "Risk: Interstitial Lung Disease / Pneumonitis",
        "summary": (
            "ILD is a known class effect of EGFR TKIs and the leading cause of "
            "treatment-related death (58% of EGFR TKI fatalities). Prosinertimib "
            "all-grade rate: 3.8%, Grade 3+: 1.2%, fatal: 0.4%. Included in EU-RMP "
            "as an important identified risk and in FDA label Warnings and Precautions."
        ),
        "sections": [
            {
                "heading": "Risk Minimization Measures",
                "detail_type": "text",
                "content": [
                    "Product labeling: SmPC Section 4.4 and 4.8; USPI Warnings and Precautions Section 5.1",
                    "Patient Alert Card: distributed with each dispensing, includes ILD symptom checklist",
                    "HCP Educational Materials: slide deck and pocket guide for oncologists/pulmonologists",
                    "Dear Healthcare Professional Communication (DHPC) issued at initial approval",
                    "Mandatory patient counseling on symptoms (cough, dyspnea, fever) at treatment initiation",
                ],
            },
            {
                "heading": "Monitoring Protocol",
                "detail_type": "text",
                "content": [
                    "Baseline chest CT or X-ray before treatment initiation",
                    "Clinical assessment for respiratory symptoms at each visit",
                    "Low-threshold chest imaging for any new respiratory symptoms",
                    "Immediate HRCT if ILD suspected (do not wait for chest X-ray result)",
                    "Pulmonary function tests (DLCO) if pre-existing pulmonary disease",
                ],
            },
            {
                "heading": "Dose Modification Algorithm",
                "detail_type": "key_value_pairs",
                "content": {
                    "Grade 1 (asymptomatic)": "Withhold, HRCT in 2 weeks. Resume if stable/improved.",
                    "Grade 2 (symptomatic)": "Permanently discontinue. Oral prednisone 0.5\u20131 mg/kg taper.",
                    "Grade 3 (severe)": "Permanently discontinue. IV methylprednisolone 1\u20132 mg/kg.",
                    "Grade 4 (life-threatening)": "Permanently discontinue. ICU care, IV corticosteroids, ventilatory support.",
                },
            },
            {
                "heading": "Rechallenge Data",
                "detail_type": "text",
                "content": (
                    "Rechallenge with the same EGFR TKI after ILD resolution is generally "
                    "not recommended due to high recurrence risk. Cross-class rechallenge "
                    "data: 13.6% ILD recurrence rate when switching to an alternative EGFR TKI "
                    "after ILD recovery. If rechallenge is considered: minimum 4-week washout, "
                    "complete ILD resolution on imaging, close monitoring with CT at Weeks 2, "
                    "4, and 8, and pulmonologist oversight required."
                ),
            },
            {
                "heading": "Patient Education Points",
                "detail_type": "text",
                "content": [
                    "Report immediately: new or worsening cough, shortness of breath, fever",
                    "Do not dismiss mild respiratory symptoms as \u2018common cold\u2019",
                    "Carry Patient Alert Card at all times; show to any treating physician",
                    "Avoid exposure to known respiratory irritants (dust, fumes, mold)",
                    "Annual influenza vaccination recommended; COVID-19 vaccination per guidelines",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "EU-RMP \u00a7VI.2", "title": "Important Identified Risk: ILD/Pneumonitis", "description": "ILD listed as important identified risk in Risk Management Plan with routine and additional risk minimization"},
            {"code": "FDA Label \u00a75.1", "title": "Warnings and Precautions: ILD/Pneumonitis", "description": "FDA-mandated warning for ILD including incidence rates, monitoring requirements, and dose modifications"},
            {"code": "PMC7829873", "title": "EGFR TKI-Related ILD Mortality", "description": "58% of all EGFR TKI treatment-related deaths attributed to ILD across class"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2025-014", "label": "ILD/Pneumonitis Signal", "relationship": "active monitoring signal"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class ILD rates"},
            {"item_type": "risk", "item_id": "hepatotox", "label": "Hepatotoxicity Risk", "relationship": "concurrent identified risk"},
        ],
        "metadata": {"risk_category": "important_identified_risk", "rmp_section": "VI.2", "risk_level": "high"},
    },

    # -----------------------------------------------------------------------
    # RISK: Hepatotoxicity
    # -----------------------------------------------------------------------
    ("risk", "hepatotox"): {
        "title": "Risk: Hepatotoxicity",
        "summary": (
            "Hepatotoxicity is an important identified risk for prosinertimib with "
            "ALT >3x ULN in 8.2% of patients. Two potential Hy\u2019s Law cases in 1,247 "
            "exposed patients. DILI Network classification: hepatocellular pattern. "
            "Class effect across EGFR TKIs with gefitinib showing highest risk (RR 8.38)."
        ),
        "sections": [
            {
                "heading": "Hy\u2019s Law Criteria",
                "detail_type": "key_value_pairs",
                "content": {
                    "Criterion 1": "ALT or AST >3x ULN (drug-induced hepatocellular injury)",
                    "Criterion 2": "Total bilirubin >2x ULN (indicates significant liver dysfunction)",
                    "Criterion 3": "No alternative explanation (viral hepatitis, alcohol, other drugs)",
                    "ALP criterion": "ALP <2x ULN (rules out cholestatic/biliary obstruction)",
                    "Prosinertimib cases": "2/1,247 (0.16%) met all Hy\u2019s Law criteria",
                    "Implication": "~10% risk of fatal DILI in Hy\u2019s Law population if drug not withdrawn",
                },
            },
            {
                "heading": "Monitoring Schedule",
                "detail_type": "table",
                "content": [
                    {"Timepoint": "Baseline", "Tests": "ALT, AST, TBL, ALP, albumin", "Frequency": "Before first dose", "Action": "Do not initiate if ALT >3x ULN"},
                    {"Timepoint": "Week 2\u20133", "Tests": "ALT, AST, TBL", "Frequency": "Once", "Action": "Early detection of rapid-onset hepatotoxicity"},
                    {"Timepoint": "Monthly \u00d73", "Tests": "ALT, AST, TBL", "Frequency": "Monthly", "Action": "Monitor during dose stabilization"},
                    {"Timepoint": "Ongoing", "Tests": "ALT, AST, TBL", "Frequency": "Every 2\u20133 months", "Action": "Routine surveillance"},
                    {"Timepoint": "As needed", "Tests": "Full hepatic panel", "Frequency": "If symptoms arise", "Action": "Investigate jaundice, RUQ pain, fatigue"},
                ],
            },
            {
                "heading": "Dose Modification Rules",
                "detail_type": "key_value_pairs",
                "content": {
                    "ALT 3\u20135x ULN": "Withhold; recheck weekly. Resume at same dose if <3x ULN within 2 weeks.",
                    "ALT 5\u201310x ULN": "Withhold; hepatology consult. Resume at reduced dose (40 mg) if <3x ULN within 3 weeks.",
                    "ALT >10x ULN": "Permanently discontinue. Hepatology follow-up required.",
                    "Hy\u2019s Law met": "Permanently discontinue. Report as serious ADR. Close clinical follow-up.",
                    "Re-elevation on rechallenge": "Permanently discontinue. Do not rechallenge again.",
                },
            },
            {
                "heading": "DILI Network Classification",
                "detail_type": "text",
                "content": (
                    "Drug-Induced Liver Injury Network (DILIN) classification for prosinertimib: "
                    "Pattern: hepatocellular (R-value >5). Latency: short-intermediate "
                    "(median 35 days, range 14\u201390 days). Severity: mostly mild-moderate "
                    "(DILIN severity score 1\u20132 in 92% of cases). Mechanism: suspected "
                    "reactive metabolite formation via CYP3A4 \u2014 N-desmethyl metabolite "
                    "shows higher hepatocyte toxicity in vitro than parent compound."
                ),
            },
            {
                "heading": "Patient Education Points",
                "detail_type": "text",
                "content": [
                    "Report immediately: yellowing of skin/eyes, dark urine, right upper abdominal pain",
                    "Avoid excessive alcohol consumption during treatment",
                    "Inform treating physician of all other medications (especially acetaminophen, statins, azole antifungals)",
                    "Attend all scheduled blood test appointments \u2014 liver monitoring is essential",
                    "Carry Patient Alert Card listing hepatotoxicity as a known risk",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "FDA DILI Guidance 2009", "title": "Premarketing Clinical Evaluation of DILI", "description": "FDA framework for assessing hepatotoxicity risk including Hy\u2019s Law, monitoring algorithms, and labeling"},
            {"code": "EU-RMP \u00a7VI.2", "title": "Important Identified Risk: Hepatotoxicity", "description": "Hepatotoxicity in Risk Management Plan with dose modification algorithm and monitoring requirements"},
            {"code": "ICH E2A", "title": "Clinical Safety Data Management", "description": "Definitions for seriousness including hepatic failure as a life-threatening adverse event"},
            {"code": "DILIN Classification", "title": "Drug-Induced Liver Injury Network", "description": "Standardized causality assessment and classification system for DILI"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2025-019", "label": "Hepatotoxicity Signal", "relationship": "active monitoring signal"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class hepatotoxicity comparison"},
            {"item_type": "risk", "item_id": "ild", "label": "ILD Risk Management", "relationship": "concurrent identified risk"},
        ],
        "metadata": {"risk_category": "important_identified_risk", "rmp_section": "VI.2", "risk_level": "high"},
    },

    # -----------------------------------------------------------------------
    # RISK: QT Prolongation
    # -----------------------------------------------------------------------
    ("risk", "qt-prolongation"): {
        "title": "Risk: QT/QTc Interval Prolongation",
        "summary": (
            "QTc prolongation is an important identified risk based on the TQT study "
            "showing mean \u0394QTcF of 12.8 msec (upper 90% CI: 14.3 msec). Concentration-"
            "dependent effect with implications for dose modifications and drug interactions. "
            "ICH E14 regulatory threshold (10 msec) exceeded."
        ),
        "sections": [
            {
                "heading": "Risk Minimization Measures",
                "detail_type": "text",
                "content": [
                    "Product labeling: SmPC Section 4.4 warning + ECG monitoring recommendations",
                    "Contraindication: congenital long QT syndrome (SmPC Section 4.3)",
                    "Drug interaction warnings: CYP3A4 inhibitors, other QT-prolonging drugs (SmPC Section 4.5)",
                    "Patient Alert Card: includes instruction to report palpitations, syncope, dizziness",
                    "HCP communication: ECG monitoring protocol distributed to prescribers",
                ],
            },
            {
                "heading": "ECG Monitoring Intervals",
                "detail_type": "table",
                "content": [
                    {"Timepoint": "Baseline", "ECG Type": "Triplicate 12-lead", "Timing": "Before first dose", "Action": "Do not initiate if QTc >480 msec"},
                    {"Timepoint": "Day 15", "ECG Type": "Triplicate 12-lead", "Timing": "Trough and 2h post-dose", "Action": "Early steady-state check"},
                    {"Timepoint": "Month 1\u20133", "ECG Type": "Single 12-lead", "Timing": "Monthly", "Action": "Routine monitoring"},
                    {"Timepoint": "Month 3+", "ECG Type": "Single 12-lead", "Timing": "Every 3 months", "Action": "Ongoing surveillance"},
                    {"Timepoint": "Dose change", "ECG Type": "Triplicate 12-lead", "Timing": "1 week after change", "Action": "Re-assess at new exposure level"},
                    {"Timepoint": "New QT drug added", "ECG Type": "Triplicate 12-lead", "Timing": "Within 1 week", "Action": "Assess combined effect"},
                ],
            },
            {
                "heading": "Dose Modification for QTc",
                "detail_type": "key_value_pairs",
                "content": {
                    "QTc 481\u2013500 msec": "Withhold until QTc <481 msec. Resume at reduced dose (40 mg).",
                    "QTc >500 msec (single)": "Withhold. Repeat ECG within 24 hours. Electrolyte correction.",
                    "QTc >500 msec (confirmed)": "Withhold until QTc <481 msec. Resume at 40 mg with weekly ECG \u00d74.",
                    "QTc >500 msec on 40 mg": "Permanently discontinue.",
                    "\u0394QTc >60 msec from baseline": "Withhold. Cardiology consultation. Resume only if QTc normalizes.",
                    "Torsades de Pointes": "Permanently discontinue. IV magnesium. Cardiology emergency.",
                },
            },
            {
                "heading": "Concomitant Medication Warnings",
                "detail_type": "text",
                "content": [
                    "Strong CYP3A4 inhibitors (ketoconazole, itraconazole, clarithromycin): increase prosinertimib exposure 40\u201360% \u2014 avoid or reduce dose",
                    "Other QT-prolonging drugs (ondansetron, fluoroquinolones, antiarrhythmics): additive QTc risk \u2014 ECG monitoring required",
                    "Drugs causing electrolyte imbalance (diuretics, laxatives): hypokalemia/hypomagnesemia increase QT risk \u2014 correct electrolytes before initiating",
                    "Grapefruit juice: moderate CYP3A4 inhibition \u2014 avoid during treatment",
                ],
            },
            {
                "heading": "Patient Education Points",
                "detail_type": "text",
                "content": [
                    "Report immediately: palpitations, feeling faint or dizzy, fainting episodes (syncope)",
                    "Inform all healthcare providers about prosinertimib treatment for QT interaction checks",
                    "Maintain adequate hydration; avoid excessive vomiting/diarrhea without medical advice",
                    "Do not take new medications (including OTC) without consulting prescriber",
                    "Attend all scheduled ECG appointments \u2014 cardiac monitoring is mandatory",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "ICH E14", "title": "Clinical Evaluation of QT/QTc Interval Prolongation", "description": "ICH guideline defining TQT study design and regulatory threshold of 10 msec for QTc prolongation"},
            {"code": "FDA QT Guidance 2005", "title": "E14 Implementation Guidance", "description": "FDA questions and answers on TQT studies, concentration\u2013QTc analysis, and labeling implications"},
            {"code": "ICH S7B", "title": "Nonclinical Cardiac Safety", "description": "Requirements for hERG assay, in vivo QT assessment, and integrated risk evaluation"},
            {"code": "SmPC \u00a74.3/4.4/4.5", "title": "Contraindications, Warnings, Interactions", "description": "Product label sections addressing QT risk, concomitant drug warnings, and monitoring"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2026-003", "label": "QT Prolongation Signal", "relationship": "active signal under evaluation"},
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "related cardiac risk"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class QTc comparison"},
        ],
        "metadata": {"risk_category": "important_identified_risk", "rmp_section": "VI.2", "risk_level": "high"},
    },

    # -----------------------------------------------------------------------
    # RISK: Skin Toxicity
    # -----------------------------------------------------------------------
    ("risk", "skin-tox"): {
        "title": "Risk: Dermatologic / Skin Toxicity",
        "summary": (
            "Acneiform rash is the most common adverse event with EGFR TKIs, occurring "
            "in 42% of prosinertimib-treated patients (Grade 3: 3.8%). Severe cutaneous "
            "reactions (SJS/TEN-like) are rare (0.3%) but serious. Rash severity "
            "correlates with treatment efficacy. Signal SIG-2025-008 closed after "
            "label update in August 2025."
        ),
        "sections": [
            {
                "heading": "Risk Minimization Measures",
                "detail_type": "text",
                "content": [
                    "Product labeling: SmPC Section 4.4 (special warnings) and 4.8 (undesirable effects)",
                    "Patient Alert Card: skin toxicity section with photo examples of Grade 1\u20133 rash",
                    "HCP Educational Materials: management ladder poster for clinic display",
                    "Prophylactic skin care recommendation in prescribing information",
                    "Dermatology referral pathway established for Grade 3+ cases",
                ],
            },
            {
                "heading": "Management Ladder",
                "detail_type": "table",
                "content": [
                    {"Grade": "1 (Mild)", "Symptoms": "Papules/pustules <10% BSA", "Treatment": "Moisturizer + SPF 30+ sunscreen + topical hydrocortisone 1%", "Dose Action": "Continue treatment"},
                    {"Grade": "2 (Moderate)", "Symptoms": "Papules/pustules 10\u201330% BSA, pruritic", "Treatment": "Topical clindamycin 1% + oral doxycycline 100 mg BID", "Dose Action": "Continue, consider prophylaxis"},
                    {"Grade": "3 (Severe)", "Symptoms": "Papules/pustules >30% BSA, limiting ADL", "Treatment": "Dose reduction + systemic corticosteroids + dermatology referral", "Dose Action": "Reduce to 40 mg"},
                    {"Grade": "SJS/TEN", "Symptoms": "Blistering, mucosal involvement, epidermal detachment", "Treatment": "Immediate discontinuation, hospitalization, burn unit if TEN", "Dose Action": "Permanently discontinue"},
                ],
            },
            {
                "heading": "Efficacy Correlation",
                "detail_type": "text",
                "content": (
                    "Rash severity serves as a pharmacodynamic biomarker for EGFR inhibition. "
                    "Meta-analysis across EGFR TKI trials (n=1,781) demonstrates that patients "
                    "developing Grade 2+ skin toxicity have significantly better outcomes: "
                    "OS HR 0.51 (95% CI: 0.40\u20130.65, p<0.001), PFS HR 0.55 (95% CI: "
                    "0.44\u20130.68, p<0.001). Prosinertimib-specific data: median PFS 14.2 "
                    "months (rash) vs 8.7 months (no rash), HR 0.52 (p=0.003). This suggests "
                    "that aggressive rash management (maintaining dose intensity) may be "
                    "preferable to dose reduction for mild-moderate skin toxicity."
                ),
            },
            {
                "heading": "Prophylactic Doxycycline (STEPP Trial)",
                "detail_type": "text",
                "content": (
                    "The STEPP trial (Skin Toxicity Evaluation Protocol with Panitumumab) "
                    "randomized 95 patients to pre-emptive vs reactive skin treatment. "
                    "Pre-emptive arm received: moisturizer + sunscreen + topical hydrocortisone "
                    "1% + oral doxycycline 100 mg BID from Day 1 of EGFR inhibitor therapy. "
                    "Results: Grade 2+ skin toxicity reduced from 62% to 29% (p<0.001). "
                    "No impact on treatment efficacy (PFS/OS similar between arms). "
                    "Now recommended by ESMO and NCCN guidelines. Prosinertimib prescribing "
                    "information recommends considering prophylactic doxycycline for patients "
                    "at high risk of skin toxicity."
                ),
            },
            {
                "heading": "Patient Education Points",
                "detail_type": "text",
                "content": [
                    "Skin rash is expected and may indicate the drug is working \u2014 do not stop treatment without medical advice",
                    "Apply fragrance-free moisturizer twice daily and SPF 30+ sunscreen to exposed areas",
                    "Avoid hot water, harsh soaps, and alcohol-based skin products",
                    "Report immediately: widespread blistering, mouth/eye sores, skin peeling (may indicate SJS/TEN)",
                    "Nail changes (paronychia) are common \u2014 wear gloves for wet work, avoid tight shoes",
                ],
            },
        ],
        "regulatory_references": [
            {"code": "SmPC \u00a74.4/4.8", "title": "Special Warnings and Undesirable Effects", "description": "Updated August 2025 with severe cutaneous reactions warning and SJS/TEN-like reactions (frequency: rare)"},
            {"code": "STEPP Trial", "title": "Prophylactic Skin Treatment for EGFR Inhibitors", "description": "Lacouture et al. \u2014 pre-emptive skin care reduces Grade 2+ skin toxicity from 62% to 29%"},
            {"code": "EU-RMP \u00a7VI.2", "title": "Important Identified Risk: Skin Toxicity", "description": "Skin toxicity in RMP with routine risk minimization (labeling) and additional measures (patient card, HCP materials)"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2025-008", "label": "Severe Cutaneous Reactions Signal (Closed)", "relationship": "closed signal after label update"},
            {"item_type": "drug_class", "item_id": "egfr-tki", "label": "EGFR TKI Class Profile", "relationship": "class skin toxicity comparison"},
            {"item_type": "risk", "item_id": "ild", "label": "ILD Risk Management", "relationship": "concurrent identified risk"},
        ],
        "metadata": {"risk_category": "important_identified_risk", "rmp_section": "VI.2", "risk_level": "moderate"},
    },

    # -----------------------------------------------------------------------
    # DRUG CLASS: EGFR TKI
    # -----------------------------------------------------------------------
    ("drug_class", "egfr-tki"): {
        "title": "Drug Class: EGFR Tyrosine Kinase Inhibitors",
        "summary": (
            "Prosinertimib is a 3rd-generation mutant-selective EGFR TKI for NSCLC. "
            "Five EGFR TKIs are currently marketed: erlotinib (1st-gen, 2004), "
            "gefitinib (1st-gen, 2003/2015), afatinib (2nd-gen, 2013), osimertinib "
            "(3rd-gen, 2015), dacomitinib (2nd-gen, 2018)."
        ),
        "sections": [
            {
                "heading": "Drug Comparison",
                "detail_type": "table",
                "content": [
                    {
                        "Drug": "Erlotinib (Tarceva)",
                        "Generation": "1st",
                        "Target": "EGFR (reversible)",
                        "Approval": "2004",
                        "ILD Rate": "1\u20135%",
                        "Cardiac Signal": "Minimal",
                        "Diarrhea": "48\u201362%",
                        "Rash": "37\u201376%",
                    },
                    {
                        "Drug": "Gefitinib (Iressa)",
                        "Generation": "1st",
                        "Target": "EGFR (reversible)",
                        "Approval": "2003/2015",
                        "ILD Rate": "1\u20134%",
                        "Cardiac Signal": "Minimal",
                        "Diarrhea": "35\u201347%",
                        "Rash": "37\u201354%",
                    },
                    {
                        "Drug": "Afatinib (Gilotrif)",
                        "Generation": "2nd",
                        "Target": "Pan-HER (irreversible)",
                        "Approval": "2013",
                        "ILD Rate": "1\u20133%",
                        "Cardiac Signal": "Low",
                        "Diarrhea": "87\u201396%",
                        "Rash": "69\u201389%",
                    },
                    {
                        "Drug": "Dacomitinib (Vizimpro)",
                        "Generation": "2nd",
                        "Target": "Pan-HER (irreversible)",
                        "Approval": "2018",
                        "ILD Rate": "2\u20133%",
                        "Cardiac Signal": "Minimal",
                        "Diarrhea": "78\u201387%",
                        "Rash": ">80%",
                    },
                    {
                        "Drug": "Osimertinib (Tagrisso)",
                        "Generation": "3rd",
                        "Target": "EGFR T790M (irreversible)",
                        "Approval": "2015",
                        "ILD Rate": "4% (12.3% Japan)",
                        "Cardiac Signal": "QTc + LVEF",
                        "Diarrhea": "42\u201348%",
                        "Rash": "20\u201340%",
                    },
                    {
                        "Drug": "Prosinertimib",
                        "Generation": "3rd",
                        "Target": "EGFR mutant-selective (irreversible)",
                        "Approval": "2025",
                        "ILD Rate": "3.8%",
                        "Cardiac Signal": "QTc + under eval",
                        "Diarrhea": "38\u201345%",
                        "Rash": "42%",
                    },
                ],
            },
            {
                "heading": "Class Mechanism of Action",
                "detail_type": "text",
                "content": (
                    "EGFR (ErbB1/HER1) is a receptor tyrosine kinase that drives cell "
                    "proliferation, survival, and migration via RAS/MAPK and PI3K/AKT "
                    "pathways. Activating mutations in EGFR (exon 19 deletion, L858R point "
                    "mutation) are found in 10\u201315% of Western NSCLC patients and 30\u201350% "
                    "of Asian patients. EGFR TKIs competitively bind the ATP-binding site of "
                    "the EGFR kinase domain. Generational differences: 1st-generation "
                    "(reversible, EGFR-specific), 2nd-generation (irreversible, pan-HER \u2014 "
                    "inhibits EGFR/HER2/HER4), 3rd-generation (irreversible, mutant-selective "
                    "\u2014 spares wild-type EGFR, active against T790M resistance mutation)."
                ),
            },
            {
                "heading": "Regulatory History",
                "detail_type": "timeline",
                "content": [
                    {"date": "2003-07", "event": "Gefitinib (Iressa) first approved in Japan for NSCLC"},
                    {"date": "2003-05", "event": "Gefitinib approved by FDA via accelerated approval"},
                    {"date": "2004-11", "event": "Erlotinib (Tarceva) approved by FDA for advanced NSCLC"},
                    {"date": "2005-06", "event": "Gefitinib restricted in US after ISEL trial failed to show OS benefit"},
                    {"date": "2013-07", "event": "Afatinib (Gilotrif) approved by FDA for EGFR-mutant NSCLC"},
                    {"date": "2015-07", "event": "Gefitinib re-approved by FDA with companion diagnostic requirement"},
                    {"date": "2015-11", "event": "Osimertinib (Tagrisso) approved via breakthrough therapy for T790M+ NSCLC"},
                    {"date": "2018-09", "event": "Dacomitinib (Vizimpro) approved for first-line EGFR-mutant NSCLC"},
                    {"date": "2018-04", "event": "Osimertinib approved as first-line treatment (FLAURA trial)"},
                    {"date": "2025-06", "event": "Prosinertimib approved for EGFR-mutant NSCLC with differentiated safety profile"},
                ],
            },
            {
                "heading": "Safety Differentiation by Generation",
                "detail_type": "key_value_pairs",
                "content": {
                    "1st-generation (erlotinib, gefitinib)": "Reversible, EGFR-specific. Lower diarrhea/rash vs 2nd-gen. Gefitinib: hepatotoxicity concern. Erlotinib: higher rash rate.",
                    "2nd-generation (afatinib, dacomitinib)": "Irreversible, pan-HER. Highest diarrhea (87\u201396%) and rash (69\u201389%) rates due to wild-type EGFR/HER2 inhibition. Better efficacy vs 1st-gen.",
                    "3rd-generation (osimertinib, prosinertimib)": "Irreversible, mutant-selective. Lower skin/GI toxicity. New concern: cardiac effects (QTc prolongation, LVEF decrease). Better CNS penetration.",
                },
            },
            {
                "heading": "Prosinertimib Positioning",
                "detail_type": "text",
                "content": (
                    "Prosinertimib is positioned as a 3rd-generation mutant-selective EGFR "
                    "TKI with a differentiated cardiac safety profile compared to osimertinib. "
                    "Key differentiators: lower mean QTcF prolongation (12.8 msec vs 16.2 msec), "
                    "higher hERG IC50 safety margin (12x vs 6x), and potentially lower LVEF "
                    "decrease signal. Trade-offs: slightly higher rash rate (42% vs 20\u201340%) "
                    "and hepatotoxicity signal requiring monitoring. Clinical program includes "
                    "head-to-head cardiac safety comparison vs osimertinib (CARDIAC-EGFR trial, "
                    "expected readout 2027). Target population: patients with EGFR-mutant "
                    "NSCLC who have cardiac comorbidities or risk factors where osimertinib\u2019s "
                    "cardiac profile may be a concern."
                ),
            },
        ],
        "regulatory_references": [
            {"code": "FDA Oncology CDx", "title": "Companion Diagnostic Requirements for EGFR TKIs", "description": "FDA requirement for validated EGFR mutation testing before prescribing EGFR TKIs"},
            {"code": "ICH E2C(R2)", "title": "PBRER for Class-Level Safety Review", "description": "Periodic benefit-risk evaluation including class effect analysis for EGFR TKI safety signals"},
            {"code": "EMA CHMP Assessment", "title": "Prosinertimib EPAR", "description": "European public assessment report including class comparison and benefit-risk assessment"},
            {"code": "PMC4155619", "title": "Gefitinib and the EGFR TKI ILD Crisis in Japan", "description": "Historical analysis of gefitinib-related ILD deaths that shaped EGFR TKI class safety monitoring"},
        ],
        "related_items": [
            {"item_type": "signal", "item_id": "SIG-2026-001", "label": "Cardiac Failure Signal", "relationship": "active class-effect signal"},
            {"item_type": "signal", "item_id": "SIG-2025-014", "label": "ILD/Pneumonitis Signal", "relationship": "known class-effect risk"},
            {"item_type": "risk", "item_id": "qt-prolongation", "label": "QT Prolongation Risk", "relationship": "3rd-gen class concern"},
        ],
        "metadata": {"class_size": 6, "generations": ["1st", "2nd", "3rd"], "therapeutic_area": "NSCLC"},
    },


    # -----------------------------------------------------------------------
    # ROLES
    # -----------------------------------------------------------------------
    ("role", "head-ps"): {
        "title": "Head of Patient Safety / Pharmacovigilance",
        "summary": (
            "Global safety lead responsible for benefit-risk management, signal detection oversight, "
            "and regulatory compliance. Reports to CMO. Regulatory mandate per GVP Module I.4 (EU) "
            "and 21 CFR 312.32 (US)."
        ),
        "sections": [
            {
                "heading": "Key Responsibilities",
                "content": [
                    "Oversee signal detection, validation, and assessment across all products",
                    "Provide strategic oversight for PBRER/PSUR and DSUR authoring",
                    "Lead interactions with regulatory authorities on safety matters (EMA, FDA, MHRA)",
                    "Serve as primary sponsor liaison to DSMBs across clinical trial programs",
                    "Drive safety labeling strategy including SmPC/USPI updates",
                    "Support QPPV in maintaining the Pharmacovigilance System Master File (PSMF)",
                    "Oversee CRO and vendor performance for pharmacovigilance activities",
                    "Chair the Safety Management Team (SMT) and safety governance meetings",
                    "Lead aggregate benefit-risk assessments integrating clinical, preclinical, and epidemiological data",
                    "Approve safety communications including Dear Healthcare Professional Communications (DHPCs)",
                ],
            },
            {
                "heading": "Regulatory Mandate",
                "content": [
                    "GVP Module I.4: MAH must appoint appropriately qualified person responsible for safety oversight",
                    "Must ensure adequate resources for pharmacovigilance system operation",
                    "Responsible for quality and integrity of safety data submitted to regulators",
                    "Ensures timely submission of all expedited and periodic safety reports",
                    "Must maintain awareness of emerging safety issues across all products in portfolio",
                ],
            },
            {
                "heading": "Required Qualifications",
                "content": [
                    "MD, PharmD, or equivalent doctoral-level medical/pharmaceutical degree",
                    "Minimum 10 years of pharmacovigilance experience in pharmaceutical industry",
                    "Demonstrated experience with regulatory submissions (BLA, NDA, MAA safety sections)",
                    "Prior leadership of signal management and risk management programs",
                    "Experience presenting to regulatory advisory committees",
                ],
            },
            {
                "heading": "Decision Authority",
                "content": [
                    {"key": "Escalation to CMO", "value": "Any validated signal with potential for label change, SUSAR cluster, or Hy's Law case"},
                    {"key": "Label change recommendation", "value": "Authority to recommend SmPC/USPI updates to SRC; requires SRC vote for implementation"},
                    {"key": "Clinical trial safety halt", "value": "Authority to recommend suspension of dosing pending DSMB review; CMO approval required for formal clinical hold"},
                    {"key": "Urgent safety measure", "value": "Authority to initiate EU urgent safety restriction per Article 22 of Regulation 726/2004"},
                    {"key": "Vendor escalation", "value": "Authority to issue CAPAs to CRO vendors and recommend contract remediation"},
                ],
            },
            {
                "heading": "Key Interactions",
                "content": [
                    {"key": "Weekly", "value": "Signal management team, CRO oversight calls, case processing triage"},
                    {"key": "Monthly", "value": "Safety Management Team (chair), regulatory affairs alignment, medical affairs sync"},
                    {"key": "Quarterly", "value": "Safety Review Committee (member), DSMB meetings, Board safety update"},
                    {"key": "Ad hoc", "value": "Regulatory authority queries, urgent safety measures, SUSAR review"},
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-i", "label": "GVP Module I Section I.4 — Qualified person responsible for pharmacovigilance"},
            {"id": "21cfr312-32", "label": "21 CFR 312.32 — IND safety reporting"},
            {"id": "ich-e2e", "label": "ICH E2E — Pharmacovigilance Planning"},
        ],
        "related_items": [
            {"type": "role", "id": "qppv", "label": "QPPV"},
            {"type": "role", "id": "signal-director", "label": "Director, Signal Management"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
        ],
    },
    ("role", "qppv"): {
        "title": "Qualified Person Responsible for Pharmacovigilance (QPPV)",
        "summary": (
            "EU legally mandated role per Directive 2001/83/EC Article 104. Must reside in EU, "
            "have regulatory independence, and maintain the Pharmacovigilance System Master File (PSMF)."
        ),
        "sections": [
            {
                "heading": "Legal Mandate",
                "content": [
                    "Directive 2001/83/EC Article 104: MAH must permanently and continuously have at their disposal an appropriately qualified person responsible for pharmacovigilance",
                    "Regulation 726/2004 Article 28a: QPPV personally responsible for the establishment and maintenance of the pharmacovigilance system",
                    "Personally accountable for ensuring ICSR collection, collation, and reporting within regulatory timelines",
                    "Must ensure signal detection is performed and all emerging safety concerns are reported to competent authorities and EMA",
                    "Liable under EU law for pharmacovigilance system failures; personal accountability cannot be delegated",
                ],
            },
            {
                "heading": "Independence",
                "content": [
                    "Dotted-line reporting to CMO; cannot be overruled on safety decisions by commercial or business interests",
                    "Must have direct access to the Board of Directors for urgent safety escalations",
                    "Organizational independence: safety recommendations cannot be suppressed or delayed for commercial reasons",
                    "Right to raise safety concerns directly with regulatory authorities if internal escalation fails",
                    "Protected from dismissal or penalty for exercising pharmacovigilance responsibilities in good faith",
                ],
            },
            {
                "heading": "PSMF Responsibility",
                "content": [
                    "GVP Module II: QPPV is responsible for creation, maintenance, and availability of the PSMF",
                    "PSMF must describe the pharmacovigilance system covering all authorized products",
                    "Structure: quality system, organizational structure, processes, databases, contractual arrangements, audit findings",
                    "Must be available for inspection by competent authorities within 7 calendar days of request",
                    "Maintained as a living document with version control; Annex I (list of products) updated within 30 days of changes",
                    "Must include documentation of data sources, signal detection methodology, and risk management processes",
                ],
            },
            {
                "heading": "Qualification Requirements",
                "content": [
                    "Medical, pharmacy, or life sciences degree (GVP Module I.3 — appropriately qualified)",
                    "Minimum 2 years of pharmacovigilance experience per GVP Module I.3 guidance",
                    "Thorough knowledge of EU pharmacovigilance legislation and GVP guidelines",
                    "Proficiency in English (EMA working language); knowledge of additional EU languages preferred",
                    "Must reside and operate in an EU/EEA Member State",
                ],
            },
            {
                "heading": "Backup Arrangements",
                "content": [
                    "Designated deputy QPPV with equivalent qualifications must be formally appointed",
                    "Documented delegation procedure specifying scope, triggers, and communication protocol",
                    "24/7 availability requirement: QPPV or deputy must be contactable at all times for urgent safety matters",
                    "Backup arrangements must be documented in the PSMF and available for inspection",
                    "Delegation does not transfer personal accountability — QPPV retains ultimate responsibility",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "dir-2001-83-art104", "label": "Directive 2001/83/EC Article 104 — QPPV requirements"},
            {"id": "reg-726-2004", "label": "Regulation 726/2004 Article 28a — Centralized procedure PV obligations"},
            {"id": "gvp-mod-i-3", "label": "GVP Module I Section I.3 — Qualified person qualifications"},
            {"id": "gvp-mod-ii", "label": "GVP Module II — Pharmacovigilance System Master File"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "role", "id": "pv-quality-manager", "label": "PV Quality Manager"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
        ],
    },
    ("role", "signal-director"): {
        "title": "Director, Signal Management",
        "summary": (
            "Leads signal detection, validation, and assessment per GVP Module IX. Responsible for "
            "disproportionality analyses, clinical case review, and signal dossier preparation."
        ),
        "sections": [
            {
                "heading": "Signal Detection Methods",
                "content": [
                    {"key": "PRR (Proportional Reporting Ratio)", "value": "PRR >= 2.0 AND N >= 3 AND chi-squared >= 4.0 (Evans criteria)"},
                    {"key": "ROR (Reporting Odds Ratio)", "value": "Lower bound of 95% CI > 1.0"},
                    {"key": "EBGM (Empirical Bayes Geometric Mean)", "value": "EB05 (lower 5th percentile) >= 2.0 (Multi-item Gamma Poisson Shrinker)"},
                    {"key": "BCPNN (Bayesian Confidence Propagation Neural Network)", "value": "IC025 (lower 2.5th percentile of IC) > 0 (WHO-UMC method)"},
                    {"key": "Temporal scan", "value": "TreeScan and MaxSPRT for temporal clustering of events post-exposure"},
                ],
            },
            {
                "heading": "Workflow Responsibilities",
                "content": [
                    "Monthly screening of FAERS, EudraVigilance, and VigiBase for statistical signals across all marketed products",
                    "Continuous monitoring of internal safety database (Oracle Argus) for emerging case clusters",
                    "Clinical validation review: medical assessment of statistical signals for clinical relevance and biological plausibility",
                    "Signal dossier preparation per GVP Module IX format: signal summary, evidence assessment, proposed action",
                    "Participation in PRAC signal procedure: response to PRAC signal assessments within 60-day timeline",
                    "Literature signal monitoring: systematic review of published case reports, epidemiological studies, and mechanistic data",
                    "Signal tracking: maintain signal tracking tool documenting status from detection through closure",
                ],
            },
            {
                "heading": "Decision Points",
                "content": [
                    {"key": "Potential → Validated signal", "value": "When clinical review confirms a new causal association or a change in character/frequency of a known association"},
                    {"key": "Label change recommendation", "value": "When validated signal meets criteria: consistent signal across data sources, biologically plausible, clinically significant"},
                    {"key": "PASS initiation", "value": "When additional data needed to characterize risk magnitude, risk factors, or effectiveness of risk minimization"},
                    {"key": "Signal closure", "value": "When evidence insufficient after full evaluation, or when appropriate action already taken"},
                ],
            },
            {
                "heading": "Tools and Systems",
                "content": [
                    "Oracle Empirica Signal: primary platform for disproportionality analysis and signal management workflow",
                    "Custom R scripts: supplementary Bayesian analyses, forest plots, time-to-onset distributions",
                    "Python analytics pipeline: automated data extraction, MedDRA coding validation, SMQ-based screening",
                    "MedDRA Browser: term selection, SMQ hierarchy navigation, version migration impact assessment",
                    "Signal tracking database: internal tool linking signals to regulatory actions and labeling outcomes",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-ix", "label": "GVP Module IX — Signal Management"},
            {"id": "gvp-mod-ix-rev1", "label": "GVP Module IX Addendum I — Signal management methodologies"},
            {"id": "ich-e2e", "label": "ICH E2E — Pharmacovigilance Planning"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "role", "id": "ta-head", "label": "TA Head, Oncology"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
        ],
    },
    ("role", "ta-head"): {
        "title": "Therapeutic Area Head, Oncology",
        "summary": (
            "Medical subject matter expert for NSCLC and EGFR biology. Provides mechanistic plausibility "
            "assessments for safety signals, drug class intelligence, and disease context for benefit-risk decisions."
        ),
        "sections": [
            {
                "heading": "Therapeutic Context",
                "content": [
                    "NSCLC epidemiology: ~2.2 million new lung cancer cases globally per year; NSCLC represents 85% of all lung cancers",
                    "EGFR mutation landscape: exon 19 deletion (45%), L858R point mutation (40%), exon 20 insertions (5-10%), other rare mutations",
                    "T790M resistance mutation: acquired in ~60% of patients progressing on first-generation EGFR TKIs",
                    "C797S tertiary resistance: emerging mechanism of resistance to third-generation EGFR TKIs; cis vs trans configuration determines treatment options",
                    "MET amplification as bypass resistance mechanism in 5-20% of EGFR TKI-resistant cases",
                    "Histological transformation (SCLC) in ~5-15% of resistant cases; requires biopsy at progression",
                ],
            },
            {
                "heading": "Drug Class Intelligence",
                "content": [
                    {"key": "First-generation EGFR TKIs", "value": "Erlotinib (Tarceva), gefitinib (Iressa) — reversible EGFR inhibitors; class effects: rash, diarrhea, ILD"},
                    {"key": "Second-generation", "value": "Afatinib (Gilotrif), dacomitinib (Vizimpro) — irreversible pan-HER inhibitors; enhanced GI and skin toxicity due to EGFR wild-type inhibition"},
                    {"key": "Third-generation", "value": "Osimertinib (Tagrisso) — mutant-selective, CNS-penetrant; QTc prolongation, ILD, cardiac toxicity as differentiating safety signals"},
                    {"key": "Class-effect AEs", "value": "Acneiform rash (EGFR in skin), diarrhea (EGFR in GI epithelium), ILD (rare but serious class effect, ~3-4%)"},
                    {"key": "Drug-specific AEs", "value": "Must distinguish class effects from drug-specific signals for accurate labeling and risk communication"},
                ],
            },
            {
                "heading": "Mechanistic Plausibility Role",
                "content": [
                    "Evaluates biological plausibility of new safety signals using target biology and known off-target effects",
                    "Assesses preclinical data (in vitro kinase panels, animal toxicology) for mechanistic support of clinical signals",
                    "Provides drug class context: differentiates class-effect AEs from drug-specific signals",
                    "Reviews published literature for mechanistic case reports and pharmacological rationale",
                    "Integrates pharmacokinetic/pharmacodynamic data (exposure-response for safety endpoints)",
                    "Advises on nonclinical study design to address mechanistic questions raised by clinical signals",
                ],
            },
            {
                "heading": "Key Decisions",
                "content": [
                    "Input to signal prioritization: assigns mechanistic plausibility score (high/medium/low/none) for each new signal",
                    "PBRER medical context: authors disease and treatment landscape sections for periodic benefit-risk evaluation",
                    "Investigator Brochure safety sections: ensures preclinical and clinical safety data are accurately integrated",
                    "Provides competitive intelligence on safety profiles of marketed comparators for benefit-risk contextualization",
                    "Advisory input on clinical trial eligibility criteria based on emerging safety data",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "ich-e2e", "label": "ICH E2E — Pharmacovigilance Planning"},
            {"id": "ich-e2c-r2", "label": "ICH E2C(R2) — Periodic Benefit-Risk Evaluation Report"},
            {"id": "gvp-mod-ix", "label": "GVP Module IX — Signal Management (plausibility assessment)"},
        ],
        "related_items": [
            {"type": "role", "id": "signal-director", "label": "Director, Signal Management"},
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
        ],
    },
    ("role", "pv-ops-director"): {
        "title": "Director, Pharmacovigilance Operations",
        "summary": (
            "Leads ICSR processing, regulatory reporting compliance, and CRO oversight. Ensures all individual "
            "case safety reports are processed and submitted within regulatory timelines per GVP Module VI and 21 CFR 314.80."
        ),
        "sections": [
            {
                "heading": "Case Processing Oversight",
                "content": [
                    "Manages end-to-end ICSR lifecycle: intake, data entry, medical review, coding, quality review, submission",
                    "Ensures expedited reports submitted within 15 calendar days (fatal/life-threatening) or 90 days (non-serious) per GVP Module VI",
                    "Monitors compliance KPIs: regulatory submission timeliness (target >= 98%), data accuracy, duplicate detection rate",
                    "Manages case backlog and surge capacity planning; escalates resource needs to Head of Patient Safety",
                    "Oversees MedDRA coding consistency and version migration across reporting periods",
                ],
            },
            {
                "heading": "CRO and Vendor Management",
                "content": [
                    "Primary oversight of outsourced case processing vendors (CROs) per GVP Module I.6",
                    "Conducts quarterly business reviews with KPI scorecards: timeliness, quality, volume accuracy",
                    "Manages Safety Data Exchange Agreements (SDEAs) and Pharmacovigilance Agreements (PVAs) with partners",
                    "Performs or coordinates vendor audits in collaboration with PV Quality Manager",
                    "Ensures vendor staff training on product-specific safety profiles and processing conventions",
                ],
            },
            {
                "heading": "Systems and Database Management",
                "content": [
                    "Oracle Argus Safety database owner: configuration, validation, user access, data integrity",
                    "Manages E2B(R3) gateway submissions to EudraVigilance and FDA FAERS",
                    "Oversees system upgrades, MedDRA dictionary updates, and regulatory configuration changes",
                    "Ensures database lock procedures for periodic reporting and signal detection activities",
                ],
            },
            {
                "heading": "Regulatory Reporting Compliance",
                "content": [
                    {"key": "EU expedited (EudraVigilance)", "value": "15 days fatal/life-threatening, 90 days non-serious; E2B(R3) format"},
                    {"key": "US expedited (FAERS)", "value": "15 days serious/unexpected per 21 CFR 314.80; MedWatch 3500A or E2B"},
                    {"key": "Clinical trial SUSARs", "value": "7 days fatal/life-threatening, 15 days all other serious unexpected per ICH E2A"},
                    {"key": "Compliance target", "value": ">= 98% on-time submission rate across all regulatory authorities"},
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-vi", "label": "GVP Module VI — Collection, Management, and Submission of ICSRs"},
            {"id": "21cfr314-80", "label": "21 CFR 314.80 — Postmarketing reporting of adverse drug experiences"},
            {"id": "ich-e2a", "label": "ICH E2A — Clinical Safety Data Management"},
            {"id": "gvp-mod-i-6", "label": "GVP Module I Section I.6 — Outsourced pharmacovigilance activities"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "role", "id": "pv-quality-manager", "label": "PV Quality Manager"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
        ],
    },
    ("role", "risk-director"): {
        "title": "Director, Risk Management",
        "summary": (
            "Leads development and maintenance of EU Risk Management Plans (RMPs) and US REMS programs. "
            "Evaluates effectiveness of risk minimization measures per GVP Module V and GVP Module XVI."
        ),
        "sections": [
            {
                "heading": "Risk Management Plan (RMP)",
                "content": [
                    "Authors and maintains EU RMP per GVP Module V: safety specification, pharmacovigilance plan, risk minimization measures",
                    "Safety specification: identifies important identified risks, important potential risks, and missing information",
                    "Coordinates RMP updates triggered by new safety data, post-authorization commitments, or regulatory requests",
                    "Ensures RMP submissions aligned with MAA lifecycle: initial, variations, renewals, PSUSA outcomes",
                    "Manages RMP milestones and regulatory commitments tracking",
                ],
            },
            {
                "heading": "Risk Minimization and REMS",
                "content": [
                    "Designs and implements additional risk minimization measures (aRMMs): educational materials, DHPC, controlled access programs",
                    "US REMS: develops and maintains REMS programs including ETASU, medication guides, communication plans per 21 CFR 314.520",
                    "Evaluates effectiveness of risk minimization using GVP Module XVI criteria: process indicators, outcome indicators, surveys",
                    "Coordinates with commercial and medical affairs on risk communication materials",
                ],
            },
            {
                "heading": "Post-Authorization Safety Studies (PASS)",
                "content": [
                    "Designs and oversees PASS studies per GVP Module VIII: imposed and voluntary study protocols",
                    "Manages PASS registration in EU PAS Register and ensures protocol compliance",
                    "Coordinates with epidemiology team on study design, data sources (claims databases, registries), and analysis plans",
                    "Ensures PASS results integrated into RMP updates and periodic safety reports",
                ],
            },
            {
                "heading": "Emerging Risk Assessment",
                "content": [
                    {"key": "Risk categorization", "value": "Important identified, important potential, missing information — per GVP Module V Part II"},
                    {"key": "Risk scoring", "value": "Severity x frequency x detectability matrix for prioritization"},
                    {"key": "Risk communication triggers", "value": "New important identified risk, change in risk characterization, effectiveness measure failure"},
                    {"key": "Pediatric risk assessment", "value": "Age-specific risk evaluation per Pediatric Regulation (EC) 1901/2006"},
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-v", "label": "GVP Module V — Risk Management Systems"},
            {"id": "gvp-mod-xvi", "label": "GVP Module XVI — Risk Minimisation Measures: Selection and Effectiveness"},
            {"id": "gvp-mod-viii", "label": "GVP Module VIII — Post-Authorisation Safety Studies"},
            {"id": "21cfr314-520", "label": "21 CFR 314.520 — REMS requirements"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "committee", "id": "rmc", "label": "Risk Management Committee"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
        ],
    },
    ("role", "agg-reporting-director"): {
        "title": "Director, Aggregate Reporting",
        "summary": (
            "Leads preparation and submission of periodic aggregate safety reports including PSURs/PBRERs (ICH E2C(R2)), "
            "DSURs (ICH E2F), and PADERs. Manages PSUSA procedure timelines and regulatory commitments."
        ),
        "sections": [
            {
                "heading": "Periodic Report Portfolio",
                "content": [
                    {"key": "PBRER/PSUR", "value": "Per ICH E2C(R2) — periodic benefit-risk evaluation for marketed products; EURD list-driven submission schedule"},
                    {"key": "DSUR", "value": "Per ICH E2F — annual development safety update report for investigational products in clinical trials"},
                    {"key": "PADER", "value": "Post-Authorization Data Exclusivity report — aggregate safety data during data exclusivity period"},
                    {"key": "IND Annual Report", "value": "Per 21 CFR 312.33 — annual summary of clinical and safety data for FDA"},
                ],
            },
            {
                "heading": "PBRER Authoring Process",
                "content": [
                    "Data lock point management: coordinate database lock with PV Operations 60 days before EURD list deadline",
                    "Line listing generation and reconciliation against regulatory submissions",
                    "Signal and risk evaluation sections: integrate signal management outputs and RMP updates",
                    "Benefit-risk analysis: structured framework per ICH E2C(R2) Section 4 — benefit, risk, and benefit-risk context",
                    "Internal review cycle: medical review → Head of PS → QPPV sign-off → regulatory submission",
                    "Post-PSUSA procedure: implement PRAC assessment outcomes and CMDh/CHMP positions",
                ],
            },
            {
                "heading": "Regulatory Timelines",
                "content": [
                    "Maintains master timeline tracker for all periodic reports across global portfolio",
                    "EURD list synchronization: monitors EU reference date list updates for submission schedule changes",
                    "Coordinates with regulatory affairs for submission logistics: eCTD format, cover letters, response to questions",
                    "Tracks post-submission regulatory questions and coordinates cross-functional response teams",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "ich-e2c-r2", "label": "ICH E2C(R2) — Periodic Benefit-Risk Evaluation Report"},
            {"id": "ich-e2f", "label": "ICH E2F — Development Safety Update Report"},
            {"id": "gvp-mod-vii", "label": "GVP Module VII — Periodic Safety Update Report"},
            {"id": "21cfr312-33", "label": "21 CFR 312.33 — IND Annual Reports"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "role", "id": "qppv", "label": "QPPV"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
        ],
    },
    ("role", "pv-quality-manager"): {
        "title": "PV Quality Manager",
        "summary": (
            "Ensures pharmacovigilance quality system compliance per GVP Module I and ICH Q10. Manages SOPs, "
            "training, audits, CAPA tracking, and inspection readiness for the pharmacovigilance system."
        ),
        "sections": [
            {
                "heading": "Quality System Management",
                "content": [
                    "Maintains PV quality system aligned with GVP Module I.5 and ICH Q10 principles",
                    "Manages PV SOP library: authoring, review cycle (biennial), version control, training attestation tracking",
                    "Oversees document management system for PV procedures, work instructions, and templates",
                    "Ensures PV quality metrics reported to SMT: CAPA status, deviation trends, training compliance rates",
                ],
            },
            {
                "heading": "Audit and Inspection Readiness",
                "content": [
                    "Develops annual PV audit plan covering internal processes, CRO vendors, and PSMF adequacy",
                    "Conducts internal PV audits per risk-based schedule; manages findings through CAPA process",
                    "Maintains inspection readiness: PSMF current, SOPs up to date, training records complete, quality metrics available",
                    "Coordinates responses to regulatory inspections (EMA, FDA, national competent authorities)",
                    "Tracks inspection findings and commitments to resolution with defined timelines",
                ],
            },
            {
                "heading": "CAPA Management",
                "content": [
                    "Manages CAPA system for PV deviations: root cause analysis, corrective actions, effectiveness checks",
                    "Categorizes deviations by severity (critical, major, minor) and tracks resolution timelines",
                    "Ensures CAPAs address systemic issues, not just symptoms; trend analysis of recurring deviations",
                    "Reports CAPA status and quality trends to SMT monthly and SRC quarterly",
                ],
            },
            {
                "heading": "Training and Compliance",
                "content": [
                    "Manages PV training curriculum: role-based training matrix, new hire onboarding, annual refresher training",
                    "Ensures all PV personnel (internal and CRO) trained on applicable SOPs before performing PV tasks",
                    "Tracks training compliance rates per GVP Module I.5 requirements (target >= 95%)",
                    "Coordinates product-specific safety training for new approvals or significant label changes",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-i-5", "label": "GVP Module I Section I.5 — Quality system for pharmacovigilance"},
            {"id": "gvp-mod-ii", "label": "GVP Module II — PSMF quality requirements"},
            {"id": "gvp-mod-iii", "label": "GVP Module III — Pharmacovigilance inspections"},
            {"id": "ich-q10", "label": "ICH Q10 — Pharmaceutical Quality System"},
        ],
        "related_items": [
            {"type": "role", "id": "qppv", "label": "QPPV"},
            {"type": "role", "id": "pv-ops-director", "label": "Director, PV Operations"},
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
        ],
    },
    # -----------------------------------------------------------------------
    # COMMITTEES
    # -----------------------------------------------------------------------
    ("committee", "smt"): {
        "title": "Safety Management Team (SMT)",
        "summary": (
            "Monthly cross-functional review of aggregate safety data, active signals, case processing metrics, "
            "and operational KPIs. Chaired by Head of Patient Safety."
        ),
        "sections": [
            {
                "heading": "Standing Agenda",
                "content": [
                    "1. Signal portfolio review — new, ongoing, and closed signals across all products",
                    "2. Case volume and compliance metrics — submission timeliness, backlog, duplicate rates",
                    "3. Aggregate report status — PBRER/DSUR milestones, upcoming data lock points",
                    "4. CAPA update — open deviations, overdue actions, effectiveness check results",
                    "5. Vendor performance — CRO scorecard review, escalation items",
                    "6. Literature monitoring findings — new safety-relevant publications and case reports",
                    "7. Regulatory intelligence — new guidances, PRAC outcomes, FDA safety communications affecting portfolio",
                    "8. Action item review — status of prior meeting actions, new assignments",
                ],
            },
            {
                "heading": "Membership",
                "content": [
                    "Head of Patient Safety (Chair)",
                    "QPPV",
                    "Director, Signal Management",
                    "Director, PV Operations",
                    "Director, Risk Management",
                    "Director, Aggregate Reporting",
                    "PV Quality Manager",
                    "Therapeutic Area Head, Oncology",
                ],
            },
            {
                "heading": "Quorum and Governance",
                "content": [
                    "Quorum: minimum 5 of 8 members present, including Chair (Head of PS) and QPPV",
                    "Decisions by consensus; disagreements escalated to SRC",
                    "Meetings held monthly on fixed schedule; additional ad-hoc meetings as needed",
                    "Designated note-taker (rotating); minutes distributed within 5 business days",
                ],
            },
            {
                "heading": "Escalation Criteria",
                "content": [
                    "Ad-hoc meeting triggers requiring immediate convening of SMT:",
                    "New validated signal with urgent safety concern (potential for regulatory action)",
                    "Regulatory authority query requiring cross-functional response within short timeline",
                    "SUSAR cluster: >= 3 SUSARs of same event type within 30-day window",
                    "Hy's Law case: ALT >= 3x ULN + bilirubin >= 2x ULN without alternative cause",
                    "Case processing compliance dropping below 90% submission timeliness",
                ],
            },
            {
                "heading": "Decision Matrix",
                "content": [
                    {"key": "Routine signal update (no new action needed)", "value": "Note in minutes; continue monitoring per existing plan"},
                    {"key": "New validated signal", "value": "Escalate to SRC for benefit-risk review and action decision"},
                    {"key": "Urgent safety measure", "value": "Immediate notification to CMO; initiate regulatory procedure per Article 22"},
                    {"key": "Label change recommendation", "value": "Prepare signal dossier; SRC vote required before regulatory submission"},
                    {"key": "CAPA overdue > 30 days", "value": "Escalate to responsible director with remediation deadline"},
                ],
            },
            {
                "heading": "Minutes Requirements",
                "content": [
                    "Minutes distributed to all members within 5 business days of meeting",
                    "Action items tracked with responsible person, due date, and status",
                    "Minutes maintained in PSMF as evidence of pharmacovigilance system governance",
                    "Quarterly summary of SMT decisions and actions included in SRC report",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-i", "label": "GVP Module I — Pharmacovigilance systems and quality systems"},
            {"id": "gvp-mod-ii", "label": "GVP Module II — PSMF governance documentation"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety (Chair)"},
            {"type": "role", "id": "qppv", "label": "QPPV"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
        ],
    },
    ("committee", "src"): {
        "title": "Safety Review Committee (SRC)",
        "summary": (
            "Quarterly executive-level benefit-risk review chaired by CMO. Makes decisions on labeling changes, "
            "risk communications, clinical trial modifications, and escalation to Board of Directors."
        ),
        "sections": [
            {
                "heading": "Standing Agenda",
                "content": [
                    "1. SMT quarterly summary — signals, escalations, and recommendations",
                    "2. Benefit-risk assessment updates — per-product structured B-R framework review",
                    "3. Labeling decisions — proposed SmPC/USPI changes, DHPC review and approval",
                    "4. RMP and REMS status — risk minimization effectiveness, new commitments",
                    "5. Clinical trial safety — DSMB recommendations, SUSAR trends, protocol amendment proposals",
                    "6. Regulatory interactions — PRAC outcomes, FDA safety reviews, inspection findings",
                    "7. Strategic safety matters — competitive landscape safety intelligence, pipeline risk assessment",
                ],
            },
            {
                "heading": "Membership",
                "content": [
                    "Chief Medical Officer (Chair)",
                    "Head of Patient Safety (Vice-Chair)",
                    "QPPV",
                    "VP Regulatory Affairs",
                    "VP Clinical Development",
                    "General Counsel (or designee)",
                    "VP Medical Affairs",
                    "Head of Biostatistics (as needed)",
                ],
            },
            {
                "heading": "Decision Authority",
                "content": [
                    {"key": "Label change approval", "value": "SRC vote required; majority with Chair concurrence; QPPV has veto on safety grounds"},
                    {"key": "DHPC issuance", "value": "SRC approval required; legal and regulatory review must be completed prior to vote"},
                    {"key": "Clinical trial modification", "value": "Protocol amendments for safety: SRC approval required before IRB/EC submission"},
                    {"key": "Board escalation", "value": "Any safety issue with potential material impact on patients, regulatory status, or company reputation"},
                    {"key": "Urgent safety measure", "value": "CMO may act unilaterally with retrospective SRC ratification within 72 hours"},
                ],
            },
            {
                "heading": "Quorum and Voting",
                "content": [
                    "Quorum: minimum 5 of 8 members including Chair (CMO) and either QPPV or Head of PS",
                    "Decisions by majority vote; Chair has casting vote in case of tie",
                    "QPPV retains independent veto authority on any decision that may compromise patient safety",
                    "Voting members must declare conflicts of interest at start of each meeting",
                ],
            },
            {
                "heading": "Documentation and Follow-up",
                "content": [
                    "Formal minutes with documented decisions, rationale, and dissenting opinions",
                    "Action items assigned with accountable owner and deadline",
                    "Minutes reviewed and approved at subsequent meeting",
                    "SRC decisions archived in PSMF and available for regulatory inspection",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-i", "label": "GVP Module I — Pharmacovigilance governance"},
            {"id": "ich-e2c-r2", "label": "ICH E2C(R2) — Benefit-risk evaluation framework"},
            {"id": "gvp-mod-v", "label": "GVP Module V — Risk management decision-making"},
        ],
        "related_items": [
            {"type": "committee", "id": "smt", "label": "Safety Management Team"},
            {"type": "committee", "id": "dsmb", "label": "DSMB"},
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "role", "id": "qppv", "label": "QPPV"},
        ],
    },
    ("committee", "rmc"): {
        "title": "Risk Management Committee (RMC)",
        "summary": (
            "Quarterly review of EU Risk Management Plan and REMS effectiveness. Evaluates emerging risks, "
            "assesses risk minimization measure performance, and recommends updates to risk management strategy."
        ),
        "sections": [
            {
                "heading": "Standing Agenda",
                "content": [
                    "1. RMP status review — current version, pending variations, regulatory commitments tracker",
                    "2. Risk minimization measure effectiveness — process and outcome indicator review per GVP Module XVI",
                    "3. REMS assessment — ETASU compliance rates, medication guide distribution metrics",
                    "4. Emerging risk assessment — new important identified/potential risks for safety specification update",
                    "5. PASS study updates — enrollment, interim results, protocol deviations",
                    "6. Missing information evaluation — data gaps and strategies for characterization",
                    "7. Action items and next steps",
                ],
            },
            {
                "heading": "Membership",
                "content": [
                    "Director, Risk Management (Chair)",
                    "Head of Patient Safety",
                    "Director, Signal Management",
                    "Epidemiology Lead",
                    "Regulatory Affairs representative",
                    "Medical Affairs representative",
                    "Commercial representative (for aRMM implementation feasibility)",
                ],
            },
            {
                "heading": "Effectiveness Evaluation Framework",
                "content": [
                    {"key": "Process indicators", "value": "Distribution metrics, HCP acknowledgment rates, training completion rates"},
                    {"key": "Outcome indicators", "value": "Incidence rate changes for targeted risks, drug utilization patterns, off-label use monitoring"},
                    {"key": "Survey-based assessment", "value": "HCP knowledge and behavior surveys per GVP Module XVI methodology"},
                    {"key": "Evaluation cycle", "value": "Per RMP milestones; typically at 18 months post-approval, then every 3 years"},
                ],
            },
            {
                "heading": "Escalation to SRC",
                "content": [
                    "New important identified risk requiring safety specification update",
                    "Risk minimization measure demonstrated ineffective by outcome indicators",
                    "REMS modification required (FDA) or additional aRMM needed (EU)",
                    "PASS results requiring RMP or labeling update",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "gvp-mod-v", "label": "GVP Module V — Risk Management Systems"},
            {"id": "gvp-mod-xvi", "label": "GVP Module XVI — Risk Minimisation Measures effectiveness evaluation"},
            {"id": "gvp-mod-viii", "label": "GVP Module VIII — Post-Authorisation Safety Studies"},
            {"id": "21cfr314-520", "label": "21 CFR 314.520 — REMS requirements"},
        ],
        "related_items": [
            {"type": "role", "id": "risk-director", "label": "Director, Risk Management (Chair)"},
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
        ],
    },
    ("committee", "dsmb"): {
        "title": "Data Safety Monitoring Board (DSMB)",
        "summary": (
            "Independent external committee providing unblinded safety oversight for the PROSPER clinical trial "
            "program per FDA Guidance on DMCs (2006) and ICH E9. Ensures participant safety through interim "
            "analysis review and authority to recommend trial modification or termination."
        ),
        "sections": [
            {
                "heading": "Composition",
                "content": [
                    "3 independent members, all free from significant conflicts of interest with sponsor per FDA DMC Guidance",
                    "Clinical domain expert: oncologist with NSCLC/EGFR TKI expertise, not an investigator on the trial",
                    "Biostatistician: independent of sponsor's statistical team, experienced in interim analysis methodology",
                    "Ethicist/patient advocate: expertise in clinical trial ethics and risk communication to participants",
                    "All members must sign conflict of interest declarations and confidentiality agreements annually",
                    "Independent statistical analysis center (ISAC) prepares unblinded reports; separate from sponsor's CRO",
                ],
            },
            {
                "heading": "Charter Requirements",
                "content": [
                    "DSMB charter established before first patient enrolled; signed by all members and sponsor",
                    "Stopping rules defined using O'Brien-Fleming alpha-spending function (Lan-DeMets implementation)",
                    "Three meeting types specified: Open, Closed, and Executive sessions",
                    "Quorum rules: all 3 members must be present for Closed and Executive sessions",
                    "Communication procedures: DSMB communicates only with sponsor via written recommendation letters",
                    "Charter specifies procedures for urgent unblinded safety review between scheduled meetings",
                    "Annual charter review and amendment process documented",
                ],
            },
            {
                "heading": "Meeting Types",
                "content": [
                    {"key": "Open session", "value": "Sponsor representatives present; only blinded (aggregate) data reviewed; operational updates, protocol amendments, enrollment status"},
                    {"key": "Closed session", "value": "DSMB members + independent statistician only; unblinded data by treatment arm reviewed; safety and efficacy interim analyses presented"},
                    {"key": "Executive session", "value": "DSMB members only (no statistician); deliberation on findings and formulation of recommendation; documented in confidential minutes"},
                ],
            },
            {
                "heading": "Unblinding Procedures",
                "content": [
                    "Independent statistician at ISAC prepares all unblinded reports; sponsor biostatisticians see only blinded data",
                    "Unblinded reports transmitted via secure encrypted channel directly to DSMB members before Closed session",
                    "Sponsor receives only the DSMB's recommendation letter — never raw unblinded data or treatment-arm-specific results",
                    "If DSMB recommends trial termination, formal unblinding procedure per charter with regulatory notification",
                    "All unblinded materials retained by ISAC under access controls; destroyed per retention schedule after trial completion",
                ],
            },
            {
                "heading": "Stopping Rules",
                "content": [
                    "Efficacy stopping: O'Brien-Fleming boundaries with Lan-DeMets alpha-spending function preserving overall alpha = 0.05",
                    "Futility stopping: conditional power < 10% at interim analysis (non-binding futility boundary)",
                    "Safety stopping criteria: pre-specified excess SAE thresholds by treatment arm (e.g., >= 2-fold excess Grade 4+ toxicity)",
                    "Specific stopping triggers for ILD (>= 5% incidence with >= 2 fatal cases) and hepatotoxicity (>= 3 Hy's Law cases)",
                    "DSMB recommendations are advisory; sponsor retains final decision authority but must document rationale if not following recommendation",
                    "All stopping boundary crossings documented in DSMB minutes and communicated to regulatory authorities per ICH E9(R1)",
                ],
            },
        ],
        "regulatory_references": [
            {"id": "fda-dmc-2006", "label": "FDA Guidance for Clinical Trial Sponsors: Establishment and Operation of Clinical Trial Data Monitoring Committees (2006)"},
            {"id": "ich-e9-r1", "label": "ICH E9(R1) — Statistical Principles for Clinical Trials, Addendum on Estimands"},
            {"id": "21cfr50-25", "label": "21 CFR 50.25(a)(5) — Informed consent elements regarding DMC oversight"},
            {"id": "ich-e6-r2", "label": "ICH E6(R2) — Good Clinical Practice, Section 5.5.2 (DMC requirements)"},
        ],
        "related_items": [
            {"type": "role", "id": "head-ps", "label": "Head of Patient Safety (Sponsor Liaison)"},
            {"type": "committee", "id": "src", "label": "Safety Review Committee"},
            {"type": "role", "id": "ta-head", "label": "TA Head, Oncology"},
        ],
    },


    # -----------------------------------------------------------------------
    # REGULATIONS, REPORTS, KPIs, MARKETS, SOPs
    # -----------------------------------------------------------------------
# ---- Paste these entries into _DETAIL_DATA dict ----

    # ── REGULATIONS ──────────────────────────────────────────────────────
    ("regulation", "21-cfr-312-32"): {
        "title": "21 CFR 312.32 — IND Safety Reports",
        "summary": (
            "FDA requirements for IND safety reporting. Fatal or life-threatening "
            "unexpected suspected adverse reactions must be reported within 7 calendar "
            "days; all other serious unexpected reactions within 15 calendar days."
        ),
        "sections": [
            {
                "heading": "Reporting Timelines",
                "detail_type": "key_value_pairs",
                "content": {
                    "7-day telephone/fax report": "Fatal or life-threatening unexpected suspected adverse reactions",
                    "8-day follow-up (written)": "Follow-up to 7-day telephone/fax report with complete IND Safety Report",
                    "15-day written report": "All other serious AND unexpected suspected adverse reactions",
                    "Annual IND safety report": "Due within 60 days of the IND anniversary date",
                },
            },
            {
                "heading": "Definitions",
                "detail_type": "text",
                "content": (
                    "Unexpected: An adverse event is unexpected if it is not listed in nature, "
                    "severity, or frequency in the current Investigator's Brochure (IB). "
                    "Serious: An adverse event that results in death, is life-threatening, "
                    "requires inpatient hospitalization or prolongation of existing hospitalization, "
                    "results in persistent or significant disability/incapacity, is a congenital "
                    "anomaly/birth defect, or is a medically important event. Causality assessment "
                    "is required: the sponsor must assess whether there is a reasonable possibility "
                    "that the drug caused the event."
                ),
            },
            {
                "heading": "Process",
                "detail_type": "text",
                "content": [
                    "Sponsor identifies adverse event from any source (clinical trial, spontaneous, literature)",
                    "Assess seriousness, expectedness, and causality",
                    "Unblind treatment assignment if necessary for safety evaluation",
                    "Prepare IND Safety Report (Form FDA 3500A or narrative)",
                    "File with FDA within required timeframe (7-day or 15-day)",
                    "Notify all participating investigators and reviewing IRBs promptly",
                    "Submit follow-up information as it becomes available",
                ],
            },
            {
                "heading": "Aggregate Analysis Requirements",
                "detail_type": "text",
                "content": (
                    "The annual IND safety report must include: line listings of all serious "
                    "adverse events (SAEs) from all studies conducted under the IND; a summary "
                    "of all IND safety reports submitted during the reporting period; a narrative "
                    "or tabular summary of significant new safety information; identification of "
                    "any new safety signals or changes in the character, severity, or frequency "
                    "of known risks; updated Investigator's Brochure reflecting new safety data."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 312.32 — IND Safety Reporting",
            "21 CFR 312.33 — Annual Reports",
            "ICH E2A — Clinical Safety Data Management: Definitions and Standards for Expedited Reporting",
            "FDA Guidance: Safety Reporting Requirements for INDs and BA/BE Studies (2012)",
        ],
        "related_items": [
            "regulation/21-cfr-314-80",
            "report/dsur",
            "committee/dsmb",
        ],
    },
    ("regulation", "21-cfr-314-80"): {
        "title": "21 CFR 314.80 — Post-Marketing Reporting of Adverse Drug Experiences",
        "summary": (
            "FDA requirements for post-marketing safety reporting by NDA/ANDA holders. "
            "15-day alert reports are required for adverse experiences that are both serious "
            "AND unexpected. Periodic reports are submitted quarterly for the first 3 years "
            "after approval, then annually."
        ),
        "sections": [
            {
                "heading": "Reporting Timelines",
                "detail_type": "key_value_pairs",
                "content": {
                    "15-day alert reports": "Serious AND unexpected adverse drug experiences — submitted to FDA within 15 calendar days of initial receipt",
                    "15-day alert (increased frequency)": "Reports that indicate the frequency of a serious expected ADE has increased above the rate stated in labeling",
                    "Periodic reports (Years 1–3)": "Quarterly, due 30 days after close of each quarter following approval date",
                    "Periodic reports (Year 4+)": "Annual, due 60 days after anniversary of approval date",
                },
            },
            {
                "heading": "FAERS and MedWatch",
                "detail_type": "text",
                "content": (
                    "Reports are submitted to the FDA Adverse Event Reporting System (FAERS) using "
                    "MedWatch Form FDA 3500A for mandatory (manufacturer) reports. Healthcare "
                    "professionals and consumers use Form FDA 3500 for voluntary reports. Electronic "
                    "submission is required via the FDA Electronic Submissions Gateway using the "
                    "ICH E2B(R3) format. FAERS data is publicly searchable and used by FDA for "
                    "signal detection and safety surveillance."
                ),
            },
            {
                "heading": "PADER Requirements",
                "detail_type": "text",
                "content": (
                    "Periodic Adverse Drug Experience Reports (PADERs) must contain: a narrative "
                    "summary and analysis of the information in the report and an analysis of the "
                    "15-day alert reports submitted during the reporting interval; a MedWatch 3500A "
                    "form for each adverse experience not reported as a 15-day alert; a history of "
                    "actions taken since the last report because of adverse drug experiences (e.g., "
                    "labeling changes, studies initiated); an index with patient identification, "
                    "adverse reaction term, and outcome."
                ),
            },
            {
                "heading": "Comparison with PBRER",
                "detail_type": "text",
                "content": (
                    "FDA announced in the Federal Register (2014) that it would accept a PBRER "
                    "(ICH E2C(R2)) in lieu of the PADER for NDAs, but the regulation at 314.80 "
                    "remains in effect. Sponsors of ANDAs generally submit PADERs. The PBRER "
                    "provides a more comprehensive benefit-risk evaluation framework compared to "
                    "the primarily listing-focused PADER."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 314.80 — Postmarketing Reporting of Adverse Drug Experiences",
            "21 CFR 314.81(b)(2)(i) — PADER",
            "FDA Guidance: Postmarketing Safety Reporting for Human Drug and Biological Products (2001)",
            "MedWatch Form FDA 3500A",
        ],
        "related_items": [
            "regulation/21-cfr-312-32",
            "report/pader",
            "report/pbrer",
            "market/us",
        ],
    },
    ("regulation", "gvp-module-vi"): {
        "title": "GVP Module VI — Collection, Management, and Submission of ICSRs",
        "summary": (
            "EU Good Pharmacovigilance Practices for Individual Case Safety Report (ICSR) "
            "management. Defines the four minimum validity criteria, Day 0 rules, coding "
            "standards, E2B(R3) transmission format, and submission timelines for "
            "EudraVigilance."
        ),
        "sections": [
            {
                "heading": "Case Validity — Four Minimum Criteria",
                "detail_type": "text",
                "content": [
                    "An identifiable reporter (name, initials, address, or qualification)",
                    "An identifiable patient (name, initials, age, sex, date of birth, or other identifier)",
                    "At least one suspected adverse reaction",
                    "At least one suspect medicinal product",
                ],
            },
            {
                "heading": "Day 0 and Clock Start Rules",
                "detail_type": "key_value_pairs",
                "content": {
                    "Day 0": "Date of first awareness — the date the MAH first receives the minimum information constituting a valid ICSR",
                    "Clock start for solicited reports": "Day the valid case is received from the study site or CRO",
                    "Clock start for literature": "Date the MAH becomes aware of the publication (not the publication date itself)",
                    "Clock start for regulatory authority reports": "Date the report is received by the MAH from the authority",
                },
            },
            {
                "heading": "Submission Timelines",
                "detail_type": "key_value_pairs",
                "content": {
                    "Serious EEA cases": "15 calendar days from Day 0 to EudraVigilance",
                    "Serious non-EEA cases": "15 calendar days from Day 0 to EudraVigilance",
                    "Non-serious EEA cases": "90 calendar days from Day 0 to EudraVigilance",
                    "Non-serious non-EEA cases": "Not required to submit to EudraVigilance (maintain in safety database)",
                },
            },
            {
                "heading": "E2B(R3) Format and EudraVigilance",
                "detail_type": "text",
                "content": (
                    "All ICSRs must be transmitted in ICH E2B(R3) format (HL7/XML-based Individual "
                    "Case Safety Report). EudraVigilance is the EU system for managing and analysing "
                    "ICSRs. MAHs must register for EudraVigilance access and maintain a current "
                    "EudraVigilance profile (EVWEB or gateway). Acknowledgements (ACK) must be "
                    "monitored; rejected transmissions require correction and re-submission. MedDRA "
                    "is the mandatory coding dictionary for adverse reactions."
                ),
            },
            {
                "heading": "Follow-up Obligations",
                "detail_type": "text",
                "content": (
                    "MAHs must actively seek follow-up information for all serious cases and for "
                    "non-serious cases when clinically relevant information is missing. Follow-up "
                    "attempts must be documented. Significant new information (e.g., new adverse "
                    "reaction, change in seriousness or outcome, additional causality data) triggers "
                    "a new 15-day or 90-day clock for the follow-up submission. At minimum 3 "
                    "follow-up attempts should be made for serious cases."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module VI Rev 2 — Management and Reporting of Adverse Reactions to Medicinal Products",
            "ICH E2B(R3) — Electronic Transmission of ICSRs",
            "EudraVigilance Access Policy",
            "Regulation (EU) No 1235/2010",
            "Directive 2001/83/EC Article 107",
        ],
        "related_items": [
            "regulation/gvp-module-ix",
            "kpi/case-processing-time",
            "kpi/serious-15-day",
            "market/eu",
        ],
    },
    ("regulation", "gvp-module-ix"): {
        "title": "GVP Module IX — Signal Management",
        "summary": (
            "EU Good Pharmacovigilance Practices for signal management. Defines the 6-stage "
            "signal process from detection through tracking, using disproportionality "
            "analysis methods (PRR, ROR, EBGM) and a structured prioritization matrix."
        ),
        "sections": [
            {
                "heading": "Six-Stage Signal Management Process",
                "detail_type": "text",
                "content": [
                    "Stage 1 — Signal Detection: Systematic review of data sources including EudraVigilance, clinical trials, literature, and other sources using statistical and clinical methods",
                    "Stage 2 — Signal Validation: Verify signal is a true signal (not noise/artifact), assess clinical relevance, confirm it represents new information or a change in known information",
                    "Stage 3 — Signal Prioritization: Rank validated signals by impact using a prioritization matrix considering severity, frequency, public health impact, novelty, and reversibility",
                    "Stage 4 — Signal Assessment: In-depth evaluation including comprehensive review of all available data, benefit-risk analysis, and determination of whether a causal relationship exists",
                    "Stage 5 — Recommendation for Action: Propose regulatory actions (labeling update, DHPC, RMP update, restriction, withdrawal) proportionate to the risk",
                    "Stage 6 — Tracking and Outcome: Monitor implementation and effectiveness of actions, close or escalate as appropriate, document rationale and outcomes",
                ],
            },
            {
                "heading": "Detection Methods and Thresholds",
                "detail_type": "key_value_pairs",
                "content": {
                    "PRR (Proportional Reporting Ratio)": "Signal threshold: PRR ≥ 2, chi-squared ≥ 4, N ≥ 3 cases",
                    "ROR (Reporting Odds Ratio)": "Signal threshold: lower bound of 95% CI of ROR > 1",
                    "EBGM (Empirical Bayes Geometric Mean)": "Signal threshold: EB05 (lower bound of 90% CI) ≥ 2",
                    "IC (Information Component, WHO)": "Signal threshold: IC025 (lower bound of 95% CI) > 0",
                    "Clinical review": "Cases with unexpected severity, novel mechanism, or regulatory concern regardless of statistical thresholds",
                },
            },
            {
                "heading": "Prioritization Matrix",
                "detail_type": "table",
                "content": {
                    "columns": ["Factor", "High Priority", "Medium Priority", "Low Priority"],
                    "rows": [
                        ["Severity", "Fatal/life-threatening", "Serious (hospitalization)", "Non-serious/reversible"],
                        ["Frequency", "Common (≥1/100)", "Uncommon (1/1000–1/100)", "Rare (<1/1000)"],
                        ["Public health impact", "Widespread use, vulnerable population", "Moderate use", "Limited use/niche indication"],
                        ["Preventability", "Not preventable", "Partially preventable", "Fully preventable with existing measures"],
                        ["Novelty", "Unknown risk, novel mechanism", "Known class effect, new for product", "Variation of known risk"],
                    ],
                },
            },
            {
                "heading": "PRAC Signal Procedure",
                "detail_type": "text",
                "content": (
                    "EMA screens EudraVigilance monthly using statistical methods to identify potential "
                    "signals for centrally authorised products (CAPs). Validated signals are published "
                    "in the PRAC recommendations on signals. MAHs are requested to submit a detailed "
                    "assessment within specified timelines (typically 60 days). PRAC evaluates the MAH "
                    "assessment and issues a recommendation: routine pharmacovigilance, additional "
                    "risk minimisation, labeling update, referral under Article 20 or 31, or PASS. "
                    "Signal tracking is maintained in the EMA signal management tracking tool (EPITT)."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module IX Rev 1 — Signal Management",
            "GVP Module IX Addendum I — Methodological Aspects of Signal Detection from Spontaneous Reports",
            "Regulation (EC) No 726/2004 Article 28a",
            "Directive 2001/83/EC Article 107h–107k",
            "PRAC Rules of Procedure",
        ],
        "related_items": [
            "regulation/gvp-module-vi",
            "kpi/signal-detection-cycle",
            "report/psur",
            "market/eu",
        ],
    },
    ("regulation", "ich-e2c-r2"): {
        "title": "ICH E2C(R2) — Periodic Benefit-Risk Evaluation Report (PBRER)",
        "summary": (
            "International harmonised guideline for the Periodic Benefit-Risk Evaluation "
            "Report. Defines 19 report sections covering interval and cumulative safety data, "
            "signal evaluation, benefit-risk analysis by indication, and conclusions."
        ),
        "sections": [
            {
                "heading": "19 PBRER Sections",
                "detail_type": "text",
                "content": [
                    "Section 1: Title page",
                    "Section 2: Executive summary",
                    "Section 3: Table of contents",
                    "Section 4: Introduction",
                    "Section 5: Worldwide marketing approval status",
                    "Section 6: Actions taken in the reporting interval for safety reasons",
                    "Section 7: Changes to the reference safety information",
                    "Section 8: Estimated exposure and use patterns",
                    "Section 9: Data in summary tabulations",
                    "Section 10: Summaries of significant findings from clinical trials during the reporting interval",
                    "Section 11: Findings from non-interventional studies",
                    "Section 12: Information from other clinical trials and sources",
                    "Section 13: Non-clinical data",
                    "Section 14: Literature",
                    "Section 15: Other periodic reports",
                    "Section 16: Lack of efficacy in controlled clinical trials",
                    "Section 17: Late-breaking information",
                    "Section 18: Overview of signals: new, ongoing, or closed",
                    "Section 19: Signal and risk evaluation",
                    "Section 20: Benefit evaluation",
                    "Section 21: Integrated benefit-risk analysis for authorised indications",
                    "Section 22: Conclusions and actions",
                    "Section 23: Appendices",
                ],
            },
            {
                "heading": "Benefit-Risk Evaluation Methodology",
                "detail_type": "text",
                "content": (
                    "The PBRER requires an integrated benefit-risk analysis conducted for each approved "
                    "indication separately. Benefits are characterised based on: magnitude of treatment "
                    "effect, clinical relevance, quality and strength of evidence, and generalisability. "
                    "Risks are characterised by: seriousness, frequency, reversibility, preventability, "
                    "and impact on patients. The evaluation must conclude whether the overall benefit-risk "
                    "balance remains favourable, or whether any regulatory actions are warranted. A "
                    "structured framework (such as the PrOACT-URL or BRAT) may be used."
                ),
            },
            {
                "heading": "Interval vs. Cumulative Data",
                "detail_type": "key_value_pairs",
                "content": {
                    "Interval data": "New safety information received during the reporting period (data lock point to data lock point)",
                    "Cumulative data": "All safety data since DIBD/IBD (International Birth Date or first authorisation) — includes interval data",
                    "Exposure estimates": "Both interval and cumulative patient-exposure should be estimated where possible",
                    "Line listings": "Serious adverse reactions from interval period; cumulative for specific signals under evaluation",
                    "Signal section": "Covers new signals detected in interval, ongoing signals, and signals closed in interval, but evaluation considers cumulative data",
                },
            },
            {
                "heading": "Indication-by-Indication Analysis",
                "detail_type": "text",
                "content": (
                    "For products with multiple approved indications, the benefit-risk evaluation must be "
                    "performed separately for each indication. This accounts for different disease severity, "
                    "patient populations, treatment alternatives, dosing regimens, and risk profiles "
                    "across indications. Where a risk applies to all indications, it may be discussed "
                    "once with cross-reference, but the benefit-risk conclusion must be stated for each "
                    "indication individually."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2C(R2) — Periodic Benefit-Risk Evaluation Report (PBRER)",
            "ICH E2C(R2) Q&A Document",
            "EU GVP Module VII — Periodic Safety Update Report",
            "EMA Guidance on the Format and Content of the PSUR/PBRER",
        ],
        "related_items": [
            "report/pbrer",
            "report/psur",
            "regulation/gvp-module-ix",
            "regulation/21-cfr-314-80",
        ],
    },

    # ── REPORTS ──────────────────────────────────────────────────────────
    ("report", "dsur"): {
        "title": "DSUR — Development Safety Update Report",
        "summary": (
            "Per ICH E2F, the DSUR provides an annual safety review for investigational "
            "drugs. Based on the Development International Birth Date (DIBD), with submission "
            "deadline of DIBD + 60 calendar days. Contains 20 sections covering line listings, "
            "overall safety assessment, important risks, and benefit-risk conclusions."
        ),
        "sections": [
            {
                "heading": "Structure (20 Sections per ICH E2F)",
                "detail_type": "text",
                "content": [
                    "1. Title page",
                    "2. Executive summary",
                    "3. Table of contents",
                    "4. Introduction",
                    "5. Worldwide marketing approval status",
                    "6. Actions taken for safety reasons during the reporting period",
                    "7. Changes to the Reference Safety Information (RSI/IB)",
                    "8. Inventory of ongoing and completed clinical trials",
                    "9. Estimated cumulative exposure (clinical trials and market)",
                    "10. Data in line listings and summary tabulations",
                    "11. Significant findings from clinical trials",
                    "12. Safety findings from non-interventional studies",
                    "13. Other safety information (preclinical, literature, registries)",
                    "14. Late-breaking information",
                    "15. Overview of signals (new, ongoing, closed)",
                    "16. Summary of identified and potential risks",
                    "17. Summary of important findings during the reporting period",
                    "18. Overall safety assessment",
                    "19. Summary of important risks",
                    "20. Benefit-risk considerations",
                ],
            },
            {
                "heading": "Key Sections in Detail",
                "detail_type": "key_value_pairs",
                "content": {
                    "Section 7 (Line Listings)": "All SAEs from interventional studies conducted by the sponsor, listed by study, patient, event, seriousness criteria, causality, and outcome",
                    "Section 18 (Overall Safety Assessment)": "Integrated analysis of all safety data — characterise the overall safety profile, compare to RSI, identify any changes",
                    "Section 19 (Important Risks)": "Consolidation of identified and potential risks, missing information — directly informs the risk management strategy",
                    "Section 20 (Benefit-Risk Conclusions)": "Whether the benefit-risk balance supports continuation of clinical development; any necessary protocol amendments or additional safeguards",
                },
            },
            {
                "heading": "DSUR vs. PBRER",
                "detail_type": "table",
                "content": {
                    "columns": ["Aspect", "DSUR", "PBRER"],
                    "rows": [
                        ["Applicable phase", "Investigational (pre-approval)", "Post-marketing (post-approval)"],
                        ["Guideline", "ICH E2F", "ICH E2C(R2)"],
                        ["Reference safety info", "Investigator's Brochure (IB)", "Company Core Safety Information (CCSI)"],
                        ["Reporting cycle", "Annual from DIBD", "Per EURD list or approval-based"],
                        ["Primary purpose", "Support continued development", "Evaluate ongoing benefit-risk for marketed product"],
                        ["Regulatory recipients", "All regulatory authorities where IND/CTA active", "All authorities where product approved"],
                    ],
                },
            },
        ],
        "regulatory_references": [
            "ICH E2F — Development Safety Update Report",
            "21 CFR 312.33 (annual report — DSUR accepted as alternative)",
            "EU Clinical Trials Regulation (EU) No 536/2014 Article 43",
        ],
        "related_items": [
            "regulation/21-cfr-312-32",
            "report/pbrer",
            "committee/dsmb",
        ],
    },
    ("report", "pbrer"): {
        "title": "PBRER — Periodic Benefit-Risk Evaluation Report",
        "summary": (
            "Per ICH E2C(R2), the PBRER is the global standard for periodic safety reporting "
            "of approved medicinal products. Contains 19+ sections with interval and cumulative "
            "data, signal evaluation, benefit-risk analysis by indication, and conclusions. "
            "Submission frequency defined per the EU EURD list."
        ),
        "sections": [
            {
                "heading": "Key Sections",
                "detail_type": "key_value_pairs",
                "content": {
                    "Section 15 (Other Periodic Reports)": "Cross-reference to other periodic reports covering the same substance",
                    "Section 16 (Lack of Efficacy)": "Evaluation of lack of efficacy reports, especially where this represents a safety concern (e.g., treatment failure in serious diseases)",
                    "Section 18 (Signals Overview)": "New signals detected during interval, ongoing signal evaluations, signals closed — tabular format with status and actions",
                    "Section 19 (Signal and Risk Evaluation)": "Detailed evaluation of each significant signal, updated characterisation of identified and potential risks",
                    "Section 20 (Benefit Evaluation)": "Summary of efficacy/effectiveness data, new indications, new formulations; context for benefit-risk evaluation",
                    "Section 21 (Integrated Benefit-Risk)": "Indication-by-indication benefit-risk analysis; conclusion on whether the balance remains favourable",
                },
            },
            {
                "heading": "Interval vs. Cumulative Data",
                "detail_type": "text",
                "content": (
                    "The PBRER distinguishes between interval data (events and information received "
                    "during the current reporting period) and cumulative data (all data from IBD/first "
                    "authorisation to the current data lock point). Section 9 summary tabulations "
                    "present both interval and cumulative serious adverse reaction counts by SOC and PT. "
                    "Estimated exposure must be provided for both interval and cumulative periods. "
                    "Clinical trial data should separate blinded vs. unblinded information. Post-marketing "
                    "exposure can be estimated from sales data, defined daily doses, or prescription data."
                ),
            },
            {
                "heading": "Submission Frequency (EURD List)",
                "detail_type": "text",
                "content": (
                    "In the EU, submission frequency is governed by the EURD (European Union Reference "
                    "Dates) list maintained by EMA. Typical schedule: 6-monthly for the first 2 years "
                    "after authorisation, annually for the next 2 years, then every 3 years. Frequency "
                    "may be adjusted by PRAC. The EURD list defines the data lock point (DLP) and "
                    "submission deadline (DLP + 70 days for single-active-substance products, DLP + 90 "
                    "days for others). For non-EU markets, submission follows local regulatory requirements."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2C(R2) — Periodic Benefit-Risk Evaluation Report",
            "EU GVP Module VII — Periodic Safety Update Report",
            "EURD List (European Union Reference Dates)",
            "Regulation (EC) No 726/2004 Article 28(2)",
        ],
        "related_items": [
            "regulation/ich-e2c-r2",
            "report/dsur",
            "report/psur",
            "report/pader",
        ],
    },
    ("report", "psur"): {
        "title": "PSUR — EU Periodic Safety Update Report / PSUSA Process",
        "summary": (
            "In the EU, the PSUR is a PBRER submitted under the PSUR Single Assessment (PSUSA) "
            "procedure. PRAC conducts a single assessment for all products containing the same "
            "active substance, regardless of MAH. Outcomes can include maintenance, variation, "
            "suspension, revocation, or referral."
        ),
        "sections": [
            {
                "heading": "Relationship to PBRER",
                "detail_type": "text",
                "content": (
                    "Since 2012, the EU PSUR follows the ICH E2C(R2) PBRER format. The terms 'PSUR' "
                    "and 'PBRER' are often used interchangeably in EU context. All MAHs for products "
                    "containing the same active substance submit their PSURs to EMA under a single "
                    "assessment procedure (PSUSA), using the same data lock point defined in the "
                    "EURD list."
                ),
            },
            {
                "heading": "PSUSA Procedure",
                "detail_type": "timeline",
                "content": [
                    {"event": "Data Lock Point (DLP)", "description": "As defined in the EURD list for the active substance"},
                    {"event": "PSUR submission", "description": "DLP + 70 days (single substance) or DLP + 90 days (combination/complex)"},
                    {"event": "PRAC assessment start", "description": "Validation and start of assessment procedure"},
                    {"event": "PRAC rapporteur report", "description": "Day 60 — preliminary assessment with list of questions to MAH"},
                    {"event": "MAH responses", "description": "Day 90 — MAH provides responses to PRAC questions"},
                    {"event": "PRAC recommendation", "description": "Day 120 — final recommendation adopted by PRAC"},
                    {"event": "CMDh/CHMP decision", "description": "Day 150 — position adopted; if disagreement, referral to CHMP"},
                    {"event": "European Commission decision", "description": "Legally binding decision for all EU member states"},
                ],
            },
            {
                "heading": "Possible Outcomes",
                "detail_type": "key_value_pairs",
                "content": {
                    "Maintain": "No change — benefit-risk remains favourable, no new safety concerns",
                    "Vary (Type II variation)": "Update SmPC and/or PIL to reflect new safety information",
                    "Suspend": "Temporary suspension of marketing authorisation pending further data",
                    "Revoke": "Permanent withdrawal of marketing authorisation",
                    "Referral (Article 20/31)": "Referral to CHMP for EU-wide assessment when serious safety concern arises",
                    "Additional pharmacovigilance activities": "Require PASS, enhanced monitoring, or DHPC",
                },
            },
        ],
        "regulatory_references": [
            "Regulation (EC) No 726/2004 Article 28(2)",
            "Directive 2001/83/EC Article 107b–107g",
            "EU GVP Module VII — Periodic Safety Update Report",
            "EURD List and PSUSA Procedure Guidance",
        ],
        "related_items": [
            "report/pbrer",
            "regulation/ich-e2c-r2",
            "regulation/gvp-module-ix",
            "market/eu",
        ],
    },
    ("report", "pader"): {
        "title": "PADER — FDA Periodic Adverse Drug Experience Report",
        "summary": (
            "The PADER is the FDA's regulatory instrument for periodic post-marketing safety "
            "reporting under 21 CFR 314.81(b)(2)(i). NDA holders submit quarterly reports for "
            "the first 3 years after approval, then annual reports. Due 30 days after the close "
            "of each quarterly/annual reporting period."
        ),
        "sections": [
            {
                "heading": "Submission Schedule",
                "detail_type": "key_value_pairs",
                "content": {
                    "Quarters 1–12 (Years 1–3)": "Quarterly submission, due 30 days after quarter close based on approval date",
                    "Year 4 and beyond": "Annual submission, due 60 days after the anniversary of the approval date",
                    "Data lock point": "End of each quarterly or annual period (not a fixed calendar date)",
                },
            },
            {
                "heading": "Required Content",
                "detail_type": "text",
                "content": [
                    "A 3500A form for each adverse drug experience not submitted as a 15-day alert report",
                    "A narrative summary and analysis of the data including 15-day alerts submitted during the period",
                    "A history of actions taken since last report due to adverse drug experiences",
                    "An index of patient identifiers, adverse reaction terms, and outcomes",
                    "A narrative discussion of any significant changes in adverse event patterns",
                ],
            },
            {
                "heading": "Relationship to PBRER",
                "detail_type": "text",
                "content": (
                    "The FDA has stated it will accept a PBRER (ICH E2C(R2)) in lieu of a PADER for "
                    "NDA holders. This allows sponsors with global products to prepare a single periodic "
                    "report. However, the submission schedule may differ: PADERs follow the NDA approval "
                    "date, while PBRERs follow the International Birth Date (IBD). ANDA holders generally "
                    "continue to submit PADERs rather than PBRERs."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 314.80 — Postmarketing Reporting of Adverse Drug Experiences",
            "21 CFR 314.81(b)(2)(i) — Periodic Adverse Drug Experience Reports",
            "FDA Federal Register Notice (2014) — Acceptance of ICH E2C(R2) PBRER",
        ],
        "related_items": [
            "regulation/21-cfr-314-80",
            "report/pbrer",
            "market/us",
        ],
    },

    # ── KPIs ─────────────────────────────────────────────────────────────
    ("kpi", "case-processing-time"): {
        "title": "Case Processing Time",
        "summary": (
            "Average time from Day 0 (date of first awareness of a valid ICSR) to submission "
            "to the relevant regulatory authority. Target is within 15 calendar days for "
            "expedited (serious) cases."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Target (expedited/serious)": "≤ 15 calendar days from Day 0 to submission",
                    "Target (non-serious)": "≤ 90 calendar days from Day 0 to submission",
                    "Regulatory basis": "GVP Module VI (EU), 21 CFR 314.80/312.32 (US), ICH E2D",
                    "Measurement": "Calendar days from receipt date (Day 0) to electronic submission timestamp",
                },
            },
            {
                "heading": "Measurement Methodology",
                "detail_type": "text",
                "content": (
                    "Calculated as: Submission Date − Day 0 Date (in calendar days). Measured per case, "
                    "then aggregated as mean, median, and P90 across the reporting period. Broken down "
                    "by case source (spontaneous, clinical trial, literature, authority), seriousness, "
                    "and market. Excludes nullified/voided cases."
                ),
            },
            {
                "heading": "Trend Analysis and Root Causes for Misses",
                "detail_type": "text",
                "content": [
                    "Common root causes: delayed receipt from source, insufficient initial information requiring extensive follow-up, data entry backlog, medical review bottleneck, quality check rework, system/technical failures",
                    "Trend analysis: track monthly/quarterly, compare to rolling 12-month average, identify seasonal patterns (e.g., holiday periods), monitor after process changes",
                    "Industry benchmark: median 10–12 days for expedited cases; top quartile achieves median ≤ 8 days",
                ],
            },
        ],
        "regulatory_references": [
            "GVP Module VI Rev 2",
            "21 CFR 314.80",
            "ICH E2D",
        ],
        "related_items": [
            "kpi/serious-15-day",
            "regulation/gvp-module-vi",
            "sop/PV-SOP-001",
        ],
    },
    ("kpi", "serious-15-day"): {
        "title": "Serious 15-Day Expedited Reporting Compliance Rate",
        "summary": (
            "Percentage of serious expedited ICSRs submitted within the 15-calendar-day "
            "regulatory deadline. Target ≥ 95%; top quartile organisations achieve ≥ 98%."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of expedited ICSRs submitted on time ÷ Total expedited ICSRs due) × 100",
                    "Target": "≥ 95%",
                    "Top quartile benchmark": "≥ 98%",
                    "Regulatory consequence of non-compliance": "Inspection findings (critical/major), warning letters, consent decrees",
                },
            },
            {
                "heading": "Stratification",
                "detail_type": "text",
                "content": (
                    "Should be tracked globally and stratified by: regulatory authority (FDA, EMA, "
                    "PMDA, NMPA, etc.), product, case source (spontaneous, trial, literature), "
                    "business partner/CRO, and processing site. Late submissions should be root-cause "
                    "analysed and tracked in a CAPA system."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module VI",
            "21 CFR 314.80 / 312.32",
            "ICH E2D",
        ],
        "related_items": [
            "kpi/case-processing-time",
            "kpi/7-day-compliance",
            "regulation/gvp-module-vi",
        ],
    },
    ("kpi", "7-day-compliance"): {
        "title": "7-Day Fatal/Life-Threatening Reporting Compliance",
        "summary": (
            "Compliance rate for IND 7-day telephone/fax reports for fatal or life-threatening "
            "unexpected suspected adverse reactions under 21 CFR 312.32(c)(2)."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of 7-day reports submitted on time ÷ Total 7-day reports due) × 100",
                    "Target": "100% — zero tolerance for late reporting of fatal/life-threatening events",
                    "Regulatory basis": "21 CFR 312.32(c)(2)",
                    "Follow-up": "Written follow-up (IND Safety Report) due within 8 additional calendar days",
                },
            },
            {
                "heading": "Process Controls",
                "detail_type": "text",
                "content": (
                    "Given the extremely short timeline, organisations must have 24/7 intake capability, "
                    "immediate medical officer escalation pathways, pre-approved unblinding procedures, "
                    "and templated reporting formats. Any miss is typically classified as a critical "
                    "deviation requiring immediate CAPA."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 312.32(c)(2)",
            "FDA Guidance: Safety Reporting Requirements for INDs (2012)",
        ],
        "related_items": [
            "kpi/serious-15-day",
            "regulation/21-cfr-312-32",
        ],
    },
    ("kpi", "signal-detection-cycle"): {
        "title": "Signal Detection Cycle Time",
        "summary": (
            "Time from data availability to completion of signal detection review cycle. "
            "Measures the efficiency of routine pharmacovigilance signal detection activities."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Measurement": "Calendar days from scheduled data extraction/lock to completion of signal detection review and documentation",
                    "Target": "≤ 30 calendar days per cycle",
                    "Frequency": "Monthly or quarterly depending on product risk and volume",
                    "Regulatory basis": "GVP Module IX, ICH E2E",
                },
            },
            {
                "heading": "Components",
                "detail_type": "text",
                "content": [
                    "Data extraction and quality check: 1–3 days",
                    "Statistical screening (PRR, ROR, EBGM): 2–5 days",
                    "Clinical review of statistical signals: 5–10 days",
                    "Medical assessment and documentation: 3–7 days",
                    "Peer review and sign-off: 2–5 days",
                    "Total target: ≤ 30 days end-to-end",
                ],
            },
        ],
        "regulatory_references": [
            "GVP Module IX Rev 1",
            "ICH E2E — Pharmacovigilance Planning",
        ],
        "related_items": [
            "regulation/gvp-module-ix",
            "kpi/serious-15-day",
        ],
    },
    ("kpi", "e2b-acceptance"): {
        "title": "E2B Transmission Acceptance Rate",
        "summary": (
            "Percentage of E2B(R3) ICSR transmissions accepted by regulatory authorities "
            "(EudraVigilance, FDA ESG) without rejection. Target ≥ 98%."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of E2B transmissions accepted (ACK01/ACK02) ÷ Total transmissions sent) × 100",
                    "Target": "≥ 98%",
                    "Rejection types": "ACK03 (warning — accepted with issues), ACK04 (rejected — must re-submit)",
                    "Measurement period": "Monthly",
                },
            },
            {
                "heading": "Common Rejection Reasons",
                "detail_type": "text",
                "content": [
                    "Invalid MedDRA coding (version mismatch or deprecated terms)",
                    "Missing mandatory fields (e.g., reporter country, seriousness criteria)",
                    "Invalid product identification (substance name, ATC code mismatch)",
                    "Duplicate case detection by authority database",
                    "Schema validation errors (XML structure, data type mismatches)",
                    "Gateway connectivity or authentication failures",
                ],
            },
        ],
        "regulatory_references": [
            "ICH E2B(R3)",
            "EudraVigilance Technical Documentation",
            "FDA ESG Gateway Guide",
        ],
        "related_items": [
            "kpi/case-processing-time",
            "regulation/gvp-module-vi",
        ],
    },
    ("kpi", "training-compliance"): {
        "title": "PV Training Compliance Rate",
        "summary": (
            "Percentage of pharmacovigilance personnel who have completed all required training "
            "curricula within defined timelines. Target ≥ 95%."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of staff with all required training current ÷ Total PV staff) × 100",
                    "Target": "≥ 95%",
                    "Measurement frequency": "Monthly snapshot",
                    "Regulatory basis": "GVP Module I (PV system), 21 CFR 211.25 (qualified personnel), ICH E6(R2) GCP",
                },
            },
            {
                "heading": "Training Categories",
                "detail_type": "text",
                "content": [
                    "Role-based initial training (within 30 days of assignment to PV role)",
                    "Annual refresher on SOPs, regulatory updates, and safety database systems",
                    "Product-specific training for new product assignments",
                    "MedDRA coding certification and recertification",
                    "GCP/GVP regulatory training (biennial)",
                    "Vendor/CRO oversight training for outsourced activities",
                ],
            },
        ],
        "regulatory_references": [
            "GVP Module I — Pharmacovigilance Systems and Their Quality Systems",
            "21 CFR 211.25",
            "ICH E6(R2) Section 2.8",
        ],
        "related_items": [
            "kpi/sop-currency",
            "sop/PV-SOP-005",
        ],
    },
    ("kpi", "sop-currency"): {
        "title": "SOP Currency Rate",
        "summary": (
            "Percentage of pharmacovigilance SOPs that are within their review cycle and not "
            "overdue for periodic review. Target 100%."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of SOPs current and within review cycle ÷ Total PV SOPs) × 100",
                    "Target": "100% — all SOPs must be current",
                    "Review cycle": "Every 2 years or upon significant regulatory change, whichever is sooner",
                    "Grace period": "30 days from review due date before classified as overdue",
                    "Regulatory basis": "GVP Module I, ICH Q10, 21 CFR 211.22",
                },
            },
            {
                "heading": "Tracking",
                "detail_type": "text",
                "content": (
                    "Maintain a master SOP register with: SOP number, title, effective date, review due date, "
                    "owner, status (current/under review/overdue/retired). Report monthly at PV governance "
                    "meetings. Overdue SOPs should trigger immediate review initiation and temporary risk "
                    "assessment. Common root causes for overdue SOPs: resource constraints, pending regulatory "
                    "guidance, organisational restructuring, cross-functional review delays."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module I",
            "ICH Q10 — Pharmaceutical Quality System",
        ],
        "related_items": [
            "kpi/training-compliance",
            "sop/PV-SOP-001",
        ],
    },
    ("kpi", "capa-closure-rate"): {
        "title": "CAPA Closure Rate",
        "summary": (
            "Percentage of pharmacovigilance Corrective and Preventive Actions (CAPAs) closed "
            "within the target timeline. Target ≥ 90% closed on time."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Number of CAPAs closed on or before target date ÷ Total CAPAs due for closure) × 100",
                    "Target": "≥ 90% closed on time",
                    "Typical timelines": "Minor CAPAs: 30 days; Major CAPAs: 90 days; Critical CAPAs: as defined in action plan",
                    "Measurement": "Monthly, reported at quality governance meetings",
                },
            },
            {
                "heading": "CAPA Lifecycle",
                "detail_type": "text",
                "content": [
                    "Identification: deviation detected via audit, inspection, KPI breach, or complaint",
                    "Root cause analysis: Ishikawa, 5-Whys, or fault-tree analysis",
                    "Corrective action: immediate fix to address the specific instance",
                    "Preventive action: systemic fix to prevent recurrence (process change, training, system update)",
                    "Effectiveness check: verify the CAPA achieved its objective 30–90 days after implementation",
                    "Closure: documented evidence of completion and effectiveness, approved by quality",
                ],
            },
        ],
        "regulatory_references": [
            "GVP Module I",
            "ICH Q10 — Pharmaceutical Quality System",
            "21 CFR 820.90 (QSR — CAPA)",
        ],
        "related_items": [
            "kpi/sop-currency",
            "kpi/serious-15-day",
        ],
    },

    # ── MARKETS ──────────────────────────────────────────────────────────
    ("market", "us"): {
        "title": "United States — FDA Regulatory Framework",
        "summary": (
            "The US FDA regulates drugs through IND (investigational) and NDA/BLA (marketing) "
            "applications. Post-marketing safety is monitored via FAERS, MedWatch, REMS programs, "
            "and post-marketing commitments/requirements (PMCs/PMRs)."
        ),
        "sections": [
            {
                "heading": "Drug Development Pathway",
                "detail_type": "key_value_pairs",
                "content": {
                    "Pre-IND": "Pre-clinical studies, CMC, toxicology; pre-IND meeting with FDA (Type B)",
                    "IND (Investigational New Drug)": "21 CFR 312 — allows clinical trials in US; 30-day review; clinical hold possible",
                    "NDA (New Drug Application)": "21 CFR 314 — complete dossier for marketing approval; standard (10-month) or priority (6-month) review",
                    "BLA (Biologics License Application)": "Section 351 PHS Act — for biological products",
                    "Accelerated pathways": "Fast Track, Breakthrough Therapy, Accelerated Approval, Priority Review",
                },
            },
            {
                "heading": "Post-Marketing Safety Framework",
                "detail_type": "text",
                "content": [
                    "FAERS (FDA Adverse Event Reporting System): central database for post-marketing adverse event reports",
                    "MedWatch: FDA's safety reporting program — Form 3500 (voluntary), Form 3500A (mandatory)",
                    "REMS (Risk Evaluation and Mitigation Strategies): required when necessary to ensure benefits outweigh risks; may include medication guide, communication plan, ETASU",
                    "PMCs/PMRs (Post-Marketing Commitments/Requirements): studies or clinical trials required by FDA as condition of approval or requested post-approval",
                    "Sentinel System: active surveillance using electronic health data from >100 million patients",
                    "Drug Safety Communications (DSCs): public safety announcements",
                ],
            },
            {
                "heading": "Companion Diagnostics",
                "detail_type": "text",
                "content": (
                    "FDA requires companion diagnostics (CDx) for drugs with biomarker-driven indications. "
                    "CDx are regulated as Class III medical devices and require PMA (Premarket Approval) "
                    "or De Novo classification. Co-development with the therapeutic is expected. For EGFR "
                    "TKIs, approved CDx include cobas EGFR Mutation Test v2, therascreen EGFR RGQ PCR Kit, "
                    "and FoundationOne CDx (NGS-based). LDTs (Laboratory Developed Tests) remain a "
                    "regulatory gray area — FDA has proposed but not finalised regulation."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 312 — Investigational New Drug Application",
            "21 CFR 314 — Applications for FDA Approval to Market a New Drug",
            "21 CFR 314.80 — Postmarketing Reporting",
            "FDCA Section 505-1 — REMS",
            "FDA Sentinel Initiative",
        ],
        "related_items": [
            "regulation/21-cfr-312-32",
            "regulation/21-cfr-314-80",
            "report/pader",
        ],
    },
    ("market", "eu"): {
        "title": "European Union — EMA Regulatory Framework",
        "summary": (
            "The EMA coordinates EU-wide regulation through the centralised procedure, with CHMP "
            "for efficacy and PRAC for pharmacovigilance. Key instruments include the RMP, "
            "PSUR/PSUSA, EudraVigilance, referral procedures, and the EPAR."
        ),
        "sections": [
            {
                "heading": "Centralised Procedure",
                "detail_type": "text",
                "content": (
                    "Mandatory for: biotech products, orphan medicines, HIV/cancer/diabetes/neurodegenerative "
                    "diseases/autoimmune/viral diseases (since 2004), and advanced therapies. Optional for "
                    "other innovative products. Results in a single EU-wide marketing authorisation valid "
                    "in all member states. Assessment by CHMP rapporteur and co-rapporteur over 210 days "
                    "(active review time). European Commission issues the final decision."
                ),
            },
            {
                "heading": "Pharmacovigilance Framework",
                "detail_type": "key_value_pairs",
                "content": {
                    "PRAC": "Pharmacovigilance Risk Assessment Committee — responsible for all aspects of risk management, signal assessment, PSUR assessment, and referrals",
                    "RMP (Risk Management Plan)": "Required at time of MA application; includes safety specification, pharmacovigilance plan, and risk minimisation measures",
                    "PSUR/PSUSA": "Periodic safety reporting per EURD list with single assessment by PRAC",
                    "EudraVigilance": "EU database for ICSRs — all serious and non-serious (EEA) cases reported here",
                    "DHPC (Dear Healthcare Professional Communication)": "Direct communication to HCPs about important new safety information",
                    "PASS (Post-Authorisation Safety Study)": "Non-interventional or interventional study to obtain further data on safety profile",
                },
            },
            {
                "heading": "Referral Procedures",
                "detail_type": "key_value_pairs",
                "content": {
                    "Article 20": "Triggered by pharmacovigilance data — PRAC assesses, CHMP gives opinion, Commission decides",
                    "Article 31": "Referral in the interest of the Union — broader scope, can address any safety/efficacy concern",
                    "Article 107i (Urgent Union Procedure)": "For urgent safety issues — PRAC must give recommendation within 60 days",
                    "Outcome options": "Maintain, vary (Type II), suspend, revoke marketing authorisation",
                },
            },
            {
                "heading": "EPAR (European Public Assessment Report)",
                "detail_type": "text",
                "content": (
                    "Published by EMA for every centrally authorised product. Contains a summary of the "
                    "scientific assessment, benefit-risk conclusions, conditions of the MA, and a "
                    "lay-language summary (package leaflet). Updated after each significant variation. "
                    "Publicly available on EMA website — key resource for understanding the regulatory "
                    "basis of approval and post-marketing obligations."
                ),
            },
        ],
        "regulatory_references": [
            "Regulation (EC) No 726/2004",
            "Directive 2001/83/EC",
            "Regulation (EU) No 1235/2010 (pharmacovigilance)",
            "EU GVP Modules I–XVI",
            "Clinical Trials Regulation (EU) No 536/2014",
        ],
        "related_items": [
            "regulation/gvp-module-vi",
            "regulation/gvp-module-ix",
            "report/psur",
            "report/pbrer",
        ],
    },
    ("market", "japan"): {
        "title": "Japan — PMDA Regulatory Framework",
        "summary": (
            "Japan's PMDA (Pharmaceuticals and Medical Devices Agency) oversees drug regulation "
            "with unique requirements including EPPV (Early Post-marketing Phase Vigilance), "
            "bridging study requirements, and heightened awareness of ILD risk following the "
            "gefitinib crisis (588 deaths, class action lawsuits)."
        ),
        "sections": [
            {
                "heading": "Regulatory Pathway",
                "detail_type": "key_value_pairs",
                "content": {
                    "Clinical Trial Notification (CTN)": "30-day review period before trial initiation",
                    "New Drug Application (J-NDA)": "Submitted to PMDA; review by Office of New Drug teams; PMDA review + MHLW approval",
                    "Review timeline": "Standard 12 months; Priority (SAKIGAKE) 6 months; Conditional early approval available",
                    "SAKIGAKE designation": "Japan's breakthrough therapy equivalent — priority review, pre-submission consultation, extended re-exam period",
                    "Re-examination (reexam)": "Post-marketing re-evaluation of efficacy/safety; typically 8 years for new actives (4 years for orphan)",
                },
            },
            {
                "heading": "Gefitinib Crisis and Its Legacy",
                "detail_type": "text",
                "content": (
                    "Gefitinib (Iressa) was approved in Japan in July 2002 — the first country globally. "
                    "Within months, reports of fatal interstitial lung disease (ILD) accumulated rapidly. "
                    "By 2012, approximately 588 deaths attributed to gefitinib-related ILD had been reported "
                    "in Japan. Class action lawsuits were filed by patients' families. The crisis led to: "
                    "strengthened EPPV requirements, black box warnings, mandatory patient consent documentation, "
                    "restricted prescribing to pulmonologists, and a fundamental shift in Japanese regulatory "
                    "culture toward heightened vigilance for pulmonary toxicity. Japanese regulators now "
                    "scrutinize ILD risk for all oncology products with particular intensity."
                ),
            },
            {
                "heading": "EPPV (Early Post-marketing Phase Vigilance)",
                "detail_type": "text",
                "content": (
                    "Unique to Japan. For the first 6 months after launch, MAHs must implement intensive "
                    "monitoring: MR visits to all prescribing institutions, collection of all adverse events "
                    "(not just serious/unexpected), prompt safety information distribution to HCPs, and "
                    "dedicated safety management team. EPPV was significantly strengthened after the "
                    "gefitinib crisis. PMDA inspects EPPV compliance."
                ),
            },
            {
                "heading": "ILD Risk in Japanese Patients",
                "detail_type": "key_value_pairs",
                "content": {
                    "Incidence multiplier": "Japanese patients show 2–3× higher ILD incidence vs. Western populations for EGFR TKIs and many other drug classes",
                    "Contributing factors": "Genetic predisposition (HLA types, MUC5B polymorphisms), higher prevalence of pre-existing ILD, environmental factors, diagnostic vigilance",
                    "Regulatory expectation": "All oncology products must include ILD in the risk management plan; specific ILD monitoring protocols required",
                    "Bridging studies": "PMDA may require Japan-specific bridging or dedicated J-cohort to characterise ILD risk in Japanese patients",
                },
            },
            {
                "heading": "Bridging Studies",
                "detail_type": "text",
                "content": (
                    "Per ICH E5, PMDA evaluates whether foreign clinical data can be extrapolated to "
                    "Japanese patients. Factors considered: ethnic sensitivity of PK/PD, disease prevalence "
                    "and characteristics, medical practice differences. If bridging is needed, a Japanese "
                    "bridging study (typically Phase I PK + limited Phase II) is required. For oncology, "
                    "PMDA increasingly accepts global MRCT data with adequate Japanese sub-population "
                    "(typically ≥ 20% of enrollment or a dedicated Japanese cohort)."
                ),
            },
        ],
        "regulatory_references": [
            "Pharmaceutical and Medical Devices Act (PMD Act, 2014)",
            "ICH E5 — Ethnic Factors in the Acceptability of Foreign Clinical Data",
            "PMDA EPPV Guidance",
            "MHLW Ordinance on GVP",
        ],
        "related_items": [
            "market/us",
            "market/eu",
            "report/dsur",
        ],
    },
    ("market", "china"): {
        "title": "China — NMPA Regulatory Framework",
        "summary": (
            "China's NMPA (National Medical Products Administration) has undergone rapid reform "
            "since 2015. In 2024, 46 Class 1 innovative drugs were approved. The EGFR TKI market "
            "features 8 domestic competitors. NRDL (National Reimbursement Drug List) pricing "
            "negotiations and MRCT acceptance have transformed the landscape."
        ),
        "sections": [
            {
                "heading": "Regulatory Pathway",
                "detail_type": "key_value_pairs",
                "content": {
                    "IND (Clinical Trial Application)": "60-day default approval (silence = consent since 2018)",
                    "NDA": "Standard review ~200 working days; Priority Review for innovative drugs, paediatrics, rare diseases",
                    "Drug classification": "Class 1 (globally novel), Class 2 (modified), Class 3 (generic), Class 4 (imported), Class 5 (others)",
                    "Breakthrough Therapy Designation": "Introduced 2020 — allows rolling submission, enhanced communication with CDE",
                    "Conditional approval": "Available for serious diseases with unmet need — post-marketing confirmatory study required",
                },
            },
            {
                "heading": "Innovation Landscape (2024)",
                "detail_type": "text",
                "content": (
                    "In 2024, NMPA approved 46 Class 1 innovative drugs — a record number reflecting "
                    "China's ambition to become a global pharmaceutical innovator. The oncology segment "
                    "dominates, with 8 domestically developed EGFR TKIs now competing in the Chinese market "
                    "(including almonertinib, furmonertinib, befotertinib, and limertinib alongside global "
                    "products). Chinese biotechs are increasingly pursuing global development, with several "
                    "US FDA applications originating from China-first clinical programs."
                ),
            },
            {
                "heading": "NRDL Pricing and Market Access",
                "detail_type": "text",
                "content": (
                    "The National Reimbursement Drug List (NRDL) is updated annually through competitive "
                    "price negotiations. Inclusion in NRDL is critical for market access — covers >95% of "
                    "the insured population. Typical price reductions: 50–70% from list price at negotiation. "
                    "Products are initially included for 2 years with volume-based renewal. NRDL listing "
                    "significantly increases volume but at dramatically lower prices. For EGFR TKIs, "
                    "intense domestic competition has driven prices well below global levels."
                ),
            },
            {
                "heading": "MRCT Acceptance",
                "detail_type": "text",
                "content": (
                    "Since 2018, NMPA/CDE accepts Multi-Regional Clinical Trial (MRCT) data for "
                    "registration, aligned with ICH E17. Requirements: Chinese sub-population must be "
                    "adequately represented (typically ≥ 20% or sufficient for subgroup analysis); "
                    "clinical sites in China must comply with Chinese GCP; ethnic sensitivity assessment "
                    "must be addressed. This policy shift has enabled simultaneous global submissions "
                    "and reduced development timelines by 2–3 years compared to the previous China-"
                    "specific study requirement."
                ),
            },
            {
                "heading": "Pharmacovigilance Requirements",
                "detail_type": "key_value_pairs",
                "content": {
                    "ICSR reporting": "15 calendar days for serious; periodic reporting per NMPA schedule",
                    "PSUR": "NMPA accepts PBRER format; submission typically annual for first 5 years then every 5 years",
                    "Risk Management Plan": "Required at NDA submission; NMPA-specific template",
                    "MAH system": "Marketing Authorization Holder bears full PV responsibility (implemented 2019)",
                    "Annual report": "Annual safety report required for all marketed products",
                },
            },
        ],
        "regulatory_references": [
            "Drug Administration Law (revised 2019)",
            "Provisions for Drug Registration (2020)",
            "CDE Technical Guidelines for MRCT Acceptance",
            "NMPA Pharmacovigilance Regulations (2021)",
            "NRDL Negotiation Rules (updated annually)",
        ],
        "related_items": [
            "market/us",
            "market/japan",
            "report/pbrer",
        ],
    },

    # ── SOPs ─────────────────────────────────────────────────────────────
    ("sop", "PV-SOP-001"): {
        "title": "PV-SOP-001 — ICSR Intake and Triage",
        "summary": (
            "Defines the process for receipt, triage, and initial processing of Individual "
            "Case Safety Reports (ICSRs) from all sources."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure consistent, timely, and compliant receipt and triage of adverse event "
                    "reports from all sources (spontaneous, clinical trial, literature, health authorities, "
                    "patient support programs, social media, and business partners)."
                ),
            },
            {
                "heading": "Scope",
                "detail_type": "text",
                "content": (
                    "Applies to all pharmacovigilance staff involved in case intake, including safety "
                    "database operators, call centre personnel, medical information staff, and CRO/vendor "
                    "partners performing delegated intake activities."
                ),
            },
            {
                "heading": "Regulatory Basis",
                "detail_type": "text",
                "content": "GVP Module VI, 21 CFR 314.80/312.32, ICH E2D, ICH E2B(R3)",
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Receive report from any source channel (phone, fax, email, portal, literature scan, social media monitoring)",
                    "2. Log receipt with timestamp to establish Day 0",
                    "3. Assess case validity (4 minimum criteria per GVP Module VI)",
                    "4. Triage for seriousness and expectedness against RSI/CCSI",
                    "5. Assign regulatory reporting timeline (7-day, 15-day, 90-day, or non-reportable)",
                    "6. Enter initial case data into safety database within 24 hours of receipt",
                    "7. Assign to case processor for full data entry and medical review",
                    "8. If insufficient for valid case, document and file; re-evaluate upon follow-up",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon regulatory change",
                    "Training requirement": "All intake staff must complete training within 30 days of assignment; annual refresher required",
                    "Competency assessment": "Practical test with 5 mock cases of varying complexity; minimum score 80%",
                },
            },
        ],
        "regulatory_references": [
            "GVP Module VI Rev 2",
            "21 CFR 314.80",
            "ICH E2D",
        ],
        "related_items": [
            "sop/PV-SOP-002",
            "kpi/case-processing-time",
            "regulation/gvp-module-vi",
        ],
    },
    ("sop", "PV-SOP-002"): {
        "title": "PV-SOP-002 — ICSR Data Entry and Medical Review",
        "summary": (
            "Defines the process for complete ICSR data entry, MedDRA coding, medical review, "
            "causality assessment, and quality control prior to regulatory submission."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure accurate, complete, and medically reviewed ICSRs that meet regulatory "
                    "standards for E2B(R3) transmission and internal quality requirements."
                ),
            },
            {
                "heading": "Scope",
                "detail_type": "text",
                "content": (
                    "Applies to case processors, MedDRA coders, medical reviewers (physicians/pharmacists), "
                    "and QC reviewers involved in the case processing workflow."
                ),
            },
            {
                "heading": "Regulatory Basis",
                "detail_type": "text",
                "content": "GVP Module VI, ICH E2B(R3), MedDRA MSSO Coding Guidelines, ICH E2A",
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Complete data entry of all available information into safety database fields",
                    "2. Code adverse events using current MedDRA version (LLT → PT → HLT → HLGT → SOC)",
                    "3. Code products using WHODrug dictionary (for suspect, concomitant, and interacting drugs)",
                    "4. Perform medical review: assess seriousness criteria, expectedness against RSI, causality (WHO-UMC or Naranjo scale)",
                    "5. Generate case narrative — structured summary of patient, medical history, drug exposure, event details, and outcome",
                    "6. QC review: verify completeness, coding accuracy, narrative quality, regulatory classification",
                    "7. Approve for submission or return for rework with documented feedback",
                    "8. Generate E2B(R3) and transmit to applicable authorities",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon MedDRA version update or regulatory change",
                    "Training requirement": "Role-specific: coders (MedDRA certification), medical reviewers (causality assessment training), QC (completeness checklist training)",
                    "Competency assessment": "Annual inter-rater reliability assessment for MedDRA coding; medical review calibration exercise quarterly",
                },
            },
        ],
        "regulatory_references": [
            "GVP Module VI Rev 2",
            "ICH E2B(R3)",
            "ICH E2A",
            "MedDRA Introductory Guide",
        ],
        "related_items": [
            "sop/PV-SOP-001",
            "sop/PV-SOP-003",
            "kpi/case-processing-time",
            "kpi/e2b-acceptance",
        ],
    },
    ("sop", "PV-SOP-003"): {
        "title": "PV-SOP-003 — Expedited and Periodic Regulatory Reporting",
        "summary": (
            "Defines the process for preparing and submitting expedited (7-day, 15-day) and "
            "periodic (PADER, PSUR/PBRER, DSUR) safety reports to regulatory authorities worldwide."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure all expedited and periodic regulatory safety reports are prepared, "
                    "reviewed, approved, and submitted in compliance with applicable regulatory "
                    "requirements and within mandated timelines."
                ),
            },
            {
                "heading": "Scope",
                "detail_type": "text",
                "content": (
                    "Applies to regulatory affairs, pharmacovigilance, medical safety, and quality "
                    "assurance personnel involved in report preparation, review, and submission."
                ),
            },
            {
                "heading": "Regulatory Basis",
                "detail_type": "text",
                "content": "21 CFR 312.32, 21 CFR 314.80, GVP Module VI, GVP Module VII, ICH E2F, ICH E2C(R2), ICH E2D",
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Maintain reporting calendar with all regulatory deadlines by product and market",
                    "2. For expedited reports: confirm regulatory classification, prepare E2B(R3), medical officer sign-off, transmit within timeline",
                    "3. For periodic reports: initiate project plan 90 days before DLP, coordinate cross-functional data collection, draft/review/approve per timeline",
                    "4. Track submission confirmations and acknowledgements; re-submit rejected transmissions",
                    "5. Maintain submission log with case/report ID, authority, submission date, acknowledgement status",
                    "6. Escalate late or at-risk submissions to Head of PV immediately",
                    "7. Document any deviations from timeline with root cause analysis",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon new market entry or regulatory change",
                    "Training requirement": "Market-specific reporting requirements training; periodic report authoring training for writers",
                    "Competency assessment": "Mock submission exercise annually; regulatory intelligence update quarterly",
                },
            },
        ],
        "regulatory_references": [
            "21 CFR 312.32 / 314.80",
            "GVP Module VI / VII",
            "ICH E2F / E2C(R2)",
        ],
        "related_items": [
            "sop/PV-SOP-002",
            "kpi/serious-15-day",
            "kpi/7-day-compliance",
            "report/dsur",
            "report/pbrer",
        ],
    },
    ("sop", "PV-SOP-004"): {
        "title": "PV-SOP-004 — Signal Detection and Management",
        "summary": (
            "Defines the process for routine signal detection, validation, prioritization, "
            "assessment, and escalation in compliance with GVP Module IX."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure systematic, timely, and documented signal detection and management "
                    "activities for all products in the pharmacovigilance portfolio, using both "
                    "quantitative (statistical) and qualitative (clinical) methods."
                ),
            },
            {
                "heading": "Scope",
                "detail_type": "text",
                "content": (
                    "Applies to signal management team (epidemiologists, medical safety officers, "
                    "biostatisticians), QPPV/Deputy QPPV, Safety Management Team members, and "
                    "any contracted signal detection service providers."
                ),
            },
            {
                "heading": "Regulatory Basis",
                "detail_type": "text",
                "content": "GVP Module IX Rev 1, GVP Module IX Addendum I, ICH E2E, 21 CFR 314.80",
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Define signal detection schedule per product (monthly for high-volume, quarterly for others)",
                    "2. Extract data from safety database, EudraVigilance, FAERS, and literature",
                    "3. Run statistical disproportionality analyses (PRR, ROR, EBGM/IC as applicable)",
                    "4. Clinical review of statistical alerts and targeted medical review of selected SOC/PTs",
                    "5. Validate signals: confirm new information, rule out confounders/reporting artifacts",
                    "6. Prioritize validated signals using prioritization matrix (severity, frequency, public health impact)",
                    "7. Conduct detailed signal assessment for prioritized signals — present at Safety Management Team",
                    "8. Recommend and track actions (labeling update, RMP update, DHPC, additional study, etc.)",
                    "9. Document all activities in signal tracking tool; update signal status at each governance meeting",
                    "10. Close signals with documented rationale when actions complete and effectiveness verified",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon change in detection methodology or regulatory guidance",
                    "Training requirement": "Signal detection methodology, disproportionality analysis interpretation, signal management tools",
                    "Competency assessment": "Participation in at least 2 signal evaluation cycles before independent work; annual calibration exercise",
                },
            },
        ],
        "regulatory_references": [
            "GVP Module IX Rev 1",
            "GVP Module IX Addendum I",
            "ICH E2E",
        ],
        "related_items": [
            "regulation/gvp-module-ix",
            "kpi/signal-detection-cycle",
            "sop/PV-SOP-003",
        ],
    },
    ("sop", "PV-SOP-005"): {
        "title": "PV-SOP-005 — PV Training and Competency Management",
        "summary": (
            "Defines the process for identifying, delivering, tracking, and assessing "
            "pharmacovigilance training and competency for all personnel with PV responsibilities."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure all personnel performing pharmacovigilance activities are adequately "
                    "trained, demonstrate competency, and maintain current knowledge of applicable "
                    "regulations, SOPs, and safety database systems."
                ),
            },
            {
                "heading": "Scope",
                "detail_type": "text",
                "content": (
                    "Applies to all internal pharmacovigilance staff, medical safety officers, "
                    "contracted PV personnel, business partner/CRO staff performing delegated PV "
                    "activities, and non-PV staff with AE reporting obligations (medical information, "
                    "clinical operations, sales/marketing, medical affairs)."
                ),
            },
            {
                "heading": "Regulatory Basis",
                "detail_type": "text",
                "content": "GVP Module I, 21 CFR 211.25, ICH E6(R2) Section 2.8, EU GMP Annex 1",
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Define role-based training curriculum for each PV function (intake, processing, medical review, signal, reporting, QPPV)",
                    "2. Assign training within LMS within 5 business days of role assignment",
                    "3. Complete initial training within 30 calendar days — no independent case work until training complete",
                    "4. Deliver product-specific training within 15 days of new product assignment",
                    "5. Schedule and deliver annual refresher training (regulatory updates, SOP changes, lessons learned)",
                    "6. Conduct competency assessments (knowledge tests, practical exercises, observed work)",
                    "7. Track training compliance monthly; report at governance meetings",
                    "8. Remediate non-compliance: escalation to line manager at 14 days overdue, to Head of PV at 30 days",
                    "9. Maintain training records for inspection readiness (minimum 5 years after role change)",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon significant organisational/regulatory change",
                    "Training requirement": "Training administrators must complete LMS administration course and train-the-trainer programme",
                    "Competency assessment": "Self-referential: training team competency is assessed by QA during internal PV audits",
                },
            },
        ],
        "regulatory_references": [
            "GVP Module I",
            "21 CFR 211.25",
            "ICH E6(R2)",
        ],
        "related_items": [
            "kpi/training-compliance",
            "sop/PV-SOP-001",
            "sop/PV-SOP-002",
        ],
    },

    # ── REGULATIONS (additional) ──────────────────────────────────────────

    ("regulation", "21-cfr-312-33"): {
        "title": "21 CFR 312.33 — IND Annual Reports",
        "summary": (
            "Requires IND sponsors to submit annual reports within 60 days of the "
            "IND anniversary date. Covers clinical trial progress, safety data summary, "
            "protocol amendments, chemistry updates, and an overall investigational plan."
        ),
        "sections": [
            {
                "heading": "Required Content",
                "detail_type": "key_value_pairs",
                "content": {
                    "Individual study information": "Title, protocol number, enrollment status, study completion date, safety/efficacy data summary",
                    "Summary of safety data": "Narrative summary of the most frequent and most serious adverse events by body system",
                    "IB revisions": "A summary of any significant revisions to the Investigator's Brochure during the reporting period",
                    "Protocol modifications": "Description of significant protocol amendments and reasons",
                    "Phase of development": "Current phase(s) and overall development plan for the next year",
                    "Foreign marketing developments": "Approval, withdrawal, or suspension actions in foreign countries",
                },
            },
            {
                "heading": "DSUR as Alternative",
                "detail_type": "text",
                "content": (
                    "FDA accepts the ICH E2F Development Safety Update Report (DSUR) in lieu of "
                    "the annual report required under 312.33. If a DSUR is submitted, it must "
                    "contain any additional information required by 312.33 not already covered."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR 312.33 — Annual Reports",
            "ICH E2F — Development Safety Update Report",
        ],
        "related_items": [
            "regulation/21-cfr-312-32",
            "report/dsur",
        ],
    },
    ("regulation", "21-cfr-part-11"): {
        "title": "21 CFR Part 11 — Electronic Records; Electronic Signatures",
        "summary": (
            "FDA regulation establishing criteria for acceptance of electronic records "
            "and electronic signatures as equivalent to paper records and handwritten "
            "signatures. Applies to all FDA-regulated activities including pharmacovigilance."
        ),
        "sections": [
            {
                "heading": "Key Requirements",
                "detail_type": "key_value_pairs",
                "content": {
                    "Validation": "Systems must be validated to ensure accuracy, reliability, and consistent intended performance",
                    "Audit trails": "Secure, computer-generated, time-stamped audit trails for record creation, modification, or deletion",
                    "Access controls": "Procedures and controls to limit system access to authorised individuals",
                    "Electronic signatures": "Must be unique to one individual, verified before use, and linked to the signed record",
                    "Authority checks": "System must verify that persons signing have the authority to do so",
                },
            },
            {
                "heading": "PV System Impact",
                "detail_type": "text",
                "content": (
                    "Safety databases, E2B transmission systems, signal detection tools, and "
                    "document management systems used in pharmacovigilance must comply with "
                    "Part 11. This includes audit trail requirements for ICSR data entry, "
                    "electronic signatures for medical review approval, and validated workflows."
                ),
            },
        ],
        "regulatory_references": [
            "21 CFR Part 11 — Electronic Records; Electronic Signatures",
            "FDA Guidance: Scope and Application (2003)",
            "EU GMP Annex 11 — Computerised Systems",
        ],
        "related_items": [
            "regulation/21-cfr-312-32",
            "sop/PV-SOP-002",
        ],
    },
    ("regulation", "gvp-module-i"): {
        "title": "GVP Module I — Pharmacovigilance Systems and Their Quality Systems",
        "summary": (
            "EMA guideline defining the requirements for the pharmacovigilance system, "
            "including the QPPV role, PSMF, quality system, and organisational structure "
            "needed to fulfil EU pharmacovigilance obligations."
        ),
        "sections": [
            {
                "heading": "Key Elements",
                "detail_type": "key_value_pairs",
                "content": {
                    "QPPV": "Qualified Person for Pharmacovigilance — single named individual residing in the EU responsible for PV system oversight",
                    "PSMF": "Pharmacovigilance System Master File — documents the PV system; must be available for inspection within 7 days",
                    "Quality system": "Must cover SOPs, training, auditing, CAPA, record management, and compliance monitoring",
                    "Outsourcing": "MAH retains responsibility even when PV activities are delegated to third parties",
                },
            },
            {
                "heading": "Prosinertimib Compliance",
                "detail_type": "text",
                "content": (
                    "The Prosinertimib pharmacovigilance system is maintained per GVP Module I "
                    "with a designated QPPV, a current PSMF, and a documented quality management "
                    "system covering all PV processes from ICSR intake through signal management."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module I Rev 2 — Pharmacovigilance Systems and Their Quality Systems",
            "Directive 2001/83/EC Article 104",
            "Regulation (EU) No 1235/2010",
        ],
        "related_items": [
            "regulation/gvp-module-ii",
            "sop/PV-SOP-001",
        ],
    },
    ("regulation", "gvp-module-ii"): {
        "title": "GVP Module II — Pharmacovigilance System Master File",
        "summary": (
            "EMA guideline on the content, format, and maintenance of the Pharmacovigilance "
            "System Master File (PSMF). The PSMF is a detailed description of the PV system "
            "used by the MAH and must be kept at the QPPV's disposal."
        ),
        "sections": [
            {
                "heading": "PSMF Content Requirements",
                "detail_type": "text",
                "content": [
                    "QPPV contact details, qualifications, and CV",
                    "Organisational structure of the MAH's PV system",
                    "Data sources and processing workflows",
                    "Computerised systems and databases used for PV activities",
                    "Quality management system description including SOPs, training, and auditing",
                    "Contractual arrangements with third parties performing PV tasks",
                    "List of products covered by the PV system with regulatory status",
                    "Performance indicators and compliance monitoring results",
                ],
            },
            {
                "heading": "Maintenance",
                "detail_type": "text",
                "content": (
                    "The PSMF must be kept continuously up to date and available for "
                    "inspection. The location is recorded in the EU PV database. Logbook "
                    "entries must document all significant changes. PSMF must be submitted "
                    "to competent authorities within 7 days of a request."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module II Rev 2 — Pharmacovigilance System Master File",
            "Commission Implementing Regulation (EU) No 520/2012",
        ],
        "related_items": [
            "regulation/gvp-module-i",
            "audit/gvp-internal-2026",
        ],
    },
    ("regulation", "gvp-module-v"): {
        "title": "GVP Module V — Risk Management Systems",
        "summary": (
            "EMA guideline on the EU Risk Management Plan (RMP) structure and content. "
            "Defines how to characterise the safety profile, plan pharmacovigilance "
            "activities, and implement risk minimisation measures."
        ),
        "sections": [
            {
                "heading": "RMP Structure",
                "detail_type": "text",
                "content": [
                    "Part I: Product overview",
                    "Part II: Safety specification (epidemiology, non-clinical, clinical trial exposure, populations not studied, post-authorisation experience)",
                    "Part III: Pharmacovigilance plan (routine and additional PV activities)",
                    "Part IV: Plans for post-authorisation efficacy studies",
                    "Part V: Risk minimisation measures (routine and additional)",
                    "Part VI: Summary of the RMP",
                    "Part VII: Annexes (including worldwide marketing status, synopsis of ongoing studies)",
                ],
            },
            {
                "heading": "Prosinertimib RMP Status",
                "detail_type": "text",
                "content": (
                    "The Prosinertimib RMP covers identified risks (ILD, hepatotoxicity, QT "
                    "prolongation, skin toxicity), potential risks (cardiac failure), and missing "
                    "information (long-term safety >2 years, renal impairment, paediatric use). "
                    "Additional risk minimisation includes prescriber education materials and "
                    "patient alert cards for ILD symptoms."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module V Rev 2 — Risk Management Systems",
            "EMA Guidance on Format of RMP in the EU",
        ],
        "related_items": [
            "kpi/rmp-implementation",
            "risk/ild",
        ],
    },
    ("regulation", "gvp-module-vii"): {
        "title": "GVP Module VII — Periodic Safety Update Report",
        "summary": (
            "EMA guideline on the EU-specific requirements for PSURs including "
            "format (ICH E2C(R2) PBRER), submission frequency per EURD list, and "
            "the PSUSA single assessment procedure by PRAC."
        ),
        "sections": [
            {
                "heading": "Key Requirements",
                "detail_type": "key_value_pairs",
                "content": {
                    "Format": "ICH E2C(R2) PBRER format is mandatory in the EU since 2012",
                    "Submission frequency": "Defined by the EURD list; typically 6-monthly for first 2 years, annual for 2 years, then 3-yearly",
                    "DLP and deadline": "DLP + 70 days (single substance) or DLP + 90 days (combination products)",
                    "Assessment": "PRAC conducts single assessment (PSUSA) for all products with same active substance",
                },
            },
            {
                "heading": "Prosinertimib PSUR Schedule",
                "detail_type": "text",
                "content": (
                    "Prosinertimib is currently on a 6-monthly PSUR cycle per the EURD list. "
                    "Next DLP: 2026-06-30. Submission deadline: 2026-09-08. PRAC rapporteur "
                    "assessment expected by Day 60, with PRAC recommendation at Day 120."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module VII Rev 1 — Periodic Safety Update Report",
            "ICH E2C(R2)",
            "EURD List (European Union Reference Dates)",
        ],
        "related_items": [
            "report/psur",
            "report/pbrer",
            "regulation/ich-e2c-r2",
        ],
    },
    ("regulation", "gvp-module-xv"): {
        "title": "GVP Module XV — Safety Communication",
        "summary": (
            "EMA guideline on safety communication tools including Direct Healthcare "
            "Professional Communications (DHPCs), public health communications, and "
            "coordination of safety messaging with national competent authorities."
        ),
        "sections": [
            {
                "heading": "Communication Tools",
                "detail_type": "key_value_pairs",
                "content": {
                    "DHPC": "Direct Healthcare Professional Communication — letter distributed to prescribers/pharmacists about important new safety information",
                    "Public communication": "Safety announcements for the general public via EMA website and press releases",
                    "SmPC/PIL updates": "Labeling changes reflecting new safety information — coordinated across EU",
                    "Risk communication plan": "Part of the RMP risk minimisation strategy; tested for effectiveness",
                },
            },
            {
                "heading": "Prosinertimib DHPCs Issued",
                "detail_type": "text",
                "content": (
                    "One DHPC issued for Prosinertimib regarding ILD risk and mandatory baseline "
                    "CT screening. Distributed to oncologists and pulmonologists in all EU member "
                    "states. Effectiveness survey planned at 6-month mark."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module XV Rev 1 — Safety Communication",
            "Directive 2001/83/EC Article 106a",
        ],
        "related_items": [
            "regulation/gvp-module-v",
            "risk/ild",
        ],
    },
    ("regulation", "gvp-module-xvi"): {
        "title": "GVP Module XVI — Risk Minimisation Measures: Selection of Tools and Effectiveness Indicators",
        "summary": (
            "EMA guideline on selecting, implementing, and evaluating additional risk "
            "minimisation measures (aRMMs) beyond routine measures. Covers educational "
            "materials, controlled access programmes, and effectiveness evaluation."
        ),
        "sections": [
            {
                "heading": "Types of Additional Risk Minimisation",
                "detail_type": "text",
                "content": [
                    "Educational materials for HCPs (prescriber guides, checklists)",
                    "Educational materials for patients (patient alert cards, brochures)",
                    "Controlled access programmes (restricted distribution, pregnancy prevention programmes)",
                    "Other tools (specific packaging, dosing devices, formulation restrictions)",
                ],
            },
            {
                "heading": "Effectiveness Evaluation",
                "detail_type": "text",
                "content": (
                    "MAHs must evaluate whether aRMMs achieve their objectives using process "
                    "indicators (e.g., distribution rates) and outcome indicators (e.g., knowledge "
                    "surveys, adherence to recommended monitoring). Evaluation plans and results "
                    "are included in the RMP and PSUR."
                ),
            },
        ],
        "regulatory_references": [
            "GVP Module XVI Rev 3 — Risk Minimisation Measures",
            "GVP Module V Rev 2 — Risk Management Systems",
        ],
        "related_items": [
            "regulation/gvp-module-v",
            "regulation/gvp-module-xv",
            "kpi/rems-compliance",
        ],
    },
    ("regulation", "ich-e2a"): {
        "title": "ICH E2A — Clinical Safety Data Management: Definitions and Standards for Expedited Reporting",
        "summary": (
            "Foundational ICH guideline defining terms (adverse event, adverse reaction, "
            "unexpected, serious) and establishing standards for expedited reporting of "
            "individual case safety reports from clinical trials."
        ),
        "sections": [
            {
                "heading": "Key Definitions",
                "detail_type": "key_value_pairs",
                "content": {
                    "Adverse Event (AE)": "Any untoward medical occurrence in a patient administered a pharmaceutical product; does not necessarily have a causal relationship",
                    "Adverse Drug Reaction (ADR)": "A response to a drug which is noxious and unintended, occurring at doses normally used (marketed products) or at any dose (pre-approval)",
                    "Serious": "Results in death, is life-threatening, requires hospitalisation, causes persistent disability, is a congenital anomaly, or is medically important",
                    "Unexpected": "Not consistent with applicable product information (IB for investigational, labeling for marketed)",
                },
            },
            {
                "heading": "Reporting Standards",
                "detail_type": "text",
                "content": (
                    "Sponsors must report to regulators all serious and unexpected adverse "
                    "reactions (SUSARs) from clinical trials within 15 days (7 days for fatal "
                    "or life-threatening). Reports should include minimum information: identifiable "
                    "patient, identifiable reporter, suspect drug, and adverse event."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2A — Clinical Safety Data Management (1994)",
            "21 CFR 312.32",
        ],
        "related_items": [
            "regulation/ich-e2b-r3",
            "regulation/ich-e2d",
            "regulation/21-cfr-312-32",
        ],
    },
    ("regulation", "ich-e2b-r3"): {
        "title": "ICH E2B(R3) — Electronic Transmission of Individual Case Safety Reports",
        "summary": (
            "ICH guideline defining the data elements and electronic message format for "
            "ICSR transmission between regulatory authorities and pharmaceutical companies. "
            "Uses the HL7/ICH ICSR standard (XML-based)."
        ),
        "sections": [
            {
                "heading": "Key Features",
                "detail_type": "key_value_pairs",
                "content": {
                    "Format": "HL7 v3-based XML (replaced E2B(R2) SGML format)",
                    "Data elements": "~250 fields covering patient demographics, drug information, reaction details, reporter info, and narrative",
                    "Transmission": "Gateway-to-gateway electronic transmission to EudraVigilance, FDA ESG, PMDA",
                    "MedDRA coding": "Adverse events must be coded using the current MedDRA version at the Lowest Level Term (LLT)",
                    "Acknowledgements": "ACK messages confirm successful receipt and processing by the receiving authority",
                },
            },
            {
                "heading": "Implementation",
                "detail_type": "text",
                "content": (
                    "All major regulatory authorities now require E2B(R3) format. The transition "
                    "from R2 to R3 introduced expanded fields for patient medical history, parent-"
                    "child reports, and improved drug identification. Safety database systems must "
                    "be validated for R3 compliance."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2B(R3) — Electronic Transmission of ICSRs (2013)",
            "ICH M2 — Electronic Standards for Transmission of Regulatory Information",
        ],
        "related_items": [
            "regulation/ich-e2a",
            "kpi/e2b-acceptance",
            "sop/PV-SOP-002",
        ],
    },
    ("regulation", "ich-e2d"): {
        "title": "ICH E2D — Post-Approval Safety Data Management",
        "summary": (
            "ICH guideline on safety data management for marketed products including "
            "expedited and periodic reporting of post-marketing adverse reactions, "
            "stimulated reports, and literature monitoring."
        ),
        "sections": [
            {
                "heading": "Scope and Reporting",
                "detail_type": "key_value_pairs",
                "content": {
                    "Expedited reports": "Serious unexpected ADRs: 15 calendar days from Day 0",
                    "Solicited reports": "Reports from organised data collection systems (registries, PSPs) — apply regulatory reporting criteria",
                    "Literature monitoring": "MAH must monitor worldwide medical literature for ICSRs — Day 0 = date of publication awareness",
                    "Consumer reports": "Reports from patients/consumers should be handled the same as HCP reports for regulatory reporting",
                },
            },
            {
                "heading": "Day 0 Rules",
                "detail_type": "text",
                "content": (
                    "Day 0 is the date the MAH first becomes aware of information containing "
                    "the minimum criteria for a valid case. For clinical trials, Day 0 is the "
                    "date the sponsor first receives the information. For post-marketing, it is "
                    "the date any employee of the MAH's PV system first becomes aware."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2D — Post-Approval Safety Data Management (2003)",
        ],
        "related_items": [
            "regulation/ich-e2a",
            "regulation/21-cfr-314-80",
            "kpi/serious-15-day",
        ],
    },
    ("regulation", "ich-e2e"): {
        "title": "ICH E2E — Pharmacovigilance Planning",
        "summary": (
            "ICH guideline on pharmacovigilance planning at the time of marketing "
            "authorisation application. Defines the safety specification, pharmacovigilance "
            "plan, and how to identify areas requiring further investigation."
        ),
        "sections": [
            {
                "heading": "Safety Specification Components",
                "detail_type": "text",
                "content": [
                    "Non-clinical safety findings relevant to human use",
                    "Clinical trial safety findings: common and serious AEs, identified risks",
                    "Populations not studied in clinical trials (e.g., paediatric, elderly, renal/hepatic impairment)",
                    "Identified risks and potential risks",
                    "Summary of the safety concerns requiring further investigation",
                ],
            },
            {
                "heading": "Pharmacovigilance Plan",
                "detail_type": "text",
                "content": (
                    "The PV plan describes routine and additional activities to characterise "
                    "risks, identify new risks, and increase knowledge about the safety profile. "
                    "Additional activities may include targeted follow-up questionnaires, PASS "
                    "(post-authorisation safety studies), registries, or targeted clinical trials. "
                    "The plan is updated as new data become available."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2E — Pharmacovigilance Planning (2004)",
            "GVP Module V — Risk Management Systems",
        ],
        "related_items": [
            "regulation/gvp-module-v",
            "regulation/ich-e2c-r2",
        ],
    },
    ("regulation", "ich-e2f"): {
        "title": "ICH E2F — Development Safety Update Report (DSUR)",
        "summary": (
            "ICH guideline defining the format, content, and timing of the DSUR — "
            "an annual safety report for investigational drugs. Provides a comprehensive "
            "annual safety review from the DIBD covering all clinical development."
        ),
        "sections": [
            {
                "heading": "DSUR Timing",
                "detail_type": "key_value_pairs",
                "content": {
                    "Reference date": "Development International Birth Date (DIBD) — date of first approval for clinical investigation anywhere in the world",
                    "Reporting period": "Annual — from DIBD anniversary to next DIBD anniversary",
                    "Submission deadline": "Within 60 calendar days of the data lock point",
                    "Recipients": "All regulatory authorities where IND/CTA is active",
                },
            },
            {
                "heading": "Key Sections",
                "detail_type": "text",
                "content": (
                    "The DSUR contains 20 sections covering: study inventory, exposure, line "
                    "listings of SAEs, significant safety findings, signal overview, overall "
                    "safety assessment, summary of important risks, and benefit-risk conclusions "
                    "for continued development. It effectively bridges ICH E2A (expedited) and "
                    "ICH E2C (periodic marketed product) reporting."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E2F — Development Safety Update Report (2010)",
            "21 CFR 312.33 (FDA accepts DSUR as annual IND report)",
        ],
        "related_items": [
            "report/dsur",
            "regulation/21-cfr-312-33",
        ],
    },
    ("regulation", "ich-e6-r3"): {
        "title": "ICH E6(R3) — Good Clinical Practice",
        "summary": (
            "The updated ICH GCP guideline (R3, 2023) providing a principles-based framework "
            "for designing, conducting, recording, and reporting clinical trials. Introduces "
            "risk-based quality management and modernised approaches to data governance."
        ),
        "sections": [
            {
                "heading": "Key Changes from R2",
                "detail_type": "text",
                "content": [
                    "Risk-based quality management as a foundational requirement",
                    "Annex 1: interventional clinical trials; Annex 2: non-traditional designs and decentralised elements",
                    "Technology-neutral approach — accommodates digital health tools, eConsent, remote monitoring",
                    "Enhanced focus on participant safety, rights, and wellbeing",
                    "Proportionate approach to monitoring based on risk assessment",
                    "Explicit requirements for data governance and integrity across all data sources",
                ],
            },
            {
                "heading": "Safety Reporting Under GCP",
                "detail_type": "text",
                "content": (
                    "Investigators must report all SAEs to the sponsor immediately (within 24 hours). "
                    "Sponsors must report SUSARs to regulators and ethics committees per ICH E2A "
                    "timelines. Unblinding procedures must be defined and documented. Annual safety "
                    "reports (DSURs) must be provided to investigators, IRBs, and regulators."
                ),
            },
        ],
        "regulatory_references": [
            "ICH E6(R3) — Good Clinical Practice (2023)",
            "21 CFR Parts 50, 56, 312",
            "EU Clinical Trials Regulation (EU) No 536/2014",
        ],
        "related_items": [
            "regulation/ich-e2a",
            "trial/PROSPER-1",
        ],
    },
    ("regulation", "ich-m1-meddra"): {
        "title": "ICH M1 — MedDRA (Medical Dictionary for Regulatory Activities)",
        "summary": (
            "MedDRA is the ICH-maintained international medical terminology used for "
            "regulatory communication and evaluation of safety data. Five hierarchical "
            "levels from System Organ Class (SOC) to Lowest Level Term (LLT)."
        ),
        "sections": [
            {
                "heading": "Hierarchy",
                "detail_type": "key_value_pairs",
                "content": {
                    "SOC (System Organ Class)": "Broadest grouping (27 SOCs), e.g., 'Respiratory, thoracic and mediastinal disorders'",
                    "HLGT (High Level Group Term)": "Grouping of HLTs within an SOC",
                    "HLT (High Level Term)": "Grouping of PTs by anatomy, pathology, physiology, or mechanism",
                    "PT (Preferred Term)": "Distinct descriptor for a symptom, sign, disease, or procedure (~28,000 PTs)",
                    "LLT (Lowest Level Term)": "Most specific level — synonyms and sub-concepts linked to a PT (~85,000 LLTs)",
                },
            },
            {
                "heading": "Use in Pharmacovigilance",
                "detail_type": "text",
                "content": (
                    "MedDRA coding is mandatory for E2B(R3) ICSR submissions. Adverse events "
                    "are coded at the LLT level. Signal detection uses Standardised MedDRA "
                    "Queries (SMQs) — pre-defined groupings of PTs for detecting safety signals "
                    "for specific medical conditions. MedDRA is updated twice yearly (March/September)."
                ),
            },
        ],
        "regulatory_references": [
            "ICH M1 — MedDRA",
            "MedDRA Introductory Guide (MSSO)",
            "MedDRA SMQ Introductory Guide",
        ],
        "related_items": [
            "regulation/ich-e2b-r3",
            "sop/PV-SOP-002",
        ],
    },

    # ── KPIs (additional) ─────────────────────────────────────────────────

    ("kpi", "aggregate-submissions"): {
        "title": "Aggregate Report Submission Compliance",
        "summary": (
            "Tracks on-time submission of aggregate safety reports (DSUR, PBRER/PSUR, "
            "PADER) to all applicable regulatory authorities. Target 100% on-time."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Reports submitted on or before deadline / Total reports due) x 100",
                    "Target": "100% on-time submission",
                    "Report types tracked": "DSUR, PBRER/PSUR, PADER, Annual IND reports",
                    "Measurement frequency": "Monthly review at PV governance meeting",
                },
            },
        ],
        "regulatory_references": [
            "ICH E2F (DSUR)", "ICH E2C(R2) (PBRER)", "21 CFR 314.81 (PADER)",
        ],
        "related_items": ["report/dsur", "report/pbrer"],
    },
    ("kpi", "benefit-risk"): {
        "title": "Benefit-Risk Assessment Currency",
        "summary": (
            "Measures whether benefit-risk evaluations are current and documented "
            "for all approved indications. Target: all evaluations updated within "
            "the last PBRER cycle."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Indications with current B-R evaluation / Total approved indications) x 100",
                    "Target": "100%",
                    "Trigger for update": "New signal, PSUR cycle, regulatory request, or significant new data",
                },
            },
        ],
        "regulatory_references": ["ICH E2C(R2) Section 21", "GVP Module VII"],
        "related_items": ["report/pbrer", "regulation/ich-e2c-r2"],
    },
    ("kpi", "capa-closure"): {
        "title": "PV CAPA On-Time Closure",
        "summary": (
            "Percentage of pharmacovigilance CAPAs closed within their assigned "
            "target date. Distinct from the broader capa-closure-rate KPI by "
            "focusing on PV-specific corrective actions only."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(PV CAPAs closed on time / Total PV CAPAs due) x 100",
                    "Target": ">= 90%",
                    "Scope": "CAPAs originating from PV audits, inspections, and deviation reports",
                },
            },
        ],
        "regulatory_references": ["GVP Module I", "ICH Q10"],
        "related_items": ["kpi/capa-closure-rate", "capa/CAPA-2026-001"],
    },
    ("kpi", "data-accuracy"): {
        "title": "ICSR Data Accuracy Rate",
        "summary": (
            "Percentage of ICSRs passing QC review without rework. Measures the "
            "accuracy of data entry, MedDRA coding, and medical review quality."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(ICSRs passing QC on first review / Total ICSRs reviewed) x 100",
                    "Target": ">= 95% first-pass accuracy",
                    "Error categories": "Coding errors, narrative deficiencies, missing fields, causality misclassification",
                },
            },
        ],
        "regulatory_references": ["GVP Module VI", "ICH E2B(R3)"],
        "related_items": ["sop/PV-SOP-002", "kpi/e2b-acceptance"],
    },
    ("kpi", "ev-reporting"): {
        "title": "EudraVigilance Reporting Compliance",
        "summary": (
            "Compliance rate for ICSR submissions to EudraVigilance within "
            "required timelines. Covers both expedited and non-expedited reports."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(ICSRs submitted to EV on time / Total ICSRs due for EV) x 100",
                    "Target": ">= 98%",
                    "Timelines": "15 days (serious EEA), 90 days (non-serious EEA)",
                },
            },
        ],
        "regulatory_references": ["GVP Module VI", "Commission Implementing Regulation (EU) No 520/2012"],
        "related_items": ["regulation/gvp-module-vi", "kpi/serious-15-day"],
    },
    ("kpi", "inspection-readiness"): {
        "title": "Inspection Readiness Score",
        "summary": (
            "Composite score measuring preparedness for regulatory PV inspections. "
            "Assessed quarterly against a checklist covering PSMF, SOPs, training, "
            "CAPA status, and system access."
        ),
        "sections": [
            {
                "heading": "Scoring Components",
                "detail_type": "key_value_pairs",
                "content": {
                    "PSMF currency": "Is the PSMF up to date and available within 7 days? (20 pts)",
                    "SOP currency": "Are all PV SOPs current and approved? (20 pts)",
                    "Training compliance": "Are all PV staff trained on current SOPs? (20 pts)",
                    "CAPA status": "Are all CAPAs on track for on-time closure? (20 pts)",
                    "Mock inspection": "Has a mock inspection been conducted in the last 12 months? (20 pts)",
                },
            },
        ],
        "regulatory_references": ["GVP Module III — Pharmacovigilance Inspections"],
        "related_items": ["audit/gvp-internal-2026", "kpi/sop-currency", "kpi/training-compliance"],
    },
    ("kpi", "labeling-alignment"): {
        "title": "Labeling Safety Alignment",
        "summary": (
            "Measures alignment between the Company Core Safety Information (CCSI) "
            "and local labels across all markets. Target: all local labels updated "
            "within 60 days of CCSI change."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Markets with labels aligned to current CCSI / Total markets) x 100",
                    "Target": "100% alignment within 60 days of CCSI update",
                    "Tracking": "Label change tracker updated after each safety variation or PI update",
                },
            },
        ],
        "regulatory_references": ["GVP Module XVI", "ICH E2C(R2)"],
        "related_items": ["regulation/gvp-module-xv", "kpi/benefit-risk"],
    },
    ("kpi", "open-signals"): {
        "title": "Open Signal Ageing",
        "summary": (
            "Tracks the number and age of open (unresolved) safety signals. "
            "Target: no signal open longer than 12 months without documented "
            "justification and action plan."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Measure": "Count of open signals by age band (0-3mo, 3-6mo, 6-12mo, >12mo)",
                    "Target": "Zero signals >12 months without documented action plan",
                    "Escalation": "Signals open >6 months reviewed at Safety Governance Board",
                },
            },
        ],
        "regulatory_references": ["GVP Module IX — Signal Management"],
        "related_items": ["signal/SIG-2026-001", "kpi/signal-closure-rate"],
    },
    ("kpi", "pm-commitments"): {
        "title": "Post-Marketing Commitment Tracking",
        "summary": (
            "Tracks status and on-time delivery of post-marketing commitments (PMCs) "
            "and post-marketing requirements (PMRs) from regulatory authorities."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(PMCs/PMRs on schedule / Total active PMCs/PMRs) x 100",
                    "Target": "100% on schedule",
                    "FDA reporting": "PMC/PMR status reported annually to FDA per FDAAA Section 505(o)(3)(E)",
                },
            },
        ],
        "regulatory_references": ["FDAAA 2007 Section 505(o)", "21 CFR 314.81"],
        "related_items": ["trial/PROSPER-1", "regulation/21-cfr-314-80"],
    },
    ("kpi", "rems-compliance"): {
        "title": "REMS Compliance Rate",
        "summary": (
            "Compliance rate for Risk Evaluation and Mitigation Strategy (REMS) "
            "requirements where applicable. Tracks adherence to ETASU, medication "
            "guides, and communication plans."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Measure": "Compliance with all REMS elements per FDA-approved REMS",
                    "Target": "100% compliance with ETASU and other REMS elements",
                    "Assessment": "REMS assessment submitted to FDA per approved schedule",
                },
            },
        ],
        "regulatory_references": ["FDCA Section 505-1", "FDA REMS Guidance"],
        "related_items": ["regulation/gvp-module-xvi", "market/us"],
    },
    ("kpi", "rmp-implementation"): {
        "title": "Risk Management Plan Implementation Status",
        "summary": (
            "Tracks implementation of all pharmacovigilance and risk minimisation "
            "activities specified in the EU Risk Management Plan."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(RMP activities on schedule / Total RMP activities) x 100",
                    "Target": "100% on schedule",
                    "Activities tracked": "Additional PV activities, PASS studies, educational materials, effectiveness surveys",
                },
            },
        ],
        "regulatory_references": ["GVP Module V Rev 2", "GVP Module XVI"],
        "related_items": ["regulation/gvp-module-v", "kpi/rems-compliance"],
    },
    ("kpi", "sdea-reporting"): {
        "title": "SDEA (Solicited/Stimulated) Reporting Compliance",
        "summary": (
            "Tracks compliance for reporting of solicited adverse events from "
            "patient support programmes, market research, and disease registries "
            "per ICH E2D standards."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Solicited reports processed on time / Total solicited reports) x 100",
                    "Target": ">= 95%",
                    "Sources": "Patient support programmes, surveys, registries, social media monitoring",
                },
            },
        ],
        "regulatory_references": ["ICH E2D", "GVP Module VI"],
        "related_items": ["regulation/ich-e2d", "sop/PV-SOP-001"],
    },
    ("kpi", "serious-7-day"): {
        "title": "7-Day Fatal/Life-Threatening Reporting Rate",
        "summary": (
            "Compliance rate for 7-day reporting of fatal or life-threatening "
            "unexpected suspected adverse reactions under IND. Target 100%."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(7-day reports submitted on time / Total 7-day reports due) x 100",
                    "Target": "100% — zero tolerance",
                    "Scope": "Fatal or life-threatening unexpected SUSARs from clinical trials",
                },
            },
        ],
        "regulatory_references": ["21 CFR 312.32(c)(2)"],
        "related_items": ["kpi/7-day-compliance", "regulation/21-cfr-312-32"],
    },
    ("kpi", "signal-closure-rate"): {
        "title": "Signal Closure Rate",
        "summary": (
            "Percentage of validated signals closed (concluded with a final "
            "assessment) within 12 months of detection."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Formula": "(Signals closed within 12 months / Total signals validated) x 100",
                    "Target": ">= 80% closed within 12 months",
                    "Exceptions": "Complex signals requiring additional studies may exceed 12 months with documented justification",
                },
            },
        ],
        "regulatory_references": ["GVP Module IX — Signal Management"],
        "related_items": ["kpi/open-signals", "kpi/signal-eval-timeliness"],
    },
    ("kpi", "signal-eval-timeliness"): {
        "title": "Signal Evaluation Timeliness",
        "summary": (
            "Measures whether signal evaluation activities (validation, prioritisation, "
            "assessment) are completed within defined timelines per GVP Module IX."
        ),
        "sections": [
            {
                "heading": "Metric Definition",
                "detail_type": "key_value_pairs",
                "content": {
                    "Validation": "Within 30 days of signal detection",
                    "Prioritisation": "Within 15 days of validation",
                    "Assessment initiation": "Within 30 days of prioritisation",
                    "Target": ">= 90% of signals meeting each milestone on time",
                },
            },
        ],
        "regulatory_references": ["GVP Module IX Rev 1"],
        "related_items": ["kpi/signal-closure-rate", "kpi/signal-detection-cycle"],
    },

    # ── AUDITS ────────────────────────────────────────────────────────────

    ("audit", "gcp-mhra-2026"): {
        "title": "GCP Inspection — MHRA (2026)",
        "summary": (
            "Scheduled MHRA GCP inspection of the Prosinertimib PROSPER-1 trial site "
            "in the UK. Focused on informed consent, source data verification, SAE "
            "reporting compliance, and investigator oversight."
        ),
        "sections": [
            {
                "heading": "Inspection Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Authority": "MHRA (Medicines and Healthcare products Regulatory Agency)",
                    "Type": "Routine GCP inspection",
                    "Scope": "PROSPER-1 Phase III trial — UK investigator sites",
                    "Scheduled date": "2026-06-15 to 2026-06-19",
                    "Status": "Preparation in progress",
                },
            },
            {
                "heading": "Key Focus Areas",
                "detail_type": "text",
                "content": [
                    "Informed consent process and documentation",
                    "Source data verification and data integrity",
                    "SAE/SUSAR reporting timeliness and completeness",
                    "Investigator oversight and delegation logs",
                    "IMP accountability and storage",
                ],
            },
        ],
        "regulatory_references": ["ICH E6(R3)", "UK SI 2004/1031 (Clinical Trials Regulations)"],
        "related_items": ["trial/PROSPER-1", "regulation/ich-e6-r3"],
    },
    ("audit", "gvp-ema-2025"): {
        "title": "GVP Inspection — EMA/NCA (2025)",
        "summary": (
            "Completed EMA-triggered GVP inspection conducted by the Dutch MEB as "
            "lead authority. Covered pharmacovigilance system, signal management, "
            "PSUR process, and QPPV oversight. Outcome: satisfactory with 2 minor findings."
        ),
        "sections": [
            {
                "heading": "Inspection Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Authority": "MEB (Netherlands) on behalf of EMA",
                    "Type": "Routine GVP inspection",
                    "Dates": "2025-09-22 to 2025-09-26",
                    "Outcome": "Satisfactory — 2 minor findings, 0 major, 0 critical",
                    "CAPA deadline": "2026-01-15 (completed)",
                },
            },
            {
                "heading": "Findings",
                "detail_type": "text",
                "content": [
                    "Minor: PSMF logbook entry for vendor change was delayed by 15 days",
                    "Minor: One SOP (PV-SOP-004) was 3 weeks past scheduled review date at time of inspection",
                ],
            },
        ],
        "regulatory_references": ["GVP Module III — Pharmacovigilance Inspections"],
        "related_items": ["regulation/gvp-module-i", "capa/CAPA-2025-018"],
    },
    ("audit", "gvp-internal-2026"): {
        "title": "Internal PV System Audit (2026)",
        "summary": (
            "Scheduled internal quality audit of the pharmacovigilance system per "
            "GVP Module I requirements. Covers all PV processes, vendor oversight, "
            "training compliance, and CAPA effectiveness."
        ),
        "sections": [
            {
                "heading": "Audit Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Type": "Internal quality audit",
                    "Scope": "Full PV system — ICSR processing, signal management, periodic reporting, vendor oversight",
                    "Scheduled date": "2026-05-12 to 2026-05-16",
                    "Lead auditor": "Quality Assurance — PV Audit Team",
                    "Status": "Planning phase",
                },
            },
            {
                "heading": "Audit Objectives",
                "detail_type": "text",
                "content": [
                    "Verify CAPA effectiveness from 2025 EMA inspection findings",
                    "Assess training compliance across all PV roles",
                    "Review SOP currency and adherence",
                    "Evaluate vendor/CRO oversight and KPI monitoring",
                    "Confirm inspection readiness for upcoming FDA PAI",
                ],
            },
        ],
        "regulatory_references": ["GVP Module I Rev 2", "GVP Module III"],
        "related_items": ["audit/gvp-ema-2025", "kpi/inspection-readiness"],
    },
    ("audit", "fda-pai-2026"): {
        "title": "FDA Pre-Approval Inspection (2026)",
        "summary": (
            "Anticipated FDA pre-approval inspection (PAI) for the Prosinertimib NDA "
            "submission. Will cover clinical data integrity, manufacturing sites, "
            "and pharmacovigilance readiness."
        ),
        "sections": [
            {
                "heading": "Inspection Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Authority": "FDA CDER / Office of Regulatory Affairs (ORA)",
                    "Type": "Pre-Approval Inspection (PAI)",
                    "Scope": "Clinical investigator sites, sponsor facilities, CMO/manufacturing sites",
                    "Expected window": "Q3/Q4 2026 (pending NDA filing acceptance)",
                    "Status": "Readiness preparation",
                },
            },
            {
                "heading": "Preparation Activities",
                "detail_type": "text",
                "content": [
                    "Pre-inspection readiness assessment completed for all pivotal trial sites",
                    "Source data verification for key efficacy and safety endpoints",
                    "Manufacturing site GMP readiness confirmed",
                    "PV system inspection readiness per FDA Compliance Program 7348.810",
                    "Mock inspection scheduled for 2026-07",
                ],
            },
        ],
        "regulatory_references": [
            "FDA Compliance Program 7348.811 (Clinical Investigators)",
            "FDA Compliance Program 7346.832 (Pre-Approval Inspections)",
        ],
        "related_items": ["audit/gcp-mhra-2026", "trial/PROSPER-1"],
    },
    ("audit", "ema-gvp-2026"): {
        "title": "EMA Pharmacovigilance Inspection (2026)",
        "summary": (
            "Anticipated EMA-triggered GVP inspection in 2026 as part of the "
            "centralised procedure for Prosinertimib marketing authorisation. "
            "Will follow up on 2025 inspection findings and assess expanded PV system."
        ),
        "sections": [
            {
                "heading": "Inspection Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Authority": "EMA-coordinated (lead NCA to be assigned)",
                    "Type": "Pre-authorisation GVP inspection",
                    "Expected window": "Q4 2026",
                    "Focus": "Signal management, RMP implementation, QPPV oversight, vendor management",
                    "Status": "Anticipated — preparing readiness documentation",
                },
            },
            {
                "heading": "Key Preparation Steps",
                "detail_type": "text",
                "content": [
                    "PSMF updated with current vendor contracts and system descriptions",
                    "All CAPAs from 2025 inspection verified as effective",
                    "Signal management process walkthrough prepared",
                    "RMP implementation evidence compiled",
                ],
            },
        ],
        "regulatory_references": ["GVP Module III", "GVP Module I"],
        "related_items": ["audit/gvp-ema-2025", "audit/gvp-internal-2026"],
    },

    # ── CAPAs ─────────────────────────────────────────────────────────────

    ("capa", "CAPA-2026-001"): {
        "title": "CAPA-2026-001: Signal Detection Cycle Time Improvement",
        "summary": (
            "Corrective action to address signal detection cycle times exceeding "
            "the 30-day target in Q4 2025. Root cause: manual data extraction step "
            "creating bottleneck. Implementing automated disproportionality screening."
        ),
        "sections": [
            {
                "heading": "CAPA Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Classification": "Major",
                    "Source": "KPI breach — signal detection cycle time",
                    "Root cause": "Manual FAERS data extraction and formatting delayed initiation of statistical analysis",
                    "Corrective action": "Implement automated data extraction pipeline from FAERS quarterly files",
                    "Preventive action": "Establish automated disproportionality screening with configurable alert thresholds",
                    "Target closure": "2026-06-30",
                    "Status": "In progress — automation development 70% complete",
                },
            },
        ],
        "regulatory_references": ["GVP Module IX", "GVP Module I"],
        "related_items": ["kpi/signal-detection-cycle", "kpi/capa-closure"],
    },
    ("capa", "CAPA-2026-002"): {
        "title": "CAPA-2026-002: E2B(R3) Transmission Errors",
        "summary": (
            "Corrective action for repeated E2B(R3) acknowledgement failures (ACK errors) "
            "on EudraVigilance submissions. Root cause: MedDRA version mismatch after "
            "March 2026 dictionary update."
        ),
        "sections": [
            {
                "heading": "CAPA Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Classification": "Major",
                    "Source": "KPI breach — E2B acceptance rate dropped to 89%",
                    "Root cause": "Safety database MedDRA dictionary not updated to version 27.0 in time; deprecated LLTs caused validation failures",
                    "Corrective action": "Emergency MedDRA update applied; re-submission of 12 rejected cases",
                    "Preventive action": "MedDRA update SOP amended to require update within 5 business days of MSSO release",
                    "Target closure": "2026-04-30",
                    "Status": "Corrective action complete; preventive action in SOP review cycle",
                },
            },
        ],
        "regulatory_references": ["ICH E2B(R3)", "GVP Module VI"],
        "related_items": ["kpi/e2b-acceptance", "regulation/ich-e2b-r3"],
    },
    ("capa", "CAPA-2026-003"): {
        "title": "CAPA-2026-003: Late Expedited Report — Hepatotoxicity Case",
        "summary": (
            "Corrective action for a single late 15-day expedited ICSR (submitted on Day 17). "
            "Root cause: delayed triage due to incomplete initial report from investigator site."
        ),
        "sections": [
            {
                "heading": "CAPA Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Classification": "Critical",
                    "Source": "Late expedited ICSR submission — Day 17 vs. 15-day deadline",
                    "Root cause": "Initial report lacked seriousness criteria; follow-up revealing hospitalisation received on Day 12",
                    "Corrective action": "Case submitted on Day 17; deviation report filed; investigator re-trained on SAE reporting requirements",
                    "Preventive action": "Implement automated triage alerts for cases approaching Day 10 without seriousness determination",
                    "Target closure": "2026-05-15",
                    "Status": "Corrective action complete; preventive action in UAT",
                },
            },
        ],
        "regulatory_references": ["21 CFR 312.32", "GVP Module VI"],
        "related_items": ["kpi/serious-15-day", "risk/hepatotox"],
    },
    ("capa", "CAPA-2025-018"): {
        "title": "CAPA-2025-018: PSMF Logbook Update Delay",
        "summary": (
            "Corrective action from the 2025 EMA GVP inspection finding. PSMF logbook "
            "entry for a vendor change was delayed by 15 days beyond the required timeframe."
        ),
        "sections": [
            {
                "heading": "CAPA Details",
                "detail_type": "key_value_pairs",
                "content": {
                    "Classification": "Minor",
                    "Source": "2025 EMA GVP inspection — Finding #1",
                    "Root cause": "No automated trigger for PSMF logbook update upon vendor contract change",
                    "Corrective action": "Retrospective logbook entry added with documented justification",
                    "Preventive action": "PSMF update checklist integrated into vendor management SOP; automated reminders in contract management system",
                    "Target closure": "2026-01-15",
                    "Status": "Closed — effectiveness verified at Q1 2026 internal review",
                },
            },
        ],
        "regulatory_references": ["GVP Module II", "GVP Module I"],
        "related_items": ["audit/gvp-ema-2025", "regulation/gvp-module-ii"],
    },

    # ── RISKS (additional) ────────────────────────────────────────────────

    ("risk", "hypertension"): {
        "title": "Hypertension — Prosinertimib Risk Profile",
        "summary": (
            "Hypertension is an identified risk for Prosinertimib, observed in 12.3% of "
            "patients in clinical trials. Most cases are Grade 1-2 and manageable with "
            "standard antihypertensive therapy. Grade 3+ hypertension occurred in 3.1%."
        ),
        "sections": [
            {
                "heading": "Clinical Data",
                "detail_type": "key_value_pairs",
                "content": {
                    "Overall incidence": "12.3% (all grades)",
                    "Grade 3+": "3.1%",
                    "Median onset": "4.6 weeks from treatment initiation",
                    "Management": "Standard antihypertensives (ACE inhibitors, ARBs, calcium channel blockers)",
                    "Dose modification required": "2.8% of patients required dose reduction",
                    "Discontinuation due to hypertension": "0.4%",
                },
            },
            {
                "heading": "Mechanism",
                "detail_type": "text",
                "content": (
                    "EGFR inhibition affects vascular endothelial function through disruption "
                    "of nitric oxide signaling pathways. This is a recognized class effect for "
                    "EGFR TKIs, though incidence varies across agents. Prosinertimib's rate is "
                    "comparable to other third-generation EGFR TKIs."
                ),
            },
            {
                "heading": "Monitoring",
                "detail_type": "text",
                "content": [
                    "Blood pressure monitoring at baseline and every 2 weeks for the first 3 months",
                    "Monthly monitoring thereafter",
                    "Target BP < 140/90 mmHg (< 130/80 for patients with diabetes or CKD)",
                    "Dose reduction if Grade 3 hypertension persists despite optimal medical management",
                ],
            },
        ],
        "regulatory_references": [
            "Prosinertimib Investigator's Brochure Section 5.3",
            "CCSI Section 4.4 — Special Warnings",
        ],
        "related_items": ["risk/qt-prolongation", "trial/PROSPER-1"],
    },
    ("risk", "severe-diarrhea"): {
        "title": "Severe Diarrhea — Prosinertimib Risk Profile",
        "summary": (
            "Diarrhea is the most common adverse event with Prosinertimib (any grade: 48.2%). "
            "Severe (Grade 3+) diarrhea occurred in 7.8% of patients. A class effect of EGFR "
            "TKIs due to inhibition of chloride secretion in intestinal epithelium."
        ),
        "sections": [
            {
                "heading": "Clinical Data",
                "detail_type": "key_value_pairs",
                "content": {
                    "Overall incidence": "48.2% (all grades)",
                    "Grade 3+": "7.8%",
                    "Median onset": "8 days from treatment initiation",
                    "Median duration": "12 days (Grade 1-2), 18 days (Grade 3+)",
                    "Management": "Loperamide, dose interruption/reduction for Grade 3+",
                    "Discontinuation due to diarrhea": "1.2%",
                },
            },
            {
                "heading": "Risk Minimisation",
                "detail_type": "text",
                "content": [
                    "Patient education on early diarrhea management and when to contact physician",
                    "Prophylactic loperamide may be considered in patients with prior GI sensitivity",
                    "Dose reduction algorithm: Grade 3 — interrupt until Grade 1 or less, resume at reduced dose",
                    "Hydration and electrolyte monitoring for Grade 3+ events",
                ],
            },
        ],
        "regulatory_references": [
            "Prosinertimib Investigator's Brochure Section 5.3",
            "CCSI Section 4.8 — Undesirable Effects",
        ],
        "related_items": ["risk/skin-tox", "trial/PROSPER-1"],
    },

    # ── SIGNAL (additional) ───────────────────────────────────────────────

    ("signal", "SIG-2025-022"): {
        "title": "SIG-2025-022: Prosinertimib — Ocular Toxicity",
        "summary": (
            "A validated signal of ocular toxicity (keratitis, corneal epithelial "
            "defects) from post-marketing spontaneous reports. 8 cases received "
            "including 2 with corneal ulceration. PRR 2.14 (95% CI: 1.32-3.47). "
            "Under evaluation — potential EGFR class effect."
        ),
        "sections": [
            {
                "heading": "Case Summary",
                "detail_type": "text",
                "content": (
                    "8 spontaneous reports received: 4 keratitis, 2 corneal epithelial defects, "
                    "2 corneal ulceration. All patients were on standard 80 mg dose. Median onset "
                    "2.1 months. 6 of 8 cases resolved after treatment discontinuation or dose "
                    "reduction. Two cases required ophthalmologic intervention."
                ),
            },
            {
                "heading": "Class Effect Context",
                "detail_type": "text",
                "content": (
                    "Ocular toxicity is a recognized class effect of EGFR TKIs. EGFR is expressed "
                    "in corneal and conjunctival epithelium. Erlotinib and afatinib carry labeled "
                    "warnings for corneal disorders. The Prosinertimib signal rate appears within "
                    "the range observed for the EGFR TKI class."
                ),
            },
            {
                "heading": "Action Timeline",
                "detail_type": "timeline",
                "content": [
                    {"date": "2025-10-01", "event": "Signal detected via routine disproportionality analysis"},
                    {"date": "2025-10-20", "event": "Signal validated — confirmed as true signal"},
                    {"date": "2025-12-15", "event": "Case series review completed"},
                    {"date": "2026-02-01", "event": "Evaluation ongoing — labeling update under consideration"},
                ],
            },
        ],
        "regulatory_references": [
            "GVP Module IX — Signal Management",
        ],
        "related_items": ["signal/SIG-2026-001", "risk/skin-tox"],
    },

    # ── SOPs (additional) ─────────────────────────────────────────────────

    ("sop", "PV-SOP-006"): {
        "title": "PV-SOP-006 — PBRER/PSUR Preparation and Submission",
        "summary": (
            "Defines the process for authoring, reviewing, approving, and submitting "
            "Periodic Benefit-Risk Evaluation Reports (PBRERs) and PSURs to regulatory "
            "authorities per ICH E2C(R2) and GVP Module VII."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure timely, complete, and high-quality periodic safety reports that "
                    "meet ICH E2C(R2) content requirements and are submitted within regulatory "
                    "deadlines per the EURD list and local requirements."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Establish DLP and submission deadlines per EURD list and local requirements",
                    "2. Generate cumulative and interval data extracts from safety database",
                    "3. Author all 19+ PBRER sections per ICH E2C(R2) template",
                    "4. Conduct signal review and integrated benefit-risk evaluation",
                    "5. Medical review and quality review of draft report",
                    "6. QPPV/delegate approval",
                    "7. Submit to all applicable regulatory authorities within deadline",
                    "8. Track acknowledgements and respond to authority questions",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon regulatory change",
                    "Training requirement": "All PBRER authors and reviewers must complete training on ICH E2C(R2) format and content",
                },
            },
        ],
        "regulatory_references": ["ICH E2C(R2)", "GVP Module VII"],
        "related_items": ["report/pbrer", "report/psur", "kpi/aggregate-submissions"],
    },
    ("sop", "PV-SOP-007"): {
        "title": "PV-SOP-007 — Risk Management Plan Maintenance",
        "summary": (
            "Defines the process for creating, updating, and maintaining the EU Risk "
            "Management Plan (RMP) including safety specification updates, PV plan "
            "revisions, and risk minimisation effectiveness evaluation."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure the RMP remains current and accurately reflects the evolving "
                    "safety profile of the product throughout its lifecycle, from initial "
                    "MA application through post-marketing."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Maintain safety specification with identified risks, potential risks, and missing information",
                    "2. Update PV plan when new risks are identified or existing risks are re-characterised",
                    "3. Implement and track additional risk minimisation measures",
                    "4. Evaluate effectiveness of risk minimisation using defined indicators",
                    "5. Submit RMP updates with Type II variations or at regulatory request",
                    "6. Coordinate with regulatory affairs for submission across all markets",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon significant safety signal",
                    "Training requirement": "RMP authors must be trained on GVP Module V and XVI requirements",
                },
            },
        ],
        "regulatory_references": ["GVP Module V Rev 2", "GVP Module XVI"],
        "related_items": ["regulation/gvp-module-v", "kpi/rmp-implementation"],
    },
    ("sop", "PV-SOP-008"): {
        "title": "PV-SOP-008 — Literature Monitoring and Case Identification",
        "summary": (
            "Defines the process for systematic monitoring of worldwide medical "
            "literature for ICSRs, safety signals, and relevant safety information "
            "per ICH E2D requirements."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure systematic identification and processing of adverse event "
                    "reports published in the medical literature, as required by ICH E2D. "
                    "Day 0 is the date the MAH becomes aware of the publication."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Define search strategy: databases (PubMed, Embase), search terms (product name, INN, synonyms), frequency (weekly)",
                    "2. Screen retrieved articles for valid ICSRs (4 minimum criteria)",
                    "3. Extract case information and enter into safety database with Day 0 = awareness date",
                    "4. Process per standard ICSR workflow (data entry, MedDRA coding, medical review)",
                    "5. Retain search results and screening documentation for audit trail",
                    "6. Document non-case articles containing relevant safety information for signal evaluation",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years",
                    "Training requirement": "Literature screening staff must complete training on ICSR identification from publications",
                },
            },
        ],
        "regulatory_references": ["ICH E2D", "GVP Module VI"],
        "related_items": ["sop/PV-SOP-001", "regulation/ich-e2d"],
    },
    ("sop", "PV-SOP-009"): {
        "title": "PV-SOP-009 — Vendor and CRO Oversight for PV Activities",
        "summary": (
            "Defines the process for selecting, qualifying, overseeing, and auditing "
            "third-party vendors and CROs performing delegated pharmacovigilance activities."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure that outsourced PV activities meet the same quality and "
                    "compliance standards as in-house operations, and that the MAH retains "
                    "full responsibility for the PV system per GVP Module I."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Vendor qualification: assess capabilities, SOPs, training, technology, and regulatory track record",
                    "2. Establish Safety Data Exchange Agreement (SDEA) or PV Agreement defining roles and timelines",
                    "3. Define KPIs and reporting requirements in the contract",
                    "4. Conduct ongoing oversight: monthly KPI review, quarterly governance meetings",
                    "5. Audit vendor PV operations at least every 2 years (risk-based frequency)",
                    "6. Document vendor performance and escalate non-compliance through CAPA process",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon significant vendor change",
                    "Training requirement": "Vendor oversight staff must be trained on SDEA requirements and inspection expectations",
                },
            },
        ],
        "regulatory_references": ["GVP Module I Rev 2", "GVP Module II"],
        "related_items": ["regulation/gvp-module-i", "audit/gvp-internal-2026"],
    },
    ("sop", "PV-SOP-010"): {
        "title": "PV-SOP-010 — DSUR Preparation and Submission",
        "summary": (
            "Defines the process for authoring, reviewing, and submitting the "
            "Development Safety Update Report (DSUR) per ICH E2F for all "
            "investigational products."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure timely and compliant DSUR preparation covering all clinical "
                    "trials conducted under the IND/CTA, submitted within 60 days of the "
                    "DIBD anniversary to all relevant regulatory authorities."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Determine DIBD and reporting period; confirm DLP",
                    "2. Compile trial inventory, exposure data, and line listings from all active/completed studies",
                    "3. Author 20 DSUR sections per ICH E2F template",
                    "4. Perform overall safety assessment and benefit-risk evaluation",
                    "5. Medical and quality review; QPPV approval",
                    "6. Submit to all authorities with active IND/CTA within 60 days of DLP",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years",
                    "Training requirement": "DSUR authors must be trained on ICH E2F content and format requirements",
                },
            },
        ],
        "regulatory_references": ["ICH E2F", "21 CFR 312.33"],
        "related_items": ["report/dsur", "regulation/ich-e2f"],
    },
    ("sop", "PV-SOP-011"): {
        "title": "PV-SOP-011 — Safety Database Management and Validation",
        "summary": (
            "Defines the requirements for managing, validating, and maintaining the "
            "pharmacovigilance safety database including access controls, audit trails, "
            "backup procedures, and 21 CFR Part 11 compliance."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure the safety database operates in a validated state with "
                    "documented evidence of compliance with 21 CFR Part 11, EU GMP Annex 11, "
                    "and applicable data integrity requirements."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Maintain validated state: IQ/OQ/PQ documentation, change control for all system updates",
                    "2. User access management: role-based access, periodic access reviews (quarterly)",
                    "3. Audit trail: enabled for all data creation, modification, and deletion events",
                    "4. Data backup: daily incremental, weekly full, tested quarterly restore",
                    "5. Dictionary updates: MedDRA and WHODrug updates applied within defined timelines",
                    "6. Electronic signature compliance: Part 11 requirements for case approval and submission",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Every 2 years or upon major system upgrade",
                    "Training requirement": "System administrators and QA must be trained on computerised system validation requirements",
                },
            },
        ],
        "regulatory_references": ["21 CFR Part 11", "EU GMP Annex 11"],
        "related_items": ["regulation/21-cfr-part-11", "sop/PV-SOP-002"],
    },
    ("sop", "PV-SOP-012"): {
        "title": "PV-SOP-012 — Regulatory Intelligence and Safety Labeling Updates",
        "summary": (
            "Defines the process for monitoring regulatory intelligence, assessing "
            "impact on the pharmacovigilance system, and implementing safety labeling "
            "changes across all markets."
        ),
        "sections": [
            {
                "heading": "Purpose",
                "detail_type": "text",
                "content": (
                    "To ensure timely awareness of regulatory changes affecting PV operations "
                    "and systematic implementation of safety labeling updates to maintain "
                    "alignment between the CCSI and all local product labels."
                ),
            },
            {
                "heading": "Key Steps",
                "detail_type": "text",
                "content": [
                    "1. Monitor regulatory intelligence sources: authority websites, industry associations, regulatory alerts",
                    "2. Assess impact of regulatory changes on PV SOPs, systems, and processes",
                    "3. Implement required changes within defined timelines",
                    "4. Track CCSI updates and trigger local label alignment across all markets",
                    "5. Maintain labeling change tracker with target dates and completion status",
                    "6. Report labeling alignment status at PV governance meetings",
                ],
            },
            {
                "heading": "Review Cycle and Training",
                "detail_type": "key_value_pairs",
                "content": {
                    "Review cycle": "Annually or upon significant regulatory change",
                    "Training requirement": "Regulatory affairs and PV staff must be trained on regulatory intelligence monitoring",
                },
            },
        ],
        "regulatory_references": ["GVP Module XV", "GVP Module XVI"],
        "related_items": ["kpi/labeling-alignment", "regulation/gvp-module-xv"],
    },

    # ── TRIALS ────────────────────────────────────────────────────────────

    ("trial", "PROSPER-1"): {
        "title": "PROSPER-1: Phase III Pivotal Trial — Prosinertimib vs. Osimertinib in 1L EGFR+ NSCLC",
        "summary": (
            "Randomised, open-label, Phase III trial comparing prosinertimib 80 mg QD "
            "vs. osimertinib 80 mg QD as first-line treatment in patients with locally "
            "advanced or metastatic NSCLC harbouring EGFR-activating mutations (Ex19del "
            "or L858R). Primary endpoint: PFS by blinded IRC."
        ),
        "sections": [
            {
                "heading": "Trial Design",
                "detail_type": "key_value_pairs",
                "content": {
                    "Phase": "III",
                    "Design": "Randomised 1:1, open-label, active-controlled, multicentre, global",
                    "Population": "Treatment-naive locally advanced/metastatic NSCLC with EGFR Ex19del or L858R",
                    "N (planned)": "650 patients",
                    "Primary endpoint": "Progression-free survival (PFS) by blinded independent review committee (IRC)",
                    "Key secondary": "Overall survival (OS), objective response rate (ORR), duration of response (DoR), CNS PFS",
                    "Comparator": "Osimertinib 80 mg QD",
                },
            },
            {
                "heading": "Safety Monitoring",
                "detail_type": "text",
                "content": [
                    "Independent Data Safety Monitoring Board (DSMB) reviews unblinded safety data every 6 months",
                    "Pre-defined stopping boundaries for futility and safety",
                    "Mandatory ILD monitoring: chest CT at baseline, Week 6, Week 12, then every 12 weeks",
                    "Cardiac monitoring: ECG at baseline, Weeks 2, 4, 8, 12, then every 12 weeks; ECHO at baseline and every 24 weeks",
                    "Hepatic monitoring: LFTs every 2 weeks for first 3 months, then monthly",
                ],
            },
        ],
        "regulatory_references": [
            "IND 123456 (FDA)", "EudraCT 2025-001234-56 (EMA)", "ICH E6(R3)",
        ],
        "related_items": ["trial/PROSPER-2", "trial/PROSPER-3", "risk/ild"],
    },
    ("trial", "PROSPER-2"): {
        "title": "PROSPER-2: Phase III Trial — Prosinertimib in 2L EGFR+ NSCLC (Post-Osimertinib)",
        "summary": (
            "Randomised, Phase III trial evaluating prosinertimib in patients with "
            "EGFR+ NSCLC who have progressed on prior osimertinib. Targets T790M-"
            "independent resistance mechanisms including C797S. Primary endpoint: PFS."
        ),
        "sections": [
            {
                "heading": "Trial Design",
                "detail_type": "key_value_pairs",
                "content": {
                    "Phase": "III",
                    "Design": "Randomised 2:1, double-blind, placebo-controlled (+BSC), multicentre",
                    "Population": "EGFR+ NSCLC progressed on osimertinib; includes C797S mutation cohort",
                    "N (planned)": "450 patients",
                    "Primary endpoint": "Progression-free survival (PFS) by blinded IRC",
                    "Key secondary": "OS, ORR, intracranial ORR, patient-reported outcomes (PROs)",
                },
            },
            {
                "heading": "Status",
                "detail_type": "text",
                "content": (
                    "Currently enrolling. First patient randomised Q4 2025. Interim analysis "
                    "planned after 60% PFS events. DSMB oversight with 6-monthly reviews."
                ),
            },
        ],
        "regulatory_references": [
            "IND 123457 (FDA)", "EudraCT 2025-001235-78",
        ],
        "related_items": ["trial/PROSPER-1", "trial/PROSPER-3"],
    },
    ("trial", "PROSPER-3"): {
        "title": "PROSPER-3: Phase II Trial — Prosinertimib + Chemotherapy Combination",
        "summary": (
            "Single-arm, Phase II trial evaluating prosinertimib in combination with "
            "platinum-pemetrexed chemotherapy in patients with EGFR+ NSCLC and "
            "concurrent TP53 co-mutations. Primary endpoint: ORR."
        ),
        "sections": [
            {
                "heading": "Trial Design",
                "detail_type": "key_value_pairs",
                "content": {
                    "Phase": "II",
                    "Design": "Single-arm, open-label, multicentre",
                    "Population": "EGFR+ NSCLC with concurrent TP53 co-mutation (associated with poorer TKI response)",
                    "N (planned)": "120 patients",
                    "Primary endpoint": "Objective response rate (ORR) by RECIST 1.1",
                    "Key secondary": "PFS, OS, safety and tolerability of combination, ctDNA clearance rate",
                },
            },
            {
                "heading": "Safety Considerations",
                "detail_type": "text",
                "content": (
                    "Combination of EGFR TKI with platinum chemotherapy requires enhanced "
                    "monitoring for overlapping toxicities: myelosuppression, ILD, hepatotoxicity, "
                    "and GI toxicity. Dose modification algorithm defines priority of dose changes "
                    "when overlapping toxicities occur."
                ),
            },
        ],
        "regulatory_references": [
            "IND 123458 (FDA)", "ICH E6(R3)",
        ],
        "related_items": ["trial/PROSPER-1", "trial/PROSPER-2"],
    },

}


# ---------------------------------------------------------------------------
# Detail endpoint
# ---------------------------------------------------------------------------

@router.get("/detail/{item_type}/{item_id}", response_model=DetailResponse)
async def get_detail(item_type: str, item_id: str) -> DetailResponse:
    """Return deepening detail for a signal, risk, or drug class item."""
    key = (item_type, item_id)
    if key not in _DETAIL_DATA:
        raise HTTPException(
            status_code=404,
            detail=f"No detail found for {item_type}/{item_id}",
        )
    data = _DETAIL_DATA[key]
    return DetailResponse(
        request_id=_make_request_id(),
        timestamp=_now().isoformat(),
        item_type=item_type,
        item_id=item_id,
        **data,
    )
