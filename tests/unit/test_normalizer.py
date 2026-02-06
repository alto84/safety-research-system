"""
Tests for ResponseNormalizer — output standardization and edge case handling.

The ResponseNormalizer transforms heterogeneous outputs from different foundation
models (Claude, GPT, Gemini) into the standardized SafetyPrediction format.
"""

import pytest
import json
import math
from datetime import timedelta
from dataclasses import asdict

from tests.conftest import SafetyPrediction, TokenCount


# ---------------------------------------------------------------------------
# ResponseNormalizer reference implementation
# ---------------------------------------------------------------------------

class ResponseNormalizer:
    """Transforms raw model outputs into standardized SafetyPrediction objects."""

    REQUIRED_SEVERITY_GRADES = ["grade_1", "grade_2", "grade_3", "grade_4"]

    def normalize(self, raw_response: dict, model_id: str, latency_ms: int) -> SafetyPrediction:
        """Normalize a raw model response dict into a SafetyPrediction."""
        risk_score = self._extract_risk_score(raw_response)
        confidence = self._extract_confidence(raw_response)
        severity = self._normalize_severity_distribution(raw_response.get("severity_distribution", {}))
        time_horizon = self._extract_time_horizon(raw_response)
        rationale = raw_response.get("mechanistic_rationale", "")
        pathway_refs = raw_response.get("pathway_references", [])
        evidence = raw_response.get("evidence_sources", [])
        tokens = self._extract_token_usage(raw_response)

        return SafetyPrediction(
            risk_score=risk_score,
            confidence=confidence,
            severity_distribution=severity,
            time_horizon=time_horizon,
            mechanistic_rationale=rationale,
            pathway_references=pathway_refs,
            evidence_sources=evidence,
            model_id=model_id,
            latency_ms=latency_ms,
            token_usage=tokens,
        )

    def _extract_risk_score(self, raw: dict) -> float:
        """Extract and clamp risk score to [0.0, 1.0]."""
        score = raw.get("risk_score")
        if score is None:
            raise ValueError("Missing required field: risk_score")
        if not isinstance(score, (int, float)):
            raise TypeError(f"risk_score must be numeric, got {type(score).__name__}")
        if math.isnan(score) or math.isinf(score):
            raise ValueError(f"risk_score must be finite, got {score}")
        return max(0.0, min(1.0, float(score)))

    def _extract_confidence(self, raw: dict) -> float:
        """Extract confidence, default to 0.5 if missing."""
        conf = raw.get("confidence", 0.5)
        if not isinstance(conf, (int, float)):
            return 0.5
        if math.isnan(conf) or math.isinf(conf):
            return 0.5
        return max(0.0, min(1.0, float(conf)))

    def _normalize_severity_distribution(self, dist: dict) -> dict:
        """Ensure severity distribution has all grades and sums to ~1.0."""
        normalized = {}
        for grade in self.REQUIRED_SEVERITY_GRADES:
            val = dist.get(grade, 0.0)
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                val = 0.0
            normalized[grade] = max(0.0, float(val))

        total = sum(normalized.values())
        if total > 0:
            normalized = {k: v / total for k, v in normalized.items()}
        else:
            # Uniform distribution as fallback
            n = len(self.REQUIRED_SEVERITY_GRADES)
            normalized = {k: 1.0 / n for k in self.REQUIRED_SEVERITY_GRADES}

        return normalized

    def _extract_time_horizon(self, raw: dict) -> timedelta:
        """Extract time horizon in hours, default to 72h."""
        hours = raw.get("time_horizon_hours", 72)
        if not isinstance(hours, (int, float)) or hours <= 0:
            return timedelta(hours=72)
        return timedelta(hours=hours)

    def _extract_token_usage(self, raw: dict) -> TokenCount:
        """Extract token usage or return zeros."""
        usage = raw.get("token_usage", {})
        if not isinstance(usage, dict):
            return TokenCount()
        return TokenCount(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )


# ===========================================================================
# Tests
# ===========================================================================

@pytest.fixture
def normalizer():
    return ResponseNormalizer()


