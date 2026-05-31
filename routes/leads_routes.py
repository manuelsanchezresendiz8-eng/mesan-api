# routes/leads_routes.py -- MESAN Omega Leads v1.3

from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging

router = APIRouter()

logger = logging.getLogger("mesan.leads")

# TEMPORAL
# Migrar a PostgreSQL posteriormente
leads_store = []


class LeadPayload(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    empresa: str = Field(..., min_length=2, max_length=120)

    email: Optional[str] = Field(default="", max_length=120)
    telefono: Optional[str] = Field(default="", max_length=20)
    whatsapp: Optional[str] = Field(default="", max_length=20)

    sector: Optional[str] = Field(default="", max_length=80)
    facturacion: Optional[str] = Field(default="", max_length=50)

    mensaje: Optional[str] = Field(default="", max_length=500)


# ==========================================================
# Repository Layer
# ==========================================================

def save_lead(lead: dict):
    """
    Temporal:
    Actualmente guarda en memoria.
    Futuro:
    PostgreSQL
    """
    leads_store.append(lead)


# ==========================================================
# Health
# ==========================================================

@router.get("/leads/health")
async def leads_health():

    return {
        "status": "ok",
        "service": "MESAN Leads",
        "version": "1.3",
        "total_leads": len(leads_store)
    }


# ==========================================================
# Estadísticas
# ==========================================================

@router.get("/leads/stats")
async def leads_stats():

    return {
        "version": "1.3",
        "total_leads": len(leads_store)
    }


# ==========================================================
# Crear Lead
# ==========================================================

@router.post("/leads")
async def crear_lead(payload: LeadPayload):

    try:

        lead = {
            "id": len(leads_store) + 1,

            "nombre": payload.nombre.strip(),
            "empresa": payload.empresa.strip(),

            "email": (payload.email or "").strip(),

            "telefono": (
                payload.telefono
                or payload.whatsapp
                or ""
            ).strip(),

            "sector": (payload.sector or "").strip(),

            "facturacion": (
                payload.facturacion or ""
            ).strip(),

            "mensaje": (
                payload.mensaje or ""
            ).strip(),

            "status": "nuevo",

            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "created_at": datetime.now(
                timezone.utc
            ).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            )
        }

        save_lead(lead)

        logger.info(
            f"[MESAN-LEAD] "
            f"empresa={lead['empresa']} "
            f"sector={lead['sector']}"
        )

        return {
            "status": "ok",
            "lead_id": lead["id"],
            "message": "Diagnóstico en proceso.",
            "redirect": "/demo_enterprise.html"
        }

    except Exception as e:

        logger.exception(
            "Error guardando lead"
        )

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": str(e)
            }
        )


# ==========================================================
# Obtener Leads
# ==========================================================

@router.get("/leads")
async def obtener_leads():

    return {
        "total": len(leads_store),
        "leads": leads_store
    }
