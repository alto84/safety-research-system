# Software Architecture Review: Population-Level Safety Module Merge

**Review Date:** 2026-02-07
**Reviewer:** Principal Software Architect
**Scope:** Phase 0-1 merge of population-level risk models into safety-research-system
**Status:** Pre-implementation architectural assessment

---

## Executive Summary

The proposed merge introduces well-designed population-level risk analytics (Bayesian risk estimation, correlated mitigation modeling, FAERS signal detection) into an existing patient-level biomarker scoring platform. The architectural approach is **sound but requires critical fixes before production deployment**.

**Recommendation:** CONDITIONAL APPROVAL with 7 must-fix issues and 12 recommendations for Phase 2.

---

## Strengths

### 1. **Excellent Module Cohesion**
The new modules (`bayesian_risk.py`, `mitigation_model.py`, `faers_signal.py`) follow the established pattern from `biomarker_scores.py`:
- Pure functions with no hidden state
- Dataclass-based outputs with clear provenance
- Self-contained computation logic
- Comprehensive docstrings with mathematical formulas and citations

### 2. **Strong Schema Design**
The population-level Pydantic schemas (`BayesianPosteriorRequest`, `MitigationAnalysisRequest`, `FAERSSignalResponse`) are:
- Consistent with existing patient-level schemas
- Well-documented with field descriptions
- Include appropriate validation (e.g., `@field_validator` for adverse event types)
- Return structured responses with `request_id` and `timestamp` for audit trails

### 3. **Separation of Concerns**
Clean separation between:
- Data layer (`data/sle_cart_studies.py`) - immutable clinical data
- Model layer (`src/models/`) - pure computation
- API layer (`src/api/`) - HTTP interface and orchestration
- Schema layer (`src/api/schemas.py`) - contracts and validation

### 4. **Mathematical Rigor**
Bayesian and Monte Carlo implementations show:
- Correct Beta-Binomial conjugacy
- Proper credible interval computation
- Documented correlation correction formula with boundary conditions
- Appropriate uncertainty quantification

### 5. **Existing Infrastructure Quality**
The platform already has:
- Comprehensive middleware stack (timing, rate limiting, API key auth, error handling)
- Strong input validation patterns
- WebSocket support for real-time monitoring
- Type hints throughout (mypy strict mode enabled)

---

## Issues (Must-Fix)

### 1. **CRITICAL: Missing Population Routes** ⚠️ BLOCKER
**Location:** `src/api/app.py`
**Issue:** The merge plan specifies adding `/api/v1/population/*` endpoints, but:
- No `population_routes.py` router exists
- The 1078-line `app.py` contains only patient-level endpoints
- Population schemas exist but are unused

**Impact:** The new modules are dead code until wired into the API.

**Fix:**
```python
# Create src/api/population_routes.py
from fastapi import APIRouter, HTTPException
from src.api.schemas import (
    BayesianPosteriorRequest, BayesianPosteriorResponse,
    MitigationAnalysisRequest, MitigationAnalysisResponse,
    # ... other population schemas
)
from src.models.bayesian_risk import compute_posterior, CRS_PRIOR, ICANS_PRIOR
from src.models.mitigation_model import analyze_correlated_mitigations
from src.models.faers_signal import query_faers_signals

router = APIRouter(prefix="/api/v1/population", tags=["Population Risk"])

@router.post("/bayesian", response_model=BayesianPosteriorResponse)
async def compute_bayesian_posterior(req: BayesianPosteriorRequest):
    # Implementation
    pass

# ... other endpoints

# Then in app.py:
from src.api.population_routes import router as population_router
app.include_router(population_router)
```

**Test:** `curl http://localhost:8000/api/v1/population/bayesian` should not return 404.

---

### 2. **CRITICAL: Monte Carlo Performance Hazard** ⚠️ PERFORMANCE
**Location:** `src/models/mitigation_model.py:analyze_correlated_mitigations()`
**Issue:** Default `n_samples=10000` runs on **every API request** with no caching.

**Impact:**
- 10K-sample Monte Carlo takes ~50-200ms depending on CPU
- Under load (100 req/min rate limit), this is 5-20 seconds of CPU per minute
- No async execution → blocks the event loop
- Memory allocation/GC churn from repeated sampling

