from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin


class LineageNode(Base, BaseModelMixin):
    __tablename__ = "lineage_nodes"

    node_key = Column(String(255), unique=True, nullable=False, index=True) # dataset:customers_raw, column:email
    name = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False) # DATASET, COLUMN, PIPELINE, DASHBOARD, REPORT
    domain = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    outgoing_edges = relationship("LineageEdge", foreign_keys="LineageEdge.source_node_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("LineageEdge", foreign_keys="LineageEdge.target_node_id", back_populates="target_node", cascade="all, delete-orphan")


class LineageEdge(Base, BaseModelMixin):
    __tablename__ = "lineage_edges"

    source_node_id = Column(String(36), ForeignKey("lineage_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(String(36), ForeignKey("lineage_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    transformation_type = Column(String(100), default="DIRECT_TRANSFORM") # DIRECT_TRANSFORM, AGGREGATION, FILTER, JOIN
    pipeline_name = Column(String(255), nullable=True)

    source_node = relationship("LineageNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("LineageNode", foreign_keys=[target_node_id], back_populates="incoming_edges")


class GlossaryTerm(Base, BaseModelMixin):
    __tablename__ = "glossary_terms"

    term = Column(String(255), unique=True, nullable=False, index=True)
    definition = Column(Text, nullable=False)
    business_domain = Column(String(100), nullable=False, index=True)
    owner = Column(String(255), nullable=True)
    status = Column(String(30), default="APPROVED") # DRAFT, APPROVED, DEPRECATED
    related_datasets = Column(JSON, nullable=True) # list of dataset names or IDs
