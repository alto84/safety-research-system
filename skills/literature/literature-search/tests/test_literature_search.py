#!/usr/bin/env python3
"""
Comprehensive tests for literature-search skill.

Tests cover:
- Query parsing and construction
- API response handling
- Error handling (network failures, parse errors)
- Rate limiting
- Article metadata extraction
- Filtering functionality
- Edge cases and error conditions
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import xml.etree.ElementTree as ET
import urllib.error
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from search import (
    PubMedSearch,
    PubMedArticle,
    RateLimiter,
    search_pubmed,
    NetworkError,
    ParseError,
    PubMedSearchError
)


class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct interval."""
        limiter = RateLimiter(requests_per_second=2.0)
        self.assertEqual(limiter.min_interval, 0.5)

    def test_rate_limiter_default(self):
        """Test rate limiter with default settings."""
        limiter = RateLimiter()
        self.assertAlmostEqual(limiter.min_interval, 1.0 / 3.0, places=5)

    @patch('search.time.time')
    @patch('search.time.sleep')
    def test_rate_limiter_enforces_delay(self, mock_sleep, mock_time):
        """Test that rate limiter enforces delays between requests."""
        # Simulate time progression: start at 1.0 to avoid initial 0.0
        mock_time.side_effect = [1.0, 1.0, 1.1, 1.1]

        limiter = RateLimiter(requests_per_second=2.0)  # 0.5s interval

        # First call - should not wait (enough time passed since last_request_time=0)
        limiter.wait()
        mock_sleep.assert_not_called()

        # Second call - should wait (only 0.1s passed, need 0.5s)
        limiter.wait()
        mock_sleep.assert_called_once()
        # Should wait 0.5 - 0.1 = 0.4s
        self.assertAlmostEqual(mock_sleep.call_args[0][0], 0.4, places=2)


class TestPubMedArticle(unittest.TestCase):
    """Test PubMedArticle dataclass."""

    def test_article_creation(self):
        """Test creating a PubMedArticle instance."""
        article = PubMedArticle(
            pmid='12345678',
            title='Test Article',
            authors=['Smith J', 'Doe J'],
            abstract='Test abstract',
            publication_date='2023-05-15',
            doi='10.1234/test',
            url='https://pubmed.ncbi.nlm.nih.gov/12345678/',
            journal='Nature',
            volume='123',
            issue='4',
            pages='100-110'
        )

        self.assertEqual(article.pmid, '12345678')
        self.assertEqual(article.title, 'Test Article')
        self.assertEqual(len(article.authors), 2)

    def test_article_to_dict(self):
        """Test converting article to dictionary."""
        article = PubMedArticle(
            pmid='12345678',
            title='Test',
            authors=['Smith J'],
            abstract='Abstract',
            publication_date='2023-01-01',
            doi='10.1234/test',
            url='https://test.url'
        )

        result = article.to_dict()

        self.assertIsInstance(result, dict)
        self.assertEqual(result['pmid'], '12345678')
        self.assertEqual(result['title'], 'Test')
        self.assertIn('authors', result)


class TestPubMedSearchNetworking(unittest.TestCase):
    """Test network request handling."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    @patch('urllib.request.urlopen')
    def test_successful_request(self, mock_urlopen):
        """Test successful HTTP request."""
        mock_response = Mock()
        mock_response.read.return_value = b'<xml>test</xml>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.client._make_request('http://test.url')

        self.assertEqual(result, '<xml>test</xml>')
        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_network_error_handling(self, mock_urlopen):
        """Test network error is properly caught and raised."""
        mock_urlopen.side_effect = urllib.error.URLError('Connection failed')

        with self.assertRaises(NetworkError):
            self.client._make_request('http://test.url')

    @patch('urllib.request.urlopen')
    def test_timeout_handling(self, mock_urlopen):
        """Test timeout handling."""
        mock_urlopen.side_effect = TimeoutError('Request timeout')

        with self.assertRaises(NetworkError):
            self.client._make_request('http://test.url')


class TestEsearchParsing(unittest.TestCase):
    """Test Esearch XML response parsing."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    def test_parse_esearch_success(self):
        """Test parsing valid Esearch response."""
        xml_response = '''<?xml version="1.0"?>
        <eSearchResult>
            <IdList>
                <Id>12345678</Id>
                <Id>87654321</Id>
                <Id>11111111</Id>
            </IdList>
        </eSearchResult>'''

        pmids = self.client._parse_esearch_response(xml_response)

        self.assertEqual(len(pmids), 3)
        self.assertEqual(pmids[0], '12345678')
        self.assertEqual(pmids[1], '87654321')
        self.assertEqual(pmids[2], '11111111')

    def test_parse_esearch_empty_results(self):
        """Test parsing Esearch response with no results."""
        xml_response = '''<?xml version="1.0"?>
        <eSearchResult>
            <IdList></IdList>
        </eSearchResult>'''

        pmids = self.client._parse_esearch_response(xml_response)

        self.assertEqual(len(pmids), 0)

    def test_parse_esearch_missing_idlist(self):
        """Test parsing Esearch response with missing IdList."""
        xml_response = '''<?xml version="1.0"?>
        <eSearchResult>
            <Count>0</Count>
        </eSearchResult>'''

        pmids = self.client._parse_esearch_response(xml_response)

        self.assertEqual(len(pmids), 0)

    def test_parse_esearch_invalid_xml(self):
        """Test parsing invalid XML raises ParseError."""
        xml_response = '<invalid xml'

        with self.assertRaises(ParseError):
            self.client._parse_esearch_response(xml_response)


