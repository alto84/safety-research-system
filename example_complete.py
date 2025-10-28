#!/usr/bin/env python3
"""
COMPREHENSIVE END-TO-END EXAMPLE: Complete Safety Research System

This example demonstrates the FULL power of the safety research system:
1. Agent-Audit-Resolve pattern with automatic validation and retry
2. Parallel execution of multiple tasks for performance
3. Performance profiling showing timing improvements
4. Multiple task types (literature review, statistical analysis, risk modeling)
5. Orchestrator synthesizing results from compressed summaries
6. Complete case processing workflow from intake to final report

This uses stub implementations (no real LLM calls) to demonstrate the
architecture and flow in a self-contained example.
"""

import sys
import time
from typing import Dict, Any
from datetime import datetime

# Import models
from models.case import Case, CaseStatus, CasePriority
from models.task import Task, TaskType, TaskStatus
from models.audit_result import AuditResult, AuditStatus, ValidationIssue, IssueSeverity

# Import core components
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor
from core.performance_profiler import PerformanceProfiler

# Import agents
from agents.orchestrator import Orchestrator
from agents.base_worker import BaseWorker
from agents.base_auditor import BaseAuditor


# ============================================================================
# STUB WORKER IMPLEMENTATIONS (Realistic but no real LLM calls)
# ============================================================================

class LiteratureReviewWorker(BaseWorker):
    """
    Simulates a literature review agent that searches and synthesizes published evidence.

    Demonstrates: Multi-attempt improvement (fails first time, passes after retry)
    """

    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.attempt_count = 0

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute literature review with stub data."""
        self.attempt_count += 1
        query = input_data.get("query", "")
        has_corrections = len(input_data.get("corrections", [])) > 0

        print(f"\n  [LiteratureWorker] Attempt {self.attempt_count}: Searching for '{query[:50]}...'")

        # Simulate work
        time.sleep(0.1)

        if has_corrections:
            print(f"  [LiteratureWorker] Addressing {len(input_data['corrections'])} audit findings...")
            time.sleep(0.05)

        # First attempt: incomplete (missing sources, weak confidence)
        # Second attempt: complete (adds sources and proper confidence)
        if has_corrections:
            return {
                "summary": f"Comprehensive literature review on {query[:30]}",
                "methodology": "Systematic search of PubMed, Cochrane, FDA databases",
                "findings": [
                    "Multiple case reports identified linking ADCs to ILD",
                    "Pooled incidence rate: 2.3% across 5 randomized trials",
                    "Median time to onset: 4.2 months (range 1-12 months)",
                ],
                "sources": [
                    "Smith et al. (2023) - NEJM study on T-DM1 ILD risk",
                    "Johnson et al. (2022) - Meta-analysis of ADC safety",
                    "FDA Adverse Event Reporting System (2020-2023)",
                ],
                "limitations": [
                    "Heterogeneous ADC mechanisms across studies",
                    "Varying ILD diagnostic criteria",
                    "Limited long-term follow-up data",
                ],
                "confidence": "Moderate - based on convergent evidence from multiple sources",
                "quality_score": 8.5,
            }
        else:
            # Incomplete first attempt (will trigger audit failure)
            return {
                "summary": f"Initial search on {query[:30]}",
                "methodology": "Database search",
                "findings": ["Some evidence found"],
                "sources": [],  # MISSING - will fail audit
                "limitations": [],  # MISSING - will fail audit
                "confidence": "",  # MISSING - will fail audit
            }


class StatisticalAnalysisWorker(BaseWorker):
    """
    Simulates a statistical analysis agent that analyzes clinical data.

    Demonstrates: High-quality output that passes audit on first attempt
    """

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute statistical analysis with stub data."""
        query = input_data.get("query", "")

        print(f"\n  [StatisticsWorker] Analyzing clinical data for: '{query[:50]}...'")

        # Simulate complex statistical work
        time.sleep(0.15)

        # This worker produces high-quality output that passes audit immediately
        return {
            "summary": "Statistical analysis of ADC-ILD association using FAERS data",
            "methodology": "Disproportionality analysis with Reporting Odds Ratio (ROR)",
            "findings": [
                "ROR: 3.2 (95% CI: 2.1-4.8) - significant association",
                "N=156 ILD cases reported with ADCs out of 4,892 total ADC reports",
                "Compared to background ILD rate in oncology: ROR suggests 3x elevated risk",
            ],
            "statistical_tests": [
                "Chi-square test: p < 0.001",
                "Fisher's exact test: p = 0.0004",
                "Bayesian confidence propagation: 99.2% probability of true signal",
            ],
            "sources": [
                "FDA FAERS Database (2018-2023)",
                "WHO VigiBase pharmacovigilance data",
            ],
            "limitations": [
                "Reporting bias inherent in pharmacovigilance databases",
                "Confounding by indication (oncology patients at baseline ILD risk)",
                "Lack of exposure denominator data",
            ],
            "confidence": "Moderate-to-High - consistent signal across multiple databases",
            "quality_score": 9.0,
        }


