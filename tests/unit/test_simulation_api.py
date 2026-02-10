"""
Unit tests for pharmaceutical company simulation API endpoints.

Tests the 5 simulation endpoints added to population_routes.py:
    - /api/v1/pharma/simulation/run
    - /api/v1/pharma/simulation/status
    - /api/v1/pharma/simulation/log
    - /api/v1/pharma/simulation/deliverables/{role_id}
    - /api/v1/pharma/simulation/tree

Since the simulation module (src/data/pharma_simulation.py) may not exist yet,
tests cover both the unavailable fallback responses and (via mocking) the full
happy-path behavior when the module is present.
"""

import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.data.pharma_org import ORG_ROLES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Mock data for when the simulation module is "available"
# ---------------------------------------------------------------------------

MOCK_SIMULATION_RESULT = {
    "completed": True,
    "total_roles_executed": 10,
    "total_deliverables": 25,
    "duration_seconds": 1.5,
    "delegation_depth": 3,
}

MOCK_SIMULATION_STATUS = {
    "total_roles": 10,
    "active_roles": 3,
    "completed_roles": 7,
    "total_deliverables": 25,
    "completion_pct": 70.0,
}

MOCK_ACTIVITY_LOG = [
    {
        "timestamp": "2026-02-09T12:00:00Z",
        "role_id": "ceo",
        "action": "delegated",
        "detail": "Delegated clinical oversight to CMO",
    },
    {
        "timestamp": "2026-02-09T12:01:00Z",
        "role_id": "cmo",
        "action": "accepted",
        "detail": "Accepted clinical oversight task",
    },
    {
        "timestamp": "2026-02-09T12:02:00Z",
        "role_id": "cmo",
        "action": "delegated",
        "detail": "Delegated trial monitoring to VP Clinical Ops",
    },
]

MOCK_DELIVERABLES = [
    {
        "deliverable_id": "d-001",
        "title": "Clinical Development Plan",
        "status": "completed",
        "delegated_by": "ceo",
    },
    {
        "deliverable_id": "d-002",
        "title": "Site Selection Report",
        "status": "in_progress",
        "delegated_by": "ceo",
    },
]

MOCK_DELEGATION_TREE = {
    "root": "ceo",
    "children": {
        "ceo": ["cmo", "head_cmc", "head_qa", "head_commercial"],
        "cmo": ["vp_clinops", "vp_medaffairs", "head_pv"],
    },
    "total_delegations": 7,
}


# ===========================================================================
# 1. GET /api/v1/pharma/simulation/run
# ===========================================================================

class TestSimulationRun:
    """Tests for the simulation run endpoint."""

    def test_run_returns_200(self, client):
        response = client.get("/api/v1/pharma/simulation/run")
        assert response.status_code == 200

    def test_run_has_request_id(self, client):
        data = client.get("/api/v1/pharma/simulation/run").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
        assert len(data["request_id"]) > 0

    def test_run_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/simulation/run").json()
        assert "timestamp" in data
        # Verify it parses as ISO datetime
        datetime.fromisoformat(data["timestamp"])

    def test_run_request_id_is_valid_uuid(self, client):
        data = client.get("/api/v1/pharma/simulation/run").json()
        uuid.UUID(data["request_id"])  # Raises ValueError if invalid

    def test_run_unavailable_has_status_field(self, client):
        """When simulation module is missing, response should say unavailable."""
        data = client.get("/api/v1/pharma/simulation/run").json()
        # If the simulation module is not yet built, we get an unavailable status
        if "status" in data and data["status"] == "unavailable":
            assert "message" in data
            assert "not yet available" in data["message"]

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._run_simulation", return_value=MOCK_SIMULATION_RESULT)
    def test_run_with_mock_returns_result(self, mock_sim, client):
        data = client.get("/api/v1/pharma/simulation/run").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert data["completed"] is True
        assert data["total_roles_executed"] == 10
        assert data["total_deliverables"] == 25

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._run_simulation", side_effect=RuntimeError("boom"))
    def test_run_exception_returns_500(self, mock_sim, client):
        response = client.get("/api/v1/pharma/simulation/run")
        assert response.status_code == 500
        assert "boom" in response.json()["detail"]


# ===========================================================================
# 2. GET /api/v1/pharma/simulation/status
# ===========================================================================

