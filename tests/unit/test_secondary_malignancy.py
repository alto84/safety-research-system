"""
Comprehensive unit tests for src/models/secondary_malignancy.py

Tests the secondary malignancy signal detection module including:
- Data structure completeness and integrity
- Risk assessment for all 6 CAR-T products
- Monitoring protocol completeness
- Causality framework structure
- Regulatory timeline ordering and content
- Known signals data quality
- Epidemiological summary accuracy
"""

import pytest
from datetime import date

from src.models.secondary_malignancy import (
    CAR_T_PRODUCTS,
    DisproportionalityMetrics,
    FAERS_SUMMARY_STATS,
    FDA_REGULATORY_TIMELINE,
    KNOWN_SIGNALS,
    MALIGNANCY_TYPES,
    MalignancyType,
    RegulatoryMilestone,
    SecondaryMalignancySignal,
    TherapyTarget,
    assess_secondary_malignancy_risk,
    get_all_signals_data,
    get_causality_framework,
    get_monitoring_protocol,
)


# ============================================================================
# Known signals data integrity
# ============================================================================


class TestKnownSignalsIntegrity:
    """Verify that all known signals have required fields and valid data."""

    def test_known_signals_not_empty(self):
        """KNOWN_SIGNALS must contain at least one signal."""
        assert len(KNOWN_SIGNALS) > 0

    def test_all_signals_have_product_name(self):
        """Every signal must have a non-empty product name."""
        for signal in KNOWN_SIGNALS:
            assert signal.product_name, f"Signal missing product_name"
            assert signal.product_name in CAR_T_PRODUCTS, (
                f"Signal product '{signal.product_name}' not in product registry"
            )

    def test_all_signals_have_malignancy_type(self):
        """Every signal must have a valid MalignancyType."""
        for signal in KNOWN_SIGNALS:
            assert isinstance(signal.malignancy_type, MalignancyType), (
                f"Signal for {signal.product_name} has invalid malignancy_type"
            )

    def test_all_signals_have_positive_onset_time(self):
        """Time to onset must be positive."""
        for signal in KNOWN_SIGNALS:
            assert signal.time_to_onset_months > 0, (
                f"Signal for {signal.product_name} has non-positive "
                f"time_to_onset_months: {signal.time_to_onset_months}"
            )

    def test_all_signals_have_positive_reporting_rate(self):
        """Reporting rate per 1000 must be positive."""
        for signal in KNOWN_SIGNALS:
            assert signal.reporting_rate_per_1000 > 0, (
                f"Signal for {signal.product_name} has non-positive "
                f"reporting_rate: {signal.reporting_rate_per_1000}"
            )

    def test_all_signals_have_disproportionality_metrics(self):
        """Every signal must have PRR, ROR, EBGM metrics."""
        for signal in KNOWN_SIGNALS:
            dm = signal.disproportionality_metrics
            assert isinstance(dm, DisproportionalityMetrics), (
                f"Signal for {signal.product_name} missing disproportionality_metrics"
            )
            assert dm.prr > 0, f"{signal.product_name}: PRR must be positive"
            assert dm.ror > 0, f"{signal.product_name}: ROR must be positive"
            assert dm.ebgm > 0, f"{signal.product_name}: EBGM must be positive"

    def test_all_signals_have_evidence_grade(self):
        """Every signal must have a valid evidence grade."""
        valid_grades = {"strong", "moderate", "limited", "case_report"}
        for signal in KNOWN_SIGNALS:
            assert signal.evidence_grade in valid_grades, (
                f"Signal for {signal.product_name} has invalid evidence_grade: "
                f"'{signal.evidence_grade}'"
            )

    def test_all_signals_have_references(self):
        """Every signal must have at least one PubMed reference."""
        for signal in KNOWN_SIGNALS:
            assert len(signal.references) > 0, (
                f"Signal for {signal.product_name} "
                f"({signal.malignancy_type.value}) has no references"
            )

    def test_all_signals_have_regulatory_actions(self):
        """Every signal must have at least one regulatory action."""
        for signal in KNOWN_SIGNALS:
            assert len(signal.regulatory_actions) > 0, (
                f"Signal for {signal.product_name} "
                f"({signal.malignancy_type.value}) has no regulatory_actions"
            )

    def test_car_transgene_detected_is_optional_bool(self):
        """car_transgene_detected must be True, False, or None."""
        for signal in KNOWN_SIGNALS:
            assert signal.car_transgene_detected in (True, False, None), (
                f"Signal for {signal.product_name}: car_transgene_detected "
                f"must be True, False, or None"
            )

    def test_at_least_one_car_positive_signal(self):
        """At least one known signal must have CAR transgene confirmed."""
        car_positive = [
            s for s in KNOWN_SIGNALS
            if s.car_transgene_detected is True
        ]
        assert len(car_positive) > 0, (
            "Expected at least one signal with CAR transgene confirmed"
        )

    def test_t_cell_lymphoma_signals_for_all_products(self):
        """Every CAR-T product must have a T-cell lymphoma signal (per FDA)."""
        products_with_tcl = set()
        for signal in KNOWN_SIGNALS:
            if signal.malignancy_type == MalignancyType.T_CELL_LYMPHOMA:
                products_with_tcl.add(signal.product_name)

        for product in CAR_T_PRODUCTS:
            assert product in products_with_tcl, (
                f"Product {product} missing T-cell lymphoma signal "
                f"(required by FDA boxed warning)"
            )


