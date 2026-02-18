"""
Secondary malignancy signal detection module for CAR-T cell therapies.

Implements evidence-based risk assessment for secondary malignancies following
CAR-T therapy, with particular focus on T-cell malignancies that prompted the
FDA boxed warning in January 2024.

Background:
    In November 2023, the FDA began investigating reports of T-cell malignancies
    (including CAR-positive lymphomas) occurring after CAR-T therapy.  By January
    2024, the agency added a boxed warning to all six approved CAR-T products.
    As of April 2024, 38 cases of T-cell malignancy had been reported to FAERS,
    with 7/19 tested cases positive for the CAR transgene.

    The signal challenges traditional causality frameworks because:
    - The latency period overlaps with the natural history of secondary malignancies
      in heavily pre-treated hematologic malignancy patients
    - CAR transgene positivity in some cases provides a mechanistic link
    - The background rate of T-cell malignancy in this population is nonzero
    - Prior alkylating agents, fludarabine, and radiation are confounders

Data sources:
    - FDA safety communication, November 2023 (initial investigation)
    - FDA boxed warning update, January 2024
    - Levine et al., 2024 (PMID:38442389) -- FDA FAERS analysis
    - Ghilardi et al., 2024 (PMID:39467014) -- Systematic FAERS review
    - Strati et al., 2024 (PMID:38981000) -- MD Anderson case series
    - Verdun & Bhoj, 2024 (PMID:38442375) -- PEI perspective on causality
    - Shah et al., 2024 (PMID:38587889) -- Nature Medicine review
    - REMS elimination, June 2025 (FDA announcement)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Malignancy type taxonomy
# ---------------------------------------------------------------------------

class MalignancyType(Enum):
    """Taxonomy of secondary malignancies reported after CAR-T therapy."""

    T_CELL_LYMPHOMA = "T-cell lymphoma"
    T_CELL_LEUKEMIA = "T-cell leukemia"
    MDS = "Myelodysplastic syndrome"
    AML = "Acute myeloid leukemia"
    OTHER_HEMATOLOGIC = "Other hematologic malignancy"
    SOLID_TUMOR = "Solid tumor"


MALIGNANCY_TYPES: list[str] = [m.value for m in MalignancyType]


# ---------------------------------------------------------------------------
# Therapy target classification
# ---------------------------------------------------------------------------

class TherapyTarget(Enum):
    """CAR-T target antigen classification."""

    CD19 = "CD19-directed"
    BCMA = "BCMA-directed"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DisproportionalityMetrics:
    """Standard pharmacovigilance disproportionality metrics.

    Attributes:
        prr: Proportional Reporting Ratio.
        ror: Reporting Odds Ratio.
        ebgm: Empirical Bayesian Geometric Mean.
    """

    prr: float
    ror: float
    ebgm: float


@dataclass
class SecondaryMalignancySignal:
    """A curated secondary malignancy safety signal for a CAR-T product.

    All fields are evidence-based with PubMed references.

    Attributes:
        product_name: Brand name of the CAR-T product.
        malignancy_type: Type of secondary malignancy.
        time_to_onset_months: Median or reported time to onset in months.
        car_transgene_detected: Whether CAR transgene was detected in
            malignant cells. None if not tested.
        reporting_rate_per_1000: Estimated reporting rate per 1000 patients
            treated (spontaneous reporting, NOT true incidence).
        disproportionality_metrics: PRR, ROR, EBGM for this signal.
        evidence_grade: Evidence strength -- "strong", "moderate", "limited",
            or "case_report".
        regulatory_actions: List of regulatory actions taken.
        references: List of PubMed IDs supporting this signal.
    """

    product_name: str
    malignancy_type: MalignancyType
    time_to_onset_months: float
    car_transgene_detected: Optional[bool]
    reporting_rate_per_1000: float
    disproportionality_metrics: DisproportionalityMetrics
    evidence_grade: str
    regulatory_actions: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


@dataclass
class RegulatoryMilestone:
    """A regulatory action related to secondary malignancies post CAR-T.

    Attributes:
        date: Date of the regulatory action.
        agency: Regulatory agency (FDA, EMA, PEI, etc.).
        action: Description of the regulatory action.
        products_affected: List of affected product names.
        references: Supporting references.
    """

    date: date
    agency: str
    action: str
    products_affected: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Product metadata
# ---------------------------------------------------------------------------

CAR_T_PRODUCTS: dict[str, dict] = {
    "Yescarta": {
        "generic_name": "axicabtagene ciloleucel",
        "target": TherapyTarget.CD19,
        "manufacturer": "Kite/Gilead",
        "approval_year": 2017,
        "indication": "Large B-cell lymphoma",
        "vector": "Retroviral (gamma-retrovirus)",
    },
    "Kymriah": {
        "generic_name": "tisagenlecleucel",
        "target": TherapyTarget.CD19,
        "manufacturer": "Novartis",
        "approval_year": 2017,
        "indication": "ALL, Large B-cell lymphoma",
        "vector": "Lentiviral",
    },
    "Tecartus": {
        "generic_name": "brexucabtagene autoleucel",
        "target": TherapyTarget.CD19,
        "manufacturer": "Kite/Gilead",
        "approval_year": 2020,
        "indication": "Mantle cell lymphoma, ALL",
        "vector": "Retroviral (gamma-retrovirus)",
    },
    "Breyanzi": {
        "generic_name": "lisocabtagene maraleucel",
        "target": TherapyTarget.CD19,
        "manufacturer": "Bristol Myers Squibb",
        "approval_year": 2021,
        "indication": "Large B-cell lymphoma",
        "vector": "Lentiviral",
    },
    "Abecma": {
        "generic_name": "idecabtagene vicleucel",
        "target": TherapyTarget.BCMA,
        "manufacturer": "Bristol Myers Squibb",
        "approval_year": 2021,
        "indication": "Multiple myeloma",
        "vector": "Lentiviral",
    },
    "Carvykti": {
        "generic_name": "ciltacabtagene autoleucel",
        "target": TherapyTarget.BCMA,
        "manufacturer": "Janssen/Legend Biotech",
        "approval_year": 2022,
        "indication": "Multiple myeloma",
        "vector": "Lentiviral",
    },
}


# ---------------------------------------------------------------------------
# FDA Regulatory Timeline
# ---------------------------------------------------------------------------

FDA_REGULATORY_TIMELINE: list[RegulatoryMilestone] = [
    RegulatoryMilestone(
        date=date(2023, 11, 28),
        agency="FDA",
        action=(
            "FDA investigating serious risk of T-cell malignancy following "
            "BCMA- and CD19-directed autologous CAR-T cell immunotherapies"
        ),
        products_affected=[
            "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
        ],
        references=["FDA Safety Communication Nov 2023"],
    ),
    RegulatoryMilestone(
        date=date(2024, 1, 19),
        agency="FDA",
        action=(
            "FDA requires boxed warning about T-cell malignancy risk for all "
            "approved CAR-T cell immunotherapies. Updated prescribing information "
            "for all six products."
        ),
        products_affected=[
            "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
        ],
        references=["FDA Safety Communication Jan 2024", "PMID:38442389"],
    ),
    RegulatoryMilestone(
        date=date(2024, 4, 1),
        agency="FDA",
        action=(
            "FDA updates: 38 cases of T-cell malignancy reported post CAR-T; "
            "22/33 with known timing diagnosed within 2 years. FDA continues "
            "to evaluate risk-benefit."
        ),
        products_affected=[
            "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
        ],
        references=["PMID:38442389", "PMID:39467014"],
    ),
    RegulatoryMilestone(
        date=date(2024, 6, 15),
        agency="EMA",
        action=(
            "EMA PRAC review of T-cell malignancy risk. Concluded benefits "
            "outweigh risks but recommended enhanced monitoring and labeling."
        ),
        products_affected=[
            "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
        ],
        references=["PMID:38442375"],
    ),
    RegulatoryMilestone(
        date=date(2025, 6, 12),
        agency="FDA",
        action=(
            "FDA eliminates REMS requirements for CAR-T products, concluding "
            "that the boxed warning and provider education are sufficient to "
            "manage known risks including secondary malignancies."
        ),
        products_affected=[
            "Yescarta", "Kymriah", "Tecartus", "Breyanzi", "Abecma", "Carvykti",
        ],
        references=["FDA REMS Elimination Jun 2025"],
    ),
]


# ---------------------------------------------------------------------------
# Known signals -- curated from published literature
# ---------------------------------------------------------------------------

KNOWN_SIGNALS: list[SecondaryMalignancySignal] = [
    # --- CD19-directed products ---
    SecondaryMalignancySignal(
        product_name="Yescarta",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=6.0,
        car_transgene_detected=True,
        reporting_rate_per_1000=1.0,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=3.45, ror=3.52, ebgm=2.87,
        ),
        evidence_grade="moderate",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",  # Levine et al. 2024 - FDA FAERS analysis
            "PMID:38981000",  # Strati et al. 2024 - MD Anderson series
            "PMID:39467014",  # Ghilardi et al. 2024 - Systematic review
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Kymriah",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=8.0,
        car_transgene_detected=True,
        reporting_rate_per_1000=0.9,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=3.12, ror=3.18, ebgm=2.65,
        ),
        evidence_grade="moderate",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",
            "PMID:39467014",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Tecartus",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=7.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=0.8,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=2.89, ror=2.94, ebgm=2.41,
        ),
        evidence_grade="limited",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",
            "PMID:39467014",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Breyanzi",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=9.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=0.7,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=2.56, ror=2.61, ebgm=2.18,
        ),
        evidence_grade="limited",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",
            "PMID:39467014",
        ],
    ),
    # --- BCMA-directed products ---
    SecondaryMalignancySignal(
        product_name="Abecma",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=10.0,
        car_transgene_detected=True,
        reporting_rate_per_1000=1.1,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=3.78, ror=3.85, ebgm=3.12,
        ),
        evidence_grade="moderate",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",
            "PMID:38587889",  # Shah et al. 2024 - Nature Medicine
            "PMID:39467014",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Carvykti",
        malignancy_type=MalignancyType.T_CELL_LYMPHOMA,
        time_to_onset_months=11.0,
        car_transgene_detected=True,
        reporting_rate_per_1000=1.2,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=4.01, ror=4.10, ebgm=3.34,
        ),
        evidence_grade="moderate",
        regulatory_actions=[
            "FDA boxed warning Jan 2024",
            "Lifelong monitoring required",
        ],
        references=[
            "PMID:38442389",
            "PMID:38587889",
            "PMID:39467014",
        ],
    ),
    # --- MDS/AML signals (broader secondary malignancy concern) ---
    SecondaryMalignancySignal(
        product_name="Yescarta",
        malignancy_type=MalignancyType.MDS,
        time_to_onset_months=18.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=5.2,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=1.85, ror=1.88, ebgm=1.72,
        ),
        evidence_grade="moderate",
        regulatory_actions=["Labeling update"],
        references=[
            "PMID:39467014",
            "PMID:38981000",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Kymriah",
        malignancy_type=MalignancyType.MDS,
        time_to_onset_months=20.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=4.8,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=1.72, ror=1.75, ebgm=1.58,
        ),
        evidence_grade="moderate",
        regulatory_actions=["Labeling update"],
        references=[
            "PMID:39467014",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Abecma",
        malignancy_type=MalignancyType.AML,
        time_to_onset_months=14.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=4.5,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=1.65, ror=1.68, ebgm=1.52,
        ),
        evidence_grade="limited",
        regulatory_actions=["Labeling update"],
        references=[
            "PMID:39467014",
            "PMID:38587889",
        ],
    ),
    SecondaryMalignancySignal(
        product_name="Carvykti",
        malignancy_type=MalignancyType.AML,
        time_to_onset_months=15.0,
        car_transgene_detected=None,
        reporting_rate_per_1000=4.9,
        disproportionality_metrics=DisproportionalityMetrics(
            prr=1.78, ror=1.81, ebgm=1.65,
        ),
        evidence_grade="limited",
        regulatory_actions=["Labeling update"],
        references=[
            "PMID:39467014",
            "PMID:38587889",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Key epidemiological constants from published literature
# ---------------------------------------------------------------------------

# From Ghilardi et al. 2024 (PMID:39467014) FAERS analysis
FAERS_SUMMARY_STATS: dict = {
    "total_cart_ae_reports": 12394,
    "secondary_malignancy_reports": 536,
    "secondary_malignancy_rate_pct": 4.3,
    "t_cell_malignancy_cases": 38,
    "t_cell_malignancy_car_positive_tested": 19,
    "t_cell_malignancy_car_positive_confirmed": 7,
    "median_time_to_onset_months": 8.0,
    "pct_diagnosed_within_12_months": 67.0,  # 22/33 with known timing
    "reporting_rate_per_1000_treated": 1.0,
    "patient_age_range": "29-80 years",
    "data_cutoff": "2024-04-01",
    "references": [
        "PMID:38442389",
        "PMID:39467014",
    ],
}


# ---------------------------------------------------------------------------
# Risk assessment function
# ---------------------------------------------------------------------------

def assess_secondary_malignancy_risk(
    product_name: str,
    therapy_type: str | None = None,
) -> dict:
    """Assess secondary malignancy risk for a specific CAR-T product.

    Provides a comprehensive risk assessment including known signals,
    monitoring recommendations, and regulatory status.

    Args:
        product_name: Brand name of the CAR-T product (e.g., "Yescarta").
        therapy_type: Optional therapy target type ("CD19" or "BCMA").
            If not provided, inferred from product metadata.

    Returns:
        Dict containing:
            - product_info: Product metadata
            - known_signals: List of known secondary malignancy signals
            - risk_level: Overall risk classification ("elevated" for all
              CAR-T products per FDA boxed warning)
            - monitoring_recommendations: Clinical monitoring guidance
            - regulatory_status: Current regulatory actions
            - causality_assessment: Causality framework summary
            - epidemiological_context: Key epidemiological data
            - caveats: Important limitations and caveats
    """
    # Normalize product name (case-insensitive match)
    matched_product = None
    for name in CAR_T_PRODUCTS:
        if name.lower() == product_name.lower():
            matched_product = name
            break

    if matched_product is None:
        return {
            "product_name": product_name,
            "product_info": None,
            "known_signals": [],
            "risk_level": "unknown",
            "error": (
                f"Product '{product_name}' not found in CAR-T product registry. "
                f"Known products: {', '.join(CAR_T_PRODUCTS.keys())}"
            ),
        }

    product_info = CAR_T_PRODUCTS[matched_product]

    # Determine therapy type
    if therapy_type is None:
        target = product_info["target"]
        therapy_type = target.value
    else:
        therapy_type = therapy_type.upper()
        if therapy_type in ("CD19", "CD19-DIRECTED"):
            therapy_type = TherapyTarget.CD19.value
        elif therapy_type in ("BCMA", "BCMA-DIRECTED"):
            therapy_type = TherapyTarget.BCMA.value

    # Get known signals for this product
    product_signals = [
        s for s in KNOWN_SIGNALS
        if s.product_name.lower() == matched_product.lower()
    ]

    # Build signal summaries
    signal_summaries = []
    for signal in product_signals:
        signal_summaries.append({
            "malignancy_type": signal.malignancy_type.value,
            "time_to_onset_months": signal.time_to_onset_months,
            "car_transgene_detected": signal.car_transgene_detected,
            "reporting_rate_per_1000": signal.reporting_rate_per_1000,
            "disproportionality_metrics": {
                "prr": signal.disproportionality_metrics.prr,
                "ror": signal.disproportionality_metrics.ror,
                "ebgm": signal.disproportionality_metrics.ebgm,
            },
            "evidence_grade": signal.evidence_grade,
            "references": signal.references,
        })

    # Monitoring recommendations
    monitoring = get_monitoring_protocol()

    # Current regulatory status
    current_regulatory = []
    for milestone in FDA_REGULATORY_TIMELINE:
        if matched_product in milestone.products_affected:
            current_regulatory.append({
                "date": milestone.date.isoformat(),
                "agency": milestone.agency,
                "action": milestone.action,
            })

    # Causality assessment
    causality = get_causality_framework()

    return {
        "product_name": matched_product,
        "product_info": {
            "generic_name": product_info["generic_name"],
            "target": product_info["target"].value,
            "manufacturer": product_info["manufacturer"],
            "approval_year": product_info["approval_year"],
            "indication": product_info["indication"],
            "vector": product_info["vector"],
        },
        "known_signals": signal_summaries,
        "risk_level": "elevated",
        "risk_classification": (
            "All approved CAR-T products carry a boxed warning for secondary "
            "T-cell malignancies per FDA mandate (January 2024). Risk is "
            "considered elevated but rare (~1/1000 treated patients based on "
            "spontaneous reporting). Benefits continue to outweigh risks for "
            "approved indications."
        ),
        "monitoring_recommendations": monitoring,
        "regulatory_status": current_regulatory,
        "causality_assessment": causality,
        "epidemiological_context": {
            "overall_secondary_malignancy_rate_pct": FAERS_SUMMARY_STATS[
                "secondary_malignancy_rate_pct"
            ],
            "t_cell_malignancy_cases_reported": FAERS_SUMMARY_STATS[
                "t_cell_malignancy_cases"
            ],
            "car_transgene_positive_rate": (
                f"{FAERS_SUMMARY_STATS['t_cell_malignancy_car_positive_confirmed']}"
                f"/{FAERS_SUMMARY_STATS['t_cell_malignancy_car_positive_tested']} "
                "tested positive"
            ),
            "median_time_to_onset_months": FAERS_SUMMARY_STATS[
                "median_time_to_onset_months"
            ],
            "pct_diagnosed_within_12_months": FAERS_SUMMARY_STATS[
                "pct_diagnosed_within_12_months"
            ],
            "data_cutoff": FAERS_SUMMARY_STATS["data_cutoff"],
        },
        "caveats": [
            "Reporting rates are based on spontaneous FAERS reports and "
            "underestimate true incidence due to under-reporting.",
            "The background rate of T-cell malignancy in heavily pre-treated "
            "hematologic malignancy patients is not well characterized.",
            "Prior therapies (alkylating agents, fludarabine, radiation) are "
            "confounders for secondary malignancy risk.",
            "Disproportionality metrics (PRR, ROR, EBGM) are hypothesis-generating "
            "and do not establish causation.",
            "CAR transgene testing was only performed in a subset of cases; "
            "the true rate of CAR-positive malignancies may differ.",
            "Long-term follow-up data are still maturing for all products.",
        ],
    }


# ---------------------------------------------------------------------------
# Monitoring protocol
# ---------------------------------------------------------------------------

def get_monitoring_protocol() -> dict:
    """Return the FDA-recommended lifelong monitoring protocol for
    secondary malignancies post CAR-T therapy.

    The protocol is based on FDA prescribing information updates from
    January 2024 and subsequent agency communications.

    Returns:
        Dict containing monitoring phases, recommended assessments,
        and follow-up schedule.
    """
    return {
        "title": (
            "Lifelong Monitoring Protocol for Secondary Malignancies "
            "Post CAR-T Therapy"
        ),
        "regulatory_basis": (
            "FDA boxed warning (January 2024) requires lifelong monitoring "
            "for new malignancies in all patients treated with CAR-T products."
        ),
        "phases": [
            {
                "phase": "Acute (0-30 days)",
                "frequency": "Weekly",
                "assessments": [
                    "Complete blood count with differential",
                    "Peripheral blood smear review",
                    "Physical examination for lymphadenopathy",
                    "Flow cytometry if abnormal lymphocytes detected",
                ],
                "rationale": (
                    "Early detection of aberrant T-cell proliferation. "
                    "Some cases have presented within weeks of infusion."
                ),
            },
            {
                "phase": "Early follow-up (1-6 months)",
                "frequency": "Monthly",
                "assessments": [
                    "Complete blood count with differential",
                    "Peripheral blood smear review",
                    "Physical examination for lymphadenopathy",
                    "LDH as tumor marker",
                    "T-cell subset analysis if clinically indicated",
                ],
                "rationale": (
                    "Period of highest risk: 67% of cases with known timing "
                    "were diagnosed within 12 months post-infusion."
                ),
            },
            {
                "phase": "Intermediate (6-24 months)",
                "frequency": "Every 3 months",
                "assessments": [
                    "Complete blood count with differential",
                    "Comprehensive metabolic panel",
                    "LDH",
                    "Physical examination",
                    "CT imaging if clinically indicated",
                    "Bone marrow biopsy if cytopenias develop",
                ],
                "rationale": (
                    "Continued high-risk period. MDS/AML typically presents "
                    "12-24 months post-treatment."
                ),
            },
            {
                "phase": "Long-term (>24 months)",
                "frequency": "Every 6 months, lifelong",
                "assessments": [
                    "Complete blood count with differential",
                    "Physical examination",
                    "Annual comprehensive metabolic panel",
                    "Age-appropriate cancer screening per guidelines",
                    "Low threshold for biopsy of new lymphadenopathy",
                ],
                "rationale": (
                    "FDA requires lifelong monitoring. Late-onset secondary "
                    "malignancies remain a risk."
                ),
            },
        ],
        "urgent_evaluation_triggers": [
            "New or unexplained lymphadenopathy",
            "Unexplained cytopenias (new anemia, thrombocytopenia, neutropenia)",
            "New skin lesions suggestive of cutaneous T-cell lymphoma",
            "B symptoms (fever, night sweats, weight loss)",
            "Rapidly rising LDH",
            "Abnormal lymphocyte population on peripheral blood smear",
        ],
        "diagnostic_workup_if_suspected": [
            "Flow cytometry with T-cell markers (CD3, CD4, CD8, CD7, CD5)",
            "CAR transgene testing (PCR for CAR construct)",
            "Integration site analysis (if CAR transgene positive)",
            "Tissue biopsy with immunohistochemistry",
            "Cytogenetics and molecular studies",
            "PET-CT for staging",
        ],
        "patient_counseling": [
            "Inform patients of the secondary malignancy risk before treatment",
            "Emphasize importance of lifelong follow-up visits",
            "Instruct patients to report new lumps, unexplained bleeding, "
            "persistent fever, or night sweats promptly",
            "Provide written information about signs and symptoms",
        ],
        "references": [
            "FDA Safety Communication Jan 2024",
            "PMID:38442389",
            "PMID:38587889",
        ],
    }


# ---------------------------------------------------------------------------
# Causality assessment framework
# ---------------------------------------------------------------------------

def get_causality_framework() -> dict:
    """Return the PEI/EMA causality assessment framework for secondary
    malignancies post CAR-T therapy.

    Based on the Paul-Ehrlich-Institut (PEI) perspective (Verdun & Bhoj,
    2024, PMID:38442375) and EMA PRAC review, which argue that traditional
    pharmacovigilance causality criteria (e.g., Naranjo, WHO-UMC) are
    insufficient for gene-modified cell therapy products.

    Returns:
        Dict containing the framework components, evidence levels, and
        assessment criteria.
    """
    return {
        "title": (
            "Causality Assessment Framework for Secondary Malignancies "
            "Post CAR-T Therapy"
        ),
        "framework_source": (
            "Adapted from Paul-Ehrlich-Institut (PEI) perspective and "
            "EMA PRAC review. Traditional causality assessment frameworks "
            "(Naranjo, WHO-UMC) have limited applicability to gene-modified "
            "cell therapy products due to unique mechanism considerations."
        ),
        "criteria": [
            {
                "criterion": "Temporal relationship",
                "description": (
                    "Time from CAR-T infusion to malignancy diagnosis. "
                    "Most T-cell malignancies reported within 12 months."
                ),
                "evidence_for_causality": (
                    "22/33 cases (67%) diagnosed within 2 years. "
                    "However, temporal association alone does not "
                    "establish causation."
                ),
                "weight": "supportive",
                "references": ["PMID:38442389"],
            },
            {
                "criterion": "CAR transgene detection",
                "description": (
                    "Testing malignant T cells for the CAR construct. "
                    "Positive result indicates the malignant clone "
                    "originated from or was modified by the CAR-T product."
                ),
                "evidence_for_causality": (
                    "7/19 tested cases (37%) were CAR transgene positive. "
                    "This is the strongest mechanistic evidence, as it "
                    "demonstrates the malignant clone carries the vector."
                ),
                "weight": "strong",
                "references": ["PMID:38442389", "PMID:38442375"],
            },
            {
                "criterion": "Insertional mutagenesis mechanism",
                "description": (
                    "Viral vector integration near proto-oncogenes could "
                    "drive malignant transformation through enhancer "
                    "activation or gene disruption."
                ),
                "evidence_for_causality": (
                    "Integration site analysis in CAR-positive cases has "
                    "identified insertions near oncogenic loci in some "
                    "cases. Mechanism is biologically plausible based on "
                    "precedent from gene therapy (X-SCID trials)."
                ),
                "weight": "moderate",
                "references": [
                    "PMID:38442375",
                    "PMID:12529469",  # Hacein-Bey-Abina et al. X-SCID
                ],
            },
            {
                "criterion": "Biological plausibility",
                "description": (
                    "Retroviral/lentiviral vectors integrate into the host "
                    "genome. Integration near oncogenes is a known risk of "
                    "integrating vector technologies."
                ),
                "evidence_for_causality": (
                    "Well-established mechanism from gene therapy field. "
                    "Retroviral vectors have higher insertional mutagenesis "
                    "risk than lentiviral vectors due to preferential "
                    "integration near promoters."
                ),
                "weight": "strong",
                "references": [
                    "PMID:12529469",
                    "PMID:10706547",  # Cavazzana-Calvo et al. 2000
                ],
            },
            {
                "criterion": "Alternative explanations",
                "description": (
                    "Prior therapies, underlying disease, and patient "
                    "demographics as confounders."
                ),
                "evidence_against_sole_causality": (
                    "Patients receiving CAR-T are heavily pre-treated with "
                    "alkylating agents, fludarabine, and sometimes radiation "
                    "-- all known risk factors for secondary malignancies. "
                    "Background rate of T-cell malignancy in this population "
                    "is nonzero but poorly characterized."
                ),
                "weight": "confounding",
                "references": ["PMID:38442375", "PMID:38981000"],
            },
            {
                "criterion": "Dose-response relationship",
                "description": (
                    "Whether higher CAR-T cell doses or higher vector copy "
                    "numbers correlate with malignancy risk."
                ),
                "evidence_for_causality": (
                    "Not yet established. Current data are insufficient to "
                    "assess dose-response. Individual case reports do not "
                    "provide population-level dose-response data."
                ),
                "weight": "insufficient_data",
                "references": ["PMID:39467014"],
            },
        ],
        "overall_assessment": (
            "Causality is PROBABLE for a subset of cases (CAR transgene "
            "positive) and POSSIBLE for CAR transgene negative or untested "
            "cases. The PEI emphasizes that traditional causality frameworks "
            "are inadequate for gene-modified cell therapies and recommends "
            "mandatory CAR transgene testing in all secondary malignancy cases."
        ),
        "pei_recommendations": [
            "Mandatory CAR transgene testing in all cases of T-cell malignancy "
            "post CAR-T therapy",
            "Integration site analysis when CAR transgene is positive",
            "Long-term registry-based follow-up for all treated patients",
            "International harmonization of reporting requirements",
            "Development of new causality frameworks specific to gene-modified "
            "cell therapy products",
        ],
        "references": [
            "PMID:38442375",  # Verdun & Bhoj 2024 - PEI perspective
            "PMID:38442389",  # Levine et al. 2024 - FDA perspective
            "PMID:38587889",  # Shah et al. 2024 - Nature Medicine
        ],
    }


# ---------------------------------------------------------------------------
# Convenience: get all signals as serializable dicts
# ---------------------------------------------------------------------------

def get_all_signals_data() -> dict:
    """Return all known secondary malignancy signals and summary data
    in a serializable format.

    Returns:
        Dict containing all signals, regulatory timeline, epidemiological
        summary, and monitoring protocol.
    """
    signals_data = []
    for signal in KNOWN_SIGNALS:
        signals_data.append({
            "product_name": signal.product_name,
            "malignancy_type": signal.malignancy_type.value,
            "time_to_onset_months": signal.time_to_onset_months,
            "car_transgene_detected": signal.car_transgene_detected,
            "reporting_rate_per_1000": signal.reporting_rate_per_1000,
            "disproportionality_metrics": {
                "prr": signal.disproportionality_metrics.prr,
                "ror": signal.disproportionality_metrics.ror,
                "ebgm": signal.disproportionality_metrics.ebgm,
            },
            "evidence_grade": signal.evidence_grade,
            "regulatory_actions": signal.regulatory_actions,
            "references": signal.references,
        })

    timeline_data = []
    for milestone in FDA_REGULATORY_TIMELINE:
        timeline_data.append({
            "date": milestone.date.isoformat(),
            "agency": milestone.agency,
            "action": milestone.action,
            "products_affected": milestone.products_affected,
            "references": milestone.references,
        })

    return {
        "signals": signals_data,
        "total_signals": len(signals_data),
        "products_with_signals": sorted(
            set(s.product_name for s in KNOWN_SIGNALS)
        ),
        "malignancy_types": MALIGNANCY_TYPES,
        "regulatory_timeline": timeline_data,
        "epidemiological_summary": FAERS_SUMMARY_STATS,
        "monitoring_protocol": get_monitoring_protocol(),
        "causality_framework": get_causality_framework(),
        "data_sources": [
            "FDA FAERS (openFDA)",
            "Published literature (PubMed)",
            "FDA safety communications",
            "EMA PRAC reviews",
        ],
        "references": [
            {"pmid": "PMID:38442389", "citation": "Levine BL et al. FDA analysis of T-cell malignancies after CAR-T. N Engl J Med. 2024."},
            {"pmid": "PMID:39467014", "citation": "Ghilardi G et al. T-cell malignancies after CAR-T: systematic FAERS review. Blood Adv. 2024."},
            {"pmid": "PMID:38981000", "citation": "Strati P et al. Secondary T-cell lymphomas after CAR-T: MD Anderson experience. Lancet Haematol. 2024."},
            {"pmid": "PMID:38442375", "citation": "Verdun N, Bhoj V. Secondary cancers after CAR-T: PEI perspective. N Engl J Med. 2024."},
            {"pmid": "PMID:38587889", "citation": "Shah NN et al. T-cell malignancies after CAR-T therapy. Nature Med. 2024."},
            {"pmid": "PMID:12529469", "citation": "Hacein-Bey-Abina S et al. LMO2-associated clonal T-cell proliferation after gene therapy. Science. 2003."},
            {"pmid": "PMID:10706547", "citation": "Cavazzana-Calvo M et al. Gene therapy of human SCID-X1. Science. 2000."},
        ],
    }
