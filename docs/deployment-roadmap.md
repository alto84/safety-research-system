# PSP Deployment Roadmap

**Document Classification:** AstraZeneca Confidential - Internal Use Only
**Version:** 1.0 | **Date:** 2026-02-06
**Owner:** Data Science & AI / Clinical Operations / Safety Sciences

---

## Overview

PSP deployment follows a three-stage gated approach. Each stage has defined entry criteria, deliverables, success metrics, and gate reviews before proceeding.

```
STAGE 1 (Year 1)          STAGE 2 (Year 2)          STAGE 3 (Year 3+)
Foundation & Validation    Pilot Deployment          Enterprise Scale
$8M                        $7M                       $5M
-----------------------    ---------------------     ----------------------
Build platform             Deploy advisory mode      Cross-TA expansion
Retrospective validation   Prospective validation    Regulatory submissions
3 study integrations       DURGA + SLE-LN pilots     Enterprise deployment
DURGA integration path     Clinician feedback loop   Continuous learning
FDA pre-submission         EMA qualification          SaMD clearance
```

---

## Stage 1: Foundation and Validation (Year 1)

### Objective

Build the core platform, validate predictive performance retrospectively, and establish the pathway for integration into AZ clinical systems.

### Budget: $8M

| Category | Allocation | Details |
|----------|-----------|---------|
| Engineering (platform build) | $3.5M | Data pipelines, feature store, model serving, dashboard |
| Data science (model development) | $2.0M | Model training, evaluation framework, interpretability |
| Clinical/science (validation) | $1.0M | Retrospective study execution, expert adjudication |
| Infrastructure (cloud, security) | $1.0M | AWS environment, security hardening, compliance tooling |
| Regulatory/quality | $0.5M | GAMP validation, 21 CFR Part 11, FDA pre-submission |

### Q1 (Months 1-3): Infrastructure and Data

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| Cloud environment provisioned (AWS, AZ-managed) | Engineering | InfoSec approval |
| Data governance framework approved | Data Steward / DPO | Legal, Ethics review |
| Data pipelines for 3 retrospective studies built | Data Engineering | Data access agreements |
| Feature store schema defined and implemented | Data Science / Engineering | Clinical SME input |
| Security controls implemented (encryption, RBAC, audit) | InfoSec / Engineering | 21 CFR Part 11 requirements |
| AI partner endpoints configured (Claude, GPT, Gemini) | Engineering | Procurement, MSAs signed |

### Q2 (Months 4-6): Model Development

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| Baseline features engineered from 3 studies | Data Science | Data pipelines operational |
| Longitudinal feature engineering (cytokine kinetics, labs) | Data Science | Time-series data available |
| CRS prediction model v0.1 trained and evaluated | Data Science | Feature store populated |
| ICANS prediction model v0.1 trained and evaluated | Data Science | Feature store populated |
| Evaluation framework automated | ML Engineering | Metrics defined, data versioned |
| Custom AI eval suite v1.0 deployed | Data Science | Eval items curated by Safety Scientists |
| **FDA pre-submission meeting** | Regulatory Affairs | Briefing document prepared |

### Q3 (Months 7-9): Validation

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| Retrospective validation study 1 complete | Biostatistics / Data Science | Pre-specified analysis plan |
| Retrospective validation study 2 complete | Biostatistics / Data Science | Independent dataset |
| Retrospective validation study 3 complete | Biostatistics / Data Science | Independent dataset |
| External validation (1 academic cohort) initiated | Clinical Partnerships | Data sharing agreement |
| Fairness and bias assessment complete | Data Science / Biostatistics | Subgroup data sufficient |
| Model cards v1.0 authored | Data Science / Safety Sciences | All validation results available |

### Q4 (Months 10-12): Integration Pathway

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| DURGA integration architecture designed | Engineering / DURGA team | DURGA API specifications |
| DURGA integration proof-of-concept (sandbox) | Engineering | DURGA sandbox access |
| Risk dashboard prototype (clinician-facing) | UX / Engineering | Clinician design feedback |
| GAMP validation documentation complete | Quality Assurance | All testing complete |
| PCCP draft submitted to FDA | Regulatory Affairs | FDA pre-sub feedback |
| **Stage 1 Gate Review** | Steering Committee | All deliverables assessed |

