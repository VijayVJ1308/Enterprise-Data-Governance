"""
Phase 20: Unified Big Data Processing Session Provider.
Supports PySpark cluster / local JVM execution and high-performance in-process
DuckDB + PyArrow OLAP execution.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import pandas as pd
import duckdb

from spark.config import SparkMedallionConfig

logger = logging.getLogger("EnterpriseBigDataEngine")


class SparkSessionProvider:
    """Manages big data execution engine (PySpark or DuckDB + PyArrow)."""

    def __init__(self, config: Optional[SparkMedallionConfig] = None):
        self.config = config or SparkMedallionConfig()
        self._spark_session = None
        self._duckdb_con = None
        self._engine_type = "duckdb"
        self._init_engine()

    def _init_engine(self):
        """Attempt initializing PySpark, falling back gracefully to vectorized DuckDB."""
        try:
            from pyspark.sql import SparkSession
            # Attempt building SparkSession
            spark = (
                SparkSession.builder.master(self.config.master)
                .appName(self.config.app_name)
                .config("spark.ui.enabled", "false")
                .config("spark.sql.warehouse.dir", self.config.warehouse_dir)
                .getOrCreate()
            )
            self._spark_session = spark
            self._engine_type = "pyspark"
            logger.info("Initialized PySpark execution session successfully.")
        except Exception as e:
            # Fall back to DuckDB in-process OLAP engine
            self._spark_session = None
            self._engine_type = "duckdb"
            logger.info(f"Using DuckDB OLAP engine for big data transformations (PySpark skipped: {e})")

        self._duckdb_con = duckdb.connect(database=":memory:")
        self._duckdb_con.execute(f"SET memory_limit='{self.config.memory_limit}'")

    @property
    def engine_type(self) -> str:
        return self._engine_type

    @property
    def spark(self):
        return self._spark_session

    @property
    def duckdb(self) -> duckdb.DuckDBPyConnection:
        return self._duckdb_con

    def execute_sql(self, query: str, tables: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
        """Execute a vectorized SQL query across memory tables."""
        con = self._duckdb_con
        if tables:
            for name, df in tables.items():
                con.register(name, df)
        return con.execute(query).df()

    def read_parquet(self, path: str) -> pd.DataFrame:
        """Read Parquet file or directory into DataFrame."""
        if os.path.isdir(path):
            return self._duckdb_con.execute(f"SELECT * FROM read_parquet('{path}/*.parquet')").df()
        return self._duckdb_con.execute(f"SELECT * FROM read_parquet('{path}')").df()

    def write_parquet(self, df: pd.DataFrame, output_path: str, compression: str = "snappy") -> str:
        """Write DataFrame to Parquet file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self._duckdb_con.register("_temp_export", df)
        self._duckdb_con.execute(
            f"COPY _temp_export TO '{output_path}' (FORMAT PARQUET, COMPRESSION '{compression}')"
        )
        self._duckdb_con.unregister("_temp_export")
        return output_path

    def read_json(self, path: str) -> pd.DataFrame:
        """Read JSON file or directory into DataFrame."""
        if os.path.isdir(path):
            return self._duckdb_con.execute(f"SELECT * FROM read_json_auto('{path}/*.json')").df()
        return self._duckdb_con.execute(f"SELECT * FROM read_json_auto('{path}')").df()

    def stop(self):
        """Clean up active sessions."""
        if self._spark_session:
            try:
                self._spark_session.stop()
            except Exception:
                pass
        if self._duckdb_con:
            try:
                self._duckdb_con.close()
            except Exception:
                pass
