# Predictive Safety Platform Technical Specification

## Document Control
- **Version**: 0.1.0 (Draft)
- **Status**: Research & Design Phase
- **Last Updated**: 2026-02-06

---

## 1. System Overview

The Predictive Safety Platform is an AI-enabled clinical safety system that transforms pharmacovigilance from reactive event characterization to proactive risk prediction. The system integrates multi-modal patient data through a three-layer engine to produce mechanistic, interpretable safety predictions.

### 1.1 Primary Objectives

| Objective | Description | Success Metric |
|-----------|-------------|----------------|
| Population Risk Profiling | Define population-level safety indices for portfolio investment decisions | Calibrated risk estimates within 15% of observed rates |
| Patient Risk Scoring | Predict individual patient risk at screening and during treatment | AUROC > 0.80 for Grade 3+ CRS prediction |
| Mechanistic Reasoning | Ground predictions in biological pathways, not just statistical correlation | >80% of predictions trace to known mechanistic pathways |
| Clinical Integration | Deliver predictions into existing clinical workflows | <5 min latency for real-time risk updates |
| Regulatory Readiness | Produce audit-grade explanations suitable for regulatory submissions | Pass independent validation audit |

### 1.2 Scope

**In Scope (Stage 1)**:
- CRS (Cytokine Release Syndrome) prediction for CAR-T therapies
- ICANS (Immune effector Cell-Associated Neurotoxicity Syndrome)
- IEC-HS/HLH (Hemophagocytic Lymphohistiocytosis)
- 3 retrospective clinical studies for model development
- Study-A trial data integration pathway

**Future Scope (Stage 2-3)**:
- TCE (T-cell Engager) safety prediction
- Checkpoint inhibitor immune-related AEs
- Cross-TA expansion (oncology, immunology, rare diseases)
- Real-time prospective deployment
- Study-B trial integration

---

## 2. Architecture

### 2.1 Three-Layer Engine

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 3: OPERATIONAL INTEGRATION          │
│  ┌──────────┐ ┌──────────────┐ ┌───────────┐ ┌───────────┐ │
│  │Dashboard │ │ Alert Engine │ │Audit Trail│ │Reg Reports│ │
│  └────┬─────┘ └──────┬───────┘ └─────┬─────┘ └─────┬─────┘ │
├───────┴──────────────┴───────────────┴───────────────┴──────┤
│                    LAYER 2: AGENTIC SCIENTIFIC REASONING     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │  Hypothesis   │ │  Mechanistic │ │  Graph Network       │ │
│  │  Generation   │ │  Validation  │ │  Memory (KG)         │ │
│  └───────┬──────┘ └──────┬───────┘ └──────────┬───────────┘ │
├──────────┴───────────────┴────────────────────┴─────────────┤
│                    LAYER 1: MODEL ORCHESTRATION              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │  Claude   │ │   GPT    │ │  Gemini  │ │   Ensemble     │ │
│  │  Opus 4.5 │ │   5.2    │ │    3     │ │   Aggregator   │ │
│  └──────┬───┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘ │
├─────────┴──────────┴────────────┴────────────────┴──────────┤
│                    DATA LAYER                                │
│  ┌─────────┐ ┌──────┐ ┌──────┐ ┌───────┐ ┌──────┐ ┌─────┐ │
│  │Clinical │ │ Labs │ │Genomic│ │Imaging│ │ EHR  │ │Lit. │ │
│  │ Trials  │ │      │ │       │ │       │ │      │ │     │ │
│  └─────────┘ └──────┘ └──────┘ └───────┘ └──────┘ └─────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Layer 1: Model Orchestration

**Purpose**: Normalize, route, and combine predictions from multiple foundation models.

**Components**:

#### 2.2.1 Prompt Router
Routes clinical queries to the most appropriate model based on:
- Query complexity and domain specificity
- Model capability benchmarks (maintained via eval framework)
- Latency requirements (real-time monitoring vs. batch analysis)
- Cost optimization (tiered routing: fast/cheap for screening, thorough for alerts)

