"""
Edge case patient generator for CAR-T cell therapy safety prediction.

Generates 45 carefully constructed edge-case patients:
  - 20 patients with extreme but physiologically plausible values
  - 10 patients with significant missing data (50%+ labs missing)
  - 5 patients with late-onset CRS (Day 14+)
  - 5 patients with concurrent CRS + ICANS
  - 5 patients who develop IEC-HS / HLH from CRS

All patients use fixed seeds for reproducibility and are biologically
plausible even at extremes.
"""

from __future__ import annotations

import copy
import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from data.trial_configs import ALL_TRIALS, ZUMA1, JULIET, KARMMA, CARTITUDE1, TRANSCEND
from data.synthetic_cohorts import (
    BaselineLabs,
    CARTDose,
    CohortData,
    Comorbidities,
    CRSOutcome,
    CytokinePanel,
    ICANSOutcome,
    IECHSOutcome,
    LabPanel,
    PatientRecord,
    VitalSigns,
    _clamp,
    _dubois_bsa,
    _generate_vitals_timeseries,
    _generate_labs_timeseries,
    _generate_cytokine_timeseries,
    _generate_ice_scores,
    _round2,
)


EDGE_SEED = 99000


def _make_base_patient(rng: np.random.Generator, idx: int, tag: str) -> PatientRecord:
    """Create a base patient record with reasonable defaults."""
    p = PatientRecord()
    p.patient_id = f"EDGE-{tag}-{idx:04d}"
    p.trial_name = "EDGE-CASES"
    p.cohort_index = idx
    p.is_edge_case = True
    p.edge_case_type = tag
    p.age = 60
    p.sex = "M"
    p.weight_kg = 80.0
    p.height_cm = 175.0
    p.bsa_m2 = round(_dubois_bsa(80.0, 175.0), 2)
    p.disease_type = "NHL"
    p.disease_subtype = "DLBCL"
    p.disease_stage = "IV"
    p.tumor_burden_spd = 35.0
    p.prior_lines = 3
    p.comorbidities = Comorbidities()
    p.lymphodepletion = "Flu 30mg/m2 x3d + Cy 500mg/m2 x3d"
    p.cart_dose = CARTDose(
        product_name="axicabtagene ciloleucel",
        trade_name="Yescarta",
        target="CD19",
        costimulatory_domain="CD28",
        dose_value=2e6,
        dose_unit="cells/kg",
        cd4_cd8_ratio=1.0,
        viability_pct=93.0,
    )
    p.baseline_labs = BaselineLabs(
        WBC=4.0, ANC=2.5, ALC=0.5, Hemoglobin=11.0, Platelets=150.0,
        Creatinine=0.9, BUN=14.0, AST=25.0, ALT=22.0, LDH=280.0,
        Albumin=3.8, CRP=8.0, Ferritin=400.0, Fibrinogen=300.0, D_dimer=0.3,
    )
    p.crs = CRSOutcome()
    p.icans = ICANSOutcome()
    p.iec_hs = IECHSOutcome()
    return p


# ============================================================================
# 1. Extreme-value patients (20)
# ============================================================================

