# Agentic Memory Architecture for Safety Research

_Version 0.1 -- March 16, 2026_

_Designed for Claude Opus 4.6 (1M context window, 128K max output tokens)_

---

## 1. Architecture Overview

This document specifies a memory architecture for agentic systems built on large-context language models. The design targets Claude Opus 4.6 with its 1M token context window, but the principles generalize to any sufficiently large context model.

### Design Goals

1. **Safety-first persistence**: Memory contents are auditable, attributable, and tamper-evident.
2. **Efficient context utilization**: Maximize the information density within the 1M token budget without degrading reasoning quality.
3. **Cross-session continuity**: Agents can resume tasks across sessions without re-deriving state from scratch.
4. **Multi-agent coordination**: Multiple agents can share memory with well-defined consistency and access control guarantees.

### System Diagram

```
+------------------------------------------------------------------+
|                        AGENT RUNTIME                             |
|                                                                  |
|  +------------------+    +------------------+    +-----------+   |
|  |   I/O Layer      |    |   Cache Layer    |    |  Memory   |   |
|  |  (Tool Results,  |--->| (Working Memory, |--->|   Layer   |   |
|  |   User Input,    |    |  Session State,  |    | (Durable  |   |
|  |   Observations)  |    |  Compacted Ctx)  |    |  Store)   |   |
|  +------------------+    +------------------+    +-----------+   |
|         ^                        ^                     ^         |
|         |                        |                     |         |
|  +------+------------------------+---------------------+------+  |
|  |              Context Window (up to 1M tokens)              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  +------------------------------------------------------------+  |
|  |              Safety Monitor (read-only audit)               |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
         |                                          |
         v                                          v
  +--------------+                          +----------------+
  | External     |                          | Persistent     |
  | Tools / APIs |                          | Memory Store   |
  +--------------+                          | (DB / Files)   |
                                            +----------------+
```

### Architectural Principles

- **Explicit provenance**: Every memory entry records its source (tool output, user statement, agent inference) and timestamp.
- **Separation of recall and reasoning**: The memory system retrieves; the model reasons. Memory never contains executable instructions that bypass the model's own judgment.
- **Graceful degradation**: If memory is unavailable or corrupted, the agent falls back to in-context information and transparently reports the limitation.
- **Least privilege**: Agents access only the memory partitions they need for their current task.

---

## 2. Memory Hierarchy

Adapted from the three-layer model proposed in Yu et al. (arXiv 2603.10062), mapped to the practical constraints of a large-context LLM agent.

### Layer 1: I/O Layer (Ephemeral)

**Purpose**: Raw interaction data -- tool call results, user messages, API responses, file contents.

| Property | Value |
|---|---|
| Lifetime | Current turn or tool call |
| Token budget | Up to 200K tokens per turn |
| Persistence | None -- discarded after processing |
| Safety property | Inputs are untrusted by default |

**Behavior**: Raw tool outputs and user inputs enter here. The agent processes them, extracts relevant facts, and promotes selected information to the cache layer. Large tool outputs (e.g., full file contents) are summarized before promotion.

**Safety rule**: All I/O layer content is treated as **untrusted input**. The agent must not directly copy I/O content into durable memory without validation (see Section 4).

### Layer 2: Cache Layer (Session-Scoped Working Memory)

**Purpose**: The agent's active working set for the current session -- plans, intermediate results, conversation state, recently retrieved memories.

| Property | Value |
|---|---|
| Lifetime | Current session |
| Token budget | 300K--600K tokens (dynamic) |
| Persistence | Lost on session end unless explicitly saved |
| Safety property | Agent-controlled; subject to compaction |

**Behavior**: This is the primary workspace. It contains:
- The current task plan and progress state
- Summaries of processed I/O data
- Retrieved memory entries relevant to the current task
- Reasoning traces and intermediate conclusions

