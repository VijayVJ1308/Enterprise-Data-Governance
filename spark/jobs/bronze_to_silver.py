"""
Phase 20: Bronze to Silver Medallion Cleansing Batch Job.
Cleanses raw ingested records, eliminates duplicates, trims strings,
validates primary key constraints, enriches lineage audit headers,
and outputs certified Parquet tables into the Silver Lakehouse tier.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from spark.config import SparkMedallionConfig
from spark.session import SparkSessionProvider


class BronzeToSilverCleanser:
    """Transforms raw Bronze landing records into certified Silver Parquet datasets."""

    def __init__(
        self,
        config: Optional[SparkMedallionConfig] = None,
        session_provider: Optional[SparkSessionProvider] = None,
    ):
        self.config = config or SparkMedallionConfig()
        self.session = session_provider or SparkSessionProvider(self.config)

    def cleanse_dataset(
        self,
        dataset_name: str,
        input_path: str,
        primary_key: str,
        output_dir: Optional[str] = None,
        impute_defaults: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute Bronze-to-Silver cleansing pipeline:
        - Load raw records (Parquet or JSON)
        - Deduplicate on primary key
        - Strip whitespace across string columns
        - Impute defaults for specified nullable fields
        - Inject Silver audit lineage fields
        - Save certified Parquet file
        """
        # 1. Load raw data
        if input_path.endswith(".parquet") or (os.path.isdir(input_path) and any(f.endswith(".parquet") for f in os.listdir(input_path))):
            df = self.session.read_parquet(input_path)
        elif input_path.endswith(".json") or (os.path.isdir(input_path) and any(f.endswith(".json") for f in os.listdir(input_path))):
            df = self.session.read_json(input_path)
        else:
            raise ValueError(f"Unsupported input file format for: {input_path}")

        initial_count = len(df)
        if initial_count == 0:
            return {
                "dataset_name": dataset_name,
                "input_records": 0,
                "silver_records": 0,
                "deduplicated_count": 0,
                "dropped_count": 0,
                "output_file": None,
                "status": "EMPTY",
            }

        # 2. Drop records where primary key is null or empty
        if primary_key in df.columns:
            non_null_mask = df[primary_key].notna() & (df[primary_key].astype(str).str.strip() != "")
            dropped_null_pks = int((~non_null_mask).sum())
            df = df[non_null_mask].copy()
        else:
            dropped_null_pks = 0

        # 3. Deduplicate on primary key (keep first or latest)
        pre_dedup_count = len(df)
        if primary_key in df.columns:
            df = df.drop_duplicates(subset=[primary_key], keep="last")
        dedup_count = pre_dedup_count - len(df)

        # 4. Cleanse string columns: trim whitespace
        string_cols = df.select_dtypes(include=["object", "string"]).columns
        for col in string_cols:
            df[col] = df[col].astype(str).str.strip()
            # If column is email, lowercase
            if "email" in col.lower():
                df[col] = df[col].str.lower()

        # 5. Impute optional field defaults
        if impute_defaults:
            for col, default_val in impute_defaults.items():
                if col in df.columns:
                    df[col] = df[col].fillna(default_val)

        # 6. Inject Silver Medallion Lineage Metadata
        job_id = f"silver-job-{uuid.uuid4().hex[:8]}"
        processed_at = datetime.now(timezone.utc).isoformat()
        df["_silver_processed_at"] = processed_at
        df["_silver_job_id"] = job_id
        df["_is_cleansed"] = True

        # 7. Write to Silver Parquet destination
        target_dir = output_dir or self.config.get_tier_path("silver", dataset_name)
        os.makedirs(target_dir, exist_ok=True)
        output_file = os.path.join(target_dir, f"{dataset_name}_silver.parquet")

        self.session.write_parquet(df, output_file, compression=self.config.parquet_compression)

        return {
            "dataset_name": dataset_name,
            "input_records": initial_count,
            "silver_records": len(df),
            "deduplicated_count": dedup_count,
            "dropped_count": dropped_null_pks,
            "output_file": output_file,
            "job_id": job_id,
            "status": "SUCCESS",
        }
