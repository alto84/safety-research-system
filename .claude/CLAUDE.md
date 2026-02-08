# Safety Research System — Agent Instructions

## Project Identity
This is an **open-source Predictive Safety Platform** for cell therapy adverse event risk estimation.
It is **fully independent** — no proprietary data, no personal references, no company-internal information.
All data comes from published literature, public registries (ClinicalTrials.gov), and public APIs (openFDA).

## Architecture
- **Backend:** Python 3.13 + FastAPI (single server, three route groups: patient-level, population-level, system)
- **Frontend:** Single-page HTML dashboard in `src/api/static/index.html` (vanilla JS, no build tools, ~5000+ lines)
- **Models:** `src/models/` — 7-model risk registry, Bayesian risk, correlated mitigation, FAERS signal detection, ensemble scoring, model validation
- **Data:** `data/sle_cart_studies.py` — curated clinical data; `data/cell_therapy_registry.py` — 12 therapy types, 21 AE profiles
- **Knowledge Graph:** `src/data/knowledge/` — 4 signaling pathways, 47 directed steps, 15 molecular targets, 9 cell types, 22 PubMed references
- **Tests:** `tests/` — pytest, 1400+ tests, run with `python -m pytest tests/ -q`
- **API:** `src/api/` — FastAPI app with 33 endpoints, Pydantic schemas, rate-limiting middleware
- **Analysis:** `analysis/` — Publication-ready risk model analyses

## Design Principles
1. **Data-agnostic:** Modules accept any adverse event type, any treatment, any data source. No hardcoded AE names in core logic.
2. **Extensible:** New adverse events, treatments, data sources, and timescales plug in via configuration, not code changes.
3. **Modular:** Each model (Bayesian, mitigation, FAERS, ensemble) is a standalone module with clean interfaces.
4. **Evidence-graded:** All estimates carry uncertainty bounds, evidence grades, and source attribution.
5. **Clinically meaningful:** Outputs are in clinical units (percentages, relative risks), with caveats and limitations surfaced.
6. **Public data only:** No proprietary data. Designed for future internalization with private data to improve models.
7. **Source-linked:** Every data point, pathway edge, and mechanism step references a PubMed ID or published source.

## Code Standards
- Type hints on all functions. Pydantic for API schemas. Dataclasses for internal models.
- All API responses include `request_id` and `timestamp` for traceability.
- Tests live in `tests/unit/` and `tests/integration/`. Run before committing.
- No secrets, credentials, or personal information in code or comments.
- Commit messages: imperative mood, explain "why" not "what."
- Vanilla JS + SVG for all dashboard visualizations — no external frontend dependencies.

## Key Modules
| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `bayesian_risk.py` | Beta-Binomial posteriors, evidence accrual, stopping boundaries | `compute_posterior()`, `compute_evidence_accrual()`, `compute_stopping_boundaries()` |
| `mitigation_model.py` | Correlated RR combination, Monte Carlo | `combine_correlated_rr()`, `monte_carlo_mitigated_risk()` |
| `faers_signal.py` | PRR/ROR/EBGM signal detection via openFDA | `get_faers_signals()`, `compute_prr()` |
| `model_registry.py` | 7 risk estimation approaches | `MODEL_REGISTRY`, `estimate_risk()`, `compare_models()` |
| `model_validation.py` | Scientific model testing | `calibration_check()`, `brier_score()`, `coverage_probability()` |
| `sle_cart_studies.py` | Clinical trial data, AE rates, data sources | `get_sle_baseline_risk()`, `CLINICAL_TRIALS` |
| `cell_therapy_registry.py` | 12 therapy types + AE taxonomy | `THERAPY_TYPES`, `AE_TAXONOMY` |
| `population_routes.py` | Population + CDP + knowledge + publication + narrative endpoints | 25 routes |
| `ensemble_runner.py` | Two-layer biomarker scoring ensemble | `BiomarkerEnsembleRunner`, `EnsembleResult` |
| `narrative_engine.py` | Template-based clinical narrative generation | `generate_narrative()`, `generate_briefing()` |

## Knowledge Graph (`src/data/knowledge/`)
| Module | Content |
|--------|---------|
| `references.py` | 22 publications with PubMed IDs, evidence grades |
| `cell_types.py` | 9 cell populations with markers, activation states, AE roles |
| `molecular_targets.py` | 15 druggable targets with modulators, pathway membership |
| `pathways.py` | 4 cascades: CRS IL-6 trans-signaling, ICANS BBB disruption, HLH IFN-γ feedback, general |
| `mechanisms.py` | 6 therapy-to-AE chains (CAR-T CD19, TCR-T, CAR-NK, gene therapy) |
| `graph_queries.py` | Query API: `get_pathway_for_ae()`, `get_intervention_points()`, `get_mechanism_chain()` |
| `integration.py` | Knowledge-to-model bridge: `get_mechanistic_context()`, `get_narrative_context()` |