**Compaction**: When the cache layer approaches its budget ceiling, the system triggers compaction (see Section 3). Compacted content is replaced with summaries that preserve key facts and decisions while reducing token count.

**Safety rule**: Cache contents are **agent-generated** and should be treated with moderate trust. Compaction summaries must be marked as derived content, not primary sources.

### Layer 3: Memory Layer (Persistent Cross-Session Storage)

**Purpose**: Durable storage that survives across sessions. This is the long-term knowledge base.

| Property | Value |
|---|---|
| Lifetime | Indefinite (until explicitly deleted or expired) |
| Token budget | Unbounded (stored externally) |
| Persistence | Durable -- backed by external storage |
| Safety property | Highest integrity requirements |

**Stored content types**:
- **Factual memories**: Verified facts extracted from tools or user statements
- **Procedural memories**: Learned procedures, preferences, and patterns
- **Episodic memories**: Summaries of past sessions and their outcomes
- **Index metadata**: Tags, embeddings, access timestamps for retrieval

**Safety rule**: Memory layer writes require validation (see Section 4). Every entry carries a provenance record and an integrity hash.

### Shared vs. Distributed Memory (Multi-Agent)

Following the taxonomy from arXiv 2603.10062:

| Paradigm | Use Case | Consistency Model |
|---|---|---|
| **Shared memory** | Agents collaborating on a single task; shared knowledge base | Sequential consistency -- all agents see writes in the same order |
| **Distributed memory** | Independent agents with occasional coordination | Eventual consistency -- agents sync periodically |
| **Hybrid** | Team of agents with private working memory and a shared fact store | Private caches with shared memory layer; explicit sync points |

For safety research, the **hybrid model** is recommended: each agent maintains its own cache layer, but the memory layer is shared with access controls. This limits blast radius if one agent's cache is corrupted.

---

## 3. Context Window Management Strategy

### Token Budget Allocation

The 1M token context window is partitioned dynamically. The following are target allocations, not hard limits:

```
1,000,000 tokens total
├── System prompt + instructions:         ~10,000 tokens  (1%)
├── Retrieved memories (from Layer 3):    ~100,000 tokens (10%)
├── Cache / working memory (Layer 2):     ~500,000 tokens (50%)
├── Current I/O (Layer 1):                ~200,000 tokens (20%)
├── Reserved for output generation:       ~128,000 tokens (13%)
└── Safety margin / headroom:             ~62,000 tokens  (6%)
```

### What Goes In Context vs. External Storage

| In Context | External Storage |
|---|---|
| Active task plan and current step | Full session history beyond current session |
| Relevant retrieved memories (summaries) | Raw memory entries not relevant to current task |
| Recent tool outputs being actively used | Historical tool outputs already processed |
| User conversation for current session | Prior session transcripts |
| Critical safety constraints and rules | Full policy documents (retrieve relevant sections) |

**Guiding principle**: Context holds what the agent needs to reason about *right now*. Everything else lives in external storage and is retrieved on demand.

### Compaction Triggers and Strategy

Compaction is triggered when context usage crosses defined thresholds:

```python
COMPACTION_THRESHOLDS = {
    "soft": 0.70,   # 700K tokens -- begin summarizing oldest cache entries
    "hard": 0.85,   # 850K tokens -- aggressively compact, drop low-priority content
    "critical": 0.92 # 920K tokens -- emergency compaction, preserve only essentials
}
```

**Compaction procedure**:

1. **Identify candidates**: Rank cache entries by recency and relevance to current task.
2. **Summarize**: Replace verbose entries with summaries. Preserve: key decisions, facts, unresolved questions. Discard: redundant reasoning traces, superseded plans.
3. **Offload**: Move compacted-away content to external storage with a retrieval key, so it can be recalled if needed.
4. **Verify**: After compaction, verify that critical task state is still present in context. If not, retrieve it.

**Safety rule**: Compaction must never silently drop safety-relevant information (constraints, user-specified boundaries, access control state). These are tagged as non-compactable.

