"""
Integration tests for pharmaceutical company simulation API endpoints.

Tests all 6 pharma endpoints using FastAPI's TestClient against the real
application (src/api/app.py).
"""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.data.pharma_org import ORG_ROLES, PIPELINE_STAGES, REGULATORY_MAP


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    with TestClient(app) as c:
        yield c


# ===========================================================================
# GET /api/v1/pharma/org
# ===========================================================================

@pytest.mark.integration
class TestPharmaOrg:
    """Tests for the full organizational hierarchy endpoint."""

    def test_org_returns_200(self, client):
        response = client.get("/api/v1/pharma/org")
        assert response.status_code == 200

    def test_org_has_request_id(self, client):
        data = client.get("/api/v1/pharma/org").json()
        assert "request_id" in data
        assert isinstance(data["request_id"], str)
        assert len(data["request_id"]) > 0

    def test_org_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/org").json()
        assert "timestamp" in data

    def test_org_has_roles(self, client):
        data = client.get("/api/v1/pharma/org").json()
        assert "roles" in data
        assert isinstance(data["roles"], dict)

    def test_org_total_roles_matches(self, client):
        data = client.get("/api/v1/pharma/org").json()
        assert data["total_roles"] == len(data["roles"])
        assert data["total_roles"] == len(ORG_ROLES)

    def test_org_contains_ceo(self, client):
        data = client.get("/api/v1/pharma/org").json()
        assert "ceo" in data["roles"]

    def test_org_role_has_required_fields(self, client):
        data = client.get("/api/v1/pharma/org").json()
        ceo = data["roles"]["ceo"]
        required_fields = [
            "role_id", "title", "reports_to", "responsibilities",
            "regulatory_frameworks", "skills", "status", "current_task",
        ]
        for field in required_fields:
            assert field in ceo, f"CEO role missing field '{field}'"


# ===========================================================================
# GET /api/v1/pharma/pipeline
# ===========================================================================

