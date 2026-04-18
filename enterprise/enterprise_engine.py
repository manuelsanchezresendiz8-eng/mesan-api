import math
import re
import urllib.parse
from io import BytesIO

# =========================
# HELPERS
# =========================
def safe_get(d, key, default=0):
    return d.get(key) if isinstance(d, dict) else default

def limpiar_telefono(tel):
    tel = re.sub(r"\D", "", tel or "")
    if not tel.startswith("52"):
        tel = "52" + tel
    return tel

# =========================
# SALARIOS MÉXICO 2026
# =========================
def salario_base(zona="general"):
    return 447.00 if zona == "frontera" else 248.93

# =========================
# MOTOR REPSE (COSTOS)
# =========================
def motor_repse(data):
    empleados = int(data.get("num_empleados", 1))
    zona = data.get("zona", "general")

    base = salario_base(zona)
    salario_real = base * 1.25

    nomina = salario_real * empleados * 30

    carga = 1 + 0.30 + 0.05 + 0.08 + 0.10 + 0.025
    costo_real = nomina * carga

    operativo = costo_real * (1 + 0.15 + 0.10 + 0.05)

    precio = operativo * 1.30

    alertas = []
    if data.get("contratos") != "todos":
        alertas.append("Contratos incompletos")
    if data.get("imss") != "completo":
        alertas.append("IMSS irregular")
    if data.get("factura", data.get("situacion_fiscal", "")) != "al_corriente":
        alertas.append("Facturacion irregular")

    riesgo = "BAJO"
    if len(alertas) >= 2:
        riesgo = "ALTO"
    elif len(alertas) == 1:
        riesgo = "MEDIO"

    return {
        "precio_recomendado": round(precio, 2),
        "costo_real": round(operativo, 2),
        "riesgo_repse": riesgo,
        "alertas": alertas
    }

# =========================
# AUDITORIA REPSE
# =========================
def auditoria_repse(data):
    score = 100
    alertas = []

    if data.get("contratos") == "ninguno":
        score -= 30
        alertas.append("Sin contratos")
    if data.get("imss") == "ninguno":
        score -= 30
        alertas.append("Sin IMSS")
    if data.get("factura", data.get("situacion_fiscal", "")) == "irregular":
        score -= 20
        alertas.append("Facturacion irregular")
    if data.get("historial") == "si":
        score -= 20
        alertas.append("Historial de multas")

    nivel = "CUMPLIMIENTO ALTO"
    if score < 50:
        nivel = "RIESGO CRITICO"
    elif score < 80:
        nivel = "RIESGO MEDIO"

    return {
        "score": score,
        "nivel": nivel,
        "alertas": alertas
    }

# =========================
# RENTABILIDAD
# =========================
def rentabilidad(data):
    precio = float(data.get("precio_servicio", 0))
    empleados = int(data.get("num_empleados", 1))
    salario = salario_base(data.get("zona", "general")) * 1.2

    costo = salario * empleados * 30
    utilidad = precio - costo
    margen = (utilidad / precio * 100) if precio else 0

    precio_ideal = costo * 1.5
    fuga_oculta = max(0, precio_ideal - precio)

    return {
        "utilidad": round(utilidad, 2),
        "margen": round(margen, 2),
        "precio_ideal": round(precio_ideal, 2),
        "fuga_oculta": round(fuga_oculta, 2)
    }

# =========================
# SIMULADOR
# =========================
def simulador(data):
    precio = float(data.get("precio_servicio", 0))
    empleados = int(data.get("num_empleados", 1))
    salario = salario_base(data.get("zona", "general")) * 1.2

    costo = salario * empleados * 30

    actual = precio - costo
    subir = (precio * 1.2) - costo
    reducir = precio - (salario * max(1, int(empleados * 0.85)) * 30)

    escenarios = {
        "actual": actual,
        "subir_precio": subir,
        "reducir_personal": reducir
    }

    mejor = max(escenarios, key=escenarios.get)

    return {
        "actual": round(actual, 2),
        "subir_precio": round(subir, 2),
        "reducir_personal": round(reducir, 2),
        "mejor": mejor
    }

