# models/database.py -- MESAN Omega Enterprise Event Store v2.0
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Index, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

Base = declarative_base()

class EnterpriseEvent(Base):
    __tablename__ = "enterprise_events"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    event_id       = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True)
    tenant_id      = Column(String(128), nullable=False, index=True)
    trace_id       = Column(String(128), nullable=False, index=True)
    correlation_id = Column(String(128), nullable=True, index=True)
    engine_type        = Column(String(128), nullable=False, index=True)
    engine_version     = Column(String(32),  nullable=False)
    regulatory_version = Column(String(64),  nullable=False)
    event_type     = Column(String(128), nullable=False, index=True)
    severity       = Column(String(32),  default="INFO", nullable=False, index=True)
    input_payload  = Column(JSON, nullable=True)
    output_result  = Column(JSON, nullable=True)
    metadata_      = Column("metadata", JSON, nullable=True)
    execution_time_ms  = Column(Integer, default=0)
    system_confidence  = Column(String(32), nullable=True)
    success        = Column(Boolean, default=True, nullable=False)
    error_message  = Column(Text, nullable=True)
    retry_count    = Column(Integer, default=0)
    deleted        = Column(Boolean, default=False, nullable=False, index=True)
    created_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_tenant_trace",  "tenant_id", "trace_id"),
        Index("idx_engine_event",  "engine_type", "event_type"),
        Index("idx_created_at",    "created_at"),
    )
