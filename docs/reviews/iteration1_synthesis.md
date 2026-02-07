# Iteration 1 Synthesis: Prioritized Improvement Plan

**Date:** 2026-02-07
**Source Reviews:**
- Oncologist (Dr. Sarah Nguyen, MD) -- Clinical accuracy & workflow
- ICU Nurse (Jessica Martinez, RN) -- Bedside usability & safety
- Pharmacist (Dr. Kevin Park, PharmD) -- Medication safety & REMS
- UX Designer (Alex Rivera) -- Accessibility & interaction design
- Data Scientist (Dr. Rachel Chen, PhD) -- Model transparency & responsible AI

**Overall Grade from Reviewers:** B- (Oncologist), B- (Nurse), Needs Improvement (Pharmacist), 6.5/10 (UX)

---

## 1. Common Themes

These issues were raised independently by **3 or more reviewers**:

### A. No Longitudinal Trend Visualization (Oncologist, Nurse, UX)
All three noted that the dashboard shows single-timepoint snapshots but clinicians make decisions based on trajectories. The oncologist wants sparklines for CRP/ferritin/LDH. The nurse wants rate-of-change alerts. The UX reviewer identified this as the single highest-impact improvement.

### B. Missing Vital Sign Alerts -- Hypotension, SpO2, Tachycardia (Oncologist, Nurse, Pharmacist)
The alert system checks lab values but not vital signs. Hypotension (SBP <90), hypoxia (SpO2 <94%), and tachycardia (HR >120) are CRS grading criteria that generate no alerts. Flagged as a **patient safety gap** by both the nurse and oncologist.

### C. No Intervention/Medication Tracking (Oncologist, Nurse, Pharmacist)
No way to track tocilizumab doses given, steroid regimens, vasopressor status, or oxygen modality. The oncologist, nurse, and pharmacist all independently identified this as critical. The pharmacist specifically flagged missing tocilizumab dose counting (max 3 in 24h, max 4 total).

### D. Missing Respiratory Rate from Clinical Visit Form (Oncologist, Nurse)
Respiratory rate exists in demo data but is absent from the manual entry form. Tachypnea is an early decompensation sign.

### E. Composite Score Misleads as a Probability (Data Scientist, Oncologist)
The composite score displayed as "XX.X%" on a gradient bar implies a calibrated probability but is actually a weighted average of arbitrarily normalized values. Both the data scientist and oncologist flagged this as opaque and potentially misleading.

### F. CAR-HEMATOTOX Scoring Discrepancy (Oncologist, Data Scientist)
The score range (0-4 in demo cases) and threshold (>=3) do not match the published model (0-2 scale, threshold >=2). Flagged as a patient safety concern by the oncologist and a data accuracy issue by the data scientist.

### G. CRS Grade Selection is Non-Functional (Oncologist, Nurse, UX)
Clicking a CRS grade box toggles a CSS class but does not update patient state, trigger management guidance, or persist. The UX reviewer noted it allows multiple simultaneous selections. All three reviewers said this false affordance is confusing.

### H. No Infection vs. CRS Differential Support (Oncologist, Nurse)
Every fever requires dual evaluation for CRS and infection. The dashboard assumes CRS without prompting infection workup (cultures, procalcitonin, antibiotics status).

### I. ALT Missing from NORMAL_RANGES (Oncologist, Pharmacist)
ALT is in demo data but not in the dashboard's `NORMAL_RANGES` object, so abnormal ALT values are not flagged. Both the oncologist and pharmacist noted this -- the pharmacist specifically linked it to tocilizumab hepatotoxicity monitoring.

### J. No Structured Note / Handoff Generation (Nurse, UX)
The nurse wants SBAR handoff generation. The UX reviewer wants a comprehensive print summary. Neither exists.

### K. Checklist State Not Persisted (Nurse, UX)
Pre-infusion and day-1 checklists reset on tab switch. Both the nurse and UX reviewer flagged this as a workflow disruption.

