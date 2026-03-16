# Multi-Agent Parallel Experimentation Framework for Safety Research

_Design Document -- March 16, 2026_

---

## 1. Framework Overview

This framework adapts the pattern demonstrated by Karpathy's Autoresearch (8 agents, 110+ commits in 12 hours) to the domain of AI safety research. Where Autoresearch used 4 Claude + 4 Codex instances to autonomously iterate on training code, we deploy specialized agent roles -- researcher, experimenter, analyst, auditor -- operating in parallel against a shared experiment registry backed by the agentic memory system described in ArXiv 2603.10062.

### Design Principles

- **Safety-first**: No experiment modifies shared state without auditor approval. Every action is logged immutably.
- **Parallelism with isolation**: Agents run concurrently in sandboxed environments. One agent's failure cannot cascade.
- **Structured memory hierarchy**: Per-agent working memory (cache layer), shared experiment registry (memory layer), persistent results store (I/O layer) -- following the three-layer architecture from the multi-agent memory paper.
- **Human-in-the-loop escalation**: Agents can propose but never unilaterally execute high-risk operations. A configurable risk threshold determines what requires human approval.

### Architecture Diagram (Logical)

```
                          +------------------+
                          |   Orchestrator   |
                          |  (Task Queue +   |
                          |   Coordinator)   |
                          +--------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
     +--------v-------+  +--------v-------+  +--------v-------+
     |  Researcher(s)  |  | Experimenter(s)|  |   Analyst(s)   |
     |  (Literature    |  |  (Runs safety  |  |  (Evaluates    |
     |   review,       |  |   experiments  |  |   results,     |
     |   hypotheses)   |  |   in sandbox)  |  |   statistics)  |
     +--------+-------+  +--------+-------+  +--------+-------+
              |                    |                    |
              +--------------------+--------------------+
                                   |
                          +--------v---------+
                          |    Auditor(s)     |
                          |  (Safety review,  |
                          |   gate-keeping)   |
                          +--------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
     +--------v-------+  +--------v-------+  +--------v-------+
     |  Per-Agent      |  |  Shared        |  |  Persistent    |
     |  Working Memory |  |  Experiment    |  |  Results       |
     |  (Cache)        |  |  Registry      |  |  Store         |
     +----------------+  +----------------+  +----------------+
```

---

## 2. Agent Roles

### 2.1 Researcher

**Purpose**: Literature review, hypothesis generation, and experiment proposal.

| Attribute | Detail |
|-----------|--------|
| Capabilities | Web search, paper retrieval, memory read (shared + own) |
| Restrictions | No code execution, no file writes outside own workspace |
| Outputs | Experiment proposals (structured JSON), literature summaries |
| Cardinality | 1--3 instances |

The researcher scans recent publications, safety benchmarks, and prior experiment results in the shared registry. It produces structured experiment proposals containing a hypothesis, methodology, expected outcomes, risk assessment, and resource requirements.

### 2.2 Experimenter

**Purpose**: Executes approved experiments in sandboxed environments.

| Attribute | Detail |
|-----------|--------|
| Capabilities | Code execution (sandboxed), file I/O (within sandbox), GPU access (quota-limited) |
| Restrictions | No network access except allowlisted APIs, no writes to shared state without auditor approval |
| Outputs | Raw experiment results, logs, artifacts |
| Cardinality | 2--4 instances (parallelism is the primary throughput lever) |

Experimenters pull approved tasks from the shared queue, execute them in isolated containers, and write results to their per-agent working memory. Results only propagate to the shared registry after auditor review.

### 2.3 Analyst

**Purpose**: Statistical evaluation, result interpretation, and cross-experiment synthesis.

| Attribute | Detail |
|-----------|--------|
| Capabilities | Read access to all experiment results, statistical computation, visualization generation |
| Restrictions | No code execution outside analysis sandbox, no experiment modification |
| Outputs | Analysis reports, statistical summaries, trend identification, recommendations for follow-up experiments |
| Cardinality | 1--2 instances |

The analyst compares results across experiments, identifies statistical anomalies, checks for p-hacking or confounds, and produces synthesis reports that feed back into the researcher's hypothesis generation.

### 2.4 Auditor

**Purpose**: Safety gate-keeping, policy enforcement, and audit trail maintenance.

| Attribute | Detail |
|-----------|--------|
| Capabilities | Read access to everything, veto power over experiment proposals and result publications, write access to audit log |
| Restrictions | Cannot propose or execute experiments (separation of duties) |
| Outputs | Approval/rejection decisions with justifications, safety violation reports, audit summaries |
| Cardinality | 1--2 instances (at least one must be available at all times) |

The auditor is the only role that can authorize transitions between pipeline stages. It reviews experiment proposals for safety risks, validates that execution stayed within approved parameters, and gates publication of results to the shared registry.

**Critical constraint**: The auditor role must run on a separate model instance with an independent system prompt to prevent prompt injection from other agents' outputs.

---

## 3. Coordination Protocol

### 3.1 Message Passing

Agents communicate exclusively through a structured message bus. Direct agent-to-agent communication is prohibited -- all messages route through the orchestrator, which logs them to the immutable audit trail.

