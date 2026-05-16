# models/diagnostico.py — MESAN Ω v2.5.0

from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, Float
from datetime import datetime
import uuid
from database import Base


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    lead_id       = Column(String, index=True, default="")
    score         = Column(Integer, default=0)
    clasificacion = Column(String, default="REVISION")
    nivel_riesgo  = Column(String, default="MEDIO")
    resultado_json = Column(Text, default="{}")
    fecha         = Column(DateTime, default=datetime.utcnow)

    # Campos financiero avanzado
    nivel         = Column(String, default="MEDIO")
    area          = Column(String, default="")
    impacto       = Column(Float, default=0)
    causa         = Column(Text, default="")
    detalle       = Column(Text, default="")
    plan          = Column(Text, default="")
    sector        = Column(String, default="GENERAL")
    empresa       = Column(String, default="")
    pagado        = Column(Boolean, default=False)
