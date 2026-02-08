"""
Integration tests for CDP (Clinical Development Plan) and therapy API endpoints.

Tests the following endpoints using FastAPI's TestClient:
    - GET /api/v1/cdp/monitoring-schedule
    - GET /api/v1/cdp/eligibility-criteria
    - GET /api/v1/cdp/stopping-rules
    - GET /api/v1/cdp/sample-size
    - GET /api/v1/therapies
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
# GET /api/v1/therapies
# ===========================================================================

@pytest.mark.integration
class TestTherapiesList:
    """Tests for the therapy types listing endpoint."""

    def test_therapies_returns_200(self, client):
        response = client.get("/api/v1/therapies")
        assert response.status_code == 200

    def test_therapies_has_therapies_list(self, client):
        data = client.get("/api/v1/therapies").json()
        assert "therapies" in data
        assert isinstance(data["therapies"], list)

    def test_therapies_list_nonempty(self, client):
        data = client.get("/api/v1/therapies").json()
        assert len(data["therapies"]) > 0

    def test_therapies_have_required_fields(self, client):
        data = client.get("/api/v1/therapies").json()
        for therapy in data["therapies"]:
            assert "id" in therapy
            assert "name" in therapy
            assert "category" in therapy
            assert "data_available" in therapy

    def test_therapies_include_cart_cd19(self, client):
        """The registry should include at least the CAR-T CD19 therapy."""
        data = client.get("/api/v1/therapies").json()
        ids = [t["id"] for t in data["therapies"]]
        assert "cart_cd19" in ids

    def test_cart_cd19_has_data_available(self, client):
        """CAR-T CD19 should have data_available = True."""
        data = client.get("/api/v1/therapies").json()
        cd19 = next(t for t in data["therapies"] if t["id"] == "cart_cd19")
        assert cd19["data_available"] is True

    def test_therapies_have_categories(self, client):
        """Each therapy should have a non-empty category string."""
        data = client.get("/api/v1/therapies").json()
        for therapy in data["therapies"]:
            assert isinstance(therapy["category"], str)
            assert len(therapy["category"]) > 0


# ===========================================================================
# GET /api/v1/cdp/monitoring-schedule
# ===========================================================================

@pytest.mark.integration
class TestMonitoringSchedule:
    """Tests for the CDP monitoring schedule endpoint."""

    def test_monitoring_schedule_returns_200(self, client):
        response = client.get("/api/v1/cdp/monitoring-schedule")
        assert response.status_code == 200

    def test_monitoring_schedule_has_schedule(self, client):
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        assert "schedule" in data
        assert isinstance(data["schedule"], list)

    def test_monitoring_schedule_has_therapy_type(self, client):
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        assert "therapy_type" in data
        assert isinstance(data["therapy_type"], str)

    def test_monitoring_schedule_has_required_time_windows(self, client):
        """The schedule should cover pre-infusion through long-term follow-up."""
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        schedule = data["schedule"]
        time_windows = [entry["time_window"] for entry in schedule]

        # Should have at least a pre-infusion, acute, and long-term window
        assert any("pre" in w.lower() for w in time_windows), (
            "Schedule should include a pre-infusion window"
        )
        assert any("acute" in w.lower() or "d0" in w.lower() for w in time_windows), (
            "Schedule should include an acute monitoring window"
        )
        assert any("long" in w.lower() or "y1" in w.lower() for w in time_windows), (
            "Schedule should include a long-term follow-up window"
        )

    def test_monitoring_schedule_entries_have_required_fields(self, client):
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        for entry in data["schedule"]:
            assert "time_window" in entry
            assert "days" in entry
            assert "activities" in entry
            assert isinstance(entry["activities"], list)
            assert len(entry["activities"]) > 0
            assert "frequency" in entry
            assert "rationale" in entry

    def test_monitoring_schedule_at_least_5_windows(self, client):
        """A comprehensive monitoring schedule should have at least 5 time windows."""
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        assert len(data["schedule"]) >= 5

    def test_monitoring_schedule_custom_therapy_type(self, client):
        """Should accept a custom therapy_type query parameter."""
        response = client.get(
            "/api/v1/cdp/monitoring-schedule",
            params={"therapy_type": "custom-therapy"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["therapy_type"] == "custom-therapy"

    def test_monitoring_schedule_activities_are_strings(self, client):
        """All activities in each window should be non-empty strings."""
        data = client.get("/api/v1/cdp/monitoring-schedule").json()
        for entry in data["schedule"]:
            for activity in entry["activities"]:
                assert isinstance(activity, str)
                assert len(activity) > 0


# ===========================================================================
# GET /api/v1/cdp/eligibility-criteria
# ===========================================================================

@pytest.mark.integration
class TestEligibilityCriteria:
    """Tests for the CDP eligibility criteria endpoint."""

    def test_eligibility_criteria_returns_200(self, client):
        response = client.get("/api/v1/cdp/eligibility-criteria")
        assert response.status_code == 200

    def test_eligibility_has_inclusion_and_exclusion(self, client):
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        assert "inclusion" in data
        assert "exclusion" in data
        assert isinstance(data["inclusion"], list)
        assert isinstance(data["exclusion"], list)

    def test_eligibility_inclusion_nonempty(self, client):
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        assert len(data["inclusion"]) > 0

    def test_eligibility_exclusion_nonempty(self, client):
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        assert len(data["exclusion"]) > 0

    def test_eligibility_criteria_have_required_fields(self, client):
        """Each criterion should have criterion, rationale, and category."""
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        for criterion in data["inclusion"] + data["exclusion"]:
            assert "criterion" in criterion
            assert "rationale" in criterion
            assert "category" in criterion
            assert isinstance(criterion["criterion"], str)
            assert len(criterion["criterion"]) > 0

    def test_eligibility_has_therapy_type(self, client):
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        assert "therapy_type" in data

    def test_eligibility_inclusion_has_age_criterion(self, client):
        """Inclusion criteria should include an age requirement."""
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        criteria_text = [c["criterion"].lower() for c in data["inclusion"]]
        assert any("age" in c for c in criteria_text), (
            "Inclusion criteria should specify an age requirement"
        )

    def test_eligibility_exclusion_has_safety_criteria(self, client):
        """Exclusion criteria should include safety-related exclusions."""
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        categories = [c["category"] for c in data["exclusion"]]
        assert "Safety" in categories, (
            "Exclusion criteria should include Safety category items"
        )

    def test_eligibility_exclusion_has_infection_criterion(self, client):
        """Exclusion criteria should mention active infection."""
        data = client.get("/api/v1/cdp/eligibility-criteria").json()
        criteria_text = [c["criterion"].lower() for c in data["exclusion"]]
        assert any("infection" in c for c in criteria_text), (
            "Exclusion criteria should include an active infection exclusion"
        )

    def test_eligibility_custom_therapy_type(self, client):
        """Should accept a custom therapy_type query parameter."""
        response = client.get(
            "/api/v1/cdp/eligibility-criteria",
            params={"therapy_type": "custom-therapy"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["therapy_type"] == "custom-therapy"


# ===========================================================================
# GET /api/v1/cdp/stopping-rules
# ===========================================================================

@pytest.mark.integration
class TestStoppingRules:
    """Tests for the CDP Bayesian stopping rules endpoint."""

    def test_stopping_rules_returns_200(self, client):
        response = client.get("/api/v1/cdp/stopping-rules")
        assert response.status_code == 200

    def test_stopping_rules_has_rules_list(self, client):
        data = client.get("/api/v1/cdp/stopping-rules").json()
        assert "rules" in data
        assert isinstance(data["rules"], list)

    def test_stopping_rules_has_therapy_type(self, client):
        data = client.get("/api/v1/cdp/stopping-rules").json()
        assert "therapy_type" in data

    def test_stopping_rules_cover_key_ae_types(self, client):
        """Stopping rules should cover CRS, ICANS, and ICAHS."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        ae_types = [rule["ae_type"] for rule in data["rules"]]
        ae_types_lower = [a.lower() for a in ae_types]
        assert any("crs" in a for a in ae_types_lower), "Should have CRS stopping rule"
        assert any("icans" in a for a in ae_types_lower), "Should have ICANS stopping rule"
        assert any("icahs" in a for a in ae_types_lower), "Should have ICAHS stopping rule"

    def test_stopping_rules_have_required_fields(self, client):
        """Each rule should have ae_type, target_rate_pct, posterior_threshold,
        description, and boundaries."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        for rule in data["rules"]:
            assert "ae_type" in rule
            assert "target_rate_pct" in rule
            assert "posterior_threshold" in rule
            assert "description" in rule
            assert "boundaries" in rule
            assert isinstance(rule["boundaries"], list)

    def test_stopping_rules_boundaries_have_valid_structure(self, client):
        """Each boundary point should have n_patients and max_events."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        for rule in data["rules"]:
            for boundary in rule["boundaries"]:
                assert "n_patients" in boundary
                assert "max_events" in boundary
                assert isinstance(boundary["n_patients"], int)
                assert isinstance(boundary["max_events"], int)
                assert boundary["n_patients"] > 0
                assert boundary["max_events"] >= 0

    def test_stopping_rules_boundaries_monotonic(self, client):
        """Within each rule, boundaries should be monotonically non-decreasing."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        for rule in data["rules"]:
            boundaries = rule["boundaries"]
            for i in range(1, len(boundaries)):
                assert boundaries[i]["max_events"] >= boundaries[i - 1]["max_events"], (
                    f"Non-monotonic boundary in {rule['ae_type']}: "
                    f"n={boundaries[i]['n_patients']} has fewer events "
                    f"({boundaries[i]['max_events']}) than "
                    f"n={boundaries[i - 1]['n_patients']} "
                    f"({boundaries[i - 1]['max_events']})"
                )

    def test_stopping_rules_target_rates_positive(self, client):
        """All target rates should be positive percentages."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        for rule in data["rules"]:
            assert rule["target_rate_pct"] > 0

    def test_stopping_rules_thresholds_valid(self, client):
        """All posterior thresholds should be in (0, 1)."""
        data = client.get("/api/v1/cdp/stopping-rules").json()
        for rule in data["rules"]:
            assert 0.0 < rule["posterior_threshold"] < 1.0


