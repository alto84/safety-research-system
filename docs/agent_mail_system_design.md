# Agent Mail System Design for Safety Research System

## Executive Summary

This document specifies a custom **Agent Mail System** designed specifically for the safety-research-system's Agent-Audit-Resolve pattern. The system enables asynchronous, observable communication between agents while maintaining the existing architecture's simplicity and reliability.

**Timeline**: 1-2 weeks implementation
**Dependencies**: Python 3.11 stdlib only (queue, threading, sqlite3, dataclasses, json)
**Integration**: Non-breaking, opt-in migration path

---

## 1. Architecture Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SAFETY RESEARCH SYSTEM                      │
│                                                                     │
│  ┌──────────────┐         ┌──────────────┐        ┌─────────────┐ │
│  │ Orchestrator │◄────────┤ Resolution   │◄───────┤   Task      │ │
│  │              │         │ Engine       │        │  Executor   │ │
│  └───────┬──────┘         └───────┬──────┘        └──────┬──────┘ │
│          │                        │                      │        │
│          │                        │                      │        │
│          ▼                        ▼                      ▼        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    AGENT MAIL SYSTEM                          │ │
│  │  ┌──────────────────────────────────────────────────────────┐│ │
│  │  │              AgentMailbox (Central Hub)                   ││ │
│  │  │                                                           ││ │
│  │  │  ├─ MessageRouter (routes by agent_id/topic)            ││ │
│  │  │  ├─ MessageStore (persistence layer)                     ││ │
│  │  │  ├─ SubscriptionManager (pub/sub)                        ││ │
│  │  │  ├─ HumanReviewQueue (oversight interface)               ││ │
│  │  │  └─ MessageHistory (audit trail)                         ││ │
│  │  └──────────────────────────────────────────────────────────┘│ │
│  │                                                               │ │
│  │  Transport Layer (pluggable):                                │ │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────┐          │ │
│  │  │ InMemory   │  │  SQLite     │  │ (Future:     │          │ │
│  │  │ Queue      │  │  Persistence│  │  Redis/etc.) │          │ │
│  │  └────────────┘  └─────────────┘  └──────────────┘          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│          ▲                        ▲                      ▲        │
│          │                        │                      │        │
│  ┌───────┴──────┐         ┌───────┴──────┐        ┌──────┴──────┐ │
│  │  Workers     │         │  Auditors    │        │   Human     │ │
│  │  (send/recv) │         │  (send/recv) │        │  Reviewer   │ │
│  └──────────────┘         └──────────────┘        └─────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Components

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **AgentMessage** | Message data structure | Dataclass with sender, receiver, content, metadata |
| **AgentMailbox** | Central message hub | Singleton managing all agent mailboxes |
| **MessageRouter** | Routes messages to destinations | Thread-safe routing by agent_id or topic |
| **MessageStore** | Persistence layer | SQLite for audit trail (optional) |
| **SubscriptionManager** | Pub/sub coordination | Topic-based subscriptions |
| **HumanReviewQueue** | Human oversight | Priority queue for messages requiring review |
| **MessageHistory** | Audit trail | Complete history with search/filter capabilities |

---

## 2. Message Format & Data Model

### 2.1 AgentMessage Dataclass

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import uuid

class MessageType(Enum):
    """Types of messages in the system."""
    TASK_ASSIGNMENT = "task_assignment"       # Assign task to worker
    TASK_RESULT = "task_result"               # Worker returns result
    AUDIT_REQUEST = "audit_request"           # Request audit of output
    AUDIT_RESULT = "audit_result"             # Auditor returns result
    CORRECTION_REQUEST = "correction_request" # Request worker corrections
    STATUS_UPDATE = "status_update"           # Status change notification
    HUMAN_REVIEW = "human_review"             # Requires human review
    BROADCAST = "broadcast"                   # Broadcast to all agents
    QUERY = "query"                          # Query/question message
    RESPONSE = "response"                    # Response to query

class MessagePriority(Enum):
    """Priority levels for messages."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class DeliveryMode(Enum):
    """How message should be delivered."""
    DIRECT = "direct"           # Direct to specific agent
    BROADCAST = "broadcast"     # To all agents
    TOPIC = "topic"            # To topic subscribers
    ROUND_ROBIN = "round_robin" # Load balance across agents

@dataclass
class AgentMessage:
    """
    A message sent between agents in the system.

    This is the core data structure for all agent communication.
    Designed to be serializable, traceable, and auditable.
    """
    # Identity
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Routing
    sender_id: str = ""                      # Agent ID of sender
    receiver_id: Optional[str] = None        # Agent ID of receiver (None for broadcast)
    topic: Optional[str] = None              # Topic for pub/sub
    delivery_mode: DeliveryMode = DeliveryMode.DIRECT

    # Content
    message_type: MessageType = MessageType.QUERY
    subject: str = ""                        # Brief subject line
    body: Dict[str, Any] = field(default_factory=dict)  # Message payload

    # Metadata
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None     # Links related messages
    reply_to: Optional[str] = None          # Message being replied to

    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Flags
    requires_human_review: bool = False
    is_delivered: bool = False
    is_read: bool = False

    # Audit trail
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_delivered(self) -> None:
        """Mark message as delivered."""
        self.is_delivered = True
        self.delivered_at = datetime.utcnow()

    def mark_read(self) -> None:
        """Mark message as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "topic": self.topic,
            "delivery_mode": self.delivery_mode.value,
            "message_type": self.message_type.value,
            "subject": self.subject,
            "body": self.body,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "created_at": self.created_at.isoformat(),
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "requires_human_review": self.requires_human_review,
            "is_delivered": self.is_delivered,
            "is_read": self.is_read,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create from dictionary."""
        # Parse enums and dates
        msg = cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            topic=data.get("topic"),
            delivery_mode=DeliveryMode(data["delivery_mode"]),
            message_type=MessageType(data["message_type"]),
            subject=data["subject"],
            body=data["body"],
            priority=MessagePriority(data["priority"]),
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            requires_human_review=data["requires_human_review"],
            is_delivered=data["is_delivered"],
            is_read=data["is_read"],
            metadata=data.get("metadata", {}),
        )

        # Parse timestamps
        if data.get("created_at"):
            msg.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("delivered_at"):
            msg.delivered_at = datetime.fromisoformat(data["delivered_at"])
        if data.get("read_at"):
            msg.read_at = datetime.fromisoformat(data["read_at"])
        if data.get("expires_at"):
            msg.expires_at = datetime.fromisoformat(data["expires_at"])

        return msg
```

### 2.2 Message Examples

#### Task Assignment Message
```python
AgentMessage(
    sender_id="orchestrator_001",
    receiver_id="literature_agent_001",
    message_type=MessageType.TASK_ASSIGNMENT,
    subject="Literature Review: Drug X Hepatotoxicity",
    body={
        "task_id": "task_12345",
        "task_type": "literature_review",
        "query": "Is there a causal relationship between Drug X and hepatotoxicity?",
        "context": {"drug_name": "Drug X", "adverse_event": "Hepatotoxicity"},
        "data_sources": ["pubmed", "clinical_trials_db"]
    },
    priority=MessagePriority.HIGH,
    correlation_id="case_abc123"
)
```

#### Audit Result Message
```python
AgentMessage(
    sender_id="literature_auditor_001",
    receiver_id="resolution_engine_001",
    message_type=MessageType.AUDIT_RESULT,
    subject="Audit Failed: Missing Evidence Chain",
    body={
        "task_id": "task_12345",
        "audit_status": "failed",
        "issues": [
            {
                "category": "missing_evidence",
                "severity": "critical",
                "description": "No primary sources cited for hepatotoxicity claim",
                "suggested_fix": "Add PMID references from PubMed search"
            }
        ],
        "recommendations": ["Search PubMed for primary studies", "Verify case reports"]
    },
    reply_to="msg_original_task_assignment",
    correlation_id="case_abc123",
    requires_human_review=False
)
```

---

## 3. Transport & Storage Strategy

### 3.1 Transport Layer (Pluggable Design)

```python
from abc import ABC, abstractmethod
from queue import Queue, PriorityQueue
from typing import Optional, List
import threading

class MessageTransport(ABC):
    """Abstract base for message transport implementations."""

    @abstractmethod
    def send(self, message: AgentMessage) -> bool:
        """Send a message."""
        pass

    @abstractmethod
    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Receive a message for an agent (blocking with timeout)."""
        pass

    @abstractmethod
    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """Peek at next message without removing (non-blocking)."""
        pass

    @abstractmethod
    def get_queue_size(self, agent_id: str) -> int:
        """Get number of pending messages for an agent."""
        pass


