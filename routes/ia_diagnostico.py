# -*- coding: utf-8 -*-

from fastapi import APIRouter
from pydantic import BaseModel, Field
import os
import httpx
import unicodedata
import logging
import traceback

from core.preguntas import generar_preguntas

router = APIRouter()

# =========================
# INPUT MODEL
# =========================
class InputAI(BaseModel):
    texto: str
    respuestas: dict = Field(default_factory=dict)

# =========================
# NORMALIZAR TEXTO
# =========================
def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto

# =========================
# DETECTAR INDUSTRIA
# =========================
def detectar_industria(texto: str) -> str:
    if any(p in texto for p in ["clinica", "hospital", "medico", "cofepris"]):
        return "SALUD"
    if any(p in texto for p in ["seguridad", "guardia", "vigilancia"]):
        return "SEGURIDAD"
    if any(p in texto for p in ["obra", "construccion", "albanil"]):
        return "CONSTRUCCION"
    if any(p in texto for p in ["restaurante", "comida", "cocina"]):
        return "ALIMENTOS"
    if any(p in texto for p in ["fabrica", "produccion"]):
        return "MANUFACTURA"
    if any(p in texto for p in ["tienda", "retail", "comercio"]):
        return "RETAIL"
    if any(p in texto for p in ["banco", "credito", "financiera"]):
        return "FINANCIERO"
    if any(p in texto for p in ["logistica", "transporte", "almacen"]):
        return "LOGISTICA"
    if any(p in texto for p in ["software", "app", "saas"]):
        return "TECNOLOGIA"
    if any(p in texto for p in ["servicio", "outsourcing"]):
        return "SERVICIOS"
    return "GENERAL"

# =========================
# ANALISIS BASE
# =========================
def analizar_fallback(texto: str, respuestas: dict, industria: str):
    causas = []
    impacto = 0

    if "imss" in texto:
        causas.append("Incumplimiento IMSS")
        impacto += 80000

    if "sat" in texto or "embargo" in texto:
        causas.append("Riesgo fiscal SAT")
        impacto += 200000

    if "bloqueo" in texto or "cuenta" in texto:
        causas.append("Bloqueo de cuentas bancarias")
        impacto += 150000

    if industria == "SEGURIDAD":
        causas.append("Falta de permisos regulatorios")
        impacto += 150000

    if impacto == 0:
        impacto = 25000

    return causas, impacto

# =========================
# ANTHROPIC
# =========================
async def llamar_anthropic(texto, industria, impacto, riesgo, causas, respuestas):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    prompt = f"""
Analiza como consultor experto en Mexico:

Industria: {industria}
Problema: {texto}
Riesgo: {riesgo}
Impacto: {impacto}
Causas: {causas}
"""

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if r.status_code == 200:
                return r.json()["content"][0]["text"]

            logging.error(f"Anthropic error {r.status_code}: {r.text}")

    except Exception:
        logging.error(traceback.format_exc())

    return ""

# =========================
# ENDPOINT
# =========================
@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = normalizar(data.texto)
    respuestas = data.respuestas

    industria = detectar_industria(texto)
    causas, impacto = analizar_fallback(texto, respuestas, industria)

    # =========================
    # RIESGO
    # =========================
    if impacto > 300000:
        riesgo = "CRITICO"
    elif impacto > 100000:
        riesgo = "ALTO"
    elif impacto > 50000:
        riesgo = "MEDIO"
    else:
        riesgo = "BAJO"

    impacto_min = impacto
    impacto_max = int(impacto * 2.5)

    # =========================
    # IA
    # =========================
    analisis_ai = await llamar_anthropic(
        texto, industria, impacto, riesgo, causas, respuestas
    )

    # =========================
    # PREGUNTAS
    # =========================
    preguntas = generar_preguntas(industria, texto, riesgo)

    # =========================
    # WHATSAPP
    # =========================
    whatsapp = (
        f"MESAN Omega - ALERTA {riesgo}\n\n"
        f"Detectamos riesgo en tu operacion.\n"
        f"Impacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
        f"Responde SI y te digo como resolverlo en 30 dias."
    )

    # =========================
    # LOGGING
    # =========================
    logging.info(f"Diagnostico | {industria} | {riesgo} | ${impacto}")

    # =========================
    # RESPONSE FINAL
    # =========================
    return {
        "ok": True,
        "industria": industria,
        "riesgo": riesgo,
        "impacto": impacto,
        "impacto_min": impacto_min,
        "impacto_max": impacto_max,
        "causas": causas,
        "preguntas": preguntas,
        "analisis_ai": analisis_ai,

        "decision": {
            "accion_inmediata": causas[0] if causas else "Revision inmediata",
            "prioridad": "URGENTE" if riesgo in ["CRITICO", "ALTO"] else "MEDIA",
            "ventana_dias": 7 if riesgo == "CRITICO" else 15 if riesgo == "ALTO" else 30
        },

        "whatsapp": whatsapp,

        "cierre": f"Atencion especializada requerida en {industria}. Podemos ayudarte a resolverlo en 30 dias."
    }
