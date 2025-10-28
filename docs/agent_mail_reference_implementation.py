"""
Agent Mail System - Minimal Reference Implementation

This is a simplified, working implementation of the core agent mail concepts.
Shows the essential patterns without all the bells and whistles.

Usage:
    python agent_mail_reference_implementation.py
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from queue import Queue, PriorityQueue
import threading
import time
import uuid


# ============================================================================
# MESSAGE DATA MODEL
# ============================================================================

class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    AUDIT_REQUEST = "audit_request"
    AUDIT_RESULT = "audit_result"
    STATUS_UPDATE = "status_update"


class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class AgentMessage:
    """A message sent between agents."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.TASK_ASSIGNMENT
    subject: str = ""
    body: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_delivered: bool = False
    is_read: bool = False

    def mark_delivered(self):
        self.is_delivered = True

    def mark_read(self):
        self.is_read = True


# ============================================================================
# TRANSPORT LAYER
# ============================================================================

class InMemoryTransport:
    """In-memory message transport using threading.Queue."""

    def __init__(self):
        self.mailboxes: Dict[str, Queue] = {}
        self.lock = threading.Lock()

    def _get_mailbox(self, agent_id: str) -> Queue:
        """Get or create mailbox for agent."""
        with self.lock:
            if agent_id not in self.mailboxes:
                self.mailboxes[agent_id] = Queue()
            return self.mailboxes[agent_id]

    def send(self, message: AgentMessage) -> bool:
        """Send message to agent's queue."""
        mailbox = self._get_mailbox(message.receiver_id)
        mailbox.put(message)
        message.mark_delivered()
        return True

    def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[AgentMessage]:
        """Receive next message (blocking with timeout)."""
        mailbox = self._get_mailbox(agent_id)
        try:
            message = mailbox.get(timeout=timeout)
            message.mark_read()
            return message
        except:
            return None

    def get_queue_size(self, agent_id: str) -> int:
        """Get pending message count."""
        mailbox = self._get_mailbox(agent_id)
        return mailbox.qsize()


# ============================================================================
# AGENT MAILBOX (Central Hub)
# ============================================================================

