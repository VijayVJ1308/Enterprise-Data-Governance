"""
Phase 2 Database Schema & ER Model Verification Tests

Tests schema creation, table reflection, model relationships, and constraints.
"""

import unittest
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, inspect
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker

from backend.app.core.database import Base
from backend.app.models import (
    User,
    Role,
    Permission,
    DataOwner,
    DataSteward,
    Dataset,
    DatasetColumn,
    DatasetProfile,
    QualityRule,
    QualityResult,
    QualityIssue,
    RemediationAction,
    GovernancePolicy,
    PolicyViolation,
    ComplianceFramework,
    ComplianceControl,
    LineageNode,
    LineageEdge,
    GlossaryTerm,
    SchemaVersion,
    SchemaDriftEvent,
    DataContract,
    DataContractViolation,
    Alert,
    AuditLog,
    MetadataEntry,
)


class TestPhase2DatabaseSchema(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()

    def tearDown(self):
        self.session.close()

    def test_all_28_tables_created(self):
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        expected_tables = [
            "users",
            "roles",
            "permissions",
            "user_roles",
            "role_permissions",
            "datasets",
            "dataset_columns",
            "dataset_profiles",
            "quality_rules",
            "quality_results",
            "quality_issues",
            "data_owners",
            "data_stewards",
            "metadata",
            "glossary_terms",
            "lineage_nodes",
            "lineage_edges",
            "governance_policies",
            "policy_violations",
            "compliance_frameworks",
            "compliance_controls",
            "schema_versions",
            "schema_drift_events",
            "data_contracts",
            "data_contract_violations",
            "alerts",
            "audit_logs",
            "remediation_actions",
        ]
        for table in expected_tables:
            self.assertIn(table, table_names, f"Table missing from database schema: {table}")

    def test_user_role_permission_relationship(self):
        role = Role(name="ADMIN", description="Platform Administrator")
        perm = Permission(name="DATASET_CREATE", resource="datasets", action="create")
        user = User(username="admin_user", email="admin@enterprise.com", hashed_password="hashed_pwd")
        role.permissions.append(perm)
        user.roles.append(role)

        self.session.add_all([role, perm, user])
        self.session.commit()

        fetched_user = self.session.query(User).filter_by(username="admin_user").first()
        self.assertIsNotNone(fetched_user)
        self.assertEqual(len(fetched_user.roles), 1)
        self.assertEqual(fetched_user.roles[0].name, "ADMIN")
        self.assertEqual(len(fetched_user.roles[0].permissions), 1)
        self.assertEqual(fetched_user.roles[0].permissions[0].name, "DATASET_CREATE")

    def test_dataset_catalog_and_quality_rule_relationship(self):
        owner = DataOwner(name="Jane Doe", email="jane.owner@enterprise.com", department="Sales")
        steward = DataSteward(name="John Smith", email="john.steward@enterprise.com", department="Governance")

        dataset = Dataset(
            dataset_name="customers_raw",
            description="Raw CRM Customer Dataset",
            domain="Sales",
            source_system="CRM",
            location="minio://bronze/customers",
            format="parquet",
            owner=owner,
            steward=steward,
        )

        col = DatasetColumn(column_name="email", data_type="VARCHAR", is_nullable=True)
        dataset.columns.append(col)

        rule = QualityRule(
            rule_id="DQ-001",
            rule_name="email_not_null",
            dataset=dataset,
            column_name="email",
            rule_type="NOT_NULL",
            severity="HIGH",
        )

        self.session.add(dataset)
        self.session.commit()

        fetched_ds = self.session.query(Dataset).filter_by(dataset_name="customers_raw").first()
        self.assertIsNotNone(fetched_ds)
        self.assertEqual(fetched_ds.owner.email, "jane.owner@enterprise.com")
        self.assertEqual(len(fetched_ds.columns), 1)
        self.assertEqual(fetched_ds.columns[0].column_name, "email")
        self.assertEqual(len(fetched_ds.quality_rules), 1)
        self.assertEqual(fetched_ds.quality_rules[0].rule_id, "DQ-001")


if __name__ == "__main__":
    unittest.main()
