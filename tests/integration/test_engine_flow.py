"""
Integration tests for PSPEngine — end-to-end flow from patient data to Safety Index.

These tests verify that the complete prediction pipeline works correctly:
PatientData -> PromptRouter -> Model Inference -> Normalizer -> Ensemble -> SafetyIndex -> Alerts
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field
import uuid

from tests.conftest import (
    SafetyQuery,
    SafetyPrediction,
    AggregatedRisk,
    SafetyIndex,
    EventRisk,
    AuditRecord,
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


# ---------------------------------------------------------------------------
# PSPEngine — orchestrates the full prediction pipeline
# ---------------------------------------------------------------------------

class PSPEngine:
    """Core PSP prediction engine, integrating all components."""

    def __init__(
        self,
        router: PromptRouter,
        normalizer: ResponseNormalizer,
        ensemble: EnsembleAggregator,
        safety_calculator: SafetyIndexCalculator,
        alert_engine: AlertEngine,
        knowledge_graph: KnowledgeGraph,
        model_call_fn=None,
    ):
        self.router = router
        self.normalizer = normalizer
        self.ensemble = ensemble
        self.safety_calculator = safety_calculator
        self.alert_engine = alert_engine
        self.kg = knowledge_graph
        self._model_call_fn = model_call_fn or self._default_model_call
        self._audit_log: list[AuditRecord] = []

    def _default_model_call(self, endpoint: ModelEndpoint, query: SafetyQuery) -> dict:
        """Default mock model call. In production, this calls the actual API."""
        raise NotImplementedError("Model call function must be provided.")

    def predict(self, patient: PatientData, domain: str = "crs") -> tuple[SafetyIndex, Alert | None]:
        """Run the full prediction pipeline for a patient.

        Returns (SafetyIndex, optional Alert).
        """
        # 1. Build queries for each event type
        queries = self._build_queries(patient, domain)

        # 2. For each event type, route to models and collect predictions
        event_aggregations = {}
        all_raw_outputs = []

        for event_type, query in queries.items():
            predictions = self._collect_predictions(query)
            all_raw_outputs.extend(predictions)
            event_aggregations[event_type] = self.ensemble.aggregate(predictions)

        # 3. Query knowledge graph for pathways
        pathways = []
        if self.kg.get_node("node:cart_cell"):
            found = self.kg.find_relevant_pathways("node:cart_cell", "Adverse_Event")
            pathways = ["/".join(p) for p in found] if found else []

        # 4. Compute Safety Index
        crs_agg = event_aggregations.get("crs", AggregatedRisk(risk_score=0.0, confidence_interval=(0, 0)))
        icans_agg = event_aggregations.get("icans", AggregatedRisk(risk_score=0.0, confidence_interval=(0, 0)))
        hlh_agg = event_aggregations.get("hlh", AggregatedRisk(risk_score=0.0, confidence_interval=(0, 0)))

        model_agreements = [1.0 - agg.disagreement_score for agg in event_aggregations.values()]
        avg_agreement = sum(model_agreements) / len(model_agreements) if model_agreements else 0.5

        biomarkers = self._extract_key_biomarkers(patient)

        safety_index = self.safety_calculator.compute(
            crs_agg=crs_agg,
            icans_agg=icans_agg,
            hlh_agg=hlh_agg,
            model_agreement=avg_agreement,
            pathways=pathways,
            biomarkers=biomarkers,
            model_versions={"claude-opus-4": "4.0", "gpt-5.2": "5.2", "gemini-3": "3.0"},
            graph_version="kg-v1.2.0",
            patient_id=patient.patient_id,
        )

        # 5. Evaluate alerts
        alert = self.alert_engine.evaluate(patient.patient_id, crs_agg)

        # 6. Record audit trail
        self._record_audit(patient, crs_agg, all_raw_outputs, safety_index)

        return safety_index, alert

    def _build_queries(self, patient: PatientData, domain: str) -> dict[str, SafetyQuery]:
        """Build SafetyQueries for each event type."""
        event_types = ["crs", "icans", "hlh"]
        queries = {}
        for et in event_types:
            queries[et] = SafetyQuery(
                patient_id=patient.patient_id,
                domain=et,
                query_text=f"Assess {et.upper()} risk for patient {patient.patient_id}.",
                urgency=Urgency.BATCH,
                cost_tier=CostTier.MEDIUM,
                features=patient.baseline_labs,
            )
        return queries

    def _collect_predictions(self, query: SafetyQuery) -> list[SafetyPrediction]:
        """Route query to models, collect and normalize responses."""
        predictions = []
        # Call each available model
        for model_id, endpoint in self.router.available_models.items():
            try:
                raw = self._model_call_fn(endpoint, query)
                pred = self.normalizer.normalize(raw, model_id, raw.get("latency_ms", 0))
                predictions.append(pred)
            except Exception:
                continue  # Skip failed models
        return predictions

    def _extract_key_biomarkers(self, patient: PatientData) -> list[str]:
        """Extract notable biomarker features from patient data."""
        biomarkers = []
        labs = patient.baseline_labs
        if labs.get("il6_pg_ml", 0) > 20:
            biomarkers.append("il6_elevated")
        if labs.get("ferritin_ng_ml", 0) > 1000:
            biomarkers.append("ferritin_elevated")
        if labs.get("crp_mg_l", 0) > 50:
            biomarkers.append("crp_elevated")
        if labs.get("ldh_u_l", 0) > 400:
            biomarkers.append("ldh_elevated")
        if labs.get("platelets_k_ul", 0) < 100:
            biomarkers.append("thrombocytopenia")
        return biomarkers

    def _record_audit(self, patient, crs_agg, raw_outputs, safety_index):
        """Record an audit entry."""
        record = AuditRecord(
            prediction_id=safety_index.prediction_id,
            timestamp=safety_index.timestamp,
            patient_id=patient.patient_id,
            input_features=patient.baseline_labs,
            graph_snapshot_version="kg-v1.2.0",
            model_versions=safety_index.model_versions,
            prompt_router_decision={"method": "complexity_routing"},
            raw_model_outputs=[str(o) for o in raw_outputs],
            ensemble_weights=crs_agg.contributing_models,
            calibration_params={"platt_a": -1.0, "platt_b": 0.0},
            final_prediction=crs_agg,
            mechanistic_explanation=safety_index.primary_mechanism,
            pathway_trace=safety_index.contributing_pathways,
            confidence_interval=safety_index.confidence_interval,
            disagreement_score=crs_agg.disagreement_score,
            similar_historical_outcomes=[],
        )
        self._audit_log.append(record)

    @property
    def audit_log(self) -> list[AuditRecord]:
        return self._audit_log


# ---------------------------------------------------------------------------
# Helper: mock model call factory
# ---------------------------------------------------------------------------

def make_mock_model_call(risk_score: float, confidence: float = 0.85):
    """Create a model call function that returns a fixed response."""
    def model_call(endpoint: ModelEndpoint, query: SafetyQuery) -> dict:
        return {
            "risk_score": risk_score,
            "confidence": confidence,
            "severity_distribution": {
                "grade_1": max(0, 0.8 - risk_score),
                "grade_2": 0.15,
                "grade_3": min(0.5, risk_score * 0.5),
                "grade_4": min(0.35, risk_score * 0.4),
            },
            "time_horizon_hours": max(12, int(72 * (1 - risk_score))),
            "mechanistic_rationale": f"Risk assessment: {risk_score:.2f}",
            "pathway_references": [],
            "evidence_sources": [],
            "latency_ms": 2000,
            "token_usage": {"prompt_tokens": 2000, "completion_tokens": 300, "total_tokens": 2300},
        }
    return model_call


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def crs_knowledge_graph(crs_pathway_nodes, crs_pathway_edges):
    kg = KnowledgeGraph()
    for node in crs_pathway_nodes:
        kg.add_node(node)
    for edge in crs_pathway_edges:
        kg.add_edge(edge)
    return kg


@pytest.fixture
def engine_low_risk(all_endpoints, crs_knowledge_graph):
    """PSP engine configured with mock models returning low-risk scores."""
    return PSPEngine(
        router=PromptRouter(all_endpoints),
        normalizer=ResponseNormalizer(),
        ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
        safety_calculator=SafetyIndexCalculator(),
        alert_engine=AlertEngine(),
        knowledge_graph=crs_knowledge_graph,
        model_call_fn=make_mock_model_call(0.12),
    )


@pytest.fixture
def engine_high_risk(all_endpoints, crs_knowledge_graph):
    """PSP engine configured with mock models returning high-risk scores."""
    return PSPEngine(
        router=PromptRouter(all_endpoints),
        normalizer=ResponseNormalizer(),
        ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
        safety_calculator=SafetyIndexCalculator(),
        alert_engine=AlertEngine(),
        knowledge_graph=crs_knowledge_graph,
        model_call_fn=make_mock_model_call(0.82),
    )


@pytest.fixture
def engine_failing_models(all_endpoints, crs_knowledge_graph):
    """PSP engine where some models fail (return invalid data)."""
    call_count = {"n": 0}

    def flaky_model_call(endpoint: ModelEndpoint, query: SafetyQuery) -> dict:
        call_count["n"] += 1
        if call_count["n"] % 3 == 0:
            raise ConnectionError("Model API unavailable")
        return {
            "risk_score": 0.50,
            "confidence": 0.70,
            "severity_distribution": {"grade_1": 0.3, "grade_2": 0.3, "grade_3": 0.3, "grade_4": 0.1},
            "time_horizon_hours": 48,
            "mechanistic_rationale": "Moderate risk.",
            "pathway_references": [],
            "evidence_sources": [],
            "latency_ms": 1500,
            "token_usage": {"prompt_tokens": 2000, "completion_tokens": 300, "total_tokens": 2300},
        }

    return PSPEngine(
        router=PromptRouter(all_endpoints),
        normalizer=ResponseNormalizer(),
        ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
        safety_calculator=SafetyIndexCalculator(),
        alert_engine=AlertEngine(),
        knowledge_graph=crs_knowledge_graph,
        model_call_fn=flaky_model_call,
    )


# ===========================================================================
# Tests
# ===========================================================================

class TestLowRiskPatientFlow:
    """End-to-end flow for a low-risk patient."""

    def test_produces_safety_index(self, engine_low_risk, low_risk_patient):
        si, alert = engine_low_risk.predict(low_risk_patient)
        assert si is not None
        assert isinstance(si, SafetyIndex)

    def test_risk_score_is_low(self, engine_low_risk, low_risk_patient):
        si, _ = engine_low_risk.predict(low_risk_patient)
        assert si.overall_risk < 0.50

    def test_no_critical_alert(self, engine_low_risk, low_risk_patient):
        _, alert = engine_low_risk.predict(low_risk_patient)
        if alert is not None:
            assert alert.level != AlertLevel.CRITICAL

    def test_audit_record_created(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        assert len(engine_low_risk.audit_log) == 1
        record = engine_low_risk.audit_log[0]
        assert record.patient_id == low_risk_patient.patient_id

    def test_event_risks_populated(self, engine_low_risk, low_risk_patient):
        si, _ = engine_low_risk.predict(low_risk_patient)
        assert si.crs_risk is not None
        assert si.icans_risk is not None
        assert si.hlh_risk is not None

    def test_trajectory_populated(self, engine_low_risk, low_risk_patient):
        si, _ = engine_low_risk.predict(low_risk_patient)
        assert len(si.risk_trajectory) > 0


class TestHighRiskPatientFlow:
    """End-to-end flow for a high-risk patient."""

    def test_produces_safety_index(self, engine_high_risk, high_risk_patient):
        si, alert = engine_high_risk.predict(high_risk_patient)
        assert si is not None

    def test_risk_score_is_high(self, engine_high_risk, high_risk_patient):
        si, _ = engine_high_risk.predict(high_risk_patient)
        assert si.overall_risk > 0.50

    def test_critical_alert_generated(self, engine_high_risk, high_risk_patient):
        _, alert = engine_high_risk.predict(high_risk_patient)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_intensive_monitoring_recommended(self, engine_high_risk, high_risk_patient):
        si, _ = engine_high_risk.predict(high_risk_patient)
        protocol = si.monitoring_protocol.lower()
        assert "icu" in protocol or "continuous" in protocol or "q4h" in protocol

    def test_biomarkers_detected(self, engine_high_risk, high_risk_patient):
        si, _ = engine_high_risk.predict(high_risk_patient)
        assert len(si.key_biomarkers) > 0

    def test_audit_includes_model_versions(self, engine_high_risk, high_risk_patient):
        engine_high_risk.predict(high_risk_patient)
        record = engine_high_risk.audit_log[0]
        assert len(record.model_versions) > 0


class TestRiskOrdering:
    """Tests that the engine produces correct relative risk ordering."""

    def test_high_risk_patient_scores_higher_than_low(self, all_endpoints, crs_knowledge_graph, low_risk_patient, high_risk_patient):
        """Verify risk monotonicity: high-risk patient should score higher."""
        # Engine that returns risk proportional to baseline IL-6
        def il6_based_call(endpoint, query):
            il6 = query.features.get("il6_pg_ml", 5.0)
            risk = min(1.0, il6 / 100.0)  # Scale: 100 pg/mL -> 1.0
            return {
                "risk_score": risk,
                "confidence": 0.85,
                "severity_distribution": {"grade_1": 0.3, "grade_2": 0.3, "grade_3": 0.2, "grade_4": 0.2},
                "time_horizon_hours": 48,
                "mechanistic_rationale": "IL-6 based",
                "pathway_references": [], "evidence_sources": [],
                "latency_ms": 2000,
                "token_usage": {"prompt_tokens": 2000, "completion_tokens": 300, "total_tokens": 2300},
            }

        engine = PSPEngine(
            router=PromptRouter(all_endpoints),
            normalizer=ResponseNormalizer(),
            ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
            safety_calculator=SafetyIndexCalculator(),
            alert_engine=AlertEngine(),
            knowledge_graph=crs_knowledge_graph,
            model_call_fn=il6_based_call,
        )

        si_low, _ = engine.predict(low_risk_patient)
        si_high, _ = engine.predict(high_risk_patient)
        assert si_high.overall_risk > si_low.overall_risk


class TestModelFailureResilience:
    """Tests that the engine handles model failures gracefully."""

    def test_produces_result_despite_failures(self, engine_failing_models, medium_risk_patient):
        """Engine should still produce a result when some models fail."""
        si, alert = engine_failing_models.predict(medium_risk_patient)
        assert si is not None
        assert isinstance(si, SafetyIndex)

    def test_audit_log_records_despite_failures(self, engine_failing_models, medium_risk_patient):
        engine_failing_models.predict(medium_risk_patient)
        assert len(engine_failing_models.audit_log) >= 1


class TestKnowledgeGraphIntegration:
    """Tests that the knowledge graph is consulted during prediction."""

    def test_pathways_included_in_safety_index(self, engine_low_risk, low_risk_patient):
        si, _ = engine_low_risk.predict(low_risk_patient)
        # The KG has a path from cart_cell to CRS, so pathways should be populated
        assert len(si.contributing_pathways) > 0

    def test_empty_kg_still_works(self, all_endpoints, low_risk_patient):
        """Engine should function even without KG data."""
        engine = PSPEngine(
            router=PromptRouter(all_endpoints),
            normalizer=ResponseNormalizer(),
            ensemble=EnsembleAggregator(platt_a=-4.0, platt_b=2.0),
            safety_calculator=SafetyIndexCalculator(),
            alert_engine=AlertEngine(),
            knowledge_graph=KnowledgeGraph(),  # Empty
            model_call_fn=make_mock_model_call(0.30),
        )
        si, _ = engine.predict(low_risk_patient)
        assert si is not None


class TestAuditCompleteness:
    """Tests that audit records contain all required fields."""

    def test_audit_has_prediction_id(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        record = engine_low_risk.audit_log[0]
        assert record.prediction_id is not None and len(record.prediction_id) > 0

    def test_audit_has_timestamp(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        record = engine_low_risk.audit_log[0]
        assert record.timestamp is not None

    def test_audit_has_input_features(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        record = engine_low_risk.audit_log[0]
        assert len(record.input_features) > 0
        assert "il6_pg_ml" in record.input_features

    def test_audit_has_model_outputs(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        record = engine_low_risk.audit_log[0]
        assert len(record.raw_model_outputs) > 0

    def test_audit_has_confidence_interval(self, engine_low_risk, low_risk_patient):
        engine_low_risk.predict(low_risk_patient)
        record = engine_low_risk.audit_log[0]
        assert isinstance(record.confidence_interval, tuple)
        assert len(record.confidence_interval) == 2
