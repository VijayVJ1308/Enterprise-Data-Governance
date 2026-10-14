from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class DimensionWeights:
    completeness: float = 0.25
    validity: float = 0.20
    uniqueness: float = 0.20
    consistency: float = 0.15
    timeliness: float = 0.10
    accuracy: float = 0.10


@dataclass
class QualityScoreBreakdown:
    dataset_name: str
    completeness_score: float
    validity_score: float
    uniqueness_score: float
    consistency_score: float
    timeliness_score: float
    accuracy_score: float
    overall_quality_score: float
    dimension_scores: Dict[str, float] = field(default_factory=dict)


class QualityScoreCalculator:
    """
    Quality Score Calculation Engine across 6 dimensions:
    Completeness, Validity, Uniqueness, Consistency, Timeliness, Accuracy.
    """

    def __init__(self, weights: DimensionWeights = None):
        self.weights = weights or DimensionWeights()

    def calculate_dataset_score(
        self,
        dataset_name: str,
        profile_data: Dict[str, Any],
        quality_results: List[Dict[str, Any]],
    ) -> QualityScoreBreakdown:

        # 1. Completeness Score (Average non-null rate across columns)
        null_pcts = profile_data.get("null_percentages", {})
        if null_pcts:
            comp_score = sum(100.0 - float(pct) for pct in null_pcts.values()) / len(null_pcts)
        else:
            comp_score = 100.0

        # 2. Uniqueness Score (Uniqueness rate across columns)
        unique_pcts = profile_data.get("uniqueness_percentages", {})
        if unique_pcts:
            uniq_score = sum(float(pct) for pct in unique_pcts.values()) / len(unique_pcts)
        else:
            uniq_score = 100.0

        # 3. Rule Pass Rates categorized by dimension
        validity_passes = []
        consistency_passes = []
        accuracy_passes = []

        for r in quality_results:
            rule_type = str(r.get("rule_type", "")).upper()
            pass_rate = float(r.get("pass_rate", 100.0))

            if rule_type in ["VALID_FORMAT", "REGEX", "RANGE", "ACCEPTED_VALUES"]:
                validity_passes.append(pass_rate)
            elif rule_type in ["BUSINESS_RULE", "CUSTOM_PYTHON", "CUSTOM_SQL"]:
                consistency_passes.append(pass_rate)
            elif rule_type in ["REFERENTIAL_INTEGRITY", "SCHEMA"]:
                accuracy_passes.append(pass_rate)

        val_score = sum(validity_passes) / len(validity_passes) if validity_passes else 95.0
        cons_score = sum(consistency_passes) / len(consistency_passes) if consistency_passes else 95.0
        acc_score = sum(accuracy_passes) / len(accuracy_passes) if accuracy_passes else 95.0
        time_score = 98.0  # Default freshness SLA score

        # 4. Weighted Overall Quality Score
        w = self.weights
        overall = round(
            (comp_score * w.completeness)
            + (val_score * w.validity)
            + (uniq_score * w.uniqueness)
            + (cons_score * w.consistency)
            + (time_score * w.timeliness)
            + (acc_score * w.accuracy),
            2,
        )

        dim_scores = {
            "Completeness": round(comp_score, 2),
            "Validity": round(val_score, 2),
            "Uniqueness": round(uniq_score, 2),
            "Consistency": round(cons_score, 2),
            "Timeliness": round(time_score, 2),
            "Accuracy": round(acc_score, 2),
        }

        return QualityScoreBreakdown(
            dataset_name=dataset_name,
            completeness_score=round(comp_score, 2),
            validity_score=round(val_score, 2),
            uniqueness_score=round(uniq_score, 2),
            consistency_score=round(cons_score, 2),
            timeliness_score=round(time_score, 2),
            accuracy_score=round(acc_score, 2),
            overall_quality_score=overall,
            dimension_scores=dim_scores,
        )

    def calculate_enterprise_score(self, dataset_scores: List[QualityScoreBreakdown]) -> Dict[str, Any]:
        if not dataset_scores:
            return {"enterprise_quality_score": 100.0, "total_datasets": 0}

        avg_score = sum(ds.overall_quality_score for ds in dataset_scores) / len(dataset_scores)
        return {
            "enterprise_quality_score": round(avg_score, 2),
            "total_datasets": len(dataset_scores),
            "dataset_scores": {ds.dataset_name: ds.overall_quality_score for ds in dataset_scores},
        }
