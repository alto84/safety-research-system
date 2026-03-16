# Multi-Session Memory Persistence for AI Agents

## Design Document

_Safety Research System — March 2026_

---

## 1. Overview

This document describes a prototype for **multi-session memory persistence** in agentic AI systems. The goal is to give AI agents a durable, auditable memory layer that survives session boundaries, supports multi-agent coordination, and maintains strong safety invariants.

### Why External Persistence?

Claude's 1M-token context window (GA as of March 2026) is powerful but insufficient for full memory persistence:

| Limitation | Why persistence helps |
|---|---|
| **Session boundary** | Context is lost when a session ends. Persistence allows memory to carry across sessions. |
| **Multi-agent sharing** | Two agents cannot share a context window. A shared store enables coordinated memory. |
| **Auditability** | In-context memory is opaque. An external store provides a full audit trail. |
| **Selective recall** | Loading 1M tokens has >2 min prefill latency. Selective retrieval is faster and cheaper. |
| **Integrity verification** | External stores can apply checksums; context windows cannot. |

### Design Principles

1. **Safety first** — every operation is logged, checksummed, and access-controlled.
2. **Simplicity** — stdlib-only Python, file-based JSON storage, no hidden magic.
3. **Auditability** — full read/write/delete audit trail with timestamps and agent IDs.
4. **Incremental complexity** — start simple (JSON files), upgrade later (SQLite, vector DB).

---

## 2. Storage Backend

### Current: File-Based JSON

The prototype uses a single JSON file per memory store, written atomically:

```
data/
  memories.json          # primary memory store
  memories.json.wal      # write-ahead log (append-only)
  audit.jsonl            # append-only audit log
```

**Atomic write strategy:**
1. Write new state to a temporary file (`memories.json.tmp.<pid>`)
2. `fsync` the temporary file
3. Rename temp file over the target (atomic on POSIX)

This prevents corruption from crashes mid-write.

### Future: SQLite

SQLite provides ACID transactions, indexing, and concurrent reads without external dependencies (Python ships `sqlite3` in stdlib). Migration path:

- Same `MemoryEntry` schema maps directly to a table
- Write-ahead log becomes SQLite WAL mode
- Audit log becomes a second table with foreign keys

### Future: Vector Database

For semantic search over memory content, a vector database (e.g., ChromaDB, Qdrant) can be layered on:

- Embed memory content at write time
- Store embeddings alongside the JSON/SQLite record
- Query by cosine similarity for semantic retrieval
- Keep the file-based store as the source of truth; the vector index is a derived cache

---

## 3. Memory Schema

Each memory entry contains:

| Field | Type | Description |
|---|---|---|
| `id` | `str` (UUID4) | Unique identifier for the memory |
| `content` | `str` | The memory payload (text only, max 100 KB) |
| `metadata` | `dict[str, str]` | User-defined key-value tags (string values only) |
| `agent_id` | `str` | Identifier of the agent that created the memory |
| `session_id` | `str` | Session in which the memory was created |
| `created_at` | `str` (ISO 8601) | Creation timestamp |
| `updated_at` | `str` (ISO 8601) | Last modification timestamp |
| `access_count` | `int` | Number of times this memory has been read |
| `checksum` | `str` (SHA-256) | Integrity hash over `content + agent_id + session_id + created_at` |

### Why String-Only Metadata?

Arbitrary nested objects in metadata create deserialization risks and complicate validation. String-only values are trivially serializable, comparable, and safe from injection.

### Content Safety

Memory content is restricted to UTF-8 text. The following are rejected:

- Content exceeding 100 KB
- Content containing null bytes
- Empty content strings

No executable code, pickled objects, or binary blobs are stored in the content field.

---

## 4. Safety Features

### 4.1 Write-Ahead Logging (WAL)

Before any mutation (store, update, delete), the operation is appended to `memories.json.wal` as a single JSON line:

```json
{"op": "store", "entry_id": "abc-123", "timestamp": "2026-03-16T12:00:00Z", "agent_id": "agent-1"}
```

