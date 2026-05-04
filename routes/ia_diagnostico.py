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

def detectar_impacto_declarado(texto: str) -> int:
    import re
    texto = texto.lower()
    patrones = [
        (r'(\d+)\s*millon', 1000000),
        (r'medio\s*millon', 500000),
        (r'(\d+)\s*millones', 1000000),
        (r'\$\s*(\d+[\.,]?\d*)\s*k', 1000),
        (r'(\d+)\s*mil\s*al\s*dia', 1000),
        (r'(\d+[\.,]?\d*)\s*mil', 1000),
    ]
    for patron, mult in patrones:
        m = re.search(patron, texto)
        if m:
            try:
                val = float(m.group(1).replace(',', '.')) if m.lastindex else 1
                return int(val * mult)
            except:
                return int(mult)
    return 0

def detectar_industria(texto: str) -> str:
    if any(p in texto for p in ["call center", "contact center", "agentes telefonicos", "cobranza telefonica"]):
        return "CALL_CENTER"
    if any(p in texto for p in ["seguridad privada", "guardia", "sspc", "dgsp", "cuip", "guardias"]):
        return "SEGURIDAD"
    if any(p in texto for p in ["huelga", "sindicato", "emplazamiento", "paro laboral", "paro de labores", "contrato colectivo"]):
        return "LABORAL"
    if any(p in texto for p in ["accidente laboral", "incapacidad", "riesgo de trabajo", "imss nego", "obra determinada"]):
        return "LABORAL"
    if any(p in texto for p in ["limpieza", "aseo", "intendencia", "outsourcing", "repse", "staffing"]):
        return "SERVICIOS_APOYO"
    if any(p in texto for p in ["hospital", "clinica", "medico", "cofepris", "paciente"]):
        return "SALUD"
    if any(p in texto for p in ["cbtis", "preparatoria", "escuela", "universidad", "plantel"]):
        return "EDUCACION"
    if any(p in texto for p in ["saas", "mrr", "churn", "aws", "sla", "startup", "fintech"]):
        return "TECNOLOGIA"
    if any(p in texto for p in ["obra", "construccion", "albanil", "cemento", "edificio"]):
        return "CONSTRUCCION"
    if any(p in texto for p in ["restaurante", "comida", "cocina", "alimentos", "cofepris"]):
        return "ALIMENTOS"
    if any(p in texto for p in ["fabrica", "produccion", "maquila", "planta", "manufactura", "refacciones", "ensamble"]):
        return "MANUFACTURA"
    if any(p in texto for p in ["tienda", "retail", "inventario", "comercio"]):
        return "RETAIL"
    if any(p in texto for p in ["banco", "credito", "financiera", "prestamos", "wallet"]):
        return "FINANCIERO"
    if any(p in texto for p in ["transporte", "logistica", "almacen", "flete", "trailer"]):
        return "LOGISTICA"
    return "GENERAL"

