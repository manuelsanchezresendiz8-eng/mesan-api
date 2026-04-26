from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os
import httpx
import unicodedata
import logging
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.preguntas import generar_preguntas

router = APIRouter()

class InputAI(BaseModel):
    texto: str
    respuestas: dict = {}

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto

def detectar_industria(texto: str) -> str:
    t = texto.lower()
    if any(p in t for p in ["consultorio", "consultario", "medico", "clinica", "cofepris", "cofepreis", "farmacia", "hospital", "salud", "doctor"]):
        return "SALUD"
    if any(p in t for p in ["tienda", "ropa", "retail", "mostrador", "comercio"]):
        return "RETAIL"
    if any(p in t for p in ["obra", "construccion", "albanil", "contratista", "edificio"]):
        return "CONSTRUCCION"
    if any(p in t for p in ["restaurante", "cocina", "alimentos", "comida", "cafe"]):
        return "ALIMENTOS"
    if any(p in t for p in ["fabrica", "produccion", "maquinaria", "planta", "linea"]):
        return "MANUFACTURA"
    return "GENERAL"

def analizar_fallback(texto: str, respuestas: dict, industria: str):
    causas = []
    impacto = 0

    if industria == "SALUD":
        if any(p in texto for p in ["cofepris", "cofepreis", "inspeccion", "revision", "visita"]):
            causas.append("Revisión activa COFEPRIS — riesgo de clausura sanitaria")
            impacto += 90000
        if any(p in texto for p in ["consultorio", "medico", "clinica"]):
            causas.append("Operación médica bajo inspección — validación NOM obligatoria")
            impacto += 40000
        if respuestas.get("acta") == "Acta levantada":
            causas.append("Acta de inspección levantada — proceso sancionador iniciado")
            impacto += 70000
        if respuestas.get("aviso") == "No":
            causas.append("Sin aviso de funcionamiento — operación irregular ante COFEPRIS")
            impacto += 50000
        if respuestas.get("expediente") == "No":
            causas.append("Sin expediente sanitario — sin defensa técnica ante inspección")
            impacto += 60000

    elif industria == "CONSTRUCCION":
        if "obra" in texto:
            causas.append("Riesgo IMSS en obra — capitales constitutivos")
            impacto += 150000
        if respuestas.get("imss_obra") == "Ninguno":
            causas.append("Trabajadores sin IMSS en obra")
            impacto += 100000
        if respuestas.get("repse") in ["Vencido", "No tengo"]:
            causas.append("REPSE vencido o inexistente")
            impacto += 80000

    elif industria == "RETAIL":
        if "rotacion" in texto or "empleados" in texto:
            causas.append("Alta rotación laboral — riesgo de demandas")
            impacto += 60000
        if respuestas.get("contratos") == "No":
            causas.append("Sin contratos laborales firmados")
            impacto += 40000

    elif industria == "ALIMENTOS":
        if any(p in texto for p in ["cofepris", "inspeccion"]):
            causas.append("Inspección sanitaria activa — riesgo de clausura")
            impacto += 100000
        if respuestas.get("licencia") in ["Vencida", "No"]:
            causas.append("Licencia sanitaria vencida o inexistente")
            impacto += 80000

    elif industria == "MANUFACTURA":
        if any(p in texto for p in ["produccion", "maquinaria", "linea"]):
            causas.append("Falla en línea de producción — pérdida de capacidad operativa")
            impacto += 180000
        if respuestas.get("tiempo_paro") == "Más de 3 días":
            causas.append("Paro prolongado — incumplimiento de pedidos")
            impacto += 100000

    else:
        if "imss" in texto:
            causas.append("Incumplimiento IMSS — multas y capitales constitutivos")
            impacto += 80000
        if "sat" in texto or "auditoria" in texto:
            causas.append("Auditoría SAT activa — riesgo de embargo")
            impacto += 200000
        if "cfdi" in texto or "factura" in texto:
            causas.append("Inconsistencias CFDI — riesgo fiscal")
            impacto += 120000

    if impacto == 0:
        impacto = 25000

    return causas, impacto

