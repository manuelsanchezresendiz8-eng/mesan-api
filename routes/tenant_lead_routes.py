"""API de leads privados con aislamiento estricto por tenant."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from core.auth.tenant_context import get_tenant
from core.lead_store import (
    LeadNotFoundError,
    get_tenant_lead,
    list_tenant_leads,
    update_tenant_lead,
)

router = APIRouter(prefix="/tenant/leads", tags=["Leads por empresa"])


class TenantLeadPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estatus: Optional[str] = Field(default=None, max_length=50)
    nivel_riesgo: Optional[str] = Field(default=None, max_length=50)
    impacto_estimado: Optional[Decimal] = Field(default=None, ge=0)
    omega_score: Optional[Decimal] = Field(default=None, ge=0, le=100)
    nombre_contacto: Optional[str] = Field(default=None, max_length=200)
    whatsapp: Optional[str] = Field(default=None, max_length=50)
    empleados: Optional[str] = Field(default=None, max_length=50)
    origen: Optional[str] = Field(default=None, max_length=100)
    fuente_detalle: Optional[str] = Field(default=None, max_length=150)


def _tenant_id() -> str:
    tenant = get_tenant()
    if tenant is None or not tenant.tenant_id:
        raise HTTPException(status_code=401, detail="TENANT_CONTEXT_MISSING")
    return tenant.tenant_id


def _serialize(lead):
    result = {}
    for field in (
        "id", "tenant_id", "nombre", "nombre_contacto", "email", "telefono",
        "whatsapp", "empleados", "origen", "fuente_detalle", "estatus",
        "nivel_riesgo", "impacto_estimado", "omega_score", "created_at",
        "updated_at",
    ):
        value = getattr(lead, field, None)
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, (datetime, date)):
            value = value.isoformat()
        result[field] = value
    return result


@router.get("")
def list_private_leads():
    return [_serialize(lead) for lead in list_tenant_leads(_tenant_id())]


@router.get("/{lead_id}")
def get_private_lead(lead_id: str):
    try:
        return _serialize(get_tenant_lead(lead_id, _tenant_id()))
    except LeadNotFoundError:
        raise HTTPException(status_code=404, detail="LEAD_NOT_FOUND")


@router.patch("/{lead_id}")
def patch_private_lead(lead_id: str, payload: TenantLeadPatch):
    fields = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not fields:
        raise HTTPException(status_code=422, detail="NO_FIELDS_TO_UPDATE")
    try:
        lead = update_tenant_lead(lead_id, _tenant_id(), fields)
        return _serialize(lead)
    except LeadNotFoundError:
        raise HTTPException(status_code=404, detail="LEAD_NOT_FOUND")
