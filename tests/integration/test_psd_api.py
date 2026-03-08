"""
Integration tests for Patient Safety Dashboard API endpoints.

Tests all 11 PSD endpoints using FastAPI's TestClient against the real
application (src/api/app.py).
"""

import re

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


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _assert_common(data: dict) -> None:
    """Check fields common to every PSD response."""
    assert "request_id" in data
    assert isinstance(data["request_id"], str) and len(data["request_id"]) > 0
    assert "timestamp" in data


# ===========================================================================
# GET /api/v1/psd/overview
# ===========================================================================

@pytest.mark.integration
class TestPSDOverview:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/overview")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/overview").json()
        _assert_common(data)
        for key in ("organization", "governance_bodies", "operating_model", "product_portfolio"):
            assert key in data, f"Missing key '{key}'"

    def test_governance_bodies_are_list(self, client):
        data = client.get("/api/v1/psd/overview").json()
        assert isinstance(data["governance_bodies"], list)
        assert len(data["governance_bodies"]) > 0


# ===========================================================================
# GET /api/v1/psd/compliance/us
# ===========================================================================

@pytest.mark.integration
class TestPSDComplianceUS:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/compliance/us")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/compliance/us").json()
        _assert_common(data)
        for key in ("product", "nda_number", "compliance_items", "reporting_timelines",
                     "fda_actions", "overall_status", "summary"):
            assert key in data, f"Missing key '{key}'"

    def test_overall_status_is_valid_rag(self, client):
        data = client.get("/api/v1/psd/compliance/us").json()
        assert data["overall_status"] in ("red", "amber", "green")

    def test_reporting_timeline_rates_in_range(self, client):
        data = client.get("/api/v1/psd/compliance/us").json()
        for rt in data["reporting_timelines"]:
            assert 0 <= rt["compliance_rate"] <= 100


# ===========================================================================
# GET /api/v1/psd/compliance/eu
# ===========================================================================

@pytest.mark.integration
class TestPSDComplianceEU:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/compliance/eu")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/compliance/eu").json()
        _assert_common(data)
        for key in ("product", "eu_number", "gvp_modules", "eudravigilance_stats",
                     "qppv_network", "psmf", "overall_status"):
            assert key in data, f"Missing key '{key}'"

    def test_gvp_modules_are_list(self, client):
        data = client.get("/api/v1/psd/compliance/eu").json()
        assert isinstance(data["gvp_modules"], list)
        assert len(data["gvp_modules"]) > 0


# ===========================================================================
# GET /api/v1/psd/icsr
# ===========================================================================

@pytest.mark.integration
class TestPSDICSR:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/icsr")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/icsr").json()
        _assert_common(data)
        for key in ("reporting_period", "total_cases", "case_volumes_by_source",
                     "case_volumes_by_seriousness", "pipeline_metrics", "compliance_rates"):
            assert key in data, f"Missing key '{key}'"

    def test_case_volume_percentages_sum(self, client):
        data = client.get("/api/v1/psd/icsr").json()
        pcts = [v["percentage"] for v in data["case_volumes_by_source"]]
        assert all(0 <= p <= 100 for p in pcts)

    def test_total_cases_positive(self, client):
        data = client.get("/api/v1/psd/icsr").json()
        assert data["total_cases"] > 0


# ===========================================================================
# GET /api/v1/psd/signals
# ===========================================================================

@pytest.mark.integration
class TestPSDSignals:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/signals")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/signals").json()
        _assert_common(data)
        for key in ("product", "total_signals", "active_signals",
                     "pipeline_summary", "detection_methods"):
            assert key in data, f"Missing key '{key}'"

    def test_total_signals_matches_list(self, client):
        data = client.get("/api/v1/psd/signals").json()
        assert data["total_signals"] == len(data["active_signals"])

    def test_signal_dates_valid(self, client):
        data = client.get("/api/v1/psd/signals").json()
        for sig in data["active_signals"]:
            assert DATE_RE.match(sig["detection_date"]), f"Bad date: {sig['detection_date']}"


# ===========================================================================
# GET /api/v1/psd/aggregate-reports
# ===========================================================================

@pytest.mark.integration
class TestPSDAggregateReports:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/aggregate-reports")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/aggregate-reports").json()
        _assert_common(data)
        for key in ("product", "reports", "calendar_year", "upcoming_deadlines"):
            assert key in data, f"Missing key '{key}'"

    def test_report_progress_in_range(self, client):
        data = client.get("/api/v1/psd/aggregate-reports").json()
        for r in data["reports"]:
            assert 0 <= r["progress_pct"] <= 100
            assert r["sections_complete"] <= r["sections_total"]


# ===========================================================================
# GET /api/v1/psd/risk-management
# ===========================================================================

@pytest.mark.integration
class TestPSDRiskManagement:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/risk-management")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/risk-management").json()
        _assert_common(data)
        for key in ("product", "rmp", "rmp_commitments", "rems", "rems_elements",
                     "risk_minimization_effectiveness"):
            assert key in data, f"Missing key '{key}'"

    def test_rems_compliance_in_range(self, client):
        data = client.get("/api/v1/psd/risk-management").json()
        for elem in data["rems_elements"]:
            assert 0 <= elem["compliance_rate"] <= 100
            assert elem["status"] in ("red", "amber", "green")


# ===========================================================================
# GET /api/v1/psd/quality
# ===========================================================================

@pytest.mark.integration
class TestPSDQuality:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/quality")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/quality").json()
        _assert_common(data)
        for key in ("sop_inventory", "capa_tracker", "capa_items",
                     "training_compliance", "audits_inspections", "quality_metrics"):
            assert key in data, f"Missing key '{key}'"

    def test_sop_statuses_valid_rag(self, client):
        data = client.get("/api/v1/psd/quality").json()
        for sop in data["sop_inventory"]:
            assert sop["status"] in ("red", "amber", "green")


