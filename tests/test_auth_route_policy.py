"""Pruebas de política de roles y rutas de autenticación P0.1."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

from core.auth.authorization import platform_permission_is_allowed, role_is_allowed
from core.auth.auth_middleware import _is_public, _requires_platform_operator


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


def test_internal_get_routes_are_not_mistaken_for_static_assets():
    protected = [
        "/jarvis/dashboard",
        "/guardian/dashboard",
        "/commercial/dashboard",
        "/commercial/mission-control",
        "/billing/status",
        "/jarvis-sales/leads",
        "/jarvis-sales/dashboard",
        "/market/events",
        "/market/regulatory/alerts/tenant-123",
    ]
    for path in protected:
        assert not _is_public(path, "GET"), path
    assert _is_public("/mantenimiento", "GET")


def test_intended_public_flows_remain_public():
    assert _is_public("/auth/bootstrap", "POST")
    assert _is_public("/auth/login", "POST")
    assert _is_public("/api/leads", "POST")
    assert _is_public("/api/chat/jarvis/lead", "POST")
    assert _is_public("/api/chat/jarvis/lead-fallback", "GET")
    assert _is_public("/execute", "POST")
    assert _is_public("/billing/checkout", "POST")
    assert _is_public("/diagnostico-exitoso", "GET")
    assert _is_public("/demo", "GET")


def test_role_policy_is_explicit_and_fail_closed():
    assert role_is_allowed("owner", {"owner", "admin"})
    assert role_is_allowed("admin", {"owner", "admin"})
    assert not role_is_allowed("member", {"owner", "admin"})
    assert role_is_allowed("member", {"member", "admin", "owner"})
    assert not role_is_allowed(None, {"owner", "admin"})
    assert not role_is_allowed("superuser", {"owner", "admin", "superuser"})



def test_platform_only_routes_are_separated_from_tenant_routes():
    for path in ("/jarvis/kpis", "/jarvis-sales/leads", "/guardian/incidents", "/system/mode", "/smtp/send", "/market/events", "/commercial/shadow/activate", "/commercial/mission-control/data", "/commercial/dashboard", "/guardian/backups", "/system/cleanup"):
        assert _requires_platform_operator(path), path
    for path in ("/jarvis/briefing", "/market/regulatory/alerts/tenant-123", "/customer"):
        assert not _requires_platform_operator(path), path


def test_platform_login_is_an_explicit_public_flow():
    assert _is_public("/auth/platform/login", "POST")
    assert not _is_public("/auth/platform/login", "GET")



def test_platform_permissions_separate_reads_from_mutations():
    assert platform_permission_is_allowed(["platform:read"], "GET")
    assert platform_permission_is_allowed(["platform:read"], "HEAD")
    assert not platform_permission_is_allowed(["platform:read"], "POST")
    assert platform_permission_is_allowed(["platform:operate"], "POST")
    assert not platform_permission_is_allowed(["platform:operate"], "GET")
    assert platform_permission_is_allowed(["platform:admin"], "DELETE")
    assert not platform_permission_is_allowed(None, "GET")
    assert not platform_permission_is_allowed(["platform:unknown"], "GET")
    assert not platform_permission_is_allowed("platform:admin", "POST")
