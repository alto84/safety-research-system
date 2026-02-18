"""
Tests for the GET /api/v1/knowledge/graph endpoint.

The knowledge graph endpoint combines data from PATHWAY_REGISTRY,
MOLECULAR_TARGET_REGISTRY, CELL_TYPE_REGISTRY, and MECHANISM_REGISTRY
into a unified force-directed graph format with nodes, edges, pathways,
and stats.
"""

import pytest

from fastapi.testclient import TestClient

from src.api.app import app
from src.api.population_routes import _build_knowledge_graph


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    c = TestClient(app, raise_server_exceptions=False)
    yield c


# ===========================================================================
# Direct unit tests for _build_knowledge_graph()
# ===========================================================================


class TestBuildKnowledgeGraphUnit:
    """Unit tests for the _build_knowledge_graph helper function."""

    def test_returns_dict_with_required_keys(self):
        """Graph data must contain nodes, edges, pathways, and stats."""
        result = _build_knowledge_graph()
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result
        assert "pathways" in result
        assert "stats" in result

    def test_nodes_have_required_fields(self):
        """Each node must have id, type, label, pathways, and size."""
        result = _build_knowledge_graph()
        for node in result["nodes"]:
            assert "id" in node, f"Node missing 'id': {node}"
            assert "type" in node, f"Node {node['id']} missing 'type'"
            assert "label" in node, f"Node {node['id']} missing 'label'"
            assert "pathways" in node, f"Node {node['id']} missing 'pathways'"
            assert "size" in node, f"Node {node['id']} missing 'size'"

    def test_edges_have_required_fields(self):
        """Each edge must have source, target, relation, pathway, confidence."""
        result = _build_knowledge_graph()
        for edge in result["edges"]:
            assert "source" in edge, f"Edge missing 'source': {edge}"
            assert "target" in edge, f"Edge missing 'target': {edge}"
            assert "relation" in edge, f"Edge missing 'relation': {edge}"
            assert "pathway" in edge, f"Edge missing 'pathway': {edge}"
            assert "confidence" in edge, f"Edge missing 'confidence': {edge}"

    def test_stats_fields(self):
        """Stats must contain total_nodes, total_edges, total_pathways."""
        result = _build_knowledge_graph()
        stats = result["stats"]
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "total_pathways" in stats

    def test_stats_match_data(self):
        """Stats counts must match actual data lengths."""
        result = _build_knowledge_graph()
        assert result["stats"]["total_nodes"] == len(result["nodes"])
        assert result["stats"]["total_edges"] == len(result["edges"])
        assert result["stats"]["total_pathways"] == len(result["pathways"])

    def test_node_ids_unique(self):
        """All node IDs must be unique."""
        result = _build_knowledge_graph()
        ids = [n["id"] for n in result["nodes"]]
        assert len(ids) == len(set(ids)), f"Duplicate node IDs found: {[x for x in ids if ids.count(x) > 1]}"

    def test_edges_reference_existing_nodes(self):
        """All edge source/target IDs must exist in the node list."""
        result = _build_knowledge_graph()
        node_ids = {n["id"] for n in result["nodes"]}
        for edge in result["edges"]:
            assert edge["source"] in node_ids, (
                f"Edge source '{edge['source']}' not in nodes"
            )
            assert edge["target"] in node_ids, (
                f"Edge target '{edge['target']}' not in nodes"
            )

    def test_has_multiple_node_types(self):
        """Graph should contain nodes of at least 3 different types."""
        result = _build_knowledge_graph()
        types = {n["type"] for n in result["nodes"]}
        assert len(types) >= 3, f"Only {len(types)} node types: {types}"

    def test_contains_drug_nodes(self):
        """Graph should contain at least one drug node from molecular targets."""
        result = _build_knowledge_graph()
        drug_nodes = [n for n in result["nodes"] if n["type"] == "drug"]
        assert len(drug_nodes) >= 1, "No drug nodes found"
        # Tocilizumab should be present (approved for CRS)
        drug_names = {n["id"] for n in drug_nodes}
        assert "Tocilizumab" in drug_names, f"Tocilizumab not in drugs: {drug_names}"

    def test_contains_cell_type_nodes(self):
        """Graph should contain cell type nodes from CELL_TYPE_REGISTRY."""
        result = _build_knowledge_graph()
        cell_nodes = [n for n in result["nodes"] if n["type"] == "cell_type"]
        assert len(cell_nodes) >= 1, "No cell_type nodes found"

    def test_pathways_include_signaling_pathways(self):
        """Pathways list should include the 4 signaling pathways."""
        result = _build_knowledge_graph()
        pw_names = result["pathways"]
        # At least 4 signaling pathway names
        assert len(pw_names) >= 4, f"Only {len(pw_names)} pathways"

    def test_node_size_correlates_with_connectivity(self):
        """Nodes with more edges should have larger size values."""
        result = _build_knowledge_graph()
        # Find a highly connected node (IL-6 or similar)
        node_map = {n["id"]: n for n in result["nodes"]}
        edge_counts = {}
        for e in result["edges"]:
            edge_counts[e["source"]] = edge_counts.get(e["source"], 0) + 1
            edge_counts[e["target"]] = edge_counts.get(e["target"], 0) + 1

        # Find max connectivity node
        if edge_counts:
            max_node_id = max(edge_counts, key=edge_counts.get)
            max_node = node_map.get(max_node_id)
            if max_node:
                assert max_node["size"] > 1, (
                    f"Most connected node {max_node_id} has size {max_node['size']}"
                )

    def test_confidence_values_valid(self):
        """All edge confidence values should be between 0 and 1."""
        result = _build_knowledge_graph()
        for edge in result["edges"]:
            assert 0 <= edge["confidence"] <= 1, (
                f"Invalid confidence {edge['confidence']} on edge "
                f"{edge['source']}->{edge['target']}"
            )

    def test_no_self_loops(self):
        """Edges should not have the same source and target."""
        result = _build_knowledge_graph()
        for edge in result["edges"]:
            assert edge["source"] != edge["target"], (
                f"Self-loop found: {edge['source']}"
            )


