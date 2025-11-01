"""
Unit tests for Case model.

Tests cover:
- Case creation and initialization
- Status transitions
- Task management
- Findings tracking
- Serialization
"""

import pytest
from datetime import datetime
from models.case import Case, CaseStatus, CasePriority


# Note: Use 'Case' directly instead of importing 'ResearchCase'
# (The conftest.py fixture uses ResearchCase which may not exist)


class TestCase:
    """Test Case model."""

    def test_case_creation(self):
        """Test creating a case."""
        case = Case(
            title="ADC-ILD Investigation",
            description="Investigate ILD mechanisms in ADC treatment",
            question="What causes ILD in ADC patients?"
        )

        assert case.case_id is not None
        assert case.title == "ADC-ILD Investigation"
        assert case.description == "Investigate ILD mechanisms in ADC treatment"
        assert case.question == "What causes ILD in ADC patients?"
        assert case.status == CaseStatus.SUBMITTED
        assert case.priority == CasePriority.MEDIUM

    def test_case_with_priority(self):
        """Test case with different priorities."""
        for priority in [CasePriority.LOW, CasePriority.MEDIUM, CasePriority.HIGH, CasePriority.URGENT]:
            case = Case(
                title="Test Case",
                priority=priority
            )
            assert case.priority == priority

    def test_case_status_update(self):
        """Test updating case status."""
        case = Case(title="Test Case")
        original_time = case.updated_at

        import time
        time.sleep(0.01)

        case.update_status(CaseStatus.IN_PROGRESS)

        assert case.status == CaseStatus.IN_PROGRESS
        assert case.updated_at > original_time

    def test_case_completion(self):
        """Test case completion sets timestamp."""
        case = Case(title="Test Case")

        case.update_status(CaseStatus.COMPLETED)

        assert case.status == CaseStatus.COMPLETED
        assert case.completed_at is not None
        assert case.completed_at >= case.created_at

    def test_add_task_to_case(self):
        """Test adding tasks to a case."""
        case = Case(title="Test Case")

        case.add_task("task-001")
        case.add_task("task-002")
        case.add_task("task-003")

        assert len(case.tasks) == 3
        assert "task-001" in case.tasks
        assert "task-002" in case.tasks
        assert "task-003" in case.tasks

    def test_add_findings(self):
        """Test adding findings to a case."""
        case = Case(title="Test Case")

        case.add_finding("ild_incidence", "15%")
        case.add_finding("mechanism", "Immune-mediated")
        case.add_finding("risk_factors", ["age", "pre-existing lung disease"])

        assert case.findings["ild_incidence"] == "15%"
        assert case.findings["mechanism"] == "Immune-mediated"
        assert "age" in case.findings["risk_factors"]

    def test_case_with_context(self):
        """Test case with context data."""
        case = Case(
            title="ADC Safety Review",
            context={
                "therapeutic_area": "oncology",
                "drug_class": "ADC",
                "specific_products": ["trastuzumab deruxtecan"],
                "adverse_event": "ILD"
            }
        )

        assert case.context["therapeutic_area"] == "oncology"
        assert case.context["drug_class"] == "ADC"
        assert "trastuzumab deruxtecan" in case.context["specific_products"]

    def test_case_with_data_sources(self):
        """Test case with data sources."""
        case = Case(
            title="Safety Review",
            data_sources=["pubmed", "faers", "clinical_trials_gov"]
        )

        assert "pubmed" in case.data_sources
        assert "faers" in case.data_sources
        assert len(case.data_sources) == 3

    def test_case_with_submitter(self):
        """Test case with submitter information."""
        case = Case(
            title="Safety Question",
            submitter="safety_scientist_01"
        )

        assert case.submitter == "safety_scientist_01"

    def test_case_with_sme(self):
        """Test case with assigned SME."""
        case = Case(
            title="Complex Case",
            assigned_sme="sme_oncology_01"
        )

        assert case.assigned_sme == "sme_oncology_01"

    def test_case_final_report(self):
        """Test case with final report."""
        case = Case(title="Test Case")

        final_report = {
            "executive_summary": "Comprehensive findings on ADC-ILD",
            "key_findings": ["Finding 1", "Finding 2"],
            "recommendations": ["Rec 1", "Rec 2"],
            "limitations": ["Limit 1"]
        }

        case.final_report = final_report
        case.update_status(CaseStatus.COMPLETED)

        assert case.final_report is not None
        assert case.final_report["executive_summary"] == "Comprehensive findings on ADC-ILD"

    def test_case_metadata(self):
        """Test case with metadata."""
        case = Case(
            title="Test Case",
            metadata={
                "version": "1.0",
                "tags": ["urgent", "high-priority"],
                "estimated_days": 5
            }
        )

        assert case.metadata["version"] == "1.0"
        assert "urgent" in case.metadata["tags"]

    def test_case_serialization(self):
        """Test case to_dict serialization."""
        case = Case(
            title="ADC Safety",
            description="Safety review",
            question="Is it safe?",
            priority=CasePriority.HIGH,
            submitter="user123"
        )

        case_dict = case.to_dict()

        assert case_dict["case_id"] == case.case_id
        assert case_dict["title"] == "ADC Safety"
        assert case_dict["description"] == "Safety review"
        assert case_dict["status"] == "submitted"
        assert case_dict["priority"] == "high"
        assert "created_at" in case_dict
        assert "updated_at" in case_dict


