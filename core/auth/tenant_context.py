# core/auth/tenant_context.py
from contextvars import ContextVar
from typing import Optional
from core.auth.tenant_model import Tenant

_current_tenant: ContextVar[Optional[Tenant]] = ContextVar("current_tenant", default=None)

def set_tenant(tenant: Tenant) -> None: _current_tenant.set(tenant)
def get_tenant() -> Optional[Tenant]: return _current_tenant.get()
def clear_tenant() -> None: _current_tenant.set(None)

class TenantContextError(RuntimeError):
    """Error critico: contexto de tenant no inicializado."""
    pass

def require_tenant() -> Tenant:
    tenant = _current_tenant.get()
    if tenant is None: raise TenantContextError("TENANT_CONTEXT_MISSING")
    return tenant
