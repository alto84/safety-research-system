"""
Unit tests for src/data/ctgov_cache.py

Tests the CT.gov AE data loader, AE term normalization, trial summary
computation, and filtering by AE type.
"""

import pytest

from src.data.ctgov_cache import (
    AE_TERM_MAP,
    normalize_ae_term,
    get_summary,
    get_trial_summaries,
    get_trial_ae_rates,
)


# ============================================================================
# AE_TERM_MAP
# ============================================================================


class TestAETermMap:
    """Tests for the AE term mapping constants."""

    def test_has_crs_category(self):
        assert "crs" in AE_TERM_MAP

    def test_has_icans_category(self):
        assert "icans" in AE_TERM_MAP

    def test_has_cytopenias_category(self):
        assert "cytopenias" in AE_TERM_MAP

    def test_has_infections_category(self):
        assert "infections" in AE_TERM_MAP

    def test_has_hlh_category(self):
        assert "hlh" in AE_TERM_MAP

    def test_all_categories_have_patterns(self):
        for cat, patterns in AE_TERM_MAP.items():
            assert len(patterns) > 0, f"Category '{cat}' has no patterns"

    def test_all_patterns_are_lowercase(self):
        for cat, patterns in AE_TERM_MAP.items():
            for p in patterns:
                assert p == p.lower(), f"Pattern '{p}' in '{cat}' is not lowercase"


# ============================================================================
# normalize_ae_term
# ============================================================================


class TestNormalizeAETerm:
    """Tests for normalize_ae_term()."""

    def test_crs_exact_match(self):
        assert normalize_ae_term("Cytokine Release Syndrome") == "crs"

    def test_crs_lowercase(self):
        assert normalize_ae_term("cytokine release syndrome") == "crs"

    def test_crs_abbreviation(self):
        assert normalize_ae_term("CRS") == "crs"

    def test_cytokine_storm(self):
        assert normalize_ae_term("Cytokine Storm") == "crs"

    def test_icans_neurotoxicity(self):
        assert normalize_ae_term("Neurotoxicity") == "icans"

    def test_icans_encephalopathy(self):
        assert normalize_ae_term("Encephalopathy") == "icans"

    def test_icans_aphasia(self):
        assert normalize_ae_term("Aphasia") == "icans"

    def test_icans_confused_state(self):
        assert normalize_ae_term("Confused state") == "icans"

    def test_cytopenias_neutropenia(self):
        assert normalize_ae_term("Neutropenia") == "cytopenias"

    def test_cytopenias_thrombocytopenia(self):
        assert normalize_ae_term("Thrombocytopenia") == "cytopenias"

    def test_cytopenias_anemia(self):
        assert normalize_ae_term("Anemia") == "cytopenias"

    def test_cytopenias_febrile_neutropenia(self):
        assert normalize_ae_term("Febrile neutropenia") == "cytopenias"

    def test_infections_pneumonia(self):
        assert normalize_ae_term("Pneumonia") == "infections"

    def test_infections_sepsis(self):
        assert normalize_ae_term("Sepsis") == "infections"

    def test_infections_general(self):
        assert normalize_ae_term("Infection") == "infections"

    def test_hlh_full_name(self):
        assert normalize_ae_term("Hemophagocytic lymphohistiocytosis") == "hlh"

    def test_hlh_abbreviation(self):
        assert normalize_ae_term("HLH") == "hlh"

    def test_hlh_mas(self):
        assert normalize_ae_term("Macrophage Activation Syndrome") == "hlh"

    def test_unknown_term_returns_none(self):
        assert normalize_ae_term("Headache") is None

    def test_empty_string_returns_none(self):
        assert normalize_ae_term("") is None

    def test_whitespace_handling(self):
        assert normalize_ae_term("  Neutropenia  ") == "cytopenias"

    def test_case_insensitive(self):
        assert normalize_ae_term("CYTOKINE RELEASE SYNDROME") == "crs"

    def test_substring_match(self):
        """Substring matching should work for terms containing a pattern."""
        assert normalize_ae_term("Severe cytokine release syndrome grade 4") == "crs"


# ============================================================================
# get_summary
# ============================================================================


class TestGetSummary:
    """Tests for get_summary()."""

    def test_returns_dict(self):
        result = get_summary()
        assert isinstance(result, dict)

    def test_has_total_trials(self):
        result = get_summary()
        assert "total_trials_with_ae_data" in result

    def test_total_trials_is_47(self):
        result = get_summary()
        assert result["total_trials_with_ae_data"] == 47

    def test_has_serious_event_types(self):
        result = get_summary()
        assert "unique_serious_event_types" in result
        assert result["unique_serious_event_types"] > 0

    def test_has_other_event_types(self):
        result = get_summary()
        assert "unique_other_event_types" in result
        assert result["unique_other_event_types"] > 0


# ============================================================================
# get_trial_summaries
# ============================================================================


