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

from fastapi import APIRouter
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
