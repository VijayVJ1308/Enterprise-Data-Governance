from sqlalchemy import Column, String, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import BaseModelMixin


class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)


class User(Base, BaseModelMixin):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")


class Role(Base, BaseModelMixin):
    __tablename__ = "roles"

    name = Column(String(50), unique=True, nullable=False, index=True) # ADMIN, DATA_ENGINEER, etc.
    description = Column(String(255), nullable=True)

    users = relationship("User", secondary="user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")


class Permission(Base, BaseModelMixin):
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False) # datasets, rules, issues, etc.
    action = Column(String(50), nullable=False)   # create, read, update, delete

    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
