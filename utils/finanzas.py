def calcular_finanzas(precio, empleados, sueldo):
    costo_empleado = sueldo * 1.35
    costo_total = costo_empleado * empleados
    ingreso = precio * empleados
    utilidad = ingreso - costo_total

    margen = 0
    if ingreso > 0:
        margen = utilidad / ingreso

    return {
        "costo_empleado": round(costo_empleado, 2),
        "costo_total": round(costo_total, 2),
        "ingreso": round(ingreso, 2),
        "utilidad": round(utilidad, 2),
        "margen": round(margen, 4)
    }


def calcular_precio_sugerido(sueldo, margen_objetivo=0.25):
    costo = sueldo * 1.35
    return round(costo / (1 - margen_objetivo), 2)
