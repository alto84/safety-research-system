#!/usr/bin/env bash
# Quick-start the Predictive Safety Platform
# Usage: ./start.sh [port]

PORT=${1:-8000}
echo "Starting Predictive Safety Platform on port $PORT..."
python3 run_server.py --port "$PORT" --open
