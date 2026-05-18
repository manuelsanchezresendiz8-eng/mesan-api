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

    causas_txt = " | ".join([c[:80] for c in causas[:4]])
    fecha_hoy  = datetime.now().strftime("%d de %B de %Y")

    modo_crisis = riesgo == "CRITICO" and len(causas) >= 4

    impacto_bajo     = int(impacto * 0.4)
    impacto_probable = int(impacto * 0.75)
    impacto_critico  = int(impacto * 1.0)
    if industria == "FINANCIERO":
        impacto_critico = min(impacto_critico, 2500000)

    prompt_normal = f"""
Actua como consultor senior de riesgo empresarial en Mexico.
Entrega diagnosticos EJECUTIVOS, concretos y accionables.

REGLAS:
- NO expliques leyes extensamente
- NO hagas introducciones largas
- Usa lenguaje ejecutivo y bullets cortos
- NO exageres montos
- Usa lenguaje de riesgo estimado
- Maximo 120 palabras por seccion

Fecha actual: {fecha_hoy}
Industria: {industria}
Riesgo: {riesgo}
Situacion: {texto}
Factores: {causas_txt}

ESCENARIOS FINANCIEROS OBLIGATORIOS (NO modificar):
- Conservador: ${impacto_bajo:,}
- Probable: ${impacto_probable:,}
- Critico: ${impacto_critico:,}

RESPONDE EXACTAMENTE:

## 1. HALLAZGO PRINCIPAL
[Resumen ejecutivo]

## 2. IMPACTO OPERATIVO
[Impacto operativo real]

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

## 4. ESCENARIO 30 DIAS
[Timeline ejecutivo con fechas desde {fecha_hoy}]

## 5. RECOMENDACIONES PRIORITARIAS
- Accion 1:
- Accion 2:
- Accion 3:
- Accion 4:

Analisis referencial sujeto a validacion legal y fiscal especializada.
"""

    prompt_crisis = f"""
Actua como consultor senior de crisis empresariales en Mexico.
Este caso involucra multiples contingencias simultaneas.
Prioriza: CONTENCION, ACCIONES, CONTINUIDAD OPERATIVA.

NO hagas texto academico. NO expliques leyes. NO excedas 90 palabras por seccion.
Estilo Big4: concreto, accionable, financiero, enfocado en mitigacion inmediata.

Fecha actual: {fecha_hoy}
Industria: {industria}
Riesgo: {riesgo}
Contexto: {texto}
Factores: {causas_txt}

ESCENARIOS FINANCIEROS OBLIGATORIOS (NO modificar):
- Conservador: ${impacto_bajo:,}
- Probable: ${impacto_probable:,}
- Critico: ${impacto_critico:,}

RESPONDE EXACTAMENTE:

## 1. HALLAZGO PRINCIPAL
[maximo 90 palabras]

## 2. IMPACTO OPERATIVO
[maximo 90 palabras]

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

## 4. ESCENARIO 30 DIAS
[maximo 90 palabras con fechas desde {fecha_hoy}]

## 5. RECOMENDACIONES PRIORITARIAS
- Accion inmediata 24h:
- Accion inmediata 72h:
- Accion semana 1:
- Accion semana 2:
- Accion financiera:
- Accion legal:

Analisis referencial sujeto a validacion especializada.
"""

    prompt = prompt_crisis if modo_crisis else prompt_normal

    # REGLAS ESPECIALIZADAS FINANCIERO
    if industria == "FINANCIERO":
        prompt += """

REGLAS EJECUTIVAS OBLIGATORIAS — TURNAROUND ADVISOR:

LOGICA DE CLASIFICACION:
- Si existen deuda + cartera vencida + ISR + lineas de credito + nomina comprometida simultaneamente: clasifica como "estres financiero severo" o "riesgo de insolvencia operativa"
- Si cartera vencida > ingresos mensuales: "dependencia critica de cobranza"
- Si ISR retenido vencido: "contingencia fiscal prioritaria"
- Si lineas de credito usadas para nomina: "capital de trabajo agotado"

PRIORIDAD DE RECOMENDACIONES:
1. Supervivencia de caja — acciones en 24-72 horas
2. Evitar incumplimiento bancario — antes del proximo vencimiento
3. Proteger nomina — semana 1
4. Contingencia SAT — semana 2
5. Regularizacion IMSS — semana 3-4

ESCENARIOS FINANCIEROS — SIEMPRE PROGRESIVOS:
Los montos deben ser: Conservador < Probable < Critico
NUNCA invertir el orden.

PROHIBIDO usar: "evaluar opciones", "explorar alternativas", "considerar medidas", "presion moderada", "ligera tension", "flujo ajustado"

USAR OBLIGATORIAMENTE: "negociar", "reestructurar", "suspender", "priorizar", "reducir", "inyectar", "renegociar"

MINIMO 4 RECOMENDACIONES COMPLETAS — nunca terminar incompleto.

Cada recomendacion: accion concreta + objetivo + plazo especifico

TONO: turnaround consultant + restructuring advisor + CRO corporativo. NO chatbot motivacional.

EJEMPLOS CORRECTOS:
- Negociar con banco extension de 60 dias antes del vencimiento de esta semana
- Suspender pagos no criticos y priorizar nomina y SAT en proximas 72 horas
- Reestructurar deuda bancaria solicitando periodo de gracia de 90 dias
- Reducir gastos fijos operativos minimo 20% en los proximos 14 dias
- Activar cobranza ejecutiva en las 2 cuentas principales con plazo de 15 dias
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
                    "max_tokens": 1400,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"]
            logging.error(f"Claude Error: {r.text}")
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
    # CLASIFICACION FINANCIERA REAL — LOGICA EJECUTIVA
    if industria == "FINANCIERO":

        # Detectores de estres financiero severo
        tiene_deuda       = any(p in texto for p in ["deuda", "bancaria", "banco"])
        tiene_cartera     = any(p in texto for p in ["cartera vencida", "no pagar", "dejaron de pagar"])
        tiene_isr         = any(p in texto for p in ["isr", "retenido", "sat"])
        tiene_lineas      = any(p in texto for p in ["linea de credito", "lineas de credito", "credito para"])
        tiene_nomina_comp = any(p in texto for p in ["nomina", "pagar nomina", "cubrir pagos"])

        factores_criticos = sum([tiene_deuda, tiene_cartera, tiene_isr, tiene_lineas, tiene_nomina_comp])

        if factores_criticos >= 3:
            causas.append("Estres financiero severo — multiples presiones simultaneas sobre liquidez")
            impacto += 500000

        # Cartera vencida mayor a ingresos mensuales
        if tiene_cartera:
            causas.append("Dependencia critica de cobranza — cartera vencida comprometida")
            impacto += 400000

        # ISR retenido vencido
        if tiene_isr:
            causas.append("Contingencia fiscal prioritaria — ISR retenido no enterado")
            impacto += 350000

        # Lineas de credito para nomina
        if tiene_lineas and tiene_nomina_comp:
            causas.append("Capital de trabajo agotado — lineas de credito usadas para nomina")
            impacto += 300000

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
        riesgo = "BA
