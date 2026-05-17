# models/cotizacion.py — MESAN Ω
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship, declarative_base
from decimal import Decimal
import datetime

Base = declarative_base()

class CotizacionIndustrial(Base):
    __tablename__ = "cotizaciones_industriales"
    id                          = Column(Integer, primary_key=True, index=True)
    folio                       = Column(String(50), unique=True, index=True, nullable=False)
    cliente_nombre              = Column(String(255), nullable=False)
    fecha_creacion              = Column(DateTime, default=datetime.datetime.utcnow)
    costo_directo_total         = Column(Numeric(12, 2), default=0)
    gastos_indirectos_total     = Column(Numeric(12, 2), default=0)
    utilidad_solicitada_porcentaje = Column(Numeric(5, 2), default=0)
    precio_final_neto           = Column(Numeric(12, 2), default=0)
    conceptos = relationship("ConceptoCotizacion", back_populates="cotizacion", cascade="all, delete-orphan")

class ConceptoCotizacion(Base):
    __tablename__ = "conceptos_cotizacion"
    id             = Column(Integer, primary_key=True, index=True)
    cotizacion_id  = Column(Integer, ForeignKey("cotizaciones_industriales.id", ondelete="CASCADE"), nullable=False)
    descripcion    = Column(String(500), nullable=False)
    tipo_concepto  = Column(String(50), nullable=False)
    cantidad       = Column(Numeric(12, 2), nullable=False)
    costo_unitario = Column(Numeric(12, 2), nullable=False)
    costo_total    = Column(Numeric(12, 2), nullable=False)
    cotizacion     = relationship("CotizacionIndustrial", back_populates="conceptos")
