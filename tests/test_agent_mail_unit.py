"""
Unit Tests for Agent Mail Components

Tests individual components in isolation:
- Message transport (serialization)
- Message queue (priority, thread-safety)
- Event bus (pub/sub)
- Audit trail (SQLite operations)
"""

import pytest
import tempfile
import os
import threading
import time
from core.agent_mail.transport import AgentMessage, MessageType, MessagePriority
from core.agent_mail.message_queue import InMemoryMessageQueue
from core.agent_mail.event_bus import EventBus
from core.agent_mail.audit_trail import AuditTrail


class TestAgentMessage:
    """Test AgentMessage dataclass."""

    def test_message_creation(self):
        """Test basic message creation."""
        msg = AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            from_agent="TestAgent",
            to_agent="Worker1",
            subject="Test",
            body="Test body",
            data={"key": "value"}
        )

        assert msg.message_type == MessageType.TASK_ASSIGNMENT
        assert msg.from_agent == "TestAgent"
        assert msg.to_agent == "Worker1"
        assert msg.subject == "Test"
        assert msg.data["key"] == "value"
        assert msg.message_id is not None  # Auto-generated
        assert msg.timestamp is not None  # Auto-generated

    def test_message_serialization_json(self):
        """Test message to/from JSON."""
        msg = AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            from_agent="TestAgent",
            to_agent="Worker1",
            subject="Test",
            data={"key": "value"},
            priority=MessagePriority.HIGH
        )

        # Serialize
        json_str = msg.to_json()
        assert isinstance(json_str, str)
        assert "TestAgent" in json_str

        # Deserialize
        msg2 = AgentMessage.from_json(json_str)

        assert msg.message_id == msg2.message_id
        assert msg.from_agent == msg2.from_agent
        assert msg.data == msg2.data
        assert msg.priority == msg2.priority

    def test_message_serialization_dict(self):
        """Test message to/from dict."""
        msg = AgentMessage(
            message_type=MessageType.TASK_RESULT,
            from_agent="Worker1",
            to_agent="Orchestrator",
            subject="Result",
            data={"result": "success"}
        )

        # Serialize
        msg_dict = msg.to_dict()
        assert isinstance(msg_dict, dict)
        assert msg_dict["message_type"] == "task_result"  # Enum converted to string
        assert msg_dict["from_agent"] == "Worker1"

        # Deserialize
        msg2 = AgentMessage.from_dict(msg_dict)
        assert msg.message_id == msg2.message_id
        assert msg.message_type == msg2.message_type

    def test_message_reply(self):
        """Test creating reply to message."""
        original = AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            from_agent="Orchestrator",
            to_agent="Worker1",
            subject="Do work",
            thread_id="thread-123"
        )

        reply = original.create_reply(
            from_agent="Worker1",
            subject="Work done",
            data={"status": "completed"}
        )

        # Reply should be properly configured
        assert reply.to_agent == "Orchestrator"  # Reply to sender
        assert reply.thread_id == "thread-123"  # Same thread
        assert reply.parent_id == original.message_id  # Link to parent
        assert reply.priority == original.priority  # Inherit priority


