"""
Phase 6 Data Profiling Engine Verification Tests

Tests metric calculations (row count, null rate, uniqueness, percentiles, stddev),
pattern distributions, and database persistence into dataset_profiles table.
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
from backend.app.models.catalog import Dataset, DatasetProfile, DatasetColumn
from data_quality.profiling.pattern_analyzer import PatternAnalyzer
from data_quality.profiling.profiler import DataProfiler
from data_quality.profiling.profile_repository import ProfileRepository
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion
from data_quality.main_profiling import run_profiling_pipeline


class TestPhase6DataProfiling(unittest.TestCase):

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

    def test_pattern_analyzer(self):
        samples = ["user@example.com", "admin@company.org", "invalid_email_no_at"]
        dist = PatternAnalyzer.analyze_patterns(samples)
        self.assertIn("EMAIL", dist)
        self.assertGreater(dist["EMAIL"], 50.0)

    def test_data_profiler_statistics(self):
        records = [
            {"id": "1", "age": 20, "salary": 50000.0, "email": "a@x.com"},
            {"id": "2", "age": 30, "salary": 70000.0, "email": "b@x.com"},
            {"id": "3", "age": 40, "salary": 90000.0, "email": None},
            {"id": "4", "age": 50, "salary": 110000.0, "email": "d@x.com"},
        ]
        profiler = DataProfiler()
        profile = profiler.profile_records("test_dataset", records)

        self.assertEqual(profile["row_count"], 4)
        self.assertEqual(profile["column_count"], 4)
        self.assertEqual(profile["null_counts"]["email"], 1)
        self.assertEqual(profile["null_percentages"]["email"], 25.0)

        # Numerical statistics check
        age_stats = profile["column_statistics"]["age"]["numeric_statistics"]
        self.assertIsNotNone(age_stats)
        self.assertEqual(age_stats["min"], 20.0)
        self.assertEqual(age_stats["max"], 50.0)
        self.assertEqual(age_stats["mean"], 35.0)
        self.assertEqual(age_stats["median"], 35.0)
        self.assertIn("percentiles", age_stats)
        self.assertEqual(age_stats["percentiles"]["p50"], 35.0)

    def test_profile_repository_persistence(self):
        profiler = DataProfiler()
        records = [
            {"cust_id": "C-1", "score": 100},
            {"cust_id": "C-2", "score": 90},
        ]
        profile = profiler.profile_records("test_repo_cust", records)
        saved_profile = ProfileRepository.save_profile(self.session, profile)

        self.assertIsNotNone(saved_profile.id)
        self.assertEqual(saved_profile.row_count, 2)

        # Query catalog tables
        dataset = self.session.query(Dataset).filter_by(dataset_name="test_repo_cust").first()
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.row_count, 2)

        cols = self.session.query(DatasetColumn).filter_by(dataset_id=dataset.id).all()
        self.assertEqual(len(cols), 2)

    def test_run_profiling_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        results = run_profiling_pipeline(bronze_lake_dir=self.bronze_dir)
        self.assertGreater(len(results), 4)
        first_res = results[0]
        self.assertIn("row_count", first_res)
        self.assertIn("column_statistics", first_res)


if __name__ == "__main__":
    unittest.main()
