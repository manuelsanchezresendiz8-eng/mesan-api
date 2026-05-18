# -*- coding: utf-8 -*-
# routes/ia_diagnostico.py — MESAN Ω v4.0
# Tono: riesgo estimado, NO afirmaciones definitivas

from fastapi import APIRouter
from pydantic import BaseModel, Field
import unicodedata
import logging
import os
import httpx
import traceback
from datetime import datetime

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
    if any(p in texto for p in ["ingresos", "egresos", "gastos fijos", "flujo", "caja", "deficit", "perdida mensual", "no tengo caja", "sin liquidez", "deuda"]):
        return "FINANCIERO"
    return "GENERAL"

def analizar_fallback(texto, respuestas, industria):
    causas = []
    impacto = 0
    impacto_declarado = detectar_impacto_declarado(texto)

    if industria == "LABORAL":
        if any(p in texto for p in ["huelga", "paro", "emplazamiento", "sindicato"]):
            causas.append("Posible conflicto sindical con riesgo de paro operativo")
            impacto += impacto_declarado * 30 if impacto_declarado > 0 else 2000000
        if any(p in texto for p in ["accidente", "incapacidad", "herido", "lesion"]):
            causas.append("Posible accidente laboral con exposicion de responsabilidad patronal")
            impacto += 300000
        if any(p in texto for p in ["imss", "incapacidad", "obra determinada"]):
            causas.append("Posible irregularidad IMSS — riesgo de demanda laboral")
            impacto += 150000
        if any(p in texto for p in ["prestaciones", "contrato colectivo"]):
            causas.append("Posible conflicto por prestaciones — riesgo de escalamiento")
            impacto += 500000

    elif industria == "SEGURIDAD":
        causas.append("Posible brecha de regularizacion en registro SSPC — ventana de cumplimiento activa")
        impacto += 300000
        if any(p in texto for p in ["herido", "asalto", "lesion", "accidente", "disparo"]):
            causas.append("Posible incidente con lesion — exposicion de responsabilidad civil")
            impacto += 600000
        if any(p in texto for p in ["imss", "sin imss", "no tiene imss"]):
            causas.append("Posible trabajador sin cobertura IMSS")
            impacto += 200000
        if any(p in texto for p in ["sin seguro", "sin seguro rc", "sin seguro de responsabilidad civil", "no tenemos seguro"]):
            causas.append("Ausencia de cobertura de responsabilidad civil para personal operativo")
            impacto += 250000
        if any(p in texto for p in ["plazas", "corporativos", "sucursales", "ubicaciones", "sitios"]):
            causas.append("Operacion multisede — mayor exposicion operativa")
            impacto += 180000

    elif industria == "MANUFACTURA":
        if any(p in texto for p in ["huelga", "paro", "sindicato"]):
            causas.append("Posible conflicto sindical — presion relevante sobre continuidad operativa")
            impacto += impacto_declarado * 30 if impacto_declarado > 0 else 3000000
        if "emplazamiento" in texto:
            causas.append("Emplazamiento sindical activo — ventana critica de negociacion")
            impacto += 1800000
        if any(p in texto for p in ["imss", "stps", "accidente"]):
            causas.append("Posible riesgo laboral — IMSS y STPS")
            impacto += 200000
        if any(p in texto for p in ["cliente americano", "cliente unico", "solo cliente", "penalizacion contractual", "exportacion"]):
            causas.append("Alta dependencia de cliente estrategico — exposicion de concentracion")
            impacto += 2500000

    elif industria == "SERVICIOS_APOYO":
        causas.append("Posible brecha de regularizacion REPSE — exposicion administrativa y contractual")
        impacto += 180000
        if any(p in texto for p in ["accidente", "herido", "lesion"]):
            causas.append("Posible accidente laboral sin cobertura adecuada")
            impacto += 400000

    elif industria == "SALUD":
        causas.append("Posible riesgo de observacion sanitaria COFEPRIS")
        impacto += 200000

    elif industria == "TECNOLOGIA":
        causas.append("Posible riesgo operativo y fiscal")
        impacto += 150000

    elif industria == "FINANCIERO":
        import re

        causas_financieras = []

        def extraer_monto(patron, txt):
            m = re.search(patron, txt)
            if not m:
                return 0
            try:
                return int(m.group(1).replace(",", "").replace(".", ""))
            except:
                return 0

        ingresos_ext  = extraer_monto(r'factura\s+([\d,\.]+)', texto)
        deuda_ext     = extraer_monto(r'deuda\s+(?:bancaria\s+)?de\s+([\d,\.]+)', texto)
        pago_banco    = extraer_monto(r'pagos?\s+de\s+([\d,\.]+)', texto)
        nomina_ext    = extraer_monto(r'nomina\s+es\s+de\s+([\d,\.]+)', texto)
        gastos_ext    = extraer_monto(r'gastos?\s+fijos\s+son\s+([\d,\.]+)', texto)

        obligaciones  = pago_banco + nomina_ext + gastos_ext
        deficit       = obligaciones - ingresos_ext

        if deficit > 0:
            causas_financieras.append("Deficit operativo mensual — obligaciones superan ingresos")
            impacto += deficit * 6
            if deuda_ext >= (ingresos_ext * 4) and ingresos_ext > 0:
                causas_financieras.append("Nivel de apalancamiento elevado — deuda superior a capacidad operativa anual")
                impacto += int(deuda_ext * 0.20)
            if nomina_ext >= (ingresos_ext * 0.50) and ingresos_ext > 0:
                causas_financieras.append("Alta carga laboral sobre flujo operativo")
                impacto += 250000
            if pago_banco >= (ingresos_ext * 0.15) and ingresos_ext > 0:
                causas_financieras.append("Presion bancaria significativa sobre liquidez")
                impacto += 180000
            if deficit >= 40000:
                causas_financieras.append("Liquidez critica — flujo insuficiente para cubrir obligaciones mensuales")
                impacto += 350000
            if deficit >= 80000:
                causas_financieras.append("Riesgo de continuidad operativa en corto plazo")
                impacto += 500000
        else:
            causas_financieras.append("Presion financiera moderada detectada")
            impacto += 120000

        if any(p in texto for p in ["ya no me alcanza", "sin liquidez", "no puedo pagar", "atrasado", "morosidad"]):
            causas_financieras.append("Tension de liquidez declarada por direccion")
            impacto += 220000

        impacto = min(impacto, max(deuda_ext if deuda_ext > 0 else 2500000, 2500000))
        causas.extend(causas_financieras)

    if "imss" in texto and industria not in ["LABORAL", "SEGURIDAD", "MANUFACTURA", "SERVICIOS_APOYO"]:
        causas.append("Posible incumplimiento IMSS")
        impacto += 80000
    if "sat" in texto or "auditoria" in texto:
        causas.append("Posible riesgo fiscal SAT")
        impacto += 200000
    if "bloqueo" in texto or "embargo" in texto:
        causas.append("Posible presion de cuentas bancarias")
        impacto += 150000
    if "nomina" in texto and industria not in ["LABORAL", "MANUFACTURA"]:
        causas.append("Posible riesgo de incumplimiento laboral en nomina")
        impacto += 100000

    # MULTIPLICADOR OPERATIVO — SEGURIDAD
    if industria == "SEGURIDAD":
        empleados_seg = int(respuestas.get("num_empleados", 0))
        if empleados_seg >= 40 or any(p in texto for p in ["40 guardias", "50 guardias", "60 guardias"]):
            impacto += 180000
        if "corporativos" in texto:
            impacto += 120000
        if "plazas" in texto:
            impacto += 90000

    if impacto_declarado > 0 and impacto < impacto_declarado:
        impacto = impacto_declarado
    if impacto == 0:
        impacto = 25000

    return causas, impacto

