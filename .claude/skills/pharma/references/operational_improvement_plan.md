# Operational Improvement Plan: PV Organization for Prosinertimib (EGFR Inhibitor, NSCLC)

## Prepared by: Head of Patient Safety / Pharmacovigilance
## Regulatory Basis: GVP Modules I, V, VI, IX; ICH E2B(R3), E2C(R2), E2F; 21 CFR 312.32, 314.80

---

## 1. Org Chart vs. API Role Inconsistencies

The dashboard org chart shows 4 direct reports; the API shows 5 director-level roles. These must be reconciled.

| Dashboard Role | API Role | Issue | Recommendation |
|---|---|---|---|
| QPPV (EU) | -- not in API | QPPV is a legal designation, not an operational role. If the QPPV also holds an operational function (e.g., Safety Science Lead), this should be explicit. | Retain QPPV as a designated person overlay. The QPPV should be one of the existing directors (recommend: Director, Signal Management or Safety Science Lead). Do NOT create a standalone QPPV headcount unless volume justifies it. |
| Safety Science Lead | Director, Signal Management | Same function, different names. | Standardize to **Director, Signal Management & Safety Science**. Single role, single person. |
| PV Operations Manager | VP PV Operations (now: Associate Director, PV Operations) | Title inflation in API. For a single-product company with 18 FTEs, a VP title is not warranted. **RESOLVED.** | Standardize to **Associate Director, PV Operations**. The "VP" title should be reserved for when the portfolio exceeds 2 products or case volume exceeds 5,000/year. |
| Safety Surveillance Director | -- split across two API roles | Dashboard merges literature monitoring and signal detection. API separates them correctly. | Keep them functionally separated per GVP Module IX (signal management must have independence from case processing). Literature screening is outsourced to MedSearch Global, so the internal role is oversight, not execution. |
| -- not in dashboard | Director, Risk Management & Epidemiology | Missing from dashboard entirely. | Add to dashboard. This is a GVP Module V requirement. For a single approved product with an EU RMP obligation, this role is non-negotiable. |
| -- not in dashboard | Associate Director, Aggregate Reporting | Missing from dashboard. | Add to dashboard. PSUR/PBRER, DSUR, and PADER are distinct deliverables requiring dedicated ownership. |
| -- not in dashboard | Manager, PV Quality & Compliance | Missing from dashboard. | Add to dashboard. Per GVP Module I, the quality system for PV must be identifiable and auditable. |

### Resolved Org Chart (Recommended)

```
Head of Patient Safety / Pharmacovigilance
├── QPPV (EU) — designated person, overlay on Director Signal Mgmt
├── Director, Signal Management & Safety Science
│   ├── Signal detection (quantitative: PRR/ROR/EBGM)
│   ├── Signal validation & clinical assessment
│   └── Benefit-risk assessment support
├── Associate Director, PV Operations
│   ├── ICSR intake, triage, data entry (outsourced to SafetyFirst Ltd)
│   ├── Medical review (INTERNAL — see Gap #1 below)
│   ├── QC and submission
│   └── Safety database administration (Argus Cloud)
├── Director, Risk Management & Epidemiology
│   ├── EU RMP authoring and maintenance
│   ├── US REMS (if required)
│   ├── Risk minimization measure effectiveness evaluation
│   └── Epidemiological study oversight
├── Associate Director, Aggregate Reporting
│   ├── PSUR/PBRER authoring
│   ├── DSUR authoring
│   └── PADER coordination
└── Manager, PV Quality & Compliance
    ├── SOP lifecycle management (12 SOPs)
    ├── Internal audit program
    ├── CAPA management
    ├── Training program
    └── PSMF maintenance
```

**Net change:** Dashboard goes from 4 visible roles to 6 (adding Risk Management, Aggregate Reporting, PV Quality). QPPV becomes an overlay, not a separate box. Title adjustments applied.

---

## 2. Operational Gaps

### Gap 1: Medical Review of ICSRs (CRITICAL)
**Current state:** Case intake is outsourced to SafetyFirst Ltd. There is no explicit medical review function visible in either dashboard or API.
**Regulatory requirement:** GVP Module VI requires that serious ICSRs undergo medical/scientific assessment by a qualified healthcare professional. Outsourcing data entry is standard; outsourcing medical causality assessment is high-risk.
**Recommendation:** Establish 1 internal Safety Physician (MD or PharmD with PV experience) reporting to the Associate Director, PV Operations. This person performs causality assessment, seriousness/expectedness determination, and medical narrative review for all serious cases. For a case volume of ~42 ICSRs with 8 serious (based on current simulation data), this is a part-time function that can be combined with medical review duties for aggregate reports.

