"""Login y bootstrap controlado de MESAN Omega multiempresa."""
import hmac
import logging
import os
import uuid

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from core.auth.jwt_handler import create_token
from core.auth.passwords import hash_password, verify_password
from core.auth.tenant_db_models import TenantMembership, TenantRecord, UserRecord
from core.rate_limiter import rate_limit_check

logger = logging.getLogger("mesan.auth.routes")
router = APIRouter(prefix="/auth", tags=["Autenticación"])


class BootstrapPayload(BaseModel):
    tenant_name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=12, max_length=128)


class LoginPayload(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)
    tenant_id: str = Field(min_length=1, max_length=36)


@router.post("/bootstrap", status_code=201)
def bootstrap(
    payload: BootstrapPayload,
    request: Request,
    x_bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
):
    """Crea la primera empresa/admin solo con secreto de bootstrap del entorno."""
    rate_limit_check(request, key="auth_bootstrap", max_requests=3, window_seconds=300)
    expected = os.getenv("MESAN_BOOTSTRAP_TOKEN", "")
    if not expected or not x_bootstrap_token or not hmac.compare_digest(expected, x_bootstrap_token):
        raise HTTPException(status_code=403, detail="BOOTSTRAP_NOT_AUTHORIZED")

    db = SessionLocal()
    try:
        # Serializa intentos simultáneos: solo una transacción puede completar el bootstrap.
        db.execute(text("SELECT pg_advisory_xact_lock(73190423011)"))
        if db.query(UserRecord.id).first() is not None:
            raise HTTPException(status_code=409, detail="BOOTSTRAP_ALREADY_USED")

        tenant = TenantRecord(id=str(uuid.uuid4()), name=payload.tenant_name.strip(), status="active")
        user = UserRecord(
            id=str(uuid.uuid4()),
            email=payload.email.strip().lower(),
            password_hash=hash_password(payload.password),
            status="active",
        )
        db.add_all([tenant, user])
        db.flush()
        db.add(TenantMembership(
            id=str(uuid.uuid4()), tenant_id=tenant.id, user_id=user.id,
            role="owner", status="active",
        ))
        db.commit()
        return {
            "status": "created",
            "tenant_id": tenant.id,
            "user_id": user.id,
            "message": "Bootstrap creado. Deshabilite MESAN_BOOTSTRAP_TOKEN y use /auth/login.",
        }
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="BOOTSTRAP_CONFLICT")
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        db.close()


@router.post("/login")
def login(payload: LoginPayload, request: Request):
    """Autentica usuario y emite JWT solo para una membresía activa."""
    rate_limit_check(request, key="auth_login", max_requests=5, window_seconds=300)
    db = SessionLocal()
    try:
        email = payload.email.strip().lower()
        user = db.query(UserRecord).filter(
            UserRecord.email == email,
            UserRecord.status == "active",
        ).first()
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="INVALID_CREDENTIALS")

        membership = (
            db.query(TenantMembership)
            .join(TenantRecord, TenantRecord.id == TenantMembership.tenant_id)
            .filter(
                TenantMembership.user_id == user.id,
                TenantMembership.tenant_id == payload.tenant_id,
                TenantMembership.status == "active",
                TenantRecord.status == "active",
            )
            .first()
        )
        if membership is None:
            raise HTTPException(status_code=403, detail="ACTIVE_MEMBERSHIP_REQUIRED")

        token = create_token(user_id=user.id, tenant_id=membership.tenant_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 3600,
            "tenant_id": membership.tenant_id,
            "role": membership.role,
        }
    finally:
        db.close()
