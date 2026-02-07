# ICU Nurse Clinical Dashboard Review

**Reviewer:** Jessica Martinez, RN, BSN
**Role:** Senior ICU Nurse, Cell Therapy Unit (100+ CAR-T patients)
**Date:** 2026-02-07
**System Reviewed:** Cell Therapy Safety Platform - Clinical Dashboard (`index.html`) and Demo Cases (`demo_cases.js`)

---

## 1. Bedside Usability

### What Works
- The **Clinical Visit tab** with manual entry is the right idea. Nurses need a way to enter vitals and labs quickly, and the form grid layout with labeled fields and units is clear.
- **Lab value auto-flagging** (red border for high, amber for low) on manual input is excellent. When I type a creatinine of 1.8 into the field, I want immediate visual feedback that it is out of range. This feature delivers that.
- The **monospace font on numeric values** makes it easy to scan columns of numbers quickly, which matters when you are comparing trends across a shift.
- **Dark mode** is genuinely helpful. ICU lights are often dimmed at night, and a bright white screen is disruptive to patients and painful for nurses who have been staring at monitors for 10 hours.

### Problems
- **No quick-entry workflow.** The Clinical Visit form requires filling in ~15 lab fields, 4 vital sign fields, and 4 clinical assessment fields before I can run a prediction. During a busy shift with 2 CAR-T patients, I do not have 5 minutes to type all of this. I need either (a) a way to pull values from the EMR automatically, or (b) a minimal entry mode where I enter only the 4-5 values that changed since last assessment and the system carries forward the rest.
- **No timestamp on entries.** When I enter vitals, there is no field for the time of assessment. Was this the 0200 check or the 0600 check? This is critical for trending.
- **Blood pressure is a single text field** (`visit_bp` with placeholder "120/80"). This is error-prone. Nurses will type "120/80", "120 / 80", "120-80", or just "120". It should be two separate numeric fields for systolic and diastolic, just like every bedside monitor and EMR in existence.
- **Respiratory rate is missing from the Clinical Visit form.** It is in the demo case data (`respiratory_rate`) and is a critical vital sign for CRS assessment (tachypnea is an early sign of respiratory compromise), but the manual entry form only has Temperature, Heart Rate, BP, and SpO2.
- **No way to save partial entries.** If I get pulled away mid-entry for a code blue, I lose everything I typed. The form needs auto-save or at minimum a "Save Draft" button.
- **All form fields are disabled** in the Pre-Infusion view (the `disabled` attribute is set on selects and inputs). This means I cannot actually use this view to document a real pre-infusion assessment. It appears to only display demo data.

### Severity: HIGH
The manual entry workflow is the single biggest barrier to clinical adoption. If it takes too long, nurses will not use it.

---

## 2. Alarm Design

### What Works
- The **alert banner system** with color-coded severity (red for danger, amber for warning, green for success) follows standard clinical conventions. Red = act now, amber = watch closely.
- **Specific, actionable alert text.** The alerts do not just say "abnormal value." They say things like "Ferritin 5800 ng/mL markedly elevated. Consider HScore assessment and HLH/IEC-HS evaluation." This tells me what to do next, which is far better than most clinical decision support tools.
- **CRS grade-specific management guidance** in the CRS Management Algorithm card is well-structured. Grade 1 through Grade 4 each have clear actions.
- The **HLH warning** fires on ferritin >10,000 and fibrinogen <1.5 g/L, which are clinically appropriate thresholds.

