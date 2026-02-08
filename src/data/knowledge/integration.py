"""
Lightweight integration bridge between the knowledge graph and risk models.

Provides utility functions that, given a patient's adverse event type, return
relevant mechanistic context from the knowledge graph -- pathway descriptions,
key biomarkers, druggable targets, and intervention options.  This enables the
narrative engine and API endpoints to enrich risk assessment outputs with
biological rationale without restructuring existing model code.

Usage::

    from src.data.knowledge.integration import get_mechanistic_context

    context = get_mechanistic_context("CRS")
    print(context["pathway_summary"])
    print(context["key_biomarkers"])
    print(context["druggable_targets"])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.data.knowledge.graph_queries import (
    get_pathway_for_ae,
    get_intervention_points,
    get_biomarker_rationale,
)
from src.data.knowledge.pathways import (
    PATHWAY_REGISTRY,
    get_pathways_for_ae,
)
from src.data.knowledge.molecular_targets import (
    MOLECULAR_TARGET_REGISTRY,
    TargetCategory,
    get_druggable_targets,
    get_targets_in_pathway,
)
from src.data.knowledge.cell_types import get_cells_involved_in_ae
from src.data.knowledge.mechanisms import (
    MECHANISM_REGISTRY,
    AECategory,
    get_mechanisms_for_ae,
)


# ---------------------------------------------------------------------------
# AE name normalisation
# ---------------------------------------------------------------------------

_AE_ALIASES: dict[str, str] = {
    "CRS": "CRS",
    "CYTOKINE RELEASE SYNDROME": "CRS",
    "ICANS": "ICANS",
    "NEUROTOXICITY": "ICANS",
    "HLH": "HLH/MAS",
    "HLH/MAS": "HLH/MAS",
    "MAS": "HLH/MAS",
    "HEMOPHAGOCYTIC LYMPHOHISTIOCYTOSIS": "HLH/MAS",
    "ICAHS": "CRS",  # ICAHS shares CRS cytokine biology
}

_AE_TO_CATEGORY: dict[str, str] = {
    "CRS": "Cytokine Release Syndrome",
    "ICANS": "ICANS",
    "HLH/MAS": "HLH/MAS",
}


def _normalise_ae(ae_type: str) -> str:
    """Normalise an AE name to the canonical form used by the knowledge graph."""
    return _AE_ALIASES.get(ae_type.upper(), ae_type.upper())


# ---------------------------------------------------------------------------
# Core integration functions
# ---------------------------------------------------------------------------

@dataclass
class MechanisticContext:
    """Mechanistic context for an adverse event from the knowledge graph.

    Attributes:
        ae_type: Canonical AE type string.
        pathway_summary: One-paragraph summary of the dominant signaling
            pathway(s) driving this AE.
        pathway_names: List of contributing pathway names.
        key_biomarkers: Clinically measurable biomarkers with their
            normal and AE ranges plus clinical utility.
        druggable_targets: Pharmacologically targetable molecules with
            available modulators and mechanisms.
        intervention_points: Pathway steps where pharmacological
            intervention is possible, with agents listed.
        feedback_loops: Descriptions of positive/negative feedback
            mechanisms that amplify or sustain the AE.
        cell_types_involved: Cell populations driving the AE.
        risk_factors: Patient/disease factors that increase AE risk.
        reference_pmids: PubMed IDs supporting the context.
    """

    ae_type: str
    pathway_summary: str
    pathway_names: list[str] = field(default_factory=list)
    key_biomarkers: list[dict[str, str]] = field(default_factory=list)
    druggable_targets: list[dict[str, Any]] = field(default_factory=list)
    intervention_points: list[dict[str, Any]] = field(default_factory=list)
    feedback_loops: list[str] = field(default_factory=list)
    cell_types_involved: list[str] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    reference_pmids: list[str] = field(default_factory=list)


def get_mechanistic_context(ae_type: str) -> MechanisticContext:
    """Return mechanistic context from the knowledge graph for a given AE.

    Aggregates pathway descriptions, biomarker data, druggable targets,
    intervention points, feedback loops, involved cell types, risk
    factors, and supporting references into a single data structure that
    can be consumed by the narrative engine or API endpoints.

    Args:
        ae_type: Adverse event type string.  Accepts common synonyms
            (e.g. "CRS", "Cytokine Release Syndrome", "ICANS",
            "neurotoxicity", "HLH", "HLH/MAS").

    Returns:
        MechanisticContext dataclass with all relevant knowledge-graph
        information for the requested AE.
    """
    canonical = _normalise_ae(ae_type)

    # --- Pathways ---
    pathway_graph = get_pathway_for_ae(canonical)
    pathway_names = [pw.name for pw in pathway_graph.pathways]
    pathway_summary = " ".join(
        pw.description for pw in pathway_graph.pathways
    ) if pathway_graph.pathways else (
        f"No specific signaling pathway data available for {ae_type}."
    )

    # --- Feedback loops ---
    feedback_loops = pathway_graph.feedback_loops

    # --- Biomarkers ---
    biomarker_targets = [
        t for t in MOLECULAR_TARGET_REGISTRY.values()
        if t.category == TargetCategory.BIOMARKER and t.biomarker_utility
    ]
    # Filter to biomarkers relevant to this AE's pathways
    ae_pathway_names = set()
    for pw in pathway_graph.pathways:
        for step in pw.steps:
            ae_pathway_names.add(step.source.lower())
            ae_pathway_names.add(step.target.lower())

    key_biomarkers: list[dict[str, str]] = []
    for bt in biomarker_targets:
        # Include if any of the biomarker's upstream drivers or pathways
        # overlap with molecules in this AE's pathways
        bt_relevant = any(
            p.lower() in " ".join(ae_pathway_names)
            for p in bt.downstream_of
        ) or any(
            pw_name in " ".join(bt.pathways)
            for pw_name in ["acute_phase", "macrophage", "endothelial"]
        )
        if bt_relevant or not pathway_graph.pathways:
            key_biomarkers.append({
                "name": bt.name,
                "normal_range": bt.normal_range,
                "ae_range": bt.ae_range,
                "clinical_utility": bt.biomarker_utility,
            })

    # --- Druggable targets ---
    all_druggable = get_druggable_targets()
    # Filter to targets in pathways relevant to this AE
    ae_mol_names = pathway_graph.key_molecules
    ae_mol_lower = {m.lower() for m in ae_mol_names}

    druggable_targets: list[dict[str, Any]] = []
    for target in all_druggable:
        name_lower = target.name.lower()
        in_ae_pathways = any(mol in name_lower for mol in ae_mol_lower)
        in_ae_outcomes = any(
            canonical in pw.ae_outcomes
            for pw_name in target.pathways
            for pw in PATHWAY_REGISTRY.values()
            if pw_name in pw.name.lower() or pw_name.lower() in pw.name.lower()
        )
        if in_ae_pathways or in_ae_outcomes or not pathway_graph.pathways:
            modulators = [
                {
                    "drug": mod.name,
                    "mechanism": mod.mechanism,
                    "status": mod.status.value,
                }
                for mod in target.modulators
            ]
            druggable_targets.append({
                "target_name": target.name,
                "gene_symbol": target.gene_symbol,
                "clinical_relevance": target.clinical_relevance,
                "modulators": modulators,
            })

    # --- Intervention points ---
    interventions = get_intervention_points(canonical)
    intervention_points: list[dict[str, Any]] = [
        {
            "pathway": ip.pathway_name,
            "step": f"{ip.step.source} -> {ip.step.target}",
            "agents": ip.agents,
            "mechanism": ip.mechanism_of_action,
        }
        for ip in interventions
    ]

    # --- Cell types ---
    cell_types = get_cells_involved_in_ae(canonical)
    cell_type_names = [ct.name for ct in cell_types]

    # --- Mechanism risk factors ---
    ae_full = _AE_TO_CATEGORY.get(canonical, canonical)
    risk_factors: list[str] = []
    for mech in MECHANISM_REGISTRY.values():
        if mech.ae_category.value == ae_full or canonical in mech.ae_category.value:
            risk_factors.extend(mech.risk_factors)

    # --- References ---
    all_refs: set[str] = set(pathway_graph.references)
    for mech in MECHANISM_REGISTRY.values():
        if mech.ae_category.value == ae_full or canonical in mech.ae_category.value:
            all_refs.update(mech.key_references)

    return MechanisticContext(
        ae_type=canonical,
        pathway_summary=pathway_summary,
        pathway_names=pathway_names,
        key_biomarkers=key_biomarkers,
        druggable_targets=druggable_targets,
        intervention_points=intervention_points,
        feedback_loops=feedback_loops,
        cell_types_involved=cell_type_names,
        risk_factors=risk_factors,
        reference_pmids=sorted(all_refs),
    )


def get_narrative_context(ae_type: str) -> dict[str, Any]:
    """Return a dictionary suitable for injection into narrative templates.

    This is a convenience wrapper around :func:`get_mechanistic_context`
    that flattens the result into a plain dictionary for easy consumption
    by string-formatting or template-based narrative engines.

    Args:
        ae_type: Adverse event type string (same synonyms accepted).

    Returns:
        Dictionary with string keys suitable for template substitution.
    """
    ctx = get_mechanistic_context(ae_type)

    # Build a concise biomarker summary string
    biomarker_lines = []
    for bm in ctx.key_biomarkers:
        biomarker_lines.append(
            f"  - {bm['name']}: normal {bm['normal_range']}, "
            f"AE range {bm['ae_range']}. {bm['clinical_utility']}"
        )
    biomarker_summary = "\n".join(biomarker_lines) if biomarker_lines else "None identified."

    # Build intervention summary
    intervention_lines = []
    for ip in ctx.intervention_points:
        agents_str = ", ".join(ip["agents"]) if ip["agents"] else "none available"
        intervention_lines.append(
            f"  - {ip['step']} in {ip['pathway']}: {agents_str}"
        )
    intervention_summary = "\n".join(intervention_lines) if intervention_lines else "None identified."

    # Build druggable target summary
    target_lines = []
    for dt in ctx.druggable_targets:
        drugs = ", ".join(m["drug"] for m in dt["modulators"])
        target_lines.append(f"  - {dt['target_name']} ({dt['gene_symbol']}): {drugs}")
    target_summary = "\n".join(target_lines) if target_lines else "None identified."

    return {
        "ae_type": ctx.ae_type,
        "pathway_summary": ctx.pathway_summary,
        "pathway_names": ctx.pathway_names,
        "biomarker_summary": biomarker_summary,
        "key_biomarkers": ctx.key_biomarkers,
        "target_summary": target_summary,
        "druggable_targets": ctx.druggable_targets,
        "intervention_summary": intervention_summary,
        "intervention_points": ctx.intervention_points,
        "feedback_loops": ctx.feedback_loops,
        "cell_types_involved": ctx.cell_types_involved,
        "risk_factors": ctx.risk_factors,
        "reference_pmids": ctx.reference_pmids,
        "reference_count": len(ctx.reference_pmids),
    }
