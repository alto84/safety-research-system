"""Pharmaceutical company simulation engine.

Generates role-specific deliverables, activity logs, and delegation trees
for a simulated cell therapy company running a Phase I first-in-human trial.

Each deliverable is grounded in real regulatory frameworks from pharma_org.py.
All data is for simulation purposes only -- no proprietary or patient data.

Phase 5 of the pharma company simulation. Preceding phases:
  1. Org hierarchy (pharma_org.py: ORG_ROLES)
  2. Regulatory mapping (pharma_org.py: REGULATORY_MAP)
  3. Pipeline stages (pharma_org.py: PIPELINE_STAGES)
  4. Quality metrics (pharma_org.py: get_quality_metrics)
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from typing import Any

from src.data.pharma_org import (
    ORG_ROLES,
    REGULATORY_MAP,
    get_quality_metrics,
)


# ---------------------------------------------------------------------------
# Module-level simulation state
# ---------------------------------------------------------------------------

SIMULATION_LOG: list[dict[str, Any]] = []
DELIVERABLES: dict[str, list[dict[str, Any]]] = {}

# Simulation epoch -- all timestamps are relative to this.
_SIM_START = datetime(2025, 11, 1, 8, 0, 0, tzinfo=timezone.utc)

# Phase I FIH trial baseline constants (consistent with pharma_org pipeline)
_PHASE1_START = "2024-11"
_ENROLLED_PATIENTS = 28
_SCREEN_FAILURES = 9
_TOTAL_SCREENED = _ENROLLED_PATIENTS + _SCREEN_FAILURES  # 37
_NUM_SITES = 3
_DOSE_LEVELS = 4  # 3+3 escalation
_DLT_WINDOW_DAYS = 28
_DSUR_DIB_DATE = "2024-11-01"  # DSUR data lock point = IND effective date
_DSUR_REPORTING_PERIOD_END = "2025-10-31"

# ICSR counts consistent with ~28 patients in Phase I
_TOTAL_ICSRS = 42
_SERIOUS_ICSRS = 8
_NON_SERIOUS_ICSRS = _TOTAL_ICSRS - _SERIOUS_ICSRS  # 34
_EXPEDITED_REPORTS = 3  # 15-day or 7-day IND safety reports
_CRS_CASES = 6
_ICANS_CASES = 2
_DEATHS = 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ts(day_offset: int, hour: int = 9) -> str:
    """Return an ISO-8601 timestamp offset from the simulation start."""
    dt = _SIM_START + timedelta(days=day_offset, hours=hour - 8)
    return dt.isoformat()


def _make_deliverable(
    deliverable_id: str,
    title: str,
    role_id: str,
    category: str,
    regulatory_refs: list[str],
    status: str = "draft",
    version: str = "1.0",
    sections: list[dict[str, Any]] | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a standardised deliverable dict."""
    return {
        "deliverable_id": deliverable_id,
        "title": title,
        "role_id": role_id,
        "category": category,
        "regulatory_refs": regulatory_refs,
        "status": status,
        "version": version,
        "created": _ts(0),
        "sections": sections or [],
        "data": data or {},
    }


def _log_entry(
    day_offset: int,
    hour: int,
    role_id: str,
    action: str,
    description: str,
    regulatory_basis: str,
    target: str | None = None,
    deliverable_id: str | None = None,
) -> dict[str, Any]:
    """Build a standardised activity log entry."""
    entry: dict[str, Any] = {
        "timestamp": _ts(day_offset, hour),
        "role_id": role_id,
        "action": action,
        "description": description,
        "regulatory_basis": regulatory_basis,
    }
    if target is not None:
        entry["target"] = target
    if deliverable_id is not None:
        entry["deliverable_id"] = deliverable_id
    return entry


# ---------------------------------------------------------------------------
# CMO deliverables
# ---------------------------------------------------------------------------

def generate_cmo_deliverables() -> list[dict[str, Any]]:
    """Generate Chief Medical Officer deliverables.

    Produces a benefit-risk assessment summary, DSMB charter outline,
    and clinical development plan overview. References ICH E2C(R2)
    for periodic benefit-risk evaluation and CIOMS IV principles.

    Returns:
        List of structured deliverable dicts.
    """
    benefit_risk = _make_deliverable(
        deliverable_id="cmo_benefit_risk_v1",
        title="Benefit-Risk Assessment Summary -- AZ-CT-001 Phase I",
        role_id="cmo",
        category="medical_strategy",
        regulatory_refs=["ICH_E2C_R2", "ICH_E8_R1"],
        status="under_review",
        sections=[
            {
                "heading": "Benefit Assessment",
                "content": (
                    "Preliminary efficacy signals in 3 of 4 dose cohorts. "
                    "Objective response observed in 5/28 evaluable patients "
                    "(17.9%) at interim analysis."
                ),
            },
            {
                "heading": "Risk Assessment",
                "content": (
                    f"Grade >= 3 CRS in {_CRS_CASES} patients ({_CRS_CASES}/{_ENROLLED_PATIENTS} = "
                    f"{round(_CRS_CASES / _ENROLLED_PATIENTS * 100, 1)}%). "
                    f"ICANS reported in {_ICANS_CASES} patients. "
                    f"No treatment-related deaths. "
                    f"{_SERIOUS_ICSRS} serious AEs total across all dose levels."
                ),
            },
            {
                "heading": "Benefit-Risk Balance",
                "content": (
                    "Current benefit-risk profile supports continuation of "
                    "dose escalation with enhanced CRS monitoring per protocol."
                ),
            },
        ],
        data={
            "enrolled": _ENROLLED_PATIENTS,
            "evaluable": _ENROLLED_PATIENTS,
            "objective_responses": 5,
            "orr_pct": 17.9,
            "grade3_plus_crs": _CRS_CASES,
            "icans_cases": _ICANS_CASES,
            "deaths": _DEATHS,
            "serious_aes": _SERIOUS_ICSRS,
        },
    )

    dsmb_charter = _make_deliverable(
        deliverable_id="cmo_dsmb_charter_v1",
        title="DSMB Charter Outline -- AZ-CT-001",
        role_id="cmo",
        category="governance",
        regulatory_refs=["ICH_E6_R3", "ICH_E9", "21_CFR_312"],
        status="draft",
        sections=[
            {
                "heading": "Charter Scope",
                "content": (
                    "Independent Data Safety Monitoring Board for Phase I "
                    "dose-escalation study AZ-CT-001. Reviews safety data "
                    "after each dose cohort per 3+3 design."
                ),
            },
            {
                "heading": "Membership",
                "content": (
                    "Minimum 3 members: oncologist/hematologist (chair), "
                    "biostatistician, pharmacovigilance expert. "
                    "All independent of sponsor."
                ),
            },
            {
                "heading": "Meeting Schedule",
                "content": (
                    "Scheduled after each cohort completes DLT window "
                    f"({_DLT_WINDOW_DAYS} days). Ad-hoc meetings triggered "
                    "by SAE clustering or > 33% DLT rate in any cohort."
                ),
            },
            {
                "heading": "Decision Framework",
                "content": (
                    "Escalate / expand / de-escalate / halt recommendations. "
                    "Uses modified Bayesian Optimal Interval (mBOIN) boundaries."
                ),
            },
        ],
        data={
            "dlt_window_days": _DLT_WINDOW_DAYS,
            "dose_levels": _DOSE_LEVELS,
            "patients_per_cohort": 3,
            "max_expansion": 6,
        },
    )

    cdp_overview = _make_deliverable(
        deliverable_id="cmo_cdp_overview_v1",
        title="Clinical Development Plan Overview -- CAR-T Autoimmune Program",
        role_id="cmo",
        category="development_strategy",
        regulatory_refs=["ICH_E8_R1", "21_CFR_312", "CBER_early_phase"],
        status="approved",
        sections=[
            {
                "heading": "Program Objective",
                "content": (
                    "Develop autologous CD19 CAR-T therapy for refractory "
                    "systemic lupus erythematosus (SLE). Target accelerated "
                    "approval via breakthrough therapy designation."
                ),
            },
            {
                "heading": "Phase I (Current)",
                "content": (
                    f"First-in-human 3+3 dose escalation, {_DOSE_LEVELS} dose "
                    f"levels, {_NUM_SITES} sites. Primary endpoint: safety/DLT. "
                    f"Enrolled {_ENROLLED_PATIENTS}/{_TOTAL_SCREENED} screened."
                ),
            },
            {
                "heading": "Phase II (Planned)",
                "content": (
                    "Single-arm expansion at RP2D. Primary: complete B-cell "
                    "depletion at Month 3. Key secondary: SLE Responder Index "
                    "at Month 6. N ~ 40."
                ),
            },
            {
                "heading": "Phase III (Planned)",
                "content": (
                    "Randomized controlled vs. standard of care (belimumab). "
                    "Co-primary: SRI-4 at Week 52, steroid-free remission. "
                    "Target N = 200."
                ),
            },
        ],
        data={
            "indication": "Systemic Lupus Erythematosus",
            "therapy_type": "Autologous CD19 CAR-T",
            "phase1_sites": _NUM_SITES,
            "phase1_enrolled": _ENROLLED_PATIENTS,
            "phase2_target_n": 40,
            "phase3_target_n": 200,
        },
    )

    return [benefit_risk, dsmb_charter, cdp_overview]


# ---------------------------------------------------------------------------
# VP Clinical Ops deliverables
# ---------------------------------------------------------------------------