### Problems
- **No alert prioritization or suppression.** Looking at the `generateAlerts()` function, all alerts are generated and displayed simultaneously. A high-risk patient on day 3 of severe CRS could have 5-6 alerts showing at once (high risk, high fever, HLH warning, low fibrinogen, severe thrombocytopenia, severe neutropenia). This is textbook alarm fatigue. The system needs a priority hierarchy where the most critical alert is prominent and others are collapsed or grouped.
- **No alert acknowledgment.** There is no way to dismiss or acknowledge an alert. In a 12-hour shift, seeing the same 5 red banners for 12 hours straight means I stop reading them by hour 2. I need to be able to acknowledge "I have seen this and taken action" so the alert either disappears or changes to a "acknowledged" state.
- **No escalation alerts.** The system shows the current state but does not compare to the previous assessment. If a patient's CRP went from 48 to 185 in 12 hours (like Case 2, James Williams, Day 1 to Day 2), that rate of change is more alarming than the absolute value. The system should flag rapid deterioration: "CRP increased 172% in 24 hours."
- **No audio/visual alarm for critical values.** A ferritin of 10,000 or a systolic BP of 88 should produce a visual alarm that is impossible to miss, not just a red banner that blends in with the other red banners.
- **Missing alert for hypotension.** The alert generation checks temperature, ferritin, fibrinogen, platelets, and ANC, but does not alert on systolic BP <90. Hypotension is a defining criterion for CRS Grade 2+ and is one of the most time-sensitive findings. This is a safety gap.
- **No alert for tachycardia.** Heart rate >120 is not flagged. Tachycardia is often the first sign of hemodynamic compromise before blood pressure drops.
- **No alert for SpO2 <94%.** Hypoxia is a CRS grading criterion but is not included in the alert logic.

### Severity: HIGH
Missing hypotension, tachycardia, and hypoxia alerts is a patient safety issue. These are the vital sign changes that define CRS grading.

---

## 3. Documentation

### What Works
- The **Print button** exists in the header and the print CSS hides the sidebar and navigation, which is a reasonable starting point for generating a paper record.
- **Teaching points** at the bottom of each demo case are excellent for documentation. When I am writing a clinical note, having the clinical context summarized (e.g., "Low baseline EASIX (0.74) predicted mild CRS course") helps me document the clinical reasoning.

### Problems
- **No structured note generation.** I need a "Generate Assessment Note" button that produces text I can copy-paste into Epic/Cerner. Something like: "Day 3 post axi-cel infusion. CRS Grade 1. Temp 38.4C, HR 96, BP 118/68, SpO2 97%, RR 18. EASIX 3.12 (low risk). HScore 89 (low probability HLH). CRP 48, ferritin 620, LDH 340. No ICANS (ICE 10/10). Plan: Continue supportive care with acetaminophen. Next assessment in 4 hours."
- **No nursing assessment documentation fields.** Where do I document skin assessment (capillary refill, rash, edema)? Where do I document I&O (fluid balance is critical in CRS with capillary leak)? Where do I document pain assessment? Where do I document the patient's subjective complaints?
- **Printed output is untested and likely poor.** The print CSS (`@media print`) hides critical elements but does not reformat the remaining content for paper. Score cards with colored borders may not print well in grayscale. There is no page break management for multi-page printouts.
- **No PDF export.** Many institutions require PDF documentation for the medical record. Print-to-PDF via browser is unreliable for formatting.
- **No way to document interventions.** If I gave tocilizumab, acetaminophen, or started a fluid bolus, there is nowhere to record that in this system. The demo case clinical notes mention these interventions, but the dashboard has no field for them.

### Severity: MODERATE
Documentation is a secondary function (the EMR is primary), but the lack of note generation and intervention documentation limits the tool's value for clinical workflow.

---

## 4. Handoff Support

### What Works
- The **patient sidebar** with risk level badges gives a quick visual summary of patient acuity. An incoming nurse can glance at the sidebar and see which patients are high risk.
- The **timeline view** in the sidebar showing disease trajectory with color-coded dots (green/amber/red) is a nice touch for understanding where a patient has been.