---

## 2. Critical Fixes (Patient Safety / Clinical Accuracy)

These must be fixed before any clinical use:

| # | Issue | Reviewer(s) | Details |
|---|-------|-------------|---------|
| C1 | **Missing vital sign alerts** | Nurse, Oncologist | No alerts for SBP <90, SpO2 <94%, HR >120, RR >24. These define CRS grades. |
| C2 | **CAR-HEMATOTOX score range and threshold wrong** | Oncologist, Data Scientist | Demo shows 0-4 range with >=3 threshold; published model uses 0-2 with >=2 threshold. Patients could be under-triaged. |
| C3 | **Composite score displayed as percentage (implies probability)** | Data Scientist | "72.3%" is not a probability. Must relabel or replace with ordinal risk summary. |
| C4 | **Case 8 CRS grading error** | Oncologist | Temp 37.8C coded as CRS Grade 1; ASTCT requires >=38.0C. Should be Grade 0. |
| C5 | **Demo case pre-computed scores are wrong** | Data Scientist | EASIX, HScore, CAR-HEMATOTOX scores in demo_cases.js do not match formulas applied to the lab values. |
| C6 | **CRS grade selector allows multiple selections** | UX | A patient can only have one CRS grade. Must be exclusive (radio behavior). |
| C7 | **"AI-powered" label is misleading** | Data Scientist | These are deterministic formulas, not ML models. Remove "AI-powered" from descriptions. |

---

## 3. High-Impact Improvements

Significant usability or clinical value improvements:

| # | Issue | Reviewer(s) | Details |
|---|-------|-------------|---------|
| H1 | **Add trend visualization across timepoints** | Oncologist, Nurse, UX | SVG line charts for CRP, ferritin, LDH, IL-6, ANC, platelets across timepoints. Include rate-of-change indicators. |
| H2 | **Add vital sign alerts to `generateAlerts()`** | Nurse, Oncologist | SBP <90 (danger), HR >120 (warning), SpO2 <94% (danger), RR >24 (warning). |
| H3 | **Add respiratory rate to Clinical Visit form** | Nurse, Oncologist | Field exists in demo data but missing from manual entry form. |
| H4 | **Add ALT to NORMAL_RANGES** | Oncologist, Pharmacist | Enable flagging of abnormal ALT. Add tocilizumab-specific threshold at 5x ULN. |
| H5 | **Make CRS grade selection functional and exclusive** | Oncologist, Nurse, UX | Radio behavior, persist selection, highlight matching management protocol, auto-suggest grade from vitals. |
| H6 | **Add tocilizumab dose calculator** | Nurse, Pharmacist | Weight-based calculation (8mg/kg, max 800mg). Display calculated dose in CRS management view. |
| H7 | **Persist checklist and assessment state** | Nurse, UX | Store in localStorage keyed by patient + timepoint. Restore on re-render. |
| H8 | **Show skipped/failed models with reasons** | Data Scientist | Render `models_skipped` from ensemble response. Show what data is missing. |
| H9 | **Replace composite % with risk summary or add caveat** | Data Scientist, Oncologist | Show "3 of 5 models HIGH" or add explicit "not a probability" label. |
| H10 | **Add colorblind-safe secondary indicators** | UX | Icons alongside color-coded risk levels. Critical for 8% of male clinicians. |
| H11 | **Fix keyboard accessibility** | UX | Convert div[onclick] to button elements. Add ARIA roles/labels. Add tabindex. |
| H12 | **Add patient banner to print output** | UX | Name, ID, DOB, risk level, timestamp. Required for clinical documentation. |
| H13 | **Split BP into systolic/diastolic fields** | Nurse | Current single text field is error-prone. |

---

## 4. Nice-to-Haves

Lower priority but valuable improvements:

