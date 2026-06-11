# core/auth/auth_middleware.py -- MESAN Omega Auth Middleware v1.0
"""
FastAPI Auth Middleware Ω

Valida JWT en cada request entrante.
Inyecta tenant context en el pipeline.
Limpia contexto en todos los caminos de ejecución.

Rutas públicas (no requieren auth):
    GET  /health
    GET  /ready
    GET  /engines
    GET  /diagnostics
    GET  /features
    POST /api/leads (configurable)
"""

import logging
import os
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.auth.jwt_handler import JWTError, verify_token
from core.auth.tenant_context import clear_tenant, set_tenant
from core.auth.tenant_model import Tenant

logger = logging.getLogger("mesan.auth")

# ── Rutas públicas — no requieren token ──────────────────────────────────────
PUBLIC_PATHS = {
    "/health",
    "/ready",
    "/engines",
    "/diagnostics",
    "/features",
    "/docs",
    "/openapi.json",
}

PUBLIC_PREFIXES = (
    "/api/leads",
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
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
    """
    FastAPI-compatible auth middleware.

    Flujo:
        1. Rutas públicas → pass-through sin validar token
        2. Extraer Bearer token del header Authorization
        3. Verificar JWT con jwt_handler
        4. Inyectar Tenant en context
        5. Ejecutar request
        6. Limpiar context en TODOS los caminos (éxito, error, excepción)
    """
    path = request.url.path

    # ── Rutas públicas ────────────────────────────────────────────────────
    if _is_public(path):
        return await call_next(request)

    # ── Extraer token ─────────────────────────────────────────────────────
    token = _extract_token(request)
    if not token:
        logger.warning("[AUTH] Token faltante | path=%s", path)
        return JSONResponse(
            status_code=401,
            content={"error": "AUTH_TOKEN_MISSING", "path": path},
        )

    # ── Verificar JWT e inyectar tenant ───────────────────────────────────
    try:
        payload = verify_token(token)
        tenant_id = payload.get("tenant_id")

        if not tenant_id:
            logger.warning("[AUTH] Token sin tenant_id | path=%s", path)
            return JSONResponse(
                status_code=401,
                content={"error": "AUTH_TENANT_MISSING"},
            )

        tenant = Tenant(tenant_id=tenant_id)
        set_tenant(tenant)

        logger.info("[AUTH] OK | tenant=%s | path=%s", tenant_id, path)

        # ── Ejecutar request ──────────────────────────────────────────────
        response = await call_next(request)
        return response

    except JWTError as e:
        logger.warning("[AUTH] JWT ERROR | path=%s | error=%s", path, str(e))
        return JSONResponse(
            status_code=401,
            content={"error": str(e)},
        )

    except Exception as e:
        logger.exception("[AUTH] MIDDLEWARE FAILURE | path=%s", path)
        return JSONResponse(
            status_code=500,
            content={"error": "AUTH_MIDDLEWARE_FAILURE"},
        )

    finally:
        # ── Limpiar context en TODOS los caminos ──────────────────────────
        clear_tenant()
