def calcular_fuga_nomina(datos: dict):

    salario_diario = float(datos.get("salario_promedio", 300))
    empleados = int(datos.get("num_empleados", 1))
    tipo_riesgo = datos.get("nivel_riesgo", "medio")
    contratos = datos.get("contratos", "completo")

    riesgo_factor = {
        "bajo": 0.015,
        "medio": 0.03,
        "alto": 0.05
    }.get(tipo_riesgo, 0.03)

    fuga_operativa = salario_diario * empleados * riesgo_factor

    UMA = float(datos.get("uma", 108.57))
    multa_base = 50 * UMA
    exposicion_legal = 0

    if contratos == "ninguno":
        exposicion_legal += multa_base * empleados
    elif contratos == "parcial":
        exposicion_legal += (multa_base * empleados) * 0.5

    total_fuga = fuga_operativa + exposicion_legal

    riesgo_score = min(100, (
        (exposicion_legal / 10000) * 40 +
        (fuga_operativa / 5000) * 60
    ))

    return {
        "fuga_operativa_estimada": round(fuga_operativa, 2),
        "exposicion_legal_estimada": round(exposicion_legal, 2),
        "total_fuga": round(total_fuga, 2),
        "riesgo_score": round(riesgo_score, 2),
        "nivel": (
            "CRITICO" if riesgo_score > 70 else
            "ALTO" if riesgo_score > 40 else
            "MEDIO"
        )
    }fuga_nomina.py
