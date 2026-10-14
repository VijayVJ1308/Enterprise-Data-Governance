import hashlib
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset
from backend.app.models.schema_contract import SchemaVersion, SchemaDriftEvent

logger = logging.getLogger("SchemaDriftEngine")


class SchemaDriftEngine:

    @staticmethod
    def _compute_schema_hash(columns_spec: List[Dict[str, Any]]) -> str:
        """
        Computes a deterministic SHA256 hash for a given column specification.
        """
        sorted_cols = sorted(
            [{"name": c["name"], "type": c.get("type", "STRING").upper(), "nullable": c.get("nullable", True)} for c in columns_spec],
            key=lambda x: x["name"],
        )
        serialized = json.dumps(sorted_cols, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def record_schema_version(
        db_session: Session,
        dataset_name: str,
        columns_spec: List[Dict[str, Any]],
    ) -> SchemaVersion:
        """
        Records an initial or baseline schema version for a dataset.
        """
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found in Data Catalog.")

        schema_hash = SchemaDriftEngine._compute_schema_hash(columns_spec)

        latest_version = (
            db_session.query(SchemaVersion)
            .filter_by(dataset_id=dataset.id)
            .order_by(SchemaVersion.version_number.desc())
            .first()
        )

        next_version_num = (latest_version.version_number + 1) if latest_version else 1

        version_record = SchemaVersion(
            dataset_id=dataset.id,
            version_number=next_version_num,
            schema_hash=schema_hash,
            columns_spec=columns_spec,
        )
        db_session.add(version_record)
        db_session.commit()
        db_session.refresh(version_record)
        logger.info(f"Recorded Schema Version v{next_version_num} for dataset '{dataset_name}' (Hash: {schema_hash[:8]}).")
        return version_record

    @staticmethod
    def detect_schema_drift(
        db_session: Session,
        dataset_name: str,
        incoming_columns_spec: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compares incoming dataset schema against the latest recorded SchemaVersion.
        Detects added, removed, type-changed, or nullability-changed columns.
        """
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_name}' not found in Data Catalog.")

        latest_version = (
            db_session.query(SchemaVersion)
            .filter_by(dataset_id=dataset.id)
            .order_by(SchemaVersion.version_number.desc())
            .first()
        )

        # If no previous version exists, record baseline
        if not latest_version:
            new_version = SchemaDriftEngine.record_schema_version(db_session, dataset_name, incoming_columns_spec)
            return {
                "drift_detected": False,
                "dataset_name": dataset_name,
                "message": "Initial schema baseline created.",
                "current_version": new_version.version_number,
                "drift_events": [],
            }

        incoming_hash = SchemaDriftEngine._compute_schema_hash(incoming_columns_spec)
        if incoming_hash == latest_version.schema_hash:
            return {
                "drift_detected": False,
                "dataset_name": dataset_name,
                "message": "Schema matches latest version. No drift detected.",
                "current_version": latest_version.version_number,
                "drift_events": [],
            }

        # Compare column specs
        prev_cols = {c["name"]: c for c in latest_version.columns_spec}
        inc_cols = {c["name"]: c for c in incoming_columns_spec}

        drift_events: List[Dict[str, Any]] = []

        # 1. Added Columns
        for col_name, inc_spec in inc_cols.items():
            if col_name not in prev_cols:
                drift_events.append({
                    "column_name": col_name,
                    "drift_type": "ADDED",
                    "previous_value": None,
                    "current_value": json.dumps(inc_spec),
                    "severity": "LOW",
                })

        # 2. Removed Columns
        for col_name, prev_spec in prev_cols.items():
            if col_name not in inc_cols:
                drift_events.append({
                    "column_name": col_name,
                    "drift_type": "REMOVED",
                    "previous_value": json.dumps(prev_spec),
                    "current_value": None,
                    "severity": "CRITICAL",
                })

        # 3. Modified Columns (Type changed, Nullable changed)
        for col_name in set(prev_cols.keys()).intersection(inc_cols.keys()):
            p_spec = prev_cols[col_name]
            i_spec = inc_cols[col_name]

            p_type = p_spec.get("type", "STRING").upper()
            i_type = i_spec.get("type", "STRING").upper()

            if p_type != i_type:
                drift_events.append({
                    "column_name": col_name,
                    "drift_type": "TYPE_CHANGED",
                    "previous_value": p_type,
                    "current_value": i_type,
                    "severity": "CRITICAL",
                })

            p_null = p_spec.get("nullable", True)
            i_null = i_spec.get("nullable", True)
            if p_null != i_null:
                drift_events.append({
                    "column_name": col_name,
                    "drift_type": "NULLABLE_CHANGED",
                    "previous_value": str(p_null),
                    "current_value": str(i_null),
                    "severity": "MEDIUM",
                })

        # Record drift events and create new schema version
        persisted_events = []
        for dev in drift_events:
            event_record = SchemaDriftEvent(
                dataset_id=dataset.id,
                column_name=dev["column_name"],
                drift_type=dev["drift_type"],
                previous_value=dev["previous_value"],
                current_value=dev["current_value"],
                severity=dev["severity"],
            )
            db_session.add(event_record)
            persisted_events.append(dev)

        new_version = SchemaDriftEngine.record_schema_version(db_session, dataset_name, incoming_columns_spec)

        logger.warning(f"Detected schema drift in dataset '{dataset_name}': {len(drift_events)} changes logged.")

        return {
            "drift_detected": True,
            "dataset_name": dataset_name,
            "previous_version": latest_version.version_number,
            "current_version": new_version.version_number,
            "drift_events_count": len(drift_events),
            "drift_events": persisted_events,
        }

    @staticmethod
    def get_drift_events(db_session: Session, dataset_name: str) -> List[SchemaDriftEvent]:
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            return []
        return (
            db_session.query(SchemaDriftEvent)
            .filter_by(dataset_id=dataset.id)
            .order_by(SchemaDriftEvent.detected_at.desc())
            .all()
        )
