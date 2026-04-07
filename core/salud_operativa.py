def evaluar_salud_operativa(data):
    score = 0
    observaciones = []

    if data.get("procesos") == "no":
        score += 20
        observaciones.append("Empresa sin procesos definidos")

    if data.get("inspeccion") == "preocupado":
        score += 15
        observaciones.append("Alta vulnerabilidad ante inspeccion")

    if data.get("inspeccion") == "dudoso":
        score += 8
        observaciones.append("Inseguridad ante posible inspeccion")

    if data.get("historial") == "si":
        score += 20
        observaciones.append("Historial de multas o inspecciones previas")

    return {"score_operativo": score, "observaciones": observaciones}

