# Safety Research System: Deep Code Review, UI Plan & Multi-Claude Collaboration Strategy

## Part 1: Codebase Overview

### What This System Is

A **pharmaceutical safety research platform** (~11K lines of Python) implementing a novel **Agent-Audit-Resolve** pattern. It orchestrates specialized AI agents to conduct evidence-based safety assessments (literature reviews, statistical analyses, mechanistic inference) with mandatory quality validation and anti-fabrication controls.

**Flagship demonstration**: A 19,139-word publication-ready manuscript on ADC-induced Interstitial Lung Disease with 165 verified references.

### Architecture Summary

```
                          ┌─────────────────────┐
                          │    ORCHESTRATOR      │
                          │  (compressed views   │
                          │   only - 2-3 lines   │
                          │   per task result)    │
                          └──────────┬───────────┘
                                     │ decompose case → tasks
                    ┌────────────────┼────────────────┐
                    ▼                ▼                 ▼
              ┌──────────┐   ┌──────────┐      ┌──────────┐
              │  Task 1   │   │  Task 2   │      │  Task N   │
              │ LIT_REVIEW│   │ STATS     │      │ MECHANISM │
              └────┬──────┘   └────┬──────┘      └────┬──────┘
                   │               │                   │
          ┌────────▼────────────────▼───────────────────▼──────┐
          │              RESOLUTION ENGINE                      │
          │   ┌──────────────────────────────────────────┐     │
          │   │  1. TASK EXECUTOR → Worker Agent          │     │
          │   │  2. AUDIT ENGINE  → Auditor Agent         │     │
          │   │  3. Decision:                             │     │
          │   │     PASS → CONTEXT COMPRESSOR → return    │     │
          │   │     FAIL → extract corrections → RETRY    │     │
          │   │     CRITICAL → ESCALATE to human          │     │
          │   └──────────────────────────────────────────┘     │
          └────────────────────────────────────────────────────┘
```

### Module Map

| Module | Files | Lines | Purpose |
|--------|-------|-------|---------|
| `models/` | 4 | ~1,000 | Data types: Task, Case, Evidence, AuditResult |
| `core/` | 7 | ~3,800 | Engines: LLM integration, task execution, audit, resolution, compression, confidence |
| `agents/` | 9 | ~3,500 | Orchestrator, base classes, workers (literature, stats, ADC/ILD), auditors (literature, stats), PubMed connector |
| `guidelines/` | 2 | ~300 | Audit checklists for literature and statistics validation |
| `tests` | 2 | ~1,700 | Integration tests: end-to-end research validation, hybrid audit system |

### Key Design Decisions

1. **Context Compression**: Orchestrator never sees full outputs - only 2-3 sentence summaries (80-95% reduction). This prevents context window overload in multi-task cases.

2. **Hybrid Validation**: Two-layer audit system:
   - **Layer 1** (hard-coded): Score fabrication, banned phrases, missing evidence - *cannot be overridden*
   - **Layer 2** (LLM-powered): Semantic violation detection, evidence-claim linkage - *gracefully degrades if API unavailable*

3. **Thought Pipes**: LLM reasoning replaces brittle conditional logic for agent routing, evidence assessment, conflict resolution, and compression.

4. **Evidence Provenance**: Every claim traces to verified sources via `EvidenceChain → EvidenceClaim → Source` hierarchy with PMID/DOI/URL verification.

5. **Anti-Fabrication**: Detects fake PMIDs (sequential patterns like "12345678"), placeholder titles/authors, scores >80% without external validation, and banned superlative language.

---

## Part 2: UI Feasibility Assessment

### What's Possible Right Now

The codebase is a **pure Python library with no web layer**. There are no HTTP endpoints, no frontend assets, no CLI interface. However, the architecture is well-structured with clean data models and separation of concerns, which makes it highly amenable to a UI layer.

### Proposed UI Architecture: Terminal + Web Hybrid

#### Option A: Rich Terminal UI (Textual/Rich) - Fastest to Implement

