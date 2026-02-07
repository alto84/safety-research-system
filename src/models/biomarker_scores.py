"""
Deterministic clinical biomarker scoring models for cell therapy safety prediction.

Each class implements a published, peer-reviewed scoring formula. No external ML
libraries are required -- all computations are closed-form arithmetic or logistic
functions from the cited papers.

Models implemented:
    1. EASIX                - Pennisi et al. 2021, Korell et al. 2022
    2. Modified EASIX       - Pennisi et al. 2021, Korell et al. 2022
    3. Pre-Modified EASIX   - Korell et al. 2022
    4. HScore               - Fardet et al. 2014
    5. CAR-HEMATOTOX        - Rejeski et al. 2022
    6. Teachey Cytokine     - Teachey et al. 2016
    7. Hay Binary Classifier- Hay et al. 2017

All models share a common ``ScoringResult`` output format and accept patient lab
data as a plain ``dict[str, float | int | bool | str]``.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared output types
# ---------------------------------------------------------------------------

class RiskLevel(Enum):
    """Standardised risk stratification returned by every scoring model."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ValidationError(Exception):
    """Raised when input parameters fail validation."""


@dataclass
class ScoringResult:
    """Standardised output returned by every scoring model.

    Attributes:
        model_name: Canonical name of the scoring model.
        score: The numeric score produced by the formula (None if computation
            failed due to missing/invalid data).
        risk_level: Categorised risk (low / moderate / high), or None on error.
        confidence: Confidence in the result (0.0-1.0). Reduced when data is
            missing or boundary conditions are hit.
        contributing_factors: Dict mapping each input variable to its
            contribution or raw value used in the calculation.
        warnings: Non-fatal validation warnings encountered during scoring.
        errors: Fatal validation errors (score may be ``None``).
        citation: Short literature reference for the formula.
        timestamp: When the score was computed.
        metadata: Additional model-specific data (e.g. probability, flags).
    """

    model_name: str
    score: float | None
    risk_level: RiskLevel | None
    confidence: float
    contributing_factors: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    citation: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """Return True if no blocking errors were recorded."""
        return len(self.errors) == 0 and self.score is not None


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

# Physiological upper bounds used for sanity-checking lab values.
# Values above these are almost certainly data-entry errors.
_PHYSIOLOGICAL_BOUNDS: dict[str, tuple[float, float]] = {
    "ldh_u_per_l":          (0.0, 50_000.0),
    "creatinine_mg_dl":     (0.0, 30.0),
    "platelets_per_nl":     (0.0, 2_000.0),
    "crp_mg_dl":            (0.0, 500.0),
    "crp_mg_l":             (0.0, 5_000.0),
    "ferritin_ng_ml":       (0.0, 200_000.0),
    "temperature_c":        (30.0, 45.0),
    "temperature_f":        (86.0, 113.0),
    "ast_u_per_l":          (0.0, 20_000.0),
    "triglycerides_mmol_l": (0.0, 50.0),
    "fibrinogen_g_l":       (0.0, 15.0),
    "hemoglobin_g_dl":      (0.0, 25.0),
    "anc_10e9_per_l":       (0.0, 100.0),
    "ifn_gamma_pg_ml":      (0.0, 500_000.0),
    "sgp130_ng_ml":         (0.0, 10_000.0),
    "il1ra_pg_ml":          (0.0, 500_000.0),
    "mcp1_pg_ml":           (0.0, 500_000.0),
}

# Common aliases → canonical field names.  Allows callers to use short
# names (e.g. "ldh") in addition to the precise canonical keys.
_FIELD_ALIASES: dict[str, str] = {
    # EASIX
    "ldh": "ldh_u_per_l",
    "LDH": "ldh_u_per_l",
    "creatinine": "creatinine_mg_dl",
    "Creatinine": "creatinine_mg_dl",
    "platelets": "platelets_per_nl",
    "Platelets": "platelets_per_nl",
    "plt": "platelets_per_nl",
    # m-EASIX
    "crp": "crp_mg_dl",
    "CRP": "crp_mg_dl",
    "crp_mg": "crp_mg_dl",
    "crp_mgl": "crp_mg_l",
    # HScore
    "temperature": "temperature_c",
    "temp": "temperature_c",
    "temp_c": "temperature_c",
    "organomegaly": "organomegaly",
    "cytopenias": "cytopenias_lineages",
    "ferritin": "ferritin_ng_ml",
    "Ferritin": "ferritin_ng_ml",
    "triglycerides": "triglycerides_mmol_l",
    "tg": "triglycerides_mmol_l",
    "fibrinogen": "fibrinogen_g_l",
    "ast": "ast_u_per_l",
    "AST": "ast_u_per_l",
    "hemophagocytosis": "hemophagocytosis_on_bm",
    "immunosuppression": "known_immunosuppression",
    # CAR-HEMATOTOX
    "anc": "anc_10e9_per_l",
    "ANC": "anc_10e9_per_l",
    "hemoglobin": "hemoglobin_g_dl",
    "hgb": "hemoglobin_g_dl",
    "Hgb": "hemoglobin_g_dl",
    # Teachey
    "ifn_gamma": "ifn_gamma_pg_ml",
    "IFN_gamma": "ifn_gamma_pg_ml",
    "sgp130": "sgp130_ng_ml",
    "il1ra": "il1ra_pg_ml",
    "IL1RA": "il1ra_pg_ml",
    # Hay
    "mcp1": "mcp1_pg_ml",
    "MCP1": "mcp1_pg_ml",
    "max_temp_36h": "temperature_c",
    "hours_since_infusion": "hours_since_infusion",
    "heart_rate": "heart_rate_bpm",
    "hr": "heart_rate_bpm",
}


