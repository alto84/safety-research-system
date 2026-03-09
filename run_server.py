#!/usr/bin/env python3
"""
Start the Simulated Patient Safety API server.

Usage:
    python run_server.py                       # defaults: 0.0.0.0:8000
    python run_server.py --port 8080           # custom port
    python run_server.py --host 127.0.0.1      # localhost only
    python run_server.py --reload              # auto-reload on code changes
    python run_server.py --workers 4           # multiple workers (no reload)
    python run_server.py --open                # auto-open browser

Environment variables:
    SAFETY_API_KEY      API key for authentication (optional; auth disabled if unset)
    LOG_LEVEL           Logging level (default: INFO)
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys


def _port_in_use(port: int) -> int | None:
    """Check if port is in use. Returns the PID if detectable, else -1, or None if free."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return None  # Port is free
        except OSError:
            pass
    # Try to find the PID (Windows)
    try:
        import subprocess
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                return int(parts[-1])
    except Exception:
        pass
    return -1  # In use but can't find PID


def _find_free_port(start: int = 8000) -> int:
    """Find the next free port starting from start."""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start  # fallback


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulated Patient Safety API server",
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
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the dashboard in the default browser",
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

    # Check for port conflicts
    pid = _port_in_use(args.port)
    if pid is not None:
        if pid > 0:
            print(f"Port {args.port} is already in use by PID {pid}.")
            print(f"  To kill it:  taskkill /PID {pid} /F  (Windows)")
            print(f"               kill {pid}              (Linux/Mac)")
        else:
            print(f"Port {args.port} is already in use.")
        alt = _find_free_port(args.port + 1)
        print(f"  Alternative: python run_server.py --port {alt}")
        print()
        response = input(f"Use port {alt} instead? [Y/n] ").strip().lower()
        if response in ("", "y", "yes"):
            args.port = alt
        else:
            print("Exiting.")
            sys.exit(1)

    base = f"http://localhost:{args.port}"

    print()
    print("=" * 60)
    print("  Simulated Patient Safety")
    print("=" * 60)
    print()
    print(f"  Clinical Dashboard:  {base}/clinical")
    print(f"  PSD Dashboard:       {base}/psd")
    print(f"  API Docs (Swagger):  {base}/docs")
    print(f"  Health Check:        {base}/api/v1/health")
    print()
    print("=" * 60)
    print()

    # Open browser if requested
    if args.open:
        import threading
        import webbrowser
        threading.Timer(1.5, webbrowser.open, args=[f"{base}/psd"]).start()

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