class InMemoryTransport(MessageTransport):
    """
    In-memory message transport using threading.Queue.

    Thread-safe, fast, suitable for single-process deployment.
    Messages lost on restart (no persistence).
    """

    def __init__(self):
        self.mailboxes: Dict[str, Queue] = {}
        self.lock = threading.Lock()

    def _get_mailbox(self, agent_id: str) -> Queue:
        """Get or create mailbox for agent."""
        with self.lock:
            if agent_id not in self.mailboxes:
                self.mailboxes[agent_id] = Queue()
            return self.mailboxes[agent_id]

    def send(self, message: AgentMessage) -> bool:
        """Send message to agent's queue."""
        mailbox = self._get_mailbox(message.receiver_id)
        mailbox.put(message)
        message.mark_delivered()
        return True

    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Receive next message (blocking with timeout)."""
        mailbox = self._get_mailbox(agent_id)
        try:
            message = mailbox.get(timeout=timeout)
            message.mark_read()
            return message
        except:
            return None

    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """Non-blocking peek at next message."""
        mailbox = self._get_mailbox(agent_id)
        if mailbox.empty():
            return None
        # Can't peek without removing in Queue, return None
        # (Would need custom implementation for true peek)
        return None

    def get_queue_size(self, agent_id: str) -> int:
        """Get pending message count."""
        mailbox = self._get_mailbox(agent_id)
        return mailbox.qsize()


class SQLiteTransport(MessageTransport):
    """
    SQLite-backed message transport with persistence.

    Slower than in-memory but provides:
    - Persistence across restarts
    - Full audit trail
    - Search/query capabilities
    """

    def __init__(self, db_path: str = "agent_mail.db"):
        self.db_path = db_path
        self._init_database()
        self.lock = threading.Lock()

    def _init_database(self) -> None:
        """Initialize SQLite schema."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                receiver_id TEXT,
                topic TEXT,
                delivery_mode TEXT,
                message_type TEXT,
                subject TEXT,
                body TEXT,  -- JSON serialized
                priority INTEGER,
                correlation_id TEXT,
                reply_to TEXT,
                created_at TEXT,
                delivered_at TEXT,
                read_at TEXT,
                expires_at TEXT,
                requires_human_review INTEGER,
                is_delivered INTEGER,
                is_read INTEGER,
                metadata TEXT,  -- JSON serialized
                INDEX idx_receiver (receiver_id, is_delivered, is_read),
                INDEX idx_topic (topic),
                INDEX idx_correlation (correlation_id)
            )
        """)

        conn.commit()
        conn.close()

    def send(self, message: AgentMessage) -> bool:
        """Store message in database."""
        import sqlite3
        import json

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                message.message_id,
                message.sender_id,
                message.receiver_id,
                message.topic,
                message.delivery_mode.value,
                message.message_type.value,
                message.subject,
                json.dumps(message.body),
                message.priority.value,
                message.correlation_id,
                message.reply_to,
                message.created_at.isoformat(),
                message.delivered_at.isoformat() if message.delivered_at else None,
                message.read_at.isoformat() if message.read_at else None,
                message.expires_at.isoformat() if message.expires_at else None,
                1 if message.requires_human_review else 0,
                1 if message.is_delivered else 0,
                1 if message.is_read else 0,
                json.dumps(message.metadata)
            ))

            conn.commit()
            conn.close()

            message.mark_delivered()
            return True

    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Fetch next unread message from database."""
        import sqlite3
        import json
        import time

        start_time = time.time()

        while True:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Fetch oldest unread message
                cursor.execute("""
                    SELECT * FROM messages
                    WHERE receiver_id = ? AND is_read = 0
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """, (agent_id,))

                row = cursor.fetchone()

                if row:
                    # Parse message
                    message = self._row_to_message(row)

                    # Mark as read
                    message.mark_read()
                    cursor.execute("""
                        UPDATE messages
                        SET is_read = 1, read_at = ?
                        WHERE message_id = ?
                    """, (message.read_at.isoformat(), message.message_id))

                    conn.commit()
                    conn.close()
                    return message

                conn.close()

            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None
            else:
                return None

            # Wait a bit before retrying
            time.sleep(0.1)

    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """Peek at next message without marking as read."""
        import sqlite3

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM messages
                WHERE receiver_id = ? AND is_read = 0
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """, (agent_id,))

            row = cursor.fetchone()
            conn.close()

            return self._row_to_message(row) if row else None

    def get_queue_size(self, agent_id: str) -> int:
        """Count unread messages."""
        import sqlite3

        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE receiver_id = ? AND is_read = 0
            """, (agent_id,))

            count = cursor.fetchone()[0]
            conn.close()
            return count

    def _row_to_message(self, row) -> AgentMessage:
        """Convert database row to AgentMessage."""
        import json
        # Implementation to parse row into AgentMessage
        # (Column mapping omitted for brevity)
        pass
