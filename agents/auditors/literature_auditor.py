"""Literature review auditor agent."""
from typing import Dict, Any, List
import logging
import re
import requests
from urllib.parse import urlparse

from agents.base_auditor import BaseAuditor


logger = logging.getLogger(__name__)


class LiteratureAuditor(BaseAuditor):
    """
    Auditor agent for validating literature review outputs.

    This auditor checks:
    - Source quality and credibility
    - Evidence grading accuracy
    - Citation completeness
    - Proper uncertainty expression
    - Compliance with CLAUDE.md guidelines
    """

    def __init__(self, agent_id: str = "lit_auditor_01", config: Dict[str, Any] = None, enable_intelligent_audit: bool = False):
        """Initialize literature review auditor."""
        super().__init__(agent_id, config, enable_intelligent_audit)
        self.version = "1.0.0"

    def _load_validation_criteria(self) -> Dict[str, Any]:
        """
        Load validation criteria for literature reviews.

        Returns:
            Dictionary of validation criteria
        """
        return {
            "required_fields": [
                "summary",
                "sources",
                "evidence_level",
                "confidence",
                "limitations",
                "methodology",
            ],
            "min_sources": 2,
            "required_source_fields": ["title", "authors", "year"],
            "max_confidence_without_validation": "moderate",
        }

    def validate(
        self,
        task_input: Dict[str, Any],
        task_output: Dict[str, Any],
        task_metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Validate literature review output.

        Args:
            task_input: Original input given to worker
            task_output: Output from literature worker
            task_metadata: Additional metadata

        Returns:
            Audit result dictionary
        """
        logger.info("LiteratureAuditor: Starting validation")

        issues = []
        passed_checks = []
        failed_checks = []

        result = task_output.get("result", {})

        # Check 1: Anti-fabrication compliance (CRITICAL)
        fabrication_issues = self.check_anti_fabrication_compliance(task_output)
        if fabrication_issues:
            issues.extend(fabrication_issues)
            failed_checks.append("anti_fabrication_compliance")
        else:
            passed_checks.append("anti_fabrication_compliance")

        # Check 2: Completeness
        completeness_issues = self.check_completeness(
            task_output,
            self.validation_criteria["required_fields"]
        )
        if completeness_issues:
            issues.extend(completeness_issues)
            failed_checks.append("completeness")
        else:
            passed_checks.append("completeness")

        # Check 3: Source quality
        source_issues = self._check_source_quality(result)
        if source_issues:
            issues.extend(source_issues)
            failed_checks.append("source_quality")
        else:
            passed_checks.append("source_quality")

        # Check 4: Evidence grading
        evidence_issues = self._check_evidence_grading(result)
        if evidence_issues:
            issues.extend(evidence_issues)
            failed_checks.append("evidence_grading")
        else:
            passed_checks.append("evidence_grading")

        # Check 5: Citation completeness
        citation_issues = self._check_citations(result)
        if citation_issues:
            issues.extend(citation_issues)
            failed_checks.append("citation_completeness")
        else:
            passed_checks.append("citation_completeness")

        # Check 6: Evidence provenance (CRITICAL)
        provenance_issues = self.check_evidence_provenance(task_output)
        if provenance_issues:
            issues.extend(provenance_issues)
            failed_checks.append("evidence_provenance")
        else:
            passed_checks.append("evidence_provenance")

        # Determine overall status
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        if critical_issues:
            status = "failed"
        elif issues:
            status = "partial"
        else:
            status = "passed"

        # Generate summary
        summary = self._generate_summary(status, issues, passed_checks)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        logger.info(
            f"LiteratureAuditor: Validation complete. Status: {status}, "
            f"Issues: {len(issues)}"
        )

        return {
            "status": status,
            "summary": summary,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "issues": issues,
            "recommendations": recommendations,
        }

    def _verify_source_authenticity(self, source: Dict[str, Any], source_index: int) -> List[Dict[str, Any]]:
        """
        Verify that a source is authentic and not fabricated.

        This method performs multiple checks:
        1. PMID format validation (must be 8 digits, not obvious fakes like "12345678")
        2. URL accessibility check (HTTP HEAD request with timeout)
        3. Detection of common placeholder patterns
        4. Verification that source fields aren't generic/fake

        Args:
            source: Source dictionary to verify
            source_index: Index of source in sources list (for error reporting)

        Returns:
            List of critical issues for any fabricated sources
        """
        issues = []

        # Pattern detection for common placeholders
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

        # Check for placeholder patterns in title
        title = source.get('title', '')
        for pattern, field, description in PLACEHOLDER_PATTERNS:
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

        # Check for placeholder patterns in authors
        authors = source.get('authors', '')
        if isinstance(authors, list):
            authors = ', '.join(authors)

        for pattern, field, description in PLACEHOLDER_PATTERNS:
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

        # PMID validation
        if 'pmid' in source:
            pmid = str(source['pmid'])

            # Check PMID format (must be 8 digits for modern PMIDs, 1-8 digits allowed)
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

            # Check for obvious fake PMIDs (sequential patterns)
            if re.match(r'^(12345678|87654321|11111111|22222222|33333333|44444444|55555555|66666666|77777777|88888888|99999999|00000000)$', pmid):
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

            # Check for sequential digits in PMID (e.g., "12345678", "23456789")
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

        # URL validation
        if 'url' in source:
            url = source['url']

            # Check URL format
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

            # Check for placeholder URLs
            placeholder_url_patterns = [
                r'example\.com',
                r'example\.org',
                r'test\.com',
                r'placeholder',
                r'fake',
                r'dummy',
                r'localhost',
                r'127\.0\.0\.1',
            ]

            for pattern in placeholder_url_patterns:
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

            # Attempt to verify URL accessibility (only if not already flagged)
            if not any(issue.get('category') in ['invalid_url_format', 'fabricated_url'] for issue in issues):
                url_accessible = self._check_url_accessibility(url)
                if not url_accessible:
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

        # Check DOI format if present
        if 'doi' in source:
            doi = source['doi']
            # DOI format: 10.xxxx/yyyy (basic validation)
            # Only validate if doi is not None
            if doi is not None and not re.match(r'^10\.\d{4,}/\S+$', doi):
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

    def _is_sequential_pattern(self, pmid: str) -> bool:
        """
        Check if PMID contains sequential digit pattern.

        Args:
            pmid: PMID string to check

        Returns:
            True if sequential pattern detected, False otherwise
        """
        # Check for ascending sequence (e.g., 12345678, 23456789)
        for i in range(len(pmid) - 3):
            if len(pmid) >= 4:
                chunk = pmid[i:i+4]
                if chunk == '1234' or chunk == '2345' or chunk == '3456' or \
                   chunk == '4567' or chunk == '5678' or chunk == '6789':
                    return True

        # Check for descending sequence (e.g., 87654321)
        for i in range(len(pmid) - 3):
            if len(pmid) >= 4:
                chunk = pmid[i:i+4]
                if chunk == '9876' or chunk == '8765' or chunk == '7654' or \
                   chunk == '6543' or chunk == '5432' or chunk == '4321':
                    return True

        return False

    def _check_url_accessibility(self, url: str, timeout: int = 5) -> bool:
        """
        Check if a URL is accessible via HTTP HEAD request.

        Args:
            url: URL to check
            timeout: Request timeout in seconds (default: 5)

        Returns:
            True if URL is accessible (HTTP 2xx or 3xx), False otherwise
        """
        try:
            # Use HEAD request to minimize bandwidth
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            # Consider 2xx and 3xx status codes as accessible
            return 200 <= response.status_code < 400
        except requests.exceptions.RequestException as e:
            # Log the exception for debugging
            logger.debug(f"URL accessibility check failed for {url}: {str(e)}")
            return False
        except Exception as e:
            # Catch any other unexpected errors
            logger.warning(f"Unexpected error checking URL {url}: {str(e)}")
            return False

    def _check_source_quality(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check quality and credibility of sources."""
        issues = []
        sources = result.get("sources", [])

        if len(sources) < self.validation_criteria["min_sources"]:
            issues.append({
                "category": "insufficient_sources",
                "severity": "warning",
                "description": (
                    f"Only {len(sources)} sources provided. "
                    f"Minimum {self.validation_criteria['min_sources']} recommended."
                ),
                "location": "sources",
                "suggested_fix": "Include additional high-quality sources",
            })

        # Check each source for authenticity and completeness
        for i, source in enumerate(sources):
            # CRITICAL: Verify source authenticity first
            authenticity_issues = self._verify_source_authenticity(source, i)
            issues.extend(authenticity_issues)

            # Check each source has required fields
            missing_fields = [
                field for field in self.validation_criteria["required_source_fields"]
                if field not in source
            ]
            if missing_fields:
                issues.append({
                    "category": "incomplete_source",
                    "severity": "warning",
                    "description": (
                        f"Source {i+1} missing fields: {', '.join(missing_fields)}"
                    ),
                    "location": f"sources[{i}]",
                    "suggested_fix": f"Add missing fields: {', '.join(missing_fields)}",
                })

        return issues

    def _check_evidence_grading(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check evidence level grading."""
        issues = []

        evidence_level = result.get("evidence_level", "").lower()
        confidence = result.get("confidence", "").lower()

        # Check for high confidence without strong evidence
        if "high" in confidence and evidence_level not in ["high", "level 1"]:
            issues.append({
                "category": "confidence_evidence_mismatch",
                "severity": "critical",
                "description": (
                    f"High confidence claimed with {evidence_level} evidence level. "
                    "This violates evidence standards."
                ),
                "location": "confidence",
                "suggested_fix": "Lower confidence level or provide stronger evidence",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
            })

        return issues

    def _check_citations(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check citation completeness."""
        issues = []

        sources = result.get("sources", [])

        # Check if sources have proper identifiers (PMID, DOI, etc.)
        for i, source in enumerate(sources):
            has_identifier = any(
                key in source for key in ["pmid", "doi", "url", "trial_id"]
            )
            if not has_identifier:
                issues.append({
                    "category": "missing_identifier",
                    "severity": "info",
                    "description": f"Source {i+1} lacks identifier (PMID, DOI, URL)",
                    "location": f"sources[{i}]",
                    "suggested_fix": "Add PMID, DOI, or URL for verification",
                })

        return issues

    def _generate_summary(
        self, status: str, issues: List[Dict[str, Any]], passed_checks: List[str]
    ) -> str:
        """Generate audit summary."""
        if status == "passed":
            return (
                f"Literature review validation passed. "
                f"All {len(passed_checks)} checks completed successfully."
            )
        elif status == "partial":
            return (
                f"Literature review validation partially passed. "
                f"{len(passed_checks)} checks passed, {len(issues)} issues found. "
                f"No critical issues."
            )
        else:  # failed
            critical_count = len([i for i in issues if i.get("severity") == "critical"])
            return (
                f"Literature review validation failed. "
                f"{critical_count} critical issues found requiring immediate attention."
            )

    def _generate_recommendations(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on issues found."""
        recommendations = []

        # Group issues by category
        categories = set(issue.get("category") for issue in issues)

        if "fabricated_source" in categories or "fabricated_pmid" in categories or "fabricated_url" in categories:
            recommendations.append(
                "CRITICAL: Replace all fabricated sources with real, verifiable citations. "
                "Use actual PubMed articles, DOIs, or accessible URLs."
            )

        if "invalid_pmid_format" in categories:
            recommendations.append(
                "Verify PMID format (1-8 digits) or use alternative identifiers (DOI, URL)"
            )

        if "inaccessible_url" in categories:
            recommendations.append(
                "Verify all URLs are accessible and correct. Consider using DOI or PMID for academic sources."
            )

        if "score_fabrication" in categories:
            recommendations.append(
                "Remove fabricated scores and rely on evidence-based assessment"
            )

        if "missing_evidence" in categories:
            recommendations.append(
                "Provide clear evidence chain with sources and methodology"
            )

        if "insufficient_sources" in categories:
            recommendations.append(
                "Expand literature search to include more high-quality sources"
            )

        if "confidence_evidence_mismatch" in categories:
            recommendations.append(
                "Align confidence levels with strength of evidence"
            )

        return recommendations
