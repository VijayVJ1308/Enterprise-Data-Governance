import re
from typing import Dict, List, Any

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$|^\+?1-\d{3}-\d{3}-\d{4}$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{4}/\d{2}/\d{2}$")
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
NUMERIC_REGEX = re.compile(r"^-?\d+(\.\d+)?$")


class PatternAnalyzer:
    @staticmethod
    def analyze_patterns(sample_values: List[Any]) -> Dict[str, float]:
        if not sample_values:
            return {"UNKNOWN": 100.0}

        total = len(sample_values)
        counts = {
            "EMAIL": 0,
            "PHONE": 0,
            "DATE": 0,
            "UUID": 0,
            "NUMERIC_STRING": 0,
            "TEXT": 0,
        }

        for val in sample_values:
            if val is None:
                continue
            str_val = str(val).strip()
            if not str_val:
                continue

            if EMAIL_REGEX.match(str_val):
                counts["EMAIL"] += 1
            elif PHONE_REGEX.match(str_val):
                counts["PHONE"] += 1
            elif DATE_REGEX.match(str_val):
                counts["DATE"] += 1
            elif UUID_REGEX.match(str_val):
                counts["UUID"] += 1
            elif NUMERIC_REGEX.match(str_val):
                counts["NUMERIC_STRING"] += 1
            else:
                counts["TEXT"] += 1

        distribution = {}
        for pattern_name, count in counts.items():
            if count > 0:
                distribution[pattern_name] = round((count / total) * 100.0, 2)

        return distribution if distribution else {"TEXT": 100.0}
