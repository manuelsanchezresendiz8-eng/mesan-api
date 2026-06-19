from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from database import SessionLocal
from models import Lead

router = APIRouter()

class Interaccion(BaseModel):
    nombre: str
    email: str
    telefono: str
    texto_inicial: str
    respuestas: list
    riesgo: str
    impacto_min: int
    impacto_max: int

@router.post("/crm/interaccion")
async def guardar_interaccion(data: Interaccion):
    db = SessionLocal()

    lead = Lead(
        nombre=data.nombre,
        email=data.email,
        telefono=data.telefono,
        score=data.impacto_max,
        clasificacion=data.riesgo,
        impacto_min=data.impacto_min,
        impacto_max=data.impacto_max,
        estatus="caliente",
        fecha=datetime.now()
    )

    db.add(lead)
    db.commit()
    db.close()

    return {"ok": True}
