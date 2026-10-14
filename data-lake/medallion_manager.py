import os
import json
import logging
from typing import List, Dict, Any
from data_lake.parquet_utils import ParquetUtils
from data_lake.minio_client import MinIOClient

logger = logging.getLogger("MedallionManager")


class MedallionManager:
    """
    Medallion Lakehouse Architecture Manager.
    Coordinates Bronze -> Silver -> Gold data lake layer promotions.
    """

    def __init__(self, base_lake_dir: str = "data/lake"):
        self.base_lake_dir = base_lake_dir
        self.bronze_dir = os.path.join(base_lake_dir, "bronze")
        self.silver_dir = os.path.join(base_lake_dir, "silver")
        self.gold_dir = os.path.join(base_lake_dir, "gold")
        self.minio_client = MinIOClient()

        os.makedirs(self.bronze_dir, exist_ok=True)
        os.makedirs(self.silver_dir, exist_ok=True)
        os.makedirs(self.gold_dir, exist_ok=True)

    def promote_bronze_to_silver(self, dataset_name: str) -> Dict[str, Any]:
        """
        Promotes raw dataset from Bronze landing to Silver cleaned layer.
        Cleans formatting, standardizes strings, removes duplicates, and writes Parquet.
        """
        bronze_path = os.path.join(self.bronze_dir, dataset_name, f"{dataset_name}_raw.json")
        if not os.path.exists(bronze_path):
            raise FileNotFoundError(f"Bronze raw dataset not found: {bronze_path}")

        with open(bronze_path, "r", encoding="utf-8") as f:
            raw_records = json.load(f)

        seen_hashes = set()
        cleaned_records = []

        for record in raw_records:
            # 1. Deduplication check using record hash
            rec_hash = record.get("_record_hash")
            if rec_hash and rec_hash in seen_hashes:
                continue
            if rec_hash:
                seen_hashes.add(rec_hash)

            cleaned = dict(record)

            # 2. String standardization & whitespace trimming
            for k, v in cleaned.items():
                if isinstance(v, str) and not k.startswith("_"):
                    v_trimmed = v.strip()
                    # Normalize common country codes
                    if k.lower() == "country":
                        if v_trimmed.upper() in ["USA", "US", "UNITED STATES"]:
                            v_trimmed = "USA"
                        elif v_trimmed.upper() in ["UK", "UNITED KINGDOM"]:
                            v_trimmed = "UK"
                    cleaned[k] = v_trimmed

            cleaned["_silver_promoted_at"] = os.getenv("CURRENT_TIME", "2026-09-21T10:00:00Z")
            cleaned_records.append(cleaned)

        # Write to Silver layer in Parquet format
        silver_dataset_dir = os.path.join(self.silver_dir, dataset_name)
        os.makedirs(silver_dataset_dir, exist_ok=True)
        silver_file = os.path.join(silver_dataset_dir, f"{dataset_name}.parquet")

        ParquetUtils.write_parquet(cleaned_records, silver_file)
        self.minio_client.upload_file("silver-lake", f"{dataset_name}/{dataset_name}.parquet", silver_file)

        logger.info(f"Promoted dataset '{dataset_name}' Bronze -> Silver. Cleaned records: {len(cleaned_records)}.")
        return {
            "dataset_name": dataset_name,
            "bronze_count": len(raw_records),
            "silver_count": len(cleaned_records),
            "duplicates_removed": len(raw_records) - len(cleaned_records),
            "silver_file": silver_file,
            "status": "SUCCESS",
        }

    def build_gold_marts(self) -> Dict[str, Any]:
        """
        Builds Gold aggregated business marts (Star Schema Dimensions & Facts).
        Promotes Silver datasets -> Gold business marts in Parquet format.
        """
        marts_created = []

        # 1. Build dim_customers
        silver_cust_file = os.path.join(self.silver_dir, "customers", "customers.parquet")
        if os.path.exists(silver_cust_file):
            customers = ParquetUtils.read_parquet(silver_cust_file)
            dim_cust = []
            for c in customers:
                dim_cust.append({
                    "customer_sk": c.get("customer_id"),
                    "full_name": f"{c.get('first_name', '')} {c.get('last_name', '')}".strip(),
                    "email": c.get("email"),
                    "country": c.get("country", "UNKNOWN"),
                    "customer_type": c.get("customer_type", "INDIVIDUAL"),
                    "registration_date": c.get("registration_date"),
                    "status": c.get("status", "ACTIVE"),
                })
            gold_cust_file = os.path.join(self.gold_dir, "dim_customers", "dim_customers.parquet")
            ParquetUtils.write_parquet(dim_cust, gold_cust_file)
            self.minio_client.upload_file("gold-lake", "dim_customers/dim_customers.parquet", gold_cust_file)
            marts_created.append({"mart": "dim_customers", "records": len(dim_cust), "file": gold_cust_file})

        # 2. Build fact_orders & sales_mart
        silver_orders_file = os.path.join(self.silver_dir, "orders", "orders.parquet")
        if os.path.exists(silver_orders_file):
            orders = ParquetUtils.read_parquet(silver_orders_file)
            fact_orders = []
            daily_revenue = {}

            for o in orders:
                qty = float(o.get("quantity", 0))
                price = float(o.get("unit_price", 0))
                disc = float(o.get("discount", 0))
                tax = float(o.get("tax", 0))
                total = float(o.get("total_amount", 0))
                order_dt = str(o.get("order_date", "1970-01-01"))

                fact_orders.append({
                    "order_id": o.get("order_id"),
                    "customer_id": o.get("customer_id"),
                    "product_id": o.get("product_id"),
                    "order_date": order_dt,
                    "quantity": qty,
                    "net_amount": round(qty * price - disc, 2),
                    "total_amount": total,
                    "order_status": o.get("order_status"),
                })

                daily_revenue[order_dt] = round(daily_revenue.get(order_dt, 0.0) + total, 2)

            gold_orders_file = os.path.join(self.gold_dir, "fact_orders", "fact_orders.parquet")
            ParquetUtils.write_parquet(fact_orders, gold_orders_file)
            self.minio_client.upload_file("gold-lake", "fact_orders/fact_orders.parquet", gold_orders_file)
            marts_created.append({"mart": "fact_orders", "records": len(fact_orders), "file": gold_orders_file})

            # Build sales_mart aggregated summary
            sales_mart = [{"order_date": dt, "total_revenue": rev, "order_count": len([o for o in fact_orders if o["order_date"] == dt])} for dt, rev in daily_revenue.items()]
            gold_sales_file = os.path.join(self.gold_dir, "sales_mart", "sales_mart.parquet")
            ParquetUtils.write_parquet(sales_mart, gold_sales_file)
            self.minio_client.upload_file("gold-lake", "sales_mart/sales_mart.parquet", gold_sales_file)
            marts_created.append({"mart": "sales_mart", "records": len(sales_mart), "file": gold_sales_file})

        logger.info(f"Built Gold Business Marts. Total marts created: {len(marts_created)}.")
        return {"marts": marts_created, "status": "SUCCESS"}
