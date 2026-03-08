# 4. Director, Signal Management & Safety Science
> Parent: 2-head-ps | Children: -- | Cross-ref: 3-qppv, 5-pv-ops, 6-risk-mgmt, 7-aggregate-reporting, 8-pv-quality

## Role
Director, Signal Management & Safety Science. Owns the end-to-end signal management lifecycle for Prosinertimib (EGFR inhibitor, NSCLC): detection, validation, evaluation, prioritization, regulatory notification, label impact assessment, and closure. Accountable to the QPPV and Head of Patient Safety.

## Regulatory Grounding
- **EU GVP Module IX (Rev 1, EMA/827661/2011):** Signal management -- detection (IX.I.3), validation (IX.I.4), confirmation (IX.II), analysis & prioritisation (IX.II), assessment (IX.II), recommendation for action (IX.II), tracking. **Addendum I:** Methodological aspects of signal detection from spontaneous reports.
- **CIOMS VIII (2010):** Practical Aspects of Signal Detection in Pharmacovigilance -- methodology, thresholds, clinical assessment
- **FDA Good Pharmacovigilance Practices and Pharmacoepidemiologic Assessment (2005):** US signal detection obligations, FAERS screening
- **ICH E2E:** Pharmacovigilance Planning -- signal detection strategy as part of the Pharmacovigilance Plan
- **21 CFR 314.80 / 314.81:** Post-marketing signal obligations (US)
- **Regulation (EU) 726/2004, Art 16(3):** PRAC notification timelines for validated signals
- **ICH E2C(R2):** PBRER -- signal evaluation feeds Section 16.3
- **ICH E2F:** DSUR -- signal evaluation feeds Section 10

---

## Sub-Processes

### a. Routine Signal Detection Screening
Run monthly disproportionality analysis against FAERS (openFDA) and perform quarterly EVDAS eRMR review. Apply four statistical methods in parallel: PRR, ROR, EBGM (MGPS), and BCPNN (IC). Document all outputs with data lock point, run date, software version, and database vintage. Per GVP Module IX, Section IX.I.3 (Rev 1, EMA/827661/2011), signal detection must be performed at defined intervals with pre-specified methods and documented thresholds.

**Screening frequency summary:**
| Source | Frequency | Regulatory basis |
|---|---|---|
| FAERS (openFDA) | Monthly | FDA Good PV Practices (2005); 21 CFR 314.80/314.81 |
| EVDAS eRMR review | Within 30 calendar days of receipt; quarterly full query | GVP Module IX, Section IX.I.3.4 |
| MAH safety database | Monthly | GVP Module IX, Section IX.I.3 |
| Literature (PubMed/Embase) | Weekly | GVP Module VI, Appendix 2 |
| Clinical trial SAE/AESI | Biweekly | ICH E2F; DSMB charter |

**FAERS screening frequency:** Monthly (minimum). Each run covers all Prosinertimib brand/generic name variants plus relevant SMQs (Standardised MedDRA Queries).

**EVDAS screening frequency:** Review eRMRs (electronic Reaction Monitoring Reports) within 30 calendar days of receipt per GVP IX.I.3.4. Quarterly full EVDAS query including SDR (Signal Detection from EudraVigilance) outputs. Document all statistical signals of disproportionate reporting (SDRs) flagged by EMA and MAH response to each.

**Literature screening frequency:** Weekly structured PubMed/Embase searches using a validated 42-term search strategy covering Prosinertimib, osimertinib (class), EGFR inhibitor (class), plus all target AE terms. Monthly Cochrane Library review. Per GVP Module VI, literature ICSRs must be submitted within 15 days.

**Clinical trial signal detection:** Biweekly cumulative review of all SAEs and AESIs from ongoing PROSPER trials. MedDRA PT-level frequency tables with time-to-onset analysis. Integration with DSMB unblinded safety data per charter (see sub-process i).

**Detection thresholds (product-specific for Prosinertimib):**

| Method | Threshold | Rationale |
|--------|-----------|-----------|
| PRR | >= 2.0 AND chi-squared >= 4.0 AND N >= 3 | Evans et al. 2001; standard SRS threshold |
| ROR | Lower 95% CI > 1.0 AND N >= 3 | van Puijenbroek et al. 2002 |
| EBGM (MGPS) | EB05 (5th percentile) >= 2.0 | DuMouchel 1999; FDA standard |
| BCPNN (IC) | IC025 (lower 95% credibility) > 0 | Bate et al. 1998; WHO/UMC method |

