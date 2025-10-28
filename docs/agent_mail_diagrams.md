# Agent Mail System - Visual Diagrams

## Message Flow Diagrams

### 1. Task Assignment Flow (Agent-Audit-Resolve Pattern)

```
┌─────────────┐                                           ┌──────────────┐
│ Orchestrator│                                           │  Agent Mail  │
│             │                                           │   Mailbox    │
└──────┬──────┘                                           └───────┬──────┘
       │                                                          │
       │ 1. Create Task                                          │
       │────────────────────────────────────────────────────────>│
       │    MessageType: TASK_ASSIGNMENT                         │
       │    To: literature_worker_001                            │
       │    Body: {task_id, query, data_sources}                 │
       │    CorrelationID: case_abc123                           │
       │                                                          │
       │                                           ┌──────────────┴────────────┐
       │                                           │  Routes to worker mailbox │
       │                                           └──────────────┬────────────┘
       │                                                          │
       │                                           ┌──────────────▼────────────┐
       │                                           │   Literature Worker       │
       │                                           │   - Receives message      │
       │                                           │   - Executes task         │
       │                                           │   - Generates output      │
       │                                           └──────────────┬────────────┘
       │                                                          │
       │ 2. Task Result                                          │
       │<────────────────────────────────────────────────────────│
       │    MessageType: TASK_RESULT                             │
       │    From: literature_worker_001                          │
       │    Body: {task_id, output}                              │
       │    CorrelationID: case_abc123                           │
       │                                                          │
       │ 3. Audit Request                                        │
       │────────────────────────────────────────────────────────>│
       │    MessageType: AUDIT_REQUEST                           │
       │    To: literature_auditor_001                           │
       │    Body: {task_id, input, output}                       │
       │                                                          │
       │                                           ┌──────────────▼────────────┐
       │                                           │   Literature Auditor      │
       │                                           │   - Validates output      │
       │                                           │   - Checks compliance     │
       │                                           │   - Generates issues      │
       │                                           └──────────────┬────────────┘
       │                                                          │
       │ 4. Audit Result                                         │
       │<────────────────────────────────────────────────────────│
       │    MessageType: AUDIT_RESULT                            │
       │    From: literature_auditor_001                         │
       │    Body: {status, issues, recommendations}              │
       │                                                          │
       │ 5a. If FAILED → Correction Request                      │
       │────────────────────────────────────────────────────────>│
       │    MessageType: CORRECTION_REQUEST                      │
       │    To: literature_worker_001                            │
       │    Body: {corrections, previous_output}                 │
       │    [Loop back to step 1]                                │
       │                                                          │
       │ 5b. If CRITICAL → Human Review                          │
       │────────────────────────────────────────────────────────>│
       │    MessageType: HUMAN_REVIEW                            │
       │    To: human_reviewer                                   │
       │    Body: {task_id, audit_result, history}               │
       │    RequiresHumanReview: true                            │
       │                                                          │
```

### 2. Pub/Sub Pattern (Status Updates)

```
┌──────────┐                                    ┌──────────────┐
│ Worker 1 │                                    │  Agent Mail  │
└────┬─────┘                                    │   Mailbox    │
     │                                          └───────┬──────┘
     │ Publish to "task_completed"                     │
     │─────────────────────────────────────────────────>│
     │   Topic: "task_completed"                       │
     │   Body: {task_id, status, metrics}              │
     │                                                  │
     │                               ┌──────────────────┴───────────────────┐
     │                               │  Find subscribers to "task_completed"│
     │                               │  - Monitor Dashboard                  │
     │                               │  - Performance Profiler               │
     │                               │  - Audit Logger                       │
     │                               └──────────────────┬───────────────────┘
     │                                                  │
     │                                    ┌─────────────┼─────────────┐
     │                                    │             │             │
     │                                    ▼             ▼             ▼
     │                          ┌──────────────┐ ┌───────────┐ ┌──────────┐
     │                          │   Monitor    │ │ Profiler  │ │  Audit   │
     │                          │  Dashboard   │ │           │ │  Logger  │
     │                          │              │ │           │ │          │
     │                          │ - Updates UI │ │ - Records │ │ - Logs   │
     │                          │ - Shows      │ │   metrics │ │   event  │
     │                          │   progress   │ │           │ │          │
     │                          └──────────────┘ └───────────┘ └──────────┘
     │
```

