"""
Knowledge graph for biological pathway data.

Provides an in-memory graph with an optional Neo4j backend. Supports pathway
loading, traversal queries, patient similarity search, and mechanism validation
used by the reasoning engine.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.data.graph.schema import (
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    PathwayDefinition,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Neo4j backend protocol (optional external dependency)
# ---------------------------------------------------------------------------

@runtime_checkable
class Neo4jDriver(Protocol):
    """Protocol for a Neo4j driver -- allows plugging in ``neo4j.Driver``
    without importing it at module level."""

    def session(self, **kwargs: Any) -> Any: ...
    def close(self) -> None: ...


@dataclass
class PathQueryResult:
    """Result of a path traversal query between two nodes.

    Attributes:
        paths: Each path is an ordered list of (node_id, edge_type, node_id) triples.
        min_hops: Shortest path length found.
        max_weight_path: The path with the highest cumulative edge weight.
    """

    paths: list[list[tuple[str, EdgeType, str]]]
    min_hops: int
    max_weight_path: list[tuple[str, EdgeType, str]]


@dataclass
class SimilarityResult:
    """Result of a patient-similarity query against the knowledge graph.

    Attributes:
        score: Jaccard similarity of activated pathway sets.
        shared_pathways: Pathway IDs active in both patients.
        unique_to_query: Pathway IDs active only in the query patient.
    """

    score: float
    shared_pathways: list[str]
    unique_to_query: list[str]


class KnowledgeGraph:
    """Biological knowledge graph for cell therapy safety.

    Stores nodes and edges in memory with adjacency-list indexing. Optionally
    syncs to a Neo4j database for persistent storage and complex Cypher queries.

    Usage::

        kg = KnowledgeGraph()
        kg.load_pathway(il6_pathway)
        result = kg.find_paths("CYTOKINE:IL6", "AE:CRS")
    """

    def __init__(self, neo4j_driver: Neo4jDriver | None = None) -> None:
        """Initialize the knowledge graph.

        Args:
            neo4j_driver: Optional Neo4j driver instance. When provided, all
                mutations are mirrored to the database.
        """
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._adj: dict[str, list[GraphEdge]] = defaultdict(list)
        self._rev_adj: dict[str, list[GraphEdge]] = defaultdict(list)
        self._type_index: dict[NodeType, set[str]] = defaultdict(set)
        self._pathway_membership: dict[str, set[str]] = defaultdict(set)
        self._neo4j: Neo4jDriver | None = neo4j_driver
        logger.info("KnowledgeGraph initialized (neo4j=%s)", neo4j_driver is not None)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph. Idempotent -- re-adding is a no-op.

        Args:
            node: The GraphNode to add.
        """
        if node.node_id in self._nodes:
            return
        self._nodes[node.node_id] = node
        self._type_index[node.node_type].add(node.node_id)

    def add_edge(self, edge: GraphEdge) -> None:
        """Add a directed edge to the graph.

        Source and target nodes must already exist; raises ``KeyError`` otherwise.

        Args:
            edge: The GraphEdge to add.

        Raises:
            KeyError: If source or target node is not in the graph.
        """
        if edge.source_id not in self._nodes:
            raise KeyError(f"Source node '{edge.source_id}' not in graph")
        if edge.target_id not in self._nodes:
            raise KeyError(f"Target node '{edge.target_id}' not in graph")
        self._edges.append(edge)
        self._adj[edge.source_id].append(edge)
        self._rev_adj[edge.target_id].append(edge)

    def load_pathway(self, pathway: PathwayDefinition) -> int:
        """Load all nodes and edges from a PathwayDefinition.

        Args:
            pathway: The pathway to load.

        Returns:
            The number of new edges added (nodes are idempotent).
        """
        for node in pathway.nodes:
            self.add_node(node)

        added = 0
        for edge in pathway.edges:
            # Skip edges whose nodes weren't in this pathway's node list
            if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
                logger.warning(
                    "Skipping edge %s->%s: node(s) missing from pathway '%s'",
                    edge.source_id, edge.target_id, pathway.pathway_id,
                )
                continue
            self.add_edge(edge)
            added += 1

            # Track pathway membership
            if edge.edge_type == EdgeType.PARTICIPATES_IN:
                self._pathway_membership[edge.target_id].add(edge.source_id)

        logger.info(
            "Loaded pathway '%s': %d nodes, %d edges",
            pathway.pathway_id, len(pathway.nodes), added,
        )

        if self._neo4j is not None:
            self._sync_pathway_to_neo4j(pathway)

        return added

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_node(self, node_id: str) -> GraphNode | None:
        """Look up a node by ID.

        Args:
            node_id: The unique node identifier.

        Returns:
            The GraphNode, or None if not found.
        """
        return self._nodes.get(node_id)

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Return all nodes of a given type.

        Args:
            node_type: The NodeType to filter on.

        Returns:
            List of matching GraphNode objects.
        """
        return [self._nodes[nid] for nid in self._type_index.get(node_type, set())]

    def get_neighbors(
        self,
        node_id: str,
        edge_types: set[EdgeType] | None = None,
        direction: str = "outgoing",
    ) -> list[tuple[GraphEdge, GraphNode]]:
        """Get neighboring nodes connected by edges of specified types.

        Args:
            node_id: The starting node.
            edge_types: Filter to these edge types. ``None`` means all.
            direction: ``'outgoing'``, ``'incoming'``, or ``'both'``.

        Returns:
            List of ``(edge, neighbor_node)`` tuples.
        """
        results: list[tuple[GraphEdge, GraphNode]] = []

        if direction in ("outgoing", "both"):
            for edge in self._adj.get(node_id, []):
                if edge_types is None or edge.edge_type in edge_types:
                    neighbor = self._nodes.get(edge.target_id)
                    if neighbor is not None:
                        results.append((edge, neighbor))

        if direction in ("incoming", "both"):
            for edge in self._rev_adj.get(node_id, []):
                if edge_types is None or edge.edge_type in edge_types:
                    neighbor = self._nodes.get(edge.source_id)
                    if neighbor is not None:
                        results.append((edge, neighbor))

        return results

    def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_hops: int = 6,
        edge_types: set[EdgeType] | None = None,
    ) -> PathQueryResult:
        """Find all simple paths between two nodes using BFS.

        Args:
            source_id: Starting node ID.
            target_id: Destination node ID.
            max_hops: Maximum path length to search.
            edge_types: Restrict traversal to these edge types.

        Returns:
            A PathQueryResult with all discovered paths.
        """
        if source_id not in self._nodes or target_id not in self._nodes:
            return PathQueryResult(paths=[], min_hops=0, max_weight_path=[])

        all_paths: list[list[tuple[str, EdgeType, str]]] = []

        # BFS with path tracking
        queue: deque[tuple[str, list[tuple[str, EdgeType, str]], set[str]]] = deque()
        queue.append((source_id, [], {source_id}))

        while queue:
            current, path, visited = queue.popleft()

            if len(path) > max_hops:
                continue

            if current == target_id and path:
                all_paths.append(path)
                continue

            for edge in self._adj.get(current, []):
                if edge_types is not None and edge.edge_type not in edge_types:
                    continue
                if edge.target_id not in visited:
                    new_visited = visited | {edge.target_id}
                    new_path = path + [(edge.source_id, edge.edge_type, edge.target_id)]
                    queue.append((edge.target_id, new_path, new_visited))

        if not all_paths:
            return PathQueryResult(paths=[], min_hops=0, max_weight_path=[])

        min_hops = min(len(p) for p in all_paths)

        # Find highest-weight path
        def _path_weight(path: list[tuple[str, EdgeType, str]]) -> float:
            total = 0.0
            for src, etype, tgt in path:
                for edge in self._adj.get(src, []):
                    if edge.target_id == tgt and edge.edge_type == etype:
                        total += edge.weight
                        break
            return total

        max_weight_path = max(all_paths, key=_path_weight)

        return PathQueryResult(
            paths=all_paths,
            min_hops=min_hops,
            max_weight_path=max_weight_path,
        )

    def get_upstream_causes(
        self,
        adverse_event_id: str,
        max_depth: int = 4,
    ) -> list[tuple[GraphNode, float]]:
        """Walk upstream from an adverse event to find causal entities.

        Traverses TRIGGERS, CAUSES, ACTIVATES, and UPSTREAM_OF edges in reverse
        to identify the mechanistic chain leading to an adverse event.

        Args:
            adverse_event_id: The adverse event node ID (e.g. ``'AE:CRS'``).
            max_depth: How many hops upstream to search.

        Returns:
            List of ``(node, cumulative_weight)`` sorted by weight descending.
        """
        causal_types = {
            EdgeType.TRIGGERS, EdgeType.CAUSES, EdgeType.ACTIVATES,
            EdgeType.UPSTREAM_OF, EdgeType.AMPLIFIES,
        }

        results: dict[str, float] = {}
        visited: set[str] = set()
        queue: deque[tuple[str, float, int]] = deque()
        queue.append((adverse_event_id, 1.0, 0))

        while queue:
            current, cumulative, depth = queue.popleft()

            if depth > max_depth:
                continue
            if current in visited:
                continue
            visited.add(current)

            if current != adverse_event_id:
                results[current] = max(results.get(current, 0.0), cumulative)

            for edge in self._rev_adj.get(current, []):
                if edge.edge_type in causal_types:
                    queue.append((edge.source_id, cumulative * edge.weight, depth + 1))

        ranked = [
            (self._nodes[nid], weight)
            for nid, weight in results.items()
            if nid in self._nodes
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def validate_mechanism(
        self,
        cause_id: str,
        effect_id: str,
        required_intermediates: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Validate that a causal mechanism exists between two entities.

        Checks whether a directed path exists and optionally whether specified
        intermediate nodes appear on at least one path.

        Args:
            cause_id: The proposed causal entity.
            effect_id: The proposed effect entity.
            required_intermediates: Node IDs that must appear on the path.

        Returns:
            Tuple of ``(is_valid, explanation)``.
        """
        result = self.find_paths(cause_id, effect_id, max_hops=6)

        if not result.paths:
            return False, f"No mechanistic path found from '{cause_id}' to '{effect_id}'"

        if required_intermediates:
            for path in result.paths:
                path_nodes = set()
                for src, _, tgt in path:
                    path_nodes.add(src)
                    path_nodes.add(tgt)
                if all(inter in path_nodes for inter in required_intermediates):
                    intermediates_str = " -> ".join(required_intermediates)
                    return True, (
                        f"Valid mechanism: {cause_id} -> {intermediates_str} -> "
                        f"{effect_id} (path length {len(path)} hops)"
                    )
            missing = [
                i for i in required_intermediates
                if not any(
                    i in {src for src, _, _ in p} | {tgt for _, _, tgt in p}
                    for p in result.paths
                )
            ]
            return False, (
                f"Path exists ({result.min_hops} hops) but missing required "
                f"intermediates: {missing}"
            )

        return True, (
            f"Valid mechanism: {result.min_hops}-hop path found "
            f"({len(result.paths)} total paths)"
        )

    def compute_patient_similarity(
        self,
        patient_cytokines_a: dict[str, float],
        patient_cytokines_b: dict[str, float],
        threshold_multiplier: float = 2.0,
    ) -> SimilarityResult:
        """Compute pathway-based similarity between two patients.

        Maps each patient's elevated cytokines to the pathways they participate
        in, then computes Jaccard similarity of the pathway sets.

        Args:
            patient_cytokines_a: Cytokine node ID -> measured value for patient A.
            patient_cytokines_b: Cytokine node ID -> measured value for patient B.
            threshold_multiplier: A cytokine is 'elevated' if its value exceeds
                this multiple of the upper normal range.

        Returns:
            SimilarityResult with score, shared pathways, and unique pathways.
        """
        def _active_pathways(cytokines: dict[str, float]) -> set[str]:
            active = set()
            for cyt_id, value in cytokines.items():
                node = self._nodes.get(cyt_id)
                if node is None:
                    continue
                normal_range = node.properties.get("normal_range_pg_ml")
                if normal_range and value > normal_range[1] * threshold_multiplier:
                    # Find pathways this cytokine participates in
                    for edge in self._adj.get(cyt_id, []):
                        if edge.edge_type == EdgeType.PARTICIPATES_IN:
                            active.add(edge.target_id)
            return active

        pathways_a = _active_pathways(patient_cytokines_a)
        pathways_b = _active_pathways(patient_cytokines_b)

        intersection = pathways_a & pathways_b
        union = pathways_a | pathways_b

        score = len(intersection) / len(union) if union else 0.0

        return SimilarityResult(
            score=score,
            shared_pathways=sorted(intersection),
            unique_to_query=sorted(pathways_a - pathways_b),
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def node_count(self) -> int:
        """Total number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Total number of edges in the graph."""
        return len(self._edges)

    def summary(self) -> dict[str, Any]:
        """Return a summary of graph contents by node and edge type.

        Returns:
            Dict with ``node_counts``, ``edge_counts``, and ``pathways``.
        """
        node_counts = {
            nt.value: len(ids) for nt, ids in self._type_index.items()
        }
        edge_counts: dict[str, int] = defaultdict(int)
        for edge in self._edges:
            edge_counts[edge.edge_type.value] += 1

        return {
            "total_nodes": self.node_count,
            "total_edges": self.edge_count,
            "node_counts": dict(node_counts),
            "edge_counts": dict(edge_counts),
            "pathways": sorted(self._pathway_membership.keys()),
        }

    # ------------------------------------------------------------------
    # Neo4j sync (private)
    # ------------------------------------------------------------------

    def _sync_pathway_to_neo4j(self, pathway: PathwayDefinition) -> None:
        """Mirror a pathway to Neo4j. Requires an active driver."""
        if self._neo4j is None:
            return

        try:
            with self._neo4j.session() as session:
                for node in pathway.nodes:
                    session.run(
                        f"MERGE (n:{node.node_type.value} {{id: $id}}) "
                        "SET n.name = $name, n += $props",
                        id=node.node_id,
                        name=node.name,
                        props=node.properties,
                    )
                for edge in pathway.edges:
                    session.run(
                        f"MATCH (a {{id: $src}}), (b {{id: $tgt}}) "
                        f"MERGE (a)-[r:{edge.edge_type.value}]->(b) "
                        "SET r.weight = $weight, r += $props",
                        src=edge.source_id,
                        tgt=edge.target_id,
                        weight=edge.weight,
                        props=edge.properties,
                    )
            logger.info("Synced pathway '%s' to Neo4j", pathway.pathway_id)
        except Exception:
            logger.exception("Failed to sync pathway '%s' to Neo4j", pathway.pathway_id)
