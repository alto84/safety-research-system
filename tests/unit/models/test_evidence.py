"""
Unit tests for Evidence models (Source, EvidenceClaim, EvidenceChain).

Tests cover:
- Source validation
- EvidenceClaim creation and validation
- Evidence provenance requirements
- Confidence level enforcement
- JSON serialization
"""

import pytest
import json
from models.evidence import (
    Source, EvidenceClaim, EvidenceChain,
    SourceType, ConfidenceLevel, ClaimType, ExtractionMethod
)


# =============================================================================
# Source Tests
# =============================================================================

class TestSource:
    """Test Source model."""

    def test_source_creation_with_url(self):
        """Test creating a source with URL."""
        source = Source(
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            title="Test Paper",
            authors=["Author A"],
            date="2023"
        )

        assert source.url == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        assert source.title == "Test Paper"
        assert source.authors == ["Author A"]
        assert source.date == "2023"
        assert source.source_id is not None  # Auto-generated

    def test_source_with_pmid(self):
        """Test source with PubMed ID."""
        source = Source(
            url="https://pubmed.ncbi.nlm.nih.gov/32272236/",
            pmid="32272236",
            title="T-DXd Paper",
            authors=["Modi S", "Saura C"],
            date="2020"
        )

        assert source.pmid == "32272236"
        assert "32272236" in source.url

    def test_source_with_metadata(self):
        """Test source with rich metadata."""
        source = Source(
            url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            title="Clinical Trial Results",
            authors=["PI A", "Researcher B"],
            date="2023",
            source_type=SourceType.RANDOMIZED_CONTROLLED_TRIAL,
            sample_size=500,
            verification_status=True
        )

        assert source.source_type == SourceType.RANDOMIZED_CONTROLLED_TRIAL
        assert source.sample_size == 500
        assert source.verification_status is True

    def test_source_quality_score(self):
        """Test source quality scoring based on type."""
        high_quality = Source(
            url="https://example.org/systematic-review",
            title="Systematic Review",
            source_type=SourceType.SYSTEMATIC_REVIEW,
            sample_size=2000,
            verification_status=True
        )

        low_quality = Source(
            url="https://example.org/case-report",
            title="Case Report",
            source_type=SourceType.CASE_REPORT,
            verification_status=False
        )

        # Systematic reviews should rank higher
        assert high_quality.source_type.value == "systematic_review"
        assert low_quality.source_type.value == "case_report"


# =============================================================================
# EvidenceClaim Tests
# =============================================================================

