"""Repository pattern implementations for data access."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from .models import CaseDB, TaskDB, AuditResultDB, EvidenceDB, UserDB
from models.case import Case, CaseStatus, CasePriority
from models.task import Task, TaskStatus, TaskType
from models.audit_result import AuditResult, AuditStatus

logger = logging.getLogger(__name__)


class CaseRepository:
    """Repository for Case database operations."""

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, case: Case) -> CaseDB:
        """
        Create a new case in database.

        Args:
            case: Case dataclass instance

        Returns:
            Created CaseDB instance
        """
        case_db = CaseDB(
            case_id=case.case_id,
            title=case.title,
            description=case.description,
            question=case.question,
            status=case.status,
            priority=case.priority,
            submitter=case.submitter,
            assigned_sme=case.assigned_sme,
            context=case.context,
            data_sources=case.data_sources,
            findings=case.findings,
            final_report=case.final_report,
            metadata=case.metadata,
            created_at=case.created_at,
            updated_at=case.updated_at,
            completed_at=case.completed_at,
        )

        self.session.add(case_db)
        self.session.flush()
        logger.info(f"Created case: {case.case_id}")

        return case_db

    def get_by_id(self, case_id: str) -> Optional[CaseDB]:
        """
        Get case by case_id.

        Args:
            case_id: Case identifier

        Returns:
            CaseDB instance or None
        """
        return self.session.query(CaseDB).filter(CaseDB.case_id == case_id).first()

    def get_by_uuid(self, uuid: UUID) -> Optional[CaseDB]:
        """
        Get case by UUID.

        Args:
            uuid: Database UUID

        Returns:
            CaseDB instance or None
        """
        return self.session.query(CaseDB).filter(CaseDB.id == uuid).first()

    def get_all(
        self,
        status: Optional[CaseStatus] = None,
        priority: Optional[CasePriority] = None,
        submitter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CaseDB]:
        """
        Get all cases with optional filters.

        Args:
            status: Filter by status
            priority: Filter by priority
            submitter: Filter by submitter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of CaseDB instances
        """
        query = self.session.query(CaseDB)

        if status:
            query = query.filter(CaseDB.status == status)
        if priority:
            query = query.filter(CaseDB.priority == priority)
        if submitter:
            query = query.filter(CaseDB.submitter == submitter)

        return query.order_by(CaseDB.created_at.desc()).limit(limit).offset(offset).all()

    def update(self, case_id: str, updates: Dict[str, Any]) -> Optional[CaseDB]:
        """
        Update case fields.

        Args:
            case_id: Case identifier
            updates: Dictionary of field updates

        Returns:
            Updated CaseDB instance or None
        """
        case_db = self.get_by_id(case_id)
        if not case_db:
            return None

        for key, value in updates.items():
            if hasattr(case_db, key):
                setattr(case_db, key, value)

        case_db.updated_at = datetime.utcnow()
        self.session.flush()
        logger.info(f"Updated case: {case_id}")

        return case_db

    def delete(self, case_id: str) -> bool:
        """
        Delete case by ID.

        Args:
            case_id: Case identifier

        Returns:
            True if deleted, False if not found
        """
        case_db = self.get_by_id(case_id)
        if not case_db:
            return False

        self.session.delete(case_db)
        self.session.flush()
        logger.info(f"Deleted case: {case_id}")

        return True


class TaskRepository:
    """Repository for Task database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, task: Task, case_uuid: UUID) -> TaskDB:
        """
        Create a new task in database.

        Args:
            task: Task dataclass instance
            case_uuid: UUID of parent case

        Returns:
            Created TaskDB instance
        """
        task_db = TaskDB(
            task_id=task.task_id,
            case_id=case_uuid,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            status=task.status,
            assigned_agent=task.assigned_agent,
            priority=task.priority,
            retry_count=task.retry_count,
            max_retries=task.max_retries,
            input_data=task.input_data,
            output=task.output,
            error_message=task.error_message,
            metadata=task.metadata,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
        )

        self.session.add(task_db)
        self.session.flush()
        logger.info(f"Created task: {task.task_id}")

        return task_db

    def get_by_id(self, task_id: str) -> Optional[TaskDB]:
        """Get task by task_id."""
        return self.session.query(TaskDB).filter(TaskDB.task_id == task_id).first()

    def get_by_case(self, case_id: str) -> List[TaskDB]:
        """Get all tasks for a case."""
        return (
            self.session.query(TaskDB)
            .join(CaseDB)
            .filter(CaseDB.case_id == case_id)
            .order_by(TaskDB.created_at.asc())
            .all()
        )

    def get_by_status(
        self,
        status: TaskStatus,
        task_type: Optional[TaskType] = None,
        limit: int = 100,
    ) -> List[TaskDB]:
        """
        Get tasks by status and optional type.

        Args:
            status: Task status to filter by
            task_type: Optional task type filter
            limit: Maximum number of results

        Returns:
            List of TaskDB instances
        """
        query = self.session.query(TaskDB).filter(TaskDB.status == status)

        if task_type:
            query = query.filter(TaskDB.task_type == task_type)

        return query.order_by(TaskDB.priority.desc(), TaskDB.created_at.asc()).limit(limit).all()

    def update(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskDB]:
        """Update task fields."""
        task_db = self.get_by_id(task_id)
        if not task_db:
            return None

        for key, value in updates.items():
            if hasattr(task_db, key):
                setattr(task_db, key, value)

        task_db.updated_at = datetime.utcnow()
        self.session.flush()
        logger.info(f"Updated task: {task_id}")

        return task_db


