# 5. Associate Director, PV Operations (ICSR Case Processing)
> Parent: 2-head-ps | Children: -- | Cross-ref: 4-signal-mgmt, 7-aggregate-reporting, 8-pv-quality

## Role
Owns the day-to-day ICSR case processing pipeline for Prosinertimib: intake from all sources, triage, data entry, MedDRA coding, medical review, quality control, and regulatory submission of individual case safety reports. Ensures all cases are processed within regulatory timelines (7-day, 15-day, 90-day) and that the safety database is accurate, complete, and audit-ready.

## Regulatory Grounding
- **EU GVP Module VI:** Collection, Management, and Submission of Reports of Suspected Adverse Reactions
- **ICH E2B(R3):** Electronic Transmission of ICSRs (HL7/ICH format)
- **ICH E2D:** Post-Approval Safety Data Management
- **ICH E2A:** Clinical Safety Data Management (definitions, expedited reporting)
- **MedDRA:** Medical Dictionary for Regulatory Activities (current version for coding)
- **21 CFR 312.32:** IND Safety Reporting
- **21 CFR 314.80:** Post-marketing Reporting

## Sub-Processes

### 1. Case Intake & Triage
Receive adverse event reports from all sources: clinical trial sites (via CRO/EDC), spontaneous reports (HCPs, patients, call center), literature, regulatory authorities, and solicited programs. Triage within 24 hours: confirm minimum criteria, classify as serious/non-serious, and assign regulatory clock start date (Day 0).

**Day 0 Rules (GVP Module VI, Section VI.B.2):**
Day 0 is the date the MAH first possesses all four minimum valid ICSR criteria simultaneously:
1. An **identifiable reporter** (name, initials, or qualification such as HCP/consumer)
2. An **identifiable patient** (name, initials, age, sex, or other qualifier)
3. A **suspected medicinal product** (brand name, active substance, or description)
4. A **suspected adverse reaction** (verbatim term from reporter)

All four are non-negotiable for validity. If received across multiple contacts, Day 0 = date all four are available. Clock starts regardless of seriousness classification. For solicited reports (e.g., patient support programs), Day 0 = date information reaches PV-qualified personnel.

[NEEDS SUB-SKILL] Case intake and triage workflow with decision tree.

### 2. Data Entry & Narrative Writing
Enter case data into the safety database per E2B(R3) data elements. Write concise clinical narratives following the company narrative template: patient demographics, medical history, suspect product details (dose, indication, dates), event description (onset, course, outcome), relevant lab/diagnostic data, and reporter causality assessment. Target: data entry complete within 3 calendar days of receipt.

**E2B(R3) Minimum Data Elements (ICH E2B(R3) Implementation Guide):**

| Category | Required Elements |
|----------|------------------|
| **Transmission** | Batch number, sender/receiver IDs, transmission date |
| **Case ID** | Case identifier, report type (initial/follow-up/nullification), seriousness criteria, date of receipt |
| **Primary Source** | Reporter type (HCP, consumer, literature), reporter qualifications, country |
| **Patient** | Age (or age group), sex, weight, height, medical history, relevant conditions |
| **Reaction/Event** | MedDRA-coded term (LLT/PT), onset date, duration, outcome, seriousness criteria per reaction (E2B(R3) change from case-level) |
| **Drug Information** | Product name, active substance, dose, route, formulation, therapy dates, indication, action taken, rechallenge info, batch/lot number |
| **Causality** | Source of assessment (reporter, sponsor), method, result |
| **Narrative** | Case narrative, sender comments |

Null Flavor values (ASKU, MASK, NI) permitted per E2B(R3) to explain absent mandatory fields.

### 3. MedDRA Coding
Code all adverse events using current MedDRA version at the Lowest Level Term (LLT) level; system auto-maps to PT and SOC. Apply MedDRA Points to Consider for consistent term selection. For Prosinertimib EGFR-inhibitor AEs: ensure correct coding of dermatologic toxicities (acneiform rash vs. maculopapular rash), diarrhea grading, and ILD/pneumonitis distinction.

[NEEDS SUB-SKILL] MedDRA coding quality and consistency procedures.

### 4. Medical Review & Causality Assessment
Route all serious cases and cases of special interest to the designated medical reviewer. Medical reviewer assesses: company causality (using WHO-UMC criteria), seriousness criteria confirmation, expectedness against RSI/CCSI, and listedness against SmPC. Document medical reviewer comments and any case reclassification.

