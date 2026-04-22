# routes/dashboard.py

import logging
from fastapi import APIRouter, Header, HTTPException
from datetime import datetime, timedelta

router = APIRouter()

try:
    from database import SessionLocal
    from models import Lead
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False
    logging.warning("DB no disponible en dashboard")


def verificar_key(api_key: str):
    import os
    expected = os.getenv("MESAN_API_KEY", "mesan2026mexicali")
    if api_key != expected:
        raise HTTPException(status_code=403, detail="API Key invalida")


@router.get("/dashboard")
async def dashboard(api_key: str = Header(None, alias="api-key")):
    verificar_key(api_key)

    if not DB_AVAILABLE:
        return {
            "total": 0,
            "criticos": 0,
            "pagados": 0,
            "nuevos_hoy": 0,
            "impacto_total": 0,
            "error": "DB no disponible"
        }

    try:
        db = SessionLocal()
        leads = db.query(Lead).all()

        criticosList = ["ALTO", "CRISIS FINANCIERA", "RIESGO OPERATIVO", "RIESGO LEGAL"]

        hoy = datetime.utcnow().date()
        nuevos_hoy = [
            l for l in leads
            if l.fecha and l.fecha.date() == hoy
        ]

        impacto_total = sum(
            int(l.impacto_max or 0) for l in leads
        )

        db.close()

        return {
            "total": len(leads),
            "criticos": len([l for l in leads if l.clasificacion in criticosList]),
            "pagados": len([l for l in leads if l.estatus == "pagado"]),
            "nuevos_hoy": len(nuevos_hoy),
            "impacto_total": impacto_total,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Error dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/leads-por-dia")
async def leads_por_dia(api_key: str = Header(None, alias="api-key")):
    verificar_key(api_key)

    if not DB_AVAILABLE:
        return {"data": []}

    try:
        db = SessionLocal()
        leads = db.query(Lead).all()
        db.close()

        conteo = {}
        for l in leads:
            if l.fecha:
                dia = l.fecha.date().isoformat()
                conteo[dia] = conteo.get(dia, 0) + 1

        data = [{"fecha": k, "total": v} for k, v in sorted(conteo.items())]

        return {"data": data}

    except Exception as e:
        logging.error(f"Error leads por dia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# v2 — actualizado
