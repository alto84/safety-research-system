"""
Signaling pathways as directed graphs for cell therapy AE pathophysiology.

Each pathway is represented as a set of nodes (molecules, cells, processes)
connected by directed edges (activates, inhibits, produces, leads_to). Every
edge carries PubMed references and a confidence weight.

This module provides deeper mechanistic detail than crs_pathways.py, with
explicit temporal phases, feedback loop annotations, and intervention points.

Usage::

    from src.data.knowledge.pathways import PATHWAY_REGISTRY, get_pathway
    pathway = get_pathway("PW:IL6_TRANS_SIGNALING")
    for step in pathway.steps:
        print(f"{step.source} --{step.relation}--> {step.target}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Relation(Enum):
    """Types of relationships in signaling pathways."""

    ACTIVATES = "activates"
    INHIBITS = "inhibits"
    PRODUCES = "produces"
    BINDS = "binds"
    LEADS_TO = "leads_to"
    AMPLIFIES = "amplifies"
    RECRUITS = "recruits"
    CLEAVES = "cleaves"
    TRANSLOCATES_TO = "translocates_to"
    TRANSCRIBES = "transcribes"
    DIMERIZES_WITH = "dimerizes_with"
    SHEDS = "sheds"


class TemporalWindow(Enum):
    """Temporal windows relative to CAR-T infusion."""

    IMMEDIATE = "0-6h"
    EARLY = "6-24h"
    PEAK = "24-72h"
    SUSTAINED = "72h-7d"
    LATE = "7-14d"
    DELAYED = ">14d"


@dataclass(frozen=True)
class PathwayStep:
    """A single directed step in a signaling pathway.

    Attributes:
        source: Source entity (molecule, cell, or process).
        target: Target entity.
        relation: Type of relationship.
        mechanism: Mechanistic description of this step.
        confidence: Confidence weight (0.0-1.0) based on evidence strength.
        temporal_window: When this step typically occurs post-infusion.
        is_feedback_loop: Whether this step is part of a positive/negative
            feedback loop.
        intervention_point: Whether this step can be pharmacologically targeted.
        intervention_agents: Drugs that can interrupt this step.
        references: PubMed IDs supporting this step.
    """

    source: str
    target: str
    relation: Relation
    mechanism: str
    confidence: float = 0.9
    temporal_window: TemporalWindow = TemporalWindow.PEAK
    is_feedback_loop: bool = False
    intervention_point: bool = False
    intervention_agents: tuple[str, ...] = ()
    references: tuple[str, ...] = ()


@dataclass
class SignalingPathway:
    """A complete signaling pathway as a directed graph.

    Attributes:
        pathway_id: Unique identifier.
        name: Human-readable pathway name.
        description: Detailed biological description.
        steps: Ordered list of directed pathway steps.
        entry_points: Entities that initiate this pathway.
        exit_points: Terminal entities (clinical outcomes).
        feedback_loops: Descriptions of positive/negative feedback loops.
        intervention_summary: Summary of pharmacological intervention points.
        ae_outcomes: Adverse events this pathway contributes to.
        key_references: Primary references for the entire pathway.
    """

    pathway_id: str
    name: str
    description: str
    steps: list[PathwayStep] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    exit_points: list[str] = field(default_factory=list)
    feedback_loops: list[str] = field(default_factory=list)
    intervention_summary: str = ""
    ae_outcomes: list[str] = field(default_factory=list)
    key_references: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pathway 1: IL-6 Trans-Signaling Cascade (CRS core mechanism)
# ---------------------------------------------------------------------------

IL6_TRANS_SIGNALING = SignalingPathway(
    pathway_id="PW:IL6_TRANS_SIGNALING",
    name="IL-6 Trans-Signaling Cascade",
    description=(
        "The dominant pathological signaling mode in CRS. CAR-T cell activation "
        "releases IFN-gamma, which activates monocytes to produce IL-6. "
        "Simultaneously, neutrophil ADAM17 sheds membrane IL-6R to generate "
        "sIL-6R. The IL-6/sIL-6R complex binds ubiquitous gp130 on endothelial "
        "cells (which lack membrane IL-6R), activating JAK1/STAT3 and driving "
        "endothelial IL-6 production in a positive feedback loop. This trans-signaling "
        "mode is pro-inflammatory, distinct from classical IL-6 signaling which has "
        "regenerative/anti-inflammatory roles."
    ),
    steps=[
        PathwayStep(
            source="CAR-T_cell",
            target="target_cell",
            relation=Relation.BINDS,
            mechanism="CAR engages cognate antigen (e.g. CD19, BCMA) on target cell via scFv domain",
            confidence=0.95,
            temporal_window=TemporalWindow.IMMEDIATE,
            references=("PMID:27455965",),
        ),
        PathwayStep(
            source="CAR-T_cell",
            target="IFN-gamma",
            relation=Relation.PRODUCES,
            mechanism="CAR engagement triggers CD3-zeta and costimulatory domain (CD28/4-1BB) signaling, inducing IFN-gamma transcription and secretion. IFN-gamma is the earliest cytokine released.",
            confidence=0.95,
            temporal_window=TemporalWindow.EARLY,
            references=("PMID:27455965", "PMID:29643512"),
        ),
        PathwayStep(
            source="CAR-T_cell",
            target="GM-CSF",
            relation=Relation.PRODUCES,
            mechanism="Activated CAR-T cells secrete GM-CSF, which primes monocytes/macrophages for enhanced cytokine production.",
            confidence=0.80,
            temporal_window=TemporalWindow.EARLY,
            references=("PMID:37828045",),
        ),
        PathwayStep(
            source="target_cell",
            target="DAMPs",
            relation=Relation.PRODUCES,
            mechanism="Perforin/granzyme-mediated lysis of target cells releases damage-associated molecular patterns (HMGB1, ATP, uric acid).",
            confidence=0.85,
            temporal_window=TemporalWindow.EARLY,
            references=("PMID:29643511",),
        ),
        PathwayStep(
            source="IFN-gamma",
            target="monocyte",
            relation=Relation.ACTIVATES,
            mechanism="IFN-gamma binds IFNGR on monocytes, activating JAK1/JAK2 and STAT1, inducing inflammatory gene program.",
            confidence=0.95,
            temporal_window=TemporalWindow.EARLY,
            references=("PMID:29643512",),
        ),
        PathwayStep(
            source="monocyte",
            target="IL-6",
            relation=Relation.PRODUCES,
            mechanism="Activated monocytes are the PRIMARY source of IL-6 in CRS (Norelli et al., 2018). NF-kB and STAT3 drive IL6 transcription.",
            confidence=0.95,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29643512",),
        ),
        PathwayStep(
            source="monocyte",
            target="IL-1beta",
            relation=Relation.PRODUCES,
            mechanism="NLRP3 inflammasome activation in monocytes processes pro-IL-1beta to active IL-1beta. IL-1beta is upstream of IL-6 in the cascade.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29643512", "PMID:29643511"),
        ),
        PathwayStep(
            source="neutrophil",
            target="sIL-6R",
            relation=Relation.SHEDS,
            mechanism="ADAM17 metalloproteinase on activated neutrophils cleaves membrane-bound IL-6R ectodomain, generating soluble IL-6R (sIL-6R). Neutrophil activation precedes clinical CRS.",
            confidence=0.85,
            temporal_window=TemporalWindow.EARLY,
            references=("PMID:38123583", "PMID:30442748"),
        ),
        PathwayStep(
            source="IL-6",
            target="sIL-6R",
            relation=Relation.BINDS,
            mechanism="IL-6 binds sIL-6R in the circulation, forming the IL-6/sIL-6R binary complex. This complex is the active trans-signaling ligand.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:30442748",),
        ),
        PathwayStep(
            source="IL-6/sIL-6R_complex",
            target="gp130",
            relation=Relation.DIMERIZES_WITH,
            mechanism="IL-6/sIL-6R binary complex induces gp130 homodimerization on endothelial cells, which ubiquitously express gp130 but lack membrane IL-6R.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:30442748", "PMID:33168950"),
        ),
        PathwayStep(
            source="gp130_dimer",
            target="JAK1/JAK2",
            relation=Relation.ACTIVATES,
            mechanism="gp130 homodimer activates constitutively associated JAK1 and JAK2 kinases via transphosphorylation.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:38123583",),
        ),
        PathwayStep(
            source="JAK1",
            target="STAT3",
            relation=Relation.ACTIVATES,
            mechanism="Activated JAK1 phosphorylates STAT3 on Y705. Phospho-STAT3 dimerizes and translocates to the nucleus.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:38123583",),
        ),
        PathwayStep(
            source="STAT3",
            target="IL-6_gene",
            relation=Relation.TRANSCRIBES,
            mechanism="Nuclear STAT3 binds the IL6 promoter, driving IL-6 transcription. This creates a POSITIVE FEEDBACK LOOP: IL-6 -> gp130 -> JAK/STAT3 -> more IL-6.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            is_feedback_loop=True,
            references=("PMID:30442748",),
        ),
        PathwayStep(
            source="endothelial_cell",
            target="IL-6",
            relation=Relation.PRODUCES,
            mechanism="Activated endothelial cells produce additional IL-6, VEGF, IL-8, MCP-1, and PAI-1, amplifying the inflammatory cascade.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            is_feedback_loop=True,
            references=("PMID:30442748", "PMID:29025771"),
        ),
        PathwayStep(
            source="IL-6",
            target="CRP",
            relation=Relation.PRODUCES,
            mechanism="IL-6/STAT3 signaling in hepatocytes drives CRP transcription as part of the acute phase response.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:28854140",),
        ),
        PathwayStep(
            source="IL-6",
            target="CRS",
            relation=Relation.LEADS_TO,
            mechanism="Systemic IL-6 elevation causes fever (hypothalamic PGE2), hypotension (vascular leak, NO), and hypoxia (pulmonary capillary leak).",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            intervention_point=True,
            intervention_agents=("tocilizumab", "siltuximab"),
            references=("PMID:30275568", "PMID:29084955"),
        ),
    ],
    entry_points=["CAR-T_cell", "target_cell"],
    exit_points=["CRS", "CRP"],
    feedback_loops=[
        "STAT3 positive feedback: IL-6 -> gp130 -> JAK1 -> STAT3 -> IL6 gene -> IL-6 (self-amplifying)",
        "Endothelial amplification: IL-6 trans-signaling activates endothelium -> endothelium produces more IL-6, VEGF, IL-8",
        "NF-kB loop: TNF-alpha -> TNFR1 -> NF-kB -> TNF, IL-6, IL-1beta gene transcription",
    ],
    intervention_summary=(
        "Tocilizumab (anti-IL-6R) blocks both classical and trans-signaling by preventing IL-6 from engaging gp130. "
        "Siltuximab (anti-IL-6) directly neutralizes circulating IL-6. Anakinra (IL-1Ra) blocks IL-1beta upstream of IL-6. "
        "Ruxolitinib (JAK1/2 inhibitor) blocks downstream signaling. Corticosteroids (dexamethasone) inhibit NF-kB."
    ),
    ae_outcomes=["CRS"],
    key_references=["PMID:29643512", "PMID:30442748", "PMID:38123583", "PMID:27455965"],
)


# ---------------------------------------------------------------------------
# Pathway 2: BBB Disruption and ICANS
# ---------------------------------------------------------------------------

BBB_DISRUPTION_ICANS = SignalingPathway(
    pathway_id="PW:BBB_DISRUPTION_ICANS",
    name="Blood-Brain Barrier Disruption and ICANS",
    description=(
        "ICANS results from convergent mechanisms disrupting the BBB: (1) cytokine-driven "
        "endothelial activation releasing Ang-2 and destabilizing pericyte-endothelial "
        "junctions; (2) direct on-target/off-tumor killing of CD19+ brain pericytes by "
        "CD19 CAR-T cells; (3) CNS cytokine infiltration through the disrupted BBB; "
        "(4) reactive astrocytosis and kynurenine pathway activation producing neurotoxic "
        "quinolinic acid (glutamate excitotoxicity). ICANS typically follows CRS onset "
        "by 1-3 days but can occur independently."
    ),
    steps=[
        PathwayStep(
            source="systemic_cytokines",
            target="CNS_endothelium",
            relation=Relation.ACTIVATES,
            mechanism="IL-6 (via trans-signaling), TNF-alpha, IFN-gamma, and IL-1beta activate CNS endothelial cells.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29025771",),
        ),
        PathwayStep(
            source="CNS_endothelium",
            target="Ang-2",
            relation=Relation.PRODUCES,
            mechanism="Weibel-Palade body exocytosis releases stored Ang-2 and vWF. Ang-2 is a competitive antagonist of Ang-1 at the Tie2 receptor.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29025771",),
        ),
        PathwayStep(
            source="Ang-2",
            target="pericyte_Tie2",
            relation=Relation.INHIBITS,
            mechanism="Ang-2 displaces Ang-1 from Tie2 on pericytes. Loss of Ang-1/Tie2 signaling causes pericyte detachment from the microvasculature.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29025771",),
        ),
        PathwayStep(
            source="CD19_CAR-T",
            target="CD19+_pericyte",
            relation=Relation.ACTIVATES,
            mechanism="Brain mural cells (pericytes) express CD19 at low levels. CD19 CAR-T cells directly target and lyse these pericytes, providing an on-target/off-tumor mechanism for BBB disruption.",
            confidence=0.75,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:33082430", "PMID:37798640"),
        ),
        PathwayStep(
            source="pericyte_loss",
            target="BBB_permeability",
            relation=Relation.LEADS_TO,
            mechanism="Combined pericyte detachment (Ang-2) and pericyte lysis (CAR-T) disrupts the neurovascular unit. Tight junction proteins (claudin-5, occludin) are downregulated.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:37798640",),
        ),
        PathwayStep(
            source="BBB_permeability",
            target="CNS_cytokine_infiltration",
            relation=Relation.LEADS_TO,
            mechanism="Systemic cytokines (IFN-gamma, IL-6, TNF-alpha) cross the disrupted BBB into the brain parenchyma.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:29025771", "PMID:30154262"),
        ),
        PathwayStep(
            source="CNS_cytokines",
            target="astrocyte",
            relation=Relation.ACTIVATES,
            mechanism="IFN-gamma and TNF-alpha induce reactive astrocytosis. Activated astrocytes upregulate IDO (indoleamine 2,3-dioxygenase), entering the kynurenine pathway.",
            confidence=0.80,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:31204436", "PMID:30154262"),
        ),
        PathwayStep(
            source="astrocyte_IDO",
            target="quinolinic_acid",
            relation=Relation.PRODUCES,
            mechanism="IDO converts tryptophan to kynurenine, which is further metabolized to quinolinic acid (QA) by activated microglia/macrophages. QA is an NMDA receptor agonist.",
            confidence=0.75,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:30154262",),
        ),
        PathwayStep(
            source="quinolinic_acid",
            target="NMDA_receptor",
            relation=Relation.ACTIVATES,
            mechanism="Quinolinic acid activates NMDA receptors on neurons, causing calcium influx and glutamate excitotoxicity.",
            confidence=0.70,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:30154262",),
        ),
        PathwayStep(
            source="glutamate_excitotoxicity",
            target="ICANS",
            relation=Relation.LEADS_TO,
            mechanism="Neuronal excitotoxicity manifests as encephalopathy, aphasia, tremor, seizures, and in severe cases, fatal cerebral edema.",
            confidence=0.75,
            temporal_window=TemporalWindow.SUSTAINED,
            intervention_point=True,
            intervention_agents=("dexamethasone", "anti-seizure_prophylaxis"),
            references=("PMID:30275568",),
        ),
    ],
    entry_points=["systemic_cytokines", "CD19_CAR-T"],
    exit_points=["ICANS"],
    feedback_loops=[
        "Neuroinflammatory amplification: CNS cytokines -> reactive astrocytosis -> GFAP/S100b release -> further BBB disruption",
    ],
    intervention_summary=(
        "Dexamethasone is first-line for ICANS grade >= 2 (crosses BBB, reduces endothelial activation and neuroinflammation). "
        "Anti-seizure prophylaxis (levetiracetam) for grade >= 2. Tocilizumab is less effective for ICANS (does not cross intact BBB). "
        "Anakinra may help (IL-1 protected against neurotoxicity in preclinical models)."
    ),
    ae_outcomes=["ICANS"],
    key_references=["PMID:29025771", "PMID:33082430", "PMID:30154262", "PMID:37798640"],
)


# ---------------------------------------------------------------------------
# Pathway 3: HLH/MAS Hyperinflammation
# ---------------------------------------------------------------------------

HLH_MAS_PATHWAY = SignalingPathway(
    pathway_id="PW:HLH_MAS",
    name="Hemophagocytic Lymphohistiocytosis / Macrophage Activation Syndrome",
    description=(
        "CAR-T-associated HLH (carHLH or IEC-HS) represents the extreme end of "
        "macrophage hyperactivation. Sustained IFN-gamma from CAR-T cells drives "
        "uncontrolled macrophage activation, hemophagocytosis, and an IFN-gamma/IL-18 "
        "positive feedback loop. Distinct from CRS: HLH features ferritin >10,000, "
        "cytopenias, hepatic dysfunction, and coagulopathy that persist AFTER CRS "
        "resolution. Impaired NK cell perforin/granzyme function (failure to eliminate "
        "hyperactivated macrophages) sustains the syndrome."
    ),
    steps=[
        PathwayStep(
            source="CAR-T_cell",
            target="IFN-gamma",
            relation=Relation.PRODUCES,
            mechanism="Sustained, high-level IFN-gamma production from persistently activated CAR-T cells. Higher and more prolonged than in CRS alone.",
            confidence=0.90,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:39134524",),
        ),
        PathwayStep(
            source="IFN-gamma",
            target="macrophage",
            relation=Relation.ACTIVATES,
            mechanism="IFN-gamma drives classical (M1) macrophage activation via IFNGR/JAK/STAT1 signaling, transitioning to hemophagocytic phenotype at high concentrations.",
            confidence=0.95,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:29643511", "PMID:39338775"),
        ),
        PathwayStep(
            source="macrophage",
            target="IL-18",
            relation=Relation.PRODUCES,
            mechanism="Hyperactivated macrophages secrete IL-18 via inflammasome-mediated processing. IL-18 is a key differentiator of HLH from CRS.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:39134524", "PMID:39338775"),
        ),
        PathwayStep(
            source="IL-18",
            target="IFN-gamma",
            relation=Relation.AMPLIFIES,
            mechanism="IL-18 potently stimulates IFN-gamma production from T cells and NK cells, creating a POSITIVE FEEDBACK LOOP: IFN-gamma -> macrophage -> IL-18 -> more IFN-gamma.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            is_feedback_loop=True,
            references=("PMID:39134524",),
        ),
        PathwayStep(
            source="macrophage",
            target="ferritin",
            relation=Relation.PRODUCES,
            mechanism="Hemophagocytic macrophages secrete massive quantities of ferritin (>10,000 ng/mL). Ferritin is both a biomarker and a potential inflammatory mediator.",
            confidence=0.90,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:36906275",),
        ),
        PathwayStep(
            source="macrophage",
            target="hemophagocytosis",
            relation=Relation.LEADS_TO,
            mechanism="Hyperactivated macrophages engulf blood cells (erythrocytes, platelets, leukocytes) in bone marrow, spleen, and liver sinusoids.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:36906275", "PMID:34263927"),
        ),
        PathwayStep(
            source="NK_cell",
            target="perforin/granzyme",
            relation=Relation.PRODUCES,
            mechanism="NK cells normally regulate macrophage numbers via perforin/granzyme-mediated killing. In HLH, impaired NK cytotoxicity (functional or absolute) permits uncontrolled macrophage expansion.",
            confidence=0.80,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:39338775",),
        ),
        PathwayStep(
            source="impaired_NK_function",
            target="macrophage_expansion",
            relation=Relation.LEADS_TO,
            mechanism="Failure to clear hyperactivated macrophages sustains the hemophagocytic state and cytokine storm.",
            confidence=0.80,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:39338775",),
        ),
        PathwayStep(
            source="hemophagocytosis",
            target="coagulopathy",
            relation=Relation.LEADS_TO,
            mechanism="Platelet consumption by hemophagocytosis plus tissue factor expression drives DIC with falling fibrinogen and rising D-dimer.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            references=("PMID:36906275",),
        ),
        PathwayStep(
            source="macrophage_activation",
            target="HLH/MAS",
            relation=Relation.LEADS_TO,
            mechanism="Multi-organ failure from cytokine storm, hemophagocytosis, coagulopathy, and hepatic dysfunction. Mortality 20-50% if untreated.",
            confidence=0.85,
            temporal_window=TemporalWindow.SUSTAINED,
            intervention_point=True,
            intervention_agents=("anakinra", "ruxolitinib", "emapalumab", "etoposide"),
            references=("PMID:36906275", "PMID:34263927"),
        ),
    ],
    entry_points=["CAR-T_cell", "IFN-gamma"],
    exit_points=["HLH/MAS"],
    feedback_loops=[
        "IFN-gamma/IL-18 amplification loop: IFN-gamma -> macrophage -> IL-18 -> IFN-gamma (positive feedback sustaining hyperinflammation)",
        "CXCL9/CXCL10 chemokine loop: IFN-gamma -> CXCL9/CXCL10 -> T-cell/NK-cell recruitment -> more IFN-gamma",
    ],
    intervention_summary=(
        "Anakinra (IL-1Ra): blocks upstream IL-1beta and may interrupt macrophage activation. "
        "Ruxolitinib (JAK1/2i): blocks IFN-gamma and IL-6 downstream signaling. "
        "Emapalumab (anti-IFN-gamma): directly neutralizes the primary driver. "
        "Etoposide: cytotoxic elimination of hyperactivated macrophages (last resort). "
        "Corticosteroids: broad immunosuppression but less effective alone."
    ),
    ae_outcomes=["HLH/MAS"],
    key_references=["PMID:36906275", "PMID:34263927", "PMID:39134524", "PMID:39338775"],
)


# ---------------------------------------------------------------------------
# Pathway 4: TNF-alpha / NF-kB Amplification
# ---------------------------------------------------------------------------

TNF_NFKB_AMPLIFICATION = SignalingPathway(
    pathway_id="PW:TNF_NFKB",
    name="TNF-alpha / NF-kB Inflammatory Amplification",
    description=(
        "TNF-alpha released by activated CAR-T cells and macrophages signals through "
        "TNFR1 to activate NF-kB, a master inflammatory transcription factor. NF-kB "
        "drives transcription of TNF, IL-6, IL-1beta, IL-8 (CXCL8), and MCP-1 (CCL2). "
        "MCP-1 recruits additional monocytes, amplifying the feedforward loop."
    ),
    steps=[
        PathwayStep(
            source="TNF-alpha",
            target="TNFR1",
            relation=Relation.BINDS,
            mechanism="TNF-alpha trimerizes TNFR1, recruiting TRADD and TRAF2 to the death domain.",
            confidence=0.90,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29084955",),
        ),
        PathwayStep(
            source="TNFR1",
            target="NF-kB",
            relation=Relation.ACTIVATES,
            mechanism="TRADD/TRAF2 complex activates IKK, which phosphorylates IkB-alpha for proteasomal degradation, releasing NF-kB for nuclear translocation.",
            confidence=0.85,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29084955",),
        ),
        PathwayStep(
            source="NF-kB",
            target="TNF_gene",
            relation=Relation.TRANSCRIBES,
            mechanism="NF-kB binds the TNF promoter, driving autocrine TNF-alpha production (positive feedback).",
            confidence=0.80,
            temporal_window=TemporalWindow.PEAK,
            is_feedback_loop=True,
            intervention_point=True,
            intervention_agents=("dexamethasone",),
            references=("PMID:29084955",),
        ),
        PathwayStep(
            source="NF-kB",
            target="IL6_gene",
            relation=Relation.TRANSCRIBES,
            mechanism="NF-kB drives IL-6 transcription, converging with the STAT3-driven IL-6 loop.",
            confidence=0.80,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29084955",),
        ),
        PathwayStep(
            source="NF-kB",
            target="MCP-1",
            relation=Relation.TRANSCRIBES,
            mechanism="NF-kB drives MCP-1 (CCL2) transcription. MCP-1 is a potent monocyte chemoattractant.",
            confidence=0.75,
            temporal_window=TemporalWindow.PEAK,
            references=("PMID:29084955",),
        ),
        PathwayStep(
            source="MCP-1",
            target="monocyte_recruitment",
            relation=Relation.RECRUITS,
            mechanism="MCP-1 gradient recruits circulating monocytes to sites of inflammation, providing fresh IL-6-producing cells and amplifying the cytokine storm.",
            confidence=0.80,
            temporal_window=TemporalWindow.PEAK,
            is_feedback_loop=True,
            references=("PMID:29643512",),
        ),
    ],
    entry_points=["TNF-alpha"],
    exit_points=["CRS"],
    feedback_loops=[
        "TNF-alpha/NF-kB autocrine loop: TNF-alpha -> TNFR1 -> NF-kB -> TNF gene -> more TNF-alpha",
        "Monocyte recruitment loop: NF-kB -> MCP-1 -> monocyte recruitment -> more IL-6/TNF-alpha production",
    ],
    intervention_summary="Corticosteroids (dexamethasone) inhibit NF-kB nuclear translocation.",
    ae_outcomes=["CRS"],
    key_references=["PMID:29084955"],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# Known pathway coverage gaps (future work):
#   - B-cell aplasia / hypogammaglobulinemia: the most common long-term
#     CD19 CAR-T toxicity (100% incidence).  A mechanism chain exists
#     (CART_CD19_B_CELL_APLASIA) but no signaling pathway is modelled yet.
#   - Prolonged cytopenias: ~30% of SLE patients; mechanism involves
#     hematopoietic stem cell niche disruption and sustained inflammation.
#   - Infection complications: ~12.8% in SLE cohorts, secondary to B-cell
#     aplasia and prolonged neutropenia.  Requires immunodeficiency pathway.
#   - T-cell lymphoma: recently identified FDA safety signal (Nov 2023);
#     monitored in FAERS but lacks a mechanistic pathway model.

PATHWAY_REGISTRY: dict[str, SignalingPathway] = {
    pw.pathway_id: pw for pw in [
        IL6_TRANS_SIGNALING,
        BBB_DISRUPTION_ICANS,
        HLH_MAS_PATHWAY,
        TNF_NFKB_AMPLIFICATION,
    ]
}


def get_pathway(pathway_id: str) -> SignalingPathway | None:
    """Look up a signaling pathway by ID.

    Args:
        pathway_id: Pathway identifier (e.g. "PW:IL6_TRANS_SIGNALING").

    Returns:
        The SignalingPathway, or None if not found.
    """
    return PATHWAY_REGISTRY.get(pathway_id)


def get_pathways_for_ae(ae_type: str) -> list[SignalingPathway]:
    """Return all pathways that contribute to a given adverse event.

    Args:
        ae_type: Adverse event type (e.g. "CRS", "ICANS", "HLH/MAS").

    Returns:
        List of SignalingPathway objects.
    """
    return [
        pw for pw in PATHWAY_REGISTRY.values()
        if ae_type in pw.ae_outcomes
    ]


def get_intervention_points_for_ae(ae_type: str) -> list[PathwayStep]:
    """Return all intervention points (pharmacologically targetable steps)
    in pathways contributing to a given AE.

    Args:
        ae_type: Adverse event type.

    Returns:
        List of PathwayStep objects where intervention_point is True.
    """
    results: list[PathwayStep] = []
    for pw in get_pathways_for_ae(ae_type):
        results.extend(s for s in pw.steps if s.intervention_point)
    return results


def get_feedback_loops_for_ae(ae_type: str) -> list[str]:
    """Return descriptions of all feedback loops in pathways for a given AE.

    Args:
        ae_type: Adverse event type.

    Returns:
        List of feedback loop description strings.
    """
    loops: list[str] = []
    for pw in get_pathways_for_ae(ae_type):
        loops.extend(pw.feedback_loops)
    return loops
