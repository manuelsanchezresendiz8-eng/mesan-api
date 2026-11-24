"""Política de rutas: API privada requiere JWT; excepciones legacy son explícitas."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.auth.auth_middleware import _is_public


def test_tenant_lead_endpoints_are_not_public():
    assert not _is_public("/api/v1/tenant/leads", "GET")
    assert not _is_public("/api/v1/tenant/leads/lead-123", "GET")
    assert not _is_public("/api/v1/tenant/leads/lead-123", "PATCH")


def test_audit_trace_endpoint_is_not_public():
    assert not _is_public("/execute/audit/trace-123", "GET")


def test_legacy_crm_routes_keep_their_explicit_basic_auth_exemption():
    assert _is_public("/api/leads", "GET")
    assert _is_public("/api/leads/lead-123", "PATCH")


def test_admin_and_internal_operations_require_jwt():
    protected = [
        ("/commercial/shadow/activate", "POST"),
        ("/commercial/shadow/deactivate", "POST"),
        ("/commercial/shadow/run", "POST"),
        ("/commercial/shadow/status", "GET"),
        ("/smtp/send", "POST"),
        ("/smtp/welcome", "POST"),
        ("/smtp/proposal", "POST"),
        ("/smtp/status", "GET"),
        ("/jarvis/warroom", "GET"),
        ("/jarvis/kpis", "GET"),
        ("/jarvis/briefing", "POST"),
        ("/commercial/mission-control", "GET"),
        ("/guardian/incidents", "GET"),
        ("/guardian/security", "GET"),
        ("/guardian/predictive", "GET"),
        ("/system/mode", "GET"),
    ]
    for path, method in protected:
        assert not _is_public(path, method), (path, method)


def test_intended_public_flows_remain_public():
    assert _is_public("/auth/bootstrap", "POST")
    assert _is_public("/auth/login", "POST")
    assert _is_public("/api/leads", "POST")
    assert _is_public("/execute", "POST")
def test_internal_get_routes_are_not_mistaken_for_static_assets():
    protected = [
        "/jarvis/dashboard",
        "/guardian/dashboard",
        "/commercial/dashboard",
        "/commercial/mission-control",
        "/billing/status",
    ]
    for path in protected:
        assert not _is_public(path, "GET"), path
    assert _is_public("/mantenimiento", "GET")