### Gap 2: CRO Oversight Framework (HIGH)
**Current state:** Four outsourced vendors, no visible vendor management function or KPI framework.
**Regulatory requirement:** GVP Module I (Section I.C.1) requires that the MAH remains responsible for all delegated PV activities and maintains oversight.
**Recommendation:**
- Assign vendor oversight to PV Quality & Compliance (for audit/qualification) and PV Operations (for day-to-day KPIs).
- Define KPIs per vendor:
  - **SafetyFirst Ltd:** Case processing timeliness (<24h serious, <5 days non-serious), data accuracy rate (>98%), query response time (<48h).
  - **MedSearch Global:** Literature screening recall (>95%), false positive rate (<30%), coverage of defined search strings.
  - **PharmaLex (LPPV):** Local submission timeliness (100% on-time), local regulation tracking accuracy.
  - **Argus Cloud:** System uptime (>99.5%), E2B(R3) transmission success rate, validation status currency.
- Conduct quarterly business reviews with all vendors. Annual on-site audits for SafetyFirst Ltd and MedSearch Global.

### Gap 3: Aggregate Reporting Resources (MEDIUM)
**Current state:** No dedicated aggregate reporting role visible in dashboard. The report calendar for a single approved product includes: PBRER (typically every 6 months for 2 years post-approval, then annually), DSUR (if ongoing trials), PADER (US, annually).
**Regulatory requirement:** ICH E2C(R2) requires that PBRER authoring is performed by qualified personnel with access to cumulative safety data.
**Recommendation:** The Associate Director, Aggregate Reporting should have 1 medical writer (can be outsourced) and direct access to the safety database. For the current volume (1 product, 3 aggregate reports/year), 1.0 FTE internal + 0.5 FTE outsourced medical writing is sufficient.

### Gap 4: Clinical Trial Safety / SAE Reconciliation (MEDIUM)
**Current state:** Dashboard Section 10 covers clinical trial safety but no role is explicitly mapped to it.
**Recommendation:** Clinical trial SAE reconciliation (matching ICSR database to clinical database) should be owned by PV Operations with defined reconciliation frequency (monthly during active enrollment, quarterly during follow-up). Assign to the Associate Director, PV Operations with a reconciliation SOP.

---

## 3. Process Improvements

### 3a. ICSR Processing Workflow
**Current workflow (inferred):** Case received by SafetyFirst Ltd -> data entry in Argus -> QC by SafetyFirst -> submission.
**Problem:** Medical review step is invisible. Causality assessment may be happening at the CRO without adequate physician oversight.
**Improved workflow:**
1. Case receipt and triage (SafetyFirst Ltd, <24h for serious)
2. Data entry and coding (SafetyFirst Ltd, MedDRA coding)
3. QC check (SafetyFirst Ltd, data completeness and coding accuracy)
4. **Medical review (INTERNAL Safety Physician)** -- causality, expectedness, seriousness confirmation, narrative review
5. Approval and submission (PV Operations, regulatory timeline compliance)
6. Follow-up management (SafetyFirst Ltd, with internal oversight)

### 3b. Signal Triage Process
**Current state:** Signal detection exists (Section 6) but triage from detection to action is not formalized.
**Improved process per GVP Module IX:**
1. **Detection** (automated, monthly): Run PRR/ROR/EBGM on cumulative data. Literature signals from MedSearch Global.
2. **Validation** (Director, Signal Management & Safety Science, within 30 days of detection): Clinical review, biological plausibility, confounding assessment.
3. **Prioritization** (SMT, monthly meeting): Classify as validated/refuted/under evaluation. Assign priority (high/medium/low).
4. **Assessment** (within 60 days of validation for high priority): Full signal assessment report with benefit-risk impact.
5. **Action** (Head of PV decision, within 30 days of assessment): Label update, DHPC, RMP amendment, study protocol amendment, or continued monitoring.
6. **Tracking** (PV Quality): Signal tracking log with audit trail.

### 3c. PSMF Maintenance
**Current state:** No mention of PSMF in current structure.
**Recommendation:** The PSMF is a legal requirement under EU PV legislation (Directive 2010/84/EU, Regulation 1235/2010). Assign PSMF maintenance to PV Quality & Compliance. Update within 30 days of any change to PV system (personnel, vendor, database, process). Conduct annual full review.

---

## 4. Resource Allocation Assessment

### Current: 18 Internal FTEs + 24 Outsourced

