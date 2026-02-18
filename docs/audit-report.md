# Safety Research System - Code Audit Report

**Date:** 2026-02-17
**Auditor:** Claude Opus 4.6 (automated code review)
**Codebase:** `C:\Users\alto8\safety-research-system`
**Test suite:** 1933 tests passing, 46% overall coverage (32.51s)

---

## Executive Summary

The codebase is well-structured for its maturity level. The API layer is solid with
good schema validation, middleware separation, and OpenAPI documentation. The core
models (`bayesian_risk`, `mitigation_model`, `model_registry`) are well-tested
(88-97% coverage). However, there are significant coverage gaps in the engine/
subsystem (0%), the biomarker_scores module (16%), and the full API endpoint layer
(19%). The 7,788-line monolithic dashboard HTML is the largest UX risk. Security
posture is adequate for a research tool but needs tightening for any production
deployment.

**Priority distribution:** 3 P0, 8 P1, 10 P2, 8 P3

---

## Findings

### P0 - Critical / Must Fix

| # | Category | Description | Suggested Fix | Effort |
|---|----------|-------------|---------------|--------|
| P0-1 | **Security** | CORS is configured with `allow_origins=["*"]` combined with `allow_credentials=True` in `src/api/app.py:193-195`. This is explicitly forbidden by the CORS spec and most browsers will reject it, but some older clients may allow credential leakage to any origin. | Set `allow_origins` to a specific list (e.g., `["http://localhost:8000"]`) or remove `allow_credentials=True` if cookies are not needed. Make this configurable via environment variable. | S |
| P0-2 | **Security** | The `ErrorHandlingMiddleware` in `src/api/middleware.py:251` returns `str(exc)` in the error response body. In production, unhandled exceptions may leak internal paths, database details, or stack information to clients. | Return a generic message to clients; log the full exception server-side only. Add a `DEBUG` mode flag that controls whether detailed errors are returned. | S |
| P0-3 | **Memory Leak** | `_patient_timelines` (`src/api/app.py:86`), `_ws_connections` (`src/api/app.py:90`), and `_request_log` (`src/api/middleware.py:176`) are unbounded in-memory dictionaries that grow indefinitely. Under sustained load or long uptime, these will consume all available memory. `_patient_timelines` appends every prediction result forever. `_request_log` only prunes per-IP on access, so IPs that stop sending requests leave stale entries permanently. | Add TTL-based eviction. For `_patient_timelines`, cap at N entries per patient (e.g., 1000) and/or add a max-age eviction. For `_request_log`, add a periodic cleanup or use a bounded data structure. For `_ws_connections`, this is partially handled but dead connections from non-graceful disconnects may linger. | M |

---

### P1 - High / Should Fix Soon