```
Message Schema:
{
    "id": "uuid",
    "timestamp": "ISO-8601",
    "sender": {"role": "researcher", "instance_id": "r-01"},
    "recipient": "orchestrator" | {"role": "auditor", "instance_id": "a-01"},
    "type": "proposal" | "approval" | "rejection" | "result" | "query" | "alert",
    "payload": { ... },
    "priority": "low" | "normal" | "high" | "critical",
    "in_reply_to": "uuid | null"
}
```

### 3.2 Shared Task Queue

The orchestrator maintains a priority queue of tasks. Each task has a lifecycle state:

```
PROPOSED -> UNDER_REVIEW -> APPROVED -> QUEUED -> IN_PROGRESS -> COMPLETED -> ANALYZED -> PUBLISHED
                |                                      |              |
                v                                      v              v
            REJECTED                               FAILED        RETRACTED
```

Tasks are claimed by agents using optimistic locking -- an agent claims a task, and the orchestrator confirms the claim only if no other agent has already claimed it. This avoids the need for distributed locks.

### 3.3 Result Aggregation

Results flow through a three-stage aggregation pipeline:

1. **Raw results** -- Written by experimenters to per-agent working memory. Unvalidated.
2. **Validated results** -- After auditor confirms the experiment ran within approved parameters, results move to a staging area in the shared registry.
3. **Published results** -- After analyst review confirms statistical validity, results are committed to the persistent results store with an immutable hash.

### 3.4 Consensus Protocol for Shared State Mutations

Any modification to the shared experiment registry requires:

1. The proposing agent submits a mutation request.
2. At least one auditor approves.
3. The orchestrator applies the mutation and records the pre-state hash, mutation, and post-state hash in the audit log.

This mirrors the cache coherence protocols discussed in ArXiv 2603.10062, adapted for safety-critical operation.

---

## 4. Experiment Lifecycle

### Stage 1: Propose

**Actor**: Researcher

The researcher submits a structured experiment proposal:

```json
{
    "hypothesis": "Fine-tuning with RLHF on adversarial prompts reduces jailbreak success rate",
    "methodology": {
        "type": "comparative",
        "control": "baseline model without adversarial RLHF",
        "treatment": "model with adversarial RLHF (500 steps)",
        "metrics": ["jailbreak_success_rate", "helpfulness_score", "refusal_rate"],
        "dataset": "harmbench-v2",
        "compute_budget": {"gpu_hours": 4, "max_memory_gb": 80}
    },
    "risk_assessment": {
        "level": "medium",
        "concerns": ["Generates adversarial content during training"],
        "mitigations": ["Output filtering on training logs", "Sandboxed execution"]
    },
    "expected_duration_hours": 2,
    "priority": "normal"
}
```

### Stage 2: Review

**Actor**: Auditor

The auditor evaluates the proposal against the safety policy:

- Does the compute budget stay within limits?
- Are the identified risks adequately mitigated?
- Does the experiment overlap with or contradict any running experiment?
- Is the methodology sound enough to justify the resource expenditure?

The auditor produces an approval or rejection with written justification, which becomes part of the permanent record.

### Stage 3: Execute

**Actor**: Experimenter

Upon approval, the experiment enters the task queue. An experimenter claims it, provisions a sandboxed environment matching the approved resource limits, and runs the experiment. During execution:

- The experimenter writes periodic heartbeats to its working memory.
- If any resource limit is approached (>90% of budget), the orchestrator issues a warning.
- If any limit is exceeded, the circuit breaker terminates execution immediately.

### Stage 4: Analyze

**Actor**: Analyst

The analyst receives the raw results and performs:

- Statistical significance testing
- Effect size computation
- Comparison with prior experiments on the same hypothesis
- Identification of confounding variables
- Visualization generation

The analyst produces a structured report and flags any anomalies for human review.

### Stage 5: Report

**Actor**: Orchestrator (automated) + Human (for high-risk findings)

The final report aggregates:

- Original proposal and approval rationale
- Execution logs and resource consumption
- Analysis report with statistical findings
- Auditor sign-off on result validity

Reports are committed to the persistent results store. Significant findings trigger notifications to human researchers. The researcher agent consumes published reports to inform the next cycle of hypothesis generation, creating a continuous improvement loop.

---

## 5. Safety Guardrails

### 5.1 Sandboxed Execution Environments

Each agent runs in an isolated container with:

- **Filesystem**: Read-only base image + agent-specific writable overlay. No access to host filesystem.
- **Network**: Default-deny firewall. Experimenters have no network access. Researchers have allowlisted read-only access to paper repositories and search APIs.
- **IPC**: Agents communicate only through the message bus. No shared memory, no Unix sockets, no direct container-to-container networking.
- **Capabilities**: All Linux capabilities dropped except the minimum required. No `CAP_SYS_ADMIN`, no `CAP_NET_RAW`.

```yaml
# Per-agent container security policy
security_policy:
  filesystem:
    root: read_only
    workspace: read_write
    max_disk_mb: 5120
  network:
    default: deny
    allowlist: []  # Populated per-role
  capabilities:
    drop: [ALL]
    add: []
  seccomp: default  # Block dangerous syscalls
```