class TestInMemoryMessageQueue:
    """Test InMemoryMessageQueue."""

    def test_send_receive(self):
        """Test basic send and receive."""
        queue = InMemoryMessageQueue()

        msg = AgentMessage(
            from_agent="Sender",
            to_agent="Receiver",
            subject="Test"
        )

        # Send
        queue.send(msg)

        # Receive
        received = queue.receive("Receiver", timeout=1.0)

        assert received is not None
        assert received.message_id == msg.message_id
        assert received.from_agent == "Sender"

    def test_priority_ordering(self):
        """Test messages are received in priority order."""
        queue = InMemoryMessageQueue()

        # Send messages with different priorities
        low_msg = AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="Low",
            priority=MessagePriority.LOW
        )
        high_msg = AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="High",
            priority=MessagePriority.HIGH
        )
        medium_msg = AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="Medium",
            priority=MessagePriority.MEDIUM
        )

        # Send in non-priority order
        queue.send(low_msg)
        queue.send(high_msg)
        queue.send(medium_msg)

        # Receive in priority order
        msg1 = queue.receive("B", timeout=1.0)
        msg2 = queue.receive("B", timeout=1.0)
        msg3 = queue.receive("B", timeout=1.0)

        assert msg1.message_id == high_msg.message_id  # Priority 1 first
        assert msg2.message_id == medium_msg.message_id  # Priority 5 second
        assert msg3.message_id == low_msg.message_id  # Priority 10 last

    def test_receive_nowait(self):
        """Test non-blocking receive."""
        queue = InMemoryMessageQueue()

        # No messages
        msg = queue.receive_nowait("Agent1")
        assert msg is None

        # Send message
        queue.send(AgentMessage(from_agent="A", to_agent="Agent1", subject="Test"))

        # Should receive immediately
        msg = queue.receive_nowait("Agent1")
        assert msg is not None
        assert msg.subject == "Test"

    def test_inbox_size(self):
        """Test inbox size tracking."""
        queue = InMemoryMessageQueue()

        assert queue.get_inbox_size("Agent1") == 0

        # Send 3 messages
        for i in range(3):
            queue.send(AgentMessage(from_agent="A", to_agent="Agent1", subject=f"Msg {i}"))

        assert queue.get_inbox_size("Agent1") == 3

        # Receive 1
        queue.receive("Agent1")
        assert queue.get_inbox_size("Agent1") == 2

    def test_message_history(self):
        """Test message history tracking."""
        queue = InMemoryMessageQueue()

        thread_id = "thread-123"

        # Send messages in same thread
        for i in range(3):
            queue.send(AgentMessage(
                from_agent="A",
                to_agent="B",
                subject=f"Msg {i}",
                thread_id=thread_id
            ))

        # Get history
        history = queue.get_message_history(thread_id)
        assert len(history) == 3

    def test_thread_safety(self):
        """Test concurrent sends and receives."""
        queue = InMemoryMessageQueue()
        errors = []

        def sender(agent_id: int):
            """Send 10 messages."""
            try:
                for i in range(10):
                    msg = AgentMessage(
                        from_agent=f"Sender{agent_id}",
                        to_agent="Receiver",
                        subject=f"Msg {i}"
                    )
                    queue.send(msg)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        def receiver():
            """Receive 30 messages."""
            received = []
            try:
                for i in range(30):
                    msg = queue.receive("Receiver", timeout=2.0)
                    if msg:
                        received.append(msg)
                return received
            except Exception as e:
                errors.append(e)
                return received

        # Start 3 senders
        senders = [threading.Thread(target=sender, args=(i,)) for i in range(3)]
        for t in senders:
            t.start()

        # Start receiver
        received_messages = []
        receiver_thread = threading.Thread(
            target=lambda: received_messages.extend(receiver())
        )
        receiver_thread.start()

        # Wait for completion
        for t in senders:
            t.join()
        receiver_thread.join()

        # Verify
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(received_messages) == 30, f"Expected 30, got {len(received_messages)}"


class TestEventBus:
    """Test EventBus pub/sub."""

    def test_subscribe_publish(self):
        """Test basic pub/sub."""
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

    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        bus = EventBus()

        received1 = []
        received2 = []

        bus.subscribe("test.event", lambda d: received1.append(d))
        bus.subscribe("test.event", lambda d: received2.append(d))

        bus.publish("test.event", {"data": "test"})

        assert len(received1) == 1
        assert len(received2) == 1

    def test_wildcard_subscription(self):
        """Test wildcard '*' subscription."""
        bus = EventBus()

        received_all = []

        # Subscribe to all events
        bus.subscribe("*", lambda d: received_all.append(d))

        # Publish different event types
        bus.publish("event.type1", {"type": 1})
        bus.publish("event.type2", {"type": 2})

        # Wildcard should receive both
        assert len(received_all) == 2

    def test_exception_isolation(self):
        """Test that one failing callback doesn't affect others."""
        bus = EventBus()

        received = []

        def failing_callback(data):
            raise ValueError("Intentional error")

        def working_callback(data):
            received.append(data)

        bus.subscribe("test.event", failing_callback)
        bus.subscribe("test.event", working_callback)

        # Publish - should not crash
        bus.publish("test.event", {"data": "test"})

        # Working callback should have received event
        assert len(received) == 1

    def test_unsubscribe(self):
        """Test unsubscribe."""
        bus = EventBus()

        received = []

        def listener(data):
            received.append(data)

        bus.subscribe("test.event", listener)
        bus.publish("test.event", {"count": 1})

        # Unsubscribe
        bus.unsubscribe("test.event", listener)
        bus.publish("test.event", {"count": 2})

        # Should only have received first event
        assert len(received) == 1


