"""
Phase 22: Enterprise Demo Data Seeder CLI Script.
Seeds metadata catalog, business glossary, lineage DAG, data contracts,
quality rules, issues lifecycle, and creates sample Bronze/Silver/Gold Parquet tables.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
import pandas as pd

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.catalog import Dataset, DatasetColumn, DataOwner
from backend.app.models.quality import QualityRule, QualityIssue
from backend.app.models.lineage import LineageNode, LineageEdge, GlossaryTerm
from backend.app.models.schema_contract import DataContract, SchemaDriftEvent


def seed_demo_data() -> dict:
    """Populate full database schema and lakehouse demo files."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    counts = {}

    try:
        # 1. Seed Datasets & Columns
        if db.query(Dataset).count() == 0:
            ds_crm = Dataset(
                dataset_name="crm_customers",
                domain="CRM",
                source_system="PostgreSQL",
                location="minio://bronze/crm_customers",
                format="parquet",
                classification="CONFIDENTIAL",
                description="Core customer master register with contact details.",
                row_count=142500,
                quality_score=94.2,
                certification_status="CERTIFIED",
            )
            ds_erp = Dataset(
                dataset_name="erp_transactions",
                domain="ERP",
                source_system="SAP",
                location="minio://bronze/erp_transactions",
                format="parquet",
                classification="RESTRICTED",
                description="General ledger journal settlement transactions.",
                row_count=2450000,
                quality_score=97.8,
                certification_status="CERTIFIED",
            )
            ds_hr = Dataset(
                dataset_name="hr_employee_master",
                domain="HR",
                source_system="Workday",
                location="minio://bronze/hr_employee_master",
                format="parquet",
                classification="CONFIDENTIAL",
                description="Employee compensation tiers and demographics.",
                row_count=8500,
                quality_score=88.5,
                certification_status="PENDING",
            )
            ds_ecom = Dataset(
                dataset_name="ecommerce_orders",
                domain="ECOMMERCE",
                source_system="Shopify",
                location="minio://bronze/ecommerce_orders",
                format="parquet",
                classification="INTERNAL",
                description="Digital checkout cart lines and fulfillment records.",
                row_count=890000,
                quality_score=92.1,
                certification_status="CERTIFIED",
            )

            db.add_all([ds_crm, ds_erp, ds_hr, ds_ecom])
            db.commit()

            # Add Column details
            cols = [
                DatasetColumn(dataset_id=ds_crm.id, column_name="customer_id", data_type="VARCHAR(64)", is_nullable=False, is_primary_key=True),
                DatasetColumn(dataset_id=ds_crm.id, column_name="email", data_type="VARCHAR(255)", is_nullable=False, classification="CONFIDENTIAL"),
                DatasetColumn(dataset_id=ds_crm.id, column_name="phone", data_type="VARCHAR(32)", is_nullable=True, classification="CONFIDENTIAL"),
                DatasetColumn(dataset_id=ds_erp.id, column_name="txn_id", data_type="UUID", is_nullable=False, is_primary_key=True),
                DatasetColumn(dataset_id=ds_erp.id, column_name="amount_usd", data_type="DECIMAL(14,2)", is_nullable=False),
                DatasetColumn(dataset_id=ds_hr.id, column_name="ssn", data_type="VARCHAR(11)", is_nullable=False, classification="RESTRICTED"),
            ]
            db.add_all(cols)
            db.commit()

        counts["datasets"] = db.query(Dataset).count()
        counts["columns"] = db.query(DatasetColumn).count()

        # 2. Seed Business Glossary
        if db.query(GlossaryTerm).count() == 0:
            terms = [
                GlossaryTerm(term="Customer ID", business_domain="CRM", definition="Unique persistent identifier for business account", owner="Alice Zhang", status="APPROVED"),
                GlossaryTerm(term="Gross Margin", business_domain="FINANCE", definition="Revenue minus direct cost of goods sold", owner="Marcus Vance", status="APPROVED"),
                GlossaryTerm(term="PII", business_domain="GOVERNANCE", definition="Personally Identifiable Information subject to GDPR/HIPAA", owner="Elena Rostova", status="APPROVED"),
            ]
            db.add_all(terms)
            db.commit()

        counts["glossary_terms"] = db.query(GlossaryTerm).count()

        # 3. Seed Lineage Graph
        if db.query(LineageNode).count() == 0:
            n1 = LineageNode(node_key="src_crm_postgres", name="Postgres CRM RDS", node_type="SOURCE", domain="CRM")
            n2 = LineageNode(node_key="bronze_crm", name="bronze.crm_customers", node_type="DATASET", domain="CRM")
            n3 = LineageNode(node_key="silver_crm", name="silver.dim_customer", node_type="DATASET", domain="CRM")
            n4 = LineageNode(node_key="gold_mrr", name="gold.mrr_executive_mart", node_type="DATASET", domain="FINANCE")
            n5 = LineageNode(node_key="bi_tableau", name="Tableau Executive MRR", node_type="DASHBOARD", domain="FINANCE")

            db.add_all([n1, n2, n3, n4, n5])
            db.commit()

            e1 = LineageEdge(source_node_id=n1.id, target_node_id=n2.id, transformation_type="DIRECT_TRANSFORM", pipeline_name="Kafka Ingest")
            e2 = LineageEdge(source_node_id=n2.id, target_node_id=n3.id, transformation_type="DIRECT_TRANSFORM", pipeline_name="PySpark Cleanse")
            e3 = LineageEdge(source_node_id=n3.id, target_node_id=n4.id, transformation_type="AGGREGATION", pipeline_name="dbt Dimensional Model")
            e4 = LineageEdge(source_node_id=n4.id, target_node_id=n5.id, transformation_type="DIRECT_TRANSFORM", pipeline_name="Direct Query Connector")

            db.add_all([e1, e2, e3, e4])
            db.commit()

        counts["lineage_nodes"] = db.query(LineageNode).count()
        counts["lineage_edges"] = db.query(LineageEdge).count()

        # 4. Seed Data Contracts
        crm_ds = db.query(Dataset).filter(Dataset.dataset_name == "crm_customers").first()
        erp_ds = db.query(Dataset).filter(Dataset.dataset_name == "erp_transactions").first()

        if db.query(DataContract).count() == 0 and crm_ds and erp_ds:
            c1 = DataContract(
                contract_name="cnt_crm_customers",
                dataset_id=crm_ds.id,
                version="1.4.0",
                yaml_spec="dataset: crm_customers\nversion: 1.4.0\ncolumns:\n  customer_id: VARCHAR(64)\n  email: VARCHAR(255)\n",
                status="ACTIVE",
            )
            c2 = DataContract(
                contract_name="cnt_erp_transactions",
                dataset_id=erp_ds.id,
                version="2.1.0",
                yaml_spec="dataset: erp_transactions\nversion: 2.1.0\ncolumns:\n  txn_id: UUID\n  amount_usd: DECIMAL(14,2)\n",
                status="ACTIVE",
            )
            db.add_all([c1, c2])
            db.commit()

        counts["contracts"] = db.query(DataContract).count()

        # 5. Seed Quality Rules & Issues
        if db.query(QualityRule).count() == 0 and crm_ds and erp_ds:
            r1 = QualityRule(rule_id="RULE-COMP-EMAIL", rule_name="Email Completeness", dataset_id=crm_ds.id, column_name="email", rule_type="NOT_NULL", severity="HIGH")
            r2 = QualityRule(rule_id="RULE-VAL-AMOUNT", rule_name="Non-Negative Balance", dataset_id=erp_ds.id, column_name="amount_usd", rule_type="RANGE", severity="CRITICAL")
            r3 = QualityRule(rule_id="RULE-UNIQ-CUST", rule_name="Customer ID Uniqueness", dataset_id=crm_ds.id, column_name="customer_id", rule_type="UNIQUE", severity="CRITICAL")
            db.add_all([r1, r2, r3])
            db.commit()

        if db.query(QualityIssue).count() == 0 and crm_ds and erp_ds:
            i1 = QualityIssue(
                issue_id="ISSUE-DEMO-1",
                dataset_id=crm_ds.id,
                column_name="email",
                severity="HIGH",
                status="OPEN",
                description="14 records found with null email",
            )
            i2 = QualityIssue(
                issue_id="ISSUE-DEMO-2",
                dataset_id=erp_ds.id,
                column_name="amount_usd",
                severity="CRITICAL",
                status="RESOLVED",
                description="3 negative transactions corrected",
            )
            db.add_all([i1, i2])
            db.commit()

        counts["quality_rules"] = db.query(QualityRule).count()
        counts["quality_issues"] = db.query(QualityIssue).count()

        # 6. Seed Sample Parquet Files in Lakehouse
        base_dir = os.path.dirname(os.path.dirname(__file__))
        silver_lake = os.path.join(base_dir, "data", "lake", "silver")
        os.makedirs(silver_lake, exist_ok=True)
        demo_parquet = os.path.join(silver_lake, "demo_customers.parquet")
        if not os.path.exists(demo_parquet):
            df_demo = pd.DataFrame([
                {"customer_id": f"DEMO-{i}", "first_name": f"User {i}", "email": f"user{i}@corp.com", "spend": 100.0 * i}
                for i in range(50)
            ])
            df_demo.to_parquet(demo_parquet, engine="pyarrow", compression="snappy")
        counts["lakehouse_parquet_created"] = demo_parquet

    finally:
        db.close()

    return counts


if __name__ == "__main__":
    print("🌱 Seeding Enterprise Data Governance Demo Data...")
    res = seed_demo_data()
    print("✅ Seeding Complete! Summary:")
    for k, v in res.items():
        print(f"  - {k}: {v}")
