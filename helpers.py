def normalizar_clasificacion(valor):
    if not valor:
        return "MEDIO"

    v = str(valor).upper()

    if v in ["ALTO", "CRITICO", "CRÍTICO"]:
        return "ALTO"
    if v in ["MEDIO", "VULNERABLE", "INESTABLE"]:
        return "MEDIO"
    if v in ["BAJO", "ESTABLE"]:
        return "BAJO"

    return "MEDIO"
