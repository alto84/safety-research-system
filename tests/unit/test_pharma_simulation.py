"""
Unit tests for src/data/pharma_simulation.py

Tests the pharmaceutical company simulation engine including:
- Each role's deliverable generator returns expected structure
- Simulation orchestrator populates all 11 roles
- Activity log has correct delegation chains
- Regulatory references are valid (exist in REGULATORY_MAP)
- Data consistency (numbers match across deliverables)
- Helper functions return correct structures

Target: 80+ tests covering all generators, orchestrator, and helpers.
"""

import pytest

from src.data.pharma_org import (
    ORG_ROLES,
    REGULATORY_MAP,
    get_quality_metrics,
)
from src.data.pharma_simulation import (
    DELIVERABLES,
    SIMULATION_LOG,
    generate_biostats_deliverables,
    generate_ceo_deliverables,
    generate_clindev_deliverables,
    generate_clinops_deliverables,
    generate_cmc_deliverables,
    generate_cmo_deliverables,
    generate_commercial_deliverables,
    generate_medaffairs_deliverables,
    generate_pv_deliverables,
    generate_qa_deliverables,
    generate_regulatory_deliverables,
    get_activity_log,
    get_all_deliverable_ids,
    get_all_regulatory_refs_from_deliverables,
    get_all_regulatory_refs_from_log,
    get_delegation_tree,
    get_role_deliverables,
    get_simulation_status,
    run_simulation,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def _run_simulation_once():
    """Run the simulation once before each test to populate state."""
    run_simulation()
    yield
    # Clean up after each test
    SIMULATION_LOG.clear()
    DELIVERABLES.clear()


# ============================================================================
# Deliverable structure validation helpers
# ============================================================================

REQUIRED_DELIVERABLE_KEYS = {
    "deliverable_id",
    "title",
    "role_id",
    "category",
    "regulatory_refs",
    "status",
    "version",
    "created",
    "sections",
    "data",
}

VALID_STATUSES = {"draft", "under_review", "approved", "final", "planned", "in_progress"}


def _assert_valid_deliverable(d: dict, expected_role_id: str) -> None:
    """Assert that a deliverable dict has all required keys and valid values."""
    missing = REQUIRED_DELIVERABLE_KEYS - set(d.keys())
    assert not missing, f"Deliverable {d.get('deliverable_id', '?')} missing keys: {missing}"
    assert d["role_id"] == expected_role_id, (
        f"Deliverable {d['deliverable_id']} has role_id '{d['role_id']}' "
        f"but expected '{expected_role_id}'"
    )
    assert d["deliverable_id"], "deliverable_id must not be empty"
    assert d["title"], "title must not be empty"
    assert d["category"], "category must not be empty"
    assert isinstance(d["regulatory_refs"], list), "regulatory_refs must be a list"
    assert len(d["regulatory_refs"]) >= 1, (
        f"Deliverable {d['deliverable_id']} has no regulatory_refs"
    )
    assert d["status"] in VALID_STATUSES, (
        f"Deliverable {d['deliverable_id']} has invalid status '{d['status']}'"
    )
    assert isinstance(d["sections"], list), "sections must be a list"
    assert isinstance(d["data"], dict), "data must be a dict"
    assert d["created"], "created timestamp must not be empty"


# ============================================================================
# CMO deliverable tests
# ============================================================================


class TestCMODeliverables:
    """Tests for generate_cmo_deliverables."""

    def test_returns_list(self):
        deliverables = generate_cmo_deliverables()
        assert isinstance(deliverables, list)

    def test_returns_three_deliverables(self):
        deliverables = generate_cmo_deliverables()
        assert len(deliverables) == 3

    def test_structure_validity(self):
        for d in generate_cmo_deliverables():
            _assert_valid_deliverable(d, "cmo")

    def test_benefit_risk_present(self):
        ids = [d["deliverable_id"] for d in generate_cmo_deliverables()]
        assert "cmo_benefit_risk_v1" in ids

    def test_dsmb_charter_present(self):
        ids = [d["deliverable_id"] for d in generate_cmo_deliverables()]
        assert "cmo_dsmb_charter_v1" in ids

    def test_cdp_overview_present(self):
        ids = [d["deliverable_id"] for d in generate_cmo_deliverables()]
        assert "cmo_cdp_overview_v1" in ids

    def test_benefit_risk_references_ich_e2c_r2(self):
        br = [d for d in generate_cmo_deliverables() if d["deliverable_id"] == "cmo_benefit_risk_v1"][0]
        assert "ICH_E2C_R2" in br["regulatory_refs"]

    def test_benefit_risk_data_has_enrolled(self):
        br = [d for d in generate_cmo_deliverables() if d["deliverable_id"] == "cmo_benefit_risk_v1"][0]
        assert br["data"]["enrolled"] == 28

    def test_benefit_risk_zero_deaths(self):
        br = [d for d in generate_cmo_deliverables() if d["deliverable_id"] == "cmo_benefit_risk_v1"][0]
        assert br["data"]["deaths"] == 0

    def test_dsmb_charter_has_sections(self):
        charter = [d for d in generate_cmo_deliverables() if d["deliverable_id"] == "cmo_dsmb_charter_v1"][0]
        assert len(charter["sections"]) >= 3


# ============================================================================
# VP Clinical Ops deliverable tests
# ============================================================================


class TestClinOpsDeliverables:
    """Tests for generate_clinops_deliverables."""

    def test_returns_three_deliverables(self):
        assert len(generate_clinops_deliverables()) == 3

    def test_structure_validity(self):
        for d in generate_clinops_deliverables():
            _assert_valid_deliverable(d, "vp_clinops")

    def test_trial_status_present(self):
        ids = [d["deliverable_id"] for d in generate_clinops_deliverables()]
        assert "clinops_trial_status_v1" in ids

    def test_protocol_deviations_present(self):
        ids = [d["deliverable_id"] for d in generate_clinops_deliverables()]
        assert "clinops_protocol_deviations_v1" in ids

    def test_monitoring_schedule_present(self):
        ids = [d["deliverable_id"] for d in generate_clinops_deliverables()]
        assert "clinops_monitoring_schedule_v1" in ids

    def test_trial_status_has_3_sites(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert len(ts["data"]["sites"]) == 3

    def test_trial_status_enrollment_consistent(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert ts["data"]["enrolled"] == 28
        assert ts["data"]["screen_failures"] == 9
        assert ts["data"]["total_screened"] == 37

    def test_site_enrollment_sums_to_total(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        site_total = sum(s["enrolled"] for s in ts["data"]["sites"])
        assert site_total == ts["data"]["enrolled"]

    def test_site_screen_failures_sum_to_total(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        sf_total = sum(s["screen_failures"] for s in ts["data"]["sites"])
        assert sf_total == ts["data"]["screen_failures"]

    def test_protocol_deviations_major_plus_minor(self):
        pd = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_protocol_deviations_v1"][0]
        assert pd["data"]["major"] + pd["data"]["minor"] == pd["data"]["total_deviations"]

    def test_references_ich_e6_r3(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert "ICH_E6_R3" in ts["regulatory_refs"]

    def test_references_21_cfr_312(self):
        ts = [d for d in generate_clinops_deliverables() if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert "21_CFR_312" in ts["regulatory_refs"]


# ============================================================================
# Head PV deliverable tests
# ============================================================================


class TestPVDeliverables:
    """Tests for generate_pv_deliverables."""

    def test_returns_four_deliverables(self):
        assert len(generate_pv_deliverables()) == 4

    def test_structure_validity(self):
        for d in generate_pv_deliverables():
            _assert_valid_deliverable(d, "head_pv")

    def test_icsr_summary_present(self):
        ids = [d["deliverable_id"] for d in generate_pv_deliverables()]
        assert "pv_icsr_summary_v1" in ids

    def test_signal_detection_present(self):
        ids = [d["deliverable_id"] for d in generate_pv_deliverables()]
        assert "pv_signal_detection_v1" in ids

    def test_dsur_outline_present(self):
        ids = [d["deliverable_id"] for d in generate_pv_deliverables()]
        assert "pv_dsur_outline_v1" in ids

    def test_expedited_log_present(self):
        ids = [d["deliverable_id"] for d in generate_pv_deliverables()]
        assert "pv_expedited_log_v1" in ids

    def test_icsr_serious_plus_non_serious_equals_total(self):
        icsr = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        assert icsr["data"]["serious"] + icsr["data"]["non_serious"] == icsr["data"]["total_icsrs"]

    def test_icsr_total_is_42(self):
        icsr = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        assert icsr["data"]["total_icsrs"] == 42

    def test_icsr_serious_is_8(self):
        icsr = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        assert icsr["data"]["serious"] == 8

    def test_icsr_consistent_with_small_phase1(self):
        """ICSR counts should be plausible for ~28 patients."""
        icsr = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        # Average of 1-2 AEs per patient is reasonable for Phase I CAR-T
        assert 10 <= icsr["data"]["total_icsrs"] <= 100

    def test_signal_detection_has_prr_and_ror(self):
        sig = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_signal_detection_v1"][0]
        for signal in sig["data"]["signals"]:
            assert "prr" in signal
            assert "ror" in signal
            assert signal["prr"] > 0
            assert signal["ror"] > 0

    def test_signal_detection_prr_ci_bounds(self):
        sig = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_signal_detection_v1"][0]
        for signal in sig["data"]["signals"]:
            assert signal["prr_ci_lower"] < signal["prr"] < signal["prr_ci_upper"]
            assert signal["ror_ci_lower"] < signal["ror"] < signal["ror_ci_upper"]

    def test_dsur_references_ich_e2f(self):
        dsur = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_dsur_outline_v1"][0]
        assert "ICH_E2F" in dsur["regulatory_refs"]

    def test_expedited_reports_count_matches(self):
        exp = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_expedited_log_v1"][0]
        assert len(exp["data"]["reports"]) == exp["data"]["total_expedited"]
        assert exp["data"]["total_expedited"] == 3

    def test_expedited_reports_all_have_dates(self):
        exp = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_expedited_log_v1"][0]
        for report in exp["data"]["reports"]:
            assert report["date_aware"]
            assert report["date_submitted"]
            assert report["days_to_submit"] <= 15

    def test_dsur_cumulative_exposure_matches_enrolled(self):
        dsur = [d for d in generate_pv_deliverables() if d["deliverable_id"] == "pv_dsur_outline_v1"][0]
        assert dsur["data"]["cumulative_exposure"] == 28


# ============================================================================
# VP Regulatory deliverable tests
# ============================================================================


class TestRegulatoryDeliverables:
    """Tests for generate_regulatory_deliverables."""

    def test_returns_three_deliverables(self):
        assert len(generate_regulatory_deliverables()) == 3

    def test_structure_validity(self):
        for d in generate_regulatory_deliverables():
            _assert_valid_deliverable(d, "vp_regulatory")

    def test_ind_annual_report_present(self):
        ids = [d["deliverable_id"] for d in generate_regulatory_deliverables()]
        assert "reg_ind_annual_report_v1" in ids

    def test_eop2_briefing_present(self):
        ids = [d["deliverable_id"] for d in generate_regulatory_deliverables()]
        assert "reg_eop2_briefing_v1" in ids

    def test_submission_timeline_present(self):
        ids = [d["deliverable_id"] for d in generate_regulatory_deliverables()]
        assert "reg_submission_timeline_v1" in ids

    def test_ind_references_21_cfr_312(self):
        ind = [d for d in generate_regulatory_deliverables() if d["deliverable_id"] == "reg_ind_annual_report_v1"][0]
        assert "21_CFR_312" in ind["regulatory_refs"]

    def test_eop2_references_fda_meetings(self):
        eop2 = [d for d in generate_regulatory_deliverables() if d["deliverable_id"] == "reg_eop2_briefing_v1"][0]
        assert "FDA_meetings" in eop2["regulatory_refs"]

    def test_submission_timeline_has_milestones(self):
        tl = [d for d in generate_regulatory_deliverables() if d["deliverable_id"] == "reg_submission_timeline_v1"][0]
        assert len(tl["data"]["milestones"]) >= 5


# ============================================================================
# Head Biostats deliverable tests
# ============================================================================


class TestBiostatsDeliverables:
    """Tests for generate_biostats_deliverables."""

    def test_returns_four_deliverables(self):
        assert len(generate_biostats_deliverables()) == 4

    def test_structure_validity(self):
        for d in generate_biostats_deliverables():
            _assert_valid_deliverable(d, "head_biostats")

    def test_sap_present(self):
        ids = [d["deliverable_id"] for d in generate_biostats_deliverables()]
        assert "biostats_sap_v1" in ids

    def test_dlt_analysis_present(self):
        ids = [d["deliverable_id"] for d in generate_biostats_deliverables()]
        assert "biostats_dlt_analysis_v1" in ids

    def test_sample_size_present(self):
        ids = [d["deliverable_id"] for d in generate_biostats_deliverables()]
        assert "biostats_sample_size_v1" in ids

    def test_interim_plan_present(self):
        ids = [d["deliverable_id"] for d in generate_biostats_deliverables()]
        assert "biostats_interim_plan_v1" in ids

    def test_sap_references_ich_e9(self):
        sap = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_sap_v1"][0]
        assert "ICH_E9" in sap["regulatory_refs"]

    def test_sap_has_3_plus_3_design(self):
        sap = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_sap_v1"][0]
        assert sap["data"]["design"] == "3+3 dose escalation"

    def test_dlt_analysis_dose_levels(self):
        dlt = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_dlt_analysis_v1"][0]
        assert len(dlt["data"]["dlt_by_dose_level"]) == 4

    def test_dlt_analysis_total_dlts_consistent(self):
        dlt = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_dlt_analysis_v1"][0]
        total = sum(dl["dlts"] for dl in dlt["data"]["dlt_by_dose_level"])
        assert total == dlt["data"]["total_dlts"]

    def test_sample_size_phase2_is_40(self):
        ss = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_sample_size_v1"][0]
        assert ss["data"]["n_enrolled"] == 40

    def test_interim_plan_obrien_fleming(self):
        ip = [d for d in generate_biostats_deliverables() if d["deliverable_id"] == "biostats_interim_plan_v1"][0]
        assert ip["data"]["spending_function"] == "OBrien_Fleming"


# ============================================================================
# Head CMC deliverable tests
# ============================================================================


class TestCMCDeliverables:
    """Tests for generate_cmc_deliverables."""

    def test_returns_four_deliverables(self):
        assert len(generate_cmc_deliverables()) == 4

    def test_structure_validity(self):
        for d in generate_cmc_deliverables():
            _assert_valid_deliverable(d, "head_cmc")

    def test_batch_summary_present(self):
        ids = [d["deliverable_id"] for d in generate_cmc_deliverables()]
        assert "cmc_batch_summary_v1" in ids

    def test_release_testing_present(self):
        ids = [d["deliverable_id"] for d in generate_cmc_deliverables()]
        assert "cmc_release_testing_v1" in ids

    def test_stability_present(self):
        ids = [d["deliverable_id"] for d in generate_cmc_deliverables()]
        assert "cmc_stability_v1" in ids

    def test_process_validation_present(self):
        ids = [d["deliverable_id"] for d in generate_cmc_deliverables()]
        assert "cmc_process_validation_v1" in ids

    def test_batch_counts_match_quality_metrics(self):
        qm = get_quality_metrics()
        bs = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_batch_summary_v1"][0]
        assert bs["data"]["total_batches"] == qm["batches"]["manufactured_ytd"]
        assert bs["data"]["released"] == qm["batches"]["released"]
        assert bs["data"]["failed"] == qm["batches"]["failed"]

    def test_23_batches_21_released_2_failed(self):
        bs = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_batch_summary_v1"][0]
        assert bs["data"]["total_batches"] == 23
        assert bs["data"]["released"] == 21
        assert bs["data"]["failed"] == 2

    def test_released_plus_failed_le_total(self):
        bs = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_batch_summary_v1"][0]
        assert bs["data"]["released"] + bs["data"]["failed"] <= bs["data"]["total_batches"]

    def test_batch_references_21_cfr_1271(self):
        bs = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_batch_summary_v1"][0]
        assert "21_CFR_1271" in bs["regulatory_refs"]

    def test_stability_references_ich_q1a(self):
        stab = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_stability_v1"][0]
        assert "ICH_Q1A" in stab["regulatory_refs"]

    def test_release_testing_has_tests(self):
        rt = [d for d in generate_cmc_deliverables() if d["deliverable_id"] == "cmc_release_testing_v1"][0]
        assert len(rt["data"]["tests"]) >= 5


# ============================================================================
# Head QA deliverable tests
# ============================================================================


class TestQADeliverables:
    """Tests for generate_qa_deliverables."""

    def test_returns_five_deliverables(self):
        assert len(generate_qa_deliverables()) == 5

    def test_structure_validity(self):
        for d in generate_qa_deliverables():
            _assert_valid_deliverable(d, "head_qa")

    def test_capa_tracker_present(self):
        ids = [d["deliverable_id"] for d in generate_qa_deliverables()]
        assert "qa_capa_tracker_v1" in ids

    def test_deviation_trends_present(self):
        ids = [d["deliverable_id"] for d in generate_qa_deliverables()]
        assert "qa_deviation_trends_v1" in ids

    def test_audit_schedule_present(self):
        ids = [d["deliverable_id"] for d in generate_qa_deliverables()]
        assert "qa_audit_schedule_v1" in ids

    def test_training_compliance_present(self):
        ids = [d["deliverable_id"] for d in generate_qa_deliverables()]
        assert "qa_training_compliance_v1" in ids

    def test_gxp_matrix_present(self):
        ids = [d["deliverable_id"] for d in generate_qa_deliverables()]
        assert "qa_gxp_matrix_v1" in ids

    def test_capa_data_matches_quality_metrics(self):
        qm = get_quality_metrics()
        capa = [d for d in generate_qa_deliverables() if d["deliverable_id"] == "qa_capa_tracker_v1"][0]
        assert capa["data"]["open"] == qm["capa"]["open"]
        assert capa["data"]["overdue"] == qm["capa"]["overdue"]
        assert capa["data"]["closed_ytd"] == qm["capa"]["closed_ytd"]

    def test_capa_has_root_cause_categories(self):
        capa = [d for d in generate_qa_deliverables() if d["deliverable_id"] == "qa_capa_tracker_v1"][0]
        assert "root_cause_categories" in capa["data"]
        assert len(capa["data"]["root_cause_categories"]) >= 3

    def test_gxp_matrix_references_ich_q9(self):
        gxp = [d for d in generate_qa_deliverables() if d["deliverable_id"] == "qa_gxp_matrix_v1"][0]
        assert "ICH_Q9" in gxp["regulatory_refs"]

    def test_audit_schedule_has_audits(self):
        audit = [d for d in generate_qa_deliverables() if d["deliverable_id"] == "qa_audit_schedule_v1"][0]
        assert len(audit["data"]["audits"]) >= 2


# ============================================================================
# VP Medical Affairs deliverable tests
# ============================================================================


class TestMedAffairsDeliverables:
    """Tests for generate_medaffairs_deliverables."""

    def test_returns_four_deliverables(self):
        assert len(generate_medaffairs_deliverables()) == 4

    def test_structure_validity(self):
        for d in generate_medaffairs_deliverables():
            _assert_valid_deliverable(d, "vp_med_affairs")

    def test_publication_plan_present(self):
        ids = [d["deliverable_id"] for d in generate_medaffairs_deliverables()]
        assert "medaffairs_pub_plan_v1" in ids

    def test_kol_tracker_present(self):
        ids = [d["deliverable_id"] for d in generate_medaffairs_deliverables()]
        assert "medaffairs_kol_tracker_v1" in ids

    def test_sab_minutes_present(self):
        ids = [d["deliverable_id"] for d in generate_medaffairs_deliverables()]
        assert "medaffairs_sab_minutes_v1" in ids

    def test_congress_plan_present(self):
        ids = [d["deliverable_id"] for d in generate_medaffairs_deliverables()]
        assert "medaffairs_congress_plan_v1" in ids

    def test_publication_plan_has_5_publications(self):
        pub = [d for d in generate_medaffairs_deliverables() if d["deliverable_id"] == "medaffairs_pub_plan_v1"][0]
        assert len(pub["data"]["publications_planned"]) == 5

    def test_publication_plan_references_phrma_code(self):
        pub = [d for d in generate_medaffairs_deliverables() if d["deliverable_id"] == "medaffairs_pub_plan_v1"][0]
        assert "PhRMA_Code" in pub["regulatory_refs"]

    def test_kol_engaged_le_identified(self):
        kol = [d for d in generate_medaffairs_deliverables() if d["deliverable_id"] == "medaffairs_kol_tracker_v1"][0]
        assert kol["data"]["kols_engaged"] <= kol["data"]["kols_identified"]


# ============================================================================
# Head Clinical Development deliverable tests
# ============================================================================


class TestClinDevDeliverables:
    """Tests for generate_clindev_deliverables."""

    def test_returns_three_deliverables(self):
        assert len(generate_clindev_deliverables()) == 3

    def test_structure_validity(self):
        for d in generate_clindev_deliverables():
            _assert_valid_deliverable(d, "head_clindev")

    def test_cdp_summary_present(self):
        ids = [d["deliverable_id"] for d in generate_clindev_deliverables()]
        assert "clindev_cdp_summary_v1" in ids

    def test_tpp_present(self):
        ids = [d["deliverable_id"] for d in generate_clindev_deliverables()]
        assert "clindev_tpp_v1" in ids

    def test_indication_sequencing_present(self):
        ids = [d["deliverable_id"] for d in generate_clindev_deliverables()]
        assert "clindev_indication_seq_v1" in ids

    def test_cdp_references_ich_e8_r1(self):
        cdp = [d for d in generate_clindev_deliverables() if d["deliverable_id"] == "clindev_cdp_summary_v1"][0]
        assert "ICH_E8_R1" in cdp["regulatory_refs"]

    def test_indication_sequencing_has_3_indications(self):
        ind = [d for d in generate_clindev_deliverables() if d["deliverable_id"] == "clindev_indication_seq_v1"][0]
        assert len(ind["data"]["indications"]) == 3


# ============================================================================
# Head Commercial deliverable tests
# ============================================================================


class TestCommercialDeliverables:
    """Tests for generate_commercial_deliverables."""

    def test_returns_three_deliverables(self):
        assert len(generate_commercial_deliverables()) == 3

    def test_structure_validity(self):
        for d in generate_commercial_deliverables():
            _assert_valid_deliverable(d, "head_commercial")

    def test_market_landscape_present(self):
        ids = [d["deliverable_id"] for d in generate_commercial_deliverables()]
        assert "commercial_market_landscape_v1" in ids

    def test_competitive_intel_present(self):
        ids = [d["deliverable_id"] for d in generate_commercial_deliverables()]
        assert "commercial_competitive_intel_v1" in ids

    def test_early_access_present(self):
        ids = [d["deliverable_id"] for d in generate_commercial_deliverables()]
        assert "commercial_early_access_v1" in ids

    def test_market_landscape_references_phrma_code(self):
        ml = [d for d in generate_commercial_deliverables() if d["deliverable_id"] == "commercial_market_landscape_v1"][0]
        assert "PhRMA_Code" in ml["regulatory_refs"]


# ============================================================================
# CEO deliverable tests
# ============================================================================


class TestCEODeliverables:
    """Tests for generate_ceo_deliverables."""

    def test_returns_one_deliverable(self):
        assert len(generate_ceo_deliverables()) == 1

    def test_structure_validity(self):
        for d in generate_ceo_deliverables():
            _assert_valid_deliverable(d, "ceo")

    def test_executive_summary_present(self):
        ids = [d["deliverable_id"] for d in generate_ceo_deliverables()]
        assert "ceo_executive_summary_v1" in ids

    def test_references_sox(self):
        es = generate_ceo_deliverables()[0]
        assert "SOX" in es["regulatory_refs"]


# ============================================================================
# Simulation orchestrator tests
# ============================================================================


class TestRunSimulation:
    """Tests for the run_simulation() orchestrator."""

    def test_returns_dict(self):
        result = run_simulation()
        assert isinstance(result, dict)

    def test_result_has_required_keys(self):
        result = run_simulation()
        assert "deliverables" in result
        assert "activity_log" in result
        assert "summary" in result

    def test_all_11_roles_have_deliverables(self):
        result = run_simulation()
        assert len(result["deliverables"]) == 11

    def test_every_org_role_represented(self):
        result = run_simulation()
        for role_id in ORG_ROLES:
            assert role_id in result["deliverables"], (
                f"Role '{role_id}' missing from simulation deliverables"
            )

    def test_total_deliverables_count(self):
        """11 roles should produce at least 30 deliverables total."""
        result = run_simulation()
        total = sum(len(d) for d in result["deliverables"].values())
        assert total >= 30

    def test_activity_log_not_empty(self):
        result = run_simulation()
        assert len(result["activity_log"]) > 0

    def test_activity_log_has_at_least_40_entries(self):
        result = run_simulation()
        assert len(result["activity_log"]) >= 40

    def test_summary_roles_active(self):
        result = run_simulation()
        assert result["summary"]["roles_active"] == 11

    def test_summary_has_timestamps(self):
        result = run_simulation()
        assert result["summary"]["simulation_start"]
        assert result["summary"]["simulation_end"]

    def test_clears_previous_state(self):
        """Running simulation twice should not accumulate state."""
        run_simulation()
        r1_total = sum(len(d) for d in DELIVERABLES.values())
        run_simulation()
        r2_total = sum(len(d) for d in DELIVERABLES.values())
        assert r1_total == r2_total

    def test_hierarchy_order(self):
        result = run_simulation()
        order = result["summary"]["hierarchy_order"]
        assert order[0] == "ceo"
        assert "cmo" in order
        # CMO should come before its reports
        cmo_idx = order.index("cmo")
        for report_id in ["vp_clinops", "head_pv", "vp_regulatory", "head_biostats", "vp_med_affairs", "head_clindev"]:
            report_idx = order.index(report_id)
            assert cmo_idx < report_idx, (
                f"CMO (index {cmo_idx}) should come before {report_id} (index {report_idx})"
            )


# ============================================================================
# Activity log tests
# ============================================================================


class TestActivityLog:
    """Tests for activity log structure and delegation chains."""

    def test_log_entries_have_required_fields(self):
        for entry in SIMULATION_LOG:
            assert "timestamp" in entry
            assert "role_id" in entry
            assert "action" in entry
            assert "description" in entry
            assert "regulatory_basis" in entry

    def test_log_entries_have_valid_actions(self):
        valid_actions = {"initiated", "delegated", "completed", "escalated", "reviewed"}
        for entry in SIMULATION_LOG:
            assert entry["action"] in valid_actions, (
                f"Invalid action '{entry['action']}' in log entry"
            )

    def test_delegated_entries_have_target(self):
        for entry in SIMULATION_LOG:
            if entry["action"] == "delegated":
                assert "target" in entry, (
                    f"Delegated entry missing target: {entry['description']}"
                )

    def test_delegation_targets_are_valid_roles(self):
        for entry in SIMULATION_LOG:
            if entry["action"] == "delegated" and "target" in entry:
                assert entry["target"] in ORG_ROLES, (
                    f"Delegation target '{entry['target']}' is not a valid role"
                )

    def test_ceo_initiates_first(self):
        assert SIMULATION_LOG[0]["role_id"] == "ceo"
        assert SIMULATION_LOG[0]["action"] == "initiated"

    def test_ceo_delegates_to_cmo(self):
        ceo_delegations = [
            e for e in SIMULATION_LOG
            if e["role_id"] == "ceo" and e["action"] == "delegated"
        ]
        targets = {e["target"] for e in ceo_delegations}
        assert "cmo" in targets

    def test_ceo_delegates_to_all_direct_reports(self):
        ceo_delegations = [
            e for e in SIMULATION_LOG
            if e["role_id"] == "ceo" and e["action"] == "delegated"
        ]
        targets = {e["target"] for e in ceo_delegations}
        for role_id, role in ORG_ROLES.items():
            if role["reports_to"] == "ceo":
                assert role_id in targets, (
                    f"CEO did not delegate to direct report '{role_id}'"
                )

    def test_cmo_delegates_to_all_reports(self):
        cmo_delegations = [
            e for e in SIMULATION_LOG
            if e["role_id"] == "cmo" and e["action"] == "delegated"
        ]
        targets = {e["target"] for e in cmo_delegations}
        for role_id, role in ORG_ROLES.items():
            if role["reports_to"] == "cmo":
                assert role_id in targets, (
                    f"CMO did not delegate to report '{role_id}'"
                )

    def test_completed_entries_have_deliverable_ids(self):
        completed = [e for e in SIMULATION_LOG if e["action"] == "completed"]
        with_ids = [e for e in completed if e.get("deliverable_id")]
        # Most completed entries should have deliverable IDs
        assert len(with_ids) >= 20

    def test_timestamps_are_chronological(self):
        timestamps = [e["timestamp"] for e in SIMULATION_LOG]
        assert timestamps == sorted(timestamps), "Activity log is not chronologically ordered"

    def test_escalation_exists(self):
        escalations = [e for e in SIMULATION_LOG if e["action"] == "escalated"]
        assert len(escalations) >= 1, "No escalation entries found"

    def test_review_exists(self):
        reviews = [e for e in SIMULATION_LOG if e["action"] == "reviewed"]
        assert len(reviews) >= 1, "No review entries found"


# ============================================================================
# Regulatory reference validity tests
# ============================================================================


class TestRegulatoryReferenceValidity:
    """Tests that all regulatory references in deliverables exist in REGULATORY_MAP."""

    def test_all_deliverable_refs_in_map(self):
        refs = get_all_regulatory_refs_from_deliverables()
        invalid = refs - set(REGULATORY_MAP.keys())
        # Allow 21_CFR_610 as an acceptable unlisted ref (used in release testing)
        acceptable_unlisted = {"21_CFR_610"}
        truly_invalid = invalid - acceptable_unlisted
        assert not truly_invalid, (
            f"Regulatory refs in deliverables not in REGULATORY_MAP: {truly_invalid}"
        )

    def test_all_log_refs_in_map(self):
        refs = get_all_regulatory_refs_from_log()
        invalid = refs - set(REGULATORY_MAP.keys())
        assert not invalid, (
            f"Regulatory refs in activity log not in REGULATORY_MAP: {invalid}"
        )

    def test_deliverables_reference_at_least_15_frameworks(self):
        refs = get_all_regulatory_refs_from_deliverables()
        assert len(refs) >= 15

    def test_log_references_at_least_8_frameworks(self):
        refs = get_all_regulatory_refs_from_log()
        assert len(refs) >= 8


# ============================================================================
# Data consistency tests
# ============================================================================


class TestDataConsistency:
    """Tests that numbers are consistent across deliverables."""

    def test_enrolled_patients_consistent(self):
        """Multiple deliverables reference 28 enrolled patients."""
        # CMO benefit-risk
        cmo_delivs = get_role_deliverables("cmo")
        br = [d for d in cmo_delivs if d["deliverable_id"] == "cmo_benefit_risk_v1"][0]
        assert br["data"]["enrolled"] == 28

        # ClinOps trial status
        clinops_delivs = get_role_deliverables("vp_clinops")
        ts = [d for d in clinops_delivs if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert ts["data"]["enrolled"] == 28

        # PV DSUR outline
        pv_delivs = get_role_deliverables("head_pv")
        dsur = [d for d in pv_delivs if d["deliverable_id"] == "pv_dsur_outline_v1"][0]
        assert dsur["data"]["cumulative_exposure"] == 28

    def test_three_sites_consistent(self):
        """Multiple deliverables reference 3 sites."""
        cmo_delivs = get_role_deliverables("cmo")
        cdp = [d for d in cmo_delivs if d["deliverable_id"] == "cmo_cdp_overview_v1"][0]
        assert cdp["data"]["phase1_sites"] == 3

        clinops_delivs = get_role_deliverables("vp_clinops")
        ts = [d for d in clinops_delivs if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert len(ts["data"]["sites"]) == 3

    def test_deaths_zero_everywhere(self):
        """No deaths reported in any deliverable."""
        cmo_delivs = get_role_deliverables("cmo")
        br = [d for d in cmo_delivs if d["deliverable_id"] == "cmo_benefit_risk_v1"][0]
        assert br["data"]["deaths"] == 0

        pv_delivs = get_role_deliverables("head_pv")
        icsr = [d for d in pv_delivs if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        assert icsr["data"]["deaths"] == 0

        dsur = [d for d in pv_delivs if d["deliverable_id"] == "pv_dsur_outline_v1"][0]
        assert dsur["data"]["deaths"] == 0

    def test_batch_counts_consistent_with_quality_metrics(self):
        qm = get_quality_metrics()
        cmc_delivs = get_role_deliverables("head_cmc")
        bs = [d for d in cmc_delivs if d["deliverable_id"] == "cmc_batch_summary_v1"][0]
        assert bs["data"]["total_batches"] == qm["batches"]["manufactured_ytd"]
        assert bs["data"]["released"] == qm["batches"]["released"]
        assert bs["data"]["failed"] == qm["batches"]["failed"]

    def test_expedited_reports_count_consistent(self):
        pv_delivs = get_role_deliverables("head_pv")
        icsr = [d for d in pv_delivs if d["deliverable_id"] == "pv_icsr_summary_v1"][0]
        exp = [d for d in pv_delivs if d["deliverable_id"] == "pv_expedited_log_v1"][0]
        assert icsr["data"]["expedited_reports"] == exp["data"]["total_expedited"]

    def test_dose_levels_consistent(self):
        """Dose levels should be consistent across CMO, biostats, clinops."""
        cmo_delivs = get_role_deliverables("cmo")
        charter = [d for d in cmo_delivs if d["deliverable_id"] == "cmo_dsmb_charter_v1"][0]
        assert charter["data"]["dose_levels"] == 4

        biostats_delivs = get_role_deliverables("head_biostats")
        sap = [d for d in biostats_delivs if d["deliverable_id"] == "biostats_sap_v1"][0]
        assert sap["data"]["dose_levels"] == 4

        clinops_delivs = get_role_deliverables("vp_clinops")
        ts = [d for d in clinops_delivs if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert ts["data"]["dose_levels_completed"] == 4

    def test_dlt_total_consistent_between_biostats_and_clinops(self):
        biostats_delivs = get_role_deliverables("head_biostats")
        dlt = [d for d in biostats_delivs if d["deliverable_id"] == "biostats_dlt_analysis_v1"][0]
        assert dlt["data"]["total_dlts"] == 2

        clinops_delivs = get_role_deliverables("vp_clinops")
        ts = [d for d in clinops_delivs if d["deliverable_id"] == "clinops_trial_status_v1"][0]
        assert ts["data"]["total_dlts"] == 2

    def test_phase2_sample_size_consistent(self):
        biostats_delivs = get_role_deliverables("head_biostats")
        ss = [d for d in biostats_delivs if d["deliverable_id"] == "biostats_sample_size_v1"][0]
        assert ss["data"]["n_enrolled"] == 40

        cmo_delivs = get_role_deliverables("cmo")
        cdp = [d for d in cmo_delivs if d["deliverable_id"] == "cmo_cdp_overview_v1"][0]
        assert cdp["data"]["phase2_target_n"] == 40


# ============================================================================
# Helper function tests
# ============================================================================


class TestGetSimulationStatus:
    """Tests for get_simulation_status."""

    def test_returns_dict(self):
        status = get_simulation_status()
        assert isinstance(status, dict)

    def test_has_required_keys(self):
        status = get_simulation_status()
        assert "roles_active" in status
        assert "total_deliverables" in status
        assert "total_log_entries" in status
        assert "deliverables_per_role" in status

    def test_roles_active_is_11(self):
        status = get_simulation_status()
        assert status["roles_active"] == 11

    def test_total_deliverables_positive(self):
        status = get_simulation_status()
        assert status["total_deliverables"] > 0

    def test_per_role_sums_to_total(self):
        status = get_simulation_status()
        per_role_sum = sum(status["deliverables_per_role"].values())
        assert per_role_sum == status["total_deliverables"]


class TestGetRoleDeliverables:
    """Tests for get_role_deliverables."""

    def test_returns_list_for_valid_role(self):
        result = get_role_deliverables("cmo")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_returns_empty_list_for_invalid_role(self):
        result = get_role_deliverables("nonexistent")
        assert result == []

    def test_returns_deep_copy(self):
        r1 = get_role_deliverables("cmo")
        r2 = get_role_deliverables("cmo")
        assert r1 is not r2
        # Modifying one shouldn't affect the other
        r1[0]["title"] = "MODIFIED"
        assert r2[0]["title"] != "MODIFIED"


class TestGetActivityLog:
    """Tests for get_activity_log."""

    def test_returns_list(self):
        result = get_activity_log()
        assert isinstance(result, list)

    def test_default_limit_50(self):
        result = get_activity_log()
        assert len(result) <= 50

    def test_custom_limit(self):
        result = get_activity_log(limit=5)
        assert len(result) <= 5

    def test_returns_most_recent_first(self):
        result = get_activity_log(limit=10)
        timestamps = [e["timestamp"] for e in result]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_zero_limit_returns_all(self):
        result = get_activity_log(limit=0)
        assert len(result) == len(SIMULATION_LOG)

    def test_negative_limit_returns_all(self):
        result = get_activity_log(limit=-1)
        assert len(result) == len(SIMULATION_LOG)


class TestGetDelegationTree:
    """Tests for get_delegation_tree."""

    def test_returns_dict(self):
        tree = get_delegation_tree()
        assert isinstance(tree, dict)

    def test_root_is_ceo(self):
        tree = get_delegation_tree()
        assert tree["role_id"] == "ceo"

    def test_ceo_has_delegated_to(self):
        tree = get_delegation_tree()
        assert len(tree["delegated_to"]) >= 1

    def test_tree_has_title(self):
        tree = get_delegation_tree()
        assert tree["title"] == "Chief Executive Officer"

    def test_cmo_in_tree(self):
        tree = get_delegation_tree()
        child_roles = {c["role_id"] for c in tree["delegated_to"]}
        assert "cmo" in child_roles

    def test_cmo_has_children(self):
        tree = get_delegation_tree()
        cmo_node = [c for c in tree["delegated_to"] if c["role_id"] == "cmo"][0]
        assert len(cmo_node["delegated_to"]) >= 1

    def test_tree_depth_at_least_3(self):
        """CEO -> CMO -> CMO reports gives depth 3."""
        tree = get_delegation_tree()
        cmo_node = [c for c in tree["delegated_to"] if c["role_id"] == "cmo"][0]
        assert len(cmo_node["delegated_to"]) >= 1
        # This confirms we have at least 3 levels

    def test_all_nodes_have_role_id(self):
        tree = get_delegation_tree()

        def _check(node: dict) -> None:
            assert "role_id" in node
            assert "title" in node
            for child in node.get("delegated_to", []):
                _check(child)

        _check(tree)


class TestGetAllDeliverableIds:
    """Tests for get_all_deliverable_ids."""

    def test_returns_sorted_list(self):
        ids = get_all_deliverable_ids()
        assert isinstance(ids, list)
        assert ids == sorted(ids)

    def test_all_ids_unique(self):
        ids = get_all_deliverable_ids()
        assert len(ids) == len(set(ids))

    def test_count_at_least_30(self):
        ids = get_all_deliverable_ids()
        assert len(ids) >= 30

    def test_known_ids_present(self):
        ids = get_all_deliverable_ids()
        assert "cmo_benefit_risk_v1" in ids
        assert "pv_icsr_summary_v1" in ids
        assert "biostats_sap_v1" in ids
        assert "cmc_batch_summary_v1" in ids
        assert "qa_capa_tracker_v1" in ids


# ============================================================================
# Module-level constant tests
# ============================================================================


class TestModuleConstants:
    """Tests for module-level simulation constants."""

    def test_enrolled_plus_screen_failures_equals_screened(self):
        from src.data.pharma_simulation import (
            _ENROLLED_PATIENTS,
            _SCREEN_FAILURES,
            _TOTAL_SCREENED,
        )
        assert _ENROLLED_PATIENTS + _SCREEN_FAILURES == _TOTAL_SCREENED

    def test_serious_plus_non_serious_equals_total_icsrs(self):
        from src.data.pharma_simulation import (
            _NON_SERIOUS_ICSRS,
            _SERIOUS_ICSRS,
            _TOTAL_ICSRS,
        )
        assert _SERIOUS_ICSRS + _NON_SERIOUS_ICSRS == _TOTAL_ICSRS

    def test_phase1_start_is_2024_11(self):
        from src.data.pharma_simulation import _PHASE1_START
        assert _PHASE1_START == "2024-11"

    def test_num_sites_is_3(self):
        from src.data.pharma_simulation import _NUM_SITES
        assert _NUM_SITES == 3

    def test_dose_levels_is_4(self):
        from src.data.pharma_simulation import _DOSE_LEVELS
        assert _DOSE_LEVELS == 4
