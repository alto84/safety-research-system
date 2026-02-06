"""
Hypothesis generator for mechanistic safety hypotheses.

Uses the knowledge graph and foundation model predictions to generate
testable hypotheses about *why* a patient is at risk, identifying the
specific biological mechanisms (signaling cascades, cytokine amplification
loops, pathway cross-talk) that drive the predicted adverse event.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from src.data.graph.knowledge_graph import KnowledgeGraph
from src.data.graph.schema import EdgeType, NodeType
from src.engine.orchestrator.normalizer import SafetyPrediction
from src.safety_index.index import AdverseEventType

logger = logging.getLogger(__name__)


class EvidenceLevel(Enum):
    """Strength of evidence supporting a hypothesis."""

    STRONG = "strong"             # Supported by KG pathway + model + biomarkers
    MODERATE = "moderate"         # Supported by KG pathway + one of model/biomarkers
    WEAK = "weak"                 # Supported by model alone or partial KG match
    SPECULATIVE = "speculative"   # Novel hypothesis from model reasoning only


@dataclass
class MechanisticHypothesis:
    """A mechanistic hypothesis explaining a predicted adverse event.

    Describes a specific biological pathway or mechanism that the system
    believes is contributing to the patient's risk.

    Attributes:
        hypothesis_id: Unique identifier.
        patient_id: The patient this hypothesis applies to.
        adverse_event: The adverse event being explained.
        title: Short description of the hypothesis.
        mechanism_chain: Ordered list of node IDs forming the causal chain.
        mechanism_description: Human-readable mechanistic narrative.
        supporting_evidence: Evidence supporting this hypothesis.
        evidence_level: Strength classification.
        confidence: Confidence in the hypothesis (0.0 - 1.0).
        testable_predictions: Predictions that could validate the hypothesis.
        suggested_biomarkers: Biomarkers to monitor for validation.
        therapeutic_implications: Potential interventions targeting this mechanism.
        timestamp: When the hypothesis was generated.
    """

    hypothesis_id: str
    patient_id: str
    adverse_event: AdverseEventType
    title: str
    mechanism_chain: list[str]
    mechanism_description: str
    supporting_evidence: list[str]
    evidence_level: EvidenceLevel
    confidence: float
    testable_predictions: list[str] = field(default_factory=list)
    suggested_biomarkers: list[str] = field(default_factory=list)
    therapeutic_implications: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, self.confidence))


class HypothesisGenerator:
    """Generates mechanistic safety hypotheses from KG + model predictions.

    The generation process:
        1. Identify the patient's elevated biomarkers.
        2. Walk upstream in the KG from the adverse event to find activated
           pathways that match the biomarker pattern.
        3. Rank pathways by activation strength and model agreement.
        4. Generate hypotheses with causal chain descriptions.
        5. For each hypothesis, identify testable predictions and therapeutic
           implications.

    Usage::

        generator = HypothesisGenerator(knowledge_graph=kg)
        hypotheses = generator.generate(
            patient_id="PAT-001",
            adverse_event=AdverseEventType.CRS,
            biomarkers={"CYTOKINE:IL6": 5000.0, ...},
            model_predictions=[pred1, pred2],
        )
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        max_hypotheses: int = 5,
        min_confidence: float = 0.2,
    ) -> None:
        """Initialize the hypothesis generator.

        Args:
            knowledge_graph: The biological knowledge graph.
            max_hypotheses: Maximum number of hypotheses to return.
            min_confidence: Minimum confidence threshold for a hypothesis.
        """
        self._kg = knowledge_graph
        self._max_hypotheses = max_hypotheses
        self._min_confidence = min_confidence
        self._hypothesis_counter = 0

    def generate(
        self,
        patient_id: str,
        adverse_event: AdverseEventType,
        biomarkers: dict[str, float],
        model_predictions: list[SafetyPrediction] | None = None,
    ) -> list[MechanisticHypothesis]:
        """Generate mechanistic hypotheses for a patient's adverse event risk.

        Args:
            patient_id: The patient identifier.
            adverse_event: The predicted adverse event.
            biomarkers: Current biomarker values keyed by graph node ID.
            model_predictions: Optional model predictions for evidence.

        Returns:
            Ranked list of MechanisticHypothesis objects.
        """
        logger.info(
            "Generating hypotheses for patient %s, event %s (%d biomarkers)",
            patient_id, adverse_event.value, len(biomarkers),
        )

        ae_node_id = f"AE:{adverse_event.value}"

        # Step 1: Find upstream causal entities from the KG
        upstream_causes = self._kg.get_upstream_causes(ae_node_id, max_depth=5)

        # Step 2: Identify which upstream entities have elevated biomarkers
        activated_entities = self._find_activated_entities(
            upstream_causes, biomarkers,
        )

        # Step 3: Build pathway-based hypotheses
        hypotheses: list[MechanisticHypothesis] = []

        # Generate pathway activation hypotheses
        pathway_hypotheses = self._generate_pathway_hypotheses(
            patient_id, adverse_event, ae_node_id,
            activated_entities, biomarkers, model_predictions,
        )
        hypotheses.extend(pathway_hypotheses)

        # Generate amplification loop hypotheses
        loop_hypotheses = self._detect_amplification_loops(
            patient_id, adverse_event, activated_entities, biomarkers,
        )
        hypotheses.extend(loop_hypotheses)

        # Generate rate-of-escalation hypotheses
        escalation_hypotheses = self._generate_escalation_hypotheses(
            patient_id, adverse_event, activated_entities, biomarkers,
        )
        hypotheses.extend(escalation_hypotheses)

        # Filter and rank
        hypotheses = [h for h in hypotheses if h.confidence >= self._min_confidence]
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        hypotheses = hypotheses[:self._max_hypotheses]

        logger.info(
            "Generated %d hypotheses for patient %s (filtered from candidates)",
            len(hypotheses), patient_id,
        )

        return hypotheses

    # ------------------------------------------------------------------
    # Internal hypothesis generation methods
    # ------------------------------------------------------------------

    def _find_activated_entities(
        self,
        upstream_causes: list[tuple[Any, float]],
        biomarkers: dict[str, float],
    ) -> list[tuple[Any, float, float]]:
        """Find upstream entities that have matching elevated biomarkers.

        Returns:
            List of ``(graph_node, causal_weight, fold_change)`` tuples.
        """
        activated = []
        for node, weight in upstream_causes:
            value = biomarkers.get(node.node_id)
            if value is None:
                continue

            # Get normal range from node properties
            normal_range = (
                node.properties.get("normal_range_pg_ml")
                or node.properties.get("normal_range_ng_ml")
                or node.properties.get("normal_range_mg_l")
                or node.properties.get("normal_range_mg_dl")
                or node.properties.get("normal_range_u_l")
            )
            if normal_range and normal_range[1] > 0:
                fold_change = value / normal_range[1]
                if fold_change > 1.5:  # At least 1.5x above normal
                    activated.append((node, weight, fold_change))
            elif value > 0:
                activated.append((node, weight, 1.0))

        return activated

    def _generate_pathway_hypotheses(
        self,
        patient_id: str,
        adverse_event: AdverseEventType,
        ae_node_id: str,
        activated_entities: list[tuple[Any, float, float]],
        biomarkers: dict[str, float],
        model_predictions: list[SafetyPrediction] | None,
    ) -> list[MechanisticHypothesis]:
        """Generate hypotheses based on activated KG pathways."""
        hypotheses: list[MechanisticHypothesis] = []

        for node, causal_weight, fold_change in activated_entities:
            # Find the path from this entity to the adverse event
            path_result = self._kg.find_paths(
                node.node_id, ae_node_id, max_hops=4,
            )

            if not path_result.paths:
                continue

            # Use the highest-weight path
            best_path = path_result.max_weight_path
            chain = [step[0] for step in best_path] + [best_path[-1][2]]

            # Determine evidence level
            evidence_level = self._assess_evidence_level(
                node, fold_change, model_predictions,
            )

            # Build evidence list
            evidence = [
                f"{node.name} is {fold_change:.1f}x above normal range",
                f"KG path to {adverse_event.value}: {len(best_path)} hops "
                f"(causal weight: {causal_weight:.2f})",
            ]
            if model_predictions:
                agreeing = sum(
                    1 for p in model_predictions if p.risk_score > 0.5
                )
                evidence.append(
                    f"{agreeing}/{len(model_predictions)} models predict elevated risk"
                )

            # Confidence based on evidence strength
            confidence = self._compute_hypothesis_confidence(
                causal_weight, fold_change, evidence_level,
            )

            # Build therapeutic implications
            therapeutics = self._find_therapeutic_targets(chain)

            # Build testable predictions
            testable = self._build_testable_predictions(node, chain, adverse_event)

            # Suggested monitoring biomarkers
            suggested = self._suggest_monitoring_biomarkers(chain, biomarkers)

            self._hypothesis_counter += 1
            hypothesis = MechanisticHypothesis(
                hypothesis_id=f"HYP-{self._hypothesis_counter:06d}",
                patient_id=patient_id,
                adverse_event=adverse_event,
                title=f"{node.name}-driven {adverse_event.value} via {len(best_path)}-step cascade",
                mechanism_chain=chain,
                mechanism_description=self._describe_mechanism(best_path),
                supporting_evidence=evidence,
                evidence_level=evidence_level,
                confidence=confidence,
                testable_predictions=testable,
                suggested_biomarkers=suggested,
                therapeutic_implications=therapeutics,
            )
            hypotheses.append(hypothesis)

        return hypotheses

    def _detect_amplification_loops(
        self,
        patient_id: str,
        adverse_event: AdverseEventType,
        activated_entities: list[tuple[Any, float, float]],
        biomarkers: dict[str, float],
    ) -> list[MechanisticHypothesis]:
        """Detect positive feedback loops among activated entities."""
        hypotheses: list[MechanisticHypothesis] = []

        activated_ids = {node.node_id for node, _, _ in activated_entities}

        for node, _, fold_change in activated_entities:
            # Check for AMPLIFIES edges that form loops
            neighbors = self._kg.get_neighbors(
                node.node_id,
                edge_types={EdgeType.AMPLIFIES, EdgeType.CAUSES},
                direction="outgoing",
            )
            for edge, target in neighbors:
                if target.node_id in activated_ids and target.node_id != node.node_id:
                    # Check if target also amplifies back to this node
                    reverse = self._kg.get_neighbors(
                        target.node_id,
                        edge_types={EdgeType.AMPLIFIES, EdgeType.CAUSES},
                        direction="outgoing",
                    )
                    for rev_edge, rev_target in reverse:
                        if rev_target.node_id == node.node_id:
                            # Found a loop
                            self._hypothesis_counter += 1
                            hypothesis = MechanisticHypothesis(
                                hypothesis_id=f"HYP-{self._hypothesis_counter:06d}",
                                patient_id=patient_id,
                                adverse_event=adverse_event,
                                title=(
                                    f"Positive feedback loop: {node.name} <-> "
                                    f"{target.name}"
                                ),
                                mechanism_chain=[node.node_id, target.node_id, node.node_id],
                                mechanism_description=(
                                    f"{node.name} and {target.name} form a positive "
                                    f"feedback loop that may sustain and amplify the "
                                    f"inflammatory response. Both are currently elevated "
                                    f"above normal, suggesting active loop engagement."
                                ),
                                supporting_evidence=[
                                    f"{node.name} is {fold_change:.1f}x above normal",
                                    f"Bidirectional amplification edges in knowledge graph",
                                ],
                                evidence_level=EvidenceLevel.MODERATE,
                                confidence=min(0.8, fold_change / 20.0 + 0.3),
                                testable_predictions=[
                                    f"Blocking {node.name} should reduce {target.name}",
                                    f"Both markers should rise in parallel if loop is active",
                                ],
                            )
                            hypotheses.append(hypothesis)

        return hypotheses

    def _generate_escalation_hypotheses(
        self,
        patient_id: str,
        adverse_event: AdverseEventType,
        activated_entities: list[tuple[Any, float, float]],
        biomarkers: dict[str, float],
    ) -> list[MechanisticHypothesis]:
        """Generate hypotheses about risk of escalation from current to severe."""
        hypotheses: list[MechanisticHypothesis] = []

        # Check for entities that are elevated but not yet at severe levels
        # and have strong connections to severe outcomes
        for node, weight, fold_change in activated_entities:
            if 2.0 < fold_change < 10.0:  # Elevated but not extreme
                # Check if this entity connects to severe clinical signs
                severe_signs = self._kg.get_neighbors(
                    node.node_id,
                    edge_types={EdgeType.CAUSES, EdgeType.TRIGGERS, EdgeType.ACTIVATES},
                    direction="outgoing",
                )
                severe_targets = [
                    (e, n) for e, n in severe_signs
                    if n.node_type in (NodeType.ADVERSE_EVENT, NodeType.CLINICAL_SIGN)
                ]
                if severe_targets:
                    self._hypothesis_counter += 1
                    target_names = [n.name for _, n in severe_targets[:3]]
                    hypothesis = MechanisticHypothesis(
                        hypothesis_id=f"HYP-{self._hypothesis_counter:06d}",
                        patient_id=patient_id,
                        adverse_event=adverse_event,
                        title=f"Escalation risk: rising {node.name} ({fold_change:.1f}x)",
                        mechanism_chain=[node.node_id] + [n.node_id for _, n in severe_targets[:3]],
                        mechanism_description=(
                            f"{node.name} is currently {fold_change:.1f}x above normal. "
                            f"If it continues to rise, KG paths indicate it could trigger: "
                            f"{', '.join(target_names)}. Close monitoring recommended."
                        ),
                        supporting_evidence=[
                            f"{node.name} at {fold_change:.1f}x normal",
                            f"Direct pathway connections to {len(severe_targets)} severe outcomes",
                        ],
                        evidence_level=EvidenceLevel.MODERATE,
                        confidence=min(0.6, fold_change / 15.0 + 0.2),
                        testable_predictions=[
                            f"If {node.name} exceeds 10x normal, expect clinical deterioration",
                        ],
                        suggested_biomarkers=[node.node_id],
                    )
                    hypotheses.append(hypothesis)

        return hypotheses

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assess_evidence_level(
        self,
        node: Any,
        fold_change: float,
        model_predictions: list[SafetyPrediction] | None,
    ) -> EvidenceLevel:
        """Assess the overall evidence level for a hypothesis."""
        has_kg_path = True  # We only generate hypotheses with KG paths
        has_biomarker = fold_change > 2.0
        has_model_support = False

        if model_predictions:
            high_risk_models = sum(1 for p in model_predictions if p.risk_score > 0.5)
            has_model_support = high_risk_models > len(model_predictions) / 2

        if has_kg_path and has_biomarker and has_model_support:
            return EvidenceLevel.STRONG
        elif has_kg_path and (has_biomarker or has_model_support):
            return EvidenceLevel.MODERATE
        elif has_kg_path:
            return EvidenceLevel.WEAK
        else:
            return EvidenceLevel.SPECULATIVE

    @staticmethod
    def _compute_hypothesis_confidence(
        causal_weight: float,
        fold_change: float,
        evidence_level: EvidenceLevel,
    ) -> float:
        """Compute confidence score for a hypothesis."""
        evidence_multiplier = {
            EvidenceLevel.STRONG: 1.0,
            EvidenceLevel.MODERATE: 0.7,
            EvidenceLevel.WEAK: 0.4,
            EvidenceLevel.SPECULATIVE: 0.2,
        }
        multiplier = evidence_multiplier[evidence_level]

        # Base confidence from causal weight and fold change
        base = min(1.0, causal_weight * 0.5 + min(fold_change / 20.0, 0.5))
        return min(1.0, base * multiplier + 0.1)

    def _describe_mechanism(
        self,
        path: list[tuple[str, EdgeType, str]],
    ) -> str:
        """Build a human-readable description of a mechanistic path."""
        parts: list[str] = []
        for source_id, edge_type, target_id in path:
            source_node = self._kg.get_node(source_id)
            target_node = self._kg.get_node(target_id)
            source_name = source_node.name if source_node else source_id
            target_name = target_node.name if target_node else target_id
            verb = edge_type.value.lower().replace("_", " ")
            parts.append(f"{source_name} {verb} {target_name}")
        return " -> ".join(parts) if parts else "Unknown mechanism"

    def _find_therapeutic_targets(self, chain: list[str]) -> list[str]:
        """Find drugs that target entities in the mechanism chain."""
        therapeutics: list[str] = []
        drug_nodes = self._kg.get_nodes_by_type(NodeType.DRUG)

        for drug in drug_nodes:
            targets = self._kg.get_neighbors(
                drug.node_id,
                edge_types={EdgeType.TARGETS, EdgeType.INHIBITS, EdgeType.TREATS},
                direction="outgoing",
            )
            for _, target_node in targets:
                if target_node.node_id in chain:
                    mechanism = drug.properties.get("mechanism", "unknown mechanism")
                    therapeutics.append(
                        f"{drug.name} ({mechanism}) targets {target_node.name}"
                    )
                    break

        return therapeutics

    def _build_testable_predictions(
        self,
        trigger_node: Any,
        chain: list[str],
        adverse_event: AdverseEventType,
    ) -> list[str]:
        """Generate testable predictions for a hypothesis."""
        predictions = [
            f"If {trigger_node.name} continues to rise, downstream markers "
            f"in the cascade should follow within 6-12 hours",
        ]

        # Check for downstream nodes in the chain that aren't yet measured
        for node_id in chain:
            node = self._kg.get_node(node_id)
            if node and node.node_type == NodeType.CYTOKINE:
                predictions.append(
                    f"Monitor {node.name} for secondary elevation"
                )

        return predictions[:4]  # Cap at 4 predictions

    def _suggest_monitoring_biomarkers(
        self,
        chain: list[str],
        current_biomarkers: dict[str, float],
    ) -> list[str]:
        """Suggest additional biomarkers to monitor based on the mechanism."""
        suggestions: list[str] = []
        for node_id in chain:
            if node_id not in current_biomarkers:
                node = self._kg.get_node(node_id)
                if node and node.node_type in (
                    NodeType.CYTOKINE, NodeType.BIOMARKER, NodeType.PROTEIN,
                ):
                    suggestions.append(node_id)
        return suggestions[:5]
