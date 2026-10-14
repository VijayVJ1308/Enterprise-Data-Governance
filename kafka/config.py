"""
Phase 19: Apache Kafka Streaming Ingestion & Real-Time Alerting Configuration
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class KafkaConfig:
    """Enterprise Kafka Streaming Configuration"""

    bootstrap_servers: str = field(
        default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    )
    client_id: str = "enterprise-governance-streaming-engine"
    default_group_id: str = "enterprise-governance-consumers"

    # Core Streaming Topics
    TOPIC_CRM_EVENTS: str = "enterprise.crm.events"
    TOPIC_ERP_TRANSACTIONS: str = "enterprise.erp.transactions"
    TOPIC_ECOMMERCE_ORDERS: str = "enterprise.ecommerce.orders"
    TOPIC_QUALITY_ALERTS: str = "enterprise.quality.alerts"
    TOPIC_GOVERNANCE_AUDIT: str = "enterprise.governance.audit"
    TOPIC_DEAD_LETTER_QUEUE: str = "enterprise.dlq"

    # Micro-batching and window settings
    max_batch_size: int = 100
    batch_timeout_ms: int = 2000
    auto_offset_reset: str = "earliest"  # 'earliest' or 'latest'
    enable_auto_commit: bool = False

    # Reliability and buffering
    retries: int = 3
    compression_type: str = "gzip"
    dlq_enabled: bool = True

    def get_all_managed_topics(self) -> List[str]:
        return [
            self.TOPIC_CRM_EVENTS,
            self.TOPIC_ERP_TRANSACTIONS,
            self.TOPIC_ECOMMERCE_ORDERS,
            self.TOPIC_QUALITY_ALERTS,
            self.TOPIC_GOVERNANCE_AUDIT,
            self.TOPIC_DEAD_LETTER_QUEUE,
        ]
