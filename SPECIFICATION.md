# Predictive Safety Platform — System Specification

> **Version:** 1.0 | **Date:** 2026-02-07
> **Repository:** https://github.com/alto84/safety-research-system
> **Status:** Active Development (Phase 1 complete, Phase 2 in progress)

---

## 1. Executive Summary

The Predictive Safety Platform (PSP) is an open-source, data-agnostic system for estimating, monitoring, and mitigating adverse event risk in advanced cell therapies. Starting with CAR-T therapy in systemic lupus erythematosus (SLE), the platform is designed to extend to any cell therapy, any adverse event, any data source, and any timescale.

**Core value proposition:** Transform fragmented safety data into unified, quantitative, evidence-graded risk assessments that evolve as new data accrues — from early development through post-marketing.

**Design for internalization:** Built entirely on public data and open models. Architected so that pharmaceutical companies can internalize the system with their proprietary data (clinical databases, internal safety reports, registry data) to produce company-specific risk models without modifying core platform logic.

---

## 2. Design Philosophy

### 2.1 Data Agnosticism
The platform accepts **any structured safety data** without hardcoded assumptions about specific adverse events, treatments, or data sources. Core analytical modules operate on generic interfaces:

- **Bayesian risk module:** Accepts any `(prior, events, n)` tuple — works for CRS, ICANS, ICAHS, cardiac toxicity, secondary malignancy, or any future AE type
- **Mitigation module:** Accepts any `(strategy_id, relative_risk, target_aes, correlation_matrix)` — works for tocilizumab, corticosteroids, or any future intervention
- **Signal detection:** Accepts any `(product, adverse_event, reporting_database)` — works for FAERS, EudraVigilance, VigiBase, or internal safety databases
- **Evidence accrual:** Accepts any `(timeline_of_studies, event_counts)` — works for any trial program or pooled analysis

### 2.2 Extensibility Model
New capabilities plug in via **configuration registries**, not code changes:

| Extension Point | Mechanism | Example |
|----------------|-----------|---------|
| New adverse event | Add to AE registry (`data/sle_cart_studies.py`) | LICATS, cardiac toxicity, secondary malignancy |
| New treatment | Add to treatment registry | CAR-T for myasthenia gravis, TCR-T, NK cell therapy |
| New data source | Add `DataSource` entry + adapter | CIBMTR registry, internal clinical database |
| New mitigation | Add `MitigationStrategy` entry + correlations | Ruxolitinib, dasatinib, prophylactic regimens |
| New time horizon | Extend `StudyDataPoint` timeline | 5-year follow-up, post-marketing surveillance |
| New scoring model | Implement model interface, register in ensemble | Custom ML model, neural network, rule-based system |

### 2.3 Modularity
Each analytical module is a standalone Python module with:
- **No cross-module imports** (except through the API layer)
- **Pure function interfaces** (dataclass in → dataclass out)
- **No global state** (all configuration passed explicitly)
- **Independent testability** (each module has its own test suite)

### 2.4 Evidence Grading
Every output carries:
- **Point estimate** with **95% credible/confidence interval**
- **Evidence grade** (Strong / Moderate / Limited / Insufficient)
- **Source attribution** (which studies, which databases)
- **Limitations and caveats** surfaced to the user
- **Sample size and statistical power** context

---

## 3. System Architecture

### 3.1 Layer Diagram

```
+--------------------------------------------------------------+
|                     DASHBOARD (HTML/JS)                       |
|  Patient Scoring | Population Risk | Trials | Signals | Exec |
+--------------------------------------------------------------+
                            |
                     REST API (FastAPI)
                            |
+--------------------------------------------------------------+
|                    API LAYER (src/api/)                        |
|  app.py | schemas.py | population_routes.py | middleware.py   |
+--------------------------------------------------------------+
                            |
        +-------------------+-------------------+
        |                   |                   |
+-------+------+   +-------+------+   +--------+-----+
| PATIENT-LEVEL|   |POPULATION-LVL|   |  SIGNALS     |
| src/models/  |   | src/models/  |   | src/models/  |
| biomarker_   |   | bayesian_    |   | faers_       |
|  scores.py   |   |  risk.py     |   |  signal.py   |
| ensemble_    |   | mitigation_  |   +--------------+
|  runner.py   |   |  model.py    |
+--------------+   +--------------+
        |                   |
+-------+-------------------+-------+
|          DATA LAYER               |
| data/sle_cart_studies.py          |
| src/data/graph/knowledge_graph.py |
| config/*.yaml                     |
+-----------------------------------+
```

