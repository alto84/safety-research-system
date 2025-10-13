"""Base class for worker agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging


logger = logging.getLogger(__name__)


class BaseWorker(ABC):
    """
    Abstract base class for all worker agents.

    Worker agents are responsible for executing specific tasks
    (e.g., literature review, statistical analysis, risk modeling).

    Each worker must implement the execute() method that:
    - Takes input data
    - Performs the analysis/work
    - Returns structured output

    Workers should be stateless and reusable.
    """

    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        Initialize the worker agent.

        Args:
            agent_id: Unique identifier for this agent instance
            config: Configuration dictionary for the agent
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.version = "1.0.0"
        logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id}")

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task assigned to this worker.

        Args:
            input_data: Dictionary containing:
                - query/question: The primary input
                - context: Additional context
                - data_sources: List of data sources to use
                - corrections: (optional) Corrections from previous audit
                - previous_output: (optional) Previous attempt output
                - audit_feedback: (optional) Feedback from auditor

        Returns:
            Dictionary containing:
                - result: Primary output/findings
                - confidence: Confidence level (if applicable)
                - sources: Sources used
                - methodology: Brief description of approach
                - limitations: Known limitations
                - metadata: Additional metadata

        Raises:
            ValueError: If input is invalid
            Exception: If execution fails
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")

        # Basic validation - can be overridden in subclasses
        required_fields = ["query", "context"]
        missing_fields = [field for field in required_fields if field not in input_data]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        return True

    def handle_corrections(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process corrections from audit feedback for retry attempts.

        This method should be called at the start of execute() when
        corrections are present in input_data.

        Args:
            input_data: Input data potentially containing corrections

        Returns:
            Modified input data with corrections integrated
        """
        if "corrections" not in input_data:
            return input_data

        corrections = input_data["corrections"]
        logger.info(f"{self.__class__.__name__}: Processing {len(corrections)} corrections")

        # Log the corrections for the agent to address
        for i, correction in enumerate(corrections):
            logger.info(
                f"  Correction {i+1}: [{correction.get('severity')}] "
                f"{correction.get('category')} - {correction.get('description')}"
            )

        return input_data

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this worker agent.

        Returns:
            Dictionary containing agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "version": self.version,
            "config": self.config,
        }
