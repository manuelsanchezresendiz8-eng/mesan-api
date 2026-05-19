# -*- coding: utf-8 -*-
# routes/ia_diagnostico.py -- MESAN Ω v4.0
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

# CRISIS EVENTS -- pesos reales
CRISIS_EVENTS = {
    "cuentas_bloqueadas": {"score": 95, "impacto": 1200000, "nivel": "CRITICO", "tendencia": "ASCENDENTE"},
    "embargo_sat":        {"score": 92, "impacto": 1500000, "nivel": "CRITICO", "tendencia": "ASCENDENTE"},
    "nomina_riesgo":      {"score": 85, "impacto": 650000,  "nivel": "ALTO",    "tendencia": "ASCENDENTE"},
    "huelga_activa":      {"score": 97, "impacto": 3000000, "nivel": "CRITICO", "tendencia": "ASCENDENTE"},
    "cliente_rescision":  {"score": 82, "impacto": 800000,  "nivel": "ALTO",    "tendencia": "ASCENDENTE"},
    "sin_rc_lesionado":   {"score": 94, "impacto": 1800000, "nivel": "CRITICO", "tendencia": "ASCENDENTE"},
    "infonavit_omision":  {"score": 78, "impacto": 450000,  "nivel": "ALTO",    "tendencia": "ASCENDENTE"},
}

def aplicar_colision_riesgos(texto, impacto, score):
    """Motor de colision -- multiplica impacto cuando coexisten riesgos criticos"""
    t = texto.lower()

    if ("bloqueo" in t or "embargo" in t) and "nomina" in t:
        impacto = int(impacto * 1.8)
        score += 12

    if ("huelga" in t or "sindicato" in t) and "cliente americano" in t:
        impacto = int(impacto * 2.5)
        score += 15

    if "sspc" in t and ("lesion" in t or "herido" in t) and ("sin seguro" in t or "responsabilidad civil" in t):
        impacto = int(impacto * 2.2)
        score += 14

    if "sat" in t and ("bloqueo" in t or "embargo" in t):
        impacto = int(impacto * 2.0)
        score += 15

    if "infonavit" in t and ("bloqueo" in t or "embargo" in t):
        impacto = int(impacto * 1.6)
        score += 10

    return int(impacto), min(score, 99)

def detectar_industria(texto: str) -> str:
    t = texto.lower()
    sectores = {
        "SEGURIDAD":       ["seguridad privada", "guardia", "sspc", "guardias", "custodia", "dgsp", "cuip"],
        "LABORAL":         ["huelga", "sindicato", "paro laboral", "emplazamiento", "contrato colectivo"],
        "FINANCIERO":      ["deuda", "liquidez", "flujo", "credito", "cartera vencida", "banco", "sin liquidez", "no me alcanza", "ingresos", "egresos", "gastos fijos", "caja", "deficit"],
        "LOGISTICA":       ["logistica", "trailer", "operadores", "flete", "transporte", "almacen"],
        "MANUFACTURA":     ["maquila", "planta", "produccion", "manufactura", "fabrica", "ensamble"],
        "SERVICIOS_APOYO": ["repse", "limpieza", "outsourcing", "intendencia", "staffing"],
        "SALUD":           ["hospital", "clinica", "medico", "cofepris", "paciente"],
        "CONSTRUCCION":    ["obra", "construccion", "albanil", "cemento", "edificio"],
        "TECNOLOGIA":      ["saas", "mrr", "churn", "aws", "startup", "fintech"],
        "RETAIL":          ["tienda", "retail", "inventario", "comercio"],
        "EDUCACION":       ["escuela", "universidad", "preparatoria", "plantel"],
        "ALIMENTOS":       ["restaurante", "comida", "cocina", "alimentos"],
    }
    for sector, palabras in sectores.items():
        if any(p in t for p in palabras):
            return sector
    return "GENERAL"

