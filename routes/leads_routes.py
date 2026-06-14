# routes/leads_routes.py -- MESAN Omega Leads Routes (Fase 1)
"""
Rutas de captacion y gestion de leads.

Seguridad (Fase 1):
    POST /api/leads
        -- PUBLICA. Sin ninguna capa de auth. Es la captura desde la
           landing (formulario de contacto).

    GET   /api/leads
    GET   /api/leads/{lead_id}
    PATCH /api/leads/{lead_id}
        -- Exentas de JWT en core/auth/auth_middleware.py (no existe
           flujo de login en Fase 1), protegidas EXCLUSIVAMENTE por
           Depends(verify_crm_credentials) (Basic Auth).

    ADVERTENCIA: si se elimina Depends(verify_crm_credentials) de
    cualquiera de estas 3 rutas, la ruta queda PUBLICA sin que
    auth_middleware lo detecte (esta exenta de JWT por diseno).
    Ver core/auth/auth_middleware.py para el detalle completo.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth.basic_auth import verify_crm_credentials
from core.lead_store import (
    LeadNotFoundError,
    create_lead,
    get_lead,
    list_leads,
    update_lead,
)
from core.models.lead_models import LeadCreate, LeadOut, LeadUpdate

logger = logging.getLogger("mesan.leads")

router = APIRouter(prefix="/api/leads", tags=["leads"])


# ----------------------------------------------------------------------------
# POST /api/leads -- PUBLICA (captura desde landing)
# ----------------------------------------------------------------------------
@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
async def create_lead_endpoint(payload: LeadCreate) -> LeadOut:
    """
    Crea un nuevo lead a partir del formulario de la landing.

    PUBLICA: sin Depends de autenticacion. Cualquier visitante de la
    landing puede invocar este endpoint para registrarse como lead.
    """
    lead = create_lead(payload)
    logger.info("[LEADS] Nuevo lead creado | lead_id=%s", lead.lead_id)
    return lead


# ----------------------------------------------------------------------------
# GET /api/leads -- PROTEGIDA (Basic Auth)
# ----------------------------------------------------------------------------
@router.get("", response_model=list[LeadOut])
async def list_leads_endpoint(
    _user: str = Depends(verify_crm_credentials),
) -> list[LeadOut]:
    """
    Lista todos los leads registrados.

    PROTEGIDA: requiere Basic Auth (CRM_BASIC_USER / CRM_BASIC_PASSWORD).
    Exenta de JWT en auth_middleware.py -- NO eliminar
    Depends(verify_crm_credentials) sin agregar una proteccion
    equivalente.
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
    """
    Obtiene el detalle de un lead por su ID.

    PROTEGIDA: requiere Basic Auth. Exenta de JWT en
    auth_middleware.py -- NO eliminar Depends(verify_crm_credentials)
    sin agregar una proteccion equivalente.
    """
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
    """
    Actualiza campos de un lead existente (ej. estatus, notas).

    PROTEGIDA: requiere Basic Auth. Exenta de JWT en
    auth_middleware.py -- NO eliminar Depends(verify_crm_credentials)
    sin agregar una proteccion equivalente.
    """
    try:
        lead = update_lead(lead_id, payload)
    except LeadNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead no encontrado: {lead_id}",
        )
    logger.info(
        "[LEADS] Lead actualizado | lead_id=%s | usuario=%s", lead_id, _user
    )
    return lead
