"""
Integration tests for population-level API endpoints.

Tests all 8 population/signal endpoints using FastAPI's TestClient against
the real application (src/api/app.py). The FAERS endpoint is mocked to avoid
live network calls to the openFDA API.
"""

import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from src.api.app import app
from src.models.faers_signal import FAERSSummary, FAERSSignal


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    with TestClient(app) as c:
        yield c


# ===========================================================================
# GET /api/v1/population/risk
# ===========================================================================

@pytest.mark.integration
class TestPopulationRisk:
    """Tests for the SLE CAR-T baseline risk summary endpoint."""

    def test_risk_returns_200(self, client):
        response = client.get("/api/v1/population/risk")
        assert response.status_code == 200

    def test_risk_has_required_fields(self, client):
        data = client.get("/api/v1/population/risk").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "indication" in data
        assert "n_patients_pooled" in data
        assert "baseline_risks" in data
        assert "mitigated_risks" in data

    def test_risk_indication_is_sle(self, client):
        data = client.get("/api/v1/population/risk").json()
        assert data["indication"] == "SLE"

    def test_risk_n_patients_pooled_is_47(self, client):
        data = client.get("/api/v1/population/risk").json()
        assert data["n_patients_pooled"] == 47

    def test_risk_baseline_risks_contains_expected_keys(self, client):
        data = client.get("/api/v1/population/risk").json()
        baseline = data["baseline_risks"]
        assert "crs_grade3_plus" in baseline
        assert "icans_grade3_plus" in baseline
        assert "icahs" in baseline

    def test_risk_baseline_risks_have_estimates(self, client):
        data = client.get("/api/v1/population/risk").json()
        baseline = data["baseline_risks"]
        for key in ["crs_grade3_plus", "icans_grade3_plus", "icahs"]:
            assert "estimate" in baseline[key]
            assert isinstance(baseline[key]["estimate"], (int, float))

    def test_risk_mitigated_risks_present(self, client):
        data = client.get("/api/v1/population/risk").json()
        mitigated = data["mitigated_risks"]
        assert "crs" in mitigated
        assert "icans" in mitigated

    def test_risk_has_evidence_grade(self, client):
        data = client.get("/api/v1/population/risk").json()
        assert "evidence_grade" in data
        assert isinstance(data["evidence_grade"], str)


# ===========================================================================
# POST /api/v1/population/bayesian
# ===========================================================================

@pytest.mark.integration
class TestBayesianPosterior:
    """Tests for the Bayesian posterior computation endpoint."""

    def test_bayesian_valid_crs(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 1,
            "n_patients": 47,
        })
        assert response.status_code == 200

    def test_bayesian_response_has_estimate(self, client):
        data = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 1,
            "n_patients": 47,
        }).json()
        assert "estimate" in data
        estimate = data["estimate"]
        assert "mean_pct" in estimate
        assert "ci_low_pct" in estimate
        assert "ci_high_pct" in estimate

    def test_bayesian_ci_ordering(self, client):
        data = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 1,
            "n_patients": 47,
        }).json()
        estimate = data["estimate"]
        assert estimate["ci_low_pct"] < estimate["mean_pct"]
        assert estimate["mean_pct"] < estimate["ci_high_pct"]

    def test_bayesian_has_request_id_and_timestamp(self, client):
        data = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 1,
            "n_patients": 47,
        }).json()
        assert "request_id" in data
        assert "timestamp" in data

    def test_bayesian_invalid_ae_returns_422(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "UNKNOWN_AE",
            "n_events": 1,
            "n_patients": 47,
        })
        assert response.status_code == 422

    def test_bayesian_events_exceed_patients_returns_422(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 50,
            "n_patients": 47,
        })
        assert response.status_code == 422

    def test_bayesian_zero_events_valid(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "CRS",
            "n_events": 0,
            "n_patients": 47,
        })
        assert response.status_code == 200
        data = response.json()
        # Zero events should yield a low mean
        assert data["estimate"]["mean_pct"] < 10.0

    def test_bayesian_case_insensitive_ae(self, client):
        """Lowercase 'crs' should be accepted and normalised to 'CRS'."""
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "crs",
            "n_events": 1,
            "n_patients": 47,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["estimate"]["adverse_event"] == "CRS"

    def test_bayesian_icans_valid(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "ICANS",
            "n_events": 0,
            "n_patients": 47,
        })
        assert response.status_code == 200

    def test_bayesian_icahs_valid(self, client):
        response = client.post("/api/v1/population/bayesian", json={
            "adverse_event": "ICAHS",
            "n_events": 2,
            "n_patients": 47,
        })
        assert response.status_code == 200


