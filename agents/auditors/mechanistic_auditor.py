"""Mechanistic inference auditor agent."""
from typing import Dict, Any, List
import logging

from agents.base_auditor import BaseAuditor


logger = logging.getLogger(__name__)


class MechanisticAuditor(BaseAuditor):
    """
    Auditor agent for validating mechanistic inference outputs.

    This auditor checks:
    - Pathway identification validity
    - Biological plausibility assessment
    - Causality inference logic
    - Evidence strength evaluation
    - Assumption documentation
    - Compliance with CLAUDE.md guidelines
    """

    def __init__(self, agent_id: str = "mech_auditor_01", config: Dict[str, Any] = None):
        """Initialize mechanistic inference auditor."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria for mechanistic inference.

        Returns:
            Dictionary of validation criteria
        """
        return {
            "required_fields": [
                "summary",
                "pathways",
                "biological_plausibility",
                "causality_assessment",
                "evidence_strength",
                "key_findings",
                "confidence",
                "limitations",
                "assumptions",
                "methodology",
            ],
            "min_pathways": 0,  # May be zero if no pathways identified
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
        Validate mechanistic inference output.

        Args:
            task_input: Original input given to worker
            task_output: Output from mechanistic inference worker
            task_metadata: Additional metadata

        Returns:
            Audit result dictionary
        """
        logger.info("MechanisticAuditor: Starting validation")

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

        # Check 3: Pathway analysis
        pathway_issues = self._check_pathway_analysis(result)
        if pathway_issues:
            issues.extend(pathway_issues)
            failed_checks.append("pathway_analysis")
        else:
            passed_checks.append("pathway_analysis")

        # Check 4: Biological plausibility
        plausibility_issues = self._check_biological_plausibility(result)
        if plausibility_issues:
            issues.extend(plausibility_issues)
            failed_checks.append("biological_plausibility")
        else:
            passed_checks.append("biological_plausibility")

        # Check 5: Causality assessment
        causality_issues = self._check_causality_assessment(result)
        if causality_issues:
            issues.extend(causality_issues)
            failed_checks.append("causality_assessment")
        else:
            passed_checks.append("causality_assessment")

        # Check 6: Evidence strength
        evidence_issues = self._check_evidence_strength(result)
        if evidence_issues:
            issues.extend(evidence_issues)
            failed_checks.append("evidence_strength")
        else:
            passed_checks.append("evidence_strength")

        # Check 7: Assumptions
        assumption_issues = self._check_assumptions(result)
        if assumption_issues:
            issues.extend(assumption_issues)
            failed_checks.append("assumptions")
        else:
            passed_checks.append("assumptions")

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
            f"MechanisticAuditor: Validation complete. Status: {status}, "
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

    def _check_pathway_analysis(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check pathway identification and analysis."""
        issues = []

        pathways = result.get("pathways", [])

        # Pathways may be empty (no mechanistic link found) - not an error
        # But we should check structure if pathways are present

        if isinstance(pathways, list) and len(pathways) > 0:
            for i, pathway in enumerate(pathways):
                if not isinstance(pathway, dict):
                    issues.append({
                        "category": "invalid_pathway_structure",
                        "severity": "critical",
                        "description": f"Pathway {i} is not a dictionary",
                        "location": f"result.pathways[{i}]",
                        "suggested_fix": "Each pathway should be a dictionary with pathway details",
                    })
                    continue

                # Check for key pathway fields
                required_pathway_fields = ["pathway_name"]
                missing_fields = [f for f in required_pathway_fields if f not in pathway]

                if missing_fields:
                    issues.append({
                        "category": "incomplete_pathway",
                        "severity": "warning",
                        "description": (
                            f"Pathway {i} missing fields: {missing_fields}"
                        ),
                        "location": f"result.pathways[{i}]",
                        "suggested_fix": "Add pathway name and components",
                    })

                # Check for relevance justification
                if "relevance_reasons" not in pathway and "relevance_score" not in pathway:
                    issues.append({
                        "category": "missing_pathway_justification",
                        "severity": "warning",
                        "description": (
                            f"Pathway {i} lacks relevance justification"
                        ),
                        "location": f"result.pathways[{i}]",
                        "suggested_fix": "Explain why this pathway is relevant to the question",
                    })

        return issues

    def _check_biological_plausibility(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check biological plausibility assessment."""
        issues = []

        plausibility = result.get("biological_plausibility", {})

        if not plausibility:
            issues.append({
                "category": "missing_plausibility",
                "severity": "critical",
                "description": "No biological plausibility assessment provided",
                "location": "result.biological_plausibility",
                "suggested_fix": "Assess biological plausibility of the mechanistic relationship",
                "guideline_reference": "Mechanistic analysis requires plausibility assessment",
            })
            return issues

        # Check for overall assessment
        if "overall_plausibility" not in plausibility:
            issues.append({
                "category": "missing_overall_plausibility",
                "severity": "critical",
                "description": "Missing overall plausibility conclusion",
                "location": "result.biological_plausibility",
                "suggested_fix": "Provide overall plausibility assessment (High/Moderate/Low)",
            })

        # Check for supporting evidence
        if "supporting_evidence" not in plausibility:
            issues.append({
                "category": "missing_supporting_evidence",
                "severity": "warning",
                "description": "No supporting evidence listed for plausibility",
                "location": "result.biological_plausibility",
                "suggested_fix": "List evidence supporting biological plausibility",
            })

        # Check for limiting factors
        if "limiting_factors" not in plausibility:
            issues.append({
                "category": "missing_limiting_factors",
                "severity": "warning",
                "description": "No limiting factors identified for plausibility",
                "location": "result.biological_plausibility",
                "suggested_fix": "Identify factors limiting biological plausibility",
            })

        # Check for unjustified high plausibility
        overall = plausibility.get("overall_plausibility", "").lower()
        if "high" in overall:
            supporting = plausibility.get("supporting_evidence", [])
            if len(supporting) < 2:
                issues.append({
                    "category": "unjustified_high_plausibility",
                    "severity": "warning",
                    "description": (
                        "'High' plausibility stated but limited supporting evidence. "
                        "CLAUDE.md requires conservative assessments."
                    ),
                    "location": "result.biological_plausibility.overall_plausibility",
                    "suggested_fix": "Lower to 'Moderate' or provide more supporting evidence",
                    "guideline_reference": "CLAUDE.md: Conservative assessment required",
                })

        return issues

    def _check_causality_assessment(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check mechanistic causality assessment."""
        issues = []

        causality = result.get("causality_assessment", {})

        if not causality:
            issues.append({
                "category": "missing_causality",
                "severity": "critical",
                "description": "No mechanistic causality assessment provided",
                "location": "result.causality_assessment",
                "suggested_fix": "Assess mechanistic causality using established criteria",
                "guideline_reference": "Mechanistic analysis requires causality evaluation",
            })
            return issues

        # Check for causality level
        if "causality_level" not in causality:
            issues.append({
                "category": "missing_causality_level",
                "severity": "critical",
                "description": "No causality level conclusion provided",
                "location": "result.causality_assessment",
                "suggested_fix": "Provide causality level (Strong/Moderate/Weak/Insufficient)",
            })

        # Check for criteria assessment
        if "criteria_assessments" not in causality:
            issues.append({
                "category": "missing_criteria_assessment",
                "severity": "warning",
                "description": "No detailed criteria assessment provided",
                "location": "result.causality_assessment",
                "suggested_fix": "Assess individual causality criteria (plausibility, specificity, etc.)",
            })

        # Check for interpretation
        if "interpretation" not in causality:
            issues.append({
                "category": "missing_causality_interpretation",
                "severity": "warning",
                "description": "No interpretation of causality assessment",
                "location": "result.causality_assessment",
                "suggested_fix": "Interpret what the causality level means for decision-making",
            })

        # Validate scoring if present
        if "total_score" in causality and "max_score" in causality:
            total = causality["total_score"]
            max_score = causality["max_score"]

            if total > max_score:
                issues.append({
                    "category": "invalid_causality_score",
                    "severity": "critical",
                    "description": f"Total score {total} exceeds maximum {max_score}",
                    "location": "result.causality_assessment",
                    "suggested_fix": "Verify causality scoring calculation",
                })

            # Check for score without justification
            if "criteria_assessments" not in causality:
                issues.append({
                    "category": "score_without_justification",
                    "severity": "warning",
                    "description": "Causality score provided without criteria breakdown",
                    "location": "result.causality_assessment",
                    "suggested_fix": "Document how score was calculated from individual criteria",
                })

        return issues

    def _check_evidence_strength(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check evidence strength assessment."""
        issues = []

        evidence_strength = result.get("evidence_strength", {})

        if not evidence_strength:
            issues.append({
                "category": "missing_evidence_strength",
                "severity": "critical",
                "description": "No evidence strength assessment provided",
                "location": "result.evidence_strength",
                "suggested_fix": "Assess strength of mechanistic evidence base",
            })
            return issues

        # Check for overall strength
        if "overall_strength" not in evidence_strength:
            issues.append({
                "category": "missing_overall_strength",
                "severity": "warning",
                "description": "No overall evidence strength conclusion",
                "location": "result.evidence_strength",
                "suggested_fix": "Provide overall strength assessment",
            })

        # Check for evidence types
        if "evidence_types" not in evidence_strength:
            issues.append({
                "category": "missing_evidence_types",
                "severity": "warning",
                "description": "Evidence types not documented",
                "location": "result.evidence_strength",
                "suggested_fix": "List types of evidence (in vitro, in vivo, human studies)",
            })
        else:
            evidence_types = evidence_strength["evidence_types"]
            if not evidence_types or len(evidence_types) == 0:
                issues.append({
                    "category": "no_evidence_types",
                    "severity": "warning",
                    "description": "No evidence types identified",
                    "location": "result.evidence_strength.evidence_types",
                    "suggested_fix": "Identify and document available evidence types",
                })

        return issues

    def _check_assumptions(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check mechanistic assumptions documentation."""
        issues = []

        assumptions = result.get("assumptions", [])

        if not assumptions:
            issues.append({
                "category": "missing_assumptions",
                "severity": "critical",
                "description": "No mechanistic assumptions documented",
                "location": "result.assumptions",
                "suggested_fix": (
                    "Document assumptions (e.g., pathway completeness, "
                    "preclinical-to-human translation, target engagement)"
                ),
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
                    "Document additional assumptions about pathway database, "
                    "mechanism translation, and target engagement"
                ),
            })

        # Check for critical mechanistic assumptions
        critical_assumptions = [
            "pathway", "translat", "target", "mechanism"
        ]

        assumption_text = " ".join(assumptions).lower()
        missing_critical = []

        for critical in critical_assumptions:
            if critical not in assumption_text:
                missing_critical.append(critical)

        if len(missing_critical) >= 3:  # Most are missing
            issues.append({
                "category": "missing_critical_assumptions",
                "severity": "info",
                "description": (
                    "Consider documenting assumptions about: "
                    "pathway completeness, mechanism translation, target engagement"
                ),
                "location": "result.assumptions",
                "suggested_fix": "Expand assumption documentation",
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
                f"Mechanistic inference output validation PASSED. "
                f"All {len(passed_checks)} validation checks satisfied. "
                f"Pathway analysis, plausibility, and causality assessments valid."
            )
        elif status == "partial":
            return (
                f"Mechanistic inference output validation PARTIAL. "
                f"{len(passed_checks)} checks passed, {len(issues)} issues found. "
                f"Issues are non-critical but should be addressed."
            )
        else:  # failed
            critical_count = sum(1 for i in issues if i.get("severity") == "critical")
            return (
                f"Mechanistic inference output validation FAILED. "
                f"{critical_count} critical issues found. "
                f"Mechanistic analysis requires revision before acceptance."
            )

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations."""
        if not issues:
            return ["Mechanistic inference output meets all quality standards - ready for use"]

        recommendations = []

        # Group by category
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        warning_issues = [i for i in issues if i.get("severity") == "warning"]

        if critical_issues:
            recommendations.append(
                f"ADDRESS {len(critical_issues)} CRITICAL ISSUES: "
                "Review plausibility, causality, and evidence strength assessments"
            )

        if warning_issues:
            recommendations.append(
                f"Address {len(warning_issues)} warnings to improve quality: "
                "Expand documentation and justification"
            )

        # Specific recommendations
        categories = set(i.get("category") for i in issues)

        if "missing_plausibility" in categories or "missing_overall_plausibility" in categories:
            recommendations.append(
                "Complete biological plausibility assessment with supporting evidence"
            )

        if "missing_causality" in categories or "missing_causality_level" in categories:
            recommendations.append(
                "Perform mechanistic causality assessment using Bradford Hill-like criteria"
            )

        if "missing_evidence_strength" in categories:
            recommendations.append(
                "Assess evidence strength and document evidence types (in vitro, in vivo, human)"
            )

        if "missing_assumptions" in categories or "insufficient_assumptions" in categories:
            recommendations.append(
                "Document all mechanistic assumptions (pathway completeness, translation, target engagement)"
            )

        if "unjustified_high_plausibility" in categories:
            recommendations.append(
                "Revise plausibility assessment to be more conservative per CLAUDE.md guidelines"
            )

        return recommendations
