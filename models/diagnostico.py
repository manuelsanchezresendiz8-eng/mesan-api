# models/diagnostico.py
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre         = Column(String, nullable=True)
    email          = Column(String, nullable=True)
    telefono       = Column(String, nullable=True)

    sector         = Column(String, nullable=True)
    texto_input    = Column(Text, nullable=True)

    score          = Column(Integer, default=0)
    clasificacion  = Column(String, default="MEDIO")
    tendencia      = Column(String, default="ESTABLE")
    confianza      = Column(Integer, default=70)

    impacto_min    = Column(Float, default=0)
    impacto_max    = Column(Float, default=0)

    causas         = Column(Text, nullable=True)
    analisis_ai    = Column(Text, nullable=True)
    plan_30_dias   = Column(Text, nullable=True)
    whatsapp       = Column(Text, nullable=True)

    pagado         = Column(Boolean, default=False)
    estatus        = Column(String, default="nuevo")

    fecha          = Column(DateTime, default=datetime.utcnow)
    fecha_pago     = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id":           self.id,
            "nombre":       self.nombre,
            "email":        self.email,
            "telefono":     self.telefono,
            "sector":       self.sector,
            "score":        self.score,
            "clasificacion":self.clasificacion,
            "tendencia":    self.tendencia,
            "confianza":    self.confianza,
            "impacto_min":  self.impacto_min,
            "impacto_max":  self.impacto_max,
            "pagado":       self.pagado,
            "estatus":      self.estatus,
            "fecha":        str(self.fecha) if self.fecha else None,
        }
