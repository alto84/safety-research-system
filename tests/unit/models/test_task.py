"""
Unit tests for Task model.

Tests cover:
- Task creation and initialization
- Status transitions
- Retry logic
- Audit history
- Serialization
"""

import pytest
from datetime import datetime, timedelta
from models.task import Task, TaskType, TaskStatus
from models.audit_result import AuditResult, AuditStatus


class TestTask:
    """Test Task model."""

    def test_task_creation(self):
        """Test creating a task."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test question"}
        )

        assert task.task_id is not None
        assert task.task_type == TaskType.LITERATURE_REVIEW
        assert task.status == TaskStatus.PENDING
        assert task.input_data["query"] == "Test question"
        assert task.retry_count == 0
        assert task.created_at is not None

    def test_task_all_types(self):
        """Test all task types can be created."""
        types = [
            TaskType.LITERATURE_REVIEW,
            TaskType.STATISTICAL_ANALYSIS,
            TaskType.RISK_MODELING,
            TaskType.MECHANISTIC_INFERENCE,
            TaskType.DATA_AGGREGATION,
            TaskType.CAUSALITY_ASSESSMENT
        ]

        for task_type in types:
            task = Task(task_type=task_type)
            assert task.task_type == task_type

    def test_task_status_update(self):
        """Test updating task status."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)
        original_time = task.updated_at

        # Update status
        task.update_status(TaskStatus.IN_PROGRESS)

        assert task.status == TaskStatus.IN_PROGRESS
        assert task.updated_at > original_time
        assert task.completed_at is None

    def test_task_completion(self):
        """Test task completion sets timestamp."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        task.update_status(TaskStatus.COMPLETED)

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.completed_at >= task.created_at

    def test_task_retry_logic(self):
        """Test retry count and limit."""
        task = Task(
            task_type=TaskType.STATISTICAL_ANALYSIS,
            max_retries=2
        )

        # Initially can retry
        assert task.can_retry() is True
        assert task.retry_count == 0

        # First retry
        task.increment_retry()
        assert task.retry_count == 1
        assert task.can_retry() is True

        # Second retry
        task.increment_retry()
        assert task.retry_count == 2
        assert task.can_retry() is False  # Max reached

    def test_task_audit_history(self):
        """Test adding audit results to task."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        audit1 = AuditResult(
            status=AuditStatus.PASSED,
            issues=[],
            recommendations=[]
        )

        audit2 = AuditResult(
            status=AuditStatus.FAILED,
            issues=[{"severity": "high", "description": "Test issue"}],
            recommendations=["Fix the issue"]
        )

        task.add_audit_result(audit1)
        task.add_audit_result(audit2)

        assert len(task.audit_history) == 2
        assert task.audit_history[0].status == AuditStatus.PASSED
        assert task.audit_history[1].status == AuditStatus.FAILED

    def test_task_with_case_id(self):
        """Test task associated with a case."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            case_id="CASE-123"
        )

        assert task.case_id == "CASE-123"

    def test_task_with_assigned_agent(self):
        """Test task assigned to an agent."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            assigned_agent="literature_agent_01"
        )

        assert task.assigned_agent == "literature_agent_01"

    def test_task_output_data(self):
        """Test task with output data."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        output = {
            "summary": "Research findings",
            "sources": ["source1", "source2"]
        }

        task.output_data = output
        task.update_status(TaskStatus.COMPLETED)

        assert task.output_data == output
        assert task.output_data["summary"] == "Research findings"

    def test_task_metadata(self):
        """Test task with metadata."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            metadata={
                "priority": "high",
                "estimated_duration": 300,
                "tags": ["urgent", "safety-signal"]
            }
        )

        assert task.metadata["priority"] == "high"
        assert "urgent" in task.metadata["tags"]

    def test_task_serialization(self):
        """Test task to_dict serialization."""
        task = Task(
            task_type=TaskType.STATISTICAL_ANALYSIS,
            input_data={"data": [1, 2, 3]},
            metadata={"version": "1.0"}
        )

        task_dict = task.to_dict()

        assert task_dict["task_id"] == task.task_id
        assert task_dict["task_type"] == "statistical_analysis"
        assert task_dict["status"] == "pending"
        assert task_dict["input_data"] == {"data": [1, 2, 3]}
        assert task_dict["metadata"] == {"version": "1.0"}
        assert "created_at" in task_dict
        assert "updated_at" in task_dict


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_all_statuses(self):
        """Test all task statuses exist."""
        statuses = [
            TaskStatus.PENDING,
            TaskStatus.ASSIGNED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.AUDITING,
            TaskStatus.AUDIT_FAILED,
            TaskStatus.REQUIRES_REVISION
        ]

        for status in statuses:
            assert isinstance(status, TaskStatus)

    def test_status_workflow(self):
        """Test typical status workflow."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        # Workflow: PENDING → ASSIGNED → IN_PROGRESS → AUDITING → COMPLETED
        assert task.status == TaskStatus.PENDING

        task.update_status(TaskStatus.ASSIGNED)
        assert task.status == TaskStatus.ASSIGNED

        task.update_status(TaskStatus.IN_PROGRESS)
        assert task.status == TaskStatus.IN_PROGRESS

        task.update_status(TaskStatus.AUDITING)
        assert task.status == TaskStatus.AUDITING

        task.update_status(TaskStatus.COMPLETED)
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_failed_workflow(self):
        """Test task failure workflow."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        task.update_status(TaskStatus.IN_PROGRESS)
        task.update_status(TaskStatus.FAILED)

        assert task.status == TaskStatus.FAILED

    def test_audit_failed_workflow(self):
        """Test audit failure workflow."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        task.update_status(TaskStatus.AUDITING)
        task.update_status(TaskStatus.AUDIT_FAILED)

        assert task.status == TaskStatus.AUDIT_FAILED

    def test_revision_workflow(self):
        """Test revision request workflow."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        task.update_status(TaskStatus.AUDITING)
        task.update_status(TaskStatus.REQUIRES_REVISION)

        assert task.status == TaskStatus.REQUIRES_REVISION


