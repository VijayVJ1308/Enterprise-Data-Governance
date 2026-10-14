from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin


class DataOwner(Base, BaseModelMixin):
    __tablename__ = "data_owners"

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)

    datasets = relationship("Dataset", back_populates="owner")


class DataSteward(Base, BaseModelMixin):
    __tablename__ = "data_stewards"

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=True)

    datasets = relationship("Dataset", back_populates="steward")


class Dataset(Base, BaseModelMixin):
    __tablename__ = "datasets"

    dataset_name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    domain = Column(String(100), nullable=False, index=True) # Sales, HR, Finance, Supply Chain
    source_system = Column(String(100), nullable=False) # CRM, ERP, API
    location = Column(String(500), nullable=False) # minio://bronze/customers
    format = Column(String(50), nullable=False, default="parquet") # parquet, csv, json, postgres
    size_bytes = Column(Integer, default=0)
    row_count = Column(Integer, default=0)
    refresh_frequency = Column(String(50), default="DAILY") # HOURLY, DAILY, WEEKLY
    classification = Column(String(50), default="INTERNAL", index=True) # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, PII
    quality_score = Column(Float, default=100.0)
    certification_status = Column(String(50), default="UNCERTIFIED") # DRAFT, PENDING, CERTIFIED

    owner_id = Column(String(36), ForeignKey("data_owners.id"), nullable=True)
    steward_id = Column(String(36), ForeignKey("data_stewards.id"), nullable=True)

    owner = relationship("DataOwner", back_populates="datasets")
    steward = relationship("DataSteward", back_populates="datasets")

    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")
    profiles = relationship("DatasetProfile", back_populates="dataset", cascade="all, delete-orphan")
    quality_rules = relationship("QualityRule", back_populates="dataset", cascade="all, delete-orphan")
    quality_issues = relationship("QualityIssue", back_populates="dataset", cascade="all, delete-orphan")
    schema_versions = relationship("SchemaVersion", back_populates="dataset", cascade="all, delete-orphan")
    contracts = relationship("DataContract", back_populates="dataset", cascade="all, delete-orphan")


class DatasetColumn(Base, BaseModelMixin):
    __tablename__ = "dataset_columns"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    classification = Column(String(50), default="INTERNAL")
    is_masked = Column(Boolean, default=False)
    description = Column(Text, nullable=True)

    dataset = relationship("Dataset", back_populates="columns")


class DatasetProfile(Base, BaseModelMixin):
    __tablename__ = "dataset_profiles"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    null_counts = Column(JSON, nullable=True)
    null_percentages = Column(JSON, nullable=True)
    unique_counts = Column(JSON, nullable=True)
    uniqueness_percentages = Column(JSON, nullable=True)
    column_statistics = Column(JSON, nullable=True) # min, max, mean, median, stddev, percentiles

    dataset = relationship("Dataset", back_populates="profiles")


class MetadataEntry(Base, BaseModelMixin):
    __tablename__ = "metadata"

    key = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    category = Column(String(100), nullable=False) # system, dataset, governance
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True)
