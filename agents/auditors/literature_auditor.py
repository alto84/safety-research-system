"""Literature review auditor agent."""
from typing import Dict, Any, List
import logging

from agents.base_auditor import BaseAuditor


logger = logging.getLogger(__name__)


class LiteratureAuditor(BaseAuditor):
    """
    Auditor agent for validating literature review outputs.

    This auditor checks:
    - Source quality and credibility
    - Evidence grading accuracy
    - Citation completeness
    - Proper uncertainty expression
    - Compliance with CLAUDE.md guidelines
    """

    def __init__(self, agent_id: str = "lit_auditor_01", config: Dict[str, Any] = None):
        """Initialize literature review auditor."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria for literature reviews.

        Returns:
            Dictionary of validation criteria
        """
        return {
            "required_fields": [
                "summary",
                "sources",
                "evidence_level",
                "confidence",
                "limitations",
                "methodology",
            ],
            "min_sources": 2,
            "required_source_fields": ["title", "authors", "year"],
            "max_confidence_without_validation": "moderate",
        }

    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate literature review output.

        Args:
            task_input: Original input given to worker
            task_output: Output from literature worker
            task_metadata: Additional metadata

        Returns:
            Audit result dictionary
        """
        logger.info("LiteratureAuditor: Starting validation")

        issues = []
        passed_checks = []
        failed_checks = []

        result = task_output.get("result", {})

        # Check 1: Anti-fabrication compliance (CRITICAL)
        fabrication_issues = self.check_anti_fabrication_compliance(task_output)
        if fabrication_issues:
            issues.extend(fabrication_issues)
            failed_checks.append("anti_fabrication_compliance")
        else:
            passed_checks.append("anti_fabrication_compliance")

        # Check 2: Completeness
        completeness_issues = self.check_completeness(
            task_output,
            self.validation_criteria["required_fields"]
        )
        if completeness_issues:
            issues.extend(completeness_issues)
            failed_checks.append("completeness")
        else:
            passed_checks.append("completeness")

        # Check 3: Source quality
        source_issues = self._check_source_quality(result)
        if source_issues:
            issues.extend(source_issues)
            failed_checks.append("source_quality")
        else:
            passed_checks.append("source_quality")

        # Check 4: Evidence grading
        evidence_issues = self._check_evidence_grading(result)
        if evidence_issues:
            issues.extend(evidence_issues)
            failed_checks.append("evidence_grading")
        else:
            passed_checks.append("evidence_grading")

        # Check 5: Citation completeness
        citation_issues = self._check_citations(result)
        if citation_issues:
            issues.extend(citation_issues)
            failed_checks.append("citation_completeness")
        else:
            passed_checks.append("citation_completeness")

        # Determine overall status
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if critical_issues:
            status = "failed"
        elif issues:
            status = "partial"
        else:
            status = "passed"

        # Generate summary
        summary = self._generate_summary(status, issues, passed_checks)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        logger.info(
            f"LiteratureAuditor: Validation complete. Status: {status}, "
            f"Issues: {len(issues)}"
        )

        return {
            "status": status,
            "summary": summary,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "issues": issues,
            "recommendations": recommendations,
        }

    def _check_source_quality(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check quality and credibility of sources."""
        issues = []
        sources = result.get("sources", [])

        if len(sources) < self.validation_criteria["min_sources"]:
            issues.append({
                "category": "insufficient_sources",
                "severity": "warning",
                "description": (
                    f"Only {len(sources)} sources provided. "
                    f"Minimum {self.validation_criteria['min_sources']} recommended."
                ),
                "location": "sources",
                "suggested_fix": "Include additional high-quality sources",
            })

        # Check each source has required fields
        for i, source in enumerate(sources):
            missing_fields = [
                field for field in self.validation_criteria["required_source_fields"]
                if field not in source
            ]
            if missing_fields:
                issues.append({
                    "category": "incomplete_source",
                    "severity": "warning",
                    "description": (
                        f"Source {i+1} missing fields: {', '.join(missing_fields)}"
                    ),
                    "location": f"sources[{i}]",
                    "suggested_fix": f"Add missing fields: {', '.join(missing_fields)}",
                })

        return issues

    def _check_evidence_grading(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check evidence level grading."""
        issues = []

        evidence_level = result.get("evidence_level", "").lower()
        confidence = result.get("confidence", "").lower()

        # Check for high confidence without strong evidence
        if "high" in confidence and evidence_level not in ["high", "level 1"]:
            issues.append({
                "category": "confidence_evidence_mismatch",
                "severity": "critical",
                "description": (
                    f"High confidence claimed with {evidence_level} evidence level. "
                    "This violates evidence standards."
                ),
                "location": "confidence",
                "suggested_fix": "Lower confidence level or provide stronger evidence",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
            })

        return issues

    def _check_citations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check citation completeness."""
        issues = []

        sources = result.get("sources", [])

        # Check if sources have proper identifiers (PMID, DOI, etc.)
        for i, source in enumerate(sources):
            has_identifier = any(
                key in source for key in ["pmid", "doi", "url", "trial_id"]
            )
            if not has_identifier:
                issues.append({
                    "category": "missing_identifier",
                    "severity": "info",
                    "description": f"Source {i+1} lacks identifier (PMID, DOI, URL)",
                    "location": f"sources[{i}]",
                    "suggested_fix": "Add PMID, DOI, or URL for verification",
                })

        return issues

    def _generate_summary(
        self, status: str, issues: List[Dict[str, Any]], passed_checks: List[str]
    ) -> str:
        """Generate audit summary."""
        if status == "passed":
            return (
                f"Literature review validation passed. "
                f"All {len(passed_checks)} checks completed successfully."
            )
        elif status == "partial":
            return (
                f"Literature review validation partially passed. "
                f"{len(passed_checks)} checks passed, {len(issues)} issues found. "
                f"No critical issues."
            )
        else:  # failed
            critical_count = len([i for i in issues if i.get("severity") == "critical"])
            return (
                f"Literature review validation failed. "
                f"{critical_count} critical issues found requiring immediate attention."
            )

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues found."""
        recommendations = []

        # Group issues by category
        categories = set(issue.get("category") for issue in issues)

        if "score_fabrication" in categories:
            recommendations.append(
                "Remove fabricated scores and rely on evidence-based assessment"
            )

        if "missing_evidence" in categories:
            recommendations.append(
                "Provide clear evidence chain with sources and methodology"
            )

        if "insufficient_sources" in categories:
            recommendations.append(
                "Expand literature search to include more high-quality sources"
            )

        if "confidence_evidence_mismatch" in categories:
            recommendations.append(
                "Align confidence levels with strength of evidence"
            )

        return recommendations
