# PubMed Connector Documentation

Production-ready connector for NCBI E-utilities PubMed API integration.

## Overview

The PubMed Connector provides a robust, production-ready interface to search and retrieve scientific literature from PubMed. It implements best practices including rate limiting, caching, error handling, and structured data parsing.

## Features

- **Real API Integration**: Uses NCBI E-utilities API (no authentication required for basic usage)
- **Rate Limiting**: Automatic rate limiting (2.5 req/s default, 9 req/s with API key) to prevent 429 errors
- **Caching**: In-memory cache with TTL to reduce redundant API calls
- **Structured Data**: Returns structured `PaperDetails` objects with complete metadata
- **Error Handling**: Comprehensive error handling for network and API issues
- **XML Parsing**: Robust XML parsing with ElementTree
- **Batch Operations**: Efficient batch fetching of multiple papers
- **Advanced Filtering**: Support for date ranges, article types, species, and language filters

## Installation

The connector requires the `requests` library (already in requirements.txt):

```bash
pip install requests
```

## Quick Start

```python
from agents.data_sources.pubmed_connector import PubMedConnector

# Initialize connector
connector = PubMedConnector()

# Search for papers
pmids = connector.search_pubmed("cancer immunotherapy", max_results=10)

# Fetch paper details
paper = connector.fetch_paper_details(pmids[0])
print(paper.title)
print(paper.authors)
print(paper.abstract)
```

## API Reference

### PubMedConnector

Main class for interacting with PubMed API.

#### `__init__(email=None, cache_ttl=3600, api_key=None)`

Initialize the connector.

**Parameters:**
- `email` (str, optional): Your email address (recommended by NCBI for higher rate limits)
- `cache_ttl` (int): Cache time-to-live in seconds (default: 3600 = 1 hour)
- `api_key` (str, optional): NCBI API key (enables 10 req/s instead of 3 req/s)

**Example:**
```python
connector = PubMedConnector(email="researcher@institution.edu")
```

### Core Methods

#### `search_pubmed(query, max_results=100)`

Search PubMed and return list of PMIDs.

**Parameters:**
- `query` (str): PubMed search query using standard PubMed syntax
- `max_results` (int): Maximum number of results to return (default: 100)

**Returns:**
- `List[str]`: List of PMIDs as strings

**Example:**
```python
pmids = connector.search_pubmed("trastuzumab deruxtecan", max_results=20)
# Returns: ['41060507', '41036093', '41032684', ...]
```

**Query Syntax:**
- Simple: `"cancer treatment"`
- Boolean: `"breast cancer AND HER2"`
- Field-specific: `"Smith J[Author]"`
- Combined: `"checkpoint inhibitor AND (melanoma OR lung cancer)"`

#### `fetch_paper_details(pmid)`

Fetch detailed information for a specific PMID.

**Parameters:**
- `pmid` (str): PubMed ID

**Returns:**
- `PaperDetails`: Object containing structured paper metadata

**Example:**
```python
paper = connector.fetch_paper_details("32272236")
print(paper.title)        # Paper title
print(paper.authors)      # List of author names
print(paper.abstract)     # Full abstract text
print(paper.journal)      # Journal name
print(paper.publication_date)  # Publication date
print(paper.doi)          # DOI
print(paper.pmcid)        # PMC ID (if available)
print(paper.keywords)     # Keywords (if available)
```

#### `validate_pmid(pmid)`

Validate if a PMID exists in PubMed.

**Parameters:**
- `pmid` (str): PubMed ID to validate

**Returns:**
- `bool`: True if PMID exists, False otherwise

**Example:**
```python
is_valid = connector.validate_pmid("32272236")  # True
is_fake = connector.validate_pmid("99999999999")  # False
```

#### `search_with_filters(query, filters=None, max_results=100)`

Advanced search with filters.

**Parameters:**
- `query` (str): Base search query
- `filters` (dict, optional): Dictionary of filters to apply
- `max_results` (int): Maximum number of results (default: 100)

