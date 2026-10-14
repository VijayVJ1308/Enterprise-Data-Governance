import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from governance.classification.pii_classifier import PIIClassifier
from governance.masking.masking_engine import DataMaskingEngine
from governance.policies.policy_evaluator import GovernancePolicyEvaluator
from governance.compliance.compliance_service import ComplianceService
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("GovernanceEnginePipeline")


def run_governance_pipeline(
    bronze_lake_dir: str = "data/lake/bronze"
) -> Dict[str, Any]:
    Base.metadata.create_all(bind=engine)
    db_session: Session = SessionLocal()

    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]
    governance_summary = []

    try:
        logger.info("Starting Enterprise Data Governance & Compliance Pipeline...")

        for ds_name in datasets:
            raw_file = os.path.join(bronze_lake_dir, ds_name, f"{ds_name}_raw.json")
            if not os.path.exists(raw_file):
                logger.warning(f"Dataset file '{raw_file}' not found. Skipping.")
                continue

            with open(raw_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            # 1. PII & Sensitivity Classification
            class_map = PIIClassifier.classify_dataset(records)
            pii_cols = [col for col, info in class_map.items() if info["classification"] == "PII"]

            # 2. Dynamic Field Masking Demo (Data Analyst Role)
            masked_records = DataMaskingEngine.mask_records(
                records=records[:5],
                column_classifications=class_map,
                user_role="DATA_ANALYST"
            )

            # 3. Governance Policy Evaluation
            violations = GovernancePolicyEvaluator.evaluate_policies(
                db_session=db_session,
                dataset_name=ds_name,
                records=records
            )

            governance_summary.append({
                "dataset_name": ds_name,
                "record_count": len(records),
                "pii_columns": pii_cols,
                "policy_violations": len(violations),
            })

        # 4. Regulatory Compliance Evaluation
        compliance_status = ComplianceService.evaluate_compliance_status(db_session)
        logger.info(f"Governance Pipeline complete. Overall Compliance Score: {compliance_status['overall_compliance_score']}%.")

        return {
            "status": "SUCCESS",
            "datasets_evaluated": len(governance_summary),
            "summary": governance_summary,
            "compliance_status": compliance_status,
        }
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Governance Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    args = parser.parse_args()
    run_governance_pipeline(bronze_lake_dir=args.bronze_dir)