class TestCaseStatus:
    """Test CaseStatus enum."""

    def test_all_statuses(self):
        """Test all case statuses exist."""
        statuses = [
            CaseStatus.SUBMITTED,
            CaseStatus.ASSIGNED,
            CaseStatus.IN_PROGRESS,
            CaseStatus.COMPLETED,
            CaseStatus.REQUIRES_HUMAN_REVIEW,
            CaseStatus.CLOSED
        ]

        for status in statuses:
            assert isinstance(status, CaseStatus)

    def test_typical_workflow(self):
        """Test typical case workflow."""
        case = Case(title="Workflow Test")

        # SUBMITTED → ASSIGNED → IN_PROGRESS → COMPLETED → CLOSED
        assert case.status == CaseStatus.SUBMITTED

        case.update_status(CaseStatus.ASSIGNED)
        assert case.status == CaseStatus.ASSIGNED

        case.update_status(CaseStatus.IN_PROGRESS)
        assert case.status == CaseStatus.IN_PROGRESS

        case.update_status(CaseStatus.COMPLETED)
        assert case.status == CaseStatus.COMPLETED

        case.update_status(CaseStatus.CLOSED)
        assert case.status == CaseStatus.CLOSED

    def test_human_review_workflow(self):
        """Test workflow requiring human review."""
        case = Case(title="Complex Case")

        case.update_status(CaseStatus.IN_PROGRESS)
        case.update_status(CaseStatus.REQUIRES_HUMAN_REVIEW)

        assert case.status == CaseStatus.REQUIRES_HUMAN_REVIEW


class TestCasePriority:
    """Test CasePriority enum."""

    def test_all_priorities(self):
        """Test all priority levels exist."""
        priorities = [
            CasePriority.LOW,
            CasePriority.MEDIUM,
            CasePriority.HIGH,
            CasePriority.URGENT
        ]

        for priority in priorities:
            assert isinstance(priority, CasePriority)


class TestCaseEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_case(self):
        """Test creating case with minimal data."""
        case = Case()

        assert case.case_id is not None
        assert case.title == ""
        assert case.description == ""
        assert len(case.tasks) == 0

    def test_many_tasks(self):
        """Test case with many tasks."""
        case = Case(title="Large Case")

        for i in range(100):
            case.add_task(f"task-{i:03d}")

        assert len(case.tasks) == 100
        assert "task-050" in case.tasks

    def test_many_findings(self):
        """Test case with many findings."""
        case = Case(title="Comprehensive Case")

        for i in range(50):
            case.add_finding(f"finding_{i}", f"value_{i}")

        assert len(case.findings) == 50
        assert case.findings["finding_25"] == "value_25"

    def test_case_timestamps_ordering(self):
        """Test case timestamps are in correct order."""
        case = Case(title="Timestamp Test")

        import time
        time.sleep(0.01)

        case.update_status(CaseStatus.IN_PROGRESS)

        time.sleep(0.01)

        case.update_status(CaseStatus.COMPLETED)

        assert case.created_at <= case.updated_at
        assert case.updated_at <= case.completed_at

    def test_overwrite_finding(self):
        """Test overwriting an existing finding."""
        case = Case(title="Test Case")

        case.add_finding("result", "initial value")
        assert case.findings["result"] == "initial value"

        case.add_finding("result", "updated value")
        assert case.findings["result"] == "updated value"
