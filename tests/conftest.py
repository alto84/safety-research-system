"""
Pytest Configuration and Shared Fixtures
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.evidence import Source, EvidenceClaim, EvidenceChain, ClaimType, ConfidenceLevel, SourceType
from models.task import Task, TaskType, TaskStatus
from models.case import Case
from models.audit_result import AuditResult, AuditStatus


# =============================================================================
# Source Fixtures
# =============================================================================

@pytest.fixture
def basic_source():
    """Create a basic source for testing."""
    return Source(
        url="https://pubmed.ncbi.nlm.nih.gov/32272236/",
        title="Test Research Paper",
        authors=["Smith, J.", "Doe, A."],
        date="2023",
        pmid="32272236"
    )


@pytest.fixture
def peer_reviewed_source():
    """Create a peer-reviewed source (with PMID)."""
    return Source(
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        title="Peer-Reviewed Study on ADC Mechanisms",
        authors=["Researcher A", "Scientist B", "Expert C"],
        date="2024",
        pmid="12345678",
        source_type=SourceType.RANDOMIZED_CONTROLLED_TRIAL,
        sample_size=500,
        verification_status=True
    )


@pytest.fixture
def multiple_sources(peer_reviewed_source):
    """Create multiple sources for testing."""
    sources = [peer_reviewed_source]

    for i in range(2, 5):
        sources.append(Source(
            url=f"https://pubmed.ncbi.nlm.nih.gov/{i}2345678/",
            title=f"Study {i}",
            authors=[f"Author {i}"],
            date="2023",
            pmid=f"{i}2345678",
            source_type=SourceType.COHORT_STUDY
        ))

    return sources


# =============================================================================
# Evidence Claim Fixtures
# =============================================================================

@pytest.fixture
def basic_claim(basic_source):
    """Create a basic evidence claim."""
    return EvidenceClaim(
        claim_text="ILD incidence is approximately 15% in clinical trials",
        claim_type=ClaimType.NUMERICAL,
        sources=[basic_source],
        confidence=ConfidenceLevel.MODERATE
    )


@pytest.fixture
def numerical_claim(peer_reviewed_source):
    """Create a numerical claim."""
    return EvidenceClaim(
        claim_text="T-DXd shows 15% ILD incidence in DESTINY-Breast01",
        claim_type=ClaimType.NUMERICAL,
        sources=[peer_reviewed_source],
        confidence=ConfidenceLevel.MODERATE,
        numerical_value=15.0,
        unit="%"
    )


@pytest.fixture
def mechanistic_claim(multiple_sources):
    """Create a mechanistic claim."""
    return EvidenceClaim(
        claim_text="TGF-β drives pulmonary fibrosis through SMAD signaling",
        claim_type=ClaimType.MECHANISTIC,
        sources=multiple_sources,
        confidence=ConfidenceLevel.HIGH
    )


# =============================================================================
# Evidence Chain Fixtures
# =============================================================================

@pytest.fixture
def evidence_chain(basic_claim, mechanistic_claim):
    """Create an evidence chain with multiple claims."""
    chain = EvidenceChain(description="Test evidence chain")
    chain.add_claim(basic_claim)
    chain.add_claim(mechanistic_claim)
    return chain


# =============================================================================
# Task Fixtures
# =============================================================================

@pytest.fixture
def basic_task():
    """Create a basic research task."""
    return Task(
        task_type=TaskType.LITERATURE_REVIEW,
        input_data={
            "query": "What is the mechanism of ADC-induced ILD?",
            "context": {"therapeutic_class": "ADC"}
        }
    )


@pytest.fixture
def statistics_task():
    """Create a statistics analysis task."""
    return Task(
        task_type=TaskType.STATISTICAL_ANALYSIS,
        input_data={
            "data": [1.0, 2.0, 3.0, 4.0, 5.0],
            "analysis_type": "descriptive"
        }
    )


# =============================================================================
# Research Case Fixtures
# =============================================================================

@pytest.fixture
def basic_case():
    """Create a basic research case."""
    return Case(
        case_id="TEST-001",
        title="ADC-ILD Mechanism Investigation",
        description="Investigate the mechanistic basis of ILD in ADC treatment"
    )


# =============================================================================
# Audit Result Fixtures
# =============================================================================

@pytest.fixture
def passing_audit():
    """Create a passing audit result."""
    return AuditResult(
        status=AuditStatus.PASSED,
        issues=[],
        recommendations=["Continue with current approach"],
        metadata={"auditor": "test_auditor"}
    )


@pytest.fixture
def failing_audit():
    """Create a failing audit result."""
    return AuditResult(
        status=AuditStatus.FAILED,
        issues=[
            {
                "severity": "critical",
                "category": "fabricated_source",
                "description": "Source contains placeholder data"
            }
        ],
        recommendations=["Replace placeholder sources with real references"],
        metadata={"auditor": "test_auditor"}
    )


# =============================================================================
# Mock LLM Fixtures
# =============================================================================

@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response."""
    return {
        "content": "This is a test LLM response",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        "model": "test-model"
    }


