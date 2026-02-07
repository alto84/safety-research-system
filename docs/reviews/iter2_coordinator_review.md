# Cell Therapy Coordinator Review - Iteration 2

**Reviewer:** Karen Liu, BSN, RN, OCN, BMTCN
**Role:** Cell Therapy Coordinator (12 years experience, CAR-T programs)
**Date:** 2026-02-07
**Files Reviewed:** `index.html` (dashboard), `demo_cases.js` (8 demo patients)

---

## Executive Summary

This platform has a solid clinical foundation and reflects genuine understanding of cell therapy workflows. The scoring models (EASIX, HScore, CAR-HEMATOTOX, Hay classifier) are the right ones, the CRS/ICANS grading follows ASTCT consensus, and the demo cases are remarkably realistic. As someone who coordinates 5-10 CAR-T patients simultaneously, however, the dashboard in its current form is designed as a single-patient deep-dive tool, not a multi-patient operational cockpit. That distinction is the single largest gap between this system and what I would use during a 12-hour shift. Below I detail what works well, what needs rethinking, and what is missing entirely.

---

## 1. Multi-Patient Workflow

### What Works
- The patient sidebar with risk-level badges (LOW/MODERATE/HIGH) is the right idea. Color-coded risk at a glance is exactly how I scan my patient board.
- Clicking a patient card immediately loads their data. The interaction model is correct.
- The sidebar shows current timepoint risk, which is what matters.

### Critical Gaps

**No multi-patient overview panel.** When I arrive at 0700 for shift, the first thing I need is a single screen that answers: "Who needs me right now?" The current design forces me to click through patients one at a time. I need a table or grid view showing all active patients with columns for:
- Patient name and cell therapy day
- Current CRS grade and ICANS grade
- Most recent temperature
- ANC (for neutropenic precaution decisions)
- Platelet count (for transfusion thresholds)
- Risk trajectory (worsening vs. stable vs. improving)
- Time since last assessment
- Any active alerts

**No sort or filter on the sidebar.** With 8 demo patients visible, the sidebar is manageable. In a real program with 8-12 active patients across inpatient and outpatient settings, I need to sort by risk level (HIGH first), by cell therapy day (early post-infusion patients get priority), or by time since last assessment. The sidebar currently has no sort, filter, or search capability.

**No badge counts for alerts.** The sidebar patient cards show risk level but do not show the number of active alerts. If a patient has three critical alerts (high fever + hypotension + low fibrinogen), I need to see a "3" badge before I even click into that patient. This is how Epic and Cerner worklists function and coordinators rely on it.

**No concept of "my patients."** In a multi-coordinator program, I carry a defined panel. There is no way to mark which patients are mine vs. a colleague's. A simple assignment tag would be sufficient.

**Fixed sidebar width of 320px.** On a standard hospital workstation monitor (often 1366x768), this sidebar consumes nearly a quarter of the screen. On smaller screens the layout collapses to a stacked view (which the responsive CSS handles), but then I lose simultaneous sidebar-plus-content viewing entirely.

---

## 2. Shift Handoff

### What Works
- Each patient's clinical notes are excellent narrative summaries. If I were reading these in a handoff, I would know exactly what happened.
- The timeline with timepoint dots and risk-color coding in the sidebar is a good visual for trajectory.
- The trend charts with sparklines would be useful during a verbal handoff.

### Critical Gaps

**No handoff report generator.** This is a significant omission. At shift change (0700/1900), the outgoing coordinator needs to produce a structured summary for each patient that includes:
1. One-line status (e.g., "Day 3 post-axi-cel, Grade 1 CRS, stable")
2. Key events this shift (e.g., "Fever onset 1400, tocilizumab administered 1530")
3. Active issues (e.g., "ANC 0.1, on filgrastim; platelet transfusion threshold 10K")
4. Pending items (e.g., "ICE score due at 2000; blood cultures pending 48h")
5. Anticipatory guidance (e.g., "Watch for CRS escalation; tocilizumab re-dose criteria")

The system has all the data elements to generate this but does not offer the function. A "Generate Handoff Summary" button per patient -- or better, a "Shift Handoff Report" that compiles all active patients -- would be transformative.

