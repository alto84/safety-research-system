"""
Battle testing and stress tests for the safety prediction system.

Verifies system robustness under:
    - High-volume random patient generation
    - Adversarial inputs (NaN, Inf, extreme values, empty data)
    - Performance benchmarks (throughput requirements)
    - Memory stability under sustained load
"""

import math
import random
import time
import pytest
from datetime import timedelta

# Import scorers from biomarker tests
from tests.unit.test_biomarker_scores import (
    EASIXScorer,
    HScoreCalculator,
    CARHematotoxScorer,
    TeacheyModelScorer,
    HayModelScorer,
)

# Import validation
from tests.unit.test_input_validation import InputValidator

# Import ensemble and normalizer
from tests.unit.test_ensemble import EnsembleAggregator
from tests.unit.test_normalizer import ResponseNormalizer
from tests.conftest import SafetyPrediction, TokenCount


# ---------------------------------------------------------------------------
# Random patient generators
# ---------------------------------------------------------------------------

def random_valid_labs() -> dict:
    """Generate physiologically plausible random lab values."""
    return {
        "il6_pg_ml": random.uniform(0.5, 10000.0),
        "ifn_gamma_pg_ml": random.uniform(1.0, 5000.0),
        "crp_mg_l": random.uniform(0.5, 400.0),
        "ferritin_ng_ml": random.uniform(10.0, 50000.0),
        "ldh_u_l": random.uniform(100.0, 5000.0),
        "platelets_k_ul": random.uniform(5.0, 500.0),
        "creatinine_mg_dl": random.uniform(0.3, 10.0),
        "temperature_c": random.uniform(36.0, 41.5),
        "hemoglobin_g_dl": random.uniform(5.0, 18.0),
        "wbc_k_ul": random.uniform(0.5, 50.0),
        "anc_k_ul": random.uniform(0.1, 20.0),
        "fibrinogen_mg_dl": random.uniform(50.0, 800.0),
        "triglycerides_mmol_l": random.uniform(0.5, 10.0),
        "ast_u_l": random.uniform(10.0, 1000.0),
    }


def random_adversarial_input() -> dict:
    """Generate adversarial inputs designed to break the system."""
    adversarial_values = [
        float("nan"),
        float("inf"),
        float("-inf"),
        0.0,
        -1.0,
        -9999999.0,
        9999999999.0,
        1e308,
        -1e308,
        1e-308,
        "not_a_number",
        None,
        [],
        {},
        True,
        False,
    ]

    data = {}
    fields = [
        "il6_pg_ml", "crp_mg_l", "ferritin_ng_ml", "ldh_u_l",
        "platelets_k_ul", "creatinine_mg_dl", "temperature_c",
        "hemoglobin_g_dl", "wbc_k_ul",
    ]

    for field_name in fields:
        if random.random() < 0.7:  # 70% chance of including each field
            data[field_name] = random.choice(adversarial_values)

    return data


# ===========================================================================
# Tests
# ===========================================================================

@pytest.mark.stress
class TestHighVolumeEASIX:
    """Stress test EASIX scorer with 1000 random patients."""

    def test_1000_random_patients_no_crashes(self):
        """EASIX should not crash on 1000 valid random inputs."""
        scorer = EASIXScorer()
        random.seed(42)

        for i in range(1000):
            labs = random_valid_labs()
            try:
                result = scorer.compute(
                    ldh=labs["ldh_u_l"],
                    creatinine=labs["creatinine_mg_dl"],
                    platelets=labs["platelets_k_ul"],
                )
                if result["score"] is not None:
                    assert math.isfinite(result["score"])
                    assert result["score"] >= 0
            except ValueError:
                # Only acceptable exception: division by zero
                pass

    def test_performance_100_patients_under_1_second(self):
        """Score 100 patients in under 1 second."""
        scorer = EASIXScorer()
        random.seed(42)

        start = time.perf_counter()
        for _ in range(100):
            labs = random_valid_labs()
            scorer.compute(
                ldh=labs["ldh_u_l"],
                creatinine=labs["creatinine_mg_dl"],
                platelets=labs["platelets_k_ul"],
            )
        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"Scoring 100 patients took {elapsed:.2f}s (>1s)"


