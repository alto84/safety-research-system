# Codebase Snapshot — 2026-02-09

## System Identity

**Predictive Safety Platform (PSP)** — An AI-enabled clinical decision support system for predicting cell therapy adverse events (CRS, ICANS, HLH/IEC-HS) in real time.

**Scale:** ~19,400 lines of source code, ~12,000 lines of tests, 915 tests passing, 15-tab dashboard, 24 API endpoints, knowledge graph with 90+ nodes across 5 signaling pathways.

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│  BROWSER: index.html (4,766 lines, vanilla JS + SVG)            │
│  15 tabs: 9 patient-level + 6 population/system                 │
│  Demo cases (8 patients, multi-timepoint), dark/light theme     │
└─────────────────────┬───────────────────────────────────────────┘
                      │ fetch() / WebSocket
┌─────────────────────▼───────────────────────────────────────────┐
│  FASTAPI (app.py 1,096 lines + population_routes.py 1,498 lines)│
│                                                                  │
│  Middleware Stack:                                               │
│    ErrorHandling → RateLimit(100/min) → APIKey → RequestTiming  │
│                                                                  │
│  24 Endpoints:                                                   │
│    Patient:  POST /predict, /predict/batch, GET /timeline       │
│    Scores:   GET /scores/easix, /scores/hscore, /scores/car-*   │
│    Population: GET /risk, /evidence-accrual, /trials, /comparison│
│    Bayesian: POST /bayesian, /mitigations                       │
│    Signals:  GET /signals/faers                                  │
│    CDP/CSP:  GET /monitoring-schedule, /eligibility-criteria,    │
│              /stopping-rules, /sample-size                       │
│    System:   GET /health, /system/architecture                   │
│    WebSocket: /ws/monitor/{patient_id}                           │
└──────────┬────────────────────┬──────────────────────────────────┘
           │                    │
    ┌──────▼──────┐     ┌──────▼──────────────────────────────┐
    │  ENSEMBLE   │     │  STATISTICAL MODELS                  │
    │  RUNNER     │     │                                      │
    │  (378 lines)│     │  bayesian_risk.py    (378 lines)    │
    │             │     │  mitigation_model.py (557 lines)    │
    │  7 biomarker│     │  faers_signal.py     (941 lines)    │
    │  models in  │     │  model_registry.py   (917 lines)    │
    │  2 layers   │     │  model_validation.py (482 lines)    │
    └──────┬──────┘     └──────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────────────────┐
    │  BIOMARKER SCORES (1,400 lines)                         │
    │  Layer 0 (standard labs): EASIX, m-EASIX, P-m-EASIX,   │
    │    HScore, CAR-HEMATOTOX                                │
    │  Layer 1 (cytokines): Teachey 3-Cytokine, Hay Binary   │
    └─────────────────────────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────────────────┐
    │  KNOWLEDGE GRAPH                                         │
    │  src/data/knowledge/ (2,978 lines across 6 modules)     │
    │  src/data/graph/     (1,653 lines across 3 modules)     │
    │                                                          │
    │  9 cell types, 14 molecular targets, 4 pathways,        │
    │  6 mechanism chains, 31 PubMed references                │
    │  90+ shared graph nodes, 5 pre-built pathway builders   │
    └─────────────────────────────────────────────────────────┘
           │
    ┌──────▼──────────────────────────────────────────────────┐
    │  CLINICAL DATA                                           │
    │  data/sle_cart_studies.py      (811 lines)              │
    │  data/cell_therapy_registry.py (~1,000 lines)           │
    │  data/synthetic_cohorts.py     (~1,200 lines)           │
    │  data/trial_configs.py         (489 lines)              │
    │  data/edge_cases.py            (~500 lines)             │
    │                                                          │
    │  6 pivotal trials, 785 synthetic patients,              │
    │  45 edge cases, 20+ AE types, 5 therapy types           │
    └─────────────────────────────────────────────────────────┘
