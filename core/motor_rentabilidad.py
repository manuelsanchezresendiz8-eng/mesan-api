def motor_rentabilidad(datos: dict) -> dict:
    """
    MESAN Omega - Motor de rentabilidad empresarial
    """

    precio = float(datos.get("precio_servicio", 0))
    empleados = int(datos.get("num_empleados", 1))
    salario = float(datos.get("salario_promedio", 300))

    costo_nomina = salario * empleados * 30
    utilidad = precio - costo_nomina
    margen = (utilidad / precio * 100) if precio else 0

    precio_ideal = costo_nomina * 1.5
    fuga_oculta = max(0, precio_ideal - precio)

    if margen < 0:
        estado = "PERDIENDO DINERO"
    elif margen < 20:
        estado = "MARGEN CRITICO"
    elif margen < 40:
        estado = "MARGEN BAJO"
    else:
        estado = "SALUDABLE"

    return {
        "costo_nomina": round(costo_nomina, 2),
        "utilidad": round(utilidad, 2),
        "margen": round(margen, 2),
        "estado": estado,
        "precio_ideal": round(precio_ideal, 2),
        "fuga_oculta": round(fuga_oculta, 2)
    }
