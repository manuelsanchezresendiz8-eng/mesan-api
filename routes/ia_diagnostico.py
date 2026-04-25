from fastapi import APIRouter
from pydantic import BaseModel
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.preguntas import generar_preguntas

router = APIRouter()

class InputAI(BaseModel):
    texto: str
    respuestas: dict = {}

def detectar_industria(texto: str) -> str:
    t = texto.lower()
    if any(p in t for p in ["consultorio", "medico", "clinica", "cofepris", "farmacia", "hospital"]):
        return "SALUD"
    if any(p in t for p in ["tienda", "ropa", "retail", "mostrador"]):
        return "RETAIL"
    if any(p in t for p in ["obra", "construccion", "albanil", "contratista"]):
        return "CONSTRUCCION"
    if any(p in t for p in ["restaurante", "cocina", "alimentos", "comida"]):
        return "ALIMENTOS"
    if any(p in t for p in ["fabrica", "produccion", "maquinaria", "planta", "linea"]):
        return "MANUFACTURA"
    return "GENERAL"

@router.post("/ai/diagnostico")
async def ai_diagnostico(data: InputAI):

    texto = data.texto.lower()
    respuestas = data.respuestas or {}

    industria = detectar_industria(texto)
    causas = []
    impacto = 0

    if industria == "SALUD":
        if "cofepris" in texto:
            causas.append("Revisión activa COFEPRIS — riesgo de clausura sanitaria")
            impacto += 90000
        if "consultorio" in texto:
            causas.append("Operación médica bajo inspección — validación NOM obligatoria")
            impacto += 40000
        if "asistente" in texto or "solo" in texto:
            causas.append("Estructura operativa mínima — mayor exposición en inspección")
            impacto += 20000
        # Segunda capa — respuestas del usuario
        if respuestas.get("acta") == "Acta levantada":
            causas.append("Acta de inspección levantada — proceso formal iniciado")
            impacto += 50000
        if respuestas.get("aviso") == "No":
            causas.append("Sin aviso de funcionamiento — operación ilegal ante COFEPRIS")
            impacto += 40000
        if respuestas.get("expediente") == "No":
            causas.append("Sin expediente sanitario — sin defensa ante inspección")
            impacto += 60000

    elif industria == "RETAIL":
        if "rotacion" in texto or "empleados" in texto:
            causas.append("Alta rotación laboral — riesgo de demandas e inspecciones")
            impacto += 60000
        if "contrato" in texto:
            causas.append("Sin contratos laborales — vulnerabilidad legal total")
            impacto += 50000
        if respuestas.get("contratos") == "No":
            impacto += 40000
            causas.append("Confirmado: sin contratos firmados")
        if respuestas.get("rotacion") == "Alta":
            impacto += 30000

    elif industria == "CONSTRUCCION":
        if "obra" in texto:
            causas.append("Riesgo IMSS en obra — capitales constitutivos")
            impacto += 150000
        if respuestas.get("imss_obra") == "Ninguno":
            impacto += 100000
            causas.append("Confirmado: trabajadores sin IMSS en obra")
        if respuestas.get("repse") in ["Vencido", "No tengo"]:
            impacto += 80000
            causas.append("REPSE vencido o inexistente")

    elif industria == "ALIMENTOS":
        if "cofepris" in texto or "inspeccion" in texto:
            causas.append("Inspección sanitaria activa — riesgo de clausura")
            impacto += 100000
        if respuestas.get("licencia") in ["Vencida", "No"]:
            impacto += 80000
            causas.append("Licencia sanitaria vencida o inexistente")

    elif industria == "MANUFACTURA":
        if any(p in texto for p in ["produccion", "maquinaria", "linea", "refaccion"]):
            causas.append("Falla en línea de producción — pérdida de capacidad operativa")
            impacto += 180000
        if respuestas.get("tiempo_paro") == "Más de 3 días":
            impacto += 100000
            causas.append("Paro prolongado — incumplimiento de pedidos inminente")

    else:
        if "imss" in texto:
            causas.append("Incumplimiento IMSS — multas y capitales constitutivos")
            impacto += 80000
        if "sat" in texto or "auditoria" in texto:
            causas.append("Auditoría SAT activa — riesgo de embargo")
            impacto += 200000
        if "contrato" in texto:
            causas.append("Sin contratos laborales — vulnerabilidad legal")
            impacto += 50000
        if "cfdi" in texto or "factura" in texto:
            causas.append("Inconsistencias CFDI — riesgo SAT")
            impacto += 120000

    if impacto == 0:
        impacto = 25000

    if impacto > 300000:
        riesgo = "CRÍTICO"
        prob = "ALTA"
        tendencia = "CRÍTICO — acción inmediata requerida"
    elif impacto > 100000:
        riesgo = "ALTO"
        prob = "ALTA"
        tendencia = "ALTO — con riesgo de escalar a CRÍTICO"
    elif impacto > 50000:
        riesgo = "MEDIO"
        prob = "MEDIA"
        tendencia = "MEDIO → con tendencia a ALTO"
    else:
        riesgo = "BAJO"
        prob = "BAJA"
        tendencia = "ESTABLE — monitoreo preventivo recomendado"

    impacto_min = impacto
    impacto_max = int(impacto * 3)

    preguntas = generar_preguntas(industria, texto, riesgo)

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
        "probabilidad": prob,
        "causas": causas,
        "consecuencias": consecuencias,
        "preguntas": preguntas,
        "plan_30_dias": [
            f"Semana 1: Auditoría especializada sector {industria}",
            "Semana 2: Corrección normativa y regularización",
            "Semana 3: Alineación fiscal y legal",
            "Semana 4: Blindaje operativo MESAN Ω"
        ],
        "whatsapp": whatsapp,
        "cierre": f"Este caso requiere atención especializada en {industria}. MESAN Ω puede resolverlo en 30 días. ¿Agendamos hoy?"
    }
