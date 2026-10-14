import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.models.catalog import Dataset
from backend.app.models.governance import GovernancePolicy, PolicyViolation
from governance.classification.pii_classifier import PIIClassifier

logger = logging.getLogger("GovernancePolicyEvaluator")

DEFAULT_GOVERNANCE_POLICIES = [
    {
        "policy_code": "POL-001",
        "name": "Mandatory Data Ownership",
        "description": "Every dataset in the data lake/catalog must have an assigned Data Owner.",
        "category": "OWNERSHIP",
        "severity": "HIGH",
    },
    {
        "policy_code": "POL-002",
        "name": "Minimum Quality Score SLA",
        "description": "Dataset quality score must be at least 80.0%.",
        "category": "QUALITY",
        "severity": "CRITICAL",
    },
    {
        "policy_code": "POL-003",
        "name": "PII Protection & Classification",
        "description": "All datasets containing PII must be properly classified and flagged for dynamic masking.",
        "category": "SECURITY",
        "severity": "CRITICAL",
    },
    {
        "policy_code": "POL-004",
        "name": "Refresh Frequency SLA Definition",
        "description": "Datasets must define an explicit refresh frequency SLA (HOURLY, DAILY, WEEKLY).",
        "category": "SLA",
        "severity": "MEDIUM",
    },
]


class GovernancePolicyEvaluator:
    """
    Evaluates enterprise governance policies against registered datasets and records.
    """

    @staticmethod
    def initialize_default_policies(db_session: Session) -> None:
        """
        Seeds default policies if not present in the database.
        """
        for pol_spec in DEFAULT_GOVERNANCE_POLICIES:
            existing = db_session.query(GovernancePolicy).filter_by(policy_code=pol_spec["policy_code"]).first()
            if not existing:
                policy = GovernancePolicy(
                    policy_code=pol_spec["policy_code"],
                    name=pol_spec["name"],
                    description=pol_spec["description"],
                    category=pol_spec["category"],
                    severity=pol_spec["severity"],
                    enabled=True,
                    owner="Governance Council"
                )
                db_session.add(policy)
        db_session.commit()

    @staticmethod
    def evaluate_policies(
        db_session: Session,
        dataset_name: str,
        records: Optional[List[Dict[str, Any]]] = None
    ) -> List[PolicyViolation]:
        """
        Evaluates active policies against target dataset and logs any PolicyViolation records.
        """
        GovernancePolicyEvaluator.initialize_default_policies(db_session)

        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            logger.warning(f"Dataset '{dataset_name}' not found for policy evaluation.")
            return []

        policies = db_session.query(GovernancePolicy).filter_by(enabled=True).all()
        violations = []

        for policy in policies:
            violation_desc = None

            # POL-001: Mandatory Ownership
            if policy.policy_code == "POL-001":
                if not dataset.owner_id and not dataset.owner:
                    violation_desc = f"Dataset '{dataset_name}' lacks an assigned Data Owner."

            # POL-002: Minimum Quality Score (>= 80.0%)
            elif policy.policy_code == "POL-002":
                score = dataset.quality_score if dataset.quality_score is not None else 100.0
                if score < 80.0:
                    violation_desc = f"Dataset '{dataset_name}' quality score ({score:.1f}%) is below SLA threshold of 80.0%."

            # POL-003: PII Classification & Masking
            elif policy.policy_code == "POL-003":
                if records:
                    class_map = PIIClassifier.classify_dataset(records)
                    pii_cols = [col for col, info in class_map.items() if info["classification"] == "PII"]
                    if pii_cols and dataset.classification == "INTERNAL":
                        violation_desc = f"Dataset '{dataset_name}' contains unflagged PII columns: {', '.join(pii_cols)}."

            # POL-004: Refresh Frequency SLA
            elif policy.policy_code == "POL-004":
                if not dataset.refresh_frequency or dataset.refresh_frequency.upper() == "UNKNOWN":
                    violation_desc = f"Dataset '{dataset_name}' does not have a defined refresh frequency SLA."

            if violation_desc:
                # Check existing open violation
                existing_violation = db_session.query(PolicyViolation).filter_by(
                    policy_id=policy.id,
                    dataset_id=dataset.id,
                    status="OPEN"
                ).first()

                if not existing_violation:
                    violation = PolicyViolation(
                        policy_id=policy.id,
                        dataset_id=dataset.id,
                        description=violation_desc,
                        status="OPEN",
                        detected_at=datetime.now(timezone.utc)
                    )
                    db_session.add(violation)
                    violations.append(violation)
                else:
                    violations.append(existing_violation)

        db_session.commit()
        for v in violations:
            db_session.refresh(v)

        logger.info(f"Policy evaluation completed for '{dataset_name}'. Found {len(violations)} violations.")
        return violations