```
┌──────────────────────────────────────────────────────────┐
│  SAFETY RESEARCH SYSTEM                    [Cases] [Log] │
├──────────────┬───────────────────────────────────────────┤
│ CASES        │  CASE: ADC-ILD Safety Assessment          │
│              │  Status: IN_PROGRESS  Priority: HIGH      │
│ ▸ ADC-ILD    │                                           │
│   Safety     │  TASKS                                    │
│              │  ┌─────────────────────────────────────┐  │
│ ▸ Drug-X     │  │ ✓ Literature Review    PASSED       │  │
│   Cardiac    │  │   15 sources, confidence: moderate  │  │
│              │  │ ⟳ Statistical Analysis  AUDITING    │  │
│ ▸ Combo-Y    │  │   Retry 1/2: missing CI data       │  │
│   Hepato     │  │ ○ Mechanistic Inference PENDING     │  │
│              │  └─────────────────────────────────────┘  │
│              │                                           │
│              │  AUDIT LOG                                │
│              │  12:01 LitAuditor: PASS (0 critical)     │
│              │  12:03 StatsAuditor: FAIL (1 critical)   │
│              │  12:03 → Correction: add confidence int. │
│              │  12:05 StatsAgent: retrying with fixes    │
│              │                                           │
│              │  EVIDENCE CHAIN                           │
│              │  ▸ Claim: "ILD incidence 10-15%"         │
│              │    Source: PMID 38238097 ✓ verified       │
│              │    Confidence: HIGH (score: 78.5)         │
├──────────────┴───────────────────────────────────────────┤
│ > Submit new case: _                                     │
└──────────────────────────────────────────────────────────┘
```

**Tech**: Python `textual` library (already fits the pure-Python ecosystem)
- Real-time task status updates
- Drill-down into audit results
- Evidence chain browser
- Case submission form
- ~500-800 lines of code to implement

#### Option B: Web Dashboard (FastAPI + HTMX) - Most Interactive

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser: http://localhost:8000                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐  ┌──────────────────────────────────────────────┐  │
│  │ Sidebar  │  │  Pipeline Visualization                      │  │
│  │          │  │                                              │  │
│  │ Cases    │  │  [Worker] ──→ [Auditor] ──→ [Compressor]   │  │
│  │ --------│  │     ↑              │                          │  │
│  │ ADC-ILD │  │     └── RETRY ←────┘                         │  │
│  │ Drug-X  │  │                                              │  │
│  │ Combo-Y │  │  Live task status, audit issues, evidence    │  │
│  │          │  │  traces, confidence scores, compression      │  │
│  │ Agents   │  │  ratios - all updating in real-time via SSE │  │
│  │ --------│  │                                              │  │
│  │ LitAgent │  └──────────────────────────────────────────────┘  │
│  │ StatsAg  │                                                    │
│  │ ADCResrc │  ┌──────────────────────────────────────────────┐  │
│  │          │  │  Confidence Calibration Dashboard             │  │
│  │ Config   │  │                                              │  │
│  │ --------│  │  Source Quality: ████████░░ 85/100            │  │
│  │ Audits   │  │  Source Count:  ██████░░░░ 75/100            │  │
│  │ Evidence │  │  Recency:       ████████░░ 80/100            │  │
│  │ Reports  │  │  Sample Size:   ███████░░░ 70/100            │  │
│  │          │  │  Overall:       MODERATE (78.5)              │  │
│  └─────────┘  └──────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tech**: FastAPI + HTMX + Jinja2 templates (minimal JS, server-rendered)
- REST API wrapping existing Python classes
- Server-Sent Events for real-time updates
- HTMX for interactive drill-down without heavy JS frameworks
- ~1,500-2,500 lines of code to implement

#### Option C: Full React/Next.js SPA - Most Powerful but Heaviest

**Best for**: If this becomes a team tool with multiple concurrent users, role-based access, or needs rich interactive visualizations (evidence graph networks, audit timelines).

