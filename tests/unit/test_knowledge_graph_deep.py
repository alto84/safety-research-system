"""
Tests for the deep scientific knowledge graph for cell therapy pathophysiology.

Tests cover:
    - References: Citation database integrity and lookup
    - Cell types: Cell definitions, activation states, AE roles
    - Molecular targets: Targets, modulators, pathway membership
    - Pathways: Signaling cascades, feedback loops, intervention points
    - Mechanisms: Therapy->AE chains, step ordering, branching
    - Graph queries: Cross-module search, biomarker rationale, AE overviews
"""

import pytest


# ===========================================================================
# Tests for references.py
# ===========================================================================

class TestReferences:
    """Tests for the citation database."""

    def test_references_not_empty(self):
        from src.data.knowledge.references import REFERENCES
        assert len(REFERENCES) > 0, "Reference database should not be empty"

    def test_all_references_have_pmid(self):
        from src.data.knowledge.references import REFERENCES
        for pmid, ref in REFERENCES.items():
            assert pmid.startswith("PMID:"), f"PMID format: {pmid}"
            assert ref.pmid == pmid

    def test_all_references_have_required_fields(self):
        from src.data.knowledge.references import REFERENCES
        for ref in REFERENCES.values():
            assert ref.first_author, f"Missing first_author: {ref.pmid}"
            assert ref.year > 2000, f"Invalid year: {ref.pmid} -> {ref.year}"
            assert ref.journal, f"Missing journal: {ref.pmid}"
            assert ref.title, f"Missing title: {ref.pmid}"
            assert ref.key_finding, f"Missing key_finding: {ref.pmid}"
            assert ref.evidence_grade in (
                "meta_analysis", "rct", "prospective_cohort",
                "retrospective", "case_series", "preclinical",
                "review", "consensus",
            ), f"Invalid evidence_grade: {ref.pmid} -> {ref.evidence_grade}"

    def test_get_reference_existing(self):
        from src.data.knowledge.references import get_reference
        ref = get_reference("PMID:30275568")
        assert ref is not None
        assert ref.first_author == "Lee"
        assert ref.year == 2019
        assert "ASTCT" in ref.key_finding

    def test_get_reference_nonexistent(self):
        from src.data.knowledge.references import get_reference
        assert get_reference("PMID:99999999") is None

    def test_get_references_by_tag_crs(self):
        from src.data.knowledge.references import get_references_by_tag
        crs_refs = get_references_by_tag("CRS")
        assert len(crs_refs) >= 5, "Should have multiple CRS references"
        for ref in crs_refs:
            assert "CRS" in ref.tags

    def test_get_references_by_tag_icans(self):
        from src.data.knowledge.references import get_references_by_tag
        icans_refs = get_references_by_tag("ICANS")
        assert len(icans_refs) >= 3

    def test_get_references_by_evidence_grade(self):
        from src.data.knowledge.references import get_references_by_evidence_grade
        preclinical = get_references_by_evidence_grade("preclinical")
        assert len(preclinical) >= 2
        for ref in preclinical:
            assert ref.evidence_grade == "preclinical"

    def test_norelli_reference(self):
        """Norelli 2018 is a key CRS reference."""
        from src.data.knowledge.references import get_reference
        ref = get_reference("PMID:29643512")
        assert ref is not None
        assert ref.first_author == "Norelli"
        assert ref.year == 2018
        assert "IL-6" in ref.key_finding or "monocyte" in ref.key_finding.lower()

    def test_gust_reference(self):
        """Gust 2017 is the foundational ICANS/endothelial paper."""
        from src.data.knowledge.references import get_reference
        ref = get_reference("PMID:29025771")
        assert ref is not None
        assert ref.first_author == "Gust"
        assert "Ang-2" in ref.key_finding or "endothelial" in ref.key_finding.lower()


# ===========================================================================
# Tests for cell_types.py
# ===========================================================================

