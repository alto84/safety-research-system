"""Resolution engine for handling audit failures and retries."""
import logging
import json
from typing import Dict, Any, Optional
from enum import Enum

from models.task import Task, TaskStatus
from models.audit_result import AuditResult, AuditStatus, IssueSeverity
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.llm_integration import ThoughtPipeExecutor, get_reasoning_cache


logger = logging.getLogger(__name__)


class ResolutionDecision(Enum):
    """Possible decisions from resolution engine."""
    ACCEPT = "accept"  # Audit passed, accept results
    RETRY = "retry"    # Audit failed, retry task with corrections
    ESCALATE = "escalate"  # Cannot resolve, escalate to human
    ABORT = "abort"    # Max retries exceeded or critical failure


class ResolutionEngine:
    """
    Manages resolution of audit failures through retries and escalation.

    This class implements the core loop:
    1. Task executes
    2. Audit validates
    3. If audit fails and retries available: provide corrections and retry
    4. If audit passes or max retries exceeded: finalize
    5. If critical issues: escalate to human

    The resolution engine prevents context overload by handling the
    retry loop without involving the orchestrator.
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        max_retries: int = 2,
        enable_intelligent_resolution: bool = True,
    ):
        """
        Initialize the resolution engine.

        Args:
            task_executor: TaskExecutor instance for running tasks
            audit_engine: AuditEngine instance for validating outputs
            max_retries: Maximum retry attempts per task
            enable_intelligent_resolution: If True, use LLM-driven resolution decisions
        """
        self.task_executor = task_executor
        self.audit_engine = audit_engine
        self.max_retries = max_retries
        self.resolution_history: Dict[str, list] = {}
        self.enable_intelligent_resolution = enable_intelligent_resolution
        self.thought_pipe = ThoughtPipeExecutor() if enable_intelligent_resolution else None
        self.reasoning_cache = get_reasoning_cache() if enable_intelligent_resolution else None

    def execute_with_validation(self, task: Task) -> tuple[ResolutionDecision, Optional[AuditResult]]:
        """
        Execute a task with automatic validation and retry on failure.

        This is the main entry point for the Task→Audit→Resolve loop.

        Args:
            task: Task to execute and validate

        Returns:
            Tuple of (ResolutionDecision, final AuditResult)
        """
        task.max_retries = self.max_retries
        resolution_log = []

        logger.info(f"Starting execution with validation for task {task.task_id}")

        while True:
            try:
                # Step 1: Execute task
                logger.info(f"Executing task {task.task_id} (attempt {task.retry_count + 1})")
                self.task_executor.execute_task(task)
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "executed",
                    "status": "success",
                })

                # Step 2: Audit task output
                logger.info(f"Auditing task {task.task_id}")
                task.update_status(TaskStatus.AUDITING)
                audit_result = self.audit_engine.audit_task(task)
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "audited",
                    "status": audit_result.status.value,
                    "issues_count": len(audit_result.issues),
                })

                # Step 3: Evaluate audit result
                if self.enable_intelligent_resolution:
                    try:
                        decision = self._evaluate_audit_result_intelligent(task, audit_result)
                        logger.info(f"Intelligent resolution: {decision.value}")
                    except Exception as e:
                        logger.warning(f"Intelligent resolution failed: {e}. Falling back to hard-coded.")
                        decision = self._evaluate_audit_result(task, audit_result)
                else:
                    decision = self._evaluate_audit_result(task, audit_result)

                if decision == ResolutionDecision.ACCEPT:
                    logger.info(f"Task {task.task_id} accepted after validation")
                    task.update_status(TaskStatus.COMPLETED)
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.RETRY:
                    logger.info(f"Task {task.task_id} requires revision (attempt {task.retry_count + 1})")
                    task.update_status(TaskStatus.REQUIRES_REVISION)
                    task.increment_retry()

                    # Prepare corrections for retry
                    corrections = self._prepare_corrections(audit_result)
                    task.input_data["corrections"] = corrections
                    task.input_data["previous_output"] = task.output_data
                    task.input_data["audit_feedback"] = audit_result.summary

                    resolution_log.append({
                        "attempt": task.retry_count,
                        "action": "retry_scheduled",
                        "corrections_count": len(corrections),
                    })

                    # Continue loop to retry
                    continue

                elif decision == ResolutionDecision.ESCALATE:
                    logger.warning(f"Task {task.task_id} escalated to human review")
                    task.update_status(TaskStatus.AUDIT_FAILED)
                    task.metadata["requires_human_review"] = True
                    task.metadata["escalation_reason"] = "Critical audit issues found"
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.ABORT:
                    logger.error(f"Task {task.task_id} aborted after {task.retry_count} attempts")
                    task.update_status(TaskStatus.FAILED)
                    task.metadata["abort_reason"] = "Max retries exceeded"
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

            except Exception as e:
                logger.error(f"Error in resolution loop for task {task.task_id}: {str(e)}")
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "error",
                    "error": str(e),
                })
                task.update_status(TaskStatus.FAILED)
                task.metadata["error"] = str(e)
                self._save_resolution_history(task.task_id, resolution_log)
                return ResolutionDecision.ABORT, None

    def _evaluate_audit_result(self, task: Task, audit_result: AuditResult) -> ResolutionDecision:
        """
        Evaluate audit result and determine next action.

        Args:
            task: Task that was audited
            audit_result: Result of the audit

        Returns:
            ResolutionDecision indicating next action
        """
        # If audit passed, accept the task
        if audit_result.status == AuditStatus.PASSED:
            return ResolutionDecision.ACCEPT

        # If audit has critical issues, escalate immediately
        if audit_result.has_critical_issues():
            logger.warning(f"Task {task.task_id} has critical issues, escalating")
            return ResolutionDecision.ESCALATE

        # If audit failed but task can retry, schedule retry
        if audit_result.status == AuditStatus.FAILED and task.can_retry():
            return ResolutionDecision.RETRY

        # If max retries exceeded, abort
        if not task.can_retry():
            logger.warning(f"Task {task.task_id} exceeded max retries")
            return ResolutionDecision.ABORT

        # Default: escalate for human review
        return ResolutionDecision.ESCALATE

    def _prepare_corrections(self, audit_result: AuditResult) -> list[Dict[str, Any]]:
        """
        Prepare correction instructions from audit result.

        Args:
            audit_result: Audit result containing issues

        Returns:
            List of correction instructions
        """
        corrections = []

        for issue in audit_result.issues:
            correction = {
                "category": issue.category,
                "severity": issue.severity.value,
                "description": issue.description,
                "location": issue.location,
                "suggested_fix": issue.suggested_fix,
                "guideline_reference": issue.guideline_reference,
            }
            corrections.append(correction)

        # Add general recommendations
        for rec in audit_result.recommendations:
            corrections.append({
                "category": "recommendation",
                "severity": "info",
                "description": rec,
            })

        return corrections

    def _save_resolution_history(self, task_id: str, resolution_log: list) -> None:
        """Save resolution history for debugging and analysis."""
        self.resolution_history[task_id] = resolution_log
        logger.debug(f"Saved resolution history for task {task_id}: {len(resolution_log)} entries")

    def get_resolution_history(self, task_id: str) -> list:
        """Get resolution history for a task."""
        return self.resolution_history.get(task_id, [])

    def _evaluate_audit_result_intelligent(self, task: Task, audit_result: AuditResult) -> ResolutionDecision:
        """
        Use LLM reasoning to determine resolution decision based on audit result.

        This is a THOUGHT PIPE: Instead of binary pass/fail logic, Claude analyzes:
        - Issue severity and fixability
        - Case priority and time constraints
        - Probability that retry would actually fix the issues
        - Whether partial acceptance with caveats is appropriate

        Args:
            task: Task that was audited
            audit_result: Result of the audit

        Returns:
            ResolutionDecision with intelligent reasoning
        """
        # HARD CONSTRAINTS - bypass LLM for critical violations
        if audit_result.has_critical_issues():
            critical_issues = [i for i in audit_result.issues if i.severity == IssueSeverity.CRITICAL]

            # Auto-escalate for fabrication (no LLM override)
            fabrication_categories = [
                "fabricated_source",
                "fabricated_pmid",
                "score_fabrication",
                "banned_language"
            ]
            if any(issue.category in fabrication_categories for issue in critical_issues):
                logger.warning(
                    f"Task {task.task_id}: Fabrication detected - AUTO-ESCALATE (bypassing LLM)"
                )
                return ResolutionDecision.ESCALATE

        # If audit passed cleanly, accept (no LLM needed)
        if audit_result.status == AuditStatus.PASSED:
            return ResolutionDecision.ACCEPT

        # If max retries exceeded, abort (no LLM override)
        if not task.can_retry():
            logger.warning(f"Task {task.task_id}: Max retries exceeded - AUTO-ABORT")
            return ResolutionDecision.ABORT

        # Check cache first
        cache_key_context = {
            "task_id": task.task_id,
            "retry_count": task.retry_count,
            "audit_status": audit_result.status.value,
            "issues": [
                {"category": i.category, "severity": i.severity.value}
                for i in audit_result.issues
            ]
        }

        if self.reasoning_cache:
            cached = self.reasoning_cache.get(
                prompt="intelligent_resolution_decision",
                context=cache_key_context
            )
            if cached:
                decision_str = cached.get("decision", "").upper()
                try:
                    return ResolutionDecision(decision_str.lower())
                except ValueError:
                    pass  # Invalid cached decision, proceed with LLM call

        # Build rich context for Claude
        context = self._build_resolution_context(task, audit_result)

        # Build reasoning prompt
        prompt = self._build_resolution_prompt()

        # Execute thought pipe
        response = self.thought_pipe.execute_thought_pipe(
            prompt=prompt,
            context=context,
            validation_fn=self._validate_resolution_response,
            max_retries=1
        )

        # Extract decision
        decision_str = response.get("decision", "").upper()
        reasoning = response.get("reasoning", "")

        logger.info(
            f"Intelligent resolution for task {task.task_id}:\n"
            f"Decision: {decision_str}\n"
            f"Reasoning: {reasoning[:200]}..."
        )

        # Cache the decision
        if self.reasoning_cache:
            self.reasoning_cache.set(
                prompt="intelligent_resolution_decision",
                context=cache_key_context,
                response=response
            )

        # Convert to enum
        try:
            decision = ResolutionDecision(decision_str.lower())
        except ValueError:
            logger.error(f"Invalid decision from LLM: {decision_str}. Defaulting to ESCALATE")
            decision = ResolutionDecision.ESCALATE

        # SAFETY CHECK: If LLM says ACCEPT but critical issues exist, override to ESCALATE
        if decision == ResolutionDecision.ACCEPT and audit_result.has_critical_issues():
            logger.warning(
                f"LLM decided ACCEPT despite critical issues. "
                f"Overriding to ESCALATE for human review."
            )
            decision = ResolutionDecision.ESCALATE

        # Store reasoning in task metadata for audit trail
        task.metadata["resolution_reasoning"] = reasoning
        task.metadata["resolution_confidence"] = response.get("confidence", "Unknown")

        return decision

    def _build_resolution_context(self, task: Task, audit_result: AuditResult) -> Dict[str, Any]:
        """Build context for resolution decision."""
        # Summarize task output (don't include full output to save tokens)
        output_summary = "Output produced successfully"
        if task.output_data and "result" in task.output_data:
            result = task.output_data["result"]
            if isinstance(result, dict):
                summary_fields = ["summary", "executive_summary", "conclusion"]
                for field in summary_fields:
                    if field in result and isinstance(result[field], str):
                        output_summary = result[field][:300]
                        break

        # Get case context if available
        case_priority = task.metadata.get("case_priority", "MEDIUM")
        case_question = task.metadata.get("case_question", "")

        # Get retry history
        retry_history = []
        if task.retry_count > 0:
            retry_history = task.metadata.get("retry_history", [])

        return {
            "task": {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "output_summary": output_summary,
            },
            "audit_result": {
                "status": audit_result.status.value,
                "summary": audit_result.summary,
                "issues": [
                    {
                        "category": issue.category,
                        "severity": issue.severity.value,
                        "description": issue.description,
                        "location": issue.location,
                        "suggested_fix": issue.suggested_fix,
                        "guideline_reference": issue.guideline_reference,
                    }
                    for issue in audit_result.issues
                ],
                "passed_checks": audit_result.passed_checks,
                "recommendations": audit_result.recommendations,
            },
            "case_context": {
                "priority": case_priority,
                "question": case_question,
            },
            "retry_history": retry_history,
        }

    def _build_resolution_prompt(self) -> str:
        """Build the reasoning prompt for intelligent resolution."""
        return """Analyze this audit result and determine the appropriate resolution decision.

