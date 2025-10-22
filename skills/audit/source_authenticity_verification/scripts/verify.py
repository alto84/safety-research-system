"""
Source Authenticity Verification Skill

Validates source authenticity and detects fabricated sources in literature reviews.
This is a deterministic skill that performs:
- PMID format and pattern validation
- URL format and accessibility verification
- DOI format validation
- Placeholder pattern detection
- Sequential digit pattern detection

Type: Deterministic (100% code-based, no LLM)
Category: Audit
Version: 1.0.0
"""

from typing import Dict, Any, List
import logging
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from skills.base import DeterministicSkill, SkillMetadata, SkillCategory, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class SourceAuthenticityVerification(DeterministicSkill):
    """
    Verifies source authenticity and detects fabrication.

    This skill performs multiple validation checks:
    1. PMID format validation (8 digits, not sequential patterns)
    2. URL format and accessibility verification
    3. DOI format validation
    4. Placeholder pattern detection (e.g., "Example Study", "Smith et al.")
    5. Generic/fake source field detection

    All checks are deterministic (no LLM) and follow CLAUDE.md compliance.
    """

    # Placeholder patterns for titles and authors
    PLACEHOLDER_PATTERNS = [
        # Generic placeholder titles
        (r'(?i)example\s+study', 'title', "Generic 'Example Study' placeholder detected"),
        (r'(?i)sample\s+research', 'title', "Generic 'Sample Research' placeholder detected"),
        (r'(?i)test\s+paper', 'title', "Generic 'Test Paper' placeholder detected"),
        (r'(?i)placeholder', 'title', "Explicit placeholder text detected"),
        (r'(?i)lorem\s+ipsum', 'title', "Lorem ipsum placeholder text detected"),
        (r'(?i)to\s+be\s+determined', 'title', "TBD placeholder detected"),
        (r'(?i)tbd', 'title', "TBD abbreviation detected"),

        # Generic author patterns
        (r'(?i)^smith\s+et\s+al\.?$', 'authors', "Generic 'Smith et al.' placeholder detected"),
        (r'(?i)^jones\s+et\s+al\.?$', 'authors', "Generic 'Jones et al.' placeholder detected"),
        (r'(?i)^doe\s+et\s+al\.?$', 'authors', "Generic 'Doe et al.' placeholder detected"),
        (r'(?i)^author\s+name', 'authors', "Generic 'Author Name' placeholder detected"),
        (r'(?i)^et\s+al\.?$', 'authors', "Incomplete 'et al.' without actual authors"),
    ]

    # Placeholder URL patterns
    PLACEHOLDER_URL_PATTERNS = [
        r'example\.com',
        r'example\.org',
        r'test\.com',
        r'placeholder',
        r'fake',
        r'dummy',
        r'localhost',
        r'127\.0\.0\.1',
    ]

    # Fake PMID patterns (sequential, repetitive)
    FAKE_PMID_PATTERNS = [
        '12345678', '87654321', '11111111', '22222222', '33333333',
        '44444444', '55555555', '66666666', '77777777', '88888888',
        '99999999', '00000000'
    ]

    def _get_metadata(self) -> SkillMetadata:
        """Get skill metadata."""
        return SkillMetadata(
            name="source_authenticity_verification",
            version="1.0.0",
            category=SkillCategory.AUDIT,
            skill_type=None,  # Set by DeterministicSkill parent
            description=(
                "Validates source authenticity, detects fabricated PMIDs/URLs, "
                "and identifies placeholder patterns"
            ),
            author="Safety Research System",
        )

    def _get_input_schema(self) -> List[SkillInput]:
        """Define input schema."""
        return [
            SkillInput(
                name="sources",
                type_hint="List[Dict[str, Any]]",
                description="List of source dictionaries with fields: pmid, url, doi, title, authors",
                required=True,
            ),
        ]

    def _get_output_schema(self) -> List[SkillOutput]:
        """Define output schema."""
        return [
            SkillOutput(
                name="authentic_sources",
                type_hint="List[Dict[str, Any]]",
                description="Sources that passed all authenticity checks",
            ),
            SkillOutput(
                name="fabricated_sources",
                type_hint="List[Dict[str, Any]]",
                description="Sources flagged as potentially fabricated",
            ),
            SkillOutput(
                name="issues",
                type_hint="List[Dict[str, Any]]",
                description="Detailed validation issues found",
                schema={
                    "category": "str (fabricated_source, invalid_pmid_format, etc.)",
                    "severity": "str (critical, warning)",
                    "description": "str (human-readable description)",
                    "location": "str (e.g., sources[0].pmid)",
                    "suggested_fix": "str (actionable fix)",
                    "guideline_reference": "str (CLAUDE.md reference)",
                },
            ),
        ]

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate input parameters.

        Args:
            inputs: Input dictionary with 'sources' key

        Returns:
            True if valid

        Raises:
            ValueError: If inputs are invalid
        """
        if "sources" not in inputs:
            raise ValueError("Required input 'sources' not provided")

        sources = inputs["sources"]
        if not isinstance(sources, list):
            raise ValueError("Input 'sources' must be a list")

        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                raise ValueError(f"Source at index {i} must be a dictionary")

        return True

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute source authenticity verification.

        Args:
            inputs: Dictionary with 'sources' key containing list of sources

        Returns:
            Dictionary with authentic_sources, fabricated_sources, and issues
        """
        sources = inputs["sources"]

        authentic_sources = []
        fabricated_sources = []
        all_issues = []

        for i, source in enumerate(sources):
            issues = self._verify_source(source, i)

            if issues:
                # Has issues - flag as potentially fabricated
                fabricated_sources.append({
                    **source,
                    "_verification_issues": issues,
                })
                all_issues.extend(issues)
            else:
                # No issues - authentic
                authentic_sources.append(source)

        logger.info(
            f"Source authenticity verification complete: "
            f"{len(authentic_sources)} authentic, "
            f"{len(fabricated_sources)} fabricated, "
            f"{len(all_issues)} total issues"
        )

        return {
            "authentic_sources": authentic_sources,
            "fabricated_sources": fabricated_sources,
            "issues": all_issues,
            "summary": {
                "total_sources": len(sources),
                "authentic_count": len(authentic_sources),
                "fabricated_count": len(fabricated_sources),
                "total_issues": len(all_issues),
            },
        }

    def _verify_source(self, source: Dict[str, Any], source_index: int) -> List[Dict[str, Any]]:
        """
        Verify a single source for authenticity.

        Args:
            source: Source dictionary to verify
            source_index: Index in sources list (for error reporting)

        Returns:
            List of validation issues (empty if authentic)
        """
        issues = []

        # Check 1: Placeholder patterns in title
        title = source.get('title', '') or ''
        for pattern, field, description in self.PLACEHOLDER_PATTERNS:
            if field == 'title' and re.search(pattern, title):
                issues.append({
                    "category": "fabricated_source",
                    "severity": "critical",
                    "description": (
                        f"Source {source_index + 1}: {description}. "
                        f"Title: '{title}'. This appears to be fabricated data."
                    ),
                    "location": f"sources[{source_index}].title",
                    "suggested_fix": "Replace with real, verifiable source",
                    "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION",
                })

        # Check 2: Placeholder patterns in authors
        authors = source.get('authors', '') or ''
        if isinstance(authors, list):
            authors = ', '.join(authors)

        for pattern, field, description in self.PLACEHOLDER_PATTERNS:
            if field == 'authors' and re.search(pattern, str(authors)):
                issues.append({
                    "category": "fabricated_source",
                    "severity": "critical",
                    "description": (
                        f"Source {source_index + 1}: {description}. "
                        f"Authors: '{authors}'. This appears to be fabricated data."
                    ),
                    "location": f"sources[{source_index}].authors",
                    "suggested_fix": "Replace with real, verifiable authors",
                    "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION",
                })

        # Check 3: PMID validation
        if 'pmid' in source:
            pmid_issues = self._verify_pmid(source['pmid'], source_index)
            issues.extend(pmid_issues)

        # Check 4: URL validation
        if 'url' in source:
            url_issues = self._verify_url(source['url'], source_index)
            issues.extend(url_issues)

        # Check 5: DOI validation
        if 'doi' in source:
            doi_issues = self._verify_doi(source['doi'], source_index)
            issues.extend(doi_issues)

        return issues

    def _verify_pmid(self, pmid: Any, source_index: int) -> List[Dict[str, Any]]:
        """Verify PMID format and detect fabrication patterns."""
        issues = []
        pmid = str(pmid)

        # Format validation (1-8 digits)
        if not re.match(r'^\d{1,8}$', pmid):
            issues.append({
                "category": "invalid_pmid_format",
                "severity": "critical",
                "description": (
                    f"Source {source_index + 1}: PMID '{pmid}' is not a valid format. "
                    f"PMIDs must be 1-8 digit numbers."
                ),
                "location": f"sources[{source_index}].pmid",
                "suggested_fix": "Use valid PMID or remove PMID field",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
            })
            return issues  # Skip further checks if format is wrong

        # Check for obvious fake PMIDs (in known fake list)
        if pmid in self.FAKE_PMID_PATTERNS:
            issues.append({
                "category": "fabricated_pmid",
                "severity": "critical",
                "description": (
                    f"Source {source_index + 1}: PMID '{pmid}' appears to be fabricated "
                    f"(sequential or repetitive pattern). This is not a real PubMed ID."
                ),
                "location": f"sources[{source_index}].pmid",
                "suggested_fix": "Replace with real, verifiable PMID",
                "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION",
            })

        # Check for sequential digit patterns
        if len(pmid) == 8 and self._is_sequential_pattern(pmid):
            issues.append({
                "category": "fabricated_pmid",
                "severity": "critical",
                "description": (
                    f"Source {source_index + 1}: PMID '{pmid}' contains sequential pattern, "
                    f"suggesting fabrication. Real PMIDs are not sequential."
                ),
                "location": f"sources[{source_index}].pmid",
                "suggested_fix": "Replace with real, verifiable PMID",
                "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION",
            })

        return issues

    def _is_sequential_pattern(self, pmid: str) -> bool:
        """
        Check if PMID contains sequential digit pattern.

        Detects patterns like: 1234, 2345, 3456, ..., 9876, 8765, etc.

        Args:
            pmid: PMID string to check

        Returns:
            True if sequential pattern detected
        """
        # Ascending sequences
        ascending = ['1234', '2345', '3456', '4567', '5678', '6789']
        for chunk in ascending:
            if chunk in pmid:
                return True

        # Descending sequences
        descending = ['9876', '8765', '7654', '6543', '5432', '4321']
        for chunk in descending:
            if chunk in pmid:
                return True

        return False

    def _verify_url(self, url: str, source_index: int) -> List[Dict[str, Any]]:
        """Verify URL format, detect placeholders, and check accessibility."""
        issues = []

        # Format validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                issues.append({
                    "category": "invalid_url_format",
                    "severity": "critical",
                    "description": (
                        f"Source {source_index + 1}: URL '{url}' is not properly formatted. "
                        f"Must include scheme (http/https) and domain."
                    ),
                    "location": f"sources[{source_index}].url",
                    "suggested_fix": "Use properly formatted, verifiable URL",
                    "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
                })
                return issues  # Skip further checks if format is wrong
        except Exception as e:
            issues.append({
                "category": "invalid_url_format",
                "severity": "critical",
                "description": (
                    f"Source {source_index + 1}: URL '{url}' cannot be parsed: {str(e)}"
                ),
                "location": f"sources[{source_index}].url",
                "suggested_fix": "Use properly formatted, verifiable URL",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
            })
            return issues

        # Placeholder pattern detection
        for pattern in self.PLACEHOLDER_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                issues.append({
                    "category": "fabricated_url",
                    "severity": "critical",
                    "description": (
                        f"Source {source_index + 1}: URL '{url}' contains placeholder pattern '{pattern}'. "
                        f"This is not a real, verifiable source."
                    ),
                    "location": f"sources[{source_index}].url",
                    "suggested_fix": "Replace with real, verifiable URL",
                    "guideline_reference": "CLAUDE.md: SCORE FABRICATION PROHIBITION",
                })
                return issues  # Don't check accessibility for placeholders

        # Accessibility check (HTTP HEAD request)
        accessible = self._check_url_accessibility(url)
        if not accessible:
            issues.append({
                "category": "inaccessible_url",
                "severity": "critical",
                "description": (
                    f"Source {source_index + 1}: URL '{url}' is not accessible. "
                    f"HTTP request failed or timed out. Cannot verify this source."
                ),
                "location": f"sources[{source_index}].url",
                "suggested_fix": "Verify URL is correct and accessible, or use alternative identifier",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
            })

        return issues

    def _check_url_accessibility(self, url: str, timeout: int = 5) -> bool:
        """
        Check if URL is accessible via HTTP HEAD request.

        Args:
            url: URL to check
            timeout: Request timeout in seconds (default: 5)

        Returns:
            True if URL is accessible (HTTP 2xx or 3xx)
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return 200 <= response.status_code < 400
        except requests.exceptions.RequestException as e:
            logger.debug(f"URL accessibility check failed for {url}: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error checking URL {url}: {str(e)}")
            return False

    def _verify_doi(self, doi: Any, source_index: int) -> List[Dict[str, Any]]:
        """Verify DOI format."""
        issues = []

        # Skip if doi is None
        if doi is None:
            return issues

        doi = str(doi)

        # DOI format: 10.xxxx/yyyy (basic validation)
        if not re.match(r'^10\.\d{4,}/\S+$', doi):
            issues.append({
                "category": "invalid_doi_format",
                "severity": "warning",
                "description": (
                    f"Source {source_index + 1}: DOI '{doi}' does not match standard format. "
                    f"DOIs should start with '10.' followed by registrant code and suffix."
                ),
                "location": f"sources[{source_index}].doi",
                "suggested_fix": "Verify DOI format (e.g., 10.1234/example)",
            })

        return issues


# Convenience function for direct usage
def verify_source_authenticity(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function to verify source authenticity.

    Args:
        sources: List of source dictionaries

    Returns:
        Verification result with authentic_sources, fabricated_sources, and issues
    """
    skill = SourceAuthenticityVerification()
    return skill.execute({"sources": sources})