**Product-specific threshold considerations:** For known EGFR class effects (acneiform rash, diarrhea, ILD, paronychia), apply elevated PRR threshold of >= 3.0 to avoid signal noise from expected class pharmacology. Document class-effect exclusions in the Signal Management Plan. Review thresholds annually or when cumulative case volume exceeds 500 new reports since last review.

**Cross-references:** Validated signals feed into: benefit-risk assessment (see 1-cmo, Sub-process 2), RMP updates (see 6-risk-mgmt), PBRER Section 16.3 (see 7-aggregate-reporting), and QPPV notification (see 3-qppv, Sub-process 5).

[NEEDS SUB-SKILL] Routine signal detection screening automation and workflow.

### b. Signal Validation
For each statistical signal or clinical concern flagged by any source, assemble a signal validation package within 15 business days. The validation assessment must include: (1) biological plausibility based on EGFR mechanism and known pharmacology, (2) temporal relationship analysis (time-to-onset distribution), (3) dose-response evaluation from clinical trial dose-finding data, (4) dechallenge/rechallenge evidence, (5) comparator drug context (osimertinib, erlotinib, gefitinib class data), and (6) confounding factor assessment. Classify as validated signal, refuted signal, or under evaluation per GVP IX.I.4 criteria. A signal is validated when clinical review confirms a new causal association or a new aspect of a known association (per GVP Module IX, Section IX.I.4, three evaluation elements: previous awareness, strength of evidence, clinical relevance).

### c. Signal Evaluation (Full Clinical Assessment)
For each validated signal, complete a Signal Assessment Report (SAR) within 30 calendar days of validation. The SAR must include: cumulative case review with line listing, disproportionality analysis with trend over time, clinical trial incidence comparison, mechanistic assessment referencing the knowledge graph pathways, benefit-risk impact analysis, and regulatory action recommendation. Use the CIOMS VIII framework: seriousness, frequency, preventability, reversibility, and public health impact. The SAR is the primary input to the Safety Management Team (SMT) for decision-making.

[NEEDS SUB-SKILL] Signal evaluation full clinical assessment and SAR authoring.

### d. Signal Prioritization & Classification
Assign every signal a priority level using a structured 2x2 impact-likelihood matrix:

| | Low Likelihood (PRR < 2 or sparse data) | High Likelihood (PRR >= 2 with confirmed trend) |
|---|---|---|
| **High Impact** (fatal/life-threatening, no mitigation) | MEDIUM -- Accelerated evaluation (30 days) | HIGH -- Urgent evaluation (15 days), QPPV notification within 24h |
| **Low Impact** (non-serious, manageable, reversible) | LOW -- Routine evaluation (60 days) | MEDIUM -- Standard evaluation (30 days) |

Maintain the signal tracking log with current status (new / under evaluation / validated / closed-refuted / closed-validated) for all signals. Present the complete signal portfolio at monthly SMT meetings. Track signal-to-action cycle time as a KPI with target of 60 days from detection to SMT decision.

### e. Regulatory Notification (PRAC, FDA)
**PRAC notification (EU) per GVP Module IX, Section IX.III (Rev 1):**

| Scenario | Timeline | Regulatory basis |
|---|---|---|
| Emerging safety issue (urgent public health impact) | 3 working days | GVP IX.III |
| Validated signal -- standalone notification | 30 calendar days from validation | GVP IX.III |
| Validated signal -- important risk requiring variation | 3 months | GVP IX.III |
| Validated signal -- other risk requiring variation | 6 months | GVP IX.III |
| Signal includable in upcoming PSUR (if due within 6 months) | Within PSUR | GVP IX.III / VII |
| Urgent safety restriction (Art 20/31 referral trigger) | 24 hours | Regulation (EU) 726/2004 Art. 16(3) |

Include the signal summary, supporting data, and proposed action in all notifications.

**FDA notification (US):** Report significant new safety information under 21 CFR 314.81(b)(1) as a field alert or via a 15-day Alert Report (for individual serious, unexpected cases) per 21 CFR 314.80(c)(1). For signals warranting labeling changes, submit a CBE-0 supplement (safety labeling changes that can be implemented without prior FDA approval per 21 CFR 314.70(c)(6)(iii)).

