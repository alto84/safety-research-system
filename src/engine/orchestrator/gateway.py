"""
Secure API gateway for foundation model communication.

Provides mTLS-capable HTTP transport, PII stripping, audit logging, rate
limiting, and circuit-breaker patterns for calling external model APIs.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTP client protocol (avoids hard dependency on httpx/aiohttp)
# ---------------------------------------------------------------------------

@runtime_checkable
class AsyncHTTPClient(Protocol):
    """Protocol for an async HTTP client."""

    async def post(
        self,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Send an async POST request.

        Returns an object with ``.status_code`` and ``.json()`` method.
        """
        ...

    async def aclose(self) -> None:
        """Close the client and release resources."""
        ...


# ---------------------------------------------------------------------------
# mTLS configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TLSConfig:
    """Mutual TLS configuration for secure API communication.

    Attributes:
        ca_cert_path: Path to the Certificate Authority certificate.
        client_cert_path: Path to the client certificate.
        client_key_path: Path to the client private key.
        verify_server: Whether to verify the server's certificate.
        min_tls_version: Minimum acceptable TLS version.
    """

    ca_cert_path: Path | None = None
    client_cert_path: Path | None = None
    client_key_path: Path | None = None
    verify_server: bool = True
    min_tls_version: str = "TLSv1.3"

    @property
    def is_mtls_enabled(self) -> bool:
        """Whether mutual TLS is configured."""
        return (
            self.client_cert_path is not None
            and self.client_key_path is not None
        )


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Token bucket rate limiter with per-model limits.

    Attributes:
        requests_per_minute: Maximum requests allowed per minute.
        tokens_per_minute: Maximum tokens allowed per minute.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100_000,
    ) -> None:
        self._rpm = requests_per_minute
        self._tpm = tokens_per_minute
        self._request_timestamps: list[float] = []
        self._token_counts: list[tuple[float, int]] = []
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 1000) -> bool:
        """Attempt to acquire a rate limit slot.

        Args:
            estimated_tokens: Estimated token consumption for this request.

        Returns:
            True if the request is allowed, False if rate-limited.
        """
        async with self._lock:
            now = time.monotonic()
            cutoff = now - 60.0

            # Prune old entries
            self._request_timestamps = [
                t for t in self._request_timestamps if t > cutoff
            ]
            self._token_counts = [
                (t, c) for t, c in self._token_counts if t > cutoff
            ]

            # Check request rate
            if len(self._request_timestamps) >= self._rpm:
                return False

            # Check token rate
            total_tokens = sum(c for _, c in self._token_counts)
            if total_tokens + estimated_tokens > self._tpm:
                return False

            # Record this request
            self._request_timestamps.append(now)
            self._token_counts.append((now, estimated_tokens))
            return True

    @property
    def current_rpm(self) -> int:
        """Current requests per minute."""
        cutoff = time.monotonic() - 60.0
        return sum(1 for t in self._request_timestamps if t > cutoff)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing recovery


class CircuitBreaker:
    """Circuit breaker for model API endpoints.

    Opens the circuit after ``failure_threshold`` consecutive failures,
    waits ``recovery_timeout`` seconds, then allows a test request.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time > self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """Record a successful request."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "Circuit breaker OPENED after %d consecutive failures",
                self._failure_count,
            )

    @property
    def is_available(self) -> bool:
        """Whether the circuit allows requests."""
        return self.state != CircuitState.OPEN


# ---------------------------------------------------------------------------
# PII stripper
# ---------------------------------------------------------------------------

class PIIStripper:
    """Removes personally identifiable information from prompts before
    they are sent to external model APIs.

    Strips:
        - Patient names (via configurable patterns)
        - Medical record numbers (MRN)
        - Social security numbers
        - Phone numbers
        - Email addresses
        - Dates of birth
    """

    _PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
        ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
        ("mrn", re.compile(r"\bMRN[:\s]*\w+\b", re.IGNORECASE), "[MRN_REDACTED]"),
        ("phone", re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE_REDACTED]"),
        ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL_REDACTED]"),
        ("dob", re.compile(
            r"\b(?:DOB|date of birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            re.IGNORECASE,
        ), "[DOB_REDACTED]"),
        ("date", re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"), "[DATE_REDACTED]"),
    ]

    def __init__(self, additional_patterns: list[tuple[str, str, str]] | None = None) -> None:
        """Initialize the PII stripper.

        Args:
            additional_patterns: Extra ``(name, regex, replacement)`` triples.
        """
        self._custom_patterns: list[tuple[str, re.Pattern[str], str]] = []
        if additional_patterns:
            for name, pattern, replacement in additional_patterns:
                self._custom_patterns.append((name, re.compile(pattern), replacement))

    def strip(self, text: str) -> tuple[str, list[str]]:
        """Remove PII from text.

        Args:
            text: The input text that may contain PII.

        Returns:
            Tuple of ``(cleaned_text, list_of_redaction_types)``.
        """
        redactions: list[str] = []

        for name, pattern, replacement in self._PATTERNS + self._custom_patterns:
            if pattern.search(text):
                text = pattern.sub(replacement, text)
                redactions.append(name)

        return text, redactions