class TestAuditTrail:
    """Test SQLite audit trail."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)

    def test_log_message(self, temp_db):
        """Test logging message to database."""
        trail = AuditTrail(temp_db)

        msg = AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            from_agent="Orchestrator",
            to_agent="Worker1",
            subject="Test task"
        )

        # Log
        trail.log_message(msg)

        # Retrieve
        retrieved = trail.get_message(msg.message_id)
        assert retrieved is not None
        assert retrieved["message_id"] == msg.message_id
        assert retrieved["subject"] == "Test task"

    def test_get_thread(self, temp_db):
        """Test retrieving thread messages."""
        trail = AuditTrail(temp_db)

        thread_id = "thread-123"

        # Log 3 messages in same thread
        for i in range(3):
            msg = AgentMessage(
                from_agent="A",
                to_agent="B",
                subject=f"Msg {i}",
                thread_id=thread_id
            )
            trail.log_message(msg)

        # Get thread
        thread_messages = trail.get_thread(thread_id)
        assert len(thread_messages) == 3

        # Should be in chronological order
        assert thread_messages[0]["subject"] == "Msg 0"
        assert thread_messages[2]["subject"] == "Msg 2"

    def test_get_agent_messages(self, temp_db):
        """Test getting messages for specific agent."""
        trail = AuditTrail(temp_db)

        # Log messages
        trail.log_message(AgentMessage(from_agent="Worker1", to_agent="Auditor", subject="Msg1"))
        trail.log_message(AgentMessage(from_agent="Orchestrator", to_agent="Worker1", subject="Msg2"))
        trail.log_message(AgentMessage(from_agent="Worker1", to_agent="Orchestrator", subject="Msg3"))

        # Get sent messages
        sent = trail.get_agent_messages("Worker1", direction="sent")
        assert len(sent) == 2  # Msg1, Msg3

        # Get received messages
        received = trail.get_agent_messages("Worker1", direction="received")
        assert len(received) == 1  # Msg2

        # Get both
        both = trail.get_agent_messages("Worker1", direction="both")
        assert len(both) == 3

    def test_search_messages(self, temp_db):
        """Test full-text search."""
        trail = AuditTrail(temp_db)

        # Log messages
        trail.log_message(AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="Hepatotoxicity research",
            body="Study on liver damage"
        ))
        trail.log_message(AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="Cardiotoxicity research",
            body="Study on heart damage"
        ))

        # Search
        results = trail.search_messages("hepatotoxicity")
        assert len(results) == 1
        assert "Hepatotoxicity" in results[0]["subject"]

        results = trail.search_messages("damage")
        assert len(results) == 2  # Both have "damage" in body

    def test_acknowledgments(self, temp_db):
        """Test logging and querying acknowledgments."""
        trail = AuditTrail(temp_db)

        msg = AgentMessage(
            from_agent="A",
            to_agent="B",
            subject="Test",
            requires_ack=True
        )
        trail.log_message(msg)

        # Before ack
        unacked = trail.get_unacknowledged_messages()
        assert len(unacked) == 1

        # Log acknowledgment
        trail.log_acknowledgment(msg.message_id, "B")

        # After ack
        unacked = trail.get_unacknowledged_messages()
        assert len(unacked) == 0

    def test_thread_safety(self, temp_db):
        """Test concurrent writes to database."""
        trail = AuditTrail(temp_db)
        errors = []

        def writer(agent_id: int):
            """Write 10 messages."""
            try:
                for i in range(10):
                    msg = AgentMessage(
                        from_agent=f"Agent{agent_id}",
                        to_agent="Receiver",
                        subject=f"Msg {i}"
                    )
                    trail.log_message(msg)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        # Start 3 concurrent writers
        threads = [threading.Thread(target=writer, args=(i,)) for i in range(3)]
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify
        assert len(errors) == 0, f"Errors: {errors}"

        # Should have 30 messages total
        stats = trail.get_stats()
        assert stats["total_messages"] == 30

    def test_stats(self, temp_db):
        """Test statistics generation."""
        trail = AuditTrail(temp_db)

        # Log various messages
        trail.log_message(AgentMessage(
            message_type=MessageType.TASK_ASSIGNMENT,
            from_agent="Orchestrator",
            to_agent="Worker1",
            subject="Task 1"
        ))
        trail.log_message(AgentMessage(
            message_type=MessageType.TASK_RESULT,
            from_agent="Worker1",
            to_agent="Orchestrator",
            subject="Result 1"
        ))

        stats = trail.get_stats()

        assert stats["total_messages"] == 2
        assert stats["unique_agents"] == 2
        assert "messages_by_type" in stats
        assert stats["messages_by_type"]["task_assignment"] == 1


def test_import_all():
    """Test that all components can be imported."""
    from core.agent_mail import AgentMessage, MessageType, MessagePriority
    from core.agent_mail.message_queue import InMemoryMessageQueue
    from core.agent_mail.event_bus import EventBus
    from core.agent_mail.audit_trail import AuditTrail
    from core.agent_mail.mailbox import AgentMailbox, MailboxFactory

    assert AgentMessage is not None
    assert MessageType is not None
    assert MessagePriority is not None
    assert InMemoryMessageQueue is not None
    assert EventBus is not None
    assert AuditTrail is not None
    assert AgentMailbox is not None
    assert MailboxFactory is not None
