import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_quality.rules.default_rules import DEFAULT_ENTERPRISE_RULES
from data_quality.engine.rule_evaluator import RuleEvaluator
from data_quality.engine.quality_repository import QualityRepository
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataQualityEngine")


def run_quality_pipeline(bronze_lake_dir: str = "data/lake/bronze") -> List[Dict[str, Any]]:
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    evaluator = RuleEvaluator()
    results = []

    if not os.path.exists(bronze_lake_dir):
        logger.warning(f"Bronze lake directory '{bronze_lake_dir}' does not exist.")
        return results

    # Load all datasets for referential integrity checks
    loaded_datasets: Dict[str, List[Dict[str, Any]]] = {}
    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]

    for ds in datasets:
        raw_file = os.path.join(bronze_lake_dir, ds, f"{ds}_raw.json")
        if os.path.exists(raw_file):
            with open(raw_file, "r", encoding="utf-8") as f:
                loaded_datasets[ds] = json.load(f)

    try:
        logger.info(f"Starting Data Quality Rule Evaluation on {len(DEFAULT_ENTERPRISE_RULES)} declarative rules...")
        for rule_spec in DEFAULT_ENTERPRISE_RULES:
            ds_name = rule_spec.dataset_name
            records = loaded_datasets.get(ds_name, [])

            if not records:
                logger.warning(f"Skipping rule '{rule_spec.rule_id}': Dataset '{ds_name}' has no loaded records.")
                continue

            eval_res = evaluator.evaluate_rule(rule_spec, records, parent_datasets=loaded_datasets)
            QualityRepository.save_rule_and_result(db_session, rule_spec, eval_res)
            results.append({
                "rule_id": eval_res.rule_id,
                "dataset": eval_res.dataset_name,
                "passed": eval_res.passed,
                "pass_rate": eval_res.pass_rate,
                "failed_records": eval_res.failed_records,
            })

        logger.info(f"Quality pipeline evaluation completed. Evaluated {len(results)} rules.")
        return results
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Quality Rule Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    args = parser.parse_args()
    run_quality_pipeline(bronze_lake_dir=args.bronze_dir)
