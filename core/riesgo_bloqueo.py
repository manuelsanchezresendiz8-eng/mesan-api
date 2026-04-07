def evaluar_riesgo_bloqueo(score_total):
    if score_total >= 120:
        return {
            "nivel": "ALTO RIESGO DE BLOQUEO",
            "mensaje": "Peligro inminente. El IMSS puede emitir orden de embargo de cuentas.",
            "documentos": [
                "Tarjeta de Identificacion Patronal (TIP)",
                "Identificacion oficial del Patron",
                "Poder Notarial (Personas Morales)",
                "Pago inicial del 20% del adeudo",
                "Formato de solicitud de convenio"
            ]
        }
    elif score_total >= 80:
        return {
            "nivel": "RIESGO MEDIO",
            "mensaje": "Atencion. Actuar antes de recibir notificacion oficial.",
            "documentos": [
                "Tarjeta de Identificacion Patronal (TIP)",
                "Identificacion oficial del Patron"
            ]
        }
    return {
        "nivel": "RIESGO BAJO",
        "mensaje": "Riesgo de congelamiento bajo por ahora.",
        "documentos": []
    }

