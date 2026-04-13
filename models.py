from sqlalchemy import Column, String, Integer
from database import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column("id", String, primary_key=True, index=True)
    nombre = Column("nombre", String)
    email = Column("email", String)
    telefono = Column("telefono", String)
    score = Column("score", Integer)
    clasificacion = Column("clasificacion", String)
    impacto_min = Column("impacto_min", Integer)
    impacto_max = Column("impacto_max", Integer)
    estatus = Column("estatus", String)
    fecha = Column("fecha", String)
