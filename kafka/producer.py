"""
Phase 19: High-throughput Streaming Producer for Enterprise Event Streams.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from kafka.config import KafkaConfig
from kafka.message import StreamMessage
from kafka.broker import StreamingBroker


class StreamingProducer:
    """Enterprise Kafka Event Producer supporting CRM, ERP, and Ecommerce streams."""

    def __init__(self, config: Optional[KafkaConfig] = None, broker: Optional[StreamingBroker] = None):
        self.config = config or KafkaConfig()
        self.broker = broker or StreamingBroker()
        self.producer_id = f"producer-{uuid.uuid4().hex[:8]}"

    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> StreamMessage:
        """Publish a single structured message to a Kafka topic."""
        if not isinstance(value, dict):
            raise ValueError(f"Message value must be a dictionary, got {type(value)}")

        msg_headers = {
            "producer_id": self.producer_id,
            "trace_id": str(uuid.uuid4()),
            "schema_version": "1.0",
            "emitted_at": datetime.now(timezone.utc).isoformat(),
        }
        if headers:
            msg_headers.update(headers)

        message = StreamMessage(
            topic=topic,
            value=value,
            key=key,
            headers=msg_headers,
        )
        published_msg = self.broker.publish(message)
        return published_msg

    def send_batch(
        self,
        topic: str,
        messages: List[Dict[str, Any]],
        key_field: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> List[StreamMessage]:
        """Publish a batch of messages to a Kafka topic."""
        results = []
        for msg_dict in messages:
            key = str(msg_dict[key_field]) if key_field and key_field in msg_dict else None
            published = self.send(topic, msg_dict, key=key, headers=headers)
            results.append(published)
        return results

    def emit_crm_customer_event(
        self,
        customer_id: str,
        action: str,
        customer_data: Dict[str, Any],
    ) -> StreamMessage:
        """Emit customer lifecycle event (CREATED, UPDATED, DELETED) to CRM topic."""
        payload = {
            "event_type": f"CUSTOMER_{action.upper()}",
            "customer_id": customer_id,
            "data": customer_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send(
            topic=self.config.TOPIC_CRM_EVENTS,
            value=payload,
            key=customer_id,
            headers={"domain": "CRM", "entity": "Customer"},
        )

    def emit_erp_transaction_event(
        self,
        txn_id: str,
        amount_usd: float,
        currency: str,
        txn_data: Dict[str, Any],
    ) -> StreamMessage:
        """Emit financial journal entry event to ERP topic."""
        payload = {
            "event_type": "ERP_TXN_SETTLEMENT",
            "txn_id": txn_id,
            "amount_usd": amount_usd,
            "currency": currency,
            "details": txn_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send(
            topic=self.config.TOPIC_ERP_TRANSACTIONS,
            value=payload,
            key=txn_id,
            headers={"domain": "ERP", "entity": "Transaction"},
        )

    def emit_order_event(
        self,
        order_id: str,
        customer_id: str,
        total_amount: float,
        status: str,
    ) -> StreamMessage:
        """Emit ecommerce checkout or status change event."""
        payload = {
            "event_type": f"ORDER_{status.upper()}",
            "order_id": order_id,
            "customer_id": customer_id,
            "total_amount": total_amount,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send(
            topic=self.config.TOPIC_ECOMMERCE_ORDERS,
            value=payload,
            key=order_id,
            headers={"domain": "ECOMMERCE", "entity": "Order"},
        )

    def flush(self) -> None:
        """No-op for in-memory broker, flushes socket buffer in network mode."""
        pass
