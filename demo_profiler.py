#!/usr/bin/env python3
"""Demonstration of the performance profiler module."""

import time
import random
from core.performance_profiler import PerformanceProfiler, profile


def simulate_database_query():
    """Simulate a database query."""
    time.sleep(random.uniform(0.01, 0.05))
    return [{"id": i, "data": f"record_{i}"} for i in range(100)]


def simulate_data_processing(data):
    """Simulate data processing."""
    time.sleep(random.uniform(0.005, 0.02))
    return [item["data"].upper() for item in data]


def simulate_api_call():
    """Simulate an API call."""
    time.sleep(random.uniform(0.02, 0.08))
    return {"status": "success", "data": "response"}


def demo_basic_profiling():
    """Demonstrate basic profiling with context managers."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Profiling with Context Managers")
    print("=" * 80)

    profiler = PerformanceProfiler()

    # Simulate a workflow
    for i in range(5):
        with profiler.profile("database_query"):
            data = simulate_database_query()

        with profiler.profile("data_processing"):
            processed = simulate_data_processing(data)

        with profiler.profile("api_call"):
            result = simulate_api_call()

    # Print summary
    profiler.print_summary()


def demo_nested_profiling():
    """Demonstrate nested profiling operations."""
    print("\n" + "=" * 80)
    print("DEMO 2: Nested Profiling Operations")
    print("=" * 80)

    profiler = PerformanceProfiler()

    for i in range(3):
        with profiler.profile("complete_workflow"):
            with profiler.profile("data_fetch"):
                data = simulate_database_query()

            with profiler.profile("transform"):
                processed = simulate_data_processing(data)

            with profiler.profile("publish"):
                result = simulate_api_call()

    profiler.print_summary(sort_by="mean")


def demo_global_profiler():
    """Demonstrate using the global profiler."""
    print("\n" + "=" * 80)
    print("DEMO 3: Using Global Profiler (Convenience Function)")
    print("=" * 80)

    # Using the convenience function
    for i in range(4):
        with profile("global_operation_1"):
            time.sleep(random.uniform(0.01, 0.03))

        with profile("global_operation_2"):
            time.sleep(random.uniform(0.02, 0.05))

    # Get the global profiler and print summary
    from core.performance_profiler import get_global_profiler
    global_profiler = get_global_profiler()
    global_profiler.print_summary()


def demo_statistics_access():
    """Demonstrate accessing statistics programmatically."""
    print("\n" + "=" * 80)
    print("DEMO 4: Accessing Statistics Programmatically")
    print("=" * 80)

    profiler = PerformanceProfiler()

    # Run some operations
    for i in range(10):
        with profiler.profile("fast_operation"):
            time.sleep(0.001)

        with profiler.profile("slow_operation"):
            time.sleep(0.05)

    # Get statistics
    stats_dict = profiler.get_summary_dict()

    print("\nProgrammatic Statistics Access:")
    print(f"Total operations tracked: {stats_dict['totals']['num_operations']}")
    print(f"Total calls: {stats_dict['totals']['total_calls']}")
    print(f"Total time: {profiler.format_duration(stats_dict['totals']['total_time'])}")

    print("\nPer-operation details:")
    for op_name, op_stats in stats_dict['operations'].items():
        print(f"\n  {op_name}:")
        print(f"    Count: {op_stats['count']}")
        print(f"    Mean: {profiler.format_duration(op_stats['mean_time'])}")
        print(f"    Median: {profiler.format_duration(op_stats['median_time'])}")
        print(f"    Min: {profiler.format_duration(op_stats['min_time'])}")
        print(f"    Max: {profiler.format_duration(op_stats['max_time'])}")


def demo_thread_safety():
    """Demonstrate thread-safe operation."""
    import threading

    print("\n" + "=" * 80)
    print("DEMO 5: Thread-Safe Profiling")
    print("=" * 80)

    profiler = PerformanceProfiler()

    def worker(worker_id, num_ops):
        """Worker function for threaded operations."""
        for i in range(num_ops):
            with profiler.profile(f"worker_{worker_id}_task"):
                time.sleep(random.uniform(0.001, 0.01))

            with profiler.profile("shared_task"):
                time.sleep(random.uniform(0.001, 0.005))

    # Create and start threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, 3))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("\nAll threads completed. Profiling results:")
    profiler.print_summary(sort_by="count")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("PERFORMANCE PROFILER DEMONSTRATION")
    print("=" * 80)

    try:
        demo_basic_profiling()
        demo_nested_profiling()
        demo_global_profiler()
        demo_statistics_access()
        demo_thread_safety()

        print("\n" + "=" * 80)
        print("All demonstrations completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
