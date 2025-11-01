"""
Unit tests for AuditEngine.

Tests cover:
- Auditor registration
- Task auditing
- Audit result processing
- Issue collection
- Audit history
"""

import pytest
from unittest.mock import Mock, MagicMock
from models.task import Task, TaskType, TaskStatus
from models.audit_result import AuditResult, AuditStatus, ValidationIssue, IssueSeverity
from core.audit_engine import AuditEngine


class TestAuditEngine:
    """Test AuditEngine class."""

    def test_engine_creation(self):
        """Test creating audit engine."""
        engine = AuditEngine()
        assert engine is not None
        assert len(engine.auditor_registry) == 0
        assert len(engine.audit_history) == 0

    def test_register_auditor(self):
        """Test registering an auditor."""
        engine = AuditEngine()
        mock_auditor = Mock()

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        assert TaskType.LITERATURE_REVIEW in engine.auditor_registry
        assert engine.auditor_registry[TaskType.LITERATURE_REVIEW] == mock_auditor

    def test_audit_task_success(self):
        """Test successful task audit."""
        engine = AuditEngine()

        # Create mock auditor
        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "TestAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "All checks passed",
            "issues": [],
            "passed_checks": ["check1", "check2"],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        # Create task with output
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test"},
            output_data={"result": "Test output"}
        )

        # Audit the task
        audit_result = engine.audit_task(task)

        assert audit_result.status == AuditStatus.PASSED
        assert len(audit_result.issues) == 0
        assert len(audit_result.passed_checks) == 2
        mock_auditor.validate.assert_called_once()

    def test_audit_task_with_issues(self):
        """Test task audit that finds issues."""
        engine = AuditEngine()

        # Mock auditor that finds issues
        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "TestAuditor"
        mock_auditor.validate.return_value = {
            "status": "failed",
            "summary": "Critical issues found",
            "issues": [
                {
                    "category": "fabrication",
                    "severity": "critical",
                    "description": "Fake source detected",
                    "suggested_fix": "Replace with real source"
                }
            ],
            "passed_checks": [],
            "failed_checks": ["source_validation"],
            "recommendations": ["Add real sources"]
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Output with fake source"}
        )

        audit_result = engine.audit_task(task)

        assert audit_result.status == AuditStatus.FAILED
        assert len(audit_result.issues) == 1
        assert audit_result.issues[0].severity == IssueSeverity.CRITICAL
        assert len(audit_result.failed_checks) == 1

    def test_audit_task_no_auditor(self):
        """Test auditing task with no registered auditor."""
        engine = AuditEngine()

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Test"}
        )

        with pytest.raises(ValueError, match="No auditor registered"):
            engine.audit_task(task)

    def test_audit_task_no_output(self):
        """Test auditing task with no output."""
        engine = AuditEngine()
        mock_auditor = Mock()
        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data=None  # No output
        )

        with pytest.raises(ValueError, match="has no output"):
            engine.audit_task(task)

    def test_audit_history_tracking(self):
        """Test audit history is tracked."""
        engine = AuditEngine()

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "TestAuditor"
        mock_auditor.validate.return_value = {
            "status": "passed",
            "summary": "Test",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Test"}
        )

        # Audit twice
        audit_result1 = engine.audit_task(task)
        audit_result2 = engine.audit_task(task)

        history = engine.get_audit_history(task.task_id)
        assert len(history) == 2

    def test_get_critical_issues(self):
        """Test getting critical issues from audit history."""
        engine = AuditEngine()

        mock_auditor = Mock()
        mock_auditor.__class__.__name__ = "TestAuditor"
        mock_auditor.validate.return_value = {
            "status": "failed",
            "summary": "Issues found",
            "issues": [
                {
                    "category": "critical_issue",
                    "severity": "critical",
                    "description": "Critical problem"
                },
                {
                    "category": "warning_issue",
                    "severity": "warning",
                    "description": "Warning problem"
                }
            ],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Test"}
        )

        engine.audit_task(task)

        critical_issues = engine.get_all_critical_issues(task.task_id)
        assert len(critical_issues) == 1
        assert critical_issues[0].severity == IssueSeverity.CRITICAL


@pytest.mark.unit
class TestAuditEngineIntegration:
    """Integration tests for AuditEngine."""

    def test_multiple_task_types(self):
        """Test engine with multiple task types."""
        engine = AuditEngine()

        # Register auditors for different task types
        lit_auditor = Mock()
        lit_auditor.__class__.__name__ = "LiteratureAuditor"
        lit_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        stats_auditor = Mock()
        stats_auditor.__class__.__name__ = "StatisticsAuditor"
        stats_auditor.validate.return_value = {
            "status": "passed",
            "summary": "OK",
            "issues": [],
            "passed_checks": [],
            "failed_checks": [],
            "recommendations": []
        }

        engine.register_auditor(TaskType.LITERATURE_REVIEW, lit_auditor)
        engine.register_auditor(TaskType.STATISTICAL_ANALYSIS, stats_auditor)

        # Audit different task types
        lit_task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            output_data={"result": "Lit output"}
        )
        stats_task = Task(
            task_type=TaskType.STATISTICAL_ANALYSIS,
            output_data={"result": "Stats output"}
        )

        lit_result = engine.audit_task(lit_task)
        stats_result = engine.audit_task(stats_task)

        assert lit_result.auditor_agent == "LiteratureAuditor"
        assert stats_result.auditor_agent == "StatisticsAuditor"
        lit_auditor.validate.assert_called_once()
        stats_auditor.validate.assert_called_once()
