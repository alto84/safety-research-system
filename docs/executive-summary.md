# Predictive Safety Platform (PSP) - Executive Summary

**Document Classification:** AstraZeneca Confidential - Internal Use Only
**Version:** 1.0 | **Date:** 2026-02-06
**Author:** Cell Therapy Safety Sciences / Data Science & AI
**Sponsor:** SVP Patient Safety, SVP Oncology R&D

---

## The Problem

Cell and gene therapy (CGT) represents one of the highest-value frontiers in oncology and immunology, but it carries a disproportionate safety burden that threatens program viability.

### Current State

- **40% of FDA clinical holds** are attributable to CGT programs, despite CGT representing a fraction of the overall clinical portfolio.
- **Immune-mediated serious adverse events** --- cytokine release syndrome (CRS), immune effector cell-associated neurotoxicity syndrome (ICANS), and hemophagocytic lymphohistiocytosis / macrophage activation syndrome (HLH/MAS) --- are the primary drivers of regulatory holds, treatment discontinuations, and patient harm.
- The onset of these events is often rapid (hours to days post-infusion), with narrow intervention windows. Current pharmacovigilance approaches detect signals **after** harm has occurred.
- A single 6-month clinical hold costs an estimated **$50-80M** in direct costs (operational, manufacturing idle time, regulatory remediation) and **$200M+** in risk-adjusted NPV erosion from delayed commercialization.

### Why Existing Approaches Fall Short

| Approach | Limitation |
|----------|-----------|
| Manual signal detection | Reactive; identifies patterns only after multiple events |
| Static risk scoring | Cannot integrate longitudinal, multi-modal patient data |
| Rule-based monitoring | Misses non-linear, multi-factor risk interactions |
| Single-biomarker thresholds | Insufficient sensitivity/specificity for complex immune cascades |

---

## The Solution: Predictive Safety Platform

PSP is an AI-powered platform that predicts immune-mediated adverse events **before clinical manifestation**, enabling preemptive intervention and proactive regulatory engagement.

### Core Capabilities

1. **Multi-Modal Risk Prediction** --- Integrates clinical labs, cytokine kinetics, genomics, vitals, and manufacturing batch data into patient-level risk trajectories.
2. **Temporal Modeling** --- Predicts not just whether an event will occur, but **when** and at what **severity grade**, enabling time-sensitive clinical decisions.
3. **Mechanistic Interpretability** --- Model outputs are grounded in known immunological pathways (IL-6/JAK-STAT, endothelial activation, myeloid hyperactivation), enabling regulatory defensibility and clinician trust.
4. **Continuous Learning** --- Multi-model AI architecture absorbs capability improvements from frontier models (Claude, GPT, Gemini) automatically through standardized evaluation and routing.

### Platform Architecture (Summary)

```
Data Layer          AI Layer              Application Layer
-----------         ----------            ------------------
Clinical DBs   -->  Feature Engine   -->  Risk Dashboard (DURGA)
Lab Systems    -->  Prediction Models -->  Clinician Alerts
Genomics       -->  Causal Inference -->  Regulatory Signal Reports
Manufacturing  -->  NLP/Literature   -->  DSMB Briefing Packs
```

---

## Investment and Returns

### Investment Profile

| Stage | Timeline | Investment | Deliverable |
|-------|----------|-----------|-------------|
| Stage 1: Foundation | Year 1 | $8M | Validated tool, 3 study integrations, DURGA pathway |
| Stage 2: Pilot | Year 2 | $7M | Advisory-mode deployment in DURGA and SLE-LN trials |
| Stage 3: Scale | Year 3+ | $5M | Cross-TA enterprise deployment, regulatory submissions |
| **Total** | **3 years** | **$20M** | |

### Return on Investment

**Conservative scenario (single hold avoidance):**

- Avoiding one 6-month clinical hold saves $50-80M in direct costs.
- At $20M total investment, the **base-case ROI is approximately 6:1** on direct cost avoidance alone.
- **Payback period: ~18 months** (mid-Stage 2).

**Value drivers beyond hold avoidance:**

| Value Driver | Estimated Annual Value |
|-------------|----------------------|
| Reduced clinical hold duration | $50-80M per event avoided |
| Faster dose optimization through predictive safety margins | $10-20M in trial efficiency |
| Proactive regulatory engagement (pre-submission safety packages) | Acceleration of BLA timelines |
| Reduced patient discontinuation from preemptive management | Improved efficacy readouts |
| Cross-portfolio signal detection | Portfolio-level risk mitigation |

### Strategic Value

- **Regulatory differentiation:** No competitor has deployed prospective AI-based safety prediction in CGT filings. First-mover advantage with FDA/EMA.
- **Pipeline protection:** De-risks the $5B+ CGT and bispecific portfolio by shifting safety from reactive to predictive.
- **Platform economics:** Marginal cost of adding a new molecule to PSP decreases with each deployment. Stage 3 extends to T-cell engagers (TCEs), checkpoint inhibitors, and all immunology MoAs.

---

## Scalability Pathway

```
Stage 1-2: Cell Therapy (CAR-T, CAR-NK, TIL)
    |
    v
Stage 3a: T-Cell Engagers (bispecifics, trispecifics)
    |
    v
Stage 3b: Checkpoint Inhibitors (irAE prediction)
    |
    v
Stage 4: All MoAs, All Therapeutic Areas
    |
    v
Enterprise Platform: Standard safety AI layer across R&D
```

The platform is designed from inception for cross-modality generalization. The feature engineering layer abstracts molecule-specific biomarkers into a common immunological risk ontology, enabling transfer learning across programs.

---

## Governance and Oversight

- **Steering Committee:** SVP Patient Safety (chair), SVP Oncology R&D, VP Data Science & AI, VP Regulatory Affairs, Chief Medical Officer (CGT)
- **Operating Model:** Joint team across Safety Sciences, Data Science, Clinical Operations, and IT/Engineering
- **Regulatory Strategy:** Co-development with FDA CBER through pre-submission meetings; alignment with FDA AI/ML SaMD framework
- **Ethics Review:** Independent AI ethics review board with external clinical and bioethics advisors

---

## Decision Requested

Approval of $8M Stage 1 funding to build the foundational platform, validate against 3 retrospective clinical studies, and establish the DURGA integration pathway. Stage 2/3 funding contingent on Stage 1 milestone achievement.

**Stage 1 Go/No-Go Criteria:**
- AUROC >= 0.80 for Grade >= 3 CRS prediction at 24h pre-onset
- Successful DURGA integration proof-of-concept
- FDA pre-submission feedback on AI-augmented safety monitoring
- Data governance framework approved by DPO and Legal
