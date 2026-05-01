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
    sector: str = "" # sector declarado desde frontend

# ═══ CONTEXTO REGULATORIO POR INDUSTRIA ═══
CONTEXTO_REGULATORIO = {
    "SALUD": """Marco regulatorio en México:
- COFEPRIS (Comisión Federal para la Protección contra Riesgos Sanitarios) — ente rector
- Aviso de funcionamiento obligatorio ante COFEPRIS
- NOM-004-SSA3 (expediente clínico), NOM-005-SSA3 y demás NOM aplicables
- Licencia sanitaria para establecimientos de salud
- IMSS obligatorio para todo el personal
- Responsabilidad penal del director técnico ante irregularidades""",

    "SEGURIDAD": """Marco regulatorio en México:
- Ley Federal de Seguridad Privada — marco rector (NO la CNBV, esa regula bancos)
- SSPC (Secretaría de Seguridad y Protección Ciudadana) — Permiso Federal obligatorio
- DGSP (Dirección General de Seguridad Privada) — registro federal obligatorio
- CUIP (Clave Única de Identificación Policial) para CADA elemento — sin esto no puede operar
- SEDENA — portación de armamento requiere permiso específico
- Fianza y seguro de responsabilidad civil obligatorios
- Sin registros: operación ilegal + nulidad de contratos + responsabilidad patrimonial personal

IMPACTO EN CASCADA (calcular siempre en este orden):
1. Pérdida de contratos corporativos (hospital, plazas): $300K-$900K MXN
2. Embargo IMSS por trabajadores no registrados o accidentes: $120K-$250K MXN  
3. Multas SSPC por operación ilegal: $100K-$500K MXN
4. Demandas laborales por accidentes sin cobertura: $80K-$300K MXN
5. Clausura + pérdida total de operación: impacto indefinido
TOTAL REAL: siempre superior a $500K MXN en casos con clientes corporativos""",

    "CONSTRUCCION": """Marco regulatorio en México:
- IMSS — registro obligatorio de TODOS los trabajadores en obra
- REPSE (Registro de Prestadoras de Servicios Especializados) — obligatorio si subcontrata
- STPS — normativa de seguridad e higiene en obra
- Licencias de construcción municipales
- Capital constitutivo IMSS ante accidentes de trabajadores no registrados
- Responsabilidad solidaria ante el contratante si hay incumplimiento""",

    "ALIMENTOS": """Marco regulatorio en México:
- COFEPRIS — licencia sanitaria obligatoria para establecimientos de alimentos
- NOM-251-SSA1 (buenas prácticas de higiene) — obligatoria
- Aviso de funcionamiento ante COFEPRIS
- Certificación en manipulación de alimentos para todo el personal
- IMSS para todo el personal
- Verificación periódica de COFEPRIS y riesgo de clausura inmediata""",

    "MANUFACTURA": """Marco regulatorio en México:
- STPS — seguridad e higiene industrial obligatoria
- IMSS — registro de todos los trabajadores de planta
- SEMARNAT — si hay procesos con impacto ambiental
- NOM aplicables según giro (NOM-001-STPS, NOM-002-STPS, etc.)
- Responsabilidad civil ante accidentes laborales sin cobertura IMSS""",

    "SERVICIOS_APOYO": """Marco regulatorio en México:
- REPSE (Registro de Prestadoras de Servicios Especializados) — obligatorio para limpieza, mantenimiento y outsourcing
- IMSS — registro obligatorio de TODOS los trabajadores
- STPS — condiciones de trabajo y seguridad
- LFT — contratos laborales firmados obligatorios
- Responsabilidad solidaria del contratante si hay incumplimiento IMSS/REPSE
- Sin REPSE: cliente puede rescindir contrato sin indemnización""",

    "RETAIL": """Marco regulatorio en México:
- LFT (Ley Federal del Trabajo) — contratos laborales obligatorios
- IMSS — registro de todo el personal
- SAT — facturación CFDI correcta y declaraciones fiscales
- PROFECO — derechos del consumidor
- Licencia de funcionamiento municipal""",

    "GENERAL": """Marco regulatorio en México:
- SAT — obligaciones fiscales, CFDI y declaraciones
- IMSS — seguridad social de todos los trabajadores
- LFT — contratos laborales y condiciones de trabajo
- STPS — condiciones de seguridad e higiene
- Licencias municipales de funcionamiento"""
}

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto

