# Safety Research System — Agent Instructions

## Project Identity
This is an **open-source Simulated Patient Safety** for cell therapy adverse event risk estimation.
It is **fully independent** — no proprietary data, no personal references, no company-internal information.
All data comes from published literature, public registries (ClinicalTrials.gov), and public APIs (openFDA).

## Architecture
- **Backend:** Python 3.13 + FastAPI (single server, four route groups: patient-level, population-level, patient-safety/PSD, system)
- **Frontend:** Single-page HTML dashboard in `src/api/static/index.html` (vanilla JS, no build tools, ~8400+ lines)
- **Models:** `src/models/` — 7-model risk registry, Bayesian risk, correlated mitigation, FAERS signal detection, ensemble scoring, model validation, AE classifier (SapBERT), secondary malignancy detection
- **Data:** `data/sle_cart_studies.py` — curated clinical data; `data/cell_therapy_registry.py` — 12 therapy types, 21 AE profiles
- **Knowledge Graph:** `src/data/knowledge/` — 4 signaling pathways, 47 directed steps, 15 molecular targets, 9 cell types, 25 PubMed references, 9 mechanism chains
- **Tests:** `tests/` — pytest, 2313+ tests, run with `python -m pytest tests/ -q`
- **API:** `src/api/` — FastAPI app with 76+ endpoints, Pydantic schemas, rate-limiting middleware
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
| `ae_classifier.py` | SapBERT-based AE term classification, 13 MedDRA categories, 470 terms | `classify_ae_term()`, `embed_ae_terms()`, `get_model_status()` |
| `secondary_malignancy.py` | FDA boxed warning tracker, 10 signals, 6 CAR-T products | `assess_secondary_malignancy_risk()`, `get_monitoring_protocol()` |
| `temporal_signal.py` | FAERS temporal signal evolution, 6 products x 4 AE categories, regulatory milestones | `get_temporal_profile()`, `get_all_temporal_profiles()`, `get_regulatory_timeline()` |
| `patient_safety_routes.py` | PSD (Prosinertimib) — 13 endpoints for Head of Patient Safety dashboard | org roles, signals, compliance, KPIs, AI intelligence, chat |

## Knowledge Graph (`src/data/knowledge/`)
| Module | Content |
|--------|---------|
| `references.py` | 25 publications with PubMed IDs, evidence grades |
| `cell_types.py` | 9 cell populations with markers, activation states, AE roles |
| `molecular_targets.py` | 15 druggable targets with modulators, pathway membership |
| `pathways.py` | 4 cascades: CRS IL-6 trans-signaling, ICANS BBB disruption, IEC-HS IFN-γ/IL-18 feedback, TNF/NF-kB amplification |
| `mechanisms.py` | 9 therapy-to-AE chains (CAR-T CD19 CRS/ICANS/IEC-HS, TCR-T, CAR-NK, gene therapy, secondary malignancy) |
| `graph_queries.py` | Query API: `get_pathway_for_ae()`, `get_intervention_points()`, `get_mechanism_chain()` |
| `integration.py` | Knowledge-to-model bridge: `get_mechanistic_context()`, `get_narrative_context()` |

## Dashboards
- **Clinical Dashboard** (`/clinical`, 26 tabs): Patient-level (9) + Population-level (10) + Pharma simulation tabs. Vanilla JS + SVG.
- **Patient Safety Dashboard** (`/psd`, 16 sections): Head of Patient Safety view for Prosinertimib (EGFR TKI, NSCLC). Org chart, signals, compliance, KPIs, AI intelligence, chat panel.

