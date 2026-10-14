"""
Phase 16 ML Anomaly Detection & Rule Recommendation Verification Tests

Tests Z-Score, IQR, volume/freshness anomaly detection, alert generation, and automated ML rule recommendation heuristics.
"""

import os
import sys
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base
from backend.app.models.observability import Alert
from ml.anomaly_detector import AnomalyDetector
from ml.rule_recommender import MLRuleRecommender
from ml.main_ml import run_ml_pipeline
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion


class TestPhase16ML(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.bronze_dir = os.path.join(self.temp_dir, "bronze")

        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_zscore_anomaly_detection(self):
        historical = [100.0, 102.0, 98.0, 101.0, 99.0, 100.5]
        # Normal value
        normal_res = AnomalyDetector.detect_zscore_anomaly(historical, 101.0)
        self.assertFalse(normal_res["is_anomaly"])

        # Extreme outlier value
        outlier_res = AnomalyDetector.detect_zscore_anomaly(historical, 500.0)
        self.assertTrue(outlier_res["is_anomaly"])
        self.assertGreater(outlier_res["z_score"], 3.0)

    def test_iqr_anomaly_detection(self):
        historical = [10.0, 12.0, 11.0, 10.5, 12.5, 11.5, 13.0, 10.2]
        # Normal value
        normal_res = AnomalyDetector.detect_iqr_anomaly(historical, 11.8)
        self.assertFalse(normal_res["is_anomaly"])

        # Outlier value
        outlier_res = AnomalyDetector.detect_iqr_anomaly(historical, 50.0)
        self.assertTrue(outlier_res["is_anomaly"])

    def test_volume_and_freshness_anomalies(self):
        historical_counts = [1000, 1050, 980, 1020, 1010]
        # Normal count
        vol_normal = AnomalyDetector.detect_volume_anomaly(historical_counts, 1015)
        self.assertFalse(vol_normal["is_anomaly"])

        # Abnormal count drop
        vol_drop = AnomalyDetector.detect_volume_anomaly(historical_counts, 100)
        self.assertTrue(vol_drop["is_anomaly"])

        # Freshness SLA check (30 hours ago, threshold 24 hours)
        stale_time = datetime.now(timezone.utc) - timedelta(hours=30)
        freshness_res = AnomalyDetector.detect_freshness_anomaly(stale_time, expected_frequency_hours=24.0)
        self.assertTrue(freshness_res["is_anomaly"])

    def test_ml_rule_recommender(self):
        records = [
            {"id": "C-1", "status": "ACTIVE", "age": 25, "user_email": "a@x.com"},
            {"id": "C-2", "status": "ACTIVE", "age": 30, "user_email": "b@x.com"},
            {"id": "C-3", "status": "INACTIVE", "age": 35, "user_email": "c@x.com"},
            {"id": "C-4", "status": "ACTIVE", "age": 40, "user_email": "d@x.com"},
        ]
        # Duplicate status values to trigger ACCEPTED_VALUES for 20+ rows test helper
        records_large = records * 6  # 24 rows

        recs = MLRuleRecommender.recommend_rules_for_dataset("customers", records_large)
        rule_types = [r["rule_type"] for r in recs]

        self.assertIn("NOT_NULL", rule_types)
        self.assertIn("RANGE", rule_types)
        self.assertIn("VALID_FORMAT", rule_types)

    def test_run_ml_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        res = run_ml_pipeline(bronze_lake_dir=self.bronze_dir)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(len(res["anomaly_evaluations"]), 0)
        self.assertGreater(len(res["rule_recommendations"]), 0)


if __name__ == "__main__":
    unittest.main()
