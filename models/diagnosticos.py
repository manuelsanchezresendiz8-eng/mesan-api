# models/diagnostico.py — MESAN Ω v2.5.0

from sqlalchemy import Column, String, Integer, Text, DateTime
from datetime import datetime
from database import Base


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id = Column(String, primary_key=True, index=True)
    lead_id = Column(String, index=True)
    score = Column(Integer, default=0)
    clasificacion = Column(String, default="REVISION")
    nivel_riesgo = Column(String, default="MEDIO")
    resultado_json = Column(Text, default="{}")
    fecha = Column(DateTime, default=datetime.utcnow)
