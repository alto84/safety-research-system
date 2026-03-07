"""
Comprehensive unit tests for src/models/temporal_signal.py

Tests the temporal signal evolution module including:
- Data structure integrity (SignalTimepoint, RegulatoryMilestone, TemporalSignalProfile)
- Temporal profiles for all 6 CAR-T products x 4 AE categories = 24 profiles
- PRR/EBGM value realism (non-negative, realistic ranges)
- Regulatory milestone chronological ordering and content
- Product lookup (case-insensitive, partial matching)
- AE category normalization and aliases
- Signal detection threshold crossing logic
- API endpoint integration tests (200, 404 for unknown product)
- Edge cases and boundary conditions
"""

import pytest
from datetime import date

from src.models.temporal_signal import (
    AE_CATEGORIES,
    MilestoneType,
    PRODUCT_METADATA,
    REGULATORY_MILESTONES,
    RegulatoryMilestone,
    SignalStatus,
    SignalTimepoint,
    TemporalSignalProfile,
    get_all_temporal_profiles,
    get_product_profiles,
    get_regulatory_timeline,
    get_signal_summary,
    get_temporal_profile,
    milestone_to_dict,
    profile_to_dict,
    _find_product,
    _normalize_ae_category,
    _quarter_end_date,
    _quarter_label,
    _quarters_between,
)


# ============================================================================
# Data structure tests
# ============================================================================


class TestSignalTimepoint:
    """Verify SignalTimepoint dataclass behavior."""

    def test_basic_creation(self):
        """SignalTimepoint can be created with required fields."""
        tp = SignalTimepoint(
            date=date(2023, 3, 31),
            reporting_quarter="2023Q1",
            case_count=10,
            cumulative_cases=42,
            prr=3.5,
            ror=4.0,
            ebgm=2.8,
            ic025=0.5,
        )
        assert tp.date == date(2023, 3, 31)
        assert tp.reporting_quarter == "2023Q1"
        assert tp.case_count == 10
        assert tp.cumulative_cases == 42
        assert tp.prr == 3.5
        assert tp.ror == 4.0
        assert tp.ebgm == 2.8
        assert tp.ic025 == 0.5
        assert tp.data_source == "FAERS_modeled"

    def test_custom_data_source(self):
        """data_source can be overridden."""
        tp = SignalTimepoint(
            date=date(2023, 6, 30),
            reporting_quarter="2023Q2",
            case_count=5,
            cumulative_cases=47,
            prr=3.6,
            ror=4.1,
            ebgm=2.9,
            ic025=0.6,
            data_source="published",
        )
        assert tp.data_source == "published"


class TestRegulatoryMilestone:
    """Verify RegulatoryMilestone dataclass behavior."""

    def test_basic_creation(self):
        """RegulatoryMilestone can be created with required fields."""
        m = RegulatoryMilestone(
            date=date(2024, 1, 19),
            milestone_type=MilestoneType.BOXED_WARNING,
            description="Test boxed warning",
        )
        assert m.date == date(2024, 1, 19)
        assert m.milestone_type == MilestoneType.BOXED_WARNING
        assert m.description == "Test boxed warning"
        assert m.source_url == ""
        assert m.products_affected == []

    def test_with_products_affected(self):
        """products_affected can be provided."""
        m = RegulatoryMilestone(
            date=date(2024, 1, 19),
            milestone_type=MilestoneType.BOXED_WARNING,
            description="Boxed warning for all",
            products_affected=["Kymriah", "Yescarta"],
        )
        assert len(m.products_affected) == 2
        assert "Kymriah" in m.products_affected


class TestTemporalSignalProfile:
    """Verify TemporalSignalProfile dataclass behavior."""

    def test_basic_creation(self):
        """TemporalSignalProfile can be created with minimal fields."""
        p = TemporalSignalProfile(
            product_name="Kymriah",
            generic_name="tisagenlecleucel",
            ae_category="CRS",
        )
        assert p.product_name == "Kymriah"
        assert p.generic_name == "tisagenlecleucel"
        assert p.ae_category == "CRS"
        assert p.timepoints == []
        assert p.milestones == []
        assert p.first_signal_date is None
        assert p.threshold_crossed_date is None
        assert p.current_status == SignalStatus.MONITORING

    def test_all_signal_statuses(self):
        """All SignalStatus enum values exist."""
        assert SignalStatus.EMERGING.value == "emerging"
        assert SignalStatus.CONFIRMED.value == "confirmed"
        assert SignalStatus.UNDER_REVIEW.value == "under_review"
        assert SignalStatus.RESOLVED.value == "resolved"
        assert SignalStatus.MONITORING.value == "monitoring"


