# Pharma Skill Registry — Master Index

## PV Organization Hierarchy (Numbered Skills)

```
1-cmo.md — Chief Medical Officer (Safety Oversight)
├── 2-head-ps.md — Head of Patient Safety / Pharmacovigilance
│   ├── 3-qppv.md — QPPV (EU) — Qualified Person for Pharmacovigilance
│   ├── 4-signal-mgmt.md — Director, Signal Management & Safety Science
│   │   └── [NEEDS SUB-SKILL] Routine Signal Detection Screening
│   │   └── [NEEDS SUB-SKILL] Signal Evaluation (Full Clinical Assessment)
│   │   └── [NEEDS SUB-SKILL] Label Impact Assessment
│   ├── 5-pv-ops.md — Associate Director, PV Operations (ICSR Case Processing)
│   │   └── [NEEDS SUB-SKILL] Case Intake & Triage
│   │   └── [NEEDS SUB-SKILL] Regulatory Submission (E2B(R3))
│   │   └── [NEEDS SUB-SKILL] Literature Surveillance & Case Extraction
│   │   └── [NEEDS SUB-SKILL] MedDRA Coding & Data Entry Quality
│   │   └── [NEEDS SUB-SKILL] Medical Review & Causality Assessment Protocol
│   ├── 6-risk-mgmt.md — Director, Risk Management & Epidemiology
│   │   └── [NEEDS SUB-SKILL] RMP Safety Specification Maintenance
│   │   └── [NEEDS SUB-SKILL] Risk Minimisation Measure Design & Effectiveness
│   ├── 7-aggregate-reporting.md — Associate Director, Aggregate Reporting
│   │   └── [NEEDS SUB-SKILL] PBRER Authoring Cycle
│   │   └── [NEEDS SUB-SKILL] DSUR Authoring Cycle
│   └── 8-pv-quality.md — Manager, PV Quality & Compliance
│       └── [NEEDS SUB-SKILL] CAPA Management
```

## Skill File Details

| # | File | Role | Parent | Children | Cross-refs |
|---|------|------|--------|----------|------------|
| 1 | 1-cmo.md | Chief Medical Officer | Board/CEO | 2 | 3 (QPPV independence) |
| 2 | 2-head-ps.md | Head of Patient Safety / Pharmacovigilance | 1-cmo | 3, 4, 5, 6, 7, 8 | 1 (escalation) |
| 3 | 3-qppv.md | QPPV (EU) | 2-head-ps (solid), 1-cmo (dotted) | -- | 1, 2, 4, 5, 8 |
| 4 | 4-signal-mgmt.md | Director, Signal Management & Safety Science | 2-head-ps | -- | 3, 5, 6, 7, 8 |
| 5 | 5-pv-ops.md | Associate Director, PV Operations | 2-head-ps | -- | 4, 7, 8 |
| 6 | 6-risk-mgmt.md | Director, Risk Management & Epidemiology | 2-head-ps | -- | 4, 5, 7, 8 |
| 7 | 7-aggregate-reporting.md | Associate Director, Aggregate Reporting | 2-head-ps | -- | 3, 4, 5, 6, 8 |
| 8 | 8-pv-quality.md | Manager, PV Quality & Compliance | 2-head-ps | -- | 3, 4, 5, 6, 7 |

## Cross-Functional Skills (outside PV org)

These roles interact with the PV organization but report through separate chains of command.

| File | Role | Primary PV touchpoints |
|------|------|----------------------|
| regulatory-submission.md | VP Regulatory Affairs | Label changes (4), variations (6, 7), submissions (5) |
| quality-gxp-compliance.md | Head of Quality Assurance | QMS alignment (8), inspection support (3, 8) |
| clinical-ops-trial-management.md | VP Clinical Operations | SAE reconciliation (5), trial safety data (4, 7) |
| biostats-analysis-plan.md | Head of Biostatistics | Exposure estimates (7), signal statistics (4) |
| medical-affairs-kol.md | VP Medical Affairs | Safety communications (1, 4), educational materials (6) |
| cmc-manufacturing.md | Head of CMC / Manufacturing | Product quality defects affecting safety (5, 8) |

## References Directory

| File | Content |
|------|---------|
| references/gvp_module_summaries.md | EU GVP Module summaries (I-XVI) |
| references/ich_fda_summaries.md | ICH E2A-E2F, FDA CFR summaries |
| references/literature_review.md | Literature review methodology and sources |
| references/operational_improvement_plan.md | PV operational improvement plan (former head_patient_safety_operational_plan.md) |