AUDIT STATUS: {audit_result[status]}
ISSUES FOUND: {len(audit_result[issues])}
TASK RETRY COUNT: {task[retry_count]}/{task[max_retries]}
CASE PRIORITY: {case_context[priority]}

ISSUES DETAIL:
{audit_issues_json}

DECISION OPTIONS:
1. **ACCEPT** - Issues are acceptable given context OR task meets minimum requirements
2. **RETRY** - Issues can be fixed by worker; retry will add value
3. **ESCALATE** - Requires human expert judgment
4. **ABORT** - Unfixable or not worth retrying

YOUR ANALYSIS MUST CONSIDER:

**For EACH Issue:**
- Is it fixable on retry? (e.g., "missing field" YES, "no measured data available" NO)
- Does it truly block acceptance? (e.g., "missing CI" warning may be acceptable for preliminary analysis)
- What's the suggested fix? Is it actionable?

**Case Context:**
- Priority level: HIGH priority may warrant accepting with caveats; LOW priority can wait for perfection
- Time constraints: Is iterating worth the delay?

**Retry Value Assessment:**
- Will the worker actually be able to fix these issues given another attempt?
- Are corrections actionable? ("Add sources" YES, "Get primary data" NO if unavailable)
- Have we seen these same issues in retry history? (Pattern of unfixable issues)

