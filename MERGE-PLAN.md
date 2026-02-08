# Comprehensive Merge Plan: Predictive Safety Platform

> **Status:** Draft | **Date:** 2026-02-07
> **Source Repos:** Sartor-claude-network (PSP dashboard), safety-research-system (target)
> **Objective:** Merge the best of both repos into a unified Predictive Safety Platform for CAR-T safety in autoimmune indications

---

## Phase 0: Foundation (Current — In Progress)

### 0.1 Port Core Python Modules (PARALLEL)
- [x] `src/models/bayesian_risk.py` — Beta-Binomial framework, evidence accrual (Agent running)
- [x] `src/models/mitigation_model.py` — Correlated mitigation correction, Monte Carlo (Agent running)
- [x] `data/sle_cart_studies.py` — Clinical data layer (Agent running)
- [x] `src/models/faers_signal.py` — FAERS signal detection (Agent running)
- [x] `src/api/schemas.py` — Population-level Pydantic schemas (Done)

### 0.2 Wire Population API Endpoints
- [ ] `src/api/population_routes.py` — FastAPI router for population-level endpoints
- [ ] Register router in `src/api/app.py`
- [ ] Test endpoint connectivity

---

## Phase 1: Merge Execution (PARALLEL AGENTS)

### Stream A: Backend Integration
**Agent Type:** general-purpose (full write access)

1. **API Integration**
   - Wire `bayesian_risk`, `mitigation_model`, `faers_signal` into the FastAPI app
   - Add endpoints: `/api/v1/population/risk`, `/api/v1/population/bayesian`,
     `/api/v1/population/mitigations`, `/api/v1/population/evidence-accrual`,
     `/api/v1/population/trials`, `/api/v1/signals/faers`
   - Ensure CORS, auth middleware, rate limiting apply to new routes
   - Add OpenAPI tags and documentation

2. **Knowledge Graph Enrichment**
   - Port the 16 Sartor knowledge graph markdown files into `src/data/knowledge/`
   - Wire adverse event nodes, mitigation nodes, and trial nodes into the existing KnowledgeGraph
   - Add pathway connections: CRS ↔ IL-6 ↔ tocilizumab, ICANS ↔ BBB ↔ corticosteroids
   - Connect evidence accrual data points to study nodes

3. **Safety Index Enhancement**
   - Add population-level risk domain to the existing Safety Index
   - Connect Bayesian posteriors as a fifth signal domain alongside biomarker, pathway, model, clinical
   - Add mitigation effectiveness as adjustable parameter in risk calculations

### Stream B: Dashboard / Frontend
**Agent Type:** general-purpose (full write access)

1. **Enhanced HTML Dashboard** (extend existing `src/api/static/index.html`)
   - Add population-level tab/section with:
     - Evidence accrual curve (SVG chart showing Bayesian CI narrowing)
     - Forest plot (cross-study AE rate comparison: SLE vs DLBCL vs ALL vs MM)
     - Mitigation explorer (interactive correlated combination calculator)
     - Clinical trial tracker (enrollment status table)
     - FAERS signal monitor (product × AE heatmap)
   - Add executive summary view
   - Add data source inventory with quality assessment
   - Wire all new sections to the population API endpoints via fetch()

2. **Existing Demo Dashboard Updates**
   - Update `demo/index.html` to link to the new population views
   - Add navigation between patient-level (existing) and population-level (new) dashboards

### Stream C: Data Validation & Testing
**Agent Type:** general-purpose

1. **Unit Tests**
   - `tests/unit/test_bayesian_risk.py` — Posterior computation, CI bounds, prior specifications
   - `tests/unit/test_mitigation_model.py` — Correlated formula boundary conditions (rho=0 → multiplicative, rho=1 → min), Monte Carlo convergence
   - `tests/unit/test_faers_signal.py` — PRR/ROR/EBGM computation, signal classification
   - `tests/unit/test_sle_data.py` — Data integrity, sum checks, no missing fields

2. **Integration Tests**
   - `tests/integration/test_population_api.py` — All new endpoints return valid responses
   - `tests/integration/test_end_to_end.py` — Full pipeline: patient biomarkers → ensemble → population context → mitigation recommendation

3. **Mathematical Verification**
   - Verify correlated combination formula at boundary conditions
   - Verify Bayesian posteriors against hand calculations
   - Verify Monte Carlo convergence (10K samples should converge within ±0.5pp)
   - Cross-check adverse event rates against published sources

---

## Phase 2: Expert Persona Review (PARALLEL)

### Reviewer Personas
Each reviewer evaluates the merged codebase from their domain perspective:

1. **Pharmacovigilance Officer** — Reviews FAERS signal detection methodology, disproportionality metrics, signal classification thresholds. Checks regulatory alignment (ICH E2E, FDA Guidance).

2. **Biostatistician** — Reviews Bayesian framework (prior elicitation, posterior computation, CI approximation), correlated mitigation model (formula derivation, boundary conditions), Monte Carlo implementation, evidence accrual methodology.