def analizar_fallback(texto, respuestas, industria):
    causas = []
    impacto = 0

    impacto_declarado = detectar_impacto_declarado(texto)

    if industria == "LABORAL":
        if any(p in texto for p in ["huelga", "paro", "emplazamiento", "sindicato"]):
            causas.append("Huelga activa - perdida de produccion por dia")
            if impacto_declarado > 0:
                impacto += impacto_declarado * 30
            else:
                impacto += 2000000
        if any(p in texto for p in ["accidente", "incapacidad", "herido", "lesion"]):
            causas.append("Accidente laboral sin cobertura IMSS - responsabilidad patronal directa")
            impacto += 300000
        if any(p in texto for p in ["imss", "incapacidad", "obra determinada"]):
            causas.append("IMSS nego incapacidad - riesgo de demanda laboral")
            impacto += 150000
        if any(p in texto for p in ["prestaciones", "contrato colectivo"]):
            causas.append("Conflicto por prestaciones - riesgo de escalamiento sindical")
            impacto += 500000

    elif industria == "SEGURIDAD":
        causas.append("Operacion sin permisos federales SSPC")
        impacto += 300000
        if any(p in texto for p in ["herido", "asalto", "lesion", "accidente", "disparo"]):
            causas.append("Incidente con lesion - responsabilidad civil y penal activa")
            causas.append("Sin seguro de responsabilidad civil = patron responde con patrimonio")
            impacto += 600000
        if any(p in texto for p in ["hospital", "plaza", "corporativo", "cliente"]):
            causas.append("Clientes corporativos en riesgo de rescision de contrato")
            impacto += 400000
        if any(p in texto for p in ["imss", "sin imss", "no tiene imss"]):
            causas.append("Trabajador sin IMSS - capital constitutivo obligatorio")
            impacto += 200000

    elif industria == "MANUFACTURA":
        if any(p in texto for p in ["huelga", "paro", "sindicato"]):
            causas.append("Conflicto sindical - paro de produccion activo")
            if impacto_declarado > 0:
                impacto += impacto_declarado * 30
            else:
                impacto += 3000000
        if any(p in texto for p in ["imss", "stps", "accidente"]):
            causas.append("Riesgo laboral - IMSS y STPS")
            impacto += 200000

    elif industria == "SERVICIOS_APOYO":
        causas.append("REPSE vencido - responsabilidad solidaria activa")
        impacto += 180000
        if any(p in texto for p in ["accidente", "herido", "lesion"]):
            causas.append("Accidente laboral - trabajador sin cobertura")
            causas.append("Responsabilidad civil: seguro RC o pago directo al trabajador")
            impacto += 400000

    elif industria == "SALUD":
        causas.append("Riesgo de clausura sanitaria COFEPRIS")
        impacto += 200000

    elif industria == "TECNOLOGIA":
        causas.append("Riesgo operativo y fiscal")
        impacto += 150000

    if "imss" in texto and industria not in ["LABORAL", "SEGURIDAD", "MANUFACTURA", "SERVICIOS_APOYO"]:
        causas.append("Incumplimiento IMSS - multas y capitales constitutivos")
        impacto += 80000

    if "sat" in texto or "auditoria" in texto:
        causas.append("Riesgo fiscal SAT - posible embargo")
        impacto += 200000

    if "bloqueo" in texto or "embargo" in texto:
        causas.append("Bloqueo de cuentas bancarias")
        impacto += 150000

    if "nomina" in texto and industria not in ["LABORAL", "MANUFACTURA"]:
        causas.append("Riesgo de incumplimiento laboral de nomina")
        impacto += 100000

    if impacto_declarado > 0 and impacto < impacto_declarado:
        impacto = impacto_declarado

    if impacto == 0:
        impacto = 25000

    return causas, impacto

def ajustar_laboral(causas, impacto, respuestas):
    if respuestas.get("huelga") == "Si":
        causas.append("Huelga activa confirmada - paralizacion total de operaciones")
        impacto = int(impacto * 1.8)
    elif respuestas.get("huelga") == "En negociacion":
        causas.append("Conflicto en fase critica de negociacion sindical")
        impacto = int(impacto * 1.3)

    if respuestas.get("demanda_laboral") == "Si":
        causas.append("Demanda formal presentada ante JLCA")
        impacto += 800000
    elif respuestas.get("demanda_laboral") == "No se":
        impacto += 300000

    return causas, impacto

def ajustar_por_respuestas(causas, impacto, respuestas, industria):
    if respuestas.get("acta") == "Acta levantada":
        causas.append("Proceso sancionador activo")
        impacto += 120000
    if respuestas.get("empleados") == "Mas de 20":
        causas.append("Alto volumen de empleados expuestos")
        impacto += 100000
    if respuestas.get("dias_paro") == "Mas de 3 dias":
        causas.append("Paro prolongado - dano acumulado critico")
        impacto += 500000
    return causas, impacto