```python
class PromptRouter:
    """Routes clinical safety queries to optimal model endpoints."""

    def route(self, query: SafetyQuery) -> ModelEndpoint:
        # Complexity scoring
        complexity = self.assess_complexity(query)

        # Domain matching
        domain_scores = {
            model: self.domain_benchmark(model, query.domain)
            for model in self.available_models
        }

        # Latency-aware selection
        if query.urgency == Urgency.REALTIME:
            candidates = self.filter_by_latency(domain_scores, max_ms=2000)
        else:
            candidates = domain_scores

        return self.select_optimal(candidates, complexity, query.cost_tier)
```

#### 2.2.2 Response Normalizer
Transforms heterogeneous model outputs into a standardized prediction format:

```python
@dataclass
class SafetyPrediction:
    """Standardized prediction output from any foundation model."""
    risk_score: float              # 0.0 - 1.0 calibrated probability
    confidence: float              # Model confidence in the prediction
    severity_distribution: dict    # {grade_1: p, grade_2: p, grade_3: p, ...}
    time_horizon: TimeDelta        # Predicted time to onset
    mechanistic_rationale: str     # Natural language explanation
    pathway_references: list[str]  # Knowledge graph node IDs
    evidence_sources: list[str]    # Data points that drove the prediction
    model_id: str                  # Which model produced this
    latency_ms: int                # Response time
    token_usage: TokenCount        # Cost tracking
```

#### 2.2.3 Ensemble Aggregator
Combines predictions from multiple models:

- **Weighted averaging**: Model weights derived from eval performance on safety benchmarks
- **Confidence calibration**: Platt scaling on held-out validation set
- **Disagreement detection**: Flags cases where models substantially disagree for human review
- **Uncertainty quantification**: Produces calibrated confidence intervals, not just point estimates

```python
class EnsembleAggregator:
    """Combines multi-model predictions with calibrated uncertainty."""

    def aggregate(self, predictions: list[SafetyPrediction]) -> AggregatedRisk:
        # Weight by model eval performance
        weights = self.get_model_weights(predictions)

        # Detect disagreement
        if self.disagreement_score(predictions) > self.threshold:
            return AggregatedRisk(
                requires_human_review=True,
                disagreement_analysis=self.analyze_disagreement(predictions)
            )

        # Calibrated ensemble
        ensemble_score = self.weighted_average(predictions, weights)
        calibrated = self.platt_calibrate(ensemble_score)

        # Uncertainty from model spread
        ci = self.confidence_interval(predictions, weights)

        return AggregatedRisk(
            risk_score=calibrated,
            confidence_interval=ci,
            contributing_models=self.attribution(predictions, weights)
        )
```

#### 2.2.4 API Security Gateway
All model calls pass through secured API boundaries:

- **Authentication**: mTLS with organization-issued certificates
- **Data classification**: Patient data never leaves the organization's network boundary
- **Prompt sanitization**: Strips PII before foundation model calls where possible
- **Audit logging**: Every API call logged with full request/response for regulatory audit
- **Rate limiting**: Per-model and per-trial rate limits
- **Failover**: Automatic fallback to secondary model if primary is unavailable

### 2.3 Layer 2: Agentic Scientific Reasoning

**Purpose**: Generate and validate mechanistic hypotheses about safety risk.

#### 2.3.1 Graph Network Memory

The knowledge graph is the institutional memory of the platform — encoding known biological mechanisms, validated hypotheses, and observed relationships.