**No "since last assessment" tracking.** The system shows timepoints but does not track when a real user last reviewed data. In practice, I need to know: "What changed since I last looked at this patient 4 hours ago?" A simple diff or "new since" marker on labs, vitals, and alerts would be extremely valuable.

**No shift-based time awareness.** The header has a clock, which is good. But the system does not understand shift concepts. There is no way to mark "I assessed this patient at 0830" and have the system flag when the next assessment is due. Nursing typically assesses CAR-T patients q4h-q8h depending on CRS grade, and the coordinator needs to track compliance with that cadence across all patients.

**Print support is present but basic.** The print CSS hides the sidebar and navigation, which is correct, but there is no option to print a structured handoff form. The print output would be whatever task view is currently displayed, which is not a handoff-oriented format.

---

## 3. Documentation Support

### What Works
- CRS grading via the clickable grade strip (Grade 0-4) is well-designed. The visual layout with ASTCT criteria under each grade is exactly what a coordinator references during grading. The localStorage persistence of the selected grade per patient per timepoint is a thoughtful touch.
- The ICE score calculator with all five domains (orientation, naming, commands, writing, attention) is accurate and functional. The auto-grading from total score to ICANS grade is correct per ASTCT criteria.
- The HScore component breakdown table showing individual variable contributions is clinically useful for documentation.

### Critical Gaps

**No CRS/ICANS documentation timestamp.** When I grade CRS or ICANS, I need to record the datetime of that assessment. The current grade selector stores the grade in localStorage but attaches no timestamp. For REMS reporting, the exact time of CRS onset, peak grade, and resolution must be documented. Similarly, the time of each ICANS grade change matters for steroid dosing decisions.

**No CRS/ICANS event log.** I need a running chronological log of: "Day 1 0800: CRS Grade 0, Day 2 1400: CRS Grade 1 (fever onset 38.4C), Day 2 2200: CRS Grade 2 (hypotension requiring fluids), Day 3 0200: Tocilizumab administered 8mg/kg." The system captures snapshots at defined timepoints but has no way to document events between timepoints, which is where the actual clinical action happens.

**No REMS reporting support.** All FDA-approved CAR-T products require REMS program participation. The system mentions "REMS requirements reviewed" in the discharge checklist, which is good. But there is no dedicated REMS module to capture the required data elements:
- CRS grade (highest), onset date, resolution date
- ICANS grade (highest), onset date, resolution date
- Tocilizumab doses given (number, dates, doses)
- Corticosteroid use (type, dose, duration)
- ICU admission (yes/no, duration)
- Adverse events requiring reporting

A REMS Summary tab that pre-populates from the clinical data and allows the coordinator to review and export would save 30-45 minutes per patient.

**No chart export.** There is no "Export to PDF" or "Copy to Clipboard" function for assessment data. When I document in Epic, I need to transfer the risk scores, lab interpretations, and clinical assessments into a progress note. Currently I would have to manually transcribe everything. A structured text export (or better, FHIR-compatible data export) would integrate into the documentation workflow.

**Checklist state is not shared.** The pre-infusion checklist and discharge checklist use localStorage, meaning they are device-specific and user-specific. If the day shift coordinator checks off items, the night shift coordinator opening the same patient on a different workstation sees unchecked boxes. Checklists need server-side persistence to function in a multi-user environment.

---

## 4. Anticipated Orders and Tests

### What Works
- The `getAnticipatedTests()` function correctly adjusts test recommendations based on clinical state. Fever triggers blood cultures and ferritin. High risk adds triglycerides and fibrinogen. ANC < 0.5 triggers G-CSF. This context-sensitive logic is clinically sound.
- The test priority tiering (STAT / urgent / routine) with color-coded borders is immediately interpretable.
- The Hematologic Recovery view correctly includes G-CSF criteria (ANC < 0.5) and transfusion triggers.

### Tests That Are Correctly Timed
- CBC with differential daily (correct baseline frequency)
- CMP daily (correct, captures LDH and creatinine for EASIX)
- CRP daily (correct, best CRS trajectory marker)
- Blood cultures with fever (correct, essential to differentiate CRS from infection)
- IL-6 with high fever >= 38.9C (correct threshold for the Hay classifier)
- ICE score q8-12h (correct frequency during monitoring)

