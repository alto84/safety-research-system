---
name: literature_search
description: Use when you need to search PubMed for scientific literature, retrieve article metadata (titles, abstracts, authors, DOIs), or gather evidence for research questions. Provides access to NCBI's PubMed database through E-utilities API.
license: MIT
allowed-tools:
  - Bash
  - Read
  - Write
---

# Literature Search

## Overview

The literature_search skill provides programmatic access to PubMed's database of biomedical literature. It enables searching for scientific articles, retrieving detailed metadata (titles, abstracts, authors, publication dates, DOIs), and filtering results by date ranges and article types. Built on NCBI's E-utilities API, this skill handles rate limiting, error recovery, and structured data extraction automatically.

## When to Use This Skill

Use this skill when you need to:

- **Search PubMed** for articles on specific topics, diseases, treatments, or research areas
- **Gather evidence** for literature reviews, systematic reviews, or meta-analyses
- **Retrieve article metadata** including abstracts, author lists, DOIs, and publication information
- **Filter literature** by publication date ranges or article types (reviews, clinical trials, etc.)
- **Validate citations** by retrieving authoritative metadata from PubMed
- **Build reference lists** for research papers or safety assessments
- **Track recent publications** on emerging topics or safety concerns

**Trigger patterns:**
- User asks to "search PubMed for..."
- User requests "find articles about..."
- User needs "recent literature on..."
- User wants to "retrieve abstracts for..."
- Task involves literature review or evidence gathering
- Task requires citation validation or reference building

## Quick Start

### Basic Search

```python
from skills.literature.literature_search.scripts.search import search_pubmed

# Simple search
results = search_pubmed("antibody-drug conjugates lung disease", max_results=10)

for article in results:
    print(f"Title: {article['title']}")
    print(f"PMID: {article['pmid']}")
    print(f"Authors: {', '.join(article['authors'][:3])}...")
    print(f"Date: {article['publication_date']}")
    print(f"URL: {article['url']}")
    print()
```

### Search with Filters

```python
# Search for recent reviews
results = search_pubmed(
    query="COVID-19 vaccines",
    max_results=20,
    filters={
        'min_date': '2022/01/01',
        'max_date': '2024/12/31',
        'article_type': 'Review'
    }
)
```

### Command-Line Usage

```bash
# Basic search
python scripts/search.py "cancer immunotherapy" --max-results 10

# Search with filters
python scripts/search.py "diabetes treatment" \
  --max-results 20 \
  --min-date 2020/01/01 \
  --article-type "Clinical Trial" \
  --output results.json

# Complex query
python scripts/search.py "Smith J[Author] AND cancer[Title]" --max-results 5
```

## Query Syntax

The skill supports full PubMed query syntax for precise searches:

### Boolean Operators

```python
# AND - all terms must be present
search_pubmed("cancer AND treatment")

# OR - at least one term must be present
search_pubmed("diabetes OR hyperglycemia")

# NOT - exclude terms
search_pubmed("asthma NOT children")

# Combine operators (use parentheses for precedence)
search_pubmed("(diabetes OR hyperglycemia) AND (treatment OR therapy)")
```

### Field Tags

Use field tags to search specific metadata fields:

```python
# Search by author
search_pubmed("Smith J[Author]")

# Search in title only
search_pubmed("lung disease[Title]")

# Search in abstract
search_pubmed("interstitial pneumonitis[Abstract]")

# Search by journal
search_pubmed("cancer[Title] AND Nature[Journal]")

# Search by MeSH terms (Medical Subject Headings)
search_pubmed("Diabetes Mellitus, Type 2[MeSH]")

# Search by publication type
search_pubmed("cancer treatment[Title] AND Review[Publication Type]")
```

### Common Field Tags

| Tag | Description | Example |
|-----|-------------|---------|
| `[Author]` | Author name | `Smith J[Author]` |
| `[Title]` | Article title | `cancer[Title]` |
| `[Abstract]` | Abstract text | `treatment[Abstract]` |
| `[Journal]` | Journal name | `Nature[Journal]` |
| `[MeSH]` | MeSH terms | `Neoplasms[MeSH]` |
| `[Publication Type]` | Article type | `Review[Publication Type]` |
| `[Affiliation]` | Author affiliation | `Harvard[Affiliation]` |

### Phrase Searching

```python
# Use quotes for exact phrases
search_pubmed('"interstitial lung disease"')

# Combine with other terms
search_pubmed('"antibody-drug conjugates" AND safety')
```

## Filters

The `filters` parameter accepts a dictionary with the following keys:

### Date Filters