### Prefill Latency Management

At 1M tokens, prefill latency can exceed 2 minutes. Mitigation strategies:

- **Lazy loading**: Start with minimal context; retrieve memories only as needed.
- **Prioritized retrieval**: Load the most relevant memories first so the agent can begin work while additional context streams in.
- **Incremental context**: For multi-turn sessions, add to existing context rather than rebuilding from scratch.

---

## 4. Safety Considerations

### 4.1 Memory Poisoning

**Threat**: An adversary (or a malfunctioning tool) injects false information into the memory layer, causing the agent to act on incorrect beliefs in future sessions.

**Mitigations**:

- **Input validation**: All data entering the memory layer passes through a validation step. The agent must distinguish between **observed facts** (from trusted tools), **user claims** (stated but not verified), and **agent inferences** (derived by the model).
- **Provenance tracking**: Every memory entry records:
  ```
  {
      source_type: "tool_output" | "user_statement" | "agent_inference",
      source_id: "<tool_call_id or message_id>",
      session_id: "<session identifier>",
      timestamp: "<ISO 8601>",
      confidence: float,  # 0.0 to 1.0
      integrity_hash: "<SHA-256 of content at write time>"
  }
  ```
- **Confidence decay**: Memory entries that have not been re-confirmed lose confidence over time. Entries below a threshold are flagged for re-verification before use.
- **Write-ahead audit log**: All memory mutations (create, update, delete) are logged to an append-only audit trail before being applied. This allows forensic analysis of poisoning incidents.

### 4.2 Hallucinated Memories

**Threat**: The agent fabricates a memory -- claiming to recall something from a prior session that never occurred.

**Mitigations**:

- **Retrieval-only recall**: The agent does not "remember" anything directly. All cross-session knowledge comes from explicit memory retrieval operations. If the memory system returns no results, the agent must say so rather than confabulating.
- **Citation requirement**: When the agent uses a memory, it must cite the memory entry ID and source. This is auditable.
- **Consistency checks**: Before acting on a retrieved memory, the agent cross-references it against other available evidence. Contradictions are flagged.
- **Distinguishing recall from inference**: The system prompt instructs the agent to clearly separate "I retrieved this from memory" from "I am inferring this." The safety monitor (Section 4.5) checks for violations.

### 4.3 Consistency Guarantees

For multi-agent setups with shared memory:

- **Read-your-writes**: An agent that writes a memory entry will see it in subsequent reads within the same session.
- **Monotonic reads**: Once an agent reads a version of a memory entry, it will not see an older version in subsequent reads.
- **Conflict resolution**: If two agents write to the same memory key concurrently, the system applies last-writer-wins with full version history. No writes are silently lost -- the overwritten version is preserved in the audit log.
- **Atomic operations**: Batch memory updates (e.g., updating a plan with multiple steps) are atomic -- either all entries are written or none are.

### 4.4 Access Control

```
Memory Namespace Structure:

/global/                  # Read by all agents, written by admins only
/shared/<team_id>/        # Read/write by team members
/private/<agent_id>/      # Read/write by owning agent only
/audit/                   # Append-only, read by safety monitor only
```

**Permissions model**:

| Role | /global/ | /shared/ | /private/ | /audit/ |
|---|---|---|---|---|
| Admin | R/W | R/W | R (audit) | R |
| Agent (team member) | R | R/W (own team) | R/W (own) | W (append) |
| Agent (external) | R | -- | -- | W (append) |
| Safety monitor | R | R | R | R |

**Safety rule**: No agent can modify another agent's private memory. No agent can delete audit log entries.

### 4.5 Safety Monitor

A read-only observer that runs alongside the agent (or as a post-hoc analysis step):