# Mapa de sectores válidos desde frontend
SECTORES_VALIDOS = {
    "salud": "SALUD",
    "tecnologia": "TECNOLOGIA",
    "saas": "TECNOLOGIA",
    "software": "TECNOLOGIA",
    "retail": "RETAIL",
    "comercio": "RETAIL",
    "construccion": "CONSTRUCCION",
    "inmobiliaria": "CONSTRUCCION",
    "manufactura": "MANUFACTURA",
    "industria": "MANUFACTURA",
    "alimentos": "ALIMENTOS",
    "restaurante": "ALIMENTOS",
    "servicios": "SERVICIOS_APOYO",
    "limpieza": "SERVICIOS_APOYO",
    "seguridad": "SEGURIDAD",
    "logistica": "LOGISTICA",
    "transporte": "LOGISTICA",
    "financiero": "FINANCIERO",
    "educacion": "EDUCACION",
    "general": "GENERAL"
}

# ═══════════════════════════════════════
# CLASIFICADOR DE DOCUMENTO (CAPA 0)
# ═══════════════════════════════════════
def clasificar_documento(texto: str) -> dict:
    t = texto.lower()

    # Tipo de documento
    tipo = "otro"
    if any(p in t for p in ["agradecimiento", "despedida", "otra empresa", "presupuestal",
                              "terminacion", "rescision", "cancelacion de contrato"]):
        tipo = "terminacion_servicio"
    elif any(p in t for p in ["acta", "inspeccion", "levantaron", "visita de verificacion"]):
        tipo = "inspeccion"
    elif any(p in t for p in ["requerimiento", "notificacion", "multa", "embargo", "clausura"]):
        tipo = "requerimiento_autoridad"
    elif any(p in t for p in ["contrato de servicio", "convenio", "acuerdo", "prestacion"]):
        tipo = "contrato"

    # Sector con reglas duras (alta confianza)
    sector_regla = None
    conf_regla = 0.0

    if any(p in t for p in ["cbtis", "preparatoria", "escuela", "colegio", "universidad",
                              "alumno", "docente", "plantel", "comite ceap"]):
        sector_regla = "EDUCACION"
        conf_regla = 0.95
    elif any(p in t for p in ["hospital", "clinica", "paciente", "cofepris", "medico"]):
        sector_regla = "SALUD"
        conf_regla = 0.95
    elif any(p in t for p in ["limpieza", "mantenimiento", "intendencia", "instalaciones"]):
        sector_regla = "SERVICIOS_APOYO"
        conf_regla = 0.88
    elif any(p in t for p in ["obra", "construccion", "albanil"]):
        sector_regla = "CONSTRUCCION"
        conf_regla = 0.90

    return {
        "tipo_documento": tipo,
        "sector_regla": sector_regla,
        "confianza_regla": conf_regla
    }

