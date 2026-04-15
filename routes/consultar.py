from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
import uuid
from datetime import datetime

from utils.finanzas import calcular_finanzas, calcular_precio_sugerido

router = APIRouter()

consultas_db = []

@router.post("/consultar")
async def consultar(data: dict):

    precio_cliente = float(data.get("precio_cliente", 0))
    precio_competencia = float(data.get("precio_competencia", 0))
    sueldo = float(data.get("sueldo", 12000))

    finanzas = calcular_finanzas(precio_cliente, 1, sueldo)
    precio_min = calcular_precio_sugerido(sueldo, 0.25)

    if precio_competencia < precio_min:
        semaforo = "ROJO"
        diagnostico = "Competencia insostenible — opera por debajo del costo real"
        recomendacion = "NO bajar precio. Evidenciar riesgo del competidor."
    elif precio_cliente > precio_competencia:
        semaforo = "AMARILLO"
        diagnostico = "Precio superior al mercado. Requiere justificación de valor."
        recomendacion = "Defender precio con diferenciación o ajustar ligeramente."
    else:
        semaforo = "VERDE"
        diagnostico = "Precio competitivo y sostenible."
        recomendacion = "Escalar operación."

    consulta = {
        "id": str(uuid.uuid4()),
        "fecha": datetime.now().isoformat(),
        "precio_cliente": precio_cliente,
        "precio_competencia": precio_competencia,
        "semaforo": semaforo,
        "diagnostico": diagnostico
    }

    consultas_db.append(consulta)

    return {
        "ok": True,
        "semaforo": semaforo,
        "diagnostico": diagnostico,
        "recomendacion": recomendacion,
        "finanzas": finanzas,
        "precio_minimo": precio_min
    }


@router.get("/consultas")
async def historial():
    return {"consultas": consultas_db[::-1]}
