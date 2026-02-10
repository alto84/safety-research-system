# End-of-Phase-2 Meeting Briefing Document

> **SIMULATED** -- This document is a simulated regulatory deliverable for the pharma company simulation.
> It does not represent an actual FDA briefing document or contain real clinical data.

**Meeting Type:** Type B -- End-of-Phase-2 Meeting
**Product:** Autologous Anti-CD19 CAR-T Cell Therapy
**IND Number:** IND XXXXXX
**Indication:** Systemic Lupus Erythematosus (SLE)
**Sponsor:** [Sponsor Name -- Cell Therapy Startup]
**Proposed Meeting Date:** [Q3 2027]
**Date of Document:** [Date]
**Regulation:** FDA Guidance for Industry -- Formal Meetings Between the FDA and Sponsors or Applicants of PDUFA Products (2009)

---

## Table of Contents

1. [Purpose of the Meeting](#1-purpose-of-the-meeting)
2. [Product Background](#2-product-background)
3. [Product Description](#3-product-description)
4. [Chemistry, Manufacturing, and Controls Summary](#4-chemistry-manufacturing-and-controls-summary)
5. [Nonclinical Summary](#5-nonclinical-summary)
6. [Clinical Experience to Date](#6-clinical-experience-to-date)
7. [Proposed Phase III Pivotal Study Design](#7-proposed-phase-iii-pivotal-study-design)
8. [Regulatory Strategy](#8-regulatory-strategy)
9. [Questions for FDA Discussion](#9-questions-for-fda-discussion)
10. [References](#10-references)

---

## 1. Purpose of the Meeting

The Sponsor requests this End-of-Phase-2 (EOP2) meeting to discuss the following with FDA/CBER:

1. Adequacy of the Phase I/II clinical data to support initiation of a Phase III pivotal trial
2. Agreement on the proposed Phase III study design, including primary endpoint, patient population, and statistical analysis plan
3. Acceptability of the proposed adaptive design elements
4. CMC considerations for commercial-scale manufacturing
5. Regulatory pathway and submission strategy for a Biologics License Application (BLA)

This meeting is requested under 21 CFR 312.47(b) and the FDA Guidance for Formal Meetings (2009). The Sponsor requests a face-to-face meeting with FDA/CBER Division of Cellular and Gene Therapies (DCGT).

---

## 2. Product Background

### 2.1 Disease Overview

Systemic lupus erythematosus (SLE) is a chronic, relapsing-remitting autoimmune disease characterized by loss of B-cell tolerance, autoantibody production, and multi-organ inflammation. Despite available therapies (hydroxychloroquine, mycophenolate, belimumab, anifrolumab, voclosporin), a significant proportion of patients remain refractory to treatment, with persistent disease activity, organ damage accrual, and impaired quality of life.

**Unmet Medical Need:**
- Approximately 30-40% of SLE patients have inadequate response to standard of care
- Organ damage accrues progressively despite treatment (measured by SLICC/ACR Damage Index)
- SLE carries a standardized mortality ratio of 2-5x compared to the general population
- No currently approved therapy achieves sustained drug-free remission in a substantial proportion of patients

### 2.2 Scientific Rationale for Anti-CD19 CAR-T in SLE

CD19-positive B cells play a central role in SLE pathogenesis through autoantibody production, antigen presentation, and cytokine secretion. Anti-CD19 CAR-T therapy provides deep B-cell depletion including CD20-negative plasmablasts and a subset of long-lived plasma cells not targeted by rituximab (anti-CD20).

Published case series (Mackensen et al., Nat Med 2022; Muller et al., NEJM 2024) have demonstrated:
- Rapid and sustained clinical responses (SLEDAI-2K reduction to 0)
- Serological remission (anti-dsDNA normalization, complement normalization)
- B-cell reconstitution with naive phenotype (suggesting immune reset)
- Drug-free remission maintained beyond 12 months

### 2.3 Regulatory Designations

| Designation | Status | Date |
|-------------|--------|------|
| RMAT (Regenerative Medicine Advanced Therapy) | [Granted/Pending] | [Date] |
| Breakthrough Therapy | [Granted/Pending] | [Date] |
| Orphan Drug (subset populations) | [Under evaluation] | -- |

---

## 3. Product Description

### 3.1 General Description

| Attribute | Description |
|-----------|-------------|
| **Product Name** | [Product Code/Name] |
| **Product Class** | Autologous, genetically modified T-cell immunotherapy |
| **Target Antigen** | CD19 |
| **Construct** | Anti-CD19 scFv -- CD28 hinge/TM -- CD28 costimulatory domain -- CD3-zeta signaling domain |
| **Vector** | Self-inactivating (SIN) lentiviral vector |
| **Cell Type** | Autologous T cells (CD4+ and CD8+) |
| **Route of Administration** | Intravenous infusion |
| **Dosing** | Single infusion; dose based on CAR-positive viable T cells per kg body weight |
| **Lymphodepletion** | Fludarabine (30 mg/m2 x 3 days) + Cyclophosphamide (300 mg/m2 x 3 days) |

### 3.2 Mechanism of Action

The anti-CD19 CAR-T cells bind to CD19-expressing B-lineage cells, triggering T-cell activation, cytotoxic killing of target cells, and CAR-T cell proliferation. This results in:

1. **Depletion of CD19+ B cells** across all maturation stages (pro-B through memory B cells and plasmablasts)
2. **Elimination of autoreactive B-cell clones** driving SLE pathology
3. **B-cell reconstitution** from hematopoietic precursors with a predominantly naive phenotype, representing an "immune reset"

### 3.3 Differentiation from Anti-CD20 Therapy

| Feature | Anti-CD20 (rituximab) | Anti-CD19 CAR-T |
|---------|----------------------|-----------------|
| Target cell range | CD20+ B cells only | Broader: includes CD20-negative plasmablasts |
| Depth of depletion | Incomplete; spares tissue-resident B cells | Deep; penetrates tissue compartments |
| Duration of effect | Requires repeated dosing | Single infusion; sustained effect |
| Immune reset | Not observed | Naive B-cell reconstitution observed |

---

## 4. Chemistry, Manufacturing, and Controls Summary

### 4.1 Manufacturing Process Overview

Per 21 CFR 1271 (Human Cells, Tissues, and Cellular and Tissue-Based Products) and applicable CBER guidances for cell and gene therapy products.

**Manufacturing Steps:**
1. Leukapheresis at qualified clinical apheresis center
2. Cryopreservation and shipment of apheresis material to manufacturing facility
3. T-cell enrichment and activation (anti-CD3/CD28 stimulation)
4. Lentiviral transduction (MOI [X])
5. Ex vivo expansion ([X] days)
6. Harvest, wash, formulation in cryopreservation medium
7. Fill into infusion bags, controlled-rate freezing
8. Quality control release testing
9. Cryogenic shipment to clinical site

### 4.2 Release Specifications

| Test | Method | Specification |
|------|--------|---------------|
| Cell viability | Trypan blue exclusion | >= [X]% |
| CAR expression (% CAR+) | Flow cytometry | >= [X]% |
| Total viable cells | Automated cell counter | [Range] |
| Vector copy number (VCN) | qPCR | <= [X] copies/cell |
| Sterility | USP <71> / BacT/ALERT | No growth (14-day) |
| Endotoxin | LAL kinetic turbidimetric | < [X] EU/mL |
| Mycoplasma | qPCR | Not detected |
| Replication-competent lentivirus (RCL) | p24 ELISA / qPCR | Not detected |
| T-cell phenotype | Flow cytometry (CD4/CD8/CAR) | Report result |
| Potency | Cytotoxicity assay (CD19+ target cells) | >= [X]% specific lysis |

### 4.3 Scale-Up Considerations for Phase III / Commercial

| Topic | Current (Phase I/II) | Proposed (Phase III / Commercial) |
|-------|---------------------|-----------------------------------|
| Manufacturing site | [Site A] | [Site A + Site B for redundancy] |
| Process | Manual/semi-automated | Semi-automated / closed system |
| Batch size | Single patient | Single patient (autologous) |
| Vein-to-vein time | [XX] days | Target [XX] days (process optimization) |
| Capacity | [XX] patients/year | [XXX] patients/year |

**Sponsor seeks FDA feedback on:** Comparability strategy for process changes between Phase II and Phase III (Section 9, Question 5).

---

## 5. Nonclinical Summary

### 5.1 Pharmacology Studies

| Study | Model | Key Findings |
|-------|-------|--------------|
| In vitro cytotoxicity | CD19+ human B-cell lines | Dose-dependent killing; EC50 E:T ratio [X:1] |
| In vitro specificity | CD19-negative cell lines | No off-target killing observed |
| In vivo efficacy | NSG mice engrafted with human CD19+ cells | [Summary of B-cell depletion kinetics] |
| Cytokine release | Co-culture with CD19+ targets | Dose-dependent IFN-gamma, TNF-alpha, IL-2 release |

### 5.2 Toxicology / Safety Studies

| Study | Model | Key Findings |
|-------|-------|--------------|
| Single-dose toxicology | NSG mice | B-cell aplasia (expected); no unexpected organ toxicity |
| Biodistribution | qPCR in NSG mice | CAR-T cells detected in blood, spleen, bone marrow; low/absent in non-target organs |
| Tumorigenicity (insertional mutagenesis) | Integration site analysis (ISA) | Polyclonal integration pattern; no dominant clones |

### 5.3 Nonclinical Conclusions

The nonclinical program supports the safety and pharmacological activity of the anti-CD19 CAR-T product. Findings are consistent with the known class effects of CD19-targeted CAR-T therapies. No unexpected safety signals were identified.

---

## 6. Clinical Experience to Date

### 6.1 Phase I Study (Protocol [XXXX]-001)

**Study Design:** Open-label, multicenter, 3+3 dose-escalation
**Population:** Adult patients with SLE (ACR/EULAR 2019 criteria) refractory to >= 2 standard-of-care therapies, SLEDAI-2K >= 6
**Dose Levels:** DL1 [X x 10^6], DL2 [X x 10^6], DL3 [X x 10^6] CAR+ T cells/kg
**Sites:** 3 active sites
**Enrollment:** [N] subjects treated

#### 6.1.1 Efficacy Results

| Endpoint | DL1 (N=X) | DL2 (N=X) | DL3 (N=X) | All (N=X) |
|----------|-----------|-----------|-----------|-----------|
| SLEDAI-2K = 0 at Week 24 | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| SRI-4 response at Week 24 | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| Anti-dsDNA normalization | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| Complement (C3/C4) normalization | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| Complete B-cell depletion (Day 14) | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| Corticosteroid taper to <= 5 mg/day | [N (%)] | [N (%)] | [N (%)] | [N (%)] |
| Drug-free remission at Week 52 | [N (%)] | [N (%)] | [N (%)] | [N (%)] |

#### 6.1.2 Safety Results

| Adverse Event | All Grades N (%) | Grade >= 3 N (%) |
|---------------|------------------|-------------------|
| CRS (any grade) | [N (%)] | [N (%)] |
| CRS Grade 1 | [N (%)] | -- |
| CRS Grade 2 | [N (%)] | -- |
| CRS Grade >= 3 | -- | [N (%)] |
| ICANS (any grade) | [N (%)] | [N (%)] |
| Cytopenias (any) | [N (%)] | [N (%)] |
| Neutropenia | [N (%)] | [N (%)] |
| Thrombocytopenia | [N (%)] | [N (%)] |
| Infections | [N (%)] | [N (%)] |
| Hypogammaglobulinemia | [N (%)] | [N (%)] |

**CRS Management:** [Summary of tocilizumab/corticosteroid use]
**ICANS Management:** [Summary]
**Deaths:** [None / narrative]

#### 6.1.3 Pharmacokinetics / Pharmacodynamics

| Parameter | DL1 | DL2 | DL3 |
|-----------|-----|-----|-----|
| CAR-T Cmax (cells/uL) | [Value] | [Value] | [Value] |
| Time to Cmax (days) | [Value] | [Value] | [Value] |
| CAR-T persistence (last detectable) | [Value] | [Value] | [Value] |
| B-cell depletion nadir (day) | [Value] | [Value] | [Value] |
| B-cell recovery onset (day) | [Value] | [Value] | [Value] |
| Cytokine peak (IL-6, IFN-gamma) | [Value] | [Value] | [Value] |

### 6.2 Phase II Study (Protocol [XXXX]-002)

**Study Design:** Open-label, multicenter, expansion cohort at recommended Phase II dose (RP2D)
**Population:** Same as Phase I with broadened eligibility
**RP2D:** [X x 10^6] CAR+ T cells/kg (selected from Phase I)
**Sites:** [N] sites
**Enrollment:** [N] subjects treated

#### 6.2.1 Efficacy Results

| Endpoint | RP2D (N=X) |
|----------|------------|
| **Primary: SRI-4 at Week 52** | **[N (%)] [95% CI]** |
| SLEDAI-2K = 0 at Week 52 | [N (%)] |
| BICLA response at Week 52 | [N (%)] |
| Anti-dsDNA normalization at Week 52 | [N (%)] |
| Complement normalization at Week 52 | [N (%)] |
| Corticosteroid-free (prednisone 0 mg) at Week 52 | [N (%)] |
| No flare through Week 52 | [N (%)] |
| SLICC/ACR Damage Index (no worsening) | [N (%)] |
| Lupus nephritis complete response (if applicable) | [N (%)] |

#### 6.2.2 Safety Results

[Summary consistent with Phase I profile; cross-reference DSUR Year 2]

### 6.3 Dose Selection Rationale for Phase III

Based on the integrated Phase I/II data:
- **Selected dose for Phase III:** [X x 10^6] CAR+ T cells/kg (= RP2D)
- **Rationale:** [Summary of dose-response, safety margin, PK/PD relationship]
- **Lymphodepletion regimen:** Fludarabine 30 mg/m2 + Cyclophosphamide 300 mg/m2 x 3 days (consistent with Phase I/II)

---

## 7. Proposed Phase III Pivotal Study Design

### 7.1 Study Synopsis

| Parameter | Detail |
|-----------|--------|
| **Title** | A Phase III, Randomized, Controlled Study to Evaluate the Efficacy and Safety of Autologous Anti-CD19 CAR-T Cell Therapy vs. Standard of Care in Patients with Refractory Systemic Lupus Erythematosus |
| **Protocol Number** | [XXXX]-003 |
| **Phase** | Phase III Pivotal |
| **Design** | Randomized, active-controlled, open-label with blinded endpoint assessment |
| **Population** | Adults with SLE (ACR/EULAR 2019 criteria), SLEDAI-2K >= 6, refractory to >= 2 SOC therapies |
| **Randomization** | 2:1 (CAR-T : standard of care) |
| **Primary Endpoint** | **SRI-4 response at Week 52** |
| **Key Secondary Endpoints** | BICLA at Week 52; drug-free remission at Week 52; time to first flare; SLICC/ACR Damage Index; corticosteroid reduction; PRO (SF-36, FACIT-Fatigue) |
| **Sample Size** | [N] subjects (see Section 7.5) |
| **Study Duration** | 52-week primary analysis + 4-year long-term follow-up |
| **Sites** | Approximately [XX] sites globally |

### 7.2 Primary Endpoint: SRI-4 at Week 52

The SLE Responder Index (SRI-4) is a validated composite endpoint accepted by FDA for SLE registration trials (used in belimumab and anifrolumab approvals). SRI-4 response is defined as:

1. Reduction of >= 4 points from baseline in SLEDAI-2K, AND
2. No new British Isles Lupus Assessment Group (BILAG) A organ domain score and no more than 1 new BILAG B score, AND
3. No worsening (< 0.3-point increase) in Physician Global Assessment (PGA)

**Justification:** SRI-4 is the standard primary endpoint for SLE pivotal trials per FDA precedent and provides a clinically meaningful composite assessment of disease activity improvement without worsening in other organ domains.

### 7.3 Adaptive Design Elements

Per FDA Guidance for Industry: Adaptive Designs for Clinical Trials of Drugs and Biologics (2019) and ICH E9(R1) Addendum on Estimands and Sensitivity Analysis:

1. **Pre-planned interim analysis** at approximately 50% information fraction
   - Futility assessment (non-binding)
   - Sample size re-estimation based on conditional power (blinded or unblinded per IDMC charter)
   - Efficacy assessment with alpha spending (Lan-DeMets O'Brien-Fleming boundary)

2. **Sample size re-estimation**
   - Initial sample size based on assumed SRI-4 rate of [X]% (CAR-T) vs. [X]% (SOC)
   - Conditional power threshold for sample size increase: 50%
   - Maximum sample size cap: [N] subjects

3. **IDMC governance**
   - Independent Data Monitoring Committee reviews unblinded data
   - Pre-specified stopping rules for safety (excess mortality, excessive Grade >= 3 CRS/ICANS)
   - Futility stopping if conditional power < [X]% at interim

**Estimand framework (ICH E9(R1)):**
- **Treatment:** Single infusion of anti-CD19 CAR-T vs. SOC
- **Population:** Refractory SLE (intent-to-treat)
- **Endpoint:** SRI-4 at Week 52
- **Intercurrent events:** Treatment switching (handled by treatment policy strategy); death (composite strategy); rescue medication (treatment policy strategy)
- **Summary measure:** Difference in response rates

### 7.4 Control Arm Considerations

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Standard of Care (proposed)** | Optimized background SLE therapy per investigator discretion | Clinically relevant; ethical; reflects real-world practice | Open-label design required due to manufacturing logistics |
| Active comparator (belimumab) | IV belimumab + SOC | Well-characterized efficacy; head-to-head data | Limits generalizability; regulatory complexity |
| Delayed treatment / crossover | SOC with optional CAR-T crossover at Week 52 | Ethical; patient retention | Dilutes long-term efficacy signal |

**Sponsor proposal:** Standard of care control with blinded endpoint assessment (BICLA/SRI-4 assessed by blinded evaluator independent of treating physician). Open-label for treatment assignment is necessary due to the nature of the CAR-T manufacturing and infusion process.

### 7.5 Sample Size Rationale

Per ICH E9(R1) and FDA Guidance on Adaptive Designs:

**Assumptions:**
- SRI-4 response rate at Week 52 (CAR-T arm): [X]% (based on Phase II data)
- SRI-4 response rate at Week 52 (SOC arm): [X]% (based on published literature for refractory SLE)
- Randomization ratio: 2:1 (CAR-T : SOC)
- Alpha: 0.025 (one-sided) / 0.05 (two-sided)
- Power: 90%
- Dropout rate: [X]%
- Alpha spending: Lan-DeMets O'Brien-Fleming for interim analysis

**Calculated sample size:** [N] subjects ([N] CAR-T : [N] SOC)
- Includes [X]% inflation for adaptive design
- Maximum sample size (with re-estimation): [N] subjects

### 7.6 Key Eligibility Criteria (Proposed)

**Inclusion:**
1. Age >= 18 years
2. SLE per ACR/EULAR 2019 classification criteria
3. SLEDAI-2K >= 6 at screening
4. Refractory to >= 2 standard-of-care therapies (including at least one of: mycophenolate, azathioprine, cyclophosphamide, belimumab, anifrolumab, voclosporin)
5. Positive anti-dsDNA or anti-nuclear antibodies
6. Adequate organ function for leukapheresis and lymphodepletion

**Exclusion:**
1. Active severe neuropsychiatric SLE
2. eGFR < 30 mL/min/1.73m2 (unless due to active lupus nephritis amenable to treatment)
3. Prior CAR-T or gene therapy
4. Active uncontrolled infection
5. Positive for HIV, active HBV, or active HCV
6. Malignancy within past 5 years (except non-melanoma skin cancer)
7. Pregnancy or lactation

### 7.7 Long-Term Follow-Up

Per FDA Guidance for Long-Term Follow-Up After Administration of a Gene Therapy Product (2020):
- All subjects who receive CAR-T will be followed for a minimum of 5 years for delayed adverse events
- Monitoring includes: secondary malignancies, replication-competent lentivirus (RCL), insertional oncogenesis
- Annual assessments after primary analysis period

---

## 8. Regulatory Strategy

### 8.1 Proposed Pathway

| Element | Proposal |
|---------|----------|
| **Application Type** | BLA (Biologics License Application) per PHS Act Section 351(a) |
| **Review Division** | CBER / Division of Cellular and Gene Therapies (DCGT) |
| **Expedited Programs** | RMAT + Breakthrough Therapy (if granted) |
| **Approval Pathway** | Traditional approval based on SRI-4 at Week 52 (primary); potential accelerated approval based on SLEDAI-2K = 0 (if supported by FDA) |
| **Review Priority** | Priority Review (if RMAT/Breakthrough + significant improvement) |

### 8.2 RMAT Considerations

If RMAT designation is granted per 21 CFR 351 / RMAT Guidance:
- Potential for accelerated approval based on surrogate or intermediate endpoint
- Surrogate considered: Complete B-cell depletion + serological remission (anti-dsDNA normalization + complement normalization) as a reasonably likely surrogate for long-term clinical benefit
- Post-marketing confirmatory study would be required

### 8.3 Pediatric Considerations

Per Pediatric Research Equity Act (PREA):
- SLE affects pediatric patients; pediatric study plan will be required
- Sponsor proposes deferral of pediatric studies until after adult Phase III completion
- Pediatric Study Plan (PSP) to be submitted per FDA requirements

---

## 9. Questions for FDA Discussion

The Sponsor respectfully requests FDA's feedback on the following questions:

### Question 1: Primary Endpoint Acceptability
Does FDA agree that SRI-4 at Week 52 is an acceptable primary endpoint for a pivotal Phase III study in refractory SLE? Would FDA consider SLEDAI-2K = 0 (complete remission) as a co-primary or key secondary endpoint?

### Question 2: Control Arm and Study Design
Does FDA agree with the proposed open-label, randomized (2:1), standard-of-care-controlled design with blinded endpoint assessment? Are there specific requirements for the blinded assessment procedure that FDA would recommend?

### Question 3: Adaptive Design Elements
Does FDA agree with the proposed adaptive design including a pre-planned interim analysis for futility and sample size re-estimation per ICH E9(R1) framework? Does FDA have recommendations regarding the interim analysis timing or alpha-spending approach?

### Question 4: Accelerated Approval Pathway (RMAT)
If RMAT designation is granted, would FDA consider accelerated approval based on a surrogate endpoint (e.g., complete B-cell depletion + serological remission)? What level of evidence would be required for the surrogate, and what would the post-marketing confirmatory study requirements entail?

### Question 5: CMC Comparability for Process Changes
The Sponsor plans to implement manufacturing process optimizations (transition from manual to semi-automated closed system) between Phase II and Phase III. Does FDA agree that a comparability protocol based on release specifications, potency, and a subset of Phase III patients would be sufficient to bridge the process change? Or would a separate clinical bridging study be required?

### Question 6: Long-Term Follow-Up Requirements
Does FDA agree with the proposed 5-year long-term follow-up plan? Are there specific endpoints or monitoring requirements beyond those outlined in the FDA Gene Therapy Long-Term Follow-Up Guidance that should be included for this CAR-T product in an autoimmune indication?

### Question 7: Pediatric Development
Does FDA agree with the proposed deferral of pediatric studies until after completion of the adult Phase III study? What are FDA's expectations for the Pediatric Study Plan timeline?

---

## 10. References

1. Mackensen A, et al. Anti-CD19 CAR T cells for refractory systemic lupus erythematosus. Nat Med. 2022;28(10):2124-2132. PMID: 36109639
2. Muller F, et al. CD19-targeted CAR T cells in refractory antisynthetase syndrome. NEJM. 2024;390(8):687-700. PMID: 38381674
3. FDA Guidance for Industry: Formal Meetings Between the FDA and Sponsors or Applicants of PDUFA Products (2009)
4. FDA Guidance for Industry: Adaptive Designs for Clinical Trials of Drugs and Biologics (2019)
5. ICH E9(R1): Addendum on Estimands and Sensitivity Analysis in Clinical Trials (2019)
6. ICH E8(R1): General Considerations for Clinical Trials (2021)
7. FDA Guidance for Industry: Long Term Follow-Up After Administration of a Gene Therapy Product (2020)
8. FDA Guidance for Industry: Expedited Programs for Regenerative Medicine Therapies for Serious Conditions (RMAT) (2019)
9. 21 CFR 1271: Human Cells, Tissues, and Cellular and Tissue-Based Products
10. Petri M, et al. Derivation and validation of the Systemic Lupus International Collaborating Clinics classification criteria for systemic lupus erythematosus. Arthritis Rheum. 2012;64(8):2677-2686. PMID: 22553077

---

## Appendices

- **Appendix A:** Phase I/II Study Synopses
- **Appendix B:** Integrated Safety Summary Tables
- **Appendix C:** Manufacturing Process Flow Diagram
- **Appendix D:** Proposed Phase III Protocol Synopsis
- **Appendix E:** Statistical Analysis Plan Outline (Phase III)
- **Appendix F:** Proposed Pediatric Study Plan Timeline
- **Appendix G:** Product Quality Comparability Protocol (draft)

---

*SIMULATED DOCUMENT -- Not for regulatory use. Created as part of the pharma company simulation for the Safety Research System.*
