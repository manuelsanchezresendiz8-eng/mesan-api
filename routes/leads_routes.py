# routes/leads_routes.py -- MESAN Omega Leads Routes (Fase 1)
"""
Rutas de captacion y gestion de leads.

Seguridad (Fase 1):
    POST /api/leads  -- PUBLICA (captura desde landing), con rate
                         limiting + honeypot validado en backend.
    GET  /api/leads  -- Basic Auth (CRM)
    GET  /api/leads/{lead_id}   -- Basic Auth (CRM)
    PATCH /api/leads/{lead_id}  -- Basic Auth (CRM)

    ADVERTENCIA: GET/PATCH estan exentas de JWT en auth_middleware.py.
    Su unica proteccion es Depends(verify_crm_credentials).
    NO eliminar esa dependencia sin agregar proteccion equivalente.

Rate limiting (Fase 1.5):
    POST /api/leads limitado a 5 solicitudes por IP cada 60 segundos.
    Ver core/rate_limiter.py.

Validacion de payload (Fase 1.5, revision ChatGPT):
    - correo usa EmailStr -- rechaza formatos invalidos a nivel Pydantic.
    - nombre y whatsapp tienen longitud minima/maxima.
    - El honeypot ('website') se valida tambien en backend, NUNCA solo
      en frontend -- un bot que llame directo al endpoint (sin pasar
      por el HTML/JS) saltaria una validacion que solo existiera en
      el cliente.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from core.auth.basic_auth import verify_crm_credentials
from core.lead_store import LeadNotFoundError, create_lead, get_lead, list_leads, update_lead
from core.rate_limiter import rate_limit_check

logger = logging.getLogger("mesan.leads")

router = APIRouter(prefix="/api/leads", tags=["Leads"])


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    """
    Payload enviado por index.html al hacer submit del formulario.

    'website' es el honeypot: un campo oculto en el HTML que ningun
    usuario humano deberia llenar. Si llega con contenido, la
    solicitud se descarta en el endpoint (ver create_lead_endpoint).
    """
    nombre:    str = Field(min_length=2, max_length=120)
    empresa:   Optional[str] = Field(default=None, max_length=200)
    correo:    EmailStr
    whatsapp:  str = Field(min_length=8, max_length=25)
    sector:    Optional[str] = Field(default=None, max_length=100)
    empleados: Optional[str] = Field(default=None, max_length=50)
    fuente:    Optional[str] = Field(default="landing_mesan_omega", max_length=150)
    timestamp: Optional[str] = None
    website:   Optional[str] = Field(default=None, max_length=200)  # honeypot


class LeadUpdate(BaseModel):
    """Campos actualizables desde el CRM Enterprise."""
    estatus:          Optional[str] = Field(default=None, max_length=50)
    nivel_riesgo:     Optional[str] = Field(default=None, max_length=50)
    impacto_estimado: Optional[float] = Field(default=None, ge=0)
    omega_score:      Optional[float] = Field(default=None, ge=0, le=100)
    nombre_contacto:  Optional[str] = Field(default=None, max_length=200)
    whatsapp:         Optional[str] = Field(default=None, max_length=25)
    empleados:        Optional[str] = Field(default=None, max_length=50)
    origen:           Optional[str] = Field(default=None, max_length=100)
    fuente_detalle:   Optional[str] = Field(default=None, max_length=150)


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
async def create_lead_endpoint(payload: LeadCreate, request: Request) -> LeadOut:
    """
    Crea un nuevo lead desde el formulario de la landing.

    PUBLICA: sin autenticacion. Protegida por:
      1. Rate limiting (5 solicitudes por IP cada 60 segundos).
      2. Honeypot validado en backend (campo 'website' debe llegar vacio).
      3. Validacion fuerte de tipos/longitudes via Pydantic.
    """
    rate_limit_check(request, key="create_lead", max_requests=5, window_seconds=60)

    # Honeypot: si el campo oculto 'website' llega con contenido, es un
    # bot (un humano nunca ve ni llena ese campo). Se descarta de forma
    # silenciosa -- se responde 201 falso-positivo para no delatar la
    # trampa al bot, pero el lead NUNCA se persiste.
    if payload.website:
        logger.warning(
            "[LEADS] Honeypot disparado | ip=%s | website='%s'",
            request.client.host if request.client else "unknown",
            payload.website,
        )
        # Respuesta identica a un 201 real, sin crear el lead, para que
        # el bot no aprenda a evitar la trampa.
        return LeadOut(
            id=None,
            nombre_contacto=payload.nombre,
            estatus="nuevo",
        )

    lead = create_lead(payload.model_dump(exclude={"website"}))
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
    Exenta de JWT en auth_middleware.py -- NO eliminar Depends.
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