**MHRA (UK):** Post-Brexit independent signal notification per MHRA GVP signal management guidance. Submit validated signal notifications within 15 days to MHRA PV team.

**Coordination:** QPPV (3-qppv) must be informed of all validated signals before external notification. Document the regulatory notification decision (notify / do not notify with rationale) for every validated signal.

### f. Signal Committee Preparation & Presentation
Prepare the monthly Safety Management Team (SMT) meeting package including: (1) signal pipeline dashboard showing all active signals with status and priority, (2) new signals detected since last meeting with preliminary assessment, (3) signals requiring SMT decision (validation outcome, proposed action), (4) closed signals with final disposition rationale, (5) detection method performance metrics (false positive rate, detection-to-decision cycle time). The SMT comprises: Head of Patient Safety (chair), QPPV, Director Signal Management, Director Risk Management, Medical Advisor (oncology), Regulatory Affairs representative, and Biostatistician. Quorum requires QPPV + 3 members. All decisions documented in minutes with action items, owners, and due dates.

### g. Label Impact Assessment
For each validated signal, perform a structured label impact assessment within 15 business days. Determine whether the signal warrants: (1) new addition to the product label (SmPC Section 4.4/4.8 or USPI Sections 5/6), (2) modification of existing labeling language (frequency upgrade, severity reclassification), (3) new contraindication or warning, (4) dose modification recommendation, (5) Risk Management Plan update (new important identified risk, removal of important potential risk), or (6) no label change with documented justification. Cross-reference the Company Core Safety Information (CCSI) and Company Core Data Sheet (CCDS) to ensure global consistency. Coordinate with Regulatory Affairs for variation/supplement submission timeline.

[NEEDS SUB-SKILL] Label impact assessment methodology and CCSI/CCDS cross-referencing.

### h. Signal Tracking & Closure
Maintain the signal tracking system (currently: dashboard Section 6 + API endpoint /api/v1/psd/signals) with lifecycle dates for each signal: detection date, validation date, evaluation completion date, SMT decision date, regulatory notification date (if applicable), label update effective date (if applicable), and closure date.

**Signal closure criteria (must document ALL of the following):**
1. Clinical evaluation is complete with documented conclusion (validated or refuted)
2. SMT has reviewed and approved the closure recommendation
3. If validated: all recommended actions (label update, DHPC, RMP amendment) have been implemented or are tracked with confirmed timelines
4. If refuted: documented rationale with clinical evidence supporting refutation, reviewed by at least one independent clinical expert
5. QPPV (3-qppv) has signed off on the closure
6. Signal closure is recorded in the next PBRER/PSUR (Section 16.3) and DSUR (Section 10)

**Re-opening criteria:** A closed signal must be re-opened if: new cases materially change the evidence base (>50% increase in case count), new mechanistic evidence emerges, or regulatory authority requests re-evaluation.

### i. Clinical Trial Signal Detection (DSMB Interaction)
For ongoing PROSPER trials, maintain a parallel clinical trial signal detection process integrated with but independent from post-marketing signal detection.

**Routine monitoring:** Biweekly blinded SAE/AESI frequency tables by treatment arm (aggregate, not by-patient). Monthly time-to-onset analysis. Cumulative incidence curves for pre-specified AESIs (ILD, hepatotoxicity, cardiac events, QTc prolongation, severe cutaneous reactions).

**DSMB interaction:** Provide unblinded safety data packages to the DSMB per charter schedule (typically every 6 months or after pre-specified event count thresholds). Ensure the signal detection lead has no access to unblinded data unless specifically authorized by the DSMB charter for safety signal evaluation purposes.

**Unblinding rules:** Emergency unblinding for individual patient safety is handled by PV Operations (5-pv-ops) per SOP. Signal-level unblinding (aggregate treatment arm data) requires DSMB authorization or Sponsor safety committee decision per ICH E9(R1). Document the unblinding rationale, date, and scope. Once unblinded at the signal level, the study integrity assessment must be updated.

**Escalation from trial signals:** Any clinical trial signal meeting the impact-likelihood HIGH threshold (sub-process d) triggers: (1) ad-hoc DSMB meeting request within 5 business days, (2) QPPV notification within 24 hours, (3) assessment of SUSAR reporting obligations under 21 CFR 312.32 / EU CT Regulation 536/2014, and (4) Investigator notification per ICH E6(R3) if the finding affects the benefit-risk of continued participation.

