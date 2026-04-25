from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import unicodedata
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.industria import detectar_industria
from core.motor_industrias import analizar_por_industria

router = APIRouter()


class InputAI(BaseModel):
    texto: str


def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = normalizar(data.texto)

    industria = detectar_industria(texto)

    causas, impacto, preguntas, consecuencias = analizar_por_industria(texto, industria)

    if impacto > 300000:
        riesgo = "CRÍTICO"
        prob = "ALTA"
        tendencia = "CRÍTICO — acción inmediata requerida"
    elif impacto > 150000:
        riesgo = "ALTO"
        prob = "ALTA"
        tendencia = "ALTO — con riesgo de escalar a CRÍTICO"
    elif impacto > 70000:
        riesgo = "MEDIO"
        prob = "MEDIA"
        tendencia = "MEDIO → con tendencia a ALTO"
    else:
        riesgo = "BAJO"
        prob = "BAJA"
        tendencia = "ESTABLE — monitoreo preventivo recomendado"

    impacto_min = impacto
    impacto_max = int(impacto * 3)

    causa_principal = causas[0] if causas else ""

    whatsapp = (
        f"MESAN Ω — ALERTA {industria}\n\n"
        f"Detectamos riesgo {riesgo} en tu operación.\n\n"
        f"{causa_principal}\n\n"
        f"Impacto estimado:\n"
        f"${impacto_min:,} – ${impacto_max:,} MXN\n\n"
        f"Antes de darte la solución exacta necesito confirmar:\n\n"
    )
    for i, p in enumerate(preguntas[:2]):
        whatsapp += f"{i+1}. {p}\n"
    whatsapp += "\nSi quieres lo vemos hoy y te digo exactamente cómo corregirlo en 30 días."

    return {
        "ok": True,
        "riesgo": riesgo,
        "tendencia": tendencia,
        "industria": industria,
        "impacto": impacto,
        "impacto_min": impacto_min,
        "impacto_max": impacto_max,
        "probabilidad": prob,
        "causas": causas,
        "consecuencias": consecuencias,
        "preguntas": preguntas[:3],
        "plan_30_dias": [
            f"Semana 1: Auditoría especializada en sector {industria}",
            "Semana 2: Corrección normativa y regularización inmediata",
            "Semana 3: Alineación fiscal y legal",
            "Semana 4: Blindaje operativo MESAN Ω"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Este caso requiere atención especializada en {industria}. MESAN Ω puede resolverlo en 30 días. ¿Agendamos hoy?"
    }
    