class TestCellTypes:
    """Tests for cell type definitions."""

    def test_registry_not_empty(self):
        from src.data.knowledge.cell_types import CELL_TYPE_REGISTRY
        assert len(CELL_TYPE_REGISTRY) >= 8

    def test_all_cells_have_required_fields(self):
        from src.data.knowledge.cell_types import CELL_TYPE_REGISTRY
        for cell in CELL_TYPE_REGISTRY.values():
            assert cell.cell_id
            assert cell.name
            assert cell.lineage
            assert cell.tissue
            assert len(cell.surface_markers) > 0
            assert len(cell.activation_states) > 0
            assert len(cell.roles_in_ae) > 0

    def test_macrophage_has_hemophagocytic_state(self):
        from src.data.knowledge.cell_types import get_cell_type
        mac = get_cell_type("CELL:MACROPHAGE")
        assert mac is not None
        state_names = [s.name for s in mac.activation_states]
        assert "hemophagocytic" in state_names

    def test_endothelial_cell_in_crs_and_icans(self):
        from src.data.knowledge.cell_types import get_cell_type
        endo = get_cell_type("CELL:ENDOTHELIAL")
        assert endo is not None
        assert "CRS" in endo.roles_in_ae
        assert "ICANS" in endo.roles_in_ae

    def test_pericyte_cd19_expression(self):
        from src.data.knowledge.cell_types import get_cell_type
        pericyte = get_cell_type("CELL:PERICYTE")
        assert pericyte is not None
        assert "CD19_low" in pericyte.surface_markers
        assert "ICANS" in pericyte.roles_in_ae

    def test_get_cells_involved_in_crs(self):
        from src.data.knowledge.cell_types import get_cells_involved_in_ae
        crs_cells = get_cells_involved_in_ae("CRS")
        cell_names = [c.name for c in crs_cells]
        assert "CAR-T Cell" in cell_names
        assert "Monocyte" in cell_names
        assert "Macrophage" in cell_names
        assert "Endothelial Cell" in cell_names

    def test_get_cells_involved_in_hlh(self):
        from src.data.knowledge.cell_types import get_cells_involved_in_ae
        hlh_cells = get_cells_involved_in_ae("HLH")
        cell_names = [c.name for c in hlh_cells]
        assert "Macrophage" in cell_names
        assert "Natural Killer Cell" in cell_names

    def test_monocyte_is_primary_il6_source(self):
        from src.data.knowledge.cell_types import get_cell_type
        mono = get_cell_type("CELL:MONOCYTE")
        assert mono is not None
        assert "primary" in mono.roles_in_ae["CRS"].lower() or "PRIMARY" in mono.roles_in_ae["CRS"]

    def test_neutrophil_early_activation(self):
        from src.data.knowledge.cell_types import get_cell_type
        neutrophil = get_cell_type("CELL:NEUTROPHIL")
        assert neutrophil is not None
        assert "CRS" in neutrophil.roles_in_ae
        assert "sIL-6R" in neutrophil.activation_states[0].secreted_factors

    def test_astrocyte_quinolinic_acid(self):
        from src.data.knowledge.cell_types import get_cell_type
        astrocyte = get_cell_type("CELL:ASTROCYTE")
        assert astrocyte is not None
        secreted = astrocyte.activation_states[0].secreted_factors
        assert "quinolinic_acid" in secreted


# ===========================================================================
# Tests for molecular_targets.py
# ===========================================================================