**Estimate**: ~4,000-6,000 lines across API + frontend. Heavier investment.

### My Recommendation: Option B (FastAPI + HTMX)

Reasons:
1. FastAPI naturally wraps the existing Python class interfaces
2. HTMX gives rich interactivity without a JS build toolchain
3. Server-Sent Events fit the async task execution model perfectly
4. The audit/resolution loop is inherently visual and benefits from a dashboard
5. Minimal new dependencies (fastapi, uvicorn, jinja2, htmx via CDN)

### UI Components I Would Build

| Component | What It Shows | Interaction |
|-----------|---------------|-------------|
| **Case Dashboard** | All cases with status, priority, task counts | Create new case, filter, sort |
| **Task Pipeline View** | Visual Worker→Audit→Resolve flow per task | Click to drill into any stage |
| **Audit Inspector** | Issues list with severity, category, suggested fixes | Filter by severity, expand details |
| **Evidence Browser** | Claims → Sources hierarchy with verification status | Click claim to see source chain |
| **Confidence Dashboard** | Calibration scores with component breakdown | Hover for scoring explanation |
| **Compression Monitor** | Before/after sizes, compression ratios | Toggle between compressed/full view |
| **Agent Status Panel** | Which agents are active, task queues, retry counts | Monitor agent utilization |
| **Report Viewer** | Final synthesized report in rendered markdown | Export to PDF/Word |

### Implementation Plan for UI

```
Phase 1: API Layer (~400 lines)
  - FastAPI app wrapping Orchestrator, ResolutionEngine, AuditEngine
  - Endpoints: /cases, /cases/{id}/tasks, /tasks/{id}/audit, /evidence
  - WebSocket/SSE for live task updates

Phase 2: Core Dashboard (~600 lines)
  - Case list + detail views
  - Task pipeline visualization
  - Audit result inspector

Phase 3: Evidence & Confidence (~500 lines)
  - Evidence chain browser
  - Confidence calibration dashboard
  - Source verification status

Phase 4: Interactive Features (~400 lines)
  - New case submission form
  - Manual audit trigger
  - Report export
  - Agent configuration panel
```

---

## Part 3: Multi-Claude Code Collaboration Strategy

### The Vision

Multiple Claude Code instances running on your desktop, each specializing in different aspects of this system, coordinating through shared artifacts.

### Collaboration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR DESKTOP                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Claude Code   │  │ Claude Code   │  │ Claude Code   │      │
│  │ Instance A    │  │ Instance B    │  │ Instance C    │      │
│  │               │  │               │  │               │      │
│  │ ROLE:         │  │ ROLE:         │  │ ROLE:         │      │
│  │ Core Engine   │  │ UI/Frontend   │  │ Testing &     │      │
│  │ Development   │  │ Development   │  │ Quality       │      │
│  │               │  │               │  │               │      │
│  │ Works on:     │  │ Works on:     │  │ Works on:     │      │
│  │ - core/       │  │ - ui/         │  │ - tests/      │      │
│  │ - models/     │  │ - templates/  │  │ - guidelines/ │      │
│  │ - agents/     │  │ - static/     │  │ - CI/CD       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                  │
│                   ┌────────▼────────┐                         │
│                   │  SHARED GIT REPO │                         │
│                   │  (coordination   │                         │
│                   │   point)         │                         │
│                   └─────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Coordination Mechanisms

#### 1. Git Branch Strategy (Primary Coordination)

```
main
 ├── claude/core-engine-improvements
 ├── claude/ui-dashboard-build
 ├── claude/test-coverage-expansion
 └── claude/agent-new-worker-type
```

Each Claude Code instance works on its own branch. PRs are the integration point.

#### 2. Shared Interface Contracts (`.contracts/` directory)

Create interface definition files that all instances reference:

