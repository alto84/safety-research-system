# Safety Research System — Agent Instructions

## Project Identity
This is an **open-source Predictive Safety Platform** for cell therapy adverse event risk estimation.
It is **fully independent** — no proprietary data, no personal references, no company-internal information.
All data comes from published literature, public registries (ClinicalTrials.gov), and public APIs (openFDA).

## Architecture
- **Backend:** Python 3.13 + FastAPI (single server, two route groups: patient-level + population-level)
- **Frontend:** Single-page HTML dashboard in `src/api/static/index.html` (vanilla JS, no build tools)
- **Models:** `src/models/` — Bayesian risk, correlated mitigation, FAERS signal detection, ensemble scoring
- **Data:** `data/sle_cart_studies.py` — curated clinical data, `src/data/knowledge/` — knowledge graph
- **Tests:** `tests/` — pytest, 421+ tests, run with `python -m pytest tests/ -q`
- **API:** `src/api/` — FastAPI app, routes, schemas

## Design Principles
1. **Data-agnostic:** Modules accept any adverse event type, any treatment, any data source. No hardcoded AE names in core logic.
2. **Extensible:** New adverse events, treatments, data sources, and timescales plug in via configuration, not code changes.
3. **Modular:** Each model (Bayesian, mitigation, FAERS, ensemble) is a standalone module with clean interfaces.
4. **Evidence-graded:** All estimates carry uncertainty bounds, evidence grades, and source attribution.
5. **Clinically meaningful:** Outputs are in clinical units (percentages, relative risks), with caveats and limitations surfaced.
6. **Public data only:** No proprietary data. Designed for future internalization with private data to improve models.

## Code Standards
- Type hints on all functions. Pydantic for API schemas. Dataclasses for internal models.
- All API responses include `request_id` and `timestamp` for traceability.
- Tests live in `tests/unit/` and `tests/integration/`. Run before committing.
- No secrets, credentials, or personal information in code or comments.
- Commit messages: imperative mood, explain "why" not "what."

## Key Modules
| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `bayesian_risk.py` | Beta-Binomial posteriors, evidence accrual | `compute_posterior()`, `compute_evidence_accrual()` |
| `mitigation_model.py` | Correlated RR combination, Monte Carlo | `combine_correlated_rr()`, `monte_carlo_mitigated_risk()` |
| `faers_signal.py` | PRR/ROR/EBGM signal detection | `get_faers_signals()`, `compute_prr()` |
| `sle_cart_studies.py` | Clinical trial data, AE rates, data sources | `get_sle_baseline_risk()`, `CLINICAL_TRIALS` |
| `cell_therapy_registry.py` | All cell therapy types + AE taxonomy | `THERAPY_TYPES`, `AE_TAXONOMY` |
| `model_registry.py` | Multiple risk modeling approaches | `MODEL_REGISTRY`, `estimate_risk()`, `compare_models()` |
| `model_validation.py` | Scientific model testing framework | `calibration_check()`, `brier_score()`, `coverage_probability()` |
| `population_routes.py` | Population-level API endpoints | 8+ routes under `/api/v1/population/` and `/api/v1/signals/` |
| `ensemble_model.py` | Multi-model patient-level scoring | `compute_safety_index()` |

## Expansion Vision
The platform is expanding from SLE CAR-T to ALL cell therapy types:
- **Treatment selector:** User picks therapy type (CAR-T, TCR-T, NK, TIL, gene therapy, etc.)
- **Dynamic AE registry:** AEs auto-populated based on selected therapy type
- **Multiple risk models:** Bayesian, frequentist, meta-analysis, time-to-event — user selects approach
- **Model validation:** Calibration plots, Brier scores, cross-validation, sequential prediction testing
- **CDP/CSP support:** Dashboards for clinical development plans, inclusion/exclusion criteria suggestion
- **Flexible data integration:** Not just Bayesian — support any statistical approach via model registry
- See `EXPANSION-PLAN.md` for full roadmap.

## Dashboard Requirements
The dashboard at `src/api/static/index.html` must include:
- **Patient-level tabs:** Biomarker scoring, ensemble risk assessment, grading predictions (9 tabs)
- **Population-level tabs:** Evidence accrual, mitigation explorer, signal detection, executive summary (4 tabs)
- **CDP/CSP tab (planned):** Protocol design support, inclusion/exclusion criteria, monitoring schedule
- **Treatment selector (planned):** Dropdown to switch therapy type, auto-updates all views
- All charts rendered client-side (vanilla SVG), data from API via fetch()
- Responsive, professional appearance suitable for clinical/regulatory audience
- 704+ tests, run with `python -m pytest tests/ -q`

## Git & Deployment
- **Repo:** https://github.com/alto84/safety-research-system.git
- **Branch:** master
- Push from Rocinante (has credentials). gpuserver1 pulls.
- **gpuserver1:** `ssh alton@192.168.1.100` — runs tests, serves dashboard, does heavy computation
- Commit and push frequently. Document state in SESSION-STATE.md.

## What NOT To Do
- Do not reference AstraZeneca, personal names, or internal data
- Do not hardcode adverse event types — use configuration/registry patterns
- Do not add dependencies without justification (keep it lightweight)
- Do not create files without clear purpose (no file bloat)
- Do not over-engineer — working code that solves the problem beats elegant code that doesn't
