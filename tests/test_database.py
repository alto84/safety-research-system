"""Integration tests for database layer."""
import pytest
from datetime import datetime

from database.base import Base, get_engine, init_db
from database.models import CaseDB, TaskDB, AuditResultDB, EvidenceDB
from database.repositories import CaseRepository, TaskRepository
from models.case import Case, CaseStatus, CasePriority
from models.task import Task, TaskStatus, TaskType
from sqlalchemy.orm import Session


@pytest.fixture
def test_db():
    """Create test database."""
    # Use in-memory SQLite for testing
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    engine = get_engine()
    Base.metadata.create_all(engine)
    
    session = Session(engine)
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)


def test_case_repository_create(test_db):
    """Test case creation in database."""
    repo = CaseRepository(test_db)
    
    case = Case(
        case_id="test-case-1",
        title="Test Case",
        description="Test Description",
        question="Test Question?",
        status=CaseStatus.SUBMITTED,
        priority=CasePriority.MEDIUM,
        submitter="test_user"
    )
    
    case_db = repo.create(case)
    test_db.commit()
    
    assert case_db is not None
    assert case_db.case_id == "test-case-1"
    assert case_db.title == "Test Case"


def test_case_repository_get(test_db):
    """Test case retrieval."""
    repo = CaseRepository(test_db)
    
    case = Case(
        case_id="test-case-2",
        title="Test Case 2",
        description="Description",
        question="Question?",
        submitter="test_user"
    )
    
    repo.create(case)
    test_db.commit()
    
    retrieved = repo.get_by_id("test-case-2")
    assert retrieved is not None
    assert retrieved.case_id == "test-case-2"


def test_task_repository(test_db):
    """Test task repository operations."""
    case_repo = CaseRepository(test_db)
    task_repo = TaskRepository(test_db)
    
    # Create case first
    case = Case(
        case_id="case-for-task",
        title="Case",
        description="Desc",
        question="Q?",
        submitter="user"
    )
    case_db = case_repo.create(case)
    test_db.commit()
    
    # Create task
    task = Task(
        task_id="task-1",
        title="Test Task",
        description="Task Description",
        task_type=TaskType.LITERATURE_SEARCH,
        status=TaskStatus.PENDING
    )
    
    task_db = task_repo.create(task, case_db.id)
    test_db.commit()
    
    assert task_db is not None
    assert task_db.task_id == "task-1"
