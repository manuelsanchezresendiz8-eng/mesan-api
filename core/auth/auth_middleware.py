# core/auth/auth_middleware.py -- MESAN Omega Auth Middleware v1.4
"""
FastAPI Auth Middleware Ω

Valida JWT en cada request entrante.
Inyecta tenant context en el pipeline.
Limpia contexto en todos los caminos de ejecución.

Exentas de JWT: health/metadata públicos, captura pública de leads,
diagnóstico público y las rutas legacy del CRM protegidas por Basic Auth.
Las operaciones administrativas y los endpoints internos requieren JWT.

ESTRATEGIA:
    Las rutas CRM legacy conservan Basic Auth mediante
    Depends(verify_crm_credentials). No eliminar esa protección.
"""
import logging
import re
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from core.auth.jwt_handler import JWTError, verify_token
from core.auth.tenant_context import reset_tenant, set_tenant
from core.auth.tenant_model import Tenant
from database import SessionLocal
from core.auth.tenant_db_models import TenantMembership, TenantRecord, UserRecord
from core.context import RequestContext

logger = logging.getLogger("mesan.auth")

PUBLIC_PATHS = {
    "/health",
    "/ready",
    "/engines",
    "/diagnostics",
    "/features",
    "/docs",
    "/openapi.json",
}

# Las rutas CRM legacy están exentas de JWT, pero NO son públicas:
# su única protección es Depends(verify_crm_credentials) en el endpoint.
# Mantener aquí solo flujos realmente públicos.
PUBLIC_METHOD_PATHS = {
    ("/auth/bootstrap", "POST"),
    ("/auth/login", "POST"),
    ("/api/leads", "POST"),
    ("/api/leads", "GET"),
    ("/crm_enterprise.html", "GET"),
    # Diagnóstico público desde landing; limitado por IP y validación de payload.
    ("/execute", "POST"),
    # Checkout y confirmación del flujo público de diagnóstico.
    ("/billing/checkout", "POST"),
    ("/diagnostico-exitoso", "GET"),
    # Captura pública del formulario conversacional JARVIS.
    ("/api/chat/jarvis/lead", "POST"),
    ("/api/chat/jarvis/lead-fallback", "GET"),
    # Vistas de demostración con datos de demo, no de clientes.
    ("/demo", "GET"),
    ("/demo/diagnostico", "GET"),
    ("/demo/guardian", "GET"),
}

_LEAD_ID_PATH_RE = re.compile(r"^/api/leads/[^/]+$")


def _is_lead_id_path_exempt(path: str, method: str) -> bool:
    return method.upper() in ("GET", "PATCH") and bool(_LEAD_ID_PATH_RE.match(path))


def _is_static_landing_asset(path: str, method: str) -> bool:
    if method.upper() != "GET":
        return False
    if path == "/crm_enterprise.html":
        return False
    # Rutas de ejecución son API aunque no usen el prefijo /api.
    # En particular, /execute/audit/{trace_id} debe exigir JWT y membresía.
    if path.startswith((
        "/api/", "/pro/", "/api/v1/", "/execute/",
        "/auth/", "/commercial/", "/jarvis/", "/guardian/",
        "/system/", "/smtp/", "/billing/", "/tenant/",
        "/omega/", "/customer", "/market/", "/jarvis-sales/",
    )):
        return False
    return True


def _is_public(path: str, method: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    if (path, method.upper()) in PUBLIC_METHOD_PATHS:
        return True
    if _is_lead_id_path_exempt(path, method):
        return True
    if _is_static_landing_asset(path, method):
        return True
    return False


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    parts = auth_header.split(" ")
    if len(parts) != 2:
        return None
    return parts[1]


async def auth_middleware(request: Request, call_next):
    # CVE-2026-48710: scope["path"] es inmune a manipulacion via Host header
    path = request.scope.get("path", request.url.path)
    method = request.method

    if _is_public(path, method):
        return await call_next(request)

    token = _extract_token(request)
    if not token:
        logger.warning("[AUTH] Token faltante | path=%s method=%s", path, method)
        return JSONResponse(
            status_code=401,
            content={"error": "AUTH_TOKEN_MISSING", "path": path},
        )

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not user_id or not tenant_id:
            return JSONResponse(status_code=401, content={"error": "AUTH_IDENTITY_OR_TENANT_MISSING"})

        # tenant_id selecciona el espacio solicitado; la membresía activa en
        # PostgreSQL, no el claim ni X-Tenant-ID, concede el acceso.
        db = SessionLocal()
        try:
            membership = (
                db.query(TenantMembership)
                .join(UserRecord, UserRecord.id == TenantMembership.user_id)
                .join(TenantRecord, TenantRecord.id == TenantMembership.tenant_id)
                .filter(
                    TenantMembership.user_id == user_id,
                    TenantMembership.tenant_id == tenant_id,
                    TenantMembership.status == "active",
                    UserRecord.status == "active",
                    TenantRecord.status == "active",
                )
                .first()
            )
        finally:
            db.close()

        if membership is None:
            logger.warning("[AUTH] Membresía no válida | user=%s tenant=%s", user_id, tenant_id)
            return JSONResponse(status_code=403, content={"error": "TENANT_MEMBERSHIP_REQUIRED"})

        context_token = set_tenant(Tenant(tenant_id=tenant_id))
        previous_ctx = getattr(request.state, "ctx", None)
        if previous_ctx is not None:
            request.state.ctx = RequestContext(
                tenant_id=tenant_id,
                request_id=previous_ctx.request_id,
                user_id=user_id,
                role=membership.role,
                correlation_id=previous_ctx.correlation_id,
            )
        logger.info("[AUTH] OK | user=%s tenant=%s | path=%s", user_id, tenant_id, path)
        try:
            return await call_next(request)
        finally:
            reset_tenant(context_token)

    except JWTError as e:
        logger.warning("[AUTH] JWT ERROR | path=%s | error=%s", path, str(e))
        return JSONResponse(
            status_code=401,
            content={"error": str(e)},
        )

    except Exception:
        logger.exception("[AUTH] MIDDLEWARE FAILURE | path=%s", path)
        return JSONResponse(
            status_code=500,
            content={"error": "AUTH_MIDDLEWARE_FAILURE"},
        )
