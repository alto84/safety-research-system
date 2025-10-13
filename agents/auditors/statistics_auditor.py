"""Statistical analysis auditor agent."""
from typing import Dict, Any, List
import logging

from agents.base_auditor import BaseAuditor


logger = logging.getLogger(__name__)


class StatisticsAuditor(BaseAuditor):
    """
    Auditor agent for validating statistical analysis outputs.

    This auditor checks:
    - Methodology appropriateness
    - Assumption verification
    - Statistical rigor
    - Proper uncertainty quantification
    - Compliance with CLAUDE.md guidelines
    """

    def __init__(self, agent_id: str = "stats_auditor_01", config: Dict[str, Any] = None):
        """Initialize statistical analysis auditor."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria for statistical analyses.

        Returns:
            Dictionary of validation criteria
        """
        return {
            "required_fields": [
                "summary",
                "primary_result",
                "interpretation",
                "assumptions",
                "limitations",
                "methodology",
                "confidence",
            ],
            "required_result_fields": ["test", "p_value"],
            "min_assumptions": 2,
        }

    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate statistical analysis output.

        Args:
            task_input: Original input given to worker
            task_output: Output from statistics worker
            task_metadata: Additional metadata

        Returns:
            Audit result dictionary
        """
        logger.info("StatisticsAuditor: Starting validation")

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

        # Check 3: Statistical methodology
        methodology_issues = self._check_methodology(result)
        if methodology_issues:
            issues.extend(methodology_issues)
            failed_checks.append("methodology")
        else:
            passed_checks.append("methodology")

        # Check 4: Assumptions
        assumption_issues = self._check_assumptions(result)
        if assumption_issues:
            issues.extend(assumption_issues)
            failed_checks.append("assumptions")
        else:
            passed_checks.append("assumptions")

        # Check 5: Uncertainty quantification
        uncertainty_issues = self._check_uncertainty(result)
        if uncertainty_issues:
            issues.extend(uncertainty_issues)
            failed_checks.append("uncertainty_quantification")
        else:
            passed_checks.append("uncertainty_quantification")

        # Check 6: Result validity
        result_issues = self._check_results(result)
        if result_issues:
            issues.extend(result_issues)
            failed_checks.append("result_validity")
        else:
            passed_checks.append("result_validity")

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
            f"StatisticsAuditor: Validation complete. Status: {status}, "
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

    def _check_methodology(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check statistical methodology appropriateness."""
        issues = []

        methodology = result.get("methodology", "")

        # Check if methodology is documented
        if not methodology or len(methodology) < 20:
            issues.append({
                "category": "insufficient_methodology",
                "severity": "critical",
                "description": "Statistical methodology is not adequately documented",
                "location": "methodology",
                "suggested_fix": "Provide detailed description of statistical approach",
                "guideline_reference": "CLAUDE.md: MEASUREMENT REQUIREMENT",
            })

        # Check for mention of actual data vs theoretical
        if "actual data" not in methodology.lower() and "measured" not in methodology.lower():
            issues.append({
                "category": "theoretical_only",
                "severity": "warning",
                "description": (
                    "Methodology does not explicitly mention measured data. "
                    "Analysis may be theoretical only."
                ),
                "location": "methodology",
                "suggested_fix": "Clarify whether analysis uses actual measured data or is theoretical",
            })

        return issues

    def _check_assumptions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check statistical assumptions documentation and verification."""
        issues = []

        assumptions = result.get("assumptions", [])

        # Check minimum assumptions documented
        if len(assumptions) < self.validation_criteria["min_assumptions"]:
            issues.append({
                "category": "insufficient_assumptions",
                "severity": "warning",
                "description": (
                    f"Only {len(assumptions)} assumptions documented. "
                    f"Statistical analyses typically have multiple assumptions."
                ),
                "location": "assumptions",
                "suggested_fix": "Document all relevant statistical assumptions",
            })

        # Check if assumptions were verified
        assumptions_met = result.get("assumptions_met", "")
        if not assumptions_met:
            issues.append({
                "category": "unverified_assumptions",
                "severity": "critical",
                "description": "Statistical assumptions were not verified",
                "location": "assumptions_met",
                "suggested_fix": "Verify and document whether assumptions are met",
                "guideline_reference": "Statistical rigor requirements",
            })

        return issues

    def _check_uncertainty(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check uncertainty quantification."""
        issues = []

        primary_result = result.get("primary_result", {})

        # Check for confidence intervals
        if "confidence_interval" not in primary_result:
            issues.append({
                "category": "missing_confidence_interval",
                "severity": "warning",
                "description": "No confidence interval provided for primary result",
                "location": "primary_result",
                "suggested_fix": "Include confidence intervals for effect estimates",
            })

        # Check confidence level expression
        confidence = result.get("confidence", "").lower()
        if not any(word in confidence for word in ["low", "moderate", "high", "uncertain"]):
            issues.append({
                "category": "unclear_confidence",
                "severity": "warning",
                "description": "Confidence level not clearly expressed",
                "location": "confidence",
                "suggested_fix": "Explicitly state confidence level (low/moderate/high)",
                "guideline_reference": "CLAUDE.md: UNCERTAINTY EXPRESSION",
            })

        return issues

    def _check_results(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check statistical results validity."""
        issues = []

        primary_result = result.get("primary_result", {})

        # Check for required result fields
        missing_fields = [
            field for field in self.validation_criteria["required_result_fields"]
            if field not in primary_result
        ]

        if missing_fields:
            issues.append({
                "category": "incomplete_results",
                "severity": "critical",
                "description": f"Primary result missing fields: {', '.join(missing_fields)}",
                "location": "primary_result",
                "suggested_fix": f"Add missing fields: {', '.join(missing_fields)}",
            })

        # Check for measurement data acknowledgment
        p_value = str(primary_result.get("p_value", "")).lower()
        if "cannot determine" in p_value or "no actual data" in p_value or "measurement data" in p_value:
            # This is good - acknowledging lack of data
            pass
        elif isinstance(primary_result.get("p_value"), (int, float)):
            # Numerical p-value without data source is suspicious
            if "data_source" not in result.get("metadata", {}):
                issues.append({
                    "category": "unsupported_result",
                    "severity": "critical",
                    "description": (
                        "Numerical result provided without documented data source. "
                        "This may be fabrication."
                    ),
                    "location": "primary_result.p_value",
                    "suggested_fix": "Either remove numerical result or document data source",
                    "guideline_reference": "CLAUDE.md: MEASUREMENT REQUIREMENT",
                })

        return issues

    def _generate_summary(
        self, status: str, issues: List[Dict[str, Any]], passed_checks: List[str]
    ) -> str:
        """Generate audit summary."""
        if status == "passed":
            return (
                f"Statistical analysis validation passed. "
                f"All {len(passed_checks)} checks completed successfully."
            )
        elif status == "partial":
            return (
                f"Statistical analysis validation partially passed. "
                f"{len(passed_checks)} checks passed, {len(issues)} issues found. "
                f"No critical issues."
            )
        else:  # failed
            critical_count = len([i for i in issues if i.get("severity") == "critical"])
            return (
                f"Statistical analysis validation failed. "
                f"{critical_count} critical issues found requiring immediate attention."
            )

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues found."""
        recommendations = []

        # Group issues by category
        categories = set(issue.get("category") for issue in issues)

        if "unsupported_result" in categories or "score_fabrication" in categories:
            recommendations.append(
                "Ensure all numerical results are supported by actual measurement data"
            )

        if "unverified_assumptions" in categories:
            recommendations.append(
                "Verify and document all statistical assumptions before reporting results"
            )

        if "missing_confidence_interval" in categories:
            recommendations.append(
                "Include confidence intervals for all effect estimates"
            )

        if "theoretical_only" in categories:
            recommendations.append(
                "Clearly distinguish between theoretical framework and empirical analysis"
            )

        return recommendations
