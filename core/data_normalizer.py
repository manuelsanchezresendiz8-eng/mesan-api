# core/data_normalizer.py

def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ["true", "1", "yes", "si", "sí"]
    return False


def normalizar_data(data: dict) -> dict:
    return {
        "cumplimiento": data.get("cumplimiento", 50),
        "consistencia": data.get("consistencia", 50),
        "operacion": data.get("operacion", 50),
        "defensa": data.get("defensa", 50),

        "salario_real": float(data.get("salario_real", 0) or 0),
        "salario_declarado": float(data.get("salario_declarado", 0) or 0),

        "empleados_reales": int(data.get("empleados_reales", 0) or 0),
        "empleados_imss": int(data.get("empleados_imss", 0) or 0),

        "diferencias_cfdi": parse_bool(data.get("diferencias_cfdi", False)),

        "entropia": data.get("entropia", 50),

        "factura": data.get("factura", data.get("situacion_fiscal", "")),
        "imss": data.get("imss", data.get("registro_imss", "")),
        "contratos": data.get("contratos", data.get("contratos_laborales", "")),
        "procesos": data.get("procesos", data.get("procesos_documentados", "")),
        "inspeccion": data.get("inspeccion", data.get("ante_inspeccion", "")),
        "historial": data.get("historial", data.get("historial_multas", "")),

        "nombre": (data.get("nombre", "") or "").strip(),
        "email": (data.get("email", "") or "").strip(),
        "telefono": (data.get("telefono", "") or "").strip(),
        "giro": (data.get("giro", "") or "").strip(),
        "zona": data.get("zona", "general"),
        "empleados": int(data.get("empleados", data.get("num_empleados", 1)) or 1),
        "precio_servicio": float(data.get("precio_servicio", 0) or 0),
    }

# v2 — actualizado
