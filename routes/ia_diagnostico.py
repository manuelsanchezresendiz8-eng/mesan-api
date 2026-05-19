# -*- coding: utf-8 -*-
# routes/ia_diagnostico.py -- MESAN Ω v4.0

from fastapi import APIRouter
from pydantic import BaseModel, Field
import unicodedata
import logging
import os
import httpx
import traceback
from datetime import datetime

from core.preguntas import generar_preguntas

try:
    from services.refine_engine import generar_refinamiento
except Exception:
    generar_refinamiento = None

router = APIRouter()


class InputAI(BaseModel):
    texto: str
    respuestas: dict = Field(default_factory=dict)


def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return texto.encode("ascii", "ignore").decode("utf-8")


def detectar_industria(texto: str) -> str:
    t = texto.lower()

    sectores = {
        "SEGURIDAD": [
            "seguridad privada", "guardia", "sspc", "custodia"
        ],
        "LABORAL": [
            "huelga", "sindicato", "paro laboral"
        ],
        "FINANCIERO": [
            "deuda", "liquidez", "flujo", "credito",
            "cartera vencida", "banco", "nomina",
            "sat", "isr", "iva"
        ],
        "LOGISTICA": [
            "logistica", "trailer", "flete", "transporte"
        ],
        "MANUFACTURA": [
            "maquila", "planta", "produccion", "fabrica"
        ],
        "SERVICIOS_APOYO": [
            "repse", "outsourcing", "staffing"
        ]
    }

    for sector, palabras in sectores.items():
        if any(p in t for p in palabras):
            return sector

    return "GENERAL"


def aplicar_colision_riesgos(texto, impacto, score):

    t = texto.lower()

    if ("bloqueo" in t or "embargo" in t) and "nomina" in t:
        impacto = int(impacto * 1.8)
        score += 12

    if "sat" in t and ("bloqueo" in t or "embargo" in t):
        impacto = int(impacto * 2.0)
        score += 15

    return int(impacto), min(score, 99)


def analizar_fallback(texto, respuestas, industria):

    t = texto.lower()

    causas = []
    impacto = 0
    score = 25

    if any(p in t for p in [
        "bloqueo",
        "embargo",
        "cuentas bloqueadas",
        "inmovilizacion",
        "pae"
    ]):
        causas.append(
            "Inmovilizacion bancaria detectada -- continuidad operativa comprometida"
        )
        impacto += 1200000
        score += 30

    if "sat" in t:
        causas.append(
            "Credito fiscal o presion SAT detectada"
        )
        impacto += 800000
        score += 20

    if "nomina" in t:
        causas.append(
            "Presion sobre cumplimiento de nomina"
        )
        impacto += 350000
        score += 18

    if "imss" in t:
        causas.append(
            "Posible contingencia IMSS detectada"
        )
        impacto += 280000
        score += 10

    if "infonavit" in t:
        causas.append(
            "Omisiones patronales INFONAVIT detectadas"
        )
        impacto += 450000
        score += 15

    if "cartera vencida" in t:
        causas.append(
            "Cartera vencida critica -- flujo comprometido"
        )
        impacto += 600000
        score += 15

    if any(p in t for p in [
        "linea de credito",
        "prestamo bancario",
        "deuda bancaria"
    ]):
        causas.append(
            "Nivel elevado de apalancamiento financiero"
        )
        impacto += 400000
        score += 12

    impacto, score = aplicar_colision_riesgos(
        t,
        impacto,
        score
    )

    if impacto == 0:
        impacto = 25000

    return causas, impacto


def ajustar_por_respuestas(causas, impacto, respuestas, industria):

    if respuestas.get("acta") == "Acta levantada":
        causas.append(
            "Posible proceso sancionador activo"
        )
        impacto += 120000

    if respuestas.get("empleados") == "Mas de 20":
        causas.append(
            "Alto volumen de personal con posible exposicion"
        )
        impacto += 100000

    return causas, impacto


