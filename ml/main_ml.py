import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.anomaly_detector import AnomalyDetector
from ml.rule_recommender import MLRuleRecommender
from backend.app.models.observability import Alert
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MLGovernancePipeline")


def run_ml_pipeline(
    bronze_lake_dir: str = "data/lake/bronze"
) -> Dict[str, Any]:
    Base.metadata.create_all(bind=engine)
    db_session: Session = SessionLocal()

    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]
    anomaly_summary = []
    recommendation_summary = []

    try:
        logger.info("Starting ML Anomaly Detection & Rule Recommendation Pipeline...")

        for ds_name in datasets:
            raw_file = os.path.join(bronze_lake_dir, ds_name, f"{ds_name}_raw.json")
            if not os.path.exists(raw_file):
                logger.warning(f"Dataset file '{raw_file}' not found. Skipping.")
                continue

            with open(raw_file, "r", encoding="utf-8") as f:
                records = json.load(f)

            current_count = len(records)
            # Simulated historical row counts for Z-Score / IQR baseline
            historical_counts = [current_count - 5, current_count + 3, current_count - 2, current_count + 1]

            # 1. Volume Anomaly Detection
            vol_anomaly = AnomalyDetector.detect_volume_anomaly(historical_counts, current_count)

            if vol_anomaly["is_anomaly"]:
                alert = Alert(
                    alert_type="VOLUME_ANOMALY",
                    severity="HIGH",
                    dataset_name=ds_name,
                    message=f"Row count anomaly detected in dataset '{ds_name}'. Count: {current_count}.",
                    status="UNACKNOWLEDGED",
                    triggered_at=datetime.now(timezone.utc),
                    details=vol_anomaly
                )
                db_session.add(alert)

            anomaly_summary.append({
                "dataset_name": ds_name,
                "current_count": current_count,
                "volume_anomaly": vol_anomaly["is_anomaly"],
            })

            # 2. ML Rule Recommendations
            recs = MLRuleRecommender.recommend_rules_for_dataset(ds_name, records)
            recommendation_summary.append({
                "dataset_name": ds_name,
                "recommended_rules_count": len(recs),
                "rules": recs
            })

        db_session.commit()
        logger.info(f"ML Pipeline complete. Evaluated {len(anomaly_summary)} datasets.")

        return {
            "status": "SUCCESS",
            "anomaly_evaluations": anomaly_summary,
            "rule_recommendations": recommendation_summary,
        }
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise ML Anomaly Detection Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    args = parser.parse_args()
    run_ml_pipeline(bronze_lake_dir=args.bronze_dir)
