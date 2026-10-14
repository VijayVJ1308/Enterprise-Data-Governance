import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset, DatasetProfile, DatasetColumn

logger = logging.getLogger("ProfileRepository")


class ProfileRepository:

    @staticmethod
    def save_profile(db_session: Session, profile_data: Dict[str, Any]) -> DatasetProfile:
        dataset_name = profile_data["dataset_name"]
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()

        # If dataset does not exist in catalog, auto-create catalog entry
        if not dataset:
            dataset = Dataset(
                dataset_name=dataset_name,
                description=f"Auto-registered dataset profile for {dataset_name}",
                domain="General",
                source_system="IngestionPlatform",
                location=f"data/lake/bronze/{dataset_name}",
                format="json",
                row_count=profile_data["row_count"],
            )
            db_session.add(dataset)
            db_session.flush()

        dataset.row_count = profile_data["row_count"]

        # Save DatasetProfile record
        profile_record = DatasetProfile(
            dataset_id=dataset.id,
            row_count=profile_data["row_count"],
            column_count=profile_data["column_count"],
            null_counts=profile_data["null_counts"],
            null_percentages=profile_data["null_percentages"],
            unique_counts=profile_data["unique_counts"],
            uniqueness_percentages=profile_data["uniqueness_percentages"],
            column_statistics=profile_data["column_statistics"],
        )
        db_session.add(profile_record)

        # Sync DatasetColumn entries
        for col_name, col_stats in profile_data.get("column_statistics", {}).items():
            existing_col = db_session.query(DatasetColumn).filter_by(dataset_id=dataset.id, column_name=col_name).first()
            if not existing_col:
                col_entry = DatasetColumn(
                    dataset_id=dataset.id,
                    column_name=col_name,
                    data_type=col_stats.get("data_type", "STRING"),
                    is_nullable=profile_data["null_counts"].get(col_name, 0) > 0,
                    classification="PII" if "email" in col_name.lower() or "phone" in col_name.lower() else "INTERNAL",
                )
                db_session.add(col_entry)

        db_session.commit()
        db_session.refresh(profile_record)
        logger.info(f"Persisted profile for dataset '{dataset_name}' (ID: {dataset.id}).")
        return profile_record