### Problems
- **There is no handoff summary feature.** This is a significant gap. At every shift change (0700 and 1900), I need to give a structured handoff. The SBAR format (Situation, Background, Assessment, Recommendation) is standard. This system has all the data to generate one automatically but does not.
- **No way to compare two timepoints side by side.** During handoff, I need to say "CRP went from 48 to 185 since last shift." The system shows one timepoint at a time. I need a comparison view or at minimum a trend summary.
- **No shift summary.** What changed in the last 12 hours? What interventions were given? What is the plan for the next shift? None of this is available.
- **No "flag for oncoming nurse" feature.** Sometimes I need to highlight something specific for the next nurse: "Watch for delayed ICANS - patient was confused briefly at 0300 but ICE was 9/10 at 0500. May be starting to trend."
- **No pending orders or follow-up tracking.** The "Anticipated Tests" list is generic based on the clinical state. What about the specific orders I requested that have not resulted yet? "Waiting on IL-6 result from 1400 draw."

### Severity: HIGH
Handoff communication failures are the #1 cause of adverse events in hospitals. A tool that aims to support CAR-T safety monitoring must support structured handoff.

---

## 5. Monitoring Workflows

### What Works
- The **Pre-Infusion Monitoring Plan** (line 931-944 of index.html) specifies appropriate frequencies: vitals q4h, CBC daily, CRP daily, ferritin daily if CRS develops, ICE score q8-12h. These align with institutional protocols I have worked with.
- The **Anticipated Tests** feature dynamically adjusts based on clinical state. If there is fever, blood cultures and ferritin are added as STAT. If the patient is high risk, triglycerides and D-dimer are added. This is smart clinical logic.
- The **priority coding** on test orders (red=stat, amber=urgent, green=routine) matches how we think about lab ordering.

### Problems
- **The monitoring plan does not specify q4h versus q2h versus q1h escalation based on CRS grade.** The CRS Management Algorithm card mentions "Monitor q4h" for Grade 1, "Monitor q2h" for Grade 2, and "Monitor q1h" for Grade 3, but the Anticipated Tests list always shows "Vital signs q4h." These should be dynamically adjusted.
- **No timer or reminder system.** Saying "vitals q4h" is useless if there is no alert when 4 hours have passed. I need a countdown timer or at minimum a "Next assessment due" display.
- **No escalation pathway from floor to ICU.** The CRS Management Algorithm mentions "ICU transfer" for Grade 3, but there is no structured ICU transfer checklist, no ICU bed status indicator, and no way to initiate an ICU consult from the dashboard.
- **Lab ordering frequency does not adapt automatically.** During Grade 3 CRS, I should be drawing CBC q6h, not daily. The demo case teaching points (Case 2) mention "CBC with differential q6h during Grade 3+ CRS," but the dashboard's anticipated tests algorithm does not implement this escalation.
- **No medication administration tracking.** Tocilizumab dosing (8mg/kg, max 800mg, can repeat x1 in 8 hours) is mentioned in the management algorithm but there is no way to track when it was given or whether a second dose is indicated. This is the most time-critical medication decision in CRS management.
- **q6h monitoring frequency is not mentioned anywhere in the dashboard.** The demo case anticipated tests reference q6h and q12h frequencies, but the dashboard only generates q4h, q8-12h, daily, and STAT. There is a gap for the intermediate monitoring frequencies used in ICU-level care.

### Severity: HIGH
Monitoring frequency escalation is fundamental to CRS management. The disconnect between the management algorithm guidance and the actual monitoring plan logic needs to be fixed.

---

## 6. Patient Safety

### Critical Safety Gaps

1. **No hypotension alert.** Systolic BP <90 mmHg is not flagged. This is a CRS grading criterion (Grade 2 = hypotension not requiring vasopressors, Grade 3 = hypotension requiring vasopressors). James Williams (Case 2) drops to 92/56 on Day 2 and 88/52 on Day 3. The system should be screaming about this.

2. **No SpO2 alert.** Oxygen saturation <94% is not flagged. SpO2 of 92% (Case 2, Day 3) requires immediate intervention but generates no alert.

