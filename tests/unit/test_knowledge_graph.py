"""
Tests for KnowledgeGraph — pathway queries, mechanism validation, and
graph traversal for CRS/ICANS/HLH pathways.

The KnowledgeGraph is the institutional memory of the platform, encoding biological
mechanisms, validated hypotheses, and observed relationships.
"""

import pytest
from dataclasses import dataclass, field
from typing import Optional

from tests.conftest import KGNode, KGEdge


# ---------------------------------------------------------------------------
# KnowledgeGraph reference implementation (in-memory for testing)
# ---------------------------------------------------------------------------

class KnowledgeGraph:
    """In-memory knowledge graph for testing platform pathway queries.

    Production implementation uses Neo4j with Cypher queries. This in-memory
    version mirrors the same interface for unit testing.
    """

    def __init__(self):
        self._nodes: dict[str, KGNode] = {}
        self._edges: list[KGEdge] = []
        self._adjacency: dict[str, list[KGEdge]] = {}  # source_id -> edges

    def add_node(self, node: KGNode):
        """Add a node to the graph."""
        self._nodes[node.node_id] = node

    def add_edge(self, edge: KGEdge):
        """Add a directed edge to the graph."""
        if edge.source_id not in self._nodes:
            raise ValueError(f"Source node {edge.source_id} not in graph.")
        if edge.target_id not in self._nodes:
            raise ValueError(f"Target node {edge.target_id} not in graph.")
        self._edges.append(edge)
        self._adjacency.setdefault(edge.source_id, []).append(edge)

    def get_node(self, node_id: str) -> Optional[KGNode]:
        """Retrieve a node by ID."""
        return self._nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> list[KGEdge]:
        """Get all outgoing edges from a node."""
        return self._adjacency.get(node_id, [])

    def get_edges_by_type(self, edge_type: str) -> list[KGEdge]:
        """Get all edges of a given type."""
        return [e for e in self._edges if e.edge_type == edge_type]

    def find_path(self, start_id: str, end_id: str, max_depth: int = 10) -> list[str]:
        """BFS to find shortest path between two nodes. Returns list of node IDs."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return []
        if start_id == end_id:
            return [start_id]

        visited = {start_id}
        queue = [(start_id, [start_id])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                break
            for edge in self.get_edges_from(current):
                if edge.target_id == end_id:
                    return path + [end_id]
                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    queue.append((edge.target_id, path + [edge.target_id]))

        return []  # No path found

    def find_relevant_pathways(self, start_id: str, target_type: str = "Adverse_Event") -> list[list[str]]:
        """Find all paths from start_id to any node of target_type, up to depth 10."""
        paths = []
        target_ids = [nid for nid, n in self._nodes.items() if n.node_type == target_type]
        for tid in target_ids:
            path = self.find_path(start_id, tid)
            if path:
                paths.append(path)
        return paths

    def validate_mechanism(self, pathway: list[str]) -> dict:
        """Validate that a proposed mechanistic pathway is supported by graph edges.

        Returns a dict with:
            valid: bool -- whether all edges exist
            missing_edges: list -- edges not found in graph
            total_evidence: int -- sum of evidence_count on valid edges
        """
        missing = []
        evidence_total = 0

        for i in range(len(pathway) - 1):
            src, tgt = pathway[i], pathway[i + 1]
            # Find any edge between src and tgt
            edges_from_src = self.get_edges_from(src)
            found = [e for e in edges_from_src if e.target_id == tgt]
            if not found:
                missing.append((src, tgt))
            else:
                ev_count = found[0].properties.get("evidence_count", 0)
                evidence_total += ev_count

        return {
            "valid": len(missing) == 0,
            "missing_edges": missing,
            "total_evidence": evidence_total,
        }

    def get_correlating_biomarkers(self, adverse_event_id: str) -> list[tuple[str, float]]:
        """Get biomarkers that correlate with an adverse event, sorted by correlation."""
        results = []
        for edge in self._edges:
            if edge.target_id == adverse_event_id and edge.edge_type == "CORRELATES_WITH":
                corr = edge.properties.get("correlation", 0.0)
                results.append((edge.source_id, corr))
        return sorted(results, key=lambda x: x[1], reverse=True)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return len(self._edges)


# ===========================================================================
# Tests
# ===========================================================================

@pytest.fixture
def empty_graph():
    return KnowledgeGraph()


@pytest.fixture
def crs_graph(crs_pathway_nodes, crs_pathway_edges):
    """A knowledge graph populated with the CRS pathway."""
    kg = KnowledgeGraph()
    for node in crs_pathway_nodes:
        kg.add_node(node)
    for edge in crs_pathway_edges:
        kg.add_edge(edge)
    return kg


class TestGraphConstruction:
    """Tests for adding nodes and edges."""

    def test_add_node(self, empty_graph):
        node = KGNode("test_node", "Cytokine", {"name": "Test"})
        empty_graph.add_node(node)
        assert empty_graph.node_count == 1

    def test_add_edge_valid(self, empty_graph):
        empty_graph.add_node(KGNode("a", "Protein"))
        empty_graph.add_node(KGNode("b", "Pathway"))
        empty_graph.add_edge(KGEdge("a", "b", "ACTIVATES"))
        assert empty_graph.edge_count == 1

    def test_add_edge_missing_source_raises(self, empty_graph):
        empty_graph.add_node(KGNode("b", "Pathway"))
        with pytest.raises(ValueError, match="Source node"):
            empty_graph.add_edge(KGEdge("missing", "b", "ACTIVATES"))

    def test_add_edge_missing_target_raises(self, empty_graph):
        empty_graph.add_node(KGNode("a", "Protein"))
        with pytest.raises(ValueError, match="Target node"):
            empty_graph.add_edge(KGEdge("a", "missing", "ACTIVATES"))

    def test_crs_graph_populated(self, crs_graph, crs_pathway_nodes, crs_pathway_edges):
        assert crs_graph.node_count == len(crs_pathway_nodes)
        assert crs_graph.edge_count == len(crs_pathway_edges)


class TestNodeRetrieval:
    """Tests for node lookup."""

    def test_get_existing_node(self, crs_graph):
        node = crs_graph.get_node("node:il6")
        assert node is not None
        assert node.node_type == "Cytokine"
        assert node.properties["name"] == "IL-6"

    def test_get_nonexistent_node_returns_none(self, crs_graph):
        assert crs_graph.get_node("node:does_not_exist") is None

    def test_adverse_event_nodes_have_meddra(self, crs_graph):
        crs_node = crs_graph.get_node("node:crs")
        assert crs_node is not None
        assert "meddra_term" in crs_node.properties
        assert crs_node.properties["meddra_term"] == "Cytokine release syndrome"


class TestEdgeQueries:
    """Tests for edge-based queries."""

    def test_get_edges_from_node(self, crs_graph):
        edges = crs_graph.get_edges_from("node:il6")
        assert len(edges) > 0
        target_ids = [e.target_id for e in edges]
        assert "node:sil6r" in target_ids

    def test_get_edges_from_leaf_node(self, crs_graph):
        """CRS node is a terminal node (no outgoing edges in our test data)."""
        edges = crs_graph.get_edges_from("node:crs")
        assert len(edges) == 0

    def test_get_edges_by_type(self, crs_graph):
        activates = crs_graph.get_edges_by_type("ACTIVATES")
        assert len(activates) >= 3  # CAR-T->Expansion, IFN-gamma->Macrophage, sIL6R->Endothelial
        for edge in activates:
            assert edge.edge_type == "ACTIVATES"

    def test_correlates_with_edges(self, crs_graph):
        correlates = crs_graph.get_edges_by_type("CORRELATES_WITH")
        assert len(correlates) == 2  # ferritin, crp
        for edge in correlates:
            assert "correlation" in edge.properties


class TestPathFinding:
    """Tests for BFS path finding."""

    def test_path_cart_to_crs(self, crs_graph):
        """The full CRS cascade path should be discoverable."""
        path = crs_graph.find_path("node:cart_cell", "node:crs")
        assert len(path) > 0
        assert path[0] == "node:cart_cell"
        assert path[-1] == "node:crs"

    def test_path_il6_to_crs(self, crs_graph):
        """IL-6 -> sIL-6R -> Endothelial Activation -> Vascular Leak -> CRS."""
        path = crs_graph.find_path("node:il6", "node:crs")
        assert len(path) > 0
        assert "node:il6" == path[0]
        assert "node:crs" == path[-1]

    def test_no_path_between_unconnected(self, crs_graph):
        """Tocilizumab -> CRS has no forward path (tocilizumab INHIBITS, doesn't lead to CRS)."""
        # Tocilizumab only has an INHIBITS edge to sIL-6R, which does connect forward.
        # But let's test truly disconnected: CRS -> cart_cell (reverse direction)
        path = crs_graph.find_path("node:crs", "node:cart_cell")
        assert path == []  # No reverse path in a directed graph

    def test_path_to_self(self, crs_graph):
        path = crs_graph.find_path("node:il6", "node:il6")
        assert path == ["node:il6"]

    def test_path_nonexistent_node(self, crs_graph):
        path = crs_graph.find_path("node:fake", "node:crs")
        assert path == []


class TestPathwayDiscovery:
    """Tests for finding relevant pathways to adverse events."""

    def test_find_pathways_from_cart_cell(self, crs_graph):
        pathways = crs_graph.find_relevant_pathways("node:cart_cell", "Adverse_Event")
        assert len(pathways) >= 1
        # Should find path to CRS and/or vascular leak
        endpoint_nodes = [p[-1] for p in pathways]
        assert "node:crs" in endpoint_nodes or "node:vascular_leak" in endpoint_nodes

    def test_find_pathways_from_il6(self, crs_graph):
        pathways = crs_graph.find_relevant_pathways("node:il6", "Adverse_Event")
        assert len(pathways) >= 1

    def test_find_pathways_no_results(self, crs_graph):
        """Drug node may not have a forward path to adverse events."""
        # Actually tocilizumab -> sIL6R -> endothelial -> vascular_leak -> crs
        # So it does connect. Let's test from CRS itself (terminal).
        pathways = crs_graph.find_relevant_pathways("node:crs", "Adverse_Event")
        # CRS is itself an AE, path to self = [node:crs]
        assert any(p == ["node:crs"] for p in pathways)


class TestMechanismValidation:
    """Tests for validate_mechanism."""

    def test_valid_mechanism(self, crs_graph):
        # cart_cell -> t_cell_expansion -> ifn_gamma -> macrophage_activation -> il6
        pathway = [
            "node:cart_cell",
            "node:t_cell_expansion",
            "node:ifn_gamma",
            "node:macrophage_activation",
            "node:il6",
        ]
        result = crs_graph.validate_mechanism(pathway)
        assert result["valid"] is True
        assert len(result["missing_edges"]) == 0
        assert result["total_evidence"] > 0

    def test_invalid_mechanism_missing_edge(self, crs_graph):
        # cart_cell -> il6 has no direct edge
        pathway = ["node:cart_cell", "node:il6"]
        result = crs_graph.validate_mechanism(pathway)
        assert result["valid"] is False
        assert len(result["missing_edges"]) == 1

    def test_partial_mechanism(self, crs_graph):
        # il6 -> sil6r exists, sil6r -> crs does NOT exist directly
        pathway = ["node:il6", "node:sil6r", "node:crs"]
        result = crs_graph.validate_mechanism(pathway)
        assert result["valid"] is False
        # sil6r -> crs is missing (there is sil6r -> endothelial_activation, not sil6r -> crs)

    def test_single_node_pathway_always_valid(self, crs_graph):
        result = crs_graph.validate_mechanism(["node:il6"])
        assert result["valid"] is True
        assert result["total_evidence"] == 0

    def test_evidence_accumulates(self, crs_graph):
        pathway = ["node:cart_cell", "node:t_cell_expansion"]
        result = crs_graph.validate_mechanism(pathway)
        assert result["total_evidence"] == 120  # From edge properties


class TestBiomarkerCorrelation:
    """Tests for biomarker-AE correlation queries."""

    def test_crs_biomarkers(self, crs_graph):
        biomarkers = crs_graph.get_correlating_biomarkers("node:crs")
        assert len(biomarkers) == 2  # ferritin and crp
        # Should be sorted by correlation descending
        assert biomarkers[0][1] >= biomarkers[1][1]
        # Ferritin has higher correlation (0.72 vs 0.58)
        assert biomarkers[0][0] == "node:ferritin"

    def test_no_biomarkers_for_drug(self, crs_graph):
        biomarkers = crs_graph.get_correlating_biomarkers("node:tocilizumab")
        assert len(biomarkers) == 0
