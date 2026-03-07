# Organizational Alignment Audit Report

**Date:** 2026-03-06
**Scope:** Skill files 1-8, _index.md, patient_safety_dashboard.html, patient_safety_routes.py

---

## 1. Process Ownership Overlap Findings

### 1a. Signal Detection

| Location | Context | Concern |
|----------|---------|---------|
| 4-signal-mgmt.md (sub-process a) | "Routine Signal Detection Screening" -- OWNS signal detection end-to-end | PRIMARY OWNER -- correct |
| 2-head-ps.md (sub-process b) | "Signal Escalation & Evaluation" -- receives signal detection outputs, validates/refutes | Acceptable: describes HEAD role as consumer/decision-maker, not performer |
| 1-cmo.md (SRC agenda item 1) | "Safety signal updates and dispositions" -- reviews at governance level | Acceptable: governance oversight, not operational ownership |

**Verdict: NO OVERLAP.** Signal detection is clearly owned by 4-signal-mgmt. File 2 describes the Head of PS as a consumer of signal outputs, which is correct role delineation.

### 1b. ICSR Processing

| Location | Context | Concern |
|----------|---------|---------|
| 5-pv-ops.md (header) | "Associate Director, PV Operations (ICSR Case Processing)" | PRIMARY OWNER -- correct |
| 2-head-ps.md (sub-process a) | "Daily Safety Oversight" -- reviews ICSR volume, triage queue, compliance metrics | Acceptable: oversight role |
| 3-qppv.md (sub-process 2) | "EudraVigilance Compliance" -- oversees ICSR submissions to EudraVigilance | POTENTIAL OVERLAP: EudraVigilance submission is an ICSR processing activity. Should clarify that QPPV has EU regulatory oversight of submissions while 5-pv-ops performs the actual submission work. |

**Verdict: MINOR OVERLAP.** 3-qppv sub-process 2 (EudraVigilance Compliance) overlaps with 5-pv-ops ICSR submission. The QPPV's role should be framed as regulatory oversight/compliance monitoring of EudraVigilance submissions, not operational execution. The current text in 3-qppv ("Oversee ICSR submissions") is appropriately worded but should explicitly reference 5-pv-ops as the executing function.

### 1c. RMP Maintenance

| Location | Context | Concern |
|----------|---------|---------|
| 6-risk-mgmt.md (header) | "Director, Risk Management & Epidemiology" | PRIMARY OWNER -- correct (stub file) |
| 2-head-ps.md (Dashboard Integration) | "Section 8: Risk Management (RMP, REMS, risk minimization)" | Acceptable: oversight reference |

**Verdict: NO OVERLAP.**

### 1d. PBRER/DSUR Authoring

| Location | Context | Concern |
|----------|---------|---------|
| 7-aggregate-reporting.md (header) | "Associate Director, Aggregate Reporting" | PRIMARY OWNER -- correct (stub file) |
| 2-head-ps.md (sub-process c) | "Aggregate Report Cycle Management" -- owns reporting calendar, assigns writing, reviews drafts | POTENTIAL OVERLAP: "Own the reporting calendar" and "assign writing responsibilities" could create ambiguity with 7-aggregate-reporting who should own the operational calendar. |
| 1-cmo.md (sub-process 2) | "CMO signs off on all benefit-risk conclusions in PSURs, DSURs, and RMP updates" | Acceptable: sign-off authority, not authoring |
| 4-signal-mgmt.md (sub-process h) | "Signal closure is recorded in the next PBRER/PSUR (Section 16.3) and DSUR (Section 10)" | Acceptable: describes signal data feeding into aggregate reports, not authoring |

**Verdict: MINOR OVERLAP.** 2-head-ps sub-process c claims to "own the reporting calendar" and "assign writing responsibilities," which is operational territory that should belong to 7-aggregate-reporting. The Head of PS role should be framed as approving the calendar and reviewing final drafts, while 7-aggregate-reporting owns the operational execution.

### 1e. SOP/CAPA/Training

