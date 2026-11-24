"""Política de rutas: API privada requiere JWT; excepciones legacy son explícitas."""
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
