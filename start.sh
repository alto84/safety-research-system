#!/usr/bin/env bash
# Quick-start the Simulated Patient Safety
# Usage: ./start.sh [port]

PORT=${1:-8000}
echo "Starting Simulated Patient Safety on port $PORT..."
python3 run_server.py --port "$PORT" --open
