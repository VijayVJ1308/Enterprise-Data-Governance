from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from contracts.contract_validator import ContractValidator
from contracts.drift_detector import SchemaDriftEngine

router = APIRouter()


class RegisterContractRequest(BaseModel):
    dataset_name: str
    yaml_spec: str
    contract_name: Optional[str] = None
    version: str = "1.0.0"
    status: str = "ACTIVE"


class ValidateContractRequest(BaseModel):
    contract_name: str
    columns_spec: List[Dict[str, Any]]
    quality_score: Optional[float] = None


class SchemaDriftRequest(BaseModel):
    dataset_name: str
    columns_spec: List[Dict[str, Any]]


@router.post("/register", summary="Register Data Contract")
def register_contract(req: RegisterContractRequest, db: Session = Depends(get_db)):
    """Register or update a declarative YAML Data Contract for a dataset."""
    try:
        contract = ContractValidator.register_contract(
            db,
            dataset_name=req.dataset_name,
            yaml_spec=req.yaml_spec,
            contract_name=req.contract_name,
            version=req.version,
            status=req.status,
        )
        return {
            "status": "success",
            "contract_id": contract.id,
            "contract_name": contract.contract_name,
            "version": contract.version,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate", summary="Validate Data Contract Constraints")
def validate_contract(req: ValidateContractRequest, db: Session = Depends(get_db)):
    """Validate incoming schema and quality score against active Data Contract."""
    try:
        res = ContractValidator.validate_contract(
            db,
            contract_name=req.contract_name,
            current_columns_spec=req.columns_spec,
            current_quality_score=req.quality_score,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/drift/detect", summary="Detect Schema Drift")
def detect_schema_drift(req: SchemaDriftRequest, db: Session = Depends(get_db)):
    """Compare incoming dataset schema against baseline schema version to detect schema drift."""
    try:
        return SchemaDriftEngine.detect_schema_drift(db, req.dataset_name, req.columns_spec)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