- **Memory integrity checks**: Periodically verifies integrity hashes on memory entries.
- **Anomaly detection**: Flags unusual patterns -- rapid writes, bulk deletions, entries with no provenance, contradictory memories.
- **Policy compliance**: Checks that memory operations conform to access control rules and that safety-critical context was not dropped during compaction.
- **Alert thresholds**: Configurable severity levels (info, warning, critical) with appropriate notification channels.

---

## 5. Interface Specification

### 5.1 Core Data Types

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SourceType(Enum):
    TOOL_OUTPUT = "tool_output"
    USER_STATEMENT = "user_statement"
    AGENT_INFERENCE = "agent_inference"
    COMPACTION_SUMMARY = "compaction_summary"


class MemoryNamespace(Enum):
    GLOBAL = "global"
    SHARED = "shared"
    PRIVATE = "private"


@dataclass
class Provenance:
    source_type: SourceType
    source_id: str
    session_id: str
    timestamp: datetime
    agent_id: str
    confidence: float  # 0.0 to 1.0


@dataclass
class MemoryEntry:
    entry_id: str              # Unique identifier (UUID)
    namespace: MemoryNamespace
    key: str                   # Hierarchical key, e.g. "project/findings/result_1"
    content: str               # The memory content (text)
    provenance: Provenance
    tags: list[str] = field(default_factory=list)
    integrity_hash: str = ""   # SHA-256 of content
    version: int = 1
    expires_at: Optional[datetime] = None
```

### 5.2 Operations

#### store

Write a new memory entry. Fails if the key already exists (use `update` for existing keys).

```python
def store(
    namespace: MemoryNamespace,
    key: str,
    content: str,
    source_type: SourceType,
    source_id: str,
    tags: list[str] = None,
    confidence: float = 1.0,
    ttl_seconds: int = None,
) -> MemoryEntry:
    """
    Store a new memory entry.

    Safety checks performed:
    1. Verify agent has write access to namespace.
    2. Reject if key already exists (prevents silent overwrites).
    3. Compute integrity hash of content.
    4. Write to audit log before committing.
    5. Validate content length is within limits.

    Returns the created MemoryEntry with assigned entry_id.
    Raises:
        KeyExistsError - if key already exists
        AccessDeniedError - if agent lacks write permission
        ValidationError - if content fails safety checks
    """
    ...
```

#### retrieve

Fetch a memory entry by exact key.

```python
def retrieve(
    namespace: MemoryNamespace,
    key: str,
    verify_integrity: bool = True,
) -> Optional[MemoryEntry]:
    """
    Retrieve a memory entry by key.

    Safety checks performed:
    1. Verify agent has read access to namespace.
    2. If verify_integrity is True, recompute hash and compare.
       Log a warning if mismatch (possible tampering).
    3. Update access timestamp for recency tracking.

    Returns the MemoryEntry or None if not found.
    Raises:
        AccessDeniedError - if agent lacks read permission
        IntegrityError - if hash verification fails
    """
    ...
```

#### search

Find memory entries matching a query. Supports semantic similarity and tag filtering.

```python
def search(
    query: str,
    namespace: MemoryNamespace = None,  # None = search all accessible
    tags: list[str] = None,
    min_confidence: float = 0.0,
    max_results: int = 20,
    recency_weight: float = 0.3,  # Balance relevance vs. recency
) -> list[MemoryEntry]:
    """
    Search for memory entries matching a query.

    Ranking formula:
        score = (1 - recency_weight) * semantic_similarity
                + recency_weight * recency_score

    Safety checks performed:
    1. Filter results to only namespaces the agent can read.
    2. Exclude entries below min_confidence.
    3. Exclude expired entries.
    4. Log the search query and result count to audit trail.

    Returns a ranked list of MemoryEntry objects.
    """
    ...
