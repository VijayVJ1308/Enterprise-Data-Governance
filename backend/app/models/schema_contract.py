from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class SchemaVersion(Base, BaseModelMixin):
    __tablename__ = "schema_versions"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    schema_hash = Column(String(64), nullable=False)
    columns_spec = Column(JSON, nullable=False) # list of column definitions

    dataset = relationship("Dataset", back_populates="schema_versions")


class SchemaDriftEvent(Base, BaseModelMixin):
    __tablename__ = "schema_drift_events"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    drift_type = Column(String(50), nullable=False) # ADDED, REMOVED, TYPE_CHANGED, NULLABLE_CHANGED
    previous_value = Column(String(255), nullable=True)
    current_value = Column(String(255), nullable=True)
    severity = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    detected_at = Column(DateTime(timezone=True), default=utc_now)


class DataContract(Base, BaseModelMixin):
    __tablename__ = "data_contracts"

    contract_name = Column(String(255), unique=True, nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(20), default="1.0.0")
    yaml_spec = Column(Text, nullable=False)
    status = Column(String(30), default="ACTIVE") # ACTIVE, INACTIVE, DRAFT

    dataset = relationship("Dataset", back_populates="contracts")
    violations = relationship("DataContractViolation", back_populates="contract", cascade="all, delete-orphan")


class DataContractViolation(Base, BaseModelMixin):
    __tablename__ = "data_contract_violations"

    contract_id = Column(String(36), ForeignKey("data_contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    violation_type = Column(String(50), nullable=False) # SCHEMA_MISMATCH, QUALITY_SLA_BREACH, FRESHNESS_SLA_BREACH
    details = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utc_now)

    contract = relationship("DataContract", back_populates="violations")
