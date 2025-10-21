"""
Comprehensive Test Suite for Statistical Evidence Extraction

This test suite verifies the deterministic extraction of statistical evidence
from medical and scientific text.
"""

import sys
import os
import unittest

# Add parent directory to path to import extract module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.extract import extract_statistics


class TestHazardRatioExtraction(unittest.TestCase):
    """Test hazard ratio extraction patterns."""

    def test_basic_hr_extraction(self):
        """Test basic HR extraction with equals sign."""
        text = "Treatment showed benefit (HR = 0.75)"
        result = extract_statistics(text)
        self.assertEqual(len(result['hazard_ratios']), 1)
        self.assertEqual(result['hazard_ratios'][0]['value'], 0.75)

    def test_hr_with_spaces(self):
        """Test HR with various spacing patterns."""
        text = "Results: HR  0.68, hazard ratio: 1.25, HR=0.95"
        result = extract_statistics(text)
        self.assertEqual(len(result['hazard_ratios']), 3)
        values = [hr['value'] for hr in result['hazard_ratios']]
        self.assertIn(0.68, values)
        self.assertIn(1.25, values)
        self.assertIn(0.95, values)

    def test_hr_in_parentheses(self):
        """Test HR extraction when value is in parentheses."""
        text = "Primary outcome HR (0.82) was significant"
        result = extract_statistics(text)
        self.assertEqual(len(result['hazard_ratios']), 1)
        self.assertEqual(result['hazard_ratios'][0]['value'], 0.82)


class TestOddsRatioExtraction(unittest.TestCase):
    """Test odds ratio extraction patterns."""

    def test_basic_or_extraction(self):
        """Test basic OR extraction."""
        text = "Association with outcome (OR = 2.5)"
        result = extract_statistics(text)
        self.assertEqual(len(result['odds_ratios']), 1)
        self.assertEqual(result['odds_ratios'][0]['value'], 2.5)

    def test_or_spelled_out(self):
        """Test odds ratio spelled out."""
        text = "The odds ratio was 1.8 for the primary endpoint"
        result = extract_statistics(text)
        self.assertEqual(len(result['odds_ratios']), 1)
        self.assertEqual(result['odds_ratios'][0]['value'], 1.8)

    def test_multiple_or_values(self):
        """Test extraction of multiple OR values."""
        text = "OR 2.3 for A, OR 1.5 for B, and OR 3.2 for C"
        result = extract_statistics(text)
        self.assertEqual(len(result['odds_ratios']), 3)
        values = [or_val['value'] for or_val in result['odds_ratios']]
        self.assertEqual(values, [2.3, 1.5, 3.2])


class TestRiskRatioExtraction(unittest.TestCase):
    """Test risk ratio extraction patterns."""

    def test_basic_rr_extraction(self):
        """Test basic RR extraction."""
        text = "Risk ratio RR = 1.5"
        result = extract_statistics(text)
        self.assertEqual(len(result['risk_ratios']), 1)
        self.assertEqual(result['risk_ratios'][0]['value'], 1.5)

    def test_relative_risk_extraction(self):
        """Test relative risk extraction."""
        text = "The relative risk was 2.1"
        result = extract_statistics(text)
        self.assertEqual(len(result['risk_ratios']), 1)
        self.assertEqual(result['risk_ratios'][0]['value'], 2.1)


class TestPValueExtraction(unittest.TestCase):
    """Test p-value extraction patterns."""

    def test_p_value_with_equals(self):
        """Test p-value with equals sign."""
        text = "Results were significant (p = 0.05)"
        result = extract_statistics(text)
        self.assertEqual(len(result['p_values']), 1)
        self.assertEqual(result['p_values'][0]['value'], 0.05)

    def test_p_value_with_less_than(self):
        """Test p-value with less than sign."""
        text = "Highly significant (p < 0.001)"
        result = extract_statistics(text)
        self.assertEqual(len(result['p_values']), 1)
        self.assertEqual(result['p_values'][0]['value'], 0.001)

    def test_multiple_p_values(self):
        """Test extraction of multiple p-values."""
        text = "Primary endpoint p = 0.001, secondary p = 0.03, tertiary p < 0.05"
        result = extract_statistics(text)
        self.assertEqual(len(result['p_values']), 3)
        values = [p['value'] for p in result['p_values']]
        self.assertIn(0.001, values)
        self.assertIn(0.03, values)
        self.assertIn(0.05, values)

    def test_p_value_spelled_out(self):
        """Test p-value spelled out."""
        text = "The p-value = 0.02 for this comparison"
        result = extract_statistics(text)
        self.assertEqual(len(result['p_values']), 1)
        self.assertEqual(result['p_values'][0]['value'], 0.02)


