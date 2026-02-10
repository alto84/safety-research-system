# CAPA Tracker -- Cell Therapy Program

> **SIMULATED** -- This document is a simulated deliverable for the pharma company simulation.
> It does not represent any real company, product, or regulatory status.

**Document ID:** QA-CAPA-001
**Version:** 1.0
**Effective Date:** 2026-02-09
**Prepared by:** Head of Quality Assurance (Simulated)
**Review Cycle:** Monthly

---

## Purpose

This tracker records all Corrective and Preventive Actions (CAPAs) for the cell therapy program. CAPAs are initiated when systemic issues are identified through deviations, audit findings, complaints, OOS results, or trend analysis. Root cause investigations follow ICH Q9(R1) risk management principles, and effectiveness checks are required before closure.

---

## ICH Q9 Risk Categories Referenced

All CAPAs are classified using ICH Q9(R1) risk categories:

| Risk Category | Description | Example in Cell Therapy |
|---------------|-------------|------------------------|
| **Patient Safety** | Direct risk to patient health or product quality | Sterility failure, potency OOS, COI mix-up |
| **Product Quality** | Risk to meeting product specifications | Viability below spec, endotoxin exceedance |
| **Data Integrity** | Risk to accuracy, completeness, or reliability of data | Batch record errors, ALCOA+ deviations |
| **Regulatory Compliance** | Risk of non-compliance with applicable regulations | GMP deviation, training gaps, audit findings |
| **Supply Chain / Logistics** | Risk to material supply or product distribution | Temperature excursion, vendor quality failure |

---

## Open CAPA Log

| CAPA ID | Date Opened | Source | Description | Root Cause Category | ICH Q9 Risk Category | Severity | Status | Due Date | Owner |
|---------|-------------|--------|-------------|--------------------|--------------------|----------|--------|----------|-------|
| CAPA-2026-001 | 2026-01-15 | Deviation DEV-2026-004 | **Temperature excursion during cryoshipment to Site 002.** Dry shipper data logger recorded temperature of -142C for approximately 45 minutes during transit (specification: <= -150C). Product was placed on quality hold pending disposition. Investigation revealed shipper was loaded 6 hours before courier pickup, exceeding the validated 4-hour hold time. | Procedural -- SOP did not specify maximum hold time between shipper loading and courier pickup. | Supply Chain / Logistics; Product Quality | High | **Investigation Complete -- Corrective Action In Progress.** Root cause confirmed. Corrective action: revise SOP-SHIP-003 to include maximum 2-hour hold time between loading and pickup. Preventive action: add hold-time check to shipping checklist; qualify backup shipping lane. Effectiveness check: monitor next 5 shipments for compliance. | 2026-03-15 | Director, Supply Chain |
| CAPA-2026-002 | 2026-01-22 | Internal Review | **Documentation error in Batch Record BR-2026-003.** Manufacturing operator recorded cell count at Step 5 (expansion) but entered the value in the Step 6 (harvest) field. Error discovered during QA batch record review. The correct value was verified from the raw instrument printout. No impact to product quality (data was accurate, entry location was wrong). | Human Error -- Batch record form design contributed to error; Steps 5 and 6 fields are adjacent with similar formatting. | Data Integrity; Regulatory Compliance | Medium | **Root Cause Analysis In Progress.** Preliminary assessment: batch record layout contributes to transcription errors. Proposed corrective action: redesign batch record pages 12-14 to add visual separation between steps and require independent verification signatures for cell count entries. Evaluating electronic batch record (eBR) system as long-term preventive action. | 2026-03-31 | QA Manager |
| CAPA-2026-003 | 2026-01-28 | Internal Audit AUD-2025-002 | **Training gap identified during manufacturing area audit.** Audit finding F-2025-002-03: two manufacturing technicians had not completed annual retraining on SOP-MFG-010 (Aseptic Technique) within the required 12-month window. Training records showed last completion 14 months prior. No deviations or contamination events linked to these individuals during the gap period. | Systemic -- Training management system (spreadsheet-based) lacks automated alerts for training due dates. | Regulatory Compliance; Patient Safety | High | **Corrective Action In Progress.** Immediate action: both technicians retrained and competency-assessed (completed 2026-02-03). Corrective action: implement monthly training compliance report reviewed by QA. Preventive action: evaluate Learning Management System (LMS) vendors with automated recurrence alerts. RFP issued to 3 vendors. | 2026-04-15 | Training Coordinator |
| CAPA-2026-004 | 2026-02-01 | Protocol Deviation PD-2026-001 (Site 001) | **Protocol deviation: patient infused outside the specified window.** Protocol requires CAR-T infusion within 72 hours of thaw. Patient 004 was infused at 78 hours post-thaw due to clinical hold for transient fever (unrelated to product). Investigator assessed the deviation as having no impact on product quality (post-thaw stability data supports 96-hour window at 2-8C). Reported to IRB and Sponsor per protocol requirements. | Operational -- Protocol did not include provisions for clinical holds extending the infusion window. Clinical scenario was foreseeable but not addressed in the protocol. | Patient Safety; Regulatory Compliance | Medium | **Investigation Complete -- Preventive Action Pending.** Root cause: protocol lacked flexibility for clinical holds. No product quality impact (supported by stability data). Corrective action: submit protocol amendment to add provision for clinical holds with documented justification (up to 96 hours supported by stability data). Preventive action: add clinical hold scenario to site training materials. Protocol amendment drafted, pending Sponsor and IRB review. | 2026-04-30 | VP Clinical Operations |
| CAPA-2026-005 | 2026-02-05 | OOS Investigation OOS-2026-001 | **Out-of-specification result: endotoxin in Batch BR-2026-005.** Release testing for Batch BR-2026-005 (Patient 006) returned endotoxin result of 6.2 EU/kg (specification: < 5.0 EU/kg). Batch placed on hold. Phase 1 OOS investigation initiated per SOP-QC-015. Laboratory investigation (Phase 1): sample retested in duplicate -- results 2.1 EU/kg and 2.3 EU/kg. Original result attributed to potential sample handling error (LAL reagent lot was at end of qualified shelf life). | Under Investigation -- Phase 2 investigation initiated to determine if assignable laboratory cause exists. Potential contributing factors: LAL reagent lot nearing expiration, sample handling during initial test. | Product Quality; Patient Safety | Critical | **Phase 2 Investigation In Progress.** Phase 1 (lab investigation) complete: retest results within specification. Phase 2 (manufacturing investigation) in progress to rule out process-related endotoxin introduction. If Phase 2 confirms laboratory assignable cause, batch may be dispositioned for release based on retest results per SOP-QC-015. Corrective action (proposed): implement LAL reagent lot-use tracking with 30-day pre-expiry alert. Preventive action: add duplicate testing requirement for endotoxin at release. | 2026-03-15 | QC Director |

