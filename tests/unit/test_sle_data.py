"""
Unit tests for data/sle_cart_studies.py

Tests the clinical data constants, utility functions, and data integrity
of the curated SLE CAR-T and oncology comparator datasets.
"""

import pytest

from data.sle_cart_studies import (
    ADVERSE_EVENT_RATES,
    CLINICAL_TRIALS,
    DATA_SOURCES,
    get_comparison_chart_data,
    get_sle_baseline_risk,
    get_trial_summary,
)


# ============================================================================
# ADVERSE_EVENT_RATES
# ============================================================================


class TestAdverseEventRates:
    """Tests for the adverse event rate data."""

    def test_contains_sle_entries(self):
        """There should be SLE entries in the dataset."""
        sle = [ae for ae in ADVERSE_EVENT_RATES if ae.indication == "SLE"]
        assert len(sle) > 0

    def test_contains_oncology_entries(self):
        """There should be oncology comparator entries (DLBCL, ALL, MM)."""
        oncology_indications = {"DLBCL", "ALL", "MM"}
        oncology = [
            ae for ae in ADVERSE_EVENT_RATES
            if ae.indication in oncology_indications
        ]
        assert len(oncology) > 0

    @pytest.mark.parametrize(
        "idx", range(len(ADVERSE_EVENT_RATES)),
        ids=[ae.trial for ae in ADVERSE_EVENT_RATES],
    )
    def test_n_patients_positive(self, idx):
        """Every entry should have n_patients > 0."""
        assert ADVERSE_EVENT_RATES[idx].n_patients > 0

    @pytest.mark.parametrize(
        "idx", range(len(ADVERSE_EVENT_RATES)),
        ids=[ae.trial for ae in ADVERSE_EVENT_RATES],
    )
    def test_rates_between_0_and_100(self, idx):
        """CRS and ICANS rates (any grade and grade 3+) should be in [0, 100]."""
        ae = ADVERSE_EVENT_RATES[idx]
        for rate_name in ("crs_any_grade", "crs_grade3_plus",
                          "icans_any_grade", "icans_grade3_plus"):
            rate = getattr(ae, rate_name)
            assert 0.0 <= rate <= 100.0, (
                f"{ae.trial}: {rate_name}={rate} out of [0, 100]"
            )

    def test_grade3_plus_does_not_exceed_any_grade(self):
        """Grade 3+ rate should not exceed the any-grade rate for the same AE."""
        for ae in ADVERSE_EVENT_RATES:
            assert ae.crs_grade3_plus <= ae.crs_any_grade + 0.01, (
                f"{ae.trial}: CRS grade 3+ ({ae.crs_grade3_plus}) > "
                f"any grade ({ae.crs_any_grade})"
            )
            assert ae.icans_grade3_plus <= ae.icans_any_grade + 0.01, (
                f"{ae.trial}: ICANS grade 3+ ({ae.icans_grade3_plus}) > "
                f"any grade ({ae.icans_any_grade})"
            )

    def test_contains_expected_oncology_trials(self):
        """Should contain all major pivotal oncology comparator trials."""
        trial_names = {ae.trial for ae in ADVERSE_EVENT_RATES}
        expected = {"ZUMA-1", "JULIET", "TRANSCEND", "ELIANA", "KarMMa", "CARTITUDE-1"}
        assert expected.issubset(trial_names)

    def test_all_have_indication(self):
        """Every entry must have a non-empty indication field."""
        for ae in ADVERSE_EVENT_RATES:
            assert isinstance(ae.indication, str) and len(ae.indication) > 0


# ============================================================================
# CLINICAL_TRIALS
# ============================================================================


