"""
Tests validating regulatory requirements for the PSP.

These tests ensure:
1. Audit trail completeness (21 CFR Part 11 compliance)
2. PII handling (GDPR / data minimization)
3. Reproducibility (same inputs -> same outputs)
4. Model documentation traceability
5. Prediction explainability requirements
"""

import pytest
import re
import copy
from datetime import datetime, timedelta

from tests.conftest import (
    SafetyIndex,
    AuditRecord,
    AggregatedRisk,
    PatientData,
    SafetyPrediction,
    TokenCount,
)


# ---------------------------------------------------------------------------
# PII detection utilities
# ---------------------------------------------------------------------------

# Patterns that should NEVER appear in foundation model prompts or logs
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "mrn": re.compile(r"\bMRN[:\s]*\d{6,10}\b", re.IGNORECASE),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "date_of_birth": re.compile(r"\b(?:DOB|date of birth)[:\s]?\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    "full_name": re.compile(r"\b(?:patient name|name)[:\s]?[A-Z][a-z]+ [A-Z][a-z]+\b"),
}


def contains_pii(text: str) -> list[str]:
    """Scan text for PII patterns. Returns list of matched pattern names."""
    matches = []
    for pattern_name, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            matches.append(pattern_name)
    return matches


def is_pseudonymized(patient_id: str) -> bool:
    """Check if a patient ID follows pseudonymization format (PSP-xxx or similar)."""
    # Valid formats: PSP-TEST-xxx, PSP-xxx, PSEUDO-xxx, or UUID-like
    pseudo_pattern = re.compile(
        r"^(PSP-|PSEUDO-|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        re.IGNORECASE,
    )
    return bool(pseudo_pattern.match(patient_id))


# ===========================================================================
# Tests
# ===========================================================================

class TestAuditTrailCompleteness:
    """Tests for 21 CFR Part 11 audit trail requirements.

    Every prediction must have a complete, immutable audit record containing:
    - Unique prediction ID
    - Timestamp
    - Patient identifier (pseudonymized)
    - All input features used
    - Model versions
    - Graph snapshot version
    - Raw model outputs
    - Ensemble weights and calibration parameters
    - Final prediction with confidence interval
    - Mechanistic explanation and pathway trace
    """

    def test_audit_has_unique_prediction_id(self, sample_audit_record):
        assert sample_audit_record.prediction_id is not None
        assert len(sample_audit_record.prediction_id) > 0

    def test_audit_has_timestamp(self, sample_audit_record):
        assert isinstance(sample_audit_record.timestamp, datetime)

    def test_audit_has_patient_id(self, sample_audit_record):
        assert sample_audit_record.patient_id is not None
        assert len(sample_audit_record.patient_id) > 0

    def test_audit_patient_id_is_pseudonymized(self, sample_audit_record):
        assert is_pseudonymized(sample_audit_record.patient_id)

    def test_audit_has_input_features(self, sample_audit_record):
        assert isinstance(sample_audit_record.input_features, dict)
        assert len(sample_audit_record.input_features) > 0

    def test_audit_has_all_model_versions(self, sample_audit_record):
        assert isinstance(sample_audit_record.model_versions, dict)
        assert len(sample_audit_record.model_versions) >= 1
        for model, version in sample_audit_record.model_versions.items():
            assert isinstance(model, str)
            assert isinstance(version, str)
            assert len(version) > 0

    def test_audit_has_graph_snapshot_version(self, sample_audit_record):
        assert sample_audit_record.graph_snapshot_version is not None
        assert len(sample_audit_record.graph_snapshot_version) > 0

    def test_audit_has_router_decision(self, sample_audit_record):
        assert isinstance(sample_audit_record.prompt_router_decision, dict)
        assert len(sample_audit_record.prompt_router_decision) > 0

    def test_audit_has_raw_model_outputs(self, sample_audit_record):
        assert isinstance(sample_audit_record.raw_model_outputs, list)
        assert len(sample_audit_record.raw_model_outputs) >= 1

    def test_audit_has_ensemble_weights(self, sample_audit_record):
        assert isinstance(sample_audit_record.ensemble_weights, dict)
        assert abs(sum(sample_audit_record.ensemble_weights.values()) - 1.0) < 0.01

    def test_audit_has_calibration_params(self, sample_audit_record):
        assert isinstance(sample_audit_record.calibration_params, dict)
        assert "platt_a" in sample_audit_record.calibration_params
        assert "platt_b" in sample_audit_record.calibration_params

    def test_audit_has_final_prediction(self, sample_audit_record):
        assert isinstance(sample_audit_record.final_prediction, AggregatedRisk)

    def test_audit_has_confidence_interval(self, sample_audit_record):
        ci = sample_audit_record.confidence_interval
        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] <= ci[1]

    def test_audit_has_mechanistic_explanation(self, sample_audit_record):
        assert isinstance(sample_audit_record.mechanistic_explanation, str)
        assert len(sample_audit_record.mechanistic_explanation) > 0

    def test_audit_has_pathway_trace(self, sample_audit_record):
        assert isinstance(sample_audit_record.pathway_trace, list)
        assert len(sample_audit_record.pathway_trace) >= 1

    def test_audit_has_similar_historical_outcomes(self, sample_audit_record):
        assert isinstance(sample_audit_record.similar_historical_outcomes, list)


