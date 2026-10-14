"""
Phase 19: Streaming Consumer with Group Offsets, Bronze Ingestion, and DLQ.
"""

import os
import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from kafka.config import KafkaConfig
from kafka.message import StreamMessage
from kafka.broker import StreamingBroker
from ingestion.streaming.stream_ingestor import StreamIngestor


class StreamingConsumer:
    """Enterprise Kafka Consumer supporting consumer groups, micro-batch Bronze landing, and DLQ."""

    def __init__(
        self,
        topics: List[str],
        group_id: Optional[str] = None,
        config: Optional[KafkaConfig] = None,
        broker: Optional[StreamingBroker] = None,
    ):
        self.topics = topics
        self.config = config or KafkaConfig()
        self.group_id = group_id or self.config.default_group_id
        self.broker = broker or StreamingBroker()
        self.uncommitted_offsets: Dict[str, Dict[int, int]] = {}

    def poll(self, max_messages: int = 100, auto_commit: bool = False) -> List[StreamMessage]:
        """Poll messages from subscribed topics across all partitions."""
        batch = []
        for topic in self.topics:
            for partition_id in range(self.broker.num_partitions):
                remaining = max_messages - len(batch)
                if remaining <= 0:
                    break

                messages = self.broker.fetch(
                    topic=topic,
                    group_id=self.group_id,
                    partition_id=partition_id,
                    max_messages=remaining,
                    auto_commit=auto_commit,
                )

                if messages:
                    batch.extend(messages)
                    if not auto_commit:
                        # Record latest offset for explicit manual commit
                        highest_offset = max(m.offset for m in messages) + 1
                        topic_offsets = self.uncommitted_offsets.setdefault(topic, {})
                        topic_offsets[partition_id] = highest_offset

            if len(batch) >= max_messages:
                break

        return batch

    def commit(self) -> None:
        """Manually commit offsets for all successfully processed messages."""
        for topic, partitions in self.uncommitted_offsets.items():
            for partition_id, offset in partitions.items():
                self.broker.commit_offset(
                    group_id=self.group_id,
                    topic=topic,
                    partition_id=partition_id,
                    offset=offset,
                )
        self.uncommitted_offsets.clear()

    def route_to_dlq(self, raw_message: Any, error: Exception) -> StreamMessage:
        """Forward corrupted or unprocessable message to the Dead Letter Queue."""
        dlq_payload = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "original_payload": raw_message.to_dict() if isinstance(raw_message, StreamMessage) else str(raw_message),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        dlq_msg = StreamMessage(
            topic=self.config.TOPIC_DEAD_LETTER_QUEUE,
            value=dlq_payload,
            key=str(uuid.uuid4()),
            headers={"source_group": self.group_id, "is_dlq": "true"},
        )
        return self.broker.publish(dlq_msg)

    def consume_to_bronze(
        self,
        dataset_name: str,
        topic: str,
        bronze_output_dir: str = "data/lake/bronze",
        max_records: int = 100,
    ) -> Dict[str, Any]:
        """
        Poll streaming events from topic, enrich with ingestion telemetry,
        and land directly to the Medallion Bronze lakehouse.
        """
        messages = self.poll(max_messages=max_records, auto_commit=False)
        if not messages:
            return {
                "dataset_name": dataset_name,
                "topic": topic,
                "record_count": 0,
                "output_file": None,
                "status": "EMPTY",
            }

        payloads = [m.value for m in messages]
        ingestor = StreamIngestor(output_dir=bronze_output_dir)
        landing_summary = ingestor.ingest_stream_batch(
            dataset_name=dataset_name,
            topic_name=topic,
            payloads=payloads,
        )

        # Commit offset now that landing is complete and safe
        self.commit()

        landing_summary["topic"] = topic
        landing_summary["partition_offsets"] = {
            f"p{m.partition}": m.offset for m in messages
        }
        return landing_summary

    def get_committed_offset(self, topic: str, partition_id: int) -> int:
        return self.broker.get_offset(self.group_id, topic, partition_id)