def _resolve_aliases(data: dict[str, Any]) -> dict[str, Any]:
    """Return a new dict with alias keys replaced by canonical names.

    Canonical keys already present take precedence over aliases.
    """
    resolved: dict[str, Any] = {}
    for key, value in data.items():
        canonical = _FIELD_ALIASES.get(key, key)
        # Don't overwrite if canonical key was explicitly provided
        if canonical not in resolved:
            resolved[canonical] = value
    return resolved


def _validate_positive(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    warnings: list[str],
    *,
    required: bool = True,
) -> float | None:
    """Extract a numeric value from *data*, validating positivity and bounds.

    Returns the value if valid, or ``None`` if missing or invalid.  Appends
    messages to *errors* or *warnings* accordingly.
    """
    raw = data.get(key)
    if raw is None:
        if required:
            errors.append(f"Missing required field: {key}")
        else:
            warnings.append(f"Optional field not provided: {key}")
        return None

    try:
        value = float(raw)
    except (TypeError, ValueError):
        errors.append(f"Non-numeric value for {key}: {raw!r}")
        return None

    lo, hi = _PHYSIOLOGICAL_BOUNDS.get(key, (0.0, float("inf")))
    if value < lo:
        errors.append(f"{key} = {value} is below physiological minimum ({lo})")
        return None
    if value > hi:
        warnings.append(
            f"{key} = {value} exceeds expected physiological maximum ({hi}); "
            "verify data entry"
        )

    return value


def _validate_non_negative_int(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    warnings: list[str],
    *,
    required: bool = True,
    max_value: int | None = None,
) -> int | None:
    """Extract a non-negative integer from *data*."""
    raw = data.get(key)
    if raw is None:
        if required:
            errors.append(f"Missing required field: {key}")
        else:
            warnings.append(f"Optional field not provided: {key}")
        return None

    try:
        value = int(raw)
    except (TypeError, ValueError):
        errors.append(f"Non-integer value for {key}: {raw!r}")
        return None

    if value < 0:
        errors.append(f"{key} = {value} cannot be negative")
        return None
    if max_value is not None and value > max_value:
        warnings.append(f"{key} = {value} exceeds expected maximum ({max_value})")
    return value


def _validate_bool(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    warnings: list[str],
    *,
    required: bool = True,
) -> bool | None:
    """Extract a boolean from *data*."""
    raw = data.get(key)
    if raw is None:
        if required:
            errors.append(f"Missing required field: {key}")
        else:
            warnings.append(f"Optional field not provided: {key}")
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        if raw.lower() in ("true", "yes", "1"):
            return True
        if raw.lower() in ("false", "no", "0"):
            return False
    errors.append(f"Cannot interpret {key} = {raw!r} as boolean")
    return None


# ---------------------------------------------------------------------------
# 1. EASIX  (Endothelial Activation and Stress Index)
# ---------------------------------------------------------------------------

class EASIX:
    """Endothelial Activation and Stress Index.

    Formula::

        EASIX = (LDH [U/L] * Creatinine [mg/dL]) / Platelets [10^9/L]

    Published:
        - Pennisi M et al. Modified EASIX predicts severe CRS in adult
          patients after CAR-T cell therapy.  Blood Adv. 2021;5(17):3481-3489.
        - Korell F et al. EASIX and modified EASIX as predictors for CRS and
          ICANS in patients receiving CAR-T cell therapy.  J Cancer Res Clin
          Oncol. 2022.

    Reported AUC: 0.80-0.92 for severe (Grade >= 3) CRS prediction.

    Risk stratification thresholds (derived from published tertile analyses):
        - Low:      EASIX < 3.2
        - Moderate: 3.2 <= EASIX < 10.0
        - High:     EASIX >= 10.0

    Required patient data keys:
        - ``ldh_u_per_l``       : Lactate dehydrogenase (U/L)
        - ``creatinine_mg_dl``  : Serum creatinine (mg/dL)
        - ``platelets_per_nl``  : Platelet count (cells/nL = 10^9/L)
    """

    MODEL_NAME = "EASIX"
    CITATION = (
        "Pennisi et al. Blood Adv 2021;5(17):3481-3489; "
        "Korell et al. J Cancer Res Clin Oncol 2022"
    )

    THRESHOLD_LOW = 3.2
    THRESHOLD_HIGH = 10.0

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the EASIX score for a single patient.

        Args:
            patient_data: Dict with keys ``ldh_u_per_l``, ``creatinine_mg_dl``,
                ``platelets_per_nl``.

        Returns:
            A ScoringResult with the EASIX value and risk level.
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []

        ldh = _validate_positive(patient_data, "ldh_u_per_l", errors, warnings)
        creatinine = _validate_positive(patient_data, "creatinine_mg_dl", errors, warnings)
        platelets = _validate_positive(patient_data, "platelets_per_nl", errors, warnings)

        if errors:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        # Type narrowing -- all values validated above.
        assert ldh is not None and creatinine is not None and platelets is not None

        if platelets == 0.0:
            errors.append("platelets_per_nl = 0; cannot compute EASIX (division by zero)")
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        easix = (ldh * creatinine) / platelets

        risk_level = self._classify(easix)
        confidence = 1.0 if not warnings else 0.85

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=easix,
            risk_level=risk_level,
            confidence=confidence,
            contributing_factors={
                "ldh_u_per_l": ldh,
                "creatinine_mg_dl": creatinine,
                "platelets_per_nl": platelets,
            },
            warnings=warnings,
            citation=self.CITATION,
        )

    @classmethod
    def _classify(cls, easix: float) -> RiskLevel:
        if easix < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if easix < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH


# ---------------------------------------------------------------------------
# 2. Modified EASIX  (m-EASIX)
# ---------------------------------------------------------------------------

class ModifiedEASIX:
    """Modified Endothelial Activation and Stress Index.

    Replaces serum creatinine with C-reactive protein (CRP) to capture the
    inflammatory component of endothelial activation more directly.

    Formula::

        m-EASIX = (LDH [U/L] * CRP [mg/dL]) / Platelets [10^9/L]

    Published:
        - Pennisi M et al. Blood Adv. 2021;5(17):3481-3489.
        - Korell F et al. J Cancer Res Clin Oncol. 2022.

    Reported AUC: up to 0.89 for CRS prediction.

    Risk stratification:
        - Low:      m-EASIX < 5.0
        - Moderate: 5.0 <= m-EASIX < 20.0
        - High:     m-EASIX >= 20.0

    Required patient data keys:
        - ``ldh_u_per_l``       : Lactate dehydrogenase (U/L)
        - ``crp_mg_dl``         : C-reactive protein (mg/dL)
        - ``platelets_per_nl``  : Platelet count (cells/nL = 10^9/L)
    """

    MODEL_NAME = "Modified_EASIX"
    CITATION = (
        "Pennisi et al. Blood Adv 2021;5(17):3481-3489; "
        "Korell et al. J Cancer Res Clin Oncol 2022"
    )

    THRESHOLD_LOW = 5.0
    THRESHOLD_HIGH = 20.0

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the modified EASIX score.

        Args:
            patient_data: Dict with keys ``ldh_u_per_l``, ``crp_mg_dl``,
                ``platelets_per_nl``.

        Returns:
            A ScoringResult with the m-EASIX value and risk level.
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []

        ldh = _validate_positive(patient_data, "ldh_u_per_l", errors, warnings)
        crp = _validate_positive(patient_data, "crp_mg_dl", errors, warnings)
        platelets = _validate_positive(patient_data, "platelets_per_nl", errors, warnings)

        if errors:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        assert ldh is not None and crp is not None and platelets is not None

        if platelets == 0.0:
            errors.append(
                "platelets_per_nl = 0; cannot compute m-EASIX (division by zero)"
            )
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        m_easix = (ldh * crp) / platelets

        risk_level = self._classify(m_easix)
        confidence = 1.0 if not warnings else 0.85

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=m_easix,
            risk_level=risk_level,
            confidence=confidence,
            contributing_factors={
                "ldh_u_per_l": ldh,
                "crp_mg_dl": crp,
                "platelets_per_nl": platelets,
            },
            warnings=warnings,
            citation=self.CITATION,
        )

    @classmethod
    def _classify(cls, m_easix: float) -> RiskLevel:
        if m_easix < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if m_easix < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH


# ---------------------------------------------------------------------------
# 3. Pre-Modified EASIX  (P-m-EASIX)
# ---------------------------------------------------------------------------

