"""
AE mechanism chains linking therapy action to clinical outcome.

Each mechanism is a complete chain: Therapy -> target engagement ->
downstream cascade -> clinical adverse event, with branching points,
feedback loops, and intervention opportunities annotated.

Includes therapy type-specific mechanisms for CAR-T (CD19, BCMA),
TCR-T, NK cell, TIL, CAR-M, and gene therapy modalities.

Data sourced from:
    - Lee et al., 2019 (PMID:30275568)
    - Liu et al., 2024 (TCR-T review, PMID:39352714)
    - Liu et al., 2020 (CAR-NK, PMID:32433173)
    - Zhang et al., 2024 (CAR-M, PMID:38368579)
    - Di Stasi et al., 2014 (iCasp9, PMID:25389405)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TherapyModality(Enum):
    """Cell/gene therapy modality classifications."""

    CAR_T_CD19 = "CAR-T (CD19)"
    CAR_T_BCMA = "CAR-T (BCMA)"
    CAR_T_DUAL = "CAR-T (dual-target)"
    TCR_T = "TCR-T"
    CAR_NK = "CAR-NK"
    TIL = "TIL"
    CAR_M = "CAR-M (macrophage)"
    GENE_THERAPY_AAV = "Gene Therapy (AAV)"
    GENE_THERAPY_LENTIVIRAL = "Gene Therapy (lentiviral)"
    TREG = "Treg"
    MSC = "MSC"


class AECategory(Enum):
    """Adverse event categories."""

    CRS = "Cytokine Release Syndrome"
    ICANS = "ICANS"
    HLH_MAS = "HLH/MAS"
    B_CELL_APLASIA = "B-Cell Aplasia"
    ON_TARGET_OFF_TUMOR = "On-Target/Off-Tumor Toxicity"
    CROSS_REACTIVITY = "Cross-Reactivity Toxicity"
    INSERTIONAL_MUTAGENESIS = "Insertional Mutagenesis"
    PROLONGED_CYTOPENIA = "Prolonged Cytopenia"
    GVHD = "GvHD"
    INFECTION = "Infection"


@dataclass(frozen=True)
class MechanismStep:
    """A single step in an AE mechanism chain.

    Attributes:
        step_number: Position in the chain (1-indexed).
        entity: The molecule, cell, or process at this step.
        action: What happens at this step.
        detail: Mechanistic detail.
        temporal_onset: Typical timing relative to infusion.
        biomarkers: Measurable biomarkers at this step.
        is_branching_point: Whether the mechanism can diverge here.
        branches: Alternative outcomes from this point.
        is_intervention_point: Whether intervention is possible here.
        interventions: Available interventions at this point.
    """

    step_number: int
    entity: str
    action: str
    detail: str
    temporal_onset: str = ""
    biomarkers: tuple[str, ...] = ()
    is_branching_point: bool = False
    branches: tuple[str, ...] = ()
    is_intervention_point: bool = False
    interventions: tuple[str, ...] = ()


@dataclass
class MechanismChain:
    """A complete mechanism chain from therapy to adverse event.

    Attributes:
        mechanism_id: Unique identifier.
        therapy_modality: The therapy type.
        ae_category: The resulting adverse event.
        name: Short descriptive name.
        description: Detailed mechanism summary.
        steps: Ordered list of mechanism steps.
        risk_factors: Patient/disease factors that increase risk.
        severity_determinants: What determines AE severity.
        typical_onset: Typical onset timing post-infusion.
        typical_duration: Typical duration.
        incidence_range: Published incidence range.
        mortality_rate: Published mortality rate.
        key_references: PubMed IDs.
    """

    mechanism_id: str
    therapy_modality: TherapyModality
    ae_category: AECategory
    name: str
    description: str
    steps: list[MechanismStep] = field(default_factory=list)
    risk_factors: list[str] = field(default_factory=list)
    severity_determinants: list[str] = field(default_factory=list)
    typical_onset: str = ""
    typical_duration: str = ""
    incidence_range: str = ""
    mortality_rate: str = ""
    key_references: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mechanism 1: CAR-T CD19 -> CRS
# ---------------------------------------------------------------------------

CART_CD19_CRS = MechanismChain(
    mechanism_id="MECH:CART_CD19_CRS",
    therapy_modality=TherapyModality.CAR_T_CD19,
    ae_category=AECategory.CRS,
    name="CD19 CAR-T Induced CRS",
    description=(
        "CD19 CAR-T cells engage CD19 on B cells/tumor cells, triggering T-cell "
        "activation and IFN-gamma release. IFN-gamma activates bystander monocytes/"
        "macrophages (the primary IL-6 source). Neutrophil ADAM17 sheds sIL-6R, "
        "enabling IL-6 trans-signaling on endothelial cells. A STAT3-mediated "
        "positive feedback loop amplifies IL-6 production. Severity correlates with "
        "tumor burden (antigen load) and CAR-T dose."
    ),
    steps=[
        MechanismStep(1, "CD19 CAR-T cell", "engages CD19+ target", "scFv domain binds CD19 on malignant/normal B cells", "0-6h"),
        MechanismStep(2, "CAR-T cell", "activates", "CD3-zeta ITAM phosphorylation + CD28/4-1BB costimulatory signals", "0-6h"),
        MechanismStep(3, "CAR-T cell", "releases cytokines", "IFN-gamma (earliest, 2-24h), TNF-alpha, IL-2, GM-CSF, perforin/granzyme B", "2-24h",
                      biomarkers=("IFN-gamma", "sCD25")),
        MechanismStep(4, "target cell", "lysed", "Perforin pores + granzyme B serine protease cascade -> apoptosis; DAMPs released (HMGB1, ATP)", "6-24h",
                      biomarkers=("LDH",)),
        MechanismStep(5, "IFN-gamma", "activates monocytes/macrophages", "IFNGR -> JAK1/JAK2 -> STAT1 activation; monocytes are the PRIMARY IL-6 source", "6-48h",
                      is_branching_point=True, branches=("mild_CRS_self_limiting", "severe_CRS_amplification_loop")),
        MechanismStep(6, "monocyte/macrophage", "produces IL-6, IL-1beta", "NF-kB and STAT3 drive cytokine transcription; IL-1beta is upstream of IL-6", "24-72h",
                      biomarkers=("IL-6", "IL-1beta"),
                      is_intervention_point=True, interventions=("anakinra_IL-1_blockade",)),
        MechanismStep(7, "neutrophil ADAM17", "sheds sIL-6R", "Metalloproteinase cleaves membrane IL-6R ectodomain; early event preceding CRS", "6-24h",
                      biomarkers=("sIL-6R",)),
        MechanismStep(8, "IL-6/sIL-6R", "activates gp130 (trans-signaling)", "Binary complex binds ubiquitous gp130 on endothelial cells -> JAK1/STAT3", "24-72h",
                      is_intervention_point=True, interventions=("tocilizumab_anti-IL-6R", "siltuximab_anti-IL-6")),
        MechanismStep(9, "STAT3", "drives IL-6 gene transcription", "POSITIVE FEEDBACK: IL-6 -> gp130 -> JAK1 -> STAT3 -> IL-6 gene -> more IL-6", "24-72h"),
        MechanismStep(10, "endothelial activation", "vascular leak", "Activated endothelium expresses tissue factor, releases Ang-2/vWF, loses barrier function", "48-120h",
                      biomarkers=("Ang-2", "vWF", "EASIX"),
                      is_branching_point=True, branches=("CRS_resolution", "ICANS_progression", "HLH_progression")),
        MechanismStep(11, "CRS", "clinical syndrome", "Fever (PGE2), hypotension (vascular leak + NO), hypoxia (pulmonary capillary leak)", "24-168h",
                      biomarkers=("CRP", "ferritin", "IL-6"),
                      is_intervention_point=True, interventions=("tocilizumab", "dexamethasone", "supportive_care")),
    ],
    risk_factors=[
        "High tumor burden / antigen load",
        "High CAR-T cell dose",
        "4-1BB vs CD28 costimulatory domain (different kinetics)",
        "Lymphodepletion regimen intensity",
        "Pre-infusion inflammatory state (baseline IL-6, CRP, ferritin)",
        "Prior CRS history",
        "Thrombocytopenia at baseline",
    ],
    severity_determinants=[
        "Peak IL-6 level (correlates with grade)",
        "Tumor burden (higher burden -> more antigen -> more activation)",
        "CAR-T expansion kinetics (rapid expansion -> more IFN-gamma)",
        "Baseline endothelial activation (pre-existing EASIX elevation)",
        "CD4:CD8 ratio in infusion product (higher CD4 fraction -> more CRS)",
    ],
    typical_onset="1-7 days post-infusion (median day 2-3)",
    typical_duration="7-14 days",
    incidence_range="Any grade: 42-94%; Grade >= 3: 2-46% (product-dependent)",
    mortality_rate="<3% with current management",
    key_references=["PMID:29643512", "PMID:27455965", "PMID:30275568", "PMID:38123583"],
)


# ---------------------------------------------------------------------------
# Mechanism 2: CD19 CAR-T -> ICANS
# ---------------------------------------------------------------------------

CART_CD19_ICANS = MechanismChain(
    mechanism_id="MECH:CART_CD19_ICANS",
    therapy_modality=TherapyModality.CAR_T_CD19,
    ae_category=AECategory.ICANS,
    name="CD19 CAR-T Induced ICANS",
    description=(
        "ICANS results from convergent BBB disruption mechanisms: (1) systemic "
        "cytokine-driven endothelial activation with Ang-2 release and pericyte "
        "detachment; (2) direct on-target/off-tumor killing of CD19+ brain "
        "pericytes; (3) CNS cytokine infiltration producing reactive astrocytosis "
        "and kynurenine-pathway neurotoxicity (quinolinic acid -> glutamate "
        "excitotoxicity via NMDA receptors)."
    ),
    steps=[
        MechanismStep(1, "systemic CRS cytokines", "activate CNS endothelium", "IL-6 trans-signaling, TNF-alpha, IFN-gamma, IL-1beta activate brain endothelial cells", "24-72h",
                      biomarkers=("IL-6", "IFN-gamma")),
        MechanismStep(2, "endothelial activation", "Weibel-Palade body exocytosis", "Releases stored Ang-2 and vWF into CNS microvasculature", "48-96h",
                      biomarkers=("Ang-2", "vWF", "Ang-2/Ang-1_ratio")),
        MechanismStep(3, "Ang-2", "antagonizes Tie2 on pericytes", "Displaces protective Ang-1; pericyte detachment from CNS microvasculature", "48-96h"),
        MechanismStep(4, "CD19 CAR-T", "targets CD19+ brain pericytes", "Brain mural cells express CD19 (on-target/off-tumor). Direct lysis disrupts neurovascular unit.", "48-96h"),
        MechanismStep(5, "BBB disruption", "cytokine infiltration into CNS", "Loss of tight junctions (claudin-5, occludin) permits IFN-gamma, IL-6, TNF-alpha entry into brain parenchyma", "72-168h",
                      biomarkers=("CSF_protein", "CSF_cytokines")),
        MechanismStep(6, "reactive astrocytosis", "kynurenine pathway activation", "IFN-gamma induces IDO in astrocytes/microglia; tryptophan -> kynurenine -> quinolinic acid", "72-168h",
                      biomarkers=("GFAP", "S100b", "CSF_quinolinic_acid")),
        MechanismStep(7, "quinolinic acid", "NMDA receptor agonism", "Glutamate excitotoxicity: calcium influx -> neuronal injury -> encephalopathy, seizures", "72-168h"),
        MechanismStep(8, "ICANS", "clinical neurotoxicity", "Encephalopathy, aphasia, tremor, seizures; ICE score for grading. Fatal cerebral edema in severe cases.", "48-168h",
                      biomarkers=("ICE_score",),
                      is_intervention_point=True, interventions=("dexamethasone", "levetiracetam", "ICU_monitoring")),
    ],
    risk_factors=[
        "Preceding CRS severity (CRS typically precedes ICANS by 1-3 days)",
        "High tumor burden",
        "Pre-existing neurological conditions",
        "Baseline thrombocytopenia (reflects endothelial dysfunction)",
        "Young age (more permeable BBB in children)",
        "High-dose CAR-T product",
    ],
    severity_determinants=[
        "Peak IL-6 and IFN-gamma levels",
        "Ang-2:Ang-1 ratio (endothelial activation)",
        "CSF quinolinic acid levels",
        "EASIX score at baseline",
        "Speed of CRS onset (rapid CRS -> higher ICANS risk)",
    ],
    typical_onset="2-10 days post-infusion (median day 5-7, typically 1-3 days after CRS onset)",
    typical_duration="2-21 days",
    incidence_range="Any grade: 20-64%; Grade >= 3: 10-28% (product-dependent)",
    mortality_rate="<5% with current management; fatal cerebral edema is rare",
    key_references=["PMID:29025771", "PMID:33082430", "PMID:30154262", "PMID:37798640"],
)


# ---------------------------------------------------------------------------
# Mechanism 3: TCR-T -> Cross-Reactivity Toxicity
# ---------------------------------------------------------------------------

TCRT_CROSS_REACTIVITY = MechanismChain(
    mechanism_id="MECH:TCRT_CROSS_REACTIVITY",
    therapy_modality=TherapyModality.TCR_T,
    ae_category=AECategory.CROSS_REACTIVITY,
    name="TCR-T Cross-Reactivity Toxicity",
    description=(
        "TCR-T cells recognize peptide-MHC complexes, making them HLA-restricted. "
        "Cross-reactivity occurs when the engineered TCR recognizes structurally "
        "similar peptides (mimotopes) presented by the same or different HLA alleles "
        "on normal tissues. Fatal cardiotoxicity from MAGE-A3 TCR cross-reacting "
        "with titin in cardiac tissue illustrates this risk. TCRs not subjected to "
        "thymic negative selection (e.g., from immunized mice or affinity-enhanced) "
        "carry higher cross-reactivity risk."
    ),
    steps=[
        MechanismStep(1, "TCR-T cell", "recognizes target peptide-MHC", "Engineered TCR binds intended tumor-associated antigen presented by specific HLA allele", "0-24h"),
        MechanismStep(2, "TCR", "cross-reacts with mimotope", "TCR CDR3 regions bind structurally similar peptide from a different protein expressed on normal tissue", "0-48h"),
        MechanismStep(3, "normal tissue cell", "targeted for killing", "On-target antigen in tumor is mimicked by structurally similar epitope in normal tissue (e.g., titin in cardiac myocytes for MAGE-A3)", "24-96h"),
        MechanismStep(4, "tissue destruction", "organ damage", "Perforin/granzyme-mediated cytolysis of normal tissue cells causes organ-specific toxicity (cardiotoxicity, hepatotoxicity, etc.)", "24-168h"),
    ],
    risk_factors=[
        "TCR from immunized mice (no thymic selection against human self-antigens)",
        "Affinity-enhanced TCRs with CDR mutations",
        "Target antigen with structural homologs in normal tissues",
        "HLA alloreactivity (TCR recognizes different HLA alleles presenting various peptides)",
        "Lack of comprehensive cross-reactivity screening pre-infusion",
    ],
    severity_determinants=[
        "Tissue distribution of cross-reactive antigen",
        "Affinity of TCR for mimotope vs target (higher affinity -> worse toxicity)",
        "Vitality of affected organ (cardiac >> skin)",
    ],
    typical_onset="1-5 days post-infusion",
    typical_duration="Days to weeks (can be fatal within 48h for cardiac events)",
    incidence_range="Rare but unpredictable; 2/9 patients died in MAGE-A3 trial",
    mortality_rate="High when cardiac tissue involved (2/9 deaths in early MAGE-A3 trials)",
    key_references=["PMID:39352714"],
)


# ---------------------------------------------------------------------------
# Mechanism 4: CAR-NK reduced CRS
# ---------------------------------------------------------------------------

CARNK_REDUCED_CRS = MechanismChain(
    mechanism_id="MECH:CARNK_LOW_CRS",
    therapy_modality=TherapyModality.CAR_NK,
    ae_category=AECategory.CRS,
    name="CAR-NK Reduced CRS Risk",
    description=(
        "CAR-NK cells produce a different cytokine profile than CAR-T cells, with "
        "less sustained IFN-gamma production and shorter in vivo persistence. NK "
        "cells do not produce IL-6 directly. The allogeneic nature of cord blood-derived "
        "CAR-NK cells and KIR mismatch-based selection enhance anti-tumor activity via "
        "missing-self recognition without inducing GvHD. Clinical trials have shown "
        "no grade >= 3 CRS and no ICANS with CAR-NK therapy."
    ),
    steps=[
        MechanismStep(1, "CAR-NK cell", "engages target antigen", "CAR (e.g., anti-CD19) binds target. Also has intrinsic NK recognition via NKG2D, KIR mismatch.", "0-6h"),
        MechanismStep(2, "CAR-NK cell", "cytolysis", "Perforin/granzyme-mediated killing + ADCC via CD16. Shorter persistence than CAR-T (weeks vs months).", "0-24h"),
        MechanismStep(3, "CAR-NK cell", "limited cytokine release", "IFN-gamma and TNF-alpha production is less sustained than CAR-T. No direct IL-6 production by NK cells.", "6-48h"),
        MechanismStep(4, "limited monocyte activation", "reduced IL-6 production", "Lower and shorter IFN-gamma exposure -> less monocyte/macrophage activation -> less IL-6 amplification.", "24-72h"),
    ],
    risk_factors=[
        "Cytokine armoring (IL-15 co-expression increases persistence but may increase CRS risk)",
        "High tumor burden (still a risk factor but with lower magnitude)",
    ],
    severity_determinants=[
        "IL-15 armoring status",
        "CAR-NK dose",
        "Tumor burden",
    ],
    typical_onset="N/A (CRS typically absent)",
    typical_duration="N/A",
    incidence_range="Grade >= 3 CRS: 0% in clinical trials to date; no ICANS reported",
    mortality_rate="No CRS-related mortality reported",
    key_references=["PMID:32433173"],
)


# ---------------------------------------------------------------------------
# Mechanism 5: Gene Therapy -> Insertional Mutagenesis
# ---------------------------------------------------------------------------

GENE_THERAPY_INSERTIONAL = MechanismChain(
    mechanism_id="MECH:GT_INSERTIONAL",
    therapy_modality=TherapyModality.GENE_THERAPY_LENTIVIRAL,
    ae_category=AECategory.INSERTIONAL_MUTAGENESIS,
    name="Lentiviral Gene Therapy Insertional Mutagenesis",
    description=(
        "Lentiviral and retroviral vectors integrate into the host genome to provide "
        "stable transgene expression. Integration near proto-oncogenes or tumor "
        "suppressors can dysregulate gene expression, leading to clonal expansion "
        "and secondary malignancies (MDS, AML). FDA mandated a boxed warning for "
        "all approved CAR-T products in January 2024 regarding T-cell malignancy risk. "
        "The Skysona (elivaldogene autotemcel) experience showed 15% MDS incidence."
    ),
    steps=[
        MechanismStep(1, "lentiviral vector", "integrates into genome", "Integrase mediates semi-random insertion into host cell DNA, with preference for transcriptionally active regions.", "during_manufacturing"),
        MechanismStep(2, "integration site", "near proto-oncogene", "Integration within or near genes like LMO2, MDS1-EVI1, or PRDM16 can dysregulate expression.", "during_manufacturing"),
        MechanismStep(3, "proto-oncogene activation", "clonal expansion", "Enhancer/promoter elements in the vector activate adjacent oncogenes; affected cell gains proliferative advantage.", "months_to_years"),
        MechanismStep(4, "clonal expansion", "secondary malignancy", "Accumulation of additional mutations in the expanding clone leads to MDS, AML, or T-cell lymphoma.", "months_to_years",
                      biomarkers=("CBC", "bone_marrow_biopsy", "integration_site_analysis")),
    ],
    risk_factors=[
        "Retroviral vectors (gamma-retroviral > lentiviral for insertional mutagenesis risk)",
        "Prior exposure to alkylating agents / chemotherapy",
        "Number of vector copy numbers per cell",
        "Patient age (younger patients may have longer risk exposure window)",
        "Specific vector design (self-inactivating vectors lower risk)",
    ],
    severity_determinants=[
        "Proximity of integration to oncogenes",
        "Vector copy number",
        "Vector enhancer/promoter strength",
    ],
    typical_onset="Months to years post-treatment (median 2-5 years in gene therapy trials)",
    typical_duration="Permanent",
    incidence_range="MDS/AML: up to 15% in Skysona trials; T-cell lymphoma: rare but reported after CAR-T",
    mortality_rate="Variable; MDS/AML carries significant mortality",
    key_references=[
        "PMID:12529469",   # Hacein-Bey-Abina et al. 2003 - LMO2 insertional mutagenesis in X-SCID gene therapy
        "PMID:10706547",   # Cavazzana-Calvo et al. 2000 - Gene therapy of human SCID-X1 disease
        "PMID:25389405",   # Di Stasi et al. 2014 - iCasp9 safety switch
        "PMID:38123583",   # FDA 2024 T-cell malignancy investigation after CAR-T
    ],
)


# ---------------------------------------------------------------------------
# Mechanism 6: CAR-T CD19 -> B-Cell Aplasia
# ---------------------------------------------------------------------------

CART_CD19_B_CELL_APLASIA = MechanismChain(
    mechanism_id="MECH:CART_CD19_BCELL_APLASIA",
    therapy_modality=TherapyModality.CAR_T_CD19,
    ae_category=AECategory.B_CELL_APLASIA,
    name="CD19 CAR-T On-Target/Off-Tumor B-Cell Aplasia",
    description=(
        "CD19 is expressed on all normal B cells from the pro-B cell stage through "
        "mature B cells (but not on plasma cells). CD19 CAR-T cells cannot "
        "distinguish malignant from normal CD19+ cells, resulting in B-cell aplasia "
        "and secondary hypogammaglobulinemia. This is an expected pharmacological "
        "effect that persists as long as functional CAR-T cells remain."
    ),
    steps=[
        MechanismStep(1, "CD19 CAR-T", "targets all CD19+ cells", "CAR does not distinguish malignant vs normal B cells", "0-7d"),
        MechanismStep(2, "normal B cells", "eliminated", "Perforin/granzyme-mediated killing of all CD19+ B-lineage cells from pro-B through mature B cells", "7-28d",
                      biomarkers=("CD19+_B_cell_count",)),
        MechanismStep(3, "B-cell aplasia", "hypogammaglobulinemia", "Loss of B cells -> cessation of new antibody production -> falling IgG, IgA, IgM over weeks to months", "1-6_months",
                      biomarkers=("IgG", "IgA", "IgM"),
                      is_intervention_point=True, interventions=("IVIG_replacement",)),
        MechanismStep(4, "hypogammaglobulinemia", "infection risk", "Increased susceptibility to encapsulated bacteria, respiratory viruses, and opportunistic infections", "months_to_years"),
    ],
    risk_factors=[
        "CAR-T persistence (longer persistence = longer B-cell aplasia)",
        "4-1BB costimulatory domain (longer CAR-T persistence vs CD28)",
        "Prior rituximab therapy (already depleted B cells)",
    ],
    severity_determinants=[
        "Depth and duration of B-cell aplasia",
        "IgG nadir level",
        "Patient baseline immune status",
    ],
    typical_onset="7-14 days (coincides with CAR-T expansion)",
    typical_duration="Months to years; can be permanent with persistent CAR-T",
    incidence_range="Nearly 100% with effective CD19 CAR-T",
    mortality_rate="<1% with IVIG support",
    key_references=[
        "PMID:36519539",   # Mackensen et al. 2022 - Anti-CD19 CAR T cells for refractory SLE (B-cell depletion)
        "PMID:38242083",   # Muller et al. 2024 - CD19 CAR-T in autoimmune disease, prolonged B-cell aplasia
        "PMID:29643512",   # Neelapu et al. 2017 - Axi-cel ZUMA-1 (B-cell aplasia as on-target effect)
        "PMID:30275568",   # Lee et al. 2019 - ASTCT consensus, B-cell aplasia management
    ],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

MECHANISM_REGISTRY: dict[str, MechanismChain] = {
    m.mechanism_id: m for m in [
        CART_CD19_CRS,
        CART_CD19_ICANS,
        TCRT_CROSS_REACTIVITY,
        CARNK_REDUCED_CRS,
        GENE_THERAPY_INSERTIONAL,
        CART_CD19_B_CELL_APLASIA,
    ]
}


def get_mechanism(mechanism_id: str) -> MechanismChain | None:
    """Look up a mechanism chain by ID.

    Args:
        mechanism_id: Mechanism identifier (e.g. "MECH:CART_CD19_CRS").

    Returns:
        The MechanismChain, or None if not found.
    """
    return MECHANISM_REGISTRY.get(mechanism_id)


def get_mechanisms_for_therapy(modality: TherapyModality) -> list[MechanismChain]:
    """Return all mechanism chains for a given therapy modality.

    Args:
        modality: The TherapyModality to filter on.

    Returns:
        List of MechanismChain objects.
    """
    return [m for m in MECHANISM_REGISTRY.values() if m.therapy_modality == modality]


def get_mechanisms_for_ae(ae_category: AECategory) -> list[MechanismChain]:
    """Return all mechanism chains that lead to a given AE.

    Args:
        ae_category: The AECategory to filter on.

    Returns:
        List of MechanismChain objects.
    """
    return [m for m in MECHANISM_REGISTRY.values() if m.ae_category == ae_category]


def get_mechanism_chain(
    therapy_type: str,
    ae_type: str,
) -> list[MechanismStep]:
    """Get the step-by-step mechanism chain for a therapy-AE pair.

    Args:
        therapy_type: Therapy modality string (e.g. "CAR-T (CD19)").
        ae_type: AE category string (e.g. "Cytokine Release Syndrome").

    Returns:
        Ordered list of MechanismStep objects, or empty list if no match.
    """
    for mech in MECHANISM_REGISTRY.values():
        if mech.therapy_modality.value == therapy_type and mech.ae_category.value == ae_type:
            return mech.steps
    return []
