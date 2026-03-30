def calcular_irp(respuestas):
    score = 0
    codigos = []

    if respuestas["factura"] == "no":
        score += 30; codigos.append("F3_RISK")
    elif respuestas["factura"] == "no_seguro":
        score += 20; codigos.append("F2_WARN")
    else:
        codigos.append("F1_OK")

    if respuestas["contabilidad"] == "no_tiene":
        score += 15; codigos.append("F6_RISK")
    elif respuestas["contabilidad"] == "interno":
        score += 10; codigos.append("F5_WARN")
    else:
        codigos.append("F4_OK")

    if respuestas["imss"] == "no":
        score += 40; codigos.append("L3_RISK")
    elif respuestas["imss"] == "parcial":
        score += 25; codigos.append("L2_WARN")
    else:
        codigos.append("L1_OK")

    if respuestas["contratos"] == "no":
        score += 15; codigos.append("L6_RISK")
    elif respuestas["contratos"] == "algunos":
        score += 10; codigos.append("L5_WARN")
    else:
        codigos.append("L4_OK")

    if respuestas["rpbi"] == "si":
        if respuestas["contrato_rpbi"] == "no":
            score += 30; codigos.append("H5_RISK")
        else:
            codigos.append("H4_OK")
    else:
        codigos.append("H0_NA")

    if respuestas["procesos"] == "no":
        score += 30; codigos.append("O3_RISK")
    else:
        codigos.append("O1_OK")

    if respuestas["inspeccion"] == "preocupado":
        score += 30; codigos.append("P3_RISK")
    elif respuestas["inspeccion"] == "dudoso":
        score += 15; codigos.append("P2_WARN")
    else:
        codigos.append("P1_OK")

    if respuestas["historial"] == "si":
        score += 20; codigos.append("S2_ALERT")
    else:
        codigos.append("S1_OK")

    if score >= 70:
        nivel = "ALTO"; irp = "IRP_HIGH"
    elif score >= 40:
        nivel = "MEDIO"; irp = "IRP_MED"
    else:
        nivel = "BAJO"; irp = "IRP_LOW"

    return {"score": score, "nivel": nivel, "codigo_irp": irp, "codigos_detectados": codigos}


def mapear_soluciones(codigos):
    soluciones = {
        "F3_RISK": {"area": "Fiscal", "accion": "Regularizar facturacion", "prioridad": "ALTA"},
        "L3_RISK": {"area": "Laboral", "accion": "Registrar empleados IMSS", "prioridad": "ALTA"},
        "H5_RISK": {"area": "Sanitario", "accion": "Contratar RPBI", "prioridad": "ALTA"},
        "O3_RISK": {"area": "Operativo", "accion": "Crear procesos", "prioridad": "ALTA"},
        "P3_RISK": {"area": "Legal", "accion": "Preparacion inspeccion", "prioridad": "ALTA"},
        "S2_ALERT": {"area": "Historico", "accion": "Auditoria preventiva", "prioridad": "ALTA"},
    }
    return [{"codigo": c, **soluciones[c]} for c in codigos if c in soluciones]


def calcular_impacto_economico(soluciones):
    tabulador = {
        "F3_RISK": {"min": 19500, "max": 65000, "prob": 0.7},
        "L3_RISK": {"min": 48000, "max": 120000, "prob": 0.8},
        "H5_RISK": {"min": 85000, "max": 150000, "prob": 0.6},
        "O3_RISK": {"min": 12000, "max": 50000, "prob": 1.0},
        "S2_ALERT": {"min": 25000, "max": 60000, "prob": 0.9}
    }
    impacto_min = 0
    impacto_max = 0
    for s in soluciones:
        data = tabulador.get(s["codigo"], {"min": 5000, "max": 15000, "prob": 1})
        impacto_min += data["min"] * data["prob"]
        impacto_max += data["max"] * data["prob"]
    return {
        "impacto_min": int(impacto_min),
        "impacto_max": int(impacto_max),
        "impacto_anual_min": int(impacto_min * 12),
        "impacto_anual_max": int(impacto_max * 12)
    }


def ejecutar_diagnostico(data):
    r = calcular_irp(data)
    s = mapear_soluciones(r["codigos_detectados"])
    i = calcular_impacto_economico(s)
    return {"resultado": r, "soluciones": s, "impacto": i}
Cuando lo tengas pegado → click "Commit changes" 🎯
