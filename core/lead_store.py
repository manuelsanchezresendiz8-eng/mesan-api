# core/lead_store.py -- MESAN Omega Lead Store (Fase 1)
"""
Capa de acceso a datos para la tabla 'leads' en PostgreSQL.

Fuente unica de verdad: PostgreSQL via SQLAlchemy.
No existe ninguna otra capa escribiendo en esta tabla.

Operaciones disponibles:
    create_lead(payload)         -> Lead
    list_leads()                 -> list[Lead]
    get_lead(lead_id)            -> Lead
    update_lead(lead_id, fields) -> Lead

Errores:
    LeadNotFoundError — lanzado cuando lead_id no existe en la tabla.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Lead

logger = logging.getLogger("mesan.lead_store")


class LeadNotFoundError(Exception):
    pass


def _get_db() -> Session:
    return SessionLocal()


# ── CREATE ────────────────────────────────────────────────────────────────────
def create_lead(payload: dict) -> Lead:
    """
    Crea un nuevo lead en PostgreSQL a partir del payload de la landing.

    Payload esperado (enviado por index.html):
        nombre, empresa, correo, whatsapp, sector, empleados,
        fuente, timestamp (todos string)

    Mapeo:
        nombre_contacto = payload['nombre']
        nombre          = payload['nombre']      (compatibilidad legacy)
        email           = payload['correo']
        whatsapp        = payload['whatsapp']
        empleados       = payload['empleados']
        origen          = 'landing'
        fuente_detalle  = payload.get('fuente', 'landing_mesan_omega')
        estatus         = 'nuevo'
    """
    db = _get_db()
    try:
        lead = Lead(
            nombre_contacto = payload.get("nombre"),
            nombre          = payload.get("nombre"),       # legacy
            email           = payload.get("correo"),
            whatsapp        = payload.get("whatsapp"),
            empleados       = payload.get("empleados"),
            origen          = "landing",
            fuente_detalle  = payload.get("fuente", "landing_mesan_omega"),
            estatus         = "nuevo",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info("[LEAD_STORE] Lead creado | id=%s | nombre=%s", lead.id, lead.nombre_contacto)
        return lead
    except Exception as e:
        db.rollback()
        logger.error("[LEAD_STORE] Error creando lead: %s", e)
        raise
    finally:
        db.close()


# ── LIST ──────────────────────────────────────────────────────────────────────
def list_leads() -> list:
    """
    Devuelve todos los leads ordenados por created_at DESC.
    """
    db = _get_db()
    try:
        leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
        return leads
    finally:
        db.close()


# ── GET ───────────────────────────────────────────────────────────────────────
def get_lead(lead_id: str) -> Lead:
    """
    Devuelve un lead por su ID.
    Lanza LeadNotFoundError si no existe.
    """
    db = _get_db()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise LeadNotFoundError(f"Lead no encontrado: {lead_id}")
        return lead
    finally:
        db.close()


# ── UPDATE ────────────────────────────────────────────────────────────────────
def update_lead(lead_id: str, fields: dict) -> Lead:
    """
    Actualiza campos de un lead existente.
    Solo actualiza los campos presentes en 'fields' (patch parcial).
    Lanza LeadNotFoundError si no existe.

    Campos actualizables desde el CRM:
        estatus, nivel_riesgo, impacto_estimado, omega_score,
        nombre_contacto, whatsapp, empleados, origen, fuente_detalle
    """
    db = _get_db()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise LeadNotFoundError(f"Lead no encontrado: {lead_id}")

        for key, value in fields.items():
            if hasattr(lead, key) and value is not None:
                setattr(lead, key, value)

        db.commit()
        db.refresh(lead)
        logger.info("[LEAD_STORE] Lead actualizado | id=%s", lead_id)
        return lead
    except LeadNotFoundError:
        raise
    except Exception as e:
        db.rollback()
        logger.error("[LEAD_STORE] Error actualizando lead %s: %s", lead_id, e)
        raise
    finally:
        db.close()
