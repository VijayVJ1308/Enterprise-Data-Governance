import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("MLRuleRecommender")


class MLRuleRecommender:
    """
    ML & Heuristics-driven Quality Rule Recommendation Engine.
    Analyzes dataset profile statistics and sample values to suggest declarative quality rules.
    """

    @staticmethod
    def recommend_rules_for_dataset(
        dataset_name: str,
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not records:
            return []

        total_rows = len(records)
        columns = list(records[0].keys())
        recommended_rules = []
        rule_counter = 1

        for col in columns:
            vals = [row.get(col) for row in records]
            non_nulls = [v for v in vals if v is not None and str(v).strip() != ""]
            null_count = total_rows - len(non_nulls)
            null_rate = null_count / total_rows if total_rows > 0 else 0.0

            unique_vals = set(non_nulls)
            unique_count = len(unique_vals)
            uniqueness_rate = unique_count / total_rows if total_rows > 0 else 0.0

            # 1. Recommend NOT_NULL rule
            if null_rate == 0.0:
                recommended_rules.append({
                    "rule_id": f"REC-{dataset_name.upper()}-{rule_counter:03d}",
                    "dataset_name": dataset_name,
                    "column_name": col,
                    "rule_type": "NOT_NULL",
                    "rule_expression": None,
                    "severity": "HIGH",
                    "confidence": 0.98,
                    "rationale": f"Column '{col}' has 0% nulls across {total_rows} records."
                })
                rule_counter += 1

            # 2. Recommend UNIQUE rule
            if uniqueness_rate == 1.0 and total_rows > 5:
                recommended_rules.append({
                    "rule_id": f"REC-{dataset_name.upper()}-{rule_counter:03d}",
                    "dataset_name": dataset_name,
                    "column_name": col,
                    "rule_type": "UNIQUE",
                    "rule_expression": None,
                    "severity": "HIGH",
                    "confidence": 0.95,
                    "rationale": f"Column '{col}' is 100% unique across all {total_rows} records."
                })
                rule_counter += 1

            # 3. Recommend RANGE rule for numeric columns
            numeric_vals = [v for v in non_nulls if isinstance(v, (int, float))]
            if len(numeric_vals) == len(non_nulls) and len(numeric_vals) > 0:
                min_v = min(numeric_vals)
                max_v = max(numeric_vals)

                # If min_v is positive, range starts at 0 or min_v * 0.9
                buffer_min = 0 if min_v >= 0 else round(min_v * 1.1, 2)
                buffer_max = round(max_v * 1.1, 2) if max_v >= 0 else round(max_v * 0.9, 2)

                recommended_rules.append({
                    "rule_id": f"REC-{dataset_name.upper()}-{rule_counter:03d}",
                    "dataset_name": dataset_name,
                    "column_name": col,
                    "rule_type": "RANGE",
                    "rule_expression": f"BETWEEN {buffer_min} AND {buffer_max}",
                    "severity": "MEDIUM",
                    "confidence": 0.90,
                    "rationale": f"Column '{col}' numeric range observed: [{min_v}, {max_v}]."
                })
                rule_counter += 1

            # 4. Recommend ACCEPTED_VALUES for low cardinality categorical columns
            if 2 <= unique_count <= 10 and total_rows >= 20 and len(numeric_vals) != len(non_nulls):
                accepted_str = ", ".join(f"'{v}'" for v in sorted(unique_vals))
                recommended_rules.append({
                    "rule_id": f"REC-{dataset_name.upper()}-{rule_counter:03d}",
                    "dataset_name": dataset_name,
                    "column_name": col,
                    "rule_type": "ACCEPTED_VALUES",
                    "rule_expression": f"IN ({accepted_str})",
                    "severity": "MEDIUM",
                    "confidence": 0.92,
                    "rationale": f"Column '{col}' has low cardinality ({unique_count} unique values)."
                })
                rule_counter += 1

            # 5. Recommend VALID_FORMAT for Email / Phone
            col_lower = col.lower()
            if "email" in col_lower:
                recommended_rules.append({
                    "rule_id": f"REC-{dataset_name.upper()}-{rule_counter:03d}",
                    "dataset_name": dataset_name,
                    "column_name": col,
                    "rule_type": "VALID_FORMAT",
                    "rule_expression": "EMAIL",
                    "severity": "HIGH",
                    "confidence": 0.99,
                    "rationale": f"Column '{col}' detected as email address format."
                })
                rule_counter += 1

        logger.info(f"Generated {len(recommended_rules)} ML quality rule recommendations for dataset '{dataset_name}'.")
        return recommended_rules
