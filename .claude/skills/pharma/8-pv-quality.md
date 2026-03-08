# 8. Manager, PV Quality & Compliance
> Parent: 2-head-ps | Children: -- | Cross-ref: 3-qppv, 4-signal-mgmt, 5-pv-ops, 6-risk-mgmt, 7-aggregate-reporting

## Role
Owns the pharmacovigilance quality management system (PV QMS) for the Patient Safety organization: SOPs, work instructions, CAPA management, training compliance, internal audits, and inspection readiness. Ensures PV activities comply with GVP Module I (Section I.B.2-I.B.4), ICH Q10 principles applied to PV, and applicable CFR requirements. Acts as the PV quality point of contact during regulatory inspections. Receives SOP compliance data from all PV functions (4, 5, 6, 7) as input for quality metrics.

## Regulatory Grounding
- **EU GVP Module I (EMA/541760/2011):** Pharmacovigilance Systems and Their Quality Systems (Section I.B: quality system elements)
- **EU GVP Module III:** Pharmacovigilance Inspections (inspection scope, common findings, CAPA expectations)
- **EU GVP Module II:** PSMF content and format requirements (day-to-day maintenance performed here; oversight by 3-qppv)
- **EU Implementing Regulation 520/2012:** PSMF requirements
- **ICH Q10:** Pharmaceutical Quality System (CAPA, management review, continuous improvement)
- **21 CFR 314.80:** Post-marketing reporting compliance
- **21 CFR Part 11:** Electronic records and signatures (PV database validation)

## Sub-Processes

### 1. SOP & Work Instruction Management
Maintain the PV SOP library (12-15 SOPs for single-product company). Each SOP must have: designated owner (from the relevant function -- e.g., signal detection SOP owned by 4-signal-mgmt), review cycle (every 2 years per GVP Module I, Section I.B.9, or upon regulatory change), version control, training record linkage, and effective date. Key SOPs:
- PV-SOP-001: ICSR intake & triage (owner: 5-pv-ops)
- PV-SOP-002: Expedited safety reporting (owner: 5-pv-ops)
- PV-SOP-003: Signal management (owner: 4-signal-mgmt)
- PV-SOP-004: PBRER/PSUR authorship (owner: 7-aggregate-reporting)
- PV-SOP-005: Safety database management (owner: 5-pv-ops)
- PV-SOP-006: Vendor/CRO oversight (owner: 8-pv-quality)
- PV-SOP-007: QPPV responsibilities (owner: 3-qppv)
- PV-SOP-008: Literature surveillance (owner: 4-signal-mgmt)
- PV-SOP-009: SAE reconciliation (owner: 5-pv-ops)
- PV-SOP-010: RMP maintenance (owner: 6-risk-mgmt)
- PV-SOP-011: Training management (owner: 8-pv-quality)
- PV-SOP-012: CAPA management (owner: 8-pv-quality)

Note: The Head of PS (2-head-ps) approves all SOPs; this role manages the SOP lifecycle process.

### 2. CAPA Management
Manage the PV CAPA system per ICH Q10 principles: identification (from audits, deviations, inspections, complaints), root cause analysis, corrective action implementation, effectiveness check (30-90 days post-implementation), and closure. Track CAPA aging (target: close within 90 days per GVP Module I). Escalate overdue CAPAs (>120 days) to Head of PV. Current tracker: 7 open CAPAs.

**Root Cause Analysis Methodology:**

| Method | Application | When to Use |
|--------|-------------|-------------|
| **Ishikawa (Fishbone) Diagram** | Categorize causes across 6 domains: People, Process, Procedure, Systems, Materials, Environment | Complex/systemic deviations with multiple potential contributing factors; all critical findings |
| **5-Why Analysis** | Iterative "Why?" questioning to trace causal chain from symptom to root cause (minimum 5 iterations) | All CAPAs as initial triage; sufficient as sole method for minor/isolated deviations |

CAPA workflow: (1) Identify deviation and classify severity, (2) Document immediate containment action, (3) Perform root cause analysis (5-Why minimum; Ishikawa mandatory for critical/major), (4) Define corrective action with owner and due date, (5) Implement, (6) Effectiveness check at 30-90 days post-implementation, (7) Close with documented evidence of sustained correction.

[NEEDS SUB-SKILL] CAPA management lifecycle and root cause analysis procedures.

Common CAPA triggers (from GVP inspection findings -- see references/literature_review.md):
- Late expedited report submissions
- Incomplete ICSR data elements
- Missing or inadequate medical review documentation
- SOP non-compliance or outdated SOPs
- Training gaps for new PV personnel

