import math
from collections import Counter
from typing import List, Dict, Any, Union
from data_quality.profiling.pattern_analyzer import PatternAnalyzer


class DataProfiler:
    """
    Automated Data Profiling Engine.
    Calculates 17+ dataset and column metrics for data quality and metadata cataloging.
    """

    @staticmethod
    def _calculate_percentile(sorted_nums: List[float], p: float) -> float:
        if not sorted_nums:
            return 0.0
        k = (len(sorted_nums) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_nums[int(k)]
        d0 = sorted_nums[int(f)] * (c - k)
        d1 = sorted_nums[int(c)] * (k - f)
        return round(d0 + d1, 4)

    @staticmethod
    def _infer_type(values: List[Any]) -> str:
        non_nulls = [v for v in values if v is not None and str(v).strip() != ""]
        if not non_nulls:
            return "UNKNOWN"

        sample = non_nulls[:100]
        int_matches = 0
        float_matches = 0
        bool_matches = 0

        for s in sample:
            if isinstance(s, bool) or str(s).lower() in ["true", "false"]:
                bool_matches += 1
            elif isinstance(s, int):
                int_matches += 1
            elif isinstance(s, float):
                float_matches += 1
            else:
                str_val = str(s).strip()
                try:
                    int(str_val)
                    int_matches += 1
                except ValueError:
                    try:
                        float(str_val)
                        float_matches += 1
                    except ValueError:
                        pass

        total = len(sample)
        if bool_matches == total:
            return "BOOLEAN"
        elif int_matches == total:
            return "INTEGER"
        elif (int_matches + float_matches) == total:
            return "FLOAT"
        else:
            return "STRING"

    def profile_records(self, dataset_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {
                "dataset_name": dataset_name,
                "row_count": 0,
                "column_count": 0,
                "null_counts": {},
                "null_percentages": {},
                "unique_counts": {},
                "uniqueness_percentages": {},
                "column_statistics": {},
            }

        row_count = len(records)
        columns = list(records[0].keys())
        column_count = len(columns)

        null_counts = {}
        null_percentages = {}
        unique_counts = {}
        uniqueness_percentages = {}
        column_statistics = {}

        for col in columns:
            col_values = [r.get(col) for r in records]
            non_null_values = [v for v in col_values if v is not None and str(v).strip() != ""]
            null_cnt = row_count - len(non_null_values)
            null_pct = round((null_cnt / row_count) * 100.0, 2)

            distinct_vals = set(str(v) for v in non_null_values)
            unique_cnt = len(distinct_vals)
            unique_pct = round((unique_cnt / max(1, len(non_null_values))) * 100.0, 2)

            null_counts[col] = null_cnt
            null_percentages[col] = null_pct
            unique_counts[col] = unique_cnt
            uniqueness_percentages[col] = unique_pct

            inferred_type = self._infer_type(col_values)

            # Numerical metrics if numeric
            numeric_stats = None
            if inferred_type in ["INTEGER", "FLOAT"]:
                nums = []
                for v in non_null_values:
                    try:
                        nums.append(float(v))
                    except (ValueError, TypeError):
                        pass

                if nums:
                    nums_sorted = sorted(nums)
                    n = len(nums_sorted)
                    val_min = round(nums_sorted[0], 4)
                    val_max = round(nums_sorted[-1], 4)
                    val_mean = round(sum(nums_sorted) / n, 4)

                    # Median
                    if n % 2 == 1:
                        val_median = round(nums_sorted[n // 2], 4)
                    else:
                        val_median = round((nums_sorted[n // 2 - 1] + nums_sorted[n // 2]) / 2.0, 4)

                    # Standard deviation
                    variance = sum((x - val_mean) ** 2 for x in nums_sorted) / max(1, n)
                    val_stddev = round(math.sqrt(variance), 4)

                    # Percentiles
                    percentiles = {
                        "p25": self._calculate_percentile(nums_sorted, 25),
                        "p50": val_median,
                        "p75": self._calculate_percentile(nums_sorted, 75),
                        "p90": self._calculate_percentile(nums_sorted, 90),
                        "p95": self._calculate_percentile(nums_sorted, 95),
                        "p99": self._calculate_percentile(nums_sorted, 99),
                    }

                    numeric_stats = {
                        "min": val_min,
                        "max": val_max,
                        "mean": val_mean,
                        "median": val_median,
                        "stddev": val_stddev,
                        "percentiles": percentiles,
                    }

            # Cardinality rating
            if unique_cnt == len(non_null_values) and len(non_null_values) > 0:
                cardinality = "UNIQUE"
            elif unique_pct > 60.0:
                cardinality = "HIGH"
            elif unique_pct > 10.0:
                cardinality = "MEDIUM"
            elif unique_cnt == 1:
                cardinality = "SINGLE_VALUE"
            else:
                cardinality = "LOW"

            # Value distribution (Top 5)
            val_counts = Counter(str(v) for v in non_null_values)
            top_5 = val_counts.most_common(5)
            value_dist = {k: v for k, v in top_5}

            # Pattern distribution for string types
            pattern_dist = PatternAnalyzer.analyze_patterns(non_null_values) if inferred_type == "STRING" else {}

            column_statistics[col] = {
                "data_type": inferred_type,
                "cardinality": cardinality,
                "numeric_statistics": numeric_stats,
                "pattern_distribution": pattern_dist,
                "value_distribution": value_dist,
            }

        return {
            "dataset_name": dataset_name,
            "row_count": row_count,
            "column_count": column_count,
            "null_counts": null_counts,
            "null_percentages": null_percentages,
            "unique_counts": unique_counts,
            "uniqueness_percentages": uniqueness_percentages,
            "column_statistics": column_statistics,
        }