def _generate_extreme_patients(rng: np.random.Generator) -> List[PatientRecord]:
    """
    20 patients with extreme but physiologically plausible values.
    Each one pushes different parameters to realistic limits.
    """
    patients = []
    idx = 0

    # --- 1. Very elderly, low weight ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.age = 86
    p.sex = "F"
    p.weight_kg = 42.0
    p.height_cm = 152.0
    p.bsa_m2 = round(_dubois_bsa(42.0, 152.0), 2)
    p.comorbidities = Comorbidities(cardiovascular=True, pulmonary=True, renal=True)
    p.baseline_labs.Creatinine = 2.1
    p.baseline_labs.Hemoglobin = 7.2
    p.baseline_labs.Platelets = 35.0
    p.baseline_labs.Albumin = 2.1
    p.crs = CRSOutcome(occurred=True, max_grade=2, onset_day=3.0, peak_day=5.0,
                         resolution_day=10.0)
    patients.append(p)

    # --- 2. Morbidly obese ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.age = 45
    p.sex = "M"
    p.weight_kg = 155.0
    p.height_cm = 180.0
    p.bsa_m2 = round(_dubois_bsa(155.0, 180.0), 2)
    p.baseline_labs.LDH = 580.0
    p.tumor_burden_spd = 95.0
    p.crs = CRSOutcome(occurred=True, max_grade=4, onset_day=1.5, peak_day=3.0,
                         resolution_day=9.0, required_tocilizumab=True,
                         required_steroids=True, required_vasopressors=True)
    patients.append(p)

    # --- 3. Very young adult ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.age = 19
    p.sex = "M"
    p.weight_kg = 65.0
    p.height_cm = 178.0
    p.bsa_m2 = round(_dubois_bsa(65.0, 178.0), 2)
    p.tumor_burden_spd = 120.0  # very high burden
    p.baseline_labs.LDH = 1200.0
    p.baseline_labs.Ferritin = 2500.0
    p.crs = CRSOutcome(occurred=True, max_grade=4, onset_day=1.0, peak_day=2.5,
                         resolution_day=8.0, required_tocilizumab=True,
                         required_steroids=True, required_vasopressors=True)
    p.icans = ICANSOutcome(occurred=True, max_grade=4, onset_day=3.0, peak_day=4.5,
                            resolution_day=10.0, ice_score_nadir=0)
    patients.append(p)

    # --- 4. Extremely high baseline LDH ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.baseline_labs.LDH = 1800.0
    p.baseline_labs.Ferritin = 2800.0
    p.baseline_labs.CRP = 65.0
    p.tumor_burden_spd = 110.0
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=1.5, peak_day=3.5,
                         resolution_day=8.0, required_tocilizumab=True)
    patients.append(p)

    # --- 5. Severe baseline pancytopenia ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.baseline_labs.WBC = 0.5
    p.baseline_labs.ANC = 0.1
    p.baseline_labs.ALC = 0.02
    p.baseline_labs.Hemoglobin = 6.5
    p.baseline_labs.Platelets = 12.0
    p.prior_lines = 8
    p.crs = CRSOutcome(occurred=True, max_grade=2, onset_day=4.0, peak_day=6.0,
                         resolution_day=11.0)
    patients.append(p)

    # --- 6. Extreme renal impairment ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.comorbidities = Comorbidities(renal=True)
    p.baseline_labs.Creatinine = 3.8
    p.baseline_labs.BUN = 55.0
    p.baseline_labs.Albumin = 2.5
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=2.0, peak_day=4.0,
                         resolution_day=10.0, required_tocilizumab=True,
                         required_steroids=True)
    patients.append(p)

    # --- 7. Extreme hepatic impairment ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.comorbidities = Comorbidities(hepatic=True)
    p.baseline_labs.AST = 180.0
    p.baseline_labs.ALT = 165.0
    p.baseline_labs.Albumin = 2.0
    p.baseline_labs.Fibrinogen = 160.0
    p.crs = CRSOutcome(occurred=True, max_grade=2, onset_day=3.0, peak_day=5.0,
                         resolution_day=9.0)
    patients.append(p)

    # --- 8. Hyperfibrinogenemia at baseline ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.baseline_labs.Fibrinogen = 580.0
    p.baseline_labs.CRP = 75.0
    p.baseline_labs.Ferritin = 2200.0
    p.baseline_labs.D_dimer = 4.5
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=2.0, peak_day=4.0,
                         resolution_day=9.0, required_tocilizumab=True)
    patients.append(p)

    # --- 9. No CRS despite high risk factors ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.tumor_burden_spd = 90.0
    p.baseline_labs.LDH = 900.0
    p.baseline_labs.Ferritin = 2000.0
    p.crs = CRSOutcome(occurred=False)  # did NOT develop CRS
    p.icans = ICANSOutcome(occurred=False)
    patients.append(p)

    # --- 10. CRS grade 1 only despite massive burden ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.tumor_burden_spd = 130.0
    p.baseline_labs.LDH = 1500.0
    p.crs = CRSOutcome(occurred=True, max_grade=1, onset_day=2.0, peak_day=3.0,
                         resolution_day=5.0)
    patients.append(p)

    # --- 11. Very low CD4:CD8 ratio ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.cart_dose.cd4_cd8_ratio = 0.12
    p.cart_dose.viability_pct = 72.0
    p.crs = CRSOutcome(occurred=True, max_grade=1, onset_day=5.0, peak_day=6.5,
                         resolution_day=9.0)
    patients.append(p)

    # --- 12. Very high CD4:CD8 ratio ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.cart_dose.cd4_cd8_ratio = 4.8
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=1.0, peak_day=2.5,
                         resolution_day=7.0, required_tocilizumab=True)
    patients.append(p)

    # --- 13. MM patient with extreme paraprotein ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.disease_type = "MM"
    p.disease_subtype = "Multiple Myeloma"
    p.disease_stage = "ISS-III"
    p.tumor_burden_spd = 0.0
    p.paraprotein_burden = 11.5
    p.prior_lines = 9
    p.cart_dose = CARTDose(
        product_name="idecabtagene vicleucel", trade_name="Abecma",
        target="BCMA", costimulatory_domain="4-1BB",
        dose_value=450e6, dose_unit="total_cells",
        cd4_cd8_ratio=0.8, viability_pct=88.0,
    )
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=1.0, peak_day=2.0,
                         resolution_day=6.0, required_tocilizumab=True)
    patients.append(p)

    # --- 14. Patient with all comorbidities ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.age = 74
    p.comorbidities = Comorbidities(cardiovascular=True, pulmonary=True,
                                     renal=True, hepatic=True)
    p.baseline_labs.Creatinine = 2.5
    p.baseline_labs.AST = 95.0
    p.baseline_labs.ALT = 88.0
    p.baseline_labs.Hemoglobin = 8.0
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=2.0, peak_day=4.0,
                         resolution_day=11.0, required_tocilizumab=True,
                         required_steroids=True)
    patients.append(p)

    # --- 15. Extreme baseline ferritin (pre-existing iron overload) ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.baseline_labs.Ferritin = 2900.0
    p.prior_lines = 7
    p.crs = CRSOutcome(occurred=True, max_grade=2, onset_day=2.5, peak_day=4.0,
                         resolution_day=8.0)
    patients.append(p)

    # --- 16. Extremely low platelets + high D-dimer (DIC-like baseline) ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.baseline_labs.Platelets = 18.0
    p.baseline_labs.D_dimer = 4.8
    p.baseline_labs.Fibrinogen = 170.0
    p.crs = CRSOutcome(occurred=True, max_grade=2, onset_day=3.0, peak_day=5.0,
                         resolution_day=9.0)
    patients.append(p)

    # --- 17. Biphasic CRS (resolves, then recurs) ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    # Model as two separate events; first is mild, second is more severe
    p.crs = CRSOutcome(occurred=True, max_grade=3, onset_day=2.0, peak_day=3.5,
                         resolution_day=12.0, required_tocilizumab=True)
    # The longer resolution time encodes the biphasic nature
    patients.append(p)

    # --- 18. ICANS without CRS ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.crs = CRSOutcome(occurred=False)
    p.icans = ICANSOutcome(occurred=True, max_grade=3, onset_day=5.0, peak_day=7.0,
                            resolution_day=12.0, ice_score_nadir=2)
    patients.append(p)

    # --- 19. Ultra-rapid CRS onset (within hours) ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.crs = CRSOutcome(occurred=True, max_grade=4, onset_day=0.3, peak_day=1.0,
                         resolution_day=5.0, required_tocilizumab=True,
                         required_steroids=True, required_vasopressors=True)
    patients.append(p)

    # --- 20. FL patient with no toxicity at all ---
    p = _make_base_patient(rng, idx, "EXTREME"); idx += 1
    p.disease_subtype = "FL"
    p.tumor_burden_spd = 8.0
    p.baseline_labs.LDH = 180.0
    p.baseline_labs.Ferritin = 120.0
    p.baseline_labs.CRP = 2.0
    p.cart_dose.costimulatory_domain = "4-1BB"
    p.cart_dose.product_name = "tisagenlecleucel"
    p.cart_dose.trade_name = "Kymriah"
    p.crs = CRSOutcome(occurred=False)
    p.icans = ICANSOutcome(occurred=False)
    patients.append(p)

    return patients


