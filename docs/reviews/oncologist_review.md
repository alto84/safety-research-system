# Oncologist Clinical Review: Cell Therapy Safety Platform

**Reviewer:** Dr. Sarah Nguyen, MD (Cell Therapy / Hematologic Oncology)
**Experience:** 5 years managing CAR-T patients, ~100+ total cases
**Date:** 2026-02-07
**Files Reviewed:** `index.html` (dashboard), `demo_cases.js` (8 demo patients)

---

## 1. Clinical Accuracy

### CRS Grading Criteria (ASTCT Consensus)

The CRS grading in `CRS_GRADES` (index.html lines 506-512) is **mostly correct** per Lee et al. 2019 ASTCT consensus, but has notable issues:

- **Grade 1:** Correctly defined as fever >= 38.0C without hypotension or hypoxia. **Accurate.**
- **Grade 2:** States "hypotension not requiring vasopressors, and/or hypoxia requiring low-flow O2." **Accurate**, but should specify "low-flow nasal cannula" explicitly rather than just "low-flow O2" since the distinction from high-flow is clinically critical.
- **Grade 3:** States "hypotension requiring a vasopressor (+/- vasopressin), and/or hypoxia requiring high-flow O2 or non-rebreather." **Accurate.**
- **Grade 4:** States "hypotension requiring multiple vasopressors, and/or hypoxia requiring positive pressure (CPAP/BiPAP/ventilator)." **Accurate.**

**Error:** The CRS grading display has 5 boxes (Grade 0-4), which is correct, but the interactive grade selector (onclick toggle) is cosmetic-only with no data binding. If a clinician clicks Grade 3, it does not update any state or trigger re-assessment. This is a false affordance -- it looks interactive but does nothing useful.

**Missing from CRS grading:** The ASTCT criteria explicitly require that fever (T >= 38.0C) must be present AND not attributable to another cause. The dashboard does not prompt the clinician to consider alternative etiologies (infection, drug fever, transfusion reaction) before assigning a CRS grade. This is a clinically important omission.

### HScore Thresholds

- The 169-point threshold for >93% HLH probability is **correct** per Fardet et al. 2014.
- The maximum score of 337 is **correct**.
- HLH warning triggers at ferritin >10,000 and fibrinogen <1.5 g/L. These are **clinically appropriate** thresholds.

**Issue:** The HScore component breakdown table relies on the API prediction response. If the API is disconnected (which it often is in a demo), the HScore section shows nothing actionable. There should be a fallback calculator using the form inputs, similar to the ICE score calculator.

### Management Algorithms

**CRS Management (lines 1022-1034):**
- Grade 1: Supportive care + acetaminophen. **Correct.**
- Grade 2: "Consider Tocilizumab 8mg/kg IV (max 800mg)." **Partially correct.** The max dose should be specified as "max 800mg per dose" and the current guidelines recommend tocilizumab at Grade 2 for patients with comorbidities or risk factors, not universally. The word "consider" is appropriate but the algorithm lacks nuance about when to pull the trigger vs. observe.
- Grade 3: Tocilizumab + Dexamethasone 10mg IV q6h. **Correct per most institutional protocols.** However, some centers use methylprednisolone 1mg/kg as an alternative to dexamethasone. This option is not presented.
- Grade 4: Tocilizumab + "High-dose methylprednisolone 1g IV." **Correct.** However, the algorithm does not specify this should be pulse dosing (typically 1g daily x 3 days), which is important.

**ICANS Management (lines 1230-1244):**
- Grade 1: Levetiracetam 750mg BID. **Reasonable but debatable.** Some centers do not start seizure prophylaxis until Grade 2. The ASTCT guidelines recommend seizure prophylaxis at Grade >= 2. Starting at Grade 1 is more aggressive and institution-dependent. The dose of 750mg BID is the correct prophylactic dose.
- Grade 2: Dexamethasone 10mg IV q6h. **Correct.**
- Grade 3: Dexamethasone 10mg IV q6h or methylprednisolone 1mg/kg. **Correct.** Should also mention consider intubation for airway protection.
- Grade 4: Methylprednisolone 1g IV daily x3 days. **Correct.** Mentioning neurosurgery consult for cerebral edema is appropriate.

**Critical omission in ICANS management:** No mention of tocilizumab for concurrent CRS. If ICANS occurs WITH CRS (as in Case 2, James Williams), tocilizumab should be given for the CRS component, and steroids for the ICANS component. The management algorithm presents them as isolated entities.

### EASIX Score

