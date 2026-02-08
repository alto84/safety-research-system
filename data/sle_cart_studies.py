"""
Clinical study data for CAR-T safety in autoimmune indications.

Curated from published clinical trial literature and public registries (ClinicalTrials.gov).
Contains adverse event rates from SLE CAR-T trials and oncology comparators,
clinical trial metadata, and data source inventory for the safety research system.

All SLE trial data sourced from published studies 2022-2025. Oncology comparator
data from approved CAR-T product pivotal trials (ZUMA-1, JULIET, TRANSCEND,
ELIANA, KarMMa, CARTITUDE-1).

Usage:
    from data.sle_cart_studies import (
        ADVERSE_EVENT_RATES,
        CLINICAL_TRIALS,
        DATA_SOURCES,
        get_adverse_events_by_indication,
        get_sle_trials,
        get_comparison_chart_data,
        get_trial_summary,
        get_sle_baseline_risk,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class AdverseEventRate:
    """Adverse event rates by indication and product.

    Rates are expressed as percentages (0-100). Fields follow ASTCT consensus
    grading for CRS and ICANS, plus ICAHS and LICATS for autoimmune-specific
    toxicities.
    """
    indication: str         # "SLE", "DLBCL", "ALL", "MM"
    product: str
    trial: str
    n_patients: int
    crs_any_grade: float    # percentage
    crs_grade3_plus: float
    icans_any_grade: float
    icans_grade3_plus: float
    icahs_rate: float
    licats_rate: float = 0.0
    source: str = ""
    year: int = 2024
    n_events: int | None = None
    source_table: str = ""


@dataclass
class ClinicalTrial:
    """Clinical trial metadata for CAR-T studies in autoimmune and oncology indications."""
    name: str
    sponsor: str
    nct_id: str
    phase: str
    target: str         # CD19, BCMA, BCMA/CD19 dual
    indication: str
    enrollment: int
    status: str         # Recruiting, Active, Completed, Not yet recruiting


@dataclass
class DataSource:
    """Data source for CAR-T safety surveillance and signal detection."""
    name: str
    type: str           # Literature, RWD, Spontaneous Reporting, Registry
    coverage: str
    cart_data_available: bool
    autoimmune_cart_data: bool
    access_method: str
    strengths: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


# ============================================================================
# Adverse Event Rate Data
# ============================================================================

ADVERSE_EVENT_RATES: list[AdverseEventRate] = [
    # =========================================================================
    # SLE / Autoimmune CAR-T Trials
    # =========================================================================
    AdverseEventRate(
        indication="SLE",
        product="Anti-CD19 CAR-T (pooled)",
        trial="SLE Pooled Analysis",
        n_patients=47,
        crs_any_grade=56.0,
        crs_grade3_plus=2.1,
        icans_any_grade=3.0,
        icans_grade3_plus=1.5,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Pooled analysis of published SLE CAR-T studies 2022-2025",
        year=2025,
        n_events=1,
        source_table="Table 1 (pooled)",
    ),
    AdverseEventRate(
        indication="SLE",
        product="Anti-CD19 CAR-T (MB-CART19.1)",
        trial="Mackensen et al. 2022",
        n_patients=5,
        crs_any_grade=60.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Mackensen A et al. Nat Med 2022;28:2124-2132",
        year=2022,
        n_events=3,
        source_table="Table 2",
    ),
    AdverseEventRate(
        indication="SLE",
        product="Anti-CD19 CAR-T",
        trial="Muller et al. 2024",
        n_patients=15,
        crs_any_grade=53.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Muller F et al. N Engl J Med 2024;390:687-700",
        year=2024,
        n_events=8,
        source_table="Table 2",
    ),
    AdverseEventRate(
        indication="SLE",
        product="Anti-CD19 CAR-T (YTB323)",
        trial="CASTLE 2025",
        n_patients=8,
        crs_any_grade=50.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Novartis CASTLE trial interim results, ASH 2024",
        year=2025,
        n_events=4,
        source_table="Abstract",
    ),
    AdverseEventRate(
        indication="SLE",
        product="BCMA-CD19 cCAR",
        trial="BCMA-CD19 cCAR SLE",
        n_patients=7,
        crs_any_grade=57.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Jin X et al. BCMA/CD19 compound CAR-T in SLE, 2024",
        year=2024,
        n_events=4,
        source_table="Table 1",
    ),
    AdverseEventRate(
        indication="SLE",
        product="CD19/BCMA co-infusion",
        trial="Co-infusion SLE",
        n_patients=6,
        crs_any_grade=67.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Dual-target co-infusion approach in refractory SLE, 2024",
        year=2024,
        n_events=4,
        source_table="Table 1",
    ),
    AdverseEventRate(
        indication="SLE",
        product="CABA-201 (desar-cel)",
        trial="Cabaletta RESET-SLE",
        n_patients=4,
        crs_any_grade=50.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="Cabaletta Bio RESET-SLE Phase 1 interim, ACR 2024",
        year=2024,
        n_events=2,
        source_table="Abstract",
    ),
    AdverseEventRate(
        indication="SLE",
        product="Anti-CD19 CAR-T",
        trial="BMS Breakfree-1",
        n_patients=2,
        crs_any_grade=50.0,
        crs_grade3_plus=0.0,
        icans_any_grade=0.0,
        icans_grade3_plus=0.0,
        icahs_rate=0.0,
        licats_rate=0.0,
        source="BMS Breakfree-1 SLE cohort preliminary, 2025",
        year=2025,
        n_events=1,
        source_table="Abstract",
    ),

    # =========================================================================
    # Oncology Comparators - DLBCL
    # =========================================================================
    AdverseEventRate(
        indication="DLBCL",
        product="Axi-cel (Yescarta)",
        trial="ZUMA-1",
        n_patients=101,
        crs_any_grade=93.0,
        crs_grade3_plus=13.0,
        icans_any_grade=64.0,
        icans_grade3_plus=28.0,
        icahs_rate=0.0,
        source="Neelapu SS et al. N Engl J Med 2017;377:2531-2544 (ZUMA-1)",
        year=2017,
    ),
    AdverseEventRate(
        indication="DLBCL",
        product="Tisa-cel (Kymriah)",
        trial="JULIET",
        n_patients=111,
        crs_any_grade=58.0,
        crs_grade3_plus=14.0,
        icans_any_grade=21.0,
        icans_grade3_plus=12.0,
        icahs_rate=0.0,
        source="Schuster SJ et al. N Engl J Med 2019;380:45-56 (JULIET)",
        year=2019,
    ),
    AdverseEventRate(
        indication="DLBCL",
        product="Liso-cel (Breyanzi)",
        trial="TRANSCEND",
        n_patients=269,
        crs_any_grade=42.0,
        crs_grade3_plus=2.0,
        icans_any_grade=30.0,
        icans_grade3_plus=10.0,
        icahs_rate=0.0,
        source="Abramson JS et al. Lancet 2020;396:839-852 (TRANSCEND NHL 001)",
        year=2020,
    ),

    # =========================================================================
    # Oncology Comparators - ALL
    # =========================================================================
    AdverseEventRate(
        indication="ALL",
        product="Tisa-cel (Kymriah)",
        trial="ELIANA",
        n_patients=75,
        crs_any_grade=77.0,
        crs_grade3_plus=48.0,
        icans_any_grade=40.0,
        icans_grade3_plus=13.0,
        icahs_rate=0.0,
        source="Maude SL et al. N Engl J Med 2018;378:439-448 (ELIANA)",
        year=2018,
    ),

    # =========================================================================
    # Oncology Comparators - Multiple Myeloma
    # =========================================================================
    AdverseEventRate(
        indication="MM",
        product="Ide-cel (Abecma)",
        trial="KarMMa",
        n_patients=128,
        crs_any_grade=89.0,
        crs_grade3_plus=7.0,
        icans_any_grade=40.0,
        icans_grade3_plus=4.0,
        icahs_rate=0.0,
        source="Munshi NC et al. N Engl J Med 2021;384:705-716 (KarMMa)",
        year=2021,
    ),
    AdverseEventRate(
        indication="MM",
        product="Cilta-cel (Carvykti)",
        trial="CARTITUDE-1",
        n_patients=97,
        crs_any_grade=95.0,
        crs_grade3_plus=4.0,
        icans_any_grade=21.0,
        icans_grade3_plus=10.0,
        icahs_rate=0.0,
        source="Berdeja JG et al. Lancet 2021;398:314-324 (CARTITUDE-1)",
        year=2021,
    ),
]


# ============================================================================
# Clinical Trials Data
# ============================================================================

CLINICAL_TRIALS: list[ClinicalTrial] = [
    # =========================================================================
    # Autoimmune CAR-T Trials
    # =========================================================================
    ClinicalTrial(
        name="CASTLE",
        sponsor="Novartis",
        nct_id="NCT05765006",
        phase="Phase 1/2",
        target="CD19",
        indication="SLE",
        enrollment=48,
        status="Recruiting",
    ),
    ClinicalTrial(
        name="RESET-SLE",
        sponsor="Cabaletta Bio",
        nct_id="NCT05765864",
        phase="Phase 1",
        target="CD19",
        indication="SLE",
        enrollment=36,
        status="Recruiting",
    ),
    ClinicalTrial(
        name="RESET-Myositis",
        sponsor="Cabaletta Bio",
        nct_id="NCT06220045",
        phase="Phase 1",
        target="CD19",
        indication="Myositis",
        enrollment=24,
        status="Recruiting",
    ),
    ClinicalTrial(
        name="Breakfree-1",
        sponsor="Bristol Myers Squibb",
        nct_id="NCT06099756",
        phase="Phase 1",
        target="CD19",
        indication="SLE, SSc, Myositis",
        enrollment=60,
        status="Recruiting",
    ),
    ClinicalTrial(
        name="KYV-101 Autoimmune",
        sponsor="Kyverna Therapeutics",
        nct_id="NCT06277856",
        phase="Phase 2",
        target="CD19",
        indication="Lupus Nephritis",
        enrollment=40,
        status="Recruiting",
    ),
    ClinicalTrial(
        name="BCMA-CD19 cCAR SLE",
        sponsor="iCell Gene Therapeutics",
        nct_id="NCT05474495",
        phase="Phase 1",
        target="BCMA/CD19 dual",
        indication="SLE",
        enrollment=20,
        status="Active",
    ),
    ClinicalTrial(
        name="Erlangen Expanded Access",
        sponsor="University Hospital Erlangen",
        nct_id="NCT05858983",
        phase="Phase 1/2",
        target="CD19",
        indication="SLE, SSc, Myositis, NMOSD",
        enrollment=30,
        status="Active",
    ),
    ClinicalTrial(
        name="GC012F / AZD0120",
        sponsor="AstraZeneca/Gracell",
        nct_id="NCT06684042",
        phase="Phase 1",
        target="BCMA/CD19 dual",
        indication="SLE",
        enrollment=12,
        status="Recruiting",
    ),

    # =========================================================================
    # Oncology Comparator Trials
    # =========================================================================
    ClinicalTrial(
        name="ZUMA-1",
        sponsor="Kite/Gilead",
        nct_id="NCT02348216",
        phase="Phase 1/2",
        target="CD19",
        indication="DLBCL",
        enrollment=101,
        status="Completed",
    ),
    ClinicalTrial(
        name="JULIET",
        sponsor="Novartis",
        nct_id="NCT02445248",
        phase="Phase 2",
        target="CD19",
        indication="DLBCL",
        enrollment=167,
        status="Completed",
    ),
    ClinicalTrial(
        name="TRANSCEND NHL 001",
        sponsor="BMS/Juno",
        nct_id="NCT02631044",
        phase="Phase 1",
        target="CD19",
        indication="DLBCL",
        enrollment=269,
        status="Completed",
    ),
    ClinicalTrial(
        name="ELIANA",
        sponsor="Novartis",
        nct_id="NCT02435849",
        phase="Phase 2",
        target="CD19",
        indication="ALL",
        enrollment=75,
        status="Completed",
    ),
    ClinicalTrial(
        name="KarMMa",
        sponsor="BMS/Bluebird",
        nct_id="NCT03361748",
        phase="Phase 2",
        target="BCMA",
        indication="MM",
        enrollment=128,
        status="Completed",
    ),
    ClinicalTrial(
        name="CARTITUDE-1",
        sponsor="Janssen/Legend",
        nct_id="NCT03548207",
        phase="Phase 1b/2",
        target="BCMA",
        indication="MM",
        enrollment=97,
        status="Completed",
    ),
]


# ============================================================================
# Data Sources
# ============================================================================

DATA_SOURCES: list[DataSource] = [
    DataSource(
        name="Published Clinical Trial Literature",
        type="Literature",
        coverage=(
            "Peer-reviewed publications from SLE CAR-T trials (2022-2025) "
            "and approved oncology CAR-T pivotal trials"
        ),
        cart_data_available=True,
        autoimmune_cart_data=True,
        access_method="PubMed, journal databases, conference abstracts (ASH, ACR, EULAR)",
        strengths=[
            "Rigorous peer review process",
            "Standardized AE grading (CTCAE, ASTCT consensus)",
            "Detailed patient-level safety data in supplements",
            "Longitudinal follow-up data available for oncology products",
        ],
        limitations=[
            "Publication lag of 6-18 months from data cutoff",
            "Small sample sizes in autoimmune CAR-T trials (n=2-15)",
            "Heterogeneous reporting across trials and institutions",
            "Potential publication bias toward favorable outcomes",
        ],
    ),
    DataSource(
        name="FDA Adverse Event Reporting System (FAERS)",
        type="Spontaneous Reporting",
        coverage=(
            "Post-marketing spontaneous reports for approved CAR-T products "
            "(Kymriah, Yescarta, Breyanzi, Abecma, Carvykti, Tecvayli)"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method="FDA FAERS public dashboard, openFDA API, quarterly data extracts",
        strengths=[
            "Large post-marketing dataset capturing real-world use",
            "Captures rare events not seen in clinical trials",
            "Ongoing surveillance with quarterly updates",
            "Publicly accessible with structured data fields",
        ],
        limitations=[
            "Voluntary reporting leads to significant underreporting",
            "No autoimmune indication CAR-T data yet (no approved products)",
            "Lacks denominator data for incidence calculation",
            "Reporting quality varies; duplicate reports possible",
        ],
    ),
    DataSource(
        name="CIBMTR (Center for International Blood and Marrow Transplant Research)",
        type="Registry",
        coverage=(
            "Mandatory reporting of all commercial CAR-T infusions in the US "
            "as REMS requirement; ~15,000+ infusions tracked"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method=(
            "CIBMTR research database; requires data use agreement; "
            "annual summary reports published"
        ),
        strengths=[
            "Mandatory reporting for all US commercial CAR-T infusions",
            "Standardized data collection forms",
            "Long-term follow-up (15 years required by REMS)",
            "Largest real-world CAR-T safety database globally",
        ],
        limitations=[
            "Currently oncology indications only",
            "Reporting completeness decreases with longer follow-up",
            "Data access requires institutional DUA and IRB approval",
            "Variable data quality across reporting centers",
        ],
    ),
    DataSource(
        name="EudraVigilance",
        type="Spontaneous Reporting",
        coverage=(
            "EU pharmacovigilance database for all EMA-authorized products "
            "including CAR-T therapies"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method="EudraVigilance online portal (adrreports.eu), EMA access for signal detection",
        strengths=[
            "Covers entire EU/EEA population",
            "Structured MedDRA-coded adverse event data",
            "Signal detection algorithms run routinely by EMA",
            "Complementary to FAERS for global safety picture",
        ],
        limitations=[
            "No autoimmune CAR-T products approved in EU yet",
            "Voluntary reporting with known underreporting",
            "Less granular than clinical trial data",
            "Access to line-level data restricted to regulatory authorities",
        ],
    ),
    DataSource(
        name="Investigator-Sponsored Trial Databases",
        type="RWD",
        coverage=(
            "Individual center databases from Erlangen, Beijing, Shanghai, "
            "Charite tracking autoimmune CAR-T patients"
        ),
        cart_data_available=True,
        autoimmune_cart_data=True,
        access_method="Collaborative agreements; published in aggregate in conference abstracts and papers",
        strengths=[
            "Primary source of autoimmune CAR-T safety data",
            "Detailed patient-level data including biomarkers",
            "Captures nuanced clinical context",
            "Earliest available data on novel safety signals",
        ],
        limitations=[
            "Small cohorts (typically n=5-20 per center)",
            "Non-standardized data collection across sites",
            "Access restricted to collaborating investigators",
            "Selection bias in academic referral populations",
        ],
    ),
    DataSource(
        name="WHO VigiBase",
        type="Spontaneous Reporting",
        coverage=(
            "Global ICSR database maintained by the Uppsala Monitoring Centre; "
            "aggregates reports from 170+ countries"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method=(
            "VigiAccess (public portal) for aggregate queries; "
            "VigiLyze for detailed analysis (requires UMC access)"
        ),
        strengths=[
            "Broadest global coverage of any pharmacovigilance database",
            "Useful for rare signal detection across populations",
            "Standardized MedDRA coding",
            "Complements regional databases (FAERS, EudraVigilance)",
        ],
        limitations=[
            "Highest level of data aggregation; least granular",
            "Duplicate reports across contributing national databases",
            "No autoimmune CAR-T data currently available",
            "Variable data quality across contributing countries",
        ],
    ),
    DataSource(
        name="TriNetX",
        type="RWD",
        coverage=(
            "Federated EHR network covering 150M+ patients across "
            "120+ healthcare organizations globally"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method=(
            "TriNetX platform (requires institutional license); "
            "federated queries without data movement"
        ),
        strengths=[
            "Large-scale real-world data across diverse populations",
            "Near real-time data updates",
            "Federated model preserves patient privacy",
            "Good for epidemiological background rate estimation",
        ],
        limitations=[
            "No autoimmune CAR-T patients yet (pre-approval)",
            "CAR-T coding inconsistencies across institutions",
            "Limited to structured EHR data; lacks clinical detail",
            "May miss events documented in unstructured notes",
        ],
    ),
    DataSource(
        name="Optum CDM",
        type="RWD",
        coverage=(
            "Claims and EHR data covering 67M+ US patients; "
            "integrated medical and pharmacy claims"
        ),
        cart_data_available=True,
        autoimmune_cart_data=False,
        access_method="Optum data licensing; requires DUA and IRB approval",
        strengths=[
            "Longitudinal patient-level data with integrated claims",
            "Good for comorbidity and comedication analysis",
            "Large denominator for rate comparisons",
            "Captures post-discharge outcomes",
        ],
        limitations=[
            "US-only population",
            "No autoimmune CAR-T patients (pre-approval)",
            "Claims-based AE identification has limited sensitivity",
            "Commercial/Medicare populations may not match trial demographics",
        ],
    ),
]


# ============================================================================
# Utility Functions
# ============================================================================

def get_adverse_events_by_indication(indication: str) -> list[AdverseEventRate]:
    """Filter adverse event rates by indication.

    Args:
        indication: Target indication string (e.g. "SLE", "DLBCL", "ALL", "MM").

    Returns:
        List of AdverseEventRate entries matching the indication.
    """
    return [ae for ae in ADVERSE_EVENT_RATES if ae.indication == indication]


def get_sle_trials() -> list[AdverseEventRate]:
    """Get individual SLE CAR-T trial data, excluding the pooled analysis.

    Returns:
        List of AdverseEventRate entries for individual SLE trials only.
    """
    return [
        ae for ae in ADVERSE_EVENT_RATES
        if ae.indication == "SLE" and ae.trial != "SLE Pooled Analysis"
    ]


def get_comparison_chart_data() -> list[dict]:
    """Get primary entries for cross-indication comparison charts.

    Returns one data point per primary trial for visualization: the pooled SLE
    analysis plus each oncology pivotal trial.

    Returns:
        List of dicts with keys: label, indication, product, crs_any_grade,
        crs_grade3_plus, icans_any_grade, icans_grade3_plus, n_patients, category.
    """
    primary_trials = [
        "SLE Pooled Analysis",
        "ZUMA-1",
        "JULIET",
        "TRANSCEND",
        "ELIANA",
        "KarMMa",
        "CARTITUDE-1",
    ]

    results: list[dict] = []
    for ae in ADVERSE_EVENT_RATES:
        if ae.trial not in primary_trials:
            continue

        if ae.indication == "SLE":
            label = "SLE (Pooled)"
        else:
            product_short = ae.product.split(" ")[0]
            label = f"{product_short} ({ae.indication})"

        results.append({
            "label": label,
            "indication": ae.indication,
            "product": ae.product,
            "crs_any_grade": ae.crs_any_grade,
            "crs_grade3_plus": ae.crs_grade3_plus,
            "icans_any_grade": ae.icans_any_grade,
            "icans_grade3_plus": ae.icans_grade3_plus,
            "n_patients": ae.n_patients,
            "category": "Autoimmune" if ae.indication == "SLE" else "Oncology",
        })

    return results


def get_trial_summary() -> dict:
    """Get counts of clinical trials by status.

    Returns:
        Dict with keys: recruiting, active, completed, not_yet_recruiting, total.
    """
    recruiting = sum(1 for t in CLINICAL_TRIALS if t.status == "Recruiting")
    active = sum(1 for t in CLINICAL_TRIALS if t.status == "Active")
    completed = sum(1 for t in CLINICAL_TRIALS if t.status == "Completed")
    not_yet_recruiting = sum(
        1 for t in CLINICAL_TRIALS if t.status == "Not yet recruiting"
    )

    return {
        "recruiting": recruiting,
        "active": active,
        "completed": completed,
        "not_yet_recruiting": not_yet_recruiting,
        "total": len(CLINICAL_TRIALS),
    }


def get_sle_baseline_risk() -> dict:
    """Get the baseline risk estimates for SLE CAR-T with 95% confidence intervals.

    Derived from the pooled SLE analysis (n=47). Wide CIs reflect the small
    sample size. Upper bounds for zero-event rates use the rule of 3
    (3/n for 95% CI upper bound when 0 events observed).

    Returns:
        Dict with risk estimate entries, each containing 'estimate' (percentage)
        and 'ci95' (two-element list with lower and upper bounds).
    """
    return {
        "crs_any": {
            "estimate": 56.0,
            "ci95": [40.9, 70.4],  # Any-grade CRS from pooled SLE (n=47)
        },
        "crs_grade3_plus": {
            "estimate": 2.1,
            "ci95": [0.3, 7.4],
        },
        "icans_any": {
            "estimate": 3.0,
            "ci95": [0.4, 10.5],  # Any-grade ICANS from pooled SLE (n=47)
        },
        "icans_grade3_plus": {
            "estimate": 0.0,
            "ci95": [0.0, 6.4],  # 0/47 events; upper bound from rule-of-3: 3/47 = 6.4%
        },
        "icahs": {
            "estimate": 0.0,
            "ci95": [0.0, 6.4],  # upper bound from rule-of-3: 3/47 = 6.4%
        },
        "licats": {
            "estimate": 0.0,
            "ci95": [0.0, 6.4],  # Grade 3+ LICATS; any-grade ~77% (Hagen 2025)
        },
        "infection": {
            "estimate": 12.8,
            "ci95": [4.8, 25.7],  # Infections within 90 days from pooled SLE (n=47)
        },
        "cytopenias": {
            "estimate": 29.8,
            "ci95": [17.3, 44.9],  # Prolonged cytopenias (>14 days) from pooled SLE (n=47)
        },
    }