```python
# Articles from specific date range
filters = {
    'min_date': '2020/01/01',  # YYYY/MM/DD format
    'max_date': '2023/12/31'
}
results = search_pubmed("COVID-19", max_results=50, filters=filters)

# Last 5 years
filters = {'min_date': '2019/01/01'}
results = search_pubmed("immunotherapy", filters=filters)
```

### Article Type Filters

```python
# Reviews only
filters = {'article_type': 'Review'}
results = search_pubmed("cancer treatment", filters=filters)

# Clinical trials
filters = {'article_type': 'Clinical Trial'}
results = search_pubmed("diabetes drugs", filters=filters)

# Meta-analyses
filters = {'article_type': 'Meta-Analysis'}
results = search_pubmed("drug efficacy", filters=filters)
```

### Common Article Types

- `Review` - Review articles
- `Systematic Review` - Systematic reviews
- `Meta-Analysis` - Meta-analyses
- `Clinical Trial` - Clinical trials
- `Randomized Controlled Trial` - RCTs
- `Case Reports` - Case reports
- `Guideline` - Clinical guidelines

### Combined Filters

```python
# Recent reviews on a topic
filters = {
    'min_date': '2022/01/01',
    'article_type': 'Review'
}
results = search_pubmed("CRISPR therapy", max_results=30, filters=filters)
```

## Output Structure

Each article returned is a dictionary with the following fields:

```python
{
    'pmid': '12345678',                    # PubMed ID (string)
    'title': 'Article Title Here',        # Article title (string)
    'authors': [                           # List of authors (strings)
        'Smith John',
        'Johnson Mary',
        'Williams Robert'
    ],
    'abstract': 'Full abstract text...',  # Abstract (string, may be "No abstract available")
    'publication_date': '2023-05-15',     # Publication date (YYYY-MM-DD, YYYY-MM, or YYYY)
    'doi': '10.1234/journal.2023.001',    # DOI (string or None)
    'url': 'https://pubmed.ncbi.nlm.nih.gov/12345678/',  # PubMed URL (string)
    'journal': 'Nature Medicine',         # Journal name (string or None)
    'volume': '29',                        # Volume (string or None)
    'issue': '5',                          # Issue (string or None)
    'pages': '1234-1245'                   # Page range (string or None)
}
```

### Handling Missing Data

Some fields may be `None` or contain placeholder text:

```python
for article in results:
    # Check for missing abstract
    if article['abstract'] == "No abstract available":
        print(f"Article {article['pmid']} has no abstract")

    # Check for missing DOI
    if article['doi'] is None:
        print(f"Article {article['pmid']} has no DOI")

    # Handle missing authors
    if not article['authors']:
        print(f"Article {article['pmid']} has no listed authors")
```

## Integration Patterns

### Chaining with Evidence Classification

```python
from skills.literature.literature_search.scripts.search import search_pubmed
from skills.literature.evidence_level_classification import classify_evidence

# 1. Search for literature
articles = search_pubmed("ADC interstitial lung disease", max_results=50)

# 2. Classify evidence level for each article
classified_articles = []
for article in articles:
    evidence_level = classify_evidence(article)
    article['evidence_level'] = evidence_level
    classified_articles.append(article)

# 3. Filter for high-quality evidence
high_quality = [a for a in classified_articles if a['evidence_level'] in ['I', 'II']]
```

### Chaining with Source Authentication

```python
from skills.literature.literature_search.scripts.search import search_pubmed
from skills.audit.source_authenticity_verification import verify_sources

# 1. Search for literature
articles = search_pubmed("cancer treatment", max_results=20)

# 2. Verify source authenticity
verification_result = verify_sources(articles)

# 3. Use only authenticated sources
authentic_articles = verification_result['authentic_sources']
fabricated = verification_result['fabricated_sources']

if fabricated:
    print(f"Warning: {len(fabricated)} fabricated sources detected")
```

### Building a Literature Review Workflow

