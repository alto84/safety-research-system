"""
Unit tests for AuditResult and ValidationIssue models.

Tests cover:
- ValidationIssue creation
- AuditResult creation and management
- Issue severity handling
- Issue filtering
- Serialization
"""

import pytest
from models.audit_result import (
    AuditResult, ValidationIssue, AuditStatus, IssueSeverity
)


class TestValidationIssue:
    """Test ValidationIssue model."""

    def test_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            category="fabrication",
            severity=IssueSeverity.CRITICAL,
            description="Detected fabricated source",
            location="sources[0]"
        )

        assert issue.issue_id is not None
        assert issue.category == "fabrication"
        assert issue.severity == IssueSeverity.CRITICAL
        assert issue.description == "Detected fabricated source"
        assert issue.location == "sources[0]"

    def test_issue_with_suggested_fix(self):
        """Test issue with suggested fix."""
        issue = ValidationIssue(
            category="missing_citation",
            severity=IssueSeverity.WARNING,
            description="Numerical claim lacks source",
            suggested_fix="Add source with PMID or URL"
        )

        assert issue.suggested_fix == "Add source with PMID or URL"

    def test_issue_with_guideline_reference(self):
        """Test issue with guideline reference."""
        issue = ValidationIssue(
            category="confidence_mismatch",
            severity=IssueSeverity.WARNING,
            description="High confidence without peer-reviewed sources",
            guideline_reference="CLAUDE.md Section 3.2"
        )

        assert issue.guideline_reference == "CLAUDE.md Section 3.2"

    def test_issue_serialization(self):
        """Test issue to_dict serialization."""
        issue = ValidationIssue(
            category="test_category",
            severity=IssueSeverity.INFO,
            description="Test description",
            location="test_location"
        )

        issue_dict = issue.to_dict()

        assert issue_dict["issue_id"] == issue.issue_id
        assert issue_dict["category"] == "test_category"
        assert issue_dict["severity"] == "info"
        assert issue_dict["description"] == "Test description"

    def test_all_severities(self):
        """Test all severity levels."""
        severities = [
            IssueSeverity.CRITICAL,
            IssueSeverity.WARNING,
            IssueSeverity.INFO
        ]

        for severity in severities:
            issue = ValidationIssue(
                category="test",
                severity=severity,
                description="Test"
            )
            assert issue.severity == severity


class TestAuditResult:
    """Test AuditResult model."""

    def test_audit_creation(self):
        """Test creating an audit result."""
        audit = AuditResult(
            task_id="task-123",
            auditor_agent="literature_auditor",
            status=AuditStatus.PASSED
        )

        assert audit.audit_id is not None
        assert audit.task_id == "task-123"
        assert audit.auditor_agent == "literature_auditor"
        assert audit.status == AuditStatus.PASSED
        assert len(audit.issues) == 0

    def test_audit_with_issues(self):
        """Test audit with validation issues."""
        issue1 = ValidationIssue(
            category="fabrication",
            severity=IssueSeverity.CRITICAL,
            description="Fake PMID detected"
        )

        issue2 = ValidationIssue(
            category="missing_citation",
            severity=IssueSeverity.WARNING,
            description="Source lacks URL"
        )

        audit = AuditResult(
            task_id="task-456",
            auditor_agent="test_auditor",
            status=AuditStatus.FAILED,
            issues=[issue1, issue2]
        )

        assert len(audit.issues) == 2
        assert audit.issues[0].severity == IssueSeverity.CRITICAL
        assert audit.issues[1].severity == IssueSeverity.WARNING

    def test_add_issue(self):
        """Test adding issues to audit."""
        audit = AuditResult(
            task_id="task-789",
            auditor_agent="test_auditor"
        )

        issue = ValidationIssue(
            category="test",
            severity=IssueSeverity.INFO,
            description="Test issue"
        )

        audit.add_issue(issue)

        assert len(audit.issues) == 1
        assert audit.issues[0] == issue

    def test_has_critical_issues(self):
        """Test checking for critical issues."""
        audit = AuditResult()

        # No critical issues initially
        assert audit.has_critical_issues() is False

        # Add warning issue
        audit.add_issue(ValidationIssue(
            category="test",
            severity=IssueSeverity.WARNING,
            description="Warning"
        ))
        assert audit.has_critical_issues() is False

        # Add critical issue
        audit.add_issue(ValidationIssue(
            category="test",
            severity=IssueSeverity.CRITICAL,
            description="Critical"
        ))
        assert audit.has_critical_issues() is True

    def test_get_issues_by_severity(self):
        """Test filtering issues by severity."""
        audit = AuditResult()

        # Add mixed severity issues
        audit.add_issue(ValidationIssue(
            category="test1",
            severity=IssueSeverity.CRITICAL,
            description="Critical 1"
        ))
        audit.add_issue(ValidationIssue(
            category="test2",
            severity=IssueSeverity.WARNING,
            description="Warning 1"
        ))
        audit.add_issue(ValidationIssue(
            category="test3",
            severity=IssueSeverity.CRITICAL,
            description="Critical 2"
        ))
        audit.add_issue(ValidationIssue(
            category="test4",
            severity=IssueSeverity.INFO,
            description="Info 1"
        ))

        critical_issues = audit.get_issues_by_severity(IssueSeverity.CRITICAL)
        warning_issues = audit.get_issues_by_severity(IssueSeverity.WARNING)
        info_issues = audit.get_issues_by_severity(IssueSeverity.INFO)

        assert len(critical_issues) == 2
        assert len(warning_issues) == 1
        assert len(info_issues) == 1

    def test_audit_with_passed_checks(self):
        """Test audit with passed checks."""
        audit = AuditResult(
            passed_checks=[
                "source_validation",
                "confidence_calibration",
                "provenance_tracking"
            ]
        )

        assert len(audit.passed_checks) == 3
        assert "source_validation" in audit.passed_checks

    def test_audit_with_failed_checks(self):
        """Test audit with failed checks."""
        audit = AuditResult(
            status=AuditStatus.FAILED,
            failed_checks=[
                "fabrication_detection",
                "numerical_validation"
            ]
        )

        assert len(audit.failed_checks) == 2
        assert "fabrication_detection" in audit.failed_checks

    def test_audit_with_recommendations(self):
        """Test audit with recommendations."""
        audit = AuditResult(
            recommendations=[
                "Add peer-reviewed sources",
                "Lower confidence level",
                "Include limitations section"
            ]
        )

        assert len(audit.recommendations) == 3
        assert "Add peer-reviewed sources" in audit.recommendations

    def test_audit_with_score(self):
        """Test audit with numerical score."""
        audit = AuditResult(
            status=AuditStatus.PASSED,
            score=85.5
        )

        assert audit.score == 85.5

    def test_audit_summary(self):
        """Test audit with summary."""
        audit = AuditResult(
            status=AuditStatus.PASSED,
            summary="All validation checks passed successfully"
        )

        assert audit.summary == "All validation checks passed successfully"

    def test_audit_metadata(self):
        """Test audit with metadata."""
        audit = AuditResult(
            metadata={
                "audit_duration_ms": 1500,
                "checks_performed": 15,
                "version": "1.0"
            }
        )

        assert audit.metadata["audit_duration_ms"] == 1500
        assert audit.metadata["checks_performed"] == 15

    def test_audit_serialization(self):
        """Test audit to_dict serialization."""
        issue = ValidationIssue(
            category="test",
            severity=IssueSeverity.WARNING,
            description="Test issue"
        )

        audit = AuditResult(
            task_id="task-999",
            auditor_agent="test_auditor",
            status=AuditStatus.PARTIAL,
            issues=[issue],
            passed_checks=["check1", "check2"],
            failed_checks=["check3"],
            score=75.0,
            summary="Partial pass",
            recommendations=["Fix check3"]
        )

        audit_dict = audit.to_dict()

        assert audit_dict["audit_id"] == audit.audit_id
        assert audit_dict["task_id"] == "task-999"
        assert audit_dict["status"] == "partial"
        assert len(audit_dict["issues"]) == 1
        assert audit_dict["score"] == 75.0
        assert "created_at" in audit_dict


