"""
Phase 14 Automated Data Remediation Engine Verification Tests

Tests whitespace trimming, case normalization, phone & country standardization, default filling, deduplication, DB action logging, and issue lifecycle auto-resolution.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base
from backend.app.models.catalog import Dataset
from backend.app.models.quality import QualityIssue, RemediationAction
from data_quality.remediation.remediation_engine import RemediationEngine, RemediationService
from data_quality.main_remediation import run_remediation_pipeline
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion


class TestPhase14RemediationEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.bronze_dir = os.path.join(self.temp_dir, "bronze")
        self.silver_dir = os.path.join(self.temp_dir, "silver")

        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Seed test dataset in catalog
        self.dataset = Dataset(
            dataset_name="customers_test",
            domain="Sales",
            source_system="CRM",
            location="minio://bronze/customers_test",
            format="PARQUET",
        )
        self.session.add(self.dataset)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_trim_whitespace(self):
        records = [
            {"id": "1", "name": "  Alice Smith  ", "city": "New York  "},
            {"id": "2", "name": "Bob Jones", "city": " Chicago"},
        ]
        cleaned, affected = RemediationEngine.trim_whitespace(records)
        self.assertEqual(affected, 2)
        self.assertEqual(cleaned[0]["name"], "Alice Smith")
        self.assertEqual(cleaned[0]["city"], "New York")
        self.assertEqual(cleaned[1]["city"], "Chicago")

    def test_normalize_case(self):
        records = [
            {"email": "USER@EXAMPLE.COM", "state": "ny", "name": "john doe"},
            {"email": "Alice@Example.Com", "state": "ca", "name": "JANE SMITH"},
        ]
        case_map = {"email": "lower", "state": "upper", "name": "title"}
        cleaned, affected = RemediationEngine.normalize_case(records, case_map)
        self.assertEqual(affected, 2)
        self.assertEqual(cleaned[0]["email"], "user@example.com")
        self.assertEqual(cleaned[0]["state"], "NY")
        self.assertEqual(cleaned[0]["name"], "John Doe")

    def test_format_phone_numbers(self):
        records = [
            {"phone": "1234567890"},
            {"phone": "(987) 654-3210"},
            {"phone": "+1-555-123-4567"},
        ]
        cleaned, affected = RemediationEngine.format_phone_numbers(records, column_name="phone")
        self.assertEqual(affected, 2)
        self.assertEqual(cleaned[0]["phone"], "+1-123-456-7890")
        self.assertEqual(cleaned[1]["phone"], "+1-987-654-3210")
        self.assertEqual(cleaned[2]["phone"], "+1-555-123-4567")

    def test_standardize_country_codes(self):
        records = [
            {"country": "United States"},
            {"country": "usa"},
            {"country": "United Kingdom"},
            {"country": "Germany"},
        ]
        cleaned, affected = RemediationEngine.standardize_country_codes(records, column_name="country")
        self.assertEqual(affected, 4)
        self.assertEqual(cleaned[0]["country"], "USA")
        self.assertEqual(cleaned[1]["country"], "USA")
        self.assertEqual(cleaned[2]["country"], "GBR")
        self.assertEqual(cleaned[3]["country"], "DEU")

    def test_fill_defaults(self):
        records = [
            {"id": "1", "status": None, "country": ""},
            {"id": "2", "status": "ACTIVE", "country": "NULL"},
        ]
        defaults_map = {"status": "PENDING", "country": "USA"}
        cleaned, affected = RemediationEngine.fill_defaults(records, defaults_map)
        self.assertEqual(affected, 2)
        self.assertEqual(cleaned[0]["status"], "PENDING")
        self.assertEqual(cleaned[0]["country"], "USA")
        self.assertEqual(cleaned[1]["country"], "USA")

    def test_deduplicate_records(self):
        records = [
            {"id": "1", "name": "Alice"},
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
        ]
        cleaned, dropped = RemediationEngine.deduplicate_records(records, key_columns=["id"])
        self.assertEqual(dropped, 1)
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(cleaned[0]["id"], "1")
        self.assertEqual(cleaned[1]["id"], "2")

    def test_remediation_service_db_logging_and_issue_resolution(self):
        # Create an open quality issue
        issue = QualityIssue(
            issue_id="ISS-999",
            dataset_id=self.dataset.id,
            column_name="email",
            severity="HIGH",
            description="Email whitespace present",
            status="OPEN",
            detected_at=datetime.now(timezone.utc),
        )
        self.session.add(issue)
        self.session.commit()

        records = [{"email": "  user@test.com  "}]
        cleaned, rem_action = RemediationService.execute_remediation_action(
            db_session=self.session,
            dataset_name="customers_test",
            action_type="TRIM_WHITESPACE",
            records=records,
            params={"columns": ["email"]},
            issue_id="ISS-999",
            executed_by="TEST_RUNNER"
        )

        self.assertEqual(rem_action.affected_rows, 1)
        self.assertEqual(rem_action.action_type, "TRIM_WHITESPACE")

        # Verify Issue was transitioned to RESOLVED
        updated_issue = self.session.query(QualityIssue).filter_by(issue_id="ISS-999").first()
        self.assertEqual(updated_issue.status, "RESOLVED")
        self.assertIn("Auto-remediated", updated_issue.resolution_notes)

    def test_run_remediation_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        res = run_remediation_pipeline(bronze_lake_dir=self.bronze_dir, silver_lake_dir=self.silver_dir)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(res["datasets_processed"], 0)

        # Check remediated output file for customers
        remediated_cust_file = os.path.join(self.silver_dir, "customers", "customers_remediated.json")
        self.assertTrue(os.path.exists(remediated_cust_file))

        with open(remediated_cust_file, "r", encoding="utf-8") as f:
            remediated_data = json.load(f)
        self.assertIsInstance(remediated_data, list)
        self.assertGreater(len(remediated_data), 0)


if __name__ == "__main__":
    unittest.main()
