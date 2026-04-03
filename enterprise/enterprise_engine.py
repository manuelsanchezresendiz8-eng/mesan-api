def clasificar_cliente(score, impacto_anual):
    if impacto_anual > 1000000:
        return "CRITICO"
    elif impacto_anual > 500000:
        return "ALTO RIESGO"
    elif score >= 70:
        return "VULNERABLE"
    elif score >= 40:
        return "INESTABLE"
    else:
        return "ESTABLE"

def sistema_enterprise(data):
    from core.mesan_core import calcular_irp, mapear_soluciones, calcular_impacto_economico
    resultado = calcular_irp(data)
    soluciones = mapear_soluciones(resultado["codigos_detectados"])
    impacto = calcular_impacto_economico(soluciones)
    clasificacion = clasificar_cliente(resultado["score"], impacto["impacto_anual_max"])
    return {
        "diagnostico": resultado,
        "clasificacion": clasificacion,
        "soluciones": soluciones,
        "impacto": impacto
    }