@pytest.mark.integration
class TestPharmaPipeline:
    """Tests for the clinical pipeline endpoint."""

    def test_pipeline_returns_200(self, client):
        response = client.get("/api/v1/pharma/pipeline")
        assert response.status_code == 200

    def test_pipeline_has_request_id(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert "request_id" in data

    def test_pipeline_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert "timestamp" in data

    def test_pipeline_has_stages(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert "stages" in data
        assert isinstance(data["stages"], list)

    def test_pipeline_total_stages_matches(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert data["total_stages"] == len(data["stages"])
        assert data["total_stages"] == len(PIPELINE_STAGES)

    def test_pipeline_has_status_summary(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert "status_summary" in data
        assert isinstance(data["status_summary"], dict)

    def test_pipeline_first_stage_is_preclinical(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert data["stages"][0]["id"] == "preclinical"

    def test_pipeline_last_stage_is_approval(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        assert data["stages"][-1]["id"] == "approval"

    def test_pipeline_stage_has_required_fields(self, client):
        data = client.get("/api/v1/pharma/pipeline").json()
        stage = data["stages"][0]
        required = ["id", "name", "owner", "status", "regulations"]
        for field in required:
            assert field in stage, f"Stage missing field '{field}'"


# ===========================================================================
# GET /api/v1/pharma/regulatory-map
# ===========================================================================

@pytest.mark.integration
class TestPharmaRegulatoryMap:
    """Tests for the regulatory framework mapping endpoint."""

    def test_regulatory_map_returns_200(self, client):
        response = client.get("/api/v1/pharma/regulatory-map")
        assert response.status_code == 200

    def test_regulatory_map_has_request_id(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert "request_id" in data

    def test_regulatory_map_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert "timestamp" in data

    def test_regulatory_map_has_frameworks(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert "frameworks" in data
        assert isinstance(data["frameworks"], dict)

    def test_regulatory_map_total_matches(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert data["total_frameworks"] == len(data["frameworks"])
        assert data["total_frameworks"] == len(REGULATORY_MAP)

    def test_regulatory_map_has_categories(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert "categories" in data
        assert isinstance(data["categories"], dict)

    def test_regulatory_map_framework_has_required_fields(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        framework = data["frameworks"]["ICH_E6_R3"]
        required = ["title", "category", "url", "description"]
        for field in required:
            assert field in framework, f"Framework missing field '{field}'"

    def test_regulatory_map_has_at_least_30_frameworks(self, client):
        data = client.get("/api/v1/pharma/regulatory-map").json()
        assert data["total_frameworks"] >= 30


# ===========================================================================
# GET /api/v1/pharma/quality-metrics
# ===========================================================================

@pytest.mark.integration
class TestPharmaQualityMetrics:
    """Tests for the quality metrics endpoint."""

    def test_quality_metrics_returns_200(self, client):
        response = client.get("/api/v1/pharma/quality-metrics")
        assert response.status_code == 200

    def test_quality_metrics_has_request_id(self, client):
        data = client.get("/api/v1/pharma/quality-metrics").json()
        assert "request_id" in data

    def test_quality_metrics_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/quality-metrics").json()
        assert "timestamp" in data

    def test_quality_metrics_has_metrics(self, client):
        data = client.get("/api/v1/pharma/quality-metrics").json()
        assert "metrics" in data
        assert isinstance(data["metrics"], dict)

    def test_quality_metrics_has_all_sections(self, client):
        data = client.get("/api/v1/pharma/quality-metrics").json()
        metrics = data["metrics"]
        required = {"deviations", "capa", "audits", "training", "batches"}
        assert set(metrics.keys()) == required

    def test_quality_metrics_training_compliance_in_range(self, client):
        data = client.get("/api/v1/pharma/quality-metrics").json()
        pct = data["metrics"]["training"]["compliance_pct"]
        assert 0 <= pct <= 100


# ===========================================================================
# GET /api/v1/pharma/role/{role_id}
# ===========================================================================

@pytest.mark.integration
class TestPharmaRoleDetail:
    """Tests for the single role detail endpoint."""

    def test_role_ceo_returns_200(self, client):
        response = client.get("/api/v1/pharma/role/ceo")
        assert response.status_code == 200

    def test_role_ceo_has_request_id(self, client):
        data = client.get("/api/v1/pharma/role/ceo").json()
        assert "request_id" in data

    def test_role_ceo_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/role/ceo").json()
        assert "timestamp" in data

    def test_role_ceo_has_role_data(self, client):
        data = client.get("/api/v1/pharma/role/ceo").json()
        assert "role" in data
        assert data["role"]["role_id"] == "ceo"
        assert data["role"]["title"] == "Chief Executive Officer"

    def test_role_vp_clinops_returns_200(self, client):
        response = client.get("/api/v1/pharma/role/vp_clinops")
        assert response.status_code == 200

    def test_role_invalid_returns_404(self, client):
        response = client.get("/api/v1/pharma/role/nonexistent_role")
        assert response.status_code == 404

    def test_role_invalid_error_message(self, client):
        data = client.get("/api/v1/pharma/role/nonexistent_role").json()
        assert "detail" in data
        assert "nonexistent_role" in data["detail"]

    def test_all_roles_accessible(self, client):
        """Every role ID from ORG_ROLES should be accessible via the endpoint."""
        for role_id in ORG_ROLES:
            response = client.get(f"/api/v1/pharma/role/{role_id}")
            assert response.status_code == 200, (
                f"Role '{role_id}' returned status {response.status_code}"
            )


# ===========================================================================
# GET /api/v1/pharma/role/{role_id}/skills
# ===========================================================================

@pytest.mark.integration
class TestPharmaRoleSkills:
    """Tests for the role skills endpoint."""

    def test_skills_ceo_returns_200(self, client):
        response = client.get("/api/v1/pharma/role/ceo/skills")
        assert response.status_code == 200

    def test_skills_ceo_has_request_id(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        assert "request_id" in data

    def test_skills_ceo_has_timestamp(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        assert "timestamp" in data

    def test_skills_ceo_has_role_id(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        assert data["role_id"] == "ceo"

    def test_skills_ceo_has_skills_list(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    def test_skills_ceo_total_matches(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        assert data["total_skills"] == len(data["skills"])

    def test_skills_have_required_fields(self, client):
        data = client.get("/api/v1/pharma/role/ceo/skills").json()
        for skill in data["skills"]:
            assert "skill_id" in skill
            assert "name" in skill
            assert "category" in skill
            assert "description" in skill

    def test_skills_invalid_role_returns_404(self, client):
        response = client.get("/api/v1/pharma/role/nonexistent/skills")
        assert response.status_code == 404

    def test_skills_head_pv_has_pharmacovigilance(self, client):
        """Head of PV should have pharmacovigilance as a skill."""
        data = client.get("/api/v1/pharma/role/head_pv/skills").json()
        skill_ids = [s["skill_id"] for s in data["skills"]]
        assert "pharmacovigilance" in skill_ids

    def test_all_roles_skills_accessible(self, client):
        """Every role's skills endpoint should be accessible."""
        for role_id in ORG_ROLES:
            response = client.get(f"/api/v1/pharma/role/{role_id}/skills")
            assert response.status_code == 200, (
                f"Role '{role_id}' skills returned status {response.status_code}"
            )
            data = response.json()
            assert data["total_skills"] >= 1, (
                f"Role '{role_id}' has 0 skills from endpoint"
            )