# ============================================================================
# Product registry
# ============================================================================


class TestProductRegistry:
    """Verify CAR-T product metadata completeness."""

    def test_six_products_registered(self):
        """All 6 approved CAR-T products must be registered."""
        expected = {"Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti"}
        assert set(CAR_T_PRODUCTS.keys()) == expected

    def test_product_has_required_fields(self):
        """Every product must have required metadata fields."""
        required_fields = {
            "generic_name", "target", "manufacturer",
            "approval_year", "indication", "vector",
        }
        for name, info in CAR_T_PRODUCTS.items():
            for field_name in required_fields:
                assert field_name in info, (
                    f"Product {name} missing field '{field_name}'"
                )

    def test_product_targets_are_valid(self):
        """Every product target must be CD19 or BCMA."""
        for name, info in CAR_T_PRODUCTS.items():
            assert isinstance(info["target"], TherapyTarget), (
                f"Product {name} has invalid target type"
            )

    def test_cd19_products(self):
        """Verify CD19-directed products."""
        cd19_products = {
            name for name, info in CAR_T_PRODUCTS.items()
            if info["target"] == TherapyTarget.CD19
        }
        assert "Yescarta" in cd19_products
        assert "Kymriah" in cd19_products
        assert "Tecartus" in cd19_products
        assert "Breyanzi" in cd19_products

    def test_bcma_products(self):
        """Verify BCMA-directed products."""
        bcma_products = {
            name for name, info in CAR_T_PRODUCTS.items()
            if info["target"] == TherapyTarget.BCMA
        }
        assert "Abecma" in bcma_products
        assert "Carvykti" in bcma_products

    def test_approval_years_reasonable(self):
        """Approval years must be between 2017 and 2025."""
        for name, info in CAR_T_PRODUCTS.items():
            year = info["approval_year"]
            assert 2017 <= year <= 2025, (
                f"Product {name} has unreasonable approval year: {year}"
            )


# ============================================================================
# Risk assessment for each product
# ============================================================================