class TestClinicalTrials:
    """Tests for the clinical trial registry data."""

    def test_contains_autoimmune_trials(self):
        """Should contain autoimmune indication trials (SLE, Myositis, etc.)."""
        autoimmune_keywords = {"SLE", "Myositis", "Lupus", "SSc", "NMOSD"}
        ai_trials = [
            t for t in CLINICAL_TRIALS
            if any(kw in t.indication for kw in autoimmune_keywords)
        ]
        assert len(ai_trials) > 0

    def test_contains_oncology_trials(self):
        """Should contain oncology trials (DLBCL, ALL, MM)."""
        onc_indications = {"DLBCL", "ALL", "MM"}
        onc_trials = [
            t for t in CLINICAL_TRIALS
            if t.indication in onc_indications
        ]
        assert len(onc_trials) > 0

    @pytest.mark.parametrize(
        "idx", range(len(CLINICAL_TRIALS)),
        ids=[t.name for t in CLINICAL_TRIALS],
    )
    def test_has_nct_id_or_placeholder(self, idx):
        """Every trial should have an NCT ID (or a non-empty placeholder)."""
        trial = CLINICAL_TRIALS[idx]
        assert isinstance(trial.nct_id, str) and len(trial.nct_id) > 0

    @pytest.mark.parametrize(
        "idx", range(len(CLINICAL_TRIALS)),
        ids=[t.name for t in CLINICAL_TRIALS],
    )
    def test_enrollment_positive(self, idx):
        """Enrollment should be > 0 for all trials."""
        assert CLINICAL_TRIALS[idx].enrollment > 0

    def test_all_nct_ids_start_with_nct(self):
        """All NCT IDs should follow the NCTxxxxxxxx format."""
        for trial in CLINICAL_TRIALS:
            assert trial.nct_id.startswith("NCT"), (
                f"Trial {trial.name} has non-NCT id: {trial.nct_id}"
            )

    def test_valid_statuses(self):
        """All trials should have a recognized status."""
        valid_statuses = {"Recruiting", "Active", "Completed", "Not yet recruiting"}
        for trial in CLINICAL_TRIALS:
            assert trial.status in valid_statuses, (
                f"Trial {trial.name} has unknown status: {trial.status}"
            )

    def test_all_have_nonempty_name(self):
        for trial in CLINICAL_TRIALS:
            assert isinstance(trial.name, str) and len(trial.name) > 0


# ============================================================================
# DATA_SOURCES
# ============================================================================


class TestDataSources:
    """Tests for the data source inventory."""

    def test_8_data_sources(self):
        assert len(DATA_SOURCES) == 8

    @pytest.mark.parametrize(
        "idx", range(len(DATA_SOURCES)),
        ids=[ds.name for ds in DATA_SOURCES],
    )
    def test_required_fields_present(self, idx):
        """Each data source must have name, type, coverage, cart_data_available,
        autoimmune_cart_data, and access_method."""
        ds = DATA_SOURCES[idx]
        assert isinstance(ds.name, str) and len(ds.name) > 0
        assert isinstance(ds.type, str) and len(ds.type) > 0
        assert isinstance(ds.coverage, str) and len(ds.coverage) > 0
        assert isinstance(ds.cart_data_available, bool)
        assert isinstance(ds.autoimmune_cart_data, bool)
        assert isinstance(ds.access_method, str) and len(ds.access_method) > 0

    def test_all_have_strengths_and_limitations(self):
        """Every data source should have at least one strength and one limitation."""
        for ds in DATA_SOURCES:
            assert len(ds.strengths) > 0, f"{ds.name} has no strengths"
            assert len(ds.limitations) > 0, f"{ds.name} has no limitations"

    def test_all_have_cart_data(self):
        """All 8 curated data sources should have CAR-T data available."""
        for ds in DATA_SOURCES:
            assert ds.cart_data_available is True, (
                f"{ds.name} does not have CAR-T data available"
            )

    def test_known_types(self):
        """Data source types should be from the expected set."""
        valid_types = {"Literature", "Spontaneous Reporting", "Registry", "RWD"}
        for ds in DATA_SOURCES:
            assert ds.type in valid_types, (
                f"{ds.name} has unexpected type: {ds.type}"
            )


# ============================================================================
# get_sle_baseline_risk()
# ============================================================================


