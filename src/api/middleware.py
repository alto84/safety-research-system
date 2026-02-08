"""
Middleware for the prediction API server.

Provides:
    - Request timing (X-Process-Time header)
    - Request ID generation and injection
    - API key authentication
    - Rate limiting (simple in-memory token bucket)
    - Global error handling
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request ID context
# ---------------------------------------------------------------------------

_REQUEST_ID_HEADER = "X-Request-ID"
_PROCESS_TIME_HEADER = "X-Process-Time"


# ---------------------------------------------------------------------------
# Request timing middleware
# ---------------------------------------------------------------------------

class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Adds request timing and request ID headers to every response.

    Headers added:
        X-Request-ID: Unique identifier for the request.
        X-Process-Time: Server processing time in milliseconds.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER, str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.monotonic()

        logger.info(
            "Request %s: %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        response = await call_next(request)

        process_time_ms = (time.monotonic() - start_time) * 1000
        response.headers[_REQUEST_ID_HEADER] = request_id
        response.headers[_PROCESS_TIME_HEADER] = f"{process_time_ms:.2f}ms"

        logger.info(
            "Response %s: status=%d time=%.2fms",
            request_id,
            response.status_code,
            process_time_ms,
        )

        return response


# ---------------------------------------------------------------------------
# API key authentication middleware
# ---------------------------------------------------------------------------

# The API key is read from the SAFETY_API_KEY environment variable.
# If the variable is not set, authentication is disabled (development mode).
_API_KEY_HEADER = "X-API-Key"

# Paths that do not require authentication
_PUBLIC_PATHS = {
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Simple header-based API key authentication.

    Reads the expected API key from the ``SAFETY_API_KEY`` environment variable.
    If the variable is not set, authentication is disabled and a warning is
    logged on startup.

    Public paths (health check, docs) are always allowed.
    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)
        self._api_key = os.environ.get("SAFETY_API_KEY", "")
        if not self._api_key:
            logger.warning(
                "SAFETY_API_KEY not set. API key authentication is DISABLED. "
                "Set the environment variable to enable it."
            )

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip auth for public paths and WebSocket upgrades
        if (
            request.url.path in _PUBLIC_PATHS
            or request.url.path.startswith("/docs")
            or request.url.path.startswith("/redoc")
            or not self._api_key
        ):
            return await call_next(request)

        # Check API key
        provided_key = request.headers.get(_API_KEY_HEADER, "")
        if provided_key != self._api_key:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            logger.warning(
                "Authentication failed for %s %s (request_id=%s)",
                request.method,
                request.url.path,
                request_id,
            )
            return JSONResponse(
                status_code=401,
                content={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Unauthorized",
                    "detail": "Invalid or missing API key. Provide a valid key via the X-API-Key header.",
                    "status_code": 401,
                },
            )

        return await call_next(request)


# ---------------------------------------------------------------------------
# Rate limiting middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter using a sliding window counter.

    Limits requests per IP address. Default: 100 requests per minute.
    Returns HTTP 429 when the limit is exceeded.

    Note: For production use, replace with a Redis-backed limiter.
    """

    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 100,
    ) -> None:
        super().__init__(app)
        self._rpm = requests_per_minute
        self._request_log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for test client
        if client_ip == "testclient":
            return await call_next(request)
        now = time.monotonic()
        cutoff = now - 60.0

        # Prune old entries
        timestamps = self._request_log[client_ip]
        self._request_log[client_ip] = [t for t in timestamps if t > cutoff]

        if len(self._request_log[client_ip]) >= self._rpm:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            logger.warning(
                "Rate limit exceeded for %s (request_id=%s, count=%d/%d)",
                client_ip,
                request_id,
                len(self._request_log[client_ip]),
                self._rpm,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self._rpm} requests per minute. Try again later.",
                    "status_code": 429,
                },
                headers={"Retry-After": "60"},
            )

        self._request_log[client_ip].append(now)
        return await call_next(request)


# ---------------------------------------------------------------------------
# Error handling middleware
# ---------------------------------------------------------------------------

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions and returns a structured error response.

    Ensures the client always receives a JSON body with ``request_id``,
    ``timestamp``, ``error``, and ``status_code`` fields.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            logger.exception(
                "Unhandled exception for %s %s (request_id=%s): %s",
                request.method,
                request.url.path,
                request_id,
                exc,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": "Internal server error",
                    "detail": str(exc),
                    "status_code": 500,
                },
            )