**Fix:**
```python
# Option 1: Reduce default samples for API endpoints
MitigationAnalysisRequest(
    n_monte_carlo_samples: int = Field(1000, ge=100, le=10000)  # 1K default
)

# Option 2: Implement result caching
from functools import lru_cache

@lru_cache(maxsize=128)
def _cached_mitigation_analysis(
    mitigations_tuple: tuple[str, ...],  # tuples are hashable
    baseline_risk: float,
    n_samples: int,
) -> MitigationResult:
    return analyze_correlated_mitigations(...)
```

**Test:** Benchmark with `pytest-benchmark` at 1K, 5K, 10K samples. Target <100ms p95 for API responsiveness.

---

### 3. **HIGH: FAERS API Rate Limiting Insufficient** ⚠️ RELIABILITY
**Location:** `src/models/faers_signal.py:_rate_limit()`
**Issue:**
- In-memory `_request_timestamps` list is **not thread-safe**
- Multiple FastAPI workers will each maintain separate rate limit state
- Actual rate could be `40 * num_workers` requests/minute → API ban

**Impact:** OpenFDA blocks IPs that exceed rate limits, breaking the FAERS feature.

**Fix:**
```python
# Option 1: Use Redis for distributed rate limiting
import redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# In app.py startup:
redis_client = redis.from_url("redis://localhost")
await FastAPILimiter.init(redis_client)

# On FAERS endpoint:
@router.get("/signals/faers", dependencies=[Depends(RateLimiter(times=40, minutes=1))])

# Option 2: Single-worker deployment with warning
# Add to README: "FAERS endpoints require single-worker deployment (uvicorn --workers=1)"
```

**Test:** Start 4 Uvicorn workers, hammer FAERS endpoint, verify total rate stays <40/min.

---

### 4. **HIGH: SQL Injection Risk in Knowledge Graph Queries** ⚠️ SECURITY
**Location:** MERGE-PLAN.md Phase 1, Stream A, Step 2
**Issue:** Plan mentions "wire adverse event nodes" and "connect evidence accrual data points" to KnowledgeGraph, but no details on query construction. If dynamic queries use string interpolation:

```python
# UNSAFE
query = f"MATCH (n:AdverseEvent {{name: '{ae_name}'}}) RETURN n"
neo4j_session.run(query)
```

**Impact:** Arbitrary Cypher injection if `ae_name` comes from user input.

**Fix:**
```python
# SAFE: Use parameterized queries
query = "MATCH (n:AdverseEvent {name: $ae_name}) RETURN n"
neo4j_session.run(query, parameters={"ae_name": ae_name})
```

**Test:** Penetration test with `ae_name = "CRS') MATCH (n) DETACH DELETE n //"` should NOT delete nodes.

---

### 5. **MEDIUM: Missing Input Validation on Population Endpoints** ⚠️ SECURITY
**Location:** `src/api/schemas.py`
**Issue:**
- `BayesianPosteriorRequest.n_events` allows `n_events > n_patients` (impossible)
- `MitigationAnalysisRequest.selected_mitigations` doesn't validate against known mitigation IDs
- `FAERSSummaryResponse.products_queried` is open-ended string list

**Impact:**
- Nonsensical inputs produce confusing errors deep in computation
- Invalid mitigation IDs cause KeyError instead of 400 Bad Request
- Potential for injection attacks via product names

**Fix:**
```python
class BayesianPosteriorRequest(BaseModel):
    n_events: int = Field(..., ge=0)
    n_patients: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_events_le_patients(self):
        if self.n_events > self.n_patients:
            raise ValueError(f"n_events ({self.n_events}) cannot exceed n_patients ({self.n_patients})")
        return self

class MitigationAnalysisRequest(BaseModel):
    selected_mitigations: list[str] = Field(..., min_length=1)

    @field_validator("selected_mitigations")
    @classmethod
    def validate_mitigation_ids(cls, v):
        from src.models.mitigation_model import MITIGATION_STRATEGIES
        invalid = set(v) - set(MITIGATION_STRATEGIES.keys())
        if invalid:
            raise ValueError(f"Invalid mitigation IDs: {invalid}")
        return v
```

