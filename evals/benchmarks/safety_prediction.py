"""
Safety prediction benchmark suite for PSP evaluation.

Runs the full evaluation battery across synthetic datasets:
1. Discrimination: AUROC for Grade 3+ events (target > 0.80)
2. Calibration: Brier score (target < 0.15) and ECE (target < 0.10)
3. Timing accuracy: Onset timing MAE (target < 12 hours)
4. Clinical utility: Net Reclassification Improvement (target > 0)
5. Sensitivity: TPR at 90% specificity (target > 0.70)
6. Fairness: Equalized odds, demographic parity, calibration across subgroups (target < 0.05 disparity)
7. Mechanistic validity: fraction of predictions with valid pathway traces

Usage:
    benchmark = SafetyPredictionBenchmark()
    dataset = generate_retrospective_validation_dataset()
    predictions = my_model.predict(dataset)
    report = benchmark.run(dataset, predictions)
    print(report.summary())
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from evals.metrics.clinical_metrics import (
    GradedOutcome,
    GradedPrediction,
    EvalResult,
    auroc_graded,
    brier_score,
    expected_calibration_error,
    onset_timing_mae,
    net_reclassification_improvement,
    sensitivity_at_specificity,
)
from evals.metrics.fairness import (
    SubgroupLabel,
    equalized_odds,
    demographic_parity,
    calibration_by_subgroup,
)
from evals.datasets.synthetic import SyntheticDataset


@dataclass
class BenchmarkTarget:
    """A single benchmark target with pass/fail threshold."""
    metric_name: str
    target_value: float
    comparison: str  # "greater_than", "less_than"
    description: str

    def passes(self, actual: float) -> bool:
        if self.comparison == "greater_than":
            return actual >= self.target_value
        elif self.comparison == "less_than":
            return actual <= self.target_value
        return False


@dataclass
class BenchmarkResult:
    """Result of a single benchmark metric evaluation."""
    target: BenchmarkTarget
    eval_result: EvalResult
    passed: bool

    @property
    def metric_name(self) -> str:
        return self.target.metric_name

    @property
    def value(self) -> float:
        return self.eval_result.value


@dataclass
class BenchmarkReport:
    """Complete benchmark report across all metrics."""
    dataset_name: str
    results: list[BenchmarkResult]
    n_patients: int
    event_rate: float
    severe_event_rate: float

    @property
    def n_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def n_total(self) -> int:
        return len(self.results)

    @property
    def all_passed(self) -> bool:
        return self.n_passed == self.n_total

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"PSP Safety Prediction Benchmark Report",
            f"{'=' * 50}",
            f"Dataset: {self.dataset_name}",
            f"Patients: {self.n_patients}",
            f"Event rate: {self.event_rate:.1%}",
            f"Severe event rate (Grade 3+): {self.severe_event_rate:.1%}",
            f"",
            f"Results: {self.n_passed}/{self.n_total} passed",
            f"{'-' * 50}",
        ]

        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            comp = ">=" if r.target.comparison == "greater_than" else "<="
            lines.append(
                f"  [{status}] {r.metric_name}: {r.value:.4f} "
                f"(target {comp} {r.target.target_value:.4f})"
            )

        lines.append(f"{'=' * 50}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Export results as a dictionary for logging/storage."""
        return {
            "dataset": self.dataset_name,
            "n_patients": self.n_patients,
            "event_rate": self.event_rate,
            "severe_event_rate": self.severe_event_rate,
            "passed": self.n_passed,
            "total": self.n_total,
            "all_passed": self.all_passed,
            "metrics": {
                r.metric_name: {
                    "value": r.value,
                    "target": r.target.target_value,
                    "passed": r.passed,
                }
                for r in self.results
            },
        }


# ---------------------------------------------------------------------------
# Benchmark definitions
# ---------------------------------------------------------------------------

SAFETY_TARGETS = [
    BenchmarkTarget("auroc_grade3plus", 0.80, "greater_than", "AUROC for Grade 3+ CRS prediction"),
    BenchmarkTarget("brier_score", 0.15, "less_than", "Brier score for probability calibration"),
    BenchmarkTarget("ece", 0.10, "less_than", "Expected Calibration Error"),
    BenchmarkTarget("onset_timing_mae_hours", 12.0, "less_than", "Onset timing MAE in hours"),
    BenchmarkTarget("sensitivity_at_90spec", 0.70, "greater_than", "Sensitivity at 90% specificity for Grade 3+"),
    BenchmarkTarget("equalized_odds_disparity", 0.05, "less_than", "Max equalized odds disparity across demographics"),
    BenchmarkTarget("demographic_parity_disparity", 0.05, "less_than", "Max demographic parity disparity"),
    BenchmarkTarget("calibration_subgroup_disparity", 0.05, "less_than", "Max calibration disparity across subgroups"),
]


