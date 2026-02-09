"""Unit tests for the cross-source signal triangulation module."""

import math

import pytest

from src.models.signal_triangulation import (
    triangulate_signals,
    _compute_divergence,
    _compute_weighted_trial_rate,
    _METHODOLOGY,
    _CAVEATS,
)


# ===========================================================================
# triangulate_signals() — structure & content
# ===========================================================================

class TestTriangulateSignalsStructure:
    """Verify the top-level return structure of triangulate_signals()."""

    def test_returns_dict(self):
        result = triangulate_signals()
        assert isinstance(result, dict)

    def test_has_signals_key(self):
        result = triangulate_signals()
        assert "signals" in result

    def test_signals_is_list(self):
        result = triangulate_signals()
        assert isinstance(result["signals"], list)

    def test_has_summary_key(self):
        result = triangulate_signals()
        assert "summary" in result

    def test_has_methodology_key(self):
        result = triangulate_signals()
        assert "methodology" in result

    def test_methodology_is_nonempty_string(self):
        result = triangulate_signals()
        assert isinstance(result["methodology"], str)
        assert len(result["methodology"]) > 50

    def test_has_caveats_key(self):
        result = triangulate_signals()
        assert "caveats" in result

    def test_caveats_is_list(self):
        result = triangulate_signals()
        assert isinstance(result["caveats"], list)
        assert len(result["caveats"]) >= 3

    def test_signals_have_expected_fields(self):
        result = triangulate_signals()
        if result["signals"]:
            s = result["signals"][0]
            expected_fields = [
                "ae_type", "product", "faers_rate_pct", "trial_rate_pct",
                "divergence_pct", "direction", "flag", "confidence_level",
            ]
            for field in expected_fields:
                assert field in s, f"Missing field: {field}"


class TestTriangulateSignalsSummary:
    """Verify summary counts are consistent with signals."""

    def test_summary_has_total_signals(self):
        result = triangulate_signals()
        assert "total_signals" in result["summary"]

    def test_summary_total_matches_signal_count(self):
        result = triangulate_signals()
        assert result["summary"]["total_signals"] == len(result["signals"])

    def test_summary_has_flagged_count(self):
        result = triangulate_signals()
        assert "flagged_count" in result["summary"]

    def test_summary_has_ae_types_analyzed(self):
        result = triangulate_signals()
        assert "ae_types_analyzed" in result["summary"]
        assert isinstance(result["summary"]["ae_types_analyzed"], list)

    def test_flag_counts_sum_to_total(self):
        result = triangulate_signals()
        summary = result["summary"]
        total = (
            summary.get("significant_count", 0)
            + summary.get("moderate_count", 0)
            + summary.get("aligned_count", 0)
        )
        assert total == summary["total_signals"]

    def test_flagged_count_excludes_aligned(self):
        result = triangulate_signals()
        summary = result["summary"]
        flagged = summary.get("significant_count", 0) + summary.get("moderate_count", 0)
        assert summary["flagged_count"] == flagged

    def test_produces_signals_for_all_mapped_ae_types(self):
        result = triangulate_signals()
        ae_types = result["summary"]["ae_types_analyzed"]
        assert "crs" in ae_types
        assert "icans" in ae_types
        assert "infections" in ae_types
        assert "cytopenias" in ae_types


# ===========================================================================
# ae_type filter
# ===========================================================================

class TestTriangulateSignalsFilter:
    """Verify ae_type filtering works correctly."""

    def test_filter_crs_only(self):
        result = triangulate_signals(ae_type="crs")
        for s in result["signals"]:
            assert s["ae_type"] == "crs"

    def test_filter_icans_only(self):
        result = triangulate_signals(ae_type="icans")
        for s in result["signals"]:
            assert s["ae_type"] == "icans"

    def test_filter_infections_only(self):
        result = triangulate_signals(ae_type="infections")
        for s in result["signals"]:
            assert s["ae_type"] == "infections"

    def test_filter_cytopenias_only(self):
        result = triangulate_signals(ae_type="cytopenias")
        for s in result["signals"]:
            assert s["ae_type"] == "cytopenias"

    def test_filter_reduces_signal_count(self):
        all_result = triangulate_signals()
        crs_result = triangulate_signals(ae_type="crs")
        assert len(crs_result["signals"]) < len(all_result["signals"])

    def test_filter_invalid_ae_type_returns_empty(self):
        result = triangulate_signals(ae_type="nonexistent")
        assert result["signals"] == []
        assert result["summary"]["total_signals"] == 0

    def test_filter_case_insensitive(self):
        result = triangulate_signals(ae_type="CRS")
        assert len(result["signals"]) > 0
        for s in result["signals"]:
            assert s["ae_type"] == "crs"

    def test_filter_whitespace_trimmed(self):
        result = triangulate_signals(ae_type="  crs  ")
        assert len(result["signals"]) > 0


# ===========================================================================
# Divergence calculation
# ===========================================================================

