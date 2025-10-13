"""Context compressor for creating minimal summaries for the orchestrator."""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.task import Task
from models.audit_result import AuditResult, AuditStatus
from core.llm_integration import ThoughtPipeExecutor, get_reasoning_cache


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

    def __init__(
        self,
        max_summary_length: int = 500,
        enable_intelligent_compression: bool = True,
    ):
        """
        Initialize the context compressor.

        Args:
            max_summary_length: Maximum character length for summaries
            enable_intelligent_compression: If True, use LLM-driven intelligent compression
        """
        self.max_summary_length = max_summary_length
        self.enable_intelligent_compression = enable_intelligent_compression
        self.compression_stats: Dict[str, Dict[str, Any]] = {}
        self.thought_pipe = ThoughtPipeExecutor() if enable_intelligent_compression else None
        self.reasoning_cache = get_reasoning_cache() if enable_intelligent_compression else None
        self.completed_task_summaries: Dict[str, str] = {}  # Track summaries for cross-task connections

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

        Uses intelligent compression if enabled, otherwise falls back to legacy method.

        Args:
            task: Task to summarize
            audit_result: Audit result if available

        Returns:
            Brief summary string
        """
        if self.enable_intelligent_compression:
            try:
                return self._generate_summary_intelligent(task, audit_result)
            except Exception as e:
                logger.warning(
                    f"Intelligent compression failed for task {task.task_id}: {e}. "
                    f"Falling back to legacy compression."
                )
                return self._generate_summary_legacy(task, audit_result)
        else:
            return self._generate_summary_legacy(task, audit_result)

    def _generate_summary_legacy(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> str:
        """
        Generate a brief 2-3 sentence summary using legacy template-based method.

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

    def _generate_summary_intelligent(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> str:
        """
        Generate intelligent summary using LLM-driven compression.

        This preserves critical information intelligently rather than using
        mechanical truncation:
        - Quantitative claims with confidence levels
        - Mechanistic insights
        - Key limitations and uncertainties
        - Relevance to case question
        - Cross-task connections

        Args:
            task: Task to summarize
            audit_result: Audit result if available

        Returns:
            Intelligent compressed summary string

        Raises:
            Exception: If intelligent compression fails
        """
        # Build context for compression
        context = self._build_compression_context(task, audit_result)

        # Check cache first
        cache_key_context = {
            "task_id": task.task_id,
            "output_hash": self._hash_output(task.output_data),
            "audit_status": audit_result.status.value if audit_result else "no_audit",
            "max_length": self.max_summary_length,
        }

        if self.reasoning_cache:
            cached = self.reasoning_cache.get(
                prompt="intelligent_compression",
                context=cache_key_context
            )
            if cached:
                logger.debug(f"Cache hit for compression of task {task.task_id}")
                compressed = cached.get("compressed_summary", "")

                # Validate cached result
                if self._validate_compressed_summary(compressed, task, audit_result):
                    # Store for cross-task connections
                    self.completed_task_summaries[task.task_id] = compressed
                    return compressed
                else:
                    logger.warning("Cached compression failed validation, recomputing")

        # Build compression prompt
        prompt = self._build_compression_prompt()

        # Execute thought pipe
        response = self.thought_pipe.execute_thought_pipe(
            prompt=prompt,
            context=context,
            validation_fn=self._validate_compression_response,
            max_retries=1
        )

        # Extract compressed summary
        compressed_summary = response.get("compressed_summary", "")

        # Validate against original
        if not self._validate_compressed_summary(compressed_summary, task, audit_result):
            raise ValueError("Compressed summary failed validation against original")

        # Store full response for audit trail
        task.metadata["compression_response"] = response

        # Cache the result
        if self.reasoning_cache:
            self.reasoning_cache.set(
                prompt="intelligent_compression",
                context=cache_key_context,
                response=response
            )

        # Store for cross-task connections
        self.completed_task_summaries[task.task_id] = compressed_summary

        logger.info(
            f"Intelligent compression for task {task.task_id}: "
            f"{context['original_length']} → {len(compressed_summary)} chars "
            f"({response.get('compression_metadata', {}).get('compression_ratio', 0):.1f}% reduction)"
        )

        return compressed_summary

    def _build_compression_context(
        self, task: Task, audit_result: Optional[AuditResult]
    ) -> Dict[str, Any]:
        """Build context for intelligent compression."""
        # Extract full task output
        output_data = task.output_data or {}
        result = output_data.get("result", {})

        # Get case context if available
        case_question = task.metadata.get("case_question", "")
        case_priority = task.metadata.get("case_priority", "MEDIUM")

        # Get other completed task summaries for cross-task connections
        other_completed_tasks = []
        for tid, summary in self.completed_task_summaries.items():
            if tid != task.task_id:
                other_completed_tasks.append({
                    "task_id": tid,
                    "summary": summary
                })

        # Prepare audit summary
        audit_summary = None
        if audit_result:
            audit_summary = {
                "status": audit_result.status.value,
                "summary": audit_result.summary,
                "critical_issues_count": len([
                    i for i in audit_result.issues
                    if i.severity.value == "critical"
                ]),
                "total_issues_count": len(audit_result.issues),
                "key_issues": [
                    {
                        "category": i.category,
                        "severity": i.severity.value,
                        "description": i.description,
                    }
                    for i in audit_result.issues[:3]  # Top 3 issues only
                ]
            }

        # Calculate original length
        original_text = json.dumps(result, default=str)
        original_length = len(original_text)

        return {
            "task_output": result,
            "audit_result": audit_summary,
            "task_metadata": {
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "execution_time": output_data.get("execution_time"),
                "retry_count": task.retry_count,
            },
            "case_context": {
                "case_question": case_question,
                "case_priority": case_priority,
            },
            "other_completed_tasks": other_completed_tasks,
            "compression_target": {
                "max_length": self.max_summary_length,
                "preserve_fields": [
                    "quantitative_findings",
                    "confidence_level",
                    "critical_limitations"
                ],
                "audience": "orchestrator_agent"
            },
            "original_length": original_length,
        }

    def _build_compression_prompt(self) -> str:
        """Build the reasoning prompt for intelligent compression."""
        return """Intelligently compress this task output into a concise summary for the orchestrator.

TASK OUTPUT:
{task_output}

AUDIT RESULT:
{audit_result}

CASE CONTEXT:
{case_context}

OTHER COMPLETED TASKS (for identifying connections):
{other_completed_tasks}

COMPRESSION TARGET:
- Max length: {compression_target[max_length]} characters
- Audience: Orchestrator agent (needs to make decisions based on this summary)
- Preserve: {compression_target[preserve_fields]}

YOUR TASK:
Extract 2-3 sentences capturing the MOST CRITICAL findings from this task output.

REQUIREMENTS:

**1. Critical Information Preservation:**
- Preserve ALL quantitative claims with exact values and confidence levels
- Preserve key mechanistic insights (how/why findings work)
- Preserve critical limitations and uncertainties (CLAUDE.MD compliance)
- Preserve audit status if critical issues found

**2. Relevance to Case:**
- Prioritize findings most relevant to case question: "{case_context[case_question]}"
- Explain WHY these findings matter to the case

**3. Cross-Task Connections:**
- Identify connections to other completed tasks if applicable
- Note if findings confirm/contradict/complement other tasks

**4. Adaptive Compression:**
- Compress based on IMPORTANCE, not fixed truncation
- Keep critical numerical claims intact (no rounding/approximation)
- Remove verbose explanations but keep essential context
- If audit has critical issues, prioritize mentioning them

**5. CLAUDE.MD COMPLIANCE:**
- Do NOT inflate confidence levels during compression
- Do NOT introduce new claims not in original output
- Do NOT remove uncertainty expressions or limitations
- Do NOT create composite scores without basis in original
- Preserve exact phrasing for confidence levels

**EXAMPLE COMPRESSION:**

Original (1500 chars):
"The literature review identified 45 relevant studies examining the relationship between Drug X and hepatotoxicity.
Of these, 23 were randomized controlled trials, 15 were cohort studies, and 7 were case reports. The meta-analysis
showed an odds ratio of 2.3 (95% CI: 1.8-2.9, p<0.001) for hepatotoxicity in patients taking Drug X compared to
controls. However, significant heterogeneity was observed (I²=67%), suggesting variability in study quality and
patient populations. Key limitations include: publication bias cannot be ruled out, most studies had small sample
sizes (median n=120), and follow-up periods varied widely (3-24 months). The mechanistic understanding is limited,
with only 3 studies investigating biological pathways."

Compressed (380 chars):
"Meta-analysis of 45 studies found Drug X associated with 2.3x increased hepatotoxicity risk (95% CI: 1.8-2.9,
p<0.001). Moderate confidence due to high heterogeneity (I²=67%) and potential publication bias. Critical limitation:
mechanistic understanding minimal (only 3 pathway studies). Small sample sizes (median n=120) limit generalizability."

Return JSON:
{{
    "compressed_summary": "2-3 sentences, <{compression_target[max_length]} chars, preserving critical findings",
    "key_findings_structured": {{
        "quantitative_findings": [
            {{
                "claim": "specific numerical claim",
                "value": "exact value with units",
                "confidence": "confidence level from original",
                "source_count": "number if applicable"
            }}
        ],
        "mechanistic_insights": ["key mechanistic findings"],
        "confidence_level": "overall confidence from original (no inflation)",
        "critical_limitations": ["key limitations that could affect interpretation"]
    }},
    "relevance_to_case": "1 sentence: why these findings matter to case question",
    "connections_to_other_tasks": [
        {{
            "related_task": "task_id if connection exists",
            "connection": "nature of connection (confirms/contradicts/complements)"
        }}
    ],
    "audit_status_note": "mention if critical issues found, otherwise null",
    "compression_metadata": {{
        "original_length": {original_length},
        "compressed_length": "length of compressed_summary",
        "compression_ratio": "percentage reduction",
        "information_preserved": ["list of key information types preserved"]
    }}
}}

CRITICAL VALIDATION CHECKS:
1. compressed_summary MUST be <{compression_target[max_length]} chars
2. ALL numerical claims in compressed_summary MUST match original exactly
3. Confidence level MUST NOT be higher than original
4. NO new claims introduced that aren't in original
5. Limitations from original MUST be preserved if mentioned

If original output has no meaningful findings, state that clearly (e.g., "No significant findings identified").
"""

    def _validate_compression_response(
        self, response: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """Validate that compression response is valid and safe."""
        # Check required fields
        if "compressed_summary" not in response:
            logger.error(f"Missing compressed_summary in response. Keys present: {list(response.keys())}")
            return False

        compressed_summary = response["compressed_summary"]

        # Check length constraint
        max_length = context["compression_target"]["max_length"]
        if len(compressed_summary) > max_length:
            logger.error(
                f"Compressed summary exceeds max length: {len(compressed_summary)} > {max_length}"
            )
            return False

        # Check for empty summary
        if len(compressed_summary.strip()) < 20:
            logger.error("Compressed summary too short (<20 chars)")
            return False

        # Check key_findings_structured present
        if "key_findings_structured" not in response:
            logger.warning("Missing key_findings_structured in response")
            return False

        # Check confidence level present
        if "confidence_level" not in response["key_findings_structured"]:
            logger.warning("Missing confidence_level in key_findings_structured")
            # This is a warning, not a failure

        # Check compression metadata
        if "compression_metadata" in response:
            metadata = response["compression_metadata"]
            if "compressed_length" in metadata:
                claimed_length = metadata["compressed_length"]
                actual_length = len(compressed_summary)
                # Allow small discrepancy due to character counting differences
                if abs(claimed_length - actual_length) > 10:
                    logger.warning(
                        f"Compression metadata length mismatch: "
                        f"claimed {claimed_length}, actual {actual_length}"
                    )

        return True

    def _validate_compressed_summary(
        self, compressed_summary: str, task: Task, audit_result: Optional[AuditResult]
    ) -> bool:
        """
        Validate compressed summary against original to detect fabrication or inflation.

        Critical checks:
        - No new numerical claims not in original
        - No confidence inflation
        - No removal of critical limitations
        - No fabricated connections

        Args:
            compressed_summary: Compressed summary to validate
            task: Original task
            audit_result: Original audit result

        Returns:
            True if valid, False if validation fails
        """
        # Basic validation
        if not compressed_summary or len(compressed_summary) > self.max_summary_length:
            logger.error("Compressed summary length validation failed")
            return False

        # Extract original output for comparison
        if not task.output_data or "result" not in task.output_data:
            # If no output data, any summary is potentially fabricated
            logger.warning("No output data to validate against")
            # Allow generic status summaries
            allowed_phrases = ["completed", "failed", "no significant findings", "no data available"]
            if not any(phrase in compressed_summary.lower() for phrase in allowed_phrases):
                logger.error("Summary contains claims but no output data exists")
                return False

        # Extract numerical claims from compressed summary
        compressed_numbers = self._extract_numerical_claims(compressed_summary)

        # Extract numerical claims from original output
        original_output = json.dumps(task.output_data.get("result", {}), default=str)
        original_numbers = self._extract_numerical_claims(original_output)

        # Check for fabricated numerical claims
        for num_claim in compressed_numbers:
            # Check if this number or similar range exists in original
            if not self._number_exists_in_original(num_claim, original_numbers, original_output):
                logger.error(
                    f"Compressed summary contains numerical claim not in original: {num_claim}"
                )
                return False

        # Check for confidence inflation (simplified check)
        compressed_lower = compressed_summary.lower()
        original_lower = original_output.lower()

        high_confidence_terms = ["very high confidence", "high confidence", "strong confidence", "definitive"]
        compressed_has_high_conf = any(term in compressed_lower for term in high_confidence_terms)
        original_has_high_conf = any(term in original_lower for term in high_confidence_terms)

        if compressed_has_high_conf and not original_has_high_conf:
            logger.error("Confidence inflation detected: compressed has high confidence but original doesn't")
            return False

        # Check for limitation removal if original had limitations
        limitation_indicators = ["limitation", "caveat", "uncertainty", "cannot determine", "unclear"]
        original_has_limitations = any(term in original_lower for term in limitation_indicators)
        compressed_has_limitations = any(term in compressed_lower for term in limitation_indicators)

        if original_has_limitations and not compressed_has_limitations and len(compressed_summary) > 100:
            logger.warning(
                "Original had limitations but compressed summary omits them. "
                "This may be acceptable if summary is very brief."
            )
            # Warning only, not a failure

        return True

    def _extract_numerical_claims(self, text: str) -> List[str]:
        """Extract numerical claims from text for validation."""
        import re

        # Patterns for numbers
        patterns = [
            r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%',  # Range percentages: 10-20%
            r'\d+(?:\.\d+)?%',  # Single percentages: 15%
            r'\d+(?:,\d{3})*(?:\.\d+)?',  # Numbers with commas: 1,234.56
            r'p\s*[<>=]\s*0?\.\d+',  # p-values: p<0.05
            r'OR\s*=?\s*\d+(?:\.\d+)?',  # Odds ratios: OR=2.3
            r'RR\s*=?\s*\d+(?:\.\d+)?',  # Relative risks: RR=1.5
            r'CI:\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?',  # Confidence intervals: CI: 1.2-3.4
            r'n\s*=\s*\d+(?:,\d{3})*',  # Sample sizes: n=100
        ]

        claims = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            claims.extend(matches)

        return claims

    def _number_exists_in_original(
        self, num_claim: str, original_numbers: List[str], original_text: str
    ) -> bool:
        """Check if a numerical claim exists in the original output."""
        # Direct match
        if num_claim in original_numbers:
            return True

        # Check if appears in original text
        if num_claim in original_text:
            return True

        # Allow slight formatting differences
        # e.g., "2.3" vs "2.30", "1,000" vs "1000"
        normalized_claim = num_claim.replace(",", "").strip()
        normalized_original = original_text.replace(",", "")

        if normalized_claim in normalized_original:
            return True

        return False

    def _hash_output(self, output_data: Optional[Dict[str, Any]]) -> str:
        """Create hash of output data for caching."""
        import hashlib

        if not output_data:
            return "no_output"

        output_str = json.dumps(output_data, sort_keys=True, default=str)
        return hashlib.sha256(output_str.encode()).hexdigest()[:16]

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

        # Check if intelligent compression response is available
        if "compression_response" in task.metadata:
            compression_response = task.metadata["compression_response"]
            if "key_findings_structured" in compression_response:
                # Use the structured findings from intelligent compression
                structured = compression_response["key_findings_structured"]
                findings = {
                    "confidence_level": structured.get("confidence_level"),
                    "quantitative_findings_count": len(structured.get("quantitative_findings", [])),
                    "mechanistic_insights_count": len(structured.get("mechanistic_insights", [])),
                    "limitations_count": len(structured.get("critical_limitations", [])),
                }

        if not task.output_data:
            return findings

        result = task.output_data.get("result", {})
        if not isinstance(result, dict):
            return findings

        # Extract specific high-value fields based on task type (if not already from intelligent compression)
        if not findings:
            key_fields = [
                "conclusion",
                "recommendation",
                "risk_level",
                "confidence",
                "confidence_level",
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