**Schema**:
```
Nodes:
  - Gene (symbol, expression_level, variants)
  - Protein (name, function, interaction_partners)
  - Cytokine (name, normal_range, cascade_position)
  - Receptor (name, cell_types, signaling_pathway)
  - Cell_Type (name, lineage, activation_markers)
  - Pathway (name, components, trigger_conditions)
  - Adverse_Event (MedDRA_term, severity_grades, onset_timing)
  - Drug (name, target, mechanism_of_action)
  - Patient_Cohort (trial_id, characteristics, outcomes)
  - Biomarker (name, measurement_type, prognostic_value)

Edges:
  - ACTIVATES (Protein -> Pathway, weight, evidence_count)
  - PRODUCES (Cell_Type -> Cytokine, conditions, rate)
  - TRIGGERS (Cytokine -> Adverse_Event, threshold, time_to_onset)
  - INHIBITS (Drug -> Protein, IC50, selectivity)
  - EXPRESSES (Cell_Type -> Receptor, level)
  - CORRELATES_WITH (Biomarker -> Adverse_Event, correlation, p_value)
  - PREDICTS (Biomarker -> Risk_Level, AUROC, validation_source)
  - CASCADES_TO (Cytokine -> Cytokine, amplification_factor, delay)
  - VARIANT_AFFECTS (Gene -> Protein, effect_type, penetrance)
```

**CRS Mechanism Example**:
```
CAR-T_Cell -[ACTIVATES]-> T_Cell_Expansion
T_Cell_Expansion -[PRODUCES]-> IFN-gamma
IFN-gamma -[ACTIVATES]-> Macrophage_Activation
Macrophage_Activation -[PRODUCES]-> IL-6
IL-6 -[BINDS]-> sIL-6R (trans-signaling)
IL-6/sIL-6R -[ACTIVATES]-> Endothelial_Activation
Endothelial_Activation -[PRODUCES]-> IL-6 (amplification loop)
Endothelial_Activation -[TRIGGERS]-> Vascular_Leak
Vascular_Leak + Cytokine_Storm -[MANIFESTS_AS]-> CRS_Grade_3+

Intervention point: Tocilizumab -[INHIBITS]-> IL-6R
```

**Graph Database**: Neo4j Enterprise (or Amazon Neptune for cloud deployment)
- Property graph model (not RDF — clinical teams need intuitive schema)
- Cypher queries for pathway traversal
- Graph Neural Network embeddings for similarity and prediction
- Versioned graph snapshots for reproducibility

#### 2.3.2 Hypothesis Generator

An agentic system that formulates testable safety hypotheses:

```python
class HypothesisGenerator:
    """Generates mechanistic safety hypotheses using KG + foundation models."""

    async def generate(self, context: PatientContext) -> list[Hypothesis]:
        # 1. Query knowledge graph for relevant pathways
        pathways = self.kg.find_relevant_pathways(
            drug=context.treatment,
            patient_features=context.features,
            known_risks=context.existing_risk_factors
        )

        # 2. Use foundation model to reason about patient-specific risk
        reasoning_prompt = self.build_reasoning_prompt(
            patient=context,
            pathways=pathways,
            similar_cases=self.kg.find_similar_patients(context)
        )

        model_reasoning = await self.orchestrator.query(
            reasoning_prompt,
            model_preference="high_reasoning"  # Route to strongest reasoner
        )

        # 3. Extract structured hypotheses
        hypotheses = self.extract_hypotheses(model_reasoning)

        # 4. Validate against known mechanisms
        validated = []
        for h in hypotheses:
            h.mechanistic_support = self.kg.validate_mechanism(h.pathway)
            h.evidence_strength = self.assess_evidence(h)
            validated.append(h)

        return sorted(validated, key=lambda h: h.risk_score, reverse=True)
```

#### 2.3.3 Mechanistic Validator

Ensures predictions are grounded in biology, not just statistical artifacts:

- **Pathway consistency**: Does the predicted mechanism follow known signaling cascades?
- **Temporal plausibility**: Is the predicted onset timing consistent with pathway kinetics?
- **Dose-response coherence**: Does the risk scale appropriately with relevant biomarkers?
- **Cross-validation**: Does the mechanism explain observations in related therapies?