class TestSimulationStatus:
    """Tests for the simulation status endpoint."""

    def test_status_returns_200(self, client):
        response = client.get("/api/v1/pharma/simulation/status")
        assert response.status_code == 200

    def test_status_has_request_id(self, client):
        data = client.get("/api/v1/pharma/simulation/status").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)

    def test_status_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/simulation/status").json()
        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"])

    def test_status_request_id_is_valid_uuid(self, client):
        data = client.get("/api/v1/pharma/simulation/status").json()
        uuid.UUID(data["request_id"])

    def test_status_unavailable_response(self, client):
        data = client.get("/api/v1/pharma/simulation/status").json()
        if "status" in data and data["status"] == "unavailable":
            assert "message" in data

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_simulation_status", return_value=MOCK_SIMULATION_STATUS)
    def test_status_with_mock_returns_summary(self, mock_status, client):
        data = client.get("/api/v1/pharma/simulation/status").json()
        assert data["total_roles"] == 10
        assert data["completion_pct"] == 70.0
        assert data["active_roles"] == 3
        assert data["completed_roles"] == 7

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_simulation_status", side_effect=RuntimeError("fail"))
    def test_status_exception_returns_500(self, mock_status, client):
        response = client.get("/api/v1/pharma/simulation/status")
        assert response.status_code == 500
        assert "fail" in response.json()["detail"]


# ===========================================================================
# 3. GET /api/v1/pharma/simulation/log
# ===========================================================================

class TestSimulationLog:
    """Tests for the simulation activity log endpoint."""

    def test_log_returns_200(self, client):
        response = client.get("/api/v1/pharma/simulation/log")
        assert response.status_code == 200

    def test_log_has_request_id(self, client):
        data = client.get("/api/v1/pharma/simulation/log").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)

    def test_log_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/simulation/log").json()
        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"])

    def test_log_request_id_is_valid_uuid(self, client):
        data = client.get("/api/v1/pharma/simulation/log").json()
        uuid.UUID(data["request_id"])

    def test_log_default_limit_is_50(self, client):
        """Without a limit parameter, default should be 50."""
        data = client.get("/api/v1/pharma/simulation/log").json()
        if "limit" in data:
            assert data["limit"] == 50

    def test_log_custom_limit(self, client):
        data = client.get("/api/v1/pharma/simulation/log?limit=10").json()
        if "limit" in data:
            assert data["limit"] == 10

    def test_log_limit_validation_too_low(self, client):
        """Limit below 1 should fail validation."""
        response = client.get("/api/v1/pharma/simulation/log?limit=0")
        assert response.status_code == 422

    def test_log_limit_validation_too_high(self, client):
        """Limit above 1000 should fail validation."""
        response = client.get("/api/v1/pharma/simulation/log?limit=1001")
        assert response.status_code == 422

    def test_log_limit_validation_negative(self, client):
        """Negative limit should fail validation."""
        response = client.get("/api/v1/pharma/simulation/log?limit=-1")
        assert response.status_code == 422

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_activity_log", return_value=MOCK_ACTIVITY_LOG)
    def test_log_with_mock_returns_entries(self, mock_log, client):
        data = client.get("/api/v1/pharma/simulation/log").json()
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert data["total_entries"] == 3
        assert data["entries"][0]["role_id"] == "ceo"

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_activity_log", return_value=MOCK_ACTIVITY_LOG[:1])
    def test_log_with_limit_param_passed(self, mock_log, client):
        data = client.get("/api/v1/pharma/simulation/log?limit=5").json()
        assert data["limit"] == 5
        mock_log.assert_called_once_with(limit=5)

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_activity_log", side_effect=RuntimeError("log error"))
    def test_log_exception_returns_500(self, mock_log, client):
        response = client.get("/api/v1/pharma/simulation/log")
        assert response.status_code == 500
        assert "log error" in response.json()["detail"]


# ===========================================================================
# 4. GET /api/v1/pharma/simulation/deliverables/{role_id}
# ===========================================================================

