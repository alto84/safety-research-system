# Predictive Safety Platform System Architecture

## High-Level Architecture

```
                                    ┌─────────────────────┐
                                    │   Clinical Users     │
                                    │   (Dashboard/API)    │
                                    └──────────┬──────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   API Gateway        │
                                    │   (mTLS, Auth, Audit)│
                                    └──────────┬──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
         ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
         │  Dashboard Service   │   │  Alert Service       │   │  Batch Analytics     │
         │  (Real-time UI)      │   │  (Event Processing)  │   │  (Population Risk)   │
         └──────────┬──────────┘   └──────────┬──────────┘   └──────────┬──────────┘
                    │                          │                          │
                    └──────────────────────────┼──────────────────────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │   SafetyEngine        │
                                    │   (Core Prediction)   │
                                    └──────────┬──────────┘
                                               │
                    ┌──────────────┬────────────┼────────────┬──────────────┐
                    │              │            │            │              │
         ┌──────────▼───┐  ┌──────▼──────┐  ┌──▼──────────┐  ┌───────────▼──┐
         │ Model         │  │ Knowledge   │  │ Feature      │  │ Hypothesis   │
         │ Orchestrator  │  │ Graph       │  │ Store        │  │ Generator    │
         └──────┬───────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                │                  │                 │                 │
         ┌──────▼───────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
         │ Claude API   │  │ Neo4j       │  │ Data Lake   │         │
         │ GPT API      │  │ Graph DB    │  │ (S3/ADLS)   │  ┌──────▼──────┐
         │ Gemini API   │  │             │  │             │  │ Agent        │
         └──────────────┘  └─────────────┘  └──────┬──────┘  │ Framework    │
                                                    │         └─────────────┘
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                             ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼───────┐
                             │ Clinical    │ │ Lab Systems │ │ Genomics    │
                             │ Trial DB   │ │ (HL7/FHIR) │ │ Pipeline    │
                             └────────────┘ └────────────┘ └─────────────┘
```

## Component Details

### 1. API Gateway
- **Technology**: Kong / AWS API Gateway
- **Authentication**: mTLS with organization-issued certificates
- **Authorization**: RBAC (clinician, data scientist, admin, audit)
- **Rate Limiting**: Per-user and per-endpoint quotas
- **Audit**: Every request logged with full context

### 2. Dashboard Service
- **Framework**: Next.js (React) with WebSocket for real-time updates
- **Hosting**: Internal infrastructure (Kubernetes)
- **Key Views**:
  - Trial overview with patient risk heatmap
  - Individual patient risk trajectory
  - Interactive mechanism explorer (D3.js graph visualization)
  - Prediction audit log
  - Model performance monitoring

### 3. SafetyEngine
- **Language**: Python 3.11+
- **Framework**: FastAPI (REST + WebSocket endpoints)
- **Orchestration**: LangGraph for agent workflows
- **Core loop**:
  1. Receive patient data update
  2. Extract features from Feature Store
  3. Query Knowledge Graph for relevant mechanisms
  4. Route to Model Orchestrator for inference
  5. Aggregate predictions via Ensemble
  6. Generate Safety Index
  7. Evaluate alerts
  8. Push to Dashboard + Audit

### 4. Model Orchestrator
- **Multi-model routing**: Query complexity → model selection
- **Parallel inference**: Multiple models queried simultaneously
- **Response normalization**: Standardized SafetyPrediction format
- **Ensemble aggregation**: Weighted combination with disagreement detection
- **Cost tracking**: Per-query cost accounting per model

### 5. Knowledge Graph
- **Database**: Neo4j Enterprise
- **Size**: ~100K nodes, ~500K edges (growing)
- **Content**: Biological mechanisms, pathway interactions, drug targets, validated hypotheses
- **Embeddings**: Node2Vec + Graph Attention Network embeddings
- **Query interface**: Cypher (direct) + natural language (via foundation model)

### 6. Feature Store
- **Technology**: Feast / Tecton (or custom on Delta Lake)
- **Storage**: Two-tier
  - **Online**: Redis/DynamoDB for real-time serving (<10ms)
  - **Offline**: Delta Lake for batch training
- **Features**: ~200 features per patient (baseline + longitudinal + graph-derived)
- **Versioning**: Full lineage tracking for reproducibility

### 7. Data Pipeline
- **Streaming**: Apache Kafka for real-time lab results and vitals
- **Batch**: Apache Airflow DAGs for clinical trial data, genomics, literature
- **Processing**: Apache Spark for large-scale transformations
- **Quality**: Great Expectations for data validation and profiling

