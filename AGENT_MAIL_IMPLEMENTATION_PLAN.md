# Custom Agent Mail Implementation Plan
## Tailored for Safety Research System

**Version:** 1.0
**Date:** 2025-10-28
**Status:** Ready for Implementation
**Estimated Time:** 2-3 weeks
**Risk Level:** Low (incremental, non-breaking)

---

## Executive Summary

Based on comprehensive analysis of the current system and lightweight messaging patterns, this plan outlines a **custom agent mail system** specifically designed for the safety-research-system's Agent-Audit-Resolve pattern.

### Key Design Decisions

1. **No External Dependencies** - Python 3.11 stdlib only (queue, threading, SQLite)
2. **Hybrid Architecture** - In-memory queues for speed + SQLite for persistence
3. **Non-Breaking Migration** - Feature flags allow gradual rollout
4. **Thread-Safe by Design** - Works with existing ThreadPoolExecutor
5. **Human Oversight Built-In** - FastAPI dashboard querying SQLite audit trail

### What We're Building

```

┌────────────────────────────────────────────────────────────────────────────┐
│                     AGENT MAIL SYSTEM                                      │
│                                                                            │
│  ┌─────────────────┐     ┌──────────────┐     ┌────────────────────┐   │
│  │ Message Queue   │────▶│  Event Bus   │────▶│  Audit Trail       │   │
│  │  (Priority)     │     │  (Pub/Sub)   │     │  (SQLite)          │   │
│  └─────────────────┘     └──────────────┘     └────────────────────┘   │
│          ▲                       ▲                      ▲                 │
│          │                       │                      │                 │
│          │                       │                      │                 │
│  ┌───────┴────────┐      ┌──────┴───────┐     ┌───────┴──────────┐     │
│  │  Orchestrator  │      │   Workers    │     │  Human Dashboard  │     │
│  │  (enqueues)    │      │  (execute)   │     │  (FastAPI)        │     │
│  └────────────────┘      └──────────────┘     └───────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Current System Analysis Summary

### Communication Patterns Identified

1. **Orchestrator → ResolutionEngine**: Synchronous blocking call (30-60s per task)
2. **ResolutionEngine → TaskExecutor**: Direct method call
3. **TaskExecutor → Worker**: Synchronous execution (blocks for LLM API calls)
4. **ResolutionEngine → AuditEngine**: Direct method call
5. **AuditEngine → Auditor**: Synchronous validation (5-30s + optional LLM)
6. **Data Flow**: Via mutable Task/Case objects (dict-based)

### Current Bottlenecks

1. **Worker execution blocks** (30-60s) - Could be async
2. **Auditor validation blocks** (5-30s) - Could be async
3. **LLM calls block everything** (2-10s each) - Could use queues
4. **No persistence** - Crashes lose all state
5. **No audit trail** - Can't review history
6. **No human oversight interface** - Can't monitor/intervene

### Coupling Issues

- Task object mutated by 3+ components
- Implicit feedback loop (corrections via dict injection)
- Dictionary-based communication (no type safety)
- ResolutionEngine tightly couples task executor + audit engine

---

## Architecture Design

### Design Principles

1. **Start Minimal** - Core features first, enhancements later
2. **Non-Breaking** - Existing synchronous code continues working
3. **Opt-In Migration** - Feature flags control rollout per component
4. **Thread-Safe** - Works with existing ThreadPoolExecutor
5. **Audit First** - Every message logged to SQLite
6. **Human-Friendly** - Web UI for monitoring and intervention

### Core Components

#### 1. Message Transport Layer

**File**: `core/agent_mail/transport.py`

```python
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import uuid
import json

class MessageType(Enum):
    """Types of messages in the system."""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    AUDIT_REQUEST = "audit_request"
    AUDIT_RESULT = "audit_result"
    RETRY_REQUEST = "retry_request"
    ESCALATION = "escalation"
    HUMAN_REVIEW = "human_review"
    STATUS_UPDATE = "status_update"

class MessagePriority(Enum):
    """Message priority levels."""
    HIGH = 1
    MEDIUM = 5
    LOW = 10

