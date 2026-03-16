"""
Multi-Session Memory Persistence for AI Agents.

A safety-focused, auditable memory store for agentic AI systems.
Provides cross-session and cross-agent memory with integrity verification,
write-ahead logging, and full audit trails.

Uses only Python stdlib. No external dependencies.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CONTENT_BYTES: int = 100 * 1024  # 100 KB
MAX_METADATA_KEYS: int = 64
MAX_METADATA_VALUE_BYTES: int = 4096
ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class MemoryStoreError(Exception):
    """Base exception for all memory store errors."""


class ValidationError(MemoryStoreError):
    """Raised when input validation fails."""


class IntegrityError(MemoryStoreError):
    """Raised when a checksum verification fails."""


class AccessDeniedError(MemoryStoreError):
    """Raised when an agent attempts an unauthorised operation."""


class EntryNotFoundError(MemoryStoreError):
    """Raised when a requested memory entry does not exist."""


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------


@dataclass
class MemoryEntry:
    """A single memory record with full provenance metadata."""

    id: str
    content: str
    metadata: dict[str, str]
    agent_id: str
    session_id: str
    created_at: str
    updated_at: str
    access_count: int = 0
    checksum: str = ""

    def compute_checksum(self) -> str:
        """Compute SHA-256 over the integrity-critical fields."""
        payload = (
            self.content + self.agent_id + self.session_id + self.created_at
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def verify(self) -> bool:
        """Return True if the stored checksum matches the computed one."""
        return self.checksum == self.compute_checksum()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        return cls(**data)


@dataclass
class AuditRecord:
    """A single audit-log entry."""

    timestamp: str
    operation: str
    entry_id: str
    agent_id: str
    session_id: str
    details: str = ""

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------


def _validate_identifier(value: str, name: str) -> None:
    """Validate that *value* is a non-empty string of safe characters."""
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{name} must be a non-empty string")
    if not ID_PATTERN.match(value):
        raise ValidationError(
            f"{name} must match [a-zA-Z0-9_-]+, got: {value!r}"
        )


def _validate_content(content: str) -> None:
    """Validate memory content against safety constraints."""
    if not isinstance(content, str):
        raise ValidationError("content must be a string")
    if not content:
        raise ValidationError("content must not be empty")
    if "\x00" in content:
        raise ValidationError("content must not contain null bytes")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        raise ValidationError(
            f"content exceeds maximum size of {MAX_CONTENT_BYTES} bytes"
        )


def _validate_metadata(metadata: dict[str, str]) -> None:
    """Validate that metadata is a dict of string->string pairs."""
    if not isinstance(metadata, dict):
        raise ValidationError("metadata must be a dict")
    if len(metadata) > MAX_METADATA_KEYS:
        raise ValidationError(
            f"metadata must have at most {MAX_METADATA_KEYS} keys"
        )
    for k, v in metadata.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise ValidationError(
                f"metadata keys and values must be strings, got: {type(k).__name__} -> {type(v).__name__}"
            )
        if len(v.encode("utf-8")) > MAX_METADATA_VALUE_BYTES:
            raise ValidationError(
                f"metadata value for key {k!r} exceeds {MAX_METADATA_VALUE_BYTES} bytes"
            )


# ---------------------------------------------------------------------------
# Memory Store
# ---------------------------------------------------------------------------


class MemoryStore:
    """File-backed memory store with audit logging and integrity checks.

    All mutations are preceded by a write-ahead log entry and followed
    by an atomic file write (write-to-temp then rename).

    Parameters
    ----------
    data_dir:
        Directory where ``memories.json``, the WAL, and the audit log
        are stored.  Created automatically if it does not exist.
    """

    def __init__(self, data_dir: str | Path = "data") -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._store_path = self._data_dir / "memories.json"
        self._wal_path = self._data_dir / "memories.json.wal"
        self._audit_path = self._data_dir / "audit.jsonl"

        # In-memory index: id -> MemoryEntry
        self._entries: dict[str, MemoryEntry] = {}

        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load the memory store from disk, replaying the WAL if needed."""
        if self._store_path.exists():
            raw = self._store_path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw) if raw.strip() else {}
            for entry_data in data.get("entries", []):
                entry = MemoryEntry.from_dict(entry_data)
                self._entries[entry.id] = entry

        # Replay WAL — each line is a JSON mutation record.  In this
        # simple prototype the WAL only records *intent*; the actual
        # entry data is in the main store.  A production system would
        # store full payloads in the WAL for crash recovery.
        if self._wal_path.exists():
            self._flush()  # Persist current state and clear WAL

    def _flush(self) -> None:
        """Atomically write the in-memory state to disk and clear the WAL."""
        data = {
            "version": 1,
            "entry_count": len(self._entries),
            "entries": [e.to_dict() for e in self._entries.values()],
        }
        self._atomic_write(self._store_path, json.dumps(data, indent=2, ensure_ascii=False))

        # Clear the WAL now that the main store is up-to-date.
        if self._wal_path.exists():
            self._wal_path.unlink()

    def _atomic_write(self, target: Path, content: str) -> None:
        """Write *content* to *target* atomically via temp-file + rename."""
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._data_dir), prefix=target.name + ".tmp.", suffix=""
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(target))
        except BaseException:
            # Clean up temp file on failure.
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _append_wal(self, operation: str, entry_id: str, agent_id: str) -> None:
        """Append a write-ahead log record."""
        record = {
            "op": operation,
            "entry_id": entry_id,
            "timestamp": _now_iso(),
            "agent_id": agent_id,
        }
        with open(self._wal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _append_audit(self, record: AuditRecord) -> None:
        """Append an audit record to the append-only audit log."""
        with open(self._audit_path, "a", encoding="utf-8") as f:
            f.write(record.to_json_line() + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _audit(
        self,
        operation: str,
        entry_id: str,
        agent_id: str,
        session_id: str = "",
        details: str = "",
    ) -> None:
        record = AuditRecord(
            timestamp=_now_iso(),
            operation=operation,
            entry_id=entry_id,
            agent_id=agent_id,
            session_id=session_id,
            details=details,
        )
        self._append_audit(record)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(
        self,
        content: str,
        agent_id: str,
        session_id: str,
        metadata: Optional[dict[str, str]] = None,
    ) -> MemoryEntry:
        """Create a new memory entry.

        Parameters
        ----------
        content:
            The text content to store (max 100 KB, no null bytes).
        agent_id:
            Identifier of the agent creating this memory.
        session_id:
            Identifier of the current session.
        metadata:
            Optional string-to-string tags.

        Returns
        -------
        The newly created ``MemoryEntry`` with its computed checksum.
        """
        _validate_identifier(agent_id, "agent_id")
        _validate_identifier(session_id, "session_id")
        _validate_content(content)
        if metadata is None:
            metadata = {}
        _validate_metadata(metadata)

        now = _now_iso()
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            metadata=metadata,
            agent_id=agent_id,
            session_id=session_id,
            created_at=now,
            updated_at=now,
            access_count=0,
        )
        entry.checksum = entry.compute_checksum()

        # WAL -> mutate -> flush
        self._append_wal("store", entry.id, agent_id)
        self._entries[entry.id] = entry
        self._flush()
        self._audit("store", entry.id, agent_id, session_id)

        return entry

    def retrieve(self, entry_id: str, agent_id: str) -> MemoryEntry:
        """Retrieve a memory entry by ID, verifying its integrity.

        Parameters
        ----------
        entry_id:
            The UUID of the memory to retrieve.
        agent_id:
            The agent requesting access (logged for audit).

        Returns
        -------
        The ``MemoryEntry``.

        Raises
        ------
        EntryNotFoundError
            If no entry with the given ID exists.
        IntegrityError
            If the checksum verification fails.
        """
        _validate_identifier(agent_id, "agent_id")

        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"No entry with id {entry_id!r}")

        if not entry.verify():
            self._audit(
                "verify_fail", entry_id, agent_id, entry.session_id,
                details="checksum mismatch on retrieve",
            )
            raise IntegrityError(
                f"Checksum verification failed for entry {entry_id!r}"
            )

        entry.access_count += 1
        entry.updated_at = _now_iso()
        self._flush()
        self._audit("retrieve", entry_id, agent_id, entry.session_id)

        return entry

    def search(
        self,
        agent_id: str,
        *,
        session_id: Optional[str] = None,
        metadata_filter: Optional[dict[str, str]] = None,
        query: Optional[str] = None,
        limit: int = 50,
        sort_by_recency: bool = True,
    ) -> list[MemoryEntry]:
        """Search memories by session, metadata, or text query.

        Parameters
        ----------
        agent_id:
            The agent performing the search (logged for audit).
        session_id:
            If given, restrict results to this session.
        metadata_filter:
            If given, only return entries whose metadata contains all
            specified key-value pairs.
        query:
            If given, perform substring matching on content.  This is a
            placeholder for future semantic search.
        limit:
            Maximum number of results to return.
        sort_by_recency:
            If True, sort results by ``updated_at`` descending.

        Returns
        -------
        A list of matching ``MemoryEntry`` objects.
        """
        _validate_identifier(agent_id, "agent_id")
        if session_id is not None:
            _validate_identifier(session_id, "session_id")
        if metadata_filter is not None:
            _validate_metadata(metadata_filter)

        results: list[MemoryEntry] = []

        for entry in self._entries.values():
            # Session filter
            if session_id is not None and entry.session_id != session_id:
                continue

            # Metadata filter
            if metadata_filter is not None:
                if not all(
                    entry.metadata.get(k) == v
                    for k, v in metadata_filter.items()
                ):
                    continue

            # Substring query (placeholder for semantic search)
            if query is not None:
                if query.lower() not in entry.content.lower():
                    continue

            results.append(entry)

        if sort_by_recency:
            results.sort(key=lambda e: e.updated_at, reverse=True)

        results = results[:limit]

        self._audit(
            "search", "", agent_id,
            session_id or "",
            details=f"returned {len(results)} results",
        )

        return results

    def update(
        self,
        entry_id: str,
        agent_id: str,
        *,
        content: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> MemoryEntry:
        """Update the content or metadata of an existing memory.

        Only the agent that created the memory may update it.

        Parameters
        ----------
        entry_id:
            The UUID of the memory to update.
        agent_id:
            The agent requesting the update (must match the entry's creator).
        content:
            New content string, if updating content.
        metadata:
            New metadata dict, if updating metadata.

        Returns
        -------
        The updated ``MemoryEntry``.
        """
        _validate_identifier(agent_id, "agent_id")

        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"No entry with id {entry_id!r}")

        if entry.agent_id != agent_id:
            raise AccessDeniedError(
                f"Agent {agent_id!r} cannot update entry owned by {entry.agent_id!r}"
            )

        if content is not None:
            _validate_content(content)
            entry.content = content

        if metadata is not None:
            _validate_metadata(metadata)
            entry.metadata = metadata

        entry.updated_at = _now_iso()
        entry.checksum = entry.compute_checksum()

        self._append_wal("update", entry_id, agent_id)
        self._flush()
        self._audit("update", entry_id, agent_id, entry.session_id)

        return entry

    def delete(self, entry_id: str, agent_id: str) -> None:
        """Delete a memory entry.

        Only the agent that created the memory may delete it.

        Parameters
        ----------
        entry_id:
            The UUID of the memory to delete.
        agent_id:
            The agent requesting deletion (must match the entry's creator).
        """
        _validate_identifier(agent_id, "agent_id")

        entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"No entry with id {entry_id!r}")

        if entry.agent_id != agent_id:
            raise AccessDeniedError(
                f"Agent {agent_id!r} cannot delete entry owned by {entry.agent_id!r}"
            )

        session_id = entry.session_id

        self._append_wal("delete", entry_id, agent_id)
        del self._entries[entry_id]
        self._flush()
        self._audit("delete", entry_id, agent_id, session_id)

    def merge_sessions(
        self, source_session_id: str, target_session_id: str, agent_id: str
    ) -> int:
        """Move all memories from one session to another.

        The requesting agent must own every memory in the source session.

        Parameters
        ----------
        source_session_id:
            The session to merge from.
        target_session_id:
            The session to merge into.
        agent_id:
            The agent requesting the merge.

        Returns
        -------
        The number of memories moved.
        """
        _validate_identifier(source_session_id, "source_session_id")
        _validate_identifier(target_session_id, "target_session_id")
        _validate_identifier(agent_id, "agent_id")

        if source_session_id == target_session_id:
            raise ValidationError("source and target sessions must differ")

        # Collect entries in the source session
        source_entries = [
            e for e in self._entries.values()
            if e.session_id == source_session_id
        ]

        if not source_entries:
            return 0

        # Verify ownership
        for entry in source_entries:
            if entry.agent_id != agent_id:
                raise AccessDeniedError(
                    f"Agent {agent_id!r} does not own entry {entry.id!r} "
                    f"(owned by {entry.agent_id!r}) in source session"
                )

        # Perform the merge
        self._append_wal("merge_sessions", source_session_id, agent_id)
        now = _now_iso()
        for entry in source_entries:
            entry.session_id = target_session_id
            entry.updated_at = now
            entry.checksum = entry.compute_checksum()

        self._flush()
        self._audit(
            "merge_sessions", source_session_id, agent_id, target_session_id,
            details=f"moved {len(source_entries)} entries from {source_session_id} to {target_session_id}",
        )

        return len(source_entries)

    def get_audit_log(
        self,
        *,
        entry_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, str]]:
        """Read and filter the audit log.

        Parameters
        ----------
        entry_id:
            If given, only return records for this entry.
        agent_id:
            If given, only return records for this agent.
        operation:
            If given, only return records for this operation type.
        limit:
            Maximum number of records to return (most recent first).

        Returns
        -------
        A list of audit record dicts, most recent first.
        """
        records: list[dict[str, str]] = []

        if not self._audit_path.exists():
            return records

        with open(self._audit_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if entry_id is not None and record.get("entry_id") != entry_id:
                    continue
                if agent_id is not None and record.get("agent_id") != agent_id:
                    continue
                if operation is not None and record.get("operation") != operation:
                    continue

                records.append(record)

        # Most recent first
        records.reverse()
        return records[:limit]

    def verify_all(self, agent_id: str) -> list[str]:
        """Verify checksums on all entries.

        Parameters
        ----------
        agent_id:
            The agent performing the verification (for audit).

        Returns
        -------
        A list of entry IDs that failed verification.
        """
        _validate_identifier(agent_id, "agent_id")
        failed: list[str] = []

        for entry_id, entry in self._entries.items():
            if not entry.verify():
                failed.append(entry_id)
                self._audit(
                    "verify_fail", entry_id, agent_id, entry.session_id,
                    details="checksum mismatch during bulk verify",
                )

        self._audit(
            "verify_all", "", agent_id, "",
            details=f"checked {len(self._entries)} entries, {len(failed)} failed",
        )

        return failed

    @property
    def entry_count(self) -> int:
        """Return the number of entries in the store."""
        return len(self._entries)

    def list_sessions(self) -> list[str]:
        """Return a sorted list of all distinct session IDs."""
        return sorted({e.session_id for e in self._entries.values()})


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------


def _demo() -> None:
    """Run a short demonstration of the memory store."""
    import shutil

    demo_dir = Path("data_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)

    store = MemoryStore(data_dir=demo_dir)
    print("=== Memory Store Demo ===\n")

    # Store some memories
    e1 = store.store(
        content="The agent discovered that retry logic reduces API failures by 40%.",
        agent_id="agent-1",
        session_id="session-1",
        metadata={"topic": "reliability", "priority": "high"},
    )
    print(f"Stored: {e1.id[:8]}... -> {e1.content[:60]}...")

    e2 = store.store(
        content="User prefers concise responses under 200 words.",
        agent_id="agent-1",
        session_id="session-1",
        metadata={"topic": "preferences"},
    )
    print(f"Stored: {e2.id[:8]}... -> {e2.content[:60]}...")

    e3 = store.store(
        content="Multi-agent coordination requires shared memory with access control.",
        agent_id="agent-2",
        session_id="session-2",
        metadata={"topic": "architecture"},
    )
    print(f"Stored: {e3.id[:8]}... -> {e3.content[:60]}...")

    # Retrieve with integrity check
    print(f"\nRetrieving {e1.id[:8]}...")
    retrieved = store.retrieve(e1.id, agent_id="agent-1")
    print(f"  Content: {retrieved.content}")
    print(f"  Checksum verified: {retrieved.verify()}")
    print(f"  Access count: {retrieved.access_count}")

    # Search by metadata
    print("\nSearching for topic='reliability'...")
    results = store.search("agent-1", metadata_filter={"topic": "reliability"})
    print(f"  Found {len(results)} result(s)")

    # Search by query (substring)
    print("\nSearching for query='memory'...")
    results = store.search("agent-1", query="memory")
    for r in results:
        print(f"  {r.id[:8]}... -> {r.content[:60]}...")

    # Search by session
    print("\nListing session-1 memories...")
    results = store.search("agent-1", session_id="session-1")
    print(f"  Found {len(results)} entries in session-1")

    # Update
    print(f"\nUpdating {e2.id[:8]}...")
    updated = store.update(
        e2.id, "agent-1",
        content="User prefers concise responses under 150 words.",
    )
    print(f"  New content: {updated.content}")

    # Merge sessions
    print("\nMerging session-1 into session-3...")
    moved = store.merge_sessions("session-1", "session-3", "agent-1")
    print(f"  Moved {moved} entries")
    print(f"  Sessions now: {store.list_sessions()}")

    # Delete
    print(f"\nDeleting {e1.id[:8]}...")
    store.delete(e1.id, "agent-1")
    print(f"  Entry count: {store.entry_count}")

    # Verify all
    print("\nRunning integrity check...")
    failures = store.verify_all("agent-1")
    print(f"  Failures: {len(failures)}")

    # Audit log
    print("\nRecent audit log:")
    for record in store.get_audit_log(limit=5):
        print(f"  [{record['timestamp']}] {record['operation']:15s} "
              f"entry={record['entry_id'][:8] if record['entry_id'] else '(none)':10s} "
              f"agent={record['agent_id']}")

    # Cleanup
    shutil.rmtree(demo_dir)
    print("\nDemo complete. Cleaned up demo data.")


if __name__ == "__main__":
    _demo()
