"""
Phase 15 Governance Engine & Sensitive Data Protection Verification Tests

Tests PII classification, dynamic field masking (FULL/PARTIAL/HASH), role-based data access, governance policy evaluation, and compliance framework control mapping (GDPR, HIPAA, SOC 2, ISO 27001).
"""

import os
import sys
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
from backend.app.models.governance import GovernancePolicy, PolicyViolation, ComplianceFramework
from governance.classification.pii_classifier import PIIClassifier
from governance.masking.masking_engine import DataMaskingEngine
from governance.policies.policy_evaluator import GovernancePolicyEvaluator
from governance.compliance.compliance_service import ComplianceService
from governance.main_governance import run_governance_pipeline
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion


class TestPhase15GovernanceEngine(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = os.path.join(self.temp_dir, "raw")
        self.bronze_dir = os.path.join(self.temp_dir, "bronze")

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
            quality_score=95.0,
            refresh_frequency="DAILY"
        )
        self.session.add(self.dataset)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_pii_classifier_column_heuristics(self):
        res_email = PIIClassifier.classify_column("user_email")
        self.assertEqual(res_email["classification"], "PII")
        self.assertEqual(res_email["pii_type"], "EMAIL")

        res_ssn = PIIClassifier.classify_column("ssn_number")
        self.assertEqual(res_ssn["classification"], "PII")
        self.assertEqual(res_ssn["pii_type"], "SSN")

        res_phone = PIIClassifier.classify_column("mobile_phone")
        self.assertEqual(res_phone["classification"], "PII")

        res_internal = PIIClassifier.classify_column("order_total")
        self.assertEqual(res_internal["classification"], "INTERNAL")

    def test_pii_classifier_sample_value_heuristics(self):
        samples_ssn = ["123-45-6789", "987-65-4321"]
        res = PIIClassifier.classify_column("custom_id", sample_values=samples_ssn)
        self.assertEqual(res["classification"], "PII")
        self.assertEqual(res["pii_type"], "SSN")

    def test_data_masking_engine_strategies(self):
        # 1. Full Masking
        self.assertEqual(DataMaskingEngine.mask_value("secret", strategy="FULL"), "***MASKED***")

        # 2. Partial Masking
        self.assertEqual(DataMaskingEngine.mask_value("john@example.com", pii_type="EMAIL", strategy="PARTIAL"), "j***@example.com")
        self.assertEqual(DataMaskingEngine.mask_value("1234567890", pii_type="PHONE", strategy="PARTIAL"), "***-***-7890")
        self.assertEqual(DataMaskingEngine.mask_value("123-45-6789", pii_type="SSN", strategy="PARTIAL"), "***-**-6789")

        # 3. Hash Masking (SHA-256)
        hashed = DataMaskingEngine.mask_value("user@example.com", strategy="HASH")
        self.assertEqual(len(hashed), 16)
        self.assertNotEqual(hashed, "user@example.com")

    def test_data_masking_engine_user_roles(self):
        records = [
            {"customer_id": "C-101", "email": "alice@test.com", "salary": "$100,000"}
        ]
        class_map = {
            "email": {"classification": "PII", "pii_type": "EMAIL"},
            "salary": {"classification": "CONFIDENTIAL", "pii_type": "SALARY"}
        }

        # Analyst role: Masked
        masked_analyst = DataMaskingEngine.mask_records(records, class_map, user_role="DATA_ANALYST")
        self.assertEqual(masked_analyst[0]["email"], "a***@test.com")

        # Admin role: Unmasked
        unmasked_admin = DataMaskingEngine.mask_records(records, class_map, user_role="DATA_GOVERNANCE_ADMIN")
        self.assertEqual(unmasked_admin[0]["email"], "alice@test.com")

    def test_governance_policy_evaluator(self):
        violations = GovernancePolicyEvaluator.evaluate_policies(self.session, "customers_test")
        self.assertGreater(len(violations), 0)

        # Dataset has no owner_id, POL-001 should trigger
        pol_001_violation = any(v.description.startswith("Dataset 'customers_test' lacks an assigned Data Owner") for v in violations)
        self.assertTrue(pol_001_violation)

    def test_compliance_service_framework_mapping(self):
        status = ComplianceService.evaluate_compliance_status(self.session)
        self.assertEqual(status["status"], "COMPLIANT")
        self.assertGreaterEqual(status["overall_compliance_score"], 80.0)

        framework_codes = [f["framework_code"] for f in status["frameworks"]]
        self.assertIn("GDPR", framework_codes)
        self.assertIn("HIPAA", framework_codes)
        self.assertIn("SOC2", framework_codes)
        self.assertIn("ISO27001", framework_codes)

    def test_run_governance_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        res = run_governance_pipeline(bronze_lake_dir=self.bronze_dir)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreater(res["datasets_evaluated"], 0)
        self.assertIn("compliance_status", res)


if __name__ == "__main__":
    unittest.main()
