# Cell Therapy Safety Platform -- Emergency Medicine Physician Review (Iteration 2)

**Reviewer:** Dr. Marcus Rivera, MD, FACEP
**Role:** Medical Director, Cell Therapy Acute Response Team; Emergency Medicine Faculty
**Experience:** >200 CRS/ICANS cases managed in ED and step-down units
**Date:** 2026-02-07
**Files Reviewed:**
- `src/api/static/index.html` (2154 lines -- full dashboard UI)
- `src/api/static/demo_cases.js` (2428 lines -- 8 demo clinical cases)
- `src/api/app.py` (full FastAPI backend)

---

## Executive Summary

This platform shows significant clinical maturity in its understanding of cell therapy toxicities. The 8 demo cases are well-constructed and represent realistic clinical trajectories that I have personally encountered. The scoring models (EASIX, HScore, CAR-HEMATOTOX, Teachey, Hay) are correctly referenced and the ASTCT consensus grading is properly implemented. However, there are several findings that range from patient-safety concerns to workflow inefficiencies that would prevent me from deploying this in a live clinical environment without modification.

**Critical count:** 4 P0 findings, 7 P1 findings, 9 P2 findings, 6 P3 findings

---

## P0 -- Patient Safety (Must Fix Before Clinical Use)

### P0-1: No Tocilizumab Dosing Prompt or Weight-Based Calculator

**Location:** `index.html`, lines 1222-1238 (CRS Management Algorithm)

The CRS management algorithm states "Tocilizumab 8mg/kg IV (max 800mg)" as text but provides no dosing calculator. In my experience, dosing errors with tocilizumab are among the most common medication errors in CRS management. At 2am with a decompensating patient, a covering resident needs to see:

- **Patient weight** (displayed prominently)
- **Calculated dose** (weight x 8mg/kg)
- **Max dose cap** (800mg)
- **Repeat dose eligibility** (max 3 doses in 24 hours, no more than 4 total per REMS)
- **Time since last dose** (if re-dosing)

The current static text blocks are informational but not actionable in a dosing emergency. The patient weight is available in the demo case data (`weight_kg`) but is not used anywhere in the CRS management view to calculate a dose.

**Risk:** Dosing error (overdose or underdose) in a time-critical scenario.

**Recommendation:** Add a prominent, auto-calculated tocilizumab dose card at the top of the CRS view that reads the patient's weight, computes 8mg/kg, caps at 800mg, and displays it in large font with a timestamp for when it was last given.

---

### P0-2: CRS Grade 2 Hypotension Threshold is Missing from Vital Sign Alerts

**Location:** `index.html`, lines 1989-2033 (`generateAlerts` function)

The alert logic fires on `systolic_bp < 90` (line 2017), but ASTCT Grade 2 CRS is defined as hypotension "not requiring vasopressors." The problem is clinical: many patients develop CRS-related hypotension with SBP in the 90-100 range that is still clinically significant and warrants fluid resuscitation and close monitoring. The current threshold at SBP < 90 will miss the critical window where a patient is transitioning from Grade 1 to Grade 2.

Additionally, there is **no MAP (Mean Arterial Pressure) calculation anywhere in the dashboard**. MAP < 65 is the universally accepted ICU threshold for clinically significant hypotension and is a far more reliable indicator than SBP alone, particularly in CRS where diastolic pressure often drops first.

**Current behavior:** A patient with BP 92/48 (MAP = 63) generates no alert despite having a MAP below the critical threshold.

**Risk:** Delayed recognition of hemodynamic compromise. Missed Grade 2 CRS escalation.

**Recommendation:**
1. Calculate and display MAP = (SBP + 2*DBP) / 3 for every vital sign set.
2. Alert on MAP < 65 as a danger alert.
3. Alert on SBP < 100 in the context of fever (temperature >= 38.0C) as a warning, since this suggests evolving CRS-related vasodilation.
4. Calculate and display Shock Index (HR/SBP). SI > 0.9 should generate a warning; SI > 1.2 should generate a danger alert. Shock Index is more sensitive than SBP alone for detecting early hemodynamic instability, and it is trivial to calculate from available data.

---

