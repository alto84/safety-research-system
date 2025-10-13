"""Task model for agent work units."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class TaskStatus(Enum):
    """Status of a task in the system."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    AUDITING = "auditing"
    AUDIT_FAILED = "audit_failed"
    REQUIRES_REVISION = "requires_revision"


class TaskType(Enum):
    """Types of tasks that can be assigned to agents."""
    LITERATURE_REVIEW = "literature_review"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    RISK_MODELING = "risk_modeling"
    MECHANISTIC_INFERENCE = "mechanistic_inference"
    DATA_AGGREGATION = "data_aggregation"
    CAUSALITY_ASSESSMENT = "causality_assessment"


@dataclass
class Task:
    """
    Represents a unit of work assigned to an agent.

    Attributes:
        task_id: Unique identifier for the task
        task_type: Type of task from TaskType enum
        status: Current status of the task
        case_id: ID of the parent case this task belongs to
        assigned_agent: Name/ID of the agent assigned to this task
        input_data: Input parameters and data for the task
        output_data: Results produced by the agent
        created_at: Timestamp of task creation
        updated_at: Timestamp of last update
        completed_at: Timestamp of completion
        retry_count: Number of times this task has been retried
        max_retries: Maximum allowed retries
        audit_history: List of audit results for this task
        metadata: Additional task metadata
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType = TaskType.LITERATURE_REVIEW
    status: TaskStatus = TaskStatus.PENDING
    case_id: str = ""
    assigned_agent: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 2
    audit_history: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_status(self, new_status: TaskStatus) -> None:
        """Update task status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status == TaskStatus.COMPLETED:
            self.completed_at = datetime.utcnow()

    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

    def add_audit_result(self, audit_result: 'AuditResult') -> None:
        """Add an audit result to the history."""
        self.audit_history.append(audit_result)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "case_id": self.case_id,
            "assigned_agent": self.assigned_agent,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }
