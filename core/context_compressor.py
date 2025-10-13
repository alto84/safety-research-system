"""Context compressor for creating minimal summaries for the orchestrator."""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from models.task import Task
from models.audit_result import AuditResult, AuditStatus


logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Compresses task results into minimal summaries for the orchestrator.

    This prevents context overload by ensuring the orchestrator only receives:
    - Task completion status
    - Brief summary (2-3 sentences)
    - Key metadata (execution time, confidence level, etc.)
    - References to full results for drill-down if needed

    The orchestrator never sees full worker outputs.
    """

    def __init__(self, max_summary_length: int = 500):
        """
        Initialize the context compressor.

        Args:
            max_summary_length: Maximum character length for summaries
        """
        self.max_summary_length = max_summary_length
        self.compression_stats: Dict[str, Dict[str, Any]] = {}

    def compress_task_result(
        self,
        task: Task,
        audit_result: Optional[AuditResult] = None,
    ) -> Dict[str, Any]:
        """
        Compress a task result into a minimal summary.

        Args:
            task: Completed task
            audit_result: Final audit result (if available)

        Returns:
            Compressed summary dictionary
        """
        logger.debug(f"Compressing result for task {task.task_id}")

        # Calculate compression stats
        original_size = self._estimate_size(task.output_data) if task.output_data else 0

        # Build compressed summary
        compressed = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "summary": self._generate_summary(task, audit_result),
            "key_findings": self._extract_key_findings(task, audit_result),
            "metadata": self._compress_metadata(task, audit_result),
            "compressed_at": datetime.utcnow().isoformat(),
        }

        compressed_size = self._estimate_size(compressed)
        compression_ratio = (
            (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        )

        # Store compression stats
        self.compression_stats[task.task_id] = {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
        }

        logger.info(
            f"Compressed task {task.task_id}: {original_size} → {compressed_size} bytes "
            f"({compression_ratio:.1f}% reduction)"
        )

        return compressed

    def _generate_summary(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> str:
        """
        Generate a brief 2-3 sentence summary.

        Args:
            task: Task to summarize
            audit_result: Audit result if available

        Returns:
            Brief summary string
        """
        summary_parts = []

        # Task completion statement
        if task.status.value == "completed":
            summary_parts.append(f"{task.task_type.value.replace('_', ' ').title()} completed successfully.")
        else:
            summary_parts.append(f"{task.task_type.value.replace('_', ' ').title()} ended with status: {task.status.value}.")

        # Add key finding from output if available
        if task.output_data and "result" in task.output_data:
            result = task.output_data["result"]
            if isinstance(result, dict):
                # Try to extract a key finding
                for key in ["conclusion", "summary", "key_finding", "primary_result"]:
                    if key in result:
                        finding = result[key]
                        if isinstance(finding, str):
                            summary_parts.append(finding[:200])  # Limit length
                        break

        # Add audit status if available
        if audit_result:
            if audit_result.status == AuditStatus.PASSED:
                summary_parts.append("Validation passed.")
            else:
                summary_parts.append(
                    f"Validation {audit_result.status.value} with {len(audit_result.issues)} issues."
                )

        # Join and truncate if needed
        full_summary = " ".join(summary_parts)
        if len(full_summary) > self.max_summary_length:
            full_summary = full_summary[:self.max_summary_length - 3] + "..."

        return full_summary

    def _extract_key_findings(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> Dict[str, Any]:
        """
        Extract only the most important findings.

        Args:
            task: Task to extract from
            audit_result: Audit result if available

        Returns:
            Dictionary of key findings
        """
        findings = {}

        if not task.output_data:
            return findings

        result = task.output_data.get("result", {})
        if not isinstance(result, dict):
            return findings

        # Extract specific high-value fields based on task type
        key_fields = [
            "conclusion",
            "recommendation",
            "risk_level",
            "confidence",
            "sample_size",
            "p_value",
            "effect_size",
            "causality_assessment",
            "source_count",
            "evidence_level",
        ]

        for field in key_fields:
            if field in result:
                findings[field] = result[field]

        # Add audit quality indicator
        if audit_result:
            findings["validation_status"] = audit_result.status.value
            findings["issues_count"] = len(audit_result.issues)

        return findings

    def _compress_metadata(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> Dict[str, Any]:
        """
        Compress metadata to only essential fields.

        Args:
            task: Task
            audit_result: Audit result if available

        Returns:
            Compressed metadata dictionary
        """
        metadata = {
            "execution_time": task.output_data.get("execution_time") if task.output_data else None,
            "retry_count": task.retry_count,
            "agent": task.assigned_agent,
        }

        # Add audit metadata if available
        if audit_result:
            metadata["audit_id"] = audit_result.audit_id
            metadata["auditor"] = audit_result.auditor_agent

        # Add escalation flag if needed
        if task.metadata.get("requires_human_review"):
            metadata["requires_human_review"] = True
            metadata["escalation_reason"] = task.metadata.get("escalation_reason")

        return metadata

    def _estimate_size(self, obj: Any) -> int:
        """
        Estimate size of an object in bytes (rough approximation).

        Args:
            obj: Object to estimate

        Returns:
            Approximate size in bytes
        """
        import sys
        import json

        try:
            # For dict/list, use JSON serialization length
            if isinstance(obj, (dict, list)):
                return len(json.dumps(obj, default=str))
            # For other objects, use sys.getsizeof
            return sys.getsizeof(obj)
        except:
            return 0

    def get_compression_stats(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compression statistics for a task.

        Args:
            task_id: Task ID

        Returns:
            Compression statistics or None
        """
        return self.compression_stats.get(task_id)

    def get_average_compression_ratio(self) -> float:
        """
        Get average compression ratio across all compressed tasks.

        Returns:
            Average compression ratio percentage
        """
        if not self.compression_stats:
            return 0.0

        ratios = [
            stats["compression_ratio"]
            for stats in self.compression_stats.values()
            if stats["compression_ratio"] > 0
        ]

        return sum(ratios) / len(ratios) if ratios else 0.0
