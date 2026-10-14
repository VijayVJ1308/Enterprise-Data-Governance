"""
Phase 20: PySpark Medallion Transformations & DuckDB Big Data Profiling Configuration.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SparkMedallionConfig:
    """Configuration for Big Data Medallion Lakehouse Transformations & Profiling."""

    app_name: str = "Enterprise-Medallion-Lakehouse-Engine"
    master: str = field(
        default_factory=lambda: os.getenv("SPARK_MASTER", "local[*]")
    )
    bronze_path: str = field(
        default_factory=lambda: os.getenv("LAKE_BRONZE_PATH", "data/lake/bronze")
    )
    silver_path: str = field(
        default_factory=lambda: os.getenv("LAKE_SILVER_PATH", "data/lake/silver")
    )
    gold_path: str = field(
        default_factory=lambda: os.getenv("LAKE_GOLD_PATH", "data/lake/gold")
    )
    warehouse_dir: str = field(
        default_factory=lambda: os.getenv("SPARK_WAREHOUSE_DIR", "data/lake/warehouse")
    )
    parquet_compression: str = "snappy"
    memory_limit: str = "2GB"

    def get_tier_path(self, tier: str, dataset_name: str) -> str:
        base = {
            "bronze": self.bronze_path,
            "silver": self.silver_path,
            "gold": self.gold_path,
        }.get(tier.lower(), self.bronze_path)
        return os.path.join(base, dataset_name)
