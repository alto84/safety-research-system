"""Mechanistic inference worker agent for biological pathway and mechanism analysis."""
from typing import Dict, Any, List, Optional
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agents.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class MechanisticAgent(BaseWorker):
    """
    Worker agent for mechanistic inference and biological pathway analysis.

    This agent performs:
    - Drug mechanism of action analysis
    - Biological pathway identification
    - Causality inference from mechanistic data
    - Target-toxicity relationship assessment
    - Pharmacodynamic mechanism evaluation

    Expected input:
        - query: The mechanistic question
        - context: Context including drug name, target, adverse event, etc.
        - mechanism_data: Known mechanism data (targets, pathways, etc.)
        - pathway_data: Biological pathway information (optional)

    Output:
        - mechanism_summary: Summary of mechanism findings
        - pathways: Identified biological pathways
        - causality_assessment: Mechanistic causality evaluation
        - evidence_strength: Strength of mechanistic evidence
        - biological_plausibility: Plausibility assessment
    """

    def __init__(
        self,
        agent_id: str = "mechanistic_agent_01",
        config: Dict[str, Any] = None
    ):
        """
        Initialize mechanistic inference agent.

        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
        """
        super().__init__(agent_id, config)
        self.version = "1.0.0"

        # Pathway knowledge base (simplified - would be a real database in production)
        self.pathway_database = self._initialize_pathway_database()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute mechanistic inference task.

        Args:
            input_data: Input containing query, mechanism_data, context

        Returns:
            Dictionary with mechanistic analysis results
        """
        # Validate input
        self.validate_input(input_data)

        # Handle corrections from previous audit if present
        input_data = self.handle_corrections(input_data)

        query = input_data.get("query", "")
        context = input_data.get("context", {})
        mechanism_data = input_data.get("mechanism_data", {})
        pathway_data = input_data.get("pathway_data", {})

        logger.info(f"MechanisticAgent: Starting mechanistic analysis for query: '{query}'")

        # Execute mechanistic inference
        result = self._conduct_mechanistic_analysis(
            query, mechanism_data, pathway_data, context
        )

        logger.info(f"MechanisticAgent: Analysis complete")

        return result

    def _conduct_mechanistic_analysis(
        self,
        query: str,
        mechanism_data: Dict[str, Any],
        pathway_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct mechanistic inference analysis.

        Args:
            query: Mechanistic question
            mechanism_data: Known mechanism data
            pathway_data: Pathway information
            context: Additional context

        Returns:
            Structured mechanistic analysis results
        """
        # Extract key entities
        drug_name = context.get("drug_name", "Unknown drug")
        target = mechanism_data.get("target", "Unknown target")
        adverse_event = context.get("adverse_event", "Unknown adverse event")
        mechanism_of_action = mechanism_data.get("mechanism_of_action", "")

        # Identify relevant pathways
        pathways = self._identify_pathways(
            target, adverse_event, mechanism_data, pathway_data
        )

        # Assess biological plausibility
        plausibility = self._assess_biological_plausibility(
            target, adverse_event, pathways, mechanism_data
        )

        # Evaluate mechanistic causality
        causality = self._evaluate_mechanistic_causality(
            drug_name, target, adverse_event, pathways, mechanism_data
        )

        # Assess evidence strength
        evidence_strength = self._assess_mechanistic_evidence_strength(
            mechanism_data, pathways, causality
        )

        # Generate mechanism summary
        summary = self._generate_mechanism_summary(
            drug_name, target, adverse_event, pathways, plausibility, causality
        )

        # Extract key findings
        key_findings = self._extract_mechanistic_findings(
            pathways, plausibility, causality, evidence_strength
        )

        return {
            "summary": summary,
            "mechanism_of_action": mechanism_of_action,
            "target": target,
            "pathways": pathways,
            "biological_plausibility": plausibility,
            "causality_assessment": causality,
            "evidence_strength": evidence_strength,
            "key_findings": key_findings,
            "confidence": self._assess_confidence(
                mechanism_data, pathways, causality
            ),
            "limitations": self._identify_limitations(mechanism_data, pathways),
            "assumptions": self._document_assumptions(),
            "methodology": self._document_methodology(
                drug_name, target, adverse_event
            ),
            "metadata": {
                "analysis_date": datetime.utcnow().isoformat(),
                "drug": drug_name,
                "target": target,
                "adverse_event": adverse_event,
                "pathways_identified": len(pathways),
                "model_version": self.version,
            },
        }

    def _initialize_pathway_database(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize pathway knowledge base.

        In production, this would connect to a real pathway database
        (e.g., KEGG, Reactome, WikiPathways).
        """
        return {
            "her2_signaling": {
                "name": "HER2/ERBB2 Signaling Pathway",
                "components": ["ERBB2", "PI3K", "AKT", "MAPK"],
                "tissues": ["breast", "lung", "gastric"],
                "related_toxicities": ["cardiotoxicity", "ILD"],
            },
            "pi3k_akt": {
                "name": "PI3K/AKT Pathway",
                "components": ["PI3K", "AKT", "mTOR"],
                "tissues": ["multiple"],
                "related_toxicities": ["metabolic", "immunosuppression"],
            },
            "inflammatory_response": {
                "name": "Inflammatory Response Pathway",
                "components": ["TNF-alpha", "IL-6", "NF-kB"],
                "tissues": ["lung", "liver", "kidney"],
                "related_toxicities": ["ILD", "hepatotoxicity", "nephrotoxicity"],
            },
            "immune_checkpoint": {
                "name": "Immune Checkpoint Pathway",
                "components": ["PD-1", "PD-L1", "CTLA-4"],
                "tissues": ["immune cells"],
                "related_toxicities": ["immune-related adverse events", "pneumonitis"],
            },
            "pulmonary_fibrosis": {
                "name": "Pulmonary Fibrosis Pathway",
                "components": ["TGF-beta", "fibroblasts", "collagen"],
                "tissues": ["lung"],
                "related_toxicities": ["ILD", "pulmonary fibrosis"],
            },
        }

    def _identify_pathways(
        self,
        target: str,
        adverse_event: str,
        mechanism_data: Dict[str, Any],
        pathway_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify relevant biological pathways.

        Args:
            target: Drug target
            adverse_event: Adverse event of interest
            mechanism_data: Known mechanism data
            pathway_data: Additional pathway data

        Returns:
            List of identified pathways with details
        """
        identified_pathways = []

        # Search pathway database for relevant pathways
        target_lower = target.lower()
        ae_lower = adverse_event.lower()

        for pathway_id, pathway_info in self.pathway_database.items():
            relevance_score = 0
            reasons = []

            # Check target relevance
            for component in pathway_info["components"]:
                if component.lower() in target_lower or target_lower in component.lower():
                    relevance_score += 3
                    reasons.append(f"Target {target} is component of pathway")

            # Check adverse event relevance
            for toxicity in pathway_info["related_toxicities"]:
                if toxicity.lower() in ae_lower or ae_lower in toxicity.lower():
                    relevance_score += 2
                    reasons.append(f"Pathway linked to {adverse_event}")

            # Check tissue relevance
            tissue_context = mechanism_data.get("affected_tissue", "").lower()
            if tissue_context:
                for tissue in pathway_info["tissues"]:
                    if tissue in tissue_context:
                        relevance_score += 1
                        reasons.append(f"Pathway active in {tissue}")

            if relevance_score > 0:
                identified_pathways.append({
                    "pathway_id": pathway_id,
                    "pathway_name": pathway_info["name"],
                    "components": pathway_info["components"],
                    "relevance_score": relevance_score,
                    "relevance_reasons": reasons,
                    "confidence": self._pathway_confidence(relevance_score),
                })

        # Sort by relevance
        identified_pathways.sort(key=lambda x: x["relevance_score"], reverse=True)

        return identified_pathways

    def _pathway_confidence(self, relevance_score: int) -> str:
        """Determine confidence in pathway relevance."""
        if relevance_score >= 5:
            return "High confidence - strong mechanistic link"
        elif relevance_score >= 3:
            return "Moderate confidence - plausible mechanistic link"
        else:
            return "Low confidence - weak mechanistic link"

    def _assess_biological_plausibility(
        self,
        target: str,
        adverse_event: str,
        pathways: List[Dict[str, Any]],
        mechanism_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess biological plausibility of target-toxicity relationship.

        Args:
            target: Drug target
            adverse_event: Adverse event
            pathways: Identified pathways
            mechanism_data: Mechanism data

        Returns:
            Plausibility assessment
        """
        plausibility_score = 0
        supporting_evidence = []
        limiting_factors = []

        # Factor 1: Pathway connectivity
        if len(pathways) > 0:
            plausibility_score += 2
            supporting_evidence.append(
                f"{len(pathways)} relevant biological pathways identified"
            )
        else:
            limiting_factors.append("No direct pathway connections identified")

        # Factor 2: Target expression in affected tissue
        affected_tissue = mechanism_data.get("affected_tissue", "").lower()
        target_expression = mechanism_data.get("target_expression", {})

        if affected_tissue in target_expression:
            expression_level = target_expression[affected_tissue]
            if expression_level in ["high", "moderate"]:
                plausibility_score += 2
                supporting_evidence.append(
                    f"Target {target} expressed in {affected_tissue} tissue"
                )
            else:
                limiting_factors.append(
                    f"Low target expression in {affected_tissue} tissue"
                )
        else:
            limiting_factors.append("Target expression in affected tissue unknown")

        # Factor 3: Known class effects
        if mechanism_data.get("known_class_effects"):
            plausibility_score += 1
            supporting_evidence.append(
                "Similar adverse events reported for drug class"
            )

        # Factor 4: Timing consistency
        if mechanism_data.get("mechanism_onset_consistent"):
            plausibility_score += 1
            supporting_evidence.append(
                "Mechanism onset time consistent with observed adverse event timing"
            )

        # Determine overall plausibility
        if plausibility_score >= 5:
            overall = "High biological plausibility"
        elif plausibility_score >= 3:
            overall = "Moderate biological plausibility"
        elif plausibility_score >= 1:
            overall = "Low to moderate biological plausibility"
        else:
            overall = "Limited biological plausibility"

        return {
            "overall_plausibility": overall,
            "plausibility_score": plausibility_score,
            "max_score": 6,
            "supporting_evidence": supporting_evidence,
            "limiting_factors": limiting_factors,
            "interpretation": self._interpret_plausibility(plausibility_score),
        }

    def _interpret_plausibility(self, score: int) -> str:
        """Interpret plausibility score."""
        if score >= 5:
            return (
                "Strong mechanistic rationale supports causal relationship. "
                "Multiple lines of biological evidence converge."
            )
        elif score >= 3:
            return (
                "Plausible mechanistic rationale with some supporting evidence. "
                "Causal relationship is biologically feasible."
            )
        elif score >= 1:
            return (
                "Weak mechanistic rationale. "
                "Causal relationship possible but lacks strong biological support."
            )
        else:
            return (
                "Insufficient mechanistic evidence. "
                "Causal relationship not well supported by biological data."
            )

    def _evaluate_mechanistic_causality(
        self,
        drug_name: str,
        target: str,
        adverse_event: str,
        pathways: List[Dict[str, Any]],
        mechanism_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate causality from mechanistic perspective.

        Uses Bradford Hill-like criteria adapted for mechanistic data.

        Args:
            drug_name: Drug name
            target: Drug target
            adverse_event: Adverse event
            pathways: Identified pathways
            mechanism_data: Mechanism data

        Returns:
            Mechanistic causality assessment
        """
        criteria_assessment = []

        # Criterion 1: Biological plausibility (already assessed)
        plausibility = self._assess_biological_plausibility(
            target, adverse_event, pathways, mechanism_data
        )
        criteria_assessment.append({
            "criterion": "Biological Plausibility",
            "assessment": plausibility["overall_plausibility"],
            "score": plausibility["plausibility_score"],
        })

        # Criterion 2: Specificity of mechanism
        specificity_score = 0
        if mechanism_data.get("target_specific"):
            specificity_score = 2
            specificity = "High - target-specific mechanism"
        elif mechanism_data.get("class_effect"):
            specificity_score = 1
            specificity = "Moderate - class effect mechanism"
        else:
            specificity = "Low - non-specific mechanism"

        criteria_assessment.append({
            "criterion": "Specificity",
            "assessment": specificity,
            "score": specificity_score,
        })

        # Criterion 3: Consistency with known pharmacology
        consistency_score = 0
        if mechanism_data.get("consistent_with_pharmacology"):
            consistency_score = 2
            consistency = "High - consistent with known pharmacology"
        else:
            consistency = "Moderate - pharmacology data limited"
            consistency_score = 1

        criteria_assessment.append({
            "criterion": "Pharmacological Consistency",
            "assessment": consistency,
            "score": consistency_score,
        })

        # Criterion 4: Temporal relationship
        temporal_score = 0
        if mechanism_data.get("temporal_relationship_established"):
            temporal_score = 1
            temporal = "Mechanism onset precedes adverse event"
        else:
            temporal = "Temporal relationship unclear"

        criteria_assessment.append({
            "criterion": "Temporal Relationship",
            "assessment": temporal,
            "score": temporal_score,
        })

        # Calculate total causality score
        total_score = sum(item["score"] for item in criteria_assessment)
        max_score = 7  # Maximum possible score

        # Determine causality level
        if total_score >= 6:
            causality_level = "Strong mechanistic causality"
        elif total_score >= 4:
            causality_level = "Moderate mechanistic causality"
        elif total_score >= 2:
            causality_level = "Weak mechanistic causality"
        else:
            causality_level = "Insufficient mechanistic evidence for causality"

        return {
            "causality_level": causality_level,
            "total_score": total_score,
            "max_score": max_score,
            "score_percentage": (total_score / max_score) * 100,
            "criteria_assessments": criteria_assessment,
            "interpretation": self._interpret_causality(total_score, max_score),
        }

    def _interpret_causality(self, score: int, max_score: int) -> str:
        """Interpret mechanistic causality score."""
        percentage = (score / max_score) * 100

        if percentage >= 85:
            return (
                "Strong mechanistic evidence supports causal relationship. "
                "Multiple independent mechanistic criteria satisfied."
            )
        elif percentage >= 50:
            return (
                "Moderate mechanistic evidence supports possible causal relationship. "
                "Some mechanistic criteria satisfied but gaps remain."
            )
        else:
            return (
                "Weak mechanistic evidence. "
                "Causal relationship not well established mechanistically. "
                "Clinical and epidemiological data needed for fuller assessment."
            )

    def _assess_mechanistic_evidence_strength(
        self,
        mechanism_data: Dict[str, Any],
        pathways: List[Dict[str, Any]],
        causality: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess strength of mechanistic evidence.

        Args:
            mechanism_data: Mechanism data
            pathways: Identified pathways
            causality: Causality assessment

        Returns:
            Evidence strength assessment
        """
        evidence_types = []
        strength_score = 0

        # Check for different types of evidence
        if mechanism_data.get("in_vitro_evidence"):
            evidence_types.append("In vitro studies")
            strength_score += 1

        if mechanism_data.get("in_vivo_evidence"):
            evidence_types.append("In vivo/animal studies")
            strength_score += 2

        if mechanism_data.get("human_mechanistic_studies"):
            evidence_types.append("Human mechanistic studies")
            strength_score += 3

        if len(pathways) > 0:
            evidence_types.append("Pathway analysis")
            strength_score += 1

        # Determine overall strength
        if strength_score >= 5:
            overall_strength = "Strong mechanistic evidence base"
        elif strength_score >= 3:
            overall_strength = "Moderate mechanistic evidence base"
        elif strength_score >= 1:
            overall_strength = "Limited mechanistic evidence base"
        else:
            overall_strength = "Minimal mechanistic evidence"

        return {
            "overall_strength": overall_strength,
            "strength_score": strength_score,
            "evidence_types": evidence_types,
            "evidence_hierarchy": (
                "Human mechanistic studies > Animal studies > In vitro studies"
            ),
        }

    def _extract_mechanistic_findings(
        self,
        pathways: List[Dict[str, Any]],
        plausibility: Dict[str, Any],
        causality: Dict[str, Any],
        evidence_strength: Dict[str, Any]
    ) -> List[str]:
        """Extract key mechanistic findings."""
        findings = []

        # Pathway finding
        if pathways:
            top_pathway = pathways[0]
            findings.append(
                f"Primary pathway identified: {top_pathway['pathway_name']} "
                f"({top_pathway['confidence']})"
            )

        # Plausibility finding
        findings.append(plausibility["overall_plausibility"])

        # Causality finding
        findings.append(
            f"{causality['causality_level']} "
            f"(score: {causality['total_score']}/{causality['max_score']})"
        )

        # Evidence strength finding
        findings.append(evidence_strength["overall_strength"])

        return findings

    def _assess_confidence(
        self,
        mechanism_data: Dict[str, Any],
        pathways: List[Dict[str, Any]],
        causality: Dict[str, Any]
    ) -> str:
        """Assess overall confidence in mechanistic analysis."""
        # Base confidence on evidence quality and quantity
        if mechanism_data.get("human_mechanistic_studies") and len(pathways) > 1:
            confidence = "Moderate to High - human mechanistic data available"
        elif mechanism_data.get("in_vivo_evidence") or len(pathways) > 0:
            confidence = "Moderate - preclinical mechanistic data available"
        else:
            confidence = "Low - limited mechanistic data"

        # Adjust based on causality score
        causality_score = causality.get("total_score", 0)
        if causality_score < 2:
            confidence = "Low - weak mechanistic support"

        return confidence

    def _identify_limitations(
        self,
        mechanism_data: Dict[str, Any],
        pathways: List[Dict[str, Any]]
    ) -> List[str]:
        """Identify limitations of mechanistic analysis."""
        limitations = [
            "Mechanistic data alone cannot establish clinical causality",
            "Pathway analysis based on simplified knowledge base - may miss novel mechanisms",
        ]

        if not mechanism_data.get("human_mechanistic_studies"):
            limitations.append(
                "Lack of human mechanistic studies - extrapolation from preclinical data"
            )

        if not pathways:
            limitations.append(
                "No established pathways identified - may involve novel mechanisms"
            )

        if not mechanism_data.get("dose_response_data"):
            limitations.append(
                "Dose-response relationship not characterized mechanistically"
            )

        return limitations

    def _document_assumptions(self) -> List[str]:
        """Document key assumptions in mechanistic analysis."""
        return [
            "Pathway database is comprehensive and current",
            "Preclinical mechanism translates to human biology",
            "Target engagement occurs at therapeutic doses",
            "Identified pathways are complete (may miss novel mechanisms)",
            "Mechanism in model systems reflects clinical mechanism",
        ]

    def _document_methodology(
        self,
        drug_name: str,
        target: str,
        adverse_event: str
    ) -> str:
        """Document mechanistic analysis methodology."""
        return (
            f"Mechanistic inference analysis for {drug_name} ({target}) "
            f"and {adverse_event}. "
            f"Pathway analysis conducted using biological pathway database. "
            f"Biological plausibility assessed across multiple dimensions "
            f"(pathway connectivity, target expression, class effects, timing). "
            f"Mechanistic causality evaluated using Bradford Hill-like criteria "
            f"adapted for mechanistic data. "
            f"Evidence strength graded by study type hierarchy."
        )

    def _generate_mechanism_summary(
        self,
        drug_name: str,
        target: str,
        adverse_event: str,
        pathways: List[Dict[str, Any]],
        plausibility: Dict[str, Any],
        causality: Dict[str, Any]
    ) -> str:
        """Generate mechanistic summary."""
        summary_parts = [
            f"Mechanistic analysis of {drug_name} ({target}) and {adverse_event}."
        ]

        if pathways:
            summary_parts.append(
                f"{len(pathways)} relevant biological pathways identified."
            )

        summary_parts.append(plausibility["overall_plausibility"] + ".")
        summary_parts.append(causality["causality_level"] + ".")

        return " ".join(summary_parts)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate mechanistic analysis input.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        super().validate_input(input_data)

        if not input_data.get("query"):
            raise ValueError("Query is required for mechanistic analysis")

        # Mechanism data or context required
        if not input_data.get("mechanism_data") and not input_data.get("context"):
            raise ValueError(
                "Either mechanism_data or context must be provided"
            )

        return True