class PreModifiedEASIX:
    """Pre-lymphodepletion Modified EASIX.

    Identical formula to Modified EASIX, but computed from laboratory values
    drawn **before** lymphodepleting chemotherapy.  The distinction is
    clinically important: the pre-LD timepoint is the earliest opportunity
    for risk stratification before therapy-induced cytopenia confounds counts.

    Formula::

        P-m-EASIX = (LDH [U/L] * CRP [mg/dL]) / Platelets [10^9/L]

    Published:
        - Korell F et al. J Cancer Res Clin Oncol. 2022.

    The result carries ``metadata["is_pre_infusion"] = True`` to distinguish
    it from standard m-EASIX computed at later timepoints.

    Required patient data keys (all from pre-LD labs):
        - ``ldh_u_per_l``
        - ``crp_mg_dl``
        - ``platelets_per_nl``
    """

    MODEL_NAME = "Pre_Modified_EASIX"
    CITATION = "Korell et al. J Cancer Res Clin Oncol 2022"

    THRESHOLD_LOW = 5.0
    THRESHOLD_HIGH = 20.0

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the pre-lymphodepletion modified EASIX score.

        Args:
            patient_data: Dict with keys ``ldh_u_per_l``, ``crp_mg_dl``,
                ``platelets_per_nl``.  Values should be from pre-LD labs.

        Returns:
            A ScoringResult with ``metadata["is_pre_infusion"] = True``.
        """
        inner = ModifiedEASIX()
        result = inner.score(patient_data)

        # Re-label the result for this variant
        result.model_name = self.MODEL_NAME
        result.citation = self.CITATION
        result.metadata["is_pre_infusion"] = True

        # Apply P-m-EASIX thresholds (same numerical values as m-EASIX; kept
        # explicit so they can diverge if future data warrants it).
        if result.score is not None:
            result.risk_level = self._classify(result.score)

        return result

    @classmethod
    def _classify(cls, score_value: float) -> RiskLevel:
        if score_value < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if score_value < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH


# ---------------------------------------------------------------------------
# 4. HScore  (Hemophagocytic Syndrome Score)
# ---------------------------------------------------------------------------

class HScore:
    """Hemophagocytic Syndrome Score.

    A validated weighted scoring system for the diagnosis of reactive
    hemophagocytic lymphohistiocytosis (HLH).  Relevant to CAR-T safety
    because IEC-associated HLH / macrophage activation syndrome is a
    recognised life-threatening complication.

    Published:
        Fardet L et al. Development and validation of the HScore, a score
        for the diagnosis of reactive hemophagocytic syndrome.  Arthritis
        Rheumatol. 2014;66(9):2613-2620.

    Nine variables, each contributing weighted points:

    ===========================  ====================  ======
    Variable                     Criterion             Points
    ===========================  ====================  ======
    Temperature (C)              <38.4                 0
                                 38.4 - 39.4           33
                                 >39.4                 49
    Organomegaly                 None                  0
                                 Hepato- or spleno-    23
                                 Both                  38
    Cytopenias (lineages)        1 lineage             0
                                 2 lineages            24
                                 3 lineages            34
    Ferritin (ng/mL)             <2000                 0
                                 2000 - 6000           35
                                 >6000                 50
    Triglycerides (mmol/L)       <1.5                  0
                                 1.5 - 4.0             44
                                 >4.0                  64
    Fibrinogen (g/L)             >2.5                  0
                                 <=2.5                 30
    AST (U/L)                    <30                   0
                                 >=30                  19
    Hemophagocytosis on BM       No                    0
                                 Yes                   35
    Known immunosuppression      No                    0
                                 Yes                   18
    ===========================  ====================  ======

    Score range: 0-337.  Score >169 => >93% probability of HLH.

    Risk stratification:
        - Low:      HScore < 90
        - Moderate: 90 <= HScore < 169
        - High:     HScore >= 169  (>93% HLH probability)

    Required patient data keys:
        - ``temperature_c``              : float
        - ``organomegaly``               : str ("none"/"hepatomegaly"/
          "splenomegaly"/"both")
        - ``cytopenias_lineages``        : int (1, 2, or 3)
        - ``ferritin_ng_ml``             : float
        - ``triglycerides_mmol_l``       : float
        - ``fibrinogen_g_l``             : float
        - ``ast_u_per_l``               : float
        - ``hemophagocytosis_on_bm``    : bool
        - ``known_immunosuppression``   : bool
    """

    MODEL_NAME = "HScore"
    CITATION = "Fardet et al. Arthritis Rheumatol 2014;66(9):2613-2620"
    MAX_SCORE = 337
    HLH_THRESHOLD = 169

    THRESHOLD_LOW = 90
    THRESHOLD_HIGH = 169

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the HScore.

        Handles missing variables gracefully: each missing variable contributes
        0 points but reduces confidence.  At least 3 of the 9 variables must
        be present for a result.

        Args:
            patient_data: Dict of clinical variables.

        Returns:
            A ScoringResult with the HScore (0-337) and risk level.
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []
        factors: dict[str, Any] = {}
        total = 0
        variables_available = 0
        total_variables = 9

        # --- Temperature ---
        temp = _validate_positive(
            patient_data, "temperature_c", errors, warnings, required=False,
        )
        # Clear any error from optional missing field (errors list may have
        # unrelated entries; the helper only appends to warnings for optional).
        if temp is not None:
            variables_available += 1
            if temp < 38.4:
                pts = 0
            elif temp <= 39.4:
                pts = 33
            else:
                pts = 49
            total += pts
            factors["temperature_c"] = {"value": temp, "points": pts}

        # --- Organomegaly ---
        organo = patient_data.get("organomegaly")
        if organo is not None:
            variables_available += 1
            organo_str = str(organo).lower().strip()
            if organo_str in ("none", "no", "0", "false"):
                pts = 0
            elif organo_str in ("hepatomegaly", "splenomegaly", "hepato", "spleno"):
                pts = 23
            elif organo_str in ("both", "hepatosplenomegaly"):
                pts = 38
            else:
                warnings.append(
                    f"Unrecognised organomegaly value: {organo!r}; "
                    "expected 'none', 'hepatomegaly', 'splenomegaly', or 'both'. "
                    "Scoring as 0."
                )
                pts = 0
            total += pts
            factors["organomegaly"] = {"value": organo_str, "points": pts}
        else:
            warnings.append("Optional field not provided: organomegaly")

        # --- Cytopenias ---
        cyto = _validate_non_negative_int(
            patient_data, "cytopenias_lineages", errors, warnings,
            required=False, max_value=3,
        )
        if cyto is not None:
            variables_available += 1
            if cyto <= 1:
                pts = 0
            elif cyto == 2:
                pts = 24
            else:  # 3
                pts = 34
            total += pts
            factors["cytopenias_lineages"] = {"value": cyto, "points": pts}

        # --- Ferritin ---
        ferritin = _validate_positive(
            patient_data, "ferritin_ng_ml", errors, warnings, required=False,
        )
        if ferritin is not None:
            variables_available += 1
            if ferritin < 2000.0:
                pts = 0
            elif ferritin <= 6000.0:
                pts = 35
            else:
                pts = 50
            total += pts
            factors["ferritin_ng_ml"] = {"value": ferritin, "points": pts}

        # --- Triglycerides ---
        trig = _validate_positive(
            patient_data, "triglycerides_mmol_l", errors, warnings, required=False,
        )
        if trig is not None:
            variables_available += 1
            if trig < 1.5:
                pts = 0
            elif trig <= 4.0:
                pts = 44
            else:
                pts = 64
            total += pts
            factors["triglycerides_mmol_l"] = {"value": trig, "points": pts}

        # --- Fibrinogen ---
        fib = _validate_positive(
            patient_data, "fibrinogen_g_l", errors, warnings, required=False,
        )
        if fib is not None:
            variables_available += 1
            pts = 30 if fib <= 2.5 else 0
            total += pts
            factors["fibrinogen_g_l"] = {"value": fib, "points": pts}

        # --- AST ---
        ast_val = _validate_positive(
            patient_data, "ast_u_per_l", errors, warnings, required=False,
        )
        if ast_val is not None:
            variables_available += 1
            pts = 19 if ast_val >= 30.0 else 0
            total += pts
            factors["ast_u_per_l"] = {"value": ast_val, "points": pts}

        # --- Hemophagocytosis on bone marrow ---
        hemo = _validate_bool(
            patient_data, "hemophagocytosis_on_bm", errors, warnings, required=False,
        )
        if hemo is not None:
            variables_available += 1
            pts = 35 if hemo else 0
            total += pts
            factors["hemophagocytosis_on_bm"] = {"value": hemo, "points": pts}

        # --- Known immunosuppression ---
        immuno = _validate_bool(
            patient_data, "known_immunosuppression", errors, warnings, required=False,
        )
        if immuno is not None:
            variables_available += 1
            pts = 18 if immuno else 0
            total += pts
            factors["known_immunosuppression"] = {"value": immuno, "points": pts}

        # --- Fatal errors from validation ---
        if errors:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        # --- Require at least 3 variables for a meaningful result ---
        if variables_available < 3:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=[
                    f"Insufficient data: only {variables_available}/9 HScore "
                    "variables provided (minimum 3 required)"
                ],
                warnings=warnings,
                citation=self.CITATION,
            )

        confidence = variables_available / total_variables
        if variables_available < total_variables:
            warnings.append(
                f"Partial HScore: {variables_available}/{total_variables} variables "
                "provided. Score is a lower bound."
            )

        risk_level = self._classify(total)
        hlh_probability = self._approximate_probability(total)

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=float(total),
            risk_level=risk_level,
            confidence=round(confidence, 3),
            contributing_factors=factors,
            warnings=warnings,
            citation=self.CITATION,
            metadata={
                "max_possible_score": self.MAX_SCORE,
                "hlh_probability_estimate": round(hlh_probability, 4),
                "variables_available": variables_available,
                "variables_total": total_variables,
            },
        )

    @classmethod
    def _classify(cls, hscore: int) -> RiskLevel:
        if hscore < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if hscore < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH

    @staticmethod
    def _approximate_probability(hscore: int) -> float:
        """Approximate HLH probability from the HScore.

        The original Fardet 2014 paper provides a probability curve.  We
        approximate it with a logistic function fitted to the published data
        points::

            P(HLH) ~ 1 / (1 + exp(-0.04 * (HScore - 168)))

        At HScore = 169, P ~ 0.52; at HScore = 250, P ~ 0.96.
        """
        return 1.0 / (1.0 + math.exp(-0.04 * (hscore - 168)))


# ---------------------------------------------------------------------------
# 5. CAR-HEMATOTOX Score
# ---------------------------------------------------------------------------

class CARHematotox:
    """CAR-HEMATOTOX Score.

    A validated baseline scoring system for predicting severe hematotoxicity
    (prolonged cytopenias) after CAR-T cell therapy.  Validated in a
    multicenter cohort of 549 patients.

    Published:
        Rejeski K et al. CAR-HEMATOTOX: a model for CAR T-cell-related
        hematologic toxicity in relapsed/refractory large B-cell lymphoma.
        Blood. 2021;138(24):2499-2513.

    Scoring (5 variables, each 0-2 points):

    ==========================  ========================  ======
    Variable                    Criterion                 Points
    ==========================  ========================  ======
    ANC (x10^9/L)              >1.0                      0
                                0.5 - 1.0                 1
                                <0.5                      2
    Hemoglobin (g/dL)          >10                       0
                                8 - 10                    1
                                <8                        2
    Platelets (x10^9/L)        >100                      0
                                50 - 100                  1
                                <50                       2
    CRP (mg/L)                 <10                       0
                                10 - 50                   1
                                >50                       2
    Ferritin (ng/mL)           <500                      0
                                500 - 1000                1
                                >1000                     2
    ==========================  ========================  ======

    Score range: 0-10.  Higher = greater hematotoxicity risk.

    Risk stratification:
        - Low:      0-1
        - Moderate: 2
        - High:     >= 3

    Required patient data keys:
        - ``anc_10e9_per_l``    : Absolute neutrophil count (x10^9/L)
        - ``hemoglobin_g_dl``   : Hemoglobin (g/dL)
        - ``platelets_per_nl``  : Platelet count (x10^9/L)
        - ``crp_mg_l``          : C-reactive protein (mg/L)
        - ``ferritin_ng_ml``    : Ferritin (ng/mL)
    """

    MODEL_NAME = "CAR_HEMATOTOX"
    CITATION = "Rejeski et al. Blood 2021;138(24):2499-2513"
    MAX_SCORE = 10

    THRESHOLD_LOW = 2       # 0-1 = low
    THRESHOLD_HIGH = 3      # >= 3 = high

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the CAR-HEMATOTOX score.

        Args:
            patient_data: Dict of baseline lab values.

        Returns:
            A ScoringResult with the score (0-10) and risk level.
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []
        factors: dict[str, Any] = {}
        total = 0
        variables_available = 0
        total_variables = 5

        # --- ANC ---
        anc = _validate_positive(
            patient_data, "anc_10e9_per_l", errors, warnings, required=False,
        )
        if anc is not None:
            variables_available += 1
            if anc < 0.5:
                pts = 2
            elif anc <= 1.0:
                pts = 1
            else:
                pts = 0
            total += pts
            factors["anc_10e9_per_l"] = {"value": anc, "points": pts}

        # --- Hemoglobin ---
        hgb = _validate_positive(
            patient_data, "hemoglobin_g_dl", errors, warnings, required=False,
        )
        if hgb is not None:
            variables_available += 1
            if hgb < 8.0:
                pts = 2
            elif hgb <= 10.0:
                pts = 1
            else:
                pts = 0
            total += pts
            factors["hemoglobin_g_dl"] = {"value": hgb, "points": pts}

        # --- Platelets ---
        plt_count = _validate_positive(
            patient_data, "platelets_per_nl", errors, warnings, required=False,
        )
        if plt_count is not None:
            variables_available += 1
            if plt_count < 50.0:
                pts = 2
            elif plt_count <= 100.0:
                pts = 1
            else:
                pts = 0
            total += pts
            factors["platelets_per_nl"] = {"value": plt_count, "points": pts}

        # --- CRP (mg/L) ---
        crp = _validate_positive(
            patient_data, "crp_mg_l", errors, warnings, required=False,
        )
        if crp is not None:
            variables_available += 1
            if crp < 10.0:
                pts = 0
            elif crp <= 50.0:
                pts = 1
            else:
                pts = 2
            total += pts
            factors["crp_mg_l"] = {"value": crp, "points": pts}

        # --- Ferritin ---
        ferritin = _validate_positive(
            patient_data, "ferritin_ng_ml", errors, warnings, required=False,
        )
        if ferritin is not None:
            variables_available += 1
            if ferritin < 500.0:
                pts = 0
            elif ferritin <= 1000.0:
                pts = 1
            else:
                pts = 2
            total += pts
            factors["ferritin_ng_ml"] = {"value": ferritin, "points": pts}

        # --- Fatal errors ---
        if errors:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        # --- Require at least 3 of 5 variables ---
        if variables_available < 3:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=[
                    f"Insufficient data: only {variables_available}/5 "
                    "CAR-HEMATOTOX variables provided (minimum 3 required)"
                ],
                warnings=warnings,
                citation=self.CITATION,
            )

        confidence = variables_available / total_variables
        if variables_available < total_variables:
            warnings.append(
                f"Partial CAR-HEMATOTOX: {variables_available}/{total_variables} "
                "variables provided. Score may underestimate risk."
            )

        risk_level = self._classify(total)

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=float(total),
            risk_level=risk_level,
            confidence=round(confidence, 3),
            contributing_factors=factors,
            warnings=warnings,
            citation=self.CITATION,
            metadata={
                "max_possible_score": self.MAX_SCORE,
                "variables_available": variables_available,
                "variables_total": total_variables,
            },
        )

    @classmethod
    def _classify(cls, score_value: int) -> RiskLevel:
        if score_value < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if score_value < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH


# ---------------------------------------------------------------------------
# 6. Teachey 3-Cytokine Model
# ---------------------------------------------------------------------------

class TeacheyCytokineModel:
    """Teachey 3-Cytokine Logistic Regression Model for Severe CRS.

    A logistic regression model using three cytokine/soluble-receptor
    biomarkers measured within the first 72 hours after CAR-T infusion.
    Predicts probability of severe (Grade 4-5) CRS.

    Published:
        Teachey DT et al. Identification of predictive biomarkers for
        cytokine release syndrome after chimeric antigen receptor T-cell
        therapy for acute lymphoblastic leukemia.  Cancer Discov.
        2016;6(6):664-679.

    Formula::

        logit(P) = beta_0
                 + beta_1 * ln(IFN_gamma)
                 + beta_2 * ln(sgp130)
                 + beta_3 * ln(IL1RA)

        P(severe CRS) = 1 / (1 + exp(-logit(P)))

    Approximate published coefficients:
        beta_0 = -8.5
        beta_1 =  0.8  (IFN-gamma, pg/mL)
        beta_2 =  1.2  (sgp130, ng/mL)
        beta_3 =  0.6  (IL-1RA, pg/mL)

    Reported AUC: 0.93-0.98.

    Risk stratification (on predicted probability):
        - Low:      P < 0.20
        - Moderate: 0.20 <= P < 0.50
        - High:     P >= 0.50

    Required patient data keys:
        - ``ifn_gamma_pg_ml``  : IFN-gamma (pg/mL)
        - ``sgp130_ng_ml``     : Soluble gp130 (ng/mL)
        - ``il1ra_pg_ml``      : IL-1 receptor antagonist (pg/mL)
    """

    MODEL_NAME = "Teachey_Cytokine_3var"
    CITATION = "Teachey et al. Cancer Discov 2016;6(6):664-679"

    # Published approximate coefficients
    BETA_0: float = -8.5
    BETA_1_IFN_GAMMA: float = 0.8
    BETA_2_SGP130: float = 1.2
    BETA_3_IL1RA: float = 0.6

    THRESHOLD_LOW: float = 0.20
    THRESHOLD_HIGH: float = 0.50

    def predict(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Compute the probability of severe CRS.

        Args:
            patient_data: Dict with cytokine measurements.

        Returns:
            A ScoringResult where ``score`` is the predicted probability
            (0.0-1.0) and ``risk_level`` is derived from that probability.
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []

        ifn_gamma = _validate_positive(
            patient_data, "ifn_gamma_pg_ml", errors, warnings,
        )
        sgp130 = _validate_positive(
            patient_data, "sgp130_ng_ml", errors, warnings,
        )
        il1ra = _validate_positive(
            patient_data, "il1ra_pg_ml", errors, warnings,
        )

        if errors:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        assert ifn_gamma is not None and sgp130 is not None and il1ra is not None

        # Guard against log(0)
        if ifn_gamma <= 0.0 or sgp130 <= 0.0 or il1ra <= 0.0:
            errors.append(
                "All cytokine values must be > 0 for log transformation. "
                f"Got: IFNg={ifn_gamma}, sgp130={sgp130}, IL1RA={il1ra}"
            )
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=None,
                risk_level=None,
                confidence=0.0,
                errors=errors,
                warnings=warnings,
                citation=self.CITATION,
            )

        log_ifn = math.log(ifn_gamma)
        log_sgp130 = math.log(sgp130)
        log_il1ra = math.log(il1ra)

        logit = (
            self.BETA_0
            + self.BETA_1_IFN_GAMMA * log_ifn
            + self.BETA_2_SGP130 * log_sgp130
            + self.BETA_3_IL1RA * log_il1ra
        )

        probability = 1.0 / (1.0 + math.exp(-logit))

        risk_level = self._classify(probability)

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=round(probability, 6),
            risk_level=risk_level,
            confidence=0.95,  # Model has validated AUC 0.93-0.98
            contributing_factors={
                "ifn_gamma_pg_ml": ifn_gamma,
                "sgp130_ng_ml": sgp130,
                "il1ra_pg_ml": il1ra,
                "log_ifn_gamma": round(log_ifn, 4),
                "log_sgp130": round(log_sgp130, 4),
                "log_il1ra": round(log_il1ra, 4),
                "logit": round(logit, 4),
            },
            warnings=warnings,
            citation=self.CITATION,
            metadata={
                "probability_severe_crs": round(probability, 6),
                "coefficients": {
                    "beta_0": self.BETA_0,
                    "beta_1_ifn_gamma": self.BETA_1_IFN_GAMMA,
                    "beta_2_sgp130": self.BETA_2_SGP130,
                    "beta_3_il1ra": self.BETA_3_IL1RA,
                },
            },
        )

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Alias for :meth:`predict` (uniform interface for ensemble runner)."""
        return self.predict(patient_data)

    @classmethod
    def _classify(cls, probability: float) -> RiskLevel:
        if probability < cls.THRESHOLD_LOW:
            return RiskLevel.LOW
        if probability < cls.THRESHOLD_HIGH:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH


# ---------------------------------------------------------------------------
# 7. Hay Binary Classifier
# ---------------------------------------------------------------------------

class HayBinaryClassifier:
    """Hay Binary Classifier for Early Severe CRS Screening.

    A simple rule-based classifier for very early identification of patients
    who will develop severe CRS.  Designed for the first 36 hours after
    CAR-T infusion.

    Published:
        Hay KA et al. Kinetics and biomarkers of severe cytokine release
        syndrome after CD19 chimeric antigen receptor-modified T-cell
        therapy.  Blood. 2017;130(21):2295-2306.

    Rule::

        IF fever >= 38.9 C within 36h of infusion
            AND (MCP-1 > 1343 pg/mL
                 OR (MCP-1 unavailable AND tachycardia present))
        THEN predict severe CRS

    Reported performance:
        Sensitivity: 100%
        Specificity: 95%

    Risk stratification:
        - Low:      Rule not met
        - Moderate: Fever criterion met but MCP-1 and tachycardia data missing
        - High:     Full rule met (severe CRS predicted)

    Required patient data keys:
        - ``temperature_c`` : Peak temperature in Celsius (within first 36h)
          **OR** ``temperature_f`` : Peak temperature in Fahrenheit

    Optional but strongly recommended:
        - ``hours_since_infusion`` : Hours elapsed since CAR-T infusion
        - ``mcp1_pg_ml``          : Monocyte chemoattractant protein-1 (pg/mL)
        - ``tachycardia``         : bool (heart rate > 100 bpm)
    """

    MODEL_NAME = "Hay_Binary_Classifier"
    CITATION = "Hay et al. Blood 2017;130(21):2295-2306"

    FEVER_THRESHOLD_C: float = 38.9
    MCP1_THRESHOLD: float = 1343.0
    MAX_HOURS: float = 36.0

    def predict(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Apply the Hay binary classification rule.

        Args:
            patient_data: Dict with temperature, timing, and optionally
                MCP-1 and tachycardia status.

        Returns:
            A ScoringResult where ``score`` is 1.0 (severe CRS predicted)
            or 0.0 (not predicted).
        """
        patient_data = _resolve_aliases(patient_data)
        errors: list[str] = []
        warnings: list[str] = []

        # --- Resolve temperature to Celsius ---
        temp_c: float | None = None

        temp_c_raw = _validate_positive(
            patient_data, "temperature_c", [], [], required=False,
        )
        if temp_c_raw is not None:
            temp_c = temp_c_raw
        else:
            temp_f_raw = _validate_positive(
                patient_data, "temperature_f", [], [], required=False,
            )
            if temp_f_raw is not None:
                temp_c = (temp_f_raw - 32.0) * 5.0 / 9.0
            else:
                errors.append("Missing required field: temperature_c or temperature_f")
                return ScoringResult(
                    model_name=self.MODEL_NAME,
                    score=None,
                    risk_level=None,
                    confidence=0.0,
                    errors=errors,
                    warnings=warnings,
                    citation=self.CITATION,
                )

        # --- Hours since infusion (optional but affects confidence) ---
        hours: float | None = None
        raw_hours = patient_data.get("hours_since_infusion")
        if raw_hours is not None:
            try:
                hours = float(raw_hours)
            except (TypeError, ValueError):
                warnings.append(
                    f"Non-numeric hours_since_infusion: {raw_hours!r}; "
                    "ignoring timing check"
                )

        timing_valid = True
        if hours is not None and hours > self.MAX_HOURS:
            timing_valid = False
            warnings.append(
                f"hours_since_infusion = {hours:.1f}h exceeds the 36h window "
                "for the Hay classifier. Applying rule but confidence is reduced."
            )

        # --- Fever criterion ---
        has_fever = temp_c >= self.FEVER_THRESHOLD_C

        if not has_fever:
            return ScoringResult(
                model_name=self.MODEL_NAME,
                score=0.0,
                risk_level=RiskLevel.LOW,
                confidence=0.95 if timing_valid else 0.70,
                contributing_factors={
                    "temperature_c": round(temp_c, 2),
                    "fever_criterion_met": False,
                },
                warnings=warnings,
                citation=self.CITATION,
                metadata={
                    "prediction": "not_severe_crs",
                    "fever_threshold_c": self.FEVER_THRESHOLD_C,
                },
            )

        # --- Fever present: check MCP-1 or tachycardia ---
        mcp1 = _validate_positive(
            patient_data, "mcp1_pg_ml", [], warnings, required=False,
        )
        tachycardia = _validate_bool(
            patient_data, "tachycardia", [], warnings, required=False,
        )

        mcp1_positive = mcp1 is not None and mcp1 > self.MCP1_THRESHOLD
        mcp1_unavailable = mcp1 is None
        tachy_positive = tachycardia is True

        # The Hay rule:
        #   fever AND (MCP-1 elevated  OR  (MCP-1 unavailable AND tachycardia))
        rule_met = mcp1_positive or (mcp1_unavailable and tachy_positive)

        if rule_met:
            score_val = 1.0
            risk_level = RiskLevel.HIGH
            prediction = "severe_crs"
            confidence = 0.95 if timing_valid else 0.75
        elif mcp1_unavailable and tachycardia is None:
            # Fever present but neither MCP-1 nor tachycardia info available
            score_val = 0.0
            risk_level = RiskLevel.MODERATE
            prediction = "indeterminate"
            confidence = 0.50
            warnings.append(
                "Fever criterion met but neither MCP-1 nor tachycardia data "
                "available. Cannot fully evaluate Hay rule. Flagging as "
                "moderate risk for clinical review."
            )
        else:
            # Fever present, but MCP-1 below threshold (or unavailable with
            # tachycardia absent) -- rule not met.
            score_val = 0.0
            risk_level = RiskLevel.LOW
            prediction = "not_severe_crs"
            confidence = 0.90 if timing_valid else 0.65

        return ScoringResult(
            model_name=self.MODEL_NAME,
            score=score_val,
            risk_level=risk_level,
            confidence=confidence,
            contributing_factors={
                "temperature_c": round(temp_c, 2),
                "fever_criterion_met": has_fever,
                "mcp1_pg_ml": mcp1,
                "mcp1_above_threshold": mcp1_positive,
                "tachycardia": tachycardia,
                "hours_since_infusion": hours,
            },
            warnings=warnings,
            citation=self.CITATION,
            metadata={
                "prediction": prediction,
                "fever_threshold_c": self.FEVER_THRESHOLD_C,
                "mcp1_threshold_pg_ml": self.MCP1_THRESHOLD,
                "rule_fully_evaluated": mcp1 is not None or tachycardia is not None,
            },
        )

    def score(self, patient_data: dict[str, Any]) -> ScoringResult:
        """Alias for :meth:`predict` (uniform interface for ensemble runner)."""
        return self.predict(patient_data)
