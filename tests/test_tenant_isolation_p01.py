"""Regresiones P0.1 para contexto y persistencia tenant-scoped de sellos."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.auth.tenant_context import get_tenant, reset_tenant, set_tenant
from core.auth.tenant_model import Tenant
from core.integration.audit_db_models import AuditSealRecord
from core.integration.phase5_bridge import SnapshotBridge
from core.snapshot_engine import SnapshotEngine
from database import Base
from core.auth.tenant_db_models import TenantRecord


@pytest.fixture
def audit_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield Session
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def make_bridge(session_factory):
    bridge = SnapshotBridge.__new__(SnapshotBridge)
    bridge._enabled = True
    bridge._engine = SnapshotEngine()
    bridge._session_factory = session_factory
    bridge._record_model = AuditSealRecord
    return bridge


def test_tenant_context_restores_previous_value():
    original = set_tenant(Tenant(tenant_id="tenant-original"))
    try:
        request_token = set_tenant(Tenant(tenant_id="tenant-request"))
        try:
            assert get_tenant().tenant_id == "tenant-request"
        finally:
            reset_tenant(request_token)
        assert get_tenant().tenant_id == "tenant-original"
    finally:
        reset_tenant(original)


def test_audit_seal_survives_bridge_recreation_and_is_tenant_scoped(audit_db):
    bridge = make_bridge(audit_db)
    response = {
        "omega_score": 72.5,
        "total_exposure_mxn": 15000,
        "nivel": "MEDIO",
        "executive_summary": "Diagnostico de prueba",
    }

    seal = bridge.seal(response, "tenant-a", "trace-a")
    assert seal is not None
    assert seal["algorithm"] == "SHA-256"

    # Nueva instancia: no comparte estado en memoria con la instancia que selló.
    restarted_bridge = make_bridge(audit_db)
    assert restarted_bridge.get_by_trace("trace-a", "tenant-a")["state_hash"] == seal["state_hash"]
    assert restarted_bridge.get_by_trace("trace-a", "tenant-b") is None
    assert restarted_bridge.get_by_trace("unknown", "tenant-a") is None
    assert len(restarted_bridge.history("tenant-a")) == 1
    assert restarted_bridge.history("tenant-b") == []

    assert restarted_bridge.verify("trace-a", response, "tenant-a")["verified"] is True
    assert restarted_bridge.verify("trace-a", response, "tenant-b") == {
        "verified": False,
        "reason": "SELLO_NO_ENCONTRADO",
    }

    tampered_response = {**response, "omega_score": 99.9}
    assert restarted_bridge.verify("trace-a", tampered_response, "tenant-a")["verified"] is False

    # Un trace duplicado no reemplaza ni altera el sello original.
    assert restarted_bridge.seal(tampered_response, "tenant-a", "trace-a") is None
    persisted = restarted_bridge.get_by_trace("trace-a", "tenant-a")
    assert persisted["state_hash"] == seal["state_hash"]