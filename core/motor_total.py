import logging

try:
    from core.irp_engine import calcular_irp, mapear_soluciones, calcular_impacto_economico, resumen_ejecutivo_pro
except Exception as e:
    logging.error(f"Error importando irp_engine: {e}")
    calcular_irp = None

try:
    from core.omega_engine import MesanOmega
    omega = MesanOmega()
except Exception as e:
    logging.error(f"Error importando omega_engine: {e}")
    omega = None

try:
    from core.indice_omega import calcular_indice_omega
except Exception as e:
    logging.error(f"Error importando indice_omega: {e}")
    calcular_indice_omega = None

try:
    from core.predictivo import calcular_tendencia, probabilidad_crisis, alerta_predictiva
except Exception as e:
    logging.error(f"Error importando predictivo: {e}")
    calcular_tendencia = None


def motor_total(data: dict) -> dict:

    if not calcular_irp:
        return {
            "error": "Motor no disponible",
            "resultado": {"score": 0, "nivel": "N/A"},
            "soluciones": [],
            "impacto": {"impacto_min": 0, "impacto_max": 0, "impacto_anual_min": 0, "impacto_anual_max": 0},
            "indice_omega": {"indice_omega": 0, "decision": "N/A"},
            "resumen": {"estado": "N/A"}
        }

    # 1. IRP
    resultado_irp = calcular_irp(data)

    # 2. SOLUCIONES
    soluciones = mapear_soluciones(resultado_irp["codigos_detectados"])

    # 3. IMPACTO
    empleados = data.get("empleados", 50)
    impacto = calcular_impacto_economico(soluciones, empleados)

    # 4. INDICE OMEGA
    indice_omega = {"indice_omega": 0, "decision": "N/A"}
    if calcular_indice_omega:
        imse_val = 50
        if omega:
            imse_data = omega.calcular_imse(
                data.get("F", 50),
                data.get("O", 50),
                data.get("S", 50),
                data.get("N", 50)
            )
            imse_val = imse_data.get("imse", 50)

        indice_omega = calcular_indice_omega(
            resultado_irp["score"],
            imse_val,
            impacto.get("impacto_anual_max", 0)
        )

    # 5. IMSE
    imse_data = {}
    if omega:
        imse_data = omega.calcular_imse(
            data.get("F", 50),
            data.get("O", 50),
            data.get("S", 50),
            data.get("N", 50)
        )

    # 6. PREDICTIVO
    predictivo = {}
    if calcular_tendencia:
        historico = data.get("historico_scores", [indice_omega["indice_omega"]])
        tendencia = calcular_tendencia(historico)
        prob = probabilidad_crisis(indice_omega["indice_omega"], tendencia["tendencia"])
        alerta = alerta_predictiva(indice_omega["indice_omega"], prob)
        predictivo = {
            "tendencia": tendencia,
            "probabilidad_crisis": prob,
            "alerta": alerta
        }

    # 7. RESUMEN
    resumen = resumen_ejecutivo_pro(soluciones, impacto)

    return {
        "resultado": resultado_irp,
        "soluciones": soluciones,
        "impacto": impacto,
        "indice_omega": indice_omega,
        "imse": imse_data,
        "predictivo": predictivo,
        "resumen": resumen,
        "dinero_perdido_mensual": impacto.get("impacto_max", 0),
        "urgencia": resumen["estado"]
    }
