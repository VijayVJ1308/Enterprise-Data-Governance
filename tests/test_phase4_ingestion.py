"""
Phase 4 Data Ingestion Framework Verification Tests

Tests Batch Ingestor (CSV, JSON), API Ingestor, Stream Ingestor, and metadata enrichment.
"""

import os
import sys
import shutil
import tempfile
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_generator.main import generate_all_datasets
from ingestion.batch.batch_ingestor import BatchIngestor
from ingestion.api.api_ingestor import ApiIngestor
from ingestion.streaming.stream_ingestor import StreamIngestor
from ingestion.main import run_ingestion


class TestPhase4Ingestion(unittest.TestCase):

    def setUp(self):
        self.raw_dir = tempfile.mkdtemp()
        self.bronze_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.raw_dir)
        shutil.rmtree(self.bronze_dir)

    def test_batch_ingestor_csv_and_metadata_enrichment(self):
        # Generate sample CSV dataset
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        csv_path = os.path.join(self.raw_dir, "customers.csv")

        ingestor = BatchIngestor(output_dir=self.bronze_dir)
        result = ingestor.ingest_dataset("customers", "csv", csv_path)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreater(result["record_count"], 0)
        self.assertTrue(os.path.exists(result["output_file"]))

        # Verify metadata enrichment in landing file
        records = ingestor.read_json(result["output_file"])
        first_rec = records[0]
        self.assertIn("_ingestion_id", first_rec)
        self.assertIn("_ingestion_timestamp", first_rec)
        self.assertIn("_record_hash", first_rec)
        self.assertEqual(first_rec["_source_type"], "csv")

    def test_api_ingestor(self):
        api_ingestor = ApiIngestor(output_dir=self.bronze_dir)
        res = api_ingestor.ingest_api_endpoint("employees_api", "http://localhost:8000/api/v1/employees")

        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(res["record_count"], 0)
        self.assertTrue(os.path.exists(res["output_file"]))

    def test_stream_ingestor(self):
        stream_ingestor = StreamIngestor(output_dir=self.bronze_dir)
        sample_payloads = [
            {"event_id": "EVT-001", "user_id": "U-100", "action": "LOGIN"},
            {"event_id": "EVT-002", "user_id": "U-101", "action": "PURCHASE"},
        ]
        res = stream_ingestor.ingest_stream_batch("user_events", "events_topic", sample_payloads)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["record_count"], 2)
        self.assertTrue(os.path.exists(res["output_file"]))

    def test_run_ingestion_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        ingested_summary = run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)
        self.assertGreater(len(ingested_summary), 5)


if __name__ == "__main__":
    unittest.main()
