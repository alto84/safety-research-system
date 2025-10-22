#!/usr/bin/env python3
"""
PubMed literature search implementation using E-utilities API.

This module provides functions for searching PubMed and retrieving article metadata.
Uses the NCBI E-utilities API without requiring an API key (3 requests/second limit).

API Documentation:
- Esearch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
- Efetch: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
"""

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json


@dataclass
class PubMedArticle:
    """Represents a PubMed article with metadata."""
    pmid: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: str
    doi: Optional[str]
    url: str
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 3.0):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests allowed per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self):
        """Wait if necessary to maintain rate limit."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()


class PubMedSearchError(Exception):
    """Base exception for PubMed search errors."""
    pass


class NetworkError(PubMedSearchError):
    """Raised when network request fails."""
    pass


class ParseError(PubMedSearchError):
    """Raised when XML parsing fails."""
    pass


class PubMedSearch:
    """
    PubMed search client using E-utilities API.

    Handles search queries, result retrieval, and rate limiting.
    """

    BASE_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self, rate_limit: float = 3.0):
        """
        Initialize PubMed search client.

        Args:
            rate_limit: Maximum requests per second (default 3.0 for no API key)
        """
        self.rate_limiter = RateLimiter(rate_limit)

    def _make_request(self, url: str) -> str:
        """
        Make HTTP request with error handling.

        Args:
            url: URL to request

        Returns:
            Response text

        Raises:
            NetworkError: If request fails
        """
        self.rate_limiter.wait()

        try:
            # Add User-Agent header to comply with NCBI guidelines
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'PubMedSearch/1.0 (Python; Safety Research System)')

            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            raise NetworkError(f"Network request failed: {e}")
        except Exception as e:
            raise NetworkError(f"Unexpected error during request: {e}")

    def _parse_esearch_response(self, xml_text: str) -> List[str]:
        """
        Parse Esearch XML response to extract PMIDs.

        Args:
            xml_text: XML response from Esearch

        Returns:
            List of PMIDs

        Raises:
            ParseError: If XML parsing fails
        """
        try:
            root = ET.fromstring(xml_text)
            id_list = root.find('IdList')

            if id_list is None:
                return []

            return [id_elem.text for id_elem in id_list.findall('Id') if id_elem.text]
        except ET.ParseError as e:
            raise ParseError(f"Failed to parse Esearch XML: {e}")

    def _parse_efetch_response(self, xml_text: str) -> List[PubMedArticle]:
        """
        Parse Efetch XML response to extract article metadata.

        Args:
            xml_text: XML response from Efetch

        Returns:
            List of PubMedArticle objects

        Raises:
            ParseError: If XML parsing fails
        """
        try:
            root = ET.fromstring(xml_text)
            articles = []

            for pubmed_article in root.findall('.//PubmedArticle'):
                article_data = self._extract_article_data(pubmed_article)
                if article_data:
                    articles.append(article_data)

            return articles
        except ET.ParseError as e:
            raise ParseError(f"Failed to parse Efetch XML: {e}")

    def _extract_article_data(self, pubmed_article: ET.Element) -> Optional[PubMedArticle]:
        """
        Extract article data from PubmedArticle XML element.

        Args:
            pubmed_article: PubmedArticle XML element

        Returns:
            PubMedArticle object or None if required fields missing
        """
        medline_citation = pubmed_article.find('.//MedlineCitation')
        if medline_citation is None:
            return None

        # Extract PMID
        pmid_elem = medline_citation.find('.//PMID')
        if pmid_elem is None or not pmid_elem.text:
            return None
        pmid = pmid_elem.text

        # Extract article metadata
        article = medline_citation.find('.//Article')
        if article is None:
            return None

        # Title
        title_elem = article.find('.//ArticleTitle')
        title = title_elem.text if title_elem is not None and title_elem.text else "No title available"

        # Authors
        authors = []
        author_list = article.find('.//AuthorList')
        if author_list is not None:
            for author in author_list.findall('.//Author'):
                last_name = author.find('LastName')
                fore_name = author.find('ForeName')

                if last_name is not None and last_name.text:
                    if fore_name is not None and fore_name.text:
                        authors.append(f"{last_name.text} {fore_name.text}")
                    else:
                        authors.append(last_name.text)

        # Abstract
        abstract_parts = []
        abstract = article.find('.//Abstract')
        if abstract is not None:
            for abstract_text in abstract.findall('.//AbstractText'):
                if abstract_text.text:
                    # Handle labeled abstracts (e.g., BACKGROUND:, METHODS:)
                    label = abstract_text.get('Label')
                    if label:
                        abstract_parts.append(f"{label}: {abstract_text.text}")
                    else:
                        abstract_parts.append(abstract_text.text)

        abstract_text = " ".join(abstract_parts) if abstract_parts else "No abstract available"

        # Publication date
        pub_date_elem = article.find('.//Journal/JournalIssue/PubDate')
        pub_date = self._extract_pub_date(pub_date_elem)

        # Journal info
        journal_elem = article.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None and journal_elem.text else None

        volume_elem = article.find('.//Journal/JournalIssue/Volume')
        volume = volume_elem.text if volume_elem is not None and volume_elem.text else None

        issue_elem = article.find('.//Journal/JournalIssue/Issue')
        issue = issue_elem.text if issue_elem is not None and issue_elem.text else None

        pagination_elem = article.find('.//Pagination/MedlinePgn')
        pages = pagination_elem.text if pagination_elem is not None and pagination_elem.text else None

        # DOI
        doi = None
        article_id_list = pubmed_article.find('.//PubmedData/ArticleIdList')
        if article_id_list is not None:
            for article_id in article_id_list.findall('.//ArticleId'):
                if article_id.get('IdType') == 'doi' and article_id.text:
                    doi = article_id.text
                    break

        # URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return PubMedArticle(
            pmid=pmid,
            title=title,
            authors=authors,
            abstract=abstract_text,
            publication_date=pub_date,
            doi=doi,
            url=url,
            journal=journal,
            volume=volume,
            issue=issue,
            pages=pages
        )

    def _extract_pub_date(self, pub_date_elem: Optional[ET.Element]) -> str:
        """
        Extract publication date from PubDate XML element.

        Args:
            pub_date_elem: PubDate XML element

        Returns:
            Publication date string (YYYY-MM-DD or YYYY-MM or YYYY)
        """
        if pub_date_elem is None:
            return "Unknown"

        year_elem = pub_date_elem.find('Year')
        month_elem = pub_date_elem.find('Month')
        day_elem = pub_date_elem.find('Day')

        year = year_elem.text if year_elem is not None and year_elem.text else None
        month = month_elem.text if month_elem is not None and month_elem.text else None
        day = day_elem.text if day_elem is not None and day_elem.text else None

        if year:
            # Convert month name to number if needed
            if month:
                month_map = {
                    'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                    'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                    'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                }
                month_num = month_map.get(month, month)

                if day:
                    return f"{year}-{month_num.zfill(2)}-{day.zfill(2)}"
                else:
                    return f"{year}-{month_num.zfill(2)}"
            else:
                return year

        return "Unknown"

    def search(self, query: str, max_results: int = 20,
               filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Search PubMed for articles matching query.

        Args:
            query: Search query string (e.g., "cancer AND treatment")
            max_results: Maximum number of results to return (default 20)
            filters: Optional filters dict with keys:
                - min_date: Minimum publication date (YYYY/MM/DD)
                - max_date: Maximum publication date (YYYY/MM/DD)
                - article_type: Article type filter (e.g., "Review")

        Returns:
            List of PMIDs matching query

        Raises:
            NetworkError: If request fails
            ParseError: If response parsing fails
        """
        # Build query with filters
        search_term = query
        if filters:
            if 'article_type' in filters:
                search_term += f" AND {filters['article_type']}[ptyp]"

        # Build URL
        params = {
            'db': 'pubmed',
            'term': search_term,
            'retmax': str(max_results),
            'retmode': 'xml'
        }

        if filters:
            if 'min_date' in filters:
                params['mindate'] = filters['min_date']
            if 'max_date' in filters:
                params['maxdate'] = filters['max_date']
            if 'min_date' in filters or 'max_date' in filters:
                params['datetype'] = 'pdat'

        url = f"{self.BASE_ESEARCH_URL}?{urllib.parse.urlencode(params)}"

        # Make request
        response = self._make_request(url)

        # Parse response
        pmids = self._parse_esearch_response(response)

        return pmids

    def fetch_details(self, pmids: List[str]) -> List[PubMedArticle]:
        """
        Fetch detailed article information for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of PubMedArticle objects

        Raises:
            NetworkError: If request fails
            ParseError: If response parsing fails
        """
        if not pmids:
            return []

        # Build URL
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }

        url = f"{self.BASE_EFETCH_URL}?{urllib.parse.urlencode(params)}"

        # Make request
        response = self._make_request(url)

        # Parse response
        articles = self._parse_efetch_response(response)

        return articles


