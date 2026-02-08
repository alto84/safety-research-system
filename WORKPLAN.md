# PSP Workplan — Visualization, Integration, Publication

## Workstream 1: Dashboard Visualizations
**Goal**: Updated architecture visualization + knowledge graph pathway visualization
- Update System Architecture tab with richer interactive dependency graph
- New "Knowledge Graph" tab (Tab 16) showing:
  - Interactive signaling pathway diagrams (CRS IL-6 cascade, ICANS BBB disruption, HLH)
  - Molecular target network with intervention points
  - Mechanism chains from therapy → AE with branching
  - Cell type interaction maps
  - Every node/edge clickable → shows PubMed reference
- API endpoints to serve knowledge graph data for visualization

## Workstream 2: Claude AI Integration (Phase 1)
**Goal**: Implement API narrative module + dashboard chat
- `src/api/claude_narratives.py` — narrative generation for risk assessments
- `POST /api/v1/chat` endpoint for dashboard chat
- Chat panel in dashboard UI (collapsible, context-aware)
- System prompts that include knowledge graph context

## Workstream 3: Code Cleanup
**Goal**: Clean imports, remove dead code, consistent formatting
- Fix any import warnings or unused variables
- Ensure all modules have proper `__init__.py`
- Consistent docstrings on public functions
- Remove any debug prints or TODO comments that are resolved

## Workstream 4: Team of Critics
**Goal**: Expert persona review with actionable feedback
- Biostatistician: Model validity, statistical rigor, CI interpretation
- Pharmacovigilance Officer: Signal detection, regulatory compliance, CIOMS format
- Clinical Physician: Clinical utility, grading accuracy, management algorithms
- Regulatory Affairs: IND readiness, DSUR format, documentation completeness
- CMC/Manufacturing: Cell therapy process considerations
- Consolidate feedback → prioritized action items → implement top fixes

## Workstream 5: gpuserver1 Publication Analysis
**Goal**: Novel risk model analysis on public data, publication-ready
- Use FAERS public data + published trial data
- Run all 7 risk models with cross-validation
- Compare autoimmune vs oncology CAR-T safety profiles
- Bayesian meta-analysis with mechanistic priors from knowledge graph
- Generate figures, tables, and statistical summaries
- All results linked to PubMed sources or knowledge graph mechanisms
- Target: draft methods + results section for publication
