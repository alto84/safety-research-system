#!/usr/bin/env python3
"""
Comprehensive tests for evidence level classification.

Tests cover:
- Each evidence level (I, II-1, II-2, II-3, III)
- Keyword matching
- Edge cases (unknown study types, empty inputs)
- Field priority (study_type vs title vs abstract)
- Case insensitivity
- Helper functions
"""

import sys
import os

# Add parent directory to path to import classify module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import unittest
from classify import (
    classify_evidence_level,
    get_level_description,
    classify_with_details,
    normalize_text
)


class TestNormalizeText(unittest.TestCase):
    """Tests for text normalization utility."""

    def test_normalize_basic(self):
        """Test basic text normalization."""
        self.assertEqual(normalize_text("Hello World"), "hello world")

    def test_normalize_extra_whitespace(self):
        """Test normalization removes extra whitespace."""
        self.assertEqual(normalize_text("Hello  \n  World"), "hello world")

    def test_normalize_empty_string(self):
        """Test normalization handles empty strings."""
        self.assertEqual(normalize_text(""), "")

    def test_normalize_none(self):
        """Test normalization handles None input."""
        self.assertEqual(normalize_text(None), "")


class TestEvidenceLevelI(unittest.TestCase):
    """Tests for Level I classification (Systematic reviews and meta-analyses)."""

    def test_systematic_review_in_study_type(self):
        """Test classification of systematic review by study_type."""
        source = {"study_type": "systematic review"}
        self.assertEqual(classify_evidence_level(source), "I")

    def test_meta_analysis_in_title(self):
        """Test classification of meta-analysis by title."""
        source = {"title": "A meta-analysis of AI safety interventions"}
        self.assertEqual(classify_evidence_level(source), "I")

    def test_cochrane_review(self):
        """Test classification of Cochrane review."""
        source = {"study_type": "Cochrane review"}
        self.assertEqual(classify_evidence_level(source), "I")

    def test_systematic_review_case_insensitive(self):
        """Test that classification is case-insensitive."""
        source = {"study_type": "SYSTEMATIC REVIEW"}
        self.assertEqual(classify_evidence_level(source), "I")


class TestEvidenceLevelII1(unittest.TestCase):
    """Tests for Level II-1 classification (RCTs)."""

    def test_rct_full_name(self):
        """Test classification of RCT by full name."""
        source = {"study_type": "randomized controlled trial"}
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_rct_abbreviation(self):
        """Test classification of RCT by abbreviation."""
        source = {"title": "An RCT of treatment effectiveness"}
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_randomised_british_spelling(self):
        """Test classification with British spelling."""
        source = {"study_type": "randomised controlled trial"}
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_double_blind_indicator(self):
        """Test classification by double-blind indicator."""
        source = {"abstract": "This double-blind placebo-controlled study..."}
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_randomized_in_study_design(self):
        """Test classification by randomized in study_design."""
        source = {"study_design": "randomized"}
        self.assertEqual(classify_evidence_level(source), "II-1")


class TestEvidenceLevelII2(unittest.TestCase):
    """Tests for Level II-2 classification (Cohort studies)."""

    def test_cohort_study(self):
        """Test classification of cohort study."""
        source = {"study_type": "cohort study"}
        self.assertEqual(classify_evidence_level(source), "II-2")

    def test_prospective_study(self):
        """Test classification of prospective study."""
        source = {"study_design": "prospective"}
        self.assertEqual(classify_evidence_level(source), "II-2")

    def test_longitudinal_study(self):
        """Test classification of longitudinal study."""
        source = {"title": "A longitudinal analysis of outcomes"}
        self.assertEqual(classify_evidence_level(source), "II-2")


class TestEvidenceLevelII3(unittest.TestCase):
    """Tests for Level II-3 classification (Case-control studies)."""

    def test_case_control_hyphenated(self):
        """Test classification of case-control study (hyphenated)."""
        source = {"study_type": "case-control study"}
        self.assertEqual(classify_evidence_level(source), "II-3")

    def test_case_control_no_hyphen(self):
        """Test classification of case-control study (no hyphen)."""
        source = {"study_type": "case control study"}
        self.assertEqual(classify_evidence_level(source), "II-3")


