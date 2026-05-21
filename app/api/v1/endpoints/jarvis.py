# app/api/v1/endpoints/jarvis.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.agents.jarvis_market_agent import JarvisMarketAgent

router = APIRouter(prefix="/jarvis", tags=["Engine Jarvis"])

class LeadSchema(BaseModel):
    nombre: str
    sector: str
    empleados: int
    ubicacion: str
    puesto_contacto: str

def verificar_privilegios_ejecutivos():
    pass

@router.post("/analizar-prospecto", status_code=status.HTTP_200_OK)
async def procesar_inteligencia_prospecto(
    payload: LeadSchema,
    autorizado: bool = Depends(verificar_privilegios_ejecutivos)
):
    agente = JarvisMarketAgent()
    try:
        analisis = await agente.analizar_lead_y_generar_pitch(payload.dict())
        return {
            "status": "success",
            "meta_analisis": {"prospecto": payload.nombre, "sector_clave": payload.sector},
            "inteligencia_generada": analisis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Jarvis: {str(e)}")
