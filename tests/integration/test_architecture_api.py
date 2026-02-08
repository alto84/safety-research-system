"""
Integration tests for the system architecture API endpoint.

Tests the GET /api/v1/system/architecture endpoint that returns
structured metadata about the platform's modules, dependencies,
endpoints, model registry, test summary, and system health.
"""

import pytest

from fastapi.testclient import TestClient

from src.api.app import app


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance.

    Uses raise_server_exceptions=False to avoid lifespan interference
    with other integration test modules that share the same app singleton.
    """
    c = TestClient(app, raise_server_exceptions=False)
    yield c


# ===========================================================================
# GET /api/v1/system/architecture
# ===========================================================================

@pytest.mark.integration
class TestSystemArchitecture:
    """Tests for the system architecture metadata endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/system/architecture")
        assert response.status_code == 200

    def test_has_required_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "modules" in data
        assert "dependencies" in data
        assert "endpoints" in data
        assert "registry_models" in data
        assert "test_summary" in data
        assert "system_health" in data

    def test_modules_is_list(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert isinstance(data["modules"], list)
        assert len(data["modules"]) > 0

    def test_modules_have_required_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        for module in data["modules"]:
            assert "name" in module
            assert "path" in module
            assert "description" in module
            assert "public_functions" in module
            assert "classes" in module
            assert "lines_of_code" in module

    def test_modules_contain_key_modules(self, client):
        data = client.get("/api/v1/system/architecture").json()
        names = [m["name"] for m in data["modules"]]
        assert "bayesian_risk" in names
        assert "biomarker_scores" in names
        assert "ensemble_runner" in names
        assert "model_registry" in names
        assert "app" in names
        assert "population_routes" in names

    def test_dependencies_is_list(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert isinstance(data["dependencies"], list)
        assert len(data["dependencies"]) > 0

    def test_dependencies_have_source_and_target(self, client):
        data = client.get("/api/v1/system/architecture").json()
        for dep in data["dependencies"]:
            assert "source" in dep
            assert "target" in dep
            assert "import_names" in dep
            assert isinstance(dep["import_names"], list)

    def test_dependency_graph_has_expected_edges(self, client):
        data = client.get("/api/v1/system/architecture").json()
        edges = [(d["source"], d["target"]) for d in data["dependencies"]]
        assert ("app", "ensemble_runner") in edges
        assert ("app", "schemas") in edges
        assert ("population_routes", "bayesian_risk") in edges

    def test_endpoints_is_list(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert isinstance(data["endpoints"], list)
        assert len(data["endpoints"]) > 10

    def test_endpoints_have_required_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        for ep in data["endpoints"]:
            assert "method" in ep
            assert "path" in ep
            assert "summary" in ep

    def test_endpoints_contain_key_endpoints(self, client):
        data = client.get("/api/v1/system/architecture").json()
        paths = [ep["path"] for ep in data["endpoints"]]
        assert "/api/v1/predict" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/population/risk" in paths
        assert "/api/v1/system/architecture" in paths

    def test_endpoints_have_methods(self, client):
        data = client.get("/api/v1/system/architecture").json()
        methods = set(ep["method"] for ep in data["endpoints"])
        assert "GET" in methods
        assert "POST" in methods

    def test_registry_models_is_list(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert isinstance(data["registry_models"], list)
        assert len(data["registry_models"]) == 7

    def test_registry_models_have_required_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        for model in data["registry_models"]:
            assert "id" in model
            assert "name" in model
            assert "description" in model
            assert "suitable_for" in model
            assert "requires" in model

    def test_registry_models_contain_expected_models(self, client):
        data = client.get("/api/v1/system/architecture").json()
        model_ids = [m["id"] for m in data["registry_models"]]
        assert "bayesian_beta_binomial" in model_ids
        assert "frequentist_exact" in model_ids
        assert "wilson_score" in model_ids
        assert "kaplan_meier" in model_ids

    def test_test_summary_has_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        ts = data["test_summary"]
        assert "total_tests" in ts
        assert "test_files" in ts
        assert "unit_tests" in ts
        assert "integration_tests" in ts
        assert ts["total_tests"] > 0

    def test_system_health_has_fields(self, client):
        data = client.get("/api/v1/system/architecture").json()
        sh = data["system_health"]
        assert "models_loaded" in sh
        assert "api_version" in sh
        assert "total_endpoints" in sh
        assert "total_modules" in sh
        assert sh["models_loaded"] == 7
        assert sh["api_version"] == "0.1.0"

    def test_system_health_endpoints_matches(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert data["system_health"]["total_endpoints"] == len(data["endpoints"])

    def test_system_health_modules_matches(self, client):
        data = client.get("/api/v1/system/architecture").json()
        assert data["system_health"]["total_modules"] == len(data["modules"])

    def test_response_has_request_id_format(self, client):
        data = client.get("/api/v1/system/architecture").json()
        request_id = data["request_id"]
        assert len(request_id) == 36  # UUID format
        assert request_id.count("-") == 4
