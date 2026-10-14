"""
Phase 5 Bronze/Silver/Gold Data Lake Storage Verification Tests

Tests Parquet serialization, MinIO S3 compatibility interface, and Medallion layer promotions.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_lake.parquet_utils import ParquetUtils
from data_lake.minio_client import MinIOClient
from data_lake.medallion_manager import MedallionManager
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion


class TestPhase5DataLake(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.lake_dir = os.path.join(self.temp_dir, "lake")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_parquet_utils_read_write(self):
        records = [
            {"id": "1", "name": "  Alice  ", "score": 95.5},
            {"id": "2", "name": "Bob", "score": 88.0},
        ]
        file_path = os.path.join(self.temp_dir, "test.parquet")
        written_path = ParquetUtils.write_parquet(records, file_path)
        self.assertTrue(os.path.exists(written_path))

        read_records = ParquetUtils.read_parquet(written_path)
        self.assertEqual(len(read_records), 2)
        self.assertEqual(read_records[0]["name"], "  Alice  ")

    def test_minio_client_interface(self):
        client = MinIOClient()
        test_file = os.path.join(self.temp_dir, "sample.txt")
        with open(test_file, "w") as f:
            f.write("lake content")

        uploaded = client.upload_file("bronze-lake", "sample.txt", test_file)
        self.assertIsNotNone(uploaded)

    def test_medallion_manager_bronze_silver_gold_promotion(self):
        # 1. Generate Raw & Ingest to Bronze
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        bronze_landing = os.path.join(self.lake_dir, "bronze")
        run_ingestion(source_dir=self.raw_dir, target_dir=bronze_landing)

        manager = MedallionManager(base_lake_dir=self.lake_dir)

        # 2. Promote Bronze -> Silver
        silver_res = manager.promote_bronze_to_silver("customers")
        self.assertEqual(silver_res["status"], "SUCCESS")
        self.assertTrue(os.path.exists(silver_res["silver_file"]))

        manager.promote_bronze_to_silver("orders")

        # 3. Promote Silver -> Gold
        gold_res = manager.build_gold_marts()
        self.assertEqual(gold_res["status"], "SUCCESS")
        self.assertGreater(len(gold_res["marts"]), 1)

        # Verify Gold Parquet mart file exists
        gold_mart_path = os.path.join(self.lake_dir, "gold", "dim_customers", "dim_customers.parquet")
        self.assertTrue(os.path.exists(gold_mart_path))


if __name__ == "__main__":
    unittest.main()
