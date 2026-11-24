from contextvars import ContextVar, Token
from typing import Optional
from core.auth.tenant_model import Tenant

_current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)

def set_tenant(tenant: Tenant) -> Token:
    """Set tenant context and return the token needed to restore prior context."""
    return _current_tenant.set(tenant)

def reset_tenant(token: Token) -> None:
    _current_tenant.reset(token)

def get_tenant() -> Optional[Tenant]:
    return _current_tenant.get()

def clear_tenant() -> None:
    """Legacy compatibility; request middleware should use reset_tenant(token)."""
    _current_tenant.set(None)

class TenantContextError(RuntimeError):
    pass

def require_tenant() -> Tenant:
    tenant = _current_tenant.get()
    if tenant is None:
        raise TenantContextError("TENANT_CONTEXT_MISSING")
    return tenant