For a single-product EGFR inhibitor (approved, NSCLC indication), this total headcount of 42 is reasonable but the ratio deserves scrutiny.

**Benchmarking (single-product, small-to-mid pharma):**
- Industry range: 12-25 internal FTEs for PV
- Outsourcing ratio: 40-60% outsourced is standard for case processing and literature screening
- Current ratio: 57% outsourced (24/42) -- within normal range

**Assessment by function:**

| Function | Current Internal | Current Outsourced | Recommended Internal | Recommended Outsourced | Rationale |
|---|---|---|---|---|---|
| PV Operations (ICSR) | ~4 | ~12 (SafetyFirst) | 3-4 (incl. 1 Safety Physician) | 10-12 | Case volume (~200-500/yr for single approved EGFR inhibitor) supports this. The Safety Physician is the critical internal add. |
| Signal Management | ~3 | 0 | 3 | 0 | Signal management should be fully internal per GVP Module IX best practice. Clinical judgment cannot be outsourced. |
| Risk Management | ~2 | ~2 | 2 | 1-2 (epi study support) | RMP authoring internal; epidemiological study execution can be outsourced to CRO. |
| Aggregate Reporting | ~2 | ~3 (medical writing) | 2 | 2-3 (medical writing) | Keep strategic oversight internal; outsource document production. |
| PV Quality | ~2 | 0 | 2 | 0 | Quality function must be internal for independence. |
| Literature Screening | ~1 | ~4 (MedSearch) | 1 (oversight) | 3-4 | Appropriate to outsource; internal role is oversight and search strategy. |
| LPPV | 0 | ~3 (PharmaLex) | 0 | 3 | Fully outsourced LPPV is standard for small-to-mid pharma. |
| Database Admin | ~1 | Argus Cloud | 1 | Argus Cloud | Need internal system owner even with cloud-hosted database. |
| QPPV/Leadership | ~3 | 0 | 3 (Head PV + QPPV overlay + admin) | 0 | -- |
| **Total** | **~18** | **~24** | **17-19** | **19-24** | Slight internal optimization possible |

**Key recommendation:** The total is appropriate. The critical gap is not headcount but the Safety Physician role (internal medical review). This can be filled by converting one outsourced FTE to an internal hire, keeping total cost neutral.

---

## 5. Roles to Add, Rename, Consolidate, or Split

| Action | Role | Justification |
|---|---|---|
| **ADD** | Safety Physician (1 FTE) | Medical review of serious ICSRs, causality assessment. GVP Module VI requirement. |
| **RENAME** | PV Operations Manager -> Associate Director, PV Operations | Right-size title for single-product company |
| **RENAME** | Safety Science Lead -> Director, Signal Management & Safety Science | Clarify scope, align with GVP Module IX |
| **RENAME** | Safety Surveillance Director -> split function | Literature surveillance oversight stays with Signal Management; remove standalone "Surveillance Director" title |
| **CONSOLIDATE** | QPPV as overlay on Director, Signal Management | QPPV is a legal designation. Avoid creating a standalone role with no operational function. |
| **ADD TO DASHBOARD** | Director, Risk Management & Epidemiology | Already in API; missing from dashboard |
| **ADD TO DASHBOARD** | Associate Director, Aggregate Reporting | Already in API; missing from dashboard |
| **ADD TO DASHBOARD** | Manager, PV Quality & Compliance | Already in API; missing from dashboard |
| **DO NOT ADD** | Standalone Medical Information role | Not needed at this stage. Medical information queries can be handled by Medical Affairs with PV triage for AE reports. |

---

## 6. Summary of Priorities

| Priority | Action | Timeline | Cost Impact |
|---|---|---|---|
| P1 (Critical) | Hire Safety Physician for internal medical review | Immediate (0-3 months) | +1 FTE (offset by -1 outsourced) |
| P1 (Critical) | Reconcile dashboard org chart with API roles | Immediate | None (configuration) |
| P2 (High) | Establish CRO oversight KPI framework | 0-6 months | None (process) |
| P2 (High) | Formalize signal triage process per GVP Module IX | 0-6 months | None (SOP) |
| P3 (Medium) | Add ICSR medical review step to processing workflow | 0-3 months (after Safety Physician hire) | None (process) |
| P3 (Medium) | Establish PSMF and assign ownership | 0-6 months | None (document) |
| P4 (Low) | Title standardization across dashboard and API | 3-6 months | None (configuration) |
| P4 (Low) | SAE reconciliation SOP and schedule | 3-6 months | None (SOP) |
