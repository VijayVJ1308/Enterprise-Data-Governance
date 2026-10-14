"""
Phase 13 Schema Drift Monitoring & Data Contracts Verification Tests

Tests YAML data contract parsing, contract registration, multi-dimensional validation
(schema, quality SLA, freshness SLA), contract violation persistence, schema versioning,
and automated schema drift detection (added, removed, type changed, nullability altered).
"""

import os
import sys
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import Base
from backend.app.models.catalog import Dataset
from contracts.contract_validator import ContractValidator
from contracts.drift_detector import SchemaDriftEngine


SAMPLE_YAML_CONTRACT = """
contract_name: customers_contract_v1
dataset: customers_test
version: 1.0.0
owner: jane.owner@enterprise.com
domain: Sales

schema:
  - name: customer_id
    type: STRING
    nullable: false
  - name: first_name
    type: STRING
    nullable: false
  - name: email
    type: STRING
    nullable: false

quality_slas:
  min_quality_score: 90.0

freshness_slas:
  max_age_hours: 24
"""


class TestPhase13ContractsAndDrift(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
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

    def test_register_and_validate_passing_contract(self):
        contract = ContractValidator.register_contract(
            db_session=self.session,
            dataset_name="customers_test",
            yaml_spec=SAMPLE_YAML_CONTRACT,
        )

        self.assertIsNotNone(contract.id)
        self.assertEqual(contract.contract_name, "customers_contract_v1")

        current_spec = [
            {"name": "customer_id", "type": "STRING", "nullable": False},
            {"name": "first_name", "type": "STRING", "nullable": False},
            {"name": "email", "type": "STRING", "nullable": False},
        ]
        now = datetime.now(timezone.utc)

        result = ContractValidator.validate_contract(
            db_session=self.session,
            contract_name="customers_contract_v1",
            current_columns_spec=current_spec,
            current_quality_score=95.0,
            data_timestamp=now,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["violations_count"], 0)

    def test_validate_failing_contract_violations(self):
        ContractValidator.register_contract(
            db_session=self.session,
            dataset_name="customers_test",
            yaml_spec=SAMPLE_YAML_CONTRACT,
        )

        # Mismatched type, missing required email column, low quality score, stale data
        invalid_spec = [
            {"name": "customer_id", "type": "INTEGER", "nullable": False},
            {"name": "first_name", "type": "STRING", "nullable": False},
        ]
        stale_time = datetime.now(timezone.utc) - timedelta(hours=48)

        result = ContractValidator.validate_contract(
            db_session=self.session,
            contract_name="customers_contract_v1",
            current_columns_spec=invalid_spec,
            current_quality_score=75.0,
            data_timestamp=stale_time,
        )

        self.assertFalse(result["passed"])
        self.assertGreaterEqual(result["violations_count"], 3)

        violations = ContractValidator.get_contract_violations(self.session, "customers_contract_v1")
        v_types = [v.violation_type for v in violations]
        self.assertIn("SCHEMA_MISMATCH", v_types)
        self.assertIn("QUALITY_SLA_BREACH", v_types)
        self.assertIn("FRESHNESS_SLA_BREACH", v_types)

    def test_schema_drift_detection(self):
        initial_spec = [
            {"name": "customer_id", "type": "STRING", "nullable": False},
            {"name": "first_name", "type": "STRING", "nullable": True},
            {"name": "email", "type": "STRING", "nullable": True},
        ]

        # 1. Record baseline schema version v1
        v1 = SchemaDriftEngine.record_schema_version(self.session, "customers_test", initial_spec)
        self.assertEqual(v1.version_number, 1)

        # 2. Check no drift when schema is identical
        res1 = SchemaDriftEngine.detect_schema_drift(self.session, "customers_test", initial_spec)
        self.assertFalse(res1["drift_detected"])

        # 3. Mutate schema: add 'phone', remove 'email', change 'first_name' type to INTEGER
        mutated_spec = [
            {"name": "customer_id", "type": "STRING", "nullable": False},
            {"name": "first_name", "type": "INTEGER", "nullable": False},
            {"name": "phone", "type": "STRING", "nullable": True},
        ]

        res2 = SchemaDriftEngine.detect_schema_drift(self.session, "customers_test", mutated_spec)
        self.assertTrue(res2["drift_detected"])
        self.assertEqual(res2["current_version"], 2)

        drift_types = [dev["drift_type"] for dev in res2["drift_events"]]
        self.assertIn("ADDED", drift_types)
        self.assertIn("REMOVED", drift_types)
        self.assertIn("TYPE_CHANGED", drift_types)

        events = SchemaDriftEngine.get_drift_events(self.session, "customers_test")
        self.assertGreaterEqual(len(events), 3)


if __name__ == "__main__":
    unittest.main()
