"""
Pre-built CRS, ICANS, and HLH mechanism definitions.

Contains curated pathway definitions based on published literature describing
the mechanistic biology of cell therapy toxicities. These pathways can be
loaded into the KnowledgeGraph to enable mechanism validation and hypothesis
generation.

Key references:
    - Lee et al., Biol Blood Marrow Transplant, 2019 (ASTCT consensus grading)
    - Norelli et al., Nature Medicine, 2018 (monocyte-derived IL-6 in CRS)
    - Giavridis et al., Nature Medicine, 2018 (macrophage activation in CRS)
    - Gust et al., Cancer Discovery, 2017 (endothelial activation in ICANS)
    - Teachey et al., Cancer Discovery, 2016 (cytokine kinetics in CRS)
"""

from __future__ import annotations

from src.data.graph.schema import (
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
    PathwayDefinition,
    TemporalPhase,
)


# ---------------------------------------------------------------------------
# Shared node definitions (reused across pathways)
# ---------------------------------------------------------------------------

# Cell types
_CAR_T_CELL = GraphNode(
    node_id="CELL:CAR_T",
    node_type=NodeType.CELL_TYPE,
    name="CAR-T Cell",
    properties={"lineage": "T lymphocyte", "engineered": True},
)
_MONOCYTE = GraphNode(
    node_id="CELL:MONOCYTE",
    node_type=NodeType.CELL_TYPE,
    name="Monocyte",
    properties={"lineage": "myeloid"},
)
_MACROPHAGE = GraphNode(
    node_id="CELL:MACROPHAGE",
    node_type=NodeType.CELL_TYPE,
    name="Macrophage",
    properties={"lineage": "myeloid"},
)
_ENDOTHELIAL_CELL = GraphNode(
    node_id="CELL:ENDOTHELIAL",
    node_type=NodeType.CELL_TYPE,
    name="Endothelial Cell",
    properties={"tissue": "vascular"},
)
_TUMOR_CELL = GraphNode(
    node_id="CELL:TUMOR",
    node_type=NodeType.CELL_TYPE,
    name="Tumor Cell (CD19+)",
    properties={"antigen": "CD19"},
)
_NK_CELL = GraphNode(
    node_id="CELL:NK",
    node_type=NodeType.CELL_TYPE,
    name="Natural Killer Cell",
    properties={"lineage": "innate lymphoid"},
)
_ASTROCYTE = GraphNode(
    node_id="CELL:ASTROCYTE",
    node_type=NodeType.CELL_TYPE,
    name="Astrocyte",
    properties={"tissue": "CNS"},
)
_PERICYTE = GraphNode(
    node_id="CELL:PERICYTE",
    node_type=NodeType.CELL_TYPE,
    name="Brain Pericyte",
    properties={"tissue": "CNS vasculature"},
)
_DENDRITIC_CELL = GraphNode(
    node_id="CELL:DENDRITIC",
    node_type=NodeType.CELL_TYPE,
    name="Dendritic Cell",
    properties={"lineage": "myeloid"},
)

# Cytokines
_IL6 = GraphNode(
    node_id="CYTOKINE:IL6",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-6 (IL-6)",
    properties={
        "gene": "IL6",
        "normal_range_pg_ml": (0, 7),
        "crs_peak_pg_ml": (100, 100_000),
        "half_life_hours": 2.5,
    },
)
_TNF_ALPHA = GraphNode(
    node_id="CYTOKINE:TNF_ALPHA",
    node_type=NodeType.CYTOKINE,
    name="Tumor Necrosis Factor-alpha (TNF-a)",
    properties={
        "gene": "TNF",
        "normal_range_pg_ml": (0, 8.1),
        "crs_peak_pg_ml": (10, 5_000),
    },
)
_IFN_GAMMA = GraphNode(
    node_id="CYTOKINE:IFN_GAMMA",
    node_type=NodeType.CYTOKINE,
    name="Interferon-gamma (IFN-g)",
    properties={
        "gene": "IFNG",
        "normal_range_pg_ml": (0, 15.6),
        "crs_peak_pg_ml": (500, 50_000),
    },
)
_IL1_BETA = GraphNode(
    node_id="CYTOKINE:IL1_BETA",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-1 beta (IL-1b)",
    properties={"gene": "IL1B", "normal_range_pg_ml": (0, 5)},
)
_IL2 = GraphNode(
    node_id="CYTOKINE:IL2",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-2 (IL-2)",
    properties={"gene": "IL2", "normal_range_pg_ml": (0, 31)},
)
_IL8 = GraphNode(
    node_id="CYTOKINE:IL8",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-8 (IL-8 / CXCL8)",
    properties={"gene": "CXCL8"},
)
_IL10 = GraphNode(
    node_id="CYTOKINE:IL10",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-10 (IL-10)",
    properties={"gene": "IL10", "role": "anti-inflammatory"},
)
_IL15 = GraphNode(
    node_id="CYTOKINE:IL15",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-15 (IL-15)",
    properties={"gene": "IL15"},
)
_IL18 = GraphNode(
    node_id="CYTOKINE:IL18",
    node_type=NodeType.CYTOKINE,
    name="Interleukin-18 (IL-18)",
    properties={"gene": "IL18"},
)
_MCP1 = GraphNode(
    node_id="CYTOKINE:MCP1",
    node_type=NodeType.CYTOKINE,
    name="Monocyte Chemoattractant Protein-1 (MCP-1 / CCL2)",
    properties={"gene": "CCL2"},
)
_GM_CSF = GraphNode(
    node_id="CYTOKINE:GM_CSF",
    node_type=NodeType.CYTOKINE,
    name="GM-CSF",
    properties={"gene": "CSF2"},
)
_PERFORIN = GraphNode(
    node_id="PROTEIN:PERFORIN",
    node_type=NodeType.PROTEIN,
    name="Perforin",
    properties={"gene": "PRF1"},
)
_GRANZYME_B = GraphNode(
    node_id="PROTEIN:GRANZYME_B",
    node_type=NodeType.PROTEIN,
    name="Granzyme B",
    properties={"gene": "GZMB"},
)

# Receptors
_IL6R = GraphNode(
    node_id="RECEPTOR:IL6R",
    node_type=NodeType.RECEPTOR,
    name="IL-6 Receptor (IL-6R / CD126)",
    properties={"gene": "IL6R", "type": "membrane-bound"},
)
_SIL6R = GraphNode(
    node_id="RECEPTOR:SIL6R",
    node_type=NodeType.RECEPTOR,
    name="Soluble IL-6 Receptor (sIL-6R)",
    properties={"gene": "IL6R", "type": "soluble", "enables_trans_signaling": True},
)
_GP130 = GraphNode(
    node_id="RECEPTOR:GP130",
    node_type=NodeType.RECEPTOR,
    name="Glycoprotein 130 (gp130)",
    properties={"gene": "IL6ST", "role": "signal transduction"},
)
_TNFR1 = GraphNode(
    node_id="RECEPTOR:TNFR1",
    node_type=NodeType.RECEPTOR,
    name="TNF Receptor 1 (TNFR1)",
    properties={"gene": "TNFRSF1A"},
)
_IFNGR = GraphNode(
    node_id="RECEPTOR:IFNGR",
    node_type=NodeType.RECEPTOR,
    name="IFN-gamma Receptor",
    properties={"gene": "IFNGR1"},
)
_CD19_ANTIGEN = GraphNode(
    node_id="RECEPTOR:CD19",
    node_type=NodeType.RECEPTOR,
    name="CD19 (tumor antigen)",
    properties={"gene": "CD19"},
)

# Signaling proteins
_STAT3 = GraphNode(
    node_id="PROTEIN:STAT3",
    node_type=NodeType.PROTEIN,
    name="STAT3",
    properties={"gene": "STAT3", "type": "transcription factor"},
)
_JAK1 = GraphNode(
    node_id="PROTEIN:JAK1",
    node_type=NodeType.PROTEIN,
    name="JAK1",
    properties={"gene": "JAK1", "type": "kinase"},
)
_JAK2 = GraphNode(
    node_id="PROTEIN:JAK2",
    node_type=NodeType.PROTEIN,
    name="JAK2",
    properties={"gene": "JAK2", "type": "kinase"},
)
_NFKB = GraphNode(
    node_id="PROTEIN:NFKB",
    node_type=NodeType.PROTEIN,
    name="NF-kB",
    properties={"gene": "NFKB1", "type": "transcription factor"},
)
_ANG2 = GraphNode(
    node_id="PROTEIN:ANG2",
    node_type=NodeType.PROTEIN,
    name="Angiopoietin-2 (Ang-2)",
    properties={"gene": "ANGPT2", "role": "vascular destabilizer"},
)
_VEGF = GraphNode(
    node_id="PROTEIN:VEGF",
    node_type=NodeType.PROTEIN,
    name="Vascular Endothelial Growth Factor (VEGF)",
    properties={"gene": "VEGFA"},
)
_VWF = GraphNode(
    node_id="PROTEIN:VWF",
    node_type=NodeType.PROTEIN,
    name="Von Willebrand Factor (vWF)",
    properties={"gene": "VWF", "role": "endothelial activation marker"},
)
_FERRITIN = GraphNode(
    node_id="BIOMARKER:FERRITIN",
    node_type=NodeType.BIOMARKER,
    name="Ferritin",
    properties={"normal_range_ng_ml": (12, 300), "hlh_threshold_ng_ml": 10_000},
)
_CRP = GraphNode(
    node_id="BIOMARKER:CRP",
    node_type=NodeType.BIOMARKER,
    name="C-Reactive Protein (CRP)",
    properties={"normal_range_mg_l": (0, 10), "crs_elevation": True},
)
_D_DIMER = GraphNode(
    node_id="BIOMARKER:D_DIMER",
    node_type=NodeType.BIOMARKER,
    name="D-dimer",
    properties={"normal_range_mg_l": (0, 0.5), "role": "coagulopathy marker"},
)
_FIBRINOGEN = GraphNode(
    node_id="BIOMARKER:FIBRINOGEN",
    node_type=NodeType.BIOMARKER,
    name="Fibrinogen",
    properties={"normal_range_mg_dl": (200, 400)},
)
_LDH = GraphNode(
    node_id="BIOMARKER:LDH",
    node_type=NodeType.BIOMARKER,
    name="Lactate Dehydrogenase (LDH)",
    properties={"normal_range_u_l": (140, 280)},
)
_SOLUBLE_CD25 = GraphNode(
    node_id="BIOMARKER:SCD25",
    node_type=NodeType.BIOMARKER,
    name="Soluble CD25 (sIL-2Ra)",
    properties={"gene": "IL2RA"},
)

# Genes (key transcriptional regulators)
_IL6_GENE = GraphNode(
    node_id="GENE:IL6",
    node_type=NodeType.GENE,
    name="IL6 Gene",
    properties={"chromosome": "7p15.3"},
)
_TNF_GENE = GraphNode(
    node_id="GENE:TNF",
    node_type=NodeType.GENE,
    name="TNF Gene",
    properties={"chromosome": "6p21.33"},
)
_IFNG_GENE = GraphNode(
    node_id="GENE:IFNG",
    node_type=NodeType.GENE,
    name="IFNG Gene",
    properties={"chromosome": "12q15"},
)