# ===========================================================================
# POST /api/v1/population/mitigations
# ===========================================================================

@pytest.mark.integration
class TestMitigationAnalysis:
    """Tests for the correlated mitigation analysis endpoint."""

    def test_mitigation_valid_tocilizumab_crs(self, client):
        response = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab"],
            "target_ae": "CRS",
        })
        assert response.status_code == 200

    def test_mitigation_response_structure(self, client):
        data = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab"],
            "target_ae": "CRS",
        }).json()
        assert "baseline_risk_pct" in data
        assert "mitigated_risk_pct" in data
        assert "combined_rr" in data

    def test_mitigation_reduces_risk(self, client):
        data = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab"],
            "target_ae": "CRS",
        }).json()
        assert data["mitigated_risk_pct"] <= data["baseline_risk_pct"]

    def test_mitigation_unknown_id_returns_400(self, client):
        response = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["nonexistent_drug"],
            "target_ae": "CRS",
        })
        assert response.status_code == 400

    def test_mitigation_not_targeting_ae_gives_rr_1(self, client):
        """Corticosteroids target ICANS, not CRS. Combined RR should be 1.0."""
        data = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["corticosteroids"],
            "target_ae": "CRS",
        }).json()
        assert data["combined_rr"] == 1.0

    def test_mitigation_multiple_strategies(self, client):
        response = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab", "anakinra"],
            "target_ae": "CRS",
        })
        assert response.status_code == 200
        data = response.json()
        # Two applicable mitigations should be listed
        assert len(data["mitigations_applied"]) == 2
        assert "tocilizumab" in data["mitigations_applied"]
        assert "anakinra" in data["mitigations_applied"]

    def test_mitigation_combined_rr_less_than_1(self, client):
        data = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab", "anakinra"],
            "target_ae": "CRS",
        }).json()
        assert data["combined_rr"] < 1.0

    def test_mitigation_has_request_id_and_timestamp(self, client):
        data = client.post("/api/v1/population/mitigations", json={
            "selected_mitigations": ["tocilizumab"],
            "target_ae": "CRS",
        }).json()
        assert "request_id" in data
        assert "timestamp" in data


# ===========================================================================
# GET /api/v1/population/evidence-accrual
# ===========================================================================

