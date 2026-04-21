def normalizar_clasificacion(valor: str) -> str:

    if not valor:
        return "MEDIO"

    v = str(valor).upper().strip()

    mapa = {
        "ALTO": "ALTO",
        "IRP_HIGH": "RIESGO OPERATIVO",
        "HIGH": "RIESGO OPERATIVO",
        "CRITICO": "CRISIS FINANCIERA",
        "CRITICAL": "CRISIS FINANCIERA",
        "CRISIS": "CRISIS FINANCIERA",
        "CRISIS FINANCIERA": "CRISIS FINANCIERA",
        "RIESGO OPERATIVO": "RIESGO OPERATIVO",
        "RIESGO LEGAL": "RIESGO LEGAL",
        "RIESGO REPSE": "RIESGO REPSE",
        "IRP_MED": "INEFICIENCIA",
        "MEDIO": "MEDIO",
        "MEDIUM": "MEDIO",
        "INEFICIENCIA": "INEFICIENCIA",
        "IRP_LOW": "ESTABLE",
        "BAJO": "ESTABLE",
        "LOW": "ESTABLE",
        "ESTABLE": "ESTABLE",
        "PREVENTIVO ALTO": "RIESGO OPERATIVO",
        "CONTROLADO": "ESTABLE",
    }

    return mapa.get(v, "MEDIO")