---

### 6. **MEDIUM: In-Memory State Pattern Not Production-Ready** ⚠️ SCALABILITY
**Location:** `src/api/app.py` lines 85-89
**Issue:**
```python
_patient_timelines: dict[str, list[dict[str, Any]]] = defaultdict(list)
_model_last_run: dict[str, datetime] = {}
_ws_connections: dict[str, list[WebSocket]] = defaultdict(list)
```

**Impact:**
- Lost on server restart
- Not shared across multiple workers (each worker has separate state)
- Unbounded memory growth (no eviction policy)
- WebSocket connections tied to specific worker instances

**Fix:**
```python
# Phase 1: Add TTL eviction
from collections import OrderedDict
import time

class TTLCache:
    def __init__(self, ttl_seconds=3600, max_size=10000):
        self._cache = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size

    def set(self, key, value):
        self._evict_expired()
        self._cache[key] = (value, time.time())
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def get(self, key):
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            del self._cache[key]
        return None

    def _evict_expired(self):
        now = time.time()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts >= self._ttl]
        for k in expired:
            del self._cache[k]

# Phase 2: Move to Redis/PostgreSQL for multi-worker persistence
```

---

### 7. **LOW: CORS Wildcard in Production** ⚠️ SECURITY
**Location:** `src/api/app.py` line 179
**Issue:**
```python
allow_origins=["*"],  # Allows any domain
```

**Impact:** Opens the API to CSRF attacks and unauthorized cross-origin requests.