**Partial Acceptance:**
- Can we accept with documented limitations/caveats instead of rejecting?
- Is "good enough for preliminary assessment" appropriate here?

REASONING REQUIREMENTS:
- Explain why each issue does or doesn't warrant rejection
- If RETRY: specify which issues are fixable and which corrections to prioritize
- If ESCALATE: explain what human judgment is needed
- If ACCEPT despite warnings: justify why warnings are acceptable in this context
- Express confidence in your decision

CLAUDE.MD COMPLIANCE:
- Do NOT accept fabricated data or evidence chain violations
- Do NOT downplay critical issues without strong justification
- Preserve uncertainty - if unsure, ESCALATE
- Default to skepticism: reject if quality insufficient

Return JSON:
{{
    "decision": "ACCEPT" | "RETRY" | "ESCALATE" | "ABORT",
    "reasoning": "Comprehensive explanation considering all issues and context",
    "issue_analysis": [
        {{
            "issue_category": "category_name",
            "severity": "critical/warning/info",
            "fixable_on_retry": true/false,
            "blocks_acceptance": true/false,
            "assessment": "Why this issue does/doesn't warrant rejection"
        }}
    ],
    "correction_strategy": {{
        "priority_fixes": ["List of fixes worker should prioritize"],
        "guidance_to_worker": "Specific guidance on what to change",
        "expected_outcome": "What we expect from retry"
    }},
    "confidence": "High/Moderate/Low - justification",
    "accept_with_caveats": null or {{"caveat": "Documented limitation if accepting despite issues"}},
    "limitations": ["Limitations of this decision"]
}}