---

## CAPA Summary Metrics

| Metric | Value |
|--------|-------|
| Total Open CAPAs | 5 |
| Critical Severity | 1 (CAPA-2026-005) |
| High Severity | 2 (CAPA-2026-001, CAPA-2026-003) |
| Medium Severity | 2 (CAPA-2026-002, CAPA-2026-004) |
| Overdue CAPAs | 0 |
| Average Age (days) | 18 |
| CAPAs Closed YTD (2026) | 0 |
| CAPAs Opened YTD (2026) | 5 |

---

## Root Cause Category Distribution

| Root Cause Category | Count | Percentage |
|--------------------|-------|------------|
| Procedural (SOP gaps) | 1 | 20% |
| Human Error | 1 | 20% |
| Systemic (system/tool gaps) | 1 | 20% |
| Operational (protocol/process gaps) | 1 | 20% |
| Under Investigation | 1 | 20% |

---

## ICH Q9 Risk Category Distribution

| Risk Category | CAPAs Involving |
|---------------|----------------|
| Patient Safety | 3 (CAPA-2026-003, -004, -005) |
| Product Quality | 3 (CAPA-2026-001, -005, -002 secondary) |
| Data Integrity | 1 (CAPA-2026-002) |
| Regulatory Compliance | 3 (CAPA-2026-002, -003, -004) |
| Supply Chain / Logistics | 1 (CAPA-2026-001) |

*Note: CAPAs may map to multiple ICH Q9 risk categories.*

---

## Escalation Criteria

Per QA-SOP-001, CAPAs are escalated to the CEO when:
- Severity is Critical
- Patient safety is directly impacted
- Regulatory notification may be required (e.g., IND safety report, field alert)
- CAPA is overdue by more than 30 days

**Current escalations:** CAPA-2026-005 (Critical -- endotoxin OOS) escalated to CEO on 2026-02-06 per SOP.

---

## Document History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-02-09 | Head of QA (Simulated) | Initial creation with 5 open CAPAs |

---

*This tracker is reviewed monthly during the QA management review meeting. CAPA status updates are provided to the CEO weekly.*
