"""
Integration tests for narrative generation API endpoints.

Tests the POST /api/v1/narratives/generate and
GET /api/v1/narratives/patient/{patient_id}/briefing endpoints using
FastAPI's TestClient against the real application.
"""

import pytest

from fastapi.testclient import TestClient

from src.api.app import app


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    with TestClient(app) as c:
        yield c


# ===========================================================================
# POST /api/v1/narratives/generate
# ===========================================================================

@pytest.mark.integration
class TestNarrativeGenerate:
    """Tests for the narrative generation endpoint."""

    def test_generate_returns_200(self, client):
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-001",
        })
        assert response.status_code == 200

    def test_generate_has_required_fields(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-001",
        }).json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "patient_id" in data
        assert "executive_summary" in data
        assert "risk_narrative" in data
        assert "mechanistic_context" in data
        assert "recommended_monitoring" in data
        assert "references" in data

    def test_generate_patient_id_matches(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "PAT-ABC-123",
        }).json()
        assert data["patient_id"] == "PAT-ABC-123"

    def test_generate_with_risk_scores(self, client):
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-002",
            "risk_scores": {
                "composite_score": 0.72,
                "risk_level": "high",
                "data_completeness": 0.85,
                "models_run": 5,
                "individual_scores": [
                    {"model_name": "EASIX", "score": 12.5, "risk_level": "high"},
                    {"model_name": "HScore", "score": 145.0, "risk_level": "moderate"},
                ],
                "contributing_factors": ["Elevated CRP", "Low platelets"],
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert "high" in data["executive_summary"].lower() or "0.72" in data["executive_summary"]

    def test_generate_with_lab_values(self, client):
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-003",
            "lab_values": {
                "crp": 85.0,
                "ferritin": 2200.0,
                "ldh": 620.0,
                "platelets": 45.0,
            },
        })
        assert response.status_code == 200
        data = response.json()
        # Should mention elevated labs
        assert "CRP" in data["executive_summary"] or "ferritin" in data["executive_summary"]

    def test_generate_includes_mechanism_context(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-004",
            "therapy_type": "CAR-T (CD19)",
            "include_mechanisms": True,
        }).json()
        assert len(data["mechanistic_context"]) > 0
        # Should include CRS mechanism details for CAR-T CD19
        assert "CRS" in data["mechanistic_context"] or "cytokine" in data["mechanistic_context"].lower()

    def test_generate_excludes_mechanisms_when_disabled(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-005",
            "include_mechanisms": False,
        }).json()
        assert data["mechanistic_context"] == ""

    def test_generate_excludes_monitoring_when_disabled(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-006",
            "include_monitoring": False,
        }).json()
        assert data["recommended_monitoring"] == ""

    def test_generate_includes_monitoring(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-007",
            "include_monitoring": True,
        }).json()
        assert len(data["recommended_monitoring"]) > 0
        assert "monitoring" in data["recommended_monitoring"].lower()

    def test_generate_has_references(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-008",
            "therapy_type": "CAR-T (CD19)",
        }).json()
        assert isinstance(data["references"], list)
        # Should have PubMed references from the knowledge graph
        assert len(data["references"]) > 0
        # References should be PMID format
        pmid_refs = [r for r in data["references"] if r.startswith("PMID:")]
        assert len(pmid_refs) > 0

    def test_generate_generation_method(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-009",
        }).json()
        assert data["generation_method"] == "template_rules_v1"

    def test_generate_disclaimer_present(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-010",
        }).json()
        assert "disclaimer" in data
        assert "clinical judgment" in data["disclaimer"].lower()

    def test_generate_with_custom_ae_types(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-011",
            "ae_types": ["CRS"],
        }).json()
        assert response_ok(data)

    def test_generate_rejects_empty_patient_id(self, client):
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "",
        })
        assert response.status_code == 422

    def test_generate_sections_present(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-012",
        }).json()
        assert "sections" in data
        assert isinstance(data["sections"], list)

    def test_generate_high_risk_monitoring_is_intensified(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-013",
            "risk_scores": {
                "composite_score": 0.85,
                "risk_level": "high",
                "data_completeness": 0.9,
                "models_run": 5,
            },
        }).json()
        monitoring = data["recommended_monitoring"]
        assert "intensified" in monitoring.lower() or "continuous" in monitoring.lower()

    def test_generate_low_risk_monitoring_is_standard(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-014",
            "risk_scores": {
                "composite_score": 0.15,
                "risk_level": "low",
                "data_completeness": 0.9,
                "models_run": 5,
            },
        }).json()
        monitoring = data["recommended_monitoring"]
        assert "standard" in monitoring.lower()

    def test_generate_with_unknown_therapy_type(self, client):
        """Should still work for unknown therapy types, just with less mechanism data."""
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-015",
            "therapy_type": "Unknown Therapy",
        })
        assert response.status_code == 200

    def test_generate_risk_narrative_interprets_scores(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-016",
            "risk_scores": {
                "composite_score": 0.55,
                "risk_level": "moderate",
                "data_completeness": 0.75,
                "models_run": 4,
                "individual_scores": [
                    {"model_name": "EASIX", "score": 8.5, "risk_level": "moderate", "citation": "Pennisi 2021"},
                ],
            },
        }).json()
        assert "0.55" in data["risk_narrative"] or "moderate" in data["risk_narrative"].lower()

    def test_generate_mechanism_mentions_intervention_points(self, client):
        data = client.post("/api/v1/narratives/generate", json={
            "patient_id": "TEST-017",
            "therapy_type": "CAR-T (CD19)",
            "ae_types": ["CRS"],
        }).json()
        mech = data["mechanistic_context"]
        # CAR-T CD19 CRS mechanism has known intervention points
        assert "intervention" in mech.lower() or "tocilizumab" in mech.lower()

    def test_generate_with_all_options(self, client):
        """Test with all fields populated."""
        response = client.post("/api/v1/narratives/generate", json={
            "patient_id": "FULL-TEST-001",
            "therapy_type": "CAR-T (CD19)",
            "ae_types": ["CRS", "ICANS"],
            "include_mechanisms": True,
            "include_monitoring": True,
            "risk_scores": {
                "composite_score": 0.65,
                "risk_level": "high",
                "data_completeness": 0.80,
                "models_run": 5,
                "individual_scores": [
                    {"model_name": "EASIX", "score": 15.0, "risk_level": "high"},
                    {"model_name": "HScore", "score": 200.0, "risk_level": "high"},
                    {"model_name": "CAR_HEMATOTOX", "score": 3.0, "risk_level": "high"},
                ],
                "contributing_factors": ["Elevated CRP", "Thrombocytopenia"],
            },
            "lab_values": {
                "crp": 85.0,
                "ferritin": 2200.0,
                "ldh": 620.0,
                "platelets": 45.0,
                "creatinine": 1.8,
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["executive_summary"]) > 50
        assert len(data["risk_narrative"]) > 50
        assert len(data["mechanistic_context"]) > 50
        assert len(data["recommended_monitoring"]) > 50


# ===========================================================================
# GET /api/v1/narratives/patient/{patient_id}/briefing
# ===========================================================================

@pytest.mark.integration
class TestClinicalBriefing:
    """Tests for the clinical briefing endpoint."""

    def test_briefing_returns_200(self, client):
        response = client.get("/api/v1/narratives/patient/TEST-001/briefing")
        assert response.status_code == 200

    def test_briefing_has_required_fields(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-001/briefing").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "patient_id" in data
        assert "therapy_type" in data
        assert "briefing_title" in data
        assert "risk_level" in data
        assert "sections" in data
        assert "intervention_points" in data
        assert "timing_expectations" in data
        assert "key_references" in data

    def test_briefing_patient_id_matches(self, client):
        data = client.get("/api/v1/narratives/patient/PAT-XYZ/briefing").json()
        assert data["patient_id"] == "PAT-XYZ"

    def test_briefing_default_therapy_type(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-002/briefing").json()
        assert data["therapy_type"] == "CAR-T (CD19)"

    def test_briefing_custom_therapy_type(self, client):
        data = client.get(
            "/api/v1/narratives/patient/TEST-003/briefing?therapy_type=TCR-T"
        ).json()
        assert data["therapy_type"] == "TCR-T"

    def test_briefing_has_sections(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-004/briefing").json()
        sections = data["sections"]
        assert isinstance(sections, list)
        assert len(sections) >= 3  # At least risk, population, mechanisms

    def test_briefing_sections_have_headings(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-005/briefing").json()
        for section in data["sections"]:
            assert "heading" in section
            assert "body" in section
            assert len(section["heading"]) > 0
            assert len(section["body"]) > 0

    def test_briefing_has_intervention_points(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-006/briefing").json()
        interventions = data["intervention_points"]
        assert isinstance(interventions, list)
        # CAR-T CD19 has known intervention points
        assert len(interventions) > 0

    def test_briefing_intervention_points_structure(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-007/briefing").json()
        for ip in data["intervention_points"]:
            assert "ae_type" in ip
            assert "pathway_step" in ip
            assert "agents" in ip
            assert "temporal_window" in ip

    def test_briefing_has_timing_expectations(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-008/briefing").json()
        timing = data["timing_expectations"]
        assert isinstance(timing, dict)
        # CAR-T CD19 should have CRS timing
        assert len(timing) > 0

    def test_briefing_has_key_references(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-009/briefing").json()
        refs = data["key_references"]
        assert isinstance(refs, list)
        assert len(refs) > 0
        # Should have PMID references
        pmid_refs = [r for r in refs if r.startswith("PMID:")]
        assert len(pmid_refs) > 0

    def test_briefing_generation_method(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-010/briefing").json()
        assert data["generation_method"] == "template_rules_v1"

    def test_briefing_disclaimer_present(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-011/briefing").json()
        assert "disclaimer" in data
        assert "clinical judgment" in data["disclaimer"].lower()

    def test_briefing_title_contains_patient_id(self, client):
        data = client.get("/api/v1/narratives/patient/BRIEF-001/briefing").json()
        assert "BRIEF-001" in data["briefing_title"]

    def test_briefing_includes_monitoring_section(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-012/briefing").json()
        headings = [s["heading"] for s in data["sections"]]
        assert any("monitor" in h.lower() for h in headings)

    def test_briefing_includes_risk_assessment_section(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-013/briefing").json()
        headings = [s["heading"] for s in data["sections"]]
        assert any("risk" in h.lower() for h in headings)

    def test_briefing_includes_mechanistic_section(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-014/briefing").json()
        headings = [s["heading"] for s in data["sections"]]
        assert any("mechan" in h.lower() or "biolog" in h.lower() for h in headings)

    def test_briefing_includes_population_context(self, client):
        data = client.get("/api/v1/narratives/patient/TEST-015/briefing").json()
        headings = [s["heading"] for s in data["sections"]]
        assert any("population" in h.lower() for h in headings)


# ===========================================================================
# Helper
# ===========================================================================

def response_ok(data: dict) -> bool:
    """Check that a narrative response has the basic expected structure."""
    return (
        "request_id" in data
        and "patient_id" in data
        and "executive_summary" in data
    )