```

#### update

Modify an existing memory entry. Creates a new version; the old version is preserved in history.

```python
def update(
    namespace: MemoryNamespace,
    key: str,
    new_content: str = None,
    new_tags: list[str] = None,
    new_confidence: float = None,
    reason: str = "",  # Why the update is being made
) -> MemoryEntry:
    """
    Update an existing memory entry. Non-destructive: previous
    version is preserved in version history.

    Safety checks performed:
    1. Verify agent has write access to namespace.
    2. Verify entry exists (fail if not).
    3. Increment version number.
    4. Recompute integrity hash.
    5. Write old version + update reason to audit log.
    6. If confidence is being lowered, log a warning.

    Returns the updated MemoryEntry.
    Raises:
        KeyNotFoundError - if key does not exist
        AccessDeniedError - if agent lacks write permission
    """
    ...
```

#### delete

Mark a memory entry as deleted. The entry is tombstoned, not physically removed, to preserve audit history.

```python
def delete(
    namespace: MemoryNamespace,
    key: str,
    reason: str,  # Required: why is this being deleted
) -> bool:
    """
    Soft-delete a memory entry. The entry is tombstoned and excluded
    from future reads/searches, but preserved in the audit log.

    Safety checks performed:
    1. Verify agent has write access to namespace.
    2. Require a non-empty reason (no silent deletions).
    3. Write deletion event to audit log with full entry snapshot.
    4. Entries in /global/ require admin role to delete.

    Returns True if entry was deleted, False if not found.
    Raises:
        AccessDeniedError - if agent lacks permission
        ValueError - if reason is empty
    """
    ...
```

### 5.3 Batch Operations

```python
def batch_store(entries: list[StoreRequest]) -> list[MemoryEntry]:
    """Atomic batch write. All entries are stored or none are."""
    ...

def batch_retrieve(keys: list[tuple[MemoryNamespace, str]]) -> list[Optional[MemoryEntry]]:
    """Retrieve multiple entries in a single call. Reduces round trips."""
    ...
```

### 5.4 Context Loading Helper

A higher-level function that bridges the memory layer and the context window.

```python
def load_relevant_context(
    task_description: str,
    token_budget: int = 100_000,
    namespace: MemoryNamespace = None,
) -> str:
    """
    Retrieve and format memory entries relevant to a task,
    fitting within a token budget.

    Procedure:
    1. Search memory for entries relevant to task_description.
    2. Rank by combined relevance + recency score.
    3. Greedily pack entries into the token budget, highest-ranked first.
    4. Format each entry with provenance metadata for in-context use.
    5. Append a summary line: "Loaded N memory entries (M tokens)."

    Safety properties:
    - Each entry in the output includes its source_type and confidence.
    - Entries with confidence < 0.5 are marked with a warning prefix.
    - The agent can distinguish verified facts from uncertain claims.

    Returns a formatted string ready for insertion into context.
    """
    ...
```

### 5.5 Audit Log Schema

```python
@dataclass
class AuditEvent:
    event_id: str
    timestamp: datetime
    agent_id: str
    session_id: str
    operation: str          # "store" | "retrieve" | "update" | "delete" | "search"
    namespace: str
    key: str
    detail: str             # Operation-specific detail (e.g., old content hash for updates)
    outcome: str            # "success" | "denied" | "error"
```

The audit log is append-only. No agent, including admins, can modify or delete audit entries. The log is the ground truth for forensic analysis of memory integrity.

---

## Appendix: Open Questions for Future Work

1. **Embedding model selection**: Which embedding model should back the `search` operation? Must balance retrieval quality against latency and cost.
2. **Compaction fidelity measurement**: How do we quantify information loss during compaction? Can we detect when compaction has dropped safety-critical context?
3. **Adversarial robustness**: How does this architecture hold up when a tool is actively trying to poison the memory (e.g., a compromised API returning subtly false data)?
4. **Memory capacity planning**: For long-running agents (hundreds of sessions), how should we manage memory growth? Aging policies, summarization of old episodic memories, and archival strategies need further study.
5. **Cross-model compatibility**: If the underlying model is swapped (e.g., from Opus to Sonnet for cost reasons), how do we ensure memory entries remain interpretable?