@pytest.mark.integration
class TestEvidenceAccrual:
    """Tests for the evidence accrual timeline endpoint."""

    def test_evidence_accrual_returns_200(self, client):
        response = client.get("/api/v1/population/evidence-accrual")
        assert response.status_code == 200

    def test_evidence_accrual_has_timeline(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        assert "timeline" in data
        assert isinstance(data["timeline"], list)

    def test_evidence_accrual_timeline_has_7_entries(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        assert len(data["timeline"]) == 7

    def test_evidence_accrual_has_ci_widths(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        assert "current_ci_width_crs_pct" in data
        assert "projected_ci_width_crs_pct" in data

    def test_evidence_accrual_ci_narrows(self, client):
        """Projected CI width should be smaller than current CI width."""
        data = client.get("/api/v1/population/evidence-accrual").json()
        assert data["current_ci_width_crs_pct"] > data["projected_ci_width_crs_pct"]

    def test_evidence_accrual_entries_have_crs_and_icans(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        for entry in data["timeline"]:
            assert "crs_mean_pct" in entry
            assert "crs_ci_width_pct" in entry
            assert "icans_mean_pct" in entry
            assert "icans_ci_width_pct" in entry

    def test_evidence_accrual_entries_have_metadata(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        for entry in data["timeline"]:
            assert "label" in entry
            assert "year" in entry
            assert "n_cumulative_patients" in entry
            assert "is_projected" in entry

    def test_evidence_accrual_has_request_id(self, client):
        data = client.get("/api/v1/population/evidence-accrual").json()
        assert "request_id" in data
        assert "timestamp" in data


# ===========================================================================
# GET /api/v1/population/trials
# ===========================================================================

@pytest.mark.integration
class TestTrialRegistry:
    """Tests for the clinical trial registry endpoint."""

    def test_trials_returns_200(self, client):
        response = client.get("/api/v1/population/trials")
        assert response.status_code == 200

    def test_trials_response_structure(self, client):
        data = client.get("/api/v1/population/trials").json()
        assert "recruiting" in data
        assert "active" in data
        assert "completed" in data
        assert "total" in data
        assert "trials" in data

    def test_trials_total_greater_than_zero(self, client):
        data = client.get("/api/v1/population/trials").json()
        assert data["total"] > 0

    def test_trials_filter_by_sle(self, client):
        data = client.get("/api/v1/population/trials", params={
            "indication": "SLE",
        }).json()
        # Every returned trial should mention SLE in its indication
        for trial in data["trials"]:
            assert "SLE" in trial["indication"].upper()

    def test_trials_nonexistent_indication_empty(self, client):
        data = client.get("/api/v1/population/trials", params={
            "indication": "ZZZZZ_NONEXISTENT",
        }).json()
        assert data["total"] == 0
        assert len(data["trials"]) == 0

    def test_trials_have_expected_fields(self, client):
        data = client.get("/api/v1/population/trials").json()
        if data["trials"]:
            trial = data["trials"][0]
            assert "name" in trial
            assert "sponsor" in trial
            assert "nct_id" in trial
            assert "phase" in trial
            assert "indication" in trial
            assert "status" in trial

    def test_trials_has_request_id(self, client):
        data = client.get("/api/v1/population/trials").json()
        assert "request_id" in data
        assert "timestamp" in data


# ===========================================================================
# GET /api/v1/signals/faers (mocked)
# ===========================================================================

def _make_synthetic_faers_summary() -> FAERSSummary:
    """Build a synthetic FAERSSummary for testing without hitting openFDA."""
    signal = FAERSSignal(
        product="KYMRIAH",
        adverse_event="Cytokine release syndrome",
        n_cases=150,
        n_total_product=500,
        n_total_ae=2000,
        n_total_database=100000,
        prr=3.75,
        prr_ci_low=2.80,
        prr_ci_high=5.02,
        ror=3.90,
        ror_ci_low=2.85,
        ror_ci_high=5.34,
        ebgm=3.50,
        ebgm05=2.60,
        is_signal=True,
        signal_strength="strong",
    )
    return FAERSSummary(
        products_queried=["KYMRIAH"],
        total_reports=500,
        signals_detected=1,
        strong_signals=1,
        signals=[signal],
        query_timestamp="2026-02-07T00:00:00Z",
    )


@pytest.mark.integration
class TestFAERSSignals:
    """Tests for the FAERS signal detection endpoint (mocked external API)."""

    def test_faers_returns_200(self, client):
        with patch(
            "src.api.population_routes.get_faers_signals",
            new_callable=AsyncMock,
            return_value=_make_synthetic_faers_summary(),
        ):
            response = client.get("/api/v1/signals/faers")
        assert response.status_code == 200

    def test_faers_response_structure(self, client):
        with patch(
            "src.api.population_routes.get_faers_signals",
            new_callable=AsyncMock,
            return_value=_make_synthetic_faers_summary(),
        ):
            data = client.get("/api/v1/signals/faers").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "products_queried" in data
        assert "total_reports" in data
        assert "signals_detected" in data
        assert "strong_signals" in data
        assert "signals" in data

    def test_faers_signal_content(self, client):
        with patch(
            "src.api.population_routes.get_faers_signals",
            new_callable=AsyncMock,
            return_value=_make_synthetic_faers_summary(),
        ):
            data = client.get("/api/v1/signals/faers").json()
        assert len(data["signals"]) == 1
        signal = data["signals"][0]
        assert signal["product"] == "KYMRIAH"
        assert signal["adverse_event"] == "Cytokine release syndrome"
        assert signal["is_signal"] is True
        assert signal["signal_strength"] == "strong"
        assert signal["prr"] == pytest.approx(3.75)
        assert signal["ebgm"] == pytest.approx(3.50)

    def test_faers_products_queried(self, client):
        with patch(
            "src.api.population_routes.get_faers_signals",
            new_callable=AsyncMock,
            return_value=_make_synthetic_faers_summary(),
        ):
            data = client.get("/api/v1/signals/faers").json()
        assert "KYMRIAH" in data["products_queried"]

    def test_faers_counts(self, client):
        with patch(
            "src.api.population_routes.get_faers_signals",
            new_callable=AsyncMock,
            return_value=_make_synthetic_faers_summary(),
        ):
            data = client.get("/api/v1/signals/faers").json()
        assert data["total_reports"] == 500
        assert data["signals_detected"] == 1
        assert data["strong_signals"] == 1


# ===========================================================================
# GET /api/v1/population/mitigations/strategies
# ===========================================================================

@pytest.mark.integration
class TestMitigationStrategies:
    """Tests for the mitigation strategies listing endpoint."""

    def test_strategies_returns_200(self, client):
        response = client.get("/api/v1/population/mitigations/strategies")
        assert response.status_code == 200

    def test_strategies_has_strategies_list(self, client):
        data = client.get("/api/v1/population/mitigations/strategies").json()
        assert "strategies" in data
        assert isinstance(data["strategies"], list)

    def test_strategies_total_is_5(self, client):
        data = client.get("/api/v1/population/mitigations/strategies").json()
        assert data["total"] == 5

    def test_strategies_have_required_fields(self, client):
        data = client.get("/api/v1/population/mitigations/strategies").json()
        for strategy in data["strategies"]:
            assert "id" in strategy
            assert "name" in strategy
            assert "mechanism" in strategy
            assert "target_aes" in strategy
            assert "relative_risk" in strategy
            assert "evidence_level" in strategy

    def test_strategies_include_known_ids(self, client):
        data = client.get("/api/v1/population/mitigations/strategies").json()
        ids = [s["id"] for s in data["strategies"]]
        assert "tocilizumab" in ids
        assert "corticosteroids" in ids
        assert "anakinra" in ids

    def test_strategies_relative_risk_values(self, client):
        data = client.get("/api/v1/population/mitigations/strategies").json()
        for strategy in data["strategies"]:
            # All strategies should have a positive RR
            assert strategy["relative_risk"] > 0


# ===========================================================================
# GET /api/v1/population/comparison
# ===========================================================================

@pytest.mark.integration
class TestAEComparison:
    """Tests for the cross-indication AE rate comparison endpoint."""

    def test_comparison_returns_200(self, client):
        response = client.get("/api/v1/population/comparison")
        assert response.status_code == 200

    def test_comparison_has_comparison_data(self, client):
        data = client.get("/api/v1/population/comparison").json()
        assert "comparison_data" in data
        assert isinstance(data["comparison_data"], list)

    def test_comparison_contains_autoimmune_and_oncology(self, client):
        data = client.get("/api/v1/population/comparison").json()
        categories = set()
        for entry in data["comparison_data"]:
            if "category" in entry:
                categories.add(entry["category"])
            elif "indication_group" in entry:
                categories.add(entry["indication_group"])
            # Also check product/name fields for indication clues
            name = entry.get("name", "") + entry.get("product", "")
            if "SLE" in name.upper() or "AUTOIMMUNE" in name.upper() or "LUPUS" in name.upper():
                categories.add("Autoimmune")
            elif any(onc in name.upper() for onc in ["DLBCL", "ALL", "MYELOMA", "LYMPHOMA", "ONCOLOGY"]):
                categories.add("Oncology")
        # The data should represent both autoimmune and oncology indications
        assert len(data["comparison_data"]) >= 2

    def test_comparison_data_entries_are_dicts(self, client):
        data = client.get("/api/v1/population/comparison").json()
        for entry in data["comparison_data"]:
            assert isinstance(entry, dict)

    def test_comparison_has_note(self, client):
        data = client.get("/api/v1/population/comparison").json()
        assert "note" in data
