# Shared vs. Distributed Memory Paradigms for Multi-Agent AI Systems

## A Safety Research Evaluation

_Safety Research System — March 2026_

---

## Executive Summary

As multi-agent AI systems move from research prototypes to production deployments — exemplified by Karpathy's [Autoresearch](https://github.com/karpathy/autoresearch) running 8 concurrent agents producing 110+ commits in 12 hours — the question of how agents share and manage memory becomes a first-order safety concern. This evaluation compares shared and distributed memory paradigms through the lens of safety research, drawing on the architectural framing proposed in [Yu et al. (arXiv 2603.10062)](https://arxiv.org/abs/2603.10062), which models multi-agent memory as a computer architecture problem with a three-layer hierarchy (I/O, cache, memory) and identifies critical gaps in cache sharing, access control, and consistency protocols.

The central finding is that **distributed memory with controlled sharing surfaces is the safer default**, but practical systems require hybrid approaches that combine per-agent isolation with explicit, auditable sharing mechanisms.

---

## 1. Shared Memory Paradigm

### 1.1 How It Works

In a shared memory architecture, all agents read from and write to a common memory store — a single vector database, document store, or key-value system. Every agent has equal visibility into the full memory space. This mirrors symmetric multiprocessing (SMP) in classical computing, where all processors access a unified address space.

In the AI agent context, shared memory typically manifests as:

- A single vector store (e.g., ChromaDB, Qdrant) that all agents query and update
- A shared file system or database where agents write findings and read each other's work
- A common context document (e.g., a shared markdown file or wiki) that agents collaboratively edit

### 1.2 Advantages

**Simple coordination.** Agents do not need explicit message-passing to share knowledge. If Agent A discovers a relevant fact, Agent B can immediately retrieve it from the shared store. This reduces the engineering overhead for inter-agent communication.

**Single source of truth.** There is one canonical version of every memory entry. There are no divergent copies to reconcile. If a fact is updated, all agents see the update on their next read.

**Lower storage overhead.** Shared knowledge is stored once rather than replicated across agents. For large knowledge bases, this can significantly reduce storage and embedding costs.

**Natural knowledge accumulation.** As agents work in parallel, the shared store becomes progressively richer. Later agents benefit from earlier agents' discoveries without explicit handoffs.

### 1.3 Disadvantages

**Write contention.** When multiple agents attempt to update the same memory concurrently, conflicts arise. Without locking or conflict resolution, agents overwrite each other's contributions. Yu et al. identify this as the core consistency challenge: "agents overwrite each other, read stale information, or rely on inconsistent versions of shared facts."

**Single point of failure.** If the shared store becomes corrupted or unavailable, all agents lose memory access simultaneously. There is no graceful degradation — the entire system stalls or operates without memory.

**Difficult access control.** In a flat shared space, enforcing granular permissions is complex. Which agent can read which memories? Can Agent A modify Agent B's entries? The access protocol — permissions, scope, granularity — remains under-specified in most current frameworks, as Yu et al. note.

**Noisy neighbor problem.** A malfunctioning agent that writes garbage to the shared store pollutes the memory for all other agents. There is no natural containment boundary.

**Scalability ceiling.** As agent count grows, contention on the shared store increases. Read-heavy workloads scale better than write-heavy ones, but hot spots in the memory space become bottlenecks.

### 1.4 Safety Implications

- **Information leakage is the default.** Every agent can see everything. If one agent processes sensitive data, that data is visible to all agents unless explicit filtering is added on top.
- **Corruption blast radius is maximal.** A single bad write can affect every agent in the system. Memory poisoning attacks — whether from a compromised agent or adversarial input — propagate system-wide.
- **Auditability is centralized but coarse.** A single audit log captures all operations, making it easy to collect but hard to attribute. Distinguishing which agent caused which state change requires careful logging of agent identity on every operation.
- **Rollback is all-or-nothing.** Rolling back a corrupted memory entry may require reverting changes from multiple agents, some of which may have been valid. Selective rollback is difficult without versioning per-entry per-agent.

---

## 2. Distributed Memory Paradigm

### 2.1 How It Works

In a distributed memory architecture, each agent maintains its own private memory store. Agents do not have direct access to each other's memory. Information sharing occurs through explicit message-passing, publish-subscribe mechanisms, or controlled synchronization protocols. This mirrors distributed computing systems (e.g., MPI) where each node has local memory and communicates through defined interfaces.

