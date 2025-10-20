"""
Base class for all skills in the Safety Research System.

Skills are modular, composable units that perform specific tasks. They can be:
- Deterministic (100% code-based, no LLM)
- Hybrid (mix of code and LLM reasoning)
- LLM-driven (primarily LLM-based with validation)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillType(Enum):
    """Types of skills based on implementation approach."""
    DETERMINISTIC = "deterministic"  # 100% code-based, no LLM
    HYBRID = "hybrid"  # Mix of code and LLM
    LLM = "llm"  # Primarily LLM-driven


class SkillCategory(Enum):
    """Skill categories for organization."""
    LITERATURE = "literature"
    STATISTICS = "statistics"
    AUDIT = "audit"
    RESOLUTION = "resolution"
    COMPRESSION = "compression"


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    name: str
    version: str
    category: SkillCategory
    skill_type: SkillType
    description: str
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SkillInput:
    """Defines an input parameter for a skill."""
    name: str
    type_hint: str  # e.g., "List[Dict]", "str", "int"
    description: str
    required: bool = True
    default: Any = None


@dataclass
class SkillOutput:
    """Defines an output from a skill."""
    name: str
    type_hint: str
    description: str
    schema: Optional[Dict[str, Any]] = None


@dataclass
class SkillExecutionResult:
    """Result of skill execution."""
    skill_name: str
    success: bool
    output: Dict[str, Any]
    execution_time_ms: float
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    """
    Abstract base class for all skills.

    All skills must implement:
    - execute(): Main execution method
    - validate_inputs(): Input validation
    - get_metadata(): Skill metadata
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize skill.

        Args:
            config_path: Optional path to skill configuration file
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}
        self.metadata = self.get_metadata()
        self.execution_count = 0
        self.total_execution_time_ms = 0.0

    def _load_config(self) -> Dict[str, Any]:
        """Load skill configuration from YAML."""
        if not self.config_path or not self.config_path.exists():
            return {}

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill with given inputs.

        Args:
            inputs: Input parameters for the skill

        Returns:
            Output dictionary with results

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If execution fails
        """
        pass

    @abstractmethod
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate input parameters.

        Args:
            inputs: Input parameters to validate

        Returns:
            True if inputs are valid

        Raises:
            ValueError: If inputs are invalid with specific error message
        """
        pass

    @abstractmethod
    def get_metadata(self) -> SkillMetadata:
        """
        Get skill metadata.

        Returns:
            SkillMetadata object with skill information
        """
        pass

    def execute_with_validation(self, inputs: Dict[str, Any]) -> SkillExecutionResult:
        """
        Execute skill with input validation and timing.

        Args:
            inputs: Input parameters

        Returns:
            SkillExecutionResult with execution details
        """
        import time

        start_time = time.time()

        try:
            # Validate inputs
            self.validate_inputs(inputs)

            # Execute
            output = self.execute(inputs)

            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000

            # Update stats
            self.execution_count += 1
            self.total_execution_time_ms += execution_time_ms

            return SkillExecutionResult(
                skill_name=self.metadata.name,
                success=True,
                output=output,
                execution_time_ms=execution_time_ms,
                metadata={
                    "version": self.metadata.version,
                    "category": self.metadata.category.value,
                    "type": self.metadata.skill_type.value,
                    "execution_count": self.execution_count,
                    "avg_execution_time_ms": self.total_execution_time_ms / self.execution_count,
                }
            )

        except ValueError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Skill {self.metadata.name} input validation failed: {e}")
            return SkillExecutionResult(
                skill_name=self.metadata.name,
                success=False,
                output={},
                execution_time_ms=execution_time_ms,
                error=f"Input validation failed: {str(e)}",
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Skill {self.metadata.name} execution failed: {e}", exc_info=True)
            return SkillExecutionResult(
                skill_name=self.metadata.name,
                success=False,
                output={},
                execution_time_ms=execution_time_ms,
                error=f"Execution failed: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """
        Get skill schema (inputs, outputs, configuration).

        Returns:
            Schema dictionary
        """
        return {
            "metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "category": self.metadata.category.value,
                "type": self.metadata.skill_type.value,
                "description": self.metadata.description,
            },
            "inputs": self._get_input_schema(),
            "outputs": self._get_output_schema(),
            "configuration": self.config,
        }

    @abstractmethod
    def _get_input_schema(self) -> List[SkillInput]:
        """Return list of input parameters with types and descriptions."""
        pass

    @abstractmethod
    def _get_output_schema(self) -> List[SkillOutput]:
        """Return list of output parameters with types and descriptions."""
        pass

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<{self.__class__.__name__} "
            f"name={self.metadata.name} "
            f"version={self.metadata.version} "
            f"type={self.metadata.skill_type.value}>"
        )


class DeterministicSkill(BaseSkill):
    """
    Base class for deterministic skills (100% code-based, no LLM).

    Deterministic skills:
    - Always produce same output for same input
    - No LLM calls
    - Can be cached aggressively
    - Fast execution (typically <500ms)
    - Highly testable
    """

    def get_metadata(self) -> SkillMetadata:
        """Override to set skill type to DETERMINISTIC."""
        metadata = self._get_metadata()
        metadata.skill_type = SkillType.DETERMINISTIC
        return metadata

    @abstractmethod
    def _get_metadata(self) -> SkillMetadata:
        """Subclasses implement this instead of get_metadata()."""
        pass


class HybridSkill(BaseSkill):
    """
    Base class for hybrid skills (mix of code and LLM).

    Hybrid skills:
    - Deterministic code for structure and validation
    - LLM calls for reasoning/semantic analysis
    - Moderate caching (cache LLM responses)
    - Moderate execution time (1-5 seconds)
    - Validation of LLM outputs
    """

    def __init__(self, config_path: Optional[Path] = None, thought_pipe_executor=None):
        """
        Initialize hybrid skill.

        Args:
            config_path: Optional path to skill configuration
            thought_pipe_executor: LLM execution engine
        """
        super().__init__(config_path)
        self.thought_pipe = thought_pipe_executor

    def get_metadata(self) -> SkillMetadata:
        """Override to set skill type to HYBRID."""
        metadata = self._get_metadata()
        metadata.skill_type = SkillType.HYBRID
        return metadata

    @abstractmethod
    def _get_metadata(self) -> SkillMetadata:
        """Subclasses implement this instead of get_metadata()."""
        pass


class LLMSkill(BaseSkill):
    """
    Base class for LLM-driven skills (primarily LLM-based).

    LLM skills:
    - Primarily LLM reasoning
    - Code for input/output validation only
    - Limited caching (temperature > 0 often)
    - Longer execution time (2-10 seconds)
    - Validation of LLM outputs critical
    """

    def __init__(self, config_path: Optional[Path] = None, thought_pipe_executor=None):
        """
        Initialize LLM skill.

        Args:
            config_path: Optional path to skill configuration
            thought_pipe_executor: LLM execution engine
        """
        super().__init__(config_path)
        self.thought_pipe = thought_pipe_executor

        if not self.thought_pipe:
            logger.warning(f"LLM skill {self.__class__.__name__} initialized without thought_pipe_executor")

    def get_metadata(self) -> SkillMetadata:
        """Override to set skill type to LLM."""
        metadata = self._get_metadata()
        metadata.skill_type = SkillType.LLM
        return metadata

    @abstractmethod
    def _get_metadata(self) -> SkillMetadata:
        """Subclasses implement this instead of get_metadata()."""
        pass