3. **No respiratory rate alert.** RR >24 is not flagged. Tachypnea is often the earliest sign of respiratory decompensation.

4. **No trending or rate-of-change detection.** A ferritin that goes from 890 to 3400 in 24 hours is more alarming than a stable ferritin of 3400. The system only evaluates single-timepoint snapshots.

5. **No weight-based dosing support.** Tocilizumab is dosed at 8mg/kg. The patient weight is in the demo data (`weight_kg`) but the dashboard never calculates the actual dose. When a patient is crashing and I need tocilizumab NOW, I should not be doing mental math.

6. **CRS grading is not automatically suggested.** The system has all the data to suggest a CRS grade (temperature, BP, O2 requirement) but requires the nurse to manually click through the CRS grade strip. During a rapid deterioration, the system should auto-calculate and display the current grade based on the vital signs.

7. **No sepsis screening.** Fever + tachycardia + hypotension in a neutropenic patient could be sepsis, not just CRS. The differential diagnosis between CRS and sepsis is life-or-death, and the system does not address it at all.

8. **No DIC screening.** The system tracks fibrinogen and D-dimer but does not calculate a DIC score (ISTH criteria). Case 2 on Day 3 has fibrinogen 2.0, D-dimer 4.8, platelets 38 - this patient may have DIC and the system does not flag it.

9. **No fluid balance tracking.** Third-spacing and capillary leak are hallmarks of severe CRS. Without I&O tracking, we cannot assess volume status.

10. **No "call physician" button or escalation trigger.** When parameters cross critical thresholds, the system should have a one-click escalation that pages the on-call physician with a structured summary.

### Severity: CRITICAL
The missing vital sign alerts (hypotension, SpO2, respiratory rate) represent the most serious safety gap in this system. These are the parameters that determine CRS grade and drive treatment decisions.

---

## 7. CRS Assessment Tool

### What Works
- The **CRS grade strip** (Grade 0 through Grade 4 displayed as clickable boxes with criteria text) is visually clear and uses the correct ASTCT consensus criteria (Lee et al. 2019).
- The **color coding** (green for Grade 0, yellow for Grade 1, amber for Grade 2, orange for Grade 3, red for Grade 4) is intuitive.
- The **management algorithm** paired directly below the grading tool is the right workflow. Grade the CRS, then immediately see what to do about it.

### Problems
- **The grading tool is not interactive enough.** I click a grade box and it toggles a "selected" CSS class, but nothing else happens. It does not update the patient record, does not change the monitoring frequency, does not trigger appropriate orders. It is decorative, not functional.
- **No guided CRS grading questionnaire.** Instead of asking me to read criteria and pick a grade, the system should walk me through it: "Is the patient febrile (T >= 38.0C)? Yes/No. Is the patient hypotensive? Yes/No. Does the patient require vasopressors? Yes/No. Does the patient require supplemental oxygen? Yes/No. What type?" Then auto-calculate the grade. This is how it works in a rapid assessment.
- **No time-stamped CRS grade history.** I need to see: Grade 0 (baseline) -> Grade 1 (Day 1 0800) -> Grade 2 (Day 2 1400) -> Grade 3 (Day 2 2200). The trajectory matters as much as the current grade.
- **The CRS management algorithm is static text.** It should highlight the row that matches the current CRS grade so I can instantly see the relevant management plan.
- **No tocilizumab dose calculator integrated into the CRS view.** When I determine CRS Grade 2, the very next thing I need is "Tocilizumab dose for this patient: 8mg/kg x 72kg = 576mg IV over 1 hour."

### Severity: MODERATE
The CRS grading tool looks good but is not functional enough for bedside use during a rapidly evolving clinical scenario.

---

## 8. Top 5 Improvements (Bedside Nurse Perspective)