### P0-3: ICE Score Calculator Does Not Pre-populate from Patient Data

**Location:** `index.html`, lines 1354-1448 (ICANS view, `renderICANS` function)

The ICE score calculator always defaults to maximum values (all dropdowns default to the highest option). This means a user who opens the ICANS tab for a patient with ICE score = 3 (Grade 3 ICANS, from the clinical data) will see a calculator defaulting to ICE = 10 (normal). The actual ICE score from the patient's timepoint data (`tp.clinical.ice_score`) is available but is **never displayed prominently** on the ICANS assessment view.

For a patient actively deteriorating neurologically, the most important number on the screen should be their current ICE score and ICANS grade, displayed in large font at the top, not buried in a calculator that resets to normal values.

**Risk:** False reassurance. A clinician opening this view at 2am sees "10/10 Normal" by default and may not realize the patient's actual ICE score has dropped. This could delay steroid initiation for ICANS.

**Recommendation:**
1. Display the patient's current ICE score and ICANS grade at the top of the ICANS view in large font with color coding (green = 10, yellow = 7-9, orange = 3-6, red = 0-2).
2. Pre-populate the calculator dropdowns with values that would produce the patient's recorded ICE score, or clearly label the calculator as "NEW Assessment" to distinguish it from stored data.
3. Show a delta from the last ICE score (e.g., "ICE 5/10, down from 8/10 at last assessment") to highlight the trajectory.

---

### P0-4: ICANS Without CRS is Not Explicitly Flagged

**Location:** `index.html`, lines 1354-1448 (ICANS view); lines 1989-2033 (alert generation)

The demo Case 5 (Sarah Thompson) perfectly illustrates ICANS developing after CRS resolution -- a scenario that requires different management (dexamethasone, not tocilizumab, since tocilizumab does not cross the blood-brain barrier effectively). However, the dashboard has **no automated alert** for the specific condition of "ICANS present with CRS grade 0."

This is a clinical trap I have seen catch residents repeatedly. They see ICANS, think "this is part of CRS," and reach for tocilizumab first. The dashboard should explicitly flag: "ICANS detected WITHOUT active CRS. Tocilizumab is NOT first-line for isolated ICANS. Dexamethasone is the recommended initial therapy."

The data to detect this is already present: `tp.clinical.icans_grade > 0 && tp.clinical.crs_grade === 0`.

**Risk:** Inappropriate treatment selection (tocilizumab instead of dexamethasone for isolated ICANS), potentially delaying effective therapy for neurotoxicity.

**Recommendation:** Add an alert in `generateAlerts()` that fires when ICANS grade > 0 and CRS grade = 0, with explicit text stating dexamethasone is first-line and tocilizumab has poor CNS penetration.

---

## P1 -- Critical Workflow Issues

### P1-1: No Temperature Trend Velocity / Rate-of-Rise Calculation

**Location:** `index.html`, lines 799-828 (trend direction logic); demo case data

The trend logic (`getTrendDirection`) uses a simple percent change between the last two values. For temperature, this is clinically inadequate. What matters in CRS is the **velocity** of temperature rise. A patient whose temperature goes from 37.0 to 38.5 in 4 hours is a very different clinical picture from one whose temperature drifts from 37.0 to 38.5 over 24 hours.

The current implementation treats these identically because it only compares the last two timepoint values without accounting for the time interval between them.

**What I want to see:** Temperature rise rate in degrees per hour (dT/dt). A rise of >0.5C/hour should flag as "rapid escalation" and correlate with more severe CRS trajectories.

**Recommendation:** Calculate time-normalized rate of change for temperature (and ideally CRP and ferritin as well). Display as "Temp +1.2C over 6h" rather than just an up-arrow.

---

### P1-2: CRS Grade Selection Does Not Trigger Management Protocol Highlight Correctly

**Location:** `index.html`, lines 1909-1922 (`selectCRSGrade` function)

The CRS grade selector uses `data-crs-mgmt` attributes to highlight the matching management protocol when a grade is clicked. However, the management algorithm blocks (lines 1224-1237) do not actually have `data-crs-mgmt` attributes set on them. The selector function queries for `[data-crs-mgmt]` elements but finds none, so clicking a CRS grade box does nothing beyond visual selection of the grade box itself.

