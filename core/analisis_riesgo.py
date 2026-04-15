def calcular_indice_cumplimiento(presupuesto_propuesto, sueldo_neto_total, zona_geografica="Nacional"):
    """
    Analiza si un presupuesto es legalmente viable en México.
    """
    isn_tasa = 0.04 if zona_geografica == "BC" else 0.03

    carga_social_minima = sueldo_neto_total * 0.35
    impuesto_nomina = sueldo_neto_total * isn_tasa

    costo_operativo_legal = sueldo_neto_total + carga_social_minima + impuesto_nomina

    if presupuesto_propuesto < costo_operativo_legal:
        return {
            "riesgo": "CRÍTICO",
            "diagnostico": "Presupuesto insuficiente para cubrir obligaciones de ley.",
            "deficit_estimado": round(costo_operativo_legal - presupuesto_propuesto, 2)
        }

    return {"riesgo": "BAJO", "diagnostico": "Cumplimiento normativo validado."}