- Formula is LDH x Creatinine / Platelets. The dashboard correctly sends these three parameters to the API.
- **Issue with thresholds:** The dashboard displays EASIX as high/moderate/low risk but the actual validated cutpoints are not shown to the clinician. The original EASIX publication (Luft et al. 2017) used specific cutpoints. For CAR-T CRS prediction, the pre-infusion EASIX cutpoint for severe CRS varies by study (some use 3.2, others use different values). The dashboard should display what thresholds it uses.

### CAR-HEMATOTOX Score

- The dashboard correctly identifies this as Rejeski et al. Blood 2021.
- Score range 0-10 is **incorrect.** The actual CAR-HEMATOTOX model uses a 0-2 composite score based on the HCT-CI adapted scoring, with components scored 0-2 each for 5 variables. **However**, the published simplified scoring uses a binary high (>=2) vs. low (<2) cutpoint. The dashboard displays scores of 0-4 in the demo cases, which does not match the published 0-2 range. **This needs verification against the actual scoring implementation.**
- The >=3 threshold for "high risk" (line 1347) does not match the published cutpoint of >=2.

**This is a significant clinical accuracy concern.** If the scoring thresholds are wrong, clinicians could under-triage patients.

---

## 2. Workflow Fit

### Task Navigation Assessment

The task tabs are: Overview, Pre-Infusion, Day 1 Monitor, CRS Monitor, ICANS, HLH Screen, Hematologic, Discharge, Clinical Visit.

**What works:**
- The progression from Pre-Infusion through Day 1, CRS, ICANS, HLH, Hematologic, to Discharge roughly mirrors the clinical timeline. This is logical.
- The Overview tab providing a composite risk summary is useful as a "landing page."
- The Clinical Visit tab for manual data entry is essential for real-world use.

**What does not match clinical workflow:**

1. **No "Active CRS Management" tab.** When a patient is actively in Grade 2-3 CRS, I need a single view showing: current CRS grade, current interventions (tocilizumab doses given, steroid regimen, vasopressor status, O2 requirement), and what has been tried. The CRS Monitor tab shows grading criteria and lab trends but not the management state.

2. **No "Infection Workup" tab or section.** Every fever in a CAR-T patient requires simultaneous CRS assessment AND infection workup. The dashboard does recommend blood cultures in the anticipated tests, but there is no dedicated space to track culture results, antibiotic status, or infection vs. CRS differential. In practice, I spend significant time distinguishing the two.

3. **Missing "Orders/Interventions" tracking.** The dashboard shows what tests to order (anticipated tests) but has no way to track what has actually been done. A checklist is only useful if it persists and can be shared with the nursing team.

4. **The Day 1 tab is too narrow.** Day 1 is important, but the Hay binary classifier is a niche tool that most centers do not have MCP-1 assays available for. This tab should be "Early Monitoring (Day 0-3)" rather than just Day 1, since most of the early CRS risk assessment happens over the first 72 hours.

5. **No longitudinal trending view.** I cannot see how labs have trended across timepoints on a single screen. Clicking through individual timepoints is clunky. I need sparklines or small multiples showing CRP, ferritin, LDH, and counts over time on the overview.

---

## 3. Decision Support -- Anticipated Test Recommendations

### Tests That Are Correctly Recommended

The `getAnticipatedTests()` function (lines 1747-1782) dynamically recommends tests based on current state:
- CBC, CMP, CRP daily -- **Correct, standard of care.**
- Vital signs q4h -- **Correct.**
- Blood cultures with fever -- **Correct and important.**
- Ferritin with fever -- **Correct.**
- IL-6 and MCP-1 at higher fevers -- **IL-6 is reasonable; MCP-1 is aspirational** (most centers cannot obtain this).
- G-CSF when ANC <0.5 -- **Reasonable but timing is debated.** Some centers hold G-CSF during active CRS due to concern about exacerbating inflammation.
- ICE score q8-12h -- **Correct.**
- Immunoglobulins weekly -- **Correct for outpatient.**

### Tests That Are Missing

1. **Coagulation panel (PT/INR/PTT):** Not in the standard anticipated tests. Essential when fibrinogen is dropping -- DIC monitoring requires a full coag panel, not just fibrinogen.
2. **Uric acid:** Should be monitored when LDH is rising rapidly (tumor lysis risk, especially in high-burden cases like DEMO-002).
3. **Phosphate, calcium, potassium:** Tumor lysis labs -- critical in the first 72 hours for high-burden patients.
4. **Procalcitonin:** Increasingly used to distinguish infection from CRS-related fever. Not a perfect test but clinically useful.
5. **Lactate:** When patients are hypotensive, lactate is essential to assess perfusion. Not mentioned anywhere.
6. **BNP or troponin:** For Grade 3-4 CRS with hemodynamic instability, cardiac biomarkers should be checked. CRS can cause cardiomyopathy.
7. **Chest X-ray:** Should be recommended when O2 requirement develops, not just "CT chest if persistent hypoxia."
8. **Urinalysis:** Baseline and with AKI -- simple but missing.
9. **sCD25 (soluble IL-2 receptor):** Mentioned in Case 4 anticipated tests but not in the dynamic test generator. This is a key HLH marker.
10. **Blood smear review:** Should be recommended when cytopenias develop to look for hemophagocytes, schistocytes (TMA), or relapse.