### 2.4 Layer 3: Operational Integration

**Purpose**: Deliver predictions to clinical workflows in interpretable, actionable form.

#### 2.4.1 Clinical Dashboard

**Design Requirements**:
- Real-time patient risk display (updated as new data arrives)
- Risk trajectory visualization (how risk evolves over treatment course)
- Mechanistic drill-down (click a risk score → see the predicted pathway)
- Population heatmap (trial-wide risk landscape)
- Alert management (configurable thresholds, escalation paths)

**Dashboard Views**:

1. **Trial Overview**: All patients, color-coded by current risk level
2. **Patient Detail**: Individual risk trajectory, contributing factors, recommendations
3. **Mechanism Explorer**: Interactive pathway visualization showing predicted cascade
4. **Comparison View**: This patient vs. similar historical patients
5. **Audit View**: Prediction history, accuracy tracking, model performance

#### 2.4.2 Alert Engine

```python
class AlertEngine:
    """Real-time safety alert generation and routing."""

    alert_levels = {
        AlertLevel.INFO: "Risk score updated, within normal range",
        AlertLevel.WATCH: "Risk elevated above baseline, enhanced monitoring recommended",
        AlertLevel.WARNING: "Significant risk increase, clinical review recommended",
        AlertLevel.CRITICAL: "High risk of imminent Grade 3+ event, immediate action"
    }

    def evaluate(self, patient: Patient, prediction: AggregatedRisk) -> Alert | None:
        # Check absolute risk threshold
        if prediction.risk_score > self.critical_threshold:
            return self.create_alert(AlertLevel.CRITICAL, patient, prediction)

        # Check rate of change (risk acceleration)
        trajectory = self.get_trajectory(patient)
        if trajectory.acceleration > self.accel_threshold:
            return self.create_alert(AlertLevel.WARNING, patient, prediction)

        # Check mechanistic triggers (specific pathway activation markers)
        if self.mechanistic_triggers_met(patient, prediction):
            return self.create_alert(AlertLevel.WATCH, patient, prediction)

        return None
```

#### 2.4.3 Regulatory Audit Trail

Every prediction must be reproducible and explainable:

```python
@dataclass
class AuditRecord:
    """Complete audit trail for a single prediction."""
    prediction_id: str
    timestamp: datetime
    patient_id: str  # Pseudonymized

    # Input state
    input_features: dict          # All data that went into the prediction
    graph_snapshot_version: str   # KG version used
    model_versions: dict          # {model_name: version}

    # Processing trace
    prompt_router_decision: dict  # Why this model was selected
    raw_model_outputs: list       # Unprocessed model responses
    ensemble_weights: dict        # How models were combined
    calibration_params: dict      # Platt scaling parameters

    # Output
    final_prediction: AggregatedRisk
    mechanistic_explanation: str
    pathway_trace: list[str]      # Graph traversal path

    # Validation
    confidence_interval: tuple
    disagreement_score: float
    similar_historical_outcomes: list
```

---

## 3. Data Architecture

### 3.1 Data Sources and Integration

| Source | Data Type | Volume | Latency | Integration |
|--------|-----------|--------|---------|-------------|
| Clinical Trial DB | Demographics, dosing, outcomes | ~10K patients | Batch (daily) | Direct ETL |
| Lab Systems | Cytokine panels, CBC, chemistry | ~100K results/study | Near real-time | HL7/FHIR |
| Genomics | WES/WGS, gene expression | ~5K patients | Batch | VCF/BAM pipeline |
| Imaging | CT, MRI, PET | ~50K images | Batch | DICOM integration |
| EHR | Clinical notes, medications, vitals | Variable | Near real-time | FHIR API |
| Literature | PubMed, case reports | Continuous | Batch (weekly) | NLP pipeline |
| FAERS/EudraVigilance | Spontaneous reports | Continuous | Batch (monthly) | Structured download |
| Knowledge Graph | Mechanisms, pathways | Continuous | Real-time | Direct write |

