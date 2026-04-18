def generar_plan_accion(data: dict, riesgo: int, imse: int) -> list:
    """
    Genera plan de acción basado en datos reales del diagnóstico.
    """
    acciones = []

    salario_real = data.get("salario_real", 0)
    salario_declarado = data.get("salario_declarado", 0)
    empleados_reales = data.get("empleados_reales", 0)
    empleados_imss = data.get("empleados_imss", 0)
    diferencias_cfdi = data.get("diferencias_cfdi", False)

    # SUBREGISTRO SALARIAL
    if salario_real > 0 and salario_declarado < salario_real:
        acciones.append({
            "problema": "Subregistro salarial detectado",
            "impacto": "Riesgo de multa y recálculo de cuotas IMSS",
            "accion": "Ajustar SBC al salario real",
            "prioridad": "ALTA",
            "tiempo": "Inmediato"
        })

    # EMPLEADOS NO REGISTRADOS
    if empleados_reales > empleados_imss:
        acciones.append({
            "problema": "Empleados no registrados en IMSS",
            "impacto": "Multa y riesgo penal laboral",
            "accion": "Regularizar plantilla faltante",
            "prioridad": "ALTA",
            "tiempo": "1-7 días"
        })

    # DIFERENCIAS CFDI
    if diferencias_cfdi:
        acciones.append({
            "problema": "Diferencias entre CFDI y nómina",
            "impacto": "Inconsistencia fiscal detectable por SAT",
            "accion": "Conciliar CFDI con dispersión real",
            "prioridad": "MEDIA",
            "tiempo": "7-15 días"
        })

    # IMSE BAJO
    if imse < 60:
        acciones.append({
            "problema": "Baja madurez de seguridad empresarial",
            "impacto": "Alta exposición a inspecciones",
            "accion": "Revisión integral de cumplimiento REPSE",
            "prioridad": "MEDIA",
            "tiempo": "15-30 días"
        })

    # RIESGO CRÍTICO
    if riesgo > 80:
        acciones.append({
            "problema": "Riesgo crítico detectado",
            "impacto": "Alta probabilidad de auditoría IMSS/SAT",
            "accion": "Auditoría inmediata y estrategia de regularización",
            "prioridad": "URGENTE",
            "tiempo": "Inmediato"
        })

    return acciones
