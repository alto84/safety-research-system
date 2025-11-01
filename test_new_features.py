"""Comprehensive tests for new features."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import unittest
from datetime import datetime

# New agents
from agents.workers.risk_modeler import RiskModelerAgent
from agents.workers.mechanistic_agent import MechanisticAgent
from agents.auditors.risk_modeling_auditor import RiskModelingAuditor
from agents.auditors.mechanistic_auditor import MechanisticAuditor

# Analytics
from analytics.advanced_analytics import (
    ConfidenceCalibrator,
    AuditMetricsDashboard,
    TrendAnalyzer,
    ComparativeAnalyzer
)

# Domains
from domains.domain_config import (
    DomainRegistry,
    get_domain_template,
    SafetyDomain
)

# Caching & Performance
from core.caching_performance import (
    MemoryCache,
    ResultCache,
    PerformanceMonitor,
    memoize,
    monitor_performance
)

# Human Review
from core.human_review import (
    ReviewWorkflow,
    ReviewItem,
    ReviewDecision,
    FeedbackCollector
)


class TestRiskModelerAgent(unittest.TestCase):
    """Test Risk Modeling Agent."""

    def test_risk_modeling_agent_initialization(self):
        """Test agent initialization."""
        agent = RiskModelerAgent(agent_id="test_risk_01")
        self.assertEqual(agent.agent_id, "test_risk_01")
        self.assertEqual(agent.version, "1.0.0")

    def test_risk_calculations(self):
        """Test risk calculations."""
        agent = RiskModelerAgent()

        input_data = {
            "query": "What is the ILD risk with Drug X?",
            "context": {"drug_name": "Drug X", "adverse_event": "ILD"},
            "risk_data": {
                "events": 15,
                "total_population": 100,
                "person_years": 150.0,
            },
        }

        result = agent.execute(input_data)

        self.assertIn("risk_estimates", result)
        self.assertIn("confidence_intervals", result)
        self.assertIn("bayesian_estimates", result)

        # Check absolute risk
        risk_estimates = result["risk_estimates"]
        self.assertIn("absolute_risk", risk_estimates)
        self.assertEqual(risk_estimates["absolute_risk"]["value"], 0.15)

    def test_confidence_intervals(self):
        """Test confidence interval calculation."""
        agent = RiskModelerAgent()

        input_data = {
            "query": "Risk assessment",
            "context": {},
            "risk_data": {
                "events": 20,
                "total_population": 200,
            },
        }

        result = agent.execute(input_data)

        ci = result["confidence_intervals"]
        self.assertIn("lower_bound", ci)
        self.assertIn("upper_bound", ci)
        self.assertGreaterEqual(ci["upper_bound"], ci["lower_bound"])


class TestMechanisticAgent(unittest.TestCase):
    """Test Mechanistic Inference Agent."""

    def test_mechanistic_agent_initialization(self):
        """Test agent initialization."""
        agent = MechanisticAgent(agent_id="test_mech_01")
        self.assertEqual(agent.agent_id, "test_mech_01")
        self.assertIsNotNone(agent.pathway_database)

    def test_pathway_identification(self):
        """Test pathway identification."""
        agent = MechanisticAgent()

        input_data = {
            "query": "What is the mechanism of ILD with HER2-targeting ADCs?",
            "context": {
                "drug_name": "Trastuzumab deruxtecan",
                "adverse_event": "ILD",
            },
            "mechanism_data": {
                "target": "HER2",
                "mechanism_of_action": "HER2 inhibition",
            },
        }

        result = agent.execute(input_data)

        self.assertIn("pathways", result)
        self.assertIn("biological_plausibility", result)
        self.assertIn("causality_assessment", result)

        # Should identify HER2 pathways
        pathways = result["pathways"]
        self.assertGreater(len(pathways), 0)


class TestRiskModelingAuditor(unittest.TestCase):
    """Test Risk Modeling Auditor."""

    def test_auditor_initialization(self):
        """Test auditor initialization."""
        auditor = RiskModelingAuditor(agent_id="test_audit_01")
        self.assertEqual(auditor.agent_id, "test_audit_01")

    def test_valid_risk_output(self):
        """Test validation of valid risk modeling output."""
        auditor = RiskModelingAuditor()

        task_output = {
            "result": {
                "summary": "Risk assessment completed",
                "risk_estimates": {
                    "absolute_risk": {"value": 0.10, "percentage": 10.0}
                },
                "confidence_intervals": {
                    "point_estimate": 0.10,
                    "lower_bound": 0.05,
                    "upper_bound": 0.15,
                    "method": "Wilson score",
                },
                "key_findings": ["Risk: 10%"],
                "confidence": "Moderate",
                "limitations": ["Sample size limited", "Observational data"],
                "assumptions": ["Independence", "Constant risk", "MAR"],
                "methodology": "Risk modeling using Wilson score",
                "sensitivity_analysis": {"robustness": "Moderate"},
            }
        }

        result = auditor.validate({}, task_output)

        # Status can be "passed" or "partial" (partial means minor warnings, acceptable)
        self.assertIn(result["status"], ["passed", "partial"])
        self.assertGreater(len(result["passed_checks"]), 0)


class TestAnalytics(unittest.TestCase):
    """Test advanced analytics modules."""

    def test_confidence_calibrator(self):
        """Test confidence calibration."""
        calibrator = ConfidenceCalibrator()

        # Add some assessments
        calibrator.add_assessment("High", True, 0, 0, "literature_agent")
        calibrator.add_assessment("High", True, 0, 1, "literature_agent")
        calibrator.add_assessment("Moderate", True, 0, 0, "risk_agent")
        calibrator.add_assessment("Moderate", False, 2, 1, "risk_agent")

        analysis = calibrator.analyze_calibration()

        self.assertEqual(analysis["status"], "analyzed")
        self.assertIn("calibration_by_level", analysis)

    def test_audit_metrics_dashboard(self):
        """Test audit metrics dashboard."""
        dashboard = AuditMetricsDashboard()

        # Add audit results
        dashboard.add_audit_result(
            "literature_review",
            "passed",
            [],
            ["completeness", "quality"],
            [],
            duration=2.5
        )

        dashboard.add_audit_result(
            "risk_modeling",
            "failed",
            [{"severity": "critical", "category": "missing_ci"}],
            ["completeness"],
            ["confidence_intervals"],
            duration=3.0
        )

        data = dashboard.generate_dashboard_data()

        self.assertEqual(data["status"], "generated")
        self.assertEqual(data["overall_metrics"]["total_audits"], 2)
        self.assertEqual(data["overall_metrics"]["passed_audits"], 1)

    def test_trend_analyzer(self):
        """Test trend analysis."""
        analyzer = TrendAnalyzer()

        # Add assessments over time
        base_date = datetime(2025, 1, 1)
        analyzer.add_assessment(
            "drug_x_ild",
            base_date,
            risk_estimate=0.10,
            confidence_level="Moderate"
        )

        analyzer.add_assessment(
            "drug_x_ild",
            datetime(2025, 2, 1),
            risk_estimate=0.12,
            confidence_level="Moderate"
        )

        analyzer.add_assessment(
            "drug_x_ild",
            datetime(2025, 3, 1),
            risk_estimate=0.14,
            confidence_level="High"
        )

        trends = analyzer.analyze_trends("drug_x_ild")

        self.assertEqual(trends["status"], "analyzed")
        self.assertIn("risk_trend", trends)

    def test_comparative_analyzer(self):
        """Test comparative analysis."""
        analyzer = ComparativeAnalyzer()

        # Add entity assessments
        analyzer.add_entity_assessment(
            "drug_a",
            "Drug A",
            risk_estimate=0.05,
            confidence_level="Moderate",
            audit_pass_rate=0.90
        )

        analyzer.add_entity_assessment(
            "drug_b",
            "Drug B",
            risk_estimate=0.15,
            confidence_level="Moderate",
            audit_pass_rate=0.85
        )

        comparison = analyzer.compare_entities()

        self.assertEqual(comparison["status"], "compared")
        self.assertEqual(comparison["entities_compared"], 2)
        self.assertIn("risk_ranking", comparison)


class TestDomainSystem(unittest.TestCase):
    """Test multi-domain configuration system."""

    def test_domain_registry(self):
        """Test domain registry."""
        registry = DomainRegistry()

        domains = registry.list_domains()

        self.assertIn("adc_ild", domains)
        self.assertIn("cardiovascular", domains)
        self.assertIn("hepatotoxicity", domains)

    def test_domain_template(self):
        """Test domain template."""
        template = get_domain_template("cardiovascular")

        self.assertIsNotNone(template)

        case = template.create_case_template(
            "Sunitinib",
            "cardiac dysfunction"
        )

        self.assertIn("title", case)
        self.assertIn("question", case)
        self.assertIn("context", case)
        self.assertEqual(case["context"]["domain"], "cardiovascular")

    def test_assessment_checklist(self):
        """Test assessment checklist generation."""
        template = get_domain_template("hepatotoxicity")

        checklist = template.generate_assessment_checklist()

        self.assertIsInstance(checklist, list)
        self.assertGreater(len(checklist), 0)


class TestCachingPerformance(unittest.TestCase):
    """Test caching and performance monitoring."""

    def test_memory_cache(self):
        """Test memory cache."""
        cache = MemoryCache(default_ttl=60)

        # Set and get
        cache.set("key1", {"data": "value1"})
        value = cache.get("key1")

        self.assertEqual(value["data"], "value1")

        # Test non-existent key
        self.assertIsNone(cache.get("nonexistent"))

    def test_result_cache(self):
        """Test result cache."""
        cache = ResultCache()

        # Cache a result
        cache.cache_result(
            {"result": "computed_value"},
            "expensive_operation",
            arg1="test"
        )

        # Retrieve cached result
        result = cache.get_cached_result("expensive_operation", arg1="test")

        self.assertIsNotNone(result)
        self.assertEqual(result["result"], "computed_value")

        # Test cache stats
        stats = cache.get_stats()
        self.assertEqual(stats["cache_hits"], 1)

    def test_memoization(self):
        """Test memoization decorator."""
        call_count = [0]

        @memoize(ttl=60)
        def expensive_func(x, y):
            call_count[0] += 1
            return x + y

        # First call
        result1 = expensive_func(5, 3)
        self.assertEqual(result1, 8)
        self.assertEqual(call_count[0], 1)

        # Second call (cached)
        result2 = expensive_func(5, 3)
        self.assertEqual(result2, 8)
        self.assertEqual(call_count[0], 1)  # Not called again

    def test_performance_monitor(self):
        """Test performance monitoring."""
        monitor = PerformanceMonitor()

        # Record operations
        monitor.record_operation("operation1", 1.5, success=True)
        monitor.record_operation("operation1", 2.0, success=True)
        monitor.record_operation("operation2", 0.5, success=False)

        # Get metrics
        metrics = monitor.get_metrics("operation1")

        self.assertEqual(metrics["count"], 2)
        self.assertEqual(metrics["error_count"], 0)
        self.assertAlmostEqual(metrics["avg_duration"], 1.75)

        # Generate report
        report = monitor.generate_report()

        self.assertIn("overall", report)
        self.assertEqual(report["overall"]["total_operations"], 3)


class TestHumanReview(unittest.TestCase):
    """Test human-in-the-loop review interface."""

    def test_review_workflow(self):
        """Test review workflow."""
        workflow = ReviewWorkflow("test_workflow", auto_approve_low_risk=True)

        # Add low-risk item (should auto-approve)
        low_risk_item = ReviewItem(
            "item_001",
            "task_result",
            {"summary": "Low risk finding"},
            "low",
            "Routine check"
        )

        workflow.add_item(low_risk_item)

        # Should be auto-approved
        self.assertEqual(len(workflow.pending_items), 0)
        self.assertEqual(len(workflow.completed_items), 1)

        # Add high-risk item
        high_risk_item = ReviewItem(
            "item_002",
            "task_result",
            {"summary": "High risk finding"},
            "high",
            "Risk >10%"
        )

        workflow.add_item(high_risk_item)

        # Should be pending
        self.assertEqual(len(workflow.pending_items), 1)

    def test_review_submission(self):
        """Test review submission."""
        workflow = ReviewWorkflow("test_workflow", auto_approve_low_risk=False)

        item = ReviewItem(
            "item_001",
            "task_result",
            {"summary": "Test"},
            "medium",
            "Test review"
        )

        workflow.add_item(item)

        # Submit review
        success = workflow.submit_review(
            "item_001",
            ReviewDecision.APPROVED,
            "test_reviewer",
            "Looks good"
        )

        self.assertTrue(success)
        self.assertEqual(len(workflow.pending_items), 0)
        self.assertEqual(len(workflow.completed_items), 1)

    def test_feedback_collector(self):
        """Test feedback collection."""
        collector = FeedbackCollector()

        # Collect feedback
        collector.collect_feedback(
            "item_001",
            "task_result",
            rating=4,
            feedback_text="Good quality",
            category="accuracy"
        )

        collector.collect_feedback(
            "item_002",
            "audit_result",
            rating=5,
            feedback_text="Excellent",
            category="completeness"
        )

        # Get summary
        summary = collector.get_feedback_summary()

        self.assertEqual(summary["total_feedback"], 2)
        self.assertEqual(summary["avg_rating"], 4.5)


def run_all_tests():
    """Run all tests."""
    print("="*80)
    print("RUNNING NEW FEATURES COMPREHENSIVE TEST SUITE")
    print("="*80)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRiskModelerAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestMechanisticAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskModelingAuditor))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalytics))
    suite.addTests(loader.loadTestsFromTestCase(TestDomainSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestCachingPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestHumanReview))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*80)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