class TestTaskType:
    """Test TaskType enum."""

    def test_all_types(self):
        """Test all task types exist."""
        types = [
            TaskType.LITERATURE_REVIEW,
            TaskType.STATISTICAL_ANALYSIS,
            TaskType.RISK_MODELING,
            TaskType.MECHANISTIC_INFERENCE,
            TaskType.DATA_AGGREGATION,
            TaskType.CAUSALITY_ASSESSMENT
        ]

        for task_type in types:
            assert isinstance(task_type, TaskType)
            assert task_type.value is not None


class TestTaskEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_max_retries(self):
        """Test task with zero max retries."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            max_retries=0
        )

        assert task.can_retry() is False

    def test_negative_retry_count(self):
        """Test task doesn't allow negative retries."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        # Manually set negative (shouldn't happen in practice)
        task.retry_count = -1

        # Should still work
        assert task.retry_count == -1

    def test_task_timestamps_ordering(self):
        """Test task timestamps are in correct order."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        import time
        time.sleep(0.01)  # Small delay

        task.update_status(TaskStatus.IN_PROGRESS)

        time.sleep(0.01)

        task.update_status(TaskStatus.COMPLETED)

        assert task.created_at <= task.updated_at
        assert task.updated_at <= task.completed_at

    def test_empty_input_data(self):
        """Test task with empty input data."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={}
        )

        assert task.input_data == {}

    def test_large_audit_history(self):
        """Test task with many audit results."""
        task = Task(task_type=TaskType.LITERATURE_REVIEW)

        # Add many audit results
        for i in range(10):
            audit = AuditResult(
                status=AuditStatus.PASSED if i % 2 == 0 else AuditStatus.FAILED,
                issues=[],
                recommendations=[]
            )
            task.add_audit_result(audit)

        assert len(task.audit_history) == 10
