import math

def calcular_fuga_nomina_predictiva(datos: dict):

    salario_diario = float(datos.get("salario_promedio", 300))
    empleados = int(datos.get("num_empleados", 1))
    riesgo_base = datos.get("nivel_riesgo", "medio")

    factor_riesgo = {
        "bajo": 0.015,
        "medio": 0.03,
        "alto": 0.05
    }.get(riesgo_base, 0.03)

    fuga_mensual = salario_diario * empleados * factor_riesgo

    crecimiento = {
        "bajo": 1.02,
        "medio": 1.05,
        "alto": 1.10
    }.get(riesgo_base, 1.05)

    fuga_3m = sum(fuga_mensual * (crecimiento ** i) for i in range(1, 4))
    fuga_6m = sum(fuga_mensual * (crecimiento ** i) for i in range(1, 7))

    UMA = float(datos.get("uma", 108.57))
    empleados_norm = max(empleados, 1)
    multa_base = 50 * UMA
    exposicion_legal = 0
    contratos = datos.get("contratos", "completo")

    if contratos == "ninguno":
        exposicion_legal = multa_base * empleados_norm
    elif contratos == "parcial":
        exposicion_legal = (multa_base * empleados_norm) * 0.5

    base_scale = max(empleados * salario_diario * 30, 1)

    score_futuro = min(100, (
        (fuga_3m / base_scale) * 35 +
        (fuga_6m / (base_scale * 2)) * 35 +
        (exposicion_legal / (base_scale * 3)) * 30
    ))

    if score_futuro > 70:
        nivel = "CRITICO"
    elif score_futuro > 40:
        nivel = "ALTO"
    else:
        nivel = "MEDIO"

    return {
        "fuga_actual_mensual": round(fuga_mensual, 2),
        "fuga_3m": round(fuga_3m, 2),
        "fuga_6m": round(fuga_6m, 2),
        "exposicion_legal": round(exposicion_legal, 2),
        "score_predictivo": round(score_futuro, 2),
        "nivel": nivel
    }
