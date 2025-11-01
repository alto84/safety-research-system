"""Message model for agent-to-agent communication."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import uuid


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


class MessagePriority(Enum):
    """Priority levels for message delivery."""
    URGENT = 1    # Deliver immediately
    HIGH = 2      # High priority
    NORMAL = 3    # Normal priority (default)
    LOW = 4       # Low priority

    def __lt__(self, other):
        """Enable priority comparison for queue sorting."""
        if not isinstance(other, MessagePriority):
            return NotImplemented
        return self.value < other.value


@dataclass
class Message:
    """
    Standard message format for agent-to-agent communication.

    Messages are the fundamental unit of communication in the mail system.
    They support threading, priorities, attachments, and TTL.

    Attributes:
        message_id: Unique identifier for the message
        sender_id: ID of the sending agent
        recipient_ids: List of recipient agent IDs
        message_type: Type of message from MessageType enum
        subject: Message subject line
        body: Message body content (structured data)
        thread_id: Optional conversation thread identifier
        in_reply_to: Optional ID of message being replied to
        timestamp: Timestamp of message creation
        priority: Message priority level
        ttl: Time to live in seconds (None = no expiration)
        attachments: Optional attachments (structured data)
        metadata: Additional message metadata
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_ids: List[str] = field(default_factory=list)
    message_type: MessageType = MessageType.NOTIFICATION
    subject: str = ""
    body: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: MessagePriority = MessagePriority.NORMAL
    ttl: Optional[int] = None  # Time to live in seconds
    attachments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize message to dictionary for storage/transmission.

        Returns:
            Dictionary representation of the message
        """
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "recipient_ids": self.recipient_ids,
            "message_type": self.message_type.value,
            "subject": self.subject,
            "body": self.body,
            "thread_id": self.thread_id,
            "in_reply_to": self.in_reply_to,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "ttl": self.ttl,
            "attachments": self.attachments,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Deserialize message from dictionary.

        Args:
            data: Dictionary containing message data

        Returns:
            Message instance
        """
        # Parse enums from string values
        message_type = MessageType(data.get("message_type", "notification"))
        priority = MessagePriority(data.get("priority", 3))

        # Parse datetime from ISO format
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender_id=data.get("sender_id", ""),
            recipient_ids=data.get("recipient_ids", []),
            message_type=message_type,
            subject=data.get("subject", ""),
            body=data.get("body", {}),
            thread_id=data.get("thread_id"),
            in_reply_to=data.get("in_reply_to"),
            timestamp=timestamp,
            priority=priority,
            ttl=data.get("ttl"),
            attachments=data.get("attachments", {}),
            metadata=data.get("metadata", {}),
        )

    def is_expired(self) -> bool:
        """
        Check if message has exceeded its time to live.

        Returns:
            True if message is expired, False otherwise
        """
        if self.ttl is None:
            return False

        age_seconds = (datetime.utcnow() - self.timestamp).total_seconds()
        return age_seconds > self.ttl

    def create_reply(
        self,
        sender_id: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        **kwargs
    ) -> 'Message':
        """
        Create a reply message to this message.

        Args:
            sender_id: ID of the agent sending the reply
            message_type: Type of the reply message
            subject: Subject of the reply
            body: Body content of the reply
            **kwargs: Additional message fields (priority, attachments, etc.)

        Returns:
            New Message instance configured as a reply
        """
        return Message(
            sender_id=sender_id,
            recipient_ids=[self.sender_id],
            message_type=message_type,
            subject=subject,
            body=body,
            thread_id=self.thread_id or self.message_id,
            in_reply_to=self.message_id,
            priority=kwargs.get("priority", self.priority),
            ttl=kwargs.get("ttl"),
            attachments=kwargs.get("attachments", {}),
            metadata=kwargs.get("metadata", {}),
        )

    def validate(self) -> bool:
        """
        Validate message fields.

        Returns:
            True if message is valid, False otherwise
        """
        # Check required fields
        if not self.message_id:
            return False
        if not self.sender_id:
            return False
        if not self.recipient_ids:
            return False
        if not isinstance(self.recipient_ids, list):
            return False
        if not self.subject:
            return False

        # Validate thread consistency
        if self.in_reply_to and not self.thread_id:
            # If replying to a message, must have a thread_id
            return False

        # Validate TTL
        if self.ttl is not None and self.ttl < 0:
            return False

        return True