### Missing or Incorrectly Timed Tests

**Post-Day 7 cytokine panel.** The anticipated tests do not include a cytokine panel (IL-6, IL-10, IFN-gamma, TNF-alpha) at Day 7 as a trend assessment. Many programs obtain this routinely at Day 7 regardless of CRS status to assess immune activation trajectory.

**IVIG for B-cell aplasia.** The discharge view mentions "IgG monthly - IVIG if IgG < 400" which is correct, but this should also appear in the outpatient follow-up anticipated tests for all patients at Day 28 and Day 100. The immunoglobulin level check is mentioned weekly in the anticipated tests, but the context and threshold (IgG < 400 mg/dL) should be explicit.

**Filgrastim monitoring.** While the system correctly triggers G-CSF at ANC < 0.5, it does not include the monitoring that goes with G-CSF administration: daily ANC while on filgrastim, discontinuation criteria (ANC > 1.0-1.5 for 2-3 consecutive days), and the caveat about not starting filgrastim during active CRS (as it may worsen cytokine release). The demo Case 7 (Linda Park) correctly notes filgrastim use but the anticipated test logic does not flag the CRS-timing concern.

**CMV/EBV reactivation monitoring.** The demo Case 7 anticipated tests include "CMV/EBV PCR weekly" but the `getAnticipatedTests()` function in the dashboard does not generate this for any patient. In immunosuppressed patients post-CAR-T (especially those with prolonged cytopenias or on steroids for ICANS), weekly viral reactivation monitoring is standard at many institutions.

**Coagulation panel (PT/PTT/INR).** The anticipated tests include fibrinogen and D-dimer when risk is high, but a full coagulation panel is typically ordered during severe CRS, especially when DIC is a concern. The HLH screening section correctly identifies fibrinogen as critical but the complete DIC workup panel is not generated.

**Urinalysis.** For patients developing AKI during CRS (e.g., Cases 2 and 3), a urinalysis to differentiate prerenal from intrinsic renal injury is standard practice but not mentioned.

**Echocardiogram.** For Grade 3+ CRS with persistent tachycardia or hemodynamic instability, many programs obtain a bedside echo to assess cardiac function. This is not included in the anticipated tests or CRS management algorithm.

---

## 5. Day-by-Day Workflow Accuracy

### Pre-Infusion (Baseline)

**Strengths:**
- Baseline lab panel is comprehensive and correctly identifies which labs feed into which scoring models (EASIX, HScore, CAR-HEMATOTOX).
- The pre-infusion checklist covers the essential safety items: tocilizumab bedside, ICU bed availability, leukapheresis product verification, consent, lymphodepletion completion.
- The baseline risk factor form captures tumor burden, prior therapies, ECOG, and bridging therapy.

**Gaps:**
- No field for lymphodepletion regimen details (flu/cy dose, timing, day of completion). Different regimens carry different myelosuppressive risk.
- The ECOG field is a simple number input. In practice, the coordinator also documents the functional details ("able to do light housework" vs. "bedbound > 50% of waking hours") because ECOG scoring can be subjective.
- No organ function checklist (cardiac clearance, pulmonary function, hepatitis B screening, HIV status). These are standard pre-CAR-T requirements.
- The bridging therapy dropdown offers only "None/Radiation/Chemo" but the actual options are more nuanced and product-specific. The demo cases correctly show detailed bridging (e.g., "Polatuzumab-BR x1 cycle") but the form does not capture this.
- No documentation of cell product details: lot number, cell dose, viability, product identity verification. This is a Joint Commission and FACT accreditation requirement.

### Day 1 Post-Infusion

**Strengths:**
- The Hay Binary Classifier integration is excellent. This is exactly the right tool for Day 1 risk stratification.
- The fever threshold logic is correct: 38.9C triggers the Hay classifier, 38.0C triggers CRS Grade 1 assessment.
- The Day 1 checklist covers vitals, labs, neuro assessment, and patient education.