```python
# .contracts/api_contract.py
"""
Interface contract between core engine and UI layer.
Both Claude instances reference this file.
"""

class CaseAPI:
    """UI instance calls these; Core instance implements these."""
    def get_case(case_id: str) -> CaseResponse: ...
    def create_case(request: CreateCaseRequest) -> CaseResponse: ...
    def get_task_status(task_id: str) -> TaskStatusResponse: ...
    def get_audit_result(task_id: str) -> AuditResultResponse: ...
    def get_evidence_chain(chain_id: str) -> EvidenceChainResponse: ...

class EventStream:
    """Real-time events from core to UI."""
    def subscribe(case_id: str) -> AsyncIterator[Event]: ...
```

#### 3. Task Coordination File (`.claude-tasks.md`)

A shared markdown file in the repo that Claude instances read/write:

```markdown
# Active Claude Code Tasks

## Instance A (Core Engine)
- [x] Add WebSocket event emission to ResolutionEngine
- [ ] Implement CaseAPI contract in FastAPI
- [ ] Add async task execution support

## Instance B (UI)
- [x] Scaffold FastAPI + HTMX project structure
- [ ] Build case dashboard (waiting on: Instance A CaseAPI)
- [ ] Build audit inspector component

## Instance C (Testing)
- [x] Expand unit test coverage for models/
- [ ] Add API integration tests
- [ ] Performance benchmark suite

## Blockers
- Instance B blocked on Instance A: need CaseAPI endpoints before dashboard
```

#### 4. Specific Collaboration Scenarios

**Scenario 1: Building the UI (Parallel Development)**

| Instance A (Backend) | Instance B (Frontend) | Instance C (Quality) |
|---|---|---|
| Add FastAPI endpoints wrapping `Orchestrator` | Build HTMX templates consuming API endpoints | Write API contract tests |
| Implement SSE for live task updates | Build real-time task status UI | Write end-to-end test scenarios |
| Add async task execution | Build evidence chain browser | Performance-test the pipeline |
| Implement report export API | Build report viewer with markdown rendering | Validate audit checklist compliance |

**Scenario 2: Adding a New Agent Type (Sequential + Parallel)**

| Phase | Instance A | Instance B | Instance C |
|---|---|---|---|
| 1. Design | Write `BaseWorker` subclass skeleton | -- | Write test cases for new agent |
| 2. Implement | Build agent logic + PubMed integration | Add agent to UI agent panel | Run tests, report failures |
| 3. Audit | Build matching `BaseAuditor` subclass | Add audit results to UI inspector | Validate audit catches known-bad data |
| 4. Integrate | Register in `TaskExecutor` routing | Update dashboard to show new task type | Integration test full pipeline |

**Scenario 3: Refactoring (Coordinated)**

| Step | Who | What |
|---|---|---|
| 1 | Instance C | Run full test suite, establish baseline coverage |
| 2 | Instance A | Refactor core/ modules (e.g., extract event system) |
| 3 | Instance C | Run tests after each refactor step, report regressions |
| 4 | Instance B | Update UI to use new interfaces |
| 5 | Instance C | Final validation pass |

### How Claude Code Instances Actually Coordinate on Desktop

1. **Separate Terminal Windows**: Each instance runs in its own terminal, working on its own branch
2. **Git as Message Bus**: Commits and branch state are the communication medium
3. **You as Orchestrator**: You tell each instance what the others are doing and what contracts to follow
4. **Shared Files**: `.contracts/`, `.claude-tasks.md`, and interface files serve as coordination artifacts
5. **PR Reviews**: One instance can review another's PR using `gh pr view` and provide feedback

### Practical Example Session

```
Terminal 1 (You → Claude A):
  "Build a FastAPI API layer for the Orchestrator, ResolutionEngine, and
   AuditEngine. Follow the contract in .contracts/api_contract.py.
   Work on branch claude/api-layer."

Terminal 2 (You → Claude B):
  "Build HTMX templates for the case dashboard and task pipeline view.
   The API will be at localhost:8000. Use the endpoints defined in
   .contracts/api_contract.py. Work on branch claude/ui-dashboard."

Terminal 3 (You → Claude C):
  "Write comprehensive tests for the API endpoints defined in
   .contracts/api_contract.py. Also test that the UI templates
   render correctly with sample data. Work on branch claude/test-suite."
```

