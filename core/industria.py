"""
MESAN Ω — Motor de Clasificación Industrial
Basado en SCIAN México con normalización ortográfica
"""
import unicodedata
from datetime import datetime

# ═══════════════════════════════════════════════════════
# DETECTOR DE INDUSTRIA
# ═══════════════════════════════════════════════════════

def detectar_industria(texto: str) -> str:
    t = "".join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

    # SECTOR 11 — AGROPECUARIO Y PESCA
    if any(p in t for p in [
        "campo", "agricultura", "agricola", "cultivo", "siembra", "cosecha",
        "ganaderia", "ganado", "bovino", "porcino", "avicola", "aves", "granja",
        "rancho", "forestal", "madera", "tala", "vivero", "pesca", "acuicultura",
        "camaricultura", "invernadero", "hidroponia", "fertilizante", "riego"
    ]):
        return "AGROPECUARIO"

    # SECTOR 21-22 — ENERGÍA Y EXTRACTIVA
    if any(p in t for p in [
        "mineria", "mina", "extraccion", "petroleo", "gas", "pemex", "cfe",
        "electricidad", "panel solar", "fotovoltaico", "subestacion", "hidroelectrica",
        "cantera", "arena", "grava", "litio", "yacimiento", "gasolinera", "combustible"
    ]):
        return "ENERGIA_MINERIA"

    # SECTOR 23 — CONSTRUCCIÓN E INMOBILIARIA
    if any(p in t for p in [
        "construccion", "obra", "edificio", "vivienda", "fraccionamiento",
        "arquitecto", "ingenieria civil", "inmobiliaria", "bienes raices",
        "remodelacion", "pintura", "impermeabilizacion", "concreto", "cemento",
        "lote", "terreno", "desarrolladora", "repse", "albanil"
    ]):
        return "CONSTRUCCION_INMOBILIARIA"

    # SECTOR 31-33 — MANUFACTURA
    if any(p in t for p in [
        "fabrica", "manufactura", "planta", "maquila", "maquiladora", "ensamble",
        "automotriz", "autopartes", "metalica", "plastico", "quimica", "textil",
        "alimentos procesados", "empaque", "linea de produccion", "mantenimiento industrial",
        "maquinaria", "herramental", "muebles", "electronica", "fundicion"
    ]):
        return "MANUFACTURA"

    # SECTOR 43-46 — RETAIL Y COMERCIO
    if any(p in t for p in [
        "tienda", "comercio", "retail", "supermercado", "abarrotes",
        "ropa", "calzado", "ferreteria", "refaccionaria", "punto de venta", "pos",
        "inventario", "merma", "faltante", "robo hormiga", "perdida de inventario",
        "perdidas en inventario", "mostrador", "distribuidor", "mayorista", "ecommerce",
        "sucursal", "polanco", "boutique", "papeleria", "joyeria"
    ]):
        return "RETAIL"

    # SECTOR 48-49 — LOGÍSTICA Y TRANSPORTE
    if any(p in t for p in [
        "transporte", "flete", "logistica", "almacen", "bodega", "cedis",
        "paqueteria", "mensajeria", "trailer", "camion", "chofer", "operador",
        "mudanza", "aduana", "importacion", "exportacion", "ultima milla"
    ]):
        return "LOGISTICA"

    # SECTOR 52 — FINANCIERO
    if any(p in t for p in [
        "banco", "bancario", "credito", "prestamo", "financiera", "sofom",
        "casa de bolsa", "cnbv", "condusef", "aseguradora", "seguro",
        "afore", "pension", "fintech", "pagos digitales", "casa de cambio"
    ]):
        return "FINANCIERO"

    # SECTOR 54-56 — SERVICIOS PROFESIONALES Y APOYO
    if any(p in t for p in [
        "consultoria", "despacho", "abogado", "contador", "auditoria", "fiscal",
        "marketing", "publicidad", "recursos humanos", "reclutamiento", "outsourcing",
        "limpieza", "aseo", "fumigacion", "jardineria",
        "call center", "contact center"
    ]):
        return "SERVICIOS_ESPECIALIZADOS"

    # SECTOR 56 — SEGURIDAD PRIVADA (separado por su regulación específica)
    if any(p in t for p in [
        "seguridad privada", "vigilancia", "guardia", "custodia", "escolta",
        "proteccion", "sspc", "dgsp", "rnsp", "monitoreo alarmas"
    ]):
        return "SEGURIDAD"

    # SECTOR 61 — EDUCACIÓN
    if any(p in t for p in [
        "escuela", "colegio", "universidad", "instituto", "capacitacion", "curso",
        "preescolar", "primaria", "secundaria", "preparatoria", "sep", "rvoe"
    ]):
        return "EDUCACION"

    # SECTOR 62 — SALUD
    if any(p in t for p in [
        "hospital", "clinica", "medico", "doctor", "dentista", "laboratorio clinico",
        "farmaceutica", "optica", "psicologo", "veterinaria", "salud",
        "cofepris", "nom-004", "expediente clinico", "enfermera", "consultorio"
    ]):
        return "SALUD"

    # SECTOR 71 — ENTRETENIMIENTO
    if any(p in t for p in [
        "gimnasio", "spa", "estetica", "barberia", "entretenimiento",
        "cine", "teatro", "casino", "bar", "antro", "discoteca",
        "club deportivo", "salon de eventos"
    ]):
        return "ENTRETENIMIENTO"

    # SECTOR 72 — HOSPITALIDAD Y ALIMENTOS
    if any(p in t for p in [
        "restaurante", "cocina", "cafeteria", "taqueria", "comida",
        "hotel", "motel", "airbnb", "hospedaje", "banquetes", "catering",
        "comedor industrial", "panaderia", "pasteleria"
    ]):
        return "HOSPITALIDAD_ALIMENTOS"

    # SECTOR 81-93 — OTROS Y GOBIERNO
    if any(p in t for p in [
        "taller mecanico", "autolavado", "lavanderia", "funeraria",
        "asociacion", "ong", "iglesia", "sindicato",
        "gobierno", "municipio", "sat", "imss", "licitacion"
    ]):
        return "SERVICIOS_GENERALES_GOBIERNO"

    # TECNOLOGÍA
    if any(p in t for p in [
        "software", "app", "startup", "saas", "ecommerce digital",
        "programacion", "developer", "sistemas", "ia", "machine learning",
        "ciberseguridad", "cloud", "hosting"
    ]):
        return "TECNOLOGIA"

    return "POR_CLASIFICAR"