### 5.2 Resource Limits

Hard limits are enforced at the container level (cgroups). The orchestrator enforces soft limits and budget tracking.

| Resource | Per-Agent Limit | System Total |
|----------|----------------|--------------|
| CPU | 4 cores | 32 cores |
| RAM | 16 GB | 128 GB |
| GPU | 1 H100 (experimenter only) | 8 H100 |
| Disk | 5 GB writable | 40 GB |
| API calls | 100/min (researcher), 0 (experimenter) | 400/min |
| Experiment duration | 4 hours max | -- |
| Token budget per agent turn | 200K tokens | 1M tokens aggregate |

If an agent attempts to exceed its limits, the container runtime terminates the process. The orchestrator logs the violation and, depending on severity, may quarantine the agent for human review.

### 5.3 Mandatory Auditor Review Gates

The following operations **always** require auditor approval:

1. Moving an experiment from PROPOSED to APPROVED
2. Publishing results from per-agent working memory to the shared registry
3. Any experiment that scored "medium" or "high" on the risk assessment
4. Modifications to the experiment registry schema
5. Changes to any agent's system prompt or configuration

Operations that require **human** approval (not just auditor-agent):

1. Experiments rated "critical" risk
2. Any modification to the auditor's own configuration
3. Disabling or modifying safety guardrails
4. Granting network access to an experimenter agent

### 5.4 Kill Switches and Circuit Breakers

**Kill switches** (immediate termination):

- **Per-agent kill**: Terminates a single agent's container. Triggered by resource limit violation, safety policy breach, or human command.
- **Role kill**: Terminates all agents of a given role. Used when a systemic issue is detected in one role's behavior.
- **Global kill**: Terminates all agents and freezes the shared registry. Nuclear option for critical safety events.

**Circuit breakers** (automatic triggers):

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Agent error rate | >50% of tasks fail in 30 min | Pause agent, alert human |
| Resource spike | >90% of any limit | Warning; >100% terminates |
| Audit backlog | >10 unreviewed items | Pause new proposals |
| Anomalous output | Toxicity/harm classifier fires | Terminate experiment, quarantine results |
| Agent loop detection | Same action repeated >5 times | Pause agent, alert human |
| Cross-agent conflict | >3 contradictory results on same hypothesis | Pause pipeline, request human arbitration |

### 5.5 Immutable Audit Logs

All events are written to an append-only log. The log is implemented as a hash chain -- each entry includes the SHA-256 hash of the previous entry, making tampering detectable.

```
Log Entry Schema:
{
    "sequence": 1042,
    "timestamp": "2026-03-16T14:23:07Z",
    "prev_hash": "a3f2b1...",
    "event_type": "experiment_approved",
    "actor": {"role": "auditor", "instance_id": "aud-01"},
    "target": {"experiment_id": "exp-0073"},
    "detail": { ... },
    "hash": "b7c4d2..."  // SHA-256(sequence + timestamp + prev_hash + event_type + actor + target + detail)
}
```

Agents have **no write access** to the audit log -- only the orchestrator can append entries, and it does so for every state transition, message, and resource event. The log is replicated to an external store that no agent can reach.

---

## 6. Integration with Memory System

This framework maps directly onto the three-layer memory hierarchy from ArXiv 2603.10062.

### 6.1 Per-Agent Working Memory (Cache Layer)

Each agent maintains a private working memory that persists within a session but is not directly visible to other agents.

**Contents**:
- Current task context (the experiment being worked on)
- Scratch computations and intermediate results
- Draft proposals or analyses not yet submitted
- Agent-local conversation history

**Implementation**: Leverages Claude's 1M token context window (GA as of March 12, 2026). Context compaction auto-summarizes older entries when approaching the limit. Each agent's working memory is isolated -- one agent cannot read another's cache.

**Eviction policy**: LRU with priority pinning. Active experiment context is pinned; completed experiment context is eligible for eviction after results are committed.

### 6.2 Shared Experiment Registry (Memory Layer)

The central coordination structure, visible to all agents with role-based access control.

**Contents**:

| Section | Read Access | Write Access |
|---------|------------|--------------|
| Experiment proposals | All | Researcher (create), Auditor (approve/reject) |
| Task queue | All | Orchestrator (manage), Experimenter (claim) |
| Published results | All | Orchestrator (commit, after auditor approval) |
| Agent status | All | Orchestrator (update) |
| Safety policies | All | Human only |

**Consistency model**: Linearizable for state transitions (proposal -> approval -> execution). Eventual consistency is acceptable for read-only queries (e.g., analyst reading published results).

**Implementation**: A structured store (SQLite or PostgreSQL) fronted by the orchestrator. All access goes through the orchestrator's API -- no agent has direct database access. This enforces the access control matrix above and ensures every mutation is logged.

### 6.3 Persistent Results Store (I/O Layer)

Long-term storage for completed experiment results, analysis reports, and audit logs.

**Contents**:
- Immutable experiment artifacts (model checkpoints, evaluation outputs)
- Analysis reports with statistical summaries
- Full audit log chain
- Literature review summaries and citation graphs

