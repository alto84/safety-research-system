# Predictive Safety Platform Regulatory Compliance Framework

**Version:** 1.0 | **Date:** 2026-02-06
**Owner:** Regulatory Affairs / Quality Assurance / Safety Research Team

---

## 1. Regulatory Landscape

The platform operates at the intersection of pharmaceutical safety and AI/ML-based software. The following regulatory frameworks apply:

| Framework | Jurisdiction | Applicability |
|-----------|-------------|---------------|
| FDA AI/ML-Based SaMD Action Plan | US | AI model lifecycle, predetermined change control |
| EU AI Act (High-Risk Classification) | EU | Risk classification, transparency, human oversight |
| 21 CFR Part 11 | US | Electronic records, electronic signatures, audit trails |
| EU Annex 11 | EU | Computerized systems in GxP environments |
| GAMP 5 (2nd Edition) | Global | Risk-based validation of computerized systems |
| ICH E6(R3) | Global | GCP requirements for computerized systems in trials |
| ICH E2B(R3) | Global | Individual case safety report standards |
| FDA CBER Guidance on CGT | US | Cell therapy-specific safety monitoring requirements |

---

## 2. FDA AI/ML SaMD Framework Compliance

### 2.1 Product Classification

The platform functions as a **Clinical Decision Support (CDS) tool in advisory mode**. Under current FDA guidance:

- The platform does **not** autonomously make treatment decisions. All outputs are recommendations presented to qualified clinicians.
- Classification target: **Class II SaMD** (provides information to inform clinical management; condition is serious).
- Regulatory pathway: **De Novo** or **510(k)** depending on predicate availability at time of submission.

### 2.2 Good Machine Learning Practice (GMLP)

The platform adheres to the FDA/Health Canada/MHRA joint principles for GMLP:

| Principle | Platform Implementation |
|-----------|--------------------|
| Multi-disciplinary expertise | Joint team: Safety Scientists, Clinicians, Data Scientists, Regulatory, QA |
| Good software engineering | CI/CD with automated testing, code review, version control |
| Representative data | Clinical validation across demographics, disease subtypes, geographies |
| Independent training/test sets | Temporal split (no data leakage), external validation cohorts |
| Reference standards | Adjudicated AE grading (ASTCT consensus criteria) as ground truth |
| Model transparency | Interpretability layer with feature attributions, mechanistic mappings |
| Focus on deployed performance | Prospective monitoring, real-world performance tracking |
| Security and resilience | Adversarial testing, input validation, graceful degradation |
| Human-AI teaming | Advisory-mode design, clinician override capability |
| Monitoring and re-training | Continuous drift detection, controlled update process |

### 2.3 Predetermined Change Control Plan (PCCP)

The PCCP defines the boundaries within which platform models can be updated without requiring a new regulatory submission.

**Permitted changes (within PCCP scope):**
- Model re-training on new data from the same study populations and data types.
- Feature weight updates within pre-specified bounds (no new feature categories).
- Threshold recalibration within clinically validated ranges.
- Performance improvements where all validation metrics remain above pre-specified minima.

**Changes requiring new submission:**
- Addition of new data modalities (e.g., adding imaging features to a lab-only model).
- Extension to new therapeutic areas or molecule classes.
- Changes to the intended use or target population.
- Architectural changes (e.g., switching from ensemble to foundation model).
- Any change that degrades performance on any validated subgroup below pre-specified thresholds.

**PCCP documentation requirements:**
- Description of modification types and their boundaries
- Validation protocol for each change type
- Performance monitoring plan with statistical process control limits
- Rollback procedures and criteria
- Notification procedures to regulatory authorities

---

## 3. GAMP 5 Validation

### 3.1 System Classification

Under GAMP 5 (2nd Edition), platform components are classified as:

| Component | GAMP Category | Validation Approach |
|-----------|--------------|-------------------|
| Data ingestion pipelines | Category 4 (configured) | Configuration verification, data integrity testing |
| Feature engineering code | Category 5 (custom) | Full lifecycle validation (requirements, design, code review, testing) |
| ML model training framework | Category 5 (custom) | Algorithm verification, training reproducibility |
| Trained ML models | Category 5 (custom) | Performance validation, clinical validation |
| Risk dashboard (UI) | Category 4 (configured) | Configuration verification, UAT |
| Cloud infrastructure (AWS) | Category 1 (infrastructure) | Qualification of managed services |

### 3.2 Validation Lifecycle

```
User Requirements Specification (URS)
    |
    v
Functional Requirements Specification (FRS)
    |
    v
Design Specification (DS)
    |       \
    v        v
Code Development    Configuration
    |               |
    v               v
Unit Testing (IQ)   Config Verification
    |               |
    v               v
Integration Testing (OQ)
    |
    v
Performance Qualification (PQ) / Clinical Validation
    |
    v
Validation Summary Report
    |
    v
Periodic Review (annual + triggered)
```

### 3.3 Risk-Based Testing

Following ICH Q9 risk management principles:

| Risk Level | Test Coverage | Examples |
|-----------|--------------|---------|
| High | Exhaustive testing, independent verification | AE grade prediction, alert triggering logic |
| Medium | Representative testing, automated regression | Feature calculations, data transformations |
| Low | Verification of configuration | UI layout, report formatting |

---

## 4. 21 CFR Part 11 Compliance

### 4.1 Electronic Records

