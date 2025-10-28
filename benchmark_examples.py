#!/usr/bin/env python3
"""
Examples: Different ways to use the benchmark suite

This file demonstrates various usage patterns for the parallel execution benchmark.
"""

from benchmark_parallel_execution import (
    StubTaskExecutor,
    ParallelExecutionBenchmark,
    run_custom_benchmark,
    ComparisonResult
)


def example_1_simple_custom_benchmark():
    """Example 1: Simple custom benchmark with specific parameters."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Simple Custom Benchmark")
    print("=" * 80)

    # Run a benchmark with 3 tasks at 0.5s latency
    result = run_custom_benchmark(task_count=3, latency=0.5)

    print(f"\nResults for 3 tasks with 0.5s latency:")
    print(f"  Sequential time: {result.sequential_time:.3f}s")
    print(f"  Parallel time:   {result.parallel_time:.3f}s")
    print(f"  Speedup:         {result.speedup:.2f}x")
    print(f"  Efficiency:      {result.efficiency:.1f}%")
    print(f"  Time saved:      {result.sequential_time - result.parallel_time:.3f}s")


def example_2_compare_latencies():
    """Example 2: Compare different latency scenarios."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Compare Different Latencies")
    print("=" * 80)

    latencies = [0.1, 0.5, 1.0, 2.0]
    task_count = 4

    print(f"\nComparing {task_count} tasks with different latencies:")
    print(f"{'Latency':<12} | {'Sequential':<12} | {'Parallel':<12} | {'Speedup':<10}")
    print("-" * 60)

    for latency in latencies:
        result = run_custom_benchmark(task_count=task_count, latency=latency)
        print(
            f"{latency:>10.1f}s | "
            f"{result.sequential_time:>10.3f}s | "
            f"{result.parallel_time:>10.3f}s | "
            f"{result.speedup:>8.2f}x"
        )


def example_3_find_optimal_task_count():
    """Example 3: Find optimal task count for parallelization."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Find Optimal Task Count")
    print("=" * 80)

    latency = 0.5
    task_counts = range(1, 9)

    print(f"\nFinding optimal task count (latency={latency}s per task):")
    print(f"{'Tasks':<8} | {'Sequential':<12} | {'Parallel':<12} | {'Speedup':<10} | {'Efficiency':<12}")
    print("-" * 70)

    best_efficiency = 0
    best_task_count = 0

    for count in task_counts:
        result = run_custom_benchmark(task_count=count, latency=latency)
        print(
            f"{count:<8} | "
            f"{result.sequential_time:>10.3f}s | "
            f"{result.parallel_time:>10.3f}s | "
            f"{result.speedup:>8.2f}x | "
            f"{result.efficiency:>10.1f}%"
        )

        if result.efficiency > best_efficiency and count > 1:
            best_efficiency = result.efficiency
            best_task_count = count

    print(f"\nOptimal task count: {best_task_count} tasks (efficiency: {best_efficiency:.1f}%)")


def example_4_using_executor_directly():
    """Example 4: Use StubTaskExecutor directly for custom benchmarks."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Using StubTaskExecutor Directly")
    print("=" * 80)

    # Create executor with custom latency
    executor = StubTaskExecutor(task_latency=0.3)

    # Create custom task definitions
    tasks = [
        {"type": "literature_review", "priority": "high"},
        {"type": "statistical_analysis", "priority": "medium"},
        {"type": "risk_modeling", "priority": "high"}
    ]

    print(f"\nExecuting {len(tasks)} custom tasks with 0.3s latency each...")

    # Run sequential
    seq_result = executor.execute_sequential(tasks)
    print(f"\n  Sequential execution:")
    print(f"    Total time: {seq_result.total_time:.3f}s")
    print(f"    Avg per task: {seq_result.avg_task_time:.3f}s")

    # Run parallel
    par_result = executor.execute_parallel(tasks, max_workers=3)
    print(f"\n  Parallel execution:")
    print(f"    Total time: {par_result.total_time:.3f}s")
    print(f"    Avg per task: {par_result.avg_task_time:.3f}s")

    # Calculate improvement
    speedup = seq_result.total_time / par_result.total_time
    time_saved = seq_result.total_time - par_result.total_time
    print(f"\n  Performance improvement:")
    print(f"    Speedup: {speedup:.2f}x")
    print(f"    Time saved: {time_saved:.3f}s ({time_saved/seq_result.total_time*100:.1f}%)")


def example_5_batch_size_analysis():
    """Example 5: Analyze optimal batch size for task processing."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Batch Size Analysis")
    print("=" * 80)

    total_tasks = 12
    latency = 0.5
    batch_sizes = [1, 2, 3, 4, 6]

    print(f"\nProcessing {total_tasks} tasks with different batch sizes:")
    print(f"(Simulating batched parallel execution)")
    print(f"\n{'Batch Size':<12} | {'Total Time':<12} | {'Batches':<10} | {'Efficiency':<12}")
    print("-" * 60)

    import math

    for batch_size in batch_sizes:
        num_batches = math.ceil(total_tasks / batch_size)
        time_per_batch = latency  # All tasks in batch run in parallel
        total_time = num_batches * time_per_batch
        sequential_time = total_tasks * latency
        efficiency = (sequential_time / total_time / total_tasks) * 100

        print(
            f"{batch_size:<12} | "
            f"{total_time:>10.3f}s | "
            f"{num_batches:<10} | "
            f"{efficiency:>10.1f}%"
        )


def example_6_worker_pool_sizing():
    """Example 6: Test different worker pool sizes."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Worker Pool Sizing")
    print("=" * 80)

    task_count = 8
    latency = 0.5
    worker_counts = [1, 2, 4, 8, 16]

    executor = StubTaskExecutor(task_latency=latency)
    tasks = [{"data": f"task_{i}"} for i in range(task_count)]

    print(f"\nTesting {task_count} tasks with different worker pool sizes:")
    print(f"{'Workers':<10} | {'Time':<12} | {'Speedup':<10}")
    print("-" * 40)

    # Get baseline (sequential)
    seq_result = executor.execute_sequential(tasks)
    sequential_time = seq_result.total_time

    for workers in worker_counts:
        par_result = executor.execute_parallel(tasks, max_workers=workers)
        speedup = sequential_time / par_result.total_time
        print(
            f"{workers:<10} | "
            f"{par_result.total_time:>10.3f}s | "
            f"{speedup:>8.2f}x"
        )


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("PARALLEL EXECUTION BENCHMARK - USAGE EXAMPLES")
    print("=" * 80)

    examples = [
        example_1_simple_custom_benchmark,
        example_2_compare_latencies,
        example_3_find_optimal_task_count,
        example_4_using_executor_directly,
        example_5_batch_size_analysis,
        example_6_worker_pool_sizing
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