### 8. Agent Framework
- **Technology**: Claude Code / custom agent harness
- **Agent Types**:
  - **Hypothesis Agent**: Generates safety hypotheses from patient context + KG
  - **Validation Agent**: Tests hypotheses against evidence and mechanisms
  - **Literature Agent**: Scans new publications for relevant safety signals
  - **Summarization Agent**: Produces clinical narratives from raw predictions
- **Memory**: Persistent context via Knowledge Graph + session memory

---

## Data Flow Diagrams

### Real-Time Patient Monitoring

```
Lab Result (HL7) ──→ Kafka ──→ Feature Extractor ──→ Feature Store (Online)
                                       │
                                       ▼
                              SafetyEngine triggered
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                           Claude    GPT     Gemini
                              │        │        │
                              └────────┼────────┘
                                       ▼
                              Ensemble Aggregator
                                       │
                                       ▼
                              Safety Index Updated
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                          Dashboard  Alert    Audit
                          (WebSocket) Engine   Log
```

### Batch Population Analysis

```
Clinical Trial DB ──→ Airflow DAG ──→ Feature Store (Offline)
                                              │
                                              ▼
                                     Population Risk Calculator
                                              │
                                              ▼
                                     PopulationSafetyIndex
                                              │
                                    ┌─────────┼─────────┐
                                    ▼         ▼         ▼
                               Dashboard  Reports   Portfolio
                               (Batch)    (PDF)     Analytics
```

### Knowledge Graph Update

```
New Publication ──→ Literature Agent ──→ Entity Extraction ──→ KG Update
                                               │
New Clinical Data ──→ Outcome Analysis ──→ Evidence Update ──→ KG Update
                                               │
Hypothesis Validated ──→ Confidence Update ──→ Edge Weight Update ──→ KG Update
```

---

## Deployment Architecture

### Development Environment
```
Developer Workstation
  └── Claude Code Agent Harness
       ├── SafetyEngine (local)
       ├── Neo4j (Docker)
       ├── Feature Store (local/mock)
       └── Model APIs (sandbox endpoints)
```

### Staging Environment
```
Cloud (Kubernetes)
  ├── SafetyEngine (3 replicas)
  ├── Neo4j Cluster (3 nodes)
  ├── Feature Store (Feast on Redis)
  ├── Kafka Cluster
  ├── Dashboard (2 replicas)
  ├── Alert Service (2 replicas)
  └── Model API Gateway (secure proxy to external models)
```

### Production Environment
```
Cloud (Kubernetes) — GxP Validated
  ├── SafetyEngine (5 replicas, auto-scaling)
  ├── Neo4j Enterprise Cluster (3 nodes, HA)
  ├── Feature Store (Feast on DynamoDB)
  ├── Kafka Cluster (managed)
  ├── Dashboard (3 replicas, CDN)
  ├── Alert Service (3 replicas, priority queues)
  ├── Model API Gateway (mTLS, audit)
  ├── Monitoring (Prometheus + Grafana + PagerDuty)
  └── Backup (daily snapshots, cross-region)
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────┐
│                Organization Network Boundary     │
│                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ Patient   │    │ Safety   │    │ Dashboard│   │
│  │ Data      │───▶│ Engine   │───▶│ (no PII) │   │
│  │ (encrypted)    │          │    │          │   │
│  └──────────┘    └────┬─────┘    └──────────┘   │
│                       │                           │
│              ┌────────▼────────┐                  │
│              │ Secure API Proxy │                  │
│              │ (PII Stripping)  │                  │
│              └────────┬────────┘                  │
│                       │ (no patient data)         │
├───────────────────────┼───────────────────────────┤
│                       │                           │
│              ┌────────▼────────┐                  │
│              │ Foundation Model│                  │
│              │ API Endpoints   │                  │
│              │ (Claude/GPT/    │                  │
│              │  Gemini)        │                  │
│              └─────────────────┘                  │
│                                                   │
│              External Cloud (Approved)             │
└───────────────────────────────────────────────────┘
```

**Key Security Principles**:
1. Patient data never leaves the organization's network boundary
2. Foundation model prompts are stripped of PII where possible
3. When PII is required for reasoning, it goes through approved enterprise API endpoints with BAA/DPA
4. All model interactions logged in immutable audit trail
5. Dashboard displays pseudonymized identifiers only
6. Encryption at rest (AES-256) and in transit (TLS 1.3) everywhere
