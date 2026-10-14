from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class Alert(Base, BaseModelMixin):
    __tablename__ = "alerts"

    alert_type = Column(String(100), nullable=False, index=True) # QUALITY_FAILURE, SCHEMA_DRIFT, SLA_BREACH
    severity = Column(String(20), default="MEDIUM", index=True) # LOW, MEDIUM, HIGH, CRITICAL
    dataset_name = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(30), default="UNACKNOWLEDGED", index=True) # UNACKNOWLEDGED, ACKNOWLEDGED, RESOLVED
    triggered_at = Column(DateTime(timezone=True), default=utc_now)
    details = Column(JSON, nullable=True)


class AuditLog(Base, BaseModelMixin):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False, index=True) # QUALITY_RULE_CREATED, SENSITIVE_DATA_ACCESSED, etc.
    resource = Column(String(255), nullable=False) # datasets/customers, rules/DQ-001
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)
    request_id = Column(String(64), nullable=True)
    result = Column(String(50), default="SUCCESS") # SUCCESS, FAILURE, DENIED
    details = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_logs")