```

### 3.2 Hybrid Transport (Best of Both)

```python
class HybridTransport(MessageTransport):
    """
    Hybrid transport: In-memory for speed + SQLite for persistence.

    - Messages delivered via in-memory queues (fast)
    - All messages also written to SQLite (audit trail)
    - On restart, can reload undelivered messages from SQLite
    """

    def __init__(self, db_path: str = "agent_mail.db"):
        self.memory = InMemoryTransport()
        self.sqlite = SQLiteTransport(db_path)

    def send(self, message: AgentMessage) -> bool:
        """Send via both transports."""
        # Write to SQLite first (durability)
        self.sqlite.send(message)
        # Then deliver via memory (speed)
        self.memory.send(message)
        return True

    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Receive from memory (fast path)."""
        message = self.memory.receive(agent_id, timeout)
        if message:
            # Update SQLite to mark as read
            self.sqlite._mark_read(message.message_id)
        return message

    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """Peek from memory."""
        return self.memory.peek(agent_id)

    def get_queue_size(self, agent_id: str) -> int:
        """Get size from memory."""
        return self.memory.get_queue_size(agent_id)
```

---

## 4. API Design

### 4.1 AgentMailbox (Central Hub)

```python
from typing import Optional, List, Callable
import threading
import logging

logger = logging.getLogger(__name__)


class AgentMailbox:
    """
    Central message hub for all agent communication.

    Responsibilities:
    - Message routing (direct, broadcast, topic-based)
    - Subscription management (pub/sub)
    - Human review queue
    - Message history and audit trail
    - Callback notifications

    Thread-safe singleton instance.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, transport: Optional[MessageTransport] = None):
        """
        Initialize the mailbox.

        Args:
            transport: Message transport layer (defaults to HybridTransport)
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return

        self.transport = transport or HybridTransport()
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [agent_ids]
        self.callbacks: Dict[str, List[Callable]] = {}  # agent_id -> [callback_fns]
        self.human_review_queue: PriorityQueue = PriorityQueue()
        self.message_history: List[AgentMessage] = []
        self._lock = threading.Lock()
        self._initialized = True

        logger.info("AgentMailbox initialized with transport: %s", type(self.transport).__name__)

    # ============================================================================
    # SENDING MESSAGES
    # ============================================================================

    def send(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        requires_human_review: bool = False,
        **kwargs
    ) -> str:
        """
        Send a direct message to a specific agent.

        Args:
            sender_id: ID of sending agent
            receiver_id: ID of receiving agent
            message_type: Type of message
            subject: Message subject
            body: Message payload
            priority: Message priority
            correlation_id: ID linking related messages
            requires_human_review: If True, route to human review queue
            **kwargs: Additional message attributes

        Returns:
            Message ID
        """
        message = AgentMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            subject=subject,
            body=body,
            priority=priority,
            correlation_id=correlation_id,
            requires_human_review=requires_human_review,
            delivery_mode=DeliveryMode.DIRECT,
            **kwargs
        )

        self._route_message(message)
        return message.message_id

    def broadcast(
        self,
        sender_id: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Broadcast message to all registered agents.

        Args:
            sender_id: ID of sending agent
            message_type: Type of message
            subject: Message subject
            body: Message payload
            **kwargs: Additional message attributes

        Returns:
            Message ID
        """
        message = AgentMessage(
            sender_id=sender_id,
            receiver_id=None,
            message_type=message_type,
            subject=subject,
            body=body,
            delivery_mode=DeliveryMode.BROADCAST,
            **kwargs
        )

        self._route_message(message)
        return message.message_id

    def publish(
        self,
        sender_id: str,
        topic: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Publish message to a topic (pub/sub pattern).

        Args:
            sender_id: ID of sending agent
            topic: Topic name
            message_type: Type of message
            subject: Message subject
            body: Message payload
            **kwargs: Additional message attributes

        Returns:
            Message ID
        """
        message = AgentMessage(
            sender_id=sender_id,
            topic=topic,
            message_type=message_type,
            subject=subject,
            body=body,
            delivery_mode=DeliveryMode.TOPIC,
            **kwargs
        )

        self._route_message(message)
        return message.message_id

    def reply(
        self,
        original_message: AgentMessage,
        sender_id: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Reply to a message (maintains conversation thread).

        Args:
            original_message: Message being replied to
            sender_id: ID of sending agent
            message_type: Type of message
            subject: Message subject
            body: Message payload
            **kwargs: Additional message attributes

        Returns:
            Message ID
        """
        message = AgentMessage(
            sender_id=sender_id,
            receiver_id=original_message.sender_id,
            message_type=message_type,
            subject=f"Re: {original_message.subject}",
            body=body,
            reply_to=original_message.message_id,
            correlation_id=original_message.correlation_id,
            delivery_mode=DeliveryMode.DIRECT,
            **kwargs
        )

        self._route_message(message)
        return message.message_id

    # ============================================================================
    # RECEIVING MESSAGES
    # ============================================================================

    def receive(
        self,
        agent_id: str,
        timeout: Optional[float] = None,
        blocking: bool = True
    ) -> Optional[AgentMessage]:
        """
        Receive next message for an agent.

        Args:
            agent_id: ID of agent receiving message
            timeout: Timeout in seconds (None = wait forever if blocking)
            blocking: If True, block until message arrives; if False, return None immediately

        Returns:
            Next message or None if no message available
        """
        if not blocking:
            timeout = 0.001  # Very short timeout for non-blocking

        message = self.transport.receive(agent_id, timeout=timeout)

        if message:
            logger.debug(
                f"Agent {agent_id} received message {message.message_id} "
                f"from {message.sender_id}: {message.subject}"
            )

        return message

    def peek(self, agent_id: str) -> Optional[AgentMessage]:
        """
        Peek at next message without removing from queue.

        Args:
            agent_id: ID of agent

        Returns:
            Next message or None
        """
        return self.transport.peek(agent_id)

    def receive_all(
        self,
        agent_id: str,
        max_messages: Optional[int] = None
    ) -> List[AgentMessage]:
        """
        Receive all pending messages for an agent.

        Args:
            agent_id: ID of agent
            max_messages: Maximum messages to retrieve (None = all)

        Returns:
            List of messages
        """
        messages = []
        count = 0

        while True:
            if max_messages and count >= max_messages:
                break

            message = self.receive(agent_id, timeout=0.001, blocking=False)
            if not message:
                break

            messages.append(message)
            count += 1

        return messages

    def get_pending_count(self, agent_id: str) -> int:
        """
        Get number of pending messages for an agent.

        Args:
            agent_id: ID of agent

        Returns:
            Count of pending messages
        """
        return self.transport.get_queue_size(agent_id)

    # ============================================================================
    # SUBSCRIPTION (PUB/SUB)
    # ============================================================================

    def subscribe(self, agent_id: str, topic: str) -> None:
        """
        Subscribe agent to a topic.

        Args:
            agent_id: ID of subscribing agent
            topic: Topic name
        """
        with self._lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []

            if agent_id not in self.subscriptions[topic]:
                self.subscriptions[topic].append(agent_id)
                logger.info(f"Agent {agent_id} subscribed to topic '{topic}'")

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """
        Unsubscribe agent from a topic.

        Args:
            agent_id: ID of agent
            topic: Topic name
        """
        with self._lock:
            if topic in self.subscriptions:
                if agent_id in self.subscriptions[topic]:
                    self.subscriptions[topic].remove(agent_id)
                    logger.info(f"Agent {agent_id} unsubscribed from topic '{topic}'")

    def get_topic_subscribers(self, topic: str) -> List[str]:
        """
        Get all subscribers to a topic.

        Args:
            topic: Topic name

        Returns:
            List of agent IDs
        """
        with self._lock:
            return self.subscriptions.get(topic, []).copy()

    # ============================================================================
    # CALLBACKS (PUSH NOTIFICATIONS)
    # ============================================================================

    def register_callback(
        self,
        agent_id: str,
        callback: Callable[[AgentMessage], None]
    ) -> None:
        """
        Register a callback function to be called when message arrives.

        This enables push-based notification instead of polling.

        Args:
            agent_id: ID of agent
            callback: Function to call with message
        """
        with self._lock:
            if agent_id not in self.callbacks:
                self.callbacks[agent_id] = []

            self.callbacks[agent_id].append(callback)
            logger.info(f"Registered callback for agent {agent_id}")

    def unregister_callback(
        self,
        agent_id: str,
        callback: Callable[[AgentMessage], None]
    ) -> None:
        """
        Unregister a callback function.

        Args:
            agent_id: ID of agent
            callback: Function to unregister
        """
        with self._lock:
            if agent_id in self.callbacks:
                if callback in self.callbacks[agent_id]:
                    self.callbacks[agent_id].remove(callback)

    # ============================================================================
    # HUMAN REVIEW
    # ============================================================================

    def get_human_review_queue(self) -> List[AgentMessage]:
        """
        Get all messages requiring human review.

        Returns:
            List of messages requiring review (sorted by priority)
        """
        messages = []
        temp_queue = []

        # Empty queue into list
        while not self.human_review_queue.empty():
            try:
                priority, message = self.human_review_queue.get_nowait()
                messages.append(message)
                temp_queue.append((priority, message))
            except:
                break

        # Restore queue
        for item in temp_queue:
            self.human_review_queue.put(item)

        # Sort by priority (highest first)
        messages.sort(key=lambda m: m.priority.value, reverse=True)
        return messages

    def approve_message(self, message_id: str) -> None:
        """
        Approve a message in human review queue and deliver it.

        Args:
            message_id: ID of message to approve
        """
        # Find and remove from review queue
        temp_queue = []
        message_to_approve = None

        while not self.human_review_queue.empty():
            try:
                priority, message = self.human_review_queue.get_nowait()
                if message.message_id == message_id:
                    message_to_approve = message
                else:
                    temp_queue.append((priority, message))
            except:
                break

        # Restore queue (minus approved message)
        for item in temp_queue:
            self.human_review_queue.put(item)

        # Deliver approved message
        if message_to_approve:
            message_to_approve.requires_human_review = False
            message_to_approve.metadata["human_approved"] = True
            message_to_approve.metadata["approved_at"] = datetime.utcnow().isoformat()
            self._route_message(message_to_approve)
            logger.info(f"Message {message_id} approved and delivered")

    def reject_message(self, message_id: str, reason: str = "") -> None:
        """
        Reject a message in human review queue.

        Args:
            message_id: ID of message to reject
            reason: Reason for rejection
        """
        # Find and remove from review queue
        temp_queue = []

        while not self.human_review_queue.empty():
            try:
                priority, message = self.human_review_queue.get_nowait()
                if message.message_id != message_id:
                    temp_queue.append((priority, message))
                else:
                    logger.info(f"Message {message_id} rejected: {reason}")
            except:
                break

        # Restore queue (minus rejected message)
        for item in temp_queue:
            self.human_review_queue.put(item)

    # ============================================================================
    # MESSAGE HISTORY & AUDIT TRAIL
    # ============================================================================

    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: Optional[int] = 100
    ) -> List[AgentMessage]:
        """
        Get message history with optional filtering.

        Args:
            agent_id: Filter by sender or receiver
            correlation_id: Filter by correlation ID
            limit: Maximum messages to return

        Returns:
            List of messages
        """
        with self._lock:
            messages = self.message_history.copy()

        # Apply filters
        if agent_id:
            messages = [
                m for m in messages
                if m.sender_id == agent_id or m.receiver_id == agent_id
            ]

        if correlation_id:
            messages = [
                m for m in messages
                if m.correlation_id == correlation_id
            ]

        # Sort by created_at (newest first)
        messages.sort(key=lambda m: m.created_at, reverse=True)

        # Limit
        if limit:
            messages = messages[:limit]

        return messages

    def get_conversation_thread(self, message_id: str) -> List[AgentMessage]:
        """
        Get full conversation thread for a message.

        Args:
            message_id: ID of message in thread

        Returns:
            List of messages in conversation (chronological order)
        """
        # Find the message
        message = None
        with self._lock:
            for m in self.message_history:
                if m.message_id == message_id:
                    message = m
                    break

        if not message:
            return []

        # Get all messages with same correlation_id
        correlation_id = message.correlation_id or message.message_id

        thread = []
        with self._lock:
            thread = [
                m for m in self.message_history
                if m.correlation_id == correlation_id or m.message_id == correlation_id
            ]

        # Sort chronologically
        thread.sort(key=lambda m: m.created_at)
        return thread

    # ============================================================================
    # INTERNAL METHODS
    # ============================================================================

    def _route_message(self, message: AgentMessage) -> None:
        """
        Route message based on delivery mode.

        Args:
            message: Message to route
        """
        # Add to history
        with self._lock:
            self.message_history.append(message)

        # Human review check
        if message.requires_human_review:
            priority = -message.priority.value  # Negative for PriorityQueue (higher priority = lower number)
            self.human_review_queue.put((priority, message))
            logger.info(f"Message {message.message_id} routed to human review queue")
            return

        # Route based on delivery mode
        if message.delivery_mode == DeliveryMode.DIRECT:
            self._deliver_direct(message)

        elif message.delivery_mode == DeliveryMode.BROADCAST:
            self._deliver_broadcast(message)

        elif message.delivery_mode == DeliveryMode.TOPIC:
            self._deliver_topic(message)

        # Trigger callbacks
        self._trigger_callbacks(message)

    def _deliver_direct(self, message: AgentMessage) -> None:
        """Deliver message to specific agent."""
        self.transport.send(message)
        logger.debug(
            f"Delivered message {message.message_id} to {message.receiver_id}"
        )

    def _deliver_broadcast(self, message: AgentMessage) -> None:
        """Deliver message to all registered agents."""
        # Get all unique agent IDs
        agent_ids = set()

        with self._lock:
            # From subscriptions
            for subscribers in self.subscriptions.values():
                agent_ids.update(subscribers)

            # From callbacks
            agent_ids.update(self.callbacks.keys())

        # Send to each agent
        for agent_id in agent_ids:
            msg_copy = AgentMessage(
                message_id=str(uuid.uuid4()),  # New ID for each copy
                sender_id=message.sender_id,
                receiver_id=agent_id,
                message_type=message.message_type,
                subject=message.subject,
                body=message.body.copy(),
                priority=message.priority,
                correlation_id=message.correlation_id,
                delivery_mode=DeliveryMode.DIRECT,
            )
            self.transport.send(msg_copy)

        logger.debug(
            f"Broadcast message {message.message_id} to {len(agent_ids)} agents"
        )

    def _deliver_topic(self, message: AgentMessage) -> None:
        """Deliver message to topic subscribers."""
        subscribers = self.get_topic_subscribers(message.topic)

        for agent_id in subscribers:
            msg_copy = AgentMessage(
                message_id=str(uuid.uuid4()),  # New ID for each copy
                sender_id=message.sender_id,
                receiver_id=agent_id,
                topic=message.topic,
                message_type=message.message_type,
                subject=message.subject,
                body=message.body.copy(),
                priority=message.priority,
                correlation_id=message.correlation_id,
                delivery_mode=DeliveryMode.DIRECT,
            )
            self.transport.send(msg_copy)

        logger.debug(
            f"Delivered topic message {message.message_id} to {len(subscribers)} subscribers"
        )

    def _trigger_callbacks(self, message: AgentMessage) -> None:
        """Trigger registered callbacks for message."""
        if not message.receiver_id:
            return

        callbacks = []
        with self._lock:
            callbacks = self.callbacks.get(message.receiver_id, []).copy()

        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                logger.error(
                    f"Error in callback for agent {message.receiver_id}: {e}"
                )
