# Expansion Plan: Universal Cell Therapy Safety Platform

> **Date:** 2026-02-08 | **Status:** Active
> **Goal:** Expand from SLE CAR-T to ALL cell therapy types with CDP/CSP support

---

## Phase 1: Deep Research — Cell Therapy Landscape (AGENT TEAM)

### 1.1 Cell Therapy Types to Support
Research and catalog ALL cell therapy modalities:
- **CAR-T** (CD19, BCMA, CD22, dual-target, armored, etc.)
- **TCR-T** (tumor-specific TCR therapies)
- **NK Cell Therapy** (allogeneic, iPSC-derived, CAR-NK)
- **TIL Therapy** (tumor-infiltrating lymphocytes)
- **CAR-M** (CAR-macrophage)
- **Gene Therapy** (in vivo gene editing, ex vivo gene-modified cells)
- **MSC Therapy** (mesenchymal stem cells)
- **Regulatory T-cell (Treg) therapy**
- **Gamma-delta T-cell therapy**

For each: key AEs, incidence rates, risk factors, approved products, pipeline.

### 1.2 Adverse Event Taxonomy
Build comprehensive AE registry across all cell therapies:
- CRS (all grades, onset timing, duration)
- ICANS/neurotoxicity
- ICAHS (hemophagocytic lymphohistiocytosis-like)
- LICATS (liver toxicity)
- Cytopenias (neutropenia, thrombocytopenia, anemia — timing, duration)
- Infections (bacterial, viral, fungal — by time window)
- Cardiac toxicity (arrhythmia, cardiomyopathy, troponin elevation)
- Secondary malignancies (T-cell lymphoma, MDS/AML)
- GvHD (for allogeneic therapies)
- Tumor lysis syndrome
- B-cell aplasia / hypogammaglobulinemia
- On-target off-tumor toxicity
- Insertional mutagenesis (gene therapy)
- Infusion reactions
- Organ-specific toxicities by target antigen

### 1.3 Data Sources per Therapy Type
Map which data sources are relevant for each therapy type.

---

## Phase 2: Architecture Expansion

### 2.1 Treatment Type Registry
```python
@dataclass
class TherapyType:
    id: str                    # "car-t-cd19", "tcr-t", "car-nk", etc.
    name: str
    category: str              # "CAR-T", "TCR-T", "NK", "TIL", "Gene Therapy"
    target_antigens: list[str]
    applicable_aes: list[str]  # Which AEs are relevant
    approved_products: list[str]
    default_priors: dict       # AE -> PriorSpec
    data_sources: list[str]
    risk_factors: list[str]
```

### 2.2 Treatment Selector UI
- Dropdown/selector for therapy category → specific therapy type
- Auto-populates relevant AEs, priors, data sources, mitigations
- Dynamic dashboard that adapts to selected therapy

### 2.3 Flexible Risk Modeling (Beyond Bayesian)
Multiple statistical approaches, selectable per use case:
- **Bayesian Beta-Binomial** (current) — small samples, sequential updating
- **Frequentist meta-analysis** — random-effects pooling across studies
- **Kaplan-Meier / time-to-event** — onset timing, duration analysis
- **Logistic regression** — risk factor identification
- **Bayesian network** — multi-AE dependency modeling
- **Machine learning** — pattern detection in biomarker data
- **Empirical Bayes** — shrinkage estimation across therapy types

### 2.4 Model Validation Framework
Scientific testing of risk models as data accrues:
- **Calibration plots** — predicted vs observed rates
- **Brier scores** — accuracy of probabilistic predictions
- **Cross-validation** — leave-one-study-out
- **Sequential prediction** — predict next study's rate from prior data
- **Coverage probability** — do 95% CIs contain true rate 95% of time?
- **Sensitivity analysis** — prior choice impact, discount factor sweep
- **Model comparison** — Bayesian vs frequentist vs ML head-to-head

---

## Phase 3: CDP/CSP Dashboard

### 3.1 Clinical Safety Plan (CSP) Generator
Dashboard view that aggregates risk models to support CSP writing:
- **Risk summary table** — all AEs by severity, frequency, expected onset
- **Suggested monitoring schedule** — based on AE onset timing profiles
- **Suggested stopping rules** — Bayesian monitoring boundaries
- **Risk mitigation plan** — recommended interventions per AE

### 3.2 Inclusion/Exclusion Criteria Suggester
Based on risk model outputs:
- **Risk factor analysis** — which patient characteristics increase AE risk
- **Suggested exclusions** — patients at elevated risk (cardiac, hepatic, prior CRS)
- **Suggested inclusion criteria** — target population definition
- **Subgroup risk profiles** — age, comorbidity, prior therapy impact

### 3.3 Protocol Design Support
- **Sample size estimation** — given Bayesian posterior, how many patients needed
- **DSMB charter guidance** — stopping rules, interim analysis schedule
- **Comparator selection** — which oncology data to benchmark against

---

## Phase 4: Dashboard Quality & Testing

### 4.1 Chrome Testing Protocol
- Open every tab, verify data loads
- Click every interactive element
- Test error states (API down, slow response)
- Test responsive layout
- Verify print/export
- Screenshot each view for comparison

### 4.2 Feature Audit
- Cut features that don't render well or are too limited
- Improve visualizations that are hard to read
- Add missing interactions
- Fix any broken API calls

### 4.3 Iteration Cycle
1. Test → identify issues → fix → re-test
2. At least 2 full cycles
3. Agent teams for parallel testing + fixing

---

## Phase 5: Implementation Priority

### Sprint 1 (Immediate)
1. Research all cell therapy types + AE profiles (agent team)
2. Test current dashboard in Chrome (agent)
3. Create TherapyType registry and selector
4. Fix any dashboard issues found in testing

### Sprint 2
1. Add treatment type selector to dashboard
2. Expand AE registry beyond current 4 types
3. Add frequentist meta-analysis as alternative model
4. Add model validation framework (calibration, Brier score)

### Sprint 3
1. CDP/CSP dashboard tab
2. Inclusion/exclusion criteria suggester
3. Monitoring schedule generator
4. Stopping rules integration

### Sprint 4
1. Full Chrome testing cycle
2. Feature audit and pruning
3. Final iteration and polish
4. gpuserver1 heavy computation (Monte Carlo validation, model comparison)

---

## Agent Team Assignments

| Agent | Task | Type |
|-------|------|------|
| Researcher 1 | Cell therapy types + AE profiles | Explore/Research |
| Researcher 2 | Risk modeling approaches for cell therapy | Explore/Research |
| Tester 1 | Chrome dashboard testing — every button | Browser automation |
| Builder 1 | TherapyType registry + selector | general-purpose |
| Builder 2 | CDP/CSP dashboard tab | general-purpose |
| Validator | Model validation framework | general-purpose |
| gpuserver1 | Heavy computation, meta-analysis | Remote |

---

## Context Preservation
- This file: `EXPANSION-PLAN.md`
- Session state: `SESSION-STATE.md`
- Agent instructions: `.claude/CLAUDE.md`
- System spec: `SPECIFICATION.md`
- All pushed to GitHub for any agent to read