def generate_clinops_deliverables() -> list[dict[str, Any]]:
    """Generate VP Clinical Operations deliverables.

    Produces a trial status report (3 sites, enrollment numbers, screen
    failures), a protocol deviation summary, and a monitoring visit schedule.
    References ICH E6(R3) for GCP and 21 CFR 312 for IND compliance.

    Returns:
        List of structured deliverable dicts.
    """
    trial_status = _make_deliverable(
        deliverable_id="clinops_trial_status_v1",
        title="Trial Status Report -- AZ-CT-001 Phase I FIH",
        role_id="vp_clinops",
        category="trial_management",
        regulatory_refs=["ICH_E6_R3", "21_CFR_312", "CBER_early_phase"],
        status="final",
        sections=[
            {
                "heading": "Enrollment Summary",
                "content": (
                    f"Total screened: {_TOTAL_SCREENED}. Enrolled: {_ENROLLED_PATIENTS}. "
                    f"Screen failures: {_SCREEN_FAILURES} ({round(_SCREEN_FAILURES / _TOTAL_SCREENED * 100, 1)}%). "
                    f"Across {_NUM_SITES} active sites."
                ),
            },
            {
                "heading": "Site Performance",
                "content": (
                    "Site 001 (Academic Medical Center): 12 enrolled, 4 screen failures. "
                    "Site 002 (Community Hospital): 9 enrolled, 3 screen failures. "
                    "Site 003 (Research Institute): 7 enrolled, 2 screen failures."
                ),
            },
            {
                "heading": "Dose Escalation Status",
                "content": (
                    f"Cohort 1 (DL1): 3/3 complete, 0 DLTs, escalated. "
                    f"Cohort 2 (DL2): 3/3 complete, 0 DLTs, escalated. "
                    f"Cohort 3 (DL3): 6/6 complete (expanded), 1 DLT, escalated. "
                    f"Cohort 4 (DL4): 3/3 complete, 1 DLT. Expansion enrolling."
                ),
            },
        ],
        data={
            "total_screened": _TOTAL_SCREENED,
            "enrolled": _ENROLLED_PATIENTS,
            "screen_failures": _SCREEN_FAILURES,
            "screen_failure_rate_pct": round(_SCREEN_FAILURES / _TOTAL_SCREENED * 100, 1),
            "sites": [
                {"id": "001", "name": "Academic Medical Center", "enrolled": 12, "screen_failures": 4},
                {"id": "002", "name": "Community Hospital", "enrolled": 9, "screen_failures": 3},
                {"id": "003", "name": "Research Institute", "enrolled": 7, "screen_failures": 2},
            ],
            "dose_levels_completed": 4,
            "total_dlts": 2,
        },
    )

    protocol_deviations = _make_deliverable(
        deliverable_id="clinops_protocol_deviations_v1",
        title="Protocol Deviation Summary -- AZ-CT-001",
        role_id="vp_clinops",
        category="compliance",
        regulatory_refs=["ICH_E6_R3", "21_CFR_312", "21_CFR_50"],
        status="final",
        sections=[
            {
                "heading": "Deviation Overview",
                "content": (
                    "Total deviations reported: 14. Major: 2. Minor: 12. "
                    "No deviations impacted patient safety or data integrity."
                ),
            },
            {
                "heading": "Categories",
                "content": (
                    "Informed consent timing: 3 (minor). "
                    "Lab window exceedances: 4 (minor). "
                    "Dose administration timing: 2 (1 major, 1 minor). "
                    "Concomitant medication violations: 3 (minor). "
                    "Missed assessments: 2 (1 major, 1 minor)."
                ),
            },
            {
                "heading": "Corrective Actions",
                "content": (
                    "Site-level retraining completed for Sites 001 and 003. "
                    "Protocol clarification amendment (Amendment 3) filed "
                    "to address lab window ambiguity."
                ),
            },
        ],
        data={
            "total_deviations": 14,
            "major": 2,
            "minor": 12,
            "by_category": {
                "informed_consent_timing": 3,
                "lab_window_exceedance": 4,
                "dose_administration_timing": 2,
                "concomitant_medication": 3,
                "missed_assessment": 2,
            },
            "sites_retrained": ["001", "003"],
            "amendment_filed": "Amendment 3",
        },
    )

    monitoring_schedule = _make_deliverable(
        deliverable_id="clinops_monitoring_schedule_v1",
        title="Monitoring Visit Schedule -- AZ-CT-001",
        role_id="vp_clinops",
        category="monitoring",
        regulatory_refs=["ICH_E6_R3", "21_CFR_312"],
        status="approved",
        sections=[
            {
                "heading": "Monitoring Strategy",
                "content": (
                    "Risk-based monitoring per ICH E6(R3). On-site visits "
                    "supplemented with centralized statistical monitoring. "
                    "Site visits every 4-6 weeks during active enrollment."
                ),
            },
            {
                "heading": "Visit Schedule",
                "content": (
                    "Site 001: 8 visits completed, next visit 2025-12-15. "
                    "Site 002: 7 visits completed, next visit 2025-12-10. "
                    "Site 003: 6 visits completed, next visit 2025-12-20."
                ),
            },
        ],
        data={
            "monitoring_type": "risk_based",
            "visit_frequency_weeks": "4-6",
            "visits_completed": {
                "001": 8,
                "002": 7,
                "003": 6,
            },
            "total_visits_completed": 21,
            "next_visits": {
                "001": "2025-12-15",
                "002": "2025-12-10",
                "003": "2025-12-20",
            },
        },
    )

    return [trial_status, protocol_deviations, monitoring_schedule]


# ---------------------------------------------------------------------------
# Head PV deliverables
# ---------------------------------------------------------------------------

def generate_pv_deliverables() -> list[dict[str, Any]]:
    """Generate Head of Pharmacovigilance deliverables.

    Produces an ICSR summary, signal detection results (PRR/ROR),
    a DSUR Year 1 outline, and an expedited reporting log.
    References ICH E2E for pharmacovigilance planning, ICH E2F for DSUR,
    and 21 CFR 312.32 for IND safety reporting.

    Returns:
        List of structured deliverable dicts.
    """
    icsr_summary = _make_deliverable(
        deliverable_id="pv_icsr_summary_v1",
        title="ICSR Summary Report -- AZ-CT-001",
        role_id="head_pv",
        category="safety_reporting",
        regulatory_refs=["ICH_E2B_R3", "ICH_E2A", "21_CFR_312_32"],
        status="final",
        sections=[
            {
                "heading": "Case Volume",
                "content": (
                    f"Total ICSRs received: {_TOTAL_ICSRS}. "
                    f"Serious: {_SERIOUS_ICSRS} ({round(_SERIOUS_ICSRS / _TOTAL_ICSRS * 100, 1)}%). "
                    f"Non-serious: {_NON_SERIOUS_ICSRS}. "
                    f"Expedited reports submitted: {_EXPEDITED_REPORTS}."
                ),
            },
            {
                "heading": "Serious Case Breakdown",
                "content": (
                    f"CRS Grade >= 3: {_CRS_CASES} cases. "
                    f"ICANS Grade >= 2: {_ICANS_CASES} cases. "
                    "Prolonged cytopenia: 2 cases. "
                    "Febrile neutropenia: 1 case. "
                    f"Deaths: {_DEATHS}."
                ),
            },
            {
                "heading": "Processing Metrics",
                "content": (
                    "Median time to initial receipt: 1.2 days. "
                    "Serious cases processed within 24h: 100%. "
                    "15-day IND safety reports filed on time: 100%."
                ),
            },
        ],
        data={
            "total_icsrs": _TOTAL_ICSRS,
            "serious": _SERIOUS_ICSRS,
            "non_serious": _NON_SERIOUS_ICSRS,
            "expedited_reports": _EXPEDITED_REPORTS,
            "crs_cases": _CRS_CASES,
            "icans_cases": _ICANS_CASES,
            "prolonged_cytopenia": 2,
            "febrile_neutropenia": 1,
            "deaths": _DEATHS,
            "median_receipt_days": 1.2,
            "serious_processed_24h_pct": 100.0,
            "fifteen_day_on_time_pct": 100.0,
        },
    )

    signal_detection = _make_deliverable(
        deliverable_id="pv_signal_detection_v1",
        title="Signal Detection Results -- AZ-CT-001 and FAERS Background",
        role_id="head_pv",
        category="signal_detection",
        regulatory_refs=["ICH_E2C_R2", "21_CFR_312_32", "CIOMS_V"],
        status="under_review",
        sections=[
            {
                "heading": "Signal Detection Methodology",
                "content": (
                    "Disproportionality analysis using Proportional Reporting "
                    "Ratio (PRR) and Reporting Odds Ratio (ROR) against FAERS "
                    "background rates for CAR-T products."
                ),
            },
            {
                "heading": "Signals Detected",
                "content": (
                    "CRS: PRR = 4.2 (95% CI: 2.8-6.3), ROR = 4.5 (95% CI: 2.9-7.0). "
                    "Expected signal for CAR-T class. "
                    "ICANS: PRR = 3.1 (95% CI: 1.4-6.8), ROR = 3.3 (95% CI: 1.5-7.2). "
                    "No unexpected signals identified."
                ),
            },
            {
                "heading": "Conclusion",
                "content": (
                    "All detected signals are consistent with known CAR-T "
                    "class effects. No new safety signals requiring regulatory "
                    "action. Continued routine surveillance recommended."
                ),
            },
        ],
        data={
            "signals": [
                {
                    "event": "Cytokine Release Syndrome",
                    "prr": 4.2,
                    "prr_ci_lower": 2.8,
                    "prr_ci_upper": 6.3,
                    "ror": 4.5,
                    "ror_ci_lower": 2.9,
                    "ror_ci_upper": 7.0,
                    "status": "known_class_effect",
                },
                {
                    "event": "ICANS",
                    "prr": 3.1,
                    "prr_ci_lower": 1.4,
                    "prr_ci_upper": 6.8,
                    "ror": 3.3,
                    "ror_ci_lower": 1.5,
                    "ror_ci_upper": 7.2,
                    "status": "known_class_effect",
                },
            ],
            "unexpected_signals": 0,
            "faers_background_source": "openFDA FAERS Q3 2025",
        },
    )

    dsur_outline = _make_deliverable(
        deliverable_id="pv_dsur_outline_v1",
        title="DSUR Year 1 Outline -- AZ-CT-001",
        role_id="head_pv",
        category="periodic_reporting",
        regulatory_refs=["ICH_E2F", "21_CFR_312"],
        status="draft",
        sections=[
            {
                "heading": "DSUR Header",
                "content": (
                    f"Reporting period: {_DSUR_DIB_DATE} to {_DSUR_REPORTING_PERIOD_END}. "
                    f"Development International Birth Date (DIBD): {_DSUR_DIB_DATE}. "
                    "Investigational product: AZ-CT-001 (autologous CD19 CAR-T)."
                ),
            },
            {
                "heading": "Section Outline per ICH E2F",
                "content": (
                    "1. Executive Summary. "
                    "2. Worldwide Marketing Approval Status (N/A -- investigational). "
                    "3. Actions Taken for Safety Reasons. "
                    "4. Changes to Reference Safety Information. "
                    "5. Ongoing and Completed Clinical Trials. "
                    "6. Estimated Cumulative Subject Exposure. "
                    "7. Data in Line Listings and Summary Tabulations. "
                    "8. Significant Findings from Clinical Trials. "
                    "9. Safety Findings from Non-Interventional Studies (N/A). "
                    "10. Other Safety Information. "
                    "11. Late-Breaking Information. "
                    "12. Overall Safety Assessment. "
                    "13. Summary of Important Risks. "
                    "14. Benefit-Risk Analysis. "
                    "Appendices: Line listings, IB changes, SAE narratives."
                ),
            },
            {
                "heading": "Key Data Points",
                "content": (
                    f"Cumulative exposure: {_ENROLLED_PATIENTS} patients. "
                    f"Total ICSRs: {_TOTAL_ICSRS}. "
                    f"Serious ICSRs: {_SERIOUS_ICSRS}. "
                    f"Expedited reports: {_EXPEDITED_REPORTS}. "
                    f"Deaths: {_DEATHS}."
                ),
            },
        ],
        data={
            "reporting_period_start": _DSUR_DIB_DATE,
            "reporting_period_end": _DSUR_REPORTING_PERIOD_END,
            "dibd": _DSUR_DIB_DATE,
            "cumulative_exposure": _ENROLLED_PATIENTS,
            "total_icsrs": _TOTAL_ICSRS,
            "serious_icsrs": _SERIOUS_ICSRS,
            "expedited_reports": _EXPEDITED_REPORTS,
            "deaths": _DEATHS,
            "dsur_sections_count": 14,
        },
    )

    expedited_log = _make_deliverable(
        deliverable_id="pv_expedited_log_v1",
        title="Expedited Safety Reporting Log -- AZ-CT-001",
        role_id="head_pv",
        category="safety_reporting",
        regulatory_refs=["21_CFR_312_32", "ICH_E2A"],
        status="final",
        sections=[
            {
                "heading": "Expedited Reports Filed",
                "content": (
                    f"Total expedited reports: {_EXPEDITED_REPORTS}. "
                    "All filed within regulatory timelines."
                ),
            },
        ],
        data={
            "reports": [
                {
                    "report_id": "EXP-001",
                    "event": "CRS Grade 4",
                    "report_type": "15-day IND safety report",
                    "date_aware": "2025-03-12",
                    "date_submitted": "2025-03-19",
                    "days_to_submit": 7,
                    "regulatory_ref": "21_CFR_312_32",
                    "outcome": "Resolved",
                },
                {
                    "report_id": "EXP-002",
                    "event": "ICANS Grade 3",
                    "report_type": "15-day IND safety report",
                    "date_aware": "2025-05-08",
                    "date_submitted": "2025-05-14",
                    "days_to_submit": 6,
                    "regulatory_ref": "21_CFR_312_32",
                    "outcome": "Resolved",
                },
                {
                    "report_id": "EXP-003",
                    "event": "Febrile Neutropenia Grade 3",
                    "report_type": "15-day IND safety report",
                    "date_aware": "2025-07-21",
                    "date_submitted": "2025-07-28",
                    "days_to_submit": 7,
                    "regulatory_ref": "21_CFR_312_32",
                    "outcome": "Resolved",
                },
            ],
            "total_expedited": _EXPEDITED_REPORTS,
            "all_on_time": True,
        },
    )

    return [icsr_summary, signal_detection, dsur_outline, expedited_log]


