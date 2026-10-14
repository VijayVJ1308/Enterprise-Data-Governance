"""
Phase 19: Real-time Streaming Quality Alert Engine.
Inspects streaming Kafka events on-the-wire, detects schema and business rule
violations, publishes alerts to enterprise.quality.alerts topic, and formats
external dispatch payloads (Slack, PagerDuty, Email).
"""

import re
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

from kafka.config import KafkaConfig
from kafka.message import StreamMessage
from kafka.broker import StreamingBroker


@dataclass
class QualityAlert:
    """Represents a real-time data quality violation detected on a Kafka topic."""

    alert_id: str
    rule_code: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    topic: str
    record_id: str
    dimension: str
    description: str
    payload_snapshot: Dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StreamingAlertEngine:
    """Evaluates wire-level assertions against streaming messages and dispatches alerts."""

    EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    def __init__(
        self,
        config: Optional[KafkaConfig] = None,
        broker: Optional[StreamingBroker] = None,
    ):
        self.config = config or KafkaConfig()
        self.broker = broker or StreamingBroker()
        self.dispatched_alerts: List[QualityAlert] = []

    def inspect_crm_message(self, message: StreamMessage) -> List[QualityAlert]:
        """Validate CRM customer streaming events on the wire."""
        alerts: List[QualityAlert] = []
        val = message.value or {}

        # 1. Completeness: customer_id
        cust_id = val.get("customer_id")
        if not cust_id:
            alerts.append(
                QualityAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                    rule_code="STREAM_COMP_CUSTOMER_ID",
                    severity="CRITICAL",
                    topic=message.topic,
                    record_id="UNKNOWN",
                    dimension="completeness",
                    description="Streaming CRM record missing required 'customer_id' primary identifier.",
                    payload_snapshot=val,
                )
            )
            return alerts

        data = val.get("data", {})
        # 2. Validity: Email format if present
        email = data.get("email")
        if email and not self.EMAIL_REGEX.match(str(email)):
            alerts.append(
                QualityAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                    rule_code="STREAM_VAL_INVALID_EMAIL",
                    severity="HIGH",
                    topic=message.topic,
                    record_id=str(cust_id),
                    dimension="validity",
                    description=f"Invalid email pattern detected on wire: '{email}'",
                    payload_snapshot=val,
                )
            )

        return alerts

    def inspect_erp_message(self, message: StreamMessage) -> List[QualityAlert]:
        """Validate ERP transaction settlements on the wire."""
        alerts: List[QualityAlert] = []
        val = message.value or {}

        txn_id = val.get("txn_id")
        if not txn_id:
            alerts.append(
                QualityAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                    rule_code="STREAM_COMP_TXN_ID",
                    severity="CRITICAL",
                    topic=message.topic,
                    record_id="UNKNOWN",
                    dimension="completeness",
                    description="Streaming ERP transaction missing mandatory 'txn_id'.",
                    payload_snapshot=val,
                )
            )
            return alerts

        # Business Rule: Negative amount without prior credit note authorization
        amount = val.get("amount_usd")
        if amount is not None:
            try:
                num_amount = float(amount)
                if num_amount < 0:
                    alerts.append(
                        QualityAlert(
                            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                            rule_code="STREAM_VAL_NEGATIVE_AMOUNT",
                            severity="CRITICAL",
                            topic=message.topic,
                            record_id=str(txn_id),
                            dimension="validity",
                            description=f"Negative financial settlement detected on wire: {num_amount} USD",
                            payload_snapshot=val,
                        )
                    )
            except (ValueError, TypeError):
                alerts.append(
                    QualityAlert(
                        alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                        rule_code="STREAM_VAL_NON_NUMERIC_AMOUNT",
                        severity="HIGH",
                        topic=message.topic,
                        record_id=str(txn_id),
                        dimension="validity",
                        description=f"Non-numeric transaction amount detected: '{amount}'",
                        payload_snapshot=val,
                    )
                )

        # Currency code format check (ISO 4217: 3 uppercase letters)
        currency = val.get("currency")
        if currency and (len(str(currency)) != 3 or not str(currency).isupper()):
            alerts.append(
                QualityAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                    rule_code="STREAM_CONS_CURRENCY_ISO",
                    severity="MEDIUM",
                    topic=message.topic,
                    record_id=str(txn_id),
                    dimension="consistency",
                    description=f"Non-ISO currency code detected on wire: '{currency}'",
                    payload_snapshot=val,
                )
            )

        return alerts

    def inspect_ecommerce_message(self, message: StreamMessage) -> List[QualityAlert]:
        """Validate Ecommerce orders on the wire."""
        alerts: List[QualityAlert] = []
        val = message.value or {}

        order_id = val.get("order_id")
        if not order_id:
            alerts.append(
                QualityAlert(
                    alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                    rule_code="STREAM_COMP_ORDER_ID",
                    severity="CRITICAL",
                    topic=message.topic,
                    record_id="UNKNOWN",
                    dimension="completeness",
                    description="Streaming order missing mandatory 'order_id'.",
                    payload_snapshot=val,
                )
            )
            return alerts

        total_amount = val.get("total_amount")
        if total_amount is not None:
            try:
                if float(total_amount) <= 0:
                    alerts.append(
                        QualityAlert(
                            alert_id=f"ALT-{uuid.uuid4().hex[:8]}",
                            rule_code="STREAM_VAL_ZERO_ORDER_AMOUNT",
                            severity="HIGH",
                            topic=message.topic,
                            record_id=str(order_id),
                            dimension="validity",
                            description=f"Zero or negative order total detected: {total_amount}",
                            payload_snapshot=val,
                        )
                    )
            except (ValueError, TypeError):
                pass

        return alerts

    def inspect_and_publish(self, message: StreamMessage) -> List[QualityAlert]:
        """Inspect any incoming message according to its topic and publish alerts if violations found."""
        detected: List[QualityAlert] = []
        if message.topic == self.config.TOPIC_CRM_EVENTS:
            detected = self.inspect_crm_message(message)
        elif message.topic == self.config.TOPIC_ERP_TRANSACTIONS:
            detected = self.inspect_erp_message(message)
        elif message.topic == self.config.TOPIC_ECOMMERCE_ORDERS:
            detected = self.inspect_ecommerce_message(message)

        for alert in detected:
            self.dispatched_alerts.append(alert)
            alert_msg = StreamMessage(
                topic=self.config.TOPIC_QUALITY_ALERTS,
                value=alert.to_dict(),
                key=alert.record_id,
                headers={"severity": alert.severity, "rule_code": alert.rule_code},
            )
            self.broker.publish(alert_msg)

        return detected

    @staticmethod
    def format_slack_webhook(alert: QualityAlert, channel: str = "#data-quality-alerts") -> Dict[str, Any]:
        """Format Slack Block Kit webhook payload for real-time channel alerting."""
        color = "#ef4444" if alert.severity == "CRITICAL" else "#f59e0b" if alert.severity == "HIGH" else "#3b82f6"
        return {
            "channel": channel,
            "attachments": [
                {
                    "color": color,
                    "title": f"🚨 Data Quality Alert: {alert.rule_code} [{alert.severity}]",
                    "text": alert.description,
                    "fields": [
                        {"title": "Topic", "value": alert.topic, "short": True},
                        {"title": "Record ID", "value": alert.record_id, "short": True},
                        {"title": "Dimension", "value": alert.dimension.upper(), "short": True},
                        {"title": "Timestamp", "value": alert.timestamp, "short": True},
                    ],
                    "footer": "AegisData Streaming Observability Engine",
                }
            ],
        }

    @staticmethod
    def format_pagerduty_incident(alert: QualityAlert, service_key: str = "PAGERDUTY_KEY_PLACEHOLDER") -> Dict[str, Any]:
        """Format PagerDuty Events API v2 incident payload."""
        pd_severity = "critical" if alert.severity == "CRITICAL" else "error" if alert.severity == "HIGH" else "warning"
        return {
            "routing_key": service_key,
            "event_action": "trigger",
            "dedup_key": f"{alert.topic}:{alert.record_id}:{alert.rule_code}",
            "payload": {
                "summary": f"{alert.rule_code} violation in {alert.topic}: {alert.description}",
                "source": alert.topic,
                "severity": pd_severity,
                "custom_details": {
                    "alert_id": alert.alert_id,
                    "dimension": alert.dimension,
                    "record_id": alert.record_id,
                    "payload_snapshot": alert.payload_snapshot,
                },
            },
        }

    @staticmethod
    def format_email_alert(alert: QualityAlert, recipients: Optional[List[str]] = None) -> Dict[str, Any]:
        """Format email notification payload."""
        rcpt = recipients or ["data-governance@enterprise.org", "oncall-steward@enterprise.org"]
        return {
            "to": rcpt,
            "subject": f"[{alert.severity}] Streaming Quality Alert: {alert.rule_code} on {alert.topic}",
            "body": f"""
ALERT IDENTIFIER: {alert.alert_id}
SEVERITY: {alert.severity}
DIMENSION: {alert.dimension.upper()}
TOPIC: {alert.topic}
RECORD IDENTIFIER: {alert.record_id}
DESCRIPTION: {alert.description}
TIMESTAMP: {alert.timestamp}

Payload Sample:
{alert.payload_snapshot}
            """.strip(),
        }
