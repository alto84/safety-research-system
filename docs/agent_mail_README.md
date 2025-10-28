# Agent Mail System - Documentation Index

This directory contains comprehensive documentation for the **Agent Mail System** designed for the safety-research-system.

---

## Quick Start

**New to Agent Mail?** Start here:

1. Read the **Executive Summary** for high-level overview
2. Review the **Visual Diagrams** to understand message flows
3. Run the **Reference Implementation** to see it in action
4. Study the **System Design** for detailed architecture
5. Follow the **Implementation Roadmap** to build it

---

## Documentation Structure

### 1. Executive Summary
**File**: `agent_mail_executive_summary.md`

**Purpose**: High-level overview for decision makers

**Content**:
- What is Agent Mail?
- Key features and benefits
- Technical specifications
- Implementation timeline
- Cost-benefit analysis
- Recommendation

**Audience**: Technical leads, product managers, stakeholders

**Read Time**: 10 minutes

---

### 2. System Design
**File**: `agent_mail_system_design.md`

**Purpose**: Comprehensive architectural specification

**Content**:
- Component diagram
- Message format (AgentMessage dataclass)
- Transport layer (InMemory, SQLite, Hybrid)
- AgentMailbox API (send, receive, subscribe, publish)
- Integration with Agent-Audit-Resolve pattern
- Message flow examples
- Storage strategy
- Threading/concurrency model
- Testing strategy
- Performance characteristics
- Future enhancements

**Audience**: Engineers, architects

**Read Time**: 45 minutes

---

### 3. Visual Diagrams
**File**: `agent_mail_diagrams.md`

**Purpose**: Visual representation of system architecture and flows

**Content**:
- Message flow diagrams (task assignment, pub/sub, human review)
- Transport architecture diagram
- Component interaction diagrams
- Threading model diagrams
- Complete case processing timeline
- Performance comparison charts

**Audience**: All technical roles

**Read Time**: 20 minutes

---

### 4. Reference Implementation
**File**: `agent_mail_reference_implementation.py`

**Purpose**: Working code demonstrating core concepts

**Content**:
- Minimal implementation (~500 lines)
- AgentMessage dataclass
- InMemoryTransport
- AgentMailbox
- BaseAgentWithMail, WorkerAgent, AuditorAgent
- OrchestratorAgent
- 5 working demos

**Audience**: Engineers

**Usage**:
```bash
python docs/agent_mail_reference_implementation.py
```

**Run Time**: 10 seconds

---

### 5. Implementation Roadmap
**File**: `agent_mail_implementation_roadmap.md`

**Purpose**: Day-by-day implementation plan

**Content**:
- Week 1: Core infrastructure (5 days)
  - Days 1-2: Message data model & transport
  - Days 3-4: AgentMailbox hub
  - Day 5: Testing & documentation
- Week 2: Integration (5 days)
  - Days 6-7: Enhanced base classes
  - Days 8-9: Enhanced resolution engine
  - Day 10: Migration, testing & polish
- Testing strategy
- Migration plan
- Success metrics
- Risk mitigation

**Audience**: Engineers, project managers

**Read Time**: 30 minutes

---

## Quick Reference

### Key Concepts

**AgentMessage**: A message sent between agents
```python
@dataclass
class AgentMessage:
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    subject: str
    body: Dict[str, Any]
    correlation_id: Optional[str]
    # ... more fields
```

**MessageType**: Type of message
- TASK_ASSIGNMENT: Assign task to worker
- TASK_RESULT: Worker returns result
- AUDIT_REQUEST: Request audit
- AUDIT_RESULT: Auditor returns result
- STATUS_UPDATE: Status notification
- HUMAN_REVIEW: Requires human review

**AgentMailbox**: Central hub for all communication
```python
mailbox = AgentMailbox()

# Send message
mailbox.send(sender_id="A", receiver_id="B", ...)

# Receive message
message = mailbox.receive(agent_id="B", timeout=5.0)

# Publish to topic
mailbox.publish(sender_id="A", topic="events", ...)

# Subscribe to topic
mailbox.subscribe(agent_id="C", topic="events")
```

---

## Usage Examples

### Example 1: Send/Receive
```python
from core.agent_mail import AgentMailbox, MessageType

mailbox = AgentMailbox()

# Send
mailbox.send(
    sender_id="orchestrator",
    receiver_id="worker",
    message_type=MessageType.TASK_ASSIGNMENT,
    subject="Execute Task",
    body={"task_id": "123", "query": "..."}
)

# Receive
message = mailbox.receive(agent_id="worker", timeout=10.0)
print(f"Received: {message.subject}")
```

### Example 2: Pub/Sub
```python
# Subscribe
mailbox.subscribe(agent_id="dashboard", topic="task_completed")

# Publish
mailbox.publish(
    sender_id="worker",
    topic="task_completed",
    message_type=MessageType.STATUS_UPDATE,
    subject="Task completed",
    body={"task_id": "123"}
)

# Dashboard receives
message = mailbox.receive(agent_id="dashboard")
```