class TestEfetchParsing(unittest.TestCase):
    """Test Efetch XML response parsing."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    def test_parse_efetch_complete_article(self):
        """Test parsing complete article with all fields."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article Title</ArticleTitle>
                        <Abstract>
                            <AbstractText>This is the abstract text.</AbstractText>
                        </Abstract>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                            <Author>
                                <LastName>Doe</LastName>
                                <ForeName>Jane</ForeName>
                            </Author>
                        </AuthorList>
                        <Journal>
                            <Title>Nature Medicine</Title>
                            <JournalIssue>
                                <Volume>29</Volume>
                                <Issue>5</Issue>
                                <PubDate>
                                    <Year>2023</Year>
                                    <Month>May</Month>
                                    <Day>15</Day>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                        <Pagination>
                            <MedlinePgn>100-110</MedlinePgn>
                        </Pagination>
                    </Article>
                </MedlineCitation>
                <PubmedData>
                    <ArticleIdList>
                        <ArticleId IdType="doi">10.1234/nature.2023.001</ArticleId>
                    </ArticleIdList>
                </PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        self.assertEqual(len(articles), 1)
        article = articles[0]

        self.assertEqual(article.pmid, '12345678')
        self.assertEqual(article.title, 'Test Article Title')
        self.assertEqual(len(article.authors), 2)
        self.assertEqual(article.authors[0], 'Smith John')
        self.assertEqual(article.abstract, 'This is the abstract text.')
        self.assertEqual(article.publication_date, '2023-05-15')
        self.assertEqual(article.doi, '10.1234/nature.2023.001')
        self.assertEqual(article.journal, 'Nature Medicine')
        self.assertEqual(article.volume, '29')
        self.assertEqual(article.issue, '5')
        self.assertEqual(article.pages, '100-110')

    def test_parse_efetch_minimal_article(self):
        """Test parsing article with minimal fields."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Minimal Article</ArticleTitle>
                        <Journal>
                            <JournalIssue>
                                <PubDate>
                                    <Year>2023</Year>
                                </PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData></PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        self.assertEqual(len(articles), 1)
        article = articles[0]

        self.assertEqual(article.pmid, '12345678')
        self.assertEqual(article.title, 'Minimal Article')
        self.assertEqual(article.authors, [])
        self.assertEqual(article.abstract, 'No abstract available')
        self.assertEqual(article.publication_date, '2023')
        self.assertIsNone(article.doi)

    def test_parse_efetch_labeled_abstract(self):
        """Test parsing article with labeled abstract sections."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test</ArticleTitle>
                        <Abstract>
                            <AbstractText Label="BACKGROUND">Background text here.</AbstractText>
                            <AbstractText Label="METHODS">Methods text here.</AbstractText>
                            <AbstractText Label="RESULTS">Results text here.</AbstractText>
                        </Abstract>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData></PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        self.assertEqual(len(articles), 1)
        abstract = articles[0].abstract

        self.assertIn('BACKGROUND: Background text here.', abstract)
        self.assertIn('METHODS: Methods text here.', abstract)
        self.assertIn('RESULTS: Results text here.', abstract)

    def test_parse_efetch_invalid_xml(self):
        """Test parsing invalid XML raises ParseError."""
        xml_response = '<invalid xml'

        with self.assertRaises(ParseError):
            self.client._parse_efetch_response(xml_response)

    def test_parse_efetch_missing_pmid(self):
        """Test parsing article without PMID returns None."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <Article>
                        <ArticleTitle>No PMID Article</ArticleTitle>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        # Should skip article without PMID
        self.assertEqual(len(articles), 0)


class TestDateExtraction(unittest.TestCase):
    """Test publication date extraction."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    def test_extract_full_date(self):
        """Test extracting complete date (YYYY-MM-DD)."""
        pub_date_xml = '''
        <PubDate>
            <Year>2023</Year>
            <Month>05</Month>
            <Day>15</Day>
        </PubDate>'''

        pub_date_elem = ET.fromstring(pub_date_xml)
        date = self.client._extract_pub_date(pub_date_elem)

        self.assertEqual(date, '2023-05-15')

    def test_extract_month_name(self):
        """Test extracting date with month name."""
        pub_date_xml = '''
        <PubDate>
            <Year>2023</Year>
            <Month>May</Month>
            <Day>15</Day>
        </PubDate>'''

        pub_date_elem = ET.fromstring(pub_date_xml)
        date = self.client._extract_pub_date(pub_date_elem)

        self.assertEqual(date, '2023-05-15')

    def test_extract_year_month_only(self):
        """Test extracting date without day."""
        pub_date_xml = '''
        <PubDate>
            <Year>2023</Year>
            <Month>May</Month>
        </PubDate>'''

        pub_date_elem = ET.fromstring(pub_date_xml)
        date = self.client._extract_pub_date(pub_date_elem)

        self.assertEqual(date, '2023-05')

    def test_extract_year_only(self):
        """Test extracting date with year only."""
        pub_date_xml = '''
        <PubDate>
            <Year>2023</Year>
        </PubDate>'''

        pub_date_elem = ET.fromstring(pub_date_xml)
        date = self.client._extract_pub_date(pub_date_elem)

        self.assertEqual(date, '2023')

    def test_extract_missing_date(self):
        """Test handling missing date element."""
        date = self.client._extract_pub_date(None)

        self.assertEqual(date, 'Unknown')