@pytest.mark.stress
class TestHighVolumeHScore:
    """Stress test HScore calculator with 1000 random patients."""

    def test_1000_random_patients_no_crashes(self):
        """HScore should not crash on 1000 valid random inputs."""
        scorer = HScoreCalculator()
        random.seed(42)

        for i in range(1000):
            labs = random_valid_labs()
            result = scorer.compute(
                temperature_c=labs["temperature_c"],
                ferritin_ng_ml=labs["ferritin_ng_ml"],
                triglycerides_mmol_l=labs["triglycerides_mmol_l"],
                fibrinogen_g_l=labs["fibrinogen_mg_dl"] / 100.0,  # Convert mg/dL to g/L
                ast_u_l=labs["ast_u_l"],
            )
            assert isinstance(result["score"], (int, float))
            assert result["score"] >= 0
            assert 0.0 <= result["probability_hlh"] <= 1.0


@pytest.mark.stress
class TestHighVolumeCARHematotox:
    """Stress test CAR-HEMATOTOX scorer."""

    def test_1000_random_patients_no_crashes(self):
        """CAR-HEMATOTOX should not crash on 1000 valid random inputs."""
        scorer = CARHematotoxScorer()
        random.seed(42)

        for i in range(1000):
            labs = random_valid_labs()
            result = scorer.compute(
                anc_k_ul=labs["anc_k_ul"],
                hemoglobin_g_dl=labs["hemoglobin_g_dl"],
                platelets_k_ul=labs["platelets_k_ul"],
                crp_mg_l=labs["crp_mg_l"],
                ferritin_ng_ml=labs["ferritin_ng_ml"],
            )
            assert 0 <= result["score"] <= 10


@pytest.mark.stress
class TestHighVolumeTeachey:
    """Stress test Teachey model."""

    def test_1000_random_patients_no_crashes(self):
        """Teachey model should not crash on 1000 valid random inputs."""
        scorer = TeacheyModelScorer()
        random.seed(42)

        for i in range(1000):
            labs = random_valid_labs()
            result = scorer.compute(
                ifn_gamma_pg_ml=labs["ifn_gamma_pg_ml"],
                sgp130_ng_ml=random.uniform(10, 5000),
                il1ra_pg_ml=random.uniform(10, 10000),
            )
            assert 0.0 <= result["probability"] <= 1.0


@pytest.mark.stress
class TestHighVolumeHay:
    """Stress test Hay model."""

    def test_1000_random_patients_no_crashes(self):
        """Hay model should not crash on 1000 random inputs."""
        scorer = HayModelScorer()
        random.seed(42)

        for i in range(1000):
            result = scorer.compute(
                fever_present=random.choice([True, False]),
                fever_onset_hours=random.uniform(1, 100) if random.random() > 0.3 else None,
                mcp1_pg_ml=random.uniform(0, 5000) if random.random() > 0.3 else None,
                tachycardia=random.choice([True, False]),
                hypotension=random.choice([True, False]),
            )
            assert result["prediction"] in ("positive", "negative")
            assert isinstance(result["decision_path"], list)


@pytest.mark.stress
class TestAdversarialInputs:
    """Test system resilience against adversarial inputs."""

    def test_validator_handles_adversarial_inputs(self):
        """Input validator should not crash on adversarial data."""
        validator = InputValidator()
        random.seed(42)

        for i in range(500):
            data = random_adversarial_input()
            try:
                result = validator.validate(data)
                # Should return a ValidationResult (possibly invalid)
                assert isinstance(result.valid, bool)
                assert isinstance(result.errors, list)
            except Exception as e:
                pytest.fail(
                    f"Validator crashed on adversarial input {data}: {e}"
                )

    def test_normalizer_handles_adversarial_responses(self):
        """ResponseNormalizer should not crash on garbage model outputs."""
        normalizer = ResponseNormalizer()
        adversarial_responses = [
            {},  # empty
            {"risk_score": float("nan")},
            {"risk_score": float("inf")},
            {"risk_score": -999},
            {"risk_score": 999},
            {"risk_score": 0.5, "confidence": float("nan")},
            {"risk_score": 0.5, "severity_distribution": {"grade_1": float("nan")}},
            {"risk_score": 0.5, "time_horizon_hours": -10},
            {"risk_score": 0.5, "time_horizon_hours": "soon"},
            {"risk_score": 0.5, "token_usage": "invalid"},
        ]

        for raw in adversarial_responses:
            try:
                pred = normalizer.normalize(raw, "test-model", 1000)
                # If it succeeded, verify output is sane
                assert 0.0 <= pred.risk_score <= 1.0
                assert 0.0 <= pred.confidence <= 1.0
            except (ValueError, TypeError):
                # Expected for truly invalid inputs (missing risk_score, NaN, etc.)
                pass

    def test_ensemble_handles_extreme_predictions(self):
        """Ensemble should not crash when predictions have extreme values."""
        aggregator = EnsembleAggregator()

        predictions = [
            SafetyPrediction(
                risk_score=0.0, confidence=1.0,
                severity_distribution={"grade_1": 1.0, "grade_2": 0.0, "grade_3": 0.0, "grade_4": 0.0},
                time_horizon=timedelta(hours=72),
                mechanistic_rationale="test",
                pathway_references=[], evidence_sources=[],
                model_id="model_a", latency_ms=1000,
            ),
            SafetyPrediction(
                risk_score=1.0, confidence=1.0,
                severity_distribution={"grade_1": 0.0, "grade_2": 0.0, "grade_3": 0.0, "grade_4": 1.0},
                time_horizon=timedelta(hours=12),
                mechanistic_rationale="test",
                pathway_references=[], evidence_sources=[],
                model_id="model_b", latency_ms=1000,
            ),
        ]

        result = aggregator.aggregate(predictions)
        assert 0.0 <= result.risk_score <= 1.0
        assert result.requires_human_review  # Max disagreement


