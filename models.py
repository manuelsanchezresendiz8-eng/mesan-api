from sqlalchemy import Column, String, Integer
from database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    email = Column(String)
    telefono = Column(String)
    score = Column(Integer)
    clasificacion = Column(String)
    impacto_min = Column(Integer)
    impacto_max = Column(Integer)
    estatus = Column(String)
    fecha = Column(String)