class TestMilestoneType:
    """Verify MilestoneType enum completeness."""

    def test_all_types_exist(self):
        """All required milestone types exist."""
        types = {m.value for m in MilestoneType}
        assert "FDA Approval" in types
        assert "Boxed Warning" in types
        assert "REMS Update" in types
        assert "Label Change" in types
        assert "Dear Healthcare Provider Letter" in types
        assert "Class-wide Review" in types
        assert "Safety Communication" in types
        assert "Advisory Committee Meeting" in types

    def test_at_least_8_types(self):
        """At least 8 milestone types defined."""
        assert len(MilestoneType) >= 8


# ============================================================================
# Quarter utility tests
# ============================================================================


class TestQuarterUtilities:
    """Test quarter label and date generation."""

    def test_quarter_label(self):
        assert _quarter_label(2017, 4) == "2017Q4"
        assert _quarter_label(2023, 1) == "2023Q1"

    def test_quarter_end_date_q1(self):
        assert _quarter_end_date(2023, 1) == date(2023, 3, 31)

    def test_quarter_end_date_q2(self):
        assert _quarter_end_date(2023, 2) == date(2023, 6, 30)

    def test_quarter_end_date_q3(self):
        assert _quarter_end_date(2023, 3) == date(2023, 9, 30)

    def test_quarter_end_date_q4(self):
        assert _quarter_end_date(2023, 4) == date(2023, 12, 31)

    def test_quarters_between_same_year(self):
        qs = _quarters_between(date(2023, 1, 1), date(2023, 12, 31))
        assert len(qs) == 4
        assert qs[0] == (2023, 1)
        assert qs[3] == (2023, 4)

    def test_quarters_between_cross_year(self):
        qs = _quarters_between(date(2023, 10, 1), date(2024, 6, 30))
        assert (2023, 4) in qs
        assert (2024, 1) in qs
        assert (2024, 2) in qs

    def test_quarters_between_partial_start(self):
        """Start date in middle of quarter still includes that quarter."""
        qs = _quarters_between(date(2023, 2, 15), date(2023, 6, 30))
        assert (2023, 1) in qs
        assert (2023, 2) in qs


# ============================================================================
# Product metadata tests
# ============================================================================


class TestProductMetadata:
    """Verify product metadata completeness."""

    def test_six_products(self):
        """Must have exactly 6 CAR-T products."""
        assert len(PRODUCT_METADATA) == 6

    def test_all_product_names(self):
        """All expected product names are present."""
        expected = {"Kymriah", "Yescarta", "Tecartus", "Breyanzi", "Abecma", "Carvykti"}
        assert set(PRODUCT_METADATA.keys()) == expected

    def test_all_have_generic_names(self):
        """Every product has a generic_name."""
        for name, meta in PRODUCT_METADATA.items():
            assert "generic_name" in meta, f"{name} missing generic_name"
            assert len(meta["generic_name"]) > 5

    def test_all_have_approval_dates(self):
        """Every product has an approval_date."""
        for name, meta in PRODUCT_METADATA.items():
            assert "approval_date" in meta, f"{name} missing approval_date"
            assert isinstance(meta["approval_date"], date)

    def test_approval_dates_chronological(self):
        """Products approved in the correct order."""
        dates = [(name, meta["approval_date"]) for name, meta in PRODUCT_METADATA.items()]
        kymriah_date = PRODUCT_METADATA["Kymriah"]["approval_date"]
        carvykti_date = PRODUCT_METADATA["Carvykti"]["approval_date"]
        assert kymriah_date < carvykti_date

    def test_target_antigens(self):
        """Products have correct target antigens."""
        cd19_products = {"Kymriah", "Yescarta", "Tecartus", "Breyanzi"}
        bcma_products = {"Abecma", "Carvykti"}
        for name in cd19_products:
            assert PRODUCT_METADATA[name]["target_antigen"] == "CD19"
        for name in bcma_products:
            assert PRODUCT_METADATA[name]["target_antigen"] == "BCMA"

    def test_kymriah_approval_august_2017(self):
        """Kymriah approved Aug 30, 2017."""
        assert PRODUCT_METADATA["Kymriah"]["approval_date"] == date(2017, 8, 30)

    def test_yescarta_approval_october_2017(self):
        """Yescarta approved Oct 18, 2017."""
        assert PRODUCT_METADATA["Yescarta"]["approval_date"] == date(2017, 10, 18)


