# core/auth/jwt_handler.py -- MESAN Omega JWT Handler v1.2
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

logger = logging.getLogger("mesan.auth")
SECRET_KEY = os.getenv("MESAN_SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    logger.warning("[AUTH] MESAN_SECRET_KEY not set — JWT disabled.")

class JWTError(Exception):
    pass

def create_token(user_id: str, tenant_id: str, expires_minutes: int = 60) -> str:
    """Emite token ligado a usuario; el middleware valida su membresia activa."""
    if not SECRET_KEY:
        raise JWTError("MESAN_SECRET_KEY_NOT_SET")
    if not user_id or not tenant_id:
        raise JWTError("TOKEN_IDENTITY_AND_TENANT_REQUIRED")
    import jwt
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict:
    if not SECRET_KEY:
        raise JWTError("MESAN_SECRET_KEY_NOT_SET")
    if not isinstance(token, str) or not token or len(token) > 8192:
        raise JWTError("TOKEN_INVALID")
    import jwt
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "tenant_id", "iat", "exp"]},
        )
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not isinstance(user_id, str) or not user_id:
            raise JWTError("TOKEN_SUBJECT_MISSING")
        if not isinstance(tenant_id, str) or not 1 <= len(tenant_id) <= 36:
            raise JWTError("TOKEN_TENANT_INVALID")
        return payload
    except jwt.ExpiredSignatureError:
        raise JWTError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise JWTError("TOKEN_INVALID")
