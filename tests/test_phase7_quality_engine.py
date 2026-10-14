"""
Phase 7 Data Quality Rule Engine Verification Tests

Tests rule execution for 14+ declarative rule types, pass rate metrics,
issue creation, and database persistence into quality_rules, quality_results, and quality_issues.
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
from backend.app.models.quality import QualityRule, QualityResult, QualityIssue
from data_quality.rules.rule_definitions import QualityRuleSpec
from data_quality.engine.rule_evaluator import RuleEvaluator
from data_quality.engine.quality_repository import QualityRepository
from data_generator.main import generate_all_datasets
from ingestion.main import run_ingestion
from data_quality.main_quality import run_quality_pipeline


class TestPhase7QualityEngine(unittest.TestCase):

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

    def test_evaluator_not_null_and_unique(self):
        records = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"},
            {"id": None, "name": "Charlie"},
            {"id": "2", "name": "Duplicate Bob"},
        ]
        evaluator = RuleEvaluator()

        # Not Null rule
        rule_null = QualityRuleSpec(rule_id="R-1", rule_name="not_null_id", dataset_name="test", column_name="id", rule_type="NOT_NULL")
        res_null = evaluator.evaluate_rule(rule_null, records)
        self.assertFalse(res_null.passed)
        self.assertEqual(res_null.failed_records, 1)

        # Unique rule
        rule_uniq = QualityRuleSpec(rule_id="R-2", rule_name="unique_id", dataset_name="test", column_name="id", rule_type="UNIQUE")
        res_uniq = evaluator.evaluate_rule(rule_uniq, records)
        self.assertFalse(res_uniq.passed)

    def test_evaluator_referential_integrity(self):
        customers = [{"customer_id": "C-1"}, {"customer_id": "C-2"}]
        orders = [{"order_id": "O-1", "customer_id": "C-1"}, {"order_id": "O-2", "customer_id": "C-999_BAD"}]
        parents = {"customers": customers}

        rule = QualityRuleSpec(
            rule_id="R-FK",
            rule_name="fk_cust",
            dataset_name="orders",
            column_name="customer_id",
            rule_type="REFERENTIAL_INTEGRITY",
            params={"parent_dataset": "customers", "parent_column": "customer_id"},
        )
        evaluator = RuleEvaluator()
        res = evaluator.evaluate_rule(rule, orders, parent_datasets=parents)

        self.assertFalse(res.passed)
        self.assertEqual(res.failed_records, 1)

    def test_quality_repository_persistence_and_issue_creation(self):
        evaluator = RuleEvaluator()
        records = [{"email": "invalid_email_format"}]
        rule_spec = QualityRuleSpec(
            rule_id="DQ-TEST-001",
            rule_name="email_fmt",
            dataset_name="test_dataset",
            column_name="email",
            rule_type="VALID_FORMAT",
            rule_expression="EMAIL",
            severity="HIGH",
        )
        eval_res = evaluator.evaluate_rule(rule_spec, records)
        QualityRepository.save_rule_and_result(self.session, rule_spec, eval_res)

        # Query database tables
        db_rule = self.session.query(QualityRule).filter_by(rule_id="DQ-TEST-001").first()
        self.assertIsNotNone(db_rule)

        db_result = self.session.query(QualityResult).filter_by(rule_id=db_rule.id).first()
        self.assertIsNotNone(db_result)
        self.assertFalse(db_result.passed)

        # Verify auto-creation of QualityIssue
        db_issue = self.session.query(QualityIssue).filter_by(issue_id="ISS-DQ-TEST-001").first()
        self.assertIsNotNone(db_issue)
        self.assertEqual(db_issue.status, "OPEN")
        self.assertEqual(db_issue.severity, "HIGH")

    def test_run_quality_pipeline_end_to_end(self):
        generate_all_datasets(scale_name="small", output_dir=self.raw_dir)
        run_ingestion(source_dir=self.raw_dir, target_dir=self.bronze_dir)

        results = run_quality_pipeline(bronze_lake_dir=self.bronze_dir)
        self.assertGreater(len(results), 5)
        first_res = results[0]
        self.assertIn("rule_id", first_res)
        self.assertIn("pass_rate", first_res)


if __name__ == "__main__":
    unittest.main()
