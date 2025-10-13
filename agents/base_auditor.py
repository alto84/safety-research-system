"""Base class for auditor agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging


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

    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        Initialize the auditor agent.

        Args:
            agent_id: Unique identifier for this agent instance
            config: Configuration dictionary for the agent
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.version = "1.0.0"
        self.validation_criteria = self._load_validation_criteria()
        logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id}")

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

        This is a critical check that all auditors should perform.

        Args:
            output: Worker output to check

        Returns:
            List of issues found (empty if compliant)
        """
        issues = []
        result = output.get("result", {})

        # Check for fabricated scores
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
                })

        # Check for banned language
        banned_phrases = [
            "exceptional performance",
            "outstanding",
            "world-class",
            "industry-leading",
            "a+" , "grade a",
        ]

        summary_text = output.get("result", {}).get("summary", "").lower()
        for phrase in banned_phrases:
            if phrase in summary_text:
                issues.append({
                    "category": "banned_language",
                    "severity": "critical",
                    "description": (
                        f"Output contains banned phrase '{phrase}' without extraordinary evidence. "
                        "CLAUDE.md prohibits this language without external validation."
                    ),
                    "location": "result.summary",
                    "suggested_fix": "Replace with evidence-based language like 'preliminary observation suggests'",
                    "guideline_reference": "CLAUDE.md: MANDATORY LANGUAGE RESTRICTIONS",
                })

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
            })

        return issues

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
