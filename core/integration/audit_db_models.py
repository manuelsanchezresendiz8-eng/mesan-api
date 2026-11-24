"""SQLAlchemy model for immutable, tenant-scoped Phase 5 audit seals."""
import uuid

from sqlalchemy import Column, DateTime, Float, String, UniqueConstraint, Index
from sqlalchemy.sql import func

from database import Base


class AuditSealRecord(Base):
    __tablename__ = "mesan_audit_seals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trace_id", name="uq_mesan_audit_seal_tenant_trace"),
        Index("ix_mesan_audit_seals_tenant_time", "tenant_id", "sealed_at"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(128), nullable=False, index=True)
    trace_id = Column(String(128), nullable=False)
    snapshot_id = Column(String(36), nullable=False)
    sealed_at = Column(String(40), nullable=False)
    state_hash = Column(String(64), nullable=False)
    algorithm = Column(String(16), nullable=False, default="SHA-256")
    engine_version = Column(String(32), nullable=False)
    omega_score = Column(Float, nullable=False, default=0.0)
    risk_level = Column(String(20), nullable=False)
    exposure_total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
