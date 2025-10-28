# Agent Mail System - Implementation Roadmap

## Overview

This document provides a concrete, week-by-week plan for implementing the agent mail system in the safety-research-system.

**Target Timeline**: 2 weeks (10 working days)
**Dependencies**: Python 3.11 stdlib only
**Risk Level**: Low (non-breaking, opt-in design)

---

## Week 1: Core Infrastructure

### Day 1-2: Message Data Model & Transport

**Goal**: Implement foundational message types and transport layer

**Files to Create**:
```
core/agent_mail/
├── __init__.py
├── message.py          # AgentMessage dataclass, enums
└── transport.py        # InMemoryTransport, SQLiteTransport, HybridTransport
```

**Tasks**:
- [ ] Create `AgentMessage` dataclass with all fields
- [ ] Define `MessageType`, `MessagePriority`, `DeliveryMode` enums
- [ ] Implement `InMemoryTransport` using `threading.Queue`
- [ ] Implement `SQLiteTransport` with schema creation
- [ ] Implement `HybridTransport` combining both
- [ ] Write unit tests for transport layer

**Test Coverage**:
- Basic send/receive
- Queue ordering by priority
- SQLite persistence
- Thread safety (concurrent send/receive)
- Message expiration

**Success Criteria**:
- Can send/receive messages between agents
- Messages persist across restarts (SQLite)
- Thread-safe with >10 concurrent senders
- Throughput >1000 msg/sec (InMemory), >100 msg/sec (SQLite)

**Estimated Time**: 16 hours

---

### Day 3-4: AgentMailbox Hub

**Goal**: Implement central coordination and routing

**Files to Create**:
```
core/agent_mail/
├── mailbox.py          # AgentMailbox central hub
├── router.py           # Message routing logic (optional separate file)
└── history.py          # Message history queries (optional separate file)
```

**Tasks**:
- [ ] Implement `AgentMailbox` singleton
- [ ] Add send/receive APIs
- [ ] Add broadcast functionality
- [ ] Add pub/sub (subscribe/publish/unsubscribe)
- [ ] Add callback registration
- [ ] Add human review queue
- [ ] Add message history storage and queries
- [ ] Implement conversation threading (correlation_id)
- [ ] Write integration tests

**Test Coverage**:
- Direct messaging
- Broadcast to all agents
- Topic-based pub/sub
- Callback notifications
- Human review queue operations
- Message history retrieval
- Conversation thread reconstruction

**Success Criteria**:
- All messaging patterns work correctly
- Pub/sub delivers to all subscribers
- Human review queue prioritizes correctly
- Message history searchable by correlation_id
- Zero message loss in normal operation

**Estimated Time**: 16 hours

---

### Day 5: Testing & Documentation

**Goal**: Comprehensive testing and usage documentation

**Files to Create**:
```
tests/
├── test_agent_mail_message.py
├── test_agent_mail_transport.py
├── test_agent_mail_mailbox.py
└── test_agent_mail_integration.py

docs/
└── agent_mail_usage_guide.md
```

**Tasks**:
- [ ] Write comprehensive unit tests (target >90% coverage)
- [ ] Write integration tests
- [ ] Write performance benchmarks
- [ ] Document all public APIs
- [ ] Create usage examples
- [ ] Create migration guide

**Test Coverage**:
- Edge cases (empty queues, timeouts, etc.)
- Error handling (malformed messages, etc.)
- Performance tests (throughput, latency)
- Concurrent access tests
- Stress tests (10K+ messages)

**Success Criteria**:
- >90% code coverage
- All tests pass
- Performance benchmarks documented
- Usage guide complete

**Estimated Time**: 8 hours

---

## Week 2: Integration with Existing Code

### Day 6-7: Enhanced Base Classes

**Goal**: Add mail support to BaseWorker and BaseAuditor

**Files to Create/Modify**:
```
agents/
├── base_worker_mail.py      # New: Mail-enabled base worker
└── base_auditor_mail.py     # New: Mail-enabled base auditor
```

**Tasks**:
- [ ] Create `BaseWorkerWithMail` extending `BaseWorker`
- [ ] Add message loop thread
- [ ] Add TASK_ASSIGNMENT handler
- [ ] Add CORRECTION_REQUEST handler
- [ ] Create `BaseAuditorWithMail` extending `BaseAuditor`
- [ ] Add AUDIT_REQUEST handler
- [ ] Write migration script to convert existing agents
- [ ] Write tests for agent communication

**Test Coverage**:
- Worker receives task assignment and returns result
- Worker handles corrections and retries
- Auditor receives audit request and returns result
- Thread safety in message handlers
- Graceful shutdown

**Success Criteria**:
- Workers/auditors can operate via mail
- Backward compatible (can still use old interface)
- Tests pass for both sync and mail modes

**Estimated Time**: 16 hours

---

### Day 8-9: Enhanced Resolution Engine

**Goal**: Add mail-based communication to ResolutionEngine

