"""
Agent Mailbox (High-Level API)

Simplified API for agent communication that combines:
- In-memory message queue (fast)
- Event bus (pub/sub)
- Audit trail (persistent)
"""

from typing import Optional, Dict, List
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
    Combines in-memory queue (fast) + audit trail (persistent) + event bus (notifications).

    Features:
    - Simple send/receive API
    - Automatic audit trail logging
    - Automatic event publishing
    - Thread history retrieval
    - Acknowledgment support

    Example:
        >>> # Create mailbox for an agent
        >>> mailbox = AgentMailbox(
        ...     agent_name="LiteratureWorker",
        ...     message_queue=queue,
        ...     event_bus=bus,
        ...     audit_trail=trail
        ... )
        >>>
        >>> # Send message
        >>> msg = mailbox.send(
        ...     to_agent="Auditor",
        ...     message_type=MessageType.TASK_RESULT,
        ...     subject="Literature review complete",
        ...     data={"results": [...]}
        ... )
        >>>
        >>> # Receive message (blocking)
        >>> incoming = mailbox.receive(timeout=5.0)
        >>> if incoming:
        ...     mailbox.acknowledge(incoming)
    """

    def __init__(
        self,
        agent_name: str,
        message_queue: InMemoryMessageQueue,
        event_bus: EventBus,
        audit_trail: Optional[AuditTrail] = None
    ):
        """
        Initialize agent mailbox.

        Args:
            agent_name: Name of agent owning this mailbox
            message_queue: In-memory message queue
            event_bus: Event bus for pub/sub
            audit_trail: Optional audit trail for persistence
        """
        self.agent_name = agent_name
        self.message_queue = message_queue
        self.event_bus = event_bus
        self.audit_trail = audit_trail

        logger.debug(f"Mailbox created for {agent_name}")

    def send(
        self,
        to_agent: str,
        message_type: MessageType,
        subject: str,
        body: str = "",
        data: Optional[Dict] = None,
        thread_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.MEDIUM,
        requires_ack: bool = False,
        metadata: Optional[Dict] = None
    ) -> AgentMessage:
        """
        Send message to another agent.

        Automatically:
        - Enqueues to recipient's inbox
        - Logs to audit trail
        - Publishes event to event bus

        Args:
            to_agent: Recipient agent name
            message_type: Type of message
            subject: Human-readable subject
            body: Markdown-formatted body (optional)
            data: Structured data payload (optional)
            thread_id: Thread ID for grouping messages (optional)
            parent_id: Parent message ID for replies (optional)
            priority: Message priority
            requires_ack: Whether acknowledgment is required
            metadata: Additional metadata (optional)

        Returns:
            The sent AgentMessage (for tracking)

        Example:
            >>> msg = mailbox.send(
            ...     to_agent="Orchestrator",
            ...     message_type=MessageType.TASK_RESULT,
            ...     subject="Task completed successfully",
            ...     body="## Results\n\nFound 42 papers...",
            ...     data={"task_id": "task-123", "paper_count": 42},
            ...     thread_id="task-123",
            ...     priority=MessagePriority.HIGH
            ... )
        """
        message = AgentMessage(
            message_type=message_type,
            from_agent=self.agent_name,
            to_agent=to_agent,
            subject=subject,
            body=body,
            data=data or {},
            thread_id=thread_id,
            parent_id=parent_id,
            priority=priority,
            requires_ack=requires_ack,
            metadata=metadata or {}
        )

        # Send to in-memory queue
        self.message_queue.send(message)

        # Persist to audit trail
        if self.audit_trail:
            try:
                self.audit_trail.log_message(message)
            except Exception as e:
                logger.error(f"Failed to log message to audit trail: {e}", exc_info=True)

        # Publish event
        try:
            self.event_bus.publish(f"message.sent", {
                "message_id": message.message_id,
                "message_type": message_type.value,
                "from": self.agent_name,
                "to": to_agent,
                "thread_id": thread_id,
                "priority": priority.value
            })

            # Also publish type-specific event
            self.event_bus.publish(f"message.sent.{message_type.value}", {
                "message_id": message.message_id,
                "from": self.agent_name,
                "to": to_agent,
                "subject": subject
            })
        except Exception as e:
            logger.error(f"Failed to publish event: {e}", exc_info=True)

        logger.info(
            f"[{self.agent_name}] Sent {message_type.value} to {to_agent}: "
            f"{subject} (priority={priority.value})"
        )

        return message

    def receive(self, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive next message (blocking).

        Messages are returned in priority order (HIGH before MEDIUM before LOW).

        Args:
            timeout: Max time to wait in seconds (None = wait forever)

        Returns:
            AgentMessage or None if timeout

        Example:
            >>> # Block until message arrives
            >>> msg = mailbox.receive()
            >>>
            >>> # Wait up to 5 seconds
            >>> msg = mailbox.receive(timeout=5.0)
            >>> if msg is None:
            ...     print("No messages received")
        """
        message = self.message_queue.receive(self.agent_name, timeout=timeout)

        if message:
            # Publish event
            try:
                self.event_bus.publish(f"message.received", {
                    "message_id": message.message_id,
                    "message_type": message.message_type.value,
                    "from": message.from_agent,
                    "to": self.agent_name,
                    "thread_id": message.thread_id
                })

                # Also publish type-specific event
                self.event_bus.publish(f"message.received.{message.message_type.value}", {
                    "message_id": message.message_id,
                    "from": message.from_agent,
                    "to": self.agent_name,
                    "subject": message.subject
                })
            except Exception as e:
                logger.error(f"Failed to publish event: {e}", exc_info=True)

            logger.info(
                f"[{self.agent_name}] Received {message.message_type.value} from {message.from_agent}: "
                f"{message.subject}"
            )

        return message

    def receive_nowait(self) -> Optional[AgentMessage]:
        """
        Non-blocking receive (returns None immediately if no messages).

        Returns:
            AgentMessage or None if no messages in inbox
        """
        return self.receive(timeout=0.001)

    def reply(
        self,
        original_message: AgentMessage,
        subject: str,
        body: str = "",
        data: Optional[Dict] = None,
        message_type: Optional[MessageType] = None,
        priority: Optional[MessagePriority] = None
    ) -> AgentMessage:
        """
        Reply to a message.

        Automatically sets thread_id, parent_id, and to_agent.

        Args:
            original_message: Message being replied to
            subject: Reply subject
            body: Reply body
            data: Reply data
            message_type: Type of reply (defaults to STATUS_UPDATE)
            priority: Reply priority (defaults to original priority)

        Returns:
            The sent reply message

        Example:
            >>> # Receive request
            >>> request = mailbox.receive()
            >>>
            >>> # Send reply
            >>> reply = mailbox.reply(
            ...     request,
            ...     subject="Request processed",
            ...     data={"status": "completed"}
            ... )
        """
        return self.send(
            to_agent=original_message.from_agent,  # Reply to sender
            message_type=message_type or MessageType.STATUS_UPDATE,
            subject=subject,
            body=body,
            data=data,
            thread_id=original_message.thread_id or original_message.message_id,
            parent_id=original_message.message_id,
            priority=priority or original_message.priority
        )

    def acknowledge(self, message: AgentMessage):
        """
        Acknowledge receipt/processing of message.

        Logs acknowledgment to audit trail and publishes event.

        Args:
            message: Message to acknowledge

        Example:
            >>> msg = mailbox.receive()
            >>> # Process message...
            >>> mailbox.acknowledge(msg)
        """
        if self.audit_trail:
            try:
                self.audit_trail.log_acknowledgment(message.message_id, self.agent_name)
            except Exception as e:
                logger.error(f"Failed to log acknowledgment: {e}", exc_info=True)

        # Publish event
        try:
            self.event_bus.publish("message.acknowledged", {
                "message_id": message.message_id,
                "ack_by": self.agent_name,
                "original_from": message.from_agent,
                "original_to": message.to_agent
            })
        except Exception as e:
            logger.error(f"Failed to publish acknowledgment event: {e}", exc_info=True)

        logger.debug(f"[{self.agent_name}] Acknowledged message {message.message_id[:8]}")

    def get_inbox_size(self) -> int:
        """
        Get number of pending messages.

        Returns:
            Number of messages waiting in inbox
        """
        return self.message_queue.get_inbox_size(self.agent_name)

    def has_messages(self) -> bool:
        """
        Check if mailbox has pending messages.

        Returns:
            True if messages are waiting
        """
        return self.get_inbox_size() > 0

    def get_thread_history(self, thread_id: str) -> List[AgentMessage]:
        """
        Get all messages in thread.

        Tries audit trail first (persistent), falls back to in-memory.

        Args:
            thread_id: Thread to retrieve

        Returns:
            List of messages in chronological order

        Example:
            >>> # Get conversation history
            >>> history = mailbox.get_thread_history("task-123")
            >>> for msg in history:
            ...     print(f"{msg.from_agent} → {msg.to_agent}: {msg.subject}")
        """
        if self.audit_trail:
            try:
                messages_dict = self.audit_trail.get_thread(thread_id)
                return [AgentMessage.from_dict(m) for m in messages_dict]
            except Exception as e:
                logger.error(f"Failed to retrieve thread from audit trail: {e}", exc_info=True)

        # Fallback to in-memory
        return self.message_queue.get_message_history(thread_id)

    def get_my_messages(
        self,
        direction: str = "both",
        limit: int = 100
    ) -> List[AgentMessage]:
        """
        Get messages sent/received by this agent.

        Args:
            direction: "sent", "received", or "both"
            limit: Maximum number to return

        Returns:
            List of messages (newest first)
        """
        if self.audit_trail:
            try:
                messages_dict = self.audit_trail.get_agent_messages(
                    self.agent_name,
                    direction,
                    limit
                )
                return [AgentMessage.from_dict(m) for m in messages_dict]
            except Exception as e:
                logger.error(f"Failed to retrieve agent messages: {e}", exc_info=True)

        return []

    def search_messages(
        self,
        query: str,
        message_type: Optional[MessageType] = None
    ) -> List[AgentMessage]:
        """
        Search messages involving this agent.

        Args:
            query: Search query (searches subject and body)
            message_type: Optional message type filter

        Returns:
            List of matching messages

        Example:
            >>> # Find all messages about hepatotoxicity
            >>> results = mailbox.search_messages("hepatotoxicity")
        """
        if self.audit_trail:
            try:
                messages_dict = self.audit_trail.search_messages(
                    query,
                    message_type=message_type.value if message_type else None,
                    agent=self.agent_name
                )
                return [AgentMessage.from_dict(m) for m in messages_dict]
            except Exception as e:
                logger.error(f"Failed to search messages: {e}", exc_info=True)

        return []

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"AgentMailbox("
            f"agent={self.agent_name}, "
            f"pending={self.get_inbox_size()}, "
            f"audit_trail={'enabled' if self.audit_trail else 'disabled'}"
            f")"
        )