### 3. Training Program Management
Maintain role-based PV training curriculum aligned to GVP Module I, Section I.B.7. Training requirements by role type:
- **All PV staff:** GVP fundamentals, company PV system overview, applicable SOPs (initial + annual refresher)
- **Case processors (5-pv-ops):** MedDRA coding, E2B(R3) data elements, narrative writing, safety database operation
- **Signal analysts (4-signal-mgmt):** Disproportionality methods, EVDAS navigation, signal validation methodology
- **Medical reviewers:** Causality assessment (WHO-UMC criteria), seriousness/expectedness determination
- **Report authors (7-aggregate-reporting):** ICH E2C(R2)/E2F templates, benefit-risk framework
- **CRO staff (outsourced):** Company SOPs applicable to their delegated functions

**Detailed Training Matrix by Role:**

| Role | Initial Training | Ongoing/Refresher | Additional |
|------|-----------------|-------------------|------------|
| **Case processors** | GVP basics, E2B(R3) data elements, MedDRA coding, safety DB SOP, expedited timelines | Annual: SOP updates, MedDRA version changes | New product onboarding |
| **Medical reviewers** | Causality assessment (WHO-UMC), seriousness criteria, expectedness vs RSI/CCSI | Annual: RSI/CCSI updates, new safety concerns | Signal awareness training |
| **Signal analysts** | GVP Module IX, disproportionality methods, EVDAS navigation, signal tracking SOP | Annual: methodology updates, PRAC guidance | New database tool training |
| **Report authors** | ICH E2C(R2)/E2F templates, benefit-risk methodology, data integration | Annual: template/regulatory changes | EURD list management |
| **Risk management** | GVP V/VIII/XVI, RMP template, PASS design, ENCEPP standards | Annual: PRAC guidance updates | Epidemiological methods |
| **PV quality staff** | GVP Module I/III, CAPA/Ishikawa/5-Why, audit techniques, PSMF requirements | Annual: inspection trends, regulatory changes | Lead auditor certification |
| **CRO staff** | Company SOPs for delegated functions, safety DB access procedures | Annual: SOP refresher per quality agreement | As triggered by CAPA findings |
| **All PV personnel** | PV system overview, data privacy/GDPR, SOX/compliance awareness | Annual refresher on all role-relevant SOPs | Ad hoc: regulatory change alerts |

Track training compliance rate (target: >95%). Training must be completed before performing regulated activities. Document competency assessment. No regulated activity permitted before training record is confirmed in LMS.

### 4. Internal PV Audit Program
Execute annual PV internal audit plan covering: ICSR processing compliance (5-pv-ops), expedited reporting timeliness (5-pv-ops), signal detection process adherence (4-signal-mgmt), aggregate report quality (7-aggregate-reporting), vendor/CRO PV oversight, PSMF accuracy (3-qppv). Issue audit reports with findings classified per GVP Module III:
- **Critical:** Conditions, practices, or processes that adversely affect patient safety or data integrity
- **Major:** Non-compliance with applicable regulations/guidelines that could potentially affect patient safety
- **Minor:** Observations not directly affecting compliance but worth improving

Track finding closure within agreed timelines.

### 5. PSMF Maintenance (Day-to-Day)
Maintain the Pharmacovigilance System Master File per GVP Module II. Update within 30 days of any change. Full annual review. Coordinate with 3-qppv for QPPV oversight and sign-off. PSMF must be available to inspectors within 7 days of request (electronic access preferred).

**PSMF Content Checklist (GVP Module II):**

| Section | Required Content |
|---------|-----------------|
| **QPPV details** | Name, contact, CV, EU/EEA residence confirmation, deputisation arrangements, availability declaration |
| **Organizational structure** | Org chart with PV staffing (FTEs by function), reporting lines, site locations, contact details |
| **Computerized systems** | Safety database name/version/vendor, validation status (IQ/OQ/PQ), E2B(R3) compliance, backup/recovery procedures, 21 CFR Part 11/Annex 11 compliance |
| **Contractual arrangements** | List of all PV service providers (CROs, LPPVs, vendors), quality agreement summaries, scope of delegated activities, oversight mechanisms |
| **Data sources** | Description of all AE intake channels: clinical trial sites, spontaneous (HCP/consumer), literature, regulatory authorities, solicited programs, registries |
| **PV processes** | References to SOPs covering: ICSR processing, signal management, aggregate reporting, risk management, literature monitoring, reconciliation |
| **Quality system** | CAPA system description, internal audit schedule and findings summary, training system, compliance metrics summary |
| **Product list** | All authorized products with MA numbers, DIBD/IBD, applicable safety concerns, RMP status |
| **Logbook (Annex I)** | Chronological log of all PSMF changes with dates, descriptions, and responsible person |

