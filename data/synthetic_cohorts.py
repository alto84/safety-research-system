"""
Synthetic patient cohort generator for CAR-T cell therapy safety prediction.

Generates realistic time-series patient data matching 6 published landmark
CAR-T trials (ZUMA-1, JULIET, ELARA, KarMMa, CARTITUDE-1, TRANSCEND).

Each patient has:
  - Baseline demographics, labs, vitals, comorbidities
  - Time-series vitals (q4-6h), labs (daily), cytokines (q12h) Day 0-28
  - Known CRS/ICANS/IEC-HS outcomes with biologically realistic trajectories

Biological relationships encoded:
  - Higher tumor burden / LDH -> higher CRS risk
  - CD28 costimulatory -> earlier, more intense CRS
  - 4-1BB costimulatory -> later onset, lower peak CRS
  - IL-6 rises 12-24h before clinical CRS symptoms
  - Severe CRS: ferritin >5000, CRP >100, fibrinogen drops
  - ICANS follows CRS with 24-48h delay
  - IEC-HS: ferritin >10000, fibrinogen <150, triglycerides >265

Usage:
    from data.synthetic_cohorts import generate_all_cohorts
    cohorts, mega = generate_all_cohorts()
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from data.trial_configs import (
    ALL_TRIALS,
    TrialConfig,
    NORMAL_RANGES,
)


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class Comorbidities:
    cardiovascular: bool = False
    pulmonary: bool = False
    renal: bool = False
    hepatic: bool = False


@dataclass
class BaselineLabs:
    """Baseline laboratory values (Day -7)."""
    # CBC
    WBC: float = 0.0          # x10^9/L
    ANC: float = 0.0          # x10^9/L
    ALC: float = 0.0          # x10^9/L
    Hemoglobin: float = 0.0   # g/dL
    Platelets: float = 0.0    # x10^9/L
    # CMP
    Creatinine: float = 0.0   # mg/dL
    BUN: float = 0.0          # mg/dL
    AST: float = 0.0          # U/L
    ALT: float = 0.0          # U/L
    LDH: float = 0.0          # U/L
    Albumin: float = 0.0      # g/dL
    # Inflammatory
    CRP: float = 0.0          # mg/L
    Ferritin: float = 0.0     # ng/mL
    Fibrinogen: float = 0.0   # mg/dL
    D_dimer: float = 0.0      # mg/L FEU


@dataclass
class CARTDose:
    """CAR-T product dosing details."""
    product_name: str = ""
    trade_name: str = ""
    target: str = ""
    costimulatory_domain: str = ""
    dose_value: float = 0.0
    dose_unit: str = ""
    cd4_cd8_ratio: float = 1.0
    viability_pct: float = 95.0


@dataclass
class VitalSigns:
    """Single vital signs measurement."""
    time_hours: float = 0.0   # hours since Day 0 infusion
    Temperature: float = 37.0  # Celsius
    HR: float = 75.0          # bpm
    BP_sys: float = 120.0     # mmHg
    BP_dia: float = 75.0      # mmHg
    RR: float = 16.0          # breaths/min
    SpO2: float = 98.0        # %


@dataclass
class LabPanel:
    """Single daily laboratory panel."""
    time_hours: float = 0.0
    # CBC
    WBC: Optional[float] = None
    ANC: Optional[float] = None
    ALC: Optional[float] = None
    Hemoglobin: Optional[float] = None
    Platelets: Optional[float] = None
    # CMP
    Creatinine: Optional[float] = None
    BUN: Optional[float] = None
    AST: Optional[float] = None
    ALT: Optional[float] = None
    LDH: Optional[float] = None
    Albumin: Optional[float] = None
    # Inflammatory
    CRP: Optional[float] = None
    Ferritin: Optional[float] = None
    Fibrinogen: Optional[float] = None
    D_dimer: Optional[float] = None
    # Additional
    Triglycerides: Optional[float] = None


@dataclass
class CytokinePanel:
    """Single cytokine panel measurement (q12h)."""
    time_hours: float = 0.0
    IL6: Optional[float] = None          # pg/mL
    IFN_gamma: Optional[float] = None    # pg/mL
    TNF_alpha: Optional[float] = None    # pg/mL
    IL10: Optional[float] = None         # pg/mL
    MCP1: Optional[float] = None         # pg/mL
    IL1RA: Optional[float] = None        # pg/mL
    sgp130: Optional[float] = None       # ng/mL


@dataclass
class CRSOutcome:
    """CRS event details."""
    occurred: bool = False
    max_grade: int = 0          # ASTCT 0-4
    onset_day: float = 0.0      # fractional day
    peak_day: float = 0.0
    resolution_day: float = 0.0
    required_tocilizumab: bool = False
    required_steroids: bool = False
    required_vasopressors: bool = False


@dataclass
class ICANSOutcome:
    """ICANS event details."""
    occurred: bool = False
    max_grade: int = 0          # 0-4
    onset_day: float = 0.0
    peak_day: float = 0.0
    resolution_day: float = 0.0
    ice_score_nadir: int = 10   # 0-10, lower = worse


@dataclass
class IECHSOutcome:
    """IEC-HS (HLH-like) event details."""
    occurred: bool = False
    onset_day: float = 0.0
    peak_ferritin: float = 0.0
    nadir_fibrinogen: float = 0.0
    peak_triglycerides: float = 0.0


@dataclass
class PatientRecord:
    """Complete synthetic patient record."""
    # Identifiers
    patient_id: str = ""
    trial_name: str = ""
    cohort_index: int = 0

    # Demographics
    age: int = 0
    sex: str = "M"
    weight_kg: float = 0.0
    height_cm: float = 0.0
    bsa_m2: float = 0.0

    # Disease
    disease_type: str = ""
    disease_subtype: str = ""
    disease_stage: str = ""
    tumor_burden_spd: float = 0.0  # cm^2, 0 for MM
    paraprotein_burden: float = 0.0  # g/dL for MM, 0 for NHL
    prior_lines: int = 0

    # Comorbidities
    comorbidities: Comorbidities = field(default_factory=Comorbidities)

    # Treatment
    lymphodepletion: str = ""
    cart_dose: CARTDose = field(default_factory=CARTDose)

    # Baseline labs (Day -7)
    baseline_labs: BaselineLabs = field(default_factory=BaselineLabs)

    # Time-series data
    vitals_timeseries: List[VitalSigns] = field(default_factory=list)
    labs_timeseries: List[LabPanel] = field(default_factory=list)
    cytokine_timeseries: List[CytokinePanel] = field(default_factory=list)

    # ICE scores (for ICANS tracking, daily Day 0-28)
    ice_scores: List[Tuple[float, int]] = field(default_factory=list)

    # Outcomes
    crs: CRSOutcome = field(default_factory=CRSOutcome)
    icans: ICANSOutcome = field(default_factory=ICANSOutcome)
    iec_hs: IECHSOutcome = field(default_factory=IECHSOutcome)

    # Flags
    has_missing_data: bool = False
    is_edge_case: bool = False
    edge_case_type: str = ""


@dataclass
class CohortData:
    """A complete cohort of patients from one trial."""
    trial_name: str
    config: TrialConfig
    patients: List[PatientRecord]

    @property
    def n_patients(self) -> int:
        return len(self.patients)

    def crs_any_count(self) -> int:
        return sum(1 for p in self.patients if p.crs.occurred)

    def crs_grade3plus_count(self) -> int:
        return sum(1 for p in self.patients if p.crs.max_grade >= 3)

    def icans_any_count(self) -> int:
        return sum(1 for p in self.patients if p.icans.occurred)

    def icans_grade3plus_count(self) -> int:
        return sum(1 for p in self.patients if p.icans.max_grade >= 3)

    def summary(self) -> Dict[str, Any]:
        n = self.n_patients
        return {
            "trial": self.trial_name,
            "n": n,
            "crs_any": f"{self.crs_any_count()}/{n} ({100*self.crs_any_count()/n:.0f}%)",
            "crs_3+": f"{self.crs_grade3plus_count()}/{n} ({100*self.crs_grade3plus_count()/n:.0f}%)",
            "icans_any": f"{self.icans_any_count()}/{n} ({100*self.icans_any_count()/n:.0f}%)",
            "icans_3+": f"{self.icans_grade3plus_count()}/{n} ({100*self.icans_grade3plus_count()/n:.0f}%)",
            "median_age": int(np.median([p.age for p in self.patients])),
            "male_pct": f"{100*sum(1 for p in self.patients if p.sex=='M')/n:.0f}%",
        }


# ============================================================================
# Generator helpers
# ============================================================================

def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _round2(value: float) -> float:
    return round(value, 2)


def _dubois_bsa(weight_kg: float, height_cm: float) -> float:
    """DuBois BSA formula."""
    return 0.007184 * (weight_kg ** 0.425) * (height_cm ** 0.725)


def _crs_risk_modifier(
    tumor_burden: float,
    baseline_ldh: float,
    costim: str,
    comorbidities: Comorbidities,
) -> float:
    """
    Compute a multiplicative risk modifier for CRS based on patient factors.
    Returns a value centered around 1.0.

    This modifier is intentionally kept close to 1.0 so that the aggregate
    cohort rates match published trial data (which already reflect the
    product's costimulatory domain). The modifier primarily shifts individual
    risk within the cohort rather than inflating the overall rate.
    """
    mod = 1.0
    # Higher tumor burden increases CRS risk (modest effect on binary rate)
    if tumor_burden > 40:
        mod *= 1.08
    elif tumor_burden > 20:
        mod *= 1.03
    # Higher baseline LDH increases CRS risk
    if baseline_ldh > 400:
        mod *= 1.06
    elif baseline_ldh > 300:
        mod *= 1.02
    # Costimulatory domain: the trial rates already encode this difference,
    # so we apply only a small nudge for individual variability
    if costim == "CD28":
        mod *= 1.02
    else:  # 4-1BB
        mod *= 0.98
    # Comorbidities add modest risk
    if comorbidities.cardiovascular:
        mod *= 1.02
    if comorbidities.renal:
        mod *= 1.02
    return mod


def _generate_baseline_labs(rng: np.random.Generator, cfg: TrialConfig,
                            comorbidities: Comorbidities) -> BaselineLabs:
    """Generate physiologically plausible baseline lab values."""
    labs = BaselineLabs()

    # Post-lymphodepletion CBC: patients are typically cytopenic
    labs.WBC = _clamp(rng.normal(3.5, 2.0), 0.5, 15.0)
    labs.ANC = _clamp(rng.normal(2.0, 1.2), 0.1, 10.0)
    labs.ALC = _clamp(rng.normal(0.5, 0.4), 0.05, 3.0)
    labs.Hemoglobin = _clamp(rng.normal(10.5, 2.0), 6.0, 16.0)
    labs.Platelets = _clamp(rng.normal(120.0, 60.0), 10.0, 400.0)

    # CMP
    base_creat = 1.0 if not comorbidities.renal else 1.6
    labs.Creatinine = _clamp(rng.normal(base_creat, 0.3), 0.4, 4.0)
    labs.BUN = _clamp(rng.normal(15.0, 6.0), 5.0, 60.0)

    base_ast = 30.0 if not comorbidities.hepatic else 55.0
    labs.AST = _clamp(rng.normal(base_ast, 12.0), 8.0, 200.0)
    labs.ALT = _clamp(rng.normal(base_ast - 5, 15.0), 5.0, 200.0)

    labs.LDH = _clamp(rng.normal(cfg.baseline_ldh_mean, cfg.baseline_ldh_std),
                       100.0, 2000.0)
    labs.Albumin = _clamp(rng.normal(3.6, 0.5), 1.5, 5.0)

    # Inflammatory markers
    labs.CRP = _clamp(rng.normal(cfg.baseline_crp_mean, cfg.baseline_crp_std),
                       0.1, 80.0)
    labs.Ferritin = _clamp(rng.normal(cfg.baseline_ferritin_mean, cfg.baseline_ferritin_std),
                            10.0, 3000.0)
    labs.Fibrinogen = _clamp(rng.normal(310.0, 60.0), 150.0, 600.0)
    labs.D_dimer = _clamp(rng.exponential(0.4), 0.1, 5.0)

    # Round all values
    for fld in labs.__dataclass_fields__:
        setattr(labs, fld, _round2(getattr(labs, fld)))

    return labs


# ============================================================================
# Outcome assignment
# ============================================================================

def _assign_outcomes(
    rng: np.random.Generator,
    cfg: TrialConfig,
    patient: PatientRecord,
) -> None:
    """
    Assign CRS, ICANS, and IEC-HS outcomes to a patient based on trial rates
    and individual risk factors.
    """
    risk_mod = _crs_risk_modifier(
        patient.tumor_burden_spd if cfg.disease_type == "NHL" else patient.paraprotein_burden * 10,
        patient.baseline_labs.LDH,
        cfg.product.costimulatory_domain,
        patient.comorbidities,
    )

    # --- CRS ---
    # Apply risk_mod on the logit scale so that high base rates aren't pushed
    # above their natural ceiling.  This keeps aggregate rates close to the
    # published trial figures while still allowing individual variability.
    base_rate = cfg.crs_any_rate
    if base_rate <= 0:
        effective_crs_rate = 0.0
    elif base_rate >= 1.0:
        effective_crs_rate = 0.99
    else:
        logit = math.log(base_rate / (1 - base_rate))
        logit += (risk_mod - 1.0) * 2.0  # moderate shift on logit scale
        effective_crs_rate = 1.0 / (1.0 + math.exp(-logit))
    effective_crs_rate = _clamp(effective_crs_rate, 0.0, 0.99)
    patient.crs.occurred = rng.random() < effective_crs_rate

    if patient.crs.occurred:
        # Grade assignment
        # Probability of grade 3+ among CRS patients
        if cfg.crs_any_rate > 0:
            p_severe = cfg.crs_grade3plus_rate / cfg.crs_any_rate
        else:
            p_severe = 0.0
        p_severe = _clamp(p_severe * risk_mod, 0.0, 0.95)
        is_severe = rng.random() < p_severe
        if is_severe:
            patient.crs.max_grade = rng.choice([3, 4], p=[0.7, 0.3])
        else:
            patient.crs.max_grade = rng.choice([1, 2], p=[0.55, 0.45])

        # Onset timing
        onset = rng.normal(cfg.crs_median_onset_day, cfg.crs_onset_std)
        patient.crs.onset_day = _clamp(round(onset, 1), 0.5, 21.0)

        # Peak and resolution
        if patient.crs.max_grade >= 3:
            peak_delay = rng.uniform(1.0, 3.0)
            resolution_delay = rng.uniform(3.0, 8.0)
            patient.crs.required_tocilizumab = rng.random() < 0.85
            patient.crs.required_steroids = rng.random() < 0.60
            patient.crs.required_vasopressors = patient.crs.max_grade == 4
        else:
            peak_delay = rng.uniform(0.5, 2.0)
            resolution_delay = rng.uniform(1.5, 5.0)
            patient.crs.required_tocilizumab = rng.random() < 0.20
            patient.crs.required_steroids = rng.random() < 0.10
            patient.crs.required_vasopressors = False

        patient.crs.peak_day = round(patient.crs.onset_day + peak_delay, 1)
        patient.crs.resolution_day = round(patient.crs.peak_day + resolution_delay, 1)

    # --- ICANS ---
    # ICANS rate from the trial config already reflects the overall population.
    # We apply a modest CRS-conditional shift to preserve aggregate rates.
    effective_icans_rate = cfg.icans_any_rate
    if patient.crs.occurred:
        effective_icans_rate = _clamp(effective_icans_rate * 1.05, 0.0, 0.95)
    else:
        effective_icans_rate = _clamp(effective_icans_rate * 0.50, 0.0, 0.95)
    patient.icans.occurred = rng.random() < effective_icans_rate

    if patient.icans.occurred:
        if cfg.icans_any_rate > 0:
            p_severe_icans = cfg.icans_grade3plus_rate / cfg.icans_any_rate
        else:
            p_severe_icans = 0.0
        p_severe_icans = _clamp(p_severe_icans * risk_mod, 0.0, 0.90)
        is_severe_icans = rng.random() < p_severe_icans
        if is_severe_icans:
            patient.icans.max_grade = rng.choice([3, 4], p=[0.65, 0.35])
            patient.icans.ice_score_nadir = rng.integers(0, 4)
        else:
            patient.icans.max_grade = rng.choice([1, 2], p=[0.50, 0.50])
            patient.icans.ice_score_nadir = rng.integers(4, 8)

        # ICANS onset: 24-48h after CRS onset (if CRS), otherwise around CRS timing
        if patient.crs.occurred:
            icans_delay = rng.uniform(1.0, 3.0)
            patient.icans.onset_day = round(patient.crs.onset_day + icans_delay, 1)
        else:
            patient.icans.onset_day = round(rng.normal(cfg.crs_median_onset_day + 2.0, 2.0), 1)
            patient.icans.onset_day = _clamp(patient.icans.onset_day, 1.0, 21.0)

        peak_delay_icans = rng.uniform(0.5, 2.5)
        resolution_delay_icans = rng.uniform(2.0, 7.0)
        patient.icans.peak_day = round(patient.icans.onset_day + peak_delay_icans, 1)
        patient.icans.resolution_day = round(patient.icans.peak_day + resolution_delay_icans, 1)

    # --- IEC-HS (HLH-like) ---
    if patient.crs.occurred and patient.crs.max_grade >= 3:
        # IEC-HS develops from severe CRS
        effective_hs_rate = _clamp(cfg.iec_hs_rate * 5.0, 0.0, 0.50)
        patient.iec_hs.occurred = rng.random() < effective_hs_rate
    else:
        patient.iec_hs.occurred = False

    if patient.iec_hs.occurred:
        patient.iec_hs.onset_day = round(patient.crs.peak_day + rng.uniform(0.5, 2.0), 1)
        patient.iec_hs.peak_ferritin = rng.uniform(10000.0, 80000.0)
        patient.iec_hs.nadir_fibrinogen = rng.uniform(50.0, 149.0)
        patient.iec_hs.peak_triglycerides = rng.uniform(265.0, 600.0)


# ============================================================================
# Time-series generation
# ============================================================================

def _generate_vitals_timeseries(
    rng: np.random.Generator,
    patient: PatientRecord,
    cfg: TrialConfig,
) -> List[VitalSigns]:
    """
    Generate vital signs q4-6h from Day -7 through Day 28.
    Total: ~35 days * 5 measurements/day = ~175 timepoints.
    """
    vitals = []
    # Start at Day -7 (hour -168) through Day 28 (hour 672)
    start_hour = -168.0
    end_hour = 672.0

    # Base vitals for this patient
    base_temp = rng.normal(36.8, 0.2)
    base_hr = rng.normal(78.0, 8.0)
    base_bp_sys = rng.normal(125.0, 12.0)
    base_bp_dia = rng.normal(75.0, 8.0)
    base_rr = rng.normal(16.0, 2.0)
    base_spo2 = _clamp(rng.normal(97.5, 1.0), 93.0, 100.0)

    # Age adjustment
    if patient.age > 65:
        base_bp_sys += 8
        base_hr -= 3

    # Comorbidity adjustments
    if patient.comorbidities.cardiovascular:
        base_hr += 5
        base_bp_sys += 10
    if patient.comorbidities.pulmonary:
        base_spo2 -= 1.0
        base_rr += 2

    # CRS effects: define the CRS temporal profile
    crs_onset_h = patient.crs.onset_day * 24.0 if patient.crs.occurred else 9999.0
    crs_peak_h = patient.crs.peak_day * 24.0 if patient.crs.occurred else 9999.0
    crs_resolve_h = patient.crs.resolution_day * 24.0 if patient.crs.occurred else 9999.0

    # Pre-CRS fever: temperature rises 8-12h before clinical onset
    pre_crs_h = crs_onset_h - rng.uniform(8.0, 12.0)

    t = start_hour
    while t <= end_hour:
        # Interval: 4-6 hours with some jitter
        interval = rng.uniform(4.0, 6.0)

        vs = VitalSigns(time_hours=round(t, 1))

        # Compute CRS effect magnitude at this timepoint
        crs_effect = 0.0
        if patient.crs.occurred and t >= pre_crs_h:
            if t < crs_onset_h:
                # Prodromal: gradual rise
                frac = (t - pre_crs_h) / (crs_onset_h - pre_crs_h)
                crs_effect = frac * 0.3
            elif t < crs_peak_h:
                # Escalation to peak
                frac = (t - crs_onset_h) / max(crs_peak_h - crs_onset_h, 1.0)
                crs_effect = 0.3 + frac * 0.7
            elif t < crs_resolve_h:
                # Resolution
                frac = (t - crs_peak_h) / max(crs_resolve_h - crs_peak_h, 1.0)
                crs_effect = 1.0 - frac * 0.85
            else:
                crs_effect = 0.05  # residual

        grade_mult = patient.crs.max_grade / 4.0 if patient.crs.occurred else 0.0

        # Temperature
        temp_crs = crs_effect * grade_mult * rng.uniform(2.5, 4.5)
        vs.Temperature = _round2(base_temp + temp_crs + rng.normal(0, 0.15))
        vs.Temperature = _clamp(vs.Temperature, 35.5, 42.0)

        # Heart rate: rises with fever/CRS
        hr_crs = crs_effect * grade_mult * rng.uniform(15, 40)
        vs.HR = _round2(base_hr + hr_crs + rng.normal(0, 3))
        vs.HR = _clamp(vs.HR, 40.0, 180.0)

        # Blood pressure: drops in severe CRS
        bp_drop = crs_effect * grade_mult * rng.uniform(10, 35) if patient.crs.max_grade >= 3 else 0
        vs.BP_sys = _round2(base_bp_sys - bp_drop + rng.normal(0, 4))
        vs.BP_sys = _clamp(vs.BP_sys, 60.0, 200.0)
        vs.BP_dia = _round2(base_bp_dia - bp_drop * 0.5 + rng.normal(0, 3))
        vs.BP_dia = _clamp(vs.BP_dia, 35.0, 120.0)

        # Respiratory rate: rises with CRS
        rr_crs = crs_effect * grade_mult * rng.uniform(3, 10)
        vs.RR = _round2(base_rr + rr_crs + rng.normal(0, 1))
        vs.RR = _clamp(vs.RR, 8.0, 40.0)

        # SpO2: drops in severe CRS
        spo2_drop = crs_effect * grade_mult * rng.uniform(2, 8) if patient.crs.max_grade >= 2 else 0
        vs.SpO2 = _round2(base_spo2 - spo2_drop + rng.normal(0, 0.5))
        vs.SpO2 = _clamp(vs.SpO2, 70.0, 100.0)

        vitals.append(vs)
        t += interval

    return vitals


def _generate_labs_timeseries(
    rng: np.random.Generator,
    patient: PatientRecord,
    cfg: TrialConfig,
) -> List[LabPanel]:
    """
    Generate daily lab panels from Day -7 through Day 28 (36 days).
    Labs reflect lymphodepletion nadir, CRS inflammation, and IEC-HS if present.
    """
    panels = []
    bl = patient.baseline_labs

    crs_onset_h = patient.crs.onset_day * 24.0 if patient.crs.occurred else 9999.0
    crs_peak_h = patient.crs.peak_day * 24.0 if patient.crs.occurred else 9999.0
    crs_resolve_h = patient.crs.resolution_day * 24.0 if patient.crs.occurred else 9999.0

    hs_onset_h = patient.iec_hs.onset_day * 24.0 if patient.iec_hs.occurred else 9999.0

    for day in range(-7, 29):
        t_h = day * 24.0
        panel = LabPanel(time_hours=t_h)

        # --- Lymphodepletion effect ---
        # Nadir around Day -2 to Day 2, recovery by Day 14
        ld_day = day  # relative to infusion
        if ld_day < -5:
            ld_effect = 0.0
        elif ld_day < 0:
            ld_effect = min(1.0, (ld_day + 5) / 5.0)
        elif ld_day < 3:
            ld_effect = 1.0  # nadir
        elif ld_day < 14:
            ld_effect = 1.0 - (ld_day - 3) / 11.0
        else:
            ld_effect = 0.0

        # --- CRS inflammatory effect ---
        crs_effect = 0.0
        if patient.crs.occurred:
            if t_h < crs_onset_h:
                if t_h > crs_onset_h - 24:
                    crs_effect = (t_h - (crs_onset_h - 24)) / 24.0 * 0.3
            elif t_h < crs_peak_h:
                frac = (t_h - crs_onset_h) / max(crs_peak_h - crs_onset_h, 1.0)
                crs_effect = 0.3 + frac * 0.7
            elif t_h < crs_resolve_h:
                frac = (t_h - crs_peak_h) / max(crs_resolve_h - crs_peak_h, 1.0)
                crs_effect = 1.0 - frac * 0.8
            else:
                crs_effect = 0.05

        grade_factor = patient.crs.max_grade / 4.0 if patient.crs.occurred else 0.0

        # --- IEC-HS effect ---
        hs_effect = 0.0
        if patient.iec_hs.occurred and t_h >= hs_onset_h:
            hs_duration = 5.0 * 24.0  # ~5 day course
            if t_h < hs_onset_h + hs_duration:
                frac = (t_h - hs_onset_h) / hs_duration
                hs_effect = math.sin(frac * math.pi)  # bell-shaped
            else:
                hs_effect = 0.05

        # --- CBC ---
        wbc_suppression = ld_effect * 0.7
        panel.WBC = _round2(_clamp(
            bl.WBC * (1 - wbc_suppression) + rng.normal(0, 0.3),
            0.1, 30.0
        ))
        panel.ANC = _round2(_clamp(
            bl.ANC * (1 - wbc_suppression * 0.8) + rng.normal(0, 0.2),
            0.01, 20.0
        ))
        panel.ALC = _round2(_clamp(
            bl.ALC * (1 - wbc_suppression * 0.9) + rng.normal(0, 0.05),
            0.0, 5.0
        ))
        panel.Hemoglobin = _round2(_clamp(
            bl.Hemoglobin - ld_effect * 1.5 + rng.normal(0, 0.3),
            5.0, 17.0
        ))
        panel.Platelets = _round2(_clamp(
            bl.Platelets * (1 - ld_effect * 0.5) + rng.normal(0, 10),
            5.0, 500.0
        ))

        # --- CMP ---
        panel.Creatinine = _round2(_clamp(
            bl.Creatinine + crs_effect * grade_factor * 0.5 + rng.normal(0, 0.05),
            0.3, 6.0
        ))
        panel.BUN = _round2(_clamp(
            bl.BUN + crs_effect * grade_factor * 8 + rng.normal(0, 1),
            3.0, 80.0
        ))
        panel.AST = _round2(_clamp(
            bl.AST * (1 + crs_effect * grade_factor * 2.0) + rng.normal(0, 3),
            5.0, 1000.0
        ))
        panel.ALT = _round2(_clamp(
            bl.ALT * (1 + crs_effect * grade_factor * 1.5) + rng.normal(0, 3),
            5.0, 1000.0
        ))
        panel.Albumin = _round2(_clamp(
            bl.Albumin - crs_effect * grade_factor * 1.0 + rng.normal(0, 0.1),
            1.0, 5.5
        ))

        # LDH: rises with CRS and tumor lysis
        ldh_crs = crs_effect * grade_factor * bl.LDH * 1.5
        panel.LDH = _round2(_clamp(
            bl.LDH + ldh_crs + rng.normal(0, 15),
            80.0, 5000.0
        ))

        # --- Inflammatory markers ---
        # CRP: dramatic rise during CRS
        crp_peak = 50 + grade_factor * 200  # up to 250 for grade 4
        panel.CRP = _round2(_clamp(
            bl.CRP + crs_effect * crp_peak + rng.normal(0, 3),
            0.1, 500.0
        ))

        # Ferritin: rises dramatically, especially in IEC-HS
        ferritin_crs = crs_effect * grade_factor * 3000
        ferritin_hs = hs_effect * patient.iec_hs.peak_ferritin if patient.iec_hs.occurred else 0
        panel.Ferritin = _round2(_clamp(
            bl.Ferritin + ferritin_crs + ferritin_hs + rng.normal(0, 50),
            5.0, 100000.0
        ))

        # Fibrinogen: drops in severe CRS and especially IEC-HS (consumptive)
        fib_drop_crs = crs_effect * grade_factor * 100
        fib_drop_hs = hs_effect * (bl.Fibrinogen - patient.iec_hs.nadir_fibrinogen) if patient.iec_hs.occurred else 0
        panel.Fibrinogen = _round2(_clamp(
            bl.Fibrinogen - fib_drop_crs - fib_drop_hs + rng.normal(0, 10),
            30.0, 800.0
        ))

        # D-dimer: rises with coagulopathy
        panel.D_dimer = _round2(_clamp(
            bl.D_dimer + crs_effect * grade_factor * 8 + hs_effect * 15 + rng.normal(0, 0.2),
            0.1, 40.0
        ))

        # Triglycerides (important for IEC-HS)
        base_tg = rng.normal(130.0, 40.0) if day == -7 else (panels[-1].Triglycerides or 130.0)
        tg_hs = hs_effect * (patient.iec_hs.peak_triglycerides - 130) if patient.iec_hs.occurred else 0
        panel.Triglycerides = _round2(_clamp(
            base_tg + tg_hs + rng.normal(0, 5),
            40.0, 800.0
        ))

        panels.append(panel)

    return panels


def _generate_cytokine_timeseries(
    rng: np.random.Generator,
    patient: PatientRecord,
    cfg: TrialConfig,
) -> List[CytokinePanel]:
    """
    Generate cytokine panels q12h from Day 0 through Day 28 (57 timepoints).

    Key dynamics:
    - IL-6 rises 12-24h BEFORE clinical CRS symptoms (sentinel marker)
    - IFN-gamma rises with T-cell expansion
    - TNF-alpha: early acute phase
    - IL-10: regulatory response, rises with severity
    - MCP-1: monocyte recruitment
    - IL-1RA: anti-inflammatory, rises as counter-regulation
    - sgp130: soluble receptor, modulates IL-6 trans-signaling
    """
    panels = []

    crs_onset_h = patient.crs.onset_day * 24.0 if patient.crs.occurred else 9999.0
    crs_peak_h = patient.crs.peak_day * 24.0 if patient.crs.occurred else 9999.0
    crs_resolve_h = patient.crs.resolution_day * 24.0 if patient.crs.occurred else 9999.0

    grade_factor = patient.crs.max_grade / 4.0 if patient.crs.occurred else 0.0

    # IL-6 precursor window: 12-24h before clinical onset
    il6_lead_h = rng.uniform(12.0, 24.0)

    for t_h in np.arange(0, 28 * 24 + 12, 12):
        cp = CytokinePanel(time_hours=float(t_h))

        # CRS effect at this timepoint
        crs_eff = 0.0
        if patient.crs.occurred:
            if t_h < crs_onset_h:
                if t_h > crs_onset_h - il6_lead_h * 2:
                    crs_eff = (t_h - (crs_onset_h - il6_lead_h * 2)) / (il6_lead_h * 2) * 0.2
            elif t_h < crs_peak_h:
                frac = (t_h - crs_onset_h) / max(crs_peak_h - crs_onset_h, 1.0)
                crs_eff = 0.2 + frac * 0.8
            elif t_h < crs_resolve_h:
                frac = (t_h - crs_peak_h) / max(crs_resolve_h - crs_peak_h, 1.0)
                crs_eff = 1.0 - frac * 0.85
            else:
                crs_eff = 0.05

        # IL-6 precursor effect: rises BEFORE clinical CRS
        il6_pre_eff = 0.0
        if patient.crs.occurred and t_h >= (crs_onset_h - il6_lead_h) and t_h < crs_onset_h:
            il6_pre_eff = (t_h - (crs_onset_h - il6_lead_h)) / il6_lead_h

        # --- IL-6: sentinel marker, precedes clinical CRS ---
        il6_base = rng.uniform(2.0, 6.0)
        il6_peak = grade_factor * rng.uniform(500, 20000)
        il6_pre = il6_pre_eff * il6_peak * 0.3  # subclinical rise
        cp.IL6 = _round2(_clamp(
            il6_base + il6_pre + crs_eff * il6_peak + rng.normal(0, il6_base * 0.1),
            0.5, 50000.0
        ))

        # --- IFN-gamma: T-cell activation, rises with expansion ---
        ifng_base = rng.uniform(3.0, 12.0)
        ifng_peak = grade_factor * rng.uniform(200, 5000)
        cp.IFN_gamma = _round2(_clamp(
            ifng_base + crs_eff * ifng_peak + rng.normal(0, ifng_base * 0.1),
            0.5, 10000.0
        ))

        # --- TNF-alpha: early acute, peaks slightly before IL-6 peak ---
        tnf_base = rng.uniform(2.0, 7.0)
        tnf_peak = grade_factor * rng.uniform(30, 300)
        # TNF peaks a bit earlier than overall CRS peak
        tnf_shift = 0.0
        if patient.crs.occurred and crs_onset_h <= t_h < crs_peak_h:
            range_h = max(crs_peak_h - crs_onset_h, 1.0)
            tnf_shift = math.sin(((t_h - crs_onset_h) / range_h) * math.pi) * 0.3
        cp.TNF_alpha = _round2(_clamp(
            tnf_base + (crs_eff + tnf_shift) * tnf_peak + rng.normal(0, 1),
            0.5, 2000.0
        ))

        # --- IL-10: regulatory, rises proportionally to severity ---
        il10_base = rng.uniform(1.0, 4.0)
        il10_peak = grade_factor * rng.uniform(100, 3000)
        cp.IL10 = _round2(_clamp(
            il10_base + crs_eff * il10_peak + rng.normal(0, il10_base * 0.1),
            0.1, 8000.0
        ))

        # --- MCP-1: monocyte chemotaxis ---
        mcp_base = rng.uniform(50, 250)
        mcp_peak = grade_factor * rng.uniform(500, 5000)
        cp.MCP1 = _round2(_clamp(
            mcp_base + crs_eff * mcp_peak + rng.normal(0, 10),
            10.0, 15000.0
        ))

        # --- IL-1RA: counter-regulatory, slightly delayed ---
        il1ra_base = rng.uniform(100, 400)
        il1ra_peak = grade_factor * rng.uniform(2000, 20000)
        # IL-1RA peaks slightly after IL-6
        delayed_eff = 0.0
        if patient.crs.occurred and t_h > crs_onset_h:
            delay_shift = min(12.0, (t_h - crs_onset_h))
            delayed_eff = crs_eff * (delay_shift / 12.0)
        cp.IL1RA = _round2(_clamp(
            il1ra_base + delayed_eff * il1ra_peak + rng.normal(0, 20),
            10.0, 50000.0
        ))

        # --- sgp130: soluble receptor, modulates trans-signaling ---
        sgp130_base = rng.uniform(220, 350)
        # sgp130 tends to rise modestly, consumed in severe CRS
        sgp_change = -crs_eff * grade_factor * 80 + rng.normal(0, 10)
        cp.sgp130 = _round2(_clamp(
            sgp130_base + sgp_change,
            100.0, 600.0
        ))

        panels.append(cp)

    return panels


def _generate_ice_scores(
    rng: np.random.Generator,
    patient: PatientRecord,
) -> List[Tuple[float, int]]:
    """
    Generate daily ICE scores (Day 0-28). ICE score: 0-10, 10=normal.
    Deterioration tracks with ICANS.
    """
    scores = []
    icans_onset_h = patient.icans.onset_day * 24.0 if patient.icans.occurred else 9999.0
    icans_peak_h = patient.icans.peak_day * 24.0 if patient.icans.occurred else 9999.0
    icans_resolve_h = patient.icans.resolution_day * 24.0 if patient.icans.occurred else 9999.0

    for day in range(0, 29):
        t_h = day * 24.0
        base_score = 10

        if patient.icans.occurred:
            if t_h < icans_onset_h:
                score = base_score
            elif t_h < icans_peak_h:
                frac = (t_h - icans_onset_h) / max(icans_peak_h - icans_onset_h, 1.0)
                drop = (10 - patient.icans.ice_score_nadir) * frac
                score = int(round(base_score - drop))
            elif t_h < icans_resolve_h:
                frac = (t_h - icans_peak_h) / max(icans_resolve_h - icans_peak_h, 1.0)
                recovery = (10 - patient.icans.ice_score_nadir) * frac
                score = int(round(patient.icans.ice_score_nadir + recovery))
            else:
                score = base_score
        else:
            score = base_score

        # Add small noise
        score = int(_clamp(score + rng.integers(-1, 2), 0, 10))
        scores.append((float(t_h), score))

    return scores


# ============================================================================
# Patient generation
# ============================================================================

def _generate_patient(
    rng: np.random.Generator,
    cfg: TrialConfig,
    index: int,
    patient_id_prefix: str,
) -> PatientRecord:
    """Generate a single complete patient record."""
    patient = PatientRecord()

    # --- Identifiers ---
    patient.patient_id = f"{patient_id_prefix}-{index:04d}"
    patient.trial_name = cfg.trial_name
    patient.cohort_index = index

    # --- Demographics ---
    patient.age = int(_clamp(
        rng.normal(cfg.median_age, cfg.age_std),
        cfg.age_min, cfg.age_max
    ))
    patient.sex = "M" if rng.random() < cfg.male_fraction else "F"

    # Weight (sex-adjusted)
    if patient.sex == "M":
        patient.weight_kg = _clamp(rng.normal(cfg.weight_mean, cfg.weight_std), 45, 160)
    else:
        patient.weight_kg = _clamp(rng.normal(cfg.weight_mean - 12, cfg.weight_std - 2), 40, 140)
    patient.weight_kg = round(patient.weight_kg, 1)

    # Height
    if patient.sex == "M":
        patient.height_cm = round(_clamp(rng.normal(177, 7), 155, 200), 1)
    else:
        patient.height_cm = round(_clamp(rng.normal(163, 7), 145, 185), 1)

    patient.bsa_m2 = round(_dubois_bsa(patient.weight_kg, patient.height_cm), 2)

    # --- Disease ---
    patient.disease_type = cfg.disease_type
    patient.disease_subtype = cfg.disease_subtype

    if cfg.disease_type == "NHL":
        patient.disease_stage = rng.choice(["III", "IV"], p=[0.3, 0.7])
        patient.tumor_burden_spd = round(_clamp(
            rng.normal(cfg.spd_mean, cfg.spd_std), 2.0, 150.0
        ), 1)
        patient.paraprotein_burden = 0.0
    else:  # Multiple Myeloma
        patient.disease_stage = rng.choice(["ISS-I", "ISS-II", "ISS-III"], p=[0.2, 0.35, 0.45])
        patient.tumor_burden_spd = 0.0
        patient.paraprotein_burden = round(_clamp(rng.exponential(2.5), 0.1, 12.0), 2)

    patient.prior_lines = int(_clamp(
        rng.normal(cfg.prior_lines_mean, cfg.prior_lines_std), 2, 10
    ))

    # --- Comorbidities ---
    patient.comorbidities = Comorbidities(
        cardiovascular=rng.random() < cfg.comorbidity_cardiovascular_rate,
        pulmonary=rng.random() < cfg.comorbidity_pulmonary_rate,
        renal=rng.random() < cfg.comorbidity_renal_rate,
        hepatic=rng.random() < cfg.comorbidity_hepatic_rate,
    )

    # --- Lymphodepletion ---
    patient.lymphodepletion = cfg.lymphodepletion.description

    # --- CAR-T product ---
    product = cfg.product
    dose = CARTDose(
        product_name=product.name,
        trade_name=product.trade_name,
        target=product.target,
        costimulatory_domain=product.costimulatory_domain,
        dose_unit=product.dose_unit,
        cd4_cd8_ratio=round(_clamp(
            rng.normal(product.cd4_cd8_ratio_mean, product.cd4_cd8_ratio_std),
            0.1, 5.0
        ), 2),
        viability_pct=round(_clamp(rng.normal(92.0, 5.0), 70.0, 99.9), 1),
    )
    if product.dose_unit == "cells/kg":
        dose.dose_value = round(rng.uniform(product.dose_min, product.dose_max), 0)
    else:
        dose.dose_value = round(rng.uniform(product.dose_min, product.dose_max), 0)
    patient.cart_dose = dose

    # --- Baseline labs ---
    patient.baseline_labs = _generate_baseline_labs(rng, cfg, patient.comorbidities)

    # --- Outcomes ---
    _assign_outcomes(rng, cfg, patient)

    # --- Time series ---
    patient.vitals_timeseries = _generate_vitals_timeseries(rng, patient, cfg)
    patient.labs_timeseries = _generate_labs_timeseries(rng, patient, cfg)
    patient.cytokine_timeseries = _generate_cytokine_timeseries(rng, patient, cfg)
    patient.ice_scores = _generate_ice_scores(rng, patient)

    return patient


# ============================================================================
# Cohort generation
# ============================================================================

def generate_cohort(cfg: TrialConfig) -> CohortData:
    """
    Generate a complete cohort for a single trial configuration.

    Uses the trial's seed for reproducibility.
    """
    rng = np.random.default_rng(cfg.seed)

    # Generate a prefix from trial name (e.g., "ZUMA-1" -> "ZUM")
    prefix = cfg.trial_name.replace("-", "").replace(" ", "")[:3].upper()

    patients = []
    for i in range(cfg.n_patients):
        patient = _generate_patient(rng, cfg, i, prefix)
        patients.append(patient)

    cohort = CohortData(
        trial_name=cfg.trial_name,
        config=cfg,
        patients=patients,
    )

    return cohort


def generate_all_cohorts() -> Tuple[Dict[str, CohortData], CohortData]:
    """
    Generate all 6 trial cohorts plus a combined mega-cohort of 785 patients.

    Returns:
        Tuple of:
            - Dict mapping trial name -> CohortData
            - CohortData: combined mega-cohort with all 785 patients
    """
    cohorts: Dict[str, CohortData] = {}

    for trial_name, cfg in ALL_TRIALS.items():
        cohorts[trial_name] = generate_cohort(cfg)

    # Build mega-cohort
    all_patients: List[PatientRecord] = []
    for cohort in cohorts.values():
        all_patients.extend(cohort.patients)

    # Re-index patients in mega-cohort
    for i, patient in enumerate(all_patients):
        patient_copy = copy.deepcopy(patient)
        patient_copy.cohort_index = i
        all_patients[i] = patient_copy

    # Use ZUMA-1 config as placeholder for mega-cohort config
    mega_cohort = CohortData(
        trial_name="MEGA-COHORT",
        config=ALL_TRIALS["ZUMA-1"],  # placeholder
        patients=all_patients,
    )

    return cohorts, mega_cohort


# ============================================================================
# Convenience utilities
# ============================================================================

def cohort_to_flat_dicts(cohort: CohortData) -> List[Dict[str, Any]]:
    """
    Convert a cohort to a list of flat dictionaries (one per patient)
    for easy conversion to pandas DataFrames.

    Includes baseline data and outcome labels but NOT full time-series.
    """
    rows = []
    for p in cohort.patients:
        row = {
            "patient_id": p.patient_id,
            "trial_name": p.trial_name,
            "age": p.age,
            "sex": p.sex,
            "weight_kg": p.weight_kg,
            "height_cm": p.height_cm,
            "bsa_m2": p.bsa_m2,
            "disease_type": p.disease_type,
            "disease_subtype": p.disease_subtype,
            "disease_stage": p.disease_stage,
            "tumor_burden_spd": p.tumor_burden_spd,
            "paraprotein_burden": p.paraprotein_burden,
            "prior_lines": p.prior_lines,
            "comorbidity_cv": p.comorbidities.cardiovascular,
            "comorbidity_pulm": p.comorbidities.pulmonary,
            "comorbidity_renal": p.comorbidities.renal,
            "comorbidity_hepatic": p.comorbidities.hepatic,
            "lymphodepletion": p.lymphodepletion,
            "cart_product": p.cart_dose.product_name,
            "cart_target": p.cart_dose.target,
            "cart_costim": p.cart_dose.costimulatory_domain,
            "cart_dose": p.cart_dose.dose_value,
            "cart_dose_unit": p.cart_dose.dose_unit,
            "cd4_cd8_ratio": p.cart_dose.cd4_cd8_ratio,
            "viability_pct": p.cart_dose.viability_pct,
            # Baseline labs
            "bl_WBC": p.baseline_labs.WBC,
            "bl_ANC": p.baseline_labs.ANC,
            "bl_ALC": p.baseline_labs.ALC,
            "bl_Hemoglobin": p.baseline_labs.Hemoglobin,
            "bl_Platelets": p.baseline_labs.Platelets,
            "bl_Creatinine": p.baseline_labs.Creatinine,
            "bl_BUN": p.baseline_labs.BUN,
            "bl_AST": p.baseline_labs.AST,
            "bl_ALT": p.baseline_labs.ALT,
            "bl_LDH": p.baseline_labs.LDH,
            "bl_Albumin": p.baseline_labs.Albumin,
            "bl_CRP": p.baseline_labs.CRP,
            "bl_Ferritin": p.baseline_labs.Ferritin,
            "bl_Fibrinogen": p.baseline_labs.Fibrinogen,
            "bl_D_dimer": p.baseline_labs.D_dimer,
            # Outcomes
            "crs_occurred": p.crs.occurred,
            "crs_max_grade": p.crs.max_grade,
            "crs_onset_day": p.crs.onset_day if p.crs.occurred else None,
            "crs_peak_day": p.crs.peak_day if p.crs.occurred else None,
            "crs_resolution_day": p.crs.resolution_day if p.crs.occurred else None,
            "crs_tocilizumab": p.crs.required_tocilizumab,
            "crs_steroids": p.crs.required_steroids,
            "crs_vasopressors": p.crs.required_vasopressors,
            "icans_occurred": p.icans.occurred,
            "icans_max_grade": p.icans.max_grade,
            "icans_onset_day": p.icans.onset_day if p.icans.occurred else None,
            "icans_ice_nadir": p.icans.ice_score_nadir if p.icans.occurred else None,
            "iec_hs_occurred": p.iec_hs.occurred,
            "iec_hs_peak_ferritin": p.iec_hs.peak_ferritin if p.iec_hs.occurred else None,
            "iec_hs_nadir_fibrinogen": p.iec_hs.nadir_fibrinogen if p.iec_hs.occurred else None,
            # Flags
            "has_missing_data": p.has_missing_data,
            "is_edge_case": p.is_edge_case,
            "edge_case_type": p.edge_case_type,
            # Time series lengths (for validation)
            "n_vitals": len(p.vitals_timeseries),
            "n_labs": len(p.labs_timeseries),
            "n_cytokines": len(p.cytokine_timeseries),
        }
        rows.append(row)
    return rows


def print_cohort_summary(cohorts: Dict[str, CohortData]) -> None:
    """Print a summary table of all cohorts."""
    print(f"{'Trial':<15} {'N':>4} {'CRS any':>10} {'CRS 3+':>10} "
          f"{'ICANS any':>10} {'ICANS 3+':>10} {'Age':>5} {'Male':>6}")
    print("-" * 80)
    total_n = 0
    for name, cohort in cohorts.items():
        s = cohort.summary()
        print(f"{name:<15} {s['n']:>4} {s['crs_any']:>10} {s['crs_3+']:>10} "
              f"{s['icans_any']:>10} {s['icans_3+']:>10} {s['median_age']:>5} {s['male_pct']:>6}")
        total_n += s['n']
    print("-" * 80)
    print(f"{'TOTAL':<15} {total_n:>4}")


if __name__ == "__main__":
    print("Generating all cohorts...")
    cohorts, mega = generate_all_cohorts()
    print(f"\nGenerated {mega.n_patients} total patients across {len(cohorts)} trials.\n")
    print_cohort_summary(cohorts)

    # Validate a sample patient
    sample = mega.patients[0]
    print(f"\nSample patient: {sample.patient_id}")
    print(f"  Age: {sample.age}, Sex: {sample.sex}, Weight: {sample.weight_kg} kg")
    print(f"  Disease: {sample.disease_subtype}, Stage: {sample.disease_stage}")
    print(f"  CRS: grade {sample.crs.max_grade}, onset day {sample.crs.onset_day}")
    print(f"  ICANS: grade {sample.icans.max_grade}")
    print(f"  Vitals timepoints: {len(sample.vitals_timeseries)}")
    print(f"  Lab panels: {len(sample.labs_timeseries)}")
    print(f"  Cytokine panels: {len(sample.cytokine_timeseries)}")
    print(f"  ICE scores: {len(sample.ice_scores)}")
