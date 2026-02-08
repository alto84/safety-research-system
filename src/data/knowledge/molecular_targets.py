"""
Molecular targets and their relationships in cell therapy AE biology.

Defines druggable targets, signaling molecules, receptors, and biomarkers
involved in CRS, ICANS, and HLH pathways. Each target records its pathway
membership, known modulators (drugs), clinical relevance, and evidence level.

Data sourced from:
    - Lee et al., Biol Blood Marrow Transplant 2019 (PMID:30275568)
    - Neelapu et al., Nat Rev Clin Oncol 2018 (PMID:29084955)
    - Gust et al., Cancer Discov 2017 (PMID:29025771)
    - Teachey et al., Cancer Discov 2016 (PMID:27455965)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TargetCategory(Enum):
    """Classification of molecular targets."""

    CYTOKINE = "cytokine"
    RECEPTOR = "receptor"
    KINASE = "kinase"
    TRANSCRIPTION_FACTOR = "transcription_factor"
    BIOMARKER = "biomarker"
    ADHESION_MOLECULE = "adhesion_molecule"
    ENZYME = "enzyme"
    GROWTH_FACTOR = "growth_factor"
    COMPLEMENT = "complement"


class DrugStatus(Enum):
    """Approval status of modulating drugs."""

    APPROVED_CRS = "approved_for_crs"
    APPROVED_OTHER = "approved_other_indication"
    INVESTIGATIONAL = "investigational"
    PRECLINICAL = "preclinical"


@dataclass(frozen=True)
class Modulator:
    """A drug or agent that modulates a molecular target.

    Attributes:
        name: Drug name.
        mechanism: How the drug modulates the target (e.g. "receptor blockade").
        status: Regulatory/development status.
        route: Administration route.
        dose: Typical dose for CRS/ICANS management.
        evidence_refs: PubMed IDs supporting use.
    """

    name: str
    mechanism: str
    status: DrugStatus
    route: str = ""
    dose: str = ""
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class MolecularTarget:
    """A molecular target involved in cell therapy AE pathophysiology.

    Attributes:
        target_id: Unique identifier (e.g. "TARGET:IL6").
        name: Human-readable name.
        gene_symbol: HGNC gene symbol.
        category: Target classification.
        pathways: Pathways this target participates in.
        normal_range: Normal physiologic range with units.
        ae_range: Range observed during AE with units.
        clinical_relevance: Role in AE biology.
        modulators: Known drugs/agents that modulate this target.
        upstream_of: Targets/pathways activated by this target.
        downstream_of: Targets/pathways that activate this target.
        biomarker_utility: How this target is used as a biomarker (if applicable).
        references: PubMed IDs.
    """

    target_id: str
    name: str
    gene_symbol: str
    category: TargetCategory
    pathways: tuple[str, ...]
    normal_range: str
    ae_range: str
    clinical_relevance: str
    modulators: tuple[Modulator, ...] = ()
    upstream_of: tuple[str, ...] = ()
    downstream_of: tuple[str, ...] = ()
    biomarker_utility: str = ""
    references: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Core cytokine targets
# ---------------------------------------------------------------------------

IL6 = MolecularTarget(
    target_id="TARGET:IL6",
    name="Interleukin-6 (IL-6)",
    gene_symbol="IL6",
    category=TargetCategory.CYTOKINE,
    pathways=("IL-6_classical_signaling", "IL-6_trans-signaling", "JAK/STAT", "acute_phase_response"),
    normal_range="0-7 pg/mL",
    ae_range="100-100,000 pg/mL during severe CRS",
    clinical_relevance="Central driver of CRS via trans-signaling through sIL-6R/gp130 on endothelial cells. Peak levels correlate with CRS severity grade. Hepatic acute phase response driver (CRP, ferritin).",
    modulators=(
        Modulator(
            name="Tocilizumab",
            mechanism="Anti-IL-6R monoclonal antibody; blocks both membrane-bound and soluble IL-6R, preventing IL-6 from engaging gp130 signal transduction",
            status=DrugStatus.APPROVED_CRS,
            route="IV",
            dose="8 mg/kg (max 800 mg), up to 3 additional doses q8h",
            evidence_refs=("PMID:32666058", "PMID:29084955"),
        ),
        Modulator(
            name="Siltuximab",
            mechanism="Anti-IL-6 monoclonal antibody; directly neutralizes circulating IL-6 protein",
            status=DrugStatus.APPROVED_OTHER,
            route="IV",
            dose="11 mg/kg",
            evidence_refs=("PMID:29084955",),
        ),
    ),
    upstream_of=("CRP", "ferritin", "endothelial_activation", "JAK1", "STAT3"),
    downstream_of=("monocyte_activation", "macrophage_activation", "NF-kB", "STAT3_feedback"),
    biomarker_utility="Peak IL-6 > 1000 pg/mL associated with grade >= 3 CRS. Serial monitoring guides tocilizumab timing. IL-6 transiently rises after tocilizumab due to receptor blockade (not worsening disease).",
    references=("PMID:29643512", "PMID:27455965", "PMID:28854140", "PMID:30442748"),
)

IL1_BETA = MolecularTarget(
    target_id="TARGET:IL1B",
    name="Interleukin-1 beta (IL-1beta)",
    gene_symbol="IL1B",
    category=TargetCategory.CYTOKINE,
    pathways=("inflammasome", "NF-kB", "IL-1_signaling"),
    normal_range="0-5 pg/mL",
    ae_range="10-500 pg/mL during CRS",
    clinical_relevance="Upstream of IL-6 in the CRS cascade. Monocyte/macrophage-derived IL-1beta activates endothelium and drives IL-6 production. IL-1 blockade protected against both CRS and neurotoxicity in preclinical models.",
    modulators=(
        Modulator(
            name="Anakinra",
            mechanism="Recombinant IL-1 receptor antagonist (IL-1Ra); competitively blocks IL-1alpha and IL-1beta binding to IL-1R1",
            status=DrugStatus.APPROVED_OTHER,
            route="SC/IV",
            dose="100 mg SC daily or higher doses IV for severe CRS/HLH",
            evidence_refs=("PMID:29643512", "PMID:37271625"),
        ),
        Modulator(
            name="Canakinumab",
            mechanism="Anti-IL-1beta monoclonal antibody; selectively neutralizes IL-1beta",
            status=DrugStatus.APPROVED_OTHER,
            route="SC",
            dose="4 mg/kg",
            evidence_refs=(),
        ),
    ),
    upstream_of=("IL-6", "endothelial_activation", "fever"),
    downstream_of=("inflammasome_NLRP3", "monocyte_activation"),
    biomarker_utility="Less commonly measured clinically than IL-6; elevated in CSF during ICANS.",
    references=("PMID:29643512", "PMID:29643511", "PMID:37271625"),
)

IFN_GAMMA = MolecularTarget(
    target_id="TARGET:IFNG",
    name="Interferon-gamma (IFN-gamma)",
    gene_symbol="IFNG",
    category=TargetCategory.CYTOKINE,
    pathways=("IFN-gamma_signaling", "JAK/STAT", "macrophage_activation"),
    normal_range="0-15.6 pg/mL",
    ae_range="500-50,000 pg/mL; peaks earliest among CRS cytokines (24-72h)",
    clinical_relevance="The earliest and most proximal signal in CRS. Released by activated CAR-T cells within hours. Primary bridge between adaptive (T-cell) and innate (monocyte/macrophage) immune activation. Key driver of HLH via uncontrolled macrophage activation.",
    modulators=(
        Modulator(
            name="Emapalumab",
            mechanism="Anti-IFN-gamma monoclonal antibody; neutralizes circulating IFN-gamma",
            status=DrugStatus.APPROVED_OTHER,
            route="IV",
            dose="1 mg/kg then 3-10 mg/kg q3d",
            evidence_refs=(),
        ),
    ),
    upstream_of=("monocyte_activation", "macrophage_activation", "IL-6", "TNF-alpha", "IL-1beta", "CXCL9", "CXCL10"),
    downstream_of=("CAR-T_activation", "NK_cell_activation", "IL-12", "IL-15"),
    biomarker_utility="Earliest cytokine to peak post-CAR-T infusion; IFN-gamma > 500 pg/mL at 24h predicts severe CRS.",
    references=("PMID:27455965", "PMID:39277881"),
)

TNF_ALPHA = MolecularTarget(
    target_id="TARGET:TNF",
    name="Tumor Necrosis Factor-alpha (TNF-alpha)",
    gene_symbol="TNF",
    category=TargetCategory.CYTOKINE,
    pathways=("NF-kB", "TNF_signaling", "endothelial_activation"),
    normal_range="0-8.1 pg/mL",
    ae_range="10-5,000 pg/mL during CRS",
    clinical_relevance="Activates NF-kB pathway creating a positive feedback loop for inflammatory cytokine production. Directly activates endothelium. Important contributor to hemodynamic instability in CRS.",
    modulators=(),
    upstream_of=("NF-kB", "endothelial_activation", "IL-6_transcription"),
    downstream_of=("CAR-T_activation", "macrophage_activation"),
    biomarker_utility="Contributes to CRS severity but less discriminatory than IL-6 or IFN-gamma alone.",
    references=("PMID:27455965",),
)

IL18 = MolecularTarget(
    target_id="TARGET:IL18",
    name="Interleukin-18 (IL-18)",
    gene_symbol="IL18",
    category=TargetCategory.CYTOKINE,
    pathways=("inflammasome", "IFN-gamma_amplification", "macrophage_activation"),
    normal_range="0-400 pg/mL",
    ae_range=">1000 pg/mL in HLH",
    clinical_relevance="Forms a positive feedback loop with IFN-gamma: IL-18 stimulates IFN-gamma production, which in turn drives IL-18 secretion from macrophages. Key differentiator of HLH from CRS.",
    modulators=(
        Modulator(
            name="Tadekinig alfa",
            mechanism="Recombinant IL-18 binding protein; decoy receptor that neutralizes free IL-18",
            status=DrugStatus.INVESTIGATIONAL,
            route="SC",
            dose="Under investigation",
            evidence_refs=(),
        ),
    ),
    upstream_of=("IFN-gamma", "NK_cell_activation"),
    downstream_of=("inflammasome_NLRP3", "macrophage_activation"),
    biomarker_utility="Elevated IL-18 distinguishes HLH from CRS; free IL-18 (unbound by IL-18BP) is more specific.",
    references=("PMID:39277881", "PMID:39338775"),
)


# ---------------------------------------------------------------------------
# Receptors and signaling molecules
# ---------------------------------------------------------------------------

SIL6R = MolecularTarget(
    target_id="TARGET:SIL6R",
    name="Soluble IL-6 Receptor (sIL-6R)",
    gene_symbol="IL6R",
    category=TargetCategory.RECEPTOR,
    pathways=("IL-6_trans-signaling",),
    normal_range="25-75 ng/mL",
    ae_range=">100 ng/mL during CRS",
    clinical_relevance="Generated by ADAM17-mediated shedding from neutrophil surface. Enables IL-6 trans-signaling: sIL-6R binds IL-6 and the complex activates gp130 on cells lacking membrane IL-6R (endothelial cells). This is the dominant pathological signaling mode in CRS.",
    modulators=(
        Modulator(
            name="Tocilizumab",
            mechanism="Blocks both membrane-bound IL-6R and sIL-6R",
            status=DrugStatus.APPROVED_CRS,
            route="IV",
            dose="8 mg/kg",
            evidence_refs=("PMID:32666058",),
        ),
        Modulator(
            name="sgp130Fc",
            mechanism="Soluble gp130-Fc fusion protein; selectively blocks IL-6 trans-signaling without affecting classical signaling",
            status=DrugStatus.INVESTIGATIONAL,
            route="IV",
            dose="Under investigation",
            evidence_refs=(),
        ),
    ),
    upstream_of=("gp130_dimerization", "endothelial_activation"),
    downstream_of=("ADAM17_neutrophil_shedding",),
    biomarker_utility="Elevated sIL-6R indicates active trans-signaling. Rise precedes endothelial activation.",
    references=("PMID:27455965", "PMID:30442748", "PMID:38123583"),
)

GP130 = MolecularTarget(
    target_id="TARGET:GP130",
    name="Glycoprotein 130 (gp130)",
    gene_symbol="IL6ST",
    category=TargetCategory.RECEPTOR,
    pathways=("IL-6_trans-signaling", "IL-6_classical_signaling", "JAK/STAT"),
    normal_range="Ubiquitously expressed",
    ae_range="N/A (signal transducer, not measured directly)",
    clinical_relevance="Universal signal transduction subunit for IL-6 family cytokines. Homodimerization by IL-6/sIL-6R complex activates JAK1/JAK2 and downstream STAT3 phosphorylation.",
    modulators=(),
    upstream_of=("JAK1", "JAK2", "STAT3"),
    downstream_of=("IL-6/IL-6R_complex", "IL-6/sIL-6R_complex"),
    references=("PMID:30442748",),
)

ANG2 = MolecularTarget(
    target_id="TARGET:ANG2",
    name="Angiopoietin-2 (Ang-2)",
    gene_symbol="ANGPT2",
    category=TargetCategory.GROWTH_FACTOR,
    pathways=("endothelial_activation", "BBB_disruption", "vascular_leak"),
    normal_range="<5 ng/mL",
    ae_range=">10 ng/mL during ICANS",
    clinical_relevance="Released from endothelial Weibel-Palade bodies during cytokine-driven activation. Antagonizes Tie2 signaling on pericytes, destabilizing vascular junctions. Ang-2:Ang-1 ratio correlates with ICANS severity.",
    modulators=(),
    upstream_of=("pericyte_detachment", "BBB_disruption", "vascular_leak"),
    downstream_of=("endothelial_activation", "IL-6_trans-signaling", "TNF-alpha"),
    biomarker_utility="Ang-2:Ang-1 ratio > 3 associated with severe ICANS. Part of the EASIX-derived endothelial activation signature.",
    references=("PMID:29025771",),
)


# ---------------------------------------------------------------------------
# Signaling kinases and transcription factors
# ---------------------------------------------------------------------------

JAK1 = MolecularTarget(
    target_id="TARGET:JAK1",
    name="Janus Kinase 1 (JAK1)",
    gene_symbol="JAK1",
    category=TargetCategory.KINASE,
    pathways=("JAK/STAT", "IL-6_signaling", "IFN-gamma_signaling"),
    normal_range="N/A (intracellular kinase)",
    ae_range="N/A (activity measured by phospho-STAT3 levels)",
    clinical_relevance="Receptor-associated kinase activated upon gp130 dimerization. Phosphorylates STAT3 to drive IL-6 target gene transcription. JAK/STAT activation occurs prior to cytokine cascade peak in CRS.",
    modulators=(
        Modulator(
            name="Ruxolitinib",
            mechanism="JAK1/JAK2 inhibitor; blocks downstream signaling of IL-6, IFN-gamma, and other JAK-dependent cytokines",
            status=DrugStatus.APPROVED_OTHER,
            route="PO",
            dose="5-20 mg BID",
            evidence_refs=("PMID:34265098",),
        ),
    ),
    upstream_of=("STAT3",),
    downstream_of=("gp130", "IFNGR"),
    references=("PMID:38123583",),
)

STAT3 = MolecularTarget(
    target_id="TARGET:STAT3",
    name="Signal Transducer and Activator of Transcription 3 (STAT3)",
    gene_symbol="STAT3",
    category=TargetCategory.TRANSCRIPTION_FACTOR,
    pathways=("JAK/STAT", "IL-6_signaling", "acute_phase_response"),
    normal_range="N/A (intracellular transcription factor)",
    ae_range="N/A (phosphorylation state measured)",
    clinical_relevance="Phosphorylated STAT3 drives transcription of IL-6, creating a positive feedback loop (STAT3 -> IL-6 gene -> IL-6 protein -> gp130 -> STAT3). Also drives CRP and ferritin expression.",
    modulators=(),
    upstream_of=("IL-6_transcription", "CRP", "ferritin", "acute_phase_response"),
    downstream_of=("JAK1", "JAK2"),
    references=("PMID:30442748",),
)

NFKB = MolecularTarget(
    target_id="TARGET:NFKB",
    name="Nuclear Factor kappa-B (NF-kB)",
    gene_symbol="NFKB1",
    category=TargetCategory.TRANSCRIPTION_FACTOR,
    pathways=("NF-kB", "TNF_signaling", "IL-1_signaling"),
    normal_range="N/A (intracellular transcription factor)",
    ae_range="N/A",
    clinical_relevance="Master inflammatory transcription factor. TNF-alpha/TNFR1 signaling activates NF-kB, which upregulates transcription of TNF, IL-6, IL-1beta, IL-8, and MCP-1. Creates a self-amplifying inflammatory loop.",
    modulators=(
        Modulator(
            name="Dexamethasone",
            mechanism="Glucocorticoid receptor agonist; inhibits NF-kB nuclear translocation and reduces inflammatory gene transcription",
            status=DrugStatus.APPROVED_CRS,
            route="IV/PO",
            dose="10 mg IV q6h for ICANS grade >= 2; 10-20 mg IV for CRS refractory to tocilizumab",
            evidence_refs=("PMID:29084955",),
        ),
    ),
    upstream_of=("IL-6_transcription", "TNF_transcription", "IL-1beta_transcription", "IL-8_transcription", "MCP-1_transcription"),
    downstream_of=("TNFR1", "IL-1R1", "TLR"),
    references=("PMID:29084955",),
)


# ---------------------------------------------------------------------------
# Biomarker targets
# ---------------------------------------------------------------------------

CRP = MolecularTarget(
    target_id="TARGET:CRP",
    name="C-Reactive Protein (CRP)",
    gene_symbol="CRP",
    category=TargetCategory.BIOMARKER,
    pathways=("acute_phase_response",),
    normal_range="<10 mg/L",
    ae_range="50-500 mg/L during CRS",
    clinical_relevance="Hepatic acute phase reactant driven by IL-6/STAT3 signaling. Accessible bedside surrogate for IL-6 levels. Rises within 6-12h of CRS onset.",
    modulators=(),
    upstream_of=(),
    downstream_of=("IL-6", "STAT3"),
    biomarker_utility="CRP > 100 mg/L correlates with grade >= 2 CRS. Easy to measure serially. Part of modified EASIX (mEASIX) score.",
    references=("PMID:28854140",),
)

FERRITIN = MolecularTarget(
    target_id="TARGET:FERRITIN",
    name="Ferritin",
    gene_symbol="FTH1/FTL",
    category=TargetCategory.BIOMARKER,
    pathways=("acute_phase_response", "macrophage_activation", "iron_metabolism"),
    normal_range="12-300 ng/mL",
    ae_range="1000-100,000 ng/mL; >10,000 ng/mL highly suggestive of HLH",
    clinical_relevance="Both a biomarker and potential mediator. IL-6-driven hepatic production AND direct macrophage secretion. Ferritin >10,000 ng/mL is a diagnostic criterion for IEC-HS (CAR-T HLH). Extreme levels reflect macrophage hyperactivation rather than just acute phase response.",
    modulators=(),
    upstream_of=(),
    downstream_of=("IL-6", "macrophage_activation", "STAT3"),
    biomarker_utility="Dual role: (1) CRS severity marker when 1000-5000 ng/mL; (2) HLH diagnostic criterion when >10,000 ng/mL. Serial ferritin trajectory distinguishes CRS (peaks and resolves) from HLH (sustained or rising).",
    references=("PMID:28854140", "PMID:36906275"),
)

EASIX = MolecularTarget(
    target_id="TARGET:EASIX",
    name="Endothelial Activation and Stress Index (EASIX)",
    gene_symbol="N/A",
    category=TargetCategory.BIOMARKER,
    pathways=("endothelial_activation",),
    normal_range="EASIX = LDH x creatinine / platelets; lower values normal",
    ae_range="Elevated values predict severe CRS and ICANS",
    clinical_relevance="Composite biomarker reflecting endothelial dysfunction: elevated LDH (cell damage), elevated creatinine (renal endothelial injury), and low platelets (consumption/sequestration). Calculable from routine bloodwork without specialized assays.",
    modulators=(),
    upstream_of=(),
    downstream_of=("endothelial_activation", "DIC"),
    biomarker_utility="Pre-infusion EASIX predicts CRS severity and non-relapse mortality. EASIX-MM variant (with additional parameters) stratifies ICANS risk: high-risk 50%, intermediate 28.4%, low 12.7%.",
    references=("PMID:39277881", "PMID:39256221"),
)


# ---------------------------------------------------------------------------
# Safety switch targets
# ---------------------------------------------------------------------------

ICASP9 = MolecularTarget(
    target_id="TARGET:ICASP9",
    name="Inducible Caspase-9 (iCasp9) Safety Switch",
    gene_symbol="CASP9_modified",
    category=TargetCategory.ENZYME,
    pathways=("apoptosis", "safety_switch"),
    normal_range="N/A (engineered transgene)",
    ae_range="N/A",
    clinical_relevance="Safety switch engineered into CAR-T construct. Fusion of modified human caspase-9 with FKBP12-F36V domain. Administration of dimerizer drug (AP1903/rimiducid) causes FKBP homodimerization, activating caspase-9 apoptosis pathway and eliminating >90% of CAR-T cells within hours.",
    modulators=(
        Modulator(
            name="AP1903 / Rimiducid",
            mechanism="Chemical inducer of dimerization (CID); binds FKBP12-F36V domain causing iCasp9 homodimerization and apoptosis activation",
            status=DrugStatus.INVESTIGATIONAL,
            route="IV",
            dose="0.4 mg/kg single dose",
            evidence_refs=("PMID:25389405", "PMID:22158166"),
        ),
    ),
    upstream_of=("caspase_cascade", "CAR-T_apoptosis"),
    downstream_of=("AP1903_dimerizer",),
    references=("PMID:25389405", "PMID:22158166"),
)


# ---------------------------------------------------------------------------
# Aggregated registry
# ---------------------------------------------------------------------------

MOLECULAR_TARGET_REGISTRY: dict[str, MolecularTarget] = {
    t.target_id: t for t in [
        IL6, IL1_BETA, IFN_GAMMA, TNF_ALPHA, IL18,
        SIL6R, GP130, ANG2,
        JAK1, STAT3, NFKB,
        CRP, FERRITIN, EASIX,
        ICASP9,
    ]
}


def get_target(target_id: str) -> MolecularTarget | None:
    """Look up a molecular target by ID.

    Args:
        target_id: Target identifier (e.g. "TARGET:IL6").

    Returns:
        The MolecularTarget, or None if not found.
    """
    return MOLECULAR_TARGET_REGISTRY.get(target_id)


def get_targets_by_category(category: TargetCategory) -> list[MolecularTarget]:
    """Return all targets of a given category.

    Args:
        category: The TargetCategory to filter on.

    Returns:
        List of matching MolecularTarget objects.
    """
    return [t for t in MOLECULAR_TARGET_REGISTRY.values() if t.category == category]


def get_druggable_targets() -> list[MolecularTarget]:
    """Return all targets that have at least one known modulator.

    Returns:
        List of MolecularTarget objects with modulators.
    """
    return [t for t in MOLECULAR_TARGET_REGISTRY.values() if t.modulators]


def get_targets_in_pathway(pathway_name: str) -> list[MolecularTarget]:
    """Return all targets that participate in a named pathway.

    Args:
        pathway_name: Pathway name (e.g. "IL-6_trans-signaling").

    Returns:
        List of matching MolecularTarget objects.
    """
    return [
        t for t in MOLECULAR_TARGET_REGISTRY.values()
        if pathway_name in t.pathways
    ]
