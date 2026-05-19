# -*- coding: utf-8 -*-
# routes/ia_diagnostico.py -- MESAN Ω v5.0 ENTERPRISE
# Arquitectura corregida anti-truncamiento + CRO Crisis Engine

from fastapi import APIRouter
from pydantic import BaseModel, Field
import unicodedata
import logging
import os
import httpx
import traceback
from datetime import datetime

router = APIRouter()

# =========================================================
# INPUT MODEL
# =========================================================

class InputAI(BaseModel):
    texto: str
    respuestas: dict = Field(default_factory=dict)

# =========================================================
# NORMALIZADOR
# =========================================================

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return texto.encode("ascii", "ignore").decode("utf-8")

# =========================================================
# INDUSTRIAS
# =========================================================

def detectar_industria(texto: str) -> str:

    t = texto.lower()

    sectores = {
        "SEGURIDAD": ["sspc", "guardia", "seguridad privada"],
        "FINANCIERO": ["liquidez", "flujo", "cartera vencida", "banco", "credito"],
        "LABORAL": ["huelga", "sindicato", "paro"],
        "LOGISTICA": ["operadores", "trailer", "flete"],
        "SALUD": ["hospital", "clinica"],
        "SERVICIOS_APOYO": ["repse", "outsourcing"],
    }

    for sector, palabras in sectores.items():
        if any(p in t for p in palabras):
            return sector

    return "GENERAL"

# =========================================================
# ANALISIS FALLBACK
# =========================================================

def analizar_fallback(texto, industria):

    t = texto.lower()

    causas = []
    impacto = 0
    score = 25

    # SAT
    if "sat" in t or "isr" in t:
        causas.append("Contingencia fiscal prioritaria detectada")
        impacto += 800000
        score += 18

    # IMSS
    if "imss" in t:
        causas.append("Exposicion IMSS detectada")
        impacto += 350000
        score += 12

    # INFONAVIT
    if "infonavit" in t:
        causas.append("Omisiones Infonavit detectadas")
        impacto += 450000
        score += 15

    # BLOQUEO
    if any(x in t for x in ["bloqueo", "embargo", "cuentas bloqueadas"]):
        causas.append("Flujo bancario comprometido")
        impacto += 1200000
        score += 25

    # NOMINA
    if "nomina" in t:
        causas.append("Presion sobre cumplimiento de nomina")
        impacto += 450000
        score += 15

    # CARTERA
    if any(x in t for x in ["cartera vencida", "no pagaron"]):
        causas.append("Dependencia critica de cobranza")
        impacto += 850000
        score += 18

    # SSPC
    if "sspc" in t:
        causas.append("Vulnerabilidad regulatoria SSPC")
        impacto += 650000
        score += 15

    # REPSE
    if "repse" in t:
        causas.append("Brecha REPSE detectada")
        impacto += 500000
        score += 14

    # LESION
    if any(x in t for x in ["lesion", "herido", "accidente"]):
        causas.append("Responsabilidad civil operativa")
        impacto += 950000
        score += 20

    # COLISIONES
    if "bloqueo" in t and "nomina" in t:
        impacto = int(impacto * 1.6)
        score += 10

    if "sat" in t and "bloqueo" in t:
        impacto = int(impacto * 1.8)
        score += 12

    if "sspc" in t and "lesion" in t:
        impacto = int(impacto * 2.0)
        score += 15

    impacto = max(impacto, 25000)
    score = min(score, 99)

    return causas, impacto, score

# =========================================================
# MOTOR DE MODO EJECUTIVO
# =========================================================

def detectar_modo(score):

    if score >= 85:
        return "CRO_CRISIS"

    elif score >= 60:
        return "RISK_EXECUTIVE"

    return "PREVENTIVO"

# =========================================================
# COMPRESOR DE BULLETS
# =========================================================

def compactar_bullets(texto):

    lineas = texto.splitlines()

    nuevas = []
    bullets = 0

    for l in lineas:

        if l.strip().startswith("-"):
            bullets += 1

        if bullets > 3 and l.strip().startswith("-"):
            continue

        nuevas.append(l)

    return "\n".join(nuevas)

# =========================================================
# REPARADOR ANTI-TRUNCAMIENTO
# =========================================================

def reparar_respuesta(texto: str):

    if not texto:
        return texto

    cortes = [
        "reestruct",
        "negoci",
        "operac",
        "fiscal",
        "financ",
        "nomina",
        "embarg",
    ]

    for c in cortes:
        if texto.strip().endswith(c):
            texto += "..."

    if not texto.strip().endswith(("---FIN---", ".", "MXN")):
        texto += "\n\n---FIN---"

    return texto

# =========================================================
# GENERADOR CLAUDE
# =========================================================

async def llamar_claude(
    texto,
    industria,
    impacto,
    riesgo,
    causas,
    modo
):

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return ""

    fecha = datetime.now().strftime("%d de %B de %Y")

    impacto_bajo = int(impacto * 0.40)
    impacto_probable = int(impacto * 0.75)

    impacto_critico = max(
        impacto_probable + 250000,
        impacto
    )

    causas_txt = " | ".join(causas[:4])

    prompt = f"""
Actua como CRO (Chief Restructuring Officer) y advisor ejecutivo.

Fecha: {fecha}
Industria: {industria}
Modo: {modo}
Nivel Riesgo: {riesgo}

Situacion:
{texto}

Factores:
{causas_txt}

Escenarios:
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

REGLAS:
- MAXIMO 70 palabras por seccion
- NO usar tablas markdown
- NO cortar frases
- NO usar recomendaciones genericas
- Cada accion debe incluir:
  accion + objetivo + plazo

ESTRUCTURA OBLIGATORIA:

## 1. HALLAZGO CRITICO
[2 lineas maximo]

## 2. RIESGO DE CONTINUIDAD
[impacto operativo inmediato]

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

## 4. VENTANA DE COLAPSO OPERATIVO
[fechas y consecuencias]

## 5. ACCIONES EJECUTIVAS PRIORITARIAS

🔴 ACCION 24H
- Ejecutar:
- Objetivo:
- Plazo:

🟠 ACCION 72H
- Ejecutar:
- Objetivo:
- Plazo:

🟡 ACCION SEMANA 1
- Ejecutar:
- Objetivo:
- Plazo:

## 6. DECISION CEO
[orden ejecutiva final]

Analisis referencial sujeto a validacion especializada.
"""

try:
    async with httpx.AsyncClient(timeout=45) as client:

        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

        if r.status_code == 200:

            respuesta = r.json()["content"][0]["text"]

            # VALIDADORES

            if len(respuesta) < 300:
                return "Error de convergencia ejecutiva."

            if "## 5." not in respuesta:
                return "Respuesta incompleta."

            if respuesta.count("##") < 5:
                return "Estructura insuficiente."

            respuesta = compactar_bullets(respuesta)
            respuesta = reparar_respuesta(respuesta)

            return respuesta

        logging.error(f"Claude Error: {r.text}")

except Exception:
    logging.error(traceback.format_exc())

return ""
