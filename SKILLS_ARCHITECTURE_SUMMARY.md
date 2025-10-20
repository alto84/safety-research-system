# Safety Research System Skills Architecture - Executive Summary

## Overview

Successfully analyzed and created comprehensive mapping for converting the **safety-research-system** from Agent-Audit-Resolve pattern to a **skills-based architecture**. The analysis covers all 6 major components (2 workers, 2 auditors, 2 core engines) and proposes **26 reusable, composable skills**.

**Document**: See `SKILLS_ARCHITECTURE_MAPPING.md` (1,120 lines, 36KB) for complete technical details.

---

## Key Metrics

### Code Analysis
- **Components Analyzed**: 6 major files (3,100+ lines of Python)
- **Skills Proposed**: 26 reusable skills
- **Deterministic Code**: ~60% (ideal for skill extraction)
- **LLM-Driven Code**: ~25% (prompt templates + validators)
- **External Dependencies**: ~15% (data files, APIs)

### Components Breakdown
| Component | Current Lines | Skills | Type | Complexity |
|-----------|--------------|--------|------|-----------|
| LiteratureAgent | 761 | 4 | Worker | Medium-High |
| StatisticsAgent | 468 | 4 | Worker | Medium |
| LiteratureAuditor | 573 | 4 | Auditor | Medium |
| StatisticsAuditor | 342 | 4 | Auditor | Low-Medium |
| ResolutionEngine | 527 | 3 | Core | Medium-High |
| ContextCompressor | 773 | 4 | Core | Medium |

---

## Skills Architecture Overview

### **Category 1: Literature Review Skills (4 skills)**

1. **literature_search** [Tool Skill - 100% Deterministic]
   - Searches PubMed and retrieves paper metadata
   - Current code location: lines 109-140 of literature_agent.py
   - Dependencies: PubMedConnector API

2. **evidence_level_classification** [Analysis Skill - 100% Deterministic]
   - Classifies papers by evidence hierarchy (RCT/cohort/case-control/etc)
   - Current code location: lines 187-203 of literature_agent.py
   - Skill data: evidence_hierarchy.yaml, classification_patterns.yaml

3. **evidence_quality_assessment** [Reasoning Skill - 30% Deterministic, 70% LLM]
   - Multidimensional evidence quality analysis across 6 dimensions
   - Current code location: lines 290-671 of literature_agent.py
   - LLM Component: Intelligent assessment prompt
   - Deterministic Components: Validation logic, CLAUDE.md compliance enforcement

4. **literature_synthesis** [Analysis Skill - 100% Deterministic]
   - Synthesizes findings and identifies evidence gaps
   - Current code location: lines 205-223, 673-692 of literature_agent.py
   - Pure logic: Counting evidence levels, pattern-based gap identification

---

### **Category 2: Statistical Analysis Skills (4 skills)**

1. **statistical_evidence_extraction** [Extraction Skill - 100% Deterministic]
   - Extracts quantitative data from paper abstracts using regex
   - Current code location: lines 182-224 of statistics_agent.py
   - Skill data: extraction_patterns.yaml with regex patterns for:
     - Percentages (10-20%)
     - P-values (p<0.05)
     - Confidence intervals (95% CI: 1.2-3.4)
     - Sample sizes (n=100)
     - Risk ratios (RR=1.5)

2. **statistical_synthesis** [Analysis Skill - 100% Deterministic]
   - Calculates aggregate statistics (mean, median, std deviation, range)
   - Current code location: lines 244-293 of statistics_agent.py
   - Pure math: sum(), division, variance calculation

3. **heterogeneity_assessment** [Analysis Skill - 100% Deterministic]
   - Assesses variability across studies
   - Current code location: lines 295-322 of statistics_agent.py
   - Logic: Study design counting, sample size range analysis

