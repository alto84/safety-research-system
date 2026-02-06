# PSP Evaluation Framework

**Document Classification:** AstraZeneca Confidential - Internal Use Only
**Version:** 1.0 | **Date:** 2026-02-06
**Owner:** Data Science & AI / Biostatistics / Safety Sciences

---

## 1. Evaluation Philosophy

PSP models are safety-critical. Evaluation must be rigorous, multi-dimensional, and continuous. A model that discriminates well but is poorly calibrated, or one that is accurate on average but biased against a subgroup, is unacceptable for clinical deployment.

**Evaluation dimensions:**
1. Discrimination --- Can the model separate high-risk from low-risk patients?
2. Calibration --- Are predicted probabilities accurate?
3. Timing --- Can the model predict when events will occur?
4. Mechanistic validity --- Are predictions grounded in biological plausibility?
5. Clinical utility --- Does the model improve clinical decisions?
6. Fairness --- Is performance equitable across patient subgroups?

---

## 2. Primary Metrics

### 2.1 Discrimination

| Metric | Target (Stage 1) | Target (Stage 3) | Notes |
|--------|------------------|-------------------|-------|
| AUROC (Grade >= 2 CRS) | >= 0.78 | >= 0.85 | Primary discrimination metric |
| AUROC (Grade >= 3 CRS) | >= 0.80 | >= 0.88 | High-grade events are the critical target |
| AUROC (Any-grade ICANS) | >= 0.75 | >= 0.82 | Lower baseline due to less understood pathophysiology |
| AUPRC (Grade >= 3 CRS) | >= 0.40 | >= 0.55 | Accounts for class imbalance (Grade >= 3 CRS ~10-15% incidence) |
| Sensitivity at 90% specificity | >= 0.60 | >= 0.75 | Clinically relevant operating point |
| Sensitivity at 95% NPV | Report | Report | Safety-focused operating point (minimize missed high-grade events) |

**Confidence intervals:** All metrics reported with 95% CIs via bootstrapping (2000 iterations). Comparisons between models use DeLong's test (AUROC) or permutation tests.

### 2.2 Calibration

| Metric | Target | Notes |
|--------|--------|-------|
| Brier score | <= 0.15 | Lower is better. Composite of discrimination and calibration. |
| Expected Calibration Error (ECE) | <= 0.05 | Across 10 probability deciles |
| Hosmer-Lemeshow p-value | > 0.05 | No significant miscalibration |
| Calibration slope | 0.8 - 1.2 | Slope of observed vs. predicted probability regression |
| Calibration-in-the-large | Report | Mean predicted vs. observed event rate |

**Calibration plots:** Generated for every model version, overall and per subgroup. Visual inspection by Biostatistics required before deployment.

### 2.3 Timing Accuracy

| Metric | Target | Notes |
|--------|--------|-------|
| Median absolute error (time-to-event) | <= 12 hours | For CRS onset prediction |
| Time-dependent AUROC at 24h pre-onset | >= 0.80 | Can we identify risk 24 hours before clinical manifestation? |
| Time-dependent AUROC at 48h pre-onset | >= 0.75 | Earlier warning, lower expected performance |
| Concordance index (time-to-event) | >= 0.70 | Survival analysis metric for event timing ranking |
| Lead time (median) | >= 18 hours | Median advance warning before clinical onset |

---

## 3. Secondary Metrics

### 3.1 Mechanistic Validity

| Assessment | Method | Acceptance Criteria |
|-----------|--------|-------------------|
| Pathway alignment | Compare top SHAP features to known CRS/ICANS pathways | >= 70% of top-10 features map to established pathways |
| Biological plausibility | Expert review of feature attribution direction | Feature effects consistent with known biology (e.g., higher IL-6 = higher CRS risk) |
| Novel signal review | Features not mapping to known pathways reviewed for biological hypothesis | Novel signals documented and flagged for validation, not rejected outright |
| Causal consistency | Interventional analysis (does tocilizumab administration reduce predicted risk?) | Model predictions respond appropriately to known interventions |