**Gaps:**
- No infusion reaction documentation. Day 0/1 is when infusion reactions occur (distinct from CRS), and the checklist should capture: any acute reactions during infusion, vital signs at 0, 15, 30, 60 minutes post-start, symptoms during infusion (rigors, nausea, etc.).
- The checklist lacks a medication reconciliation item. Post-infusion, certain medications are contraindicated (e.g., systemic corticosteroids unless for CRS/ICANS, some immunosuppressants).
- No fluid balance tracking. Many CAR-T patients receive significant IV hydration, and I/O monitoring is critical for detecting early fluid overload or dehydration.

### Days 2-7 (Peak CRS Risk)

**Strengths:**
- The CRS monitoring view correctly implements ASTCT grading with the clickable grade strip.
- The CRS management algorithm (Grade 1-4 treatments) is accurate and follows current guidelines.
- Key lab trends (CRP, ferritin, LDH, fibrinogen) with sparkline charts are precisely what I want to see during this period.
- Alerts fire appropriately for fever, hypotension, hypoxia, and lab abnormalities.

**Gaps:**
- **The UI does not adapt to CRS grade.** When a patient is in Grade 3 CRS, the monitoring frequency should automatically escalate (vitals q1h, labs q6-8h, ICE q4h). The anticipated tests function has some of this logic but the visual presentation does not change. I would want the header or a prominent banner to reflect the current intensity level: "ACTIVE CRS GRADE 3 -- ICU PROTOCOL IN EFFECT."
- **No vasopressor tracking.** Grade 3+ CRS requires vasopressor documentation (agent, dose, titration direction). The clinical notes in the demo cases reference vasopressor use, but the dashboard has no structured field for this.
- **No oxygen requirement tracking.** Similarly, the demo clinical notes describe oxygen modalities (nasal cannula, HFNC, etc.) but the dashboard does not have a structured field to track FiO2 and delivery device. These are CRS grading criteria.
- **No tocilizumab dose counter.** After administering tocilizumab, I need to track: dose number (maximum 3-4 doses per institutional protocol), dose given (8 mg/kg, actual mg administered), time of administration, and response assessment timing (typically reassess 4-8 hours post-dose). The dashboard does not capture any of this.

### Days 7-14 (ICANS Risk Window)

**Strengths:**
- The ICANS view with the ICE score calculator is well-designed and clinically accurate.
- The ICANS grading table correctly includes consciousness level, seizures, motor findings, and cerebral edema as modifiers.
- The management algorithm for Grades 1-4 ICANS is current and correct, including seizure prophylaxis with levetiracetam.
- Demo Case 5 (Sarah Thompson) excellently demonstrates ICANS occurring as CRS resolves, which is a critical teaching pattern.

**Gaps:**
- **No visual cue that we have entered the ICANS risk window.** The task navigation has a static "ICANS" tab. For patients on Day 5-14 (the peak ICANS window), there should be a visual indicator or alert that says "You are in the ICANS risk window -- ensure ICE assessments are being performed per protocol."
- **No serial ICE score tracking.** The ICE calculator produces a score, but there is no trend display showing ICE scores over time. A declining ICE trend (10 -> 7 -> 3) is alarming and should be visually prominent. The sparkline approach used for labs would be ideal here.
- **No seizure documentation.** If a patient seizes (relevant to ICANS Grade 3-4 determination), there is no structured place to document seizure type, duration, and intervention.

### Discharge Readiness

**Strengths:**
- The discharge readiness checklist is comprehensive and clinically appropriate. The criteria (afebrile 24h, no vasopressors, no O2, CRS/ICANS resolved, ANC > 0.5, platelets > 20, oral meds tolerated, caregiver education, follow-up scheduled, REMS reviewed, proximity requirement) are all correct.
- The percentage-met indicator with color coding gives a quick visual.
- Discharge instructions cover the right return-to-ED criteria, activity restrictions, and follow-up schedule.
- The outpatient monitoring plan includes IVIG criteria and B-cell aplasia monitoring.

**Gaps:**
- **No caregiver assessment.** The checklist includes "Caregiver education completed" but not whether the caregiver is identified and available. CAR-T patients require a 24/7 caregiver for 4 weeks, and I need to document who the caregiver is and confirm their availability.
- **No driving restriction reminder with date.** The instructions say "No driving for 8 weeks post-infusion" but do not calculate and display the actual date when the restriction lifts. This is a common patient question and coordinators need this at discharge.
- **No medication reconciliation at discharge.** Patients leave on specific medications (antimicrobial prophylaxis, seizure prophylaxis if ICANS occurred, possibly ongoing steroids). The discharge view does not include a medication list.
- **No pharmacy coordination.** Many CAR-T patients are on specialty medications that require prior authorization or specialty pharmacy coordination. This is a coordinator responsibility that is not addressed.

