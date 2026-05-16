# services/repse.py — MESAN Ω v2.5.0

from core.repse import validar_giro_repse


def analizar_repse(data: dict) -> dict:
    giro = data.get("giro", "")
    contratos = data.get("contratos", "ninguno")
    imss = data.get("imss", data.get("registro_imss", "ninguno"))
    historial = data.get("historial", "no")
    factura = data.get("factura", data.get("situacion_fiscal", ""))

    validacion = validar_giro_repse(giro)
    alertas = []
    score = 100

    if contratos == "ninguno":
        score -= 30
        alertas.append("Sin contratos laborales")
    elif contratos == "algunos":
        score -= 15
        alertas.append("Algunos empleados sin contrato")

    if imss == "ninguno":
        score -= 30
        alertas.append("Sin registro IMSS")
    elif imss == "parcial":
        score -= 15
        alertas.append("Registro IMSS incompleto")

    if factura in ["irregular", "sin_facturar"]:
        score -= 20
        alertas.append("Facturacion irregular o ausente")

    if historial == "si":
        score -= 20
        alertas.append("Historial de multas previas")

    if not validacion["valido"]:
        score -= 10
        alertas.append(f"Giro '{giro}' no identificado en REPSE")

    score = max(0, score)

    if score < 50:
        nivel = "RIESGO CRITICO"
    elif score < 80:
        nivel = "RIESGO MEDIO"
    else:
        nivel = "CUMPLIMIENTO ALTO"

    return {
        "score_repse": score,
        "nivel": nivel,
        "alertas": alertas,
        "giro_valido": validacion["valido"],
        "descripcion_giro": validacion.get("descripcion", "")
    }
