import os
import logging
from fastapi import APIRouter
from core.engine import sistema_enterprise if False else None

router = APIRouter()

# =========================
# CONFIG GPT
# =========================
USE_GPT = False
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if os.getenv("OPENAI_API_KEY"):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        USE_GPT = True
        logging.info(f"GPT chat activo: {MODEL}")
    except Exception as e:
        logging.error(f"Error OpenAI chat: {e}")

SYSTEM_PROMPT = """
Eres MESAN Omega, asesor experto en nomina, REPSE e IMSS.

Tu objetivo es convertir al usuario en cliente.

Reglas:
- Habla claro, directo y breve
- Detecta perdidas economicas
- Genera urgencia (dinero perdido o riesgo legal)
- NO expliques todo (la solucion completa es de pago)
- Siempre termina con una pregunta que empuje accion
- Maximo 120 palabras

Estructura:
1. Insight (que esta mal)
2. Impacto (dinero o riesgo)
3. Pregunta de cierre
"""

FRASES_CIERRE = [
    "Esto ya te esta costando dinero hoy.",
    "Esto lo vemos en muchas empresas justo antes de una auditoria.",
    "Cada mes que pasa sin corregirlo, el riesgo aumenta.",
    "El IMSS ya detecto esto en empresas similares a la tuya."
]

# =========================
# FALLBACK LOCAL
# =========================
def fallback_local() -> str:
    return (
        "Detectamos posibles irregularidades en tu operacion. "
        "Esto puede estar costándote dinero hoy. "
        "¿Quieres que te explique como corregirlo?"
    )

def detectar_intencion(msg: str) -> str:
    m = msg.lower()
    if "empleado" in m: return "empleados"
    if "precio" in m or "cobro" in m: return "precio"
    if "servicio" in m: return "servicio"
    return "general"

def flujo_local(mensaje: str, contexto: dict) -> dict:
    intent = detectar_intencion(mensaje)

    if intent == "empleados": contexto["empleados"] = mensaje
    elif intent == "precio": contexto["precio"] = mensaje
    elif intent == "servicio": contexto["servicio"] = mensaje

    if all(k in contexto for k in ["empleados", "precio", "servicio"]):
        try:
            from enterprise.enterprise_engine import sistema_enterprise
            resultado = sistema_enterprise(contexto)
            perdida = resultado.get("impacto", {}).get("impacto_min", 12000)
        except Exception:
            perdida = 12000
            resultado = {}

        return {
            "respuesta": f"Detecto que podrias perder ${perdida} MXN al mes. ¿Quieres ver como corregirlo?",
            "cerrar": True,
            "resultado": resultado,
            "contexto": contexto
        }

    if "servicio" not in contexto:
        return {"respuesta": "¿A que se dedica tu empresa?", "contexto": contexto}
    if "empleados" not in contexto:
        return {"respuesta": "¿Cuantos empleados tienes?", "contexto": contexto}
    if "precio" not in contexto:
        return {"respuesta": "¿Cuanto cobras mensual?", "contexto": contexto}

    return {"respuesta": "Cuentame mas sobre tu operacion", "contexto": contexto}

# =========================
# ENDPOINT PRINCIPAL
# =========================
@router.post("/chat")
def chat(payload: dict):

    mensaje = payload.get("mensaje", "")
    historial = payload.get("historial", [])
    contexto = payload.get("contexto", {})

    if USE_GPT:
        try:
            import random
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += historial[-10:]
            messages.append({"role": "user", "content": mensaje[:2000]})
