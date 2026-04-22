# scripts/seed.py

import os
import uuid
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

try:
    from database import SessionLocal, engine, Base
    from models import Lead
    Base.metadata.create_all(bind=engine)
    DB_AVAILABLE = True
except Exception as e:
    logging.error(f"Error conectando DB: {e}")
    DB_AVAILABLE = False


LEADS_DEMO = [
    {
        "nombre": "Constructora Noroeste",
        "email": "contacto@constructora.com",
        "telefono": "6861234567",
        "giro": "construccion",
        "score": "85",
        "clasificacion": "ALTO",
        "impacto_min": 48000,
        "impacto_max": 120000,
        "estatus": "nuevo"
    },
    {
        "nombre": "Limpieza Industrial BC",
        "email": "info@limpiezabc.com",
        "telefono": "6869876543",
        "giro": "limpieza",
        "score": "60",
        "clasificacion": "MEDIO",
        "impacto_min": 19500,
        "impacto_max": 65000,
        "estatus": "contactado"
    },
    {
        "nombre": "Seguridad Privada Frontera",
        "email": "ops@seguridad.com",
        "telefono": "6865551234",
        "giro": "seguridad",
        "score": "30",
        "clasificacion": "ESTABLE",
        "impacto_min": 5000,
        "impacto_max": 15000,
        "estatus": "cerrado"
    }
]


def seed():
    if not DB_AVAILABLE:
        logging.error("DB no disponible — seed cancelado")
        return

    db = SessionLocal()

    try:
        existentes = db.query(Lead).count()

        if existentes > 0:
            logging.info(f"Ya existen {existentes} leads — seed omitido")
            db.close()
            return

        for data in LEADS_DEMO:
            lead = Lead(
                id=str(uuid.uuid4()),
                nombre=data["nombre"],
                email=data["email"],
                telefono=data["telefono"],
                giro=data["giro"],
                score=data["score"],
                clasificacion=data["clasificacion"],
                impacto_min=data["impacto_min"],
                impacto_max=data["impacto_max"],
                estatus=data["estatus"],
                fecha=datetime.utcnow()
            )
            db.add(lead)

        db.commit()
        logging.info(f"{len(LEADS_DEMO)} leads demo insertados")

    except Exception as e:
        logging.error(f"Error en seed: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()

# v2 — actualizado
