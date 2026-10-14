"""
Phase 21: Enterprise dbt Model Compiler & Test Runner.
Executes Jinja-templated dbt SQL models with ref() and source() dependency resolution,
materializes tables and views into DuckDB/Lakehouse, and asserts schema tests.
"""

import os
import re
import yaml
import time
from typing import Dict, Any, List, Optional
import duckdb
import pandas as pd


class DbtRunner:
    """Executes dbt transformations and runs declarative schema assertions."""

    def __init__(self, project_dir: str = "dbt", duckdb_con: Optional[duckdb.DuckDBPyConnection] = None):
        self.project_dir = project_dir
        self.con = duckdb_con or duckdb.connect(database=":memory:")
        self.models_dir = os.path.join(project_dir, "models")
        self.project_config = self._load_project_config()

    def _load_project_config(self) -> Dict[str, Any]:
        cfg_file = os.path.join(self.project_dir, "dbt_project.yml")
        if os.path.exists(cfg_file):
            with open(cfg_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {"name": "aegis_data_governance"}

    def compile_model_sql(self, sql_content: str, source_mapping: Optional[Dict[str, str]] = None) -> str:
        """Replace {{ ref('model') }} and {{ source('src', 'tbl') }} with actual table names."""
        sources = source_mapping or {}

        def replace_source(match):
            src = match.group(1).strip().strip("'\"")
            tbl = match.group(2).strip().strip("'\"")
            key = f"{src}.{tbl}"
            return sources.get(key, sources.get(tbl, f"{src}_{tbl}"))

        def replace_ref(match):
            model = match.group(1).strip().strip("'\"")
            return model

        compiled = re.sub(r"{{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*}}", replace_source, sql_content)
        compiled = re.sub(r"{{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*}}", replace_ref, compiled)
        return compiled

    def run_model(self, model_name: str, sql_file: str, source_mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Compile and execute a single dbt SQL model."""
        with open(sql_file, "r", encoding="utf-8") as f:
            raw_sql = f.read()

        compiled_sql = self.compile_model_sql(raw_sql, source_mapping)
        t_start = time.time()

        # Create or replace table in DuckDB
        create_sql = f"CREATE OR REPLACE TABLE {model_name} AS {compiled_sql}"
        self.con.execute(create_sql)
        row_count = self.con.execute(f"SELECT COUNT(*) FROM {model_name}").fetchone()[0]

        return {
            "model_name": model_name,
            "status": "SUCCESS",
            "rows_materialized": row_count,
            "elapsed_ms": int((time.time() - t_start) * 1000),
        }

    def run_all_models(self, source_tables: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Register sources, compile dependencies, and run all staging and mart models."""
        t_start = time.time()
        # Register raw source DataFrames
        source_mapping = {}
        for name, df in source_tables.items():
            self.con.register(name, df)
            source_mapping[name] = name

        # Discover all models and extract ref dependencies
        models_to_run = {}
        for subdir in ["staging", "marts"]:
            s_path = os.path.join(self.models_dir, subdir)
            if os.path.exists(s_path):
                for fname in os.listdir(s_path):
                    if fname.endswith(".sql"):
                        m_name = fname.replace(".sql", "")
                        f_path = os.path.join(s_path, fname)
                        with open(f_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        refs = re.findall(r"{{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*}}", content)
                        models_to_run[m_name] = {
                            "file": f_path,
                            "type": subdir,
                            "refs": refs,
                        }

        # Topological Sort of models based on refs
        ordered_models = []
        visited = set()
        visiting = set()

        def visit(name):
            if name in visiting:
                raise ValueError(f"Cyclic dependency detected in dbt model '{name}'")
            if name not in visited and name in models_to_run:
                visiting.add(name)
                for dep in models_to_run[name]["refs"]:
                    visit(dep)
                visiting.remove(name)
                visited.add(name)
                ordered_models.append(name)

        for m_name in sorted(models_to_run.keys()):
            visit(m_name)

        staging_results = []
        marts_results = []

        for m_name in ordered_models:
            info = models_to_run[m_name]
            res = self.run_model(m_name, info["file"], source_mapping)
            if info["type"] == "staging":
                staging_results.append(res)
            else:
                marts_results.append(res)

        return {
            "status": "SUCCESS",
            "staging_models": staging_results,
            "marts_models": marts_results,
            "total_models": len(staging_results) + len(marts_results),
            "total_elapsed_ms": int((time.time() - t_start) * 1000),
        }

    def run_schema_tests(self, schema_file: Optional[str] = None) -> Dict[str, Any]:
        """Execute declarative dbt schema tests (unique, not_null, accepted_values)."""
        file_path = schema_file or os.path.join(self.models_dir, "schema.yml")
        if not os.path.exists(file_path):
            return {"status": "SKIPPED", "tests_executed": 0, "failures": 0}

        with open(file_path, "r", encoding="utf-8") as f:
            schema_data = yaml.safe_load(f)

        test_results = []
        for model in schema_data.get("models", []):
            m_name = model["name"]
            for col in model.get("columns", []):
                col_name = col["name"]
                for test in col.get("tests", []):
                    # Test: not_null
                    if test == "not_null":
                        query = f'SELECT COUNT(*) FROM {m_name} WHERE "{col_name}" IS NULL'
                        failures = self.con.execute(query).fetchone()[0]
                        test_results.append({
                            "model": m_name,
                            "column": col_name,
                            "test": "not_null",
                            "status": "PASS" if failures == 0 else "FAIL",
                            "failures": failures,
                        })

                    # Test: unique
                    elif test == "unique":
                        query = f'''
                            SELECT COUNT(*) FROM (
                                SELECT "{col_name}", COUNT(*) as cnt 
                                FROM {m_name} 
                                WHERE "{col_name}" IS NOT NULL 
                                GROUP BY "{col_name}" 
                                HAVING COUNT(*) > 1
                            )
                        '''
                        failures = self.con.execute(query).fetchone()[0]
                        test_results.append({
                            "model": m_name,
                            "column": col_name,
                            "test": "unique",
                            "status": "PASS" if failures == 0 else "FAIL",
                            "failures": failures,
                        })

                    # Test: accepted_values
                    elif isinstance(test, dict) and "accepted_values" in test:
                        allowed = test["accepted_values"].get("values", [])
                        allowed_str = ", ".join(f"'{v}'" for v in allowed)
                        query = f'SELECT COUNT(*) FROM {m_name} WHERE "{col_name}" NOT IN ({allowed_str})'
                        failures = self.con.execute(query).fetchone()[0]
                        test_results.append({
                            "model": m_name,
                            "column": col_name,
                            "test": "accepted_values",
                            "status": "PASS" if failures == 0 else "FAIL",
                            "failures": failures,
                        })

        failed_count = sum(1 for t in test_results if t["status"] == "FAIL")

        return {
            "status": "PASS" if failed_count == 0 else "FAIL",
            "total_tests": len(test_results),
            "passed": len(test_results) - failed_count,
            "failed": failed_count,
            "results": test_results,
        }