class TestAuditStatus:
    """Test AuditStatus enum."""

    def test_all_statuses(self):
        """Test all audit statuses exist."""
        statuses = [
            AuditStatus.PASSED,
            AuditStatus.FAILED,
            AuditStatus.PARTIAL,
            AuditStatus.ESCALATED
        ]

        for status in statuses:
            assert isinstance(status, AuditStatus)

    def test_passed_audit(self):
        """Test passed audit."""
        audit = AuditResult(status=AuditStatus.PASSED)
        assert audit.status == AuditStatus.PASSED
        assert not audit.has_critical_issues()

    def test_failed_audit(self):
        """Test failed audit."""
        audit = AuditResult(
            status=AuditStatus.FAILED,
            issues=[ValidationIssue(
                category="test",
                severity=IssueSeverity.CRITICAL,
                description="Critical failure"
            )]
        )
        assert audit.status == AuditStatus.FAILED
        assert audit.has_critical_issues()

    def test_partial_audit(self):
        """Test partial audit."""
        audit = AuditResult(
            status=AuditStatus.PARTIAL,
            passed_checks=["check1", "check2"],
            failed_checks=["check3"]
        )
        assert audit.status == AuditStatus.PARTIAL
        assert len(audit.passed_checks) > 0
        assert len(audit.failed_checks) > 0

    def test_escalated_audit(self):
        """Test escalated audit."""
        audit = AuditResult(
            status=AuditStatus.ESCALATED,
            summary="Requires human expert review"
        )
        assert audit.status == AuditStatus.ESCALATED


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_audit(self):
        """Test creating empty audit."""
        audit = AuditResult()

        assert audit.audit_id is not None
        assert audit.status == AuditStatus.PASSED
        assert len(audit.issues) == 0
        assert len(audit.passed_checks) == 0
        assert len(audit.failed_checks) == 0

    def test_many_issues(self):
        """Test audit with many issues."""
        audit = AuditResult()

        for i in range(100):
            audit.add_issue(ValidationIssue(
                category=f"category_{i % 10}",
                severity=IssueSeverity.WARNING,
                description=f"Issue {i}"
            ))

        assert len(audit.issues) == 100

    def test_mixed_severity_issues(self):
        """Test audit with mixed severity issues."""
        audit = AuditResult()

        # Add 10 critical, 20 warning, 30 info
        for i in range(60):
            if i < 10:
                severity = IssueSeverity.CRITICAL
            elif i < 30:
                severity = IssueSeverity.WARNING
            else:
                severity = IssueSeverity.INFO

            audit.add_issue(ValidationIssue(
                category="test",
                severity=severity,
                description=f"Issue {i}"
            ))

        assert len(audit.get_issues_by_severity(IssueSeverity.CRITICAL)) == 10
        assert len(audit.get_issues_by_severity(IssueSeverity.WARNING)) == 20
        assert len(audit.get_issues_by_severity(IssueSeverity.INFO)) == 30

    def test_none_score(self):
        """Test audit with None score."""
        audit = AuditResult(score=None)
        assert audit.score is None

    def test_audit_timestamp(self):
        """Test audit has valid timestamp."""
        audit = AuditResult()
        assert audit.created_at is not None

        from datetime import datetime
        assert isinstance(audit.created_at, datetime)
