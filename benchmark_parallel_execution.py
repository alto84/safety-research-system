#!/usr/bin/env python3
"""
Comprehensive Benchmark: Sequential vs. Parallel Execution

This script benchmarks the performance difference between sequential and parallel
execution of tasks. It uses stub implementations with simulated API latency to
demonstrate the benefits of parallelization.

Key Features:
- Tests with 1, 2, 3, and 4 tasks
- Simulates both fast (0.5s) and slow (1.0s) task scenarios
- Uses PerformanceProfiler for detailed timing analysis
- Calculates speedup ratios and efficiency percentages
- Prints formatted comparison tables

Usage:
    python benchmark_parallel_execution.py

    # Or make it executable and run directly:
    chmod +x benchmark_parallel_execution.py
    ./benchmark_parallel_execution.py
"""

import time
import logging
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime

# Import performance profiler
from core.performance_profiler import PerformanceProfiler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    task_count: int
    execution_mode: str  # 'sequential' or 'parallel'
    total_time: float
    task_type: str  # 'fast' or 'slow'
    individual_task_times: List[float]

    @property
    def avg_task_time(self) -> float:
        """Calculate average task execution time."""
        return sum(self.individual_task_times) / len(self.individual_task_times) if self.individual_task_times else 0.0


@dataclass
class ComparisonResult:
    """Comparison between sequential and parallel execution."""
    task_count: int
    task_type: str
    sequential_time: float
    parallel_time: float
    speedup: float
    efficiency: float  # Percentage: (speedup / task_count) * 100

    def __str__(self) -> str:
        """Format comparison result as string."""
        return (
            f"Tasks: {self.task_count} | "
            f"Sequential: {self.sequential_time:.3f}s | "
            f"Parallel: {self.parallel_time:.3f}s | "
            f"Speedup: {self.speedup:.2f}x | "
            f"Efficiency: {self.efficiency:.1f}%"
        )


