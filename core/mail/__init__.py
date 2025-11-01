"""
Mail system for agent-to-agent communication.

This package provides the core message-passing infrastructure for multi-agent
collaboration in the safety research system.
"""

from core.mail.message import Message, MessageType, MessagePriority

__all__ = [
    "Message",
    "MessageType",
    "MessagePriority",
]