### Day 28 and Day 100 Follow-up

**Not addressed.** The dashboard has no dedicated view for milestone assessments. Day 28 is the standard first response assessment (PET-CT, bone marrow biopsy for myeloma, disease-specific response criteria). Day 100 is the traditional transplant/cell therapy milestone with comprehensive restaging. These are major coordinator workflow events that involve:
- Scheduling multiple tests (imaging, bone marrow, labs)
- Coordinating with radiology, pathology, and referring oncologists
- REMS data submission
- Insurance reporting and continued authorization
- Long-term complication screening (B-cell aplasia, hypogammaglobulinemia, secondary malignancies)

The Clinical Visit tab provides a manual entry form, which could theoretically be used for follow-up visits, but it lacks the structure and context of a milestone assessment workflow.

---

## 6. Pain Points -- What Would Slow Me Down

### Things That Would Force Me to Open Epic/Cerner
1. **Medication documentation.** No medication administration record capability (tocilizumab doses, steroids, filgrastim, transfusions).
2. **Nursing assessments.** No structured nursing assessment (skin, neurologic detail beyond ICE, respiratory assessment, I/O tracking).
3. **Orders.** The "anticipated tests" are suggestions only. I cannot place actual orders from this system. This is expected for a decision-support tool, but it means I toggle between this system and the EHR constantly.
4. **Vitals entry.** Vital signs are pulled from demo data, not from a live feed. In practice, I need integration with the bedside monitor or nurse-charted vitals.
5. **Communication.** No way to message the attending, fellow, pharmacist, or bedside nurse from the dashboard. No way to flag a patient for attending review.
6. **Billing and authorization.** CAR-T is among the most expensive therapies in medicine. Coordinators manage payer authorization, which this system (appropriately) does not address.

### Things I Would Want on a Mobile Device During Rounds
1. The multi-patient overview (who needs me now).
2. Per-patient: current CRS/ICANS grade, key labs (CRP, ferritin, ANC, platelets), vitals trend.
3. Quick ICE score entry (the calculator is touch-friendly if the form inputs were larger).
4. Alert notifications pushed to the device (temperature spike, lab critical value).
5. A voice-note or quick-text field to capture rounding observations.

The current responsive CSS collapses the sidebar into a short horizontal panel at < 1024px, which works but is not optimized for mobile. The data tables and form grids become unusable on a phone screen. A dedicated mobile view or progressive web app approach would be needed.

---

## 7. Demo Case Realism

### Overall Assessment
The 8 demo cases are **exceptionally realistic** and represent the core case mix that a CAR-T program encounters. The lab value trajectories are physiologically accurate, the clinical notes read like actual progress notes, and the timing of complications aligns with published literature. Whoever designed these cases has either practiced cell therapy medicine or consulted closely with someone who has.

### Individual Case Assessment

