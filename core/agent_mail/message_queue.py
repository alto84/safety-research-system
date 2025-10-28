"""
In-Memory Message Queue

Thread-safe priority queue for fast agent-to-agent messaging.
Messages are routed to per-agent inboxes with priority ordering.
"""

from queue import PriorityQueue, Empty
from typing import Optional, Dict, List
from .transport import AgentMessage, MessagePriority
import threading
import logging

logger = logging.getLogger(__name__)


class InMemoryMessageQueue:
    """
    Thread-safe priority message queue for fast in-process messaging.

    This is the primary transport for agent communication.
    Messages are routed to recipient-specific queues and ordered by priority.

    Features:
    - Per-agent inbox queues (agent_name -> PriorityQueue)
    - Priority ordering (HIGH, MEDIUM, LOW)
    - Thread-safe operations
    - Message history tracking
    - Blocking and non-blocking receive modes

    Example:
        >>> queue = InMemoryMessageQueue()
        >>> msg = AgentMessage(
        ...     from_agent="Orchestrator",
        ...     to_agent="Worker1",
        ...     priority=MessagePriority.HIGH
        ... )
        >>> queue.send(msg)
        >>> received = queue.receive("Worker1", timeout=1.0)
    """

    def __init__(self):
        # Per-agent inboxes (agent_name -> PriorityQueue)
        self.inboxes: Dict[str, PriorityQueue] = {}
        self.inbox_lock = threading.Lock()

        # Message history (message_id -> message)
        # Useful for debugging and thread reconstruction
        self.message_history: Dict[str, AgentMessage] = {}
        self.history_lock = threading.Lock()

        # Statistics
        self.stats_lock = threading.Lock()
        self.total_sent = 0
        self.total_received = 0

        # Sequence counter for tie-breaking in priority queue
        # When two messages have the same priority, use insertion order
        self._sequence_counter = 0
        self._sequence_lock = threading.Lock()

    def send(self, message: AgentMessage):
        """
        Send message to recipient's inbox.

        Thread-safe: Multiple agents can send concurrently.

        Args:
            message: AgentMessage to send

        Raises:
            ValueError: If message is missing required fields
        """
        if not message.to_agent:
            raise ValueError("Message must have a to_agent")

        recipient = message.to_agent

        # Ensure inbox exists for recipient
        with self.inbox_lock:
            if recipient not in self.inboxes:
                self.inboxes[recipient] = PriorityQueue()

        # Get sequence number for tie-breaking
        with self._sequence_lock:
            sequence = self._sequence_counter
            self._sequence_counter += 1

        # Enqueue with priority + sequence (lower number = higher priority)
        # Format: (priority, sequence, message)
        # Sequence ensures FIFO ordering for messages with same priority
        priority_value = message.priority.value
        self.inboxes[recipient].put((priority_value, sequence, message))

        # Store in history
        with self.history_lock:
            self.message_history[message.message_id] = message

        # Update stats
        with self.stats_lock:
            self.total_sent += 1

        logger.debug(
            f"Message {message.message_id[:8]} sent: "
            f"{message.from_agent} → {message.to_agent} "
            f"({message.message_type.value}, priority={message.priority.value})"
        )

    def receive(self, agent_name: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """
        Receive next message from agent's inbox (blocking).

        Messages are returned in priority order (HIGH before MEDIUM before LOW).

        Args:
            agent_name: Agent receiving message
            timeout: Max time to wait in seconds (None = wait forever)

        Returns:
            AgentMessage or None if timeout

        Example:
            >>> # Block until message arrives
            >>> msg = queue.receive("Worker1")
            >>>
            >>> # Wait up to 5 seconds
            >>> msg = queue.receive("Worker1", timeout=5.0)
            >>> if msg is None:
            ...     print("Timeout - no messages")
        """
        # Ensure inbox exists
        with self.inbox_lock:
            if agent_name not in self.inboxes:
                self.inboxes[agent_name] = PriorityQueue()

        try:
            priority, sequence, message = self.inboxes[agent_name].get(timeout=timeout)

            # Update stats
            with self.stats_lock:
                self.total_received += 1

            logger.debug(
                f"Message {message.message_id[:8]} received by {agent_name}: "
                f"{message.from_agent} → {agent_name} "
                f"({message.message_type.value})"
            )

            return message

        except Empty:
            return None

    def receive_nowait(self, agent_name: str) -> Optional[AgentMessage]:
        """
        Non-blocking receive (returns None immediately if no messages).

        Args:
            agent_name: Agent receiving message

        Returns:
            AgentMessage or None if no messages in inbox
        """
        return self.receive(agent_name, timeout=0.001)

    def peek_inbox(self, agent_name: str) -> List[AgentMessage]:
        """
        Peek at messages in inbox without removing them.

        WARNING: This creates a copy of the queue. Use sparingly.

        Args:
            agent_name: Agent to peek at

        Returns:
            List of messages currently in inbox (in priority order)
        """
        with self.inbox_lock:
            if agent_name not in self.inboxes:
                return []

            # Get all items from queue (this empties it)
            items = []
            try:
                while True:
                    items.append(self.inboxes[agent_name].get_nowait())
            except Empty:
                pass

            # Put them back
            for priority, sequence, message in items:
                self.inboxes[agent_name].put((priority, sequence, message))

            # Return just the messages (sorted by priority, then sequence)
            return [msg for _, _, msg in sorted(items, key=lambda x: (x[0], x[1]))]

    def get_message_history(self, thread_id: str) -> List[AgentMessage]:
        """
        Get all messages in a thread from in-memory history.

        Args:
            thread_id: Thread to retrieve

        Returns:
            List of messages in chronological order
        """
        with self.history_lock:
            messages = [
                msg for msg in self.message_history.values()
                if msg.thread_id == thread_id
            ]

        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages

    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """
        Get specific message from history by ID.

        Args:
            message_id: Message ID to retrieve

        Returns:
            AgentMessage or None if not found
        """
        with self.history_lock:
            return self.message_history.get(message_id)

    def get_inbox_size(self, agent_name: str) -> int:
        """
        Get number of pending messages for agent.

        Args:
            agent_name: Agent to check

        Returns:
            Number of messages in inbox
        """
        with self.inbox_lock:
            if agent_name not in self.inboxes:
                return 0
            return self.inboxes[agent_name].qsize()

    def get_stats(self) -> Dict[str, int]:
        """
        Get queue statistics.

        Returns:
            Dictionary with stats (total_sent, total_received, etc.)
        """
        with self.stats_lock:
            inbox_sizes = {}
            with self.inbox_lock:
                for agent_name, inbox in self.inboxes.items():
                    inbox_sizes[agent_name] = inbox.qsize()

            return {
                "total_sent": self.total_sent,
                "total_received": self.total_received,
                "agents_with_inboxes": len(self.inboxes),
                "inbox_sizes": inbox_sizes,
                "messages_in_history": len(self.message_history)
            }

    def clear_inbox(self, agent_name: str):
        """
        Clear all messages from agent's inbox.

        WARNING: Messages are permanently deleted.

        Args:
            agent_name: Agent whose inbox to clear
        """
        with self.inbox_lock:
            if agent_name in self.inboxes:
                # Empty the queue
                try:
                    while True:
                        self.inboxes[agent_name].get_nowait()
                except Empty:
                    pass

                logger.warning(f"Cleared inbox for {agent_name}")

    def clear_all(self):
        """
        Clear all inboxes and history.

        WARNING: All messages are permanently deleted.
        """
        with self.inbox_lock:
            self.inboxes.clear()

        with self.history_lock:
            self.message_history.clear()

        with self.stats_lock:
            self.total_sent = 0
            self.total_received = 0

        logger.warning("Cleared all queues and history")
