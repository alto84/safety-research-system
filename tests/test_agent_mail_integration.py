"""
Integration Tests for Agent Mail System

Tests complete workflows:
- End-to-end message flows
- Mailbox interactions
- Event bus integration
- Audit trail integration
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
from core.agent_mail.mailbox import AgentMailbox, MailboxFactory


@pytest.fixture
def agent_mail_system():
    """Setup complete agent mail system."""
    queue = InMemoryMessageQueue()
    event_bus = EventBus()

    # Use temporary SQLite database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    audit_trail = AuditTrail(db_path)

    # Create mailboxes for agents
    orchestrator_mailbox = AgentMailbox("Orchestrator", queue, event_bus, audit_trail)
    worker_mailbox = AgentMailbox("Worker1", queue, event_bus, audit_trail)
    auditor_mailbox = AgentMailbox("Auditor1", queue, event_bus, audit_trail)

    yield {
        "queue": queue,
        "event_bus": event_bus,
        "audit_trail": audit_trail,
        "orchestrator": orchestrator_mailbox,
        "worker": worker_mailbox,
        "auditor": auditor_mailbox,
        "db_path": db_path
    }

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestEndToEndMessageFlow:
    """Test complete message flows."""

    def test_task_assignment_execution_audit_flow(self, agent_mail_system):
        """
        Test complete task flow:
        1. Orchestrator assigns task to Worker
        2. Worker executes and sends result to Auditor
        3. Auditor validates and sends audit result to Orchestrator
        4. Orchestrator receives final result
        """
        orchestrator = agent_mail_system["orchestrator"]
        worker = agent_mail_system["worker"]
        auditor = agent_mail_system["auditor"]

        # Step 1: Orchestrator sends task to worker
        task_msg = orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject="Execute literature review",
            data={"task_id": "task-123", "query": "hepatotoxicity"},
            thread_id="task-123",
            priority=MessagePriority.HIGH
        )

        # Step 2: Worker receives task
        received_task = worker.receive(timeout=1.0)
        assert received_task is not None
        assert received_task.message_type == MessageType.TASK_ASSIGNMENT
        assert received_task.data["task_id"] == "task-123"
        assert received_task.thread_id == "task-123"

        # Worker sends result to auditor
        result_msg = worker.send(
            to_agent="Auditor1",
            message_type=MessageType.TASK_RESULT,
            subject="Literature review completed",
            data={
                "task_id": "task-123",
                "result": {"papers_found": 42, "summary": "..."}
            },
            thread_id="task-123"
        )

        # Step 3: Auditor receives result
        received_result = auditor.receive(timeout=1.0)
        assert received_result is not None
        assert received_result.message_type == MessageType.TASK_RESULT
        assert received_result.data["result"]["papers_found"] == 42

        # Auditor validates and sends audit result to orchestrator
        audit_msg = auditor.send(
            to_agent="Orchestrator",
            message_type=MessageType.AUDIT_RESULT,
            subject="Audit: PASSED",
            data={
                "task_id": "task-123",
                "status": "passed",
                "issues": []
            },
            thread_id="task-123"
        )

        # Step 4: Orchestrator receives audit result
        final_result = orchestrator.receive(timeout=1.0)
        assert final_result is not None
        assert final_result.message_type == MessageType.AUDIT_RESULT
        assert final_result.data["status"] == "passed"
        assert final_result.thread_id == "task-123"

    def test_retry_workflow(self, agent_mail_system):
        """
        Test retry workflow:
        1. Worker submits result
        2. Auditor finds issues
        3. Auditor sends retry request
        4. Worker receives corrections and retries
        """
        worker = agent_mail_system["worker"]
        auditor = agent_mail_system["auditor"]

        # Worker submits initial result
        worker.send(
            to_agent="Auditor1",
            message_type=MessageType.TASK_RESULT,
            subject="Initial attempt",
            data={"task_id": "task-456", "result": {"quality": "low"}},
            thread_id="task-456"
        )

        # Auditor receives and finds issues
        result_msg = auditor.receive()
        assert result_msg is not None

        # Auditor sends retry request
        auditor.send(
            to_agent="Worker1",
            message_type=MessageType.RETRY_REQUEST,
            subject="Retry requested",
            body="Result quality insufficient",
            data={
                "task_id": "task-456",
                "corrections": ["Improve analysis", "Add more sources"],
                "previous_output": {"quality": "low"}
            },
            thread_id="task-456"
        )

        # Worker receives retry request
        retry_msg = worker.receive()
        assert retry_msg is not None
        assert retry_msg.message_type == MessageType.RETRY_REQUEST
        assert len(retry_msg.data["corrections"]) == 2

    def test_escalation_workflow(self, agent_mail_system):
        """Test escalation to human review."""
        auditor = agent_mail_system["auditor"]

        # Auditor escalates critical issue
        auditor.send(
            to_agent="HumanReviewer",
            message_type=MessageType.ESCALATION,
            subject="CRITICAL: Task requires human review",
            body="## Critical Issues Found\n\n- Safety concern\n- Conflicting evidence",
            data={
                "task_id": "task-789",
                "reason": "critical_issues",
                "priority": "urgent"
            },
            requires_ack=True,
            priority=MessagePriority.HIGH
        )

        # Verify escalation was sent
        sent = agent_mail_system["queue"].get_inbox_size("HumanReviewer")
        assert sent == 1


class TestMailboxFeatures:
    """Test mailbox-specific features."""

    def test_reply_functionality(self, agent_mail_system):
        """Test reply creates properly linked messages."""
        sender = agent_mail_system["orchestrator"]
        receiver = agent_mail_system["worker"]

        # Send original message
        original = sender.send(
            to_agent="Worker1",
            message_type=MessageType.STATUS_UPDATE,
            subject="Status inquiry",
            data={"question": "Are you ready?"},
            thread_id="status-check"
        )

        # Receiver gets message
        received = receiver.receive()

        # Receiver replies
        reply = receiver.reply(
            received,
            subject="Re: Status inquiry",
            body="Yes, ready to proceed",
            data={"answer": "ready"}
        )

        # Verify reply structure
        assert reply.to_agent == "Orchestrator"  # Reply to sender
        assert reply.thread_id == "status-check"  # Same thread
        assert reply.parent_id == original.message_id  # Linked to original

        # Sender receives reply
        reply_received = sender.receive()
        assert reply_received.parent_id == original.message_id

    def test_acknowledge_functionality(self, agent_mail_system):
        """Test message acknowledgment."""
        sender = agent_mail_system["orchestrator"]
        receiver = agent_mail_system["worker"]
        audit_trail = agent_mail_system["audit_trail"]

        # Send message requiring acknowledgment
        msg = sender.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject="Urgent task",
            requires_ack=True
        )

        # Before acknowledgment
        unacked = audit_trail.get_unacknowledged_messages("Worker1")
        assert len(unacked) == 1

        # Receiver acknowledges
        received = receiver.receive()
        receiver.acknowledge(received)

        # After acknowledgment
        unacked = audit_trail.get_unacknowledged_messages("Worker1")
        assert len(unacked) == 0

    def test_thread_history_retrieval(self, agent_mail_system):
        """Test retrieving complete thread history."""
        orchestrator = agent_mail_system["orchestrator"]
        worker = agent_mail_system["worker"]

        thread_id = "conversation-123"

        # Exchange several messages in same thread
        orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.STATUS_UPDATE,
            subject="Msg 1",
            thread_id=thread_id
        )

        worker.receive()
        worker.send(
            to_agent="Orchestrator",
            message_type=MessageType.STATUS_UPDATE,
            subject="Msg 2",
            thread_id=thread_id
        )

        orchestrator.receive()
        orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.STATUS_UPDATE,
            subject="Msg 3",
            thread_id=thread_id
        )

        # Get thread history
        history = orchestrator.get_thread_history(thread_id)
        assert len(history) == 3

        # Should be in chronological order
        assert history[0].subject == "Msg 1"
        assert history[1].subject == "Msg 2"
        assert history[2].subject == "Msg 3"

    def test_search_functionality(self, agent_mail_system):
        """Test message search."""
        orchestrator = agent_mail_system["orchestrator"]

        # Send messages with searchable content
        orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject="Hepatotoxicity literature review",
            body="Focus on drug-induced liver injury"
        )

        orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject="Cardiotoxicity study",
            body="Analyze cardiac safety"
        )

        # Search
        results = orchestrator.search_messages("hepatotoxicity")
        assert len(results) == 1
        assert "Hepatotoxicity" in results[0].subject


class TestEventBusIntegration:
    """Test event bus integration."""

    def test_events_published_on_send(self, agent_mail_system):
        """Test that sending messages publishes events."""
        sender = agent_mail_system["orchestrator"]
        event_bus = agent_mail_system["event_bus"]

        events_received = []

        # Subscribe to message.sent events
        event_bus.subscribe("message.sent", lambda d: events_received.append(d))

        # Send message
        sender.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject="Test"
        )

        # Verify event was published
        assert len(events_received) == 1
        event = events_received[0]
        assert event["from"] == "Orchestrator"
        assert event["to"] == "Worker1"
        assert event["message_type"] == "task_assignment"

    def test_events_published_on_receive(self, agent_mail_system):
        """Test that receiving messages publishes events."""
        sender = agent_mail_system["orchestrator"]
        receiver = agent_mail_system["worker"]
        event_bus = agent_mail_system["event_bus"]

        events_received = []

        # Subscribe to message.received events
        event_bus.subscribe("message.received", lambda d: events_received.append(d))

        # Send and receive
        sender.send(to_agent="Worker1", message_type=MessageType.STATUS_UPDATE, subject="Test")
        receiver.receive()

        # Verify event was published
        assert len(events_received) == 1
        event = events_received[0]
        assert event["to"] == "Worker1"

    def test_multiple_event_listeners(self, agent_mail_system):
        """Test multiple listeners receive events."""
        sender = agent_mail_system["orchestrator"]
        event_bus = agent_mail_system["event_bus"]

        listener1_events = []
        listener2_events = []

        event_bus.subscribe("message.sent", lambda d: listener1_events.append(d))
        event_bus.subscribe("message.sent", lambda d: listener2_events.append(d))

        sender.send(to_agent="Worker1", message_type=MessageType.STATUS_UPDATE, subject="Test")

        assert len(listener1_events) == 1
        assert len(listener2_events) == 1


class TestMailboxFactory:
    """Test MailboxFactory."""

    def test_factory_creates_mailboxes(self):
        """Test factory creates and manages mailboxes."""
        factory = MailboxFactory()

        # Create mailboxes
        mailbox1 = factory.create_mailbox("Agent1")
        mailbox2 = factory.create_mailbox("Agent2")

        assert mailbox1.agent_name == "Agent1"
        assert mailbox2.agent_name == "Agent2"

        # Get existing mailbox
        same_mailbox = factory.create_mailbox("Agent1")
        assert same_mailbox is mailbox1  # Should reuse

        # Get all agents
        agents = factory.get_all_agents()
        assert "Agent1" in agents
        assert "Agent2" in agents

    def test_factory_shared_infrastructure(self):
        """Test that factory shares infrastructure between mailboxes."""
        factory = MailboxFactory()

        mailbox1 = factory.create_mailbox("Agent1")
        mailbox2 = factory.create_mailbox("Agent2")

        # Should share same queue
        assert mailbox1.message_queue is mailbox2.message_queue

        # Should share same event bus
        assert mailbox1.event_bus is mailbox2.event_bus

        # Messages should route correctly
        mailbox1.send(
            to_agent="Agent2",
            message_type=MessageType.STATUS_UPDATE,
            subject="Test"
        )

        msg = mailbox2.receive(timeout=1.0)
        assert msg is not None
        assert msg.from_agent == "Agent1"


class TestConcurrentOperations:
    """Test concurrent multi-agent operations."""

    def test_concurrent_message_exchange(self, agent_mail_system):
        """Test multiple agents sending/receiving concurrently."""
        factory = MailboxFactory(
            message_queue=agent_mail_system["queue"],
            event_bus=agent_mail_system["event_bus"],
            audit_trail=agent_mail_system["audit_trail"]
        )

        # Create multiple agent mailboxes
        agents = [factory.create_mailbox(f"Agent{i}") for i in range(5)]

        errors = []
        messages_sent = []

        def agent_activity(agent: AgentMailbox):
            """Each agent sends and receives messages."""
            try:
                # Send messages to other agents
                for other in agents:
                    if other.agent_name != agent.agent_name:
                        msg = agent.send(
                            to_agent=other.agent_name,
                            message_type=MessageType.STATUS_UPDATE,
                            subject=f"Hello from {agent.agent_name}",
                            data={"sender": agent.agent_name}
                        )
                        messages_sent.append(msg.message_id)

                time.sleep(0.1)

                # Receive messages (should get 4 messages from other agents)
                for _ in range(4):
                    msg = agent.receive(timeout=2.0)
                    if msg:
                        agent.acknowledge(msg)

            except Exception as e:
                errors.append(e)

        # Run agents concurrently
        threads = [threading.Thread(target=agent_activity, args=(agent,)) for agent in agents]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(messages_sent) == 20  # 5 agents * 4 messages each

    def test_high_throughput(self, agent_mail_system):
        """Test system under high message load."""
        factory = MailboxFactory(
            message_queue=agent_mail_system["queue"],
            event_bus=agent_mail_system["event_bus"],
            audit_trail=agent_mail_system["audit_trail"]
        )

        sender = factory.create_mailbox("Sender")
        receiver = factory.create_mailbox("Receiver")

        errors = []
        sent_count = [0]
        received_count = [0]

        def send_messages():
            """Send 100 messages."""
            try:
                for i in range(100):
                    sender.send(
                        to_agent="Receiver",
                        message_type=MessageType.STATUS_UPDATE,
                        subject=f"Msg {i}",
                        data={"index": i}
                    )
                    sent_count[0] += 1
            except Exception as e:
                errors.append(e)

        def receive_messages():
            """Receive 100 messages."""
            try:
                for i in range(100):
                    msg = receiver.receive(timeout=5.0)
                    if msg:
                        received_count[0] += 1
            except Exception as e:
                errors.append(e)

        # Run concurrently
        sender_thread = threading.Thread(target=send_messages)
        receiver_thread = threading.Thread(target=receive_messages)

        start_time = time.time()
        sender_thread.start()
        receiver_thread.start()

        sender_thread.join()
        receiver_thread.join()
        elapsed = time.time() - start_time

        # Verify
        assert len(errors) == 0, f"Errors: {errors}"
        assert sent_count[0] == 100
        assert received_count[0] == 100

        print(f"\nHigh throughput test: 100 messages in {elapsed:.2f}s "
              f"({100/elapsed:.1f} msg/sec)")


def test_complete_system_stats(agent_mail_system):
    """Test system-wide statistics."""
    factory = MailboxFactory(
        message_queue=agent_mail_system["queue"],
        event_bus=agent_mail_system["event_bus"],
        audit_trail=agent_mail_system["audit_trail"]
    )

    agent1 = factory.create_mailbox("Agent1")
    agent2 = factory.create_mailbox("Agent2")

    # Exchange some messages
    agent1.send(to_agent="Agent2", message_type=MessageType.STATUS_UPDATE, subject="Test 1")
    agent1.send(to_agent="Agent2", message_type=MessageType.TASK_ASSIGNMENT, subject="Test 2")
    agent2.receive()
    agent2.receive()

    # Get stats
    stats = factory.get_stats()

    assert stats["total_mailboxes"] == 2
    assert "Agent1" in stats["agents"]
    assert "Agent2" in stats["agents"]
    assert stats["message_queue_stats"]["total_sent"] == 2
    assert stats["message_queue_stats"]["total_received"] == 2
    assert stats["audit_trail_stats"]["total_messages"] == 2
