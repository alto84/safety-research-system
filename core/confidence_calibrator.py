"""
Confidence calibration system for evidence-based claims.

This module implements a rigorous, evidence-based confidence assessment
system that complies with CLAUDE.md anti-fabrication protocols.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.evidence import EvidenceClaim, Source, SourceType, ConfidenceLevel


logger = logging.getLogger(__name__)


# Source quality weights (higher = better quality)
SOURCE_QUALITY_WEIGHTS = {
    SourceType.SYSTEMATIC_REVIEW: 10,
    SourceType.META_ANALYSIS: 9,
    SourceType.RANDOMIZED_CONTROLLED_TRIAL: 8,
    SourceType.COHORT_STUDY: 6,
    SourceType.CASE_CONTROL_STUDY: 5,
    SourceType.CASE_SERIES: 3,
    SourceType.CASE_REPORT: 2,
    SourceType.EXPERT_OPINION: 1,
    SourceType.OTHER: 1,
}


@dataclass
class ConfidenceAssessment:
    """
    Result of confidence calibration for a claim.

    Attributes:
        claim_id: ID of the claim assessed
        confidence_level: Final assessed confidence level
        raw_score: Raw numerical score (0-100) before level mapping
        component_scores: Breakdown of score components
        justification: Detailed explanation of confidence assessment
        limitations: Limitations that affected confidence
        requires_external_validation: Whether score >80 needs validation
        assessment_metadata: Additional assessment details
    """
    claim_id: str
    confidence_level: ConfidenceLevel
    raw_score: float
    component_scores: Dict[str, float] = field(default_factory=dict)
    justification: str = ""
    limitations: List[str] = field(default_factory=list)
    requires_external_validation: bool = False
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary."""
        return {
            "claim_id": self.claim_id,
            "confidence_level": self.confidence_level.value,
            "raw_score": self.raw_score,
            "component_scores": self.component_scores,
            "justification": self.justification,
            "limitations": self.limitations,
            "requires_external_validation": self.requires_external_validation,
            "assessment_metadata": self.assessment_metadata,
        }