| # | Category | Description | Suggested Fix | Effort |
|---|----------|-------------|---------------|--------|
| P1-1 | **Test Coverage** | The entire `src/engine/` subsystem (1,620 statements across 9 files) has **0% test coverage**. This includes `core.py`, `alerts.py`, `audit.py`, `ensemble.py`, `gateway.py`, `normalizer.py`, `router.py`, `hypothesis.py`, and `validator.py`. These are non-trivial modules (e.g., `validator.py` is 209 statements with 108 branches). | Write unit tests for each engine module. Start with `core.py` and `alerts.py` as they are referenced by the SafetyEngine initialization path. | L |
| P1-2 | **Test Coverage** | `src/models/biomarker_scores.py` has only **16% coverage** (361 of 460 statements missed). This is the core scoring module implementing 7 published clinical formulas (EASIX, HScore, CAR-HEMATOTOX, Teachey, Hay). The existing `test_biomarker_scores.py` has only 45 test functions -- likely covering only a few models or edge cases. | Expand tests to cover all 7 scoring models with representative inputs, edge cases (zero values, missing fields, boundary thresholds), and expected risk levels. | M |
| P1-3 | **Test Coverage** | `src/models/ensemble_runner.py` has only **28% coverage** (84 of 135 statements missed). The `run()` method (lines 205-266), risk aggregation logic, and warning generation are all untested through integration. | Add tests that exercise the full ensemble pipeline with various data completeness scenarios (full data, partial data, no data). | M |
| P1-4 | **Test Coverage** | `src/api/app.py` has only **19% coverage**. The individual score endpoints (`/scores/easix`, `/scores/hscore`, `/scores/car-hematotox`), the full `/predict` endpoint, batch prediction, timeline retrieval, and WebSocket handler are all untested. | Add integration tests using FastAPI's `TestClient` for each endpoint. The existing `test_api_endpoints.py` appears to test only some routes. | M |
| P1-5 | **Code Quality** | `src/api/population_routes.py` is **3,195 lines** -- a single file containing 25+ route handlers, helper functions, data builders, and hardcoded clinical data (forest plot data, demographics, AE rates). This is the largest single source file and is difficult to navigate, test, and maintain. | Split into multiple route modules by domain: `population_routes.py` (risk, bayesian, mitigations), `knowledge_routes.py` (pathways, mechanisms, targets, cells), `publication_routes.py` (analysis, figures), `cdp_routes.py` (monitoring, eligibility, stopping rules), `pharma_routes.py` (org, simulation). Move hardcoded data builders into a `src/api/publication_data.py` module. | L |
| P1-6 | **Deprecation** | `datetime.utcnow()` is used **28 times** across the codebase (app.py, middleware.py, biomarker_scores.py, engine modules, safety_index). This method is deprecated since Python 3.12 and will be removed in a future version. It also creates naive datetimes without timezone info, which can cause subtle bugs. | Replace all `datetime.utcnow()` with `datetime.now(timezone.utc)`. The population_routes.py module already uses the correct pattern. | S |
| P1-7 | **Code Quality** | The dashboard `src/api/static/index.html` is a **7,788-line monolith** combining HTML, CSS (~1000 lines), and JavaScript (~6500 lines) in a single file. This makes debugging, testing, and collaborative development extremely difficult. No JS testing framework exists for the frontend. | At minimum, extract CSS to `styles.css` and JS to `dashboard.js`. Consider further splitting JS into modules (e.g., `api.js`, `charts.js`, `population-tabs.js`). Add a lightweight test runner for critical JS functions. | L |
| P1-8 | **Inconsistency** | Import paths mix `from data.sle_cart_studies` (top-level `data/`) and `from src.data.*` (inside `src/`) within the same files (`population_routes.py` lines 113 and 120 use `from data.*`, while lines 112, 122-135 use `from src.data.*`). This works because both directories are on the Python path, but it is confusing and fragile. | Standardize all imports to use `from src.data.*` or move top-level `data/` modules into `src/data/`. | S |

---

### P2 - Medium / Plan to Fix