```

---

## 5. Integration with Agent-Audit-Resolve Pattern

### 5.1 Modified ResolutionEngine with Agent Mail

```python
class ResolutionEngineWithMail(ResolutionEngine):
    """
    Resolution engine enhanced with agent mail communication.

    Changes from original:
    - Sends TASK_ASSIGNMENT messages instead of direct method calls
    - Receives TASK_RESULT messages from workers
    - Sends AUDIT_REQUEST messages to auditors
    - Receives AUDIT_RESULT messages from auditors
    - Sends CORRECTION_REQUEST messages for retries
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        mailbox: AgentMailbox,
        max_retries: int = 2,
        enable_intelligent_resolution: bool = True,
    ):
        super().__init__(
            task_executor, audit_engine, max_retries, enable_intelligent_resolution
        )
        self.mailbox = mailbox
        self.agent_id = "resolution_engine_001"

    def execute_with_validation(self, task: Task) -> tuple[ResolutionDecision, Optional[AuditResult]]:
        """
        Execute task with validation using agent mail communication.
        """
        task.max_retries = self.max_retries
        resolution_log = []
        correlation_id = task.task_id  # Use task_id as correlation

        logger.info(f"Starting execution with validation for task {task.task_id}")

        while True:
            try:
                # Step 1: Send TASK_ASSIGNMENT message to worker
                logger.info(f"Sending task assignment for {task.task_id}")

                self.mailbox.send(
                    sender_id=self.agent_id,
                    receiver_id=self._get_worker_agent_id(task.task_type),
                    message_type=MessageType.TASK_ASSIGNMENT,
                    subject=f"Execute Task: {task.task_type.value}",
                    body={
                        "task_id": task.task_id,
                        "task_type": task.task_type.value,
                        "input_data": task.input_data,
                        "retry_count": task.retry_count,
                    },
                    priority=MessagePriority.HIGH,
                    correlation_id=correlation_id,
                )

                # Step 2: Wait for TASK_RESULT message from worker
                logger.info(f"Waiting for task result from worker")

                result_message = self._wait_for_message(
                    message_type=MessageType.TASK_RESULT,
                    correlation_id=correlation_id,
                    timeout=300.0  # 5 minutes
                )

                if not result_message:
                    raise TimeoutError(f"Worker did not respond for task {task.task_id}")

                # Update task with result
                task.output_data = result_message.body.get("output")
                task.update_status(TaskStatus.COMPLETED)

                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "executed",
                    "status": "success",
                })

                # Step 3: Send AUDIT_REQUEST message to auditor
                logger.info(f"Sending audit request for task {task.task_id}")

                task.update_status(TaskStatus.AUDITING)

                self.mailbox.send(
                    sender_id=self.agent_id,
                    receiver_id=self._get_auditor_agent_id(task.task_type),
                    message_type=MessageType.AUDIT_REQUEST,
                    subject=f"Audit Task: {task.task_type.value}",
                    body={
                        "task_id": task.task_id,
                        "task_input": task.input_data,
                        "task_output": task.output_data,
                        "task_metadata": task.metadata,
                    },
                    priority=MessagePriority.HIGH,
                    correlation_id=correlation_id,
                )

                # Step 4: Wait for AUDIT_RESULT message from auditor
                logger.info(f"Waiting for audit result")

                audit_message = self._wait_for_message(
                    message_type=MessageType.AUDIT_RESULT,
                    correlation_id=correlation_id,
                    timeout=60.0  # 1 minute
                )

                if not audit_message:
                    raise TimeoutError(f"Auditor did not respond for task {task.task_id}")

                # Parse audit result
                audit_result = self._parse_audit_result(audit_message.body)
                task.add_audit_result(audit_result)

                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "audited",
                    "status": audit_result.status.value,
                    "issues_count": len(audit_result.issues),
                })

                # Step 5: Evaluate audit result (same as original)
                decision = self._evaluate_audit_result(task, audit_result)

                if decision == ResolutionDecision.ACCEPT:
                    logger.info(f"Task {task.task_id} accepted after validation")
                    task.update_status(TaskStatus.COMPLETED)
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.RETRY:
                    logger.info(f"Task {task.task_id} requires revision")
                    task.update_status(TaskStatus.REQUIRES_REVISION)
                    task.increment_retry()

                    # Send CORRECTION_REQUEST message to worker
                    corrections = self._prepare_corrections(audit_result)
                    task.input_data["corrections"] = corrections
                    task.input_data["previous_output"] = task.output_data
                    task.input_data["audit_feedback"] = audit_result.summary

                    resolution_log.append({
                        "attempt": task.retry_count,
                        "action": "retry_scheduled",
                        "corrections_count": len(corrections),
                    })

                    # Continue loop to retry
                    continue

                elif decision == ResolutionDecision.ESCALATE:
                    logger.warning(f"Task {task.task_id} escalated to human review")
                    task.update_status(TaskStatus.AUDIT_FAILED)
                    task.metadata["requires_human_review"] = True
                    task.metadata["escalation_reason"] = "Critical audit issues found"

                    # Send HUMAN_REVIEW message
                    self.mailbox.send(
                        sender_id=self.agent_id,
                        receiver_id="human_reviewer",
                        message_type=MessageType.HUMAN_REVIEW,
                        subject=f"Task {task.task_id} Requires Review",
                        body={
                            "task_id": task.task_id,
                            "audit_result": audit_result.to_dict(),
                            "resolution_history": resolution_log,
                        },
                        priority=MessagePriority.CRITICAL,
                        correlation_id=correlation_id,
                        requires_human_review=True,
                    )

                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

                elif decision == ResolutionDecision.ABORT:
                    logger.error(f"Task {task.task_id} aborted")
                    task.update_status(TaskStatus.FAILED)
                    task.metadata["abort_reason"] = "Max retries exceeded"
                    self._save_resolution_history(task.task_id, resolution_log)
                    return decision, audit_result

            except Exception as e:
                logger.error(f"Error in resolution loop: {e}")
                resolution_log.append({
                    "attempt": task.retry_count + 1,
                    "action": "error",
                    "error": str(e),
                })
                task.update_status(TaskStatus.FAILED)
                task.metadata["error"] = str(e)
                self._save_resolution_history(task.task_id, resolution_log)
                return ResolutionDecision.ABORT, None

    def _wait_for_message(
        self,
        message_type: MessageType,
        correlation_id: str,
        timeout: float
    ) -> Optional[AgentMessage]:
        """
        Wait for a specific type of message with correlation ID.
        """
        start_time = time.time()

        while True:
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                logger.error(
                    f"Timeout waiting for {message_type.value} "
                    f"with correlation_id={correlation_id}"
                )
                return None

            # Try to receive message
            message = self.mailbox.receive(
                agent_id=self.agent_id,
                timeout=1.0,
                blocking=True
            )

            if not message:
                continue

            # Check if this is the message we're waiting for
            if (message.message_type == message_type and
                message.correlation_id == correlation_id):
                return message

            # Not the message we want, put it back (or handle it)
            logger.warning(
                f"Received unexpected message {message.message_id} "
                f"of type {message.message_type.value}, expected {message_type.value}"
            )
            # In a real implementation, might want to buffer these messages

    def _get_worker_agent_id(self, task_type: TaskType) -> str:
        """Get worker agent ID for task type."""
        # Map task type to worker agent ID
        # In practice, this would query a registry
        return f"{task_type.value}_worker_001"

    def _get_auditor_agent_id(self, task_type: TaskType) -> str:
        """Get auditor agent ID for task type."""
        return f"{task_type.value}_auditor_001"

    def _parse_audit_result(self, body: Dict[str, Any]) -> AuditResult:
        """Parse audit result from message body."""
        # Convert message body to AuditResult object
        return AuditResult(
            task_id=body["task_id"],
            auditor_agent=body["auditor_agent"],
            status=AuditStatus(body["status"]),
            issues=[ValidationIssue(**issue) for issue in body.get("issues", [])],
            passed_checks=body.get("passed_checks", []),
            failed_checks=body.get("failed_checks", []),
            summary=body.get("summary", ""),
            recommendations=body.get("recommendations", []),
        )
```

### 5.2 Modified BaseWorker with Agent Mail

```python
class BaseWorkerWithMail(BaseWorker):
    """
    Enhanced base worker with agent mail support.

    Workers now:
    - Listen for TASK_ASSIGNMENT messages
    - Execute work asynchronously
    - Send TASK_RESULT messages when complete
    """

    def __init__(self, agent_id: str, mailbox: AgentMailbox, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.mailbox = mailbox
        self.is_running = False
        self.worker_thread = None

    def start(self) -> None:
        """Start listening for task assignments."""
        if self.is_running:
            logger.warning(f"{self.agent_id} already running")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"{self.agent_id} started and listening for messages")

    def stop(self) -> None:
        """Stop listening for messages."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        logger.info(f"{self.agent_id} stopped")

    def _message_loop(self) -> None:
        """Main message processing loop."""
        while self.is_running:
            try:
                # Receive next message (blocking with timeout)
                message = self.mailbox.receive(
                    agent_id=self.agent_id,
                    timeout=1.0,
                    blocking=True
                )

                if not message:
                    continue

                # Handle message based on type
                if message.message_type == MessageType.TASK_ASSIGNMENT:
                    self._handle_task_assignment(message)

                elif message.message_type == MessageType.CORRECTION_REQUEST:
                    self._handle_correction_request(message)

                else:
                    logger.warning(
                        f"{self.agent_id} received unexpected message type: "
                        f"{message.message_type.value}"
                    )

            except Exception as e:
                logger.error(f"Error in message loop for {self.agent_id}: {e}")

    def _handle_task_assignment(self, message: AgentMessage) -> None:
        """Handle task assignment message."""
        try:
            logger.info(f"{self.agent_id} handling task assignment")

            # Extract task data
            task_id = message.body["task_id"]
            input_data = message.body["input_data"]

            # Execute task
            output = self.execute(input_data)

            # Send result back
            self.mailbox.reply(
                original_message=message,
                sender_id=self.agent_id,
                message_type=MessageType.TASK_RESULT,
                subject=f"Task {task_id} Complete",
                body={
                    "task_id": task_id,
                    "output": output,
                    "agent_id": self.agent_id,
                },
                priority=MessagePriority.HIGH,
            )

            logger.info(f"{self.agent_id} completed task {task_id}")

        except Exception as e:
            logger.error(f"{self.agent_id} failed to execute task: {e}")

            # Send error message
            self.mailbox.reply(
                original_message=message,
                sender_id=self.agent_id,
                message_type=MessageType.TASK_RESULT,
                subject=f"Task {message.body['task_id']} Failed",
                body={
                    "task_id": message.body["task_id"],
                    "error": str(e),
                    "agent_id": self.agent_id,
                },
                priority=MessagePriority.HIGH,
            )
