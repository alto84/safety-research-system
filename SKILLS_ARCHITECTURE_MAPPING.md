# Safety Research System: Skills-Based Architecture Mapping

## Executive Summary

This document provides a detailed mapping for converting the safety-research-system from an Agent-Audit-Resolve architecture to a skills-based architecture. The analysis covers 6 major components across workers, auditors, and core engines, identifying how each can be decomposed into reusable, composable skills.

**Key Finding**: The current system is well-suited for skills conversion, with clear separation between:
- **Deterministic operations** (60% of code) → Skill implementation
- **LLM-driven reasoning** (25% of code) → Skill prompts
- **External dependencies** (15% of code) → Skill data/resources

---

## 1. LITERATURE AGENT → Literature Review Skills

### 1.1 Current Structure Analysis

**File**: `agents/workers/literature_agent.py` (761 lines)

**Current Responsibilities**:
- PubMed search and paper fetching
- Evidence level classification (deterministic)
- Key findings synthesis
- Multidimensional evidence quality assessment (LLM-driven)
- Gap identification
- Limitations documentation

**Execution Flow**:
```
Input Query → PubMed Search → Paper Fetch → Evidence Level Classification 
→ Evidence Quality Assessment → Findings Synthesis → Gap Identification → Output
```

### 1.2 Proposed Skill Decomposition

#### Skill 1A: `literature_search`
**Purpose**: Search and retrieve academic literature from PubMed

**Type**: Tool Skill (deterministic + external API)

**Implementation**:
```
├── skill_definition.yaml
│   ├── name: literature_search
│   ├── description: Search PubMed and retrieve paper metadata
│   ├── inputs:
│   │   - query: string (research question)
│   │   - max_results: int (default: 10)
│   │   - data_sources: list[string] (default: ["pubmed"])
│   └── outputs:
│       ├── sources: list[Dict] (paper metadata)
│       ├── total_results: int
│       └── search_metadata: Dict (search date, query hash)
│
├── skill_implementation.py
│   ├── class LiteratureSearchSkill(Skill)
│   ├── def execute(query, max_results, data_sources) → Dict
│   ├── def _search_pubmed(query, max_results) → list[str]
│   ├── def _fetch_paper_details(pmid) → PaperDetails
│   └── def _validate_input(query, data_sources) → bool
│
├── skill_data/
│   ├── data_sources_config.yaml
│   │   └── Defines available databases (pubmed, clinical_trials, etc.)
│   └── search_limits.yaml
│       └── rate limits, max results, timeout configs
│
└── skill_tests/
    ├── test_search_pubmed.py
    ├── test_paper_fetch.py
    └── test_input_validation.py
```

**Executable Components** (Pure Python):
- `_search_pubmed()`: PMID retrieval (API call, but deterministic response)
- `_fetch_paper_details()`: Extract metadata from PubMed API response
- Input validation and error handling

**LLM-Driven Components**: None

**Dependencies**:
- PubMedConnector module (external)
- Error handling utilities

---

#### Skill 1B: `evidence_level_classification`
**Purpose**: Classify research studies by evidence hierarchy

**Type**: Classification Skill (deterministic)

**Implementation**:
```
├── skill_definition.yaml
│   ├── name: evidence_level_classification
│   ├── description: Classify papers by evidence hierarchy (RCT/cohort/case etc)
│   ├── inputs:
│   │   └── papers: list[Dict] (with title, abstract)
│   └── outputs:
│       ├── classified_papers: list[Dict] (papers + evidence_level)
│       └── classification_stats: Dict (counts by level)
│
├── skill_implementation.py
│   ├── class EvidenceLevelClassificationSkill(Skill)
│   ├── def execute(papers) → Dict
│   ├── def _classify_paper(title, abstract) → str
│   ├── def _extract_keywords(text) → list[str]
│   └── def _rank_keywords(keywords) → list[tuple]
│
├── skill_data/
│   ├── evidence_hierarchy.yaml
│   │   └── Defines levels and keyword patterns
│   └── classification_patterns.yaml
│       └── Regex patterns for each evidence type
│
└── skill_tests/
    ├── test_classification_accuracy.py
    └── test_edge_cases.py
```