def search_pubmed(query: str, max_results: int = 20,
                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Search PubMed and return article details.

    This is the main entry point for PubMed searches. It performs both the search
    and detail retrieval in a single function call.

    Args:
        query: Search query string (supports PubMed query syntax)
            Examples:
            - "cancer treatment"
            - "diabetes AND (treatment OR therapy)"
            - "Smith J[Author]"
        max_results: Maximum number of results to return (default 20, max 10000)
        filters: Optional filters dictionary with keys:
            - min_date: Minimum publication date (YYYY/MM/DD format)
            - max_date: Maximum publication date (YYYY/MM/DD format)
            - article_type: Article type (e.g., "Review", "Clinical Trial")

    Returns:
        List of dictionaries, each containing:
            - pmid: PubMed ID
            - title: Article title
            - authors: List of author names
            - abstract: Article abstract
            - publication_date: Publication date (YYYY-MM-DD)
            - doi: Digital Object Identifier (may be None)
            - url: PubMed URL
            - journal: Journal name (may be None)
            - volume: Journal volume (may be None)
            - issue: Journal issue (may be None)
            - pages: Page numbers (may be None)

    Raises:
        PubMedSearchError: If search or retrieval fails
        NetworkError: If network request fails
        ParseError: If XML parsing fails

    Example:
        >>> results = search_pubmed("cancer immunotherapy", max_results=5)
        >>> for article in results:
        ...     print(f"{article['title']} ({article['pmid']})")

        >>> # Search with date filter
        >>> results = search_pubmed(
        ...     "COVID-19 vaccines",
        ...     max_results=10,
        ...     filters={'min_date': '2020/01/01', 'article_type': 'Review'}
        ... )
    """
    client = PubMedSearch()

    # Search for PMIDs
    pmids = client.search(query, max_results, filters)

    if not pmids:
        return []

    # Fetch article details
    articles = client.fetch_details(pmids)

    # Convert to dictionaries
    return [article.to_dict() for article in articles]


def main():
    """Command-line interface for PubMed search."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Search PubMed literature')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--max-results', type=int, default=20,
                       help='Maximum number of results (default: 20)')
    parser.add_argument('--min-date', help='Minimum publication date (YYYY/MM/DD)')
    parser.add_argument('--max-date', help='Maximum publication date (YYYY/MM/DD)')
    parser.add_argument('--article-type', help='Article type filter (e.g., Review)')
    parser.add_argument('--output', help='Output file (JSON format)')

    args = parser.parse_args()

    # Build filters
    filters = {}
    if args.min_date:
        filters['min_date'] = args.min_date
    if args.max_date:
        filters['max_date'] = args.max_date
    if args.article_type:
        filters['article_type'] = args.article_type

    try:
        # Perform search
        results = search_pubmed(args.query, args.max_results, filters or None)

        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))

        print(f"\nFound {len(results)} articles", file=sys.stderr)

    except PubMedSearchError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
