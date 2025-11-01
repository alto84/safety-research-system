"""
Performance benchmarks for the Safety Research System.

Tests cover:
- Evidence model creation performance
- Confidence calibration speed
- Audit engine throughput
- Context compression ratios
- Memory usage patterns
"""

import pytest
import time
from unittest.mock import Mock
from models.evidence import Source, EvidenceClaim, EvidenceChain, ClaimType, ConfidenceLevel, SourceType
from models.task import Task, TaskType
from core.confidence_calibrator import ConfidenceCalibrator
from core.audit_engine import AuditEngine


@pytest.mark.benchmark
class TestEvidenceModelPerformance:
    """Benchmark evidence model creation and operations."""

    def test_source_creation_speed(self, benchmark):
        """Benchmark source creation."""
        def create_source():
            return Source(
                url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                title="Benchmark Test Paper",
                authors=["Author A", "Author B"],
                date="2023",
                pmid="12345678",
                source_type=SourceType.RANDOMIZED_CONTROLLED_TRIAL
            )

        result = benchmark(create_source)
        assert result is not None

    def test_evidence_claim_creation_speed(self, benchmark, peer_reviewed_source):
        """Benchmark evidence claim creation."""
        def create_claim():
            return EvidenceClaim(
                claim_text="ILD incidence is 15% in trials",
                claim_type=ClaimType.NUMERICAL,
                sources=[peer_reviewed_source],
                confidence=ConfidenceLevel.MODERATE
            )

        result = benchmark(create_claim)
        assert result is not None

    def test_evidence_chain_build_speed(self, benchmark, multiple_sources):
        """Benchmark evidence chain creation with multiple claims."""
        def build_chain():
            chain = EvidenceChain(description="Benchmark chain")
            for i in range(10):
                claim = EvidenceClaim(
                    claim_text=f"Claim {i}",
                    claim_type=ClaimType.CLINICAL,
                    sources=[multiple_sources[i % len(multiple_sources)]],
                    confidence=ConfidenceLevel.LOW
                )
                chain.add_claim(claim)
            return chain

        result = benchmark(build_chain)
        assert len(result.claims) == 10

    def test_large_evidence_chain_serialization(self, benchmark, multiple_sources):
        """Benchmark serialization of large evidence chain."""
        # Create large chain
        chain = EvidenceChain(description="Large benchmark chain")
        for i in range(50):
            claim = EvidenceClaim(
                claim_text=f"Finding {i}: Numerical value is {i}%",
                claim_type=ClaimType.NUMERICAL,
                sources=[multiple_sources[i % len(multiple_sources)]],
                confidence=ConfidenceLevel.MODERATE
            )
            chain.add_claim(claim)

        result = benchmark(chain.to_json)
        assert result is not None


@pytest.mark.benchmark
class TestConfidenceCalibrationPerformance:
    """Benchmark confidence calibration operations."""

    def test_single_claim_assessment_speed(self, benchmark, basic_claim):
        """Benchmark single claim confidence assessment."""
        calibrator = ConfidenceCalibrator()

        result = benchmark(calibrator.assess_claim_confidence, basic_claim)
        assert result is not None

    def test_multiple_claims_assessment(self, benchmark):
        """Benchmark assessing multiple claims."""
        calibrator = ConfidenceCalibrator()

        # Create 100 claims
        claims = []
        for i in range(100):
            source = Source(
                url=f"https://example.org/paper{i}",
                title=f"Paper {i}",
                source_type=SourceType.COHORT_STUDY
            )
            claim = EvidenceClaim(
                claim_text=f"Finding {i}",
                claim_type=ClaimType.CLINICAL,
                sources=[source],
                confidence=ConfidenceLevel.LOW
            )
            claims.append(claim)

        def assess_all():
            results = []
            for claim in claims:
                results.append(calibrator.assess_claim_confidence(claim))
            return results

        results = benchmark(assess_all)
        assert len(results) == 100