### 3.2 Clinical Utility

| Metric | Method | Target |
|--------|--------|--------|
| Net Reclassification Improvement (NRI) | Compared to standard clinical risk factors alone | NRI > 0 (statistically significant) |
| Decision Curve Analysis | Net benefit across threshold probabilities | Net benefit > treat-all and treat-none strategies across clinically relevant thresholds (5-30%) |
| Number Needed to Screen (NNS) | Patients flagged per true high-grade event identified | NNS <= 5 for Grade >= 3 CRS |
| Alert actionability | Proportion of alerts where clinician took a preemptive action | >= 40% (Stage 2 prospective) |
| Time to intervention | Comparison of intervention timing with vs. without PSP alerts | Measurable reduction (target: >= 6 hours earlier) |

### 3.3 Fairness and Bias Assessment

**Protected attributes assessed:**
- Age (< 65 vs. >= 65)
- Sex (male vs. female)
- Race/ethnicity (as recorded per ICH E5 and regional requirements)
- Geographic region (US vs. EU vs. Asia-Pacific)
- Disease subtype (e.g., DLBCL vs. ALL vs. multiple myeloma)
- Prior treatment lines (1-2 vs. 3+)

**Fairness metrics:**

| Metric | Requirement |
|--------|-------------|
| Equalized AUROC | AUROC difference between any two subgroups <= 0.05 |
| Equalized calibration | ECE difference between subgroups <= 0.03 |
| Equalized false negative rate | FNR difference between subgroups <= 0.05 at the deployed threshold |
| Proportional representation | No subgroup underrepresented by > 50% relative to trial population |
| Disparity report | Full demographic performance breakdown in every validation report |

**Mitigation strategies for detected bias:**
- Subgroup-specific calibration (post-hoc recalibration per subgroup)
- Oversampling or re-weighting of underrepresented subgroups in training
- Subgroup-aware threshold selection
- Algorithmic fairness constraints (equalized odds, calibration within groups)
- If bias cannot be mitigated below thresholds: explicit labeling of limited validity for affected subgroup

---

## 4. Validation Protocols

### 4.1 Retrospective Validation (Stage 1)

**Design:** Multi-study retrospective cohort analysis using completed AZ CGT trials with adjudicated safety data.

**Protocol:**
1. **Study selection:** Minimum 3 completed CGT studies with individual patient-level data, >= 200 patients total, >= 30 Grade >= 3 CRS events.
2. **Temporal split:** Training on earlier studies/enrollment periods; validation on later studies/enrollment periods. No random splitting across time.
3. **Pre-specified analysis plan:** Registered internally before data lock. Primary endpoints, subgroup analyses, and success criteria defined a priori.
4. **Adjudicated labels:** AE grading adjudicated by independent clinical review (ASTCT consensus criteria for CRS, ICANS).
5. **External validation:** At minimum one validation cohort from a different institution or trial (data sharing agreement with academic partner or CIBMTR).

**Success criteria for Stage 1 gate:**
- Primary endpoint (AUROC for Grade >= 3 CRS at 24h pre-onset) >= 0.80
- No subgroup with AUROC < 0.70
- Calibration slope between 0.7 and 1.3
- At least 2 of 3 studies individually meeting AUROC >= 0.75

### 4.2 Prospective Validation (Stage 2)

**Design:** Embedded prospective validation within active clinical trials, advisory mode only (no impact on treatment decisions during validation phase).

**Protocol:**
1. **Study integration:** PSP deployed in shadow mode in DURGA program and SLE-LN CAR-T study.
2. **Data collection:** Real-time predictions generated and stored but not displayed to clinicians during blinded validation phase.
3. **Unblinding:** After pre-specified number of events (n >= 20 Grade >= 3 events per study), predictions unblinded and compared to actual outcomes.
4. **Transition to advisory mode:** If prospective validation meets pre-specified criteria, PSP transitions to clinician-visible advisory mode with IRB/ethics approval.