```

---

## 6. Usage Examples

### 6.1 Basic Send/Receive

```python
# Initialize mailbox
mailbox = AgentMailbox(transport=HybridTransport())

# Send a message
message_id = mailbox.send(
    sender_id="orchestrator_001",
    receiver_id="literature_agent_001",
    message_type=MessageType.TASK_ASSIGNMENT,
    subject="Review Drug X hepatotoxicity literature",
    body={
        "query": "Is there a causal relationship?",
        "data_sources": ["pubmed"]
    },
    priority=MessagePriority.HIGH,
    correlation_id="case_abc123"
)

# Receive message
message = mailbox.receive(
    agent_id="literature_agent_001",
    timeout=5.0,
    blocking=True
)

print(f"Received: {message.subject}")
```

### 6.2 Pub/Sub Pattern

```python
# Subscribe to topic
mailbox.subscribe(agent_id="auditor_001", topic="task_completed")
mailbox.subscribe(agent_id="auditor_002", topic="task_completed")

# Publish to topic
mailbox.publish(
    sender_id="worker_001",
    topic="task_completed",
    message_type=MessageType.STATUS_UPDATE,
    subject="Task completed successfully",
    body={"task_id": "task_123", "status": "completed"}
)

# Both auditors will receive the message
```

### 6.3 Request-Reply Pattern

```python
# Send request
request_msg = mailbox.send(
    sender_id="orchestrator",
    receiver_id="worker",
    message_type=MessageType.QUERY,
    subject="What's your current workload?",
    body={"query": "workload_status"}
)

