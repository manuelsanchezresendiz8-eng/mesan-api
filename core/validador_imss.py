def validar_nomina(empleados: int, reportados_imss: int) -> dict:

    if empleados <= 0:
        return {
            "status": "SIN_DATOS",
            "riesgo": False,
            "mensaje": "Sin empleados registrados"
        }

    diferencia = empleados - reportados_imss

    if diferencia <= 0:
        return {
            "status": "OK",
            "riesgo": False,
            "empleados_total": empleados,
            "reportados_imss": reportados_imss,
            "diferencia": 0,
            "mensaje": "Nomina correctamente registrada"
        }

    porcentaje_omision = round((diferencia / empleados) * 100, 2)

    if porcentaje_omision >= 50:
        nivel = "CRITICO"
    elif porcentaje_omision >= 25:
        nivel = "ALTO"
    else:
        nivel = "MEDIO"

    impacto_estimado = diferencia * 48000

    return {
        "status": "SUBDECLARACION",
        "riesgo": True,
        "nivel": nivel,
        "empleados_total": empleados,
        "reportados_imss": reportados_imss,
        "empleados_no_registrados": diferencia,
        "porcentaje_omision": porcentaje_omision,
        "impacto_estimado": impacto_estimado,
        "mensaje": f"{diferencia} empleados sin registro IMSS detectados"
    }
