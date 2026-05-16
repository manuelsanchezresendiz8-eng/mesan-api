# core/indice_omega.py — MESAN Ω v2.5.0

def calcular_indice_omega(imse: float, riesgo: int, cumplimiento: float = 50) -> dict:
    """
    Score maestro 0-100. Combina IMSE, riesgo IRP y cumplimiento.
    Mas alto = mas seguro.
    """
    base = 100
    penalizacion = (riesgo * 0.5) + ((100 - imse) * 0.3) + ((100 - cumplimiento) * 0.2)
    indice = max(0, round(base - penalizacion, 2))

    if indice >= 75:
        estado = "ESTABLE"
    elif indice >= 50:
        estado = "RIESGO MEDIO"
    elif indice >= 25:
        estado = "RIESGO ALTO"
    else:
        estado = "CRISIS"

    return {
        "indice_omega": indice,
        "estado": estado
    }
