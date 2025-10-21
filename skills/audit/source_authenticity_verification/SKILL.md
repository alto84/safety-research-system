---
name: source-authenticity-verification
description: Validates source authenticity and detects fabricated sources. Use when literature review outputs need verification for fabricated PMIDs (sequential patterns like "12345678"), placeholder URLs (example.com, test.com), or generic placeholder text ("Example Study", "Smith et al."). Critical for CLAUDE.md anti-fabrication compliance.
license: See repository LICENSE
allowed-tools:
  - Read
  - Bash
---

# Source Authenticity Verification

## Overview

Validates literature review sources for authenticity, detecting fabricated PMIDs, placeholder URLs, and generic source data. This skill enforces CLAUDE.md anti-fabrication protocols through deterministic pattern matching and HTTP verification.

## When to Use This Skill

Use this skill to validate sources when:
- **Literature review outputs** contain PMIDs, URLs, or DOIs requiring verification
- **Audit phase** needs to check worker agent outputs for fabricated data
- **CLAUDE.md compliance** requires anti-fabrication enforcement
- **Source authenticity** is critical for pharmaceutical safety assessments

## Quick Start

```python
from skills.audit.source_authenticity_verification.scripts.verify import verify_source_authenticity

# Validate a list of sources
result = verify_source_authenticity([
    {
        "pmid": "31415927",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31415927/",
        "title": "Real Study on ADC-ILD",
        "authors": ["Johnson A", "Smith B"]
    },
    {
        "pmid": "12345678",  # Will be flagged as fabricated
        "title": "Example Study"  # Placeholder detected
    }
])

print(f"Authentic: {len(result['authentic_sources'])}")
print(f"Fabricated: {len(result['fabricated_sources'])}")
for issue in result['issues']:
    print(f"  - {issue['category']}: {issue['description']}")
```

## Validation Operations

### PMID Validation

Detects fabricated PubMed IDs through pattern matching:

**Format validation:**
- Must be 1-8 digits only
- Rejects non-numeric characters
- Severity: CRITICAL

**Known fake patterns:**
- Sequential numbers: "12345678", "87654321"
- Repetitive patterns: "11111111", "22222222", "33333333"
- Severity: CRITICAL

**Sequential digit detection:**
- Ascending: "1234", "2345", "3456", "4567", "5678", "6789"
- Descending: "9876", "8765", "7654", "6543", "5432", "4321"
- Severity: CRITICAL

Example:
```python
# Good PMIDs (realistic)
"31415927", "27182818", "16180339"

# Bad PMIDs (fabricated)
"12345678"  # Sequential pattern detected
"11111111"  # Repetitive pattern
"abc12345"  # Invalid format
```

### URL Validation

Verifies URL format, detects placeholders, and checks accessibility:

**Format requirements:**
- Must include scheme (http/https)
- Must include valid domain
- Uses Python's `urlparse` for validation
- Severity: CRITICAL if malformed

**Placeholder detection:**
- example.com, example.org
- test.com, fake.com, dummy.com
- localhost, 127.0.0.1
- Severity: CRITICAL

**Accessibility check:**
- HTTP HEAD request with 5-second timeout
- Accepts 2xx and 3xx status codes
- Severity: CRITICAL if inaccessible
- Note: May fail in restricted network environments

Example:
```python
# Good URLs
"https://pubmed.ncbi.nlm.nih.gov/31415927/"
"https://www.nature.com/articles/nature12345"

# Bad URLs
"https://example.com/study"  # Placeholder domain
"not-a-valid-url"  # Missing scheme
"http://localhost/test"  # Localhost placeholder
```

### DOI Validation

Validates Digital Object Identifier format:

**Format:** `10.xxxx/yyyy`
- Must start with "10."
- Followed by 4+ digit registrant code
- Followed by "/" and suffix
- Severity: WARNING (not critical)

Example:
```python
# Valid DOIs
"10.1234/example.2023"
"10.1038/nature12345"

# Invalid DOIs
"invalid-doi"  # Wrong format
"10.12/x"  # Registrant code too short
```

### Placeholder Text Detection

Identifies generic placeholder text in titles and authors:

**Title patterns:**
- "Example Study", "Sample Research"
- "Test Paper", "Placeholder"
- "Lorem Ipsum", "To Be Determined", "TBD"
- Severity: CRITICAL

**Author patterns:**
- "Smith et al.", "Jones et al.", "Doe et al."
- "Author Name"
- Standalone "et al." without actual authors
- Severity: CRITICAL

Example:
```python
# Good sources
title: "Antibody-Drug Conjugates in Interstitial Lung Disease: A Systematic Review"
authors: ["Johnson A", "Smith B", "Lee C"]

# Bad sources (placeholders)
title: "Example Study on ADC"  # Flagged
authors: "Smith et al."  # Flagged as too generic
```