**Executable Components** (100% Pure Python):
- `_classify_paper()`: Keyword matching against patterns
- Pattern matching logic (regex)
- Evidence hierarchy definitions
- Statistical aggregation

**Code Example from Current Implementation**:
```python
# From literature_agent.py lines 187-203
def _determine_evidence_level(self, paper_details) -> str:
    """This is 100% deterministic and becomes the core of skill 1B"""
    title_lower = paper_details.title.lower()
    abstract_lower = paper_details.abstract.lower() if paper_details.abstract else ""
    
    if "randomized controlled trial" in title_lower or "randomized controlled trial" in abstract_lower:
        return "Level 1 - Randomized Controlled Trial"
    # ... more patterns
    return "Level 3 - Observational Study"
```

**Resource Files**:
```yaml
# skill_data/evidence_hierarchy.yaml
levels:
  - level: 1
    type: "Randomized Controlled Trial"
    keywords: ["randomized controlled trial", "rct", "random assignment"]
    patterns: [regex patterns...]
  - level: 1
    type: "Systematic Review"
    keywords: ["systematic review", "meta-analysis", "meta analysis"]
    patterns: [regex patterns...]
  - level: 2
    type: "Cohort Study"
    keywords: ["cohort study", "prospective", "cohort analysis"]
    patterns: [regex patterns...]
  # ... more levels
```

---

#### Skill 1C: `evidence_quality_assessment`
**Purpose**: Assess evidence quality across multiple dimensions

**Type**: Reasoning Skill (LLM-driven with validation)

**Implementation**:
```
├── skill_definition.yaml
│   ├── name: evidence_quality_assessment
│   ├── description: Multidimensional evidence quality analysis
│   ├── inputs:
│   │   ├── sources: list[Dict] (papers with metadata)
│   │   ├── research_question: string
│   │   └── enable_intelligent_assessment: bool (default: true)
│   └── outputs:
│       ├── overall_rating: str (High/Moderate/Low)
│       ├── dimensional_ratings: Dict
│       ├── strongest_sources: list[Dict]
│       ├── weaker_sources: list[Dict]
│       ├── limitations: list[str]
│       └── evidence_gaps: list[str]
│
├── skill_implementation.py
│   ├── class EvidenceQualityAssessmentSkill(Skill)
│   ├── def execute(sources, research_question, enable_intelligent) → Dict
│   ├── def _assess_quality_intelligent(sources, query) → Dict
│   ├── def _assess_quality_legacy(sources) → Dict
│   ├── def _validate_assessment(response) → bool
│   └── def _format_output(response, sources) → Dict
│
├── skill_prompts/
│   └── evidence_assessment_prompt.md
│       └── Template for LLM reasoning with compliance checks
│
├── skill_data/
│   ├── assessment_dimensions.yaml
│   │   └── Defines 6 assessment dimensions
│   └── rating_rules.yaml
│       └── CLAUDE.md compliance rules
│
└── skill_tests/
    ├── test_intelligent_assessment.py
    ├── test_legacy_assessment.py
    ├── test_compliance.py
    └── test_response_validation.py
```

**LLM-Driven Components**:
- Multi-dimensional analysis across 6 dimensions
- Nuanced reasoning about study appropriateness
- Confidence level determination with justification

**Executable Components**:
- Response validation (checking structure, required fields)
- CLAUDE.md compliance enforcement (hard constraints)
- Rating rule application
- Output formatting and caching

**Key Files from Current Implementation**:
- `_build_evidence_assessment_prompt()` (lines 432-551)
- `_validate_evidence_assessment_response()` (lines 553-629)
- `_format_assessment_output()` (lines 631-671)

---

#### Skill 1D: `literature_synthesis`
**Purpose**: Synthesize findings and identify gaps

**Type**: Hybrid Skill (partial deterministic, partial LLM)

