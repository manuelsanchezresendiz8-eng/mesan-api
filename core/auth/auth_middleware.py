# core/auth/auth_middleware.py -- MESAN Omega v1.7
import os
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from core.auth.jwt_handler import verify_token, JWTError
from core.auth.tenant_context import set_tenant, clear_tenant
from core.auth.tenant_model import Tenant

logger = logging.getLogger("mesan.auth")

PUBLIC_PATHS = {
    "/",
    "/health",
    "/ready",
    "/docs",
    "/openapi.json",
    "/execute",
    "/analyze"
}

async def auth_middleware(request: Request, call_next):
    clear_tenant()

    path = request.url.path

    try:

        # =========================================================
        # CORS PREFLIGHT
        # =========================================================

        if request.method == "OPTIONS":
            return await call_next(request)

        # =========================================================
        # PUBLIC ENDPOINTS
        # =========================================================

        if path in PUBLIC_PATHS:
            response = await call_next(request)
            clear_tenant()
            return response

        # =========================================================
        # AUTH HEADER
        # =========================================================

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "MISSING_OR_INVALID_AUTH_HEADER"}
            )

        token = auth_header.split(" ", 1)[1]

        # =========================================================
        # DEV / CI FALLBACK
        # =========================================================

        if token.startswith("jwt_not_installed_"):
            tenant_id = token.replace("jwt_not_installed_", "")

            set_tenant(
                Tenant(
                    tenant_id=tenant_id,
                    name="CI_TENANT",
                    plan="FREE"
                )
            )

            response = await call_next(request)
            clear_tenant()

            return response

        # =========================================================
        # JWT VALIDATION
        # =========================================================

        payload = verify_token(token)

        tenant_id = payload.get("tenant_id")

        if not tenant_id:
            return JSONResponse(
                status_code=401,
                content={"error": "INVALID_TOKEN_TENANT"}
            )

        set_tenant(
            Tenant(
                tenant_id=tenant_id,
                name="RESOLVED_FROM_JWT",
                plan=payload.get("plan", "FREE")
            )
        )

        response = await call_next(request)

        clear_tenant()

        return response

    except JWTError as e:

        clear_tenant()

        logger.warning(
            f"[AUTH] JWT error path={path} error={str(e)}"
        )

        return JSONResponse(
            status_code=401,
            content={"error": str(e)}
        )

    except Exception as e:

        clear_tenant()

        logger.exception(
            f"[AUTH] Middleware failure path={path}"
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "AUTH_MIDDLEWARE_FAILURE"
            }
        )
