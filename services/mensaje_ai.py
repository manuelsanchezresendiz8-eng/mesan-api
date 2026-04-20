def generar_mensaje(resultado: dict, nombre: str) -> str:

    indice = resultado.get("indice_omega", {}).get("indice_omega", 0)
    dinero = resultado.get("impacto", {}).get("impacto_anual_max", 0)

    if indice >= 75:
        return (
            f"{nombre}, detectamos un riesgo CRITICO en tu empresa.\n\n"
            f"Estimacion de perdida anual: ${dinero:,.0f} MXN\n\n"
            f"Esto ya te esta costando dinero hoy.\n\n"
            f"Recomendacion: intervencion inmediata.\n\n"
            f"¿Te explico en 10 minutos como resolverlo?"
        )

    elif indice >= 50:
        return (
            f"{nombre}, encontramos areas de riesgo operativo.\n\n"
            f"Podrias estar perdiendo hasta ${dinero:,.0f} MXN al año.\n\n"
            f"Esto lo vemos en muchas empresas justo antes de una auditoria.\n\n"
            f"¿Te muestro como optimizarlo?"
        )

    return (
        f"{nombre}, tu empresa esta estable.\n\n"
        f"Aun asi detectamos oportunidades de mejora.\n\n"
        f"¿Quieres que te explique como aprovecharlas?"
    )
