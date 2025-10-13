# Safety Research System

A multi-agent research system with audit validation for pharmaceutical safety assessment. This system implements a novel **Agent→Audit→Resolve** pattern to ensure quality and compliance while preventing orchestrator context overload.

## Overview

The Safety Research System helps safety knowledge groups conduct evidence-based safety assessments by:

1. **Decomposing complex safety questions** into manageable subtasks
2. **Executing tasks with specialized worker agents** (literature review, statistical analysis, etc.)
3. **Validating outputs with dedicated audit agents** that enforce quality standards and CLAUDE.md guidelines
4. **Automatically retrying with corrections** when validation fails
5. **Compressing results** to prevent orchestrator context overload
6. **Synthesizing final reports** from validated findings

## Key Features

### 🔄 Agent-Audit-Resolve Loop
Each task goes through an automatic validation cycle:
- Worker agent executes task
- Audit agent validates output against quality standards
- If validation fails: corrections provided, worker retries
- If validation passes: results compressed and passed to orchestrator
- Orchestrator only sees minimal summaries, not full outputs

### 🛡️ CLAUDE.md Compliance
Built-in enforcement of anti-fabrication protocols:
- No score fabrication without measurement data
- Mandatory evidence chains
- Required uncertainty expression
- Banned language detection
- Statistical rigor validation

### 📊 Context Compression
Prevents orchestrator overload by:
- Compressing task outputs to 2-3 sentence summaries
- Extracting only key findings
- Providing metadata references for drill-down
- Typical compression ratios: 80-95%

### 🔍 Quality Assurance
Multiple validation layers:
- Completeness checks
- Evidence quality verification
- Assumption validation
- Uncertainty quantification
- Regulatory alignment

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                         │
│  (Receives only compressed summaries, no full outputs)  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ├─> Creates Tasks
                  │
                  v
┌─────────────────────────────────────────────────────────┐
│               RESOLUTION ENGINE                         │
│         (Manages Worker→Audit→Retry Loop)              │
└─────┬───────────────────────────────────────────────────┘
      │
      ├─> Task Executor ──> Worker Agent (Literature, Stats, etc.)
      │                            │
      │                            v
      │                     Produces Output
      │                            │
      │                            v
      ├─> Audit Engine ──> Audit Agent (Validates Output)
      │                            │
      │                            v
      │                    Pass or Fail?
      │                            │
      │                   ┌────────┴────────┐
      │                   │                 │
      │                 FAIL              PASS
      │                   │                 │
      │            Provide Corrections      │
      │                   │                 │
      │                   v                 v
      │            Retry Worker      Context Compressor
      │                   │                 │
      │                   └─────────────────┘
      │                            │
      │                            v
      └──────────> Compressed Summary to Orchestrator
```

## Directory Structure

```
safety-research-system/
├── agents/
│   ├── base_worker.py          # Abstract base for worker agents
│   ├── base_auditor.py         # Abstract base for auditor agents
│   ├── orchestrator.py         # Main orchestration logic
│   ├── workers/
│   │   ├── literature_agent.py
│   │   └── statistics_agent.py
│   └── auditors/
│       ├── literature_auditor.py
│       └── statistics_auditor.py
├── core/
│   ├── task_executor.py        # Manages worker execution
│   ├── audit_engine.py         # Manages audit validation
│   ├── resolution_engine.py    # Worker→Audit→Retry loop
│   └── context_compressor.py   # Result compression
├── models/
│   ├── task.py                 # Task data model
│   ├── audit_result.py         # Audit result model
│   └── case.py                 # Case data model
├── guidelines/
│   └── audit_checklists/       # Validation criteria
│       ├── literature_review_checklist.md
│       └── statistics_checklist.md
├── config/                     # Configuration files
├── tests/                      # Unit tests
├── example_usage.py            # Example script
├── requirements.txt
├── setup.py
└── README.md
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/safety-research-system.git
cd safety-research-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Quick Start

```python
from models.case import Case, CasePriority
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor
from agents.orchestrator import Orchestrator
from agents.workers.literature_agent import LiteratureAgent
from agents.auditors.literature_auditor import LiteratureAuditor

# Setup system
task_executor = TaskExecutor()
audit_engine = AuditEngine()

# Register agents
task_executor.register_worker(TaskType.LITERATURE_REVIEW, LiteratureAgent())
audit_engine.register_auditor(TaskType.LITERATURE_REVIEW, LiteratureAuditor())

# Create engines
resolution_engine = ResolutionEngine(task_executor, audit_engine)
context_compressor = ContextCompressor()

# Create orchestrator
orchestrator = Orchestrator(
    task_executor, audit_engine, resolution_engine, context_compressor
)

# Create and process a case
case = Case(
    title="Adverse Event Assessment",
    question="Is there a causal relationship between Drug X and hepatotoxicity?",
    priority=CasePriority.HIGH,
    context={"drug_name": "Drug X", "adverse_event": "Hepatotoxicity"},
    data_sources=["pubmed", "clinical_trials_db"]
)

# Process case
report = orchestrator.process_case(case)
print(report)
```