### 6. PV Vendor & CRO Oversight
Qualify and oversee PV service providers per GVP Module I, Section I.C.1 (MAH responsibility for delegated activities). Maintain quality agreements with defined KPIs:
- **SafetyFirst Ltd (case intake):** Processing timeliness (<24h serious, <5d non-serious), data accuracy (>98%), query response (<48h)
- **MedSearch Global (literature):** Screening recall (>95%), false positive rate (<30%), search string coverage
- **PharmaLex (LPPV):** Local submission timeliness (100%), regulation tracking accuracy
- **Argus Cloud (DB):** System uptime (>99.5%), E2B transmission success, validation currency

Conduct quarterly business reviews. Annual on-site audits for SafetyFirst Ltd and MedSearch Global. Maintain vendor CAPA tracker.

### 7. Inspection Readiness & Response
Maintain perpetual inspection readiness for GVP inspections (EMA per GVP Module III), MHRA pharmacovigilance inspections, and FDA 314.80 compliance inspections. **Common GVP Inspection Findings -- Ranked (EMA/MHRA 2018-2023, literature_review.md Section 5):**

| Rank | Finding Category | Typical Deficiencies |
|------|-----------------|---------------------|
| 1 | **Quality Management System** | Inadequate CAPA management, delayed audit reports, PSMF not reflecting actual operations |
| 2 | **Risk Management** | RMP not updated with new safety information, missing effectiveness evaluation of RMMs |
| 3 | **Ongoing Safety Evaluation** | Signal management process gaps, incomplete signal tracking documentation, decision rationale missing |
| 4 | **ADR Case Processing** | Data entry errors, MedDRA coding inaccuracies, causality assessment quality, incomplete follow-up |
| 5 | **Reporting compliance** | Delayed expedited submissions, inconsistent serious/non-serious classification |
| 6 | **Documentation** | Insufficient decision rationale, incomplete audit trails |
| 7 | **Training** | Gaps in role-specific training, training not completed before task execution |
| 8 | **Vendor oversight** | Quality agreements missing KPIs, no evidence of ongoing CRO performance monitoring |
| 9 | **Database validation** | Safety database not fully validated per Part 11/Annex 11 |
| 10 | **Medical review** | Inadequate medical review of cases, no documented access to medically qualified person |

Use this ranking to prioritize mock inspection scenarios and internal audit focus areas.

Conduct annual mock inspections. During inspections: coordinate document requests, prepare back-room team, track inspector observations, draft CAPA responses within regulatory timelines.

### 8. PV Metrics & Management Review
Compile monthly PV quality metrics dashboard integrating data from all functions:
- ICSR compliance rates from 5-pv-ops (timeliness, completeness)
- Signal detection metrics from 4-signal-mgmt (signals detected/validated/closed)
- Aggregate report timeliness from 7-aggregate-reporting (on-time submission rate)
- SOP currency, training compliance, CAPA status (internal)

Present quarterly PV quality review to Head of PV (2-head-ps) and senior management per GVP Module I management review requirements.

## Key Metrics
- SOP currency rate (% of SOPs within review cycle)
- CAPA closure rate within 90 days (target: >90%)
- Training compliance rate (target: >95%)
- Expedited reporting compliance rate (15-day / 7-day) -- sourced from 5-pv-ops
- Internal audit finding closure rate
- Inspection readiness score (self-assessment, quarterly)
- Vendor KPI adherence rates

## Cross-Functional Dependencies
- 5-pv-ops: quality metrics derived from case processing data; SOPs governing ICSR workflow
- 4-signal-mgmt: SOP governance for signal detection process; signal metrics for quality dashboard
- 7-aggregate-reporting: quality review of reports before submission; report timeliness metrics
- 6-risk-mgmt: SOP for RMP maintenance; PASS quality oversight
- 3-qppv: PSMF oversight coordination; inspection readiness alignment
- IT/Validation: safety database validation and Part 11 compliance
- Corporate Quality: alignment with company-wide QMS where applicable

## Escalation
Reports to: 2-head-ps (Head of Patient Safety / Pharmacovigilance)
Escalate if: critical audit finding, inspection notification received, systemic compliance failure (e.g., expedited reporting rate <90%), CAPA requiring process redesign, vendor performance critically below KPIs

## References

- references/gvp_module_summaries.md -- GVP Modules I, II, III
- references/ich_fda_summaries.md -- 21 CFR 314.80, Part 11
- references/literature_review.md -- Section 5: PV Quality Systems, Common Inspection Findings
- references/operational_improvement_plan.md -- CRO oversight KPI framework
