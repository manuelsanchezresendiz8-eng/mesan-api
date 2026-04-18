def calcular_indice_omega(imse: float, entropia: float, risk: float) -> int:
    """
    Normaliza el IMSE a impacto negativo y calcula el Riesgo Maestro.
    0 = Perfección / 100 = Colapso inminente.
    """
    impacto_imse = 100 - imse

    indice = (
        (impacto_imse * 0.40) +
        (entropia * 0.30) +
        (risk * 0.30)
    )

    return int(indice)


def clasificar_omega(indice: int) -> str:
    """
    Categorización de estado crítico para toma de decisiones.
    """
    if indice >= 80:
        return "COLAPSO_PROBABLE"
    if indice >= 60:
        return "ALTO_RIESGO"
    if indice >= 40:
        return "INESTABLE"
    return "CONTROLADO"