## API Endpoints (71+)
- Patient: `/api/v1/predict`, `/api/v1/predict/batch`, `/api/v1/scores/easix`, `/api/v1/scores/hscore`, `/api/v1/scores/car-hematotox`, `/api/v1/patient/{patient_id}/timeline`, `/api/v1/models/status`
- Population: `/api/v1/population/risk`, `/api/v1/population/bayesian`, `/api/v1/population/mitigations`, `/api/v1/population/mitigations/strategies`, `/api/v1/population/evidence-accrual`, `/api/v1/population/trials`, `/api/v1/population/comparison`
- Signals: `/api/v1/signals/faers`, `/api/v1/signals/secondary-malignancy`, `/api/v1/signals/secondary-malignancy/monitoring-protocol`, `/api/v1/signals/secondary-malignancy/{product_name}`, `/api/v1/signals/temporal-evolution`, `/api/v1/signals/temporal-evolution/{product_name}`, `/api/v1/signals/regulatory-timeline`
- ML: `/api/v1/classify-ae`
- CDP/CSP: `/api/v1/cdp/monitoring-schedule`, `/api/v1/cdp/eligibility-criteria`, `/api/v1/cdp/stopping-rules`, `/api/v1/cdp/sample-size`
- Knowledge: `/api/v1/knowledge/pathways`, `/api/v1/knowledge/pathways/{pathway_id}`, `/api/v1/knowledge/mechanisms`, `/api/v1/knowledge/targets`, `/api/v1/knowledge/cells`, `/api/v1/knowledge/references`, `/api/v1/knowledge/overview`, `/api/v1/knowledge/graph`
- Publication: `/api/v1/publication/analysis`, `/api/v1/publication/figures/{figure_name}`
- Narratives: `/api/v1/narratives/generate`, `/api/v1/narratives/patient/{patient_id}/briefing`
- PSD: `/api/v1/psd/overview`, `/api/v1/psd/org-roles`, `/api/v1/psd/signal-portfolio`, `/api/v1/psd/regulatory-compliance`, `/api/v1/psd/risk-actions`, `/api/v1/psd/meeting-tracker`, `/api/v1/psd/kpis`, `/api/v1/psd/inspection-readiness`, `/api/v1/psd/resource-budget`, `/api/v1/psd/product-lifecycle`, `/api/v1/psd/vendor-oversight`, `/api/v1/psd/ai-intelligence`, `POST /api/v1/psd/chat`
- System: `/api/v1/system/architecture`, `/api/v1/therapies`, `/api/v1/health`

## Claude AI Integration (see `docs/claude-integration-options.md`)
Five integration paths planned:
1. **API Narratives** — `?include_narrative=true` on endpoints for Claude-generated clinical interpretations
2. **Dashboard Chat** — `POST /api/v1/chat` with collapsible AI panel, context-aware per active tab
3. **Report Generation** — DSUR, IND narratives, periodic safety reports per ICH E2F
4. **MCP Server** — Expose all SPS endpoints as MCP tools for Claude Desktop/Code
5. **Agent SDK** — Autonomous safety monitoring, FAERS surveillance, clinical Q&A agents

## Agent Team Delegation Pattern

**Default approach: Use agent teams aggressively.** When a task has multiple independent parts, spin up a team with `TeamCreate` and launch parallel agents via `Task` with `team_name` and `run_in_background: true`. This applies to:
- **Research & exploration** — Multiple agents reading different parts of the codebase simultaneously
- **Implementation** — Parallel agents working on independent modules (models, tests, frontend, data)
- **Review & validation** — Critic agents examining different aspects in parallel
- **Creative brainstorming** — Each agent explores a different angle, reports findings back

### Agent Role Templates
- **Visualization agents**: Build SVG dashboards, read existing `index.html` patterns first
- **Model agents**: Work in `src/models/`, run tests after changes
- **Knowledge agents**: Update `src/data/knowledge/`, link everything to PubMed IDs
- **gpuserver1 agents**: SSH to `alton@192.168.1.100`, pull repo, run heavy computation, save results to `analysis/`
- **Critic agents**: Read actual code before reviewing, be specific (file:line references)
- **Research agents**: Deep-dive into specific modules, report findings via `SendMessage`
- **Test agents**: Write and run tests for specific modules independently