```

---

## File Inventory (94 Python files, 143 total)

### API Layer (~10,400 lines)
| File | Lines | What It Does |
|------|-------|--------------|
| `src/api/app.py` | 1,096 | FastAPI app, patient endpoints, WebSocket, ensemble orchestration |
| `src/api/population_routes.py` | 1,498 | 14 population/CDP/system endpoints |
| `src/api/schemas.py` | 652 | All Pydantic request/response models |
| `src/api/middleware.py` | 261 | Rate limiting, API key auth, timing, error handling |
| `src/api/static/index.html` | 4,766 | 15-tab clinical dashboard (vanilla JS + SVG) |
| `src/api/static/demo_cases.js` | ~1,000 | 8 demo patients with multi-timepoint lab/vitals/cytokine data |
| `demo/index.html` | 1,122 | Standalone demo page (dark theme, glassmorphic) |

### Prediction Models (~3,400 lines)
| File | Lines | What It Does |
|------|-------|--------------|
| `src/models/biomarker_scores.py` | ~1,400 | 7 scoring models (EASIX, HScore, CAR-HEMATOTOX, Teachey, Hay) |
| `src/models/ensemble_runner.py` | 378 | Two-layer ensemble: standard labs + cytokine panel |
| `src/models/bayesian_risk.py` | 378 | Beta-Binomial posteriors, evidence accrual, stopping boundaries |
| `src/models/mitigation_model.py` | 557 | Correlated RR combination, Monte Carlo simulation |
| `src/models/faers_signal.py` | 941 | PRR/ROR/EBGM signal detection (GPS from DuMouchel 1999) |
| `src/models/model_registry.py` | 917 | 7 risk models: Bayesian, Clopper-Pearson, Wilson, DerSimonian-Laird, Empirical Bayes, Kaplan-Meier, Predictive Posterior |
| `src/models/model_validation.py` | 482 | Calibration, Brier score, LOO-CV, sequential prediction |

### Knowledge Graph (~4,600 lines)
| File | Lines | What It Does |
|------|-------|--------------|
| `src/data/knowledge/mechanisms.py` | 481 | 6 therapy→AE mechanism chains (CAR-T CRS, ICANS, TCR-T cross-reactivity, CAR-NK, gene therapy, B-cell aplasia) |
| `src/data/knowledge/cell_types.py` | 376 | 9 cell populations with activation states and AE roles |
| `src/data/knowledge/molecular_targets.py` | 517 | 14 druggable targets with modulators, ranges, pathway membership |
| `src/data/knowledge/pathways.py` | 705 | 4 signaling cascades: IL-6 trans-signaling (15 steps), BBB disruption, HLH/MAS, TNF/NF-kB |
| `src/data/knowledge/references.py` | 466 | 31 PubMed citations with evidence grades |
| `src/data/knowledge/graph_queries.py` | 433 | Cross-module query API: pathways, interventions, biomarker rationale |
| `src/data/graph/knowledge_graph.py` | 518 | In-memory graph engine (BFS, upstream causes, mechanism validation, patient similarity) |
| `src/data/graph/crs_pathways.py` | 976 | 5 pre-built pathway builders with 90 shared graph nodes |
| `src/data/graph/schema.py` | 159 | 10 node types, 22 edge types, severity grades, temporal phases |

### Clinical Data (~4,000 lines)
| File | Lines | What It Does |
|------|-------|--------------|
| `data/sle_cart_studies.py` | 811 | 16 AE rates, 14 clinical trials, 8 data sources |
| `data/cell_therapy_registry.py` | ~1,000 | 5 therapy types (CAR-T CD19/BCMA/dual, TCR-T, NK), 20+ AE taxonomy |
| `data/synthetic_cohorts.py` | ~1,200 | Full patient generator: vitals q4h, labs daily, cytokines q12h, ICE scores |
| `data/trial_configs.py` | 489 | 6 pivotal trial configs (ZUMA-1, JULIET, ELARA, KarMMa, CARTITUDE-1, TRANSCEND) |
| `data/edge_cases.py` | ~500 | 45 edge cases: extreme values, missing data, late-onset, concurrent toxicities |

### Configuration
| File | Lines | What It Does |
|------|-------|--------------|
| `config/models.yaml` | 189 | 3 LLM models (Claude/GPT/Gemini), task routing, evaluation criteria |
| `config/data_sources.yaml` | 306 | 13 data source types (EDC, CTMS, FHIR, HL7, genomics, FAERS) |
| `config/security.yaml` | 333 | 21 CFR Part 11 audit trail, AES-256, RBAC, incident response |

### Test Suite (~12,000 lines)
| Category | Tests | Files | Focus |
|----------|-------|-------|-------|
| Unit | 650 | 17 | All models, graph, input validation, normalization |
| Integration | 194 | 6 | API endpoints, prediction pipeline, engine flow |
| Validation | 20 | 1 | Synthetic cohort calibration vs published trials |
| Stress/Battle | 12 | 1 | 10K patients, adversarial inputs, NaN/Inf |
| Safety/Regulatory | 39 | 1 | Compliance, data-agnostic, public-data-only |
| **Total** | **915** | **26** | **957-line conftest.py with 3 risk-level fixtures** |

### Evaluation Framework
| File | What It Does |
|------|--------------|
| `evals/benchmarks/safety_prediction.py` | 7 benchmark metrics with targets (AUROC ≥0.80, Brier <0.15, timing MAE <12h) |
| `evals/metrics/clinical_metrics.py` | AUROC, Brier, ECE, NRI, timing accuracy |
| `evals/metrics/fairness.py` | Equalized odds, demographic parity, calibration parity (<5% disparity) |

### GPU Server Tasks (Future)
| File | What It Does |
|------|--------------|
| `gpuserver_tasks/task1_build_knowledge_graph.py` | Build graph from Reactome/STRING/DrugBank/SIDER/CTD (~100K nodes) |
| `gpuserver_tasks/task2_train_gnn_embeddings.py` | Node2Vec + GAT + R-GCN on RTX 5090 |
| `gpuserver_tasks/task3_graph_explorer.py` | Flask + D3.js interactive graph explorer |

---

## Dashboard: 15 Tabs

### Patient-Level (9 tabs)
1. **Overview** — Composite risk meter, top alerts, current status
2. **Pre-Infusion** — Lab input form, vitals, clinical context
3. **Day 1 Monitor** — D1 vitals, fever tracking, early CRS detection
4. **CRS Monitor** — ASTCT grade selector (0-4), grade-specific management
5. **ICANS** — ICE score, neuro symptoms, treatment tracker
6. **HLH Screen** — HScore computation, ferritin/fibrinogen/triglyceride tracking
7. **Hematologic** — CAR-HEMATOTOX, CBC trends, cytopenia monitoring
8. **Discharge** — Recovery metrics, cell expansion, readiness assessment
9. **Clinical Visit** — Long-term follow-up, remission status

### Population/System (6 tabs)
10. **Population Risk** — Baseline rates by AE type, cross-indication comparison
11. **Mitigation Explorer** — Strategy selector, combined RR, Monte Carlo CI
12. **Signal Detection** — FAERS signal table (PRR/ROR/EBGM), 6 CAR-T products
13. **Executive Summary** — Printable regulatory-ready summary
14. **Clinical Safety Plan** — Monitoring schedule, eligibility criteria, stopping rules, sample size
15. **System Architecture** — Module graph, endpoint catalog, model registry cards

---

## Statistical Method Inventory

### Biomarker Scoring (7 models)
| Model | Formula/Method | Risk Thresholds | Citation |
|-------|---------------|-----------------|----------|
| EASIX | (LDH × Creatinine) / Platelets | <3.2 / 3.2-10 / ≥10 | Pennisi 2021 |
| m-EASIX | (LDH × CRP) / Platelets | <5.0 / 5.0-20 / ≥20 | — |
| P-m-EASIX | Same, pre-lymphodepletion | Same | — |
| HScore | 9-variable weighted (0-337) | <90 / 90-169 / ≥169 | Fardet 2014 |
| CAR-HEMATOTOX | 5 variables × 0-2 pts (0-10) | 0-1 / 2 / ≥3 | Rejeski 2021 |
| Teachey 3-Cytokine | Logistic: β₀ + β₁ln(IFN-γ) + β₂ln(sgp130) + β₃ln(IL-1RA) | <0.20 / 0.20-0.50 / ≥0.50 | Teachey 2016 |
| Hay Binary | Fever ≥38.9°C ∧ (MCP-1 >1343 ∨ tachycardia) | Binary | Hay 2017 |

### Population Risk Models (7 approaches)
| Model | Method | Best For |
|-------|--------|----------|
| Bayesian Beta-Binomial | Conjugate posterior, 95% credible interval | Small samples, sequential updating |
| Clopper-Pearson Exact | Beta distribution CI | Regulatory submissions |
| Wilson Score | Centre-adjusted CI | Small n, extreme proportions |
| DerSimonian-Laird | Random-effects meta-analysis, Freeman-Tukey transform | Multi-study pooling |
| Empirical Bayes | Shrinkage: (1-B)×raw + B×grand_mean | Borrowing across AE types |
| Kaplan-Meier | Product-limit, Greenwood variance | Time-to-event, censored data |
| Predictive Posterior | Beta-Binomial PMF for y_new | Predicting rate in next study |

### Signal Detection
| Metric | Formula | Signal Threshold |
|--------|---------|-----------------|
| PRR | (a/(a+b)) / (c/(c+d)) | ≥2.0, CI lower >1.0 |
| ROR | (a×d) / (b×c) | CI lower >1.0 |
| EBGM | GPS (DuMouchel 1999), Gamma-Poisson Shrinker | EBGM05 ≥2.0 (strong) |

---

## Knowledge Graph Summary

### Encoded Clinical Knowledge
- **6 mechanism chains:** CAR-T CD19→CRS (11 steps), CAR-T→ICANS (8 steps), TCR-T cross-reactivity (4 steps), CAR-NK reduced CRS (4 steps), gene therapy insertional mutagenesis (4 steps), CAR-T→B-cell aplasia (4 steps)
- **4 signaling pathways:** IL-6 trans-signaling (15 steps, 3 feedback loops), BBB disruption (10 steps), HLH/MAS (10 steps, IFN-γ/IL-18 positive feedback), TNF/NF-kB amplification (6 steps)
- **14 molecular targets:** 5 cytokines (IL-6, IL-1β, IFN-γ, TNF-α, IL-18), 3 receptors (sIL-6R, gp130, Ang-2), 3 kinases/TFs (JAK1, STAT3, NF-kB), 3 biomarkers (CRP, ferritin, EASIX), 1 safety switch (iCasp9)
- **9 cell types:** CAR-T, monocyte, macrophage, endothelial, NK, pericyte, astrocyte, neutrophil, dendritic
- **31 PubMed references** with evidence grades (2 RCT, 8 prospective, 6 retrospective, 8 review, 6 preclinical, 1 consensus)

### Temporal Model
| Phase | Window | Key Events |
|-------|--------|------------|
| Immediate | 0-6h | CAR-T antigen engagement, IFN-γ secretion begins |
| Early | 6-24h | IFN-γ peaks, monocyte activation, ADAM17 shedding → sIL-6R |
| Peak | 24-72h | IL-6 peaks (100-100K pg/mL), endothelial activation, BBB infiltration |
| Sustained | 72h-7d | Continued cytokine elevation, hemophagocytosis if severe |
| Late | 7-14d | Resolution or escalation to HLH |
| Delayed | >14d | B-cell aplasia, infection risk, secondary immune complications |

---

## Dependencies (from pyproject.toml)

### Production (55+ packages)
- **ML:** torch, pytorch-lightning, scikit-learn, xgboost, shap, lifelines
- **Data:** pandas, polars, pyarrow, numpy
- **LLMs:** anthropic, openai, google-cloud-aiplatform
- **Clinical Standards:** fhir.resources, hl7apy
- **API:** fastapi, uvicorn, pydantic, httpx
- **MLOps:** mlflow, great-expectations, evidently, prometheus-client
- **Cloud:** boto3, azure-identity, azure-keyvault-secrets

### Dev
- **Testing:** pytest, pytest-cov, pytest-asyncio, pytest-mock, hypothesis
- **Quality:** ruff, mypy (strict), pre-commit

---

## What's Not Built Yet

| Gap | Status | Notes |
|-----|--------|-------|
| CI/CD pipeline | Missing | No GitHub Actions, no Docker |
| Database persistence | In-memory only | Patient timelines stored in defaultdict |
| Authentication UI | API key only | No login page, no session management |
| GNN embeddings | Planned (gpuserver) | Task scripts written, not executed |
| Interactive graph explorer | Planned (gpuserver) | Flask + D3.js, not yet running |
| Neo4j backend | Optional protocol defined | In-memory graph only |
| Real-time monitoring | Prometheus dependency present | No dashboards configured |
| LLM integration | Config defined | No actual LLM calls in prediction pipeline |
| Multi-user support | Not implemented | Single-tenant design |

---

## How to Run

```bash
# Install
pip install -e ".[dev]"

# Tests (915 passing, ~8 seconds)
python -m pytest tests/ -q

# Server
python run_server.py                    # http://localhost:8000
python run_server.py --port 8080        # custom port
python run_server.py --reload           # dev mode with auto-reload

# Dashboard
# Open http://localhost:8000 in browser
# API docs at http://localhost:8000/docs
```
