# Clinical Informaticist Review: Cell Therapy Safety Platform Dashboard

**Reviewer**: Dr. Priya Chakraborty, MD, MS-CI
**Role**: Clinical Informaticist / CMIO, Comprehensive Cancer Center
**Background**: Hematology-Oncology, Clinical Informatics; led EHR integration projects for cell therapy monitoring at three institutions
**Date**: 2026-02-07
**Artifact Version**: Iteration 2
**Files Reviewed**:
- `src/api/static/index.html` (Clinical Dashboard UI)
- `src/api/static/demo_cases.js` (Demo Patient Cases)
- `src/api/app.py` (FastAPI Prediction Server)
- `src/api/schemas.py` (Pydantic Request/Response Schemas)

---

## Executive Summary

This platform demonstrates strong clinical domain knowledge and a thoughtful approach to cell therapy adverse event monitoring. The scoring models are grounded in published literature, the tab-based workflow covers the major phases of CAR-T monitoring, and the demo cases are clinically realistic. However, from a clinical informatics perspective, the system has significant gaps in data integrity transparency, standards compliance fidelity, alert management, interoperability readiness, and audit trail capabilities that would need to be addressed before clinical deployment or regulatory review. This review catalogs these findings in detail.

**Overall Assessment**: Promising research prototype with excellent clinical content. Not ready for clinical validation review or EHR integration in its current form. Estimated effort to reach pilot readiness: 3-4 months of focused engineering and clinical validation work.

---

## 1. Data Integrity and Model Transparency

### 1.1 Scoring Model Citations

**Strengths:**
- Each scoring model carries a `citation` field in the `ScoringResult` dataclass, and citations are rendered in the UI on individual score cards (e.g., "Fardet et al. Arthritis Rheumatol 2014;66(9):2613-2620" for HScore).
- The `/api/v1/models/status` endpoint exposes a `references` list per model with full bibliographic citations.
- The `biomarker_scores.py` module header explicitly lists all seven models with their source publications.

**Deficiencies:**
- **No DOIs or PubMed IDs.** Citations are author-year format only. A clinician wanting to verify the formula cannot click through to the paper. This is a missed opportunity for transparency and a requirement for any serious CDS tool.
- **No formula display.** The EASIX formula (LDH x Creatinine / Platelets) is mentioned only in the API description string, not in the dashboard itself. A clinician should be able to see the exact formula being applied. The HScore component breakdown table partially addresses this for HScore, but the EASIX and Modified EASIX score cards show only a number with no derivation.
- **No version pinning of reference formulas.** If Pennisi et al. publish an updated EASIX formula, there is no mechanism to track which version of the formula the system implements. The `version: "1.0.0"` field on `ModelInfo` is a software version, not a formula provenance version.

### 1.2 Confidence and Uncertainty Communication

**Strengths:**
- The `ScoringResult` dataclass includes a `confidence` field (0.0-1.0), and this value is used in the composite scoring weighted average.
- The composite index is explicitly labeled "weighted score, not a probability" in the UI -- an important disclaimer.

**Critical Deficiencies:**
- **Confidence is never displayed to the clinician.** The `confidence` field exists in the API response but is completely absent from the dashboard UI. A clinician sees a composite score and individual model scores but has no indication of how confident the system is in those scores. This is a patient safety concern.
- **No confidence intervals or uncertainty bands.** The composite risk meter shows a single point indicator on a gradient bar. There is no visual representation of uncertainty. A clinician cannot distinguish between a high-confidence moderate-risk score and a low-confidence moderate-risk score.
- **The `data_completeness` field (ratio of models run to total models) is computed in `app.py` (lines 506-513) but never displayed on the dashboard.** This metric directly indicates how much data the system had to work with. A completeness of 0.3 (only 2 of 7 models ran) should look very different from 1.0. Currently, both render identically.

### 1.3 Composite Score Methodology

