# Phase 1 Test Strategy: Multi-Agent Mail System Foundation

**Document Version:** 1.0
**Date:** 2025-11-01
**Status:** Ready for Implementation
**Coverage Target:** >80% code coverage
**Test Framework:** Custom (no pytest dependency)

---

## Table of Contents

1. [Overview](#overview)
2. [Test Architecture](#test-architecture)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [Performance Tests](#performance-tests)
6. [Test Utilities](#test-utilities)
7. [Test File Structure](#test-file-structure)
8. [Success Criteria](#success-criteria)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

### Objectives

This document specifies a comprehensive testing strategy for **Phase 1 (Foundation)** of the multi-agent mail system, covering:

- **Message System:** Message, Mailbox, MailBroker, Storage
- **Agent Registry:** AgentRegistry, AgentMetadata, Discovery
- **Integration:** Agent-to-agent messaging, multi-agent coordination

### Testing Philosophy

Following the existing test patterns in `test_full_integration.py` and `test_hybrid_audit.py`:

1. **No Placeholders:** All tests use real data structures and realistic scenarios
2. **Safety First:** Critical functionality marked and tested rigorously
3. **Graceful Degradation:** Tests verify system behavior under failure conditions
4. **Comprehensive Validation:** Each test includes detailed assertions and logging
5. **Self-Documenting:** Tests serve as examples and documentation

### Coverage Requirements

- **Unit Tests:** >90% coverage for core classes
- **Integration Tests:** >80% coverage for cross-component interactions
- **Performance Tests:** Baseline metrics for optimization
- **Overall Target:** >80% total code coverage

---

## Test Architecture

### Test Organization Pattern

Following `test_full_integration.py` pattern:

```python
class TestComponentName:
    """
    Test ComponentName functionality.

    VALIDATION CRITERIA:
    - Criterion 1
    - Criterion 2
    - Criterion 3
    """

    def test_specific_behavior(self):
        """Test specific behavior with detailed validation."""
        logger.info("=" * 80)
        logger.info("TEST: Description")
        logger.info("=" * 80)

        # Setup
        component = Component()

        # Execute
        result = component.method()

        # Validate
        assert result is not None, "Result should not be None"
        assert result.field == expected, f"Expected {expected}, got {result.field}"

        logger.info("✓ TEST PASSED: Description")
```

### Test Runner Pattern

Custom test runner (no pytest):

```python
def run_test(test_func, test_name):
    """Run a single test function and report results."""
    try:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"RUNNING: {test_name}")
        logger.info(f"{'=' * 80}\n")
        test_func()
        logger.info(f"\n✓ PASSED: {test_name}\n")
        return True, None
    except AssertionError as e:
        logger.error(f"\n✗ FAILED: {test_name}")
        logger.error(f"AssertionError: {str(e)}\n")
        return False, str(e)
    except Exception as e:
        logger.error(f"\n✗ ERROR: {test_name}")
        logger.error(f"Exception: {str(e)}")
        logger.error(traceback.format_exc())
        return False, str(e)
```

---

## Unit Tests

### 1. Message Class Tests

**File:** `tests/unit/test_message.py`

#### 1.1 Message Creation and Validation

**Test:** `test_message_creation_valid`

**Scenario:** Create valid message with all required fields

**Setup:**
```python
from core.mail.message import Message, MessageType, MessagePriority
from datetime import datetime

# Create valid message
message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002", "agent_003"],
    message_type=MessageType.REQUEST,
    subject="Test Message",
    body={"content": "Hello World", "data": [1, 2, 3]}
)
```

**Assertions:**
- `assert message.message_id is not None, "Message ID should be auto-generated"`
- `assert isinstance(message.message_id, str), "Message ID should be string"`
- `assert message.sender_id == "agent_001", "Sender ID should match"`
- `assert len(message.recipient_ids) == 2, "Should have 2 recipients"`
- `assert message.message_type == MessageType.REQUEST, "Message type should match"`
- `assert message.priority == MessagePriority.NORMAL, "Default priority should be NORMAL"`
- `assert isinstance(message.timestamp, datetime), "Timestamp should be datetime object"`

**Success Criteria:** All assertions pass, message created successfully

---

**Test:** `test_message_creation_missing_required_fields`

**Scenario:** Attempt to create message without required fields

**Setup:**
```python
# Missing sender_id
try:
    message = Message(
        recipient_ids=["agent_002"],
        message_type=MessageType.REQUEST,
        subject="Test",
        body={}
    )
    assert False, "Should have raised ValueError"
except (ValueError, TypeError) as e:
    assert "sender" in str(e).lower() or "required" in str(e).lower()
```

**Assertions:**
- `ValueError` or `TypeError` raised for missing `sender_id`
- `ValueError` or `TypeError` raised for missing `recipient_ids`
- `ValueError` or `TypeError` raised for missing `message_type`
- `ValueError` or `TypeError` raised for missing `subject`
- `ValueError` or `TypeError` raised for missing `body`

**Success Criteria:** All required field validations trigger appropriate errors

---

**Test:** `test_message_invalid_recipient_ids`

**Scenario:** Create message with invalid recipient list

**Setup:**
```python
# Empty recipient list
try:
    message = Message(
        sender_id="agent_001",
        recipient_ids=[],  # Empty list
        message_type=MessageType.REQUEST,
        subject="Test",
        body={}
    )
    assert False, "Should raise ValueError for empty recipient list"
except ValueError as e:
    assert "recipient" in str(e).lower()
```

**Assertions:**
- Empty recipient list raises `ValueError`
- Non-list recipient raises `TypeError`
- Recipient with empty string raises `ValueError`

**Success Criteria:** Invalid recipient validation works correctly

---

#### 1.2 Message Serialization

**Test:** `test_message_to_dict`

**Scenario:** Serialize message to dictionary

**Setup:**
```python
message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.RESPONSE,
    subject="Test Response",
    body={"result": "success"},
    thread_id="thread_123",
    priority=MessagePriority.HIGH
)

msg_dict = message.to_dict()
```

**Assertions:**
- `assert isinstance(msg_dict, dict), "Should return dictionary"`
- `assert msg_dict["sender_id"] == "agent_001", "Sender ID preserved"`
- `assert msg_dict["recipient_ids"] == ["agent_002"], "Recipients preserved"`
- `assert msg_dict["message_type"] == "response", "Message type serialized"`
- `assert msg_dict["priority"] == "high", "Priority serialized"`
- `assert "timestamp" in msg_dict, "Timestamp included"`
- `assert "message_id" in msg_dict, "Message ID included"`

**Success Criteria:** All fields correctly serialized to dict

---

**Test:** `test_message_from_dict`

**Scenario:** Deserialize message from dictionary

**Setup:**
```python
msg_dict = {
    "message_id": "msg_123",
    "sender_id": "agent_001",
    "recipient_ids": ["agent_002"],
    "message_type": "request",
    "subject": "Test",
    "body": {"data": 123},
    "timestamp": "2025-11-01T10:00:00",
    "priority": "normal"
}

message = Message.from_dict(msg_dict)
```

**Assertions:**
- `assert message.message_id == "msg_123", "Message ID restored"`
- `assert message.sender_id == "agent_001", "Sender ID restored"`
- `assert message.message_type == MessageType.REQUEST, "Message type restored"`
- `assert message.body["data"] == 123, "Body data restored"`

**Success Criteria:** Message correctly reconstructed from dict

---

**Test:** `test_message_json_roundtrip`

**Scenario:** Serialize to JSON and back

**Setup:**
```python
import json

original = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002", "agent_003"],
    message_type=MessageType.BROADCAST,
    subject="Test Broadcast",
    body={"announcement": "System update"}
)

# Serialize to JSON
json_str = original.to_json()
msg_dict = json.loads(json_str)

# Deserialize back
restored = Message.from_dict(msg_dict)
```

**Assertions:**
- `assert json_str is not None, "JSON string should not be None"`
- `assert isinstance(json_str, str), "Should return string"`
- `assert restored.sender_id == original.sender_id, "Sender preserved"`
- `assert restored.recipient_ids == original.recipient_ids, "Recipients preserved"`
- `assert restored.message_type == original.message_type, "Type preserved"`
- `assert restored.body == original.body, "Body preserved"`

**Success Criteria:** Full JSON roundtrip preserves all data

---

#### 1.3 Message Threading

**Test:** `test_message_thread_tracking`

**Scenario:** Verify thread and reply tracking

**Setup:**
```python
# Initial message
msg1 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Initial Request",
    body={"question": "What is X?"}
)

# Reply message
msg2 = Message(
    sender_id="agent_002",
    recipient_ids=["agent_001"],
    message_type=MessageType.RESPONSE,
    subject="Re: Initial Request",
    body={"answer": "X is Y"},
    thread_id=msg1.message_id,  # Same thread
    in_reply_to=msg1.message_id  # Direct reply
)
```

**Assertions:**
- `assert msg2.thread_id == msg1.message_id, "Thread ID should match"`
- `assert msg2.in_reply_to == msg1.message_id, "Reply reference correct"`
- `assert msg2.message_type == MessageType.RESPONSE, "Response type set"`

**Success Criteria:** Thread tracking works correctly

---

#### 1.4 Message Priority

**Test:** `test_message_priority_levels`

**Scenario:** Verify all priority levels work

**Setup:**
```python
priorities = [
    MessagePriority.URGENT,
    MessagePriority.HIGH,
    MessagePriority.NORMAL,
    MessagePriority.LOW
]

messages = []
for priority in priorities:
    msg = Message(
        sender_id="agent_001",
        recipient_ids=["agent_002"],
        message_type=MessageType.NOTIFICATION,
        subject=f"Priority {priority.value}",
        body={},
        priority=priority
    )
    messages.append(msg)
```

**Assertions:**
- `assert len(messages) == 4, "Should create 4 messages"`
- `assert messages[0].priority == MessagePriority.URGENT, "Urgent priority set"`
- `assert messages[1].priority == MessagePriority.HIGH, "High priority set"`
- `assert messages[2].priority == MessagePriority.NORMAL, "Normal priority set"`
- `assert messages[3].priority == MessagePriority.LOW, "Low priority set"`

**Success Criteria:** All priority levels supported

---

### 2. Mailbox Class Tests

**File:** `tests/unit/test_mailbox.py`

#### 2.1 Mailbox Creation and Basic Operations

**Test:** `test_mailbox_creation`

**Scenario:** Create mailbox for agent

**Setup:**
```python
from core.mail.mailbox import Mailbox
from core.mail.storage import InMemoryMailStorage

storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_001", storage_backend=storage)
```

**Assertions:**
- `assert mailbox.agent_id == "agent_001", "Agent ID should match"`
- `assert mailbox.storage is not None, "Storage backend should be set"`
- `assert mailbox.inbox is not None, "Inbox should exist"`
- `assert mailbox.outbox is not None, "Outbox should exist"`

**Success Criteria:** Mailbox created with all components

---

**Test:** `test_mailbox_send_message`

**Scenario:** Send message via mailbox

**Setup:**
```python
storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_001", storage_backend=storage)

message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={"data": "test"}
)

message_id = mailbox.send(message)
```

**Assertions:**
- `assert message_id is not None, "Should return message ID"`
- `assert isinstance(message_id, str), "Message ID should be string"`
- `assert message_id == message.message_id, "Should return message's ID"`

**Mock Requirements:**
- Storage backend should be called to save message
- Outbox should contain the message

**Success Criteria:** Message sent successfully

---

**Test:** `test_mailbox_receive_message`

**Scenario:** Receive message from inbox

**Setup:**
```python
storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_002", storage_backend=storage)

# Simulate message delivery to inbox
message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={"data": "test"}
)
mailbox.inbox.put(message)

# Receive message
received = mailbox.receive(timeout=1.0)
```

**Assertions:**
- `assert received is not None, "Should receive message"`
- `assert received.message_id == message.message_id, "Message ID matches"`
- `assert received.sender_id == "agent_001", "Sender matches"`

**Success Criteria:** Message received successfully

---

**Test:** `test_mailbox_receive_timeout`

**Scenario:** Receive with timeout when inbox empty

**Setup:**
```python
storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_001", storage_backend=storage)

import time
start = time.time()
received = mailbox.receive(timeout=0.5)
elapsed = time.time() - start
```

**Assertions:**
- `assert received is None, "Should return None when empty"`
- `assert 0.4 <= elapsed <= 0.7, "Should timeout after ~0.5 seconds"`

**Success Criteria:** Timeout behavior correct

---

#### 2.2 Mailbox Filtering

**Test:** `test_mailbox_add_filter`

**Scenario:** Add message filter to mailbox

**Setup:**
```python
storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_001", storage_backend=storage)

# Filter: only accept URGENT messages
def urgent_filter(msg):
    return msg.priority == MessagePriority.URGENT

mailbox.add_filter(urgent_filter)

# Send urgent message
urgent_msg = Message(
    sender_id="agent_002",
    recipient_ids=["agent_001"],
    message_type=MessageType.NOTIFICATION,
    subject="Urgent",
    body={},
    priority=MessagePriority.URGENT
)

# Send normal message
normal_msg = Message(
    sender_id="agent_002",
    recipient_ids=["agent_001"],
    message_type=MessageType.NOTIFICATION,
    subject="Normal",
    body={},
    priority=MessagePriority.NORMAL
)

# Deliver both
mailbox.inbox.put(urgent_msg)
mailbox.inbox.put(normal_msg)

# Check filter
filtered = mailbox.check_inbox(filters={"priority": "urgent"})
```

**Assertions:**
- `assert len(filtered) == 1, "Should only match urgent message"`
- `assert filtered[0].priority == MessagePriority.URGENT, "Urgent message matched"`

**Success Criteria:** Filtering works correctly

---

#### 2.3 Thread Management

**Test:** `test_mailbox_get_thread`

**Scenario:** Retrieve all messages in a conversation thread

**Setup:**
```python
storage = InMemoryMailStorage()
mailbox = Mailbox(agent_id="agent_001", storage_backend=storage)

# Create thread
msg1 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Question",
    body={"q": "What is X?"}
)

msg2 = Message(
    sender_id="agent_002",
    recipient_ids=["agent_001"],
    message_type=MessageType.RESPONSE,
    subject="Re: Question",
    body={"a": "X is Y"},
    thread_id=msg1.message_id,
    in_reply_to=msg1.message_id
)

msg3 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Re: Question",
    body={"q": "What about Z?"},
    thread_id=msg1.message_id,
    in_reply_to=msg2.message_id
)

# Store in storage backend
for msg in [msg1, msg2, msg3]:
    storage.save_message(msg)

# Retrieve thread
thread = mailbox.get_thread(msg1.message_id)
```

**Assertions:**
- `assert len(thread) == 3, "Should retrieve all 3 messages"`
- `assert thread[0].message_id == msg1.message_id, "First message correct"`
- `assert all(m.thread_id == msg1.message_id for m in thread[1:]), "All in same thread"`

**Success Criteria:** Thread retrieval works correctly

---

### 3. MailBroker Tests

**File:** `tests/unit/test_mail_broker.py`

#### 3.1 Broker Initialization

**Test:** `test_broker_creation`

**Scenario:** Create mail broker

**Setup:**
```python
from core.mail.broker import MailBroker
from core.mail.storage import InMemoryMailStorage

storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)
```

**Assertions:**
- `assert broker.storage is not None, "Storage should be set"`
- `assert len(broker.mailboxes) == 0, "Should start with no mailboxes"`
- `assert len(broker.subscriptions) == 0, "Should start with no subscriptions"`

**Success Criteria:** Broker initialized correctly

---

**Test:** `test_broker_register_mailbox`

**Scenario:** Register mailbox for agent

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

mailbox = broker.register_mailbox("agent_001")
```

**Assertions:**
- `assert mailbox is not None, "Should return mailbox"`
- `assert mailbox.agent_id == "agent_001", "Agent ID should match"`
- `assert "agent_001" in broker.mailboxes, "Mailbox should be registered"`
- `assert broker.mailboxes["agent_001"] == mailbox, "Mailbox stored correctly"`

**Success Criteria:** Mailbox registered successfully

---

**Test:** `test_broker_register_duplicate_mailbox`

**Scenario:** Attempt to register same agent twice

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

mailbox1 = broker.register_mailbox("agent_001")
mailbox2 = broker.register_mailbox("agent_001")  # Duplicate
```

**Assertions:**
- Option A: `assert mailbox1 == mailbox2, "Should return existing mailbox"`
- Option B: `# Should raise ValueError for duplicate registration`

**Success Criteria:** Duplicate registration handled appropriately

---

#### 3.2 Message Delivery

**Test:** `test_broker_deliver_message_single_recipient`

**Scenario:** Deliver message to single recipient

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Register mailboxes
sender_box = broker.register_mailbox("agent_001")
recipient_box = broker.register_mailbox("agent_002")

# Create message
message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={"data": "test"}
)

# Deliver
success = broker.deliver_message(message)
```

**Assertions:**
- `assert success == True, "Delivery should succeed"`
- `assert recipient_box.inbox.qsize() == 1, "Recipient should have 1 message"`
- Received message matches original

**Success Criteria:** Single recipient delivery works

---

**Test:** `test_broker_deliver_message_multiple_recipients`

**Scenario:** Deliver message to multiple recipients

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Register mailboxes
sender_box = broker.register_mailbox("agent_001")
recipient_box1 = broker.register_mailbox("agent_002")
recipient_box2 = broker.register_mailbox("agent_003")

# Create message
message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002", "agent_003"],
    message_type=MessageType.BROADCAST,
    subject="Test",
    body={"data": "test"}
)

# Deliver
success = broker.deliver_message(message)
```

**Assertions:**
- `assert success == True, "Delivery should succeed"`
- `assert recipient_box1.inbox.qsize() == 1, "Recipient 1 has message"`
- `assert recipient_box2.inbox.qsize() == 1, "Recipient 2 has message"`

**Success Criteria:** Multi-recipient delivery works

---

**Test:** `test_broker_deliver_to_nonexistent_recipient`

**Scenario:** Attempt delivery to unregistered agent

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

sender_box = broker.register_mailbox("agent_001")

message = Message(
    sender_id="agent_001",
    recipient_ids=["nonexistent_agent"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={}
)

success = broker.deliver_message(message)
```

**Assertions:**
- `assert success == False, "Delivery should fail"`
- Message should be logged or added to deadletter queue

**Success Criteria:** Failed delivery handled gracefully

---

#### 3.3 Pub/Sub Functionality

**Test:** `test_broker_subscribe_to_topic`

**Scenario:** Subscribe agent to topic

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

mailbox = broker.register_mailbox("agent_001")

broker.subscribe("agent_001", "task_updates")
```

**Assertions:**
- `assert "task_updates" in broker.subscriptions, "Topic registered"`
- `assert "agent_001" in broker.subscriptions["task_updates"], "Agent subscribed"`

**Success Criteria:** Subscription registered

---

**Test:** `test_broker_broadcast_to_topic`

**Scenario:** Broadcast message to all subscribers

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Register agents and subscribe
box1 = broker.register_mailbox("agent_001")
box2 = broker.register_mailbox("agent_002")
box3 = broker.register_mailbox("agent_003")

broker.subscribe("agent_001", "announcements")
broker.subscribe("agent_002", "announcements")
# agent_003 not subscribed

# Broadcast
message = Message(
    sender_id="system",
    recipient_ids=[],  # Empty for broadcast
    message_type=MessageType.BROADCAST,
    subject="System Update",
    body={"version": "2.0"}
)

broker.broadcast(message, topic="announcements")
```

**Assertions:**
- `assert box1.inbox.qsize() == 1, "Subscriber 1 received message"`
- `assert box2.inbox.qsize() == 1, "Subscriber 2 received message"`
- `assert box3.inbox.qsize() == 0, "Non-subscriber did not receive"`

**Success Criteria:** Broadcast to subscribers only

---

#### 3.4 Broker Lifecycle

**Test:** `test_broker_start_stop`

**Scenario:** Start and stop broker delivery loop

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

broker.start()
# Broker should be running

import time
time.sleep(0.5)

broker.stop()
# Broker should be stopped
```

**Assertions:**
- Broker starts without errors
- Broker stops gracefully
- No hanging threads after stop

**Success Criteria:** Lifecycle management works

---

### 4. Storage Backend Tests

**File:** `tests/unit/test_mail_storage.py`

#### 4.1 InMemoryMailStorage

**Test:** `test_in_memory_storage_save_message`

**Scenario:** Save message to in-memory storage

**Setup:**
```python
from core.mail.storage import InMemoryMailStorage

storage = InMemoryMailStorage()

message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={"data": "test"}
)

success = storage.save_message(message)
```

**Assertions:**
- `assert success == True, "Save should succeed"`
- Message can be retrieved by ID
- Message persists in storage

**Success Criteria:** Save operation works

---

**Test:** `test_in_memory_storage_get_messages`

**Scenario:** Retrieve messages for agent

**Setup:**
```python
storage = InMemoryMailStorage()

# Save multiple messages
msg1 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Message 1",
    body={}
)

msg2 = Message(
    sender_id="agent_003",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Message 2",
    body={}
)

storage.save_message(msg1)
storage.save_message(msg2)

# Retrieve for agent_002
messages = storage.get_messages(
    agent_id="agent_002",
    filters={}
)
```

**Assertions:**
- `assert len(messages) == 2, "Should retrieve 2 messages"`
- Both messages in results

**Success Criteria:** Retrieval works correctly

---

**Test:** `test_in_memory_storage_filter_messages`

**Scenario:** Filter messages by criteria

**Setup:**
```python
storage = InMemoryMailStorage()

# Save messages with different types
msg1 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Request",
    body={}
)

msg2 = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.RESPONSE,
    subject="Response",
    body={}
)

storage.save_message(msg1)
storage.save_message(msg2)

# Filter for REQUEST type only
messages = storage.get_messages(
    agent_id="agent_002",
    filters={"message_type": "request"}
)
```

**Assertions:**
- `assert len(messages) == 1, "Should retrieve 1 REQUEST message"`
- `assert messages[0].message_type == MessageType.REQUEST, "Correct type"`

**Success Criteria:** Filtering works

---

**Test:** `test_in_memory_storage_mark_delivered`

**Scenario:** Mark message as delivered

**Setup:**
```python
storage = InMemoryMailStorage()

message = Message(
    sender_id="agent_001",
    recipient_ids=["agent_002"],
    message_type=MessageType.REQUEST,
    subject="Test",
    body={}
)

storage.save_message(message)

success = storage.mark_delivered(message.message_id)
```

**Assertions:**
- `assert success == True, "Should mark as delivered"`
- Message status updated

**Success Criteria:** Delivery marking works

---

### 5. AgentRegistry Tests

**File:** `tests/unit/test_agent_registry.py`

#### 5.1 Registry Initialization

**Test:** `test_registry_creation`

**Scenario:** Create agent registry

**Setup:**
```python
from core.registry.agent_registry import AgentRegistry

registry = AgentRegistry()
```

**Assertions:**
- `assert len(registry.agents) == 0, "Should start empty"`
- `assert len(registry.capabilities_index) == 0, "Capability index empty"`

**Success Criteria:** Registry initialized

---

#### 5.2 Agent Registration

**Test:** `test_registry_register_agent`

**Scenario:** Register agent with metadata

**Setup:**
```python
from core.registry.agent_registry import AgentRegistry, AgentMetadata

registry = AgentRegistry()

metadata = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["literature_review", "data_analysis"],
    version="1.0",
    mailbox_address="mailbox_001"
)

success = registry.register(metadata)
```

**Assertions:**
- `assert success == True, "Registration should succeed"`
- `assert "agent_001" in registry.agents, "Agent registered"`
- `assert registry.agents["agent_001"] == metadata, "Metadata stored"`
- Capabilities indexed correctly

**Success Criteria:** Agent registered successfully

---

**Test:** `test_registry_register_duplicate_agent`

**Scenario:** Attempt to register same agent twice

**Setup:**
```python
registry = AgentRegistry()

metadata1 = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001"
)

metadata2 = AgentMetadata(
    agent_id="agent_001",  # Same ID
    agent_type="worker",
    capabilities=["task_b"],
    version="1.1",
    mailbox_address="mailbox_001"
)

success1 = registry.register(metadata1)
success2 = registry.register(metadata2)
```

**Assertions:**
- Option A: `assert success2 == False, "Duplicate should fail"`
- Option B: Metadata updated to latest version

**Success Criteria:** Duplicate handling works

---

**Test:** `test_registry_unregister_agent`

**Scenario:** Unregister agent

**Setup:**
```python
registry = AgentRegistry()

metadata = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001"
)

registry.register(metadata)
success = registry.unregister("agent_001")
```

**Assertions:**
- `assert success == True, "Unregistration should succeed"`
- `assert "agent_001" not in registry.agents, "Agent removed"`
- Capability index updated

**Success Criteria:** Unregistration works

---

#### 5.3 Agent Discovery

**Test:** `test_registry_discover_by_capability`

**Scenario:** Find agents with specific capability

**Setup:**
```python
registry = AgentRegistry()

# Register agents with different capabilities
agent1 = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["literature_review", "data_analysis"],
    version="1.0",
    mailbox_address="mailbox_001"
)

agent2 = AgentMetadata(
    agent_id="agent_002",
    agent_type="worker",
    capabilities=["statistics", "modeling"],
    version="1.0",
    mailbox_address="mailbox_002"
)

agent3 = AgentMetadata(
    agent_id="agent_003",
    agent_type="worker",
    capabilities=["literature_review", "statistics"],
    version="1.0",
    mailbox_address="mailbox_003"
)

registry.register(agent1)
registry.register(agent2)
registry.register(agent3)

# Discover agents with "literature_review" capability
from core.registry.metadata import AgentRequirements

requirements = AgentRequirements(
    capabilities=["literature_review"]
)

agents = registry.discover(requirements)
```

**Assertions:**
- `assert len(agents) == 2, "Should find 2 agents"`
- `assert all("literature_review" in a.capabilities for a in agents), "All have capability"`
- Agent IDs are "agent_001" and "agent_003"

**Success Criteria:** Capability-based discovery works

---

**Test:** `test_registry_discover_multiple_capabilities`

**Scenario:** Find agents with multiple capabilities (AND logic)

**Setup:**
```python
registry = AgentRegistry()

# Register agents
agent1 = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["literature_review", "statistics"],
    version="1.0",
    mailbox_address="mailbox_001"
)

agent2 = AgentMetadata(
    agent_id="agent_002",
    agent_type="worker",
    capabilities=["literature_review"],
    version="1.0",
    mailbox_address="mailbox_002"
)

registry.register(agent1)
registry.register(agent2)

# Discover agents with BOTH capabilities
requirements = AgentRequirements(
    capabilities=["literature_review", "statistics"]
)

agents = registry.discover(requirements)
```

**Assertions:**
- `assert len(agents) == 1, "Only 1 agent has both capabilities"`
- `assert agents[0].agent_id == "agent_001", "Correct agent found"`

**Success Criteria:** Multi-capability discovery works

---

**Test:** `test_registry_discover_with_capacity_filter`

**Scenario:** Find agents with available capacity

**Setup:**
```python
registry = AgentRegistry()

# Agent with capacity
agent1 = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001",
    current_load=2,
    max_concurrent_tasks=5
)

# Agent at capacity
agent2 = AgentMetadata(
    agent_id="agent_002",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_002",
    current_load=5,
    max_concurrent_tasks=5
)

registry.register(agent1)
registry.register(agent2)

# Discover with min capacity
requirements = AgentRequirements(
    capabilities=["task_a"],
    min_capacity=1  # At least 1 slot available
)

agents = registry.discover(requirements)
```

**Assertions:**
- `assert len(agents) == 1, "Only 1 agent has capacity"`
- `assert agents[0].agent_id == "agent_001", "Agent with capacity found"`

**Success Criteria:** Capacity filtering works

---

#### 5.4 Agent Status Management

**Test:** `test_registry_heartbeat`

**Scenario:** Update agent heartbeat

**Setup:**
```python
import time
from datetime import datetime

registry = AgentRegistry()

metadata = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001"
)

registry.register(metadata)

initial_heartbeat = registry.agents["agent_001"].last_heartbeat

time.sleep(0.1)

success = registry.heartbeat("agent_001")

updated_heartbeat = registry.agents["agent_001"].last_heartbeat
```

**Assertions:**
- `assert success == True, "Heartbeat should succeed"`
- `assert updated_heartbeat > initial_heartbeat, "Heartbeat updated"`

**Success Criteria:** Heartbeat tracking works

---

**Test:** `test_registry_get_status`

**Scenario:** Check agent status

**Setup:**
```python
registry = AgentRegistry()

metadata = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001",
    status=AgentStatus.ACTIVE
)

registry.register(metadata)

status = registry.get_status("agent_001")
```

**Assertions:**
- `assert status == AgentStatus.ACTIVE, "Status should be ACTIVE"`

**Success Criteria:** Status retrieval works

---

**Test:** `test_registry_prune_stale_agents`

**Scenario:** Remove agents that haven't sent heartbeat

**Setup:**
```python
import time

registry = AgentRegistry()
registry.heartbeat_timeout = 1  # 1 second timeout

metadata = AgentMetadata(
    agent_id="agent_001",
    agent_type="worker",
    capabilities=["task_a"],
    version="1.0",
    mailbox_address="mailbox_001"
)

registry.register(metadata)

# Wait for timeout
time.sleep(1.5)

# Prune stale agents
registry.prune_stale_agents()
```

**Assertions:**
- `assert "agent_001" not in registry.agents, "Stale agent removed"`

**Success Criteria:** Pruning works correctly

---

## Integration Tests

**File:** `tests/integration/test_mail_integration.py`

### 1. End-to-End Agent Messaging

**Test:** `test_agent_to_agent_messaging`

**Scenario:** Two agents exchange messages via mail system

**VALIDATION CRITERIA:**
- Agent A sends message to Agent B
- Message delivered correctly
- Agent B receives message
- Agent B sends reply
- Agent A receives reply
- Thread tracking works

**Setup:**
```python
from core.mail.broker import MailBroker
from core.mail.storage import InMemoryMailStorage
from core.registry.agent_registry import AgentRegistry, AgentMetadata

# Create infrastructure
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)
registry = AgentRegistry()

# Register agents
agent_a_box = broker.register_mailbox("agent_a")
agent_b_box = broker.register_mailbox("agent_b")

registry.register(AgentMetadata(
    agent_id="agent_a",
    agent_type="worker",
    capabilities=["task_1"],
    version="1.0",
    mailbox_address="agent_a"
))

registry.register(AgentMetadata(
    agent_id="agent_b",
    agent_type="worker",
    capabilities=["task_2"],
    version="1.0",
    mailbox_address="agent_b"
))

# Agent A sends request
request = Message(
    sender_id="agent_a",
    recipient_ids=["agent_b"],
    message_type=MessageType.REQUEST,
    subject="Need help with task",
    body={"task": "analyze_data", "data": [1, 2, 3]}
)

agent_a_box.send(request)
broker.deliver_message(request)

# Agent B receives request
received_request = agent_b_box.receive(timeout=1.0)

# Agent B sends response
response = Message(
    sender_id="agent_b",
    recipient_ids=["agent_a"],
    message_type=MessageType.RESPONSE,
    subject="Re: Need help with task",
    body={"result": "Analysis complete", "output": [4, 5, 6]},
    thread_id=received_request.message_id,
    in_reply_to=received_request.message_id
)

agent_b_box.send(response)
broker.deliver_message(response)

# Agent A receives response
received_response = agent_a_box.receive(timeout=1.0)
```

**Assertions:**
- `assert received_request is not None, "Agent B should receive request"`
- `assert received_request.sender_id == "agent_a", "Sender correct"`
- `assert received_request.body["task"] == "analyze_data", "Request data correct"`
- `assert received_response is not None, "Agent A should receive response"`
- `assert received_response.sender_id == "agent_b", "Response sender correct"`
- `assert received_response.thread_id == request.message_id, "Thread tracking works"`
- `assert received_response.body["result"] == "Analysis complete", "Response data correct"`

**Success Criteria:** Complete message exchange works end-to-end

---

### 2. Multi-Agent Broadcast

**Test:** `test_multi_agent_broadcast`

**Scenario:** Broadcast message to multiple agents via topic subscription

**VALIDATION CRITERIA:**
- Multiple agents subscribe to topic
- Broadcast message sent
- All subscribers receive message
- Non-subscribers do not receive

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Create 5 agents
agents = []
for i in range(1, 6):
    agent_id = f"agent_{i}"
    mailbox = broker.register_mailbox(agent_id)
    agents.append((agent_id, mailbox))

# Agents 1-3 subscribe to "project_updates"
for agent_id, _ in agents[:3]:
    broker.subscribe(agent_id, "project_updates")

# Agent 4 subscribes to "system_updates"
broker.subscribe("agent_4", "system_updates")

# Agent 5 doesn't subscribe to anything

# Broadcast to "project_updates"
broadcast_msg = Message(
    sender_id="coordinator",
    recipient_ids=[],
    message_type=MessageType.BROADCAST,
    subject="Project Status Update",
    body={"status": "In Progress", "completion": 45}
)

broker.broadcast(broadcast_msg, topic="project_updates")

# Check inboxes
received = []
for agent_id, mailbox in agents:
    msg = mailbox.receive(timeout=0.5)
    if msg:
        received.append(agent_id)
```

**Assertions:**
- `assert len(received) == 3, "Exactly 3 agents should receive"`
- `assert "agent_1" in received, "Subscriber 1 received"`
- `assert "agent_2" in received, "Subscriber 2 received"`
- `assert "agent_3" in received, "Subscriber 3 received"`
- `assert "agent_4" not in received, "Different topic subscriber didn't receive"`
- `assert "agent_5" not in received, "Non-subscriber didn't receive"`

**Success Criteria:** Broadcast to subscribers only

---

### 3. Registry Discovery Integration

**Test:** `test_registry_discovery_integration`

**Scenario:** Discover agents and send messages to them

**VALIDATION CRITERIA:**
- Register multiple agents with capabilities
- Discover agents by capability
- Send message to discovered agents
- All discovered agents receive message

**Setup:**
```python
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)
registry = AgentRegistry()

# Register 3 literature agents
lit_agents = []
for i in range(1, 4):
    agent_id = f"lit_agent_{i}"
    mailbox = broker.register_mailbox(agent_id)

    metadata = AgentMetadata(
        agent_id=agent_id,
        agent_type="worker",
        capabilities=["literature_review"],
        version="1.0",
        mailbox_address=agent_id
    )

    registry.register(metadata)
    lit_agents.append((agent_id, mailbox))

# Register 2 statistics agents
stats_agents = []
for i in range(1, 3):
    agent_id = f"stats_agent_{i}"
    mailbox = broker.register_mailbox(agent_id)

    metadata = AgentMetadata(
        agent_id=agent_id,
        agent_type="worker",
        capabilities=["statistics"],
        version="1.0",
        mailbox_address=agent_id
    )

    registry.register(metadata)
    stats_agents.append((agent_id, mailbox))

# Discover literature agents
from core.registry.metadata import AgentRequirements

requirements = AgentRequirements(
    capabilities=["literature_review"]
)

discovered = registry.discover(requirements)

# Send message to all discovered agents
message = Message(
    sender_id="coordinator",
    recipient_ids=[a.agent_id for a in discovered],
    message_type=MessageType.REQUEST,
    subject="Literature Review Task",
    body={"query": "ADC mechanisms"}
)

broker.deliver_message(message)

# Check that literature agents received, stats agents didn't
lit_received = 0
stats_received = 0

for agent_id, mailbox in lit_agents:
    msg = mailbox.receive(timeout=0.5)
    if msg:
        lit_received += 1

for agent_id, mailbox in stats_agents:
    msg = mailbox.receive(timeout=0.5)
    if msg:
        stats_received += 1
```

**Assertions:**
- `assert len(discovered) == 3, "Should discover 3 literature agents"`
- `assert lit_received == 3, "All literature agents received message"`
- `assert stats_received == 0, "Statistics agents didn't receive"`

**Success Criteria:** Discovery and targeted messaging works

---

### 4. End-to-End Message Flow

**Test:** `test_end_to_end_message_flow`

**Scenario:** Complete workflow from registration to message exchange

**VALIDATION CRITERIA:**
- Agents register with registry
- Agents discover each other
- Agents exchange messages
- Conversation thread maintained
- All components work together

**Setup:**
```python
# Complete setup
storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)
registry = AgentRegistry()

# Create coordinator agent
coord_box = broker.register_mailbox("coordinator")
registry.register(AgentMetadata(
    agent_id="coordinator",
    agent_type="coordinator",
    capabilities=["planning", "coordination"],
    version="1.0",
    mailbox_address="coordinator"
))

# Create worker agents
worker_boxes = {}
for i in range(1, 4):
    agent_id = f"worker_{i}"
    mailbox = broker.register_mailbox(agent_id)
    worker_boxes[agent_id] = mailbox

    registry.register(AgentMetadata(
        agent_id=agent_id,
        agent_type="worker",
        capabilities=["task_execution"],
        version="1.0",
        mailbox_address=agent_id,
        max_concurrent_tasks=5,
        current_load=0
    ))

# Workflow: Coordinator discovers workers
requirements = AgentRequirements(
    capabilities=["task_execution"],
    min_capacity=1
)

workers = registry.discover(requirements)

# Coordinator sends task to all workers
task_msg = Message(
    sender_id="coordinator",
    recipient_ids=[w.agent_id for w in workers],
    message_type=MessageType.REQUEST,
    subject="Task Assignment",
    body={"task_type": "data_processing", "priority": "high"}
)

broker.deliver_message(task_msg)

# Workers receive and respond
responses = []
for worker_id, mailbox in worker_boxes.items():
    task = mailbox.receive(timeout=1.0)
    if task:
        # Send response
        response = Message(
            sender_id=worker_id,
            recipient_ids=["coordinator"],
            message_type=MessageType.RESPONSE,
            subject="Task Accepted",
            body={"status": "accepted", "worker": worker_id},
            thread_id=task.message_id,
            in_reply_to=task.message_id
        )
        broker.deliver_message(response)
        responses.append(response)

# Coordinator receives responses
coord_responses = []
for _ in range(len(workers)):
    resp = coord_box.receive(timeout=1.0)
    if resp:
        coord_responses.append(resp)
```

**Assertions:**
- `assert len(workers) == 3, "Should discover 3 workers"`
- `assert len(responses) == 3, "All workers responded"`
- `assert len(coord_responses) == 3, "Coordinator received all responses"`
- All responses have correct thread_id
- All responses reference original message

**Success Criteria:** Complete end-to-end flow works

---

## Performance Tests

**File:** `tests/performance/test_mail_performance.py`

### 1. Message Throughput Benchmark

**Test:** `test_message_throughput`

**Scenario:** Measure messages per second

**Setup:**
```python
import time

storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Create sender and receiver
sender_box = broker.register_mailbox("sender")
receiver_box = broker.register_mailbox("receiver")

# Send 1000 messages
num_messages = 1000
start_time = time.time()

for i in range(num_messages):
    msg = Message(
        sender_id="sender",
        recipient_ids=["receiver"],
        message_type=MessageType.NOTIFICATION,
        subject=f"Message {i}",
        body={"index": i}
    )
    broker.deliver_message(msg)

end_time = time.time()
elapsed = end_time - start_time
throughput = num_messages / elapsed
```

**Success Criteria:**
- Throughput > 1000 messages/second
- No messages lost
- Memory usage stable

**Metrics to Report:**
- Messages per second
- Average latency per message
- Memory usage at start and end

---

### 2. Latency Measurements

**Test:** `test_message_latency`

**Scenario:** Measure end-to-end message delivery latency

**Setup:**
```python
import time

storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

sender_box = broker.register_mailbox("sender")
receiver_box = broker.register_mailbox("receiver")

latencies = []

for i in range(100):
    # Send message with timestamp
    send_time = time.time()

    msg = Message(
        sender_id="sender",
        recipient_ids=["receiver"],
        message_type=MessageType.REQUEST,
        subject="Latency Test",
        body={"send_time": send_time}
    )

    broker.deliver_message(msg)

    # Receive message
    received = receiver_box.receive(timeout=1.0)
    receive_time = time.time()

    if received:
        latency = receive_time - send_time
        latencies.append(latency)

# Calculate statistics
avg_latency = sum(latencies) / len(latencies)
max_latency = max(latencies)
min_latency = min(latencies)
```

**Success Criteria:**
- Average latency < 1ms for in-memory broker
- Max latency < 10ms
- 99th percentile < 5ms

**Metrics to Report:**
- Average latency
- Min/Max latency
- 50th, 95th, 99th percentiles

---

### 3. Memory Usage Under Load

**Test:** `test_memory_usage_under_load`

**Scenario:** Monitor memory usage with many agents and messages

**Setup:**
```python
import psutil
import os

process = psutil.Process(os.getpid())

# Measure initial memory
initial_memory = process.memory_info().rss / 1024 / 1024  # MB

storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Create 100 agents
for i in range(100):
    agent_id = f"agent_{i}"
    broker.register_mailbox(agent_id)

# Send 10,000 messages
for i in range(10000):
    sender = f"agent_{i % 100}"
    recipient = f"agent_{(i + 1) % 100}"

    msg = Message(
        sender_id=sender,
        recipient_ids=[recipient],
        message_type=MessageType.NOTIFICATION,
        subject=f"Message {i}",
        body={"data": "x" * 100}  # 100 bytes
    )

    broker.deliver_message(msg)

# Measure final memory
final_memory = process.memory_info().rss / 1024 / 1024  # MB
memory_increase = final_memory - initial_memory
```

**Success Criteria:**
- Memory increase < 50MB for 10k messages
- No memory leaks (memory stabilizes)
- Memory released after message consumption

**Metrics to Report:**
- Initial memory
- Final memory
- Memory per message
- Peak memory usage

---

### 4. Concurrent Agent Performance

**Test:** `test_concurrent_agent_performance`

**Scenario:** Multiple agents sending/receiving concurrently

**Setup:**
```python
import threading
import time

storage = InMemoryMailStorage()
broker = MailBroker(storage=storage)

# Create 10 agents
num_agents = 10
agents = []
for i in range(num_agents):
    agent_id = f"agent_{i}"
    mailbox = broker.register_mailbox(agent_id)
    agents.append((agent_id, mailbox))

# Each agent sends 100 messages
messages_per_agent = 100
total_messages = num_agents * messages_per_agent

def agent_task(agent_id, mailbox):
    # Send messages to random agents
    import random
    for i in range(messages_per_agent):
        recipient = random.choice([a[0] for a in agents if a[0] != agent_id])

        msg = Message(
            sender_id=agent_id,
            recipient_ids=[recipient],
            message_type=MessageType.REQUEST,
            subject=f"Message {i}",
            body={"data": i}
        )

        broker.deliver_message(msg)

# Run concurrently
start_time = time.time()

threads = []
for agent_id, mailbox in agents:
    thread = threading.Thread(target=agent_task, args=(agent_id, mailbox))
    thread.start()
    threads.append(thread)

# Wait for completion
for thread in threads:
    thread.join()

end_time = time.time()
elapsed = end_time - start_time
throughput = total_messages / elapsed
```

**Success Criteria:**
- All messages delivered successfully
- No race conditions or deadlocks
- Throughput > 500 messages/second with concurrency

**Metrics to Report:**
- Total time
- Messages per second
- Average latency
- Thread safety verified

---

## Test Utilities

**File:** `tests/utils/test_helpers.py`

### 1. Mock Agent

```python
class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.mailbox = None
        self.messages_sent = []
        self.messages_received = []

    def set_mailbox(self, mailbox):
        """Set agent's mailbox."""
        self.mailbox = mailbox

    def send_message(self, recipient_ids: List[str], subject: str, body: Dict):
        """Send message via mailbox."""
        msg = Message(
            sender_id=self.agent_id,
            recipient_ids=recipient_ids,
            message_type=MessageType.REQUEST,
            subject=subject,
            body=body
        )
        self.mailbox.send(msg)
        self.messages_sent.append(msg)
        return msg

    def receive_message(self, timeout: float = 1.0) -> Optional[Message]:
        """Receive message from mailbox."""
        msg = self.mailbox.receive(timeout=timeout)
        if msg:
            self.messages_received.append(msg)
        return msg

    def respond_to(self, original_msg: Message, response_body: Dict):
        """Send response to a message."""
        response = Message(
            sender_id=self.agent_id,
            recipient_ids=[original_msg.sender_id],
            message_type=MessageType.RESPONSE,
            subject=f"Re: {original_msg.subject}",
            body=response_body,
            thread_id=original_msg.message_id,
            in_reply_to=original_msg.message_id
        )
        self.mailbox.send(response)
        self.messages_sent.append(response)
        return response
```

### 2. Test Fixtures

```python
def create_test_broker():
    """Create test broker with in-memory storage."""
    storage = InMemoryMailStorage()
    broker = MailBroker(storage=storage)
    return broker

def create_test_registry():
    """Create test registry."""
    return AgentRegistry()

def create_test_agent(agent_id: str, capabilities: List[str]) -> Tuple[MockAgent, Mailbox]:
    """Create test agent with mailbox."""
    agent = MockAgent(agent_id, capabilities)
    broker = create_test_broker()
    mailbox = broker.register_mailbox(agent_id)
    agent.set_mailbox(mailbox)
    return agent, mailbox

def create_test_message(
    sender_id: str = "test_sender",
    recipient_ids: List[str] = None,
    message_type: MessageType = MessageType.REQUEST,
    subject: str = "Test Message",
    body: Dict = None
) -> Message:
    """Create test message with defaults."""
    if recipient_ids is None:
        recipient_ids = ["test_recipient"]
    if body is None:
        body = {"test": "data"}

    return Message(
        sender_id=sender_id,
        recipient_ids=recipient_ids,
        message_type=message_type,
        subject=subject,
        body=body
    )
```

### 3. Assertion Helpers

```python
def assert_message_delivered(mailbox: Mailbox, timeout: float = 1.0):
    """Assert that mailbox received a message."""
    msg = mailbox.receive(timeout=timeout)
    assert msg is not None, "Expected message in mailbox"
    return msg

def assert_no_message(mailbox: Mailbox, timeout: float = 0.5):
    """Assert that mailbox is empty."""
    msg = mailbox.receive(timeout=timeout)
    assert msg is None, "Expected no message in mailbox"

def assert_thread_consistent(messages: List[Message]):
    """Assert that messages belong to same thread."""
    if len(messages) <= 1:
        return

    thread_id = messages[0].message_id
    for msg in messages[1:]:
        assert msg.thread_id == thread_id, \
            f"Message {msg.message_id} not in thread {thread_id}"

def assert_message_equals(msg1: Message, msg2: Message, check_timestamp: bool = False):
    """Assert that two messages are equal."""
    assert msg1.message_id == msg2.message_id, "Message IDs don't match"
    assert msg1.sender_id == msg2.sender_id, "Sender IDs don't match"
    assert msg1.recipient_ids == msg2.recipient_ids, "Recipient IDs don't match"
    assert msg1.message_type == msg2.message_type, "Message types don't match"
    assert msg1.subject == msg2.subject, "Subjects don't match"
    assert msg1.body == msg2.body, "Bodies don't match"

    if check_timestamp:
        assert msg1.timestamp == msg2.timestamp, "Timestamps don't match"
```

### 4. Performance Utilities

```python
import time
from contextlib import contextmanager

@contextmanager
def measure_time():
    """Context manager to measure execution time."""
    start = time.time()
    yield lambda: time.time() - start

# Usage:
# with measure_time() as get_elapsed:
#     # ... code to measure ...
#     pass
# print(f"Elapsed: {get_elapsed()}")

def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile of values."""
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[index]

def format_latency(latency_seconds: float) -> str:
    """Format latency for display."""
    if latency_seconds < 0.001:
        return f"{latency_seconds * 1000000:.2f} μs"
    elif latency_seconds < 1:
        return f"{latency_seconds * 1000:.2f} ms"
    else:
        return f"{latency_seconds:.2f} s"
```

---

## Test File Structure

```
safety-research-system/
├── tests/
│   ├── __init__.py
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_message.py
│   │   ├── test_mailbox.py
│   │   ├── test_mail_broker.py
│   │   ├── test_mail_storage.py
│   │   └── test_agent_registry.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_mail_integration.py
│   │
│   ├── performance/
│   │   ├── __init__.py
│   │   └── test_mail_performance.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── test_helpers.py
│
├── test_phase1_mail.py  # Main test runner
└── PHASE_1_TEST_STRATEGY.md  # This document
```

---

## Success Criteria

### Phase 1 Must Pass

All tests must pass before Phase 1 is considered complete:

#### Unit Tests (90%+ coverage)
- ✓ All Message class tests pass (creation, validation, serialization, threading)
- ✓ All Mailbox class tests pass (send, receive, filtering, threading)
- ✓ All MailBroker tests pass (delivery, pub/sub, lifecycle)
- ✓ All Storage backend tests pass (save, retrieve, filter, mark delivered)
- ✓ All AgentRegistry tests pass (register, discover, status, heartbeat)

#### Integration Tests (80%+ coverage)
- ✓ Agent-to-agent messaging works end-to-end
- ✓ Multi-agent broadcast works correctly
- ✓ Registry discovery integration works
- ✓ Complete message flow from registration to exchange works

#### Performance Tests (Baseline metrics)
- ✓ Message throughput > 1000 msg/s
- ✓ Average latency < 1ms (in-memory)
- ✓ Memory usage < 50MB for 10k messages
- ✓ Concurrent agents work without deadlocks

#### Safety and Reliability
- ✓ No message loss (100% delivery for registered agents)
- ✓ Failed delivery to unregistered agents handled gracefully
- ✓ Thread safety verified (no race conditions)
- ✓ Memory leaks prevented
- ✓ Graceful degradation on errors

#### Documentation
- ✓ All tests self-documenting with clear descriptions
- ✓ Example usage in test code
- ✓ Performance benchmarks documented

---

## Implementation Roadmap

### Week 1: Core Components

**Day 1-2: Message and Mailbox**
- Implement Message class
- Implement MessageType, MessagePriority enums
- Write unit tests for Message
- Implement Mailbox class
- Write unit tests for Mailbox

**Day 3-4: MailBroker and Storage**
- Implement InMemoryMailStorage
- Write unit tests for Storage
- Implement MailBroker
- Write unit tests for MailBroker

**Day 5: AgentRegistry**
- Implement AgentRegistry
- Implement AgentMetadata
- Write unit tests for Registry

### Week 2: Integration and Performance

**Day 6-7: Integration Tests**
- Write agent-to-agent messaging test
- Write multi-agent broadcast test
- Write registry discovery test
- Write end-to-end flow test

**Day 8-9: Performance Tests**
- Write throughput benchmark
- Write latency measurement
- Write memory usage test
- Write concurrent agent test

**Day 10: Test Utilities and Documentation**
- Implement MockAgent
- Implement test fixtures
- Implement assertion helpers
- Document all tests
- Create test runner
- Verify 80%+ coverage

---

## Example Test Code Snippets

### Complete Unit Test Example

```python
"""
Unit tests for Message class.
"""

import logging
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.mail.message import Message, MessageType, MessagePriority
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestMessageCreation:
    """
    Test Message class creation and validation.

    VALIDATION CRITERIA:
    - Valid messages created successfully
    - Required fields enforced
    - Invalid data rejected
    - Default values applied correctly
    """

    def test_message_creation_valid(self):
        """Create valid message with all required fields."""
        logger.info("=" * 80)
        logger.info("TEST: Message Creation - Valid")
        logger.info("=" * 80)

        # Create message
        message = Message(
            sender_id="agent_001",
            recipient_ids=["agent_002", "agent_003"],
            message_type=MessageType.REQUEST,
            subject="Test Message",
            body={"content": "Hello World", "data": [1, 2, 3]}
        )

        # Validate
        assert message.message_id is not None, "Message ID should be auto-generated"
        assert isinstance(message.message_id, str), "Message ID should be string"
        assert message.sender_id == "agent_001", "Sender ID should match"
        assert len(message.recipient_ids) == 2, "Should have 2 recipients"
        assert message.recipient_ids == ["agent_002", "agent_003"], "Recipients match"
        assert message.message_type == MessageType.REQUEST, "Message type should match"
        assert message.subject == "Test Message", "Subject should match"
        assert message.body["content"] == "Hello World", "Body content should match"
        assert message.priority == MessagePriority.NORMAL, "Default priority should be NORMAL"
        assert isinstance(message.timestamp, datetime), "Timestamp should be datetime"

        logger.info(f"Created message: {message.message_id}")
        logger.info(f"  Sender: {message.sender_id}")
        logger.info(f"  Recipients: {message.recipient_ids}")
        logger.info(f"  Type: {message.message_type.value}")
        logger.info(f"  Priority: {message.priority.value}")
        logger.info("✓ TEST PASSED: Valid message creation")

    def test_message_creation_missing_required_fields(self):
        """Attempt to create message without required fields."""
        logger.info("=" * 80)
        logger.info("TEST: Message Creation - Missing Required Fields")
        logger.info("=" * 80)

        # Test missing sender_id
        try:
            message = Message(
                recipient_ids=["agent_002"],
                message_type=MessageType.REQUEST,
                subject="Test",
                body={}
            )
            assert False, "Should have raised error for missing sender_id"
        except (ValueError, TypeError) as e:
            logger.info(f"✓ Correctly rejected missing sender_id: {e}")
            assert "sender" in str(e).lower() or "required" in str(e).lower()

        # Test empty recipient list
        try:
            message = Message(
                sender_id="agent_001",
                recipient_ids=[],
                message_type=MessageType.REQUEST,
                subject="Test",
                body={}
            )
            assert False, "Should have raised error for empty recipient_ids"
        except ValueError as e:
            logger.info(f"✓ Correctly rejected empty recipient_ids: {e}")
            assert "recipient" in str(e).lower()

        logger.info("✓ TEST PASSED: Required field validation")


class TestMessageSerialization:
    """
    Test Message serialization and deserialization.

    VALIDATION CRITERIA:
    - to_dict() produces correct structure
    - from_dict() reconstructs message
    - JSON roundtrip preserves data
    """

    def test_message_json_roundtrip(self):
        """Serialize to JSON and back."""
        logger.info("=" * 80)
        logger.info("TEST: Message JSON Roundtrip")
        logger.info("=" * 80)

        import json

        # Create original message
        original = Message(
            sender_id="agent_001",
            recipient_ids=["agent_002", "agent_003"],
            message_type=MessageType.BROADCAST,
            subject="Test Broadcast",
            body={"announcement": "System update", "version": "2.0"},
            priority=MessagePriority.HIGH
        )

        logger.info(f"Original message ID: {original.message_id}")

        # Serialize to JSON
        json_str = original.to_json()
        assert json_str is not None, "JSON string should not be None"
        assert isinstance(json_str, str), "Should return string"

        logger.info(f"Serialized to JSON ({len(json_str)} bytes)")

        # Deserialize
        msg_dict = json.loads(json_str)
        restored = Message.from_dict(msg_dict)

        # Validate
        assert restored.message_id == original.message_id, "Message ID preserved"
        assert restored.sender_id == original.sender_id, "Sender ID preserved"
        assert restored.recipient_ids == original.recipient_ids, "Recipients preserved"
        assert restored.message_type == original.message_type, "Type preserved"
        assert restored.subject == original.subject, "Subject preserved"
        assert restored.body == original.body, "Body preserved"
        assert restored.priority == original.priority, "Priority preserved"

        logger.info("✓ TEST PASSED: JSON roundtrip successful")


def run_test(test_func, test_name):
    """Run a single test function."""
    try:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"RUNNING: {test_name}")
        logger.info(f"{'=' * 80}\n")
        test_func()
        logger.info(f"\n✓ PASSED: {test_name}\n")
        return True, None
    except AssertionError as e:
        logger.error(f"\n✗ FAILED: {test_name}")
        logger.error(f"AssertionError: {str(e)}\n")
        return False, str(e)
    except Exception as e:
        logger.error(f"\n✗ ERROR: {test_name}")
        logger.error(f"Exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)


def run_all_tests():
    """Run all message tests."""
    print("\n" + "=" * 80)
    print("MESSAGE CLASS TEST SUITE")
    print("=" * 80 + "\n")

    results = []

    # Creation tests
    test1 = TestMessageCreation()
    results.append(run_test(
        test1.test_message_creation_valid,
        "Message Creation - Valid"
    ))
    results.append(run_test(
        test1.test_message_creation_missing_required_fields,
        "Message Creation - Missing Required Fields"
    ))

    # Serialization tests
    test2 = TestMessageSerialization()
    results.append(run_test(
        test2.test_message_json_roundtrip,
        "Message JSON Roundtrip"
    ))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80 + "\n")

    passed = sum(1 for result, _ in results if result)
    failed = len(results) - passed

    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed/len(results)*100:.1f}%\n")

    if failed == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")

    print("=" * 80 + "\n")

    return passed == len(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
```

---

## Conclusion

This test strategy provides comprehensive coverage for Phase 1 of the multi-agent mail system. By following this plan:

1. **All components** (Message, Mailbox, MailBroker, Storage, Registry) will have thorough unit tests
2. **Integration scenarios** will validate cross-component interactions
3. **Performance baselines** will be established for optimization
4. **Test utilities** will accelerate future test development
5. **Success criteria** are clearly defined and measurable

The tests follow existing patterns from `test_full_integration.py` and `test_hybrid_audit.py`, ensuring consistency with the project's testing philosophy.

**Next Steps:**
1. Review and approve this strategy
2. Begin implementation following the roadmap
3. Run tests continuously during development
4. Achieve >80% code coverage
5. Document any deviations from this plan

**Status:** Ready for Implementation
