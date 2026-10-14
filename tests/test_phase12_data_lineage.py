"""
Phase 12 Data Lineage & Impact Analysis Verification Tests

Tests dataset/column/pipeline lineage graph creation, end-to-end lineage graph queries,
upstream dependency resolution, downstream traversal, and downstream impact analysis.
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
from lineage.lineage_service import LineageService
from lineage.impact_analysis import ImpactAnalysisEngine
from lineage.default_lineage import seed_default_lineage


class TestPhase12DataLineage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        shutil.rmtree(self.temp_dir)

    def test_create_nodes_and_edges(self):
        # Create dataset and pipeline nodes
        src_node = LineageService.add_node(
            self.session,
            node_key="src:pos_db.transactions",
            name="POS Transactions Table",
            node_type="DATASET",
            domain="Retail",
        )
        pipe_node = LineageService.add_node(
            self.session,
            node_key="pipe:pos_ingestor",
            name="POS Batch Ingestor",
            node_type="PIPELINE",
            domain="Retail",
        )
        tgt_node = LineageService.add_node(
            self.session,
            node_key="lake:bronze.transactions",
            name="Bronze POS Transactions",
            node_type="DATASET",
            domain="Retail",
        )

        self.assertIsNotNone(src_node.id)
        self.assertEqual(pipe_node.node_type, "PIPELINE")

        # Create edges
        edge1 = LineageService.add_edge(self.session, "src:pos_db.transactions", "pipe:pos_ingestor", "DIRECT_TRANSFORM", "job_pos_batch")
        edge2 = LineageService.add_edge(self.session, "pipe:pos_ingestor", "lake:bronze.transactions", "DIRECT_TRANSFORM", "job_pos_batch")

        self.assertIsNotNone(edge1.id)
        self.assertEqual(edge2.pipeline_name, "job_pos_batch")

        graph = LineageService.get_lineage_graph(self.session)
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(len(graph["edges"]), 2)

    def test_seed_default_lineage(self):
        result = seed_default_lineage(self.session)
        self.assertGreaterEqual(result["nodes"], 15)
        self.assertGreaterEqual(result["edges"], 12)

        graph = LineageService.get_lineage_graph(self.session)
        node_keys = [n["key"] for n in graph["nodes"]]
        self.assertIn("src:crm_postgres.customers", node_keys)
        self.assertIn("lake:gold.customer_360_mart", node_keys)
        self.assertIn("dash:executive_sales_overview", node_keys)

    def test_impact_analysis_on_source_failure(self):
        seed_default_lineage(self.session)

        # Analyze impact if 'src:crm_postgres.customers' changes or breaks
        impact = ImpactAnalysisEngine.analyze_impact(self.session, "src:crm_postgres.customers")

        self.assertEqual(impact["target_node"]["key"], "src:crm_postgres.customers")
        self.assertGreaterEqual(impact["downstream_count"], 4)

        # Check impacted dashboards and data marts
        self.assertIn("Customer Churn Analytics Dashboard", impact["impacted_dashboards"])
        self.assertIn("Gold Customer 360 Mart", impact["impacted_marts"])

    def test_column_level_lineage_and_impact(self):
        seed_default_lineage(self.session)

        # Impact analysis on email column
        impact = ImpactAnalysisEngine.analyze_impact(self.session, "col:src:customers.email")
        self.assertGreaterEqual(impact["downstream_count"], 2)

        downstream_keys = [d["key"] for d in impact["downstream_impact"]]
        self.assertIn("col:silver:customers.clean_email", downstream_keys)
        self.assertIn("col:gold:customer_360.primary_email", downstream_keys)


if __name__ == "__main__":
    unittest.main()
