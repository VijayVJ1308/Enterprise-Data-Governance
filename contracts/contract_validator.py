import logging
import yaml
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset
from backend.app.models.schema_contract import DataContract, DataContractViolation

logger = logging.getLogger("ContractValidator")


class ContractValidator:

    @staticmethod
    def register_contract(
        db_session: Session,
        dataset_name: str,
        yaml_spec: str,
        contract_name: Optional[str] = None,
        version: str = "1.0.0",
        status: str = "ACTIVE",
    ) -> DataContract:
        """
        Parses and registers a declarative YAML Data Contract for a target dataset.
        """
        parsed_spec = yaml.safe_load(yaml_spec)
        c_name = contract_name or parsed_spec.get("contract_name") or f"{dataset_name}_contract"

        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found in Data Catalog.")

        existing = db_session.query(DataContract).filter_by(contract_name=c_name).first()
        if existing:
            existing.yaml_spec = yaml_spec
            existing.version = version
            existing.status = status
            db_session.commit()
            db_session.refresh(existing)
            logger.info(f"Updated existing Data Contract '{c_name}' (v{version}).")
            return existing

        contract = DataContract(
            contract_name=c_name,
            dataset_id=dataset.id,
            version=version,
            yaml_spec=yaml_spec,
            status=status.upper(),
        )
        db_session.add(contract)
        db_session.commit()
        db_session.refresh(contract)
        logger.info(f"Registered new Data Contract '{c_name}' (v{version}) for dataset '{dataset_name}'.")
        return contract

    @staticmethod
    def validate_contract(
        db_session: Session,
        contract_name: str,
        current_columns_spec: List[Dict[str, Any]],  # e.g. [{"name": "id", "type": "INTEGER", "nullable": False}]
        current_quality_score: Optional[float] = None,
        data_timestamp: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Validates an incoming dataset's schema, quality score, and data freshness against an active Data Contract.
        Generates DataContractViolation entries for any contract breaches.
        """
        contract = db_session.query(DataContract).filter_by(contract_name=contract_name).first()
        if not contract:
            raise ValueError(f"Data Contract '{contract_name}' not found.")

        if contract.status != "ACTIVE":
            logger.warning(f"Data Contract '{contract_name}' is currently {contract.status}. Skipping validation.")
            return {"passed": True, "violations": [], "status": contract.status}

        parsed_spec = yaml.safe_load(contract.yaml_spec)
        violations: List[Dict[str, str]] = []

        # 1. Validate Schema Constraints
        expected_columns = {col["name"]: col for col in parsed_spec.get("schema", [])}
        actual_columns = {col["name"]: col for col in current_columns_spec}

        for col_name, expected_col in expected_columns.items():
            if col_name not in actual_columns:
                violations.append({
                    "type": "SCHEMA_MISMATCH",
                    "details": f"Missing required column '{col_name}' specified in contract schema.",
                })
            else:
                actual_col = actual_columns[col_name]
                if expected_col.get("type") and actual_col.get("type") and expected_col["type"].upper() != actual_col["type"].upper():
                    violations.append({
                        "type": "SCHEMA_MISMATCH",
                        "details": f"Column '{col_name}' data type mismatch. Expected '{expected_col['type']}', found '{actual_col['type']}'.",
                    })
                if expected_col.get("nullable") is False and actual_col.get("nullable") is True:
                    violations.append({
                        "type": "SCHEMA_MISMATCH",
                        "details": f"Column '{col_name}' nullability constraint breach. Contract expects non-nullable column.",
                    })

        # 2. Validate Quality SLA Constraints
        quality_slas = parsed_spec.get("quality_slas", {})
        min_quality_score = quality_slas.get("min_quality_score")
        if min_quality_score is not None and current_quality_score is not None:
            if current_quality_score < min_quality_score:
                violations.append({
                    "type": "QUALITY_SLA_BREACH",
                    "details": f"Dataset quality score {current_quality_score:.2f}% is below required SLA threshold of {min_quality_score:.2f}%.",
                })

        # 3. Validate Freshness SLA Constraints
        freshness_slas = parsed_spec.get("freshness_slas", {})
        max_age_hours = freshness_slas.get("max_age_hours")
        if max_age_hours is not None and data_timestamp is not None:
            now = datetime.now(timezone.utc)
            if data_timestamp.tzinfo is None:
                data_timestamp = data_timestamp.replace(tzinfo=timezone.utc)
            data_age_hours = (now - data_timestamp).total_seconds() / 3600.0
            if data_age_hours > max_age_hours:
                violations.append({
                    "type": "FRESHNESS_SLA_BREACH",
                    "details": f"Data age ({data_age_hours:.1f} hours) exceeds contract freshness threshold of {max_age_hours} hours.",
                })

        # Persist violations in database
        persisted_violations = []
        for v in violations:
            violation_record = DataContractViolation(
                contract_id=contract.id,
                violation_type=v["type"],
                details=v["details"],
            )
            db_session.add(violation_record)
            persisted_violations.append(v)

        if violations:
            db_session.commit()
            logger.warning(f"Data Contract '{contract_name}' validation failed with {len(violations)} violations.")

        return {
            "passed": len(violations) == 0,
            "contract_name": contract_name,
            "violations_count": len(violations),
            "violations": persisted_violations,
        }

    @staticmethod
    def get_contract_violations(db_session: Session, contract_name: str) -> List[DataContractViolation]:
        contract = db_session.query(DataContract).filter_by(contract_name=contract_name).first()
        if not contract:
            return []
        return db_session.query(DataContractViolation).filter_by(contract_id=contract.id).order_by(DataContractViolation.detected_at.desc()).all()