### Over-recommendation Issues

- MCP-1 is recommended as STAT but is a send-out test at most centers with multi-day turnaround. Presenting it as "STAT" will confuse ordering teams. Should be labeled "if available locally" more prominently.

---

## 4. Demo Cases -- Clinical Realism

### Case 1 (Maria Chen -- Low-risk DLBCL): **Clinically realistic.**
- Lab trajectory is believable. CRP peaks appropriately before ferritin. ANC nadir timing from flu/cy is correct (day 3-5 post-conditioning).
- **Minor issue:** EASIX at baseline is 0.74 but at Day 3 jumps to 3.12 primarily from platelet drop. The EASIX was designed as a pre-infusion predictor; serial EASIX has less validated meaning. The dashboard does not distinguish pre-infusion EASIX from serial EASIX.

### Case 2 (James Williams -- High-risk): **Clinically realistic and well-constructed.**
- The rapid CRS escalation with high tumor burden is textbook.
- IL-6 rising to 2400 post-tocilizumab is realistic (receptor blockade effect).
- **Concern:** CRS Grade 3 at Day 2 post-infusion is early even for axi-cel. Median CRS onset for axi-cel is day 2, but Grade 3 by day 2 is at the very aggressive end. Not impossible but worth noting this represents the extreme.
- The HScore of 182 on Day 3 correctly raises HLH concern.

### Case 3 (Patricia Rodriguez -- Myeloma): **Clinically realistic.**
- Ide-cel CRS kinetics are well-represented.
- Creatinine trajectory with baseline renal impairment is realistic.
- **Issue:** The cell dose is listed as "450 x 10^6 CAR-T cells (target dose)." The actual ide-cel target dose ranges from 300-460 x 10^6. 450 is within range but on the high end. Fine.
- Free light chain response from 285 to 45 at day 14 (84% reduction) is optimistic but possible with very rapid myeloma kill.

### Case 4 (Robert Kim -- HLH transition): **Excellent teaching case. Clinically realistic.**
- The ferritin velocity (480 -> 920 -> 4500 -> 12,800) is the key diagnostic feature and is well-modeled.
- Fibrinogen dropping from 3.6 to 1.2 is realistic for HLH.
- **Issue:** The day 5 ferritin of 12,800 with AST 185 would typically have an even higher LDH than 920. LDH >1000 would be more expected at this severity. Minor point.
- HScore 212 with hemophagocytosis confirmed is appropriate.
- The case correctly shows CRS-refractory features (tocilizumab did not help) before the HLH diagnosis.

### Case 5 (Sarah Thompson -- ICANS dominant): **Clinically realistic and important.**
- The dissociation between CRS severity and ICANS severity is well-demonstrated.
- Age 71 as a risk factor for ICANS is correct.
- ICE score trajectory (10 -> 10 -> 7 -> 3 -> 8) is realistic.
- **Issue:** CRS Grade 1 at temp exactly 38.0C (Day 3). This is technically borderline -- 38.0C is the threshold. In practice, a single reading of exactly 38.0 might not be called CRS Grade 1 without a sustained or repeat fever. Minor quibble.

### Case 6 (David Okafor -- Late CRS with cilta-cel): **Clinically realistic and critically important.**
- Late-onset CRS at Day 10 with cilta-cel is well-documented in the literature.
- The "silent" first week followed by sudden onset is the exact clinical trap this case teaches.
- **Issue:** Cilta-cel dose listed as "0.75 x 10^6 CAR-T cells/kg." The approved dose is 0.5-1.0 x 10^6/kg. 0.75 is within range. Fine.
- The case correctly notes ANC is recovered when late CRS starts (unlike early CRS overlapping with conditioning neutropenia). This is a subtle but clinically important observation.