def analizar_fallback(texto, respuestas, industria):
    t = texto.lower()
    causas = []
    impacto = 0
    score = 25

    # CUENTAS BLOQUEADAS / EMBARGO
    if any(p in t for p in ["bloqueo", "embargo", "cuentas bloqueadas", "inmovilizacion", "pae", "ejecucion fiscal", "infonavit bloqueo", "cuenta bloqueada"]):
        causas.append("Inmovilizacion bancaria detectada -- continuidad operativa comprometida")
        impacto += 1200000
        score += 30

    # INFONAVIT
    if "infonavit" in t:
        causas.append("Omisiones patronales INFONAVIT detectadas -- riesgo de credito fiscal")
        impacto += 450000
        score += 15

    # NOMINA
    if "nomina" in t:
        causas.append("Presion sobre cumplimiento de nomina -- riesgo de incumplimiento en cadena")
        impacto += 350000
        score += 18

    # SAT
    if "sat" in t or "credito fiscal" in t:
        causas.append("Credito fiscal o presion SAT detectada")
        impacto += 800000
        score += 20

    # HUELGA / SINDICAL
    if any(p in t for p in ["huelga", "emplazamiento", "sindicato", "paro laboral"]):
        causas.append("Conflicto sindical con riesgo de paralizacion operativa")
        impacto += 2500000
        score += 35

    # SSPC
    if "sspc" in t:
        causas.append("Operacion con vulnerabilidad regulatoria SSPC")
        impacto += 650000
        score += 15

    # REPSE
    if "repse" in t:
        causas.append("Brecha REPSE con riesgo contractual")
        impacto += 380000
        score += 12

    # IMSS
    if "imss" in t:
        causas.append("Posible contingencia IMSS detectada")
        impacto += 280000
        score += 10

    # SUA / SIPARE
    if any(p in t for p in ["sua", "sipare"]):
        causas.append("Inconsistencias SUA/SIPARE -- posible omision de cuotas no detectada")
        impacto += 250000
        score += 8

    # LESIONES / RC
    if any(p in t for p in ["lesion", "herido", "accidente laboral"]):
        causas.append("Incidente operativo con posible responsabilidad civil")
        impacto += 950000
        score += 20

    # CLIENTE ESTRATEGICO
    if any(p in t for p in ["cliente americano", "cliente unico", "penalizacion contractual", "exportacion"]):
        causas.append("Alta dependencia de cliente estrategico -- exposicion de concentracion")
        impacto += 2500000
        score += 20

    # SEGURO RC
    if any(p in t for p in ["sin seguro", "sin seguro rc", "no tenemos seguro"]):
        causas.append("Ausencia de cobertura de responsabilidad civil para personal operativo")
        impacto += 250000
        score += 10

    # MULTISEDE
    if any(p in t for p in ["plazas", "corporativos", "sucursales", "ubicaciones"]):
        causas.append("Operacion multisede -- mayor exposicion operativa")
        impacto += 180000
        score += 5

    # CARTERA VENCIDA
    if any(p in t for p in ["cartera vencida", "no pagaron", "dejaron de pagar"]):
        causas.append("Cartera vencida critica -- flujo operativo comprometido")
        impacto += 600000
        score += 15

    # DEUDA / APALANCAMIENTO
    if any(p in t for p in ["deuda bancaria", "linea de credito", "prestamo bancario"]):
        causas.append("Nivel elevado de apalancamiento financiero")
        impacto += 400000
        score += 12

    # INDUSTRIA FINANCIERO
    if industria == "FINANCIERO":
        import re
        def extraer_monto(patron, txt):
            m = re.search(patron, txt)
            if not m:
                return 0
            try:
                return int(m.group(1).replace(",", "").replace(".", ""))
            except:
                return 0

        ingresos_ext  = extraer_monto(r'factura\s+([\d,\.]+)', t)
        egresos_ext   = extraer_monto(r'gastos?\s+fijos\s+son\s+([\d,\.]+)', t)
        pago_banco    = extraer_monto(r'pagos?\s+de\s+([\d,\.]+)', t)
        nomina_ext    = extraer_monto(r'nomina\s+es\s+de\s+([\d,\.]+)', t)
        obligaciones  = pago_banco + nomina_ext + egresos_ext
        deficit       = obligaciones - ingresos_ext if ingresos_ext > 0 else 0

        if deficit > 0:
            causas.append("Deficit operativo mensual -- obligaciones superan ingresos")
            impacto += deficit * 6
            if deficit >= 40000:
                causas.append("Liquidez critica -- flujo insuficiente para cubrir obligaciones mensuales")
                impacto += 350000
            if deficit >= 80000:
                causas.append("Riesgo de continuidad operativa en corto plazo")
                impacto += 500000

        impacto = min(impacto, 4000000)

    # COLISION DE RIESGOS
    impacto, score = aplicar_colision_riesgos(t, impacto, score)

    if impacto == 0:
        impacto = 25000

    return causas, impacto