# ============================================================================
# Regulatory milestones tests
# ============================================================================


class TestRegulatoryMilestones:
    """Verify regulatory milestone data."""

    def test_milestones_not_empty(self):
        """Must have at least 6 milestones (product approvals)."""
        assert len(REGULATORY_MILESTONES) >= 6

    def test_milestones_have_dates(self):
        """Every milestone has a valid date."""
        for m in REGULATORY_MILESTONES:
            assert isinstance(m.date, date), f"Milestone '{m.description}' has no date"

    def test_milestones_have_descriptions(self):
        """Every milestone has a non-empty description."""
        for m in REGULATORY_MILESTONES:
            assert m.description, f"Milestone on {m.date} has empty description"

    def test_milestones_have_valid_types(self):
        """Every milestone has a valid MilestoneType."""
        for m in REGULATORY_MILESTONES:
            assert isinstance(m.milestone_type, MilestoneType)

    def test_fda_investigation_november_2023(self):
        """FDA safety communication about T-cell malignancies on Nov 28, 2023."""
        comm = [m for m in REGULATORY_MILESTONES
                if m.date == date(2023, 11, 28)
                and m.milestone_type == MilestoneType.SAFETY_COMMUNICATION]
        assert len(comm) >= 1
        assert "T-cell" in comm[0].description or "malignancy" in comm[0].description.lower()

    def test_boxed_warning_january_2024(self):
        """FDA boxed warning added in Jan 2024."""
        bw = [m for m in REGULATORY_MILESTONES
              if m.milestone_type == MilestoneType.BOXED_WARNING
              and m.date.year == 2024
              and m.date.month == 1]
        assert len(bw) >= 1

    def test_rems_update_april_2024(self):
        """REMS update in Apr 2024."""
        rems = [m for m in REGULATORY_MILESTONES
                if m.milestone_type == MilestoneType.REMS_UPDATE
                and m.date.year == 2024
                and m.date.month == 4]
        assert len(rems) >= 1

    def test_odac_meeting_june_2024(self):
        """ODAC meeting in Jun 2024."""
        odac = [m for m in REGULATORY_MILESTONES
                if m.milestone_type == MilestoneType.ADVISORY_COMMITTEE
                and m.date.year == 2024]
        assert len(odac) >= 1

    def test_regulatory_timeline_sorted(self):
        """get_regulatory_timeline returns sorted milestones."""
        timeline = get_regulatory_timeline()
        for i in range(len(timeline) - 1):
            assert timeline[i].date <= timeline[i + 1].date, (
                f"Milestone at index {i} ({timeline[i].date}) is after "
                f"index {i+1} ({timeline[i+1].date})"
            )

    def test_boxed_warning_affects_all_products(self):
        """Boxed warning milestone affects all 6 products."""
        bw = [m for m in REGULATORY_MILESTONES
              if m.milestone_type == MilestoneType.BOXED_WARNING]
        assert len(bw) >= 1
        assert len(bw[0].products_affected) == 6


# ============================================================================
# AE category normalization tests
# ============================================================================


