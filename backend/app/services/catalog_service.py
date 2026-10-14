import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.app.models.catalog import Dataset, DatasetColumn, DatasetProfile, DataOwner, DataSteward

logger = logging.getLogger("CatalogService")

VALID_CERTIFICATION_STATUSES = {"UNCERTIFIED", "DRAFT", "PENDING", "CERTIFIED"}
VALID_CLASSIFICATIONS = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "PII"}


class CatalogService:

    @staticmethod
    def register_dataset(
        db_session: Session,
        dataset_name: str,
        domain: str,
        source_system: str,
        location: str,
        description: Optional[str] = None,
        format_type: str = "parquet",
        refresh_frequency: str = "DAILY",
        classification: str = "INTERNAL",
        owner_email: Optional[str] = None,
        steward_email: Optional[str] = None,
    ) -> Dataset:
        existing = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if existing:
            return existing

        owner_obj = db_session.query(DataOwner).filter_by(email=owner_email).first() if owner_email else None
        steward_obj = db_session.query(DataSteward).filter_by(email=steward_email).first() if steward_email else None

        dataset = Dataset(
            dataset_name=dataset_name,
            description=description or f"Enterprise dataset for {dataset_name}",
            domain=domain,
            source_system=source_system,
            location=location,
            format=format_type,
            refresh_frequency=refresh_frequency,
            classification=classification.upper() if classification.upper() in VALID_CLASSIFICATIONS else "INTERNAL",
            owner_id=owner_obj.id if owner_obj else None,
            steward_id=steward_obj.id if steward_obj else None,
            certification_status="UNCERTIFIED",
        )
        db_session.add(dataset)
        db_session.commit()
        db_session.refresh(dataset)
        logger.info(f"Registered dataset '{dataset_name}' in domain '{domain}'.")
        return dataset

    @staticmethod
    def search_catalog(
        db_session: Session,
        query_text: Optional[str] = None,
        domain: Optional[str] = None,
        classification: Optional[str] = None,
        certification_status: Optional[str] = None,
        min_quality_score: Optional[float] = None,
    ) -> List[Dataset]:
        query = db_session.query(Dataset)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.filter(
                or_(
                    Dataset.dataset_name.ilike(search_pattern),
                    Dataset.description.ilike(search_pattern),
                    Dataset.domain.ilike(search_pattern),
                    Dataset.source_system.ilike(search_pattern),
                )
            )

        if domain:
            query = query.filter(Dataset.domain.ilike(domain))

        if classification:
            query = query.filter(Dataset.classification == classification.upper())

        if certification_status:
            query = query.filter(Dataset.certification_status == certification_status.upper())

        if min_quality_score is not None:
            query = query.filter(Dataset.quality_score >= min_quality_score)

        return query.order_by(Dataset.quality_score.desc()).all()

    @staticmethod
    def get_dataset_details(db_session: Session, dataset_id_or_name: str) -> Optional[Dict[str, Any]]:
        dataset = (
            db_session.query(Dataset)
            .filter(or_(Dataset.id == dataset_id_or_name, Dataset.dataset_name == dataset_id_or_name))
            .first()
        )
        if not dataset:
            return None

        columns = db_session.query(DatasetColumn).filter_by(dataset_id=dataset.id).all()
        latest_profile = (
            db_session.query(DatasetProfile)
            .filter_by(dataset_id=dataset.id)
            .order_by(DatasetProfile.created_at.desc())
            .first()
        )

        return {
            "dataset_id": dataset.id,
            "dataset_name": dataset.dataset_name,
            "description": dataset.description,
            "domain": dataset.domain,
            "source_system": dataset.source_system,
            "location": dataset.location,
            "format": dataset.format,
            "size_bytes": dataset.size_bytes,
            "row_count": dataset.row_count,
            "refresh_frequency": dataset.refresh_frequency,
            "classification": dataset.classification,
            "quality_score": dataset.quality_score,
            "certification_status": dataset.certification_status,
            "owner": dataset.owner.name if dataset.owner else None,
            "steward": dataset.steward.name if dataset.steward else None,
            "last_updated": dataset.updated_at.isoformat() if dataset.updated_at else None,
            "columns": [
                {
                    "column_name": c.column_name,
                    "data_type": c.data_type,
                    "is_nullable": c.is_nullable,
                    "classification": c.classification,
                    "is_masked": c.is_masked,
                }
                for c in columns
            ],
            "latest_profile": {
                "row_count": latest_profile.row_count,
                "column_count": latest_profile.column_count,
                "null_percentages": latest_profile.null_percentages,
                "column_statistics": latest_profile.column_statistics,
            }
            if latest_profile
            else None,
        }

    @staticmethod
    def update_certification_status(db_session: Session, dataset_id: str, new_status: str) -> Dataset:
        target = new_status.upper()
        if target not in VALID_CERTIFICATION_STATUSES:
            raise ValueError(f"Invalid certification status '{new_status}'. Must be one of {VALID_CERTIFICATION_STATUSES}")

        dataset = db_session.query(Dataset).filter_by(id=dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        dataset.certification_status = target
        db_session.commit()
        db_session.refresh(dataset)
        logger.info(f"Updated dataset '{dataset.dataset_name}' certification status to '{target}'.")
        return dataset