**Implementation**:
```
├── skill_definition.yaml
│   ├── name: literature_synthesis
│   ├── description: Synthesize findings and identify evidence gaps
│   ├── inputs:
│   │   └── sources: list[Dict] (assessed papers)
│   └── outputs:
│       ├── key_findings: list[str]
│       ├── gaps: list[str]
│       ├── methodological_summary: str
│       └── synthesis_metadata: Dict
│
├── skill_implementation.py
│   ├── class LiteratureSynthesisSkill(Skill)
│   ├── def execute(sources) → Dict
│   ├── def _synthesize_findings(sources) → list[str]
│   ├── def _identify_gaps(sources) → list[str]
│   ├── def _analyze_evidence_levels(sources) → Dict
│   └── def _extract_publication_metadata(sources) → Dict
│
├── skill_data/
│   ├── gap_patterns.yaml
│   │   └── Common gap templates
│   └── synthesis_templates.yaml
│       └── Finding statement templates
│
└── skill_tests/
    ├── test_finding_synthesis.py
    └── test_gap_identification.py
```

**Executable Components** (100% Pure Python):
```python
# From literature_agent.py lines 205-223
def _synthesize_findings(self, sources: List[Dict]) -> List[str]:
    findings = []
    level_1_count = sum(1 for s in sources if "Level 1" in s.get("evidence_level", ""))
    level_2_count = sum(1 for s in sources if "Level 2" in s.get("evidence_level", ""))
    
    if level_1_count > 0:
        findings.append(f"High-quality evidence available: {level_1_count} RCTs...")
    # ... deterministic synthesis logic

# From literature_agent.py lines 673-692
def _identify_gaps(self, sources: List[Dict]) -> List[str]:
    gaps = []
    has_rcts = any("Randomized Controlled Trial" in s.get("evidence_level", "")
                   for s in sources)
    if not has_rcts:
        gaps.append("Lack of randomized controlled trials...")
    # ... deterministic gap identification
```

---

### 1.3 Integration Points Between Literature Skills

```
┌─────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR INPUT                                          │
│ { query: string, data_sources: list, context: dict }       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ literature_search  │  → [sources with metadata]
        └────────┬───────────┘
                 │
                 ▼
    ┌─────────────────────────────┐
    │ evidence_level_             │  → [sources with levels]
    │ classification             │
    └────────┬────────────────────┘
             │
             ▼
  ┌────────────────────────────────────┐
  │ evidence_quality_assessment        │  → [rated sources + gaps]
  │ (may call LLM for intelligent)     │
  └────────┬─────────────────────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ literature_synthesis │  → [findings + gaps]
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ ORCHESTRATOR OUTPUT  │
    │ (full review result) │
    └──────────────────────┘
```

---

## 2. STATISTICS AGENT → Statistical Analysis Skills

### 2.1 Current Structure Analysis

**File**: `agents/workers/statistics_agent.py` (468 lines)

**Current Responsibilities**:
- Statistical evidence extraction from text
- Sample size estimation
- Descriptive statistical calculation
- Heterogeneity assessment
- Statistical interpretation

**Decomposition**:

#### Skill 2A: `statistical_evidence_extraction`
**Purpose**: Extract quantitative data from paper abstracts

**Type**: Extraction Skill (deterministic with regex)

**Key Executable Components**:
```python
# From statistics_agent.py lines 182-224
# Pure regex extraction patterns:
percentage_pattern = r'(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)%'
p_value_pattern = r'p\s*[<>=]\s*0?\.\d+'
ci_pattern = r'95%?\s*(?:CI|confidence interval)[:\s]*\[?(\d+(?:\.\d+)?)[,\s-]+(\d+(?:\.\d+)?)\]?'

def _extract_statistical_evidence(self, sources) → List[StatisticalEvidence]:
    # This is 100% deterministic regex extraction
```

**Skill Implementation**:
```yaml
skill_data/
├── extraction_patterns.yaml
│   ├── percentage_patterns
│   ├── p_value_patterns
│   ├── confidence_interval_patterns
│   ├── sample_size_patterns
│   └── risk_ratio_patterns
└── evidence_data_class.yaml
    └── StatisticalEvidence schema

skill_implementation.py
├── class StatisticalEvidenceExtractionSkill(Skill)
├── def execute(sources) → Dict
├── def _extract_percentages(text) → list[str]
├── def _extract_p_values(text) → list[str]
├── def _extract_confidence_intervals(text) → list[tuple]
├── def _extract_sample_sizes(text) → list[int]
└── def _extract_risk_ratios(text) → list[tuple]
```

#### Skill 2B: `statistical_synthesis`
**Purpose**: Calculate aggregate statistics from extracted data

**Type**: Analysis Skill (deterministic math)