| Requirement | Implementation |
|------------|----------------|
| Audit trail | Immutable, timestamped log of all data changes, model predictions, and user actions. Stored in append-only audit database. |
| Record retention | All records retained for protocol duration + 15 years minimum. Archived in validated long-term storage. |
| Record integrity | SHA-256 checksums on all stored records. Integrity verification on retrieval. |
| Record availability | Records retrievable in human-readable format throughout retention period. |
| Copy controls | Export restricted by role. Watermarking on exported reports. |

### 4.2 Electronic Signatures

| Requirement | Implementation |
|------------|----------------|
| Signature binding | Electronic signatures cryptographically bound to their respective records. |
| Signature components | Enterprise SSO (SAML 2.0) + MFA for all GxP actions. |
| Signature meaning | Each signature records: identity, date/time, meaning (authorship, review, approval). |
| Non-repudiation | Digital certificates managed by organizational PKI infrastructure. |

### 4.3 System Controls

| Requirement | Implementation |
|------------|----------------|
| Access control | RBAC with quarterly access reviews. Privileged access requires approval workflow. |
| Authority checks | System enforces role-based permissions for all functions (view, edit, approve, configure). |
| Device checks | Device trust verification via endpoint management (Intune). |
| Session controls | Automatic timeout after 15 minutes of inactivity. Concurrent session limits. |
| Operational checks | Sequential step enforcement for critical workflows (e.g., model validation before deployment). |

---

## 5. Human-in-the-Loop Requirements

### 5.1 Design Principles

The platform is architected as an **advisory system**, not an autonomous decision-maker. This is a fundamental design constraint, not an optional feature.

**Mandatory human decision points:**

| Decision | Human Role | Platform Role |
|----------|-----------|----------|
| Patient risk classification | Medical Monitor / Investigator decides | Provides risk score, confidence interval, contributing factors |
| Preemptive intervention (e.g., tocilizumab, steroids) | Treating physician decides | Provides risk trajectory and time-to-event estimate |
| Dose modification or treatment hold | Investigator / Sponsor Medical decides | Provides risk-benefit analysis inputs |
| Safety signal escalation | Safety Scientist decides | Identifies potential signals, ranks by evidence strength |
| Regulatory notification | Regulatory Affairs decides | Drafts signal summary, provides supporting evidence |

### 5.2 Alert Design

- **No autonomous actions.** The platform never triggers treatment changes, protocol amendments, or regulatory submissions without human authorization.
- **Graded alerting:** Risk scores mapped to alert tiers (Watch / Advisory / Urgent) with role-appropriate routing.
- **Dismissal documentation:** Clinician must document rationale when overriding or dismissing a high-confidence alert. Dismissal patterns monitored for systematic issues.
- **Feedback loop:** Clinician decisions (follow / override) feed back into model performance monitoring.

### 5.3 Clinician Override

- Override is always available and never penalized.
- Override rationale captured in structured format (drop-down categories + free text).
- Override patterns analyzed quarterly for model improvement opportunities and to detect systematic disagreement patterns.

---

## 6. Model Documentation Standards

### 6.1 Model Card (Per Deployed Model)

Every deployed platform model must have a model card containing:

1. **Model details:** Name, version, architecture, training date, training data description.
2. **Intended use:** Target population, clinical context, decision support function.
3. **Performance metrics:** Discrimination (AUROC, AUPRC), calibration (Brier score), timing accuracy, clinical utility (NRI), per validated subgroup.
4. **Limitations:** Known failure modes, populations with limited validation, data dependencies.
5. **Ethical considerations:** Fairness analysis results, bias assessment, demographic performance breakdown.
6. **Training data:** Source studies, inclusion/exclusion criteria, sample sizes, label definitions, class balance.
7. **Validation history:** Retrospective studies, prospective validation results, external validation results.
8. **Update history:** Version changelog, PCCP compliance status, re-validation results.

### 6.2 Algorithm Description Document

Technical document for regulatory submission containing:
- Mathematical formulation of the algorithm
- Feature definitions with clinical rationale
- Training procedure (optimization, regularization, hyperparameter selection)
- Handling of missing data, class imbalance, temporal irregularity
- Ensemble/routing logic (if multi-model)
- Interpretability method description and validation

### 6.3 Clinical Validation Report

- Study protocol (prospective or retrospective with pre-specified analysis plan)
- Patient disposition and demographics
- Primary and secondary endpoint results with confidence intervals
- Subgroup analyses (age, sex, race/ethnicity, disease subtype, geography)
- Comparison to standard-of-care risk assessment
- Clinical utility analysis (decision curve analysis, NRI)
- Failure analysis (false negatives examined individually)

---

## 7. Regulatory Engagement Plan

| Milestone | Regulatory Activity | Timeline |
|-----------|-------------------|----------|
| Stage 1 Q2 | Pre-submission meeting with FDA CBER (AI in CGT safety) | Year 1 Month 6 |
| Stage 1 Q4 | PCCP draft shared with FDA for feedback | Year 1 Month 12 |
| Stage 2 Q1 | EMA qualification advice request (novel methodology) | Year 2 Month 3 |
| Stage 2 Q3 | Clinical validation protocol agreed with FDA | Year 2 Month 9 |
| Stage 3 Q2 | De Novo / 510(k) submission (if standalone SaMD) | Year 3 Month 6 |
| Stage 3 Q4 | Inclusion in BLA safety package (first program) | Year 3 Month 12 |
| Ongoing | Annual PCCP compliance reports | Annually |
