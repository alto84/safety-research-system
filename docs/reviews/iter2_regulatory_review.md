# Regulatory Affairs & Quality Assurance Review: Cell Therapy Safety Platform

**Reviewer:** Thomas Eriksson, MPH, RAC
**Role:** Regulatory Affairs and Quality Assurance Specialist, Cell and Gene Therapy
**Date:** 2026-02-07
**Software Version Reviewed:** 0.1.0
**Review Type:** Comprehensive Regulatory, Safety, and Quality Assessment (Iteration 2)

---

## Executive Summary

This review evaluates the Cell Therapy Safety Platform -- a clinical decision support tool providing deterministic biomarker scoring (EASIX, Modified EASIX, Pre-Modified EASIX, HScore, CAR-HEMATOTOX, Teachey Cytokine Model, Hay Binary Classifier) and ensemble risk stratification for CRS, ICANS, and HLH adverse events in patients receiving CAR-T cell therapy. The review assesses REMS compliance readiness, safety signal detection, model validation, regulatory classification risk, data governance, version control, risk management, and quality metrics.

**Overall Assessment: NOT READY FOR CLINICAL USE.** The platform demonstrates strong clinical domain knowledge and technically sound algorithm implementations, but has critical gaps that must be resolved before any clinical deployment, even as a non-regulated decision support tool. The most urgent findings involve (1) an absent or inadequate SaMD/CDS disclaimer, (2) no REMS-specific reporting integration, (3) no audit trail or electronic signature capability, (4) CORS configured to allow all origins, and (5) in-memory data stores with no persistence or backup.

**Risk Rating: HIGH** -- The tool presents patient safety risks if deployed without the mitigations identified in this review.

---

## 1. REMS Compliance Assessment

### 1.1 CAR-T REMS Program Coverage

All six FDA-approved CAR-T products with active REMS programs should be supported. The dashboard's Clinical Visit view (`renderClinicalVisit()` in `index.html`) includes a product selector with five products:

| Product (Brand) | Generic Name | Listed in UI? | REMS Elements |
|---|---|---|---|
| Yescarta | Axicabtagene ciloleucel | YES | Certification, safe use conditions |
| Kymriah | Tisagenlecleucel | YES (as "Tisagenlecleucel") | Certification, safe use conditions |
| Tecartus | Brexucabtagene autoleucel | **NO -- MISSING** | Certification, safe use conditions |
| Breyanzi | Lisocabtagene maraleucel | YES | Certification, safe use conditions |
| Abecma | Idecabtagene vicleucel | YES | Certification, safe use conditions |
| Carvykti | Ciltacabtagene autoleucel | YES | Certification, safe use conditions |

**Finding REG-01 (MAJOR):** Tecartus (brexucabtagene autoleucel) is missing from the product selector. All FDA-approved CAR-T products must be available for selection to ensure accurate REMS reporting. This is not an academic omission -- Tecartus is approved for relapsed/refractory mantle cell lymphoma and ALL and has distinct CRS/ICANS profiles.

### 1.2 REMS Data Element Capture

REMS programs for CAR-T products require certified healthcare facilities to report specific data elements. Assessment of required vs. captured fields:

| REMS Required Element | Captured? | Location | Notes |
|---|---|---|---|
| Patient demographics | Partial | `Demographics` schema | Age, weight, BSA only. Missing: sex/gender, race/ethnicity |
| Product identification | YES | `ProductInfo` schema | Product name, dose |
| Infusion date/time | Partial | `hours_since_infusion` | Relative timing only; no absolute date/time |
| CRS occurrence and grade | Partial | UI only | CRS grade selector in dashboard, but NOT captured in API schema or persisted |
| CRS onset date | **NO** | -- | Not in any schema |
| CRS resolution date | **NO** | -- | Not in any schema |
| ICANS occurrence and grade | Partial | UI only | ICE calculator in dashboard, not persisted |
| ICANS onset/resolution dates | **NO** | -- | Not in any schema |
| Tocilizumab use | **NO** | -- | Not tracked |
| Corticosteroid use | **NO** | -- | Not tracked |
| ICU admission | **NO** | -- | Not tracked |
| Death and cause | **NO** | -- | Not tracked |
| Hospitalization duration | **NO** | -- | Not tracked |
| Retreatment information | **NO** | -- | Not tracked |

