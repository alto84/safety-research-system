# Agent Development Guide

This guide explains how to create custom worker agents and auditor agents for the Safety Research System.

---

## Table of Contents

- [Overview](#overview)
- [Worker Agent Development](#worker-agent-development)
- [Auditor Agent Development](#auditor-agent-development)
- [Agent Registration](#agent-registration)
- [Testing Agents](#testing-agents)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

The Safety Research System uses two types of agents:

1. **Worker Agents**: Perform specific tasks (e.g., literature review, statistical analysis)
2. **Auditor Agents**: Validate worker outputs against quality standards

All agents follow abstract base classes that define their interface.

---

## Worker Agent Development

### 1. Create Worker Agent Class

Create a new file in `/agents/workers/`:

```python
"""Custom agent for <task description>."""
from typing import Dict, Any
import logging

from agents.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class MyCustomWorker(BaseWorker):
    """
    Worker agent for <specific task>.

    This agent performs <task description> by <methodology>.
    """

    def __init__(self, agent_id: str = "my_custom_worker", config: Dict[str, Any] = None):
        """Initialize the custom worker agent."""
        super().__init__(agent_id, config)
        self.version = "1.0.0"

        # Initialize any agent-specific resources
        self.data_connector = self._initialize_data_connector()

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the custom task.

        Args:
            input_data: Dictionary containing:
                - query: The primary question/task
                - context: Additional context
                - corrections: (optional) Corrections from previous audit
                - previous_output: (optional) Previous attempt output
                - audit_feedback: (optional) Feedback from auditor

        Returns:
            Dictionary containing:
                - summary: Brief summary of findings
                - result: Detailed results
                - sources: List of sources used
                - confidence: Confidence level
                - limitations: Known limitations
                - methodology: Description of approach
                - metadata: Additional metadata
        """
        # Validate input
        self.validate_input(input_data)

        # Handle corrections from retry
        input_data = self.handle_corrections(input_data)

        # Extract input parameters
        query = input_data.get("query", "")
        context = input_data.get("context", {})

        logger.info(f"{self.agent_id}: Executing task for query: {query[:50]}...")

        try:
            # Step 1: Data collection
            data = self._collect_data(query, context)

            # Step 2: Analysis
            analysis = self._analyze_data(data, context)

            # Step 3: Synthesis
            results = self._synthesize_results(analysis)

            # Build output
            output = {
                "summary": self._generate_summary(results),
                "result": results,
                "sources": self._extract_sources(data),
                "confidence": self._assess_confidence(results),
                "limitations": self._identify_limitations(results),
                "methodology": self._describe_methodology(),
                "metadata": {
                    "data_points_analyzed": len(data),
                    "agent_version": self.version,
                }
            }

            logger.info(f"{self.agent_id}: Task completed successfully")
            return output

        except Exception as e:
            logger.error(f"{self.agent_id}: Task execution failed: {str(e)}")
            raise

    def _collect_data(self, query: str, context: Dict[str, Any]) -> list:
        """Collect data for analysis."""
        # Implement data collection logic
        # Example: Query external APIs, databases, etc.
        pass

    def _analyze_data(self, data: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collected data."""
        # Implement analysis logic
        pass

    def _synthesize_results(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize analysis into structured results."""
        # Implement synthesis logic
        pass

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate concise summary of results."""
        # Return 2-3 sentence summary
        pass

    def _extract_sources(self, data: list) -> list:
        """Extract source references."""
        # Return list of source dictionaries
        pass

    def _assess_confidence(self, results: Dict[str, Any]) -> str:
        """Assess confidence level in results."""
        # Return: "Low", "Moderate", "High" with justification
        pass

    def _identify_limitations(self, results: Dict[str, Any]) -> list:
        """Identify limitations of the analysis."""
        # Return list of limitation strings
        pass

    def _describe_methodology(self) -> str:
        """Describe the methodology used."""
        # Return methodology description
        pass

    def _initialize_data_connector(self):
        """Initialize data connector if needed."""
        # Return connector instance or None
        pass
```

### 2. Key Worker Methods

**Required Methods**:
- `execute(input_data)`: Main execution method
- `validate_input(input_data)`: Input validation (inherited, can override)
- `handle_corrections(input_data)`: Process audit corrections (inherited)

**Output Structure**:

```python
{
    "summary": "2-3 sentence summary",
    "result": {
        # Structured results
        "key_finding_1": "...",
        "key_finding_2": "...",
    },
    "sources": [
        {
            "title": "Source title",
            "authors": "Author A, Author B",
            "year": 2024,
            "pmid": "12345678",
            "url": "https://..."
        }
    ],
    "confidence": "Moderate - based on X studies, limited by Y",
    "limitations": [
        "Limitation 1",
        "Limitation 2"
    ],
    "methodology": "Methodology description",
    "metadata": {
        # Additional metadata
    }
}
```

### 3. Handling Retries

When a task is retried after audit failure:

```python
def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    # Handle corrections from previous audit
    input_data = self.handle_corrections(input_data)

    # Check if this is a retry
    if "corrections" in input_data:
        corrections = input_data["corrections"]
        previous_output = input_data.get("previous_output", {})
        audit_feedback = input_data.get("audit_feedback", "")

        # Log corrections
        logger.info(f"Processing {len(corrections)} corrections from audit")

        # Address each correction
        for correction in corrections:
            if correction["category"] == "missing_sources":
                # Add more sources
                pass
            elif correction["category"] == "missing_confidence_interval":
                # Add confidence intervals
                pass

    # Continue with normal execution
    # ...
```

---

## Auditor Agent Development

### 1. Create Auditor Agent Class

Create a new file in `/agents/auditors/`:

```python
"""Custom auditor for validating <worker type> outputs."""
from typing import Dict, Any, List
import logging
import os

from agents.base_auditor import BaseAuditor

logger = logging.getLogger(__name__)


class MyCustomAuditor(BaseAuditor):
    """
    Auditor agent for validating <worker type> outputs.

    This auditor checks for:
    - Required fields completeness
    - Data quality standards
    - CLAUDE.md anti-fabrication compliance
    - Domain-specific validation criteria
    """

    def __init__(
        self,
        agent_id: str = "my_custom_auditor",
        config: Dict[str, Any] = None,
        enable_intelligent_audit: bool = False
    ):
        """Initialize the custom auditor agent."""
        super().__init__(agent_id, config, enable_intelligent_audit)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """Load validation criteria for this auditor."""
        # Load from file or define inline
        return {
            "required_fields": [
                "summary",
                "result",
                "sources",
                "confidence",
                "limitations",
                "methodology"
            ],
            "minimum_sources": 3,
            "required_confidence_expression": True,
            "banned_phrases": [
                # Add domain-specific banned phrases
            ]
        }

    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate worker output against quality standards.

        Args:
            task_input: Original input to the worker
            task_output: Output produced by the worker
            task_metadata: Additional task metadata

        Returns:
            Audit result dictionary with status and issues
        """
        logger.info(f"{self.agent_id}: Starting validation")

        issues = []
        passed_checks = []
        failed_checks = []

        # 1. CLAUDE.md anti-fabrication compliance (ALWAYS RUN)
        claude_issues = self.check_anti_fabrication_compliance(task_output)
        issues.extend(claude_issues)

        if not claude_issues:
            passed_checks.append("CLAUDE.md anti-fabrication compliance")
        else:
            failed_checks.append("CLAUDE.md anti-fabrication compliance")

        # 2. Completeness check
        completeness_issues = self.check_completeness(
            task_output,
            self.validation_criteria["required_fields"]
        )
        issues.extend(completeness_issues)

        if not completeness_issues:
            passed_checks.append("Required fields completeness")
        else:
            failed_checks.append("Required fields completeness")

        # 3. Evidence provenance
        provenance_issues = self.check_evidence_provenance(task_output)
        issues.extend(provenance_issues)

        if not provenance_issues:
            passed_checks.append("Evidence provenance tracking")
        else:
            failed_checks.append("Evidence provenance tracking")

        # 4. Domain-specific validation
        domain_issues = self._validate_domain_specific(task_output)
        issues.extend(domain_issues)

        if not domain_issues:
            passed_checks.append("Domain-specific validation")
        else:
            failed_checks.append("Domain-specific validation")

        # Determine overall status
        critical_issues = [i for i in issues if i.get("severity") == "critical"]

        if critical_issues:
            status = "failed"
            summary = f"Validation failed with {len(critical_issues)} critical issues"
        elif issues:
            status = "partial"
            summary = f"Validation passed with {len(issues)} warnings"
        else:
            status = "passed"
            summary = "All validation checks passed"

        # Build result
        result = {
            "status": status,
            "summary": summary,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "issues": issues,
            "recommendations": self._generate_recommendations(issues),
        }

        logger.info(f"{self.agent_id}: Validation complete - {status}")
        return result

    def _validate_domain_specific(self, output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform domain-specific validation."""
        issues = []
        result = output.get("result", {})

        # Example: Check minimum source count
        sources = result.get("sources", [])
        min_sources = self.validation_criteria.get("minimum_sources", 0)

        if len(sources) < min_sources:
            issues.append({
                "category": "insufficient_sources",
                "severity": "warning",
                "description": (
                    f"Only {len(sources)} sources provided, "
                    f"minimum {min_sources} recommended for this task type"
                ),
                "location": "result.sources",
                "suggested_fix": f"Add at least {min_sources - len(sources)} more sources",
            })

        # Add more domain-specific checks
        # ...

        return issues

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues found."""
        recommendations = []

        if any(i["category"] == "insufficient_sources" for i in issues):
            recommendations.append(
                "Expand literature search to include more sources"
            )

        if any(i["category"] == "missing_confidence_interval" for i in issues):
            recommendations.append(
                "Add confidence intervals to all quantitative claims"
            )

        return recommendations
```

### 2. Validation Checklist

Create a validation checklist in `/guidelines/audit_checklists/`:

```markdown
# My Custom Auditor Validation Checklist

## Required Fields
- [ ] summary
- [ ] result
- [ ] sources
- [ ] confidence
- [ ] limitations
- [ ] methodology

## Quality Standards
- [ ] Minimum 3 sources
- [ ] Confidence level expressed with justification
- [ ] Limitations clearly stated
- [ ] No fabricated data (CLAUDE.md compliance)

## Domain-Specific
- [ ] <domain-specific check 1>
- [ ] <domain-specific check 2>
```

---

## Agent Registration

### 1. Register Worker Agent

```python
from models.task import TaskType
from core.task_executor import TaskExecutor
from agents.workers.my_custom_worker import MyCustomWorker

# Initialize task executor
task_executor = TaskExecutor()

# Register worker
worker = MyCustomWorker(agent_id="custom_worker_001")
task_executor.register_worker(TaskType.MY_CUSTOM_TASK, worker)
```

### 2. Register Auditor Agent

```python
from models.task import TaskType
from core.audit_engine import AuditEngine
from agents.auditors.my_custom_auditor import MyCustomAuditor

# Initialize audit engine
audit_engine = AuditEngine()

# Register auditor
auditor = MyCustomAuditor(
    agent_id="custom_auditor_001",
    enable_intelligent_audit=True  # Enable LLM semantic analysis
)
audit_engine.register_auditor(TaskType.MY_CUSTOM_TASK, auditor)
```

### 3. Add Task Type

Update `/models/task.py`:

```python
class TaskType(Enum):
    """Types of tasks that can be assigned to agents."""
    LITERATURE_REVIEW = "literature_review"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    MY_CUSTOM_TASK = "my_custom_task"  # Add your task type
```

---

## Testing Agents

### Unit Tests

```python
import pytest
from agents.workers.my_custom_worker import MyCustomWorker

class TestMyCustomWorker:
    """Test suite for MyCustomWorker."""

    @pytest.fixture
    def worker(self):
        """Create worker instance for testing."""
        return MyCustomWorker()

    def test_execute_success(self, worker):
        """Test successful execution."""
        input_data = {
            "query": "test query",
            "context": {"param": "value"}
        }

        output = worker.execute(input_data)

        assert "summary" in output
        assert "result" in output
        assert "confidence" in output
        assert isinstance(output["sources"], list)

    def test_execute_with_corrections(self, worker):
        """Test execution with audit corrections."""
        input_data = {
            "query": "test query",
            "corrections": [
                {
                    "category": "missing_sources",
                    "severity": "warning",
                    "description": "Add more sources"
                }
            ],
            "previous_output": {"result": "previous result"}
        }

        output = worker.execute(input_data)

        assert "result" in output
        # Verify corrections were addressed
```

### Integration Tests

```python
from models.task import Task, TaskType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine

def test_full_workflow():
    """Test full workflow with custom agents."""
    # Setup
    task_executor = TaskExecutor()
    audit_engine = AuditEngine()

    task_executor.register_worker(TaskType.MY_CUSTOM_TASK, MyCustomWorker())
    audit_engine.register_auditor(TaskType.MY_CUSTOM_TASK, MyCustomAuditor())

    resolution_engine = ResolutionEngine(task_executor, audit_engine)

    # Create task
    task = Task(
        task_type=TaskType.MY_CUSTOM_TASK,
        input_data={"query": "test query"}
    )

    # Execute with validation
    decision, audit_result = resolution_engine.execute_with_validation(task)

    # Verify
    assert decision == ResolutionDecision.ACCEPT
    assert audit_result.status == AuditStatus.PASSED
```

---

## Best Practices

### Worker Agents

1. **Idempotency**: Agents should produce same output for same input
2. **Error Handling**: Catch and log errors, provide helpful messages
3. **Retry Support**: Handle corrections gracefully in retry attempts
4. **Resource Cleanup**: Clean up connections, files, etc.
5. **Logging**: Log important steps and decisions
6. **Configuration**: Use config dict for customization
7. **Versioning**: Track agent version in metadata

### Auditor Agents

1. **Comprehensive Checks**: Check all aspects of output quality
2. **Specific Issues**: Provide detailed issue descriptions
3. **Actionable Fixes**: Suggest specific corrections
4. **Severity Levels**: Use appropriate severity (critical/warning/info)
5. **No False Positives**: Ensure checks are accurate
6. **CLAUDE.md Compliance**: Always check anti-fabrication protocols
7. **Intelligent Audit**: Enable semantic analysis for complex violations

### General

1. **Documentation**: Write clear docstrings
2. **Type Hints**: Use type hints for all signatures
3. **Testing**: Write comprehensive unit and integration tests
4. **Performance**: Optimize for speed and efficiency
5. **Monitoring**: Log metrics for monitoring
6. **Backwards Compatibility**: Maintain compatibility with existing code

---

## Examples

See the following production agents for reference:

- **Worker Agents**:
  - `/agents/workers/literature_agent.py`: Literature review agent
  - `/agents/workers/adc_ild_researcher.py`: Specialized domain agent
  - `/agents/workers/statistics_agent.py`: Statistical analysis agent

- **Auditor Agents**:
  - `/agents/auditors/literature_auditor.py`: Literature validation
  - `/agents/auditors/statistics_auditor.py`: Statistics validation

---

## Support

For questions about agent development:
- **GitHub Discussions**: Ask questions
- **CONTRIBUTING.md**: General contribution guidelines
- **ARCHITECTURE.md**: System architecture details

---

**Last Updated**: November 1, 2025
