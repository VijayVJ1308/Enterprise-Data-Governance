import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.quality import QualityIssue, QualityRule
from backend.app.models.catalog import Dataset

logger = logging.getLogger("IssueManagementService")

VALID_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "IGNORED", "REOPENED"}
VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

# State machine allowed transitions
ALLOWED_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "IGNORED", "RESOLVED"},
    "IN_PROGRESS": {"RESOLVED", "IGNORED", "OPEN"},
    "RESOLVED": {"REOPENED"},
    "IGNORED": {"REOPENED", "OPEN"},
    "REOPENED": {"IN_PROGRESS", "RESOLVED", "IGNORED"},
}


class IssueManagementService:

    @staticmethod
    def create_issue(
        db_session: Session,
        dataset_name: str,
        description: str,
        column_name: Optional[str] = None,
        rule_id: Optional[str] = None,
        severity: str = "MEDIUM",
        owner: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> QualityIssue:
        sev_upper = severity.upper()
        if sev_upper not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{severity}'. Must be one of {VALID_SEVERITIES}")

        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            dataset = Dataset(dataset_name=dataset_name, domain="General", source_system="IngestionPlatform", location="data/lake/bronze")
            db_session.add(dataset)
            db_session.flush()

        rule_obj = db_session.query(QualityRule).filter_by(rule_id=rule_id).first() if rule_id else None
        rule_fk = rule_obj.id if rule_obj else None

        issue_id = f"ISS-{uuid_hex()[:8]}"
        issue = QualityIssue(
            issue_id=issue_id,
            dataset_id=dataset.id,
            column_name=column_name,
            rule_id=rule_fk,
            severity=sev_upper,
            description=description,
            status="OPEN",
            owner=owner or dataset.owner_id,
            assigned_to=assigned_to,
            detected_at=datetime.now(timezone.utc),
        )
        db_session.add(issue)
        db_session.commit()
        db_session.refresh(issue)
        logger.info(f"Created Quality Issue '{issue_id}' for dataset '{dataset_name}' (Severity: {sev_upper}).")
        return issue

    @staticmethod
    def transition_status(
        db_session: Session,
        issue_id: str,
        new_status: str,
        resolution_notes: Optional[str] = None,
        user: str = "SYSTEM",
    ) -> QualityIssue:
        issue = db_session.query(QualityIssue).filter_by(issue_id=issue_id).first()
        if not issue:
            raise ValueError(f"Issue '{issue_id}' not found.")

        target_status = new_status.upper()
        if target_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {VALID_STATUSES}")

        current_status = issue.status.upper()
        allowed = ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValueError(f"Invalid state transition from '{current_status}' to '{target_status}'. Allowed: {allowed}")

        issue.status = target_status
        if resolution_notes:
            issue.resolution_notes = resolution_notes

        if target_status in ["RESOLVED", "IGNORED"]:
            issue.resolved_at = datetime.now(timezone.utc)
        elif target_status == "REOPENED":
            issue.resolved_at = None

        db_session.commit()
        db_session.refresh(issue)
        logger.info(f"Transitioned Issue '{issue_id}' status: {current_status} -> {target_status} by {user}.")
        return issue

    @staticmethod
    def assign_issue(db_session: Session, issue_id: str, assigned_to: str) -> QualityIssue:
        issue = db_session.query(QualityIssue).filter_by(issue_id=issue_id).first()
        if not issue:
            raise ValueError(f"Issue '{issue_id}' not found.")

        issue.assigned_to = assigned_to
        db_session.commit()
        db_session.refresh(issue)
        logger.info(f"Assigned Issue '{issue_id}' to '{assigned_to}'.")
        return issue

    @staticmethod
    def list_issues(
        db_session: Session,
        dataset_name: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[QualityIssue]:
        query = db_session.query(QualityIssue)

        if dataset_name:
            dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
            if dataset:
                query = query.filter_by(dataset_id=dataset.id)
            else:
                return []

        if status:
            query = query.filter_by(status=status.upper())

        if severity:
            query = query.filter_by(severity=severity.upper())

        if owner:
            query = query.filter(QualityIssue.owner == owner)

        return query.all()


def uuid_hex():
    import uuid
    return uuid.uuid4().hex
