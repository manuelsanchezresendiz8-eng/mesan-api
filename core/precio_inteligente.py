def calcular_precio_cierre(costo_total: float):

    precio_minimo = round(costo_total / 0.95, 2)
    precio_objetivo = round(costo_total / 0.80, 2)
    precio_cierre = round((precio_minimo + precio_objetivo) / 2, 2)

    return {
        "precio_minimo": precio_minimo,
        "precio_objetivo": precio_objetivo,
        "precio_cierre": precio_cierre
    }