# ---------------------------------------------------------------------------
# VP Regulatory deliverables
# ---------------------------------------------------------------------------

def generate_regulatory_deliverables() -> list[dict[str, Any]]:
    """Generate VP Regulatory Affairs deliverables.

    Produces an IND annual report outline, an EOP2 meeting briefing
    document outline, and a regulatory submission timeline.
    References 21 CFR 312 for IND requirements and ICH M4 for CTD format.

    Returns:
        List of structured deliverable dicts.
    """
    ind_annual_report = _make_deliverable(
        deliverable_id="reg_ind_annual_report_v1",
        title="IND Annual Report Outline -- AZ-CT-001",
        role_id="vp_regulatory",
        category="regulatory_submission",
        regulatory_refs=["21_CFR_312", "ICH_M4"],
        status="draft",
        sections=[
            {
                "heading": "Report Scope",
                "content": (
                    "Annual report for IND 123456 covering the period "
                    "from IND effective date (2024-10-15) through "
                    "anniversary (2025-10-14). Per 21 CFR 312.33."
                ),
            },
            {
                "heading": "Required Content",
                "content": (
                    "1. Individual study information (AZ-CT-001 Phase I). "
                    "2. Summary of most frequent/serious AEs. "
                    "3. IND safety report summaries. "
                    "4. Subject enrollment (total and by study). "
                    "5. Completed/discontinued studies. "
                    "6. Investigator Brochure revisions. "
                    "7. Manufacturing changes. "
                    "8. General investigational plan for coming year. "
                    "9. Log of outstanding regulatory commitments."
                ),
            },
            {
                "heading": "Timeline",
                "content": (
                    "IND anniversary: 2025-10-15. "
                    "60-day filing deadline: 2025-12-14. "
                    "Target internal draft: 2025-11-15. "
                    "Target final: 2025-12-01."
                ),
            },
        ],
        data={
            "ind_number": "IND 123456",
            "ind_effective_date": "2024-10-15",
            "anniversary_date": "2025-10-15",
            "filing_deadline": "2025-12-14",
            "enrolled_during_period": _ENROLLED_PATIENTS,
            "safety_reports_filed": _EXPEDITED_REPORTS,
        },
    )

    eop2_briefing = _make_deliverable(
        deliverable_id="reg_eop2_briefing_v1",
        title="EOP2 Meeting Briefing Document Outline -- AZ-CT-001",
        role_id="vp_regulatory",
        category="regulatory_strategy",
        regulatory_refs=["21_CFR_312", "FDA_meetings", "ICH_M4"],
        status="planned",
        sections=[
            {
                "heading": "Meeting Objective",
                "content": (
                    "Discuss Phase II design, endpoints, and regulatory "
                    "pathway for accelerated approval. Obtain FDA agreement "
                    "on pivotal study design."
                ),
            },
            {
                "heading": "Briefing Document Sections",
                "content": (
                    "1. Product overview and mechanism of action. "
                    "2. Nonclinical summary. "
                    "3. Phase I results (safety, PK, preliminary efficacy). "
                    "4. CMC status and manufacturing scalability. "
                    "5. Proposed Phase II design and endpoints. "
                    "6. Proposed Phase III design (if discussed). "
                    "7. Specific questions for FDA."
                ),
            },
            {
                "heading": "Key Questions for FDA",
                "content": (
                    "Q1: Is complete B-cell depletion at Month 3 an acceptable "
                    "surrogate endpoint for accelerated approval? "
                    "Q2: Is a single-arm Phase II design acceptable given "
                    "the unmet medical need? "
                    "Q3: What post-marketing commitments would FDA anticipate?"
                ),
            },
        ],
        data={
            "meeting_type": "End-of-Phase-2",
            "target_request_date": "2026-Q3",
            "target_meeting_date": "2026-Q4",
            "fda_division": "CBER / Office of Tissues and Advanced Therapies",
            "questions_count": 3,
        },
    )

    submission_timeline = _make_deliverable(
        deliverable_id="reg_submission_timeline_v1",
        title="Regulatory Submission Timeline -- AZ-CT-001",
        role_id="vp_regulatory",
        category="regulatory_planning",
        regulatory_refs=["21_CFR_312", "21_CFR_601", "eCTD", "PDUFA"],
        status="approved",
        sections=[
            {
                "heading": "Milestone Timeline",
                "content": (
                    "IND filed: 2024-09. IND effective: 2024-10. "
                    "Phase I FIH start: 2024-11. "
                    "IND annual report: 2025-12. "
                    "Phase I completion: 2026-Q2 (projected). "
                    "EOP2 meeting request: 2026-Q3. "
                    "Phase II start: 2027-Q1 (projected). "
                    "BLA submission: 2029-Q4 (projected)."
                ),
            },
        ],
        data={
            "milestones": [
                {"event": "IND Filed", "date": "2024-09", "status": "completed"},
                {"event": "IND Effective", "date": "2024-10", "status": "completed"},
                {"event": "Phase I Start", "date": "2024-11", "status": "completed"},
                {"event": "IND Annual Report", "date": "2025-12", "status": "in_progress"},
                {"event": "Phase I Completion", "date": "2026-Q2", "status": "projected"},
                {"event": "EOP2 Meeting Request", "date": "2026-Q3", "status": "projected"},
                {"event": "Phase II Start", "date": "2027-Q1", "status": "projected"},
                {"event": "BLA Submission", "date": "2029-Q4", "status": "projected"},
            ],
        },
    )

    return [ind_annual_report, eop2_briefing, submission_timeline]


# ---------------------------------------------------------------------------
# Head Biostats deliverables
# ---------------------------------------------------------------------------

