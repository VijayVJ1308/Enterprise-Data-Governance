import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.lineage import GlossaryTerm
from backend.app.models.catalog import Dataset

logger = logging.getLogger("GlossaryService")

VALID_GLOSSARY_STATUSES = {"DRAFT", "APPROVED", "DEPRECATED"}


class GlossaryService:

    @staticmethod
    def create_term(
        db_session: Session,
        term: str,
        definition: str,
        business_domain: str,
        owner: Optional[str] = None,
        status: str = "APPROVED",
        related_datasets: Optional[List[str]] = None,
    ) -> GlossaryTerm:
        target_status = status.upper()
        if target_status not in VALID_GLOSSARY_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_GLOSSARY_STATUSES}")

        existing = db_session.query(GlossaryTerm).filter_by(term=term).first()
        if existing:
            return existing

        glossary_item = GlossaryTerm(
            term=term,
            definition=definition,
            business_domain=business_domain,
            owner=owner,
            status=target_status,
            related_datasets=related_datasets or [],
        )
        db_session.add(glossary_item)
        db_session.commit()
        db_session.refresh(glossary_item)
        logger.info(f"Created Glossary Term '{term}' in domain '{business_domain}'.")
        return glossary_item

    @staticmethod
    def update_term(
        db_session: Session,
        term_id_or_name: str,
        definition: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        business_domain: Optional[str] = None,
    ) -> GlossaryTerm:
        term_item = (
            db_session.query(GlossaryTerm)
            .filter(or_(GlossaryTerm.id == term_id_or_name, GlossaryTerm.term == term_id_or_name))
            .first()
        )
        if not term_item:
            raise ValueError(f"Glossary term '{term_id_or_name}' not found.")

        if definition:
            term_item.definition = definition
        if owner:
            term_item.owner = owner
        if business_domain:
            term_item.business_domain = business_domain
        if status:
            st_upper = status.upper()
            if st_upper not in VALID_GLOSSARY_STATUSES:
                raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_GLOSSARY_STATUSES}")
            term_item.status = st_upper

        db_session.commit()
        db_session.refresh(term_item)
        logger.info(f"Updated Glossary Term '{term_item.term}'.")
        return term_item

    @staticmethod
    def link_dataset_to_term(db_session: Session, term_id_or_name: str, dataset_name: str) -> GlossaryTerm:
        term_item = (
            db_session.query(GlossaryTerm)
            .filter(or_(GlossaryTerm.id == term_id_or_name, GlossaryTerm.term == term_id_or_name))
            .first()
        )
        if not term_item:
            raise ValueError(f"Glossary term '{term_id_or_name}' not found.")

        dataset = db_session.query(Dataset).filter_by(dataset_name=dataset_name).first()
        if not dataset:
            logger.warning(f"Dataset '{dataset_name}' not found in catalog, linking by name.")

        related = list(term_item.related_datasets or [])
        if dataset_name not in related:
            related.append(dataset_name)
            term_item.related_datasets = related
            db_session.commit()
            db_session.refresh(term_item)
            logger.info(f"Linked dataset '{dataset_name}' to glossary term '{term_item.term}'.")
        return term_item

    @staticmethod
    def search_terms(
        db_session: Session,
        query_text: Optional[str] = None,
        business_domain: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[GlossaryTerm]:
        query = db_session.query(GlossaryTerm)

        if query_text:
            pattern = f"%{query_text}%"
            query = query.filter(
                or_(
                    GlossaryTerm.term.ilike(pattern),
                    GlossaryTerm.definition.ilike(pattern),
                    GlossaryTerm.business_domain.ilike(pattern),
                )
            )

        if business_domain:
            query = query.filter(GlossaryTerm.business_domain.ilike(business_domain))

        if status:
            query = query.filter(GlossaryTerm.status == status.upper())

        return query.order_by(GlossaryTerm.term.asc()).all()
