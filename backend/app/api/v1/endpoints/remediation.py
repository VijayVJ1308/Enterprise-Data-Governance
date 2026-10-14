from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from data_quality.remediation.remediation_engine import RemediationService

router = APIRouter()


class RemediationActionRequest(BaseModel):
    dataset_name: str
    action_type: str  # TRIM_WHITESPACE, CASE_NORMALIZE, FILL_DEFAULT, COUNTRY_NORMALIZE, DEDUPLICATE
    records: List[Dict[str, Any]]
    params: Optional[Dict[str, Any]] = None
    executed_by: str = "API_USER"


@router.post("/execute", summary="Execute Automated Remediation Action")
def execute_remediation(req: RemediationActionRequest, db: Session = Depends(get_db)):
    """Executes deterministic data remediation (whitespace trimming, case normalization, deduplication, default filling)."""
    try:
        remediated_records, action_log = RemediationService.execute_remediation_action(
            db_session=db,
            dataset_name=req.dataset_name,
            action_type=req.action_type,
            records=req.records,
            params=req.params or {},
            executed_by=req.executed_by,
        )
        return {
            "status": "success",
            "dataset_name": req.dataset_name,
            "action_type": req.action_type,
            "records_remediated": len(remediated_records),
            "rows_affected": action_log.affected_rows if action_log else 0,
            "audit_action_id": action_log.id if action_log else None,
            "remediated_records": remediated_records,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
