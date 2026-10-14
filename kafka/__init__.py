"""
Phase 19: Apache Kafka Streaming Ingestion & Real-Time Alerting Package
"""

from kafka.config import KafkaConfig
from kafka.message import StreamMessage
from kafka.broker import StreamingBroker
from kafka.producer import StreamingProducer
from kafka.consumer import StreamingConsumer
from kafka.alerting import StreamingAlertEngine, QualityAlert

__all__ = [
    "KafkaConfig",
    "StreamMessage",
    "StreamingBroker",
    "StreamingProducer",
    "StreamingConsumer",
    "StreamingAlertEngine",
    "QualityAlert",
]
