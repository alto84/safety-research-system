"""
ClinicalTrials.gov API Connector

Production-ready connector using ClinicalTrials.gov API v2 for trial searches.
Implements rate limiting, caching, error handling, and structured data parsing.
"""

import time
import logging
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import requests
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class ClinicalTrial:
    """Structured container for clinical trial metadata."""
    nct_id: str
    title: str
    status: str
    phase: Optional[str]
    conditions: List[str]
    interventions: List[str]
    sponsors: List[str]
    enrollment: Optional[int]
    start_date: Optional[str]
    completion_date: Optional[str]
    primary_outcome: Optional[str]
    brief_summary: Optional[str]
    detailed_description: Optional[str]
    locations: List[Dict[str, str]]
    study_type: Optional[str]
    url: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RateLimiter:
    """Rate limiter for API calls."""

    def __init__(self, max_requests_per_second: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            max_requests_per_second: Maximum requests per second
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


class ClinicalTrialsConnector:
    """
    Production-ready ClinicalTrials.gov API v2 connector.

    Features:
    - Rate limiting (configurable)
    - Local caching to reduce API calls
    - Comprehensive error handling
    - JSON parsing for structured data
    - Advanced search filters
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2"
    STUDIES_URL = f"{BASE_URL}/studies"

    def __init__(self, cache_ttl: int = 3600, rate_limit: float = 1.0):
        """
        Initialize ClinicalTrials.gov connector.

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            rate_limit: Requests per second (default: 1.0)
        """
        self.rate_limiter = RateLimiter(max_requests_per_second=rate_limit)
        self.cache = SimpleCache(ttl_seconds=cache_ttl)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClinicalTrialsConnector/1.0 (Safety Research System)'
        })
        logger.info(f"ClinicalTrialsConnector initialized (rate limit: {rate_limit} req/s)")

    def _make_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> requests.Response:
        """
        Make rate-limited API request with error handling.

        Args:
            url: API endpoint URL
            params: Query parameters
            method: HTTP method

        Returns:
            Response object

        Raises:
            requests.RequestException: On network or API errors
        """
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, json=params, timeout=30)

            response.raise_for_status()
            return response

        except requests.Timeout:
            logger.error(f"Request timeout for URL: {url}")
            raise
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def search_trials(
        self,
        query: Optional[str] = None,
        condition: Optional[str] = None,
        intervention: Optional[str] = None,
        status: Optional[str] = None,
        phase: Optional[str] = None,
        max_results: int = 100
    ) -> List[str]:
        """
        Search ClinicalTrials.gov and return list of NCT IDs.

        Args:
            query: General search query
            condition: Condition/disease to search for
            intervention: Intervention/treatment to search for
            status: Trial status (e.g., "RECRUITING", "COMPLETED")
            phase: Trial phase (e.g., "PHASE1", "PHASE2", "PHASE3")
            max_results: Maximum number of results to return

        Returns:
            List of NCT IDs as strings

        Example:
            >>> connector = ClinicalTrialsConnector()
            >>> nct_ids = connector.search_trials(
            ...     condition="lung cancer",
            ...     intervention="trastuzumab deruxtecan",
            ...     status="RECRUITING"
            ... )
        """
        # Build cache key
        cache_key_parts = [
            f"q={query}" if query else "",
            f"c={condition}" if condition else "",
            f"i={intervention}" if intervention else "",
            f"s={status}" if status else "",
            f"p={phase}" if phase else "",
            f"max={max_results}"
        ]
        cache_key = f"search:{hashlib.md5(':'.join(filter(None, cache_key_parts)).encode()).hexdigest()}"

        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Build query parameters
        params = {
            "format": "json",
            "pageSize": min(max_results, 1000),  # API limit
        }

        # Build query parts
        query_parts = []
        if query:
            query_parts.append(query)
        if condition:
            query_parts.append(f"AREA[Condition]{condition}")
        if intervention:
            query_parts.append(f"AREA[Intervention]{intervention}")
        if status:
            query_parts.append(f"AREA[OverallStatus]{status}")
        if phase:
            query_parts.append(f"AREA[Phase]{phase}")

        if query_parts:
            params["query.term"] = " AND ".join(query_parts)

        try:
            response = self._make_request(self.STUDIES_URL, params)
            data = response.json()

            # Extract NCT IDs from response
            nct_ids = []
            if "studies" in data:
                for study in data["studies"][:max_results]:
                    protocol_section = study.get("protocolSection", {})
                    identification_module = protocol_section.get("identificationModule", {})
                    nct_id = identification_module.get("nctId")
                    if nct_id:
                        nct_ids.append(nct_id)

            logger.info(f"Found {len(nct_ids)} trials for query: {params.get('query.term', 'all')[:100]}")

            # Cache results
            self.cache.set(cache_key, nct_ids)

            return nct_ids

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def fetch_trial_details(self, nct_id: str) -> ClinicalTrial:
        """
        Fetch detailed information for a specific NCT ID.

        Args:
            nct_id: ClinicalTrials.gov NCT ID

        Returns:
            ClinicalTrial object with structured metadata

        Example:
            >>> connector = ClinicalTrialsConnector()
            >>> trial = connector.fetch_trial_details("NCT04644237")
            >>> print(trial.title)
        """
        # Check cache
        cache_key = f"fetch:{nct_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        params = {
            "format": "json",
            "query.term": f"AREA[NCTId]{nct_id}"
        }

        try:
            response = self._make_request(self.STUDIES_URL, params)
            data = response.json()

            if not data.get("studies"):
                raise ValueError(f"No trial found for NCT ID: {nct_id}")

            study = data["studies"][0]
            protocol_section = study.get("protocolSection", {})

            # Extract identification info
            id_module = protocol_section.get("identificationModule", {})
            title = id_module.get("officialTitle") or id_module.get("briefTitle", "No title")

            # Extract status info
            status_module = protocol_section.get("statusModule", {})
            status = status_module.get("overallStatus", "Unknown")
            start_date = self._extract_date(status_module.get("startDateStruct"))
            completion_date = self._extract_date(status_module.get("completionDateStruct"))

            # Extract design info
            design_module = protocol_section.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else None
            study_type = design_module.get("studyType")
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment = enrollment_info.get("count")

            # Extract conditions
            conditions_module = protocol_section.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])

            # Extract interventions
            arms_module = protocol_section.get("armsInterventionsModule", {})
            interventions = [
                interv.get("name", "Unknown")
                for interv in arms_module.get("interventions", [])
            ]

            # Extract sponsors
            sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsor_module.get("leadSponsor", {})
            sponsors = [lead_sponsor.get("name")] if lead_sponsor.get("name") else []
            collaborators = sponsor_module.get("collaborators", [])
            sponsors.extend([c.get("name") for c in collaborators if c.get("name")])

            # Extract outcomes
            outcomes_module = protocol_section.get("outcomesModule", {})
            primary_outcomes = outcomes_module.get("primaryOutcomes", [])
            primary_outcome = primary_outcomes[0].get("measure") if primary_outcomes else None

            # Extract descriptions
            description_module = protocol_section.get("descriptionModule", {})
            brief_summary = description_module.get("briefSummary")
            detailed_description = description_module.get("detailedDescription")

            # Extract locations
            contacts_module = protocol_section.get("contactsLocationsModule", {})
            locations_data = contacts_module.get("locations", [])
            locations = [
                {
                    "facility": loc.get("facility", "Unknown"),
                    "city": loc.get("city", ""),
                    "state": loc.get("state", ""),
                    "country": loc.get("country", ""),
                }
                for loc in locations_data
            ]

            trial = ClinicalTrial(
                nct_id=nct_id,
                title=title,
                status=status,
                phase=phase,
                conditions=conditions,
                interventions=interventions,
                sponsors=sponsors,
                enrollment=enrollment,
                start_date=start_date,
                completion_date=completion_date,
                primary_outcome=primary_outcome,
                brief_summary=brief_summary,
                detailed_description=detailed_description,
                locations=locations,
                study_type=study_type,
                url=f"https://clinicaltrials.gov/study/{nct_id}"
            )

            logger.info(f"Fetched details for NCT ID: {nct_id}")

            # Cache results
            self.cache.set(cache_key, trial)

            return trial

        except Exception as e:
            logger.error(f"Fetch failed for NCT ID {nct_id}: {e}")
            raise

    def _extract_date(self, date_struct: Optional[Dict]) -> Optional[str]:
        """Extract date string from date structure."""
        if not date_struct:
            return None

        year = date_struct.get("year")
        month = date_struct.get("month")
        day = date_struct.get("day")

        if year:
            parts = [str(year)]
            if month:
                parts.append(str(month).zfill(2))
            if day:
                parts.append(str(day).zfill(2))
            return "-".join(parts)

        return None

    def batch_fetch_trials(self, nct_ids: List[str]) -> List[ClinicalTrial]:
        """
        Fetch details for multiple NCT IDs efficiently.

        Args:
            nct_ids: List of ClinicalTrials.gov NCT IDs

        Returns:
            List of ClinicalTrial objects
        """
        trials = []
        for nct_id in nct_ids:
            try:
                trial = self.fetch_trial_details(nct_id)
                trials.append(trial)
            except Exception as e:
                logger.warning(f"Failed to fetch NCT ID {nct_id}: {e}")
                continue

        logger.info(f"Successfully fetched {len(trials)}/{len(nct_ids)} trials")
        return trials

    def search_with_filters(
        self,
        disease: str,
        drug: Optional[str] = None,
        phase: Optional[str] = None,
        recruiting_only: bool = False,
        completed_only: bool = False,
        max_results: int = 100
    ) -> List[str]:
        """
        Advanced search with common filters for safety research.

        Args:
            disease: Disease/condition name
            drug: Drug/intervention name
            phase: Trial phase (PHASE1, PHASE2, PHASE3, PHASE4)
            recruiting_only: Only include recruiting trials
            completed_only: Only include completed trials
            max_results: Maximum results

        Returns:
            List of NCT IDs matching criteria
        """
        status = None
        if recruiting_only:
            status = "RECRUITING"
        elif completed_only:
            status = "COMPLETED"

        return self.search_trials(
            condition=disease,
            intervention=drug,
            phase=phase,
            status=status,
            max_results=max_results
        )

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
