import os
import csv
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Union


class BatchIngestor:
    def __init__(self, output_dir: str = "data/lake/bronze"):
        self.output_dir = output_dir

    def _generate_metadata(self, source_type: str, source_identifier: str) -> Dict[str, Any]:
        return {
            "_ingestion_id": str(uuid.uuid4()),
            "_ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
            "_source_type": source_type,
            "_source_identifier": source_identifier,
        }

    def _add_record_hash(self, record: Dict[str, Any]) -> Dict[str, Any]:
        record_copy = dict(record)
        serialized = json.dumps(record_copy, sort_keys=True, default=str)
        record_copy["_record_hash"] = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return record_copy

    def read_csv(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        return records

    def read_json(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"JSON file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
            if isinstance(content, list):
                return content
            elif isinstance(content, dict):
                return [content]
            else:
                raise ValueError("JSON file content must be a dict or list of dicts")

    def read_parquet(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Parquet file not found: {filepath}")
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(filepath)
            return table.to_pylist()
        except ImportError:
            # Fallback for lightweight testing environments without pyarrow
            raise RuntimeError("pyarrow is required to read native Parquet files.")

    def ingest_dataset(self, dataset_name: str, source_type: str, source_path_or_url: str) -> Dict[str, Any]:
        source_type_lower = source_type.lower()
        if source_type_lower == "csv":
            raw_records = self.read_csv(source_path_or_url)
        elif source_type_lower == "json":
            raw_records = self.read_json(source_path_or_url)
        elif source_type_lower == "parquet":
            raw_records = self.read_parquet(source_path_or_url)
        else:
            raise ValueError(f"Unsupported batch source type: {source_type}")

        meta = self._generate_metadata(source_type_lower, source_path_or_url)
        ingested_records = []
        for record in raw_records:
            enriched = dict(record)
            enriched.update(meta)
            enriched = self._add_record_hash(enriched)
            ingested_records.append(enriched)

        # Save to bronze landing directory
        target_dir = os.path.join(self.output_dir, dataset_name)
        os.makedirs(target_dir, exist_ok=True)
        output_file = os.path.join(target_dir, f"{dataset_name}_raw.json")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(ingested_records, f, indent=2, default=str)

        return {
            "dataset_name": dataset_name,
            "record_count": len(ingested_records),
            "ingestion_id": meta["_ingestion_id"],
            "output_file": output_file,
            "status": "SUCCESS",
        }