| # | Category | Description | Suggested Fix | Effort |
|---|----------|-------------|---------------|--------|
| P2-1 | **Test Coverage** | `src/safety_index/` (384 statements across 4 files) has **0% coverage**. This includes the core `SafetyIndex` computation, `PatientRiskScorer`, and `PopulationAnalyzer` -- all significant modules. `test_safety_index.py` exists but has only 17 test functions that appear to test only basic instantiation. | Write comprehensive tests for Safety Index computation, domain scoring, risk categorization, and edge cases. | M |
| P2-2 | **Test Coverage** | `src/data/graph/` (370 statements across 3 files) has **0% coverage**. This is the original knowledge graph implementation (`knowledge_graph.py`, `crs_pathways.py`, `schema.py`). While a newer `src/data/knowledge/` module exists with good coverage, the old graph module is still imported by `src/engine/core.py`. | Either write tests for `src/data/graph/` or remove it if it has been superseded by `src/data/knowledge/`. If it is dead code, removing it reduces maintenance burden. | M |
| P2-3 | **Performance** | The batch prediction endpoint (`/api/v1/predict/batch`, `src/api/app.py:601-638`) processes patients **sequentially** in a for loop, calling `await predict()` one at a time. With up to 100 patients allowed, this could be slow. | Use `asyncio.gather()` to run predictions concurrently. Since the actual computation (`_ensemble_runner.run()`) is synchronous, consider using `asyncio.to_thread()` or a thread pool executor for true parallelism. | M |
| P2-4 | **Performance** | `_count_tests()` in `population_routes.py:181-222` scans the entire `tests/` directory tree at runtime, reading and parsing every test file to count test functions. This is called for the `/api/v1/system/architecture` endpoint. It does filesystem I/O on every request with no caching. | Cache the result with a TTL (e.g., 5 minutes) or compute at startup only. The count does not change during runtime unless tests are being actively developed. | S |
| P2-5 | **Performance** | The `_load_analysis_json()` function in `population_routes.py:1835-1847` uses a module-level global cache (`_analysis_cache`) that is never invalidated. While this is good for performance, if the file is updated while the server is running, stale data will be served indefinitely. | Add a file modification timestamp check to invalidate the cache when the file changes, or add a cache-clear admin endpoint. | S |
| P2-6 | **Dashboard UX** | There are **two different fetch patterns** in the dashboard: `apiFetch()` (line 1213) for patient-level calls and `popFetch()` (line 3615) for population-level calls. They have different error handling approaches -- `apiFetch` throws on error, `popFetch` returns `{data, error}`. This inconsistency makes error handling unpredictable. | Consolidate into a single fetch wrapper. The `popFetch` pattern (`{data, error}`) is safer for UI rendering since it avoids unhandled promise rejections. | S |
| P2-7 | **Dashboard UX** | The dashboard has no **retry mechanism** for failed API calls. If the server is temporarily unavailable (e.g., during restart), all tabs show error states with no way to retry except manually navigating away and back. | Add a retry button to error states, and implement automatic retry with exponential backoff for transient failures (5xx, network errors). | S |
| P2-8 | **Dashboard UX** | The sidebar layout uses `grid-template-columns: 320px 1fr` (line 173) which breaks on narrow viewports. The `@media (max-width: 1024px)` rule (line 436) likely hides or stacks the sidebar, but there is no responsive design for tablet-sized screens (768-1024px). | Add intermediate breakpoints and consider a collapsible sidebar that can be toggled on medium screens. | M |
| P2-9 | **Security** | The API key authentication middleware skips auth for any path starting with `/docs` or `/redoc` (line 125-126), but also skips auth entirely for **all static files** since the static mount (`/static/`) is not included in the public paths check, and the check uses `startswith` matching. Any WebSocket upgrade also bypasses auth (comment on line 123 says "Skip auth for WebSocket upgrades" but the code does not actually check for WebSocket). | Explicitly enumerate which paths should bypass auth. Add WebSocket authentication (e.g., token in query parameter or first message). Ensure static file serving does not bypass auth if the dashboard should be protected. | M |
| P2-10 | **Code Quality** | The `_normalise_score()` function in `src/api/app.py:410-433` imports `math` inside the function body on every call. While Python caches module imports, this is a code smell and inconsistent with the module-level imports at the top of the file. | Move `import math` to the top of the file (it is already imported on line 14 -- remove the redundant inline import). | S |

---

### P3 - Low / Nice to Have

| # | Category | Description | Suggested Fix | Effort |
|---|----------|-------------|---------------|--------|
| P3-1 | **Missing Feature** | No **data export** capability. The dashboard visualizes risk data but provides no way to export patient timelines, population analyses, or publication data as CSV/PDF for clinical reports or regulatory submissions. | Add export endpoints (`/api/v1/export/timeline/{patient_id}?format=csv`) and export buttons in the dashboard UI. | M |
| P3-2 | **Missing Feature** | No **audit logging** for API access. While there is an `AuditTrail` class in `src/engine/integration/audit.py`, it is not wired into the API middleware. There is no persistent record of who accessed which patient data and when. For clinical software, this is often a regulatory requirement. | Add audit logging middleware that records request method, path, user (from API key), timestamp, and response status to a persistent store (file or database). | M |
| P3-3 | **Missing Feature** | No **API versioning strategy** beyond the `/api/v1/` prefix. There is no mechanism for deprecating endpoints, no version negotiation, and no documentation of what constitutes a breaking change. | Document the versioning strategy. Add response headers indicating API version and deprecation warnings. Plan for `/api/v2/` migration path. | S |
| P3-4 | **Missing Feature** | No **patient data persistence**. All patient timelines are in-memory (`_patient_timelines` dict) and lost on server restart. The code comments acknowledge this: "replace with database in production" (line 85). | For the research phase, consider SQLite as a minimal persistence layer. This also resolves P0-3 since database storage has natural size management. | L |
| P3-5 | **Dashboard UX** | The dashboard lacks **keyboard navigation** for chart interactions and SVG visualizations. While tab navigation has proper ARIA attributes (`role="tablist"`, `aria-selected`, keyboard arrow key support), the SVG charts and interactive elements within tabs are not keyboard-accessible. | Add `tabindex`, `role`, and `aria-label` attributes to interactive SVG elements. Add keyboard event handlers for chart interactions (tooltip display, data point selection). | M |
| P3-6 | **Code Quality** | The `_classify_node_type()` function in `population_routes.py:1383-1455` uses keyword-matching heuristics to classify pathway nodes. The code's own docstring (lines 1396-1410) acknowledges this is fragile, order-dependent, and should be stored as a field in the data structure. | Add a `node_type` field to the `PathwayStep` dataclass in `src/data/knowledge/pathways.py` and populate it at data definition time rather than inferring it at render time. | M |
| P3-7 | **Code Quality** | Several response models in `population_routes.py` return raw `dict` instead of Pydantic response models (e.g., `list_mitigations()` at line 798, `ae_comparison()` at line 835, `signal_triangulation()` at line 764, `faers_comparison()` at line 715). This bypasses Pydantic validation and produces inconsistent API documentation. | Define proper Pydantic response models for all endpoints and add `response_model=` to the route decorators. | M |
| P3-8 | **Missing Feature** | No **WebSocket authentication**. The WebSocket endpoint (`/ws/monitor/{patient_id}`) accepts connections from any client without API key validation. A malicious client could monitor any patient's data stream by guessing patient IDs. | Add token-based authentication for WebSocket connections (e.g., pass API key as query parameter during upgrade, or require an auth message as the first frame). | S |

