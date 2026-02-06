"""
Tests for SafetyIndex computation — score ranges, mechanistic consistency,
and structural validity of the composite risk output.

The SafetyIndex is the primary PSP output: a composite, mechanistically-grounded
risk score for a patient at a point in time.
"""

import pytest
import math
from datetime import datetime, timedelta, timezone

from tests.conftest import (
    SafetyIndex,
    EventRisk,
    AggregatedRisk,
    PatientData,
)


# ---------------------------------------------------------------------------
# SafetyIndexCalculator reference implementation
# ---------------------------------------------------------------------------

class SafetyIndexCalculator:
    """Computes the SafetyIndex from aggregated model predictions and patient context."""

    # Trajectory time points (hours post-infusion)
    TRAJECTORY_HOURS = [1, 4, 12, 24, 48, 72]

    # Evidence strength thresholds
    EVIDENCE_THRESHOLDS = {
        "strong": 0.85,     # model_agreement >= 0.85
        "moderate": 0.70,   # model_agreement >= 0.70
        "limited": 0.0,     # everything else
    }

    # Monitoring protocol mapping
    MONITORING_PROTOCOLS = {
        (0.0, 0.3): "Standard q12h vitals and daily cytokine panel",
        (0.3, 0.6): "Enhanced q8h vitals, q12h cytokine panel, daily neurotox assessment",
        (0.6, 0.8): "Intensive q4h vitals, q8h cytokine panel, continuous telemetry",
        (0.8, 1.01): "Continuous vitals, q4h cytokine panel, ICU standby",
    }

    def compute(
        self,
        crs_agg: AggregatedRisk,
        icans_agg: AggregatedRisk,
        hlh_agg: AggregatedRisk,
        model_agreement: float,
        pathways: list,
        biomarkers: list,
        model_versions: dict,
        graph_version: str,
        patient_id: str = "",
    ) -> SafetyIndex:
        """Compute the SafetyIndex from per-event aggregated risks."""
        # Overall risk: max of individual event risks (conservative)
        overall = max(crs_agg.risk_score, icans_agg.risk_score, hlh_agg.risk_score)
        overall = max(0.0, min(1.0, overall))

        # Event-specific risks
        crs_risk = self._build_event_risk(crs_agg, "crs")
        icans_risk = self._build_event_risk(icans_agg, "icans")
        hlh_risk = self._build_event_risk(hlh_agg, "hlh")

        # Risk trajectory (simplified: linear interpolation toward peak)
        peak_time = self._estimate_peak_time(overall)
        trajectory = self._build_trajectory(overall, peak_time)

        # Evidence and monitoring
        evidence_strength = self._assess_evidence(model_agreement)
        monitoring = self._select_monitoring(overall)
        intervention = self._select_intervention(overall)

        # Primary mechanism from pathways
        primary_mechanism = pathways[0] if pathways else "Unknown"

        # Confidence interval from most significant event
        ci = crs_agg.confidence_interval  # CRS is primary focus

        import uuid
        return SafetyIndex(
            overall_risk=overall,
            crs_risk=crs_risk,
            icans_risk=icans_risk,
            hlh_risk=hlh_risk,
            risk_trajectory=trajectory,
            peak_risk_time=peak_time,
            primary_mechanism=primary_mechanism,
            contributing_pathways=pathways,
            key_biomarkers=biomarkers[:5],  # Top 5
            confidence_interval=ci,
            model_agreement=model_agreement,
            evidence_strength=evidence_strength,
            monitoring_protocol=monitoring,
            intervention_readiness=intervention,
            prediction_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            model_versions=model_versions,
            graph_version=graph_version,
        )

    def _build_event_risk(self, agg: AggregatedRisk, event_type: str) -> EventRisk:
        """Build an EventRisk from an AggregatedRisk."""
        # Default severity distributions by event type
        default_severity = {
            "crs": {"grade_1": 0.40, "grade_2": 0.30, "grade_3": 0.20, "grade_4": 0.10},
            "icans": {"grade_1": 0.35, "grade_2": 0.30, "grade_3": 0.25, "grade_4": 0.10},
            "hlh": {"grade_1": 0.0, "grade_2": 0.0, "grade_3": 0.55, "grade_4": 0.45},
        }
        # Default onset times (hours)
        default_onset = {"crs": 48, "icans": 120, "hlh": 168}

        onset_hours = default_onset.get(event_type, 72)
        onset = timedelta(hours=onset_hours)
        onset_ci = (timedelta(hours=onset_hours * 0.5), timedelta(hours=onset_hours * 1.5))

        return EventRisk(
            probability=agg.risk_score,
            severity_distribution=default_severity.get(event_type, {}),
            expected_onset=onset,
            onset_ci=onset_ci,
            mechanistic_path=[],
        )

    def _estimate_peak_time(self, overall_risk: float) -> timedelta:
        """Higher risk patients tend to peak earlier."""
        if overall_risk > 0.7:
            return timedelta(hours=24)
        elif overall_risk > 0.4:
            return timedelta(hours=48)
        else:
            return timedelta(hours=72)

    def _build_trajectory(self, overall: float, peak_time: timedelta) -> list:
        """Build risk trajectory across standard time points."""
        peak_hours = peak_time.total_seconds() / 3600
        trajectory = []
        for h in self.TRAJECTORY_HOURS:
            if h <= peak_hours:
                # Rising phase
                t = overall * (h / peak_hours) if peak_hours > 0 else overall
            else:
                # Declining phase
                decline = 0.9 ** ((h - peak_hours) / 12)
                t = overall * decline
            trajectory.append(round(max(0.0, min(1.0, t)), 4))
        return trajectory

    def _assess_evidence(self, model_agreement: float) -> str:
        """Map model agreement to evidence strength label."""
        if model_agreement >= self.EVIDENCE_THRESHOLDS["strong"]:
            return "strong"
        elif model_agreement >= self.EVIDENCE_THRESHOLDS["moderate"]:
            return "moderate"
        return "limited"

    def _select_monitoring(self, overall: float) -> str:
        """Select monitoring protocol based on overall risk."""
        for (lo, hi), protocol in self.MONITORING_PROTOCOLS.items():
            if lo <= overall < hi:
                return protocol
        return self.MONITORING_PROTOCOLS[(0.8, 1.01)]

    def _select_intervention(self, overall: float) -> str:
        """Select intervention readiness based on overall risk."""
        if overall >= 0.7:
            return "Tocilizumab and dexamethasone at bedside, vasopressor access"
        elif overall >= 0.4:
            return "Tocilizumab available on unit, dexamethasone on standby"
        return "Tocilizumab available per institutional protocol"