**Concern: Automation Bias Risk.**
- The composite score uses a confidence-weighted average of normalized individual scores (`_compute_composite_score`, lines 360-385 of `app.py`). The normalization functions (`_normalise_score`, lines 388-411) use arbitrary, undocumented transforms:
  - EASIX: `log1p(score) / log1p(50)` -- Why 50? This ceiling is not derived from any published reference.
  - HScore: `score / 337` -- Correct denominator (337 is max HScore), but linear normalization of a non-linear score loses clinical meaning.
  - CAR-HEMATOTOX: `score / 10` -- Correct range.
  - Teachey: treated as already 0-1. Hay: 0 or 1 binary.
- **The mixing of fundamentally different score types into a single composite index is methodologically questionable.** EASIX is a ratio of lab values; HScore is a weighted clinical scoring system; Teachey is a logistic regression probability. Combining them via confidence-weighted averaging is not validated in any published literature.
- **This composite score is the dominant visual element on the dashboard (large risk meter, bold text).** Clinicians will anchor on it. If the methodology is not validated, this creates substantial automation bias risk -- a clinician may defer to the composite score rather than reviewing individual model outputs.

**Recommendation:** Either (a) validate the composite methodology in a clinical study before deployment, (b) remove the composite score and present only individual validated scores, or (c) clearly label the composite as "experimental/unvalidated" with prominent disclaimers in the UI, not just fine print.

### 1.4 Missing Data Transparency

- When a model is skipped due to missing inputs, the dashboard renders a dashed-border card with "Not Evaluated" and "Missing required inputs" (lines 983-989 of `index.html`). This is acceptable but insufficient.
- **The card does not specify which inputs are missing.** The `models_skipped` list from the `LayerDetail` gives only model names, not the reason for skipping. A clinician cannot determine which lab to order to enable the model.
- **The skipped model cards use `opacity: 0.5` and dashed borders.** In a glance-based workflow (which is how bedside clinicians actually use dashboards), these could easily be overlooked. A "Not Evaluated" state should be more visually distinct -- potentially with a specific color (e.g., gray) and an action prompt ("Order [lab] to enable this score").

---

## 2. Standards Compliance

### 2.1 CRS Grading (ASTCT Lee 2019)

**Strengths:**
- The CRS grading criteria displayed in the `CRS_GRADES` constant (lines 541-547 of `index.html`) correctly follow the ASTCT 2019 consensus structure:
  - Grade 1: Fever only, no hypotension, no hypoxia.
  - Grade 2: Fever + hypotension not requiring vasopressors, and/or hypoxia requiring low-flow O2.
  - Grade 3: Fever + hypotension requiring a vasopressor, and/or hypoxia requiring high-flow O2.
  - Grade 4: Fever + hypotension requiring multiple vasopressors, and/or hypoxia requiring positive pressure.
- The CRS management algorithm in `renderCRS()` appropriately maps grades to interventions.

**Deficiencies:**
- **Grade 5 (death) is missing.** The ASTCT consensus includes Grade 5. While omitting it from an interactive selector is understandable (a dead patient is not being assessed), it should be present in the grading reference table for completeness and documentation purposes.
- **The grading criteria text is slightly imprecise.** The ASTCT 2019 definition for Grade 2 specifies "hypotension not requiring vasopressors AND/OR hypoxia requiring low-flow nasal cannula" with specific thresholds. The dashboard abbreviates "low-flow O2" without specifying the threshold (<=6L/min by nasal cannula). Similarly, Grade 3 does not specify that "high-flow" means >6L/min nasal cannula, face mask, non-rebreather, or Venturi mask. These thresholds matter for accurate grading at the bedside.
- **CRS grading is manual (click-to-select) rather than algorithmically derived from the vital signs already in the system.** The dashboard has temperature, blood pressure, SpO2, and oxygen requirement data in the demo cases. It could auto-suggest a CRS grade based on these inputs, with clinician override. Currently, the vital signs and CRS grade are disconnected -- the system shows vital signs and separately asks the clinician to click a CRS grade, creating an opportunity for inconsistency.
- **No CRS grading validation.** If a clinician clicks "Grade 3" but the vitals show SBP 120 and SpO2 98%, the system accepts this without question. A CDS system should flag discrepancies between entered CRS grade and objective vital sign data.

### 2.2 ICANS Grading (ASTCT Consensus)