This means the connection between "I've assessed Grade 3 CRS" and "here is what I should do for Grade 3 CRS" is broken. The clinician must manually scan the management text blocks to find the matching grade.

**Recommendation:** Add `data-crs-mgmt="1"`, `data-crs-mgmt="2"`, etc. to each management protocol block so the grade selector actually highlights the corresponding treatment algorithm.

---

### P1-3: No Vasopressor Status Tracking or Oxygen Requirement Display

**Location:** Throughout the CRS and Overview views

The demo case data contains `oxygen_requirement` strings (e.g., "4L nasal cannula", "High-flow nasal cannula 40L/min 60% FiO2") but this information is **never rendered anywhere in the dashboard**. Oxygen requirement is a core criterion for CRS grading per ASTCT:

- Grade 2: low-flow nasal cannula (<=6L)
- Grade 3: high-flow nasal cannula or non-rebreather
- Grade 4: positive pressure ventilation (CPAP/BiPAP/ventilator)

Similarly, vasopressor status is not captured or displayed anywhere. The discharge criteria reference "No vasopressor requirement" (line 1615) but this is a hardcoded `true` value, not derived from actual data.

**Recommendation:**
1. Display oxygen requirement prominently in the CRS view and Overview, next to vital signs.
2. Add vasopressor status (none / single agent / multiple agents) as a tracked clinical data point.
3. These two parameters, combined with temperature, are the complete set needed for ASTCT CRS grading. All three should be visible in a single glance.

---

### P1-4: HScore 169 Threshold Alert Only Fires on Ferritin > 10,000, Not on HScore Itself

**Location:** `index.html`, lines 2004-2009 (alert generation for HLH)

The alert logic fires on `labs.ferritin > 10000` and `labs.fibrinogen < 1.5` individually, but there is no alert that fires when the **actual computed HScore exceeds 169** (the threshold for >93% HLH probability). This is significant because HScore can exceed 169 even when ferritin is below 10,000 -- for example, a patient with ferritin 5000, fibrinogen 1.2, triglycerides 4.0, 3 cytopenias, and hemophagocytosis can score well above 169.

The HScore result is available in `pred.individual_scores` and its value is checked in the HLH view display (line 1486), but it is never used to generate a dashboard-level alert.

**Recommendation:** Add an alert in `generateAlerts()` that checks the HScore from the prediction result. If HScore >= 169, fire a danger alert: "HScore [score] exceeds 169 (>93% HLH probability). Evaluate for IEC-HS. Consider pulse methylprednisolone."

---

### P1-5: No Biphasic CRS Warning or Recurrence Detection

**Location:** Alert generation and trend logic

In my experience, approximately 10-15% of CRS cases show a biphasic pattern: initial CRS resolves, then recurs 2-4 days later, often more severely than the first episode. The dashboard has no mechanism to detect or warn about this pattern.

The data model supports it -- a patient could have CRS grade 2 at day 3, grade 0 at day 5, then grade 3 at day 7. But the trend logic only looks at the last two timepoints and would simply show "worsening" without flagging the clinically distinct pattern of recurrence after resolution.

**Recommendation:** When CRS grade transitions from >0 to 0 and then back to >0 across timepoints, generate a specific alert: "Biphasic CRS pattern detected. Second CRS episode after initial resolution. Consider more aggressive management -- biphasic CRS is often more severe on recurrence."

---

### P1-6: Print View Strips Critical Information

**Location:** `index.html`, lines 341-357 (print CSS)

The print CSS hides the entire patient sidebar (`display: none !important`), which means the printed clinical summary loses:
- Patient demographics and ID
- Diagnosis and product information
- Timepoint context

While there is a `print-header` div (lines 500-503) that provides some of this, it only contains basic identifiers. A printed clinical summary used for transfer documentation or SBAR handoff needs:
- Complete patient demographics (age, sex, weight, BSA)
- Diagnosis and stage
- CAR-T product and dose
- Infusion date and current day post-infusion
- All current vital signs
- CRS and ICANS grade
- Current medications (not tracked)
- Oxygen requirement (not displayed)

