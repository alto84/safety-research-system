#!/usr/bin/env python3
"""Example demonstrating performance profiling in the Orchestrator class.

This script shows how the performance profiler is integrated into the
Orchestrator and how to access profiling statistics after processing a case.
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import required components
from models.case import Case, CaseStatus
from models.task import Task, TaskType
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor
from agents.orchestrator import Orchestrator


def create_example_case() -> Case:
    """Create an example safety case for demonstration.

    Returns:
        Case object with sample data
    """
    case = Case(
        title="Example Safety Case",
        question="What are the key safety considerations for this medical intervention?",
        context={
            "has_clinical_data": True,
            "intervention_type": "drug",
            "patient_population": "adults",
        },
        data_sources=["pubmed", "clinical_trials_gov"],
    )
    return case


def example_with_profiling():
    """Example showing orchestrator with profiling enabled."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Orchestrator with Profiling Enabled")
    print("=" * 80 + "\n")

    # Initialize components (normally these would be properly configured)
    task_executor = TaskExecutor()
    audit_engine = AuditEngine()
    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine
    )
    context_compressor = ContextCompressor()

    # Create orchestrator with profiling enabled (default)
    orchestrator = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=True  # This is the default
    )

    # Create and process a case
    case = create_example_case()

    try:
        # Note: This will fail in demo mode because we don't have real LLM backends
        # In production, this would process the case and collect timing data
        result = orchestrator.process_case(case)

        # The final report includes performance stats automatically
        if "performance_stats" in result:
            print("\nPerformance statistics included in final report:")
            print(f"  Total operations: {result['performance_stats']['totals']['num_operations']}")
            print(f"  Total calls: {result['performance_stats']['totals']['total_calls']}")

        # You can also access stats directly
        print("\nDirect access to performance statistics:")
        orchestrator.print_performance_summary(sort_by="total")

        # Or get them as a dictionary
        stats = orchestrator.get_performance_stats()
        print("\nStats as dictionary:")
        for op_name, op_stats in stats['operations'].items():
            print(f"  {op_name}: {op_stats['count']} calls, "
                  f"mean={op_stats['mean_time']:.3f}s")

    except Exception as e:
        print(f"Expected error in demo mode: {type(e).__name__}")
        print("In production, this would show actual profiling data from case processing.")


def example_without_profiling():
    """Example showing orchestrator with profiling disabled."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Orchestrator with Profiling Disabled")
    print("=" * 80 + "\n")

    # Initialize components
    task_executor = TaskExecutor()
    audit_engine = AuditEngine()
    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine
    )
    context_compressor = ContextCompressor()

    # Create orchestrator with profiling disabled
    orchestrator = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=False  # Disable profiling for production speed
    )

    print("Profiling is disabled - no overhead from timing operations")
    print(f"Profiler enabled: {orchestrator.profiler.enabled}")


def example_profiling_operations():
    """Example showing what operations are profiled in the Orchestrator."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Operations Profiled by Orchestrator")
    print("=" * 80 + "\n")

    print("The Orchestrator profiles the following operations:")
    print("\n1. process_case_total")
    print("   - Total time to process an entire case")
    print("\n2. decompose_case")
    print("   - Time to decompose a case into tasks")
    print("\n3. execute_all_tasks")
    print("   - Total time to execute all tasks in a case")
    print("\n4. task_<TaskType>")
    print("   - Time to execute each specific task type")
    print("   - Examples: task_LITERATURE_REVIEW, task_STATISTICAL_ANALYSIS")
    print("\n5. resolution_engine_validation")
    print("   - Time spent in the resolution engine validation loop")
    print("\n6. compress_task_result")
    print("   - Time to compress task results")
    print("\n7. check_human_review")
    print("   - Time to check if human review is needed")
    print("\n8. synthesize_final_report")
    print("   - Time to synthesize the final report")


def example_custom_profiling():
    """Example showing how to add custom profiling to your own code."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Adding Custom Profiling to Your Code")
    print("=" * 80 + "\n")

    from core.performance_profiler import PerformanceProfiler
    import time

    # Create a profiler instance
    profiler = PerformanceProfiler()

    # Profile some operations
    for i in range(5):
        with profiler.profile("data_loading"):
            time.sleep(0.01)  # Simulate loading

        with profiler.profile("computation"):
            time.sleep(0.02)  # Simulate computation

        with profiler.profile("saving_results"):
            time.sleep(0.005)  # Simulate saving

    # Show results
    print("\nCustom profiling results:")
    profiler.print_summary()

    # You can also use the global profiler
    from core.performance_profiler import profile, get_global_profiler

    for i in range(3):
        with profile("global_operation"):
            time.sleep(0.01)

    print("\nGlobal profiler results:")
    get_global_profiler().print_summary()


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("ORCHESTRATOR PERFORMANCE PROFILING EXAMPLES")
    print("=" * 80)

    example_with_profiling()
    example_without_profiling()
    example_profiling_operations()
    example_custom_profiling()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