**Implementation**: Object storage (S3-compatible) with content-addressed naming (SHA-256 of contents). Once written, objects are never modified or deleted. Retention policy: indefinite for experiment results and audit logs; 90 days for intermediate artifacts.

### 6.4 Memory Flow Across the Experiment Lifecycle

```
Researcher working memory          Shared Registry           Persistent Store
         |                               |                         |
         |-- [draft proposal] -->        |                         |
         |   (stays in cache until       |                         |
         |    researcher submits)        |                         |
         |                               |                         |
         |-- submit_proposal() --------> | PROPOSED                |
         |                               |     |                   |
         |                               |  auditor reviews        |
         |                               |     |                   |
         |                               | APPROVED                |
         |                               |     |                   |
         |                  Experimenter claims task                |
         |                               |     |                   |
         |              Experimenter working memory                 |
         |              (sandbox execution, local results)          |
         |                               |     |                   |
         |                               | COMPLETED               |
         |                               |     |                   |
         |                               |  auditor validates      |
         |                               |     |                   |
         |                  Analyst working memory                  |
         |                  (statistical analysis)                  |
         |                               |     |                   |
         |                               | PUBLISHED ------------> | results archived
         |                               |                         | audit log appended
         |                               |                         |
         |<-- read published results --- |                         |
         |   (feeds next hypothesis)     |                         |
```

---

## 7. Implementation Sketch

### 7.1 Core Orchestrator

