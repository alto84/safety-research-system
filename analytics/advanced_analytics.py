"""Advanced analytics for confidence calibration, audit metrics, trend analysis, and comparison."""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import json


logger = logging.getLogger(__name__)


class ConfidenceCalibrator:
    """
    Analyzes confidence calibration to detect overconfidence or underconfidence.

    Compares stated confidence levels against actual audit outcomes to
    identify systematic biases in confidence assessment.
    """

    def __init__(self):
        """Initialize confidence calibrator."""
        self.calibration_data: List[Dict[str, Any]] = []

    def add_assessment(
        self,
        stated_confidence: str,
        audit_passed: bool,
        critical_issues: int,
        warning_issues: int,
        agent_type: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add a confidence assessment for calibration analysis.

        Args:
            stated_confidence: Confidence level stated by agent (e.g., "High", "Moderate", "Low")
            audit_passed: Whether audit validation passed
            critical_issues: Number of critical issues found
            warning_issues: Number of warning issues found
            agent_type: Type of agent that made the assessment
            metadata: Additional metadata
        """
        self.calibration_data.append({
            "stated_confidence": stated_confidence,
            "audit_passed": audit_passed,
            "critical_issues": critical_issues,
            "warning_issues": warning_issues,
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def analyze_calibration(self) -> Dict[str, Any]:
        """
        Analyze confidence calibration.

        Returns:
            Dictionary with calibration analysis results
        """
        if not self.calibration_data:
            return {
                "status": "insufficient_data",
                "message": "No calibration data available",
                "recommendations": ["Collect more assessments for calibration analysis"],
            }

        # Group by stated confidence level
        by_confidence = defaultdict(list)
        for item in self.calibration_data:
            confidence = item["stated_confidence"].lower()
            by_confidence[confidence].append(item)

        # Analyze each confidence level
        calibration_results = {}

        for confidence, items in by_confidence.items():
            passed_count = sum(1 for item in items if item["audit_passed"])
            total_count = len(items)
            pass_rate = passed_count / total_count if total_count > 0 else 0

            avg_critical = statistics.mean(item["critical_issues"] for item in items)
            avg_warning = statistics.mean(item["warning_issues"] for item in items)

            # Expected pass rates by confidence level
            expected_pass_rates = {
                "high": 0.95,
                "moderate": 0.80,
                "low": 0.60,
            }

            expected = expected_pass_rates.get(confidence, 0.75)
            calibration_error = pass_rate - expected

            # Assess calibration
            if abs(calibration_error) <= 0.10:
                calibration_status = "well_calibrated"
            elif calibration_error > 0.10:
                calibration_status = "underconfident"
            elif calibration_error < -0.10:
                calibration_status = "overconfident"
            else:
                calibration_status = "moderate_miscalibration"

            calibration_results[confidence] = {
                "total_assessments": total_count,
                "pass_rate": pass_rate,
                "expected_pass_rate": expected,
                "calibration_error": calibration_error,
                "calibration_status": calibration_status,
                "avg_critical_issues": avg_critical,
                "avg_warning_issues": avg_warning,
            }

        # Overall calibration assessment
        overall_status = self._assess_overall_calibration(calibration_results)

        return {
            "status": "analyzed",
            "total_assessments": len(self.calibration_data),
            "calibration_by_level": calibration_results,
            "overall_calibration": overall_status,
            "recommendations": self._generate_calibration_recommendations(
                calibration_results, overall_status
            ),
        }

    def _assess_overall_calibration(
        self, calibration_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess overall system calibration."""
        errors = [
            result["calibration_error"]
            for result in calibration_results.values()
        ]

        if not errors:
            return {"status": "unknown", "mean_error": 0}

        mean_error = statistics.mean(errors)
        mean_abs_error = statistics.mean(abs(e) for e in errors)

        if mean_abs_error <= 0.10:
            status = "well_calibrated"
        elif mean_error > 0.15:
            status = "systematically_underconfident"
        elif mean_error < -0.15:
            status = "systematically_overconfident"
        else:
            status = "moderate_miscalibration"

        return {
            "status": status,
            "mean_error": mean_error,
            "mean_absolute_error": mean_abs_error,
        }

    def _generate_calibration_recommendations(
        self,
        calibration_results: Dict[str, Dict[str, Any]],
        overall_status: Dict[str, Any]
    ) -> List[str]:
        """Generate calibration recommendations."""
        recommendations = []

        overall = overall_status["status"]

        if overall == "systematically_overconfident":
            recommendations.append(
                "CRITICAL: System is systematically overconfident. "
                "Review confidence assessment criteria and enforce more conservative standards."
            )

        elif overall == "systematically_underconfident":
            recommendations.append(
                "System is systematically underconfident. "
                "Consider allowing higher confidence when well-justified."
            )

        # Specific recommendations by confidence level
        for level, results in calibration_results.items():
            if results["calibration_status"] == "overconfident":
                recommendations.append(
                    f"{level.capitalize()} confidence assessments are overconfident "
                    f"(pass rate {results['pass_rate']:.1%} vs expected {results['expected_pass_rate']:.1%}). "
                    f"Tighten quality criteria for this confidence level."
                )

        if not recommendations:
            recommendations.append("Confidence calibration is acceptable. Continue monitoring.")

        return recommendations


class AuditMetricsDashboard:
    """
    Generates dashboard data for audit metrics and system performance.
    """

    def __init__(self):
        """Initialize audit metrics dashboard."""
        self.audit_history: List[Dict[str, Any]] = []

    def add_audit_result(
        self,
        task_type: str,
        audit_status: str,
        issues: List[Dict[str, Any]],
        passed_checks: List[str],
        failed_checks: List[str],
        duration: float = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add audit result for dashboard tracking.

        Args:
            task_type: Type of task audited
            audit_status: Audit status (passed/failed/partial)
            issues: List of issues found
            passed_checks: List of passed checks
            failed_checks: List of failed checks
            duration: Audit duration in seconds
            metadata: Additional metadata
        """
        self.audit_history.append({
            "task_type": task_type,
            "audit_status": audit_status,
            "issues": issues,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """
        Generate comprehensive dashboard data.

        Returns:
            Dashboard data dictionary
        """
        if not self.audit_history:
            return {
                "status": "no_data",
                "message": "No audit data available for dashboard",
            }

        # Overall metrics
        total_audits = len(self.audit_history)
        passed_audits = sum(1 for a in self.audit_history if a["audit_status"] == "passed")
        failed_audits = sum(1 for a in self.audit_history if a["audit_status"] == "failed")
        partial_audits = sum(1 for a in self.audit_history if a["audit_status"] == "partial")

        # Issue metrics
        total_issues = sum(len(a["issues"]) for a in self.audit_history)
        critical_issues = sum(
            sum(1 for issue in a["issues"] if issue.get("severity") == "critical")
            for a in self.audit_history
        )
        warning_issues = sum(
            sum(1 for issue in a["issues"] if issue.get("severity") == "warning")
            for a in self.audit_history
        )

        # By task type
        by_task_type = self._aggregate_by_task_type()

        # By issue category
        by_issue_category = self._aggregate_by_issue_category()

        # Top failing checks
        top_failing_checks = self._get_top_failing_checks()

        # Performance metrics
        durations = [a["duration"] for a in self.audit_history if a["duration"] is not None]
        avg_duration = statistics.mean(durations) if durations else None

        return {
            "status": "generated",
            "generated_at": datetime.utcnow().isoformat(),
            "overall_metrics": {
                "total_audits": total_audits,
                "passed_audits": passed_audits,
                "failed_audits": failed_audits,
                "partial_audits": partial_audits,
                "pass_rate": passed_audits / total_audits if total_audits > 0 else 0,
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "warning_issues": warning_issues,
                "avg_duration_seconds": avg_duration,
            },
            "by_task_type": by_task_type,
            "by_issue_category": by_issue_category,
            "top_failing_checks": top_failing_checks,
            "recommendations": self._generate_dashboard_recommendations(
                passed_audits, failed_audits, total_audits, critical_issues
            ),
        }

    def _aggregate_by_task_type(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate metrics by task type."""
        by_type = defaultdict(lambda: {
            "count": 0,
            "passed": 0,
            "failed": 0,
            "partial": 0,
            "total_issues": 0,
            "critical_issues": 0,
        })

        for audit in self.audit_history:
            task_type = audit["task_type"]
            by_type[task_type]["count"] += 1
            by_type[task_type][audit["audit_status"]] += 1
            by_type[task_type]["total_issues"] += len(audit["issues"])
            by_type[task_type]["critical_issues"] += sum(
                1 for issue in audit["issues"] if issue.get("severity") == "critical"
            )

        return dict(by_type)

    def _aggregate_by_issue_category(self) -> Dict[str, int]:
        """Aggregate issues by category."""
        categories = defaultdict(int)

        for audit in self.audit_history:
            for issue in audit["issues"]:
                category = issue.get("category", "unknown")
                categories[category] += 1

        # Sort by frequency
        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    def _get_top_failing_checks(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top failing checks."""
        failed_check_counts = defaultdict(int)

        for audit in self.audit_history:
            for check in audit["failed_checks"]:
                failed_check_counts[check] += 1

        # Sort by frequency
        top_checks = sorted(
            failed_check_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {"check_name": check, "failure_count": count}
            for check, count in top_checks
        ]

    def _generate_dashboard_recommendations(
        self,
        passed: int,
        failed: int,
        total: int,
        critical: int
    ) -> List[str]:
        """Generate dashboard recommendations."""
        recommendations = []

        pass_rate = passed / total if total > 0 else 0

        if pass_rate < 0.70:
            recommendations.append(
                f"ALERT: Low pass rate ({pass_rate:.1%}). "
                "Review quality standards or provide additional agent training."
            )

        if critical > 0:
            recommendations.append(
                f"CRITICAL: {critical} critical issues detected. "
                "Immediate attention required."
            )

        if failed / total > 0.30 if total > 0 else False:
            recommendations.append(
                "High failure rate detected. "
                "Consider revising task decomposition or agent capabilities."
            )

        if not recommendations:
            recommendations.append(
                f"System performing well (pass rate: {pass_rate:.1%}). Continue monitoring."
            )

        return recommendations


class TrendAnalyzer:
    """
    Analyzes trends in repeated safety assessments over time.
    """

    def __init__(self):
        """Initialize trend analyzer."""
        self.assessment_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add_assessment(
        self,
        entity_id: str,
        assessment_date: datetime,
        risk_estimate: Optional[float] = None,
        confidence_level: Optional[str] = None,
        key_findings: Optional[List[str]] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add assessment for trend analysis.

        Args:
            entity_id: Unique identifier for entity being assessed (e.g., drug-AE pair)
            assessment_date: Date of assessment
            risk_estimate: Quantitative risk estimate if available
            confidence_level: Confidence level
            key_findings: Key findings
            metadata: Additional metadata
        """
        self.assessment_history[entity_id].append({
            "assessment_date": assessment_date,
            "risk_estimate": risk_estimate,
            "confidence_level": confidence_level,
            "key_findings": key_findings or [],
            "metadata": metadata or {},
        })

        # Keep sorted by date
        self.assessment_history[entity_id].sort(key=lambda x: x["assessment_date"])

    def analyze_trends(self, entity_id: str) -> Dict[str, Any]:
        """
        Analyze trends for a specific entity.

        Args:
            entity_id: Entity identifier

        Returns:
            Trend analysis results
        """
        if entity_id not in self.assessment_history:
            return {
                "status": "not_found",
                "message": f"No assessment history for entity: {entity_id}",
            }

        assessments = self.assessment_history[entity_id]

        if len(assessments) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 assessments for trend analysis",
                "assessment_count": len(assessments),
            }

        # Analyze risk estimate trends
        risk_trend = self._analyze_risk_trend(assessments)

        # Analyze confidence trends
        confidence_trend = self._analyze_confidence_trend(assessments)

        # Analyze finding stability
        finding_stability = self._analyze_finding_stability(assessments)

        # Generate overall trend assessment
        overall_trend = self._assess_overall_trend(risk_trend, confidence_trend, finding_stability)

        return {
            "status": "analyzed",
            "entity_id": entity_id,
            "assessment_count": len(assessments),
            "date_range": {
                "first": assessments[0]["assessment_date"].isoformat(),
                "last": assessments[-1]["assessment_date"].isoformat(),
            },
            "risk_trend": risk_trend,
            "confidence_trend": confidence_trend,
            "finding_stability": finding_stability,
            "overall_trend": overall_trend,
            "recommendations": self._generate_trend_recommendations(overall_trend),
        }

    def _analyze_risk_trend(
        self, assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze risk estimate trends."""
        risk_estimates = [
            a["risk_estimate"]
            for a in assessments
            if a["risk_estimate"] is not None
        ]

        if len(risk_estimates) < 2:
            return {"status": "insufficient_data"}

        # Calculate trend direction
        first_half_avg = statistics.mean(risk_estimates[:len(risk_estimates)//2])
        second_half_avg = statistics.mean(risk_estimates[len(risk_estimates)//2:])

        change = second_half_avg - first_half_avg
        percent_change = (change / first_half_avg * 100) if first_half_avg > 0 else 0

        if abs(percent_change) < 10:
            direction = "stable"
        elif percent_change > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        return {
            "status": "analyzed",
            "direction": direction,
            "percent_change": percent_change,
            "first_period_avg": first_half_avg,
            "recent_period_avg": second_half_avg,
            "data_points": len(risk_estimates),
        }

    def _analyze_confidence_trend(
        self, assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze confidence level trends."""
        confidence_levels = [
            a["confidence_level"]
            for a in assessments
            if a["confidence_level"] is not None
        ]

        if len(confidence_levels) < 2:
            return {"status": "insufficient_data"}

        # Map confidence to numeric
        confidence_map = {"low": 1, "moderate": 2, "high": 3}

        numeric_confidence = [
            confidence_map.get(c.lower().split("-")[0].strip(), 2)
            for c in confidence_levels
        ]

        first_half_avg = statistics.mean(numeric_confidence[:len(numeric_confidence)//2])
        second_half_avg = statistics.mean(numeric_confidence[len(numeric_confidence)//2:])

        if second_half_avg > first_half_avg + 0.3:
            direction = "increasing"
        elif second_half_avg < first_half_avg - 0.3:
            direction = "decreasing"
        else:
            direction = "stable"

        return {
            "status": "analyzed",
            "direction": direction,
            "recent_avg_confidence": second_half_avg,
            "data_points": len(confidence_levels),
        }

    def _analyze_finding_stability(
        self, assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze stability of key findings."""
        if len(assessments) < 2:
            return {"status": "insufficient_data"}

        # Compare consecutive assessments
        changes = 0
        for i in range(len(assessments) - 1):
            findings1 = set(assessments[i]["key_findings"])
            findings2 = set(assessments[i+1]["key_findings"])

            # Jaccard similarity
            if findings1 or findings2:
                similarity = len(findings1 & findings2) / len(findings1 | findings2)
            else:
                similarity = 1.0

            if similarity < 0.5:  # Less than 50% overlap
                changes += 1

        stability_rate = 1 - (changes / (len(assessments) - 1))

        if stability_rate >= 0.80:
            stability = "high"
        elif stability_rate >= 0.50:
            stability = "moderate"
        else:
            stability = "low"

        return {
            "status": "analyzed",
            "stability": stability,
            "stability_rate": stability_rate,
            "finding_changes": changes,
        }

    def _assess_overall_trend(
        self,
        risk_trend: Dict[str, Any],
        confidence_trend: Dict[str, Any],
        finding_stability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess overall trend."""
        status_parts = []

        # Risk trend component
        if risk_trend.get("status") == "analyzed":
            if risk_trend["direction"] == "increasing":
                status_parts.append("Increasing risk signal")
            elif risk_trend["direction"] == "decreasing":
                status_parts.append("Decreasing risk signal")
            else:
                status_parts.append("Stable risk signal")

        # Stability component
        if finding_stability.get("status") == "analyzed":
            if finding_stability["stability"] == "high":
                status_parts.append("findings consistent over time")
            elif finding_stability["stability"] == "low":
                status_parts.append("findings vary significantly")

        overall_status = "; ".join(status_parts) if status_parts else "Trend analysis inconclusive"

        return {
            "summary": overall_status,
            "requires_attention": (
                risk_trend.get("direction") == "increasing" or
                finding_stability.get("stability") == "low"
            ),
        }

    def _generate_trend_recommendations(
        self, overall_trend: Dict[str, Any]
    ) -> List[str]:
        """Generate trend-based recommendations."""
        recommendations = []

        if overall_trend.get("requires_attention"):
            recommendations.append(
                "ATTENTION REQUIRED: Significant changes detected in risk assessment. "
                "Review recent evidence and consider updating safety recommendations."
            )

        summary = overall_trend.get("summary", "")
        if "increasing risk" in summary.lower():
            recommendations.append(
                "Risk signal trending upward. "
                "Recommend: Enhanced surveillance and updated risk communication."
            )

        if "vary significantly" in summary.lower():
            recommendations.append(
                "Key findings show high variability. "
                "Recommend: Deeper investigation into sources of inconsistency."
            )

        if not recommendations:
            recommendations.append(
                "Assessment trends are stable and consistent. Continue routine monitoring."
            )

        return recommendations


class ComparativeAnalyzer:
    """
    Compares assessments across different entities (drugs, compounds, etc.).
    """

    def __init__(self):
        """Initialize comparative analyzer."""
        self.entity_assessments: Dict[str, Dict[str, Any]] = {}

    def add_entity_assessment(
        self,
        entity_id: str,
        entity_name: str,
        risk_estimate: Optional[float] = None,
        confidence_level: Optional[str] = None,
        audit_pass_rate: Optional[float] = None,
        key_characteristics: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add entity assessment for comparison.

        Args:
            entity_id: Unique entity identifier
            entity_name: Entity name
            risk_estimate: Risk estimate
            confidence_level: Confidence level
            audit_pass_rate: Audit pass rate for this entity
            key_characteristics: Key characteristics for comparison
            metadata: Additional metadata
        """
        self.entity_assessments[entity_id] = {
            "entity_name": entity_name,
            "risk_estimate": risk_estimate,
            "confidence_level": confidence_level,
            "audit_pass_rate": audit_pass_rate,
            "key_characteristics": key_characteristics or {},
            "metadata": metadata or {},
        }

    def compare_entities(
        self, entity_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple entities.

        Args:
            entity_ids: List of entity IDs to compare (if None, compare all)

        Returns:
            Comparison results
        """
        if not self.entity_assessments:
            return {
                "status": "no_data",
                "message": "No entity assessments available for comparison",
            }

        # Select entities to compare
        if entity_ids:
            entities = {
                eid: self.entity_assessments[eid]
                for eid in entity_ids
                if eid in self.entity_assessments
            }
        else:
            entities = self.entity_assessments

        if len(entities) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 entities for comparison",
            }

        # Risk ranking
        risk_ranking = self._rank_by_risk(entities)

        # Confidence comparison
        confidence_comparison = self._compare_confidence(entities)

        # Quality comparison (audit pass rates)
        quality_comparison = self._compare_quality(entities)

        # Generate insights
        insights = self._generate_comparative_insights(
            risk_ranking, confidence_comparison, quality_comparison
        )

        return {
            "status": "compared",
            "entities_compared": len(entities),
            "risk_ranking": risk_ranking,
            "confidence_comparison": confidence_comparison,
            "quality_comparison": quality_comparison,
            "insights": insights,
            "recommendations": self._generate_comparative_recommendations(insights),
        }

    def _rank_by_risk(
        self, entities: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank entities by risk estimate."""
        ranked = []

        for entity_id, data in entities.items():
            risk = data.get("risk_estimate")
            if risk is not None:
                ranked.append({
                    "entity_id": entity_id,
                    "entity_name": data["entity_name"],
                    "risk_estimate": risk,
                })

        # Sort by risk (descending)
        ranked.sort(key=lambda x: x["risk_estimate"], reverse=True)

        # Add rank
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked

    def _compare_confidence(
        self, entities: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare confidence levels across entities."""
        confidence_counts = defaultdict(int)

        for data in entities.values():
            confidence = data.get("confidence_level", "unknown").lower()
            confidence_counts[confidence] += 1

        return {
            "distribution": dict(confidence_counts),
            "most_common": max(confidence_counts.items(), key=lambda x: x[1])[0],
        }

    def _compare_quality(
        self, entities: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare assessment quality (audit pass rates)."""
        quality_data = []

        for entity_id, data in entities.items():
            pass_rate = data.get("audit_pass_rate")
            if pass_rate is not None:
                quality_data.append({
                    "entity_id": entity_id,
                    "entity_name": data["entity_name"],
                    "audit_pass_rate": pass_rate,
                })

        # Sort by pass rate (descending)
        quality_data.sort(key=lambda x: x["audit_pass_rate"], reverse=True)

        avg_pass_rate = (
            statistics.mean(item["audit_pass_rate"] for item in quality_data)
            if quality_data else None
        )

        return {
            "by_entity": quality_data,
            "average_pass_rate": avg_pass_rate,
        }

    def _generate_comparative_insights(
        self,
        risk_ranking: List[Dict[str, Any]],
        confidence_comparison: Dict[str, Any],
        quality_comparison: Dict[str, Any]
    ) -> List[str]:
        """Generate comparative insights."""
        insights = []

        # Risk insights
        if risk_ranking:
            highest_risk = risk_ranking[0]
            lowest_risk = risk_ranking[-1]

            if len(risk_ranking) >= 2:
                risk_range = highest_risk["risk_estimate"] - lowest_risk["risk_estimate"]
                if risk_range > 0.05:  # >5% difference
                    insights.append(
                        f"Substantial risk variation detected: "
                        f"{highest_risk['entity_name']} ({highest_risk['risk_estimate']:.1%}) "
                        f"vs {lowest_risk['entity_name']} ({lowest_risk['risk_estimate']:.1%})"
                    )

        # Confidence insights
        most_common_confidence = confidence_comparison.get("most_common", "unknown")
        if most_common_confidence != "unknown":
            insights.append(
                f"Most common confidence level: {most_common_confidence}"
            )

        # Quality insights
        avg_pass_rate = quality_comparison.get("average_pass_rate")
        if avg_pass_rate is not None:
            if avg_pass_rate < 0.70:
                insights.append(
                    f"Low average audit pass rate ({avg_pass_rate:.1%}) - "
                    "quality improvement needed"
                )

        return insights

    def _generate_comparative_recommendations(
        self, insights: List[str]
    ) -> List[str]:
        """Generate comparative recommendations."""
        recommendations = []

        for insight in insights:
            if "substantial risk variation" in insight.lower():
                recommendations.append(
                    "Investigate sources of risk variation. "
                    "Consider targeted risk mitigation for high-risk entities."
                )

            if "low average audit pass rate" in insight.lower():
                recommendations.append(
                    "Prioritize quality improvement initiatives. "
                    "Review assessment methodologies and auditor training."
                )

        if not recommendations:
            recommendations.append(
                "Comparative analysis shows reasonable consistency. "
                "Continue standard monitoring protocols."
            )

        return recommendations