@dataclass
class AgentMessage:
    """
    Standard message format for agent communication.

    All communication between agents flows through this structure.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.STATUS_UPDATE
    from_agent: str = ""  # Sender agent name
    to_agent: str = ""  # Recipient agent name
    subject: str = ""  # Human-readable subject
    body: str = ""  # Markdown-formatted body
    data: Dict[str, Any] = field(default_factory=dict)  # Structured data
    thread_id: Optional[str] = None  # For grouping related messages
    parent_id: Optional[str] = None  # Reply-to message
    priority: MessagePriority = MessagePriority.MEDIUM
    requires_ack: bool = False  # Require acknowledgment?
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extensible

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        d = asdict(self)
        d['message_type'] = self.message_type.value
        d['priority'] = self.priority.value
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> 'AgentMessage':
        """Deserialize from dictionary."""
        d['message_type'] = MessageType(d['message_type'])
        d['priority'] = MessagePriority(d['priority'])
        return cls(**d)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))
```

**Why This Design?**
- Dataclass for type safety (vs. dicts in current system)
- Extensible metadata field for future features
- Thread ID for conversation grouping
- Priority for queue ordering
- JSON serializable for SQLite storage

---

#### 2. In-Memory Message Queue

**File**: `core/agent_mail/message_queue.py`

```python
from queue import PriorityQueue, Queue, Empty
from typing import Optional, Callable, Dict, List
from .transport import AgentMessage, MessagePriority
import threading
import logging

logger = logging.getLogger(__name__)

class InMemoryMessageQueue:
    """
    Thread-safe priority message queue for fast in-process messaging.

    This is the primary transport for agent communication.
    Messages are routed to recipient-specific queues.
    """

    def __init__(self):
        # Per-agent inboxes (agent_name -> PriorityQueue)
        self.inboxes: Dict[str, PriorityQueue] = {}
        self.inbox_lock = threading.Lock()

        # Global result queue (for orchestrator to collect results)
        self.result_queue = Queue()

        # Message history (message_id -> message)
        self.message_history: Dict[str, AgentMessage] = {}
        self.history_lock = threading.Lock()

    def send(self, message: AgentMessage):
        """
        Send message to recipient's inbox.

        Thread-safe: Multiple agents can send concurrently.
        """
        recipient = message.to_agent

        # Ensure inbox exists
        with self.inbox_lock:
            if recipient not in self.inboxes:
                self.inboxes[recipient] = PriorityQueue()

        # Enqueue with priority
        priority_value = message.priority.value
        self.inboxes[recipient].put((priority_value, message))

        # Store in history
        with self.history_lock:
            self.message_history[message.message_id] = message

        logger.debug(f"Message {message.message_id} sent to {recipient}")

    def receive(self, agent_name: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive next message from agent's inbox (blocking).

        Args:
            agent_name: Agent receiving message
            timeout: Max time to wait (None = wait forever)

        Returns:
            AgentMessage or None if timeout
        """
        # Ensure inbox exists
        with self.inbox_lock:
            if agent_name not in self.inboxes:
                self.inboxes[agent_name] = PriorityQueue()

        try:
            priority, message = self.inboxes[agent_name].get(timeout=timeout)
            logger.debug(f"Agent {agent_name} received message {message.message_id}")
            return message
        except Empty:
            return None

    def receive_nowait(self, agent_name: str) -> Optional[AgentMessage]:
        """
        Non-blocking receive (returns None if no messages).
        """
        return self.receive(agent_name, timeout=0.001)

    def get_message_history(self, thread_id: str) -> List[AgentMessage]:
        """Get all messages in a thread (for audit trail)."""
        with self.history_lock:
            return [
                msg for msg in self.message_history.values()
                if msg.thread_id == thread_id
            ]

    def get_inbox_size(self, agent_name: str) -> int:
        """Get number of pending messages for agent."""
        with self.inbox_lock:
            if agent_name not in self.inboxes:
                return 0
            return self.inboxes[agent_name].qsize()
```

**Why This Design?**
- Per-agent inboxes (no broadcast needed for direct messages)
- PriorityQueue respects message priority
- Thread-safe with locks
- Blocking/non-blocking receive options
- Message history for debugging

---

#### 3. Event Bus (Pub/Sub)

**File**: `core/agent_mail/event_bus.py`

```python
from collections import defaultdict
from typing import Callable, Any, List
import threading
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    Simple pub/sub event bus for broadcasting events to multiple subscribers.

    Use for:
    - Audit events (log to multiple destinations)
    - Status updates (notify dashboard, logger, metrics)
    - Alerts (notify human, log, escalate)
    """

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        """
        Subscribe to event type.

        Args:
            event_type: Event to subscribe to (e.g., "task.completed")
                       Use "*" for all events
            callback: Function to call when event published
        """
        with self.lock:
            self.subscribers[event_type].append(callback)

        logger.debug(f"Subscribed to {event_type}")

    def publish(self, event_type: str, data: Any):
        """
        Publish event to all subscribers.

        Args:
            event_type: Type of event
            data: Event data (any type)
        """
        # Get subscribers (copy to avoid deadlock)
        with self.lock:
            callbacks = self.subscribers[event_type].copy()
            wildcard_callbacks = self.subscribers.get("*", []).copy()

        all_callbacks = callbacks + wildcard_callbacks

        # Execute outside lock (avoid deadlock)
        for callback in all_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"EventBus callback error: {e}", exc_info=True)

        logger.debug(f"Published {event_type} to {len(all_callbacks)} subscribers")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove subscription."""
        with self.lock:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
```

**Why This Design?**
- Decouples event producers from consumers
- Multiple subscribers per event (log + dashboard + metrics)
- Wildcard "*" subscribes to all events
- Thread-safe
- Exception handling per subscriber (one failure doesn't break others)

---

#### 4. Persistent Audit Trail

**File**: `core/agent_mail/audit_trail.py`

```python
import sqlite3
import json
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional
from .transport import AgentMessage