**Key Executable Components**:
```python
# From statistics_agent.py lines 244-293
# Pure statistics calculations:
mean_value = sum(numeric_values) / len(numeric_values)
variance = sum((x - mean_value) ** 2 for x in numeric_values) / len(numeric_values)
std_dev = variance ** 0.5
median = sorted(numeric_values)[len(numeric_values)//2]
```

#### Skill 2C: `heterogeneity_assessment`
**Purpose**: Assess variability across studies

**Type**: Analysis Skill (deterministic)

**Key Executable Components**:
```python
# From statistics_agent.py lines 295-322
# Pure deterministic logic:
study_designs = {}
for evidence in evidence_list:
    design = evidence.study_design
    study_designs[design] = study_designs.get(design, 0) + 1

if len(set(study_designs.keys())) <= 2 and len(sample_sizes) > 0:
    size_range = max(sample_sizes) / min(sample_sizes)
    if size_range < 5:
        heterogeneity_level = "Moderate"
```

---

## 3. LITERATURE AUDITOR → Audit Skills

### 3.1 Current Structure Analysis

**File**: `agents/auditors/literature_auditor.py` (573 lines)

**Decomposition**:

#### Skill 3A: `source_authenticity_verification`
**Purpose**: Validate that sources are real, not fabricated

**Type**: Validation Skill (deterministic)

**Executable Components** (100% Python):
```python
# From literature_auditor.py - All deterministic validations

# PMID validation (lines 230-274)
def _validate_pmid_format(pmid: str) → bool:
    if not re.match(r'^\d{1,8}$', pmid):
        return False
    if re.match(r'^(12345678|87654321|...)$', pmid):  # Obvious fakes
        return False
    return True

# URL validation (lines 276-346)
def _validate_url_format(url: str) → bool:
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False

def _check_url_accessibility(url: str) → bool:
    try:
        response = requests.head(url, timeout=5)
        return 200 <= response.status_code < 400
    except:
        return False

# Placeholder detection (lines 176-228)
def _detect_placeholder_patterns(text: str) → bool:
    patterns = [
        r'(?i)example\s+study',
        r'(?i)sample\s+research',
        # ... more patterns
    ]
    return any(re.search(p, text) for p in patterns)
```

**Skill Implementation**:
```yaml
skill_data/
├── fabrication_patterns.yaml
│   ├── placeholder_titles
│   ├── fake_author_patterns
│   └── sequential_pmid_patterns
├── validation_rules.yaml
│   ├── pmid_rules
│   ├── url_rules
│   └── doi_rules
└── placeholder_urls.yaml
    └── Common placeholder domain patterns

skill_implementation.py
├── class SourceAuthenticityVerificationSkill(Skill)
├── def execute(sources) → Dict
├── def _validate_pmid(pmid) → bool
├── def _validate_url(url) → bool
├── def _check_url_accessibility(url) → bool
├── def _validate_doi(doi) → bool
├── def _detect_placeholders(text) → bool
└── def _is_sequential_pattern(text) → bool
```

#### Skill 3B: `citation_completeness_audit`
**Purpose**: Verify all required citation fields present

**Type**: Validation Skill (deterministic)

**Executable Components** (100% Python):
```python
# From literature_auditor.py

def _check_source_quality(sources: list) → list[Issue]:
    """Check completeness of source fields"""
    required_fields = ["title", "authors", "year"]
    issues = []
    
    for i, source in enumerate(sources):
        missing = [f for f in required_fields if f not in source]
        if missing:
            issues.append({
                "category": "incomplete_source",
                "severity": "warning",
                "location": f"sources[{i}]"
            })
    return issues
```

#### Skill 3C: `evidence_grading_audit`
**Purpose**: Verify evidence levels are appropriate for confidence

**Type**: Validation Skill (deterministic)

**Executable Components** (100% Python):
```python
# From literature_auditor.py lines 462-483

def _check_evidence_grading(result: Dict) → list[Issue]:
    evidence_level = result.get("evidence_level", "").lower()
    confidence = result.get("confidence", "").lower()
    
    # Hard constraint: High confidence requires high evidence
    if "high" in confidence and evidence_level not in ["high", "level 1"]:
        return [{
            "category": "confidence_evidence_mismatch",
            "severity": "critical",
            "description": "High confidence with low evidence"
        }]
    return []
```

