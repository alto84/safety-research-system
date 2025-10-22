# Safety Research Skills

This directory contains modular, composable skills for the Safety Research System, implementing the **Skills-Based Architecture** using Anthropic's skills framework.

## Architecture Overview

Skills are small, focused units that:
- Perform a single, well-defined task
- Can be 100% deterministic code OR hybrid (code + LLM)
- Compose together to form complex workflows
- Are independently testable and versionable
- Load only when needed (minimal context overhead)

## Skill Categories

### Literature (2 implemented, 2 planned)
- **literature_search** (37 tests) - PubMed API integration for source retrieval
- **evidence-level-classification** (36 tests) - Classify evidence hierarchy (Level I-V)
- `evidence_quality_assessment` (planned) - Multidimensional quality evaluation
- `literature_synthesis` (planned) - Aggregate findings across sources

### Statistics (1 implemented, 3 planned)
- **statistical-evidence-extraction** (36 tests) - Extract numerical claims via regex
- `statistical_synthesis` (planned) - Calculate aggregate statistics
- `heterogeneity_assessment` (planned) - Analyze cross-study variability
- `statistical_interpretation` (planned) - Clinical interpretation of findings

### Audit (1 implemented, 7 planned)
- **source-authenticity-verification** (32 tests) - Validate PMIDs/URLs, detect fabrication
- `citation_completeness_audit` (planned) - Check required citation fields
- `evidence_grading_audit` (planned) - Validate evidence-confidence alignment
- `audit_issue_compilation` (planned) - Aggregate validation issues
- `statistical_methodology_audit` (planned) - Validate methodology documentation
- `assumption_audit` (planned) - Verify statistical assumptions
- `uncertainty_quantification_audit` (planned) - Check confidence intervals
- `result_validity_audit` (planned) - Verify data source alignment

### Resolution (0 implemented, 3 planned)
- `audit_result_evaluation` (planned) - Decide RETRY/ESCALATE/ABORT
- `correction_extraction` (planned) - Transform issues to actionable corrections
- `retry_orchestration` (planned) - Manage retry loop workflow

### Compression (0 implemented, 4 planned)
- `key_finding_extraction` (planned) - Extract numerical claims
- `summary_generation` (planned) - Generate concise summaries
- `fabrication_detection_in_compression` (planned) - Validate summary accuracy
- `metadata_compression` (planned) - Simplify metadata

**Current Status: 4 of 26 skills implemented (141 tests passing)**

### Config (Shared Resources)
- `evidence_hierarchy.yaml` - Evidence level definitions
- `classification_patterns.yaml` - Pattern matching rules
- `fabrication_patterns.yaml` - Fabrication detection patterns
- `validation_rules.yaml` - Validation criteria
- `hard_constraints.yaml` - Immutable safety thresholds

## Skill Structure

Each skill follows this structure:

```
skills/{category}/{skill_name}/
├── skill.yaml              # Manifest (metadata, inputs, outputs)
├── README.md               # Documentation and usage examples
├── main.py                 # Core implementation
├── prompts/                # LLM prompts (if hybrid skill)
│   └── {prompt_name}.md
├── tests/                  # Unit tests
│   └── test_{skill_name}.py
└── CHANGELOG.md            # Version history
```

## Skill Manifest (skill.yaml)

```yaml
name: source_authenticity_verification
version: 1.0.0
category: audit
type: deterministic  # or 'hybrid' or 'llm'
description: Validates source authenticity, detects fabricated PMIDs/URLs

inputs:
  sources:
    type: List[Dict]
    description: Sources to validate (with 'pmid', 'url', 'title' fields)
    required: true

outputs:
  validation_result:
    type: Dict
    schema:
      authentic_sources: List[Dict]
      fabricated_sources: List[Dict]
      issues: List[ValidationIssue]

dependencies:
  - requests>=2.28.0  # For URL checking

configuration:
  patterns_file: ../config/fabrication_patterns.yaml

performance:
  avg_execution_time_ms: 150
  deterministic: true
  cacheable: true
```

## Usage

### From Python