# ===========================================================================
# API endpoint integration tests
# ===========================================================================


class TestKnowledgeGraphAPI:
    """Tests for the GET /api/v1/knowledge/graph endpoint."""

    def test_returns_200(self, client):
        """Endpoint should return 200 OK."""
        response = client.get("/api/v1/knowledge/graph")
        assert response.status_code == 200

    def test_response_has_request_id(self, client):
        """Response should include a request_id for traceability."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "request_id" in data
        assert len(data["request_id"]) > 0

    def test_response_has_timestamp(self, client):
        """Response should include a timestamp."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "timestamp" in data

    def test_response_has_nodes_list(self, client):
        """Response should contain a nodes list."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) > 0

    def test_response_has_edges_list(self, client):
        """Response should contain an edges list."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "edges" in data
        assert isinstance(data["edges"], list)
        assert len(data["edges"]) > 0

    def test_response_has_pathways_list(self, client):
        """Response should contain a pathways list."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "pathways" in data
        assert isinstance(data["pathways"], list)
        assert len(data["pathways"]) >= 4

    def test_response_has_stats(self, client):
        """Response should contain stats with counts."""
        data = client.get("/api/v1/knowledge/graph").json()
        assert "stats" in data
        stats = data["stats"]
        assert stats["total_nodes"] > 0
        assert stats["total_edges"] > 0
        assert stats["total_pathways"] > 0

    def test_reasonable_graph_size(self, client):
        """Graph should have a reasonable number of nodes and edges."""
        data = client.get("/api/v1/knowledge/graph").json()
        # Based on 4 pathways + 15 targets + 9 cell types + drugs + mechanism entities
        assert data["stats"]["total_nodes"] >= 30, (
            f"Expected >= 30 nodes, got {data['stats']['total_nodes']}"
        )
        assert data["stats"]["total_edges"] >= 40, (
            f"Expected >= 40 edges, got {data['stats']['total_edges']}"
        )

    def test_node_types_present(self, client):
        """Multiple node types should be present in the response."""
        data = client.get("/api/v1/knowledge/graph").json()
        types = {n["type"] for n in data["nodes"]}
        # Should have at least cytokine, drug, cell_type/cell, process
        assert len(types) >= 3, f"Only {len(types)} types: {types}"

    def test_edge_relations_present(self, client):
        """Multiple edge relation types should be present."""
        data = client.get("/api/v1/knowledge/graph").json()
        relations = {e["relation"] for e in data["edges"]}
        assert len(relations) >= 2, f"Only {len(relations)} relations: {relations}"
        # 'activates' and 'produces' should be present from the pathways
        assert "activates" in relations or "produces" in relations, (
            f"Expected 'activates' or 'produces' in relations: {relations}"
        )
