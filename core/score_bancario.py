import math

def calcular_score_bancario(datos: dict) -> dict:
    """
    MESAN Omega - Scoring tipo banco (FICO-style)
    Rango: 0 - 1000
    """

    salario = float(datos.get("salario_promedio", 300))
    empleados = int(datos.get("num_empleados", 1))
    contratos = datos.get("contratos", "completo")
    imss = datos.get("imss", "completo")
    historial = datos.get("historial", "no")

    score = 650

    if contratos == "ninguno":
        score -= 180
    elif contratos == "parcial":
        score -= 90

    if imss == "ninguno":
        score -= 150
    elif imss == "parcial":
        score -= 70

    if historial == "si":
        score -= 120
    else:
        score += 40

    ratio_nomina = empleados * salario
    factor_empresa = min(
        math.log1p(ratio_nomina) / math.log1p(2000000),
        1
    )
    score -= factor_empresa * 80

    if ratio_nomina > 100000:
        score -= 50

    score = max(0, min(1000, score))

    if score >= 800:
        nivel = "AAA"
    elif score >= 650:
        nivel = "AA"
    elif score >= 500:
        nivel = "A"
    elif score >= 350:
        nivel = "B"
    else:
        nivel = "C"

    return {
        "score": round(score, 2),
        "nivel": nivel
    }