### 3.2 Data Pipeline

```
Raw Sources → Ingestion → Normalization → Feature Store → Model Input
                                              ↓
                                        Knowledge Graph ← Literature NLP
                                              ↓
                                      Graph Embeddings → Model Input
```

**Key Pipeline Components**:

1. **Ingestion Layer**: Apache Kafka for streaming, Airflow for batch orchestration
2. **Normalization**:
   - Medical coding: MedDRA for AEs, WHO-DD for drugs, LOINC for labs
   - Unit standardization: SI units, reference range normalization
   - Temporal alignment: All data on a common patient timeline
3. **Feature Store**:
   - Patient-level features (demographics, baseline labs, genomic risk scores)
   - Time-series features (cytokine kinetics, treatment response curves)
   - Graph features (pathway activation scores, node centrality)
4. **Privacy Layer**:
   - Pseudonymization at ingestion
   - Differential privacy for aggregate statistics
   - Data minimization: only features relevant to prediction retained
   - Access control: role-based, need-to-know

### 3.3 Feature Engineering

**Baseline Features** (available at screening):
- Demographics (age, sex, BMI, race/ethnicity)
- Disease characteristics (tumor burden, disease stage, prior lines)
- Baseline labs (CRP, ferritin, IL-6, LDH, fibrinogen)
- Genomic risk variants (HLA type, cytokine gene polymorphisms)
- Treatment parameters (CAR-T product, dose, bridging therapy)
- Comorbidities (cardiovascular, renal, hepatic function)

**Longitudinal Features** (available during treatment):
- Cytokine kinetics (IL-6, IFN-gamma, TNF-alpha, IL-10 time series)
- CAR-T expansion kinetics (flow cytometry, qPCR)
- Vital sign trajectories (temperature, blood pressure, heart rate)
- Lab trajectories (CRP, ferritin, coagulation markers)
- Clinical observations (neurotoxicity assessments, ICE scores)

**Graph-Derived Features**:
- Pathway activation scores (based on observed biomarker patterns)
- Mechanistic similarity to known high-risk profiles
- Drug-target-pathway connectivity scores
- Literature recency weights (newer evidence weighted higher)

---

## 4. Model Architecture

### 4.1 Foundation Model Layer

**Multi-model approach** — no single model dependency:

| Model | Role | Strength | Access |
|-------|------|----------|--------|
| Claude Opus | Primary reasoning, mechanistic analysis | Long-context, nuanced reasoning | Enterprise API |
| GPT-5 | Pattern recognition, large-scale feature analysis | Broad training data | Enterprise API |
| Gemini | Multi-modal integration, structured output | Native multi-modal | Enterprise API |

**Prompt Engineering Strategy**:
- Domain-specific system prompts encoding pharmacovigilance expertise
- Few-shot examples from validated case studies
- Structured output schemas for consistent parsing
- Chain-of-thought reasoning for mechanistic explanations
- Tool use: models can query the knowledge graph during reasoning

### 4.2 Custom Model Components

Beyond foundation model inference, specialized trained models:

#### 4.2.1 Cytokine Trajectory Predictor
- **Architecture**: Temporal Transformer (attention over time-series lab values)
- **Input**: First 24h cytokine panel + baseline features
- **Output**: Predicted cytokine trajectory for next 7 days
- **Training**: Retrospective CAR-T study data
- **Purpose**: Early warning of cytokine storm trajectory

#### 4.2.2 Graph Neural Network Risk Scorer
- **Architecture**: Graph Attention Network (GAT) over knowledge graph
- **Input**: Patient feature vector + graph neighborhood
- **Output**: Risk score grounded in graph topology
- **Training**: Patient outcomes mapped to graph substructures
- **Purpose**: Ensures predictions are mechanistically consistent

