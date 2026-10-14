"""
Phase 20: Silver to Gold Medallion Business Mart Aggregation Job.
Transforms normalized Silver tables into analytical dimensional star-schema marts:
1. Customer 360 Mart (Lifetime value, order history, tiering)
2. Financial MRR Mart (Monthly revenue, settlement summaries)
3. Quality Health Executive Mart (Dimension score telemetry)
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd

from spark.config import SparkMedallionConfig
from spark.session import SparkSessionProvider


class SilverToGoldAggregator:
    """Aggregates Silver lakehouse tables into certified Gold business marts."""

    def __init__(
        self,
        config: Optional[SparkMedallionConfig] = None,
        session_provider: Optional[SparkSessionProvider] = None,
    ):
        self.config = config or SparkMedallionConfig()
        self.session = session_provider or SparkSessionProvider(self.config)

    def build_customer_360_mart(
        self,
        customers_silver_path: str,
        orders_silver_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Merge customer master with order transactions to create a Customer 360 Mart.
        Computes lifetime spend, order frequency, average order value, and value tier.
        """
        cust_df = self.session.read_parquet(customers_silver_path)
        orders_df = self.session.read_parquet(orders_silver_path)

        has_domain = "domain" in cust_df.columns
        domain_select = "c.domain," if has_domain else "'UNKNOWN' AS domain,"
        domain_group = ", c.domain" if has_domain else ""

        query = f"""
            SELECT 
                c.customer_id,
                c.first_name,
                c.email,
                {domain_select}
                COUNT(o.order_id) AS total_orders,
                COALESCE(SUM(o.total_amount), 0.0) AS lifetime_spend,
                COALESCE(AVG(o.total_amount), 0.0) AS avg_order_value,
                MAX(o.timestamp) AS last_order_timestamp,
                CASE 
                    WHEN COALESCE(SUM(o.total_amount), 0.0) >= 5000 THEN 'PLATINUM'
                    WHEN COALESCE(SUM(o.total_amount), 0.0) >= 1500 THEN 'GOLD'
                    WHEN COALESCE(SUM(o.total_amount), 0.0) >= 500 THEN 'SILVER'
                    ELSE 'BRONZE'
                END AS customer_value_tier,
                CURRENT_TIMESTAMP AS _gold_created_at
            FROM cust_df c
            LEFT JOIN orders_df o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id, c.first_name, c.email{domain_group}
        """
        gold_df = self.session.execute_sql(query, {"cust_df": cust_df, "orders_df": orders_df})

        target_dir = output_dir or self.config.get_tier_path("gold", "customer_360")
        os.makedirs(target_dir, exist_ok=True)
        output_file = os.path.join(target_dir, "customer_360_gold.parquet")

        self.session.write_parquet(gold_df, output_file, compression=self.config.parquet_compression)

        return {
            "mart_name": "customer_360",
            "record_count": len(gold_df),
            "output_file": output_file,
            "status": "SUCCESS",
        }

    def build_financial_mrr_mart(
        self,
        transactions_silver_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate ledger transactions by month and currency to produce Monthly Recurring Revenue (MRR).
        """
        txn_df = self.session.read_parquet(transactions_silver_path)

        query = """
            SELECT 
                SUBSTRING(CAST(timestamp AS VARCHAR), 1, 7) AS settlement_month,
                currency,
                COUNT(txn_id) AS total_transactions,
                SUM(CASE WHEN amount_usd > 0 THEN amount_usd ELSE 0 END) AS gross_revenue_usd,
                SUM(CASE WHEN amount_usd < 0 THEN ABS(amount_usd) ELSE 0 END) AS refunds_usd,
                SUM(amount_usd) AS net_revenue_usd,
                AVG(amount_usd) AS avg_transaction_usd,
                CURRENT_TIMESTAMP AS _gold_created_at
            FROM txn_df
            GROUP BY SUBSTRING(CAST(timestamp AS VARCHAR), 1, 7), currency
            ORDER BY settlement_month DESC
        """
        mrr_df = self.session.execute_sql(query, {"txn_df": txn_df})

        target_dir = output_dir or self.config.get_tier_path("gold", "financial_mrr")
        os.makedirs(target_dir, exist_ok=True)
        output_file = os.path.join(target_dir, "financial_mrr_gold.parquet")

        self.session.write_parquet(mrr_df, output_file, compression=self.config.parquet_compression)

        return {
            "mart_name": "financial_mrr",
            "record_count": len(mrr_df),
            "output_file": output_file,
            "status": "SUCCESS",
        }
