from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin, utc_now


class GovernancePolicy(Base, BaseModelMixin):
    __tablename__ = "governance_policies"

    policy_code = Column(String(50), unique=True, nullable=False, index=True) # POL-001
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False) # ACCESS, OWNERSHIP, QUALITY, SLA
    severity = Column(String(20), default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    enabled = Column(Boolean, default=True)
    owner = Column(String(255), nullable=True)

    violations = relationship("PolicyViolation", back_populates="policy", cascade="all, delete-orphan")


class PolicyViolation(Base, BaseModelMixin):
    __tablename__ = "policy_violations"

    policy_id = Column(String(36), ForeignKey("governance_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="OPEN") # OPEN, RESOLVED, EXEMPTED
    detected_at = Column(DateTime(timezone=True), default=utc_now)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    policy = relationship("GovernancePolicy", back_populates="violations")


class ComplianceFramework(Base, BaseModelMixin):
    __tablename__ = "compliance_frameworks"

    framework_code = Column(String(50), unique=True, nullable=False, index=True) # GDPR, HIPAA, SOC2, ISO27001
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    controls = relationship("ComplianceControl", back_populates="framework", cascade="all, delete-orphan")


class ComplianceControl(Base, BaseModelMixin):
    __tablename__ = "compliance_controls"

    framework_id = Column(String(36), ForeignKey("compliance_frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    control_code = Column(String(50), nullable=False, index=True) # CC1.1, Art32, 164.312
    description = Column(Text, nullable=False)
    owner = Column(String(255), nullable=True)
    status = Column(String(30), default="PASS") # PASS, FAIL, IN_PROGRESS, NOT_APPLICABLE
    evidence_summary = Column(Text, nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), default=utc_now)

    framework = relationship("ComplianceFramework", back_populates="controls")