### Stage 1 Gate Criteria

| Criterion | Requirement | Status |
|-----------|-------------|--------|
| AUROC (Grade >= 3 CRS, 24h pre-onset) | >= 0.80 on at least 2/3 studies | |
| Calibration | ECE <= 0.07 | |
| Fairness | No subgroup AUROC < 0.70 | |
| DURGA integration PoC | Functional in sandbox | |
| FDA pre-submission | Meeting completed, feedback documented | |
| GAMP validation | IQ/OQ complete | |
| Budget | Within 10% of allocation | |

---

## Stage 2: Pilot Deployment (Year 2)

### Objective

Deploy PSP in advisory mode within active clinical trials. Collect prospective validation data and clinician feedback. Refine models based on real-world performance.

### Budget: $7M

| Category | Allocation | Details |
|----------|-----------|---------|
| Engineering (DURGA integration, scale) | $2.5M | Production integration, monitoring, alerting |
| Data science (model refinement) | $1.5M | Prospective recalibration, new features, model updates |
| Clinical operations (deployment support) | $1.5M | Site training, workflow integration, feedback collection |
| Regulatory/quality | $1.0M | Prospective validation study, EMA qualification, PQ |
| Infrastructure (production ops) | $0.5M | Production environment, SLA management |

### Q1 (Months 13-15): Deployment Preparation

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| DURGA production integration complete | Engineering / DURGA team | DURGA release cycle alignment |
| PSP deployed in shadow mode (DURGA program) | Engineering / Clinical Ops | IRB/ethics approval for shadow deployment |
| PSP deployed in shadow mode (SLE-LN CAR-T study) | Engineering / Clinical Ops | Study team agreement |
| Site training materials developed | Clinical Ops / Medical Affairs | Clinician feedback on prototype |
| Production monitoring dashboards operational | ML Engineering / SRE | Monitoring infrastructure |
| **EMA qualification advice request submitted** | Regulatory Affairs | EMA briefing document |

### Q2 (Months 16-18): Shadow Mode and Prospective Data Collection

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| Shadow mode predictions logged for >= 50 patients | Data Science / Clinical Ops | Enrollment pace |
| Real-time data pipeline performance validated | Engineering | Production SLAs met |
| Clinician interface usability testing (10+ investigators) | UX / Clinical Ops | Site access |
| Model monitoring framework operational | ML Engineering | Drift detection calibrated |
| AI eval suite v2.0 (incorporating prospective findings) | Data Science | New clinical cases available |

### Q3 (Months 19-21): Prospective Validation Unblinding

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| Prospective validation analysis (DURGA) | Biostatistics | Pre-specified event threshold met |
| Prospective validation analysis (SLE-LN) | Biostatistics | Pre-specified event threshold met |
| Model recalibration based on prospective data | Data Science | Validation results reviewed |
| Clinician feedback analysis and model refinement | Data Science / UX | Feedback collected |
| Advisory mode deployment plan approved | Steering Committee / IRB | Prospective validation meets criteria |

### Q4 (Months 22-24): Advisory Mode Activation

| Deliverable | Owner | Dependencies |
|-------------|-------|-------------|
| PSP transitions to advisory mode (DURGA) | Clinical Ops / Engineering | IRB approval, site training |
| PSP transitions to advisory mode (SLE-LN) | Clinical Ops / Engineering | IRB approval, site training |
| Clinician override tracking operational | Engineering / Safety Sciences | Feedback loop architecture |
| Clinical utility assessment initiated | Biostatistics / Safety Sciences | Advisory mode generating data |
| EMA qualification feedback received | Regulatory Affairs | EMA timeline |
| **Stage 2 Gate Review** | Steering Committee | All deliverables assessed |

### Stage 2 Gate Criteria

| Criterion | Requirement | Status |
|-----------|-------------|--------|
| Prospective AUROC (Grade >= 3 CRS) | >= 0.78 | |
| Lead time (median) | >= 12 hours | |
| False positive rate at deployed threshold | <= 25% | |
| No critical safety failures | Zero missed Grade >= 4 with high-confidence low-risk prediction | |
| Clinician satisfaction (survey) | >= 70% find alerts useful | |
| System reliability | >= 99.5% uptime during pilot | |
| Budget | Within 10% of allocation | |

