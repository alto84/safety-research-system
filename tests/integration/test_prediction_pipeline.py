"""
Integration tests for the full prediction pipeline.

Verifies end-to-end data flow from raw patient data through all scoring
layers to a final PredictionResult. Tests risk stratification accuracy,
alert generation, and graceful handling of missing data.
"""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from tests.conftest import (
    SafetyQuery,
    SafetyPrediction,
    AggregatedRisk,
    SafetyIndex,
    EventRisk,
    AlertLevel,
    Alert,
    PatientData,
    ModelEndpoint,
    TokenCount,
    Urgency,
    CostTier,
    KGNode,
    KGEdge,
)

# Import reference implementations from unit tests
from tests.unit.test_router import PromptRouter
from tests.unit.test_normalizer import ResponseNormalizer
from tests.unit.test_ensemble import EnsembleAggregator
from tests.unit.test_safety_index import SafetyIndexCalculator
from tests.unit.test_alerts import AlertEngine
from tests.unit.test_knowledge_graph import KnowledgeGraph

# Import the SafetyEngine and helper from test_engine_flow
from tests.integration.test_engine_flow import SafetyEngine, make_mock_model_call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def crs_knowledge_graph(crs_pathway_nodes, crs_pathway_edges):
    """A knowledge graph populated with the CRS pathway."""
    kg = KnowledgeGraph()
    for node in crs_pathway_nodes:
        kg.add_node(node)
    for edge in crs_pathway_edges:
        kg.add_edge(edge)
    return kg


def _make_engine(all_endpoints, crs_knowledge_graph, risk_score):
    """Helper to build a SafetyEngine with a fixed model risk score."""
    return SafetyEngine(
        router=PromptRouter(all_endpoints),
        normalizer=ResponseNormalizer(),
        ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
        safety_calculator=SafetyIndexCalculator(),
        alert_engine=AlertEngine(),
        knowledge_graph=crs_knowledge_graph,
        model_call_fn=make_mock_model_call(risk_score),
    )


def _make_il6_engine(all_endpoints, crs_knowledge_graph):
    """Engine that returns risk proportional to baseline IL-6."""
    def il6_call(endpoint, query):
        il6 = query.features.get("il6_pg_ml", 5.0)
        risk = min(1.0, il6 / 100.0)
        return {
            "risk_score": risk,
            "confidence": 0.85,
            "severity_distribution": {
                "grade_1": max(0, 0.8 - risk),
                "grade_2": 0.15,
                "grade_3": min(0.5, risk * 0.5),
                "grade_4": min(0.35, risk * 0.4),
            },
            "time_horizon_hours": max(12, int(72 * (1 - risk))),
            "mechanistic_rationale": f"IL-6 based risk: {risk:.2f}",
            "pathway_references": [],
            "evidence_sources": [],
            "latency_ms": 2000,
            "token_usage": {"prompt_tokens": 2000, "completion_tokens": 300, "total_tokens": 2300},
        }

    return SafetyEngine(
        router=PromptRouter(all_endpoints),
        normalizer=ResponseNormalizer(),
        ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
        safety_calculator=SafetyIndexCalculator(),
        alert_engine=AlertEngine(),
        knowledge_graph=crs_knowledge_graph,
        model_call_fn=il6_call,
    )


# ===========================================================================
# Tests
# ===========================================================================

@pytest.mark.integration
class TestHighRiskPatientPipeline:
    """Patient with known high CRS risk should produce high risk score."""

    def test_high_risk_produces_high_score(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.85)
        si, alert = engine.predict(high_risk_patient)
        assert si.overall_risk > 0.50

    def test_high_risk_triggers_critical_alert(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.85)
        _, alert = engine.predict(high_risk_patient)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_high_risk_intensive_monitoring(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.85)
        si, _ = engine.predict(high_risk_patient)
        protocol = si.monitoring_protocol.lower()
        assert any(kw in protocol for kw in ["icu", "continuous", "q4h"])

    def test_high_risk_detects_biomarkers(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.85)
        si, _ = engine.predict(high_risk_patient)
        assert len(si.key_biomarkers) > 0


@pytest.mark.integration
class TestLowRiskPatientPipeline:
    """Patient with low CRS risk should produce low risk score."""

    def test_low_risk_produces_low_score(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.10)
        si, alert = engine.predict(low_risk_patient)
        assert si.overall_risk < 0.50

    def test_low_risk_no_critical_alert(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.10)
        _, alert = engine.predict(low_risk_patient)
        if alert is not None:
            assert alert.level != AlertLevel.CRITICAL

    def test_low_risk_standard_monitoring(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.10)
        si, _ = engine.predict(low_risk_patient)
        protocol = si.monitoring_protocol.lower()
        assert "standard" in protocol or "q12h" in protocol