class AgentMailbox:
    """Central message hub for all agent communication."""

    def __init__(self, transport: Optional[InMemoryTransport] = None):
        self.transport = transport or InMemoryTransport()
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> [agent_ids]
        self.message_history: List[AgentMessage] = []
        self.lock = threading.Lock()

    def send(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Send a message to a specific agent."""
        message = AgentMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            subject=subject,
            body=body,
            priority=priority,
            correlation_id=correlation_id,
        )

        # Add to history
        with self.lock:
            self.message_history.append(message)

        # Deliver
        self.transport.send(message)

        print(f"[MAIL] {sender_id} → {receiver_id}: {subject}")
        return message.message_id

    def receive(
        self,
        agent_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[AgentMessage]:
        """Receive next message for an agent."""
        return self.transport.receive(agent_id, timeout=timeout)

    def get_pending_count(self, agent_id: str) -> int:
        """Get number of pending messages."""
        return self.transport.get_queue_size(agent_id)

    def subscribe(self, agent_id: str, topic: str):
        """Subscribe agent to a topic."""
        with self.lock:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = []
            if agent_id not in self.subscriptions[topic]:
                self.subscriptions[topic].append(agent_id)

    def publish(
        self,
        sender_id: str,
        topic: str,
        message_type: MessageType,
        subject: str,
        body: Dict[str, Any],
    ) -> None:
        """Publish message to topic subscribers."""
        subscribers = self.subscriptions.get(topic, [])
        for agent_id in subscribers:
            self.send(
                sender_id=sender_id,
                receiver_id=agent_id,
                message_type=message_type,
                subject=subject,
                body=body,
            )

    def get_message_history(
        self,
        correlation_id: Optional[str] = None
    ) -> List[AgentMessage]:
        """Get message history."""
        with self.lock:
            messages = self.message_history.copy()

        if correlation_id:
            messages = [m for m in messages if m.correlation_id == correlation_id]

        messages.sort(key=lambda m: m.created_at)
        return messages


# ============================================================================
# AGENT IMPLEMENTATIONS
# ============================================================================

class BaseAgentWithMail:
    """Base class for agents with mail support."""

    def __init__(self, agent_id: str, mailbox: AgentMailbox):
        self.agent_id = agent_id
        self.mailbox = mailbox
        self.is_running = False
        self.worker_thread = None

    def start(self):
        """Start listening for messages."""
        if self.is_running:
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.worker_thread.start()
        print(f"[AGENT] {self.agent_id} started")

    def stop(self):
        """Stop listening."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2.0)
        print(f"[AGENT] {self.agent_id} stopped")

    def _message_loop(self):
        """Main message processing loop."""
        while self.is_running:
            try:
                message = self.mailbox.receive(
                    agent_id=self.agent_id,
                    timeout=0.5
                )

                if message:
                    self._handle_message(message)

            except Exception as e:
                print(f"[ERROR] {self.agent_id}: {e}")

    def _handle_message(self, message: AgentMessage):
        """Handle incoming message (override in subclass)."""
        pass


class WorkerAgent(BaseAgentWithMail):
    """Example worker agent that processes tasks."""

    def _handle_message(self, message: AgentMessage):
        """Handle task assignments."""
        if message.message_type == MessageType.TASK_ASSIGNMENT:
            print(f"[WORKER] {self.agent_id} executing task: {message.subject}")

            # Simulate work
            time.sleep(0.5)

            # Send result back
            self.mailbox.send(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.TASK_RESULT,
                subject=f"Completed: {message.subject}",
                body={
                    "task_id": message.body.get("task_id"),
                    "result": "Task completed successfully",
                    "data": {"findings": ["Finding 1", "Finding 2"]},
                },
                correlation_id=message.correlation_id,
            )


class AuditorAgent(BaseAgentWithMail):
    """Example auditor agent that validates outputs."""

    def _handle_message(self, message: AgentMessage):
        """Handle audit requests."""
        if message.message_type == MessageType.AUDIT_REQUEST:
            print(f"[AUDITOR] {self.agent_id} auditing: {message.subject}")

            # Simulate audit
            time.sleep(0.3)

            # Determine pass/fail (simple logic for demo)
            passed = len(message.body.get("output", {}).get("data", {}).get("findings", [])) >= 2

            # Send audit result back
            self.mailbox.send(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.AUDIT_RESULT,
                subject=f"Audit: {'PASSED' if passed else 'FAILED'}",
                body={
                    "task_id": message.body.get("task_id"),
                    "status": "passed" if passed else "failed",
                    "issues": [] if passed else [{"category": "insufficient_findings"}],
                },
                correlation_id=message.correlation_id,
            )


class OrchestratorAgent:
    """Example orchestrator that coordinates work."""

    def __init__(self, agent_id: str, mailbox: AgentMailbox):
        self.agent_id = agent_id
        self.mailbox = mailbox

    def process_task(
        self,
        task_id: str,
        worker_id: str,
        auditor_id: str,
        query: str
    ) -> str:
        """Process a task through worker → audit cycle."""
        correlation_id = task_id

        print(f"\n[ORCHESTRATOR] Processing task {task_id}")

        # Step 1: Send task to worker
        self.mailbox.send(
            sender_id=self.agent_id,
            receiver_id=worker_id,
            message_type=MessageType.TASK_ASSIGNMENT,
            subject=f"Execute: {query}",
            body={"task_id": task_id, "query": query},
            correlation_id=correlation_id,
        )

        # Step 2: Wait for result
        print(f"[ORCHESTRATOR] Waiting for worker result...")
        result_msg = self._wait_for_message(
            message_type=MessageType.TASK_RESULT,
            correlation_id=correlation_id,
            timeout=5.0
        )

        if not result_msg:
            return "ERROR: Worker timeout"

        print(f"[ORCHESTRATOR] Received result from worker")

        # Step 3: Send to auditor
        self.mailbox.send(
            sender_id=self.agent_id,
            receiver_id=auditor_id,
            message_type=MessageType.AUDIT_REQUEST,
            subject=f"Audit: {query}",
            body={
                "task_id": task_id,
                "input": {"query": query},
                "output": result_msg.body,
            },
            correlation_id=correlation_id,
        )

        # Step 4: Wait for audit result
        print(f"[ORCHESTRATOR] Waiting for audit result...")
        audit_msg = self._wait_for_message(
            message_type=MessageType.AUDIT_RESULT,
            correlation_id=correlation_id,
            timeout=5.0
        )

        if not audit_msg:
            return "ERROR: Auditor timeout"

        status = audit_msg.body.get("status")
        print(f"[ORCHESTRATOR] Audit result: {status}")

        return status

    def _wait_for_message(
        self,
        message_type: MessageType,
        correlation_id: str,
        timeout: float
    ) -> Optional[AgentMessage]:
        """Wait for a specific message."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            message = self.mailbox.receive(
                agent_id=self.agent_id,
                timeout=0.5
            )

            if message and message.message_type == message_type and message.correlation_id == correlation_id:
                return message

        return None


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo_basic_messaging():
    """Demonstrate basic send/receive."""
    print("\n" + "="*60)
    print("DEMO 1: Basic Messaging")
    print("="*60)

    mailbox = AgentMailbox()

    # Send a message
    msg_id = mailbox.send(
        sender_id="agent_a",
        receiver_id="agent_b",
        message_type=MessageType.TASK_ASSIGNMENT,
        subject="Hello, Agent B!",
        body={"data": "test"}
    )

    # Receive the message
    message = mailbox.receive(agent_id="agent_b", timeout=1.0)

    print(f"Received: {message.subject}")
    print(f"Body: {message.body}")
    print(f"From: {message.sender_id}")


def demo_pub_sub():
    """Demonstrate publish/subscribe."""
    print("\n" + "="*60)
    print("DEMO 2: Publish/Subscribe")
    print("="*60)

    mailbox = AgentMailbox()

    # Subscribe agents to topic
    mailbox.subscribe("monitor_1", "task_completed")
    mailbox.subscribe("monitor_2", "task_completed")
    mailbox.subscribe("monitor_3", "task_completed")

    # Publish event
    mailbox.publish(
        sender_id="worker",
        topic="task_completed",
        message_type=MessageType.STATUS_UPDATE,
        subject="Task 123 completed",
        body={"task_id": "123", "status": "success"}
    )

    # All subscribers receive
    for i in range(1, 4):
        msg = mailbox.receive(f"monitor_{i}", timeout=1.0)
        if msg:
            print(f"Monitor {i} received: {msg.subject}")


def demo_agent_workflow():
    """Demonstrate full agent workflow."""
    print("\n" + "="*60)
    print("DEMO 3: Full Agent Workflow (Worker → Audit)")
    print("="*60)

    mailbox = AgentMailbox()

    # Create and start agents
    worker = WorkerAgent(agent_id="worker_001", mailbox=mailbox)
    auditor = AuditorAgent(agent_id="auditor_001", mailbox=mailbox)
    orchestrator = OrchestratorAgent(agent_id="orchestrator_001", mailbox=mailbox)

    worker.start()
    auditor.start()

    # Wait for agents to start
    time.sleep(0.2)

    # Process a task
    status = orchestrator.process_task(
        task_id="task_123",
        worker_id="worker_001",
        auditor_id="auditor_001",
        query="Analyze Drug X safety"
    )

    print(f"\n[RESULT] Final status: {status}")

    # Show message history
    print("\n[HISTORY] Message trace:")
    history = mailbox.get_message_history(correlation_id="task_123")
    for msg in history:
        print(f"  {msg.created_at.strftime('%H:%M:%S.%f')[:-3]} "
              f"[{msg.message_type.value}] {msg.sender_id} → {msg.receiver_id}")

    # Cleanup
    time.sleep(0.5)
    worker.stop()
    auditor.stop()


def demo_parallel_tasks():
    """Demonstrate parallel task execution."""
    print("\n" + "="*60)
    print("DEMO 4: Parallel Task Execution")
    print("="*60)

    mailbox = AgentMailbox()

    # Create multiple workers and auditors
    workers = [
        WorkerAgent(f"worker_{i}", mailbox) for i in range(3)
    ]
    auditors = [
        AuditorAgent(f"auditor_{i}", mailbox) for i in range(3)
    ]

    # Start all agents
    for w in workers:
        w.start()
    for a in auditors:
        a.start()

    time.sleep(0.2)

    # Create orchestrator
    orch = OrchestratorAgent("orchestrator", mailbox)

    # Process 3 tasks in parallel using threads
    import concurrent.futures

    def process_task(task_num):
        return orch.process_task(
            task_id=f"task_{task_num}",
            worker_id=f"worker_{task_num}",
            auditor_id=f"auditor_{task_num}",
            query=f"Analyze Dataset {task_num}"
        )

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_task, i) for i in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    elapsed = time.time() - start_time

    print(f"\n[RESULT] All tasks completed in {elapsed:.2f}s")
    print(f"[RESULT] Statuses: {results}")

    # Cleanup
    time.sleep(0.5)
    for w in workers:
        w.stop()
    for a in auditors:
        a.stop()


def demo_message_history():
    """Demonstrate message history and audit trail."""
    print("\n" + "="*60)
    print("DEMO 5: Message History & Audit Trail")
    print("="*60)

    mailbox = AgentMailbox()

    # Simulate a conversation
    correlation_id = "case_abc123"

    messages = [
        ("orchestrator", "worker", MessageType.TASK_ASSIGNMENT, "Do task A"),
        ("worker", "orchestrator", MessageType.TASK_RESULT, "Task A done"),
        ("orchestrator", "auditor", MessageType.AUDIT_REQUEST, "Audit task A"),
        ("auditor", "orchestrator", MessageType.AUDIT_RESULT, "Audit failed"),
        ("orchestrator", "worker", MessageType.TASK_ASSIGNMENT, "Retry task A"),
        ("worker", "orchestrator", MessageType.TASK_RESULT, "Task A done (retry)"),
        ("orchestrator", "auditor", MessageType.AUDIT_REQUEST, "Audit task A (retry)"),
        ("auditor", "orchestrator", MessageType.AUDIT_RESULT, "Audit passed"),
    ]

    for sender, receiver, msg_type, subject in messages:
        mailbox.send(
            sender_id=sender,
            receiver_id=receiver,
            message_type=msg_type,
            subject=subject,
            body={},
            correlation_id=correlation_id
        )
        time.sleep(0.05)  # Small delay to show progression

    # Retrieve history
    history = mailbox.get_message_history(correlation_id=correlation_id)

    print(f"\nComplete audit trail for {correlation_id}:")
    print(f"Total messages: {len(history)}\n")

    for i, msg in enumerate(history, 1):
        print(f"{i}. [{msg.message_type.value:20}] "
              f"{msg.sender_id:15} → {msg.receiver_id:15} | {msg.subject}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Agent Mail System - Reference Implementation")
    print("="*60)

    # Run all demos
    demo_basic_messaging()
    demo_pub_sub()
    demo_agent_workflow()
    demo_parallel_tasks()
    demo_message_history()

    print("\n" + "="*60)
    print("All demos completed!")
    print("="*60 + "\n")