class TestSearchFunction(unittest.TestCase):
    """Test PubMed search functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    @patch.object(PubMedSearch, '_make_request')
    def test_search_basic_query(self, mock_request):
        """Test basic search query."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <eSearchResult>
            <IdList>
                <Id>12345678</Id>
            </IdList>
        </eSearchResult>'''

        pmids = self.client.search('cancer treatment', max_results=10)

        self.assertEqual(len(pmids), 1)
        self.assertEqual(pmids[0], '12345678')

        # Verify URL construction
        call_args = mock_request.call_args[0][0]
        self.assertIn('term=cancer+treatment', call_args)
        self.assertIn('retmax=10', call_args)

    @patch.object(PubMedSearch, '_make_request')
    def test_search_with_date_filters(self, mock_request):
        """Test search with date range filters."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <eSearchResult><IdList></IdList></eSearchResult>'''

        filters = {
            'min_date': '2020/01/01',
            'max_date': '2023/12/31'
        }

        self.client.search('test query', filters=filters)

        # Verify filters in URL
        call_args = mock_request.call_args[0][0]
        self.assertIn('mindate=2020%2F01%2F01', call_args)
        self.assertIn('maxdate=2023%2F12%2F31', call_args)
        self.assertIn('datetype=pdat', call_args)

    @patch.object(PubMedSearch, '_make_request')
    def test_search_with_article_type_filter(self, mock_request):
        """Test search with article type filter."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <eSearchResult><IdList></IdList></eSearchResult>'''

        filters = {'article_type': 'Review'}

        self.client.search('test query', filters=filters)

        # Verify article type in query
        call_args = mock_request.call_args[0][0]
        self.assertIn('Review%5Bptyp%5D', call_args)  # [ptyp] URL-encoded


class TestFetchDetails(unittest.TestCase):
    """Test fetching article details."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    @patch.object(PubMedSearch, '_make_request')
    def test_fetch_details_success(self, mock_request):
        """Test successful fetch of article details."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test Article</ArticleTitle>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData></PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client.fetch_details(['12345678'])

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].pmid, '12345678')

    def test_fetch_details_empty_list(self):
        """Test fetching details with empty PMID list."""
        articles = self.client.fetch_details([])

        self.assertEqual(len(articles), 0)


class TestSearchPubMedFunction(unittest.TestCase):
    """Test high-level search_pubmed function."""

    @patch.object(PubMedSearch, 'fetch_details')
    @patch.object(PubMedSearch, 'search')
    def test_search_pubmed_integration(self, mock_search, mock_fetch):
        """Test full search_pubmed integration."""
        # Mock search returning PMIDs
        mock_search.return_value = ['12345678', '87654321']

        # Mock fetch returning articles
        mock_fetch.return_value = [
            PubMedArticle(
                pmid='12345678',
                title='Article 1',
                authors=['Smith J'],
                abstract='Abstract 1',
                publication_date='2023-01-01',
                doi='10.1234/test1',
                url='https://pubmed.ncbi.nlm.nih.gov/12345678/'
            ),
            PubMedArticle(
                pmid='87654321',
                title='Article 2',
                authors=['Doe J'],
                abstract='Abstract 2',
                publication_date='2023-02-01',
                doi='10.1234/test2',
                url='https://pubmed.ncbi.nlm.nih.gov/87654321/'
            )
        ]

        results = search_pubmed('test query', max_results=10)

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]['pmid'], '12345678')
        self.assertEqual(results[1]['pmid'], '87654321')

    @patch.object(PubMedSearch, 'search')
    def test_search_pubmed_no_results(self, mock_search):
        """Test search_pubmed with no results."""
        mock_search.return_value = []

        results = search_pubmed('obscure query')

        self.assertEqual(len(results), 0)

    @patch.object(PubMedSearch, 'search')
    def test_search_pubmed_with_filters(self, mock_search):
        """Test search_pubmed passes filters correctly."""
        mock_search.return_value = []

        filters = {
            'min_date': '2020/01/01',
            'article_type': 'Review'
        }

        search_pubmed('test', max_results=20, filters=filters)

        # Verify search was called with filters
        mock_search.assert_called_once_with('test', 20, filters)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    @patch.object(PubMedSearch, '_make_request')
    def test_network_error_propagates(self, mock_request):
        """Test that NetworkError propagates from search."""
        mock_request.side_effect = NetworkError('Connection failed')

        client = PubMedSearch()

        with self.assertRaises(NetworkError):
            client.search('test query')

    @patch.object(PubMedSearch, '_make_request')
    def test_parse_error_propagates(self, mock_request):
        """Test that ParseError propagates from search."""
        mock_request.return_value = '<invalid xml'

        client = PubMedSearch()

        with self.assertRaises(ParseError):
            client.search('test query')

    def test_pubmed_search_error_base_class(self):
        """Test PubMedSearchError is base for all errors."""
        self.assertTrue(issubclass(NetworkError, PubMedSearchError))
        self.assertTrue(issubclass(ParseError, PubMedSearchError))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and unusual inputs."""

    def setUp(self):
        """Set up test client."""
        self.client = PubMedSearch()

    @patch.object(PubMedSearch, '_make_request')
    def test_empty_query(self, mock_request):
        """Test handling empty query string."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <eSearchResult><IdList></IdList></eSearchResult>'''

        pmids = self.client.search('', max_results=10)

        self.assertEqual(len(pmids), 0)

    @patch.object(PubMedSearch, '_make_request')
    def test_special_characters_in_query(self, mock_request):
        """Test handling special characters in query."""
        mock_request.return_value = '''<?xml version="1.0"?>
        <eSearchResult><IdList></IdList></eSearchResult>'''

        # Should not crash with special characters
        pmids = self.client.search('test & query [Special]', max_results=10)

        self.assertIsNotNone(pmids)

    def test_article_with_no_authors(self):
        """Test parsing article with no authors."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test</ArticleTitle>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData></PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].authors, [])

    def test_article_with_only_lastname(self):
        """Test parsing author with only last name."""
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345678</PMID>
                    <Article>
                        <ArticleTitle>Test</ArticleTitle>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                            </Author>
                        </AuthorList>
                        <Journal>
                            <JournalIssue>
                                <PubDate><Year>2023</Year></PubDate>
                            </JournalIssue>
                        </Journal>
                    </Article>
                </MedlineCitation>
                <PubmedData></PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''

        articles = self.client._parse_efetch_response(xml_response)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].authors, ['Smith'])


if __name__ == '__main__':
    unittest.main()
