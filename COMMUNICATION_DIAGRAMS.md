# Safety Research System: Communication Architecture Diagrams

## 1. High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                              │
│                     (orchestrator.py)                             │
│                                                                  │
│  process_case()                                                  │
│    ├─ Decompose case into tasks                                 │
│    ├─ For each task:                                            │
│    │   ├─ Call ResolutionEngine.execute_with_validation()      │
│    │   ├─ Compress result                                       │
│    │   └─ Store in task_summaries (thread-safe)               │
│    └─ Synthesize final report from summaries                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                           │ Direct call
                           │ (blocking)
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                   RESOLUTION ENGINE                               │
│                (resolution_engine.py)                            │
│                                                                  │
│  execute_with_validation(task)                                  │
│    LOOP:                                                         │
│      ├─ Call TaskExecutor.execute_task(task)                   │
│      │  └─ task.output_data = result                           │
│      ├─ Call AuditEngine.audit_task(task)                      │
│      │  └─ task.audit_history += audit_result                 │
│      ├─ Call _evaluate_audit_result(task, audit_result)       │
│      │  └─ Decision: ACCEPT|RETRY|ESCALATE|ABORT             │
│      └─ If RETRY:                                              │
│         ├─ Prepare corrections                                 │
│         ├─ task.input_data["corrections"] = corrections       │
│         └─ Loop back to TaskExecutor                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
        │                              │
        │ Direct call                  │ Direct call
        │ (blocking)                   │ (blocking)
        ↓                              ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│   TASK EXECUTOR              │  │   AUDIT ENGINE               │
│  (task_executor.py)         │  │  (audit_engine.py)          │
│                              │  │                              │
│ execute_task(task)          │  │ audit_task(task)             │
│  ├─ Route: TaskType→Worker  │  │  ├─ Route: TaskType→Auditor │
│  │  (or LLM intelligent)    │  │  └─ auditor.validate(...)   │
│  ├─ worker.execute(...)     │  │     └─ Returns AuditResult   │
│  └─ task.output_data=result │  │                              │
│                              │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘
        │                                      │
        │ Direct call                          │ Direct call
        │ (blocking)                           │ (blocking)
        ↓                                      ↓
┌──────────────────────────────┐  ┌──────────────────────────────┐
│     WORKER AGENTS            │  │    AUDITOR AGENTS            │
│  (LiteratureAgent, etc)      │  │  (LiteratureAuditor, etc)   │
│                              │  │                              │
│ execute(input_data)          │  │ validate(input, output, meta)│
│  └─ Returns dict with result │  │  ├─ Hard-coded checks       │
│                              │  │  ├─ LLM semantic checks     │
│                              │  │  └─ Returns validation_out  │
│                              │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘
```

## 2. Detailed Task Execution Flow (Sequence Diagram)

```
Orchestrator          ResolutionEngine      TaskExecutor         AuditEngine         Worker              Auditor
    │                      │                    │                    │                │                   │
    │ execute_with_val()   │                    │                    │                │                   │
    ├─────────────────────>│                    │                    │                │                   │
    │(blocking)            │                    │                    │                │                   │
    │                      │ execute_task()     │                    │                │                   │
    │                      ├───────────────────>│                    │                │                   │
    │                      │                    │ execute(input)     │                │                   │
    │                      │                    ├───────────────────>│                │                   │
    │                      │                    │                    │ [Process task]                    │
    │                      │                    │<───────── output ──┤                │                   │
    │                      │<──── output_data ──┤                    │                │                   │
    │                      │                    │                    │                │                   │
    │                      │                    │                    │ audit_task()   │                   │
    │                      │                    │                    ├───────────────>│                   │
    │                      │                    │                    │                │ validate(...)    │
    │                      │                    │                    │                ├──────────────────>│
    │                      │                    │                    │                │                   │
    │                      │                    │                    │                │  [Validate]      │
    │                      │                    │                    │                │  [Find issues]   │
    │                      │                    │                    │                │  [Rate checks]   │
    │                      │                    │                    │                │  [LLM analysis]  │
    │                      │                    │                    │<───────────────── result ──────────┤
    │                      │                    │<──── audit_result ─┤                │                   │
    │                      │                    │                    │                │                   │
    │                      │ _evaluate_audit_result()                │                │                   │
    │                      │(decision: ACCEPT|RETRY|ESCALATE|ABORT)  │                │                   │
    │                      │                    │                    │                │                   │
    │                      │ IF RETRY:          │                    │                │                   │
    │                      │  prepare_corrections()                  │                │                   │
    │                      │  task.input_data["corrections"]=...     │                │                   │
    │                      │  LOOP BACK TO execute_task()            │                │                   │
    │                      │                    │                    │                │                   │
    │<─── (decision, audit_result) ────────────┤                    │                │                   │
    │ (blocking ends)      │                    │                    │                │                   │
    │                      │                    │                    │                │                   │