# ═══════════════════════════════════════════════════════
# CALCULADORA DE IMPACTO MESAN Ω
# ═══════════════════════════════════════════════════════

def calcular_impacto_mesan(industria: str, ventas_mensuales: float, perdida_detectada: float) -> dict:
    """
    Calcula el impacto financiero real basado en sector y fuga detectada.
    perdida_detectada = porcentaje de pérdida (ej: 5 = 5%)
    """
    impacto_directo = ventas_mensuales * (perdida_detectada / 100)
    impacto_anual = impacto_directo * 12

    factores_riesgo = {
        "RETAIL":                  1.25,
        "MANUFACTURA":             1.40,
        "LOGISTICA":               1.30,
        "HOSPITALIDAD_ALIMENTOS":  1.50,
        "CONSTRUCCION_INMOBILIARIA": 1.35,
        "SEGURIDAD":               1.20,
        "SALUD":                   1.30,
        "FINANCIERO":              1.45,
        "ENERGIA_MINERIA":         1.60,
        "AGROPECUARIO":            1.20,
        "EDUCACION":               1.10,
        "SERVICIOS_ESPECIALIZADOS": 1.15,
        "TECNOLOGIA":              1.20,
    }

    factor = factores_riesgo.get(industria, 1.10)
    impacto_total = impacto_anual * factor

    if perdida_detectada > 8:
        nivel = "CRITICO"
    elif perdida_detectada > 4:
        nivel = "ALTO"
    elif perdida_detectada > 2:
        nivel = "MEDIO"
    else:
        nivel = "OBSERVACION"

    return {
        "perdida_mensual_neta": round(impacto_directo, 2),
        "proyeccion_anual_real": round(impacto_total, 2),
        "factor_riesgo_sector": factor,
        "nivel_alerta": nivel
    }


# ═══════════════════════════════════════════════════════
# GENERADOR DE REPORTE EJECUTIVO MESAN Ω
# ═══════════════════════════════════════════════════════

def generar_reporte_ejecutivo(datos_auditoria: dict, impacto: dict) -> str:
    """
    Genera reporte ejecutivo tipo Big4.
    datos_auditoria: { industria, hallazgo, puntos_control: [str, str] }
    """
    fecha = datos_auditoria.get("fecha", datetime.now().strftime("%d/%m/%Y"))
    industria = datos_auditoria.get("industria", "NO CLASIFICADO")
    hallazgo = datos_auditoria.get("hallazgo", "Sin hallazgo registrado")
    puntos = datos_auditoria.get("puntos_control", ["Por definir", "Por definir"])

    reporte = f"""
REPORTE DE INTERVENCIÓN MESAN Ω — {fecha}
{'─' * 58}
SECTOR:           {industria}
NIVEL DE ALERTA:  {impacto['nivel_alerta']}
{'─' * 58}

HALLAZGO CRÍTICO:
{hallazgo}

1. IMPACTO ECONÓMICO PROYECTADO:
   Pérdida mensual neta:     ${impacto['perdida_mensual_neta']:>14,.2f} MXN
   Proyección anual real:    ${impacto['proyeccion_anual_real']:>14,.2f} MXN
   Factor de riesgo sector:  {impacto['factor_riesgo_sector']}x

2. PUNTOS DE CONTROL A INTERVENIR:
   → {puntos[0] if len(puntos) > 0 else 'Por definir'}
   → {puntos[1] if len(puntos) > 1 else 'Por definir'}

3. ACCIÓN DE SOBERANÍA (INMEDIATA):
   Intervención técnica requerida en sector {industria}.
   MESAN Ω puede resolver en 30 días. ¿Agendamos hoy?

{'─' * 58}
ESTADO: {impacto['nivel_alerta']} — REQUIERE EJECUCIÓN PRIORITARIA
MESAN Ω © 2026 — SOBERANÍA EMPRESARIAL
"""
    return reporte.strip()