**Strengths:**
- The ICE score calculator (lines 1366-1411) correctly implements all five components: Orientation (4 pts), Naming (3 pts), Following Commands (1 pt), Writing (1 pt), Attention (1 pt) = 10 total.
- The ICANS grading table (lines 1419-1427) correctly maps ICE scores to ICANS grades and includes consciousness level, seizure, motor, and cerebral edema criteria.

**Deficiencies:**
- **The ICE score calculator does not account for patients who are unarousable.** Per ASTCT consensus, if the patient cannot be assessed (unarousable), ICE = 0 and the grade depends on the level of consciousness. The current calculator assumes the clinician can assess all five domains.
- **The ICANS grading table conflates two different grading axes.** ICANS Grade 3 can be assigned based on ICE 0-2 OR clinical seizure OR focal edema on imaging. The current table presents these as column headers but does not implement multi-axis grading logic. The ICE calculator only considers the ICE score, not seizure or imaging findings.
- **No link between CRS and ICANS tabs.** ICANS frequently co-occurs with CRS (as demonstrated in demo case DEMO-002). The ICANS tab does not display the current CRS grade, and the CRS tab does not flag neurological symptoms. A unified view would better support clinical workflow.

### 2.3 HScore (Fardet 2014)

**Strengths:**
- The HScore implementation includes component-level breakdown with individual point contributions visible in the UI.
- The 169-point threshold for >93% HLH probability is correctly cited and used for risk stratification.
- The maximum score of 337 is correctly referenced.

**Deficiency:**
- **The HLH probability estimate is referenced in the UI** (`hscoreResult.metadata?.hlh_probability_estimate`) **but it is unclear whether this is derived from the original Fardet 2014 probability curve or is a simple threshold-based estimate.** The original paper provides a continuous probability function, not just a threshold. If this is an interpolation, the methodology should be documented. If it is a lookup table, the table should be cited.

### 2.4 CRS vs. IEC-HS Differentiation Table

The HLH screening tab includes a differential diagnosis table (lines 1513-1523) comparing CRS and IEC-HS features. This is clinically valuable. However:
- **The ferritin threshold listed for IEC-HS (>10,000) is correct per recent consensus, but the fibrinogen threshold is listed as "<150 mg/dL or <1.5 g/L."** These are equivalent (1.5 g/L = 150 mg/dL), so listing both is fine for unit clarity, but the alert threshold in the code only checks `< 1.5` (g/L, line 2007 of `index.html`), which is correct.
- **The table references "265 mg/dL or >3.0 mmol/L" for triglycerides.** The code alert checks against `> 10000` for ferritin and `< 1.5` for fibrinogen (lines 2004-2009) but has no triglycerides alert threshold. This is a gap -- elevated triglycerides (>3.0 mmol/L) is a diagnostic criterion for HLH that should trigger an alert.

---

## 3. Alert Fatigue

### 3.1 Alert Volume Analysis

The `generateAlerts()` function (lines 1989-2033 of `index.html`) can fire the following alerts simultaneously:
1. HIGH RISK (composite score high)
2. High Fever (temp >= 38.9) OR Fever (temp >= 38.0)
3. HLH Warning (ferritin > 10,000)
4. Low Fibrinogen (< 1.5 g/L)
5. Severe Thrombocytopenia (platelets < 20)
6. Severe Neutropenia (ANC < 0.5)
7. Hypotension (SBP < 90)
8. Tachycardia (HR > 120)
9. Hypoxia (SpO2 < 94%)
10. Tachypnea (RR > 24)
11. ALT > 5x ULN

**In a severely ill patient (e.g., demo case DEMO-002 day 3, or DEMO-004 day 5), up to 8-9 of these can fire simultaneously.** This is a significant alert fatigue risk.

### 3.2 Alert Prioritization

**Current state:** Alerts are either `danger` (red) or `warning` (yellow). There is no tiered prioritization beyond these two visual categories. All danger alerts have equal visual weight.

**Deficiency:**
- No alert prioritization hierarchy. In a critically ill patient, a "High Fever" alert and a "Severe Thrombocytopenia" alert carry equal visual prominence, but clinically the immediate threat level may differ substantially.
- No distinction between actionable alerts (e.g., "consider platelet transfusion") and informational alerts (e.g., "CRS Grade >= 1 criteria met").
- No grouping of related alerts. Hypotension + Tachycardia + High Fever are all manifestations of the same CRS episode but appear as three separate alerts.