4. **statistical_interpretation** [Reasoning Skill - 40% Deterministic, 60% LLM]
   - Interprets statistical findings in clinical context
   - Current code location: lines 324-354 of statistics_agent.py
   - Deterministic: Confidence counting, evidence quality assessment
   - LLM: Context-specific interpretation (optional, can fall back to rules)

---

### **Category 3: Literature Audit Skills (4 skills)**

1. **source_authenticity_verification** [Validation Skill - 100% Deterministic]
   - Validates sources are real, not fabricated
   - Current code location: lines 157-366 of literature_auditor.py
   - Checks:
     - PMID format validation (1-8 digits, not obvious fakes like 12345678)
     - URL format and accessibility (HTTP HEAD requests)
     - DOI format validation
     - Placeholder pattern detection (example.com, "Smith et al.", etc)
   - CRITICAL FOR SAFETY: Anti-fabrication guardrails

2. **citation_completeness_audit** [Validation Skill - 100% Deterministic]
   - Verifies all required citation fields present
   - Current code location: lines 421-460 of literature_auditor.py
   - Required fields: title, authors, year, identifier (PMID/DOI/URL)

3. **evidence_grading_audit** [Validation Skill - 100% Deterministic]
   - Verifies evidence levels align with confidence claims
   - Current code location: lines 462-483 of literature_auditor.py
   - CLAUDE.md Enforcement: No "high confidence" with "low evidence"

4. **audit_issue_compilation** [Compilation Skill - 100% Deterministic]
   - Aggregates issues into audit report
   - Categories: anti-fabrication, completeness, evidence grading, citations
   - Severity levels: critical, warning, info

---

### **Category 4: Statistics Audit Skills (4 skills)**

1. **statistical_methodology_audit** [Validation Skill - 100% Deterministic]
   - Validates methodology is adequately documented
   - Current code location: lines 154-184 of statistics_auditor.py
   - Checks: minimum documentation length, mention of "actual data" or "measured"

2. **assumption_audit** [Validation Skill - 100% Deterministic]
   - Verifies statistical assumptions documented
   - Current code location: lines 186-217 of statistics_auditor.py
   - Minimum 2 assumptions required

3. **uncertainty_quantification_audit** [Validation Skill - 100% Deterministic]
   - Validates confidence intervals and uncertainty expression
   - Current code location: lines 219-247 of statistics_auditor.py
   - Checks: Confidence intervals present, confidence level clearly stated

4. **result_validity_audit** [Validation Skill - 100% Deterministic]
   - Verifies results are backed by actual data
   - Current code location: lines 249-290 of statistics_auditor.py
   - ANTI-FABRICATION: Detects unsupported numerical results

---

### **Category 5: Resolution Skills (3 skills)**

1. **audit_result_evaluation** [Decision Skill - 80% Deterministic, 20% LLM]
   - Evaluates audit and determines next action (ACCEPT/RETRY/ESCALATE/ABORT)
   - Current code location: lines 167-197 (legacy), 241-358 (intelligent) of resolution_engine.py
   - Hard Constraints (NO LLM override):
     - Fabrication detected → ESCALATE
     - Audit passed → ACCEPT
     - Max retries exceeded → ABORT
   - Intelligent Assessment: Fixability analysis, priority consideration

2. **correction_extraction** [Transformation Skill - 100% Deterministic]
   - Transforms audit issues into actionable correction instructions
   - Current code location: lines 199-230 of resolution_engine.py
   - Output: Structured corrections with location, suggested_fix, guideline_reference

3. **retry_orchestration** [Control Skill - 100% Deterministic]
   - Manages retry loop and state tracking
   - Records resolution history for audit trail
   - Updates task status appropriately

---

### **Category 6: Compression Skills (4 skills)**

1. **key_finding_extraction** [Extraction Skill - 100% Deterministic]
   - Extracts most important findings from task output
   - Current code location: lines 629-689 of context_compressor.py
   - Regex patterns for numerical claims:
     - Percentages: 10-20%
     - P-values: p<0.05
     - Odds ratios: OR=2.3
     - Confidence intervals: CI: 1.2-3.4
     - Sample sizes: n=100