---

## Coverage Summary by Module

| Module | Statements | Missed | Coverage | Assessment |
|--------|-----------|--------|----------|------------|
| `src/api/app.py` | 309 | 230 | **19%** | Critical gap -- core endpoints untested |
| `src/api/middleware.py` | 71 | 21 | **65%** | Auth and rate limit logic partially covered |
| `src/api/narrative_engine.py` | 291 | 30 | **83%** | Good |
| `src/api/population_routes.py` | 598 | 49 | **92%** | Strong |
| `src/api/schemas.py` | 673 | 12 | **97%** | Excellent |
| `src/models/bayesian_risk.py` | 96 | 11 | **88%** | Good |
| `src/models/biomarker_scores.py` | 460 | 361 | **16%** | Critical gap -- core scoring logic |
| `src/models/ensemble_runner.py` | 135 | 84 | **28%** | Critical gap |
| `src/models/faers_signal.py` | 323 | 173 | **41%** | Moderate gap |
| `src/models/mitigation_model.py` | 125 | 9 | **89%** | Good |
| `src/models/model_registry.py` | 266 | 6 | **97%** | Excellent |
| `src/models/model_validation.py` | 165 | 13 | **92%** | Strong |
| `src/engine/*` (all 9 files) | 1,620 | 1,620 | **0%** | Untested subsystem |
| `src/safety_index/*` (4 files) | 384 | 384 | **0%** | Untested subsystem |
| `src/data/graph/*` (3 files) | 370 | 370 | **0%** | Possibly dead code |
| **TOTAL** | **6,744** | **3,426** | **46%** | |

---

## Top 5 Recommended Actions (in order)

1. **Fix CORS + error leak (P0-1, P0-2)** -- Small effort, large security impact. Restrict CORS origins and sanitize error responses.

2. **Add memory bounds (P0-3)** -- Add TTL/size limits to in-memory stores. Without this, the server will eventually crash under sustained use.

3. **Increase biomarker_scores.py coverage (P1-2)** -- This is the clinical core of the platform. At 16% coverage, there is high risk of undetected bugs in published formula implementations.

4. **Split population_routes.py (P1-5)** -- At 3,195 lines, this file is the primary contributor to code navigation difficulty. Splitting it is a prerequisite for effective collaboration.

5. **Fix datetime.utcnow() deprecation (P1-6)** -- Low effort, prevents future breakage when Python removes the deprecated API.

---

## Notes

- All 1,933 tests pass cleanly with no failures or warnings of concern.
- The `pyproject.toml` configuration was not audited for dependency pinning or security.
- No `.env` files or hardcoded secrets were found in the source code.
- The API key authentication pattern (env var `SAFETY_API_KEY`) is reasonable for a research tool.
- The codebase follows good practices for type hints, docstrings, and Pydantic validation.
- The knowledge graph modules (`src/data/knowledge/`) are well-structured with excellent coverage (96-100%).