def generate_biostats_deliverables() -> list[dict[str, Any]]:
    """Generate Head of Biostatistics deliverables.

    Produces a SAP summary (3+3 dose escalation design), DLT analysis
    framework, sample size calculations for Phase II, and interim analysis
    plan. References ICH E9(R1) for estimands and statistical principles.

    Returns:
        List of structured deliverable dicts.
    """
    sap_summary = _make_deliverable(
        deliverable_id="biostats_sap_v1",
        title="Statistical Analysis Plan Summary -- AZ-CT-001 Phase I",
        role_id="head_biostats",
        category="biostatistics",
        regulatory_refs=["ICH_E9", "ICH_E9_R1", "ICH_E6_R3"],
        status="approved",
        sections=[
            {
                "heading": "Study Design",
                "content": (
                    f"3+3 dose escalation with {_DOSE_LEVELS} planned dose levels. "
                    f"DLT observation window: {_DLT_WINDOW_DAYS} days. "
                    "Dose escalation decisions based on DLT rate per cohort."
                ),
            },
            {
                "heading": "Primary Estimand (ICH E9(R1))",
                "content": (
                    "Treatment: AZ-CT-001 single infusion. "
                    "Population: Adult SLE patients meeting eligibility criteria. "
                    "Variable: Incidence of DLTs within 28-day window. "
                    "Population-level summary: DLT rate per dose level. "
                    "Intercurrent event strategy: Treatment policy."
                ),
            },
            {
                "heading": "Analysis Populations",
                "content": (
                    "Safety population: All patients receiving any amount of "
                    "AZ-CT-001. DLT-evaluable: Patients completing full DLT "
                    "window or experiencing DLT. Efficacy-evaluable: Safety "
                    "population with >= 1 post-baseline assessment."
                ),
            },
            {
                "heading": "Dose Escalation Rules",
                "content": (
                    "0/3 DLTs: Escalate to next dose level. "
                    "1/3 DLTs: Expand cohort to 6 patients. "
                    "1/6 DLTs: Escalate to next dose level. "
                    ">= 2/6 DLTs: Dose exceeds MTD, de-escalate. "
                    "MTD = highest dose with DLT rate < 33%."
                ),
            },
        ],
        data={
            "design": "3+3 dose escalation",
            "dose_levels": _DOSE_LEVELS,
            "dlt_window_days": _DLT_WINDOW_DAYS,
            "patients_per_cohort_min": 3,
            "patients_per_cohort_max": 6,
            "mtd_threshold_pct": 33.3,
            "total_enrolled": _ENROLLED_PATIENTS,
            "total_dlts": 2,
        },
    )

    dlt_analysis = _make_deliverable(
        deliverable_id="biostats_dlt_analysis_v1",
        title="DLT Analysis Framework -- AZ-CT-001",
        role_id="head_biostats",
        category="biostatistics",
        regulatory_refs=["ICH_E9", "FDA_adaptive_design"],
        status="final",
        sections=[
            {
                "heading": "DLT Definition",
                "content": (
                    "Grade >= 4 CRS lasting > 72 hours despite tocilizumab. "
                    "Grade >= 3 ICANS lasting > 5 days. "
                    "Grade >= 4 neutropenia lasting > 21 days. "
                    "Grade >= 3 non-hematologic toxicity (excluding CRS/ICANS). "
                    "Treatment-related death."
                ),
            },
            {
                "heading": "DLT Results by Dose Level",
                "content": (
                    "DL1: 0/3 DLTs (0%). "
                    "DL2: 0/3 DLTs (0%). "
                    "DL3: 1/6 DLTs (16.7%) -- Grade 4 CRS, resolved. "
                    "DL4: 1/3 DLTs (33.3%) -- Grade 3 prolonged neutropenia."
                ),
            },
            {
                "heading": "Bayesian Posterior DLT Rates",
                "content": (
                    "Using Beta(0.5, 0.5) Jeffreys prior. "
                    "DL1: posterior mean 0.10 (95% CrI: 0.003-0.41). "
                    "DL2: posterior mean 0.10 (95% CrI: 0.003-0.41). "
                    "DL3: posterior mean 0.19 (95% CrI: 0.04-0.43). "
                    "DL4: posterior mean 0.36 (95% CrI: 0.08-0.70)."
                ),
            },
        ],
        data={
            "dlt_by_dose_level": [
                {"level": "DL1", "n": 3, "dlts": 0, "rate_pct": 0.0},
                {"level": "DL2", "n": 3, "dlts": 0, "rate_pct": 0.0},
                {"level": "DL3", "n": 6, "dlts": 1, "rate_pct": 16.7},
                {"level": "DL4", "n": 3, "dlts": 1, "rate_pct": 33.3},
            ],
            "total_dlts": 2,
            "total_evaluable": 15,
            "bayesian_prior": "Beta(0.5, 0.5)",
        },
    )

    sample_size = _make_deliverable(
        deliverable_id="biostats_sample_size_v1",
        title="Phase II Sample Size Calculations -- AZ-CT-001",
        role_id="head_biostats",
        category="biostatistics",
        regulatory_refs=["ICH_E9", "ICH_E9_R1"],
        status="draft",
        sections=[
            {
                "heading": "Primary Endpoint",
                "content": (
                    "Complete B-cell depletion at Month 3, assessed by flow "
                    "cytometry (CD19+ cells < 1/uL)."
                ),
            },
            {
                "heading": "Assumptions",
                "content": (
                    "Expected response rate: 70% (based on Phase I preliminary data "
                    "and published CAR-T SLE literature). "
                    "Null hypothesis rate: 40% (historical standard-of-care). "
                    "Alpha: 0.025 (one-sided). Power: 90%. "
                    "Dropout rate: 10%."
                ),
            },
            {
                "heading": "Result",
                "content": (
                    "Required evaluable: 36 patients. "
                    "With 10% dropout adjustment: 40 patients. "
                    "Method: exact binomial test (single-arm)."
                ),
            },
        ],
        data={
            "primary_endpoint": "Complete B-cell depletion at Month 3",
            "expected_rate": 0.70,
            "null_rate": 0.40,
            "alpha_one_sided": 0.025,
            "power": 0.90,
            "dropout_rate": 0.10,
            "n_evaluable": 36,
            "n_enrolled": 40,
            "method": "exact_binomial_single_arm",
        },
    )

    interim_plan = _make_deliverable(
        deliverable_id="biostats_interim_plan_v1",
        title="Interim Analysis Plan -- AZ-CT-001 Phase II",
        role_id="head_biostats",
        category="biostatistics",
        regulatory_refs=["ICH_E9", "ICH_E9_R1", "FDA_adaptive_design"],
        status="draft",
        sections=[
            {
                "heading": "Interim Analysis Design",
                "content": (
                    "One planned interim analysis at 50% information fraction "
                    "(20 evaluable patients). O'Brien-Fleming spending function "
                    "to control type I error."
                ),
            },
            {
                "heading": "Stopping Rules",
                "content": (
                    "Futility: Stop if conditional power < 10%. "
                    "Efficacy: Interim p-value < 0.003 (O'Brien-Fleming). "
                    "Safety: DSMB may recommend halt if DLT rate > 33% "
                    "at RP2D."
                ),
            },
        ],
        data={
            "interim_count": 1,
            "information_fraction": 0.50,
            "interim_n": 20,
            "spending_function": "OBrien_Fleming",
            "futility_conditional_power_threshold": 0.10,
            "efficacy_interim_alpha": 0.003,
            "final_alpha": 0.024,
        },
    )

    return [sap_summary, dlt_analysis, sample_size, interim_plan]


# ---------------------------------------------------------------------------
# Head CMC deliverables
# ---------------------------------------------------------------------------

def generate_cmc_deliverables() -> list[dict[str, Any]]:
    """Generate Head of CMC / Manufacturing deliverables.

    Produces a manufacturing batch summary (23 batches, 21 released, 2 failed),
    release testing panel results, stability data summary, and process
    validation status. References 21 CFR 1271 for HCT/Ps and ICH Q5E
    for comparability.

    Returns:
        List of structured deliverable dicts.
    """
    qm = get_quality_metrics()

    batch_summary = _make_deliverable(
        deliverable_id="cmc_batch_summary_v1",
        title="Manufacturing Batch Summary -- AZ-CT-001",
        role_id="head_cmc",
        category="manufacturing",
        regulatory_refs=["21_CFR_1271", "21_CFR_210", "21_CFR_211", "21_CFR_600"],
        status="final",
        sections=[
            {
                "heading": "Batch Overview",
                "content": (
                    f"Total batches manufactured: {qm['batches']['manufactured_ytd']}. "
                    f"Released: {qm['batches']['released']}. "
                    f"Failed: {qm['batches']['failed']}. "
                    f"Failure rate: {qm['batches']['failure_rate_pct']}%."
                ),
            },
            {
                "heading": "Failure Analysis",
                "content": (
                    "Batch F-017: Failed viability specification (< 70% threshold). "
                    "Root cause: Extended apheresis-to-manufacturing interval (> 48h). "
                    "Batch F-022: Failed sterility testing (Staphylococcus epidermidis). "
                    "Root cause: Environmental monitoring excursion in clean room."
                ),
            },
            {
                "heading": "Manufacturing Metrics",
                "content": (
                    "Median vein-to-vein time: 21 days. "
                    "Median transduction efficiency: 42%. "
                    "Median CAR+ cell dose: 1.5 x 10^6 CAR+ cells/kg."
                ),
            },
        ],
        data={
            "total_batches": qm["batches"]["manufactured_ytd"],
            "released": qm["batches"]["released"],
            "failed": qm["batches"]["failed"],
            "failure_rate_pct": qm["batches"]["failure_rate_pct"],
            "failed_batches": [
                {
                    "batch_id": "F-017",
                    "failure_reason": "Viability below specification (< 70%)",
                    "root_cause": "Extended apheresis-to-manufacturing interval",
                },
                {
                    "batch_id": "F-022",
                    "failure_reason": "Sterility failure (S. epidermidis)",
                    "root_cause": "Environmental monitoring excursion",
                },
            ],
            "median_vein_to_vein_days": 21,
            "median_transduction_efficiency_pct": 42,
            "median_car_plus_dose": "1.5e6 cells/kg",
        },
    )

    release_testing = _make_deliverable(
        deliverable_id="cmc_release_testing_v1",
        title="Release Testing Panel Results -- AZ-CT-001",
        role_id="head_cmc",
        category="quality_control",
        regulatory_refs=["ICH_Q6B", "ICH_Q2", "21_CFR_610"],
        status="final",
        sections=[
            {
                "heading": "Release Testing Panel",
                "content": (
                    "Specifications per IND filing (Module 3.2.S.4.1). "
                    "All released lots met all specifications."
                ),
            },
        ],
        data={
            "tests": [
                {"test": "Cell Viability", "specification": ">= 70%", "results_range": "72-95%", "pass_rate_pct": 91.3},
                {"test": "CAR Expression (% CD3+CAR+)", "specification": ">= 20%", "results_range": "28-68%", "pass_rate_pct": 100.0},
                {"test": "Sterility (USP <71>)", "specification": "No growth 14 days", "results_range": "Pass/Fail", "pass_rate_pct": 95.7},
                {"test": "Endotoxin (LAL)", "specification": "< 5 EU/mL", "results_range": "0.1-2.3 EU/mL", "pass_rate_pct": 100.0},
                {"test": "Mycoplasma (PCR)", "specification": "Not detected", "results_range": "Pass/Fail", "pass_rate_pct": 100.0},
                {"test": "Identity (Flow Cytometry)", "specification": "CD3+CAR+ confirmed", "results_range": "Pass/Fail", "pass_rate_pct": 100.0},
                {"test": "Potency (Cytotoxicity Assay)", "specification": ">= 30% lysis at 10:1 E:T", "results_range": "35-78% lysis", "pass_rate_pct": 100.0},
                {"test": "Residual Beads", "specification": "< 100 beads/3x10^6 cells", "results_range": "0-45 beads", "pass_rate_pct": 100.0},
            ],
        },
    )

    stability_data = _make_deliverable(
        deliverable_id="cmc_stability_v1",
        title="Stability Data Summary -- AZ-CT-001",
        role_id="head_cmc",
        category="stability",
        regulatory_refs=["ICH_Q1A", "ICH_Q5E"],
        status="under_review",
        sections=[
            {
                "heading": "Stability Study Design",
                "content": (
                    "Cryopreserved product stored in controlled-rate freezer "
                    "bags at -150 C (vapor-phase LN2). Stability assessed at "
                    "0, 1, 3, 6, and 12 months."
                ),
            },
            {
                "heading": "Results Summary",
                "content": (
                    "12-month data available for 8 lots. All lots maintain "
                    "viability > 70% and potency > 30% lysis through 12 months. "
                    "No significant trend in CAR expression decline."
                ),
            },
        ],
        data={
            "storage_condition": "-150C vapor-phase LN2",
            "timepoints_months": [0, 1, 3, 6, 12],
            "lots_with_12month_data": 8,
            "viability_12month_range": "73-89%",
            "potency_12month_range": "33-72% lysis",
            "car_expression_12month_range": "25-61%",
            "proposed_shelf_life_months": 18,
            "shelf_life_justification": "Extrapolation from 12-month data per ICH Q1E",
        },
    )

    process_validation = _make_deliverable(
        deliverable_id="cmc_process_validation_v1",
        title="Process Validation Status -- AZ-CT-001",
        role_id="head_cmc",
        category="manufacturing",
        regulatory_refs=["21_CFR_211", "ICH_Q8", "ICH_Q11"],
        status="in_progress",
        sections=[
            {
                "heading": "Validation Strategy",
                "content": (
                    "Stage 1 (Process Design): Complete. Design space established "
                    "via DOE for transduction parameters. "
                    "Stage 2 (Process Qualification): In progress. 3 consecutive "
                    "PPQ lots planned; 2 of 3 completed. "
                    "Stage 3 (Continued Process Verification): Planned post-PPQ."
                ),
            },
            {
                "heading": "CPPs and CQAs",
                "content": (
                    "Critical Process Parameters: Transduction MOI (3-10), "
                    "expansion duration (9-14 days), activation bead ratio (1:1 to 3:1). "
                    "Critical Quality Attributes: Viability, CAR expression, "
                    "potency, sterility, endotoxin."
                ),
            },
        ],
        data={
            "stage1_status": "complete",
            "stage2_status": "in_progress",
            "stage2_lots_completed": 2,
            "stage2_lots_planned": 3,
            "stage3_status": "planned",
            "critical_process_parameters": [
                "Transduction MOI",
                "Expansion duration",
                "Activation bead ratio",
            ],
            "critical_quality_attributes": [
                "Viability",
                "CAR expression",
                "Potency",
                "Sterility",
                "Endotoxin",
            ],
        },
    )

    return [batch_summary, release_testing, stability_data, process_validation]