**Finding REG-02 (CRITICAL):** The platform captures fewer than half the required REMS reporting elements. CRS and ICANS grading are available as UI interactions (CRS grade selector, ICE score calculator) but the selections are stored only in browser `localStorage` -- they are not transmitted to the API, not persisted in any database, and would not survive a browser cache clear. There is no mechanism to generate or export a REMS report.

**Finding REG-03 (MAJOR):** CRS and ICANS grading events must include onset date, peak grade, resolution date, and interventions administered (tocilizumab, corticosteroids, vasopressors, supplemental oxygen). None of these are captured in the `PatientDataRequest` or `PredictionResponse` schemas.

### 1.3 CRS/ICANS Grading Scale Compliance

**CRS Grading:**
The dashboard implements the ASTCT (American Society for Transplantation and Cellular Therapy) consensus grading system (Lee et al. BBMT 2019), which is the FDA-mandated grading scale for REMS reporting. The criteria definitions in `CRS_GRADES` (lines 541-547 of `index.html`) are accurate:
- Grade 1: Fever >= 38.0C, no hypotension, no hypoxia
- Grade 2: Fever + hypotension not requiring vasopressors and/or low-flow O2
- Grade 3: Fever + vasopressor-requiring hypotension and/or high-flow O2
- Grade 4: Fever + multiple vasopressors and/or positive pressure ventilation

**Assessment: COMPLIANT** with the grading scale definitions. However, the CRS grade is user-selected and not algorithmically verified against the vital signs data already in the system. The tool presents hypotension (SBP < 90) and hypoxia (SpO2 < 94%) alerts but does not cross-reference these with the manually selected CRS grade for consistency.

**ICANS Grading:**
The ICE (Immune Effector Cell-Associated Encephalopathy) score calculator correctly implements the 10-point scale with the five domains (Orientation, Naming, Following Commands, Writing, Attention). The ICANS grade mapping (ICE 7-9 = Grade 1, 3-6 = Grade 2, 0-2 = Grade 3, 0 with obtundation = Grade 4) is consistent with ASTCT consensus.

**Assessment: COMPLIANT** with the grading scale. However, Grade 3-4 ICANS grading depends on consciousness level, seizure activity, motor findings, and cerebral edema -- factors displayed in the reference table but not integrated into the calculator logic.

**Finding REG-04 (MODERATE):** The ICE calculator does not account for level of consciousness, seizure status, or cerebral edema in computing the ICANS grade. A patient with an ICE of 3 who is obtunded should be graded as ICANS Grade 4, not Grade 2. This is displayed in the reference table but the calculator would return the wrong grade.

---

## 2. Safety Signal Detection

### 2.1 Adverse Event Alerting

The dashboard generates safety alerts through the `generateAlerts()` function (lines 1989-2034 of `index.html`). The following alert conditions are implemented:

| Condition | Threshold | Alert Level | Clinical Relevance |
|---|---|---|---|
| High composite risk | `risk_level === 'high'` | DANGER | Ensemble-level escalation trigger |
| High fever | >= 38.9C | DANGER | Hay classifier trigger |
| Fever | >= 38.0C | WARNING | CRS Grade >= 1 |
| Ferritin > 10,000 | > 10,000 ng/mL | DANGER | HLH/IEC-HS |
| Fibrinogen < 1.5 | < 1.5 g/L | DANGER | Consumptive coagulopathy |
| Platelets < 20 | < 20 x10^9/L | DANGER | Bleeding risk |
| ANC < 0.5 | < 0.5 x10^9/L | WARNING | Severe neutropenia |
| Hypotension | SBP < 90 | DANGER | CRS Grade >= 2 |
| Tachycardia | HR > 120 | WARNING | Hemodynamic instability |
| Hypoxia | SpO2 < 94% | DANGER | CRS Grade >= 2 |
| Tachypnea | RR > 24 | WARNING | Respiratory decompensation |
| ALT > 5x ULN | > 165 U/L | WARNING | Hepatotoxicity |

**Assessment: ADEQUATE for basic safety signal detection.** The alert thresholds are clinically reasonable and aligned with published management algorithms.

### 2.2 Gaps in Safety Signal Detection

**Finding SAF-01 (CRITICAL):** There is no mechanism for reporting Serious Adverse Events (SAEs) or Suspected Unexpected Serious Adverse Reactions (SUSARs). In a clinical trial context, IND safety reporting requirements under 21 CFR 312.32 mandate reporting of fatal or life-threatening suspected adverse reactions within 7 calendar days, and all other SAEs within 15 calendar days. The platform has no:
- SAE classification capability (serious criteria: death, life-threatening, hospitalization, disability, congenital anomaly, other medically important event)
- SAE report form generation
- Expedited reporting timeline tracking
- MedDRA coding of adverse events
- Causality assessment fields