class TestRiskAssessment:
    """Test assess_secondary_malignancy_risk() for all products."""

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_assessment_returns_dict(self, product_name):
        """Risk assessment must return a dict for every known product."""
        result = assess_secondary_malignancy_risk(product_name)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_assessment_has_required_keys(self, product_name):
        """Risk assessment must contain all required top-level keys."""
        result = assess_secondary_malignancy_risk(product_name)
        required_keys = {
            "product_name", "product_info", "known_signals",
            "risk_level", "monitoring_recommendations",
            "regulatory_status", "causality_assessment",
        }
        for key in required_keys:
            assert key in result, (
                f"Risk assessment for {product_name} missing key '{key}'"
            )

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_level_is_elevated(self, product_name):
        """All CAR-T products must have 'elevated' risk level per FDA boxed warning."""
        result = assess_secondary_malignancy_risk(product_name)
        assert result["risk_level"] == "elevated"

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_assessment_has_signals(self, product_name):
        """Every product must have at least one known signal."""
        result = assess_secondary_malignancy_risk(product_name)
        assert len(result["known_signals"]) > 0, (
            f"No signals found for {product_name}"
        )

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_assessment_has_regulatory_status(self, product_name):
        """Every product must have regulatory status entries."""
        result = assess_secondary_malignancy_risk(product_name)
        assert len(result["regulatory_status"]) > 0, (
            f"No regulatory status for {product_name}"
        )

    @pytest.mark.parametrize("product_name", [
        "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
    ])
    def test_risk_assessment_has_caveats(self, product_name):
        """Risk assessment must include caveats."""
        result = assess_secondary_malignancy_risk(product_name)
        assert "caveats" in result
        assert len(result["caveats"]) > 0

    def test_unknown_product_returns_error(self):
        """Unknown product names must return an error dict."""
        result = assess_secondary_malignancy_risk("NonexistentProduct")
        assert result["risk_level"] == "unknown"
        assert "error" in result
        assert result["known_signals"] == []

    def test_case_insensitive_product_match(self):
        """Product name matching must be case-insensitive."""
        result_lower = assess_secondary_malignancy_risk("yescarta")
        result_upper = assess_secondary_malignancy_risk("YESCARTA")
        result_mixed = assess_secondary_malignancy_risk("Yescarta")
        assert result_lower["risk_level"] == "elevated"
        assert result_upper["risk_level"] == "elevated"
        assert result_mixed["risk_level"] == "elevated"

    def test_risk_assessment_epidemiological_context(self):
        """Risk assessment must include epidemiological context."""
        result = assess_secondary_malignancy_risk("Yescarta")
        assert "epidemiological_context" in result
        ctx = result["epidemiological_context"]
        assert "overall_secondary_malignancy_rate_pct" in ctx
        assert "t_cell_malignancy_cases_reported" in ctx
        assert ctx["t_cell_malignancy_cases_reported"] == 38

    def test_risk_assessment_with_explicit_therapy_type(self):
        """Passing explicit therapy_type should work."""
        result = assess_secondary_malignancy_risk("Yescarta", therapy_type="CD19")
        assert result["risk_level"] == "elevated"


# ============================================================================
# Monitoring protocol
# ============================================================================