3. **Clinical Safety Physician** — Reviews adverse event definitions (ASTCT CRS/ICANS grading), mitigation dosing/timing accuracy, clinical trial data accuracy, risk communication in dashboard.

4. **Software Architect** — Reviews code architecture, API design, test coverage, error handling, security (input validation, injection prevention), performance, scalability.

5. **Regulatory Affairs Specialist** — Reviews data provenance, audit trail capability, GxP considerations for clinical decision support, GRADE evidence ratings, limitations disclosures.

### Review Deliverables
Each reviewer produces:
- Strengths (what works well)
- Issues (must-fix before production)
- Recommendations (nice-to-have improvements)
- Risk assessment (what could go wrong)

---

## Phase 3: Data Source Deep Dive (PARALLEL AGENTS)

For each of the 8 data sources in the platform, assess 3-5 ways it could contribute to the risk and efficacy framework. Data sources:

1. **Published Clinical Trial Literature** → Bayesian priors, forest plot data, GRADE assessments
2. **FAERS** → Post-marketing signal detection, rare event discovery, comparative safety
3. **CIBMTR** → Real-world incidence rates, long-term follow-up, safety denominators
4. **EudraVigilance** → EU safety signals, geographic variation in AE reporting
5. **Investigator-Sponsored Trial Databases** → Autoimmune-specific granular data, biomarker correlates
6. **WHO VigiBase** → Global signal confirmation, rare event detection across populations
7. **TriNetX** → Background rate estimation, comorbidity analysis, real-world comparators
8. **Optum CDM** → Long-term outcomes, healthcare utilization, cost-effectiveness data

### Assessment Criteria
For each suggestion, evaluate:
- **Patient impact:** Most likely to reduce adverse event risk across the drug development pipeline
- **Pipeline coverage:** CDP development → early phase → large scale trials → post-marketing
- **Feasibility:** Data access, cost, timeline to integrate
- **Role-specific value:** Different views for statistician, safety physician, regulatory, payer

---

## Phase 4: Upgrade Implementation (PARALLEL)

Implement the top-ranked data source suggestions. Prioritize by patient impact.

### Candidate Upgrades (to be refined after Phase 3)
- Real-time FAERS monitoring with automated signal alerts
- Bayesian network meta-analysis incorporating indirect comparisons
- Background rate estimation from TriNetX for contextualized risk assessment
- CIBMTR long-term follow-up integration for T-cell malignancy risk bounding
- Geographic variation analysis (FAERS vs EudraVigilance) for global filing strategy
- Patient subgroup risk stratification using IST database biomarker correlates
- Decision-analytic model for cost-effectiveness of mitigation strategies
- Stopping rules integration with evidence accrual (futility and efficacy boundaries)

---

## Phase 5: Final Review & Iteration (PARALLEL)

1. **Code Review** — Architecture, security, test coverage, documentation
2. **Dashboard QA** — Visual testing, API connectivity, data accuracy
3. **Clinical Review** — Medical accuracy, appropriate caveats, decision support suitability
4. **gpuserver1 Tasks** — Run computational validation (Monte Carlo convergence, prior sensitivity analysis, Bayesian meta-regression), run full test suite, validate with synthetic patients

---

## Delegation Strategy

### Local (Rocinante) — Orchestration + Frontend
- Plan creation and review
- Schema design
- API endpoint wiring
- Dashboard HTML/JS
- Git operations

### Agent Teams — Parallel Execution
- 3-5 agents per phase working on independent streams
- Each agent gets a focused, self-contained task
- Results merged by orchestrator

### gpuserver1 — Computation + Validation
- Push code to GitHub
- SSH session runs tests, starts server, validates endpoints
- Run heavy computations (Monte Carlo validation, sensitivity analysis)
- Generate synthetic patient cohorts for end-to-end testing
- Claude Code instance follows plan document with checkpoint protocol

### Checkpoints
- After Phase 1: All modules present, API serves responses, basic tests pass
- After Phase 2: Expert feedback incorporated, no must-fix issues remaining
- After Phase 3: Data source analysis complete, upgrade plan ranked
- After Phase 4: Top upgrades implemented, tests passing
- After Phase 5: Final review clean, dashboard functional, ready for demo

---

## Success Criteria

1. **Unified API** — Single FastAPI server serving both patient-level (biomarker scoring) and population-level (Bayesian risk) endpoints
2. **Mathematical Correctness** — All formulas verified at boundary conditions and against published values
3. **Clinical Accuracy** — AE rates, trial data, and mitigation parameters match published sources
4. **Test Coverage** — All new modules have unit tests; integration tests cover API endpoints
5. **Dashboard Functional** — Population-level views render correctly and pull live data from API
6. **Expert Approval** — No must-fix issues from any reviewer persona
7. **Data Source Integration** — At least 3 new data source contributions implemented beyond current baseline
