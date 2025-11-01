# Phase 1 Implementation Plan: Mail System Foundation

**Date:** 2025-11-01
**Phase:** 1 - Foundation
**Duration Estimate:** 2-3 weeks
**Lines of Code Estimate:** ~2000 LOC
**Status:** Ready for Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Component Breakdown](#component-breakdown)
3. [Implementation Sequence](#implementation-sequence)
4. [Integration Points](#integration-points)
5. [Testing Strategy](#testing-strategy)
6. [Success Criteria](#success-criteria)
7. [File Structure](#file-structure)
8. [Dependencies](#dependencies)

---

## Overview

### Goals

Phase 1 establishes the foundational infrastructure for multi-agent mail-based communication:

1. **Message System**: Core message model with serialization and validation
2. **Mailbox System**: Personal inbox/outbox for each agent
3. **Mail Broker**: Central message routing and delivery service
4. **Storage Backend**: In-memory storage for messages
5. **Agent Registry**: Discovery and registration of agents

### Key Principles

- **Simplicity First**: Start with in-memory implementation
- **Type Safety**: Comprehensive type hints throughout
- **Existing Patterns**: Follow established codebase conventions
- **Clean Integration**: Non-invasive additions to existing system
- **Testing**: Unit tests for all components

### Non-Goals (Deferred to Later Phases)

- Persistent storage (Phase 2-3)
- Complex protocols (Phase 2)
- Collaborative planning (Phase 3)
- Production features (Phase 4)
- Claude Code instance integration (Phase 5)

---

## Component Breakdown

### Component 1: Message System

**Location**: `/home/user/safety-research-system/core/mail/message.py`

#### 1.1 Message Class

**Purpose**: Standard message format for agent communication

**Class Signature**:
```python
@dataclass
class Message:
    """
    Standard message format for agent-to-agent communication.

    Messages are the fundamental unit of communication in the mail system.
    They support threading, priorities, attachments, and TTL.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_ids: List[str]
    message_type: MessageType
    subject: str
    body: Dict[str, Any]
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: MessagePriority = MessagePriority.NORMAL
    ttl: Optional[int] = None  # Time to live in seconds
    attachments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize message for storage/transmission."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Deserialize message from dictionary."""

    def is_expired(self) -> bool:
        """Check if message has exceeded TTL."""

    def validate(self) -> bool:
        """Validate message fields."""
```

**Key Methods**:

| Method | Responsibility | Returns | LOC |
|--------|---------------|---------|-----|
| `to_dict()` | Serialize to dictionary | `Dict[str, Any]` | 15 |
| `from_dict()` | Deserialize from dictionary | `Message` | 20 |
| `is_expired()` | Check TTL expiration | `bool` | 5 |
| `validate()` | Validate all fields | `bool` | 15 |

**Dependencies**: None (core Python only)

**Estimated LOC**: 100

---

#### 1.2 MessageType Enum

**Purpose**: Define standard message types for different communication patterns

**Class Signature**:
```python
class MessageType(Enum):
    """Types of messages for agent communication."""
    REQUEST = "request"              # Request for action/information
    RESPONSE = "response"            # Response to a request
    BROADCAST = "broadcast"          # Broadcast to all subscribers
    NOTIFICATION = "notification"    # One-way notification
    QUERY = "query"                  # Query for information
    PROPOSAL = "proposal"            # Proposal for consideration
    AGREEMENT = "agreement"          # Agreement/acceptance
    REJECTION = "rejection"          # Rejection/decline
    STATUS_UPDATE = "status_update"  # Status change notification
```

**Estimated LOC**: 15

---

#### 1.3 MessagePriority Enum

**Purpose**: Define priority levels for message delivery ordering

**Class Signature**:
```python
class MessagePriority(Enum):
    """Priority levels for message delivery."""
    URGENT = 1    # Deliver immediately
    HIGH = 2      # High priority
    NORMAL = 3    # Normal priority (default)
    LOW = 4       # Low priority

    def __lt__(self, other):
        """Enable priority comparison for queue sorting."""
        return self.value < other.value
```

**Estimated LOC**: 15

---

### Component 2: Mailbox System

**Location**: `/home/user/safety-research-system/core/mail/mailbox.py`

#### 2.1 Mailbox Class

**Purpose**: Personal inbox/outbox for each agent instance

**Class Signature**:
```python
class Mailbox:
    """
    Agent's personal mailbox for sending and receiving messages.

    Each agent has one mailbox with an inbox queue and outbox queue.
    Supports message filtering, threading, and retrieval.
    """

    def __init__(
        self,
        agent_id: str,
        storage_backend: 'MailStorage',
        max_inbox_size: int = 1000
    ):
        """
        Initialize mailbox for an agent.

        Args:
            agent_id: Unique identifier for the agent
            storage_backend: Storage backend for message persistence
            max_inbox_size: Maximum messages in inbox (prevents overflow)
        """
        self.agent_id = agent_id
        self.inbox: PriorityQueue = PriorityQueue()
        self.outbox: Queue = Queue()
        self.storage = storage_backend
        self.filters: List[Callable[[Message], bool]] = []
        self.max_inbox_size = max_inbox_size
        self._lock = threading.Lock()
        logger.info(f"Mailbox initialized for agent: {agent_id}")

    def send(self, message: Message) -> str:
        """
        Send a message (places in outbox for broker to deliver).

        Args:
            message: Message to send

        Returns:
            message_id of sent message

        Raises:
            ValueError: If message validation fails
        """

    def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Retrieve next message from inbox (blocking with timeout).

        Messages are delivered in priority order (URGENT first).

        Args:
            timeout: Seconds to wait for message (None = block forever)

        Returns:
            Message if available, None if timeout
        """

    def check_inbox(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Check inbox without removing messages (peek).

        Args:
            filters: Filter criteria (sender_id, message_type, etc.)
            limit: Maximum messages to return

        Returns:
            List of messages matching filters
        """

    def add_filter(self, filter_fn: Callable[[Message], bool]) -> None:
        """
        Add filter for incoming messages.

        Filters are applied when messages are delivered to inbox.
        Messages failing filters are rejected.

        Args:
            filter_fn: Function that returns True to accept message
        """

    def get_thread(self, thread_id: str) -> List[Message]:
        """
        Get all messages in a conversation thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of messages in chronological order
        """

    def get_inbox_size(self) -> int:
        """Get current inbox size."""

    def get_outbox_size(self) -> int:
        """Get current outbox size."""

    def clear_inbox(self) -> int:
        """Clear all messages from inbox. Returns number cleared."""

    def _apply_filters(self, message: Message) -> bool:
        """Apply all filters to incoming message."""
```

**Key Methods**:

| Method | Responsibility | Returns | LOC |
|--------|---------------|---------|-----|
| `send()` | Add message to outbox | `str` (message_id) | 20 |
| `receive()` | Get next message from inbox | `Optional[Message]` | 15 |
| `check_inbox()` | Peek at inbox without removal | `List[Message]` | 25 |
| `add_filter()` | Add message filter | `None` | 5 |
| `get_thread()` | Retrieve conversation thread | `List[Message]` | 30 |
| `get_inbox_size()` | Get inbox queue size | `int` | 3 |
| `get_outbox_size()` | Get outbox queue size | `int` | 3 |
| `clear_inbox()` | Clear inbox | `int` | 10 |
| `_apply_filters()` | Apply filters to message | `bool` | 15 |

**Dependencies**:
- `core.mail.message.Message`
- `core.mail.storage.MailStorage`

**Estimated LOC**: 200

---

### Component 3: Mail Broker

**Location**: `/home/user/safety-research-system/core/mail/broker.py`

#### 3.1 MailBroker Class

**Purpose**: Central message routing and delivery service

**Class Signature**:
```python
class MailBroker:
    """
    Central message routing and delivery service.

    The broker manages all mailboxes and handles message delivery.
    Runs a background thread that continuously delivers messages
    from agent outboxes to recipient inboxes.

    Thread-safe for concurrent access.
    """

    def __init__(
        self,
        storage: 'MailStorage',
        delivery_interval: float = 0.1  # seconds between delivery cycles
    ):
        """
        Initialize mail broker.

        Args:
            storage: Storage backend for message persistence
            delivery_interval: Seconds to wait between delivery cycles
        """
        self.mailboxes: Dict[str, Mailbox] = {}
        self.storage = storage
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [agent_ids]
        self.delivery_interval = delivery_interval
        self.delivery_thread: Optional[threading.Thread] = None
        self.running = False
        self._lock = threading.Lock()
        logger.info("MailBroker initialized")

    def register_mailbox(self, agent_id: str) -> Mailbox:
        """
        Create and register mailbox for new agent.

        Args:
            agent_id: Unique identifier for agent

        Returns:
            Newly created Mailbox instance

        Raises:
            ValueError: If agent_id already registered
        """

    def unregister_mailbox(self, agent_id: str) -> bool:
        """
        Remove agent's mailbox.

        Args:
            agent_id: Agent to unregister

        Returns:
            True if unregistered, False if not found
        """

    def get_mailbox(self, agent_id: str) -> Optional[Mailbox]:
        """
        Retrieve agent's mailbox.

        Args:
            agent_id: Agent identifier

        Returns:
            Mailbox if found, None otherwise
        """

    def deliver_message(self, message: Message) -> bool:
        """
        Deliver message to recipient(s) immediately.

        Args:
            message: Message to deliver

        Returns:
            True if delivered to all recipients, False otherwise
        """

    def broadcast(self, message: Message, topic: str) -> int:
        """
        Broadcast message to all agents subscribed to topic.

        Args:
            message: Message to broadcast
            topic: Topic to broadcast on

        Returns:
            Number of agents message was delivered to
        """

    def subscribe(self, agent_id: str, topic: str) -> bool:
        """
        Subscribe agent to topic for broadcasts.

        Args:
            agent_id: Agent to subscribe
            topic: Topic to subscribe to

        Returns:
            True if subscribed successfully
        """

    def unsubscribe(self, agent_id: str, topic: str) -> bool:
        """
        Unsubscribe agent from topic.

        Args:
            agent_id: Agent to unsubscribe
            topic: Topic to unsubscribe from

        Returns:
            True if unsubscribed successfully
        """

    def start(self) -> None:
        """
        Start background message delivery thread.

        The delivery thread continuously checks all agent outboxes
        and delivers messages to recipient inboxes.
        """

    def stop(self) -> None:
        """
        Stop background delivery thread gracefully.

        Waits for current delivery cycle to complete.
        """

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get broker statistics.

        Returns:
            Dict with mailbox count, message counts, etc.
        """

    def _delivery_loop(self) -> None:
        """
        Background thread that delivers messages.

        Continuously processes all mailboxes, delivering messages
        from outboxes to inboxes.
        """

    def _deliver_from_outbox(self, agent_id: str) -> int:
        """
        Deliver all messages from one agent's outbox.

        Returns number of messages delivered.
        """
```

**Key Methods**:

| Method | Responsibility | Returns | LOC |
|--------|---------------|---------|-----|
| `register_mailbox()` | Create mailbox for agent | `Mailbox` | 15 |
| `unregister_mailbox()` | Remove agent mailbox | `bool` | 10 |
| `get_mailbox()` | Retrieve agent's mailbox | `Optional[Mailbox]` | 5 |
| `deliver_message()` | Deliver message immediately | `bool` | 30 |
| `broadcast()` | Send to all topic subscribers | `int` | 25 |
| `subscribe()` | Subscribe agent to topic | `bool` | 10 |
| `unsubscribe()` | Unsubscribe from topic | `bool` | 10 |
| `start()` | Start delivery thread | `None` | 15 |
| `stop()` | Stop delivery thread | `None` | 10 |
| `get_statistics()` | Get broker stats | `Dict[str, Any]` | 20 |
| `_delivery_loop()` | Background delivery thread | `None` | 30 |
| `_deliver_from_outbox()` | Process one agent's outbox | `int` | 25 |

**Dependencies**:
- `core.mail.message.Message`
- `core.mail.mailbox.Mailbox`
- `core.mail.storage.MailStorage`

**Estimated LOC**: 300

---

### Component 4: Storage Backend

**Location**: `/home/user/safety-research-system/core/mail/storage.py`

#### 4.1 MailStorage (Abstract Base Class)

**Purpose**: Define storage interface for message persistence

**Class Signature**:
```python
class MailStorage(ABC):
    """
    Abstract storage interface for mail messages.

    Implementations must provide message persistence,
    retrieval, and querying capabilities.
    """

    @abstractmethod
    def save_message(self, message: Message) -> bool:
        """
        Persist a message to storage.

        Args:
            message: Message to save

        Returns:
            True if saved successfully
        """
        pass

    @abstractmethod
    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Retrieve a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message if found, None otherwise
        """
        pass

    @abstractmethod
    def get_messages(
        self,
        agent_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Retrieve messages for an agent with optional filters.

        Args:
            agent_id: Agent identifier
            filters: Filter criteria (sender_id, message_type, etc.)
            limit: Maximum messages to return

        Returns:
            List of messages matching criteria
        """
        pass

    @abstractmethod
    def get_thread(self, thread_id: str) -> List[Message]:
        """
        Retrieve all messages in a conversation thread.

        Args:
            thread_id: Thread identifier

        Returns:
            List of messages in chronological order
        """
        pass

    @abstractmethod
    def mark_delivered(self, message_id: str) -> bool:
        """
        Mark message as delivered.

        Args:
            message_id: Message identifier

        Returns:
            True if marked successfully
        """
        pass

    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message from storage.

        Args:
            message_id: Message identifier

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict with message counts, storage size, etc.
        """
        pass
```

**Estimated LOC**: 80

---

#### 4.2 InMemoryMailStorage Class

**Purpose**: Simple in-memory storage implementation for Phase 1

**Class Signature**:
```python
class InMemoryMailStorage(MailStorage):
    """
    Simple in-memory message storage.

    Stores all messages in memory using dictionaries.
    Fast and simple, but not persistent across restarts.

    Thread-safe for concurrent access.
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.messages: Dict[str, Message] = {}  # message_id -> Message
        self.agent_messages: Dict[str, List[str]] = {}  # agent_id -> [message_ids]
        self.threads: Dict[str, List[str]] = {}  # thread_id -> [message_ids]
        self.delivered: Set[str] = set()  # Set of delivered message_ids
        self._lock = threading.Lock()
        logger.info("InMemoryMailStorage initialized")

    def save_message(self, message: Message) -> bool:
        """Save message to in-memory storage."""

    def get_message(self, message_id: str) -> Optional[Message]:
        """Retrieve message by ID."""

    def get_messages(
        self,
        agent_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Message]:
        """Retrieve messages for agent with filters."""

    def get_thread(self, thread_id: str) -> List[Message]:
        """Retrieve all messages in thread."""

    def mark_delivered(self, message_id: str) -> bool:
        """Mark message as delivered."""

    def delete_message(self, message_id: str) -> bool:
        """Delete message from storage."""

    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics."""

    def clear(self) -> None:
        """Clear all messages (for testing)."""

    def _matches_filters(
        self,
        message: Message,
        filters: Dict[str, Any]
    ) -> bool:
        """Check if message matches filter criteria."""
```

**Key Methods**:

| Method | Responsibility | Returns | LOC |
|--------|---------------|---------|-----|
| `save_message()` | Store message in memory | `bool` | 20 |
| `get_message()` | Retrieve by ID | `Optional[Message]` | 8 |
| `get_messages()` | Query with filters | `List[Message]` | 35 |
| `get_thread()` | Get thread messages | `List[Message]` | 15 |
| `mark_delivered()` | Mark as delivered | `bool` | 8 |
| `delete_message()` | Delete message | `bool` | 15 |
| `get_statistics()` | Get stats | `Dict[str, Any]` | 15 |
| `clear()` | Clear all (testing) | `None` | 10 |
| `_matches_filters()` | Filter matching | `bool` | 20 |

**Dependencies**:
- `core.mail.message.Message`

**Estimated LOC**: 200

---

### Component 5: Agent Registry

**Location**: `/home/user/safety-research-system/core/registry/agent_registry.py`

#### 5.1 AgentRegistry Class

**Purpose**: Central registry for agent discovery and status tracking

**Class Signature**:
```python
class AgentRegistry:
    """
    Central registry for agent discovery and management.

    Tracks all active agents, their capabilities, status, and load.
    Provides discovery methods to find agents by capabilities.
    Manages heartbeat mechanism to detect offline agents.

    Thread-safe for concurrent access.
    """

    def __init__(self, heartbeat_timeout: int = 60):
        """
        Initialize agent registry.

        Args:
            heartbeat_timeout: Seconds before agent marked as offline
        """
        self.agents: Dict[str, AgentMetadata] = {}  # agent_id -> metadata
        self.capabilities_index: Dict[str, List[str]] = {}  # capability -> [agent_ids]
        self.heartbeat_timeout = heartbeat_timeout
        self._lock = threading.Lock()
        logger.info("AgentRegistry initialized")

    def register(self, metadata: 'AgentMetadata') -> bool:
        """
        Register new agent in registry.

        Args:
            metadata: Agent metadata

        Returns:
            True if registered successfully

        Raises:
            ValueError: If agent_id already registered
        """

    def unregister(self, agent_id: str) -> bool:
        """
        Remove agent from registry.

        Args:
            agent_id: Agent to unregister

        Returns:
            True if unregistered, False if not found
        """

    def update_metadata(
        self,
        agent_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update agent metadata fields.

        Args:
            agent_id: Agent to update
            updates: Fields to update

        Returns:
            True if updated successfully
        """

    def discover(
        self,
        requirements: 'AgentRequirements'
    ) -> List['AgentMetadata']:
        """
        Find agents matching requirements.

        Args:
            requirements: Requirements for agent discovery

        Returns:
            List of matching agent metadata, sorted by relevance
        """

    def get_agent(self, agent_id: str) -> Optional['AgentMetadata']:
        """
        Get metadata for specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentMetadata if found, None otherwise
        """

    def get_all_agents(self) -> List['AgentMetadata']:
        """
        Get metadata for all registered agents.

        Returns:
            List of all agent metadata
        """

    def heartbeat(self, agent_id: str) -> bool:
        """
        Update agent's last heartbeat timestamp.

        Args:
            agent_id: Agent sending heartbeat

        Returns:
            True if updated successfully
        """

    def get_status(self, agent_id: str) -> Optional['AgentStatus']:
        """
        Get agent's current status.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentStatus if found, None otherwise
        """

    def set_status(
        self,
        agent_id: str,
        status: 'AgentStatus'
    ) -> bool:
        """
        Update agent's status.

        Args:
            agent_id: Agent identifier
            status: New status

        Returns:
            True if updated successfully
        """

    def prune_stale_agents(self) -> int:
        """
        Mark agents as offline if no recent heartbeat.

        Returns:
            Number of agents marked offline
        """

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dict with agent counts by status, capabilities, etc.
        """

    def _index_capabilities(self, agent_id: str, capabilities: List[str]) -> None:
        """Add agent to capabilities index."""

    def _remove_from_capabilities_index(self, agent_id: str) -> None:
        """Remove agent from capabilities index."""
```

**Key Methods**:

| Method | Responsibility | Returns | LOC |
|--------|---------------|---------|-----|
| `register()` | Register new agent | `bool` | 25 |
| `unregister()` | Remove agent | `bool` | 15 |
| `update_metadata()` | Update agent metadata | `bool` | 15 |
| `discover()` | Find matching agents | `List[AgentMetadata]` | 40 |
| `get_agent()` | Get specific agent | `Optional[AgentMetadata]` | 5 |
| `get_all_agents()` | Get all agents | `List[AgentMetadata]` | 5 |
| `heartbeat()` | Update heartbeat | `bool` | 10 |
| `get_status()` | Get agent status | `Optional[AgentStatus]` | 8 |
| `set_status()` | Set agent status | `bool` | 10 |
| `prune_stale_agents()` | Mark offline agents | `int` | 25 |
| `get_statistics()` | Get stats | `Dict[str, Any]` | 20 |
| `_index_capabilities()` | Index capabilities | `None` | 10 |
| `_remove_from_capabilities_index()` | Remove from index | `None` | 10 |

**Dependencies**:
- `core.registry.metadata.AgentMetadata`
- `core.registry.metadata.AgentStatus`
- `core.registry.metadata.AgentRequirements`

**Estimated LOC**: 250

---

#### 5.2 AgentMetadata Model

**Location**: `/home/user/safety-research-system/core/registry/metadata.py`

**Purpose**: Data model for agent metadata

**Class Signature**:
```python
@dataclass
class AgentMetadata:
    """
    Metadata about a registered agent.

    Contains information about agent capabilities, status,
    load, and contact information.
    """
    agent_id: str
    agent_type: str  # "worker", "auditor", "planner", "coordinator"
    capabilities: List[str]  # Task types agent can handle
    version: str
    mailbox_address: str  # Agent's mailbox ID (usually same as agent_id)
    status: 'AgentStatus' = AgentStatus.ACTIVE
    current_load: int = 0  # Number of active tasks
    max_concurrent_tasks: int = 5
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMetadata':
        """Deserialize from dictionary."""

    def is_available(self) -> bool:
        """Check if agent is available for work."""

    def has_capacity(self) -> bool:
        """Check if agent has capacity for more tasks."""

    def has_capability(self, capability: str) -> bool:
        """Check if agent has specific capability."""
```

**Estimated LOC**: 80

---

#### 5.3 AgentStatus Enum

**Purpose**: Define agent status states

**Class Signature**:
```python
class AgentStatus(Enum):
    """Status states for agents."""
    ACTIVE = "active"          # Agent running and available
    BUSY = "busy"              # Agent at max capacity
    IDLE = "idle"              # Agent available with no tasks
    OFFLINE = "offline"        # Agent not responding to heartbeat
    MAINTENANCE = "maintenance"  # Agent temporarily unavailable
    ERROR = "error"            # Agent in error state
```

**Estimated LOC**: 12

---

#### 5.4 AgentRequirements Model

**Purpose**: Specify requirements for agent discovery

**Class Signature**:
```python
@dataclass
class AgentRequirements:
    """
    Requirements for agent discovery queries.

    Used to find agents matching specific criteria.
    """
    capabilities: List[str] = field(default_factory=list)  # Required capabilities
    agent_types: List[str] = field(default_factory=list)  # Allowed agent types
    min_capacity: Optional[int] = None  # Minimum concurrent task capacity
    status: Optional['AgentStatus'] = None  # Required status
    preferred_agents: List[str] = field(default_factory=list)  # Prefer these agents
    exclude_agents: List[str] = field(default_factory=list)  # Exclude these agents

    def matches(self, metadata: AgentMetadata) -> bool:
        """Check if agent metadata matches these requirements."""
```

**Estimated LOC**: 50

---

### Component 6: Integration Layer

**Location**: `/home/user/safety-research-system/agents/base_worker.py` (modifications)

#### 6.1 MailEnabledAgent Mixin

**Purpose**: Add mail capabilities to existing agents

**Class Signature**:
```python
class MailEnabledAgent:
    """
    Mixin to add mail capabilities to existing agents.

    Agents that inherit from this mixin get:
    - Mailbox for sending/receiving messages
    - Integration with mail broker
    - Message handling methods
    """

    def __init__(self, agent_id: str, mail_broker: Optional[MailBroker] = None):
        """
        Initialize mail-enabled agent.

        Args:
            agent_id: Unique agent identifier
            mail_broker: Mail broker instance (if using mail system)
        """
        self.agent_id = agent_id
        self.mail_broker = mail_broker
        self.mailbox: Optional[Mailbox] = None

        if mail_broker:
            self.mailbox = mail_broker.register_mailbox(agent_id)
            logger.info(f"Agent {agent_id} registered with mail system")

    def send_message(
        self,
        recipient_ids: List[str],
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Send a message to other agents.

        Args:
            recipient_ids: List of recipient agent IDs
            message_type: Type of message
            subject: Message subject
            body: Message body
            **kwargs: Additional message fields (priority, thread_id, etc.)

        Returns:
            message_id of sent message
        """

    def receive_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        Receive next message from mailbox.

        Args:
            timeout: Seconds to wait (None = block forever)

        Returns:
            Message if available, None if timeout
        """

    def check_inbox(self, **filters) -> List[Message]:
        """
        Check inbox without removing messages.

        Args:
            **filters: Filter criteria

        Returns:
            List of messages matching filters
        """

    def has_mail_enabled(self) -> bool:
        """Check if agent has mail capabilities."""
        return self.mailbox is not None
```

**Estimated LOC**: 80

---

## Implementation Sequence

### Build Order

Components must be built in dependency order:

```
1. Message System (no dependencies)
   ├─ MessageType enum
   ├─ MessagePriority enum
   └─ Message class

2. Storage Backend (depends on Message)
   ├─ MailStorage abstract class
   └─ InMemoryMailStorage implementation

3. Mailbox System (depends on Message, Storage)
   └─ Mailbox class

4. Mail Broker (depends on Message, Mailbox, Storage)
   └─ MailBroker class

5. Agent Registry (no mail dependencies)
   ├─ AgentStatus enum
   ├─ AgentMetadata model
   ├─ AgentRequirements model
   └─ AgentRegistry class

6. Integration Layer (depends on all above)
   └─ MailEnabledAgent mixin
```

### Week-by-Week Plan

#### Week 1: Core Infrastructure

**Days 1-2: Message System**
- [ ] Create `core/mail/` directory
- [ ] Implement `MessageType` enum
- [ ] Implement `MessagePriority` enum
- [ ] Implement `Message` class with all methods
- [ ] Write unit tests for Message
- [ ] **Milestone**: Messages can be created, serialized, validated

**Days 3-4: Storage Backend**
- [ ] Implement `MailStorage` abstract class
- [ ] Implement `InMemoryMailStorage` class
- [ ] Write unit tests for storage
- [ ] **Milestone**: Messages can be stored and retrieved

**Day 5: Mailbox System**
- [ ] Implement `Mailbox` class
- [ ] Write unit tests for Mailbox
- [ ] **Milestone**: Agents can send/receive via mailbox

#### Week 2: Delivery and Registry

**Days 1-3: Mail Broker**
- [ ] Implement `MailBroker` class
- [ ] Implement delivery thread
- [ ] Implement broadcast/subscribe
- [ ] Write unit tests for broker
- [ ] **Milestone**: Messages automatically delivered between mailboxes

**Days 4-5: Agent Registry**
- [ ] Create `core/registry/` directory
- [ ] Implement `AgentStatus` enum
- [ ] Implement `AgentMetadata` model
- [ ] Implement `AgentRequirements` model
- [ ] Implement `AgentRegistry` class
- [ ] Write unit tests for registry
- [ ] **Milestone**: Agents can be registered and discovered

#### Week 3: Integration and Testing

**Days 1-2: Integration Layer**
- [ ] Implement `MailEnabledAgent` mixin
- [ ] Add mail capabilities to `BaseWorker`
- [ ] Add mail capabilities to `BaseAuditor`
- [ ] Write integration tests
- [ ] **Milestone**: Existing agents can use mail system

**Days 3-4: End-to-End Testing**
- [ ] Create comprehensive integration tests
- [ ] Test multi-agent scenarios
- [ ] Test thread safety
- [ ] Performance benchmarking
- [ ] **Milestone**: Full system works end-to-end

**Day 5: Documentation and Polish**
- [ ] Write API documentation
- [ ] Create usage examples
- [ ] Add inline code comments
- [ ] Update main README
- [ ] **Milestone**: Phase 1 complete and documented

---

## Integration Points

### Integration with Existing System

#### 1. BaseWorker Integration

**File**: `/home/user/safety-research-system/agents/base_worker.py`

**Change Type**: Add optional mail support (backward compatible)

**Implementation**:
```python
class BaseWorker(ABC, MailEnabledAgent):
    """Base class for worker agents (now with optional mail support)."""

    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any] = None,
        mail_broker: Optional[MailBroker] = None  # NEW PARAMETER
    ):
        # Initialize MailEnabledAgent if broker provided
        MailEnabledAgent.__init__(self, agent_id, mail_broker)

        # Original initialization
        self.config = config or {}
        self.version = "1.0.0"
        logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id}")
```

**Impact**:
- Backward compatible (mail_broker defaults to None)
- Existing code continues to work
- New code can enable mail by passing broker

---

#### 2. BaseAuditor Integration

**File**: `/home/user/safety-research-system/agents/base_auditor.py`

**Change Type**: Add optional mail support (backward compatible)

**Implementation**: Same pattern as BaseWorker

---

#### 3. Orchestrator Integration

**File**: `/home/user/safety-research-system/agents/orchestrator.py`

**Change Type**: Create new `MailEnabledOrchestrator` subclass

**Implementation**:
```python
class MailEnabledOrchestrator(Orchestrator):
    """
    Orchestrator with mail system integration.

    Can operate in two modes:
    1. Classic mode: Direct function calls (existing behavior)
    2. Mail mode: Message-based communication (new behavior)
    """

    def __init__(
        self,
        task_executor: TaskExecutor,
        audit_engine: AuditEngine,
        resolution_engine: ResolutionEngine,
        mail_broker: Optional[MailBroker] = None,
        agent_registry: Optional[AgentRegistry] = None,
        use_mail_mode: bool = False
    ):
        super().__init__(task_executor, audit_engine, resolution_engine)
        self.mail_broker = mail_broker
        self.agent_registry = agent_registry
        self.use_mail_mode = use_mail_mode

        if use_mail_mode and not mail_broker:
            raise ValueError("Mail mode requires mail_broker")
```

**Impact**:
- Existing Orchestrator unchanged
- New subclass for mail-based operation
- Can switch modes via configuration

---

#### 4. TaskExecutor Integration

**File**: `/home/user/safety-research-system/core/task_executor.py`

**Change Type**: Add optional agent registry for discovery

**Implementation**:
```python
class TaskExecutor:
    def __init__(
        self,
        worker_registry: Optional[Dict[str, Any]] = None,
        enable_intelligent_routing: bool = True,
        agent_registry: Optional[AgentRegistry] = None  # NEW PARAMETER
    ):
        self.worker_registry = worker_registry or {}
        self.agent_registry = agent_registry  # NEW
        # ... rest of initialization
```

**Impact**:
- Can discover workers via registry instead of hard-coded mapping
- Backward compatible (registry is optional)

---

### Data Model Extensions

#### 1. Task Model Extension

**File**: `/home/user/safety-research-system/models/task.py`

**Change Type**: Add optional mail-related fields

**Implementation**:
```python
@dataclass
class Task:
    # ... existing fields ...

    # NEW FIELDS (optional, default to None)
    assignment_message_id: Optional[str] = None  # Message that assigned this task
    result_message_id: Optional[str] = None  # Message containing results
    thread_id: Optional[str] = None  # Conversation thread for this task
```

**Impact**:
- Backward compatible (new fields optional)
- Enables tracking of mail-based task flow
- Can link tasks to message threads

---

### Configuration

#### 1. Mail System Configuration

**File**: `/home/user/safety-research-system/config/mail_config.py` (NEW)

**Purpose**: Centralized mail system configuration

**Implementation**:
```python
@dataclass
class MailConfig:
    """Configuration for mail system."""
    enabled: bool = False
    storage_backend: str = "in_memory"  # "in_memory" | "file" | "redis"
    heartbeat_timeout: int = 60  # seconds
    delivery_interval: float = 0.1  # seconds
    max_inbox_size: int = 1000
    message_ttl: Optional[int] = None  # seconds (None = no expiration)
    enable_statistics: bool = True
```

---

## Testing Strategy

### Unit Tests

Each component gets comprehensive unit tests:

#### 1. Message Tests

**File**: `/home/user/safety-research-system/tests/core/mail/test_message.py`

**Test Coverage**:
```python
class TestMessage:
    def test_create_message(self):
        """Test message creation with required fields."""

    def test_message_serialization(self):
        """Test to_dict() and from_dict()."""

    def test_message_validation(self):
        """Test validate() method."""

    def test_message_expiration(self):
        """Test TTL and is_expired()."""

    def test_message_threading(self):
        """Test thread_id and in_reply_to."""

    def test_message_priority(self):
        """Test priority ordering."""
```

**Estimated Tests**: 15 test methods

---

#### 2. Mailbox Tests

**File**: `/home/user/safety-research-system/tests/core/mail/test_mailbox.py`

**Test Coverage**:
```python
class TestMailbox:
    def test_send_message(self):
        """Test sending message to outbox."""

    def test_receive_message(self):
        """Test receiving message from inbox."""

    def test_receive_with_timeout(self):
        """Test receive timeout behavior."""

    def test_priority_ordering(self):
        """Test messages delivered by priority."""

    def test_check_inbox(self):
        """Test non-destructive inbox peek."""

    def test_message_filters(self):
        """Test filter functionality."""

    def test_get_thread(self):
        """Test thread retrieval."""

    def test_inbox_size_limit(self):
        """Test max inbox size enforcement."""
```

**Estimated Tests**: 20 test methods

---

#### 3. MailBroker Tests

**File**: `/home/user/safety-research-system/tests/core/mail/test_broker.py`

**Test Coverage**:
```python
class TestMailBroker:
    def test_register_mailbox(self):
        """Test mailbox registration."""

    def test_deliver_message(self):
        """Test message delivery."""

    def test_deliver_to_multiple_recipients(self):
        """Test broadcast to multiple recipients."""

    def test_topic_subscription(self):
        """Test pub/sub functionality."""

    def test_delivery_thread(self):
        """Test background delivery thread."""

    def test_thread_safety(self):
        """Test concurrent access."""

    def test_broker_statistics(self):
        """Test statistics collection."""
```

**Estimated Tests**: 18 test methods

---

#### 4. Storage Tests

**File**: `/home/user/safety-research-system/tests/core/mail/test_storage.py`

**Test Coverage**:
```python
class TestInMemoryMailStorage:
    def test_save_message(self):
        """Test message persistence."""

    def test_get_message(self):
        """Test message retrieval."""

    def test_get_messages_with_filters(self):
        """Test filtered queries."""

    def test_get_thread(self):
        """Test thread retrieval."""

    def test_mark_delivered(self):
        """Test delivery marking."""

    def test_delete_message(self):
        """Test message deletion."""

    def test_storage_statistics(self):
        """Test statistics."""

    def test_thread_safety(self):
        """Test concurrent access."""
```

**Estimated Tests**: 15 test methods

---

#### 5. Registry Tests

**File**: `/home/user/safety-research-system/tests/core/registry/test_agent_registry.py`

**Test Coverage**:
```python
class TestAgentRegistry:
    def test_register_agent(self):
        """Test agent registration."""

    def test_unregister_agent(self):
        """Test agent removal."""

    def test_discover_by_capability(self):
        """Test capability-based discovery."""

    def test_discover_by_status(self):
        """Test status-based discovery."""

    def test_heartbeat(self):
        """Test heartbeat mechanism."""

    def test_prune_stale_agents(self):
        """Test offline detection."""

    def test_update_metadata(self):
        """Test metadata updates."""

    def test_registry_statistics(self):
        """Test statistics."""
```

**Estimated Tests**: 16 test methods

---

### Integration Tests

**File**: `/home/user/safety-research-system/tests/integration/test_mail_system_integration.py`

**Test Scenarios**:

```python
class TestMailSystemIntegration:
    def test_end_to_end_message_delivery(self):
        """
        Test complete message flow:
        1. Create broker and register 2 agents
        2. Agent A sends message to Agent B
        3. Verify Agent B receives message
        """

    def test_multi_agent_conversation(self):
        """
        Test multi-turn conversation:
        1. Agent A sends query to Agent B
        2. Agent B responds
        3. Agent A sends follow-up
        4. Verify thread continuity
        """

    def test_broadcast_to_subscribers(self):
        """
        Test pub/sub:
        1. Multiple agents subscribe to topic
        2. One agent broadcasts to topic
        3. Verify all subscribers receive message
        """

    def test_agent_discovery_and_messaging(self):
        """
        Test registry integration:
        1. Register agents with capabilities
        2. Discover agents by capability
        3. Send messages to discovered agents
        """

    def test_mail_enabled_worker(self):
        """
        Test worker with mail capabilities:
        1. Create mail-enabled worker
        2. Worker sends/receives messages
        3. Worker executes tasks
        """

    def test_concurrent_messaging(self):
        """
        Test thread safety:
        1. Create 10 agents
        2. All send messages concurrently
        3. Verify all messages delivered correctly
        """

    def test_message_persistence(self):
        """
        Test storage:
        1. Send messages
        2. Retrieve from storage
        3. Verify correctness
        """
```

**Estimated Tests**: 10-12 integration test scenarios

---

### Performance Tests

**File**: `/home/user/safety-research-system/tests/performance/test_mail_performance.py`

**Benchmarks**:

```python
class TestMailPerformance:
    def test_message_delivery_latency(self):
        """Measure latency from send to receive."""
        # Target: < 100ms for in-memory

    def test_throughput(self):
        """Measure messages per second."""
        # Target: > 1000 msg/s for in-memory

    def test_scalability(self):
        """Test with increasing number of agents."""
        # Test: 10, 50, 100, 500 agents

    def test_memory_usage(self):
        """Measure memory footprint."""
        # Track memory with 1000 messages
```

**Estimated Tests**: 5-6 performance benchmarks

---

## Success Criteria

### Functional Requirements

Phase 1 is successful when:

- [ ] **Message Exchange**: 3+ agents can reliably exchange messages
- [ ] **Message Delivery**: 100% delivery rate (no lost messages)
- [ ] **Priority Ordering**: High priority messages delivered before low priority
- [ ] **Thread Support**: Conversations can be threaded and retrieved
- [ ] **Pub/Sub**: Broadcast to subscribed agents works correctly
- [ ] **Agent Discovery**: Registry can find agents by capabilities
- [ ] **Heartbeat**: Stale agents detected and marked offline
- [ ] **Integration**: Existing agents can opt-in to mail system
- [ ] **Backward Compatibility**: Existing code works without modification

---

### Performance Requirements

- [ ] **Latency**: Message delivery < 100ms (in-memory, same process)
- [ ] **Throughput**: > 1000 messages/second (in-memory)
- [ ] **Scalability**: Support 100+ registered agents
- [ ] **Memory**: < 1MB for 1000 messages in storage
- [ ] **CPU**: Delivery thread < 5% CPU when idle

---

### Quality Requirements

- [ ] **Test Coverage**: > 80% unit test coverage
- [ ] **Thread Safety**: All components thread-safe
- [ ] **Type Safety**: 100% type hints with mypy validation
- [ ] **Documentation**: All public APIs documented
- [ ] **Code Quality**: Passes pylint with score > 8.0
- [ ] **Logging**: Comprehensive logging at INFO level

---

### Acceptance Test Scenario

**Scenario**: Three agents collaborate on a task

```python
def test_acceptance_scenario():
    """
    Acceptance test: 3 agents collaborate via mail.

    Scenario:
    1. Orchestrator sends task request to Worker A
    2. Worker A sends question to Worker B
    3. Worker B responds to Worker A
    4. Worker A sends results to Orchestrator
    5. Orchestrator sends results to Auditor
    6. Auditor approves or requests corrections
    """
    # Setup
    broker = MailBroker(storage=InMemoryMailStorage())
    registry = AgentRegistry()
    broker.start()

    # Create agents
    orchestrator = MailEnabledOrchestrator(
        ..., mail_broker=broker, agent_registry=registry
    )
    worker_a = LiteratureAgent("worker_a", mail_broker=broker)
    worker_b = StatisticsAgent("worker_b", mail_broker=broker)
    auditor = LiteratureAuditor("auditor", mail_broker=broker)

    # Register agents
    registry.register(AgentMetadata(
        agent_id="worker_a",
        agent_type="worker",
        capabilities=["literature_review"],
        ...
    ))
    registry.register(AgentMetadata(
        agent_id="worker_b",
        agent_type="worker",
        capabilities=["statistical_analysis"],
        ...
    ))
    registry.register(AgentMetadata(
        agent_id="auditor",
        agent_type="auditor",
        capabilities=["literature_audit"],
        ...
    ))

    # 1. Orchestrator → Worker A
    orchestrator.send_message(
        recipient_ids=["worker_a"],
        message_type=MessageType.REQUEST,
        subject="Literature review needed",
        body={"query": "Review ADC-ILD papers", "context": {...}}
    )

    # 2. Worker A receives and sends question to Worker B
    msg = worker_a.receive_message(timeout=5.0)
    assert msg is not None
    assert msg.subject == "Literature review needed"

    worker_a.send_message(
        recipient_ids=["worker_b"],
        message_type=MessageType.QUERY,
        subject="Statistical question",
        body={"question": "What test should I use?"},
        thread_id=msg.message_id  # Thread messages together
    )

    # 3. Worker B receives and responds
    query_msg = worker_b.receive_message(timeout=5.0)
    assert query_msg is not None

    worker_b.send_message(
        recipient_ids=["worker_a"],
        message_type=MessageType.RESPONSE,
        subject="Re: Statistical question",
        body={"answer": "Use chi-square test"},
        thread_id=query_msg.thread_id,
        in_reply_to=query_msg.message_id
    )

    # 4. Worker A receives response and sends results
    response_msg = worker_a.receive_message(timeout=5.0)
    assert response_msg is not None
    assert response_msg.body["answer"] == "Use chi-square test"

    worker_a.send_message(
        recipient_ids=["orchestrator"],
        message_type=MessageType.RESPONSE,
        subject="Literature review complete",
        body={"result": {...}, "methodology": "..."},
        thread_id=msg.message_id
    )

    # 5. Orchestrator receives and forwards to Auditor
    result_msg = orchestrator.receive_message(timeout=5.0)
    assert result_msg is not None

    orchestrator.send_message(
        recipient_ids=["auditor"],
        message_type=MessageType.REQUEST,
        subject="Audit needed",
        body={"task_output": result_msg.body},
        thread_id=msg.message_id
    )

    # 6. Auditor receives and approves
    audit_request = auditor.receive_message(timeout=5.0)
    assert audit_request is not None

    auditor.send_message(
        recipient_ids=["orchestrator"],
        message_type=MessageType.RESPONSE,
        subject="Audit complete",
        body={"status": "APPROVED", "score": 0.95},
        thread_id=audit_request.thread_id,
        in_reply_to=audit_request.message_id
    )

    # Verify final result
    final_msg = orchestrator.receive_message(timeout=5.0)
    assert final_msg is not None
    assert final_msg.body["status"] == "APPROVED"

    # Verify thread continuity
    thread = broker.storage.get_thread(msg.message_id)
    assert len(thread) >= 6  # All messages in thread

    # Cleanup
    broker.stop()
```

**This test passing = Phase 1 complete!**

---

## File Structure

Complete directory structure after Phase 1 implementation:

```
/home/user/safety-research-system/
├── agents/
│   ├── __init__.py
│   ├── base_worker.py              # MODIFIED: Add MailEnabledAgent mixin
│   ├── base_auditor.py             # MODIFIED: Add MailEnabledAgent mixin
│   ├── orchestrator.py             # MODIFIED: Add MailEnabledOrchestrator
│   ├── auditors/
│   │   └── ...
│   ├── workers/
│   │   └── ...
│   └── data_sources/
│       └── ...
│
├── core/
│   ├── __init__.py
│   ├── task_executor.py            # MODIFIED: Add agent_registry param
│   ├── audit_engine.py
│   ├── resolution_engine.py
│   ├── context_compressor.py
│   ├── llm_integration.py
│   ├── confidence_validator.py
│   ├── confidence_calibrator.py
│   │
│   ├── mail/                       # NEW DIRECTORY
│   │   ├── __init__.py            # NEW
│   │   ├── message.py             # NEW: Message, MessageType, MessagePriority
│   │   ├── mailbox.py             # NEW: Mailbox
│   │   ├── broker.py              # NEW: MailBroker
│   │   └── storage.py             # NEW: MailStorage, InMemoryMailStorage
│   │
│   └── registry/                   # NEW DIRECTORY
│       ├── __init__.py            # NEW
│       ├── agent_registry.py      # NEW: AgentRegistry
│       └── metadata.py            # NEW: AgentMetadata, AgentStatus, AgentRequirements
│
├── models/
│   ├── __init__.py
│   ├── task.py                     # MODIFIED: Add mail-related fields
│   ├── case.py
│   ├── evidence.py
│   └── audit_result.py
│
├── config/                         # NEW DIRECTORY
│   ├── __init__.py                # NEW
│   └── mail_config.py             # NEW: MailConfig
│
├── tests/
│   ├── core/
│   │   ├── mail/                  # NEW DIRECTORY
│   │   │   ├── __init__.py       # NEW
│   │   │   ├── test_message.py   # NEW
│   │   │   ├── test_mailbox.py   # NEW
│   │   │   ├── test_broker.py    # NEW
│   │   │   └── test_storage.py   # NEW
│   │   │
│   │   └── registry/              # NEW DIRECTORY
│   │       ├── __init__.py       # NEW
│   │       └── test_agent_registry.py  # NEW
│   │
│   ├── integration/               # NEW DIRECTORY
│   │   ├── __init__.py           # NEW
│   │   └── test_mail_system_integration.py  # NEW
│   │
│   └── performance/               # NEW DIRECTORY
│       ├── __init__.py           # NEW
│       └── test_mail_performance.py  # NEW
│
├── examples/                       # NEW DIRECTORY
│   ├── __init__.py                # NEW
│   ├── basic_messaging.py         # NEW: Simple message example
│   ├── multi_agent_collaboration.py  # NEW: 3-agent collaboration
│   └── agent_discovery.py         # NEW: Registry example
│
├── docs/                           # NEW DIRECTORY (optional)
│   ├── mail_system_api.md         # NEW: API documentation
│   └── mail_system_tutorial.md    # NEW: Tutorial
│
├── README.md                       # MODIFIED: Add Phase 1 info
├── requirements.txt                # MODIFIED: Add any new dependencies
└── setup.py
```

**Summary**:
- **New Files**: 22
- **Modified Files**: 5
- **New Directories**: 7
- **Total LOC Added**: ~2000

---

## Dependencies

### Python Standard Library

All Phase 1 components use only standard library:

- `dataclasses` - Data models
- `datetime` - Timestamps
- `enum` - Enums for types/statuses
- `queue` - Queue, PriorityQueue for mailboxes
- `threading` - Thread, Lock for concurrency
- `typing` - Type hints
- `uuid` - Unique identifiers
- `abc` - Abstract base classes
- `logging` - Logging throughout

**No external dependencies required for Phase 1!**

### Optional Dependencies (for testing)

- `pytest` - Test framework (already in requirements.txt)
- `pytest-cov` - Coverage reporting
- `pytest-timeout` - Test timeouts
- `mypy` - Type checking

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Thread safety issues | High | Use locks throughout, extensive concurrent testing |
| Memory leaks | Medium | Implement size limits, add cleanup methods, profile memory |
| Message loss | High | Comprehensive delivery tests, add message acknowledgment later |
| Performance bottlenecks | Medium | Benchmark early, optimize delivery loop, use profiling |
| Integration breakage | High | Backward compatibility, extensive integration tests |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Underestimated complexity | Medium | Build incrementally, test continuously |
| Testing takes longer | Medium | Automate tests, parallelize test execution |
| Integration issues | Medium | Test integration early and often |

---

## Next Steps After Phase 1

Once Phase 1 is complete and successful:

1. **Phase 2: Basic Collaboration**
   - Communication protocols (request-response, pub-sub)
   - Shared workspace for artifacts
   - Task marketplace for allocation

2. **Phase 3: Collaborative Planning**
   - Planning coordinator
   - Plan proposals and synthesis
   - Multi-agent planning sessions

3. **Phase 4: Production Features**
   - Persistent storage (file-based or Redis)
   - Message acknowledgments
   - Fault tolerance
   - Monitoring and debugging

4. **Phase 5: Claude Code Integration**
   - Multi-instance orchestration
   - Process isolation
   - Complex project collaboration

---

## Appendix: Code Templates

### Template: Creating a Mail-Enabled Agent

```python
from agents.base_worker import BaseWorker
from core.mail.broker import MailBroker
from core.mail.message import MessageType

class MyAgent(BaseWorker):
    """Example mail-enabled agent."""

    def __init__(
        self,
        agent_id: str,
        mail_broker: Optional[MailBroker] = None
    ):
        # Initialize base worker with mail support
        super().__init__(agent_id, config={}, mail_broker=mail_broker)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task."""
        # Can use mail system if available
        if self.has_mail_enabled():
            # Send a message to another agent
            self.send_message(
                recipient_ids=["other_agent"],
                message_type=MessageType.QUERY,
                subject="Need help",
                body={"question": "..."}
            )

            # Wait for response
            response = self.receive_message(timeout=30.0)
            if response:
                # Use response in processing
                answer = response.body.get("answer")

        # Regular execution logic
        return {"result": "..."}
```

### Template: Setting Up Mail System

```python
from core.mail.broker import MailBroker
from core.mail.storage import InMemoryMailStorage
from core.registry.agent_registry import AgentRegistry
from core.registry.metadata import AgentMetadata

# Create mail system
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)
broker.start()

# Create agent registry
registry = AgentRegistry(heartbeat_timeout=60)

# Create and register agents
agent_a = MyAgent("agent_a", mail_broker=broker)
agent_b = MyAgent("agent_b", mail_broker=broker)

# Register in registry
registry.register(AgentMetadata(
    agent_id="agent_a",
    agent_type="worker",
    capabilities=["task_type_1"],
    version="1.0.0",
    mailbox_address="agent_a"
))

# Agents can now communicate!
agent_a.send_message(
    recipient_ids=["agent_b"],
    message_type=MessageType.REQUEST,
    subject="Hello",
    body={"message": "Hello from A!"}
)

# Clean shutdown
broker.stop()
```

---

**END OF PHASE 1 IMPLEMENTATION PLAN**

This plan is ready for implementation. Each component is fully specified with class signatures, method responsibilities, dependencies, and integration points. The testing strategy ensures quality, and the success criteria provide clear goals.

**Questions or concerns? Ready to begin implementation!**