```python
from skills.audit.source_authenticity_verification import SourceAuthenticityVerification

skill = SourceAuthenticityVerification()
result = skill.execute({
    "sources": [
        {"pmid": "12345678", "title": "Example Study"},
        {"url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"},
    ]
})

print(result["validation_result"]["issues"])
```

### From Claude Code

Skills are automatically discovered and loaded when relevant to the task:

```
User: "Validate these sources for fabrication"
Claude: [Automatically loads source_authenticity_verification skill]
```

## Skill Development

### Creating a New Skill

1. **Create directory structure:**
   ```bash
   mkdir -p skills/{category}/{skill_name}/{prompts,tests}
   ```

2. **Create skill.yaml:**
   - Define inputs, outputs, dependencies
   - Specify type (deterministic/hybrid/llm)
   - Document configuration

3. **Implement main.py:**
   ```python
   from typing import Dict, Any
   from skills.base import BaseSkill

   class MySkill(BaseSkill):
       def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
           # Implementation
           return {"result": ...}
   ```

4. **Write tests:**
   - Unit tests for all code paths
   - Integration tests for skill composition
   - Edge case handling

5. **Document in README.md:**
   - Purpose and use cases
   - Input/output examples
   - Composition patterns

### Testing Skills

```bash
# Test single skill
pytest skills/audit/source_authenticity_verification/tests/ -v

# Test category
pytest skills/audit/ -v

# Test all skills
pytest skills/ -v --cov=skills --cov-report=html
```

## Skill Composition

Skills can be chained to form complex workflows:

```python
# Example: Literature review workflow
from skills.literature.literature_search import LiteratureSearch
from skills.audit.source_authenticity_verification import SourceAuthenticityVerification
from skills.literature.evidence_level_classification import EvidenceLevelClassification

# Step 1: Search PubMed
search = LiteratureSearch()
sources = search.execute({"query": "ADC interstitial lung disease"})

# Step 2: Validate sources
verify = SourceAuthenticityVerification()
validated = verify.execute({"sources": sources["results"]})

# Step 3: Classify evidence levels
classify = EvidenceLevelClassification()
classified = classify.execute({"sources": validated["authentic_sources"]})
```

## Versioning

Skills follow semantic versioning:
- **Major (1.x.x):** Breaking changes to inputs/outputs
- **Minor (x.1.x):** New features, backward compatible
- **Patch (x.x.1):** Bug fixes, no API changes

Version history is tracked in each skill's CHANGELOG.md.

## Configuration

Shared configuration files in `skills/config/`:

- **evidence_hierarchy.yaml:** Evidence level definitions (Level I-V)
- **classification_patterns.yaml:** Patterns for text classification
- **fabrication_patterns.yaml:** Known fabrication patterns
- **validation_rules.yaml:** Validation criteria per domain
- **hard_constraints.yaml:** Immutable safety thresholds

## Safety & Compliance

### Immutable Safety Checks

The following are hard-coded and cannot be modified by skills:
- Score > 80 threshold (requires external validation)
- Banned phrases list (CLAUDE.md compliance)
- Fabrication detection patterns (core algorithms)
- Evidence chain requirements

### CLAUDE.md Compliance

All skills enforce:
- No score fabrication without measurement data
- Mandatory evidence chains for claims
- Required uncertainty expression
- Banned language detection

## Performance

Skills are optimized for:
- **Minimal context usage:** Load only when needed
- **Caching:** Deterministic skills cache results
- **Parallel execution:** Independent skills can run concurrently
- **Incremental composition:** Build complex workflows from simple units

Typical execution times:
- Deterministic skills: 10-500ms
- Hybrid skills (with LLM): 1-5 seconds
- LLM-only skills: 2-10 seconds

## Contributing

1. Follow the skill structure template
2. Write comprehensive tests (>80% coverage)
3. Document inputs/outputs clearly
4. Include usage examples
5. Update CHANGELOG.md with version changes

## License

[Specify your license]

---

**Status:** Phase 1 Complete - 4 deterministic skills with 141 passing tests
**Next:** Phase 2 - Implement remaining 22 skills, then LLM integration for hybrid skills
