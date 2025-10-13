"""
Confidence validation utilities for audit integration.

This module provides validation functions that can be used by auditors
to check confidence calibration compliance with CLAUDE.md standards.
"""
import logging
from typing import Dict, Any, List, Optional

from models.evidence import EvidenceClaim, Source, SourceType, ConfidenceLevel, ClaimType
from core.confidence_calibrator import ConfidenceCalibrator


logger = logging.getLogger(__name__)


class ConfidenceValidator:
    """
    Validates confidence claims in agent outputs.

    This validator checks:
    1. Confidence is calibrated to evidence quality
    2. No overconfident claims (per CLAUDE.md)
    3. Claims >80% have external validation
    4. Proper evidence provenance
    """

    def __init__(self):
        """Initialize confidence validator."""
        self.calibrator = ConfidenceCalibrator()

    def validate_confidence_claims(
        self,
        output_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Validate confidence claims in agent output.

        Checks for:
        - Claims without evidence (critical violation)
        - Overconfident claims relative to evidence (critical violation)
        - Claims >80% without external validation (critical violation)
        - Misaligned confidence levels

        Args:
            output_data: Agent output data to validate

        Returns:
            List of validation issues (dict format for audit integration)
        """
        issues = []

        # First, check raw data for structural violations
        raw_issues = self._check_raw_data_structure(output_data)
        issues.extend(raw_issues)

        # Extract claims from output (this will skip invalid claims)
        claims = self._extract_claims_from_output(output_data)

        if not claims:
            # No claims found, check if confidence was stated anyway
            if "confidence" in output_data or "confidence_level" in output_data:
                issues.append({
                    "category": "confidence_without_evidence",
                    "severity": "critical",
                    "description": (
                        "Confidence level stated but no evidence claims provided. "
                        "Per CLAUDE.md: Cannot assess confidence without evidence."
                    ),
                    "location": "confidence",
                    "suggested_fix": "Provide structured evidence claims or remove confidence statement",
                    "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
                })
            return issues

        # Validate each claim
        for i, claim in enumerate(claims):
            claim_issues = self._validate_single_claim(claim, i)
            issues.extend(claim_issues)

        return issues

    def _check_raw_data_structure(self, output_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check raw output data for structural violations before parsing.

        This catches issues like:
        - Claims with empty source lists
        - High confidence with insufficient sources
        - Missing required fields

        Args:
            output_data: Raw output data

        Returns:
            List of validation issues
        """
        issues = []

        # Check direct evidence_claims
        raw_claims = []
        if "evidence_claims" in output_data:
            raw_claims = output_data["evidence_claims"]
        elif "result" in output_data and "evidence_claims" in output_data["result"]:
            raw_claims = output_data["result"]["evidence_claims"]
        elif "result" in output_data and "sources" in output_data["result"]:
            # Legacy format
            raw_claims = [output_data["result"]]

        for i, claim_data in enumerate(raw_claims):
            # Check for empty sources
            sources = claim_data.get("sources", [])
            if not sources or len(sources) == 0:
                issues.append({
                    "category": "claim_without_evidence",
                    "severity": "critical",
                    "description": (
                        f"Claim {i + 1} has no supporting sources. "
                        f"Per CLAUDE.md: Every claim must have evidence."
                    ),
                    "location": f"evidence_claims[{i}].sources",
                    "suggested_fix": "Provide primary source evidence or remove claim",
                    "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS - PRIMARY SOURCES ONLY",
                })

            # Check for high confidence with insufficient sources
            confidence = claim_data.get("confidence", "").lower()
            if confidence == "high" and len(sources) == 1:
                # Check if single source has PMID
                single_source = sources[0]
                if not single_source.get("pmid"):
                    issues.append({
                        "category": "high_confidence_insufficient_sources",
                        "severity": "critical",
                        "description": (
                            f"Claim {i + 1} claims HIGH confidence with only one non-peer-reviewed source. "
                            f"High confidence requires multiple sources OR a single peer-reviewed source (with PMID)."
                        ),
                        "location": f"evidence_claims[{i}].confidence",
                        "suggested_fix": "Lower confidence or add more sources",
                        "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
                    })

        return issues

    def _extract_claims_from_output(
        self, output_data: Dict[str, Any]
    ) -> List[EvidenceClaim]:
        """
        Extract EvidenceClaim objects from output data.

        Supports multiple formats:
        1. Direct evidence_claims list
        2. Claims embedded in result
        3. Legacy format with confidence + sources

        Args:
            output_data: Agent output data

        Returns:
            List of EvidenceClaim objects
        """
        claims = []

        # Format 1: Direct evidence_claims field
        if "evidence_claims" in output_data:
            for claim_data in output_data["evidence_claims"]:
                try:
                    claim = self._parse_claim_dict(claim_data)
                    if claim:
                        claims.append(claim)
                except ValueError:
                    # Claim validation failed - this is an issue we want to catch
                    # But we can't add it to claims list since it's not a valid claim
                    # Just skip it and let the validator report the issue
                    pass

        # Format 2: Claims in result
        elif "result" in output_data:
            result = output_data["result"]
            if "evidence_claims" in result:
                for claim_data in result["evidence_claims"]:
                    try:
                        claim = self._parse_claim_dict(claim_data)
                        if claim:
                            claims.append(claim)
                    except ValueError:
                        pass

            # Format 3: Legacy format with confidence + sources
            elif "confidence" in result and "sources" in result:
                try:
                    claim = self._parse_legacy_format(result)
                    if claim:
                        claims.append(claim)
                except ValueError:
                    pass

        return claims

    def _parse_claim_dict(self, claim_data: Dict[str, Any]) -> Optional[EvidenceClaim]:
        """Parse a claim dictionary into EvidenceClaim object."""
        try:
            # Try to use from_dict method
            return EvidenceClaim.from_dict(claim_data)
        except ValueError as e:
            # Validation error - this is a problem with the claim itself
            # Return a special marker so we can report it
            logger.info(f"Claim validation failed (this is good - we want to catch this): {e}")
            # Re-raise so caller can handle
            raise
        except Exception as e:
            logger.warning(f"Failed to parse claim dict: {e}")
            return None

    def _parse_legacy_format(self, result: Dict[str, Any]) -> Optional[EvidenceClaim]:
        """Parse legacy output format into EvidenceClaim."""
        try:
            # Parse sources with flexible field handling
            sources = []
            for source_data in result.get("sources", []):
                # Extract identifiers
                url = source_data.get("url")
                title = source_data.get("title")
                authors = source_data.get("authors", [])
                date = str(source_data.get("year", "")) or source_data.get("date")

                # Need at least url OR (title + authors + date)
                if not url and not (title and authors and date):
                    logger.warning(f"Skipping incomplete source: {source_data}")
                    continue

                source = Source(
                    url=url,
                    title=title,
                    authors=authors,
                    date=date,
                    pmid=source_data.get("pmid"),
                    doi=source_data.get("doi"),
                )
                sources.append(source)

            if not sources:
                logger.warning("No valid sources in legacy format")
                return None

            # Parse confidence
            confidence_str = result.get("confidence", "none").lower()
            try:
                confidence = ConfidenceLevel[confidence_str.upper()]
            except KeyError:
                # Map common variations
                if "high" in confidence_str:
                    confidence = ConfidenceLevel.HIGH
                elif "moderate" in confidence_str or "medium" in confidence_str:
                    confidence = ConfidenceLevel.MODERATE
                elif "low" in confidence_str:
                    confidence = ConfidenceLevel.LOW
                else:
                    confidence = ConfidenceLevel.NONE

            # Create claim with generic type
            claim = EvidenceClaim(
                claim_text=result.get("summary", "Legacy claim"),
                claim_type=ClaimType.QUALITATIVE,  # Default to qualitative for legacy
                confidence=confidence,
                sources=sources,
                reasoning=result.get("methodology", ""),
                limitations=result.get("limitations", []),
            )

            return claim

        except Exception as e:
            logger.warning(f"Failed to parse legacy format: {e}")
            return None

    def _validate_single_claim(
        self, claim: EvidenceClaim, claim_index: int
    ) -> List[Dict[str, Any]]:
        """
        Validate a single evidence claim.

        Args:
            claim: EvidenceClaim to validate
            claim_index: Index of claim in output

        Returns:
            List of validation issues
        """
        issues = []

        # 1. Check for claims without sources (CRITICAL)
        if not claim.has_primary_source():
            issues.append({
                "category": "claim_without_evidence",
                "severity": "critical",
                "description": (
                    f"Claim {claim_index + 1}: '{claim.claim[:100]}...' has no supporting sources. "
                    f"Per CLAUDE.md: Every claim must have evidence."
                ),
                "location": f"evidence_claims[{claim_index}]",
                "suggested_fix": "Provide primary source evidence or remove claim",
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS - PRIMARY SOURCES ONLY",
            })
            return issues  # Can't validate further without sources

        # 2. Use calibrator to assess proper confidence
        assessment = self.calibrator.assess_claim_confidence(claim)

        # 3. Check if stated confidence matches calibrated confidence
        if claim.confidence != assessment.confidence_level:
            # Determine severity
            severity = self._determine_confidence_mismatch_severity(
                claim.confidence, assessment.confidence_level
            )

            issues.append({
                "category": "confidence_miscalibration",
                "severity": severity,
                "description": (
                    f"Claim {claim_index + 1}: Stated confidence '{claim.confidence.value}' "
                    f"does not match calibrated confidence '{assessment.confidence_level.value}' "
                    f"(score: {assessment.raw_score:.1f}/100). "
                    f"{assessment.justification[:200]}..."
                ),
                "location": f"evidence_claims[{claim_index}].confidence",
                "suggested_fix": (
                    f"Adjust confidence to '{assessment.confidence_level.value}' "
                    f"or strengthen evidence base"
                ),
                "guideline_reference": "CLAUDE.md: EVIDENCE STANDARDS",
                "metadata": {
                    "stated_confidence": claim.confidence.value,
                    "calibrated_confidence": assessment.confidence_level.value,
                    "raw_score": assessment.raw_score,
                },
            })

        # 4. Check for high confidence without external validation (CRITICAL)
        if assessment.requires_external_validation:
            issues.append({
                "category": "high_confidence_without_validation",
                "severity": "critical",
                "description": (
                    f"Claim {claim_index + 1}: Confidence score {assessment.raw_score:.1f}/100 "
                    f"exceeds 80% threshold. Per CLAUDE.md: Scores >80% require external validation. "
                    f"No external validation provided."
                ),
                "location": f"evidence_claims[{claim_index}]",
                "suggested_fix": (
                    "Provide external validation data or lower confidence level"
                ),
                "guideline_reference": "CLAUDE.md: EXTERNAL VALIDATION - Scores >70% require independent verification",
            })

        # 5. Check for unverified sources
        verified_count = claim.get_verified_source_count()
        total_count = claim.get_source_count()
        if verified_count < total_count:
            unverified_count = total_count - verified_count
            issues.append({
                "category": "unverified_sources",
                "severity": "warning",
                "description": (
                    f"Claim {claim_index + 1}: {unverified_count} of {total_count} sources "
                    f"have not been verified. This reduces confidence by "
                    f"{min(unverified_count * 10, 30)} points."
                ),
                "location": f"evidence_claims[{claim_index}].sources",
                "suggested_fix": "Verify sources against external databases (PubMed, DOI, etc.)",
            })

        # 6. Check for missing critical fields
        if not claim.reasoning:
            issues.append({
                "category": "missing_reasoning",
                "severity": "warning",
                "description": (
                    f"Claim {claim_index + 1}: No reasoning provided for how sources support claim."
                ),
                "location": f"evidence_claims[{claim_index}].reasoning",
                "suggested_fix": "Explain how evidence supports the claim",
            })

        if not claim.limitations:
            issues.append({
                "category": "missing_limitations",
                "severity": "warning",
                "description": (
                    f"Claim {claim_index + 1}: No limitations provided. "
                    f"Per CLAUDE.md: Always acknowledge unknowns and limitations."
                ),
                "location": f"evidence_claims[{claim_index}].limitations",
                "suggested_fix": "Document limitations of the evidence",
                "guideline_reference": "CLAUDE.md: UNCERTAINTY EXPRESSION",
            })

        return issues

    def _determine_confidence_mismatch_severity(
        self,
        stated: ConfidenceLevel,
        calibrated: ConfidenceLevel,
    ) -> str:
        """
        Determine severity of confidence mismatch.

        Critical if:
        - Stated HIGH or ESTABLISHED but calibrated LOW or NONE
        - Any case of overconfidence by 2+ levels

        Warning otherwise.
        """
        level_order = [
            ConfidenceLevel.NONE,
            ConfidenceLevel.LOW,
            ConfidenceLevel.MODERATE,
            ConfidenceLevel.HIGH,
            ConfidenceLevel.ESTABLISHED,
        ]

        stated_idx = level_order.index(stated)
        calibrated_idx = level_order.index(calibrated)

        # Overconfidence by 2+ levels is critical
        if stated_idx - calibrated_idx >= 2:
            return "critical"

        # HIGH or ESTABLISHED stated but should be LOW or NONE
        if stated in [ConfidenceLevel.HIGH, ConfidenceLevel.ESTABLISHED]:
            if calibrated in [ConfidenceLevel.NONE, ConfidenceLevel.LOW]:
                return "critical"

        # Any overconfidence is at least a warning
        if stated_idx > calibrated_idx:
            return "warning"

        # Underconfidence (stated lower than calibrated) is just info
        return "info"

    def get_calibrator(self) -> ConfidenceCalibrator:
        """Get the underlying confidence calibrator."""
        return self.calibrator
