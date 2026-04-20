try:
    from core.validador_sat import validar_cfdi
except:
    validar_cfdi = None

try:
    from core.validador_imss import validar_nomina
except:
    validar_nomina = None


def motor_institucional(data: dict) -> dict:

    riesgos = []
    alertas = []
    impacto_total = 0

    # VALIDACION SAT
    if data.get("cfdi") and validar_cfdi:
        sat = validar_cfdi(data["cfdi"])
        if sat.get("riesgo"):
            riesgos.append("SAT")
            alertas.extend(sat.get("alertas", []))

    # VALIDACION IMSS
    if data.get("nomina") and validar_nomina:
        nomina = data["nomina"]
        imss = validar_nomina(
            nomina.get("empleados", 0),
            nomina.get("imss", 0)
        )
        if imss.get("riesgo"):
            riesgos.append("IMSS")
            alertas.append(imss.get("mensaje", ""))
            impacto_total += imss.get("impacto_estimado", 0)

    # SECTOR GOBIERNO
    if data.get("sector") == "gobierno":
        if not data.get("licitacion_vigente"):
            riesgos.append("LICITACION")
            alertas.append("Licitacion vencida o no vigente")
        if not data.get("partida_presupuestal"):
            riesgos.append("PRESUPUESTO")
            alertas.append("Partida presupuestal no asignada")

    # NIVEL FINAL
    if len(riesgos) >= 3:
        nivel = "CRITICO"
    elif len(riesgos) == 2:
        nivel = "ALTO"
    elif len(riesgos) == 1:
        nivel = "MEDIO"
    else:
        nivel = "CONTROLADO"

    return {
        "riesgos_detectados": riesgos,
        "nivel_institucional": nivel,
        "alertas": alertas,
        "impacto_estimado": impacto_total,
        "sector": data.get("sector", "privado")
    }
