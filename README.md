# Predictive Safety Platform

**Cell therapy adverse event risk estimation using public clinical data.**

A working demo with 17-tab clinical dashboard, 36 API endpoints, 7 risk models, and a knowledge graph covering 4 signaling pathways across CRS, ICANS, HLH, and hematologic toxicities.

---

## Quick Start (2 minutes)

**Requirements:** Python 3.11+ and pip. That's it.

```bash
# 1. Clone
git clone https://github.com/alto84/safety-research-system.git
cd safety-research-system

# 2. Install (only 5 lightweight dependencies)
pip install fastapi uvicorn[standard] pydantic httpx scipy

# 3. Run
python run_server.py
```

Open **http://localhost:8000/clinical** in your browser. Done.

---

## What You'll See

### Dashboard (17 tabs)

**Patient-Level (9 tabs)** -- Select a demo patient from the sidebar:

| Tab | What it shows |
|-----|--------------|
| Overview | Composite risk score, individual model scores, lab values with trends |
| Pre-Infusion | Screening risk assessment, eligibility flags |
| Day 1 Monitor | Post-infusion vital signs, early warning indicators |
| CRS Monitor | Cytokine release syndrome grading and trajectory |
| ICANS | Immune effector cell neurotoxicity assessment |
| HLH Screen | Hemophagocytic lymphohistiocytosis screening score |
| Hematologic | Cytopenia monitoring, CAR-HEMATOTOX score |
| Discharge | Readiness assessment, follow-up recommendations |
| Clinical Visit | Longitudinal follow-up tracking |

**Population-Level (8 tabs)** -- No patient selection needed:

| Tab | What it shows |
|-----|--------------|
| Population Risk | Baseline AE rates from 47 pooled SLE CAR-T patients |
| Mitigation Explorer | Interactive risk reduction modeling with correlated mitigations |
| Signal Detection | FAERS comparison across 6 CAR-T products, ClinicalTrials.gov trial evidence, cross-source triangulation |
| Executive Summary | Traffic-light risk overview for leadership |
| Clinical Safety Plan | Monitoring schedule, eligibility criteria, stopping rules, sample sizing |
| System Architecture | Interactive architecture diagram |
| Scientific Basis | Knowledge graph: signaling pathways, molecular targets, cell types, PubMed references |
| Publication Analysis | Forest plots, evidence accrual, model calibration, prior comparison |

### API (36 endpoints)

Full Swagger docs at **http://localhost:8000/docs**

Key endpoints to try:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Patient risk prediction (7 models)
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"ldh": 450, "creatinine": 1.2, "platelets": 150, "ferritin": 1500, "fibrinogen": 180, "temperature": 38.5, "hemoglobin": 10.5, "anc": 1.2, "crp": 45, "disease_burden": 0.6}'

# Population baseline risk
curl http://localhost:8000/api/v1/population/risk

# FAERS product comparison (6 approved CAR-T products, 16K+ reports)
curl http://localhost:8000/api/v1/signals/faers/comparison

# Clinical trial AE data (47 trials from ClinicalTrials.gov)
curl http://localhost:8000/api/v1/trials/ae-data

# Cross-source signal triangulation (FAERS vs trial rates)
curl http://localhost:8000/api/v1/signals/triangulation

# Knowledge graph overview
curl http://localhost:8000/api/v1/knowledge/overview
```

---

## Run Tests

```bash
# Install test runner
pip install pytest pytest-cov

# Run all 1608 tests
python -m pytest tests/ -q
```

Expected output: `1608 passed in ~10-30s` (depending on hardware).

---

## Project Structure

```
safety-research-system/
├── run_server.py                 # Start here
├── src/
│   ├── api/
│   │   ├── app.py                # FastAPI application
│   │   ├── population_routes.py  # All API endpoints
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── narrative_engine.py   # Clinical narrative generation
│   │   └── static/
│   │       └── index.html        # Dashboard (single-page, vanilla JS)
│   ├── models/
│   │   ├── bayesian_risk.py      # Beta-Binomial posteriors
│   │   ├── mitigation_model.py   # Correlated risk reduction
│   │   ├── faers_signal.py       # FAERS signal detection (PRR/ROR/EBGM)
│   │   ├── model_registry.py     # 7-model risk registry
│   │   ├── model_validation.py   # Calibration, Brier scores, coverage
│   │   ├── ensemble_runner.py    # Two-layer biomarker ensemble
│   │   └── signal_triangulation.py # FAERS vs ClinicalTrials.gov comparison
│   └── data/
│       ├── knowledge/            # Cell therapy knowledge graph
│       │   ├── pathways.py       # 4 signaling cascades (47 directed steps)
│       │   ├── mechanisms.py     # 6 therapy-to-AE mechanism chains
│       │   ├── molecular_targets.py  # 15 druggable targets
│       │   ├── cell_types.py     # 9 cell populations
│       │   ├── references.py     # 29 PubMed-linked references
│       │   └── graph_queries.py  # Query API for pathways and targets
│       ├── faers_cache.py        # Pre-computed FAERS product comparison
│       └── ctgov_cache.py        # ClinicalTrials.gov AE data loader
├── data/
│   ├── sle_cart_studies.py       # Curated SLE CAR-T clinical data (47 patients)
│   └── cell_therapy_registry.py  # 12 therapy types, 21 AE profiles
├── analysis/
│   ├── ae_database_research.md   # Research report: 12 public AE databases
│   ├── ct_gov_extractor.py       # ClinicalTrials.gov data extraction tool
│   ├── enhanced_faers.py         # FAERS product comparison extraction tool
│   └── results/                  # Extracted data files
├── tests/
│   ├── unit/                     # Unit tests
│   └── integration/              # API integration tests
└── docs/
    ├── qa-report.md              # Comprehensive QA report
    └── claude-integration-options.md  # AI integration roadmap
```

---

## Data Sources

All data is public. No proprietary data, no credentials, no API keys required.

| Source | What | How it's used |
|--------|------|--------------|
| Published literature | SLE CAR-T trial results (7 studies, 47 patients) | Baseline risk estimates, evidence accrual |
| ClinicalTrials.gov | 47 completed CAR-T trials with AE data | Trial-level AE rates, cross-trial comparison |
| openFDA (FAERS) | 16,432 spontaneous AE reports across 6 CAR-T products | Signal detection, product comparison, triangulation |
| PubMed | 29 referenced publications | Knowledge graph evidence grading |

---

## Configuration

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `SAFETY_API_KEY` | *(unset = auth disabled)* | API key for authentication |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

For the demo, no configuration is needed.

---

## Server Options

```bash
python run_server.py                    # Default: 0.0.0.0:8000
python run_server.py --port 9000        # Custom port
python run_server.py --host 127.0.0.1   # Localhost only
python run_server.py --reload           # Auto-reload on code changes (dev mode)
```

---

## License

Apache 2.0
