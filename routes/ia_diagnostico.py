import os
import httpx
from fastapi import APIRouter

router = APIRouter()

@router.post("/ai/diagnostico")
async def ai_diagnostico(data: dict):

    texto = data.get("texto", "")
    if not texto:
        return {"error": "Se requiere texto del caso"}

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    prompt = f"""Eres auditor fiscal y laboral experto en México (IMSS, SAT, REPSE, CFDI).

Analiza este caso empresarial:
{texto}

Responde EXACTAMENTE con este formato:

RIESGO: (CRÍTICO / ALTO / MEDIO / BAJO)
CAUSAS: (lista las causas principales con detalle técnico)
IMPACTO: (monto estimado en pesos MXN con justificación)
PROBABILIDAD DE AUDITORÍA: (ALTA / MEDIA / BAJA con razón)
PLAN 30 DÍAS:
  Semana 1: (acción concreta)
  Semana 2: (acción concreta)
  Semana 3: (acción concreta)
  Semana 4: (acción concreta)
RECOMENDACIÓN FINAL: (una línea directa y ejecutiva)
CIERRE: (mensaje corto invitando a contratar MESAN Ω)"""

    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        result = response.json()
        respuesta = result["content"][0]["text"]
        return {"ok": True, "respuesta": respuesta}

    except Exception as e:
        return {"ok": False, "respuesta": _fallback(texto), "error": str(e)}


def _fallback(texto: str) -> str:
    t = texto.lower()
    impacto = 0
    problemas = []

    if "incapacidad" in t:
        problemas.append("Trabajador incapacitado laborando — fraude al IMSS")
        impacto += 250000
    if "imss" in t:
        problemas.append("Incumplimiento IMSS — capitales constitutivos")
        impacto += 80000
    if "cfdi" in t or "factura" in t:
        problemas.append("Inconsistencias fiscales CFDI")
        impacto += 120000
    if "repse" in t:
        problemas.append("REPSE vencido o inexistente")
        impacto += 150000
    if "contrato" in t:
        problemas.append("Sin contratos laborales")
        impacto += 50000
    if "clausura" in t or "cofepris" in t:
        problemas.append("Bloqueo operativo por autoridad")
        impacto += 300000

    nivel = "CRÍTICO" if impacto > 200000 else "ALTO" if impacto > 80000 else "MEDIO"

    return f"""RIESGO: {nivel}
CAUSAS: {", ".join(problemas) or "Requiere análisis detallado"}
IMPACTO: ${impacto:,} MXN estimado
PROBABILIDAD DE AUDITORÍA: {"ALTA" if nivel == "CRÍTICO" else "MEDIA"}
PLAN 30 DÍAS:
  Semana 1: Auditoría interna urgente
  Semana 2: Corrección legal y laboral
  Semana 3: Ajuste fiscal y CFDI
  Semana 4: Blindaje operativo MESAN Ω
RECOMENDACIÓN FINAL: Regularización inmediata antes de que escale
CIERRE: Podemos corregir esto en 30 días. ¿Agendamos llamada hoy?"""
