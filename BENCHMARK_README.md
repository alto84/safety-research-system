# Parallel Execution Benchmark

## Overview

This benchmark suite compares sequential vs. parallel execution performance for task processing. It uses stub implementations with simulated API latency (via `time.sleep()`) to demonstrate the benefits of parallelization without requiring actual LLM calls.

## Files

- **`benchmark_parallel_execution.py`** - Main benchmark script
- **`test_benchmark_components.py`** - Component validation tests
- **`BENCHMARK_README.md`** - This documentation file

## Quick Start

### Run the Full Benchmark Suite

```bash
# Method 1: Run with Python
python benchmark_parallel_execution.py

# Method 2: Run as executable
./benchmark_parallel_execution.py
```

### Run Component Tests

```bash
python test_benchmark_components.py
```

## What Does It Test?

The benchmark tests the following scenarios:

### Task Counts
- **1 task** - Baseline to measure overhead
- **2 tasks** - Minimum for parallel benefit
- **3 tasks** - Sweet spot for parallelization
- **4 tasks** - Maximum concurrent with default settings

### Latency Scenarios
- **Fast Tasks (0.5s)** - Simulates lightweight LLM calls
- **Slow Tasks (1.0s)** - Simulates complex reasoning tasks

## Output Format

The benchmark produces three main outputs:

### 1. Summary Tables by Scenario

```
SUMMARY TABLE: Fast Tasks (0.5s latency)
================================================================
Tasks    | Sequential     | Parallel       | Speedup      | Efficiency
----------------------------------------------------------------
1        |      0.500s    |      0.504s    |     0.99x     |      99.4%
2        |      1.001s    |      0.502s    |     1.99x     |      99.6%
3        |      1.502s    |      0.502s    |     2.99x     |      99.6%
4        |      2.002s    |      0.503s    |     3.98x     |      99.6%
================================================================
```

### 2. Overall Summary & Insights

Provides key findings including:
- Single task overhead analysis
- Maximum speedup achieved
- Average parallel efficiency
- Optimization recommendations
- Decision guide for when to use parallel execution

### 3. Detailed Performance Profiling

Shows granular timing data using the `PerformanceProfiler`:

```
PERFORMANCE PROFILING SUMMARY
================================================================
Operation                    |    Count |        Total |         Mean
----------------------------------------------------------------
comparison_4tasks_sequential |        2 |       6.005s |       3.002s
comparison_4tasks_parallel   |        2 |       1.505s |     752.70ms
...
================================================================
```

## Understanding the Metrics

### Speedup Ratio

```
Speedup = Sequential Time / Parallel Time
```

- **1.0x** - No improvement (parallel overhead equals sequential)
- **2.0x** - 2 tasks complete in same time as 1 sequential task
- **4.0x** - Ideal parallelization for 4 tasks

### Efficiency Percentage

```
Efficiency = (Speedup / Task Count) × 100%
```

- **100%** - Perfect parallelization, no overhead
- **90-99%** - Excellent parallelization, minimal overhead
- **<90%** - Some overhead present, but still beneficial

## Key Findings (Typical Results)

### 1. Single Task Overhead
- Parallel execution adds ~2-5ms overhead for single tasks
- **Recommendation:** Use sequential execution for single tasks

### 2. Multi-Task Performance
- 2 tasks: ~2.0x speedup (100% efficiency)
- 3 tasks: ~3.0x speedup (100% efficiency)
- 4 tasks: ~4.0x speedup (100% efficiency)
- **Recommendation:** Always use parallel execution for 2+ tasks

### 3. Optimal Configuration
- Maximum benefit with 3-4 concurrent tasks
- ThreadPoolExecutor with 4 workers is optimal
- Additional workers may not improve performance

## Using the Custom Benchmark Function

You can run custom benchmarks with specific parameters:

```python
from benchmark_parallel_execution import run_custom_benchmark

# Run custom benchmark
result = run_custom_benchmark(
    task_count=5,
    latency=0.75,
    max_workers=4
)

print(f"Speedup: {result.speedup:.2f}x")
print(f"Time saved: {result.sequential_time - result.parallel_time:.3f}s")
```