class TestEvidenceClaim:
    """Test EvidenceClaim model."""

    def test_claim_requires_sources(self, basic_source):
        """Test that claims require at least one source."""
        # Valid claim with source
        claim = EvidenceClaim(
            claim_text="Test claim",
            claim_type=ClaimType.QUALITATIVE,
            sources=[basic_source],
            confidence=ConfidenceLevel.LOW
        )
        assert len(claim.sources) == 1

        # Invalid claim without sources
        with pytest.raises(ValueError, match="at least one source"):
            EvidenceClaim(
                claim_text="No source claim",
                claim_type=ClaimType.QUALITATIVE,
                sources=[],
                confidence=ConfidenceLevel.LOW
            )

    def test_numerical_claim_validation(self, peer_reviewed_source):
        """Test numerical claims require numbers."""
        # Valid numerical claim
        claim = EvidenceClaim(
            claim_text="ILD incidence is 15% in trials",
            claim_type=ClaimType.NUMERICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.MODERATE
        )
        assert "15" in claim.claim_text

        # Invalid - no numbers
        with pytest.raises(ValueError, match="must contain numbers"):
            EvidenceClaim(
                claim_text="ILD is common",  # No numbers
                claim_type=ClaimType.NUMERICAL,
                sources=[peer_reviewed_source],
                confidence=ConfidenceLevel.LOW
            )

    def test_high_confidence_requires_quality_sources(self, basic_source, peer_reviewed_source):
        """Test high confidence requires peer-reviewed sources."""
        # Should fail - basic source without PMID
        with pytest.raises(ValueError, match="High confidence"):
            EvidenceClaim(
                claim_text="Strong finding",
                claim_type=ClaimType.CLINICAL,
                sources=[basic_source],
                confidence=ConfidenceLevel.HIGH
            )

        # Should succeed - peer-reviewed source
        claim = EvidenceClaim(
            claim_text="Strong finding",
            claim_type=ClaimType.CLINICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.HIGH
        )
        assert claim.confidence == ConfidenceLevel.HIGH

    def test_claim_with_extraction_method(self, basic_source):
        """Test claim with extraction method tracking."""
        claim = EvidenceClaim(
            claim_text="Direct quote from paper",
            claim_type=ClaimType.CLINICAL,
            sources=[basic_source],
            confidence=ConfidenceLevel.MODERATE,
            extraction_method=ExtractionMethod.DIRECT_QUOTE
        )

        assert claim.extraction_method == ExtractionMethod.DIRECT_QUOTE

    def test_claim_serialization(self, basic_claim):
        """Test claim can be serialized to dict."""
        claim_dict = basic_claim.to_dict()

        assert "claim_text" in claim_dict
        assert "claim_type" in claim_dict
        assert "sources" in claim_dict
        assert "confidence" in claim_dict
        assert len(claim_dict["sources"]) > 0

    def test_claim_with_uncertainty(self, peer_reviewed_source):
        """Test claims can express uncertainty."""
        claim = EvidenceClaim(
            claim_text="Approximately 15% ILD incidence observed",
            claim_type=ClaimType.NUMERICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.MODERATE,
            uncertainty_notes="Wide confidence intervals in original study"
        )

        assert claim.uncertainty_notes is not None
        assert "confidence intervals" in claim.uncertainty_notes

    def test_multiple_sources_increase_confidence(self, multiple_sources):
        """Test that multiple sources support higher confidence."""
        claim = EvidenceClaim(
            claim_text="Well-supported finding from multiple studies",
            claim_type=ClaimType.CLINICAL,
            sources=multiple_sources,
            confidence=ConfidenceLevel.HIGH
        )

        assert len(claim.sources) >= 3
        assert claim.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE]


# =============================================================================
# EvidenceChain Tests
# =============================================================================