### Case 7 (Linda Park -- Prolonged cytopenias): **Clinically realistic and underrepresented in teaching.**
- Post-auto-SCT marrow reserve depletion leading to prolonged cytopenias is a real clinical problem.
- The biphasic cytopenia pattern (initial nadir, brief partial recovery, then sustained secondary suppression) is accurately described.
- Reticulocyte trajectory and MPV as early recovery markers -- good detail.
- **Issue:** CAR-HEMATOTOX score of 4 -- see my note above about whether the 0-4 range matches the published model.
- Day 28 counts defining "prolonged cytopenias" is correct terminology.

### Case 8 (Michael Santos -- Optimal outcome): **Clinically realistic.**
- All lab values and trajectories are physiologically plausible.
- **Issue:** Day 2 temperature of 37.8C is called "CRS Grade 1" (crs_grade: 1). Per ASTCT, CRS Grade 1 requires T >= 38.0C. At 37.8C, this should technically be Grade 0, not Grade 1. The clinical note even acknowledges this ambiguity but the data field says Grade 1. **This is incorrect.**

---

## 5. Missing Features

### Critical Clinical Data Not Shown

1. **Tocilizumab dose tracking:** How many doses given, timing between doses, cumulative exposure. The ASTCT guidelines limit to 3 doses in 24 hours. Without tracking, dose-limiting could be missed.

2. **Vasopressor status:** What agent, what dose, what trend. The difference between Grade 2 and Grade 3 CRS hinges on vasopressor use. The dashboard has no vasopressor tracking.

3. **O2 requirement detail:** "4L nasal cannula" vs "HFNC 40L/60%" are shown in clinical notes but not in a structured, trendable field. Oxygen escalation/de-escalation is a key CRS severity indicator.

4. **CAR-T expansion kinetics:** Flow cytometry CAR-T cell counts at serial timepoints. This data directly informs whether the therapy is working and correlates with toxicity timing. Some cases mention it in notes but it is not a structured data field.

5. **Cytokine levels over time:** IL-6 is available as a single timepoint value, but there is no trending visualization. The trajectory of IL-6 (and ideally IFN-gamma, TNF-alpha) over time is more informative than any single value.

6. **Steroid cumulative dose:** Total steroid exposure affects CAR-T efficacy. Tracking dexamethasone-equivalent cumulative dosing is essential for the risk-benefit discussion with patients.

7. **Fluid balance / Urine output:** For patients with CRS-related capillary leak and AKI, fluid balance is critical ICU data. Not represented.

8. **Concurrent medications:** Antibiotic status, antifungal/antiviral prophylaxis, growth factor administration, transfusion history -- none of these are structured in the dashboard.

9. **Weight trend:** Patients in Grade 3-4 CRS gain significant weight from capillary leak / fluid resuscitation. Daily weights are standard monitoring.

10. **ECOG Performance Status trend:** Only shown at baseline. ECOG changes during hospitalization are relevant for discharge planning and prognosis.

---

## 6. Risk Scoring Presentation

### EASIX

- **Presentation:** Clean score card with numeric value, risk level, and color coding. Works well visually.
- **Issue:** No explanation of what the score means or how it maps to outcomes. A clinician unfamiliar with EASIX would see "EASIX: 11.4" and have no context. Need to show: "EASIX >3.2 pre-infusion predicts higher risk of Grade 3+ CRS" (or whatever threshold the system uses).
- **Issue:** Serial EASIX (post-infusion) has limited validation compared to pre-infusion EASIX. The dashboard does not distinguish between the two contexts.

### HScore

- **Presentation:** Large score display with color-coded thresholds (>169 high, >100 intermediate, <100 low). **Appropriate thresholds.**
- **Issue:** The probability estimate display ("HLH Probability: X%") is good but should clarify this is derived from the original Fardet validation cohort and may differ in the CAR-T population where IEC-HS has overlapping but distinct features.
- **The HScore was validated for reactive HLH, not specifically for IEC-HS.** The dashboard should note this distinction.

### CAR-HEMATOTOX

- **Presentation:** Score card with >=3 as high-risk threshold.
- **Major issue (reiterated):** The published CAR-HEMATOTOX uses a 0-2 scale per component with a composite threshold. The demo cases show scores of 0-4, and the threshold of >=3 does not match the published model. This must be reconciled with the actual implementation. If the system uses a modified version, this should be clearly stated and cited.
- **Missing:** The expected timeline for count recovery based on the score. The original publication provides median time to ANC and platelet recovery by risk group. This information would be highly actionable.

### Composite Risk Score

- The composite risk meter (0-100% scale) is visually clear but clinically opaque. How is this composite calculated? What weights are given to each component model? In clinical practice, I would not act on a "62.4% composite score" without understanding the methodology. **The dashboard needs a transparency layer showing how the composite is derived.**

