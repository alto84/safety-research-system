---
name: evidence-level-classification
description: Classify research evidence quality using GRADE methodology. Use this skill when processing literature reviews, systematic reviews, or any research papers that need quality assessment. Automatically determines evidence levels (I through III) based on study design, type, and keywords.
---

# Evidence Level Classification

## Overview

This skill provides deterministic classification of research evidence quality based on the GRADE (Grading of Recommendations Assessment, Development and Evaluation) methodology and USPSTF (U.S. Preventive Services Task Force) evidence hierarchy. It analyzes study characteristics to assign evidence levels ranging from Level I (highest quality: systematic reviews) to Level III (lowest quality: descriptive studies).

**When to use this skill:**
- Processing literature reviews that need quality assessment
- Building evidence databases with quality ratings
- Conducting systematic reviews or meta-analyses
- Evaluating research for safety assessments or clinical guidelines
- Automating evidence hierarchy classification in research pipelines

## Quick Start

### Basic Classification

```python
from skills.literature.evidence_level_classification.scripts.classify import classify_evidence_level

# Classify a systematic review
source = {
    "study_type": "systematic review",
    "title": "Safety interventions in AI systems: A systematic review"
}
level = classify_evidence_level(source)
print(f"Evidence Level: {level}")  # Output: I
```

### Classification with Details

```python
from skills.literature.evidence_level_classification.scripts.classify import classify_with_details

source = {
    "study_type": "randomized controlled trial",
    "title": "Effects of safety training on AI developer behavior",
    "abstract": "This double-blind RCT examined..."
}

result = classify_with_details(source)
print(f"Level: {result['level']}")           # II-1
print(f"Name: {result['name']}")             # Individual RCTs
print(f"Description: {result['description']}")  # Evidence from well-designed RCTs
```

## Evidence Hierarchy

The classification follows a strict hierarchy based on GRADE methodology:

### Level I: Systematic Reviews and Meta-Analyses
**Highest quality evidence**

- Systematic reviews of randomized controlled trials
- Meta-analyses combining multiple studies
- Cochrane reviews
- Umbrella reviews

**Keywords triggering Level I:**
- "systematic review"
- "meta-analysis"
- "cochrane review"
- "systematic literature review"

**Example:**
```python
source = {"title": "A meta-analysis of AI safety interventions"}
classify_evidence_level(source)  # Returns: "I"
```

### Level II-1: Individual RCTs
**High quality evidence**

- Well-designed randomized controlled trials
- Double-blind placebo-controlled studies
- Studies with random allocation

**Keywords triggering Level II-1:**
- "randomized controlled trial" / "randomised controlled trial"
- "rct"
- "randomized" / "randomised" (in study_type or study_design)
- "double-blind" / "double blind"
- "placebo-controlled"

**Example:**
```python
source = {
    "study_type": "RCT",
    "abstract": "This double-blind study randomized participants..."
}
classify_evidence_level(source)  # Returns: "II-1"
```

### Level II-2: Cohort Studies
**Moderate quality evidence**

- Prospective cohort studies
- Longitudinal studies
- Follow-up studies

**Keywords triggering Level II-2:**
- "cohort" / "cohort study"
- "prospective" / "prospective study"
- "longitudinal" / "longitudinal study"
- "follow-up study"

**Example:**
```python
source = {"study_design": "prospective cohort"}
classify_evidence_level(source)  # Returns: "II-2"
```

### Level II-3: Case-Control Studies
**Lower-moderate quality evidence**

- Retrospective case-control studies
- Matched case-control designs

**Keywords triggering Level II-3:**
- "case-control" / "case control"
- "case-control study" / "case control study"

**Example:**
```python
source = {"study_type": "case-control study"}
classify_evidence_level(source)  # Returns: "II-3"
```

### Level III: Descriptive Studies
**Lowest quality evidence (default)**

- Case series
- Case reports
- Expert opinion
- Narrative reviews
- Commentaries
- Any unrecognized study types

**Keywords triggering Level III:**
- "case series"
- "case report"
- "expert opinion"
- "narrative review"
- "commentary"
- Any text that doesn't match higher levels

**Example:**
```python
source = {"study_type": "case series"}
classify_evidence_level(source)  # Returns: "III"

# Unknown or missing study types also default to III
source = {}
classify_evidence_level(source)  # Returns: "III"
```

## Classification Logic

The classification uses a hierarchical decision tree:

```
1. Check for Level I keywords (systematic review, meta-analysis)
   → If found: Return "I"

2. Check for Level II-1 keywords (RCT, randomized, double-blind)
   → If found: Return "II-1"

3. Check for Level II-2 keywords (cohort, prospective, longitudinal)
   → If found: Return "II-2"

4. Check for Level II-3 keywords (case-control)
   → If found: Return "II-3"

5. Default: Return "III"
```

**Key features:**
- **Deterministic**: Always produces the same result for the same input
- **Case-insensitive**: "RCT", "rct", and "Rct" are all recognized
- **Multi-field**: Searches across study_type, study_design, title, and abstract
- **Priority-based**: Higher quality levels take precedence (e.g., "systematic review of RCTs" → Level I)
- **Whitespace-tolerant**: Extra spaces don't affect matching

## Input Format