# Adverse events
_CRS_EVENT = GraphNode(
    node_id="AE:CRS",
    node_type=NodeType.ADVERSE_EVENT,
    name="Cytokine Release Syndrome (CRS)",
    properties={
        "typical_onset_days": (1, 7),
        "grading_system": "ASTCT",
        "max_grade": 5,
    },
)
_ICANS_EVENT = GraphNode(
    node_id="AE:ICANS",
    node_type=NodeType.ADVERSE_EVENT,
    name="Immune effector Cell-Associated Neurotoxicity Syndrome (ICANS)",
    properties={
        "typical_onset_days": (2, 10),
        "grading_system": "ASTCT",
        "assessment_tool": "ICE score",
    },
)
_HLH_EVENT = GraphNode(
    node_id="AE:HLH",
    node_type=NodeType.ADVERSE_EVENT,
    name="Hemophagocytic Lymphohistiocytosis (HLH/MAS)",
    properties={
        "typical_onset_days": (3, 14),
        "also_known_as": "Macrophage Activation Syndrome",
    },
)

# Drugs (interventions)
_TOCILIZUMAB = GraphNode(
    node_id="DRUG:TOCILIZUMAB",
    node_type=NodeType.DRUG,
    name="Tocilizumab (anti-IL-6R)",
    properties={"mechanism": "IL-6R blockade", "route": "IV"},
)
_SILTUXIMAB = GraphNode(
    node_id="DRUG:SILTUXIMAB",
    node_type=NodeType.DRUG,
    name="Siltuximab (anti-IL-6)",
    properties={"mechanism": "IL-6 neutralization", "route": "IV"},
)
_DEXAMETHASONE = GraphNode(
    node_id="DRUG:DEXAMETHASONE",
    node_type=NodeType.DRUG,
    name="Dexamethasone",
    properties={"mechanism": "broad immunosuppression", "route": "IV/PO"},
)
_ANAKINRA = GraphNode(
    node_id="DRUG:ANAKINRA",
    node_type=NodeType.DRUG,
    name="Anakinra (IL-1Ra)",
    properties={"mechanism": "IL-1 receptor antagonist", "route": "SC/IV"},
)
_RUXOLITINIB = GraphNode(
    node_id="DRUG:RUXOLITINIB",
    node_type=NodeType.DRUG,
    name="Ruxolitinib (JAK1/2 inhibitor)",
    properties={"mechanism": "JAK1/JAK2 inhibition", "route": "PO"},
)

# Organs
_BRAIN = GraphNode(
    node_id="ORGAN:BRAIN",
    node_type=NodeType.ORGAN,
    name="Brain",
)
_LUNG = GraphNode(
    node_id="ORGAN:LUNG",
    node_type=NodeType.ORGAN,
    name="Lung",
)
_LIVER = GraphNode(
    node_id="ORGAN:LIVER",
    node_type=NodeType.ORGAN,
    name="Liver",
)
_VASCULATURE = GraphNode(
    node_id="ORGAN:VASCULATURE",
    node_type=NodeType.ORGAN,
    name="Vasculature",
)

# Clinical signs
_FEVER = GraphNode(
    node_id="SIGN:FEVER",
    node_type=NodeType.CLINICAL_SIGN,
    name="Fever (>=38C)",
)
_HYPOTENSION = GraphNode(
    node_id="SIGN:HYPOTENSION",
    node_type=NodeType.CLINICAL_SIGN,
    name="Hypotension",
)
_HYPOXIA = GraphNode(
    node_id="SIGN:HYPOXIA",
    node_type=NodeType.CLINICAL_SIGN,
    name="Hypoxia",
)
_CEREBRAL_EDEMA = GraphNode(
    node_id="SIGN:CEREBRAL_EDEMA",
    node_type=NodeType.CLINICAL_SIGN,
    name="Cerebral Edema",
)
_COAGULOPATHY = GraphNode(
    node_id="SIGN:COAGULOPATHY",
    node_type=NodeType.CLINICAL_SIGN,
    name="Coagulopathy / DIC",
)
_ENCEPHALOPATHY = GraphNode(
    node_id="SIGN:ENCEPHALOPATHY",
    node_type=NodeType.CLINICAL_SIGN,
    name="Encephalopathy",
)
_APHASIA = GraphNode(
    node_id="SIGN:APHASIA",
    node_type=NodeType.CLINICAL_SIGN,
    name="Aphasia",
)
_SEIZURE = GraphNode(
    node_id="SIGN:SEIZURE",
    node_type=NodeType.CLINICAL_SIGN,
    name="Seizure",
)


# ---------------------------------------------------------------------------
# Pathway 1: IL-6 Classical & Trans-Signaling in CRS
# ---------------------------------------------------------------------------

