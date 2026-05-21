# services/get_diagnosticos.py
from database import SessionLocal
from models import Lead
import logging

def get_diagnosticos(limit: int = 50, sector: str = None, riesgo: str = None):
    db = SessionLocal()
    try:
        query = db.query(Lead)
        if sector:
            query = query.filter(Lead.giro == sector)
        if riesgo:
            query = query.filter(Lead.clasificacion == riesgo)
        leads = query.order_by(Lead.fecha.desc()).limit(limit).all()
        return [serialize(l) for l in leads]
    except Exception as e:
        logging.error(f"get_diagnosticos error: {e}")
        return []
    finally:
        db.close()

def get_diagnostico_by_id(lead_id: str):
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        return serialize(lead) if lead else None
    except Exception as e:
        logging.error(f"get_diagnostico_by_id error: {e}")
        return None
    finally:
        db.close()

def serialize(l):
    if not l:
        return None
    return {
        "id":            l.id,
        "nombre":        l.nombre,
        "email":         l.email,
        "telefono":      l.telefono,
        "score":         l.score,
        "clasificacion": l.clasificacion,
        "impacto_min":   l.impacto_min,
        "impacto_max":   l.impacto_max,
        "estatus":       l.estatus,
        "fecha":         str(l.fecha) if l.fecha else None,
        "giro":          getattr(l, "giro", None),
        "contexto":      getattr(l, "contexto", None),
        "diagnostico":   getattr(l, "diagnostico", None),
    }
