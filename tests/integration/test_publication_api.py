"""
Integration tests for publication analysis API endpoints.

Tests the /api/v1/publication/analysis and /api/v1/publication/figures/{name}
endpoints using FastAPI's TestClient against the real application.
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
# GET /api/v1/publication/analysis
# ===========================================================================

@pytest.mark.integration
class TestPublicationAnalysis:
    """Tests for the publication analysis endpoint."""

    def test_analysis_returns_200(self, client):
        response = client.get("/api/v1/publication/analysis")
        assert response.status_code == 200

    def test_analysis_has_required_fields(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "data_summary" in data
        assert "model_results" in data
        assert "cross_validation" in data
        assert "prior_comparison" in data
        assert "pairwise_comparisons" in data
        assert "heterogeneity" in data
        assert "ae_rates" in data
        assert "demographics" in data
        assert "evidence_accrual_crs" in data
        assert "evidence_accrual_icans" in data
        assert "limitations" in data
        assert "references" in data
        assert "key_findings" in data

    def test_analysis_data_summary_has_four_indications(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        summary = data["data_summary"]
        assert "SLE" in summary
        assert "DLBCL" in summary
        assert "ALL" in summary
        assert "MM" in summary

    def test_analysis_sle_has_47_patients(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert data["data_summary"]["SLE"]["total_patients"] == 47

    def test_analysis_has_seven_model_results(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["model_results"]) == 7

    def test_analysis_model_results_have_required_fields(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        for mr in data["model_results"]:
            assert "model_name" in mr
            assert "estimate_pct" in mr
            assert "ci_low_pct" in mr
            assert "ci_high_pct" in mr
            assert "ci_width_pct" in mr
            assert "method_type" in mr

    def test_analysis_cross_validation_has_entries(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["cross_validation"]) >= 4

    def test_analysis_prior_comparison_has_three_strategies(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["prior_comparison"]) == 3
        strategies = {pc["strategy"] for pc in data["prior_comparison"]}
        assert "uninformative" in strategies
        assert "mechanistic" in strategies
        assert "empirical" in strategies

    def test_analysis_has_pairwise_comparisons(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["pairwise_comparisons"]) > 0
        # Should include SLE vs DLBCL, ALL, MM for multiple AE types
        comparisons = {pc["comparison"] for pc in data["pairwise_comparisons"]}
        assert "SLE_vs_DLBCL" in comparisons

    def test_analysis_heterogeneity_has_entries(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["heterogeneity"]) >= 4
        ae_types = {h["ae_type"] for h in data["heterogeneity"]}
        assert "CRS Any Grade" in ae_types

    def test_analysis_ae_rates_has_four_rows(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["ae_rates"]) == 4
        indications = {r["indication"] for r in data["ae_rates"]}
        assert indications == {"SLE", "DLBCL", "ALL", "MM"}

    def test_analysis_demographics_has_13_rows(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["demographics"]) == 13

    def test_analysis_evidence_accrual_crs_has_timepoints(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        ea = data["evidence_accrual_crs"]
        assert len(ea) >= 4
        # First timepoint should be Mackensen
        assert ea[0]["timepoint"] == "Mackensen et al."
        assert ea[0]["n_cumulative"] == 5

    def test_analysis_evidence_accrual_has_projected_points(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        projected = [p for p in data["evidence_accrual_crs"] if p["is_projected"]]
        assert len(projected) >= 1

    def test_analysis_limitations_non_empty(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["limitations"]) >= 5

    def test_analysis_references_non_empty(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        assert len(data["references"]) >= 20
        # All references should have PMID
        for ref in data["references"]:
            assert "pmid" in ref
            assert "citation" in ref
            assert len(ref["pmid"]) > 0

    def test_analysis_key_findings_present(self, client):
        data = client.get("/api/v1/publication/analysis").json()
        kf = data["key_findings"]
        assert kf["sle_n_patients"] == 47
        assert kf["sle_n_trials"] == 7
        assert kf["total_patients"] == 828


# ===========================================================================
# GET /api/v1/publication/figures/{figure_name}
# ===========================================================================

@pytest.mark.integration
class TestPublicationFigures:
    """Tests for the publication figure data endpoint."""

    def test_forest_crs_any_returns_200(self, client):
        response = client.get("/api/v1/publication/figures/forest_crs_any")
        assert response.status_code == 200

    def test_forest_crs_any_has_four_groups(self, client):
        data = client.get("/api/v1/publication/figures/forest_crs_any").json()
        assert data["figure_name"] == "forest_crs_any"
        assert len(data["data"]) == 4

    def test_forest_crs_any_sle_group_has_pooled(self, client):
        data = client.get("/api/v1/publication/figures/forest_crs_any").json()
        sle = data["data"][0]
        assert sle["indication"] == "SLE"
        pooled = [s for s in sle["studies"] if s["is_pooled"]]
        assert len(pooled) == 1
        assert pooled[0]["name"] == "SLE Pooled"

    def test_forest_crs_g3_returns_200(self, client):
        response = client.get("/api/v1/publication/figures/forest_crs_g3")
        assert response.status_code == 200

    def test_forest_crs_g3_sle_rates_are_zero(self, client):
        data = client.get("/api/v1/publication/figures/forest_crs_g3").json()
        sle = data["data"][0]
        for study in sle["studies"]:
            if not study["is_pooled"]:
                assert study["rate_pct"] == 0.0

    def test_evidence_accrual_returns_200(self, client):
        response = client.get("/api/v1/publication/figures/evidence_accrual")
        assert response.status_code == 200

    def test_evidence_accrual_has_both_ae_types(self, client):
        data = client.get("/api/v1/publication/figures/evidence_accrual").json()
        assert "CRS_grade3plus" in data["data"]
        assert "ICANS_grade3plus" in data["data"]

    def test_prior_comparison_returns_200(self, client):
        response = client.get("/api/v1/publication/figures/prior_comparison")
        assert response.status_code == 200

    def test_prior_comparison_has_three_strategies(self, client):
        data = client.get("/api/v1/publication/figures/prior_comparison").json()
        assert "uninformative" in data["data"]
        assert "mechanistic" in data["data"]
        assert "empirical" in data["data"]

    def test_calibration_returns_200(self, client):
        response = client.get("/api/v1/publication/figures/calibration")
        assert response.status_code == 200

    def test_calibration_has_model_entries(self, client):
        data = client.get("/api/v1/publication/figures/calibration").json()
        assert len(data["data"]) >= 4

    def test_invalid_figure_returns_404(self, client):
        response = client.get("/api/v1/publication/figures/nonexistent")
        assert response.status_code == 404

    def test_figure_response_has_metadata(self, client):
        data = client.get("/api/v1/publication/figures/forest_crs_any").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "figure_name" in data
        assert "figure_title" in data
        assert "data" in data
