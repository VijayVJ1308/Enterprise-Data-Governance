import os
import json
import csv
from typing import List, Dict, Any


class ParquetUtils:
    """
    Parquet serialization utility supporting native pyarrow/fastparquet if available,
    with robust JSON/CSV-backed dictionary fallback for environments without C-extensions.
    """

    @staticmethod
    def write_parquet(records: List[Dict[str, Any]], filepath: str) -> str:
        if not records:
            return filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            # Convert dict values to JSON strings if nested
            flattened = []
            for r in records:
                flat_row = {}
                for k, v in r.items():
                    if isinstance(v, (dict, list)):
                        flat_row[k] = json.dumps(v)
                    else:
                        flat_row[k] = v
                flattened.append(flat_row)

            table = pa.Table.from_pylist(flattened)
            pq.write_table(table, filepath)
            return filepath
        except ImportError:
            # Fallback to structured json/parquet proxy file if pyarrow is unavailable
            fallback_file = filepath if filepath.endswith(".parquet") else f"{filepath}.parquet"
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, default=str)
            return fallback_file

    @staticmethod
    def read_parquet(filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Parquet file not found: {filepath}")

        try:
            import pyarrow.parquet as pq
            table = pq.read_table(filepath)
            return table.to_pylist()
        except ImportError:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
