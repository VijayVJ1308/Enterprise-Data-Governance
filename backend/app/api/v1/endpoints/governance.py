from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from governance.classification.pii_classifier import PIIClassifier
from governance.masking.masking_engine import DataMaskingEngine
from governance.policies.policy_evaluator import GovernancePolicyEvaluator
from governance.compliance.compliance_service import ComplianceService

router = APIRouter()


class ClassifyDatasetRequest(BaseModel):
    records: List[Dict[str, Any]]


class MaskDatasetRequest(BaseModel):
    records: List[Dict[str, Any]]
    column_classifications: Dict[str, Dict[str, Any]]
    user_role: str = "DATA_ANALYST"


class EvaluatePoliciesRequest(BaseModel):
    dataset_name: str
    records: List[Dict[str, Any]]


@router.post("/classify", summary="Auto-Classify PII & Sensitivity")
def classify_dataset_fields(req: ClassifyDatasetRequest):
    """Auto-detect and classify PII, PHI, and sensitive data fields within dataset records."""
    class_map = PIIClassifier.classify_dataset(req.records)
    pii_columns = [col for col, info in class_map.items() if info.get("classification") == "PII"]
    return {
        "status": "success",
        "pii_columns": pii_columns,
        "classifications": class_map,
    }


@router.post("/mask", summary="Dynamic Field Masking")
def mask_dataset_fields(req: MaskDatasetRequest):
    """Apply dynamic field-level masking based on target user role (e.g. DATA_ANALYST vs DATA_ENGINEER)."""
    masked_records = DataMaskingEngine.mask_records(
        records=req.records,
        column_classifications=req.column_classifications,
        user_role=req.user_role,
    )
    return {
        "status": "success",
        "user_role": req.user_role,
        "masked_records": masked_records,
    }


@router.post("/policies/evaluate", summary="Evaluate Governance Policies")
def evaluate_policies(req: EvaluatePoliciesRequest, db: Session = Depends(get_db)):
    """Evaluate mandatory governance policies (PII protection, ownership, quality thresholds)."""
    violations = GovernancePolicyEvaluator.evaluate_policies(
        db_session=db, dataset_name=req.dataset_name, records=req.records
    )
    return {
        "dataset_name": req.dataset_name,
        "violation_count": len(violations),
        "violations": violations,
    }


@router.get("/compliance", summary="Get Compliance Framework Status")
def get_compliance_status(db: Session = Depends(get_db)):
    """Retrieve compliance framework control coverage (GDPR, HIPAA, SOC 2, ISO 27001)."""
    return ComplianceService.evaluate_compliance_status(db)