class ConfidenceCalibrator:
    """
    Calibrates confidence levels for evidence-based claims.

    This class implements a transparent, evidence-based scoring system
    that adheres to CLAUDE.md anti-fabrication protocols:
    - No confidence without evidence
    - No scores >80% without external validation
    - Clear scoring methodology
    - Conservative assessments
    """

    def __init__(self):
        """Initialize the confidence calibrator."""
        self.assessment_history: List[ConfidenceAssessment] = []

    def assess_claim_confidence(
        self, claim: EvidenceClaim
    ) -> ConfidenceAssessment:
        """
        Assess confidence level for an evidence claim.

        This method calculates a confidence score based on multiple factors:
        1. Number of sources (0 sources = automatic NONE)
        2. Quality of sources (weighted by study type)
        3. Aggregate sample size
        4. Source consistency
        5. Directness of evidence
        6. Recency of evidence

        Per CLAUDE.md: Scores >80% automatically require external validation.

        Args:
            claim: EvidenceClaim to assess

        Returns:
            ConfidenceAssessment with level, score, and justification
        """
        logger.info(f"Assessing confidence for claim {claim.claim_id}")

        # Initialize component scores
        component_scores = {}
        limitations = list(claim.limitations)  # Start with claim's own limitations

        # 1. SOURCE COUNT SCORE (0-25 points)
        source_count_score = self._score_source_count(claim)
        component_scores["source_count"] = source_count_score

        # Early exit if no sources
        if len(claim.sources) == 0:
            return self._create_no_evidence_assessment(claim, limitations)

        # 2. SOURCE QUALITY SCORE (0-25 points)
        source_quality_score = self._score_source_quality(claim)
        component_scores["source_quality"] = source_quality_score

        # 3. SAMPLE SIZE SCORE (0-20 points)
        sample_size_score = self._score_sample_size(claim)
        component_scores["sample_size"] = sample_size_score

        # 4. CONSISTENCY SCORE (0-15 points)
        consistency_score = self._score_consistency(claim, limitations)
        component_scores["consistency"] = consistency_score

        # 5. DIRECTNESS SCORE (0-10 points)
        directness_score = self._score_directness(claim, limitations)
        component_scores["directness"] = directness_score

        # 6. RECENCY SCORE (0-5 points)
        recency_score = self._score_recency(claim)
        component_scores["recency"] = recency_score

        # Calculate raw score (0-100)
        raw_score = sum(component_scores.values())

        # Apply verification penalty (unverified sources reduce score)
        verification_penalty = self._calculate_verification_penalty(claim)
        if verification_penalty > 0:
            raw_score = max(0, raw_score - verification_penalty)
            component_scores["verification_penalty"] = -verification_penalty
            limitations.append(
                f"Sources not verified: reduces confidence by {verification_penalty} points"
            )

        # Map to confidence level
        confidence_level = self._map_score_to_level(raw_score)

        # Check if external validation required (CLAUDE.md rule)
        requires_validation = raw_score > 80

        # Build justification
        justification = self._build_justification(
            claim, component_scores, raw_score, confidence_level
        )

        # Create assessment
        assessment = ConfidenceAssessment(
            claim_id=claim.claim_id,
            confidence_level=confidence_level,
            raw_score=round(raw_score, 2),
            component_scores=component_scores,
            justification=justification,
            limitations=limitations,
            requires_external_validation=requires_validation,
            assessment_metadata={
                "source_count": len(claim.sources),
                "verified_sources": claim.get_verified_source_count(),
                "aggregate_sample_size": claim.get_aggregate_sample_size(),
                "assessed_at": datetime.utcnow().isoformat(),
            },
        )

        # Store in history
        self.assessment_history.append(assessment)

        logger.info(
            f"Confidence assessment complete: {confidence_level.value} "
            f"(raw_score={raw_score:.2f})"
        )

        return assessment

    def _score_source_count(self, claim: EvidenceClaim) -> float:
        """
        Score based on number of sources (0-25 points).

        Scoring:
        - 0 sources: 0 points
        - 1 source: 10 points
        - 2-3 sources: 15 points
        - 4-5 sources: 20 points
        - 6+ sources: 25 points
        """
        count = len(claim.sources)
        if count == 0:
            return 0.0
        elif count == 1:
            return 10.0
        elif count <= 3:
            return 15.0
        elif count <= 5:
            return 20.0
        else:
            return 25.0

    def _score_source_quality(self, claim: EvidenceClaim) -> float:
        """
        Score based on quality of sources (0-25 points).

        Uses weighted average of source types. Higher quality studies
        (systematic reviews, RCTs) receive higher weights.
        """
        if not claim.sources:
            return 0.0

        # Calculate weighted quality score
        total_weight = sum(
            SOURCE_QUALITY_WEIGHTS.get(source.source_type, 1)
            for source in claim.sources
        )
        max_possible_weight = len(claim.sources) * SOURCE_QUALITY_WEIGHTS[
            SourceType.SYSTEMATIC_REVIEW
        ]

        # Normalize to 0-25 scale
        quality_ratio = total_weight / max_possible_weight
        return quality_ratio * 25.0

    def _score_sample_size(self, claim: EvidenceClaim) -> float:
        """
        Score based on aggregate sample size (0-20 points).

        Scoring (logarithmic scale):
        - 0-49: 0 points
        - 50-99: 5 points
        - 100-499: 10 points
        - 500-999: 15 points
        - 1000+: 20 points
        """
        total_sample = claim.get_aggregate_sample_size()

        if total_sample < 50:
            return 0.0
        elif total_sample < 100:
            return 5.0
        elif total_sample < 500:
            return 10.0
        elif total_sample < 1000:
            return 15.0
        else:
            return 20.0

    def _score_consistency(
        self, claim: EvidenceClaim, limitations: List[str]
    ) -> float:
        """
        Score based on consistency between sources (0-15 points).

        Scoring:
        - Not assessed: 7.5 points (neutral)
        - Consistent: 15 points
        - Mixed: 7.5 points
        - Inconsistent: 0 points (major limitation)
        """
        if not claim.source_consistency:
            return 7.5  # Neutral if not assessed

        consistency = claim.source_consistency.lower()
        if consistency == "consistent":
            return 15.0
        elif consistency == "mixed":
            limitations.append("Sources show mixed results")
            return 7.5
        elif consistency == "inconsistent":
            limitations.append("Sources show inconsistent results (major limitation)")
            return 0.0
        else:
            return 7.5

    def _score_directness(
        self, claim: EvidenceClaim, limitations: List[str]
    ) -> float:
        """
        Score based on how directly evidence tests the claim (0-10 points).

        Scoring:
        - Not assessed: 5 points (neutral)
        - Direct: 10 points
        - Indirect: 5 points
        - Very indirect: 2 points
        """
        if not claim.directness:
            return 5.0  # Neutral if not assessed

        directness = claim.directness.lower()
        if directness == "direct":
            return 10.0
        elif directness == "indirect":
            limitations.append("Evidence is indirect")
            return 5.0
        elif directness == "very_indirect":
            limitations.append("Evidence is very indirect (major limitation)")
            return 2.0
        else:
            return 5.0

    def _score_recency(self, claim: EvidenceClaim) -> float:
        """
        Score based on recency of evidence (0-5 points).

        Scoring:
        - Unknown: 2.5 points (neutral)
        - Last 5 years: 5 points
        - 5-10 years: 3 points
        - 10-20 years: 2 points
        - 20+ years: 1 point
        """
        try:
            most_recent_year = claim.get_most_recent_year()
            if not most_recent_year:
                return 2.5  # Neutral if unknown

            current_year = datetime.utcnow().year
            years_old = current_year - most_recent_year

            if years_old <= 5:
                return 5.0
            elif years_old <= 10:
                return 3.0
            elif years_old <= 20:
                return 2.0
            else:
                return 1.0
        except Exception:
            return 2.5  # Neutral if error parsing dates

    def _calculate_verification_penalty(self, claim: EvidenceClaim) -> float:
        """
        Calculate penalty for unverified sources.

        Penalty: 10 points per unverified source (up to 30 points total).
        """
        verified_count = claim.get_verified_source_count()
        unverified_count = len(claim.sources) - verified_count

        # Cap penalty at 30 points
        return min(unverified_count * 10, 30)

    def _map_score_to_level(self, raw_score: float) -> ConfidenceLevel:
        """
        Map raw score to confidence level.

        Mapping (conservative thresholds):
        - 0-20: NONE
        - 21-45: LOW
        - 46-70: MODERATE
        - 71-85: HIGH
        - 86-100: ESTABLISHED (requires external validation per CLAUDE.md)

        Note: Scores >80 trigger external validation requirement.
        """
        if raw_score <= 20:
            return ConfidenceLevel.NONE
        elif raw_score <= 45:
            return ConfidenceLevel.LOW
        elif raw_score <= 70:
            return ConfidenceLevel.MODERATE
        elif raw_score <= 85:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.ESTABLISHED

    def _build_justification(
        self,
        claim: EvidenceClaim,
        component_scores: Dict[str, float],
        raw_score: float,
        confidence_level: ConfidenceLevel,
    ) -> str:
        """Build detailed justification for confidence assessment."""
        lines = [
            f"Confidence assessment: {confidence_level.value.upper()} (score: {raw_score:.2f}/100)",
            "",
            "Score breakdown:",
        ]

        # Format component scores
        for component, score in component_scores.items():
            if component != "verification_penalty":
                lines.append(f"  - {component}: {score:.2f}")
            else:
                lines.append(f"  - {component}: {score:.2f} (penalty)")

        lines.append("")
        lines.append("Evidence summary:")
        lines.append(f"  - {len(claim.sources)} source(s)")
        lines.append(
            f"  - {claim.get_verified_source_count()} verified source(s)"
        )

        if claim.get_aggregate_sample_size() > 0:
            lines.append(
                f"  - Total sample size: {claim.get_aggregate_sample_size()}"
            )

        if claim.source_consistency:
            lines.append(f"  - Consistency: {claim.source_consistency}")

        if claim.directness:
            lines.append(f"  - Directness: {claim.directness}")

        most_recent = claim.get_most_recent_year()
        if most_recent:
            lines.append(f"  - Most recent source: {most_recent}")

        return "\n".join(lines)

    def _create_no_evidence_assessment(
        self, claim: EvidenceClaim, limitations: List[str]
    ) -> ConfidenceAssessment:
        """Create assessment for claims with no evidence."""
        limitations.append("No sources provided (critical limitation)")

        return ConfidenceAssessment(
            claim_id=claim.claim_id,
            confidence_level=ConfidenceLevel.NONE,
            raw_score=0.0,
            component_scores={"source_count": 0.0},
            justification=(
                "Confidence assessment: NONE (score: 0.0/100)\n\n"
                "No evidence sources provided. Cannot assess confidence without evidence.\n"
                "Per CLAUDE.md: Claims require primary source evidence."
            ),
            limitations=limitations,
            requires_external_validation=False,
            assessment_metadata={
                "source_count": 0,
                "verified_sources": 0,
                "aggregate_sample_size": 0,
                "assessed_at": datetime.utcnow().isoformat(),
            },
        )

    def get_assessment_history(self) -> List[ConfidenceAssessment]:
        """Get history of all confidence assessments."""
        return self.assessment_history

    def get_high_confidence_claims_needing_validation(
        self,
    ) -> List[ConfidenceAssessment]:
        """
        Get assessments with scores >80% that need external validation.

        Per CLAUDE.md: Scores >80% require independent verification.
        """
        return [
            assessment
            for assessment in self.assessment_history
            if assessment.requires_external_validation
        ]