In the AI agent context, distributed memory typically manifests as:

- Per-agent JSON files, databases, or vector stores that only the owning agent reads and writes
- A message bus or event queue through which agents publish findings and subscribe to updates
- Periodic synchronization rounds where agents selectively export and import memory entries

### 2.2 Advantages

**Natural isolation.** Each agent's memory is a separate failure domain. A corrupted entry in Agent A's store does not affect Agent B. This containment is the single most important safety property for multi-agent systems.

**Fault tolerance.** If one agent's memory store fails, the other agents continue operating with their own stores. The system degrades gracefully rather than failing catastrophically.

**Inherent access boundaries.** Access control is the default rather than an overlay. Agents cannot read each other's memory without explicit sharing mechanisms. This enforces the principle of least privilege by default.

**Independent scaling.** Each agent's memory can be sized, indexed, and optimized independently. An agent doing heavy retrieval can use a vector database while a lightweight agent uses a simple key-value store.

**Easier provenance tracking.** Every memory entry has a clear owner. The causal chain — which agent created, modified, or consumed a given fact — is unambiguous.

### 2.3 Disadvantages

**Consistency challenges.** When agents need to share knowledge, ensuring all agents have a consistent view is nontrivial. The same fact may exist in different versions across agents, leading to contradictory reasoning. This is Yu et al.'s "most pressing open challenge."

**Synchronization overhead.** Explicit message-passing and synchronization protocols add latency and engineering complexity. Agents must implement serialization, conflict resolution, and retry logic.

**Knowledge duplication.** Common knowledge is replicated across agent stores, increasing storage costs and creating opportunities for divergence.

**Coordination difficulty.** Achieving consensus on shared goals or facts requires distributed coordination protocols, which are inherently more complex than reading from a shared store.

**Discovery problem.** An agent may not know that another agent already has relevant information. Without a directory or indexing layer over distributed stores, useful knowledge can remain siloed.

### 2.4 Safety Implications

- **Information leakage requires explicit action.** An agent cannot accidentally expose data to another agent. Sharing requires deliberate export through a defined interface, which can be logged, validated, and rate-limited.
- **Corruption blast radius is minimized.** A corrupted memory affects only its owning agent. Other agents are unaffected unless they explicitly import the corrupted data, and that import can be validated.
- **Auditability is naturally scoped.** Each agent's audit log covers only its own operations, making attribution trivial. Cross-agent interactions are captured at the message-passing layer, providing clear boundaries.
- **Rollback is per-agent.** Rolling back one agent's memory to a previous state does not affect other agents. This enables targeted recovery without system-wide disruption.

---

## 3. Hybrid Approaches

### 3.1 The Case for Hybrid Architecture

Neither pure paradigm is sufficient in practice. Pure shared memory sacrifices safety for convenience. Pure distributed memory sacrifices coordination efficiency for isolation. Real multi-agent systems — including Karpathy's Autoresearch, which used a shared Git repository as a coordination mechanism alongside per-agent execution environments — naturally gravitate toward hybrid designs.

### 3.2 Architecture: Per-Agent Local Memory + Shared Knowledge Base

The recommended hybrid structure consists of three tiers:

```
+------------------+     +------------------+     +------------------+
|    Agent A       |     |    Agent B       |     |    Agent C       |
|  +------------+  |     |  +------------+  |     |  +------------+  |
|  | Local      |  |     |  | Local      |  |     |  | Local      |  |
|  | Memory     |  |     |  | Memory     |  |     |  | Memory     |  |
|  | (private)  |  |     |  | (private)  |  |     |  | (private)  |  |
|  +-----+------+  |     |  +-----+------+  |     |  +-----+------+  |
|        |         |     |        |         |     |        |         |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         v                        v                        v
   +-----+------------------------+------------------------+-----+
   |              Message-Passing / Sync Layer                    |
   |  (publish/subscribe, validated transfers, access control)    |
   +-----+------------------------+------------------------+-----+
         |                        |                        |
         v                        v                        v
   +------------------------------------------------------------------+
   |                    Shared Knowledge Base                          |
   |  (read-heavy, append-mostly, versioned, access-controlled)       |
   |  - Validated facts      - Shared configurations                  |
   |  - Coordination state   - Cross-agent references                 |
   +------------------------------------------------------------------+
```

**Tier 1: Local Memory (Private).** Each agent maintains a private memory store for working state, intermediate results, hypotheses, and scratchpad content. This memory is not visible to other agents. It aligns with the "cache" layer in Yu et al.'s three-layer hierarchy.