### 3. Human Review Queue Flow

```
┌──────────┐                    ┌──────────────┐                ┌───────────┐
│ Auditor  │                    │  Agent Mail  │                │   Human   │
│          │                    │   Mailbox    │                │  Reviewer │
└────┬─────┘                    └───────┬──────┘                └─────┬─────┘
     │                                  │                             │
     │ Send message with                │                             │
     │ requires_human_review=True       │                             │
     │─────────────────────────────────>│                             │
     │                                  │                             │
     │                   ┌──────────────▼──────────────┐             │
     │                   │  Route to Human Review Queue│             │
     │                   │  - Priority: CRITICAL       │             │
     │                   │  - Hold for approval        │             │
     │                   └──────────────┬──────────────┘             │
     │                                  │                             │
     │                                  │  Get review queue           │
     │                                  │<────────────────────────────│
     │                                  │                             │
     │                                  │  Return pending messages    │
     │                                  │────────────────────────────>│
     │                                  │                             │
     │                                  │                             │
     │                                  │  Approve message            │
     │                                  │<────────────────────────────│
     │                                  │                             │
     │                   ┌──────────────▼──────────────┐             │
     │                   │  Remove from review queue   │             │
     │                   │  Add metadata:              │             │
     │                   │  - human_approved: true     │             │
     │                   │  - approved_at: timestamp   │             │
     │                   │  Deliver to recipient       │             │
     │                   └──────────────┬──────────────┘             │
     │                                  │                             │
     │<─────────────────────────────────│                             │
     │  Message delivered with approval │                             │
     │                                  │                             │
```

### 4. Message Correlation (Conversation Thread)

```
Message Timeline (correlation_id = "case_abc123"):

T0: [TASK_ASSIGNMENT]
    message_id: msg_001
    correlation_id: case_abc123
    sender: orchestrator → receiver: worker
    ↓
T1: [TASK_RESULT]
    message_id: msg_002
    correlation_id: case_abc123
    reply_to: msg_001
    sender: worker → receiver: orchestrator
    ↓
T2: [AUDIT_REQUEST]
    message_id: msg_003
    correlation_id: case_abc123
    sender: orchestrator → receiver: auditor
    ↓
T3: [AUDIT_RESULT]
    message_id: msg_004
    correlation_id: case_abc123
    reply_to: msg_003
    sender: auditor → receiver: orchestrator
    ↓
T4: [CORRECTION_REQUEST]  (audit failed)
    message_id: msg_005
    correlation_id: case_abc123
    sender: orchestrator → receiver: worker
    ↓
T5: [TASK_RESULT]  (retry)
    message_id: msg_006
    correlation_id: case_abc123
    reply_to: msg_005
    sender: worker → receiver: orchestrator
    ↓
T6: [AUDIT_REQUEST]  (retry)
    message_id: msg_007
    correlation_id: case_abc123
    sender: orchestrator → receiver: auditor
    ↓
T7: [AUDIT_RESULT]  (passed)
    message_id: msg_008
    correlation_id: case_abc123
    reply_to: msg_007
    sender: auditor → receiver: orchestrator

Query: mailbox.get_conversation_thread("msg_003")
Returns: [msg_001, msg_002, msg_003, msg_004, msg_005, msg_006, msg_007, msg_008]
```

## Transport Architecture

### Hybrid Transport (Recommended)