### Example 3: Human Review
```python
# Send message requiring review
mailbox.send(
    sender_id="auditor",
    receiver_id="orchestrator",
    message_type=MessageType.AUDIT_RESULT,
    subject="Critical issue found",
    body={"issues": [...]},
    requires_human_review=True
)

# Human reviewer checks queue
queue = mailbox.get_human_review_queue()
for msg in queue:
    if should_approve(msg):
        mailbox.approve_message(msg.message_id)
```

### Example 4: Message History
```python
# Get conversation for a case
history = mailbox.get_message_history(correlation_id="case_abc123")

for msg in history:
    print(f"{msg.created_at}: {msg.sender_id} → {msg.receiver_id}")
    print(f"  Type: {msg.message_type.value}")
    print(f"  Subject: {msg.subject}")
```

---

## Architecture at a Glance

```
Orchestrator
    │
    ├── Send TASK_ASSIGNMENT → Worker
    │                             │
    │                             ├── Execute task
    │                             │
    │   Receive TASK_RESULT ◄─────┤
    │
    ├── Send AUDIT_REQUEST → Auditor
    │                           │
    │                           ├── Validate output
    │                           │
    │   Receive AUDIT_RESULT ◄──┤
    │
    └── If FAILED:
        └── Send CORRECTION_REQUEST → Worker (retry)

All messages flow through AgentMailbox (central hub)
All messages logged in message history (audit trail)
Messages requiring review → Human Review Queue
```

---

## Technical Specifications

| Aspect | Value |
|--------|-------|
| Language | Python 3.11+ |
| Dependencies | Python stdlib only |
| Transport | Hybrid (InMemory + SQLite) |
| Latency | <10ms (in-memory) |
| Throughput | >1000 msg/sec |
| Persistence | SQLite (optional) |
| Thread Safety | Yes |
| Process Model | Single-process initially |

---

## Implementation Timeline

| Week | Focus | Deliverable |
|------|-------|-------------|
| Week 1 | Core infrastructure | Working agent mail system |
| Week 2 | Integration | Integrated with existing agents |
| Total | 10 days | Production-ready system |

---

## Benefits

### Development
- Loose coupling between agents
- Easy to test (mock messages)
- Flexible routing
- Extensible (add new message types)

### Operations
- Complete observability (message history)
- Real-time monitoring (pub/sub)
- Crash recovery (SQLite persistence)
- Human oversight (review queue)

### Safety/Compliance
- Complete audit trail
- Message traceability
- Human review workflow
- Reproducible (replay history)

---

## FAQs

**Q: Will this break existing code?**
A: No. Agent mail is opt-in via feature flags. Old code continues working.

**Q: What are the dependencies?**
A: Python stdlib only (queue, threading, sqlite3). No external packages.

**Q: How do I debug message flows?**
A: Use `mailbox.get_message_history(correlation_id)` to see complete conversation.

**Q: What if a message is lost?**
A: With SQLite persistence, messages survive crashes. Can add acknowledgments later.

**Q: Can I use this in production?**
A: After Week 2, yes. Start with feature flag disabled, then gradually enable.

**Q: How fast is it?**
A: <10ms latency, >1000 msg/sec throughput (in-memory). Comparable to direct calls.

**Q: How do I migrate existing agents?**
A: See migration plan in implementation roadmap. Gradual, non-breaking approach.

**Q: What about distributed deployment?**
A: Week 1-2 is single-process. Add Redis transport later for multi-process.

---

## Next Steps

### For Decision Makers
1. Read **Executive Summary**
2. Review cost-benefit analysis
3. Approve roadmap
4. Allocate resources

### For Engineers
1. Read **System Design**
2. Run **Reference Implementation**
3. Review **Implementation Roadmap**
4. Start Week 1 tasks

### For Project Managers
1. Review **Implementation Roadmap**
2. Set up milestones
3. Track progress
4. Monitor risks

---

## File Listing

```
docs/
├── agent_mail_README.md                        # This file (index)
├── agent_mail_executive_summary.md             # High-level overview
├── agent_mail_system_design.md                 # Detailed architecture
├── agent_mail_diagrams.md                      # Visual diagrams
├── agent_mail_reference_implementation.py      # Working demo code
└── agent_mail_implementation_roadmap.md        # Day-by-day plan
```

---

## Getting Started

### 1. Understand the System
```bash
# Read documents in order
less docs/agent_mail_executive_summary.md
less docs/agent_mail_diagrams.md
less docs/agent_mail_system_design.md
```

### 2. See It In Action
```bash
# Run the reference implementation
python docs/agent_mail_reference_implementation.py
```

### 3. Start Building
```bash
# Follow the roadmap
less docs/agent_mail_implementation_roadmap.md

# Create directory structure
mkdir -p core/agent_mail
touch core/agent_mail/__init__.py
touch core/agent_mail/message.py
touch core/agent_mail/transport.py
touch core/agent_mail/mailbox.py

# Start with Day 1-2: Message data model & transport
```

---

## Support

For questions or issues:
1. Review the design documents
2. Check the reference implementation
3. Consult the implementation roadmap
4. Reach out to the development team

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-28 | Initial design documents |

---

**Ready to implement?** Start with the **Implementation Roadmap** (Week 1, Day 1).

**Need more context?** Read the **System Design** for complete details.

**Want to see it work?** Run the **Reference Implementation**.

**Making a decision?** Review the **Executive Summary**.
