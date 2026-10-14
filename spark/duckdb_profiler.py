"""
Phase 20: High-Performance Vectorized Big Data Column Profiler using DuckDB.
Computes comprehensive statistical distributions, percentiles, distinct counts,
null rates, and categorical frequencies directly across Parquet lakehouse files.
"""

import os
import time
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd


class DuckDBProfiler:
    """Vectorized OLAP columnar statistical profiler."""

    def __init__(self, memory_limit: str = "2GB"):
        self.memory_limit = memory_limit
        self.con = duckdb.connect(database=":memory:")
        self.con.execute(f"SET memory_limit='{self.memory_limit}'")

    def profile_parquet(self, parquet_path: str, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """Profile a Parquet file or directory using native DuckDB vectorized scans."""
        if not os.path.exists(parquet_path):
            raise FileNotFoundError(f"Parquet path does not exist: {parquet_path}")

        name = dataset_name or os.path.basename(parquet_path).replace(".parquet", "")
        file_size = os.path.getsize(parquet_path) if os.path.isfile(parquet_path) else 0

        # Register parquet table view
        self.con.execute(f"CREATE OR REPLACE VIEW _profile_target AS SELECT * FROM read_parquet('{parquet_path}')")
        return self._generate_profile(view_name="_profile_target", dataset_name=name, file_size=file_size)

    def profile_dataframe(self, df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
        """Profile an in-memory DataFrame using DuckDB zero-copy query integration."""
        self.con.register("_profile_df_target", df)
        res = self._generate_profile(view_name="_profile_df_target", dataset_name=dataset_name, file_size=0)
        self.con.unregister("_profile_df_target")
        return res

    def _generate_profile(self, view_name: str, dataset_name: str, file_size: int) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Total row count & schema
        schema_info = self.con.execute(f"DESCRIBE {view_name}").fetchall()
        row_count = self.con.execute(f"SELECT COUNT(*) FROM {view_name}").fetchone()[0]

        columns_profile = []

        if row_count == 0:
            return {
                "dataset_name": dataset_name,
                "row_count": 0,
                "column_count": len(schema_info),
                "file_size_bytes": file_size,
                "columns": [],
                "profiling_time_ms": int((time.time() - start_time) * 1000),
            }

        # 2. Column-by-column statistics
        for col_name, col_type, nullable, key, default, extra in schema_info:
            col_info: Dict[str, Any] = {
                "column_name": col_name,
                "data_type": col_type,
            }

            # Basic counts
            base_stats = self.con.execute(
                f"""
                SELECT 
                    COUNT(*) - COUNT("{col_name}") AS null_count,
                    COUNT(DISTINCT "{col_name}") AS distinct_count
                FROM {view_name}
                """
            ).fetchone()

            null_count = base_stats[0]
            distinct_count = base_stats[1]

            col_info["null_count"] = int(null_count)
            col_info["null_percentage"] = round((null_count / row_count) * 100.0, 2)
            col_info["distinct_count"] = int(distinct_count)
            col_info["unique_percentage"] = round((distinct_count / row_count) * 100.0, 2)

            is_numeric = any(t in col_type.upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "NUMERIC", "BIGINT"])

            if is_numeric:
                try:
                    num_stats = self.con.execute(
                        f"""
                        SELECT 
                            MIN("{col_name}") AS min_val,
                            MAX("{col_name}") AS max_val,
                            AVG("{col_name}") AS mean_val,
                            STDDEV("{col_name}") AS std_val,
                            quantile_cont("{col_name}", 0.25) AS p25,
                            quantile_cont("{col_name}", 0.50) AS p50,
                            quantile_cont("{col_name}", 0.75) AS p75,
                            quantile_cont("{col_name}", 0.95) AS p95,
                            quantile_cont("{col_name}", 0.99) AS p99
                        FROM {view_name}
                        WHERE "{col_name}" IS NOT NULL
                        """
                    ).fetchone()

                    col_info["min_value"] = float(num_stats[0]) if num_stats[0] is not None else None
                    col_info["max_value"] = float(num_stats[1]) if num_stats[1] is not None else None
                    col_info["mean"] = round(float(num_stats[2]), 2) if num_stats[2] is not None else None
                    col_info["std_dev"] = round(float(num_stats[3]), 2) if num_stats[3] is not None else None
                    col_info["quantiles"] = {
                        "p25": round(float(num_stats[4]), 2) if num_stats[4] is not None else None,
                        "p50_median": round(float(num_stats[5]), 2) if num_stats[5] is not None else None,
                        "p75": round(float(num_stats[6]), 2) if num_stats[6] is not None else None,
                        "p95": round(float(num_stats[7]), 2) if num_stats[7] is not None else None,
                        "p99": round(float(num_stats[8]), 2) if num_stats[8] is not None else None,
                    }
                except Exception:
                    pass
            else:
                # String / Categorical top values
                try:
                    top_vals = self.con.execute(
                        f"""
                        SELECT "{col_name}" AS val, COUNT(*) AS count
                        FROM {view_name}
                        WHERE "{col_name}" IS NOT NULL
                        GROUP BY "{col_name}"
                        ORDER BY count DESC
                        LIMIT 5
                        """
                    ).fetchall()
                    col_info["top_values"] = [
                        {"value": str(v[0]), "count": int(v[1]), "percentage": round((v[1] / row_count) * 100, 2)}
                        for v in top_vals
                    ]
                except Exception:
                    pass

            columns_profile.append(col_info)

        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "dataset_name": dataset_name,
            "row_count": row_count,
            "column_count": len(columns_profile),
            "file_size_bytes": file_size,
            "columns": columns_profile,
            "profiling_time_ms": elapsed_ms,
        }