**Finding SAF-02 (MAJOR):** The following clinically significant conditions are NOT detected by the alert system:
- **Tumor lysis syndrome (TLS):** No alerts for hyperkalemia, hyperuricemia, hyperphosphatemia, or hypocalcemia. TLS can occur post-CAR-T.
- **Infection/sepsis:** Fever triggers CRS alerts but there is no mechanism to distinguish infection from CRS. Blood cultures are suggested but sepsis scoring (qSOFA, SOFA) is absent.
- **Coagulopathy/DIC:** Fibrinogen is checked but D-dimer, PT/INR, and aPTT are not part of the alert logic. DIC is a recognized CAR-T complication.
- **Cardiac toxicity:** Troponin, BNP/NT-proBNP are not captured. Cardiotoxicity from CRS-associated cytokine storm is a known risk.
- **Renal failure:** Creatinine is captured for EASIX but there is no alert for acute kidney injury (e.g., creatinine rise > 1.5x baseline or > 0.3 mg/dL increase within 48h per KDIGO).
- **Prolonged B-cell aplasia / hypogammaglobulinemia:** IgG levels are mentioned in outpatient monitoring but not tracked in the scoring engine.

**Finding SAF-03 (MAJOR):** Alert notifications are purely visual (rendered inline in the HTML). There is no:
- Audio/audible alert for critical findings
- Push notification capability
- Escalation pathway (e.g., auto-page the attending physician)
- Alert acknowledgment/documentation system
- Persistent alert log that survives page refresh

**Finding SAF-04 (MODERATE):** The ensemble runner uses a "max risk" aggregation strategy (highest risk level from any model = overall risk level). While conservative and generally appropriate for safety, this means a single model returning HIGH will override all others returning LOW. This is acceptable for clinical safety but should be documented, and the model agreement summary (e.g., "1 of 5 models: 1 HIGH, 4 LOW") should be more prominently displayed when discordance exists. The existing discordance warning in the ensemble runner (`ensemble_runner.py` line 253-264) is well-implemented.

---

## 3. Model Validation Assessment

### 3.1 Published Algorithm Fidelity

| Model | Published Formula | Implementation Correct? | Citation Accurate? | Thresholds Published? |
|---|---|---|---|---|
| EASIX | (LDH x Creatinine) / Platelets | YES | YES -- Pennisi 2021, Korell 2022 | Thresholds (3.2/10.0) appear to be derived from tertile analysis, not directly from the cited papers. |
| Modified EASIX | (LDH x CRP) / Platelets | YES | YES -- Same citations | Same threshold concern. |
| Pre-Modified EASIX | Same as m-EASIX (pre-LD) | YES | YES -- Korell 2022 | Same threshold concern. |
| HScore | 9-variable weighted score | YES -- all point values verified against Fardet 2014 | YES -- Fardet 2014, exact journal citation | YES -- 169 threshold directly from paper |
| CAR-HEMATOTOX | 5-variable point score | YES -- verified against Rejeski 2021 | YES -- Rejeski 2021, exact citation | YES -- >= 3 threshold from paper |
| Teachey Cytokine | 3-variable logistic regression | PARTIALLY -- see below | YES -- Teachey 2016 | Risk thresholds (0.20/0.50) are author-defined, not from paper |
| Hay Binary | Rule-based fever + MCP-1 | YES | YES -- Hay 2017 | YES -- 38.9C and 1343 pg/mL from paper |

**Finding VAL-01 (MAJOR):** The Teachey Cytokine Model coefficients are described as "approximate published coefficients" (`biomarker_scores.py` lines 1109-1114):
```
beta_0 = -8.5
beta_1 = 0.8 (IFN-gamma)
beta_2 = 1.2 (sgp130)
beta_3 = 0.6 (IL-1RA)
```
The word "approximate" is a red flag for a clinical tool. The original Teachey 2016 paper's supplementary materials should contain exact coefficients. If exact coefficients are not available (some papers do not publish them), this model should be clearly labeled as an approximation and its confidence should be reduced accordingly. **This would not pass a GCP audit** -- an auditor would ask for the exact published coefficients and proof of faithful implementation.