| # | Issue | Reviewer(s) | Details |
|---|-------|-------------|---------|
| N1 | Structured SBAR handoff generator | Nurse | Auto-generate shift handoff summary from current data |
| N2 | Quick-entry mode with carry-forward | Nurse | "Copy from last assessment" button for Clinical Visit |
| N3 | Alert acknowledgment system | Nurse | Dismiss/acknowledge alerts to reduce alarm fatigue |
| N4 | Alert prioritization/grouping | Nurse | Collapse lower-priority alerts when multiple fire |
| N5 | Antimicrobial prophylaxis protocol display | Pharmacist | Antiviral, antifungal, PJP prophylaxis reference table |
| N6 | Post-tocilizumab IL-6 interpretation warning | Pharmacist | Warn that IL-6 rises paradoxically after tocilizumab |
| N7 | Product-specific REMS checklists | Pharmacist | Replace single checkbox with product-specific REMS panel |
| N8 | Model validation metadata (AUC, cohort, limitations) | Data Scientist | Expandable details per score card |
| N9 | Temporal model applicability annotations | Data Scientist | Gray out models outside their validated timeframe |
| N10 | Steroid taper protocol display | Pharmacist | Standardized step-down schedule |
| N11 | Tab overflow indicators for narrow screens | UX | Fade/arrow buttons when tabs overflow |
| N12 | Loading/error/empty states for API calls | UX | Spinner, explicit errors, retry buttons |
| N13 | Form validation with clinically plausible ranges | UX | Reject temp=50C, platelets=-100, etc. |
| N14 | ICE score auto-calculate on input change | UX | Remove manual Calculate button |
| N15 | Tab badges for active alerts | UX | Red dot on CRS tab when fever detected, etc. |
| N16 | Glucose monitoring in lab panel | Pharmacist | Add for steroid-treated patients |
| N17 | Coagulation panel (PT/INR/PTT) in anticipated tests | Oncologist, Pharmacist | For DIC monitoring |
| N18 | Risk discordance warnings rendered in UI | Data Scientist | Currently buried in API metadata |
| N19 | Infection workup section/checklist | Oncologist, Nurse | Culture results, antibiotic status, procalcitonin |
| N20 | Timestamp field on Clinical Visit entries | Nurse | Currently no way to record assessment time |

---

## 5. Prioritized Task List for Iteration 2

### Task 1: Add vital sign alerts to `generateAlerts()`
- **What:** Add alert generation for SBP <90 (danger), HR >120 (warning), SpO2 <94% (danger), RR >24 (warning) in the `generateAlerts()` function in `index.html`.
- **Why:** Nurse (critical safety gap), Oncologist (missing from alert logic). These vital signs define CRS grades and drive treatment decisions.
- **Expected impact:** Closes the most serious patient safety gap in the system.
- **Complexity:** S

### Task 2: Add respiratory rate to Clinical Visit form
- **What:** Add a respiratory rate input field to the Clinical Visit manual entry form grid in `index.html`. Include it in the form submission data sent to the API.
- **Why:** Nurse (missing from form), Oncologist (tachypnea is early decompensation sign). RR exists in demo data but not in the entry form.
- **Expected impact:** Enables RR-based alerting (Task 1) and more complete clinical assessment.
- **Complexity:** S

### Task 3: Fix CRS grade selector to exclusive radio behavior
- **What:** Change `onclick="this.classList.toggle('selected')"` on CRS grade boxes to exclusive selection (deselect siblings, select clicked). Highlight the corresponding management protocol row. Persist selection in localStorage.
- **Why:** UX (allows nonsensical multi-selection), Oncologist (false affordance), Nurse (not functional enough).
- **Expected impact:** Transforms CRS section from decorative to functional clinical tool.
- **Complexity:** S

