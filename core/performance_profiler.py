"""Performance profiling module for tracking operation timing and statistics.

This module provides a lightweight, thread-safe profiler for tracking the performance
of operations throughout the safety research system. It uses context managers for
easy integration and provides detailed statistics.
"""

import time
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TimingStats:
    """Statistics for a profiled operation."""

    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    timings: List[float] = field(default_factory=list)

    def add_timing(self, duration: float) -> None:
        """Add a timing measurement to the statistics.

        Args:
            duration: Duration in seconds
        """
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.timings.append(duration)

    @property
    def mean_time(self) -> float:
        """Calculate mean time.

        Returns:
            Mean duration in seconds, or 0 if no timings recorded
        """
        return self.total_time / self.count if self.count > 0 else 0.0

    @property
    def median_time(self) -> float:
        """Calculate median time.

        Returns:
            Median duration in seconds, or 0 if no timings recorded
        """
        if not self.timings:
            return 0.0
        sorted_timings = sorted(self.timings)
        n = len(sorted_timings)
        if n % 2 == 0:
            return (sorted_timings[n // 2 - 1] + sorted_timings[n // 2]) / 2
        return sorted_timings[n // 2]


class PerformanceProfiler:
    """Thread-safe performance profiler for tracking operation timing.

    This profiler uses context managers to track timing of operations and
    accumulates statistics including count, mean, min, max, and total duration.

    Example:
        profiler = PerformanceProfiler()

        with profiler.profile("database_query"):
            # Your operation here
            result = db.query(...)

        with profiler.profile("data_processing"):
            # Another operation
            process_data(result)

        # Print summary
        profiler.print_summary()
    """

    def __init__(self, enabled: bool = True):
        """Initialize the profiler.

        Args:
            enabled: Whether profiling is enabled (default: True)
        """
        self.enabled = enabled
        self._stats: Dict[str, TimingStats] = defaultdict(TimingStats)
        self._lock = threading.Lock()
        self._active_timers: Dict[str, List[float]] = defaultdict(list)

    @contextmanager
    def profile(self, operation_name: str):
        """Context manager for profiling an operation.

        Args:
            operation_name: Name of the operation being profiled

        Yields:
            None

        Example:
            with profiler.profile("my_operation"):
                # Code to profile
                do_something()
        """
        if not self.enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            self._record_timing(operation_name, duration)

    def _record_timing(self, operation_name: str, duration: float) -> None:
        """Record a timing measurement (thread-safe).

        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
        """
        with self._lock:
            self._stats[operation_name].add_timing(duration)

    def get_stats(self, operation_name: str) -> Optional[TimingStats]:
        """Get statistics for a specific operation.

        Args:
            operation_name: Name of the operation

        Returns:
            TimingStats object if operation exists, None otherwise
        """
        with self._lock:
            return self._stats.get(operation_name)

    def get_all_stats(self) -> Dict[str, TimingStats]:
        """Get all accumulated statistics.

        Returns:
            Dictionary mapping operation names to their statistics
        """
        with self._lock:
            return dict(self._stats)

    def reset(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self._stats.clear()
            self._active_timers.clear()

    def reset_operation(self, operation_name: str) -> None:
        """Reset statistics for a specific operation.

        Args:
            operation_name: Name of the operation to reset
        """
        with self._lock:
            if operation_name in self._stats:
                del self._stats[operation_name]

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (e.g., "1.23s", "456.78ms", "12.34us")
        """
        if seconds >= 1.0:
            return f"{seconds:.3f}s"
        elif seconds >= 0.001:
            return f"{seconds * 1000:.2f}ms"
        elif seconds >= 0.000001:
            return f"{seconds * 1000000:.2f}us"
        else:
            return f"{seconds * 1000000000:.2f}ns"

    def print_summary(self, sort_by: str = "total") -> None:
        """Print a formatted summary of all profiling statistics.

        Args:
            sort_by: How to sort operations. Options: "total", "mean", "count", "name"
                    (default: "total")
        """
        stats = self.get_all_stats()

        if not stats:
            print("\nNo profiling data available.")
            return

        # Sort operations
        if sort_by == "total":
            sorted_ops = sorted(stats.items(), key=lambda x: x[1].total_time, reverse=True)
        elif sort_by == "mean":
            sorted_ops = sorted(stats.items(), key=lambda x: x[1].mean_time, reverse=True)
        elif sort_by == "count":
            sorted_ops = sorted(stats.items(), key=lambda x: x[1].count, reverse=True)
        else:  # sort by name
            sorted_ops = sorted(stats.items(), key=lambda x: x[0])

        # Calculate column widths
        max_name_len = max(len(name) for name in stats.keys())
        name_width = max(max_name_len, 20)

        # Print header
        print("\n" + "=" * 100)
        print("PERFORMANCE PROFILING SUMMARY")
        print("=" * 100)
        print(f"{'Operation':<{name_width}} | {'Count':>8} | {'Total':>12} | {'Mean':>12} | {'Min':>12} | {'Max':>12} | {'Median':>12}")
        print("-" * 100)

        # Print stats for each operation
        for op_name, op_stats in sorted_ops:
            print(
                f"{op_name:<{name_width}} | "
                f"{op_stats.count:>8} | "
                f"{self.format_duration(op_stats.total_time):>12} | "
                f"{self.format_duration(op_stats.mean_time):>12} | "
                f"{self.format_duration(op_stats.min_time):>12} | "
                f"{self.format_duration(op_stats.max_time):>12} | "
                f"{self.format_duration(op_stats.median_time):>12}"
            )

        # Print summary totals
        total_time = sum(s.total_time for s in stats.values())
        total_calls = sum(s.count for s in stats.values())

        print("-" * 100)
        print(f"{'TOTAL':<{name_width}} | {total_calls:>8} | {self.format_duration(total_time):>12}")
        print("=" * 100 + "\n")

    def get_summary_dict(self) -> Dict[str, Any]:
        """Get summary statistics as a dictionary.

        Returns:
            Dictionary containing summary statistics for all operations
        """
        stats = self.get_all_stats()

        summary = {
            "operations": {},
            "totals": {
                "total_time": 0.0,
                "total_calls": 0,
                "num_operations": len(stats)
            }
        }

        for op_name, op_stats in stats.items():
            summary["operations"][op_name] = {
                "count": op_stats.count,
                "total_time": op_stats.total_time,
                "mean_time": op_stats.mean_time,
                "median_time": op_stats.median_time,
                "min_time": op_stats.min_time,
                "max_time": op_stats.max_time
            }
            summary["totals"]["total_time"] += op_stats.total_time
            summary["totals"]["total_calls"] += op_stats.count

        return summary


# Global profiler instance for convenience
_global_profiler: Optional[PerformanceProfiler] = None


def get_global_profiler() -> PerformanceProfiler:
    """Get or create the global profiler instance.

    Returns:
        Global PerformanceProfiler instance
    """
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = PerformanceProfiler()
    return _global_profiler


def set_global_profiler(profiler: Optional[PerformanceProfiler]) -> None:
    """Set the global profiler instance.

    Args:
        profiler: PerformanceProfiler instance or None to disable
    """
    global _global_profiler
    _global_profiler = profiler


@contextmanager
def profile(operation_name: str):
    """Convenience function for profiling with the global profiler.

    Args:
        operation_name: Name of the operation being profiled

    Yields:
        None

    Example:
        from core.performance_profiler import profile

        with profile("my_operation"):
            do_something()
    """
    profiler = get_global_profiler()
    with profiler.profile(operation_name):
        yield