---

## 7. Top 5 Improvements (Prioritized)

### 1. Fix CAR-HEMATOTOX Scoring and Threshold Validation (PATIENT SAFETY -- URGENT)

The CAR-HEMATOTOX score range and cutpoints appear inconsistent with the published model. If the threshold is wrong, patients could be inappropriately risk-stratified. This must be verified against Rejeski et al. Blood 2021 and corrected. Display the actual component-level breakdown with the published scoring criteria visible to the clinician.

### 2. Add Intervention Tracking (Tocilizumab Doses, Steroids, Vasopressors, O2)

Without tracking what has already been given and when, the dashboard is an assessment tool but not a management tool. A clinician cannot safely dose tocilizumab without knowing how many prior doses were given. Add structured fields for:
- Tocilizumab: number of doses, timing of each, cumulative mg
- Steroids: current regimen, dexamethasone-equivalent cumulative dose
- Vasopressors: agent(s), dose(s), duration
- Oxygen: current modality and settings

### 3. Add Longitudinal Lab Trending Visualization

Static sparkline bars showing a single value are inadequate. Implement actual trend charts (even simple SVG line charts) showing CRP, ferritin, LDH, IL-6, ANC, platelets, and hemoglobin across all timepoints for a patient. The velocity of change (rate of rise of ferritin, rate of fall of fibrinogen) is often more informative than the absolute value. This is how I actually make clinical decisions -- by looking at trajectories, not snapshots.

### 4. Add Infection vs. CRS Differential Support

Every fever requires dual evaluation. Add a structured section that prompts the clinician through the infection workup checklist: blood cultures (results/timing), urine culture, chest imaging, procalcitonin, and antibiotic status. The current dashboard implicitly assumes every fever is CRS until proven otherwise, which is a dangerous assumption in a neutropenic, immunosuppressed population.

### 5. Add Transparency to Composite Risk Score

Display how the composite score is calculated: which models contributed, what weights were applied, and what the individual model agreement/disagreement pattern is. If 4/5 models say low risk and 1 says high risk, the composite might show "moderate" -- but the clinical interpretation is very different from 3 models saying moderate. Model agreement/disagreement is itself a signal that should be surfaced.

---

## Additional Recommendations (Beyond Top 5)

- **Fix Case 8 CRS grading:** Temperature 37.8C should not be coded as CRS Grade 1.
- **Add ALT to NORMAL_RANGES in the dashboard code.** ALT is in the demo data but missing from the `NORMAL_RANGES` object used for flagging, so abnormal ALTs will not be highlighted.
- **Add respiratory rate to alert generation.** Tachypnea (RR > 22) is an early sign of decompensation that precedes SpO2 changes.
- **Include SOFA score or qSOFA** for ICU-level patients to standardize severity assessment.
- **Make the ICE score calculator bidirectional.** Currently, the ICE calculator is manual-only. When viewing a demo case with an ICE score of 3, the calculator dropdowns should auto-populate to show which components were impaired.
- **Add printing/PDF export of a clinical summary** that includes patient demographics, current scores, active interventions, and recommended next steps -- formatted for handoff communication (SBAR format).
- **Product-specific monitoring protocols.** The monitoring duration and expected toxicity profile differ significantly between products (axi-cel vs. tisa-cel vs. liso-cel vs. ide-cel vs. cilta-cel). The dashboard should adjust monitoring recommendations based on the selected product.

---

## Summary Assessment

**Overall Grade: B-**

The dashboard demonstrates strong foundational clinical knowledge and covers the core toxicity syndromes well. The demo cases are clinically realistic and represent an excellent teaching set covering the major scenarios a cell therapy physician encounters. The CRS grading, HScore thresholds, and management algorithms are largely correct.

However, the platform currently functions more as a **risk assessment and teaching tool** than a **clinical management tool.** The absence of intervention tracking, longitudinal trending, and infection differential support means it cannot replace the clinical workflows it aims to support. A clinician would use this alongside their existing tools, not instead of them.

The CAR-HEMATOTOX scoring discrepancy is the most concerning finding and should be addressed before any clinical deployment. Score-based decision support must be accurate, or it undermines trust in the entire platform.

The demo cases are a genuine strength -- they are diverse, clinically plausible, and cover important edge cases (late CRS, isolated ICANS, HLH transition, prolonged cytopenias). The teaching points are accurate and would be valuable for fellows and advanced practice providers.

---

*Review completed 2026-02-07. All assessments reflect my clinical experience and current ASTCT/NCCN guidelines. This review is for development purposes and does not constitute formal clinical validation.*
