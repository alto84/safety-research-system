# Contributing to Safety Research System

Thank you for your interest in contributing to the Safety Research System! This document provides guidelines and instructions for contributing to the project.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Areas for Contribution](#areas-for-contribution)

---

## Code of Conduct

This project adheres to a code of professional conduct. By participating, you are expected to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members
- Maintain confidentiality for sensitive pharmaceutical data

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)
- API keys for LLM providers (Claude or OpenAI)
- Basic understanding of:
  - Multi-agent systems
  - Pharmaceutical safety science
  - REST APIs

### Quick Start

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/safety-research-system.git
cd safety-research-system

# 3. Add upstream remote
git remote add upstream https://github.com/alto84/safety-research-system.git

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 5. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 6. Install pre-commit hooks
pre-commit install

# 7. Run tests to verify setup
pytest tests/ -v

# 8. Create a feature branch
git checkout -b feature/your-feature-name
```

---

## Development Setup

### Environment Configuration

Create a `.env` file in the project root:

```bash
# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-your-key
# OR
OPENAI_API_KEY=sk-your-key

# Database (for local development)
DATABASE_URL=sqlite:///./safety_research.db

# Optional: External APIs
PUBMED_API_KEY=your-pubmed-key
CLINICALTRIALS_API_KEY=your-key

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=safety_research.log

# Feature Flags
ENABLE_INTELLIGENT_ROUTING=true
ENABLE_INTELLIGENT_RESOLUTION=true
ENABLE_INTELLIGENT_COMPRESSION=true
ENABLE_INTELLIGENT_AUDIT=true
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Black Formatter
- isort
- GitLens

