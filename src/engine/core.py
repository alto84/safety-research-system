"""
PSPEngine: top-level coordinator for the Predictive Safety Platform.

Ties together all engine components -- orchestrator, reasoning, integration,
knowledge graph, and Safety Index -- into a single cohesive API. The primary
entry point is ``process_patient()``, which runs the full prediction pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.data.graph.knowledge_graph import KnowledgeGraph
from src.data.graph.crs_pathways import get_all_pathways
from src.engine.orchestrator.router import (
    ModelBackend,
    ModelCapability,
    PromptRouter,
    SafetyQuery,
)
from src.engine.orchestrator.normalizer import ResponseNormalizer, SafetyPrediction
from src.engine.orchestrator.ensemble import EnsembleAggregator, EnsemblePrediction
from src.engine.orchestrator.gateway import SecureAPIGateway
from src.engine.reasoning.hypothesis import HypothesisGenerator, MechanisticHypothesis
from src.engine.reasoning.validator import MechanisticValidator, ValidationReport
from src.engine.integration.alerts import Alert, AlertEngine, AlertThresholdConfig
from src.engine.integration.audit import AuditEventType, AuditTrail
from src.safety_index.index import AdverseEventType, SafetyIndex
from src.safety_index.patient.scorer import PatientData, PatientRiskScorer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

@dataclass
class PredictionResult:
    """Complete result from a patient prediction pipeline run.

    Contains every artifact produced during the pipeline: individual model
    predictions, ensemble prediction, Safety Index, mechanistic hypotheses,
    validation reports, and any alerts.

    Attributes:
        patient_id: The patient who was assessed.
        adverse_events: Which adverse events were assessed.
        safety_indices: SafetyIndex for each adverse event.
        ensemble_predictions: Ensemble result for each adverse event.
        individual_predictions: Raw model predictions for each adverse event.
        hypotheses: Mechanistic hypotheses for each adverse event.
        validation_reports: Validation results for each model prediction.
        alerts: Any alerts generated during this assessment.
        session_id: Audit trail session ID for reproducibility.
        pipeline_duration_ms: Total pipeline execution time.
        timestamp: When the pipeline ran.
        metadata: Additional context.
    """

    patient_id: str
    adverse_events: list[AdverseEventType]
    safety_indices: dict[AdverseEventType, SafetyIndex] = field(default_factory=dict)
    ensemble_predictions: dict[AdverseEventType, EnsemblePrediction] = field(default_factory=dict)
    individual_predictions: dict[AdverseEventType, list[SafetyPrediction]] = field(default_factory=dict)
    hypotheses: dict[AdverseEventType, list[MechanisticHypothesis]] = field(default_factory=dict)
    validation_reports: dict[AdverseEventType, list[ValidationReport]] = field(default_factory=dict)
    alerts: list[Alert] = field(default_factory=list)
    session_id: str = ""
    pipeline_duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# PSPEngine
# ---------------------------------------------------------------------------

class PSPEngine:
    """Main entry point for the Predictive Safety Platform.

    Orchestrates the full prediction pipeline:

        1. **Route** the query to optimal foundation model(s).
        2. **Call** each model via the secure gateway.
        3. **Normalize** heterogeneous model responses.
        4. **Validate** predictions against mechanistic biology.
        5. **Ensemble** multi-model predictions with uncertainty.
        6. **Score** the patient-level Safety Index.
        7. **Generate** mechanistic hypotheses.
        8. **Evaluate** alert conditions.
        9. **Audit** the entire pipeline for reproducibility.

    Usage::

        engine = PSPEngine()
        engine.initialize()
        result = await engine.process_patient(patient_data)
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph | None = None,
        gateway: SecureAPIGateway | None = None,
        model_backend: ModelBackend | None = None,
    ) -> None:
        """Initialize the PSP Engine.

        Args:
            knowledge_graph: Pre-loaded knowledge graph. If None, a new one
                is created and populated with default pathways.
            gateway: Secure API gateway for model calls. If None, model calls
                will use the model_backend directly.
            model_backend: Direct model backend (alternative to gateway).
        """
        self._kg = knowledge_graph or KnowledgeGraph()
        self._gateway = gateway
        self._model_backend = model_backend

        # Sub-components (initialized in initialize())
        self._router = PromptRouter()
        self._normalizer = ResponseNormalizer()
        self._ensemble = EnsembleAggregator()
        self._hypothesis_gen: HypothesisGenerator | None = None
        self._validator: MechanisticValidator | None = None
        self._scorer: PatientRiskScorer | None = None
        self._alert_engine = AlertEngine()
        self._audit = AuditTrail()

        self._initialized = False

    def initialize(
        self,
        load_default_pathways: bool = True,
        alert_configs: list[AlertThresholdConfig] | None = None,
    ) -> None:
        """Initialize the engine and its sub-components.

        Must be called before ``process_patient()``.

        Args:
            load_default_pathways: Whether to load CRS/ICANS/HLH pathways
                into the knowledge graph.
            alert_configs: Alert threshold configurations. Defaults to
                standard thresholds for CRS, ICANS, and HLH.
        """
        logger.info("Initializing PSPEngine...")

        # Load knowledge graph pathways
        if load_default_pathways:
            pathways = get_all_pathways()
            for pathway in pathways:
                self._kg.load_pathway(pathway)
            logger.info(
                "Loaded %d pathways (%d nodes, %d edges)",
                len(pathways), self._kg.node_count, self._kg.edge_count,
            )

        # Initialize sub-components
        self._hypothesis_gen = HypothesisGenerator(self._kg)
        self._validator = MechanisticValidator(self._kg)
        self._scorer = PatientRiskScorer(self._kg)

        # Configure alert thresholds
        if alert_configs:
            for config in alert_configs:
                self._alert_engine.configure_thresholds(config)
        else:
            self._configure_default_alerts()

        self._initialized = True
        logger.info(
            "PSPEngine initialized (KG: %d nodes, %d edges)",
            self._kg.node_count, self._kg.edge_count,
        )

    async def process_patient(
        self,
        patient: PatientData,
        adverse_events: list[AdverseEventType] | None = None,
        generate_hypotheses: bool = True,
        validate_predictions: bool = True,
    ) -> PredictionResult:
        """Run the full prediction pipeline for a patient.

        This is the primary API method. It executes all pipeline stages
        and returns a comprehensive result.

        Args:
            patient: The patient data snapshot.
            adverse_events: Which adverse events to assess. Defaults to
                CRS, ICANS, and HLH.
            generate_hypotheses: Whether to generate mechanistic hypotheses.
            validate_predictions: Whether to run mechanistic validation.

        Returns:
            A PredictionResult with all pipeline outputs.

        Raises:
            RuntimeError: If the engine has not been initialized.
        """
        if not self._initialized:
            raise RuntimeError("PSPEngine.initialize() must be called first")

        pipeline_start = time.monotonic()

        if adverse_events is None:
            adverse_events = [
                AdverseEventType.CRS,
                AdverseEventType.ICANS,
                AdverseEventType.HLH,
            ]

        # Start audit session
        session_id = self._audit.start_session(patient.patient_id)

        self._audit.record(
            event_type=AuditEventType.PREDICTION_REQUEST,
            patient_id=patient.patient_id,
            session_id=session_id,
            actor="PSPEngine",
            input_data={
                "biomarker_count": len(patient.biomarkers),
                "hours_since_infusion": patient.hours_since_infusion,
                "adverse_events": [ae.value for ae in adverse_events],
            },
        )

        result = PredictionResult(
            patient_id=patient.patient_id,
            adverse_events=adverse_events,
            session_id=session_id,
        )

        # Process each adverse event
        for ae in adverse_events:
            try:
                await self._process_adverse_event(
                    patient, ae, result, session_id,
                    generate_hypotheses, validate_predictions,
                )
            except Exception:
                logger.exception(
                    "Error processing %s for patient %s",
                    ae.value, patient.patient_id,
                )
                self._audit.record(
                    event_type=AuditEventType.ERROR,
                    patient_id=patient.patient_id,
                    session_id=session_id,
                    actor="PSPEngine",
                    output_data={"adverse_event": ae.value, "error": "pipeline_failure"},
                )

        pipeline_duration = int((time.monotonic() - pipeline_start) * 1000)
        result.pipeline_duration_ms = pipeline_duration

        logger.info(
            "Pipeline complete for patient %s: %d AEs assessed in %dms",
            patient.patient_id, len(adverse_events), pipeline_duration,
        )

        return result

    async def _process_adverse_event(
        self,
        patient: PatientData,
        adverse_event: AdverseEventType,
        result: PredictionResult,
        session_id: str,
        generate_hypotheses: bool,
        validate_predictions: bool,
    ) -> None:
        """Run the pipeline for a single adverse event type."""
        ae_start = time.monotonic()

        # Step 1: Route the query
        query = SafetyQuery(
            patient_id=patient.patient_id,
            query_text=f"Predict {adverse_event.value} risk",
            biomarker_count=len(patient.biomarkers),
            hours_since_infusion=patient.hours_since_infusion,
            requires_mechanistic_reasoning=generate_hypotheses,
            adverse_events=[adverse_event.value],
            context={
                "biomarkers": {k: v for k, v in patient.biomarkers.items()},
                "disease_burden": patient.disease_burden,
                "prior_therapies": patient.prior_therapies,
                "car_t_product": patient.car_t_product,
            },
        )

        try:
            routing_decision = self._router.route(query)
        except RuntimeError:
            logger.warning(
                "No models available for routing; using biomarker-only scoring"
            )
            routing_decision = None

        # Step 2: Call models (if we have a routing decision and backends)
        individual_predictions: list[SafetyPrediction] = []

        if routing_decision and (self._gateway or self._model_backend):
            individual_predictions = await self._call_models(
                query, routing_decision, session_id,
            )

        # Step 3: Validate predictions
        validation_reports: list[ValidationReport] = []
        if validate_predictions and individual_predictions and self._validator:
            for pred in individual_predictions:
                report = self._validator.validate(
                    prediction=pred,
                    biomarkers=patient.biomarkers,
                    hours_since_infusion=patient.hours_since_infusion,
                    biomarker_history=patient.biomarker_history or None,
                )
                validation_reports.append(report)

                self._audit.record(
                    event_type=AuditEventType.MECHANISTIC_VALIDATION,
                    patient_id=patient.patient_id,
                    session_id=session_id,
                    actor="MechanisticValidator",
                    input_data={"model_id": pred.model_id, "risk_score": pred.risk_score},
                    output_data={
                        "result": report.overall_result.value,
                        "confidence": report.overall_confidence,
                        "warnings": report.warnings,
                    },
                )

        result.individual_predictions[adverse_event] = individual_predictions
        result.validation_reports[adverse_event] = validation_reports

        # Step 4: Ensemble predictions
        ensemble_pred: EnsemblePrediction | None = None
        if individual_predictions:
            ensemble_pred = self._ensemble.aggregate(individual_predictions)
            result.ensemble_predictions[adverse_event] = ensemble_pred

            self._audit.record(
                event_type=AuditEventType.ENSEMBLE_AGGREGATION,
                patient_id=patient.patient_id,
                session_id=session_id,
                actor="EnsembleAggregator",
                output_data={
                    "risk_score": ensemble_pred.risk_score,
                    "confidence": ensemble_pred.confidence,
                    "method": ensemble_pred.aggregation_method,
                    "model_agreement": ensemble_pred.model_agreement,
                },
            )

        # Step 5: Compute Safety Index
        model_preds_for_scorer: list[dict[str, float]] | None = None
        if individual_predictions:
            model_preds_for_scorer = [
                p.to_model_prediction_dict() for p in individual_predictions
            ]

        assert self._scorer is not None
        safety_index = self._scorer.compute(
            patient, adverse_event, model_preds_for_scorer,
        )
        result.safety_indices[adverse_event] = safety_index

        self._audit.record(
            event_type=AuditEventType.SAFETY_INDEX_COMPUTATION,
            patient_id=patient.patient_id,
            session_id=session_id,
            actor="PatientRiskScorer",
            output_data={
                "composite_score": safety_index.composite_score,
                "risk_category": safety_index.risk_category.value,
                "trend": safety_index.trend,
                "domain_scores": {
                    ds.domain: ds.score for ds in safety_index.domain_scores
                },
            },
            duration_ms=int((time.monotonic() - ae_start) * 1000),
        )

        # Step 6: Generate hypotheses
        if generate_hypotheses and self._hypothesis_gen:
            hypotheses = self._hypothesis_gen.generate(
                patient_id=patient.patient_id,
                adverse_event=adverse_event,
                biomarkers=patient.biomarkers,
                model_predictions=individual_predictions or None,
            )
            result.hypotheses[adverse_event] = hypotheses

            self._audit.record(
                event_type=AuditEventType.HYPOTHESIS_GENERATION,
                patient_id=patient.patient_id,
                session_id=session_id,
                actor="HypothesisGenerator",
                output_data={
                    "count": len(hypotheses),
                    "titles": [h.title for h in hypotheses],
                },
            )

        # Step 7: Evaluate alerts
        alerts = self._alert_engine.evaluate(safety_index)
        result.alerts.extend(alerts)

        for alert in alerts:
            self._audit.record(
                event_type=AuditEventType.ALERT_GENERATED,
                patient_id=patient.patient_id,
                session_id=session_id,
                actor="AlertEngine",
                output_data={
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.name,
                    "type": alert.alert_type.value,
                    "title": alert.title,
                },
            )

    async def _call_models(
        self,
        query: SafetyQuery,
        routing_decision: Any,
        session_id: str,
    ) -> list[SafetyPrediction]:
        """Call all routed models and normalize their responses."""
        predictions: list[SafetyPrediction] = []

        for model_cap in routing_decision.all_models:
            model_start = time.monotonic()
            prompt = self._router.format_prompt(query, model_cap)

            self._audit.record(
                event_type=AuditEventType.MODEL_CALL,
                patient_id=query.patient_id,
                session_id=session_id,
                actor=model_cap.model_id,
                input_data={"prompt_length": len(prompt)},
                parameters={
                    "model_id": model_cap.model_id,
                    "provider": model_cap.provider,
                },
            )

            try:
                raw_response: dict[str, Any] = {}

                if self._gateway:
                    raw_response = await self._gateway.call_model(
                        model_id=model_cap.model_id,
                        prompt=prompt,
                        patient_id=query.patient_id,
                    )
                elif self._model_backend:
                    raw_response = await self._model_backend.predict(
                        prompt=prompt,
                        model_id=model_cap.model_id,
                    )

                latency_ms = int((time.monotonic() - model_start) * 1000)

                prediction = self._normalizer.normalize(
                    raw_response=raw_response,
                    model_id=model_cap.model_id,
                    patient_id=query.patient_id,
                    adverse_event=query.adverse_events[0] if query.adverse_events else "UNKNOWN",
                    latency_ms=latency_ms,
                )
                predictions.append(prediction)

                self._audit.record(
                    event_type=AuditEventType.MODEL_RESPONSE,
                    patient_id=query.patient_id,
                    session_id=session_id,
                    actor=model_cap.model_id,
                    output_data={
                        "risk_score": prediction.risk_score,
                        "confidence": prediction.confidence,
                    },
                    duration_ms=latency_ms,
                )

            except Exception as exc:
                logger.error(
                    "Model call to %s failed: %s", model_cap.model_id, exc,
                )
                self._audit.record(
                    event_type=AuditEventType.ERROR,
                    patient_id=query.patient_id,
                    session_id=session_id,
                    actor=model_cap.model_id,
                    output_data={"error": str(exc)},
                )

        return predictions

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def _configure_default_alerts(self) -> None:
        """Set up default alert thresholds for CRS, ICANS, and HLH."""
        defaults = [
            AlertThresholdConfig(
                adverse_event=AdverseEventType.CRS,
                warning_threshold=0.4,
                urgent_threshold=0.6,
                critical_threshold=0.8,
                rate_of_change_threshold=0.05,
            ),
            AlertThresholdConfig(
                adverse_event=AdverseEventType.ICANS,
                warning_threshold=0.35,
                urgent_threshold=0.55,
                critical_threshold=0.75,
                rate_of_change_threshold=0.04,
            ),
            AlertThresholdConfig(
                adverse_event=AdverseEventType.HLH,
                warning_threshold=0.3,
                urgent_threshold=0.5,
                critical_threshold=0.7,
                rate_of_change_threshold=0.03,
            ),
        ]
        for config in defaults:
            self._alert_engine.configure_thresholds(config)

    def register_model(self, capability: ModelCapability) -> None:
        """Register a foundation model with the router.

        Args:
            capability: The model's capability descriptor.
        """
        self._router.register_model(capability)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def knowledge_graph(self) -> KnowledgeGraph:
        """Access the knowledge graph."""
        return self._kg

    @property
    def audit_trail(self) -> AuditTrail:
        """Access the audit trail."""
        return self._audit

    @property
    def alert_engine(self) -> AlertEngine:
        """Access the alert engine."""
        return self._alert_engine

    @property
    def is_initialized(self) -> bool:
        """Whether the engine has been initialized."""
        return self._initialized
