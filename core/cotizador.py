import logging

def calcular_cotizacion(lead) -> float:

    empleados = int(getattr(lead, "num_empleados", 0) or 0)
    riesgo = getattr(lead, "riesgo", "medio")
    impacto = getattr(lead, "impacto_max", 15000) or 15000

    base = empleados * 250

    factor_riesgo = {
        "bajo": 1,
        "medio": 1.5,
        "alto": 2.2
    }.get(str(riesgo).lower(), 1.5)

    factor_impacto = 1 + (float(impacto) / 50000)

    precio = base * factor_riesgo * factor_impacto

    precio = max(precio, 5000)
    precio = min(precio, 150000)

    return round(precio, 2)


def generar_mensaje_cotizacion(lead, link_pago=None) -> str:

    try:
        precio = calcular_cotizacion(lead)
    except Exception as e:
        logging.error(f"Error cotizacion: {e}")
        precio = 0

    precio_txt = f"${precio:,.0f} MXN" if precio else "monto personalizado"

    mensaje = f"""
Ya revisé tu caso a detalle.

El problema no es puntual — es estructural.
Si no se corrige, seguirás perdiendo dinero cada mes.

Para dejar tu operación en regla:

💰 Inversión estimada: {precio_txt}

Incluye:
- Corrección REPSE
- Cumplimiento IMSS
- Optimización de costos

"""

    if link_pago:
        mensaje += f"👉 Asegurar implementación ahora:\n{link_pago}\n\n"
    else:
        mensaje += "👉 Puedo explicarte cómo empezar paso a paso.\n\n"

    mensaje += "¿Te explico cómo lo implementamos contigo?"

    return mensaje.strip()