# Worker receives and replies
request = mailbox.receive(agent_id="worker")
mailbox.reply(
    original_message=request,
    sender_id="worker",
    message_type=MessageType.RESPONSE,
    subject="Re: What's your current workload?",
    body={"workload": "3 tasks pending"}
)
```

### 6.4 Human Review Queue

```python
# Send message requiring review
mailbox.send(
    sender_id="auditor",
    receiver_id="orchestrator",
    message_type=MessageType.AUDIT_RESULT,
    subject="Critical issues found",
    body={"issues": [...]},
    requires_human_review=True,
    priority=MessagePriority.CRITICAL
)

# Human reviewer checks queue
review_queue = mailbox.get_human_review_queue()
for msg in review_queue:
    print(f"Review needed: {msg.subject}")

    # Approve or reject
    if should_approve(msg):
        mailbox.approve_message(msg.message_id)
    else:
        mailbox.reject_message(msg.message_id, reason="Insufficient evidence")
```

### 6.5 Message History / Audit Trail

```python
# Get conversation thread
thread = mailbox.get_conversation_thread(message_id="msg_123")
for msg in thread:
    print(f"{msg.created_at}: {msg.sender_id} -> {msg.receiver_id}: {msg.subject}")

# Get all messages for a case
case_messages = mailbox.get_message_history(
    correlation_id="case_abc123",
    limit=None  # Get all
)

