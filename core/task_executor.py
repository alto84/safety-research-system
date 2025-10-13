"""Task executor for managing worker agent execution."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from models.task import Task, TaskStatus, TaskType


logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Manages execution of tasks by worker agents.

    This class handles:
    - Assignment of tasks to appropriate worker agents
    - Execution orchestration
    - Output capture
    - Error handling and timeout management
    """

    def __init__(self, worker_registry: Optional[Dict[str, Any]] = None):
        """
        Initialize the task executor.

        Args:
            worker_registry: Dictionary mapping TaskType to worker agent instances
        """
        self.worker_registry = worker_registry or {}
        self.active_tasks: Dict[str, Task] = {}

    def register_worker(self, task_type: TaskType, worker_agent: Any) -> None:
        """
        Register a worker agent for a specific task type.

        Args:
            task_type: Type of task this worker handles
            worker_agent: Worker agent instance
        """
        self.worker_registry[task_type] = worker_agent
        logger.info(f"Registered worker for task type: {task_type.value}")

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task using the appropriate worker agent.

        Args:
            task: Task to execute

        Returns:
            Dictionary containing task output

        Raises:
            ValueError: If no worker registered for task type
            Exception: If task execution fails
        """
        if task.task_type not in self.worker_registry:
            raise ValueError(f"No worker registered for task type: {task.task_type.value}")

        logger.info(f"Executing task {task.task_id} of type {task.task_type.value}")

        # Update task status
        task.update_status(TaskStatus.IN_PROGRESS)
        task.assigned_agent = self.worker_registry[task.task_type].__class__.__name__
        self.active_tasks[task.task_id] = task

        try:
            # Get the worker agent
            worker = self.worker_registry[task.task_type]

            # Execute the task
            start_time = datetime.utcnow()
            output = worker.execute(task.input_data)
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Store output in task
            task.output_data = {
                "result": output,
                "execution_time": execution_time,
                "agent": task.assigned_agent,
            }

            # Update task status
            task.update_status(TaskStatus.COMPLETED)
            logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")

            return task.output_data

        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            task.update_status(TaskStatus.FAILED)
            task.metadata["error"] = str(e)
            raise

        finally:
            # Remove from active tasks
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task

        Returns:
            Task status or None if task not found
        """
        task = self.active_tasks.get(task_id)
        return task.status if task else None

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            True if task was cancelled, False otherwise
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Cannot cancel task {task_id}: not found in active tasks")
            return False

        task = self.active_tasks[task_id]
        task.update_status(TaskStatus.FAILED)
        task.metadata["cancelled"] = True
        del self.active_tasks[task_id]

        logger.info(f"Task {task_id} cancelled")
        return True

    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self.active_tasks)