class TestEvidenceLevelIII(unittest.TestCase):
    """Tests for Level III classification (Descriptive studies)."""

    def test_case_series(self):
        """Test classification of case series."""
        source = {"study_type": "case series"}
        self.assertEqual(classify_evidence_level(source), "III")

    def test_case_report(self):
        """Test classification of case report."""
        source = {"study_type": "case report"}
        self.assertEqual(classify_evidence_level(source), "III")

    def test_expert_opinion(self):
        """Test classification of expert opinion."""
        source = {"study_type": "expert opinion"}
        self.assertEqual(classify_evidence_level(source), "III")

    def test_unknown_study_type(self):
        """Test that unknown study types default to Level III."""
        source = {"study_type": "unknown study type"}
        self.assertEqual(classify_evidence_level(source), "III")

    def test_empty_source(self):
        """Test that empty source defaults to Level III."""
        source = {}
        self.assertEqual(classify_evidence_level(source), "III")

    def test_narrative_review(self):
        """Test classification of narrative review."""
        source = {"study_type": "narrative review"}
        self.assertEqual(classify_evidence_level(source), "III")


class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions."""

    def test_get_level_description_level_i(self):
        """Test getting description for Level I."""
        desc = get_level_description("I")
        self.assertEqual(desc["name"], "Systematic reviews and meta-analyses")
        self.assertIn("systematic", desc["description"].lower())

    def test_get_level_description_level_ii1(self):
        """Test getting description for Level II-1."""
        desc = get_level_description("II-1")
        self.assertEqual(desc["name"], "Individual RCTs")
        self.assertIn("rct", desc["description"].lower())

    def test_get_level_description_unknown(self):
        """Test getting description for unknown level."""
        desc = get_level_description("INVALID")
        self.assertEqual(desc["name"], "Unknown")

    def test_classify_with_details(self):
        """Test classify_with_details returns complete information."""
        source = {"study_type": "systematic review"}
        result = classify_with_details(source)

        self.assertEqual(result["level"], "I")
        self.assertEqual(result["name"], "Systematic reviews and meta-analyses")
        self.assertIn("description", result)
        self.assertEqual(result["source_info"], source)


class TestFieldPriority(unittest.TestCase):
    """Tests for field priority and comprehensive matching."""

    def test_title_overrides_empty_study_type(self):
        """Test that title is checked when study_type is empty."""
        source = {
            "study_type": "",
            "title": "A systematic review of interventions"
        }
        self.assertEqual(classify_evidence_level(source), "I")

    def test_abstract_matching(self):
        """Test that abstract is checked for keywords."""
        source = {
            "abstract": "This randomized controlled trial examined..."
        }
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_multiple_fields_combined(self):
        """Test that all fields are combined for matching."""
        source = {
            "study_type": "observational",
            "study_design": "cohort",
            "title": "Long-term outcomes"
        }
        # Should match "cohort" from study_design
        self.assertEqual(classify_evidence_level(source), "II-2")


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions."""

    def test_conflicting_keywords(self):
        """Test priority when multiple keywords present (higher level wins)."""
        # If both "systematic review" and "rct" are present,
        # systematic review (Level I) should win
        source = {
            "title": "A systematic review of RCTs"
        }
        self.assertEqual(classify_evidence_level(source), "I")

    def test_partial_keyword_match(self):
        """Test that partial keyword matches work correctly."""
        # "randomized" alone should trigger II-1
        source = {"study_design": "randomized"}
        self.assertEqual(classify_evidence_level(source), "II-1")

    def test_whitespace_in_keywords(self):
        """Test that extra whitespace doesn't prevent matching."""
        source = {"study_type": "case   control   study"}
        self.assertEqual(classify_evidence_level(source), "II-3")

    def test_all_fields_none(self):
        """Test handling when all optional fields are None."""
        source = {
            "study_type": None,
            "study_design": None,
            "title": None,
            "abstract": None
        }
        self.assertEqual(classify_evidence_level(source), "III")


class TestDeterminism(unittest.TestCase):
    """Tests to ensure classification is deterministic."""

    def test_repeated_classification_consistent(self):
        """Test that repeated classification gives same result."""
        source = {"study_type": "cohort study"}
        results = [classify_evidence_level(source) for _ in range(10)]
        self.assertEqual(len(set(results)), 1)  # All results should be the same
        self.assertEqual(results[0], "II-2")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