# Generate audit report
for msg in case_messages:
    print(f"[{msg.message_type.value}] {msg.sender_id} -> {msg.receiver_id}")
    print(f"  Subject: {msg.subject}")
    print(f"  Time: {msg.created_at}")
    print()
```

---

## 7. Migration Strategy

### 7.1 Phase 1: Parallel Deployment (Week 1)

**Goal**: Add agent mail alongside existing synchronous calls

```python
# Both patterns work simultaneously
class ResolutionEngineHybrid(ResolutionEngine):
    def __init__(self, ..., mailbox=None, use_mail=False):
        super().__init__(...)
        self.mailbox = mailbox
        self.use_mail = use_mail  # Feature flag

    def execute_with_validation(self, task):
        if self.use_mail:
            return self._execute_with_mail(task)
        else:
            return self._execute_synchronous(task)
```

**Actions**:
- Implement core agent mail components
- Add opt-in flag to enable mail-based communication
- Deploy with mail disabled by default
- Add tests comparing sync vs mail behavior

### 7.2 Phase 2: Gradual Migration (Week 2)

**Goal**: Migrate one component at a time

1. **Start with non-critical paths**: Migrate status updates, logging
2. **Then migrate audit results**: Auditors send via mail
3. **Then migrate task results**: Workers send via mail
4. **Finally migrate task assignments**: Full async communication

**Actions**:
- Enable mail for each component incrementally
- Monitor message delivery, latency, errors
- Compare audit trail completeness
- Verify no regressions

### 7.3 Phase 3: Full Migration (Optional)

**Goal**: Remove synchronous code paths

**Actions**:
- Remove feature flags
- Delete old synchronous methods
- Update all tests to use mail
- Document new patterns

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
def test_send_receive():
    """Test basic send/receive."""
    mailbox = AgentMailbox(transport=InMemoryTransport())

    msg_id = mailbox.send(
        sender_id="sender",
        receiver_id="receiver",
        message_type=MessageType.QUERY,
        subject="Test",
        body={"data": "test"}
    )

    message = mailbox.receive(agent_id="receiver", timeout=1.0)

    assert message is not None
    assert message.message_id == msg_id
    assert message.subject == "Test"
    assert message.body["data"] == "test"


def test_pub_sub():
    """Test publish/subscribe."""
    mailbox = AgentMailbox()

    mailbox.subscribe("agent1", "topic_a")
    mailbox.subscribe("agent2", "topic_a")

    mailbox.publish(
        sender_id="publisher",
        topic="topic_a",
        message_type=MessageType.BROADCAST,
        subject="Event",
        body={}
    )

    msg1 = mailbox.receive("agent1", timeout=1.0)
    msg2 = mailbox.receive("agent2", timeout=1.0)

    assert msg1 is not None
    assert msg2 is not None
    assert msg1.subject == "Event"
    assert msg2.subject == "Event"


def test_human_review_queue():
    """Test human review queue."""
    mailbox = AgentMailbox()

    mailbox.send(
        sender_id="auditor",
        receiver_id="orchestrator",
        message_type=MessageType.AUDIT_RESULT,
        subject="Critical issue",
        body={},
        requires_human_review=True,
        priority=MessagePriority.CRITICAL
    )

    queue = mailbox.get_human_review_queue()
    assert len(queue) == 1
    assert queue[0].subject == "Critical issue"

    # Approve message
    mailbox.approve_message(queue[0].message_id)

    # Should be delivered now
    msg = mailbox.receive("orchestrator", timeout=1.0)
    assert msg is not None
    assert msg.metadata.get("human_approved") is True
```

### 8.2 Integration Tests

```python
def test_full_agent_workflow():
    """Test complete agent workflow with mail."""
    mailbox = AgentMailbox()

    # Create workers with mail support
    worker = LiteratureAgentWithMail(
        agent_id="lit_worker_001",
        mailbox=mailbox
    )
    worker.start()

    auditor = LiteratureAuditorWithMail(
        agent_id="lit_auditor_001",
        mailbox=mailbox
    )
    auditor.start()

    resolution = ResolutionEngineWithMail(
        task_executor=None,
        audit_engine=None,
        mailbox=mailbox
    )

    # Create task
    task = Task(
        task_type=TaskType.LITERATURE_REVIEW,
        input_data={"query": "Test query"}
    )

    # Execute with validation
    decision, audit_result = resolution.execute_with_validation(task)

    # Verify
    assert decision == ResolutionDecision.ACCEPT
    assert task.status == TaskStatus.COMPLETED

    # Check message history
    history = mailbox.get_message_history(correlation_id=task.task_id)
    assert len(history) >= 4  # Assignment, result, audit request, audit result

    # Cleanup
    worker.stop()
    auditor.stop()
```

### 8.3 Performance Tests