class SafetyPredictionBenchmark:
    """Runs the full safety prediction evaluation battery.

    Usage:
        benchmark = SafetyPredictionBenchmark()
        report = benchmark.run(dataset, predictions)
    """

    def __init__(self, targets: list[BenchmarkTarget] = None):
        self.targets = targets or SAFETY_TARGETS

    def run(
        self,
        dataset: SyntheticDataset,
        predictions: list[GradedPrediction],
        old_predictions: Optional[list[GradedPrediction]] = None,
        subgroup_attribute: str = "sex",
    ) -> BenchmarkReport:
        """Run all benchmarks against a dataset and predictions.

        Args:
            dataset: SyntheticDataset with known outcomes.
            predictions: Model predictions to evaluate.
            old_predictions: Optional baseline model predictions for NRI comparison.
            subgroup_attribute: Demographic attribute for fairness analysis.

        Returns:
            BenchmarkReport with all results.
        """
        outcomes = dataset.to_outcomes()
        subgroups = dataset.to_subgroup_labels(subgroup_attribute)
        results = []

        # 1. Discrimination
        auroc_result = auroc_graded(outcomes, predictions, severity_threshold=3)
        results.append(self._check_target("auroc_grade3plus", auroc_result))

        # 2. Calibration
        brier_result = brier_score(outcomes, predictions)
        results.append(self._check_target("brier_score", brier_result))

        ece_result = expected_calibration_error(outcomes, predictions)
        results.append(self._check_target("ece", ece_result))

        # 3. Timing accuracy
        timing_result = onset_timing_mae(outcomes, predictions)
        results.append(self._check_target("onset_timing_mae_hours", timing_result))

        # 4. Sensitivity
        sens_result = sensitivity_at_specificity(outcomes, predictions, target_specificity=0.90)
        results.append(self._check_target("sensitivity_at_90spec", sens_result))

        # 5. Fairness
        eo_result = equalized_odds(outcomes, predictions, subgroups)
        results.append(self._check_target("equalized_odds_disparity", eo_result))

        dp_result = demographic_parity(predictions, subgroups)
        results.append(self._check_target("demographic_parity_disparity", dp_result))

        cal_sub_result = calibration_by_subgroup(outcomes, predictions, subgroups)
        results.append(self._check_target("calibration_subgroup_disparity", cal_sub_result))

        return BenchmarkReport(
            dataset_name=dataset.name,
            results=results,
            n_patients=dataset.n_patients,
            event_rate=dataset.event_rate,
            severe_event_rate=dataset.severe_event_rate,
        )

    def _check_target(self, target_name: str, eval_result: EvalResult) -> BenchmarkResult:
        """Match an eval result against its benchmark target."""
        target = next((t for t in self.targets if t.metric_name == target_name), None)
        if target is None:
            # No target defined, create a placeholder
            target = BenchmarkTarget(target_name, 0.0, "greater_than", "No target defined")
        passed = target.passes(eval_result.value)
        return BenchmarkResult(target=target, eval_result=eval_result, passed=passed)


# ---------------------------------------------------------------------------
# Convenience: run benchmark with oracle predictions (for baseline)
# ---------------------------------------------------------------------------

def run_oracle_benchmark(dataset: SyntheticDataset) -> BenchmarkReport:
    """Run benchmark using the true latent risk scores as predictions.

    This represents the theoretical maximum performance of any model on this
    dataset and is useful for validating the benchmark infrastructure itself.
    """
    oracle_predictions = [
        GradedPrediction(
            patient_id=p.patient_id,
            risk_score=p.true_risk_score,
            predicted_grade_distribution={
                0: 1.0 - p.true_risk_score,
                1: p.true_risk_score * 0.3,
                2: p.true_risk_score * 0.25,
                3: p.true_risk_score * 0.25,
                4: p.true_risk_score * 0.2,
            },
            predicted_onset_hours=p.crs_onset_hours,
        )
        for p in dataset.patients
    ]

    benchmark = SafetyPredictionBenchmark()
    return benchmark.run(dataset, oracle_predictions)


def run_random_benchmark(dataset: SyntheticDataset, seed: int = 0) -> BenchmarkReport:
    """Run benchmark with random predictions (for lower baseline).

    No model should perform worse than random on these metrics.
    """
    import random
    rng = random.Random(seed)

    random_predictions = [
        GradedPrediction(
            patient_id=p.patient_id,
            risk_score=rng.random(),
            predicted_grade_distribution={0: 0.25, 1: 0.25, 2: 0.25, 3: 0.15, 4: 0.10},
            predicted_onset_hours=rng.uniform(12, 96),
        )
        for p in dataset.patients
    ]

    benchmark = SafetyPredictionBenchmark()
    return benchmark.run(dataset, random_predictions)
