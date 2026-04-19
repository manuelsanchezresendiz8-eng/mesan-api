def simulador_empresarial(datos: dict) -> dict:
    """
    MESAN Omega - Simulador financiero empresarial
    3 escenarios + mejor decisión
    """

    precio = float(datos.get("precio_servicio", 0))
    empleados = int(datos.get("num_empleados", 1))
    salario = float(datos.get("salario_promedio", 300))

    costo = salario * empleados * 30

    actual = precio - costo
    subir = (precio * 1.2) - costo
    reducir = precio - (salario * max(1, int(empleados * 0.85)) * 30)

    escenarios = {
        "actual": actual,
        "subir_precio": subir,
        "reducir_personal": reducir
    }

    mejor = max(escenarios, key=escenarios.get)

    return {
        "actual": round(actual, 2),
        "subir_precio": round(subir, 2),
        "reducir_personal": round(reducir, 2),
        "mejor": mejor
    }
