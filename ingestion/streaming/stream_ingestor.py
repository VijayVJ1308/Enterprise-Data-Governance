import os
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any


class StreamIngestor:
    def __init__(self, output_dir: str = "data/lake/bronze"):
        self.output_dir = output_dir

    def process_event(self, topic_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(payload)
        enriched["_ingestion_id"] = str(uuid.uuid4())
        enriched["_ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()
        enriched["_source_type"] = "kafka"
        enriched["_source_identifier"] = topic_name

        serialized = json.dumps(enriched, sort_keys=True, default=str)
        enriched["_record_hash"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return enriched

    def ingest_stream_batch(self, dataset_name: str, topic_name: str, payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        ingested = [self.process_event(topic_name, p) for p in payloads]
        target_dir = os.path.join(self.output_dir, dataset_name)
        os.makedirs(target_dir, exist_ok=True)
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(target_dir, f"{dataset_name}_stream_{timestamp_str}.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(ingested, f, indent=2, default=str)

        return {
            "dataset_name": dataset_name,
            "record_count": len(ingested),
            "output_file": output_file,
            "status": "SUCCESS",
        }
