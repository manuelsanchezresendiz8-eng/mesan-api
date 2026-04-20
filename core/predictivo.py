def calcular_tendencia(scores_historicos: list) -> dict:
    if len(scores_historicos) < 2:
        return {"tendencia": "SIN_DATOS", "delta": 0}

    delta = scores_historicos[-1] - scores_historicos[0]

    if delta <= -15:
        tendencia = "DETERIORO ACELERADO"
    elif delta < 0:
        tendencia = "DETERIORO"
    elif delta == 0:
        tendencia = "ESTABLE"
    else:
        tendencia = "MEJORA"

    return {"tendencia": tendencia, "delta": delta}


def probabilidad_crisis(indice_omega: float, tendencia: str) -> float:
    base = indice_omega / 100

    ajuste = {
        "DETERIORO ACELERADO": 0.25,
        "DETERIORO": 0.15,
        "ESTABLE": 0,
        "MEJORA": -0.1
    }

    prob = base + ajuste.get(tendencia, 0)
    prob = max(0, min(1, prob))

    return round(prob * 100, 2)


def alerta_predictiva(indice_omega: float, probabilidad: float) -> dict:
    if probabilidad >= 70:
        nivel = "CRISIS INMINENTE"
        accion = "Intervencion inmediata requerida"
    elif probabilidad >= 50:
        nivel = "RIESGO ALTO"
        accion = "Correccion en menos de 30 dias"
    elif probabilidad >= 30:
        nivel = "VIGILANCIA"
        accion = "Monitoreo mensual"
    else:
        nivel = "ESTABLE"
        accion = "Operacion normal"

    return {"nivel_alerta": nivel, "accion": accion}