### 1. Add Vital Sign Alerts for Hypotension, Tachycardia, Hypoxia, and Tachypnea
**Why:** These are the vital sign changes that determine CRS grade and drive immediate treatment decisions. A CRS monitoring tool that does not alert on hypotension or desaturation is incomplete. This is the single most important fix for patient safety.
**Implementation:** Add to `generateAlerts()`: SBP <90 (danger), HR >120 (warning), SpO2 <94% (danger), RR >24 (warning). Add respiratory rate to the Clinical Visit form.

### 2. Build a Structured Shift Handoff Generator
**Why:** Handoff happens twice daily and is when most safety-critical information is lost. The system has all the data to generate a structured SBAR handoff automatically. This would be the feature that makes nurses love this tool rather than tolerate it.
**What it should include:** Patient name, day post-infusion, current CRS grade, current ICANS grade, key vital sign trends over the last 12 hours, key lab trends, interventions given (tocilizumab, steroids, vasopressors), current risk level, and plan for the next shift.

### 3. Implement Quick-Entry Mode with Carry-Forward
**Why:** A 15-field form is a non-starter during a busy shift. I need to be able to enter only the 3-4 values that changed (e.g., new temp, new CRP, new ferritin) and have the system carry forward everything else from the last assessment. Better yet, integrate with the EMR so I do not have to enter anything manually.
**Minimum viable:** A "Copy from last assessment" button that pre-fills all fields with previous values, then I only change what is new.

### 4. Add Rate-of-Change Trending and Alerts
**Why:** A single snapshot is far less useful than understanding trajectory. A CRP of 185 that was 48 yesterday is very different from a CRP of 185 that was 200 yesterday. The system should automatically calculate and display delta values, percent change, and flag rapid deterioration patterns.
**Specifically needed:** CRP velocity, ferritin velocity, LDH velocity, creatinine trajectory, and platelet decline rate. These are the patterns experienced CAR-T nurses watch for.

### 5. Integrate Tocilizumab Dose Calculator and Administration Tracking
**Why:** Tocilizumab timing is the most critical medication decision in CRS management. I need to know: (a) the weight-based dose for this patient, (b) when the first dose was given, (c) whether a second dose is indicated (8+ hours since first dose, inadequate response), and (d) the maximum number of doses (typically 2 within 24 hours). All of this data exists in the system but is not presented as a medication management tool.

### Honorable Mentions (6-10)
6. **Auto-calculate CRS grade from vital signs** rather than requiring manual selection
7. **Add a "time since last assessment" countdown** with overdue alerts
8. **Add nursing assessment fields** (skin, I&O, pain, subjective symptoms)
9. **Add a one-click physician notification** with auto-generated clinical summary
10. **Add sepsis vs CRS differential diagnosis support** (procalcitonin ordering, lactate trending)

---

## Summary Assessment

**Overall Grade: B-**

This dashboard demonstrates strong clinical knowledge. The scoring systems are correct (EASIX, HScore, CAR-HEMATOTOX, ICE), the reference ranges are accurate, the CRS grading criteria are current (ASTCT 2019 consensus), and the demo cases are clinically realistic with believable disease trajectories. The teaching points are genuinely educational. Someone who understands CAR-T toxicity management built this.

However, the tool is currently built from a **physician/researcher perspective**, not a **bedside nursing perspective**. It excels at displaying calculated risk scores and clinical reference material. It falls short on the things that matter during a 12-hour shift: quick data entry, trending, alert management, handoff support, and intervention tracking.

The critical safety gaps (missing vital sign alerts for hypotension, hypoxia, and tachycardia) must be addressed before this tool is used in any clinical setting. A CAR-T safety monitoring dashboard that does not alert on the vital sign changes that define CRS grades is not meeting its core safety mandate.

The foundation is solid. With the improvements outlined above, this could become a genuinely useful bedside tool rather than a risk assessment display panel.

---

*Review completed by Jessica Martinez, RN, BSN. All assessments based on direct review of source code and demo case data, informed by experience managing 100+ CAR-T cell therapy patients across multiple commercial products.*