| Location | Context | Concern |
|----------|---------|---------|
| 8-pv-quality.md (header) | "Manager, PV Quality & Compliance" | PRIMARY OWNER -- correct (stub file) |
| 2-head-ps.md (sub-process h) | "Own the 12 PV SOPs and ensure they undergo periodic review" | OVERLAP: 2-head-ps claims to "own" the SOPs. This should be 8-pv-quality's domain. The Head of PS approves SOPs but should not own the operational SOP management process. |
| 2-head-ps.md (sub-process h) | "Track training compliance for all PV personnel" | OVERLAP: Training compliance tracking is a quality system function owned by 8-pv-quality. |

**Verdict: OVERLAP FOUND.** 2-head-ps sub-process h ("PV System Maintenance") duplicates process ownership that belongs to 8-pv-quality. The Head of PS should approve SOPs and review training metrics, not own the processes.

### 1f. PSMF

| Location | Context | Concern |
|----------|---------|---------|
| 3-qppv.md (sub-process 1) | "PSMF Oversight & Maintenance" with explicit ownership note: QPPV has oversight/sign-off, 8-pv-quality does day-to-day maintenance | Correctly split |
| 2-head-ps.md (sub-process h) | "Maintain the Pharmacovigilance System Master File (PSMF) per GVP Module II" | OVERLAP: Contradicts the 3-qppv ownership note. 2-head-ps should not claim PSMF maintenance. |
| 8-pv-quality.md (header cross-ref) | Cross-refs 3-qppv | Consistent with PSMF split |

**Verdict: OVERLAP FOUND.** 2-head-ps claims PSMF maintenance, but this is explicitly assigned to 8-pv-quality (day-to-day) and 3-qppv (oversight/sign-off) in 3-qppv sub-process 1.

---

## 2. Missing Cross-Reference Findings

### 2a. Asymmetric Cross-References

| Skill A says... | But Skill B does not mention... | Gap |
|-----------------|--------------------------------|-----|
| 4-signal-mgmt cross-refs 8-pv-quality | 8-pv-quality does NOT cross-ref 4-signal-mgmt | 8-pv-quality header should add 4-signal-mgmt to cross-refs |
| 4-signal-mgmt says "Associate Director, Aggregate Reporting (7-aggregate-reporting): Signals feed PBRER Section 16.3" | 7-aggregate-reporting is a stub -- cannot verify reciprocal reference | GAP (pending 7 build-out): 7-aggregate-reporting should mention receiving signal data from 4-signal-mgmt |
| 4-signal-mgmt says "Director, Risk Management & Epidemiology (6-risk-mgmt): Receives validated signals for RMP/REMS impact" | 6-risk-mgmt is a stub -- cannot verify | GAP (pending 6 build-out): 6-risk-mgmt should mention receiving signal data from 4-signal-mgmt |
| 3-qppv cross-refs 4-signal-mgmt | 4-signal-mgmt does NOT cross-ref 3-qppv in header | 4-signal-mgmt header should add 3-qppv (QPPV sign-off on signals) |
| 6-risk-mgmt cross-refs 4, 5, 7 but NOT 8 | 8-pv-quality cross-refs 6-risk-mgmt | Asymmetric: 6-risk-mgmt should cross-ref 8-pv-quality |

### 2b. Missing Data Provider References

| Consumer | Data needed | Provider | Reference exists? |
|----------|-------------|----------|-------------------|
| 7-aggregate-reporting | Signal evaluation summaries for PBRER Section 16.3 | 4-signal-mgmt | Yes (in 4-signal-mgmt cross-functional deps) |
| 7-aggregate-reporting | ICSR line listings and case summaries | 5-pv-ops | Yes (in index cross-refs: 7 refs 5) |
| 7-aggregate-reporting | RMP effectiveness data | 6-risk-mgmt | Yes (in index cross-refs: 7 refs 6) |
| 4-signal-mgmt | Coded ICSR data for detection runs | 5-pv-ops | Yes (in 4-signal-mgmt cross-functional deps) |
| 6-risk-mgmt | Validated signals for RMP update | 4-signal-mgmt | Yes (in 4-signal-mgmt cross-functional deps) |
| 8-pv-quality | SOP compliance data from all functions | 4, 5, 6, 7 | MISSING: 8-pv-quality should reference all PV functions as SOP compliance data sources |

---

## 3. Title Consistency Check

### Role Titles Across All Sources

