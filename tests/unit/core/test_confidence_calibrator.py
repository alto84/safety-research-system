"""
Unit tests for ConfidenceCalibrator.

Tests cover:
- Confidence assessment logic
- Source quality scoring
- Sample size scoring
- Consistency scoring
- Confidence level mapping
- Validation requirements
"""

import pytest
from core.confidence_calibrator import ConfidenceCalibrator, ConfidenceAssessment
from models.evidence import (
    EvidenceClaim, Source, SourceType, ConfidenceLevel, ClaimType
)


class TestConfidenceCalibrator:
    """Test ConfidenceCalibrator class."""

    def test_calibrator_creation(self):
        """Test creating a confidence calibrator."""
        calibrator = ConfidenceCalibrator()
        assert calibrator is not None
        assert len(calibrator.assessment_history) == 0

    def test_no_sources_none_confidence(self):
        """Test that 0 sources results in NONE confidence."""
        calibrator = ConfidenceCalibrator()

        # Create claim with empty sources (manually set after creation)
        source = Source(url="https://example.com", title="Temp")
        claim = EvidenceClaim(
            claim_text="Test claim",
            claim_type=ClaimType.QUALITATIVE,
            sources=[source],
            confidence=ConfidenceLevel.LOW
        )
        claim.sources = []  # Manually set to empty

        assessment = calibrator.assess_claim_confidence(claim)

        assert assessment.confidence_level == ConfidenceLevel.NONE
        assert assessment.raw_score == 0.0

    def test_single_low_quality_source(self):
        """Test single low-quality source gives LOW confidence."""
        calibrator = ConfidenceCalibrator()

        source = Source(
            url="https://example.org/case-report",
            title="Single Case Report",
            source_type=SourceType.CASE_REPORT,
            verification_status=False
        )

        claim = EvidenceClaim(
            claim_text="Finding based on case report",
            claim_type=ClaimType.CLINICAL,
            sources=[source],
            confidence=ConfidenceLevel.LOW
        )

        assessment = calibrator.assess_claim_confidence(claim)

        assert assessment.confidence_level in [ConfidenceLevel.NONE, ConfidenceLevel.LOW]
        assert assessment.raw_score <= 45.0

    def test_multiple_high_quality_sources(self):
        """Test multiple high-quality sources increase confidence."""
        calibrator = ConfidenceCalibrator()

        sources = [
            Source(
                url=f"https://pubmed.ncbi.nlm.nih.gov/{i}1111111/",
                title=f"RCT Study {i}",
                pmid=f"{i}1111111",
                source_type=SourceType.RANDOMIZED_CONTROLLED_TRIAL,
                sample_size=500,
                verification_status=True
            )
            for i in range(1, 4)
        ]

        claim = EvidenceClaim(
            claim_text="Well-supported finding from multiple RCTs",
            claim_type=ClaimType.CLINICAL,
            sources=sources,
            confidence=ConfidenceLevel.MODERATE,
            source_consistency="consistent",
            directness="direct"
        )

        assessment = calibrator.assess_claim_confidence(claim)

        assert assessment.confidence_level in [
            ConfidenceLevel.MODERATE,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.ESTABLISHED
        ]
        assert assessment.raw_score >= 46.0

    def test_inconsistent_sources_lower_confidence(self):
        """Test inconsistent sources lower confidence score."""
        calibrator = ConfidenceCalibrator()

        sources = [
            Source(
                url="https://example.org/study1",
                title="Study 1",
                source_type=SourceType.COHORT_STUDY
            ),
            Source(
                url="https://example.org/study2",
                title="Study 2",
                source_type=SourceType.COHORT_STUDY
            )
        ]

        claim = EvidenceClaim(
            claim_text="Conflicting findings",
            claim_type=ClaimType.CLINICAL,
            sources=sources,
            confidence=ConfidenceLevel.LOW,
            source_consistency="inconsistent"
        )

        assessment = calibrator.assess_claim_confidence(claim)

        assert assessment.component_scores.get("consistency", 0) == 0.0

    def test_high_score_requires_validation(self):
        """Test scores >80 require external validation."""
        calibrator = ConfidenceCalibrator()

        # Create optimal scenario
        sources = [
            Source(
                url=f"https://pubmed.ncbi.nlm.nih.gov/{i}111111/",
                title=f"Systematic Review {i}",
                pmid=f"{i}111111",
                source_type=SourceType.SYSTEMATIC_REVIEW,
                sample_size=2000,
                verification_status=True,
                date="2024"
            )
            for i in range(1, 7)  # 6 systematic reviews
        ]

        claim = EvidenceClaim(
            claim_text="Extremely well-established finding",
            claim_type=ClaimType.CLINICAL,
            sources=sources,
            confidence=ConfidenceLevel.HIGH,
            source_consistency="consistent",
            directness="direct"
        )

        assessment = calibrator.assess_claim_confidence(claim)

        if assessment.raw_score > 80:
            assert assessment.requires_external_validation is True

    def test_assessment_components(self):
        """Test all assessment components are calculated."""
        calibrator = ConfidenceCalibrator()

        source = Source(
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            title="Test Study",
            pmid="12345678",
            source_type=SourceType.COHORT_STUDY,
            sample_size=100,
            verification_status=True,
            date="2023"
        )

        claim = EvidenceClaim(
            claim_text="Test finding",
            claim_type=ClaimType.CLINICAL,
            sources=[source],
            confidence=ConfidenceLevel.LOW
        )

        assessment = calibrator.assess_claim_confidence(claim)

        # Check all components exist
        assert "source_count" in assessment.component_scores
        assert "source_quality" in assessment.component_scores
        assert "sample_size" in assessment.component_scores

    def test_assessment_serialization(self):
        """Test assessment can be serialized."""
        calibrator = ConfidenceCalibrator()

        source = Source(
            url="https://example.org/test",
            title="Test",
            source_type=SourceType.COHORT_STUDY
        )

        claim = EvidenceClaim(
            claim_text="Test",
            claim_type=ClaimType.CLINICAL,
            sources=[source],
            confidence=ConfidenceLevel.LOW
        )

        assessment = calibrator.assess_claim_confidence(claim)
        assessment_dict = assessment.to_dict()

        assert "claim_id" in assessment_dict
        assert "confidence_level" in assessment_dict
        assert "raw_score" in assessment_dict
        assert "component_scores" in assessment_dict


@pytest.mark.unit
class TestConfidenceAssessment:
    """Test ConfidenceAssessment dataclass."""

    def test_assessment_creation(self):
        """Test creating a confidence assessment."""
        assessment = ConfidenceAssessment(
            claim_id="test-claim-123",
            confidence_level=ConfidenceLevel.MODERATE,
            raw_score=65.0,
            component_scores={"source_count": 15, "source_quality": 20},
            justification="Moderate confidence based on multiple sources",
            limitations=["Limited sample size"],
            requires_external_validation=False
        )

        assert assessment.claim_id == "test-claim-123"
        assert assessment.confidence_level == ConfidenceLevel.MODERATE
        assert assessment.raw_score == 65.0
        assert len(assessment.component_scores) == 2
        assert len(assessment.limitations) == 1

    def test_assessment_to_dict(self):
        """Test assessment to_dict method."""
        assessment = ConfidenceAssessment(
            claim_id="test-123",
            confidence_level=ConfidenceLevel.LOW,
            raw_score=30.0
        )

        assessment_dict = assessment.to_dict()

        assert assessment_dict["claim_id"] == "test-123"
        assert assessment_dict["confidence_level"] == "low"
        assert assessment_dict["raw_score"] == 30.0
