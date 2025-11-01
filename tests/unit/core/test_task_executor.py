"""
Unit tests for TaskExecutor.

Tests cover:
- Worker registration
- Task execution
- Status management
- Error handling
"""

import pytest
from unittest.mock import Mock, MagicMock
from models.task import Task, TaskType, TaskStatus
from core.task_executor import TaskExecutor


class TestTaskExecutor:
    """Test TaskExecutor class."""

    def test_executor_creation(self):
        """Test creating task executor."""
        executor = TaskExecutor(enable_intelligent_routing=False)
        assert executor is not None
        assert len(executor.worker_registry) == 0
        assert len(executor.active_tasks) == 0

    def test_register_worker(self):
        """Test registering a worker."""
        executor = TaskExecutor(enable_intelligent_routing=False)
        mock_worker = Mock()

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        assert TaskType.LITERATURE_REVIEW in executor.worker_registry
        assert executor.worker_registry[TaskType.LITERATURE_REVIEW] == mock_worker

    def test_execute_task_success(self):
        """Test successful task execution."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        # Create mock worker
        mock_worker = Mock()
        mock_worker.__class__.__name__ = "TestWorker"
        mock_worker.execute.return_value = {
            "result": "Task completed successfully"
        }

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        # Create task
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test question"}
        )

        # Execute
        output = executor.execute_task(task)

        # executor.execute_task returns the full output dict
        assert output is not None
        assert "result" in output or task.output_data is not None
        assert task.status == TaskStatus.COMPLETED
        mock_worker.execute.assert_called_once()

    def test_execute_task_no_worker(self):
        """Test executing task with no registered worker."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "Test"}
        )

        with pytest.raises(ValueError, match="No worker registered"):
            executor.execute_task(task)

    def test_execute_task_updates_status(self):
        """Test task status is updated during execution."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "TestWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        task = Task(task_type=TaskType.LITERATURE_REVIEW)
        assert task.status == TaskStatus.PENDING

        executor.execute_task(task)

        assert task.status == TaskStatus.COMPLETED

    def test_multiple_workers(self):
        """Test executor with multiple workers."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        lit_worker = Mock()
        lit_worker.__class__.__name__ = "LiteratureWorker"
        lit_worker.execute.return_value = {"result": "Lit result"}

        stats_worker = Mock()
        stats_worker.__class__.__name__ = "StatsWorker"
        stats_worker.execute.return_value = {"result": "Stats result"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, lit_worker)
        executor.register_worker(TaskType.STATISTICAL_ANALYSIS, stats_worker)

        lit_task = Task(task_type=TaskType.LITERATURE_REVIEW)
        stats_task = Task(task_type=TaskType.STATISTICAL_ANALYSIS)

        lit_output = executor.execute_task(lit_task)
        stats_output = executor.execute_task(stats_task)

        assert lit_output["result"] == "Lit result"
        assert stats_output["result"] == "Stats result"
        lit_worker.execute.assert_called_once()
        stats_worker.execute.assert_called_once()

    def test_active_tasks_tracking(self):
        """Test active tasks are tracked."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "TestWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        task = Task(task_type=TaskType.LITERATURE_REVIEW)
        executor.execute_task(task)

        assert task.task_id in executor.active_tasks


@pytest.mark.unit
class TestTaskExecutorEdgeCases:
    """Test edge cases for TaskExecutor."""

    def test_execute_empty_input(self):
        """Test executing task with empty input."""
        executor = TaskExecutor(enable_intelligent_routing=False)

        mock_worker = Mock()
        mock_worker.__class__.__name__ = "TestWorker"
        mock_worker.execute.return_value = {"result": "OK"}

        executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)

        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={}
        )

        output = executor.execute_task(task)
        assert output is not None