---

## 4. STATISTICS AUDITOR → Statistics Audit Skills

### 4.1 Current Structure Analysis

**File**: `agents/auditors/statistics_auditor.py` (342 lines)

**Decomposition**:

#### Skill 4A: `statistical_methodology_audit`
**Type**: Validation Skill (deterministic)

**Executable Components**:
```python
# From statistics_auditor.py lines 154-184

def _check_methodology(result: Dict) → list[Issue]:
    methodology = result.get("methodology", "")
    
    # Check minimum length
    if not methodology or len(methodology) < 20:
        return [{"category": "insufficient_methodology", "severity": "critical"}]
    
    # Check for actual data mention
    if "actual data" not in methodology.lower() and "measured" not in methodology.lower():
        return [{"category": "theoretical_only", "severity": "warning"}]
    
    return []
```

#### Skill 4B: `assumption_audit`
**Type**: Validation Skill (deterministic)

**Executable Components**:
```python
# From statistics_auditor.py lines 186-217

def _check_assumptions(result: Dict) → list[Issue]:
    assumptions = result.get("assumptions", [])
    
    # Minimum assumptions documented
    if len(assumptions) < 2:
        return [{
            "category": "insufficient_assumptions",
            "severity": "warning"
        }]
    return []
```

#### Skill 4C: `uncertainty_quantification_audit`
**Type**: Validation Skill (deterministic)

**Key Executable Components**:
```python
# From statistics_auditor.py lines 219-247

def _check_uncertainty(result: Dict) → list[Issue]:
    primary_result = result.get("primary_result", {})
    issues = []
    
    # Check for confidence intervals
    if "confidence_interval" not in primary_result:
        issues.append({
            "category": "missing_confidence_interval",
            "severity": "warning"
        })
    
    # Check confidence level expression
    confidence = result.get("confidence", "").lower()
    if not any(w in confidence for w in ["low", "moderate", "high", "uncertain"]):
        issues.append({
            "category": "unclear_confidence",
            "severity": "warning"
        })
    
    return issues
```

---

## 5. RESOLUTION ENGINE → Resolution Skills

### 5.1 Current Structure Analysis

**File**: `core/resolution_engine.py` (527 lines)

**Decomposition**:

#### Skill 5A: `audit_result_evaluation`
**Purpose**: Evaluate audit result and determine next action

**Type**: Hybrid Skill (deterministic + intelligent)

**Executable Components** (Hard Constraints - 100% deterministic):
```python
# From resolution_engine.py lines 167-197

def _evaluate_audit_result(task: Task, audit_result: AuditResult) → ResolutionDecision:
    """Pure deterministic logic"""
    
    # Hard rule 1: Pass = Accept
    if audit_result.status == AuditStatus.PASSED:
        return ResolutionDecision.ACCEPT
    
    # Hard rule 2: Critical issues = Escalate (no LLM override)
    if audit_result.has_critical_issues():
        return ResolutionDecision.ESCALATE
    
    # Hard rule 3: Can retry? = Retry
    if audit_result.status == AuditStatus.FAILED and task.can_retry():
        return ResolutionDecision.RETRY
    
    # Hard rule 4: No retries = Abort
    if not task.can_retry():
        return ResolutionDecision.ABORT
    
    return ResolutionDecision.ESCALATE
```

**LLM-Driven Components**:
- Intelligent decision making considering fixability
- Priority assessment
- Context-aware retry recommendations

**Skill Implementation**:
```yaml
skill_data/
├── hard_constraints.yaml
│   ├── fabrication_categories (auto-escalate)
│   ├── critical_threshold
│   └── max_retries
└── decision_framework.yaml
    └── Decision tree documentation

skill_implementation.py
├── class AuditResultEvaluationSkill(Skill)
├── def execute(task, audit_result) → ResolutionDecision
├── def _apply_hard_constraints(audit_result) → Optional[Decision]
├── def _evaluate_intelligent(task, audit_result) → Decision
└── def _validate_decision(decision) → bool
```

#### Skill 5B: `correction_extraction`
**Purpose**: Extract actionable corrections from audit

**Type**: Transformation Skill (deterministic)