class AuditTrail:
    """
    SQLite-based audit trail for all agent communication.

    Features:
    - ACID transactions (durability)
    - Fast queries (indexed)
    - Human-readable queries (SQL)
    - WAL mode (better concurrency)
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.local = threading.local()
        self._init_db()

    @contextmanager
    def get_conn(self):
        """Thread-local connection."""
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            # Enable WAL mode for better concurrency
            self.local.conn.execute("PRAGMA journal_mode=WAL")
            self.local.conn.execute("PRAGMA synchronous=NORMAL")
            self.local.conn.row_factory = sqlite3.Row  # Dict-like access

        yield self.local.conn

    def _init_db(self):
        """Initialize database schema."""
        with self.get_conn() as conn:
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    message_type TEXT NOT NULL,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT NOT NULL,
                    subject TEXT,
                    body TEXT,
                    data TEXT,  -- JSON
                    thread_id TEXT,
                    parent_id TEXT,
                    priority INTEGER,
                    requires_ack BOOLEAN,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    FOREIGN KEY (parent_id) REFERENCES messages(message_id)
                )
            """)

            # Indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_thread ON messages(thread_id, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_recipient ON messages(to_agent, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sender ON messages(from_agent, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)")

            # Acknowledgments table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS acknowledgments (
                    message_id TEXT PRIMARY KEY,
                    ack_by TEXT NOT NULL,
                    ack_timestamp TEXT NOT NULL,
                    FOREIGN KEY (message_id) REFERENCES messages(message_id)
                )
            """)

            conn.commit()

    def log_message(self, message: AgentMessage):
        """
        Persist message to audit trail.

        Thread-safe: Multiple agents can log concurrently.
        """
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO messages (
                    message_id, message_type, from_agent, to_agent,
                    subject, body, data, thread_id, parent_id,
                    priority, requires_ack, timestamp, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.message_id,
                message.message_type.value,
                message.from_agent,
                message.to_agent,
                message.subject,
                message.body,
                json.dumps(message.data),
                message.thread_id,
                message.parent_id,
                message.priority.value,
                message.requires_ack,
                message.timestamp,
                json.dumps(message.metadata)
            ))
            conn.commit()

    def log_acknowledgment(self, message_id: str, ack_by: str):
        """Log message acknowledgment."""
        with self.get_conn() as conn:
            conn.execute("""
                INSERT INTO acknowledgments (message_id, ack_by, ack_timestamp)
                VALUES (?, ?, ?)
            """, (message_id, ack_by, datetime.utcnow().isoformat()))
            conn.commit()

    def get_thread(self, thread_id: str) -> List[Dict]:
        """
        Get all messages in a thread (for human oversight).

        Returns messages in chronological order.
        """
        with self.get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM messages
                WHERE thread_id = ?
                ORDER BY timestamp ASC
            """, (thread_id,))

            return [dict(row) for row in cursor.fetchall()]

    def get_agent_messages(
        self,
        agent_name: str,
        direction: str = "both",  # "sent", "received", "both"
        limit: int = 100
    ) -> List[Dict]:
        """Get messages sent/received by agent."""
        with self.get_conn() as conn:
            if direction == "sent":
                query = "SELECT * FROM messages WHERE from_agent = ? ORDER BY timestamp DESC LIMIT ?"
            elif direction == "received":
                query = "SELECT * FROM messages WHERE to_agent = ? ORDER BY timestamp DESC LIMIT ?"
            else:  # both
                query = "SELECT * FROM messages WHERE from_agent = ? OR to_agent = ? ORDER BY timestamp DESC LIMIT ?"
                cursor = conn.execute(query, (agent_name, agent_name, limit))
                return [dict(row) for row in cursor.fetchall()]

            cursor = conn.execute(query, (agent_name, limit))
            return [dict(row) for row in cursor.fetchall()]

    def search_messages(
        self,
        query: str,
        message_type: Optional[str] = None,
        agent: Optional[str] = None
    ) -> List[Dict]:
        """Full-text search in messages (for human oversight)."""
        with self.get_conn() as conn:
            sql = "SELECT * FROM messages WHERE (subject LIKE ? OR body LIKE ?)"
            params = [f"%{query}%", f"%{query}%"]

            if message_type:
                sql += " AND message_type = ?"
                params.append(message_type)

            if agent:
                sql += " AND (from_agent = ? OR to_agent = ?)"
                params.extend([agent, agent])

            sql += " ORDER BY timestamp DESC LIMIT 100"

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
```

**Why This Design?**
- SQLite is lightweight, zero-config, excellent for audit trails
- WAL mode allows concurrent reads during writes
- Indexed queries for fast lookups
- Full-text search for human oversight
- Thread-safe with thread-local connections

---

#### 5. Agent Mailbox (High-Level API)

**File**: `core/agent_mail/mailbox.py`

```python
from typing import Optional, Callable, Dict
from .transport import AgentMessage, MessageType, MessagePriority
from .message_queue import InMemoryMessageQueue
from .event_bus import EventBus
from .audit_trail import AuditTrail
import logging

logger = logging.getLogger(__name__)