### 3.2 Component Inventory

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| **FastAPI App** | `src/api/app.py` | 1079 | Main server, middleware stack, patient-level routes |
| **Population Routes** | `src/api/population_routes.py` | 572 | 8 population-level API endpoints |
| **Schemas** | `src/api/schemas.py` | 478 | Pydantic request/response validation |
| **Bayesian Risk** | `src/models/bayesian_risk.py` | 307 | Beta-Binomial posteriors, evidence accrual |
| **Mitigation Model** | `src/models/mitigation_model.py` | 555 | Correlated RR combination, Monte Carlo |
| **FAERS Signal** | `src/models/faers_signal.py` | 940 | PRR/ROR/EBGM, openFDA integration |
| **Clinical Data** | `data/sle_cart_studies.py` | 795 | 14 AE rates, 14 trials, 8 data sources |
| **Biomarker Scoring** | `src/models/biomarker_scores.py` | ~600 | CRS/ICANS/HLH scoring algorithms |
| **Ensemble Runner** | `src/models/ensemble_runner.py` | ~400 | Multi-model weighted ensemble |
| **Knowledge Graph** | `src/data/graph/knowledge_graph.py` | ~500 | Safety knowledge graph with pathways |
| **Safety Index** | `src/safety_index/index.py` | ~300 | Unified safety score across domains |
| **Dashboard** | `src/api/static/index.html` | ~2000 | Single-page HTML dashboard |
| **Tests** | `tests/` | 421+ tests | Unit, integration, safety, stress, validation |

### 3.3 API Endpoints

#### Patient-Level (existing)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/predict` | Full patient risk prediction |
| POST | `/api/v1/score/crs` | CRS-specific scoring |
| POST | `/api/v1/score/icans` | ICANS-specific scoring |
| POST | `/api/v1/score/hlh` | HLH scoring (HScore) |
| GET | `/api/v1/health` | System health check |
| GET | `/api/v1/models` | Available models |

#### Population-Level (new)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/population/risk` | SLE baseline risk summary with mitigated estimates |
| POST | `/api/v1/population/bayesian` | Custom Bayesian posterior computation |
| POST | `/api/v1/population/mitigations` | Correlated mitigation analysis with Monte Carlo |
| GET | `/api/v1/population/evidence-accrual` | Sequential Bayesian evidence accrual timeline |
| GET | `/api/v1/population/trials` | Clinical trial registry with status |
| GET | `/api/v1/population/mitigations/strategies` | Available mitigation strategies |
| GET | `/api/v1/population/comparison` | Cross-indication AE rate comparison |