```
┌────────────────────────────────────────────────────────────────┐
│                       HYBRID TRANSPORT                          │
│                                                                 │
│  Fast Path (Read):                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                 InMemory Queues                           │ │
│  │                                                           │ │
│  │  agent_001: [msg1, msg2, msg3] ←── receive() (fast!)    │ │
│  │  agent_002: [msg4, msg5]                                 │ │
│  │  agent_003: [msg6]                                       │ │
│  │                                                           │ │
│  │  Implementation: threading.Queue                         │ │
│  │  Latency: <1ms                                           │ │
│  │  Throughput: >10K msg/sec                                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Durable Path (Write):                                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                 SQLite Database                           │ │
│  │                                                           │ │
│  │  messages table:                                         │ │
│  │  ┌────────────┬──────────┬──────────┬─────────┬─────┐   │ │
│  │  │ message_id │ sender   │ receiver │ subject │ ... │   │ │
│  │  ├────────────┼──────────┼──────────┼─────────┼─────┤   │ │
│  │  │ msg_001    │ worker   │ auditor  │ Review  │ ... │   │ │
│  │  │ msg_002    │ auditor  │ worker   │ Fix     │ ... │   │ │
│  │  └────────────┴──────────┴──────────┴─────────┴─────┘   │ │
│  │                                                           │ │
│  │  Indexes: receiver_id, topic, correlation_id            │ │
│  │  Persistence: Survives restart                          │ │
│  │  Audit trail: Complete history                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  send() flow:                                                   │
│  1. Write to SQLite (durable)                                  │
│  2. Put in memory queue (fast delivery)                        │
│                                                                 │
│  receive() flow:                                                │
│  1. Get from memory queue (fast)                               │
│  2. Update SQLite (mark as read)                               │
│                                                                 │
│  Recovery on restart:                                           │
│  1. Load undelivered messages from SQLite                      │
│  2. Populate memory queues                                     │
└────────────────────────────────────────────────────────────────┘
```

## Component Interactions

### AgentMailbox Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT MAILBOX                            │
│                                                                 │
│  Public API:                                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  send(sender, receiver, type, subject, body)              │ │
│  │  receive(agent_id, timeout, blocking)                     │ │
│  │  publish(sender, topic, type, subject, body)              │ │
│  │  subscribe(agent_id, topic)                               │ │
│  │  register_callback(agent_id, callback_fn)                 │ │
│  │  get_human_review_queue()                                 │ │
│  │  get_message_history(filters)                             │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               MESSAGE ROUTER                              │ │
│  │                                                           │ │
│  │  Route by delivery mode:                                 │ │
│  │  - DIRECT    → Send to specific agent                    │ │
│  │  - BROADCAST → Send to all agents                        │ │
│  │  - TOPIC     → Send to topic subscribers                 │ │
│  │  - ROUND_ROBIN → Load balance (future)                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                │
│         ▼                  ▼                  ▼                │
│  ┌──────────┐       ┌──────────┐      ┌──────────────┐        │
│  │ Transport│       │Subscrip- │      │Human Review  │        │
│  │  Layer   │       │tion Mgr  │      │    Queue     │        │
│  │          │       │          │      │              │        │
│  │ - Memory │       │ Topics:  │      │ Priority     │        │
│  │ - SQLite │       │ {topic:  │      │ Queue:       │        │
│  │ - Hybrid │       │  [agents]│      │ [(priority,  │        │
│  │          │       │  }       │      │   message)]  │        │
│  └──────────┘       └──────────┘      └──────────────┘        │
│         │                  │                  │                │
│         └──────────────────┴──────────────────┘                │
│                            │                                    │
│                            ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │               MESSAGE HISTORY                             │ │
│  │                                                           │ │
│  │  All messages stored for:                                │ │
│  │  - Audit trail                                           │ │
│  │  - Conversation threading                                │ │
│  │  - Debugging                                             │ │
│  │  - Analytics                                             │ │
│  │                                                           │ │
│  │  Query by:                                               │ │
│  │  - agent_id (sender or receiver)                         │ │
│  │  - correlation_id (conversation thread)                  │ │
│  │  - message_type                                          │ │
│  │  - time range                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Threading Model

### Worker Agent with Mail

