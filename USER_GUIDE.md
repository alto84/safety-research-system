# User Guide

Welcome to the Safety Research System! This guide will help you use the system to conduct pharmaceutical safety assessments.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Submitting a Case](#submitting-a-case)
- [Monitoring Progress](#monitoring-progress)
- [Understanding Results](#understanding-results)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Getting Started

### What is the Safety Research System?

The Safety Research System is an AI-powered platform that helps safety teams:
- Conduct literature reviews automatically
- Analyze safety signals
- Generate evidence-based safety assessments
- Ensure quality through automated validation

### Who Should Use This System?

- **Safety Scientists**: Primary users conducting safety assessments
- **Medical Reviewers**: Reviewing safety data for regulatory submissions
- **Clinical Teams**: Assessing benefit-risk profiles
- **Regulatory Affairs**: Preparing safety documentation

### Prerequisites

- **Access**: API key or web dashboard login credentials
- **Knowledge**: Basic pharmaceutical safety concepts
- **Question**: Clear safety question to investigate

---

## Submitting a Case

### Step 1: Define Your Question

Good safety questions are:
- **Specific**: "What is the incidence of pneumonitis with trastuzumab deruxtecan?" (Good)
- **Not vague**: "Tell me about drug safety" (Too broad)

- **Focused**: "What are risk factors for T-DXd pneumonitis?" (Good)
- **Not complex**: "What is everything about all ADC safety issues?" (Too broad)

### Step 2: Provide Context

Help the system understand your question by providing:
- **Drug name**: Generic and brand names
- **Adverse event**: Specific medical term
- **Population**: Patient characteristics (if relevant)
- **Indication**: Disease being treated
- **Timeframe**: Specific time period (if relevant)

### Step 3: Submit via API or Dashboard

#### Option A: API Submission

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "https://api.safety-research-system.com/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

case_data = {
    "title": "T-DXd Pneumonitis Risk Assessment",
    "question": "What are the primary risk factors for pneumonitis in patients treated with trastuzumab deruxtecan?",
    "priority": "HIGH",  # Options: LOW, MEDIUM, HIGH, URGENT
    "context": {
        "drug_name": "trastuzumab deruxtecan",
        "brand_name": "Enhertu",
        "adverse_event": "pneumonitis",
        "indication": "HER2+ breast cancer",
        "population": "adult patients"
    },
    "data_sources": ["pubmed", "clinical_trials_db"],
    "submitter": "your.email@company.com"
}

response = requests.post(
    f"{BASE_URL}/cases",
    headers=headers,
    json=case_data
)

case = response.json()
print(f"Case submitted! ID: {case['case_id']}")
print(f"Estimated completion: {case['estimated_completion']}")
```

#### Option B: Web Dashboard

1. Log in to dashboard
2. Click "New Case"
3. Fill in the form:
   - Title
   - Question
   - Priority
   - Context fields
   - Data sources
4. Click "Submit"
5. You'll receive a case ID and estimated completion time

---

## Monitoring Progress

### Check Case Status

#### Via API

```python
case_id = "case_abc123xyz"

response = requests.get(
    f"{BASE_URL}/cases/{case_id}/status",
    headers=headers
)

status = response.json()
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']['percentage']}%")
print(f"Tasks completed: {status['progress']['completed_tasks']}/{status['progress']['total_tasks']}")
```

#### Via Dashboard

1. Go to "My Cases"
2. Find your case by ID or title
3. View real-time progress bar
4. See current task being executed

### Case Statuses

| Status | Meaning | What to Do |
|--------|---------|------------|
| `submitted` | Case received, queued for processing | Wait for processing to start |
| `in_progress` | Tasks being executed | Monitor progress |
| `completed` | All tasks done, report ready | Review results |
| `requires_human_review` | Issues need expert review | Review flagged issues |
| `failed` | Processing error | Check error message, retry |

---

## Understanding Results

### Report Structure

When complete, you'll receive a comprehensive report:

```json
{
  "case_id": "case_abc123xyz",
  "title": "T-DXd Pneumonitis Risk Assessment",
  "report": {
    "executive_summary": "High-level summary of findings",
    "findings_by_task": {
      "literature_review": {
        "summary": "Review of 45 studies found...",
        "key_findings": {
          "conclusion": "Grade 3+ ILD occurs in 10-15% of patients",
          "confidence": "Moderate - based on 45 studies",
          "source_count": 45
        }
      }
    },
    "overall_assessment": "Detailed assessment",
    "recommendations": [
      "Recommendation 1",
      "Recommendation 2"
    ],
    "confidence_level": "Moderate - additional evidence would strengthen findings",
    "limitations": [
      "Limitation 1",
      "Limitation 2"
    ]
  }
}
```

### Interpreting Confidence Levels

| Level | Meaning | Example |
|-------|---------|---------|
| **Low** | Limited evidence, high uncertainty | "Based on 3 small studies" |
| **Moderate** | Reasonable evidence, some limitations | "Based on 20 studies, some heterogeneity" |
| **High** | Strong evidence from multiple sources | Rare - requires exceptional evidence |

**Note**: System is calibrated to be conservative. Most results will be "Moderate" or "Low" confidence to avoid overconfidence.

### Understanding Limitations

Every report includes limitations. Common limitations:
- Small sample sizes
- Short follow-up periods
- Publication bias
- Limited mechanistic understanding
- Heterogeneous study populations

**Important**: Limitations don't invalidate findings - they provide context for interpretation.

---

## Common Use Cases

### Use Case 1: Adverse Event Literature Review

**Question**: "What is the incidence of hepatotoxicity with Drug X?"

**Inputs**:
```json
{
  "question": "What is the incidence of hepatotoxicity in patients treated with Drug X?",
  "context": {
    "drug_name": "Drug X",
    "adverse_event": "hepatotoxicity"
  },
  "data_sources": ["pubmed"]
}
```

**Expected Output**:
- Pooled incidence rate with confidence interval
- List of studies reviewed
- Risk factors identified
- Grading (Grade 1-5)
- Confidence assessment

---

### Use Case 2: Safety Signal Investigation

**Question**: "Is there an association between Drug Y and cardiac arrhythmias?"

**Inputs**:
```json
{
  "question": "Is there an association between Drug Y and cardiac arrhythmias?",
  "context": {
    "drug_name": "Drug Y",
    "adverse_event": "cardiac arrhythmias",
    "signal_source": "spontaneous reports"
  },
  "data_sources": ["pubmed", "faers"]
}
```

**Expected Output**:
- Evidence for association (yes/no/unclear)
- Strength of evidence (weak/moderate/strong)
- Mechanistic plausibility
- Recommendations for further investigation

---

### Use Case 3: Risk Factor Analysis

**Question**: "What patient characteristics increase risk of Drug Z toxicity?"

**Inputs**:
```json
{
  "question": "What patient characteristics are associated with increased risk of Drug Z toxicity?",
  "context": {
    "drug_name": "Drug Z",
    "adverse_event": "toxicity",
    "focus": "risk factors"
  }
}
```

**Expected Output**:
- List of risk factors with odds ratios
- Statistical significance
- Clinical relevance
- Recommendations for patient monitoring

---

## Best Practices

### Formulating Questions

**Good Questions**:
- "What is the incidence of ILD with T-DXd?"
- "What are risk factors for checkpoint inhibitor colitis?"
- "Is there evidence for Drug A-Drug B interaction?"

**Poor Questions**:
- "Tell me about safety" (too vague)
- "What is the best drug?" (comparative, subjective)
- "Should I approve this drug?" (requires human judgment)

### Providing Context

**Helpful Context**:
- Drug names (generic + brand)
- Specific adverse events (MedDRA terms preferred)
- Patient population characteristics
- Timeframe or data cutoff
- Regulatory context

**Less Helpful**:
- Internal case numbers
- Lengthy case narratives
- Irrelevant background

### Interpreting Results

**Do**:
- Read the entire report, including limitations
- Note the confidence level
- Review source references
- Consider clinical context
- Consult subject matter experts for critical decisions

**Don't**:
- Rely solely on summary statistics
- Ignore confidence assessments
- Use as sole basis for regulatory decisions
- Assume completeness (literature always evolving)

### When to Escalate

Escalate to human expert review when:
- Case flagged as "requires_human_review"
- Critical safety signal detected
- Conflicting evidence in report
- Regulatory submission deadline
- Novel adverse event not well-characterized

---

## Working with Reports

### Exporting Results

#### Via API

```python
# Get full report
response = requests.get(
    f"{BASE_URL}/cases/{case_id}/report",
    headers=headers
)

report = response.json()

# Save to file
import json
with open(f"report_{case_id}.json", "w") as f:
    json.dump(report, f, indent=2)
```

#### Via Dashboard

1. Open case report
2. Click "Export"
3. Choose format: PDF, JSON, or DOCX
4. Download file

### Citing the System

When using results in publications or submissions:

```
Analysis conducted using the Safety Research System (Version 1.0.0).
Literature review executed [date]. [X] sources analyzed.
Full methodology available at [link].
```

---

## Tips and Tricks

### Get Faster Results

1. **Prioritize appropriately**:
   - URGENT: <1 hour (use sparingly)
   - HIGH: <2 hours
   - MEDIUM: <4 hours
   - LOW: <8 hours

2. **Limit data sources**: Start with PubMed, add others if needed

3. **Be specific**: Narrow questions process faster

### Improve Result Quality

1. **Use medical terminology**: MedDRA preferred terms
2. **Specify population**: "elderly patients" vs "patients"
3. **Define timeframe**: "studies since 2020"
4. **Iterate**: Submit follow-up cases to drill deeper

### Troubleshoot Issues

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues.

---

## Support

### Getting Help

- **Documentation**: Check this guide and [FAQ.md](./FAQ.md)
- **Dashboard Help**: Click "?" icon for context help
- **Email**: support@safety-research-system.com
- **Response time**: <24 hours for standard requests

### Providing Feedback

We welcome feedback! Submit via:
- Dashboard feedback form
- Email: feedback@safety-research-system.com
- GitHub issues (for technical users)

---

**Last Updated**: November 1, 2025
