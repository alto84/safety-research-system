"""
Persistent Audit Trail

SQLite-based audit trail for all agent communication.
Provides ACID guarantees, fast queries, and human oversight capabilities.
"""

import sqlite3
import json
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, List, Optional, Any
from .transport import AgentMessage, MessageType
import logging

logger = logging.getLogger(__name__)


class AuditTrail:
    """
    SQLite-based audit trail for all agent communication.

    Features:
    - ACID transactions (durability guarantees)
    - Fast indexed queries
    - Full-text search in message content
    - WAL mode (better concurrency)
    - Thread-local connections (thread-safe)
    - Human-readable SQL queries

    Database Schema:
    - messages: All agent messages
    - acknowledgments: Message acknowledgments
    - Indexes on: thread_id, timestamp, agent names

    Example:
        >>> trail = AuditTrail("safety_audit_trail.db")
        >>> trail.log_message(message)
        >>> thread_messages = trail.get_thread("task-123")
        >>> agent_messages = trail.get_agent_messages("Worker1", direction="sent")
    """

    def __init__(self, db_path: str):
        """
        Initialize audit trail.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.local = threading.local()
        self._init_db()

        logger.info(f"AuditTrail initialized: {db_path}")

    @contextmanager
    def get_conn(self):
        """
        Get thread-local database connection.

        Uses thread-local storage to provide each thread with its own connection.
        This is safe for concurrent use.

        Yields:
            sqlite3.Connection
        """
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0  # Wait up to 10s for lock
            )

            # Enable WAL mode for better concurrency
            # WAL allows multiple readers while a writer is active
            self.local.conn.execute("PRAGMA journal_mode=WAL")

            # NORMAL is safe with WAL and faster than FULL
            self.local.conn.execute("PRAGMA synchronous=NORMAL")

            # Dict-like row access (row['column_name'])
            self.local.conn.row_factory = sqlite3.Row

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
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_thread
                ON messages(thread_id, timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recipient
                ON messages(to_agent, timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sender
                ON messages(from_agent, timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON messages(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_type
                ON messages(message_type, timestamp)
            """)

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

            logger.debug("Database schema initialized")

    def log_message(self, message: AgentMessage):
        """
        Persist message to audit trail.

        Thread-safe: Multiple agents can log concurrently.

        Args:
            message: AgentMessage to persist
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

            logger.debug(f"Logged message {message.message_id[:8]} to audit trail")

    def log_acknowledgment(self, message_id: str, ack_by: str):
        """
        Log message acknowledgment.

        Args:
            message_id: Message being acknowledged
            ack_by: Agent acknowledging the message
        """
        with self.get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO acknowledgments (message_id, ack_by, ack_timestamp)
                VALUES (?, ?, ?)
            """, (message_id, ack_by, datetime.utcnow().isoformat()))
            conn.commit()

            logger.debug(f"Logged acknowledgment for {message_id[:8]} by {ack_by}")

    def get_message(self, message_id: str) -> Optional[Dict]:
        """
        Get specific message by ID.

        Args:
            message_id: Message ID to retrieve

        Returns:
            Dictionary with message data or None if not found
        """
        with self.get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM messages WHERE message_id = ?
            """, (message_id,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_thread(self, thread_id: str) -> List[Dict]:
        """
        Get all messages in a thread.

        Returns messages in chronological order.

        Args:
            thread_id: Thread to retrieve

        Returns:
            List of message dictionaries (chronological order)
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
        """
        Get messages sent/received by agent.

        Args:
            agent_name: Agent to query
            direction: "sent", "received", or "both"
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries (newest first)
        """
        with self.get_conn() as conn:
            if direction == "sent":
                query = """
                    SELECT * FROM messages
                    WHERE from_agent = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor = conn.execute(query, (agent_name, limit))

            elif direction == "received":
                query = """
                    SELECT * FROM messages
                    WHERE to_agent = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor = conn.execute(query, (agent_name, limit))

            else:  # both
                query = """
                    SELECT * FROM messages
                    WHERE from_agent = ? OR to_agent = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor = conn.execute(query, (agent_name, agent_name, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_messages_by_type(
        self,
        message_type: MessageType,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get messages of specific type.

        Args:
            message_type: Type of messages to retrieve
            limit: Maximum number to return

        Returns:
            List of message dictionaries (newest first)
        """
        with self.get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM messages
                WHERE message_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (message_type.value, limit))

            return [dict(row) for row in cursor.fetchall()]

    def search_messages(
        self,
        query: str,
        message_type: Optional[str] = None,
        agent: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Full-text search in messages.

        Searches in subject and body fields.

        Args:
            query: Search query (supports wildcards)
            message_type: Filter by message type (optional)
            agent: Filter by agent (sender or recipient, optional)
            limit: Maximum results

        Returns:
            List of matching message dictionaries

        Example:
            >>> # Search for "hepatotoxicity" in literature review tasks
            >>> results = trail.search_messages(
            ...     "hepatotoxicity",
            ...     message_type="task_assignment"
            ... )
        """
        with self.get_conn() as conn:
            sql = """
                SELECT * FROM messages
                WHERE (subject LIKE ? OR body LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]

            if message_type:
                sql += " AND message_type = ?"
                params.append(message_type)

            if agent:
                sql += " AND (from_agent = ? OR to_agent = ?)"
                params.extend([agent, agent])

            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_unacknowledged_messages(
        self,
        agent_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get messages that require acknowledgment but haven't been acknowledged.

        Args:
            agent_name: Filter by recipient (optional)

        Returns:
            List of unacknowledged message dictionaries
        """
        with self.get_conn() as conn:
            sql = """
                SELECT m.* FROM messages m
                LEFT JOIN acknowledgments a ON m.message_id = a.message_id
                WHERE m.requires_ack = 1 AND a.message_id IS NULL
            """
            params = []

            if agent_name:
                sql += " AND m.to_agent = ?"
                params.append(agent_name)

            sql += " ORDER BY m.timestamp DESC"

            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get audit trail statistics.

        Returns:
            Dictionary with stats about messages, agents, threads, etc.
        """
        with self.get_conn() as conn:
            stats = {}

            # Total messages
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            stats["total_messages"] = cursor.fetchone()[0]

            # Messages by type
            cursor = conn.execute("""
                SELECT message_type, COUNT(*) as count
                FROM messages
                GROUP BY message_type
                ORDER BY count DESC
            """)
            stats["messages_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Unique agents
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT agent) FROM (
                    SELECT from_agent as agent FROM messages
                    UNION
                    SELECT to_agent as agent FROM messages
                )
            """)
            stats["unique_agents"] = cursor.fetchone()[0]

            # Unique threads
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT thread_id) FROM messages
                WHERE thread_id IS NOT NULL
            """)
            stats["unique_threads"] = cursor.fetchone()[0]

            # Acknowledgment rate
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total_requiring_ack,
                    SUM(CASE WHEN a.message_id IS NOT NULL THEN 1 ELSE 0 END) as acknowledged
                FROM messages m
                LEFT JOIN acknowledgments a ON m.message_id = a.message_id
                WHERE m.requires_ack = 1
            """)
            row = cursor.fetchone()
            if row[0] > 0:
                stats["acknowledgment_rate"] = f"{row[1] / row[0] * 100:.1f}%"
            else:
                stats["acknowledgment_rate"] = "N/A"

            # Date range
            cursor = conn.execute("""
                SELECT MIN(timestamp), MAX(timestamp) FROM messages
            """)
            min_ts, max_ts = cursor.fetchone()
            stats["date_range"] = {
                "earliest": min_ts,
                "latest": max_ts
            }

            # Database size
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats["db_size_bytes"] = page_count * page_size
            stats["db_size_mb"] = f"{stats['db_size_bytes'] / 1024 / 1024:.2f}"

            return stats

    def vacuum(self):
        """
        Vacuum database to reclaim space.

        Should be run periodically (e.g., nightly) to optimize storage.
        """
        with self.get_conn() as conn:
            conn.execute("VACUUM")
            logger.info("Database vacuumed")

    def analyze(self):
        """
        Update query optimizer statistics.

        Should be run periodically to ensure optimal query performance.
        """
        with self.get_conn() as conn:
            conn.execute("ANALYZE")
            logger.info("Database analyzed")

    def close(self):
        """Close database connection for this thread."""
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
            delattr(self.local, 'conn')
            logger.debug("Database connection closed")
