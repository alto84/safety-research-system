"""Resolution engine for handling audit failures and retries."""
import logging
from typing import Dict, Any, Optional
from enum import Enum

from models.task import Task, TaskStatus
from models.audit_result import AuditResult, AuditStatus
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine


logger = logging.getLogger(__name__)


class ResolutionDecision(Enum):
    """Possible decisions from resolution engine."""
    ACCEPT = "accept"  # Audit passed, accept results
    RETRY = "retry"    # Audit failed, retry task with corrections
    ESCALATE = "escalate"  # Cannot resolve, escalate to human
    ABORT = "abort"    # Max retries exceeded or critical failure


class ResolutionEngine:
    """
    Manages resolution of audit failures through retries and escalation.

    This class implements the core loop:
    1. Task executes
    2. Audit validates
    3. If audit fails and retries available: provide corrections and retry
    4. If audit passes or max retries exceeded: finalize
    5. If critical issues: escalate to human

    The resolution engine prevents context overload by handling the
    retry loop without involving the orchestrator.
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        max_retries: int = 2,
    ):
        """
        Initialize the resolution engine.

        Args:
            task_executor: TaskExecutor instance for running tasks
            audit_engine: AuditEngine instance for validating outputs
            max_retries: Maximum retry attempts per task
        """
        self.task_executor = task_executor
        self.audit_engine = audit_engine
        self.max_retries = max_retries
        self.resolution_history: Dict[str, list] = {}

    def execute_with_validation(self, task: Task) -> tuple[ResolutionDecision, Optional[AuditResult]]:
        """
        Execute a task with automatic validation and retry on failure.

        This is the main entry point for the Task→Audit→Resolve loop.

        Args:
            task: Task to execute and validate

        Returns:
            Tuple of (ResolutionDecision, final AuditResult)
        """
        task.max_retries = self.max_retries
        resolution_log = []

        logger.info(f"Starting execution with validation for task {task.task_id}")

        while True:
            try:
                # Step 1: Execute task
                logger.info(f"Executing task {task.task_id} (attempt {task.retry_count + 1})")
                self.task_executor.execute_task(task)
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "executed",
                    "status": "success",
                })

                # Step 2: Audit task output
                logger.info(f"Auditing task {task.task_id}")
                task.update_status(TaskStatus.AUDITING)
                audit_result = self.audit_engine.audit_task(task)
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "audited",
                    "status": audit_result.status.value,
                    "issues_count": len(audit_result.issues),
                })

                # Step 3: Evaluate audit result
                decision = self._evaluate_audit_result(task, audit_result)

                if decision == ResolutionDecision.ACCEPT:
                    logger.info(f"Task {task.task_id} accepted after validation")
                    task.update_status(TaskStatus.COMPLETED)
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.RETRY:
                    logger.info(f"Task {task.task_id} requires revision (attempt {task.retry_count + 1})")
                    task.update_status(TaskStatus.REQUIRES_REVISION)
                    task.increment_retry()

                    # Prepare corrections for retry
                    corrections = self._prepare_corrections(audit_result)
                    task.input_data["corrections"] = corrections
                    task.input_data["previous_output"] = task.output_data
                    task.input_data["audit_feedback"] = audit_result.summary

                    resolution_log.append({
                        "attempt": task.retry_count,
                        "action": "retry_scheduled",
                        "corrections_count": len(corrections),
                    })

                    # Continue loop to retry
                    continue

                elif decision == ResolutionDecision.ESCALATE:
                    logger.warning(f"Task {task.task_id} escalated to human review")
                    task.update_status(TaskStatus.AUDIT_FAILED)
                    task.metadata["requires_human_review"] = True
                    task.metadata["escalation_reason"] = "Critical audit issues found"
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.ABORT:
                    logger.error(f"Task {task.task_id} aborted after {task.retry_count} attempts")
                    task.update_status(TaskStatus.FAILED)
                    task.metadata["abort_reason"] = "Max retries exceeded"
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

            except Exception as e:
                logger.error(f"Error in resolution loop for task {task.task_id}: {str(e)}")
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "error",
                    "error": str(e),
                })
                task.update_status(TaskStatus.FAILED)
                task.metadata["error"] = str(e)
                self._save_resolution_history(task.task_id, resolution_log)
                return ResolutionDecision.ABORT, None

    def _evaluate_audit_result(self, task: Task, audit_result: AuditResult) -> ResolutionDecision:
        """
        Evaluate audit result and determine next action.

        Args:
            task: Task that was audited
            audit_result: Result of the audit

        Returns:
            ResolutionDecision indicating next action
        """
        # If audit passed, accept the task
        if audit_result.status == AuditStatus.PASSED:
            return ResolutionDecision.ACCEPT

        # If audit has critical issues, escalate immediately
        if audit_result.has_critical_issues():
            logger.warning(f"Task {task.task_id} has critical issues, escalating")
            return ResolutionDecision.ESCALATE

        # If audit failed but task can retry, schedule retry
        if audit_result.status == AuditStatus.FAILED and task.can_retry():
            return ResolutionDecision.RETRY

        # If max retries exceeded, abort
        if not task.can_retry():
            logger.warning(f"Task {task.task_id} exceeded max retries")
            return ResolutionDecision.ABORT

        # Default: escalate for human review
        return ResolutionDecision.ESCALATE

    def _prepare_corrections(self, audit_result: AuditResult) -> list[Dict[str, Any]]:
        """
        Prepare correction instructions from audit result.

        Args:
            audit_result: Audit result containing issues

        Returns:
            List of correction instructions
        """
        corrections = []

        for issue in audit_result.issues:
            correction = {
                "category": issue.category,
                "severity": issue.severity.value,
                "description": issue.description,
                "location": issue.location,
                "suggested_fix": issue.suggested_fix,
                "guideline_reference": issue.guideline_reference,
            }
            corrections.append(correction)

        # Add general recommendations
        for rec in audit_result.recommendations:
            corrections.append({
                "category": "recommendation",
                "severity": "info",
                "description": rec,
            })

        return corrections

    def _save_resolution_history(self, task_id: str, resolution_log: list) -> None:
        """Save resolution history for debugging and analysis."""
        self.resolution_history[task_id] = resolution_log
        logger.debug(f"Saved resolution history for task {task_id}: {len(resolution_log)} entries")

    def get_resolution_history(self, task_id: str) -> list:
        """Get resolution history for a task."""
        return self.resolution_history.get(task_id, [])
