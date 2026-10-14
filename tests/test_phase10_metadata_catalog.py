"""
Phase 10 Metadata Catalog Verification Tests

Tests dataset registration, multi-parameter search/discovery,
dataset detail fetching, and certification workflow management.
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
from backend.app.models.catalog import Dataset, DataOwner, DataSteward
from backend.app.services.catalog_service import CatalogService


class TestPhase10MetadataCatalog(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Seed sample owners
        owner = DataOwner(name="Jane Doe", email="jane.owner@enterprise.com", department="Sales")
        steward = DataSteward(name="John Smith", email="john.steward@enterprise.com", department="Governance")
        self.session.add_all([owner, steward])
        self.session.commit()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_register_and_get_dataset_details(self):
        dataset = CatalogService.register_dataset(
            db_session=self.session,
            dataset_name="customers_catalog_test",
            domain="Sales",
            source_system="CRM",
            location="minio://bronze/customers",
            classification="PII",
            owner_email="jane.owner@enterprise.com",
            steward_email="john.steward@enterprise.com",
        )

        self.assertIsNotNone(dataset.id)
        self.assertEqual(dataset.domain, "Sales")
        self.assertEqual(dataset.classification, "PII")

        details = CatalogService.get_dataset_details(self.session, dataset.id)
        self.assertIsNotNone(details)
        self.assertEqual(details["dataset_name"], "customers_catalog_test")
        self.assertEqual(details["owner"], "Jane Doe")
        self.assertEqual(details["steward"], "John Smith")

    def test_search_catalog_with_filters(self):
        CatalogService.register_dataset(self.session, "sales_orders", "Sales", "ERP", "minio://bronze/orders", classification="INTERNAL")
        CatalogService.register_dataset(self.session, "hr_employees", "HR", "API", "minio://bronze/employees", classification="CONFIDENTIAL")

        # 1. Search by domain
        sales_results = CatalogService.search_catalog(self.session, domain="Sales")
        self.assertEqual(len(sales_results), 1)
        self.assertEqual(sales_results[0].dataset_name, "sales_orders")

        # 2. Search by classification
        conf_results = CatalogService.search_catalog(self.session, classification="CONFIDENTIAL")
        self.assertEqual(len(conf_results), 1)
        self.assertEqual(conf_results[0].dataset_name, "hr_employees")

        # 3. Text query search
        text_results = CatalogService.search_catalog(self.session, query_text="employee")
        self.assertEqual(len(text_results), 1)

    def test_update_certification_status(self):
        dataset = CatalogService.register_dataset(self.session, "finance_general_ledger", "Finance", "ERP", "minio://bronze/ledger")
        self.assertEqual(dataset.certification_status, "UNCERTIFIED")

        updated = CatalogService.update_certification_status(self.session, dataset.id, "CERTIFIED")
        self.assertEqual(updated.certification_status, "CERTIFIED")

        with self.assertRaises(ValueError):
            CatalogService.update_certification_status(self.session, dataset.id, "INVALID_STATUS")


if __name__ == "__main__":
    unittest.main()