async def llamar_anthropic(texto, industria, impacto, riesgo, causas):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not causas:
        return ""
    causas_txt = ", ".join(causas[:3])
    prompt = f"""Actua como consultor Big4 en Mexico especializado en derecho laboral, fiscal y empresarial.

Industria: {industria}
Situacion: {texto}
Nivel de riesgo: {riesgo}
Impacto estimado: ${impacto:,} MXN
Causas detectadas: {causas_txt}

Responde en exactamente 5 secciones con este formato:
## 1. HALLAZGO CRITICO
[maximo 3 lineas]

## 2. IMPLICACION OPERATIVA
[maximo 3 lineas]

## 3. RIESGO FINANCIERO
[maximo 3 lineas con cifras concretas]

## 4. ESCENARIO 30 DIAS
[maximo 3 lineas con fechas especificas]

## 5. RECOMENDACION ESTRATEGICA
[maximo 3 lineas con acciones concretas]

Usa lenguaje ejecutivo. Se especifico con cifras y plazos reales de Mexico."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 700,
                      "messages": [{"role": "user", "content": prompt}]}
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

    if industria == "LABORAL":
        causas, impacto = ajustar_laboral(causas, impacto, respuestas)

    if industria == "LABORAL":
        if impacto > 3000000:
            riesgo = "CRITICO"
        elif impacto > 1000000:
            riesgo = "ALTO"
        elif impacto > 300000:
            riesgo = "MEDIO"
        else:
            riesgo = "BAJO"
    else:
        if impacto > 500000:
            riesgo = "CRITICO"
        elif impacto > 200000:
            riesgo = "ALTO"
        elif impacto > 80000:
            riesgo = "MEDIO"
        else:
            riesgo = "BAJO"

    impacto_min = impacto
    impacto_max = int(impacto * 2.5)

    analisis_ai = await llamar_anthropic(texto, industria, impacto, riesgo, causas)

    preguntas = generar_preguntas(industria, texto, riesgo)

    consecuencias = {
        "SEGURIDAD": ["Clausura por operacion ilegal", "Nulidad de contratos", "Responsabilidad patrimonial"],
        "LABORAL": ["Demanda laboral colectiva", "Multas STPS", "Paro indefinido de operaciones"],
        "MANUFACTURA": ["Perdida de produccion diaria", "Ruptura de contratos con clientes", "Demandas sindicales"],
        "SALUD": ["Clausura sanitaria COFEPRIS", "Multas", "Suspension de operaciones"],
        "SERVICIOS_APOYO": ["Rescision de contratos", "Responsabilidad solidaria", "Multas IMSS"],
        "TECNOLOGIA": ["Perdida de clientes", "Riesgo fiscal", "Problemas de continuidad"],
        "GENERAL": ["Multas y embargo", "Demandas laborales", "Auditoria SAT"]
    }.get(industria, ["Escalamiento del riesgo", "Sanciones acumuladas", "Perdida operativa"])

    mensajes_wa = {
        "SEGURIDAD": f"MESAN Omega - ALERTA CRITICA\n\nOperacion sin permisos SSPC + IMSS vencido = cierre inminente.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para plan de accion inmediato.",
        "LABORAL": (
            f"MESAN Omega - ALERTA CRITICA\n\nHuelga activa confirmada.\nOperacion detenida.\n\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nCada dia incrementa la perdida real.\nResponde SI para plan inmediato."
            if respuestas.get("huelga") == "Si" else
            f"MESAN Omega - ALERTA LABORAL\n\nConflicto laboral activo detectado.\n\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nCada dia sin accion aumenta la exposicion.\n\nResponde SI y te digo como resolverlo hoy."
        ),
        "MANUFACTURA": f"MESAN Omega - ALERTA MANUFACTURA\n\nParo de produccion activo - perdidas acumulando por dia.\n\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para plan de contencion inmediato.",
        "SERVICIOS_APOYO": f"MESAN Omega - ALERTA CRITICA\n\nIncumplimiento REPSE e IMSS detectado.\nClientes corporativos en riesgo de rescision.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para frenarlo hoy.",
        "SALUD": f"MESAN Omega - ALERTA COFEPRIS\n\nRiesgo de clausura sanitaria activo.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te digo como evitarlo.",
        "TECNOLOGIA": f"MESAN Omega - ALERTA FINANCIERA\n\nRiesgo operativo detectado.\n\nImpacto: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI para plan de estabilizacion.",
    }
    whatsapp = mensajes_wa.get(industria,
        f"MESAN Omega - ALERTA {riesgo}\n\nDetectamos riesgo en tu operacion.\nImpacto estimado: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te digo como resolverlo en 30 dias."
    )

    logging.info(f"Diagnostico | {industria} | {riesgo} | ${impacto:,}")

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
            "Semana 2: Regularizacion inmediata - correccion documental",
            "Semana 3: Blindaje legal y fiscal - prevencion de sanciones",
            "Semana 4: Estabilizacion operativa - reduccion de riesgo"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Atencion especializada requerida en {industria}. Podemos resolverlo en 30 dias."
    }