```python
import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class TaskState(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ANALYZED = "analyzed"
    PUBLISHED = "published"
    REJECTED = "rejected"
    FAILED = "failed"
    RETRACTED = "retracted"


class AgentRole(Enum):
    RESEARCHER = "researcher"
    EXPERIMENTER = "experimenter"
    ANALYST = "analyst"
    AUDITOR = "auditor"


@dataclass
class AuditEntry:
    sequence: int
    timestamp: str
    prev_hash: str
    event_type: str
    actor: dict
    target: dict
    detail: dict
    hash: str = ""

    def compute_hash(self) -> str:
        content = f"{self.sequence}{self.timestamp}{self.prev_hash}"
        content += f"{self.event_type}{json.dumps(self.actor)}"
        content += f"{json.dumps(self.target)}{json.dumps(self.detail)}"
        self.hash = hashlib.sha256(content.encode()).hexdigest()
        return self.hash


@dataclass
class Experiment:
    id: str
    state: TaskState
    proposal: dict
    claimed_by: Optional[str] = None
    results: Optional[dict] = None
    analysis: Optional[dict] = None
    audit_trail: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Orchestrator:
    """Central coordinator for the multi-agent experimentation framework.

    Manages the task queue, enforces safety policies, routes messages
    between agents, and maintains the immutable audit log.
    """

    def __init__(self, config: dict):
        self.config = config
        self.agents: dict[str, "AgentHandle"] = {}
        self.experiments: dict[str, Experiment] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.audit_log: list[AuditEntry] = []
        self.message_bus: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._circuit_breakers = CircuitBreakerSet(config.get("circuit_breakers", {}))

    async def start(self):
        """Boot the orchestrator and all registered agents."""
        self._running = True
        await asyncio.gather(
            self._process_messages(),
            self._monitor_agents(),
            self._enforce_resource_limits(),
        )

    async def register_agent(self, role: AgentRole, instance_id: str, agent: "BaseAgent"):
        """Register an agent and provision its sandboxed environment."""
        sandbox = await SandboxManager.provision(
            role=role,
            resource_limits=self.config["resource_limits"][role.value],
            network_policy=self.config["network_policies"][role.value],
        )
        handle = AgentHandle(
            instance_id=instance_id,
            role=role,
            agent=agent,
            sandbox=sandbox,
            status="ready",
        )
        self.agents[instance_id] = handle
        self._append_audit("agent_registered", {"role": role.value, "id": instance_id}, {})

    async def submit_proposal(self, sender_id: str, proposal: dict) -> str:
        """Researcher submits an experiment proposal. Returns experiment ID."""
        agent = self.agents[sender_id]
        if agent.role != AgentRole.RESEARCHER:
            raise PermissionError("Only researchers can submit proposals")

        exp_id = f"exp-{uuid.uuid4().hex[:8]}"
        experiment = Experiment(id=exp_id, state=TaskState.PROPOSED, proposal=proposal)
        self.experiments[exp_id] = experiment

        self._append_audit(
            "experiment_proposed",
            {"role": "researcher", "id": sender_id},
            {"experiment_id": exp_id},
            detail={"hypothesis": proposal.get("hypothesis", "")},
        )

        # Route to auditor for review
        await self._route_to_auditor(exp_id)
        return exp_id

    async def approve_experiment(self, auditor_id: str, exp_id: str, justification: str):
        """Auditor approves an experiment, moving it to the task queue."""
        agent = self.agents[auditor_id]
        if agent.role != AgentRole.AUDITOR:
            raise PermissionError("Only auditors can approve experiments")

        exp = self.experiments[exp_id]
        if exp.state != TaskState.UNDER_REVIEW:
            raise ValueError(f"Experiment {exp_id} is not under review (state: {exp.state})")

        risk_level = exp.proposal.get("risk_assessment", {}).get("level", "low")
        if risk_level == "critical":
            raise PermissionError(
                f"Experiment {exp_id} is critical-risk and requires human approval"
            )

        exp.state = TaskState.APPROVED
        priority = {"high": 0, "normal": 1, "low": 2}.get(
            exp.proposal.get("priority", "normal"), 1
        )
        await self.task_queue.put((priority, exp_id))
        exp.state = TaskState.QUEUED

        self._append_audit(
            "experiment_approved",
            {"role": "auditor", "id": auditor_id},
            {"experiment_id": exp_id},
            detail={"justification": justification},
        )

    async def claim_task(self, experimenter_id: str) -> Optional[str]:
        """Experimenter claims the next available task. Returns experiment ID or None."""
        agent = self.agents[experimenter_id]
        if agent.role != AgentRole.EXPERIMENTER:
            raise PermissionError("Only experimenters can claim tasks")

        if self.task_queue.empty():
            return None

        _, exp_id = await self.task_queue.get()
        exp = self.experiments[exp_id]

        # Optimistic lock: check state before assigning
        if exp.state != TaskState.QUEUED:
            return None

        exp.state = TaskState.IN_PROGRESS
        exp.claimed_by = experimenter_id

        self._append_audit(
            "experiment_claimed",
            {"role": "experimenter", "id": experimenter_id},
            {"experiment_id": exp_id},
        )
        return exp_id

    async def submit_results(self, experimenter_id: str, exp_id: str, results: dict):
        """Experimenter submits raw results for auditor validation."""
        exp = self.experiments[exp_id]
        if exp.claimed_by != experimenter_id:
            raise PermissionError("Only the claiming experimenter can submit results")

        exp.results = results
        exp.state = TaskState.COMPLETED

        self._append_audit(
            "results_submitted",
            {"role": "experimenter", "id": experimenter_id},
            {"experiment_id": exp_id},
        )

        # Route to auditor for result validation
        await self._route_to_auditor(exp_id)

    async def publish_results(self, auditor_id: str, exp_id: str):
        """Auditor validates and publishes results to the persistent store."""
        agent = self.agents[auditor_id]
        if agent.role != AgentRole.AUDITOR:
            raise PermissionError("Only auditors can publish results")

        exp = self.experiments[exp_id]
        if exp.state != TaskState.ANALYZED:
            raise ValueError("Results must be analyzed before publication")

        exp.state = TaskState.PUBLISHED
        await PersistentStore.commit(exp_id, exp.results, exp.analysis)

        self._append_audit(
            "results_published",
            {"role": "auditor", "id": auditor_id},
            {"experiment_id": exp_id},
        )

    def kill_agent(self, instance_id: str, reason: str):
        """Immediately terminate an agent's sandbox."""
        handle = self.agents.get(instance_id)
        if handle:
            handle.sandbox.terminate()
            handle.status = "killed"
            self._append_audit(
                "agent_killed",
                {"role": "system", "id": "orchestrator"},
                {"agent_id": instance_id},
                detail={"reason": reason},
            )

    def kill_all(self, reason: str):
        """Global kill switch. Terminates all agents and freezes the registry."""
        self._running = False
        for instance_id in list(self.agents.keys()):
            self.kill_agent(instance_id, reason)
        self._append_audit(
            "global_kill",
            {"role": "system", "id": "orchestrator"},
            {},
            detail={"reason": reason},
        )

    def _append_audit(self, event_type: str, actor: dict, target: dict, detail: dict = None):
        prev_hash = self.audit_log[-1].hash if self.audit_log else "genesis"
        entry = AuditEntry(
            sequence=len(self.audit_log),
            timestamp=datetime.now(timezone.utc).isoformat(),
            prev_hash=prev_hash,
            event_type=event_type,
            actor=actor,
            target=target,
            detail=detail or {},
        )
        entry.compute_hash()
        self.audit_log.append(entry)

    async def _route_to_auditor(self, exp_id: str):
        """Route an experiment to an available auditor."""
        exp = self.experiments[exp_id]
        exp.state = TaskState.UNDER_REVIEW
        available_auditors = [
            a for a in self.agents.values()
            if a.role == AgentRole.AUDITOR and a.status == "ready"
        ]
        if not available_auditors:
            # Circuit breaker: no auditor available
            self._circuit_breakers.trip("no_auditor_available")
            return
        # Round-robin or least-loaded selection
        auditor = min(available_auditors, key=lambda a: a.pending_reviews)
        await self.message_bus.put({
            "type": "review_request",
            "recipient": auditor.instance_id,
            "experiment_id": exp_id,
        })

    async def _process_messages(self):
        """Main message processing loop."""
        while self._running:
            msg = await self.message_bus.get()
            self._append_audit(
                "message_routed",
                msg.get("sender", {"role": "system"}),
                {"recipient": msg.get("recipient", "unknown")},
                detail={"type": msg.get("type")},
            )
            recipient = self.agents.get(msg.get("recipient"))
            if recipient and recipient.status == "ready":
                await recipient.agent.receive_message(msg)

    async def _monitor_agents(self):
        """Periodic health checks and circuit breaker evaluation."""
        while self._running:
            for handle in self.agents.values():
                if handle.status == "ready":
                    health = await handle.sandbox.health_check()
                    if not health.ok:
                        self._circuit_breakers.evaluate(handle, health)
            await asyncio.sleep(5)

    async def _enforce_resource_limits(self):
        """Periodic resource usage checks."""
        while self._running:
            for handle in self.agents.values():
                if handle.status == "ready":
                    usage = await handle.sandbox.resource_usage()
                    limits = self.config["resource_limits"][handle.role.value]
                    for resource, value in usage.items():
                        limit = limits.get(resource, float("inf"))
                        if value > limit:
                            self.kill_agent(handle.instance_id, f"{resource} limit exceeded")
                        elif value > 0.9 * limit:
                            await self.message_bus.put({
                                "type": "resource_warning",
                                "recipient": handle.instance_id,
                                "resource": resource,
                                "usage_pct": value / limit,
                            })
            await asyncio.sleep(10)
```