# ============================================================================
# 2. Missing data patients (10)
# ============================================================================

def _generate_missing_data_patients(rng: np.random.Generator) -> List[PatientRecord]:
    """
    10 patients with significant missing data (50%+ labs missing).
    Simulates real-world scenarios: transport issues, weekends, equipment failure.
    """
    patients = []
    base_idx = 100

    missing_patterns = [
        "weekend_gaps",         # No weekend labs
        "cytokine_unavail",     # No cytokine data at all
        "sporadic_labs",        # Random 60% missing
        "early_discharge",      # No data after Day 10
        "late_admission",       # No data before Day 3
        "equipment_failure",    # No data Days 5-10
        "transfer_gap",         # No data Days 3-7 (transferred)
        "cbc_only",             # Only CBC, no CMP or inflammatory
        "vitals_only",          # Vitals present, all labs missing >50%
        "catastrophic_missing", # 80% of all data missing
    ]

    for i, pattern in enumerate(missing_patterns):
        p = _make_base_patient(rng, base_idx + i, "MISSING")
        p.has_missing_data = True
        p.edge_case_type = f"MISSING-{pattern}"

        # Assign a mild CRS to most
        if i < 7:
            p.crs = CRSOutcome(occurred=True, max_grade=rng.choice([1, 2]),
                                onset_day=rng.uniform(2, 6),
                                peak_day=rng.uniform(4, 8),
                                resolution_day=rng.uniform(7, 14))
        patients.append(p)

    return patients