class AgentMailbox:
    """
    High-level API for agent communication.

    Each agent gets a mailbox for sending/receiving messages.
    Combines in-memory queue (fast) + audit trail (persistent).
    """

    def __init__(
        self,
        agent_name: str,
        message_queue: InMemoryMessageQueue,
        event_bus: EventBus,
        audit_trail: Optional[AuditTrail] = None
    ):
        self.agent_name = agent_name
        self.message_queue = message_queue
        self.event_bus = event_bus
        self.audit_trail = audit_trail

    def send(
        self,
        to_agent: str,
        message_type: MessageType,
        subject: str,
        body: str = "",
        data: Optional[Dict] = None,
        thread_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        requires_ack: bool = False
    ) -> AgentMessage:
        """
        Send message to another agent.

        Returns the sent message (for tracking).
        """
        message = AgentMessage(
            message_type=message_type,
            from_agent=self.agent_name,
            to_agent=to_agent,
            subject=subject,
            body=body,
            data=data or {},
            thread_id=thread_id,
            priority=priority,
            requires_ack=requires_ack
        )

        # Send to in-memory queue
        self.message_queue.send(message)

        # Persist to audit trail
        if self.audit_trail:
            self.audit_trail.log_message(message)

        # Publish event
        self.event_bus.publish(f"message.sent.{message_type.value}", {
            "message_id": message.message_id,
            "from": self.agent_name,
            "to": to_agent,
            "type": message_type.value
        })

        logger.info(f"{self.agent_name} sent {message_type.value} to {to_agent}")

        return message

    def receive(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive next message (blocking).

        Args:
            timeout: Max time to wait (None = wait forever)

        Returns:
            AgentMessage or None
        """
        message = self.message_queue.receive(self.agent_name, timeout=timeout)

        if message:
            # Publish event
            self.event_bus.publish(f"message.received.{message.message_type.value}", {
                "message_id": message.message_id,
                "from": message.from_agent,
                "to": self.agent_name,
                "type": message.message_type.value
            })

            logger.info(f"{self.agent_name} received {message.message_type.value} from {message.from_agent}")

        return message

    def receive_nowait(self) -> Optional[AgentMessage]:
        """Non-blocking receive (returns None if no messages)."""
        return self.receive(timeout=0.001)

    def acknowledge(self, message: AgentMessage):
        """Acknowledge receipt/processing of message."""
        if self.audit_trail:
            self.audit_trail.log_acknowledgment(message.message_id, self.agent_name)

        # Publish event
        self.event_bus.publish("message.acknowledged", {
            "message_id": message.message_id,
            "ack_by": self.agent_name
        })

    def get_inbox_size(self) -> int:
        """Get number of pending messages."""
        return self.message_queue.get_inbox_size(self.agent_name)

    def get_thread_history(self, thread_id: str) -> List[AgentMessage]:
        """Get all messages in thread (for context)."""
        if self.audit_trail:
            messages_dict = self.audit_trail.get_thread(thread_id)
            return [AgentMessage.from_dict(m) for m in messages_dict]
        else:
            return self.message_queue.get_message_history(thread_id)
```

**Why This Design?**
- Simple API for agents (send, receive, acknowledge)
- Automatically logs to audit trail
- Automatically publishes events
- Combines fast in-memory with persistent SQLite
- Each agent gets their own mailbox instance

---

## Integration with Existing System

### Phase 1: Add Agent Mail Infrastructure (Non-Breaking)

**Week 1: Core Components**

**Day 1-2: Message Transport**
- Create `core/agent_mail/` directory
- Implement `transport.py` (AgentMessage dataclass)
- Write unit tests
- Verify serialization/deserialization

**Day 3-4: Message Queue + Event Bus**
- Implement `message_queue.py` (InMemoryMessageQueue)
- Implement `event_bus.py` (EventBus)
- Write integration tests (thread safety)
- Benchmark performance

**Day 5: Audit Trail**
- Implement `audit_trail.py` (SQLite-based)
- Create database schema
- Write queries for human oversight
- Test concurrent writes

**Day 6-7: Mailbox API**
- Implement `mailbox.py` (AgentMailbox)
- Create factory for creating mailboxes
- Write comprehensive tests
- Document API

**Deliverables Week 1:**
- ✅ Complete agent mail infrastructure
- ✅ All unit tests passing
- ✅ API documentation
- ✅ Performance benchmarks

---

### Phase 2: Integrate with Orchestrator (Opt-In)

**Week 2: Integration**

**Day 8-9: Enhanced Base Classes**

**File**: `agents/base_worker_enhanced.py`

```python
from agents.base_worker import BaseWorker
from core.agent_mail.mailbox import AgentMailbox
from core.agent_mail.transport import MessageType, AgentMessage
from typing import Optional, Dict, Any

class EnhancedBaseWorker(BaseWorker):
    """
    Enhanced worker with agent mail support.

    Backward compatible: Works with or without mailbox.
    """

    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any] = None,
        mailbox: Optional[AgentMailbox] = None
    ):
        super().__init__(agent_id, config)
        self.mailbox = mailbox
        self.enable_agent_mail = mailbox is not None

    def execute_with_messaging(self, task_message: AgentMessage) -> AgentMessage:
        """
        Execute task received via agent mail.

        Returns result as AgentMessage.
        """
        # Extract task data from message
        task_data = task_message.data

        # Execute (uses existing execute method)
        result = self.execute(task_data)

        # Send result message
        if self.mailbox:
            result_message = self.mailbox.send(
                to_agent="ResolutionEngine",
                message_type=MessageType.TASK_RESULT,
                subject=f"Task {task_data['task_id']} completed",
                body=self._format_result_summary(result),
                data={
                    "task_id": task_data["task_id"],
                    "result": result
                },
                thread_id=task_message.thread_id
            )
            return result_message

        # Fallback: No messaging
        return AgentMessage(
            from_agent=self.agent_id,
            to_agent="ResolutionEngine",
            data={"result": result}
        )

    def handle_corrections_from_message(self, retry_message: AgentMessage) -> Dict:
        """
        Handle retry request from audit failure.

        Extracts corrections from message and prepares input.
        """
        corrections = retry_message.data.get("corrections", [])
        previous_output = retry_message.data.get("previous_output")
        audit_feedback = retry_message.body

        # Use existing handle_corrections method
        return self.handle_corrections({
            "corrections": corrections,
            "previous_output": previous_output,
            "audit_feedback": audit_feedback
        })
```

**File**: `agents/base_auditor_enhanced.py`

```python
from agents.base_auditor import BaseAuditor
from core.agent_mail.mailbox import AgentMailbox
from core.agent_mail.transport import MessageType, AgentMessage
from typing import Optional, Dict, Any

class EnhancedBaseAuditor(BaseAuditor):
    """Enhanced auditor with agent mail support."""

    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any] = None,
        mailbox: Optional[AgentMailbox] = None
    ):
        super().__init__(agent_id, config)
        self.mailbox = mailbox
        self.enable_agent_mail = mailbox is not None

    def validate_with_messaging(self, audit_message: AgentMessage) -> AgentMessage:
        """
        Validate task output received via agent mail.

        Returns audit result as AgentMessage.
        """
        # Extract task data
        task_input = audit_message.data.get("task_input")
        task_output = audit_message.data.get("task_output")
        task_metadata = audit_message.data.get("task_metadata", {})

        # Validate (uses existing validate method)
        validation_result = self.validate(task_input, task_output, task_metadata)

        # Send audit result
        if self.mailbox:
            result_message = self.mailbox.send(
                to_agent="ResolutionEngine",
                message_type=MessageType.AUDIT_RESULT,
                subject=f"Audit: {validation_result['status'].upper()}",
                body=self._format_audit_summary(validation_result),
                data={
                    "task_id": audit_message.data.get("task_id"),
                    "validation_result": validation_result
                },
                thread_id=audit_message.thread_id,
                priority=MessagePriority.HIGH if validation_result.get("has_critical_issues") else MessagePriority.MEDIUM
            )
            return result_message

        # Fallback
        return AgentMessage(
            from_agent=self.agent_id,
            to_agent="ResolutionEngine",
            data={"validation_result": validation_result}
        )
```

**Day 10: Enhanced Resolution Engine**

**File**: `core/resolution_engine_enhanced.py`

```python
from core.resolution_engine import ResolutionEngine, ResolutionDecision
from core.agent_mail.mailbox import AgentMailbox
from core.agent_mail.transport import MessageType, AgentMessage, MessagePriority
from models.task import Task
from typing import Optional

class EnhancedResolutionEngine(ResolutionEngine):
    """
    Enhanced resolution engine with agent mail support.

    Can operate in:
    - Synchronous mode (existing behavior)
    - Async messaging mode (new)
    """

    def __init__(
        self,
        task_executor,
        audit_engine,
        max_retries: int = 2,
        mailbox: Optional[AgentMailbox] = None
    ):
        super().__init__(task_executor, audit_engine, max_retries)
        self.mailbox = mailbox
        self.enable_agent_mail = mailbox is not None

    def execute_with_messaging(self, task: Task, case_context: Dict) -> AgentMessage:
        """
        Execute task with messaging (async pattern).

        1. Send task to worker
        2. Wait for result
        3. Send to auditor
        4. Wait for audit result
        5. Make resolution decision
        6. If retry: send retry message
        7. Return final result
        """
        if not self.enable_agent_mail:
            # Fall back to synchronous
            decision, audit_result = self.execute_with_validation(task, case_context)
            return self._wrap_as_message(decision, audit_result, task)

        # Get worker agent name for this task type
        worker_agent = self.task_executor.get_agent_name_for_task(task.task_type)

        # Send task to worker
        task_message = self.mailbox.send(
            to_agent=worker_agent,
            message_type=MessageType.TASK_ASSIGNMENT,
            subject=f"Execute task: {task.task_type.value}",
            body=self._format_task_description(task),
            data={
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "input_data": task.input_data
            },
            thread_id=task.task_id,  # Use task_id as thread
            priority=MessagePriority.HIGH
        )

        # Wait for result (with timeout)
        result_message = self._wait_for_message(
            message_type=MessageType.TASK_RESULT,
            thread_id=task.task_id,
            timeout=300.0  # 5 minutes
        )

        if not result_message:
            # Timeout
            return self._create_timeout_message(task)

        # Update task with result
        task.output_data = result_message.data["result"]

        # Send to auditor
        auditor_agent = self.audit_engine.get_agent_name_for_task(task.task_type)

        audit_request = self.mailbox.send(
            to_agent=auditor_agent,
            message_type=MessageType.AUDIT_REQUEST,
            subject=f"Audit task: {task.task_id}",
            body="Please validate task output",
            data={
                "task_id": task.task_id,
                "task_input": task.input_data,
                "task_output": task.output_data,
                "task_metadata": task.metadata
            },
            thread_id=task.task_id,
            priority=MessagePriority.HIGH
        )

        # Wait for audit result
        audit_message = self._wait_for_message(
            message_type=MessageType.AUDIT_RESULT,
            thread_id=task.task_id,
            timeout=120.0  # 2 minutes
        )

        if not audit_message:
            return self._create_timeout_message(task)

        validation_result = audit_message.data["validation_result"]

        # Make resolution decision
        decision = self._make_resolution_decision(task, validation_result)

        if decision == ResolutionDecision.RETRY and task.can_retry():
            # Send retry request to worker
            retry_message = self.mailbox.send(
                to_agent=worker_agent,
                message_type=MessageType.RETRY_REQUEST,
                subject=f"Retry task: {task.task_id}",
                body=self._format_corrections(validation_result),
                data={
                    "task_id": task.task_id,
                    "corrections": self._prepare_corrections(validation_result),
                    "previous_output": task.output_data,
                    "retry_count": task.retry_count + 1
                },
                thread_id=task.task_id,
                priority=MessagePriority.HIGH
            )

            task.increment_retry()

            # Recursive: Execute again
            return self.execute_with_messaging(task, case_context)

        elif decision == ResolutionDecision.ESCALATE:
            # Send to human review queue
            escalation = self.mailbox.send(
                to_agent="HumanReviewer",
                message_type=MessageType.ESCALATION,
                subject=f"ESCALATION: Task {task.task_id}",
                body=self._format_escalation(task, validation_result),
                data={
                    "task_id": task.task_id,
                    "reason": "critical_issues_detected",
                    "validation_result": validation_result
                },
                thread_id=task.task_id,
                priority=MessagePriority.HIGH,
                requires_ack=True
            )

        # Return final result
        return self._wrap_as_message(decision, validation_result, task)

    def _wait_for_message(
        self,
        message_type: MessageType,
        thread_id: str,
        timeout: float
    ) -> Optional[AgentMessage]:
        """
        Wait for specific message type in thread.

        Polls inbox until message arrives or timeout.
        """
        import time
        start = time.time()

        while time.time() - start < timeout:
            message = self.mailbox.receive(timeout=1.0)

            if message and message.message_type == message_type and message.thread_id == thread_id:
                return message

        return None  # Timeout
```

**Day 11-12: Enhanced Orchestrator**

**File**: `agents/orchestrator_enhanced.py`

```python
from agents.orchestrator import Orchestrator
from core.agent_mail.mailbox import AgentMailbox
from core.agent_mail.transport import MessageType
from core.resolution_engine_enhanced import EnhancedResolutionEngine
from models.case import Case
from typing import Dict, Any

class EnhancedOrchestrator(Orchestrator):
    """
    Enhanced orchestrator with agent mail support.

    Feature flag controlled: can run in sync or async mode.
    """

    def __init__(
        self,
        task_executor,
        audit_engine,
        resolution_engine,
        context_compressor,
        enable_parallel_execution: bool = True,
        enable_profiling: bool = True,
        enable_agent_mail: bool = False,  # NEW
        mailbox: Optional[AgentMailbox] = None
    ):
        super().__init__(
            task_executor,
            audit_engine,
            resolution_engine,
            context_compressor,
            enable_parallel_execution,
            enable_profiling
        )
        self.enable_agent_mail = enable_agent_mail
        self.mailbox = mailbox

        if enable_agent_mail and not mailbox:
            raise ValueError("enable_agent_mail=True requires mailbox")

    def _execute_task_with_validation(self, case: Case, task: Task):
        """
        Execute task with validation.

        Routes to sync or async based on feature flag.
        """
        if self.enable_agent_mail:
            # Async messaging mode
            return self._execute_task_with_messaging(case, task)
        else:
            # Sync mode (existing behavior)
            return super()._execute_task_with_validation(case, task)

    def _execute_task_with_messaging(self, case: Case, task: Task):
        """Execute task using agent mail."""

        # Use enhanced resolution engine
        if isinstance(self.resolution_engine, EnhancedResolutionEngine):
            result_message = self.resolution_engine.execute_with_messaging(
                task,
                {"case": case, "priority": case.priority}
            )

            # Extract result from message
            compressed_summary = self.context_compressor.compress_task_result(
                task,
                result_message.data.get("audit_result")
            )

            # Store compressed summary
            with self._task_summaries_lock:
                self.task_summaries[case.case_id][task.task_id] = compressed_summary

            # Add to case findings
            with self._task_summaries_lock:
                case.add_finding(task.task_type, compressed_summary)
```

**Deliverables Week 2:**
- ✅ Enhanced base classes (opt-in)
- ✅ Enhanced resolution engine
- ✅ Enhanced orchestrator
- ✅ Feature flags working
- ✅ Both sync and async modes tested

---

### Phase 3: Human Oversight Dashboard (Optional)

**Week 3: FastAPI Dashboard**

**File**: `api/dashboard.py`

```python
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from core.agent_mail.audit_trail import AuditTrail
from typing import List, Dict

app = FastAPI(title="Safety Research Dashboard")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize audit trail
audit_trail = AuditTrail("safety_audit_trail.db")

@app.get("/")
async def root():
    return {"status": "Safety Research Dashboard Online"}

@app.get("/agents")
async def list_agents():
    """List all agents."""
    # Query unique agents from messages table
    with audit_trail.get_conn() as conn:
        cursor = conn.execute("""
            SELECT DISTINCT from_agent FROM messages
            UNION
            SELECT DISTINCT to_agent FROM messages
        """)
        agents = [row[0] for row in cursor.fetchall()]

    return {"agents": agents}

@app.get("/threads")
async def list_threads(limit: int = 50):
    """List recent conversation threads."""
    with audit_trail.get_conn() as conn:
        cursor = conn.execute("""
            SELECT thread_id, COUNT(*) as message_count, MIN(timestamp) as started_at
            FROM messages
            WHERE thread_id IS NOT NULL
            GROUP BY thread_id
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))

        threads = [
            {
                "thread_id": row[0],
                "message_count": row[1],
                "started_at": row[2]
            }
            for row in cursor.fetchall()
        ]

    return {"threads": threads}

