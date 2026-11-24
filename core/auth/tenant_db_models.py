"""Persistencia de identidad y membresías para aislamiento multiempresa P0.1.

Se mantiene separada de Tenant (dataclass de contexto) para no alterar
interfaces existentes. Todas las tablas comparten database.Base.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.sql import func

from database import Base


class TenantRecord(Base):
    __tablename__ = "mesan_tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UserRecord(Base):
    __tablename__ = "mesan_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(320), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TenantMembership(Base):
    __tablename__ = "mesan_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_mesan_membership_tenant_user"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(
        String(36), ForeignKey("mesan_tenants.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    user_id = Column(
        String(36), ForeignKey("mesan_users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role = Column(String(30), nullable=False, default="member")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
