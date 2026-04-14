def evaluar_riesgo_laboral(data):
    empleados = int(data.get("empleados", 0))

    if empleados > 5:
        return {
            "riesgo": "ALTO",
            "mensaje": "Posible exposición laboral relevante"
        }

    return {
        "riesgo": "BAJO",
        "mensaje": "Riesgo laboral controlado"
    }


def check_labor_risk(tipo_contrato, recurrencia_meses):
    riesgo = "Bajo"
    recomendacion = "Sin observaciones."

    if tipo_contrato.lower() == "determinado" and recurrencia_meses >= 3:
        riesgo = "Crítico"
        recomendacion = (
            "Riesgo de demanda por estabilidad laboral. "
            "La recurrencia sugiere una relación permanente simulada (Art. 37 LFT)."
        )
    elif tipo_contrato.lower() == "determinado":
        riesgo = "Medio"
        recomendacion = "Asegurar que exista una causa técnica o sustitución temporal documentada."

    return {
        "nivel_riesgo": riesgo,
        "accion": recomendacion
    }


def calcular_margen_real(ingreso, costo_total, riesgo_laboral):
    utilidad_bruta = ingreso - costo_total

    provision_riesgo = 0
    if riesgo_laboral == "Crítico":
        provision_riesgo = max(0, utilidad_bruta * 0.15)

    utilidad_real = utilidad_bruta - provision_riesgo
    margen_real = (utilidad_real / ingreso) * 100 if ingreso > 0 else 0

    return {
        "margen_nominal": round((utilidad_bruta / ingreso) * 100, 2),
        "margen_real_ajustado": round(margen_real, 2),
        "provision_legal": round(provision_riesgo, 2)
    }