**Finding VAL-02 (MODERATE):** The EASIX risk stratification thresholds (Low < 3.2, High >= 10.0) are described as "derived from published tertile analyses" in the code comments, but neither Pennisi 2021 nor Korell 2022 appear to publish these exact cutpoints as clinically validated thresholds. The code documentation should clearly state whether these thresholds are (a) directly published, (b) derived by the development team from published distributions, or (c) expert consensus. This distinction matters for regulatory defensibility.

**Finding VAL-03 (MODERATE):** The HScore probability approximation uses a logistic function (`P = 1/(1+exp(-0.04*(HScore-168)))`) that is described as "fitted to the published data points." This is reasonable but the fit quality should be documented -- what were the data points used, what is the R-squared of the fit, and how does it compare to Fardet's published probability curve? In a clinical trial audit, the auditor would want to see this derivation.

**Finding VAL-04 (MODERATE):** The composite score normalization in `app.py` (lines 388-411) uses model-specific normalizations (e.g., `log1p(EASIX)/log1p(50)` for EASIX, `HScore/337` for HScore). These normalization functions are ad hoc -- they are not published or validated. The composite score is presented to clinicians as a percentage ("Composite index: 45.2"), which could be misinterpreted as a probability. The disclaimer "weighted score, not a probability" exists but is in 11px font and easily overlooked.

### 3.2 Clinical Trial Audit Readiness

**Would this pass scrutiny in a GCP audit?** NO, for the following reasons:

1. **No formal validation protocol.** There is no evidence of installation qualification (IQ), operational qualification (OQ), or performance qualification (PQ) testing.
2. **No test cases with known expected outputs.** The demo cases include pre-computed "expected" scores but there is no formal test harness comparing API outputs to published example calculations.
3. **The "approximate" Teachey coefficients** would be flagged immediately.
4. **No user acceptance testing documentation.**
5. **No validation of the composite scoring algorithm** against clinical outcomes.
6. **In-memory data storage** (`_patient_timelines` in `app.py`) means all data is lost on server restart -- there is no audit trail.

---

## 4. Disclaimer and Liability Assessment

### 4.1 Current Disclaimer Language

The platform includes one disclaimer at the bottom of the content area (`index.html` line 507):

> "Scores computed from published clinical formulas (EASIX, HScore, CAR-HEMATOTOX, Teachey, Hay). For clinical decision support only -- not a substitute for clinical judgment."

The API description (`app.py` line 113-117) includes:

> "Not a substitute for clinical judgment."

### 4.2 Disclaimer Deficiencies

**Finding DIS-01 (CRITICAL):** The disclaimer is grossly inadequate for a tool that could influence clinical decisions for patients receiving potentially lethal therapy. At minimum, the following must be prominently displayed:

1. **This software is NOT an FDA-cleared or approved medical device.** It has not been evaluated by the U.S. Food and Drug Administration or any other regulatory authority.
2. **This software is NOT intended to diagnose, treat, cure, or prevent any disease.**
3. **This software does NOT meet the definition of a Clinical Decision Support (CDS) tool that is exempt from FDA regulation** under Section 3060 of the 21st Century Cures Act (see criterion iv below).
4. **All clinical decisions must be made by qualified healthcare providers** who independently verify the data, apply their clinical judgment, and are solely responsible for patient care.
5. **The scoring algorithms are deterministic calculations based on published formulas.** The composite risk score is NOT a validated clinical prediction and should NOT be used as the sole basis for treatment decisions.
6. **The software has NOT been validated in a prospective clinical trial.**
7. **Version, build date, and algorithm version identifiers** should be displayed.

### 4.3 FDA SaMD Classification Risk

**Finding DIS-02 (CRITICAL):** This software presents significant FDA Software as a Medical Device (SaMD) risk. Analysis under the International Medical Device Regulators Forum (IMDRF) SaMD framework:

**Is this software a medical device?**

Under FDA guidance, software is a medical device if it is "intended for use in the diagnosis of disease or other conditions, or in the cure, mitigation, treatment, or prevention of disease" (Section 201(h) of the FD&C Act).

This platform:
- Calculates clinical risk scores from patient biomarker data
- Provides risk stratification (low/moderate/high) that could influence treatment decisions
- Generates clinical alerts (e.g., "HIGH RISK - Consider escalation")
- Provides management algorithm recommendations (tocilizumab dosing, steroid recommendations, ICU transfer)
- Includes anticipatory test ordering suggestions

**21st Century Cures Act CDS Exemption Analysis (Section 3060(a)):**

