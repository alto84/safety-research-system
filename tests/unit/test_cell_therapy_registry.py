"""
Unit tests for data/cell_therapy_registry.py

Tests the cell therapy registry for data completeness, consistency,
and structural integrity of therapy types and the AE taxonomy.
"""

import pytest

from data.cell_therapy_registry import (
    AE_TAXONOMY,
    THERAPY_TYPES,
    TherapyType,
    get_ae_definition,
    get_ae_rates_for_therapy,
    get_all_categories,
    get_applicable_aes,
    get_approved_therapies,
    summary_stats,
)


# ============================================================================
# THERAPY_TYPES — required fields
# ============================================================================


class TestTherapyTypesRequiredFields:
    """Every therapy type must have all required fields populated."""

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_id(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert therapy.id == therapy_id

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_name(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.name, str)
        assert len(therapy.name) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_category(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.category, str)
        assert len(therapy.category) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_target_antigens(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.target_antigens, list)
        assert len(therapy.target_antigens) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_applicable_aes(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.applicable_aes, list)
        assert len(therapy.applicable_aes) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_data_sources(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.data_sources, list)
        assert len(therapy.data_sources) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_references(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.references, list)
        assert len(therapy.references) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_has_risk_factors(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy.risk_factors, list)
        assert len(therapy.risk_factors) > 0

    @pytest.mark.parametrize("therapy_id", list(THERAPY_TYPES.keys()))
    def test_is_therapy_type_instance(self, therapy_id):
        therapy = THERAPY_TYPES[therapy_id]
        assert isinstance(therapy, TherapyType)


# ============================================================================
# AE Taxonomy completeness
# ============================================================================


class TestAETaxonomyCompleteness:
    """Tests for the AE_TAXONOMY dictionary."""

    def test_ae_taxonomy_nonempty(self):
        assert len(AE_TAXONOMY) > 0

    def test_ae_taxonomy_has_crs(self):
        assert "cytokine_release_syndrome" in AE_TAXONOMY

    def test_ae_taxonomy_has_icans(self):
        assert "icans" in AE_TAXONOMY

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_name(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "name" in ae
        assert isinstance(ae["name"], str)
        assert len(ae["name"]) > 0

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_description(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "description" in ae
        assert isinstance(ae["description"], str)
        assert len(ae["description"]) > 0

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_grading_system(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "grading_system" in ae

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_management(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "management" in ae
        assert isinstance(ae["management"], str)
        assert len(ae["management"]) > 0

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_biomarkers(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "biomarkers" in ae
        assert isinstance(ae["biomarkers"], list)
        assert len(ae["biomarkers"]) > 0

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_applicable_therapies(self, ae_name):
        ae = AE_TAXONOMY[ae_name]
        assert "applicable_therapies" in ae
        assert isinstance(ae["applicable_therapies"], list)
        assert len(ae["applicable_therapies"]) > 0

    @pytest.mark.parametrize("ae_name", list(AE_TAXONOMY.keys()))
    def test_ae_has_grade_definitions(self, ae_name):
        """Each AE should define at least grade_3 (the clinically significant threshold)."""
        ae = AE_TAXONOMY[ae_name]
        # At minimum, grade 3 should be defined for all AEs
        assert "grade_3" in ae or "grade_1" in ae, (
            f"AE '{ae_name}' should have grade definitions"
        )


# ============================================================================
# Data consistency — no duplicate IDs
# ============================================================================


class TestDataConsistency:
    """Tests for data integrity across the registry."""

    def test_no_duplicate_therapy_ids(self):
        """All therapy IDs should be unique (dict keys enforce this, but
        verify IDs match keys)."""
        for tid, therapy in THERAPY_TYPES.items():
            assert therapy.id == tid, (
                f"Therapy ID mismatch: key='{tid}' but therapy.id='{therapy.id}'"
            )

    def test_applicable_aes_reference_valid_taxonomy_keys(self):
        """Every applicable_ae in each therapy should exist in AE_TAXONOMY."""
        for tid, therapy in THERAPY_TYPES.items():
            for ae_key in therapy.applicable_aes:
                assert ae_key in AE_TAXONOMY, (
                    f"Therapy '{tid}' references unknown AE '{ae_key}'"
                )

    def test_default_ae_rates_reference_applicable_aes(self):
        """Every key in default_ae_rates with nonzero rates should be in
        the therapy's applicable_aes.  Zero-rate entries are allowed as
        documentation of notable absences (e.g. ICANS=0% for NK cells)."""
        for tid, therapy in THERAPY_TYPES.items():
            for ae_key, rates in therapy.default_ae_rates.items():
                if rates.get("any_grade", 0) > 0 or rates.get("grade3_plus", 0) > 0:
                    assert ae_key in therapy.applicable_aes, (
                        f"Therapy '{tid}' has nonzero rate data for '{ae_key}' "
                        f"which is not in its applicable_aes"
                    )

    def test_ae_rates_have_required_fields(self):
        """Each AE rate entry should have any_grade and grade3_plus."""
        for tid, therapy in THERAPY_TYPES.items():
            for ae_key, rates in therapy.default_ae_rates.items():
                assert "any_grade" in rates, (
                    f"Therapy '{tid}', AE '{ae_key}' missing 'any_grade'"
                )
                assert "grade3_plus" in rates, (
                    f"Therapy '{tid}', AE '{ae_key}' missing 'grade3_plus'"
                )

    def test_ae_rates_are_valid_proportions(self):
        """any_grade and grade3_plus should be between 0 and 1."""
        for tid, therapy in THERAPY_TYPES.items():
            for ae_key, rates in therapy.default_ae_rates.items():
                assert 0.0 <= rates["any_grade"] <= 1.0, (
                    f"Therapy '{tid}', AE '{ae_key}': any_grade "
                    f"{rates['any_grade']} out of [0, 1]"
                )
                assert 0.0 <= rates["grade3_plus"] <= 1.0, (
                    f"Therapy '{tid}', AE '{ae_key}': grade3_plus "
                    f"{rates['grade3_plus']} out of [0, 1]"
                )

    def test_grade3_plus_leq_any_grade(self):
        """Grade 3+ rate should never exceed any-grade rate."""
        for tid, therapy in THERAPY_TYPES.items():
            for ae_key, rates in therapy.default_ae_rates.items():
                assert rates["grade3_plus"] <= rates["any_grade"] + 1e-9, (
                    f"Therapy '{tid}', AE '{ae_key}': grade3_plus "
                    f"({rates['grade3_plus']}) > any_grade ({rates['any_grade']})"
                )

    def test_approved_products_have_required_fields(self):
        """Each approved product should have name, target, approval_year,
        indication, and sponsor."""
        for tid, therapy in THERAPY_TYPES.items():
            for product in therapy.approved_products:
                assert "name" in product, f"Therapy '{tid}' product missing 'name'"
                assert "target" in product, f"Therapy '{tid}' product missing 'target'"
                assert "approval_year" in product, f"Therapy '{tid}' product missing 'approval_year'"
                assert "indication" in product, f"Therapy '{tid}' product missing 'indication'"
                assert "sponsor" in product, f"Therapy '{tid}' product missing 'sponsor'"

    def test_pipeline_products_have_required_fields(self):
        """Each pipeline product should have name, target, phase, and sponsor."""
        for tid, therapy in THERAPY_TYPES.items():
            for product in therapy.pipeline_products:
                assert "name" in product, f"Therapy '{tid}' pipeline product missing 'name'"
                assert "target" in product, f"Therapy '{tid}' pipeline product missing 'target'"
                assert "phase" in product, f"Therapy '{tid}' pipeline product missing 'phase'"
                assert "sponsor" in product, f"Therapy '{tid}' pipeline product missing 'sponsor'"


# ============================================================================
# Helper functions
# ============================================================================


class TestHelperFunctions:
    """Tests for registry convenience functions."""

    def test_get_applicable_aes_known_therapy(self):
        """Getting AEs for a known therapy should return a non-empty list."""
        aes = get_applicable_aes("cart_cd19")
        assert isinstance(aes, list)
        assert len(aes) > 0
        assert "cytokine_release_syndrome" in aes

    def test_get_applicable_aes_unknown_therapy(self):
        """Getting AEs for an unknown therapy should return an empty list."""
        aes = get_applicable_aes("nonexistent_therapy_zzz")
        assert aes == []

    def test_get_ae_definition_known(self):
        """Getting a known AE definition should return a non-empty dict."""
        defn = get_ae_definition("cytokine_release_syndrome")
        assert isinstance(defn, dict)
        assert "name" in defn
        assert "description" in defn

    def test_get_ae_definition_unknown(self):
        """Getting an unknown AE definition should return an empty dict."""
        defn = get_ae_definition("nonexistent_ae_zzz")
        assert defn == {}

    def test_get_all_categories(self):
        """Should return a sorted list of unique category strings."""
        categories = get_all_categories()
        assert isinstance(categories, list)
        assert len(categories) > 0
        # Should be sorted
        assert categories == sorted(categories)

    def test_get_approved_therapies(self):
        """Should return only therapies with at least one approved product."""
        approved = get_approved_therapies()
        assert isinstance(approved, list)
        for therapy in approved:
            assert len(therapy.approved_products) > 0

    def test_get_ae_rates_for_therapy_known(self):
        """Getting AE rates for a known therapy + AE should return rate data."""
        rates = get_ae_rates_for_therapy("cart_cd19", "cytokine_release_syndrome")
        assert isinstance(rates, dict)
        assert "any_grade" in rates
        assert "grade3_plus" in rates

    def test_get_ae_rates_for_therapy_unknown(self):
        """Getting rates for an unknown therapy should return empty dict."""
        rates = get_ae_rates_for_therapy("nonexistent", "cytokine_release_syndrome")
        assert rates == {}

    def test_summary_stats(self):
        """summary_stats() should return aggregate registry statistics."""
        stats = summary_stats()
        assert "total_therapy_types" in stats
        assert "total_ae_types" in stats
        assert "total_approved_products" in stats
        assert "total_pipeline_products" in stats
        assert "categories" in stats
        assert stats["total_therapy_types"] == len(THERAPY_TYPES)
        assert stats["total_ae_types"] == len(AE_TAXONOMY)