**Files to Create/Modify**:
```
core/
├── resolution_engine_mail.py    # New: Mail-enabled resolution engine
└── resolution_engine.py         # Modify: Add feature flag
```

**Tasks**:
- [ ] Create `ResolutionEngineWithMail` class
- [ ] Implement mail-based task assignment
- [ ] Implement mail-based audit requests
- [ ] Add timeout handling for worker responses
- [ ] Add timeout handling for auditor responses
- [ ] Implement correlation ID tracking
- [ ] Add human review escalation via mail
- [ ] Write integration tests

**Test Coverage**:
- Full task→audit→resolve cycle via mail
- Retry flow via CORRECTION_REQUEST
- Human review escalation
- Timeout handling
- Message correlation tracking

**Success Criteria**:
- Complete Agent-Audit-Resolve cycle works via mail
- Timeout errors handled gracefully
- Message history shows complete conversation
- Tests pass comparing sync vs mail behavior

**Estimated Time**: 16 hours

---

### Day 10: Migration, Testing & Polish

**Goal**: End-to-end testing and production readiness

**Files to Create/Modify**:
```
tests/
├── test_mail_end_to_end.py     # Full case processing test
└── test_mail_performance.py    # Performance comparison

examples/
└── example_with_agent_mail.py  # Demo script

README.md                        # Update with agent mail info
```

**Tasks**:
- [ ] Write end-to-end test processing full case
- [ ] Benchmark performance vs current implementation
- [ ] Create example script showing mail usage
- [ ] Add feature flag to enable/disable mail
- [ ] Update README with agent mail section
- [ ] Create troubleshooting guide
- [ ] Code review and polish
- [ ] Performance optimization if needed

**Test Coverage**:
- Full case with multiple tasks in parallel
- Performance comparison (sync vs mail)
- Error recovery (agent crashes, restarts)
- Message persistence and recovery

**Success Criteria**:
- Can process complete case via agent mail
- Performance comparable to sync (within 10%)
- Example script runs without errors
- Documentation complete
- Ready for opt-in deployment

**Estimated Time**: 8 hours

---

## Implementation Phases

### Phase 1: Core Only (Days 1-5)
**Deliverable**: Working agent mail system (standalone)
- Can send/receive messages
- Pub/sub works
- Human review queue works
- Message history works
- Fully tested

**Risk**: Low
**Value**: Foundation for all future work

---

### Phase 2: Integration (Days 6-9)
**Deliverable**: Agent mail integrated with existing system
- Workers/auditors support mail
- Resolution engine supports mail
- Backward compatible

**Risk**: Medium (integration complexity)
**Value**: Enables async execution, audit trail

---

### Phase 3: Production Ready (Day 10)
**Deliverable**: Production-ready with opt-in flag
- End-to-end tested
- Performance validated
- Documentation complete
- Ready to deploy

**Risk**: Low (opt-in design)
**Value**: Can gradually migrate to mail

---

## Testing Strategy

### Unit Tests
```python
tests/test_agent_mail_message.py
- test_message_creation()
- test_message_serialization()
- test_message_validation()

tests/test_agent_mail_transport.py
- test_send_receive_memory()
- test_send_receive_sqlite()
- test_queue_priority()
- test_concurrent_access()
- test_persistence()

tests/test_agent_mail_mailbox.py
- test_direct_messaging()
- test_broadcast()
- test_pub_sub()
- test_callbacks()
- test_human_review_queue()
- test_message_history()
```

### Integration Tests
```python
tests/test_agent_mail_integration.py
- test_worker_receives_task()
- test_auditor_receives_request()
- test_full_resolution_cycle()
- test_retry_with_corrections()
- test_human_review_escalation()
- test_parallel_tasks()
```

### Performance Tests
```python
tests/test_agent_mail_performance.py
- test_throughput_1000_messages()
- test_latency_percentiles()
- test_memory_usage()
- test_sqlite_overhead()
- test_parallel_vs_sequential()
```

---

## Migration Plan

### Step 1: Deploy Core (Week 1 Complete)
```python
# Add agent mail to requirements (none needed - stdlib only!)

# Initialize in main app
from core.agent_mail import AgentMailbox

mailbox = AgentMailbox()  # Available but not used yet
```

**Risk**: None (no behavior change)

---

### Step 2: Migrate One Component (Week 2, Day 6-7)
```python
# Enable mail for one worker type
from agents.base_worker_mail import BaseWorkerWithMail

class LiteratureAgentWithMail(BaseWorkerWithMail):
    def _handle_task_assignment(self, message):
        # Implementation
        pass

# Old agent still works:
lit_agent_sync = LiteratureAgent()  # No mail

# New agent uses mail:
lit_agent_mail = LiteratureAgentWithMail(
    agent_id="lit_001",
    mailbox=mailbox
)
lit_agent_mail.start()
```

**Risk**: Low (old code unchanged)

---