| # | Skill File Header | _index.md Table | API routes (role field) | Dashboard HTML | Consistent? |
|---|-------------------|-----------------|------------------------|----------------|-------------|
| 1 | "Chief Medical Officer -- Safety Oversight" | "Chief Medical Officer" | "Chief Medical Officer" | (shown in org chart via API) | MINOR: Skill file appends "-- Safety Oversight" qualifier. Not in other sources. |
| 2 | "Head of Patient Safety / Pharmacovigilance" | "Head of Patient Safety / PV" | role: "Head of Patient Safety / Pharmacovigilance", name: "Head of Patient Safety" | (via API) | INCONSISTENCY: Index uses "/PV" abbreviation. API name field uses shorter form. |
| 3 | "QPPV (EU) -- Qualified Person for Pharmacovigilance" | "QPPV (EU)" | "QPPV (EU)" | (via API) | MINOR: Skill file has long-form subtitle. |
| 4 | "Director, Signal Management & Safety Science" | "Director, Signal Management & Safety Science" | "Director, Signal Management & Safety Science" | (via API) | CONSISTENT |
| 5 | "Associate Director, PV Operations (ICSR Case Processing)" | "Associate Director, PV Operations" | "Associate Director, PV Operations" | (via API) | MINOR: Skill file appends "(ICSR Case Processing)" qualifier. |
| 6 | "Director, Risk Management & Epidemiology" | "Director, Risk Management & Epidemiology" | "Director, Risk Management & Epidemiology" | (via API) | CONSISTENT |
| 7 | "Associate Director, Aggregate Reporting" | "Associate Director, Aggregate Reporting" | "Associate Director, Aggregate Reporting" | (via API) | CONSISTENT |
| 8 | "Manager, PV Quality & Compliance" | "Manager, PV Quality & Compliance" | "Manager, PV Quality & Compliance" | (via API) | CONSISTENT |

### Title Inconsistencies to Fix

1. **_index.md line 34:** Uses "Head of Patient Safety / PV" -- should be "Head of Patient Safety / Pharmacovigilance" to match the skill file and API.

---

## 4. Escalation Chain Completeness

| # | Role | Reports To | Escalation Trigger | Escalates To | Complete? |
|---|------|------------|-------------------|--------------|----------|
| 1 | CMO | CEO/Board | Material business impact, product withdrawal, Warning Letters | CEO, Board of Directors | YES |
| 2 | Head of PS | CMO (1-cmo) | Fatal/life-threatening unexpected SUSARs, new mortality signals, clinical hold events, regulatory inquiries | CMO (immediate) or SMT (next meeting) | YES |
| 3 | QPPV | Head of PS (solid), CMO (dotted) | PV system inadequacy, resource constraints, management interference | CMO directly (bypassing Head of PS) | YES |
| 4 | Dir Signal Mgmt | Head of PS / QPPV | Fatal/life-threatening new signal, class-effect signal, urgent safety restriction, DSMB pause/stop, regulatory request | Head of PS and QPPV | YES |
| 5 | AD PV Ops | Head of PS (2-head-ps) | (STUB -- no escalation section) | Not defined | INCOMPLETE |
| 6 | Dir Risk Mgmt | Head of PS (2-head-ps) | (STUB -- no escalation section) | Not defined | INCOMPLETE |
| 7 | AD Aggregate Reporting | Head of PS (2-head-ps) | (STUB -- no escalation section) | Not defined | INCOMPLETE |
| 8 | Mgr PV Quality | Head of PS (2-head-ps) | (STUB -- no escalation section) | Not defined | INCOMPLETE |

**Verdict:** The escalation chain from 4 -> 2 -> 1 -> CEO/Board is complete. The chain from 3 -> 1 (independence path) is complete. Files 5-8 are stubs with only headers, so their escalation sections are missing entirely. These need to be built out.

---

## 5. Dashboard Section-to-Skill Owner Mapping