IMPORTANT:
- RETRY only if worker can actually fix the issues
- ACCEPT with caveats is valid for preliminary work
- ESCALATE if uncertainty about quality is too high
- Do not waste retry cycles on unfixable issues
"""

    def _validate_resolution_response(self, response: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Validate that resolution response is valid."""
        decision = response.get("decision", "").upper()

        # Validate decision is valid
        valid_decisions = ["ACCEPT", "RETRY", "ESCALATE", "ABORT"]
        if decision not in valid_decisions:
            logger.error(f"Invalid decision from LLM: {decision}")
            return False

        # Validate reasoning provided
        reasoning = response.get("reasoning", "")
        if len(reasoning) < 100:
            logger.warning("Resolution reasoning is too brief (<100 chars)")
            return False

        # Validate issue analysis provided
        if "issue_analysis" not in response or len(response["issue_analysis"]) == 0:
            if len(context["audit_result"]["issues"]) > 0:
                logger.warning("Issues exist but no issue analysis provided")
                return False

        # If RETRY, must have correction strategy
        if decision == "RETRY":
            if "correction_strategy" not in response:
                logger.error("RETRY decision without correction_strategy")
                return False
            if not response["correction_strategy"].get("priority_fixes"):
                logger.error("RETRY decision without priority_fixes")
                return False

        return True
