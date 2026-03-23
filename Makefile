.PHONY: help install install-dev install-docs test test-unit test-integration test-safety test-stress test-validation lint lint-fix typecheck format check serve serve-dev clean validate setup

# ── Help ─────────────────────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Installation ─────────────────────────────────────────────────────────────
install: ## Install minimal server dependencies
	pip install -r requirements-server.txt

install-dev: ## Install all development dependencies
	pip install -e ".[dev]"

install-docs: ## Install documentation dependencies
	pip install -e ".[docs]"

# ── Testing ──────────────────────────────────────────────────────────────────
test: ## Run all tests
	python -m pytest tests/ -q

test-unit: ## Run unit tests only
	python -m pytest tests/unit/ -q

test-integration: ## Run integration tests only
	python -m pytest tests/integration/ -q

test-safety: ## Run regulatory compliance tests
	python -m pytest tests/safety/ -q

test-stress: ## Run stress and battle tests
	python -m pytest tests/stress/ -q

test-validation: ## Run model validation tests
	python -m pytest tests/validation/ -q

test-cov: ## Run tests with coverage report
	python -m pytest tests/ -q --cov=src --cov-report=term-missing --cov-report=html

# ── Code Quality ─────────────────────────────────────────────────────────────
lint: ## Run linter (ruff check)
	ruff check src/ tests/

lint-fix: ## Run linter and auto-fix issues
	ruff check --fix src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/

format-check: ## Check formatting without changes
	ruff format --check src/ tests/

typecheck: ## Run mypy type checking
	mypy src/

# ── Validation ───────────────────────────────────────────────────────────────
check: lint format-check test ## Run lint + format check + all tests
	@echo "All checks passed."

validate: ## Full validation: lint, format, typecheck, all tests
	@echo "=== Linting ==="
	ruff check src/ tests/
	@echo "=== Format Check ==="
	ruff format --check src/ tests/
	@echo "=== Type Check ==="
	mypy src/ || true
	@echo "=== Tests ==="
	python -m pytest tests/ -q
	@echo "=== Validation Complete ==="

# ── Server ───────────────────────────────────────────────────────────────────
serve: ## Start the server (production mode)
	python run_server.py

serve-dev: ## Start the server with auto-reload
	python run_server.py --reload

serve-open: ## Start the server and open browser
	python run_server.py --open

# ── Utilities ────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

setup: ## Full setup: install dev deps + pre-commit hooks
	pip install -e ".[dev]"
	pre-commit install
	@echo "Setup complete. Run 'make test' to verify."
