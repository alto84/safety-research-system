---
name: statistical-evidence-extraction
description: Extract statistical evidence (hazard ratios, odds ratios, p-values, confidence intervals, sample sizes, percentages) from medical and scientific text using deterministic regex-based pattern matching. Use when analyzing research papers, abstracts, clinical trial results, or systematic reviews to identify and structure quantitative findings.
---

# Statistical Evidence Extraction

## Overview

This skill provides deterministic, regex-based extraction of statistical evidence from medical and scientific literature. It identifies and structures key statistical measures including effect sizes (hazard ratios, odds ratios, risk ratios), significance values (p-values), precision estimates (confidence intervals), study characteristics (sample sizes), and proportions (percentages).

The extraction is **100% deterministic** and uses carefully crafted regex patterns to identify statistical values and their surrounding context, making it ideal for systematic literature reviews, meta-analyses, evidence synthesis, and research quality assessment.

## When to Use This Skill

Use this skill when you need to:

- **Extract statistics from abstracts**: Quickly identify key findings from PubMed abstracts or systematic review summaries
- **Process full-text articles**: Extract all statistical evidence from methods, results, and discussion sections
- **Systematic reviews**: Collect effect sizes and confidence intervals for meta-analysis
- **Evidence synthesis**: Aggregate statistical findings across multiple studies
- **Research quality assessment**: Verify statistical reporting completeness (effect size + CI + p-value)
- **Regulatory submissions**: Extract safety and efficacy data from clinical trial reports
- **Literature screening**: Filter papers based on presence of specific statistical evidence

**Trigger patterns:**
- "Extract statistics from this abstract"
- "Find all hazard ratios and confidence intervals"
- "What are the p-values reported in this paper?"
- "Extract statistical evidence from these trial results"

## Quick Start

### Basic Usage

```python
from scripts.extract import extract_statistics

text = """
Results: Treatment with Drug X showed significant benefit (HR 0.75, 95% CI 0.65-0.85,
p < 0.001) in the primary endpoint. The study included n = 1,234 patients, with a
response rate of 45.3% in the treatment arm versus 32.1% in the control arm (OR 1.76,
95% CI 1.42-2.18, p < 0.001).
"""

results = extract_statistics(text)

# Access extracted statistics
print(f"Hazard Ratios: {results['hazard_ratios']}")
print(f"P-values: {results['p_values']}")
print(f"Sample sizes: {results['sample_sizes']}")
print(f"Total statistics found: {results['summary']['total_statistics']}")
```

### Command-Line Usage

```bash
# Extract from text
python scripts/extract.py "HR 0.75 (95% CI 0.65-0.85, p < 0.001)"

# Extract from file
python scripts/extract.py --file abstract.txt
```

### Output Format

```json
{
  "hazard_ratios": [
    {
      "value": 0.75,
      "context": "Treatment with Drug X showed significant benefit (HR 0.75, 95% CI 0.65-0.85, p < 0.001)",
      "position": 52
    }
  ],
  "odds_ratios": [
    {
      "value": 1.76,
      "context": "versus 32.1% in the control arm (OR 1.76, 95% CI 1.42-2.18, p < 0.001)",
      "position": 187
    }
  ],
  "p_values": [
    {
      "value": 0.001,
      "context": "HR 0.75, 95% CI 0.65-0.85, p < 0.001)",
      "position": 95
    }
  ],
  "confidence_intervals": [
    {
      "lower": 0.65,
      "upper": 0.85,
      "context": "HR 0.75, 95% CI 0.65-0.85, p < 0.001",
      "position": 73
    }
  ],
  "sample_sizes": [
    {
      "value": 1234,
      "context": "The study included n = 1,234 patients",
      "position": 120
    }
  ],
  "percentages": [
    {
      "value": 45.3,
      "context": "response rate of 45.3% in the treatment arm",
      "position": 152
    }
  ],
  "summary": {
    "total_statistics": 8,
    "has_significance": true,
    "has_effect_sizes": true
  }
}
```

## Supported Statistical Measures

### 1. Effect Sizes

#### Hazard Ratio (HR)
- **What it measures**: Effect of intervention on survival time or time-to-event
- **Patterns recognized**: `HR = 0.75`, `hazard ratio: 0.75`, `HR (0.75)`
- **Interpretation**:
  - HR < 1: Protective effect (reduced hazard)
  - HR = 1: No effect
  - HR > 1: Harmful effect (increased hazard)

#### Odds Ratio (OR)
- **What it measures**: Odds of outcome given exposure
- **Patterns recognized**: `OR = 2.5`, `odds ratio: 2.5`, `OR (2.5)`
- **Interpretation**:
  - OR < 1: Protective effect (reduced odds)
  - OR = 1: No association
  - OR > 1: Risk factor (increased odds)

