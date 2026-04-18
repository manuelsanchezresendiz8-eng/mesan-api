def extraer_riesgo_ai(texto: str) -> int:

    t = texto.lower()

    if "crítico" in t or "critico" in t:
        return 85

    if any(x in t for x in ["alto riesgo", "riesgo alto"]):
        return 70

    if "alto" in t:
        return 65

    if "medio" in t:
        return 50

    if "bajo" in t:
        return 30

    return 50
