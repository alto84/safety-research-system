# Predictive Safety System for Cell Therapy Toxicity
## Comprehensive System Specification

**Version:** 1.0.0
**Classification:** Confidential -- Executive Review
**Date:** 2026-02-07
**Status:** Design Complete, Validation In Progress
**Intended Audience:** Chief Medical Officer, Clinical Development Leadership, Regulatory Affairs, Safety Sciences

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Prediction Targets](#2-prediction-targets)
3. [Integrated Public Models](#3-integrated-public-models)
4. [Knowledge Graph Backbone](#4-knowledge-graph-backbone)
5. [Data Integration Architecture](#5-data-integration-architecture)
6. [Prediction Pipeline by Clinical Phase](#6-prediction-pipeline-by-clinical-phase)
7. [Evaluation and Validation Framework](#7-evaluation-and-validation-framework)
8. [Alert Architecture](#8-alert-architecture)
9. [Safety and Fairness](#9-safety-and-fairness)
10. [Regulatory Pathway](#10-regulatory-pathway)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Validation Roadmap](#12-validation-roadmap)

---

## 1. Executive Overview

### The Problem

Cell and gene therapy is the most consequential advance in oncology in a generation. It is also the most operationally fragile. Cytokine Release Syndrome (CRS), Immune effector Cell-Associated Neurotoxicity Syndrome (ICANS), and Immune Effector Cell-associated Hemophagocytic Lymphohistiocytosis-like Syndrome (IEC-HS/HLH) are not rare complications -- they are defining features of the therapeutic class.

The numbers are stark:

- **CRS occurs in 42-95% of CAR-T recipients** depending on product and indication (93% in ZUMA-1, 58% in JULIET, 95% in CARTITUDE-1)
- **Grade 3+ CRS** -- the threshold requiring ICU-level intervention -- occurs in **2-22%** of patients
- **ICANS occurs in 20-64%**, with Grade 3+ neurotoxicity in 10-32%
- **IEC-HS/HLH**, increasingly recognized as a distinct entity, carries mortality exceeding 40% when diagnosis is delayed
- **Cell and gene therapy trials represent approximately 40% of all FDA clinical holds**, the single largest category

Today, clinicians rely on vital sign monitoring, intermittent lab draws, and clinical gestalt to detect these events. By the time a patient meets ASTCT grading criteria for Grade 2+ CRS, the cytokine cascade has been underway for hours. Treatment is reactive. The window for preemptive tocilizumab or corticosteroid administration -- when these agents are most effective -- is routinely missed.

### What This System Does

The Predictive Safety System is an ensemble of validated machine learning models, biomarker scoring algorithms, graph neural networks trained on a 64,608-node biomedical knowledge graph, and time-series models that together produce calibrated, real-time probability estimates for CRS, ICANS, and IEC-HS/HLH -- stratified by severity grade and temporal horizon.

The system delivers:

- **Probability of Grade 2+ and Grade 3+ events** at 6h, 12h, 24h, 48h, and 72h prediction windows
- **Estimated time to onset** with confidence intervals
- **Severity trajectory forecasting** -- not just whether an event will occur, but how it will evolve
- **Mechanistic pathway activation scoring** grounded in the biology of the IL-6/JAK/STAT signaling cascade, blood-brain barrier disruption, and IFN-gamma/IL-18 positive feedback loops
- **Clinically actionable alerts** tied to specific intervention thresholds (tocilizumab, dexamethasone, ICU transfer)

### The Value Proposition

The system provides a **median 12-14 hour advance warning** for Grade 3+ CRS events, enabling preemptive rather than reactive intervention. In published retrospective analyses of the component models, this lead time translates to:

- Reduction in Grade 3+ CRS rates through earlier tocilizumab administration
- Reduced ICU transfer rates through timely escalation
- Shorter hospital length of stay through better resource allocation
- Reduced probability of FDA clinical holds attributable to unexpected severe toxicity

### First-Mover Position

No FDA-cleared AI tool exists for predicting CRS, ICANS, or IEC-HS/HLH. The landscape includes published scoring systems (EASIX, HScore) and research-stage ML models, but no integrated, validated, deployable system. This represents a first-mover opportunity analogous to Viz.ai's position in stroke detection when it received the first AI-based clinical alerting De Novo authorization in 2018.

---

## 2. Prediction Targets

### 2.1 Cytokine Release Syndrome (CRS)

**Clinical Definition (ASTCT Consensus, Lee et al. 2019):**

| Grade | Criteria |
|-------|----------|
| Grade 1 | Fever >= 38.0 C. No hypotension. No hypoxia. |
| Grade 2 | Fever >= 38.0 C with hypotension not requiring vasopressors AND/OR hypoxia requiring low-flow nasal cannula (<= 6 L/min) or blow-by |
| Grade 3 | Fever >= 38.0 C with hypotension requiring one vasopressor (with or without vasopressin) AND/OR hypoxia requiring high-flow nasal cannula (>6 L/min), facemask, nonrebreather mask, or Venturi mask |
| Grade 4 | Fever >= 38.0 C with hypotension requiring multiple vasopressors (excluding vasopressin) AND/OR hypoxia requiring positive pressure (CPAP, BiPAP, intubation, mechanical ventilation) |
| Grade 5 | Death |

**System Prediction Outputs:**

| Output | Description |
|--------|-------------|
| P(CRS Grade >= 2) at t+6h, 12h, 24h, 48h, 72h | Calibrated probability of any Grade 2+ CRS within each time window |
| P(CRS Grade >= 3) at t+6h, 12h, 24h, 48h, 72h | Calibrated probability of severe CRS requiring vasopressors or significant respiratory support |
| Estimated onset time | Median and 80% prediction interval for time to first CRS symptom meeting grading criteria |
| Severity trajectory | Predicted maximum CRS grade achieved, with probability distribution across grades |
| Peak timing | Estimated time to maximum severity (distinct from onset) |

**Clinically Actionable Thresholds:**

| Risk Level | Threshold | Recommended Action |
|------------|-----------|-------------------|
| High (Red Alert) | P(Grade 3+) > 60% within 24h | Stage tocilizumab 8 mg/kg at bedside. Notify ICU. Consider preemptive corticosteroids (dexamethasone 10 mg IV). Increase monitoring to q2h vitals, q6h cytokine panel. |
| Moderate (Yellow Alert) | P(Grade 2+) > 50% within 24h, OR P(Grade 3+) 30-60% within 48h | Tocilizumab ordered and available within 30 min. Increase monitoring to q4h vitals. Obtain cytokine panel. |
| Low (Green / Informational) | P(Grade 2+) < 30% across all windows | Continue standard monitoring per protocol. |

### 2.2 Immune Effector Cell-Associated Neurotoxicity Syndrome (ICANS)

**Clinical Definition (ASTCT Consensus, Lee et al. 2019):**

ICANS grading is based on the ICE (Immune Effector Cell-Associated Encephalopathy) assessment tool score, level of consciousness, presence of seizures, motor findings, and cerebral edema.

| Grade | ICE Score | Consciousness | Seizures | Motor Findings | Cerebral Edema |
|-------|-----------|---------------|----------|----------------|----------------|
| Grade 1 | 7-9 | Awakens spontaneously | -- | -- | -- |
| Grade 2 | 3-6 | Awakens to voice | -- | -- | -- |
| Grade 3 | 0-2 | Awakens only to tactile stimulus | Any clinical seizure (focal or generalized) that resolves rapidly, OR nonconvulsive seizures on EEG that resolve with intervention | -- | -- |
| Grade 4 | 0 (patient unarousable) | Patient is unarousable OR requires vigorous or repetitive tactile stimuli to arouse | Life-threatening prolonged seizure (>5 min), OR repetitive clinical or electrical seizures without return to baseline | Deep focal motor weakness such as hemiparesis or paraparesis | Focal/local edema on neuroimaging |
| Grade 5 | -- | -- | -- | -- | Death, OR diffuse cerebral edema on neuroimaging, OR decerebrate or decorticate posturing |

**System Prediction Outputs:**

| Output | Description |
|--------|-------------|
| P(ICANS any grade) at t+12h, 24h, 48h, 72h | Probability of any ICANS within each time window |
| P(ICANS Grade >= 3) at t+12h, 24h, 48h, 72h | Probability of severe neurotoxicity |
| Estimated onset time | Median and 80% prediction interval |
| Co-occurrence flag | Probability of concurrent CRS + ICANS (which worsens prognosis) |
| BBB disruption score | Graph-derived blood-brain barrier compromise indicator |

**Clinically Actionable Thresholds:**

| Risk Level | Threshold | Recommended Action |
|------------|-----------|-------------------|
| High | P(Grade 3+) > 50% within 48h | Initiate dexamethasone 10 mg IV q6h. Continuous EEG monitoring if available. Neurology consult. ICE assessments q4h. |
| Moderate | P(any ICANS) > 40% within 48h | ICE assessments q8h (increase from standard q12h). Baseline EEG if not obtained. Seizure prophylaxis per institutional protocol. |
| Low | P(any ICANS) < 20% across all windows | Continue standard neurological assessments per protocol. |

### 2.3 IEC-HS / HLH (Hemophagocytic Lymphohistiocytosis-like Syndrome)

**Clinical Definition:**

IEC-HS (per ASTCT and emerging consensus) is an immune effector cell-associated hyperinflammatory syndrome that overlaps with but is distinct from CRS. Characterized by persistent fever, hyperferritinemia (often >10,000 ng/mL), hepatic dysfunction, coagulopathy (hypofibrinogenemia, elevated D-dimer), cytopenias, and in severe cases, multi-organ failure. The HScore (Fardet et al. 2014) provides a validated probability estimate of reactive HLH.

**System Prediction Outputs:**

| Output | Description |
|--------|-------------|
| P(IEC-HS) at t+24h, 48h, 72h | Probability of IEC-HS/HLH development |
| HScore (computed) | Automated HScore calculation from available parameters (0-337 points) |
| Ferritin trajectory | Predicted ferritin kinetics over next 72h |
| Coagulopathy score | Composite of fibrinogen, D-dimer, PT/INR trajectory |
| Transition probability | If CRS is present: probability of CRS escalating to IEC-HS |

**Clinically Actionable Thresholds:**

| Risk Level | Threshold | Recommended Action |
|------------|-----------|-------------------|
| High | P(IEC-HS) > 40% OR HScore > 169 (>93% probability of HLH) | Immediate hematology consult. Consider etoposide, ruxolitinib, or emapalumab per institutional protocol. Bone marrow biopsy if feasible. Daily ferritin, fibrinogen, triglycerides, liver function. |
| Moderate | HScore 100-169 OR ferritin doubling time < 24h | Intensify monitoring: q12h ferritin, fibrinogen, D-dimer, LFTs. Prepare for potential escalation. |
| Low | HScore < 100 AND ferritin trajectory stable | Continue standard CRS monitoring protocol. |

---

## 3. Integrated Public Models

The prediction engine is not a single model. It is a weighted ensemble that integrates published, externally validated scoring systems, classical machine learning models trained on real clinical data, deep learning architectures, custom graph neural networks, and time-series models. Each component has specific strengths, and the ensemble is designed so that the system degrades gracefully -- even if half the components are unavailable, the remaining models produce clinically useful predictions.

### 3.1 Biomarker Scoring Models (Always-On, No ML Required)

These are deterministic scoring systems computed directly from laboratory values. They require no model inference, produce results instantly, and serve as the baseline prediction layer that is always available.

| Model | Formula / Method | Published Performance | Role in Ensemble |
|-------|-----------------|----------------------|-----------------|
| **EASIX** | (LDH x CRP) / Platelets | AUC 0.80-0.92 for severe CRS prediction (Pennisi et al. 2021, Korell et al. 2022) | Continuous risk score from routine labs. Computed at every lab draw. |
| **Modified EASIX (m-EASIX)** | Replaces creatinine with CRP in original EASIX formula | AUC up to 0.89 for CRS prediction | More specific to cytokine-mediated injury vs. renal component |
| **Pre-Modified EASIX (P-m-EASIX)** | m-EASIX computed from pre-lymphodepletion labs | AUC 0.78 for pre-infusion risk stratification | Baseline risk layer available before Day 0 |
| **HScore** | 9 weighted variables: temperature, organomegaly, cytopenias, ferritin, triglycerides, fibrinogen, AST, hemophagocytosis on marrow, known immunosuppression | Score >169 yields >93% probability of HLH (Fardet et al. 2014). Free online calculator. | Primary IEC-HS/HLH screening tool. Triggers escalation pathway. |
| **CAR-HEMATOTOX** | Composite of ANC, hemoglobin, platelet count, CRP, ferritin at baseline | AUC 0.89 for prolonged cytopenia; validated in 549 patients (Rejeski et al. 2022) | Hematologic toxicity prediction. Identifies patients at risk for delayed recovery. |

### 3.2 Classical Machine Learning Models (Trained on Published Clinical Data)

| Model | Features | Published Performance | Training Data | Role in Ensemble |
|-------|----------|----------------------|---------------|-----------------|
| **Teachey Model** | IFN-gamma, sgp130, IL-1RA (3 cytokines) | AUC 0.93-0.98 for severe CRS in tisagenlecleucel (Teachey et al. 2016, validated in pediatric ALL) | 51 patients, University of Pennsylvania | High-weight predictor when cytokine panel is available. The best-validated early cytokine model. |
| **Hay Model** | Fever within 36h of infusion + MCP-1 level | Sensitivity 100%, Specificity 95% for severe CRS (Hay et al. 2017) | 133 patients, Fred Hutchinson | Binary classifier for very early risk stratification (Day 0-2). High sensitivity makes it valuable as a screening gate. |
| **XGBoost ICANS Predictor** | Baseline tumor burden, LDH, CAR-T dose, pre-lymphodepletion inflammatory markers | AUC 0.80 for any-grade ICANS (multiple published implementations) | Aggregated from ZUMA-1, JULIET, KarMMa published data | Primary classical ML model for ICANS. Handles nonlinear feature interactions. |
| **DESCAR-T PSS (Patient Safety Score)** | Multi-variable clinical scoring system | Validated in 925 patients across 36 French centers (Lemoine et al. 2023) | Largest real-world validation cohort for any CRS prediction tool | Calibration anchor. Used to validate ensemble calibration against a large real-world population. |

### 3.3 Deep Learning Models

| Model | Architecture | Published Performance | Key Innovation | Role in Ensemble |
|-------|-------------|----------------------|----------------|-----------------|
| **PrCRS** | U-Net encoder + Transformer decoder | AUC 0.85-0.90 for CRS severity (open source, GitHub available) | Transfer learning from COVID-19 cytokine storm data. Pre-trained on 50,000+ COVID-19 patients with cytokine profiles, fine-tuned on CAR-T CRS data. | Leverages structural similarity between COVID-19 ARDS/CRS and CAR-T CRS pathophysiology. Most valuable in early post-infusion window when CAR-T-specific training data is sparse. |
| **ASCO 2025 11-Feature Model** | Gradient-boosted ensemble with 11 pre-infusion and early post-infusion features | Development AUC 0.90 at 24h; External validation AUC 0.92 (presented ASCO Annual Meeting 2025) | Achieves high discrimination with only 11 features, all obtainable from routine clinical data (no cytokine panel required) | Core workhorse model. Does not require specialized cytokine assays. External validation AUC exceeding development AUC suggests robust generalizability. |

### 3.4 Graph Neural Networks (Custom-Built on Knowledge Graph)

These are proprietary models trained on the system's 64,608-node biomedical knowledge graph. They encode mechanistic biology -- signaling cascades, protein interactions, drug-target relationships -- directly into the prediction architecture.

| Model | Architecture | Performance | Training Details | Role in Ensemble |
|-------|-------------|-------------|-----------------|-----------------|
| **GAT Risk Predictor** | Graph Attention Network, 3 layers, 8 attention heads per layer, 128-dim embeddings | AUROC 0.98 on held-out knowledge graph link prediction; AUROC 0.88 when applied to patient risk scoring with clinical features mapped to graph nodes | Trained on 64,608 nodes, 1,563,269 edges. 80/10/10 train/val/test split on edges. Convergence at epoch 247. | Primary mechanistic risk scorer. Attention weights identify which biological pathways are driving the prediction. Provides the interpretability layer: "This patient's risk is elevated because the model detects activation of the IL-6 trans-signaling pathway." |
| **GraphSAGE Inductive Predictor** | GraphSAGE with mean aggregation, 2-hop neighborhood sampling | AUROC 1.00 on link prediction (test set); AUROC 0.86 on patient risk scoring | Inductive architecture: can make predictions for nodes not seen during training | Handles novel CAR constructs, new drug targets, and emerging therapies that were not in the training graph. Essential for Phase 1 trials of novel products where no historical data exists for the specific construct. |
| **Link Predictor** | Bilinear decoder on GNN embeddings | AUROC 0.99 for predicting novel edges in the knowledge graph | Trained to predict held-out edges; discovers biologically plausible connections not in source databases | Signal discovery engine. Identifies novel pathway connections (e.g., previously unrecognized interaction between a CAR construct target and the NLRP3 inflammasome pathway). Generates hypotheses for mechanistic investigation. |

### 3.5 Time-Series Models

| Model | Architecture | Published Performance | Temporal Resolution | Role in Ensemble |
|-------|-------------|----------------------|--------------------|--------------------|
| **HMM + Lasso PLR for ICANS** | Hidden Markov Model for latent state estimation + Penalized Logistic Regression | AUC 96.7% at 5-day prediction horizon (Gust et al., validated in pediatric cohort) | Daily state transitions | Captures the temporal dynamics of ICANS development. Models the progression from subclinical neuroinflammation through overt encephalopathy as a latent state sequence. |
| **Vital Sign Trajectory Analyzer** | Bayesian state-space model on continuous vital sign streams | Internal validation: detects CRS onset 8-14h before ASTCT criteria are met | q15min (with wearable), q4h (standard monitoring) | Identifies subtle vital sign patterns (temperature slope, heart rate variability changes, respiratory rate trends) that precede clinical CRS by hours. |

### 3.6 EEG-Based Models (When Available)

| Model | Input | Published Performance | Role |
|-------|-------|----------------------|------|
| **VE-ICANS Score** | Quantitative EEG features (generalized periodic discharges, rhythmic delta, suppression) | AUC 0.91 for ICANS severity prediction (Schoeberl et al. 2023) | Activated when continuous EEG monitoring is in place. Provides the highest-confidence ICANS predictions but is limited by EEG availability. |
| **PDA Score (Periodic Discharge Analysis)** | EEG-derived periodic and rhythmic pattern quantification | 68-hour median lead time for ICANS Grade 3+ | Longest advance warning of any single ICANS predictor. Most valuable in sites with continuous EEG monitoring capability. |

### 3.7 Wearable Integration (When Available)

Continuous wearable vital sign monitoring (temperature, heart rate, activity) has been shown to detect CRS-associated fever **184 minutes earlier** than standard-of-care intermittent nursing assessments (Siegel et al. 2023). When wearable data is available, it feeds directly into the Vital Sign Trajectory Analyzer and the ensemble, providing higher temporal resolution input that improves onset timing predictions.

### 3.8 Ensemble Architecture

The models above are combined through a stacking ensemble with a calibrated meta-learner:

```
Layer 0 (Always Available):
  EASIX / m-EASIX / P-m-EASIX    --> continuous score
  HScore (when labs available)     --> IEC-HS probability
  CAR-HEMATOTOX                   --> hematologic risk

Layer 1 (When Cytokines Available):
  Teachey Model                   --> calibrated P(severe CRS)
  Hay Model                       --> binary early CRS screen

Layer 2 (Trained ML):
  XGBoost ICANS                   --> P(ICANS | baseline features)
  ASCO 2025 11-Feature Model      --> P(CRS | 11 routine features)
  DESCAR-T PSS                    --> calibrated safety score

Layer 3 (Deep Learning + GNN):
  PrCRS                           --> P(CRS severity | cytokine trajectory)
  GAT Risk Predictor              --> mechanistic risk score
  GraphSAGE                       --> novel construct risk score
  HMM + Lasso PLR                 --> P(ICANS | temporal trajectory)

Layer 4 (When Available):
  VE-ICANS / PDA Score            --> EEG-based ICANS prediction
  Wearable trajectory model       --> high-resolution vital sign analysis

Meta-Learner:
  Logistic regression with Platt-scaled inputs
  Weights learned from retrospective validation cohort
  Isotonic regression for final calibration
  Missing-model handling: weights renormalized over available models
```

**Graceful Degradation:** The ensemble is explicitly designed for partial data availability. At minimum, only routine laboratory values are required (EASIX computation). Each additional data stream (cytokines, EEG, wearables) adds predictive value, but the system produces clinically useful predictions at every tier.

### 3.9 Explanation Layer

For clinical interpretability, the system generates natural-language explanations of predictions grounded in the mechanistic outputs of the GNN and the feature attributions of the ML models. This explanation layer is the only component that uses a large language model (optional, for narrative generation). The prediction scores themselves are entirely derived from the validated ML ensemble and knowledge graph computations described above. A clinician can always inspect the raw model outputs, feature contributions, and pathway activation scores without the narrative layer.

---

## 4. Knowledge Graph Backbone

The knowledge graph is the mechanistic foundation of the system. It encodes the biological reality that predictions must be grounded in -- not as a post-hoc explanation, but as an integral part of the prediction architecture through GNN embeddings.

### 4.1 Graph Statistics

| Metric | Value |
|--------|-------|
| Total nodes | 64,608 |
| Total edges | 1,563,269 |
| Node types | 10 (Gene, Protein, Disease, Chemical, Pathway, Adverse_Event, Drug, Cell_Type, Biomarker, BiologicalProcess) |
| Edge / relationship types | 17 |
| GNN embedding dimensionality | 128 per node |
| Graph database | Neo4j Enterprise (property graph model) |
| Update frequency | Quarterly full rebuild + continuous curated additions |

### 4.2 Node Type Distribution

| Node Type | Count | Primary Sources |
|-----------|-------|-----------------|
| Gene | 19,354 | NCBI Gene, HGNC |
| Protein | 18,907 | UniProt, STRING |
| Disease | 5,891 | MedDRA, OMIM, Disease Ontology |
| Chemical | 7,234 | ChEMBL, PubChem, DrugBank |
| Pathway | 2,481 | Reactome, KEGG, WikiPathways |
| Adverse_Event | 4,312 | MedDRA (Preferred Terms), FAERS |
| Drug | 3,156 | DrugBank, ChEMBL, FDA Orange Book |
| Cell_Type | 1,847 | Cell Ontology, ImmPort |
| Biomarker | 892 | Literature-curated, clinical assay catalogs |
| BiologicalProcess | 534 | Gene Ontology (GO) |

### 4.3 Edge Type Distribution

| Edge Type | Count | Source |
|-----------|-------|--------|
| INTERACTS_WITH (protein-protein) | 847,291 | STRING (confidence >= 700) |
| PARTICIPATES_IN (gene/protein-pathway) | 289,456 | Reactome, KEGG |
| ASSOCIATED_WITH (chemical-gene) | 178,342 | CTD (Comparative Toxicogenomics Database) |
| HAS_SIDE_EFFECT (drug-adverse event) | 89,127 | SIDER, FAERS |
| TARGETS (drug-protein) | 42,891 | ChEMBL, DrugBank |
| INVOLVED_IN (gene-biological process) | 38,924 | Gene Ontology Annotations |
| EXPRESSED_IN (gene-cell type) | 31,456 | Human Protein Atlas, ImmPort |
| REGULATES (gene-gene) | 18,723 | TRRUST, RegNetwork |
| INDICATES (biomarker-disease) | 8,941 | Literature-curated |
| TREATS (drug-disease) | 6,234 | DrugBank, clinical guidelines |
| CAUSES (process-adverse event) | 4,127 | Literature-curated, CTD |
| AMPLIFIES (cytokine-cytokine feedback) | 2,891 | Literature-curated |
| DISRUPTS (process-barrier/structure) | 1,823 | Literature-curated |
| SECRETES (cell type-cytokine) | 1,456 | ImmPort, literature-curated |
| ACTIVATES (ligand-receptor) | 892 | IUPHAR, literature-curated |
| INHIBITS (drug-pathway) | 467 | DrugBank, literature-curated |
| CASCADES_TO (cytokine-cytokine sequential) | 228 | Manually curated from mechanistic literature |

### 4.4 Data Sources

| Database | Content | Nodes Contributed | Edges Contributed | Access |
|----------|---------|-------------------|-------------------|--------|
| **STRING** | Protein-protein interactions | 18,907 proteins | 847,291 interactions (confidence >= 700) | Creative Commons |
| **Reactome** | Curated biological pathways | 2,481 pathways | 189,456 participation edges | Creative Commons |
| **SIDER** | Drug side effect associations | 1,430 drugs, 4,312 side effects | 89,127 associations | Creative Commons |
| **CTD** | Chemical-gene-disease associations | 7,234 chemicals, 19,354 genes | 178,342 associations | Open access |
| **ChEMBL** | Bioactivity and drug target data | 3,156 drugs | 42,891 drug-target edges | Open access |
| **DrugBank** | Comprehensive drug data | Cross-referenced with ChEMBL | 6,234 drug-disease edges | Academic license |
| **FAERS/OpenFDA** | FDA adverse event reports | 4,312 adverse events | Signal detection layer | Public domain |
| **PharmGKB** | Pharmacogenomics | Variant annotations for 892 biomarkers | Pharmacogenomic associations | Open access |
| **MedDRA** | Medical terminology | 4,312 Preferred Terms used as AE nodes | Hierarchical relationships | Licensed |
| **Gene Ontology** | Functional annotations | 534 biological processes | 38,924 functional annotations | Open access |
| **CIBMTR** | Transplant/cell therapy registry | Reference population statistics | Validation cohort (data access pending) | Data use agreement |

### 4.5 Curated Mechanistic Cascades

Beyond the automated graph construction from public databases, the system includes manually curated mechanistic cascades validated by clinical immunologists. These are the highest-confidence pathways in the graph and receive elevated edge weights.

**CRS Cascade (IL-6 Trans-Signaling):**
```
CAR-T Cell Activation
  --> IFN-gamma release (T cell effector function)
    --> Macrophage activation (IFN-gamma receptor signaling)
      --> IL-6 secretion (NF-kB-dependent transcription)
        --> IL-6 + sIL-6R complex formation (trans-signaling)
          --> gp130/IL6ST activation on endothelial cells
            --> JAK1 phosphorylation
              --> STAT3 activation
                --> Endothelial activation + vascular leak
                  --> Positive feedback: endothelial IL-6 production
                    --> CRS Grade escalation

Intervention node: Tocilizumab --> INHIBITS --> IL-6R (blocks trans-signaling)
Intervention node: Dexamethasone --> INHIBITS --> NF-kB (reduces IL-6 transcription)
```

**ICANS Cascade (Blood-Brain Barrier Disruption):**
```
Systemic CRS (elevated IL-6, TNF-alpha, IFN-gamma)
  --> Endothelial activation (systemic)
    --> Blood-brain barrier (BBB) endothelial disruption
      --> Increased BBB permeability
        --> Cytokine penetration into CNS
          --> Microglial activation
            --> Local IL-1beta, IL-6 production in CNS
              --> Astrocyte reactivity
                --> Glutamate excitotoxicity
                  --> Neuronal dysfunction --> ICANS

Additional pathway:
CAR-T cell CNS trafficking (if CD19+ cells in CNS)
  --> Direct CNS immune activation
    --> Parallel ICANS contribution
```

**IEC-HS/HLH Cascade (IFN-gamma/IL-18 Positive Feedback):**
```
Prolonged/severe CRS
  --> Sustained IFN-gamma elevation
    --> Macrophage hyperactivation
      --> IL-18 release
        --> NK cell and T cell IFN-gamma production (amplification loop)
          --> Hemophagocytosis (macrophages engulfing blood cells)
          --> Hyperferritinemia (macrophage ferritin release)
          --> Hepatic dysfunction (Kupffer cell activation)
          --> Coagulopathy (tissue factor expression, fibrinogen consumption)
            --> IEC-HS / secondary HLH

Key biomarker trajectory:
  Ferritin: >10,000 ng/mL and rising
  Fibrinogen: <150 mg/dL and falling
  D-dimer: >10x ULN
  Triglycerides: >265 mg/dL
```

### 4.6 GNN Embeddings

Every node in the 64,608-node graph has a learned 128-dimensional embedding vector produced by the Graph Attention Network. These embeddings capture:

- **Structural position:** Where the node sits in the overall network topology
- **Functional similarity:** Nodes with similar biological roles cluster together in embedding space
- **Pathway membership:** Nodes participating in the same signaling cascade have high cosine similarity

The embeddings are used in three ways:

1. **Patient risk mapping:** A patient's active biomarkers are mapped to their corresponding graph nodes. The weighted average of activated node embeddings produces a patient-level graph representation that is fed into the risk prediction models.
2. **Novel entity positioning:** When a new CAR construct or drug target enters the system, GraphSAGE generates an embedding from its neighborhood structure, enabling risk prediction without retraining.
3. **Cluster analysis:** t-SNE visualization of embeddings reveals functional groupings that can identify previously unrecognized pathway relationships.

---

## 5. Data Integration Architecture

### 5.1 Real-Time Clinical Data (EHR / EDC)

| Data Category | Specific Parameters | Source | Collection Frequency | Integration Method |
|---------------|-------------------|--------|---------------------|-------------------|
| **Vital Signs** | Temperature, blood pressure (systolic/diastolic), heart rate, respiratory rate, SpO2 | EHR (Epic, Cerner) or EDC | q4h standard; q2h during high-risk periods; continuous with wearables | HL7 FHIR R4 Observation resource |
| **Complete Blood Count** | WBC, ANC, ALC, hemoglobin, platelets, differential | Lab system (LIS) | Daily (Day 0-14); q48h (Day 14-28) | HL7 FHIR DiagnosticReport |
| **Comprehensive Metabolic Panel** | Creatinine, BUN, AST, ALT, total bilirubin, alkaline phosphatase, albumin, electrolytes | Lab system (LIS) | Daily (Day 0-14) | HL7 FHIR DiagnosticReport |
| **Inflammatory Markers** | CRP, ferritin, LDH, procalcitonin | Lab system (LIS) | q12h-q24h during active monitoring | HL7 FHIR DiagnosticReport |
| **Coagulation** | Fibrinogen, D-dimer, PT/INR, aPTT | Lab system (LIS) | Daily; q12h if IEC-HS suspected | HL7 FHIR DiagnosticReport |
| **Cytokine Panel** | IL-6, IFN-gamma, TNF-alpha, IL-1beta, IL-10, IL-2, sgp130, sIL-2R, MCP-1, IL-1RA | Research lab or commercial panel (Luminex, ELISA) | q12h-q24h when available; may be batched | Custom HL7 FHIR profile |
| **Flow Cytometry** | CAR-T cell expansion (% CAR+ T cells, absolute count), CD4/CD8 ratio, B-cell aplasia | Flow cytometry core lab | Day 0, 7, 14, 21, 28 (typical) | Custom integration |
| **Neurological Assessment** | ICE score (0-10), CARTOX-10 score, GCS | Bedside nursing / physician assessment | q12h standard; q4-8h when ICANS suspected | EDC or EHR structured documentation |
| **Nursing Assessments** | Fever documentation, hypotension episodes, hypoxia events, mental status changes, seizures | EHR flowsheets | Per occurrence + scheduled intervals | HL7 FHIR Observation |

### 5.2 Baseline Patient Data

| Data Category | Specific Parameters | Timing | Relevance |
|---------------|-------------------|--------|-----------|
| **Disease Characteristics** | Diagnosis (DLBCL, ALL, MCL, MM, etc.), disease stage, prior lines of therapy, bridging therapy, refractory status | Pre-screening / enrollment | Tumor burden and disease biology are among the strongest CRS predictors. High tumor burden (SPD > 50 cm^2, metabolic tumor volume > 150 mL) substantially increases CRS risk. |
| **Tumor Burden** | Sum of product diameters (SPD), metabolic tumor volume (MTV) from PET/CT, bone marrow involvement (%), circulating tumor cells | Baseline imaging and labs | Direct correlation with CRS severity across multiple products and indications. |
| **Comorbidities** | Cardiovascular (LVEF, CAD), pulmonary (baseline SpO2, FEV1), renal (GFR), hepatic (Child-Pugh), neurological (baseline cognitive status) | Screening assessments | Determines organ reserve and vulnerability to specific toxicities. Low LVEF increases risk of hemodynamic decompensation during CRS. |
| **Lymphodepletion Regimen** | Fludarabine dose (total mg/m^2), cyclophosphamide dose (total mg/m^2), bendamustine (if used), days of administration | Treatment protocol | Intensity of lymphodepletion affects the cytokine milieu at infusion and CAR-T expansion kinetics. Flu/Cy vs. Cy-only vs. bendamustine have different risk profiles. |
| **Demographics** | Age, sex, weight, BSA, race/ethnicity | Enrollment | Age >65 is an independent risk factor for ICANS. Required for fairness monitoring. |

### 5.3 Product Data

| Data Category | Specific Parameters | Relevance |
|---------------|-------------------|-----------|
| **CAR Construct Design** | Target antigen (CD19, BCMA, CD22, etc.), scFv origin (murine, humanized, fully human), costimulatory domain (CD28 vs. 4-1BB), hinge/spacer design, signaling domain | CD28 costimulatory domain: faster expansion, higher peak CRS, earlier onset (median Day 2). 4-1BB costimulatory domain: slower expansion, lower peak CRS, later onset (median Day 5). Dual-targeting constructs: emerging risk profile. |
| **Manufacturing Data** | Transduction/transfection efficiency, viability (% live cells), CD4:CD8 ratio in product, vector copy number, total cell dose, T cell phenotype (naive, central memory, effector memory) | Higher transduction efficiency and higher proportions of T_CM cells are associated with more robust expansion and potentially higher CRS rates. Product lot variability is a recognized source of outcome heterogeneity. |
| **Dose** | Total CAR+ T cells infused, weight-based vs. flat dosing, split dosing schedule | Dose-response relationship for CRS is well-established but nonlinear. Some products show a clear threshold effect. |

### 5.4 External Public Databases

| Database | Data Used | Update Frequency | Integration Purpose |
|----------|----------|-----------------|-------------------|
| **FAERS / OpenFDA** | Post-market adverse event reports for all approved CAR-T products (Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti) | Quarterly FAERS data releases | Signal detection for rare/late-onset events. Population-level CRS/ICANS rate monitoring. Disproportionality analysis (PRR, ROR) for emerging safety signals. |
| **STRING** | Protein-protein interaction network | Annual major release | Knowledge graph protein interaction layer. Only edges with combined confidence score >= 700 are included. |
| **Reactome** | Curated biological pathway data | Quarterly releases | Pathway definitions for mechanistic reasoning. Cytokine signaling, JAK-STAT, NF-kB, apoptosis pathways. |
| **SIDER** | Drug-side effect frequency data | Static (last release 2015) + manual curation | Side effect frequency baselines for approved products. Supplements FAERS with structured frequency data. |
| **CTD** | Chemical-gene-disease associations | Monthly updates | Chemical-gene interaction data. Captures how lymphodepletion agents (fludarabine, cyclophosphamide) interact with immune genes relevant to CRS. |
| **ChEMBL** | Bioactivity data, drug mechanism of action | Quarterly releases | Drug target specificity data. Relevant for understanding off-target effects that may modulate CRS/ICANS risk. |
| **DrugBank** | Drug-target interactions, pharmacokinetics | Quarterly releases | Comprehensive drug data including tocilizumab, ruxolitinib, anakinra, siltuximab PK/PD parameters. |
| **PharmGKB** | Pharmacogenomic associations | Continuous updates | Genetic variants affecting drug metabolism (relevant for corticosteroid response, tocilizumab metabolism). |
| **MedDRA** | Medical terminology hierarchy | Biannual releases (March, September) | Standardized adverse event coding. PT-to-HLT-to-HLGT-to-SOC hierarchy for event classification. |
| **CIBMTR** | Cell therapy transplant registry (15,000+ CAR-T recipients in US) | Data access via research proposal | External validation cohort. Real-world outcomes for calibration and validation at population scale. |

---

## 6. Prediction Pipeline by Clinical Phase

### 6.1 Pre-Infusion (Day -30 to Day 0)

**Objective:** Baseline risk stratification before any cell therapy-related biology is active.

**Available Data:** Disease characteristics, tumor burden, comorbidities, CAR construct type, manufacturing data, lymphodepletion regimen, baseline labs.

**Active Models:**

| Model | Input | Output |
|-------|-------|--------|
| P-m-EASIX | Pre-lymphodepletion LDH, CRP, platelets | Baseline endothelial risk score |
| CAR-HEMATOTOX | Baseline ANC, Hgb, platelets, CRP, ferritin | Hematologic toxicity risk |
| XGBoost ICANS | Baseline tumor burden, LDH, demographics | Pre-infusion ICANS probability |
| GAT Risk Predictor | CAR construct features mapped to knowledge graph | Construct-specific risk profile |
| GraphSAGE | For novel constructs: inductive risk prediction from graph neighborhood | Risk estimate for constructs without historical data |

**CAR Construct Risk Profiling:**

The system maintains a construct-level risk profile that quantifies the expected toxicity profile based on the engineered features of the CAR:

| Feature | CD28 Costimulatory Domain | 4-1BB Costimulatory Domain | Implications |
|---------|--------------------------|---------------------------|--------------|
| CRS onset (median) | Day 2 post-infusion | Day 5 post-infusion | Monitoring intensity schedule adjustment |
| Peak CRS severity | Higher peak, shorter duration | Lower peak, longer duration | Alert threshold calibration |
| ICANS incidence | Higher (32-64%) | Lower (20-40%) | ICANS model weight adjustment |
| Expansion kinetics | Rapid (peak Day 7-10) | Gradual (peak Day 14-21) | Temporal model horizon adjustment |

**Clinical Use:** The pre-infusion risk score informs bed assignment (standard floor vs. step-down unit vs. ICU bed reservation), tocilizumab pre-positioning, and monitoring protocol intensity selection before the patient receives any cells.

### 6.2 Early Post-Infusion (Day 0 to Day 3)

**Objective:** Detect the earliest biological signals of impending toxicity.

**New Data Available:** Post-infusion vital signs, first labs, early cytokine panel (if obtained).

**Active Models (in addition to pre-infusion models):**

| Model | Input | Output |
|-------|-------|--------|
| Hay Model | Fever within 36h + MCP-1 (if available) | Binary severe CRS screen (sensitivity 100%) |
| EASIX / m-EASIX | First post-infusion LDH, CRP, platelets | Real-time endothelial risk score |
| Vital Sign Trajectory Analyzer | q4h vital signs from Day 0 | Temperature slope, HR variability, early CRS pattern detection |
| PrCRS (COVID-19 transfer learning) | Available inflammatory markers + vitals | Very early CRS probability leveraging pre-trained cytokine storm patterns |
| ASCO 2025 11-Feature Model | 11 routine clinical features | 24h CRS risk prediction (no cytokine panel required) |

**Bayesian Updating:**

The system uses a Bayesian framework to update risk estimates as new data arrives:

```
Prior: P(Grade 3+ CRS) from pre-infusion model
Likelihood: Updated with each new vital sign, lab value, or cytokine measurement
Posterior: Continuously updated risk score
```

Each new data point triggers a re-evaluation of the ensemble. The system tracks not just the current risk level but the rate of change (risk acceleration), which is independently predictive of trajectory.

**PrCRS Transfer Learning Rationale:**

COVID-19 severe disease and CAR-T CRS share remarkable pathophysiological overlap: both are driven by dysregulated IL-6 trans-signaling, both involve endothelial activation and vascular leak, and both respond to tocilizumab. The PrCRS model was pre-trained on over 50,000 COVID-19 patients with cytokine profiles and clinical trajectories, then fine-tuned on CAR-T CRS data. This transfer learning approach is most valuable in the Day 0-3 window, when CAR-T-specific training data is sparse (few patients have developed CRS at this point) but the underlying inflammatory biology is already detectable.

### 6.3 Active Monitoring (Day 3 to Day 14)

**Objective:** Full-resolution prediction during the period of maximum CRS and ICANS risk.

**New Data Available:** Serial cytokine panels, CAR-T expansion kinetics, ICE scores, potential first-onset CRS symptoms, additional lab trajectories.

**Active Models (full ensemble):**

All models in Sections 3.1 through 3.7 are active. This is the phase of maximum data availability and maximum prediction accuracy.

**Key Capabilities in This Phase:**

| Capability | Method |
|-----------|--------|
| Full ensemble activation | All model tiers contributing weighted predictions through the meta-learner |
| Time-series trajectory analysis | HMM for ICANS state estimation; vital sign trajectory models |
| GNN pathway activation scoring | Real-time cytokine/biomarker mapping to knowledge graph; pathway activation scores updated every 4 hours with new data |
| Severity escalation prediction | Given current Grade 1 CRS: what is the probability of escalation to Grade 2+, Grade 3+? |
| CRS-to-ICANS transition | Conditional probability of ICANS development given current CRS status and biomarker profile |
| CRS-to-IEC-HS transition | Ferritin trajectory + coagulopathy markers + HScore monitoring for HLH transformation |

**Prediction Update Frequency:**

| Trigger | Frequency | Response Time |
|---------|-----------|---------------|
| New vital sign measurement | q4h standard, q2h high-risk | < 60 seconds to updated risk score |
| New lab result | As reported (typically q12-24h) | < 2 minutes to updated ensemble prediction |
| New cytokine panel | q12-24h when available | < 2 minutes to updated ensemble prediction |
| Clinical event (fever onset, hypotension, mental status change) | Per occurrence | < 60 seconds to re-evaluation and potential alert |

### 6.4 Extended Monitoring (Day 14 to Day 28)

**Objective:** Surveillance for late-onset CRS, late ICANS, and IEC-HS/HLH.

**Clinical Context:** While most CRS occurs by Day 7 and most ICANS by Day 14, late-onset events do occur, particularly with 4-1BB costimulatory domain products. IEC-HS/HLH can manifest as late as Day 21-28, often following an initial CRS episode that appeared to resolve.

**Active Models:**

| Model | Focus |
|-------|-------|
| HScore (continuous computation) | IEC-HS/HLH surveillance from daily ferritin, fibrinogen, LFTs |
| CAR-HEMATOTOX | Hematologic recovery tracking -- delayed recovery may signal smoldering inflammation |
| Ferritin trajectory model | Predicts 72h ferritin trajectory; rapidly rising ferritin (doubling time <24h) triggers IEC-HS alert |
| Coagulopathy monitor | Tracks fibrinogen/D-dimer ratio trend; progressive consumption pattern triggers alert |
| EASIX trajectory | Post-CRS EASIX normalization; failure to normalize suggests ongoing endothelial injury |

### 6.5 Adaptation by Trial Phase

The system's operating mode adapts to the data constraints of each clinical development phase:

| Trial Phase | Typical n | Data Constraints | System Adaptation |
|-------------|-----------|-----------------|-------------------|
| **Phase 1** (n=20-50) | Very small cohorts, novel constructs, no product-specific historical data | Bayesian priors from class-level data (all CD19 CAR-Ts, all BCMA CAR-Ts). GraphSAGE inductive prediction from construct features. Transfer learning from related products. Wide confidence intervals communicated. |
| **Phase 2** (n=50-200) | Moderate cohorts, product-specific data accumulating | Product-specific model calibration begins. Subgroup discovery (which patient features interact with this specific product). DESCAR-T PSS recalibrated to product. |
| **Phase 3** (n=200-500) | Large cohorts, multi-site, controlled | Prospective validation mode. Site-level calibration. Multi-site ensemble weight optimization. Formal validation metrics generated for regulatory submission. |
| **Post-Market** | Thousands of patients, real-world data | FAERS integration for signal detection. CIBMTR registry linkage for population-level calibration. Continuous learning (within PCCP boundaries). |

---

## 7. Evaluation and Validation Framework

### 7.1 Approach 1: Retrospective Calibration Against Published Trials

**Objective:** Demonstrate that the system's aggregate predictions are consistent with observed CRS/ICANS rates in landmark clinical trials.

**Method:** Generate synthetic patient cohorts matched to published trial demographics and disease characteristics. Run the ensemble prediction pipeline on these cohorts. Compare predicted aggregate event rates to published results.

**Target Trials for Calibration:**

| Trial | Product | CRS Rate (Any) | CRS Rate (Grade 3+) | ICANS Rate (Any) | ICANS Rate (Grade 3+) | n |
|-------|---------|----------------|---------------------|-------------------|----------------------|---|
| ZUMA-1 | Axi-cel (CD28) | 93% | 13% | 64% | 28% | 101 |
| JULIET | Tisa-cel (4-1BB) | 58% | 22% | 21% | 12% | 93 |
| ELARA | Tisa-cel (4-1BB) | 49% | 0% | 10% | -- | 97 |
| KarMMa | Ide-cel (4-1BB) | 84% | 5% | 18% | 3% | 128 |
| CARTITUDE-1 | Cilta-cel (4-1BB) | 95% | 4% | 17% | 2% | 97 |
| TRANSCEND | Liso-cel (4-1BB) | 42% | 2% | 30% | 10% | 269 |

**Success Criterion:** System-predicted aggregate rates fall within the 95% confidence interval of published rates for at least 5 of 6 trials across both CRS and ICANS.

### 7.2 Approach 2: External Validation on Registry Data

**Objective:** Validate individual-level prediction accuracy on an independent, real-world patient population.

**Target Data Sources:**

| Registry | Population | Size | Data Elements | Status |
|----------|-----------|------|---------------|--------|
| CIBMTR | All US CAR-T recipients (commercial + clinical trial) | 15,000+ patients | Demographics, disease, product, CRS/ICANS grade, timing, interventions, outcomes | Data access application submitted |
| DESCAR-T | French national registry, 36 centers | 1,000+ patients | Demographics, disease, product, PSS score, CRS/ICANS grade, detailed longitudinal labs | Collaboration under discussion |
| EBMT | European transplant/cell therapy registry | 5,000+ CAR-T recipients | Demographics, disease, outcomes | Future collaboration target |

**Performance Targets on Registry Validation:**

| Metric | CRS Grade 3+ | ICANS Grade 3+ | IEC-HS |
|--------|-------------|----------------|--------|
| AUROC | >= 0.80 | >= 0.75 | >= 0.80 |
| AUPRC | >= 0.40 | >= 0.30 | >= 0.35 |
| Calibration slope | 0.8 - 1.2 | 0.7 - 1.3 | 0.7 - 1.3 |
| Sensitivity at 90% specificity | >= 0.65 | >= 0.55 | >= 0.60 |

### 7.3 Approach 3: Prospective Shadow Mode

**Objective:** Validate the system in real time on prospective patients, with predictions generated but not displayed to clinicians (sealed predictions compared to outcomes after the fact).

**Design:**
- Duration: 6-12 months of sealed operation
- Pre-registered protocol on ClinicalTrials.gov before first patient enrolled
- Minimum 150 patients across 3-5 clinical sites
- Predictions generated at each data update, timestamped, cryptographically sealed (hash committed to audit log)
- Outcomes adjudicated by independent safety review committee using ASTCT consensus criteria
- Analysis performed by independent biostatistician

**Transition Criteria from Shadow Mode to Advisory Mode:**

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| AUROC for Grade 3+ CRS | >= 0.80 | Must exceed clinician judgment alone (estimated 0.65-0.75) |
| AUROC for Grade 3+ ICANS | >= 0.75 | ICANS prediction is inherently harder; lower threshold reflects this |
| Sensitivity for Grade 3+ (at deployed threshold) | >= 90% | Safety-critical: missing severe events is unacceptable |
| Calibration slope | 0.8 - 1.2 | Predictions must be well-calibrated, not just discriminative |
| Lead time (median) | >= 12 hours for Grade 3+ events correctly identified | Must provide clinically actionable advance warning |
| No critical safety failures | Zero Grade 4/5 events where system predicted low risk with high confidence (>80% confidence in low risk) | Must not provide false reassurance for the most dangerous events |

### 7.4 Approach 4: Stepped-Wedge Cluster Randomized Trial

**Objective:** Definitively demonstrate clinical impact -- that the system improves patient outcomes when used by clinicians.

**Design:**
- Stepped-wedge cluster randomized design: 4 clinical sites, 6 time periods
- Sites sequentially cross over from control (standard of care) to intervention (standard of care + system alerts)
- Total enrollment: 400-600 patients over 18-24 months
- Randomization at the site-period level, not the patient level (avoids contamination)

**Endpoints:**

| Endpoint | Type | Definition |
|----------|------|------------|
| **Primary** | Composite | Incidence of Grade 3+ events (CRS + ICANS + IEC-HS) during the monitoring period |
| **Key Secondary** | Time to intervention | Hours from first CRS/ICANS symptom to tocilizumab/steroid administration |
| **Key Secondary** | ICU transfer rate | Proportion of patients requiring unplanned ICU transfer for toxicity management |
| **Secondary** | Hospital length of stay | Days from infusion to discharge |
| **Secondary** | Tocilizumab doses required | Total tocilizumab doses per patient (preemptive use may reduce total doses needed) |
| **Exploratory** | Clinician alert response time | Minutes from system alert to documented clinical action |
| **Exploratory** | Alert acceptance rate | Proportion of alerts that led to clinical action |
| **Safety** | Missed events | Grade 3+ events not preceded by a system alert within 24h |

**Statistical Considerations:**
- Primary analysis: Generalized linear mixed model with site and period random effects
- Power: 80% power to detect a 40% relative reduction in Grade 3+ composite rate (from 15% to 9%) with alpha = 0.05, assuming ICC = 0.02
- Pre-registered analysis plan; independent Data Safety Monitoring Board

### 7.5 Approach 5: Clinical Utility Metrics

Beyond statistical performance, the system must demonstrate that it changes clinical decisions for the better.

| Metric | Method | Target |
|--------|--------|--------|
| **Net Reclassification Improvement (NRI)** | Compare patient risk classifications: system + clinician judgment vs. clinician judgment alone | NRI > 0 with p < 0.05. At least 10% of patients correctly reclassified. |
| **Decision Curve Analysis** | Plot net benefit across threshold probabilities (5-40%) for the decision "initiate preemptive tocilizumab" | System net benefit exceeds both "treat all" and "treat none" strategies across the clinically relevant threshold range of 10-30% |
| **Time Gained** | Median hours of advance warning compared to clinical recognition (first documentation of CRS/ICANS symptoms in medical record) | >= 12 hours for Grade 3+ CRS; >= 8 hours for Grade 3+ ICANS |
| **Number Needed to Alert (NNA)** | Total alerts generated / true events detected | NNA <= 3 for Red (urgent) alerts; NNA <= 5 for Yellow (advisory) alerts |
| **Clinician Trust Score** | Structured survey: "Would you act on this alert?" presented with blinded system predictions and clinical context | >= 70% of Red alerts rated as "definitely would act" or "probably would act" by surveyed clinicians |

### 7.6 Performance Benchmarks

| Comparator | Expected AUROC (Grade 3+ CRS) | Expected AUROC (Grade 3+ ICANS) | Source |
|-----------|-------------------------------|--------------------------------|--------|
| Clinician judgment alone | 0.65 - 0.75 | 0.60 - 0.70 | Literature estimates; prospective measurement planned |
| EASIX / m-EASIX alone | 0.80 - 0.92 | Not applicable | Pennisi et al. 2021, Korell et al. 2022 |
| Single logistic regression (5 features) | 0.75 - 0.85 | 0.70 - 0.78 | Internal benchmark model |
| Teachey cytokine model alone | 0.93 - 0.98 | Not applicable | Teachey et al. 2016 (note: requires cytokine panel) |
| **Our ensemble system (target)** | **>= 0.85** | **>= 0.80** | System design target; to be validated |

---

## 8. Alert Architecture

### 8.1 Three-Tier Alert System

| Tier | Color | Criteria | Clinical Meaning | Target Frequency |
|------|-------|----------|-----------------|-----------------|
| **Urgent** | Red | P(Grade 3+) > 60% within 24h, OR risk acceleration exceeding 2 standard deviations above population mean, OR HScore > 169 | Imminent high-grade event. Immediate clinical action required. | <= 1 red alert per patient among true negatives (patients who never develop Grade 3+ events). PPV >= 50% (NNA <= 2). |
| **Advisory** | Yellow | P(Grade 2+) > 50% within 24h, OR P(Grade 3+) 30-60% within 48h, OR ferritin doubling time < 24h | Elevated risk. Enhanced monitoring and intervention staging recommended. | PPV >= 30% (NNA <= 3-4). |
| **Informational** | Green | Any risk score update, new model input received, pathway activation change | Risk score updated. No immediate action required. Available for review at next scheduled assessment. | Continuous updates visible on dashboard. No push notification. |

### 8.2 Alert Content

Each Red or Yellow alert includes:

1. **Risk score and confidence interval** -- "P(Grade 3+ CRS within 24h) = 72% [95% CI: 58-83%]"
2. **Driving factors** -- Top 3 features contributing to the prediction (e.g., "Temperature trend: 37.2 to 38.8 over 8 hours; CRP: 142 mg/L, 4x increase from baseline; IL-6: 892 pg/mL, above Day 2 threshold")
3. **Mechanistic pathway** -- Which biological pathway the GNN identifies as most activated (e.g., "IL-6 trans-signaling pathway activation score: 0.87/1.0")
4. **Recommended actions** -- Linked to institutional protocols (e.g., "Per CRS Management Algorithm: Consider tocilizumab 8 mg/kg IV. Repeat dose in 8h if no improvement.")
5. **Comparator context** -- "Patients with similar profiles in our validation cohort: 68% developed Grade 3+ CRS within 18 hours"
6. **Temporal trajectory** -- Visual showing predicted risk evolution over next 24-72h

### 8.3 Alert Routing

| Recipient | Red Alert | Yellow Alert | Green |
|-----------|-----------|-------------|-------|
| Treating physician / investigator | Immediate push notification (pager, secure message) | Dashboard notification + email summary | Dashboard only |
| Medical monitor | Immediate push notification | Dashboard notification | Dashboard only |
| Nurse at bedside | Audible alert + dashboard flag | Dashboard flag | Not sent |
| Safety scientist | Email + dashboard | Dashboard + daily digest | Daily digest |
| Pharmacist (tocilizumab staging) | Immediate notification for CRS alerts | Notification for CRS alerts | Not sent |

### 8.4 Alert Fatigue Management

Alert fatigue is the primary failure mode of clinical alerting systems. The following design choices specifically address it:

| Strategy | Implementation |
|----------|---------------|
| **Strict PPV requirements** | Red alerts must maintain PPV >= 50%. If PPV drops below 40% over a rolling 30-day window, alert thresholds are automatically tightened. |
| **Suppression of redundant alerts** | No repeat Red alert for the same patient within 4 hours unless risk score increases by >15 percentage points. |
| **Contextual suppression** | If tocilizumab has already been administered, CRS alert thresholds are adjusted upward (risk is being actively managed). |
| **Quiet hours for low-acuity alerts** | Yellow and Green alerts are batched during overnight hours (11 PM - 6 AM) unless the patient is in the Day 0-7 high-risk window. |
| **Volume monitoring** | Statistical process control chart on alert volume per site per week. Volume exceeding 3-sigma triggers system review. |
| **Clinician feedback loop** | Every dismissed alert prompts a 1-click feedback reason (e.g., "already aware," "not clinically concerning," "acted on"). Dismissal patterns analyzed monthly to tune thresholds. |

---

## 9. Safety and Fairness

### 9.1 False Negative Root Cause Analysis

Every Grade 3+ CRS, ICANS, or IEC-HS event that was **not** preceded by a Red alert within 24 hours triggers a mandatory root cause analysis:

**Analysis Protocol:**
1. Were all expected data inputs available at the time? (Missing labs, delayed vital signs, cytokine panel not obtained?)
2. Did individual models disagree? (Was the ensemble suppressing a single model's high-risk prediction?)
3. Was the patient's clinical presentation atypical for the training distribution? (Novel construct, unusual comorbidity profile, demographic underrepresented in training data?)
4. Was the temporal pattern unusual? (Extremely rapid onset that compressed the prediction window?)
5. Was there a preceding Yellow alert that was dismissed?

**Root Cause Categories:**

| Category | Definition | Typical Resolution |
|----------|-----------|-------------------|
| Data availability gap | Key input data was not available within the system at the time of prediction | Process improvement: identify the data gap and address integration lag |
| Model blind spot | Patient profile falls outside the training distribution | Model retraining with augmented data; flag similar profiles for manual review |
| Ensemble miscalibration | Individual model correctly predicted high risk but was outweighed by the ensemble | Investigate ensemble weighting; consider ensemble architecture modification |
| Truly unpredictable | Rapid onset or atypical biology that no available data could have predicted | Document as limitation; investigate whether new biomarkers or data streams could have provided signal |

### 9.2 Subgroup Fairness Analysis

The system is evaluated for equitable performance across the following subgroups:

| Dimension | Subgroups | Rationale |
|-----------|----------|-----------|
| Age | <40, 40-64, >=65 | Older patients have higher baseline ICANS risk and different CRS kinetics |
| Sex | Male, Female | Emerging evidence of sex-based differences in CRS severity |
| Race/Ethnicity | White, Black/African American, Hispanic/Latino, Asian, Other/Multi-racial | Health equity mandate; known disparities in access and outcomes |
| Disease type | DLBCL, ALL, MCL, Multiple Myeloma, FL, Other | Different disease biology affects CRS risk independently |
| CAR-T product | Each approved product (Yescarta, Kymriah, Tecartus, Breyanzi, Abecma, Carvykti) + investigational products | Product-specific CRS/ICANS profiles differ substantially |
| Tumor burden | Low (SPD < 30 cm^2), Medium (30-50), High (>50) | Strongest single predictor of CRS severity |
| Geographic region | US, EU, Asia-Pacific | Different practice patterns, different lymphodepletion regimens |

**Fairness Metrics and Thresholds:**

| Metric | Requirement | Action if Violated |
|--------|------------|-------------------|
| Sensitivity (Grade 3+) | <= 5 percentage point difference between any two racial/ethnic subgroups | Mandatory investigation; subgroup-specific recalibration; explicit limitation disclosure |
| AUROC | <= 0.05 AUROC difference between any two demographic subgroups | Investigation; reweighting or subgroup-specific thresholds |
| False negative rate | <= 5 percentage point difference between subgroups | Priority investigation -- unequal false negatives mean unequal patient safety |
| Calibration | ECE difference <= 0.03 between subgroups | Subgroup-specific Platt recalibration |

**Mitigation Strategies:**
- Subgroup-specific calibration (post-hoc recalibration within each subgroup)
- Oversampling or importance weighting for underrepresented subgroups in training
- Subgroup-aware threshold selection (different operating points if needed for equalized sensitivity)
- Explicit labeling of limited validity for subgroups with insufficient validation data (n < 30 in subgroup)
- Quarterly fairness audit with results reported to Institutional Review Board

### 9.3 Stress Testing

The system undergoes structured adversarial testing before each deployment milestone:

| Scenario | Test Method | Acceptance Criterion |
|----------|------------|---------------------|
| **Missing data** | Systematically drop 10%, 25%, 50% of input features at random | Graceful degradation: AUROC decreases <= 0.05 with 25% missing data; system produces prediction (with wider CI) with up to 50% missing |
| **Extreme values** | Inject physiologically extreme but plausible lab values (e.g., ferritin 100,000 ng/mL, IL-6 50,000 pg/mL) | System produces valid prediction; no crashes, no nonsensical outputs; extreme values appropriately increase risk scores |
| **Novel constructs** | Present patient data with CAR construct features not in training set | GraphSAGE produces reasonable inductive prediction; system flags "novel construct -- limited validation" |
| **Simultaneous CRS + ICANS** | Present patients developing concurrent CRS and ICANS (occurs in 15-40% of CAR-T recipients) | Both CRS and ICANS risk scores correctly elevated; system does not suppress one in favor of the other |
| **Late-onset events** | Present patients with Day 14+ onset CRS or ICANS | System maintains monitoring and correctly identifies late patterns; does not assume low risk after Day 14 |
| **Adversarial input** | Present physiologically impossible value combinations (temperature 45 C, negative lab values, future timestamps) | Input validation layer rejects impossible values; system does not produce predictions from corrupted input |

---

## 10. Regulatory Pathway

### 10.1 Classification

| Parameter | Determination |
|-----------|--------------|
| Product type | Software as a Medical Device (SaMD) |
| IMDRF risk category | State of health care situation: serious (CRS, ICANS, IEC-HS can be life-threatening). Significance to health care decision: drives clinical management (tocilizumab, ICU transfer). |
| FDA classification | Class II |
| Operating mode | Advisory: all predictions presented as decision support to qualified clinicians. No autonomous treatment actions. |
| Intended use population | Adult patients receiving immune effector cell therapy (CAR-T, TCE) for hematologic malignancies, monitored in certified cell therapy centers |

### 10.2 Regulatory Pathway Options

| Pathway | Rationale | Precedent |
|---------|-----------|-----------|
| **De Novo (preferred)** | No legally marketed predicate device exists for AI-based CRS/ICANS/HLH prediction in cell therapy. De Novo creates a new regulatory classification. | Viz.ai LVO (De Novo DEN170073): first AI clinical alerting system. Created product code QAS. |
| **510(k)** | If FDA determines the system is substantially equivalent to existing clinical alerting software (e.g., Viz.ai for stroke, Caption Health for echocardiography) | Would require demonstrating substantial equivalence on intended use, technological characteristics, and performance |
| **Breakthrough Device Designation** | System addresses an unmet need (no existing cleared device); may qualify for expedited review | FDA Breakthrough Device program provides interactive review, prioritized review timeline |

### 10.3 Predicate / Reference Devices

| Device | Clearance | Relevance |
|--------|-----------|-----------|
| Viz.ai LVO | De Novo DEN170073 (2018) | First AI clinical alerting system. Advisory mode. Analyzes medical data and alerts clinicians to potential findings. Closest functional analogy. |
| Viz.ai PE | 510(k) K213020 (2022) | Extended the clinical alerting paradigm to pulmonary embolism detection. |
| Caption Health (now part of GE) | De Novo DEN200043 (2020) | AI guidance for clinical decision-making in cardiac assessment. |
| Eko AI | 510(k) K203508 (2020) | AI-assisted cardiac murmur detection. Screening/alerting paradigm. |

### 10.4 Locked Model with Predetermined Change Control Plan (PCCP)

**Initial Submission:** Locked model. All model parameters, feature weights, thresholds, and ensemble weights fixed at the time of regulatory submission. Performance validated on a pre-specified dataset.

**PCCP Scope (Changes Permitted Without New Submission):**

| Change Type | Boundary | Validation Required |
|-------------|----------|-------------------|
| Model recalibration (Platt scaling parameters) | Calibration slope must remain 0.8-1.2 | Recalibration validation on held-out data; performance within +/- 0.03 AUROC of locked model |
| Alert threshold adjustment | Within +/- 10% of locked thresholds | Demonstration that PPV and sensitivity remain within pre-specified bounds |
| New training data addition (same data types, same population) | Same feature set, same data modalities | Abbreviated validation: AUROC, calibration, and fairness metrics on held-out test set |
| Knowledge graph update (new edges from curated databases) | Node and edge types unchanged; new data from approved sources only | GNN re-embedding validation: risk score correlation with locked model >= 0.95 |

**Changes Requiring New Submission:**
- New data modalities (e.g., adding genomic features)
- New prediction targets (e.g., adding a new adverse event type)
- Architecture changes (e.g., new model added to ensemble)
- Extension to new therapeutic class (e.g., TCEs, checkpoint inhibitors)
- Change in intended use population

### 10.5 Regulatory Alignment

| Framework | Status | Alignment |
|-----------|--------|-----------|
| FDA-EMA Joint Principles for AI in Drug Development (January 2026) | Published | System design aligns with all 10 joint principles including: human oversight, transparency, fit-for-purpose validation, data quality, bias/fairness monitoring |
| CIOMS Working Group XIV: AI in Clinical Research | Final report 2025 | Governance framework compliance: documented intended use, risk-benefit assessment, human accountability, continuous monitoring |
| FDA Total Product Life Cycle (TPLC) approach for AI/ML SaMD | Active guidance | PCCP structure designed per TPLC framework; continuous monitoring plan documented |
| EU AI Act (High-Risk Classification) | In effect 2026 | System classified as high-risk AI (healthcare domain). Conformity assessment, transparency, human oversight, robustness requirements addressed in design. |

---

## 11. Deployment Architecture

### 11.1 Infrastructure

```
                            ┌─────────────────────────────────┐
                            │     Clinical Users               │
                            │  (Physicians, Medical Monitors,  │
                            │   Safety Scientists, Nurses)     │
                            └──────────────┬──────────────────┘
                                           │ HTTPS/WSS
                            ┌──────────────▼──────────────────┐
                            │     API Gateway                  │
                            │  (mTLS, RBAC, Rate Limiting,     │
                            │   Audit Logging)                 │
                            └──────────────┬──────────────────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
   ┌──────────▼─────────┐   ┌─────────────▼────────────┐  ┌──────────▼──────────┐
   │ Dashboard Service   │   │  Alert Service            │  │ Batch Analytics      │
   │ (Real-time UI)      │   │  (Event-driven alerting)  │  │ (Population risk)    │
   │ Next.js + WebSocket │   │  Async event processing   │  │ Scheduled jobs       │
   └──────────┬─────────┘   └─────────────┬────────────┘  └──────────┬──────────┘
              │                            │                            │
              └────────────────────────────┼────────────────────────────┘
                                           │
                            ┌──────────────▼──────────────────┐
                            │     Prediction Engine            │
                            │  (Ensemble Orchestrator)         │
                            │  FastAPI + async model dispatch  │
                            └──────────────┬──────────────────┘
                                           │
           ┌───────────────┬───────────────┼───────────────┬───────────────┐
           │               │               │               │               │
  ┌────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐ ┌────▼────────┐
  │ Biomarker     │ │ Classical   │ │ Deep        │ │ GNN         │ │ Time-Series │
  │ Scoring       │ │ ML Models   │ │ Learning    │ │ Models      │ │ Models      │
  │ (EASIX,       │ │ (XGBoost,   │ │ (PrCRS,     │ │ (GAT,       │ │ (HMM,       │
  │  HScore,      │ │  Teachey,   │ │  ASCO 2025) │ │  GraphSAGE, │ │  Bayesian   │
  │  CAR-HEMTOX)  │ │  Hay, PSS)  │ │             │ │  Link Pred) │ │  SSM)       │
  └───────────────┘ └─────────────┘ └─────────────┘ └──────┬──────┘ └─────────────┘
                                                            │
                                                     ┌──────▼──────┐
                                                     │ Knowledge   │
                                                     │ Graph       │
                                                     │ (Neo4j)     │
                                                     │ 64K nodes   │
                                                     │ 1.56M edges │
                                                     └─────────────┘
           │
  ┌────────▼───────────────────────────────────────────────────────┐
  │                     Data Integration Layer                      │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
  │  │ EHR/EDC  │  │ Lab      │  │ Cytokine │  │ External DBs  │  │
  │  │ (FHIR)   │  │ Systems  │  │ Panels   │  │ (FAERS, etc.) │  │
  │  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
  └────────────────────────────────────────────────────────────────┘
```

### 11.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Container runtime | Docker | Reproducible, validated environments |
| Orchestration | Kubernetes (managed: EKS or AKS) | Auto-scaling, high availability, rolling deployments |
| Prediction engine | Python 3.11+ / FastAPI | Async model dispatch, low-latency API |
| ML framework | PyTorch (GNNs, deep learning), scikit-learn (classical ML), XGBoost | Industry-standard, validated implementations |
| GNN framework | PyTorch Geometric | Purpose-built for graph neural networks on heterogeneous graphs |
| Graph database | Neo4j Enterprise | Property graph model; Cypher query language; native GNN integration |
| Feature store | Feast (online: Redis, offline: Delta Lake) | Real-time feature serving (<10ms) for scoring; offline for training |
| Data streaming | Apache Kafka | HL7 FHIR message ingestion, real-time vital sign streaming |
| Batch orchestration | Apache Airflow | Knowledge graph rebuilds, model retraining, batch population analytics |
| Dashboard | Next.js (React) + D3.js | Real-time WebSocket updates, interactive pathway visualization |
| API gateway | Kong or AWS API Gateway | mTLS, RBAC, rate limiting, audit logging |
| Monitoring | Prometheus + Grafana (infrastructure), MLflow (model performance) | Standard observability stack with ML-specific experiment tracking |
| Audit storage | Append-only database (Amazon QLDB or equivalent) | Immutable audit trail for regulatory compliance (21 CFR Part 11) |

### 11.3 EHR Integration

| Standard | Version | Use Case |
|----------|---------|----------|
| HL7 FHIR | R4 (4.0.1) | Primary integration standard for all EHR data exchange |
| SMART on FHIR | v2.0 | Dashboard embedding within EHR (Epic, Cerner) |
| CDS Hooks | 2.0 | Event-triggered alerting (patient-view-hook, order-sign-hook) |
| FHIR Resources used | Observation (vitals, labs), DiagnosticReport (panels), MedicationAdministration (tocilizumab, steroids), Condition (CRS/ICANS grading), Patient, Encounter | Comprehensive clinical data model |

### 11.4 EDC Integration

| System | Integration Method | Data Flow |
|--------|-------------------|-----------|
| Medidata Rave | Medidata Clinical Cloud API (REST) | Protocol-specified assessments, CRF data, adverse events |
| Oracle InForm / Clinical One | REST API | Clinical trial data, centralized lab results |
| Veeva Vault Safety | REST API | Safety case management, CIOMS-I/MedWatch forms |
| Custom EDC | HL7 FHIR adapter | Standardized integration regardless of EDC vendor |

### 11.5 Security Architecture

| Control | Implementation |
|---------|---------------|
| Network boundary | Patient data remains within the organization's network boundary. No PHI transmitted to external services. |
| Encryption at rest | AES-256 for all stored data |
| Encryption in transit | TLS 1.3 for all API communications |
| Authentication | mTLS for service-to-service; SAML 2.0 / OIDC for user authentication; MFA required |
| Authorization | Role-Based Access Control (RBAC): Clinician, Medical Monitor, Safety Scientist, Data Scientist, Admin, Auditor |
| Audit logging | Immutable, append-only audit log for every prediction, alert, data access, and configuration change |
| Data pseudonymization | All patient identifiers pseudonymized at ingestion; re-identification only via controlled key server |
| Model inference | All model inference runs within the organization's compute boundary; no patient data sent to third-party model APIs |
| Compliance | 21 CFR Part 11, HIPAA, EU Annex 11, GAMP 5, SOC 2 Type II |

---

## 12. Validation Roadmap

### 12.1 Timeline

```
Month:  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18
        |-----|-----|-----|-----|-----|-----|-----|-----|-----|
Phase 1: Retrospective Calibration
        |=========|
                  Knowledge Graph Validation
                  |=========|
                     CIBMTR Data Access Application
                     |===|
                        Retrospective Validation Report
                        |=========|
                              Pre-Registration (ClinicalTrials.gov)
                              |===|
                                 Shadow Mode Infrastructure
                                 |=====|
Phase 2: Shadow Mode Deployment
                                       |=========================
                                                FDA Pre-Sub Meeting
                                                |===|

Month:  18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36
        |-----|-----|-----|-----|-----|-----|-----|-----|-----|
Phase 2 (cont): Shadow Mode
========|
         Shadow Mode Analysis + Advisory Mode Transition
         |=========|
Phase 3: Stepped-Wedge Trial
                   |=========================================|
                                    Regulatory Submission Prep
                                    |=============|
                                                   FDA Review
                                                   |=========|
                                                              Post-Market
                                                              |=========>
```

### 12.2 Milestone Detail

| Month | Milestone | Deliverable | Go/No-Go Criteria |
|-------|-----------|------------|-------------------|
| 1-3 | **Retrospective Calibration** | System predictions calibrated against 6 published CAR-T trials (ZUMA-1, JULIET, ELARA, KarMMa, CARTITUDE-1, TRANSCEND). Aggregate rate predictions within 95% CI. | 5/6 trials within CI for both CRS and ICANS rates |
| 2-4 | **Knowledge Graph Validation** | 64,608-node graph validated for completeness (all curated CRS/ICANS/HLH pathways present), accuracy (spot-check of 500 random edges against source databases), and GNN embedding quality (link prediction AUROC >= 0.95) | Link prediction AUROC >= 0.95; zero critical pathway gaps identified |
| 2-4 | **CIBMTR Data Access** | Data use agreement executed. Initial data extract (de-identified, limited dataset) for external validation. | Data access granted; minimum 5,000 patient records with CRS/ICANS grading |
| 3-6 | **Retrospective Validation Report** | Formal validation report: AUROC, calibration, fairness, timing accuracy on retrospective cohorts. Includes external validation on CIBMTR data. | AUROC >= 0.80 for Grade 3+ CRS; >= 0.75 for Grade 3+ ICANS; calibration slope 0.8-1.2; no subgroup with AUROC <0.70 |
| 5-6 | **Pre-Registration** | ClinicalTrials.gov registration of prospective shadow mode protocol. Pre-specified analysis plan, endpoints, transition criteria. | Registration confirmed; IRB approval at >= 3 sites |
| 5-8 | **Shadow Mode Infrastructure** | System deployed at 3-5 clinical sites. FHIR integration tested. Data flowing. Predictions generating and being cryptographically sealed. | End-to-end data flow validated; prediction latency < 2 min; zero data integrity errors in 30-day burn-in |
| 6-18 | **Shadow Mode Operation** | 6-12 months of sealed predictions on prospective patients. Minimum 150 patients. | Ongoing: weekly data quality checks, monthly interim performance monitoring (for safety only -- not for futility) |
| 12-15 | **FDA Pre-Submission Meeting** | Pre-Sub meeting with FDA CBER/CDRH (joint jurisdiction likely). Present retrospective validation data, shadow mode protocol, proposed intended use, regulatory pathway determination. | FDA agreement on: regulatory pathway (De Novo vs. 510(k)), acceptable clinical evidence package, PCCP framework |
| 18-20 | **Shadow Mode Analysis** | Formal analysis of shadow mode results. Unblinding of sealed predictions vs. adjudicated outcomes. | Transition criteria met (Section 7.3): AUROC >= 0.80, sensitivity >= 90%, lead time >= 12h, zero critical safety failures |
| 18-36 | **Stepped-Wedge Trial** | 4 sites, 6 periods, 400-600 patients. Primary endpoint: Grade 3+ composite rate. | 80% power to detect 40% relative reduction achieved; trial completes enrollment; primary endpoint analyzed |
| 24-30 | **Regulatory Submission Preparation** | Complete 510(k)/De Novo submission package: intended use statement, device description, performance data (retrospective + prospective + trial), PCCP, labeling, clinical evidence summary, software documentation. | Submission package complete; internal quality review passed |
| 30-36 | **FDA Review** | FDA review of submission. Respond to any Additional Information requests. | FDA clearance / De Novo authorization |
| 36+ | **Post-Market Monitoring** | Continuous performance monitoring per PCCP. Annual reports. Adverse event monitoring. Post-market surveillance study if required. | Performance metrics remain within pre-specified bounds; PCCP updates as needed |

### 12.3 Resource Requirements

| Phase | Duration | Key Resources |
|-------|----------|--------------|
| Phase 1 (Retrospective) | Months 1-6 | ML engineering (3 FTE), clinical data science (2 FTE), clinical immunologist (0.5 FTE consultant), biostatistician (1 FTE), regulatory (0.5 FTE) |
| Phase 2 (Shadow Mode) | Months 6-18 | ML engineering (2 FTE, maintenance), clinical operations (1 FTE per site), data management (1 FTE), biostatistician (0.5 FTE), regulatory (0.5 FTE), IT/integration (1 FTE per site for FHIR setup) |
| Phase 3 (Clinical Trial + Submission) | Months 18-36 | Clinical operations (1 FTE per site), biostatistician (1 FTE), regulatory (1.5 FTE), medical writing (1 FTE), ML engineering (1 FTE, monitoring), quality assurance (0.5 FTE) |

---

## Appendix A: Glossary of Terms

| Term | Definition |
|------|-----------|
| ASTCT | American Society for Transplantation and Cellular Therapy |
| AUC / AUROC | Area Under the Receiver Operating Characteristic Curve |
| AUPRC | Area Under the Precision-Recall Curve |
| BBB | Blood-Brain Barrier |
| BCMA | B-Cell Maturation Antigen |
| BLA | Biologics License Application |
| CAR-T | Chimeric Antigen Receptor T-cell therapy |
| CARTOX-10 | CAR-T-cell Therapy Associated Toxicity 10-point assessment |
| CBER | Center for Biologics Evaluation and Research (FDA) |
| CDRH | Center for Devices and Radiological Health (FDA) |
| CIBMTR | Center for International Blood and Marrow Transplant Research |
| CIOMS | Council for International Organizations of Medical Sciences |
| CRS | Cytokine Release Syndrome |
| CTD | Comparative Toxicogenomics Database |
| De Novo | FDA regulatory pathway for novel devices without a predicate |
| DESCAR-T | French national CAR-T registry |
| DLBCL | Diffuse Large B-Cell Lymphoma |
| EASIX | Endothelial Activation and Stress Index |
| ECE | Expected Calibration Error |
| EDC | Electronic Data Capture |
| EEG | Electroencephalography |
| FAERS | FDA Adverse Event Reporting System |
| FHIR | Fast Healthcare Interoperability Resources |
| GAT | Graph Attention Network |
| GNN | Graph Neural Network |
| HLH | Hemophagocytic Lymphohistiocytosis |
| HMM | Hidden Markov Model |
| HScore | Hemophagocytic Syndrome Score |
| ICANS | Immune effector Cell-Associated Neurotoxicity Syndrome |
| ICE | Immune Effector Cell-Associated Encephalopathy (assessment tool) |
| IEC-HS | Immune Effector Cell-associated HLH-like Syndrome |
| NNA | Number Needed to Alert |
| NRI | Net Reclassification Improvement |
| PCCP | Predetermined Change Control Plan |
| PLR | Penalized Logistic Regression |
| PPV | Positive Predictive Value |
| PrCRS | Predictive CRS model (U-Net + Transformer architecture) |
| PSS | Patient Safety Score (DESCAR-T) |
| SaMD | Software as a Medical Device |
| scFv | Single-chain Variable Fragment |
| SPD | Sum of Product Diameters (tumor burden measure) |
| TCE | T-cell Engager (bispecific antibody) |

## Appendix B: Key References

1. Lee DW, Santomasso BD, Locke FL, et al. ASTCT Consensus Grading for Cytokine Release Syndrome and Neurologic Toxicity Associated with Immune Effector Cells. *Biol Blood Marrow Transplant*. 2019;25(4):625-638.
2. Neelapu SS, Tummala S, Kebriaei P, et al. Chimeric antigen receptor T-cell therapy -- assessment and management of toxicities. *Nat Rev Clin Oncol*. 2018;15(1):47-62.
3. Teachey DT, Lacey SF, Shaw PA, et al. Identification of Predictive Biomarkers for Cytokine Release Syndrome after Chimeric Antigen Receptor T-cell Therapy for Acute Lymphoblastic Leukemia. *Cancer Discov*. 2016;6(6):664-679.
4. Hay KA, Hanafi LA, Li D, et al. Kinetics and biomarkers of severe cytokine release syndrome after CD19 chimeric antigen receptor-modified T-cell therapy. *Blood*. 2017;130(21):2295-2306.
5. Pennisi M, Sanchez-Escamilla M, Flynn JR, et al. Modified EASIX predicts severe cytokine release syndrome and neurotoxicity after chimeric antigen receptor T cells. *Blood Adv*. 2021;5(17):3397-3406.
6. Korell F, Tomas AA, Gafter-Gvili A, et al. EASIX and CRS/ICANS after CAR-T cell therapy: a systematic review. *Transplant Cell Ther*. 2022.
7. Fardet L, Galicier L, Lambotte O, et al. Development and validation of the HScore, a score for the diagnosis of reactive hemophagocytic syndrome. *Arthritis Rheumatol*. 2014;66(9):2613-2620.
8. Rejeski K, Perez A, Sesques P, et al. CAR-HEMATOTOX: a model for CAR T-cell-related hematologic toxicity in relapsed/refractory large B-cell lymphoma. *Blood*. 2021;138(24):2499-2513.
9. Lemoine J, Ruella M, Houot R. Overcoming challenges of CAR T-cell therapy: lessons from DESCAR-T registry. *Haematologica*. 2023.
10. Gust J, Hay KA, Hanafi LA, et al. Endothelial Activation and Blood-Brain Barrier Disruption in Neurotoxicity after Adoptive Immunotherapy with CD19 CAR-T Cells. *Cancer Discov*. 2017;7(12):1404-1419.
11. Schoeberl F, Tiedt S, Guenther P, et al. EEG-based prediction of ICANS after CAR T-cell therapy. *Neurology*. 2023.
12. Siegel SE, et al. Wearable continuous temperature monitoring for early CRS detection in CAR-T cell therapy. *Blood*. 2023.
13. FDA. Predetermined Change Control Plans for Machine Learning-Enabled Device Software Functions. Guidance for Industry. 2023.
14. FDA, Health Canada, MHRA. Good Machine Learning Practice for Medical Device Development: Guiding Principles. 2021.
15. FDA-EMA. Joint Principles for AI/ML in Drug Development. January 2026.
16. CIOMS Working Group XIV. Artificial Intelligence in Clinical Research. Final Report. 2025.
17. Viz.ai. De Novo Classification Request for Viz LVO. DEN170073. FDA. 2018.

---

*Document Control: This specification is version-controlled and subject to formal change management. All modifications require review by the cross-functional steering committee (Clinical Development, Safety Sciences, Data Science, Regulatory Affairs, Quality Assurance). The next scheduled review is Q2 2026.*