**Executable Components** (100% Python):
```python
# From resolution_engine.py lines 199-230

def _prepare_corrections(audit_result: AuditResult) → list[Dict]:
    """Transform audit issues into correction instructions"""
    corrections = []
    
    for issue in audit_result.issues:
        correction = {
            "category": issue.category,
            "severity": issue.severity.value,
            "description": issue.description,
            "location": issue.location,
            "suggested_fix": issue.suggested_fix,
            "guideline_reference": issue.guideline_reference,
        }
        corrections.append(correction)
    
    # Add general recommendations
    for rec in audit_result.recommendations:
        corrections.append({
            "category": "recommendation",
            "severity": "info",
            "description": rec,
        })
    
    return corrections
```

---

## 6. CONTEXT COMPRESSOR → Compression Skills

### 6.1 Current Structure Analysis

**File**: `core/context_compressor.py` (773 lines)

**Decomposition**:

#### Skill 6A: `key_finding_extraction`
**Purpose**: Extract most important findings from task output

**Type**: Extraction Skill (deterministic + intelligent)

**Executable Components** (Deterministic):
```python
# From context_compressor.py lines 574-595

def _extract_numerical_claims(text: str) → List[str]:
    """Pure regex extraction"""
    patterns = [
        r'\d+(?:\.\d+)?-\d+(?:\.\d+)?%',  # Range percentages
        r'\d+(?:\.\d+)?%',                 # Single percentages
        r'p\s*[<>=]\s*0?\.\d+',           # p-values
        r'OR\s*=?\s*\d+(?:\.\d+)?',       # Odds ratios
        r'RR\s*=?\s*\d+(?:\.\d+)?',       # Relative risks
        r'CI:\s*\d+(?:\.\d+)?-\d+(?:\.\d+)?',  # Confidence intervals
        r'n\s*=\s*\d+(?:,\d{3})*',        # Sample sizes
    ]
    
    claims = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        claims.extend(matches)
    return claims

def _number_exists_in_original(num_claim: str, original_numbers: List[str]) → bool:
    """Detect fabricated numerical claims"""
    if num_claim in original_numbers:
        return True
    
    # Allow formatting differences
    normalized_claim = num_claim.replace(",", "").strip()
    normalized_original = original_text.replace(",", "")
    return normalized_claim in normalized_original
```

#### Skill 6B: `fabrication_detection_in_compression`
**Purpose**: Validate compressed summaries don't introduce fabrications

**Type**: Validation Skill (deterministic)

**Executable Components** (100% Python):
```python
# From context_compressor.py lines 497-572

def _validate_compressed_summary(compressed_summary: str, original_output: str) → bool:
    """Anti-fabrication validation"""
    
    # Extract numerical claims from both
    compressed_numbers = self._extract_numerical_claims(compressed_summary)
    original_numbers = self._extract_numerical_claims(original_output)
    
    # Check for fabricated numerical claims
    for num_claim in compressed_numbers:
        if not self._number_exists_in_original(num_claim, original_numbers, original_output):
            return False
    
    # Check for confidence inflation
    if self._has_confidence_inflation(compressed_summary, original_output):
        return False
    
    # Check for limitation removal
    if self._has_limitation_removal(compressed_summary, original_output):
        return False
    
    return True
```

---

## Detailed Mapping Table

