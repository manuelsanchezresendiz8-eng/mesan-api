# models.py -- MESAN Omega v3.3.0
# Modelos de Base de Datos — esquema final Fase 1
# ================================================
# Migración aplicada: 2026-06-16
# Columnas agregadas: nombre_contacto, whatsapp, empleados, origen,
#   fuente_detalle, nivel_riesgo, impacto_estimado, omega_score,
#   updated_at, created_at
# Backup previo: leads_backup_20260616 (19 registros)
# Total columnas tabla leads: 20

import uuid

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Numeric
from sqlalchemy.sql import func
from database import Base


class Diagnostico(Base):
    """
    Tabla principal: diagnósticos generados.
    pagado=False → solo gancho visible.
    pagado=True → diagnóstico completo desbloqueado.
    """
    __tablename__ = "diagnosticos"

    id              = Column(Integer, primary_key=True, index=True)
    nivel           = Column(String(20))
    area            = Column(String(100))
    impacto         = Column(String(100))
    causa           = Column(Text)
    detalle         = Column(Text)
    impacto_detalle = Column(Text)
    plan            = Column(Text)
    sector          = Column(String(50))
    empresa         = Column(String(200))
    pagado          = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())


class Lead(Base):
    """
    CRM comercial: leads capturados desde la landing y otros orígenes.

    Columnas originales (preservadas para compatibilidad):
        id, nombre, email, telefono, score, clasificacion,
        impacto_min, impacto_max, estatus, fecha

    Columnas CRM (migración 2026-06-16):
        nombre_contacto  -- campo principal (landing envia 'nombre')
        whatsapp         -- WhatsApp del contacto
        empleados        -- rango de empleados
        origen           -- 'landing', 'whatsapp', 'referido', etc.
        fuente_detalle   -- 'meta_ads', 'google', 'linkedin', etc.

    Columnas Omega (enriquecimiento post-evaluacion):
        nivel_riesgo     -- CRITICO / ALTO / MEDIO / BAJO
        impacto_estimado -- exposicion economica estimada MXN
        omega_score      -- score 0-100

    Timestamps:
        created_at  -- fecha de creacion del lead
        updated_at  -- ultima actualizacion

    Nota: 'nombre' y 'fecha' se mantienen como campos legacy.
    Toda logica nueva escribe en 'nombre_contacto' y timestamps.
    """
    __tablename__ = "leads"

    # ── Columnas originales (no modificar) ───────────────────────────────
    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre        = Column(String)    # legacy
    email         = Column(String)
    telefono      = Column(String)
    score         = Column(Integer)
    clasificacion = Column(String)
    impacto_min   = Column(Integer)
    impacto_max   = Column(Integer)
    estatus       = Column(String, default="nuevo")
    fecha         = Column(String)    # legacy

    # ── Columnas CRM (2026-06-16) ─────────────────────────────────────────
    nombre_contacto = Column(String(200))
    whatsapp        = Column(String(50))
    empleados       = Column(String(50))
    origen          = Column(String(100))
    fuente_detalle  = Column(String(150))

    # ── Columnas Omega ────────────────────────────────────────────────────
    nivel_riesgo     = Column(String(50))
    impacto_estimado = Column(Numeric(15, 2))
    omega_score      = Column(Numeric(5, 2))

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