class TestGetSLEBaselineRisk:
    """Tests for the baseline risk estimation function."""

    def test_returns_expected_keys(self):
        """Result should contain risk estimates for all tracked AE types."""
        result = get_sle_baseline_risk()
        required_keys = {"crs_grade3_plus", "icans_grade3_plus", "icahs", "licats"}
        assert required_keys.issubset(set(result.keys()))
        extended_keys = {"crs_any", "icans_any", "infection", "cytopenias"}
        assert extended_keys.issubset(set(result.keys()))

    def test_all_estimates_non_negative(self):
        """All point estimates should be >= 0."""
        result = get_sle_baseline_risk()
        for key, entry in result.items():
            assert entry["estimate"] >= 0.0, f"{key} estimate is negative"

    def test_ci_low_le_high(self):
        """CI lower bound should be <= upper bound for every entry."""
        result = get_sle_baseline_risk()
        for key, entry in result.items():
            ci = entry["ci95"]
            assert ci[0] <= ci[1], f"{key}: CI low ({ci[0]}) > CI high ({ci[1]})"

    def test_ci_values_are_non_negative(self):
        """CI bounds should be >= 0."""
        result = get_sle_baseline_risk()
        for key, entry in result.items():
            assert entry["ci95"][0] >= 0.0
            assert entry["ci95"][1] >= 0.0

    def test_crs_estimate_is_2_1(self):
        """CRS grade 3+ point estimate from the pooled analysis is 2.1%."""
        result = get_sle_baseline_risk()
        assert result["crs_grade3_plus"]["estimate"] == pytest.approx(2.1)

    def test_zero_event_rates_have_rule_of_3_upper_bound(self):
        """For zero-event rates, the upper bound should reflect rule-of-3."""
        result = get_sle_baseline_risk()
        # ICANS, ICAHS, LICATS all have 0 events
        for key in ("icans_grade3_plus", "icahs", "licats"):
            assert result[key]["estimate"] == 0.0
            assert result[key]["ci95"][1] > 0.0  # upper bound is positive


# ============================================================================
# get_trial_summary()
# ============================================================================


class TestGetTrialSummary:
    """Tests for the trial count summary function."""

    def test_total_equals_sum_of_status_counts(self):
        """Total should equal the sum of all status categories."""
        summary = get_trial_summary()
        counted = (
            summary["recruiting"]
            + summary["active"]
            + summary["completed"]
            + summary["not_yet_recruiting"]
        )
        assert summary["total"] == counted

    def test_all_counts_non_negative(self):
        summary = get_trial_summary()
        for key, value in summary.items():
            assert value >= 0, f"{key} is negative: {value}"

    def test_total_matches_clinical_trials_length(self):
        """Total should match the actual number of clinical trials."""
        summary = get_trial_summary()
        assert summary["total"] == len(CLINICAL_TRIALS)

    def test_has_expected_keys(self):
        summary = get_trial_summary()
        expected = {"recruiting", "active", "completed", "not_yet_recruiting", "total"}
        assert set(summary.keys()) == expected


# ============================================================================
# get_comparison_chart_data()
# ============================================================================


class TestGetComparisonChartData:
    """Tests for the cross-indication comparison data function."""

    def test_returns_list_of_dicts(self):
        data = get_comparison_chart_data()
        assert isinstance(data, list)
        assert len(data) > 0
        for item in data:
            assert isinstance(item, dict)

    def test_has_autoimmune_and_oncology_categories(self):
        """The chart data should contain both Autoimmune and Oncology entries."""
        data = get_comparison_chart_data()
        categories = {item["category"] for item in data}
        assert "Autoimmune" in categories
        assert "Oncology" in categories

    def test_expected_fields_in_each_entry(self):
        """Each entry should have the required chart fields."""
        required = {
            "label", "indication", "product", "crs_any_grade",
            "crs_grade3_plus", "icans_any_grade", "icans_grade3_plus",
            "n_patients", "category",
        }
        data = get_comparison_chart_data()
        for item in data:
            assert required.issubset(set(item.keys())), (
                f"Missing fields in {item.get('label', '?')}: "
                f"{required - set(item.keys())}"
            )

    def test_includes_sle_pooled(self):
        """The SLE pooled analysis should be present."""
        data = get_comparison_chart_data()
        labels = [item["label"] for item in data]
        assert any("SLE" in label for label in labels)

    def test_includes_oncology_pivotal_trials(self):
        """Key oncology pivotal trials should be represented."""
        data = get_comparison_chart_data()
        labels_str = " ".join(item["label"] for item in data)
        # Check that DLBCL, ALL, MM indications are present
        indications = {item["indication"] for item in data}
        assert "DLBCL" in indications
        assert "ALL" in indications
        assert "MM" in indications

    def test_n_patients_positive_in_chart_data(self):
        """All chart entries should have positive patient counts."""
        data = get_comparison_chart_data()
        for item in data:
            assert item["n_patients"] > 0

    def test_rates_are_numeric(self):
        """All rate fields should be numeric (int or float)."""
        data = get_comparison_chart_data()
        rate_fields = [
            "crs_any_grade", "crs_grade3_plus",
            "icans_any_grade", "icans_grade3_plus",
        ]
        for item in data:
            for field in rate_fields:
                assert isinstance(item[field], (int, float)), (
                    f"{item['label']}: {field} is {type(item[field])}"
                )