@pytest.fixture
def mock_llm_client(mock_llm_response):
    """Create a mock LLM client."""
    client = Mock()
    client.generate.return_value = mock_llm_response
    return client


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def sample_research_output():
    """Create sample research output for testing."""
    return {
        "executive_summary": "ADCs can cause ILD through immune-mediated mechanisms",
        "key_findings": [
            "ILD incidence varies from 10-15% across different ADCs",
            "T-DXd shows higher ILD rates than T-DM1",
            "Early detection improves outcomes"
        ],
        "sources": [
            {
                "title": "Real Study on ADC Safety",
                "authors": ["Smith J", "Doe A"],
                "year": "2023",
                "url": "https://pubmed.ncbi.nlm.nih.gov/32272236/",
                "pmid": "32272236"
            }
        ],
        "confidence": "Moderate confidence based on clinical trial data",
        "limitations": [
            "Limited to published literature",
            "Heterogeneous patient populations"
        ],
        "methodology": "Systematic literature review"
    }


@pytest.fixture
def fake_research_output():
    """Create fake/placeholder research output for audit testing."""
    return {
        "summary": "This is fake research with placeholder data",
        "sources": [
            {
                "title": "Example Study on ADC Mechanisms",
                "authors": "Smith et al.",
                "year": "2023",
                "pmid": "12345678",  # Fake PMID
                "url": "https://example.com/fake-paper"
            }
        ],
        "confidence": "Very high confidence",
        "limitations": []
    }


# =============================================================================
# Helper Functions
# =============================================================================

@pytest.fixture
def assert_no_placeholders():
    """Helper to check for placeholder patterns in text."""
    def _check(text: str) -> None:
        forbidden_patterns = [
            "example", "placeholder", "lorem ipsum",
            "test.com", "sample", "fake", "TODO"
        ]
        text_lower = text.lower()
        for pattern in forbidden_patterns:
            assert pattern not in text_lower, f"Found placeholder pattern: {pattern}"
    return _check


@pytest.fixture
def assert_valid_pmid():
    """Helper to validate PMID format."""
    def _check(pmid: str) -> None:
        assert pmid.isdigit(), f"PMID must be numeric: {pmid}"
        assert len(pmid) <= 8, f"PMID too long: {pmid}"
        # Check for obvious fake PMIDs
        fake_pmids = ["12345678", "87654321", "11111111", "99999999"]
        assert pmid not in fake_pmids, f"Fake PMID detected: {pmid}"
    return _check


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "max_retries": 3,
        "timeout": 30,
        "enable_caching": False,
        "log_level": "INFO"
    }


# =============================================================================
# Cleanup Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state between tests."""
    yield
    # Cleanup code here if needed
