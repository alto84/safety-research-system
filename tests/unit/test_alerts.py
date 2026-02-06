"""
Tests for AlertEngine — threshold detection, rate-of-change alerts, escalation,
and mechanistic trigger evaluation.

The AlertEngine evaluates patient predictions and generates alerts at
INFO / WATCH / WARNING / CRITICAL levels based on absolute risk thresholds,
risk acceleration, and mechanistic pathway activation.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from tests.conftest import (
    AlertLevel,
    Alert,
    AggregatedRisk,
    RiskTrajectory,
    PatientData,
)


# ---------------------------------------------------------------------------
# AlertEngine reference implementation
# ---------------------------------------------------------------------------

class AlertEngine:
    """Real-time safety alert generation and routing."""

    ALERT_DESCRIPTIONS = {
        AlertLevel.INFO: "Risk score updated, within normal range",
        AlertLevel.WATCH: "Risk elevated above baseline, enhanced monitoring recommended",
        AlertLevel.WARNING: "Significant risk increase, clinical review recommended",
        AlertLevel.CRITICAL: "High risk of imminent Grade 3+ event, immediate action",
    }

    def __init__(
        self,
        critical_threshold: float = 0.75,
        warning_threshold: float = 0.50,
        watch_threshold: float = 0.30,
        accel_threshold: float = 0.04,  # 4% per hour
    ):
        self.critical_threshold = critical_threshold
        self.warning_threshold = warning_threshold
        self.watch_threshold = watch_threshold
        self.accel_threshold = accel_threshold
        # In production, trajectories would come from a data store
        self._trajectories: dict[str, RiskTrajectory] = {}
        # Mechanistic trigger conditions (simplified)
        self._mechanistic_triggers: dict[str, list] = {}

    def set_trajectory(self, patient_id: str, trajectory: RiskTrajectory):
        """Set a patient's risk trajectory for rate-of-change evaluation."""
        self._trajectories[patient_id] = trajectory

    def set_mechanistic_triggers(self, patient_id: str, triggers: list[str]):
        """Set mechanistic trigger conditions for a patient."""
        self._mechanistic_triggers[patient_id] = triggers

    def get_trajectory(self, patient_id: str) -> RiskTrajectory:
        """Retrieve a patient's trajectory."""
        return self._trajectories.get(patient_id, RiskTrajectory([], [], 0.0))

    def mechanistic_triggers_met(self, patient_id: str, prediction: AggregatedRisk) -> bool:
        """Check if mechanistic pathway triggers have been met."""
        triggers = self._mechanistic_triggers.get(patient_id, [])
        if not triggers:
            return False
        # Simplified: if any trigger keywords appear in the disagreement_analysis
        # or the risk score exceeds the watch threshold
        return prediction.risk_score > self.watch_threshold and len(triggers) > 0

    def create_alert(self, level: AlertLevel, patient_id: str, prediction: AggregatedRisk) -> Alert:
        """Create an Alert object."""
        return Alert(
            level=level,
            patient_id=patient_id,
            message=self.ALERT_DESCRIPTIONS[level],
            prediction=prediction,
            timestamp=datetime.now(timezone.utc),
        )

    def evaluate(self, patient_id: str, prediction: AggregatedRisk) -> Alert | None:
        """Evaluate a prediction and return an alert if warranted."""
        # 1. Check absolute risk threshold (most severe first)
        if prediction.risk_score >= self.critical_threshold:
            return self.create_alert(AlertLevel.CRITICAL, patient_id, prediction)

        # 2. Check rate of change (risk acceleration)
        trajectory = self.get_trajectory(patient_id)
        if trajectory.acceleration >= self.accel_threshold:
            return self.create_alert(AlertLevel.WARNING, patient_id, prediction)

        # 3. Check mechanistic triggers
        if self.mechanistic_triggers_met(patient_id, prediction):
            return self.create_alert(AlertLevel.WATCH, patient_id, prediction)

        # 4. If risk is above watch threshold but no other trigger, return INFO
        if prediction.risk_score >= self.watch_threshold:
            return self.create_alert(AlertLevel.INFO, patient_id, prediction)

        # No alert warranted
        return None

    def escalate(self, alert: Alert) -> Alert:
        """Escalate an alert to the next level."""
        level_order = [AlertLevel.INFO, AlertLevel.WATCH, AlertLevel.WARNING, AlertLevel.CRITICAL]
        current_idx = level_order.index(alert.level)
        if current_idx < len(level_order) - 1:
            new_level = level_order[current_idx + 1]
            return Alert(
                level=new_level,
                patient_id=alert.patient_id,
                message=self.ALERT_DESCRIPTIONS[new_level],
                prediction=alert.prediction,
                timestamp=datetime.now(timezone.utc),
            )
        return alert  # Already at CRITICAL