# =========================
# CEO ENGINE
# =========================
def ceo_engine(rent: dict, sim: dict, auditoria: dict, repse: dict) -> dict:

    nivel_auditoria = (auditoria.get("nivel", "") or "").upper()
    utilidad = rent.get("utilidad", 0) or 0
    margen = rent.get("margen", 0) or 0
    riesgo_repse = (repse.get("riesgo_repse", "") or "").upper()
    mejor = sim.get("mejor", "actual")

    if nivel_auditoria == "RIESGO CRITICO":
        return {"decision": "RIESGO LEGAL", "prioridad": "URGENTE"}

    if utilidad < 0:
        return {"decision": "CRISIS FINANCIERA", "prioridad": "URGENTE"}

    if riesgo_repse == "ALTO" and margen < 15:
        return {"decision": "RIESGO OPERATIVO", "prioridad": "URGENTE"}

    if riesgo_repse == "ALTO":
        return {"decision": "RIESGO REPSE", "prioridad": "ALTA"}

    if margen < 20:
        return {"decision": "INEFICIENCIA", "prioridad": "ALTA"}

    if mejor != "actual" and sim.get(mejor, 0) > sim.get("actual", 0) * 1.1:
        return {"decision": "OPTIMIZACION", "prioridad": "MEDIA"}

    return {"decision": "ESTABLE", "prioridad": "BAJA"}

# =========================
# MENSAJE VENTA
# =========================
def mensaje_venta(nombre, ceo, rent, sim):
    fuga = safe_get(rent, "fuga_oculta", 0)
    actual = safe_get(sim, "actual", 0)
    mejor = safe_get(sim, "mejor", "actual")
    decision = safe_get(ceo, "decision", "ANALISIS")
    prioridad = safe_get(ceo, "prioridad", "MEDIA")

    return (
        f"Hola {nombre},\n\n"
        f"MESAN Omega detecto lo siguiente:\n\n"
        f"Estado: {decision}\n"
        f"Prioridad: {prioridad}\n\n"
        f"Perdida estimada mensual: ${fuga} MXN\n"
        f"Utilidad actual: ${actual} MXN\n"
        f"Mejor estrategia: {mejor}\n\n"
        f"Podemos corregir esto en dias.\n"
        f"Agenda tu llamada: https://wa.me/526861629643"
    )

# =========================
# WHATSAPP
# =========================
def link_whatsapp(tel, msg):
    tel = limpiar_telefono(tel)
    return f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"

# =========================
# PDF
# =========================
def generar_pdf(nombre, auditoria, repse):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        content = [
            Paragraph("Auditoria REPSE MESAN Omega", styles['Title']),
            Spacer(1, 12),
            Paragraph(f"Empresa: {nombre}", styles['Normal']),
            Paragraph(f"Nivel: {auditoria['nivel']}", styles['Normal']),
            Spacer(1, 8),
        ]

        for a in auditoria.get("alertas", []):
            content.append(Paragraph(f"- {a}", styles['Normal']))

        content.append(Spacer(1, 12))
        content.append(Paragraph(f"Precio recomendado: ${repse['precio_recomendado']}", styles['Normal']))
        content.append(Paragraph(f"Costo real: ${repse['costo_real']}", styles['Normal']))

        doc.build(content)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    except Exception as e:
        return None

# =========================
# SISTEMA ENTERPRISE (PRINCIPAL)
# =========================
def sistema_enterprise(data):

    nombre = data.get("nombre", "Empresa")
    telefono = data.get("telefono", "")

    try:
        repse = motor_repse(data)
    except Exception:
        repse = {}

    try:
        auditoria = auditoria_repse(data)
    except Exception:
        auditoria = {"nivel": "REVISION", "score": 50, "alertas": []}

    try:
        rent = rentabilidad(data)
    except Exception:
        rent = {"utilidad": 0, "margen": 0, "precio_ideal": 0, "fuga_oculta": 0}

    try:
        sim = simulador(data)
    except Exception:
        sim = {"actual": 0, "subir_precio": 0, "reducir_personal": 0, "mejor": "actual"}

    try:
        ceo = ceo_engine(rent, sim, auditoria, repse)
    except Exception:
        ceo = {"decision": "REVISION", "prioridad": "MEDIA"}

    msg = mensaje_venta(nombre, ceo, rent, sim)
    wa = link_whatsapp(telefono, msg)

    score = auditoria.get("score", 50)
    clasificacion = ceo.get("decision", "REVISION")

    return {
        "diagnostico": {"score": score},
        "clasificacion": clasificacion,
        "repse": repse,
        "auditoria": auditoria,
        "rentabilidad": rent,
        "simulacion": sim,
        "ceo": ceo,
        "whatsapp": wa,
        "soluciones": [{"area": a, "accion": "Corregir inmediatamente"} for a in auditoria.get("alertas", [])],
        "impacto": {
            "impacto_min": int(rent.get("fuga_oculta", 0)),
            "impacto_max": int(rent.get("fuga_oculta", 0) * 1.5)
        }
    }