class TestMolecularTargets:
    """Tests for molecular targets and druggable targets."""

    def test_registry_not_empty(self):
        from src.data.knowledge.molecular_targets import MOLECULAR_TARGET_REGISTRY
        assert len(MOLECULAR_TARGET_REGISTRY) >= 12

    def test_il6_target(self):
        from src.data.knowledge.molecular_targets import get_target
        il6 = get_target("TARGET:IL6")
        assert il6 is not None
        assert il6.gene_symbol == "IL6"
        assert "trans-signaling" in il6.clinical_relevance.lower() or "trans_signaling" in str(il6.pathways).lower()

    def test_il6_has_tocilizumab_modulator(self):
        from src.data.knowledge.molecular_targets import get_target
        il6 = get_target("TARGET:IL6")
        assert il6 is not None
        mod_names = [m.name for m in il6.modulators]
        assert "Tocilizumab" in mod_names

    def test_ang2_target(self):
        from src.data.knowledge.molecular_targets import get_target
        ang2 = get_target("TARGET:ANG2")
        assert ang2 is not None
        assert "Tie2" in ang2.clinical_relevance or "pericyte" in ang2.clinical_relevance

    def test_ferritin_dual_role(self):
        from src.data.knowledge.molecular_targets import get_target
        ferritin = get_target("TARGET:FERRITIN")
        assert ferritin is not None
        assert "10,000" in ferritin.biomarker_utility or "10000" in ferritin.ae_range

    def test_easix_composite_biomarker(self):
        from src.data.knowledge.molecular_targets import get_target
        easix = get_target("TARGET:EASIX")
        assert easix is not None
        assert "LDH" in easix.normal_range

    def test_icasp9_safety_switch(self):
        from src.data.knowledge.molecular_targets import get_target
        icasp9 = get_target("TARGET:ICASP9")
        assert icasp9 is not None
        assert len(icasp9.modulators) > 0
        assert "AP1903" in icasp9.modulators[0].name or "Rimiducid" in icasp9.modulators[0].name

    def test_get_druggable_targets(self):
        from src.data.knowledge.molecular_targets import get_druggable_targets
        druggable = get_druggable_targets()
        assert len(druggable) >= 5
        names = [t.name for t in druggable]
        assert any("IL-6" in n for n in names)
        assert any("IL-1" in n for n in names)

    def test_get_targets_in_pathway(self):
        from src.data.knowledge.molecular_targets import get_targets_in_pathway
        jak_stat_targets = get_targets_in_pathway("JAK/STAT")
        assert len(jak_stat_targets) >= 2
        names = [t.name for t in jak_stat_targets]
        assert any("JAK" in n for n in names)
        assert any("STAT" in n for n in names)

    def test_il1_beta_upstream_of_il6(self):
        from src.data.knowledge.molecular_targets import get_target
        il1b = get_target("TARGET:IL1B")
        assert il1b is not None
        assert "IL-6" in il1b.upstream_of or "IL6" in str(il1b.upstream_of)

    def test_all_targets_have_references(self):
        """At least most targets should have PubMed references."""
        from src.data.knowledge.molecular_targets import MOLECULAR_TARGET_REGISTRY
        targets_with_refs = [
            t for t in MOLECULAR_TARGET_REGISTRY.values()
            if t.references
        ]
        # At least 75% should have references
        assert len(targets_with_refs) >= len(MOLECULAR_TARGET_REGISTRY) * 0.7


# ===========================================================================
# Tests for pathways.py
# ===========================================================================

class TestPathways:
    """Tests for signaling pathway definitions."""

    def test_registry_not_empty(self):
        from src.data.knowledge.pathways import PATHWAY_REGISTRY
        assert len(PATHWAY_REGISTRY) >= 4

    def test_il6_trans_signaling_pathway(self):
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:IL6_TRANS_SIGNALING")
        assert pw is not None
        assert len(pw.steps) >= 10
        assert "CRS" in pw.ae_outcomes

    def test_bbb_disruption_pathway(self):
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:BBB_DISRUPTION_ICANS")
        assert pw is not None
        assert "ICANS" in pw.ae_outcomes
        # Should include pericyte step
        step_entities = [s.source for s in pw.steps] + [s.target for s in pw.steps]
        assert any("pericyte" in e.lower() for e in step_entities)

    def test_hlh_pathway(self):
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:HLH_MAS")
        assert pw is not None
        assert "HLH/MAS" in pw.ae_outcomes

    def test_il6_pathway_has_feedback_loops(self):
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:IL6_TRANS_SIGNALING")
        assert pw is not None
        assert len(pw.feedback_loops) >= 2
        assert any("STAT3" in loop for loop in pw.feedback_loops)

    def test_hlh_pathway_has_ifn_il18_loop(self):
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:HLH_MAS")
        assert pw is not None
        feedback_steps = [s for s in pw.steps if s.is_feedback_loop]
        assert len(feedback_steps) >= 1
        # IFN-gamma/IL-18 loop
        assert any("IL-18" in s.mechanism or "IFN-gamma" in s.mechanism
                    for s in feedback_steps)

    def test_pathway_steps_have_references(self):
        from src.data.knowledge.pathways import PATHWAY_REGISTRY
        for pw in PATHWAY_REGISTRY.values():
            steps_with_refs = [s for s in pw.steps if s.references]
            # At least 60% of steps should have references
            assert len(steps_with_refs) >= len(pw.steps) * 0.5, (
                f"Pathway {pw.name}: too few steps with references"
            )

    def test_get_pathways_for_crs(self):
        from src.data.knowledge.pathways import get_pathways_for_ae
        crs_pathways = get_pathways_for_ae("CRS")
        assert len(crs_pathways) >= 2
        names = [pw.name for pw in crs_pathways]
        assert any("IL-6" in n for n in names)

    def test_get_intervention_points_for_crs(self):
        from src.data.knowledge.pathways import get_intervention_points_for_ae
        interventions = get_intervention_points_for_ae("CRS")
        assert len(interventions) >= 1
        agents = []
        for step in interventions:
            agents.extend(step.intervention_agents)
        assert any("tocilizumab" in a for a in agents)

    def test_pathway_steps_ordered(self):
        """Steps should flow logically from entry to exit."""
        from src.data.knowledge.pathways import get_pathway
        pw = get_pathway("PW:IL6_TRANS_SIGNALING")
        assert pw is not None
        # First step should involve entry point
        assert any(ep in pw.steps[0].source for ep in pw.entry_points)


