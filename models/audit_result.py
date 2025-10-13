"""Audit result model for validation outcomes."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid


class AuditStatus(Enum):
    """Status of an audit."""
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some checks passed, some failed
    ESCALATED = "escalated"  # Requires human review


class IssueSeverity(Enum):
    """Severity level of a validation issue."""
    CRITICAL = "critical"  # Must be fixed
    WARNING = "warning"    # Should be fixed
    INFO = "info"          # Nice to have


@dataclass
class ValidationIssue:
    """
    Represents a specific validation issue found during audit.

    Attributes:
        issue_id: Unique identifier for the issue
        category: Category of the issue (e.g., "fabrication", "missing_evidence")
        severity: Severity level of the issue
        description: Detailed description of what's wrong
        location: Where in the output this issue was found
        suggested_fix: Recommended correction
        guideline_reference: Reference to violated guideline
    """
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""
    severity: IssueSeverity = IssueSeverity.WARNING
    description: str = ""
    location: Optional[str] = None
    suggested_fix: Optional[str] = None
    guideline_reference: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "issue_id": self.issue_id,
            "category": self.category,
            "severity": self.severity.value,
            "description": self.description,
            "location": self.location,
            "suggested_fix": self.suggested_fix,
            "guideline_reference": self.guideline_reference,
        }


@dataclass
class AuditResult:
    """
    Results from an audit agent's validation of worker output.

    Attributes:
        audit_id: Unique identifier for this audit
        task_id: ID of the task being audited
        auditor_agent: Name/ID of the auditor agent
        status: Overall audit status
        issues: List of validation issues found
        passed_checks: List of checks that passed
        failed_checks: List of checks that failed
        score: Optional numerical score (avoid fabrication)
        summary: Brief summary of audit findings
        recommendations: List of recommendations for improvement
        created_at: Timestamp of audit completion
        metadata: Additional audit metadata
    """
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    auditor_agent: str = ""
    status: AuditStatus = AuditStatus.PASSED
    issues: List[ValidationIssue] = field(default_factory=list)
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    score: Optional[float] = None
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add a validation issue to the audit."""
        self.issues.append(issue)

    def has_critical_issues(self) -> bool:
        """Check if audit has any critical issues."""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        return [issue for issue in self.issues if issue.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit result to dictionary."""
        return {
            "audit_id": self.audit_id,
            "task_id": self.task_id,
            "auditor_agent": self.auditor_agent,
            "status": self.status.value,
            "issues": [issue.to_dict() for issue in self.issues],
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "score": self.score,
            "summary": self.summary,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
