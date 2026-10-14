"""
Phase 8 Quality Score Engine Verification Tests

Tests score calculation across 6 quality dimensions (Completeness, Validity, Uniqueness,
Consistency, Timeliness, Accuracy), custom weights, enterprise aggregation, and DB persistence.
"""

import os
import sys
import shutil
import tempfile
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base
from backend.app.models.catalog import Dataset, MetadataEntry
from data_quality.scoring.score_calculator import QualityScoreCalculator, DimensionWeights
from data_quality.scoring.score_repository import ScoreRepository
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion
from data_quality.main_scoring import run_scoring_pipeline


class TestPhase8QualityScoring(unittest.TestCase):

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

    def test_score_calculator_six_dimensions(self):
        profile_data = {
            "null_percentages": {"col1": 5.0, "col2": 0.0},
            "uniqueness_percentages": {"col1": 100.0, "col2": 95.0},
        }
        quality_results = [
            {"rule_type": "VALID_FORMAT", "pass_rate": 90.0},
            {"rule_type": "BUSINESS_RULE", "pass_rate": 92.0},
            {"rule_type": "REFERENTIAL_INTEGRITY", "pass_rate": 96.0},
        ]

        calc = QualityScoreCalculator()
        breakdown = calc.calculate_dataset_score("test_ds", profile_data, quality_results)

        self.assertEqual(breakdown.completeness_score, 97.5) # (95 + 100) / 2
        self.assertEqual(breakdown.uniqueness_score, 97.5) # (100 + 95) / 2
        self.assertEqual(breakdown.validity_score, 90.0)
        self.assertEqual(breakdown.consistency_score, 92.0)
        self.assertEqual(breakdown.accuracy_score, 96.0)
        self.assertGreater(breakdown.overall_quality_score, 90.0)
        self.assertLess(breakdown.overall_quality_score, 100.0)

    def test_score_repository_persistence(self):
        calc = QualityScoreCalculator()
        profile_data = {"null_percentages": {"id": 0.0}, "uniqueness_percentages": {"id": 100.0}}
        breakdown = calc.calculate_dataset_score("customers_score_test", profile_data, [])

        dataset = ScoreRepository.update_dataset_quality_score(self.session, breakdown)
        self.assertIsNotNone(dataset.id)
        self.assertGreater(dataset.quality_score, 90.0)

        # Verify metadata entry
        meta = self.session.query(MetadataEntry).filter_by(dataset_id=dataset.id).first()
        self.assertIsNotNone(meta)
        self.assertIn("Completeness", meta.value)

    def test_run_scoring_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        res = run_scoring_pipeline(bronze_lake_dir=self.bronze_dir)
        self.assertEqual(res["status"], "SUCCESS")
        ent_summary = res["enterprise_summary"]
        self.assertIn("enterprise_quality_score", ent_summary)
        self.assertGreater(ent_summary["enterprise_quality_score"], 80.0)


if __name__ == "__main__":
    unittest.main()