**Recommendation:** Expand the print header to include a structured clinical summary block with all transfer-critical information. Consider a dedicated "Generate Transfer Summary" button that produces an SBAR-formatted document.

---

### P1-7: ALT Normal Range is Incorrect

**Location:** `index.html`, line 537

```javascript
alt: { low: 0, high: 33, unit: 'U/L', name: 'ALT' },
```

The dashboard uses an ALT upper limit of normal (ULN) of 33 U/L. However, the demo_cases.js file header (line 16) states `ALT: 7-56 U/L` as the reference range. The standard laboratory ULN for ALT is typically 35-56 U/L depending on the assay. Using 33 as ULN will cause excessive false-positive flagging.

More critically, the alert at line 2029 fires on `labs.alt > 165`, which is described as ">5x ULN." If ULN = 33, then 5x = 165. But if the intended ULN is 56 (as stated in the demo cases header), then 5x = 280, and the alert fires too early. Conversely, using the standard ULN of 40 gives 5x = 200.

**Risk:** Either false-positive ALT alerts (if ULN is truly 33) or a mismatched threshold for the hepatotoxicity alert.

**Recommendation:** Standardize ALT ULN to a single value consistently across the codebase. For CAR-T patients, the commonly used ULN for ALT is 40 U/L (male) or 33 U/L (female). Consider sex-specific ranges or use a consensus value and document it. Update the 5x ULN alert accordingly.

---

## P2 -- Important Clinical Improvements

### P2-1: No Lactate or Procalcitonin in Lab Panel

The lab panel includes the biomarker scoring inputs (LDH, creatinine, platelets, CRP, ferritin, etc.) but is missing two labs that I order on every CRS patient:

1. **Lactate**: Essential for differentiating distributive shock (CRS-related vasodilation) from other shock etiologies. Lactate > 4 in CRS suggests severe tissue hypoperfusion and supports ICU transfer.
2. **Procalcitonin**: Helps differentiate CRS (typically low PCT) from bacterial sepsis (typically elevated PCT). This is a critical distinction since CRS and sepsis can present identically (fever, hypotension, tachycardia).

**Recommendation:** Add lactate and procalcitonin to the lab panel with appropriate normal ranges and clinical context notes.

---

### P2-2: No Dexamethasone Dose Tracking or Steroid Taper Protocol

The ICANS management section (lines 1432-1445) recommends dexamethasone 10mg IV q6h for Grade 2-3 ICANS and methylprednisolone 1g IV for Grade 4. But there is no mechanism to:
- Record when steroids were started
- Track cumulative steroid dose
- Display a taper schedule
- Flag when steroids need to be tapered (prolonged steroids can ablate CAR-T cells and compromise efficacy)

The demo case 4 (Robert Kim) teaching point explicitly notes: "Steroids for IEC-HS may compromise CAR-T efficacy." This clinical tension needs to be visible in the dashboard.

**Recommendation:** Add a steroid tracking module or at minimum a taper protocol reference that can be activated when steroids are initiated.

---

### P2-3: Seizure Risk Factors Not Visible in ICANS View

The ICANS view has an excellent ICE score calculator and grading table, but does not display seizure risk factors. In the ICANS population, seizure risk is elevated by:
- ICE score < 3 (Grade 3+ ICANS)
- Prior CNS disease
- History of seizures
- Cerebral edema on imaging
- Concurrent electrolyte abnormalities (hyponatremia, hypocalcemia, hypomagnesemia)

The ICANS management protocol recommends seizure prophylaxis with levetiracetam but does not highlight when it should be started or what risk factors are present.

**Recommendation:** Add a "Seizure Risk Assessment" card to the ICANS view that pulls relevant data points and explicitly recommends prophylaxis when risk factors are present.

---

### P2-4: No Fluid Balance / Urine Output Tracking

CRS-related capillary leak syndrome causes third-spacing of fluids, leading to edema, pleural effusions, and potentially pulmonary edema -- especially when aggressive IV fluid resuscitation is given for hypotension. The dashboard has no mechanism to track:
- IV fluid intake
- Urine output
- Net fluid balance
- Weight changes (edema monitoring)