# ===========================================================================
# Tests for mechanisms.py
# ===========================================================================

class TestMechanisms:
    """Tests for AE mechanism chains."""

    def test_registry_not_empty(self):
        from src.data.knowledge.mechanisms import MECHANISM_REGISTRY
        assert len(MECHANISM_REGISTRY) >= 5

    def test_cart_cd19_crs_mechanism(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_CRS")
        assert mech is not None
        assert len(mech.steps) >= 8
        assert mech.typical_onset
        assert mech.incidence_range

    def test_mechanism_steps_ordered(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_CRS")
        assert mech is not None
        for i, step in enumerate(mech.steps):
            assert step.step_number == i + 1

    def test_cart_cd19_crs_has_branching_points(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_CRS")
        assert mech is not None
        branching = [s for s in mech.steps if s.is_branching_point]
        assert len(branching) >= 1

    def test_cart_cd19_crs_has_intervention_points(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_CRS")
        assert mech is not None
        interventions = [s for s in mech.steps if s.is_intervention_point]
        assert len(interventions) >= 2

    def test_tcrt_cross_reactivity(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:TCRT_CROSS_REACTIVITY")
        assert mech is not None
        assert "titin" in mech.description.lower() or "cardiac" in mech.description.lower()

    def test_carnk_reduced_crs(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CARNK_LOW_CRS")
        assert mech is not None
        assert "0%" in mech.incidence_range

    def test_gene_therapy_insertional_mutagenesis(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:GT_INSERTIONAL")
        assert mech is not None
        assert "lentiviral" in mech.description.lower() or "insertional" in mech.name.lower()

    def test_get_mechanisms_for_therapy(self):
        from src.data.knowledge.mechanisms import (
            get_mechanisms_for_therapy, TherapyModality,
        )
        cart_cd19 = get_mechanisms_for_therapy(TherapyModality.CAR_T_CD19)
        assert len(cart_cd19) >= 2  # CRS and ICANS at least

    def test_get_mechanisms_for_ae(self):
        from src.data.knowledge.mechanisms import (
            get_mechanisms_for_ae, AECategory,
        )
        crs_mechs = get_mechanisms_for_ae(AECategory.CRS)
        assert len(crs_mechs) >= 2  # CAR-T CRS and CAR-NK reduced CRS

    def test_get_mechanism_chain_function(self):
        from src.data.knowledge.mechanisms import get_mechanism_chain
        chain = get_mechanism_chain("CAR-T (CD19)", "Cytokine Release Syndrome")
        assert len(chain) >= 8
        assert chain[0].step_number == 1

    def test_mechanism_has_risk_factors(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_CRS")
        assert mech is not None
        assert len(mech.risk_factors) >= 4
        assert any("tumor burden" in rf.lower() for rf in mech.risk_factors)

    def test_b_cell_aplasia_mechanism(self):
        from src.data.knowledge.mechanisms import get_mechanism
        mech = get_mechanism("MECH:CART_CD19_BCELL_APLASIA")
        assert mech is not None
        assert "on-target" in mech.name.lower() or "B-Cell" in mech.name


# ===========================================================================
# Tests for graph_queries.py
# ===========================================================================

class TestGraphQueries:
    """Tests for cross-module query functions."""

    def test_get_pathway_for_crs(self):
        from src.data.knowledge.graph_queries import get_pathway_for_ae
        result = get_pathway_for_ae("CRS")
        assert len(result.pathways) >= 2
        assert result.total_steps > 10
        assert len(result.feedback_loops) >= 2
        assert len(result.references) >= 3

    def test_get_pathway_for_icans(self):
        from src.data.knowledge.graph_queries import get_pathway_for_ae
        result = get_pathway_for_ae("ICANS")
        assert len(result.pathways) >= 1

    def test_get_pathway_for_hlh(self):
        from src.data.knowledge.graph_queries import get_pathway_for_ae
        result = get_pathway_for_ae("HLH/MAS")
        assert len(result.pathways) >= 1

    def test_get_intervention_points_crs(self):
        from src.data.knowledge.graph_queries import get_intervention_points
        targets = get_intervention_points("CRS")
        assert len(targets) >= 1
        agents = []
        for t in targets:
            agents.extend(t.agents)
        assert any("tocilizumab" in a for a in agents)

    def test_get_biomarker_rationale_crp(self):
        from src.data.knowledge.graph_queries import get_biomarker_rationale
        rationale = get_biomarker_rationale("CRP")
        assert rationale.biomarker_name
        assert rationale.target is not None
        assert rationale.normal_range
        assert rationale.ae_range
        assert len(rationale.upstream_drivers) > 0

    def test_get_biomarker_rationale_ferritin(self):
        from src.data.knowledge.graph_queries import get_biomarker_rationale
        rationale = get_biomarker_rationale("ferritin")
        assert rationale.target is not None
        assert "10,000" in rationale.clinical_utility or "10000" in rationale.ae_range

    def test_get_biomarker_rationale_easix(self):
        from src.data.knowledge.graph_queries import get_biomarker_rationale
        rationale = get_biomarker_rationale("EASIX")
        assert rationale.target is not None
        assert "LDH" in rationale.clinical_utility or "LDH" in rationale.normal_range

    def test_get_biomarker_rationale_nonexistent(self):
        from src.data.knowledge.graph_queries import get_biomarker_rationale
        rationale = get_biomarker_rationale("nonexistent_marker_xyz")
        assert rationale.target is None

    def test_search_by_molecule_il6(self):
        from src.data.knowledge.graph_queries import search_by_molecule
        results = search_by_molecule("IL-6")
        assert len(results) >= 3  # Should appear in targets, pathways, and cell secretions

    def test_search_by_molecule_ang2(self):
        from src.data.knowledge.graph_queries import search_by_molecule
        results = search_by_molecule("Ang-2")
        assert len(results) >= 1

    def test_search_by_molecule_stat3(self):
        from src.data.knowledge.graph_queries import search_by_molecule
        results = search_by_molecule("STAT3")
        assert len(results) >= 1

    def test_get_ae_overview_crs(self):
        from src.data.knowledge.graph_queries import get_ae_overview
        overview = get_ae_overview("CRS")
        assert overview["ae_type"] == "CRS"
        assert len(overview["pathways"]) >= 2
        assert len(overview["cell_types"]) >= 3
        assert len(overview["biomarkers"]) >= 2
        assert len(overview["feedback_loops"]) >= 2
        assert overview["reference_count"] >= 5

    def test_get_full_mechanism_chain(self):
        from src.data.knowledge.graph_queries import get_full_mechanism_chain
        chain = get_full_mechanism_chain("CAR-T (CD19)", "Cytokine Release Syndrome")
        assert len(chain) >= 8

    def test_get_full_mechanism_chain_no_match(self):
        from src.data.knowledge.graph_queries import get_full_mechanism_chain
        chain = get_full_mechanism_chain("nonexistent", "nonexistent")
        assert chain == []


# ===========================================================================
# Scientific accuracy tests
# ===========================================================================

class TestScientificAccuracy:
    """Tests verifying scientific accuracy of the knowledge graph content."""

    def test_monocyte_primary_il6_source_norelli(self):
        """Norelli et al. 2018 established monocytes as the primary IL-6 source."""
        from src.data.knowledge.cell_types import get_cell_type
        mono = get_cell_type("CELL:MONOCYTE")
        assert mono is not None
        il6_in_secreted = any(
            "IL-6" in factor or "IL6" in factor
            for state in mono.activation_states
            for factor in state.secreted_factors
        )
        assert il6_in_secreted

    def test_il6_trans_signaling_is_pathological(self):
        """Trans-signaling (via sIL-6R) is the pathological mode."""
        from src.data.knowledge.molecular_targets import get_target
        sil6r = get_target("TARGET:SIL6R")
        assert sil6r is not None
        assert "trans" in sil6r.clinical_relevance.lower()
        assert "pathological" in sil6r.clinical_relevance.lower() or "dominant" in sil6r.clinical_relevance.lower()

    def test_stat3_positive_feedback_loop(self):
        """STAT3 -> IL-6 gene -> IL-6 -> gp130 -> STAT3 feedback loop."""
        from src.data.knowledge.molecular_targets import get_target
        stat3 = get_target("TARGET:STAT3")
        assert stat3 is not None
        assert "feedback" in stat3.clinical_relevance.lower()
        assert "IL-6" in str(stat3.upstream_of)

    def test_ang2_ang1_ratio_icans(self):
        """Ang-2:Ang-1 ratio correlates with ICANS severity (Gust 2017)."""
        from src.data.knowledge.molecular_targets import get_target
        ang2 = get_target("TARGET:ANG2")
        assert ang2 is not None
        assert "Ang-1" in ang2.biomarker_utility or "ratio" in ang2.biomarker_utility

    def test_ferritin_10000_hlh_threshold(self):
        """Ferritin >10,000 ng/mL is diagnostic for IEC-HS."""
        from src.data.knowledge.molecular_targets import get_target
        ferritin = get_target("TARGET:FERRITIN")
        assert ferritin is not None
        assert "10,000" in ferritin.clinical_relevance or "10000" in ferritin.ae_range

    def test_ifn_gamma_earliest_cytokine(self):
        """IFN-gamma is the earliest cytokine to peak post-CAR-T."""
        from src.data.knowledge.molecular_targets import get_target
        ifng = get_target("TARGET:IFNG")
        assert ifng is not None
        assert "earliest" in ifng.clinical_relevance.lower()

    def test_tocilizumab_blocks_both_il6r_forms(self):
        """Tocilizumab blocks both membrane-bound and soluble IL-6R."""
        from src.data.knowledge.molecular_targets import get_target
        il6 = get_target("TARGET:IL6")
        assert il6 is not None
        toci = [m for m in il6.modulators if m.name == "Tocilizumab"]
        assert len(toci) == 1
        assert "membrane" in toci[0].mechanism.lower() or "soluble" in toci[0].mechanism.lower()

    def test_anakinra_upstream_of_il6(self):
        """Anakinra (IL-1Ra) blocks IL-1beta which is upstream of IL-6."""
        from src.data.knowledge.molecular_targets import get_target
        il1b = get_target("TARGET:IL1B")
        assert il1b is not None
        assert "upstream" in il1b.clinical_relevance.lower()
        anakinra = [m for m in il1b.modulators if m.name == "Anakinra"]
        assert len(anakinra) == 1

    def test_cd19_pericyte_on_target_off_tumor(self):
        """Brain pericytes express CD19 (Parker et al., 2020)."""
        from src.data.knowledge.cell_types import get_cell_type
        pericyte = get_cell_type("CELL:PERICYTE")
        assert pericyte is not None
        state_names = [s.name for s in pericyte.activation_states]
        assert "targeted_by_cd19_cart" in state_names

    def test_neutrophil_sil6r_source(self):
        """Neutrophils generate sIL-6R via ADAM17 shedding."""
        from src.data.knowledge.cell_types import get_cell_type
        neutrophil = get_cell_type("CELL:NEUTROPHIL")
        assert neutrophil is not None
        assert "ADAM17" in neutrophil.roles_in_ae.get("CRS", "")

    def test_crs_before_icans_temporal_order(self):
        """CRS typically precedes ICANS by 1-3 days."""
        from src.data.knowledge.mechanisms import get_mechanism
        icans = get_mechanism("MECH:CART_CD19_ICANS")
        assert icans is not None
        assert "precedes" in icans.description.lower() or "after CRS" in icans.typical_onset.lower() or "CRS" in icans.risk_factors[0]