# ===========================================================================
# GET /api/v1/psd/clinical-trials
# ===========================================================================

@pytest.mark.integration
class TestPSDClinicalTrials:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/clinical-trials")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/clinical-trials").json()
        _assert_common(data)
        for key in ("product", "trials", "dsmb_calendar", "susar_summary",
                     "safety_review_schedule"):
            assert key in data, f"Missing key '{key}'"

    def test_trial_enrollment_consistent(self, client):
        data = client.get("/api/v1/psd/clinical-trials").json()
        for trial in data["trials"]:
            assert trial["current_enrollment"] <= trial["target_enrollment"]
            assert trial["sae_count"] >= 0
            assert trial["susar_count"] >= 0


# ===========================================================================
# GET /api/v1/psd/kpis
# ===========================================================================

@pytest.mark.integration
class TestPSDKPIs:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/kpis")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/kpis").json()
        _assert_common(data)
        for key in ("compliance_kpis", "quality_kpis", "signal_kpis",
                     "portfolio_health_kpis", "overall_rag", "kpi_count"):
            assert key in data, f"Missing key '{key}'"

    def test_overall_rag_valid(self, client):
        data = client.get("/api/v1/psd/kpis").json()
        assert data["overall_rag"] in ("red", "amber", "green")

    def test_kpi_items_have_required_fields(self, client):
        data = client.get("/api/v1/psd/kpis").json()
        for kpi in data["compliance_kpis"]:
            assert "name" in kpi
            assert "value" in kpi
            assert "rag" in kpi


# ===========================================================================
# GET /api/v1/psd/benefit-risk
# ===========================================================================

@pytest.mark.integration
class TestPSDBenefitRisk:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/benefit-risk")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/benefit-risk").json()
        _assert_common(data)
        for key in ("product", "indication", "benefit_risk_summary", "labeling_status",
                     "effects_table", "key_benefits", "key_risks",
                     "overall_benefit_risk_conclusion"):
            assert key in data, f"Missing key '{key}'"

    def test_effects_table_has_entries(self, client):
        data = client.get("/api/v1/psd/benefit-risk").json()
        assert isinstance(data["effects_table"], list)
        assert len(data["effects_table"]) > 0
        for row in data["effects_table"]:
            assert "effect" in row
            assert "category" in row


@pytest.mark.integration
class TestPSDAIIntelligence:
    def test_returns_200(self, client):
        resp = client.get("/api/v1/psd/ai-intelligence")
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.get("/api/v1/psd/ai-intelligence").json()
        _assert_common(data)
        for key in ("product", "therapeutic_area", "ai_chain", "active_hypotheses",
                     "mechanistic_analysis", "drug_class_comparison", "ai_insights_summary"):
            assert key in data, f"Missing key '{key}'"

    def test_hypotheses_have_confidence(self, client):
        data = client.get("/api/v1/psd/ai-intelligence").json()
        assert len(data["active_hypotheses"]) == 3
        for h in data["active_hypotheses"]:
            assert 0 <= h["confidence"] <= 1
            assert h["biological_plausibility"] in ("High", "Medium", "Low")
            assert h["status"] in ("Generated", "Under Investigation", "Confirmed", "Refuted")

    def test_ai_chain_has_6_stages(self, client):
        data = client.get("/api/v1/psd/ai-intelligence").json()
        assert len(data["ai_chain"]["stages"]) == 6

    def test_drug_class_comparison(self, client):
        data = client.get("/api/v1/psd/ai-intelligence").json()
        assert len(data["drug_class_comparison"]) == 5
        drugs = [d["drug"] for d in data["drug_class_comparison"]]
        assert "Prosinertimib" in drugs

    def test_therapeutic_area_context(self, client):
        data = client.get("/api/v1/psd/ai-intelligence").json()
        ta = data["therapeutic_area"]
        assert "NSCLC" in ta["disease"]
        assert "EGFR" in ta["drug_class"]


@pytest.mark.integration
class TestPSDChat:
    def test_returns_200(self, client):
        resp = client.post("/api/v1/psd/chat", json={"question": "cardiac failure"})
        assert resp.status_code == 200

    def test_has_expected_keys(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "test"}).json()
        _assert_common(data)
        for key in ("question", "answer", "sources", "confidence", "follow_up_questions"):
            assert key in data, f"Missing key '{key}'"

    def test_cardiac_question_returns_relevant_answer(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "Why cardiac failure?"}).json()
        assert "cardiac" in data["answer"].lower() or "HER2" in data["answer"]
        assert data["confidence"] > 0.5
        assert len(data["sources"]) > 0

    def test_comparison_question(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "compare to osimertinib"}).json()
        assert "osimertinib" in data["answer"].lower()

    def test_ild_question(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "ILD mechanism"}).json()
        assert "ILD" in data["answer"] or "pneumonitis" in data["answer"].lower() or "alveolar" in data["answer"].lower()

    def test_benefit_risk_question(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "benefit risk assessment"}).json()
        assert "benefit" in data["answer"].lower() or "risk" in data["answer"].lower()

    def test_unknown_question_returns_fallback(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "random unrelated topic xyz"}).json()
        assert len(data["follow_up_questions"]) > 0

    def test_follow_up_questions_provided(self, client):
        data = client.post("/api/v1/psd/chat", json={"question": "cardiac"}).json()
        assert isinstance(data["follow_up_questions"], list)
        assert len(data["follow_up_questions"]) >= 2
