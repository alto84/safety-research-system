"""Pharmaceutical company organizational simulation.

Defines the org hierarchy, roles, skills, regulatory mappings,
and clinical pipeline state for a simulated cell therapy company.

All data is for simulation purposes only. Regulatory framework IDs
reference real ICH, FDA, and EU guidelines but are not legal advice.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Skill library
# ---------------------------------------------------------------------------

SKILL_LIBRARY: dict[str, dict[str, str]] = {
    "clinical_trial_design": {
        "name": "Clinical Trial Design",
        "category": "clinical",
        "description": "Design adaptive, multi-arm, and basket trials per ICH E8(R1).",
    },
    "crs_management": {
        "name": "CRS Management",
        "category": "clinical",
        "description": "Cytokine release syndrome grading, monitoring, and intervention.",
    },
    "gcp_compliance": {
        "name": "GCP Compliance",
        "category": "regulatory",
        "description": "ICH E6(R3) Good Clinical Practice oversight.",
    },
    "biostatistics": {
        "name": "Biostatistics",
        "category": "analytics",
        "description": "Bayesian and frequentist trial analysis per ICH E9(R1).",
    },
    "regulatory_submissions": {
        "name": "Regulatory Submissions",
        "category": "regulatory",
        "description": "IND/BLA/eCTD preparation and FDA correspondence.",
    },
    "pharmacovigilance": {
        "name": "Pharmacovigilance",
        "category": "safety",
        "description": "ICSR processing, signal detection, PSUR/DSUR authoring.",
    },
    "safety_reporting": {
        "name": "Safety Reporting",
        "category": "safety",
        "description": "Expedited and periodic safety reporting per 21 CFR 312.32.",
    },
    "cell_therapy_manufacturing": {
        "name": "Cell Therapy Manufacturing",
        "category": "manufacturing",
        "description": "Autologous cell processing, lot release, chain of custody.",
    },
    "quality_management": {
        "name": "Quality Management",
        "category": "quality",
        "description": "GxP compliance, CAPA, deviation management, audit readiness.",
    },
    "medical_monitoring": {
        "name": "Medical Monitoring",
        "category": "clinical",
        "description": "Real-time safety surveillance and medical review of AEs.",
    },
    "data_management": {
        "name": "Data Management",
        "category": "clinical",
        "description": "EDC, data cleaning, CDISC SDTM/ADaM standards.",
    },
    "medical_writing": {
        "name": "Medical Writing",
        "category": "medical_affairs",
        "description": "CSR, IB, protocol, and regulatory document authoring.",
    },
    "kol_engagement": {
        "name": "KOL Engagement",
        "category": "medical_affairs",
        "description": "Key opinion leader identification and medical education.",
    },
    "market_access": {
        "name": "Market Access",
        "category": "commercial",
        "description": "Health economics, outcomes research, payer strategy.",
    },
    "launch_planning": {
        "name": "Launch Planning",
        "category": "commercial",
        "description": "Commercial launch strategy and supply chain readiness.",
    },
    "supply_chain": {
        "name": "Supply Chain",
        "category": "manufacturing",
        "description": "Cryopreservation logistics, vein-to-vein tracking.",
    },
    "risk_management": {
        "name": "Risk Management",
        "category": "quality",
        "description": "ICH Q9 risk assessment, FMEA, risk-benefit analysis.",
    },
    "executive_leadership": {
        "name": "Executive Leadership",
        "category": "leadership",
        "description": "Strategic oversight, board reporting, investor relations.",
    },
    "clinical_development_strategy": {
        "name": "Clinical Development Strategy",
        "category": "clinical",
        "description": "TPP, CDP, indication sequencing, regulatory pathway.",
    },
    "fda_interactions": {
        "name": "FDA Interactions",
        "category": "regulatory",
        "description": "Pre-IND, EOP2, pre-BLA meeting management.",
    },
    "signal_detection": {
        "name": "Signal Detection",
        "category": "safety",
        "description": "FAERS mining, PRR/ROR/EBGM analysis, signal validation.",
    },
    "cmc_development": {
        "name": "CMC Development",
        "category": "manufacturing",
        "description": "Process development, analytical methods, stability studies.",
    },
    "audit_management": {
        "name": "Audit Management",
        "category": "quality",
        "description": "FDA/EMA inspection readiness and internal audit programs.",
    },
}


# ---------------------------------------------------------------------------
# Org hierarchy — roles
# ---------------------------------------------------------------------------

ORG_ROLES: dict[str, dict[str, Any]] = {
    "ceo": {
        "role_id": "ceo",
        "title": "Chief Executive Officer",
        "reports_to": None,
        "responsibilities": [
            "Overall corporate strategy and investor relations",
            "Board-level governance and fiduciary oversight",
            "Capital allocation across clinical and commercial programs",
            "Cross-functional alignment on pipeline priorities",
        ],
        "regulatory_frameworks": ["21_CFR_11", "SOX"],
        "skills": ["executive_leadership", "risk_management"],
        "status": "active",
        "current_task": "Overseeing Phase I FIH trial progress and Series B preparation",
    },
    "cmo": {
        "role_id": "cmo",
        "title": "Chief Medical Officer",
        "reports_to": "ceo",
        "responsibilities": [
            "Medical strategy for clinical development programs",
            "Benefit-risk assessment and DSMB interactions",
            "Regulatory health authority interactions (medical lead)",
            "Medical review of safety data and IND annual reports",
            "Scientific advisory board engagement",
        ],
        "regulatory_frameworks": ["ICH_E6_R3", "ICH_E8_R1", "21_CFR_312"],
        "skills": [
            "clinical_development_strategy",
            "medical_monitoring",
            "crs_management",
        ],
        "status": "active",
        "current_task": "Reviewing Phase I interim safety data with DSMB",
    },
    "head_cmc": {
        "role_id": "head_cmc",
        "title": "Head of CMC / Manufacturing",
        "reports_to": "ceo",
        "responsibilities": [
            "Cell therapy manufacturing process development and scale-up",
            "Lot release and certificate of analysis management",
            "Supply chain logistics (vein-to-vein)",
            "CMC section authorship for IND/BLA submissions",
            "Raw material qualification and vendor management",
        ],
        "regulatory_frameworks": [
            "21_CFR_210",
            "21_CFR_211",
            "21_CFR_600",
            "21_CFR_1271",
            "ICH_Q1A",
            "ICH_Q2",
            "ICH_Q5E",
            "ICH_Q6B",
            "ICH_Q8",
            "ICH_Q11",
            "EU_GMP_Annex_1",
        ],
        "skills": [
            "cell_therapy_manufacturing",
            "cmc_development",
            "supply_chain",
        ],
        "status": "active",
        "current_task": "Scaling autologous CAR-T manufacturing for Phase I supply",
    },
    "head_qa": {
        "role_id": "head_qa",
        "title": "Head of Quality Assurance",
        "reports_to": "ceo",
        "responsibilities": [
            "GxP compliance oversight (GMP, GCP, GLP, GDP)",
            "Deviation, CAPA, and change control management",
            "Regulatory inspection readiness and audit programs",
            "Quality metrics reporting to executive leadership",
            "Batch record review and lot disposition",
        ],
        "regulatory_frameworks": [
            "21_CFR_210",
            "21_CFR_211",
            "21_CFR_600",
            "ICH_Q1A",
            "ICH_Q9",
            "ICH_Q10",
            "EU_GMP_Annex_1",
        ],
        "skills": [
            "quality_management",
            "audit_management",
            "risk_management",
        ],
        "status": "active",
        "current_task": "Preparing for pre-approval inspection readiness assessment",
    },
    "head_commercial": {
        "role_id": "head_commercial",
        "title": "Head of Commercial / Market Access",
        "reports_to": "ceo",
        "responsibilities": [
            "Commercial launch planning and market access strategy",
            "Health economics and outcomes research (HEOR)",
            "Payer engagement and reimbursement pathway development",
            "Competitive intelligence and market landscape analysis",
        ],
        "regulatory_frameworks": ["FDCA_502", "PhRMA_Code"],
        "skills": ["market_access", "launch_planning"],
        "status": "idle",
        "current_task": "Market landscape analysis for autoimmune CAR-T indications",
    },
    "vp_clinops": {
        "role_id": "vp_clinops",
        "title": "VP of Clinical Operations",
        "reports_to": "cmo",
        "responsibilities": [
            "Clinical trial execution and site management",
            "CRO oversight and vendor management",
            "Clinical data management (EDC, CDISC)",
            "Protocol development and amendment management",
            "Enrollment tracking and trial timeline management",
        ],
        "regulatory_frameworks": [
            "ICH_E6_R3",
            "ICH_E8_R1",
            "21_CFR_312",
            "21_CFR_50",
            "21_CFR_56",
            "21_CFR_11",
            "CBER_early_phase",
        ],
        "skills": [
            "clinical_trial_design",
            "gcp_compliance",
            "data_management",
        ],
        "status": "active",
        "current_task": "Managing first-in-human dose escalation at 3 clinical sites",
    },
    "vp_med_affairs": {
        "role_id": "vp_med_affairs",
        "title": "VP of Medical Affairs",
        "reports_to": "cmo",
        "responsibilities": [
            "Medical education and scientific publications",
            "KOL engagement and advisory board management",
            "Medical information and healthcare provider inquiries",
            "Investigator-sponsored study oversight",
        ],
        "regulatory_frameworks": [
            "PhRMA_Code",
            "FDCA_502",
            "ICH_E6_R3",
        ],
        "skills": [
            "kol_engagement",
            "medical_writing",
        ],
        "status": "active",
        "current_task": "Organizing scientific advisory board for Phase I data review",
    },
    "head_pv": {
        "role_id": "head_pv",
        "title": "Head of Patient Safety / Pharmacovigilance",
        "reports_to": "cmo",
        "responsibilities": [
            "Individual case safety report (ICSR) processing",
            "Signal detection and safety signal validation",
            "DSUR and PSUR authoring and submission",
            "Expedited safety reporting (15-day/7-day IND reports)",
            "Safety database management and MedDRA coding",
        ],
        "regulatory_frameworks": [
            "ICH_E2A",
            "ICH_E2B_R3",
            "ICH_E2C_R2",
            "ICH_E2D",
            "ICH_E2F",
            "21_CFR_312_32",
            "21_CFR_314_80",
            "CIOMS_I",
            "CIOMS_V",
            "CIOMS_VI",
        ],
        "skills": [
            "pharmacovigilance",
            "safety_reporting",
            "signal_detection",
        ],
        "status": "active",
        "current_task": "Processing ICSRs from Phase I and preparing DSUR Year 1",
    },
    "vp_regulatory": {
        "role_id": "vp_regulatory",
        "title": "VP of Regulatory Affairs",
        "reports_to": "cmo",
        "responsibilities": [
            "Regulatory strategy and health authority interactions",
            "IND/BLA/MAA submission planning and execution",
            "eCTD compilation and publishing",
            "Regulatory intelligence and guidance monitoring",
            "FDA meeting management (pre-IND, EOP2, pre-BLA)",
        ],
        "regulatory_frameworks": [
            "21_CFR_312",
            "21_CFR_312_23",
            "21_CFR_601",
            "ICH_M4",
            "eCTD",
            "FDA_meetings",
            "PDUFA",
            "PHS_Act_351",
        ],
        "skills": [
            "regulatory_submissions",
            "fda_interactions",
            "medical_writing",
        ],
        "status": "active",
        "current_task": "Preparing IND annual report and planning EOP2 meeting strategy",
    },
    "head_biostats": {
        "role_id": "head_biostats",
        "title": "Head of Biostatistics",
        "reports_to": "cmo",
        "responsibilities": [
            "Statistical analysis plan (SAP) authoring",
            "Bayesian and frequentist trial design and analysis",
            "DSMB charter development and interim analysis support",
            "Regulatory submission statistical sections",
            "Sample size estimation and adaptive design simulations",
        ],
        "regulatory_frameworks": [
            "ICH_E9",
            "ICH_E9_R1",
            "FDA_adaptive_design",
            "ICH_E6_R3",
        ],
        "skills": [
            "biostatistics",
            "clinical_trial_design",
            "data_management",
        ],
        "status": "active",
        "current_task": "Finalizing Phase I 3+3 dose escalation analysis and DLT assessment",
    },
    "head_clindev": {
        "role_id": "head_clindev",
        "title": "Head of Clinical Development",
        "reports_to": "cmo",
        "responsibilities": [
            "Clinical development plan (CDP) authoring and maintenance",
            "Target product profile (TPP) development",
            "Indication sequencing and lifecycle management",
            "Competitive landscape analysis for pipeline decisions",
            "Cross-functional alignment on development milestones",
        ],
        "regulatory_frameworks": [
            "ICH_E8_R1",
            "ICH_E6_R3",
            "21_CFR_312",
            "CBER_early_phase",
        ],
        "skills": [
            "clinical_development_strategy",
            "clinical_trial_design",
            "medical_writing",
        ],
        "status": "active",
        "current_task": "Updating CDP with Phase I interim data and Phase II planning",
    },
}


# ---------------------------------------------------------------------------
# Clinical pipeline stages
# ---------------------------------------------------------------------------

PIPELINE_STAGES: list[dict[str, Any]] = [
    {
        "id": "preclinical",
        "name": "Preclinical",
        "owner": "head_cmc",
        "status": "completed",
        "start": "2023-01",
        "end": "2024-06",
        "regulations": ["21_CFR_58"],
    },
    {
        "id": "ind_prep",
        "name": "IND Preparation",
        "owner": "vp_regulatory",
        "status": "completed",
        "start": "2024-03",
        "end": "2024-09",
        "regulations": ["21_CFR_312_23", "ICH_M4"],
    },
    {
        "id": "ind_filing",
        "name": "IND Filing",
        "owner": "vp_regulatory",
        "status": "completed",
        "start": "2024-09",
        "end": "2024-10",
        "regulations": ["21_CFR_312"],
    },
    {
        "id": "phase1",
        "name": "Phase I (FIH)",
        "owner": "vp_clinops",
        "status": "in_progress",
        "start": "2024-11",
        "end": None,
        "regulations": ["ICH_E6_R3", "ICH_E8_R1", "CBER_early_phase"],
    },
    {
        "id": "dsur_1",
        "name": "DSUR Year 1",
        "owner": "head_pv",
        "status": "pending",
        "start": None,
        "end": None,
        "regulations": ["ICH_E2F"],
    },
    {
        "id": "phase2",
        "name": "Phase II",
        "owner": "vp_clinops",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["ICH_E6_R3", "ICH_E9"],
    },
    {
        "id": "eop2",
        "name": "End-of-Phase-2 Meeting",
        "owner": "vp_regulatory",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["FDA_meetings"],
    },
    {
        "id": "phase3",
        "name": "Phase III (Pivotal)",
        "owner": "vp_clinops",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["ICH_E9_R1"],
    },
    {
        "id": "bla_prep",
        "name": "BLA Preparation",
        "owner": "vp_regulatory",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["21_CFR_601", "ICH_M4"],
    },
    {
        "id": "bla_submit",
        "name": "BLA Submission",
        "owner": "vp_regulatory",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["eCTD"],
    },
    {
        "id": "fda_review",
        "name": "FDA Review",
        "owner": "vp_regulatory",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["PDUFA"],
    },
    {
        "id": "approval",
        "name": "Approval",
        "owner": "ceo",
        "status": "planned",
        "start": None,
        "end": None,
        "regulations": ["21_CFR_601"],
    },
]


# ---------------------------------------------------------------------------
# Regulatory framework mapping
# ---------------------------------------------------------------------------

REGULATORY_MAP: dict[str, dict[str, Any]] = {
    # ICH Efficacy guidelines
    "ICH_E6_R3": {
        "title": "Good Clinical Practice",
        "category": "clinical",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Integrated addendum to ICH E6(R2) on GCP for clinical trials.",
    },
    "ICH_E2A": {
        "title": "Clinical Safety Data Management: Definitions and Standards for Expedited Reporting",
        "category": "safety",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Defines adverse event terminology and expedited reporting standards.",
    },
    "ICH_E2B_R3": {
        "title": "Electronic Transmission of Individual Case Safety Reports (ICSRs)",
        "category": "safety",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Data elements and message specification for ICSR transmission.",
    },
    "ICH_E2C_R2": {
        "title": "Periodic Benefit-Risk Evaluation Report (PBRER)",
        "category": "safety",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Framework for periodic safety reporting during post-authorization.",
    },
    "ICH_E2D": {
        "title": "Post-Approval Safety Data Management",
        "category": "safety",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Standards for handling safety data after marketing authorization.",
    },
    "ICH_E2F": {
        "title": "Development Safety Update Report (DSUR)",
        "category": "safety",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Annual safety report format for investigational products.",
    },
    "ICH_E8_R1": {
        "title": "General Considerations for Clinical Studies",
        "category": "clinical",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Framework for quality-by-design in clinical study planning.",
    },
    "ICH_E9": {
        "title": "Statistical Principles for Clinical Trials",
        "category": "biostatistics",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Statistical methods, sample size, analysis populations for trials.",
    },
    "ICH_E9_R1": {
        "title": "Estimands and Sensitivity Analysis in Clinical Trials",
        "category": "biostatistics",
        "url": "https://www.ich.org/page/efficacy-guidelines",
        "description": "Addendum on estimand framework for defining treatment effects.",
    },
    # ICH Multidisciplinary / Quality guidelines
    "ICH_M4": {
        "title": "Common Technical Document (CTD)",
        "category": "regulatory",
        "url": "https://www.ich.org/page/multidisciplinary-guidelines",
        "description": "Standardized format for regulatory submissions (Modules 1-5).",
    },
    "ICH_Q1A": {
        "title": "Stability Testing of New Drug Substances and Products",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Guidelines for stability study design and shelf-life determination.",
    },
    "ICH_Q2": {
        "title": "Validation of Analytical Procedures",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Validation parameters for analytical methods (specificity, accuracy, etc.).",
    },
    "ICH_Q5E": {
        "title": "Comparability of Biotechnological/Biological Products",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Comparability studies for manufacturing process changes.",
    },
    "ICH_Q6B": {
        "title": "Specifications: Test Procedures for Biotechnological/Biological Products",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Setting specifications for biologics including cell therapy products.",
    },
    "ICH_Q8": {
        "title": "Pharmaceutical Development",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Quality-by-design principles for pharmaceutical development.",
    },
    "ICH_Q9": {
        "title": "Quality Risk Management",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Principles and tools for quality risk management (FMEA, HACCP, etc.).",
    },
    "ICH_Q10": {
        "title": "Pharmaceutical Quality System",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Quality system model for pharmaceutical manufacturers.",
    },
    "ICH_Q11": {
        "title": "Development and Manufacture of Drug Substances",
        "category": "quality",
        "url": "https://www.ich.org/page/quality-guidelines",
        "description": "Guidance on drug substance development and manufacturing.",
    },
    # FDA CFR regulations
    "21_CFR_11": {
        "title": "Electronic Records; Electronic Signatures",
        "category": "regulatory",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11",
        "description": "Requirements for electronic records and signatures in FDA-regulated industries.",
    },
    "21_CFR_50": {
        "title": "Protection of Human Subjects (Informed Consent)",
        "category": "clinical",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-50",
        "description": "Informed consent requirements for clinical trial participants.",
    },
    "21_CFR_56": {
        "title": "Institutional Review Boards (IRBs)",
        "category": "clinical",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-56",
        "description": "Requirements for IRB composition, functions, and operations.",
    },
    "21_CFR_58": {
        "title": "Good Laboratory Practice (GLP) for Nonclinical Studies",
        "category": "preclinical",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-58",
        "description": "GLP standards for nonclinical laboratory studies.",
    },
    "21_CFR_210": {
        "title": "Current Good Manufacturing Practice (cGMP) — General",
        "category": "manufacturing",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-210",
        "description": "General cGMP requirements for drug manufacturing.",
    },
    "21_CFR_211": {
        "title": "Current Good Manufacturing Practice (cGMP) — Finished Pharmaceuticals",
        "category": "manufacturing",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-211",
        "description": "Detailed cGMP requirements for finished pharmaceutical products.",
    },
    "21_CFR_312": {
        "title": "Investigational New Drug Application (IND)",
        "category": "regulatory",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-312",
        "description": "IND application requirements, safety reporting, and annual reports.",
    },
    "21_CFR_312_23": {
        "title": "IND Content and Format",
        "category": "regulatory",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-312/subpart-B/section-312.23",
        "description": "Specific content and format requirements for IND submissions.",
    },
    "21_CFR_312_32": {
        "title": "IND Safety Reporting",
        "category": "safety",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-312/subpart-B/section-312.32",
        "description": "Requirements for expedited IND safety reports (7-day, 15-day).",
    },
    "21_CFR_314_80": {
        "title": "Post-marketing Safety Reporting (NDA/ANDA)",
        "category": "safety",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-314/subpart-B/section-314.80",
        "description": "Post-marketing adverse experience reporting requirements.",
    },
    "21_CFR_600": {
        "title": "Biological Products: General",
        "category": "manufacturing",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-F/part-600",
        "description": "General requirements for biological product manufacturing.",
    },
    "21_CFR_601": {
        "title": "Licensing (BLA)",
        "category": "regulatory",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-F/part-601",
        "description": "Biologics License Application requirements and review process.",
    },
    "21_CFR_1271": {
        "title": "Human Cells, Tissues, and Cellular and Tissue-Based Products (HCT/Ps)",
        "category": "manufacturing",
        "url": "https://www.ecfr.gov/current/title-21/chapter-I/subchapter-L/part-1271",
        "description": "Regulatory framework for HCT/Ps including cell therapy products.",
    },
    # FDA guidance and process
    "CBER_early_phase": {
        "title": "CBER Guidance for Early-Phase Cell Therapy Clinical Trials",
        "category": "clinical",
        "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
        "description": "CBER-specific considerations for early-phase cell and gene therapy trials.",
    },
    "FDA_meetings": {
        "title": "FDA Formal Meetings (Pre-IND, EOP2, Pre-BLA)",
        "category": "regulatory",
        "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
        "description": "Guidance on scheduling and conducting formal FDA meetings.",
    },
    "FDA_adaptive_design": {
        "title": "Adaptive Designs for Clinical Trials of Drugs and Biologics",
        "category": "biostatistics",
        "url": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents",
        "description": "FDA guidance on adaptive, Bayesian, and enrichment trial designs.",
    },
    "PDUFA": {
        "title": "Prescription Drug User Fee Act",
        "category": "regulatory",
        "url": "https://www.fda.gov/industry/prescription-drug-user-fee-amendments",
        "description": "User fee framework and FDA review timelines for drug applications.",
    },
    "PHS_Act_351": {
        "title": "Public Health Service Act Section 351 — Biologics",
        "category": "regulatory",
        "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title42-section262",
        "description": "Statutory basis for biologics licensing and regulation.",
    },
    "eCTD": {
        "title": "Electronic Common Technical Document",
        "category": "regulatory",
        "url": "https://www.ich.org/page/multidisciplinary-guidelines",
        "description": "Electronic format for regulatory submission of CTD modules.",
    },
    # CIOMS publications
    "CIOMS_I": {
        "title": "CIOMS I — International Reporting of Adverse Drug Reactions",
        "category": "safety",
        "url": "https://cioms.ch/publications/",
        "description": "International standards for individual adverse drug reaction reporting.",
    },
    "CIOMS_V": {
        "title": "CIOMS V — Current Challenges in Pharmacovigilance",
        "category": "safety",
        "url": "https://cioms.ch/publications/",
        "description": "Pragmatic approaches to pharmacovigilance challenges.",
    },
    "CIOMS_VI": {
        "title": "CIOMS VI — Management of Safety Information from Clinical Trials",
        "category": "safety",
        "url": "https://cioms.ch/publications/",
        "description": "Guidance on managing safety information during clinical development.",
    },
    # EU / Other
    "EU_GMP_Annex_1": {
        "title": "EU GMP Annex 1 — Manufacture of Sterile Medicinal Products",
        "category": "manufacturing",
        "url": "https://health.ec.europa.eu/medicinal-products/eudralex_en",
        "description": "EU requirements for sterile manufacturing including ATMPs.",
    },
    # Industry codes
    "PhRMA_Code": {
        "title": "PhRMA Code on Interactions with Healthcare Professionals",
        "category": "commercial",
        "url": "https://www.phrma.org/en/Codes-and-guidelines",
        "description": "Voluntary industry code governing HCP interactions and promotional practices.",
    },
    "FDCA_502": {
        "title": "Federal Food, Drug, and Cosmetic Act Section 502 — Misbranding",
        "category": "commercial",
        "url": "https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title21-section352",
        "description": "Statutory basis for drug labeling and promotional requirements.",
    },
    "SOX": {
        "title": "Sarbanes-Oxley Act",
        "category": "corporate_governance",
        "url": "https://www.congress.gov/bill/107th-congress/house-bill/3763",
        "description": "Corporate governance, financial disclosure, and internal controls.",
    },
}


# ---------------------------------------------------------------------------
# Quality metrics simulation
# ---------------------------------------------------------------------------

def get_quality_metrics() -> dict[str, Any]:
    """Return simulated quality metrics for the QA dashboard.

    Returns a dictionary with deviation, CAPA, audit, training, and batch
    quality metrics representative of an early-stage cell therapy company
    running a Phase I first-in-human trial.
    """
    return {
        "deviations": {
            "open": 3,
            "closed_ytd": 17,
            "critical": 0,
        },
        "capa": {
            "open": 5,
            "overdue": 1,
            "closed_ytd": 12,
            "avg_closure_days": 45,
        },
        "audits": {
            "scheduled_ytd": 4,
            "completed": 2,
            "findings_open": 7,
            "critical_findings": 0,
        },
        "training": {
            "compliance_pct": 94.2,
            "overdue_assignments": 8,
        },
        "batches": {
            "manufactured_ytd": 23,
            "released": 21,
            "failed": 2,
            "failure_rate_pct": 8.7,
        },
    }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_role(role_id: str) -> dict[str, Any] | None:
    """Return a single role by its ID, or None if not found."""
    return ORG_ROLES.get(role_id)


def get_role_skills(role_id: str) -> list[dict[str, str]] | None:
    """Return skill details for a role, or None if role not found.

    Each skill is returned as a dict with ``skill_id``, ``name``,
    ``category``, and ``description`` keys.
    """
    role = ORG_ROLES.get(role_id)
    if role is None:
        return None
    skills = []
    for skill_id in role["skills"]:
        skill_def = SKILL_LIBRARY.get(skill_id)
        if skill_def is not None:
            skills.append({
                "skill_id": skill_id,
                "name": skill_def["name"],
                "category": skill_def["category"],
                "description": skill_def["description"],
            })
    return skills


def get_all_regulatory_ids_from_roles() -> set[str]:
    """Collect every regulatory framework ID referenced by any role."""
    ids: set[str] = set()
    for role in ORG_ROLES.values():
        ids.update(role["regulatory_frameworks"])
    return ids


def get_all_regulatory_ids_from_pipeline() -> set[str]:
    """Collect every regulatory framework ID referenced by pipeline stages."""
    ids: set[str] = set()
    for stage in PIPELINE_STAGES:
        ids.update(stage["regulations"])
    return ids


def get_all_skill_ids_from_roles() -> set[str]:
    """Collect every skill ID referenced by any role."""
    ids: set[str] = set()
    for role in ORG_ROLES.values():
        ids.update(role["skills"])
    return ids
