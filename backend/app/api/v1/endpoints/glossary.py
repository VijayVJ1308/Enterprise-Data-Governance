from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from backend.app.services.glossary_service import GlossaryService

router = APIRouter()


class CreateTermRequest(BaseModel):
    term: str
    definition: str
    business_domain: str
    owner: Optional[str] = None
    status: str = "APPROVED"
    related_datasets: Optional[List[str]] = None


class UpdateTermRequest(BaseModel):
    definition: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    business_domain: Optional[str] = None


class LinkDatasetRequest(BaseModel):
    dataset_name: str


@router.get("/", summary="List & Search Glossary Terms")
def list_glossary_terms(
    q: Optional[str] = Query(None, description="Search term query"),
    domain: Optional[str] = Query(None, description="Filter by business domain"),
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, APPROVED, DEPRECATED)"),
    db: Session = Depends(get_db),
):
    """Retrieve and search business glossary terms."""
    terms = GlossaryService.search_terms(db, query_text=q, business_domain=domain, status=status)
    return [
        {
            "id": t.id,
            "term": t.term,
            "definition": t.definition,
            "business_domain": t.business_domain,
            "owner": t.owner,
            "status": t.status,
            "related_datasets": t.related_datasets or [],
        }
        for t in terms
    ]


@router.post("/", summary="Create Business Glossary Term")
def create_glossary_term(req: CreateTermRequest, db: Session = Depends(get_db)):
    """Define a new enterprise business glossary term."""
    try:
        term_item = GlossaryService.create_term(
            db,
            term=req.term,
            definition=req.definition,
            business_domain=req.business_domain,
            owner=req.owner,
            status=req.status,
            related_datasets=req.related_datasets,
        )
        return {
            "status": "success",
            "term_id": term_item.id,
            "term": term_item.term,
            "business_domain": term_item.business_domain,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{term_id_or_name}", summary="Update Glossary Term")
def update_glossary_term(term_id_or_name: str, req: UpdateTermRequest, db: Session = Depends(get_db)):
    """Update an existing glossary term's definition, domain, owner, or status."""
    try:
        term_item = GlossaryService.update_term(
            db,
            term_id_or_name,
            definition=req.definition,
            owner=req.owner,
            status=req.status,
            business_domain=req.business_domain,
        )
        return {
            "status": "success",
            "term_id": term_item.id,
            "term": term_item.term,
            "status_code": term_item.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{term_id_or_name}/link", summary="Link Dataset to Glossary Term")
def link_dataset_to_term(term_id_or_name: str, req: LinkDatasetRequest, db: Session = Depends(get_db)):
    """Link a dataset to a business glossary term."""
    try:
        term_item = GlossaryService.link_dataset_to_term(db, term_id_or_name, req.dataset_name)
        return {
            "status": "success",
            "term": term_item.term,
            "related_datasets": term_item.related_datasets,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