### 7.2 Agent Base Class

```python
from abc import ABC, abstractmethod


@dataclass
class AgentHandle:
    instance_id: str
    role: AgentRole
    agent: "BaseAgent"
    sandbox: "Sandbox"
    status: str = "ready"
    pending_reviews: int = 0


class WorkingMemory:
    """Per-agent working memory backed by Claude's 1M context window.

    Provides structured read/write access with automatic compaction
    when approaching the token budget.
    """

    def __init__(self, token_budget: int = 200_000):
        self.token_budget = token_budget
        self.entries: list[dict] = []
        self.pinned_keys: set[str] = set()

    def write(self, key: str, value: dict, pin: bool = False):
        self.entries.append({"key": key, "value": value, "ts": datetime.now(timezone.utc).isoformat()})
        if pin:
            self.pinned_keys.add(key)
        self._compact_if_needed()

    def read(self, key: str) -> Optional[dict]:
        for entry in reversed(self.entries):
            if entry["key"] == key:
                return entry["value"]
        return None

    def read_all(self, prefix: str = "") -> list[dict]:
        return [e for e in self.entries if e["key"].startswith(prefix)]

    def _compact_if_needed(self):
        estimated_tokens = sum(len(json.dumps(e)) // 4 for e in self.entries)
        if estimated_tokens > self.token_budget * 0.85:
            # Evict oldest unpinned entries
            self.entries = [
                e for e in self.entries
                if e["key"] in self.pinned_keys
            ] + self.entries[-100:]  # Keep recent context


class BaseAgent(ABC):
    """Abstract base class for all agent roles.

    Provides working memory, message handling, and the interface
    that the orchestrator uses to drive agent behavior.
    """

    def __init__(self, instance_id: str, role: AgentRole, config: dict):
        self.instance_id = instance_id
        self.role = role
        self.config = config
        self.memory = WorkingMemory(token_budget=config.get("token_budget", 200_000))
        self._message_queue: asyncio.Queue = asyncio.Queue()

    async def receive_message(self, message: dict):
        """Called by the orchestrator to deliver a message."""
        await self._message_queue.put(message)

    async def run(self, orchestrator: Orchestrator):
        """Main agent loop. Override in subclasses for role-specific behavior."""
        while True:
            try:
                await self._step(orchestrator)
            except Exception as e:
                self.memory.write("error", {"error": str(e), "type": type(e).__name__})
                raise  # Let the sandbox/orchestrator handle it

    @abstractmethod
    async def _step(self, orchestrator: Orchestrator):
        """Single step of agent behavior. Implemented by each role."""
        ...


class ResearcherAgent(BaseAgent):
    """Conducts literature review and proposes experiments."""

    def __init__(self, instance_id: str, config: dict):
        super().__init__(instance_id, AgentRole.RESEARCHER, config)

    async def _step(self, orchestrator: Orchestrator):
        # Check for new published results to inform next hypothesis
        published = self.memory.read("latest_published")
        # ... (use Claude API to reason about gaps in existing research)

        proposal = await self._generate_proposal(published)
        if proposal:
            exp_id = await orchestrator.submit_proposal(self.instance_id, proposal)
            self.memory.write(f"proposal_{exp_id}", proposal)

        # Process any incoming messages (e.g., requests for clarification)
        while not self._message_queue.empty():
            msg = await self._message_queue.get()
            await self._handle_message(msg, orchestrator)

        await asyncio.sleep(30)  # Polling interval

    async def _generate_proposal(self, context: Optional[dict]) -> Optional[dict]:
        """Use Claude to generate an experiment proposal based on current context."""
        # This would call the Claude API with the researcher's system prompt,
        # working memory context, and published results.
        # Returns a structured proposal dict or None if no new hypothesis.
        ...

    async def _handle_message(self, msg: dict, orchestrator: Orchestrator):
        ...


class ExperimenterAgent(BaseAgent):
    """Claims and executes approved experiments in a sandbox."""

    def __init__(self, instance_id: str, config: dict):
        super().__init__(instance_id, AgentRole.EXPERIMENTER, config)

    async def _step(self, orchestrator: Orchestrator):
        # Try to claim a task
        exp_id = await orchestrator.claim_task(self.instance_id)
        if exp_id is None:
            await asyncio.sleep(10)
            return

        exp = orchestrator.experiments[exp_id]
        self.memory.write(f"active_experiment", exp.proposal, pin=True)

        try:
            results = await self._execute_experiment(exp.proposal)
            await orchestrator.submit_results(self.instance_id, exp_id, results)
            self.memory.write(f"results_{exp_id}", results)
        except ResourceLimitExceeded:
            # Orchestrator will handle termination; log what we can
            self.memory.write(f"failed_{exp_id}", {"reason": "resource_limit"})
            raise
        finally:
            self.memory.pinned_keys.discard("active_experiment")

    async def _execute_experiment(self, proposal: dict) -> dict:
        """Run the experiment within the sandbox. Returns raw results."""
        # This executes the experiment code in the sandboxed environment.
        # The sandbox enforces resource limits at the container level.
        ...


class AnalystAgent(BaseAgent):
    """Evaluates experiment results and produces analysis reports."""

    def __init__(self, instance_id: str, config: dict):
        super().__init__(instance_id, AgentRole.ANALYST, config)

    async def _step(self, orchestrator: Orchestrator):
        # Look for completed experiments awaiting analysis
        for exp_id, exp in orchestrator.experiments.items():
            if exp.state == TaskState.COMPLETED and exp.results:
                analysis = await self._analyze_results(exp)
                exp.analysis = analysis
                exp.state = TaskState.ANALYZED
                self.memory.write(f"analysis_{exp_id}", analysis)
                # Notify auditor that analysis is ready for final review
                await orchestrator.message_bus.put({
                    "type": "analysis_complete",
                    "sender": {"role": "analyst", "id": self.instance_id},
                    "recipient": "orchestrator",
                    "experiment_id": exp_id,
                })
        await asyncio.sleep(15)

    async def _analyze_results(self, experiment: Experiment) -> dict:
        """Statistical analysis of experiment results using Claude for interpretation."""
        ...


class AuditorAgent(BaseAgent):
    """Reviews proposals and results for safety compliance."""

    def __init__(self, instance_id: str, config: dict):
        super().__init__(instance_id, AgentRole.AUDITOR, config)
        # Auditor uses a separate system prompt loaded from a protected config
        self.safety_policy = config["safety_policy"]

    async def _step(self, orchestrator: Orchestrator):
        while not self._message_queue.empty():
            msg = await self._message_queue.get()

            if msg["type"] == "review_request":
                exp_id = msg["experiment_id"]
                exp = orchestrator.experiments[exp_id]

                decision = await self._review(exp)

                if decision["approved"]:
                    if exp.state == TaskState.UNDER_REVIEW and exp.results is None:
                        await orchestrator.approve_experiment(
                            self.instance_id, exp_id, decision["justification"]
                        )
                    elif exp.state == TaskState.ANALYZED:
                        await orchestrator.publish_results(self.instance_id, exp_id)
                else:
                    exp.state = TaskState.REJECTED
                    self.memory.write(f"rejection_{exp_id}", decision)

        await asyncio.sleep(5)

    async def _review(self, experiment: Experiment) -> dict:
        """Evaluate an experiment against the safety policy using Claude.

        The auditor's Claude instance runs with a separate system prompt
        that cannot be influenced by other agents' outputs.
        """
        # Calls Claude API with:
        # - The auditor's safety-focused system prompt
        # - The experiment proposal or results
        # - The safety policy document
        # Returns {"approved": bool, "justification": str, "concerns": [...]}
        ...
```