```

## 3. Data Structure Flow

```
INPUT:
┌─────────────────────────────┐
│       Case Object           │
├─────────────────────────────┤
│ case_id: str                │
│ question: str               │
│ context: dict               │
│ data_sources: list[str]     │
│ status: CaseStatus          │
│ findings: dict              │
│ final_report: dict          │
└─────────────────────────────┘
          │
          ↓ Decompose
┌─────────────────────────────┐
│    Task[] (one per phase)   │
├─────────────────────────────┤
│ task_id: str                │
│ task_type: TaskType         │
│ case_id: str                │
│ input_data: dict            │
│  ├─ query                   │
│  ├─ context                 │
│  ├─ data_sources            │
│  ├─ corrections (on retry)  │
│  ├─ previous_output (...)   │
│  └─ audit_feedback (...)    │
│ output_data: dict (empty)   │
│ status: TaskStatus          │
│ retry_count: int            │
│ max_retries: int            │
│ audit_history: list         │
└─────────────────────────────┘
          │
          ├─────────────┬──────────────┐
          │             │              │
          ↓             ↓              ↓
   [Execute]    [Audit]       [Resolve]
    (Worker)   (Auditor)     (Decision)
          │             │              │
          └─────────────┼──────────────┘
                        │
                        ↓
┌──────────────────────────────────────┐
│ Task (after loop completion)         │
├──────────────────────────────────────┤
│ output_data: {                       │
│   result: {...},                     │
│   execution_time: float,             │
│   agent: str                         │
│ }                                    │
│ audit_history: [AuditResult, ...]   │
│ status: COMPLETED|FAILED|...         │
│ metadata: {escalation flags, etc}    │
└──────────────────────────────────────┘
          │
          ↓ Compress
┌──────────────────────────────────────┐
│ Compressed Summary                   │
├──────────────────────────────────────┤
│ summary: str (1-2 sentences)         │
│ key_findings: dict (3-5 points)      │
│ metadata: {escalation, etc}          │
└──────────────────────────────────────┘
          │
          ↓ Store in Orchestrator
┌──────────────────────────────────────┐
│ task_summaries[case_id][task_id]     │
│  = compressed_summary                │
└──────────────────────────────────────┘
          │
          ↓ Synthesize
┌──────────────────────────────────────┐
│       Final Report                   │
├──────────────────────────────────────┤
│ case_id: str                         │
│ title: str                           │
│ executive_summary: str               │
│ findings_by_task: dict               │
│ overall_assessment: str              │
│ recommendations: list[str]           │
│ confidence_level: str                │
│ metadata: {...}                      │
└──────────────────────────────────────┘
```

## 4. Resolution Loop State Machine

```
                    ┌─────────────────┐
                    │   PENDING       │
                    └────────┬────────┘
                             │ task created
                             ↓
                    ┌─────────────────┐
                    │   DECOMPOSED    │
                    └────────┬────────┘
                             │
                             ↓
                    ┌─────────────────┐
    ┌───────────────│   IN_PROGRESS   │◄──────────────────┐
    │               └────────┬────────┘                   │
    │                        │ worker executes           │
    │                        ↓                           │
    │               ┌─────────────────┐                  │
    │               │   AUDITING      │                  │
    │               └────────┬────────┘                  │
    │                        │ audit completes          │
    │                        ↓                           │
    │               ┌─────────────────┐                  │
    │               │   EVAL AUDIT    │                  │
    │               └────────┬────────┘                  │
    │                        │                           │
    │    ┌───────────────────┼───────────────────┐       │
    │    │                   │                   │       │
    │  RETRY         ACCEPT / ESCALATE         ABORT     │
    │    │                   │                   │       │
    │    │                   ↓                   │       │
    │    │          ┌─────────────────┐         │       │
    │    │          │  COMPLETED      │         │       │
    │    │          └─────────────────┘         │       │
    │    │                                      │       │
    │    │                                      ↓       │
    │    │          ┌─────────────────┐        │        │
    │    │          │  AUDIT_FAILED   │◄───────┘       │
    │    │          │ (escalate)      │                 │
    │    │          └─────────────────┘                 │
    │    │                                              │
    │    │          ┌─────────────────┐                │
    │    └─────────>│ REQUIRES_REVISION│                │
    │              │ (retry needed)   │                │
    │              └────────┬────────┘                 │
    │                       │ increment retry_count    │
    │                       │ prepare_corrections()    │
    │                       └──────────────────────────┘
    │
    └─ No more retries available
       ↓
      ┌─────────────────┐
      │  FAILED         │
      │ (abort)         │
      └─────────────────┘
