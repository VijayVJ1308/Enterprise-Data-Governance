import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_quality.remediation.remediation_engine import RemediationService
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataRemediationPipeline")


def run_remediation_pipeline(
    bronze_lake_dir: str = "data/lake/bronze",
    silver_lake_dir: str = "data/lake/silver"
) -> Dict[str, Any]:
    Base.metadata.create_all(bind=engine)
    db_session: Session = SessionLocal()
    os.makedirs(silver_lake_dir, exist_ok=True)

    remediation_summary = []
    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]

    try:
        logger.info("Starting Automated Data Remediation Pipeline...")

        for ds_name in datasets:
            raw_file = os.path.join(bronze_lake_dir, ds_name, f"{ds_name}_raw.json")
            if not os.path.exists(raw_file):
                logger.warning(f"Dataset file '{raw_file}' not found. Skipping.")
                continue

            with open(raw_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            initial_count = len(records)
            current_records = records

            # 1. Trim whitespace across all string columns
            current_records, trim_action = RemediationService.execute_remediation_action(
                db_session=db_session,
                dataset_name=ds_name,
                action_type="TRIM_WHITESPACE",
                records=current_records,
                params={},
                executed_by="AUTOMATED_PIPELINE"
            )

            # 2. Case normalization (dataset specific)
            if ds_name == "customers":
                current_records, case_action = RemediationService.execute_remediation_action(
                    db_session=db_session,
                    dataset_name=ds_name,
                    action_type="CASE_NORMALIZE",
                    records=current_records,
                    params={"column_case_map": {"email": "lower", "state": "upper", "country": "upper"}},
                    executed_by="AUTOMATED_PIPELINE"
                )
                current_records, country_action = RemediationService.execute_remediation_action(
                    db_session=db_session,
                    dataset_name=ds_name,
                    action_type="COUNTRY_NORMALIZE",
                    records=current_records,
                    params={"column_name": "country"},
                    executed_by="AUTOMATED_PIPELINE"
                )

            # 3. Fill defaults
            if ds_name == "orders":
                current_records, default_action = RemediationService.execute_remediation_action(
                    db_session=db_session,
                    dataset_name=ds_name,
                    action_type="FILL_DEFAULT",
                    records=current_records,
                    params={"defaults_map": {"order_status": "PENDING", "shipping_address": "STANDARD"}},
                    executed_by="AUTOMATED_PIPELINE"
                )

            # 4. Deduplicate records
            current_records, dedup_action = RemediationService.execute_remediation_action(
                db_session=db_session,
                dataset_name=ds_name,
                action_type="DEDUPLICATE",
                records=current_records,
                params={},
                executed_by="AUTOMATED_PIPELINE"
            )

            # Save clean silver dataset
            ds_silver_dir = os.path.join(silver_lake_dir, ds_name)
            os.makedirs(ds_silver_dir, exist_ok=True)
            silver_file = os.path.join(ds_silver_dir, f"{ds_name}_remediated.json")

            with open(silver_file, "w", encoding="utf-8") as f:
                json.dump(current_records, f, indent=2)

            remediation_summary.append({
                "dataset_name": ds_name,
                "initial_records": initial_count,
                "final_records": len(current_records),
                "remediated_file": silver_file
            })

            logger.info(f"Remediation finished for '{ds_name}'. Output: {silver_file}")

        return {
            "status": "SUCCESS",
            "datasets_processed": len(remediation_summary),
            "summary": remediation_summary
        }
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Quality Remediation Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    parser.add_argument("--silver-dir", default="data/lake/silver", help="Silver lake directory")
    args = parser.parse_args()
    run_remediation_pipeline(bronze_lake_dir=args.bronze_dir, silver_lake_dir=args.silver_dir)