#### Signal Detection
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/signals/faers` | FAERS disproportionality analysis |

---

## 4. Analytical Models

### 4.1 Bayesian Beta-Binomial Risk Model

**Purpose:** Estimate the true population rate of serious adverse events from sparse early-phase data.

**Method:** Conjugate Beta-Binomial framework.
- **Prior:** Beta(alpha, beta) — derived from discounted oncology CAR-T incidence
- **Likelihood:** Binomial(events | n, theta)
- **Posterior:** Beta(alpha + events, beta + n - events)
- **CI:** Exact Beta quantiles via `scipy.stats.beta.ppf(0.025, a, b)` and `ppf(0.975, a, b)`

**Current priors:**
| AE Type | Prior | Source | Rationale |
|---------|-------|--------|-----------|
| CRS G3+ | Beta(0.21, 1.29) | Discounted ~14% oncology | 85% discount for lower-dose autoimmune context |
| ICANS G3+ | Beta(0.14, 1.03) | Discounted ~12% oncology | 88% discount |
| ICAHS | Beta(0.5, 0.5) | Jeffreys non-informative | Novel AE, no prior data |

**Evidence accrual:** Sequential posterior updates across 7 timepoints (4 observed, 3 projected) showing CI narrowing from n=5 to n=200.

**Extensibility:** Any `(PriorSpec, events, n)` can be passed. New AE types just need a prior specification.

### 4.2 Correlated Mitigation Combination Model

**Purpose:** Estimate combined risk reduction from multiple interventions, accounting for mechanistic correlation.

**Core formula:**
```
RR_combined = (RR_a * RR_b)^(1-rho) * min(RR_a, RR_b)^rho
```

Where:
- `rho = 0` → multiplicative independence (different mechanisms)
- `rho = 1` → full redundancy (same mechanism, take the best)
- `0 < rho < 1` → partial overlap (geometric interpolation)

**Multi-strategy combination:** Greedy pairwise algorithm — combine the most-correlated pair first, replace with synthetic entry, repeat.

**Uncertainty propagation:** Monte Carlo simulation (5K default samples):
- Baseline risk: Beta-sampled from posterior
- Relative risks: LogNormal-sampled from strategy CI
- Output: Distribution of mitigated risk with percentile-based CI

**Current strategies:**
| Strategy | RR | Evidence | Target AEs |
|----------|------|----------|------------|
| Tocilizumab | 0.45 | Strong (oncology-derived) | CRS |
| Corticosteroids | 0.55 | Moderate (oncology-derived) | ICANS |
| Anakinra | 0.65 | Limited (preclinical) | CRS, ICANS |
| Dose reduction | 0.15 | Strong | CRS, ICANS, ICAHS |
| Lymphodepletion mod | 0.85 | Limited | CRS |

**Correlation matrix:**
| Pair | rho | Rationale |
|------|-----|-----------|
| Anakinra + Corticosteroids | 0.3 | Partial overlap in anti-inflammatory pathways |
| Anakinra + Tocilizumab | 0.4 | IL-1/IL-6 cascade overlap |
| Corticosteroids + Tocilizumab | 0.5 | Both target cytokine-driven inflammation |

### 4.3 FAERS Signal Detection

**Purpose:** Detect safety signals from post-marketing spontaneous reports.

**Methods:**
- **PRR (Proportional Reporting Ratio):** Signal if PRR >= 2, chi-squared p < 0.05, N >= 3
- **ROR (Reporting Odds Ratio):** Signal if lower 95% CI > 1
- **EBGM (Empirical Bayes Geometric Mean):** Multi-item Gamma-Poisson Shrinker, signal if EBGM05 >= 2

**Signal classification:**
- Strong: All 3 methods positive
- Moderate: 2 of 3 positive
- Weak: 1 of 3 positive
- None: No methods positive

**Data source:** openFDA API with rate limiting (40 req/min) and 15-min caching.

### 4.4 Patient-Level Ensemble Model

**Purpose:** Score individual patient risk for CRS, ICANS, and HLH based on biomarkers, vitals, and clinical context.

**Components:**
- Biomarker scoring (CRS: ferritin, CRP, IL-6, LDH; ICANS: platelet count, fibrinogen)
- HScore calculation (temperature, organomegaly, cytopenias, ferritin, triglycerides, fibrinogen, AST)
- Cytokine-based models (IFN-gamma, IL-13, MIP-1alpha, MCP-1)
- Knowledge graph pathway scoring
- Ensemble weighted combination with calibration

### 4.5 Safety Index

**Purpose:** Unified safety score across multiple signal domains.

**Domains:**
1. Biomarker signals (patient-level lab/cytokine scores)
2. Pathway signals (knowledge graph activation patterns)
3. Model ensemble signals (weighted multi-model prediction)
4. Clinical context signals (demographics, comorbidities, prior therapies)
5. Population context signals (Bayesian posterior, evidence accrual state)

---

## 5. Data Architecture

### 5.1 Data Source Registry

| # | Source | Type | Coverage | CAR-T Data | Autoimmune CAR-T |
|---|--------|------|----------|------------|------------------|
| 1 | Published Literature | Literature | Global | Yes | Yes (47 patients) |
| 2 | FAERS | Spontaneous Reporting | US | Yes (approved products) | No (pre-approval) |
| 3 | CIBMTR | Registry | US/Global | Yes (transplant/cell therapy) | Limited |
| 4 | EudraVigilance | Spontaneous Reporting | EU | Yes | No |
| 5 | Investigator-Sponsored Trials | Trial Database | Site-specific | Yes | Yes |
| 6 | WHO VigiBase | Spontaneous Reporting | Global | Yes | Minimal |
| 7 | TriNetX | RWD (EHR) | 150M+ patients | Yes | No |
| 8 | Optum CDM | RWD (Claims+EHR) | 67M+ US patients | Yes | No |

### 5.2 Clinical Data Layer

**Current data (from published literature):**
- 14 adverse event rate entries (8 SLE + 6 oncology comparators)
- 14 clinical trial entries (8 autoimmune + 6 oncology)
- Pooled SLE analysis: n=47 patients, CRS G3+ 2.1%, ICANS G3+ 0.0%
- Oncology comparators: ZUMA-1, JULIET, TRANSCEND, ELIANA, KarMMa, CARTITUDE-1

**Evidence accrual timeline:** 7 timepoints (2022-2028), 4 observed + 3 projected, cumulative n=5 to n=200

### 5.3 Knowledge Graph

**Structure:** Directed graph of safety-relevant entities and relationships.
- **Node types:** AdverseEvent, Biomarker, Pathway, Intervention, CellType, Cytokine
- **Edge types:** causes, indicates, treats, correlates_with, part_of
- **Key pathways:** CRS (IL-6 amplification loop), ICANS (BBB disruption), ICAHS (macrophage activation)

---

## 6. Dashboard Specification

### 6.1 Navigation Structure

```
[Patient Assessment] [Population Risk] [Signal Detection] [Trials] [Executive Summary]
```

### 6.2 Patient Assessment Tab
- **Input form:** Demographics, vitals, lab values, clinical context, product info
- **Risk scores:** CRS risk (gauge), ICANS risk (gauge), HLH probability (gauge)
- **Ensemble output:** Composite safety index with domain contributions
- **Recommendations:** Monitoring frequency, intervention thresholds

### 6.3 Population Risk Tab
- **Evidence accrual chart:** Line plot of posterior mean + 95% CI band over time (CRS, ICANS)
  - X-axis: Study timeline (quarters), Y-axis: Rate (%), shaded CI bands
  - Observed vs projected distinction (solid vs dashed)
- **Forest plot:** Cross-indication AE rate comparison (SLE vs oncology products)
  - Horizontal bars with point estimate + CI, grouped by indication
- **Mitigation explorer:** Interactive selection of strategies, live-computed combined RR
  - Correlation adjustment visualization, Monte Carlo CI
- **Baseline risk summary:** Card layout with key metrics and evidence grades

### 6.4 Signal Detection Tab
- **FAERS heatmap:** Product x AE matrix, color-coded by signal strength
- **Signal details:** PRR, ROR, EBGM with confidence intervals per signal
- **Trend monitoring:** Time series of report counts (when available)

### 6.5 Clinical Trials Tab
- **Trial tracker:** Table with status (Recruiting/Active/Completed), enrollment, NCT ID
- **Pipeline visualization:** Bubble chart of trials by phase and indication
- **Enrollment progress:** Bar chart of cumulative enrollment over time

### 6.6 Executive Summary Tab
- **One-page briefing:** Key safety metrics, risk-benefit context
- **Traffic light indicators:** Green/Yellow/Red for each AE category
- **Decision support:** Recommended monitoring strategy, escalation triggers
- **Export capability:** PDF/print-friendly layout

### 6.7 Design Requirements
- **Framework:** Vanilla HTML/CSS/JS with Chart.js for charts (no build tools)
- **Responsive:** Works on desktop (1920px) and tablet (768px)
- **Theming:** Professional clinical appearance, dark header, white content area
- **Loading states:** Skeleton screens while API calls complete
- **Error handling:** Graceful degradation if API endpoints are unavailable
- **Accessibility:** WCAG 2.1 AA compliance

---

## 7. Extensibility Roadmap

### 7.1 Near-Term (Current Sprint)
- Complete dashboard with all 5 tabs
- Unit tests for population-level modules
- Integration tests for all API endpoints
- Fix remaining expert review issues

### 7.2 Medium-Term (Next 2-4 Weeks)
- **New indications:** Add myasthenia gravis, idiopathic inflammatory myopathies, systemic sclerosis
- **New AE types:** LICATS (liver), cardiac toxicity, secondary malignancy, prolonged cytopenias
- **New data adapters:** CIBMTR integration, EudraVigilance API, ClinicalTrials.gov API (live queries)
- **Stopping rules:** Integrate Bayesian monitoring boundaries (futility + efficacy) into evidence accrual
- **Prior sensitivity analysis:** Sweep prior choices, report posterior sensitivity

### 7.3 Long-Term (Internalization Path)
- **Private data integration:** Plug in company clinical databases, internal safety reports
- **Model fine-tuning:** Re-estimate priors from internal data, adjust mitigation RRs from company trials
- **Regulatory submission support:** Generate ICH E2E-compliant safety summaries
- **Real-time monitoring:** Live FAERS/EudraVigilance feeds with automated signal alerts
- **Multi-therapy expansion:** TCR-T, NK cell therapy, gene therapy, bispecific antibodies

---

## 8. Technical Requirements

### 8.1 Runtime
- **Python:** 3.11+ (tested on 3.13)
- **Key dependencies:** FastAPI, uvicorn, pydantic, scipy, httpx (for FAERS)
- **Optional:** Chart.js (CDN, loaded in dashboard)
- **No database required** — all data in Python modules and YAML configs

### 8.2 Deployment
- **Development:** `python run_server.py` (uvicorn on port 8000)
- **Production consideration:** Behind reverse proxy (nginx), with API key auth enabled
- **GPU server:** Heavy computation (Monte Carlo, GNN embeddings) offloaded to gpuserver1

### 8.3 Testing
- **Framework:** pytest with coverage
- **Test categories:** unit, integration, safety, stress, validation
- **Current coverage:** 421 tests, <2s runtime
- **CI/CD:** Not yet configured (manual push + test)

### 8.4 Security
- **Input validation:** Pydantic field validators with clinical-range constraints
- **API auth:** Optional API key middleware
- **CORS:** Configurable (currently permissive for development)
- **No secrets in code:** All configuration via environment variables or config files
- **No PII:** System processes aggregate clinical data, never individual patient identifiers

---

## 9. Quality Assurance

### 9.1 Expert Reviews Completed
| Reviewer | Verdict | Key Finding |
|----------|---------|-------------|
| Biostatistician | 7 critical issues | Normal approximation replaced with exact Beta quantiles |
| Pharmacovigilance Officer | Research-grade, not regulatory | Need ICSR module, secondary malignancy tracking |
| Software Architect | A- architecture | Missing routes (now fixed), Monte Carlo performance |
| Clinical Safety Physician | 8 must-fix issues | ICANS rate inconsistency (fixed), evidence grade caveats (fixed) |

### 9.2 Mathematical Verification
- Beta-Binomial posterior: Verified against hand calculations
- Correlated RR formula: Verified at boundary conditions (rho=0 → multiplicative, rho=1 → min)
- Monte Carlo convergence: 5K samples converge within +/-0.5pp of analytical solution
- Evidence accrual: Sequential updates verified (no double-counting after fix)

---

## 10. Success Criteria

1. **Unified platform** serving patient-level and population-level risk assessment from a single API
2. **Data-agnostic core** that works for any AE type, treatment, and data source
3. **Evidence-graded outputs** with uncertainty quantification on every estimate
4. **Interactive dashboard** suitable for clinical, regulatory, and executive audiences
5. **Extensible architecture** ready for new indications, data sources, and commercial internalization
6. **Mathematical correctness** verified by domain expert review
7. **Public and reproducible** — all data from published sources, all code open-source

---

*Generated 2026-02-07 by Predictive Safety Platform development system*