**Tier 2: Message-Passing Layer.** Agents communicate through a structured synchronization layer that validates, logs, and rate-limits all inter-agent memory transfers. This layer enforces access control policies and provides the audit surface for cross-agent interactions.

**Tier 3: Shared Knowledge Base.** A common store holds validated, stable facts that have been explicitly promoted from local memory through the message-passing layer. This store is append-mostly and versioned. It aligns with the "memory" layer in Yu et al.'s hierarchy.

### 3.3 Promotion Protocol

The mechanism by which local memories become shared knowledge is critical for safety:

1. **Agent writes to local memory.** All initial writes are private.
2. **Agent promotes entry to shared store.** This requires the entry to pass validation (format, size, content checks) and the agent to have write permission for the target namespace.
3. **Promotion is logged.** The message-passing layer records the source agent, timestamp, content hash, and target namespace.
4. **Other agents read from shared store.** Reads are also logged with the requesting agent's identity.
5. **Conflicts are resolved explicitly.** If two agents promote conflicting facts, the system flags the conflict for resolution rather than silently accepting one version.

### 3.4 Mapping to Autoresearch

Karpathy's Autoresearch naturally exhibits this hybrid pattern:

| Component | Autoresearch Implementation |
|---|---|
| Local memory | Each agent's working directory and in-context state |
| Message-passing | Git commits with structured messages |
| Shared knowledge base | The shared Git repository (train.py + results) |
| Promotion protocol | Commit-and-push with the val_bpb metric as validation |
| Conflict resolution | Git merge conflicts (manual or automated) |

This is not a coincidence. Git is, in essence, a distributed version control system with explicit synchronization — the same pattern this evaluation recommends for agent memory.

---

## 4. Consistency Models

### 4.1 The Problem

When multiple agents read and write memory concurrently, the system must define what guarantees it provides about the visibility and ordering of those operations. This is the consistency model, and it is — as Yu et al. argue — the most pressing open challenge in multi-agent memory.

### 4.2 Strong Consistency

**Definition:** Every read returns the most recent write. All agents see the same state at all times.

**Mechanism:** Requires synchronous coordination — a global lock, a consensus protocol (e.g., Paxos, Raft), or serialized access through a single writer.

**Implications for agent memory:**
- Highest correctness guarantees — agents never reason from stale data
- Highest latency cost — every write must be acknowledged by the coordination layer before becoming visible
- Lowest throughput — agents block waiting for consistency checks
- Most brittle — if the coordination layer fails, the entire system stalls

**When to use:** Safety-critical shared state where stale reads could cause harm. Examples: agent role assignments, safety policy parameters, kill-switch state.

### 4.3 Eventual Consistency

**Definition:** After a write, all agents will eventually see the update, but reads may return stale data in the interim.

**Mechanism:** Agents write to local stores and synchronize asynchronously. Conflicts are detected and resolved after the fact.

**Implications for agent memory:**
- Lower latency — writes are locally acknowledged
- Higher throughput — agents operate independently most of the time
- More resilient — agents continue working during network partitions or synchronization failures
- Requires conflict resolution — divergent state must be detected and reconciled

**When to use:** Knowledge accumulation, research findings, intermediate results — any state where brief staleness is tolerable and conflicts are resolvable.

### 4.4 CAP Theorem Implications

The CAP theorem states that a distributed system can provide at most two of three guarantees: Consistency, Availability, and Partition tolerance. For multi-agent AI systems:

- **Partition tolerance is non-negotiable.** Agents may lose connectivity to the shared store, to each other, or to external services. The system must handle this gracefully.
- **The real trade-off is Consistency vs. Availability.** A CP system (consistent + partition-tolerant) will refuse to serve reads/writes during a partition to maintain consistency. An AP system (available + partition-tolerant) will continue operating but may serve stale data.

**Recommendation for safety research:** Use a **tiered consistency model** that matches the consistency guarantee to the criticality of the data:

| Data Category | Consistency Model | Example |
|---|---|---|
| Safety-critical state | Strong (CP) | Agent permissions, safety policies, kill switches |
| Coordination state | Causal | Task assignments, dependency graphs |
| Research findings | Eventual (AP) | Experimental results, intermediate analyses |
| Working memory | None (local only) | Agent scratchpad, hypotheses in progress |

