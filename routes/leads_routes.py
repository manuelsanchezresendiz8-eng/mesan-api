# routes/leads_routes.py -- MESAN Omega Leads Routes (Fase 1)
"""
Rutas de captacion y gestion de leads.

Seguridad (Fase 1):
    POST /api/leads  -- PUBLICA (captura desde landing)
    GET  /api/leads  -- Basic Auth (CRM)
    GET  /api/leads/{lead_id}   -- Basic Auth (CRM)
    PATCH /api/leads/{lead_id}  -- Basic Auth (CRM)

    ADVERTENCIA: GET/PATCH estan exentas de JWT en auth_middleware.py.
    Su unica proteccion es Depends(verify_crm_credentials).
    NO eliminar esa dependencia sin agregar proteccion equivalente.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.auth.basic_auth import verify_crm_credentials
from core.lead_store import LeadNotFoundError, create_lead, get_lead, list_leads, update_lead

logger = logging.getLogger("mesan.leads")

router = APIRouter(prefix="/api/leads", tags=["Leads"])


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    """Payload enviado por index.html al hacer submit del formulario."""
    nombre:    str
    empresa:   Optional[str] = None
    correo:    str
    whatsapp:  str
    sector:    Optional[str] = None
    empleados: Optional[str] = None
    fuente:    Optional[str] = "landing_mesan_omega"
    timestamp: Optional[str] = None


class LeadUpdate(BaseModel):
    """Campos actualizables desde el CRM Enterprise."""
    estatus:          Optional[str] = None
    nivel_riesgo:     Optional[str] = None
    impacto_estimado: Optional[float] = None
    omega_score:      Optional[float] = None
    nombre_contacto:  Optional[str] = None
    whatsapp:         Optional[str] = None
    empleados:        Optional[str] = None
    origen:           Optional[str] = None
    fuente_detalle:   Optional[str] = None


class LeadOut(BaseModel):
    """Representacion de un lead para respuestas del API."""
    id:               Optional[str] = None
    nombre_contacto:  Optional[str] = None
    nombre:           Optional[str] = None     # legacy
    email:            Optional[str] = None
    whatsapp:         Optional[str] = None
    empleados:        Optional[str] = None
    origen:           Optional[str] = None
    fuente_detalle:   Optional[str] = None
    nivel_riesgo:     Optional[str] = None
    impacto_estimado: Optional[float] = None
    omega_score:      Optional[float] = None
    estatus:          Optional[str] = None
    created_at:       Optional[datetime] = None
    updated_at:       Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────

# ----------------------------------------------------------------------------
# POST /api/leads -- PUBLICA (captura desde landing)
# ----------------------------------------------------------------------------
@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead_endpoint(payload: LeadCreate) -> LeadOut:
    """
    Crea un nuevo lead desde el formulario de la landing.
    PUBLICA: sin autenticacion.
    """
    lead = create_lead(payload.model_dump())
    logger.info("[LEADS] Nuevo lead | id=%s | nombre=%s", lead.id, lead.nombre_contacto)
    return lead


# ----------------------------------------------------------------------------
# GET /api/leads -- PROTEGIDA (Basic Auth)
# ----------------------------------------------------------------------------
@router.get("", response_model=list[LeadOut])
async def list_leads_endpoint(
    _user: str = Depends(verify_crm_credentials),
) -> list[LeadOut]:
    """
    Lista todos los leads. PROTEGIDA por Basic Auth.
    Exenta de JWT en auth_middleware.py — NO eliminar Depends.
    """
    return list_leads()


# ----------------------------------------------------------------------------
# GET /api/leads/{lead_id} -- PROTEGIDA (Basic Auth)
# ----------------------------------------------------------------------------
@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead_endpoint(
    lead_id: str,
    _user: str = Depends(verify_crm_credentials),
) -> LeadOut:
    """PROTEGIDA por Basic Auth."""
    try:
        return get_lead(lead_id)
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead no encontrado: {lead_id}",
        )


# ----------------------------------------------------------------------------
# PATCH /api/leads/{lead_id} -- PROTEGIDA (Basic Auth)
# ----------------------------------------------------------------------------
@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead_endpoint(
    lead_id: str,
    payload: LeadUpdate,
    _user: str = Depends(verify_crm_credentials),
) -> LeadOut:
    """PROTEGIDA por Basic Auth."""
    try:
        lead = update_lead(lead_id, payload.model_dump(exclude_none=True))
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead no encontrado: {lead_id}",
        )
    logger.info("[LEADS] Lead actualizado | id=%s | usuario=%s", lead_id, _user)
    return lead
