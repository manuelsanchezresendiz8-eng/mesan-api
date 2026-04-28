from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.mesan_engine import MesanOmegaEngine

router = APIRouter()

class EmpresaInput(BaseModel):
    nomina: float = 0
    empleados: int = 1
    horas_semanales: float = 40
    bajas: int = 0
    salario_promedio: float = 0
    costo_reclutamiento: float = 0
    rotacion: float = 0
    cumplimiento: float = 1.0

@router.post("/api/v1/analisis")
def analizar(data: EmpresaInput):
    engine = MesanOmegaEngine(data.dict())
    resultado = engine.ejecutar()

    riesgos = []
    if resultado["nearshoring"]["riesgo"] in ["ALTO", "CRÍTICO"]:
        riesgos.append("Exceso de jornada laboral — sobrecosto operativo")
    if resultado["rotacion"]["riesgo"] == "ALTO":
        riesgos.append("Alta rotación de personal — pérdida de capital humano")

    return {
        "status": "success",
        "riesgos": riesgos,
        "analisis": resultado
    }