This is particularly important for patients with pre-existing renal impairment (e.g., Case 3, Patricia Rodriguez, with baseline creatinine 1.4).

**Recommendation:** Consider adding at minimum a fluid balance input field and a daily weight trend.

---

### P2-5: Hemoglobin Normal Range is Not Sex-Adjusted

**Location:** `index.html`, line 533

```javascript
hemoglobin: { low: 12.0, high: 17.5, unit: 'g/dL', name: 'Hemoglobin' },
```

A single range of 12.0-17.5 is used for all patients. Standard ranges are 12.0-16.0 for females and 14.0-18.0 for males. Using a combined range means:
- A male with Hb 13.0 (abnormally low for males) will not be flagged
- The boundary is imprecise in either direction

The patient sex is available in the demo case data but is not used for sex-specific lab flagging.

**Recommendation:** Implement sex-specific hemoglobin flagging using the available `sex` field from patient data. Apply the same principle to ferritin if sex-specific ranges are clinically relevant.

---

### P2-6: CRS Grading Does Not Auto-Suggest Based on Available Vitals

The CRS grade strip (lines 1185-1193) is entirely manual -- the clinician clicks a grade. But the dashboard already has the three data elements needed for automated CRS grading:
- Temperature (fever >= 38.0C)
- Blood pressure / vasopressor status
- SpO2 / oxygen requirement

The system could at minimum **suggest** a CRS grade based on available data and ask the clinician to confirm. This would reduce grading errors, especially for covering residents unfamiliar with ASTCT criteria.

**Recommendation:** Add an "Auto-assess CRS Grade" function that evaluates available vitals and clinical data, pre-selects the suggested grade on the strip, and requires clinician confirmation. Clearly label it as "Suggested" versus "Confirmed."

---

### P2-7: No Time-Since-Infusion Calculation or Display

The infusion date is stored in patient data (`infusion_date`) and each timepoint has a `day` field, but the dashboard does not calculate or display the actual hours or days since infusion in a prominent location. This is important because:
- CRS timing varies by product (axi-cel: day 1-3 onset; tisa-cel: day 3-5; cilta-cel: day 7-12+)
- ICANS typically peaks days 5-8
- Late-onset CRS after day 10 suggests specific product-related kinetics

Knowing "this patient is day 10 post-cilta-cel" versus "day 3 post-axi-cel" fundamentally changes the clinical interpretation of the same vital sign set.

**Recommendation:** Display "Day X Post-Infusion" prominently in the header or top of each view, ideally with a product-specific expected toxicity timeline.

---

### P2-8: The Composite Score is Confusing and Potentially Misleading

**Location:** `index.html`, lines 947-971 (composite risk display); `app.py`, lines 360-411 (composite score calculation)

The composite score is described as a "weighted score, not a probability" (line 967), which is correct and appreciated. However, the visual representation (a risk meter from Low to High with a position indicator) strongly implies a probability or percentage to clinicians. The composite index is displayed as a percentage (e.g., "Composite index: 42.3") which further reinforces the probability interpretation.

The underlying calculation (confidence-weighted average of log-transformed EASIX, linear-scaled HScore, and linear-scaled CAR-HEMATOTOX) mixes fundamentally different clinical constructs:
- EASIX: endothelial activation (CRS predictor)
- HScore: HLH probability
- CAR-HEMATOTOX: cytopenia risk

Averaging these into a single number loses the clinical distinction between these different risk domains. A patient with high HScore but low EASIX is at risk for HLH, not CRS -- but the composite score does not convey this distinction.

**Recommendation:** Consider replacing the single composite score with a multi-axis risk display that shows each domain separately (CRS risk, ICANS risk, HLH risk, Cytopenia risk). If a single composite is retained, add a prominent disclaimer and consider renaming from "Composite Risk Assessment" to "Monitoring Priority Index" to avoid clinical misinterpretation.

---

### P2-9: Demo Case Data Includes "critical" Risk Level Not Handled by UI

**Location:** `demo_cases.js`, line 1075 (`expected_risk: "critical"` for Robert Kim Day 5)

