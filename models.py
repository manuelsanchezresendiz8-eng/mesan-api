# models.py
# MESAN Omega — Modelos de Base de Datos
# =======================================

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Diagnostico(Base):
    """
    Tabla principal: diagnósticos generados.
    pagado=False → solo gancho visible.
    pagado=True → diagnóstico completo desbloqueado.
    """
    __tablename__ = "diagnosticos"

    id = Column(Integer, primary_key=True, index=True)
    nivel = Column(String(20)) # CRITICO / ALTO / MEDIO / BAJO
    area = Column(String(100))
    impacto = Column(String(100)) # "560,000 - 1,400,000"
    causa = Column(Text) # Causa raíz (solo post-pago)
    detalle = Column(Text) # Detalle completo (solo post-pago)
    impacto_detalle = Column(Text) # Impacto detallado (solo post-pago)
    plan = Column(Text) # Plan de acción (solo post-pago)
    sector = Column(String(50))
    empresa = Column(String(200))
    pagado = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Lead(Base):
    """
    CRM: leads capturados para seguimiento comercial.
    Se llena automáticamente cuando nivel es ALTO o CRÍTICO.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String(200))
    sector = Column(String(50))
    nivel = Column(String(20))
    impacto = Column(String(100))
    texto = Column(Text) # Descripción original del usuario
    pagado = Column(Boolean, default=False) # Se actualiza si completa pago
    created_at = Column(DateTime(timezone=True), server_default=func.now())