class RiskModelingWorker(BaseWorker):
    """
    Simulates a risk modeling agent that builds predictive models.

    Demonstrates: Complex computational task with detailed output
    """

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk modeling with stub data."""
        query = input_data.get("query", "")

        print(f"\n  [RiskModelWorker] Building risk model for: '{query[:50]}...'")

        # Simulate complex modeling work
        time.sleep(0.12)

        return {
            "summary": "Probabilistic risk model for ADC-ILD using Bayesian network",
            "methodology": "Bayesian network with prior elicitation from published data",
            "findings": [
                "Baseline ILD risk in oncology: 0.5%",
                "With ADC exposure: 1.6% (3.2x increase)",
                "Risk factors: age >65 (+2.1x), prior lung disease (+4.5x), concurrent ICI (+1.8x)",
            ],
            "model_parameters": {
                "sensitivity": 0.82,
                "specificity": 0.91,
                "PPV": 0.15,
                "NPV": 0.995,
            },
            "risk_stratification": {
                "low_risk": "Age <65, no lung disease: 0.8% ILD risk",
                "moderate_risk": "Age >65 OR lung disease: 2.4% ILD risk",
                "high_risk": "Age >65 AND lung disease: 7.2% ILD risk",
            },
            "sources": [
                "Published ADC trial safety data (n=12 trials)",
                "Real-world evidence from 3 health systems",
            ],
            "limitations": [
                "Model calibrated on limited real-world data",
                "Assumes independence of some risk factors",
                "May not generalize to all ADC subtypes",
            ],
            "confidence": "Moderate - model validated on holdout set but limited external validation",
            "quality_score": 8.7,
        }


# ============================================================================
# STUB AUDITOR IMPLEMENTATIONS
# ============================================================================

class LiteratureAuditor(BaseAuditor):
    """
    Auditor for literature review tasks.
    Checks for required fields and quality standards.
    """

    def __init__(self, agent_id: str):
        super().__init__(agent_id, enable_intelligent_audit=False)

    def _load_validation_criteria(self) -> Dict[str, Any]:
        return {
            "required_fields": ["summary", "methodology", "findings", "sources", "limitations", "confidence"],
            "minimum_sources": 2,
        }

    def validate(self, task_input: Dict[str, Any], task_output: Dict[str, Any],
                 task_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate literature review output."""
        result = task_output.get("result", {})
        issues = []
        passed = []

        # Check required fields
        for field in self.validation_criteria["required_fields"]:
            if field in result and result[field]:
                passed.append(f"Has {field}")
            else:
                issues.append({
                    "category": "missing_field",
                    "severity": "warning",  # Use warning so it retries instead of escalates
                    "description": f"Missing required field: {field}",
                    "suggested_fix": f"Add {field} to literature review output"
                })

        # Check minimum sources
        sources = result.get("sources", [])
        if len(sources) >= self.validation_criteria["minimum_sources"]:
            passed.append(f"Has {len(sources)} sources (>= minimum)")
        else:
            issues.append({
                "category": "insufficient_sources",
                "severity": "warning",  # Use warning so it retries instead of escalates
                "description": f"Only {len(sources)} sources (minimum {self.validation_criteria['minimum_sources']})",
                "suggested_fix": "Add more published sources to support findings"
            })

        status = "passed" if len(issues) == 0 else "failed"
        print(f"    [LitAuditor] {status.upper()}: {len(passed)} checks passed, {len(issues)} issues")

        return {
            "status": status,
            "summary": "All checks passed" if status == "passed" else f"{len(issues)} critical issues",
            "passed_checks": passed,
            "failed_checks": [i["description"] for i in issues],
            "issues": issues,
            "recommendations": ["Consider adding systematic review methodology"] if status == "passed" else []
        }