The demo case for the IEC-HS case uses an `expected_risk` value of "critical" which is not handled by the `riskClass()` function (line 607-614). It falls through to `risk-unknown` (blue/info styling), which would display a blue badge for a patient who is actively dying from HLH-like syndrome. This is dangerous: a blue "UNKNOWN" badge on the most critically ill patient in the case series.

**Recommendation:** Add a "critical" risk level that maps to the most visually alarming styling (pulsing red border, bold text, etc.), or map it to "high" if a separate critical tier is not desired.

---

## P3 -- Nice-to-Have Improvements

### P3-1: SBAR-Formatted Handoff Template

The dashboard contains all the data elements needed for a structured SBAR (Situation, Background, Assessment, Recommendation) handoff, but does not provide a dedicated handoff view. An "SBAR Handoff" button that generates a text-formatted handoff note from the current patient state would be extremely valuable for:
- ED-to-ICU transfers
- Nursing shift changes
- Provider sign-out
- Transfer to outside hospitals

### P3-2: Tocilizumab Repeat Dose Timer

After administering tocilizumab, the earliest a repeat dose should be given is typically 8 hours. A visible countdown timer showing "Next tocilizumab eligible in: X hours" would prevent premature re-dosing and reduce the need to check the medication administration record.

### P3-3: Product-Specific CRS Timing Expectations

Different CAR-T products have different CRS onset kinetics. The dashboard should display product-specific expected windows:
- Axi-cel: median onset day 2, peak day 3-5
- Tisa-cel: median onset day 3, peak day 5-7
- Liso-cel: median onset day 5, peak day 5-9
- Ide-cel: median onset day 1, peak day 2-4
- Cilta-cel: median onset day 7, can be day 12+

This context helps clinicians calibrate their concern level. A fever on day 10 is expected for cilta-cel but alarming for axi-cel.

### P3-4: Levetiracetam Dosing Reminder for ICANS

The ICANS management section mentions levetiracetam but does not specify when to start prophylaxis. Standard practice is to start at ICANS Grade 2 or higher. A checkbox or prompt "Start seizure prophylaxis: Levetiracetam 750mg PO/IV BID" triggered at Grade 2+ would reduce missed doses.

### P3-5: Dark Mode Contrast for Red/Danger Elements

The dark mode theme (lines 41-61) adjusts background colors but the danger-related elements may have insufficient contrast. In the ED, screens are often viewed in various lighting conditions. Verifying WCAG AA compliance for all alert colors in dark mode would improve accessibility during night shifts.

### P3-6: IL-6 Interpretation Note Post-Tocilizumab

The demo cases correctly note that IL-6 rises paradoxically after tocilizumab administration due to IL-6 receptor blockade. However, the dashboard does not flag this anywhere in the lab display. A clinician unfamiliar with this pharmacodynamic effect might see IL-6 of 2400 (Case 2, Day 3) and panic, not realizing this is expected post-tocilizumab.

**Recommendation:** When IL-6 is markedly elevated, add a contextual note: "If tocilizumab was recently administered, IL-6 elevation is expected and does not indicate CRS worsening. Assess clinical status, not IL-6 alone."

---

## What Would Make Me NOT Trust This Tool

1. **The composite score averaging heterogeneous risk domains.** If I see a patient with a "moderate" composite score but their HScore is 180, I need the HLH signal to dominate the display, not be diluted by averaging with a normal EASIX.

2. **The ICE calculator defaulting to 10/10.** Any resident who opens the ICANS tab and sees "10/10" may be falsely reassured and move on. The patient's actual ICE score should be unmissable.

3. **The "critical" risk level rendering as blue/unknown.** If the sickest patient in the system shows a blue badge, I cannot trust the visual severity indicators.

4. **No MAP calculation.** I have been trained to think in MAP, not SBP alone. A system that does not show MAP feels incomplete to me for hemodynamic assessment.

5. **No automated alert on HScore > 169.** This is a well-validated threshold with > 93% HLH probability. If the system computes HScore and does not alert on this threshold, it is failing at its core decision-support function.

---

## What This Tool Does Well