async def llamar_anthropic(texto: str, industria: str, impacto: int, riesgo: str, causas: list, respuestas: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return ""

    causas_str = "\n".join(f"- {c}" for c in causas)
    resp_str = "\n".join(f"- {k}: {v}" for k, v in respuestas.items()) if respuestas else "Sin respuestas adicionales"

    prompt = f"""Actúa como consultor senior de una firma Big4 (Deloitte/PwC) especializado en riesgo empresarial en México.

Analiza el siguiente caso con enfoque ejecutivo:

Sector: {industria}
Situación descrita: {texto}
Riesgo detectado: {riesgo}
Impacto mensual estimado: ${impacto:,} MXN
Causas identificadas:
{causas_str}
Respuestas del cliente:
{resp_str}

Responde en este formato EXACTO:

1. Hallazgo Crítico:
Describe el problema central de forma directa y específica.

2. Implicación Operativa:
Explica cómo afecta la operación real de la empresa hoy.

3. Riesgo Financiero:
Relaciona el problema con pérdida económica concreta en pesos mexicanos.

4. Escenario a 30 días:
Qué ocurrirá específicamente si no se actúa en los próximos 30 días.

5. Recomendación Estratégica:
Acción clara, priorizada y ejecutable inmediatamente.

Reglas:
- Lenguaje ejecutivo, no genérico
- No repetir ideas entre secciones
- Conectar todo con dinero o riesgo real
- Evitar explicaciones básicas
- Sonar como consultor real de alto nivel, no como chatbot
- Máximo 3 oraciones por sección"""

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 800,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                logging.error(f"Anthropic error {response.status_code}: {response.text}")
                return ""
    except Exception:
        logging.error(f"Anthropic exception: {traceback.format_exc()}")
        return ""

@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):
    texto = normalizar(data.texto)
    respuestas = data.respuestas or {}
    industria = detectar_industria(texto)

    causas, impacto = analizar_fallback(texto, respuestas, industria)

    if impacto > 300000:
        riesgo = "CRÍTICO"
        tendencia = "CRÍTICO — acción inmediata requerida"
    elif impacto > 100000:
        riesgo = "ALTO"
        tendencia = "ALTO — con riesgo de escalar a CRÍTICO"
    elif impacto > 50000:
        riesgo = "MEDIO"
        tendencia = "MEDIO → con tendencia a ALTO"
    else:
        riesgo = "BAJO"
        tendencia = "ESTABLE — monitoreo preventivo recomendado"

    impacto_min = impacto
    impacto_max = int(impacto * 3)

    # Llamar Anthropic para análisis ejecutivo
    analisis_ai = await llamar_anthropic(texto, industria, impacto, riesgo, causas, respuestas)

    preguntas = generar_preguntas(industria, texto, riesgo)

    # WhatsApp dinámico
    if respuestas.get("acta") == "Acta levantada":
        whatsapp = (
            f"MESAN Ω — ALERTA CRÍTICA\n\n"
            f"Ya existe una inspección activa en tu operación.\n\n"
            f"Esto ya no es preventivo — estás en fase de posible sanción.\n\n"
            f"Impacto estimado:\n"
            f"${impacto_min:,} – ${impacto_max:,} MXN\n\n"
            f"¿Ya te dejaron observaciones específicas en el acta?\n\n"
            f"Te explico hoy mismo cómo evitar la sanción."
        )
    else:
        causa_principal = causas[0] if causas else ""
        whatsapp = (
            f"MESAN Ω — ALERTA {industria}\n\n"
            f"Detectamos riesgo {riesgo} en tu operación.\n\n"
            f"{causa_principal}\n\n"
            f"Impacto estimado:\n"
            f"${impacto_min:,} – ${impacto_max:,} MXN\n\n"
            f"¿Ya te levantaron acta o apenas es la visita?\n\n"
            f"Si quieres lo vemos hoy y te digo exactamente cómo corregirlo en 30 días."
        )

    consecuencias = {
        "SALUD": ["Suspensión temporal del establecimiento", "Multas sanitarias acumulativas", "Clausura parcial o total"],
        "RETAIL": ["Demandas laborales sin defensa", "Multas IMSS", "Inspección laboral"],
        "CONSTRUCCION": ["Capital constitutivo millonario", "Responsabilidad solidaria", "Paro de obra"],
        "ALIMENTOS": ["Clausura por incumplimiento NOM", "Multas sanitarias", "Pérdida de licencia"],
        "MANUFACTURA": ["Incumplimiento de pedidos", "Penalizaciones contractuales", "Pérdida de clientes"],
        "GENERAL": ["Multas y embargo preventivo", "Demandas laborales", "Auditoría sorpresa"]
    }.get(industria, ["Escalamiento del riesgo", "Sanciones acumuladas", "Pérdida operativa"])

    return {
        "ok": True,
        "industria": industria,
        "riesgo": riesgo,
        "tendencia": tendencia,
        "impacto": impacto,
        "impacto_min": impacto_min,
        "impacto_max": impacto_max,
        "probabilidad": "ALTA" if riesgo in ["CRÍTICO", "ALTO"] else "MEDIA",
        "causas": causas,
        "consecuencias": consecuencias,
        "preguntas": preguntas,
        "analisis_ai": analisis_ai,
        "plan_30_dias": [
            f"Semana 1: Auditoría especializada sector {industria} — identificación de incumplimientos",
            "Semana 2: Regularización inmediata — corrección documental y operativa",
            "Semana 3: Blindaje legal y fiscal — prevención de sanciones",
            "Semana 4: Estabilización operativa — reducción de riesgo a nivel controlado"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Este caso requiere atención especializada en {industria}. MESAN Ω puede resolverlo en 30 días. ¿Agendamos hoy?"
    }