def _apply_missing_data(patient: PatientRecord, rng: np.random.Generator) -> None:
    """
    Apply missingness patterns to a patient's time-series data.
    Modifies labs_timeseries and cytokine_timeseries in place.
    """
    pattern = patient.edge_case_type.replace("MISSING-", "")

    lab_fields = ["WBC", "ANC", "ALC", "Hemoglobin", "Platelets",
                  "Creatinine", "BUN", "AST", "ALT", "LDH", "Albumin",
                  "CRP", "Ferritin", "Fibrinogen", "D_dimer", "Triglycerides"]
    cyto_fields = ["IL6", "IFN_gamma", "TNF_alpha", "IL10", "MCP1", "IL1RA", "sgp130"]

    if pattern == "weekend_gaps":
        # Null out labs on days that fall on "weekends" (days 6,7,13,14,20,21,27,28)
        weekend_hours = set()
        for d in [6, 7, 13, 14, 20, 21, 27, 28]:
            weekend_hours.add(d * 24.0)
        for panel in patient.labs_timeseries:
            if panel.time_hours in weekend_hours:
                for fld in lab_fields:
                    setattr(panel, fld, None)

    elif pattern == "cytokine_unavail":
        # All cytokine values set to None
        for panel in patient.cytokine_timeseries:
            for fld in cyto_fields:
                setattr(panel, fld, None)

    elif pattern == "sporadic_labs":
        # Random 60% of lab measurements missing
        for panel in patient.labs_timeseries:
            for fld in lab_fields:
                if rng.random() < 0.60:
                    setattr(panel, fld, None)
        for panel in patient.cytokine_timeseries:
            for fld in cyto_fields:
                if rng.random() < 0.60:
                    setattr(panel, fld, None)

    elif pattern == "early_discharge":
        # No data after Day 10 (hour 240)
        patient.labs_timeseries = [p for p in patient.labs_timeseries if p.time_hours <= 240]
        patient.cytokine_timeseries = [p for p in patient.cytokine_timeseries if p.time_hours <= 240]
        patient.vitals_timeseries = [v for v in patient.vitals_timeseries if v.time_hours <= 240]

    elif pattern == "late_admission":
        # No data before Day 3 (hour 72), except baseline
        patient.labs_timeseries = [p for p in patient.labs_timeseries
                                    if p.time_hours < -120 or p.time_hours >= 72]
        patient.cytokine_timeseries = [p for p in patient.cytokine_timeseries
                                        if p.time_hours >= 72]
        patient.vitals_timeseries = [v for v in patient.vitals_timeseries
                                      if v.time_hours < -120 or v.time_hours >= 72]

    elif pattern == "equipment_failure":
        # No lab/cytokine data Days 5-10 (hours 120-240)
        for panel in patient.labs_timeseries:
            if 120 <= panel.time_hours <= 240:
                for fld in lab_fields:
                    setattr(panel, fld, None)
        for panel in patient.cytokine_timeseries:
            if 120 <= panel.time_hours <= 240:
                for fld in cyto_fields:
                    setattr(panel, fld, None)

    elif pattern == "transfer_gap":
        # No data Days 3-7 (hours 72-168)
        patient.labs_timeseries = [p for p in patient.labs_timeseries
                                    if p.time_hours < 72 or p.time_hours > 168]
        patient.cytokine_timeseries = [p for p in patient.cytokine_timeseries
                                        if p.time_hours < 72 or p.time_hours > 168]
        patient.vitals_timeseries = [v for v in patient.vitals_timeseries
                                      if v.time_hours < 72 or v.time_hours > 168]

    elif pattern == "cbc_only":
        # Only CBC available, null out CMP and inflammatory
        cmp_fields = ["Creatinine", "BUN", "AST", "ALT", "LDH", "Albumin"]
        inflam_fields = ["CRP", "Ferritin", "Fibrinogen", "D_dimer", "Triglycerides"]
        for panel in patient.labs_timeseries:
            for fld in cmp_fields + inflam_fields:
                setattr(panel, fld, None)
        # Also null out all cytokines
        for panel in patient.cytokine_timeseries:
            for fld in cyto_fields:
                setattr(panel, fld, None)

    elif pattern == "vitals_only":
        # Vitals present, >50% labs missing
        for panel in patient.labs_timeseries:
            for fld in lab_fields:
                if rng.random() < 0.65:
                    setattr(panel, fld, None)
        for panel in patient.cytokine_timeseries:
            for fld in cyto_fields:
                if rng.random() < 0.75:
                    setattr(panel, fld, None)

    elif pattern == "catastrophic_missing":
        # 80% of everything missing
        for panel in patient.labs_timeseries:
            for fld in lab_fields:
                if rng.random() < 0.80:
                    setattr(panel, fld, None)
        for panel in patient.cytokine_timeseries:
            for fld in cyto_fields:
                if rng.random() < 0.80:
                    setattr(panel, fld, None)
        # Also thin out vitals
        keep_indices = sorted(rng.choice(
            len(patient.vitals_timeseries),
            size=max(5, len(patient.vitals_timeseries) // 5),
            replace=False
        ))
        patient.vitals_timeseries = [patient.vitals_timeseries[i] for i in keep_indices]


# ============================================================================
# 3. Late-onset CRS patients (5)
# ============================================================================

def _generate_late_onset_crs_patients(rng: np.random.Generator) -> List[PatientRecord]:
    """
    5 patients with late-onset CRS (Day 14+).
    These are rare but documented, often seen with 4-1BB constructs
    or delayed CAR-T expansion.
    """
    patients = []
    base_idx = 200

    late_configs = [
        # (onset_day, max_grade, product_costim, notes)
        (14.0, 2, "4-1BB", "delayed_expansion"),
        (16.0, 1, "4-1BB", "smoldering_onset"),
        (18.0, 3, "4-1BB", "late_severe"),
        (21.0, 2, "4-1BB", "very_late"),
        (15.0, 1, "CD28", "unusual_cd28_late"),  # rare for CD28
    ]

    for i, (onset, grade, costim, note) in enumerate(late_configs):
        p = _make_base_patient(rng, base_idx + i, "LATE-CRS")
        p.edge_case_type = f"LATE-CRS-{note}"

        # Late CRS often in patients with lower initial burden
        p.tumor_burden_spd = rng.uniform(10, 30)
        p.baseline_labs.LDH = rng.uniform(180, 300)
        p.cart_dose.costimulatory_domain = costim

        if costim == "4-1BB":
            p.cart_dose.product_name = "tisagenlecleucel"
            p.cart_dose.trade_name = "Kymriah"

        peak_day = onset + rng.uniform(1.0, 3.0)
        resolution_day = peak_day + rng.uniform(2.0, 6.0)

        p.crs = CRSOutcome(
            occurred=True,
            max_grade=grade,
            onset_day=onset,
            peak_day=round(peak_day, 1),
            resolution_day=round(min(resolution_day, 28.0), 1),
            required_tocilizumab=grade >= 2,
        )

        patients.append(p)

    return patients


# ============================================================================
# 4. Concurrent CRS + ICANS patients (5)
# ============================================================================

def _generate_concurrent_crs_icans_patients(rng: np.random.Generator) -> List[PatientRecord]:
    """
    5 patients with concurrent CRS and ICANS (overlapping timeframes).
    ICANS onset occurs within 12h of CRS onset rather than the typical 24-48h delay.
    """
    patients = []
    base_idx = 300

    concurrent_configs = [
        # (crs_onset, crs_grade, icans_grade, ice_nadir)
        (2.0, 3, 3, 2),
        (1.5, 4, 4, 0),
        (3.0, 3, 2, 4),
        (2.5, 2, 3, 1),
        (1.0, 4, 3, 1),
    ]

    for i, (crs_onset, crs_g, icans_g, ice_nadir) in enumerate(concurrent_configs):
        p = _make_base_patient(rng, base_idx + i, "CONCURRENT")
        p.edge_case_type = "CONCURRENT-CRS-ICANS"

        # High burden patients
        p.tumor_burden_spd = rng.uniform(50, 120)
        p.baseline_labs.LDH = rng.uniform(400, 1000)
        p.baseline_labs.Ferritin = rng.uniform(800, 2500)

        crs_peak = crs_onset + rng.uniform(1.0, 2.5)
        crs_resolve = crs_peak + rng.uniform(3.0, 7.0)

        p.crs = CRSOutcome(
            occurred=True,
            max_grade=crs_g,
            onset_day=crs_onset,
            peak_day=round(crs_peak, 1),
            resolution_day=round(crs_resolve, 1),
            required_tocilizumab=True,
            required_steroids=crs_g >= 3,
            required_vasopressors=crs_g == 4,
        )

        # ICANS onset within 0-12h of CRS onset (concurrent)
        icans_onset = crs_onset + rng.uniform(0.0, 0.5)  # same day
        icans_peak = icans_onset + rng.uniform(0.5, 2.0)
        icans_resolve = icans_peak + rng.uniform(3.0, 8.0)

        p.icans = ICANSOutcome(
            occurred=True,
            max_grade=icans_g,
            onset_day=round(icans_onset, 1),
            peak_day=round(icans_peak, 1),
            resolution_day=round(icans_resolve, 1),
            ice_score_nadir=ice_nadir,
        )

        patients.append(p)

    return patients


# ============================================================================
# 5. IEC-HS / HLH patients (5)
# ============================================================================

def _generate_iec_hs_patients(rng: np.random.Generator) -> List[PatientRecord]:
    """
    5 patients who develop IEC-HS (immune effector cell-associated
    hemophagocytic lymphohistiocytosis-like syndrome) from severe CRS.

    Diagnostic criteria:
    - Ferritin > 10,000 ng/mL
    - Fibrinogen < 150 mg/dL
    - Triglycerides > 265 mg/dL
    - Plus: cytopenias, hepatitis, coagulopathy
    """
    patients = []
    base_idx = 400

    hs_configs = [
        # (crs_onset, crs_grade, peak_ferritin, nadir_fib, peak_tg)
        (2.0, 4, 45000.0, 65.0, 420.0),
        (1.5, 3, 18000.0, 110.0, 310.0),
        (3.0, 4, 72000.0, 45.0, 550.0),
        (2.0, 3, 25000.0, 95.0, 350.0),
        (1.0, 4, 55000.0, 55.0, 480.0),
    ]

    for i, (crs_onset, crs_g, pk_fer, nad_fib, pk_tg) in enumerate(hs_configs):
        p = _make_base_patient(rng, base_idx + i, "IEC-HS")
        p.edge_case_type = "IEC-HS-HLH"

        # High-risk profile
        p.tumor_burden_spd = rng.uniform(60, 130)
        p.baseline_labs.LDH = rng.uniform(500, 1200)
        p.baseline_labs.Ferritin = rng.uniform(1000, 3000)
        p.baseline_labs.CRP = rng.uniform(20, 60)

        crs_peak = crs_onset + rng.uniform(1.5, 3.0)
        crs_resolve = crs_peak + rng.uniform(5.0, 10.0)

        p.crs = CRSOutcome(
            occurred=True,
            max_grade=crs_g,
            onset_day=crs_onset,
            peak_day=round(crs_peak, 1),
            resolution_day=round(crs_resolve, 1),
            required_tocilizumab=True,
            required_steroids=True,
            required_vasopressors=crs_g == 4,
        )

        # IEC-HS develops 1-3 days after CRS peak
        hs_onset = crs_peak + rng.uniform(1.0, 3.0)
        p.iec_hs = IECHSOutcome(
            occurred=True,
            onset_day=round(hs_onset, 1),
            peak_ferritin=pk_fer,
            nadir_fibrinogen=nad_fib,
            peak_triglycerides=pk_tg,
        )

        # ICANS also often present in IEC-HS patients
        p.icans = ICANSOutcome(
            occurred=True,
            max_grade=rng.choice([2, 3, 4]),
            onset_day=round(crs_onset + rng.uniform(1.0, 2.0), 1),
            peak_day=round(crs_peak + rng.uniform(0.5, 2.0), 1),
            resolution_day=round(crs_resolve + rng.uniform(0, 3.0), 1),
            ice_score_nadir=rng.integers(0, 4),
        )

        patients.append(p)

    return patients


# ============================================================================
# Main edge case generator
# ============================================================================

def generate_edge_cases() -> CohortData:
    """
    Generate all 45 edge-case patients with complete time-series data.

    Returns:
        CohortData with 45 edge-case patients:
          - 20 extreme-value patients
          - 10 missing-data patients
          - 5 late-onset CRS patients
          - 5 concurrent CRS+ICANS patients
          - 5 IEC-HS/HLH patients
    """
    rng = np.random.default_rng(EDGE_SEED)

    # Generate all patient groups
    extreme_patients = _generate_extreme_patients(rng)
    missing_patients = _generate_missing_data_patients(rng)
    late_crs_patients = _generate_late_onset_crs_patients(rng)
    concurrent_patients = _generate_concurrent_crs_icans_patients(rng)
    iec_hs_patients = _generate_iec_hs_patients(rng)

    all_edge = (
        extreme_patients
        + missing_patients
        + late_crs_patients
        + concurrent_patients
        + iec_hs_patients
    )

    # Use ZUMA-1 config as reference for time-series generation
    ref_cfg = ZUMA1

    # Generate time-series for all edge case patients
    for patient in all_edge:
        # Create a per-patient rng for time-series reproducibility
        patient_seed = EDGE_SEED + hash(patient.patient_id) % 100000
        ts_rng = np.random.default_rng(abs(patient_seed))

        patient.vitals_timeseries = _generate_vitals_timeseries(ts_rng, patient, ref_cfg)
        patient.labs_timeseries = _generate_labs_timeseries(ts_rng, patient, ref_cfg)
        patient.cytokine_timeseries = _generate_cytokine_timeseries(ts_rng, patient, ref_cfg)
        patient.ice_scores = _generate_ice_scores(ts_rng, patient)

    # Apply missingness patterns AFTER generating base time-series
    missing_rng = np.random.default_rng(EDGE_SEED + 5000)
    for patient in missing_patients:
        _apply_missing_data(patient, missing_rng)

    # Re-index
    for i, patient in enumerate(all_edge):
        patient.cohort_index = i

    cohort = CohortData(
        trial_name="EDGE-CASES",
        config=ref_cfg,  # reference only
        patients=all_edge,
    )

    return cohort


def print_edge_case_summary(cohort: CohortData) -> None:
    """Print a summary of edge case patients."""
    print(f"Edge case cohort: {cohort.n_patients} patients\n")

    # Group by type
    type_counts: Dict[str, int] = {}
    for p in cohort.patients:
        base_type = p.edge_case_type.split("-")[0] if "-" in p.edge_case_type else p.edge_case_type
        type_counts[base_type] = type_counts.get(base_type, 0) + 1

    print(f"{'Type':<25} {'Count':>6}")
    print("-" * 35)
    for t, c in sorted(type_counts.items()):
        print(f"{t:<25} {c:>6}")

    print(f"\n{'Patient ID':<22} {'Type':<28} {'CRS':>4} {'ICANS':>6} {'HLH':>4} {'Missing':>8}")
    print("-" * 80)
    for p in cohort.patients:
        print(f"{p.patient_id:<22} {p.edge_case_type:<28} "
              f"{'G' + str(p.crs.max_grade) if p.crs.occurred else '-':>4} "
              f"{'G' + str(p.icans.max_grade) if p.icans.occurred else '-':>6} "
              f"{'Yes' if p.iec_hs.occurred else '-':>4} "
              f"{'Yes' if p.has_missing_data else '-':>8}")


if __name__ == "__main__":
    print("Generating edge cases...")
    edge_cohort = generate_edge_cases()
    print_edge_case_summary(edge_cohort)

    # Validate time-series lengths
    for p in edge_cohort.patients:
        assert len(p.vitals_timeseries) > 0, f"{p.patient_id}: no vitals"
        assert len(p.ice_scores) > 0, f"{p.patient_id}: no ICE scores"
        if not p.has_missing_data:
            assert len(p.labs_timeseries) > 0, f"{p.patient_id}: no labs"
            assert len(p.cytokine_timeseries) > 0, f"{p.patient_id}: no cytokines"

    print("\nAll edge case validations passed.")
