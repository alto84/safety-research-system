"""
Trial configuration constants for 6 landmark CAR-T clinical trials.

All rates, demographics, and clinical parameters are derived from
published pivotal trial data.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class LymphodepletionRegimen:
    """Lymphodepletion chemotherapy regimen."""
    fludarabine_dose_mg_m2: float
    fludarabine_days: int
    cyclophosphamide_dose_mg_m2: float
    cyclophosphamide_days: int
    description: str


STANDARD_FLU_CY = LymphodepletionRegimen(
    fludarabine_dose_mg_m2=30.0,
    fludarabine_days=3,
    cyclophosphamide_dose_mg_m2=500.0,
    cyclophosphamide_days=3,
    description="Flu 30mg/m2 x3d + Cy 500mg/m2 x3d",
)

REDUCED_FLU_CY = LymphodepletionRegimen(
    fludarabine_dose_mg_m2=25.0,
    fludarabine_days=3,
    cyclophosphamide_dose_mg_m2=250.0,
    cyclophosphamide_days=3,
    description="Flu 25mg/m2 x3d + Cy 250mg/m2 x3d",
)

KARMMA_FLU_CY = LymphodepletionRegimen(
    fludarabine_dose_mg_m2=30.0,
    fludarabine_days=3,
    cyclophosphamide_dose_mg_m2=300.0,
    cyclophosphamide_days=3,
    description="Flu 30mg/m2 x3d + Cy 300mg/m2 x3d",
)


@dataclass(frozen=True)
class CARTProduct:
    """CAR-T cell product characteristics."""
    name: str
    trade_name: str
    target: str
    costimulatory_domain: str
    manufacturer: str
    # Dose in cells (typical range)
    dose_min: float
    dose_max: float
    dose_unit: str
    # Typical CD4:CD8 ratio range
    cd4_cd8_ratio_mean: float
    cd4_cd8_ratio_std: float


@dataclass(frozen=True)
class TrialConfig:
    """Complete configuration for a single clinical trial cohort."""
    trial_name: str
    product: CARTProduct
    lymphodepletion: LymphodepletionRegimen

    # Cohort size
    n_patients: int

    # Disease
    disease_type: str
    disease_subtype: str

    # Demographics
    median_age: float
    age_std: float
    age_min: int
    age_max: int
    male_fraction: float

    # CRS rates
    crs_any_rate: float
    crs_grade3plus_rate: float
    crs_median_onset_day: float
    crs_onset_std: float

    # ICANS rates
    icans_any_rate: float
    icans_grade3plus_rate: float

    # IEC-HS / HLH rate (subset of severe CRS)
    iec_hs_rate: float

    # Disease-specific baseline parameters
    # SPD (sum of product of diameters) in cm^2
    spd_mean: float
    spd_std: float
    # Prior lines of therapy
    prior_lines_mean: float
    prior_lines_std: float

    # Baseline lab ranges (mean, std) -- disease-specific adjustments
    baseline_ldh_mean: float
    baseline_ldh_std: float
    baseline_ferritin_mean: float
    baseline_ferritin_std: float
    baseline_crp_mean: float
    baseline_crp_std: float

    # Weight (kg)
    weight_mean: float
    weight_std: float

    # Comorbidity rates
    comorbidity_cardiovascular_rate: float
    comorbidity_pulmonary_rate: float
    comorbidity_renal_rate: float
    comorbidity_hepatic_rate: float

    # Random seed for reproducibility
    seed: int


# ---------------------------------------------------------------------------
# Product definitions
# ---------------------------------------------------------------------------

AXI_CEL = CARTProduct(
    name="axicabtagene ciloleucel",
    trade_name="Yescarta",
    target="CD19",
    costimulatory_domain="CD28",
    manufacturer="Kite/Gilead",
    dose_min=1e6,
    dose_max=2e6,
    dose_unit="cells/kg",
    cd4_cd8_ratio_mean=1.0,
    cd4_cd8_ratio_std=0.5,
)

TISA_CEL = CARTProduct(
    name="tisagenlecleucel",
    trade_name="Kymriah",
    target="CD19",
    costimulatory_domain="4-1BB",
    manufacturer="Novartis",
    dose_min=0.6e8,
    dose_max=6.0e8,
    dose_unit="total_cells",
    cd4_cd8_ratio_mean=1.2,
    cd4_cd8_ratio_std=0.6,
)

IDE_CEL = CARTProduct(
    name="idecabtagene vicleucel",
    trade_name="Abecma",
    target="BCMA",
    costimulatory_domain="4-1BB",
    manufacturer="BMS/bluebird",
    dose_min=150e6,
    dose_max=450e6,
    dose_unit="total_cells",
    cd4_cd8_ratio_mean=1.1,
    cd4_cd8_ratio_std=0.5,
)

CILTA_CEL = CARTProduct(
    name="ciltacabtagene autoleucel",
    trade_name="Carvykti",
    target="BCMA",
    costimulatory_domain="4-1BB",
    manufacturer="J&J/Legend",
    dose_min=0.5e6,
    dose_max=1.0e6,
    dose_unit="cells/kg",
    cd4_cd8_ratio_mean=1.0,
    cd4_cd8_ratio_std=0.4,
)

LISO_CEL = CARTProduct(
    name="lisocabtagene maraleucel",
    trade_name="Breyanzi",
    target="CD19",
    costimulatory_domain="4-1BB",
    manufacturer="BMS/Juno",
    dose_min=50e6,
    dose_max=110e6,
    dose_unit="total_cells",
    cd4_cd8_ratio_mean=1.0,
    cd4_cd8_ratio_std=0.1,  # defined composition
)


# ---------------------------------------------------------------------------
# Trial configurations
# ---------------------------------------------------------------------------

ZUMA1 = TrialConfig(
    trial_name="ZUMA-1",
    product=AXI_CEL,
    lymphodepletion=STANDARD_FLU_CY,
    n_patients=101,
    disease_type="NHL",
    disease_subtype="DLBCL",
    median_age=58.0,
    age_std=11.0,
    age_min=23,
    age_max=76,
    male_fraction=0.68,
    crs_any_rate=0.93,
    crs_grade3plus_rate=0.13,
    crs_median_onset_day=2.0,
    crs_onset_std=1.5,
    icans_any_rate=0.64,
    icans_grade3plus_rate=0.28,
    iec_hs_rate=0.03,
    spd_mean=38.0,
    spd_std=25.0,
    prior_lines_mean=3.0,
    prior_lines_std=1.0,
    baseline_ldh_mean=350.0,
    baseline_ldh_std=180.0,
    baseline_ferritin_mean=600.0,
    baseline_ferritin_std=400.0,
    baseline_crp_mean=15.0,
    baseline_crp_std=20.0,
    weight_mean=85.0,
    weight_std=18.0,
    comorbidity_cardiovascular_rate=0.25,
    comorbidity_pulmonary_rate=0.10,
    comorbidity_renal_rate=0.08,
    comorbidity_hepatic_rate=0.05,
    seed=42001,
)

JULIET = TrialConfig(
    trial_name="JULIET",
    product=TISA_CEL,
    lymphodepletion=STANDARD_FLU_CY,
    n_patients=93,
    disease_type="NHL",
    disease_subtype="DLBCL",
    median_age=56.0,
    age_std=12.0,
    age_min=22,
    age_max=76,
    male_fraction=0.59,
    crs_any_rate=0.58,
    crs_grade3plus_rate=0.22,
    crs_median_onset_day=3.0,
    crs_onset_std=2.0,
    icans_any_rate=0.21,
    icans_grade3plus_rate=0.12,
    iec_hs_rate=0.04,
    spd_mean=35.0,
    spd_std=22.0,
    prior_lines_mean=3.0,
    prior_lines_std=1.0,
    baseline_ldh_mean=320.0,
    baseline_ldh_std=160.0,
    baseline_ferritin_mean=550.0,
    baseline_ferritin_std=380.0,
    baseline_crp_mean=12.0,
    baseline_crp_std=18.0,
    weight_mean=80.0,
    weight_std=17.0,
    comorbidity_cardiovascular_rate=0.22,
    comorbidity_pulmonary_rate=0.09,
    comorbidity_renal_rate=0.07,
    comorbidity_hepatic_rate=0.06,
    seed=42002,
)

ELARA = TrialConfig(
    trial_name="ELARA",
    product=TISA_CEL,
    lymphodepletion=STANDARD_FLU_CY,
    n_patients=97,
    disease_type="NHL",
    disease_subtype="FL",
    median_age=57.0,
    age_std=10.0,
    age_min=28,
    age_max=75,
    male_fraction=0.47,
    crs_any_rate=0.49,
    crs_grade3plus_rate=0.00,
    crs_median_onset_day=5.0,
    crs_onset_std=2.5,
    icans_any_rate=0.10,
    icans_grade3plus_rate=0.01,
    iec_hs_rate=0.00,
    spd_mean=25.0,
    spd_std=15.0,
    prior_lines_mean=4.0,
    prior_lines_std=1.0,
    baseline_ldh_mean=250.0,
    baseline_ldh_std=100.0,
    baseline_ferritin_mean=350.0,
    baseline_ferritin_std=250.0,
    baseline_crp_mean=8.0,
    baseline_crp_std=10.0,
    weight_mean=75.0,
    weight_std=16.0,
    comorbidity_cardiovascular_rate=0.20,
    comorbidity_pulmonary_rate=0.08,
    comorbidity_renal_rate=0.06,
    comorbidity_hepatic_rate=0.04,
    seed=42003,
)

KARMMA = TrialConfig(
    trial_name="KarMMa",
    product=IDE_CEL,
    lymphodepletion=KARMMA_FLU_CY,
    n_patients=128,
    disease_type="MM",
    disease_subtype="Multiple Myeloma",
    median_age=61.0,
    age_std=9.0,
    age_min=33,
    age_max=78,
    male_fraction=0.59,
    crs_any_rate=0.84,
    crs_grade3plus_rate=0.05,
    crs_median_onset_day=1.0,
    crs_onset_std=1.0,
    icans_any_rate=0.18,
    icans_grade3plus_rate=0.03,
    iec_hs_rate=0.02,
    spd_mean=0.0,  # Not applicable for MM; use paraprotein burden instead
    spd_std=0.0,
    prior_lines_mean=6.0,
    prior_lines_std=2.0,
    baseline_ldh_mean=280.0,
    baseline_ldh_std=120.0,
    baseline_ferritin_mean=500.0,
    baseline_ferritin_std=350.0,
    baseline_crp_mean=10.0,
    baseline_crp_std=15.0,
    weight_mean=82.0,
    weight_std=17.0,
    comorbidity_cardiovascular_rate=0.30,
    comorbidity_pulmonary_rate=0.12,
    comorbidity_renal_rate=0.15,
    comorbidity_hepatic_rate=0.05,
    seed=42004,
)

CARTITUDE1 = TrialConfig(
    trial_name="CARTITUDE-1",
    product=CILTA_CEL,
    lymphodepletion=STANDARD_FLU_CY,
    n_patients=97,
    disease_type="MM",
    disease_subtype="Multiple Myeloma",
    median_age=61.0,
    age_std=9.0,
    age_min=29,
    age_max=78,
    male_fraction=0.58,
    crs_any_rate=0.95,
    crs_grade3plus_rate=0.04,
    crs_median_onset_day=7.0,
    crs_onset_std=3.0,
    icans_any_rate=0.17,
    icans_grade3plus_rate=0.02,
    iec_hs_rate=0.01,
    spd_mean=0.0,
    spd_std=0.0,
    prior_lines_mean=6.0,
    prior_lines_std=2.0,
    baseline_ldh_mean=290.0,
    baseline_ldh_std=130.0,
    baseline_ferritin_mean=520.0,
    baseline_ferritin_std=360.0,
    baseline_crp_mean=11.0,
    baseline_crp_std=16.0,
    weight_mean=80.0,
    weight_std=17.0,
    comorbidity_cardiovascular_rate=0.28,
    comorbidity_pulmonary_rate=0.11,
    comorbidity_renal_rate=0.14,
    comorbidity_hepatic_rate=0.06,
    seed=42005,
)

TRANSCEND = TrialConfig(
    trial_name="TRANSCEND",
    product=LISO_CEL,
    lymphodepletion=STANDARD_FLU_CY,
    n_patients=269,
    disease_type="NHL",
    disease_subtype="DLBCL",
    median_age=63.0,
    age_std=10.0,
    age_min=18,
    age_max=86,
    male_fraction=0.66,
    crs_any_rate=0.42,
    crs_grade3plus_rate=0.02,
    crs_median_onset_day=5.0,
    crs_onset_std=2.5,
    icans_any_rate=0.30,
    icans_grade3plus_rate=0.10,
    iec_hs_rate=0.01,
    spd_mean=32.0,
    spd_std=20.0,
    prior_lines_mean=3.0,
    prior_lines_std=1.0,
    baseline_ldh_mean=310.0,
    baseline_ldh_std=150.0,
    baseline_ferritin_mean=480.0,
    baseline_ferritin_std=340.0,
    baseline_crp_mean=10.0,
    baseline_crp_std=14.0,
    weight_mean=83.0,
    weight_std=18.0,
    comorbidity_cardiovascular_rate=0.30,
    comorbidity_pulmonary_rate=0.12,
    comorbidity_renal_rate=0.10,
    comorbidity_hepatic_rate=0.06,
    seed=42006,
)


ALL_TRIALS: Dict[str, TrialConfig] = {
    "ZUMA-1": ZUMA1,
    "JULIET": JULIET,
    "ELARA": ELARA,
    "KarMMa": KARMMA,
    "CARTITUDE-1": CARTITUDE1,
    "TRANSCEND": TRANSCEND,
}

# Total patients across all trials
TOTAL_PATIENTS = sum(t.n_patients for t in ALL_TRIALS.values())
assert TOTAL_PATIENTS == 785, f"Expected 785 total patients, got {TOTAL_PATIENTS}"


# ---------------------------------------------------------------------------
# Normal physiological ranges (for reference / validation)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LabRange:
    """Normal reference range for a lab value."""
    name: str
    unit: str
    low: float
    high: float


NORMAL_RANGES: Dict[str, LabRange] = {
    "WBC": LabRange("White Blood Cells", "x10^9/L", 4.5, 11.0),
    "ANC": LabRange("Absolute Neutrophil Count", "x10^9/L", 1.5, 8.0),
    "ALC": LabRange("Absolute Lymphocyte Count", "x10^9/L", 1.0, 4.0),
    "Hemoglobin": LabRange("Hemoglobin", "g/dL", 12.0, 17.5),
    "Platelets": LabRange("Platelets", "x10^9/L", 150.0, 400.0),
    "Creatinine": LabRange("Creatinine", "mg/dL", 0.6, 1.2),
    "BUN": LabRange("Blood Urea Nitrogen", "mg/dL", 7.0, 20.0),
    "AST": LabRange("Aspartate Aminotransferase", "U/L", 10.0, 40.0),
    "ALT": LabRange("Alanine Aminotransferase", "U/L", 7.0, 56.0),
    "LDH": LabRange("Lactate Dehydrogenase", "U/L", 140.0, 280.0),
    "Albumin": LabRange("Albumin", "g/dL", 3.5, 5.5),
    "CRP": LabRange("C-Reactive Protein", "mg/L", 0.0, 10.0),
    "Ferritin": LabRange("Ferritin", "ng/mL", 12.0, 300.0),
    "Fibrinogen": LabRange("Fibrinogen", "mg/dL", 200.0, 400.0),
    "D_dimer": LabRange("D-dimer", "mg/L FEU", 0.0, 0.5),
    "IL6": LabRange("Interleukin-6", "pg/mL", 0.0, 7.0),
    "IFN_gamma": LabRange("Interferon-gamma", "pg/mL", 0.0, 15.0),
    "TNF_alpha": LabRange("TNF-alpha", "pg/mL", 0.0, 8.1),
    "IL10": LabRange("Interleukin-10", "pg/mL", 0.0, 5.0),
    "MCP1": LabRange("MCP-1", "pg/mL", 0.0, 300.0),
    "IL1RA": LabRange("IL-1RA", "pg/mL", 0.0, 500.0),
    "sgp130": LabRange("Soluble gp130", "ng/mL", 200.0, 400.0),
    "Temperature": LabRange("Temperature", "C", 36.1, 37.2),
    "HR": LabRange("Heart Rate", "bpm", 60.0, 100.0),
    "BP_sys": LabRange("Systolic Blood Pressure", "mmHg", 90.0, 140.0),
    "BP_dia": LabRange("Diastolic Blood Pressure", "mmHg", 60.0, 90.0),
    "RR": LabRange("Respiratory Rate", "breaths/min", 12.0, 20.0),
    "SpO2": LabRange("Oxygen Saturation", "%", 95.0, 100.0),
    "Triglycerides": LabRange("Triglycerides", "mg/dL", 40.0, 150.0),
}
