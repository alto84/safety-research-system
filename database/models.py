"""SQLAlchemy database models for persistence layer."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, DateTime, Text, Integer, Float, Boolean,
    JSON, ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base
from models.case import CaseStatus, CasePriority
from models.task import TaskStatus, TaskType
from models.audit_result import AuditStatus


class CaseDB(Base):
    """Database model for safety research cases."""

    __tablename__ = "cases"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Core fields
    case_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    question = Column(Text, nullable=False)

    # Status and priority
    status = Column(
        SQLEnum(CaseStatus),
        nullable=False,
        default=CaseStatus.SUBMITTED,
        index=True
    )
    priority = Column(
        SQLEnum(CasePriority),
        nullable=False,
        default=CasePriority.MEDIUM,
        index=True
    )

    # Assignment
    submitter = Column(String(255), nullable=False, index=True)
    assigned_sme = Column(String(255), nullable=True, index=True)

    # Data
    context = Column(JSON, nullable=False, default=dict)
    data_sources = Column(JSON, nullable=False, default=list)
    findings = Column(JSON, nullable=False, default=dict)
    final_report = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    tasks = relationship("TaskDB", back_populates="case", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_case_status_priority", "status", "priority"),
        Index("idx_case_submitter_status", "submitter", "status"),
        Index("idx_case_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<CaseDB(case_id={self.case_id}, title={self.title[:50]}, status={self.status})>"


class TaskDB(Base):
    """Database model for research tasks."""

    __tablename__ = "tasks"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Core fields
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)

    # Task type and status
    task_type = Column(
        SQLEnum(TaskType),
        nullable=False,
        index=True
    )
    status = Column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True
    )

    # Assignment
    assigned_agent = Column(String(255), nullable=True, index=True)

    # Execution details
    priority = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=2)

    # Data
    input_data = Column(JSON, nullable=False, default=dict)
    output = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    case = relationship("CaseDB", back_populates="tasks")
    audit_results = relationship("AuditResultDB", back_populates="task", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_task_status_type", "status", "task_type"),
        Index("idx_task_case_status", "case_id", "status"),
        Index("idx_task_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<TaskDB(task_id={self.task_id}, type={self.task_type}, status={self.status})>"


class AuditResultDB(Base):
    """Database model for audit results."""

    __tablename__ = "audit_results"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Core fields
    audit_id = Column(String(255), unique=True, nullable=False, index=True)
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Status
    status = Column(
        SQLEnum(AuditStatus),
        nullable=False,
        index=True
    )

    # Audit details
    auditor_type = Column(String(255), nullable=False, index=True)
    score = Column(Float, nullable=True)
    confidence_level = Column(String(100), nullable=True)

    # Findings
    issues = Column(JSON, nullable=False, default=list)
    critical_issues_count = Column(Integer, nullable=False, default=0)
    warning_issues_count = Column(Integer, nullable=False, default=0)
    suggestions = Column(JSON, nullable=False, default=list)

    # Summary
    summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=False, default=list)
    metadata = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("TaskDB", back_populates="audit_results")

    # Indexes
    __table_args__ = (
        Index("idx_audit_status_type", "status", "auditor_type"),
        Index("idx_audit_task_status", "task_id", "status"),
    )

    def __repr__(self):
        return f"<AuditResultDB(audit_id={self.audit_id}, status={self.status}, score={self.score})>"


class EvidenceDB(Base):
    """Database model for evidence sources."""

    __tablename__ = "evidence"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Core fields
    evidence_id = Column(String(255), unique=True, nullable=False, index=True)
    case_id = Column(String(255), nullable=False, index=True)
    task_id = Column(String(255), nullable=True, index=True)

    # Source information
    source_type = Column(String(100), nullable=False, index=True)
    source_id = Column(String(255), nullable=False)  # e.g., PMID, DOI
    title = Column(String(1000), nullable=False)
    authors = Column(JSON, nullable=True)

    # Publication details
    journal = Column(String(500), nullable=True)
    publication_date = Column(String(100), nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    pmid = Column(String(50), nullable=True, index=True)

    # Content
    abstract = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)

    # Evidence classification
    evidence_level = Column(String(100), nullable=True)
    claim_type = Column(String(100), nullable=True)
    confidence_level = Column(String(100), nullable=True)

    # Extracted claims
    claims = Column(JSON, nullable=False, default=list)

    # Metadata
    extraction_method = Column(String(100), nullable=True)
    metadata = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_evidence_case_type", "case_id", "source_type"),
        Index("idx_evidence_pmid", "pmid"),
        Index("idx_evidence_doi", "doi"),
    )

    def __repr__(self):
        return f"<EvidenceDB(evidence_id={self.evidence_id}, source_type={self.source_type}, title={self.title[:50]})>"


class UserDB(Base):
    """Database model for system users (for authentication)."""

    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # User identification
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)

    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)

    # Roles and permissions
    roles = Column(JSON, nullable=False, default=list)
    permissions = Column(JSON, nullable=False, default=list)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UserDB(username={self.username}, email={self.email})>"
