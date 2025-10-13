"""Evidence provenance tracking models.

This module provides comprehensive evidence tracking to ensure every claim
traces back to its source. Required by CLAUDE.md anti-fabrication protocols.

Key Features:
- Structured evidence claims with provenance
- Source validation and metadata
- Evidence chain tracking
- JSON serialization support
- Automatic validation of required fields
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid
import json
import re


class SourceType(Enum):
    """Type of evidence source, ranked by typical quality."""
    SYSTEMATIC_REVIEW = "systematic_review"  # Highest quality
    META_ANALYSIS = "meta_analysis"
    RANDOMIZED_CONTROLLED_TRIAL = "randomized_controlled_trial"
    COHORT_STUDY = "cohort_study"
    CASE_CONTROL_STUDY = "case_control_study"
    CASE_SERIES = "case_series"
    CASE_REPORT = "case_report"
    EXPERT_OPINION = "expert_opinion"  # Lowest quality
    OTHER = "other"


class ConfidenceLevel(Enum):
    """Confidence level for evidence-based claims."""
    NONE = "none"              # No evidence or purely speculative
    LOW = "low"                # Limited, weak, or inconsistent evidence
    MODERATE = "moderate"      # Multiple sources, reasonable quality
    HIGH = "high"              # Strong, consistent, direct evidence
    ESTABLISHED = "established"  # Consensus view with extensive validation


class ClaimType(Enum):
    """Types of evidence claims."""
    NUMERICAL = "numerical"  # Quantitative data (incidence rates, percentages, etc.)
    MECHANISTIC = "mechanistic"  # Mechanistic explanations or pathways
    CLINICAL = "clinical"  # Clinical observations or outcomes
    PRECLINICAL = "preclinical"  # Animal/cell studies
    STATISTICAL = "statistical"  # Statistical analyses or correlations
    QUALITATIVE = "qualitative"  # Descriptive findings
    HYPOTHESIS = "hypothesis"  # Proposed mechanisms (requires clear labeling)


class ExtractionMethod(Enum):
    """How evidence was extracted from source."""
    DIRECT_QUOTE = "direct_quote"  # Directly quoted from source
    PARAPHRASED = "paraphrased"  # Paraphrased from source content
    SYNTHESIZED = "synthesized"  # Synthesized from multiple sources
    INFERRED = "inferred"  # Logical inference from source data
    CALCULATED = "calculated"  # Calculated from provided data


@dataclass
class Source:
    """
    Represents a single evidence source with full provenance metadata.

    Every source must have sufficient information for verification.
    At minimum, requires: url OR (title + authors + date).

    Attributes:
        source_id: Unique identifier
        url: Direct URL to source (preferred for verification)
        title: Title of the source
        authors: List of authors
        date: Publication or access date (string format: YYYY-MM-DD or YYYY)
        relevant_excerpt: Specific text excerpt supporting claim
        pmid: PubMed ID if applicable
        doi: Digital Object Identifier if applicable
        source_type: Type of source (RCT, cohort, etc.)
        sample_size: Number of participants/subjects (if applicable)
        key_findings: Relevant findings from this source
        limitations: Known limitations of this source
        credibility_notes: Notes on source quality/credibility
        verification_status: Whether source has been verified to exist
        access_date: When source was accessed
        metadata: Additional source metadata
    """
    source_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    date: Optional[str] = None
    relevant_excerpt: Optional[str] = None
    pmid: Optional[str] = None
    doi: Optional[str] = None
    source_type: Optional[SourceType] = None
    sample_size: Optional[int] = None
    key_findings: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    credibility_notes: Optional[str] = None
    verification_status: bool = False
    access_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate source has minimum required information."""
        # Must have URL or (title + authors + date)
        has_url = self.url is not None and self.url.strip() != ""
        has_citation = all([
            self.title and self.title.strip(),
            self.authors and len(self.authors) > 0,
            self.date and self.date.strip()
        ])

        if not (has_url or has_citation):
            raise ValueError(
                "Source must have either url OR (title + authors + date). "
                f"Got: url={self.url}, title={self.title}, authors={self.authors}, date={self.date}"
            )

        # Validate URL format if provided
        if self.url and self.url.strip():
            if not self.url.startswith(('http://', 'https://', 'ftp://')):
                # Try to be helpful - add https if it looks like a domain
                if '.' in self.url and ' ' not in self.url:
                    self.url = f"https://{self.url}"
                else:
                    raise ValueError(f"Invalid URL format: {self.url}")

        # Convert source_type to enum if it's a string
        if isinstance(self.source_type, str):
            try:
                self.source_type = SourceType(self.source_type)
            except ValueError:
                self.source_type = SourceType.OTHER

    def to_dict(self) -> Dict[str, Any]:
        """Convert source to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "authors": self.authors,
            "date": self.date,
            "relevant_excerpt": self.relevant_excerpt,
            "pmid": self.pmid,
            "doi": self.doi,
            "source_type": self.source_type.value if self.source_type else None,
            "sample_size": self.sample_size,
            "key_findings": self.key_findings,
            "limitations": self.limitations,
            "credibility_notes": self.credibility_notes,
            "verification_status": self.verification_status,
            "access_date": self.access_date,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """Create Source from dictionary."""
        data_copy = data.copy()

        # Convert source_type from string to enum if needed
        if 'source_type' in data_copy and data_copy['source_type']:
            if isinstance(data_copy['source_type'], str):
                try:
                    data_copy['source_type'] = SourceType(data_copy['source_type'])
                except ValueError:
                    data_copy['source_type'] = SourceType.OTHER

        # Allow regeneration of source_id
        if 'source_id' in data_copy:
            del data_copy['source_id']

        return cls(**data_copy)

    def get_citation(self) -> str:
        """Generate a human-readable citation string."""
        parts = []

        if self.authors:
            if isinstance(self.authors, list):
                if len(self.authors) > 3:
                    parts.append(f"{self.authors[0]} et al.")
                else:
                    parts.append(", ".join(self.authors))
            else:
                parts.append(str(self.authors))

        if self.title:
            parts.append(f'"{self.title}"')

        if self.date:
            parts.append(f"({self.date})")

        if self.pmid:
            parts.append(f"PMID: {self.pmid}")
        elif self.doi:
            parts.append(f"DOI: {self.doi}")
        elif self.url:
            parts.append(f"URL: {self.url}")

        return " ".join(parts) if parts else "Unknown source"


@dataclass
class EvidenceClaim:
    """
    Represents a single evidence claim with full provenance.

    Every claim must be traceable to one or more sources. This enforces
    CLAUDE.md requirements that no claim can exist without evidence chain.

    Attributes:
        claim_id: Unique identifier
        claim_text: The actual claim or finding
        claim_type: Type of claim (numerical, mechanistic, etc.)
        sources: List of Source objects supporting this claim
        confidence: Confidence level in this claim
        extraction_method: How evidence was extracted
        reasoning: Explanation of how sources support the claim
        context: Additional context for the claim
        limitations: Known limitations of this evidence
        aggregate_sample_size: Total sample size across sources
        source_consistency: Assessment of agreement between sources
        directness: How directly the evidence tests the claim
        validation_notes: Notes on validation or verification
        created_at: Timestamp of claim creation
        metadata: Additional claim metadata
    """
    claim_text: str
    claim_type: ClaimType
    sources: List[Source]
    confidence: ConfidenceLevel = ConfidenceLevel.MODERATE
    extraction_method: ExtractionMethod = ExtractionMethod.PARAPHRASED
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reasoning: str = ""
    context: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    aggregate_sample_size: int = 0
    source_consistency: Optional[str] = None  # "consistent", "mixed", "inconsistent"
    directness: Optional[str] = None  # "direct", "indirect", "very_indirect"
    validation_notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate evidence claim has required components."""
        # Must have at least one source
        if not self.sources or len(self.sources) == 0:
            raise ValueError(
                f"Evidence claim must have at least one source. "
                f"Claim: '{self.claim_text[:100] if self.claim_text else 'EMPTY'}...'"
            )

        # Validate claim_text is not empty
        if not self.claim_text or not self.claim_text.strip():
            raise ValueError("Claim text cannot be empty")

        # Numerical claims should have specific validation
        if self.claim_type == ClaimType.NUMERICAL:
            # Check that claim contains numbers
            if not re.search(r'\d', self.claim_text):
                raise ValueError(
                    f"Numerical claim must contain numbers. Got: '{self.claim_text}'"
                )

        # High confidence requires multiple sources or strong single source
        if self.confidence == ConfidenceLevel.HIGH and len(self.sources) < 2:
            # Allow single source if it has PMID (peer-reviewed)
            if not any(s.pmid for s in self.sources):
                raise ValueError(
                    "High confidence claims require multiple sources or "
                    "a single peer-reviewed source (with PMID)"
                )

        # Convert claim_type to enum if it's a string
        if isinstance(self.claim_type, str):
            try:
                self.claim_type = ClaimType(self.claim_type)
            except ValueError:
                raise ValueError(f"Invalid claim_type: {self.claim_type}")

        # Convert confidence to enum if it's a string
        if isinstance(self.confidence, str):
            try:
                self.confidence = ConfidenceLevel(self.confidence)
            except ValueError:
                raise ValueError(f"Invalid confidence level: {self.confidence}")

        # Convert extraction_method to enum if it's a string
        if isinstance(self.extraction_method, str):
            try:
                self.extraction_method = ExtractionMethod(self.extraction_method)
            except ValueError:
                raise ValueError(f"Invalid extraction_method: {self.extraction_method}")

        # Auto-calculate aggregate sample size if not set
        if self.aggregate_sample_size == 0:
            self.aggregate_sample_size = self.get_aggregate_sample_size()

    def add_source(self, source: Source) -> None:
        """Add an additional source to this claim."""
        self.sources.append(source)
        # Recalculate aggregate sample size
        self.aggregate_sample_size = self.get_aggregate_sample_size()

    def has_primary_source(self) -> bool:
        """Check if claim has at least one source."""
        return len(self.sources) > 0

    def get_source_count(self) -> int:
        """Get number of sources supporting this claim."""
        return len(self.sources)

    def get_verified_source_count(self) -> int:
        """Get number of verified sources."""
        return sum(1 for source in self.sources if source.verification_status)

    def get_aggregate_sample_size(self) -> int:
        """Calculate total sample size across all sources."""
        total = 0
        for source in self.sources:
            if source.sample_size:
                total += source.sample_size
        return total

    def get_most_recent_year(self) -> Optional[int]:
        """Get most recent publication year from sources."""
        years = []
        for s in self.sources:
            if s.date:
                # Try to extract year from date string
                match = re.search(r'\d{4}', s.date)
                if match:
                    years.append(int(match.group()))
        return max(years) if years else None

    def get_source_urls(self) -> List[str]:
        """Get list of all source URLs (for validation)."""
        return [s.url for s in self.sources if s.url]

    def get_primary_source(self) -> Source:
        """Get the primary (first) source for this claim."""
        return self.sources[0]

    def validate_provenance(self) -> Dict[str, Any]:
        """
        Validate evidence provenance chain.

        Returns dict with validation results:
        - is_valid: bool
        - issues: List[str] of validation issues
        - warnings: List[str] of warnings
        """
        issues = []
        warnings = []

        # Check all sources are properly formed
        for i, source in enumerate(self.sources):
            if not source.url and not source.title:
                issues.append(
                    f"Source {i+1} missing both URL and title"
                )

            if not source.relevant_excerpt and not source.key_findings:
                warnings.append(
                    f"Source {i+1} missing relevant excerpt/key_findings (harder to verify)"
                )

            if source.source_type is None:
                warnings.append(
                    f"Source {i+1} missing source_type classification"
                )

        # Check confidence level matches source quality
        if self.confidence == ConfidenceLevel.HIGH:
            peer_reviewed = any(s.pmid or s.doi for s in self.sources)
            if not peer_reviewed:
                warnings.append(
                    "High confidence claim without peer-reviewed sources"
                )

        # Check limitations are provided for moderate+ confidence
        if self.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MODERATE, ConfidenceLevel.ESTABLISHED]:
            if not self.limitations:
                warnings.append(
                    "Moderate/high confidence claim should include limitations"
                )

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary for JSON serialization."""
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "claim_type": self.claim_type.value,
            "sources": [s.to_dict() for s in self.sources],
            "confidence": self.confidence.value,
            "extraction_method": self.extraction_method.value,
            "reasoning": self.reasoning,
            "context": self.context,
            "limitations": self.limitations,
            "aggregate_sample_size": self.aggregate_sample_size,
            "source_consistency": self.source_consistency,
            "directness": self.directness,
            "validation_notes": self.validation_notes,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceClaim':
        """Create EvidenceClaim from dictionary."""
        data_copy = data.copy()

        # Convert enums from strings
        if 'claim_type' in data_copy:
            if isinstance(data_copy['claim_type'], str):
                data_copy['claim_type'] = ClaimType(data_copy['claim_type'])
        if 'confidence' in data_copy:
            if isinstance(data_copy['confidence'], str):
                data_copy['confidence'] = ConfidenceLevel(data_copy['confidence'])
        if 'extraction_method' in data_copy:
            if isinstance(data_copy['extraction_method'], str):
                data_copy['extraction_method'] = ExtractionMethod(data_copy['extraction_method'])

        # Convert sources from dicts
        if 'sources' in data_copy:
            data_copy['sources'] = [
                Source.from_dict(s) if isinstance(s, dict) else s
                for s in data_copy['sources']
            ]

        # Remove claim_id to allow regeneration
        if 'claim_id' in data_copy:
            del data_copy['claim_id']

        return cls(**data_copy)


@dataclass
class EvidenceChain:
    """
    Collection of evidence claims forming a complete evidence chain.

    Used to track all evidence for a research output, ensuring every
    key finding is properly sourced.

    Attributes:
        chain_id: Unique identifier for this evidence chain
        claims: List of EvidenceClaim objects
        description: Description of what this evidence chain covers
        created_at: Timestamp of creation
        metadata: Additional metadata
    """
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claims: List[EvidenceClaim] = field(default_factory=list)
    description: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_claim(self, claim: EvidenceClaim) -> None:
        """Add a claim to the evidence chain."""
        self.claims.append(claim)

    def get_all_sources(self) -> List[Source]:
        """Get all unique sources across all claims."""
        all_sources = []
        seen_ids = set()

        for claim in self.claims:
            for source in claim.sources:
                if source.source_id not in seen_ids:
                    all_sources.append(source)
                    seen_ids.add(source.source_id)

        return all_sources

    def get_claims_by_type(self, claim_type: ClaimType) -> List[EvidenceClaim]:
        """Get all claims of a specific type."""
        return [c for c in self.claims if c.claim_type == claim_type]

    def validate_all(self) -> Dict[str, Any]:
        """
        Validate entire evidence chain.

        Returns validation summary for all claims.
        """
        results = {
            "total_claims": len(self.claims),
            "total_sources": len(self.get_all_sources()),
            "claims_by_type": {},
            "invalid_claims": [],
            "warnings": [],
        }

        # Count claims by type
        for claim_type in ClaimType:
            count = len(self.get_claims_by_type(claim_type))
            if count > 0:
                results["claims_by_type"][claim_type.value] = count

        # Validate each claim
        for claim in self.claims:
            validation = claim.validate_provenance()
            if not validation["is_valid"]:
                results["invalid_claims"].append({
                    "claim_id": claim.claim_id,
                    "claim_text": claim.claim_text[:100],
                    "issues": validation["issues"],
                })
            results["warnings"].extend(validation["warnings"])

        results["is_valid"] = len(results["invalid_claims"]) == 0

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence chain to dictionary."""
        return {
            "chain_id": self.chain_id,
            "description": self.description,
            "claims": [c.to_dict() for c in self.claims],
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert evidence chain to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceChain':
        """Create EvidenceChain from dictionary."""
        data_copy = data.copy()

        # Convert claims
        if 'claims' in data_copy:
            data_copy['claims'] = [
                EvidenceClaim.from_dict(c) if isinstance(c, dict) else c
                for c in data_copy['claims']
            ]

        if 'chain_id' in data_copy:
            del data_copy['chain_id']

        return cls(**data_copy)


# Utility functions for creating evidence

def create_numerical_claim(
    claim_text: str,
    source_url: str,
    source_title: Optional[str] = None,
    relevant_excerpt: Optional[str] = None,
    confidence: ConfidenceLevel = ConfidenceLevel.MODERATE,
    pmid: Optional[str] = None,
    **kwargs
) -> EvidenceClaim:
    """
    Convenience function to create a numerical evidence claim.

    Args:
        claim_text: The numerical claim (must contain numbers)
        source_url: URL to source
        source_title: Optional title
        relevant_excerpt: Specific excerpt supporting claim
        confidence: Confidence level
        pmid: Optional PMID for peer-reviewed sources
        **kwargs: Additional arguments for Source

    Returns:
        EvidenceClaim with numerical type

    Example:
        claim = create_numerical_claim(
            claim_text="ILD incidence is 10-15% in T-DXd trials",
            source_url="https://pubmed.ncbi.nlm.nih.gov/12345678",
            source_title="T-DXd Phase 2 Trial Results",
            relevant_excerpt="ILD was observed in 15% of patients",
            pmid="12345678",
            authors=["Smith J", "Jones A"],
            date="2023"
        )
    """
    source = Source(
        url=source_url,
        title=source_title,
        relevant_excerpt=relevant_excerpt,
        pmid=pmid,
        **kwargs
    )

    return EvidenceClaim(
        claim_text=claim_text,
        claim_type=ClaimType.NUMERICAL,
        sources=[source],
        confidence=confidence,
        extraction_method=ExtractionMethod.DIRECT_QUOTE if relevant_excerpt else ExtractionMethod.PARAPHRASED,
    )


def create_mechanistic_claim(
    claim_text: str,
    sources: List[Source],
    confidence: ConfidenceLevel = ConfidenceLevel.MODERATE,
    limitations: Optional[List[str]] = None,
    reasoning: Optional[str] = None,
) -> EvidenceClaim:
    """
    Convenience function to create a mechanistic evidence claim.

    Args:
        claim_text: The mechanistic claim
        sources: List of sources (mechanistic claims often need multiple)
        confidence: Confidence level
        limitations: Known limitations
        reasoning: Explanation of how sources support the claim

    Returns:
        EvidenceClaim with mechanistic type

    Example:
        source1 = Source(
            url="https://example.com/paper1",
            title="ADC Mechanism Study",
            authors=["Researcher A"],
            date="2023"
        )
        source2 = Source(
            url="https://example.com/paper2",
            title="ILD Pathophysiology",
            authors=["Scientist B"],
            date="2024"
        )

        claim = create_mechanistic_claim(
            claim_text="ADC payload causes pneumocyte apoptosis",
            sources=[source1, source2],
            confidence=ConfidenceLevel.MODERATE,
            limitations=["Based on preclinical models"],
            reasoning="Both studies show cytotoxic effects on lung cells"
        )
    """
    return EvidenceClaim(
        claim_text=claim_text,
        claim_type=ClaimType.MECHANISTIC,
        sources=sources,
        confidence=confidence,
        extraction_method=ExtractionMethod.SYNTHESIZED,
        limitations=limitations or [],
        reasoning=reasoning or "",
    )
