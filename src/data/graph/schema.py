"""
Graph schema definitions for the biological pathway knowledge graph.

Defines the node types, edge types, and data structures that represent the
mechanistic biology underlying cell therapy adverse events. The schema is
designed to capture signaling cascades from CAR-T activation through cytokine
release, endothelial activation, and organ damage.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class NodeType(enum.Enum):
    """Biological entity types represented as graph nodes."""

    GENE = "Gene"
    PROTEIN = "Protein"
    CYTOKINE = "Cytokine"
    RECEPTOR = "Receptor"
    CELL_TYPE = "Cell_Type"
    PATHWAY = "Pathway"
    ADVERSE_EVENT = "Adverse_Event"
    DRUG = "Drug"
    BIOMARKER = "Biomarker"
    ORGAN = "Organ"
    CLINICAL_SIGN = "Clinical_Sign"


class EdgeType(enum.Enum):
    """Relationship types between biological entities."""

    # Gene / protein relationships
    ENCODES = "ENCODES"                        # Gene -> Protein
    TRANSCRIBES = "TRANSCRIBES"                # Gene -> Cytokine
    REGULATES = "REGULATES"                    # Gene -> Gene

    # Signaling relationships
    ACTIVATES = "ACTIVATES"                    # Cytokine -> Receptor, Cell -> Cell
    INHIBITS = "INHIBITS"                      # Drug -> Cytokine, Protein -> Pathway
    BINDS = "BINDS"                            # Protein -> Receptor
    SECRETES = "SECRETES"                      # Cell_Type -> Cytokine
    EXPRESSES = "EXPRESSES"                    # Cell_Type -> Receptor

    # Pathway relationships
    PARTICIPATES_IN = "PARTICIPATES_IN"        # Protein -> Pathway
    TRIGGERS = "TRIGGERS"                      # Pathway -> Adverse_Event
    UPSTREAM_OF = "UPSTREAM_OF"                # Pathway -> Pathway
    DOWNSTREAM_OF = "DOWNSTREAM_OF"            # Pathway -> Pathway

    # Clinical relationships
    INDICATES = "INDICATES"                    # Biomarker -> Adverse_Event
    TREATS = "TREATS"                          # Drug -> Adverse_Event
    TARGETS = "TARGETS"                        # Drug -> Protein / Receptor
    AFFECTS = "AFFECTS"                        # Adverse_Event -> Organ
    MANIFESTS_AS = "MANIFESTS_AS"              # Adverse_Event -> Clinical_Sign

    # Mechanistic causal edges
    CAUSES = "CAUSES"                          # Generic causal
    AMPLIFIES = "AMPLIFIES"                    # Positive feedback loop edge
    PRODUCES = "PRODUCES"                      # Cell_Type -> Cytokine (in response)


class SeverityGrade(enum.IntEnum):
    """ASTCT consensus grading for CRS and ICANS (Lee et al., 2019)."""

    GRADE_0 = 0
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3
    GRADE_4 = 4
    GRADE_5 = 5  # Fatal


class TemporalPhase(enum.Enum):
    """Temporal phases of cell therapy adverse events."""

    PRE_INFUSION = "pre_infusion"
    EARLY_ONSET = "early_onset"          # 0-24 hours
    PEAK_PHASE = "peak_phase"            # 1-7 days
    RESOLUTION = "resolution"            # 7-14 days
    LATE_ONSET = "late_onset"            # >14 days


@dataclass(frozen=True)
class GraphNode:
    """A node in the biological knowledge graph.

    Attributes:
        node_id: Unique identifier (e.g., 'CYTOKINE:IL6', 'GENE:IL6').
        node_type: The biological entity type.
        name: Human-readable name.
        properties: Arbitrary metadata (ontology IDs, reference ranges, etc.).
    """

    node_id: str
    node_type: NodeType
    name: str
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must be a non-empty string")
        if not isinstance(self.node_type, NodeType):
            raise TypeError(f"node_type must be NodeType, got {type(self.node_type)}")


@dataclass(frozen=True)
class GraphEdge:
    """A directed edge in the biological knowledge graph.

    Attributes:
        source_id: Node ID of the source node.
        target_id: Node ID of the target node.
        edge_type: The relationship type.
        weight: Confidence or strength of the relationship (0.0 - 1.0).
        properties: Arbitrary metadata (publication references, evidence level, etc.).
    """

    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight must be between 0.0 and 1.0, got {self.weight}")


@dataclass
class PathwayDefinition:
    """A named biological pathway with its constituent nodes and edges.

    Pathways represent mechanistic cascades (e.g., IL-6 signaling, endothelial
    activation) that can be loaded into the knowledge graph and queried for
    mechanism validation.

    Attributes:
        pathway_id: Unique identifier for the pathway.
        name: Human-readable pathway name.
        description: Detailed description of the pathway's biological role.
        nodes: All nodes participating in this pathway.
        edges: All edges defining the pathway's signaling cascade.
        temporal_phase: When this pathway is typically active post-infusion.
        adverse_events: Adverse events this pathway can trigger.
    """

    pathway_id: str
    name: str
    description: str
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    temporal_phase: TemporalPhase = TemporalPhase.PEAK_PHASE
    adverse_events: list[str] = field(default_factory=list)
