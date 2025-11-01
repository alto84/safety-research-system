"""
Extended integration tests for end-to-end workflows.

Tests cover:
- Complete research workflows
- Multi-agent orchestration
- Audit-resolve cycles
- Cross-module integration
"""

import pytest
from unittest.mock import Mock, MagicMock
from models.task import Task, TaskType, TaskStatus
from models.case import Case, CaseStatus, CasePriority
from models.evidence import Source, EvidenceClaim, ConfidenceLevel, ClaimType, SourceType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.confidence_calibrator import ConfidenceCalibrator


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    def test_case_to_completion(self):
        """Test case from submission to completion."""
        # Create case
        case = Case(
            title="Test Safety Question",
            description="Comprehensive safety review",
            question="What are the risks?",
            priority=CasePriority.HIGH
        )

        assert case.status == CaseStatus.SUBMITTED

        # Move through workflow
        case.update_status(CaseStatus.ASSIGNED)
        assert case.status == CaseStatus.ASSIGNED

        # Add tasks
        case.add_task("task-001")
        case.add_task("task-002")
        assert len(case.tasks) == 2

        # Add findings
        case.add_finding("risk_level", "moderate")
        case.add_finding("evidence_quality", "high")

        # Complete
        case.final_report = {
            "summary": "Comprehensive findings",
            "recommendations": ["Monitor closely"]
        }
        case.update_status(CaseStatus.COMPLETED)

        assert case.status == CaseStatus.COMPLETED
        assert case.completed_at is not None
        assert case.final_report is not None

    def test_task_execution_and_audit(self):
        """Test task execution followed by audit."""
        # Setup executor and engine
        executor = TaskExecutor(enable_intelligent_routing=False)
        engine = AuditEngine()

        # Create mock worker
        mock_worker = Mock()
        mock_worker.__class__.__name__ = "TestWorker"
        mock_worker.execute.return_value = {
            "result": "Task completed",
            "sources": [
                {
                    "title": "Real Study",
                    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
                    "pmid": "12345678"
                }
            ]
        }

        # Create mock auditor
        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "TestAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "All checks passed",
            "issues": [],
            "passed_checks": ["source_validation"],
            "failed_checks": [],
            "recommendations": []
        }

        # Register
        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)
        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create and execute task
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test question"}
        )

        output = executor.execute_task(task)
        assert task.status == TaskStatus.COMPLETED
        assert output is not None

        # Audit the task
        audit_result = engine.audit_task(task)
        assert audit_result.status.value == "passed"
        assert len(task.audit_history) == 1

    def test_evidence_chain_to_confidence_assessment(self):
        """Test building evidence chain and assessing confidence."""
        # Create sources
        sources = [
            Source(
                url="https://pubmed.ncbi.nlm.nih.gov/11111111/",
                title="Study 1",
                pmid="11111111",
                source_type=SourceType.RANDOMIZED_CONTROLLED_TRIAL,
                verification_status=True
            ),
            Source(
                url="https://pubmed.ncbi.nlm.nih.gov/22222222/",
                title="Study 2",
                pmid="22222222",
                source_type=SourceType.COHORT_STUDY,
                verification_status=True
            )
        ]

        # Create claims
        claim1 = EvidenceClaim(
            claim_text="ILD incidence is 15%",
            claim_type=ClaimType.NUMERICAL,
            sources=[sources[0]],
            confidence=ConfidenceLevel.MODERATE
        )

        claim2 = EvidenceClaim(
            claim_text="Risk increases with dose",
            claim_type=ClaimType.CLINICAL,
            sources=sources,
            confidence=ConfidenceLevel.MODERATE
        )

        # Build chain
        from models.evidence import EvidenceChain
        chain = EvidenceChain(description="ADC-ILD evidence")
        chain.add_claim(claim1)
        chain.add_claim(claim2)

        # Validate chain
        validation = chain.validate_all()
        assert validation["is_valid"]
        assert validation["total_claims"] == 2
        assert validation["total_sources"] == 2

        # Assess confidence for each claim
        calibrator = ConfidenceCalibrator()
        assessment1 = calibrator.assess_claim_confidence(claim1)
        assessment2 = calibrator.assess_claim_confidence(claim2)

        assert assessment1.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MODERATE]
        assert assessment2.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MODERATE]


