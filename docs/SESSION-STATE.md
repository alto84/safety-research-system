# Session State: Predictive Safety Platform

**Date:** 2026-02-08
**Commit:** `058bf95` (master)
**Test Status:** 1400 passed, 0 failed (29 test files)
**Server:** `python run_server.py` at http://localhost:8000/clinical

---

## Architecture Overview

The Predictive Safety Platform estimates adverse event risk for cell therapy
(CAR-T, TCR-T, CAR-NK, gene therapy) in autoimmune indications. It combines
Bayesian statistical models, published clinical trial data, FAERS
pharmacovigilance signals, and a mechanistic knowledge graph into a single
FastAPI application with a vanilla-JS dashboard.

```
src/
  api/
    app.py                  -- FastAPI app, patient-level endpoints
    population_routes.py    -- Population, CDP, knowledge, publication, narrative endpoints
    schemas.py              -- Pydantic request/response models
    middleware.py           -- Request timing, rate limiting, error handling
    narrative_engine.py     -- Template-based clinical narrative generation
    static/index.html       -- Single-page dashboard (17 tabs, ~5000+ lines)
  models/
    bayesian_risk.py        -- Beta-Binomial conjugate posteriors, evidence accrual
    mitigation_model.py     -- Correlated relative risk combination, Monte Carlo
    faers_signal.py         -- PRR/ROR/EBGM disproportionality via openFDA
    model_registry.py       -- 7-model risk estimation registry
    model_validation.py     -- Calibration, Brier scores, LOO-CV, coverage
    biomarker_scores.py     -- EASIX, HScore, CAR-HEMATOTOX scoring models
    ensemble_runner.py      -- Two-layer biomarker ensemble aggregation
  data/
    knowledge/
      pathways.py           -- 4 signaling pathways (IL-6, BBB/ICANS, HLH, TNF/NF-kB)
      mechanisms.py         -- 6 therapy-to-AE mechanism chains
      molecular_targets.py  -- 15 druggable molecular targets
      cell_types.py         -- 9 cell type definitions
      references.py         -- 21 PubMed references (22 listed, 1 PMID collision)
      graph_queries.py      -- Knowledge graph query API
      integration.py        -- Knowledge-to-model bridge
data/
  sle_cart_studies.py       -- 7 SLE CAR-T trials, 6 oncology comparators, pooled analysis
  cell_therapy_registry.py  -- 12 therapy types, 21 AE profiles
tests/
  unit/                     -- Unit tests
  integration/              -- API and pipeline integration tests
  validation/               -- Calibration and statistical validation tests
  safety/                   -- Regulatory compliance tests
  stress/                   -- Stress and battle tests
```

---

## Test Summary

| Category | Count |
|----------|-------|
| Total tests | 1400 |
| Test files | 29 |
| Status | All passing |
| Runtime | ~9 seconds |

Test categories: unit, integration, validation, safety, stress.

---

## Dashboard Tabs (17)

### Patient-Level (9)
1. **Overview** -- Patient risk summary with ensemble scoring
2. **Pre-Infusion** -- Baseline risk assessment and eligibility
3. **Day 1 Monitor** -- Acute post-infusion monitoring (0-24h)
4. **CRS Monitor** -- Cytokine release syndrome grading and tracking
5. **ICANS** -- Neurotoxicity screening (ICE score, imaging)
6. **HLH Screen** -- HScore calculator, ferritin/fibrinogen trending
7. **Hematologic** -- Cytopenia monitoring, CAR-HEMATOTOX scoring
8. **Discharge** -- Discharge readiness assessment
9. **Clinical Visit** -- Follow-up visit documentation

### Population-Level (8)
10. **Population Risk** -- SLE CAR-T baseline risk with 7-model comparison
11. **Mitigation Explorer** -- Correlated mitigation strategy analysis
12. **Signal Detection** -- FAERS pharmacovigilance signal dashboard
13. **Executive Summary** -- High-level risk overview for stakeholders
14. **Clinical Safety Plan** -- CDP monitoring schedule, eligibility, stopping rules
15. **System Architecture** -- Module dependency graph, test summary
16. **Scientific Basis** -- Knowledge graph pathway visualization
17. **Publication Analysis** -- Forest plots, evidence accrual, calibration figures

---

## API Endpoints (33)