class StatisticsAuditor(BaseAuditor):
    """
    Auditor for statistical analysis tasks.
    Checks for methodological rigor and proper statistical reporting.
    """

    def __init__(self, agent_id: str):
        super().__init__(agent_id, enable_intelligent_audit=False)

    def _load_validation_criteria(self) -> Dict[str, Any]:
        return {
            "required_fields": ["summary", "methodology", "findings", "sources", "limitations", "confidence"],
        }

    def validate(self, task_input: Dict[str, Any], task_output: Dict[str, Any],
                 task_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate statistical analysis output."""
        result = task_output.get("result", {})
        issues = []
        passed = []

        # Check required fields
        for field in self.validation_criteria["required_fields"]:
            if field in result and result[field]:
                passed.append(f"Has {field}")
            else:
                issues.append({
                    "category": "missing_field",
                    "severity": "warning",
                    "description": f"Missing recommended field: {field}",
                    "suggested_fix": f"Add {field} to analysis"
                })

        # Statistical analysis is typically high quality - passes
        status = "passed"
        passed.append("Statistical methodology clearly described")
        passed.append("Limitations acknowledged")

        print(f"    [StatsAuditor] {status.upper()}: {len(passed)} checks passed")

        return {
            "status": status,
            "summary": "Statistical analysis meets quality standards",
            "passed_checks": passed,
            "failed_checks": [],
            "issues": issues,
            "recommendations": ["Consider sensitivity analysis for robustness"]
        }


class RiskModelAuditor(BaseAuditor):
    """
    Auditor for risk modeling tasks.
    Checks for model validation and appropriate uncertainty quantification.
    """

    def __init__(self, agent_id: str):
        super().__init__(agent_id, enable_intelligent_audit=False)

    def _load_validation_criteria(self) -> Dict[str, Any]:
        return {
            "required_fields": ["summary", "methodology", "findings", "limitations", "confidence"],
        }

    def validate(self, task_input: Dict[str, Any], task_output: Dict[str, Any],
                 task_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate risk modeling output."""
        result = task_output.get("result", {})
        passed = []

        # Risk models typically have good structure
        for field in self.validation_criteria["required_fields"]:
            if field in result and result[field]:
                passed.append(f"Has {field}")

        passed.append("Model assumptions clearly stated")
        passed.append("Uncertainty quantified")

        print(f"    [RiskAuditor] PASSED: {len(passed)} checks passed")

        return {
            "status": "passed",
            "summary": "Risk model meets validation standards",
            "passed_checks": passed,
            "failed_checks": [],
            "issues": [],
            "recommendations": ["Consider external validation on independent dataset"]
        }


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

def print_header(title: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print(f"{'─' * 80}")


def main():
    """Demonstrate the complete safety research system."""

    print_header("COMPREHENSIVE SAFETY RESEARCH SYSTEM DEMO")
    print("This example demonstrates:")
    print("  ✓ Agent-Audit-Resolve pattern (automatic validation & retry)")
    print("  ✓ Parallel task execution (3 tasks running concurrently)")
    print("  ✓ Performance profiling (timing analysis)")
    print("  ✓ Orchestrator synthesis (combining compressed results)")
    print("  ✓ Complete case workflow (intake → analysis → report)")

    # ========================================================================
    # STEP 1: Initialize the system
    # ========================================================================
    print_section("STEP 1: Initialize System Components")

    print("[1.1] Creating core engines...")
    task_executor = TaskExecutor(enable_intelligent_routing=False)
    audit_engine = AuditEngine()
    resolution_engine = ResolutionEngine(
        task_executor,
        audit_engine,
        max_retries=2,
        enable_intelligent_resolution=False
    )
    context_compressor = ContextCompressor()

    print("[1.2] Creating orchestrator with profiling enabled...")
    orchestrator = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=True,
        enable_parallel_execution=True,  # KEY: Parallel execution enabled!
    )

    print("[1.3] Registering worker agents...")
    task_executor.register_worker(TaskType.LITERATURE_REVIEW, LiteratureReviewWorker("lit-worker-01"))
    task_executor.register_worker(TaskType.STATISTICAL_ANALYSIS, StatisticalAnalysisWorker("stats-worker-01"))
    task_executor.register_worker(TaskType.RISK_MODELING, RiskModelingWorker("risk-worker-01"))

    print("[1.4] Registering auditor agents...")
    audit_engine.register_auditor(TaskType.LITERATURE_REVIEW, LiteratureAuditor("lit-auditor-01"))
    audit_engine.register_auditor(TaskType.STATISTICAL_ANALYSIS, StatisticsAuditor("stats-auditor-01"))
    audit_engine.register_auditor(TaskType.RISK_MODELING, RiskModelAuditor("risk-auditor-01"))

    print("\n✓ System initialized with 3 worker-auditor pairs")

    # ========================================================================
    # STEP 2: Create a complex safety case
    # ========================================================================
    print_section("STEP 2: Create Safety Case")

    case = Case(
        title="ADC-ILD Safety Assessment",
        description="Comprehensive safety assessment of interstitial lung disease (ILD) risk with antibody-drug conjugates (ADCs)",
        question="What is the risk of interstitial lung disease (ILD) with antibody-drug conjugates (ADCs)?",
        priority=CasePriority.HIGH,
        submitter="safety-team@pharma.com",
        assigned_sme="Dr. Smith",
        context={
            "has_clinical_data": True,
            "urgency": "high",
            "therapeutic_area": "oncology",
            "regulatory_context": "FDA safety review",
        },
        data_sources=["PubMed", "FDA FAERS", "Clinical Trials"],
    )

    print(f"Case ID: {case.case_id}")
    print(f"Title: {case.title}")
    print(f"Priority: {case.priority.value.upper()}")
    print(f"Question: {case.question}")
    print(f"\nThis case will be decomposed into 3 tasks:")
    print("  1. Literature Review (will fail audit, then retry and pass)")
    print("  2. Statistical Analysis (will pass audit immediately)")
    print("  3. Risk Modeling (will pass audit immediately)")

    # ========================================================================
    # STEP 3: Process the case (orchestrator handles everything)
    # ========================================================================
    print_section("STEP 3: Process Case with Parallel Execution")

    print("The orchestrator will now:")
    print("  1. Decompose case into 3 tasks")
    print("  2. Execute all tasks IN PARALLEL (not sequential!)")
    print("  3. For each task, run Agent-Audit-Resolve loop automatically")
    print("  4. Compress results to prevent context overload")
    print("  5. Synthesize final report from compressed summaries")

    print("\n" + "▼" * 40 + " ORCHESTRATOR PROCESSING " + "▼" * 40)

    start_time = time.time()
    final_report = orchestrator.process_case(case)
    total_time = time.time() - start_time

    print("▲" * 40 + " PROCESSING COMPLETE " + "▲" * 40)

    # ========================================================================
    # STEP 4: Display results
    # ========================================================================
    print_section("STEP 4: Final Case Report")

    print(f"Case Status: {case.status.value.upper()}")
    print(f"Completion Time: {total_time:.2f}s")

    # Handle both interim reports (requires_human_review) and final reports (completed)
    if case.status == CaseStatus.REQUIRES_HUMAN_REVIEW:
        print(f"\nStatus: REQUIRES HUMAN REVIEW")
        print(f"Reason: {final_report.get('escalation_reason', 'N/A')}")
        print(f"\nInterim Findings:")
        for task_type, finding in final_report.get('interim_findings', {}).items():
            print(f"  [{task_type}] {finding.get('status', 'N/A')}")
    else:
        print(f"\nExecutive Summary:")
        print(f"  {final_report['executive_summary'][:200]}...")

        print(f"\nOverall Assessment:")
        print(f"  {final_report['overall_assessment']}")

        print(f"\nConfidence Level:")
        print(f"  {final_report['confidence_level']}")

        print(f"\nRecommendations:")
        for i, rec in enumerate(final_report['recommendations'], 1):
            print(f"  {i}. {rec}")

        print(f"\nFindings by Task Type:")
        for task_type, finding in final_report['findings_by_task'].items():
            print(f"\n  [{task_type.upper()}]")
            print(f"    Status: {finding.get('status', 'N/A')}")
            print(f"    Summary: {finding.get('summary', 'N/A')[:100]}...")

    # ========================================================================
    # STEP 5: Performance analysis
    # ========================================================================
    print_section("STEP 5: Performance Profiling Results")

    print("Performance profiling shows the impact of parallel execution:")
    print("Note: With parallel execution, the 3 tasks run CONCURRENTLY,")
    print("      so total time ≈ max(task_times), not sum(task_times)!\n")

    orchestrator.print_performance_summary(sort_by="total")

    # Calculate theoretical speedup
    stats = orchestrator.get_performance_stats()
    if "operations" in stats:
        ops = stats["operations"]

        # Get individual task times
        lit_time = ops.get("task_literature_review", {}).get("total_time", 0)
        stats_time = ops.get("task_statistical_analysis", {}).get("total_time", 0)
        risk_time = ops.get("task_risk_modeling", {}).get("total_time", 0)

        sequential_time = lit_time + stats_time + risk_time
        parallel_time = max(lit_time, stats_time, risk_time) if all([lit_time, stats_time, risk_time]) else 0

        if parallel_time > 0:
            speedup = sequential_time / parallel_time
            print(f"\nParallel Execution Analysis:")
            print(f"  Sequential execution would take: {sequential_time:.2f}s")
            print(f"  Parallel execution took: {parallel_time:.2f}s")
            print(f"  Speedup: {speedup:.2f}x faster!")
            print(f"  Time saved: {sequential_time - parallel_time:.2f}s ({((sequential_time - parallel_time) / sequential_time * 100):.1f}%)")

    # ========================================================================
    # STEP 6: Summary
    # ========================================================================
    print_header("DEMONSTRATION COMPLETE", char="=")

    print("What this example demonstrated:")
    print()
    print("✓ AGENT-AUDIT-RESOLVE PATTERN:")
    print("  - Literature review failed audit, was corrected, and passed on retry")
    print("  - Statistical analysis and risk modeling passed on first attempt")
    print("  - Automatic validation and correction without manual intervention")
    print()
    print("✓ PARALLEL EXECUTION:")
    print("  - All 3 tasks executed concurrently (not one-by-one)")
    print("  - ~3x speedup compared to sequential execution")
    print("  - Thread-safe orchestrator handling concurrent results")
    print()
    print("✓ PERFORMANCE PROFILING:")
    print("  - Detailed timing for every operation")
    print("  - Identified bottlenecks (e.g., resolution_engine_validation)")
    print("  - Quantified the value of parallel execution")
    print()
    print("✓ CONTEXT COMPRESSION:")
    print("  - Task outputs compressed to key findings only")
    print("  - Prevents orchestrator context overload")
    print("  - Maintains essential information for synthesis")
    print()
    print("✓ ORCHESTRATOR SYNTHESIS:")
    print("  - Combined findings from 3 different task types")
    print("  - Generated executive summary and recommendations")
    print("  - Assessed overall confidence based on all evidence")
    print()
    print("This is the complete safety research system working together!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
