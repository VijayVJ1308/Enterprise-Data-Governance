from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from data_quality.profiling.profiler import DataProfiler
from data_quality.engine.rule_evaluator import RuleEvaluator
from data_quality.rules.default_rules import DEFAULT_ENTERPRISE_RULES
from data_quality.scoring.score_calculator import QualityScoreCalculator
from data_quality.scoring.score_repository import ScoreRepository
from backend.app.models.catalog import Dataset, MetadataEntry
import json

router = APIRouter()


class ProfileRequest(BaseModel):
    dataset_name: str
    records: List[Dict[str, Any]]


class EvaluateRulesRequest(BaseModel):
    dataset_name: str
    records: List[Dict[str, Any]]


@router.post("/profile", summary="Profile Dataset Records")
def profile_dataset(req: ProfileRequest):
    """Generates column metrics, null rates, uniqueness, and statistics for raw dataset records."""
    profiler = DataProfiler()
    profile = profiler.profile_records(req.dataset_name, req.records)
    return profile


@router.post("/evaluate", summary="Evaluate Quality Rules")
def evaluate_quality_rules(req: EvaluateRulesRequest):
    """Evaluates declarative quality rules against dataset records."""
    evaluator = RuleEvaluator()
    ds_rules = [r for r in DEFAULT_ENTERPRISE_RULES if r.dataset_name == req.dataset_name]
    if not ds_rules:
        # Fall back to evaluating default rules if none explicitly mapped
        ds_rules = DEFAULT_ENTERPRISE_RULES[:3]

    results = []
    for rule in ds_rules:
        res = evaluator.evaluate_rule(rule, req.records)
        results.append({
            "rule_id": rule.rule_id,
            "rule_name": rule.rule_name,
            "dataset_name": rule.dataset_name,
            "rule_type": rule.rule_type,
            "target_column": rule.column_name,
            "passed": res.passed,
            "pass_rate": res.pass_rate,
            "failed_records_count": res.failed_records,
            "total_records": res.total_records,
        })
    return {"dataset_name": req.dataset_name, "rule_results": results}


@router.get("/scores/{dataset_name}", summary="Get Quality Score Breakdown")
def get_quality_score(dataset_name: str, db: Session = Depends(get_db)):
    """Retrieves current quality score and 6-dimension breakdown for a dataset."""
    dataset = db.query(Dataset).filter_by(dataset_name=dataset_name).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found.")

    meta_key = f"quality_score_dimensions_{dataset_name}"
    meta_entry = db.query(MetadataEntry).filter_by(key=meta_key).first()
    dimension_scores = json.loads(meta_entry.value) if meta_entry and meta_entry.value else {}

    return {
        "dataset_name": dataset.dataset_name,
        "overall_quality_score": dataset.quality_score,
        "dimension_scores": dimension_scores,
        "certification_status": dataset.certification_status,
    }
