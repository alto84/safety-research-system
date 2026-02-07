# Clinical Pharmacist Review: Cell Therapy Safety Platform Dashboard

**Reviewer:** Dr. Kevin Park, PharmD, BCOP
**Role:** Board-Certified Oncology Pharmacist, CAR-T REMS Program Manager
**Date:** 2026-02-07
**Files Reviewed:**
- `src/api/static/index.html` (Clinical Dashboard)
- `src/api/static/demo_cases.js` (8 Demo Clinical Cases)

---

## 1. Medication Management: CRS Management Algorithm

### What the dashboard includes

The CRS Management Algorithm (rendered in `renderCRS()`, lines 1022-1034 of index.html) provides grade-stratified treatment guidance:

| CRS Grade | Dashboard Guidance | Pharmacist Assessment |
|-----------|-------------------|----------------------|
| Grade 1 | Supportive care. Acetaminophen for fever. Monitor vitals q4h. | **Acceptable.** Standard of care. |
| Grade 2 | Consider Tocilizumab 8mg/kg IV (max 800mg). IV fluids. Monitor q2h. | **Correct dosing.** Tocilizumab 8mg/kg IV with max 800mg cap is per ASTCT consensus and FDA labeling. |
| Grade 3 | Tocilizumab + Dexamethasone 10mg IV q6h. Vasopressor support. ICU transfer. Monitor q1h. | **Correct.** Dexamethasone 10mg IV q6h is standard per NCCN and institutional protocols. |
| Grade 4 | Tocilizumab + High-dose methylprednisolone 1g IV. Mechanical ventilation PRN. ICU mandatory. | **Correct.** Methylprednisolone 1g IV pulse dosing is appropriate for Grade 4/refractory CRS. |

### ICANS Management Algorithm (lines 1230-1243)

| ICANS Grade | Dashboard Guidance | Pharmacist Assessment |
|-------------|-------------------|----------------------|
| Grade 1 (ICE 7-9) | Non-sedating seizure prophylaxis (levetiracetam 750mg BID). Monitor q8h. | **Dosing concern.** Standard levetiracetam seizure prophylaxis is typically 500mg BID, titrated to 750mg BID as needed. Starting at 750mg BID is acceptable but slightly aggressive for prophylaxis in elderly patients (e.g., Case 5, age 71). Case 5 clinical note correctly uses 500mg BID. The discrepancy between the algorithm display (750mg BID) and the demo case note (500mg BID) should be reconciled. |
| Grade 2 (ICE 3-6) | Dexamethasone 10mg IV q6h. Consider MRI. Neurology consult. | **Correct.** |
| Grade 3 (ICE 0-2) | Dexamethasone 10mg IV q6h or methylprednisolone 1mg/kg. ICU transfer. Continuous EEG. | **Correct.** Methylprednisolone 1mg/kg BID is an appropriate alternative/escalation. |
| Grade 4 (ICE 0, obtunded) | Methylprednisolone 1g IV daily x3 days. ICU mandatory. Consider intubation. | **Correct.** Pulse-dose methylprednisolone 1g/day x3 is standard for Grade 4 ICANS. |

### Strengths
- Tocilizumab 8mg/kg with 800mg cap is precisely correct per FDA labeling for all approved CAR-T products.
- Steroid escalation ladder is appropriately tiered (dexamethasone 10mg -> methylprednisolone 1mg/kg -> methylprednisolone 1g pulse).
- Grade-specific interventions match ASTCT consensus guidelines.

### Gaps
- **No acetaminophen dosing specified.** Should state: acetaminophen 650-1000mg PO/IV q4-6h PRN, max 4g/24h (or 2g/24h in hepatic impairment -- relevant in CRS with transaminitis).
- **No tocilizumab infusion rate guidance.** Should specify: infuse over 60 minutes. Do NOT administer as IV push or bolus.
- **No weight-based dosing example or dose calculator.** For a 92kg patient like James Williams (Case 2), calculated dose = 736mg. For a 58kg patient like Maria Chen (Case 1), dose = 464mg. A built-in calculator would reduce dosing errors.
- **No mention of tocilizumab availability requirement at bedside** in the CRS Monitor view (it IS mentioned in the Pre-Infusion checklist, which is good).