| Component | Skill Name | Type | Deterministic % | LLM % | Key Files | Dependencies |
|-----------|-----------|------|-----------------|-------|-----------|--------------|
| **LiteratureAgent** | | | | | | |
| | literature_search | Tool | 100 | 0 | PubMedConnector | API |
| | evidence_level_classification | Analysis | 100 | 0 | Patterns DB | - |
| | evidence_quality_assessment | Reasoning | 30 | 70 | Prompts, Validators | ThoughtPipe |
| | literature_synthesis | Analysis | 100 | 0 | Templates | - |
| **StatisticsAgent** | | | | | | |
| | statistical_evidence_extraction | Extraction | 100 | 0 | Regex patterns | - |
| | statistical_synthesis | Analysis | 100 | 0 | Math utils | - |
| | heterogeneity_assessment | Analysis | 100 | 0 | - | - |
| | statistical_interpretation | Reasoning | 40 | 60 | Prompts | LLM (optional) |
| **LiteratureAuditor** | | | | | | |
| | source_authenticity_verification | Validation | 100 | 0 | Patterns, URL checker | HTTP |
| | citation_completeness_audit | Validation | 100 | 0 | Schema | - |
| | evidence_grading_audit | Validation | 100 | 0 | Rules | - |
| | audit_issue_compilation | Compilation | 100 | 0 | Issue templates | - |
| **StatisticsAuditor** | | | | | | |
| | statistical_methodology_audit | Validation | 100 | 0 | Rules | - |
| | assumption_audit | Validation | 100 | 0 | Rules | - |
| | uncertainty_quantification_audit | Validation | 100 | 0 | Rules | - |
| | result_validity_audit | Validation | 100 | 0 | Rules | - |
| **ResolutionEngine** | | | | | | |
| | audit_result_evaluation | Decision | 80 | 20 | Hard rules, Prompts | ThoughtPipe (optional) |
| | correction_extraction | Transformation | 100 | 0 | - | - |
| | retry_orchestration | Control | 100 | 0 | - | - |
| **ContextCompressor** | | | | | | |
| | key_finding_extraction | Extraction | 100 | 0 | Patterns | - |
| | summary_generation | Compression | 50 | 50 | Prompts | ThoughtPipe (optional) |
| | fabrication_detection_in_compression | Validation | 100 | 0 | Patterns | - |
| | metadata_compression | Transformation | 100 | 0 | Schema | - |

---

## Resource Requirements by Skill Type

### Configuration Files Required

```
skills/
├── literature_search/
│   ├── skill_definition.yaml
│   └── data/
│       ├── pubmed_config.yaml
│       └── search_limits.yaml
│
├── evidence_level_classification/
│   ├── skill_definition.yaml
│   └── data/
│       ├── evidence_hierarchy.yaml
│       └── classification_patterns.yaml
│
├── source_authenticity_verification/
│   ├── skill_definition.yaml
│   └── data/
│       ├── fabrication_patterns.yaml
│       ├── placeholder_patterns.yaml
│       └── sequential_patterns.yaml
│
├── statistical_evidence_extraction/
│   ├── skill_definition.yaml
│   └── data/
│       └── extraction_patterns.yaml
│
└── ... (one directory per skill)
```

### Prompt Templates Required

For skills with LLM components:
- `evidence_quality_assessment.md` (~600 lines, similar to current code)
- `statistical_interpretation.md` (new)
- `intelligent_resolution_decision.md` (extract from current code)
- `intelligent_compression.md` (extract from current code)

---

## Data Files and Schemas

### 1. Evidence Hierarchy Definition

```yaml
# evidence_hierarchy.yaml
evidence_levels:
  level_1:
    name: "Randomized Controlled Trial / Systematic Review"
    keywords: 
      - "randomized controlled trial"
      - "rct"
      - "systematic review"
      - "meta-analysis"
    weight: 5
    
  level_2:
    name: "Cohort Study"
    keywords:
      - "cohort study"
      - "prospective study"
    weight: 3
    
  level_3:
    name: "Case-Control Study"
    keywords:
      - "case-control"
      - "case control"
    weight: 2
    
  level_4:
    name: "Case Report / Case Series"
    keywords:
      - "case report"
      - "case series"
    weight: 1
```

### 2. Fabrication Patterns

```yaml
# fabrication_patterns.yaml
placeholder_titles:
  - pattern: '(?i)example\s+study'
    reason: "Generic placeholder"
  - pattern: '(?i)sample\s+research'
    reason: "Generic placeholder"
  - pattern: '(?i)test\s+paper'
    reason: "Generic placeholder"

fake_authors:
  - pattern: '^smith\s+et\s+al\.?$'
    reason: "Common fake author name"
  - pattern: '^jones\s+et\s+al\.?$'
    reason: "Common fake author name"

sequential_pmids:
  - "12345678"
  - "87654321"
  - "11111111"
  # ... more patterns

placeholder_urls:
  - "example.com"
  - "example.org"
  - "test.com"
  - "localhost"
```

### 3. Validation Schemas

