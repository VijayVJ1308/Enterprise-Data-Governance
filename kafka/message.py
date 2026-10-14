"""
Phase 19: StreamMessage definition with headers, partitioning, and JSON serialization.
"""

import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


@dataclass
class StreamMessage:
    """Represents an individual streaming record in Kafka."""

    topic: str
    value: Dict[str, Any]
    key: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    partition: int = 0
    offset: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamMessage":
        return cls(
            topic=data["topic"],
            value=data["value"],
            key=data.get("key"),
            headers=data.get("headers", {}),
            partition=data.get("partition", 0),
            offset=data.get("offset", 0),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            message_id=data.get("message_id", str(uuid.uuid4())),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "StreamMessage":
        data = json.loads(json_str)
        return cls.from_dict(data)
