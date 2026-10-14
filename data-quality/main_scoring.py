import os
import sys
import argparse
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_quality.profiling.profiler import DataProfiler
from data_quality.engine.rule_evaluator import RuleEvaluator
from data_quality.rules.default_rules import DEFAULT_ENTERPRISE_RULES
from data_quality.scoring.score_calculator import QualityScoreCalculator
from data_quality.scoring.score_repository import ScoreRepository
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("QualityScoreEngine")


def run_scoring_pipeline(bronze_lake_dir: str = "data/lake/bronze") -> Dict[str, Any]:
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    profiler = DataProfiler()
    evaluator = RuleEvaluator()
    calculator = QualityScoreCalculator()

    import json
    loaded_datasets: Dict[str, List[Dict[str, Any]]] = {}
    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]

    for ds in datasets:
        raw_file = os.path.join(bronze_lake_dir, ds, f"{ds}_raw.json")
        if os.path.exists(raw_file):
            with open(raw_file, "r", encoding="utf-8") as f:
                loaded_datasets[ds] = json.load(f)

    try:
        logger.info("Starting Quality Score Calculation across all datasets...")
        dataset_scores = []

        for ds_name, records in loaded_datasets.items():
            profile_data = profiler.profile_records(ds_name, records)

            # Evaluate rules for this dataset
            ds_rules = [r for r in DEFAULT_ENTERPRISE_RULES if r.dataset_name == ds_name]
            rule_results = []
            for rspec in ds_rules:
                res = evaluator.evaluate_rule(rspec, records, parent_datasets=loaded_datasets)
                rule_results.append({
                    "rule_type": rspec.rule_type,
                    "pass_rate": res.pass_rate,
                })

            score_breakdown = calculator.calculate_dataset_score(ds_name, profile_data, rule_results)
            ScoreRepository.update_dataset_quality_score(db_session, score_breakdown)
            dataset_scores.append(score_breakdown)

        ent_summary = calculator.calculate_enterprise_score(dataset_scores)
        logger.info(f"Quality Scoring complete. Enterprise Quality Score: {ent_summary['enterprise_quality_score']}%.")
        return {
            "enterprise_summary": ent_summary,
            "dataset_scores": [ds.__dict__ for ds in dataset_scores],
            "status": "SUCCESS",
        }
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Quality Score Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    args = parser.parse_args()
    run_scoring_pipeline(bronze_lake_dir=args.bronze_dir)