@pytest.mark.integration
class TestMissingCytokinesPipeline:
    """Patient with missing cytokine data -- Layer 0 models should still run."""

    def test_missing_cytokines_still_produces_result(self, all_endpoints, crs_knowledge_graph):
        """Even without cytokine data, the engine should produce a SafetyIndex."""
        sparse_patient = PatientData(
            patient_id="TEST-SPARSE-001",
            demographics={"age": 55, "sex": "M"},
            baseline_labs={
                "crp_mg_l": 20.0,
                "ldh_u_l": 300.0,
                # No cytokine data (no IL-6, IFN-gamma, etc.)
            },
            treatment={"product": "axi-cel", "dose_cells": 2e6},
            longitudinal_labs=[],
            genomic_features={},
            comorbidities=[],
            risk_label="unknown",
        )
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.40)
        si, _ = engine.predict(sparse_patient)
        assert si is not None
        assert isinstance(si, SafetyIndex)

    def test_missing_all_labs_still_runs(self, all_endpoints, crs_knowledge_graph):
        """Engine should not crash even with empty labs."""
        minimal_patient = PatientData(
            patient_id="TEST-MINIMAL-001",
            demographics={"age": 50, "sex": "F"},
            baseline_labs={},
            treatment={"product": "tisa-cel"},
            longitudinal_labs=[],
            genomic_features={},
            comorbidities=[],
            risk_label="unknown",
        )
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.30)
        si, _ = engine.predict(minimal_patient)
        assert si is not None


@pytest.mark.integration
class TestCompleteDataPipeline:
    """Patient with complete data should have all layers run."""

    def test_complete_data_all_layers(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        """With complete data, all event types should be scored."""
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.70)
        si, alert = engine.predict(high_risk_patient)

        # All event risks populated
        assert si.crs_risk is not None
        assert si.icans_risk is not None
        assert si.hlh_risk is not None

        # Trajectory populated
        assert len(si.risk_trajectory) > 0

        # Pathways detected from knowledge graph
        assert len(si.contributing_pathways) > 0

    def test_complete_data_audit_trail(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        """Full data should produce a complete audit record."""
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.70)
        engine.predict(high_risk_patient)
        assert len(engine.audit_log) == 1
        record = engine.audit_log[0]
        assert record.patient_id == high_risk_patient.patient_id
        assert len(record.input_features) > 0


@pytest.mark.integration
class TestAlertFiring:
    """Tests that alerts fire correctly based on risk level."""

    def test_critical_alert_for_high_risk(self, all_endpoints, crs_knowledge_graph, high_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.90)
        _, alert = engine.predict(high_risk_patient)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_no_alert_for_very_low_risk(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.05)
        _, alert = engine.predict(low_risk_patient)
        assert alert is None

    def test_info_alert_for_moderate_risk(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        """Moderate risk should produce at most an INFO-level alert."""
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.35)
        _, alert = engine.predict(medium_risk_patient)
        if alert is not None:
            assert alert.level in (AlertLevel.INFO, AlertLevel.WATCH)


@pytest.mark.integration
class TestNoFalseAlerts:
    """Verify no false alerts for low-risk patients."""

    def test_low_risk_patient_no_critical(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.10)
        _, alert = engine.predict(low_risk_patient)
        if alert is not None:
            assert alert.level != AlertLevel.CRITICAL

    def test_low_risk_patient_no_warning(self, all_endpoints, crs_knowledge_graph, low_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.05)
        _, alert = engine.predict(low_risk_patient)
        if alert is not None:
            assert alert.level not in (AlertLevel.CRITICAL, AlertLevel.WARNING)


@pytest.mark.integration
class TestFullPipelineOutputStructure:
    """Tests the full pipeline from raw patient data to PredictionResult."""

    def test_result_has_safety_index(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.50)
        si, _ = engine.predict(medium_risk_patient)
        assert isinstance(si, SafetyIndex)
        assert 0.0 <= si.overall_risk <= 1.0

    def test_result_risk_trajectory_populated(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.50)
        si, _ = engine.predict(medium_risk_patient)
        assert len(si.risk_trajectory) > 0

    def test_result_has_confidence_interval(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.50)
        si, _ = engine.predict(medium_risk_patient)
        assert isinstance(si.confidence_interval, tuple)
        assert len(si.confidence_interval) == 2

    def test_result_has_prediction_id(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.50)
        si, _ = engine.predict(medium_risk_patient)
        assert si.prediction_id is not None
        assert len(si.prediction_id) > 0

    def test_result_has_timestamp(self, all_endpoints, crs_knowledge_graph, medium_risk_patient):
        engine = _make_engine(all_endpoints, crs_knowledge_graph, 0.50)
        si, _ = engine.predict(medium_risk_patient)
        assert si.timestamp is not None


@pytest.mark.integration
class TestRiskMonotonicity:
    """Tests that the pipeline preserves risk ordering across patients."""

    def test_il6_proportional_risk(self, all_endpoints, crs_knowledge_graph, low_risk_patient, high_risk_patient):
        """Higher baseline IL-6 should produce higher risk scores."""
        engine = _make_il6_engine(all_endpoints, crs_knowledge_graph)
        si_low, _ = engine.predict(low_risk_patient)
        si_high, _ = engine.predict(high_risk_patient)
        assert si_high.overall_risk > si_low.overall_risk

    def test_medium_between_low_and_high(self, all_endpoints, crs_knowledge_graph,
                                         low_risk_patient, medium_risk_patient, high_risk_patient):
        """Medium risk patient should score between low and high."""
        engine = _make_il6_engine(all_endpoints, crs_knowledge_graph)
        si_low, _ = engine.predict(low_risk_patient)
        si_med, _ = engine.predict(medium_risk_patient)
        si_high, _ = engine.predict(high_risk_patient)
        assert si_low.overall_risk <= si_med.overall_risk <= si_high.overall_risk
