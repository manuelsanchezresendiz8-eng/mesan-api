# -*- coding: utf-8 -*-

from fastapi import APIRouter
from pydantic import BaseModel, Field
import unicodedata
import logging
import os
import httpx
import traceback

from core.preguntas import generar_preguntas

router = APIRouter()

class InputAI(BaseModel):
    texto: str
    respuestas: dict = Field(default_factory=dict)

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return texto.encode("ascii", "ignore").decode("utf-8")

def detectar_industria(texto: str) -> str:
    if any(p in texto for p in ["call center", "contact center", "agentes telefonicos"]):
        return "CALL_CENTER"
    if any(p in texto for p in ["seguridad privada", "guardia", "sspc", "dgsp", "cuip", "guardias"]):
        return "SEGURIDAD"
    # SERVICIOS_APOYO antes que SALUD — limpieza/outsourcing puede tener clientes en hospitales
    if any(p in texto for p in ["limpieza", "aseo", "intendencia", "outsourcing", "repse", "staffing"]):
        return "SERVICIOS_APOYO"
    if any(p in texto for p in ["hospital", "clinica", "medico", "cofepris"]):
        return "SALUD"
    if any(p in texto for p in ["cbtis", "preparatoria", "escuela", "universidad"]):
        return "EDUCACION"
    if any(p in texto for p in ["limpieza", "aseo", "intendencia"]):
        return "SERVICIOS_APOYO"
    if any(p in texto for p in ["saas", "mrr", "churn", "aws", "sla"]):
        return "TECNOLOGIA"
    if any(p in texto for p in ["obra", "construccion", "albanil"]):
        return "CONSTRUCCION"
    if any(p in texto for p in ["restaurante", "comida", "cocina"]):
        return "ALIMENTOS"
    if any(p in texto for p in ["fabrica", "produccion", "maquila"]):
        return "MANUFACTURA"
    if any(p in texto for p in ["tienda", "retail", "inventario"]):
        return "RETAIL"
    if any(p in texto for p in ["banco", "credito", "financiera", "fintech"]):
        return "FINANCIERO"
    if any(p in texto for p in ["transporte", "logistica", "almacen"]):
        return "LOGISTICA"
    return "GENERAL"

def analizar_fallback(texto, respuestas, industria):
    causas = []
    impacto = 0

    if "imss" in texto:
        causas.append("Incumplimiento IMSS - multas y capitales constitutivos")
        impacto += 80000

    if "sat" in texto or "auditoria" in texto:
        causas.append("Riesgo fiscal SAT - posible embargo")
        impacto += 200000

    if "bloqueo" in texto or "cuenta" in texto:
        causas.append("Bloqueo de cuentas bancarias")
        impacto += 150000

    if "nomina" in texto or "sueldo" in texto:
        causas.append("Riesgo de incumplimiento laboral")
        impacto += 100000

    if industria == "SEGURIDAD":
        causas.append("Operacion sin permisos federales SSPC")
        impacto += 300000
        if any(p in texto for p in ["hospital", "plaza", "corporativo"]):
            causas.append("Clientes corporativos en riesgo de rescision")
            impacto += 400000

    elif industria == "SALUD":
        causas.append("Riesgo de clausura sanitaria COFEPRIS")
        impacto += 200000

    elif industria == "SERVICIOS_APOYO":
        causas.append("REPSE vencido - responsabilidad solidaria activa")
        impacto += 180000

    if impacto == 0:
        impacto = 25000

    return causas, impacto

def ajustar_por_respuestas(causas, impacto, respuestas, industria):
    if respuestas.get("acta") == "Acta levantada":
        causas.append("Proceso sancionador activo")
        impacto += 120000
    if respuestas.get("empleados") == "Mas de 20":
        causas.append("Alto volumen de empleados expuestos")
        impacto += 100000
    return causas, impacto

async def llamar_anthropic(texto, industria, impacto, riesgo, causas):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not causas:
        return ""
    prompt = f"""Actua como consultor Big4 en Mexico.
Industria: {industria}
Problema: {texto}
Riesgo: {riesgo}
Impacto: ${impacto:,} MXN
Causas: {', '.join(causas)}

Responde en 5 secciones: 1.Hallazgo critico 2.Implicacion operativa 3.Riesgo financiero 4.Escenario 30 dias 5.Recomendacion estrategica. Max 3 lineas por seccion. Lenguaje ejecutivo."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]}
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"]
    except Exception:
        logging.error(traceback.format_exc())
    return ""

@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):
    texto = normalizar(data.texto)
    respuestas = data.respuestas

    industria = detectar_industria(texto)
    causas, impacto = analizar_fallback(texto, respuestas, industria)
    causas, impacto = ajustar_por_respuestas(causas, impacto, respuestas, industria)

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

    analisis_ai = await llamar_anthropic(texto, industria, impacto, riesgo, causas)

    preguntas = generar_preguntas(industria, texto, riesgo)

    consecuencias = {
        "SALUD": ["Clausura sanitaria", "Multas COFEPRIS", "Suspension de operaciones"],
        "SEGURIDAD": ["Clausura por operacion ilegal", "Nulidad de contratos", "Responsabilidad patrimonial"],
        "CONSTRUCCION": ["Capital constitutivo IMSS", "Responsabilidad solidaria", "Paro de obra"],
        "GENERAL": ["Multas y embargo", "Demandas laborales", "Auditoria SAT"]
    }.get(industria, ["Escalamiento del riesgo", "Sanciones acumuladas", "Perdida operativa"])

    mensajes_wa = {
        "SERVICIOS_APOYO": f"MESAN Omega - ALERTA {riesgo}\n\nDetectamos incumplimiento REPSE e IMSS en tu empresa.\nCon clientes corporativos en riesgo de rescision, esto puede colapsar en menos de 30 dias.\n\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te digo como frenarlo hoy.",
        "SEGURIDAD": f"MESAN Omega - ALERTA CRITICA\n\nOperacion sin permisos SSPC + IMSS vencido = cierre inminente.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para plan de accion inmediato.",
        "SALUD": f"MESAN Omega - ALERTA COFEPRIS\n\nRiesgo de clausura sanitaria activo.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te digo como evitarlo.",
        "TECNOLOGIA": f"MESAN Omega - ALERTA FINANCIERA\n\nBurn rate insostenible + riesgo de insolvencia.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para plan de estabilizacion.",
    }
    whatsapp = mensajes_wa.get(industria, 
        f"MESAN Omega - ALERTA {riesgo}\n\nDetectamos riesgo {riesgo} en tu operacion.\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te digo como resolverlo en 30 dias."
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
        "plan_30_dias": [
            f"Semana 1: Auditoria especializada sector {industria}",
            "Semana 2: Regularizacion inmediata",
            "Semana 3: Blindaje legal y fiscal",
            "Semana 4: Estabilizacion operativa"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Atencion especializada requerida en {industria}. Podemos resolverlo en 30 dias."
    }