If a crash occurs between the WAL write and the main store write, recovery replays the WAL. This guarantees that acknowledged writes are durable.

### 4.2 SHA-256 Checksums

Every memory entry carries a SHA-256 checksum computed over the concatenation of `content`, `agent_id`, `session_id`, and `created_at`. On every read, the checksum is recomputed and verified. If verification fails, the entry is flagged as corrupted in the audit log.

### 4.3 Audit Trail

All operations are recorded in an append-only JSONL audit log:

```json
{"timestamp": "...", "operation": "store", "entry_id": "...", "agent_id": "...", "session_id": "...", "details": "..."}
```

Operations logged: `store`, `retrieve`, `search`, `update`, `delete`, `verify_fail`, `merge_sessions`.

The audit log is never truncated or modified by the application. External log rotation is recommended for long-running deployments.

### 4.4 Access Control

The prototype enforces agent-scoped access:

- An agent can only **update** or **delete** memories it created (matching `agent_id`)
- Any agent can **read** any memory (read access is logged)
- Session merge requires the requesting agent to own all memories in the source session

These rules are enforced at the application layer. A production system would add authentication and cryptographic agent identity.

### 4.5 Input Validation

All public methods validate inputs before processing:

- `agent_id` and `session_id` must be non-empty strings matching `[a-zA-Z0-9_-]+`
- `content` must be a non-empty string under 100 KB with no null bytes
- `metadata` keys and values must be strings
- `id` fields must be valid UUID4 strings where applicable

---

## 5. Retrieval Strategies

### 5.1 Exact Match

Retrieve a memory by its UUID. O(1) lookup in the in-memory dict. Checksum is verified on retrieval.

### 5.2 Metadata Filter

Retrieve all memories where metadata contains specified key-value pairs. Useful for tag-based organization:

```python
store.search(agent_id="agent-1", metadata_filter={"topic": "safety"})
```

### 5.3 Recency-Weighted

Return memories sorted by `updated_at` descending, with an optional limit. This favors recent context, which is typically more relevant for agentic workflows.

### 5.4 Semantic Search (Placeholder)

The `search()` method accepts an optional `query` string parameter. In this prototype, it falls back to substring matching. The interface is designed so that a future implementation can:

1. Embed the query using an embedding model
2. Compare against pre-computed embeddings stored alongside entries
3. Return results ranked by cosine similarity

The method signature will not change; only the internal implementation will be swapped.

---

## 6. Session Management

### List by Session

```python
entries = store.search(session_id="session-42")
```

Returns all memories created in a given session, sorted by creation time.

### Merge Sessions

```python
store.merge_sessions(source_session_id="old", target_session_id="new", agent_id="agent-1")
```

Moves all memories from the source session to the target session. The agent must own all memories in the source session. This is useful when an agent resumes work across session boundaries and wants to unify its memory.

---

## 7. Concurrency Model

This prototype is **single-process, single-threaded**. The atomic write strategy (temp file + rename) provides crash safety but not concurrent writer safety.

For multi-agent deployments, the recommended upgrade path is:

1. **Short term:** File locking (`fcntl.flock`) around write operations
2. **Medium term:** SQLite with WAL mode (concurrent readers, serialized writers)
3. **Long term:** A dedicated memory service with proper transactional semantics

---

## 8. File Layout

```
safety-research-system/
  memory_store.py                 # Python module (this prototype)
  memory-persistence-design.md    # This document
  research-notes.md               # Project research notes
  data/                           # Created at runtime
    memories.json                 # Primary store
    memories.json.wal             # Write-ahead log
    audit.jsonl                   # Audit trail
```

---

## 9. References

- [Claude 1M context GA](https://claude.com/blog/1m-context-ga) — context window capabilities and limitations
- [ArXiv 2603.10062](https://arxiv.org/abs/2603.10062) — multi-agent memory from a computer architecture perspective
- [Karpathy Autoresearch](https://www.contextstudios.ai/blog/karpathy-autoresearch-prompt-replaces-paper) — multi-agent autonomous systems in practice