```

## 5. Parallel Execution Timing

```
Orchestrator Timeline:
┌────────────────────────────────────────────────────────────────┐
│ process_case()                                                 │
│                                                                │
│ ├─ _decompose_case()                      [~10ms]             │
│ │                                                              │
│ ├─ ThreadPoolExecutor(max_workers=10)                         │
│ │                                                              │
│ │  Task1:                                                     │
│ │  ├─ _execute_task_with_validation()    [~45s] ─┐           │
│ │  │                                               │           │
│ │  Task2:                                         │           │
│ │  ├─ _execute_task_with_validation()   [~30s] ──┤ PARALLEL  │
│ │  │                                              │           │
│ │  Task3:                                         │           │
│ │  └─ _execute_task_with_validation()   [~25s] ──┘           │
│ │                                                              │
│ ├─ Wait for all futures (as_completed)          [~45s total]  │
│ │                                                              │
│ ├─ _synthesize_final_report()                    [~100ms]     │
│ │                                                              │
│ └─ TOTAL TIME: ~45 seconds (max of parallel tasks)            │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Worker Thread Timeline (Task1):
┌────────────────────────────────────────────────┐
│ _execute_task_with_validation(case, task1)     │
│                                                │
│ ├─ ResolutionEngine.execute_with_validation() │
│ │                                              │
│ │  ATTEMPT 1:                                  │
│ │  ├─ TaskExecutor.execute_task()  [~30s]     │
│ │  ├─ AuditEngine.audit_task()      [~8s]     │
│ │  └─ _evaluate_audit_result()      [~2s]     │
│ │     → Decision: RETRY                       │
│ │                                              │
│ │  ATTEMPT 2:                                  │
│ │  ├─ TaskExecutor.execute_task()  [~30s]     │
│ │  ├─ AuditEngine.audit_task()      [~5s]     │
│ │  └─ _evaluate_audit_result()      [~1s]     │
│ │     → Decision: ACCEPT                      │
│ │                                              │
│ ├─ ContextCompressor.compress_result() [<1s]  │
│ ├─ task_summaries lock acquire                │
│ ├─ task_summaries[case_id][task_id] = compressed │
│ ├─ case.add_finding()                         │
│ └─ task_summaries lock release                │
│                                                │
│ TOTAL: ~45 seconds                            │
│                                                │
└────────────────────────────────────────────────┘
```

## 6. Message/Call Types Between Components

```
Orchestrator → ResolutionEngine
├─ Method: resolution_engine.execute_with_validation(task)
├─ Input: Task (modified in-place as side effect)
├─ Output: (ResolutionDecision, AuditResult)
├─ Blocking: YES (until loop completes)
└─ Return: Tuple with decision and audit result

ResolutionEngine → TaskExecutor
├─ Method: task_executor.execute_task(task)
├─ Input: Task (modified in-place)
├─ Output: Dict with result
├─ Blocking: YES (until worker completes)
└─ Side effect: task.output_data populated

TaskExecutor → Worker
├─ Method: worker.execute(input_data)
├─ Input: Dict with {query, context, data_sources, [corrections, ...]}
├─ Output: Dict with {result, confidence, sources, methodology, limitations}
├─ Blocking: YES (until worker returns)
└─ No side effects on input dict

ResolutionEngine → AuditEngine
├─ Method: audit_engine.audit_task(task)
├─ Input: Task (must have output_data populated)
├─ Output: AuditResult object
├─ Blocking: YES (until auditor returns)
└─ Side effect: Audit result added to audit_history

AuditEngine → Auditor
├─ Method: auditor.validate(task_input, task_output, task_metadata)
├─ Input: 3 dicts
├─ Output: Dict with {status, summary, issues[], passed_checks[], ...}
├─ Blocking: YES (until auditor returns)
└─ No side effects on inputs

