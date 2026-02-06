"""
Alert engine for clinical safety monitoring.

Generates, prioritizes, and manages safety alerts based on Safety Index
thresholds, rate-of-change detection, and configurable escalation rules.
Designed for integration with clinical monitoring systems.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Callable

from src.safety_index.index import AdverseEventType, RiskCategory, SafetyIndex

logger = logging.getLogger(__name__)


class AlertSeverity(IntEnum):
    """Alert severity levels (aligned with clinical urgency)."""

    INFO = 0          # Informational, no action required
    WARNING = 1       # Attention needed, non-urgent
    URGENT = 2        # Requires prompt clinical review
    CRITICAL = 3      # Requires immediate intervention


class AlertType(Enum):
    """Categories of safety alerts."""

    THRESHOLD_BREACH = "threshold_breach"       # Score crossed a threshold
    RATE_OF_CHANGE = "rate_of_change"           # Score changing rapidly
    GRADE_ESCALATION = "grade_escalation"       # Predicted grade increased
    MODEL_DISAGREEMENT = "model_disagreement"   # Models disagree significantly
    VALIDATION_FAILURE = "validation_failure"    # Mechanistic validation failed
    TREND_WORSENING = "trend_worsening"         # Sustained worsening trend
    BIOMARKER_SPIKE = "biomarker_spike"         # Single biomarker rapid rise


class AlertStatus(Enum):
    """Lifecycle status of an alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertThresholdConfig:
    """Configuration for threshold-based alerts.

    Attributes:
        adverse_event: Which AE this threshold applies to.
        warning_threshold: Score that triggers a WARNING alert.
        urgent_threshold: Score that triggers an URGENT alert.
        critical_threshold: Score that triggers a CRITICAL alert.
        rate_of_change_threshold: Score change per hour that triggers an alert.
        cooldown_seconds: Minimum time between repeat alerts for the same patient/event.
    """

    adverse_event: AdverseEventType
    warning_threshold: float = 0.4
    urgent_threshold: float = 0.6
    critical_threshold: float = 0.8
    rate_of_change_threshold: float = 0.05  # per hour
    cooldown_seconds: float = 1800.0  # 30 minutes


@dataclass
class Alert:
    """A safety alert.

    Attributes:
        alert_id: Unique identifier.
        patient_id: The patient this alert concerns.
        adverse_event: The adverse event type.
        alert_type: Category of the alert.
        severity: How urgent the alert is.
        status: Current lifecycle status.
        title: Short alert title.
        message: Detailed alert message.
        safety_index_score: The Safety Index score that triggered the alert.
        trigger_value: The specific value that triggered the alert.
        threshold_value: The threshold that was breached.
        recommended_actions: Clinical actions to consider.
        created_at: When the alert was created.
        acknowledged_at: When the alert was acknowledged.
        resolved_at: When the alert was resolved.
        acknowledged_by: Who acknowledged the alert.
        metadata: Additional context.
    """

    alert_id: str
    patient_id: str
    adverse_event: AdverseEventType
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    title: str = ""
    message: str = ""
    safety_index_score: float = 0.0
    trigger_value: float = 0.0
    threshold_value: float = 0.0
    recommended_actions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    acknowledged_by: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EscalationRule:
    """Rule for escalating an unacknowledged alert.

    Attributes:
        after_minutes: Minutes after alert creation to escalate.
        escalate_to_severity: New severity after escalation.
        notify_roles: Additional roles to notify upon escalation.
        message_suffix: Text appended to the alert message.
    """

    after_minutes: float
    escalate_to_severity: AlertSeverity
    notify_roles: list[str] = field(default_factory=list)
    message_suffix: str = ""


# Type alias for alert handlers
AlertHandler = Callable[[Alert], None]


