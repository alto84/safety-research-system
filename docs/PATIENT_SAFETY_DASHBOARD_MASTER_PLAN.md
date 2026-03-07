# Patient Safety Organization — Master Plan & Dashboard Design

**Version:** 1.0
**Date:** 2026-03-05
**Scope:** US & EU (expandable framework)
**Purpose:** Comprehensive plan for a Head of Patient Safety dashboard covering all functional areas of a pharmaceutical safety organization.

---

## Table of Contents

1. [Organization Structure & Governance](#1-organization-structure--governance)
2. [Regulatory Framework — US](#2-regulatory-framework--us)
3. [Regulatory Framework — EU](#3-regulatory-framework--eu)
4. [ICH Guidelines](#4-ich-guidelines)
5. [ICSR Case Processing & Safety Data Management](#5-icsr-case-processing--safety-data-management)
6. [Signal Detection & Safety Surveillance](#6-signal-detection--safety-surveillance)
7. [Aggregate Reporting](#7-aggregate-reporting)
8. [Risk Management](#8-risk-management)
9. [Quality System — SOPs, CAPAs & Audits](#9-quality-system--sops-capas--audits)
10. [Clinical Trial Safety](#10-clinical-trial-safety)
11. [Safety Science & Benefit-Risk](#11-safety-science--benefit-risk)
12. [Technology Landscape](#12-technology-landscape)
13. [KPIs & Dashboard Metrics](#13-kpis--dashboard-metrics)
14. [Geographic Expansion Framework](#14-geographic-expansion-framework)
15. [Implementation Roadmap](#15-implementation-roadmap)

---

## 1. Organization Structure & Governance

### 1.1 Typical PV Organization Chart

```
                        Chief Medical Officer (CMO)
                                  |
                    Head of Patient Safety / VP PV
                    /        |        |        \
            QPPV/         Safety    PV         Safety
            Deputy QPPV   Science   Operations  Surveillance
              |              |          |            |
         Local PPVs    Safety     Case        Signal
         (per market)  Physicians Processing  Detection
                       Labeling   Med Info    Epidemiology
                       Benefit-   Aggregate   Risk Mgmt
                       Risk       Reporting
```

**Key Roles:**

| Role | Regulatory Basis | Responsibilities |
|------|-----------------|------------------|
| QPPV (EU) | Dir 2001/83/EC Art 104 | Single point of accountability for EU PV system |
| Deputy QPPV | GVP Module I | Backup for QPPV, may share oversight duties |
| Local PPV (LPPV) | National requirements | In-country PV compliance for each EU member state |
| US Safety Officer | 21 CFR 312.32, 314.80 | IND/NDA safety reporting, FDA interactions |
| Safety Physician | ICH E2A, E2D | Medical assessment, causality, narratives |
| PV Scientist | GVP Module IX | Signal detection, evaluation, benefit-risk input |
| Case Processor | ICH E2B(R3) | ICSR intake, data entry, coding, submission |

**Ref:** GVP Module I (Rev 3, 2024); ICH E2E; CIOMS Working Group V

### 1.2 Governance Bodies

| Body | Purpose | Frequency | Ref |
|------|---------|-----------|-----|
| Safety Management Team (SMT) | Product-level safety review | Monthly | GVP IX |
| Safety Review Committee (SRC) | Cross-portfolio signal review | Quarterly | GVP IX |
| Risk Management Committee | RMP/REMS oversight | As needed | GVP Module V, XVI |
| DSMB/DMC | Independent clinical trial safety oversight | Per charter | ICH E6(R3), FDA 2006 Guidance |
| PV System Governance Board | PV system quality, audits, strategy | Quarterly | GVP Module I |
| Regulatory Intelligence Council | Horizon scanning, regulatory changes | Monthly | Internal best practice |

### 1.3 Operating Models

| Model | Description | Considerations |
|-------|-------------|----------------|
| Fully Insourced | All PV activities in-house | Full control, higher fixed cost |
| Fully Outsourced | CRO/CSO handles case processing + signal detection | Variable cost, requires robust SDEAs |
| Hybrid (Most Common) | Core safety science in-house, case processing outsourced | Balance of control and cost |

**Key Agreement:** Safety Data Exchange Agreement (SDEA) — required between MAH and partners per GVP Module VI and 21 CFR 314.80(b).

### 1.4 Implementation Notes
- Dashboard module: **Organization Overview** — org chart visualization, role assignments, vacancy tracking
- Dashboard module: **Governance Calendar** — meeting schedule, minutes, action items
- Data needed: HR feed for headcount, SDEA registry, committee membership lists

---

## 2. Regulatory Framework — US

### 2.1 Primary Legislation & Regulations

| Regulation | Scope | Key Requirements |
|-----------|-------|------------------|
| **21 CFR 312.32** | IND Safety Reporting | 7-day (fatal/life-threatening unexpected) and 15-day (serious unexpected) IND safety reports |
| **21 CFR 312.33** | IND Annual Reports | Annual summary of clinical experience and safety data |
| **21 CFR 314.80** | NDA Post-Marketing AE Reporting | 15-day alert reports (serious, unexpected); periodic reports quarterly (Yr 1-3), then annually |
| **21 CFR 314.81(b)(2)** | NDA Annual Reports | Annual report including AE summary, literature review |
| **21 CFR 314.98** | ANDA Post-Marketing | Same requirements as 314.80 for generics |
| **21 CFR 600.80** | BLA Post-Marketing | Biologic-specific AE reporting; 15-day/periodic structure mirrors 314.80 |
| **21 CFR Part 11** | Electronic Records | Validation, audit trails, electronic signatures |
| **21 CFR 312.64** | Investigator Reports | Investigators must report AEs to sponsors |
| **21 CFR 312.56** | Sponsor Obligations | Sponsor must review and evaluate all AE information |

### 2.2 Key FDA Guidance Documents

| Guidance | Year | Key Points |
|----------|------|------------|
| Safety Reporting Requirements for INDs/BA/BE Studies | 2012 (Rev 2015) | Clarifies what is "suspected" and when ICSRs needed |
| Post-Marketing Safety Reports: What to Report | 2001 | Defines what constitutes a reportable AE |
| MedWatch 3500A Instructions | Current | Form completion for mandatory reports |
| Good Pharmacovigilance Practices and Pharmacoepidemiologic Assessment | 2005 | Good PV practices, signal detection expectations |
| Expedited Safety Reporting for Human Drug/Biologic Products | 2015 | IND safety report content and format |
| FDA Adverse Event Reporting System (FAERS) | Ongoing | Database of post-marketing AE reports |
| Sentinel System | Ongoing | Active surveillance using real-world data |
| Safety Reporting Portal (SRP) | Current | Electronic submission gateway for safety reports |
| REMS Guidance (various) | 2019-2022 | REMS development, assessment, modification |

### 2.3 US Reporting Timelines

| Report Type | Timeline | Regulation |
|------------|----------|------------|
| IND 7-day | Within 7 calendar days (fatal/life-threatening unexpected SUSAR) | 21 CFR 312.32(c)(2) |
| IND 15-day | Within 15 calendar days (serious unexpected SUSAR) | 21 CFR 312.32(c)(1) |
| IND Annual Report | Within 60 days of IND anniversary | 21 CFR 312.33 |
| NDA/BLA 15-day Alert | Within 15 calendar days (serious, unexpected) | 21 CFR 314.80(c)(1) |
| NDA Periodic Report | Quarterly (Yr 1-3), then annually | 21 CFR 314.80(c)(2) |
| NDA Annual Report | Within 60 days of approval anniversary | 21 CFR 314.81(b)(2) |
| Field Alert Report | Within 3 days of information | 21 CFR 314.81(b)(1) |
| REMS Assessment | Per REMS timetable (12, 18, 36 months typical) | FD&C Act §505-1 |
| PADER (Pediatric) | Annually for 5 years post pediatric study | PREA §505B |

### 2.4 FDA Safety Actions

| Action | Authority | Trigger |
|--------|-----------|---------|
| Boxed Warning | 21 CFR 201.57(c)(1) | Serious risk that can be mitigated by awareness |
| REMS | FD&C Act §505-1 | Risk requires active management beyond labeling |
| Dear Healthcare Provider Letter (DHCP) | FDA Guidance | Urgent safety communication |
| Drug Safety Communication (DSC) | FDA initiative | Emerging safety issue communicated to public |
| Market Withdrawal/Recall | 21 CFR Part 7 | Benefit-risk no longer favorable |
| Clinical Hold | 21 CFR 312.42 | Unreasonable risk to trial subjects |

### 2.5 Implementation Notes
- Dashboard module: **US Compliance Tracker** — per-product status of all US reporting obligations
- Dashboard module: **FDA Communication Log** — track DSCs, DHCP letters, FDA queries
- Data needed: Product registry with IND/NDA/BLA numbers, approval dates, REMS status
- Track: 314.80 periodic report due dates, IND annual report due dates, REMS assessment windows

---

## 3. Regulatory Framework — EU

### 3.1 Primary Legislation

| Legislation | Scope |
|------------|-------|
| **Directive 2001/83/EC** (Title IX, as amended) | Core PV obligations for MAHs; establishes QPPV requirement |
| **Regulation (EC) No 726/2004** (as amended) | Centrally authorized products; EMA role in PV |
| **Directive 2010/84/EU** | Major PV amendment — strengthened PV system, added PSMF, added RMP requirements |
| **Regulation (EU) No 1235/2010** | Amended 726/2004 in parallel with 2010/84/EU |
| **Implementing Regulation (EU) No 520/2012** | Detailed rules on PV activities, PSMF content, master file |
| **Commission Implementing Regulation (EU) 2025/1466** | New (Feb 2026) — updated electronic reporting, EudraVigilance changes |
| **Clinical Trials Regulation (EU) No 536/2014** | Clinical trial safety reporting; CTIS system |
| **Delegated Regulation (EU) 2017/1569** | Commission delegated acts on PV |

### 3.2 Good Pharmacovigilance Practices (GVP) Modules

| Module | Title | Key Content |
|--------|-------|-------------|
| **I** (Rev 3) | PV Systems and Quality Systems | PSMF, quality management, PV system description |
| **II** (Rev 3) | PV System Master File | Structure and content of PSMF |
| **III** (Rev 1) | PV Inspections | Inspection procedures, preparedness |
| **IV** | Audit | Internal/external audit requirements |
| **V** (Rev 2) | Risk Management Systems | RMP structure and content, implementation |
| **VI** (Rev 2) | Collection, Management, Submission of ICSRs | Case processing, Day 0, seriousness, causality, submission |
| **VII** (Rev 1) | Periodic Safety Update Report | PSUR/PBRER format and content |
| **VIII** (Rev 4) | Post-Authorization Safety Studies | PASS design, registration, reporting |
| **IX** (Rev 1) | Signal Management | Signal detection, validation, evaluation, action |
| **X** (Rev 1) | Additional Monitoring | Black triangle ▼ scheme, enhanced monitoring |
| **XII** | Post-Authorization Efficacy Studies | PAES requirements |
| **XV** | Safety Communication | DHPC, public statements, media |
| **XVI** (Rev 3) | Risk Minimization Measures | Educational materials, controlled access, pregnancy prevention |
| **P.I** (Rev 5) | Vaccines PV | Vaccine-specific guidance |
| **P.II** (Rev 3) | Non-interventional Studies | Study design and protocol considerations |
| **P.IV** | Pregnancy and Lactation | Exposure tracking, pregnancy registries |

### 3.3 EU Reporting Requirements

| Report Type | Timeline | Reference |
|-------------|----------|-----------|
| Serious EU ICSRs | 15 days to EudraVigilance | GVP VI, Art 107(3) Dir 2001/83/EC |
| Non-serious EU ICSRs | 90 days to EudraVigilance | GVP VI, Art 107(3) |
| Serious non-EU ICSRs | 15 days to EudraVigilance | GVP VI |
| Non-serious non-EU ICSRs | 90 days to EudraVigilance | GVP VI |
| SUSAR (Clinical Trials) | 7 days (fatal/life-threatening) / 15 days (other serious) | CTR 536/2014 Art 42 |
| PSUR/PBRER | Per EURD list or as specified | GVP VII, ICH E2C(R2) |
| RMP Update | With new application, on request, significant change | GVP V |
| Annual Safety Report (ASR) | Annually per trial | CTR 536/2014 Art 43 |
| DHPC | Before dissemination: EMA/NCA review required | GVP XV |
| Signal Assessment | Per GVP IX timelines | PRAC procedures |

### 3.4 Key EU Systems

| System | Purpose |
|--------|---------|
| **EudraVigilance (EV)** | EU safety database; ICSR submission and retrieval |
| **EVDAS** | EudraVigilance Data Analysis System — signal detection |
| **CTIS** | Clinical Trials Information System (per CTR 536/2014) |
| **XEVMPD / Art 57 Database** | Product/substance registration |
| **EURD List** | EU Reference Dates list — harmonizes PSUR/PBRER submission dates |

### 3.5 Implementation Notes
- Dashboard module: **EU Compliance Tracker** — per-product GVP compliance status
- Dashboard module: **QPPV/LPPV Network** — contact details, delegation of duties, availability
- Dashboard module: **PSMF Status** — current version, last audit, pending updates
- Dashboard module: **RMP Tracker** — RMP version, last submission, pending commitments
- Data needed: EudraVigilance submission stats, EURD reference dates, PSMF metadata
- Track: PSUR due dates (from EURD list), RMP milestones, PASS/PAES commitments

---

## 4. ICH Guidelines

### 4.1 Core Safety Guidelines

| Guideline | Title | Key Application |
|-----------|-------|-----------------|
| **E2A** | Clinical Safety Data Management: Definitions and Standards | Defines "adverse event," "serious," seriousness criteria (death, life-threatening, hospitalization, disability, congenital anomaly, important medical event) |
| **E2B(R3)** | Electronic Transmission of ICSRs | Standard format for electronic ICSR (XML-based ICH ICSR); data elements, validation rules |
| **E2C(R2)** | Periodic Benefit-Risk Evaluation Report (PBRER) | Replaces PSUR; format for periodic aggregate safety reports |
| **E2D** (R1 Step 2, 2024) | Post-Approval Safety Data Management | Covers post-marketing expedited and periodic reporting |
| **E2E** | Pharmacovigilance Planning | Safety specification and PV plan (incorporated into RMP) |
| **E2F** | Development Safety Update Report (DSUR) | Annual safety summary for investigational products |
| **E6(R3)** | Good Clinical Practice (Step 4, 2023) | Updated GCP including risk-based monitoring, safety reporting in trials |
| **M1** | MedDRA | Medical Dictionary for Regulatory Activities — standardized coding |
| **E1** | Extent of Population Exposure | Minimum safety database for chronic conditions (1500 patients, 300-600 for 6-12 months) |

### 4.2 CIOMS Working Groups

| Working Group | Topic | Key Output |
|--------------|-------|------------|
| **CIOMS I** | Expedited Reporting | Foundation for expedited ICSR reporting |
| **CIOMS V** | Current Challenges in PV | PV best practices, signal management |
| **CIOMS VIII** | Signal Detection | Practical approaches to signal detection |
| **CIOMS X** | Meta-analysis for Safety | Methods for aggregating safety data |
| **CIOMS XIV** (2024) | AI in Pharmacovigilance | Framework for responsible AI use in PV |

### 4.3 Implementation Notes
- All data structures must conform to ICH E2B(R3)
- MedDRA version management critical — track current version, mapping tables
- Dashboard should reference ICH guidelines as regulatory basis for each feature

---

## 5. ICSR Case Processing & Safety Data Management

### 5.1 Case Processing Lifecycle

```
  INTAKE → TRIAGE → DATA ENTRY → MEDICAL REVIEW → CODING → QUALITY → SUBMISSION → FOLLOW-UP
    |         |          |              |             |         |          |            |
  Sources   Day 0    Demographics   Causality     MedDRA    QC/QA    E2B(R3)    Scheduled
  - HCPs   Determ.   Product info   Assessment   (PT, LLT)  Check   to RA       queries
  - Patients         Event details  Seriousness            Audit   EV/FAERS
  - Trials           Reporter info  Listedness/            trail   Partner
  - Lit               Narrative     Expectedness                   notif.
  - Solicited
  - Partners
```

### 5.2 Minimum Information for a Valid Case (Day 0)

Per ICH E2B(R3) and GVP VI, a valid ICSR requires all four:
1. **Identifiable reporter** (name, initials, or qualification)
2. **Identifiable patient** (name, initials, age, sex, or any identifier)
3. **Suspect medicinal product** (name — brand, generic, or description)
4. **Suspect adverse reaction** (at least one)

**Day 0** = date all 4 minimum criteria are first available to the organization.

### 5.3 Seriousness Criteria (ICH E2A)

| Criterion | Code |
|-----------|------|
| Results in death | DE |
| Life-threatening | LT |
| Requires inpatient hospitalization or prolongs existing hospitalization | HO |
| Results in persistent or significant disability/incapacity | DS |
| Congenital anomaly/birth defect | CA |
| Other important medical event (may require medical judgment) | OT |

### 5.4 Causality Assessment Methods

| Method | Description | Reference |
|--------|-------------|-----------|
| WHO-UMC System | Certain / Probable / Possible / Unlikely / Conditional / Unassessable | WHO-UMC criteria |
| Naranjo Algorithm | Scoring system (10 questions, score ≥9 definite, 5-8 probable, 1-4 possible, ≤0 doubtful) | Naranjo et al., 1981 |
| Company/Sponsor Assessment | Based on Bradford Hill criteria + clinical judgment | ICH E2A, GVP VI |

**EU Requirement:** MAH must provide causality assessment for every ICSR (GVP VI.C.6).

### 5.5 MedDRA Coding Hierarchy

```
SOC (System Organ Class)          — 27 SOCs (e.g., "Cardiac disorders")
  └─ HLGT (High Level Group Term) — ~337 HLGTs
       └─ HLT (High Level Term)   — ~1,737 HLTs
            └─ PT (Preferred Term) — ~27,000 PTs (primary coding level)
                 └─ LLT (Lowest Level Term) — ~83,000 LLTs (verbatim mapping)
```

**Key:** Code to LLT (closest to verbatim), report at PT level. SOC assignment follows primary SOC convention.
**Ref:** ICH M1 (MedDRA); MedDRA Term Selection: Points to Consider (MedDRA MSSO)

### 5.6 Case Processing KPIs

| KPI | Target | Regulatory Basis |
|-----|--------|------------------|
| Day 0 to submission (serious) | ≤15 calendar days | GVP VI, 21 CFR 314.80 |
| Day 0 to submission (non-serious) | ≤90 calendar days | GVP VI |
| 7-day expedited (fatal/LT unexpected) | ≤7 calendar days | 21 CFR 312.32(c)(2) |
| Case completeness rate | ≥95% | Internal quality standard |
| Duplicate detection rate | Track and trend | GVP VI |
| Case backlog (overdue cases) | 0 | Internal compliance target |
| Follow-up response rate | ≥80% | Internal quality standard |
| Coding accuracy rate | ≥98% | Internal quality standard |
| Medical review completion | 100% for serious cases | GVP VI |

### 5.7 Safety Database Systems

| System | Vendor | Key Features |
|--------|--------|--------------|
| Oracle Argus Safety | Oracle | Market leader; integrated with Argus Analytics, Argus Insight |
| LifeSphere Safety | ArisGlobal | AI-assisted case processing, auto-coding |
| Veeva Vault Safety | Veeva | Cloud-native, modern UX, Vault platform integration |
| IQVIA Vigilance Platform | IQVIA | Full PV suite with analytics |

### 5.8 Implementation Notes
- Dashboard module: **Case Processing Pipeline** — real-time case volumes, status by stage, overdue cases
- Dashboard module: **Submission Compliance** — percentage submitted within timelines, trend charts
- Dashboard module: **Case Quality Metrics** — completeness, coding accuracy, QC findings
- Dashboard module: **Intake Sources** — breakdown by source (HCP, patient, trial, literature, partner)
- Data needed: Safety database API/extract for case counts, submission dates, quality metrics
- Key alert: Any case approaching regulatory deadline should trigger red flag

---

## 6. Signal Detection & Safety Surveillance

### 6.1 Signal Management Process (GVP Module IX)

```
SIGNAL DETECTION → SIGNAL VALIDATION → SIGNAL ANALYSIS → SIGNAL ASSESSMENT → RECOMMENDATION → ACTION
       |                   |                  |                  |                 |              |
  Routine           Is it real?        Clinical        Benefit-risk         Regulatory      Label change
  screening         Known signal?      significance    evaluation           action           RMP update
  Data mining       Data quality       Epidemiology    PRAC input           DHPC            REMS mod
  Literature        Biological         Comparative     Committee            Restriction      Study
  review            plausibility       data            review               Withdrawal       PASS/PAES
```

**Ref:** GVP Module IX (Rev 1); CIOMS VIII

### 6.2 Signal Detection Methods

#### 6.2.1 Disproportionality Analysis (Quantitative)

| Method | Statistic | Description | Threshold |
|--------|-----------|-------------|-----------|
| **PRR** | Proportional Reporting Ratio | Ratio of proportion of a specific AE for a drug vs all other drugs | PRR ≥ 2, Chi² ≥ 4, N ≥ 3 |
| **ROR** | Reporting Odds Ratio | Odds ratio from 2×2 table | Lower 95% CI > 1 |
| **EBGM/MGPS** | Empirical Bayes Geometric Mean | Bayesian shrinkage (FDA method, DuMouchel) | EB05 ≥ 2 |
| **BCPNN/IC** | Information Component | Bayesian (WHO-UMC method) | IC025 > 0 |

#### 6.2.2 Other Methods

| Method | Application | Reference |
|--------|-------------|-----------|
| **Time-to-Onset Analysis** | Weibull distribution to identify temporal clustering | CIOMS VIII |
| **Literature Surveillance** | Systematic review of published case reports and studies | GVP IX, Module VI |
| **Clinical Trial Signal Detection** | Blinded/unblinded review of trial AE data, MedDRA SMQs | ICH E2F |
| **Active Surveillance** | Sentinel (US), DARWIN EU (EU) | FDA Sentinel Initiative, EMA |
| **Patient Registries** | Disease-specific or product-specific registries | GVP Module VIII |

### 6.3 Standardised MedDRA Queries (SMQs)

Pre-defined groupings of PTs for systematic signal identification:
- **Narrow scope:** High specificity, fewer false positives
- **Broad scope:** High sensitivity, captures possible related terms
- **Examples:** Anaphylactic reaction (SMQ), Drug-related hepatic disorders (SMQ), Rhabdomyolysis/myopathy (SMQ), Torsade de Pointes/QT prolongation (SMQ)

**Ref:** MedDRA MSSO; ICH E2B(R3) Appendix

### 6.4 EudraVigilance Data Analysis System (EVDAS)

- EMA's signal detection tool for centrally authorized products
- Uses IC/BCPNN method
- eRMR (electronic Reaction Monitoring Report) — automated statistical signals
- MLR (Monthly Line Listing Report) — distributed to MAHs for review
- **MAH obligation:** Review EVDAS output, respond to PRAC signal procedures

### 6.5 Signal Management KPIs

| KPI | Target | Reference |
|-----|--------|-----------|
| Signal detection review cycle | Monthly minimum | GVP IX |
| Time from signal detection to validation | ≤30 days | Internal target |
| Time from validated signal to assessment completion | ≤60 days (routine), ≤30 days (urgent) | PRAC timelines |
| Signal closure rate | Track and trend | Internal |
| False positive rate | Track and trend | Quality metric |
| Literature review coverage | 100% of defined sources | GVP IX, Module VI |
| EVDAS eRMR review completion | 100% within 30 days | EMA requirement |

### 6.6 Implementation Notes
- Dashboard module: **Signal Dashboard** — active signals by product, status, priority
- Dashboard module: **Disproportionality Metrics** — visualize PRR/ROR/EBGM/IC trends over time
- Dashboard module: **Literature Review Tracker** — search strategy, review status, new findings
- Dashboard module: **Surveillance Heatmap** — geographic/temporal distribution of reported AEs
- Data needed: Safety database aggregate data, EVDAS export, literature search results
- Integration: Connect to existing safety-research-system signal detection engine
- Alert: New statistical signal above threshold → automatic notification to Safety Physician

---

## 7. Aggregate Reporting

### 7.1 Report Types

| Report | Scope | Frequency | Regulatory Basis |
|--------|-------|-----------|------------------|
| **PSUR/PBRER** | Marketed products | Per EURD list (EU); per approval conditions | ICH E2C(R2), GVP VII, 21 CFR 314.80(c)(2) |
| **DSUR** | Investigational products | Annual (per development IBD) | ICH E2F |
| **PADER** | Pediatric studies | Annual for 5 years post pediatric study | PREA §505B, FDA Guidance |
| **IND Annual Report** | US IND | Annual within 60 days of anniversary | 21 CFR 312.33 |
| **NDA Annual Report** | US NDA | Annual within 60 days of anniversary | 21 CFR 314.81(b)(2) |
| **ASR (EU CTR)** | Clinical trials (EU) | Annual per trial | CTR 536/2014 Art 43 |

### 7.2 PBRER/PSUR Structure (ICH E2C(R2))

| Section | Content |
|---------|---------|
| 1. Introduction | Product, reporting interval, regulatory status |
| 2. Worldwide Marketing Authorization Status | Approvals, withdrawals, by country |
| 3. Actions Taken for Safety Reasons | Regulatory actions during interval |
| 4. Changes to Reference Safety Information | Changes to RSI/CCDS |
| 5. Estimated Exposure | Patient exposure data (patient-years, doses sold) |
| 6. Presentation of Data | Summary tabulations of ICSRs |
| 7. Summary of Safety Concerns (SSC) | Updated from RMP if applicable |
| 8. Signal and Risk Evaluation | New signals, updated analysis |
| 9-16. Evaluation sections | Effectiveness, subgroups, late-breaking info |
| 17. Benefit-Risk Analysis | Integrated benefit-risk evaluation |
| 18. Conclusions and Actions | Proposed actions |
| 19. Appendices | Line listings, summary tabulations |

### 7.3 DSUR Structure (ICH E2F)

| Section | Content |
|---------|---------|
| Executive Summary | Key findings and recommendations |
| Introduction | Drug info, development status |
| Worldwide Marketing Authorization Status | If partially marketed |
| Update on Safety Actions | Actions taken during interval |
| Reference Safety Information | Current IB RSI |
| Interval and Cumulative Exposure | Subjects in ongoing/completed trials |
| Data in Summary Tabulations | Serious AEs, deaths, SUSARs |
| Significant Findings | New safety findings from any source |
| Safety-Related Studies | Nonclinical and observational studies |
| Other Safety Information | Lack of efficacy, overdose, abuse |
| Late-Breaking Information | Post-data-lock information |
| Overall Safety Assessment | Integrated safety evaluation |
| Conclusion | Summary of benefit-risk |
| Appendix | Detailed line listings |

### 7.4 Implementation Notes
- Dashboard module: **Aggregate Report Calendar** — due dates, status, submission tracking
- Dashboard module: **PBRER/DSUR Status Board** — by product, current version, writing stage
- Dashboard module: **EURD Date Tracker** — EU reference dates, data lock points
- Data needed: Product registry with approval dates, EURD list entries, report writing milestones
- Alert: Reports approaching due date (30/15/7 day warnings)
- Integration: Pull AE summary data for report generation from safety database

---

## 8. Risk Management

### 8.1 EU Risk Management Plan (RMP) — GVP Module V

**RMP Structure (7 Parts):**

| Part | Content |
|------|---------|
| I | Product Overview |
| II | Safety Specification (Module SVIII of epidemiology, SI-SVII of identified/potential risks, missing info) |
| III | Pharmacovigilance Plan (routine + additional PV activities) |
| IV | Plans for Post-Authorization Efficacy Studies |
| V | Risk Minimization Measures (routine + additional) |
| VI | Summary of the Risk Management Plan |
| VII | Annexes (worldwide marketed status, SPC/PIL, ongoing/completed PV studies) |

**Key concepts:**
- **Identified Risks:** Adverse reactions with sufficient evidence of causal association
- **Potential Risks:** Safety concerns with data suggesting but not confirming a causal link
- **Missing Information:** Gaps in knowledge (e.g., long-term use, renal impairment, pediatric use, pregnancy)
- **Important identified/potential risks:** Subset requiring specific risk minimization or additional PV activities

**When to update RMP:** New marketing application, significant change to existing RMP, at EMA/NCA request, at PSUR submission if safety concerns changed

**Ref:** GVP Module V (Rev 2, 2024); Regulation (EC) 726/2004 Art 6(1); Dir 2001/83/EC Art 8(3)(iaa)

### 8.2 US REMS (Risk Evaluation and Mitigation Strategies)

**REMS Elements (FD&C Act §505-1):**

| Element | Description | Example |
|---------|-------------|---------|
| Medication Guide | Patient-facing information distributed with dispensing | Most common element |
| Communication Plan | Outreach to HCPs about serious risks | Letters, training materials |
| ETASU (Elements to Assure Safe Use) | Restricted distribution programs | Prescriber certification, patient enrollment, pharmacy certification, dispensing limits |
| Implementation System | Infrastructure to support ETASU | Databases, call centers, restricted distribution networks |
| Timetable for Assessment | Scheduled REMS performance assessment | 18 months, 3 years, 7 years |

**Key REMS Examples:** iPLEDGE (isotretinoin), TIRF REMS (fentanyl products), Clozapine REMS, Vigabatrin REMS

**REMS Assessment Metrics:**
- Process metrics (enrollment, certification rates)
- Outcome metrics (incidence of target adverse outcome)
- Survey metrics (knowledge and behavior of prescribers/patients)

**Ref:** FD&C Act §505-1; FDA REMS Guidance (2019); 21 CFR 314.520

### 8.3 Risk Minimization Measures (EU) — GVP Module XVI (Rev 3)

| Type | Examples |
|------|----------|
| **Routine** | SmPC, PL/PIL, pack size, legal status |
| **Additional** | Educational materials, patient cards, controlled access programs, pregnancy prevention programs, DHPC |

**Evaluation:** Effectiveness of risk minimization measured via indicators defined in RMP Part V.

### 8.4 Implementation Notes
- Dashboard module: **Risk Management Overview** — per-product risk profile (identified/potential risks, missing info)
- Dashboard module: **RMP Status Tracker** — version, last submission, pending Part III/V commitments
- Dashboard module: **REMS Compliance Dashboard** — enrollment rates, certification status, assessment due dates
- Dashboard module: **Risk Minimization Effectiveness** — outcome tracking for additional RMMs
- Data needed: RMP commitments database, REMS enrollment/certification data, effectiveness indicators

---

## 9. Quality System — SOPs, CAPAs & Audits

### 9.1 Quality Management System (QMS) Foundation

**Ref:** GVP Module I (Rev 3); ICH Q10; 21 CFR Part 11; ISO 9001 (principles)

**PV QMS Components:**
- Document management (SOPs, WIs, templates, forms)
- Training management and competency tracking
- Deviation and CAPA management
- Change control
- Internal audit program
- Management review
- Continuous improvement
- Vendor/partner qualification and oversight

### 9.2 Required SOPs Inventory

| Category | SOPs | Regulatory Basis |
|----------|------|------------------|
| **Case Processing** | | |
| | ICSR Intake and Triage | GVP VI |
| | AE Data Entry and Quality Control | GVP VI, ICH E2B(R3) |
| | Seriousness Assessment | ICH E2A, GVP VI |
| | Causality Assessment | GVP VI, WHO-UMC criteria |
| | MedDRA Coding | ICH M1, MedDRA MSSO |
| | Narrative Writing | GVP VI |
| | Case Follow-up | GVP VI |
| | Duplicate Detection and Management | GVP VI |
| | Case Submission to Regulatory Authorities | GVP VI, 21 CFR 314.80 |
| | Literature Surveillance | GVP VI, Module IX |
| **Signal Management** | | |
| | Signal Detection and Screening | GVP IX |
| | Signal Validation and Prioritization | GVP IX |
| | Signal Assessment and Evaluation | GVP IX |
| | Benefit-Risk Assessment | GVP V, ICH E2C(R2) |
| **Aggregate Reporting** | | |
| | PBRER/PSUR Preparation | ICH E2C(R2), GVP VII |
| | DSUR Preparation | ICH E2F |
| | PADER Preparation | PREA |
| | IND/NDA Annual Reports | 21 CFR 312.33, 314.81 |
| **Risk Management** | | |
| | RMP Development and Maintenance | GVP V |
| | REMS Management | FD&C Act §505-1 |
| | Risk Minimization Measure Implementation | GVP XVI |
| **Clinical Trial Safety** | | |
| | SAE Collection and Reporting | ICH E6(R3) |
| | SUSAR Reporting | CTR 536/2014, 21 CFR 312.32 |
| | Unblinding Procedures | ICH E6(R3), E9(R1) |
| | DSMB/DMC Charter and Operations | FDA DMC Guidance (2006) |
| **Quality & Compliance** | | |
| | PV Training and Competency | GVP Module I |
| | PSMF Maintenance | GVP Module II |
| | Deviation and CAPA Management | GVP Module I |
| | PV Audit Program | GVP Module IV |
| | Inspection Readiness | GVP Module III |
| | Change Control | GVP Module I |
| | Vendor/Partner Qualification | GVP Module I |
| | SDEA Management | GVP Module VI |
| | Document Control | GVP Module I |
| | Archiving and Record Retention | GVP Module I, 21 CFR Part 11 |
| **Safety Communication** | | |
| | DHPC Development and Dissemination | GVP XV |
| | Urgent Safety Restriction | Dir 2001/83/EC Art 22a |
| | Labeling/CCDS Update Process | GVP Module XVI |

### 9.3 CAPA Process

```
DEVIATION/FINDING → ROOT CAUSE ANALYSIS → CORRECTIVE ACTION → PREVENTIVE ACTION → EFFECTIVENESS CHECK
        |                    |                    |                   |                      |
   Identification      Fishbone/5-Why       Fix the issue      Prevent             Verify action
   Documentation       Risk assessment      Implement fix      recurrence           was effective
   Classification      Contributing         Responsible        Systemic              Follow-up
   (Minor/Major/       factors              party + deadline   improvements           audit
    Critical)
```

**CAPA Sources:**
- PV inspections (GVP Module III findings)
- Internal audits (GVP Module IV)
- Quality review findings
- Regulatory authority queries
- Compliance deviations (e.g., late submissions)
- Process failures

**CAPA KPIs:**

| KPI | Target |
|-----|--------|
| CAPA initiation within X days of finding | ≤15 days |
| CAPA on-time closure rate | ≥90% |
| CAPA effectiveness verification rate | 100% |
| Overdue CAPAs | 0 |
| Recurrence rate (same root cause) | <5% |

### 9.4 PSMF (Pharmacovigilance System Master File) — GVP Module II

**Content (per IR 520/2012, Annex I):**

| Section | Content |
|---------|---------|
| QPPV details | Name, CV, contact, delegation of duties |
| Organisational structure | PV org chart, responsibilities |
| Data sources | All sources of safety data |
| Computerised systems | Safety database, signal detection tools |
| PV processes | Summary of all PV processes |
| Quality system | QMS description, audit/inspection findings |
| Contracted activities | List of outsourced PV functions |
| Annex: Logbook | All changes to PSMF with dates |

**Location:** Must be maintained at QPPV site or accessible to QPPV.
**Updates:** Continuously maintained; changes within 30 days of event.

### 9.5 Inspection Readiness — GVP Module III

**Inspection Types:**
- **Routine:** Scheduled, risk-based selection
- **Triggered/For-Cause:** Following safety concern, CAPA non-compliance, signal issue
- **Pre-Authorization:** Before MA granted (centralized procedure)

**Key Inspection Areas:**
- PSMF completeness and currency
- QPPV availability and qualifications
- Case processing timeliness and quality
- Signal management process and outcomes
- Aggregate reporting compliance
- SDEA management
- Training records
- CAPA close-out
- IT system validation (21 CFR Part 11 / Annex 11)

### 9.6 Implementation Notes
- Dashboard module: **SOP Registry** — complete list of SOPs, version, owner, review date, status
- Dashboard module: **CAPA Tracker** — open CAPAs by source, priority, status, aging
- Dashboard module: **Training Compliance** — training completion rates by role, overdue training
- Dashboard module: **Audit & Inspection Calendar** — scheduled audits, findings, CAPA linkage
- Dashboard module: **PSMF Status** — last update, pending changes, logbook entries
- Dashboard module: **Document Control** — pending reviews, expired documents
- Data needed: Quality management system data, training records, CAPA database, audit reports

---

## 10. Clinical Trial Safety

### 10.1 Safety Reporting in Clinical Trials

#### US Requirements (21 CFR 312.32)

| Event Type | Timeline | Recipient | Form |
|------------|----------|-----------|------|
| Fatal/Life-threatening unexpected SUSAR | 7 calendar days (alert) + 8 days (follow-up = 15 total) | FDA + all investigators | IND Safety Report (MedWatch 3500A) |
| Serious unexpected SUSAR | 15 calendar days | FDA + all investigators | IND Safety Report |
| Other safety findings (increased rate, animal findings) | 15 calendar days | FDA + all investigators | IND Safety Report |
| Annual summary | Within 60 days of IND anniversary | FDA | IND Annual Report |

#### EU Requirements (CTR 536/2014)

| Event Type | Timeline | System | Reference |
|------------|----------|--------|-----------|
| Fatal/Life-threatening SUSAR | 7 days initial + 8 days follow-up | EudraVigilance (CTIS) | Art 42(2) |
| Other serious SUSAR | 15 calendar days | EudraVigilance (CTIS) | Art 42(2) |
| Annual Safety Report (ASR) | Annually | CTIS | Art 43 |
| Urgent safety measures | Immediately | NCA/Ethics Committee via CTIS | Art 54 |

### 10.2 SAE/SUSAR Workflow

```
SITE AE REPORT → SPONSOR RECEIPT → TRIAGE → EXPECTEDNESS ASSESSMENT → SUSAR DETERMINATION → REPORTING
       |                |              |              |                       |                    |
  Investigator    24hr target     Serious?     Against Reference        Unexpected +           RA + Ethics
  AE form         for SAEs       Causality?    Safety Info (RSI)        Suspected causal       Committee
  (CRF, eCRF)                    Related?      - IB (investigational)   → SUSAR                Investigators
                                               - SmPC (marketed)        → Expedited report     (per protocol)
```

### 10.3 Reference Safety Information (RSI)

| Context | RSI Document |
|---------|-------------|
| Investigational product (not marketed) | Investigator's Brochure (IB) — Section 7 |
| Investigational use of marketed product | Company Core Data Sheet (CCDS) or IB |
| Marketed product | SmPC / USPI (for expectedness) |

**IB Updates:** Safety section (Section 7) must be updated when new significant safety information emerges.

### 10.4 DSMB/DMC (Data Safety Monitoring Board)

**Ref:** FDA Guidance "Establishment and Operation of Clinical Trial DSMBs" (2006); ICH E6(R3); ICH E9(R1)

| Aspect | Description |
|--------|-------------|
| Composition | Independent clinicians, biostatistician, ethicist; no COI with sponsor |
| Charter | Written charter defining roles, meeting schedule, voting procedures, stopping rules |
| Data access | Unblinded data access (usually via independent statistician) |
| Recommendations | Continue, modify, pause, or terminate the trial |
| Meeting types | Scheduled (data review), ad hoc (urgent safety), organizational |
| Documentation | Closed session minutes (confidential), open session minutes (shared with sponsor) |

### 10.5 Unblinding Procedures

- **For expedited reporting:** Unblind individual cases when needed for regulatory reporting (21 CFR 312.32(c); CTR 536/2014)
- **Maintain overall trial integrity:** Limit unblinding to essential personnel; keep treatment assignment blinded to investigators where possible
- **Emergency unblinding:** 24/7 mechanism for investigator to unblind in medical emergency

**Ref:** ICH E9(R1); ICH E6(R3) Section 5.6

### 10.6 Implementation Notes
- Dashboard module: **Clinical Trial Safety Overview** — active trials, SAE volumes, SUSAR rates
- Dashboard module: **SUSAR Reporting Compliance** — 7/15-day submission tracking
- Dashboard module: **DSMB Meeting Calendar** — upcoming meetings, recommendations log
- Dashboard module: **IB Update Tracker** — current version, pending safety updates
- Dashboard module: **Trial-Level Safety Profiles** — per-trial AE summary, comparative rates
- Data needed: Clinical trial database (CTMS), SAE/SUSAR tracking system, DSMB minutes
- Integration: Link to safety database for trial-sourced cases

---

## 11. Safety Science & Benefit-Risk

### 11.1 Safety Physician Functions

| Function | Description | Reference |
|----------|-------------|-----------|
| Medical assessment of ICSRs | Causality, seriousness, clinical significance | GVP VI |
| Signal evaluation (medical input) | Clinical interpretation of statistical signals | GVP IX |
| Aggregate report authorship | Medical writing for PBRER/DSUR | ICH E2C(R2), E2F |
| Labeling management | CCDS/CCSI updates, SmPC/USPI changes | GVP XVI, 21 CFR 201.57 |
| Benefit-risk assessment | Contribute to product-level B-R evaluation | GVP V, ICH E2C(R2) |
| Regulatory interaction | Respond to safety queries, attend PRAC/FDA meetings | Various |
| Safety input to clinical programs | Safety strategy, protocol safety sections, consent forms | ICH E6(R3) |

### 11.2 Labeling Management

#### US Labeling Changes

| Change Type | Mechanism | Timeline | Reference |
|-------------|-----------|----------|-----------|
| CBE-0 (Changes Being Effected) | Immediate implementation, simultaneous FDA notification | Immediately for safety | 21 CFR 314.70(c)(6)(iii) |
| CBE-30 | Implement immediately, FDA has 30 days to respond | 30 days | 21 CFR 314.70(c) |
| Prior Approval Supplement (PAS) | Requires FDA approval before implementation | Variable | 21 CFR 314.70(b) |
| Annual Report | Minor labeling changes | Annual | 21 CFR 314.70(d) |

#### EU Labeling Changes

| Change Type | Mechanism | Timeline | Reference |
|-------------|-----------|----------|-----------|
| Type IA | Minor, no evaluation needed | Notify within 12 months | Reg (EC) 1234/2008 |
| Type IB | Minor, requires acknowledgment | 30-day procedure | Reg (EC) 1234/2008 |
| Type II | Major (safety-related) | 60-day evaluation | Reg (EC) 1234/2008 |
| Urgent Safety Restriction (USR) | Immediate interim change | Notify NCA immediately | Dir 2001/83/EC Art 22a |

### 11.3 Company Core Data Sheet (CCDS/CCSI)

- **Purpose:** Single reference document for safety information across all markets
- **Maintained by:** MAH/sponsor (global safety or medical affairs)
- **Updates:** Triggered by new safety signals, regulatory requirements, aggregate report findings
- **Relationship:** CCDS drives local label (SmPC/USPI) updates; defines "expected" for ICSR assessment
- **Ref:** CIOMS III/V; ICH E2C(R2)

### 11.4 Benefit-Risk Assessment Frameworks

| Framework | Description | Reference |
|-----------|-------------|-----------|
| **PrOACT-URL** | EMA's structured B-R framework (Problems, Objectives, Alternatives, Consequences, Trade-offs, Uncertainty, Risk tolerance, Linked decisions) | EMA Benefit-Risk Methodology (2010) |
| **BRAT** (Benefit-Risk Action Team) | Systematic framework using value trees and key benefit/risk measures | CIRS/FDA BRAT framework |
| **MCDA** (Multi-Criteria Decision Analysis) | Quantitative scoring of multiple benefit and risk criteria | Various (EMA pilot) |
| **NNT/NNH** | Number Needed to Treat / Number Needed to Harm | Standard pharmacoepi |
| **Effects Table** | Tabular display of benefits and risks with magnitude, frequency, seriousness | EMA Benefit-Risk template |

### 11.5 Implementation Notes
- Dashboard module: **Benefit-Risk Summary** — per-product B-R visualization (effects table format)
- Dashboard module: **Labeling Status** — CCDS version, pending changes, SmPC/USPI sync status
- Dashboard module: **Safety Science Projects** — ongoing evaluations, studies, analyses
- Data needed: CCDS repository, labeling change tracking, B-R assessment documents

---

## 12. Technology Landscape

### 12.1 Core PV Systems

| Category | Systems | Purpose |
|----------|---------|---------|
| Safety Database | Oracle Argus, Veeva Vault Safety, ArisGlobal LifeSphere | ICSR management, submission |
| Signal Detection | Empirica Signal (Oracle), ARISg Signal, EVDAS, custom | Quantitative signal detection |
| Aggregate Reporting | Argus Analytics, custom, contracted | PBRER/DSUR data and generation |
| Literature Monitoring | Embase, PubMed, contracted services | Safety literature surveillance |
| Medical Coding | MedDRA browser, auto-coding (AI-assisted) | AE and product coding |
| Submission Gateway | EudraVigilance (EVWEB/Gateway), FDA ESG/SRP | ICSR electronic submission |
| Document Management | Veeva Vault QualityDocs, SharePoint, custom | SOP, PSMF, training records |
| Clinical Safety | Medidata Rave Safety, Oracle InForm, CTMS integration | SAE/SUSAR from trials |
| BI/Analytics | Tableau, Power BI, Spotfire, custom dashboards | Safety metrics and KPIs |

### 12.2 Emerging Technology (AI/ML in PV)

**Ref:** CIOMS Working Group XIV (2024) — "Artificial Intelligence in Pharmacovigilance"

| Application | Status | Consideration |
|-------------|--------|---------------|
| Auto-coding (MedDRA) | Production use | ArisGlobal, Aris LSSS, others; requires QC validation |
| Case intake triage | Emerging | NLP for source documents, auto-classification |
| Duplicate detection | Production use | ML-based matching algorithms |
| Narrative generation | Pilot phase | LLM-assisted narrative drafting |
| Signal detection enhancement | Research/pilot | ML augmentation of disproportionality methods |
| Literature screening | Production use | NLP for relevance filtering |
| Predictive safety analytics | Research | Time-series prediction of AE trends |

### 12.3 Integration Architecture

```
                    ┌─────────────────────────────────┐
                    │   PATIENT SAFETY DASHBOARD       │
                    │   (Head of Safety View)          │
                    └──────────┬──────────────────────┘
                               │ API Layer
        ┌──────────┬───────────┼───────────┬──────────┐
        │          │           │           │          │
   Safety DB   Signal      Clinical    Quality    Regulatory
   (ICSRs)     Detection   Trial DB    System     Intelligence
   ┌────┐      ┌────┐      ┌────┐     ┌────┐      ┌────┐
   │Argus│     │EVDAS│     │CTMS │    │QMS  │     │RegIntel│
   │Veeva│     │Empir│     │EDC  │    │CAPA │     │Horizon │
   │etc. │     │ica  │     │IWRS │    │Train│     │Scan    │
   └────┘      └────┘      └────┘     └────┘      └────┘
```

### 12.4 Implementation Notes
- Our existing safety-research-system provides a strong foundation for the analytics/signal detection layer
- Dashboard should aggregate data from multiple source systems
- API-first architecture for extensibility (already present in current system)
- Consider role-based access: Head of Safety sees portfolio view; Safety Physicians see product-level detail

---

## 13. KPIs & Dashboard Metrics

### 13.1 Executive-Level KPIs (Head of Safety Dashboard)

#### Compliance & Timeliness

| KPI | Definition | Target | RAG Thresholds |
|-----|------------|--------|----------------|
| ICSR Submission Compliance (Serious) | % of serious ICSRs submitted within 15 days | ≥98% | G: ≥98%, A: 95-97%, R: <95% |
| ICSR Submission Compliance (Non-serious) | % of non-serious ICSRs submitted within 90 days | ≥95% | G: ≥95%, A: 90-94%, R: <90% |
| 7-Day Report Compliance | % of IND fatal/LT unexpected submitted within 7 days | 100% | G: 100%, A: ≥95%, R: <95% |
| Aggregate Report On-time Submission | % of PBRER/DSUR/PADER submitted by due date | 100% | G: 100%, A: ≥95%, R: <95% |
| Case Backlog | Number of overdue cases | 0 | G: 0, A: 1-5, R: >5 |

#### Quality

| KPI | Definition | Target |
|-----|------------|--------|
| Case Completeness | % of cases meeting all required data fields | ≥95% |
| Coding Accuracy | % of MedDRA coding verified as correct on QC | ≥98% |
| CAPA On-time Closure | % of CAPAs closed within target timeframe | ≥90% |
| Training Compliance | % of PV staff with current, completed training | ≥95% |
| SOP Currency | % of SOPs within review cycle (e.g., every 2 years) | 100% |

#### Safety Surveillance

| KPI | Definition | Target |
|-----|------------|--------|
| Active Signals Under Review | Count of validated signals in assessment | Track & trend |
| Signal-to-Action Time | Median days from validated signal to recommended action | ≤60 days |
| New Signals Detected (Period) | Number of new signals detected in reporting period | Track & trend |
| EVDAS eRMR Review Completion | % of eRMRs reviewed within 30 days | 100% |

#### Portfolio Health

| KPI | Definition | Target |
|-----|------------|--------|
| Products with Active RMP Commitments | Count of products with outstanding RMP commitments | Track |
| REMS Assessment Compliance | % of REMS assessments submitted on time | 100% |
| Labeling Updates Pending | Number of pending CCDS/SmPC/USPI updates | Track |
| Inspection Readiness Score | Self-assessment score (audit findings resolved) | ≥90% |

### 13.2 Operational KPIs (Drill-Down)

| Area | KPI | Target |
|------|-----|--------|
| Case Processing | Average time: receipt to submission | Track trend |
| Case Processing | Cases received per month (by source) | Track trend |
| Case Processing | Serious-to-non-serious ratio | Track trend |
| Signal Detection | Number of drug-event pairs screened | Track |
| Signal Detection | Disproportionality alerts generated | Track |
| Clinical Trials | SAEs received per trial per month | Track |
| Clinical Trials | SUSAR reporting compliance rate | ≥98% |
| Aggregate Reporting | Average days before deadline (submission buffer) | ≥15 days |
| Quality | Deviations per quarter | Track trend |
| Quality | Audit findings (critical/major/minor) | 0 critical |
| Partner Management | SDEA compliance rate | 100% |
| Literature | Articles screened per month | Track |
| Literature | Valid ICSRs from literature | Track |

### 13.3 Dashboard Layout Concept

```
┌─────────────────────────────────────────────────────────────────────┐
│  PATIENT SAFETY DASHBOARD — HEAD OF SAFETY VIEW         [Date]     │
├───────────────┬───────────────┬──────────────┬──────────────────────┤
│ COMPLIANCE    │ QUALITY       │ SIGNALS      │ PORTFOLIO            │
│ ●98.5% ICSR  │ ●96% Complete │ ●3 Active    │ ●12 Products         │
│ ●100% 7-day  │ ●99% Coding   │ ●1 New       │ ●2 RMP commits       │
│ ●100% Agg    │ ●92% CAPA     │ ●45d median  │ ●1 Label pending     │
│ ●0 Backlog   │ ●97% Training │ ●100% eRMR   │ ●100% REMS           │
├───────────────┴───────────────┴──────────────┴──────────────────────┤
│ CASE VOLUME TREND          │ SIGNAL ACTIVITY              │ ALERTS │
│ [Line chart: 12mo trend    │ [Heatmap: product x SOC      │ ! 3    │
│  by arm/source/seriousness]│  with signal strength]        │ items  │
├────────────────────────────┼────────────────────────────────┤       │
│ UPCOMING DEADLINES         │ ACTIVE TRIALS SAFETY           │       │
│ - PBRER Product A (15d)    │ - Trial 001: 5 SAEs/mo        │       │
│ - DSUR Product B (30d)     │ - Trial 002: DSMB 03/15       │       │
│ - REMS Assess C (45d)      │ - Trial 003: 2 SUSARs         │       │
├────────────────────────────┴────────────────────────────────┴───────┤
│ REGULATORY INTELLIGENCE    │ QUALITY METRICS                        │
│ - New GVP XVI Rev 3        │ [Bar chart: CAPAs by status/aging]    │
│ - IR 2025/1466 effective   │ [Pie: Deviations by category]         │
│ - FDA DSC: Drug X          │ [Training completion by role]          │
└────────────────────────────┴────────────────────────────────────────┘
```

### 13.4 Implementation Notes
- All KPIs should have historical trending (min 12 months)
- RAG (Red/Amber/Green) color coding for compliance KPIs
- Drill-down capability: Executive → Operational → Product-level → Case-level
- Alert system: Push notifications for approaching deadlines, compliance breaches
- Export capability for board presentations and regulatory submissions

---

## 14. Geographic Expansion Framework

### 14.1 Expansion Approach

The system is designed US + EU first, with a modular architecture that supports adding new regions:

| Region | Key Considerations | Priority |
|--------|-------------------|----------|
| **Japan (PMDA)** | J-GVP, DSUR equivalent, unique reporting requirements, local PPSD | High |
| **China (NMPA)** | GVP (China), unique case processing rules, local reporting | High |
| **Canada (Health Canada)** | MHPD, similar to US requirements, C.01.016-017 | Medium |
| **UK (MHRA)** | Post-Brexit: UK GVP (mirrors EU GVP), MHRA Yellow Card | Medium |
| **Australia (TGA)** | Largely aligned with ICH, Adverse Event Management System | Medium |
| **Switzerland (Swissmedic)** | EEA-aligned requirements, separate reporting gateway | Low |
| **ROW (Rest of World)** | Reference country approach, WHO Programme membership | As needed |

### 14.2 Architecture for Expansion

Each region module should include:
1. **Regulatory Reference Table** — local laws, regulations, guidance (equivalent to Sections 2-3 of this plan)
2. **Reporting Requirements** — timelines, formats, submission gateways
3. **Local Roles** — LPPV equivalent, qualified person requirements
4. **KPI Adjustments** — any region-specific compliance targets
5. **SDEA Considerations** — data exchange with local partners/distributors

### 14.3 Implementation Notes
- Modular regulatory reference system: each region = pluggable module
- Shared core: ICH guidelines apply globally
- Region-specific reporting timelines stored as configuration, not hard-coded
- Multi-language support for dashboard (future)

---

## 15. Implementation Roadmap

### Phase 1: Foundation (MVP)
**Objective:** Core dashboard with compliance tracking and case processing metrics

| Module | Description | Priority |
|--------|-------------|----------|
| Organization Overview | Org chart, roles, governance calendar | P1 |
| Case Processing Pipeline | Real-time case volumes, compliance rates, backlog | P1 |
| Submission Compliance | 15-day/90-day/7-day tracking with RAG | P1 |
| Upcoming Deadlines | Aggregate report calendar, REMS assessments | P1 |
| Regulatory Reference | US + EU regulatory requirements database | P1 |
| Executive KPI Summary | Top-line compliance, quality, signal KPIs | P1 |

### Phase 2: Signal Detection & Quality
**Objective:** Integrate signal detection engine and quality management

| Module | Description | Priority |
|--------|-------------|----------|
| Signal Dashboard | Active signals, heatmap, detection metrics | P2 |
| Disproportionality Analysis | PRR/ROR/EBGM visualization (leverage existing engine) | P2 |
| CAPA Tracker | Open CAPAs, aging, root cause analysis | P2 |
| SOP Registry | SOP inventory, review dates, currency status | P2 |
| Training Compliance | Completion rates by role, overdue items | P2 |
| Quality Metrics | Deviations, audit findings, trends | P2 |

### Phase 3: Clinical Trials & Risk Management
**Objective:** Clinical trial safety integration and risk management tools

| Module | Description | Priority |
|--------|-------------|----------|
| Clinical Trial Safety | Active trials, SAE/SUSAR volumes, DSMB calendar | P3 |
| RMP/REMS Tracker | Per-product risk management status | P3 |
| Benefit-Risk Visualization | Effects tables, B-R summary per product | P3 |
| Labeling Management | CCDS/SmPC/USPI version tracking, pending changes | P3 |

### Phase 4: Advanced Analytics & Expansion
**Objective:** AI-powered analytics and geographic expansion

| Module | Description | Priority |
|--------|-------------|----------|
| Predictive Safety Analytics | ML-based AE trend prediction (enhance existing system) | P4 |
| AI-Assisted Case Processing | Auto-coding, narrative generation, triage | P4 |
| Regulatory Intelligence | Horizon scanning, regulatory change tracking | P4 |
| Geographic Expansion | Japan, China modules | P4 |
| Literature Surveillance AI | NLP-powered literature screening | P4 |

### 15.1 Mapping to Existing System

The current safety-research-system already provides:
- **FastAPI backend** with 40+ endpoints → extend for new modules
- **Signal detection engine** → enhance and integrate into Signal Dashboard
- **26-tab dashboard** → refactor/extend for Head of Safety view
- **MedDRA coding** → leverage for case processing module
- **2242 tests** → maintain test coverage as we build
- **Safety index calculations** → feed into executive KPI module

**Key architectural decisions for implementation (future coding phase):**
1. Add regulatory reference data layer (structured regulation → requirement mapping)
2. Add product registry as core data model (products → reporting obligations)
3. Add timeline engine (calculate due dates per regulation × product × region)
4. Extend dashboard with role-based views (Executive, Safety Physician, Case Processor)
5. Add alert/notification system for compliance deadlines
6. Add document management integration (SOPs, PSMF, audit reports)

---

## Appendix A: Key Industry Organizations

| Organization | Full Name | Relevance |
|-------------|-----------|-----------|
| **ICH** | International Council for Harmonisation | Global regulatory harmonization (E2 series, M1) |
| **CIOMS** | Council for International Organizations of Medical Sciences | PV working groups, best practices |
| **WHO-UMC** | WHO Uppsala Monitoring Centre | Global ICSR database (VigiBase), causality criteria |
| **DIA** | Drug Information Association | PV conferences, training, best practices |
| **ISoP** | International Society of Pharmacovigilance | PV professional society |
| **ISPE** | International Society for Pharmacoepidemiology | Pharmacoepidemiological methods |
| **TransCelerate** | TransCelerate BioPharma | Industry collaboration on PV process standardization |
| **MedDRA MSSO** | MedDRA Maintenance and Support Services Organization | MedDRA maintenance and training |
| **EMA** | European Medicines Agency | EU PV regulation and oversight |
| **FDA** | US Food and Drug Administration | US PV regulation and oversight |
| **MHRA** | Medicines and Healthcare products Regulatory Agency (UK) | UK PV regulation |
| **PMDA** | Pharmaceuticals and Medical Devices Agency (Japan) | Japan PV regulation |

## Appendix B: Regulatory Cross-Reference Matrix

| Functional Area | US Regulation | EU Regulation | ICH Guideline | GVP Module |
|----------------|---------------|---------------|---------------|------------|
| ICSR Collection | 21 CFR 314.80, 312.32 | Dir 2001/83/EC Art 107 | E2D, E2B(R3) | VI |
| Expedited Reporting | 21 CFR 312.32(c), 314.80(c)(1) | Dir 2001/83/EC Art 107(3) | E2A | VI |
| Periodic Reporting | 21 CFR 314.80(c)(2) | Dir 2001/83/EC Art 107c | E2C(R2) | VII |
| Signal Management | FDA Guidance (2005) | Dir 2010/84/EU | — | IX |
| Risk Management | REMS (FD&C §505-1) | Dir 2001/83/EC Art 8(3)(iaa) | E2E | V, XVI |
| PV System/Quality | 21 CFR Part 11 | Dir 2001/83/EC Art 104 | — | I, II, III, IV |
| Clinical Trial Safety | 21 CFR 312.32 | CTR 536/2014 Art 42-43 | E2F, E6(R3) | — |
| Labeling | 21 CFR 201.57, 314.70 | Reg (EC) 1234/2008 | — | XVI |
| Safety Communication | FDA DSC, DHCP | Dir 2001/83/EC Art 106a | — | XV |
| Inspections | 21 CFR Part 312 Subpart D | Dir 2001/83/EC Art 111 | — | III |

## Appendix C: Abbreviations

| Abbreviation | Full Form |
|-------------|-----------|
| AE | Adverse Event |
| ASR | Annual Safety Report |
| B-R | Benefit-Risk |
| CAPA | Corrective and Preventive Action |
| CCDS | Company Core Data Sheet |
| CCSI | Company Core Safety Information |
| CRO | Contract Research Organization |
| CSO | Contract Safety Organization |
| CTIS | Clinical Trials Information System |
| CTR | Clinical Trials Regulation |
| DHCP | Dear Healthcare Provider |
| DMC | Data Monitoring Committee |
| DSUR | Development Safety Update Report |
| EBGM | Empirical Bayes Geometric Mean |
| ETASU | Elements to Assure Safe Use |
| EURD | European Union Reference Dates |
| EVDAS | EudraVigilance Data Analysis System |
| GVP | Good Pharmacovigilance Practices |
| IB | Investigator's Brochure |
| IC | Information Component |
| ICH | International Council for Harmonisation |
| ICSR | Individual Case Safety Report |
| IND | Investigational New Drug |
| LPPV | Local Person Responsible for Pharmacovigilance |
| MAH | Marketing Authorization Holder |
| NCA | National Competent Authority |
| NDA | New Drug Application |
| PADER | Pediatric Adverse Drug Event Report |
| PASS | Post-Authorization Safety Study |
| PAES | Post-Authorization Efficacy Study |
| PBRER | Periodic Benefit-Risk Evaluation Report |
| PRAC | Pharmacovigilance Risk Assessment Committee |
| PRR | Proportional Reporting Ratio |
| PSMF | Pharmacovigilance System Master File |
| PSUR | Periodic Safety Update Report |
| PT | Preferred Term |
| QPPV | Qualified Person Responsible for Pharmacovigilance |
| RAG | Red Amber Green |
| REMS | Risk Evaluation and Mitigation Strategy |
| RMP | Risk Management Plan |
| ROR | Reporting Odds Ratio |
| RSI | Reference Safety Information |
| SAE | Serious Adverse Event |
| SDEA | Safety Data Exchange Agreement |
| SmPC | Summary of Product Characteristics |
| SOC | System Organ Class |
| SOP | Standard Operating Procedure |
| SUSAR | Suspected Unexpected Serious Adverse Reaction |
| USPI | United States Prescribing Information |

---

*Document generated: 2026-03-05*
*Source: Comprehensive research synthesis from US/EU regulatory frameworks, ICH guidelines, GVP modules, CIOMS working groups, and industry best practices.*