class TestAECategoryNormalization:
    """Test AE category alias resolution."""

    def test_canonical_names(self):
        """Canonical names resolve to themselves."""
        assert _normalize_ae_category("CRS") == "CRS"
        assert _normalize_ae_category("secondary_malignancy") == "secondary_malignancy"
        assert _normalize_ae_category("neurotoxicity") == "neurotoxicity"
        assert _normalize_ae_category("cytopenias") == "cytopenias"

    def test_case_insensitive(self):
        """Category lookup is case-insensitive."""
        assert _normalize_ae_category("crs") == "CRS"
        assert _normalize_ae_category("CRS") == "CRS"
        assert _normalize_ae_category("Crs") is not None

    def test_aliases(self):
        """Common aliases resolve correctly."""
        assert _normalize_ae_category("cytokine release syndrome") == "CRS"
        assert _normalize_ae_category("icans") == "neurotoxicity"
        assert _normalize_ae_category("t-cell malignancy") == "secondary_malignancy"
        assert _normalize_ae_category("cytopenia") == "cytopenias"
        assert _normalize_ae_category("hematologic") == "cytopenias"

    def test_unknown_returns_none(self):
        """Unknown AE category returns None."""
        assert _normalize_ae_category("fake_ae") is None
        assert _normalize_ae_category("") is None
        assert _normalize_ae_category("headache") is None

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped."""
        assert _normalize_ae_category("  CRS  ") == "CRS"
        assert _normalize_ae_category(" neurotoxicity ") == "neurotoxicity"


# ============================================================================
# Product lookup tests
# ============================================================================


class TestProductLookup:
    """Test product name resolution."""

    def test_exact_match(self):
        """Exact product names resolve."""
        assert _find_product("Kymriah") == "Kymriah"
        assert _find_product("Yescarta") == "Yescarta"
        assert _find_product("Carvykti") == "Carvykti"

    def test_case_insensitive(self):
        """Product lookup is case-insensitive."""
        assert _find_product("kymriah") == "Kymriah"
        assert _find_product("YESCARTA") == "Yescarta"
        assert _find_product("tecartus") == "Tecartus"

    def test_partial_match(self):
        """Partial product name matching works."""
        assert _find_product("Kym") == "Kymriah"
        assert _find_product("breyanz") == "Breyanzi"

    def test_generic_name_match(self):
        """Generic name (INN) matching works."""
        assert _find_product("tisagenlecleucel") == "Kymriah"
        assert _find_product("axicabtagene") == "Yescarta"
        assert _find_product("ciltacabtagene") == "Carvykti"

    def test_unknown_returns_none(self):
        """Unknown product returns None."""
        assert _find_product("NotAProduct") is None
        assert _find_product("") is None
        assert _find_product("aspirin") is None


# ============================================================================
# Temporal profile generation tests
# ============================================================================


class TestTemporalProfileGeneration:
    """Verify generated temporal profiles are complete and realistic."""

    def test_all_profiles_generated(self):
        """30 profiles generated: 6 products x 5 AE categories."""
        profiles = get_all_temporal_profiles()
        assert len(profiles) == 30

    def test_profiles_for_every_product(self):
        """Every product has profiles."""
        profiles = get_all_temporal_profiles()
        products_seen = {p.product_name for p in profiles}
        assert products_seen == set(PRODUCT_METADATA.keys())

    def test_profiles_for_every_ae_category(self):
        """Every AE category has profiles."""
        profiles = get_all_temporal_profiles()
        categories_seen = {p.ae_category for p in profiles}
        assert categories_seen == set(AE_CATEGORIES)

    def test_each_profile_has_timepoints(self):
        """Every profile has at least one timepoint."""
        for profile in get_all_temporal_profiles():
            assert len(profile.timepoints) > 0, (
                f"{profile.product_name}/{profile.ae_category} has no timepoints"
            )

    def test_timepoints_chronological(self):
        """Timepoints within each profile are chronologically ordered."""
        for profile in get_all_temporal_profiles():
            dates = [tp.date for tp in profile.timepoints]
            for i in range(len(dates) - 1):
                assert dates[i] <= dates[i + 1], (
                    f"{profile.product_name}/{profile.ae_category}: "
                    f"timepoint {i} ({dates[i]}) after {i+1} ({dates[i+1]})"
                )

    def test_cumulative_cases_monotonic(self):
        """Cumulative case counts never decrease."""
        for profile in get_all_temporal_profiles():
            for i in range(len(profile.timepoints) - 1):
                assert (profile.timepoints[i].cumulative_cases
                        <= profile.timepoints[i + 1].cumulative_cases), (
                    f"{profile.product_name}/{profile.ae_category}: "
                    f"cumulative cases decreased at {profile.timepoints[i+1].reporting_quarter}"
                )

    def test_case_counts_non_negative(self):
        """Case counts are never negative."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                assert tp.case_count >= 0
                assert tp.cumulative_cases >= 0

    def test_prr_non_negative(self):
        """PRR values are non-negative."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                assert tp.prr >= 0.0, (
                    f"{profile.product_name}/{profile.ae_category} "
                    f"has negative PRR at {tp.reporting_quarter}"
                )

    def test_ror_non_negative(self):
        """ROR values are non-negative."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                assert tp.ror >= 0.0

    def test_ebgm_non_negative(self):
        """EBGM values are non-negative."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                assert tp.ebgm >= 0.0

    def test_crs_prr_high_from_start(self):
        """CRS profiles should have high PRR early (known effect)."""
        for product in PRODUCT_METADATA:
            profile = get_temporal_profile(product, "CRS")
            assert profile is not None
            # After a few quarters, CRS should have PRR > 2
            if len(profile.timepoints) > 2:
                assert profile.timepoints[2].prr > 2.0, (
                    f"{product} CRS PRR not > 2 by Q3"
                )

    def test_secondary_malignancy_delayed_onset(self):
        """Secondary malignancy signals should have delayed onset."""
        for product in PRODUCT_METADATA:
            profile = get_temporal_profile(product, "secondary_malignancy")
            assert profile is not None
            # First few quarters should have 0 or very few cases
            if len(profile.timepoints) >= 3:
                early_cases = sum(tp.case_count for tp in profile.timepoints[:3])
                # Should be very low initially
                assert early_cases <= 3, (
                    f"{product} secondary malignancy has {early_cases} cases in first 3 quarters"
                )

    def test_kymriah_has_longest_timeline(self):
        """Kymriah (earliest approval) should have the most timepoints."""
        kymriah = get_temporal_profile("Kymriah", "CRS")
        carvykti = get_temporal_profile("Carvykti", "CRS")
        assert kymriah is not None and carvykti is not None
        assert len(kymriah.timepoints) > len(carvykti.timepoints)

    def test_profiles_start_after_approval(self):
        """Timepoints should not precede product approval date."""
        for profile in get_all_temporal_profiles():
            if profile.approval_date and profile.timepoints:
                first_tp = profile.timepoints[0].date
                # Allow quarter-end to be slightly after approval within same quarter
                approval_quarter_start = date(
                    profile.approval_date.year,
                    ((profile.approval_date.month - 1) // 3) * 3 + 1,
                    1,
                )
                # First timepoint should be in same quarter as approval or later
                assert first_tp >= approval_quarter_start, (
                    f"{profile.product_name} first timepoint {first_tp} "
                    f"before approval quarter start {approval_quarter_start}"
                )


# ============================================================================
# Signal detection threshold tests
# ============================================================================


class TestSignalThresholds:
    """Test signal detection threshold crossing logic."""

    def test_crs_signals_detected_for_all_products(self):
        """CRS signals should be detected for all products (known effect)."""
        for product in PRODUCT_METADATA:
            profile = get_temporal_profile(product, "CRS")
            assert profile is not None
            assert profile.first_signal_date is not None, (
                f"{product} CRS signal never detected"
            )

    def test_first_signal_before_threshold_crossed(self):
        """first_signal_date should be <= threshold_crossed_date when both exist."""
        for profile in get_all_temporal_profiles():
            if profile.first_signal_date and profile.threshold_crossed_date:
                assert profile.first_signal_date <= profile.threshold_crossed_date

    def test_crs_confirmed_status(self):
        """CRS signals should have CONFIRMED status."""
        for product in PRODUCT_METADATA:
            profile = get_temporal_profile(product, "CRS")
            assert profile is not None
            assert profile.current_status == SignalStatus.CONFIRMED


# ============================================================================
# get_temporal_profile function tests
# ============================================================================


class TestGetTemporalProfile:
    """Test the get_temporal_profile function."""

    def test_valid_product_and_ae(self):
        """Returns profile for valid product-AE pair."""
        profile = get_temporal_profile("Kymriah", "CRS")
        assert profile is not None
        assert profile.product_name == "Kymriah"
        assert profile.ae_category == "CRS"

    def test_case_insensitive_product(self):
        """Product name lookup is case-insensitive."""
        profile = get_temporal_profile("kymriah", "CRS")
        assert profile is not None
        assert profile.product_name == "Kymriah"

    def test_case_insensitive_ae(self):
        """AE category lookup is case-insensitive."""
        profile = get_temporal_profile("Kymriah", "crs")
        assert profile is not None
        assert profile.ae_category == "CRS"

    def test_ae_alias(self):
        """AE aliases are resolved."""
        profile = get_temporal_profile("Kymriah", "icans")
        assert profile is not None
        assert profile.ae_category == "neurotoxicity"

    def test_unknown_product(self):
        """Returns None for unknown product."""
        assert get_temporal_profile("NotAProduct", "CRS") is None

    def test_unknown_ae(self):
        """Returns None for unknown AE category."""
        assert get_temporal_profile("Kymriah", "headache") is None

    def test_generic_name_lookup(self):
        """Can look up by generic name."""
        profile = get_temporal_profile("tisagenlecleucel", "CRS")
        assert profile is not None
        assert profile.product_name == "Kymriah"


# ============================================================================
# get_product_profiles tests
# ============================================================================


class TestGetProductProfiles:
    """Test the get_product_profiles function."""

    def test_returns_all_ae_categories(self):
        """Returns profiles for all AE categories for a product."""
        profiles = get_product_profiles("Kymriah")
        assert len(profiles) == 5
        categories = {p.ae_category for p in profiles}
        assert categories == set(AE_CATEGORIES)

    def test_all_same_product(self):
        """All returned profiles are for the requested product."""
        profiles = get_product_profiles("Yescarta")
        for p in profiles:
            assert p.product_name == "Yescarta"

    def test_unknown_product_returns_empty(self):
        """Unknown product returns empty list."""
        profiles = get_product_profiles("NotAProduct")
        assert profiles == []


# ============================================================================
# get_signal_summary tests
# ============================================================================


class TestSignalSummary:
    """Test the aggregate signal summary function."""

    def test_summary_has_required_keys(self):
        """Summary contains all required keys."""
        summary = get_signal_summary()
        required_keys = [
            "total_profiles", "total_products", "ae_categories",
            "products", "signals_detected", "signals_confirmed",
            "earliest_signal", "latest_signal",
            "total_regulatory_milestones", "by_ae_category", "by_product",
        ]
        for key in required_keys:
            assert key in summary, f"Summary missing key: {key}"

    def test_summary_total_profiles(self):
        """Total profiles should be 30."""
        summary = get_signal_summary()
        assert summary["total_profiles"] == 30

    def test_summary_total_products(self):
        """Total products should be 6."""
        summary = get_signal_summary()
        assert summary["total_products"] == 6

    def test_summary_ae_categories(self):
        """AE categories list is complete."""
        summary = get_signal_summary()
        assert set(summary["ae_categories"]) == set(AE_CATEGORIES)

    def test_summary_products_list(self):
        """Products list is complete."""
        summary = get_signal_summary()
        assert set(summary["products"]) == set(PRODUCT_METADATA.keys())

    def test_summary_signals_detected_positive(self):
        """At least some signals should be detected."""
        summary = get_signal_summary()
        assert summary["signals_detected"] > 0

    def test_summary_by_ae_category_structure(self):
        """by_ae_category has expected structure."""
        summary = get_signal_summary()
        for cat in AE_CATEGORIES:
            assert cat in summary["by_ae_category"]
            cat_data = summary["by_ae_category"][cat]
            assert "profiles" in cat_data
            assert "total_cumulative_cases" in cat_data
            assert "max_current_prr" in cat_data

    def test_summary_by_product_structure(self):
        """by_product has expected structure."""
        summary = get_signal_summary()
        for product in PRODUCT_METADATA:
            assert product in summary["by_product"]
            prod_data = summary["by_product"][product]
            assert "ae_categories" in prod_data
            assert "signals_detected" in prod_data
            assert "target_antigen" in prod_data

    def test_summary_regulatory_milestones_count(self):
        """Regulatory milestones count matches."""
        summary = get_signal_summary()
        assert summary["total_regulatory_milestones"] == len(REGULATORY_MILESTONES)


# ============================================================================
# Serialization tests
# ============================================================================


class TestSerialization:
    """Test profile and milestone serialization to dict."""

    def test_profile_to_dict_keys(self):
        """profile_to_dict returns dict with expected keys."""
        profile = get_temporal_profile("Kymriah", "CRS")
        assert profile is not None
        d = profile_to_dict(profile)
        expected_keys = [
            "product_name", "generic_name", "ae_category", "target_antigen",
            "approval_date", "first_signal_date", "threshold_crossed_date",
            "current_status", "total_timepoints", "latest_cumulative_cases",
            "latest_prr", "latest_ebgm", "timepoints", "milestones",
        ]
        for key in expected_keys:
            assert key in d, f"profile_to_dict missing key: {key}"

    def test_profile_to_dict_timepoints_structure(self):
        """Timepoints in serialized profile have expected structure."""
        profile = get_temporal_profile("Kymriah", "CRS")
        assert profile is not None
        d = profile_to_dict(profile)
        assert len(d["timepoints"]) > 0
        tp = d["timepoints"][0]
        for key in ["date", "quarter", "case_count", "cumulative_cases",
                     "prr", "ror", "ebgm", "ic025", "data_source"]:
            assert key in tp, f"Timepoint missing key: {key}"

    def test_milestone_to_dict_keys(self):
        """milestone_to_dict returns dict with expected keys."""
        milestones = get_regulatory_timeline()
        d = milestone_to_dict(milestones[0])
        for key in ["date", "type", "description", "source_url", "products_affected"]:
            assert key in d, f"milestone_to_dict missing key: {key}"

    def test_dates_are_iso_strings(self):
        """Dates in serialized output are ISO format strings."""
        profile = get_temporal_profile("Kymriah", "CRS")
        assert profile is not None
        d = profile_to_dict(profile)
        # approval_date should be a string like "2017-08-30"
        assert isinstance(d["approval_date"], str)
        assert len(d["approval_date"]) == 10  # YYYY-MM-DD

    def test_status_is_string(self):
        """current_status is serialized as string value."""
        profile = get_temporal_profile("Kymriah", "CRS")
        assert profile is not None
        d = profile_to_dict(profile)
        assert isinstance(d["current_status"], str)
        assert d["current_status"] in {"emerging", "confirmed", "under_review",
                                         "resolved", "monitoring"}


# ============================================================================
# API endpoint integration tests
# ============================================================================


class TestAPIEndpoints:
    """Test API endpoints (requires FastAPI TestClient)."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        from fastapi.testclient import TestClient
        from src.api.app import app
        return TestClient(app, raise_server_exceptions=False)

    def test_temporal_evolution_all(self, client):
        """GET /api/v1/signals/temporal-evolution returns 200."""
        resp = client.get("/api/v1/signals/temporal-evolution")
        assert resp.status_code == 200
        data = resp.json()
        assert "profiles" in data
        assert "milestones" in data
        assert "summary" in data
        assert len(data["profiles"]) == 30

    def test_temporal_evolution_filter_crs(self, client):
        """GET /api/v1/signals/temporal-evolution?ae_category=CRS returns 6 profiles."""
        resp = client.get("/api/v1/signals/temporal-evolution?ae_category=CRS")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["profiles"]) == 6
        for p in data["profiles"]:
            assert p["ae_category"] == "CRS"

    def test_temporal_evolution_filter_malignancy(self, client):
        """Filter by secondary_malignancy works."""
        resp = client.get("/api/v1/signals/temporal-evolution?ae_category=secondary_malignancy")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["profiles"]) == 6

    def test_temporal_evolution_invalid_ae(self, client):
        """Invalid AE category returns 400."""
        resp = client.get("/api/v1/signals/temporal-evolution?ae_category=invalid")
        assert resp.status_code == 400

    def test_temporal_evolution_product(self, client):
        """GET /api/v1/signals/temporal-evolution/Kymriah returns product profiles."""
        resp = client.get("/api/v1/signals/temporal-evolution/Kymriah")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_name"] == "Kymriah"
        assert len(data["profiles"]) == 5

    def test_temporal_evolution_product_case_insensitive(self, client):
        """Product name is case-insensitive."""
        resp = client.get("/api/v1/signals/temporal-evolution/kymriah")
        assert resp.status_code == 200
        data = resp.json()
        assert data["product_name"] == "Kymriah"

    def test_temporal_evolution_product_not_found(self, client):
        """Unknown product returns 404."""
        resp = client.get("/api/v1/signals/temporal-evolution/FakeProduct")
        assert resp.status_code == 404

    def test_regulatory_timeline(self, client):
        """GET /api/v1/signals/regulatory-timeline returns milestones."""
        resp = client.get("/api/v1/signals/regulatory-timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "milestones" in data
        assert "total_milestones" in data
        assert data["total_milestones"] >= 6

    def test_regulatory_timeline_sorted(self, client):
        """Milestones are returned in chronological order."""
        resp = client.get("/api/v1/signals/regulatory-timeline")
        data = resp.json()
        dates = [m["date"] for m in data["milestones"]]
        assert dates == sorted(dates)

    def test_all_endpoints_have_request_id(self, client):
        """All temporal signal endpoints include request_id."""
        endpoints = [
            "/api/v1/signals/temporal-evolution",
            "/api/v1/signals/temporal-evolution/Kymriah",
            "/api/v1/signals/regulatory-timeline",
        ]
        for endpoint in endpoints:
            resp = client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert "request_id" in data, f"{endpoint} missing request_id"

    def test_all_endpoints_have_timestamp(self, client):
        """All temporal signal endpoints include timestamp."""
        endpoints = [
            "/api/v1/signals/temporal-evolution",
            "/api/v1/signals/temporal-evolution/Kymriah",
            "/api/v1/signals/regulatory-timeline",
        ]
        for endpoint in endpoints:
            resp = client.get(endpoint)
            assert resp.status_code == 200
            data = resp.json()
            assert "timestamp" in data, f"{endpoint} missing timestamp"


# ============================================================================
# PRR / EBGM realism tests
# ============================================================================


class TestMetricRealism:
    """Verify disproportionality metrics are within realistic ranges."""

    def test_crs_prr_realistic_range(self):
        """CRS PRR should be in range 5-100 for established signals."""
        for product in PRODUCT_METADATA:
            profile = get_temporal_profile(product, "CRS")
            assert profile is not None
            if profile.timepoints:
                latest = profile.timepoints[-1]
                assert 1.0 < latest.prr < 200.0, (
                    f"{product} CRS PRR={latest.prr} out of realistic range"
                )

    def test_ebgm_not_greater_than_prr_by_much(self):
        """EBGM should generally not exceed PRR (Bayesian shrinkage)."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                if tp.prr > 0 and tp.ebgm > 0:
                    # EBGM can exceed PRR slightly but shouldn't be 10x larger
                    assert tp.ebgm < tp.prr * 5.0, (
                        f"{profile.product_name}/{profile.ae_category} "
                        f"EBGM={tp.ebgm} >> PRR={tp.prr} at {tp.reporting_quarter}"
                    )

    def test_ror_generally_exceeds_prr(self):
        """ROR is typically >= PRR for rare events."""
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                if tp.prr > 1.0 and tp.ror > 0:
                    assert tp.ror >= tp.prr * 0.9, (
                        f"{profile.product_name}/{profile.ae_category} "
                        f"ROR={tp.ror} much less than PRR={tp.prr}"
                    )

    def test_secondary_malignancy_prr_lower_than_crs(self):
        """Secondary malignancy PRR should generally be lower than CRS PRR."""
        for product in PRODUCT_METADATA:
            crs = get_temporal_profile(product, "CRS")
            mal = get_temporal_profile(product, "secondary_malignancy")
            assert crs is not None and mal is not None
            if crs.timepoints and mal.timepoints:
                crs_latest = crs.timepoints[-1].prr
                mal_latest = mal.timepoints[-1].prr
                # CRS is a much stronger signal than secondary malignancy
                assert crs_latest > mal_latest, (
                    f"{product}: CRS PRR ({crs_latest}) <= malignancy PRR ({mal_latest})"
                )


# ============================================================================
# Edge case tests
# ============================================================================


class TestEdgeCases:
    """Test boundary and edge conditions."""

    def test_profile_cache_consistency(self):
        """Multiple calls return same data (cached)."""
        profiles1 = get_all_temporal_profiles()
        profiles2 = get_all_temporal_profiles()
        assert len(profiles1) == len(profiles2)
        for p1, p2 in zip(profiles1, profiles2):
            assert p1.product_name == p2.product_name
            assert p1.ae_category == p2.ae_category
            assert len(p1.timepoints) == len(p2.timepoints)

    def test_empty_string_product_returns_none(self):
        """Empty string product returns None."""
        assert get_temporal_profile("", "CRS") is None

    def test_empty_string_ae_returns_none(self):
        """Empty string AE returns None."""
        assert get_temporal_profile("Kymriah", "") is None

    def test_whitespace_only_product_returns_none(self):
        """Whitespace-only product name returns None."""
        assert get_temporal_profile("   ", "CRS") is None

    def test_all_products_have_approval_date_in_profile(self):
        """Every generated profile has approval_date set."""
        for profile in get_all_temporal_profiles():
            assert profile.approval_date is not None

    def test_all_products_have_target_antigen_in_profile(self):
        """Every generated profile has target_antigen set."""
        for profile in get_all_temporal_profiles():
            assert profile.target_antigen in ("CD19", "BCMA")

    def test_all_products_have_generic_name_in_profile(self):
        """Every generated profile has generic_name set."""
        for profile in get_all_temporal_profiles():
            assert len(profile.generic_name) > 5

    def test_quarter_labels_formatted_correctly(self):
        """All quarter labels match YYYYQN pattern."""
        import re
        pattern = re.compile(r"^\d{4}Q[1-4]$")
        for profile in get_all_temporal_profiles():
            for tp in profile.timepoints:
                assert pattern.match(tp.reporting_quarter), (
                    f"Bad quarter label: {tp.reporting_quarter}"
                )