### Step 3: Enable Mail-Based Resolution (Week 2, Day 8-9)
```python
# Add feature flag
USE_AGENT_MAIL = os.getenv("USE_AGENT_MAIL", "false").lower() == "true"

if USE_AGENT_MAIL:
    resolution_engine = ResolutionEngineWithMail(
        task_executor=task_executor,
        audit_engine=audit_engine,
        mailbox=mailbox,
    )
else:
    resolution_engine = ResolutionEngine(
        task_executor=task_executor,
        audit_engine=audit_engine,
    )
```

**Risk**: Medium (can rollback with flag)

---

### Step 4: Full Migration (Post Week 2)
```python
# After validation, make mail default
USE_AGENT_MAIL = os.getenv("USE_AGENT_MAIL", "true").lower() == "true"

# Eventually remove flag and old code
```

**Risk**: Low (after thorough testing)

---

## Success Metrics

### Performance
- [ ] Latency: <10ms per message (in-memory)
- [ ] Throughput: >1000 msg/sec (in-memory)
- [ ] Persistence overhead: <100ms per message (SQLite)
- [ ] Parallel speedup: >1.5x vs sequential

### Reliability
- [ ] Zero message loss in normal operation
- [ ] Graceful degradation on failures
- [ ] Recovery from crashes (SQLite persistence)
- [ ] Thread-safe with >10 concurrent agents

### Usability
- [ ] Simple API (send/receive)
- [ ] Clear error messages
- [ ] Comprehensive documentation
- [ ] Easy migration path

### Quality
- [ ] >90% test coverage
- [ ] All tests pass
- [ ] No critical bugs
- [ ] Code review approved

---

## Risk Mitigation

### Risk: Performance Regression
**Mitigation**:
- Benchmark early and often
- Use HybridTransport (fast read, durable write)
- Profile and optimize hotspots
- Fall back to sync if needed

### Risk: Integration Complexity
**Mitigation**:
- Non-breaking, opt-in design
- Feature flags for gradual rollout
- Maintain backward compatibility
- Comprehensive tests comparing behaviors

### Risk: Thread Safety Issues
**Mitigation**:
- Use proven patterns (Queue, Lock)
- Stress test with concurrent access
- Code review for race conditions
- Document threading model clearly

### Risk: Message Loss
**Mitigation**:
- SQLite persistence
- Acknowledgment pattern (future)
- Dead letter queue (future)
- Comprehensive error handling

---

## Future Enhancements (Post Week 2)

### Phase 2A: Production Hardening (Weeks 3-4)
- Message acknowledgments
- Retry on delivery failure
- Dead letter queue
- Message expiration
- Monitoring dashboard

### Phase 2B: Distributed Deployment (Weeks 5-6)
- Redis transport
- Multi-process support
- Load balancing
- Agent discovery

### Phase 3: Advanced Features (Weeks 7-8)
- Message encryption
- Multi-tenancy
- Priority scheduling
- Circuit breakers

---

## Dependencies & Prerequisites

### Required
- Python 3.11+ (for better typing, performance)
- SQLite3 (included in stdlib)
- threading (included in stdlib)
- queue (included in stdlib)

### Optional
- Redis (for distributed deployment - future)
- pytest (for testing)
- pytest-cov (for coverage)

### No External Dependencies
The core agent mail system uses **only Python stdlib**, ensuring:
- Easy deployment
- No dependency conflicts
- Maximum compatibility
- Minimal security surface

---

## Rollout Strategy

### Week 1: Development
- Implement core
- Test thoroughly
- Document APIs

### Week 2: Integration
- Integrate with existing code
- Add feature flags
- End-to-end testing

### Week 3+: Deployment
- Deploy with mail disabled
- Enable for 10% of cases (canary)
- Monitor performance and errors
- Gradually increase to 50%, then 100%
- Remove old code after validation

---

## Questions & Answers

**Q: Will this break existing code?**
A: No. Agent mail is opt-in via feature flags. Old code continues working.

**Q: What if agent mail is slower?**
A: We can fall back to sync mode via feature flag. Benchmarks show comparable performance.

**Q: How do I debug message flows?**
A: Use `mailbox.get_message_history(correlation_id)` to see complete conversation.

**Q: What happens if a message is lost?**
A: With SQLite persistence, messages survive crashes. Can add acknowledgments later.

**Q: Can I use this in production?**
A: After Week 2, yes. Start with feature flag disabled, then gradually enable.

**Q: How do I monitor the system?**
A: Subscribe to message topics, check message history, add custom callbacks.

**Q: What about distributed deployment?**
A: Week 1-2 is single-process. Add Redis transport later for multi-process.

**Q: How do I test my agents with mail?**
A: See `examples/example_with_agent_mail.py` and test suite for patterns.

---

## Conclusion

This roadmap provides a clear, achievable path to implementing the agent mail system in 2 weeks. The design is:

- **Minimal**: Python stdlib only
- **Focused**: Solves core communication needs
- **Safe**: Non-breaking, opt-in migration
- **Testable**: Comprehensive test coverage
- **Extensible**: Easy to add features later

Follow this plan to add async communication, audit trails, and human oversight to your safety-research-system while maintaining stability and backward compatibility.
