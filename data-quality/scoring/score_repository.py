import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.catalog import Dataset, MetadataEntry
from data_quality.scoring.score_calculator import QualityScoreBreakdown

logger = logging.getLogger("ScoreRepository")


class ScoreRepository:

    @staticmethod
    def update_dataset_quality_score(db_session: Session, score_breakdown: QualityScoreBreakdown) -> Dataset:
        dataset_name = score_breakdown.dataset_name
        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()

        if not dataset:
            dataset = Dataset(
                dataset_name=dataset_name,
                description=f"Auto-registered dataset entry for {dataset_name}",
                domain="General",
                source_system="IngestionPlatform",
                location=f"data/lake/bronze/{dataset_name}",
            )
            db_session.add(dataset)
            db_session.flush()

        dataset.quality_score = score_breakdown.overall_quality_score

        # Persist detailed score dimension metadata entry
        meta_key = f"quality_score_dimensions_{dataset_name}"
        meta_entry = db_session.query(MetadataEntry).filter_by(key=meta_key).first()
        import json
        json_val = json.dumps(score_breakdown.dimension_scores)

        if meta_entry:
            meta_entry.value = json_val
        else:
            meta_entry = MetadataEntry(
                key=meta_key,
                value=json_val,
                category="quality",
                dataset_id=dataset.id,
            )
            db_session.add(meta_entry)

        db_session.commit()
        db_session.refresh(dataset)
        logger.info(f"Updated quality score for dataset '{dataset_name}': {score_breakdown.overall_quality_score}%.")
        return dataset