**Filter Options:**
- `date_from` (str): Start date in format "YYYY/MM/DD"
- `date_to` (str): End date in format "YYYY/MM/DD"
- `article_type` (str): Article type (e.g., "Review", "Clinical Trial", "Meta-Analysis")
- `species` (str): Species filter (e.g., "humans", "mice")
- `language` (str): Language code (e.g., "eng", "spa")

**Returns:**
- `List[str]`: List of PMIDs matching the filtered search

**Example:**
```python
filters = {
    "date_from": "2020/01/01",
    "date_to": "2023/12/31",
    "article_type": "Clinical Trial",
    "species": "humans"
}
pmids = connector.search_with_filters(
    "pembrolizumab",
    filters=filters,
    max_results=50
)
```

#### `batch_fetch_papers(pmids)`

Fetch details for multiple PMIDs efficiently.

**Parameters:**
- `pmids` (List[str]): List of PubMed IDs

**Returns:**
- `List[PaperDetails]`: List of paper details objects

**Example:**
```python
pmids = ["32272236", "33087473", "34449189"]
papers = connector.batch_fetch_papers(pmids)
for paper in papers:
    print(f"{paper.title} - {paper.journal}")
```

#### `clear_cache()`

Clear all cached data.

**Example:**
```python
connector.clear_cache()
```

## Data Structures

### PaperDetails

Structured container for paper metadata.

**Attributes:**
- `pmid` (str): PubMed ID
- `title` (str): Paper title
- `authors` (List[str]): List of author names (formatted as "FirstName LastName")
- `abstract` (str): Full abstract text
- `journal` (str): Journal name
- `publication_date` (str): Publication date
- `doi` (str, optional): Digital Object Identifier
- `pmcid` (str, optional): PubMed Central ID
- `keywords` (List[str], optional): Keywords/MeSH terms

**Methods:**
- `to_dict()`: Convert to dictionary

**Example:**
```python
paper = connector.fetch_paper_details("32272236")
paper_dict = paper.to_dict()
```

## Usage Examples

### Example 1: Safety Signal Detection

Search for papers about a drug and adverse event:

```python
connector = PubMedConnector()

drug = "trastuzumab deruxtecan"
adverse_event = "interstitial lung disease"

# Search for relevant papers
query = f"{drug} AND {adverse_event}"
pmids = connector.search_pubmed(query, max_results=20)

# Fetch details
papers = connector.batch_fetch_papers(pmids)

# Analyze
for paper in papers:
    print(f"{paper.title}")
    print(f"  Journal: {paper.journal} ({paper.publication_date})")
    print(f"  PMID: {paper.pmid}")
    print()
```

### Example 2: Systematic Review

Find all clinical trials for a specific indication:

```python
connector = PubMedConnector()

filters = {
    "date_from": "2020/01/01",
    "date_to": "2023/12/31",
    "article_type": "Clinical Trial",
    "species": "humans"
}

pmids = connector.search_with_filters(
    "checkpoint inhibitor melanoma",
    filters=filters,
    max_results=100
)

papers = connector.batch_fetch_papers(pmids)
print(f"Found {len(papers)} clinical trials")
```

### Example 3: Author Publication Tracking

Find papers by specific authors:

```python
connector = PubMedConnector()

query = "Smith J[Author] AND cancer immunotherapy"
pmids = connector.search_pubmed(query, max_results=50)

papers = connector.batch_fetch_papers(pmids)
for paper in papers:
    print(f"{paper.title} - {paper.publication_date}")
```

### Example 4: Citation Validation

Validate a list of PMIDs:

```python
connector = PubMedConnector()

pmids_to_validate = ["32272236", "33087473", "99999999999"]

for pmid in pmids_to_validate:
    is_valid = connector.validate_pmid(pmid)
    status = "✓ Valid" if is_valid else "✗ Invalid"
    print(f"PMID {pmid}: {status}")
```

