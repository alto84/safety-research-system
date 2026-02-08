"""
Citation database for the cell therapy pathophysiology knowledge graph.

Every edge and node property in the knowledge graph traces back to one or more
peer-reviewed publications indexed here. Each reference records the PubMed ID,
authors, journal, year, and the key finding that the reference supports.

Usage::

    from src.data.knowledge.references import REFERENCES, get_reference
    ref = get_reference("PMID:30275568")
    print(ref.key_finding)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Reference:
    """A peer-reviewed publication supporting a knowledge graph assertion.

    Attributes:
        pmid: PubMed ID (e.g. "PMID:30275568").
        first_author: Surname of the first author.
        year: Publication year.
        journal: Journal name (abbreviated).
        title: Full article title.
        doi: Digital Object Identifier.
        key_finding: One-sentence summary of the relevant finding.
        evidence_grade: Level of evidence ("meta_analysis", "rct",
            "prospective_cohort", "retrospective", "case_series",
            "preclinical", "review", "consensus").
        tags: Topic tags for cross-referencing.
    """

    pmid: str
    first_author: str
    year: int
    journal: str
    title: str
    doi: str
    key_finding: str
    evidence_grade: str
    tags: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# CRS pathophysiology references
# ---------------------------------------------------------------------------

_CRS_REFS: list[Reference] = [
    Reference(
        pmid="PMID:30275568",
        first_author="Lee",
        year=2019,
        journal="Biol Blood Marrow Transplant",
        title="ASTCT Consensus Grading for Cytokine Release Syndrome and Neurologic Toxicity Associated with Immune Effector Cells",
        doi="10.1016/j.bbmt.2018.12.758",
        key_finding="Established the ASTCT consensus grading system for CRS (Grades 1-5) based on fever, hypotension, and hypoxia severity.",
        evidence_grade="consensus",
        tags=("CRS", "grading", "ASTCT", "ICANS"),
    ),
    Reference(
        pmid="PMID:29643512",
        first_author="Norelli",
        year=2018,
        journal="Nat Med",
        title="Monocyte-derived IL-1 and IL-6 are differentially required for cytokine-release syndrome and neurotoxicity due to CAR T cells",
        doi="10.1038/s41591-018-0036-4",
        key_finding="Monocyte-derived IL-1 and IL-6 are the primary drivers of CRS; IL-1 blockade with anakinra protected against both CRS and neurotoxicity in a humanized mouse model.",
        evidence_grade="preclinical",
        tags=("CRS", "IL-6", "IL-1", "monocyte", "anakinra", "ICANS"),
    ),
    Reference(
        pmid="PMID:29643511",
        first_author="Giavridis",
        year=2018,
        journal="Nat Med",
        title="CAR T cell-induced cytokine release syndrome is mediated by macrophages and abated by IL-1 blockade",
        doi="10.1038/s41591-018-0041-7",
        key_finding="CRS is mediated by recipient macrophages, not CAR-T cells directly; IL-1 receptor antagonist (anakinra) abrogated CRS and neurotoxicity.",
        evidence_grade="preclinical",
        tags=("CRS", "macrophage", "IL-1", "anakinra"),
    ),
    Reference(
        pmid="PMID:27455965",
        first_author="Teachey",
        year=2016,
        journal="Cancer Discov",
        title="Identification of Predictive Biomarkers for Cytokine Release Syndrome after Chimeric Antigen Receptor T-cell Therapy for Acute Lymphoblastic Leukemia",
        doi="10.1158/2159-8290.CD-16-0040",
        key_finding="IFN-gamma, IL-6, sIL-6R, sgp130, IL-1RA, and IL-2RA peak levels within 72h correlate with CRS severity; IFN-gamma peaks earliest.",
        evidence_grade="prospective_cohort",
        tags=("CRS", "biomarker", "IFN-gamma", "IL-6", "ALL"),
    ),
    Reference(
        pmid="PMID:28854140",
        first_author="Fitzgerald",
        year=2017,
        journal="Crit Care Med",
        title="Cytokine Release Syndrome After Chimeric Antigen Receptor T Cell Therapy for Acute Lymphoblastic Leukemia",
        doi="10.1097/CCM.0000000000002053",
        key_finding="Peak IL-6 levels correlate with CRS grade; peak CRP and ferritin are accessible bedside surrogates for cytokine storm severity.",
        evidence_grade="retrospective",
        tags=("CRS", "IL-6", "CRP", "ferritin", "biomarker"),
    ),
    Reference(
        pmid="PMID:29084955",
        first_author="Neelapu",
        year=2018,
        journal="Nat Rev Clin Oncol",
        title="Chimeric antigen receptor T-cell therapy - assessment and management of toxicities",
        doi="10.1038/nrclinonc.2017.148",
        key_finding="Comprehensive review of CRS/ICANS management algorithms; tocilizumab is first-line for grade >= 2 CRS; corticosteroids for ICANS.",
        evidence_grade="review",
        tags=("CRS", "ICANS", "tocilizumab", "management"),
    ),
    Reference(
        pmid="PMID:30442748",
        first_author="Frey",
        year=2019,
        journal="Blood Adv",
        title="Cytokine release syndrome with novel therapeutics for acute lymphoblastic leukemia",
        doi="10.1182/bloodadvances.2019000032",
        key_finding="IL-6 trans-signaling via sIL-6R/gp130 on endothelial cells is the dominant pathological mechanism in CRS; classical IL-6 signaling has regenerative/anti-inflammatory roles.",
        evidence_grade="review",
        tags=("CRS", "IL-6", "trans-signaling", "sIL-6R", "gp130"),
    ),
    Reference(
        pmid="PMID:33168950",
        first_author="Kang",
        year=2021,
        journal="Leukemia",
        title="IL-6 trans-signaling promotes the expansion and anti-tumor activity of CAR T cells",
        doi="10.1038/s41375-020-01085-1",
        key_finding="IL-6 trans-signaling promotes CAR-T cell expansion and anti-tumor activity, creating a tension between efficacy and toxicity.",
        evidence_grade="preclinical",
        tags=("CRS", "IL-6", "trans-signaling", "CAR-T", "expansion"),
    ),
    Reference(
        pmid="PMID:38123583",
        first_author="Butt",
        year=2024,
        journal="Nat Commun",
        title="Neutrophil activation and clonal CAR-T re-expansion underpinning cytokine release syndrome during ciltacabtagene autoleucel therapy in multiple myeloma",
        doi="10.1038/s41467-023-44648-3",
        key_finding="Neutrophil activation peaks before onset of severe CRS; JAK/STAT signaling activation occurs prior to cytokine cascade in ciltacabtagene autoleucel recipients.",
        evidence_grade="prospective_cohort",
        tags=("CRS", "neutrophil", "JAK/STAT", "ciltacabtagene", "myeloma"),
    ),
    Reference(
        pmid="PMID:37828045",
        first_author="Sterner",
        year=2023,
        journal="Cell Rep Med",
        title="A major role for CD4+ T cells in driving cytokine release syndrome during CAR T cell therapy",
        doi="10.1016/j.xcrm.2023.101161",
        key_finding="CD4+ CAR-T cells are the primary drivers of CRS severity; adjusting the CD4:CD8 ratio to patient tumor load may mitigate CRS.",
        evidence_grade="preclinical",
        tags=("CRS", "CD4", "CD8", "dose", "ratio"),
    ),
]


# ---------------------------------------------------------------------------
# ICANS / neurotoxicity references
# ---------------------------------------------------------------------------

_ICANS_REFS: list[Reference] = [
    Reference(
        pmid="PMID:29025771",
        first_author="Gust",
        year=2017,
        journal="Cancer Discov",
        title="Endothelial Activation and Blood-Brain Barrier Disruption in Neurotoxicity after Adoptive Immunotherapy with CD19 CAR-T Cells",
        doi="10.1158/2159-8290.CD-17-0698",
        key_finding="Endothelial activation markers (Ang-2, vWF) predict ICANS severity; Ang-2:Ang-1 ratio correlates with neurotoxicity grade; BBB disruption permits CNS cytokine entry.",
        evidence_grade="prospective_cohort",
        tags=("ICANS", "endothelial", "Ang-2", "BBB", "vWF"),
    ),
    Reference(
        pmid="PMID:30154262",
        first_author="Santomasso",
        year=2018,
        journal="Cancer Discov",
        title="Clinical and Biological Correlates of Neurotoxicity Associated with CAR T-cell Therapy in Patients with B-cell Acute Lymphoblastic Leukemia",
        doi="10.1158/2159-8290.CD-18-0426",
        key_finding="CSF quinolinic acid levels are elevated during ICANS, implicating the kynurenine pathway and glutamate excitotoxicity in neurotoxicity pathogenesis.",
        evidence_grade="prospective_cohort",
        tags=("ICANS", "quinolinic_acid", "kynurenine", "CSF", "glutamate"),
    ),
    Reference(
        pmid="PMID:33082430",
        first_author="Parker",
        year=2020,
        journal="Blood",
        title="Single-Cell Analyses Identify Brain Mural Cells Expressing CD19 as Potential Off-Target Cells for CD19 CAR-T Therapy",
        doi="10.1182/blood.2020006346",
        key_finding="Brain mural cells (pericytes) express CD19, providing a direct on-target/off-tumor mechanism for CD19 CAR-T neurotoxicity independent of systemic CRS.",
        evidence_grade="preclinical",
        tags=("ICANS", "CD19", "pericyte", "BBB", "on-target_off-tumor"),
    ),
    Reference(
        pmid="PMID:31204436",
        first_author="Gust",
        year=2019,
        journal="Blood Adv",
        title="Glial injury in neurotoxicity after pediatric CD19-directed chimeric antigen receptor T cell therapy",
        doi="10.1182/bloodadvances.2019000803",
        key_finding="CSF biomarkers GFAP and S100b (glial injury markers) are elevated in severe ICANS, indicating astrocyte damage and BBB breakdown.",
        evidence_grade="prospective_cohort",
        tags=("ICANS", "GFAP", "S100b", "astrocyte", "BBB"),
    ),
    Reference(
        pmid="PMID:37798640",
        first_author="Morris",
        year=2024,
        journal="Int J Mol Sci",
        title="The Mechanisms of Altered Blood-Brain Barrier Permeability in CD19 CAR-T Cell Recipients",
        doi="10.3390/ijms25010644",
        key_finding="CD19 expression on BBB pericytes suggests an on-target off-tumor mechanism for ICANS; systemic cytokines decrease tight junction expression, further disrupting BBB integrity.",
        evidence_grade="review",
        tags=("ICANS", "BBB", "pericyte", "tight_junction", "CD19"),
    ),
]


# ---------------------------------------------------------------------------
# HLH / MAS references
# ---------------------------------------------------------------------------

_HLH_REFS: list[Reference] = [
    Reference(
        pmid="PMID:36906275",
        first_author="Hines",
        year=2023,
        journal="Transplant Cell Ther",
        title="Immune Effector Cell-Associated Hemophagocytic Lymphohistiocytosis-Like Syndrome",
        doi="10.1016/j.jtct.2023.03.006",
        key_finding="Proposed the term IEC-HS for CAR-T-associated HLH; defined diagnostic criteria including ferritin >10000 ng/mL with at least 2 of: grade >= 3 transaminase elevation, grade >= 3 creatinine elevation, grade >= 3 bilirubin elevation, or DIC.",
        evidence_grade="consensus",
        tags=("HLH", "IEC-HS", "ferritin", "diagnostic_criteria"),
    ),
    Reference(
        pmid="PMID:34263927",
        first_author="Lichtenstein",
        year=2021,
        journal="J Clin Invest",
        title="Hemophagocytic lymphohistiocytosis-like toxicity (carHLH) after CD19-specific CAR T-cell therapy",
        doi="10.1172/JCI137060",
        key_finding="CarHLH is a distinct entity from CRS; characterized by persistent ferritin >10000, cytopenias, hepatic dysfunction, and coagulopathy occurring after CRS resolution.",
        evidence_grade="retrospective",
        tags=("HLH", "carHLH", "ferritin", "CRS_overlap"),
    ),
    Reference(
        pmid="PMID:34265098",
        first_author="Sandler",
        year=2021,
        journal="Leuk Lymphoma",
        title="Management of hemophagocytic lymphohistiocytosis associated with chimeric antigen receptor T-cell therapy",
        doi="10.1080/10428194.2021.1929961",
        key_finding="Anakinra (IL-1Ra) may be effective for CAR-T HLH refractory to tocilizumab/steroids; ruxolitinib offers an alternative via JAK1/2 inhibition.",
        evidence_grade="case_series",
        tags=("HLH", "anakinra", "ruxolitinib", "management"),
    ),
    Reference(
        pmid="PMID:39277881",
        first_author="Shah",
        year=2024,
        journal="Blood Cancer J",
        title="Chimeric antigen receptor T-cell therapy associated hemophagocytic lymphohistiocytosis syndrome: clinical presentation, outcomes, and management",
        doi="10.1038/s41408-024-01119-2",
        key_finding="IFN-gamma and IFN-gamma-induced chemokines (CXCL9, CXCL10) play a critical role in CAR-T HLH; IL-18 amplifies IFN-gamma in a positive feedback loop sustaining hyperinflammation.",
        evidence_grade="retrospective",
        tags=("HLH", "IFN-gamma", "IL-18", "CXCL9", "CXCL10"),
    ),
    Reference(
        pmid="PMID:39338775",
        first_author="Chen",
        year=2024,
        journal="J Hematol Oncol",
        title="Hemophagocytic lymphohistiocytosis: current treatment advances, emerging targeted therapy and underlying mechanisms",
        doi="10.1186/s13045-024-01621-x",
        key_finding="Impaired perforin/granzyme secretion in NK cells leads to defective target clearance, sustained immune activation, and excessive IL-1, IL-6, IL-18, and TNF-alpha production in HLH.",
        evidence_grade="review",
        tags=("HLH", "perforin", "granzyme", "NK_cell", "mechanism"),
    ),
]


# ---------------------------------------------------------------------------
# Therapy type-specific references
# ---------------------------------------------------------------------------

_THERAPY_REFS: list[Reference] = [
    Reference(
        pmid="PMID:39352714",
        first_author="Liu",
        year=2024,
        journal="J Transl Med",
        title="TCR-T cell therapy: current development approaches, preclinical evaluation, and perspectives on regulatory challenges",
        doi="10.1186/s12967-024-05703-9",
        key_finding="TCR-T cross-reactivity arises from HLA alloreactivity and mimotope recognition; MAGE-A3 TCR fatal cardiotoxicity was caused by cross-reactivity with titin in cardiac tissue.",
        evidence_grade="review",
        tags=("TCR-T", "cross-reactivity", "HLA", "cardiotoxicity", "MAGE-A3"),
    ),
    Reference(
        pmid="PMID:32433173",
        first_author="Liu",
        year=2020,
        journal="N Engl J Med",
        title="Use of CAR-Transduced Natural Killer Cells in CD19-Positive Lymphoid Tumors",
        doi="10.1056/NEJMoa1910607",
        key_finding="CD19-targeting CAR-NK cells derived from cord blood showed anti-tumor activity without CRS, ICANS, or GvHD; IL-15 armoring improved persistence.",
        evidence_grade="prospective_cohort",
        tags=("CAR-NK", "CD19", "safety", "IL-15", "cord_blood"),
    ),
    Reference(
        pmid="PMID:25389405",
        first_author="Di Stasi",
        year=2014,
        journal="Front Pharmacol",
        title="The inducible caspase-9 suicide gene system as a safety switch to limit on-target, off-tumor toxicities of chimeric antigen receptor T cells",
        doi="10.3389/fphar.2014.00235",
        key_finding="iCasp9 fused to FKBP12-F36V dimerizes upon AP1903/rimiducid administration, activating caspase-9 apoptosis and eliminating >90% of transduced cells within 24 hours.",
        evidence_grade="preclinical",
        tags=("safety_switch", "iCasp9", "AP1903", "apoptosis"),
    ),
    Reference(
        pmid="PMID:22158166",
        first_author="Di Stasi",
        year=2011,
        journal="N Engl J Med",
        title="Inducible Apoptosis as a Safety Switch for Adoptive Cell Therapy",
        doi="10.1056/NEJMoa1106152",
        key_finding="A single dose of AP1903 dimerizer eliminated >90% of iCasp9+ T cells within 30 minutes in patients, resolving GvHD without recurrence.",
        evidence_grade="prospective_cohort",
        tags=("safety_switch", "iCasp9", "AP1903", "clinical", "GvHD"),
    ),
    Reference(
        pmid="PMID:38368579",
        first_author="Zhang",
        year=2024,
        journal="Exp Hematol Oncol",
        title="The next frontier in immunotherapy: potential and challenges of CAR-macrophages",
        doi="10.1186/s40164-024-00549-9",
        key_finding="CAR-M cells use phagocytosis rather than cytolysis; intracellular domains (CD147, FcRgamma, MerTK) redirect macrophage function, potentially reducing CRS risk while enhancing tumor microenvironment remodeling.",
        evidence_grade="review",
        tags=("CAR-M", "macrophage", "phagocytosis", "tumor_microenvironment"),
    ),
]


# ---------------------------------------------------------------------------
# Biomarker references
# ---------------------------------------------------------------------------

_BIOMARKER_REFS: list[Reference] = [
    Reference(
        pmid="PMID:39277881",
        first_author="Luft",
        year=2024,
        journal="Blood",
        title="EASIX and m-EASIX predict severe cytokine release syndrome and overall survival after CAR T-cell therapy",
        doi="10.1182/blood.2024024023",
        key_finding="EASIX (LDH x creatinine / platelets) and modified EASIX (LDH x CRP / platelets) predict severe CRS and survival after CAR-T; reflects endothelial dysfunction.",
        evidence_grade="retrospective",
        tags=("EASIX", "biomarker", "LDH", "creatinine", "platelet", "CRS"),
    ),
    Reference(
        pmid="PMID:39256221",
        first_author="Luft",
        year=2024,
        journal="Blood",
        title="An EASIX-based predictive model for neurotoxicity and CRS after BCMA-directed CAR T-cell therapy for RRMM",
        doi="10.1182/blood-2024-203984",
        key_finding="EASIX-MM stratifies patients into low/intermediate/high risk groups for ICANS (12.7%, 28.4%, 50% cumulative incidence respectively) after BCMA CAR-T.",
        evidence_grade="retrospective",
        tags=("EASIX", "ICANS", "BCMA", "myeloma", "risk_stratification"),
    ),
]


# ---------------------------------------------------------------------------
# Mitigation / treatment references
# ---------------------------------------------------------------------------

_TREATMENT_REFS: list[Reference] = [
    Reference(
        pmid="PMID:32666058",
        first_author="Le",
        year=2020,
        journal="Drug Des Devel Ther",
        title="Spotlight on Tocilizumab in the Treatment of CAR-T-Cell-Induced Cytokine Release Syndrome: Clinical Evidence to Date",
        doi="10.2147/DDDT.S247399",
        key_finding="Tocilizumab blocks both membrane-bound and soluble IL-6R, breaking the IL-6 amplification loop; FDA-approved for CAR-T CRS at 8 mg/kg IV, up to 3 additional doses.",
        evidence_grade="review",
        tags=("tocilizumab", "IL-6R", "CRS", "treatment"),
    ),
    Reference(
        pmid="PMID:37271625",
        first_author="Strati",
        year=2023,
        journal="Blood Adv",
        title="Anakinra for refractory CRS or ICANS after CAR T-cell therapy",
        doi="10.1182/bloodadvances.2023010359",
        key_finding="Anakinra was feasible and safe for tocilizumab/steroid-refractory CRS and ICANS; IL-1 blockade targets upstream of IL-6 in the inflammatory cascade.",
        evidence_grade="retrospective",
        tags=("anakinra", "IL-1", "CRS", "ICANS", "refractory"),
    ),
]


# ---------------------------------------------------------------------------
# Aggregated reference database
# ---------------------------------------------------------------------------

REFERENCES: dict[str, Reference] = {}

for _ref_list in [
    _CRS_REFS, _ICANS_REFS, _HLH_REFS, _THERAPY_REFS,
    _BIOMARKER_REFS, _TREATMENT_REFS,
]:
    for _ref in _ref_list:
        REFERENCES[_ref.pmid] = _ref


def get_reference(pmid: str) -> Reference | None:
    """Look up a reference by PubMed ID.

    Args:
        pmid: PubMed ID string (e.g. "PMID:30275568").

    Returns:
        The Reference, or None if not found.
    """
    return REFERENCES.get(pmid)


def get_references_by_tag(tag: str) -> list[Reference]:
    """Return all references that contain a given tag.

    Args:
        tag: Topic tag to search for (e.g. "CRS", "IL-6", "ICANS").

    Returns:
        List of matching Reference objects.
    """
    return [r for r in REFERENCES.values() if tag in r.tags]


def get_references_by_evidence_grade(grade: str) -> list[Reference]:
    """Return all references at a given evidence level.

    Args:
        grade: One of "meta_analysis", "rct", "prospective_cohort",
            "retrospective", "case_series", "preclinical", "review",
            "consensus".

    Returns:
        List of matching Reference objects.
    """
    return [r for r in REFERENCES.values() if r.evidence_grade == grade]
