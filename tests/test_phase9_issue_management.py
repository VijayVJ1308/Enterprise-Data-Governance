"""
Phase 9 Issue Management Verification Tests

Tests Issue creation, state machine transitions (OPEN -> IN_PROGRESS -> RESOLVED -> REOPENED),
invalid state rejection, assignment, and database query filtering.
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
from backend.app.models.quality import QualityIssue
from data_quality.issue_management.issue_service import IssueManagementService


class TestPhase9IssueManagement(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_create_and_query_issue(self):
        issue = IssueManagementService.create_issue(
            db_session=self.session,
            dataset_name="customers_issues_test",
            column_name="email",
            description="Null email values detected in 25 records.",
            severity="CRITICAL",
            owner="Data Steward Team",
        )

        self.assertIsNotNone(issue.id)
        self.assertEqual(issue.status, "OPEN")
        self.assertEqual(issue.severity, "CRITICAL")

        # Query filtered
        fetched = IssueManagementService.list_issues(self.session, dataset_name="customers_issues_test", severity="CRITICAL")
        self.assertEqual(len(fetched), 1)
        self.assertEqual(fetched[0].issue_id, issue.issue_id)

    def test_state_machine_valid_transitions(self):
        issue = IssueManagementService.create_issue(
            db_session=self.session,
            dataset_name="orders_test",
            description="Invalid total calculations.",
            severity="HIGH",
        )

        # OPEN -> IN_PROGRESS
        res1 = IssueManagementService.transition_status(self.session, issue.issue_id, "IN_PROGRESS")
        self.assertEqual(res1.status, "IN_PROGRESS")

        # IN_PROGRESS -> RESOLVED
        res2 = IssueManagementService.transition_status(self.session, issue.issue_id, "RESOLVED", resolution_notes="Applied deterministic remediation.")
        self.assertEqual(res2.status, "RESOLVED")
        self.assertIsNotNone(res2.resolved_at)

        # RESOLVED -> REOPENED
        res3 = IssueManagementService.transition_status(self.session, issue.issue_id, "REOPENED")
        self.assertEqual(res3.status, "REOPENED")
        self.assertIsNone(res3.resolved_at)

    def test_state_machine_invalid_transition_rejected(self):
        issue = IssueManagementService.create_issue(
            db_session=self.session,
            dataset_name="products_test",
            description="Negative prices detected.",
            severity="MEDIUM",
        )

        # OPEN -> REOPENED is invalid
        with self.assertRaises(ValueError):
            IssueManagementService.transition_status(self.session, issue.issue_id, "REOPENED")

    def test_assign_issue(self):
        issue = IssueManagementService.create_issue(
            db_session=self.session,
            dataset_name="suppliers_test",
            description="Missing contact email.",
            severity="LOW",
        )

        assigned = IssueManagementService.assign_issue(self.session, issue.issue_id, "john.steward@enterprise.com")
        self.assertEqual(assigned.assigned_to, "john.steward@enterprise.com")


if __name__ == "__main__":
    unittest.main()