# ---------------------------------------------------------------------------
# Head QA deliverables
# ---------------------------------------------------------------------------

def generate_qa_deliverables() -> list[dict[str, Any]]:
    """Generate Head of Quality Assurance deliverables.

    Produces a CAPA tracker with root cause categories, deviation trend
    analysis, audit schedule/findings, training compliance dashboard data,
    and GxP compliance matrix. References ICH Q9, Q10, and ALCOA+ principles.

    Returns:
        List of structured deliverable dicts.
    """
    qm = get_quality_metrics()

    capa_tracker = _make_deliverable(
        deliverable_id="qa_capa_tracker_v1",
        title="CAPA Tracker -- AZ-CT-001 Manufacturing and Clinical",
        role_id="head_qa",
        category="quality_management",
        regulatory_refs=["ICH_Q10", "21_CFR_211", "21_CFR_600"],
        status="final",
        sections=[
            {
                "heading": "CAPA Summary",
                "content": (
                    f"Open CAPAs: {qm['capa']['open']}. "
                    f"Overdue: {qm['capa']['overdue']}. "
                    f"Closed YTD: {qm['capa']['closed_ytd']}. "
                    f"Average closure time: {qm['capa']['avg_closure_days']} days."
                ),
            },
        ],
        data={
            "open": qm["capa"]["open"],
            "overdue": qm["capa"]["overdue"],
            "closed_ytd": qm["capa"]["closed_ytd"],
            "avg_closure_days": qm["capa"]["avg_closure_days"],
            "root_cause_categories": {
                "human_error": 5,
                "equipment_malfunction": 3,
                "sop_inadequacy": 4,
                "environmental": 2,
                "material_supplier": 3,
            },
            "capas": [
                {"id": "CAPA-001", "description": "Sterility failure in Batch F-022", "root_cause": "environmental", "status": "open", "days_open": 30},
                {"id": "CAPA-002", "description": "Missed monitoring visit at Site 003", "root_cause": "human_error", "status": "open", "days_open": 22},
                {"id": "CAPA-003", "description": "Apheresis shipping delay > 48h", "root_cause": "material_supplier", "status": "open", "days_open": 15},
                {"id": "CAPA-004", "description": "EDC data entry error trend", "root_cause": "sop_inadequacy", "status": "open", "days_open": 10},
                {"id": "CAPA-005", "description": "Equipment calibration overdue", "root_cause": "equipment_malfunction", "status": "overdue", "days_open": 52},
            ],
        },
    )

    deviation_trends = _make_deliverable(
        deliverable_id="qa_deviation_trends_v1",
        title="Deviation Trend Analysis -- 2025 YTD",
        role_id="head_qa",
        category="quality_management",
        regulatory_refs=["ICH_Q10", "ICH_Q9"],
        status="final",
        sections=[
            {
                "heading": "Deviation Summary",
                "content": (
                    f"Open deviations: {qm['deviations']['open']}. "
                    f"Closed YTD: {qm['deviations']['closed_ytd']}. "
                    f"Critical: {qm['deviations']['critical']}."
                ),
            },
            {
                "heading": "Trend Analysis",
                "content": (
                    "Q1 2025: 5 deviations (3 closed). "
                    "Q2 2025: 7 deviations (6 closed). "
                    "Q3 2025: 6 deviations (5 closed). "
                    "Q4 2025 (to date): 2 deviations (3 closed from prior quarters). "
                    "Downward trend in open deviations. "
                    "No recurring root cause pattern above threshold."
                ),
            },
        ],
        data={
            "open": qm["deviations"]["open"],
            "closed_ytd": qm["deviations"]["closed_ytd"],
            "critical": qm["deviations"]["critical"],
            "by_quarter": {
                "Q1_2025": {"opened": 5, "closed": 3},
                "Q2_2025": {"opened": 7, "closed": 6},
                "Q3_2025": {"opened": 6, "closed": 5},
                "Q4_2025": {"opened": 2, "closed": 3},
            },
            "total_opened_ytd": 20,
            "total_closed_ytd": 17,
        },
    )

    audit_schedule = _make_deliverable(
        deliverable_id="qa_audit_schedule_v1",
        title="Audit Schedule and Findings -- 2025",
        role_id="head_qa",
        category="audit",
        regulatory_refs=["ICH_Q10", "ICH_Q9", "21_CFR_211"],
        status="final",
        sections=[
            {
                "heading": "Audit Program",
                "content": (
                    f"Scheduled YTD: {qm['audits']['scheduled_ytd']}. "
                    f"Completed: {qm['audits']['completed']}. "
                    f"Open findings: {qm['audits']['findings_open']}. "
                    f"Critical findings: {qm['audits']['critical_findings']}."
                ),
            },
        ],
        data={
            "scheduled_ytd": qm["audits"]["scheduled_ytd"],
            "completed": qm["audits"]["completed"],
            "findings_open": qm["audits"]["findings_open"],
            "critical_findings": qm["audits"]["critical_findings"],
            "audits": [
                {
                    "id": "AUD-2025-001",
                    "type": "Internal GMP",
                    "target": "Manufacturing facility",
                    "date": "2025-03-15",
                    "status": "completed",
                    "findings": 4,
                    "critical": 0,
                },
                {
                    "id": "AUD-2025-002",
                    "type": "Internal GCP",
                    "target": "Clinical sites (001, 002)",
                    "date": "2025-06-20",
                    "status": "completed",
                    "findings": 3,
                    "critical": 0,
                },
                {
                    "id": "AUD-2025-003",
                    "type": "Vendor qualification",
                    "target": "Apheresis supplier",
                    "date": "2025-10-15",
                    "status": "scheduled",
                    "findings": 0,
                    "critical": 0,
                },
                {
                    "id": "AUD-2025-004",
                    "type": "Internal data integrity",
                    "target": "EDC system and TMF",
                    "date": "2025-12-01",
                    "status": "scheduled",
                    "findings": 0,
                    "critical": 0,
                },
            ],
        },
    )

    training_compliance = _make_deliverable(
        deliverable_id="qa_training_compliance_v1",
        title="Training Compliance Dashboard Data -- 2025",
        role_id="head_qa",
        category="training",
        regulatory_refs=["ICH_Q10", "21_CFR_211"],
        status="final",
        sections=[
            {
                "heading": "Training Metrics",
                "content": (
                    f"Overall compliance: {qm['training']['compliance_pct']}%. "
                    f"Overdue assignments: {qm['training']['overdue_assignments']}."
                ),
            },
        ],
        data={
            "compliance_pct": qm["training"]["compliance_pct"],
            "overdue_assignments": qm["training"]["overdue_assignments"],
            "by_department": {
                "manufacturing": {"compliance_pct": 96.5, "overdue": 2},
                "quality": {"compliance_pct": 98.0, "overdue": 1},
                "clinical_ops": {"compliance_pct": 91.0, "overdue": 3},
                "regulatory": {"compliance_pct": 93.5, "overdue": 2},
            },
            "curricula_count": 12,
            "total_assignments_ytd": 340,
        },
    )

    gxp_matrix = _make_deliverable(
        deliverable_id="qa_gxp_matrix_v1",
        title="GxP Compliance Matrix -- AZ-CT-001",
        role_id="head_qa",
        category="compliance",
        regulatory_refs=["ICH_Q9", "ICH_Q10", "21_CFR_210", "21_CFR_211", "ICH_E6_R3"],
        status="approved",
        sections=[
            {
                "heading": "Compliance Matrix Overview",
                "content": (
                    "GMP, GCP, GLP, and GDP compliance status across all "
                    "functions. ALCOA+ (Attributable, Legible, Contemporaneous, "
                    "Original, Accurate + Complete, Consistent, Enduring, Available) "
                    "data integrity principles applied throughout."
                ),
            },
        ],
        data={
            "gxp_areas": [
                {"area": "GMP", "status": "compliant", "last_assessment": "2025-03-15", "findings": 4, "critical": 0},
                {"area": "GCP", "status": "compliant", "last_assessment": "2025-06-20", "findings": 3, "critical": 0},
                {"area": "GLP", "status": "compliant", "last_assessment": "2024-06-01", "findings": 0, "critical": 0},
                {"area": "GDP", "status": "compliant", "last_assessment": "2025-09-01", "findings": 1, "critical": 0},
            ],
            "alcoa_plus_assessment": "compliant",
            "data_integrity_score": 94.5,
        },
    )

    return [capa_tracker, deviation_trends, audit_schedule, training_compliance, gxp_matrix]


# ---------------------------------------------------------------------------
# VP Medical Affairs deliverables
# ---------------------------------------------------------------------------

