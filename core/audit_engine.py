"""Audit engine for validating worker agent outputs."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.task import Task, TaskType
from models.audit_result import AuditResult, AuditStatus, ValidationIssue, IssueSeverity


logger = logging.getLogger(__name__)


class AuditEngine:
    """
    Manages audit validation of worker agent outputs.

    This class handles:
    - Assignment of audits to appropriate auditor agents
    - Validation orchestration
    - Issue collection and severity assessment
    - Audit result generation
    """

    def __init__(self, auditor_registry: Optional[Dict[str, Any]] = None):
        """
        Initialize the audit engine.

        Args:
            auditor_registry: Dictionary mapping TaskType to auditor agent instances
        """
        self.auditor_registry = auditor_registry or {}
        self.audit_history: Dict[str, List[AuditResult]] = {}

    def register_auditor(self, task_type: TaskType, auditor_agent: Any) -> None:
        """
        Register an auditor agent for a specific task type.

        Args:
            task_type: Type of task this auditor validates
            auditor_agent: Auditor agent instance
        """
        self.auditor_registry[task_type] = auditor_agent
        logger.info(f"Registered auditor for task type: {task_type.value}")

    def audit_task(self, task: Task) -> AuditResult:
        """
        Audit a completed task using the appropriate auditor agent.

        Args:
            task: Task to audit (must have output_data)

        Returns:
            AuditResult containing validation results

        Raises:
            ValueError: If no auditor registered for task type or task has no output
            Exception: If audit execution fails
        """
        if task.task_type not in self.auditor_registry:
            raise ValueError(f"No auditor registered for task type: {task.task_type.value}")

        if not task.output_data:
            raise ValueError(f"Task {task.task_id} has no output to audit")

        logger.info(f"Auditing task {task.task_id} of type {task.task_type.value}")

        try:
            # Get the auditor agent
            auditor = self.auditor_registry[task.task_type]
            auditor_name = auditor.__class__.__name__

            # Create audit result object
            audit_result = AuditResult(
                task_id=task.task_id,
                auditor_agent=auditor_name,
            )

            # Execute the audit
            start_time = datetime.utcnow()
            validation_output = auditor.validate(
                task_input=task.input_data,
                task_output=task.output_data,
                task_metadata=task.metadata
            )
            audit_time = (datetime.utcnow() - start_time).total_seconds()

            # Process validation output
            self._process_validation_output(audit_result, validation_output)

            # Store audit metadata
            audit_result.metadata["audit_time"] = audit_time
            audit_result.metadata["auditor_version"] = getattr(auditor, "version", "unknown")

            # Log audit result
            logger.info(
                f"Audit of task {task.task_id} completed: {audit_result.status.value} "
                f"({len(audit_result.issues)} issues found)"
            )

            # Store in history
            if task.task_id not in self.audit_history:
                self.audit_history[task.task_id] = []
            self.audit_history[task.task_id].append(audit_result)

            # Add audit result to task
            task.add_audit_result(audit_result)

            return audit_result

        except Exception as e:
            logger.error(f"Audit of task {task.task_id} failed: {str(e)}")
            # Create failed audit result
            audit_result = AuditResult(
                task_id=task.task_id,
                auditor_agent="unknown",
                status=AuditStatus.FAILED,
                summary=f"Audit failed: {str(e)}",
            )
            audit_result.metadata["error"] = str(e)
            raise

    def _process_validation_output(
        self, audit_result: AuditResult, validation_output: Dict[str, Any]
    ) -> None:
        """
        Process validation output from auditor agent.

        Args:
            audit_result: AuditResult to populate
            validation_output: Dictionary from auditor agent
        """
        # Extract status
        status_str = validation_output.get("status", "passed")
        audit_result.status = AuditStatus(status_str.lower())

        # Extract summary
        audit_result.summary = validation_output.get("summary", "")

        # Extract passed/failed checks
        audit_result.passed_checks = validation_output.get("passed_checks", [])
        audit_result.failed_checks = validation_output.get("failed_checks", [])

        # Extract issues
        issues_data = validation_output.get("issues", [])
        for issue_data in issues_data:
            issue = ValidationIssue(
                category=issue_data.get("category", "unknown"),
                severity=IssueSeverity(issue_data.get("severity", "warning")),
                description=issue_data.get("description", ""),
                location=issue_data.get("location"),
                suggested_fix=issue_data.get("suggested_fix"),
                guideline_reference=issue_data.get("guideline_reference"),
            )
            audit_result.add_issue(issue)

        # Extract recommendations
        audit_result.recommendations = validation_output.get("recommendations", [])

        # Extract optional score (use cautiously per CLAUDE.md)
        audit_result.score = validation_output.get("score")

    def get_audit_history(self, task_id: str) -> List[AuditResult]:
        """
        Get audit history for a task.

        Args:
            task_id: ID of the task

        Returns:
            List of audit results for the task
        """
        return self.audit_history.get(task_id, [])

    def get_all_critical_issues(self, task_id: str) -> List[ValidationIssue]:
        """
        Get all critical issues from all audits of a task.

        Args:
            task_id: ID of the task

        Returns:
            List of critical validation issues
        """
        critical_issues = []
        for audit_result in self.audit_history.get(task_id, []):
            critical_issues.extend(audit_result.get_issues_by_severity(IssueSeverity.CRITICAL))
        return critical_issues
