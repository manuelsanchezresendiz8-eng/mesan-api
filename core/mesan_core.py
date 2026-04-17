def calcular_irp(respuestas):
    score = 0
    codigos = []

    factura = respuestas.get("factura", respuestas.get("situacion_fiscal", "si"))
    if factura == "no":
        score += 30
        codigos.append("F3_RISK")
    elif factura == "no_seguro":
        score += 20
        codigos.append("F2_WARN")
    else:
        codigos.append("F1_OK")

    contabilidad = respuestas.get("contabilidad", respuestas.get("gestion_contable", "externo"))
    if contabilidad == "no_tiene":
        score += 15
        codigos.append("F6_RISK")
    elif contabilidad == "interno":
        score += 10
        codigos.append("F5_WARN")
    else:
        codigos.append("F4_OK")

    imss = respuestas.get("imss", respuestas.get("registro_imss", "si"))
    if imss == "no":
        score += 40
        codigos.append("L3_RISK")
    elif imss == "parcial":
        score += 25
        codigos.append("L2_WARN")
    else:
        codigos.append("L1_OK")

    contratos = respuestas.get("contratos", respuestas.get("contratos_laborales", "si"))
    if contratos == "no":
        score += 15
        codigos.append("L6_RISK")
    elif contratos == "algunos":
        score += 10
        codigos.append("L5_WARN")
    else:
        codigos.append("L4_OK")

    rpbi = respuestas.get("rpbi", "no")
    if rpbi == "si":
        contrato_rpbi = respuestas.get("contrato_rpbi", "no")
        if contrato_rpbi == "no":
            score += 30
            codigos.append("H5_RISK")
        else:
            codigos.append("H4_OK")
    else:
        codigos.append("H0_NA")

    procesos = respuestas.get("procesos", respuestas.get("procesos_documentados", "si"))
    if procesos == "no":
        score += 30
        codigos.append("O3_RISK")
    else:
        codigos.append("O1_OK")

    inspeccion = respuestas.get("inspeccion", respuestas.get("ante_inspeccion", "preparado"))
    if inspeccion == "preocupado":
        score += 30
        codigos.append("P3_RISK")
    elif inspeccion == "dudoso":
        score += 15
        codigos.append("P2_WARN")
    else:
        codigos.append("P1_OK")

    historial = respuestas.get("historial", respuestas.get("historial_multas", "no"))
    if historial == "si":
        score += 20
        codigos.append("S2_ALERT")
    else:
        codigos.append("S1_OK")

    if score >= 70:
        nivel = "ALTO"
        irp = "IRP_HIGH"
    elif score >= 40:
        nivel = "MEDIO"
        irp = "IRP_MED"
    else:
        nivel = "BAJO"
        irp = "IRP_LOW"

    return {
        "score": score,
        "nivel": nivel,
        "codigo_irp": irp,
        "codigos_detectados": codigos
    }


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