---

## Part 4: What I Can Build Right Now

Given my current session, here's what I can implement immediately:

### Tier 1: Build Now (This Session)
- [ ] FastAPI application scaffold with core API endpoints
- [ ] API wrapper for `Orchestrator.process_case()`
- [ ] REST endpoints for case/task/audit/evidence data
- [ ] SSE endpoint for live task status updates
- [ ] Basic HTMX dashboard template (case list + task view)
- [ ] Interface contract files for multi-Claude coordination

### Tier 2: Next Session
- [ ] Full task pipeline visualization
- [ ] Audit inspector with issue drill-down
- [ ] Evidence chain browser
- [ ] Confidence calibration dashboard
- [ ] Report viewer with markdown rendering

### Tier 3: With Multi-Claude Team
- [ ] Real-time WebSocket updates
- [ ] Agent configuration panel
- [ ] Historical analysis views
- [ ] Export to PDF/DOCX
- [ ] User authentication for team use
- [ ] Experiment comparison views

---

## Appendix: File-by-File Summary

### Models (`models/`)
| File | Key Classes | Purpose |
|------|-------------|---------|
| `task.py` | `Task`, `TaskType`, `TaskStatus` | Work units with 8-state lifecycle |
| `case.py` | `Case`, `CaseStatus`, `CasePriority` | Safety research requests |
| `evidence.py` | `Source`, `EvidenceClaim`, `EvidenceChain` | Full provenance tracking |
| `audit_result.py` | `AuditResult`, `ValidationIssue`, `IssueSeverity` | Structured audit findings |

### Core Engines (`core/`)
| File | Key Classes | Purpose |
|------|-------------|---------|
| `llm_integration.py` | `ThoughtPipeExecutor`, `CLAUDEMDComplianceChecker` | LLM reasoning + safety validation |
| `task_executor.py` | `TaskExecutor` | Routes tasks to appropriate worker agents |
| `audit_engine.py` | `AuditEngine` | Orchestrates validation of worker outputs |
| `resolution_engine.py` | `ResolutionEngine`, `ResolutionDecision` | Worker→Audit→Retry loop |
| `context_compressor.py` | `ContextCompressor` | 80-95% output compression |
| `confidence_calibrator.py` | `ConfidenceCalibrator` | Evidence-based confidence scoring |
| `confidence_validator.py` | `ConfidenceValidator` | Validates confidence matches evidence |

### Agents (`agents/`)
| File | Key Classes | Purpose |
|------|-------------|---------|
| `orchestrator.py` | `Orchestrator` | Case decomposition + synthesis |
| `base_worker.py` | `BaseWorker` (abstract) | Worker agent interface |
| `base_auditor.py` | `BaseAuditor` (abstract) | Auditor agent interface with hybrid validation |
| `workers/literature_agent.py` | `LiteratureAgent` | PubMed-powered literature reviews |
| `workers/statistics_agent.py` | `StatisticsAgent` | Statistical analysis |
| `workers/adc_ild_researcher.py` | `ADCILDResearcher` | Specialized ADC/ILD research |
| `auditors/literature_auditor.py` | `LiteratureAuditor` | Literature quality validation |
| `auditors/statistics_auditor.py` | `StatisticsAuditor` | Statistics quality validation |
| `data_sources/pubmed_connector.py` | `PubMedConnector` | NCBI E-utilities API integration |

### Current Gaps (No Implementation Yet)
- No web server or HTTP endpoints
- No CLI interface (`argparse`, `click`, `typer`)
- No Docker/containerization
- No CI/CD pipeline
- No environment configuration (`.env`)
- No async execution (synchronous only)
- No database (in-memory only)
- No user authentication
