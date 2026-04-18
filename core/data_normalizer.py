def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "si"]
    return False


def normalizar_data(data: dict) -> dict:
    return {
        "cumplimiento": data.get("cumplimiento", 50),
        "consistencia": data.get("consistencia", 50),
        "operacion": data.get("operacion", 50),
        "defensa": data.get("defensa", 50),

        "salario_real": data.get("salario_real", 0),
        "salario_declarado": data.get("salario_declarado", 0),

        "empleados_reales": data.get("empleados_reales", 0),
        "empleados_imss": data.get("empleados_imss", 0),

        "diferencias_cfdi": parse_bool(data.get("diferencias_cfdi", False)),

        "entropia": data.get("entropia", 50),

        "precio_servicio": float(data.get("precio_servicio", 0)),
        "num_empleados": int(data.get("num_empleados", 1)),
        "zona": data.get("zona", "general"),
        "giro": data.get("giro", ""),

        "factura": data.get("factura", data.get("situacion_fiscal", "al_corriente")),
        "imss": data.get("imss", data.get("registro_imss", "completo")),
        "contratos": data.get("contratos", "todos"),
        "procesos": data.get("procesos", "si"),
        "inspeccion": data.get("inspeccion", "preparado"),
        "historial": data.get("historial", "no"),
    }