def ajustar_laboral(causas, impacto, respuestas):
    if respuestas.get("huelga") == "Si":
        causas.append("Huelga activa confirmada -- posible paralizacion operativa")
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
        causas.append("Paro prolongado -- posible dano acumulado")
        impacto += 500000
    return causas, impacto

async def llamar_anthropic(texto, industria, impacto, riesgo, causas):

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ""

    fecha_hoy  = datetime.now().strftime("%d de %B de %Y")
    causas_txt = " | ".join([c[:80] for c in causas[:4]])

    modo_crisis = riesgo == "CRITICO" and len(causas) >= 4

    impacto_bajo     = int(impacto * 0.45)
    impacto_probable = int(impacto * 0.75)
    impacto_critico  = int(impacto)
    if industria == "FINANCIERO":
        impacto_critico = min(impacto_critico, 2500000)

    prompt = f"""
Actua como CRO (Chief Restructuring Officer) y War-Room Advisor.
NO eres consultor narrativo. Eres motor de supervivencia empresarial.

Fecha: {fecha_hoy}
Industria: {industria}
Nivel: {riesgo}
Situacion: {texto}
Factores: {causas_txt}

ESCENARIOS (NO modificar):
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

REGLAS:
- MAXIMO 60 palabras por seccion
- NO tablas markdown
- NO cortar frases
- NUNCA terminar sin completar las 7 secciones
- Acciones con: ejecutar + objetivo + plazo
- PROHIBIDO: "monitorear", "evaluar opciones", "dar seguimiento", "podria", "considerar"
- USAR: ejecutar, bloquear, renegociar, suspender, proteger, reducir

ESTRUCTURA OBLIGATORIA -- COMPLETAR LAS 7:

## 1. HALLAZGO CRITICO
[2 lineas -- directo]

## 2. RIESGO DE CONTINUIDAD
[3 bullets -- una idea cada uno]

## 3. EXPOSICION FINANCIERA
- Conservador: ${impacto_bajo:,} MXN
- Probable: ${impacto_probable:,} MXN
- Critico: ${impacto_critico:,} MXN

## 4. VENTANA DE COLAPSO
[2 fechas desde {fecha_hoy} con consecuencia]

## 5. ACCIONES EJECUTIVAS
🔴 ACCION 24H -- [titulo]
- Ejecutar: [accion max 10 palabras]
- Objetivo: [resultado esperado]
- Plazo: [fecha/hora]

🟠 ACCION 72H -- [titulo]
- Ejecutar: [accion max 10 palabras]
- Objetivo: [resultado esperado]
- Plazo: [fecha/hora]

🟡 ACCION SEMANA 1 -- [titulo]
- Ejecutar: [accion max 10 palabras]
- Objetivo: [resultado esperado]
- Plazo: [fecha]

## 6. PROTOCOLO DE SUPERVIVENCIA
- Priorizar: [que pagar primero]
- Suspender: [que congelar]
- Proteger: [que blindar]
- Riesgo embargo: [SI/NO/PROBABLE]

## 7. DECISION CEO
[UNA orden ejecutiva. Verbos: ejecutar/bloquear/renegociar/suspender. Max 2 lineas.]

Analisis referencial sujeto a validacion especializada.
"""

    # Reglas financieras adicionales
    if industria == "FINANCIERO":
        prompt += """

REGLAS FINANCIERAS:
- Prioridad 1: supervivencia de caja
- Prioridad 2: evitar incumplimiento bancario
- Prioridad 3: proteger nomina
- Prioridad 4: contener SAT
- Acciones concretas: negociar banco, recuperar cartera, separar flujo nomina
- PROHIBIDO: "optimizar", "estabilizar", "mejorar flujo"
"""

    # Reglas IMSS/INFONAVIT/EMBARGO
    if any(p in texto for p in ["bloqueo", "embargo", "infonavit", "sua", "pae", "ejecucion fiscal"]):
        prompt += """

REGLAS EMBARGO/BLOQUEO:
- Diferenciar IMSS vs INFONAVIT -- son obligaciones distintas
- Bloqueo bancario = evento critico de continuidad operativa
- Prioridad: liberar cuentas + proteger nomina + convenio SAT
- Recomendaciones: liberar parcial, convenio pago, separar flujo, auditar SUA
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
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            if r.status_code == 200:
                respuesta = r.json()["content"][0]["text"]

                # VALIDADORES
                if len(respuesta) < 300:
                    logging.error("Respuesta demasiado corta")
                    return ""
                if "## 5." not in respuesta:
                    logging.error("Respuesta incompleta -- faltan acciones")
                    return ""

                return respuesta
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
    # CLASIFICACION FINANCIERA REAL -- LOGICA EJECUTIVA
    if industria == "FINANCIERO":

        # Detectores de estres financiero severo
        tiene_deuda       = any(p in texto for p in ["deuda", "bancaria", "banco"])
        tiene_cartera     = any(p in texto for p in ["cartera vencida", "no pagar", "dejaron de pagar"])
        tiene_isr         = any(p in texto for p in ["isr", "retenido", "sat"])
        tiene_lineas      = any(p in texto for p in ["linea de credito", "lineas de credito", "credito para"])
        tiene_nomina_comp = any(p in texto for p in ["nomina", "pagar nomina", "cubrir pagos"])

        factores_criticos = sum([tiene_deuda, tiene_cartera, tiene_isr, tiene_lineas, tiene_nomina_comp])

        if factores_criticos >= 3:
            causas.append("Estres financiero severo -- multiples presiones simultaneas sobre liquidez")
            impacto += 500000

        # Cartera vencida mayor a ingresos mensuales
        if tiene_cartera:
            causas.append("Dependencia critica de cobranza -- cartera vencida comprometida")
            impacto += 400000

        # ISR retenido vencido
        if tiene_isr:
            causas.append("Contingencia fiscal prioritaria -- ISR retenido no enterado")
            impacto += 350000

        # Lineas de credito para nomina
        if tiene_lineas and tiene_nomina_comp:
            causas.append("Capital de trabajo agotado -- lineas de credito usadas para nomina")
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

    # Override por bloqueo/embargo -- severidad minima ALTO
    if any(p in texto for p in ["bloqueo", "embargo", "cuentas bloqueadas", "inmovilizacion", "pae", "ejecucion fiscal", "infonavit bloqueo", "cuenta bloqueada"]):
        if riesgo not in ["CRITICO"]:
            riesgo = "ALTO"
        tendencia_final = "ASCENDENTE"
        confianza_final = max(confianza_final, 82)

    # INSOLVENCIA OPERATIVA INMINENTE -- multiples factores criticos
    factores_insolvencia = sum([
        "cartera vencida" in texto or "dejaron de pagar" in texto,
        "isr" in texto or "sat" in texto,
        "nomina" in texto,
        "linea de credito" in texto or "lineas de credito" in texto,
        "imss" in texto,
        "banco" in texto and ("garantias" in texto or "mora" in texto)
    ])
    if factores_insolvencia >= 4:
        riesgo = "CRITICO"
        tendencia_final = "ASCENDENTE"
        causas.append("INSOLVENCIA OPERATIVA INMINENTE -- multiples presiones criticas simultaneas")

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
            f"MESAN Omega -- Riesgo laboral detectado.\n\n"
            f"Se identificaron posibles contingencias operativas y laborales.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar acciones preventivas recomendadas."
        ),
        "FINANCIERO": (
            f"MESAN Omega -- Tension financiera detectada.\n\n"
            f"Se identifico posible presion sobre liquidez y continuidad operativa.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar escenarios de estabilizacion y reestructuracion."
        ),
        "SERVICIOS_APOYO": (
            f"MESAN Omega -- Riesgo operativo detectado.\n\n"
            f"Se identificaron posibles brechas de regularizacion relacionadas con cumplimiento REPSE.\n\n"
            f"Exposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\n"
            f"Responde SI para revisar acciones preventivas recomendadas."
        ),
    }
    whatsapp = mensajes_wa.get(industria,
        f"MESAN Omega -- Alerta {riesgo}\n\nDetectamos posible riesgo en tu operacion.\nExposicion estimada: ${impacto_min:,} - ${impacto_max:,} MXN\n\nResponde SI y te explicamos como prevenirlo."
    )

    # Escenarios coherentes -- exposicion total nunca menor que perdida base
    escenario_conservador = int(impacto * 0.80)
    escenario_probable    = int(impacto * 1.30)
    escenario_alto        = int(impacto * 2.50)

    # PLAN 30 DIAS DINAMICO
    if industria == "FINANCIERO":
        if riesgo == "CRITICO":
            consecuencias = [
                "Posible incumplimiento bancario",
                "Riesgo de atraso en nomina",
                "Presion severa de liquidez"
            ]
            plan_30 = [
                "Semana 1: Reestructuracion urgente de deuda bancaria",
                "Semana 2: Recorte de gastos no esenciales",
                "Semana 3: Negociacion con acreedores y flujo prioritario",
                "Semana 4: Estabilizacion de caja y control operativo"
            ]
        elif riesgo == "ALTO":
            consecuencias = [
                "Presion de liquidez progresiva",
                "Posibles atrasos en obligaciones",
                "Riesgo de deterioro operativo"
            ]
            plan_30 = [
                "Semana 1: Auditoria financiera especializada",
                "Semana 2: Ajuste operativo inmediato",
                "Semana 3: Control de pasivos y cobranza",
                "Semana 4: Monitoreo de flujo y estabilizacion"
            ]
        else:
            plan_30 = [
                f"Semana 1: Auditoria preventiva sector {industria}",
                "Semana 2: Regularizacion documental prioritaria",
                "Semana 3: Blindaje operativo y cumplimiento",
                "Semana 4: Monitoreo continuo y estabilizacion"
            ]
    else:
        plan_30 = [
            f"Semana 1: Auditoria preventiva sector {industria}",
            "Semana 2: Regularizacion documental prioritaria",
            "Semana 3: Blindaje operativo y cumplimiento",
            "Semana 4: Monitoreo continuo y estabilizacion"
        ]

    # MOTOR DE REFINAMIENTO
    refinamiento = {}
    if generar_refinamiento:
        try:
            refinamiento = generar_refinamiento({
                "industria":   industria,
                "riesgo":      riesgo,
                "impacto":     impacto,
                "impacto_min": impacto_min,
                "impacto_max": impacto_max,
                "causas":      causas
            })
        except Exception:
            pass

    # WhatsApp ejecutivo
    whatsapp = mensajes_wa.get(industria,
        f"MESAN Omega -- ALERTA {riesgo}\n\nDetectamos presion operativa en sector {industria}.\n\nExposicion estimada:\n${impacto_min:,} - ${impacto_max:,} MXN\n\nHemos preparado escenarios de estabilizacion y contencion.\n\nResponde SI para continuar el diagnostico ejecutivo."
    )

    disclaimer = (
        "Analisis preventivo generado por MESAN Omega Intelligence Engine. "
        "No constituye dictamen legal, fiscal, financiero ni resolucion oficial."
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
        "plan_30_dias": plan_30,
        "indice_riesgo": score_final,
        "nivel_score":   nivel_final,
        "confianza":     confianza_final,
        "tendencia":     tendencia_final,
        "origen":        origen_final,
        "whatsapp":      whatsapp,
        "disclaimer":    disclaimer,
        "escenarios": {
            "conservador": escenario_conservador,
            "probable":    escenario_probable,
            "alto":        escenario_alto
        },
        "cierre":        f"Se recomienda seguimiento preventivo especializado para el sector {industria}.",
        "refinamiento":  refinamiento
    }