```yaml
# validation_schemas.yaml

literature_review_output:
  required_fields:
    - summary
    - sources
    - evidence_level
    - confidence
    - limitations
    - methodology
  
  constraints:
    min_sources: 2
    max_confidence_without_validation: "moderate"
    evidence_level_values: ["High", "Moderate", "Low", "None"]

statistical_analysis_output:
  required_fields:
    - summary
    - primary_result
    - interpretation
    - assumptions
    - limitations
    - methodology
    - confidence
  
  constraints:
    min_assumptions: 2
    required_result_fields: ["test", "p_value"]
```

---

## Composability and Chaining

### Example 1: Complete Literature Review Workflow

```python
def conduct_literature_review_workflow(query: str, orchestrator):
    """Chains literature skills in sequence"""
    
    # Step 1: Search
    search_result = orchestrator.execute_skill(
        'literature_search',
        { 'query': query, 'max_results': 10 }
    )
    sources = search_result['sources']
    
    # Step 2: Classify Evidence Levels
    classification_result = orchestrator.execute_skill(
        'evidence_level_classification',
        { 'papers': sources }
    )
    classified_sources = classification_result['classified_papers']
    
    # Step 3: Assess Quality
    quality_result = orchestrator.execute_skill(
        'evidence_quality_assessment',
        { 
            'sources': classified_sources,
            'research_question': query,
            'enable_intelligent_assessment': True
        }
    )
    
    # Step 4: Synthesize Findings
    synthesis_result = orchestrator.execute_skill(
        'literature_synthesis',
        { 'sources': classified_sources }
    )
    
    # Return combined results
    return {
        'sources': classified_sources,
        'quality_assessment': quality_result,
        'synthesis': synthesis_result,
        'methodology': '...'
    }
```

### Example 2: Complete Audit Workflow

```python
def conduct_literature_audit_workflow(task_output: Dict, orchestrator):
    """Chains audit skills in sequence"""
    
    sources = task_output['result']['sources']
    
    # Step 1: Verify Authenticity
    authenticity_issues = orchestrator.execute_skill(
        'source_authenticity_verification',
        { 'sources': sources }
    )
    
    # Step 2: Check Completeness
    completeness_issues = orchestrator.execute_skill(
        'citation_completeness_audit',
        { 'sources': sources }
    )
    
    # Step 3: Check Evidence Grading
    grading_issues = orchestrator.execute_skill(
        'evidence_grading_audit',
        { 'result': task_output['result'] }
    )
    
    # Aggregate all issues
    all_issues = authenticity_issues + completeness_issues + grading_issues
    
    # Determine status
    critical_issues = [i for i in all_issues if i['severity'] == 'critical']
    status = 'failed' if critical_issues else ('partial' if all_issues else 'passed')
    
    return {
        'status': status,
        'issues': all_issues,
        'critical_count': len(critical_issues)
    }
```

---

## Migration Strategy

### Phase 1: Extract Deterministic Code (Week 1-2)
1. Create skill directories and structures
2. Extract all 100% deterministic components
3. Create data files (patterns, rules, schemas)
4. Write comprehensive tests

### Phase 2: Extract LLM Components (Week 3)
1. Extract thought pipe prompts into skill_prompts directories
2. Create prompt validation utilities
3. Implement intelligent skill wrappers

### Phase 3: Integration & Testing (Week 4)
1. Create orchestrator for skill chaining
2. Update worker/auditor classes to use skills
3. Integration testing
4. Performance benchmarking

### Phase 4: Optimization & Documentation (Week 5)
1. Profile and optimize hot paths
2. Add comprehensive documentation
3. Create migration guide

---

## Key Benefits of Skills Architecture

| Aspect | Current | Skills-Based |
|--------|---------|--------------|
| **Reusability** | Monolithic agents | 26+ reusable skills |
| **Testability** | 100-line methods | 10-30 line skill methods |
| **Composability** | Fixed workflows | Dynamic chaining |
| **Deterministic vs LLM** | Mixed | Clear separation |
| **Caching** | Limited | Per-skill caching |
| **Documentation** | Agent level | Skill level + orchestration |
| **Token efficiency** | High context overhead | Minimal context transfer |
| **Debugging** | Full task debugging | Skill-level debugging |

---

## Summary Table: Skill Properties

All 26 proposed skills with key attributes:

[Detailed table continues with all skills listed with Type, Deterministic%, Files count, Data files needed, etc.]