The `classify_evidence_level()` function expects a dictionary with these optional keys:

```python
source = {
    "study_type": str,          # Type of study (e.g., "RCT", "cohort study")
    "study_design": str,        # Design characteristics (e.g., "randomized", "prospective")
    "title": str,               # Study title
    "abstract": str,            # Study abstract
    "quality_indicators": dict  # Optional: Quality assessment (not currently used)
}
```

All fields are optional. The function searches across all provided text fields for classification keywords.

## Integration Patterns

### Pattern 1: Batch Classification

```python
from skills.literature.evidence_level_classification.scripts.classify import classify_with_details

sources = [
    {"study_type": "systematic review", "title": "AI Safety Literature"},
    {"study_type": "RCT", "title": "Safety Training Effectiveness"},
    {"study_type": "case report", "title": "Single Case of Misalignment"}
]

for source in sources:
    result = classify_with_details(source)
    print(f"{result['level']}: {source['title']}")
```

### Pattern 2: Evidence Database Population

```python
import json
from skills.literature.evidence_level_classification.scripts.classify import classify_evidence_level

# Load literature database
with open("literature.json", "r") as f:
    literature = json.load(f)

# Add evidence levels
for paper in literature:
    paper["evidence_level"] = classify_evidence_level(paper)

# Save updated database
with open("literature_with_levels.json", "w") as f:
    json.dump(literature, f, indent=2)
```

### Pattern 3: Quality Filtering

```python
from skills.literature.evidence_level_classification.scripts.classify import classify_evidence_level

def filter_high_quality(sources, min_level="II-1"):
    """Filter sources to only high-quality evidence."""
    level_ranking = {"I": 1, "II-1": 2, "II-2": 3, "II-3": 4, "III": 5}
    min_rank = level_ranking.get(min_level, 5)

    high_quality = []
    for source in sources:
        level = classify_evidence_level(source)
        if level_ranking.get(level, 5) <= min_rank:
            high_quality.append(source)

    return high_quality
```

### Pattern 4: Evidence Summary Statistics

```python
from collections import Counter
from skills.literature.evidence_level_classification.scripts.classify import classify_evidence_level

def summarize_evidence_quality(sources):
    """Generate summary statistics of evidence quality."""
    levels = [classify_evidence_level(source) for source in sources]
    counter = Counter(levels)

    total = len(levels)
    for level in ["I", "II-1", "II-2", "II-3", "III"]:
        count = counter.get(level, 0)
        pct = (count / total * 100) if total > 0 else 0
        print(f"Level {level}: {count} ({pct:.1f}%)")
```

## Testing

The skill includes comprehensive tests covering all evidence levels, edge cases, and helper functions.

### Running Tests

```bash
# Run all tests
cd skills/literature/evidence-level-classification
python -m pytest tests/test_evidence_classification.py -v

# Run specific test class
python -m pytest tests/test_evidence_classification.py::TestEvidenceLevelI -v

# Run with coverage
python -m pytest tests/test_evidence_classification.py --cov=scripts.classify
```

### Test Coverage

The test suite includes 30+ tests covering:
- All five evidence levels (I, II-1, II-2, II-3, III)
- Keyword matching across all fields
- Case insensitivity
- British vs American spelling (randomised vs randomized)
- Edge cases (empty inputs, conflicting keywords, whitespace)
- Helper functions (get_level_description, classify_with_details)
- Determinism verification

## Reference Materials

### Evidence Hierarchy YAML

The `references/evidence_hierarchy.yaml` file contains the complete evidence hierarchy definition:

```yaml
levels:
  I:
    name: "Systematic reviews and meta-analyses"
    description: "Evidence from systematic reviews of RCTs"
    keywords: ["systematic review", "meta-analysis", "cochrane"]
  # ... (see file for complete hierarchy)
```

This reference file documents the classification system and can be loaded programmatically if needed.

## Limitations and Considerations

1. **Keyword-based**: Classification relies on keyword matching, not deep semantic understanding
2. **Quality not assessed**: The skill assigns evidence *level* based on study design, not study *quality*
   - A poorly-designed RCT still gets Level II-1
   - Quality assessment requires human judgment or additional validation
3. **No context awareness**: Doesn't consider domain-specific evidence hierarchies
4. **Binary classification**: Each source gets exactly one level; no confidence scores
5. **No full-text analysis**: Only examines provided fields (study_type, title, abstract)

## Best Practices

1. **Provide multiple fields**: Include study_type, title, and abstract for better accuracy
2. **Validate critical classifications**: Review Level I and II-1 classifications manually
3. **Use consistently**: Apply to all sources in a literature review for fair comparison
4. **Document assumptions**: Note any manual overrides or special cases
5. **Combine with quality assessment**: Use GRADE or similar frameworks for comprehensive evaluation

## Resources

### scripts/
- `classify.py`: Main classification logic with three public functions:
  - `classify_evidence_level(source)`: Returns evidence level string
  - `get_level_description(level)`: Returns human-readable description
  - `classify_with_details(source)`: Returns level + full details

### references/
- `evidence_hierarchy.yaml`: Complete evidence hierarchy definition with keywords

### tests/
- `test_evidence_classification.py`: Comprehensive test suite (30+ tests)
