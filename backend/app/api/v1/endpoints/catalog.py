from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from backend.app.services.catalog_service import CatalogService

router = APIRouter()


class DatasetRegisterRequest(BaseModel):
    dataset_name: str
    domain: str
    source_system: str
    location: str
    description: Optional[str] = None
    format_type: str = "parquet"
    refresh_frequency: str = "DAILY"
    classification: str = "INTERNAL"
    owner_email: Optional[str] = None
    steward_email: Optional[str] = None


class CertificationUpdateRequest(BaseModel):
    status: str
    updated_by: str = "SYSTEM"


@router.get("/search", summary="Search Data Catalog")
def search_catalog(
    q: Optional[str] = Query(None, description="Search query string"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    certification_status: Optional[str] = Query(None, description="Filter by certification status"),
    min_quality_score: Optional[float] = Query(None, description="Minimum quality score"),
    db: Session = Depends(get_db),
):
    """Search catalog datasets using text query or structured filters."""
    datasets = CatalogService.search_catalog(
        db,
        query_text=q,
        domain=domain,
        classification=classification,
        certification_status=certification_status,
        min_quality_score=min_quality_score,
    )
    return [
        {
            "id": d.id,
            "dataset_name": d.dataset_name,
            "domain": d.domain,
            "source_system": d.source_system,
            "location": d.location,
            "quality_score": d.quality_score,
            "classification": d.classification,
            "certification_status": d.certification_status,
            "description": d.description,
        }
        for d in datasets
    ]


@router.post("/register", summary="Register New Dataset")
def register_dataset(req: DatasetRegisterRequest, db: Session = Depends(get_db)):
    """Register a new dataset in the metadata catalog."""
    dataset = CatalogService.register_dataset(
        db_session=db,
        dataset_name=req.dataset_name,
        domain=req.domain,
        source_system=req.source_system,
        location=req.location,
        description=req.description,
        format_type=req.format_type,
        refresh_frequency=req.refresh_frequency,
        classification=req.classification,
        owner_email=req.owner_email,
        steward_email=req.steward_email,
    )
    return {
        "status": "success",
        "dataset_id": dataset.id,
        "dataset_name": dataset.dataset_name,
        "domain": dataset.domain,
    }


@router.get("/{dataset_id_or_name}", summary="Get Dataset Details")
def get_dataset(dataset_id_or_name: str, db: Session = Depends(get_db)):
    """Retrieve complete metadata, schema, and profiles for a dataset."""
    details = CatalogService.get_dataset_details(db, dataset_id_or_name)
    if not details:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id_or_name}' not found.")
    return details


@router.put("/{dataset_id}/certification", summary="Update Certification Status")
def update_certification(dataset_id: str, req: CertificationUpdateRequest, db: Session = Depends(get_db)):
    """Update dataset certification status (UNCERTIFIED, DRAFT, PENDING, CERTIFIED)."""
    dataset = CatalogService.update_certification_status(db, dataset_id, req.status, req.updated_by)
    if not dataset:
        raise HTTPException(status_code=400, detail=f"Invalid status or dataset '{dataset_id}' not found.")
    return {
        "status": "success",
        "dataset_id": dataset.id,
        "certification_status": dataset.certification_status,
    }
