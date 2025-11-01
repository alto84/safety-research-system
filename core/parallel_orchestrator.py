"""Enhanced parallel orchestrator with task scheduling, dependency management, and progress tracking."""
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from models.case import Case, CaseStatus
from models.task import Task, TaskType, TaskStatus
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels for scheduling."""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class ParallelOrchestrator:
    """
    Enhanced orchestrator with parallel task execution, scheduling, and dependency management.

    Features:
    - Parallel task execution with thread pool
    - Task prioritization and scheduling
    - Dependency management (prerequisite tasks)
    - Progress tracking and status monitoring
    - Dynamic resource allocation
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        resolution_engine: ResolutionEngine,
        context_compressor: ContextCompressor,
        max_workers: int = 3,
        enable_parallel: bool = True,
    ):
        """
        Initialize parallel orchestrator.

        Args:
            task_executor: TaskExecutor instance
            audit_engine: AuditEngine instance
            resolution_engine: ResolutionEngine instance
            context_compressor: ContextCompressor instance
            max_workers: Maximum number of parallel workers
            enable_parallel: Enable parallel execution (False for sequential)
        """
        self.task_executor = task_executor
        self.audit_engine = audit_engine
        self.resolution_engine = resolution_engine
        self.context_compressor = context_compressor
        self.max_workers = max_workers
        self.enable_parallel = enable_parallel

        self.active_cases: Dict[str, Case] = {}
        self.task_summaries: Dict[str, Dict[str, Any]] = {}  # case_id -> {task_id -> summary}

        # Task scheduling state
        self.task_queue: List[Task] = []
        self.task_priorities: Dict[str, TaskPriority] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}  # task_id -> set of prerequisite task_ids
        self.completed_tasks: Set[str] = set()

        # Progress tracking
        self.task_progress: Dict[str, Dict[str, Any]] = {}  # task_id -> progress info
        self.case_metrics: Dict[str, Dict[str, Any]] = {}  # case_id -> metrics

    def process_case(self, case: Case) -> Dict[str, Any]:
        """
        Process a complete safety case with parallel task execution.

        Args:
            case: Case to process

        Returns:
            Final case report with findings
        """
        logger.info(f"ParallelOrchestrator: Processing case {case.case_id}: {case.title}")
        start_time = time.time()

        try:
            # Update case status
            case.update_status(CaseStatus.IN_PROGRESS)
            self.active_cases[case.case_id] = case
            self.task_summaries[case.case_id] = {}
            self.case_metrics[case.case_id] = {
                "start_time": start_time,
                "tasks_total": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "parallel_enabled": self.enable_parallel,
            }

            # Step 1: Decompose case into tasks
            tasks = self._decompose_case(case)
            logger.info(f"ParallelOrchestrator: Decomposed into {len(tasks)} tasks")
            self.case_metrics[case.case_id]["tasks_total"] = len(tasks)

            # Step 2: Analyze dependencies and prioritize
            self._analyze_task_dependencies(tasks, case)
            self._prioritize_tasks(tasks, case)

            # Step 3: Execute tasks (parallel or sequential based on dependencies)
            if self.enable_parallel:
                self._execute_tasks_parallel(case, tasks)
            else:
                self._execute_tasks_sequential(case, tasks)

            # Step 4: Check if any tasks require human review
            if self._requires_human_review(case):
                logger.warning(f"Case {case.case_id} requires human review")
                case.update_status(CaseStatus.REQUIRES_HUMAN_REVIEW)
                return self._generate_interim_report(case)

            # Step 5: Synthesize final report from compressed summaries
            final_report = self._synthesize_final_report(case)

            # Update case
            case.final_report = final_report
            case.update_status(CaseStatus.COMPLETED)

            # Calculate metrics
            end_time = time.time()
            self.case_metrics[case.case_id]["end_time"] = end_time
            self.case_metrics[case.case_id]["total_duration"] = end_time - start_time

            logger.info(
                f"ParallelOrchestrator: Case {case.case_id} completed successfully "
                f"in {end_time - start_time:.2f}s"
            )

            # Add metrics to report
            final_report["performance_metrics"] = self.case_metrics[case.case_id]

            return final_report

        except Exception as e:
            logger.error(f"ParallelOrchestrator: Error processing case {case.case_id}: {str(e)}")
            case.metadata["error"] = str(e)
            case.update_status(CaseStatus.REQUIRES_HUMAN_REVIEW)
            self.case_metrics[case.case_id]["error"] = str(e)
            raise

        finally:
            # Clean up
            if case.case_id in self.active_cases:
                del self.active_cases[case.case_id]

    def _decompose_case(self, case: Case) -> List[Task]:
        """
        Decompose a case into constituent tasks.

        Args:
            case: Case to decompose

        Returns:
            List of tasks to execute
        """
        tasks = []

        # Literature review (usually independent)
        lit_task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            case_id=case.case_id,
            input_data={
                "query": case.question,
                "context": case.context,
                "data_sources": case.data_sources,
            },
            metadata={"priority": "high"},
        )
        tasks.append(lit_task)
        case.add_task(lit_task.task_id)

        # Risk modeling (may depend on literature review for incidence data)
        if case.context.get("has_risk_data", False) or case.context.get("assess_risk", True):
            risk_task = Task(
                task_type=TaskType.RISK_MODELING,
                case_id=case.case_id,
                input_data={
                    "query": f"Quantitative risk assessment for {case.question}",
                    "context": case.context,
                    "risk_data": case.context.get("risk_data", {}),
                    "prior_data": case.context.get("prior_risk_data", {}),
                },
                metadata={
                    "priority": "high",
                    "depends_on": [lit_task.task_id],  # May use literature findings
                },
            )
            tasks.append(risk_task)
            case.add_task(risk_task.task_id)

        # Mechanistic inference (independent or may benefit from literature)
        if case.context.get("assess_mechanism", True):
            mech_task = Task(
                task_type=TaskType.MECHANISTIC_INFERENCE,
                case_id=case.case_id,
                input_data={
                    "query": f"Mechanistic analysis for {case.question}",
                    "context": case.context,
                    "mechanism_data": case.context.get("mechanism_data", {}),
                    "pathway_data": case.context.get("pathway_data", {}),
                },
                metadata={
                    "priority": "normal",
                    "depends_on": [],  # Can run in parallel with literature
                },
            )
            tasks.append(mech_task)
            case.add_task(mech_task.task_id)

        # Statistical analysis (if data available)
        if case.context.get("has_clinical_data", False):
            stats_task = Task(
                task_type=TaskType.STATISTICAL_ANALYSIS,
                case_id=case.case_id,
                input_data={
                    "query": case.question,
                    "context": case.context,
                    "analysis_type": "risk_assessment",
                },
                metadata={
                    "priority": "high",
                },
            )
            tasks.append(stats_task)
            case.add_task(stats_task.task_id)

        return tasks

    def _analyze_task_dependencies(self, tasks: List[Task], case: Case) -> None:
        """
        Analyze and record task dependencies.

        Args:
            tasks: List of tasks
            case: Parent case
        """
        for task in tasks:
            task_id = task.task_id
            depends_on = task.metadata.get("depends_on", [])

            self.task_dependencies[task_id] = set(depends_on)

            logger.info(
                f"Task {task_id} ({task.task_type.value}): "
                f"{len(depends_on)} dependencies"
            )

    def _prioritize_tasks(self, tasks: List[Task], case: Case) -> None:
        """
        Assign priorities to tasks for scheduling.

        Args:
            tasks: List of tasks
            case: Parent case
        """
        for task in tasks:
            # Get priority from metadata or default
            priority_str = task.metadata.get("priority", "normal").upper()

            try:
                priority = TaskPriority[priority_str]
            except KeyError:
                priority = TaskPriority.NORMAL
                logger.warning(
                    f"Invalid priority '{priority_str}' for task {task.task_id}, "
                    f"using NORMAL"
                )

            self.task_priorities[task.task_id] = priority

            logger.info(
                f"Task {task.task_id} ({task.task_type.value}): "
                f"Priority {priority.name}"
            )

    def _execute_tasks_parallel(self, case: Case, tasks: List[Task]) -> None:
        """
        Execute tasks in parallel respecting dependencies.

        Args:
            case: Parent case
            tasks: Tasks to execute
        """
        logger.info(
            f"ParallelOrchestrator: Executing {len(tasks)} tasks in parallel "
            f"(max_workers={self.max_workers})"
        )

        remaining_tasks = {task.task_id: task for task in tasks}
        self.completed_tasks = set()

        while remaining_tasks:
            # Find tasks ready to execute (dependencies satisfied)
            ready_tasks = self._get_ready_tasks(remaining_tasks)

            if not ready_tasks:
                if remaining_tasks:
                    # Deadlock: remaining tasks but none ready
                    logger.error(
                        f"Dependency deadlock detected: {len(remaining_tasks)} tasks remaining, "
                        f"none ready to execute"
                    )
                    raise RuntimeError("Task dependency deadlock detected")
                break

            # Sort ready tasks by priority
            ready_tasks.sort(
                key=lambda t: (
                    self.task_priorities.get(t.task_id, TaskPriority.NORMAL).value,
                    t.created_at
                )
            )

            # Execute ready tasks in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {
                    executor.submit(self._execute_single_task, case, task): task
                    for task in ready_tasks
                }

                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        future.result()  # Wait for completion
                        self.completed_tasks.add(task.task_id)
                        remaining_tasks.pop(task.task_id)
                        self.case_metrics[case.case_id]["tasks_completed"] += 1

                        logger.info(
                            f"Task {task.task_id} completed. "
                            f"Progress: {len(self.completed_tasks)}/{len(tasks)}"
                        )
                    except Exception as e:
                        logger.error(f"Task {task.task_id} failed: {e}")
                        self.case_metrics[case.case_id]["tasks_failed"] += 1
                        # Remove from remaining but don't add to completed
                        remaining_tasks.pop(task.task_id)

        logger.info(
            f"ParallelOrchestrator: All tasks completed. "
            f"Success: {self.case_metrics[case.case_id]['tasks_completed']}, "
            f"Failed: {self.case_metrics[case.case_id]['tasks_failed']}"
        )

    def _execute_tasks_sequential(self, case: Case, tasks: List[Task]) -> None:
        """
        Execute tasks sequentially (fallback mode).

        Args:
            case: Parent case
            tasks: Tasks to execute
        """
        logger.info(f"ParallelOrchestrator: Executing {len(tasks)} tasks sequentially")

        # Sort by priority
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                self.task_priorities.get(t.task_id, TaskPriority.NORMAL).value,
                t.created_at
            )
        )

        for i, task in enumerate(sorted_tasks):
            logger.info(f"Executing task {i+1}/{len(tasks)}: {task.task_type.value}")

            try:
                self._execute_single_task(case, task)
                self.completed_tasks.add(task.task_id)
                self.case_metrics[case.case_id]["tasks_completed"] += 1
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                self.case_metrics[case.case_id]["tasks_failed"] += 1

    def _get_ready_tasks(self, remaining_tasks: Dict[str, Task]) -> List[Task]:
        """
        Get tasks that are ready to execute (dependencies satisfied).

        Args:
            remaining_tasks: Dictionary of remaining tasks

        Returns:
            List of ready tasks
        """
        ready = []

        for task_id, task in remaining_tasks.items():
            dependencies = self.task_dependencies.get(task_id, set())

            # Check if all dependencies completed
            if dependencies.issubset(self.completed_tasks):
                ready.append(task)

        return ready

    def _execute_single_task(self, case: Case, task: Task) -> None:
        """
        Execute a single task with validation.

        Args:
            case: Parent case
            task: Task to execute
        """
        task_id = task.task_id
        start_time = time.time()

        # Update progress
        self.task_progress[task_id] = {
            "status": "in_progress",
            "start_time": start_time,
        }

        logger.info(f"Executing task {task_id} ({task.task_type.value})")

        try:
            # Resolution engine handles the entire validation loop
            decision, audit_result = self.resolution_engine.execute_with_validation(task)

            # Compress the result into minimal summary
            compressed = self.context_compressor.compress_task_result(task, audit_result)

            # Store only the compressed summary
            self.task_summaries[case.case_id][task.task_id] = compressed

            # Update progress
            end_time = time.time()
            self.task_progress[task_id].update({
                "status": "completed",
                "end_time": end_time,
                "duration": end_time - start_time,
                "decision": decision.value,
            })

            logger.info(
                f"Task {task_id} completed in {end_time - start_time:.2f}s "
                f"with decision: {decision.value}"
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

        except Exception as e:
            end_time = time.time()
            self.task_progress[task_id].update({
                "status": "failed",
                "end_time": end_time,
                "duration": end_time - start_time,
                "error": str(e),
            })

            logger.error(f"Task {task_id} failed: {str(e)}")
            case.add_finding(
                task.task_type.value,
                {
                    "summary": f"Task failed: {str(e)}",
                    "status": "failed",
                }
            )
            raise

    def get_progress_status(self, case_id: str) -> Dict[str, Any]:
        """
        Get progress status for a case.

        Args:
            case_id: Case ID

        Returns:
            Progress status dictionary
        """
        if case_id not in self.case_metrics:
            return {"status": "not_found"}

        metrics = self.case_metrics[case_id]
        tasks_total = metrics.get("tasks_total", 0)
        tasks_completed = metrics.get("tasks_completed", 0)

        progress_percentage = (
            (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0
        )

        return {
            "case_id": case_id,
            "status": "in_progress" if tasks_completed < tasks_total else "completed",
            "progress_percentage": progress_percentage,
            "tasks_total": tasks_total,
            "tasks_completed": tasks_completed,
            "tasks_failed": metrics.get("tasks_failed", 0),
            "start_time": metrics.get("start_time"),
            "parallel_enabled": metrics.get("parallel_enabled", False),
            "task_details": self.task_progress,
        }

    def _requires_human_review(self, case: Case) -> bool:
        """Check if case requires human review."""
        for task_id in case.tasks:
            summary = self.task_summaries[case.case_id].get(task_id, {})
            if summary.get("metadata", {}).get("requires_human_review"):
                return True
        return False

    def _synthesize_final_report(self, case: Case) -> Dict[str, Any]:
        """Synthesize final report from compressed task summaries."""
        logger.info(f"ParallelOrchestrator: Synthesizing final report for case {case.case_id}")

        summaries = self.task_summaries[case.case_id]

        return {
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