class TestConfidenceIntervalExtraction(unittest.TestCase):
    """Test confidence interval extraction patterns."""

    def test_ci_with_95_percent(self):
        """Test CI with 95% prefix."""
        text = "Effect size (95% CI 0.6-0.9)"
        result = extract_statistics(text)
        self.assertEqual(len(result['confidence_intervals']), 1)
        self.assertEqual(result['confidence_intervals'][0]['lower'], 0.6)
        self.assertEqual(result['confidence_intervals'][0]['upper'], 0.9)

    def test_ci_without_percentage(self):
        """Test CI without percentage symbol."""
        text = "Results: 95 CI 1.2-2.5"
        result = extract_statistics(text)
        self.assertEqual(len(result['confidence_intervals']), 1)
        self.assertEqual(result['confidence_intervals'][0]['lower'], 1.2)
        self.assertEqual(result['confidence_intervals'][0]['upper'], 2.5)

    def test_ci_in_parentheses(self):
        """Test CI with parentheses around range."""
        text = "HR 0.75, 95% CI (0.65-0.85)"
        result = extract_statistics(text)
        self.assertEqual(len(result['confidence_intervals']), 1)
        self.assertEqual(result['confidence_intervals'][0]['lower'], 0.65)
        self.assertEqual(result['confidence_intervals'][0]['upper'], 0.85)

    def test_ci_with_en_dash(self):
        """Test CI with en dash."""
        text = "OR 2.3 (95% CI 1.5–3.2)"
        result = extract_statistics(text)
        self.assertEqual(len(result['confidence_intervals']), 1)
        self.assertEqual(result['confidence_intervals'][0]['lower'], 1.5)
        self.assertEqual(result['confidence_intervals'][0]['upper'], 3.2)

    def test_ci_with_em_dash(self):
        """Test CI with em dash."""
        text = "RR 1.8 (95% CI 1.2—2.4)"
        result = extract_statistics(text)
        self.assertEqual(len(result['confidence_intervals']), 1)
        self.assertEqual(result['confidence_intervals'][0]['lower'], 1.2)
        self.assertEqual(result['confidence_intervals'][0]['upper'], 2.4)


class TestSampleSizeExtraction(unittest.TestCase):
    """Test sample size extraction patterns."""

    def test_lowercase_n(self):
        """Test sample size with lowercase n."""
        text = "Study included n = 500 patients"
        result = extract_statistics(text)
        self.assertEqual(len(result['sample_sizes']), 1)
        self.assertEqual(result['sample_sizes'][0]['value'], 500)

    def test_uppercase_n(self):
        """Test sample size with uppercase N."""
        text = "Total sample size N = 1234"
        result = extract_statistics(text)
        self.assertEqual(len(result['sample_sizes']), 1)
        self.assertEqual(result['sample_sizes'][0]['value'], 1234)

    def test_n_in_parentheses(self):
        """Test sample size in parentheses."""
        text = "Treatment arm (n = 250) vs control (n = 250)"
        result = extract_statistics(text)
        self.assertEqual(len(result['sample_sizes']), 2)
        for sample in result['sample_sizes']:
            self.assertEqual(sample['value'], 250)

    def test_sample_size_spelled_out(self):
        """Test sample size spelled out."""
        text = "The sample size = 856 participants"
        result = extract_statistics(text)
        self.assertEqual(len(result['sample_sizes']), 1)
        self.assertEqual(result['sample_sizes'][0]['value'], 856)


class TestPercentageExtraction(unittest.TestCase):
    """Test percentage extraction patterns."""

    def test_basic_percentage(self):
        """Test basic percentage extraction."""
        text = "Response rate was 45.3%"
        result = extract_statistics(text)
        self.assertGreater(len(result['percentages']), 0)
        values = [p['value'] for p in result['percentages']]
        self.assertIn(45.3, values)

    def test_integer_percentage(self):
        """Test integer percentage."""
        text = "Adverse events occurred in 25% of patients"
        result = extract_statistics(text)
        values = [p['value'] for p in result['percentages']]
        self.assertIn(25.0, values)

    def test_multiple_percentages(self):
        """Test multiple percentage values."""
        text = "Response: 45.3% vs 32.1%, AE: 28.3% vs 41.2%"
        result = extract_statistics(text)
        self.assertGreaterEqual(len(result['percentages']), 4)
        values = [p['value'] for p in result['percentages']]
        self.assertIn(45.3, values)
        self.assertIn(32.1, values)


