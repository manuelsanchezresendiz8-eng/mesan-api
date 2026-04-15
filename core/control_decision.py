def evaluar_decision(f):

    if f["utilidad"] < 0:
        return {"decision": "RECHAZAR", "mensaje": "Genera pérdida"}

    if f["margen"] < 10:
        return {"decision": "ADVERTENCIA", "mensaje": "Margen bajo"}

    if f["margen"] >= 20:
        return {"decision": "APROBADO", "mensaje": "Operación saludable"}

    return {"decision": "REVISAR", "mensaje": "Margen mejorable"}
