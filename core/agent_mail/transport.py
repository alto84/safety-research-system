"""
Message Transport Layer

Defines core data structures for agent communication.
All messages in the system use the AgentMessage dataclass.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
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
    ACKNOWLEDGMENT = "acknowledgment"


class MessagePriority(Enum):
    """
    Message priority levels.

    Lower numeric values = higher priority.
    Used for PriorityQueue ordering.
    """
    HIGH = 1
    MEDIUM = 5
    LOW = 10


@dataclass
class AgentMessage:
    """
    Standard message format for agent communication.

    All communication between agents flows through this structure.
    Provides type safety, serialization, and metadata tracking.

    Attributes:
        message_id: Unique identifier (auto-generated UUID)
        message_type: Type of message (task, audit, status, etc.)
        from_agent: Sender agent name
        to_agent: Recipient agent name
        subject: Human-readable subject line
        body: Markdown-formatted message body
        data: Structured data payload (task input, results, etc.)
        thread_id: Groups related messages (e.g., task lifecycle)
        parent_id: Reference to parent message (for replies)
        priority: Message priority (affects queue ordering)
        requires_ack: Whether message requires acknowledgment
        timestamp: ISO 8601 timestamp of message creation
        metadata: Extensible metadata field for custom data

    Example:
        >>> msg = AgentMessage(
        ...     message_type=MessageType.TASK_ASSIGNMENT,
        ...     from_agent="Orchestrator",
        ...     to_agent="LiteratureWorker",
        ...     subject="Review hepatotoxicity literature",
        ...     data={"query": "drug hepatotoxicity", "max_results": 50}
        ... )
        >>> msg.to_json()
    """

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.STATUS_UPDATE
    from_agent: str = ""
    to_agent: str = ""
    subject: str = ""
    body: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    priority: MessagePriority = MessagePriority.MEDIUM
    requires_ack: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """
        Serialize to dictionary.

        Converts enums to their string values for JSON compatibility.

        Returns:
            Dictionary representation of the message
        """
        d = asdict(self)
        d['message_type'] = self.message_type.value
        d['priority'] = self.priority.value
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> 'AgentMessage':
        """
        Deserialize from dictionary.

        Converts string enum values back to Enum instances.

        Args:
            d: Dictionary representation

        Returns:
            AgentMessage instance
        """
        # Create a copy to avoid mutating input
        data = d.copy()

        # Convert string values back to enums
        if isinstance(data.get('message_type'), str):
            data['message_type'] = MessageType(data['message_type'])
        if isinstance(data.get('priority'), str):
            data['priority'] = MessagePriority(data['priority'])
        elif isinstance(data.get('priority'), int):
            # Handle integer priority values
            data['priority'] = MessagePriority(data['priority'])

        return cls(**data)

    def to_json(self) -> str:
        """
        Serialize to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'AgentMessage':
        """
        Deserialize from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            AgentMessage instance
        """
        return cls.from_dict(json.loads(json_str))

    def create_reply(
        self,
        from_agent: str,
        subject: str,
        body: str = "",
        data: Optional[Dict] = None,
        message_type: Optional[MessageType] = None
    ) -> 'AgentMessage':
        """
        Create a reply to this message.

        Automatically sets thread_id, parent_id, and to_agent.

        Args:
            from_agent: Agent sending the reply
            subject: Reply subject
            body: Reply body
            data: Reply data
            message_type: Type of reply (defaults to STATUS_UPDATE)

        Returns:
            New AgentMessage configured as a reply
        """
        return AgentMessage(
            message_type=message_type or MessageType.STATUS_UPDATE,
            from_agent=from_agent,
            to_agent=self.from_agent,  # Reply to sender
            subject=subject,
            body=body,
            data=data or {},
            thread_id=self.thread_id or self.message_id,  # Maintain thread
            parent_id=self.message_id,  # Link to parent
            priority=self.priority  # Inherit priority
        )

    def __repr__(self) -> str:
        """Human-readable representation."""
        return (
            f"AgentMessage("
            f"id={self.message_id[:8]}..., "
            f"type={self.message_type.value}, "
            f"from={self.from_agent}, "
            f"to={self.to_agent}, "
            f"subject='{self.subject}'"
            f")"
        )