---

## Stage 3: Enterprise Scale (Year 3+)

### Objective

Expand PSP across therapeutic areas and molecule classes. Submit for regulatory clearance. Establish as enterprise safety AI infrastructure.

### Budget: $5M

| Category | Allocation | Details |
|----------|-----------|---------|
| Engineering (cross-TA scale) | $1.5M | Multi-TA feature store, platform hardening |
| Data science (new indications) | $1.5M | TCE models, checkpoint inhibitor models |
| Regulatory submissions | $1.0M | SaMD submission, BLA safety packages |
| Clinical operations (enterprise rollout) | $0.5M | Training, change management |
| Infrastructure | $0.5M | Enterprise-grade operations |

### Stage 3a (Months 25-30): Cross-TA Expansion

| Deliverable | Owner | Timeline |
|-------------|-------|----------|
| TCE (T-cell engager) CRS/ICANS model developed | Data Science | Month 25-28 |
| TCE model retrospective validation | Biostatistics | Month 28-30 |
| Checkpoint inhibitor irAE prediction model (exploratory) | Data Science | Month 27-30 |
| Cross-TA feature ontology standardized | Data Science / Safety Sciences | Month 25-27 |
| Transfer learning framework validated | Data Science | Month 26-29 |

### Stage 3b (Months 31-36): Regulatory and Enterprise

| Deliverable | Owner | Timeline |
|-------------|-------|----------|
| SaMD regulatory submission (De Novo or 510(k)) | Regulatory Affairs | Month 31-33 |
| PSP safety data included in first BLA submission | Regulatory / Safety Sciences | Month 33-36 |
| Enterprise deployment to all CGT and TCE programs | Engineering / Clinical Ops | Month 31-36 |
| Continuous learning pipeline operational (per PCCP) | ML Engineering | Month 34-36 |
| Partnership with 2+ academic medical centers for external validation | Clinical Partnerships | Month 31-36 |
| PSP operating model transitioned to steady-state | Program Management | Month 36 |

### Stage 3 Success Criteria

| Criterion | Target |
|-----------|--------|
| Programs using PSP | >= 5 active clinical programs |
| Therapeutic areas | >= 2 (Cell Therapy + TCE minimum) |
| Regulatory submissions incorporating PSP data | >= 1 |
| SaMD clearance | Application submitted |
| Operational cost per program | Decreasing year-over-year (platform economics) |
| Clinical holds in PSP-monitored programs | Measurable reduction vs. historical baseline |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Insufficient training data (rare high-grade events) | Medium | High | Multi-study pooling, synthetic data augmentation, external data partnerships |
| DURGA integration delays | Medium | Medium | Early engagement with DURGA team, fallback standalone deployment |
| Regulatory uncertainty (evolving AI/ML guidance) | Medium | High | Proactive FDA/EMA engagement, flexible PCCP design |
| Clinician adoption resistance | Medium | Medium | Co-design with investigators, demonstrate clinical utility early |
| AI model provider disruption (pricing, availability) | Low | Medium | Multi-model architecture, no single-provider dependency |
| Data quality in real-time clinical settings | High | Medium | Robust validation pipeline, graceful degradation, missing data handling |
| Privacy/security incident | Low | High | Defense-in-depth, encryption, access controls, incident response plan |

---

## Governance Cadence

| Meeting | Frequency | Attendees | Purpose |
|---------|-----------|-----------|---------|
| Steering Committee | Quarterly | SVPs, VPs, Program Lead | Stage gate decisions, strategic direction |
| Operating Committee | Monthly | Working-level leads from each function | Execution tracking, issue resolution |
| Technical Review | Bi-weekly | Data Science, Engineering, Biostatistics | Model performance, architecture decisions |
| Clinical Advisory | Monthly | Safety Scientists, Medical Monitors, Investigators | Clinical relevance, workflow integration |
| Regulatory Sync | Monthly | Regulatory Affairs, Quality, Legal | Compliance, submission planning |