class TestGetTrialSummaries:
    """Tests for get_trial_summaries()."""

    def test_returns_list(self):
        result = get_trial_summaries()
        assert isinstance(result, list)

    def test_returns_47_trials(self):
        result = get_trial_summaries()
        assert len(result) == 47

    def test_each_trial_has_nct_id(self):
        for trial in get_trial_summaries():
            assert "nct_id" in trial
            assert trial["nct_id"].startswith("NCT")

    def test_each_trial_has_title(self):
        for trial in get_trial_summaries():
            assert "title" in trial
            assert len(trial["title"]) > 0

    def test_each_trial_has_phase(self):
        for trial in get_trial_summaries():
            assert "phase" in trial

    def test_each_trial_has_enrollment(self):
        for trial in get_trial_summaries():
            assert "enrollment" in trial
            assert isinstance(trial["enrollment"], int)

    def test_each_trial_has_ae_rates(self):
        for trial in get_trial_summaries():
            assert "ae_rates" in trial
            rates = trial["ae_rates"]
            for cat in AE_TERM_MAP:
                assert cat in rates, f"Missing AE category '{cat}' in trial {trial['nct_id']}"

    def test_ae_rates_have_required_fields(self):
        for trial in get_trial_summaries():
            for cat, rate_info in trial["ae_rates"].items():
                assert "affected" in rate_info
                assert "at_risk" in rate_info
                assert "rate_pct" in rate_info

    def test_ae_rates_non_negative(self):
        for trial in get_trial_summaries():
            for cat, rate_info in trial["ae_rates"].items():
                assert rate_info["affected"] >= 0
                assert rate_info["at_risk"] >= 0
                assert rate_info["rate_pct"] >= 0.0

    def test_ae_rate_pct_within_range(self):
        for trial in get_trial_summaries():
            for cat, rate_info in trial["ae_rates"].items():
                assert rate_info["rate_pct"] <= 100.0, (
                    f"Rate {rate_info['rate_pct']}% exceeds 100% for "
                    f"{cat} in {trial['nct_id']}"
                )

    def test_min_enrollment_filter(self):
        all_trials = get_trial_summaries()
        filtered = get_trial_summaries(min_enrollment=50)
        assert len(filtered) <= len(all_trials)
        for t in filtered:
            assert t["enrollment"] >= 50

    def test_min_enrollment_zero_returns_all(self):
        assert len(get_trial_summaries(min_enrollment=0)) == 47

    def test_min_enrollment_very_large_returns_empty(self):
        result = get_trial_summaries(min_enrollment=100000)
        assert len(result) == 0

    def test_nct_ids_are_unique(self):
        ids = [t["nct_id"] for t in get_trial_summaries()]
        assert len(ids) == len(set(ids))

    def test_known_trial_exists(self):
        """NCT05032820 should be in the dataset."""
        ids = [t["nct_id"] for t in get_trial_summaries()]
        assert "NCT05032820" in ids

    def test_known_trial_has_crs(self):
        """NCT05032820 should have CRS data (5 affected out of 40)."""
        trials = get_trial_summaries()
        trial = next(t for t in trials if t["nct_id"] == "NCT05032820")
        crs = trial["ae_rates"]["crs"]
        assert crs["affected"] == 5
        assert crs["at_risk"] == 40
        assert crs["rate_pct"] == 12.5


# ============================================================================
# get_trial_ae_rates
# ============================================================================


class TestGetTrialAERates:
    """Tests for get_trial_ae_rates()."""

    def test_returns_list(self):
        result = get_trial_ae_rates("crs")
        assert isinstance(result, list)

    def test_crs_returns_results(self):
        result = get_trial_ae_rates("crs")
        assert len(result) > 0

    def test_icans_returns_results(self):
        result = get_trial_ae_rates("icans")
        assert len(result) > 0

    def test_cytopenias_returns_results(self):
        result = get_trial_ae_rates("cytopenias")
        assert len(result) > 0

    def test_each_entry_has_ae_type(self):
        for entry in get_trial_ae_rates("crs"):
            assert entry["ae_type"] == "crs"

    def test_each_entry_has_nct_id(self):
        for entry in get_trial_ae_rates("crs"):
            assert "nct_id" in entry
            assert entry["nct_id"].startswith("NCT")

    def test_each_entry_has_rate_fields(self):
        for entry in get_trial_ae_rates("crs"):
            assert "affected" in entry
            assert "at_risk" in entry
            assert "rate_pct" in entry

    def test_invalid_ae_type_returns_empty(self):
        assert get_trial_ae_rates("nonexistent") == []

    def test_case_insensitive_ae_type(self):
        upper = get_trial_ae_rates("CRS")
        lower = get_trial_ae_rates("crs")
        assert len(upper) == len(lower)

    def test_min_enrollment_filter(self):
        all_rates = get_trial_ae_rates("crs")
        filtered = get_trial_ae_rates("crs", min_enrollment=50)
        assert len(filtered) <= len(all_rates)
        for entry in filtered:
            assert entry["enrollment"] >= 50

    def test_infections_returns_results(self):
        result = get_trial_ae_rates("infections")
        assert len(result) > 0

    def test_hlh_category(self):
        result = get_trial_ae_rates("hlh")
        assert isinstance(result, list)
