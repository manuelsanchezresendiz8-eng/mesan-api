"""Regresiones unitarias P0.1 para contexto y propiedad de sellos."""
from core.auth.tenant_context import get_tenant, reset_tenant, set_tenant
from core.auth.tenant_model import Tenant
from core.integration.phase5_bridge import SnapshotBridge


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


def test_audit_seal_lookup_requires_matching_tenant():
    bridge = SnapshotBridge.__new__(SnapshotBridge)
    bridge._enabled = True
    bridge._engine = object()
    bridge._trace_index = {
        "trace-a": {"trace_id": "trace-a", "tenant_id": "tenant-a", "state_hash": "abc"}
    }

    assert bridge.get_by_trace("trace-a", "tenant-a")["tenant_id"] == "tenant-a"
    assert bridge.get_by_trace("trace-a", "tenant-b") is None
    assert bridge.get_by_trace("unknown", "tenant-a") is None