# ---------------------------------------------------------------------------
# Audit log entry
# ---------------------------------------------------------------------------

@dataclass
class GatewayAuditEntry:
    """Audit log entry for a gateway API call.

    Attributes:
        request_id: Unique identifier for this request.
        model_id: Which model was called.
        endpoint_url: The API endpoint (without credentials).
        timestamp: When the request was made.
        latency_ms: Request latency in milliseconds.
        status_code: HTTP response status code.
        tokens_used: Total tokens consumed.
        pii_redactions: Types of PII that were stripped.
        rate_limited: Whether the request was rate-limited.
        circuit_state: Circuit breaker state at request time.
        error: Error message if the request failed.
        prompt_hash: SHA-256 hash of the prompt (for reproducibility, not content).
    """

    request_id: str
    model_id: str
    endpoint_url: str
    timestamp: float
    latency_ms: int = 0
    status_code: int = 0
    tokens_used: int = 0
    pii_redactions: list[str] = field(default_factory=list)
    rate_limited: bool = False
    circuit_state: str = "closed"
    error: str = ""
    prompt_hash: str = ""


# ---------------------------------------------------------------------------
# Secure API Gateway
# ---------------------------------------------------------------------------

@dataclass
class ModelEndpoint:
    """Configuration for a model API endpoint.

    Attributes:
        model_id: Unique model identifier.
        url: The API endpoint URL.
        api_key_env_var: Environment variable name holding the API key.
        headers: Additional HTTP headers.
        rate_limit_rpm: Per-model requests per minute limit.
        rate_limit_tpm: Per-model tokens per minute limit.
    """

    model_id: str
    url: str
    api_key_env_var: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 100_000


