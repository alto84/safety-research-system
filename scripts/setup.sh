#!/usr/bin/env bash
# Setup script for Safety Research System development environment
set -euo pipefail

echo "=== Safety Research System — Dev Setup ==="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]; }; then
    echo "ERROR: Python 3.11+ required (found $PYTHON_VERSION)"
    exit 1
fi
echo "Python $PYTHON_VERSION — OK"

# Install dev dependencies
echo "Installing dependencies..."
pip install -e ".[dev]" --quiet

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Verify tests pass
echo "Running quick test check..."
python -m pytest tests/unit/ -q --tb=line -x 2>&1 | tail -5

echo ""
echo "=== Setup Complete ==="
echo "  make serve      — start the server"
echo "  make test       — run all tests"
echo "  make check      — lint + format + test"
echo "  make help       — see all commands"