### Task 4: Fix composite score display -- remove percentage implication
- **What:** Replace `(pred.composite_score * 100).toFixed(1) + '%'` with either (a) a model agreement summary ("3 of 5 models: HIGH") or (b) a clearly labeled unitless score with visible caveat "Not a probability."
- **Why:** Data Scientist (critical -- misleads as calibrated probability), Oncologist (clinically opaque).
- **Expected impact:** Prevents dangerous over-reliance on a number that looks more precise than it is.
- **Complexity:** S

### Task 5: Add ALT to NORMAL_RANGES and fix lab flagging
- **What:** Add `alt: { low: 0, high: 33, unit: 'U/L' }` (or appropriate range) to the `NORMAL_RANGES` object in `index.html`. Ensure ALT values in demo cases are properly flagged in the lab table.
- **Why:** Oncologist (abnormal ALTs not highlighted), Pharmacist (tocilizumab hepatotoxicity monitoring).
- **Expected impact:** Catches hepatotoxicity signals that are currently invisible.
- **Complexity:** S

### Task 6: Add trend visualization (sparkline line charts) across timepoints
- **What:** For key labs (CRP, ferritin, LDH, IL-6, ANC, platelets, hemoglobin, fibrinogen), collect values across all timepoints for the current patient and render SVG polyline mini-charts in the Overview and relevant monitoring tabs. Add directional arrows (up/down/stable) next to current values.
- **Why:** Oncologist (trajectories > snapshots), Nurse (rate-of-change is more informative), UX (single biggest data density gap).
- **Expected impact:** Transforms the dashboard from snapshot viewer to trajectory analyzer -- how clinicians actually make decisions.
- **Complexity:** L

### Task 7: Add tocilizumab weight-based dose calculator
- **What:** In the CRS Management view, when Grade >= 2, calculate and display `8mg/kg x [patient weight] = [dose]mg (max 800mg)` using the patient's `weight_kg`. Add dose tracking fields (dose count, time of last dose).
- **Why:** Nurse (no mental math during a crash), Pharmacist (weight-based dosing needed, max dose enforcement).
- **Expected impact:** Reduces medication dosing errors in time-critical situations.
- **Complexity:** M

### Task 8: Split blood pressure into systolic/diastolic fields
- **What:** Replace the single `visit_bp` text input (placeholder "120/80") with two separate numeric inputs for systolic and diastolic. Parse values for alert generation.
- **Why:** Nurse (error-prone free text). Enables reliable SBP-based alerting from Task 1.
- **Expected impact:** Eliminates BP parsing errors, enables programmatic vital sign alerts.
- **Complexity:** S

### Task 9: Persist checklist state in localStorage
- **What:** On checkbox change in pre-infusion and day-1 checklists, save state to `localStorage` keyed by `patientId-timepoint-taskId`. Restore on re-render. Also persist CRS grade selection and ICE score results.
- **Why:** Nurse (loses work on tab switch), UX (significant workflow disruption).
- **Expected impact:** Prevents frustrating data loss during normal clinical workflow.
- **Complexity:** S

### Task 10: Show skipped/failed models with explanations
- **What:** In the Overview score grid, render models from `models_skipped` with a distinct "Not Evaluated" visual state and list the specific missing inputs (e.g., "Requires IFN-gamma, sgp130 -- not ordered").
- **Why:** Data Scientist (silent model omission is misleading -- "4/7 models" with no explanation).
- **Expected impact:** Clinicians understand what was evaluated and what data gaps exist.
- **Complexity:** M

### Task 11: Add colorblind-safe icons to risk indicators
- **What:** Add icons alongside color-coded risk levels throughout the UI: checkmark/shield for LOW, triangle-exclamation for MODERATE, circle-X or exclamation for HIGH. Add text labels to sparkline bars. Ensure risk meter has labeled tick marks.
- **Why:** UX (8% of male clinicians have red-green color vision deficiency -- patient safety concern).
- **Expected impact:** Makes risk indicators accessible to all clinicians regardless of color vision.
- **Complexity:** M