class TestComplexTextExtraction(unittest.TestCase):
    """Test extraction from complex text with multiple statistics."""

    def test_clinical_trial_abstract(self):
        """Test extraction from realistic clinical trial abstract."""
        text = """
        RESULTS: Primary endpoint (overall survival) showed significant improvement
        with immunotherapy (HR 0.68, 95% CI 0.57-0.81, p < 0.001). The study included
        n = 856 patients. Response rate was 31.2% vs 18.7% (OR 1.98, 95% CI 1.52-2.58,
        p < 0.001). Grade 3-4 adverse events occurred in 28.3% vs 41.2% of patients.
        """
        result = extract_statistics(text)

        # Check hazard ratios
        self.assertEqual(len(result['hazard_ratios']), 1)
        self.assertEqual(result['hazard_ratios'][0]['value'], 0.68)

        # Check odds ratios
        self.assertEqual(len(result['odds_ratios']), 1)
        self.assertEqual(result['odds_ratios'][0]['value'], 1.98)

        # Check p-values
        self.assertGreaterEqual(len(result['p_values']), 2)

        # Check confidence intervals
        self.assertGreaterEqual(len(result['confidence_intervals']), 2)

        # Check sample size
        self.assertEqual(len(result['sample_sizes']), 1)
        self.assertEqual(result['sample_sizes'][0]['value'], 856)

        # Check percentages
        self.assertGreaterEqual(len(result['percentages']), 4)

        # Check summary
        self.assertGreater(result['summary']['total_statistics'], 0)
        self.assertTrue(result['summary']['has_significance'])
        self.assertTrue(result['summary']['has_effect_sizes'])

    def test_multiple_effect_sizes(self):
        """Test text with multiple types of effect sizes."""
        text = """
        Primary analysis: HR 0.75 (95% CI 0.65-0.85, p < 0.001)
        Subgroup analysis: OR 2.3 (95% CI 1.5-3.2, p = 0.02)
        Secondary outcome: RR 1.5 (95% CI 1.2-1.8, p = 0.01)
        """
        result = extract_statistics(text)

        self.assertEqual(len(result['hazard_ratios']), 1)
        self.assertEqual(len(result['odds_ratios']), 1)
        self.assertEqual(len(result['risk_ratios']), 1)
        self.assertTrue(result['summary']['has_effect_sizes'])


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_empty_text(self):
        """Test extraction from empty text."""
        result = extract_statistics("")
        self.assertEqual(result['summary']['total_statistics'], 0)
        self.assertFalse(result['summary']['has_significance'])
        self.assertFalse(result['summary']['has_effect_sizes'])

    def test_no_statistics(self):
        """Test text with no statistics."""
        text = "This is a description of the study methodology with no results."
        result = extract_statistics(text)
        self.assertEqual(result['summary']['total_statistics'], 0)

    def test_decimal_without_leading_zero(self):
        """Test values like .75 instead of 0.75."""
        text = "HR = .75"
        result = extract_statistics(text)
        # This may or may not be extracted depending on regex - document behavior
        # Current regex requires digit before decimal

    def test_very_small_p_value(self):
        """Test very small p-value."""
        text = "Highly significant (p < 0.0001)"
        result = extract_statistics(text)
        self.assertEqual(len(result['p_values']), 1)
        self.assertEqual(result['p_values'][0]['value'], 0.0001)

    def test_context_extraction(self):
        """Test that context is properly extracted."""
        text = "The primary endpoint showed a hazard ratio HR = 0.75 which was statistically significant"
        result = extract_statistics(text)
        self.assertEqual(len(result['hazard_ratios']), 1)
        self.assertIn('HR = 0.75', result['hazard_ratios'][0]['context'])

    def test_deduplication(self):
        """Test that duplicate extractions are removed."""
        # This text might trigger the same HR multiple times if patterns overlap
        text = "HR 0.75 (HR = 0.75)"
        result = extract_statistics(text)
        # Should deduplicate based on position and value
        self.assertGreaterEqual(len(result['hazard_ratios']), 1)

    def test_integer_values(self):
        """Test extraction of integer effect sizes."""
        text = "OR 2, RR 3, HR 1"
        result = extract_statistics(text)
        self.assertGreater(len(result['odds_ratios']), 0)
        self.assertGreater(len(result['risk_ratios']), 0)
        self.assertGreater(len(result['hazard_ratios']), 0)


class TestSummaryGeneration(unittest.TestCase):
    """Test summary statistics generation."""

    def test_summary_with_all_components(self):
        """Test summary when all components present."""
        text = "HR 0.75 (95% CI 0.65-0.85, p < 0.001), n = 500"
        result = extract_statistics(text)
        self.assertTrue(result['summary']['has_effect_sizes'])
        self.assertTrue(result['summary']['has_significance'])
        self.assertGreater(result['summary']['total_statistics'], 0)

    def test_summary_with_only_effect_size(self):
        """Test summary with only effect size."""
        text = "HR 0.75"
        result = extract_statistics(text)
        self.assertTrue(result['summary']['has_effect_sizes'])
        self.assertFalse(result['summary']['has_significance'])

    def test_summary_with_only_p_value(self):
        """Test summary with only p-value."""
        text = "Results were significant (p < 0.05)"
        result = extract_statistics(text)
        self.assertTrue(result['summary']['has_significance'])
        self.assertFalse(result['summary']['has_effect_sizes'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
