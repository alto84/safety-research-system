"""
Cell populations involved in cell therapy adverse event pathogenesis.

Defines the key cell types, their activation states, surface markers, secreted
factors, and roles in CRS, ICANS, and HLH/MAS. Each cell type records its
tissue of origin, lineage, known activation triggers, and downstream effects.

Data sourced from:
    - Norelli et al., Nat Med 2018 (PMID:29643512)
    - Giavridis et al., Nat Med 2018 (PMID:29643511)
    - Gust et al., Cancer Discov 2017 (PMID:29025771)
    - Parker et al., Blood 2020 (PMID:33082430)
    - Chen et al., J Hematol Oncol 2024 (PMID:39338775)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ActivationState:
    """Describes a specific activation state of a cell type.

    Attributes:
        name: Short name for the state (e.g. "M1_polarized").
        description: Biological description.
        triggers: Signals that induce this state.
        secreted_factors: Cytokines/chemokines produced in this state.
        surface_markers: Upregulated surface markers.
        functional_outcome: What the cell does in this state.
        references: PubMed IDs supporting this state description.
    """

    name: str
    description: str
    triggers: tuple[str, ...]
    secreted_factors: tuple[str, ...]
    surface_markers: tuple[str, ...] = ()
    functional_outcome: str = ""
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class CellTypeDefinition:
    """A cell population involved in cell therapy AE pathogenesis.

    Attributes:
        cell_id: Unique identifier (e.g. "CELL:MACROPHAGE").
        name: Human-readable name.
        lineage: Hematopoietic lineage (e.g. "myeloid", "lymphoid").
        tissue: Primary tissue location.
        surface_markers: Canonical surface markers for identification.
        activation_states: Known activation states relevant to AE biology.
        roles_in_ae: AE types this cell contributes to and how.
        secreted_factors_baseline: Factors produced at baseline.
        references: PubMed IDs for general cell biology.
    """

    cell_id: str
    name: str
    lineage: str
    tissue: str
    surface_markers: tuple[str, ...]
    activation_states: tuple[ActivationState, ...]
    roles_in_ae: dict[str, str]
    secreted_factors_baseline: tuple[str, ...] = ()
    references: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Cell type definitions
# ---------------------------------------------------------------------------

CAR_T_CELL = CellTypeDefinition(
    cell_id="CELL:CAR_T",
    name="CAR-T Cell",
    lineage="lymphoid",
    tissue="blood",
    surface_markers=("CD3", "CAR_transgene", "CD4_or_CD8"),
    activation_states=(
        ActivationState(
            name="antigen_engaged",
            description="CAR recognizes target antigen on tumor/target cell, triggering activation signals through CD3-zeta and costimulatory domains (CD28 or 4-1BB).",
            triggers=("target_antigen_binding",),
            secreted_factors=("IFN-gamma", "TNF-alpha", "IL-2", "GM-CSF", "perforin", "granzyme_B"),
            surface_markers=("CD69", "CD25", "CD137", "PD-1"),
            functional_outcome="Target cell cytolysis via perforin/granzyme pathway; release of DAMPs from lysed targets; bystander activation of monocytes/macrophages via IFN-gamma.",
            references=("PMID:27455965", "PMID:37828045"),
        ),
        ActivationState(
            name="exhausted",
            description="Prolonged antigen stimulation leads to upregulation of inhibitory receptors and progressive loss of effector function.",
            triggers=("chronic_antigen_exposure", "tonic_signaling"),
            secreted_factors=("IL-10",),
            surface_markers=("PD-1", "LAG-3", "TIM-3", "TIGIT"),
            functional_outcome="Reduced cytotoxicity and cytokine production; may limit late CRS but also reduces efficacy.",
            references=(),
        ),
    ),
    roles_in_ae={
        "CRS": "Initiates the cascade by releasing IFN-gamma and TNF-alpha upon antigen engagement; IFN-gamma activates bystander monocytes/macrophages which produce IL-6.",
        "ICANS": "Indirect role via cytokine production that activates endothelium and disrupts BBB; possible direct CNS infiltration.",
        "HLH": "Sustained IFN-gamma production drives uncontrolled macrophage activation.",
    },
    secreted_factors_baseline=(),
    references=("PMID:27455965", "PMID:29643512", "PMID:37828045"),
)


MONOCYTE = CellTypeDefinition(
    cell_id="CELL:MONOCYTE",
    name="Monocyte",
    lineage="myeloid",
    tissue="blood",
    surface_markers=("CD14", "CD16", "CD11b", "HLA-DR"),
    activation_states=(
        ActivationState(
            name="ifn_gamma_activated",
            description="IFN-gamma from CAR-T cells activates circulating monocytes, which become the primary source of IL-6 in CRS.",
            triggers=("IFN-gamma", "GM-CSF", "TNF-alpha"),
            secreted_factors=("IL-6", "IL-1beta", "TNF-alpha", "IL-10", "MCP-1", "IL-8"),
            surface_markers=("CD80", "CD86", "HLA-DR_upregulated"),
            functional_outcome="Primary source of IL-6 driving CRS; IL-1beta production upstream of IL-6; chemokine secretion recruits additional monocytes.",
            references=("PMID:29643512",),
        ),
    ),
    roles_in_ae={
        "CRS": "Primary source of IL-6 production in CRS (Norelli et al., 2018); also produces IL-1beta which is upstream of IL-6.",
        "HLH": "Differentiates into tissue macrophages that become hyperactivated hemophagocytes.",
    },
    secreted_factors_baseline=("IL-10",),
    references=("PMID:29643512", "PMID:29643511"),
)


MACROPHAGE = CellTypeDefinition(
    cell_id="CELL:MACROPHAGE",
    name="Macrophage",
    lineage="myeloid",
    tissue="multiple",
    surface_markers=("CD68", "CD163", "CD14", "CD11b"),
    activation_states=(
        ActivationState(
            name="m1_classically_activated",
            description="IFN-gamma-driven classical activation producing pro-inflammatory cytokines. The dominant macrophage state in CRS.",
            triggers=("IFN-gamma", "GM-CSF", "LPS", "TNF-alpha"),
            secreted_factors=("IL-6", "IL-1beta", "TNF-alpha", "IL-12", "IL-18", "ROS", "NO"),
            surface_markers=("iNOS", "CD80", "CD86", "MHC-II_high"),
            functional_outcome="Massive cytokine production driving CRS; antigen presentation; tissue damage via ROS/NO.",
            references=("PMID:29643511",),
        ),
        ActivationState(
            name="hemophagocytic",
            description="Hyperactivated macrophages engulfing blood cells (hemophagocytosis). The hallmark of HLH/MAS.",
            triggers=("IFN-gamma_high", "IL-18", "GM-CSF", "impaired_NK_regulation"),
            secreted_factors=("ferritin", "IL-6", "IL-18", "TNF-alpha", "IL-1beta", "CXCL9", "CXCL10"),
            surface_markers=("CD163_high", "CD25_soluble", "CD68"),
            functional_outcome="Hemophagocytosis (engulfing erythrocytes, platelets, leukocytes); ferritin hypersecretion (>10000 ng/mL); consumptive coagulopathy.",
            references=("PMID:36906275", "PMID:39277881"),
        ),
    ),
    roles_in_ae={
        "CRS": "Major amplifier of cytokine storm; recipient macrophages (not CAR-T cells) mediate CRS (Giavridis et al., 2018).",
        "HLH": "Central effector cell; hyperactivated macrophages perform hemophagocytosis and produce extreme ferritin, driving multi-organ failure.",
        "ICANS": "Tissue-resident CNS macrophages (microglia) contribute to neuroinflammation.",
    },
    secreted_factors_baseline=("IL-10", "TGF-beta"),
    references=("PMID:29643511", "PMID:36906275", "PMID:39338775"),
)


ENDOTHELIAL_CELL = CellTypeDefinition(
    cell_id="CELL:ENDOTHELIAL",
    name="Endothelial Cell",
    lineage="mesenchymal",
    tissue="vasculature",
    surface_markers=("CD31", "CD34", "vWF", "VE-cadherin"),
    activation_states=(
        ActivationState(
            name="activated",
            description="Cytokine-driven endothelial activation with Weibel-Palade body exocytosis, releasing Ang-2 and vWF. Loss of barrier function.",
            triggers=("IL-6_trans_signaling", "TNF-alpha", "IFN-gamma", "IL-1beta"),
            secreted_factors=("Ang-2", "vWF", "IL-6", "IL-8", "MCP-1", "VEGF", "PAI-1"),
            surface_markers=("E-selectin", "ICAM-1", "VCAM-1"),
            functional_outcome="Vascular leak syndrome; disruption of tight junctions; BBB breakdown in CNS vasculature; DIC via tissue factor expression.",
            references=("PMID:29025771", "PMID:30442748"),
        ),
    ),
    roles_in_ae={
        "CRS": "Amplifies cytokine production through IL-6 trans-signaling (endothelial cells lack membrane IL-6R, activated via sIL-6R/gp130); vascular leak causes hypotension and hypoxia.",
        "ICANS": "CNS endothelial activation is the primary mechanism of BBB disruption; Ang-2 release destabilizes pericyte-endothelial interactions.",
        "DIC": "Endothelial activation triggers tissue factor expression and coagulation cascade activation.",
    },
    secreted_factors_baseline=("Ang-1", "NO"),
    references=("PMID:29025771", "PMID:30442748", "PMID:37798640"),
)


NK_CELL = CellTypeDefinition(
    cell_id="CELL:NK",
    name="Natural Killer Cell",
    lineage="innate_lymphoid",
    tissue="blood",
    surface_markers=("CD56", "CD16", "NKG2D", "KIR"),
    activation_states=(
        ActivationState(
            name="activated",
            description="Activated NK cells produce IFN-gamma and perform cytolysis via perforin/granzyme. In CAR-NK therapy, lower CRS risk than CAR-T.",
            triggers=("IL-15", "IL-12", "IL-18", "missing_self_KIR_mismatch"),
            secreted_factors=("IFN-gamma", "TNF-alpha", "perforin", "granzyme_B"),
            surface_markers=("CD69", "NKG2D_upregulated"),
            functional_outcome="Target cell lysis via perforin/granzyme; IFN-gamma production (less sustained than T cells, contributing to lower CRS risk).",
            references=("PMID:32433173",),
        ),
        ActivationState(
            name="impaired_cytotoxicity",
            description="Dysfunctional NK cells with reduced perforin/granzyme secretion. Contributes to HLH pathogenesis by failing to clear activated macrophages.",
            triggers=("chronic_inflammation", "TGF-beta", "IL-10"),
            secreted_factors=(),
            functional_outcome="Failure to regulate macrophage activation through cytotoxic elimination; permits uncontrolled macrophage expansion and hemophagocytosis.",
            references=("PMID:39338775",),
        ),
    ),
    roles_in_ae={
        "CRS": "In CAR-NK therapy, lower CRS risk due to shorter persistence and different cytokine profile; IFN-gamma production is less sustained.",
        "HLH": "Impaired NK cytotoxicity (defective perforin pathway) is a central mechanism in familial HLH and contributes to CAR-T-associated HLH.",
    },
    secreted_factors_baseline=(),
    references=("PMID:32433173", "PMID:39338775"),
)


BRAIN_PERICYTE = CellTypeDefinition(
    cell_id="CELL:PERICYTE",
    name="Brain Pericyte",
    lineage="mesenchymal",
    tissue="CNS_vasculature",
    surface_markers=("PDGFR-beta", "NG2", "CD146", "CD19_low"),
    activation_states=(
        ActivationState(
            name="targeted_by_cd19_cart",
            description="Brain pericytes express CD19 at low levels, making them a direct on-target/off-tumor target for CD19 CAR-T cells.",
            triggers=("CD19_CAR-T_binding",),
            secreted_factors=(),
            functional_outcome="Pericyte damage and detachment from CNS microvasculature leads to BBB disruption independent of systemic cytokine storm.",
            references=("PMID:33082430", "PMID:37798640"),
        ),
        ActivationState(
            name="ang2_detached",
            description="Ang-2 released from activated endothelium antagonizes Tie2 on pericytes, causing detachment from the microvasculature.",
            triggers=("Ang-2",),
            secreted_factors=(),
            functional_outcome="Loss of pericyte coverage increases BBB permeability and allows systemic cytokine CNS infiltration.",
            references=("PMID:29025771",),
        ),
    ),
    roles_in_ae={
        "ICANS": "Dual mechanism: (1) direct on-target/off-tumor killing by CD19 CAR-T cells; (2) Ang-2-mediated detachment. Both disrupt the BBB.",
    },
    secreted_factors_baseline=(),
    references=("PMID:33082430", "PMID:37798640", "PMID:29025771"),
)


ASTROCYTE = CellTypeDefinition(
    cell_id="CELL:ASTROCYTE",
    name="Astrocyte",
    lineage="neuroectoderm",
    tissue="CNS",
    surface_markers=("GFAP", "S100b", "aquaporin-4"),
    activation_states=(
        ActivationState(
            name="reactive",
            description="Reactive astrocytosis in response to BBB disruption and CNS cytokine infiltration. Contributes to cerebral edema and neuronal excitotoxicity.",
            triggers=("TNF-alpha", "IL-6", "IL-1beta", "IFN-gamma"),
            secreted_factors=("GFAP", "S100b", "quinolinic_acid", "glutamate"),
            surface_markers=("GFAP_upregulated",),
            functional_outcome="Release of GFAP and S100b (CSF biomarkers of ICANS severity); kynurenine pathway activation producing neurotoxic quinolinic acid; impaired glutamate reuptake causing excitotoxicity.",
            references=("PMID:31204436", "PMID:30154262"),
        ),
    ),
    roles_in_ae={
        "ICANS": "Reactive astrocytosis amplifies neuroinflammation; impaired glutamate reuptake causes NMDA receptor-mediated excitotoxicity; kynurenine pathway metabolites (quinolinic acid) are neurotoxic.",
    },
    secreted_factors_baseline=(),
    references=("PMID:31204436", "PMID:30154262"),
)


NEUTROPHIL = CellTypeDefinition(
    cell_id="CELL:NEUTROPHIL",
    name="Neutrophil",
    lineage="myeloid",
    tissue="blood",
    surface_markers=("CD66b", "CD15", "CD11b", "CD16"),
    activation_states=(
        ActivationState(
            name="early_activated",
            description="Neutrophils activate early in CRS, preceding monocyte/macrophage activation and cytokine peak. Source of sIL-6R via metalloproteinase shedding.",
            triggers=("GM-CSF", "IL-8", "complement"),
            secreted_factors=("sIL-6R", "IL-8", "elastase", "MPO"),
            surface_markers=("CD11b_upregulated", "CD62L_shed"),
            functional_outcome="Shedding of membrane IL-6R generates sIL-6R, enabling IL-6 trans-signaling on endothelial cells; early activation marker before clinical CRS onset.",
            references=("PMID:38123583",),
        ),
    ),
    roles_in_ae={
        "CRS": "Early sentinel cells; neutrophil activation precedes CRS symptoms. Critical source of sIL-6R through ADAM17-mediated ectodomain shedding, enabling pathological trans-signaling.",
    },
    secreted_factors_baseline=(),
    references=("PMID:38123583",),
)


DENDRITIC_CELL = CellTypeDefinition(
    cell_id="CELL:DENDRITIC",
    name="Dendritic Cell",
    lineage="myeloid",
    tissue="lymphoid_organs",
    surface_markers=("CD11c", "MHC-II", "CD80", "CD86"),
    activation_states=(
        ActivationState(
            name="matured",
            description="IFN-gamma-matured dendritic cells enhance antigen presentation and amplify T-cell activation, contributing to the feedforward loop.",
            triggers=("IFN-gamma", "TNF-alpha", "GM-CSF"),
            secreted_factors=("IL-12", "IL-15", "IL-6"),
            surface_markers=("CD83", "CCR7"),
            functional_outcome="Enhanced antigen presentation; IL-12 production activates NK cells; IL-15 supports T-cell and NK-cell survival.",
            references=(),
        ),
    ),
    roles_in_ae={
        "CRS": "Amplifies T-cell activation through enhanced antigen presentation and IL-12 production.",
    },
    secreted_factors_baseline=(),
    references=(),
)


# ---------------------------------------------------------------------------
# Aggregated registry
# ---------------------------------------------------------------------------

CELL_TYPE_REGISTRY: dict[str, CellTypeDefinition] = {
    ct.cell_id: ct for ct in [
        CAR_T_CELL, MONOCYTE, MACROPHAGE, ENDOTHELIAL_CELL,
        NK_CELL, BRAIN_PERICYTE, ASTROCYTE, NEUTROPHIL, DENDRITIC_CELL,
    ]
}


def get_cell_type(cell_id: str) -> CellTypeDefinition | None:
    """Look up a cell type definition by ID.

    Args:
        cell_id: Cell identifier (e.g. "CELL:MACROPHAGE").

    Returns:
        The CellTypeDefinition, or None if not found.
    """
    return CELL_TYPE_REGISTRY.get(cell_id)


def get_cells_involved_in_ae(ae_type: str) -> list[CellTypeDefinition]:
    """Return all cell types that have a documented role in a given AE.

    Args:
        ae_type: Adverse event type (e.g. "CRS", "ICANS", "HLH").

    Returns:
        List of CellTypeDefinition objects with roles in the specified AE.
    """
    return [ct for ct in CELL_TYPE_REGISTRY.values() if ae_type in ct.roles_in_ae]