### 3.3 Alert Acknowledgment and Suppression

**Critical Gap:** There is no alert acknowledgment mechanism. Alerts cannot be:
- Dismissed or acknowledged
- Suppressed for known conditions (e.g., "patient is on vasopressors, hypotension is being managed")
- Snoozed for a time period
- Escalated after a period without acknowledgment

**Clinical Impact:** A nurse on a 12-hour shift viewing this dashboard for a Grade 3 CRS patient in the ICU would see the same 8-9 alerts every time they load the page. There is no way to indicate "I have seen and addressed this." This is a recipe for alert fatigue and banner blindness -- the exact opposite of what a safety system should produce.

### 3.4 Recommendations for Alert Management

- Implement a 3-tier severity system: Critical (immediate action required), Warning (monitor closely), Advisory (informational).
- Group related alerts into a single composite alert (e.g., "CRS Grade 3 indicators: hypotension, tachycardia, fever" as one alert rather than three).
- Add alert acknowledgment with timestamp and clinician ID.
- Implement "smart suppression" -- if an alert has been acknowledged and the condition has not worsened, do not re-fire on the next page load.
- Add configurable alert thresholds per institution (e.g., some centers use platelet transfusion threshold of <10, not <20).

---

## 4. Data Completeness Handling

### 4.1 "Not Evaluated" Communication

**Current behavior:** When a model cannot run due to missing inputs, the UI shows a dashed card with "Not Evaluated" and "Missing required inputs" (lines 983-989). The card has `opacity: 0.5`.

**Problems:**
- **"Not Evaluated" is ambiguous.** It could mean: (a) the model was not run because data was missing, (b) the model was run and returned no result, or (c) the risk for this condition is unknown. A clinician could interpret "Not Evaluated" as "no concern" (i.e., absence of evidence treated as evidence of absence). This is particularly dangerous for models like HScore -- if HScore shows "Not Evaluated" because fibrinogen was not ordered, a clinician might not pursue HLH workup.
- **The system does not distinguish between "data not available" and "data not yet ordered."** These have different clinical implications. If ferritin was not ordered, the clinician should order it. If ferritin was ordered but results are pending, the clinician should wait. The current system cannot represent this distinction.

**Recommendation:** Replace "Not Evaluated" with more specific language:
- "Cannot compute -- missing: [ferritin, fibrinogen, triglycerides]" with a "What to order" link.
- Use a distinct visual treatment (e.g., gray background with a question mark icon) rather than just reduced opacity.
- Consider adding a "Data Completeness" indicator prominently in the Overview, showing percentage of models computable and which labs would enable additional models.

### 4.2 Missing Labs in Input Forms

- The Clinical Visit tab (`renderClinicalVisit()`) provides input fields for all labs defined in `NORMAL_RANGES`, but several labs required by scoring models are missing from the form:
  - `triglycerides` is in `NORMAL_RANGES` but `il6`, `d_dimer`, `total_bilirubin`, `albumin` are included in demo cases but absent from `NORMAL_RANGES` and therefore absent from the manual entry form. A clinician entering data manually cannot provide IL-6, which is clinically important for CRS assessment.
  - Cytokine inputs required by the Teachey model (`ifn_gamma`, `sgp130`, `il1ra`) are not represented in the manual entry form at all, effectively making the Teachey model impossible to use through the UI.
- The `LabValues` Pydantic schema (lines 23-60 of `schemas.py`) does not include `sgp130` or `il1ra`, which are required by the Teachey Cytokine 3-variable model. The `/api/v1/models/status` endpoint lists `sgp130_ng_ml` and `il1ra_pg_ml` as required inputs for Teachey, but these fields do not exist in the request schema. This means the Teachey model can never run through the standard API -- it is structurally unreachable.

---

## 5. Interoperability Considerations

### 5.1 FHIR R4 Compatibility

**Current State:** The API uses a custom Pydantic schema (`PatientDataRequest`) with custom field names. There is no FHIR awareness in the current implementation.

