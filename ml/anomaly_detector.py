import math
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("AnomalyDetector")


class AnomalyDetector:
    """
    Statistical Anomaly Detection Engine using Z-Score, IQR, and Freshness SLA heuristics.
    """

    @staticmethod
    def _calculate_mean_stddev(values: List[float]) -> tuple[float, float]:
        if not values:
            return 0.0, 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = math.sqrt(variance)
        return mean, stddev

    @staticmethod
    def _calculate_percentile(sorted_vals: List[float], percentile: float) -> float:
        if not sorted_vals:
            return 0.0
        n = len(sorted_vals)
        pos = (n - 1) * percentile
        lower = int(pos)
        upper = lower + 1
        weight = pos - lower
        if upper >= n:
            return float(sorted_vals[-1])
        return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight

    @staticmethod
    def detect_zscore_anomaly(
        historical_values: List[float],
        current_value: float,
        threshold: float = 3.0
    ) -> Dict[str, Any]:
        """
        Detects anomalies using Z-score metric: (|x - mu| / sigma).
        """
        if len(historical_values) < 3:
            return {
                "is_anomaly": False,
                "reason": "INSUFFICIENT_HISTORICAL_DATA",
                "z_score": 0.0,
                "confidence": 0.0
            }

        mean, stddev = AnomalyDetector._calculate_mean_stddev(historical_values)
        if stddev == 0.0:
            is_anomaly = current_value != mean
            z_score = 999.0 if is_anomaly else 0.0
        else:
            z_score = abs(current_value - mean) / stddev
            is_anomaly = z_score > threshold

        severity = "CRITICAL" if z_score >= 5.0 else ("HIGH" if z_score >= 3.0 else "LOW")

        return {
            "is_anomaly": is_anomaly,
            "metric_value": current_value,
            "historical_mean": round(mean, 2),
            "historical_stddev": round(stddev, 2),
            "z_score": round(z_score, 2),
            "threshold": threshold,
            "severity": severity,
            "method": "Z_SCORE"
        }

    @staticmethod
    def detect_iqr_anomaly(
        historical_values: List[float],
        current_value: float,
        multiplier: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detects anomalies using Interquartile Range (IQR = Q3 - Q1).
        Outlier range: [Q1 - 1.5*IQR, Q3 + 1.5*IQR].
        """
        if len(historical_values) < 4:
            return {
                "is_anomaly": False,
                "reason": "INSUFFICIENT_HISTORICAL_DATA",
                "confidence": 0.0
            }

        sorted_vals = sorted(historical_values)
        q1 = AnomalyDetector._calculate_percentile(sorted_vals, 0.25)
        q3 = AnomalyDetector._calculate_percentile(sorted_vals, 0.75)
        iqr = q3 - q1

        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)
        is_anomaly = current_value < lower_bound or current_value > upper_bound

        return {
            "is_anomaly": is_anomaly,
            "metric_value": current_value,
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "iqr": round(iqr, 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "method": "IQR"
        }

    @staticmethod
    def detect_volume_anomaly(
        historical_counts: List[int],
        current_count: int
    ) -> Dict[str, Any]:
        """
        Detects volume drop/spike anomalies in dataset row counts.
        """
        float_hist = [float(x) for x in historical_counts]
        z_res = AnomalyDetector.detect_zscore_anomaly(float_hist, float(current_count))
        iqr_res = AnomalyDetector.detect_iqr_anomaly(float_hist, float(current_count))

        is_anomaly = z_res.get("is_anomaly", False) or iqr_res.get("is_anomaly", False)
        anomaly_type = "VOLUME_DROP" if (float_hist and current_count < (sum(float_hist) / len(float_hist))) else "VOLUME_SPIKE"

        return {
            "is_anomaly": is_anomaly,
            "anomaly_type": anomaly_type if is_anomaly else None,
            "current_count": current_count,
            "z_score_details": z_res,
            "iqr_details": iqr_res,
        }

    @staticmethod
    def detect_freshness_anomaly(
        last_updated_at: datetime,
        expected_frequency_hours: float = 24.0
    ) -> Dict[str, Any]:
        """
        Checks dataset freshness against expected SLA interval.
        """
        now = datetime.now(timezone.utc)
        if last_updated_at.tzinfo is None:
            last_updated_at = last_updated_at.replace(tzinfo=timezone.utc)

        elapsed_hours = (now - last_updated_at).total_seconds() / 3600.0
        is_stale = elapsed_hours > expected_frequency_hours

        return {
            "is_anomaly": is_stale,
            "elapsed_hours": round(elapsed_hours, 2),
            "expected_frequency_hours": expected_frequency_hours,
            "severity": "CRITICAL" if elapsed_hours > (2 * expected_frequency_hours) else "HIGH",
            "reason": "FRESHNESS_SLA_BREACH" if is_stale else "HEALTHY"
        }
