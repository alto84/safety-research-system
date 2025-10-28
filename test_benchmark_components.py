#!/usr/bin/env python3
"""
Quick validation test for benchmark components.

This script tests individual components of the benchmark to ensure they work correctly.
"""

import sys
from benchmark_parallel_execution import (
    StubTaskExecutor,
    BenchmarkResult,
    ComparisonResult,
    run_custom_benchmark
)


def test_stub_executor():
    """Test the StubTaskExecutor class."""
    print("Testing StubTaskExecutor...")

    executor = StubTaskExecutor(task_latency=0.1)
    tasks = [{"data": f"task_{i}"} for i in range(2)]

    # Test sequential execution
    seq_result = executor.execute_sequential(tasks)
    assert seq_result.task_count == 2
    assert seq_result.execution_mode == "sequential"
    assert seq_result.total_time >= 0.2  # At least 2 * 0.1s
    print(f"  ✓ Sequential execution: {seq_result.total_time:.3f}s for {seq_result.task_count} tasks")

    # Test parallel execution
    par_result = executor.execute_parallel(tasks, max_workers=2)
    assert par_result.task_count == 2
    assert par_result.execution_mode == "parallel"
    assert par_result.total_time < seq_result.total_time  # Should be faster
    print(f"  ✓ Parallel execution: {par_result.total_time:.3f}s for {par_result.task_count} tasks")

    speedup = seq_result.total_time / par_result.total_time
    print(f"  ✓ Speedup achieved: {speedup:.2f}x")

    return True


def test_comparison_result():
    """Test the ComparisonResult class."""
    print("\nTesting ComparisonResult...")

    result = ComparisonResult(
        task_count=3,
        task_type="test",
        sequential_time=3.0,
        parallel_time=1.0,
        speedup=3.0,
        efficiency=100.0
    )

    result_str = str(result)
    assert "3" in result_str
    assert "3.000s" in result_str
    assert "1.000s" in result_str
    assert "3.00x" in result_str
    print(f"  ✓ ComparisonResult formatting: {result_str}")

    return True


def test_custom_benchmark():
    """Test the run_custom_benchmark function."""
    print("\nTesting custom benchmark function...")

    result = run_custom_benchmark(task_count=2, latency=0.1, max_workers=2)

    assert result.task_count == 2
    assert result.speedup > 0
    assert result.efficiency > 0
    print(f"  ✓ Custom benchmark completed")
    print(f"    - Task count: {result.task_count}")
    print(f"    - Sequential time: {result.sequential_time:.3f}s")
    print(f"    - Parallel time: {result.parallel_time:.3f}s")
    print(f"    - Speedup: {result.speedup:.2f}x")
    print(f"    - Efficiency: {result.efficiency:.1f}%")

    return True


def test_benchmark_result():
    """Test the BenchmarkResult class."""
    print("\nTesting BenchmarkResult...")

    result = BenchmarkResult(
        task_count=3,
        execution_mode="test",
        total_time=1.5,
        task_type="fast",
        individual_task_times=[0.5, 0.5, 0.5]
    )

    assert result.avg_task_time == 0.5
    print(f"  ✓ Average task time calculation: {result.avg_task_time:.3f}s")

    return True


def main():
    """Run all validation tests."""
    print("=" * 80)
    print("BENCHMARK COMPONENT VALIDATION")
    print("=" * 80)

    tests = [
        ("StubTaskExecutor", test_stub_executor),
        ("BenchmarkResult", test_benchmark_result),
        ("ComparisonResult", test_comparison_result),
        ("Custom Benchmark", test_custom_benchmark)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
