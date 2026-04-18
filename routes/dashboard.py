import json
import logging
from fastapi import APIRouter, Depends, Header, HTTPException
from database import SessionLocal
from models import Lead

router = APIRouter()


def get_api_key(api_key: str = Header(None, alias="api-key")):
    import os
    if not api_key or api_key != os.environ.get("MESAN_API_KEY"):
        raise HTTPException(status_code=403, detail="No autorizado")
    return api_key


@router.get("/dashboard")
async def dashboard(api_key: str = Depends(get_api_key)):

    try:
        db = SessionLocal()
        leads = db.query(Lead).all()
        db.close()

        total = len(leads)
        criticos = len([l for l in leads if l.clasificacion == "ALTO"])
        pagados = len([l for l in leads if l.estatus == "pagado"])
        nuevos = len([l for l in leads if l.estatus == "nuevo"])

        historial = [
            {
                "fecha": l.fecha.isoformat() if hasattr(l.fecha, "isoformat") else str(l.fecha),
                "score": l.score or 0,
                "clasificacion": l.clasificacion or "N/A"
            }
            for l in leads
        ]

        return {
            "total": total,
            "criticos": criticos,
            "pagados": pagados,
            "nuevos": nuevos,
            "historial": historial
        }

    except Exception as e:
        logging.error(f"Error en dashboard: {e}")
        return {"error": "Error obteniendo datos"}
