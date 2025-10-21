# Safety Research System

A modular, skills-based research system for pharmaceutical safety assessment. This system implements a novel **Agent→Audit→Resolve** pattern with composable, independently-testable skills that ensure quality and compliance while preventing orchestrator context overload.

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

## Skills Architecture

**Phase 1 Status: 4 of 26 planned skills implemented (141 tests passing)**

The system has been refactored into a skills-based architecture where each skill is a focused, composable unit that can be independently tested and versioned. This enables better modularity, reusability, and maintainability.

### Implemented Skills

#### Literature Skills
- **literature-search** (37 tests) - PubMed API integration for source retrieval
- **evidence-level-classification** (36 tests) - Classify evidence hierarchy (Level I-V)

#### Audit Skills
- **source-authenticity-verification** (32 tests) - Validate PMIDs/URLs, detect fabrication

#### Statistics Skills
- **statistical-evidence-extraction** (36 tests) - Extract numerical claims via regex

### Skill Composition

Skills can be chained together to form complete workflows. Example from `examples/skills_composition_demo.py`:

```python
# End-to-end literature review workflow
from skills.literature.literature_search.scripts.search import search_pubmed
from skills.audit.source_authenticity_verification.scripts.verify import verify_source_authenticity
from skills.literature.evidence_level_classification.scripts.classify import classify_evidence_level
from skills.statistics.statistical_evidence_extraction.scripts.extract import extract_statistics

# Step 1: Search PubMed
sources = search_pubmed("antibody drug conjugate interstitial lung disease", max_results=10)

# Step 2: Validate sources
verification = verify_source_authenticity(sources)
authentic_sources = verification['authentic_sources']

# Step 3: Classify evidence levels
classified_sources = []
for source in authentic_sources:
    classification = classify_evidence_level(source)
    source['evidence_level'] = classification['level']
    classified_sources.append(source)

# Step 4: Extract statistical evidence
for source in classified_sources:
    stats = extract_statistics(source.get('abstract', ''))
    source['statistics'] = stats
```

Each skill:
- Is 100% deterministic (Phase 1) or hybrid code+LLM (Phase 2+)
- Has comprehensive unit tests
- Loads only when needed (minimal context overhead)
- Can be cached for performance
- Follows semantic versioning

See `skills/README.md` for detailed skill documentation.

## Directory Structure

```
safety-research-system/
├── skills/                     # Skills-based architecture (NEW)
│   ├── README.md              # Skills documentation
│   ├── base.py                # Base skill class
│   ├── audit/                 # Audit & validation skills
│   │   └── source_authenticity_verification/
│   │       ├── SKILL.md
│   │       ├── main.py
│   │       ├── scripts/verify.py
│   │       └── tests/test_source_authenticity.py (32 tests)
│   ├── literature/            # Literature review skills
│   │   ├── literature-search/
│   │   │   └── tests/test_literature_search.py (37 tests)
│   │   └── evidence-level-classification/
│   │       └── tests/test_evidence_classification.py (36 tests)
│   └── statistics/            # Statistical analysis skills
│       └── statistical-evidence-extraction/
│           └── tests/test_statistical_extraction.py (36 tests)
├── examples/
│   └── skills_composition_demo.py  # Full workflow demonstration
├── agents/                    # Legacy agent-based architecture
│   ├── base_worker.py
│   ├── base_auditor.py
│   ├── orchestrator.py
│   └── workers/
├── core/
│   ├── task_executor.py
│   ├── audit_engine.py
│   ├── resolution_engine.py
│   └── context_compressor.py
├── models/
│   ├── task.py
│   ├── audit_result.py
│   └── case.py
├── guidelines/
│   └── audit_checklists/
├── config/
├── tests/
├── requirements.txt
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

Run the skills composition demo to see the complete workflow in action:

```bash
# Run the skills composition demo
python examples/skills_composition_demo.py
```

This demonstrates a complete literature review workflow:
1. Search PubMed for "antibody drug conjugate interstitial lung disease"
2. Validate sources for authenticity (detect fabricated PMIDs)
3. Classify evidence hierarchy (Level I-V)
4. Extract statistical evidence (hazard ratios, p-values, sample sizes, etc.)

The demo outputs detailed progress and shows how skills compose together.

### Quick Python Usage

```python
from skills.literature.literature_search.scripts.search import search_pubmed
from skills.audit.source_authenticity_verification.scripts.verify import verify_source_authenticity

# Search PubMed
sources = search_pubmed("drug safety", max_results=5)

# Validate sources
verification = verify_source_authenticity(sources)
print(f"Authentic: {len(verification['authentic_sources'])}")
print(f"Fabricated: {len(verification['fabricated_sources'])}")
```

See `examples/skills_composition_demo.py` for the complete workflow example.

## Usage

### Running the Skills Composition Demo

```bash
python examples/skills_composition_demo.py
```

This demonstrates:
1. PubMed literature search
2. Source authenticity verification (fabrication detection)
3. Evidence level classification (Level I-V hierarchy)
4. Statistical evidence extraction (HR, CI, p-values, sample sizes)

The output shows each skill executing in sequence with detailed progress.

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
# Test all skills
pytest skills/ -v

# Test specific skill
pytest skills/audit/source_authenticity_verification/tests/ -v

# Test with coverage
pytest skills/ -v --cov=skills --cov-report=html

# Test legacy agent system
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

### Phase 1: Skills Foundation (COMPLETE)
- [x] Skills-based architecture implementation
- [x] Base skill class and framework
- [x] Source authenticity verification skill (32 tests)
- [x] Literature search skill (37 tests)
- [x] Evidence level classification skill (36 tests)
- [x] Statistical evidence extraction skill (36 tests)
- [x] Skills composition demo
- [x] 141 passing tests across all skills

**Status: 4 of 26 planned skills implemented**

### Phase 2: Remaining Skills (In Progress)
Literature Skills:
- [ ] Evidence quality assessment
- [ ] Literature synthesis

Statistics Skills:
- [ ] Statistical synthesis
- [ ] Heterogeneity assessment
- [ ] Statistical interpretation

Audit Skills:
- [ ] Citation completeness audit
- [ ] Evidence grading audit
- [ ] Audit issue compilation
- [ ] Statistical methodology audit
- [ ] Assumption audit
- [ ] Uncertainty quantification audit
- [ ] Result validity audit

Resolution Skills:
- [ ] Audit result evaluation
- [ ] Correction extraction
- [ ] Retry orchestration

Compression Skills:
- [ ] Key finding extraction
- [ ] Summary generation
- [ ] Fabrication detection in compression
- [ ] Metadata compression

### Phase 3: LLM Integration
- [ ] Hybrid skills (code + LLM)
- [ ] Real LLM integration (OpenAI, Anthropic, etc.)
- [ ] Prompt templates for hybrid skills
- [ ] LLM response validation

### Phase 4: Integration & Production
- [ ] Database persistence layer
- [ ] REST API for skill composition
- [ ] Caching and performance optimization
- [ ] Human-in-the-loop interface
- [ ] Interactive dashboard
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

**Note**: Phase 1 (Skills Foundation) is complete with 4 deterministic skills and 141 passing tests. The system demonstrates the skills-based architecture pattern. Phase 2+ will add the remaining 22 skills and LLM integration for hybrid skills.
