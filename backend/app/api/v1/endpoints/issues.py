from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.api.deps import get_db
from data_quality.issue_management.issue_service import IssueManagementService

router = APIRouter()


class CreateIssueRequest(BaseModel):
    dataset_name: str
    description: str
    column_name: Optional[str] = None
    rule_id: Optional[str] = None
    severity: str = "MEDIUM"
    owner: Optional[str] = None
    assigned_to: Optional[str] = None


class TransitionStatusRequest(BaseModel):
    new_status: str
    resolution_notes: Optional[str] = None
    user: str = "SYSTEM"


class AssignIssueRequest(BaseModel):
    assignee_email: str
    user: str = "SYSTEM"


@router.get("/", summary="List Quality Issues")
def list_issues(
    dataset_name: Optional[str] = Query(None, description="Filter by dataset name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    db: Session = Depends(get_db),
):
    """Retrieve quality issues with optional status/severity/dataset filtering."""
    issues = IssueManagementService.list_issues(
        db, dataset_name=dataset_name, status=status, severity=severity
    )
    return [
        {
            "issue_id": i.issue_id,
            "column_name": i.column_name,
            "severity": i.severity,
            "status": i.status,
            "description": i.description,
            "assigned_to": i.assigned_to,
            "detected_at": i.detected_at.isoformat() if i.detected_at else None,
            "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        }
        for i in issues
    ]


@router.post("/", summary="Create Quality Issue")
def create_issue(req: CreateIssueRequest, db: Session = Depends(get_db)):
    """Create a new data quality issue."""
    try:
        issue = IssueManagementService.create_issue(
            db,
            dataset_name=req.dataset_name,
            description=req.description,
            column_name=req.column_name,
            rule_id=req.rule_id,
            severity=req.severity,
            owner=req.owner,
            assigned_to=req.assigned_to,
        )
        return {
            "status": "success",
            "issue_id": issue.issue_id,
            "severity": issue.severity,
            "issue_status": issue.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{issue_id}/transition", summary="Transition Issue Lifecycle Status")
def transition_issue_status(issue_id: str, req: TransitionStatusRequest, db: Session = Depends(get_db)):
    """Transition an issue status following allowed state machine lifecycle rules."""
    try:
        issue = IssueManagementService.transition_status(
            db, issue_id, req.new_status, req.resolution_notes, req.user
        )
        return {
            "status": "success",
            "issue_id": issue.issue_id,
            "current_status": issue.status,
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{issue_id}/assign", summary="Assign Quality Issue")
def assign_issue(issue_id: str, req: AssignIssueRequest, db: Session = Depends(get_db)):
    """Assign an issue to a steward or data engineer."""
    try:
        issue = IssueManagementService.assign_issue(db, issue_id, req.assignee_email)
        return {
            "status": "success",
            "issue_id": issue.issue_id,
            "assigned_to": issue.assigned_to,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
