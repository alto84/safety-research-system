"""
Clinical biomarker scoring models for cell therapy safety prediction.

Deterministic, peer-reviewed scoring systems for predicting adverse events
in CAR-T and other immune effector cell therapies. Each model implements
a published formula with full traceability to source literature.

Models:
    EASIX:              Endothelial Activation and Stress Index
    ModifiedEASIX:      Modified EASIX (CRP replaces creatinine)
    PreModifiedEASIX:   Pre-lymphodepletion Modified EASIX
    HScore:             Hemophagocytic Syndrome Score
    CARHematotox:       CAR-HEMATOTOX Score
    TeacheyCytokineModel: 3-cytokine logistic regression model
    HayBinaryClassifier:  Early CRS binary screen

Population-level risk models:
    bayesian_risk:      Beta-Binomial Bayesian risk estimation
    mitigation_model:   Correlated mitigation combination model
    model_registry:     Multi-method risk estimation registry (7 models)
    model_validation:   Calibration, scoring, coverage, cross-validation

FAERS signal detection:
    faers_signal:       Disproportionality analysis via openFDA API
"""

from src.models.biomarker_scores import (
    EASIX,
    CARHematotox,
    HayBinaryClassifier,
    HScore,
    ModifiedEASIX,
    PreModifiedEASIX,
    RiskLevel,
    ScoringResult,
    TeacheyCytokineModel,
    ValidationError,
)
from src.models.bayesian_risk import (
    CRS_PRIOR,
    ICAHS_PRIOR,
    ICANS_PRIOR,
    STUDY_TIMELINE,
    PosteriorEstimate,
    PriorSpec,
    StudyDataPoint,
    compute_evidence_accrual,
    compute_posterior,
)
from src.models.ensemble_runner import BiomarkerEnsembleRunner, EnsembleResult, LayerResult
from src.models.faers_signal import (
    CAR_T_PRODUCTS,
    TARGET_AES,
    FAERSSignal,
    FAERSSummary,
    compute_ebgm,
    compute_prr,
    compute_ror,
    classify_signal,
    get_faers_signals,
    get_faers_summary,
)
from src.models.model_registry import (
    MODEL_REGISTRY,
    RiskModel,
    compare_models,
    estimate_risk,
    list_models,
)
from src.models.model_validation import (
    brier_score,
    calibration_check,
    coverage_probability,
    leave_one_out_cv,
    model_comparison,
    sequential_prediction_test,
)
from src.models.mitigation_model import (
    MITIGATION_CORRELATIONS,
    MITIGATION_STRATEGIES,
    MitigationResult,
    MitigationStrategy,
    calculate_mitigated_risk,
    combine_correlated_rr,
    combine_multiple_rrs,
    get_mitigation_correlation,
    monte_carlo_mitigated_risk,
)

__all__ = [
    # Scoring models
    "EASIX",
    "ModifiedEASIX",
    "PreModifiedEASIX",
    "HScore",
    "CARHematotox",
    "TeacheyCytokineModel",
    "HayBinaryClassifier",
    # Data classes
    "RiskLevel",
    "ScoringResult",
    "ValidationError",
    # Ensemble
    "BiomarkerEnsembleRunner",
    "EnsembleResult",
    "LayerResult",
    # Bayesian risk
    "PriorSpec",
    "PosteriorEstimate",
    "StudyDataPoint",
    "CRS_PRIOR",
    "ICANS_PRIOR",
    "ICAHS_PRIOR",
    "STUDY_TIMELINE",
    "compute_posterior",
    "compute_evidence_accrual",
    # Mitigation model
    "MitigationStrategy",
    "MitigationResult",
    "MITIGATION_STRATEGIES",
    "MITIGATION_CORRELATIONS",
    "get_mitigation_correlation",
    "combine_correlated_rr",
    "combine_multiple_rrs",
    "monte_carlo_mitigated_risk",
    "calculate_mitigated_risk",
    # Model registry
    "MODEL_REGISTRY",
    "RiskModel",
    "estimate_risk",
    "compare_models",
    "list_models",
    # Model validation
    "calibration_check",
    "brier_score",
    "coverage_probability",
    "leave_one_out_cv",
    "model_comparison",
    "sequential_prediction_test",
    # FAERS signal detection
    "FAERSSignal",
    "FAERSSummary",
    "CAR_T_PRODUCTS",
    "TARGET_AES",
    "compute_prr",
    "compute_ror",
    "compute_ebgm",
    "classify_signal",
    "get_faers_signals",
    "get_faers_summary",
]
