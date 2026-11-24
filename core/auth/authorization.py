"""Helpers de autorización basados en el rol de la membresía validada."""
from fastapi import HTTPException, Request

TENANT_ROLES = frozenset({"owner", "admin", "member"})


def role_is_allowed(role: str | None, allowed_roles: set[str] | frozenset[str]) -> bool:
    """Niega roles ausentes o desconocidos; nunca concede por defecto."""
    return role in TENANT_ROLES and role in allowed_roles


def require_roles(request: Request, *allowed_roles: str) -> str:
    """Exige un rol ya inyectado por auth_middleware tras validar PostgreSQL."""
    context = getattr(request.state, "ctx", None)
    role = getattr(context, "role", None)
    if not role_is_allowed(role, frozenset(allowed_roles)):
        raise HTTPException(status_code=403, detail="INSUFFICIENT_ROLE")
    return role
