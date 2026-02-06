"""
Response normalizer for heterogeneous model outputs.

Foundation models return predictions in different formats -- some as free text,
some as JSON, some with nested structures. The ResponseNormalizer converts all
of these into a standardized SafetyPrediction dataclass that downstream
components (ensemble, alerts, audit) can consume uniformly.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Standardized prediction dataclass
# ---------------------------------------------------------------------------

@dataclass
class SafetyPrediction:
    """Normalized prediction from a single foundation model.

    This is the canonical format that all model outputs are converted into.

    Attributes:
        model_id: Which model produced this prediction.
        patient_id: The patient being assessed.
        adverse_event: The adverse event type (e.g. ``'CRS'``).
        risk_score: Predicted risk score (0.0 - 1.0).
        confidence: Model's confidence in the prediction (0.0 - 1.0).
        reasoning: Human-readable explanation of the prediction.
        key_drivers: Top factors driving the risk score.
        raw_response: The original unmodified model response.
        latency_ms: How long the model call took.
        tokens_used: Total tokens consumed (prompt + completion).
        timestamp: When the prediction was generated.
        metadata: Additional model-specific metadata.
    """

    model_id: str
    patient_id: str
    adverse_event: str
    risk_score: float
    confidence: float
    reasoning: str = ""
    key_drivers: list[str] = field(default_factory=list)
    raw_response: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    tokens_used: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.risk_score = max(0.0, min(1.0, self.risk_score))
        self.confidence = max(0.0, min(1.0, self.confidence))

    def to_model_prediction_dict(self) -> dict[str, float]:
        """Convert to the dict format expected by PatientRiskScorer.

        Returns:
            Dict with ``score``, ``confidence``, and ``model_name`` keys.
        """
        return {
            "score": self.risk_score,
            "confidence": self.confidence,
            "model_name": self.model_id,
        }


# ---------------------------------------------------------------------------
# Normalization strategies
# ---------------------------------------------------------------------------

class ResponseNormalizer:
    """Converts heterogeneous model responses into SafetyPrediction objects.

    Handles three response formats:
        1. **Structured JSON** -- preferred, parsed directly.
        2. **JSON embedded in text** -- extracted via regex and parsed.
        3. **Free text** -- parsed with heuristic extraction of scores and reasoning.

    Usage::

        normalizer = ResponseNormalizer()
        prediction = normalizer.normalize(
            raw_response=model_output,
            model_id="gpt-4",
            patient_id="PAT-001",
            adverse_event="CRS",
            latency_ms=1200,
        )
    """

    # Regex to find JSON blocks in text (handles code fences)
    _JSON_BLOCK_PATTERN = re.compile(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        re.DOTALL,
    )
    _BARE_JSON_PATTERN = re.compile(r"\{[^{}]*\}", re.DOTALL)

    # Patterns for extracting risk scores from free text
    _SCORE_PATTERNS = [
        re.compile(r"risk[_ ]?score[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
        re.compile(r"score[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
        re.compile(r"risk[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
        re.compile(r"probability[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
    ]

    _CONFIDENCE_PATTERNS = [
        re.compile(r"confidence[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
        re.compile(r"certainty[:\s]*([0-9]*\.?[0-9]+)", re.IGNORECASE),
    ]

    def normalize(
        self,
        raw_response: dict[str, Any] | str,
        model_id: str,
        patient_id: str,
        adverse_event: str,
        latency_ms: int = 0,
        tokens_used: int = 0,
    ) -> SafetyPrediction:
        """Normalize a model response into a SafetyPrediction.

        Attempts structured JSON parsing first, then JSON extraction from text,
        then free-text heuristic extraction as a fallback.

        Args:
            raw_response: The model's response (dict or string).
            model_id: Which model produced the response.
            patient_id: The patient being assessed.
            adverse_event: The adverse event type.
            latency_ms: Call latency in milliseconds.
            tokens_used: Total tokens consumed.

        Returns:
            A normalized SafetyPrediction.
        """
        # Convert string responses to dict if possible
        if isinstance(raw_response, str):
            parsed = self._try_parse_json(raw_response)
            if parsed is not None:
                return self._from_structured(
                    parsed, raw_response, model_id, patient_id,
                    adverse_event, latency_ms, tokens_used,
                )
            return self._from_free_text(
                raw_response, model_id, patient_id,
                adverse_event, latency_ms, tokens_used,
            )

        if isinstance(raw_response, dict):
            # Check if the dict wraps a text completion (common API format)
            text_content = self._extract_text_from_api_response(raw_response)
            if text_content:
                inner_parsed = self._try_parse_json(text_content)
                if inner_parsed is not None:
                    return self._from_structured(
                        inner_parsed, raw_response, model_id, patient_id,
                        adverse_event, latency_ms, tokens_used,
                    )
                return self._from_free_text(
                    text_content, model_id, patient_id,
                    adverse_event, latency_ms, tokens_used,
                    raw_dict=raw_response,
                )

            # Direct structured dict
            return self._from_structured(
                raw_response, raw_response, model_id, patient_id,
                adverse_event, latency_ms, tokens_used,
            )

        logger.warning(
            "Unexpected response type %s from model %s; returning zero prediction",
            type(raw_response).__name__, model_id,
        )
        return SafetyPrediction(
            model_id=model_id,
            patient_id=patient_id,
            adverse_event=adverse_event,
            risk_score=0.0,
            confidence=0.0,
            reasoning="Failed to parse model response",
            raw_response={"error": "unparseable", "type": type(raw_response).__name__},
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )

    # ------------------------------------------------------------------
    # Parsing strategies
    # ------------------------------------------------------------------

    def _from_structured(
        self,
        data: dict[str, Any],
        raw: Any,
        model_id: str,
        patient_id: str,
        adverse_event: str,
        latency_ms: int,
        tokens_used: int,
    ) -> SafetyPrediction:
        """Build SafetyPrediction from a structured dict."""
        risk_score = self._extract_float(data, [
            "risk_score", "riskScore", "score", "risk", "probability",
        ], default=0.0)

        confidence = self._extract_float(data, [
            "confidence", "certainty", "conf",
        ], default=0.5)

        reasoning = data.get("reasoning") or data.get("explanation") or data.get("rationale") or ""

        key_drivers = data.get("key_drivers") or data.get("drivers") or data.get("factors") or []
        if isinstance(key_drivers, str):
            key_drivers = [d.strip() for d in key_drivers.split(",")]

        return SafetyPrediction(
            model_id=model_id,
            patient_id=patient_id,
            adverse_event=data.get("adverse_event", adverse_event),
            risk_score=risk_score,
            confidence=confidence,
            reasoning=str(reasoning),
            key_drivers=list(key_drivers),
            raw_response=raw if isinstance(raw, dict) else {"text": str(raw)},
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )

    def _from_free_text(
        self,
        text: str,
        model_id: str,
        patient_id: str,
        adverse_event: str,
        latency_ms: int,
        tokens_used: int,
        raw_dict: dict[str, Any] | None = None,
    ) -> SafetyPrediction:
        """Build SafetyPrediction by extracting values from free text."""
        risk_score = self._extract_score_from_text(text, self._SCORE_PATTERNS, 0.0)
        confidence = self._extract_score_from_text(text, self._CONFIDENCE_PATTERNS, 0.3)

        # If score is > 1, assume it's a percentage
        if risk_score > 1.0:
            risk_score = risk_score / 100.0
        if confidence > 1.0:
            confidence = confidence / 100.0

        # Use the full text as reasoning (truncated)
        reasoning = text[:2000] if len(text) > 2000 else text

        logger.info(
            "Free-text extraction from %s: score=%.3f, confidence=%.3f",
            model_id, risk_score, confidence,
        )

        return SafetyPrediction(
            model_id=model_id,
            patient_id=patient_id,
            adverse_event=adverse_event,
            risk_score=risk_score,
            confidence=confidence,
            reasoning=reasoning,
            raw_response=raw_dict or {"text": text},
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={"parse_method": "free_text"},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_parse_json(self, text: str) -> dict[str, Any] | None:
        """Attempt to parse JSON from text, handling code fences."""
        # Try direct parse first
        text_stripped = text.strip()
        if text_stripped.startswith("{"):
            try:
                return json.loads(text_stripped)
            except json.JSONDecodeError:
                pass

        # Try extracting from code fences
        match = self._JSON_BLOCK_PATTERN.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding bare JSON object
        match = self._BARE_JSON_PATTERN.search(text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _extract_text_from_api_response(response: dict[str, Any]) -> str | None:
        """Extract the text content from common API response formats.

        Handles OpenAI-style ``choices[0].message.content`` and Anthropic-style
        ``content[0].text`` formats.
        """
        # OpenAI format
        choices = response.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if content:
                return str(content)

        # Anthropic format
        content = response.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict) and "text" in first:
                return str(first["text"])

        # Direct text field
        for key in ("text", "output", "response", "result"):
            if key in response and isinstance(response[key], str):
                return response[key]

        return None

    @staticmethod
    def _extract_float(
        data: dict[str, Any],
        keys: list[str],
        default: float = 0.0,
    ) -> float:
        """Extract a float value from a dict, trying multiple key names."""
        for key in keys:
            value = data.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return default

    @staticmethod
    def _extract_score_from_text(
        text: str,
        patterns: list[re.Pattern[str]],
        default: float,
    ) -> float:
        """Extract a numeric score from free text using regex patterns."""
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return default