async def llamar_anthropic(
    texto,
    industria,
    impacto,
    riesgo,
    causas
):

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return ""

    causas_txt = " | ".join(causas[:4])

    fecha_hoy = datetime.now().strftime("%d %b %Y")

    impacto_bajo = int(impacto * 0.40)
    impacto_probable = int(impacto * 0.75)
    impacto_critico = int(impacto)

    prompt = f"""
Actua como CRO corporativo especializado en crisis empresariales.

Fecha: {fecha_hoy}
Industria: {industria}
Riesgo: {riesgo}
Impacto: ${impacto:,} MXN

Factores:
{causas_txt}

Caso:
{texto}

ESTRUCTURA OBLIGATORIA:

## 1. HALLAZGO CRITICO

## 2. RIESGO DE CONTINUIDAD

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,}
- Probable: ${impacto_probable:,}
- Critico: ${impacto_critico:,}

## 4. VENTANA DE COLAPSO

## 5. ACCIONES EJECUTIVAS

## 6. PROTOCOLO DE SUPERVIVENCIA

## 7. DECISION CEO
"""

    try:

        async with httpx.AsyncClient(timeout=40) as client:

            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1400,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )

            if response.status_code == 200:

                contenido = response.json()["content"][0]["text"]

                if "## 7. DECISION CEO" not in contenido:
                    contenido += (
                        "\n\n## 7. DECISION CEO\n"
                        "Ejecutar protocolo inmediato."
                    )

                return contenido

            logging.error(
                f"Claude Error: {response.text}"
            )

    except Exception:
        logging.error(traceback.format_exc())

    return ""


@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = normalizar(data.texto)
    respuestas = data.respuestas

    industria = detectar_industria(texto)

    causas, impacto = analizar_fallback(
        texto,
        respuestas,
        industria
    )

    causas, impacto = ajustar_por_respuestas(
        causas,
        impacto,
        respuestas,
        industria
    )

    riesgo = "BAJO"

    if industria == "FINANCIERO":

        tiene_deuda = any(
            p in texto for p in ["deuda", "banco"]
        )

        tiene_cartera = any(
            p in texto for p in [
                "cartera vencida",
                "dejaron de pagar"
            ]
        )

        tiene_isr = any(
            p in texto for p in [
                "isr",
                "sat"
            ]
        )

        tiene_lineas = any(
            p in texto for p in [
                "linea de credito",
                "lineas de credito"
            ]
        )

        tiene_nomina = "nomina" in texto

        factores_criticos = sum([
            tiene_deuda,
            tiene_cartera,
            tiene_isr,
            tiene_lineas,
            tiene_nomina
        ])

        if factores_criticos >= 3:
            causas.append(
                "Estres financiero severo"
            )
            impacto += 500000

        if tiene_cartera:
            causas.append(
                "Dependencia critica de cobranza"
            )
            impacto += 400000

        if tiene_isr:
            causas.append(
                "Contingencia fiscal prioritaria"
            )
            impacto += 350000

        if tiene_lineas and tiene_nomina:
            causas.append(
                "Capital de trabajo agotado"
            )
            impacto += 300000

    if impacto >= 1500000:
        riesgo = "CRITICO"

    elif impacto >= 600000:
        riesgo = "ALTO"

    elif impacto >= 180000:
        riesgo = "MEDIO"

    else:
        riesgo = "BAJO"

    impacto_min = impacto
    impacto_max = int(impacto * 2.5)

    analisis_ai = await llamar_anthropic(
        texto,
        industria,
        impacto,
        riesgo,
        causas
    )

    preguntas = generar_preguntas(
        industria,
        texto,
        riesgo
    )

    consecuencias = {
        "FINANCIERO": [
            "Tension de liquidez progresiva",
            "Riesgo de atraso operativo",
            "Necesidad de reestructura financiera"
        ]
    }.get(
        industria,
        [
            "Escalamiento operativo",
            "Posibles sanciones",
            "Perdida operativa potencial"
        ]
    )

    plan_30 = [
        "Semana 1: Auditoria preventiva",
        "Semana 2: Regularizacion operativa",
        "Semana 3: Blindaje financiero",
        "Semana 4: Estabilizacion"
    ]

    refinamiento = {}

    if generar_refinamiento:
        try:

            refinamiento = generar_refinamiento({
                "industria": industria,
                "riesgo": riesgo,
                "impacto": impacto,
                "causas": causas
            })

        except Exception:
            pass

    disclaimer = (
        "Analisis preventivo generado por "
        "MESAN Omega Intelligence Engine."
    )

    logging.info(
        f"Diagnostico | {industria} | "
        f"{riesgo} | ${impacto:,}"
    )

    return {
        "ok": True,
        "industria": industria,
        "riesgo": riesgo,
        "impacto": impacto,
        "impacto_min": impacto_min,
        "impacto_max": impacto_max,
        "causas": causas,
        "consecuencias": consecuencias,
        "preguntas": preguntas,
        "analisis_ai": analisis_ai,
        "plan_30_dias": plan_30,
        "disclaimer": disclaimer,
        "refinamiento": refinamiento
    }
