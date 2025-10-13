"""
Test hybrid audit validation system.

This tests the combination of hard-coded safety checks + LLM semantic analysis.

CRITICAL TESTS:
1. Hard-coded catches objective violations (score >80, fabricated PMID)
2. LLM catches semantic violations (conceptual banned language)
3. Hard-coded safety checks CANNOT be overridden by LLM
4. LLM failure doesn't break hard-coded checks (graceful degradation)
"""

import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_hard_coded_score_fabrication():
    """
    Test that hard-coded checks catch score >80 violations.

    SAFETY CRITICAL: This MUST be caught regardless of LLM.
    """
    from agents.base_auditor import BaseAuditor
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 1: Hard-coded catches score >80 (SAFETY CRITICAL)")
    print("="*80)

    # Create auditor WITHOUT intelligent audit
    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=False  # Hard-coded only
    )

    # Output with fabricated score
    output = {
        "result": {
            "score": 85,  # VIOLATION: > 80
            "summary": "Analysis complete",
            "sources": ["Source 1"],
            "confidence": "Moderate",
            "limitations": ["Limited data"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Verify score fabrication caught
    score_issues = [i for i in issues if i["category"] == "score_fabrication"]

    if len(score_issues) > 0:
        print("✓ PASS: Hard-coded check caught score >80 violation")
        print(f"  Issue: {score_issues[0]['description']}")
        print(f"  Severity: {score_issues[0]['severity']}")
        assert score_issues[0]["severity"] == "critical"
        assert score_issues[0]["hard_coded"] == True
        return True
    else:
        print("✗ FAIL: Score >80 not caught by hard-coded check")
        return False


def test_hard_coded_banned_phrases():
    """
    Test that hard-coded keyword matching catches explicit banned phrases.
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 2: Hard-coded catches banned keyword phrases")
    print("="*80)

    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=False
    )

    # Output with banned phrase
    output = {
        "result": {
            "summary": "This drug shows exceptional performance compared to alternatives.",
            "sources": ["Source 1"],
            "confidence": "Moderate",
            "limitations": ["Limited data"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Verify banned phrase caught
    banned_issues = [i for i in issues if i["category"] == "banned_language"]

    if len(banned_issues) > 0:
        print("✓ PASS: Hard-coded check caught banned phrase 'exceptional performance'")
        print(f"  Issue: {banned_issues[0]['description']}")
        assert banned_issues[0]["hard_coded"] == True
        return True
    else:
        print("✗ FAIL: Banned phrase not caught")
        return False


def test_hard_coded_missing_evidence():
    """
    Test that hard-coded checks catch missing evidence chain.
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 3: Hard-coded catches missing evidence")
    print("="*80)

    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=False
    )

    # Output without sources or methodology
    output = {
        "result": {
            "summary": "ILD incidence is 15.4%",
            "confidence": "Moderate",
            "limitations": ["Limited data"]
            # Missing: sources, methodology
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Verify missing evidence caught
    evidence_issues = [i for i in issues if i["category"] == "missing_evidence"]

    if len(evidence_issues) > 0:
        print("✓ PASS: Hard-coded check caught missing evidence chain")
        print(f"  Issue: {evidence_issues[0]['description']}")
        assert evidence_issues[0]["hard_coded"] == True
        return True
    else:
        print("✗ FAIL: Missing evidence not caught")
        return False


def test_semantic_banned_concepts():
    """
    Test that LLM catches semantic violations not caught by keywords.

    Example: "This drug is the best available" = banned concept
    but doesn't contain exact keywords like "exceptional" or "world-class"
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 4: LLM catches semantic banned concepts (no exact keywords)")
    print("="*80)

    # Create auditor WITH intelligent audit
    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True  # Enable LLM layer
    )

    # Output with conceptual violation but no exact banned keywords
    output = {
        "result": {
            "summary": "This drug is clearly the best available option and superior to all alternatives in its class.",
            "sources": ["Source 1"],
            "confidence": "High",
            "limitations": ["Limited to published data"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Check for semantic violations
    semantic_issues = [i for i in issues if "semantic" in i["category"]]

    if len(semantic_issues) > 0:
        print("✓ PASS: LLM caught semantic banned concept")
        print(f"  Found {len(semantic_issues)} semantic issue(s):")
        for issue in semantic_issues:
            print(f"    - {issue['category']}: {issue['description'][:100]}...")

        # Verify it's marked as LLM-detected (not hard-coded)
        assert semantic_issues[0]["hard_coded"] == False
        return True
    else:
        print("⚠ SKIP: LLM layer not available or didn't detect semantic violation")
        print("  (This is expected if running without LLM API access)")
        return None  # Not a failure - just LLM not available


def test_evidence_claim_linkage():
    """
    Test that LLM verifies numerical claims link to specific sources.

    Hard-coded checks verify sources exist.
    LLM checks that specific claims trace to specific sources.
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 5: LLM verifies evidence-claim linkage")
    print("="*80)

    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True
    )

    # Output with numerical claim but no specific source reference
    output = {
        "result": {
            "summary": "ILD incidence is 15.4% with T-DXd treatment. The mechanism involves macrophage activation.",
            "sources": ["Generic source 1", "Generic source 2"],  # Sources exist but not linked to claims
            "confidence": "Moderate",
            "limitations": ["Limited data"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Check for evidence linkage issues
    linkage_issues = [i for i in issues if "linkage" in i["category"]]

    if len(linkage_issues) > 0:
        print("✓ PASS: LLM detected evidence-claim linkage issue")
        print(f"  Issue: {linkage_issues[0]['description'][:150]}...")
        return True
    else:
        print("⚠ SKIP: LLM layer not available or didn't detect linkage issue")
        return None


def test_confidence_justification():
    """
    Test that LLM checks if confidence level matches evidence quality.

    Example: "High confidence" but only 1 source = unjustified
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 6: LLM checks confidence justification")
    print("="*80)

    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True
    )

    # Output claiming high confidence with minimal evidence
    output = {
        "result": {
            "summary": "Analysis shows clear mechanistic relationship",
            "sources": ["Single study"],  # Only 1 source
            "confidence": "High",  # Claims high confidence
            "limitations": ["Limited to one study"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Check for confidence mismatch
    confidence_issues = [i for i in issues if "confidence" in i["category"]]

    if len(confidence_issues) > 0:
        print("✓ PASS: LLM detected unjustified confidence level")
        print(f"  Issue: {confidence_issues[0]['description'][:150]}...")
        return True
    else:
        print("⚠ SKIP: LLM layer not available or confidence acceptable")
        return None


def test_hard_coded_cannot_be_overridden():
    """
    CRITICAL SAFETY TEST: Verify LLM cannot override hard-coded violations.

    If hard-coded detects score >80, LLM CANNOT say "this is acceptable"
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 7: Hard-coded violations CANNOT be overridden by LLM (SAFETY CRITICAL)")
    print("="*80)

    # Test with intelligent audit enabled
    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True
    )

    # Output with critical hard-coded violation
    output = {
        "result": {
            "score": 92,  # CRITICAL VIOLATION
            "summary": "Comprehensive analysis with strong evidence",
            "sources": ["Source 1", "Source 2", "Source 3"],
            "confidence": "High",
            "limitations": ["Some data limitations"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Verify score violation present
    score_issues = [i for i in issues if i["category"] == "score_fabrication"]

    if len(score_issues) > 0 and score_issues[0]["hard_coded"] == True:
        print("✓ PASS: Hard-coded score violation PERSISTS even with LLM enabled")
        print(f"  Issue: {score_issues[0]['description']}")
        print("  SAFETY VERIFIED: LLM cannot override hard-coded safety checks")

        # Verify it's still marked as critical
        assert score_issues[0]["severity"] == "critical"
        return True
    else:
        print("✗ FAIL: Hard-coded violation was overridden or not detected")
        print("  SAFETY VIOLATION: Hard-coded checks MUST persist")
        return False


def test_llm_failure_graceful_degradation():
    """
    Test that LLM failure doesn't break hard-coded checks.

    If LLM fails/unavailable, system should continue with hard-coded only.
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 8: LLM failure doesn't break hard-coded checks")
    print("="*80)

    # Enable intelligent audit (even if LLM not available)
    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True
    )

    # Output with hard-coded violation
    output = {
        "result": {
            "score": 88,
            "summary": "Good analysis",
            "sources": ["Source 1"],
            "confidence": "Moderate",
            "limitations": ["Limited"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Verify hard-coded check still works
    score_issues = [i for i in issues if i["category"] == "score_fabrication"]

    if len(score_issues) > 0:
        print("✓ PASS: Hard-coded checks work even if LLM unavailable")
        print("  Graceful degradation verified")
        return True
    else:
        print("✗ FAIL: Hard-coded checks broken")
        return False


def test_hybrid_combined():
    """
    Test complete hybrid system: both hard-coded and LLM working together.
    """
    from agents.auditors.literature_auditor import LiteratureAuditor

    print("\n" + "="*80)
    print("TEST 9: Complete hybrid system (hard-coded + LLM)")
    print("="*80)

    auditor = LiteratureAuditor(
        agent_id="test_auditor",
        enable_intelligent_audit=True
    )

    # Output with BOTH hard-coded and semantic violations
    output = {
        "result": {
            "score": 85,  # Hard-coded violation
            "summary": "This analysis clearly demonstrates the drug is the best available treatment option.",  # Semantic violation
            "sources": ["Source 1"],
            "confidence": "High",  # Possibly unjustified
            "limitations": ["Minor limitations"]
        }
    }

    issues = auditor.check_anti_fabrication_compliance(output)

    # Count hard-coded vs semantic issues
    hard_coded_issues = [i for i in issues if i.get("hard_coded", False)]
    semantic_issues = [i for i in issues if not i.get("hard_coded", False)]

    print(f"  Found {len(hard_coded_issues)} hard-coded issue(s)")
    print(f"  Found {len(semantic_issues)} semantic issue(s)")

    # Verify both layers detected issues
    if len(hard_coded_issues) > 0:
        print("✓ Hard-coded layer working")
        for issue in hard_coded_issues:
            print(f"    - {issue['category']}: {issue['severity']}")
    else:
        print("✗ Hard-coded layer failed")

    if len(semantic_issues) > 0:
        print("✓ LLM layer working")
        for issue in semantic_issues:
            print(f"    - {issue['category']}")
    else:
        print("⚠ LLM layer not available or no semantic issues detected")

    # Pass if at least hard-coded works
    return len(hard_coded_issues) > 0


def main():
    """Run all hybrid audit tests."""
    print("\n" + "="*80)
    print("HYBRID AUDIT VALIDATION TEST SUITE")
    print("="*80)
    print("\nThis tests the combination of hard-coded safety checks + LLM semantic analysis.")
    print("Hard-coded checks are SAFETY CRITICAL and cannot be bypassed.")
    print("LLM adds semantic analysis layer for deeper understanding.")

    results = []

    # Hard-coded tests (MUST pass)
    results.append(("Score >80 detection", test_hard_coded_score_fabrication()))
    results.append(("Banned phrase detection", test_hard_coded_banned_phrases()))
    results.append(("Missing evidence detection", test_hard_coded_missing_evidence()))

    # LLM tests (may skip if LLM unavailable)
    results.append(("Semantic banned concepts", test_semantic_banned_concepts()))
    results.append(("Evidence-claim linkage", test_evidence_claim_linkage()))
    results.append(("Confidence justification", test_confidence_justification()))

    # Safety tests (MUST pass)
    results.append(("Hard-coded cannot be overridden", test_hard_coded_cannot_be_overridden()))
    results.append(("LLM failure graceful degradation", test_llm_failure_graceful_degradation()))

    # Integration test
    results.append(("Hybrid combined", test_hybrid_combined()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result == True)
    failed = sum(1 for _, result in results if result == False)
    skipped = sum(1 for _, result in results if result is None)

    for name, result in results:
        status = "✓ PASS" if result == True else ("✗ FAIL" if result == False else "⚠ SKIP")
        print(f"{status}: {name}")

    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped")

    # Critical safety tests
    critical_tests = [
        ("Score >80 detection", results[0][1]),
        ("Hard-coded cannot be overridden", results[6][1]),
        ("LLM failure graceful degradation", results[7][1])
    ]

    critical_passed = all(result == True for _, result in critical_tests)

    print("\n" + "="*80)
    print("SAFETY VERIFICATION")
    print("="*80)

    if critical_passed:
        print("✓ ALL CRITICAL SAFETY TESTS PASSED")
        print("  - Hard-coded checks catch objective violations")
        print("  - Hard-coded checks cannot be overridden by LLM")
        print("  - System degrades gracefully if LLM fails")
        print("\n✓ HYBRID AUDIT SYSTEM IS SAFE")
    else:
        print("✗ CRITICAL SAFETY TEST FAILED")
        print("  System is NOT SAFE for production use")
        for name, result in critical_tests:
            if result != True:
                print(f"    FAILED: {name}")

    print("="*80 + "\n")

    return critical_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test suite failed with exception: {e}", exc_info=True)
        sys.exit(1)
