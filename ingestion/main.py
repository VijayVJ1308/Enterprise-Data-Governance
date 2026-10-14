import os
import sys
import argparse
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.batch.batch_ingestor import BatchIngestor
from ingestion.api.api_ingestor import ApiIngestor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IngestionPlatform")


def run_ingestion(source_dir: str = "data/raw", target_dir: str = "data/lake/bronze") -> List[Dict[str, Any]]:
    batch_ingestor = BatchIngestor(output_dir=target_dir)
    api_ingestor = ApiIngestor(output_dir=target_dir)
    results = []

    if not os.path.exists(source_dir):
        logger.warning(f"Source directory '{source_dir}' does not exist. Run data generator first.")
        return results

    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]
    for ds in datasets:
        # Check CSV raw file
        csv_file = os.path.join(source_dir, f"{ds}.csv")
        json_file = os.path.join(source_dir, f"{ds}.json")

        if os.path.exists(csv_file):
            logger.info(f"Ingesting dataset '{ds}' from CSV: {csv_file}")
            res = batch_ingestor.ingest_dataset(dataset_name=ds, source_type="csv", source_path_or_url=csv_file)
            results.append(res)
        elif os.path.exists(json_file):
            logger.info(f"Ingesting dataset '{ds}' from JSON: {json_file}")
            res = batch_ingestor.ingest_dataset(dataset_name=ds, source_type="json", source_path_or_url=json_file)
            results.append(res)
        else:
            logger.warning(f"No source raw file found for dataset '{ds}' in '{source_dir}'")

    # Ingest API sample
    logger.info("Ingesting simulated HR REST API endpoint...")
    api_res = api_ingestor.ingest_api_endpoint(dataset_name="hr_employees_api", endpoint_url="http://localhost:8000/api/v1/employees")
    results.append(api_res)

    logger.info(f"Ingestion process completed. {len(results)} datasets landed in '{target_dir}'.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Ingestion Engine")
    parser.add_argument("--source-dir", default="data/raw", help="Raw data directory")
    parser.add_argument("--target-dir", default="data/lake/bronze", help="Bronze lake storage landing directory")
    args = parser.parse_args()
    run_ingestion(source_dir=args.source_dir, target_dir=args.target_dir)