#### Risk Ratio (RR)
- **What it measures**: Ratio of probability in exposed vs unexposed groups
- **Patterns recognized**: `RR = 1.5`, `risk ratio: 1.5`, `relative risk = 1.5`, `RR (1.5)`
- **Interpretation**:
  - RR < 1: Protective effect (reduced risk)
  - RR = 1: No difference
  - RR > 1: Risk factor (increased risk)

### 2. Statistical Significance

#### P-value
- **What it measures**: Probability of results if null hypothesis is true
- **Patterns recognized**: `p = 0.05`, `p < 0.001`, `(p = 0.05)`, `p-value: 0.05`
- **Common thresholds**:
  - p < 0.001: Highly significant
  - p < 0.01: Very significant
  - p < 0.05: Significant (conventional threshold)
  - p ≥ 0.05: Not statistically significant

### 3. Precision Estimates

#### Confidence Interval (CI)
- **What it measures**: Range likely containing true population parameter
- **Patterns recognized**: `95% CI 0.6-0.9`, `CI (0.6-0.9)`, `(0.6-0.9)`
- **Interpretation**:
  - Wider CI: Less precise estimate
  - Narrower CI: More precise estimate
  - CI excluding null value (e.g., 1.0 for ratios): Statistically significant

### 4. Study Characteristics

#### Sample Size
- **What it measures**: Number of participants or observations
- **Patterns recognized**: `n = 500`, `N = 500`, `(n = 500)`, `sample size = 500`
- **Significance**: Larger samples provide more statistical power

#### Percentage
- **What it measures**: Proportion expressed per 100
- **Patterns recognized**: `45.3%`, `45.3 percent`
- **Context**: Response rates, prevalence, proportions, changes

## Pattern Documentation

### Regex Patterns

All patterns are defined directly in the extraction code (`scripts/extract.py`). Key patterns:

```python
# Hazard Ratio
HR_PATTERN = r'\bHR[\s:=]+(\d+\.?\d*)'

# Odds Ratio
OR_PATTERN = r'\bOR[\s:=]+(\d+\.?\d*)'

# Confidence Interval
CI_PATTERN = r'95%?\s*CI[\s:=]*\(?(\d+\.?\d*)[-–—](\d+\.?\d*)\)?'

# P-value
P_VALUE_PATTERN = r'\bp[\s<>=]+(\d+\.?\d*)'
```

### Common Reporting Formats

1. **Complete effect reporting**: `HR 0.75 (95% CI 0.65-0.85, p < 0.001)`
2. **Effect with CI only**: `OR 2.3 (1.5-3.2)`
3. **Percentage with CI**: `45.3% (95% CI 40.2%-50.4%)`
4. **Sample size**: `n = 1,234` or `N = 1234`

### Edge Cases

The extraction handles:
- **Multiple dash types**: Hyphen (-), en dash (–), em dash (—)
- **Various formatting**: Spaces, colons, equals signs around values
- **Parenthesized values**: `(HR 0.75)`, `(p < 0.001)`
- **Implicit CIs**: Ranges in parentheses near effect sizes

### Validation Rules

All validation rules are implemented in the extraction code:

- **Effect sizes (HR, OR, RR)**: Typical range [0.1, 10], valid range [0.01, 100]
- **P-values**: Valid range [0, 1]
- **Confidence intervals**: Lower bound must be < upper bound
- **Sample sizes**: Must be positive integers
- **Percentages**: Typical range [0, 100]

## Integration Patterns

### Pattern 1: Literature Review Extraction

```python
from scripts.extract import extract_statistics

# Extract from multiple abstracts
abstracts = load_pubmed_abstracts(query="lung cancer treatment")

literature_data = []
for abstract in abstracts:
    stats = extract_statistics(abstract.text)
    literature_data.append({
        "pmid": abstract.pmid,
        "title": abstract.title,
        "statistics": stats,
        "has_effect_size": stats["summary"]["has_effect_sizes"],
        "has_significance": stats["summary"]["has_significance"]
    })

# Filter papers with complete statistical reporting
complete_reporting = [
    paper for paper in literature_data
    if paper["has_effect_size"] and paper["has_significance"]
]
```

### Pattern 2: Meta-Analysis Data Collection

```python
# Extract effect sizes and CIs for meta-analysis
def extract_for_meta_analysis(studies):
    meta_data = []

    for study in studies:
        stats = extract_statistics(study.results_text)

        # Match effect sizes with their CIs
        for hr in stats["hazard_ratios"]:
            # Find CI closest to this HR
            closest_ci = find_closest_ci(hr, stats["confidence_intervals"])

            meta_data.append({
                "study": study.name,
                "effect_size": hr["value"],
                "ci_lower": closest_ci["lower"] if closest_ci else None,
                "ci_upper": closest_ci["upper"] if closest_ci else None,
                "effect_type": "hazard_ratio"
            })

    return meta_data
```

### Pattern 3: Quality Assessment

