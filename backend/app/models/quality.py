from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class QualityRule(Base, BaseModelMixin):
    __tablename__ = "quality_rules"

    rule_id = Column(String(100), unique=True, nullable=False, index=True) # DQ-001
    rule_name = Column(String(255), nullable=False)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=True)
    rule_type = Column(String(50), nullable=False, index=True) # NOT_NULL, UNIQUE, VALID_FORMAT, REGEX, RANGE, etc.
    rule_expression = Column(Text, nullable=True) # > 0, regex pattern, list of values
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    category = Column(String(50), default="TECHNICAL") # TECHNICAL vs BUSINESS
    owner = Column(String(255), nullable=True)
    enabled = Column(Boolean, default=True)

    dataset = relationship("Dataset", back_populates="quality_rules")
    results = relationship("QualityResult", back_populates="rule", cascade="all, delete-orphan")
    issues = relationship("QualityIssue", back_populates="rule", cascade="all, delete-orphan")


class QualityResult(Base, BaseModelMixin):
    __tablename__ = "quality_results"

    rule_id = Column(String(36), ForeignKey("quality_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    passed = Column(Boolean, nullable=False)
    total_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    pass_rate = Column(Float, default=100.0)
    execution_time_ms = Column(Float, default=0.0)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now)
    details = Column(JSON, nullable=True)

    rule = relationship("QualityRule", back_populates="results")


class QualityIssue(Base, BaseModelMixin):
    __tablename__ = "quality_issues"

    issue_id = Column(String(100), unique=True, nullable=False, index=True) # ISS-001
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    column_name = Column(String(255), nullable=True)
    rule_id = Column(String(36), ForeignKey("quality_rules.id", ondelete="CASCADE"), nullable=True)
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN", index=True) # OPEN, IN_PROGRESS, RESOLVED, IGNORED, REOPENED
    owner = Column(String(255), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), default=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    dataset = relationship("Dataset", back_populates="quality_issues")
    rule = relationship("QualityRule", back_populates="issues")
    remediations = relationship("RemediationAction", back_populates="issue")


class RemediationAction(Base, BaseModelMixin):
    __tablename__ = "remediation_actions"

    issue_id = Column(String(36), ForeignKey("quality_issues.id", ondelete="CASCADE"), nullable=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(255), nullable=True)
    action_type = Column(String(100), nullable=False) # TRIM_WHITESPACE, CASE_NORMALIZE, PHONE_NORMALIZE, DEDUPLICATE
    affected_rows = Column(Integer, default=0)
    executed_by = Column(String(255), default="AUTOMATED_ENGINE")
    details = Column(JSON, nullable=True)

    issue = relationship("QualityIssue", back_populates="remediations")