## Rate Limiting

The connector automatically enforces rate limits to comply with NCBI policies:

- **Without API key**: 2.5 requests/second (conservative)
- **With API key**: 9 requests/second (conservative)

Rate limiting is transparent and automatic. The connector will sleep between requests as needed.

**Getting an API Key:**
1. Visit: https://www.ncbi.nlm.nih.gov/account/
2. Create an NCBI account
3. Generate an API key
4. Use it: `connector = PubMedConnector(api_key="your_key_here")`

## Caching

The connector includes an in-memory cache with TTL (time-to-live) to reduce redundant API calls:

- **Default TTL**: 1 hour (3600 seconds)
- **Cache key**: Based on query and parameters
- **Automatic**: No manual intervention needed

**Performance:**
- First request: ~200-400ms (API call)
- Cached request: <1ms (memory access)
- Speedup: 200-1000x

**Clear cache manually:**
```python
connector.clear_cache()
```

## Error Handling

The connector handles various error conditions:

### Network Errors
```python
try:
    pmids = connector.search_pubmed("cancer")
except requests.Timeout:
    print("Request timed out")
except requests.RequestException as e:
    print(f"Network error: {e}")
```

### Invalid PMIDs
```python
try:
    paper = connector.fetch_paper_details("invalid_id")
except ValueError as e:
    print(f"Invalid PMID: {e}")
```

### Rate Limit Errors
The connector's rate limiting should prevent 429 errors, but if they occur:
```python
try:
    pmids = connector.search_pubmed("cancer")
except requests.HTTPError as e:
    if e.response.status_code == 429:
        print("Rate limited - wait and retry")
```

## Performance Tips

1. **Use caching**: Repeated searches are instant with caching enabled
2. **Batch operations**: Use `batch_fetch_papers()` for multiple PMIDs
3. **Filter early**: Use `search_with_filters()` to reduce result sets
4. **API key**: Get an NCBI API key for 3x higher rate limits
5. **Appropriate max_results**: Don't fetch more papers than needed

## Testing

Run the validation suite:

```bash
python3 test_specific_requirements.py
```

This tests:
- Real API connectivity
- Search functionality
- Paper detail fetching
- PMID validation
- Rate limiting
- Caching
- Error handling

## API Endpoints Used

The connector uses three NCBI E-utilities endpoints:

1. **ESearch** (`esearch.fcgi`): Search PubMed and retrieve PMIDs
2. **EFetch** (`efetch.fcgi`): Fetch full paper details in XML format
3. **ESummary** (`esummary.fcgi`): Get document summaries for validation

All endpoints are accessed via HTTPS at `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

## Limitations

- **Rate limits**: 3 requests/second without API key (10 with key)
- **No full text**: API provides abstracts, not full paper text (use PMC for full text)
- **XML parsing**: Depends on NCBI XML format stability
- **Cache size**: In-memory cache grows with usage (cleared on restart)
- **No authentication**: Basic API doesn't require auth but has lower rate limits

## Troubleshooting

### 429 Too Many Requests
- Reduce rate limit: `connector = PubMedConnector()`
- Get API key for higher limits
- Check if other processes are using same IP

### No results found
- Verify query syntax with PubMed web interface
- Check date filters aren't too restrictive
- Try broader search terms

### Timeout errors
- Check internet connection
- NCBI services may be down (check: https://www.ncbi.nlm.nih.gov/)
- Increase timeout in code if needed

### Parse errors
- Report if XML format has changed
- Check PMID is valid with `validate_pmid()`

## References

- **NCBI E-utilities Documentation**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **PubMed Search Tips**: https://pubmed.ncbi.nlm.nih.gov/help/
- **API Key Registration**: https://www.ncbi.nlm.nih.gov/account/

## License

This connector is part of the Safety Research System and follows the same license.

## Support

For issues or questions, please refer to the main project documentation or create an issue in the project repository.