| Case | Patient | Scenario | Realism | Notes |
|------|---------|----------|---------|-------|
| 1 | Maria Chen | Low-risk DLBCL, mild Grade 1 CRS | Excellent | Textbook straightforward case. CRP preceding fever by 24h is a real observation. Self-limited Grade 1 CRS with acetaminophen only -- this is what ~40% of axi-cel patients look like. |
| 2 | James Williams | High-risk double-hit DLBCL, Grade 3 CRS + ICANS | Excellent | Double-hit with high tumor burden developing early severe CRS is a scenario I see 2-3 times per year. The IL-6 trajectory, vasopressor escalation, and tocilizumab re-dosing are all accurate. The note about paradoxical IL-6 elevation post-tocilizumab is an important teaching point that catches trainees off guard. |
| 3 | Patricia Rodriguez | Multiple myeloma, ide-cel, Grade 2 CRS | Excellent | Heavily pretreated myeloma with baseline cytopenias and renal impairment is the typical ide-cel patient. The CRS kinetics are correct for anti-BCMA products (milder than CD19). Free light chain tracking for response is appropriate. |
| 4 | Robert Kim | Transformed FL, tisa-cel, CRS transitioning to IEC-HS | Excellent | This is the most important teaching case. The ferritin velocity differentiation (CRS vs. HLH-like process) is the key clinical pearl. Ferritin going from 480 to 12,800 with fibrinogen dropping below 1.5 and triglycerides above 3.0 -- this is exactly the IEC-HS pattern. HScore crossing 169 is the diagnostic threshold correctly applied. |
| 5 | Sarah Thompson | MCL, liso-cel, isolated ICANS without significant CRS | Very Good | Demonstrates ICANS independent of CRS, which is an important concept. Age >65 as ICANS risk factor is correct. The ICE score deterioration from 10 to 3 with expressive aphasia is realistic. One minor note: MMSE baseline of 28/30 is documented but the system does not carry this forward for comparison, which would strengthen the case. |
| 6 | David Okafor | Myeloma, cilta-cel, late-onset CRS (Day 10) | Excellent | This case is critical for teaching. Cilta-cel's late CRS kinetics catch many teams off guard. The 9-day silence followed by sudden CRP and ferritin surges is exactly what happens. The teaching point about not relaxing monitoring early with cilta-cel is operationally important. Also correctly notes cilta-cel delayed neurotoxicity risk (parkinsonian features). |
| 7 | Linda Park | DLBCL post-auto-SCT, prolonged cytopenias | Excellent | High CAR-HEMATOTOX score with prior auto-SCT leading to prolonged pancytopenia extending past Day 28 -- this is a scenario that requires the most coordinator time for outpatient management (transfusion scheduling, G-CSF administration, antimicrobial prophylaxis, frequent CBCs). The reticulocyte and MPV tracking as early recovery markers is a sophisticated detail. |
| 8 | Michael Santos | DLBCL, liso-cel, optimal outcome | Very Good | Useful as a benchmark. All scores low, mild CRS, rapid recovery, discharge Day 10. Represents ~30-40% of patients who sail through. Correctly notes that even uncomplicated patients need long-term B-cell aplasia monitoring. |

### Missing Scenarios

**Bridging therapy complications.** None of the 8 cases show a patient who develops complications from bridging therapy that delay or complicate CAR-T infusion (e.g., neutropenic sepsis from bridging chemo requiring treatment delay while cells are in manufacturing).

**Manufacturing failure.** Approximately 1-3% of collections fail to produce a viable product. While this is not a safety monitoring scenario, it is a coordination nightmare (communicating with the patient, arranging alternative therapy, coordinating with the manufacturer).

**Retreatment.** No case shows a patient receiving a second CAR-T infusion after initial response and subsequent relapse. This is increasingly common with commercial products and has different risk considerations (prior tocilizumab exposure, potential anti-CAR antibodies, different risk profile on re-dosing).

**Concurrent infection during CRS.** While the cases mention blood cultures being sent, none demonstrate a patient with confirmed bacteremia concurrent with CRS. This is a management challenge where you are treating both CRS and sepsis simultaneously, and differentiating CRS fever from infection fever is clinically difficult.

**Pediatric or young adult case.** All patients are adults age 45-71. If the platform is intended for ALL-age CAR-T programs (tisa-cel is approved for pediatric ALL), a pediatric case with its different dosing, CRS kinetics, and monitoring needs would be valuable.

**Outpatient CAR-T administration.** Some centers are moving toward outpatient CAR-T with daily clinic visits. This workflow is fundamentally different and none of the cases reflect it.

---

## 8. Additional Technical Observations

### Data Architecture Concerns
- All demo data is client-side in a single JavaScript file. There is no server-side patient data persistence. For a production system, patient data must be stored securely with audit trails (HIPAA requirement).
- Lab value flagging uses hardcoded normal ranges in `NORMAL_RANGES`. In practice, normal ranges vary by laboratory and patient demographics (e.g., hemoglobin ranges differ by sex). The demo cases include both male and female patients, but the hemoglobin normal range is fixed at 12.0-17.5 g/dL without sex adjustment.