# ===========================================================================
# Tests
# ===========================================================================

@pytest.fixture
def engine():
    return AlertEngine()


class TestAbsoluteThresholdAlerts:
    """Tests for alerts triggered by absolute risk score thresholds."""

    def test_critical_threshold_triggers_critical(self, engine):
        pred = AggregatedRisk(risk_score=0.85)
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_exactly_at_critical_threshold(self, engine):
        pred = AggregatedRisk(risk_score=0.75)
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL

    def test_just_below_critical_not_critical(self, engine):
        pred = AggregatedRisk(risk_score=0.74)
        alert = engine.evaluate("patient-1", pred)
        # Should not be CRITICAL; may be INFO (above watch=0.30)
        if alert is not None:
            assert alert.level != AlertLevel.CRITICAL

    def test_very_low_risk_no_alert(self, engine):
        pred = AggregatedRisk(risk_score=0.05)
        alert = engine.evaluate("patient-1", pred)
        assert alert is None

    def test_watch_threshold_triggers_info(self, engine):
        """Above watch_threshold but below warning: INFO if no other triggers."""
        pred = AggregatedRisk(risk_score=0.35)
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.INFO

    def test_zero_risk_no_alert(self, engine):
        pred = AggregatedRisk(risk_score=0.0)
        alert = engine.evaluate("patient-1", pred)
        assert alert is None


class TestRateOfChangeAlerts:
    """Tests for alerts triggered by risk acceleration."""

    def test_rapid_acceleration_triggers_warning(self, engine, rapidly_rising_trajectory):
        engine.set_trajectory("patient-1", rapidly_rising_trajectory)
        pred = AggregatedRisk(risk_score=0.60)  # Below critical
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.WARNING

    def test_stable_trajectory_no_warning(self, engine, stable_low_trajectory):
        engine.set_trajectory("patient-1", stable_low_trajectory)
        pred = AggregatedRisk(risk_score=0.10)
        alert = engine.evaluate("patient-1", pred)
        # Low score + low acceleration -> no alert
        assert alert is None

    def test_acceleration_overridden_by_critical_threshold(self, engine, rapidly_rising_trajectory):
        """Critical threshold takes precedence over acceleration-based WARNING."""
        engine.set_trajectory("patient-1", rapidly_rising_trajectory)
        pred = AggregatedRisk(risk_score=0.90)  # Above critical
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL  # Not just WARNING

    def test_no_trajectory_set_no_warning(self, engine):
        """Without trajectory data, rate-of-change check should not trigger."""
        pred = AggregatedRisk(risk_score=0.60)
        alert = engine.evaluate("patient-1", pred)
        # No trajectory => acceleration=0.0 => no WARNING from rate-of-change
        # But 0.60 > watch_threshold=0.30 => INFO
        assert alert is not None
        assert alert.level == AlertLevel.INFO


class TestMechanisticTriggers:
    """Tests for alerts triggered by mechanistic pathway activation."""

    def test_mechanistic_triggers_produce_watch(self, engine):
        engine.set_mechanistic_triggers("patient-1", ["il6_trans_signaling_active"])
        pred = AggregatedRisk(risk_score=0.40)
        alert = engine.evaluate("patient-1", pred)
        assert alert is not None
        assert alert.level == AlertLevel.WATCH

    def test_triggers_without_elevated_risk_no_watch(self, engine):
        """Mechanistic triggers alone should not fire if risk is very low."""
        engine.set_mechanistic_triggers("patient-1", ["il6_trans_signaling_active"])
        pred = AggregatedRisk(risk_score=0.10)  # Below watch threshold
        alert = engine.evaluate("patient-1", pred)
        # Risk is below watch_threshold, so mechanistic_triggers_met returns False
        assert alert is None

    def test_no_triggers_set_no_watch_from_mechanism(self, engine):
        pred = AggregatedRisk(risk_score=0.40)
        alert = engine.evaluate("patient-1", pred)
        # 0.40 > watch_threshold => INFO (no mechanistic -> no WATCH)
        assert alert is not None
        assert alert.level == AlertLevel.INFO


