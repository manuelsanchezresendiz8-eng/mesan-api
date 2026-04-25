from fastapi import APIRouter
from pydantic import BaseModel
import unicodedata

router = APIRouter(prefix="/ai", tags=["AI"])


class InputAI(BaseModel):
    texto: str


def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


@router.post("/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = normalizar(data.texto)

    impacto = 0
    causas = []

    # --- MOTOR DE DETECCIÓN ---
    if "incapacitado" in texto or "incapacidad" in texto:
        causas.append("Trabajador incapacitado laborando — fraude IMSS y Capital Constitutivo")
        impacto += 250000

    if "imss" in texto:
        causas.append("Incumplimiento IMSS — multas y capitales constitutivos")
        impacto += 80000

    if "cfdi" in texto or "factura" in texto:
        causas.append("Inconsistencias CFDI — riesgo de auditoría SAT")
        impacto += 120000

    if "repse" in texto:
        causas.append("REPSE vencido — responsabilidad solidaria activa")
        impacto += 150000

    if "contrato" in texto:
        causas.append("Sin contratos laborales — vulnerabilidad legal")
        impacto += 50000

    if "clausura" in texto or "cofepris" in texto:
        causas.append("Bloqueo operativo — pérdida inmediata de flujo")
        impacto += 300000

    if "sat" in texto or "auditoria" in texto:
        causas.append("Auditoría SAT activa — riesgo de embargo")
        impacto += 200000

    # --- CLASIFICACIÓN ---
    if impacto > 300000:
        riesgo = "CRÍTICO"
        prob = "ALTA"
    elif impacto > 100000:
        riesgo = "ALTO"
        prob = "ALTA"
    elif impacto > 50000:
        riesgo = "MEDIO"
        prob = "MEDIA"
    else:
        riesgo = "BAJO"
        prob = "BAJA"

    if not causas:
        causas = ["Requiere análisis más detallado"]

    # --- RESPUESTA ESTRUCTURADA ---
    return {
        "ok": True,
        "riesgo": riesgo,
        "impacto": impacto,
        "probabilidad": prob,
        "causas": causas,
        "plan_30_dias": [
            "Semana 1: Auditoría interna urgente",
            "Semana 2: Corrección legal y laboral",
            "Semana 3: Ajuste fiscal y CFDI",
            "Semana 4: Blindaje operativo MESAN Ω"
        ],
        "mensaje": f"Riesgo {riesgo} con impacto estimado de ${impacto:,} MXN",
        "cierre": "Podemos corregir esto en 30 días. ¿Agendamos llamada hoy?"
    }