def generate_medaffairs_deliverables() -> list[dict[str, Any]]:
    """Generate VP of Medical Affairs deliverables.

    Produces a publication plan (3-year rolling), KOL engagement tracker,
    SAB minutes summary, and congress activity plan.
    References GPP 2022 (Good Publication Practice) and PhRMA Code.

    Returns:
        List of structured deliverable dicts.
    """
    publication_plan = _make_deliverable(
        deliverable_id="medaffairs_pub_plan_v1",
        title="Publication Plan (3-Year Rolling) -- AZ-CT-001",
        role_id="vp_med_affairs",
        category="publications",
        regulatory_refs=["PhRMA_Code", "ICH_E6_R3"],
        status="approved",
        sections=[
            {
                "heading": "Publication Strategy",
                "content": (
                    "Three-year rolling plan aligned with clinical development "
                    "milestones. All publications follow Good Publication "
                    "Practice (GPP 2022) guidelines."
                ),
            },
        ],
        data={
            "publications_planned": [
                {
                    "id": "PUB-001",
                    "type": "congress_abstract",
                    "title": "Phase I dose-escalation safety results (interim)",
                    "target_congress": "ASH Annual Meeting 2025",
                    "target_date": "2025-12",
                    "status": "submitted",
                    "lead_author": "Principal Investigator, Site 001",
                },
                {
                    "id": "PUB-002",
                    "type": "peer_reviewed_manuscript",
                    "title": "AZ-CT-001 Phase I final safety and efficacy results",
                    "target_journal": "New England Journal of Medicine",
                    "target_date": "2026-Q3",
                    "status": "planned",
                    "lead_author": "Principal Investigator, Site 001",
                },
                {
                    "id": "PUB-003",
                    "type": "congress_presentation",
                    "title": "Correlative biomarker analysis from Phase I",
                    "target_congress": "ACR Annual Meeting 2026",
                    "target_date": "2026-11",
                    "status": "planned",
                    "lead_author": "Translational Science Lead",
                },
                {
                    "id": "PUB-004",
                    "type": "peer_reviewed_manuscript",
                    "title": "CMC and manufacturing experience for autologous CAR-T in SLE",
                    "target_journal": "Cytotherapy",
                    "target_date": "2027-Q1",
                    "status": "planned",
                    "lead_author": "Head of CMC",
                },
                {
                    "id": "PUB-005",
                    "type": "peer_reviewed_manuscript",
                    "title": "Phase II results: B-cell depletion and SRI response",
                    "target_journal": "The Lancet Rheumatology",
                    "target_date": "2028-Q1",
                    "status": "planned",
                    "lead_author": "Principal Investigator",
                },
            ],
            "total_planned": 5,
            "gpp_compliant": True,
        },
    )

    kol_tracker = _make_deliverable(
        deliverable_id="medaffairs_kol_tracker_v1",
        title="KOL Engagement Tracker -- Autoimmune CAR-T",
        role_id="vp_med_affairs",
        category="medical_affairs",
        regulatory_refs=["PhRMA_Code", "FDCA_502"],
        status="final",
        sections=[
            {
                "heading": "KOL Engagement Summary",
                "content": (
                    "12 key opinion leaders identified across rheumatology "
                    "and cell therapy. 8 engaged to date. All interactions "
                    "compliant with PhRMA Code and fair market value."
                ),
            },
        ],
        data={
            "kols_identified": 12,
            "kols_engaged": 8,
            "engagement_types": {
                "advisory_board": 4,
                "consultant": 2,
                "speaker": 1,
                "investigator": 6,
            },
            "interactions_ytd": 18,
            "phrama_compliant": True,
        },
    )

    sab_minutes = _make_deliverable(
        deliverable_id="medaffairs_sab_minutes_v1",
        title="Scientific Advisory Board Minutes Summary -- Q3 2025",
        role_id="vp_med_affairs",
        category="governance",
        regulatory_refs=["PhRMA_Code"],
        status="final",
        sections=[
            {
                "heading": "Meeting Summary",
                "content": (
                    "SAB convened 2025-09-15 with 6 external advisors. "
                    "Topics: Phase I interim data review, Phase II design, "
                    "biomarker strategy, competitive landscape."
                ),
            },
            {
                "heading": "Key Recommendations",
                "content": (
                    "1. Consider B-cell depletion kinetics as pharmacodynamic endpoint. "
                    "2. Include patient-reported outcomes (PROs) in Phase II. "
                    "3. Explore lupus nephritis as second indication. "
                    "4. Strengthen manufacturing scalability before Phase II."
                ),
            },
        ],
        data={
            "meeting_date": "2025-09-15",
            "attendees_external": 6,
            "attendees_internal": 5,
            "topics": [
                "Phase I interim data review",
                "Phase II design",
                "Biomarker strategy",
                "Competitive landscape",
            ],
            "recommendations_count": 4,
            "next_meeting": "2026-03-15",
        },
    )

    congress_plan = _make_deliverable(
        deliverable_id="medaffairs_congress_plan_v1",
        title="Congress Activity Plan -- 2025/2026",
        role_id="vp_med_affairs",
        category="medical_affairs",
        regulatory_refs=["PhRMA_Code"],
        status="approved",
        sections=[
            {
                "heading": "Congress Strategy",
                "content": (
                    "Targeted presence at 4 major congresses per year. "
                    "Focus on rheumatology and cell therapy conferences."
                ),
            },
        ],
        data={
            "congresses": [
                {"name": "ASH Annual Meeting", "date": "2025-12", "activity": "Abstract presentation", "status": "confirmed"},
                {"name": "ACR Convergence", "date": "2025-11", "activity": "Scientific exhibit", "status": "confirmed"},
                {"name": "EBMT Annual Meeting", "date": "2026-03", "activity": "Poster presentation", "status": "planned"},
                {"name": "EULAR Congress", "date": "2026-06", "activity": "Oral presentation (if accepted)", "status": "planned"},
            ],
            "annual_congress_budget_usd": 450000,
        },
    )

    return [publication_plan, kol_tracker, sab_minutes, congress_plan]


# ---------------------------------------------------------------------------
# Head Clinical Development deliverables
# ---------------------------------------------------------------------------

def generate_clindev_deliverables() -> list[dict[str, Any]]:
    """Generate Head of Clinical Development deliverables.

    Produces a clinical development plan summary, target product profile,
    and indication sequencing rationale. References ICH E8(R1) for general
    clinical study considerations.

    Returns:
        List of structured deliverable dicts.
    """
    cdp_summary = _make_deliverable(
        deliverable_id="clindev_cdp_summary_v1",
        title="Clinical Development Plan Summary -- AZ-CT-001",
        role_id="head_clindev",
        category="development_strategy",
        regulatory_refs=["ICH_E8_R1", "21_CFR_312", "CBER_early_phase"],
        status="approved",
        sections=[
            {
                "heading": "Program Overview",
                "content": (
                    "Autologous CD19 CAR-T for refractory SLE. "
                    "Three-phase development with accelerated approval pathway. "
                    "Breakthrough therapy designation sought post-Phase I."
                ),
            },
            {
                "heading": "Development Milestones",
                "content": (
                    "Phase I (current): Dose escalation, safety, RP2D determination. "
                    "Phase II: Single-arm efficacy at RP2D. "
                    "Phase III: Randomized vs. standard of care. "
                    "BLA submission targeted 2029-Q4."
                ),
            },
            {
                "heading": "Regulatory Strategy",
                "content": (
                    "FDA pathway: BLA under PHS Act 351(a). "
                    "Accelerated approval via surrogate endpoint (B-cell depletion). "
                    "Post-marketing confirmatory study required."
                ),
            },
        ],
        data={
            "indication": "Systemic Lupus Erythematosus",
            "regulatory_pathway": "BLA / PHS Act 351(a) / Accelerated Approval",
            "breakthrough_designation": "to_be_requested",
            "phases": [
                {"phase": "I", "status": "in_progress", "n_target": 30, "n_enrolled": _ENROLLED_PATIENTS},
                {"phase": "II", "status": "planned", "n_target": 40, "n_enrolled": 0},
                {"phase": "III", "status": "planned", "n_target": 200, "n_enrolled": 0},
            ],
            "bla_target": "2029-Q4",
        },
    )

    tpp = _make_deliverable(
        deliverable_id="clindev_tpp_v1",
        title="Target Product Profile -- AZ-CT-001",
        role_id="head_clindev",
        category="development_strategy",
        regulatory_refs=["ICH_E8_R1", "ICH_E6_R3"],
        status="draft",
        sections=[
            {
                "heading": "Target Product Profile",
                "content": (
                    "Indication: Adult patients with refractory SLE who have "
                    "failed >= 2 prior therapies including a biologic. "
                    "Dosing: Single IV infusion of autologous CD19 CAR-T cells. "
                    "Primary endpoint: Complete B-cell depletion and SRI-4 response."
                ),
            },
        ],
        data={
            "indication": "Refractory SLE (failed >= 2 prior therapies including biologic)",
            "dosing": "Single IV infusion",
            "target_population": "Adults >= 18 years",
            "primary_efficacy_endpoint": "SRI-4 response at Week 52",
            "key_secondary_endpoints": [
                "Complete B-cell depletion at Month 3",
                "Steroid-free remission at Month 12",
                "Organ damage prevention (SLICC/ACR Damage Index)",
            ],
            "safety_profile_target": "Manageable CRS (Grade <= 2 in > 80% of patients)",
            "competitive_differentiation": "One-time treatment vs. chronic biologic therapy",
        },
    )

    indication_sequencing = _make_deliverable(
        deliverable_id="clindev_indication_seq_v1",
        title="Indication Sequencing Rationale -- CD19 CAR-T Autoimmune Program",
        role_id="head_clindev",
        category="development_strategy",
        regulatory_refs=["ICH_E8_R1", "21_CFR_312"],
        status="draft",
        sections=[
            {
                "heading": "Lead Indication: SLE",
                "content": (
                    "Rationale: Highest unmet need, published CD19 CAR-T data "
                    "(Mackensen et al., NEJM 2022), clear regulatory pathway "
                    "with FDA breakthrough therapy precedent."
                ),
            },
            {
                "heading": "Second Indication: Lupus Nephritis",
                "content": (
                    "Rationale: Natural extension of SLE, overlapping "
                    "pathophysiology, same target (CD19+ B cells). "
                    "Could leverage Phase II SLE data for IND expansion."
                ),
            },
            {
                "heading": "Third Indication: Systemic Sclerosis",
                "content": (
                    "Rationale: B-cell mediated fibrotic autoimmune disease. "
                    "Emerging preclinical evidence for CD19 CAR-T benefit. "
                    "Requires separate Phase I dose-finding."
                ),
            },
        ],
        data={
            "indications": [
                {"rank": 1, "indication": "Systemic Lupus Erythematosus", "status": "Phase I in progress", "rationale": "Highest unmet need, published data"},
                {"rank": 2, "indication": "Lupus Nephritis", "status": "Planned (IND expansion)", "rationale": "Natural SLE extension, same target"},
                {"rank": 3, "indication": "Systemic Sclerosis", "status": "Preclinical evaluation", "rationale": "B-cell mediated, emerging evidence"},
            ],
        },
    )

    return [cdp_summary, tpp, indication_sequencing]


# ---------------------------------------------------------------------------
# Head Commercial deliverables
# ---------------------------------------------------------------------------

