"""
Load and stress tests for the system.

Tests cover:
- High concurrency scenarios
- Large data volumes
- Memory pressure
- Long-running operations
"""

import pytest
from unittest.mock import Mock
from models.evidence import Source, EvidenceClaim, EvidenceChain, ClaimType, ConfidenceLevel, SourceType
from models.task import Task, TaskType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine


@pytest.mark.load
class TestHighConcurrency:
    """Test system under high concurrency."""

    def test_1000_sources_creation(self):
        """Test creating 1000 sources."""
        sources = []
        for i in range(1000):
            source = Source(
                url=f"https://pubmed.ncbi.nlm.nih.gov/{i:08d}/",
                title=f"Paper {i}",
                pmid=f"{i:08d}",
                source_type=SourceType.COHORT_STUDY
            )
            sources.append(source)

        assert len(sources) == 1000

    def test_500_claims_chain(self):
        """Test evidence chain with 500 claims."""
        chain = EvidenceChain(description="Large chain stress test")

        source = Source(
            url="https://example.org/paper",
            title="Test Paper",
            source_type=SourceType.COHORT_STUDY
        )

        for i in range(500):
            claim = EvidenceClaim(
                claim_text=f"Claim {i}: Finding with value {i}%",
                claim_type=ClaimType.NUMERICAL,
                sources=[source],
                confidence=ConfidenceLevel.LOW
            )
            chain.add_claim(claim)

        assert len(chain.claims) == 500

        # Validate
        validation = chain.validate_all()
        assert validation["is_valid"]
        assert validation["total_claims"] == 500

    def test_concurrent_task_execution(self):
        """Test executing many tasks concurrently."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "StressWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        # Create 200 tasks
        tasks = [
            Task(
                task_type=TaskType.LITERATURE_REVIEW,
                input_data={"query": f"Query {i}"}
            )
            for i in range(200)
        ]

        # Execute all
        for task in tasks:
            executor.execute_task(task)

        # Verify all completed
        completed = sum(1 for t in tasks if t.output_data is not None)
        assert completed == 200


@pytest.mark.load
class TestLargeDataVolumes:
    """Test system with large data volumes."""

    def test_large_source_list_per_claim(self):
        """Test claim with 100 sources."""
        sources = [
            Source(
                url=f"https://pubmed.ncbi.nlm.nih.gov/{i:08d}/",
                title=f"Study {i}",
                pmid=f"{i:08d}",
                source_type=SourceType.COHORT_STUDY
            )
            for i in range(100)
        ]

        claim = EvidenceClaim(
            claim_text="Finding supported by 100 studies",
            claim_type=ClaimType.CLINICAL,
            sources=sources,
            confidence=ConfidenceLevel.LOW
        )

        assert len(claim.sources) == 100

    def test_deep_evidence_chain_validation(self):
        """Test validating very deep evidence chain."""
        chain = EvidenceChain(description="Deep chain")

        # Add 1000 claims with varying sources
        for i in range(1000):
            num_sources = min(i % 10 + 1, 5)
            sources = [
                Source(
                    url=f"https://example.org/paper{i}_{j}",
                    title=f"Paper {i}-{j}",
                    source_type=SourceType.CASE_REPORT
                )
                for j in range(num_sources)
            ]

            claim = EvidenceClaim(
                claim_text=f"Claim {i}",
                claim_type=ClaimType.CLINICAL,
                sources=sources,
                confidence=ConfidenceLevel.LOW
            )
            chain.add_claim(claim)

        validation = chain.validate_all()
        assert validation["total_claims"] == 1000


@pytest.mark.load
class TestMemoryPressure:
    """Test system under memory pressure."""

    def test_memory_growth_with_audit_history(self):
        """Test memory with large audit history."""
        engine = AuditEngine()

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "MemoryAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create task and audit it 500 times
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Test"}
        )

        for i in range(500):
            engine.audit_task(task)

        history = engine.get_audit_history(task.task_id)
        assert len(history) == 500

    def test_large_serialization(self):
        """Test serializing large evidence structure."""
        chain = EvidenceChain(description="Serialization stress test")

        # Create 200 claims with multiple sources each
        for i in range(200):
            sources = [
                Source(
                    url=f"https://example.org/paper{i}_{j}",
                    title=f"Paper {i}-{j}",
                    authors=[f"Author {k}" for k in range(5)],
                    source_type=SourceType.COHORT_STUDY
                )
                for j in range(3)
            ]

            claim = EvidenceClaim(
                claim_text=f"Detailed claim {i} with extensive evidence",
                claim_type=ClaimType.CLINICAL,
                sources=sources,
                confidence=ConfidenceLevel.MODERATE
            )
            chain.add_claim(claim)

        # Serialize
        json_str = chain.to_json()
        assert len(json_str) > 10000  # Should be substantial


@pytest.mark.load
@pytest.mark.slow
class TestLongRunningOperations:
    """Test long-running operations."""

    def test_sustained_task_execution(self):
        """Test sustained task execution over time."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "SustainedWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        # Execute 300 tasks sequentially
        for i in range(300):
            task = Task(
                task_type=TaskType.LITERATURE_REVIEW,
                input_data={"query": f"Query {i}"}
            )
            executor.execute_task(task)

        # Verify executor still works
        final_task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Final"}
        )
        output = executor.execute_task(final_task)
        assert output is not None