class TestDivergenceCalculation:
    """Verify divergence computation logic."""

    def test_identical_rates_give_zero_divergence(self):
        div = _compute_divergence(50.0, 50.0)
        assert div["divergence_pct"] == 0.0
        assert div["direction"] == "aligned"
        assert div["flag"] == "aligned"

    def test_faers_higher_gives_positive_divergence(self):
        div = _compute_divergence(60.0, 40.0)
        assert div["divergence_pct"] == 50.0
        assert div["direction"] == "faers_higher"

    def test_trial_higher_gives_negative_divergence(self):
        div = _compute_divergence(30.0, 40.0)
        assert div["divergence_pct"] == -25.0
        assert div["direction"] == "trial_higher"

    def test_aligned_flag_below_25pct(self):
        div = _compute_divergence(42.0, 40.0)  # 5% divergence
        assert div["flag"] == "aligned"

    def test_moderate_flag_between_25_and_75pct(self):
        div = _compute_divergence(60.0, 40.0)  # 50% divergence
        assert div["flag"] == "moderate"

    def test_significant_flag_above_75pct(self):
        div = _compute_divergence(100.0, 40.0)  # 150% divergence
        assert div["flag"] == "significant"

    def test_zero_trial_rate_with_positive_faers(self):
        div = _compute_divergence(10.0, 0.0)
        assert div["divergence_pct"] == float("inf")
        assert div["flag"] == "significant"
        assert div["direction"] == "faers_higher"

    def test_zero_both_rates(self):
        div = _compute_divergence(0.0, 0.0)
        assert div["divergence_pct"] == 0.0
        assert div["flag"] == "aligned"

    def test_negative_divergence_moderate(self):
        div = _compute_divergence(20.0, 40.0)  # -50%
        assert div["flag"] == "moderate"

    def test_negative_divergence_significant(self):
        div = _compute_divergence(5.0, 40.0)  # -87.5%
        assert div["flag"] == "significant"


# ===========================================================================
# Weighted trial rate computation
# ===========================================================================

class TestWeightedTrialRate:
    """Verify enrollment-weighted mean computation."""

    def test_single_trial(self):
        trials = [{"enrollment": 100, "ae_rates": {"crs": {"rate_pct": 20.0, "at_risk": 100, "affected": 20}}}]
        result = _compute_weighted_trial_rate(trials, "crs")
        assert result["weighted_rate_pct"] == 20.0
        assert result["total_enrollment"] == 100
        assert result["trials_with_data"] == 1

    def test_weighted_average_two_trials(self):
        trials = [
            {"enrollment": 100, "ae_rates": {"crs": {"rate_pct": 10.0, "at_risk": 100, "affected": 10}}},
            {"enrollment": 200, "ae_rates": {"crs": {"rate_pct": 40.0, "at_risk": 200, "affected": 80}}},
        ]
        result = _compute_weighted_trial_rate(trials, "crs")
        # (10*100 + 40*200) / 300 = 9000/300 = 30.0
        assert result["weighted_rate_pct"] == 30.0
        assert result["total_enrollment"] == 300
        assert result["trials_with_data"] == 2

    def test_zero_enrollment_trial_excluded(self):
        trials = [
            {"enrollment": 0, "ae_rates": {"crs": {"rate_pct": 50.0, "at_risk": 0, "affected": 0}}},
            {"enrollment": 100, "ae_rates": {"crs": {"rate_pct": 20.0, "at_risk": 100, "affected": 20}}},
        ]
        result = _compute_weighted_trial_rate(trials, "crs")
        assert result["weighted_rate_pct"] == 20.0
        assert result["total_enrollment"] == 100

    def test_no_matching_ae_type(self):
        trials = [{"enrollment": 100, "ae_rates": {"crs": {"rate_pct": 20.0, "at_risk": 100, "affected": 20}}}]
        result = _compute_weighted_trial_rate(trials, "nonexistent")
        assert result["weighted_rate_pct"] == 0.0
        assert result["trials_with_data"] == 0

    def test_empty_trials(self):
        result = _compute_weighted_trial_rate([], "crs")
        assert result["weighted_rate_pct"] == 0.0
        assert result["total_enrollment"] == 0

    def test_trial_with_zero_at_risk_excluded(self):
        trials = [
            {"enrollment": 100, "ae_rates": {"crs": {"rate_pct": 0.0, "at_risk": 0, "affected": 0}}},
        ]
        result = _compute_weighted_trial_rate(trials, "crs")
        assert result["trials_with_data"] == 0


# ===========================================================================
# Signal content validation (against real data)
# ===========================================================================

class TestTriangulateSignalsContent:
    """Validate signal data against known FAERS/CT.gov data."""

    def test_signals_have_positive_faers_rates(self):
        result = triangulate_signals()
        has_positive = any(s["faers_rate_pct"] > 0 for s in result["signals"])
        assert has_positive

    def test_signals_have_trial_rate(self):
        result = triangulate_signals()
        has_trial = any(s["trial_rate_pct"] > 0 for s in result["signals"])
        assert has_trial

    def test_known_products_appear(self):
        result = triangulate_signals()
        products = {s["product"] for s in result["signals"]}
        assert "Yescarta" in products
        assert "Kymriah" in products

    def test_confidence_levels_are_valid(self):
        result = triangulate_signals()
        valid_levels = {"high", "moderate", "low"}
        for s in result["signals"]:
            assert s["confidence_level"] in valid_levels

    def test_flags_are_valid(self):
        result = triangulate_signals()
        valid_flags = {"aligned", "moderate", "significant"}
        for s in result["signals"]:
            assert s["flag"] in valid_flags

    def test_directions_are_valid(self):
        result = triangulate_signals()
        valid_directions = {"faers_higher", "trial_higher", "aligned"}
        for s in result["signals"]:
            assert s["direction"] in valid_directions

    def test_ae_labels_present(self):
        result = triangulate_signals()
        for s in result["signals"]:
            assert "ae_label" in s
            assert len(s["ae_label"]) > 0

    def test_faers_count_nonnegative(self):
        result = triangulate_signals()
        for s in result["signals"]:
            assert s["faers_count"] >= 0

    def test_methodology_matches_module_constant(self):
        result = triangulate_signals()
        assert result["methodology"] == _METHODOLOGY

    def test_caveats_match_module_constant(self):
        result = triangulate_signals()
        assert result["caveats"] == _CAVEATS
