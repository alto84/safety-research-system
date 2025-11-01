"""Integration tests for external API connectors."""
import pytest
from agents.data_sources.pubmed_connector import PubMedConnector
from agents.data_sources.clinical_trials_connector import ClinicalTrialsConnector


def test_pubmed_connector_initialization():
    """Test PubMed connector initialization."""
    connector = PubMedConnector()
    assert connector is not None
    assert connector.rate_limiter is not None
    assert connector.cache is not None


@pytest.mark.integration
def test_pubmed_search():
    """Test PubMed search (requires network)."""
    connector = PubMedConnector()
    pmids = connector.search_pubmed("aspirin", max_results=5)
    
    assert isinstance(pmids, list)
    assert len(pmids) <= 5


@pytest.mark.integration
def test_pubmed_fetch_details():
    """Test fetching paper details from PubMed."""
    connector = PubMedConnector()
    # Use a known PMID for aspirin
    paper = connector.fetch_paper_details("32272236")
    
    assert paper is not None
    assert paper.pmid == "32272236"
    assert paper.title
    assert paper.authors


def test_clinical_trials_connector_initialization():
    """Test ClinicalTrials.gov connector initialization."""
    connector = ClinicalTrialsConnector()
    assert connector is not None
    assert connector.rate_limiter is not None


@pytest.mark.integration
def test_clinical_trials_search():
    """Test ClinicalTrials.gov search (requires network)."""
    connector = ClinicalTrialsConnector()
    nct_ids = connector.search_trials(
        condition="lung cancer",
        max_results=5
    )
    
    assert isinstance(nct_ids, list)
    assert len(nct_ids) <= 5
