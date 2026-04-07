def generar_comentarios(score, clasificacion):
    if clasificacion == "CRITICO":
        return "Tu empresa presenta riesgos inmediatos que pueden generar multas o perdidas economicas importantes. Se recomienda accion inmediata."

    if clasificacion == "VULNERABLE":
        return "Se detectaron areas de mejora que pueden convertirse en riesgos si no se corrigen pronto."

    if clasificacion == "INESTABLE":
        return "Tu empresa tiene vulnerabilidades moderadas. Es momento de tomar medidas preventivas."

    return "Tu empresa se encuentra en estado estable, pero puede optimizar procesos para mayor proteccion."


def interpretar_texto_libre(comentario):
    comentario = comentario.lower()
    datos = {
        "meses_adeudados": [],
        "tiene_infonavit": False,
        "retenia_isr": False
    }

    if "diciembre" in comentario:
        datos["meses_adeudados"].append((12, 2025))
    if "enero" in comentario:
        datos["meses_adeudados"].append((1, 2026))
    if "febrero" in comentario:
        datos["meses_adeudados"].append((2, 2026))
    if "marzo" in comentario:
        datos["meses_adeudados"].append((3, 2026))
    if "infonavit" in comentario or "vivienda" in comentario:
        datos["tiene_infonavit"] = True
    if "reten" in comentario or "nomina" in comentario:
        datos["retenia_isr"] = True

    return datos