To qualify for the CDS exemption, ALL FOUR criteria must be met:
1. Not intended to acquire, process, or analyze a medical image or signal -- **MET**
2. Intended for the purpose of displaying, analyzing, or printing medical information -- **PARTIALLY MET**
3. Intended for the purpose of supporting or providing recommendations to a healthcare professional about prevention, diagnosis, or treatment -- **MET**
4. **Intended for the purpose of enabling a healthcare professional to independently review the basis for such recommendations so that it is not the intent that the professional rely primarily on the software** -- **NOT CLEARLY MET**

The fourth criterion is problematic because:
- The composite score is an opaque combination of normalized model outputs using ad hoc weights
- A clinician cannot independently verify the composite score without understanding log-transform normalizations and confidence-weighted averaging
- While individual model scores are shown, the composite "risk meter" with its visual traffic-light display encourages reliance on the summary rather than independent review

**IMDRF SaMD Risk Classification:**

| Factor | Assessment |
|---|---|
| State of Healthcare Situation | Critical -- CAR-T patients can rapidly deteriorate |
| Significance of Information | Treat or diagnose -- risk scores influence treatment decisions |
| IMDRF Risk Category | **Category III (High)** or **Category IV (Very High)** |

**Recommendation:** The current software likely falls under FDA regulation as a Class II medical device (SaMD) requiring 510(k) clearance or De Novo classification. The development team should either:
- (a) **Pursue FDA clearance** if clinical deployment is planned, or
- (b) **Restructure the tool** to clearly meet all four CDS exemption criteria by removing prescriptive recommendations, making all algorithm steps transparently visible, and ensuring the tool is presented as informational only.

---

## 5. Data Governance Assessment

### 5.1 PHI Exposure

**Finding DAT-01 (CRITICAL):** The demo cases in `demo_cases.js` contain what appears to be fictional patient data (names like "Maria Chen" with patient IDs like "DEMO-001"). However, the system architecture allows entry of real patient data through the Clinical Visit form, including:
- Patient ID (free text)
- All laboratory values
- Vital signs
- Clinical assessments

This data is:
- Transmitted over HTTP to the API (no HTTPS enforcement visible in the codebase)
- Stored in-memory in Python dictionaries (`_patient_timelines`)
- Exposed via WebSocket connections (`/ws/monitor/{patient_id}`)
- Accessible through REST API endpoints without authentication (when `SAFETY_API_KEY` environment variable is not set)
- CRS grade selections persisted in browser `localStorage`

### 5.2 HIPAA Compliance

**Finding DAT-02 (CRITICAL):** The system would FAIL a HIPAA security risk assessment. Specific violations:

| HIPAA Requirement | Status |
|---|---|
| Access controls (164.312(a)) | FAIL -- Authentication disabled by default; API key auth is optional |
| Audit controls (164.312(b)) | FAIL -- No audit log of who accessed what patient data and when |
| Integrity controls (164.312(c)) | FAIL -- No checksums, digital signatures, or tamper detection |
| Transmission security (164.312(e)) | FAIL -- No HTTPS enforcement; CORS allows all origins (`allow_origins=["*"]`) |
| Person authentication (164.312(d)) | FAIL -- No user authentication; no role-based access control |
| Encryption at rest | FAIL -- Data stored in plaintext Python dicts |
| Encryption in transit | UNCERTAIN -- Depends on deployment configuration |
| Minimum necessary (164.502(b)) | FAIL -- API returns all patient data with no role-based filtering |
| Business associate agreements | N/A at this stage |

**Finding DAT-03 (MAJOR):** CORS is configured to allow ALL origins:
```python
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
```
This means any website on the internet can make API requests to this server, including submitting patient data and retrieving prediction results. This is acceptable only in a local development environment and must be restricted before any deployment.

**Finding DAT-04 (MODERATE):** The WebSocket endpoint (`/ws/monitor/{patient_id}`) has no authentication or authorization. Any client that knows or guesses a patient ID can subscribe to real-time monitoring updates for that patient.

**A compliance officer would NOT approve this for clinical use** in its current state. Even for research use with de-identified data, the open CORS policy and absent authentication represent unacceptable risk.

---

## 6. Version Control and Traceability

### 6.1 Software Version Tracking

The API reports version `"0.1.0"` in both the FastAPI app configuration (`app.py` line 119) and the health endpoint (`app.py` line 988). This is a single version string with no build number, commit hash, or build timestamp.

### 6.2 Algorithm Version Tracking

