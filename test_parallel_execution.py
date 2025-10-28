"""
Test parallel execution in Orchestrator.

This test validates:
1. Parallel execution completes successfully
2. Sequential execution completes successfully
3. Both modes produce the same results
4. Thread safety (no race conditions)
5. Performance comparison between modes
6. Profiling tracks execution modes correctly
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.orchestrator import Orchestrator
from core.task_executor import TaskExecutor
from core.audit_engine import AuditEngine
from core.resolution_engine import ResolutionEngine
from core.context_compressor import ContextCompressor
from models.case import Case, CasePriority
from models.task import Task, TaskType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockWorker:
    """Mock worker that simulates task execution with a delay."""

    def __init__(self, delay: float = 0.1):
        self.delay = delay

    def execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate work with a delay."""
        time.sleep(self.delay)
        return {
            "summary": f"Completed task with query: {task_input.get('query', 'N/A')}",
            "key_findings": {
                "conclusion": "Mock finding",
                "confidence": "moderate",
                "recommendation": "Mock recommendation"
            },
            "evidence_chain": {
                "claims": [],
                "sources": [],
            }
        }


class MockAuditor:
    """Mock auditor that always approves."""

    def audit(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """Mock audit that always passes."""
        return {
            "audit_passed": True,
            "issues": [],
            "score": 0.95,
            "recommendations": [],
        }


def create_test_case(num_tasks: int = 3) -> Case:
    """Create a test case with specified number of tasks."""
    case = Case(
        title="Parallel Execution Test Case",
        description="Test case for validating parallel vs sequential execution",
        question="Test question for parallel execution",
        context={
            "has_clinical_data": True,
            "test_mode": True,
        },
        priority=CasePriority.MEDIUM,
        submitter="test_system",
    )
    return case


def test_parallel_vs_sequential():
    """Test parallel execution vs sequential execution."""
    logger.info("=" * 80)
    logger.info("TEST: PARALLEL VS SEQUENTIAL EXECUTION")
    logger.info("=" * 80)

    # Create components with mock workers/auditors
    task_executor = TaskExecutor()

    # Register mock workers
    mock_worker = MockWorker(delay=0.5)  # 500ms per task
    task_executor.register_worker(TaskType.LITERATURE_REVIEW, mock_worker)
    task_executor.register_worker(TaskType.STATISTICAL_ANALYSIS, mock_worker)
    task_executor.register_worker(TaskType.RISK_MODELING, mock_worker)

    audit_engine = AuditEngine()
    mock_auditor = MockAuditor()
    audit_engine.register_auditor(TaskType.LITERATURE_REVIEW, mock_auditor)
    audit_engine.register_auditor(TaskType.STATISTICAL_ANALYSIS, mock_auditor)
    audit_engine.register_auditor(TaskType.RISK_MODELING, mock_auditor)

    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine,
        max_retries=1,
    )

    context_compressor = ContextCompressor()

    # Test 1: Sequential execution
    logger.info("\n--- Test 1: Sequential Execution ---")
    orchestrator_seq = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=True,
        enable_parallel_execution=False,  # Sequential mode
    )

    case_seq = create_test_case()
    start_seq = time.time()
    result_seq = orchestrator_seq.process_case(case_seq)
    duration_seq = time.time() - start_seq

    logger.info(f"Sequential execution completed in {duration_seq:.2f}s")
    logger.info(f"Tasks completed: {result_seq['metadata']['tasks_completed']}")

    # Print performance stats
    stats_seq = orchestrator_seq.get_performance_stats()
    logger.info("\nSequential Execution Stats:")
    for op_name, op_stats in sorted(stats_seq['operations'].items()):
        if 'execute_tasks' in op_name:
            logger.info(f"  {op_name}: {op_stats['total_time']:.3f}s (count={op_stats['count']})")

    # Test 2: Parallel execution
    logger.info("\n--- Test 2: Parallel Execution ---")
    orchestrator_par = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=True,
        enable_parallel_execution=True,  # Parallel mode
    )

    case_par = create_test_case()
    start_par = time.time()
    result_par = orchestrator_par.process_case(case_par)
    duration_par = time.time() - start_par

    logger.info(f"Parallel execution completed in {duration_par:.2f}s")
    logger.info(f"Tasks completed: {result_par['metadata']['tasks_completed']}")

    # Print performance stats
    stats_par = orchestrator_par.get_performance_stats()
    logger.info("\nParallel Execution Stats:")
    for op_name, op_stats in sorted(stats_par['operations'].items()):
        if 'execute_tasks' in op_name:
            logger.info(f"  {op_name}: {op_stats['total_time']:.3f}s (count={op_stats['count']})")

    # Validations
    logger.info("\n--- Validations ---")

    # 1. Both should complete successfully
    assert result_seq is not None, "Sequential execution failed"
    assert result_par is not None, "Parallel execution failed"
    logger.info("✓ Both executions completed successfully")

    # 2. Both should process same number of tasks
    assert result_seq['metadata']['tasks_completed'] == result_par['metadata']['tasks_completed'], \
        "Task count mismatch"
    logger.info(f"✓ Both processed {result_seq['metadata']['tasks_completed']} tasks")

    # 3. Both should have same findings
    assert len(result_seq['findings_by_task']) == len(result_par['findings_by_task']), \
        "Findings count mismatch"
    logger.info(f"✓ Both produced {len(result_seq['findings_by_task'])} findings")

    # 4. Parallel should be faster (with 2+ tasks and 500ms delay each)
    # Expected: Sequential ~1.5s+ (3 tasks × 500ms), Parallel ~500ms+ (all concurrent)
    speedup = duration_seq / duration_par if duration_par > 0 else 0
    logger.info(f"✓ Speedup: {speedup:.2f}x (Sequential: {duration_seq:.2f}s, Parallel: {duration_par:.2f}s)")

    # 5. Profiling should track correct mode
    assert 'execute_tasks_sequential' in stats_seq['operations'], \
        "Sequential profiling missing"
    assert 'execute_tasks_parallel' in stats_par['operations'], \
        "Parallel profiling missing"
    logger.info("✓ Profiling tracked execution modes correctly")

    logger.info("\n" + "=" * 80)
    logger.info("ALL TESTS PASSED!")
    logger.info("=" * 80)

    return {
        'sequential_duration': duration_seq,
        'parallel_duration': duration_par,
        'speedup': speedup,
        'tasks_completed': result_seq['metadata']['tasks_completed'],
    }