class AlertEngine:
    """Generates and manages clinical safety alerts.

    Features:
        - **Configurable thresholds**: Per-AE threshold and rate-of-change alerts.
        - **Escalation rules**: Unacknowledged alerts automatically escalate.
        - **Rate-of-change detection**: Alerts on rapid score increases.
        - **Cooldown**: Prevents alert fatigue from repeated triggers.
        - **Handler registration**: Pluggable alert delivery (webhook, SMS, etc.).

    Usage::

        engine = AlertEngine()
        engine.configure_thresholds(AlertThresholdConfig(
            adverse_event=AdverseEventType.CRS,
            critical_threshold=0.8,
        ))
        engine.register_handler(my_webhook_handler)

        alerts = engine.evaluate(safety_index)
    """

    def __init__(self) -> None:
        """Initialize the alert engine."""
        self._thresholds: dict[AdverseEventType, AlertThresholdConfig] = {}
        self._escalation_rules: list[EscalationRule] = self._default_escalation_rules()
        self._active_alerts: dict[str, Alert] = {}  # alert_id -> Alert
        self._alert_counter = 0
        self._handlers: list[AlertHandler] = []

        # Cooldown tracking: (patient_id, adverse_event, alert_type) -> last_alert_time
        self._cooldowns: dict[tuple[str, str, str], float] = {}

        # History for rate-of-change detection
        self._score_history: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def configure_thresholds(self, config: AlertThresholdConfig) -> None:
        """Set threshold configuration for an adverse event type.

        Args:
            config: The threshold configuration.
        """
        self._thresholds[config.adverse_event] = config
        logger.info(
            "Configured alert thresholds for %s: warn=%.2f, urgent=%.2f, critical=%.2f",
            config.adverse_event.value, config.warning_threshold,
            config.urgent_threshold, config.critical_threshold,
        )

    def set_escalation_rules(self, rules: list[EscalationRule]) -> None:
        """Override the default escalation rules.

        Args:
            rules: New escalation rules.
        """
        self._escalation_rules = rules

    def register_handler(self, handler: AlertHandler) -> None:
        """Register a handler that will be called for each new alert.

        Args:
            handler: A callable that receives an Alert object.
        """
        self._handlers.append(handler)

    # ------------------------------------------------------------------
    # Alert evaluation
    # ------------------------------------------------------------------

    def evaluate(self, safety_index: SafetyIndex) -> list[Alert]:
        """Evaluate a Safety Index and generate any warranted alerts.

        Args:
            safety_index: The patient's current Safety Index.

        Returns:
            List of new alerts generated (may be empty).
        """
        config = self._thresholds.get(safety_index.adverse_event)
        if config is None:
            # Use default thresholds
            config = AlertThresholdConfig(adverse_event=safety_index.adverse_event)

        alerts: list[Alert] = []

        # 1. Threshold-based alerts
        threshold_alert = self._check_thresholds(safety_index, config)
        if threshold_alert is not None:
            alerts.append(threshold_alert)

        # 2. Rate-of-change alerts
        roc_alert = self._check_rate_of_change(safety_index, config)
        if roc_alert is not None:
            alerts.append(roc_alert)

        # 3. Model disagreement alerts
        if safety_index.model_agreement < 0.6:
            disagreement_alert = self._create_disagreement_alert(safety_index)
            if disagreement_alert is not None:
                alerts.append(disagreement_alert)

        # 4. Trend worsening alerts
        trend_alert = self._check_trend(safety_index)
        if trend_alert is not None:
            alerts.append(trend_alert)

        # Dispatch alerts to handlers
        for alert in alerts:
            self._active_alerts[alert.alert_id] = alert
            for handler in self._handlers:
                try:
                    handler(alert)
                except Exception:
                    logger.exception("Alert handler failed for %s", alert.alert_id)

        # Update score history
        key = (safety_index.patient_id, safety_index.adverse_event.value)
        self._score_history[key].append(
            (safety_index.composite_score, time.time())
        )

        # Check escalation of existing alerts
        self._process_escalations()

        return alerts

    # ------------------------------------------------------------------
    # Alert management
    # ------------------------------------------------------------------

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Mark an alert as acknowledged.

        Args:
            alert_id: The alert to acknowledge.
            acknowledged_by: Identifier of the acknowledging user.

        Returns:
            True if the alert was found and acknowledged.
        """
        alert = self._active_alerts.get(alert_id)
        if alert is None:
            return False

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        logger.info("Alert %s acknowledged by %s", alert_id, acknowledged_by)
        return True

    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved.

        Args:
            alert_id: The alert to resolve.

        Returns:
            True if the alert was found and resolved.
        """
        alert = self._active_alerts.get(alert_id)
        if alert is None:
            return False

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()

        logger.info("Alert %s resolved", alert_id)
        return True

    def get_active_alerts(
        self,
        patient_id: str | None = None,
        min_severity: AlertSeverity = AlertSeverity.INFO,
    ) -> list[Alert]:
        """Get all active (unresolved) alerts.

        Args:
            patient_id: Optional filter by patient.
            min_severity: Minimum severity to include.

        Returns:
            List of active alerts sorted by severity (highest first).
        """
        alerts = [
            a for a in self._active_alerts.values()
            if a.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)
            and a.severity >= min_severity
        ]
        if patient_id:
            alerts = [a for a in alerts if a.patient_id == patient_id]
        alerts.sort(key=lambda a: a.severity, reverse=True)
        return alerts

    # ------------------------------------------------------------------
    # Internal check methods
    # ------------------------------------------------------------------

    def _check_thresholds(
        self,
        si: SafetyIndex,
        config: AlertThresholdConfig,
    ) -> Alert | None:
        """Check if the Safety Index crosses any threshold."""
        severity: AlertSeverity | None = None
        threshold = 0.0

        if si.composite_score >= config.critical_threshold:
            severity = AlertSeverity.CRITICAL
            threshold = config.critical_threshold
        elif si.composite_score >= config.urgent_threshold:
            severity = AlertSeverity.URGENT
            threshold = config.urgent_threshold
        elif si.composite_score >= config.warning_threshold:
            severity = AlertSeverity.WARNING
            threshold = config.warning_threshold
        else:
            return None

        # Check cooldown
        if self._is_on_cooldown(
            si.patient_id, si.adverse_event, AlertType.THRESHOLD_BREACH, config,
        ):
            return None

        recommended_actions = self._get_recommended_actions(
            si.adverse_event, severity,
        )

        return self._create_alert(
            patient_id=si.patient_id,
            adverse_event=si.adverse_event,
            alert_type=AlertType.THRESHOLD_BREACH,
            severity=severity,
            title=(
                f"{severity.name} - {si.adverse_event.value} Safety Index "
                f"at {si.composite_score:.2f}"
            ),
            message=(
                f"Patient {si.patient_id}: {si.adverse_event.value} Safety Index "
                f"({si.composite_score:.3f}) has crossed the {severity.name} "
                f"threshold ({threshold:.2f}). "
                f"Risk category: {si.risk_category.value}. "
                f"Hours since infusion: {si.hours_since_infusion:.1f}."
            ),
            safety_index_score=si.composite_score,
            trigger_value=si.composite_score,
            threshold_value=threshold,
            recommended_actions=recommended_actions,
        )

    def _check_rate_of_change(
        self,
        si: SafetyIndex,
        config: AlertThresholdConfig,
    ) -> Alert | None:
        """Check if the Safety Index is changing rapidly."""
        if abs(si.trend) < config.rate_of_change_threshold:
            return None

        if si.trend <= 0:
            return None  # Only alert on worsening

        if self._is_on_cooldown(
            si.patient_id, si.adverse_event, AlertType.RATE_OF_CHANGE, config,
        ):
            return None

        severity = AlertSeverity.WARNING
        if si.trend > config.rate_of_change_threshold * 3:
            severity = AlertSeverity.CRITICAL
        elif si.trend > config.rate_of_change_threshold * 2:
            severity = AlertSeverity.URGENT

        return self._create_alert(
            patient_id=si.patient_id,
            adverse_event=si.adverse_event,
            alert_type=AlertType.RATE_OF_CHANGE,
            severity=severity,
            title=(
                f"Rapid {si.adverse_event.value} risk increase: "
                f"+{si.trend:.4f}/hr"
            ),
            message=(
                f"Patient {si.patient_id}: {si.adverse_event.value} Safety Index "
                f"is increasing at {si.trend:.4f}/hr (threshold: "
                f"{config.rate_of_change_threshold:.4f}/hr). "
                f"Current score: {si.composite_score:.3f}."
            ),
            safety_index_score=si.composite_score,
            trigger_value=si.trend,
            threshold_value=config.rate_of_change_threshold,
            recommended_actions=[
                "Increase biomarker monitoring frequency",
                "Review cytokine trajectory for accelerating pattern",
                "Prepare intervention protocol",
            ],
        )

    def _create_disagreement_alert(
        self,
        si: SafetyIndex,
    ) -> Alert | None:
        """Create an alert for significant model disagreement."""
        cooldown_key = (
            si.patient_id,
            si.adverse_event.value,
            AlertType.MODEL_DISAGREEMENT.value,
        )
        if cooldown_key in self._cooldowns:
            if time.time() - self._cooldowns[cooldown_key] < 3600:  # 1 hour cooldown
                return None

        self._cooldowns[cooldown_key] = time.time()

        return self._create_alert(
            patient_id=si.patient_id,
            adverse_event=si.adverse_event,
            alert_type=AlertType.MODEL_DISAGREEMENT,
            severity=AlertSeverity.WARNING,
            title=(
                f"Model disagreement for {si.adverse_event.value} "
                f"(agreement: {si.model_agreement:.0%})"
            ),
            message=(
                f"Patient {si.patient_id}: Foundation models disagree on "
                f"{si.adverse_event.value} risk. Agreement: {si.model_agreement:.0%}. "
                f"Ensemble score: {si.composite_score:.3f}. "
                f"Clinical judgment should guide decision-making."
            ),
            safety_index_score=si.composite_score,
            trigger_value=si.model_agreement,
            threshold_value=0.6,
            recommended_actions=[
                "Review individual model predictions",
                "Prioritize biomarker data over model predictions",
                "Consider requesting additional clinical data",
            ],
        )

    def _check_trend(self, si: SafetyIndex) -> Alert | None:
        """Check for sustained worsening trend."""
        key = (si.patient_id, si.adverse_event.value)
        history = self._score_history.get(key, [])

        if len(history) < 3:
            return None

        # Check last 3 scores are monotonically increasing
        recent = history[-3:]
        if all(recent[i][0] < recent[i + 1][0] for i in range(len(recent) - 1)):
            total_increase = recent[-1][0] - recent[0][0]
            if total_increase > 0.1:  # Significant sustained increase
                cooldown_key = (
                    si.patient_id,
                    si.adverse_event.value,
                    AlertType.TREND_WORSENING.value,
                )
                if cooldown_key in self._cooldowns:
                    if time.time() - self._cooldowns[cooldown_key] < 3600:
                        return None
                self._cooldowns[cooldown_key] = time.time()

                return self._create_alert(
                    patient_id=si.patient_id,
                    adverse_event=si.adverse_event,
                    alert_type=AlertType.TREND_WORSENING,
                    severity=AlertSeverity.URGENT,
                    title=(
                        f"Sustained worsening: {si.adverse_event.value} score "
                        f"increased {total_increase:.3f} over last 3 assessments"
                    ),
                    message=(
                        f"Patient {si.patient_id}: {si.adverse_event.value} Safety "
                        f"Index has been consistently worsening. "
                        f"Score trajectory: {' -> '.join(f'{s:.3f}' for s, _ in recent)}. "
                        f"Total increase: {total_increase:.3f}."
                    ),
                    safety_index_score=si.composite_score,
                    trigger_value=total_increase,
                    threshold_value=0.1,
                    recommended_actions=[
                        "Clinical team review of patient trajectory",
                        "Consider preemptive intervention",
                        "Increase monitoring frequency to q4h or more",
                    ],
                )
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_alert(self, **kwargs: Any) -> Alert:
        """Create a new alert with a unique ID."""
        self._alert_counter += 1
        alert_id = f"ALERT-{self._alert_counter:08d}"
        return Alert(alert_id=alert_id, **kwargs)

    def _is_on_cooldown(
        self,
        patient_id: str,
        adverse_event: AdverseEventType,
        alert_type: AlertType,
        config: AlertThresholdConfig,
    ) -> bool:
        """Check if an alert type is on cooldown for a patient."""
        key = (patient_id, adverse_event.value, alert_type.value)
        last_time = self._cooldowns.get(key)
        if last_time is None:
            self._cooldowns[key] = time.time()
            return False
        if time.time() - last_time < config.cooldown_seconds:
            return True
        self._cooldowns[key] = time.time()
        return False

    def _process_escalations(self) -> None:
        """Process escalation rules for active unacknowledged alerts."""
        now = datetime.utcnow()
        for alert in self._active_alerts.values():
            if alert.status != AlertStatus.ACTIVE:
                continue
            for rule in self._escalation_rules:
                elapsed_minutes = (now - alert.created_at).total_seconds() / 60.0
                if (
                    elapsed_minutes >= rule.after_minutes
                    and alert.severity < rule.escalate_to_severity
                ):
                    old_severity = alert.severity
                    alert.severity = rule.escalate_to_severity
                    if rule.message_suffix:
                        alert.message += f" {rule.message_suffix}"
                    logger.warning(
                        "Alert %s escalated from %s to %s after %.0f minutes",
                        alert.alert_id, old_severity.name,
                        alert.severity.name, elapsed_minutes,
                    )

    @staticmethod
    def _default_escalation_rules() -> list[EscalationRule]:
        """Return default escalation rules."""
        return [
            EscalationRule(
                after_minutes=15,
                escalate_to_severity=AlertSeverity.URGENT,
                notify_roles=["charge_nurse"],
                message_suffix="[ESCALATED: unacknowledged for 15 min]",
            ),
            EscalationRule(
                after_minutes=30,
                escalate_to_severity=AlertSeverity.CRITICAL,
                notify_roles=["attending_physician", "charge_nurse"],
                message_suffix="[ESCALATED: unacknowledged for 30 min]",
            ),
        ]

    @staticmethod
    def _get_recommended_actions(
        adverse_event: AdverseEventType,
        severity: AlertSeverity,
    ) -> list[str]:
        """Get recommended clinical actions based on AE type and severity."""
        actions: list[str] = []

        if severity >= AlertSeverity.CRITICAL:
            actions.append("Immediate physician bedside evaluation")

        if adverse_event == AdverseEventType.CRS:
            if severity >= AlertSeverity.URGENT:
                actions.append("Consider tocilizumab administration per protocol")
                actions.append("Monitor vitals q1h (BP, SpO2, temperature)")
            if severity >= AlertSeverity.CRITICAL:
                actions.append("Evaluate for vasopressor support")
                actions.append("Consider ICU transfer")
            actions.append("Order stat IL-6, CRP, ferritin levels")

        elif adverse_event == AdverseEventType.ICANS:
            if severity >= AlertSeverity.URGENT:
                actions.append("Perform ICE assessment")
                actions.append("Consider dexamethasone per protocol")
            if severity >= AlertSeverity.CRITICAL:
                actions.append("Evaluate for seizure prophylaxis")
                actions.append("Consider brain imaging")
            actions.append("Neurological checks q2h")

        elif adverse_event == AdverseEventType.HLH:
            if severity >= AlertSeverity.URGENT:
                actions.append("Stat ferritin, D-dimer, fibrinogen, LDH")
                actions.append("Consider anakinra per protocol")
            if severity >= AlertSeverity.CRITICAL:
                actions.append("Evaluate for ruxolitinib")
                actions.append("Consider ICU transfer for organ support")
            actions.append("Monitor for coagulopathy (DIC screen)")

        return actions