### 7.3 Experiment Runner (Sandbox Integration)

```python
import subprocess
from dataclasses import dataclass


@dataclass
class ResourceUsage:
    cpu_cores: float
    memory_gb: float
    gpu_utilization_pct: float
    disk_gb: float
    elapsed_seconds: float


@dataclass
class HealthStatus:
    ok: bool
    details: str = ""


class Sandbox:
    """Manages an isolated container for a single agent."""

    def __init__(self, container_id: str, resource_limits: dict):
        self.container_id = container_id
        self.resource_limits = resource_limits

    async def execute(self, command: list[str], timeout: int = 3600) -> dict:
        """Run a command inside the sandbox with hard timeout."""
        result = subprocess.run(
            ["docker", "exec", self.container_id] + command,
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    async def health_check(self) -> HealthStatus:
        result = await self.execute(["echo", "ok"], timeout=5)
        return HealthStatus(ok=result["returncode"] == 0, details=result.get("stderr", ""))

    async def resource_usage(self) -> dict:
        stats = await self.execute(["cat", "/sys/fs/cgroup/memory.current"], timeout=5)
        # Parse cgroup stats into ResourceUsage
        # (simplified -- real implementation reads multiple cgroup files)
        return {"memory_gb": int(stats["stdout"].strip()) / (1024**3)}

    def terminate(self):
        subprocess.run(["docker", "kill", self.container_id], timeout=10)


class SandboxManager:
    """Provisions and manages sandboxed containers for agents."""

    @staticmethod
    async def provision(role: AgentRole, resource_limits: dict, network_policy: dict) -> Sandbox:
        """Create a new sandboxed container for an agent."""
        container_id = f"agent-{role.value}-{uuid.uuid4().hex[:8]}"

        cmd = [
            "docker", "run", "-d",
            "--name", container_id,
            "--read-only",
            "--tmpfs", "/workspace:rw,size=5g",
            "--memory", f"{resource_limits['memory_gb']}g",
            "--cpus", str(resource_limits['cpu_cores']),
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL",
            "--network", "none" if not network_policy.get("allowlist") else "agent-net",
            "agent-base-image:latest",
        ]

        if role == AgentRole.EXPERIMENTER and resource_limits.get("gpu"):
            cmd.insert(-1, "--gpus")
            cmd.insert(-1, f'"device={resource_limits["gpu"]}"')

        subprocess.run(cmd, check=True, timeout=30)
        return Sandbox(container_id, resource_limits)


class CircuitBreakerSet:
    """Monitors system health and triggers automatic safety responses."""

    def __init__(self, config: dict):
        self.config = config
        self.trip_counts: dict[str, int] = {}
        self.tripped: set[str] = set()

    def trip(self, breaker_name: str):
        self.tripped.add(breaker_name)
        self.trip_counts[breaker_name] = self.trip_counts.get(breaker_name, 0) + 1

    def evaluate(self, agent_handle: AgentHandle, health: HealthStatus):
        if not health.ok:
            key = f"unhealthy_{agent_handle.instance_id}"
            self.trip_counts[key] = self.trip_counts.get(key, 0) + 1
            if self.trip_counts[key] >= self.config.get("max_unhealthy_checks", 3):
                self.trip(key)
                agent_handle.status = "quarantined"

    def is_tripped(self, breaker_name: str) -> bool:
        return breaker_name in self.tripped


class ExperimentRunner:
    """High-level runner that boots the full framework."""

    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)

    async def run(self):
        orchestrator = Orchestrator(self.config)

        # Provision agents according to config
        agents = []
        role_classes = {
            AgentRole.RESEARCHER: ResearcherAgent,
            AgentRole.EXPERIMENTER: ExperimenterAgent,
            AgentRole.ANALYST: AnalystAgent,
            AgentRole.AUDITOR: AuditorAgent,
        }

        for agent_spec in self.config["agents"]:
            role = AgentRole(agent_spec["role"])
            cls = role_classes[role]
            instance_id = f"{role.value}-{uuid.uuid4().hex[:4]}"
            agent = cls(instance_id, agent_spec.get("config", {}))
            await orchestrator.register_agent(role, instance_id, agent)
            agents.append((agent, orchestrator))

        # Run all agents concurrently
        await asyncio.gather(
            orchestrator.start(),
            *[agent.run(orch) for agent, orch in agents],
        )


# Entry point
if __name__ == "__main__":
    runner = ExperimentRunner("experiment_config.json")
    asyncio.run(runner.run())
```