```python
from skills.literature.literature_search.scripts.search import search_pubmed

def conduct_literature_review(topic, date_range=None):
    """
    Conduct a structured literature review.

    Args:
        topic: Research topic
        date_range: Tuple of (min_date, max_date) in YYYY/MM/DD format

    Returns:
        Dictionary with categorized articles
    """
    # Build filters
    filters = {}
    if date_range:
        filters['min_date'] = date_range[0]
        filters['max_date'] = date_range[1]

    # Search different article types
    reviews = search_pubmed(
        topic,
        max_results=20,
        filters={**filters, 'article_type': 'Review'}
    )

    clinical_trials = search_pubmed(
        topic,
        max_results=30,
        filters={**filters, 'article_type': 'Clinical Trial'}
    )

    meta_analyses = search_pubmed(
        topic,
        max_results=10,
        filters={**filters, 'article_type': 'Meta-Analysis'}
    )

    return {
        'reviews': reviews,
        'clinical_trials': clinical_trials,
        'meta_analyses': meta_analyses,
        'total_count': len(reviews) + len(clinical_trials) + len(meta_analyses)
    }

# Use the workflow
results = conduct_literature_review(
    "antibody-drug conjugates safety",
    date_range=('2018/01/01', '2024/12/31')
)

print(f"Found {results['total_count']} articles:")
print(f"  - {len(results['reviews'])} reviews")
print(f"  - {len(results['clinical_trials'])} clinical trials")
print(f"  - {len(results['meta_analyses'])} meta-analyses")
```

### Exporting for Citation Management

```python
import json
from skills.literature.literature_search.scripts.search import search_pubmed

def export_for_citation_manager(query, output_file):
    """Export search results in format suitable for citation managers."""
    results = search_pubmed(query, max_results=100)

    # Format for import
    formatted = []
    for article in results:
        formatted.append({
            'type': 'article-journal',
            'title': article['title'],
            'author': [{'family': name.split()[-1], 'given': ' '.join(name.split()[:-1])}
                      for name in article['authors']],
            'issued': {'date-parts': [[int(p) for p in article['publication_date'].split('-')]]},
            'DOI': article['doi'],
            'URL': article['url'],
            'PMID': article['pmid'],
            'container-title': article['journal'],
            'volume': article['volume'],
            'issue': article['issue'],
            'page': article['pages']
        })

    with open(output_file, 'w') as f:
        json.dump(formatted, f, indent=2)

    return formatted

# Export results
export_for_citation_manager("machine learning healthcare", "citations.json")
```

## Error Handling

The skill provides structured error handling for common issues:

### Network Errors

```python
from skills.literature.literature_search.scripts.search import (
    search_pubmed,
    NetworkError,
    ParseError,
    PubMedSearchError
)

try:
    results = search_pubmed("cancer treatment")
except NetworkError as e:
    print(f"Network request failed: {e}")
    # Retry logic or fallback
except ParseError as e:
    print(f"Failed to parse response: {e}")
    # Log error and continue
except PubMedSearchError as e:
    print(f"Search failed: {e}")
    # General error handling
```

### Empty Results

```python
results = search_pubmed("very obscure topic xyz123")

if not results:
    print("No articles found. Try:")
    print("  - Broader search terms")
    print("  - Different spelling or synonyms")
    print("  - Removing date filters")
    print("  - Checking for typos")
```

### Retry Logic

```python
import time

def search_with_retry(query, max_retries=3):
    """Search with automatic retry on network errors."""
    for attempt in range(max_retries):
        try:
            return search_pubmed(query)
        except NetworkError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise  # Re-raise on final attempt

    return []

results = search_with_retry("cancer immunotherapy")
```

## Performance Characteristics

### Rate Limiting

- **Without API key:** 3 requests/second (enforced automatically)
- **With API key:** 10 requests/second (not implemented in this version)
- Rate limiting is handled internally - no manual throttling needed

### Response Times

Typical response times (depends on network and result count):

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Search (Esearch) | 200-500ms | Returns PMIDs only |
| Fetch details (Efetch) | 500-2000ms | Depends on number of articles |
| Complete search_pubmed() | 1-3 seconds | Combined search + fetch |

### Result Limits

- **max_results parameter:** Can request up to 10,000 results per query
- **Recommended range:** 10-100 results for most use cases
- **Large searches:** For >100 results, consider pagination or multiple queries

### Optimization Tips

```python
# 1. Request only needed results
results = search_pubmed("broad topic", max_results=20)  # Not 1000

# 2. Use specific queries to reduce result set
results = search_pubmed('"exact phrase"[Title]', max_results=50)

# 3. Cache results when repeating queries
import json

def cached_search(query, cache_file='cache.json'):
    """Search with file-based caching."""
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            if query in cache:
                return cache[query]
    except FileNotFoundError:
        cache = {}

    results = search_pubmed(query)
    cache[query] = results

    with open(cache_file, 'w') as f:
        json.dump(cache, f)

    return results

# 4. Use date filters to limit scope
results = search_pubmed(
    "common topic",
    filters={'min_date': '2023/01/01'}  # Recent only
)
```

## Best Practices

### Query Construction

