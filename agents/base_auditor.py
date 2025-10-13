"""Base class for auditor agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import re
import json


logger = logging.getLogger(__name__)


class BaseAuditor(ABC):
    """
    Abstract base class for all auditor agents.

    Auditor agents are responsible for validating worker outputs
    against quality standards, guidelines, and regulations.

    Each auditor must implement the validate() method that:
    - Takes worker input and output
    - Checks against validation criteria
    - Returns structured audit result with issues and recommendations

    Auditors enforce guidelines from CLAUDE.md and other standards.
    """

    def __init__(self, agent_id: str, config: Dict[str, Any] = None, enable_intelligent_audit: bool = False):
        """
        Initialize the auditor agent.

        Args:
            agent_id: Unique identifier for this agent instance
            config: Configuration dictionary for the agent
            enable_intelligent_audit: Enable LLM-based semantic violation detection
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.version = "1.0.0"
        self.enable_intelligent_audit = enable_intelligent_audit
        self.validation_criteria = self._load_validation_criteria()

        # Initialize thought pipe executor if intelligent audit enabled
        self.thought_pipe_executor = None
        if self.enable_intelligent_audit:
            try:
                from core.llm_integration import ThoughtPipeExecutor
                self.thought_pipe_executor = ThoughtPipeExecutor()
                logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id} (intelligent audit ENABLED)")
            except ImportError as e:
                logger.warning(f"Failed to import ThoughtPipeExecutor: {e}. Intelligent audit disabled.")
                self.enable_intelligent_audit = False
        else:
            logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id} (intelligent audit disabled)")

    @abstractmethod
    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate worker output against quality standards.

        Args:
            task_input: Original input given to the worker
            task_output: Output produced by the worker
            task_metadata: Additional task metadata

        Returns:
            Dictionary containing:
                - status: "passed", "failed", "partial", or "escalated"
                - summary: Brief summary of audit findings
                - passed_checks: List of validation checks that passed
                - failed_checks: List of validation checks that failed
                - issues: List of issue dictionaries with:
                    - category: Issue category
                    - severity: "critical", "warning", or "info"
                    - description: What's wrong
                    - location: Where in output (optional)
                    - suggested_fix: How to fix (optional)
                    - guideline_reference: Which guideline violated (optional)
                - recommendations: List of improvement recommendations
                - score: Optional numerical score (use cautiously!)

        Raises:
            ValueError: If input is invalid
            Exception: If validation fails
        """
        pass

    @abstractmethod
    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria specific to this auditor type.

        Returns:
            Dictionary of validation criteria
        """
        pass

    def check_anti_fabrication_compliance(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check compliance with CLAUDE.md anti-fabrication protocols.

        HYBRID APPROACH:
        1. ALWAYS run hard-coded checks first (safety-critical, cannot be bypassed)
        2. If intelligent audit enabled, add LLM semantic analysis layer
        3. LLM CANNOT override hard-coded safety violations

        This is a critical check that all auditors should perform.

        Args:
            output: Worker output to check

        Returns:
            List of issues found (empty if compliant)
        """
        issues = []

        # ===== LAYER 1: HARD-CODED SAFETY CHECKS (ALWAYS RUN) =====
        # These are objective, safety-critical checks that CANNOT be bypassed

        # Check 1: Score fabrication (SAFETY CRITICAL)
        score_issues = self._check_score_fabrication(output)
        issues.extend(score_issues)

        # Check 2: Banned phrase keyword matching (first pass)
        banned_phrase_issues = self._check_banned_phrases_keyword(output)
        issues.extend(banned_phrase_issues)

        # Check 3: Basic structure checks
        structure_issues = self._check_basic_structure(output)
        issues.extend(structure_issues)

        # ===== LAYER 2: INTELLIGENT SEMANTIC ANALYSIS (IF ENABLED) =====
        # LLM catches semantic violations missed by keywords
        # IMPORTANT: LLM additions are EXTRA layer, NOT replacement
        if self.enable_intelligent_audit and self.thought_pipe_executor:
            try:
                semantic_issues = self._check_semantic_violations(output, issues)
                issues.extend(semantic_issues)
                logger.info(f"Intelligent audit completed: found {len(semantic_issues)} additional semantic issues")
            except Exception as e:
                logger.warning(f"Intelligent audit failed: {e}. Continuing with hard-coded checks only.")
                # Continue with hard-coded results - LLM failure is non-fatal

        return issues

    def _check_score_fabrication(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        SAFETY CRITICAL: Check for fabricated scores.

        This check CANNOT be overridden by LLM reasoning.

        Args:
            output: Worker output to check

        Returns:
            List of score fabrication issues
        """
        issues = []
        result = output.get("result", {})

        if "score" in result:
            score = result.get("score")
            if isinstance(score, (int, float)) and score > 80:
                issues.append({
                    "category": "score_fabrication",
                    "severity": "critical",
                    "description": (
                        f"Score of {score} exceeds 80% without external validation data. "
                        "CLAUDE.md prohibits scores above 80% without external validation."
                    ),
                    "location": "result.score",
                    "suggested_fix": "Remove score or provide external validation data source",
                    "guideline_reference": "CLAUDE.md: MANDATORY ANTI-FABRICATION PROTOCOLS",
                    "hard_coded": True,  # Mark as hard-coded safety check
                })

        return issues

    def _check_banned_phrases_keyword(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for banned language using keyword matching (first pass).

        This provides fast, objective detection of explicit violations.
        LLM semantic layer will catch conceptual violations.

        Args:
            output: Worker output to check

        Returns:
            List of banned language issues
        """
        issues = []
        result = output.get("result", {})

        # Banned phrases - exact keyword matching
        banned_phrases = [
            "exceptional performance",
            "outstanding",
            "world-class",
            "industry-leading",
            "a+", "grade a",
            "best in class",
            "superior to all",
        ]

        # Check all text fields
        text_fields = ["summary", "executive_summary", "conclusion"]
        for field in text_fields:
            if field in result:
                text = str(result[field]).lower()
                for phrase in banned_phrases:
                    if phrase in text:
                        issues.append({
                            "category": "banned_language",
                            "severity": "critical",
                            "description": (
                                f"Output contains banned phrase '{phrase}' without extraordinary evidence. "
                                "CLAUDE.md prohibits this language without external validation."
                            ),
                            "location": f"result.{field}",
                            "suggested_fix": "Replace with evidence-based language like 'preliminary observation suggests'",
                            "guideline_reference": "CLAUDE.md: MANDATORY LANGUAGE RESTRICTIONS",
                            "hard_coded": True,
                        })

        return issues

    def _check_basic_structure(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for basic required structures (confidence, limitations, evidence).

        Args:
            output: Worker output to check

        Returns:
            List of structural issues
        """
        issues = []
        result = output.get("result", {})

        # Check for confidence/uncertainty expression
        if "confidence" not in result and "limitations" not in result:
            issues.append({
                "category": "missing_uncertainty",
                "severity": "warning",
                "description": (
                    "Output lacks confidence level or limitations section. "
                    "CLAUDE.md requires explicit uncertainty expression."
                ),
                "location": "result",
                "suggested_fix": "Add 'confidence' and 'limitations' fields",
                "guideline_reference": "CLAUDE.md: UNCERTAINTY EXPRESSION",
                "hard_coded": True,
            })

        # Check for evidence chain
        if "sources" not in result and "methodology" not in result:
            issues.append({
                "category": "missing_evidence",
                "severity": "critical",
                "description": (
                    "Output lacks evidence chain (sources or methodology). "
                    "CLAUDE.md requires measurement data or methodology for any claim."
                ),
                "location": "result",
                "suggested_fix": "Add 'sources' or 'methodology' with specific evidence",
                "guideline_reference": "CLAUDE.md: EVIDENCE CHAIN",
                "hard_coded": True,
            })

        return issues

    def _check_semantic_violations(
        self,
        output: Dict[str, Any],
        hard_coded_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to detect semantic violations missed by keyword matching.

        This catches:
        - Conceptual banned language (e.g., "this drug is the best available")
        - Evidence-claim linkage issues (claims without specific source refs)
        - Unjustified confidence levels
        - Assumption-based quality claims

        IMPORTANT: This CANNOT override hard-coded safety checks.

        Args:
            output: Worker output to check
            hard_coded_issues: Issues already found by hard-coded checks

        Returns:
            List of additional semantic issues found by LLM
        """
        if not self.thought_pipe_executor:
            return []

        # Load CLAUDE.md guidelines for context
        claude_md_guidelines = self._load_claude_md_guidelines()

        # Build context for LLM
        context = {
            "output": output,
            "hard_coded_violations": [
                {
                    "category": issue["category"],
                    "severity": issue["severity"],
                    "description": issue["description"]
                }
                for issue in hard_coded_issues
            ],
            "claude_md_guidelines": claude_md_guidelines,
        }

        # Build prompt for semantic analysis
        prompt = self._build_semantic_audit_prompt()

        try:
            # Execute thought pipe
            result = self.thought_pipe_executor.execute_thought_pipe(
                prompt=prompt,
                context=context,
                validation_fn=self._validate_semantic_audit_response,
                max_retries=1
            )

            # Convert LLM response to issue format
            issues = self._convert_semantic_violations_to_issues(result)

            return issues

        except Exception as e:
            logger.error(f"Semantic violation check failed: {e}")
            return []

    def _build_semantic_audit_prompt(self) -> str:
        """Build prompt for LLM semantic audit."""
        return """You are a safety auditor for a pharmaceutical research system. Your task is to detect SEMANTIC violations of CLAUDE.md guidelines that keyword matching might miss.

Analyze the worker output for:

1. **Semantic Banned Language**: Concepts that violate CLAUDE.md even without exact keywords
   - Example: "this drug is the best available" = banned (implies "industry-leading")
   - Example: "demonstrates superior efficacy to all alternatives" = banned
   - Example: "clearly the optimal choice" = banned

2. **Evidence-Claim Linkage**: Do numerical/mechanistic claims actually link to specific sources?
   - Don't just check if sources exist - verify each claim traces to a source
   - Example VIOLATION: "15.4% ILD incidence" but no source reference for this number
   - Example GOOD: "15.4% ILD incidence (DESTINY-Lung01, NCT03505710)"

3. **Confidence Justification**: Is confidence level justified by evidence quality?
   - Check if "High confidence" is backed by multiple high-quality sources
   - Check if evidence quality matches claimed confidence
   - Example VIOLATION: "High confidence" but only 1 source cited

4. **Assumption-Based Quality Claims**: Are quality assessments based on measurement or assumption?
   - Example VIOLATION: "This appears to be high-quality data"
   - Example GOOD: "Study scored 8/10 on Newcastle-Ottawa Scale"

Return your analysis as JSON:

```json
{
    "semantic_violations": [
        {
            "type": "banned_concept|evidence_linkage|confidence_mismatch|quality_assumption",
            "text": "exact text from output",
            "reason": "why this violates CLAUDE.md",
            "severity": "critical|warning",
            "location": "where in output"
        }
    ],
    "evidence_linkage_issues": [
        {
            "claim": "the specific claim",
            "issue": "what's wrong",
            "severity": "critical|warning"
        }
    ],
    "confidence_assessment": {
        "claimed_confidence": "what output claims",
        "justified": true/false,
        "reason": "why confidence is/isn't justified"
    },
    "overall_assessment": "brief summary"
}
```

CRITICAL CONSTRAINTS:
- You CANNOT override hard-coded safety violations already detected
- Focus on SEMANTIC issues not caught by keyword matching
- Be specific: cite exact text and explain why it violates CLAUDE.md
- Default to skepticism: if uncertain whether something violates, flag it
"""

    def _validate_semantic_audit_response(
        self,
        response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """
        Validate LLM semantic audit response.

        Args:
            response: LLM response to validate
            context: Original context

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ["semantic_violations", "overall_assessment"]
        for field in required_fields:
            if field not in response:
                logger.warning(f"Semantic audit response missing required field: {field}")
                return False

        # Validate semantic_violations structure
        violations = response.get("semantic_violations", [])
        if not isinstance(violations, list):
            logger.warning("semantic_violations must be a list")
            return False

        for violation in violations:
            if not isinstance(violation, dict):
                return False
            required_violation_fields = ["type", "reason", "severity"]
            for field in required_violation_fields:
                if field not in violation:
                    logger.warning(f"Violation missing required field: {field}")
                    return False

        return True

    def _convert_semantic_violations_to_issues(
        self,
        semantic_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert LLM semantic analysis to standard issue format.

        Args:
            semantic_result: LLM semantic audit response

        Returns:
            List of issues in standard format
        """
        issues = []

        # Convert semantic violations
        for violation in semantic_result.get("semantic_violations", []):
            issues.append({
                "category": f"semantic_{violation['type']}",
                "severity": violation["severity"],
                "description": (
                    f"Semantic violation detected: {violation['reason']}\n"
                    f"Text: '{violation.get('text', 'N/A')[:100]}...'"
                ),
                "location": violation.get("location", "unknown"),
                "suggested_fix": "Revise to comply with CLAUDE.md guidelines",
                "guideline_reference": "CLAUDE.md: Semantic analysis",
                "hard_coded": False,  # Mark as LLM-detected
            })

        # Convert evidence linkage issues
        for issue in semantic_result.get("evidence_linkage_issues", []):
            issues.append({
                "category": "semantic_evidence_linkage",
                "severity": issue.get("severity", "warning"),
                "description": (
                    f"Evidence linkage issue: {issue['issue']}\n"
                    f"Claim: '{issue.get('claim', 'N/A')[:100]}...'"
                ),
                "location": "result",
                "suggested_fix": "Link each claim to specific source reference",
                "guideline_reference": "CLAUDE.md: EVIDENCE CHAIN",
                "hard_coded": False,
            })

        # Convert confidence assessment
        confidence_assessment = semantic_result.get("confidence_assessment", {})
        if not confidence_assessment.get("justified", True):
            issues.append({
                "category": "semantic_confidence_mismatch",
                "severity": "warning",
                "description": (
                    f"Confidence level not justified: {confidence_assessment.get('reason', 'N/A')}\n"
                    f"Claimed: {confidence_assessment.get('claimed_confidence', 'unknown')}"
                ),
                "location": "result.confidence",
                "suggested_fix": "Adjust confidence level to match evidence quality",
                "guideline_reference": "CLAUDE.md: UNCERTAINTY EXPRESSION",
                "hard_coded": False,
            })

        return issues

    def _load_claude_md_guidelines(self) -> Dict[str, Any]:
        """
        Load CLAUDE.md guidelines for LLM context.

        Returns:
            Dictionary of key CLAUDE.md guidelines
        """
        return {
            "banned_phrases": [
                "exceptional performance",
                "outstanding",
                "world-class",
                "industry-leading",
                "best in class",
                "superior to all",
            ],
            "banned_concepts": [
                "Claiming superiority without comparative data",
                "Quality assessment without measurement",
                "High confidence without multiple sources",
                "Numerical claims without source attribution",
            ],
            "score_threshold": 80,
            "evidence_requirements": [
                "Every numerical claim must link to specific source",
                "Confidence must match evidence quality",
                "No assumption-based quality claims",
                "Primary sources only - no AI outputs as evidence",
            ],
            "required_elements": [
                "Explicit confidence level",
                "Limitations section",
                "Source attribution for claims",
                "Uncertainty expression",
            ],
        }

    def check_completeness(self, output: Dict[str, Any], required_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Check if output contains all required fields.

        Args:
            output: Worker output to check
            required_fields: List of required field names

        Returns:
            List of issues for missing fields
        """
        issues = []
        result = output.get("result", {})

        for field in required_fields:
            if field not in result:
                issues.append({
                    "category": "missing_field",
                    "severity": "warning",
                    "description": f"Required field '{field}' is missing from output",
                    "location": "result",
                    "suggested_fix": f"Add '{field}' field to output",
                })

        return issues

    def check_evidence_provenance(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check evidence provenance tracking for all claims.

        This validates that numerical and mechanistic claims have proper
        source attribution with URLs or citations.

        Args:
            output: Worker output to check

        Returns:
            List of issues found (empty if compliant)
        """
        issues = []
        result = output.get("result", {})

        # Check for evidence_claims if using new structured format
        if "evidence_claims" in result:
            evidence_claims = result.get("evidence_claims", [])

            for i, claim in enumerate(evidence_claims):
                # Each claim must have sources
                sources = claim.get("sources", [])
                if not sources or len(sources) == 0:
                    issues.append({
                        "category": "missing_evidence_source",
                        "severity": "critical",
                        "description": (
                            f"Evidence claim {i+1} lacks source attribution. "
                            f"Claim: '{claim.get('claim_text', 'UNKNOWN')[:100]}...'. "
                            "CLAUDE.md requires every claim to trace to its source."
                        ),
                        "location": f"evidence_claims[{i}]",
                        "suggested_fix": "Add source with url OR (title + authors + date)",
                        "guideline_reference": "CLAUDE.md: EVIDENCE CHAIN",
                    })
                    continue

                # Check each source has minimum required info
                for j, source in enumerate(sources):
                    has_url = source.get("url") is not None and source.get("url").strip() != ""
                    has_citation = all([
                        source.get("title"),
                        source.get("authors"),
                        source.get("date")
                    ])

                    if not (has_url or has_citation):
                        issues.append({
                            "category": "incomplete_source",
                            "severity": "critical",
                            "description": (
                                f"Source {j+1} for claim {i+1} incomplete. "
                                "Must have url OR (title + authors + date)."
                            ),
                            "location": f"evidence_claims[{i}].sources[{j}]",
                            "suggested_fix": "Add url or complete citation information",
                            "guideline_reference": "CLAUDE.md: EVIDENCE CHAIN",
                        })

                    # Numerical claims must have URL for verification
                    if claim.get("claim_type") == "numerical":
                        if not has_url:
                            issues.append({
                                "category": "numerical_claim_missing_url",
                                "severity": "critical",
                                "description": (
                                    f"Numerical claim {i+1} source {j+1} missing URL. "
                                    "Numerical claims require verifiable URLs."
                                ),
                                "location": f"evidence_claims[{i}].sources[{j}]",
                                "suggested_fix": "Add source URL for numerical claim verification",
                                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
                            })

        # Legacy format: Check for numerical claims in text without sources
        # Look for patterns like "10-15%", "X%", numbers
        summary_text = str(result.get("summary", "")) + str(result.get("executive_summary", ""))
        key_findings = result.get("key_findings", [])
        if isinstance(key_findings, dict):
            key_findings = [str(v) for v in key_findings.values()]
        elif isinstance(key_findings, list):
            key_findings = [str(f) for f in key_findings]

        all_text = summary_text + " ".join(key_findings)

        # Find numerical patterns
        numerical_patterns = [
            r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%',  # Range percentages like "10-15%"
            r'\d+(?:\.\d+)?%',  # Single percentages like "15%"
            r'\d+(?:,\d{3})*(?:\.\d+)?\s*(?:patients?|subjects?|cases?)',  # Patient counts
        ]

        numerical_claims_found = []
        for pattern in numerical_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            numerical_claims_found.extend(matches)

        # If numerical claims found but no evidence_claims structure, flag it
        if numerical_claims_found and "evidence_claims" not in result:
            issues.append({
                "category": "unsourced_numerical_claims",
                "severity": "critical",
                "description": (
                    f"Found {len(set(numerical_claims_found))} numerical claims "
                    f"(e.g., {', '.join(list(set(numerical_claims_found))[:3])}) "
                    "without structured evidence provenance. "
                    "All numerical claims must link to specific sources."
                ),
                "location": "result",
                "suggested_fix": (
                    "Add 'evidence_claims' field with EvidenceClaim objects, "
                    "each linking numerical data to source URLs"
                ),
                "guideline_reference": "CLAUDE.md: EVIDENCE CHAIN",
            })

        return issues

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this auditor agent.

        Returns:
            Dictionary containing agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "version": self.version,
            "config": self.config,
            "validation_criteria": self.validation_criteria,
        }