## API Reference

### StubTaskExecutor

Simulates task execution with configurable latency.

```python
executor = StubTaskExecutor(task_latency=1.0)

# Sequential execution
seq_result = executor.execute_sequential(tasks)

# Parallel execution
par_result = executor.execute_parallel(tasks, max_workers=4)
```

### BenchmarkResult

Contains results from a single benchmark run.

**Attributes:**
- `task_count` - Number of tasks executed
- `execution_mode` - 'sequential' or 'parallel'
- `total_time` - Total wall-clock time in seconds
- `task_type` - 'fast' or 'slow'
- `individual_task_times` - List of individual task times
- `avg_task_time` - Average time per task (property)

### ComparisonResult

Comparison between sequential and parallel execution.

**Attributes:**
- `task_count` - Number of tasks
- `task_type` - Task scenario type
- `sequential_time` - Sequential execution time
- `parallel_time` - Parallel execution time
- `speedup` - Speedup ratio
- `efficiency` - Efficiency percentage

## Architecture

### Sequential Execution Flow

```
Task 1 → Task 2 → Task 3 → Task 4
|        |        |        |
0.5s     0.5s     0.5s     0.5s
Total: 2.0s
```

### Parallel Execution Flow

```
Task 1 ┐
Task 2 ├→ All complete in parallel
Task 3 │
Task 4 ┘
Total: ~0.5s (+ minimal overhead)
```

## Integration with Safety Research System

This benchmark demonstrates the potential performance improvements for:

1. **Multi-task Cases** - When orchestrator processes multiple tasks
2. **Batch Operations** - When multiple cases need processing
3. **Audit Parallel Checks** - Multiple auditors running simultaneously
4. **Data Source Queries** - Parallel API calls to external services

## Performance Profiler Integration

The benchmark uses the system's `PerformanceProfiler` class:

```python
from core.performance_profiler import PerformanceProfiler

profiler = PerformanceProfiler()

with profiler.profile("operation_name"):
    # Your code here
    pass

profiler.print_summary()
```

## Recommendations for Production

Based on benchmark results:

### When to Use Sequential Execution
- Single task execution
- Tasks with heavy CPU computation (limited by GIL)
- When overhead of thread management exceeds benefits

### When to Use Parallel Execution
- 2+ independent tasks
- I/O-bound operations (API calls, database queries)
- Tasks with network latency (LLM API calls)

### Optimal Settings
- **ThreadPool Workers:** 3-4 for typical workloads
- **Batch Size:** Group 2-4 tasks per parallel batch
- **Timeout:** Set appropriate timeouts for task execution

## Extending the Benchmark

### Add New Scenarios

```python
def test_custom_scenario():
    executor = StubTaskExecutor(task_latency=2.0)
    tasks = [{"data": f"task_{i}"} for i in range(10)]

    seq_result = executor.execute_sequential(tasks)
    par_result = executor.execute_parallel(tasks, max_workers=8)

    # Compare results...
```

### Test with Real Workers

Replace `StubTaskExecutor` with actual task execution logic:

```python
from core.task_executor import TaskExecutor

# Use real task executor instead of stub
real_executor = TaskExecutor()
```

## Troubleshooting

### Issue: Parallel execution slower than sequential

**Possible causes:**
- Task latency too low (overhead dominates)
- Too many workers (thread switching overhead)
- CPU-bound tasks (Python GIL limitation)

**Solution:**
- Increase task latency (only beneficial for I/O-bound)
- Reduce worker count to 2-4
- Use multiprocessing for CPU-bound tasks

### Issue: Inconsistent results

**Possible causes:**
- System load variations
- Thread scheduling differences
- Python GC pauses

**Solution:**
- Run multiple iterations and average
- Run on idle system
- Increase task latency to reduce timing variance

## References

- **Performance Profiler:** `/home/user/safety-research-system/core/performance_profiler.py`
- **Task Executor:** `/home/user/safety-research-system/core/task_executor.py`
- **Orchestrator:** `/home/user/safety-research-system/agents/orchestrator.py`

## License

Part of the Safety Research System. See main repository LICENSE for details.