1. **Start broad, then narrow:** Begin with general terms, then add filters
2. **Use field tags:** Constrain searches to specific fields for precision
3. **Leverage MeSH terms:** Use controlled vocabulary for medical concepts
4. **Test query syntax:** Verify queries on PubMed web interface first

### Result Processing

1. **Check for missing data:** Not all articles have abstracts, DOIs, or complete metadata
2. **Validate PMIDs:** Use source authenticity verification for critical applications
3. **Handle duplicates:** Multiple queries may return overlapping results
4. **Store results:** Save search results to avoid redundant API calls

### API Usage

1. **Respect rate limits:** Don't manually loop with delays - use the built-in rate limiter
2. **Handle errors gracefully:** Implement retry logic and fallbacks
3. **Monitor usage:** Track API calls to avoid hitting NCBI's usage policies
4. **Consider API keys:** For high-volume usage, register for an NCBI API key

## Advanced Features

### Batch Processing

```python
def batch_search(queries, max_results_per_query=20):
    """Process multiple queries in batch."""
    all_results = {}

    for query in queries:
        print(f"Searching: {query}")
        results = search_pubmed(query, max_results=max_results_per_query)
        all_results[query] = results

    return all_results

# Search multiple topics
topics = [
    "ADC pneumonitis",
    "ADC interstitial lung disease",
    "antibody-drug conjugate pulmonary toxicity"
]
results = batch_search(topics)
```

### Deduplication

```python
def deduplicate_results(results_list):
    """Remove duplicate articles from multiple searches."""
    seen_pmids = set()
    unique_articles = []

    for article in results_list:
        if article['pmid'] not in seen_pmids:
            seen_pmids.add(article['pmid'])
            unique_articles.append(article)

    return unique_articles

# Combine and deduplicate
results1 = search_pubmed("cancer treatment")
results2 = search_pubmed("oncology therapy")
all_results = results1 + results2
unique_results = deduplicate_results(all_results)
```

### Custom Sorting

```python
def sort_by_date(articles, reverse=True):
    """Sort articles by publication date."""
    return sorted(
        articles,
        key=lambda a: a['publication_date'],
        reverse=reverse  # True = newest first
    )

def sort_by_relevance(articles, keywords):
    """Sort by keyword presence in title/abstract."""
    def relevance_score(article):
        text = (article['title'] + ' ' + article['abstract']).lower()
        return sum(keyword.lower() in text for keyword in keywords)

    return sorted(articles, key=relevance_score, reverse=True)

# Use custom sorting
results = search_pubmed("machine learning")
by_date = sort_by_date(results)
by_relevance = sort_by_relevance(results, ['neural network', 'deep learning'])
```

## Troubleshooting

### Common Issues

**Issue:** No results returned
- **Solution:** Broaden query terms, check spelling, remove restrictive filters

**Issue:** NetworkError: timeout
- **Solution:** Check internet connection, retry with longer timeout, verify NCBI API is accessible

**Issue:** Missing abstracts
- **Solution:** Some articles don't have abstracts (especially older papers). Check `article['abstract']` for "No abstract available"

**Issue:** Rate limit errors
- **Solution:** Built-in rate limiting should prevent this. If occurring, ensure you're not running multiple instances simultaneously

**Issue:** Incomplete author lists
- **Solution:** Some articles list only first few authors. This is data limitation, not a bug

## Resources

### Scripts

**scripts/search.py** - Main implementation
- `search_pubmed(query, max_results, filters)` - Primary search function
- `PubMedSearch` - Low-level API client class
- Command-line interface for shell usage

### API Documentation

- **NCBI E-utilities:** https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **Esearch API:** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
- **Efetch API:** https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
- **PubMed Help:** https://pubmed.ncbi.nlm.nih.gov/help/

### Related Skills

- **evidence-level-classification** - Classify evidence quality (Level I-V)
- **source-authenticity-verification** - Validate source authenticity and detect fabrication
- **literature-synthesis** - Aggregate findings across multiple sources
- **statistical-evidence-extraction** - Extract quantitative data from articles

### PubMed Resources

- **PubMed Advanced Search:** https://pubmed.ncbi.nlm.nih.gov/advanced/
- **MeSH Database:** https://www.ncbi.nlm.nih.gov/mesh/
- **Search Field Descriptions:** https://pubmed.ncbi.nlm.nih.gov/help/#search-tags
- **PubMed API Key Registration:** https://ncbiinsights.ncbi.nlm.nih.gov/2017/11/02/new-api-keys-for-the-e-utilities/

---

**Version:** 1.0.0
**Last Updated:** 2025-10-21
**Maintainer:** Safety Research System Team