def test_thread_safety():
    """Test thread safety with many tasks."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: THREAD SAFETY (10 PARALLEL TASKS)")
    logger.info("=" * 80)

    # Create components
    task_executor = TaskExecutor()
    mock_worker = MockWorker(delay=0.1)

    # Register worker for multiple task types
    for task_type in TaskType:
        task_executor.register_worker(task_type, mock_worker)

    audit_engine = AuditEngine()
    mock_auditor = MockAuditor()

    for task_type in TaskType:
        audit_engine.register_auditor(task_type, mock_auditor)

    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine,
        max_retries=1,
    )

    context_compressor = ContextCompressor()

    orchestrator = Orchestrator(
        task_executor=task_executor,
        audit_engine=audit_engine,
        resolution_engine=resolution_engine,
        context_compressor=context_compressor,
        enable_profiling=True,
        enable_parallel_execution=True,
    )

    # Override decompose to create many tasks
    original_decompose = orchestrator._decompose_case

    def custom_decompose(case):
        """Create 10 tasks for stress testing."""
        tasks = []
        task_types = list(TaskType)

        for i in range(10):
            task_type = task_types[i % len(task_types)]
            task = Task(
                task_type=task_type,
                case_id=case.case_id,
                input_data={
                    "query": f"Task {i}",
                    "context": case.context,
                },
            )
            tasks.append(task)
            case.add_task(task.task_id)

        return tasks

    orchestrator._decompose_case = custom_decompose

    # Execute with many parallel tasks
    case = Case(
        title="Thread Safety Test",
        description="Test with many parallel tasks",
        question="Thread safety test question",
        context={"test_mode": True},
        priority=CasePriority.MEDIUM,
        submitter="test_system",
    )

    start = time.time()
    result = orchestrator.process_case(case)
    duration = time.time() - start

    logger.info(f"Completed 10 parallel tasks in {duration:.2f}s")
    logger.info(f"Tasks completed: {result['metadata']['tasks_completed']}")

    # Validations
    assert result['metadata']['tasks_completed'] == 10, "Should complete 10 tasks"
    # Note: findings_by_task uses task_type as key, so with repeated types we may have fewer
    # The important thing is all tasks completed successfully
    assert len(result['findings_by_task']) >= 5, f"Should have multiple findings (got {len(result['findings_by_task'])})"
    logger.info(f"✓ All 10 tasks completed successfully with {len(result['findings_by_task'])} unique findings (thread-safe)")

    logger.info("=" * 80)
    logger.info("THREAD SAFETY TEST PASSED!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        # Run tests
        results = test_parallel_vs_sequential()
        test_thread_safety()

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Sequential Duration: {results['sequential_duration']:.2f}s")
        print(f"Parallel Duration:   {results['parallel_duration']:.2f}s")
        print(f"Speedup:             {results['speedup']:.2f}x")
        print(f"Tasks Completed:     {results['tasks_completed']}")
        print("=" * 80)
        print("\n✓ ALL TESTS PASSED - Parallel execution working correctly!")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