This tiered approach avoids paying the performance cost of strong consistency for data that does not require it, while ensuring that safety-critical state is always consistent.

### 4.5 Versioning as a Consistency Primitive

Regardless of the consistency model, **versioning** should be a first-class primitive in any multi-agent memory system. Every memory entry should carry:

- A monotonically increasing version number
- A reference to its parent version (for conflict detection)
- A content hash (for integrity verification)
- A vector clock or Lamport timestamp (for causal ordering across agents)

This enables the system to detect conflicts, trace causal chains, and support rollback — capabilities that are essential for safety regardless of the consistency model chosen.

---

## 5. Safety Analysis

### 5.1 Which Paradigm Is Safer by Default?

**Distributed memory is safer by default.** The reasoning is straightforward:

1. **Principle of least privilege.** Distributed memory enforces isolation by default; sharing requires explicit action. Shared memory grants full access by default; restriction requires explicit action. Security engineering consistently shows that "secure by default" systems are safer than "secure by configuration" systems.

2. **Blast radius containment.** In distributed memory, a failure in one agent's memory affects only that agent. In shared memory, a failure can propagate to all agents.

3. **Audit surface.** In distributed memory, every cross-agent data flow passes through an explicit interface that can be logged and validated. In shared memory, data flows are implicit reads from a common store, making unauthorized access indistinguishable from authorized access without fine-grained logging.

### 5.2 Information Leakage

| Aspect | Shared Memory | Distributed Memory |
|---|---|---|
| Default visibility | All agents see all data | No agent sees another's data |
| Leakage mechanism | Direct read from shared store | Requires explicit export/import |
| Mitigation difficulty | Must implement and enforce ACLs | Isolation is structural |
| Residual risk | ACL misconfiguration exposes data | Over-sharing through sync layer |

