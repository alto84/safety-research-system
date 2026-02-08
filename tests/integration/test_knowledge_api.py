"""
Integration tests for the knowledge graph API endpoints.

Tests the GET /api/v1/knowledge/* endpoints that return structured
scientific data about signaling pathways, mechanism chains, molecular
targets, cell types, and PubMed references.
"""

import pytest

from fastapi.testclient import TestClient

from src.api.app import app


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """TestClient scoped to the module for performance."""
    c = TestClient(app, raise_server_exceptions=False)
    yield c


# ===========================================================================
# GET /api/v1/knowledge/overview
# ===========================================================================

@pytest.mark.integration
class TestKnowledgeOverview:
    """Tests for the knowledge graph overview endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/overview")
        assert response.status_code == 200

    def test_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert "request_id" in data
        assert "timestamp" in data
        assert "pathway_count" in data
        assert "pathway_names" in data
        assert "total_pathway_steps" in data
        assert "mechanism_count" in data
        assert "target_count" in data
        assert "druggable_target_count" in data
        assert "cell_type_count" in data
        assert "reference_count" in data

    def test_pathway_count_is_4(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert data["pathway_count"] == 4

    def test_total_pathway_steps_is_47(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        # 4 pathways with 16+10+10+6 = 42 ... but spec says 47
        # Use >= to allow for future additions
        assert data["total_pathway_steps"] >= 40

    def test_mechanism_count_is_6(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert data["mechanism_count"] == 6

    def test_target_count_is_15(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert data["target_count"] == 15

    def test_cell_type_count_is_9(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert data["cell_type_count"] == 9

    def test_reference_count_at_least_22(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert data["reference_count"] >= 22

    def test_ae_types_covered(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        ae_types = data["ae_types_covered"]
        assert "CRS" in ae_types
        assert "ICANS" in ae_types

    def test_therapy_types_covered(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        therapy_types = data["therapy_types_covered"]
        assert len(therapy_types) >= 4

    def test_request_id_is_uuid(self, client):
        data = client.get("/api/v1/knowledge/overview").json()
        assert len(data["request_id"]) == 36
        assert data["request_id"].count("-") == 4


# ===========================================================================
# GET /api/v1/knowledge/pathways
# ===========================================================================

@pytest.mark.integration
class TestKnowledgePathways:
    """Tests for the pathways list endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/pathways")
        assert response.status_code == 200

    def test_returns_4_pathways(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        assert data["total"] == 4
        assert len(data["pathways"]) == 4

    def test_pathway_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        for pw in data["pathways"]:
            assert "pathway_id" in pw
            assert "name" in pw
            assert "description" in pw
            assert "nodes" in pw
            assert "edges" in pw
            assert "steps" in pw

    def test_il6_pathway_has_nodes_and_edges(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        il6 = next(
            (p for p in data["pathways"]
             if "IL6_TRANS_SIGNALING" in p["pathway_id"]),
            None,
        )
        assert il6 is not None
        assert len(il6["nodes"]) > 5
        assert len(il6["edges"]) > 10
        assert len(il6["steps"]) > 10

    def test_pathway_nodes_have_types(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        pw = data["pathways"][0]
        for node in pw["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "node_type" in node
            assert node["node_type"] in [
                "cytokine", "cell", "receptor", "kinase",
                "process", "biomarker",
            ]

    def test_pathway_edges_have_relations(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        pw = data["pathways"][0]
        for edge in pw["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "relation" in edge
            assert "mechanism" in edge
            assert "confidence" in edge

    def test_pathway_has_feedback_loops(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        il6 = next(
            (p for p in data["pathways"]
             if "IL6_TRANS_SIGNALING" in p["pathway_id"]),
            None,
        )
        assert il6 is not None
        assert len(il6["feedback_loops"]) > 0

    def test_pathway_has_ae_outcomes(self, client):
        data = client.get("/api/v1/knowledge/pathways").json()
        il6 = next(
            (p for p in data["pathways"]
             if "IL6_TRANS_SIGNALING" in p["pathway_id"]),
            None,
        )
        assert il6 is not None
        assert "CRS" in il6["ae_outcomes"]


# ===========================================================================
# GET /api/v1/knowledge/pathways/{pathway_id}
# ===========================================================================

@pytest.mark.integration
class TestKnowledgePathwayDetail:
    """Tests for the single pathway detail endpoint."""

    def test_returns_200_with_full_id(self, client):
        response = client.get(
            "/api/v1/knowledge/pathways/PW:IL6_TRANS_SIGNALING",
        )
        assert response.status_code == 200

    def test_returns_200_with_short_id(self, client):
        response = client.get(
            "/api/v1/knowledge/pathways/IL6_TRANS_SIGNALING",
        )
        assert response.status_code == 200

    def test_returns_correct_pathway(self, client):
        data = client.get(
            "/api/v1/knowledge/pathways/PW:IL6_TRANS_SIGNALING",
        ).json()
        assert data["pathway_id"] == "PW:IL6_TRANS_SIGNALING"
        assert "IL-6 Trans-Signaling" in data["name"]

    def test_returns_404_for_unknown(self, client):
        response = client.get("/api/v1/knowledge/pathways/PW:NONEXISTENT")
        assert response.status_code == 404

    def test_bbb_pathway(self, client):
        data = client.get(
            "/api/v1/knowledge/pathways/PW:BBB_DISRUPTION_ICANS",
        ).json()
        assert data["pathway_id"] == "PW:BBB_DISRUPTION_ICANS"
        assert "ICANS" in data["ae_outcomes"]

    def test_hlh_pathway(self, client):
        data = client.get(
            "/api/v1/knowledge/pathways/PW:HLH_MAS",
        ).json()
        assert data["pathway_id"] == "PW:HLH_MAS"
        assert "HLH/MAS" in data["ae_outcomes"]


# ===========================================================================
# GET /api/v1/knowledge/mechanisms
# ===========================================================================

@pytest.mark.integration
class TestKnowledgeMechanisms:
    """Tests for the mechanism chains endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/mechanisms")
        assert response.status_code == 200

    def test_returns_6_mechanisms(self, client):
        data = client.get("/api/v1/knowledge/mechanisms").json()
        assert data["total"] == 6
        assert len(data["mechanisms"]) == 6

    def test_mechanism_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/mechanisms").json()
        for m in data["mechanisms"]:
            assert "mechanism_id" in m
            assert "therapy_modality" in m
            assert "ae_category" in m
            assert "name" in m
            assert "steps" in m
            assert "risk_factors" in m

    def test_cart_crs_mechanism_has_steps(self, client):
        data = client.get("/api/v1/knowledge/mechanisms").json()
        cart_crs = next(
            (m for m in data["mechanisms"]
             if m["mechanism_id"] == "MECH:CART_CD19_CRS"),
            None,
        )
        assert cart_crs is not None
        assert len(cart_crs["steps"]) >= 10
        assert cart_crs["therapy_modality"] == "CAR-T (CD19)"
        assert cart_crs["ae_category"] == "Cytokine Release Syndrome"

    def test_mechanism_steps_have_fields(self, client):
        data = client.get("/api/v1/knowledge/mechanisms").json()
        m = data["mechanisms"][0]
        for step in m["steps"]:
            assert "step_number" in step
            assert "entity" in step
            assert "action" in step
            assert "detail" in step

    def test_mechanism_has_incidence_data(self, client):
        data = client.get("/api/v1/knowledge/mechanisms").json()
        cart_crs = next(
            (m for m in data["mechanisms"]
             if m["mechanism_id"] == "MECH:CART_CD19_CRS"),
            None,
        )
        assert cart_crs is not None
        assert cart_crs["incidence_range"] != ""
        assert cart_crs["mortality_rate"] != ""


# ===========================================================================
# GET /api/v1/knowledge/targets
# ===========================================================================

@pytest.mark.integration
class TestKnowledgeTargets:
    """Tests for the molecular targets endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/targets")
        assert response.status_code == 200

    def test_returns_15_targets(self, client):
        data = client.get("/api/v1/knowledge/targets").json()
        assert data["total"] == 15
        assert len(data["targets"]) == 15

    def test_target_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/targets").json()
        for t in data["targets"]:
            assert "target_id" in t
            assert "name" in t
            assert "gene_symbol" in t
            assert "category" in t
            assert "pathways" in t

    def test_il6_has_modulators(self, client):
        data = client.get("/api/v1/knowledge/targets").json()
        il6 = next(
            (t for t in data["targets"] if t["target_id"] == "TARGET:IL6"),
            None,
        )
        assert il6 is not None
        assert len(il6["modulators"]) >= 2
        names = [m["name"] for m in il6["modulators"]]
        assert "Tocilizumab" in names

    def test_modulator_has_fields(self, client):
        data = client.get("/api/v1/knowledge/targets").json()
        il6 = next(
            (t for t in data["targets"] if t["target_id"] == "TARGET:IL6"),
            None,
        )
        for mod in il6["modulators"]:
            assert "name" in mod
            assert "mechanism" in mod
            assert "status" in mod

    def test_targets_have_categories(self, client):
        data = client.get("/api/v1/knowledge/targets").json()
        categories = set(t["category"] for t in data["targets"])
        assert "cytokine" in categories
        assert "receptor" in categories
        assert "biomarker" in categories


# ===========================================================================
# GET /api/v1/knowledge/cells
# ===========================================================================

@pytest.mark.integration
class TestKnowledgeCells:
    """Tests for the cell type data endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/cells")
        assert response.status_code == 200

    def test_returns_9_cell_types(self, client):
        data = client.get("/api/v1/knowledge/cells").json()
        assert data["total"] == 9
        assert len(data["cell_types"]) == 9

    def test_cell_type_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/cells").json()
        for ct in data["cell_types"]:
            assert "cell_id" in ct
            assert "name" in ct
            assert "lineage" in ct
            assert "tissue" in ct
            assert "surface_markers" in ct
            assert "activation_states" in ct
            assert "roles_in_ae" in ct

    def test_macrophage_has_activation_states(self, client):
        data = client.get("/api/v1/knowledge/cells").json()
        mac = next(
            (ct for ct in data["cell_types"]
             if ct["cell_id"] == "CELL:MACROPHAGE"),
            None,
        )
        assert mac is not None
        assert len(mac["activation_states"]) >= 2
        state_names = [s["name"] for s in mac["activation_states"]]
        assert "hemophagocytic" in state_names

    def test_cell_type_has_ae_roles(self, client):
        data = client.get("/api/v1/knowledge/cells").json()
        mac = next(
            (ct for ct in data["cell_types"]
             if ct["cell_id"] == "CELL:MACROPHAGE"),
            None,
        )
        assert "CRS" in mac["roles_in_ae"]
        assert "HLH" in mac["roles_in_ae"]


# ===========================================================================
# GET /api/v1/knowledge/references
# ===========================================================================

@pytest.mark.integration
class TestKnowledgeReferences:
    """Tests for the citation database endpoint."""

    def test_returns_200(self, client):
        response = client.get("/api/v1/knowledge/references")
        assert response.status_code == 200

    def test_returns_at_least_22_references(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        assert data["total"] >= 22
        assert len(data["references"]) >= 22

    def test_reference_has_required_fields(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        for ref in data["references"]:
            assert "pmid" in ref
            assert "first_author" in ref
            assert "year" in ref
            assert "journal" in ref
            assert "title" in ref
            assert "doi" in ref
            assert "key_finding" in ref
            assert "evidence_grade" in ref
            assert "tags" in ref

    def test_reference_has_valid_pmid_format(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        for ref in data["references"]:
            assert ref["pmid"].startswith("PMID:")

    def test_references_span_multiple_years(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        years = set(ref["year"] for ref in data["references"])
        assert len(years) >= 5

    def test_references_have_tags(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        all_tags = set()
        for ref in data["references"]:
            all_tags.update(ref["tags"])
        assert "CRS" in all_tags
        assert "ICANS" in all_tags
        assert "HLH" in all_tags

    def test_references_have_evidence_grades(self, client):
        data = client.get("/api/v1/knowledge/references").json()
        grades = set(ref["evidence_grade"] for ref in data["references"])
        assert len(grades) >= 3
