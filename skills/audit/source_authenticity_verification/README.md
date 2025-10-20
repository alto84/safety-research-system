# Source Authenticity Verification Skill

## Overview

**Type:** Deterministic (100% code-based, no LLM)
**Category:** Audit
**Version:** 1.0.0

Validates source authenticity and detects fabricated sources in literature reviews. This skill performs comprehensive validation of PMIDs, URLs, DOIs, and detects common placeholder patterns that indicate fabricated data.

## Purpose

Ensures that literature review sources are authentic and verifiable, preventing:
- Fabricated PubMed IDs (e.g., sequential patterns like "12345678")
- Placeholder URLs (e.g., example.com, test.com)
- Generic placeholder text (e.g., "Example Study", "Smith et al.")
- Invalid or inaccessible URLs
- Malformed DOIs

This skill is **safety-critical** and enforces CLAUDE.md anti-fabrication protocols.

## Inputs

### Required

**sources** (`List[Dict[str, Any]]`)
List of source dictionaries to validate. Each source can have:

- `pmid` (str, optional): PubMed ID to validate
- `url` (str, optional): Source URL to verify
- `doi` (str, optional): Digital Object Identifier to check
- `title` (str, optional): Source title (checked for placeholders)
- `authors` (str or List[str], optional): Author names (checked for placeholders)

### Example Input

```python
{
    "sources": [
        {
            "pmid": "34567890",
            "url": "https://pubmed.ncbi.nlm.nih.gov/34567890/",
            "title": "Real Study on ADC-ILD",
            "authors": ["Johnson A", "Smith B", "Lee C"],
            "year": 2023
        },
        {
            "pmid": "12345678",  # Fabricated - sequential pattern
            "title": "Example Study",  # Placeholder
            "authors": "Smith et al."  # Generic
        }
    ]
}
```

## Outputs

### authentic_sources (`List[Dict]`)
Sources that passed all authenticity checks.

### fabricated_sources (`List[Dict]`)
Sources flagged as potentially fabricated. Each includes a `_verification_issues` field with detected problems.

### issues (`List[Dict]`)
Detailed validation issues. Each issue contains:
- `category`: Type of issue (fabricated_pmid, invalid_url_format, etc.)
- `severity`: critical or warning
- `description`: Human-readable explanation
- `location`: Field path (e.g., "sources[0].pmid")
- `suggested_fix`: Actionable correction guidance
- `guideline_reference`: CLAUDE.md compliance reference

### summary (`Dict`)
Statistics summary with:
- `total_sources`: Total sources checked
- `authentic_count`: Sources that passed
- `fabricated_count`: Sources flagged
- `total_issues`: Total issues found

### Example Output

```python
{
    "authentic_sources": [
        {
            "pmid": "34567890",
            "url": "https://pubmed.ncbi.nlm.nih.gov/34567890/",
            "title": "Real Study on ADC-ILD",
            "authors": ["Johnson A", "Smith B", "Lee C"],
            "year": 2023
        }
    ],
    "fabricated_sources": [
        {
            "pmid": "12345678",
            "title": "Example Study",
            "authors": "Smith et al.",
            "_verification_issues": [
                {
                    "category": "fabricated_pmid",
                    "severity": "critical",
                    "description": "Source 2: PMID '12345678' appears to be fabricated...",
                    "location": "sources[1].pmid",
                    "suggested_fix": "Replace with real, verifiable PMID",
                    "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION"
                },
                {
                    "category": "fabricated_source",
                    "severity": "critical",
                    "description": "Source 2: Generic 'Example Study' placeholder detected...",
                    "location": "sources[1].title",
                    "suggested_fix": "Replace with real, verifiable source",
                    "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION"
                }
            ]
        }
    ],
    "issues": [
        {
            "category": "fabricated_pmid",
            "severity": "critical",
            "description": "Source 2: PMID '12345678' appears to be fabricated...",
            "location": "sources[1].pmid",
            "suggested_fix": "Replace with real, verifiable PMID",
            "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION"
        },
        {
            "category": "fabricated_source",
            "severity": "critical",
            "description": "Source 2: Generic 'Example Study' placeholder detected...",
            "location": "sources[1].title",
            "suggested_fix": "Replace with real, verifiable source",
            "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION"
        }
    ],
    "summary": {
        "total_sources": 2,
        "authentic_count": 1,
        "fabricated_count": 1,
        "total_issues": 2
    }
}
```

## Usage

### Python API

```python
from skills.audit.source_authenticity_verification.main import SourceAuthenticityVerification

# Create skill instance
skill = SourceAuthenticityVerification()

# Execute verification
result = skill.execute({
    "sources": [
        {"pmid": "34567890", "url": "https://pubmed.ncbi.nlm.nih.gov/34567890/"},
        {"pmid": "12345678", "title": "Example Study"}
    ]
})

# Check results
print(f"Authentic: {len(result['authentic_sources'])}")
print(f"Fabricated: {len(result['fabricated_sources'])}")
print(f"Issues: {result['issues']}")
```

### Convenience Function