def detectar_industria(texto: str, sector_declarado: str = "") -> str:
    # 1. Si viene sector declarado desde el frontend → respetar
    if sector_declarado:
        s = sector_declarado.lower().strip()
        if s in SECTORES_VALIDOS:
            return SECTORES_VALIDOS[s]

    # 2. Scoring por keywords — evita falsos positivos
    import unicodedata
    t = "".join(c for c in unicodedata.normalize('NFD', texto.lower()) if unicodedata.category(c) != 'Mn')

    scores = {
        "TECNOLOGIA": 0, "SALUD": 0, "SERVICIOS_APOYO": 0,
        "CONSTRUCCION": 0, "MANUFACTURA": 0, "RETAIL": 0,
        "ALIMENTOS": 0, "SEGURIDAD": 0, "LOGISTICA": 0,
        "FINANCIERO": 0, "EDUCACION": 0
    }

    kw = {
        "TECNOLOGIA": ["saas", "software", "startup", "app", "plataforma digital",
                       "mrr", "churn", "sla", "aws", "infraestructura", "tech",
                       "desarrollador", "dev", "ingeniero", "suscripcion", "api"],
        "SALUD": ["clinica", "hospital", "cofepris", "medico", "doctor",
                  "farmacia", "consultorio", "enfermera", "salud", "nom-004"],
        "SERVICIOS_APOYO": ["limpieza", "aseo", "intendencia", "conserje",
                            "fumigacion", "jardineria", "outsourcing", "staffing",
                            "mantenimiento", "instalaciones del cliente",
                            "cancelacion de contrato", "rescision", "otra empresa",
                            "condiciones economicas", "presupuestal", "contrato de servicio",
                            "carta de agradecimiento", "terminacion de contrato"],
        "SEGURIDAD": ["seguridad privada", "vigilancia", "guardia", "custodia",
                      "sspc", "dgsp", "escolta", "cuip", "rondines",
                      "permiso federal", "empresa de seguridad", "guardias"],
        "CONSTRUCCION": ["construccion", "obra", "edificio", "albanil",
                         "concreto", "cemento", "vivienda", "repse"],
        "MANUFACTURA": ["fabrica", "manufactura", "maquila", "planta",
                        "produccion", "maquinaria", "automotriz", "plastico"],
        "RETAIL": ["tienda", "inventario", "merma", "pos", "supermercado",
                   "comercio", "mostrador"],
        "ALIMENTOS": ["restaurante", "cocina", "comida", "taqueria",
                      "hotel", "hospedaje", "catering"],
        "LOGISTICA": ["transporte", "logistica", "almacen", "bodega",
                      "flete", "trailer", "chofer"],
        "FINANCIERO": ["banco", "credito", "financiera", "sofom",
                       "aseguradora", "casa de bolsa"],
        "EDUCACION": ["escuela", "colegio", "universidad", "capacitacion"]
    }

    for sector, palabras in kw.items():
        for p in palabras:
            if p in t:
                # SEGURIDAD y ALIMENTOS tienen peso extra
                if sector == "SEGURIDAD":
                    scores[sector] += 4
                elif sector == "ALIMENTOS":
                    scores[sector] += 3
                else:
                    scores[sector] += 2

    mejor = max(scores, key=scores.get)
    if scores[mejor] > 0:
        return mejor

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

    elif industria == "SEGURIDAD":
        # Operación ilegal — base crítica
        causas.append("Operación sin Permiso Federal SSPC — ilegalidad total bajo Ley Federal de Seguridad Privada")
        impacto += 300000

        # Sin CUIP
        if any(p in texto for p in ["cuip", "sin cuip", "sin identificacion"]):
            causas.append("Personal sin CUIP — nulidad de contratos con clientes corporativos")
            impacto += 200000

        # Clientes corporativos en riesgo
        if any(p in texto for p in ["hospital", "plaza", "corporativo", "cliente grande", "contrato"]):
            causas.append("Contratos con clientes corporativos en riesgo de rescisión inmediata")
            impacto += 400000

        # IMSS vencido
        if any(p in texto for p in ["imss", "seguro", "accidente", "lesion"]):
            causas.append("IMSS vencido con accidentes laborales — responsabilidad patrimonial ilimitada")
            impacto += 250000

        # Inspección activa
        if any(p in texto for p in ["inspeccion", "notificacion", "aviso", "clausura"]):
            causas.append("Inspección activa — plazo de ejecución corriendo")
            impacto += 200000

        # Sin DGSP
        if any(p in texto for p in ["dgsp", "registro", "sin registro", "nunca"]):
            causas.append("Sin registro ante DGSP — nulidad de todos los contratos comerciales")
            impacto += 150000

        if respuestas.get("permiso") == "No":
            causas.append("Sin Permiso Federal confirmado — cierre operativo inminente")
            impacto += 200000

    elif industria == "CONSTRUCCION":
        if "obra" in texto:
            causas.append("Riesgo IMSS en obra — capitales constitutivos ante accidente")
            impacto += 150000
        if respuestas.get("imss_obra") == "Ninguno":
            causas.append("Trabajadores sin IMSS en obra — responsabilidad total del contratista")
            impacto += 100000
        if respuestas.get("repse") in ["Vencido", "No tengo"]:
            causas.append("REPSE vencido o inexistente — responsabilidad solidaria activa")
            impacto += 80000

    elif industria == "RETAIL":
        if any(p in texto for p in ["perdida", "inventario", "merma", "faltante", "robo", "hurto", "sustraccion"]):
            causas.append("Pérdidas en inventario — riesgo de robo interno o error operativo")
            impacto += 120000
        if any(p in texto for p in ["sucursal", "polanco", "punto de venta"]):
            causas.append("Incidencia en punto de venta — exposición patrimonial sin control")
            impacto += 60000
        if any(p in texto for p in ["rotacion", "empleados"]):
            causas.append("Alta rotación laboral — riesgo de demandas e inspecciones STPS")
            impacto += 60000
        if respuestas.get("contratos") == "No":
            causas.append("Sin contratos laborales firmados — vulnerabilidad legal total")
            impacto += 40000
        if respuestas.get("rotacion") == "Alta":
            causas.append("Alta rotación confirmada — posible patrón de sustracción sistemática")
            impacto += 50000

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
            causas.append("Paro prolongado — incumplimiento de pedidos inminente")
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

    causas_str = "\n".join(f"- {c}" for c in causas) if causas else "- Análisis inicial — sin causas específicas detectadas aún"
    resp_str = "\n".join(f"- {k}: {v}" for k, v in respuestas.items()) if respuestas else "Sin respuestas adicionales del cliente"
    ctx_regulatorio = CONTEXTO_REGULATORIO.get(industria, CONTEXTO_REGULATORIO["GENERAL"])

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

