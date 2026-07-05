"""
MESAN Ω — Motor de Narrativa Ejecutiva v1
Genera análisis defendible en junta directiva.
"""

def generar_narrativa(resultado: dict) -> str:

    nivel = resultado.get("nivel_alerta", "GENERAL")
    sector = resultado.get("sector", "GENERAL")
    f = resultado.get("financiero", {})
    o = resultado.get("operativo", {})
    r = resultado.get("rotacion", {})

    deficit = f.get("deficit", 0)
    dias = f.get("dias", None)

    # =========================
    # 1. CAUSA RAÍZ
    # =========================
    if deficit > 0:
        causa = "desequilibrio estructural entre ingresos reales y costos fijos"
    elif r.get("impacto", 0) > 0:
        causa = "inestabilidad operativa por rotación de personal"
    else:
        causa = "ineficiencias operativas acumuladas"

    # =========================
    # 2. CONSECUENCIA
    # =========================
    if dias is not None and dias < 30:
        consecuencia = "interrupción operativa inminente por falta de liquidez"
    elif dias is not None and dias < 60:
        consecuencia = "presión financiera progresiva que limitará la operación"
    else:
        consecuencia = "deterioro gradual de la rentabilidad"

    # =========================
    # 3. CONTEXTO SECTORIAL
    # =========================
    contextos = {
        "TECNOLOGIA": (
            "En empresas tecnológicas, este patrón suele escalar rápidamente "
            "por dependencia de clientes clave y variabilidad en ingresos recurrentes."
        ),
        "SALUD": (
            "En el sector salud, esta situación se agrava por la exposición regulatoria "
            "y posibles sanciones por incumplimiento normativo COFEPRIS."
        ),
        "SERVICIOS_APOYO": (
            "En empresas de servicios especializados, este escenario impacta directamente "
            "en la continuidad operativa y estabilidad del personal asignado a clientes."
        ),
        "CONSTRUCCION": (
            "En construcción, el riesgo laboral y regulatorio (IMSS/REPSE) amplifica "
            "cualquier desequilibrio financiero con exposición a responsabilidad solidaria."
        ),
        "MANUFACTURA": (
            "En manufactura, la pérdida de flujo afecta capacidad de producción, "
            "cumplimiento de pedidos y estabilidad de la cadena de suministro."
        ),
        "RETAIL": (
            "En comercio, este desequilibrio suele manifestarse en pérdidas de inventario, "
            "rotación laboral y deterioro del punto de venta."
        ),
        "ALIMENTOS": (
            "En el sector alimentos, la presión financiera aumenta el riesgo sanitario "
            "por recortes en mantenimiento e higiene operativa."
        ),
        "SEGURIDAD": (
            "En seguridad privada, la falta de flujo compromete cumplimiento de SSPC "
            "y estabilidad del personal operativo ante clientes corporativos."
        ),
    }

    contexto = contextos.get(sector, (
        "Este tipo de desequilibrio suele derivar en pérdida de control financiero "
        "si no se corrige de forma inmediata."
    ))

    # =========================
    # 4. IMPLICACIÓN ESTRATÉGICA
    # =========================
    implicaciones = {
        "CRÍTICO": (
            "La organización ha entrado en una fase de riesgo sistémico "
            "donde la continuidad del negocio está comprometida."
        ),
        "ALTO": (
            "La empresa presenta vulnerabilidades que pueden escalar rápidamente "
            "si no se intervienen en los próximos 30 días."
        ),
        "MEDIO": (
            "Existen señales tempranas que requieren ajuste "
            "para evitar deterioro futuro."
        ),
    }

    implicacion = implicaciones.get(nivel, (
        "Se detectan áreas de mejora operativa con impacto en rentabilidad."
    ))

    # =========================
    # 5. ACCIÓN
    # =========================
    accion = (
        "Se requiere intervención inmediata enfocada en estabilizar flujo de efectivo, "
        "reducir exposición operativa y priorizar decisiones críticas de corto plazo."
    )

    return f"""Causa raíz: {causa}.

Consecuencia: {consecuencia}.

Contexto: {contexto}

Implicación: {implicacion}

Recomendación: {accion}""".strip()