class TestMonitoringProtocol:
    """Test the monitoring protocol for completeness and correctness."""

    def test_monitoring_protocol_returns_dict(self):
        """Protocol must return a dict."""
        protocol = get_monitoring_protocol()
        assert isinstance(protocol, dict)

    def test_monitoring_protocol_has_phases(self):
        """Protocol must define monitoring phases."""
        protocol = get_monitoring_protocol()
        assert "phases" in protocol
        assert len(protocol["phases"]) >= 4, (
            "Expected at least 4 monitoring phases (acute, early, "
            "intermediate, long-term)"
        )

    def test_each_phase_has_required_fields(self):
        """Each phase must have phase name, frequency, assessments."""
        protocol = get_monitoring_protocol()
        for phase in protocol["phases"]:
            assert "phase" in phase
            assert "frequency" in phase
            assert "assessments" in phase
            assert len(phase["assessments"]) > 0

    def test_acute_phase_exists(self):
        """Must include an acute monitoring phase."""
        protocol = get_monitoring_protocol()
        phase_names = [p["phase"].lower() for p in protocol["phases"]]
        assert any("acute" in name or "0-30" in name for name in phase_names)

    def test_lifelong_monitoring_phase(self):
        """Must include a long-term/lifelong monitoring phase."""
        protocol = get_monitoring_protocol()
        phase_names = [p["phase"].lower() for p in protocol["phases"]]
        assert any(
            "long-term" in name or "lifelong" in name or ">24" in name
            for name in phase_names
        )

    def test_cbc_in_all_phases(self):
        """Complete blood count should be in all monitoring phases."""
        protocol = get_monitoring_protocol()
        for phase in protocol["phases"]:
            assessments_lower = [a.lower() for a in phase["assessments"]]
            has_cbc = any(
                "complete blood count" in a or "cbc" in a
                for a in assessments_lower
            )
            assert has_cbc, (
                f"Phase '{phase['phase']}' missing CBC assessment"
            )

    def test_urgent_evaluation_triggers(self):
        """Protocol must list urgent evaluation triggers."""
        protocol = get_monitoring_protocol()
        assert "urgent_evaluation_triggers" in protocol
        assert len(protocol["urgent_evaluation_triggers"]) >= 3

    def test_diagnostic_workup(self):
        """Protocol must include diagnostic workup for suspected cases."""
        protocol = get_monitoring_protocol()
        assert "diagnostic_workup_if_suspected" in protocol
        workup = protocol["diagnostic_workup_if_suspected"]
        assert len(workup) >= 3
        # CAR transgene testing is critical
        workup_lower = [w.lower() for w in workup]
        assert any("car transgene" in w for w in workup_lower), (
            "Diagnostic workup must include CAR transgene testing"
        )

    def test_patient_counseling(self):
        """Protocol must include patient counseling points."""
        protocol = get_monitoring_protocol()
        assert "patient_counseling" in protocol
        assert len(protocol["patient_counseling"]) >= 2

    def test_monitoring_protocol_has_references(self):
        """Protocol must cite references."""
        protocol = get_monitoring_protocol()
        assert "references" in protocol
        assert len(protocol["references"]) > 0


# ============================================================================
# Causality framework
# ============================================================================


class TestCausalityFramework:
    """Test the PEI/EMA causality assessment framework."""

    def test_framework_returns_dict(self):
        """Framework must return a dict."""
        framework = get_causality_framework()
        assert isinstance(framework, dict)

    def test_framework_has_criteria(self):
        """Framework must contain assessment criteria."""
        framework = get_causality_framework()
        assert "criteria" in framework
        assert len(framework["criteria"]) >= 4

    def test_each_criterion_has_required_fields(self):
        """Each criterion must have name, description, and weight."""
        framework = get_causality_framework()
        for criterion in framework["criteria"]:
            assert "criterion" in criterion
            assert "description" in criterion
            assert "weight" in criterion

    def test_temporal_relationship_criterion(self):
        """Must include temporal relationship criterion."""
        framework = get_causality_framework()
        criteria_names = [c["criterion"].lower() for c in framework["criteria"]]
        assert any("temporal" in name for name in criteria_names)

    def test_car_transgene_criterion(self):
        """Must include CAR transgene detection criterion."""
        framework = get_causality_framework()
        criteria_names = [c["criterion"].lower() for c in framework["criteria"]]
        assert any("car transgene" in name or "transgene" in name for name in criteria_names)

    def test_insertional_mutagenesis_criterion(self):
        """Must include insertional mutagenesis mechanism criterion."""
        framework = get_causality_framework()
        criteria_names = [c["criterion"].lower() for c in framework["criteria"]]
        assert any("insertional" in name or "mutagenesis" in name for name in criteria_names)

    def test_biological_plausibility_criterion(self):
        """Must include biological plausibility criterion."""
        framework = get_causality_framework()
        criteria_names = [c["criterion"].lower() for c in framework["criteria"]]
        assert any("biological" in name or "plausibility" in name for name in criteria_names)

    def test_overall_assessment(self):
        """Framework must include an overall assessment."""
        framework = get_causality_framework()
        assert "overall_assessment" in framework
        assert len(framework["overall_assessment"]) > 0

    def test_pei_recommendations(self):
        """Framework must include PEI recommendations."""
        framework = get_causality_framework()
        assert "pei_recommendations" in framework
        assert len(framework["pei_recommendations"]) >= 3

    def test_framework_has_references(self):
        """Framework must cite PubMed references."""
        framework = get_causality_framework()
        assert "references" in framework
        assert len(framework["references"]) > 0
        # PEI perspective paper must be cited
        assert any(
            "38442375" in ref for ref in framework["references"]
        ), "Must cite Verdun & Bhoj 2024 (PMID:38442375)"


