#!/usr/bin/env bash
# Full validation script — runs all quality checks and tests
# Exit code 0 = all green, non-zero = issues found
set -euo pipefail

ERRORS=0

section() {
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
}

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; ERRORS=$((ERRORS + 1)); }

# ── Lint ─────────────────────────────────────────────────────────────────────
section "Linting (ruff check)"
if ruff check src/ tests/ --quiet 2>/dev/null; then
    pass "No lint issues"
else
    fail "Lint issues found — run 'make lint-fix'"
fi

# ── Format ───────────────────────────────────────────────────────────────────
section "Formatting (ruff format)"
if ruff format --check src/ tests/ --quiet 2>/dev/null; then
    pass "Code is formatted"
else
    fail "Formatting issues — run 'make format'"
fi

# ── Unit Tests ───────────────────────────────────────────────────────────────
section "Unit Tests"
if python -m pytest tests/unit/ -q --tb=line 2>&1; then
    pass "Unit tests passed"
else
    fail "Unit test failures"
fi

# ── Integration Tests ────────────────────────────────────────────────────────
section "Integration Tests"
if python -m pytest tests/integration/ -q --tb=line 2>&1; then
    pass "Integration tests passed"
else
    fail "Integration test failures"
fi

# ── Safety Tests ─────────────────────────────────────────────────────────────
section "Regulatory Compliance Tests"
if python -m pytest tests/safety/ -q --tb=line 2>&1; then
    pass "Safety tests passed"
else
    fail "Safety test failures"
fi

# ── Validation Tests ─────────────────────────────────────────────────────────
section "Model Validation Tests"
if python -m pytest tests/validation/ -q --tb=line 2>&1; then
    pass "Validation tests passed"
else
    fail "Validation test failures"
fi

# ── Stress Tests ─────────────────────────────────────────────────────────────
section "Stress Tests"
if python -m pytest tests/stress/ -q --tb=line 2>&1; then
    pass "Stress tests passed"
else
    fail "Stress test failures"
fi

# ── Server Smoke Test ────────────────────────────────────────────────────────
section "Server Smoke Test"
python run_server.py &
SERVER_PID=$!
sleep 3

if curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    pass "Health endpoint responds"
else
    fail "Server health check failed"
fi

kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

# ── Summary ──────────────────────────────────────────────────────────────────
section "Summary"
if [ $ERRORS -eq 0 ]; then
    echo "  All checks passed!"
    exit 0
else
    echo "  $ERRORS check(s) failed."
    exit 1
fi