def build_il6_signaling_pathway() -> PathwayDefinition:
    """IL-6 signaling cascade -- the dominant driver of CRS.

    Classical signaling: IL-6 binds membrane IL-6R on hepatocytes and some
    leukocytes, forming a complex with gp130 that activates JAK/STAT3.

    Trans-signaling: IL-6 binds soluble IL-6R (shed from neutrophils) and the
    complex activates gp130 on endothelial cells and other cells lacking
    membrane IL-6R. This is the primary pathological mechanism in CRS.
    """
    pathway_node = GraphNode(
        node_id="PATHWAY:IL6_SIGNALING",
        node_type=NodeType.PATHWAY,
        name="IL-6 Classical & Trans-Signaling",
        properties={
            "reference": "Norelli et al., Nature Medicine, 2018",
            "key_insight": "Monocyte-derived IL-6 is the primary driver of CRS",
        },
    )

    nodes = [
        _CAR_T_CELL, _TUMOR_CELL, _MONOCYTE, _MACROPHAGE, _ENDOTHELIAL_CELL,
        _IL6, _IFN_GAMMA, _TNF_ALPHA, _IL1_BETA, _MCP1,
        _IL6R, _SIL6R, _GP130,
        _JAK1, _JAK2, _STAT3, _NFKB,
        _IL6_GENE, _CRP, _FERRITIN,
        _CRS_EVENT, _FEVER, _HYPOTENSION,
        _TOCILIZUMAB, _SILTUXIMAB,
        pathway_node,
    ]

    edges = [
        # CAR-T recognition and activation
        GraphEdge("CELL:CAR_T", "RECEPTOR:CD19", EdgeType.BINDS, 0.95,
                  {"step": "CAR engages CD19 on tumor"}),
        GraphEdge("CELL:CAR_T", "CYTOKINE:IFN_GAMMA", EdgeType.SECRETES, 0.90,
                  {"timing_hours": (2, 24)}),
        GraphEdge("CELL:CAR_T", "CYTOKINE:TNF_ALPHA", EdgeType.SECRETES, 0.85,
                  {"timing_hours": (2, 24)}),
        GraphEdge("CELL:CAR_T", "CYTOKINE:GM_CSF", EdgeType.SECRETES, 0.80),

        # IFN-gamma activates monocytes/macrophages
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:MONOCYTE", EdgeType.ACTIVATES, 0.90,
                  {"mechanism": "IFNGR signaling"}),
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:MACROPHAGE", EdgeType.ACTIVATES, 0.90),
        GraphEdge("CYTOKINE:TNF_ALPHA", "CELL:MACROPHAGE", EdgeType.ACTIVATES, 0.80),

        # Monocytes/macrophages produce IL-6 (the CRS driver)
        GraphEdge("CELL:MONOCYTE", "CYTOKINE:IL6", EdgeType.SECRETES, 0.95,
                  {"key_finding": "primary source of IL-6 in CRS"}),
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:IL6", EdgeType.SECRETES, 0.90),
        GraphEdge("CELL:MONOCYTE", "CYTOKINE:IL1_BETA", EdgeType.SECRETES, 0.85),
        GraphEdge("CELL:MONOCYTE", "CYTOKINE:TNF_ALPHA", EdgeType.SECRETES, 0.80),
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:MCP1", EdgeType.SECRETES, 0.75),

        # IL-6 classical signaling (via membrane IL-6R)
        GraphEdge("CYTOKINE:IL6", "RECEPTOR:IL6R", EdgeType.BINDS, 0.90,
                  {"signaling_mode": "classical"}),
        GraphEdge("RECEPTOR:IL6R", "RECEPTOR:GP130", EdgeType.ACTIVATES, 0.95),

        # IL-6 trans-signaling (via soluble IL-6R on endothelium)
        GraphEdge("CYTOKINE:IL6", "RECEPTOR:SIL6R", EdgeType.BINDS, 0.85,
                  {"signaling_mode": "trans", "pathological": True}),
        GraphEdge("RECEPTOR:SIL6R", "RECEPTOR:GP130", EdgeType.ACTIVATES, 0.90,
                  {"target_cells": "endothelial, lacking membrane IL-6R"}),

        # Downstream JAK/STAT signaling
        GraphEdge("RECEPTOR:GP130", "PROTEIN:JAK1", EdgeType.ACTIVATES, 0.90),
        GraphEdge("RECEPTOR:GP130", "PROTEIN:JAK2", EdgeType.ACTIVATES, 0.85),
        GraphEdge("PROTEIN:JAK1", "PROTEIN:STAT3", EdgeType.ACTIVATES, 0.90),
        GraphEdge("PROTEIN:STAT3", "GENE:IL6", EdgeType.REGULATES, 0.80,
                  {"effect": "positive feedback -- STAT3 upregulates IL-6 transcription"}),

        # NF-kB activation (TNF-alpha and IL-1beta arms)
        GraphEdge("CYTOKINE:TNF_ALPHA", "RECEPTOR:TNFR1", EdgeType.BINDS, 0.90),
        GraphEdge("RECEPTOR:TNFR1", "PROTEIN:NFKB", EdgeType.ACTIVATES, 0.85),
        GraphEdge("PROTEIN:NFKB", "GENE:IL6", EdgeType.REGULATES, 0.80,
                  {"effect": "NF-kB drives IL-6 transcription"}),
        GraphEdge("PROTEIN:NFKB", "GENE:TNF", EdgeType.REGULATES, 0.80),

        # Gene transcription
        GraphEdge("GENE:IL6", "CYTOKINE:IL6", EdgeType.TRANSCRIBES, 0.95),
        GraphEdge("GENE:TNF", "CYTOKINE:TNF_ALPHA", EdgeType.TRANSCRIBES, 0.90),

        # Positive feedback loop (amplification)
        GraphEdge("CYTOKINE:IL6", "CYTOKINE:IL6", EdgeType.AMPLIFIES, 0.75,
                  {"mechanism": "STAT3-mediated transcriptional positive feedback"}),

        # Acute phase response
        GraphEdge("CYTOKINE:IL6", "BIOMARKER:CRP", EdgeType.CAUSES, 0.90,
                  {"mechanism": "hepatic acute phase response"}),
        GraphEdge("CYTOKINE:IL6", "BIOMARKER:FERRITIN", EdgeType.CAUSES, 0.80),

        # Clinical manifestations
        GraphEdge("CYTOKINE:IL6", "AE:CRS", EdgeType.TRIGGERS, 0.90),
        GraphEdge("CYTOKINE:TNF_ALPHA", "AE:CRS", EdgeType.TRIGGERS, 0.75),
        GraphEdge("AE:CRS", "SIGN:FEVER", EdgeType.MANIFESTS_AS, 0.95),
        GraphEdge("AE:CRS", "SIGN:HYPOTENSION", EdgeType.MANIFESTS_AS, 0.70),
        GraphEdge("AE:CRS", "SIGN:HYPOXIA", EdgeType.MANIFESTS_AS, 0.50),

        # Biomarker indications
        GraphEdge("BIOMARKER:CRP", "AE:CRS", EdgeType.INDICATES, 0.85),
        GraphEdge("BIOMARKER:FERRITIN", "AE:CRS", EdgeType.INDICATES, 0.75),

        # Drug interventions
        GraphEdge("DRUG:TOCILIZUMAB", "RECEPTOR:IL6R", EdgeType.TARGETS, 0.95),
        GraphEdge("DRUG:TOCILIZUMAB", "AE:CRS", EdgeType.TREATS, 0.85,
                  {"line": "first-line for grade >= 2"}),
        GraphEdge("DRUG:SILTUXIMAB", "CYTOKINE:IL6", EdgeType.TARGETS, 0.90),
        GraphEdge("DRUG:SILTUXIMAB", "AE:CRS", EdgeType.TREATS, 0.80),

        # Pathway membership
        GraphEdge("CYTOKINE:IL6", "PATHWAY:IL6_SIGNALING", EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("PROTEIN:STAT3", "PATHWAY:IL6_SIGNALING", EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("PROTEIN:JAK1", "PATHWAY:IL6_SIGNALING", EdgeType.PARTICIPATES_IN, 1.0),
    ]

    return PathwayDefinition(
        pathway_id="PATHWAY:IL6_SIGNALING",
        name="IL-6 Classical & Trans-Signaling in CRS",
        description=(
            "Monocyte- and macrophage-derived IL-6 drives CRS through both "
            "classical (membrane IL-6R) and trans (soluble IL-6R + gp130) "
            "signaling, activating JAK1/STAT3 and creating a positive feedback "
            "loop that amplifies cytokine production."
        ),
        nodes=nodes,
        edges=edges,
        temporal_phase=TemporalPhase.PEAK_PHASE,
        adverse_events=["AE:CRS"],
    )


# ---------------------------------------------------------------------------
# Pathway 2: Endothelial Activation (ICANS)
# ---------------------------------------------------------------------------

def build_endothelial_activation_pathway() -> PathwayDefinition:
    """Endothelial activation and blood-brain barrier disruption in ICANS.

    High cytokine levels -- especially IL-6, TNF-alpha, and IFN-gamma --
    activate endothelial cells, causing Ang-2 release, vWF secretion, and
    increased vascular permeability. In the CNS, this disrupts the blood-brain
    barrier and allows cytokines to enter the brain parenchyma.
    """
    pathway_node = GraphNode(
        node_id="PATHWAY:ENDOTHELIAL_ACTIVATION",
        node_type=NodeType.PATHWAY,
        name="Endothelial Activation & BBB Disruption",
        properties={
            "reference": "Gust et al., Cancer Discovery, 2017",
            "key_insight": "Endothelial activation precedes and predicts ICANS",
        },
    )

    nodes = [
        _ENDOTHELIAL_CELL, _ASTROCYTE, _PERICYTE,
        _IL6, _TNF_ALPHA, _IFN_GAMMA, _IL1_BETA,
        _ANG2, _VEGF, _VWF,
        _NFKB,
        _ICANS_EVENT, _BRAIN, _VASCULATURE,
        _CEREBRAL_EDEMA, _ENCEPHALOPATHY, _APHASIA, _SEIZURE,
        _DEXAMETHASONE, _TOCILIZUMAB,
        pathway_node,
    ]

    edges = [
        # Cytokines activate endothelium
        GraphEdge("CYTOKINE:IL6", "CELL:ENDOTHELIAL", EdgeType.ACTIVATES, 0.85,
                  {"mechanism": "IL-6 trans-signaling via sIL-6R/gp130"}),
        GraphEdge("CYTOKINE:TNF_ALPHA", "CELL:ENDOTHELIAL", EdgeType.ACTIVATES, 0.90),
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:ENDOTHELIAL", EdgeType.ACTIVATES, 0.80),
        GraphEdge("CYTOKINE:IL1_BETA", "CELL:ENDOTHELIAL", EdgeType.ACTIVATES, 0.75),

        # Endothelial cells release Weibel-Palade body contents
        GraphEdge("CELL:ENDOTHELIAL", "PROTEIN:ANG2", EdgeType.SECRETES, 0.90,
                  {"mechanism": "Weibel-Palade body exocytosis"}),
        GraphEdge("CELL:ENDOTHELIAL", "PROTEIN:VWF", EdgeType.SECRETES, 0.85),
        GraphEdge("CELL:ENDOTHELIAL", "PROTEIN:VEGF", EdgeType.PRODUCES, 0.70),

        # Ang-2 destabilizes vasculature
        GraphEdge("PROTEIN:ANG2", "ORGAN:VASCULATURE", EdgeType.AFFECTS, 0.85,
                  {"effect": "increased permeability, pericyte detachment"}),
        GraphEdge("PROTEIN:ANG2", "CELL:PERICYTE", EdgeType.INHIBITS, 0.75,
                  {"effect": "pericyte detachment from CNS microvasculature"}),

        # BBB disruption
        GraphEdge("CELL:ENDOTHELIAL", "ORGAN:BRAIN", EdgeType.AFFECTS, 0.80,
                  {"effect": "blood-brain barrier disruption"}),
        GraphEdge("CYTOKINE:IL6", "ORGAN:BRAIN", EdgeType.AFFECTS, 0.70,
                  {"mechanism": "crosses disrupted BBB"}),
        GraphEdge("CYTOKINE:TNF_ALPHA", "CELL:ASTROCYTE", EdgeType.ACTIVATES, 0.75,
                  {"mechanism": "reactive astrocytosis"}),

        # Clinical consequences
        GraphEdge("PROTEIN:ANG2", "AE:ICANS", EdgeType.TRIGGERS, 0.80),
        GraphEdge("CYTOKINE:IL6", "AE:ICANS", EdgeType.TRIGGERS, 0.70),
        GraphEdge("AE:ICANS", "ORGAN:BRAIN", EdgeType.AFFECTS, 0.95),
        GraphEdge("AE:ICANS", "SIGN:CEREBRAL_EDEMA", EdgeType.MANIFESTS_AS, 0.40,
                  {"note": "rare but fatal complication"}),
        GraphEdge("AE:ICANS", "SIGN:ENCEPHALOPATHY", EdgeType.MANIFESTS_AS, 0.85),
        GraphEdge("AE:ICANS", "SIGN:APHASIA", EdgeType.MANIFESTS_AS, 0.60),
        GraphEdge("AE:ICANS", "SIGN:SEIZURE", EdgeType.MANIFESTS_AS, 0.25),

        # Upstream pathway linkage
        GraphEdge("PATHWAY:IL6_SIGNALING", "PATHWAY:ENDOTHELIAL_ACTIVATION",
                  EdgeType.UPSTREAM_OF, 0.90),

        # Drug interventions
        GraphEdge("DRUG:DEXAMETHASONE", "AE:ICANS", EdgeType.TREATS, 0.80,
                  {"line": "first-line for ICANS grade >= 2"}),
        GraphEdge("DRUG:DEXAMETHASONE", "CELL:ENDOTHELIAL", EdgeType.INHIBITS, 0.70,
                  {"mechanism": "reduces endothelial activation"}),

        # Pathway membership
        GraphEdge("PROTEIN:ANG2", "PATHWAY:ENDOTHELIAL_ACTIVATION",
                  EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("PROTEIN:VWF", "PATHWAY:ENDOTHELIAL_ACTIVATION",
                  EdgeType.PARTICIPATES_IN, 1.0),
    ]

    return PathwayDefinition(
        pathway_id="PATHWAY:ENDOTHELIAL_ACTIVATION",
        name="Endothelial Activation & BBB Disruption (ICANS)",
        description=(
            "Pro-inflammatory cytokines (IL-6, TNF-a, IFN-g) activate vascular "
            "endothelium, triggering Ang-2 and vWF release from Weibel-Palade "
            "bodies. This increases vascular permeability, disrupts the blood-brain "
            "barrier, and permits cytokine entry into the CNS, driving ICANS."
        ),
        nodes=nodes,
        edges=edges,
        temporal_phase=TemporalPhase.PEAK_PHASE,
        adverse_events=["AE:ICANS"],
    )


# ---------------------------------------------------------------------------
# Pathway 3: Macrophage Activation (HLH/MAS)
# ---------------------------------------------------------------------------

def build_macrophage_activation_pathway() -> PathwayDefinition:
    """Macrophage activation syndrome (HLH/MAS) following CAR-T therapy.

    Uncontrolled macrophage activation leads to hemophagocytosis, extreme
    ferritin elevation, coagulopathy, and multi-organ failure. Shares
    mechanisms with CRS but represents a distinct, more severe entity.
    """
    pathway_node = GraphNode(
        node_id="PATHWAY:MACROPHAGE_ACTIVATION",
        node_type=NodeType.PATHWAY,
        name="Macrophage Activation (HLH/MAS)",
        properties={
            "reference": "Giavridis et al., Nature Medicine, 2018",
        },
    )

    nodes = [
        _CAR_T_CELL, _MACROPHAGE, _NK_CELL, _DENDRITIC_CELL,
        _IFN_GAMMA, _TNF_ALPHA, _IL6, _IL18, _IL1_BETA, _GM_CSF,
        _PERFORIN, _GRANZYME_B,
        _FERRITIN, _D_DIMER, _FIBRINOGEN, _LDH, _SOLUBLE_CD25,
        _HLH_EVENT, _COAGULOPATHY, _LIVER,
        _ANAKINRA, _RUXOLITINIB, _DEXAMETHASONE,
        pathway_node,
    ]

    edges = [
        # T-cell / NK-cell activation drives IFN-gamma storm
        GraphEdge("CELL:CAR_T", "CYTOKINE:IFN_GAMMA", EdgeType.SECRETES, 0.90),
        GraphEdge("CELL:NK", "CYTOKINE:IFN_GAMMA", EdgeType.SECRETES, 0.80),
        GraphEdge("CELL:CAR_T", "CYTOKINE:GM_CSF", EdgeType.SECRETES, 0.75),

        # IFN-gamma drives uncontrolled macrophage activation
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:MACROPHAGE", EdgeType.ACTIVATES, 0.95,
                  {"state": "hyperactivated, hemophagocytic"}),
        GraphEdge("CYTOKINE:GM_CSF", "CELL:MACROPHAGE", EdgeType.ACTIVATES, 0.80),

        # Activated macrophages produce a cytokine storm
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:IL6", EdgeType.SECRETES, 0.90),
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:TNF_ALPHA", EdgeType.SECRETES, 0.85),
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:IL1_BETA", EdgeType.SECRETES, 0.85),
        GraphEdge("CELL:MACROPHAGE", "CYTOKINE:IL18", EdgeType.SECRETES, 0.80,
                  {"key_for": "HLH specifically"}),
        GraphEdge("CELL:MACROPHAGE", "BIOMARKER:FERRITIN", EdgeType.PRODUCES, 0.90,
                  {"mechanism": "macrophage iron storage and secretion"}),

        # Perforin/granzyme pathway (impaired in familial HLH; functional in CAR-T HLH)
        GraphEdge("CELL:NK", "PROTEIN:PERFORIN", EdgeType.SECRETES, 0.85),
        GraphEdge("CELL:NK", "PROTEIN:GRANZYME_B", EdgeType.SECRETES, 0.85),

        # Hemophagocytosis and tissue damage
        GraphEdge("CELL:MACROPHAGE", "AE:HLH", EdgeType.TRIGGERS, 0.85),
        GraphEdge("CYTOKINE:IL18", "AE:HLH", EdgeType.TRIGGERS, 0.75),
        GraphEdge("AE:HLH", "ORGAN:LIVER", EdgeType.AFFECTS, 0.80),
        GraphEdge("AE:HLH", "SIGN:COAGULOPATHY", EdgeType.MANIFESTS_AS, 0.85),

        # Biomarkers
        GraphEdge("BIOMARKER:FERRITIN", "AE:HLH", EdgeType.INDICATES, 0.90,
                  {"threshold": ">10,000 ng/mL highly suggestive"}),
        GraphEdge("BIOMARKER:D_DIMER", "AE:HLH", EdgeType.INDICATES, 0.75),
        GraphEdge("BIOMARKER:FIBRINOGEN", "AE:HLH", EdgeType.INDICATES, 0.70,
                  {"pattern": "consumptive -- falling fibrinogen"}),
        GraphEdge("BIOMARKER:LDH", "AE:HLH", EdgeType.INDICATES, 0.70),
        GraphEdge("BIOMARKER:SCD25", "AE:HLH", EdgeType.INDICATES, 0.80),

        # Amplification loop
        GraphEdge("CYTOKINE:IFN_GAMMA", "CYTOKINE:IL18", EdgeType.AMPLIFIES, 0.70,
                  {"mechanism": "IFN-g/IL-18 positive feedback loop"}),
        GraphEdge("CYTOKINE:IL18", "CYTOKINE:IFN_GAMMA", EdgeType.AMPLIFIES, 0.70),

        # Drug interventions
        GraphEdge("DRUG:ANAKINRA", "CYTOKINE:IL1_BETA", EdgeType.INHIBITS, 0.85),
        GraphEdge("DRUG:ANAKINRA", "AE:HLH", EdgeType.TREATS, 0.75,
                  {"evidence": "emerging data for CAR-T HLH"}),
        GraphEdge("DRUG:RUXOLITINIB", "PROTEIN:JAK1", EdgeType.INHIBITS, 0.90),
        GraphEdge("DRUG:RUXOLITINIB", "PROTEIN:JAK2", EdgeType.INHIBITS, 0.90),
        GraphEdge("DRUG:RUXOLITINIB", "AE:HLH", EdgeType.TREATS, 0.70),
        GraphEdge("DRUG:DEXAMETHASONE", "AE:HLH", EdgeType.TREATS, 0.65),

        # Pathway linkages
        GraphEdge("PATHWAY:IL6_SIGNALING", "PATHWAY:MACROPHAGE_ACTIVATION",
                  EdgeType.UPSTREAM_OF, 0.70),

        # Pathway membership
        GraphEdge("CELL:MACROPHAGE", "PATHWAY:MACROPHAGE_ACTIVATION",
                  EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("CYTOKINE:IL18", "PATHWAY:MACROPHAGE_ACTIVATION",
                  EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("BIOMARKER:FERRITIN", "PATHWAY:MACROPHAGE_ACTIVATION",
                  EdgeType.PARTICIPATES_IN, 1.0),
    ]

    return PathwayDefinition(
        pathway_id="PATHWAY:MACROPHAGE_ACTIVATION",
        name="Macrophage Activation (HLH/MAS)",
        description=(
            "IFN-gamma-driven uncontrolled macrophage activation leads to "
            "hemophagocytosis, extreme ferritin elevation (>10,000 ng/mL), "
            "consumptive coagulopathy, and multi-organ damage. An IFN-g/IL-18 "
            "positive feedback loop sustains the hyperinflammatory state."
        ),
        nodes=nodes,
        edges=edges,
        temporal_phase=TemporalPhase.PEAK_PHASE,
        adverse_events=["AE:HLH"],
    )


# ---------------------------------------------------------------------------
# Pathway 4: TNF-alpha / NF-kB Amplification
# ---------------------------------------------------------------------------

def build_tnf_nfkb_pathway() -> PathwayDefinition:
    """TNF-alpha / NF-kB inflammatory amplification loop.

    TNF-alpha signals through TNFR1 to activate NF-kB, which upregulates
    transcription of TNF, IL-6, IL-1beta, and chemokines, creating a
    self-amplifying inflammatory cascade.
    """
    pathway_node = GraphNode(
        node_id="PATHWAY:TNF_NFKB",
        node_type=NodeType.PATHWAY,
        name="TNF-alpha / NF-kB Amplification",
    )

    nodes = [
        _MACROPHAGE, _MONOCYTE, _ENDOTHELIAL_CELL,
        _TNF_ALPHA, _IL6, _IL1_BETA, _IL8, _MCP1,
        _TNFR1, _NFKB,
        _TNF_GENE, _IL6_GENE,
        _CRS_EVENT,
        pathway_node,
    ]

    edges = [
        GraphEdge("CYTOKINE:TNF_ALPHA", "RECEPTOR:TNFR1", EdgeType.BINDS, 0.90),
        GraphEdge("RECEPTOR:TNFR1", "PROTEIN:NFKB", EdgeType.ACTIVATES, 0.85),
        GraphEdge("PROTEIN:NFKB", "GENE:TNF", EdgeType.REGULATES, 0.80,
                  {"effect": "positive feedback"}),
        GraphEdge("PROTEIN:NFKB", "GENE:IL6", EdgeType.REGULATES, 0.80),
        GraphEdge("GENE:TNF", "CYTOKINE:TNF_ALPHA", EdgeType.TRANSCRIBES, 0.90),

        # Chemokine production amplifies recruitment
        GraphEdge("PROTEIN:NFKB", "CYTOKINE:IL8", EdgeType.CAUSES, 0.75,
                  {"mechanism": "NF-kB drives CXCL8 transcription"}),
        GraphEdge("PROTEIN:NFKB", "CYTOKINE:MCP1", EdgeType.CAUSES, 0.75),
        GraphEdge("CYTOKINE:MCP1", "CELL:MONOCYTE", EdgeType.ACTIVATES, 0.80,
                  {"mechanism": "chemotaxis -- recruits more monocytes"}),

        # Feed-forward to CRS
        GraphEdge("PATHWAY:TNF_NFKB", "AE:CRS", EdgeType.TRIGGERS, 0.70),

        # Pathway membership
        GraphEdge("CYTOKINE:TNF_ALPHA", "PATHWAY:TNF_NFKB",
                  EdgeType.PARTICIPATES_IN, 1.0),
        GraphEdge("PROTEIN:NFKB", "PATHWAY:TNF_NFKB",
                  EdgeType.PARTICIPATES_IN, 1.0),
    ]

    return PathwayDefinition(
        pathway_id="PATHWAY:TNF_NFKB",
        name="TNF-alpha / NF-kB Amplification",
        description=(
            "TNF-alpha binding to TNFR1 activates NF-kB, which transcriptionally "
            "upregulates TNF, IL-6, IL-1b, IL-8, and MCP-1. MCP-1 recruits "
            "additional monocytes, creating a feed-forward amplification loop "
            "that intensifies CRS."
        ),
        nodes=nodes,
        edges=edges,
        temporal_phase=TemporalPhase.PEAK_PHASE,
        adverse_events=["AE:CRS"],
    )


# ---------------------------------------------------------------------------
# Pathway 5: IFN-gamma Axis
# ---------------------------------------------------------------------------

def build_ifn_gamma_pathway() -> PathwayDefinition:
    """IFN-gamma axis -- the earliest cytokine signal after CAR-T activation.

    IFN-gamma is released by activated CAR-T cells within hours of antigen
    engagement. It is the primary signal that activates bystander monocytes
    and macrophages, bridging adaptive and innate immune responses.
    """
    pathway_node = GraphNode(
        node_id="PATHWAY:IFN_GAMMA",
        node_type=NodeType.PATHWAY,
        name="IFN-gamma Axis",
    )

    nodes = [
        _CAR_T_CELL, _NK_CELL, _MONOCYTE, _MACROPHAGE, _DENDRITIC_CELL,
        _IFN_GAMMA, _IL6, _TNF_ALPHA, _IL1_BETA, _IL10, _IL15,
        _IFNGR, _STAT3,
        _IFNG_GENE,
        _CRS_EVENT, _ICANS_EVENT,
        pathway_node,
    ]

    edges = [
        # T-cell / NK production
        GraphEdge("CELL:CAR_T", "CYTOKINE:IFN_GAMMA", EdgeType.SECRETES, 0.95,
                  {"timing": "earliest cytokine, peaks 24-72h"}),
        GraphEdge("CELL:NK", "CYTOKINE:IFN_GAMMA", EdgeType.SECRETES, 0.80),
        GraphEdge("CYTOKINE:IL15", "CELL:NK", EdgeType.ACTIVATES, 0.70),

        # IFN-gamma receptor signaling
        GraphEdge("CYTOKINE:IFN_GAMMA", "RECEPTOR:IFNGR", EdgeType.BINDS, 0.90),
        GraphEdge("RECEPTOR:IFNGR", "PROTEIN:STAT3", EdgeType.ACTIVATES, 0.75,
                  {"note": "also activates STAT1, but STAT3 links to IL-6 axis"}),

        # Myeloid activation
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:MONOCYTE", EdgeType.ACTIVATES, 0.90),
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:MACROPHAGE", EdgeType.ACTIVATES, 0.90),
        GraphEdge("CYTOKINE:IFN_GAMMA", "CELL:DENDRITIC", EdgeType.ACTIVATES, 0.75),

        # Cross-talk to other cytokines
        GraphEdge("CYTOKINE:IFN_GAMMA", "CYTOKINE:IL6", EdgeType.CAUSES, 0.80,
                  {"mechanism": "via monocyte/macrophage activation"}),
        GraphEdge("CYTOKINE:IFN_GAMMA", "CYTOKINE:TNF_ALPHA", EdgeType.CAUSES, 0.75),
        GraphEdge("CYTOKINE:IL10", "CYTOKINE:IFN_GAMMA", EdgeType.INHIBITS, 0.60,
                  {"mechanism": "negative regulation, anti-inflammatory"}),

        # Links to CRS and ICANS
        GraphEdge("PATHWAY:IFN_GAMMA", "PATHWAY:IL6_SIGNALING",
                  EdgeType.UPSTREAM_OF, 0.90),
        GraphEdge("PATHWAY:IFN_GAMMA", "PATHWAY:ENDOTHELIAL_ACTIVATION",
                  EdgeType.UPSTREAM_OF, 0.80),
        GraphEdge("PATHWAY:IFN_GAMMA", "AE:CRS", EdgeType.TRIGGERS, 0.75),
        GraphEdge("PATHWAY:IFN_GAMMA", "AE:ICANS", EdgeType.TRIGGERS, 0.65),
    ]

    return PathwayDefinition(
        pathway_id="PATHWAY:IFN_GAMMA",
        name="IFN-gamma Axis",
        description=(
            "IFN-gamma, released by activated CAR-T and NK cells, is the earliest "
            "and most proximal signal bridging adaptive T-cell activation to innate "
            "myeloid cell activation. It drives monocytes and macrophages to produce "
            "IL-6, TNF-a, and IL-1b, initiating the cytokine cascade."
        ),
        nodes=nodes,
        edges=edges,
        temporal_phase=TemporalPhase.EARLY_ONSET,
        adverse_events=["AE:CRS", "AE:ICANS"],
    )


# ---------------------------------------------------------------------------
# Public API: load all pathways
# ---------------------------------------------------------------------------

def get_all_pathways() -> list[PathwayDefinition]:
    """Return all pre-built CRS/ICANS/HLH pathway definitions.

    Returns:
        A list of PathwayDefinition objects ready to be loaded into the
        KnowledgeGraph via ``kg.load_pathway(pathway)``.
    """
    return [
        build_il6_signaling_pathway(),
        build_endothelial_activation_pathway(),
        build_macrophage_activation_pathway(),
        build_tnf_nfkb_pathway(),
        build_ifn_gamma_pathway(),
    ]


def get_pathway_by_id(pathway_id: str) -> PathwayDefinition | None:
    """Look up a single pathway by its ID.

    Args:
        pathway_id: e.g. ``'PATHWAY:IL6_SIGNALING'``.

    Returns:
        The matching PathwayDefinition, or None if not found.
    """
    for p in get_all_pathways():
        if p.pathway_id == pathway_id:
            return p
    return None
