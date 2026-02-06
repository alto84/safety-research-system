"""
Immutable audit trail for prediction reproducibility.

Every prediction, hypothesis, validation, and alert is recorded with full
provenance -- including input data, model versions, parameters, and outputs --
so that any prediction can be fully reproduced and explained at a later date.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of events recorded in the audit trail."""

    PREDICTION_REQUEST = "prediction_request"
    MODEL_CALL = "model_call"
    MODEL_RESPONSE = "model_response"
    NORMALIZATION = "normalization"
    ENSEMBLE_AGGREGATION = "ensemble_aggregation"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    MECHANISTIC_VALIDATION = "mechanistic_validation"
    SAFETY_INDEX_COMPUTATION = "safety_index_computation"
    ALERT_GENERATED = "alert_generated"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR = "error"


@dataclass(frozen=True)
class AuditRecord:
    """An immutable audit record.

    Once created, the record is frozen and its content hash ensures
    tamper detection.

    Attributes:
        record_id: Unique sequential record identifier.
        event_type: What kind of event this records.
        timestamp: When the event occurred (Unix timestamp).
        patient_id: The patient involved (empty for system events).
        session_id: Groups related records into a prediction session.
        actor: What generated this record (model ID, engine component, user).
        input_data: The inputs to the operation.
        output_data: The outputs of the operation.
        parameters: Configuration/parameters used.
        duration_ms: How long the operation took.
        parent_record_id: Links to the record that triggered this one.
        content_hash: SHA-256 hash of the record content for integrity.
        chain_hash: Hash of this record + previous record's chain_hash.
    """

    record_id: int
    event_type: AuditEventType
    timestamp: float
    patient_id: str = ""
    session_id: str = ""
    actor: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0
    parent_record_id: int | None = None
    content_hash: str = ""
    chain_hash: str = ""


