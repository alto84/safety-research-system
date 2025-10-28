#!/usr/bin/env python3
"""
Example: Agent Mail System

Demonstrates the complete agent mail system for multi-agent coordination.

This example shows:
1. Setting up the agent mail infrastructure
2. Creating mailboxes for agents
3. Sending and receiving messages
4. Message threading and conversations
5. Event bus subscriptions
6. Audit trail queries
7. Priority-based message handling

Run: python example_agent_mail.py
"""

import time
import threading
from core.agent_mail.transport import AgentMessage, MessageType, MessagePriority
from core.agent_mail.message_queue import InMemoryMessageQueue
from core.agent_mail.event_bus import EventBus
from core.agent_mail.audit_trail import AuditTrail
from core.agent_mail.mailbox import MailboxFactory


def print_separator(title: str):
    """Print a visual separator."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def example_basic_messaging():
    """Example 1: Basic messaging between two agents."""
    print_separator("Example 1: Basic Messaging")

    # Setup infrastructure
    factory = MailboxFactory()

    # Create mailboxes
    orchestrator = factory.create_mailbox("Orchestrator")
    worker = factory.create_mailbox("Worker1")

    # Orchestrator sends task
    print("[Orchestrator] Sending task assignment...")
    msg = orchestrator.send(
        to_agent="Worker1",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Literature review on hepatotoxicity",
        body="## Task Description\n\nReview recent literature on drug-induced liver injury.",
        data={
            "task_id": "task-001",
            "query": "hepatotoxicity",
            "max_results": 50
        },
        priority=MessagePriority.HIGH
    )
    print(f"  ✓ Sent message: {msg.message_id[:8]}...")

    # Worker receives task
    print("\n[Worker1] Checking inbox...")
    received = worker.receive(timeout=1.0)
    if received:
        print(f"  ✓ Received: {received.subject}")
        print(f"  ✓ Type: {received.message_type.value}")
        print(f"  ✓ Priority: {received.priority.value}")
        print(f"  ✓ Data: {received.data}")

        # Worker acknowledges
        worker.acknowledge(received)
        print("  ✓ Acknowledged")


def example_conversation_threading():
    """Example 2: Multi-message conversation with threading."""
    print_separator("Example 2: Conversation Threading")

    factory = MailboxFactory()
    orchestrator = factory.create_mailbox("Orchestrator")
    worker = factory.create_mailbox("Worker1")

    thread_id = "conversation-001"

    # Message 1: Initial request
    print("[Orchestrator] Initiating conversation...")
    msg1 = orchestrator.send(
        to_agent="Worker1",
        message_type=MessageType.STATUS_UPDATE,
        subject="Status check",
        body="Are you ready to process tasks?",
        thread_id=thread_id
    )
    print(f"  ✓ Sent: {msg1.subject}")

    # Message 2: Worker replies
    print("\n[Worker1] Replying...")
    received1 = worker.receive()
    reply1 = worker.reply(
        received1,
        subject="Re: Status check",
        body="Yes, ready and waiting",
        data={"status": "ready", "queue_size": 0}
    )
    print(f"  ✓ Replied: {reply1.subject}")

    # Message 3: Orchestrator sends task
    print("\n[Orchestrator] Sending task...")
    received2 = orchestrator.receive()
    msg3 = orchestrator.send(
        to_agent="Worker1",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Processing task",
        body="Begin literature review",
        data={"task_id": "task-002"},
        thread_id=thread_id
    )
    print(f"  ✓ Sent: {msg3.subject}")

    # Retrieve conversation history
    print("\n[Orchestrator] Retrieving conversation history...")
    history = orchestrator.get_thread_history(thread_id)
    print(f"  ✓ Found {len(history)} messages in thread '{thread_id}':")
    for i, msg in enumerate(history, 1):
        print(f"     {i}. {msg.from_agent} → {msg.to_agent}: {msg.subject}")


def example_priority_handling():
    """Example 3: Priority-based message ordering."""
    print_separator("Example 3: Priority Message Handling")

    factory = MailboxFactory()
    sender = factory.create_mailbox("Sender")
    receiver = factory.create_mailbox("Receiver")

    # Send messages with different priorities
    print("[Sender] Sending messages with different priorities...")

    sender.send(
        to_agent="Receiver",
        message_type=MessageType.STATUS_UPDATE,
        subject="Low priority status update",
        priority=MessagePriority.LOW
    )
    print("  ✓ Sent: LOW priority message")

    sender.send(
        to_agent="Receiver",
        message_type=MessageType.ESCALATION,
        subject="URGENT: Critical issue detected",
        priority=MessagePriority.HIGH
    )
    print("  ✓ Sent: HIGH priority message")

    sender.send(
        to_agent="Receiver",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Regular task assignment",
        priority=MessagePriority.MEDIUM
    )
    print("  ✓ Sent: MEDIUM priority message")

    # Receive in priority order
    print("\n[Receiver] Receiving messages (priority order)...")
    for i in range(3):
        msg = receiver.receive(timeout=1.0)
        if msg:
            print(f"  {i+1}. Priority {msg.priority.value}: {msg.subject}")


def example_event_bus_monitoring():
    """Example 4: Event bus for system monitoring."""
    print_separator("Example 4: Event Bus Monitoring")

    factory = MailboxFactory()
    event_bus = factory.event_bus

    # Track events
    events_log = []

    def log_all_events(data):
        """Log all events."""
        events_log.append(data)
        print(f"  📡 Event: {data}")

    # Subscribe to all events
    event_bus.subscribe("*", log_all_events)

    # Create agents and exchange messages
    agent1 = factory.create_mailbox("Agent1")
    agent2 = factory.create_mailbox("Agent2")

    print("[Agent1] Sending message...")
    agent1.send(
        to_agent="Agent2",
        message_type=MessageType.STATUS_UPDATE,
        subject="Test message"
    )

    print("\n[Agent2] Receiving message...")
    msg = agent2.receive(timeout=1.0)

    print("\n[Agent2] Acknowledging message...")
    if msg:
        agent2.acknowledge(msg)

    print(f"\n✓ Total events captured: {len(events_log)}")


def example_audit_trail_queries():
    """Example 5: Querying the audit trail."""
    print_separator("Example 5: Audit Trail Queries")

    # Setup with audit trail
    audit_trail = AuditTrail("example_audit_trail.db")
    factory = MailboxFactory(audit_trail=audit_trail)

    orchestrator = factory.create_mailbox("Orchestrator")
    worker1 = factory.create_mailbox("Worker1")
    worker2 = factory.create_mailbox("Worker2")

    # Generate some activity
    print("Generating message activity...")
    for i in range(5):
        orchestrator.send(
            to_agent="Worker1",
            message_type=MessageType.TASK_ASSIGNMENT,
            subject=f"Task {i+1}",
            data={"task_id": f"task-{i+1}"}
        )
        worker1.receive()

    for i in range(3):
        orchestrator.send(
            to_agent="Worker2",
            message_type=MessageType.STATUS_UPDATE,
            subject=f"Status check {i+1}"
        )
        worker2.receive()

    # Query audit trail
    print("\n1. Messages sent by Orchestrator:")
    sent_messages = audit_trail.get_agent_messages("Orchestrator", direction="sent", limit=10)
    for msg in sent_messages[:3]:
        print(f"   → {msg['to_agent']}: {msg['subject']}")

    print("\n2. Messages received by Worker1:")
    received_messages = audit_trail.get_agent_messages("Worker1", direction="received", limit=10)
    for msg in received_messages[:3]:
        print(f"   ← {msg['from_agent']}: {msg['subject']}")

    print("\n3. Search for 'Task' messages:")
    search_results = audit_trail.search_messages("Task")
    print(f"   Found {len(search_results)} messages containing 'Task'")

    print("\n4. System statistics:")
    stats = audit_trail.get_stats()
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Unique agents: {stats['unique_agents']}")
    print(f"   Unique threads: {stats['unique_threads']}")
    print(f"   Messages by type:")
    for msg_type, count in stats['messages_by_type'].items():
        print(f"     - {msg_type}: {count}")

    # Cleanup
    import os
    if os.path.exists("example_audit_trail.db"):
        os.unlink("example_audit_trail.db")


def example_concurrent_agents():
    """Example 6: Multiple agents operating concurrently."""
    print_separator("Example 6: Concurrent Multi-Agent Operation")

    factory = MailboxFactory()

    # Create agent mailboxes
    orchestrator = factory.create_mailbox("Orchestrator")
    workers = [factory.create_mailbox(f"Worker{i}") for i in range(1, 4)]

    print(f"Created {len(workers)} worker agents")

    def worker_activity(worker_mailbox):
        """Worker receives task and sends result."""
        # Receive task
        task = worker_mailbox.receive(timeout=2.0)
        if task:
            print(f"  [{worker_mailbox.agent_name}] Received task: {task.data['task_id']}")

            # Simulate processing
            time.sleep(0.1)

            # Send result
            worker_mailbox.send(
                to_agent="Orchestrator",
                message_type=MessageType.TASK_RESULT,
                subject=f"Task {task.data['task_id']} completed",
                data={
                    "task_id": task.data['task_id'],
                    "status": "completed",
                    "worker": worker_mailbox.agent_name
                },
                thread_id=task.thread_id
            )
            print(f"  [{worker_mailbox.agent_name}] Sent result")

    # Orchestrator distributes tasks
    print("\n[Orchestrator] Distributing tasks...")
    for i, worker in enumerate(workers, 1):
        orchestrator.send(
            to_agent=worker.agent_name,
            message_type=MessageType.TASK_ASSIGNMENT,
            subject=f"Process task {i}",
            data={"task_id": f"task-{i}"},
            thread_id=f"task-{i}",
            priority=MessagePriority.HIGH
        )
        print(f"  ✓ Assigned task {i} to {worker.agent_name}")

    # Start workers concurrently
    print("\n[Workers] Processing tasks concurrently...")
    threads = [threading.Thread(target=worker_activity, args=(w,)) for w in workers]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Orchestrator collects results
    print("\n[Orchestrator] Collecting results...")
    for i in range(len(workers)):
        result = orchestrator.receive(timeout=1.0)
        if result:
            print(f"  ✓ Received result from {result.data['worker']}: {result.data['status']}")


def example_complete_workflow():
    """Example 7: Complete Agent-Audit-Resolve workflow with messaging."""
    print_separator("Example 7: Complete Agent-Audit-Resolve Workflow")

    audit_trail = AuditTrail("workflow_audit.db")
    factory = MailboxFactory(audit_trail=audit_trail)

    orchestrator = factory.create_mailbox("Orchestrator")
    worker = factory.create_mailbox("LiteratureWorker")
    auditor = factory.create_mailbox("LiteratureAuditor")

    thread_id = "task-workflow-001"

    # Step 1: Orchestrator assigns task
    print("Step 1: Orchestrator assigns task to worker")
    orchestrator.send(
        to_agent="LiteratureWorker",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Literature review: Drug safety",
        body="## Assignment\n\nReview literature on drug hepatotoxicity",
        data={
            "task_id": "task-001",
            "query": "drug hepatotoxicity",
            "max_results": 50
        },
        thread_id=thread_id,
        priority=MessagePriority.HIGH,
        requires_ack=True
    )
    print("  ✓ Task sent")

    # Step 2: Worker receives and processes
    print("\nStep 2: Worker receives task")
    task = worker.receive()
    if task:
        print(f"  ✓ Received: {task.subject}")
        worker.acknowledge(task)

        # Simulate processing
        print("  ⏳ Processing...")
        time.sleep(0.2)

        # Send result for audit
        print("  ✓ Sending result to auditor")
        worker.send(
            to_agent="LiteratureAuditor",
            message_type=MessageType.AUDIT_REQUEST,
            subject="Audit request: Literature review results",
            body="## Results\n\nFound 42 papers on drug hepatotoxicity",
            data={
                "task_id": "task-001",
                "papers_found": 42,
                "summary": "Comprehensive review completed",
                "sources": ["PubMed", "Cochrane"],
                "confidence": "high"
            },
            thread_id=thread_id
        )

    # Step 3: Auditor validates
    print("\nStep 3: Auditor validates results")
    audit_request = auditor.receive()
    if audit_request:
        print(f"  ✓ Received audit request")

        # Validate (in real system, this would be sophisticated)
        print("  ⏳ Validating...")
        time.sleep(0.1)

        result_quality = audit_request.data.get("papers_found", 0) >= 30
        status = "PASSED" if result_quality else "FAILED"

        print(f"  ✓ Validation: {status}")

        # Send audit result to orchestrator
        auditor.send(
            to_agent="Orchestrator",
            message_type=MessageType.AUDIT_RESULT,
            subject=f"Audit result: {status}",
            body=f"## Audit Summary\n\nStatus: **{status}**\n\nResults meet quality standards.",
            data={
                "task_id": "task-001",
                "status": status.lower(),
                "issues": [] if result_quality else ["Insufficient papers"],
                "quality_score": 0.95 if result_quality else 0.65
            },
            thread_id=thread_id
        )

    # Step 4: Orchestrator receives final result
    print("\nStep 4: Orchestrator receives audit result")
    final_result = orchestrator.receive()
    if final_result:
        print(f"  ✓ Task {final_result.data['task_id']}: {final_result.data['status'].upper()}")
        print(f"  ✓ Quality score: {final_result.data['quality_score']}")

    # Show thread history
    print("\n📜 Complete Conversation Thread:")
    history = orchestrator.get_thread_history(thread_id)
    for i, msg in enumerate(history, 1):
        print(f"  {i}. {msg.from_agent:20} → {msg.to_agent:20} | {msg.message_type.value:20} | {msg.subject}")

    # Cleanup
    import os
    if os.path.exists("workflow_audit.db"):
        os.unlink("workflow_audit.db")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("  Agent Mail System - Complete Examples")
    print("="*70)

    examples = [
        ("Basic Messaging", example_basic_messaging),
        ("Conversation Threading", example_conversation_threading),
        ("Priority Handling", example_priority_handling),
        ("Event Bus Monitoring", example_event_bus_monitoring),
        ("Audit Trail Queries", example_audit_trail_queries),
        ("Concurrent Agents", example_concurrent_agents),
        ("Complete Workflow", example_complete_workflow),
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()

        # Pause between examples
        if i < len(examples):
            time.sleep(0.5)

    print_separator("All Examples Complete! ✨")

    print("Summary:")
    print("  ✓ Message transport with type safety")
    print("  ✓ Priority-based queue ordering")
    print("  ✓ Conversation threading")
    print("  ✓ Event bus for monitoring")
    print("  ✓ Persistent audit trail")
    print("  ✓ Concurrent multi-agent coordination")
    print("  ✓ Complete Agent-Audit-Resolve workflow")
    print("\nAgent Mail System is ready for production use!")


if __name__ == "__main__":
    main()