@pytest.mark.integration
class TestMultiAgentOrchestration:
    """Test multi-agent orchestration scenarios."""

    def test_parallel_task_execution(self):
        """Test executing multiple tasks in parallel."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        # Create different workers
        lit_worker = Mock()
        lit_worker.__class__.__name__ = "LiteratureWorker"
        lit_worker.execute.return_value = {"result": "Literature findings"}

        stats_worker = Mock()
        stats_worker.__class__.__name__ = "StatisticsWorker"
        stats_worker.execute.return_value = {"result": "Statistical analysis"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, lit_worker)
        executor.register_worker(TaskType.STATISTICAL_ANALYSIS, stats_worker)

        # Create tasks
        lit_task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Literature question"}
        )

        stats_task = Task(
            task_type=TaskType.STATISTICAL_ANALYSIS,
            input_data={"data": [1, 2, 3]}
        )

        # Execute
        lit_output = executor.execute_task(lit_task)
        stats_output = executor.execute_task(stats_task)

        assert lit_output["result"] == "Literature findings"
        assert stats_output["result"] == "Statistical analysis"
        assert lit_task.status == TaskStatus.COMPLETED
        assert stats_task.status == TaskStatus.COMPLETED

    def test_sequential_task_dependencies(self):
        """Test tasks with dependencies."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        # Worker 1: Data aggregation
        agg_worker = Mock()
        agg_worker.__class__.__name__ = "AggregationWorker"
        agg_worker.execute.return_value = {
            "aggregated_data": [10, 20, 30, 40, 50]
        }

        # Worker 2: Statistical analysis (depends on aggregation)
        stats_worker = Mock()
        stats_worker.__class__.__name__ = "StatisticsWorker"

        def stats_execute(input_data):
            data = input_data.get("data", [])
            return {
                "mean": sum(data) / len(data) if data else 0,
                "count": len(data)
            }

        stats_worker.execute = stats_execute

        executor.register_worker(TaskType.DATA_AGGREGATION, agg_worker)
        executor.register_worker(TaskType.STATISTICAL_ANALYSIS, stats_worker)

        # Execute in sequence
        agg_task = Task(
            task_type=TaskType.DATA_AGGREGATION,
            input_data={"sources": ["source1", "source2"]}
        )

        agg_output = executor.execute_task(agg_task)

        # Use aggregation output as input to stats
        stats_task = Task(
            task_type=TaskType.STATISTICAL_ANALYSIS,
            input_data={"data": agg_output["aggregated_data"]}
        )

        stats_output = executor.execute_task(stats_task)

        assert stats_output["mean"] == 30.0
        assert stats_output["count"] == 5


@pytest.mark.integration
class TestAuditResolveLoop:
    """Test audit-resolve-retry loops."""

    def test_retry_on_audit_failure(self):
        """Test task retry when audit fails."""
        executor = TaskExecutor(enable_intelligent_routing=False)
        engine = AuditEngine()

        # Worker that improves on retry
        attempt_count = {"count": 0}

        def execute_with_improvement(input_data):
            attempt_count["count"] += 1
            if attempt_count["count"] == 1:
                # First attempt: bad output
                return {"result": "Bad output", "quality": "low"}
            else:
                # Second attempt: good output
                return {"result": "Good output", "quality": "high"}

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "ImprovingWorker"
        mock_worker.execute = execute_with_improvement

        # Auditor that fails first attempt
        audit_attempt = {"count": 0}

        def audit_with_feedback(task_input, task_output, task_metadata):
            audit_attempt["count"] += 1
            if task_output.get("quality") == "low":
                return {
                    "status": "failed",
                    "summary": "Poor quality output",
                    "issues": [
                        {
                            "category": "quality",
                            "severity": "critical",
                            "description": "Output quality insufficient"
                        }
                    ],
                    "passed_checks": [],
                    "failed_checks": ["quality_check"],
                    "recommendations": ["Improve output quality"]
                }
            else:
                return {
                    "status": "passed",
                    "summary": "Quality acceptable",
                    "issues": [],
                    "passed_checks": ["quality_check"],
                    "failed_checks": [],
                    "recommendations": []
                }

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "QualityAuditor"
        mock_auditor.validate = audit_with_feedback

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)
        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Execute and audit
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test"},
            max_retries=2
        )

        # First execution
        output1 = executor.execute_task(task)
        audit1 = engine.audit_task(task)

        assert audit1.status.value == "failed"
        assert task.can_retry()

        # Retry
        task.increment_retry()
        task.update_status(TaskStatus.PENDING)
        output2 = executor.execute_task(task)
        audit2 = engine.audit_task(task)

        assert audit2.status.value == "passed"
        assert attempt_count["count"] == 2


@pytest.mark.integration
@pytest.mark.slow
class TestLargeScaleIntegration:
    """Test large-scale integration scenarios."""

    def test_100_tasks_workflow(self):
        """Test processing 100 tasks through the system."""
        executor = TaskExecutor(enable_intelligent_routing=False)
        engine = AuditEngine()

        # Simple worker and auditor
        mock_worker = Mock()
        mock_worker.__class__.__name__ = "BulkWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "BulkAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)
        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create and process 100 tasks
        completed_count = 0
        for i in range(100):
            task = Task(
                task_type=TaskType.LITERATURE_REVIEW,
                input_data={"query": f"Question {i}"}
            )

            executor.execute_task(task)
            engine.audit_task(task)

            if task.status == TaskStatus.COMPLETED:
                completed_count += 1

        assert completed_count == 100
