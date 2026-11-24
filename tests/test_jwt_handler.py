"""Regresiones para JWT ligados a identidad y tenant."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from core.auth import jwt_handler


@pytest.fixture(autouse=True)
def secret_key(monkeypatch):
    monkeypatch.setattr(jwt_handler, "SECRET_KEY", "test-tenant-secret-not-for-production")
    monkeypatch.setattr(jwt_handler, "PLATFORM_SECRET_KEY", "test-platform-secret-not-for-production")


def _token(payload):
    return jwt.encode(payload, jwt_handler.SECRET_KEY, algorithm="HS256")


def _platform_token(payload):
    return jwt.encode(payload, jwt_handler.PLATFORM_SECRET_KEY, algorithm="HS256")


def test_create_and_verify_tenant_bound_token():
    token = jwt_handler.create_token("user-1", "tenant-1")
    payload = jwt_handler.verify_token(token)
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert "iat" in payload and "exp" in payload


def test_rejects_signed_token_without_tenant_claim():
    now = datetime.now(timezone.utc)
    token = _token({"sub": "user-1", "iat": now, "exp": now + timedelta(minutes=5)})
    with pytest.raises(jwt_handler.JWTError, match="TOKEN_INVALID"):
        jwt_handler.verify_token(token)


def test_rejects_signed_token_without_expiration():
    now = datetime.now(timezone.utc)
    token = _token({"sub": "user-1", "tenant_id": "tenant-1", "iat": now})
    with pytest.raises(jwt_handler.JWTError, match="TOKEN_INVALID"):
        jwt_handler.verify_token(token)


def test_rejects_invalid_tenant_claim_and_oversized_token():
    now = datetime.now(timezone.utc)
    token = _token({
        "sub": "user-1",
        "tenant_id": "t" * 37,
        "typ": "tenant",
        "aud": jwt_handler.TENANT_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
    })
    with pytest.raises(jwt_handler.JWTError, match="TOKEN_TENANT_INVALID"):
        jwt_handler.verify_token(token)
    with pytest.raises(jwt_handler.JWTError, match="TOKEN_INVALID"):
        jwt_handler.verify_token("x" * 8193)



def test_tenant_and_platform_tokens_are_not_interchangeable():
    tenant_token = jwt_handler.create_token("user-1", "tenant-1")
    platform_token = jwt_handler.create_platform_token("operator-1")
    tenant_payload = jwt_handler.verify_token(tenant_token)
    platform_payload = jwt_handler.verify_platform_token(platform_token)
    assert tenant_payload["typ"] == "tenant"
    assert tenant_payload["aud"] == jwt_handler.TENANT_AUDIENCE
    assert platform_payload["typ"] == "platform"
    assert platform_payload["aud"] == jwt_handler.PLATFORM_AUDIENCE
    assert "tenant_id" not in platform_payload
    with pytest.raises(jwt_handler.JWTError):
        jwt_handler.verify_platform_token(tenant_token)
    with pytest.raises(jwt_handler.JWTError):
        jwt_handler.verify_token(platform_token)


def test_platform_token_rejects_tenant_claim():
    now = datetime.now(timezone.utc)
    token = _platform_token({"sub": "operator-1", "typ": "platform", "aud": jwt_handler.PLATFORM_AUDIENCE, "tenant_id": "tenant-1", "iat": now, "exp": now + timedelta(minutes=5)})
    with pytest.raises(jwt_handler.JWTError, match="PLATFORM_TOKEN_MUST_NOT_CONTAIN_TENANT"):
        jwt_handler.verify_platform_token(token)