def generate_commercial_deliverables() -> list[dict[str, Any]]:
    """Generate Head of Commercial / Market Access deliverables.

    Produces a market landscape analysis, competitive intelligence summary,
    and early access program considerations.
    References PhRMA Code for commercial conduct.

    Returns:
        List of structured deliverable dicts.
    """
    market_landscape = _make_deliverable(
        deliverable_id="commercial_market_landscape_v1",
        title="Market Landscape Analysis -- CAR-T in Autoimmune Diseases",
        role_id="head_commercial",
        category="commercial",
        regulatory_refs=["PhRMA_Code", "FDCA_502"],
        status="final",
        sections=[
            {
                "heading": "Market Overview",
                "content": (
                    "Global autoimmune therapeutics market estimated at "
                    "$150B (2025). SLE segment approximately $3.2B with "
                    "projected 8% CAGR through 2030. Significant unmet need "
                    "in refractory population (~20% of SLE patients)."
                ),
            },
            {
                "heading": "Current Standard of Care",
                "content": (
                    "Belimumab (Benlysta): Anti-BAFF mAb, ~$1.2B annual revenue. "
                    "Anifrolumab (Saphnelo): Anti-IFNAR1, launched 2021. "
                    "Voclosporin (Lupkynis): CNI for lupus nephritis. "
                    "Background: HCQ, corticosteroids, mycophenolate."
                ),
            },
        ],
        data={
            "total_addressable_market_usd_billions": 3.2,
            "refractory_population_pct": 20,
            "projected_cagr_pct": 8.0,
            "key_competitors": [
                {"product": "Belimumab", "company": "GSK", "mechanism": "Anti-BAFF", "revenue_usd_billions": 1.2},
                {"product": "Anifrolumab", "company": "AstraZeneca", "mechanism": "Anti-IFNAR1", "revenue_usd_billions": 0.4},
                {"product": "Voclosporin", "company": "Aurinia", "mechanism": "CNI", "revenue_usd_billions": 0.3},
            ],
        },
    )

    competitive_intel = _make_deliverable(
        deliverable_id="commercial_competitive_intel_v1",
        title="Competitive Intelligence Summary -- CAR-T Autoimmune Pipeline",
        role_id="head_commercial",
        category="commercial",
        regulatory_refs=["PhRMA_Code"],
        status="under_review",
        sections=[
            {
                "heading": "CAR-T Competitors in Autoimmune",
                "content": (
                    "Multiple CAR-T programs targeting autoimmune indications. "
                    "Cabaletta Bio (CABA-201): CD19 CAR-T for lupus, Phase I/II. "
                    "Kyverna Therapeutics (KYV-101): CD19 CAR-T, lupus nephritis. "
                    "Novartis: YTB323, next-gen CAR-T, preclinical autoimmune."
                ),
            },
            {
                "heading": "Differentiation Strategy",
                "content": (
                    "AZ-CT-001 differentiators: Proprietary 4-1BB costimulatory "
                    "domain, optimized manufacturing (21-day vein-to-vein), "
                    "focus on refractory SLE population, comprehensive "
                    "correlative biomarker program."
                ),
            },
        ],
        data={
            "competitors": [
                {"company": "Cabaletta Bio", "product": "CABA-201", "stage": "Phase I/II", "indication": "Lupus"},
                {"company": "Kyverna Therapeutics", "product": "KYV-101", "stage": "Phase I/II", "indication": "Lupus Nephritis"},
                {"company": "Novartis", "product": "YTB323", "stage": "Preclinical", "indication": "Autoimmune (broad)"},
            ],
            "differentiation_factors": [
                "Proprietary 4-1BB costimulatory domain",
                "Optimized manufacturing (21-day vein-to-vein)",
                "Refractory SLE focus",
                "Comprehensive correlative biomarker program",
            ],
        },
    )

    early_access = _make_deliverable(
        deliverable_id="commercial_early_access_v1",
        title="Early Access Program Considerations -- AZ-CT-001",
        role_id="head_commercial",
        category="market_access",
        regulatory_refs=["21_CFR_312", "PhRMA_Code"],
        status="draft",
        sections=[
            {
                "heading": "Expanded Access Framework",
                "content": (
                    "Expanded access (compassionate use) program to be "
                    "considered post-Phase I if: (1) Favorable safety at RP2D, "
                    "(2) Preliminary efficacy signal, (3) Sufficient manufacturing "
                    "capacity. Per 21 CFR 312 Subpart I."
                ),
            },
            {
                "heading": "Pricing and Reimbursement Considerations",
                "content": (
                    "Reference pricing: Approved CAR-T products range "
                    "$373K-$475K per infusion. SLE indication may command "
                    "lower price given chronic disease context. "
                    "Outcomes-based contracting to be explored."
                ),
            },
        ],
        data={
            "expanded_access_criteria": [
                "Favorable safety at RP2D",
                "Preliminary efficacy signal",
                "Sufficient manufacturing capacity",
            ],
            "reference_pricing_range_usd": {"low": 373000, "high": 475000},
            "outcomes_based_model": "planned",
            "target_launch_year": 2030,
        },
    )

    return [market_landscape, competitive_intel, early_access]


# ---------------------------------------------------------------------------
# CEO deliverables (top-level, aggregated)
# ---------------------------------------------------------------------------

def generate_ceo_deliverables() -> list[dict[str, Any]]:
    """Generate CEO-level deliverables.

    The CEO produces a program-level executive summary aggregating data
    from all functional heads. References SOX for governance.

    Returns:
        List of structured deliverable dicts.
    """
    executive_summary = _make_deliverable(
        deliverable_id="ceo_executive_summary_v1",
        title="Executive Program Summary -- AZ-CT-001 Board Report",
        role_id="ceo",
        category="governance",
        regulatory_refs=["SOX", "21_CFR_11"],
        status="draft",
        sections=[
            {
                "heading": "Program Status",
                "content": (
                    f"Phase I FIH trial in progress at {_NUM_SITES} sites. "
                    f"{_ENROLLED_PATIENTS} patients enrolled across {_DOSE_LEVELS} "
                    f"dose levels. Safety profile consistent with CAR-T class. "
                    f"No treatment-related deaths."
                ),
            },
            {
                "heading": "Key Risks",
                "content": (
                    "1. Manufacturing scale-up for Phase II (2 of 3 PPQ lots complete). "
                    "2. Competitive landscape intensifying (3 competitors in Phase I/II). "
                    "3. Regulatory pathway for accelerated approval requires FDA alignment."
                ),
            },
            {
                "heading": "Financial Overview",
                "content": (
                    "Series B preparation in progress. "
                    "Current cash runway: 18 months. "
                    "Phase II estimated cost: $25M. "
                    "Series B target raise: $80M."
                ),
            },
        ],
        data={
            "enrolled": _ENROLLED_PATIENTS,
            "sites": _NUM_SITES,
            "dose_levels": _DOSE_LEVELS,
            "deaths": _DEATHS,
            "cash_runway_months": 18,
            "series_b_target_usd_millions": 80,
            "phase2_cost_estimate_usd_millions": 25,
        },
    )

    return [executive_summary]


# ---------------------------------------------------------------------------
# Mapping of role IDs to their generator functions
# ---------------------------------------------------------------------------

_ROLE_GENERATORS: dict[str, Any] = {
    "ceo": generate_ceo_deliverables,
    "cmo": generate_cmo_deliverables,
    "vp_clinops": generate_clinops_deliverables,
    "head_pv": generate_pv_deliverables,
    "vp_regulatory": generate_regulatory_deliverables,
    "head_biostats": generate_biostats_deliverables,
    "head_cmc": generate_cmc_deliverables,
    "head_qa": generate_qa_deliverables,
    "vp_med_affairs": generate_medaffairs_deliverables,
    "head_clindev": generate_clindev_deliverables,
    "head_commercial": generate_commercial_deliverables,
}


# ---------------------------------------------------------------------------
# Activity log generation
# ---------------------------------------------------------------------------

