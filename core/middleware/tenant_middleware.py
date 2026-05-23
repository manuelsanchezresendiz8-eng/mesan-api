# core/middleware/tenant_middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict
from core.auth.tenant_model import Tenant
from core.auth.tenant_context import set_tenant, clear_tenant

TENANT_DB: Dict[str, Tenant] = {
    "tenant_1": Tenant(tenant_id="tenant_1", name="Empresa A", plan="PRO"),
    "tenant_2": Tenant(tenant_id="tenant_2", name="Empresa B", plan="ENTERPRISE"),
}

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            clear_tenant()
            tenant_id = request.headers.get("X-Tenant-ID")
            if not tenant_id:
                raise HTTPException(status_code=400, detail="TENANT_ID_REQUIRED")
            tenant = TENANT_DB.get(tenant_id)
            if not tenant or not tenant.active:
                raise HTTPException(status_code=403, detail="TENANT_INVALID_OR_INACTIVE")
            set_tenant(tenant)
            return await call_next(request)
        finally:
            clear_tenant()
