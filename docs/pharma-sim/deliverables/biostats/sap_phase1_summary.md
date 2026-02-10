# Statistical Analysis Plan Summary: Phase I Anti-CD19 CAR-T in Refractory SLE

> **SIMULATED DOCUMENT** -- This is a simulated pharmaceutical deliverable produced by an AI agent
> operating in the Head of Biostatistics role. It is not based on proprietary data and does not
> represent actual regulatory submissions or clinical decisions.

**Document ID:** SAP-CART19-SLE-101-v1.0
**Protocol:** CART19-SLE-101
**Version:** 1.0
**Date:** 2026-02-09
**Author:** Biostatistics Agent (Simulated)
**Governing Guidance:** ICH E9 (Statistical Principles for Clinical Trials), ICH E9(R1) (Estimands and Sensitivity Analysis), ICH E4 (Dose-Response Information), FDA Guidance for Cellular and Gene Therapy Products

---

## Table of Contents

1. [Study Overview](#1-study-overview)
2. [Study Objectives and Endpoints](#2-study-objectives-and-endpoints)
3. [Study Design](#3-study-design)
4. [Dose-Limiting Toxicity Definition](#4-dose-limiting-toxicity-definition)
5. [Sample Size Justification](#5-sample-size-justification)
6. [Analysis Populations](#6-analysis-populations)
7. [Estimand Framework](#7-estimand-framework)
8. [Statistical Methods](#8-statistical-methods)
9. [Interim Analysis and DSMB](#9-interim-analysis-and-dsmb)
10. [Missing Data](#10-missing-data)
11. [References](#11-references)

---

## 1. Study Overview

| Parameter | Detail |
|-----------|--------|
| **Study ID** | CART19-SLE-101 |
| **Phase** | Phase I |
| **Design** | Open-label, single-arm, 3+3 dose escalation |
| **Indication** | Refractory systemic lupus erythematosus (SLE) |
| **Intervention** | Anti-CD19 CAR-T cell therapy (autologous) |
| **Dose Levels** | DL1: 0.5 x 10^6 CAR+ T cells/kg; DL2: 1.0 x 10^6/kg; DL3: 2.0 x 10^6/kg |
| **Conditioning** | Fludarabine 25 mg/m2 x 3 days + Cyclophosphamide 250 mg/m2 x 3 days |
| **Primary Objective** | Safety (DLT rate at each dose level) |
| **Sample Size** | 9--18 patients |
| **DLT Window** | Day 0 through Day 28 post-infusion |

---

## 2. Study Objectives and Endpoints

### 2.1 Primary Objective

**Objective:** To evaluate the safety and tolerability of anti-CD19 CAR-T cells and to determine the recommended Phase II dose (RP2D) in adults with refractory SLE.

**Primary Endpoint:** Incidence and severity of dose-limiting toxicities (DLTs) within 28 days of CAR-T cell infusion at each dose level.

### 2.2 Secondary Objectives

| Objective | Endpoint | Timepoint |
|-----------|----------|-----------|
| Preliminary efficacy | SRI-4 response rate | Week 24, Week 52 |
| Serological response | Anti-dsDNA normalization rate | Week 12, 24, 52 |
| Serological response | Complement (C3, C4) normalization rate | Week 12, 24, 52 |
| Disease activity | Change from baseline in SLEDAI-2K | Week 12, 24, 52 |
| Corticosteroid sparing | Proportion achieving prednisone <= 5 mg/day | Week 24, 52 |
| Pharmacokinetics | CAR-T cell expansion (Cmax, Tmax, AUC) | Days 0--28, then monthly |
| Pharmacodynamics | B-cell depletion and reconstitution kinetics | Weekly x 4, then monthly |

### 2.3 Exploratory Objectives

| Objective | Endpoint |
|-----------|----------|
| Biomarker discovery | Baseline and on-treatment cytokine profiles correlated with response/toxicity |
| Immune reconstitution | B-cell receptor (BCR) repertoire diversity at reconstitution vs. baseline |
| Predictive markers | Baseline SLEDAI-2K, anti-dsDNA titer, complement levels as predictors of response |

---

## 3. Study Design

### 3.1 3+3 Dose Escalation Schema

The standard 3+3 design is a rule-based dose escalation method appropriate for Phase I oncology and cell therapy trials where the primary objective is to identify the maximum tolerated dose (MTD) or recommended Phase II dose (RP2D).

**Escalation Algorithm:**

```
Dose Level k: Enroll 3 patients
    |
    ├── 0/3 DLTs → Escalate to Dose Level k+1
    |
    ├── 1/3 DLTs → Expand to 6 patients at Dose Level k
    |   ├── 1/6 DLTs → Escalate to Dose Level k+1
    |   └── >= 2/6 DLTs → MTD exceeded; RP2D = Dose Level k-1
    |
    └── >= 2/3 DLTs → MTD exceeded; RP2D = Dose Level k-1
```

**Minimum inter-patient interval:** 14 days between patients within a cohort (to allow observation of early toxicity before treating subsequent patients).

**Minimum inter-cohort interval:** 28 days (full DLT window) after the last patient in a cohort before dose escalation decision.

### 3.2 Dose Escalation Decision Table

| Scenario | DLTs Observed | Action |
|----------|--------------|--------|
| Cohort of 3 at DL_k | 0/3 | Escalate to DL_(k+1) |
| Cohort of 3 at DL_k | 1/3 | Expand cohort to 6 at DL_k |
| Cohort of 6 at DL_k | 0--1/6 | Escalate to DL_(k+1) |
| Cohort of 3 at DL_k | 2--3/3 | Stop escalation; DL_(k-1) is RP2D candidate |
| Cohort of 6 at DL_k | >= 2/6 | Stop escalation; DL_(k-1) is RP2D candidate |
| DL1 | >= 2/3 or >= 2/6 | Study paused; evaluate de-escalation or protocol amendment |

---

## 4. Dose-Limiting Toxicity Definition

### 4.1 DLT Assessment Window

Day 0 (CAR-T cell infusion) through Day 28 post-infusion. Only adverse events assessed as at least possibly related to CAR-T cell therapy (not solely attributable to lymphodepleting conditioning or underlying SLE disease activity) are evaluable as DLTs.

### 4.2 DLT Criteria

| Event | Grade/Duration Threshold | Grading System |
|-------|-------------------------|----------------|
| **CRS** | Grade >= 4 | ASTCT Consensus Grading (Lee et al., 2019) |
| **ICANS** | Grade >= 3 lasting > 7 days despite corticosteroid management | ASTCT Consensus Grading; ICE scoring tool |
| **Neutropenia** | Grade 4 (ANC < 500/uL) lasting > 28 days, not attributable to SLE or conditioning | CTCAE v5.0 |
| **Thrombocytopenia** | Grade 4 (platelets < 25,000/uL) lasting > 28 days, not attributable to SLE or conditioning | CTCAE v5.0 |
| **Non-hematologic toxicity** | Grade >= 4, excluding CRS and ICANS, attributable to CAR-T cells | CTCAE v5.0 |
| **Death** | Any treatment-related death | -- |

### 4.3 DLT Attribution

Events attributed solely to:
- Lymphodepleting chemotherapy (expected myelosuppression within 14 days)
- Underlying SLE disease activity (pre-existing cytopenias, flare)
- Pre-existing conditions

...are NOT counted as DLTs. Attribution is determined by the investigator with DSMB concurrence.

### 4.4 DLT-Evaluable Criteria

A patient is DLT-evaluable if:
- They received the full intended dose of CAR-T cells
- They completed the 28-day DLT assessment window OR experienced a DLT prior to Day 28
- They did not withdraw consent or become lost to follow-up during the DLT window for reasons unrelated to treatment

Patients who are not DLT-evaluable are replaced.

---

## 5. Sample Size Justification

### 5.1 Sample Size Range

The 3+3 design with 3 dose levels yields a sample size of 9--18 patients:

| Scenario | N per Level | Total N |
|----------|------------|---------|
| No expansion required at any level | 3 + 3 + 3 | 9 |
| Expansion required at 1 level | 3 + 6 + 3 (or variant) | 12 |
| Expansion required at 2 levels | 6 + 6 + 3 (or variant) | 15 |
| Expansion required at all levels | 6 + 6 + 6 | 18 |

### 5.2 Operating Characteristics of 3+3 Design

The 3+3 design has well-characterized operating characteristics (Storer, 1989; Le Tourneau et al., 2009):

| True DLT Rate | Probability of Escalation | Probability of Stopping at This Level |
|---------------|--------------------------|--------------------------------------|
| 5% | 0.91 | 0.01 |
| 10% | 0.78 | 0.04 |
| 15% | 0.65 | 0.09 |
| 20% | 0.52 | 0.15 |
| 25% | 0.40 | 0.21 |
| 30% | 0.30 | 0.25 |
| 33% | 0.25 | 0.27 |
| 40% | 0.15 | 0.29 |
| 50% | 0.06 | 0.26 |
| 60% | 0.02 | 0.19 |

**Target DLT rate for RP2D:** The 3+3 design implicitly targets a DLT rate near 20--33%. For this program, the target DLT rate for RP2D selection is < 17% (approximately 1/6), consistent with the expectation that autoimmune CAR-T therapy should have a substantially lower DLT rate than oncology applications.

### 5.3 Limitations of the 3+3 Design

- Small sample sizes at each dose level limit precision of DLT rate estimates
- The design is conservative (tends to recommend doses below the true MTD)
- Limited ability to characterize the dose-response relationship
- Does not formally optimize for a target DLT rate

These limitations are acceptable in Phase I given the primary safety objective. The Phase II trial will provide more precise efficacy and safety estimates at the RP2D.

---

## 6. Analysis Populations

| Population | Definition | Primary Use |
|-----------|-----------|-------------|
| **Enrolled** | All patients who signed informed consent | Disposition summaries |
| **Safety Population** | All patients who received any amount of CAR-T cells | Primary safety analysis; all AE summaries |
| **DLT-Evaluable Population** | Subset of Safety Population who completed the 28-day DLT window or experienced a DLT, received the full intended CAR-T cell dose, and did not discontinue for reasons unrelated to treatment | DLT analysis; dose escalation decisions |
| **Modified Intent-to-Treat (mITT)** | All patients who received any amount of CAR-T cells and had at least one post-baseline efficacy assessment | Secondary efficacy analyses |
| **Per-Protocol (PP)** | Subset of mITT who received the intended CAR-T dose, completed the protocol-specified lymphodepletion, and had no major protocol deviations that could affect efficacy assessment | Sensitivity efficacy analyses |
| **PK-Evaluable** | Subset of Safety Population with sufficient PK sampling (>= 5 post-infusion timepoints with evaluable CAR-T expansion data) | Pharmacokinetic analyses |

---

## 7. Estimand Framework

Per ICH E9(R1), the following estimand is defined for the primary analysis:

### 7.1 Primary Estimand (Safety)

| Component | Specification |
|-----------|--------------|
| **Population** | Adults 18--65 years with refractory SLE who received anti-CD19 CAR-T cells |
| **Variable (Endpoint)** | Occurrence of DLT within 28 days of CAR-T infusion (binary: yes/no) |
| **Intercurrent Events** | (1) Use of rescue medication for CRS/ICANS (tocilizumab, corticosteroids) -- treatment policy strategy (included in analysis regardless of rescue use); (2) Withdrawal of consent -- hypothetical strategy (patient would have been observed for full 28 days); (3) Death -- composite strategy (death is a DLT) |
| **Population-Level Summary** | Proportion of patients experiencing DLT at each dose level, with exact binomial 90% confidence interval |
| **Strategy for Intercurrent Events** | Treatment policy: DLTs are assessed regardless of supportive care or rescue medications administered, as these are part of standard CAR-T management |

### 7.2 Secondary Estimand (Efficacy -- SRI-4 at Week 52)

| Component | Specification |
|-----------|--------------|
| **Population** | mITT population (all treated patients with >= 1 post-baseline efficacy assessment) |
| **Variable** | SRI-4 response at Week 52 (binary: yes/no) |
| **Intercurrent Events** | (1) New immunosuppressive therapy initiated -- composite strategy (non-responder if new IS therapy started); (2) Death -- composite strategy (non-responder); (3) Withdrawal -- hypothetical strategy (multiple imputation under missing-at-random assumption) |
| **Population-Level Summary** | Proportion of SRI-4 responders with exact binomial 95% confidence interval; by dose level |
| **Strategy** | Composite: patients who require new immunosuppressive therapy or die are classified as non-responders |

---

## 8. Statistical Methods

### 8.1 Primary Analysis: DLT Rate

- **Method:** Descriptive. DLT rate at each dose level expressed as number with DLT / number DLT-evaluable.
- **Confidence Interval:** Exact (Clopper-Pearson) 90% CI for the binomial proportion at each dose level.
- **Dose Escalation Decision:** Rule-based per 3+3 algorithm (not model-based).
- **No formal hypothesis testing** is performed for the primary endpoint in Phase I.

Example presentation:

| Dose Level | N DLT-Evaluable | N DLTs | DLT Rate | 90% CI |
|------------|----------------|--------|----------|--------|
| DL1 (0.5 x 10^6/kg) | -- | -- | -- | -- |
| DL2 (1.0 x 10^6/kg) | -- | -- | -- | -- |
| DL3 (2.0 x 10^6/kg) | -- | -- | -- | -- |

### 8.2 Safety Analyses

| Analysis | Method |
|----------|--------|
| Adverse events (all) | Frequency tables by dose level, grade (CTCAE v5.0), relatedness, seriousness |
| CRS | Incidence by ASTCT grade and dose level; time to onset, duration, management (tocilizumab use) |
| ICANS | Incidence by ASTCT grade and dose level; time to onset, duration, ICE score nadir |
| Cytopenias | Incidence by CTCAE grade; time to nadir, time to recovery (ANC > 1000, platelets > 50,000) |
| Infections | Incidence by type, pathogen, grade, timing relative to infusion |
| Laboratory parameters | Shift tables (baseline to worst post-baseline grade); longitudinal plots (mean +/- SD by visit) |
| Exposure-response (exploratory) | Scatter plots of CAR-T Cmax vs. CRS grade, ICANS grade |

### 8.3 Efficacy Analyses (Secondary -- Descriptive)

| Endpoint | Analysis Method |
|----------|----------------|
| SRI-4 response | Proportion with exact 95% CI, by dose level and overall |
| Anti-dsDNA normalization | Proportion with exact 95% CI; time to normalization (Kaplan-Meier) |
| Complement normalization | Proportion with exact 95% CI |
| SLEDAI-2K change | Mean change from baseline (SD), by visit; Wilcoxon signed-rank test |
| Corticosteroid reduction | Mean daily dose over time; proportion achieving <= 5 mg/day |
| Drug-free remission | Proportion achieving SLEDAI-2K = 0 and off immunosuppression |

All efficacy analyses are **descriptive and exploratory** in Phase I. No formal hypothesis testing is performed; p-values, if presented, are nominal and not adjusted for multiplicity.

### 8.4 Pharmacokinetic / Pharmacodynamic Analyses

| Parameter | Method |
|-----------|--------|
| CAR-T expansion | Individual PK profiles (copies/ug DNA vs. time); summary statistics for Cmax, Tmax, AUC(0-28) by dose level |
| CAR-T persistence | Proportion with detectable transgene at Months 3, 6, 12 |
| B-cell depletion | Time to undetectable CD19+ B cells; nadir CD19+ count |
| B-cell reconstitution | Time to CD19+ B cell recovery (>= 10 cells/uL); characterization of reconstituted repertoire |
| Dose-PK relationship | Descriptive comparison of Cmax, AUC across dose levels; dose proportionality assessment (power model if sufficient data) |
| PK-PD relationship | Exploratory correlation between CAR-T expansion (Cmax) and B-cell depletion depth |
| PK-Safety relationship | Exploratory correlation between CAR-T expansion and CRS grade / cytokine levels |
| PK-Efficacy relationship | Exploratory correlation between CAR-T expansion / B-cell depletion and SRI-4 response |

### 8.5 Subgroup Analyses (Exploratory)

Given the small sample size, subgroup analyses are limited to descriptive summaries:
- By lupus nephritis status (yes/no)
- By baseline SLEDAI-2K (< 12 vs. >= 12)
- By baseline anti-dsDNA titer (< 2x ULN vs. >= 2x ULN)
- By number of prior therapies (2 vs. >= 3)

No formal statistical comparisons between subgroups will be performed.

---

## 9. Interim Analysis and DSMB

### 9.1 DSMB Charter Summary

| Parameter | Specification |
|-----------|--------------|
| **Composition** | >= 3 members: 1 cell therapy physician, 1 rheumatologist, 1 biostatistician; all independent of sponsor |
| **Meeting Schedule** | After each dose cohort completes 28-day DLT window; ad hoc for safety signals |
| **Data Access** | Unblinded (open-label study) |
| **Voting** | Majority rule; recommendations to sponsor; sponsor makes final decision but must document rationale if deviating from DSMB recommendation |

### 9.2 DSMB Review Schedule

| Review | Trigger | Data Reviewed | Possible Recommendations |
|--------|---------|--------------|-------------------------|
| Review 1 | DL1 cohort complete (Day 28) | DLTs, all AEs, labs, CRS/ICANS | Proceed to DL2; expand DL1; pause enrollment |
| Review 2 | DL2 cohort complete (Day 28) | Cumulative safety (DL1 + DL2) | Proceed to DL3; expand DL2; declare RP2D |
| Review 3 | DL3 cohort complete (Day 28) | Cumulative safety (all dose levels) | Declare RP2D; expand DL3; dose too high |
| Ad hoc | Any SAE, unexpected toxicity, treatment-related death | Relevant safety data | Continue; pause; terminate; protocol amendment |

### 9.3 Stopping Rules

The DSMB will recommend pausing or stopping enrollment if:

| Criterion | Action |
|-----------|--------|
| Any treatment-related death | Mandatory pause; expedited DSMB review within 72 hours |
| >= 2 patients with Grade 4+ CRS across the study | Pause enrollment; reassess CRS management and dose |
| Any case of Grade 4 cerebral edema (ICANS) | Pause enrollment; reassess neurotoxicity risk |
| DLT rate exceeds 33% at DL1 | Study paused; evaluate dose de-escalation or protocol redesign |
| Unexpected organ toxicity pattern | DSMB discretion; may recommend pause, additional monitoring, or stopping |

---

## 10. Missing Data

### 10.1 Approach to Missing Data

Given the small sample size and intensive monitoring schedule in Phase I:

| Missing Data Type | Strategy | Justification |
|-------------------|----------|---------------|
| Missing DLT assessment (patient lost before Day 28) | Patient is replaced (not DLT-evaluable) | DLT evaluability requires completing the 28-day window |
| Missing efficacy endpoint (SRI-4 at Week 52) | Non-responder imputation (primary); observed data analysis (sensitivity) | Conservative approach; consistent with composite estimand strategy |
| Missing laboratory values | Last observation carried forward (LOCF) for shift tables; observed data for longitudinal analyses | Descriptive purpose only; not used for inferential decisions |
| Missing PK timepoints | Excluded from individual PK profile; patient included in summary if >= 5 evaluable timepoints | Standard PK analysis practice |

### 10.2 Sensitivity Analyses for Efficacy

1. **Best-case / worst-case:** Missing efficacy data imputed as responder (best case) or non-responder (worst case) to bound the effect
2. **Complete case analysis:** Restrict to patients with observed Week 52 SRI-4 data
3. **Tipping point analysis:** Determine how many missing patients would need to be non-responders to change the qualitative conclusion

---

## 11. References

1. ICH E9. Statistical Principles for Clinical Trials. 1998.
2. ICH E9(R1). Addendum on Estimands and Sensitivity Analysis in Clinical Trials. 2019.
3. ICH E4. Dose-Response Information to Support Drug Registration. 1994.
4. FDA. Considerations for the Design of Early-Phase Clinical Trials of Cellular and Gene Therapy Products. 2015.
5. Storer BE. Design and analysis of Phase I clinical trials. Biometrics. 1989;45(3):925-937. PMID: 2790129
6. Le Tourneau C, et al. Dose escalation methods in Phase I cancer clinical trials. J Natl Cancer Inst. 2009;101(10):708-720. PMID: 19436029
7. Lee DW, et al. ASTCT Consensus Grading for CRS and Neurologic Toxicity. Biol Blood Marrow Transplant. 2019;25(4):625-638. PMID: 30592986
8. Clopper CJ, Pearson ES. The use of confidence or fiducial limits illustrated in the case of the binomial. Biometrika. 1934;26(4):404-413.

---

*This document is a simulated SAP summary. It does not constitute an actual Statistical Analysis Plan and is not intended for regulatory submission.*
