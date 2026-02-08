# GPU Server Work Plan — Predictive Safety Platform

> **For:** Claude Code instance on gpuserver1 (192.168.1.100)
> **Repo:** https://github.com/alto84/safety-research-system.git
> **Date:** 2026-02-07

---

## Context

We are building a Predictive Safety Platform (PSP) for CAR-T cell therapy safety in autoimmune indications. The platform combines:
- **Patient-level:** 7 deterministic biomarker scoring models (EASIX, HScore, CAR-HEMATOTOX, etc.)
- **Population-level:** Bayesian risk estimation, correlated mitigation modeling, FAERS signal detection
- **Safety Index:** Composite risk score from 4 domains (biomarker, pathway, model, clinical)

New modules just added: `bayesian_risk.py`, `mitigation_model.py`, `faers_signal.py`, `sle_cart_studies.py`

## Your Tasks (In Order)

### Task 1: Pull Latest Code and Run Existing Tests
```bash
cd ~/safety-research-system
git pull origin master
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn httpx pydantic scipy numpy
python -m pytest tests/ -v 2>&1 | head -80
```
**Checkpoint:** Report which tests pass and which fail.

### Task 2: Write and Run Unit Tests for New Modules
Create these test files:

**tests/unit/test_bayesian_risk.py:**
- Test `compute_posterior()` with CRS prior (1 event / 47 patients) → mean ~2.49%
- Test boundary: 0 events → mean should be close to prior mean but discounted
- Test CI bounds are within [0, 100]
- Test evidence accrual produces monotonically narrowing CIs
- Test evidence accrual matches standalone posterior at each point

**tests/unit/test_mitigation_model.py:**
- Test `combine_correlated_rr()` at rho=0 → multiplicative (RR_a * RR_b)
- Test `combine_correlated_rr()` at rho=1 → min(RR_a, RR_b)
- Test `combine_multiple_rrs()` with 3 mitigations
- Test `get_mitigation_correlation()` returns correct values
- Test Monte Carlo convergence: `monte_carlo_mitigated_risk()` median within ±0.5pp of analytical
- Test all 5 mitigation strategies load correctly

**tests/unit/test_sle_data.py:**
- Test all 8 SLE trials present, all 6 oncology comparators present
- Test all 14 clinical trials present
- Test `get_sle_baseline_risk()` returns expected structure
- Test `get_trial_summary()` counts match data

**tests/unit/test_faers_signal.py:**
- Test `compute_prr()` with known 2x2 table values
- Test `compute_ror()` with known values
- Test `compute_ebgm()` with known values
- Test `classify_signal()` at various thresholds
- Test edge cases (zero denominators)

**Checkpoint:** Report test results. All should pass.

### Task 3: Monte Carlo Validation
Run heavy computational validation (leverage GPU server hardware):

```python
# Monte Carlo convergence analysis
# For each number of samples [100, 500, 1000, 5000, 10000, 50000, 100000]:
# - Run monte_carlo_mitigated_risk() 20 times
# - Compute mean and std of the median estimate
# - Show convergence (std should decrease as sqrt(N))

# Prior sensitivity analysis
# For each discount factor [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
# - Recompute CRS prior
# - Compute posterior with 1/47 events
# - Show how prior choice affects posterior
```

Write results to `docs/validation/monte_carlo_convergence.md` and `docs/validation/prior_sensitivity.md`.

**Checkpoint:** Report convergence behavior and prior sensitivity findings.

### Task 4: Start the API Server and Validate Endpoints
```bash
cd ~/safety-research-system
python run_server.py &
# Wait for startup
sleep 3

# Test existing endpoints
curl http://localhost:8000/api/v1/health
curl "http://localhost:8000/api/v1/scores/easix?ldh=300&creatinine=1.2&platelets=150"

# Test population endpoints (once they exist - may need to wait for Rocinante to push)
curl http://localhost:8000/api/v1/population/risk
curl http://localhost:8000/api/v1/population/evidence-accrual
```

**Checkpoint:** Report which endpoints work.

### Task 5: Synthetic Patient Cohort Testing
Use the existing `data/synthetic_cohorts.py` to generate a test cohort, run through the full ensemble pipeline, and validate outputs.

```python
from data.synthetic_cohorts import generate_synthetic_cohort
from src.models.ensemble_runner import BiomarkerEnsembleRunner

runner = BiomarkerEnsembleRunner()
cohort = generate_synthetic_cohort(n=100)
for patient in cohort:
    result = runner.run(patient)
    # Validate: all scores within expected ranges
    # Validate: risk levels are correctly assigned
    # Validate: no errors or warnings that indicate bugs
```

**Checkpoint:** Report cohort testing results.

### Task 6: Dashboard Review
Pull up the dashboard at `http://localhost:8000/static/index.html` or `http://localhost:8000/clinical` and review:
- Does it load? Are all sections rendering?
- Does it connect to the API correctly?
- Are the visualizations accurate?
- Any JavaScript errors in the console?

**Checkpoint:** Report dashboard status and any issues.

---

## Communication Protocol

### How to Report Back
After each checkpoint, update the file: `~/safety-research-system/GPUSERVER-STATUS.md` with:
```markdown
## Checkpoint N: [Task Name]
**Status:** Pass / Fail / Partial
**Details:** [what happened]
**Issues Found:** [list any problems]
**Timestamp:** [when]
```

Rocinante will periodically check this file via SSH.

### If You Get Stuck
1. Check if there are code changes to pull: `git pull origin master`
2. Look for updated instructions in `MERGE-PLAN.md`
3. If blocked on a dependency, note it in GPUSERVER-STATUS.md and move to the next task

---

## Environment Setup
```bash
# Ensure Python 3.11+
python3 --version

# Install dependencies
pip install fastapi uvicorn httpx pydantic scipy numpy pytest

# Clone/update repo
cd ~/safety-research-system || git clone https://github.com/alto84/safety-research-system.git ~/safety-research-system
cd ~/safety-research-system
git pull origin master
```