**Fix:**
```python
# Production configuration
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Explicit whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

## Recommendations (Phase 2+)

### API Design

**R1. Versioning Strategy**
Current: Single `/api/v1/` namespace.
Concern: Breaking changes will force v2 migration for all clients.

**Recommendation:**
- Keep population endpoints in `/api/v1/population/` for now
- Document deprecation policy: 6-month notice for breaking changes
- Consider header-based versioning (`Accept: application/vnd.safety-platform.v2+json`) for Phase 3

---

**R2. Async FAERS Queries**
Current: `query_faers_signals()` is sync (uses `urllib` or `httpx` sync client).
Concern: Blocks FastAPI event loop during 5-10 multi-second openFDA API calls.

**Recommendation:**
```python
async def query_faers_signals_async(
    products: list[str],
    adverse_events: list[str],
) -> FAERSSummary:
    async with httpx.AsyncClient() as client:
        tasks = [
            _fetch_product_ae_pair(client, product, ae)
            for product in products
            for ae in adverse_events
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    # ... process results
```

---

**R3. Pagination for FAERS Results**
Current: Returns all signals in a single response.
Concern: 6 products × 10 AEs = 60 signals could be large.

**Recommendation:** Add pagination to `/api/v1/signals/faers`:
```python
@router.get("/signals/faers")
async def get_faers_signals(
    products: list[str] = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # Return paginated results with total count
```

---

### Module Structure

**R4. Circular Dependency Risk**
Current: Clean separation, but merge plan mentions Safety Index will "add population-level risk domain".
Concern: If `safety_index/index.py` imports `bayesian_risk`, and `bayesian_risk` needs Safety Index types → circular import.

**Recommendation:**
- Keep data structures in `src/models/common.py` or `src/types.py`
- Safety Index should aggregate outputs, not import model internals
- Use dependency injection pattern for extensibility

---

**R5. Test Module Organization**
Current: `tests/unit/test_biomarker_scores.py` exists, but no tests for new modules yet.
Concern: Parallel agents may create conflicting test files.

**Recommendation:**
- Create `tests/unit/test_bayesian_risk.py`, `test_mitigation_model.py`, `test_faers_signal.py` BEFORE implementation
- Add to MERGE-PLAN.md as Phase 1 prerequisites
- Use pytest parametrize for boundary condition tests:
```python
@pytest.mark.parametrize("rho,rr_a,rr_b,expected", [
    (0.0, 0.5, 0.5, 0.25),  # Independent: 0.5 * 0.5
    (1.0, 0.5, 0.6, 0.5),   # Fully correlated: min(0.5, 0.6)
    (0.5, 0.4, 0.7, pytest.approx(0.35, abs=0.05)),  # Geometric mean
])
def test_correlated_combination(rho, rr_a, rr_b, expected):
    result = combine_correlated_rr(rr_a, rr_b, rho)
    assert result == expected
```

---

### Code Quality

**R6. Type Hint Completeness**
Current: Excellent coverage in existing code (mypy strict mode).
Concern: New modules use `dict[str, Any]` in several places.

**Recommendation:**
- Replace `dict[str, Any]` with TypedDict or dataclasses where possible
- Add type stubs for external dependencies (openFDA responses)
- Enable `disallow_any_expr` in mypy for new modules

---

**R7. Error Handling Consistency**
Current: `biomarker_scores.py` returns `ScoringResult` with `errors: list[str]` field.
Concern: Population modules raise exceptions (`ValueError`, `HTTPException`) instead.

**Recommendation:** Standardize on result types with error fields:
```python
@dataclass
class BayesianResult:
    estimate: PosteriorEstimate | None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0 and self.estimate is not None
```

---

**R8. Logging Strategy**
Current: Scattered `logger.info()` calls, no structured context.
Concern: Debugging population model failures will be difficult in production.

**Recommendation:**
```python
import structlog

log = structlog.get_logger()

# In Bayesian computation:
log.info(
    "bayesian_posterior_computed",
    adverse_event=ae,
    n_events=events,
    n_patients=n,
    posterior_mean=result.mean,
    ci_width=result.ci_width,
)
```

---

### Performance

**R9. Precompute Evidence Accrual Timeline**
Current: `generate_evidence_accrual_timeline()` recalculates on every request.
Concern: Timeline is static (defined in `STUDY_TIMELINE`), no need to recompute.

**Recommendation:**
```python
# At module load time:
_EVIDENCE_TIMELINE_CACHE = generate_evidence_accrual_timeline(STUDY_TIMELINE)

@router.get("/population/evidence-accrual")
async def get_evidence_accrual():
    # Return pre-computed timeline
    return _EVIDENCE_TIMELINE_CACHE
```

---

**R10. Database for Patient Timelines**
Current: In-memory `_patient_timelines` dict (see Issue #6).
Long-term: Multi-worker deployment requires shared state.

**Recommendation:** Phase 2 migration to PostgreSQL:
```sql
CREATE TABLE patient_timelines (
    patient_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    composite_score REAL,
    risk_level TEXT,
    model_scores JSONB,
    alerts JSONB,
    PRIMARY KEY (patient_id, timestamp)
);
CREATE INDEX idx_patient_recent ON patient_timelines (patient_id, timestamp DESC);
```

---

### Security

**R11. API Key Rotation**
Current: Single `SAFETY_API_KEY` environment variable.
Concern: No rotation mechanism, leaked key requires server restart.

**Recommendation:**
```python
# Support multiple keys with expiration
API_KEYS = {
    "key_20260201": datetime(2026, 4, 1),  # Expires April 1
    "key_20260401": None,                   # No expiration
}

class APIKeyMiddleware:
    def validate_key(self, key: str) -> bool:
        if key in API_KEYS:
            expiry = API_KEYS[key]
            if expiry is None or datetime.utcnow() < expiry:
                return True
        return False
```

---

**R12. Input Sanitization for Dashboard**
Concern: If patient IDs or product names are rendered in HTML dashboard without escaping → XSS.

**Recommendation:**
- Use template engine with auto-escaping (Jinja2)
- Or sanitize in API response:
```python
import bleach

def sanitize_patient_id(patient_id: str) -> str:
    return bleach.clean(patient_id, tags=[], strip=True)
```

---

### Scalability

**R13. WebSocket Horizontal Scaling**
Current: WebSocket connections stored in `_ws_connections` dict.
Concern: Load balancer will route requests to different workers, breaking WS.

**Recommendation:**
- Phase 2: Use Redis Pub/Sub for cross-worker WS messaging
- Or: Sticky sessions on load balancer (suboptimal)
- Or: Separate WebSocket server with shared Redis state

---

### Dashboard Architecture

**R14. Single HTML File vs. Framework**
Current: `src/api/static/index.html` (single file).
Merge Plan: Extend with population-level charts.

**Trade-offs:**
| Single HTML | Framework (React/Vue) |
|-------------|----------------------|
| ✅ Zero build step | ❌ Requires Node.js build |
| ✅ Fast iteration | ✅ Component reusability |
| ❌ Hard to maintain >2000 lines | ✅ Testable UI logic |
| ❌ No client-side routing | ✅ Better UX for SPAs |

**Recommendation:**
- **Phase 1:** Keep single HTML with vanilla JS (SVG charts via D3.js or Chart.js)
- **Phase 2:** Migrate to Vite + React when dashboard exceeds 1500 lines or requires >3 new views

---

### Testing

**R15. Integration Test Strategy for FAERS**
Current: No FAERS tests mentioned in merge plan.
Concern: Live openFDA API calls in tests are:
- Slow (5-10 seconds)
- Flaky (network issues)
- Rate-limited (breaks CI)

**Recommendation:**
```python
# tests/integration/test_faers_live.py (skipped by default)
@pytest.mark.integration
@pytest.mark.skip(reason="Requires live openFDA API access")
def test_faers_query_live():
    summary = query_faers_signals(["KYMRIAH"], ["Cytokine release syndrome"])
    assert summary.total_reports > 0

# tests/unit/test_faers_mock.py (always runs)
@pytest.fixture
def mock_openfda_response():
    return {
        "meta": {"results": {"total": 1234}},
        "results": [{"count": 567}]
    }

def test_faers_signal_detection(mock_openfda_response, mocker):
    mocker.patch("src.models.faers_signal._query_openfda", return_value=mock_openfda_response)
    summary = query_faers_signals(["KYMRIAH"], ["CRS"])
    assert summary.total_reports == 1234
```

---

**R16. Mathematical Verification Tests**
Merge plan mentions "verify Bayesian posteriors against hand calculations".

**Recommendation:** Add regression tests with known results:
```python
def test_bayesian_posterior_known_case():
    # Prior: Beta(2, 5) = mean 2/(2+5) ≈ 0.286
    # Data: 3 events in 10 patients
    # Posterior: Beta(2+3, 5+10-3) = Beta(5, 12) = mean 5/17 ≈ 0.294
    prior = PriorSpec(alpha=2, beta=5, source_description="test")
    posterior = compute_posterior(prior, events=3, n=10)

    assert posterior.mean == pytest.approx(29.4, abs=0.1)  # percentage
    assert posterior.alpha == 5.0
    assert posterior.beta == 12.0
```

---

**R17. Monte Carlo Convergence Tests**
Merge plan: "Verify Monte Carlo convergence (10K samples should converge within ±0.5pp)".

**Recommendation:**
```python
def test_monte_carlo_convergence():
    # Run mitigation analysis twice with same seed
    random.seed(42)
    result1 = analyze_correlated_mitigations(
        baseline_risk=0.15,
        selected_mitigations=["tocilizumab", "anakinra"],
        n_samples=10000,
    )

    random.seed(42)
    result2 = analyze_correlated_mitigations(
        baseline_risk=0.15,
        selected_mitigations=["tocilizumab", "anakinra"],
        n_samples=10000,
    )

    # Identical seeds should give identical results
    assert result1.mitigated_risk == result2.mitigated_risk

    # Different seeds should be within 0.5 percentage points
    random.seed(99)
    result3 = analyze_correlated_mitigations(
        baseline_risk=0.15,
        selected_mitigations=["tocilizumab", "anakinra"],
        n_samples=10000,
    )
    assert abs(result1.mitigated_risk - result3.mitigated_risk) < 0.005
```

---

## Risk Assessment

### High-Risk Areas
1. **FAERS Rate Limiting** (Issue #3): Could break the entire FAERS feature → production outage
2. **Monte Carlo Performance** (Issue #2): Could cause API timeouts under load
3. **Missing Routes** (Issue #1): Blocks entire population module integration

### Medium-Risk Areas
4. **Knowledge Graph SQL Injection** (Issue #4): Security vulnerability if KG queries are dynamic
5. **In-Memory State** (Issue #6): Limits scalability, data loss on restart

### Low-Risk Areas
6. **Input Validation** (Issue #5): Mostly UX degradation, low security impact
7. **CORS Wildcard** (Issue #7): Low risk for internal deployment, but should fix

---

## Test Coverage Assessment

### Existing Coverage (Good)
- Unit tests for biomarker scores (`tests/unit/test_biomarker_scores.py`)
- Integration tests for API endpoints (`tests/integration/test_api_endpoints.py`)
- Input validation tests (`tests/unit/test_input_validation.py`)
- Safety-critical validation (`tests/safety/test_regulatory.py`)

### Gaps (Must Add)
- ❌ No tests for `bayesian_risk.py` (Bayesian computation correctness)
- ❌ No tests for `mitigation_model.py` (correlation formula boundary conditions)
- ❌ No tests for `faers_signal.py` (disproportionality metrics, rate limiting)
- ❌ No tests for population API endpoints (404 until routes are added)
- ❌ No tests for `sle_cart_studies.py` data integrity (sum checks, no missing fields)

**Recommendation:** Block merge until at least unit tests for new modules are written.

---

## Deployment Readiness Checklist

- [ ] **Issue #1 Fixed:** Population routes implemented and registered
- [ ] **Issue #2 Fixed:** Monte Carlo performance optimized (1K default + caching)
- [ ] **Issue #3 Fixed:** FAERS rate limiting uses Redis or single-worker deployment documented
- [ ] **Issue #4 Mitigated:** Knowledge graph queries use parameterized Cypher
- [ ] **Issue #5 Fixed:** Population schema validators added (events ≤ patients, valid mitigation IDs)
- [ ] **Issue #6 Mitigated:** TTL cache or Redis for patient timelines (Phase 1) / PostgreSQL (Phase 2)
- [ ] **Issue #7 Fixed:** CORS whitelist configured via environment variable
- [ ] **Tests Added:** Unit tests for all 3 new modules (bayesian, mitigation, faers)
- [ ] **Tests Added:** Integration tests for population endpoints
- [ ] **Tests Added:** Mathematical verification tests (boundary conditions, known results)
- [ ] **Documentation Updated:** OpenAPI schema includes population endpoints
- [ ] **Load Testing:** Benchmark with 100 concurrent users, verify <500ms p95 latency

---

## Final Verdict

**Architecture Grade:** A- (Strong foundation, critical gaps in wiring and performance)
**Code Quality Grade:** A (Excellent type hints, docstrings, validation patterns)
**Security Grade:** B+ (Good defaults, missing parameterization in KG queries, CORS fix needed)
**Scalability Grade:** C+ (In-memory state limits horizontal scaling, Monte Carlo blocking)
**Production Readiness:** **NOT READY** (7 must-fix issues, especially missing routes)

**Approval Contingent On:**
1. Implementing population routes (Issue #1)
2. Optimizing Monte Carlo or adding caching (Issue #2)
3. Fixing FAERS rate limiting (Issue #3)
4. Writing unit tests for new modules

**Timeline Estimate:**
- Fix Issues #1-3: 2-3 days (single developer)
- Add unit tests: 1-2 days
- Phase 2 recommendations: 5-7 days (can be deferred)

---

## Appendix A: Code Metrics

| Metric | Current | After Merge | Target |
|--------|---------|-------------|--------|
| API Endpoints | 15 | 21 (+6 population) | 25 |
| Total Lines (src/) | ~8,500 | ~11,000 | <15,000 |
| Test Coverage | ~65% | TBD (need new tests) | >80% |
| Type Hint Coverage | 95% | 95% | >90% |
| Cyclomatic Complexity (max) | 12 | TBD | <15 |

---

## Appendix B: Recommended Reading Order for Reviewers

1. `MERGE-PLAN.md` (understand goals)
2. `src/api/schemas.py` (lines 293-468: population schemas)
3. `src/models/bayesian_risk.py` (mathematical correctness)
4. `src/models/mitigation_model.py` (correlation formula)
5. `src/models/faers_signal.py` (rate limiting and caching)
6. `data/sle_cart_studies.py` (data provenance)
7. This review document

---

**Review Completed:** 2026-02-07
**Next Review:** After Phase 1 implementation (estimated 2026-02-14)