@pytest.mark.stress
class TestPerformanceBenchmarks:
    """Performance benchmarks for scoring pipeline."""

    def test_all_scorers_100_patients_under_1_second(self):
        """All five scoring models should handle 100 patients in under 1 second total."""
        random.seed(42)

        easix = EASIXScorer()
        hscore = HScoreCalculator()
        hematotox = CARHematotoxScorer()
        teachey = TeacheyModelScorer()
        hay = HayModelScorer()

        start = time.perf_counter()

        for _ in range(100):
            labs = random_valid_labs()

            easix.compute(
                ldh=labs["ldh_u_l"],
                creatinine=labs["creatinine_mg_dl"],
                platelets=labs["platelets_k_ul"],
            )
            hscore.compute(
                temperature_c=labs["temperature_c"],
                ferritin_ng_ml=labs["ferritin_ng_ml"],
                triglycerides_mmol_l=labs["triglycerides_mmol_l"],
                fibrinogen_g_l=labs["fibrinogen_mg_dl"] / 100.0,
                ast_u_l=labs["ast_u_l"],
            )
            hematotox.compute(
                anc_k_ul=labs["anc_k_ul"],
                hemoglobin_g_dl=labs["hemoglobin_g_dl"],
                platelets_k_ul=labs["platelets_k_ul"],
                crp_mg_l=labs["crp_mg_l"],
                ferritin_ng_ml=labs["ferritin_ng_ml"],
            )
            teachey.compute(
                ifn_gamma_pg_ml=labs["ifn_gamma_pg_ml"],
                sgp130_ng_ml=random.uniform(10, 5000),
                il1ra_pg_ml=random.uniform(10, 10000),
            )
            hay.compute(
                fever_present=labs["temperature_c"] > 38.0,
                fever_onset_hours=random.uniform(6, 72),
                mcp1_pg_ml=random.uniform(100, 3000),
                tachycardia=random.choice([True, False]),
            )

        elapsed = time.perf_counter() - start
        assert elapsed < 1.0, f"All scorers for 100 patients took {elapsed:.2f}s (>1s)"


@pytest.mark.stress
class TestMemoryStability:
    """Test for memory leaks under sustained load."""

    def test_no_memory_leak_10000_iterations(self):
        """Run 10,000 scoring iterations and verify no resource exhaustion.

        We verify this by checking that the loop completes without error
        and that output remains consistent after many iterations.
        """
        scorer = EASIXScorer()
        random.seed(42)

        first_result = None
        last_result = None

        for i in range(10000):
            labs = random_valid_labs()
            result = scorer.compute(
                ldh=labs["ldh_u_l"],
                creatinine=labs["creatinine_mg_dl"],
                platelets=labs["platelets_k_ul"],
            )

            if i == 0:
                first_result = result
            last_result = result

        # If we got here, no memory issues caused a crash
        assert first_result is not None
        assert last_result is not None

        # Verify the scorer still produces valid results
        verify_result = scorer.compute(ldh=200, creatinine=1.0, platelets=200)
        assert verify_result["score"] == pytest.approx(1.0)

    def test_validator_10000_iterations(self):
        """Run 10,000 validation passes."""
        validator = InputValidator()
        random.seed(42)

        for i in range(10000):
            labs = random_valid_labs()
            result = validator.validate(labs)
            assert isinstance(result.valid, bool)

        # Verify still works correctly
        result = validator.validate({"crp_mg_l": 10.0})
        assert result.valid