class AuditResultRepository:
    """Repository for AuditResult database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(self, audit_result: AuditResult, task_uuid: UUID) -> AuditResultDB:
        """
        Create a new audit result in database.

        Args:
            audit_result: AuditResult dataclass instance
            task_uuid: UUID of parent task

        Returns:
            Created AuditResultDB instance
        """
        audit_db = AuditResultDB(
            audit_id=audit_result.audit_id,
            task_id=task_uuid,
            status=audit_result.status,
            auditor_type=audit_result.auditor_type,
            score=audit_result.score,
            confidence_level=audit_result.confidence_level,
            issues=[issue.__dict__ if hasattr(issue, '__dict__') else issue for issue in audit_result.issues],
            critical_issues_count=audit_result.critical_issues_count,
            warning_issues_count=audit_result.warning_issues_count,
            suggestions=audit_result.suggestions,
            summary=audit_result.summary,
            recommendations=audit_result.recommendations,
            metadata=audit_result.metadata,
            created_at=audit_result.created_at,
            updated_at=audit_result.updated_at,
        )

        self.session.add(audit_db)
        self.session.flush()
        logger.info(f"Created audit result: {audit_result.audit_id}")

        return audit_db

    def get_by_id(self, audit_id: str) -> Optional[AuditResultDB]:
        """Get audit result by audit_id."""
        return self.session.query(AuditResultDB).filter(AuditResultDB.audit_id == audit_id).first()

    def get_by_task(self, task_id: str) -> List[AuditResultDB]:
        """Get all audit results for a task."""
        return (
            self.session.query(AuditResultDB)
            .join(TaskDB)
            .filter(TaskDB.task_id == task_id)
            .order_by(AuditResultDB.created_at.desc())
            .all()
        )


class EvidenceRepository:
    """Repository for Evidence database operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create(
        self,
        evidence_id: str,
        case_id: str,
        source_type: str,
        source_id: str,
        title: str,
        **kwargs
    ) -> EvidenceDB:
        """
        Create a new evidence record.

        Args:
            evidence_id: Unique evidence identifier
            case_id: Associated case ID
            source_type: Type of source (e.g., 'pubmed', 'clinical_trial')
            source_id: Source-specific ID (e.g., PMID)
            title: Evidence title
            **kwargs: Additional fields

        Returns:
            Created EvidenceDB instance
        """
        evidence_db = EvidenceDB(
            evidence_id=evidence_id,
            case_id=case_id,
            source_type=source_type,
            source_id=source_id,
            title=title,
            **kwargs
        )

        self.session.add(evidence_db)
        self.session.flush()
        logger.info(f"Created evidence: {evidence_id}")

        return evidence_db

    def get_by_id(self, evidence_id: str) -> Optional[EvidenceDB]:
        """Get evidence by evidence_id."""
        return self.session.query(EvidenceDB).filter(EvidenceDB.evidence_id == evidence_id).first()

    def get_by_case(self, case_id: str) -> List[EvidenceDB]:
        """Get all evidence for a case."""
        return (
            self.session.query(EvidenceDB)
            .filter(EvidenceDB.case_id == case_id)
            .order_by(EvidenceDB.created_at.desc())
            .all()
        )

    def get_by_pmid(self, pmid: str) -> Optional[EvidenceDB]:
        """Get evidence by PMID."""
        return self.session.query(EvidenceDB).filter(EvidenceDB.pmid == pmid).first()

    def search(
        self,
        case_id: Optional[str] = None,
        source_type: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[EvidenceDB]:
        """
        Search evidence with filters.

        Args:
            case_id: Filter by case
            source_type: Filter by source type
            keywords: Search keywords in title/abstract
            limit: Maximum results

        Returns:
            List of EvidenceDB instances
        """
        query = self.session.query(EvidenceDB)

        if case_id:
            query = query.filter(EvidenceDB.case_id == case_id)
        if source_type:
            query = query.filter(EvidenceDB.source_type == source_type)
        if keywords:
            # Search in title and abstract
            conditions = []
            for keyword in keywords:
                conditions.append(EvidenceDB.title.ilike(f"%{keyword}%"))
                conditions.append(EvidenceDB.abstract.ilike(f"%{keyword}%"))
            query = query.filter(or_(*conditions))

        return query.order_by(EvidenceDB.created_at.desc()).limit(limit).all()
