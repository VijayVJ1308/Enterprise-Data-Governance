"""
Phase 17 FastAPI REST Backend Implementation Verification Tests
Tests health, catalog, quality, issues, remediation, glossary, lineage, contracts, governance, and ML endpoints.
"""

import sys
import os
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import Base, engine


class TestPhase17FastAPIBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    def test_01_health_check_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")

    def test_02_register_and_search_catalog(self):
        # Register dataset
        payload = {
            "dataset_name": "customers_api_test",
            "domain": "CRM",
            "source_system": "PostgreSQL",
            "location": "data/lake/bronze/customers_api_test",
            "description": "API Test Customer Dataset",
            "classification": "CONFIDENTIAL",
        }
        res_reg = self.client.post("/api/v1/catalog/register", json=payload)
        self.assertEqual(res_reg.status_code, 200)
        reg_data = res_reg.json()
        self.assertEqual(reg_data["status"], "success")

        # Search catalog
        res_search = self.client.get("/api/v1/catalog/search?q=customers_api_test")
        self.assertEqual(res_search.status_code, 200)
        search_data = res_search.json()
        self.assertTrue(len(search_data) >= 1)
        self.assertEqual(search_data[0]["dataset_name"], "customers_api_test")

        # Get dataset details
        res_details = self.client.get(f"/api/v1/catalog/{reg_data['dataset_id']}")
        self.assertEqual(res_details.status_code, 200)
        details = res_details.json()
        self.assertEqual(details["dataset_name"], "customers_api_test")

    def test_03_quality_profiling_and_rules(self):
        sample_records = [
            {"customer_id": "CUST-001", "email": "alice@example.com", "age": 30},
            {"customer_id": "CUST-002", "email": "bob@example.com", "age": 25},
        ]
        res_prof = self.client.post(
            "/api/v1/quality/profile",
            json={"dataset_name": "customers_api_test", "records": sample_records},
        )
        self.assertEqual(res_prof.status_code, 200)
        prof_data = res_prof.json()
        self.assertEqual(prof_data["row_count"], 2)

        res_eval = self.client.post(
            "/api/v1/quality/evaluate",
            json={"dataset_name": "customers_api_test", "records": sample_records},
        )
        self.assertEqual(res_eval.status_code, 200)
        eval_data = res_eval.json()
        self.assertTrue(len(eval_data["rule_results"]) > 0)

    def test_04_issue_management_lifecycle(self):
        # Create issue
        res_create = self.client.post(
            "/api/v1/issues/",
            json={
                "dataset_name": "customers_api_test",
                "description": "High null rate in email field",
                "column_name": "email",
                "severity": "HIGH",
            },
        )
        self.assertEqual(res_create.status_code, 200)
        issue_id = res_create.json()["issue_id"]

        # Transition status OPEN -> IN_PROGRESS
        res_trans = self.client.patch(
            f"/api/v1/issues/{issue_id}/transition",
            json={"new_status": "IN_PROGRESS", "user": "STEWARD"},
        )
        self.assertEqual(res_trans.status_code, 200)
        self.assertEqual(res_trans.json()["current_status"], "IN_PROGRESS")

        # Assign issue
        res_assign = self.client.patch(
            f"/api/v1/issues/{issue_id}/assign",
            json={"assignee_email": "jane.doe@enterprise.com"},
        )
        self.assertEqual(res_assign.status_code, 200)
        self.assertEqual(res_assign.json()["assigned_to"], "jane.doe@enterprise.com")

    def test_05_remediation_engine_endpoint(self):
        raw_records = [
            {"name": "  Alice Smith  ", "country": "usa"},
            {"name": "Bob Jones", "country": "United States"},
        ]
        res_rem = self.client.post(
            "/api/v1/remediation/execute",
            json={
                "dataset_name": "customers_api_test",
                "action_type": "TRIM_WHITESPACE",
                "records": raw_records,
            },
        )
        self.assertEqual(res_rem.status_code, 200)
        rem_data = res_rem.json()
        self.assertEqual(rem_data["status"], "success")
        self.assertEqual(rem_data["remediated_records"][0]["name"], "Alice Smith")

    def test_06_business_glossary_endpoints(self):
        # Create term
        res_create = self.client.post(
            "/api/v1/glossary/",
            json={
                "term": "Customer Lifetime Value",
                "definition": "Predicted total revenue a customer will generate.",
                "business_domain": "Finance",
                "owner": "cfo@enterprise.com",
            },
        )
        self.assertEqual(res_create.status_code, 200)

        # Search terms
        res_search = self.client.get("/api/v1/glossary/?q=Lifetime")
        self.assertEqual(res_search.status_code, 200)
        terms = res_search.json()
        self.assertTrue(len(terms) >= 1)
        self.assertEqual(terms[0]["term"], "Customer Lifetime Value")

    def test_07_data_lineage_endpoints(self):
        # Add node
        res_n1 = self.client.post(
            "/api/v1/lineage/node",
            json={"node_key": "raw_cust_api", "name": "Raw Customers API", "node_type": "DATASET"},
        )
        res_n2 = self.client.post(
            "/api/v1/lineage/node",
            json={"node_key": "clean_cust_api", "name": "Clean Customers API", "node_type": "DATASET"},
        )
        self.assertEqual(res_n1.status_code, 200)
        self.assertEqual(res_n2.status_code, 200)

        # Add edge
        res_edge = self.client.post(
            "/api/v1/lineage/edge",
            json={
                "source_key": "raw_cust_api",
                "target_key": "clean_cust_api",
                "transformation_type": "REMEDIATION",
            },
        )
        self.assertEqual(res_edge.status_code, 200)

        # Get graph
        res_graph = self.client.get("/api/v1/lineage/graph")
        self.assertEqual(res_graph.status_code, 200)
        self.assertTrue(len(res_graph.json()["nodes"]) >= 2)

    def test_08_data_contracts_and_drift_endpoints(self):
        # Register Contract
        yaml_spec = """
contract_name: cust_api_contract
version: 1.0.0
schema:
  - name: customer_id
    type: STRING
    nullable: false
"""
        res_reg = self.client.post(
            "/api/v1/contracts/register",
            json={
                "dataset_name": "customers_api_test",
                "yaml_spec": yaml_spec,
                "contract_name": "cust_api_contract",
            },
        )
        self.assertEqual(res_reg.status_code, 200)

        # Detect Drift
        cols = [{"name": "customer_id", "type": "STRING", "nullable": False}]
        res_drift = self.client.post(
            "/api/v1/contracts/drift/detect",
            json={"dataset_name": "customers_api_test", "columns_spec": cols},
        )
        self.assertEqual(res_drift.status_code, 200)

    def test_09_governance_and_compliance_endpoints(self):
        # Classify PII
        sample = [{"name": "Alice", "ssn": "123-45-6789", "email": "alice@test.com"}]
        res_class = self.client.post("/api/v1/governance/classify", json={"records": sample})
        self.assertEqual(res_class.status_code, 200)
        self.assertIn("email", res_class.json()["pii_columns"])

        # Compliance status
        res_comp = self.client.get("/api/v1/governance/compliance")
        self.assertEqual(res_comp.status_code, 200)
        self.assertIn("overall_compliance_score", res_comp.json())

    def test_10_ml_anomalies_and_recommendations(self):
        # Volume Anomaly
        res_anom = self.client.post(
            "/api/v1/ml/anomalies/detect",
            json={"historical_counts": [100, 102, 98, 101], "current_count": 500},
        )
        self.assertEqual(res_anom.status_code, 200)
        self.assertTrue(res_anom.json()["is_anomaly"])

        # ML Recommendations
        sample = [{"id": 1, "price": 99.99}]
        res_rec = self.client.post(
            "/api/v1/ml/rules/recommend",
            json={"dataset_name": "products_api_test", "records": sample},
        )
        self.assertEqual(res_rec.status_code, 200)
        self.assertTrue(res_rec.json()["recommended_rules_count"] > 0)


if __name__ == "__main__":
    unittest.main()
