import os
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any


class BaseDataGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def export_csv(self, data: List[Dict[str, Any]], filepath: str) -> str:
        if not data:
            return filepath
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        headers = list(data[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        return filepath

    def export_json(self, data: List[Dict[str, Any]], filepath: str) -> str:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return filepath

    def random_date(self, start_years_ago: int = 5, end_days_ahead: int = 0) -> str:
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=start_years_ago * 365)
        end_date = now + timedelta(days=end_days_ahead)
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randint(0, max(0, days_between))
        return (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
