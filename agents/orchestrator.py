"""Orchestrator agent for managing multi-task cases."""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models.case import Case, CaseStatus
from models.task import Task, TaskType, TaskStatus
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine, ResolutionDecision
from core.context_compressor import ContextCompressor


logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator agent for managing complex multi-task safety cases.

    The orchestrator:
    1. Receives a safety case
    2. Decomposes it into subtasks
    3. Routes tasks to resolution engine (which handles worker→audit→retry loop)
    4. Receives only compressed summaries back
    5. Synthesizes final report from compressed results

    This design prevents context overload by delegating the validation
    loop to the resolution engine and only receiving minimal summaries.
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        resolution_engine: ResolutionEngine,
        context_compressor: ContextCompressor,
    ):
        """
        Initialize the orchestrator.

        Args:
            task_executor: TaskExecutor instance
            audit_engine: AuditEngine instance
            resolution_engine: ResolutionEngine instance
            context_compressor: ContextCompressor instance
        """
        self.task_executor = task_executor
        self.audit_engine = audit_engine
        self.resolution_engine = resolution_engine
        self.context_compressor = context_compressor
        self.active_cases: Dict[str, Case] = {}
        self.task_summaries: Dict[str, Dict[str, Any]] = {}  # case_id -> {task_id -> summary}

    def process_case(self, case: Case) -> Dict[str, Any]:
        """
        Process a complete safety case from intake to final report.

        Args:
            case: Case to process

        Returns:
            Final case report with findings
        """
        logger.info(f"Orchestrator: Processing case {case.case_id}: {case.title}")

        try:
            # Update case status
            case.update_status(CaseStatus.IN_PROGRESS)
            self.active_cases[case.case_id] = case
            self.task_summaries[case.case_id] = {}

            # Step 1: Decompose case into tasks
            tasks = self._decompose_case(case)
            logger.info(f"Orchestrator: Decomposed into {len(tasks)} tasks")

            # Step 2: Execute tasks (resolution engine handles validation loop)
            for task in tasks:
                self._execute_task_with_validation(case, task)

            # Step 3: Check if any tasks require human review
            if self._requires_human_review(case):
                logger.warning(f"Case {case.case_id} requires human review")
                case.update_status(CaseStatus.REQUIRES_HUMAN_REVIEW)
                return self._generate_interim_report(case)

            # Step 4: Synthesize final report from compressed summaries
            final_report = self._synthesize_final_report(case)

            # Update case
            case.final_report = final_report
            case.update_status(CaseStatus.COMPLETED)

            logger.info(f"Orchestrator: Case {case.case_id} completed successfully")

            return final_report

        except Exception as e:
            logger.error(f"Orchestrator: Error processing case {case.case_id}: {str(e)}")
            case.metadata["error"] = str(e)
            case.update_status(CaseStatus.REQUIRES_HUMAN_REVIEW)
            raise

        finally:
            # Clean up
            if case.case_id in self.active_cases:
                del self.active_cases[case.case_id]

    def _decompose_case(self, case: Case) -> List[Task]:
        """
        Decompose a case into constituent tasks.

        This is where the orchestrator determines what work needs to be done.

        Args:
            case: Case to decompose

        Returns:
            List of tasks to execute
        """
        tasks = []

        # Example decomposition logic (would be more sophisticated in production)
        # For a safety question, we typically want:

        # 1. Literature review
        lit_task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            case_id=case.case_id,
            input_data={
                "query": case.question,
                "context": case.context,
                "data_sources": case.data_sources,
            },
        )
        tasks.append(lit_task)
        case.add_task(lit_task.task_id)

        # 2. Statistical analysis (if data available)
        if case.context.get("has_clinical_data", False):
            stats_task = Task(
                task_type=TaskType.STATISTICAL_ANALYSIS,
                case_id=case.case_id,
                input_data={
                    "query": case.question,
                    "context": case.context,
                    "analysis_type": "risk_assessment",
                },
            )
            tasks.append(stats_task)
            case.add_task(stats_task.task_id)

        # Additional tasks could be added based on case requirements:
        # - Risk modeling
        # - Mechanistic inference
        # - Causality assessment

        return tasks

    def _execute_task_with_validation(self, case: Case, task: Task) -> None:
        """
        Execute a task with validation through the resolution engine.

        The resolution engine handles the full worker→audit→retry loop.
        This method only receives the compressed summary.

        Args:
            case: Parent case
            task: Task to execute
        """
        logger.info(f"Orchestrator: Executing task {task.task_id} ({task.task_type.value})")

        try:
            # Resolution engine handles the entire validation loop
            decision, audit_result = self.resolution_engine.execute_with_validation(task)

            # Compress the result into minimal summary
            compressed = self.context_compressor.compress_task_result(task, audit_result)

            # Store only the compressed summary (NOT the full output)
            self.task_summaries[case.case_id][task.task_id] = compressed

            logger.info(
                f"Orchestrator: Task {task.task_id} completed with decision: {decision.value}"
            )

            # Add finding to case (compressed only)
            case.add_finding(
                task.task_type.value,
                {
                    "summary": compressed["summary"],
                    "key_findings": compressed["key_findings"],
                    "status": decision.value,
                }
            )

            # Log compression stats
            stats = self.context_compressor.get_compression_stats(task.task_id)
            if stats:
                logger.info(
                    f"Orchestrator: Compressed task {task.task_id} by "
                    f"{stats['compression_ratio']:.1f}%"
                )

        except Exception as e:
            logger.error(f"Orchestrator: Task {task.task_id} failed: {str(e)}")
            case.add_finding(
                task.task_type.value,
                {
                    "summary": f"Task failed: {str(e)}",
                    "status": "failed",
                }
            )

    def _requires_human_review(self, case: Case) -> bool:
        """
        Check if case requires human review.

        Args:
            case: Case to check

        Returns:
            True if human review needed
        """
        # Check if any tasks were escalated
        for task_id in case.tasks:
            summary = self.task_summaries[case.case_id].get(task_id, {})
            if summary.get("metadata", {}).get("requires_human_review"):
                return True

        return False

    def _synthesize_final_report(self, case: Case) -> Dict[str, Any]:
        """
        Synthesize final report from compressed task summaries.

        This uses ONLY the compressed summaries, not full task outputs.

        Args:
            case: Case to synthesize report for

        Returns:
            Final report dictionary
        """
        logger.info(f"Orchestrator: Synthesizing final report for case {case.case_id}")

        # Collect all task summaries
        summaries = self.task_summaries[case.case_id]

        # Build final report
        report = {
            "case_id": case.case_id,
            "title": case.title,
            "question": case.question,
            "executive_summary": self._generate_executive_summary(case, summaries),
            "findings_by_task": case.findings,
            "overall_assessment": self._generate_overall_assessment(case, summaries),
            "recommendations": self._generate_recommendations(case, summaries),
            "confidence_level": self._assess_overall_confidence(summaries),
            "limitations": self._collect_limitations(summaries),
            "metadata": {
                "completion_date": datetime.utcnow().isoformat(),
                "tasks_completed": len(case.tasks),
                "compression_ratio": self.context_compressor.get_average_compression_ratio(),
            },
        }

        return report

    def _generate_executive_summary(
        self, case: Case, summaries: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate executive summary from task summaries."""
        summary_parts = [f"Safety assessment for: {case.question}"]

        for task_id, summary in summaries.items():
            summary_parts.append(summary.get("summary", ""))

        return " ".join(summary_parts)

    def _generate_overall_assessment(
        self, case: Case, summaries: Dict[str, Dict[str, Any]]
    ) -> str:
        """Generate overall assessment."""
        # Collect key findings
        assessments = []

        for summary in summaries.values():
            key_findings = summary.get("key_findings", {})
            if "conclusion" in key_findings:
                assessments.append(key_findings["conclusion"])

        if not assessments:
            return "Insufficient evidence for definitive assessment. Further investigation recommended."

        return " ".join(assessments)

    def _generate_recommendations(
        self, case: Case, summaries: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []

        # Extract recommendations from task findings
        for summary in summaries.values():
            key_findings = summary.get("key_findings", {})
            if "recommendation" in key_findings:
                recommendations.append(key_findings["recommendation"])

        if not recommendations:
            recommendations.append("Conduct additional studies to gather more evidence")

        return recommendations

    def _assess_overall_confidence(self, summaries: Dict[str, Dict[str, Any]]) -> str:
        """Assess overall confidence level."""
        confidence_levels = []

        for summary in summaries.values():
            key_findings = summary.get("key_findings", {})
            if "confidence" in key_findings:
                confidence_levels.append(key_findings["confidence"])

        # Conservative approach: take lowest confidence
        if any("low" in str(c).lower() for c in confidence_levels):
            return "Low - requires external validation"
        elif any("moderate" in str(c).lower() for c in confidence_levels):
            return "Moderate - additional evidence would strengthen findings"
        else:
            return "Requires external validation"

    def _collect_limitations(self, summaries: Dict[str, Dict[str, Any]]) -> List[str]:
        """Collect all limitations from task summaries."""
        limitations = set()

        for summary in summaries.values():
            key_findings = summary.get("key_findings", {})
            # Limitations are typically in the full task output, not compressed
            # For now, add generic limitation
            limitations.add("Analysis based on available evidence at time of review")

        return list(limitations)

    def _generate_interim_report(self, case: Case) -> Dict[str, Any]:
        """Generate interim report when human review is required."""
        return {
            "case_id": case.case_id,
            "status": "requires_human_review",
            "title": case.title,
            "question": case.question,
            "interim_findings": case.findings,
            "escalation_reason": "One or more tasks require expert review",
            "completed_tasks": len(case.tasks),
            "next_steps": [
                "Expert review of flagged issues",
                "Additional data collection if needed",
                "Refinement of analysis based on expert input",
            ],
        }
