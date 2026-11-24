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
    import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not isinstance(payload.get("sub"), str) or not payload.get("sub"):
            raise JWTError("TOKEN_SUBJECT_MISSING")
        return payload
    except jwt.ExpiredSignatureError:
        raise JWTError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise JWTError("TOKEN_INVALID")
