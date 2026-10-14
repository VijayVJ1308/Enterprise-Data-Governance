import os
import sys
import argparse
import logging
from typing import Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_lake.medallion_manager import MedallionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MedallionPipeline")


def run_medallion_pipeline(base_lake_dir: str = "data/lake") -> Dict[str, Any]:
    manager = MedallionManager(base_lake_dir=base_lake_dir)
    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]

    silver_promotions = []
    logger.info("Starting Bronze -> Silver Medallion layer promotions...")
    for ds in datasets:
        try:
            res = manager.promote_bronze_to_silver(ds)
            silver_promotions.append(res)
        except Exception as e:
            logger.warning(f"Could not promote dataset '{ds}' to Silver: {e}")

    logger.info("Starting Silver -> Gold Business Mart constructions...")
    gold_res = manager.build_gold_marts()

    logger.info("Medallion pipeline execution completed successfully.")
    return {
        "silver_promotions": silver_promotions,
        "gold_marts": gold_res,
        "status": "SUCCESS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Medallion Data Lake Pipeline")
    parser.add_argument("--lake-dir", default="data/lake", help="Data lake base directory")
    args = parser.parse_args()
    run_medallion_pipeline(base_lake_dir=args.lake_dir)
