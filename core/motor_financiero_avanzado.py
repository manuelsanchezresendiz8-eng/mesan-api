# core/motor_financiero_avanzado.py — MESAN Ω
# Motor financiero v31 — flujo, liquidez, deuda

def analizar_finanzas(data: dict) -> dict:
    ingresos     = float(data.get("ingresos", 0))
    egresos      = float(data.get("egresos", 0))
    activos      = float(data.get("activos", 0))
    pasivos      = float(data.get("pasivos", 0))
    obligaciones = float(data.get("obligaciones", 0))

    flujo        = ingresos - egresos
    flujo_aj     = flujo - obligaciones
    deuda_ratio  = round(pasivos / activos, 2) if activos else 0

    # Liquidez
    if ingresos > 0:
        cobertura = ingresos / obligaciones if obligaciones else 99
        if cobertura >= 2:
            liquidez = "SALUDABLE"
        elif cobertura >= 1:
            liquidez = "AJUSTADA"
        else:
            liquidez = "CRITICA"
    else:
        liquidez = "SIN_DATOS"

    # Nivel
    if flujo_aj < 0 or deuda_ratio > 1.5:
        nivel = "CRITICO"
    elif flujo_aj < ingresos * 0.10 or deuda_ratio > 1.0:
        nivel = "ALTO"
    elif flujo_aj < ingresos * 0.20:
        nivel = "MEDIO"
    else:
        nivel = "ESTABLE"

    impacto = abs(round(flujo_aj * 12, 0)) if flujo_aj < 0 else round(flujo_aj * 0.2, 0)

    causa_raiz = (
        "Egresos superan ingresos — deficit operativo activo" if flujo < 0
        else "Obligaciones consumen margen operativo" if flujo_aj < 0
        else "Deuda elevada respecto a activos" if deuda_ratio > 1
        else "Operacion financieramente estable"
    )

    plan = [
        "1. Auditoria de egresos — identificar gastos no criticos",
        "2. Negociacion con acreedores — diferir obligaciones 60-90 dias",
        "3. Incremento de liquidez — factoraje o linea de credito",
        "4. Revision de estructura de costos fijos",
        "5. Monitoreo mensual de flujo ajustado"
    ]

    return {
        "nivel":          nivel,
        "liquidez":       liquidez,
        "flujo":          round(flujo, 2),
        "flujo_ajustado": round(flujo_aj, 2),
        "deuda_ratio":    deuda_ratio,
        "impacto":        int(impacto),
        "_causa_raiz":    causa_raiz,
        "_plan_accion":   plan
    }