**Assessment:**
- The data model is not FHIR-compatible. A FHIR R4 integration would require mapping:
  - `PatientDataRequest` fields to `Observation` resources (for labs and vitals)
  - `patient_id` to a FHIR `Patient` resource reference
  - Scoring results to `RiskAssessment` resources
  - Alerts to `Flag` or `CommunicationRequest` resources
- The flat key-value structure of `patient_data` dict (e.g., `ldh_u_per_l`, `temperature_c`) would need to be mapped to LOINC codes for each observation.
- The API currently accepts and returns custom JSON, not FHIR bundles. An integration layer would be needed.

**Positive:** The `_LAB_KEY_MAP`, `_VITAL_KEY_MAP`, and `_CLINICAL_KEY_MAP` dictionaries in `app.py` (lines 222-264) provide a structured mapping layer that could serve as the foundation for a FHIR terminology mapping. The explicit unit annotations in field names (e.g., `_u_per_l`, `_mg_dl`, `_g_l`) also facilitate mapping.

### 5.2 LOINC and SNOMED CT Mapping

**Current State:** No standard terminology codes are used anywhere in the system. Lab values are identified by custom string keys (e.g., `ldh_u_per_l`, `ferritin_ng_ml`).

**What would be needed for EHR integration:**

| System Field | LOINC Code | LOINC Name |
|---|---|---|
| `ldh_u_per_l` | 2532-0 | Lactate dehydrogenase [Enzymatic activity/volume] |
| `creatinine_mg_dl` | 2160-0 | Creatinine [Mass/volume] in Serum or Plasma |
| `platelets_per_nl` | 777-3 | Platelets [#/volume] in Blood |
| `crp_mg_l` | 1988-5 | C reactive protein [Mass/volume] in Serum or Plasma |
| `ferritin_ng_ml` | 2276-4 | Ferritin [Mass/volume] in Serum or Plasma |
| `anc_10e9_per_l` | 751-8 | Neutrophils [#/volume] in Blood |
| `hemoglobin_g_dl` | 718-7 | Hemoglobin [Mass/volume] in Blood |
| `ast_u_per_l` | 1920-8 | Aspartate aminotransferase [Enzymatic activity/volume] |
| `fibrinogen_g_l` | 3255-7 | Fibrinogen [Mass/volume] in Platelet poor plasma |
| `triglycerides_mmol_l` | 2571-8 | Triglyceride [Mass/volume] in Serum or Plasma |
| `temperature_c` | 8310-5 | Body temperature |
| `il6_pg_ml` | 26881-3 | Interleukin 6 [Mass/volume] in Serum or Plasma |

This mapping does not exist in the codebase. Adding a LOINC mapping table would be the single most impactful step for interoperability.

### 5.3 Lab Unit Consistency

**Assessment:** The system uses standard US clinical lab reporting units for most values:
- LDH in U/L (standard)
- Creatinine in mg/dL (US standard; note that SI units use umol/L)
- Platelets in 10^9/L (standard)
- CRP in mg/L (standard; note some US labs report mg/dL)
- Ferritin in ng/mL (standard)
- Hemoglobin in g/dL (US standard)
- AST in U/L (standard)
- Fibrinogen in g/L (standard; note some US labs report mg/dL, where 1 g/L = 100 mg/dL)
- Triglycerides in mmol/L (SI standard; **US labs typically report mg/dL**, conversion: 1 mmol/L = 88.57 mg/dL)

**Critical Issue:** Triglycerides are in mmol/L, which is the SI convention. Most US clinical labs report triglycerides in mg/dL. A US clinician entering triglycerides from a standard US lab report would need to convert. The form does show the unit label (mmol/L), but this is a common source of data entry errors. The system should either accept both units with auto-conversion, or default to the units most commonly reported by the target institution's lab.

**CRP Unit Duality:** The code in `app.py` (lines 285-289) explicitly handles CRP unit conversion: `crp_mg_dl = crp_mg_l / 10.0`. This is correct, but the dual-unit situation is not documented in the UI. A clinician entering CRP needs to know the expected unit is mg/L.

---

## 6. Audit Trail and Documentation

### 6.1 Current Audit Capabilities

**What exists:**
- Each API response includes a `request_id` (UUID) and `timestamp` (lines 187-201 of `schemas.py`). This provides basic request traceability.
- The `RequestTimingMiddleware` adds `X-Request-ID` and `X-Process-Time` headers (line 193 of `app.py`).
- Server-side logging via Python's `logging` module captures prediction failures and WebSocket events.

**What is critically missing:**
- **No persistent audit log.** The system uses in-memory stores (`_patient_timelines`, `_model_last_run`, lines 85-86 of `app.py`). All data is lost on server restart. The comment "replace with database in production" (line 84) acknowledges this, but for a clinical safety system, this is not merely a production concern -- it is a fundamental architectural gap.
- **No user identity tracking.** There is no concept of "who viewed this patient's data" or "who ran this prediction." The `APIKeyMiddleware` exists but there is no user-level authentication. For HIPAA compliance and clinical audit requirements, every access must be attributable to a specific user.
- **No action logging.** When a clinician selects a CRS grade, checks a checklist item, or calculates an ICE score, these actions are stored only in `localStorage` (browser-side). They are not transmitted to the server. If the clinician clears their browser cache, all documentation of their assessments is lost.
- **No change tracking for lab values.** If a clinician enters data in the Clinical Visit form, there is no record of what was entered, when, or by whom. If the data is incorrect and later corrected, there is no audit trail of the change.
- **The CRS grade selection (stored in localStorage, line 1914-1916) is per-patient per-timepoint but is never transmitted to the server.** From a documentation perspective, the CRS grade a clinician assigns is a critical clinical determination. It should be recorded in the audit log.

### 6.2 Regulatory Considerations

For CDS tools that fall under FDA guidance ("Clinical Decision Support Software: Guidance for Industry," September 2022):
- The system should document its intended use population, intended user, and intended use environment.
- Risk assessments (especially the composite score) that could influence treatment decisions may fall under FDA oversight if they meet the four-criterion test for CDS.
- The lack of an audit trail would be a finding in any regulatory review.
- The disclaimer "For clinical decision support only -- not a substitute for clinical judgment" (line 507) is present but should be more prominent and should be part of every API response, not just the footer.

---

## 7. Workflow Integration

### 7.1 Tab Structure Analysis

The nine tabs are:
1. **Overview** -- Composite risk, individual scores, lab values, trends
2. **Pre-Infusion** -- Baseline risk assessment, checklist
3. **Day 1 Monitor** -- Hay classifier, day 1 checklist
4. **CRS Monitor** -- CRS grading, EASIX scores, management algorithm
5. **ICANS** -- ICE calculator, ICANS grading, management
6. **HLH Screen** -- HScore, CRS vs. IEC-HS differentiation
7. **Hematologic** -- CAR-HEMATOTOX, recovery monitoring
8. **Discharge** -- Discharge readiness, instructions
9. **Clinical Visit** -- Manual data entry

**Workflow Alignment Assessment:**

The tab structure broadly aligns with the clinical workflow phases of CAR-T therapy, which is a significant strength. However:

- **Temporal vs. syndrome-based organization is mixed.** Tabs 2-3 are temporal (Pre-Infusion, Day 1), while tabs 4-7 are syndrome-based (CRS, ICANS, HLH, Hematologic). This creates confusion: on Day 3 post-infusion, should the clinician use "Overview," "CRS Monitor," or "HLH Screen"? In practice, a clinician monitoring a patient with CRS on Day 3 would need to check CRS, potentially ICANS, and potentially HLH -- three separate tabs for one clinical encounter.
- **No "Active Monitoring" or "Daily Assessment" tab.** The most common clinical interaction with this system would be a daily assessment: "What is this patient's current status and what do I need to worry about?" This maps to Overview, but Overview is designed as a summary, not a guided assessment workflow. A structured "Daily Assessment" view that walks through vitals, labs, CRS grading, ICANS screen, and lab orders in sequence would reduce cognitive load and clicks.
- **Redundant content across tabs.** Lab values appear on Overview, Pre-Infusion, CRS Monitor, and Hematologic tabs. Score cards appear on Overview, Pre-Infusion, and CRS Monitor. This redundancy increases page weight and can cause confusion if the data updates differently across views (all views render from the same API response, so this is not currently a data consistency issue, but it is a cognitive load issue).

### 7.2 Click Burden Analysis

To perform a complete daily assessment for a patient who might have CRS, ICANS, and HLH risk:
1. Select patient (1 click)
2. Select timepoint (1 click)
3. View Overview (default tab -- 0 clicks)
4. Click CRS tab to check CRS grading (1 click, scroll through CRS content)
5. Click ICANS tab to calculate ICE score (1 click, interact with 5 dropdowns, click Calculate -- 7 interactions)
6. Click HLH tab to review HScore (1 click, scroll)
7. Click Hematologic tab to check CAR-HEMATOTOX (1 click, scroll)
8. Return to Overview (1 click)

**Total: minimum 14 interactions for a complete assessment.** This is acceptable for an initial assessment but is excessive for a q4h nursing check (which realistically needs 2-3 clicks: patient -> status -> done). A consolidated "Quick Status" view showing all active concerns in a single pane would significantly improve workflow efficiency.

### 7.3 Cognitive Load

**Current cognitive load per task is moderate to high:**
- Overview tab presents the composite risk meter, individual score cards (up to 7), lab values table, trend charts, and teaching points -- all on a single scrollable page. This is information-dense and appropriate for a physician making treatment decisions.
- For a bedside nurse doing a q4h check, the information density is excessive. The nurse needs: (a) current risk level, (b) any new alerts, (c) trending direction. This should be achievable in a single glance without scrolling.

**Recommendation:** Implement role-based views:
- **Physician view:** Current Overview tab with full detail.
- **Nursing view:** Simplified status card showing risk level, active alerts, trending direction, and due orders. One screen, no scrolling.
- **Pharmacist view:** Focus on intervention thresholds (tocilizumab dosing, steroid regimen, G-CSF).

---

## 8. Additional Findings

### 8.1 Demo Case Quality

The eight demo cases in `demo_cases.js` are clinically excellent. They cover:
- Low-risk CRS (DEMO-001)
- Severe CRS with tocilizumab (DEMO-002)
- Moderate CRS in myeloma / anti-BCMA CAR-T (DEMO-003)
- IEC-HS / HLH transition (DEMO-004)
- Isolated ICANS without CRS (DEMO-005)
- Late-onset CRS with cilta-cel (DEMO-006)
- Prolonged cytopenias (DEMO-007)

Each case has realistic lab trajectories, appropriate clinical notes, and valuable teaching points. The inclusion of product-specific differences (axi-cel vs. tisa-cel vs. liso-cel vs. ide-cel vs. cilta-cel) demonstrates strong domain knowledge. These cases could serve as an excellent educational tool independent of the scoring platform.

**One concern:** The `scores` object in each timepoint contains pre-computed reference values that may not match the API's calculations (as noted in the file header). These should either be removed (to avoid confusion) or validated against the API output. Discrepancies between pre-computed and API-computed scores would undermine trust in the system.

### 8.2 Security Concerns

- **CORS allows all origins** (`allow_origins=["*"]`, line 179 of `app.py`). For a clinical system handling PHI, this is unacceptable. CORS should be restricted to known origins.
- **API key middleware exists** (`APIKeyMiddleware`, line 191) but the implementation is not visible in the reviewed files. If API keys are hardcoded or transmitted in query parameters, this is a security risk.
- **Patient data is stored in memory** with no encryption at rest or access controls. The in-memory `_patient_timelines` dict is accessible to any API consumer with a valid API key.
- **WebSocket connections have no authentication** beyond the initial HTTP upgrade. Any client can subscribe to patient monitoring for any `patient_id`.

### 8.3 Print Functionality

The print CSS (lines 341-357 of `index.html`) hides the header, sidebar, and navigation, leaving only the content area. The print header includes patient name, ID, age/sex, timepoint, and print timestamp. This is a reasonable start, but:
- No "Printed by" field (should include clinician name for documentation).
- No institution name or medical record number field.
- No disclaimer/footer on printed output about CDS tool limitations.
- No page numbering for multi-page printouts.

### 8.4 Teachey and Hay Model Structural Gaps

- **Teachey Cytokine 3-variable model** requires `ifn_gamma_pg_ml`, `sgp130_ng_ml`, and `il1ra_pg_ml`. Of these, `sgp130_ng_ml` and `il1ra_pg_ml` are not in the `LabValues` Pydantic schema. The model is listed as "available" in `/api/v1/models/status` but is structurally unreachable through the API. This is a dead code path that inflates the "models available" count.
- **Hay Binary Classifier** requires `temperature_c` and `mcp1_pg_ml`. MCP-1 is in the `LabValues` schema but not in the `NORMAL_RANGES` constant, so it does not appear in the manual entry form as a flagged field. This makes it harder for clinicians to use.

---

## 9. Prioritized Recommendations

### Critical (Must fix before any clinical use)

| # | Finding | Recommendation |
|---|---------|----------------|
| C1 | No audit trail | Implement persistent, append-only audit logging for all predictions, assessments, and user actions |
| C2 | No user authentication | Add user-level auth (not just API keys) with role-based access |
| C3 | Composite score not validated | Either validate in clinical study, remove, or prominently label as experimental |
| C4 | No alert acknowledgment | Implement alert acknowledgment, suppression, and escalation |
| C5 | CORS unrestricted | Restrict CORS to known origins |
| C6 | Confidence not displayed | Show model confidence and data completeness prominently in UI |

### High Priority (Address before pilot deployment)

| # | Finding | Recommendation |
|---|---------|----------------|
| H1 | No LOINC/SNOMED mapping | Create terminology mapping table for all lab values |
| H2 | Triglycerides in SI units | Support both mmol/L and mg/dL with auto-conversion |
| H3 | CRS grade not auto-suggested | Algorithmically derive CRS grade from vital signs with clinician override |
| H4 | Teachey model unreachable | Either add sgp130/il1ra to schema or remove model from "available" count |
| H5 | "Not Evaluated" ambiguity | Specify which inputs are missing and suggest orders |
| H6 | No Grade 5 CRS | Add Grade 5 (death) to CRS grading reference |
| H7 | No triglycerides alert | Add HLH alert for triglycerides >3.0 mmol/L |

### Medium Priority (Enhance for production readiness)

| # | Finding | Recommendation |
|---|---------|----------------|
| M1 | Tab structure mixed temporal/syndrome | Add consolidated "Daily Assessment" workflow tab |
| M2 | High click burden | Create "Quick Status" single-pane view for nursing workflow |
| M3 | No formula display | Show scoring formulas on each score card |
| M4 | No DOIs/PMIDs | Add DOIs to all citations for one-click verification |
| M5 | Pre-computed scores in demo data | Validate or remove pre-computed `scores` objects |
| M6 | No FHIR resource mapping | Design FHIR R4 resource mapping for future EHR integration |
| M7 | Checklist state in localStorage only | Persist checklist completions server-side with audit |

---

## 10. Conclusion

This platform demonstrates impressive clinical depth in cell therapy adverse event monitoring. The scoring models are well-chosen, properly cited, and the demo cases serve as excellent clinical teaching tools. The tab-based workflow covers the appropriate clinical phases, and the visual design is clean and functional.

However, the system has significant gaps that would prevent it from passing a clinical validation review in its current state. The most critical issues are: (1) the lack of an audit trail, which is non-negotiable for any clinical tool; (2) the unvalidated composite score that dominates the UI and creates automation bias risk; (3) the absence of alert management features that would prevent alert fatigue in real clinical use; and (4) the lack of interoperability features (LOINC codes, FHIR mapping) needed for EHR integration.

The path from research prototype to clinical pilot is achievable but requires deliberate engineering investment in infrastructure (audit logging, authentication, persistence), standards compliance (LOINC mapping, precise grading criteria), and workflow optimization (role-based views, alert management, consolidated assessment views).

---

*Reviewed by Dr. Priya Chakraborty, MD, MS-CI -- Clinical Informaticist*
*This review is based on static code analysis of the files listed above. No live system testing was performed.*