# ============================================================================
# Regulatory timeline
# ============================================================================


class TestRegulatoryTimeline:
    """Test FDA regulatory timeline integrity."""

    def test_timeline_not_empty(self):
        """Timeline must contain entries."""
        assert len(FDA_REGULATORY_TIMELINE) >= 3

    def test_timeline_chronologically_ordered(self):
        """Entries must be in chronological order."""
        dates = [m.date for m in FDA_REGULATORY_TIMELINE]
        assert dates == sorted(dates), "Timeline must be chronologically ordered"

    def test_boxed_warning_in_timeline(self):
        """January 2024 boxed warning must be in the timeline."""
        boxed_warning = [
            m for m in FDA_REGULATORY_TIMELINE
            if "boxed warning" in m.action.lower()
        ]
        assert len(boxed_warning) >= 1
        # Must be in January 2024
        bw = boxed_warning[0]
        assert bw.date.year == 2024
        assert bw.date.month == 1

    def test_rems_elimination_in_timeline(self):
        """REMS elimination (June 2025) must be in the timeline."""
        rems = [
            m for m in FDA_REGULATORY_TIMELINE
            if "rems" in m.action.lower()
        ]
        assert len(rems) >= 1
        assert rems[0].date.year == 2025

    def test_all_milestones_have_products(self):
        """Every milestone must affect at least one product."""
        for milestone in FDA_REGULATORY_TIMELINE:
            assert len(milestone.products_affected) > 0, (
                f"Milestone on {milestone.date} has no affected products"
            )

    def test_all_milestones_have_agency(self):
        """Every milestone must specify an agency."""
        for milestone in FDA_REGULATORY_TIMELINE:
            assert milestone.agency, (
                f"Milestone on {milestone.date} has no agency"
            )


# ============================================================================
# Malignancy type taxonomy
# ============================================================================


class TestMalignancyTypes:
    """Test malignancy type taxonomy."""

    def test_malignancy_types_list(self):
        """MALIGNANCY_TYPES list must be populated."""
        assert len(MALIGNANCY_TYPES) >= 6

    def test_t_cell_lymphoma_in_types(self):
        """T-cell lymphoma must be in the taxonomy."""
        assert "T-cell lymphoma" in MALIGNANCY_TYPES

    def test_t_cell_leukemia_in_types(self):
        """T-cell leukemia must be in the taxonomy."""
        assert "T-cell leukemia" in MALIGNANCY_TYPES

    def test_mds_in_types(self):
        """MDS must be in the taxonomy."""
        assert "Myelodysplastic syndrome" in MALIGNANCY_TYPES

    def test_aml_in_types(self):
        """AML must be in the taxonomy."""
        assert "Acute myeloid leukemia" in MALIGNANCY_TYPES

    def test_solid_tumor_in_types(self):
        """Solid tumor must be in the taxonomy."""
        assert "Solid tumor" in MALIGNANCY_TYPES


# ============================================================================
# FAERS summary statistics
# ============================================================================