### Patient-Level (8 endpoints in `app.py`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/predict` | Run ensemble prediction for a patient |
| POST | `/api/v1/predict/batch` | Batch prediction for multiple patients |
| GET | `/api/v1/patient/{patient_id}/timeline` | Risk timeline for a patient |
| GET | `/api/v1/models/status` | Model availability and status |
| GET | `/api/v1/scores/easix` | Compute EASIX score |
| GET | `/api/v1/scores/hscore` | Compute HScore |
| GET | `/api/v1/scores/car-hematotox` | Compute CAR-HEMATOTOX score |
| GET | `/api/v1/health` | Health check |

### Population-Level (7 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/population/risk` | SLE CAR-T baseline risk summary |
| POST | `/api/v1/population/bayesian` | Compute Bayesian posterior for AE rate |
| POST | `/api/v1/population/mitigations` | Correlated mitigation risk analysis |
| GET | `/api/v1/population/mitigations/strategies` | List available mitigation strategies |
| GET | `/api/v1/population/evidence-accrual` | Evidence accrual timeline |
| GET | `/api/v1/population/trials` | CAR-T clinical trial registry |
| GET | `/api/v1/population/comparison` | Cross-indication AE rate comparison |

### Signals (1 endpoint)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/signals/faers` | FAERS signal detection for CAR-T products |

### CDP / Clinical Safety Plan (4 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cdp/monitoring-schedule` | 7-window monitoring schedule |
| GET | `/api/v1/cdp/eligibility-criteria` | Inclusion/exclusion criteria |
| GET | `/api/v1/cdp/stopping-rules` | Bayesian stopping boundaries |
| GET | `/api/v1/cdp/sample-size` | Sample size considerations |

### Knowledge Graph (6 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/knowledge/pathways` | List all signaling pathways |
| GET | `/api/v1/knowledge/pathways/{pathway_id}` | Get pathway detail with steps |
| GET | `/api/v1/knowledge/mechanisms` | List mechanism chains |
| GET | `/api/v1/knowledge/targets` | List molecular targets |
| GET | `/api/v1/knowledge/cells` | List cell types |
| GET | `/api/v1/knowledge/references` | List PubMed references |
| GET | `/api/v1/knowledge/overview` | Knowledge graph summary stats |

### Publication (2 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/publication/analysis` | Full publication-ready analysis data |
| GET | `/api/v1/publication/figures/{figure_name}` | Individual figure data (forest plots, calibration, etc.) |

### Narratives (2 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/narratives/generate` | Generate clinical narrative for a patient |
| GET | `/api/v1/narratives/patient/{patient_id}/briefing` | Comprehensive clinical briefing |

### System (3 endpoints)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/system/architecture` | System architecture metadata |
| GET | `/api/v1/therapies` | List available therapy types |
| GET | `/api/v1/health` | Health check |

---

## Models

### 7-Model Risk Registry (`model_registry.py`)

| Model | Method | Use Case |
|-------|--------|----------|
| `bayesian_beta_binomial` | Conjugate Beta-Binomial with informative priors | Small samples, sequential updating |
| `frequentist_exact` | Clopper-Pearson exact binomial CI | Regulatory submissions |
| `wilson_score` | Wilson score interval | Small n, proportions near 0 or 1 |
| `random_effects_meta` | DerSimonian-Laird random effects | Multi-study pooling |
| `empirical_bayes` | Shrinkage across AE types | Borrowing strength |
| `kaplan_meier` | Product-limit time-to-event | Censored data, onset timing |
| `predictive_posterior` | Beta-Binomial predictive distribution | Next-study prediction |

### Biomarker Scoring Models (`biomarker_scores.py`)

| Model | Inputs | Output |
|-------|--------|--------|
| EASIX | LDH, creatinine, platelets | Endothelial activation score |
| Modified EASIX | + ferritin, CRP | Enhanced endothelial score |
| HScore | 9 clinical/lab parameters | HLH probability (0-100%) |
| CAR-HEMATOTOX | Hematologic parameters | Cytopenia risk |
| Teachey 3-Cytokine | IFN-gamma, IL-13, MIP-1alpha | CRS severity predictor |
| Hay Binary Classifier | MCP-1, IL-8 day-1 levels | Binary severe CRS risk |

---

## Data Sources

| Source | Content | Location |
|--------|---------|----------|
| SLE CAR-T Trials | 7 trials (n=47), AE rates, demographics | `data/sle_cart_studies.py` |
| Oncology CAR-T Trials | 6 pivotal trials (n=781), comparator data | `data/sle_cart_studies.py` |
| Cell Therapy Registry | 12 therapy types, 21 AE profiles | `data/cell_therapy_registry.py` |
| openFDA FAERS | Real-time disproportionality signals | `src/models/faers_signal.py` (API) |
| Knowledge Graph | 4 pathways, 6 mechanism chains, 15 targets, 9 cell types, 21 references | `src/data/knowledge/` |