### Usability Notes
- The dark mode toggle is functional but the dark theme color choices for danger/warning states could be more distinct. On a dimmed hospital workstation at 0300, the red-on-dark-red alert styling may not pop enough.
- The teaching points section at the bottom of the Overview is valuable for trainees but would be distracting for experienced coordinators during a busy shift. Consider making it collapsible or hidden by default.
- The "Clinical Visit - Manual Entry" tab is useful for entering real patient data when the API is connected, but the form resets on task switch (navigating away and back clears inputs). This would be frustrating during a clinical encounter.
- Checklist items are bare HTML checkboxes without labels linked via `for` attributes. Accessibility (screen readers, keyboard navigation) would need improvement for ADA compliance.

### What This System Gets Right That Others Often Miss
1. **ASTCT consensus grading** is used consistently, not older grading systems.
2. **HScore with the 169 threshold** is correctly implemented and prominently displayed.
3. **The distinction between CRS and IEC-HS** is explicitly taught through the comparison table in the HLH view. Many clinical systems blur this distinction.
4. **Product-specific CRS kinetics** are acknowledged (cilta-cel late onset, liso-cel lower rates, axi-cel higher rates). This is not a generic one-size-fits-all tool.
5. **CAR-HEMATOTOX as a baseline predictive tool** is appropriately positioned. Many systems only react to cytopenias after they occur; this system flags risk before infusion.
6. **The ferritin velocity concept** (proportional rise in CRS vs. exponential rise in IEC-HS) is the most clinically important differential and it is correctly emphasized.

---

## 9. Priority Recommendations

### Must-Have for Coordinator Use (High Priority)
1. **Multi-patient dashboard view** with sortable/filterable patient table showing key parameters and alert counts at a glance.
2. **Shift handoff report generator** that compiles status, changes, pending items, and anticipatory guidance for all active patients.
3. **CRS/ICANS event log** with timestamps for grading changes, interventions (tocilizumab, steroids), and clinical milestones.
4. **REMS data module** that pre-populates from clinical data and supports required reporting fields.
5. **Server-side checklist persistence** so multi-user teams share state.

### Should-Have (Medium Priority)
6. **Tocilizumab/steroid dose tracker** with administration times and response assessment windows.
7. **Serial ICE score trend display** with sparkline like the lab trends.
8. **Day 28 and Day 100 milestone assessment workflows.**
9. **Chart export function** (structured text or PDF) for EHR documentation.
10. **Alert notification system** with configurable thresholds and push capability.

### Nice-to-Have (Lower Priority)
11. **Mobile-optimized view** for rounding.
12. **EHR integration** (FHIR-based) for live lab and vital sign feeds.
13. **Viral reactivation monitoring** (CMV/EBV) in anticipated tests for high-risk patients.
14. **Caregiver documentation** fields in the discharge workflow.
15. **Additional demo cases** for concurrent infection, retreatment, and pediatric scenarios.

---

## 10. Summary Verdict

**Clinical accuracy: 9/10.** The scoring models, grading systems, management algorithms, and demo case data are clinically sound and reflect current best practices.

**Multi-patient operational utility: 4/10.** The system is designed for deep single-patient assessment, not for managing a coordinator's daily panel of 5-10 patients. The multi-patient overview gap is the primary barrier to adoption.

**Documentation workflow: 5/10.** Good data capture elements exist (CRS grading, ICE calculator, lab display) but lack the timestamps, event logging, and export capabilities needed for actual clinical documentation.

**Day-by-day protocol coverage: 7/10.** Pre-infusion through Day 14 is well-covered. Discharge planning is solid. Post-discharge follow-up (Day 28, Day 100) is absent.

**Demo case quality: 9/10.** Among the most realistic simulated patient data I have seen in a clinical decision support tool. Minor gaps in scenario diversity (no concurrent infection, retreatment, or pediatric cases).

**Overall readiness for coordinator workflow: 6/10.** The foundation is strong. The clinical intelligence is there. The gap is operational: turning this from a clinician's reference tool into a coordinator's worklist management system. The recommendations above would bridge that gap.

---

*Reviewed by Karen Liu, BSN, RN, OCN, BMTCN -- Cell Therapy Coordinator*
*12 years experience in CAR-T coordination across academic medical center and community programs*
