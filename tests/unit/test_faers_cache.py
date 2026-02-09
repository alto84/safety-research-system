"""Unit tests for the cached FAERS product comparison data loader."""

import pytest

from src.data.faers_cache import get_faers_comparison


EXPECTED_PRODUCTS = ["Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti"]


class TestFAERSCacheLoader:
    """Tests for get_faers_comparison()."""

    def test_data_loads_successfully(self):
        data = get_faers_comparison()
        assert isinstance(data, dict)

    def test_has_metadata_key(self):
        data = get_faers_comparison()
        assert "metadata" in data

    def test_has_product_profiles_key(self):
        data = get_faers_comparison()
        assert "product_profiles" in data

    def test_has_comparison_key(self):
        data = get_faers_comparison()
        assert "comparison" in data

    def test_metadata_has_source(self):
        data = get_faers_comparison()
        assert "source" in data["metadata"]

    def test_metadata_has_extraction_date(self):
        data = get_faers_comparison()
        assert "extraction_date" in data["metadata"]

    def test_metadata_has_products_queried(self):
        data = get_faers_comparison()
        assert "products_queried" in data["metadata"]

    @pytest.mark.parametrize("product", EXPECTED_PRODUCTS)
    def test_product_profile_exists(self, product):
        data = get_faers_comparison()
        assert product in data["product_profiles"], f"Missing profile for {product}"

    def test_all_six_products_present(self):
        data = get_faers_comparison()
        profiles = data["product_profiles"]
        assert len(profiles) >= 6

    @pytest.mark.parametrize("product", EXPECTED_PRODUCTS)
    def test_product_has_total_reports(self, product):
        data = get_faers_comparison()
        prof = data["product_profiles"][product]
        assert "total_reports" in prof
        assert isinstance(prof["total_reports"], int)
        assert prof["total_reports"] > 0

    @pytest.mark.parametrize("product", EXPECTED_PRODUCTS)
    def test_product_has_top_adverse_events(self, product):
        data = get_faers_comparison()
        prof = data["product_profiles"][product]
        assert "top_adverse_events" in prof
        assert len(prof["top_adverse_events"]) > 0

    @pytest.mark.parametrize("product", EXPECTED_PRODUCTS)
    def test_product_has_approval_date(self, product):
        data = get_faers_comparison()
        prof = data["product_profiles"][product]
        assert "approval_date" in prof

    def test_comparison_has_total_reports_by_product(self):
        data = get_faers_comparison()
        assert "total_reports_by_product" in data["comparison"]

    def test_comparison_has_crs_comparison(self):
        data = get_faers_comparison()
        assert "crs_comparison" in data["comparison"]

    def test_comparison_has_neurotoxicity_comparison(self):
        data = get_faers_comparison()
        assert "neurotoxicity_comparison" in data["comparison"]

    def test_comparison_has_mortality_comparison(self):
        data = get_faers_comparison()
        assert "mortality_comparison" in data["comparison"]

    def test_comparison_has_infection_comparison(self):
        data = get_faers_comparison()
        assert "infection_comparison" in data["comparison"]

    def test_comparison_has_cytopenia_comparison(self):
        data = get_faers_comparison()
        assert "cytopenia_comparison" in data["comparison"]

    @pytest.mark.parametrize("comparison_key", [
        "crs_comparison", "neurotoxicity_comparison", "mortality_comparison",
        "infection_comparison", "cytopenia_comparison",
    ])
    def test_comparison_has_all_products(self, comparison_key):
        data = get_faers_comparison()
        comp = data["comparison"][comparison_key]
        for product in EXPECTED_PRODUCTS:
            assert product in comp, f"{product} missing from {comparison_key}"

    @pytest.mark.parametrize("comparison_key", [
        "crs_comparison", "neurotoxicity_comparison", "mortality_comparison",
        "infection_comparison", "cytopenia_comparison",
    ])
    def test_comparison_rates_are_reasonable(self, comparison_key):
        data = get_faers_comparison()
        comp = data["comparison"][comparison_key]
        for product in EXPECTED_PRODUCTS:
            rate = comp[product]["rate_pct"]
            assert 0 <= rate <= 100, (
                f"{product} {comparison_key} rate {rate}% out of range"
            )

    def test_comparison_has_top_ae_matrix(self):
        data = get_faers_comparison()
        assert "top_ae_comparison_matrix" in data["comparison"]

    def test_crs_rates_nonzero_for_all_products(self):
        data = get_faers_comparison()
        crs = data["comparison"]["crs_comparison"]
        for product in EXPECTED_PRODUCTS:
            assert crs[product]["rate_pct"] > 0, f"CRS rate is 0 for {product}"
