"""
Phase 20: PySpark Medallion Transformations & DuckDB Big Data Profiling Tests.

Tests:
1. Configuration & Lakehouse Paths
2. Engine Session Provider & SQL Execution
3. Bronze-to-Silver Cleansing, Deduplication, & Lineage Enrichment
4. Silver-to-Gold Customer 360 Dimensional Mart
5. Silver-to-Gold Financial MRR Mart
6. DuckDB Vectorized Columnar Profiler (Quantiles, Nulls, Frequencies)
7. End-to-End Medallion Lakehouse Pipeline
"""

import os
import json
import shutil
import tempfile
import unittest
import pandas as pd

from spark.config import SparkMedallionConfig
from spark.session import SparkSessionProvider
from spark.jobs.bronze_to_silver import BronzeToSilverCleanser
from spark.jobs.silver_to_gold import SilverToGoldAggregator
from spark.duckdb_profiler import DuckDBProfiler


class TestPhase20SparkMedallion(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bronze_dir = os.path.join(self.temp_dir, "bronze")
        self.silver_dir = os.path.join(self.temp_dir, "silver")
        self.gold_dir = os.path.join(self.temp_dir, "gold")
        for d in [self.bronze_dir, self.silver_dir, self.gold_dir]:
            os.makedirs(d, exist_ok=True)

        self.config = SparkMedallionConfig(
            bronze_path=self.bronze_dir,
            silver_path=self.silver_dir,
            gold_path=self.gold_dir,
        )
        self.session = SparkSessionProvider(self.config)
        self.cleanser = BronzeToSilverCleanser(self.config, self.session)
        self.aggregator = SilverToGoldAggregator(self.config, self.session)
        self.profiler = DuckDBProfiler()

    def tearDown(self):
        self.session.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_spark_medallion_config(self):
        self.assertEqual(self.config.bronze_path, self.bronze_dir)
        self.assertEqual(self.config.silver_path, self.silver_dir)
        self.assertEqual(self.config.gold_path, self.gold_dir)
        crm_path = self.config.get_tier_path("silver", "crm_customers")
        self.assertTrue(crm_path.endswith(os.path.join("silver", "crm_customers")))

    def test_session_provider_and_sql_execution(self):
        self.assertIn(self.session.engine_type, ["pyspark", "duckdb"])
        df_sample = pd.DataFrame([{"id": 1, "val": 10.5}, {"id": 2, "val": 20.0}])
        res = self.session.execute_sql("SELECT SUM(val) as total FROM df_sample", {"df_sample": df_sample})
        self.assertEqual(res.iloc[0]["total"], 30.5)

    def test_bronze_to_silver_cleansing_and_deduplication(self):
        # Create raw Bronze JSON records with duplicates, whitespace, and null primary key
        raw_records = [
            {"customer_id": "CUST-001", "first_name": "  Alice  ", "email": "ALICE@CORP.COM  ", "domain": "CRM"},
            {"customer_id": "CUST-001", "first_name": "Alice", "email": "alice@corp.com", "domain": "CRM"},  # Duplicate
            {"customer_id": "CUST-002", "first_name": "Bob  ", "email": "bob@corp.com", "domain": "CRM"},
            {"customer_id": None, "first_name": "Ghost", "email": "ghost@corp.com", "domain": "CRM"},  # Null PK
        ]
        bronze_file = os.path.join(self.bronze_dir, "customers_raw.json")
        with open(bronze_file, "w", encoding="utf-8") as f:
            json.dump(raw_records, f)

        result = self.cleanser.cleanse_dataset(
            dataset_name="crm_customers",
            input_path=bronze_file,
            primary_key="customer_id",
            output_dir=os.path.join(self.silver_dir, "crm_customers"),
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["input_records"], 4)
        self.assertEqual(result["dropped_count"], 1)  # Dropped null PK
        self.assertEqual(result["deduplicated_count"], 1)  # Dropped duplicate CUST-001
        self.assertEqual(result["silver_records"], 2)  # CUST-001 and CUST-002 remain
        self.assertTrue(os.path.exists(result["output_file"]))

        # Verify cleansed Parquet contents
        silver_df = self.session.read_parquet(result["output_file"])
        self.assertEqual(len(silver_df), 2)
        alice_row = silver_df[silver_df["customer_id"] == "CUST-001"].iloc[0]
        self.assertEqual(alice_row["first_name"], "Alice")  # Whitespace trimmed
        self.assertEqual(alice_row["email"], "alice@corp.com")  # Lowercased
        self.assertTrue(alice_row["_is_cleansed"])
        self.assertIn("_silver_processed_at", silver_df.columns)

    def test_silver_to_gold_customer_360_mart(self):
        # Prepare Silver Customers
        cust_df = pd.DataFrame([
            {"customer_id": "C-101", "first_name": "Marcus", "email": "marcus@corp.com", "domain": "CRM"},
            {"customer_id": "C-102", "first_name": "Elena", "email": "elena@corp.com", "domain": "CRM"},
        ])
        cust_file = os.path.join(self.silver_dir, "customers.parquet")
        self.session.write_parquet(cust_df, cust_file)

        # Prepare Silver Orders
        orders_df = pd.DataFrame([
            {"order_id": "O-1", "customer_id": "C-101", "total_amount": 2500.0, "timestamp": "2026-10-10T12:00:00Z"},
            {"order_id": "O-2", "customer_id": "C-101", "total_amount": 3000.0, "timestamp": "2026-10-12T15:00:00Z"},
            {"order_id": "O-3", "customer_id": "C-102", "total_amount": 450.0, "timestamp": "2026-10-14T09:00:00Z"},
        ])
        orders_file = os.path.join(self.silver_dir, "orders.parquet")
        self.session.write_parquet(orders_df, orders_file)

        mart_summary = self.aggregator.build_customer_360_mart(
            customers_silver_path=cust_file,
            orders_silver_path=orders_file,
            output_dir=os.path.join(self.gold_dir, "customer_360"),
        )

        self.assertEqual(mart_summary["status"], "SUCCESS")
        self.assertEqual(mart_summary["record_count"], 2)
        self.assertTrue(os.path.exists(mart_summary["output_file"]))

        gold_df = self.session.read_parquet(mart_summary["output_file"])
        marcus = gold_df[gold_df["customer_id"] == "C-101"].iloc[0]
        self.assertEqual(marcus["total_orders"], 2)
        self.assertEqual(marcus["lifetime_spend"], 5500.0)
        self.assertEqual(marcus["customer_value_tier"], "PLATINUM")

        elena = gold_df[gold_df["customer_id"] == "C-102"].iloc[0]
        self.assertEqual(elena["total_orders"], 1)
        self.assertEqual(elena["customer_value_tier"], "BRONZE")

    def test_silver_to_gold_financial_mrr_mart(self):
        txn_df = pd.DataFrame([
            {"txn_id": "T-1", "amount_usd": 15000.0, "currency": "USD", "timestamp": "2026-09-15 10:00:00"},
            {"txn_id": "T-2", "amount_usd": -1200.0, "currency": "USD", "timestamp": "2026-09-20 14:00:00"},
            {"txn_id": "T-3", "amount_usd": 22000.0, "currency": "USD", "timestamp": "2026-10-01 09:30:00"},
        ])
        txn_file = os.path.join(self.silver_dir, "transactions.parquet")
        self.session.write_parquet(txn_df, txn_file)

        mrr_summary = self.aggregator.build_financial_mrr_mart(
            transactions_silver_path=txn_file,
            output_dir=os.path.join(self.gold_dir, "financial_mrr"),
        )

        self.assertEqual(mrr_summary["status"], "SUCCESS")
        self.assertEqual(mrr_summary["record_count"], 2)  # Two months: 2026-09 and 2026-10

        gold_mrr = self.session.read_parquet(mrr_summary["output_file"])
        sept = gold_mrr[gold_mrr["settlement_month"] == "2026-09"].iloc[0]
        self.assertEqual(sept["gross_revenue_usd"], 15000.0)
        self.assertEqual(sept["refunds_usd"], 1200.0)
        self.assertEqual(sept["net_revenue_usd"], 13800.0)

    def test_duckdb_columnar_profiling_on_parquet(self):
        # Create a Parquet table with diverse distributions
        df = pd.DataFrame({
            "product_id": [f"P-{i}" for i in range(100)],
            "category": ["Electronics"] * 50 + ["Home"] * 30 + ["Fashion"] * 20,
            "price_usd": [10.0 + i * 2.5 for i in range(100)],
            "discount_pct": [None if i % 10 == 0 else 0.15 for i in range(100)],  # 10 nulls
        })
        sample_parquet = os.path.join(self.temp_dir, "products.parquet")
        self.session.write_parquet(df, sample_parquet)

        profile = self.profiler.profile_parquet(sample_parquet, dataset_name="products")

        self.assertEqual(profile["dataset_name"], "products")
        self.assertEqual(profile["row_count"], 100)
        self.assertEqual(profile["column_count"], 4)
        self.assertGreater(profile["profiling_time_ms"], 0)

        cols = {c["column_name"]: c for c in profile["columns"]}

        # Check category column top values
        cat_col = cols["category"]
        self.assertEqual(cat_col["null_count"], 0)
        self.assertEqual(cat_col["distinct_count"], 3)
        self.assertEqual(cat_col["top_values"][0]["value"], "Electronics")
        self.assertEqual(cat_col["top_values"][0]["count"], 50)

        # Check discount null rates
        disc_col = cols["discount_pct"]
        self.assertEqual(disc_col["null_count"], 10)
        self.assertEqual(disc_col["null_percentage"], 10.0)

        # Check price percentiles
        price_col = cols["price_usd"]
        self.assertEqual(price_col["min_value"], 10.0)
        self.assertIn("quantiles", price_col)
        self.assertIsNotNone(price_col["quantiles"]["p50_median"])
        self.assertIsNotNone(price_col["quantiles"]["p95"])

    def test_end_to_end_medallion_lakehouse_pipeline(self):
        # Raw Bronze -> Silver Cleanser -> Gold Customer 360 -> DuckDB Profile
        raw_cust = [{"customer_id": f"U-{i}", "first_name": f"User {i} ", "email": f"USER{i}@CORP.COM"} for i in range(20)]
        raw_file = os.path.join(self.bronze_dir, "e2e_cust.json")
        with open(raw_file, "w") as f:
            json.dump(raw_cust, f)

        # 1. Cleanse to Silver
        silver_res = self.cleanser.cleanse_dataset("e2e_customers", raw_file, "customer_id", self.silver_dir)
        self.assertEqual(silver_res["silver_records"], 20)

        # 2. Orders Silver
        orders = [{"order_id": f"ORD-{i}", "customer_id": f"U-{i % 5}", "total_amount": 100.0 * (i + 1), "timestamp": "2026-10-14"} for i in range(30)]
        orders_file = os.path.join(self.silver_dir, "e2e_orders.parquet")
        self.session.write_parquet(pd.DataFrame(orders), orders_file)

        # 3. Aggregate to Gold
        gold_res = self.aggregator.build_customer_360_mart(silver_res["output_file"], orders_file, self.gold_dir)
        self.assertEqual(gold_res["status"], "SUCCESS")

        # 4. Profile Gold Mart
        profile = self.profiler.profile_parquet(gold_res["output_file"], "customer_360_e2e")
        self.assertEqual(profile["row_count"], 20)
        spend_col = [c for c in profile["columns"] if c["column_name"] == "lifetime_spend"][0]
        self.assertGreater(spend_col["max_value"], 0)


if __name__ == "__main__":
    unittest.main()
