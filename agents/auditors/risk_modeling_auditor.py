"""Risk modeling auditor agent."""
from typing import Dict, Any, List
import logging

from agents.base_auditor import BaseAuditor


logger = logging.getLogger(__name__)


class RiskModelingAuditor(BaseAuditor):
    """
    Auditor agent for validating risk modeling outputs.

    This auditor checks:
    - Risk calculation accuracy
    - Confidence interval validity
    - Assumption documentation
    - Uncertainty quantification
    - Model appropriateness
    - Compliance with CLAUDE.md guidelines
    """

    def __init__(self, agent_id: str = "risk_auditor_01", config: Dict[str, Any] = None):
        """Initialize risk modeling auditor."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria for risk modeling.

        Returns:
            Dictionary of validation criteria
        """
        return {
            "required_fields": [
                "summary",
                "risk_estimates",
                "confidence_intervals",
                "key_findings",
                "confidence",
                "limitations",
                "assumptions",
                "methodology",
            ],
            "required_risk_fields": ["absolute_risk", "confidence_intervals"],
            "min_assumptions": 3,
            "min_limitations": 2,
        }

    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate risk modeling output.

        Args:
            task_input: Original input given to worker
            task_output: Output from risk modeling worker
            task_metadata: Additional metadata

        Returns:
            Audit result dictionary
        """
        logger.info("RiskModelingAuditor: Starting validation")

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

        # Check 3: Risk calculation validity
        risk_calc_issues = self._check_risk_calculations(result)
        if risk_calc_issues:
            issues.extend(risk_calc_issues)
            failed_checks.append("risk_calculations")
        else:
            passed_checks.append("risk_calculations")

        # Check 4: Confidence intervals
        ci_issues = self._check_confidence_intervals(result)
        if ci_issues:
            issues.extend(ci_issues)
            failed_checks.append("confidence_intervals")
        else:
            passed_checks.append("confidence_intervals")

        # Check 5: Assumptions documentation
        assumption_issues = self._check_assumptions(result)
        if assumption_issues:
            issues.extend(assumption_issues)
            failed_checks.append("assumptions")
        else:
            passed_checks.append("assumptions")

        # Check 6: Uncertainty quantification
        uncertainty_issues = self._check_uncertainty_quantification(result)
        if uncertainty_issues:
            issues.extend(uncertainty_issues)
            failed_checks.append("uncertainty_quantification")
        else:
            passed_checks.append("uncertainty_quantification")

        # Check 7: Sensitivity analysis
        sensitivity_issues = self._check_sensitivity_analysis(result)
        if sensitivity_issues:
            issues.extend(sensitivity_issues)
            failed_checks.append("sensitivity_analysis")
        else:
            passed_checks.append("sensitivity_analysis")

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
            f"RiskModelingAuditor: Validation complete. Status: {status}, "
            f"Issues: {len(issues)}"
        )

        return {
            "status": status,
            "summary": summary,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "issues": issues,
            "recommendations": recommendations,
            "metadata": {
                "auditor_id": self.agent_id,
                "auditor_version": self.version,
                "validation_criteria": self.validation_criteria,
            },
        }

    def _check_risk_calculations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check validity of risk calculations."""
        issues = []

        risk_estimates = result.get("risk_estimates", {})

        if not risk_estimates:
            issues.append({
                "category": "missing_risk_estimates",
                "severity": "critical",
                "description": "No risk estimates provided",
                "location": "result.risk_estimates",
                "suggested_fix": "Include at least absolute risk estimates",
                "guideline_reference": "Risk modeling requires quantitative estimates",
            })
            return issues

        # Check absolute risk
        if "absolute_risk" in risk_estimates:
            abs_risk = risk_estimates["absolute_risk"]

            # Check for valid probability values
            if "value" in abs_risk:
                value = abs_risk["value"]
                if not (0 <= value <= 1):
                    issues.append({
                        "category": "invalid_probability",
                        "severity": "critical",
                        "description": f"Absolute risk value {value} outside valid range [0,1]",
                        "location": "result.risk_estimates.absolute_risk.value",
                        "suggested_fix": "Ensure risk probability is between 0 and 1",
                        "guideline_reference": "Probabilities must be in [0,1]",
                    })

            # Check for interpretation
            if "interpretation" not in abs_risk:
                issues.append({
                    "category": "missing_interpretation",
                    "severity": "warning",
                    "description": "Risk estimate lacks interpretation",
                    "location": "result.risk_estimates.absolute_risk",
                    "suggested_fix": "Add interpretation of risk magnitude",
                })

        # Check for number needed to harm if events > 0
        metadata = result.get("metadata", {})
        if metadata.get("events_analyzed", 0) > 0:
            if "number_needed_to_harm" not in risk_estimates:
                issues.append({
                    "category": "missing_nnh",
                    "severity": "info",
                    "description": "Number Needed to Harm not calculated",
                    "location": "result.risk_estimates",
                    "suggested_fix": "Consider adding NNH for clinical interpretation",
                })

        return issues

    def _check_confidence_intervals(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check confidence interval validity."""
        issues = []

        ci = result.get("confidence_intervals", {})

        if not ci:
            issues.append({
                "category": "missing_confidence_intervals",
                "severity": "critical",
                "description": "No confidence intervals provided for risk estimates",
                "location": "result.confidence_intervals",
                "suggested_fix": "Calculate and report confidence intervals",
                "guideline_reference": "CLAUDE.md requires uncertainty quantification",
            })
            return issues

        # Check for required CI components
        required_ci_fields = ["point_estimate", "lower_bound", "upper_bound"]
        missing_ci_fields = [f for f in required_ci_fields if f not in ci]

        if missing_ci_fields:
            issues.append({
                "category": "incomplete_confidence_intervals",
                "severity": "critical",
                "description": f"Confidence intervals missing fields: {missing_ci_fields}",
                "location": "result.confidence_intervals",
                "suggested_fix": f"Add missing fields: {', '.join(missing_ci_fields)}",
            })

        # Validate CI bounds
        if all(f in ci for f in required_ci_fields):
            point = ci.get("point_estimate", 0)
            lower = ci.get("lower_bound", 0)
            upper = ci.get("upper_bound", 0)

            # Check ordering
            if not (lower <= point <= upper):
                issues.append({
                    "category": "invalid_ci_ordering",
                    "severity": "critical",
                    "description": (
                        f"Confidence interval ordering invalid: "
                        f"lower ({lower}) <= point ({point}) <= upper ({upper})"
                    ),
                    "location": "result.confidence_intervals",
                    "suggested_fix": "Verify CI calculation - bounds should bracket point estimate",
                })

            # Check bounds are valid probabilities
            for bound_name, bound_value in [("lower_bound", lower), ("upper_bound", upper)]:
                if not (0 <= bound_value <= 1):
                    issues.append({
                        "category": "invalid_ci_bounds",
                        "severity": "critical",
                        "description": f"CI {bound_name} {bound_value} outside [0,1]",
                        "location": f"result.confidence_intervals.{bound_name}",
                        "suggested_fix": "Ensure CI bounds are valid probabilities",
                    })

        # Check for method documentation
        if "method" not in ci:
            issues.append({
                "category": "missing_ci_method",
                "severity": "warning",
                "description": "Confidence interval calculation method not documented",
                "location": "result.confidence_intervals",
                "suggested_fix": "Document CI calculation method (e.g., Wilson score, Clopper-Pearson)",
            })

        return issues

    def _check_assumptions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check model assumptions documentation."""
        issues = []

        assumptions = result.get("assumptions", [])

        if not assumptions:
            issues.append({
                "category": "missing_assumptions",
                "severity": "critical",
                "description": "No model assumptions documented",
                "location": "result.assumptions",
                "suggested_fix": "Document key modeling assumptions (e.g., independence, constant risk)",
                "guideline_reference": "CLAUDE.md requires transparent assumption documentation",
            })
            return issues

        # Check minimum number of assumptions
        min_assumptions = self.validation_criteria.get("min_assumptions", 3)
        if len(assumptions) < min_assumptions:
            issues.append({
                "category": "insufficient_assumptions",
                "severity": "warning",
                "description": (
                    f"Only {len(assumptions)} assumptions documented. "
                    f"Expected at least {min_assumptions}"
                ),
                "location": "result.assumptions",
                "suggested_fix": (
                    "Document additional key assumptions (e.g., missing data, "
                    "exposure duration, competing risks)"
                ),
            })

        # Check for critical assumptions
        critical_assumptions = [
            "independent", "constant", "random", "competing"
        ]

        assumption_text = " ".join(assumptions).lower()
        missing_critical = []

        for critical in critical_assumptions:
            if critical not in assumption_text:
                missing_critical.append(critical)

        if missing_critical:
            issues.append({
                "category": "missing_critical_assumptions",
                "severity": "info",
                "description": (
                    f"Consider documenting assumptions related to: "
                    f"{', '.join(missing_critical)}"
                ),
                "location": "result.assumptions",
                "suggested_fix": "Expand assumption documentation",
            })

        return issues

    def _check_uncertainty_quantification(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check uncertainty quantification."""
        issues = []

        # Check for confidence field
        confidence = result.get("confidence", "")

        if not confidence:
            issues.append({
                "category": "missing_confidence",
                "severity": "critical",
                "description": "No confidence level stated for risk estimates",
                "location": "result.confidence",
                "suggested_fix": "Provide confidence assessment (e.g., 'Moderate - adequate sample size')",
                "guideline_reference": "CLAUDE.md requires explicit uncertainty expression",
            })

        # Check confidence is appropriately conservative
        if confidence and "high" in confidence.lower():
            # High confidence requires strong justification
            metadata = result.get("metadata", {})
            population = metadata.get("population_size", 0)

            if population < 1000:
                issues.append({
                    "category": "overconfident_assessment",
                    "severity": "warning",
                    "description": (
                        f"'High' confidence stated but sample size only {population}. "
                        "CLAUDE.md requires conservative confidence assessments."
                    ),
                    "location": "result.confidence",
                    "suggested_fix": "Consider 'Moderate' confidence for sample size < 1000",
                    "guideline_reference": "CLAUDE.md: Conservative uncertainty expression",
                })

        # Check for limitations
        limitations = result.get("limitations", [])
        min_limitations = self.validation_criteria.get("min_limitations", 2)

        if len(limitations) < min_limitations:
            issues.append({
                "category": "insufficient_limitations",
                "severity": "warning",
                "description": (
                    f"Only {len(limitations)} limitations documented. "
                    f"Expected at least {min_limitations}"
                ),
                "location": "result.limitations",
                "suggested_fix": "Document additional limitations (e.g., observational data, missing data)",
            })

        return issues

    def _check_sensitivity_analysis(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check sensitivity analysis."""
        issues = []

        sensitivity = result.get("sensitivity_analysis", {})

        if not sensitivity:
            issues.append({
                "category": "missing_sensitivity_analysis",
                "severity": "warning",
                "description": "No sensitivity analysis performed",
                "location": "result.sensitivity_analysis",
                "suggested_fix": "Perform sensitivity analysis on key assumptions",
            })
            return issues

        # Check for robustness assessment
        if "robustness" not in sensitivity:
            issues.append({
                "category": "missing_robustness_assessment",
                "severity": "info",
                "description": "Sensitivity analysis lacks overall robustness assessment",
                "location": "result.sensitivity_analysis",
                "suggested_fix": "Add robustness assessment (High/Moderate/Low)",
            })

        return issues

    def _generate_summary(
        self,
        status: str,
        issues: List[Dict[str, Any]],
        passed_checks: List[str]
    ) -> str:
        """Generate audit summary."""
        if status == "passed":
            return (
                f"Risk modeling output validation PASSED. "
                f"All {len(passed_checks)} validation checks satisfied. "
                f"Risk calculations valid, uncertainty properly quantified."
            )
        elif status == "partial":
            return (
                f"Risk modeling output validation PARTIAL. "
                f"{len(passed_checks)} checks passed, {len(issues)} issues found. "
                f"Issues are non-critical but should be addressed."
            )
        else:  # failed
            critical_count = sum(1 for i in issues if i.get("severity") == "critical")
            return (
                f"Risk modeling output validation FAILED. "
                f"{critical_count} critical issues found. "
                f"Risk estimates require revision before acceptance."
            )

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        if not issues:
            return ["Risk modeling output meets all quality standards - ready for use"]

        recommendations = []

        # Group by category
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        warning_issues = [i for i in issues if i.get("severity") == "warning"]

        if critical_issues:
            recommendations.append(
                f"ADDRESS {len(critical_issues)} CRITICAL ISSUES: "
                "Review risk calculations, confidence intervals, and assumptions"
            )

        if warning_issues:
            recommendations.append(
                f"Address {len(warning_issues)} warnings to improve quality: "
                "Expand documentation of assumptions and limitations"
            )

        # Specific recommendations
        categories = set(i.get("category") for i in issues)

        if "missing_confidence_intervals" in categories:
            recommendations.append(
                "Add confidence intervals using Wilson score or exact binomial method"
            )

        if "missing_assumptions" in categories or "insufficient_assumptions" in categories:
            recommendations.append(
                "Document all key modeling assumptions (independence, constant risk, missing data)"
            )

        if "missing_sensitivity_analysis" in categories:
            recommendations.append(
                "Perform sensitivity analysis to test robustness of estimates"
            )

        return recommendations
