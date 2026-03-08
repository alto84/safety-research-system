# 9. Therapeutic Area Head -- Oncology (NSCLC/EGFR)
> Parent: 2-head-ps | Cross-ref: 1-cmo, 4-signal-mgmt, 6-risk-mgmt, 7-aggregate-reporting

## Role
The Therapeutic Area Head, Oncology provides medical and scientific subject matter expertise for safety evaluation of Prosinertimib, a 3rd-generation EGFR tyrosine kinase inhibitor approved for 2nd-line and subsequent therapy of EGFR-mutant non-small cell lung cancer (NSCLC). This role bridges clinical pharmacology, disease biology, and safety science. The TA Head is the internal authority on EGFR TKI class effects, the NSCLC treatment landscape, and mechanistic plausibility of safety signals. Key responsibilities include biological plausibility assessment for signal evaluation (per GVP Module IX, Section IX.I.4), clinical context for benefit-risk assessments (per ICH E2C(R2) Sections 17-18), and advisory input on risk management measures (per GVP Module V).

## Regulatory Grounding
- EU GVP Module IX (Signal management) -- mechanistic plausibility as validation criterion (IX.I.4)
- EU GVP Module V (Risk management) -- risk characterization, additional risk minimization measures
- ICH E2C(R2) -- PBRER Sections 16 (risks), 17 (benefits), 18 (integrated benefit-risk analysis)
- ICH E2F -- DSUR clinical significance assessment
- ICH E2E -- Pharmacovigilance planning, class-effect considerations
- FDA Approved Drug Products labeling for EGFR TKI class (osimertinib, erlotinib, gefitinib, afatinib, dacomitinib)

---

## Sub-Processes

### a. Mechanistic Plausibility Assessment
When a new signal is validated by Signal Management (4-signal-mgmt, sub-process b), assess biological plausibility based on:
- **EGFR/HER pathway biology** in the relevant tissue type (e.g., EGFR expression in skin, lung, liver, cardiac tissue)
- **Known class effects** of EGFR TKIs (erlotinib, gefitinib, afatinib, osimertinib, dacomitinib) -- frequency, severity, and mechanism
- **Prosinertimib-specific selectivity profile** -- kinase panel data, off-target inhibition (e.g., HER2, HER4, wild-type EGFR)
- **Non-clinical data** -- in vitro kinase panels, repeat-dose animal toxicology, genetic toxicology findings
- **Published literature** -- case reports, mechanistic studies, epidemiological data

**Output:** Mechanistic plausibility statement classified as **High** (established pathway, class precedent), **Medium** (plausible pathway, limited direct evidence), or **Low** (no known mechanism, no class precedent). Include evidence summary with PubMed references. Filed with the Signal Assessment Report (4-signal-mgmt, sub-process c).

**Timeline:** 10 business days from receipt of validated signal notification.

### b. Drug Class Safety Intelligence
Maintain the EGFR TKI class safety reference document. Continuously track safety data from competitor products and regulatory actions:

| Product | Brand | Generation | Key Safety Signals |
|---------|-------|------------|-------------------|
| Osimertinib | TAGRISSO | 3rd | ILD (3.5%), QTc prolongation, cardiomyopathy (LVEF decline), dermatologic |
| Erlotinib | TARCEVA | 1st | ILD (0.8%), hepatotoxicity, GI perforation, skin rash |
| Gefitinib | IRESSA | 1st | ILD (1-3%, higher in Japanese population), hepatotoxicity |
| Afatinib | GILOTRIF | 2nd | Diarrhea (96%), skin rash (89%), hepatotoxicity, ILD (0.7%) |
| Dacomitinib | VIZIMPRO | 2nd | Diarrhea (87%), dermatologic (78%), ILD (2.6%) |

**Known EGFR TKI class effects and approximate incidence ranges:**
- Skin rash / acneiform dermatitis: 40-90%
- Diarrhea: 40-60%
- Hepatotoxicity (ALT/AST elevation): 20-30%
- ILD / pneumonitis: 1-4%
- Cardiac effects (QTc prolongation, LVEF decline): 1-10% depending on agent
- Ocular toxicity (corneal erosion, keratitis): 1-5%
- Paronychia: 10-30%

**Update frequency:** Quarterly, or within 5 business days of any regulatory safety action on a competitor EGFR TKI.

**Key references:** FDA approved labels for all listed products; PMID:28841389 (osimertinib cardiac safety); PMID:17192538 (lapatinib cardiac); PMID:22025146 (vandetanib QT prolongation); NCCN NSCLC Guidelines; ESMO Clinical Practice Guidelines for metastatic NSCLC.