Workspace settings (`.vscode/settings.json`):

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false
}
```

#### PyCharm

1. Configure Python interpreter to use virtual environment
2. Enable Black formatter: Settings > Tools > Black
3. Enable pytest: Settings > Tools > Python Integrated Tools > Testing
4. Configure type checking: Settings > Editor > Inspections > Python > Type Checker

---

## Development Workflow

### Branching Strategy

We use **Git Flow**:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent production fixes
- `release/*`: Release preparation

### Feature Development Workflow

```bash
# 1. Sync with upstream
git checkout develop
git fetch upstream
git merge upstream/develop

# 2. Create feature branch
git checkout -b feature/intelligent-causality-assessment

# 3. Make changes and commit frequently
git add .
git commit -m "Add causality assessment framework"

# 4. Write tests
# Add tests in tests/ directory

# 5. Run tests and linting
pytest tests/ -v --cov
black .
isort .
flake8 .
mypy .

# 6. Push to your fork
git push origin feature/intelligent-causality-assessment

# 7. Create Pull Request on GitHub
```

### Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# Good commits
feat(agents): Add ADC-ILD specialized researcher agent
fix(audit): Correct PMID validation regex pattern
docs(api): Add examples for webhook integration
test(resolution): Add tests for intelligent resolution decisions

# Bad commits
fix: stuff
update files
WIP
```

### Code Review Process

1. **Self-Review**: Review your own code before requesting review
2. **Automated Checks**: Ensure all CI checks pass
3. **Peer Review**: At least one maintainer approval required
4. **Address Feedback**: Respond to all review comments
5. **Squash Commits**: Maintainers may squash commits before merge

---

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with these specific conventions:

#### General

- Line length: 100 characters (not 79)
- Use Black formatter (enforced)
- Use type hints for all function signatures
- Use docstrings (Google style) for all public functions

#### Naming Conventions

```python
# Classes: PascalCase
class LiteratureAgent:
    pass

# Functions/Methods: snake_case
def execute_task(task_id: str) -> Dict[str, Any]:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Enums: PascalCase for class, UPPER_SNAKE_CASE for members
class TaskStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

#### Type Hints

```python
from typing import Dict, List, Optional, Any, Union

# Always use type hints for function signatures
def process_case(
    case: Case,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """Process a safety research case.

    Args:
        case: The case to process
        timeout: Optional timeout in seconds

    Returns:
        Dictionary containing case results

    Raises:
        ValueError: If case is invalid
        TimeoutError: If processing exceeds timeout
    """
    pass

# Use TypedDict for structured dictionaries
from typing import TypedDict

class TaskOutput(TypedDict):
    result: Dict[str, Any]
    execution_time: float
    agent: str
```

#### Docstrings

Use Google-style docstrings:

```python
def execute_with_validation(
    self,
    task: Task,
    max_retries: int = 2
) -> Tuple[ResolutionDecision, Optional[AuditResult]]:
    """Execute a task with automatic validation and retry.

    This method implements the Task→Audit→Retry loop. It executes
    the task, validates the output, and retries with corrections
    if the audit fails.

    Args:
        task: Task to execute and validate
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple of (ResolutionDecision, final AuditResult)
        ResolutionDecision is one of: ACCEPT, RETRY, ESCALATE, ABORT

    Raises:
        ValueError: If task is invalid or malformed
        TimeoutError: If execution exceeds configured timeout
        Exception: If an unexpected error occurs during execution

    Example:
        ```python
        task = Task(task_type=TaskType.LITERATURE_REVIEW)
        decision, audit_result = engine.execute_with_validation(task)

        if decision == ResolutionDecision.ACCEPT:
            print(f"Task passed: {audit_result.summary}")
        ```

    Note:
        The retry loop is handled internally. The caller never needs
        to manage retries explicitly.
    """
    pass
```

### Error Handling

```python
# Use specific exceptions
from models.exceptions import (
    TaskExecutionError,
    AuditValidationError,
    ConfigurationError
)

# Don't catch generic exceptions unless necessary
try:
    result = execute_task(task)
except TaskExecutionError as e:
    logger.error(f"Task execution failed: {e}")
    raise
except Exception as e:
    # Only catch-all if truly unexpected
    logger.exception(f"Unexpected error: {e}")
    raise

# Always log exceptions
logger.exception("Error message", exc_info=True)

# Provide helpful error messages
raise ValueError(
    f"Invalid task type '{task.task_type}'. "
    f"Must be one of: {', '.join(TaskType.__members__.keys())}"
)
```

### Logging

```python
import logging

# Get logger at module level
logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical issues")

# Include context in log messages
logger.info(
    f"Task {task.task_id} completed successfully "
    f"in {execution_time:.2f}s by {agent_name}"
)

# Use structured logging for important events
logger.info(
    "Task completed",
    extra={
        "task_id": task.task_id,
        "execution_time": execution_time,
        "agent": agent_name,
        "retry_count": task.retry_count
    }
)
```

---

## Testing

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── test_task_executor.py
│   ├── test_audit_engine.py
│   └── test_resolution_engine.py
├── integration/             # Integration tests
│   ├── test_full_workflow.py
│   └── test_agent_orchestration.py
├── fixtures/                # Test fixtures and data
│   ├── sample_cases.json
│   └── mock_responses.py
└── conftest.py             # Pytest configuration
```

### Writing Tests

```python
import pytest
from models.task import Task, TaskType
from core.task_executor import TaskExecutor

class TestTaskExecutor:
    """Test suite for TaskExecutor."""

    @pytest.fixture
    def task_executor(self):
        """Create TaskExecutor instance for testing."""
        executor = TaskExecutor()
        # Register mock workers
        executor.register_worker(TaskType.LITERATURE_REVIEW, MockLiteratureAgent())
        return executor

    def test_execute_task_success(self, task_executor):
        """Test successful task execution."""
        task = Task(
            task_type=TaskType.LITERATURE_REVIEW,
            input_data={"query": "test query"}
        )

        output = task_executor.execute_task(task)

        assert output is not None
        assert "result" in output
        assert task.status == TaskStatus.COMPLETED

    def test_execute_task_invalid_type(self, task_executor):
        """Test that invalid task type raises ValueError."""
        task = Task(task_type="invalid_type")

        with pytest.raises(ValueError, match="No worker registered"):
            task_executor.execute_task(task)

    @pytest.mark.parametrize("task_type,expected_agent", [
        (TaskType.LITERATURE_REVIEW, "LiteratureAgent"),
        (TaskType.STATISTICAL_ANALYSIS, "StatisticsAgent"),
    ])
    def test_agent_routing(self, task_executor, task_type, expected_agent):
        """Test that tasks are routed to correct agents."""
        task = Task(task_type=task_type)
        task_executor.execute_task(task)
        assert task.assigned_agent == expected_agent
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_task_executor.py

# Run specific test
pytest tests/unit/test_task_executor.py::TestTaskExecutor::test_execute_task_success

# Run with verbose output
pytest -v

# Run only failed tests from last run
pytest --lf

# Run tests matching pattern
pytest -k "test_intelligent"

# Run with specific markers
pytest -m "slow"  # Only slow tests
pytest -m "not slow"  # Skip slow tests
```

### Test Markers

```python
import pytest

# Mark slow tests
@pytest.mark.slow
def test_full_integration():
    pass

# Mark tests requiring API keys
@pytest.mark.requires_api_key
def test_llm_integration():
    pass

# Skip conditionally
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="Requires Anthropic API key"
)
def test_claude_integration():
    pass
```

### Coverage Requirements

- Minimum coverage: 80% overall
- Critical paths (audit, resolution): 95%+
- All public APIs must have tests
- Edge cases and error paths must be tested

---

## Documentation

### Documentation Requirements

All contributions must include appropriate documentation:

1. **Code Documentation**:
   - Docstrings for all public functions/classes
   - Inline comments for complex logic
   - Type hints for all function signatures

2. **API Documentation**:
   - Update `API.md` for new endpoints
   - Include request/response examples
   - Document error codes

3. **User Documentation**:
   - Update `USER_GUIDE.md` for user-facing features
   - Add examples and screenshots
   - Update `FAQ.md` for common questions

4. **Developer Documentation**:
   - Update `ARCHITECTURE.md` for architectural changes
   - Update `AGENT_DEVELOPMENT.md` for new agent patterns
   - Add diagrams for complex interactions

### Building Documentation

```bash
# Generate API documentation
python -m pdoc --html --output-dir docs/ .

# Build Sphinx documentation (if configured)
cd docs/
make html
```

---

## Pull Request Process

### Before Submitting

1. **Code Quality**:
   - [ ] All tests pass
   - [ ] Code formatted with Black
   - [ ] Imports sorted with isort
   - [ ] No linting errors (flake8)
   - [ ] Type checking passes (mypy)
   - [ ] Coverage meets requirements

2. **Documentation**:
   - [ ] Docstrings added/updated
   - [ ] README updated if needed
   - [ ] CHANGELOG.md updated
   - [ ] Relevant docs updated

3. **Testing**:
   - [ ] Unit tests added
   - [ ] Integration tests added (if applicable)
   - [ ] Manual testing completed
   - [ ] Edge cases covered

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Use bullet points

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] All CI checks pass

## Screenshots (if applicable)

## Related Issues
Fixes #123
Related to #456
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer approval required
3. All review comments must be addressed
4. Final approval from project lead for major changes

### After Merge

1. Delete your feature branch
2. Sync your fork with upstream
3. Update local `develop` branch

---

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.9.7]
- Package version: [e.g., 1.0.0]

## Additional Context
Screenshots, logs, etc.
```

### Feature Requests

Use the feature request template:

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Who needs this and why?

## Proposed Solution
How should this work?

## Alternatives Considered
Other approaches considered

## Additional Context
Mockups, examples, etc.
```

---

## Areas for Contribution

### High-Priority Areas

1. **Specialized Agents**:
   - Oncology-specific agents
   - Cardiology-specific agents
   - Pediatric safety agents

2. **Data Source Connectors**:
   - ClinicalTrials.gov API
   - FDA FAERS database
   - EMA EudraVigilance

3. **Advanced Analytics**:
   - Causal inference algorithms
   - Bayesian network analysis
   - Time-series safety signal detection

4. **Visualization**:
   - Interactive dashboards
   - Network diagrams for drug-event relationships
   - Timeline visualizations

5. **Performance**:
   - Caching optimizations
   - Parallel task execution
   - Database query optimization

### Good First Issues

Look for issues tagged with:
- `good-first-issue`
- `help-wanted`
- `documentation`

### Advanced Contributions

For experienced contributors:
- Thought pipe architecture enhancements
- Multi-LLM ensemble reasoning
- Federated learning for safety signals
- Real-time event streaming

---

## Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md`
- Release notes
- Project README

Significant contributions may result in:
- Co-authorship on publications
- Conference presentations
- Maintainer status

---

## Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bug reports and feature requests
- **Email**: dev@safety-research-system.com
- **Slack**: Join our contributor Slack (request invite)

---

## License

By contributing, you agree that your contributions will be licensed under the project's license.

---

Thank you for contributing to the Safety Research System! Your efforts help improve pharmaceutical safety assessment worldwide.

**Last Updated**: November 1, 2025