class TestAlertEscalation:
    """Tests for alert escalation logic."""

    def test_info_escalates_to_watch(self, engine):
        alert = Alert(level=AlertLevel.INFO, patient_id="p1", message="test", prediction=AggregatedRisk())
        escalated = engine.escalate(alert)
        assert escalated.level == AlertLevel.WATCH

    def test_watch_escalates_to_warning(self, engine):
        alert = Alert(level=AlertLevel.WATCH, patient_id="p1", message="test", prediction=AggregatedRisk())
        escalated = engine.escalate(alert)
        assert escalated.level == AlertLevel.WARNING

    def test_warning_escalates_to_critical(self, engine):
        alert = Alert(level=AlertLevel.WARNING, patient_id="p1", message="test", prediction=AggregatedRisk())
        escalated = engine.escalate(alert)
        assert escalated.level == AlertLevel.CRITICAL

    def test_critical_cannot_escalate_further(self, engine):
        alert = Alert(level=AlertLevel.CRITICAL, patient_id="p1", message="test", prediction=AggregatedRisk())
        escalated = engine.escalate(alert)
        assert escalated.level == AlertLevel.CRITICAL

    def test_escalated_alert_has_correct_patient(self, engine):
        alert = Alert(level=AlertLevel.INFO, patient_id="p1", message="test", prediction=AggregatedRisk())
        escalated = engine.escalate(alert)
        assert escalated.patient_id == "p1"


class TestAlertStructure:
    """Tests for alert object completeness."""

    def test_alert_has_timestamp(self, engine):
        pred = AggregatedRisk(risk_score=0.85)
        alert = engine.evaluate("patient-1", pred)
        assert alert.timestamp is not None

    def test_alert_has_patient_id(self, engine):
        pred = AggregatedRisk(risk_score=0.85)
        alert = engine.evaluate("patient-1", pred)
        assert alert.patient_id == "patient-1"

    def test_alert_has_prediction_reference(self, engine):
        pred = AggregatedRisk(risk_score=0.85)
        alert = engine.evaluate("patient-1", pred)
        assert alert.prediction is pred

    def test_alert_message_not_empty(self, engine):
        pred = AggregatedRisk(risk_score=0.85)
        alert = engine.evaluate("patient-1", pred)
        assert len(alert.message) > 0


class TestCustomThresholds:
    """Tests with non-default threshold configurations."""

    def test_lower_critical_threshold(self):
        engine = AlertEngine(critical_threshold=0.50)
        pred = AggregatedRisk(risk_score=0.55)
        alert = engine.evaluate("p1", pred)
        assert alert.level == AlertLevel.CRITICAL

    def test_higher_critical_threshold(self):
        engine = AlertEngine(critical_threshold=0.95)
        pred = AggregatedRisk(risk_score=0.90)
        alert = engine.evaluate("p1", pred)
        # 0.90 < 0.95: not critical
        if alert is not None:
            assert alert.level != AlertLevel.CRITICAL

    def test_very_sensitive_acceleration(self):
        engine = AlertEngine(accel_threshold=0.01)
        trajectory = RiskTrajectory(
            timestamps=[datetime(2026, 2, 6, h, 0, 0) for h in range(5)],
            scores=[0.20, 0.22, 0.24, 0.26, 0.28],
            acceleration=0.02,
        )
        engine.set_trajectory("p1", trajectory)
        pred = AggregatedRisk(risk_score=0.28)
        alert = engine.evaluate("p1", pred)
        # acceleration 0.02 > threshold 0.01 -> WARNING
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