```
┌─────────────────────────────────────────────────────────┐
│                  WORKER AGENT                           │
│                                                         │
│  Main Thread:                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  worker = LiteratureAgentWithMail(                 │ │
│  │      agent_id="lit_worker_001",                    │ │
│  │      mailbox=mailbox                               │ │
│  │  )                                                  │ │
│  │  worker.start()  # Spawns message loop thread      │ │
│  └────────────────────────────────────────────────────┘ │
│                            │                            │
│                            │ spawn                      │
│                            ▼                            │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Message Loop Thread (daemon):                     │ │
│  │                                                     │ │
│  │  while is_running:                                 │ │
│  │      # Block waiting for message                   │ │
│  │      message = mailbox.receive(                    │ │
│  │          agent_id=self.agent_id,                   │ │
│  │          timeout=1.0,                              │ │
│  │          blocking=True                             │ │
│  │      )                                             │ │
│  │                                                     │ │
│  │      if message:                                   │ │
│  │          # Handle message based on type            │ │
│  │          if TASK_ASSIGNMENT:                       │ │
│  │              ┌──────────────────────────────────┐  │ │
│  │              │ Execute task in current thread │  │ │
│  │              │ - Parse input                   │  │ │
│  │              │ - Run analysis                  │  │ │
│  │              │ - Generate output               │  │ │
│  │              └──────────────────────────────────┘  │ │
│  │                            │                       │ │
│  │                            ▼                       │ │
│  │              ┌──────────────────────────────────┐  │ │
│  │              │ Send TASK_RESULT message        │  │ │
│  │              │ mailbox.reply(...)              │  │ │
│  │              └──────────────────────────────────┘  │ │
│  │                                                     │ │
│  │          elif CORRECTION_REQUEST:                  │ │
│  │              # Handle retry with corrections       │ │
│  └────────────────────────────────────────────────────┘ │
│                                                         │
│  Thread Safety:                                         │
│  - Message loop thread receives messages               │
│  - Mailbox internally uses threading.Lock              │
│  - Queue.get() is thread-safe                          │
│  - No shared mutable state between threads             │
└─────────────────────────────────────────────────────────┘
```

### Orchestrator with Parallel Execution

```
┌────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                              │
│                                                                │
│  Main Thread:                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  orchestrator.process_case(case)                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Decompose case into tasks                               │ │
│  │  tasks = [lit_task, stats_task, risk_task]              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ThreadPoolExecutor (max_workers=10):                    │ │
│  │                                                           │ │
│  │  Thread 1:                Thread 2:          Thread 3:   │ │
│  │  ┌─────────────┐         ┌─────────────┐   ┌──────────┐ │ │
│  │  │ Process     │         │ Process     │   │ Process  │ │ │
│  │  │ lit_task    │         │ stats_task  │   │risk_task │ │ │
│  │  │             │         │             │   │          │ │ │
│  │  │ 1. Send     │         │ 1. Send     │   │1. Send   │ │ │
│  │  │    TASK_    │         │    TASK_    │   │   TASK_  │ │ │
│  │  │    ASSIGN   │         │    ASSIGN   │   │   ASSIGN │ │ │
│  │  │             │         │             │   │          │ │ │
│  │  │ 2. Wait for │         │ 2. Wait for │   │2. Wait   │ │ │
│  │  │    RESULT   │         │    RESULT   │   │   RESULT │ │ │
│  │  │             │         │             │   │          │ │ │
│  │  │ 3. Send     │         │ 3. Send     │   │3. Send   │ │ │
│  │  │    AUDIT_   │         │    AUDIT_   │   │   AUDIT_ │ │ │
│  │  │    REQUEST  │         │    REQUEST  │   │   REQUEST│ │ │
│  │  │             │         │             │   │          │ │ │
│  │  │ 4. Wait for │         │ 4. Wait for │   │4. Wait   │ │ │
│  │  │    AUDIT    │         │    AUDIT    │   │   AUDIT  │ │ │
│  │  │             │         │             │   │          │ │ │
│  │  │ 5. Return   │         │ 5. Return   │   │5. Return │ │ │
│  │  └─────────────┘         └─────────────┘   └──────────┘ │ │
│  │                                                           │ │
│  │  All threads share same AgentMailbox (thread-safe)       │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            │                                   │
│                            ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Collect results from all threads                        │ │
│  │  Synthesize final report                                 │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Data Flow Example

### Complete Case Processing with Agent Mail

```
Case: "Assess Drug X hepatotoxicity risk"

TIMELINE:

T0: Orchestrator creates case
    └─> Decomposes into 3 tasks:
        - Literature Review
        - Statistical Analysis
        - Risk Modeling

T1: Orchestrator (3 parallel threads):

    Thread 1 (Lit Review):
    ┌─────────────────────────────────────────────────────┐
    │ Send TASK_ASSIGNMENT → lit_worker_001               │
    │   correlation_id: case_123                          │
    │   body: {query: "Drug X hepatotoxicity literature"} │
    └─────────────────────────────────────────────────────┘

    Thread 2 (Stats):
    ┌─────────────────────────────────────────────────────┐
    │ Send TASK_ASSIGNMENT → stats_worker_001             │
    │   correlation_id: case_123                          │
    │   body: {analysis_type: "risk_assessment"}          │
    └─────────────────────────────────────────────────────┘

    Thread 3 (Risk):
    ┌─────────────────────────────────────────────────────┐
    │ Send TASK_ASSIGNMENT → risk_worker_001              │
    │   correlation_id: case_123                          │
    │   body: {model_type: "bayesian_network"}            │
    └─────────────────────────────────────────────────────┘

T2: Workers receive and execute (parallel):

    lit_worker_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive TASK_ASSIGNMENT                             │
    │ Execute literature search                           │
    │ Generate findings                                   │
    │ Send TASK_RESULT → resolution_engine                │
    │   Time: 45 seconds                                  │
    └─────────────────────────────────────────────────────┘

    stats_worker_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive TASK_ASSIGNMENT                             │
    │ Execute statistical analysis                        │
    │ Generate report                                     │
    │ Send TASK_RESULT → resolution_engine                │
    │   Time: 30 seconds                                  │
    └─────────────────────────────────────────────────────┘

    risk_worker_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive TASK_ASSIGNMENT                             │
    │ Build Bayesian network                              │
    │ Calculate probabilities                             │
    │ Send TASK_RESULT → resolution_engine                │
    │   Time: 60 seconds                                  │
    └─────────────────────────────────────────────────────┘

T3: Orchestrator receives results, sends for audit:

    All 3 threads (parallel):
    ┌─────────────────────────────────────────────────────┐
    │ Receive TASK_RESULT                                 │
    │ Send AUDIT_REQUEST → corresponding auditor          │
    └─────────────────────────────────────────────────────┘

T4: Auditors validate (parallel):

    lit_auditor_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive AUDIT_REQUEST                               │
    │ Check sources, evidence, compliance                 │
    │ Result: FAILED - missing PMIDs                      │
    │ Send AUDIT_RESULT → resolution_engine               │
    └─────────────────────────────────────────────────────┘

    stats_auditor_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive AUDIT_REQUEST                               │
    │ Validate statistics, check confidence intervals     │
    │ Result: PASSED                                      │
    │ Send AUDIT_RESULT → resolution_engine               │
    └─────────────────────────────────────────────────────┘

    risk_auditor_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive AUDIT_REQUEST                               │
    │ Validate model assumptions                          │
    │ Result: PASSED                                      │
    │ Send AUDIT_RESULT → resolution_engine               │
    └─────────────────────────────────────────────────────┘

T5: Resolution decisions:

    Thread 1 (Lit Review - FAILED):
    ┌─────────────────────────────────────────────────────┐
    │ Decision: RETRY                                     │
    │ Send CORRECTION_REQUEST → lit_worker_001            │
    │   corrections: ["Add PMID references"]              │
    └─────────────────────────────────────────────────────┘

    Thread 2 (Stats - PASSED):
    ┌─────────────────────────────────────────────────────┐
    │ Decision: ACCEPT                                    │
    │ Compress results                                    │
    │ Return to orchestrator                              │
    └─────────────────────────────────────────────────────┘

    Thread 3 (Risk - PASSED):
    ┌─────────────────────────────────────────────────────┐
    │ Decision: ACCEPT                                    │
    │ Compress results                                    │
    │ Return to orchestrator                              │
    └─────────────────────────────────────────────────────┘

T6: Lit review retry:

    lit_worker_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive CORRECTION_REQUEST                          │
    │ Re-execute with corrections                         │
    │ Add PMID references                                 │
    │ Send TASK_RESULT → resolution_engine                │
    └─────────────────────────────────────────────────────┘