---

## Knowledge Graph

### Pathways (4)
1. **IL-6 Trans-Signaling Cascade** (PW:IL6_TRANS_SIGNALING) -- 16 steps, CRS mechanism
2. **BBB Disruption and ICANS** (PW:BBB_DISRUPTION_ICANS) -- 10 steps, neurotoxicity
3. **HLH/MAS Hyperinflammation** (PW:HLH_MAS) -- 10 steps, hemophagocytic syndrome
4. **TNF-alpha/NF-kB Amplification** (PW:TNF_NFKB) -- 6 steps, inflammatory feedforward

### Known Pathway Gaps
- B-cell aplasia / hypogammaglobulinemia (mechanism chain exists, no pathway)
- Prolonged cytopenias (~30% of SLE patients)
- Infection complications (~12.8% in SLE)
- T-cell lymphoma (FDA safety signal, FAERS monitored)

### Mechanism Chains (6)
- CAR-T CD19 -> CRS (11 steps)
- CAR-T CD19 -> ICANS (8 steps)
- CAR-T CD19 -> B-cell aplasia (5 steps)
- TCR-T -> cross-reactivity (7 steps)
- CAR-NK -> reduced CRS (6 steps)
- Gene therapy -> insertional mutagenesis (4 steps)

---

## Known Issues / Remaining Backlog

### From Team-of-Critics Review (`docs/team-of-critics-review.md`)

**Critical (unfixed)**
- C3: EBGM05 weighted average is not the true mixture 5th percentile (`faers_signal.py` line 398). Requires numerical root-finding for the mixture quantile.

**High (unfixed)**
- H5: Database size estimation via NAUSEA*10 is unreliable (`faers_signal.py` lines 705-732)
- H6: Two mechanism chains have empty `key_references` (GENE_THERAPY_INSERTIONAL, CART_CD19_B_CELL_APLASIA)
- H4: Dose-reduction RR=0.15 with "Strong" evidence is optimistic (`mitigation_model.py` lines 192-194)

**Medium (partially addressed)**
- M2: Unused variable `manual_b` in empirical Bayes (now commented out, lines 407-408)
- M3: KM O(n*k) complexity -- docstring added noting acceptable for n<1000 (DONE)
- M6: No data versioning or change control for clinical data
- M8: Missing management algorithm integration
- M10: Pathway coverage gaps -- docstring added documenting known gaps (DONE)

**Low**
- L1: Evidence accrual field naming confusion (cumulative vs per-timepoint)
- L2: No MedDRA version tracking in FAERS target terms
- L3: No persistent audit log for GxP compliance
- L4: API version 0.1.0 with no deprecation policy
- L5: Confidence scores lack documented calibration methodology
- L6: No Weber effect caveat for recently approved products
- L7: SLE-specific biomarker threshold calibration not implemented
- L8: Pooled analysis lacks heterogeneity metrics in API response

### Other Known Issues
- Duplicate PMID:39277881 in `references.py` causes reference count to be 21, not 22 (fixed in prior session)
- `from scipy.special import betaln, gammaln` is imported inside `predictive_posterior()` function body rather than at module level (deliberate to avoid import cost for unused models)
- Dashboard is vanilla JS with no build system -- any major UI changes require editing the single `index.html`

### TODOs in Code
1. `src/models/faers_signal.py:750` -- Replace NAUSEA-based database size estimation with direct openFDA total query
2. `src/models/model_registry.py:536` -- Optimise KM for larger datasets with running at-risk count

---

## Recent Commit History

```
058bf95 Improve knowledge graph layout: wider nodes, two-line labels, better spacing
5cc65fc Fix pathway diagram freeze on ICANS/HLH and add publication tab styling
1d4f60b Wrap tab bar into two rows for all 17 tabs to be visible
9fcdb68 Fix MEDIUM critic items: M1, M4, M5, M7, M9
7f13f3f Fix remaining HIGH critic items: H2, H7, H8
cf9fa83 Fix critical and quick-win items from team-of-critics review
ce7e7b4 Fix narrative generation bugs
9180215 Add narrative generation, publication analysis tab, and critic fixes
d73aeeb Add Scientific Basis knowledge graph visualization (Tab 16)
6f8c87b Fix critical issues from team-of-critics review
```

---

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn scipy pydantic

# Run server
python run_server.py
# Open http://localhost:8000/clinical

# Run tests
python -m pytest tests/ -q

# Run specific test categories
python -m pytest tests/unit/ -q
python -m pytest tests/integration/ -q
python -m pytest tests/validation/ -q
```