# ===========================================================================
# Tests
# ===========================================================================

@pytest.fixture
def calculator():
    return SafetyIndexCalculator()


@pytest.fixture
def low_crs_agg():
    return AggregatedRisk(risk_score=0.10, confidence_interval=(0.05, 0.18), disagreement_score=0.03)


@pytest.fixture
def low_icans_agg():
    return AggregatedRisk(risk_score=0.05, confidence_interval=(0.02, 0.10), disagreement_score=0.02)


@pytest.fixture
def low_hlh_agg():
    return AggregatedRisk(risk_score=0.02, confidence_interval=(0.01, 0.05), disagreement_score=0.01)


@pytest.fixture
def high_crs_agg():
    return AggregatedRisk(risk_score=0.82, confidence_interval=(0.72, 0.90), disagreement_score=0.06)


@pytest.fixture
def high_icans_agg():
    return AggregatedRisk(risk_score=0.45, confidence_interval=(0.30, 0.58), disagreement_score=0.08)


@pytest.fixture
def high_hlh_agg():
    return AggregatedRisk(risk_score=0.25, confidence_interval=(0.15, 0.38), disagreement_score=0.05)


class TestOverallRiskComputation:
    """Tests for the overall_risk field (max of event-specific risks)."""

    def test_overall_risk_is_max_of_events(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.92,
            pathways=["pathway:crs_grade1_self_limiting"],
            biomarkers=["il6_normal"],
            model_versions={"claude-opus-4": "4.0"},
            graph_version="kg-v1.2.0",
        )
        assert si.overall_risk == pytest.approx(0.10)  # Max of 0.10, 0.05, 0.02

    def test_high_risk_overall(self, calculator, high_crs_agg, high_icans_agg, high_hlh_agg):
        si = calculator.compute(
            high_crs_agg, high_icans_agg, high_hlh_agg,
            model_agreement=0.88,
            pathways=["pathway:il6_trans_signaling"],
            biomarkers=["il6_critical"],
            model_versions={"claude-opus-4": "4.0"},
            graph_version="kg-v1.2.0",
        )
        assert si.overall_risk == pytest.approx(0.82)

    def test_overall_risk_bounded_0_to_1(self, calculator):
        extreme = AggregatedRisk(risk_score=1.5, confidence_interval=(0.0, 1.0))
        zero = AggregatedRisk(risk_score=0.0, confidence_interval=(0.0, 0.0))
        si = calculator.compute(
            extreme, zero, zero,
            model_agreement=0.5,
            pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert 0.0 <= si.overall_risk <= 1.0


class TestRiskTrajectory:
    """Tests for the risk_trajectory field."""

    def test_trajectory_has_correct_length(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert len(si.risk_trajectory) == len(SafetyIndexCalculator.TRAJECTORY_HOURS)

    def test_trajectory_values_in_valid_range(self, calculator, high_crs_agg, high_icans_agg, high_hlh_agg):
        si = calculator.compute(
            high_crs_agg, high_icans_agg, high_hlh_agg,
            model_agreement=0.88, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        for val in si.risk_trajectory:
            assert 0.0 <= val <= 1.0

    def test_high_risk_peaks_early(self, calculator, high_crs_agg, high_icans_agg, high_hlh_agg):
        si = calculator.compute(
            high_crs_agg, high_icans_agg, high_hlh_agg,
            model_agreement=0.88, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        # Overall 0.82 -> peak at 24h, which is TRAJECTORY_HOURS index 3
        # Values should rise then fall
        assert si.peak_risk_time == timedelta(hours=24)

    def test_low_risk_peaks_late(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert si.peak_risk_time == timedelta(hours=72)


class TestEvidenceStrength:
    """Tests for evidence_strength classification."""

    def test_high_agreement_strong(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.92, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert si.evidence_strength == "strong"

    def test_medium_agreement_moderate(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.75, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert si.evidence_strength == "moderate"

    def test_low_agreement_limited(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.55, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert si.evidence_strength == "limited"


class TestMonitoringProtocol:
    """Tests for monitoring protocol selection based on risk level."""

    def test_low_risk_standard_monitoring(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert "q12h" in si.monitoring_protocol.lower() or "standard" in si.monitoring_protocol.lower()

    def test_high_risk_intensive_monitoring(self, calculator, high_crs_agg, high_icans_agg, high_hlh_agg):
        si = calculator.compute(
            high_crs_agg, high_icans_agg, high_hlh_agg,
            model_agreement=0.88, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert "icu" in si.monitoring_protocol.lower() or "continuous" in si.monitoring_protocol.lower()


class TestMechanisticConsistency:
    """Tests ensuring mechanistic fields are populated correctly."""

    def test_primary_mechanism_from_pathways(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9,
            pathways=["pathway:crs_grade1_self_limiting", "pathway:mild_inflammation"],
            biomarkers=["il6_normal"],
            model_versions={}, graph_version="test",
        )
        assert si.primary_mechanism == "pathway:crs_grade1_self_limiting"

    def test_empty_pathways_unknown_mechanism(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9,
            pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        assert si.primary_mechanism == "Unknown"

    def test_biomarkers_limited_to_top5(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        many_biomarkers = [f"biomarker_{i}" for i in range(10)]
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9,
            pathways=["p1"], biomarkers=many_biomarkers,
            model_versions={}, graph_version="test",
        )
        assert len(si.key_biomarkers) == 5


class TestStructuralValidity:
    """Tests that the SafetyIndex structure is complete and valid."""

    def test_all_required_fields_present(self, calculator, low_crs_agg, low_icans_agg, low_hlh_agg):
        si = calculator.compute(
            low_crs_agg, low_icans_agg, low_hlh_agg,
            model_agreement=0.9, pathways=["p1"], biomarkers=["b1"],
            model_versions={"claude": "4.0"}, graph_version="kg-v1.0",
        )
        assert si.prediction_id is not None
        assert si.timestamp is not None
        assert si.crs_risk is not None
        assert si.icans_risk is not None
        assert si.hlh_risk is not None
        assert isinstance(si.confidence_interval, tuple)
        assert len(si.confidence_interval) == 2

    def test_event_risk_probabilities_valid(self, calculator, high_crs_agg, high_icans_agg, high_hlh_agg):
        si = calculator.compute(
            high_crs_agg, high_icans_agg, high_hlh_agg,
            model_agreement=0.88, pathways=[], biomarkers=[],
            model_versions={}, graph_version="test",
        )
        for event_risk in [si.crs_risk, si.icans_risk, si.hlh_risk]:
            assert 0.0 <= event_risk.probability <= 1.0
            assert sum(event_risk.severity_distribution.values()) == pytest.approx(1.0, abs=0.01)
            assert event_risk.expected_onset.total_seconds() > 0
            assert event_risk.onset_ci[0] <= event_risk.onset_ci[1]