T7: Re-audit literature review:

    lit_auditor_001:
    ┌─────────────────────────────────────────────────────┐
    │ Receive AUDIT_REQUEST (retry)                       │
    │ Validate updated output                             │
    │ Result: PASSED                                      │
    │ Send AUDIT_RESULT → resolution_engine               │
    └─────────────────────────────────────────────────────┘

T8: All tasks complete:

    Orchestrator:
    ┌─────────────────────────────────────────────────────┐
    │ All 3 threads completed                             │
    │ Collect compressed summaries                        │
    │ Synthesize final report                             │
    │ Return to user                                      │
    └─────────────────────────────────────────────────────┘

AUDIT TRAIL (mailbox.get_message_history(correlation_id="case_123")):

[TASK_ASSIGNMENT] orchestrator → lit_worker_001 (T1)
[TASK_ASSIGNMENT] orchestrator → stats_worker_001 (T1)
[TASK_ASSIGNMENT] orchestrator → risk_worker_001 (T1)
[TASK_RESULT] lit_worker_001 → resolution_engine (T2)
[TASK_RESULT] stats_worker_001 → resolution_engine (T2)
[TASK_RESULT] risk_worker_001 → resolution_engine (T2)
[AUDIT_REQUEST] resolution_engine → lit_auditor_001 (T3)
[AUDIT_REQUEST] resolution_engine → stats_auditor_001 (T3)
[AUDIT_REQUEST] resolution_engine → risk_auditor_001 (T3)
[AUDIT_RESULT] lit_auditor_001 → resolution_engine (T4) - FAILED
[AUDIT_RESULT] stats_auditor_001 → resolution_engine (T4) - PASSED
[AUDIT_RESULT] risk_auditor_001 → resolution_engine (T4) - PASSED
[CORRECTION_REQUEST] resolution_engine → lit_worker_001 (T5)
[TASK_RESULT] lit_worker_001 → resolution_engine (T6)
[AUDIT_REQUEST] resolution_engine → lit_auditor_001 (T7)
[AUDIT_RESULT] lit_auditor_001 → resolution_engine (T7) - PASSED

Total messages: 15
Total time: ~90 seconds (parallelized from ~135 seconds sequential)
Audit trail: Complete history with timestamps, correlation
```

## Performance Comparison

### Synchronous vs Agent Mail

```
SYNCHRONOUS (current):
┌────────────────────────────────────────────────────┐
│ Task 1: Execute → Audit → Retry → Audit           │
│ ████████████████████████████████████░              │
│ Time: 90s                                          │
└────────────────────────────────────────────────────┘
│ Task 2: Execute → Audit                            │
│                                  ████████████░     │
│ Time: 30s                                          │
└────────────────────────────────────────────────────┘
│ Task 3: Execute → Audit                            │
│                                            ██████░ │
│ Time: 20s                                          │
└────────────────────────────────────────────────────┘
Total: 140 seconds (sequential)

AGENT MAIL (parallel):
┌────────────────────────────────────────────────────┐
│ Task 1: ████████████████████████████████████░      │
│ Task 2:      ████████████░                         │
│ Task 3:                ██████░                     │
│                                                    │
│ ←──────────────── 90s ───────────────→            │
└────────────────────────────────────────────────────┘
Total: 90 seconds (parallelized)

Speedup: 1.56x (140s → 90s)

With 10 tasks: ~5x speedup
```

## Summary Benefits

| Feature | Synchronous | Agent Mail |
|---------|-------------|------------|
| **Parallelism** | ThreadPoolExecutor | ThreadPoolExecutor + Async messaging |
| **Audit Trail** | task.audit_history only | Complete message history |
| **Human Oversight** | Manual | Built-in review queue |
| **Observability** | Limited | Full message tracing |
| **Decoupling** | Tight (method calls) | Loose (messages) |
| **Recovery** | Lost on crash | SQLite persistence |
| **Debugging** | Stack traces | Message timeline |
| **Future Scaling** | Single process | Easy to distribute |