1. **ASTCT CRS grading criteria are correctly stated** (lines 541-547). The grade definitions match the consensus. The inclusion of all 5 grades (0-4) with specific organ criteria is accurate.

2. **The HScore component breakdown table** in the HLH view (lines 1492-1504) is excellent. Seeing each variable's contribution to the total score helps clinicians understand what is driving the HLH probability and what interventions might alter the trajectory.

3. **The teaching points system** is outstanding. The teaching points in the demo cases are clinically accurate, well-referenced, and cover nuanced management decisions (e.g., the steroids-vs-efficacy tension in IEC-HS, the biphasic cytopenia pattern). This would be valuable for fellow and resident education.

4. **The 8 demo cases are clinically realistic** and cover the spectrum of CAR-T toxicities well: straightforward CRS (Cases 1, 8), severe CRS (Case 2), product-specific patterns (Cases 3, 6), HLH overlap (Case 4), isolated ICANS (Case 5), prolonged cytopenias (Case 7), and late-onset CRS (Case 6).

5. **The CRS-vs-IEC-HS differential table** (lines 1512-1524) is a useful clinical reference that I have not seen in other dashboards.

6. **Real-time sparkline trends** for labs are well-designed and provide at-a-glance trajectory information. The color coding of abnormal values and the normal range band in the SVG are visually effective.

7. **The pre-infusion checklist** (lines 1118-1127) covers the essential safety checks. Tocilizumab availability verification is correctly listed.

8. **The anticipated tests generator** (lines 2043-2078) appropriately escalates monitoring frequency based on CRS severity and risk level. The conditional logic for ordering blood cultures with fever is correct.

---

## Summary Prioritization Table

| ID | Priority | Finding | Category |
|----|----------|---------|----------|
| P0-1 | P0 | No tocilizumab dosing calculator | Medication safety |
| P0-2 | P0 | Missing MAP calculation, hypotension threshold too low | Hemodynamic assessment |
| P0-3 | P0 | ICE score not displayed from patient data, defaults to 10 | Neuro assessment |
| P0-4 | P0 | ICANS without CRS not flagged | Treatment decision |
| P1-1 | P1 | No temperature trend velocity | CRS escalation |
| P1-2 | P1 | CRS grade selection does not highlight management protocol | Workflow |
| P1-3 | P1 | O2 requirement and vasopressor status not displayed | CRS grading |
| P1-4 | P1 | HScore > 169 does not generate alert | HLH detection |
| P1-5 | P1 | No biphasic CRS recurrence detection | CRS pattern recognition |
| P1-6 | P1 | Print view loses critical clinical information | Transfer documentation |
| P1-7 | P1 | ALT normal range inconsistency | Lab accuracy |
| P2-1 | P2 | No lactate or procalcitonin | Differential diagnosis |
| P2-2 | P2 | No steroid tracking or taper protocol | Medication management |
| P2-3 | P2 | Seizure risk factors not displayed | ICANS safety |
| P2-4 | P2 | No fluid balance tracking | Volume management |
| P2-5 | P2 | Hemoglobin not sex-adjusted | Lab accuracy |
| P2-6 | P2 | CRS grade not auto-suggested from vitals | Workflow efficiency |
| P2-7 | P2 | No day-post-infusion display | Clinical context |
| P2-8 | P2 | Composite score mixes unrelated risk domains | Clinical interpretation |
| P2-9 | P2 | "critical" risk level not handled in UI | Visual safety |
| P3-1 | P3 | No SBAR handoff template | Communication |
| P3-2 | P3 | No tocilizumab repeat dose timer | Medication safety |
| P3-3 | P3 | No product-specific CRS timing reference | Clinical context |
| P3-4 | P3 | No levetiracetam dosing prompt at Grade 2 ICANS | Medication safety |
| P3-5 | P3 | Dark mode contrast verification needed | Accessibility |
| P3-6 | P3 | No IL-6 interpretation note post-tocilizumab | Lab interpretation |

---

*Reviewed as part of the Cell Therapy Safety Platform clinical validation process. This review reflects the clinical judgment of an emergency medicine physician experienced in CAR-T toxicity management and does not constitute regulatory guidance.*
