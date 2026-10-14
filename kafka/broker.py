"""
Phase 19: Streaming Message Broker & Topic Partition Store.
Provides a thread-safe partition engine for local execution and testing,
with consumer group offset tracking, replay, and partition assignment.
"""

import socket
import threading
from typing import Dict, List, Optional
from kafka.message import StreamMessage


class StreamingBroker:
    """Thread-safe streaming broker managing partitioned topic queues and consumer offsets."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StreamingBroker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, num_partitions: int = 3):
        if self._initialized:
            return
        self.num_partitions = num_partitions
        # Structure: {topic: {partition_id: [StreamMessage, ...]}}
        self._topics: Dict[str, Dict[int, List[StreamMessage]]] = {}
        # Structure: {group_id: {topic: {partition_id: offset}}}
        self._consumer_offsets: Dict[str, Dict[str, Dict[int, int]]] = {}
        self._broker_lock = threading.RLock()
        self._initialized = True

    @classmethod
    def reset_instance(cls):
        """Reset broker state (useful for test fixtures)."""
        with cls._lock:
            if cls._instance:
                with cls._instance._broker_lock:
                    cls._instance._topics.clear()
                    cls._instance._consumer_offsets.clear()

    def create_topic(self, topic: str, partitions: Optional[int] = None) -> None:
        parts = partitions or self.num_partitions
        with self._broker_lock:
            if topic not in self._topics:
                self._topics[topic] = {p: [] for p in range(parts)}

    def publish(self, message: StreamMessage) -> StreamMessage:
        with self._broker_lock:
            if message.topic not in self._topics:
                self.create_topic(message.topic)

            partitions = self._topics[message.topic]
            # Determine partition using key hash or round-robin
            if message.key:
                partition_id = hash(message.key) % len(partitions)
            else:
                partition_id = message.partition % len(partitions)

            current_queue = partitions[partition_id]
            offset = len(current_queue)

            message.partition = partition_id
            message.offset = offset
            current_queue.append(message)
            return message

    def fetch(
        self,
        topic: str,
        group_id: str,
        partition_id: int,
        max_messages: int = 100,
        auto_commit: bool = False,
    ) -> List[StreamMessage]:
        with self._broker_lock:
            if topic not in self._topics:
                return []

            partitions = self._topics[topic]
            if partition_id not in partitions:
                return []

            # Get current committed offset for group
            group_topics = self._consumer_offsets.setdefault(group_id, {})
            topic_offsets = group_topics.setdefault(topic, {})
            current_offset = topic_offsets.get(partition_id, 0)

            queue = partitions[partition_id]
            messages = queue[current_offset : current_offset + max_messages]

            if auto_commit and messages:
                new_offset = current_offset + len(messages)
                topic_offsets[partition_id] = new_offset

            return list(messages)

    def commit_offset(self, group_id: str, topic: str, partition_id: int, offset: int) -> None:
        with self._broker_lock:
            group_topics = self._consumer_offsets.setdefault(group_id, {})
            topic_offsets = group_topics.setdefault(topic, {})
            topic_offsets[partition_id] = offset

    def get_offset(self, group_id: str, topic: str, partition_id: int) -> int:
        with self._broker_lock:
            return (
                self._consumer_offsets.get(group_id, {})
                .get(topic, {})
                .get(partition_id, 0)
            )

    def get_topic_watermark(self, topic: str, partition_id: int) -> int:
        with self._broker_lock:
            if topic in self._topics and partition_id in self._topics[topic]:
                return len(self._topics[topic][partition_id])
            return 0

    def get_topic_message_count(self, topic: str) -> int:
        with self._broker_lock:
            if topic not in self._topics:
                return 0
            return sum(len(q) for q in self._topics[topic].values())

    @staticmethod
    def is_external_broker_available(host: str = "localhost", port: int = 9092, timeout_sec: float = 0.5) -> bool:
        """Check if external Kafka broker socket is responding."""
        try:
            with socket.create_connection((host, port), timeout=timeout_sec):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False
