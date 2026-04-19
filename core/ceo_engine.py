def ceo_engine(rent: dict, sim: dict, auditoria: dict, repse: dict) -> dict:
    """
    MESAN Omega - CEO Engine v2
    Toma decisiones empresariales con 4 inputs.
    """

    nivel_auditoria = (auditoria.get("nivel", "") or "").upper()
    utilidad = rent.get("utilidad", 0) or 0
    margen = rent.get("margen", 0) or 0
    riesgo_repse = (repse.get("riesgo_repse", "") or "").upper()
    mejor = sim.get("mejor", "actual")

    if nivel_auditoria == "RIESGO CRITICO":
        return {"decision": "RIESGO LEGAL", "prioridad": "URGENTE"}

    if utilidad < 0:
        return {"decision": "CRISIS FINANCIERA", "prioridad": "URGENTE"}

    if riesgo_repse == "ALTO" and margen < 15:
        return {"decision": "RIESGO OPERATIVO", "prioridad": "URGENTE"}

    if riesgo_repse == "ALTO":
        return {"decision": "RIESGO REPSE", "prioridad": "ALTA"}

    if margen < 20:
        return {"decision": "INEFICIENCIA", "prioridad": "ALTA"}

    if mejor != "actual" and sim.get(mejor, 0) > sim.get("actual", 0) * 1.1:
        return {"decision": "OPTIMIZACION", "prioridad": "MEDIA"}

    return {"decision": "ESTABLE", "prioridad": "BAJA"}