MARCO REGULATORIO APLICABLE (usa ÚNICAMENTE estas autoridades — no inventes otras):
{ctx_regulatorio}

Responde en este formato EXACTO:

1. Hallazgo Crítico:
Describe el problema central de forma directa y específica. Menciona la autoridad reguladora correcta del sector.

2. Implicación Operativa:
Explica cómo afecta la operación real de la empresa hoy. Sé concreto.

3. Riesgo Financiero:
Relaciona el problema con pérdida económica concreta en pesos mexicanos. Incluye multas reales del sector.

4. Escenario a 30 días:
Qué ocurrirá específicamente si no se actúa. Sé preciso con los plazos y consecuencias.

5. Recomendación Estratégica:
Acción clara, priorizada y ejecutable inmediatamente. Incluye los pasos específicos del sector.

Reglas:
- Lenguaje ejecutivo, no genérico
- NO repetir ideas entre secciones
- Citar SOLO las autoridades del marco regulatorio provisto — nunca inventar otras
- Conectar todo con dinero o riesgo real
- Sonar como consultor real de alto nivel, no como chatbot
- Máximo 3-4 oraciones por sección"""

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 900,
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

    # CAPA 0: Clasificar documento primero
    clasificacion_doc = clasificar_documento(texto)
    tipo_doc = clasificacion_doc["tipo_documento"]

    # Si es terminación de servicio → sector del cliente, no del proveedor
    if tipo_doc == "terminacion_servicio" and clasificacion_doc["sector_regla"]:
        industria = clasificacion_doc["sector_regla"]
    elif clasificacion_doc["sector_regla"] and clasificacion_doc["confianza_regla"] >= 0.90:
        industria = clasificacion_doc["sector_regla"]
    else:
        industria = detectar_industria(texto, data.sector or "")

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

    # Anthropic solo cuando hay respuestas
    analisis_ai = ""
    if respuestas:
        analisis_ai = await llamar_anthropic(texto, industria, impacto, riesgo, causas, respuestas)

    preguntas = generar_preguntas(industria, texto, riesgo)

    # WhatsApp dinámico
   if respuestas.get("acta") == "Acta levantada":
        whatsapp = (
            f"MESAN Ω — ALERTA CRÍTICA\n\n"
            f"Ya existe una inspección activa en tu operación.\n\n"
            f"Impacto estimado:\n"
            f"${impacto_min:,} – ${impacto_max:,} MXN\n\n"
            f"¿Ya te dejaron observaciones en el acta?\n\n"
            f"Te explico hoy mismo cómo evitar la sanción."
        )
    elif industria == "SEGURIDAD":
        whatsapp = (
            f"MESAN Ω — ALERTA CRÍTICA SEGURIDAD\n\n"
            f"SSPC + IMSS + clientes corporativos pueden detener tu empresa en menos de 30 días.\n\n"
            f"Impacto real estimado:\n"
            f"${impacto_min:,} – ${impacto_max:,} MXN + posible cierre operativo\n\n"
            f"¿Ya te notificaron formalmente o solo fue visita?"
        )
    else:
        causa_principal = causas[0] if causas else ""
        whatsapp = (
            f"MESAN Ω — ALERTA {industria}\n\n"
            f"Detectamos riesgo {riesgo} en tu operación.\n\n"
            f"{causa_principal}\n\n"
            f"Impacto estimado:\n"
            f"${impacto_min:,} – ${impacto_max:,} MXN\n\n"
            f"Si quieres lo vemos hoy y te digo exactamente cómo corregirlo en 30 días."
        )

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
            f"Semana 1: Auditoría especializada sector {industria}",
            "Semana 2: Regularización inmediata — corrección documental",
            "Semana 3: Blindaje legal y fiscal — prevención de sanciones",
            "Semana 4: Estabilización operativa — reducción de riesgo"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Este caso requiere atención especializada en {industria}. MESAN Ω puede resolverlo en 30 días."
    }
