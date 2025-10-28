#!/usr/bin/env python3
"""
Simple example demonstrating the Agent-Audit-Resolve pattern.
Uses stub implementations (no real LLM calls) to show the flow.
"""
import sys
from typing import Dict, Any

# Import core components
from models.task import Task, TaskType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine, ResolutionDecision
from agents.base_worker import BaseWorker
from agents.base_auditor import BaseAuditor


class SimpleWorker(BaseWorker):
    """Stub worker that simulates literature review (no real LLM)."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.attempt = 0

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute with stub implementation. First attempt fails audit, second passes."""
        self.attempt += 1
        has_corrections = len(input_data.get("corrections", [])) > 0

        print(f"\n[Worker] Attempt {self.attempt}: {input_data.get('query')}")
        if has_corrections:
            print(f"[Worker] Processing {len(input_data['corrections'])} corrections")

        # Return incomplete on first attempt, complete on retry
        return {
            "result": f"Analysis of {input_data.get('query')}",
            "summary": "Preliminary analysis completed",
            "methodology": "Literature review",
            "sources": ["Source A", "Source B"] if has_corrections else [],
            "limitations": ["Limited data"] if has_corrections else [],
            "confidence": "Moderate" if has_corrections else ""
        }


class SimpleAuditor(BaseAuditor):
    """Stub auditor that validates required fields (no real LLM)."""

    def __init__(self, agent_id: str):
        super().__init__(agent_id, enable_intelligent_audit=False)

    def _load_validation_criteria(self) -> Dict[str, Any]:
        return {"required_fields": ["summary", "methodology", "sources", "limitations", "confidence"]}

    def validate(self, task_input: Dict[str, Any], task_output: Dict[str, Any],
                 task_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate that all required fields are present and non-empty."""
        result = task_output.get("result", {})
        issues = []
        passed = []

        for field in self.validation_criteria["required_fields"]:
            if field in result and result[field]:
                passed.append(f"Has {field}")
            else:
                issues.append({
                    "category": "missing_field",
                    "severity": "warning",
                    "description": f"Missing required field: {field}",
                    "suggested_fix": f"Add {field} to output"
                })

        status = "passed" if len(issues) == 0 else "failed"
        print(f"[Auditor] {status.upper()}: {len(passed)} passed, {len(issues)} issues")

        return {
            "status": status,
            "summary": "All checks passed" if status == "passed" else f"{len(issues)} issues found",
            "passed_checks": passed,
            "failed_checks": [i["description"] for i in issues],
            "issues": issues,
            "recommendations": []
        }


def main():
    """Demonstrate Agent-Audit-Resolve pattern."""
    print("=" * 70)
    print("AGENT-AUDIT-RESOLVE PATTERN DEMO")
    print("=" * 70)

    # Step 1: Create engines (disable intelligent features to avoid LLM calls)
    print("\n[1] Creating engines...")
    task_executor = TaskExecutor(enable_intelligent_routing=False)
    audit_engine = AuditEngine()
    resolution_engine = ResolutionEngine(
        task_executor, audit_engine, max_retries=2, enable_intelligent_resolution=False
    )

    # Step 2: Register worker and auditor
    print("[2] Registering agents...")
    task_executor.register_worker(TaskType.LITERATURE_REVIEW, SimpleWorker("worker-01"))
    audit_engine.register_auditor(TaskType.LITERATURE_REVIEW, SimpleAuditor("auditor-01"))

    # Step 3: Create task
    print("[3] Creating task...")
    task = Task(
        task_type=TaskType.LITERATURE_REVIEW,
        input_data={"query": "What are the side effects of Drug X?", "context": {}}
    )
    print(f"    Task ID: {task.task_id}")
    print(f"    Query: {task.input_data['query']}")

    # Step 4: Execute with validation (handles Agent->Audit->Resolve loop automatically)
    print("\n[4] Executing Agent-Audit-Resolve loop...")
    print("-" * 70)
    decision, final_audit = resolution_engine.execute_with_validation(task)
    print("-" * 70)

    # Step 5: Show results
    print("\n[5] RESULTS:")
    print(f"    Decision: {decision.value.upper()}")
    print(f"    Status: {task.status.value.upper()}")
    print(f"    Attempts: {task.retry_count + 1}")
    print(f"    Final Audit: {final_audit.status.value.upper()}")

    if task.output_data and "result" in task.output_data:
        result = task.output_data["result"]
        print(f"\n    Output Summary: {result.get('summary', 'N/A')}")
        print(f"    Sources: {len(result.get('sources', []))}")
        print(f"    Confidence: {result.get('confidence', 'N/A')}")

    print("\n" + "=" * 70)
    if decision == ResolutionDecision.ACCEPT:
        print("SUCCESS: Task completed and passed validation!")
        print("=" * 70)
        return 0
    else:
        print(f"FAILED: Task ended with {decision.value}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
