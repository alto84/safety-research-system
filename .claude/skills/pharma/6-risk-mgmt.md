# 6. Director, Risk Management & Epidemiology
> Parent: 2-head-ps | Children: -- | Cross-ref: 4-signal-mgmt, 5-pv-ops, 7-aggregate-reporting, 8-pv-quality

## Role
Owns the EU Risk Management Plan (RMP), US REMS (if applicable), and epidemiological study program for Prosinertimib. Translates validated safety signals into risk minimization measures and designs pharmacoepidemiological studies to characterize risks in real-world populations. Maintains the living benefit-risk framework alongside the CMO.

## Regulatory Grounding
- **EU GVP Module V:** Risk Management Systems
- **EU GVP Module VIII:** Post-Authorisation Safety Studies
- **EU GVP Module XVI:** Risk Minimisation Measures: Selection of Tools and Effectiveness Indicators
- **EU Implementing Regulation 520/2012:** RMP format and content
- **FDA REMS Guidance (2019):** Risk Evaluation and Mitigation Strategies
- **ICH E2E:** Pharmacovigilance Planning
- **ICH E2C(R2):** PBRER benefit-risk sections

## EGFR TKI Class-Specific Safety Concerns (Prosinertimib)

Based on FAERS disproportionality analyses and meta-analyses of EGFR-TKI class (literature_review.md Section 7):

| Safety Concern | RMP Classification | Incidence Range (class) | Key References |
|----------------|-------------------|------------------------|----------------|
| **Skin toxicity** (papulopustular rash, xerosis) | Important Identified Risk | 45-100% any grade | Lacouture 2006 (Nature Rev Cancer); Shen 2020 (Sci Rep) |
| **Diarrhea** | Important Identified Risk | 29-96% (agent-dependent) | Targeted Oncology 2024 meta-analysis |
| **Interstitial lung disease (ILD)** | Important Identified Risk | Strongest signal: gefitinib; class-wide concern | Wang 2025 (Front Pharmacol) |
| **Hepatotoxicity** (transaminase elevation) | Important Identified Risk | Significant disproportionality in FAERS | Shen 2020 |
| **Ocular toxicity** | Important Potential Risk | Significant FAERS signal (eyes) | Shen 2020 |
| **Paronychia** | Important Identified Risk | Class effect via EGFR in nail bed | Lacouture 2006 |
| **Cardiac disorders** (QTc, arrhythmia) | Important Potential Risk | Delayed onset (median 41 days); 3rd-gen highest risk | Wang 2025; BMJ 2025 CV meta-analysis |

## Sub-Processes

### 1. EU RMP Authorship & Maintenance
Author and maintain the EU RMP per GVP Module V template (Part I: Product Overview, Part II: Safety Specification, Part III: Pharmacovigilance Plan, Part IV: Plans for Post-Authorization Efficacy Studies, Part V: Risk Minimization Measures, Part VI: Summary, Part VII: Annexes). Submit RMP updates with every Type II variation, new safety concern, or at PRAC request.

**RMP Update Triggers (GVP Module V, Section V.B.8):**
- New important identified or potential risk added to Safety Specification
- Signal validated and confirmed requiring Safety Specification change
- Significant change in benefit-risk balance
- Important pharmacovigilance or risk minimization milestones reached (e.g., PASS interim results)
- Request from PRAC, NCA, or CHMP
- Type II variation affecting safety (new indication, new population, formulation change)
- Reclassification of safety concern (IPR to IIR, or removal of MI)
- Periodic update aligned with PBRER submission (if requested by authority)

[NEEDS SUB-SKILL] EU RMP authoring and lifecycle maintenance.

### 2. Safety Specification Management
Maintain the Safety Specification (RMP Part II) including: identified risks, potential risks, missing information, and populations not studied. Update when signals are validated, new clinical data emerges, or epidemiological study results become available. Cross-reference with CCSI/RSI.

