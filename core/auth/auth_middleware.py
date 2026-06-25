# core/auth/auth_middleware.py -- MESAN Omega Auth Middleware v1.2
"""
FastAPI Auth Middleware Ω

Valida JWT en cada request entrante.
Inyecta tenant context en el pipeline.
Limpia contexto en todos los caminos de ejecución.

Exentas de JWT (no requieren Bearer token en este middleware):
    GET  /health
    GET  /ready
    GET  /engines
    GET  /diagnostics
    GET  /features
    GET  /docs
    GET  /openapi.json
    POST /api/leads                  -- pública de verdad (captura desde landing)
    GET  /api/leads                  -- protegida por Basic Auth (ver leads_routes.py)
    GET  /crm_enterprise.html         -- protegida por Basic Auth (ver main.py)
    GET/PATCH /api/leads/{lead_id}    -- protegida por Basic Auth (ver leads_routes.py)

ESTRATEGIA FASE 1 (sin duplicar autenticación):
    No existe hoy un flujo de obtención de JWT (sin endpoint de login,
    sin store de usuarios). Exigir JWT en las rutas del CRM dejaría el
    CRM inaccesible para todos, incluido el operador — Basic Auth nunca
    llegaría a ejecutarse porque este middleware se ejecuta ANTES que
    cualquier Depends() de FastAPI.

    Por eso, para Fase 1:
      - Las 4 rutas del CRM quedan exentas de JWT aquí.
      - Basic Auth (core/auth/basic_auth.py) es la ÚNICA capa de protección
        para esas 4 rutas — aplicado vía Depends(verify_crm_credentials)
        directamente en cada endpoint.
      - POST /api/leads sigue siendo pública sin ninguna capa — es la
        captura de la landing.

    Fase 2: cuando exista login + emisión de JWT real, retirar las 4 rutas
    CRM de las exenciones de este middleware y depender solo de JWT,
    eliminando Basic Auth para evitar doble autenticación.

CHANGELOG v1.1 (Fase 1 — corrección de seguridad):
    - PUBLIC_PREFIXES eliminado. La excepción de /api/leads ya NO es por
      prefijo de ruta — antes, cualquier ruta que empezara con "/api/leads"
      (incluyendo GET /api/leads, GET /api/leads/{id}, PATCH /api/leads/{id})
      quedaba pública por accidente.

CHANGELOG v1.2 (Fase 1 — corrección de orden de ejecución):
    - v1.1 dejaba GET/PATCH /api/leads* y /crm_enterprise.html exigiendo
      JWT, pero sin flujo de obtención de JWT -> 401 siempre, Basic Auth
      nunca se ejecutaba (falso cierre de seguridad: cerrado, llave
      equivocada). Corregido: estas 4 rutas quedan exentas de JWT aquí
      y dependen exclusivamente de Basic Auth a nivel de endpoint.
"""


import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.auth.jwt_handler import JWTError, verify_token
from core.auth.tenant_context import clear_tenant, set_tenant
from core.auth.tenant_model import Tenant

logger = logging.getLogger("mesan.auth")

# ── Rutas públicas — no requieren token (sin importar método) ────────────────
PUBLIC_PATHS = {
    "/health",
    "/ready",
    "/engines",
    "/diagnostics",
    "/features",
    "/docs",
    "/openapi.json",
}

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ ⚠️  ADVERTENCIA DE REGRESIÓN DE SEGURIDAD — LEER ANTES DE MODIFICAR  ⚠️    ║
# ║                                                                            ║
# ║ Las entradas marcadas "Basic Auth" abajo NO son públicas, aunque estén    ║
# ║ exentas de JWT en este middleware. Su única protección real es el         ║
# ║ Depends(verify_crm_credentials) declarado en el ENDPOINT correspondiente  ║
# ║ (routes/leads_routes.py y main.py).                                       ║
# ║                                                                            ║
# ║ Si se agrega aquí una nueva exención de JWT para una ruta del CRM,        ║
# ║ es OBLIGATORIO verificar que ese mismo endpoint tenga                     ║
# ║ Depends(verify_crm_credentials) — de lo contrario la ruta queda           ║
# ║ públicamente abierta sin ninguna protección.                              ║
# ║                                                                            ║
# ║ Checklist al tocar este archivo o las rutas CRM:                          ║
# ║   [ ] ¿Sigue Depends(verify_crm_credentials) presente en las 4 rutas      ║
# ║       CRM (GET /api/leads, GET/PATCH /api/leads/{id},                     ║
# ║       GET /crm_enterprise.html)?                                          ║
# ║   [ ] ¿POST /api/leads sigue siendo la ÚNICA ruta sin ninguna capa?       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── Excepción específica por método + ruta exacta ────────────────────────────
# (path, method) -> exenta de JWT. NO usar prefijos: cada entrada es exacta.
#
# FASE 1 — nota de seguridad:
#   /api/leads (POST)        -> pública de verdad (captura desde landing).
#   /crm_enterprise.html,
#   /api/leads (GET),
#   /api/leads/{id} (GET/PATCH)
#       -> exentas de JWT (no existe flujo de obtención de token en Fase 1),
#          pero NO son públicas: quedan protegidas por Basic Auth
#          (core/auth/basic_auth.py, Depends(verify_crm_credentials))
#          aplicado directamente en cada endpoint.
#
#   auth_middleware corre ANTES que cualquier Depends() de ruta. Si estas
#   4 rutas no estuvieran aquí, auth_middleware devolvería 401 por falta de
#   JWT antes de que Basic Auth pudiera ejecutarse — dejando el CRM
#   inaccesible incluso con credenciales Basic Auth correctas.
#
#   Fase 2: cuando exista flujo JWT real (login + emisión de tokens),
#   estas 4 rutas deben retirarse de aquí y depender solo de JWT,
#   eliminando Basic Auth para evitar doble autenticación.
PUBLIC_METHOD_PATHS = {
    ("/api/leads", "POST"),
    ("/api/leads", "GET"),
    ("/crm_enterprise.html", "GET"),
    # /execute es el endpoint de diagnostico Ω — publico (flujo landing)
    # Protegido por rate limiting estricto + validacion fuerte de payload.
    # Fase 2: retirar cuando exista JWT real para prospectos.
    ("/execute", "POST"),
}