### Team Workflow
1. `TeamCreate` with descriptive name
2. `TaskCreate` for each independent work item
3. Launch agents in parallel with `Task` (set `team_name`, `run_in_background: true`)
4. Agents report back via `SendMessage` to team lead
5. Team lead synthesizes findings, assigns follow-up tasks
6. `SendMessage` type `shutdown_request` when done, then `TeamDelete`

### Rules
- Always run `python -m pytest tests/ -q` after code changes
- Commit and push frequently from Rocinante
- Agents should read actual code before making changes or recommendations
- Push agents to their limits — use the full context window, read deeply, be thorough

## Git & Deployment
- **Repo:** https://github.com/alto84/safety-research-system.git
- **Branch:** master
- Push from Rocinante (has credentials). gpuserver1 pulls.
- **gpuserver1:** `ssh alton@192.168.1.100` — RTX 5090, 128GB RAM, runs tests, heavy computation
- **Server:** `python run_server.py` or `start.bat` → http://localhost:8000 (Clinical: `/clinical`, PSD: `/psd`)
- Commit and push frequently.

## Pharma Company Simulation (CEO Mission)

This project includes a simulated pharmaceutical company organizational structure
implemented as recursive AI agent teams. The CEO (top-level agent) delegates to
C-suite roles, who delegate to VPs, who delegate to operational leads.

### Organizational Hierarchy
```
CEO
├── CMO (Chief Medical Officer)
│   ├── VP Clinical Operations
│   ├── VP Medical Affairs
│   ├── Head of Patient Safety / Pharmacovigilance
│   ├── Therapeutic Area Head, Oncology (NSCLC/EGFR)
│   ├── VP Regulatory Affairs
│   ├── Head of Biostatistics
│   └── Head of Clinical Development
├── Head of CMC / Manufacturing
├── Head of Quality Assurance
└── Head of Commercial / Market Access
```

### Governing Frameworks
All agent behaviors are grounded in real regulatory frameworks:
- **Clinical Trials:** ICH E6(R3) GCP, ICH E8(R1), 21 CFR Parts 11/50/56/312
- **Pharmacovigilance:** ICH E2A-E2F, 21 CFR 312.32/314.80, CIOMS I-VI
- **Cell Therapy Specific:** FDA CBER guidances, 21 CFR 1271, PHS Act §351
- **Quality:** ICH Q1-Q12, 21 CFR 210/211/600, EU GMP Annex 1
- **Ethics:** Declaration of Helsinki, Belmont Report, 45 CFR 46 (Common Rule)
- **Biostatistics:** ICH E9(R1), FDA adaptive design guidance
- **Regulatory Submissions:** ICH CTD (M4), eCTD format, FDA BLA pathway

### Skill Library
Agent skills live in `.claude/skills/pharma/` organized by role.
Each skill is a reusable prompt template with:
- Regulatory grounding (which guidance applies)
- Input/output specification
- Escalation path (who to report to)
- Dashboard visualization (which tab shows output)

### Dashboard Tabs for Pharma Simulation
Tabs beyond the original 17 are pharma simulation tabs:
- **Org Chart**: Interactive hierarchy showing agent roles, status, current tasks
- **Regulatory Map**: Which regulations apply to which activities
- **Clinical Pipeline**: IND → Phase I → Phase II → Phase III → BLA timeline
- **PV Dashboard**: Pharmacovigilance signal detection, ICSR tracking, PSUR status
- **Quality Metrics**: GxP compliance, CAPA tracking, audit readiness

### Agent Communication Pattern
- Agents report UP (to their manager agent) with structured status updates
- Agents delegate DOWN with specific task descriptions + regulatory context
- Cross-functional coordination through the CEO agent (this level)
- All decisions reference the governing framework that applies

## What NOT To Do
- Do not reference AstraZeneca, personal names, or internal data
- Do not hardcode adverse event types — use configuration/registry patterns
- Do not add external JS/CSS dependencies — keep vanilla
- Do not create files without clear purpose (no file bloat)
- Do not over-engineer — working code that solves the problem beats elegant code that doesn't
- Do not fabricate data or statistics — all claims must be evidence-based
- Do not skip PubMed references for scientific claims