class TestSimulationDeliverables:
    """Tests for the role deliverables endpoint."""

    def test_deliverables_ceo_returns_200(self, client):
        response = client.get("/api/v1/pharma/simulation/deliverables/ceo")
        assert response.status_code == 200

    def test_deliverables_has_request_id(self, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)

    def test_deliverables_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"])

    def test_deliverables_request_id_is_valid_uuid(self, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        uuid.UUID(data["request_id"])

    def test_deliverables_invalid_role_returns_404(self, client):
        """An unknown role_id should return 404, not 200 or 500."""
        response = client.get("/api/v1/pharma/simulation/deliverables/nonexistent_role")
        # When simulation is unavailable, it returns 200 with unavailable status;
        # when available, it should return 404 for bad role IDs.
        # The 404 check only applies when the simulation module is loaded
        # because we validate role_id before calling the simulation.
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "unavailable"
        else:
            assert response.status_code == 404

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    def test_deliverables_invalid_role_returns_404_when_available(self, client):
        """With simulation available, invalid role_id must be 404."""
        response = client.get("/api/v1/pharma/simulation/deliverables/nonexistent_role")
        assert response.status_code == 404
        assert "nonexistent_role" in response.json()["detail"]

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    def test_deliverables_404_lists_valid_roles(self, client):
        """The 404 error detail should include valid role IDs."""
        data = client.get("/api/v1/pharma/simulation/deliverables/badid").json()
        assert "Valid role IDs" in data["detail"]

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_role_deliverables", return_value=MOCK_DELIVERABLES)
    def test_deliverables_with_mock_returns_list(self, mock_del, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        assert "deliverables" in data
        assert isinstance(data["deliverables"], list)
        assert data["total_deliverables"] == 2
        assert data["role_id"] == "ceo"

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_role_deliverables", return_value=MOCK_DELIVERABLES)
    def test_deliverables_item_has_expected_fields(self, mock_del, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        item = data["deliverables"][0]
        assert "deliverable_id" in item
        assert "title" in item
        assert "status" in item

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_role_deliverables", return_value=[])
    def test_deliverables_empty_list_is_valid(self, mock_del, client):
        data = client.get("/api/v1/pharma/simulation/deliverables/ceo").json()
        assert data["deliverables"] == []
        assert data["total_deliverables"] == 0

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_role_deliverables", side_effect=RuntimeError("del error"))
    def test_deliverables_exception_returns_500(self, mock_del, client):
        response = client.get("/api/v1/pharma/simulation/deliverables/ceo")
        assert response.status_code == 500
        assert "del error" in response.json()["detail"]

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_role_deliverables", return_value=MOCK_DELIVERABLES)
    def test_deliverables_all_known_roles_return_200(self, mock_del, client):
        """Every known role_id should return 200 from deliverables endpoint."""
        for role_id in list(ORG_ROLES.keys())[:3]:  # Test a sample for speed
            response = client.get(f"/api/v1/pharma/simulation/deliverables/{role_id}")
            assert response.status_code == 200, (
                f"Role '{role_id}' deliverables returned {response.status_code}"
            )


# ===========================================================================
# 5. GET /api/v1/pharma/simulation/tree
# ===========================================================================

class TestSimulationTree:
    """Tests for the delegation tree endpoint."""

    def test_tree_returns_200(self, client):
        response = client.get("/api/v1/pharma/simulation/tree")
        assert response.status_code == 200

    def test_tree_has_request_id(self, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)

    def test_tree_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"])

    def test_tree_request_id_is_valid_uuid(self, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        uuid.UUID(data["request_id"])

    def test_tree_unavailable_response(self, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        if "status" in data and data["status"] == "unavailable":
            assert "message" in data

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_delegation_tree", return_value=MOCK_DELEGATION_TREE)
    def test_tree_with_mock_returns_structure(self, mock_tree, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert data["root"] == "ceo"
        assert "children" in data
        assert data["total_delegations"] == 7

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_delegation_tree", return_value=MOCK_DELEGATION_TREE)
    def test_tree_children_is_dict(self, mock_tree, client):
        data = client.get("/api/v1/pharma/simulation/tree").json()
        assert isinstance(data["children"], dict)

    @patch("src.api.population_routes._SIMULATION_AVAILABLE", True)
    @patch("src.api.population_routes._get_delegation_tree", side_effect=RuntimeError("tree error"))
    def test_tree_exception_returns_500(self, mock_tree, client):
        response = client.get("/api/v1/pharma/simulation/tree")
        assert response.status_code == 500
        assert "tree error" in response.json()["detail"]


# ===========================================================================
# Cross-cutting: Response structure consistency
# ===========================================================================

class TestSimulationResponseConsistency:
    """Cross-cutting tests that all simulation endpoints share common patterns."""

    ENDPOINTS = [
        "/api/v1/pharma/simulation/run",
        "/api/v1/pharma/simulation/status",
        "/api/v1/pharma/simulation/log",
        "/api/v1/pharma/simulation/deliverables/ceo",
        "/api/v1/pharma/simulation/tree",
    ]

    def test_all_endpoints_return_200(self, client):
        for url in self.ENDPOINTS:
            response = client.get(url)
            assert response.status_code == 200, f"{url} returned {response.status_code}"

    def test_all_endpoints_return_json(self, client):
        for url in self.ENDPOINTS:
            response = client.get(url)
            assert response.headers["content-type"].startswith("application/json"), (
                f"{url} content-type is {response.headers['content-type']}"
            )

    def test_all_endpoints_have_request_id(self, client):
        for url in self.ENDPOINTS:
            data = client.get(url).json()
            assert "request_id" in data, f"{url} missing request_id"

    def test_all_endpoints_have_timestamp(self, client):
        for url in self.ENDPOINTS:
            data = client.get(url).json()
            assert "timestamp" in data, f"{url} missing timestamp"

    def test_all_request_ids_are_unique(self, client):
        """Each request should get a unique request_id."""
        ids = set()
        for url in self.ENDPOINTS:
            data = client.get(url).json()
            ids.add(data["request_id"])
        assert len(ids) == len(self.ENDPOINTS), "request_ids are not unique across endpoints"
