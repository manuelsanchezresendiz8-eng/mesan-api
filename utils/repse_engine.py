def calcular_semaforo_repse(datos):
    riesgo_acumulado = 0
    alertas = []

    sector = str(datos.get("sector", "")).lower()

    if not datos.get("tiene_repse") and sector in ["construccion", "construcción", "logistica", "logística"]:
        impacto = datos.get("facturacion_mensual", 0) * 0.30
        riesgo_acumulado += impacto
        alertas.append({
            "tipo": "REPSE",
            "nivel": "CRITICO",
            "mensaje": "Facturacion no deducible sin REPSE",
            "impacto": round(impacto, 2)
        })

    empleados = datos.get("empleados", 0)
    if empleados > 0:
        multa_imss = empleados * 12500
        riesgo_acumulado += multa_imss
        alertas.append({
            "tipo": "IMSS",
            "nivel": "ALTO",
            "mensaje": "Riesgo de capitales constitutivos",
            "impacto": multa_imss
        })

    if riesgo_acumulado > 500000:
        color = "ROJO"
    elif riesgo_acumulado > 100000:
        color = "AMARILLO"
    else:
        color = "VERDE"

    return {
        "color": color,
        "exposicion_financiera": round(riesgo_acumulado, 2),
        "alertas": alertas,
        "total_alertas": len(alertas)
    }
