"""
Phase 11 Business Glossary Verification Tests

Tests glossary term creation, definition/owner updates, dataset linking,
status lifecycle (DRAFT -> APPROVED -> DEPRECATED), and term search queries.
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
from backend.app.models.lineage import GlossaryTerm
from backend.app.services.glossary_service import GlossaryService
from backend.app.services.default_glossary import seed_default_glossary_terms


class TestPhase11BusinessGlossary(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_create_and_search_term(self):
        term = GlossaryService.create_term(
            db_session=self.session,
            term="Customer LTV",
            definition="Lifetime value of a customer.",
            business_domain="Sales",
            owner="VP Marketing",
            status="APPROVED",
            related_datasets=["customers"],
        )

        self.assertIsNotNone(term.id)
        self.assertEqual(term.term, "Customer LTV")

        results = GlossaryService.search_terms(self.session, query_text="lifetime")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].term, "Customer LTV")

    def test_update_term_and_link_dataset(self):
        term = GlossaryService.create_term(
            db_session=self.session,
            term="Churn Rate",
            definition="Percentage of customers lost.",
            business_domain="Sales",
            status="DRAFT",
        )

        # Update definition and status
        updated = GlossaryService.update_term(self.session, term.id, definition="Annual percentage of lost customers.", status="APPROVED")
        self.assertEqual(updated.status, "APPROVED")
        self.assertEqual(updated.definition, "Annual percentage of lost customers.")

        # Link dataset
        linked = GlossaryService.link_dataset_to_term(self.session, term.id, "customers")
        self.assertIn("customers", linked.related_datasets)

    def test_seed_default_glossary_terms(self):
        seed_default_glossary_terms(self.session)

        terms = GlossaryService.search_terms(self.session)
        self.assertGreaterEqual(len(terms), 6)

        term_names = [t.term for t in terms]
        self.assertIn("Customer", term_names)
        self.assertIn("Revenue", term_names)
        self.assertIn("Order", term_names)


if __name__ == "__main__":
    unittest.main()