class MailboxFactory:
    """
    Factory for creating agent mailboxes.

    Centralizes message queue, event bus, and audit trail management.

    Example:
        >>> factory = MailboxFactory(
        ...     message_queue=InMemoryMessageQueue(),
        ...     event_bus=EventBus(),
        ...     audit_trail=AuditTrail("trail.db")
        ... )
        >>>
        >>> # Create mailboxes for agents
        >>> worker_mailbox = factory.create_mailbox("Worker1")
        >>> auditor_mailbox = factory.create_mailbox("Auditor1")
    """

    def __init__(
        self,
        message_queue: Optional[InMemoryMessageQueue] = None,
        event_bus: Optional[EventBus] = None,
        audit_trail: Optional[AuditTrail] = None
    ):
        """
        Initialize mailbox factory.

        Args:
            message_queue: Shared message queue (creates new if None)
            event_bus: Shared event bus (creates new if None)
            audit_trail: Shared audit trail (optional)
        """
        self.message_queue = message_queue or InMemoryMessageQueue()
        self.event_bus = event_bus or EventBus()
        self.audit_trail = audit_trail

        self.mailboxes: Dict[str, AgentMailbox] = {}

        logger.info("MailboxFactory initialized")

    def create_mailbox(self, agent_name: str) -> AgentMailbox:
        """
        Create mailbox for agent.

        Reuses existing mailbox if already created.

        Args:
            agent_name: Name of agent

        Returns:
            AgentMailbox instance
        """
        if agent_name in self.mailboxes:
            return self.mailboxes[agent_name]

        mailbox = AgentMailbox(
            agent_name=agent_name,
            message_queue=self.message_queue,
            event_bus=self.event_bus,
            audit_trail=self.audit_trail
        )

        self.mailboxes[agent_name] = mailbox

        logger.info(f"Created mailbox for {agent_name}")

        return mailbox

    def get_mailbox(self, agent_name: str) -> Optional[AgentMailbox]:
        """
        Get existing mailbox for agent.

        Args:
            agent_name: Name of agent

        Returns:
            AgentMailbox or None if not created yet
        """
        return self.mailboxes.get(agent_name)

    def get_all_agents(self) -> List[str]:
        """
        Get list of all agents with mailboxes.

        Returns:
            List of agent names
        """
        return list(self.mailboxes.keys())

    def get_stats(self) -> Dict:
        """
        Get statistics across all mailboxes.

        Returns:
            Dictionary with stats
        """
        return {
            "total_mailboxes": len(self.mailboxes),
            "agents": list(self.mailboxes.keys()),
            "message_queue_stats": self.message_queue.get_stats(),
            "event_bus_stats": self.event_bus.get_stats(),
            "audit_trail_stats": self.audit_trail.get_stats() if self.audit_trail else None
        }