@pytest.mark.benchmark
class TestAuditEnginePerformance:
    """Benchmark audit engine operations."""

    def test_audit_throughput(self, benchmark):
        """Benchmark audit engine throughput."""
        engine = AuditEngine()

        # Create mock auditor
        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "BenchmarkAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": ["check1"],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create task
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Test output"}
        )

        result = benchmark(engine.audit_task, task)
        assert result is not None

    def test_multiple_audits_performance(self, benchmark):
        """Benchmark multiple sequential audits."""
        engine = AuditEngine()

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "BenchmarkAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create 50 tasks
        tasks = [
            Task(
                task_type=TaskType.LITERATURE_REVIEW,
                output_data={"result": f"Output {i}"}
            )
            for i in range(50)
        ]

        def audit_all():
            results = []
            for task in tasks:
                results.append(engine.audit_task(task))
            return results

        results = benchmark(audit_all)
        assert len(results) == 50


@pytest.mark.benchmark
class TestMemoryUsage:
    """Benchmark memory usage patterns."""

    def test_large_source_list_memory(self):
        """Test memory usage with large source lists."""
        import sys

        # Create 1000 sources
        sources = []
        for i in range(1000):
            source = Source(
                url=f"https://pubmed.ncbi.nlm.nih.gov/{i:08d}/",
                title=f"Paper {i}",
                authors=[f"Author {j}" for j in range(5)],
                date="2023",
                pmid=f"{i:08d}",
                source_type=SourceType.COHORT_STUDY
            )
            sources.append(source)

        # Rough size check
        size = sys.getsizeof(sources)
        assert size > 0
        assert len(sources) == 1000

    def test_evidence_chain_memory_growth(self):
        """Test memory growth with increasing chain size."""
        import sys

        source = Source(
            url="https://example.org/paper",
            title="Test Paper",
            source_type=SourceType.COHORT_STUDY
        )

        chain = EvidenceChain(description="Memory test")

        # Add 500 claims
        for i in range(500):
            claim = EvidenceClaim(
                claim_text=f"Claim {i}",
                claim_type=ClaimType.CLINICAL,
                sources=[source],
                confidence=ConfidenceLevel.LOW
            )
            chain.add_claim(claim)

        assert len(chain.claims) == 500
        size = sys.getsizeof(chain.claims)
        assert size > 0


@pytest.mark.benchmark
class TestSerializationPerformance:
    """Benchmark serialization performance."""

    def test_source_dict_conversion(self, benchmark, peer_reviewed_source):
        """Benchmark source to_dict conversion."""
        result = benchmark(lambda: peer_reviewed_source.to_dict() if hasattr(peer_reviewed_source, 'to_dict') else vars(peer_reviewed_source))
        assert result is not None

    def test_claim_dict_conversion(self, benchmark, numerical_claim):
        """Benchmark claim to_dict conversion."""
        result = benchmark(numerical_claim.to_dict)
        assert result is not None

    def test_chain_json_serialization(self, benchmark, evidence_chain):
        """Benchmark chain JSON serialization."""
        result = benchmark(evidence_chain.to_json)
        assert result is not None
        assert len(result) > 0


@pytest.mark.benchmark
class TestValidationPerformance:
    """Benchmark validation operations."""

    def test_evidence_chain_validation(self, benchmark):
        """Benchmark evidence chain validation."""
        # Create chain
        source = Source(
            url="https://example.org/paper",
            title="Test Paper",
            source_type=SourceType.SYSTEMATIC_REVIEW
        )

        chain = EvidenceChain(description="Validation benchmark")
        for i in range(100):
            claim = EvidenceClaim(
                claim_text=f"Claim {i}",
                claim_type=ClaimType.CLINICAL,
                sources=[source],
                confidence=ConfidenceLevel.MODERATE
            )
            chain.add_claim(claim)

        result = benchmark(chain.validate_all)
        assert result["is_valid"]
        assert result["total_claims"] == 100