[NEEDS SUB-SKILL] Medical review and causality assessment protocol.

### 5. Quality Control (QC)
Perform QC on all cases before submission. QC checklist: narrative accuracy, MedDRA coding correctness, E2B data element completeness, regulatory timeline compliance, causality consistency, and duplicate check. Two-tier QC: 100% QC on expedited cases, statistical sampling (10-20%) on non-expedited. Track error rates by error category.

### 6. Regulatory Submission
Submit ICSRs to regulatory authorities per applicable timelines: 15-day (FDA IND safety reports for unexpected serious), 15-day (EudraVigilance SUSARs), 7-day (fatal/life-threatening unexpected), 90-day (non-expedited). Transmit via FDA ESG (E2B(R3)) and EudraVigilance gateway (EVWEB/E2B(R3)). Archive submission acknowledgments.

[NEEDS SUB-SKILL] Regulatory submission workflow and E2B(R3) transmission procedures.

### 7. Reconciliation & Duplicate Management
Perform reconciliation of safety data between: safety database and clinical trial EDC, safety database and CRO case tracker, FAERS/EudraVigilance and company database. Identify and merge duplicate cases per documented duplicate detection algorithm. Report reconciliation discrepancies and resolution.

**Reconciliation Frequency Requirements:**

| Reconciliation Pair | Frequency | Basis |
|---------------------|-----------|-------|
| Safety DB vs. clinical trial EDC | Monthly during active enrollment; quarterly in follow-up | GVP VI, ICH E2D |
| Safety DB vs. CRO case tracker | Monthly (per Quality Agreement) | GVP Module I (outsourced activity oversight) |
| Safety DB vs. FAERS/EudraVigilance | Quarterly | 21 CFR 314.80; GVP VI Addendum I |
| Duplicate detection sweep | Continuous (automated) + quarterly manual audit | GVP VI Addendum I |

### 8. Case Processing Metrics & Reporting
Track and report weekly operational metrics: cases received, cases processed, cases pending, aging report (cases approaching deadline), expedited submission compliance rate, QC error rate, and CRO performance against KPIs. Current YTD: 1,247 cases processed.

**CRO Oversight KPIs (per Quality Agreement with SafetyFirst Ltd):**

| KPI | Target | Measurement |
|-----|--------|-------------|
| Case intake acknowledgment | Within 24 hours of receipt | % cases acknowledged on time |
| Initial data entry completeness | >95% of E2B fields populated | Monthly audit sample (n=20) |
| Data entry accuracy | <3% error rate | QC findings per case reviewed |
| Expedited case processing | Completed within 5 calendar days | % cases meeting timeline |
| Follow-up request turnaround | Within 48 hours of trigger | Average response time |
| Reconciliation discrepancy rate | <2% per reconciliation cycle | Discrepancies / total cases |
| Training currency | 100% staff current on SOPs | Quarterly training compliance report |
| CAPA response time | Draft within 15 business days | Days from CAPA issuance to response |

Review CRO KPI dashboard monthly. Conduct formal CRO performance review quarterly. Trigger remediation plan if any KPI misses target for 2 consecutive months.

## Key Metrics
- Expedited reporting compliance rate (target: >98% within timeline)
- Average case processing time (receipt to submission)
- QC error rate (target: <5%)
- Case backlog / aging (cases >10 days without submission)
- Duplicate detection rate
- CRO KPI adherence (if outsourced)

## Cross-Functional Dependencies
- 4-signal-mgmt: coded case data feeds signal detection analyses
- 7-aggregate-reporting: line listings and case counts for PBRER/DSUR
- 8-pv-quality: QC metrics feed compliance reporting; SOPs govern all processes
- Clinical Operations: clinical trial SAE reconciliation
- IT: safety database uptime, E2B gateway connectivity, MedDRA version upgrades
- CRO (SafetyFirst Ltd): case intake and initial data entry per quality agreement

## Escalation
Reports to: 2-head-ps (Head of Patient Safety / Pharmacovigilance)
Escalate if: case processing backlog exceeding 48 hours, expedited case at risk of late submission, safety database system outage, CRO performance below KPI thresholds

## References

- references/gvp_module_summaries.md -- GVP Module VI
- references/ich_fda_summaries.md -- ICH E2B(R3); 21 CFR 312.32, 314.80
- references/literature_review.md -- Section 4: PV Outsourcing