### Task 12: Add patient identification to print output
- **What:** Add a print-only header block (`@media print`) showing patient name, ID, DOB, current day post-infusion, risk level, and print timestamp. Add `@page` margin rules.
- **Why:** UX (printed documents without patient ID are a Joint Commission violation and patient safety hazard).
- **Expected impact:** Makes printed output clinically usable for charting and handoff.
- **Complexity:** S

### Task 13: Add "Not AI" disclosure and clinical disclaimer
- **What:** Remove "AI-powered" from API description in `app.py`. Add a visible footer or banner to the dashboard: "Scores computed from published clinical formulas. For clinical decision support only -- not a substitute for clinical judgment."
- **Why:** Data Scientist (misleading labeling implies ML authority that does not exist).
- **Expected impact:** Responsible AI compliance. Sets appropriate expectations for clinicians.
- **Complexity:** S

### Task 14: Fix Case 8 CRS grade and validate demo case scores
- **What:** In `demo_cases.js`, change Case 8 Day 2 from `crs_grade: 1` to `crs_grade: 0` (temp 37.8C < 38.0C threshold). Review and either recompute or remove the `scores` objects in all demo cases to match actual formula outputs, or add a comment clarifying they are illustrative.
- **Why:** Oncologist (incorrect CRS grading), Data Scientist (pre-computed scores do not match formulas).
- **Expected impact:** Eliminates clinically incorrect data that could confuse trainees and validators.
- **Complexity:** M

### Task 15: Add keyboard accessibility to interactive elements
- **What:** Convert all `div[onclick]` elements (patient cards, CRS grade boxes, timeline buttons) to `<button>` elements with `role`, `aria-label`, and keyboard event handlers. Add `role="tablist"`/`role="tab"`/`role="tabpanel"` to task navigation. Add `aria-live="polite"` to dynamic content areas.
- **Why:** UX (fails WCAG 2.1 Level A -- keyboard access is a mandatory requirement).
- **Expected impact:** Makes the dashboard usable for clinicians with motor impairments or assistive technology.
- **Complexity:** M

---

## Summary by Complexity

| Complexity | Count | Tasks |
|------------|-------|-------|
| **S (Small)** | 7 | #1, #2, #3, #4, #5, #9, #12, #13 |
| **M (Medium)** | 5 | #7, #10, #11, #14, #15 |
| **L (Large)** | 1 | #6 |

**Recommended Iteration 2 approach:** Start with the cluster of Small tasks (1-5, 8-9, 12-13) to close safety gaps and quick wins. Then tackle Medium tasks (7, 10-11, 14-15) for clinical functionality. The Large task (6 - trend charts) is the single highest-impact feature but requires the most development effort -- consider tackling it last once the foundation is solid.

---

## Reviewer Consensus Matrix

| Issue | Oncologist | Nurse | Pharmacist | UX | Data Sci |
|-------|:----------:|:-----:|:----------:|:--:|:--------:|
| Vital sign alerts missing | X | X | | | |
| Trend visualization needed | X | X | | X | |
| Intervention/med tracking | X | X | X | | |
| CRS selector non-functional | X | X | | X | |
| Composite score misleading | X | | | | X |
| CAR-HEMATOTOX threshold wrong | X | | | | X |
| ALT missing from flagging | X | | X | | |
| Infection vs CRS differential | X | X | | | |
| Checklist state not persisted | | X | | X | |
| No handoff/note generation | | X | | X | |
| Tocilizumab dose calculator | | X | X | | |
| Keyboard/accessibility gaps | | | | X | |
| Colorblind safety gaps | | | | X | |
| Skipped models invisible | | | | | X |
| Antimicrobial prophylaxis absent | | | X | | |
| REMS documentation inadequate | | | X | | |

---

*Synthesis completed 2026-02-07. This document consolidates 5 independent professional reviews into an actionable plan for Iteration 2 development.*