## Output Structure

The skill returns a structured result with three main components:

**authentic_sources** (List[Dict])
- Sources that passed all validation checks
- No critical issues detected
- Safe to use in literature review

**fabricated_sources** (List[Dict])
- Sources flagged with one or more critical issues
- Includes `_verification_issues` field with details
- Should be rejected or require manual review

**issues** (List[Dict])
- Detailed validation issues found
- Each issue contains:
  - `category`: Issue type (fabricated_pmid, invalid_url_format, etc.)
  - `severity`: critical or warning
  - `description`: Human-readable explanation
  - `location`: Field path (e.g., "sources[0].pmid")
  - `suggested_fix`: Actionable correction guidance
  - `guideline_reference`: CLAUDE.md compliance reference

**summary** (Dict)
- `total_sources`: Total sources checked
- `authentic_count`: Sources that passed
- `fabricated_count`: Sources flagged
- `total_issues`: Total issues found

## Integration Patterns

### With Literature Review Workflow

```python
from skills.literature.literature_search import search_literature
from skills.audit.source_authenticity_verification.scripts.verify import verify_source_authenticity

# Step 1: Search for literature
sources = search_literature("ADC interstitial lung disease")

# Step 2: Verify source authenticity
verification = verify_source_authenticity(sources)

# Step 3: Use only authentic sources
if verification["fabricated_sources"]:
    print(f"WARNING: {len(verification['fabricated_sources'])} fabricated sources detected!")
    for issue in verification["issues"]:
        if issue["severity"] == "critical":
            print(f"  CRITICAL: {issue['description']}")

# Step 4: Proceed with authentic sources only
authenticated_sources = verification["authentic_sources"]
```

### With Audit Pipeline

```python
from skills.audit.source_authenticity_verification.scripts.verify import verify_source_authenticity
from skills.audit.citation_completeness import check_citation_completeness

# Multi-stage audit
sources = get_literature_review_output()

# Stage 1: Authenticity (safety-critical)
auth_result = verify_source_authenticity(sources)

if auth_result["fabricated_sources"]:
    # CRITICAL: Escalate immediately
    return {
        "status": "failed",
        "reason": "fabrication_detected",
        "issues": auth_result["issues"]
    }

# Stage 2: Citation completeness (quality check)
citation_result = check_citation_completeness(auth_result["authentic_sources"])
```

## Performance Characteristics

- **Execution time**: ~150ms average per source
- **Deterministic**: Same input → same output (100% reproducible)
- **Cacheable**: Results can be safely cached
- **Parallel-safe**: No shared state, can run concurrently
- **Network dependent**: URL accessibility checks require network access

## Safety & CLAUDE.md Compliance

### Immutable Validation Patterns

The following validation patterns are **hard-coded** and cannot be modified by meta-learning systems:

- Fake PMID list (12345678, 87654321, etc.)
- Sequential digit patterns
- Placeholder URL domains
- Placeholder text patterns

These patterns enforce CLAUDE.md anti-fabrication protocols and are **safety-critical**.

### Severity Levels

**CRITICAL** (must fix):
- Fabricated PMIDs, URLs, sources
- Invalid PMID/URL formats
- Inaccessible URLs
- Placeholder text in titles/authors

**WARNING** (should fix):
- Invalid DOI format
- Missing recommended fields

### Auto-Update Policy

This skill is marked **NEVER_UPDATE** for automated modifications. Validation logic is safety-critical and requires human review for any changes.

## Resources

### scripts/verify.py

Main implementation of source authenticity verification. Contains:
- `SourceAuthenticityVerification` class (full implementation)
- `verify_source_authenticity()` convenience function
- All validation methods (PMID, URL, DOI, placeholder detection)
- See scripts/verify.py for full API documentation

### tests/

Comprehensive test suite with 32 unit tests covering:
- Input validation
- PMID validation (format, fabrication, sequential patterns)
- URL validation (format, placeholders, accessibility)
- DOI validation
- Placeholder detection
- Multiple sources handling
- Error handling
- Performance metrics

Run tests:
```bash
pytest skills/audit/source_authenticity_verification/tests/ -v
```

## Limitations

1. **Network dependency**: URL accessibility checks require outbound HTTP access. May fail in:
   - Restricted network environments
   - Air-gapped systems
   - Firewall-blocked domains

2. **False positives**: Legitimate PMIDs containing sequential digits may be flagged (rare but possible)

3. **DOI coverage**: Only validates format, not authenticity (would require CrossRef API)

4. **Language**: Placeholder detection patterns are English-centric

## Version History

- **1.0.0** (2025-10-20): Initial extraction from LiteratureAuditor, full Anthropic skills format