#### 4.2.3 Survival Analysis Model
- **Architecture**: DeepSurv (Cox proportional hazards with neural network)
- **Input**: Baseline + longitudinal features
- **Output**: Time-to-event probability curves for each AE type
- **Training**: Retrospective clinical data with right-censoring
- **Purpose**: Quantifies not just if but when events occur

### 4.3 Ensemble Strategy

```
Foundation Model Predictions ─┐
Custom Model Predictions ─────┼──→ Ensemble Layer ──→ Calibrated Risk Score
Graph-Based Risk Scores ──────┘         │
                                         ↓
                                  Disagreement Check
                                  Uncertainty Quantification
                                  Mechanistic Consistency Validation
```

**Ensemble Method**: Stacking with logistic regression meta-learner
- Base models produce calibrated probabilities
- Meta-learner learns optimal combination weights
- Weights updated monthly from prospective validation data
- Fallback: Simple average if meta-learner has insufficient calibration data

---

## 5. Safety Index

### 5.1 Definition

The **Safety Index** is the primary output — a composite score that converts diverse data into a single interpretable metric with mechanistic backing.

```python
@dataclass
class SafetyIndex:
    """The core platform output for a patient at a point in time."""

    # Composite risk
    overall_risk: float           # 0.0 - 1.0, calibrated probability of any Grade 2+ event

    # Event-specific risks
    crs_risk: EventRisk           # CRS-specific prediction
    icans_risk: EventRisk         # ICANS-specific prediction
    hlh_risk: EventRisk           # HLH-specific prediction

    # Temporal component
    risk_trajectory: list[float]  # Predicted risk at t+1h, t+4h, t+12h, t+24h, t+48h, t+72h
    peak_risk_time: timedelta     # When is risk predicted to peak

    # Mechanistic grounding
    primary_mechanism: str         # Dominant predicted pathway
    contributing_pathways: list    # All pathways contributing to risk
    key_biomarkers: list           # Top 5 features driving the prediction

    # Confidence and uncertainty
    confidence_interval: tuple     # 95% CI around overall_risk
    model_agreement: float         # How much do the models agree (0-1)
    evidence_strength: str         # "strong" / "moderate" / "limited"

    # Clinical recommendation
    monitoring_protocol: str       # Suggested monitoring frequency
    intervention_readiness: str    # Suggested intervention staging

    # Audit
    prediction_id: str
    timestamp: datetime
    model_versions: dict
    graph_version: str


@dataclass
class EventRisk:
    """Risk assessment for a specific adverse event type."""
    probability: float             # Calibrated probability
    severity_distribution: dict    # {grade_1: p, grade_2: p, grade_3: p, grade_4: p}
    expected_onset: timedelta      # Predicted time to onset
    onset_ci: tuple                # 95% CI for onset timing
    mechanistic_path: list[str]    # Predicted cascade sequence
```

### 5.2 Population-Level Safety Index

Aggregates individual patient indices across a trial or portfolio:

```python
@dataclass
class PopulationSafetyIndex:
    """Population-level risk assessment for a trial or molecule."""

    overall_rate: float            # Expected event rate
    rate_ci: tuple                 # 95% CI
    severity_distribution: dict    # Expected grade distribution

    high_risk_fraction: float      # % of population above risk threshold
    risk_distribution: dict        # Histogram of patient risk scores

    # Comparisons
    vs_historical: float           # Relative risk vs. historical data
    vs_comparator: float           # If available, vs. active comparator

    # Portfolio value
    hold_probability: float        # Estimated probability of clinical hold
    expected_hold_duration: int    # Days, if hold occurs
    risk_mitigation_impact: float  # Expected reduction with platform-guided monitoring
```

---

## 6. Evaluation Framework

### 6.1 Custom Evaluation Suite

The platform requires domain-specific evaluations, not generic ML benchmarks.