ResolutionEngine → LLM (via ThoughtPipeExecutor)
├─ Method: thought_pipe.execute_thought_pipe(prompt, context, validation_fn, max_retries)
├─ Input: Prompt string, context dict
├─ Output: Response dict
├─ Blocking: YES (2-10 seconds, network I/O)
└─ Side effect: Response cached for future use
```

## 7. Coupling Dependencies (What breaks if X changes)

```
If Worker interface changes (e.g., returns different dict structure):
├─ TaskExecutor.execute_task() breaks
├─ ResolutionEngine (expects specific fields in task.output_data)
├─ AuditEngine (validates task.output_data)
└─ Orchestrator (accesses output_data in compression)
   Impact: 4 components affected

If Task.input_data structure changes (e.g., rename "query" to "question"):
├─ Worker.execute() breaks (looks for "query")
├─ Feedback loop breaks (ResolutionEngine expects "corrections" field)
├─ AuditEngine.audit_task() breaks (passes input_data)
└─ Orchestrator (creates input_data in decomposition)
   Impact: 5 components affected

If AuditResult structure changes:
├─ ResolutionEngine._evaluate_audit_result() breaks
├─ Orchestrator.compress_task_result() breaks
├─ AuditEngine._process_validation_output() breaks
└─ Orchestrator.print_performance_summary() breaks
   Impact: 4 components affected

If LLM API interface changes:
├─ ResolutionEngine._evaluate_audit_result_intelligent() breaks
├─ TaskExecutor._intelligent_route_task() breaks
├─ BaseAuditor._check_semantic_violations() breaks
└─ LiteratureAgent (if uses intelligent evidence assessment)
   Impact: 4 components affected, but with fallback to hard-coded
```

## 8. Async Message Queue Architecture (Proposed)

```
                        ┌──────────────────┐
                        │   Orchestrator   │
                        └────────┬─────────┘
                                 │ publishes
                                 ↓
                     ┌───────────────────────┐
                     │   task_queue          │
                     │  (RabbitMQ/Kafka)     │
                     │  [TaskMessage]        │
                     └───────────┬───────────┘
                                 │ consumes
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Worker 1   │ │  Worker 2   │ │  Worker N   │
            │ (on Pod 1)  │ │ (on Pod 2)  │ │ (on Pod N)  │
            └────────┬────┘ └────────┬────┘ └────────┬────┘
                     │ publishes      │ publishes     │ publishes
                     ↓                ↓               ↓
                     └───────────┬────────────────────┘
                                 │
                     ┌───────────────────────┐
                     │   audit_queue         │
                     │  (RabbitMQ/Kafka)     │
                     │ [AuditMessage]        │
                     └───────────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  Auditor 1  │ │  Auditor 2  │ │  Auditor N  │
            │ (on Pod 1)  │ │ (on Pod 2)  │ │ (on Pod N)  │
            └────────┬────┘ └────────┬────┘ └────────┬────┘
                     │ publishes      │ publishes     │ publishes
                     ↓                ↓               ↓
                     └───────────┬────────────────────┘
                                 │
                     ┌───────────────────────┐
                     │ resolution_queue      │
                     │ (RabbitMQ/Kafka)      │
                     │ [ResolutionMessage]   │
                     └───────────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    ↓            ↓            ↓
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │Resolution 1 │ │Resolution 2 │ │Resolution N │
            │ (Engine)    │ │ (Engine)    │ │ (Engine)    │
            └────────┬────┘ └────────┬────┘ └────────┬────┘
                     │                │                │
                     │ IF RETRY:      │ IF RETRY:      │
                     │ republish to   │ republish to   │
                     │ task_queue     │ task_queue     │
                     │                │                │
                     └───────────┬────────────────────┘
                                 │ IF ACCEPT/ESCALATE/ABORT
                                 ↓
                     ┌───────────────────────┐
                     │   results_queue       │
                     │  (RabbitMQ/Kafka)     │
                     │ [ResultMessage]       │
                     └───────────┬───────────┘
                                 │
                                 ↓
                        ┌──────────────────┐
                        │   Orchestrator   │
                        │ (subscribes to   │
                        │  results_queue)  │
                        └──────────────────┘

Benefits:
├─ Decoupled execution (components don't call each other)
├─ Horizontal scaling (100s of workers on Kubernetes)
├─ Message persistence (can retry if service fails)
├─ Better latency (pipeline parallelism)
├─ Load balancing (queues balance work across workers)
└─ Observability (can monitor queue depth, throughput, etc)
```

---

## Summary

The current system uses **tightly-coupled, synchronous method calls** throughout. This works well for:
- Development and testing
- Single-machine deployments
- Simple sequential workflows

The proposed async messaging architecture would support:
- Multi-machine deployments
- Horizontal scaling
- Better fault tolerance
- Parallel pipeline processing
