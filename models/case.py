"""Case model for safety research requests."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid


class CaseStatus(Enum):
    """Status of a safety research case."""
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"
    CLOSED = "closed"


class CasePriority(Enum):
    """Priority level for case processing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Case:
    """
    Represents a safety research case/question submitted to the system.

    Attributes:
        case_id: Unique identifier for the case
        title: Brief title of the safety question
        description: Detailed description of the safety question
        status: Current status of the case
        priority: Priority level for processing
        submitter: Name/ID of person who submitted the case
        assigned_sme: Subject matter expert assigned to oversee
        question: The core safety question to answer
        context: Additional context and relevant information
        data_sources: List of data sources to consult
        tasks: List of task IDs associated with this case
        findings: Key findings from completed tasks
        final_report: Final synthesized report
        created_at: Timestamp of case submission
        updated_at: Timestamp of last update
        completed_at: Timestamp of completion
        metadata: Additional case metadata
    """
    case_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: CaseStatus = CaseStatus.SUBMITTED
    priority: CasePriority = CasePriority.MEDIUM
    submitter: str = ""
    assigned_sme: Optional[str] = None
    question: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    findings: Dict[str, Any] = field(default_factory=dict)
    final_report: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_status(self, new_status: CaseStatus) -> None:
        """Update case status and timestamp."""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        if new_status == CaseStatus.COMPLETED:
            self.completed_at = datetime.utcnow()

    def add_task(self, task_id: str) -> None:
        """Add a task to the case."""
        self.tasks.append(task_id)
        self.updated_at = datetime.utcnow()

    def add_finding(self, key: str, value: Any) -> None:
        """Add a finding to the case."""
        self.findings[key] = value
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary representation."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "submitter": self.submitter,
            "assigned_sme": self.assigned_sme,
            "question": self.question,
            "context": self.context,
            "data_sources": self.data_sources,
            "tasks": self.tasks,
            "findings": self.findings,
            "final_report": self.final_report,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }
