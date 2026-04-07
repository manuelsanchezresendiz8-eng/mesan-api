def calcular_riesgo_fiscal(data):
    score = 0
    alertas = []

    if data.get("factura") == "no":
        score += 40
        alertas.append("Discrepancia fiscal detectada (SAT)")

    if data.get("factura") == "no_seguro":
        score += 20
        alertas.append("Posible riesgo fiscal - revisar facturacion")

    if data.get("contabilidad") == "no_tiene":
        score += 30
        alertas.append("Sin control contable formal")

    if data.get("contabilidad") == "interno":
        score += 10
        alertas.append("Contabilidad interna - riesgo de errores")

    return {"score_fiscal": score, "alertas_fiscales": alertas}