class TestFAERSSummaryStats:
    """Test epidemiological summary data accuracy."""

    def test_total_ae_reports(self):
        """Total AE reports must match published figure."""
        assert FAERS_SUMMARY_STATS["total_cart_ae_reports"] == 12394

    def test_secondary_malignancy_reports(self):
        """Secondary malignancy report count must match."""
        assert FAERS_SUMMARY_STATS["secondary_malignancy_reports"] == 536

    def test_secondary_malignancy_rate(self):
        """4.3% rate (536/12394) must match."""
        assert FAERS_SUMMARY_STATS["secondary_malignancy_rate_pct"] == pytest.approx(4.3, abs=0.1)

    def test_t_cell_malignancy_cases(self):
        """38 T-cell malignancy cases must match."""
        assert FAERS_SUMMARY_STATS["t_cell_malignancy_cases"] == 38

    def test_car_positive_rate(self):
        """7/19 CAR transgene positive must match."""
        assert FAERS_SUMMARY_STATS["t_cell_malignancy_car_positive_tested"] == 19
        assert FAERS_SUMMARY_STATS["t_cell_malignancy_car_positive_confirmed"] == 7

    def test_pct_diagnosed_within_12_months(self):
        """67% diagnosed within 12 months must match."""
        assert FAERS_SUMMARY_STATS["pct_diagnosed_within_12_months"] == pytest.approx(67.0, abs=1.0)


# ============================================================================
# get_all_signals_data()
# ============================================================================


class TestGetAllSignalsData:
    """Test the convenience function for serializable output."""

    def test_returns_dict(self):
        """Must return a dict."""
        data = get_all_signals_data()
        assert isinstance(data, dict)

    def test_has_signals_list(self):
        """Must contain a signals list."""
        data = get_all_signals_data()
        assert "signals" in data
        assert len(data["signals"]) > 0

    def test_has_total_signals_count(self):
        """Must contain a total signals count matching the list."""
        data = get_all_signals_data()
        assert data["total_signals"] == len(data["signals"])

    def test_has_products_with_signals(self):
        """Must list products that have signals."""
        data = get_all_signals_data()
        assert "products_with_signals" in data
        assert len(data["products_with_signals"]) == 6  # all 6 products

    def test_has_regulatory_timeline(self):
        """Must include regulatory timeline."""
        data = get_all_signals_data()
        assert "regulatory_timeline" in data
        assert len(data["regulatory_timeline"]) > 0

    def test_has_monitoring_protocol(self):
        """Must include monitoring protocol."""
        data = get_all_signals_data()
        assert "monitoring_protocol" in data

    def test_has_causality_framework(self):
        """Must include causality framework."""
        data = get_all_signals_data()
        assert "causality_framework" in data

    def test_has_references(self):
        """Must include reference list."""
        data = get_all_signals_data()
        assert "references" in data
        assert len(data["references"]) > 0

    def test_signal_dict_serializable(self):
        """Every signal in the list must be a plain dict (serializable)."""
        data = get_all_signals_data()
        for signal in data["signals"]:
            assert isinstance(signal, dict)
            assert isinstance(signal["malignancy_type"], str)
            assert isinstance(signal["disproportionality_metrics"], dict)

    def test_data_sources_listed(self):
        """Must list data sources."""
        data = get_all_signals_data()
        assert "data_sources" in data
        assert len(data["data_sources"]) >= 2


# ============================================================================
# Edge cases and validation
# ============================================================================


class TestEdgeCases:
    """Test edge cases and input validation."""

    def test_empty_product_name(self):
        """Empty product name should return error."""
        result = assess_secondary_malignancy_risk("")
        assert result["risk_level"] == "unknown"

    def test_none_therapy_type_inferred(self):
        """None therapy_type should be inferred from product metadata."""
        result = assess_secondary_malignancy_risk("Abecma", therapy_type=None)
        assert result["risk_level"] == "elevated"

    def test_disproportionality_metrics_consistent(self):
        """PRR, ROR, EBGM should be roughly consistent across signals.

        For a real signal: PRR and ROR should be similar in magnitude,
        and EBGM should be in a comparable range.
        """
        for signal in KNOWN_SIGNALS:
            dm = signal.disproportionality_metrics
            # PRR and ROR should be within a factor of 2 of each other
            ratio = dm.prr / dm.ror if dm.ror > 0 else float("inf")
            assert 0.5 <= ratio <= 2.0, (
                f"Signal for {signal.product_name}: PRR/ROR ratio {ratio} "
                f"outside expected range"
            )
