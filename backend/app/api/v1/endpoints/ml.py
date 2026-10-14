from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from ml.anomaly_detector import AnomalyDetector
from ml.rule_recommender import MLRuleRecommender

router = APIRouter()


class VolumeAnomalyRequest(BaseModel):
    historical_counts: List[int]
    current_count: int


class RecommendRulesRequest(BaseModel):
    dataset_name: str
    records: List[Dict[str, Any]]


@router.post("/anomalies/detect", summary="Detect Volume Anomaly")
def detect_volume_anomaly(req: VolumeAnomalyRequest):
    """Detect statistical row count volume anomalies using Z-score and Interquartile Range (IQR)."""
    res = AnomalyDetector.detect_volume_anomaly(req.historical_counts, req.current_count)
    return res


@router.post("/rules/recommend", summary="ML Rule Recommendations")
def recommend_rules(req: RecommendRulesRequest):
    """Generate ML-driven recommended quality rules based on dataset profiling and column distributions."""
    recs = MLRuleRecommender.recommend_rules_for_dataset(req.dataset_name, req.records)
    return {
        "dataset_name": req.dataset_name,
        "recommended_rules_count": len(recs),
        "recommendations": recs,
    }
