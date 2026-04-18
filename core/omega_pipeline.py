from core.data_normalizer import normalizar_data
from core.indice_omega import calcular_indice_omega, clasificar_omega
from core.action_engine import generar_plan_accion


def ejecutar_analisis_completo(data: dict, ai_text: str = "") -> dict:
    """
    Pipeline completo de análisis MESAN Omega.
    """

    # NORMALIZAR
    data = normalizar_data(data)

    # SCORES BASE
    cumplimiento = data.get("cumplimiento", 50)
    consistencia = data.get("consistencia", 50)
    operacion = data.get("operacion", 50)
    entropia = data.get("entropia", 50)

    # IMSE
    imse = round(
        (cumplimiento * 0.30) +
        (consistencia * 0.25) +
        (operacion * 0.25) +
        ((100 - entropia) * 0.20),
        2
    )

    # RIESGO
    riesgo = min(100, int(entropia * 0.5 + (100 - imse) * 0.5))

    # INDICE OMEGA
    indice = calcular_indice_omega(imse, entropia, riesgo)
    estado = clasificar_omega(indice)

    # PLAN DE ACCIÓN
    acciones = generar_plan_accion(data, riesgo, imse)

    return {
        "imse": imse,
        "riesgo": riesgo,
        "entropia": entropia,
        "indice_omega": indice,
        "estado_omega": estado,
        "acciones": acciones
    }
