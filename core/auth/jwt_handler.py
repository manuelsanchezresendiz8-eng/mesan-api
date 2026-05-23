# core/auth/jwt_handler.py -- MESAN Omega JWT Handler v1.1
import os, logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

logger = logging.getLogger("mesan.auth")

SECRET_KEY = os.getenv("MESAN_SECRET_KEY")
ALGORITHM  = "HS256"

if not SECRET_KEY:
    logger.warning("[AUTH] MESAN_SECRET_KEY not set — JWT disabled.")

class JWTError(Exception):
    pass

def create_token(tenant_id: str, expires_minutes: int = 60) -> str:
    if not SECRET_KEY: raise JWTError("MESAN_SECRET_KEY_NOT_SET")
    import jwt
    payload = {"tenant_id": tenant_id,
               "iat": datetime.now(timezone.utc),
               "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Dict:
    if not SECRET_KEY: raise JWTError("MESAN_SECRET_KEY_NOT_SET")
    import jwt
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise JWTError("TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise JWTError("TOKEN_INVALID")