@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """Get all messages in thread."""
    messages = audit_trail.get_thread(thread_id)
    return {"thread_id": thread_id, "messages": messages}

@app.get("/agents/{agent_name}/messages")
async def get_agent_messages(agent_name: str, direction: str = "both", limit: int = 100):
    """Get messages for agent."""
    messages = audit_trail.get_agent_messages(agent_name, direction, limit)
    return {"agent": agent_name, "messages": messages}

@app.get("/search")
async def search_messages(q: str, message_type: str = None, agent: str = None):
    """Search messages."""
    results = audit_trail.search_messages(q, message_type, agent)
    return {"query": q, "results": results}

@app.websocket("/ws/live")
async def websocket_live_updates(websocket: WebSocket):
    """Real-time message updates."""
    await websocket.accept()

    # Subscribe to event bus
    # (Would need to share event bus instance from main system)

    try:
        while True:
            # In real implementation, this would receive from event bus
            await websocket.receive_text()
    except:
        pass

# Run: uvicorn api.dashboard:app --reload --port 8000
```

**Simple Frontend** (React/Vue):

```javascript
// Dashboard.jsx
import React, { useState, useEffect } from 'react';

function Dashboard() {
  const [threads, setThreads] = useState([]);
  const [selectedThread, setSelectedThread] = useState(null);

  useEffect(() => {
    // Fetch threads
    fetch('http://localhost:8000/threads')
      .then(r => r.json())
      .then(data => setThreads(data.threads));

    // WebSocket for live updates
    const ws = new WebSocket('ws://localhost:8000/ws/live');
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      // Update UI
    };

    return () => ws.close();
  }, []);

  const loadThread = (threadId) => {
    fetch(`http://localhost:8000/threads/${threadId}`)
      .then(r => r.json())
      .then(data => setSelectedThread(data));
  };

  return (
    <div className="dashboard">
      <h1>Safety Research System</h1>

      <div className="threads">
        <h2>Conversation Threads</h2>
        {threads.map(thread => (
          <div key={thread.thread_id} onClick={() => loadThread(thread.thread_id)}>
            <strong>{thread.thread_id}</strong>
            <span>{thread.message_count} messages</span>
            <span>{thread.started_at}</span>
          </div>
        ))}
      </div>

      {selectedThread && (
        <div className="thread-details">
          <h2>Thread: {selectedThread.thread_id}</h2>
          {selectedThread.messages.map(msg => (
            <div key={msg.message_id} className="message">
              <strong>{msg.from_agent} → {msg.to_agent}</strong>
              <p>{msg.subject}</p>
              <pre>{msg.body}</pre>
              <small>{msg.timestamp}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Migration Strategy

### Feature Flags for Gradual Rollout

**Configuration**: `config/agent_mail_config.py`

```python
from dataclasses import dataclass

@dataclass
class AgentMailConfig:
    """Configuration for agent mail system."""

    # Feature flags
    enable_agent_mail: bool = False  # Master switch
    enable_audit_trail: bool = True  # Persist to SQLite
    enable_event_bus: bool = True  # Pub/sub events
    enable_human_dashboard: bool = False  # FastAPI dashboard

    # Performance
    message_queue_maxsize: int = 1000
    worker_timeout_seconds: float = 300.0  # 5 minutes
    auditor_timeout_seconds: float = 120.0  # 2 minutes

    # Persistence
    audit_trail_db_path: str = "safety_audit_trail.db"
    enable_wal_mode: bool = True  # Better concurrency

    # Dashboard
    dashboard_port: int = 8000
    dashboard_host: str = "localhost"

# Global config
config = AgentMailConfig()
```

**Usage in Code**:

```python
from config.agent_mail_config import config

# In orchestrator initialization
orchestrator = EnhancedOrchestrator(
    ...,
    enable_agent_mail=config.enable_agent_mail,
    mailbox=mailbox if config.enable_agent_mail else None
)
```

### Rollout Phases

**Phase 1: Infrastructure Only (Week 1)**
- Enable: `enable_audit_trail=True, enable_event_bus=True`
- Disable: `enable_agent_mail=False` (keeps sync behavior)
- Result: Events logged, no behavior change
- Risk: **Low** - Only adds logging

**Phase 2: Single Agent Test (Week 2)**
- Enable: `enable_agent_mail=True` for LiteratureAgent only
- Others remain synchronous
- Result: Test messaging with one agent
- Risk: **Low** - Easy to revert

**Phase 3: Full Rollout (Week 3)**
- Enable: `enable_agent_mail=True` for all agents
- Result: Full async messaging
- Risk: **Medium** - Monitor carefully

**Phase 4: Dashboard (Week 3+)**
- Enable: `enable_human_dashboard=True`
- Result: Web UI for monitoring
- Risk: **Low** - Optional feature

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_agent_mail_unit.py`

```python
import pytest
from core.agent_mail.transport import AgentMessage, MessageType
from core.agent_mail.message_queue import InMemoryMessageQueue
from core.agent_mail.event_bus import EventBus
import threading
import time

def test_message_serialization():
    """Test message to/from dict."""
    msg = AgentMessage(
        message_type=MessageType.TASK_ASSIGNMENT,
        from_agent="TestAgent",
        to_agent="Worker1",
        subject="Test",
        data={"key": "value"}
    )

    # Serialize
    msg_dict = msg.to_dict()

    # Deserialize
    msg2 = AgentMessage.from_dict(msg_dict)

    assert msg.message_id == msg2.message_id
    assert msg.from_agent == msg2.from_agent
    assert msg.data == msg2.data

def test_message_queue_priority():
    """Test priority ordering."""
    queue = InMemoryMessageQueue()

    # Send messages with different priorities
    low_msg = AgentMessage(from_agent="A", to_agent="B", priority=MessagePriority.LOW)
    high_msg = AgentMessage(from_agent="A", to_agent="B", priority=MessagePriority.HIGH)
    medium_msg = AgentMessage(from_agent="A", to_agent="B", priority=MessagePriority.MEDIUM)

    queue.send(low_msg)
    queue.send(high_msg)
    queue.send(medium_msg)

    # Receive in priority order
    msg1 = queue.receive("B")
    msg2 = queue.receive("B")
    msg3 = queue.receive("B")

    assert msg1.message_id == high_msg.message_id  # Priority 1 first
    assert msg2.message_id == medium_msg.message_id  # Priority 5 second
    assert msg3.message_id == low_msg.message_id  # Priority 10 last

def test_event_bus_pub_sub():
    """Test event bus publish/subscribe."""
    bus = EventBus()

    received_events = []

    def listener(data):
        received_events.append(data)

    # Subscribe
    bus.subscribe("test.event", listener)

    # Publish
    bus.publish("test.event", {"value": 123})

    # Verify
    assert len(received_events) == 1
    assert received_events[0]["value"] == 123

def test_message_queue_thread_safety():
    """Test concurrent sends/receives."""
    queue = InMemoryMessageQueue()

    def sender(agent_id):
        for i in range(10):
            msg = AgentMessage(from_agent=f"Sender{agent_id}", to_agent="Receiver")
            queue.send(msg)
            time.sleep(0.001)

    def receiver():
        messages = []
        for i in range(30):
            msg = queue.receive("Receiver", timeout=1.0)
            if msg:
                messages.append(msg)
        return messages

    # Start 3 senders
    senders = [threading.Thread(target=sender, args=(i,)) for i in range(3)]
    for t in senders:
        t.start()

    # Start receiver
    received_messages = []
    receiver_thread = threading.Thread(target=lambda: received_messages.extend(receiver()))
    receiver_thread.start()

    # Wait
    for t in senders:
        t.join()
    receiver_thread.join()

    # Verify all messages received
    assert len(received_messages) == 30
```

### Integration Tests

**File**: `tests/test_agent_mail_integration.py`

```python
import pytest
from core.agent_mail.mailbox import AgentMailbox
from core.agent_mail.message_queue import InMemoryMessageQueue
from core.agent_mail.event_bus import EventBus
from core.agent_mail.audit_trail import AuditTrail
from core.agent_mail.transport import MessageType
import threading
import time
import tempfile
import os

@pytest.fixture
def agent_mail_system():
    """Setup complete agent mail system."""
    queue = InMemoryMessageQueue()
    event_bus = EventBus()

    # Use temporary SQLite database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    audit_trail = AuditTrail(temp_db.name)

    # Create mailboxes for agents
    orchestrator_mailbox = AgentMailbox("Orchestrator", queue, event_bus, audit_trail)
    worker_mailbox = AgentMailbox("Worker1", queue, event_bus, audit_trail)
    auditor_mailbox = AgentMailbox("Auditor1", queue, event_bus, audit_trail)

    yield {
        "queue": queue,
        "event_bus": event_bus,
        "audit_trail": audit_trail,
        "orchestrator": orchestrator_mailbox,
        "worker": worker_mailbox,
        "auditor": auditor_mailbox,
        "db_path": temp_db.name
    }

    # Cleanup
    os.unlink(temp_db.name)

def test_end_to_end_task_flow(agent_mail_system):
    """Test complete task assignment → execution → audit flow."""

    orchestrator = agent_mail_system["orchestrator"]
    worker = agent_mail_system["worker"]
    auditor = agent_mail_system["auditor"]

    # Orchestrator sends task to worker
    task_msg = orchestrator.send(
        to_agent="Worker1",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Execute literature review",
        data={"task_id": "task-123", "query": "Test query"},
        thread_id="task-123"
    )

    # Worker receives task
    received_task = worker.receive(timeout=1.0)
    assert received_task is not None
    assert received_task.message_type == MessageType.TASK_ASSIGNMENT
    assert received_task.data["task_id"] == "task-123"

    # Worker sends result
    result_msg = worker.send(
        to_agent="Auditor1",
        message_type=MessageType.TASK_RESULT,
        subject="Task completed",
        data={"task_id": "task-123", "result": {"success": True}},
        thread_id="task-123"
    )

    # Auditor receives result
    received_result = auditor.receive(timeout=1.0)
    assert received_result is not None
    assert received_result.message_type == MessageType.TASK_RESULT

    # Auditor sends audit result
    audit_msg = auditor.send(
        to_agent="Orchestrator",
        message_type=MessageType.AUDIT_RESULT,
        subject="Audit passed",
        data={"task_id": "task-123", "status": "passed"},
        thread_id="task-123"
    )

    # Orchestrator receives audit result
    final_result = orchestrator.receive(timeout=1.0)
    assert final_result is not None
    assert final_result.message_type == MessageType.AUDIT_RESULT

    # Verify thread history in audit trail
    thread_history = agent_mail_system["audit_trail"].get_thread("task-123")
    assert len(thread_history) == 3  # Task, result, audit

def test_event_bus_logging(agent_mail_system):
    """Test that all messages trigger events."""

    event_bus = agent_mail_system["event_bus"]
    orchestrator = agent_mail_system["orchestrator"]

    events_received = []

    def log_event(data):
        events_received.append(data)

    # Subscribe to all events
    event_bus.subscribe("message.sent.*", log_event)

    # Send message
    orchestrator.send(
        to_agent="Worker1",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Test",
        data={}
    )

    # Verify event was published
    assert len(events_received) > 0
```

---

## Risk Assessment & Mitigation

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|---------|------------|
| **Performance degradation** | Medium | High | Benchmark before/after, keep sync fallback |
| **Race conditions** | Low | High | Comprehensive thread safety tests |
| **Message loss** | Low | Critical | Persist to SQLite, add acknowledgments |
| **Increased complexity** | High | Medium | Excellent documentation, gradual rollout |
| **SQLite locks** | Low | Medium | Use WAL mode, tune timeout |

### Mitigation Strategies

1. **Performance**: Keep both sync and async modes, compare benchmarks
2. **Thread Safety**: Use locks consistently, write stress tests
3. **Message Loss**: Audit trail captures everything, requires_ack flag
4. **Complexity**: Feature flags allow disabling, comprehensive docs
5. **SQLite**: WAL mode + reasonable timeouts (10s default)

---

## Success Metrics

### Technical Metrics

- **Message throughput**: >1000 msgs/sec (in-memory)
- **Message latency**: <10ms (queue to inbox)
- **Audit trail latency**: <50ms (SQLite write)
- **Thread safety**: 0 race conditions in stress tests
- **Test coverage**: >90% for agent mail code

### Functional Metrics

- **Feature flag adoption**: Gradual rollout without issues
- **Audit completeness**: 100% of messages logged
- **Human oversight**: Dashboard shows all threads
- **Backward compatibility**: Sync mode still works

---

## Maintenance & Operations

### Monitoring

**Key Metrics to Track:**

```python
# In event bus subscribers
def monitor_message_flow(data):
    """Monitor message flow metrics."""
    metrics.increment(f"message.sent.{data['type']}")
    metrics.timing(f"message.latency.{data['type']}", data.get('latency_ms'))

event_bus.subscribe("message.*", monitor_message_flow)
```

**SQLite Database Maintenance:**

```bash
# Periodic vacuum (reclaim space)
sqlite3 safety_audit_trail.db "VACUUM;"

# Analyze (update statistics for query optimizer)
sqlite3 safety_audit_trail.db "ANALYZE;"

# Check integrity
sqlite3 safety_audit_trail.db "PRAGMA integrity_check;"
```

**Backup Strategy:**

```bash
# Daily backup
cp safety_audit_trail.db safety_audit_trail.db.$(date +%Y%m%d)

# Or use SQLite backup API
sqlite3 safety_audit_trail.db ".backup safety_audit_trail.backup.db"
```

---

## Documentation Deliverables

1. **API Documentation** - Docstrings for all classes/methods
2. **Integration Guide** - How to add agent mail to existing agents
3. **Dashboard Guide** - How to use web UI
4. **Troubleshooting Guide** - Common issues and solutions
5. **Performance Tuning Guide** - Optimization tips

---

## Appendix: Complete File Structure

```
safety-research-system/
├── core/
│   ├── agent_mail/
│   │   ├── __init__.py
│   │   ├── transport.py          # AgentMessage dataclass
│   │   ├── message_queue.py      # InMemoryMessageQueue
│   │   ├── event_bus.py          # EventBus (pub/sub)
│   │   ├── audit_trail.py        # AuditTrail (SQLite)
│   │   └── mailbox.py            # AgentMailbox (high-level API)
│   ├── task_executor.py
│   ├── audit_engine.py
│   ├── resolution_engine.py
│   └── resolution_engine_enhanced.py  # NEW
├── agents/
│   ├── base_worker.py
│   ├── base_auditor.py
│   ├── base_worker_enhanced.py       # NEW
│   ├── base_auditor_enhanced.py      # NEW
│   ├── orchestrator.py
│   └── orchestrator_enhanced.py      # NEW
├── api/
│   └── dashboard.py                  # FastAPI dashboard
├── config/
│   └── agent_mail_config.py          # Configuration
├── tests/
│   ├── test_agent_mail_unit.py
│   └── test_agent_mail_integration.py
├── docs/
│   ├── agent_mail_api.md
│   ├── agent_mail_integration_guide.md
│   ├── agent_mail_dashboard_guide.md
│   └── agent_mail_troubleshooting.md
└── safety_audit_trail.db             # SQLite database
```

---

## Next Steps

1. **Review this plan** - Discuss with team
2. **Approve architecture** - Confirm design decisions
3. **Allocate resources** - 1 engineer, 2-3 weeks
4. **Start Week 1** - Implement core components
5. **Iterate based on feedback** - Adjust as needed

---

**Total Estimated Time: 2-3 weeks**
**Risk Level: Low (incremental, non-breaking)**
**Value: High (async messaging, audit trail, human oversight)**

Ready to implement? Let's start with Week 1, Day 1!