# ===========================================================================
# GET /api/v1/cdp/sample-size
# ===========================================================================

@pytest.mark.integration
class TestSampleSize:
    """Tests for the CDP sample size considerations endpoint."""

    def test_sample_size_returns_200(self, client):
        response = client.get("/api/v1/cdp/sample-size")
        assert response.status_code == 200

    def test_sample_size_has_scenarios(self, client):
        data = client.get("/api/v1/cdp/sample-size").json()
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)

    def test_sample_size_has_therapy_type(self, client):
        data = client.get("/api/v1/cdp/sample-size").json()
        assert "therapy_type" in data

    def test_sample_size_scenarios_nonempty(self, client):
        data = client.get("/api/v1/cdp/sample-size").json()
        assert len(data["scenarios"]) > 0

    def test_sample_size_scenarios_have_required_fields(self, client):
        """Each scenario should have target_precision, estimated_n, current_n,
        additional_needed, and notes."""
        data = client.get("/api/v1/cdp/sample-size").json()
        for scenario in data["scenarios"]:
            assert "target_precision" in scenario
            assert "estimated_n" in scenario
            assert "current_n" in scenario
            assert "additional_needed" in scenario
            assert "notes" in scenario

    def test_sample_size_additional_needed_nonnegative(self, client):
        """additional_needed should never be negative."""
        data = client.get("/api/v1/cdp/sample-size").json()
        for scenario in data["scenarios"]:
            assert scenario["additional_needed"] >= 0

    def test_sample_size_estimated_n_gte_current_n(self, client):
        """estimated_n should be >= current_n for all scenarios."""
        data = client.get("/api/v1/cdp/sample-size").json()
        for scenario in data["scenarios"]:
            assert scenario["estimated_n"] >= scenario["current_n"]

    def test_sample_size_additional_equals_difference(self, client):
        """additional_needed should equal estimated_n - current_n."""
        data = client.get("/api/v1/cdp/sample-size").json()
        for scenario in data["scenarios"]:
            expected = scenario["estimated_n"] - scenario["current_n"]
            assert scenario["additional_needed"] == expected

    def test_sample_size_custom_therapy_type(self, client):
        """Should accept a custom therapy_type query parameter."""
        response = client.get(
            "/api/v1/cdp/sample-size",
            params={"therapy_type": "custom-therapy"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["therapy_type"] == "custom-therapy"