## Dashboard (17 tabs)
- **Patient-level (9):** Overview, Pre-Infusion, Day 1 Monitor, CRS Monitor, ICANS, HLH Screen, Hematologic, Discharge, Clinical Visit
- **Population-level (8):** Population Risk, Mitigation Explorer, Signal Detection, Executive Summary, Clinical Safety Plan, System Architecture, Scientific Basis, Publication Analysis
- Therapy type selector at top (8 therapy types)
- All charts: vanilla SVG, data from API via `fetch()`

## API Endpoints (33)
- Patient: `/api/v1/predict`, `/api/v1/predict/batch`, `/api/v1/scores/easix`, `/api/v1/scores/hscore`, `/api/v1/scores/car-hematotox`, `/api/v1/patient/{patient_id}/timeline`, `/api/v1/models/status`
- Population: `/api/v1/population/risk`, `/api/v1/population/bayesian`, `/api/v1/population/mitigations`, `/api/v1/population/mitigations/strategies`, `/api/v1/population/evidence-accrual`, `/api/v1/population/trials`, `/api/v1/population/comparison`
- Signals: `/api/v1/signals/faers`
- CDP/CSP: `/api/v1/cdp/monitoring-schedule`, `/api/v1/cdp/eligibility-criteria`, `/api/v1/cdp/stopping-rules`, `/api/v1/cdp/sample-size`
- Knowledge: `/api/v1/knowledge/pathways`, `/api/v1/knowledge/pathways/{pathway_id}`, `/api/v1/knowledge/mechanisms`, `/api/v1/knowledge/targets`, `/api/v1/knowledge/cells`, `/api/v1/knowledge/references`, `/api/v1/knowledge/overview`
- Publication: `/api/v1/publication/analysis`, `/api/v1/publication/figures/{figure_name}`
- Narratives: `/api/v1/narratives/generate`, `/api/v1/narratives/patient/{patient_id}/briefing`
- System: `/api/v1/system/architecture`, `/api/v1/therapies`, `/api/v1/health`

## Claude AI Integration (see `docs/claude-integration-options.md`)
Five integration paths planned:
1. **API Narratives** — `?include_narrative=true` on endpoints for Claude-generated clinical interpretations
2. **Dashboard Chat** — `POST /api/v1/chat` with collapsible AI panel, context-aware per active tab
3. **Report Generation** — DSUR, IND narratives, periodic safety reports per ICH E2F
4. **MCP Server** — Expose all PSP endpoints as MCP tools for Claude Desktop/Code
5. **Agent SDK** — Autonomous safety monitoring, FAERS surveillance, clinical Q&A agents

## Agent Team Delegation Pattern
When delegating to agent teams:
- **Visualization agents**: Build SVG dashboards, read existing `index.html` patterns first
- **Model agents**: Work in `src/models/`, run tests after changes
- **Knowledge agents**: Update `src/data/knowledge/`, link everything to PubMed IDs
- **gpuserver1 agents**: SSH to `alton@192.168.1.100`, pull repo, run heavy computation, save results to `analysis/`
- **Critic agents**: Read actual code before reviewing, be specific (file:line references)
- Always run `python -m pytest tests/ -q` after code changes
- Commit and push frequently from Rocinante

## Git & Deployment
- **Repo:** https://github.com/alto84/safety-research-system.git
- **Branch:** master
- Push from Rocinante (has credentials). gpuserver1 pulls.
- **gpuserver1:** `ssh alton@192.168.1.100` — RTX 5090, 128GB RAM, runs tests, heavy computation
- **Server:** `python run_server.py` → http://localhost:8000/clinical
- Commit and push frequently. Document state in SESSION-STATE.md.

## What NOT To Do
- Do not reference AstraZeneca, personal names, or internal data
- Do not hardcode adverse event types — use configuration/registry patterns
- Do not add external JS/CSS dependencies — keep vanilla
- Do not create files without clear purpose (no file bloat)
- Do not over-engineer — working code that solves the problem beats elegant code that doesn't
- Do not fabricate data or statistics — all claims must be evidence-based
- Do not skip PubMed references for scientific claims
