# Knowledge Graph Design: Cell Therapy Pathophysiology

## Overview

The deep scientific knowledge graph encodes the mechanistic biology of cell therapy adverse events as a queryable directed graph. Every factual assertion traces to a PubMed-indexed publication. The graph connects therapy actions through signaling cascades to clinical outcomes, enabling:

1. **Mechanistic reasoning** -- Explain *why* a patient is at risk, not just *that* they are
2. **Intervention targeting** -- Identify pharmacological targets in the causal chain
3. **Biomarker interpretation** -- Provide biological rationale for biomarker changes
4. **Risk prediction improvement** -- Inform Bayesian priors with mechanistic knowledge

## Architecture

### Module Structure

```
src/data/knowledge/
    __init__.py              -- Package init with module descriptions
    references.py            -- Citation database (PubMed IDs, key findings)
    cell_types.py            -- Cell populations, activation states, AE roles
    molecular_targets.py     -- Druggable targets, modulators, pathway membership
    pathways.py              -- Signaling cascades as directed step graphs
    mechanisms.py            -- Therapy -> AE chains with branching/intervention
    graph_queries.py         -- Cross-module query API
```

### Data Flow

```
references.py  <-- Every other module references PMIDs from here
      |
cell_types.py  <-- Defines cell populations (CAR-T, monocyte, macrophage, etc.)
      |
molecular_targets.py  <-- Defines molecules (IL-6, Ang-2, STAT3, etc.)
      |
pathways.py  <-- Composes molecules + cells into signaling cascades
      |
mechanisms.py  <-- Composes pathways into full therapy -> AE chains
      |
graph_queries.py  <-- Unified query API across all modules
```

### Relationship to Existing Graph Module

The existing `src/data/graph/` module provides:
- `schema.py` -- GraphNode/GraphEdge/PathwayDefinition (generic graph primitives)
- `crs_pathways.py` -- Pre-built CRS/ICANS/HLH pathway definitions
- `knowledge_graph.py` -- In-memory graph with BFS path finding

The new `src/data/knowledge/` module extends this with:
- Therapy type-specific mechanisms (CAR-T, TCR-T, CAR-NK, TIL, gene therapy)
- Deep mechanistic detail (temporal windows, feedback loops, branching points)
- Molecular target database with druggability information
- Cell biology with activation states and secretion profiles
- Cross-module query functions for clinical reasoning

The two modules are complementary: `src/data/graph/` provides the graph engine, while `src/data/knowledge/` provides the domain content.

## How the Knowledge Graph Connects to Existing Risk Models

### Integration with Bayesian Risk Model (`bayesian_risk.py`)

The knowledge graph can improve Bayesian priors by:

1. **Mechanistic prior calibration** -- Instead of using discounted oncology rates, priors can be informed by the number of active CRS pathway steps for a given therapy type. A CAR-NK therapy with fewer CRS-contributing pathways warrants a lower prior than a CD19 CAR-T.

2. **Evidence weighting** -- Pathway confidence scores (0.0-1.0) from the knowledge graph can weight evidence contributions in the Bayesian update. Steps with higher-confidence evidence carry more weight.

3. **Therapy-specific priors** -- `mechanisms.py` provides incidence ranges by therapy type, enabling the model to use `MechanismChain.incidence_range` for therapy-specific prior specification.

### Integration with Mitigation Model (`mitigation_model.py`)

The knowledge graph directly supports mitigation modeling by:

1. **Intervention point identification** -- `get_intervention_points("CRS")` returns all steps where drugs can interrupt the cascade, with mechanism of action details
2. **Correlated mitigation** -- Pathway topology reveals which mitigations share targets (e.g., tocilizumab and siltuximab both target IL-6 signaling)
3. **Sequential intervention timing** -- Temporal windows in pathway steps inform when each intervention is most effective

### Integration with FAERS Signal Detection (`faers_signal.py`)