### 7.4 Example Configuration

```json
{
    "agents": [
        {"role": "researcher", "config": {"token_budget": 200000}},
        {"role": "researcher", "config": {"token_budget": 200000}},
        {"role": "experimenter", "config": {"token_budget": 150000}},
        {"role": "experimenter", "config": {"token_budget": 150000}},
        {"role": "experimenter", "config": {"token_budget": 150000}},
        {"role": "analyst", "config": {"token_budget": 200000}},
        {"role": "auditor", "config": {"token_budget": 200000, "safety_policy": "policies/safety_v1.json"}},
        {"role": "auditor", "config": {"token_budget": 200000, "safety_policy": "policies/safety_v1.json"}}
    ],
    "resource_limits": {
        "researcher": {"cpu_cores": 4, "memory_gb": 16, "gpu": null},
        "experimenter": {"cpu_cores": 4, "memory_gb": 16, "gpu": "0"},
        "analyst": {"cpu_cores": 4, "memory_gb": 16, "gpu": null},
        "auditor": {"cpu_cores": 2, "memory_gb": 8, "gpu": null}
    },
    "network_policies": {
        "researcher": {"allowlist": ["arxiv.org", "semanticscholar.org", "api.anthropic.com"]},
        "experimenter": {"allowlist": []},
        "analyst": {"allowlist": ["api.anthropic.com"]},
        "auditor": {"allowlist": ["api.anthropic.com"]}
    },
    "circuit_breakers": {
        "max_unhealthy_checks": 3,
        "max_error_rate_pct": 50,
        "max_audit_backlog": 10
    }
}
```

---

## References

- Karpathy, A. (2026). "Autoresearch." 8 agents (4 Claude + 4 Codex), 110+ commits in 12 hours of autonomous LLM training research.
- Yu, Z. et al. (2026). "Multi-Agent Memory from a Computer Architecture Perspective." ArXiv 2603.10062. Three-layer memory hierarchy, shared vs. distributed paradigms, cache coherence for agents.
- Anthropic (2026). Claude Opus 4.6: 1M context window (GA), 128K max output, built-in context compaction.
