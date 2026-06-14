# core/auth/basic_auth.py -- MESAN Omega Basic Auth (Fase 1, CRM)
"""
Basic Auth para las rutas del CRM en Fase 1.

Por que existe:
    auth_middleware.py v1.2 exime de JWT a las siguientes rutas porque
    no existe (todavia) un flujo de login/emision de JWT:

        GET   /api/leads
        GET   /api/leads/{lead_id}
        PATCH /api/leads/{lead_id}
        GET   /crm_enterprise.html

    Esas rutas NO son publicas: su unica proteccion real es la
    dependencia `verify_crm_credentials` definida aqui, aplicada via
    `Depends(verify_crm_credentials)` en cada endpoint.

Fail-closed:
    Si las variables de entorno CRM_BASIC_USER / CRM_BASIC_PASSWORD no
    estan definidas, TODAS las requests a las rutas protegidas devuelven
    503 (no 200, no "passthrough"). Nunca se permite acceso sin
    credenciales configuradas.

Comparacion segura:
    Se usa `secrets.compare_digest` para evitar timing attacks al
    comparar usuario y password.

Fase 2:
    Cuando exista login + emision de JWT real, este modulo y las 4
    exenciones correspondientes en auth_middleware.py deben retirarse,
    dejando JWT como unica capa de autenticacion para el CRM.
"""

import logging
import os
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

logger = logging.getLogger("mesan.auth.basic")

_security = HTTPBasic()


def verify_crm_credentials(
    credentials: HTTPBasicCredentials = Depends(_security),
) -> str:
    """
    Dependencia FastAPI: valida Basic Auth contra CRM_BASIC_USER /
    CRM_BASIC_PASSWORD (variables de entorno).

    Returns:
        El nombre de usuario autenticado (str), si las credenciales
        son correctas.

    Raises:
        HTTPException 503: si CRM_BASIC_USER o CRM_BASIC_PASSWORD no
            estan configuradas en el entorno (fail-closed: nunca se
            permite acceso sin credenciales configuradas).
        HTTPException 401: si el usuario o password no coinciden,
            con header WWW-Authenticate para disparar el prompt del
            navegador.
    """
    expected_user = os.environ.get("CRM_BASIC_USER")
    expected_password = os.environ.get("CRM_BASIC_PASSWORD")

    if not expected_user or not expected_password:
        logger.error(
            "[BASIC_AUTH] CRM_BASIC_USER/CRM_BASIC_PASSWORD no configuradas "
            "-- acceso denegado (fail-closed)"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRM_AUTH_NOT_CONFIGURED",
        )

    user_ok = secrets.compare_digest(credentials.username, expected_user)
    password_ok = secrets.compare_digest(credentials.password, expected_password)

    if not (user_ok and password_ok):
        logger.warning(
            "[BASIC_AUTH] Credenciales invalidas | usuario_recibido=%s",
            credentials.username,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Basic"},
        )

    logger.info("[BASIC_AUTH] OK | usuario=%s", credentials.username)
    return credentials.username