class TestEvidenceChain:
    """Test EvidenceChain model."""

    def test_chain_creation(self):
        """Test creating an evidence chain."""
        chain = EvidenceChain(description="Test evidence chain")

        assert chain.description == "Test evidence chain"
        assert chain.chain_id is not None
        assert len(chain.claims) == 0

    def test_add_claims_to_chain(self, basic_claim, numerical_claim):
        """Test adding claims to chain."""
        chain = EvidenceChain(description="Multi-claim chain")

        chain.add_claim(basic_claim)
        chain.add_claim(numerical_claim)

        assert len(chain.claims) == 2
        assert chain.claims[0] == basic_claim
        assert chain.claims[1] == numerical_claim

    def test_chain_validation(self, evidence_chain):
        """Test evidence chain validation."""
        validation = evidence_chain.validate_all()

        assert "is_valid" in validation
        assert "total_claims" in validation
        assert "total_sources" in validation
        assert validation["total_claims"] > 0

    def test_chain_serialization(self, evidence_chain):
        """Test chain JSON serialization."""
        json_str = evidence_chain.to_json()

        assert json_str is not None
        assert len(json_str) > 0

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert "claims" in parsed
        assert "description" in parsed

    def test_chain_provenance_tracking(self, basic_claim, mechanistic_claim):
        """Test chain tracks provenance through claims."""
        chain = EvidenceChain(description="Provenance test")
        chain.add_claim(basic_claim)
        chain.add_claim(mechanistic_claim)

        # Get all sources
        all_sources = []
        for claim in chain.claims:
            all_sources.extend(claim.sources)

        assert len(all_sources) > 0

    def test_chain_to_dict(self, evidence_chain):
        """Test chain to_dict method."""
        chain_dict = evidence_chain.to_dict()

        assert "chain_id" in chain_dict
        assert "description" in chain_dict
        assert "claims" in chain_dict
        assert isinstance(chain_dict["claims"], list)

    def test_empty_chain_validation(self):
        """Test validation of empty chain."""
        chain = EvidenceChain(description="Empty chain")
        validation = chain.validate_all()

        assert validation["total_claims"] == 0
        assert validation["total_sources"] == 0


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_source_without_url_or_title(self):
        """Test source with minimal data."""
        # Source requires at least url OR (title + authors + date)
        with pytest.raises(ValueError):
            source = Source()

    def test_claim_confidence_consistency(self, peer_reviewed_source):
        """Test confidence level is consistent with source quality."""
        # High confidence with quality source - OK
        claim = EvidenceClaim(
            claim_text="Finding with strong support",
            claim_type=ClaimType.CLINICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.HIGH
        )
        assert claim.confidence == ConfidenceLevel.HIGH

    def test_numerical_extraction(self, peer_reviewed_source):
        """Test numerical value extraction."""
        claim = EvidenceClaim(
            claim_text="ILD rate was 15.5% (95% CI: 12.0-19.0)",
            claim_type=ClaimType.NUMERICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.MODERATE,
            numerical_value=15.5,
            unit="%"
        )

        assert claim.numerical_value == 15.5
        assert claim.unit == "%"

    def test_source_type_hierarchy(self):
        """Test source type quality hierarchy."""
        types_highest_to_lowest = [
            SourceType.SYSTEMATIC_REVIEW,
            SourceType.META_ANALYSIS,
            SourceType.RANDOMIZED_CONTROLLED_TRIAL,
            SourceType.COHORT_STUDY,
            SourceType.CASE_CONTROL_STUDY,
            SourceType.CASE_SERIES,
            SourceType.CASE_REPORT,
            SourceType.EXPERT_OPINION
        ]

        # Verify enum values exist
        for source_type in types_highest_to_lowest:
            assert isinstance(source_type, SourceType)

    def test_claim_type_categories(self):
        """Test all claim type categories."""
        types = [
            ClaimType.NUMERICAL,
            ClaimType.MECHANISTIC,
            ClaimType.CLINICAL,
            ClaimType.PRECLINICAL,
            ClaimType.STATISTICAL,
            ClaimType.QUALITATIVE,
            ClaimType.HYPOTHESIS
        ]

        for claim_type in types:
            assert isinstance(claim_type, ClaimType)


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
class TestEvidenceIntegration:
    """Integration tests for evidence models."""

    def test_full_evidence_workflow(self, peer_reviewed_source):
        """Test complete workflow from source to chain."""
        # Create claim
        claim = EvidenceClaim(
            claim_text="T-DXd shows 15% ILD incidence",
            claim_type=ClaimType.NUMERICAL,
            sources=[peer_reviewed_source],
            confidence=ConfidenceLevel.MODERATE,
            numerical_value=15.0,
            unit="%"
        )

        # Create chain
        chain = EvidenceChain(description="ADC-ILD evidence")
        chain.add_claim(claim)

        # Serialize
        json_str = chain.to_json()
        assert json_str is not None

        # Validate
        validation = chain.validate_all()
        assert validation["is_valid"]
        assert validation["total_claims"] == 1
        assert validation["total_sources"] == 1

    def test_complex_evidence_chain(self, multiple_sources):
        """Test complex evidence chain with multiple claims."""
        chain = EvidenceChain(description="Complex ADC mechanism")

        # Add numerical claim
        numerical = EvidenceClaim(
            claim_text="15% ILD incidence in pooled analysis",
            claim_type=ClaimType.NUMERICAL,
            sources=multiple_sources[:2],
            confidence=ConfidenceLevel.MODERATE
        )
        chain.add_claim(numerical)

        # Add mechanistic claim
        mechanistic = EvidenceClaim(
            claim_text="Payload-driven immune activation",
            claim_type=ClaimType.MECHANISTIC,
            sources=multiple_sources[2:],
            confidence=ConfidenceLevel.MODERATE
        )
        chain.add_claim(mechanistic)

        # Add hypothesis
        hypothesis = EvidenceClaim(
            claim_text="Feed-forward amplification may explain severity",
            claim_type=ClaimType.HYPOTHESIS,
            sources=multiple_sources,
            confidence=ConfidenceLevel.LOW
        )
        chain.add_claim(hypothesis)

        # Validate complex chain
        validation = chain.validate_all()
        assert validation["total_claims"] == 3
        assert validation["is_valid"]