2. **summary_generation** [Compression Skill - 50% Deterministic, 50% LLM]
   - Generates concise 2-3 sentence summaries for orchestrator
   - Current code location: lines 97-263 of context_compressor.py
   - Intelligent compression: Preserves critical info intelligently
   - Legacy fallback: Template-based compression

3. **fabrication_detection_in_compression** [Validation Skill - 100% Deterministic]
   - CRITICAL SAFETY: Validates compressed summaries don't fabricate data
   - Current code location: lines 497-572 of context_compressor.py
   - Checks:
     - Numerical claims exist in original
     - Confidence not inflated
     - Limitations not removed
     - No new fabricated connections

4. **metadata_compression** [Transformation Skill - 100% Deterministic]
   - Compresses metadata to essentials only
   - Current code location: lines 691-720 of context_compressor.py
   - Keeps: execution_time, retry_count, agent, audit status
   - Removes: verbose explanations, debug info

---

## Resource Files Required

### Configuration Files (YAML)
```
skills/
├── evidence_hierarchy.yaml                 # Evidence level definitions
├── classification_patterns.yaml            # Regex patterns for classification
├── extraction_patterns.yaml                # Regex for statistics extraction
├── fabrication_patterns.yaml               # Placeholder detection patterns
├── validation_rules.yaml                   # Audit validation rules
├── placeholder_urls.yaml                   # Common fake URL patterns
├── hard_constraints.yaml                   # Resolution hard rules
├── assessment_dimensions.yaml              # Evidence assessment dimensions
└── validation_schemas.yaml                 # Output schemas
```

### Prompt Templates (Markdown)
```
prompts/
├── evidence_quality_assessment.md          # 600+ line LLM prompt (existing)
├── statistical_interpretation.md           # New - context-aware stats interpretation
├── intelligent_resolution_decision.md      # 150+ line decision reasoning prompt
└── intelligent_compression.md              # 200+ line compression prompt
```

### Data Schemas (YAML)
- Evidence hierarchy with keywords and weights
- Fabrication patterns with reasons
- Validation schemas for all output types
- Hard constraints for auto-escalation

---

## Skill Dependencies and Chaining

### Complete Literature Review Workflow
```
Query
  ↓
literature_search (API call)
  ↓
evidence_level_classification (100% Python)
  ↓
evidence_quality_assessment (LLM optional)
  ↓
literature_synthesis (100% Python)
  ↓
[Literature Review Output]
  ↓
  ├→ source_authenticity_verification (audit)
  ├→ citation_completeness_audit (audit)
  ├→ evidence_grading_audit (audit)
  ↓
key_finding_extraction (compression)
  ↓
summary_generation (compression)
  ↓
fabrication_detection_in_compression (validation)
  ↓
[Compressed Output for Orchestrator]
```

### Dependency Graph (Low to High)
1. **No Dependencies**: 17 skills (pure extraction, validation, transformation)
2. **Single Dependency**: 7 skills (e.g., evidence_quality depends on literature_search)
3. **Multiple Dependencies**: 2 skills (audit_result_evaluation, summary_generation)

---

## Key Technical Decisions

### 1. Deterministic vs LLM Split
- **100% Deterministic** (17 skills): All validation, extraction, compilation
- **Hybrid** (7 skills): Assessment, synthesis, interpretation
- **Deterministic Preferred**: Falls back to rules when LLM unavailable

### 2. Hard Constraints (Never Override)
- Fabrication detected → ESCALATE (skip LLM)
- Critical issues found → ESCALATE (skip LLM)
- Max retries exceeded → ABORT (skip LLM)
- CLAUDE.md violations → REJECT (skip LLM)

