from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["AI"])

class InputAI(BaseModel):
    texto: str

@router.post("/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = data.texto.lower()

    impacto = 0
    causas = []
    riesgo = "MEDIO"
    prob = "MEDIA"

    # --- REGLAS DE DETECCIÓN ---
    if "incapacitado" in texto or "incapacidad" in texto:
        causas.append("Trabajador incapacitado laborando — fraude al IMSS y riesgo de Capital Constitutivo")
        impacto += 250000

    if "imss" in texto:
        causas.append("Incumplimiento IMSS — exposición a capitales constitutivos y multas")
        impacto += 80000

    if "cfdi" in texto or "factura" in texto:
        causas.append("Inconsistencias en CFDI — riesgo de auditoría SAT")
        impacto += 120000

    if "repse" in texto:
        causas.append("REPSE vencido — responsabilidad solidaria activa")
        impacto += 150000

    if "contrato" in texto:
        causas.append("Ausencia de contratos laborales — vulnerabilidad legal")
        impacto += 50000

    if "clausura" in texto or "cofepris" in texto:
        causas.append("Bloqueo operativo — pérdida inmediata de flujo")
        impacto += 300000

    if "sat" in texto or "auditoria" in texto or "auditoría" in texto:
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

    # --- RESPUESTA ---
    respuesta = f"""RIESGO: {riesgo}

CAUSAS DETECTADAS:
{chr(10).join(f"• {c}" for c in causas)}

IMPACTO ECONÓMICO ESTIMADO: ${impacto:,} MXN

PROBABILIDAD DE AUDITORÍA: {prob}

PLAN 30 DÍAS:
Semana 1: Auditoría interna urgente
Semana 2: Corrección legal y laboral
Semana 3: Ajuste fiscal y CFDI
Semana 4: Blindaje operativo MESAN Ω

RECOMENDACIÓN FINAL: Actuar de inmediato para evitar escalamiento

CIERRE: Podemos corregir esto en 30 días. ¿Agendamos llamada hoy?"""

    return {
        "ok": True,
        "riesgo": riesgo,
        "impacto": impacto,
        "probabilidad": prob,
        "causas": causas,
        "respuesta": respuesta
    }