See `example_usage.py` for a complete working example.

## Usage

### Running the Example

```bash
python example_usage.py
```

This will:
1. Initialize the system with literature and statistics agents
2. Create an example safety assessment case
3. Process the case through the full workflow
4. Display the final report with findings and recommendations

### Creating Custom Worker Agents

```python
from agents.base_worker import BaseWorker

class MyCustomWorker(BaseWorker):
    def execute(self, input_data):
        # Your custom logic here
        return {
            "result": {
                "summary": "...",
                "confidence": "Low - requires validation",
                "limitations": ["..."],
                "methodology": "...",
            }
        }
```

### Creating Custom Auditor Agents

```python
from agents.base_auditor import BaseAuditor

class MyCustomAuditor(BaseAuditor):
    def _load_validation_criteria(self):
        return {"required_fields": ["summary", "confidence"]}

    def validate(self, task_input, task_output, task_metadata):
        issues = []
        # Check anti-fabrication compliance
        issues.extend(self.check_anti_fabrication_compliance(task_output))
        # Add custom validation logic

        return {
            "status": "passed" if not issues else "failed",
            "issues": issues,
            "summary": "...",
            "passed_checks": [...],
            "failed_checks": [...],
            "recommendations": [...]
        }
```

## Key Concepts

### Task-Audit-Resolve Pattern

The core innovation is the three-phase validation loop:

1. **Task Execution**: Worker agent performs analysis
2. **Audit Validation**: Auditor checks output quality
3. **Resolution**:
   - If PASS → compress and forward to orchestrator
   - If FAIL → provide corrections and retry (up to max retries)
   - If CRITICAL → escalate to human review

This pattern ensures quality while keeping the orchestrator's context minimal.

### Context Compression

Full worker outputs can be large (10KB+). The context compressor:
- Extracts key findings (conclusion, confidence, sample size, etc.)
- Generates 2-3 sentence summary
- Provides metadata for drill-down
- Typically achieves 80-95% compression

### CLAUDE.md Enforcement

All auditors enforce mandatory anti-fabrication protocols:
- **No score fabrication**: Scores >80% require external validation
- **Evidence requirements**: Every claim needs measurement data
- **Uncertainty expression**: Confidence levels mandatory
- **Banned language**: No "exceptional" without extraordinary evidence

## Configuration

### Audit Checklists

Validation criteria are defined in `guidelines/audit_checklists/`:
- `literature_review_checklist.md`: Literature review standards
- `statistics_checklist.md`: Statistical analysis standards

### Adding Data Sources

Extend worker agents to integrate with:
- PubMed API
- Clinical trials databases
- Internal safety databases
- Real-world evidence sources

### Customizing Retry Behavior

```python
resolution_engine = ResolutionEngine(
    task_executor,
    audit_engine,
    max_retries=3  # Customize retry attempts
)
```

## Development

### Running Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Code Formatting

```bash
black .
isort .
flake8 .
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

### Phase 1: Core System (Current)
- [x] Agent-Audit-Resolve pattern
- [x] Context compression
- [x] CLAUDE.md compliance
- [x] Literature and statistics agents
- [x] Example usage

### Phase 2: Integration
- [ ] Real LLM integration (OpenAI, Anthropic, etc.)
- [ ] PubMed and clinical trials API integration
- [ ] Database persistence layer
- [ ] REST API for case submission

### Phase 3: Advanced Features
- [ ] Risk modeling agents
- [ ] Mechanistic inference agents
- [ ] Causality assessment framework
- [ ] Interactive dashboard
- [ ] Regulatory report generation

### Phase 4: Scale & Production
- [ ] Parallel task execution
- [ ] Caching and performance optimization
- [ ] Human-in-the-loop interface
- [ ] Feedback loop implementation
- [ ] Multi-tenant support

## License

[Specify your license]

## Citations

This system implements concepts from:
- Multi-agent orchestration frameworks
- Evidence-based medicine methodologies
- Regulatory science best practices
- Quality assurance patterns

## Acknowledgments

Inspired by the need for rigorous, evidence-based safety assessment in pharmaceutical research, with explicit enforcement of quality standards and anti-fabrication protocols.

## Contact

[Your contact information]

---

**Note**: This is a prototype system. For production use, integrate with actual LLM providers, databases, and implement appropriate security measures.