| Section | Dashboard Title | Primary Skill Owner | Secondary/Supporting |
|---------|----------------|--------------------|--------------------|
| 1 | Org Structure & Governance | 2-head-ps (operational), 1-cmo (governance) | All roles appear in org chart |
| 2 | US Regulatory Framework | 2-head-ps (reference material) | Cross-functional (Regulatory Affairs) |
| 3 | EU Regulatory Framework | 3-qppv (EU regulatory), 2-head-ps | Cross-functional (Regulatory Affairs) |
| 4 | ICH Guidelines | 2-head-ps (reference material) | All roles reference ICH |
| 5 | ICSR Case Processing | 5-pv-ops | 3-qppv (EudraVigilance oversight) |
| 6 | Signal Detection & Surveillance | 4-signal-mgmt | 2-head-ps (escalation recipient) |
| 7 | Aggregate Reporting | 7-aggregate-reporting | 2-head-ps (reviewer), 1-cmo (sign-off) |
| 8 | Risk Management | 6-risk-mgmt | 4-signal-mgmt (signal input) |
| 9 | Quality System | 8-pv-quality | 3-qppv (PSMF oversight) |
| 10 | Clinical Trial Safety | 1-cmo (DSMB oversight), 4-signal-mgmt (trial signal detection) | 5-pv-ops (SAE processing) |
| 11 | Safety Science & Benefit-Risk | 1-cmo (benefit-risk decisions), 2-head-ps (B-R leadership) | 4-signal-mgmt (signal input) |
| 12 | Technology Landscape | 8-pv-quality (system validation) | No clear single owner |
| 13 | KPIs & Metrics | 8-pv-quality (compliance metrics), 2-head-ps (oversight) | All roles contribute KPIs |
| 14 | Geographic Expansion | 3-qppv (LPPV network) | 2-head-ps (strategic) |
| 15 | Implementation Roadmap | 2-head-ps (strategic planning) | 8-pv-quality (milestone tracking) |

### Sections Without Clear Single Owner
- **Section 12 (Technology Landscape):** No skill file explicitly owns technology/system landscape. Recommend assigning to 8-pv-quality (system validation and compliance) or creating a cross-functional note.
- **Section 13 (KPIs & Metrics):** Aggregates KPIs from all roles. 8-pv-quality is the natural owner for the compliance scoreboard.

---

## 6. Recommended Fixes

### Priority 1 -- Overlap Corrections (in 2-head-ps.md)

1. **Sub-process c (Aggregate Report Cycle Management):** Change "Own the reporting calendar" to "Approve the reporting calendar maintained by Associate Director, Aggregate Reporting (7-aggregate-reporting)." Change "assign writing responsibilities" to "review writing assignments."
2. **Sub-process h (PV System Maintenance):** Change "Own the 12 PV SOPs" to "Approve PV SOPs maintained by Manager, PV Quality & Compliance (8-pv-quality)." Change "Track training compliance" to "Review training compliance reports from 8-pv-quality." Change "Maintain the PSMF" to "Review PSMF updates prepared by 8-pv-quality and approved by QPPV (3-qppv)."

### Priority 2 -- Title Fix (in _index.md)

1. Change "Head of Patient Safety / PV" to "Head of Patient Safety / Pharmacovigilance" in the index table.

### Priority 3 -- Missing Cross-References

1. **8-pv-quality.md:** Add 4-signal-mgmt and 7-aggregate-reporting to cross-refs.
2. **4-signal-mgmt.md:** Add 3-qppv to cross-refs (QPPV sign-off on signal closure).
3. **6-risk-mgmt.md:** Add 8-pv-quality to cross-refs.

### Priority 4 -- Stub Build-Out (Files 5, 6, 7, 8)

Files 5-8 are stubs with only the header line. They need full build-out including:
- Role description, regulatory grounding, sub-processes
- Escalation section (reports to, triggers, escalates to)
- Cross-functional dependencies
- Dashboard integration mapping
- Key metrics

---

## 7. Fixes Applied in This Audit

The following simple fixes were applied directly to skill files:

1. **_index.md:** "Head of Patient Safety / PV" corrected to "Head of Patient Safety / Pharmacovigilance"
2. **8-pv-quality.md:** Added 4-signal-mgmt and 7-aggregate-reporting to cross-refs
3. **4-signal-mgmt.md:** Added 3-qppv to cross-refs
4. **6-risk-mgmt.md:** Added 8-pv-quality to cross-refs
5. **2-head-ps.md:** Reworded sub-process c and h to clarify oversight vs. ownership (removed process ownership claims for SOPs, PSMF, reporting calendar, and training tracking)