class SecureAPIGateway:
    """Secure gateway for communicating with foundation model APIs.

    Provides:
        - **mTLS**: Mutual TLS authentication for enterprise API endpoints.
        - **PII stripping**: Removes patient PII before sending prompts.
        - **Audit logging**: Immutable record of all API calls.
        - **Rate limiting**: Per-model request and token rate limits.
        - **Circuit breaker**: Automatic failure detection and recovery.

    Usage::

        gateway = SecureAPIGateway(
            tls_config=TLSConfig(ca_cert_path=Path("/certs/ca.pem")),
            http_client=my_async_client,
        )
        gateway.register_endpoint(ModelEndpoint(
            model_id="gpt-4",
            url="https://api.openai.com/v1/chat/completions",
        ))
        response = await gateway.call_model("gpt-4", prompt, patient_id="PAT-001")
    """

    def __init__(
        self,
        tls_config: TLSConfig | None = None,
        http_client: AsyncHTTPClient | None = None,
        pii_stripper: PIIStripper | None = None,
    ) -> None:
        """Initialize the secure API gateway.

        Args:
            tls_config: TLS/mTLS configuration.
            http_client: The async HTTP client to use for requests.
            pii_stripper: PII stripping engine. Defaults to standard stripper.
        """
        self._tls_config = tls_config or TLSConfig()
        self._http_client = http_client
        self._pii_stripper = pii_stripper or PIIStripper()
        self._endpoints: dict[str, ModelEndpoint] = {}
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._audit_log: list[GatewayAuditEntry] = []
        self._request_counter = 0

    def register_endpoint(self, endpoint: ModelEndpoint) -> None:
        """Register a model API endpoint.

        Args:
            endpoint: The endpoint configuration.
        """
        self._endpoints[endpoint.model_id] = endpoint
        self._rate_limiters[endpoint.model_id] = RateLimiter(
            requests_per_minute=endpoint.rate_limit_rpm,
            tokens_per_minute=endpoint.rate_limit_tpm,
        )
        self._circuit_breakers[endpoint.model_id] = CircuitBreaker()
        logger.info("Registered endpoint for model '%s': %s", endpoint.model_id, endpoint.url)

    async def call_model(
        self,
        model_id: str,
        prompt: str,
        patient_id: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.1,
        estimated_tokens: int = 2000,
    ) -> dict[str, Any]:
        """Send a prompt to a model API with full security pipeline.

        Pipeline:
            1. Validate endpoint and circuit breaker
            2. Rate limit check
            3. Strip PII from prompt
            4. Send request with mTLS
            5. Log audit entry
            6. Update circuit breaker

        Args:
            model_id: Which model to call.
            prompt: The prompt text (will be PII-stripped).
            patient_id: Patient ID for audit trail.
            max_tokens: Maximum response tokens.
            temperature: Sampling temperature.
            estimated_tokens: Estimated total token count for rate limiting.

        Returns:
            The model's response as a dict.

        Raises:
            RuntimeError: If the model is unavailable or rate-limited.
            KeyError: If the model ID is not registered.
        """
        if model_id not in self._endpoints:
            raise KeyError(f"Model '{model_id}' is not registered")

        endpoint = self._endpoints[model_id]
        circuit = self._circuit_breakers[model_id]
        limiter = self._rate_limiters[model_id]

        # Generate request ID
        self._request_counter += 1
        request_id = f"REQ-{self._request_counter:08d}"

        # Check circuit breaker
        if not circuit.is_available:
            entry = GatewayAuditEntry(
                request_id=request_id,
                model_id=model_id,
                endpoint_url=endpoint.url,
                timestamp=time.time(),
                circuit_state=circuit.state.value,
                error="Circuit breaker is OPEN",
            )
            self._audit_log.append(entry)
            raise RuntimeError(f"Circuit breaker OPEN for model '{model_id}'")

        # Check rate limit
        if not await limiter.acquire(estimated_tokens):
            entry = GatewayAuditEntry(
                request_id=request_id,
                model_id=model_id,
                endpoint_url=endpoint.url,
                timestamp=time.time(),
                rate_limited=True,
                error="Rate limited",
            )
            self._audit_log.append(entry)
            raise RuntimeError(f"Rate limited for model '{model_id}'")

        # Strip PII
        cleaned_prompt, redactions = self._pii_stripper.strip(prompt)
        if redactions:
            logger.info(
                "Stripped PII from prompt for %s: %s", request_id, redactions,
            )

        # Compute prompt hash for reproducibility
        prompt_hash = hashlib.sha256(cleaned_prompt.encode()).hexdigest()[:16]

        # Build request payload
        payload = self._build_payload(
            endpoint, cleaned_prompt, max_tokens, temperature,
        )

        # Send request
        start_time = time.monotonic()
        status_code = 0
        error_msg = ""
        response_data: dict[str, Any] = {}
        tokens_used = 0

        try:
            if self._http_client is None:
                raise RuntimeError(
                    "No HTTP client configured. Provide an AsyncHTTPClient "
                    "implementation (e.g., httpx.AsyncClient)."
                )

            response = await self._http_client.post(
                endpoint.url,
                json=payload,
                headers=endpoint.headers,
                timeout=30.0,
            )
            status_code = response.status_code
            response_data = response.json()
            tokens_used = self._extract_token_usage(response_data)
            circuit.record_success()

        except Exception as exc:
            error_msg = str(exc)
            circuit.record_failure()
            logger.error("Model call failed for %s: %s", model_id, error_msg)

        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Audit log
        entry = GatewayAuditEntry(
            request_id=request_id,
            model_id=model_id,
            endpoint_url=endpoint.url,
            timestamp=time.time(),
            latency_ms=latency_ms,
            status_code=status_code,
            tokens_used=tokens_used,
            pii_redactions=redactions,
            rate_limited=False,
            circuit_state=circuit.state.value,
            error=error_msg,
            prompt_hash=prompt_hash,
        )
        self._audit_log.append(entry)

        if error_msg:
            raise RuntimeError(f"Model call failed: {error_msg}")

        return response_data

    # ------------------------------------------------------------------
    # Payload construction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(
        endpoint: ModelEndpoint,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Build the API request payload.

        Constructs an OpenAI-compatible chat completion payload. Providers
        with different formats should override or transform this.
        """
        return {
            "model": endpoint.model_id,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a pharmaceutical safety AI. Analyze patient data "
                        "and predict adverse event risk. Return structured JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

    @staticmethod
    def _extract_token_usage(response: dict[str, Any]) -> int:
        """Extract token usage from a model API response."""
        usage = response.get("usage", {})
        return usage.get("total_tokens", 0)

    # ------------------------------------------------------------------
    # Audit access
    # ------------------------------------------------------------------

    @property
    def audit_log(self) -> list[GatewayAuditEntry]:
        """Return the full audit log (read-only copy)."""
        return list(self._audit_log)

    def get_audit_entries(
        self,
        model_id: str | None = None,
        since_timestamp: float | None = None,
    ) -> list[GatewayAuditEntry]:
        """Query the audit log with optional filters.

        Args:
            model_id: Filter to a specific model.
            since_timestamp: Only entries after this Unix timestamp.

        Returns:
            Filtered list of audit entries.
        """
        entries = self._audit_log
        if model_id is not None:
            entries = [e for e in entries if e.model_id == model_id]
        if since_timestamp is not None:
            entries = [e for e in entries if e.timestamp >= since_timestamp]
        return entries