```python
def test_message_throughput():
    """Test message throughput."""
    mailbox = AgentMailbox(transport=InMemoryTransport())

    # Send 1000 messages
    start = time.time()
    for i in range(1000):
        mailbox.send(
            sender_id="sender",
            receiver_id="receiver",
            message_type=MessageType.QUERY,
            subject=f"Message {i}",
            body={"index": i}
        )
    send_time = time.time() - start

    # Receive 1000 messages
    start = time.time()
    for i in range(1000):
        msg = mailbox.receive("receiver", timeout=1.0)
        assert msg is not None
    receive_time = time.time() - start

    print(f"Send: {1000/send_time:.0f} msg/sec")
    print(f"Receive: {1000/receive_time:.0f} msg/sec")

    # Should handle >1000 msg/sec easily


def test_sqlite_persistence():
    """Test SQLite persistence overhead."""
    import tempfile
    import os

    db_path = os.path.join(tempfile.gettempdir(), "test_mail.db")
    mailbox = AgentMailbox(transport=SQLiteTransport(db_path))

    # Send messages
    start = time.time()
    for i in range(100):
        mailbox.send(
            sender_id="sender",
            receiver_id="receiver",
            message_type=MessageType.QUERY,
            subject=f"Message {i}",
            body={"index": i}
        )
    elapsed = time.time() - start

    print(f"SQLite throughput: {100/elapsed:.0f} msg/sec")

    # Cleanup
    os.remove(db_path)
```

---

## 9. Performance Characteristics

### 9.1 Latency

| Transport | Send Latency | Receive Latency | Total Round-Trip |
|-----------|--------------|-----------------|------------------|
| InMemory | <1ms | <1ms (blocking) | ~2ms |
| SQLite | ~5-10ms | ~5-10ms | ~15-20ms |
| Hybrid | ~5-10ms | <1ms | ~10-15ms |

**Recommendation**: Use Hybrid for production (fast receive, persistent send)

### 9.2 Throughput

| Transport | Messages/sec | Notes |
|-----------|--------------|-------|
| InMemory | >10,000 | Limited by GIL |
| SQLite | ~100-500 | Limited by disk I/O |
| Hybrid | ~500-1000 | Write bottleneck |

**Recommendation**: For high-throughput scenarios (>1000 msg/sec), consider Redis transport

### 9.3 Memory Usage

- **InMemory**: ~1KB per message in queue
- **SQLite**: ~500 bytes per message on disk
- **Hybrid**: Both (1KB memory + 500B disk)

**Recommendation**: Set max queue size limits and implement message expiration

---

## 10. Future Enhancements

### 10.1 Phase 2 Features (Weeks 3-4)

1. **Redis Transport**
   - Distributed deployment
   - >10,000 msg/sec throughput
   - Pub/sub scaling

2. **Message Acknowledgments**
   - Guaranteed delivery
   - Retry on failure
   - Dead letter queue

3. **Priority Queues**
   - CRITICAL messages jump queue
   - Fair scheduling

4. **Message Compression**
   - Reduce storage for large payloads
   - Transparent compression/decompression

### 10.2 Phase 3 Features (Weeks 5-6)

1. **Agent Discovery**
   - Dynamic agent registration
   - Health checks
   - Load balancing

2. **Message Encryption**
   - End-to-end encryption for sensitive data
   - Key management

3. **Monitoring Dashboard**
   - Message flow visualization
   - Performance metrics
   - Alert on anomalies

4. **Multi-Tenancy**
   - Isolated mailboxes per tenant
   - Access controls

---

## 11. Summary & Recommendations

### 11.1 Recommended Architecture

**For 1-2 week implementation**:

```
┌────────────────────────────────────────────┐
│  AgentMailbox (Central Hub)                │
│                                            │
│  Transport: HybridTransport                │
│  - InMemory queues for fast delivery      │
│  - SQLite for persistence & audit trail   │
│                                            │
│  Features:                                 │
│  - Direct messaging (send/receive)         │
│  - Pub/sub (topics)                        │
│  - Human review queue                      │
│  - Message history                         │
│  - Correlation IDs for threads             │
└────────────────────────────────────────────┘
```

**Dependencies**: Python 3.11 stdlib only (queue, threading, sqlite3)

**Migration**: Opt-in with feature flags, gradual rollout

### 11.2 What This Enables

1. **Async Communication**: Workers/auditors don't block orchestrator
2. **Observable**: Complete message history for debugging
3. **Human Oversight**: Review queue for critical decisions
4. **Flexible Routing**: Direct, broadcast, pub/sub patterns
5. **Audit Trail**: Every interaction logged and searchable
6. **Future-Proof**: Easy to swap InMemory → Redis later

### 11.3 Integration Points

| Component | Change Required | Effort |
|-----------|----------------|--------|
| BaseWorker | Add mail support, message loop | 1 day |
| BaseAuditor | Add mail support, message loop | 1 day |
| ResolutionEngine | Replace method calls with messages | 2 days |
| TaskExecutor | Add mail-based routing | 1 day |
| Orchestrator | Optional: use mail for coordination | 1 day |
| Models | No changes needed | 0 days |

**Total Effort**: ~6-8 days for core implementation

### 11.4 Key Design Decisions

1. **Transport**: Hybrid (InMemory + SQLite) for speed + persistence
2. **Message Format**: Dataclass (like existing models) for consistency
3. **Delivery**: Both push (callbacks) and pull (polling) supported
4. **Addressing**: Agent IDs (direct) + Topics (pub/sub)
5. **Threading**: Thread-safe queues, compatible with existing ThreadPoolExecutor

---

## 12. File Structure

```
safety-research-system/
├── core/
│   ├── agent_mail/
│   │   ├── __init__.py
│   │   ├── message.py              # AgentMessage, enums
│   │   ├── transport.py            # Transport implementations
│   │   ├── mailbox.py              # AgentMailbox hub
│   │   ├── router.py               # MessageRouter
│   │   └── history.py              # MessageHistory, audit queries
│   ├── resolution_engine_mail.py   # Mail-enabled resolution engine
│   └── task_executor_mail.py       # Mail-enabled task executor
├── agents/
│   ├── base_worker_mail.py         # Mail-enabled base worker
│   └── base_auditor_mail.py        # Mail-enabled base auditor
├── tests/
│   ├── test_agent_mail.py          # Mail system tests
│   └── test_mail_integration.py    # Integration tests
└── docs/
    └── agent_mail_system_design.md # This document
```

---

## Conclusion

This agent mail system is designed specifically for the safety-research-system's needs:

- **Minimal**: Uses only Python stdlib, no external dependencies
- **Focused**: Solves async communication, audit trail, human oversight
- **Clean Integration**: Non-breaking, opt-in migration
- **Simple**: Can be implemented in 1-2 weeks
- **Extensible**: Easy to add Redis/RabbitMQ later

The system preserves the Agent-Audit-Resolve pattern while adding:
- Asynchronous execution
- Complete observability
- Human review capabilities
- Flexible routing patterns

This foundation supports future enhancements like distributed deployment, advanced monitoring, and multi-agent collaboration.
