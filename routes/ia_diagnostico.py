import os
from fastapi import APIRouter
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


@router.post("/ai/diagnostico")
async def ai_diagnostico(data: dict):

    texto = data.get("texto", "")

    if not texto:
        return {"error": "Se requiere texto del caso"}

    prompt = f"""
Eres auditor fiscal y laboral experto en México (IMSS, SAT, REPSE, CFDI).

Analiza este caso empresarial:
{texto}

Responde EXACTAMENTE con este formato, sin texto adicional:

RIESGO: (CRÍTICO / ALTO / MEDIO / BAJO)
CAUSAS: (lista las causas principales)
IMPACTO: (monto estimado en pesos MXN)
PROBABILIDAD DE AUDITORÍA: (ALTA / MEDIA / BAJA)
PLAN 30 DÍAS:
  Semana 1: (acción)
  Semana 2: (acción)
  Semana 3: (acción)
  Semana 4: (acción)
RECOMENDACIÓN FINAL: (una línea directa)
CIERRE: (mensaje corto invitando a contratar MESAN Ω)
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        respuesta = res.choices[0].message.content
        return {"ok": True, "respuesta": respuesta}

    except Exception as e:
        return {"ok": False, "respuesta": _fallback(texto), "error": str(e)}


def _fallback(texto: str) -> str:
    t = texto.lower()
    impacto = 0
    problemas = []

    if "imss" in t:
        problemas.append("Incumplimiento IMSS")
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