# Rutas con parámetro variable ({lead_id}) -- no se puede usar igualdad exacta
# de string. Se valida por patron + metodo, restringido a un solo segmento
# tras /api/leads/ (ej. /api/leads/LEAD-ABC123, no /api/leads/x/y).
import re
_LEAD_ID_PATH_RE = re.compile(r"^/api/leads/[^/]+$")


def _is_lead_id_path_exempt(path: str, method: str) -> bool:
    """GET/PATCH /api/leads/{lead_id} -- exentas de JWT aquí.

    ⚠️ NO son públicas: su protección real es Depends(verify_crm_credentials)
    en routes/leads_routes.py. Si esa dependencia se elimina del endpoint,
    estas rutas quedan completamente abiertas sin que este middleware lo
    detecte. Ver advertencia de regresión arriba.
    """
    return method.upper() in ("GET", "PATCH") and bool(_LEAD_ID_PATH_RE.match(path))


def _is_static_landing_asset(path: str, method: str) -> bool:
    """GET sobre archivos publicos servidos por StaticFiles (la landing y
    sus paginas legales) -- exentos de JWT por diseno, igual que
    /crm_enterprise.html, pero estos SI son verdaderamente publicos (sin
    Basic Auth tampoco): son la landing comercial que cualquier visitante
    debe poder ver.

    /crm_enterprise.html NO esta aqui -- tiene su propia ruta explicita
    en main.py con Depends(verify_crm_credentials) y su propia entrada en
    PUBLIC_METHOD_PATHS arriba.

    Cualquier archivo nuevo agregado a la raiz del repo (servido por el
    StaticFiles mount al final de main.py) cae aqui automaticamente sin
    necesidad de tocar este archivo, siempre que sea GET y no sea
    /crm_enterprise.html.
    """
    if method.upper() != "GET":
        return False
    if path == "/crm_enterprise.html":
        return False
    if path.startswith("/api/"):
        return False
    # Rutas de la app (FastAPI routers) ya manejadas por PUBLIC_PATHS /
    # PUBLIC_METHOD_PATHS / auth real -- no se tratan aqui para evitar
    # exentar accidentalmente algo que deberia llevar JWT real en el
    # futuro (ej. /pro/*, /api/v1/*).
    if path.startswith("/pro/") or path.startswith("/api/v1/"):
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
    """
    FastAPI-compatible auth middleware.

    Flujo:
        1. Rutas/método públicos → pass-through sin validar token
        2. Extraer Bearer token del header Authorization
        3. Verificar JWT con jwt_handler
        4. Inyectar Tenant en context
        5. Ejecutar request
        6. Limpiar context en TODOS los caminos (éxito, error, excepción)
    """
    # CVE-2026-48710 "BadHost": usar scope["path"] en lugar de request.url.path
    # request.url.path puede ser manipulado via Host header malformado.
    # request.scope["path"] refleja el path real del ASGI server.
    path   = request.scope.get("path", request.url.path)
    method = request.method

    # ── Rutas/método públicos ────────────────────────────────────────────
    if _is_public(path, method):
        return await call_next(request)

    # ── Extraer token ─────────────────────────────────────────────────────
    token = _extract_token(request)
    if not token:
        logger.warning("[AUTH] Token faltante | path=%s method=%s", path, method)
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