1. **Signal biological plausibility** -- When a new signal is detected, the knowledge graph can validate whether a mechanistic pathway exists between the therapy and the detected AE
2. **Disproportionality context** -- A high PRR for a mechanistically plausible AE is more concerning than one with no known pathway

### Integration with Biomarker Scoring (`biomarker_scores.py`)

1. **Biomarker rationale** -- `get_biomarker_rationale("CRP")` explains *why* CRP is elevated (IL-6/STAT3 hepatic acute phase response) and what level indicates risk
2. **Composite biomarker construction** -- The EASIX score rationale (endothelial dysfunction composite) is documented, including the biological basis for each component

## API Endpoints Needed

### Knowledge Graph API Routes

```
GET  /api/v1/knowledge/pathways/{ae_type}
     Returns all signaling pathways for an AE type

GET  /api/v1/knowledge/mechanisms/{therapy_type}/{ae_type}
     Returns the mechanism chain for a therapy-AE pair

GET  /api/v1/knowledge/interventions/{ae_type}
     Returns all intervention points for an AE

GET  /api/v1/knowledge/biomarker/{name}
     Returns biological rationale for a biomarker

GET  /api/v1/knowledge/molecule/{name}
     Returns all graph appearances of a molecule

GET  /api/v1/knowledge/overview/{ae_type}
     Returns comprehensive AE overview across all modules

GET  /api/v1/knowledge/references?tag={tag}
     Returns PubMed references filtered by topic tag

GET  /api/v1/knowledge/cell_types/{ae_type}
     Returns cell types involved in an AE
```

## Dashboard Visualizations

### Planned Visualizations

1. **Pathway Diagrams** -- Interactive directed graphs showing signaling cascades from therapy to AE, with nodes colored by type (cell=green, cytokine=orange, receptor=blue, AE=red) and edges weighted by confidence

2. **Mechanism Chain View** -- Horizontal timeline showing the mechanism chain steps with temporal windows, branching points (diamonds), and intervention points (hexagons with drug icons)

3. **Biomarker Waterfall** -- Upstream drivers flowing down to biomarker elevation, showing the biological logic behind each marker

4. **Intervention Map** -- Network diagram showing all druggable targets, their pathway locations, and which AEs they can prevent/treat

5. **Feedback Loop Diagrams** -- Circular pathway diagrams highlighting positive feedback loops (STAT3, NF-kB, IFN-gamma/IL-18) with amplification annotations

## Evidence Standards

### Requirements

- Every edge must have at least one PubMed ID
- Confidence weights (0.0-1.0) reflect evidence strength
- Evidence grades classify each reference (meta-analysis > RCT > prospective cohort > retrospective > case series > preclinical > review)
- Novel or low-evidence connections must be flagged

### Current Coverage

| Module | Entities | With References | Coverage |
|--------|----------|-----------------|----------|
| References | 22 papers | 22/22 | 100% |
| Cell Types | 9 types | 8/9 | 89% |
| Molecular Targets | 15 targets | 14/15 | 93% |
| Pathway Steps | 47 steps | 40/47 | 85% |
| Mechanism Steps | 39 steps | N/A (inherited) | -- |

## Future Directions

### Literature Mining (Phase 2)

- Automated PubMed search via Entrez API for new CRS/ICANS/HLH publications
- NLP extraction of molecular relationships from abstracts
- Semi-automated knowledge graph update with human review

### Automated Updates (Phase 3)

- ClinicalTrials.gov monitoring for new cell therapy trials
- FDA safety communications integration
- FAERS signal cross-referencing with graph pathways

### Extended Coverage (Phase 4)

- Autoimmune-specific CAR-T pathophysiology (SLE, myositis, SSc)
- Bispecific antibody mechanisms (overlap with CAR-T CRS but different kinetics)
- Allogeneic cell therapy GvHD pathways
- Treg therapy immunosuppression mechanisms

### Graph Database Migration (Phase 5)

- Neo4j backend (schema already supports via `knowledge_graph.py`)
- Cypher queries for complex graph traversals
- Graph neural networks for novel pathway prediction
