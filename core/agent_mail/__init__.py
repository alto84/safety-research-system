"""
Agent Mail System for Safety Research System

A lightweight, Python stdlib-only messaging system for multi-agent coordination.

Components:
- transport: Core message dataclass and types
- message_queue: In-memory priority queue for fast messaging
- event_bus: Pub/sub event system for broadcasting
- audit_trail: SQLite-based persistent audit trail
- mailbox: High-level API for agents

Key Features:
- No external dependencies (Python 3.11 stdlib only)
- Thread-safe by design
- Hybrid: Fast in-memory + persistent SQLite
- Non-breaking: Opt-in via feature flags
"""

from .transport import AgentMessage, MessageType, MessagePriority

__all__ = [
    "AgentMessage",
    "MessageType",
    "MessagePriority",
]

__version__ = "1.0.0"