**Success criteria for Stage 2 gate:**
- Prospective AUROC for Grade >= 3 CRS >= 0.78 (accounting for real-world data quality)
- Lead time >= 12 hours for >= 70% of correctly identified events
- False positive rate <= 25% at the deployed operating threshold
- No critical safety failures (missed Grade >= 4 event where model predicted low risk with high confidence)

### 4.3 External Validation

- Minimum one external validation per therapeutic indication before regulatory submission.
- External data sources: academic medical center collaborations, CIBMTR registry, published individual patient data (IPD) meta-analyses.
- External validation performance expected to be 3-5% lower AUROC than internal validation (documented and justified).

---

## 5. Continuous Monitoring

### 5.1 Performance Monitoring (Post-Deployment)

| Monitor | Method | Frequency | Alert Threshold |
|---------|--------|-----------|----------------|
| Discrimination drift | Rolling AUROC (90-day window) | Weekly | AUROC drops > 0.03 from baseline |
| Calibration drift | Rolling ECE (90-day window) | Weekly | ECE exceeds 0.08 |
| Input feature drift | KL divergence / PSI per feature | Daily | PSI > 0.2 for any critical feature |
| Prediction distribution shift | KS test on predicted probability distribution | Weekly | p < 0.01 |
| Missing data rate change | Completeness monitoring per feature | Daily | Completeness drops > 10% from baseline |
| Alert volume anomaly | Statistical process control on alert rate | Daily | Rate outside 3-sigma control limits |
| False negative review | Manual review of all missed high-grade events | Per event | Every Grade >= 3 miss triggers root cause analysis |

### 5.2 Drift Response Protocol

```
Drift detected (automated alert)
    |
    v
Triage by ML Engineer (within 24 hours)
    |
    +--> Minor drift (within control limits): Document, continue monitoring
    |
    +--> Moderate drift (approaching thresholds): Investigate root cause
    |       |
    |       +--> Data quality issue: Fix upstream, retrigger pipeline
    |       +--> Population shift: Assess need for recalibration
    |       +--> Model degradation: Initiate revalidation
    |
    +--> Critical drift (thresholds breached):
            |
            v
        Model quarantine (revert to previous version or disable)
            |
            v
        Root cause analysis (48-hour deadline)
            |
            v
        Corrective action (retraining, recalibration, or architecture change)
            |
            v
        Revalidation per PCCP or new submission
```

### 5.3 Model Retraining Cadence

| Trigger | Expected Frequency | Validation Required |
|---------|-------------------|-------------------|
| Scheduled retraining (new data accumulation) | Quarterly | Abbreviated validation (within PCCP scope) |
| Drift-triggered retraining | As needed | Full revalidation if outside PCCP scope |
| New study population | Per study activation | Population-specific validation |
| Model architecture update | Annually or less | Full validation + regulatory assessment |

---

## 6. Evaluation Infrastructure

### 6.1 Evaluation Pipeline

- Fully automated evaluation pipeline triggered on every model version candidate.
- All metrics computed, logged, and versioned in MLflow (or equivalent experiment tracker).
- Validation reports auto-generated in regulatory-compliant format (PDF with digital signature).
- No model promoted to production without passing automated gate checks AND human review sign-off.

### 6.2 Evaluation Data Management

- Held-out evaluation datasets versioned and immutable (DVC or equivalent).
- Evaluation data never used in training or hyperparameter tuning.
- Evaluation data refreshed semi-annually with new adjudicated cases.
- Old evaluation sets retained for longitudinal performance tracking.

### 6.3 Reproducibility

- Every evaluation run is fully reproducible: model version, data version, code version, environment specification, random seeds --- all logged.
- Reproduction verified quarterly by independent team member.
- Regulatory inspectors can reproduce any reported result from archived artifacts.