---

## Key Thresholds & Decision Criteria Summary

| Decision Point | Threshold / Criterion | Timeline | Authority |
|---|---|---|---|
| Statistical signal flag | PRR >= 2, chi2 >= 4, N >= 3 (or EB05 >= 2, or IC025 > 0) | At each detection run | Signal Detection Lead |
| Signal validation decision | Clinical plausibility + temporal + dose-response assessment | 15 business days from flag | Director, Signal Management & Safety Science |
| Signal Assessment Report | CIOMS VIII full clinical evaluation | 30 calendar days from validation | Director, Signal Management & Safety Science |
| QPPV urgent notification | Fatal/life-threatening new signal | 24 hours | Director, Signal Management & Safety Science |
| PRAC notification | Validated signal, new causal association | 30 calendar days standalone; 3 months important risk variation; 3 working days emerging safety issue (GVP IX.III) | QPPV (sign-off, see 3-qppv Sub-process 5) |
| FDA safety reporting | Significant new safety information | 15-day Alert Report or periodic | Director, Signal Management & Safety Science |
| SMT decision | Review all active signals | Monthly (or ad-hoc for HIGH) | SMT (quorum required) |
| Label update submission | SMT decision to update label | CBE-0 (US) / Type II variation (EU) within 30 days of decision | Regulatory Affairs |
| Signal closure | All criteria met (see sub-process h) | QPPV sign-off required | SMT + QPPV |

## Signal Source Stratification
Every signal must be tagged with its source category for tracking and reporting:
- **Spontaneous (post-marketing):** FAERS, EudraVigilance, national databases
- **Clinical trial:** Ongoing PROSPER program, investigator-sponsored studies
- **Literature:** Published case reports, case series, epidemiological studies
- **Regulatory intelligence:** PRAC recommendations, FDA safety communications, MHRA alerts
- **Other structured data:** Registries, electronic health records (future), social media monitoring (per GVP Module IX.I.3.1)

## Cross-Functional Dependencies
- **Associate Director, PV Operations (5-pv-ops):** Provides coded ICSR data for detection runs; handles individual case follow-up
- **Director, Risk Management & Epidemiology (6-risk-mgmt):** Receives validated signals for RMP/REMS impact assessment; updates important identified/potential risk lists
- **Associate Director, Aggregate Reporting (7-aggregate-reporting):** Signals feed PBRER Section 16.3 (signals evaluated during reporting interval) and DSUR Section 10
- **Regulatory Affairs:** Label change submissions triggered by validated signals; variation/supplement filing
- **Clinical Development:** Trial protocol amendments if signal affects benefit-risk; DSMB communication
- **Medical Affairs:** KOL communication, medical information updates, investigator notifications
- **Legal:** Litigation hold assessment for validated signals with serious outcomes

## Key Metrics (KPIs)
| KPI | Target | Current |
|---|---|---|
| Signal detection review cycle compliance | 100% on-time | 100% |
| Signal evaluation timeliness (detection to SAR) | <= 60 days | 52 days avg |
| Open validated signals | <= 5 at any time | 3 |
| Signal closure rate (within 90 days of validation) | >= 80% | 75% |
| EVDAS eRMR review compliance (within 30 days) | 100% | 100% |
| False positive rate | Track quarterly | -- |

## Escalation
- **Reports to:** Head of Patient Safety / QPPV (2-head-ps, 3-qppv)
- **Escalate if:** New unexpected fatal/life-threatening signal, class-effect signal affecting multiple EGFR inhibitors, any signal requiring urgent safety restriction (Art 20 referral), DSMB recommendation to pause/stop a trial, regulatory authority request for signal evaluation

## Dashboard Integration
- **Section 6** of the Patient Safety Dashboard displays the signal management pipeline, active signals table, detection methods, literature surveillance status, and EVDAS review status
- **API endpoint:** `/api/v1/psd/signals` returns signal items with disproportionality metrics, pipeline summary, recent assessments, and detection methods
- **Signal KPIs** displayed in Section 13 (KPIs & Compliance Scoreboard)

---

## References

- references/gvp_module_summaries.md -- GVP Module IX (Signal Management)
- references/ich_fda_summaries.md -- ICH E2E, E2C(R2), E2F; CIOMS VIII; 21 CFR 314.80/314.81
- references/literature_review.md -- Literature surveillance methodology
