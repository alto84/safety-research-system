# Clinical Safety Workflows for CAR-T Cell Therapy

> Reference document for building a clinical dashboard UI. Covers the full treatment timeline from pre-infusion assessment through discharge, including scoring models, monitoring frequencies, escalation protocols, and role-based information needs.

---

## Table of Contents

1. [Pre-Infusion Assessment (Day -7 to Day 0)](#1-pre-infusion-assessment-day--7-to-day-0)
2. [Day 1 Post-Infusion Monitoring](#2-day-1-post-infusion-monitoring)
3. [Active CRS Monitoring (Day 1-14)](#3-active-crs-monitoring-day-1-14)
4. [ICANS Assessment](#4-icans-assessment)
5. [HLH / IEC-HS Screening](#5-hlh--iec-hs-screening)
6. [Hematologic Recovery Tracking](#6-hematologic-recovery-tracking)
7. [Discharge Planning](#7-discharge-planning)
8. [Decision Support: Anticipatory Orders](#8-decision-support-anticipatory-orders)
9. [Standard Monitoring Frequencies](#9-standard-monitoring-frequencies)
10. [Key Action Thresholds](#10-key-action-thresholds)
11. [Role-Based Information Needs](#11-role-based-information-needs)

---

## 1. Pre-Infusion Assessment (Day -7 to Day 0)

### Timeline Overview

| Day | Activity |
|-----|----------|
| Day -7 to -6 | Baseline assessment, labs, risk scoring |
| Day -5 to -3 | Lymphodepleting chemotherapy (typically fludarabine + cyclophosphamide) |
| Day -2 to -1 | Rest period (minimum 2 days post-chemo before infusion) |
| Day 0 | CAR-T cell infusion |

### Baseline Labs (Day -7 to -5)

| Category | Tests | Purpose |
|----------|-------|---------|
| CBC with differential | WBC, ANC, ALC, hemoglobin, platelets | Baseline hematologic status; CAR-HEMATOTOX input |
| Comprehensive metabolic panel | BMP/CMP, LFTs (AST, ALT, bilirubin, albumin) | Organ function baseline |
| Inflammatory markers | CRP, ferritin, LDH | Baseline inflammation; EASIX/CAR-HEMATOTOX input |
| Coagulation | PT/INR, fibrinogen, D-dimer | Baseline coagulation; HLH screening |
| Renal function | Creatinine, BUN, GFR | EASIX input; organ function |
| Lipid panel | Triglycerides | HScore baseline |
| Cytokines (if available) | IL-6, IL-10, IFN-gamma, MCP-1 | Baseline for trend monitoring |
| Virology panel | CMV, EBV, HHV-6, adenovirus, HBV, HCV, HIV | Reactivation risk |
| Uric acid, phosphorus | Tumor lysis labs | TLS risk |
| Immunoglobulins | IgG, IgA, IgM | Baseline humoral immunity |

### Risk Scoring Models (Calculated Pre-Infusion)

#### CAR-HEMATOTOX Score (Day -5, before lymphodepletion)

Predicts risk of prolonged severe neutropenia (>=14 days). Five components measured before lymphodepletion:

| Component | Threshold | Points |
|-----------|-----------|--------|
| ANC | Low (threshold determined by Youden optimization) | 0-1 |
| Hemoglobin | Low | 0-1 |
| Platelet count | Low (double-weighted: sensitivity cutoff = +1, specificity cutoff = +1) | 0-2 |
| CRP | Elevated | 0-1 |
| Ferritin | Elevated (double-weighted: sensitivity cutoff = +1, specificity cutoff = +1) | 0-2 |

**Risk stratification:**
- Score 0-1: LOW risk (median neutropenia ~7 days, 95% CI 6-10 days)
- Score >=2: HIGH risk (median neutropenia ~16.5 days, 95% CI 13-43 days)

**Sensitivity:** 95% at threshold of 2; validated AUC 0.89

#### EASIX Baseline

```
EASIX = (LDH [U/L] x Creatinine [mg/dL]) / Platelets [10^9/L]
```

Endothelial Activation and Stress Index. Predicts CRS/ICANS severity.

#### Modified EASIX (m-EASIX)

```
m-EASIX = (LDH [U/L] x CRP [mg/dL]) / Platelets [10^9/L]
```

Substitutes CRP for creatinine. m-EASIX may outperform EASIX for predicting severe CRS (AUC ~80% at lymphodepletion timepoint).

### Pre-Infusion Vitals and Assessment

| Assessment | Frequency | Notes |
|------------|-----------|-------|
| Vital signs (T, HR, BP, RR, SpO2) | q4h during lymphodepletion | Baseline trending |
| Weight | Daily | Fluid balance |
| Neurological baseline (ICE score) | Once (Day -1 or Day 0) | Establish patient's baseline cognition |
| Performance status (ECOG/KPS) | Once | Functional baseline |
| Cardiac assessment (ECG, echo if indicated) | Per institutional protocol | Cardiac function baseline |
| Infection screening | At admission | Dental, skin, urinalysis, blood cultures if febrile |

### Dashboard UI: Pre-Infusion View

**Should display:**
- CAR-HEMATOTOX score with risk category (color-coded: green/red)
- EASIX and m-EASIX baseline values
- All baseline labs with abnormal flagging
- Lymphodepletion regimen and schedule
- Countdown to infusion day
- Checklist of required pre-infusion items (labs drawn, virology cleared, consent documented, tocilizumab on hand)

---

## 2. Day 1 Post-Infusion Monitoring

### What Is Checked

| Parameter | Frequency | Rationale |
|-----------|-----------|-----------|
| Temperature | q4h (minimum) | Fever >=38.0C is the hallmark of CRS onset |
| Heart rate, BP, RR, SpO2 | q4h | Hemodynamic instability = CRS grade escalation |
| Neurological assessment (ICE score) | q8-12h (twice daily) | Early ICANS detection |
| Handwriting sample | q8h (three times daily) | Sensitive early sign of neurotoxicity |
| Fluid intake/output | Continuous | Volume status for CRS management |
| Weight | Daily | Capillary leak assessment |

### Day 1 Labs

| Test | Frequency | Key Thresholds |
|------|-----------|----------------|
| CBC with differential | Daily | ANC trending |
| CRP | Daily | Rising CRP = inflammatory activation |
| Ferritin | Daily | >500 and rising = concerning; >10,000 = HLH concern |
| LDH | Daily | EASIX calculation; tumor lysis |
| CMP (including creatinine) | Daily | Organ function; EASIX calculation |
| Fibrinogen | Daily | <150 mg/dL = coagulopathy concern |
| Coagulation (PT/INR) | Daily | DIC screening |

### Early Warning Signs (Day 1)

| Sign | Significance | Action |
|------|-------------|--------|
| Fever >=38.0C | CRS Grade 1 onset | Begin CRS grading; increase monitoring |
| Fever >=38.9C within 36h | Hay classifier trigger | Draw MCP-1 level |
| Tachycardia (HR >100) | Possible early hemodynamic compromise | Assess volume status |
| Hypotension (SBP <90) | CRS Grade 2+ | Fluid bolus; consider tocilizumab |
| Any cognitive change | Possible early ICANS | Formal ICE score; alert physician |

### Hay Classifier (Early CRS Prediction)

Two-step algorithm for predicting severe (Grade >=4) CRS:

1. **Step 1:** Fever >=38.9C within 36 hours of infusion?
   - No -> Low risk for severe CRS (continue standard monitoring)
   - Yes -> Proceed to Step 2
2. **Step 2:** Serum MCP-1 >=1343.5 pg/mL?
   - No -> Low risk
   - Yes -> HIGH risk for Grade >=4 CRS (sensitivity 100%, specificity 95%)

**Dashboard implication:** System should automatically flag patients with early high fever and prompt MCP-1 order if not already drawn.

### Dashboard UI: Day 1 View

**Should display:**
- Real-time vital signs with trend graphs (last 24h)
- CRS grade indicator (currently Grade 0/1/2/3/4)
- Hay classifier status (not triggered / Step 1 triggered / HIGH RISK)
- EASIX and m-EASIX recalculated with Day +1 labs
- Lab trend sparklines (CRP, ferritin, fibrinogen)
- ICE score trend
- Time since infusion (hours)

---

## 3. Active CRS Monitoring (Day 1-14)

### ASTCT CRS Grading Criteria (2019 Consensus)

| Grade | Fever (>=38C) | Hypotension | Hypoxia |
|-------|---------------|-------------|---------|
| 1 | Yes | No | No |
| 2 | Yes | Responsive to fluids and/or low-dose vasopressor | Requires low-flow O2 (<=6L NC) |
| 3 | Yes | Requires vasopressor (with or without vasopressin) | Requires high-flow NC, facemask, nonrebreather, or Venturi mask |
| 4 | Yes | Requires multiple vasopressors (excluding vasopressin) | Requires positive pressure ventilation (CPAP, BiPAP, intubation) |

**Key rule:** Grade is determined by the MOST SEVERE parameter. Fever is required for all grades but alone defines Grade 1.

### CRS Peak Timeline

- **Typical onset:** Day 1-3 post-infusion
- **Typical peak:** Day 3-7
- **Typical resolution:** Day 7-14
- **Median onset:** ~2-3 days post-infusion (varies by product)

### Labs During Active CRS

| Test | Frequency | Purpose |
|------|-----------|---------|
| CBC with diff | Daily | Cytopenias, neutrophil nadir |
| CRP | Daily (q12h if Grade >=2) | Inflammation trend; m-EASIX |
| Ferritin | Daily (q12h if Grade >=2) | HLH screening; severity marker |
| LDH | Daily | EASIX; hemolysis; tumor lysis |
| Creatinine, BUN | Daily | Renal function; EASIX |
| AST/ALT, bilirubin | Daily | Hepatotoxicity |
| Fibrinogen | Daily (q12h if Grade >=2) | Coagulopathy; <150 = action threshold |
| Triglycerides | q48h (daily if HLH suspected) | HScore component |
| D-dimer | Daily if coagulopathy suspected | DIC screening |
| PT/INR, aPTT | Daily | Coagulopathy |
| IL-6 (if available) | q24-48h | CRS biomarker |
| Procalcitonin | As needed | Distinguish infection from CRS |

### EASIX/m-EASIX Trending

Recalculate EASIX and m-EASIX daily during active CRS:

```
EASIX  = (LDH x Creatinine) / Platelets
m-EASIX = (LDH x CRP) / Platelets
```

**Predictive timepoints:**
- Day -1 (pre-infusion): Baseline prediction
- Day +1: Early post-infusion risk
- Day +3: Best predictor of ICANS (any grade and severe)

### CRS Treatment Escalation Protocol

#### Grade 1 CRS
- **Intervention:** Supportive care only
- Acetaminophen for fever
- IV fluids for hydration
- Monitor q4h vitals
- **No tocilizumab or steroids**

#### Grade 2 CRS
- **First-line:** Tocilizumab 8 mg/kg IV (max 800 mg) over 1 hour
  - May repeat once after 8 hours if no improvement
  - Maximum 3 doses in 24 hours; maximum 4 doses total
- **If no response to tocilizumab (1-2 hours):** Add dexamethasone 10 mg IV q6h
- IV fluids; 1-2 fluid boluses for hypotension
- Low-flow supplemental O2 as needed
- Increase vitals monitoring to q2-4h

#### Grade 3 CRS
- **Tocilizumab** (if not already given): 8 mg/kg IV
- **Dexamethasone** 10 mg IV q6h
- Vasopressor support (single agent)
- High-flow O2 or non-invasive ventilation
- **ICU transfer**
- Continuous hemodynamic monitoring
- Consider methylprednisolone 1-2 mg/kg if refractory

#### Grade 4 CRS
- **Tocilizumab** (if doses remain)
- **Methylprednisolone** 1000 mg IV daily x3 days (pulse dose)
- Multiple vasopressors
- Mechanical ventilation
- **ICU mandatory**
- Consider third-line agents if refractory:
  - Anakinra (IL-1 receptor antagonist) 100-200 mg SC/IV q6-8h
  - Siltuximab (anti-IL-6, if tocilizumab unavailable)
  - Ruxolitinib (JAK inhibitor)

#### Refractory CRS (no improvement after 2 doses tocilizumab + steroids)
- Anakinra escalation
- Siltuximab consideration
- High-dose methylprednisolone (1 g/day x3)
- Evaluate for IEC-HS (see Section 5)

### Dashboard UI: CRS Monitoring View

**Should display:**
- Current CRS grade (large, color-coded badge: green/yellow/orange/red)
- CRS grade timeline (horizontal bar showing grade changes over time)
- Vital signs trend (T, BP, HR, SpO2) with threshold lines
- Tocilizumab dose tracker (doses given / max 4, time of each dose)
- Steroid administration log
- Lab trends: CRP, ferritin, fibrinogen, LDH (sparklines with thresholds)
- EASIX/m-EASIX daily trend chart
- O2 requirement trend
- Vasopressor status and doses
- Escalation recommendation engine (based on current grade and trajectory)

---

## 4. ICANS Assessment

### ICE Score (Immune Effector Cell-Associated Encephalopathy Score)

10-point assessment tool. **Higher ICE score = better function = lower ICANS grade.**

| Domain | Task | Points |
|--------|------|--------|
| **Orientation** | Year, month, city, hospital | 4 points (1 each) |
| **Naming** | Name 3 objects | 3 points (1 each) |
| **Writing** | Write a standard sentence | 1 point |
| **Attention** | Count backwards from 100 by 10 | 1 point |
| **Commands** | Follow a simple command (e.g., "show me 2 fingers") | 1 point |
| | **Total** | **10 points** |

### ICANS Grading (ASTCT Consensus)

| Parameter | Grade 1 | Grade 2 | Grade 3 | Grade 4 |
|-----------|---------|---------|---------|---------|
| ICE score | 7-9 | 3-6 | 0-2 | 0 (patient unarousable) |
| Depressed consciousness | Awakens spontaneously | Awakens to voice | Awakens only to tactile stimulus | Unarousable OR requires vigorous/repetitive stimuli |
| Seizure | -- | -- | Any clinical seizure (focal or generalized) that resolves rapidly, OR non-convulsive seizures on EEG that resolve with intervention | Life-threatening prolonged seizure (>5 min); OR repetitive clinical or electrical seizures without return to baseline |
| Motor findings | -- | -- | -- | Deep focal motor weakness |
| Elevated ICP / cerebral edema | -- | -- | Focal/local edema on imaging | Diffuse cerebral edema on imaging; decerebrate/decorticate posturing; CN VI palsy; papilledema; Cushing's triad |

**Grading rule:** ICANS grade = highest (most severe) grade across ALL domains.

### ICANS Timing Relative to CRS

- **Typical onset:** Day 3-7 post-infusion (usually after CRS onset)
- **Can occur concurrently with CRS** or after CRS resolution
- **Peak:** Day 5-10
- **Duration:** Usually 2-4 weeks; most resolve within 21 days
- **Important:** ICANS can occur WITHOUT preceding CRS (though uncommon)

### ICANS Management

| Grade | Management |
|-------|------------|
| Grade 1 | Supportive care; hold oral medications that increase aspiration risk; seizure prophylaxis (levetiracetam 500-750 mg BID); monitor q8h ICE |
| Grade 2 | Dexamethasone 10 mg IV q6h; continue seizure prophylaxis; increase ICE assessment to q4-6h; consider neurology consult |
| Grade 3 | ICU transfer; dexamethasone 10 mg IV q6h (or methylprednisolone 1 mg/kg BID); EEG monitoring; CT/MRI head; neurology consult; consider intubation for airway protection |
| Grade 4 | ICU; methylprednisolone 1000 mg IV daily x3 days; continuous EEG; urgent neuroimaging; evaluate for cerebral edema; consider mannitol/hypertonic saline if ICP elevated |

**Critical note:** Tocilizumab does NOT treat ICANS and may worsen it. Steroids are the mainstay of ICANS treatment.

### Assessment Frequency

| Situation | ICE Score Frequency | Writing Assessment |
|-----------|--------------------|--------------------|
| No ICANS (baseline) | q12h (twice daily) | q8h (three times daily) |
| Grade 1 ICANS | q8h | q8h |
| Grade 2 ICANS | q4-6h | q4-6h |
| Grade 3-4 ICANS | q2-4h (if arousable) | As tolerated |

### Dashboard UI: ICANS View

**Should display:**
- Current ICE score with breakdown by domain (visual: 10-point bar)
- ICE score trend over time
- Current ICANS grade (color-coded badge)
- Handwriting sample log (timestamped photo captures or quality ratings)
- Level of consciousness indicator
- Seizure event log
- Steroid dosing timeline
- Neuroimaging results/status
- EEG status (if ordered)
- Relationship to CRS timeline (overlay CRS grade and ICANS grade on same timeline)

---

## 5. HLH / IEC-HS Screening

### Terminology

- **HLH:** Hemophagocytic Lymphohistiocytosis (traditional syndrome)
- **IEC-HS:** Immune Effector Cell-Associated Hemophagocytic Lymphohistiocytosis-like Syndrome (ASTCT terminology for CAR-T associated HLH-like presentation)

### When to Suspect IEC-HS

IEC-HS typically presents AFTER CRS has begun to resolve (distinguishing feature). Suspect when:

- Ferritin >10,000 ng/mL (and rising)
- Ferritin doubling time <48 hours
- Fibrinogen <150 mg/dL (or rapidly falling)
- Triglycerides >265 mg/dL (>3 mmol/L)
- New or worsening cytopenias (beyond expected from lymphodepletion)
- AST/ALT rising disproportionately
- Persistent/recurrent fevers AFTER CRS resolution
- Splenomegaly (new or worsening)

### IEC-HS vs CRS: Key Distinctions

| Feature | CRS | IEC-HS |
|---------|-----|--------|
| Timing | Day 1-7 typically | After CRS onset, often during resolution |
| Fever pattern | Continuous during CRS | Persistent/recurrent after CRS resolves |
| Ferritin | Elevated but usually <10,000 | Often >10,000, rapidly rising |
| Fibrinogen | Mildly decreased | Markedly decreased (<150) |
| Triglycerides | Often normal | Elevated |
| Cytopenias | Expected from lymphodepletion | New/worsening beyond expected |
| Hepatotoxicity | Mild | Often prominent (AST/ALT elevation) |
| Response to tocilizumab | Usually responsive | Often refractory |

### HScore Components (for HLH Probability Calculation)

| Variable | Criteria | Points |
|----------|----------|--------|
| Known immunosuppression | No / Yes | 0 / 18 |
| Temperature | <=38.4C / 38.4-39.4C / >39.4C | 0 / 33 / 49 |
| Organomegaly | None / Hepatomegaly OR splenomegaly / Both | 0 / 23 / 38 |
| Cytopenias (lineages affected) | 1 / 2 / 3 | 0 / 24 / 34 |
| Ferritin (ng/mL) | <2,000 / 2,000-6,000 / >6,000 | 0 / 35 / 50 |
| Triglycerides (mmol/L) | <1.5 / 1.5-4.0 / >4.0 | 0 / 44 / 64 |
| Fibrinogen (g/L) | >2.5 / <=2.5 | 0 / 30 |
| AST (IU/L) | <30 / >=30 | 0 / 19 |
| Hemophagocytosis on BM aspirate | No / Yes | 0 / 35 |

**HScore interpretation:**
- <=90: <1% probability of HLH
- 91-168: Intermediate probability
- >=169: Generally considered diagnostic threshold (~93% sensitivity, ~86% specificity)
- >=250: >99% probability

**Important caveat for CAR-T patients:** Traditional HLH criteria (HLH-2004 and HScore) have limitations in the post-CAR-T setting. HLH-2004 has frequent false negatives; HScore has high false positive rates in this population. Use in conjunction with clinical judgment and the ASTCT IEC-HS framework.

### IEC-HS ASTCT Diagnostic Framework

Three required features:
1. **Signs of macrophage activation or HLH** (elevated ferritin, cytopenias, coagulopathy)
2. **Direct relationship to IEC therapy** (temporal association)
3. **New onset or worsening of:** cytopenias, elevated ferritin, coagulopathy (low fibrinogen), and/or liver enzyme elevation

**Chronological independence from CRS** is a key diagnostic feature.

### Ferritin/Fibrinogen/Triglyceride Patterns

| Marker | CRS Pattern | IEC-HS Pattern | Action Threshold |
|--------|-------------|----------------|------------------|
| Ferritin | Rises with CRS, peaks at Grade 2-3, declines with resolution | Continues rising or re-rises after CRS resolution; >10,000 | >10,000 ng/mL: HIGH alert |
| Fibrinogen | Mild decrease during CRS | Progressive decline; <150 mg/dL | <150 mg/dL: Transfuse cryoprecipitate; evaluate for IEC-HS |
| Triglycerides | Usually normal-mildly elevated | Rising, often >265 mg/dL | >265 mg/dL with other features: evaluate for IEC-HS |

### IEC-HS Management

- **Etoposide** (50-100 mg/m2): Consider for severe/refractory IEC-HS
- **Anakinra** (100 mg SC/IV q6-12h): IL-1 blockade
- **Ruxolitinib** (JAK inhibitor): For refractory cases
- **Emapalumab** (anti-IFN-gamma): Severe refractory HLH
- **High-dose steroids:** Methylprednisolone 1-2 mg/kg or pulse dosing
- **Supportive care:** Fibrinogen replacement, platelet transfusion, fresh frozen plasma

### Dashboard UI: HLH/IEC-HS View

**Should display:**
- HScore calculator (auto-populated from labs; manually enter physical exam findings)
- HScore probability gauge (0-100% probability visualization)
- Ferritin trend chart with >10,000 threshold line
- Fibrinogen trend chart with <150 threshold line
- Triglyceride trend chart
- CRS-vs-IEC-HS timeline differentiator (show CRS resolution point and persistence of features)
- Alert system: Auto-flag when ferritin >10,000 AND fibrinogen <150
- Cytopenia depth chart (ANC, Hgb, Plt over time with expected recovery overlay)

---

## 6. Hematologic Recovery Tracking

### CAR-HEMATOTOX Score Interpretation for Recovery

| Risk Category | Expected Neutropenia Duration | Infection Risk | Transfusion Need |
|---------------|-------------------------------|----------------|------------------|
| Low (Score 0-1) | ~7 days (median) | Moderate | Lower |
| High (Score >=2) | ~16.5 days (median), range 13-43 days | Very high | Higher |

### Expected CBC Recovery Timelines

| Parameter | Nadir Timing | Expected Recovery (Low Risk) | Expected Recovery (High Risk) | Worry Threshold |
|-----------|-------------|------------------------------|-------------------------------|-----------------|
| ANC | Day 5-10 | Day 14-21 | Day 21-42+ | ANC <500 at Day +30 |
| Platelets | Day 7-14 | Day 21-30 | Day 30-60+ | Plt <50,000 at Day +30 |
| Hemoglobin | Day 7-14 | Day 21-30 | Day 30-60 | Transfusion-dependent at Day +30 |
| Lymphocytes | Day 0-7 | Months | Months | Prolonged lymphopenia expected (B-cell aplasia from anti-CD19) |

### Biphasic Cytopenia Pattern

Many CAR-T patients exhibit a biphasic pattern:
1. **Phase 1 (Early):** Day 0-14, related to lymphodepleting chemotherapy
2. **Recovery phase:** Brief improvement around Day 14-21
3. **Phase 2 (Late):** Day 21-42+, immune-mediated (associated with higher CRS grade and higher CAR-HEMATOTOX score)

**Dashboard should visualize this biphasic pattern** with expected recovery corridors based on CAR-HEMATOTOX risk category.

### Prolonged Cytopenias (Day 30+)

When to worry:
- **ANC <500/uL at Day +30:** Evaluate for bone marrow failure, infection, disease progression
- **Platelets <20,000 at Day +30:** Evaluate BM; consider thrombopoietin receptor agonist
- **Transfusion dependence at Day +30:** Bone marrow biopsy

Evaluation for prolonged cytopenias:
- Bone marrow biopsy with aspirate
- Flow cytometry (disease status)
- Cytogenetics/molecular studies
- Viral reactivation panel (CMV, EBV, HHV-6, parvovirus B19)
- Iron studies, B12, folate

### G-CSF Considerations

| Factor | Guidance |
|--------|----------|
| Timing | Generally avoid G-CSF in first 14-21 days post-infusion (theoretical concern about CAR-T expansion interference) |
| When to use | ANC <500 with active or high-risk infection, typically after Day +14-21 |
| Product | Filgrastim 5 mcg/kg/day or pegfilgrastim (single dose) |
| Controversy | Growing evidence that G-CSF after Day +14 does not impair CAR-T efficacy; some centers use earlier |
| Monitor | CBC daily while on G-CSF until ANC recovery |

### Dashboard UI: Hematologic Recovery View

**Should display:**
- CBC trend charts (ANC, Hgb, Plt) with expected recovery corridors (shaded bands based on CAR-HEMATOTOX risk)
- Day count since infusion (prominent)
- CAR-HEMATOTOX risk category (persistent display)
- Biphasic pattern overlay (expected nadir/recovery phases)
- Transfusion log (RBC, platelets, cryo)
- G-CSF administration tracker
- Infection event overlay on CBC timeline
- Alert: Flag if counts below expected at recovery milestones (Day +14, +21, +30)
- Bone marrow biopsy status/results if obtained

---

## 7. Discharge Planning

### Discharge Criteria

All of the following should be met:

| Criterion | Requirement |
|-----------|-------------|
| CRS | Resolved to Grade 0 (no fever, hemodynamically stable, no supplemental O2) for >=24 hours |
| ICANS | Resolved to Grade 0-1 (ICE score >=7) for >=24 hours |
| Hemodynamics | Off vasopressors >=24 hours |
| Respiratory | Off supplemental O2 >=24 hours |
| Neurological | Stable or improving; can perform self-care |
| Infection | No active uncontrolled infection |
| Oral intake | Tolerating oral medications and adequate PO intake |
| Fever | Afebrile (no temp >=38.0C for >=24-48 hours off antipyretics) |
| Labs | Stable or improving (no concerning trends in ferritin, fibrinogen, LFTs) |
| Caregiver | Dedicated 24/7 caregiver available |
| Proximity | Patient resides within 1-2 hours (per institution) of treatment center for >=30 days |
| Education | Patient/caregiver educated on warning signs requiring immediate return |

### Outpatient Monitoring Schedule

| Timeframe | Visit Frequency | Labs | Assessments |
|-----------|----------------|------|-------------|
| Week 1-2 post-discharge | Daily clinic visits | CBC, CMP, CRP, ferritin | Vitals, ICE score, symptom review |
| Week 3-4 | 2-3x per week | CBC, CMP | Vitals, symptom review |
| Month 2-3 | Weekly | CBC, CMP, immunoglobulins | Symptom review, disease reassessment |
| Month 3-6 | Every 2-4 weeks | CBC, immunoglobulins | Disease monitoring (PET/CT per protocol) |
| Month 6-12 | Monthly | CBC, immunoglobulins | Long-term follow-up |
| Year 1+ | Per institutional protocol | Annual labs | LTFU per FACT/ASTCT guidelines |

### Readmission Risk

- **30-day readmission rate:** ~24%
- **Median time to readmission:** 7 days post-discharge
- **Peak risk window:** Day 7-14 post-discharge (Day 14-28 post-infusion)

**Top reasons for readmission:**
1. Cancer/treatment-related complications (~22%)
2. Sepsis/infection (~18%)
3. Neurologic events (~15%)
4. Neutropenia/pancytopenia (~11%)
5. Fever, hypotension, or hypoxia (~8%)

### Red Flags for Immediate Return

Patients/caregivers must be educated on:
- Fever >=38.0C
- New confusion, difficulty speaking, or writing changes
- Seizure activity
- Difficulty breathing or new O2 requirement
- Persistent vomiting/inability to take medications
- New or worsening bleeding
- Signs of infection (chills, rigors, wound changes)

### Dashboard UI: Discharge Planning View

**Should display:**
- Discharge readiness checklist (each criterion with green/red status)
- Outstanding items preventing discharge
- Outpatient monitoring schedule (auto-generated calendar)
- Readmission risk score (based on CRS grade, ICANS history, cytopenia depth)
- Patient education completion tracker
- Caregiver documentation status
- Follow-up appointment scheduling status
- Day counter since infusion and since discharge

---

## 8. Decision Support: Anticipatory Orders

### Pre-Infusion (Day -7 to Day 0)

| Anticipatory Action | Trigger | Order |
|--------------------|---------|-------|
| Baseline labs panel | Admission | CBC, CMP, LDH, ferritin, CRP, fibrinogen, triglycerides, coags, virology panel, immunoglobulins, uric acid |
| CAR-HEMATOTOX calculation | Labs resulted (Day -5) | Auto-calculate and display risk score |
| EASIX/m-EASIX baseline | Labs resulted | Auto-calculate |
| Tocilizumab availability | Day -1 | Verify 2-4 doses tocilizumab available in pharmacy (not dispensed, just verified) |
| Seizure prophylaxis standing order | Day -1 | Levetiracetam 500-750 mg BID ready to initiate |
| Emergency medication kit | Day 0 | Tocilizumab, dexamethasone, epinephrine, diphenhydramine at bedside |

### Day 1-3 Post-Infusion

| Anticipatory Action | Trigger | Order |
|--------------------|---------|-------|
| MCP-1 level | Fever >=38.9C within 36h | STAT MCP-1 (Hay classifier Step 2) |
| Blood cultures x2 | Any fever >=38.0C | Peripheral + central line cultures |
| CRS lab panel | Fever onset | CRP, ferritin, fibrinogen, LDH, CMP (q12-24h) |
| Tocilizumab | CRS Grade 2 | Pre-authorize tocilizumab 8 mg/kg IV |
| ICU consult | CRS Grade 2 worsening | Pre-emptive ICU notification |
| Repeat EASIX/m-EASIX | Day +1 labs resulted | Auto-calculate trend |

### Day 3-7 (Peak CRS/ICANS Risk)

| Anticipatory Action | Trigger | Order |
|--------------------|---------|-------|
| Neurology consult | ICE score drop >=3 points from baseline or ICANS Grade 2 | Consult order |
| EEG | ICANS Grade 3 or seizure | Continuous EEG monitoring |
| CT/MRI head | ICANS Grade 3, new focal deficit, or concern for cerebral edema | STAT imaging |
| Dexamethasone | ICANS Grade 2 | Dexamethasone 10 mg IV q6h |
| HLH screening panel | Ferritin >10,000 OR rising ferritin after CRS resolution | Triglycerides, fibrinogen, AST, LDH, sIL-2R |
| HScore calculation | HLH screening labs resulted | Auto-calculate |
| Hematology/HLH consult | HScore >=169 | Consult order |

### Day 7-14 (Late Complications)

| Anticipatory Action | Trigger | Order |
|--------------------|---------|-------|
| Viral reactivation panel | Day +7 (routine) or unexplained fever | CMV, EBV, HHV-6, adenovirus PCR |
| G-CSF consideration | ANC <500 at Day +14 with infection | Filgrastim 5 mcg/kg/day order |
| Bone marrow biopsy | Cytopenias not recovering at Day +28-30 | BM biopsy/aspirate order |
| IVIG | IgG <400 mg/dL with infection | IVIG replacement |

---

## 9. Standard Monitoring Frequencies

### Vital Signs

| Phase | Frequency | Escalation Trigger |
|-------|-----------|-------------------|
| Lymphodepletion (Day -5 to -3) | q4h | Fever, hypotension |
| Rest period (Day -2 to -1) | q4h | Fever |
| Day 0 (infusion day) | q1h during infusion, then q4h | Any infusion reaction |
| Day 1-3 (early monitoring) | q4h (q2h if CRS Grade >=1) | CRS grade escalation |
| Active CRS (any grade) | q2-4h (q1h if Grade >=3) | Hemodynamic instability |
| Active ICANS | q2-4h (continuous monitoring if Grade >=3) | Neurological deterioration |
| Recovery/pre-discharge | q4-6h | New symptoms |
| Outpatient | Per visit (daily initially) | Any new fever or symptoms |

### Laboratory Tests

| Test | Baseline | Day 0-7 | Day 7-14 | Day 14-30 | Outpatient |
|------|----------|---------|----------|-----------|------------|
| CBC with diff | Daily | Daily | Daily | 2-3x/week | Weekly -> biweekly |
| CMP | Daily | Daily | Daily | 2-3x/week | Weekly -> biweekly |
| CRP | Once | Daily | Daily (q12h if CRS active) | 2-3x/week | Per visit |
| Ferritin | Once | Daily | Daily (q12h if >=Grade 2 CRS) | 2-3x/week | Weekly |
| Fibrinogen | Once | Daily | Daily | 2-3x/week | As needed |
| LDH | Once | Daily | Daily | 2-3x/week | Weekly |
| Triglycerides | Once | q48h | q48h (daily if HLH concern) | Weekly | As needed |
| PT/INR | Once | Daily | Daily | As needed | As needed |
| Virology panel | Once | -- | Day +7 | Day +14, +21, +28 | Monthly x3 |
| Immunoglobulins | Once | -- | -- | Day +28 | Monthly |
| Cytokines (IL-6, etc.) | Optional | q24-48h | As needed | -- | -- |

### Neurological Assessment (ICE Score)

| Phase | ICE Score Frequency | Writing Assessment |
|-------|--------------------|--------------------|
| Baseline | Once (Day -1 or Day 0) | Once |
| Day 1-14 (no ICANS) | q12h (twice daily) | q8h (three times daily) |
| ICANS Grade 1 | q8h | q8h |
| ICANS Grade 2 | q4-6h | q4-6h |
| ICANS Grade 3-4 | q2-4h (if arousable) | As tolerated |
| Post-ICANS resolution | q12h x48h, then daily until discharge | Daily |

---

## 10. Key Action Thresholds

### Temperature

| Threshold | Action |
|-----------|--------|
| >=38.0C (100.4F) | CRS Grade 1; obtain blood cultures; start CRS monitoring protocol |
| >=38.9C (102.0F) within 36h of infusion | Hay classifier Step 1 triggered; order MCP-1 level |
| >=39.4C (102.9F) | High HScore temperature component; escalate monitoring |
| Persistent fever after CRS resolution | Evaluate for infection vs IEC-HS |

### Hemodynamic

| Threshold | Action |
|-----------|--------|
| SBP <90 mmHg | CRS Grade 2 (if responsive to fluids); assess for Grade 3-4 |
| Requiring 1 vasopressor | CRS Grade 3; ICU transfer |
| Requiring 2+ vasopressors | CRS Grade 4; ICU mandatory |
| SpO2 <94% on room air | Supplemental O2; assess CRS grade |
| Requiring >6L NC | CRS Grade 3 |
| Requiring positive pressure ventilation | CRS Grade 4 |

### Laboratory

| Marker | Threshold | Action |
|--------|-----------|--------|
| Ferritin | >10,000 ng/mL | HIGH ALERT: Evaluate for IEC-HS; increase monitoring to q12h |
| Ferritin | Doubling in <48 hours | Alert: Rapid rise pattern; evaluate for IEC-HS |
| Fibrinogen | <200 mg/dL | Warning: Trending down; increase monitoring |
| Fibrinogen | <150 mg/dL | ACTION: Transfuse cryoprecipitate; evaluate for DIC/IEC-HS |
| Fibrinogen | <100 mg/dL | CRITICAL: Active coagulopathy; urgent evaluation |
| CRP | >100 mg/L | Significant inflammation; correlate with CRS grade |
| CRP | Rising trend after initial decline | Possible secondary process (infection, IEC-HS) |
| LDH | >2x ULN and rising | Evaluate for hemolysis, tumor lysis, disease progression |
| Triglycerides | >265 mg/dL (>3 mmol/L) | HLH component; evaluate in context of other HScore criteria |
| Triglycerides | >354 mg/dL (>4 mmol/L) | High HScore component; increased HLH probability |
| ANC | <500/uL | Neutropenic precautions; monitor for infection |
| ANC | <500/uL at Day +14 with fever/infection | Consider G-CSF |
| ANC | <500/uL at Day +30 | Prolonged cytopenia evaluation; consider BM biopsy |
| Platelets | <20,000/uL | Transfusion threshold (may adjust for bleeding risk) |
| Platelets | <50,000/uL at Day +30 | Prolonged cytopenia evaluation |
| IgG | <400 mg/dL | IVIG replacement if recurrent infections |
| Creatinine | >1.5x baseline | Evaluate for renal injury (CRS-related or nephrotoxicity) |
| AST/ALT | >5x ULN | Hepatotoxicity evaluation; HLH screening |
| MCP-1 | >=1343.5 pg/mL (with fever >=38.9C) | Hay classifier POSITIVE: HIGH risk for severe CRS |

### Neurological (ICE Score)

| Threshold | Action |
|-----------|--------|
| ICE 7-9 (drop from 10) | ICANS Grade 1; initiate seizure prophylaxis; increase monitoring |
| ICE 3-6 | ICANS Grade 2; dexamethasone; neurology consult |
| ICE 0-2 | ICANS Grade 3 (SEVERE); ICU transfer; high-dose steroids; EEG; imaging |
| ICE 0 + unarousable | ICANS Grade 4; ICU; pulse steroids; urgent imaging; evaluate for cerebral edema |
| Any seizure | Minimum ICANS Grade 3; ICU; EEG monitoring; antiepileptics |

### HScore

| Threshold | Probability | Action |
|-----------|-------------|--------|
| <=90 | <1% HLH | Low probability; continue routine monitoring |
| 91-168 | Intermediate | Close monitoring; consider additional workup |
| >=169 | High (>54%) | Probable HLH/IEC-HS; initiate treatment |
| >=250 | Very high (>99%) | Definitive HLH/IEC-HS; aggressive treatment |

---

## 11. Role-Based Information Needs

### Attending Physician

**Primary needs:** Decision-making data, risk stratification, treatment escalation

| Information Element | Priority | Display |
|--------------------|----------|---------|
| Current CRS grade + trajectory | Critical | Large badge + trend arrow |
| Current ICANS grade + ICE score | Critical | Large badge + trend |
| EASIX/m-EASIX trend | High | Trend chart |
| CAR-HEMATOTOX risk category | High | Persistent display |
| Hay classifier status | High (Day 0-3) | Alert banner |
| HScore (if applicable) | High | Calculator with auto-populated values |
| Lab trend dashboard (CRP, ferritin, fibrinogen, LDH) | High | Sparklines |
| Tocilizumab doses used/remaining | High | Counter (X/4) |
| Steroid cumulative dosing | High | Running total |
| Vasopressor status/doses | High | Current status |
| O2 requirements | High | Current + trend |
| CBC recovery trajectory vs expected | Medium | Chart with corridors |
| Treatment escalation recommendations | Medium | Algorithm-based suggestions |
| Discharge readiness checklist | Medium | Checklist with status |

### Clinical Pharmacist

**Primary needs:** Medication management, drug interactions, dosing optimization

| Information Element | Priority | Display |
|--------------------|----------|---------|
| Tocilizumab dosing (weight-based) and administration times | Critical | Dose tracker with timestamps |
| Steroid dosing schedule and cumulative exposure | Critical | Timeline + running dose |
| Seizure prophylaxis status (levetiracetam) | High | Active medication status |
| G-CSF eligibility (day count, ANC) | High | Decision support flag |
| Drug interactions with concurrent medications | High | Alert system |
| Anakinra/siltuximab dosing (if refractory) | High | Protocol reference |
| IVIG replacement eligibility (IgG level) | Medium | Lab value + threshold |
| Antimicrobial prophylaxis status | Medium | Active med list |
| Renal function for dose adjustments | Medium | Creatinine trend |
| Hepatic function for dose adjustments | Medium | LFT trend |
| Tumor lysis prophylaxis (allopurinol, rasburicase) | Medium | Active med status |
| Medication reconciliation at discharge | Medium | Discharge med list |

### Nurse (Bedside / Clinic)

**Primary needs:** Assessment tools, monitoring schedules, escalation triggers

| Information Element | Priority | Display |
|--------------------|----------|---------|
| Vital signs entry and trend display | Critical | Real-time charting |
| ICE score assessment tool (guided entry) | Critical | Interactive calculator |
| Writing sample documentation | Critical | Photo capture / quality rating |
| CRS grading guide (quick reference) | Critical | Always-accessible reference card |
| Current monitoring frequency schedule | Critical | Timer / countdown to next assessment |
| Alert thresholds for immediate physician notification | Critical | Color-coded threshold display |
| Fluid balance (I&O) | High | Running totals |
| Medication administration schedule | High | MAR integration |
| Patient weight (daily) | High | Trend |
| Temperature trend (fever pattern) | High | Graph with threshold lines |
| Neurological assessment checklist | High | Structured form |
| Infusion reaction monitoring (Day 0) | High | Protocol checklist |
| Patient education documentation | Medium | Checklist |
| Caregiver assessment and education status | Medium | Status tracker |
| Fall risk assessment (ICANS-related) | Medium | Risk score |

---

## Appendix A: Scoring Model Quick Reference

### ASTCT CRS Grade Summary
```
Grade 1: Fever only (>=38C)
Grade 2: Fever + hypotension (fluid-responsive) and/or low-flow O2 (<=6L)
Grade 3: Fever + vasopressor(s) and/or high-flow O2/facemask
Grade 4: Fever + multiple vasopressors and/or positive pressure ventilation
```

### ICE Score Quick Reference
```
Orientation (4 pts): Year? Month? City? Hospital?
Naming (3 pts):      Name 3 objects (e.g., point to clock, pen, button)
Writing (1 pt):      Write a standard sentence
Attention (1 pt):    Count backward from 100 by 10s
Commands (1 pt):     Follow simple command ("show me 2 fingers")
Total: 10 points
```

### EASIX Formula
```
EASIX   = (LDH [U/L] x Creatinine [mg/dL]) / Platelets [10^9/L]
m-EASIX = (LDH [U/L] x CRP [mg/dL]) / Platelets [10^9/L]
```

### Hay Classifier
```
Step 1: Fever >=38.9C within 36h of infusion? --> If yes, proceed
Step 2: MCP-1 >=1343.5 pg/mL? --> If yes, HIGH RISK (Grade >=4 CRS)
Sensitivity: 100% | Specificity: 95%
```

### CAR-HEMATOTOX Risk
```
Score 0-1: LOW risk  --> Median neutropenia ~7 days
Score >=2:  HIGH risk --> Median neutropenia ~16.5 days
```

### HScore Probability
```
<=90:   <1% HLH probability
91-168: Intermediate
>=169:  Probable (>54%)
>=250:  Very high (>99%)
```

---

## Appendix B: Dashboard Architecture Recommendations

### Critical Real-Time Displays

1. **Patient Header Bar:** Name, MRN, Day +X post-infusion, CRS Grade, ICANS Grade, CAR-HEMATOTOX risk
2. **Timeline View:** Horizontal timeline from Day -7 to current, showing infusion day, CRS episodes, ICANS episodes, interventions
3. **Vital Signs Panel:** Real-time T, HR, BP, RR, SpO2 with configurable threshold lines
4. **Lab Trend Panel:** Sparklines for CRP, ferritin, fibrinogen, LDH, CBC components
5. **Score Panel:** EASIX, m-EASIX, HScore (auto-calculated), ICE score trends
6. **Intervention Log:** Tocilizumab doses, steroid doses, vasopressors, O2 requirement, transfusions
7. **Alert Panel:** Active alerts with severity (info/warning/critical)

### Alert Priority Levels

| Level | Color | Examples |
|-------|-------|---------|
| INFO (blue) | Blue | New lab results available; scheduled assessment due |
| WARNING (yellow) | Yellow | CRP rising trend; ANC approaching 500; ICE score dropped 2 points |
| URGENT (orange) | Orange | CRS Grade 2; ferritin >5000; fibrinogen <200 |
| CRITICAL (red) | Red | CRS Grade 3-4; ICANS Grade 3-4; ferritin >10,000; Hay classifier positive; HScore >=169 |

### Workflow-Triggered Automations

| Trigger | System Action |
|---------|---------------|
| Fever >=38.0C documented | Auto-escalate monitoring frequency; prompt CRS grading; suggest blood cultures |
| CRS Grade >=2 | Auto-order CRS lab panel (CRP, ferritin, fibrinogen, LDH); notify attending; suggest tocilizumab |
| ICE score drops >=3 points | Alert attending; suggest dexamethasone if ICANS Grade >=2; suggest neurology consult |
| Ferritin >10,000 | Alert: IEC-HS screening; auto-order triglycerides if not recent; calculate HScore |
| ANC <500 at Day >=14 | Prompt G-CSF consideration; flag infection risk |
| All discharge criteria met | Generate discharge readiness notification; pre-populate discharge orders |

---

*Document version: 1.0*
*Sources: ASTCT 2019 Consensus Grading (Lee et al., BBMT 2019), Hay et al. Blood 2017 (CRS biomarker classification), Rejeski et al. Blood 2021 (CAR-HEMATOTOX), Fardet et al. Arthritis & Rheumatology 2014 (HScore), EBMT/EHA CAR-T Cell Handbook, ASCO Guideline JCO 2022 (immune-related AE management), Lancet Haematology 2024 (IEC hematotoxicity review).*