@pytest.fixture
def valid_raw_response():
    """A well-formed raw response from a foundation model."""
    return {
        "risk_score": 0.65,
        "confidence": 0.88,
        "severity_distribution": {
            "grade_1": 0.10,
            "grade_2": 0.25,
            "grade_3": 0.40,
            "grade_4": 0.25,
        },
        "time_horizon_hours": 36,
        "mechanistic_rationale": "IL-6 amplification loop detected based on kinetics.",
        "pathway_references": ["pathway:il6_trans_signaling"],
        "evidence_sources": ["il6_elevated", "ferritin_elevated"],
        "token_usage": {
            "prompt_tokens": 2500,
            "completion_tokens": 400,
            "total_tokens": 2900,
        },
    }


class TestRiskScoreExtraction:
    """Tests for _extract_risk_score."""

    def test_valid_score_preserved(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": 0.65}) == 0.65

    def test_score_clamped_above_one(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": 1.5}) == 1.0

    def test_score_clamped_below_zero(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": -0.3}) == 0.0

    def test_zero_score_preserved(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": 0.0}) == 0.0

    def test_one_score_preserved(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": 1.0}) == 1.0

    def test_integer_score_converted(self, normalizer):
        assert normalizer._extract_risk_score({"risk_score": 1}) == 1.0
        assert isinstance(normalizer._extract_risk_score({"risk_score": 1}), float)

    def test_missing_score_raises(self, normalizer):
        with pytest.raises(ValueError, match="Missing required field"):
            normalizer._extract_risk_score({})

    def test_none_score_raises(self, normalizer):
        with pytest.raises(ValueError, match="Missing required field"):
            normalizer._extract_risk_score({"risk_score": None})

    def test_string_score_raises(self, normalizer):
        with pytest.raises(TypeError, match="must be numeric"):
            normalizer._extract_risk_score({"risk_score": "high"})

    def test_nan_score_raises(self, normalizer):
        with pytest.raises(ValueError, match="must be finite"):
            normalizer._extract_risk_score({"risk_score": float("nan")})

    def test_inf_score_raises(self, normalizer):
        with pytest.raises(ValueError, match="must be finite"):
            normalizer._extract_risk_score({"risk_score": float("inf")})


class TestConfidenceExtraction:
    """Tests for _extract_confidence."""

    def test_valid_confidence(self, normalizer):
        assert normalizer._extract_confidence({"confidence": 0.88}) == 0.88

    def test_missing_confidence_defaults_to_half(self, normalizer):
        assert normalizer._extract_confidence({}) == 0.5

    def test_string_confidence_defaults_to_half(self, normalizer):
        assert normalizer._extract_confidence({"confidence": "high"}) == 0.5

    def test_nan_confidence_defaults_to_half(self, normalizer):
        assert normalizer._extract_confidence({"confidence": float("nan")}) == 0.5

    def test_confidence_clamped_above(self, normalizer):
        assert normalizer._extract_confidence({"confidence": 2.0}) == 1.0

    def test_confidence_clamped_below(self, normalizer):
        assert normalizer._extract_confidence({"confidence": -0.5}) == 0.0


class TestSeverityDistribution:
    """Tests for _normalize_severity_distribution."""

    def test_valid_distribution_preserved(self, normalizer):
        dist = {"grade_1": 0.10, "grade_2": 0.25, "grade_3": 0.40, "grade_4": 0.25}
        result = normalizer._normalize_severity_distribution(dist)
        assert abs(sum(result.values()) - 1.0) < 1e-9
        assert set(result.keys()) == {"grade_1", "grade_2", "grade_3", "grade_4"}

    def test_missing_grades_filled_with_zero(self, normalizer):
        dist = {"grade_3": 0.8, "grade_4": 0.2}
        result = normalizer._normalize_severity_distribution(dist)
        assert "grade_1" in result
        assert "grade_2" in result
        assert result["grade_1"] == 0.0
        assert result["grade_2"] == 0.0
        assert abs(sum(result.values()) - 1.0) < 1e-9

    def test_unnormalized_distribution_renormalized(self, normalizer):
        dist = {"grade_1": 2.0, "grade_2": 3.0, "grade_3": 4.0, "grade_4": 1.0}
        result = normalizer._normalize_severity_distribution(dist)
        assert abs(sum(result.values()) - 1.0) < 1e-9
        assert result["grade_3"] == pytest.approx(0.4)

    def test_empty_distribution_becomes_uniform(self, normalizer):
        result = normalizer._normalize_severity_distribution({})
        assert abs(sum(result.values()) - 1.0) < 1e-9
        for v in result.values():
            assert v == pytest.approx(0.25)

    def test_all_zeros_becomes_uniform(self, normalizer):
        dist = {"grade_1": 0.0, "grade_2": 0.0, "grade_3": 0.0, "grade_4": 0.0}
        result = normalizer._normalize_severity_distribution(dist)
        for v in result.values():
            assert v == pytest.approx(0.25)

    def test_negative_values_clamped(self, normalizer):
        dist = {"grade_1": -0.5, "grade_2": 0.3, "grade_3": 0.5, "grade_4": 0.2}
        result = normalizer._normalize_severity_distribution(dist)
        assert result["grade_1"] == 0.0
        assert abs(sum(result.values()) - 1.0) < 1e-9

    def test_nan_values_treated_as_zero(self, normalizer):
        dist = {"grade_1": float("nan"), "grade_2": 0.5, "grade_3": 0.3, "grade_4": 0.2}
        result = normalizer._normalize_severity_distribution(dist)
        assert not math.isnan(result["grade_1"])
        assert abs(sum(result.values()) - 1.0) < 1e-9

    def test_extra_grades_ignored(self, normalizer):
        dist = {"grade_1": 0.25, "grade_2": 0.25, "grade_3": 0.25, "grade_4": 0.25, "grade_5": 0.5}
        result = normalizer._normalize_severity_distribution(dist)
        assert "grade_5" not in result
        assert len(result) == 4


class TestTimeHorizon:
    """Tests for _extract_time_horizon."""

    def test_valid_hours(self, normalizer):
        result = normalizer._extract_time_horizon({"time_horizon_hours": 36})
        assert result == timedelta(hours=36)

    def test_missing_defaults_to_72h(self, normalizer):
        result = normalizer._extract_time_horizon({})
        assert result == timedelta(hours=72)

    def test_zero_hours_defaults(self, normalizer):
        result = normalizer._extract_time_horizon({"time_horizon_hours": 0})
        assert result == timedelta(hours=72)

    def test_negative_hours_defaults(self, normalizer):
        result = normalizer._extract_time_horizon({"time_horizon_hours": -10})
        assert result == timedelta(hours=72)

    def test_string_hours_defaults(self, normalizer):
        result = normalizer._extract_time_horizon({"time_horizon_hours": "soon"})
        assert result == timedelta(hours=72)

    def test_fractional_hours(self, normalizer):
        result = normalizer._extract_time_horizon({"time_horizon_hours": 4.5})
        assert result == timedelta(hours=4.5)


class TestFullNormalization:
    """Tests for the complete normalize() method."""

    def test_valid_response_normalizes_cleanly(self, normalizer, valid_raw_response):
        pred = normalizer.normalize(valid_raw_response, "claude-opus-4", 3200)
        assert pred.risk_score == 0.65
        assert pred.confidence == 0.88
        assert pred.model_id == "claude-opus-4"
        assert pred.latency_ms == 3200
        assert abs(sum(pred.severity_distribution.values()) - 1.0) < 1e-9
        assert pred.time_horizon == timedelta(hours=36)
        assert len(pred.pathway_references) == 1
        assert pred.token_usage.total_tokens == 2900

    def test_minimal_response_fills_defaults(self, normalizer):
        raw = {"risk_score": 0.5}
        pred = normalizer.normalize(raw, "gpt-5.2", 1000)
        assert pred.risk_score == 0.5
        assert pred.confidence == 0.5
        assert pred.time_horizon == timedelta(hours=72)
        assert pred.mechanistic_rationale == ""
        assert pred.pathway_references == []
        assert pred.evidence_sources == []

    def test_missing_risk_score_raises(self, normalizer):
        with pytest.raises(ValueError):
            normalizer.normalize({}, "gemini-3", 1000)

    def test_output_types_correct(self, normalizer, valid_raw_response):
        pred = normalizer.normalize(valid_raw_response, "claude-opus-4", 3200)
        assert isinstance(pred, SafetyPrediction)
        assert isinstance(pred.risk_score, float)
        assert isinstance(pred.confidence, float)
        assert isinstance(pred.severity_distribution, dict)
        assert isinstance(pred.time_horizon, timedelta)
        assert isinstance(pred.token_usage, TokenCount)
