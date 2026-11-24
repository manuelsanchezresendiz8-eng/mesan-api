# core/auth/jwt_handler.py -- MESAN Omega JWT Handler v1.3
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

logger = logging.getLogger("mesan.auth")
SECRET_KEY = os.getenv("MESAN_SECRET_KEY")
PLATFORM_SECRET_KEY = os.getenv("MESAN_PLATFORM_SECRET_KEY")
ALGORITHM = "HS256"
TENANT_AUDIENCE = "mesan-tenant-api"
PLATFORM_AUDIENCE = "mesan-platform-api"

if not SECRET_KEY:
    logger.warning("[AUTH] MESAN_SECRET_KEY not set — JWT disabled.")


class JWTError(Exception):
    pass


def _encode(payload: dict, secret_key: str | None, missing_error: str) -> str:
    if not secret_key:
        raise JWTError(missing_error)
    import jwt
    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def create_token(user_id: str, tenant_id: str, expires_minutes: int = 60) -> str:
    """Emite JWT exclusivamente para identidad y audiencia de tenant."""
    if not user_id or not tenant_id:
        raise JWTError("TOKEN_IDENTITY_AND_TENANT_REQUIRED")
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": user_id,
        "tenant_id": tenant_id,
        "typ": "tenant",
        "aud": TENANT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }, SECRET_KEY, "MESAN_SECRET_KEY_NOT_SET")


def create_platform_token(operator_id: str, expires_minutes: int = 30) -> str:
    """Emite JWT de operador, criptográficamente distinguible del JWT tenant."""
    if not operator_id:
        raise JWTError("PLATFORM_OPERATOR_ID_REQUIRED")
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": operator_id,
        "typ": "platform",
        "aud": PLATFORM_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }, PLATFORM_SECRET_KEY, "MESAN_PLATFORM_SECRET_KEY_NOT_SET")


def _decode(token: str, audience: str, required: list[str], secret_key: str, missing_error: str) -> Dict:
    if not secret_key:
        raise JWTError(missing_error)
    if not isinstance(token, str) or not token or len(token) > 8192:
        raise JWTError("TOKEN_INVALID")
    import jwt
    try:
        return jwt.decode(
            token,
            secret_key,
            algorithms=[ALGORITHM],
            audience=audience,
            options={"require": required},
        )
    except jwt.ExpiredSignatureError:
        raise JWTError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise JWTError("TOKEN_INVALID")


def verify_token(token: str) -> Dict:
    payload = _decode(
        token,
        TENANT_AUDIENCE,
        ["sub", "tenant_id", "typ", "aud", "iat", "exp"],
        SECRET_KEY,
        "MESAN_SECRET_KEY_NOT_SET",
    )
    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    if payload.get("typ") != "tenant":
        raise JWTError("TOKEN_TYPE_INVALID")
    if not isinstance(user_id, str) or not user_id:
        raise JWTError("TOKEN_SUBJECT_MISSING")
    if not isinstance(tenant_id, str) or not 1 <= len(tenant_id) <= 36:
        raise JWTError("TOKEN_TENANT_INVALID")
    return payload


def verify_platform_token(token: str) -> Dict:
    payload = _decode(
        token,
        PLATFORM_AUDIENCE,
        ["sub", "typ", "aud", "iat", "exp"],
        PLATFORM_SECRET_KEY,
        "MESAN_PLATFORM_SECRET_KEY_NOT_SET",
    )
    operator_id = payload.get("sub")
    if payload.get("typ") != "platform":
        raise JWTError("TOKEN_TYPE_INVALID")
    if not isinstance(operator_id, str) or not operator_id:
        raise JWTError("TOKEN_SUBJECT_MISSING")
    if "tenant_id" in payload:
        raise JWTError("PLATFORM_TOKEN_MUST_NOT_CONTAIN_TENANT")
    return payload