**Evaluation Dimensions**:

| Dimension | Metric | Target | Method |
|-----------|--------|--------|--------|
| Discrimination | AUROC for Grade 3+ events | >0.80 | Retrospective validation |
| Calibration | Brier score, calibration plots | <0.15 | Probability vs. observed |
| Timing Accuracy | MAE for onset prediction | <12 hours | Predicted vs. actual onset |
| Mechanistic Validity | Expert agreement on pathway | >80% | Clinical expert review |
| Sensitivity | True positive rate at 90% specificity | >0.70 | ROC analysis |
| Specificity | True negative rate at 80% sensitivity | >0.65 | ROC analysis |
| Clinical Utility | Net reclassification improvement | >0 (positive) | NRI analysis |
| Fairness | Equalized odds across demographics | <5% disparity | Subgroup analysis |

### 6.2 Evaluation Protocol

**Retrospective Validation (Stage 1)**:
1. Train on Study A + Study B (known outcomes)
2. Validate on Study C (held out, known outcomes)
3. Compare predictions to actual events
4. Expert review of mechanistic explanations
5. Calibration assessment across risk strata

**Prospective Validation (Stage 2)**:
1. Deploy predictions in shadow mode (clinicians don't see them)
2. Compare predictions to outcomes in real time
3. Calibrate and adjust
4. Switch to advisory mode (clinicians see predictions, not binding)
5. Measure clinical impact (intervention timing, outcome changes)

### 6.3 Model Monitoring

Continuous monitoring for:
- **Distribution shift**: Patient population characteristics vs. training data
- **Performance degradation**: Rolling AUROC, calibration drift
- **Fairness drift**: Performance parity across demographic groups
- **Knowledge graph staleness**: Are pathway weights still current?

---

## 7. Partnership Integration Model

### 7.1 Design Principles

The platform is designed for automatic capability absorption:

1. **API-First**: All model interactions through versioned APIs. New model versions drop in without re-engineering.
2. **Eval-Driven**: Custom benchmarks targeting safety prediction. When a model improves on the eval, its weight in the ensemble increases automatically.
3. **Roadmap Influence**: Pharmacovigilance needs fed directly to partner product teams. Custom evals guide model improvement.
4. **Interpretability by Design**: Explanations are required output, not optional. Partners must support chain-of-thought and evidence citation.
5. **Failure Transparency**: When models fail or disagree, diagnostic details are available. No black boxes.

### 7.2 Partner Evaluation Criteria

| Criterion | Weight | Assessment Method |
|-----------|--------|-------------------|
| Safety prediction AUROC | 25% | Custom eval suite |
| Mechanistic reasoning quality | 20% | Expert blind review |
| Calibration accuracy | 15% | Brier score comparison |
| Latency | 10% | P50/P95 response time |
| Cost efficiency | 10% | $/prediction at quality threshold |
| Data security posture | 10% | Security audit |
| Roadmap alignment | 10% | Partnership agreement terms |

---

## 8. Security and Compliance

### 8.1 Data Security

- **Network boundary**: Patient data never leaves the organization's network. Foundation models accessed via secure API endpoints within the organization's infrastructure (or approved cloud boundaries).
- **Encryption**: AES-256 at rest, TLS 1.3 in transit
- **Access control**: Role-based with principle of least privilege
- **Audit logging**: Immutable logs for all data access and model calls
- **Data classification**: Automated classification and handling per organizational data policies

### 8.2 Regulatory Compliance

- **GxP Validation**: Platform validated per GAMP 5 / CSV principles
- **21 CFR Part 11**: Electronic records and signatures compliance
- **GDPR/Privacy**: Data minimization, purpose limitation, patient consent management
- **FDA AI Guidance**: Compliant with FDA framework for AI/ML in drug development
- **Model documentation**: Per FDA's guidance on predetermined change control plans

### 8.3 Ethical Considerations

- **Bias monitoring**: Continuous assessment across demographic groups
- **Human oversight**: All critical predictions require clinical review
- **Transparency**: Patients informed that AI assists safety monitoring
- **Right to explanation**: Any prediction can be fully explained in clinical terms
- **Override capability**: Clinicians can always override system recommendations

---

## 9. Implementation Roadmap

### 9.1 Stage 1: Build (Months 1-12)

| Quarter | Deliverables |
|---------|-------------|
| Q1 | Knowledge graph schema, data pipeline design, eval framework definition |
| Q2 | Graph populated with CRS/ICANS mechanisms, first model prototypes |
| Q3 | Retrospective validation on 3 studies, dashboard prototype |
| Q4 | Stage 1 validation report, partnership agreements finalized |

### 9.2 Stage 2: Pilot (Months 13-24)

| Quarter | Deliverables |
|---------|-------------|
| Q5 | Shadow deployment on pilot study trial |
| Q6 | Shadow validation results, calibration update |
| Q7 | Advisory mode deployment, Study-B integration |
| Q8 | Stage 2 validation report, regulatory strategy document |

### 9.3 Stage 3: Scale (Months 25-36+)

| Quarter | Deliverables |
|---------|-------------|
| Q9-Q10 | Cross-TA expansion, TCE safety module |
| Q11-Q12 | Enterprise deployment, regulatory submission support |

---

## 10. Technical Requirements

### 10.1 Infrastructure

| Component | Specification |
|-----------|--------------|
| Compute | GPU cluster (NVIDIA A100/H100) for model inference |
| Graph DB | Neo4j Enterprise, 64GB+ RAM, SSD storage |
| Data Lake | S3/ADLS for raw data, Delta Lake for processed |
| Orchestration | Apache Airflow for batch, Kafka for streaming |
| Dashboard | React/Next.js frontend, WebSocket for real-time |
| API Gateway | Kong/AWS API Gateway with mTLS |
| Monitoring | Prometheus + Grafana for system, custom for ML |
| CI/CD | GitHub Actions, automated eval runs on PR |

### 10.2 Development Environment

- **IDE**: Claude Code / Codex agent harness for development
- **Language**: Python 3.11+ (core engine), TypeScript (dashboard)
- **ML Framework**: PyTorch (custom models), LangChain/LangGraph (agent orchestration)
- **Graph**: Neo4j Python driver, PyTorch Geometric (GNN)
- **Testing**: pytest, model eval framework, integration test suite
- **Documentation**: Sphinx (API docs), MkDocs (user guides)

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| CRS | Cytokine Release Syndrome — systemic inflammatory response to immune cell activation |
| ICANS | Immune effector Cell-Associated Neurotoxicity Syndrome |
| IEC-HS | Immune Effector Cell-associated HLH-like Syndrome |
| HLH | Hemophagocytic Lymphohistiocytosis |
| CAR-T | Chimeric Antigen Receptor T-cell therapy |
| TCE | T-cell Engager (bispecific antibody) |
| CBI | Checkpoint Inhibitor |
| MOA | Mechanism of Action |
| MedDRA | Medical Dictionary for Regulatory Activities |
| FAERS | FDA Adverse Event Reporting System |
| Safety Index | Composite mechanistic risk score |
| KG | Knowledge Graph |
| GNN | Graph Neural Network |

## Appendix B: References

1. Lee DW, et al. ASTCT Consensus Grading for CRS and Neurologic Toxicity. Biol Blood Marrow Transplant. 2019.
2. FDA Guidance: Clinical Pharmacology Considerations for Human Gene Therapy. 2024.
3. FDA Framework for AI/ML-Based Software as Medical Device. 2021.
4. Neelapu SS, et al. CRS after CAR T-cell therapy. Nat Rev Clin Oncol. 2018.
5. Shimabukuro-Vornhagen A, et al. CRS. J Immunother Cancer. 2018.