class TestPIIHandling:
    """Tests for GDPR compliance and data minimization."""

    def test_patient_ids_pseudonymized(self, low_risk_patient, medium_risk_patient, high_risk_patient):
        """All test patient IDs follow pseudonymization conventions."""
        for patient in [low_risk_patient, medium_risk_patient, high_risk_patient]:
            assert is_pseudonymized(patient.patient_id), (
                f"Patient ID '{patient.patient_id}' does not follow pseudonymization format"
            )

    def test_patient_data_no_real_names(self, low_risk_patient, medium_risk_patient, high_risk_patient):
        """Patient data should not contain real names, SSNs, or other PII."""
        for patient in [low_risk_patient, medium_risk_patient, high_risk_patient]:
            # Check demographics dict as string
            demo_str = str(patient.demographics)
            pii_found = contains_pii(demo_str)
            assert len(pii_found) == 0, f"PII detected in demographics: {pii_found}"

    def test_model_rationale_no_pii(
        self,
        claude_crs_prediction_low,
        gpt_crs_prediction_low,
        claude_crs_prediction_high,
    ):
        """Mechanistic rationales should not contain PII."""
        for pred in [claude_crs_prediction_low, gpt_crs_prediction_low, claude_crs_prediction_high]:
            pii_found = contains_pii(pred.mechanistic_rationale)
            assert len(pii_found) == 0, (
                f"PII detected in model rationale from {pred.model_id}: {pii_found}"
            )

    def test_audit_record_uses_pseudonymized_id(self, sample_audit_record):
        """Audit records should use pseudonymized patient IDs, not real identifiers."""
        assert is_pseudonymized(sample_audit_record.patient_id)

    def test_pii_detection_catches_ssn(self):
        """Verify the PII detector catches Social Security Numbers."""
        assert "ssn" in contains_pii("Patient SSN is 123-45-6789")

    def test_pii_detection_catches_email(self):
        assert "email" in contains_pii("Contact: patient@hospital.com")

    def test_pii_detection_catches_mrn(self):
        assert "mrn" in contains_pii("MRN: 12345678")

    def test_pii_detection_clean_text(self):
        """Clinical text without PII should pass cleanly."""
        text = "IL-6 elevated at 48 pg/mL. CRP 85 mg/L. Ferritin 2200 ng/mL."
        assert len(contains_pii(text)) == 0