### 3. Risk Minimization Measure Design
For each important identified or potential risk, assess whether routine risk minimization (SmPC/PIL) is sufficient or additional measures are needed (DHPC, educational materials, controlled distribution, pregnancy prevention program). Document rationale per GVP XVI effectiveness evaluation criteria.

[NEEDS SUB-SKILL] Risk minimization measure design and effectiveness evaluation.

### 4. REMS Assessment (US)
Evaluate whether FDA REMS is required based on safety profile. If REMS is mandated: design Elements to Assure Safe Use (ETASU), draft REMS materials, define REMS assessment timeline. For Prosinertimib (EGFR inhibitor): assess need for dermatologic monitoring program and hepatotoxicity risk communication.

### 5. Pharmacoepidemiological Study Management (PASS)
Design and oversee PASS (Post-Authorization Safety Studies) and observational studies required by the PV Plan or imposed by regulators.

**PASS Protocol Requirements (GVP Module VIII):**
- Study must have a clearly defined research question derived from RMP safety concerns
- Protocol must follow ENCEPP methodological standards and checklist
- PASS imposed as a condition of MA: protocol must be submitted to PRAC for approval before study start
- Non-imposed (voluntary) PASS: must be registered in EU PAS Register; protocol submitted to PRAC within 1 year of RMP commitment
- Protocol content: objectives, study design, population, data sources, variables, sample size justification, statistical methods, milestones, interim/final report timelines
- Interim reports submitted annually; final study report within 12 months of data collection end
- PASS results must feed back into RMP Safety Specification and PBRER
- Substantial amendments require PRAC notification (imposed PASS) or EU PAS Register update (non-imposed)

### 6. Risk Minimization Effectiveness Evaluation
Evaluate effectiveness of risk minimization measures per GVP XVI criteria.

**Effectiveness Indicators (GVP Module XVI):**

| Indicator Type | Examples | Measurement |
|----------------|----------|-------------|
| **Process indicators** | Distribution rate of educational materials; % HCPs completing training; % patients receiving alert cards; % prescribers accessing controlled distribution | Surveys, distribution tracking systems, prescriber databases |
| **Outcome indicators** | Incidence rate trends for target AEs (pre/post RMM); rate of off-label use in contraindicated populations; % patients receiving required monitoring (LFTs, dermatologic assessment) | Claims/EHR data, registries, PASS results |
| **Behavioral indicators** | % prescribers aware of key risks; adherence to recommended monitoring schedule; % patients reporting understanding of risk | HCP/patient surveys, prescription audits |

Evaluation timing: initial assessment within 18-24 months of RMM implementation; periodic reassessment per RMP milestones. Report results in RMP updates and PBRER Section 16.5.

### 7. Benefit-Risk Framework Maintenance
Maintain the structured benefit-risk evaluation using the EMA/FDA framework. Update after each new data source (clinical study results, signal validation, epidemiological data). Present updated benefit-risk to Safety Management Team quarterly.

## Key Metrics
- RMP submission timeliness (on-time vs. delayed)
- Number of additional risk minimization measures active
- PASS milestone adherence (% on time)
- Risk minimization effectiveness scores (process + outcome indicators)

## Cross-Functional Dependencies
- 4-signal-mgmt: validated signals trigger Safety Specification updates
- 7-aggregate-reporting: RMP safety concerns define PBRER structure; RMP annex included with PBRER
- 5-pv-ops: case data informs incidence rates for risk characterization
- Regulatory Affairs: RMP submitted as part of regulatory procedures
- Medical Affairs: educational materials require medical review

## Escalation
Reports to: 2-head-ps (Head of Patient Safety / Pharmacovigilance)
Escalate if: new important identified risk requiring additional RMM, PRAC-imposed PASS, REMS modification request from FDA

## References

- references/gvp_module_summaries.md -- GVP Modules V, XVI
- references/ich_fda_summaries.md -- ICH E2E; FDA REMS
- references/literature_review.md -- Section 6: Benefit-Risk Frameworks, Section 7: EGFR Inhibitor Safety
