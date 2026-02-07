#!/usr/bin/env python3
"""
Start the Predictive Safety Platform API server.

Usage:
    python run_server.py                       # defaults: 0.0.0.0:8000
    python run_server.py --port 8080           # custom port
    python run_server.py --host 127.0.0.1      # localhost only
    python run_server.py --reload              # auto-reload on code changes
    python run_server.py --workers 4           # multiple workers (no reload)

Environment variables:
    SAFETY_API_KEY      API key for authentication (optional; auth disabled if unset)
    LOG_LEVEL           Logging level (default: INFO)
"""

from __future__ import annotations

import argparse
import logging
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predictive Safety Platform API server",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1; ignored if --reload is set)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        import uvicorn
    except ImportError:
        print(
            "ERROR: uvicorn is not installed. Install it with:\n"
            "  pip install uvicorn[standard]\n"
            "or install the full project:\n"
            "  pip install -e .[dev]",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Starting Predictive Safety Platform API on {args.host}:{args.port}")
    print(f"  Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  ReDoc:      http://{args.host}:{args.port}/redoc")
    print(f"  Health:     http://{args.host}:{args.port}/api/v1/health")

    uvicorn.run(
        "src.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