class TestReproducibility:
    """Tests for prediction reproducibility.

    Given the same inputs, model versions, and graph state, the system should
    produce identical outputs. This is required for regulatory validation.
    """

    def test_safety_index_deterministic_structure(self, low_risk_safety_index):
        """Safety Index structure should be fully deterministic (except prediction_id/timestamp)."""
        si = low_risk_safety_index
        # All fields that must be deterministic
        assert si.overall_risk == 0.12
        assert si.model_agreement == 0.92
        assert si.evidence_strength == "strong"
        assert len(si.risk_trajectory) == 6
        assert len(si.key_biomarkers) == 5

    def test_event_risk_deterministic(self, low_risk_safety_index):
        """EventRisk components should be fully reproducible."""
        crs = low_risk_safety_index.crs_risk
        assert crs.probability == 0.10
        severity_sum = sum(crs.severity_distribution.values())
        assert severity_sum == pytest.approx(1.0, abs=0.01)

    def test_same_inputs_same_risk_ordering(self):
        """Verify that identical aggregated risks produce consistent Safety Index ordering."""
        from tests.unit.test_safety_index import SafetyIndexCalculator
        calc = SafetyIndexCalculator()

        agg_a = AggregatedRisk(risk_score=0.3, confidence_interval=(0.2, 0.4))
        agg_b = AggregatedRisk(risk_score=0.7, confidence_interval=(0.6, 0.8))
        zero = AggregatedRisk(risk_score=0.0, confidence_interval=(0.0, 0.0))

        si_1 = calc.compute(agg_a, zero, zero, 0.9, ["p1"], ["b1"], {}, "v1")
        si_2 = calc.compute(agg_b, zero, zero, 0.9, ["p1"], ["b1"], {}, "v1")

        assert si_1.overall_risk < si_2.overall_risk

    def test_model_version_recorded_for_reproducibility(self, low_risk_safety_index):
        """Model versions must be recorded so predictions can be reproduced later."""
        mv = low_risk_safety_index.model_versions
        assert isinstance(mv, dict)
        assert len(mv) > 0
        # Each version should be a non-empty string
        for model, version in mv.items():
            assert len(version) > 0

    def test_graph_version_recorded(self, low_risk_safety_index):
        assert low_risk_safety_index.graph_version is not None
        assert len(low_risk_safety_index.graph_version) > 0


class TestExplainability:
    """Tests for prediction explainability requirements.

    FDA AI/ML guidance requires that predictions be explainable in clinical terms.
    """

    def test_safety_index_has_primary_mechanism(self, high_risk_safety_index):
        assert high_risk_safety_index.primary_mechanism is not None
        assert len(high_risk_safety_index.primary_mechanism) > 0

    def test_safety_index_has_contributing_pathways(self, high_risk_safety_index):
        assert len(high_risk_safety_index.contributing_pathways) >= 1

    def test_safety_index_has_key_biomarkers(self, high_risk_safety_index):
        assert len(high_risk_safety_index.key_biomarkers) >= 1
        assert len(high_risk_safety_index.key_biomarkers) <= 5

    def test_event_risk_has_mechanistic_path(self, high_risk_safety_index):
        """Each event risk should trace a mechanistic pathway."""
        crs = high_risk_safety_index.crs_risk
        assert len(crs.mechanistic_path) >= 1

    def test_confidence_interval_present(self, high_risk_safety_index):
        ci = high_risk_safety_index.confidence_interval
        assert ci is not None
        assert ci[0] <= ci[1]

    def test_model_agreement_present(self, high_risk_safety_index):
        assert 0.0 <= high_risk_safety_index.model_agreement <= 1.0

    def test_monitoring_recommendation_present(self, high_risk_safety_index):
        assert len(high_risk_safety_index.monitoring_protocol) > 0

    def test_intervention_readiness_present(self, high_risk_safety_index):
        assert len(high_risk_safety_index.intervention_readiness) > 0


class TestDataMinimization:
    """Tests for data minimization principle (GDPR Article 5).

    Only features relevant to prediction should be retained and forwarded.
    """

    def test_patient_data_contains_only_clinical_fields(self, low_risk_patient):
        """Patient data should contain clinical data, not administrative/identifying data."""
        # These fields should NOT exist in patient data
        forbidden_fields = ["full_name", "ssn", "address", "insurance_id", "physician_name"]
        all_keys = set()
        all_keys.update(low_risk_patient.demographics.keys())
        all_keys.update(low_risk_patient.baseline_labs.keys())
        for field_name in forbidden_fields:
            assert field_name not in all_keys, f"Forbidden field '{field_name}' found in patient data"

    def test_audit_input_features_are_clinical(self, sample_audit_record):
        """Audit record input features should be clinical measurements only."""
        for key in sample_audit_record.input_features:
            # All keys should look like clinical lab measurements
            assert not any(
                pii_word in key.lower()
                for pii_word in ["name", "ssn", "address", "phone", "email"]
            )
