"""
Query functions over the cell therapy pathophysiology knowledge graph.

Provides a high-level API for querying pathways, intervention points,
mechanism chains, biomarker rationale, and molecular relationships across
all knowledge graph modules.

Usage::

    from src.data.knowledge.graph_queries import (
        get_pathway_for_ae,
        get_intervention_points,
        get_mechanism_chain,
        get_biomarker_rationale,
        search_by_molecule,
    )

    pathways = get_pathway_for_ae("CRS")
    interventions = get_intervention_points("ICANS")
    chain = get_mechanism_chain("CAR-T (CD19)", "Cytokine Release Syndrome")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.data.knowledge.pathways import (
    SignalingPathway,
    PathwayStep,
    PATHWAY_REGISTRY,
    get_pathways_for_ae,
    get_intervention_points_for_ae,
    get_feedback_loops_for_ae,
)
from src.data.knowledge.mechanisms import (
    MechanismChain,
    MechanismStep,
    TherapyModality,
    AECategory,
    MECHANISM_REGISTRY,
    get_mechanisms_for_therapy,
    get_mechanisms_for_ae,
)
from src.data.knowledge.molecular_targets import (
    MolecularTarget,
    Modulator,
    MOLECULAR_TARGET_REGISTRY,
    get_druggable_targets,
    get_targets_in_pathway,
)
from src.data.knowledge.cell_types import (
    CellTypeDefinition,
    CELL_TYPE_REGISTRY,
    get_cells_involved_in_ae,
)
from src.data.knowledge.references import (
    Reference,
    REFERENCES,
    get_references_by_tag,
)


# ---------------------------------------------------------------------------
# Result data structures
# ---------------------------------------------------------------------------

@dataclass
class PathwayGraph:
    """Result of a pathway query.

    Attributes:
        pathways: List of signaling pathways contributing to the AE.
        total_steps: Total number of mechanistic steps across all pathways.
        feedback_loops: All feedback loops identified.
        key_molecules: Key molecules involved.
        references: All PubMed IDs supporting the pathways.
    """

    pathways: list[SignalingPathway]
    total_steps: int
    feedback_loops: list[str]
    key_molecules: list[str]
    references: list[str]


@dataclass
class InterventionTarget:
    """A pharmacological intervention point.

    Attributes:
        step: The pathway step where intervention is possible.
        pathway_name: Name of the pathway containing this step.
        agents: Available intervention agents.
        target_molecule: The molecular target being modulated.
        mechanism_of_action: How the intervention works.
        evidence_refs: PubMed IDs supporting the intervention.
    """

    step: PathwayStep
    pathway_name: str
    agents: list[str]
    target_molecule: str
    mechanism_of_action: str
    evidence_refs: list[str]


@dataclass
class BiologicalRationale:
    """Biological rationale for a biomarker's clinical utility.

    Attributes:
        biomarker_name: Name of the biomarker.
        target: The molecular target definition.
        pathways: Pathways this biomarker participates in.
        upstream_drivers: What drives elevation of this biomarker.
        clinical_utility: How the biomarker is used clinically.
        normal_range: Normal reference range.
        ae_range: Range observed during adverse events.
        evidence_refs: PubMed IDs.
    """

    biomarker_name: str
    target: MolecularTarget | None
    pathways: list[str]
    upstream_drivers: list[str]
    clinical_utility: str
    normal_range: str
    ae_range: str
    evidence_refs: list[str]


@dataclass
class PathwayNode:
    """A node in a pathway search result.

    Attributes:
        node_id: Identifier.
        node_type: Type (e.g. "cytokine", "receptor", "cell_type").
        name: Human-readable name.
        pathways: Pathways this node appears in.
        connections: Other nodes this node connects to.
        references: PubMed IDs.
    """

    node_id: str
    node_type: str
    name: str
    pathways: list[str]
    connections: list[str]
    references: list[str]


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------

def get_pathway_for_ae(ae_type: str) -> PathwayGraph:
    """Get all signaling pathways that contribute to a given adverse event.

    Aggregates pathways, feedback loops, key molecules, and references.

    Args:
        ae_type: Adverse event type (e.g. "CRS", "ICANS", "HLH/MAS").

    Returns:
        PathwayGraph with aggregated pathway information.
    """
    pathways = get_pathways_for_ae(ae_type)
    total_steps = sum(len(pw.steps) for pw in pathways)
    feedback_loops = get_feedback_loops_for_ae(ae_type)

    # Collect unique molecules mentioned in pathway steps
    molecules: set[str] = set()
    refs: set[str] = set()
    for pw in pathways:
        for step in pw.steps:
            molecules.add(step.source)
            molecules.add(step.target)
            refs.update(step.references)
        refs.update(pw.key_references)

    return PathwayGraph(
        pathways=pathways,
        total_steps=total_steps,
        feedback_loops=feedback_loops,
        key_molecules=sorted(molecules),
        references=sorted(refs),
    )


def get_intervention_points(ae_type: str) -> list[InterventionTarget]:
    """Get all pharmacological intervention points for a given AE.

    For each interventable step, resolves the molecular target, agents,
    and mechanism of action from the molecular_targets registry.

    Args:
        ae_type: Adverse event type (e.g. "CRS", "ICANS", "HLH/MAS").

    Returns:
        List of InterventionTarget objects with actionable details.
    """
    results: list[InterventionTarget] = []
    pathways = get_pathways_for_ae(ae_type)

    for pw in pathways:
        for step in pw.steps:
            if not step.intervention_point:
                continue

            # Try to find the molecular target for this step
            target_mol = ""
            moa = step.mechanism
            refs: list[str] = list(step.references)

            # Search for matching molecular target
            for target in MOLECULAR_TARGET_REGISTRY.values():
                name_lower = target.name.lower()
                if (step.target.lower() in name_lower
                        or step.source.lower() in name_lower):
                    target_mol = target.name
                    if target.modulators:
                        moa = target.modulators[0].mechanism
                        for mod in target.modulators:
                            refs.extend(mod.evidence_refs)
                    break

            results.append(InterventionTarget(
                step=step,
                pathway_name=pw.name,
                agents=list(step.intervention_agents),
                target_molecule=target_mol,
                mechanism_of_action=moa,
                evidence_refs=refs,
            ))

    return results


def get_full_mechanism_chain(
    therapy_type: str,
    ae_type: str,
) -> list[MechanismStep]:
    """Get the step-by-step mechanism chain for a therapy-AE pair.

    Delegates to the mechanisms module.

    Args:
        therapy_type: Therapy modality string (e.g. "CAR-T (CD19)").
        ae_type: AE category string (e.g. "Cytokine Release Syndrome").

    Returns:
        Ordered list of MechanismStep objects.
    """
    from src.data.knowledge.mechanisms import get_mechanism_chain as _get_chain
    return _get_chain(therapy_type, ae_type)


def get_biomarker_rationale(biomarker: str) -> BiologicalRationale:
    """Get the biological rationale for why a biomarker is clinically useful.

    Links the biomarker to its upstream drivers, pathway membership, and
    clinical interpretation guidelines.

    Args:
        biomarker: Biomarker name or target ID (e.g. "CRP", "ferritin",
            "IL-6", "EASIX", "TARGET:CRP").

    Returns:
        BiologicalRationale with comprehensive explanation.
    """
    # Search for matching target
    target: MolecularTarget | None = None
    search_term = biomarker.lower()

    for t in MOLECULAR_TARGET_REGISTRY.values():
        if (search_term in t.name.lower()
                or search_term == t.target_id.lower()
                or search_term == t.gene_symbol.lower()):
            target = t
            break

    if target is None:
        return BiologicalRationale(
            biomarker_name=biomarker,
            target=None,
            pathways=[],
            upstream_drivers=[],
            clinical_utility="No matching target found in knowledge graph.",
            normal_range="Unknown",
            ae_range="Unknown",
            evidence_refs=[],
        )

    return BiologicalRationale(
        biomarker_name=target.name,
        target=target,
        pathways=list(target.pathways),
        upstream_drivers=list(target.downstream_of),
        clinical_utility=target.biomarker_utility or target.clinical_relevance,
        normal_range=target.normal_range,
        ae_range=target.ae_range,
        evidence_refs=list(target.references),
    )


def search_by_molecule(molecule: str) -> list[PathwayNode]:
    """Search the knowledge graph for all appearances of a molecule.

    Searches across molecular targets, cell types, pathways, and mechanisms
    for references to the given molecule name.

    Args:
        molecule: Molecule name to search for (e.g. "IL-6", "perforin",
            "Ang-2", "STAT3").

    Returns:
        List of PathwayNode objects representing the molecule's graph presence.
    """
    results: list[PathwayNode] = []
    search_lower = molecule.lower()

    # Search molecular targets
    for target in MOLECULAR_TARGET_REGISTRY.values():
        if (search_lower in target.name.lower()
                or search_lower == target.gene_symbol.lower()):
            connections: list[str] = []
            connections.extend(f"-> {u}" for u in target.upstream_of)
            connections.extend(f"<- {d}" for d in target.downstream_of)

            results.append(PathwayNode(
                node_id=target.target_id,
                node_type=target.category.value,
                name=target.name,
                pathways=list(target.pathways),
                connections=connections,
                references=list(target.references),
            ))

    # Search pathway steps
    for pw in PATHWAY_REGISTRY.values():
        for step in pw.steps:
            if (search_lower in step.source.lower()
                    or search_lower in step.target.lower()):
                results.append(PathwayNode(
                    node_id=f"{pw.pathway_id}:{step.source}->{step.target}",
                    node_type="pathway_step",
                    name=f"{step.source} --{step.relation.value}--> {step.target}",
                    pathways=[pw.name],
                    connections=[f"{step.source} -> {step.target}"],
                    references=list(step.references),
                ))

    # Search cell types for secreted factors
    for ct in CELL_TYPE_REGISTRY.values():
        for state in ct.activation_states:
            if search_lower in " ".join(state.secreted_factors).lower():
                results.append(PathwayNode(
                    node_id=f"{ct.cell_id}:{state.name}",
                    node_type="cell_type_secretion",
                    name=f"{ct.name} ({state.name}) secretes {molecule}",
                    pathways=[],
                    connections=[f"{ct.name} --secretes--> {molecule}"],
                    references=list(state.references),
                ))

    return results


def get_ae_overview(ae_type: str) -> dict[str, Any]:
    """Get a comprehensive overview of an adverse event across all modules.

    Aggregates pathways, mechanisms, cell types, biomarkers, interventions,
    and references for a given AE.

    Args:
        ae_type: Adverse event type (e.g. "CRS", "ICANS", "HLH").

    Returns:
        Dictionary with keys: pathways, mechanisms, cell_types, biomarkers,
        interventions, feedback_loops, references.
    """
    # Map common names to AE categories
    ae_map = {
        "CRS": "Cytokine Release Syndrome",
        "ICANS": "ICANS",
        "HLH": "HLH/MAS",
        "HLH/MAS": "HLH/MAS",
    }
    ae_full = ae_map.get(ae_type, ae_type)

    pathway_graph = get_pathway_for_ae(ae_type)
    interventions = get_intervention_points(ae_type)
    cell_types = get_cells_involved_in_ae(ae_type)

    # Find matching mechanisms
    mechanisms: list[MechanismChain] = []
    for mech in MECHANISM_REGISTRY.values():
        if mech.ae_category.value == ae_full or ae_type in mech.ae_category.value:
            mechanisms.append(mech)

    # Collect biomarker targets
    from src.data.knowledge.molecular_targets import TargetCategory
    biomarkers = [
        t for t in MOLECULAR_TARGET_REGISTRY.values()
        if t.category == TargetCategory.BIOMARKER
        and t.biomarker_utility
    ]

    # Collect all references
    all_refs: set[str] = set(pathway_graph.references)
    for mech in mechanisms:
        all_refs.update(mech.key_references)
    for ct in cell_types:
        all_refs.update(ct.references)

    return {
        "ae_type": ae_type,
        "pathways": [pw.name for pw in pathway_graph.pathways],
        "total_pathway_steps": pathway_graph.total_steps,
        "mechanisms": [m.name for m in mechanisms],
        "cell_types": [ct.name for ct in cell_types],
        "biomarkers": [b.name for b in biomarkers],
        "interventions": [
            {"agent": ", ".join(i.agents), "target": i.target_molecule}
            for i in interventions
        ],
        "feedback_loops": pathway_graph.feedback_loops,
        "references": sorted(all_refs),
        "reference_count": len(all_refs),
    }