Each scoring model has a `version` field in the `ModelInfo` response (all set to `"1.0.0"`), but this version is not embedded in the scoring output. When a `PredictionResponse` is returned, it does not include which version of each algorithm produced which score.

**Finding VER-01 (MAJOR):** There is no way to determine which exact algorithm version produced a historical score. If the EASIX thresholds are modified (e.g., changing THRESHOLD_HIGH from 10.0 to 8.0), historical scores would be indistinguishable from scores computed with the new thresholds. This violates 21 CFR Part 11 traceability requirements and would fail a GCP audit.

**Finding VER-02 (MAJOR):** There is no change control documentation. No changelog, no design history file (DHF), no design control process per 21 CFR 820.30. For a medical device (or potential SaMD), the FDA requires:
- Design input documentation
- Design output documentation
- Design review records
- Design verification and validation records
- Design transfer records
- Design change documentation

**Finding VER-03 (MODERATE):** The `ScoringResult` dataclass includes a `timestamp` field, which is good. However, the `ModelInfo` response uses a hardcoded version `"1.0.0"` for all models rather than deriving it from the actual model class, creating a maintenance risk where the response version could diverge from the actual implementation.

### 6.3 Electronic Signatures and Audit Trail

**Finding VER-04 (CRITICAL):** There are no electronic signatures per 21 CFR Part 11. If this tool is used in a clinical trial context:
- Clinical assessments (CRS grade, ICANS grade) are not linked to an authenticated user
- There is no "sign and lock" functionality
- There is no audit trail of changes to clinical assessments
- Checklist items in `localStorage` can be arbitrarily modified by the user without logging

---

## 7. Risk Management Assessment

### 7.1 Failure Mode Analysis

The following failure modes represent the highest-risk scenarios:

| Failure Mode | Severity | Probability | Detectability | RPN | Mitigation in Place? |
|---|---|---|---|---|---|
| **FM-01:** False LOW risk when patient is developing severe CRS | CRITICAL (patient death) | Low-Moderate | Low (clinician may defer to tool) | **HIGH** | Partial -- model agreement summary shown, but composite score could mask individual HIGH scores if other models are LOW |
| **FM-02:** Missing lab values cause model to be skipped, incomplete risk assessment | HIGH | High (cytokine assays often unavailable) | Moderate -- skipped models shown as "Not Evaluated" | **MODERATE** | YES -- skipped models displayed in UI, data completeness metric returned |
| **FM-03:** Data entry error (e.g., entering LDH in wrong units) | HIGH | Moderate | Low -- validation catches some physiological bounds but not unit errors | **HIGH** | Partial -- physiological bounds checked (e.g., LDH max 50,000) but no unit conversion warnings |
| **FM-04:** Server crash/restart loses all patient timeline data | MODERATE | High (in-memory storage) | High (obvious data loss) | **MODERATE** | NO -- no persistence mechanism |
| **FM-05:** Composite score misinterpreted as probability | MODERATE | High (percentage display) | Low (small disclaimer) | **HIGH** | Partial -- disclaimer present but inadequate prominence |
| **FM-06:** CRS grade selected in UI does not match vital signs data | HIGH | Moderate | Low | **HIGH** | NO -- no cross-validation between selected CRS grade and vitals data |
| **FM-07:** API accessed without authentication; unauthorized modification of patient data | HIGH | Moderate (auth disabled by default) | Low | **HIGH** | Partial -- API key middleware exists but disabled when env var not set |
| **FM-08:** Teachey model returns incorrect probability due to approximate coefficients | MODERATE | Unknown | Low (no reference validation) | **MODERATE** | NO -- coefficients explicitly labeled "approximate" |

### 7.2 Risk Mitigation Assessment

**Finding RSK-01 (CRITICAL):** The single most dangerous failure mode (FM-01: false LOW risk) has insufficient mitigation. The composite score uses a confidence-weighted average, meaning a single HIGH-risk model with low confidence could be "diluted" by multiple LOW-risk models with higher confidence. Example scenario:
- HScore returns HIGH (score 200/337) with confidence 0.556 (5/9 variables)
- EASIX returns LOW with confidence 1.0
- Modified EASIX returns LOW with confidence 1.0
- CAR-HEMATOTOX returns LOW with confidence 0.6

The composite score would be dominated by the three LOW scores despite a clinically actionable HScore. While the overall risk level uses max-risk aggregation (correctly reporting HIGH), the visual composite score meter could show a low-to-moderate position, creating cognitive dissonance.