def ajustar_laboral(causas, impacto, respuestas):
    if respuestas.get("huelga") == "Si":
        causas.append("Huelga activa confirmada — posible paralizacion operativa")
        impacto = int(impacto * 1.8)
    elif respuestas.get("huelga") == "En negociacion":
        causas.append("Conflicto en fase critica de negociacion sindical")
        impacto = int(impacto * 1.3)
    if respuestas.get("demanda_laboral") == "Si":
        causas.append("Posible demanda formal ante JLCA")
        impacto += 800000
    elif respuestas.get("demanda_laboral") == "No se":
        impacto += 300000
    return causas, impacto

def ajustar_por_respuestas(causas, impacto, respuestas, industria):
    if respuestas.get("acta") == "Acta levantada":
        causas.append("Posible proceso sancionador activo")
        impacto += 120000
    if respuestas.get("empleados") == "Mas de 20":
        causas.append("Alto volumen de personal con posible exposicion")
        impacto += 100000
    if respuestas.get("dias_paro") == "Mas de 3 dias":
        causas.append("Paro prolongado — posible dano acumulado")
        impacto += 500000
    return causas, impacto

async def llamar_anthropic(texto, industria, impacto, riesgo, causas):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not causas:
        return ""
    causas_txt = ", ".join(causas[:3])
    fecha_hoy = datetime.now().strftime("%d de %B de %Y")
    prompt = f"""
Actua como consultor ejecutivo de riesgo empresarial en Mexico.
Estilo: Deloitte / EY / KPMG / PwC.

Fecha: {fecha_hoy}
Industria: {industria}
Nivel estimado: {riesgo}
Exposicion estimada: ${impacto:,} MXN
Factores: {causas_txt}
Situacion: {texto}

REGLAS CRITICAS:
- Maximo 500 palabras en total
- Secciones breves y ejecutivas
- Optimizado para lectura movil
- NO uses: fraude, evasion, invalidacion total, sancion definitiva, maximos recargos, incumplimiento confirmado
- Describe todo como: posible contingencia, exposicion estimada, presion operativa, regularizacion preventiva
- NO redactes dictamen legal
- Enfocate en: exposicion estimada, continuidad operativa, riesgo reputacional, gestion de contingencias

Formato exacto:

# ANALISIS DE RIESGO EMPRESARIAL

## 1. HALLAZGO PRINCIPAL
[3 lineas maximo]

## 2. POSIBLE IMPACTO OPERATIVO
[3 lineas maximo]

## 3. EXPOSICION FINANCIERA ESTIMADA
- Escenario conservador: [monto estimado]
- Escenario probable: [monto estimado]
- Escenario de alta exposicion: [monto estimado]

## 4. ESCENARIO PROYECTADO — 30 DIAS
[maximo 2 lineas con fechas a partir del {fecha_hoy}]

## 5. RECOMENDACIONES PRIORITARIAS
[minimo 3 recomendaciones completas y accionables]

Cierra con:
"Este analisis es referencial. Los escenarios son estimados con base en variables declaradas y patrones generales de riesgo empresarial. Se recomienda validar con asesoria especializada."

IMPORTANTE: Completa SIEMPRE las 5 secciones. NO truncar. NO terminar antes de las recomendaciones.
"""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1200,
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

    # NIVEL DE RIESGO
    # CLASIFICACION FINANCIERA REAL
    if industria == "FINANCIERO":
        if impacto >= 1500000:
            riesgo = "CRITICO"
            tendencia_final = "ASCENDENTE"
        elif impacto >= 600000:
            riesgo = "ALTO"
            tendencia_final = "VOLATIL"
        elif impacto >= 180000:
            riesgo = "MEDIO"
            tendencia_final = "ESTABLE"
        else:
            riesgo = "BAJO"
            tendencia_final = "CONTROLADA"

    if industria == "LABORAL":
        t_check = texto.lower()
        if any(p in t_check for p in ["huelga", "paro", "emplazamiento", "sindicato"]):
            riesgo = "CRITICO"
    
    if industria == "MANUFACTURA" and "emplazamiento" in texto:
        riesgo = "CRITICO"
    elif impacto > 1200000:
        riesgo = "ALTO"
    elif impacto > 350000:
        riesgo = "MEDIO"
    else:
        riesgo = "BAJO"

    if industria not in ["LABORAL", "MANUFACTURA"]:
        if impacto > 1200000:
            riesgo = "CRITICO"
        elif impacto > 450000:
            riesgo = "ALTO"
        elif impacto > 120000:
            riesgo = "MEDIO"
        else:
            riesgo = "BAJO"

    impacto_min = impacto
    impacto_max = int(impacto * 2.5)

    if riesgo == "CRITICO":
        indice_riesgo = min(95, 85 + min(int(impacto / 1000000), 10))
    elif riesgo == "ALTO":
        indice_riesgo = min(80, 60 + min(int(impacto / 200000), 20))
    elif riesgo == "MEDIO":
        indice_riesgo = min(60, 40 + min(int(impacto / 100000), 20))
    else:
        indice_riesgo = 20

    # SCORING DINAMICO
    try:
        from core.scoring_engine import calcular_score
        scoring_data = {
            **respuestas,
            "industria": industria,
            "ingresos": float(respuestas.get("ingresos", 0) or 0),
            "egresos": float(respuestas.get("egresos", 0) or 0),
        }
        scoring = calcular_score(scoring_data)
        score_final     = scoring.get("score", indice_riesgo)
        nivel_final     = scoring.get("nivel", riesgo)
        confianza_final = scoring.get("confianza", 74)
        origen_final    = scoring.get("origen", ["Variables declaradas", "Simulacion operativa"])
    except Exception:
        score_final     = indice_riesgo
        nivel_final     = riesgo
        confianza_final = 74
        origen_final    = ["Variables declaradas", "Simulacion operativa", "Patrones regulatorios"]
        scoring         = {}

    # TENDENCIA DINAMICA
    if score_final >= 75:
        tendencia_final = "ASCENDENTE"
    elif score_final >= 40:
        tendencia_final = "ESTABLE"
    else:
        tendencia_final = "CONTROLADA"

    # CLAUDE
    analisis_ai = await llamar_anthropic(texto, industria, impacto, riesgo, causas)

    # FALLBACK REPORTE EJECUTIVO
    if not analisis_ai:
        try:
            from services.executive_report_generator import generar_reporte
            analisis_ai = generar_reporte(scoring, respuestas)
        except Exception:
            pass

    preguntas = generar_preguntas(industria, texto, riesgo)

    consecuencias = {
        "SEGURIDAD": ["Posible clausura por operacion sin permisos", "Nulidad de contratos", "Responsabilidad patrimonial estimada"],
        "LABORAL": ["Posible demanda laboral colectiva", "Multas STPS estimadas", "Paro de operaciones"],
        "MANUFACTURA": ["Posible perdida de produccion", "Ruptura de contratos con clientes", "Contingencias sindicales"],
        "SALUD": ["Posible clausura sanitaria COFEPRIS", "Multas estimadas", "Suspension de operaciones"],
        "SERVICIOS_APOYO": ["Posible presion en renovaciones contractuales", "Exposicion administrativa estimada", "Requerimientos de regularizacion operativa"],
        "FINANCIERO": ["Tension de liquidez progresiva", "Posibles fricciones operativas en cumplimiento de obligaciones", "Necesidad de reestructuracion financiera preventiva"],
        "GENERAL": ["Posibles multas y sanciones", "Contingencias laborales estimadas", "Revision SAT potencial"]
    }.get(industria, ["Escalamiento del riesgo", "Sanciones estimadas", "Perdida operativa potencial"])

    mensajes_wa = {
        "LABORAL": (
            f"MESAN Omega — Riesgo laboral detectado.\n\n"
            f"Se identificaron posibles contingencias operativas y laborales.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar acciones preventivas recomendadas."
        ),
        "FINANCIERO": (
            f"MESAN Omega — Tension financiera detectada.\n\n"
            f"Se identifico posible presion sobre liquidez y continuidad operativa.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar escenarios de estabilizacion y reestructuracion."
        ),
        "SERVICIOS_APOYO": (
            f"MESAN Omega — Riesgo operativo detectado.\n\n"
            f"Se identificaron posibles brechas de regularizacion relacionadas con cumplimiento REPSE.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar acciones preventivas recomendadas."
        ),
    }
    whatsapp = mensajes_wa.get(industria,
        f"MESAN Omega — Alerta {riesgo}\n\nDetectamos posible riesgo en tu operacion.\nExposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te explicamos como p
                                