class AuditTrail:
    """Immutable, append-only audit trail for full prediction reproducibility.

    Features:
        - **Immutable records**: Once written, records cannot be modified.
        - **Hash chain**: Each record includes a chained hash linking to the
          previous record, providing tamper evidence.
        - **Session tracking**: Related operations are grouped by session ID.
        - **Full provenance**: Input data, parameters, and outputs are captured.
        - **Thread-safe**: Uses locking for concurrent access.

    Usage::

        audit = AuditTrail()

        # Start a prediction session
        session_id = audit.start_session("PAT-001")

        # Record events
        audit.record(
            event_type=AuditEventType.PREDICTION_REQUEST,
            patient_id="PAT-001",
            session_id=session_id,
            input_data={"biomarkers": {...}},
        )

        # Query audit trail
        records = audit.get_session_records(session_id)
    """

    def __init__(self, max_records: int = 100_000) -> None:
        """Initialize the audit trail.

        Args:
            max_records: Maximum number of records to retain in memory.
                Older records are archived (logged) when this limit is reached.
        """
        self._records: list[AuditRecord] = []
        self._record_counter = 0
        self._session_counter = 0
        self._max_records = max_records
        self._lock = threading.Lock()
        self._last_chain_hash = "genesis"
        logger.info("AuditTrail initialized (max_records=%d)", max_records)

    def start_session(self, patient_id: str = "") -> str:
        """Start a new audit session and return its ID.

        Args:
            patient_id: Optional patient ID to associate with the session.

        Returns:
            A unique session ID string.
        """
        with self._lock:
            self._session_counter += 1
            session_id = f"SESSION-{self._session_counter:08d}"

        self.record(
            event_type=AuditEventType.PREDICTION_REQUEST,
            patient_id=patient_id,
            session_id=session_id,
            actor="system",
            input_data={"action": "session_start"},
        )

        return session_id

    def record(
        self,
        event_type: AuditEventType,
        patient_id: str = "",
        session_id: str = "",
        actor: str = "",
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        parameters: dict[str, Any] | None = None,
        duration_ms: int = 0,
        parent_record_id: int | None = None,
    ) -> int:
        """Record an event in the audit trail.

        Args:
            event_type: The type of event.
            patient_id: The patient involved.
            session_id: The session this record belongs to.
            actor: What generated this event.
            input_data: Inputs to the operation.
            output_data: Outputs of the operation.
            parameters: Configuration used.
            duration_ms: Operation duration in milliseconds.
            parent_record_id: ID of the triggering record.

        Returns:
            The record ID of the new audit record.
        """
        with self._lock:
            self._record_counter += 1
            record_id = self._record_counter

            # Compute content hash
            content = {
                "record_id": record_id,
                "event_type": event_type.value,
                "patient_id": patient_id,
                "session_id": session_id,
                "actor": actor,
                "input_data": input_data or {},
                "output_data": output_data or {},
                "parameters": parameters or {},
                "duration_ms": duration_ms,
                "parent_record_id": parent_record_id,
            }
            content_hash = self._compute_hash(content)

            # Compute chain hash (links to previous record)
            chain_input = f"{self._last_chain_hash}:{content_hash}"
            chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()

            record = AuditRecord(
                record_id=record_id,
                event_type=event_type,
                timestamp=time.time(),
                patient_id=patient_id,
                session_id=session_id,
                actor=actor,
                input_data=input_data or {},
                output_data=output_data or {},
                parameters=parameters or {},
                duration_ms=duration_ms,
                parent_record_id=parent_record_id,
                content_hash=content_hash,
                chain_hash=chain_hash,
            )

            self._records.append(record)
            self._last_chain_hash = chain_hash

            # Archive old records if needed
            if len(self._records) > self._max_records:
                self._archive_oldest(len(self._records) - self._max_records)

        logger.debug(
            "Audit record %d: %s (patient=%s, session=%s)",
            record_id, event_type.value, patient_id, session_id,
        )

        return record_id

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_record(self, record_id: int) -> AuditRecord | None:
        """Look up a single record by ID.

        Args:
            record_id: The record ID to find.

        Returns:
            The AuditRecord, or None if not found.
        """
        with self._lock:
            for record in self._records:
                if record.record_id == record_id:
                    return record
        return None

    def get_session_records(self, session_id: str) -> list[AuditRecord]:
        """Get all records for a session.

        Args:
            session_id: The session to query.

        Returns:
            Chronologically ordered list of records.
        """
        with self._lock:
            return [r for r in self._records if r.session_id == session_id]

    def get_patient_records(
        self,
        patient_id: str,
        event_type: AuditEventType | None = None,
        since: float | None = None,
    ) -> list[AuditRecord]:
        """Get all records for a patient.

        Args:
            patient_id: The patient to query.
            event_type: Optional filter by event type.
            since: Optional Unix timestamp filter (records after this time).

        Returns:
            Chronologically ordered list of records.
        """
        with self._lock:
            records = [r for r in self._records if r.patient_id == patient_id]
            if event_type is not None:
                records = [r for r in records if r.event_type == event_type]
            if since is not None:
                records = [r for r in records if r.timestamp >= since]
            return records

    def get_prediction_provenance(self, session_id: str) -> dict[str, Any]:
        """Get complete provenance for a prediction session.

        Reconstructs the full chain of operations that produced a prediction,
        including all model calls, parameters, and intermediate results.

        Args:
            session_id: The prediction session to trace.

        Returns:
            Dict with structured provenance information.
        """
        records = self.get_session_records(session_id)
        if not records:
            return {"error": "session not found"}

        provenance: dict[str, Any] = {
            "session_id": session_id,
            "start_time": records[0].timestamp,
            "end_time": records[-1].timestamp,
            "total_duration_ms": sum(r.duration_ms for r in records),
            "record_count": len(records),
            "patient_id": records[0].patient_id,
            "operations": [],
        }

        for record in records:
            provenance["operations"].append({
                "record_id": record.record_id,
                "event_type": record.event_type.value,
                "actor": record.actor,
                "duration_ms": record.duration_ms,
                "input_summary": self._summarize_data(record.input_data),
                "output_summary": self._summarize_data(record.output_data),
                "parameters": record.parameters,
            })

        return provenance

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_chain_integrity(self) -> tuple[bool, str]:
        """Verify the integrity of the audit trail hash chain.

        Returns:
            Tuple of ``(is_valid, message)``.
        """
        with self._lock:
            if not self._records:
                return True, "Audit trail is empty"

            prev_chain_hash = "genesis"
            for record in self._records:
                # Recompute content hash
                content = {
                    "record_id": record.record_id,
                    "event_type": record.event_type.value,
                    "patient_id": record.patient_id,
                    "session_id": record.session_id,
                    "actor": record.actor,
                    "input_data": record.input_data,
                    "output_data": record.output_data,
                    "parameters": record.parameters,
                    "duration_ms": record.duration_ms,
                    "parent_record_id": record.parent_record_id,
                }
                expected_content_hash = self._compute_hash(content)

                if record.content_hash != expected_content_hash:
                    return False, (
                        f"Content hash mismatch at record {record.record_id}"
                    )

                # Verify chain hash
                chain_input = f"{prev_chain_hash}:{record.content_hash}"
                expected_chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()

                if record.chain_hash != expected_chain_hash:
                    return False, (
                        f"Chain hash mismatch at record {record.record_id}"
                    )

                prev_chain_hash = record.chain_hash

        return True, f"Audit trail integrity verified ({len(self._records)} records)"

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    @property
    def record_count(self) -> int:
        """Total number of records in the audit trail."""
        with self._lock:
            return len(self._records)

    def summary(self) -> dict[str, Any]:
        """Return a summary of the audit trail."""
        with self._lock:
            event_counts: dict[str, int] = {}
            for record in self._records:
                key = record.event_type.value
                event_counts[key] = event_counts.get(key, 0) + 1

            unique_patients = len({r.patient_id for r in self._records if r.patient_id})
            unique_sessions = len({r.session_id for r in self._records if r.session_id})

            return {
                "total_records": len(self._records),
                "unique_patients": unique_patients,
                "unique_sessions": unique_sessions,
                "event_counts": event_counts,
                "oldest_timestamp": self._records[0].timestamp if self._records else None,
                "newest_timestamp": self._records[-1].timestamp if self._records else None,
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_hash(content: dict[str, Any]) -> str:
        """Compute SHA-256 hash of a dict's JSON representation."""
        serialized = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    @staticmethod
    def _summarize_data(data: dict[str, Any], max_keys: int = 5) -> dict[str, str]:
        """Produce a brief summary of a data dict for provenance display."""
        summary: dict[str, str] = {}
        for i, (key, value) in enumerate(data.items()):
            if i >= max_keys:
                summary["..."] = f"({len(data) - max_keys} more keys)"
                break
            if isinstance(value, dict):
                summary[key] = f"dict({len(value)} keys)"
            elif isinstance(value, list):
                summary[key] = f"list({len(value)} items)"
            elif isinstance(value, str) and len(value) > 100:
                summary[key] = value[:100] + "..."
            else:
                summary[key] = str(value)
        return summary

    def _archive_oldest(self, count: int) -> None:
        """Archive the oldest records (log them and remove from memory)."""
        to_archive = self._records[:count]
        self._records = self._records[count:]
        logger.info(
            "Archived %d audit records (IDs %d - %d)",
            len(to_archive),
            to_archive[0].record_id if to_archive else 0,
            to_archive[-1].record_id if to_archive else 0,
        )