**Finding RSK-02 (MAJOR):** There is no formal risk management file per ISO 14971. For a SaMD, this is a regulatory requirement. The risk management process should include:
- Intended use and reasonably foreseeable misuse
- Hazard identification
- Risk estimation and evaluation
- Risk control measures
- Residual risk evaluation
- Risk management review

### 7.3 Alert Fatigue Risk

The alert system generates multiple simultaneous alerts without prioritization. A patient with fever, hypotension, tachycardia, and elevated ferritin could generate 4-6 alerts simultaneously. There is no mechanism to suppress lower-priority alerts when a higher-priority alert is active, and no "acknowledge and document" workflow.

---

## 8. Quality Metrics Assessment

### 8.1 Performance Tracking

**Finding QUA-01 (MAJOR):** There are NO mechanisms for tracking:
- **Sensitivity/specificity** of the scoring models against actual patient outcomes
- **False positive rate** (patients flagged HIGH who did not develop severe AEs)
- **False negative rate** (patients scored LOW who did develop severe AEs)
- **Clinician override rate** (how often clinicians disagreed with the tool's assessment)
- **Alert response time** (time from alert generation to clinical action)
- **Alert acknowledgment rate**
- **Model accuracy drift** over time as patient populations change

### 8.2 System Performance Metrics

The middleware tracks request timing (`X-Process-Time` header) and rate limiting, which is a start. The health endpoint reports uptime and model availability. However, there is no:
- Response time percentile tracking (P50, P95, P99)
- Error rate monitoring
- Model execution time per model
- Dashboard for operational metrics

### 8.3 Clinical Outcome Tracking

**Finding QUA-02 (CRITICAL for clinical trial use):** There is no mechanism to record actual clinical outcomes and compare them to predicted risk levels. This is essential for:
- Post-market surveillance (if deployed as a device)
- Continuous model validation
- Identifying population subgroups where models perform poorly
- Regulatory submissions demonstrating real-world performance

---

## 9. Additional Regulatory Findings

### 9.1 Intended Use Statement

**Finding ADD-01 (MAJOR):** There is no formal Intended Use / Indications for Use statement. This is the foundational document for any regulatory strategy. The intended use must specify:
- Target user population (cell therapy physicians, nurse practitioners, pharmacists?)
- Target patient population (specific CAR-T products? specific indications?)
- Clinical setting (REMS-certified facilities only? academic medical centers?)
- Intended role in clinical workflow (screening? monitoring? reporting?)
- What the tool is NOT intended for

### 9.2 Labeling

**Finding ADD-02 (MODERATE):** The current "labeling" (in the regulatory sense) consists only of the dashboard title, the footer disclaimer, and the API description. For a clinical tool, even one not regulated as a medical device, proper labeling should include:
- Instructions for use (IFU)
- User manual
- Quick reference guide
- Training requirements
- Technical requirements and system specifications
- Known limitations

### 9.3 International Regulatory Considerations

If this tool is intended for use outside the United States:
- EU MDR (Medical Device Regulation 2017/745) has a broader definition of SaMD than the FDA
- UK MHRA has specific guidance on standalone clinical decision support
- Health Canada and TGA (Australia) have separate SaMD classification frameworks
- All jurisdictions would likely classify this as a medical device requiring regulatory approval

---

## 10. Prioritized Recommendations

### Immediate (Before Any Clinical Exposure)

| # | Finding | Action Required |
|---|---|---|
| 1 | DIS-01 | Implement a comprehensive, prominent disclaimer that appears on every page and at the top of every API response. Include explicit "NOT an FDA-cleared medical device" language. |
| 2 | DAT-02 | Restrict CORS to specific authorized origins. Enable HTTPS. Enable API key authentication by default. |
| 3 | DAT-03 | Implement user authentication with role-based access control. |
| 4 | VER-04 | Implement audit trail logging for all clinical data access and modifications. |
| 5 | SAF-01 | Add SAE classification and reporting capability if the tool will be used in a clinical trial context. |

### Short-Term (Before Pilot Deployment)

| # | Finding | Action Required |
|---|---|---|
| 6 | REG-01 | Add Tecartus to the product selector. |
| 7 | REG-02 | Add REMS data elements (CRS/ICANS onset/resolution dates, interventions, outcomes) to the API schema. |
| 8 | VAL-01 | Obtain and implement exact Teachey coefficients from the original publication or corresponding author. If exact coefficients are unavailable, clearly label this model as "approximation" in the UI and reduce its weight in the composite. |
| 9 | RSK-01 | Add visual prominence to model discordance warnings. Consider showing the composite score meter ONLY when models agree, and showing a "DISCORDANT -- REVIEW INDIVIDUAL SCORES" alert when they disagree. |
| 10 | DIS-02 | Engage regulatory counsel to determine whether the tool requires FDA clearance. Document the regulatory strategy. |
| 11 | VER-01 | Embed algorithm version identifiers in every scoring result. Implement change control documentation. |
| 12 | FM-04 | Implement persistent data storage (database) for patient timelines and clinical assessments. |

### Medium-Term (Before Broad Deployment)

| # | Finding | Action Required |
|---|---|---|
| 13 | QUA-01 | Implement outcome tracking and model performance metrics. |
| 14 | RSK-02 | Create a formal risk management file per ISO 14971. |
| 15 | ADD-01 | Draft a formal Intended Use statement. |
| 16 | SAF-02 | Expand safety detection to include TLS, DIC, cardiac toxicity, AKI, and infection/sepsis differentiation. |
| 17 | REG-04 | Enhance the ICE calculator to incorporate consciousness level, seizure status, and cerebral edema for accurate ICANS grading. |
| 18 | VAL-02 | Document the provenance and validation status of all risk stratification thresholds. |
| 19 | ADD-02 | Develop user-facing documentation (IFU, user manual, training materials). |
| 20 | QUA-02 | Implement prospective outcome tracking to enable continuous model validation. |

---

## 11. Positive Findings

While this review has focused on deficiencies (as is appropriate for a regulatory assessment), the following positive aspects should be acknowledged:

1. **Algorithm implementations are well-documented** with inline citations, formula documentation, and clear code structure. The biomarker scoring code in `biomarker_scores.py` is among the best-documented clinical algorithm implementations I have reviewed.

2. **Input validation is robust.** Physiological bounds checking, NaN/Inf rejection, and type validation are thorough. The `_validate_positive`, `_validate_non_negative_int`, and `_validate_bool` helper functions are well-designed.

3. **The layered ensemble architecture** (Standard Labs + Cytokine Panel) correctly reflects clinical data availability patterns. Not all centers have access to cytokine assays, and the tool gracefully degrades when data is unavailable.

4. **Partial scoring with confidence adjustment** (e.g., HScore computing with 5/9 variables and reducing confidence proportionally) is a pragmatic approach that maintains clinical utility while communicating uncertainty.

5. **CRS and ICANS grading scales are accurate** per ASTCT consensus criteria.

6. **Clinical management algorithms** (CRS management by grade, ICANS management by grade) are consistent with current NCCN and ASTCT guidelines.

7. **The teaching points and clinical workflow tabs** (Pre-Infusion, Day 1, CRS Monitor, ICANS, HLH, Hematologic, Discharge) demonstrate deep domain knowledge of the CAR-T clinical care pathway.

8. **The anticipated test ordering system** is clinically intelligent, adjusting recommendations based on the patient's current status (e.g., adding blood cultures and ferritin when fever is present).

9. **Model discordance detection** in the ensemble runner is a valuable safety feature.

10. **Request traceability** (request IDs, timestamps on all responses) provides a foundation for audit trail capability.

---

## 12. Conclusion

This platform represents a technically competent implementation of published clinical scoring algorithms for CAR-T cell therapy safety monitoring. The clinical domain knowledge embedded in the workflows, alert logic, and teaching content is of high quality. However, the system has fundamental gaps in regulatory compliance, data governance, and clinical safety infrastructure that preclude clinical use in its current form.

The most critical path to clinical deployment is: (1) formal regulatory strategy determination (SaMD vs. CDS exemption), (2) HIPAA-compliant data architecture, (3) comprehensive disclaimers, and (4) audit trail implementation. These four items are non-negotiable prerequisites for any clinical exposure, including research use with real patient data.

I would recommend engaging FDA regulatory counsel before investing further development effort, as the regulatory classification determination will fundamentally shape the required development, testing, and documentation activities.

---

*This review was conducted based on source code review only. No live system testing was performed. Findings should be verified through hands-on testing and independent clinical validation.*

**Reviewer Credentials:**
Thomas Eriksson, MPH, RAC
Regulatory Affairs Certified (RAC) -- Regulatory Affairs Professionals Society
Master of Public Health, Epidemiology concentration
Experience: 12 years in regulatory affairs for cell and gene therapy programs, including 5 approved CAR-T BLAs and associated REMS programs.