---

## 2. Drug Interactions and Drugs to Avoid During CAR-T

### Critical gap: No drug interaction guidance

The dashboard does **not** include any drug interaction warnings or contraindicated medication lists. This is a significant omission for a clinical decision support tool.

**Missing content that should be present:**

1. **Systemic corticosteroids prior to infusion:** The dashboard does not warn against corticosteroid use in the 72 hours before CAR-T infusion. All product labels (Yescarta, Kymriah, Breyanzi, Abecma, Carvykti) recommend avoiding systemic corticosteroids before infusion as they may impair CAR-T cell expansion and efficacy. Case 3 (Patricia Rodriguez) received dexamethasone 40mg weekly as bridging therapy -- the dashboard should flag the washout period requirement.

2. **Live vaccines:** Post-CAR-T patients have prolonged B-cell aplasia and immunosuppression. No mention of avoiding live vaccines for at least 6 weeks before lymphodepletion and indefinitely post-infusion until immune reconstitution.

3. **Myelosuppressive agents:** No warning about concurrent myelosuppressive drugs that could compound CAR-T-related cytopenias.

4. **CYP450 interactions with tocilizumab:** Tocilizumab can normalize CYP450 enzyme activity (particularly CYP3A4) that is suppressed during inflammation. This can reduce levels of concurrently administered drugs metabolized via CYP3A4 (e.g., simvastatin, cyclosporine, warfarin). The dashboard should flag this for patients on narrow therapeutic index drugs.

5. **Levetiracetam interactions:** While levetiracetam has minimal drug interactions, it requires renal dose adjustment. Case 3 (creatinine 1.4, eGFR 52) would need dose reduction. No renal dosing guidance is provided.

6. **G-CSF timing:** The dashboard recommends G-CSF (filgrastim 5mcg/kg) for ANC <0.5 (line 1395), but does not specify timing restrictions. Per consensus, G-CSF should generally be avoided in the first 21 days post-infusion as it may exacerbate CRS by stimulating myeloid-derived cytokine release. The appropriate timing threshold (typically day 14+ or day 21+, varying by institution) should be stated.

---

## 3. REMS Compliance

### What the dashboard includes

The Discharge view (lines 1406-1477) contains a readiness checklist with the item:
> "REMS requirements reviewed"

This is rendered as an unchecked checkbox in the discharge criteria list (line 1422).

### Assessment: Insufficient for REMS compliance

The single checkbox "REMS requirements reviewed" is **critically inadequate** for REMS documentation. Each approved CAR-T product has its own REMS program, and the dashboard should capture:

1. **Product-specific REMS certification:** Yescarta, Kymriah, Breyanzi, Abecma, and Carvykti each have separate REMS programs. The dashboard knows the product (it's in the patient data) but doesn't tailor REMS requirements accordingly.

2. **Required REMS elements not captured:**
   - Certification that the healthcare facility is enrolled in the specific product REMS
   - Verification that the prescriber is certified under the REMS
   - Documentation that tocilizumab (minimum 2 doses per patient) is available on-site prior to infusion
   - Patient enrollment in the REMS program
   - Mandatory 4-week post-infusion monitoring proximity requirement (patient must reside within 2 hours of the certified facility -- this IS captured in the discharge checklist, which is good)
   - Adverse event reporting requirements to the REMS program
   - Training documentation for nursing and pharmacy staff

3. **No REMS lot/product verification step:** The Pre-Infusion checklist includes "Leukapheresis product thawed and verified" but does not include chain-of-identity verification (patient identity matching to the specific autologous product), which is a REMS and institutional safety requirement.

4. **No post-marketing REMS reporting prompts:** The discharge view should prompt for adverse event reporting to the REMS program (and to FDA MedWatch) for any Grade 3+ CRS, Grade 3+ ICANS, or prolonged cytopenias.

---

## 4. Prophylaxis Medications

### What the dashboard includes

- **Seizure prophylaxis:** Mentioned in ICANS management (levetiracetam 750mg BID for Grade 1 ICANS, line 1232). Also mentioned in Case 5 clinical notes (levetiracetam 500mg BID, line 1399).
- **G-CSF for neutropenia:** Filgrastim 5mcg/kg daily recommended when ANC <0.5 (line 1395).

### What is missing

1. **Antimicrobial prophylaxis -- entirely absent.** This is a major gap. Standard of care for CAR-T patients includes:
   - **Antiviral prophylaxis:** Acyclovir 400mg PO BID or valacyclovir 500mg PO daily for HSV/VZV reactivation prevention. Should begin at lymphodepletion and continue for at least 1 year or until CD4 recovery >200.
   - **PJP prophylaxis:** Trimethoprim-sulfamethoxazole (TMP-SMX) DS 1 tablet PO three times weekly, or alternatives (atovaquone 1500mg PO daily, or dapsone 100mg PO daily). Should begin after count recovery and continue for at least 6 months.
   - **Antifungal prophylaxis:** Fluconazole 200-400mg PO daily during neutropenia (ANC <0.5). Some institutions use micafungin 50mg IV daily in the setting of mucositis.
   - **Antibacterial prophylaxis:** Levofloxacin 500mg PO daily during severe neutropenia (ANC <0.5) per institutional policy, though this varies.

2. **No IVIG replacement guidance during the acute phase.** The Discharge view mentions IgG monitoring and "IVIG if IgG <400" (line 1470), which is good. However, there is no guidance on IgG monitoring during the inpatient phase when hypogammaglobulinemia can be acute.

3. **Seizure prophylaxis timing is unclear.** Some institutions initiate levetiracetam prophylactically for all patients beginning on the day of infusion (especially for axi-cel, which has higher ICANS rates). Others initiate at first sign of ICANS. The dashboard should state the institutional approach clearly.

4. **Tumor lysis syndrome prophylaxis:** Not mentioned anywhere. For patients with high tumor burden (e.g., Case 2, LDH 842), allopurinol or rasburicase should be considered. While TLS is uncommon with CAR-T, it is reported and the high-risk cases warrant prophylaxis discussion.

5. **Antiemetic prophylaxis:** Not mentioned. Patients receiving lymphodepletion with fludarabine/cyclophosphamide require antiemetic prophylaxis (ondansetron, +/- dexamethasone -- though steroids are generally avoided peri-infusion).

---

## 5. Pharmacokinetic Considerations: Tocilizumab Timing and Re-dosing

### What the dashboard includes

The CRS Management Algorithm provides grade-specific tocilizumab recommendations. Demo Case 2 (James Williams) clinical notes document:
- First tocilizumab dose at Grade 3 CRS onset (Day 2)
- Second tocilizumab dose given within 8 hours when first was insufficient (Day 3 clinical note references this per ASTCT guidelines)

Case 4 (Robert Kim) documents a second tocilizumab for IEC-HS on Day 5.

### Assessment: Key PK details missing from the algorithm display

1. **Maximum number of doses not stated.** Per FDA labeling, maximum 3 doses of tocilizumab in a 24-hour period, and maximum 4 doses total. The dashboard algorithm does not state these limits. Exceeding 3 doses without clinical response should prompt consideration of alternative agents (siltuximab, corticosteroid escalation).

2. **Minimum interval between doses not stated.** The minimum interval is 8 hours between tocilizumab doses. This is critical safety information that should be displayed in the CRS management algorithm.

3. **Onset of action not communicated.** Tocilizumab typically shows clinical improvement (defervescence, hemodynamic improvement) within 1-4 hours. If no improvement within 8 hours, a second dose or escalation should be considered. This decision-support timing is absent.

4. **Post-tocilizumab IL-6 interpretation missing from CRS Monitor view.** The teaching point in Case 2 correctly states that IL-6 rises paradoxically after tocilizumab (due to IL-6 receptor blockade increasing free serum IL-6). However, this critical pharmacologic concept is not communicated in the CRS Monitor view itself. Clinicians viewing IL-6 values post-tocilizumab could misinterpret rising IL-6 as treatment failure. A warning label on IL-6 values post-tocilizumab should be added.

5. **Weight-based dosing with actual body weight.** The dashboard does not specify whether to use actual body weight (ABW), ideal body weight (IBW), or adjusted body weight. Per FDA labeling, actual body weight should be used. For obese patients, some institutions cap at 100kg. This should be stated.

6. **Tocilizumab preparation and stability:** Not mentioned. Tocilizumab for CRS should be pre-mixed and available at bedside (not in pharmacy), with 24-hour room temperature stability once diluted. This operational pharmacy detail matters for rapid administration.

---

## 6. Lab Monitoring for Drug Toxicity

### Tocilizumab-related monitoring

The dashboard includes the following relevant labs:
- **AST** (in NORMAL_RANGES, tracked across all demo cases)
- **Platelets** (tracked)
- **ANC** (tracked)

**Gaps:**
- **ALT is defined in demo case data but NOT in the dashboard's NORMAL_RANGES constant** (lines 492-503 of index.html). ALT is present in every demo case lab panel but the dashboard only defines AST for flagging. Both AST and ALT should be monitored for tocilizumab hepatotoxicity. Tocilizumab carries a boxed warning for hepatotoxicity (ALT/AST >5x ULN warrants holding the drug). The dashboard should flag when transaminases exceed 5x ULN as a specific tocilizumab safety threshold, not just the standard high/low range flags.
- **No hepatitis B screening mentioned.** Tocilizumab requires HBV screening (HBsAg, anti-HBc) before use due to risk of HBV reactivation. This should be in the pre-infusion checklist.
- **No GI perforation warning.** Tocilizumab carries a risk of GI perforation. While rare in the CAR-T context, patients with concurrent diverticulitis or GI involvement should be flagged.

### Corticosteroid-related monitoring

**Not present in the dashboard:**
- **Glucose monitoring.** High-dose dexamethasone (10mg IV q6h) and methylprednisolone (1g IV) cause significant hyperglycemia. The dashboard has no glucose in its lab panels or NORMAL_RANGES. For patients on high-dose steroids, blood glucose should be monitored q6h with sliding-scale insulin coverage. This is especially relevant for Case 6 (David Okafor) and Case 3 (Patricia Rodriguez, myeloma patients who may have pre-existing steroid-induced glucose intolerance).
- **Blood pressure monitoring during steroid escalation.** While vitals are tracked, there is no specific alert for steroid-induced hypertension.
- **Steroid taper schedule not protocolized.** Case 2 and Case 5 clinical notes mention steroid tapers, but the dashboard provides no standardized taper protocol. Abrupt discontinuation of high-dose steroids risks adrenal crisis. A recommended taper schedule should be displayed (e.g., dexamethasone 10mg q6h x 2 days, then 10mg q12h x 2 days, then 10mg daily x 2 days, then discontinue).

### Additional monitoring gaps

- **Coagulation studies (PT/INR, PTT):** Not in the dashboard lab panel. Relevant for DIC monitoring during IEC-HS (Case 4) and for patients on anticoagulants who receive tocilizumab (CYP450 normalization effect on warfarin).
- **Uric acid:** Not tracked. Relevant for tumor lysis syndrome risk in high-burden cases.
- **Phosphorus, potassium, calcium:** Not in the standard panel. Relevant for TLS monitoring and steroid-related electrolyte shifts.

---

## 7. Top 5 Improvements (Pharmacist Perspective)

### 1. Add a Comprehensive Medication Safety Panel

**Priority: CRITICAL**

Create a dedicated "Medications" tab or card within each view that includes:
- Active medication list with doses, routes, frequencies
- Drug interaction checker highlighting tocilizumab CYP450 effects
- Antimicrobial prophylaxis protocol (antiviral, antifungal, PJP, antibacterial)
- Steroid taper protocol with dose calculator
- Tocilizumab dose calculator (weight-based, with 800mg cap enforcement)
- Maximum tocilizumab dose counter (tracking doses 1-4, with 8-hour interval enforcement)
- Contraindicated medication list (pre-infusion corticosteroids, live vaccines, myelosuppressive agents without indication)

This is the single most impactful addition from a medication safety perspective. The dashboard currently has no medication management view at all.

### 2. Add Glucose Monitoring and Steroid-Specific Safety Alerts

**Priority: HIGH**

- Add blood glucose to the lab monitoring panel (NORMAL_RANGES) with alerts at >180 mg/dL and >250 mg/dL
- When steroids are active (Grade 2+ CRS with dexamethasone, or any ICANS requiring steroids), auto-generate orders for blood glucose monitoring q6h and insulin sliding scale
- Add steroid taper protocol as a structured, step-down display (not free-text in clinical notes)
- Flag steroid contraindications: active infection without coverage, uncontrolled diabetes, GI bleeding history

### 3. Expand REMS Documentation to Product-Specific Checklists

**Priority: HIGH**

Replace the single "REMS requirements reviewed" checkbox with a product-specific REMS panel that includes:
- Prescriber/facility certification verification
- Tocilizumab bedside availability confirmation (quantity: minimum 2 doses calculated for the patient's weight)
- Chain-of-identity verification for autologous product
- Patient REMS enrollment confirmation
- Adverse event reporting prompts (auto-triggered by Grade 3+ CRS/ICANS)
- 4-week proximity requirement documentation
- Post-discharge REMS follow-up scheduling

### 4. Add Post-Tocilizumab IL-6 Interpretation Warning

**Priority: HIGH**

When IL-6 values are displayed after a tocilizumab dose has been administered, add a prominent warning:

> "IL-6 values are unreliable for 2-3 weeks after tocilizumab administration. Tocilizumab blocks the IL-6 receptor, causing paradoxical elevation of free serum IL-6. Elevated IL-6 post-tocilizumab does NOT indicate treatment failure. Assess clinical response (fever curve, hemodynamics, oxygen requirement) rather than IL-6 levels to guide re-dosing decisions."

This prevents one of the most common pharmacologic misinterpretations in CAR-T management.

### 5. Add Antimicrobial Prophylaxis Protocol Display

**Priority: HIGH**

Create a prophylaxis section (either in Pre-Infusion or as a persistent sidebar element) displaying:

| Prophylaxis | Agent | Dose | Start | Duration |
|------------|-------|------|-------|----------|
| HSV/VZV | Acyclovir | 400mg PO BID | Day of lymphodepletion | 1 year or until CD4 >200 |
| PJP | TMP-SMX DS | 1 tab PO 3x/week | After count recovery | 6+ months |
| Fungal | Fluconazole | 200-400mg PO daily | During ANC <0.5 | Until ANC recovery |
| Bacterial | Levofloxacin | 500mg PO daily | During ANC <0.5 (per institutional policy) | Until ANC recovery |
| IVIG | Immunoglobulin | 400-500mg/kg IV | IgG <400 mg/dL | PRN based on levels |
| Seizure | Levetiracetam | 500-750mg PO BID | Per institutional protocol | 30 days post-ICANS resolution |

This is fundamental infection prevention that is entirely absent from the current dashboard.

---

## Summary Assessment

| Domain | Rating | Notes |
|--------|--------|-------|
| CRS Drug Dosing | Good | Tocilizumab and steroid doses are correct per guidelines |
| ICANS Drug Dosing | Good | Steroid escalation ladder is appropriate |
| Drug Interactions | Not Present | No interaction checking or contraindication warnings |
| REMS Compliance | Poor | Single checkbox; no product-specific documentation |
| Prophylaxis | Poor | Only seizure prophylaxis and G-CSF mentioned; no antimicrobials |
| PK Considerations | Fair | Correct in demo notes but not in algorithm display |
| Lab Monitoring for Drug Toxicity | Fair | AST tracked but ALT missing from flagging; no glucose |
| Medication Safety Overall | Needs Improvement | No medication management view, no dose calculators |

The dashboard has a strong clinical foundation with correct grading criteria and risk scores. However, **it functions as a risk assessment and monitoring tool rather than a comprehensive clinical decision support system**. The absence of a medication management layer -- including prophylaxis protocols, drug interaction warnings, dose calculators, REMS documentation, and drug-specific lab monitoring -- represents the most significant gap from a pharmacist's perspective. Adding these elements would transform this from a monitoring dashboard into a true safety platform.

---

*Review completed by Dr. Kevin Park, PharmD, BCOP*
*Board-Certified Oncology Pharmacist | CAR-T REMS Program Manager*