```python
def assess_statistical_reporting_quality(text):
    """
    Assess completeness of statistical reporting.

    Quality criteria:
    - Effect size reported (HR, OR, RR)
    - Confidence interval reported
    - P-value or significance reported
    """
    stats = extract_statistics(text)

    quality_score = {
        "has_effect_size": stats["summary"]["has_effect_sizes"],
        "has_confidence_interval": len(stats["confidence_intervals"]) > 0,
        "has_significance": stats["summary"]["has_significance"],
        "complete_reporting": False
    }

    # Complete reporting = effect size + CI + p-value
    quality_score["complete_reporting"] = all([
        quality_score["has_effect_size"],
        quality_score["has_confidence_interval"],
        quality_score["has_significance"]
    ])

    return quality_score
```

### Pattern 4: Batch Processing

```bash
# Process multiple files
for file in abstracts/*.txt; do
    echo "Processing $file"
    python scripts/extract.py --file "$file" > "results/$(basename $file .txt).json"
done

# Combine results
python -c "
import json
import glob

all_results = []
for result_file in glob.glob('results/*.json'):
    with open(result_file) as f:
        all_results.append(json.load(f))

with open('combined_statistics.json', 'w') as f:
    json.dump(all_results, f, indent=2)
"
```

## Working with the Skill

### Example 1: Extract from Clinical Trial Abstract

```python
abstract = """
BACKGROUND: Novel immunotherapy in advanced lung cancer.

METHODS: Randomized controlled trial (n = 856) comparing immunotherapy vs chemotherapy.

RESULTS: Primary endpoint (overall survival) showed significant improvement with
immunotherapy (HR 0.68, 95% CI 0.57-0.81, p < 0.001). Median OS was 14.2 months
vs 10.3 months. Response rate was 31.2% vs 18.7% (OR 1.98, 95% CI 1.52-2.58,
p < 0.001). Grade 3-4 adverse events occurred in 28.3% vs 41.2% of patients.
"""

stats = extract_statistics(abstract)

print(f"Sample size: {stats['sample_sizes'][0]['value']}")
print(f"Primary HR: {stats['hazard_ratios'][0]['value']}")
print(f"Response OR: {stats['odds_ratios'][0]['value']}")
print(f"Statistical significance: {len(stats['p_values'])} p-values found")
```

### Example 2: Filter High-Quality Evidence

```python
def filter_high_quality_studies(texts):
    """
    Filter studies with complete statistical reporting.
    """
    high_quality = []

    for i, text in enumerate(texts):
        stats = extract_statistics(text)

        # Criteria: At least one effect size with CI and p-value
        has_complete_evidence = (
            stats["summary"]["has_effect_sizes"] and
            len(stats["confidence_intervals"]) > 0 and
            stats["summary"]["has_significance"]
        )

        if has_complete_evidence:
            high_quality.append({
                "index": i,
                "text": text,
                "statistics": stats
            })

    return high_quality
```

### Example 3: Extract Statistics by Category

```python
def categorize_statistics(text):
    """
    Categorize extracted statistics by evidence type.
    """
    stats = extract_statistics(text)

    categorized = {
        "efficacy": {
            "effect_sizes": stats["hazard_ratios"] + stats["odds_ratios"] + stats["risk_ratios"],
            "response_rates": [p for p in stats["percentages"] if "response" in p["context"].lower()]
        },
        "safety": {
            "adverse_event_rates": [p for p in stats["percentages"] if "adverse" in p["context"].lower() or "AE" in p["context"]]
        },
        "study_design": {
            "sample_sizes": stats["sample_sizes"]
        },
        "statistical_significance": {
            "p_values": stats["p_values"],
            "confidence_intervals": stats["confidence_intervals"]
        }
    }

    return categorized
```

## Limitations and Considerations

### Current Limitations

1. **Scientific notation**: P-values like `p = 1.2e-5` are not currently captured (only decimal notation)
2. **Comma separators**: Large numbers with commas (e.g., `n = 1,234`) may not parse correctly
3. **Context interpretation**: Extraction is syntax-based; does not interpret what the statistic represents
4. **Association matching**: Does not automatically link effect sizes to their corresponding CIs and p-values

### Best Practices

1. **Verify extractions**: Always review context to ensure correct interpretation
2. **Check for completeness**: Use summary flags to identify incomplete statistical reporting
3. **Validate ranges**: Check that effect sizes and p-values fall within expected ranges
4. **Handle duplicates**: The extraction automatically deduplicates, but verify if multiple formats are used
5. **Consider context**: Use the context field to understand what each statistic represents

### Future Enhancements

Potential improvements for this skill:
- Support for scientific notation in p-values
- Automatic matching of effect sizes with their CIs and p-values
- Extraction of additional statistics (mean, median, standard deviation, correlation coefficients)
- Support for Bayesian statistics (posterior probabilities, credible intervals)
- Multi-language support for non-English papers

## Resources

### Scripts
- `scripts/extract.py`: Main extraction script with `extract_statistics()` function

### Assets
This skill does not include asset files.

---

**Skill version**: 1.0.0
**Last updated**: 2025-10-21
**Deterministic**: Yes (100% regex-based, no LLM calls)