def _generate_activity_log() -> list[dict[str, Any]]:
    """Build a realistic activity log showing delegation and completion.

    Simulates the CEO delegating to direct reports, who delegate to their
    reports, who complete work and escalate results back up the chain.

    Returns:
        Chronologically ordered list of activity log entries.
    """
    log: list[dict[str, Any]] = []

    # Day 0: CEO kicks off
    log.append(_log_entry(0, 8, "ceo", "initiated", "Initiated quarterly program review and deliverable generation", "SOX"))
    log.append(_log_entry(0, 8, "ceo", "delegated", "Delegated clinical program review to CMO", "21_CFR_11", target="cmo"))
    log.append(_log_entry(0, 8, "ceo", "delegated", "Delegated manufacturing status review to Head CMC", "21_CFR_11", target="head_cmc"))
    log.append(_log_entry(0, 8, "ceo", "delegated", "Delegated quality metrics compilation to Head QA", "21_CFR_11", target="head_qa"))
    log.append(_log_entry(0, 9, "ceo", "delegated", "Delegated market analysis update to Head Commercial", "21_CFR_11", target="head_commercial"))

    # Day 0: CMO delegates to reports
    log.append(_log_entry(0, 10, "cmo", "delegated", "Delegated trial status report to VP Clinical Ops", "ICH_E6_R3", target="vp_clinops", deliverable_id="clinops_trial_status_v1"))
    log.append(_log_entry(0, 10, "cmo", "delegated", "Delegated DSUR Year 1 preparation to Head of PV", "ICH_E2F", target="head_pv", deliverable_id="pv_dsur_outline_v1"))
    log.append(_log_entry(0, 10, "cmo", "delegated", "Delegated IND annual report preparation to VP Regulatory", "21_CFR_312", target="vp_regulatory", deliverable_id="reg_ind_annual_report_v1"))
    log.append(_log_entry(0, 11, "cmo", "delegated", "Delegated SAP review and DLT analysis to Head Biostats", "ICH_E9", target="head_biostats", deliverable_id="biostats_sap_v1"))
    log.append(_log_entry(0, 11, "cmo", "delegated", "Delegated publication plan update to VP Medical Affairs", "PhRMA_Code", target="vp_med_affairs", deliverable_id="medaffairs_pub_plan_v1"))
    log.append(_log_entry(0, 11, "cmo", "delegated", "Delegated CDP update to Head of Clinical Development", "ICH_E8_R1", target="head_clindev", deliverable_id="clindev_cdp_summary_v1"))

    # Day 1-3: Direct reports complete their work
    log.append(_log_entry(1, 9, "vp_clinops", "completed", "Completed trial status report for 3 active sites", "ICH_E6_R3", deliverable_id="clinops_trial_status_v1"))
    log.append(_log_entry(1, 10, "vp_clinops", "completed", "Completed protocol deviation summary", "ICH_E6_R3", deliverable_id="clinops_protocol_deviations_v1"))
    log.append(_log_entry(1, 14, "vp_clinops", "completed", "Finalized monitoring visit schedule", "ICH_E6_R3", deliverable_id="clinops_monitoring_schedule_v1"))

    log.append(_log_entry(1, 10, "head_pv", "completed", "Completed ICSR summary report", "ICH_E2B_R3", deliverable_id="pv_icsr_summary_v1"))
    log.append(_log_entry(1, 14, "head_pv", "completed", "Completed signal detection analysis (PRR/ROR)", "ICH_E2C_R2", deliverable_id="pv_signal_detection_v1"))
    log.append(_log_entry(2, 9, "head_pv", "completed", "Drafted DSUR Year 1 outline", "ICH_E2F", deliverable_id="pv_dsur_outline_v1"))
    log.append(_log_entry(2, 11, "head_pv", "completed", "Finalized expedited reporting log", "21_CFR_312_32", deliverable_id="pv_expedited_log_v1"))

    log.append(_log_entry(1, 11, "head_biostats", "completed", "Finalized SAP summary for Phase I", "ICH_E9", deliverable_id="biostats_sap_v1"))
    log.append(_log_entry(2, 9, "head_biostats", "completed", "Completed DLT analysis framework with Bayesian posteriors", "ICH_E9", deliverable_id="biostats_dlt_analysis_v1"))
    log.append(_log_entry(2, 14, "head_biostats", "completed", "Drafted Phase II sample size calculations", "ICH_E9_R1", deliverable_id="biostats_sample_size_v1"))
    log.append(_log_entry(3, 9, "head_biostats", "completed", "Drafted interim analysis plan for Phase II", "FDA_adaptive_design", deliverable_id="biostats_interim_plan_v1"))

    log.append(_log_entry(2, 10, "vp_regulatory", "completed", "Drafted IND annual report outline", "21_CFR_312", deliverable_id="reg_ind_annual_report_v1"))
    log.append(_log_entry(2, 15, "vp_regulatory", "completed", "Drafted EOP2 meeting briefing document outline", "FDA_meetings", deliverable_id="reg_eop2_briefing_v1"))
    log.append(_log_entry(3, 10, "vp_regulatory", "completed", "Finalized regulatory submission timeline", "21_CFR_312", deliverable_id="reg_submission_timeline_v1"))

    log.append(_log_entry(1, 12, "vp_med_affairs", "completed", "Updated 3-year publication plan", "PhRMA_Code", deliverable_id="medaffairs_pub_plan_v1"))
    log.append(_log_entry(2, 9, "vp_med_affairs", "completed", "Updated KOL engagement tracker", "PhRMA_Code", deliverable_id="medaffairs_kol_tracker_v1"))
    log.append(_log_entry(2, 14, "vp_med_affairs", "completed", "Compiled SAB minutes summary", "PhRMA_Code", deliverable_id="medaffairs_sab_minutes_v1"))
    log.append(_log_entry(3, 9, "vp_med_affairs", "completed", "Finalized congress activity plan", "PhRMA_Code", deliverable_id="medaffairs_congress_plan_v1"))

    log.append(_log_entry(2, 10, "head_clindev", "completed", "Updated clinical development plan summary", "ICH_E8_R1", deliverable_id="clindev_cdp_summary_v1"))
    log.append(_log_entry(2, 15, "head_clindev", "completed", "Drafted target product profile", "ICH_E8_R1", deliverable_id="clindev_tpp_v1"))
    log.append(_log_entry(3, 10, "head_clindev", "completed", "Completed indication sequencing rationale", "ICH_E8_R1", deliverable_id="clindev_indication_seq_v1"))

    # CEO direct reports (not under CMO)
    log.append(_log_entry(1, 9, "head_cmc", "completed", "Compiled manufacturing batch summary", "21_CFR_1271", deliverable_id="cmc_batch_summary_v1"))
    log.append(_log_entry(1, 14, "head_cmc", "completed", "Compiled release testing panel results", "ICH_Q6B", deliverable_id="cmc_release_testing_v1"))
    log.append(_log_entry(2, 10, "head_cmc", "completed", "Compiled stability data summary", "ICH_Q1A", deliverable_id="cmc_stability_v1"))
    log.append(_log_entry(2, 15, "head_cmc", "completed", "Updated process validation status", "21_CFR_211", deliverable_id="cmc_process_validation_v1"))

    log.append(_log_entry(1, 10, "head_qa", "completed", "Updated CAPA tracker", "ICH_Q10", deliverable_id="qa_capa_tracker_v1"))
    log.append(_log_entry(1, 15, "head_qa", "completed", "Completed deviation trend analysis", "ICH_Q10", deliverable_id="qa_deviation_trends_v1"))
    log.append(_log_entry(2, 9, "head_qa", "completed", "Updated audit schedule and findings", "ICH_Q10", deliverable_id="qa_audit_schedule_v1"))
    log.append(_log_entry(2, 14, "head_qa", "completed", "Compiled training compliance data", "ICH_Q10", deliverable_id="qa_training_compliance_v1"))
    log.append(_log_entry(3, 9, "head_qa", "completed", "Finalized GxP compliance matrix", "ICH_Q9", deliverable_id="qa_gxp_matrix_v1"))

    log.append(_log_entry(1, 14, "head_commercial", "completed", "Completed market landscape analysis", "PhRMA_Code", deliverable_id="commercial_market_landscape_v1"))
    log.append(_log_entry(2, 10, "head_commercial", "completed", "Updated competitive intelligence summary", "PhRMA_Code", deliverable_id="commercial_competitive_intel_v1"))
    log.append(_log_entry(2, 15, "head_commercial", "completed", "Drafted early access program considerations", "21_CFR_312", deliverable_id="commercial_early_access_v1"))

    # Day 3-4: CMO reviews
    log.append(_log_entry(3, 14, "cmo", "reviewed", "Reviewed all clinical function deliverables", "ICH_E6_R3"))
    log.append(_log_entry(3, 15, "cmo", "completed", "Completed benefit-risk assessment summary", "ICH_E2C_R2", deliverable_id="cmo_benefit_risk_v1"))
    log.append(_log_entry(3, 16, "cmo", "completed", "Drafted DSMB charter outline", "ICH_E6_R3", deliverable_id="cmo_dsmb_charter_v1"))
    log.append(_log_entry(4, 9, "cmo", "completed", "Finalized clinical development plan overview", "ICH_E8_R1", deliverable_id="cmo_cdp_overview_v1"))
    log.append(_log_entry(4, 10, "cmo", "escalated", "Escalated combined clinical program summary to CEO", "ICH_E6_R3", target="ceo"))

    # Day 4-5: CEO compiles and completes
    log.append(_log_entry(4, 14, "ceo", "reviewed", "Reviewed all functional deliverables from direct reports", "SOX"))
    log.append(_log_entry(5, 9, "ceo", "completed", "Completed executive program summary for board report", "SOX", deliverable_id="ceo_executive_summary_v1"))

    # Sort chronologically so parallel activities interleave properly
    log.sort(key=lambda e: e["timestamp"])
    return log


# ---------------------------------------------------------------------------
# Simulation orchestrator
# ---------------------------------------------------------------------------

def run_simulation() -> dict[str, Any]:
    """Run the full simulation, generating all deliverables and activity log.

    Clears previous state, then generates deliverables for each role in
    organisational hierarchy order (CEO delegates to CMO, who delegates
    to reports, etc.). Logs each activity with timestamp, role, action,
    and delegation chain.

    Returns:
        Dict with keys ``deliverables``, ``activity_log``, and ``summary``.
    """
    global SIMULATION_LOG, DELIVERABLES  # noqa: PLW0603

    # Clear previous state
    SIMULATION_LOG.clear()
    DELIVERABLES.clear()

    # Hierarchy order: CEO -> CEO direct reports -> CMO reports
    hierarchy_order = [
        "ceo",
        # CEO direct reports
        "cmo",
        "head_cmc",
        "head_qa",
        "head_commercial",
        # CMO reports
        "vp_clinops",
        "head_pv",
        "vp_regulatory",
        "head_biostats",
        "vp_med_affairs",
        "head_clindev",
    ]

    for role_id in hierarchy_order:
        generator = _ROLE_GENERATORS.get(role_id)
        if generator is not None:
            deliverables = generator()
            DELIVERABLES[role_id] = deliverables

    # Generate the activity log (extend in-place so imported references stay valid)
    SIMULATION_LOG.extend(_generate_activity_log())

    summary = {
        "roles_active": len(DELIVERABLES),
        "total_deliverables": sum(len(d) for d in DELIVERABLES.values()),
        "total_log_entries": len(SIMULATION_LOG),
        "simulation_start": _ts(0),
        "simulation_end": _ts(5, 17),
        "hierarchy_order": hierarchy_order,
    }

    return {
        "deliverables": copy.deepcopy(DELIVERABLES),
        "activity_log": list(SIMULATION_LOG),
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Helper / query functions
# ---------------------------------------------------------------------------

def get_simulation_status() -> dict[str, Any]:
    """Return a summary of the current simulation state.

    Returns:
        Dict with role count, deliverable count, log entry count,
        and per-role deliverable counts.
    """
    per_role = {role_id: len(delivs) for role_id, delivs in DELIVERABLES.items()}
    return {
        "roles_active": len(DELIVERABLES),
        "total_deliverables": sum(len(d) for d in DELIVERABLES.values()),
        "total_log_entries": len(SIMULATION_LOG),
        "deliverables_per_role": per_role,
    }


def get_role_deliverables(role_id: str) -> list[dict[str, Any]]:
    """Return deliverables for a single role.

    Args:
        role_id: The role identifier (e.g. ``"cmo"``, ``"head_pv"``).

    Returns:
        List of deliverable dicts for the specified role, or an empty
        list if the role has no deliverables or is not found.
    """
    return copy.deepcopy(DELIVERABLES.get(role_id, []))


def get_activity_log(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent activity log entries.

    Args:
        limit: Maximum number of entries to return. Defaults to 50.
            Use 0 or negative to return all entries.

    Returns:
        List of activity log dicts, most recent first.
    """
    if limit <= 0:
        return list(reversed(SIMULATION_LOG))
    return list(reversed(SIMULATION_LOG[-limit:]))


def get_delegation_tree() -> dict[str, Any]:
    """Build a tree of who delegated what to whom.

    Walks the activity log and constructs a nested delegation tree
    rooted at the CEO. Each node contains the role, actions taken,
    and children (delegated-to roles).

    Returns:
        Nested dict representing the delegation hierarchy with
        deliverables at each level.
    """
    # Build delegation edges from the log
    delegations: dict[str, list[dict[str, Any]]] = {}
    for entry in SIMULATION_LOG:
        if entry["action"] == "delegated" and "target" in entry:
            src = entry["role_id"]
            if src not in delegations:
                delegations[src] = []
            delegations[src].append({
                "target": entry["target"],
                "description": entry["description"],
                "deliverable_id": entry.get("deliverable_id"),
                "timestamp": entry["timestamp"],
            })

    # Collect completions per role
    completions: dict[str, list[str]] = {}
    for entry in SIMULATION_LOG:
        if entry["action"] == "completed" and entry.get("deliverable_id"):
            role = entry["role_id"]
            if role not in completions:
                completions[role] = []
            completions[role].append(entry["deliverable_id"])

    def _build_node(role_id: str) -> dict[str, Any]:
        role_info = ORG_ROLES.get(role_id, {})
        node: dict[str, Any] = {
            "role_id": role_id,
            "title": role_info.get("title", "Unknown"),
            "deliverables_completed": completions.get(role_id, []),
            "delegated_to": [],
        }
        seen_targets: set[str] = set()
        for d in delegations.get(role_id, []):
            target = d["target"]
            if target not in seen_targets:
                seen_targets.add(target)
                child_node = _build_node(target)
                child_node["delegation_description"] = d["description"]
                child_node["delegation_timestamp"] = d["timestamp"]
                node["delegated_to"].append(child_node)
        return node

    return _build_node("ceo")


def get_all_deliverable_ids() -> list[str]:
    """Return a flat list of all deliverable IDs across all roles.

    Returns:
        Sorted list of deliverable ID strings.
    """
    ids = []
    for delivs in DELIVERABLES.values():
        for d in delivs:
            ids.append(d["deliverable_id"])
    return sorted(ids)


def get_all_regulatory_refs_from_deliverables() -> set[str]:
    """Collect every regulatory reference used across all deliverables.

    Returns:
        Set of regulatory framework ID strings.
    """
    refs: set[str] = set()
    for delivs in DELIVERABLES.values():
        for d in delivs:
            refs.update(d["regulatory_refs"])
    return refs


def get_all_regulatory_refs_from_log() -> set[str]:
    """Collect every regulatory_basis value from the activity log.

    Returns:
        Set of regulatory framework ID strings.
    """
    return {entry["regulatory_basis"] for entry in SIMULATION_LOG}