### c. Disease Context for Benefit-Risk
Provide NSCLC treatment landscape context for benefit-risk assessments per ICH E2C(R2) Sections 17-18:

- **Disease severity:** 5-year overall survival for EGFR-mutant NSCLC approximately 30-40% with TKI therapy; median OS 24-38 months depending on line and mutation type
- **Standard of care by line of therapy:**
  - 1L: Osimertinib (FLAURA, PMID:29151359) -- median PFS 18.9 months
  - 2L (post-osimertinib): Platinum-based chemotherapy or clinical trials; limited effective options
  - Prosinertimib positioning: 2nd-line and subsequent therapy
- **Unmet medical need:** Patients progressing on osimertinib (resistance mutations C797S, MET amplification); CNS metastases (30-50% of patients); T790M-negative progression
- **Patient population characteristics:** Median age 60-65 years; higher prevalence in never-smokers, women, East Asian populations; common comorbidities include COPD, cardiovascular disease; ECOG PS 0-1 typical for TKI-eligible patients

**Update frequency:** Annually, or when major clinical trial results or guideline updates change the treatment landscape.

### d. Signal Hypothesis Generation
For emerging safety signals, generate testable mechanistic hypotheses:

1. **Pathway proposal:** Map a biological pathway connecting Prosinertimib's mechanism of action (EGFR/HER kinase inhibition) to the observed adverse event. Reference knowledge graph pathways where applicable.
2. **Biomarker identification:** Identify candidate biomarkers that would support or refute the hypothesis (e.g., serum KL-6 for ILD, troponin/BNP for cardiac signals, EGFR expression in target tissue).
3. **Study design suggestion:** Propose designs to test the hypothesis -- biomarker substudies in ongoing trials, targeted follow-up questionnaires, post-marketing observational studies, or in vitro mechanistic studies.
4. **Hypothesis tracking:** Maintain status for each hypothesis: Generated --> Under Investigation --> Confirmed / Refuted. Document evidence at each transition.

This sub-process embodies the AI-native approach to safety science -- hypothesis-driven investigation rather than purely data-driven detection. Each hypothesis is linked to its originating signal (4-signal-mgmt signal ID).

### e. Aggregate Report Medical Content
Provide TA-specific clinical commentary for aggregate reports authored by 7-aggregate-reporting:

- **PBRER Section 16 (Evaluation of Risks):** Mechanistic interpretation of cumulative safety data; class-effect contextualization; plausibility assessment for new or evolving risks
- **PBRER Section 17 (Evaluation of Benefits):** Efficacy context including response rates, PFS/OS data, CNS activity, quality of life; comparison to available alternatives in 2L+ NSCLC
- **PBRER Section 18 (Integrated Benefit-Risk):** Comparative positioning versus standard of care; assessment of whether the benefit-risk balance remains favorable given the cumulative safety profile and the unmet medical need
- **DSUR clinical significance assessment:** Interpretation of SAE/AESI patterns from ongoing PROSPER trials; mechanistic relevance of new findings

**Timeline:** Draft TA sections within 15 business days of data lock point; final review within 5 business days of receiving the integrated draft.

### f. Cross-Functional Safety Communication
Translate safety signals and aggregate safety data into clinically meaningful communication for non-PV stakeholders:

- **Investigators:** Safety letters per ICH E6(R3); Investigator's Brochure safety update sections
- **Commercial / Medical Affairs:** Safety talking points for HCP engagement; responses to unsolicited medical information requests; advisory board safety briefing materials
- **Regulatory submissions:** Clinical significance narratives for safety-related variations, CBE-0 supplements, and responses to regulatory authority questions
- **Publications:** Safety sections for clinical trial manuscripts; contribution to class-effect review articles

All communications must be consistent with the approved label and the CCSI/CCDS.

---

## Escalation Path
- **Reports to:** Head of Patient Safety (2-head-ps)
- **Escalate immediately if:**
  - Mechanistic analysis suggests a previously unrecognized target organ toxicity
  - Class-effect data from a competitor product materially changes the benefit-risk assessment for Prosinertimib
  - Regulatory safety action on a competitor EGFR TKI (e.g., boxed warning, REMS, withdrawal) has implications for Prosinertimib positioning
  - New published evidence contradicts the established mechanistic plausibility assessment for a labeled risk
- **Escalate at next SMT:** Updated class safety intelligence, revised plausibility assessments, hypothesis status transitions

## Dashboard Integration
- **Section 16:** AI Safety Intelligence -- class safety comparison, mechanistic plausibility tracker, hypothesis pipeline, disease landscape context

---

## References

- references/ich_fda_summaries.md -- ICH E2C(R2), E2E, E2F
- references/gvp_module_summaries.md -- GVP Modules V, IX
