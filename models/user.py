# models/user.py

import os
from datetime import datetime

try:
    from sqlalchemy import Column, String, DateTime, Boolean
    from database import Base

    class User(Base):
        __tablename__ = "users"

        id = Column(String, primary_key=True)
        nombre = Column(String, nullable=True)
        email = Column(String, nullable=False)
        password_hash = Column(String, nullable=True)
        plan = Column(String, default="free")
        estatus = Column(String, default="activo")
        api_key = Column(String, nullable=True)
        company_id = Column(String, nullable=True)
        fecha_registro = Column(DateTime, default=datetime.utcnow)
        fecha_pago = Column(DateTime, nullable=True)
        es_admin = Column(Boolean, default=False)

        def to_dict(self):
            return {
                "id": self.id,
                "nombre": self.nombre,
                "email": self.email,
                "plan": self.plan,
                "estatus": self.estatus,
                "company_id": self.company_id,
                "es_admin": self.es_admin,
                "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None
            }

except Exception as e:
    import logging
    logging.warning(f"SQLAlchemy no disponible para User: {e}")

    class User:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def to_dict(self):
            return self.__dict__

# v2 — actualizado