The [Collaborative Memory framework (Rezazadeh et al., 2025)](https://arxiv.org/abs/2505.18279) addresses shared-memory leakage through dynamic bipartite access graphs, but this adds substantial complexity. Distributed memory achieves comparable isolation with simpler mechanisms.

### 5.3 Memory Corruption Blast Radius

| Scenario | Shared Memory | Distributed Memory |
|---|---|---|
| Single corrupted entry | All agents may read and act on it | Only the owning agent is affected |
| Poisoning attack | System-wide impact | Contained to target agent |
| Cascading corruption | High risk (corrupt entry informs writes by other agents) | Low risk (corruption does not cross agent boundaries unless explicitly shared) |
| Detection difficulty | Must distinguish legitimate updates from corruption across all agents | Scope of investigation limited to one agent |

### 5.4 Auditability

| Aspect | Shared Memory | Distributed Memory |
|---|---|---|
| Audit log location | Centralized | Per-agent + cross-agent sync layer |
| Attribution | Requires agent ID on every operation | Ownership is structural |
| Cross-agent causality | Implicit (hard to trace) | Explicit (captured at sync boundaries) |
| Log tampering risk | Single log to protect | Multiple logs; compromise of one does not affect others |

### 5.5 Rollback Capabilities

| Aspect | Shared Memory | Distributed Memory |
|---|---|---|
| Granularity | Per-entry (but entangled with other agents' state) | Per-agent (clean isolation) |
| Side effects | Rolling back entry X may invalidate Agent B's decisions based on X | Rolling back Agent A has no effect on Agent B |
| Complexity | Requires dependency tracking across agents | Simple: restore agent's store to a prior snapshot |
| Partial rollback | Difficult — must identify all downstream effects | Natural — each agent is an independent rollback unit |

### 5.6 Threat Model Summary

For a multi-agent system running safety research, the primary threats to memory are:

1. **Accidental corruption.** An agent writes malformed or incorrect data due to a bug or hallucination. Distributed memory contains this to a single agent.

2. **Adversarial manipulation.** An external attacker or compromised agent attempts to poison the memory to influence other agents' behavior. Distributed memory limits the attack surface to explicit sharing interfaces.

3. **Information exfiltration.** Sensitive data in one agent's memory is accessed by an unauthorized agent. Distributed memory prevents this structurally; shared memory relies on ACL enforcement.

4. **Consistency violation.** Agents operate on contradictory information, leading to incoherent system behavior. This is a risk in both paradigms, but distributed memory makes inconsistency explicit (agents have visibly different state) rather than implicit (agents read different versions from a shared store depending on timing).

---

## 6. Recommendation

### For a safety research system: Distributed memory with controlled sharing surfaces.

The recommendation is a hybrid architecture that defaults to distributed memory and adds sharing through explicit, auditable channels. Concretely:

### 6.1 Architecture

1. **Each agent gets a private memory store** (per the design in `memory-persistence-design.md`). This store is the agent's sole source of truth for its own state. It uses atomic writes, WAL, checksums, and per-agent audit logging.

2. **A shared knowledge base** holds validated, promoted facts. Writes to this store go through a promotion protocol that validates content, checks permissions, logs the operation, and detects conflicts.

3. **A message-passing layer** mediates all cross-agent communication. Every message is logged with source agent, destination agent, timestamp, and content hash.

4. **A tiered consistency model** applies strong consistency only to safety-critical state (permissions, policies, kill switches) and eventual consistency to research findings and coordination state.

### 6.2 Why This Approach

- **Safe by default.** Agent isolation is structural, not configurational. A new agent added to the system has zero access to other agents' memory until explicitly granted.
- **Auditable by construction.** Every cross-agent data flow passes through a logged interface. The audit trail captures not just what happened, but the causal chain of why.
- **Rollback-friendly.** Each agent can be independently rolled back without affecting the rest of the system. The shared knowledge base is versioned and append-mostly, supporting point-in-time recovery.
- **Incrementally adoptable.** The architecture starts simple (per-agent JSON files + a shared directory with file locking) and scales to more sophisticated backends (SQLite, vector databases, dedicated memory services) without changing the inter-agent contract.
- **Consistent with proven patterns.** This architecture mirrors Git's model (local commits + explicit push/pull), which Autoresearch already demonstrated at scale with 8 concurrent agents.

### 6.3 Implementation Priority

| Priority | Component | Rationale |
|---|---|---|
| P0 | Per-agent private memory stores with checksums and audit logs | Foundation; already prototyped in `memory_store.py` |
| P0 | Agent identity and basic access control | Required for any multi-agent deployment |
| P1 | Promotion protocol with validation and conflict detection | Enables safe sharing without sacrificing isolation |
| P1 | Tiered consistency model (strong for safety state, eventual for findings) | Balances safety with performance |
| P2 | Vector clock / causal ordering for cross-agent events | Enables debugging and root-cause analysis |
| P2 | Semantic search over the shared knowledge base | Improves agent discovery of relevant shared facts |
| P3 | Formal verification of consistency guarantees | Long-term reliability investment |

### 6.4 Open Questions

1. **Cache sharing across agents.** Yu et al. identify this as a critical gap. In the hybrid model, should agents share a cache layer (e.g., a shared embedding cache for common queries) even while keeping primary memory distributed? This could improve latency without significantly compromising isolation, but the access control and invalidation semantics need careful design.

2. **Consistency model for promoted facts.** When Agent A promotes a fact that contradicts a fact previously promoted by Agent B, what is the resolution policy? Options include last-writer-wins (simple but lossy), version branching (preserves both but adds complexity), and quorum-based resolution (robust but requires multiple agents to validate).

3. **Memory garbage collection.** In a long-running multi-agent system, stale entries accumulate. What is the safe deletion policy? Tombstoning (marking as deleted but retaining) preserves audit trails but increases storage. Hard deletion reduces storage but loses provenance.

4. **Cross-system memory.** As multi-agent systems interact with external tools and services, the memory boundary extends beyond agents. How should tool outputs, API responses, and external state be integrated into the agent memory hierarchy?

---

## References

- Yu, Z. et al. (2026). "Multi-Agent Memory from a Computer Architecture Perspective: Visions and Challenges Ahead." [arXiv:2603.10062](https://arxiv.org/abs/2603.10062)
- Karpathy, A. (2026). "Autoresearch: AI agents running research on single-GPU nanochat training automatically." [GitHub](https://github.com/karpathy/autoresearch)
- Rezazadeh, A. et al. (2025). "Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control." [arXiv:2505.18279](https://arxiv.org/abs/2505.18279)
- Karpathy Autoresearch analysis. [Context Studios](https://www.contextstudios.ai/blog/karpathy-autoresearch-prompt-replaces-paper)
- Karpathy Autoresearch analysis. [Substack](https://kenhuangus.substack.com/p/exploring-andrej-karpathys-autoresearch)
- Multi-Agent Coordination: Understanding the Limits. [ChatBotKit](https://chatbotkit.com/guides/multi-agent-coordination-guide)
