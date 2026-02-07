"""
Integration tests for the FastAPI server (src/api/app.py).

Tests REST API endpoints for health checks, prediction requests,
individual scoring models, and error handling. Uses a test client
that mimics the expected API interface.
"""

import pytest
import json
from dataclasses import dataclass, field
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Lightweight mock FastAPI test client
# ---------------------------------------------------------------------------
# Since src/api/app.py is being created by another agent, we implement a
# reference test client that mirrors the expected API contract.

class MockResponse:
    """Simulates an HTTP response."""

    def __init__(self, status_code: int, json_data: dict | list | None = None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is not None:
            return self._json_data
        raise ValueError("No JSON content")


class SafetyAPITestClient:
    """Reference test client implementing the expected API contract.

    This client simulates the FastAPI application endpoints for testing
    before the actual app is built. Validates request/response contracts.
    """

    def __init__(self):
        self._models_healthy = True

    def get(self, url: str, params: dict | None = None) -> MockResponse:
        """Simulate a GET request."""
        if url == "/api/v1/health":
            return self._handle_health()
        elif url == "/api/v1/scores/easix":
            return self._handle_easix(params or {})
        elif url == "/api/v1/scores/hscore":
            return self._handle_hscore(params or {})
        elif url == "/api/v1/scores/car-hematotox":
            return self._handle_car_hematotox(params or {})
        elif url == "/api/v1/models/status":
            return self._handle_models_status()
        return MockResponse(404, {"error": "Not found"})

    def post(self, url: str, json: dict | list | None = None) -> MockResponse:
        """Simulate a POST request."""
        if url == "/api/v1/predict":
            return self._handle_predict(json)
        elif url == "/api/v1/predict/batch":
            return self._handle_batch_predict(json)
        return MockResponse(404, {"error": "Not found"})

    # ------------------------------------------------------------------
    # Endpoint handlers
    # ------------------------------------------------------------------

    def _handle_health(self) -> MockResponse:
        return MockResponse(200, {
            "status": "healthy",
            "version": "0.1.0",
            "models_available": self._models_healthy,
        })

    def _handle_predict(self, body: dict | None) -> MockResponse:
        if body is None:
            return MockResponse(422, {"detail": "Request body required"})

        # Validate required fields
        patient_id = body.get("patient_id")
        if not patient_id:
            return MockResponse(422, {"detail": "patient_id is required"})

        baseline_labs = body.get("baseline_labs", {})

        # Validate lab values
        for key, value in baseline_labs.items():
            if not isinstance(value, (int, float)):
                return MockResponse(
                    400,
                    {"detail": f"Invalid lab value for {key}: expected numeric, got {type(value).__name__}"},
                )
            if value < 0:
                return MockResponse(
                    400,
                    {"detail": f"Invalid lab value for {key}: negative values not allowed"},
                )

        # Compute a simple risk score from available data
        risk_score = self._compute_mock_risk(baseline_labs)

        return MockResponse(200, {
            "patient_id": patient_id,
            "risk_score": risk_score,
            "risk_category": "high" if risk_score > 0.6 else "moderate" if risk_score > 0.3 else "low",
            "confidence": 0.85,
            "safety_index": {
                "overall_risk": risk_score,
                "crs_risk": risk_score * 0.9,
                "icans_risk": risk_score * 0.5,
                "hlh_risk": risk_score * 0.3,
            },
            "alerts": [],
        })

    def _handle_batch_predict(self, body: list | dict | None) -> MockResponse:
        if body is None:
            return MockResponse(422, {"detail": "Request body required"})

        if isinstance(body, dict):
            patients = body.get("patients", [])
        elif isinstance(body, list):
            patients = body
        else:
            return MockResponse(400, {"detail": "Invalid request body"})

        results = []
        for patient in patients:
            response = self._handle_predict(patient)
            results.append(response.json())

        return MockResponse(200, {"results": results, "count": len(results)})

    def _handle_easix(self, params: dict) -> MockResponse:
        ldh = params.get("ldh")
        creatinine = params.get("creatinine")
        platelets = params.get("platelets")

        if ldh is None or creatinine is None or platelets is None:
            return MockResponse(422, {"detail": "ldh, creatinine, and platelets are required"})

        try:
            ldh = float(ldh)
            creatinine = float(creatinine)
            platelets = float(platelets)
        except (ValueError, TypeError):
            return MockResponse(400, {"detail": "Parameters must be numeric"})

        if platelets == 0:
            return MockResponse(400, {"detail": "Platelets cannot be zero"})

        score = (ldh * creatinine) / platelets
        return MockResponse(200, {
            "score": score,
            "inputs": {"ldh": ldh, "creatinine": creatinine, "platelets": platelets},
        })

    def _handle_hscore(self, params: dict) -> MockResponse:
        # Simplified: accepts temperature and ferritin at minimum
        temperature = params.get("temperature_c")
        if temperature is not None:
            try:
                temperature = float(temperature)
            except (ValueError, TypeError):
                return MockResponse(400, {"detail": "temperature_c must be numeric"})

        ferritin = params.get("ferritin_ng_ml")
        if ferritin is not None:
            try:
                ferritin = float(ferritin)
            except (ValueError, TypeError):
                return MockResponse(400, {"detail": "ferritin_ng_ml must be numeric"})

        score = 0
        if temperature is not None and temperature > 39.4:
            score += 49
        if ferritin is not None and ferritin > 6000:
            score += 50

        return MockResponse(200, {"score": score, "partial": True})

    def _handle_car_hematotox(self, params: dict) -> MockResponse:
        score = 0
        anc = params.get("anc_k_ul")
        if anc is not None:
            try:
                anc = float(anc)
                if anc < 0.5:
                    score += 2
                elif anc < 1.5:
                    score += 1
            except (ValueError, TypeError):
                return MockResponse(400, {"detail": "anc_k_ul must be numeric"})

        return MockResponse(200, {"score": score})

    def _handle_models_status(self) -> MockResponse:
        return MockResponse(200, {
            "models": [
                {"model_id": "claude-opus-4", "status": "available", "latency_ms": 3000},
                {"model_id": "gpt-5.2", "status": "available", "latency_ms": 2000},
                {"model_id": "gemini-3", "status": "available", "latency_ms": 1500},
            ],
            "total_available": 3,
        })

    def _compute_mock_risk(self, labs: dict) -> float:
        """Compute a mock risk score from lab values."""
        score = 0.0
        count = 0

        il6 = labs.get("il6_pg_ml", 0)
        if il6 > 0:
            score += min(1.0, il6 / 100.0)
            count += 1

        ferritin = labs.get("ferritin_ng_ml", 0)
        if ferritin > 0:
            score += min(1.0, ferritin / 5000.0)
            count += 1

        crp = labs.get("crp_mg_l", 0)
        if crp > 0:
            score += min(1.0, crp / 200.0)
            count += 1

        if count == 0:
            return 0.25  # Default when no data

        return min(1.0, score / count)


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def client():
    return SafetyAPITestClient()


@pytest.fixture
def valid_predict_body():
    """Valid prediction request body."""
    return {
        "patient_id": "TEST-API-001",
        "baseline_labs": {
            "il6_pg_ml": 48.0,
            "ferritin_ng_ml": 2200.0,
            "crp_mg_l": 85.0,
            "ldh_u_l": 620.0,
        },
        "treatment": {
            "product": "axi-cel",
            "dose_cells": 5e6,
        },
    }


@pytest.fixture
def minimal_predict_body():
    """Minimal valid prediction request."""
    return {
        "patient_id": "TEST-API-002",
        "baseline_labs": {},
    }


# ===========================================================================
# Tests
# ===========================================================================

@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_has_status(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_version(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "version" in data

    def test_health_has_models_available(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "models_available" in data


@pytest.mark.integration
class TestPredictEndpointValid:
    """Tests for POST /api/v1/predict with valid data."""

    def test_predict_returns_200(self, client, valid_predict_body):
        response = client.post("/api/v1/predict", json=valid_predict_body)
        assert response.status_code == 200

    def test_predict_returns_patient_id(self, client, valid_predict_body):
        response = client.post("/api/v1/predict", json=valid_predict_body)
        data = response.json()
        assert data["patient_id"] == "TEST-API-001"

    def test_predict_returns_risk_score(self, client, valid_predict_body):
        response = client.post("/api/v1/predict", json=valid_predict_body)
        data = response.json()
        assert 0.0 <= data["risk_score"] <= 1.0

    def test_predict_returns_risk_category(self, client, valid_predict_body):
        response = client.post("/api/v1/predict", json=valid_predict_body)
        data = response.json()
        assert data["risk_category"] in ("low", "moderate", "high", "critical")

    def test_predict_returns_safety_index(self, client, valid_predict_body):
        response = client.post("/api/v1/predict", json=valid_predict_body)
        data = response.json()
        assert "safety_index" in data
        si = data["safety_index"]
        assert "overall_risk" in si
        assert "crs_risk" in si


@pytest.mark.integration
class TestPredictEndpointMissingData:
    """Tests for POST /api/v1/predict with missing data."""

    def test_predict_no_body_returns_422(self, client):
        response = client.post("/api/v1/predict", json=None)
        assert response.status_code == 422

    def test_predict_no_patient_id_returns_422(self, client):
        response = client.post("/api/v1/predict", json={"baseline_labs": {}})
        assert response.status_code == 422

    def test_predict_empty_labs_returns_200(self, client, minimal_predict_body):
        """Empty labs should still succeed with default risk."""
        response = client.post("/api/v1/predict", json=minimal_predict_body)
        assert response.status_code == 200


@pytest.mark.integration
class TestPredictEndpointInvalidData:
    """Tests for POST /api/v1/predict with invalid data."""

    def test_predict_string_lab_value_returns_400(self, client):
        body = {
            "patient_id": "TEST-BAD",
            "baseline_labs": {"il6_pg_ml": "high"},
        }
        response = client.post("/api/v1/predict", json=body)
        assert response.status_code == 400

    def test_predict_negative_lab_value_returns_400(self, client):
        body = {
            "patient_id": "TEST-BAD",
            "baseline_labs": {"crp_mg_l": -10.0},
        }
        response = client.post("/api/v1/predict", json=body)
        assert response.status_code == 400


@pytest.mark.integration
class TestEASIXEndpoint:
    """Tests for GET /api/v1/scores/easix."""

    def test_easix_valid(self, client):
        response = client.get("/api/v1/scores/easix", params={
            "ldh": "200", "creatinine": "1.0", "platelets": "200",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == pytest.approx(1.0)

    def test_easix_missing_params_returns_422(self, client):
        response = client.get("/api/v1/scores/easix", params={"ldh": "200"})
        assert response.status_code == 422

    def test_easix_platelets_zero_returns_400(self, client):
        response = client.get("/api/v1/scores/easix", params={
            "ldh": "200", "creatinine": "1.0", "platelets": "0",
        })
        assert response.status_code == 400


@pytest.mark.integration
class TestHScoreEndpoint:
    """Tests for GET /api/v1/scores/hscore."""

    def test_hscore_with_temperature(self, client):
        response = client.get("/api/v1/scores/hscore", params={
            "temperature_c": "40.0",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["score"] >= 49  # High temp contribution

    def test_hscore_invalid_temperature(self, client):
        response = client.get("/api/v1/scores/hscore", params={
            "temperature_c": "not_a_number",
        })
        assert response.status_code == 400


@pytest.mark.integration
class TestCARHematotoxEndpoint:
    """Tests for GET /api/v1/scores/car-hematotox."""

    def test_car_hematotox_low_anc(self, client):
        response = client.get("/api/v1/scores/car-hematotox", params={
            "anc_k_ul": "0.3",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 2

    def test_car_hematotox_normal_anc(self, client):
        response = client.get("/api/v1/scores/car-hematotox", params={
            "anc_k_ul": "5.0",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0


@pytest.mark.integration
class TestModelsStatusEndpoint:
    """Tests for GET /api/v1/models/status."""

    def test_models_status_returns_200(self, client):
        response = client.get("/api/v1/models/status")
        assert response.status_code == 200

    def test_models_status_has_models(self, client):
        response = client.get("/api/v1/models/status")
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0

    def test_models_status_has_total(self, client):
        response = client.get("/api/v1/models/status")
        data = response.json()
        assert data["total_available"] == 3


@pytest.mark.integration
class TestBatchPrediction:
    """Tests for batch prediction endpoint."""

    def test_batch_predict_multiple_patients(self, client):
        body = {
            "patients": [
                {"patient_id": "P1", "baseline_labs": {"il6_pg_ml": 10.0}},
                {"patient_id": "P2", "baseline_labs": {"il6_pg_ml": 500.0}},
                {"patient_id": "P3", "baseline_labs": {"il6_pg_ml": 50.0}},
            ]
        }
        response = client.post("/api/v1/predict/batch", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_batch_predict_empty_list(self, client):
        body = {"patients": []}
        response = client.post("/api/v1/predict/batch", json=body)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


@pytest.mark.integration
class TestErrorResponses:
    """Tests for proper error response formats."""

    def test_404_for_unknown_route(self, client):
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_422_has_detail(self, client):
        response = client.post("/api/v1/predict", json=None)
        data = response.json()
        assert "detail" in data

    def test_400_has_detail(self, client):
        response = client.post("/api/v1/predict", json={
            "patient_id": "P1",
            "baseline_labs": {"crp_mg_l": "not_a_number"},
        })
        data = response.json()
        assert "detail" in data