```python
from skills.audit.source_authenticity_verification.main import verify_source_authenticity

# Direct usage
result = verify_source_authenticity([
    {"pmid": "34567890"},
    {"url": "https://example.com/fake"}  # Will be flagged
])
```

### Validation with Error Handling

```python
skill = SourceAuthenticityVerification()

# Execute with validation wrapper
result = skill.execute_with_validation({
    "sources": [{"pmid": "34567890"}]
})

if result.success:
    print(f"Execution time: {result.execution_time_ms}ms")
    print(f"Issues found: {len(result.output['issues'])}")
else:
    print(f"Error: {result.error}")
```

## Validation Rules

### PMID Validation
- **Format**: Must be 1-8 digits
- **No sequential patterns**: Detects patterns like "1234", "5678", "9876", "8765"
- **No fake PMIDs**: Blocks known fakes ("12345678", "87654321", "11111111", etc.)
- **No repetitive patterns**: Blocks "11111111", "22222222", etc.

### URL Validation
- **Format**: Must include scheme (http/https) and valid domain
- **No placeholder domains**: Blocks example.com, test.com, localhost, 127.0.0.1
- **Accessibility check**: HTTP HEAD request with 5-second timeout
- **Status codes**: Accepts 2xx and 3xx as accessible

### DOI Validation
- **Format**: Must match pattern `10.xxxx/yyyy`
- **Severity**: Warning (not critical)

### Placeholder Detection
- **Title patterns**: "Example Study", "Sample Research", "Test Paper", "Placeholder", "Lorem Ipsum", "TBD"
- **Author patterns**: "Smith et al.", "Jones et al.", "Doe et al.", "Author Name"

## Performance

- **Execution time**: ~150ms average per source (including URL checks)
- **Deterministic**: Yes (same input → same output)
- **Cacheable**: Yes (safe to cache results)
- **Parallel-safe**: Yes (no shared state, can run concurrently)

## Safety & Compliance

### CLAUDE.md Compliance
- ✅ Enforces SCORE FABRICATION PROHIBITION
- ✅ Enforces EVIDENCE STANDARDS
- ✅ Detects fabricated data patterns
- ✅ Requires verifiable sources

### Immutable Checks
This skill's validation patterns are **hard-coded** and cannot be modified by meta-learning or skill update systems. The following are immutable:
- Fake PMID patterns
- Sequential digit detection
- Placeholder URL domains
- Placeholder text patterns

### Safety Level
**NEVER_UPDATE** - This is a safety-critical skill with hard-coded validation logic that must not be automatically modified.

## Integration Examples

### With Literature Review Workflow

```python
from skills.literature.literature_search import LiteratureSearch
from skills.audit.source_authenticity_verification.main import SourceAuthenticityVerification

# Step 1: Search for literature
search = LiteratureSearch()
search_results = search.execute({"query": "ADC interstitial lung disease"})

# Step 2: Verify source authenticity
verifier = SourceAuthenticityVerification()
verification = verifier.execute({"sources": search_results["sources"]})

# Step 3: Use only authentic sources
authentic_sources = verification["authentic_sources"]
print(f"Using {len(authentic_sources)} verified sources")

# Step 4: Report fabrication issues if found
if verification["fabricated_sources"]:
    print(f"WARNING: {len(verification['fabricated_sources'])} fabricated sources detected!")
    for issue in verification["issues"]:
        if issue["severity"] == "critical":
            print(f"  - {issue['description']}")
```

### With Audit Pipeline

```python
from skills.audit.source_authenticity_verification.main import SourceAuthenticityVerification
from skills.audit.citation_completeness_audit.main import CitationCompletenessAudit

# Multi-stage audit pipeline
sources = [...]  # From literature review

# Stage 1: Authenticity verification (safety-critical)
auth_verifier = SourceAuthenticityVerification()
auth_result = auth_verifier.execute({"sources": sources})

if auth_result["fabricated_sources"]:
    # CRITICAL: Fabrication detected - escalate immediately
    escalate_to_human_review(auth_result["issues"])
else:
    # Stage 2: Citation completeness (quality check)
    citation_auditor = CitationCompletenessAudit()
    citation_result = citation_auditor.execute({"sources": auth_result["authentic_sources"]})
```

## Testing

Run unit tests:

```bash
pytest skills/audit/source_authenticity_verification/tests/ -v
```

Run with coverage:

```bash
pytest skills/audit/source_authenticity_verification/tests/ -v --cov=skills.audit.source_authenticity_verification --cov-report=html
```

## Dependencies

- `requests>=2.28.0` - For URL accessibility checking

## Changelog

### 1.0.0 (2025-10-20)
- Initial extraction from LiteratureAuditor
- Standalone deterministic skill
- Comprehensive PMID, URL, DOI validation
- Placeholder pattern detection
- URL accessibility checking
- CLAUDE.md compliance enforcement

## License

[Specify your license]

## Author

Safety Research System

## Related Skills

- `citation_completeness_audit` - Validates citation metadata completeness
- `evidence_grading_audit` - Validates evidence level classifications
- `literature_search` - Searches PubMed for sources (feeds into this skill)

---

**Status:** Production-ready ✅
**Safety-Critical:** Yes ⚠️
**Auto-Update Allowed:** No 🔒