### 3. Skill Boundaries
- **Clear input/output contracts** for each skill
- **Single responsibility** (evidence grading ≠ evidence quality)
- **Reusable across contexts** (e.g., PMID validation used in both auditors)
- **Data-driven** (patterns/rules in YAML files, not code)

### 4. Caching Strategy
- Cache at skill level for expensive operations (API calls, LLM calls)
- Invalidation based on content hash (not time-based)
- Separate cache per skill with deterministic keys

---

## Migration Path (Estimated 4-5 weeks)

### Week 1: Setup & Deterministic Extraction
- Create skill directory structure
- Extract 17 deterministic skills
- Create YAML configuration files
- Write comprehensive unit tests

### Week 2: Extraction Continuation & API Skills
- Complete remaining 9 skills
- Implement PubMedConnector wrapper
- Add HTTP request utilities
- Integration testing between skills

### Week 3: LLM Integration
- Extract thought pipe prompts from current code
- Create prompt validation utilities
- Implement intelligent skill wrappers
- Add caching infrastructure

### Week 4: Orchestration & Migration
- Build skill orchestrator
- Migrate workers to use skills
- Migrate auditors to use skills
- Update resolution engine to use skills

### Week 5: Optimization & Polish
- Performance profiling
- Token optimization
- Comprehensive documentation
- Migration guide for remaining code

---

## Benefits Summary

| Aspect | Current | Skills-Based |
|--------|---------|--------------|
| **Reusability** | Skills embedded in agents | 26 standalone, reusable skills |
| **Testability** | 100-500 line methods | 10-40 line skill methods |
| **Composability** | Fixed sequential workflows | Dynamic DAG composition |
| **Code Separation** | LLM + deterministic mixed | Clear separation |
| **Caching** | Limited, at agent level | Per-skill, content-aware |
| **Documentation** | Agent-level docs | Skill-level + orchestration docs |
| **Token Efficiency** | Full output in context | Minimal context transfer |
| **Debugging** | Agent-level debugging | Skill-level granularity |
| **Maintenance** | Monolithic changes | Isolated skill updates |
| **Scaling** | Coupled to agents | Independent skill scaling |

---

## Critical Safety Features Preserved

1. **Anti-Fabrication**: 6 dedicated validation skills
   - PMID format validation
   - URL accessibility checks
   - Placeholder detection
   - Numerical claim verification

2. **CLAUDE.md Compliance**: Built into validation
   - Hard constraints for confidence-evidence alignment
   - Mandatory limitations documentation
   - Evidence chain traceability
   - Uncertainty expression requirements

3. **Escalation Rules**: Immutable hard constraints
   - Fabrication → auto-escalate
   - Critical issues → auto-escalate
   - No LLM override capability

---

## Files Included

1. **SKILLS_ARCHITECTURE_MAPPING.md** (36KB, 1,120 lines)
   - Complete technical mapping
   - Code examples from current implementation
   - Resource files specifications
   - Integration point diagrams
   - Composability examples
   - Migration strategy

2. **This Summary Document**
   - Executive overview
   - Quick reference metrics
   - Key technical decisions
   - Benefits analysis

---

## Next Steps

1. **Review** this analysis and SKILLS_ARCHITECTURE_MAPPING.md
2. **Validate** proposed skill boundaries with domain experts
3. **Prioritize** skills for initial extraction (suggest: start with deterministic skills)
4. **Create** skill templates and base classes
5. **Begin** Week 1 implementation with deterministic skills
6. **Establish** testing patterns early for consistent validation

---

## Questions Answered in Mapping Document

- **Which code becomes a skill?** See detailed component sections
- **What data files are needed?** See "Data Files and Schemas" section
- **How do skills compose?** See "Composability and Chaining" section  
- **What's the migration path?** See "Migration Strategy" section
- **Where are specific code examples?** Each skill section references current line numbers
- **What about LLM integration?** Covered in each hybrid skill section
- **How is safety maintained?** Detailed in hard constraints and validation sections

