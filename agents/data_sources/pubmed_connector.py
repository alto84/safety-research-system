"""
PubMed API Connector for Literature Search

Production-ready connector using NCBI E-utilities API for PubMed searches.
Implements rate limiting, caching, error handling, and structured data parsing.
"""

import time
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from functools import lru_cache
import hashlib


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PaperDetails:
    """Structured container for paper metadata."""
    pmid: str
    title: str
    authors: List[str]
    abstract: str
    journal: str
    publication_date: str
    doi: Optional[str] = None
    pmcid: Optional[str] = None
    keywords: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RateLimiter:
    """Rate limiter for API calls (NCBI requires max 3 requests/second without API key)."""

    def __init__(self, max_requests_per_second: float = 2.5):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum requests per second (default 2.5 to be conservative)
        """
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0.0

    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.3f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 3600):
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = timedelta(seconds=ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                logger.debug(f"Cache hit for key: {key[:50]}")
                return value
            else:
                # Expired, remove from cache
                del self.cache[key]
                logger.debug(f"Cache expired for key: {key[:50]}")
        return None

    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp."""
        self.cache[key] = (value, datetime.now())
        logger.debug(f"Cache set for key: {key[:50]}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")


class PubMedConnector:
    """
    Production-ready PubMed API connector using NCBI E-utilities.

    Features:
    - Rate limiting (3 requests/second max)
    - Local caching to reduce API calls
    - Comprehensive error handling
    - XML parsing for structured data
    - Advanced search filters
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ESEARCH_URL = f"{BASE_URL}/esearch.fcgi"
    EFETCH_URL = f"{BASE_URL}/efetch.fcgi"
    ESUMMARY_URL = f"{BASE_URL}/esummary.fcgi"

    def __init__(self, email: Optional[str] = None, cache_ttl: int = 3600, api_key: Optional[str] = None):
        """
        Initialize PubMed connector.

        Args:
            email: Optional email for NCBI (recommended for higher rate limits)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            api_key: Optional NCBI API key (allows 10 requests/second instead of 3)
        """
        self.email = email
        self.api_key = api_key
        # Use higher rate limit if API key provided
        rate_limit = 9.0 if api_key else 2.5  # Conservative to avoid 429 errors
        self.rate_limiter = RateLimiter(max_requests_per_second=rate_limit)
        self.cache = SimpleCache(ttl_seconds=cache_ttl)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PubMedConnector/1.0 (Safety Research System)'
        })
        logger.info(f"PubMedConnector initialized (rate limit: {rate_limit} req/s)")

    def _make_request(self, url: str, params: Dict[str, Any]) -> requests.Response:
        """
        Make rate-limited API request with error handling.

        Args:
            url: API endpoint URL
            params: Query parameters

        Returns:
            Response object

        Raises:
            requests.RequestException: On network or API errors
        """
        # Add email if provided
        if self.email:
            params['email'] = self.email

        # Add API key if provided
        if self.api_key:
            params['api_key'] = self.api_key

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def search_pubmed(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search PubMed and return list of PMIDs.

        Args:
            query: Search query string (PubMed syntax)
            max_results: Maximum number of results to return

        Returns:
            List of PMIDs as strings

        Example:
            >>> connector = PubMedConnector()
            >>> pmids = connector.search_pubmed("trastuzumab deruxtecan", max_results=10)
        """
        # Check cache
        cache_key = f"search:{hashlib.md5(f'{query}:{max_results}'.encode()).hexdigest()}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml',
            'usehistory': 'y'
        }

        try:
            response = self._make_request(self.ESEARCH_URL, params)
            root = ET.fromstring(response.content)

            # Extract PMIDs
            pmids = [id_elem.text for id_elem in root.findall('.//Id')]

            logger.info(f"Found {len(pmids)} results for query: {query[:50]}")

            # Cache results
            self.cache.set(cache_key, pmids)

            return pmids

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Failed to parse PubMed response: {e}")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def fetch_paper_details(self, pmid: str) -> PaperDetails:
        """
        Fetch detailed information for a specific PMID.

        Args:
            pmid: PubMed ID

        Returns:
            PaperDetails object with structured metadata

        Example:
            >>> connector = PubMedConnector()
            >>> paper = connector.fetch_paper_details("32272236")
            >>> print(paper.title)
        """
        # Check cache
        cache_key = f"fetch:{pmid}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml',
            'rettype': 'abstract'
        }

        try:
            response = self._make_request(self.EFETCH_URL, params)
            root = ET.fromstring(response.content)

            # Parse article data
            article = root.find('.//PubmedArticle')
            if article is None:
                raise ValueError(f"No article found for PMID: {pmid}")

            # Extract title
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title available"

            # Extract authors
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('.//Author'):
                    lastname = author.find('LastName')
                    forename = author.find('ForeName')
                    if lastname is not None:
                        author_name = lastname.text
                        if forename is not None:
                            author_name = f"{forename.text} {author_name}"
                        authors.append(author_name)

            # Extract abstract
            abstract_parts = []
            abstract = article.find('.//Abstract')
            if abstract is not None:
                for text_elem in abstract.findall('.//AbstractText'):
                    label = text_elem.get('Label')
                    text = text_elem.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
            abstract_text = " ".join(abstract_parts) if abstract_parts else "No abstract available"

            # Extract journal
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"

            # Extract publication date
            pub_date = article.find('.//PubDate')
            pub_date_str = "Unknown date"
            if pub_date is not None:
                year = pub_date.find('Year')
                month = pub_date.find('Month')
                day = pub_date.find('Day')
                parts = []
                if year is not None:
                    parts.append(year.text)
                if month is not None:
                    parts.append(month.text)
                if day is not None:
                    parts.append(day.text)
                if parts:
                    pub_date_str = " ".join(parts)

            # Extract DOI
            doi = None
            article_ids = article.findall('.//ArticleId')
            for aid in article_ids:
                if aid.get('IdType') == 'doi':
                    doi = aid.text
                    break

            # Extract PMCID
            pmcid = None
            for aid in article_ids:
                if aid.get('IdType') == 'pmc':
                    pmcid = aid.text
                    break

            # Extract keywords
            keywords = []
            keyword_list = article.find('.//KeywordList')
            if keyword_list is not None:
                for kw in keyword_list.findall('.//Keyword'):
                    if kw.text:
                        keywords.append(kw.text)

            paper = PaperDetails(
                pmid=pmid,
                title=title,
                authors=authors,
                abstract=abstract_text,
                journal=journal,
                publication_date=pub_date_str,
                doi=doi,
                pmcid=pmcid,
                keywords=keywords if keywords else None
            )

            logger.info(f"Fetched details for PMID: {pmid}")

            # Cache results
            self.cache.set(cache_key, paper)

            return paper

        except ET.ParseError as e:
            logger.error(f"XML parsing error for PMID {pmid}: {e}")
            raise ValueError(f"Failed to parse PubMed response for PMID {pmid}: {e}")
        except Exception as e:
            logger.error(f"Fetch failed for PMID {pmid}: {e}")
            raise

    def validate_pmid(self, pmid: str) -> bool:
        """
        Validate if a PMID exists in PubMed.

        Args:
            pmid: PubMed ID to validate

        Returns:
            True if PMID exists, False otherwise

        Example:
            >>> connector = PubMedConnector()
            >>> connector.validate_pmid("32272236")  # Real PMID
            True
            >>> connector.validate_pmid("99999999999")  # Fake PMID
            False
        """
        # Check cache
        cache_key = f"validate:{pmid}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml'
        }

        try:
            response = self._make_request(self.ESUMMARY_URL, params)
            root = ET.fromstring(response.content)

            # Check for error in response
            error = root.find('.//ERROR')
            if error is not None:
                logger.info(f"PMID {pmid} not found: {error.text}")
                result = False
            else:
                # Check if we got a valid document summary
                doc_sum = root.find('.//DocSum')
                result = doc_sum is not None
                logger.info(f"PMID {pmid} validation: {result}")

            # Cache results
            self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Validation failed for PMID {pmid}: {e}")
            return False

    def search_with_filters(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 100
    ) -> List[str]:
        """
        Advanced search with filters.

        Args:
            query: Base search query
            filters: Dictionary of filters to apply
                - date_from: Start date (YYYY/MM/DD)
                - date_to: End date (YYYY/MM/DD)
                - article_type: Type of article (e.g., "Review", "Clinical Trial")
                - species: Species filter (e.g., "humans")
                - language: Language filter (e.g., "eng")
            max_results: Maximum number of results

        Returns:
            List of PMIDs matching the search criteria

        Example:
            >>> connector = PubMedConnector()
            >>> filters = {
            ...     "date_from": "2020/01/01",
            ...     "date_to": "2023/12/31",
            ...     "article_type": "Clinical Trial"
            ... }
            >>> pmids = connector.search_with_filters(
            ...     "trastuzumab deruxtecan",
            ...     filters=filters
            ... )
        """
        # Build filtered query
        query_parts = [query]

        if filters:
            if 'date_from' in filters or 'date_to' in filters:
                date_from = filters.get('date_from', '1900/01/01')
                date_to = filters.get('date_to', '2100/12/31')
                query_parts.append(f'("{date_from}"[Date - Publication] : "{date_to}"[Date - Publication])')

            if 'article_type' in filters:
                query_parts.append(f'"{filters["article_type"]}"[Publication Type]')

            if 'species' in filters:
                query_parts.append(f'"{filters["species"]}"[MeSH Terms]')

            if 'language' in filters:
                query_parts.append(f'{filters["language"]}[Language]')

        combined_query = " AND ".join(query_parts)
        logger.info(f"Filtered search query: {combined_query}")

        return self.search_pubmed(combined_query, max_results=max_results)

    def batch_fetch_papers(self, pmids: List[str]) -> List[PaperDetails]:
        """
        Fetch details for multiple PMIDs efficiently.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of PaperDetails objects
        """
        papers = []
        for pmid in pmids:
            try:
                paper = self.fetch_paper_details(pmid)
                papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to fetch PMID {pmid}: {e}")
                continue

        logger.info(f"Successfully fetched {len(papers)}/{len(pmids)} papers")
        return papers

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
