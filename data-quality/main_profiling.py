import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_quality.profiling.profiler import DataProfiler
from data_quality.profiling.profile_repository import ProfileRepository
from backend.app.core.database import SessionLocal, Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataProfilingEngine")


def run_profiling_pipeline(bronze_lake_dir: str = "data/lake/bronze") -> List[Dict[str, Any]]:
    Base.metadata.create_all(bind=engine)
    db_session = SessionLocal()
    profiler = DataProfiler()
    profile_results = []

    if not os.path.exists(bronze_lake_dir):
        logger.warning(f"Bronze lake directory '{bronze_lake_dir}' does not exist.")
        return profile_results

    datasets = ["customers", "products", "orders", "employees", "suppliers", "transactions"]

    try:
        for ds in datasets:
            raw_file = os.path.join(bronze_lake_dir, ds, f"{ds}_raw.json")
            if os.path.exists(raw_file):
                logger.info(f"Profiling dataset '{ds}' from: {raw_file}")
                with open(raw_file, "r", encoding="utf-8") as f:
                    records = json.load(f)

                profile = profiler.profile_records(dataset_name=ds, records=records)
                ProfileRepository.save_profile(db_session, profile)
                profile_results.append(profile)
            else:
                logger.warning(f"Raw landing file missing for dataset '{ds}': {raw_file}")

        logger.info(f"Profiling pipeline completed. {len(profile_results)} datasets profiled.")
        return profile_results
    finally:
        db_session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Data Profiling Engine")
    parser.add_argument("--bronze-dir", default="data/lake/bronze", help="Bronze lake directory")
    args = parser.parse_args()
    run_profiling_pipeline(bronze_lake_dir=args.bronze_dir)
