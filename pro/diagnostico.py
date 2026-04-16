from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

diagnostico_router = APIRouter()

class Empleado(BaseModel):
    nombre: str
    sueldo_base: float
    percepciones_gravables: float

class DiagnosticoRequest(BaseModel):
    empleados: List[Empleado]

def evaluar(emp):
    resultados = []

    if emp["percepciones_gravables"] > emp["sueldo_base"] * 1.5:
        resultados.append({
            "empleado": emp["nombre"],
            "riesgo": "CRITICO",
            "mensaje": "Subdeclaración IMSS detectada",
            "solucion": "Ajustar SBC conforme a percepciones",
            "fundamento": "Art. 27 LSS"
        })

    if emp["percepciones_gravables"] == 0:
        resultados.append({
            "empleado": emp["nombre"],
            "riesgo": "CRITICO",
            "mensaje": "Empleado sin cotización en IMSS",
            "solucion": "Registrar alta inmediata",
            "fundamento": "Art. 15 LSS"
        })

    return resultados

@diagnostico_router.post("/diagnostico")
async def diagnostico(data: DiagnosticoRequest):
    resultados = []

    for emp in data.empleados:
        resultados.extend(evaluar(emp.dict()))

    return {
        "total_empleados": len(data.empleados),
        "resultados": resultados
    }