class StubTaskExecutor:
    """
    Stub implementation of task executor for benchmarking.

    Simulates task execution with configurable latency using time.sleep().
    This mimics real-world API calls to LLM services.
    """

    def __init__(self, task_latency: float = 1.0):
        """
        Initialize stub task executor.

        Args:
            task_latency: Simulated latency per task in seconds (default: 1.0s)
        """
        self.task_latency = task_latency
        self.profiler = PerformanceProfiler()

    def execute_task_stub(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task (stub implementation).

        Args:
            task_id: Unique task identifier
            task_data: Task input data

        Returns:
            Simulated task output
        """
        with self.profiler.profile(f"task_execution_{task_id}"):
            # Simulate API latency (e.g., LLM call)
            logger.debug(f"Executing task {task_id} with {self.task_latency}s latency")
            time.sleep(self.task_latency)

            # Return stub result
            return {
                "task_id": task_id,
                "result": f"Completed task {task_id}",
                "execution_time": self.task_latency,
                "timestamp": datetime.utcnow().isoformat()
            }

    def execute_sequential(self, tasks: List[Dict[str, Any]]) -> BenchmarkResult:
        """
        Execute tasks sequentially (one after another).

        Args:
            tasks: List of task definitions

        Returns:
            BenchmarkResult with timing information
        """
        self.profiler.reset()
        task_times = []

        with self.profiler.profile("sequential_execution_total"):
            for i, task in enumerate(tasks):
                task_id = f"task_{i+1}"
                start = time.perf_counter()
                self.execute_task_stub(task_id, task)
                end = time.perf_counter()
                task_times.append(end - start)

        stats = self.profiler.get_stats("sequential_execution_total")
        total_time = stats.total_time if stats else 0.0

        return BenchmarkResult(
            task_count=len(tasks),
            execution_mode="sequential",
            total_time=total_time,
            task_type="fast" if self.task_latency < 0.8 else "slow",
            individual_task_times=task_times
        )

    def execute_parallel(self, tasks: List[Dict[str, Any]], max_workers: int = 4) -> BenchmarkResult:
        """
        Execute tasks in parallel using ThreadPoolExecutor.

        Args:
            tasks: List of task definitions
            max_workers: Maximum number of parallel workers (default: 4)

        Returns:
            BenchmarkResult with timing information
        """
        self.profiler.reset()
        task_times = []

        with self.profiler.profile("parallel_execution_total"):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_task = {}
                for i, task in enumerate(tasks):
                    task_id = f"task_{i+1}"
                    future = executor.submit(self.execute_task_stub, task_id, task)
                    future_to_task[future] = (task_id, time.perf_counter())

                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task_id, start_time = future_to_task[future]
                    end_time = time.perf_counter()
                    task_times.append(end_time - start_time)

                    try:
                        result = future.result()
                        logger.debug(f"Task {task_id} completed")
                    except Exception as e:
                        logger.error(f"Task {task_id} failed: {e}")

        stats = self.profiler.get_stats("parallel_execution_total")
        total_time = stats.total_time if stats else 0.0

        return BenchmarkResult(
            task_count=len(tasks),
            execution_mode="parallel",
            total_time=total_time,
            task_type="fast" if self.task_latency < 0.8 else "slow",
            individual_task_times=task_times
        )


class ParallelExecutionBenchmark:
    """
    Main benchmark orchestrator for comparing sequential vs parallel execution.
    """

    def __init__(self):
        """Initialize the benchmark suite."""
        self.results: List[ComparisonResult] = []
        self.profiler = PerformanceProfiler()

    def run_benchmark_suite(self) -> None:
        """
        Run complete benchmark suite with various task counts and scenarios.
        """
        print("\n" + "=" * 100)
        print("PARALLEL EXECUTION BENCHMARK SUITE")
        print("=" * 100)
        print("\nThis benchmark compares sequential vs parallel execution across different scenarios.")
        print("Simulated API latency is used to mimic real-world LLM calls.\n")

        # Test configurations
        task_counts = [1, 2, 3, 4]
        scenarios = [
            ("Fast Tasks (0.5s latency)", 0.5),
            ("Slow Tasks (1.0s latency)", 1.0)
        ]

        for scenario_name, latency in scenarios:
            print("\n" + "-" * 100)
            print(f"SCENARIO: {scenario_name}")
            print("-" * 100)

            scenario_results = []

            for task_count in task_counts:
                comparison = self._run_single_comparison(task_count, latency)
                scenario_results.append(comparison)
                self.results.append(comparison)

            # Print scenario summary table
            self._print_scenario_table(scenario_name, scenario_results)

        # Print overall summary
        self._print_overall_summary()

    def _run_single_comparison(self, task_count: int, latency: float) -> ComparisonResult:
        """
        Run a single comparison between sequential and parallel execution.

        Args:
            task_count: Number of tasks to execute
            latency: Simulated latency per task in seconds

        Returns:
            ComparisonResult with timing and speedup information
        """
        # Create task definitions
        tasks = [{"data": f"task_{i+1}"} for i in range(task_count)]

        # Create executor with specified latency
        executor = StubTaskExecutor(task_latency=latency)

        # Run sequential execution
        print(f"\n  Running {task_count} task(s) sequentially...")
        with self.profiler.profile(f"comparison_{task_count}tasks_sequential"):
            sequential_result = executor.execute_sequential(tasks)

        # Run parallel execution
        print(f"  Running {task_count} task(s) in parallel...")
        with self.profiler.profile(f"comparison_{task_count}tasks_parallel"):
            parallel_result = executor.execute_parallel(tasks, max_workers=4)

        # Calculate speedup and efficiency
        speedup = sequential_result.total_time / parallel_result.total_time if parallel_result.total_time > 0 else 0
        efficiency = (speedup / task_count * 100) if task_count > 0 else 0

        comparison = ComparisonResult(
            task_count=task_count,
            task_type="fast" if latency < 0.8 else "slow",
            sequential_time=sequential_result.total_time,
            parallel_time=parallel_result.total_time,
            speedup=speedup,
            efficiency=efficiency
        )

        print(f"  Result: {comparison}")

        return comparison

    def _print_scenario_table(self, scenario_name: str, results: List[ComparisonResult]) -> None:
        """
        Print formatted table for a scenario's results.

        Args:
            scenario_name: Name of the scenario
            results: List of comparison results for this scenario
        """
        print("\n" + "  " + "=" * 96)
        print(f"  SUMMARY TABLE: {scenario_name}")
        print("  " + "=" * 96)
        print(f"  {'Tasks':<8} | {'Sequential':<14} | {'Parallel':<14} | {'Speedup':<12} | {'Efficiency':<12}")
        print("  " + "-" * 96)

        for result in results:
            print(
                f"  {result.task_count:<8} | "
                f"{result.sequential_time:>10.3f}s    | "
                f"{result.parallel_time:>10.3f}s    | "
                f"{result.speedup:>8.2f}x     | "
                f"{result.efficiency:>9.1f}%"
            )

        print("  " + "=" * 96)

    def _print_overall_summary(self) -> None:
        """Print overall benchmark summary with insights."""
        print("\n" + "=" * 100)
        print("OVERALL SUMMARY & INSIGHTS")
        print("=" * 100)

        # Group results by task type
        fast_results = [r for r in self.results if r.task_type == "fast"]
        slow_results = [r for r in self.results if r.task_type == "slow"]

        print("\nKey Findings:")
        print("-" * 100)

        # Finding 1: Single task overhead
        single_task_results = [r for r in self.results if r.task_count == 1]
        if single_task_results:
            avg_overhead = sum(r.parallel_time - r.sequential_time for r in single_task_results) / len(single_task_results)
            print(f"\n1. Single Task Overhead:")
            print(f"   - Parallel execution adds ~{avg_overhead*1000:.1f}ms overhead for single tasks")
            print(f"   - Conclusion: Sequential is better for single tasks")

        # Finding 2: Maximum speedup
        if self.results:
            max_speedup_result = max(self.results, key=lambda r: r.speedup)
            print(f"\n2. Maximum Speedup Achieved:")
            print(f"   - {max_speedup_result.speedup:.2f}x with {max_speedup_result.task_count} {max_speedup_result.task_type} tasks")
            print(f"   - Time saved: {max_speedup_result.sequential_time - max_speedup_result.parallel_time:.3f}s")

        # Finding 3: Efficiency analysis
        multi_task_results = [r for r in self.results if r.task_count > 1]
        if multi_task_results:
            avg_efficiency = sum(r.efficiency for r in multi_task_results) / len(multi_task_results)
            print(f"\n3. Average Parallel Efficiency (multi-task):")
            print(f"   - {avg_efficiency:.1f}% efficiency across all multi-task scenarios")
            if avg_efficiency > 80:
                print(f"   - Excellent parallelization with minimal overhead")
            elif avg_efficiency > 60:
                print(f"   - Good parallelization, some threading overhead present")
            else:
                print(f"   - Moderate parallelization, consider optimization")

        # Finding 4: Optimal task count
        print(f"\n4. Optimization Recommendations:")
        for task_count in [2, 3, 4]:
            count_results = [r for r in self.results if r.task_count == task_count]
            if count_results:
                avg_speedup = sum(r.speedup for r in count_results) / len(count_results)
                avg_time_saved = sum(r.sequential_time - r.parallel_time for r in count_results) / len(count_results)
                print(f"   - {task_count} tasks: ~{avg_speedup:.2f}x speedup, saves ~{avg_time_saved:.3f}s")

        # Finding 5: When to use parallel
        print(f"\n5. Decision Guide - When to Use Parallel Execution:")
        print(f"   - Use SEQUENTIAL for: 1 task (avoids overhead)")
        print(f"   - Use PARALLEL for: 2+ tasks (significant speedup)")
        print(f"   - Maximum benefit: 3-4 concurrent tasks with current ThreadPool settings")

        print("\n" + "=" * 100)

        # Print detailed profiler stats
        print("\nDETAILED PERFORMANCE PROFILING:")
        self.profiler.print_summary(sort_by="total")


def run_custom_benchmark(
    task_count: int,
    latency: float,
    max_workers: int = 4
) -> ComparisonResult:
    """
    Run a custom benchmark with specific parameters.

    This is a convenience function for running individual benchmarks with custom settings.

    Args:
        task_count: Number of tasks to execute
        latency: Simulated latency per task in seconds
        max_workers: Maximum number of parallel workers

    Returns:
        ComparisonResult with timing and speedup information

    Example:
        >>> result = run_custom_benchmark(task_count=5, latency=0.75, max_workers=4)
        >>> print(f"Speedup: {result.speedup:.2f}x")
    """
    tasks = [{"data": f"task_{i+1}"} for i in range(task_count)]
    executor = StubTaskExecutor(task_latency=latency)

    sequential_result = executor.execute_sequential(tasks)
    parallel_result = executor.execute_parallel(tasks, max_workers=max_workers)

    speedup = sequential_result.total_time / parallel_result.total_time if parallel_result.total_time > 0 else 0
    efficiency = (speedup / task_count * 100) if task_count > 0 else 0

    return ComparisonResult(
        task_count=task_count,
        task_type="custom",
        sequential_time=sequential_result.total_time,
        parallel_time=parallel_result.total_time,
        speedup=speedup,
        efficiency=efficiency
    )


def main():
    """
    Main entry point for the benchmark script.

    Runs the complete benchmark suite and displays results.
    """
    # Run the comprehensive benchmark suite
    benchmark = ParallelExecutionBenchmark()
    benchmark.run_benchmark_suite()

    # Example: Run a custom benchmark
    print("\n" + "=" * 100)
    print("BONUS: Custom Benchmark Example")
    print("=" * 100)
    print("\nRunning custom benchmark with 5 tasks at 0.75s latency...")

    custom_result = run_custom_benchmark(task_count=5, latency=0.75, max_workers=4)
    print(f"\nCustom Result: {custom_result}")
    print(f"Time saved: {custom_result.sequential_time - custom_result.parallel_time:.3f}s")

    print("\n" + "=" * 100)
    print("BENCHMARK COMPLETE!")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    main()
