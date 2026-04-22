# core/omega_pipeline.py

import logging

try:
    from core.data_normalizer import normalizar_data
except:
    normalizar_data = None

try:
    from core.irp_engine import calcular_irp, mapear_soluciones, calcular_impacto_economico
except:
    calcular_irp = None

try:
    from core.action_engine import generar_plan_accion
except:
    generar_plan_accion = None

try:
    from core.events import emit
except:
    emit = None


def ejecutar_analisis_completo(data: dict, ai_text: str = "") -> dict:

    # 1. NORMALIZAR
    if normalizar_data:
        data = normalizar_data(data)

    # 2. IRP
    resultado_irp = {"score": 0, "nivel": "BAJO", "codigo_irp": "IRP_LOW", "codigos_detectados": []}
    if calcular_irp:
        try:
            resultado_irp = calcular_irp(data)
        except Exception as e:
            logging.error(f"Error IRP: {e}")

    # 3. SOLUCIONES
    soluciones = []
    if mapear_soluciones:
        try:
            soluciones = mapear_soluciones(resultado_irp.get("codigos_detectados", []))
        except Exception as e:
            logging.error(f"Error soluciones: {e}")

    # 4. IMPACTO
    impacto = {"impacto_min": 0, "impacto_max": 0, "impacto_anual_min": 0, "impacto_anual_max": 0}
    if calcular_impacto_economico:
        try:
            impacto = calcular_impacto_economico(soluciones, data.get("empleados", 1))
        except Exception as e:
            logging.error(f"Error impacto: {e}")

    # 5. PLAN DE ACCION
    acciones = []
    if generar_plan_accion:
        try:
            acciones = generar_plan_accion(
                data,
                resultado_irp.get("score", 0),
                data.get("operacion", 50)
            )
        except Exception as e:
            logging.error(f"Error acciones: {e}")

    # 6. EMITIR EVENTO
    if emit:
        try:
            emit("ANALISIS_COMPLETO", {
                "score": resultado_irp.get("score", 0),
                "nivel": resultado_irp.get("nivel", "BAJO")
            })
        except Exception as e:
            logging.error(f"Error emit: {e}")

    return {
        "resultado": resultado_irp,
        "soluciones": soluciones,
        "impacto": impacto,
        "acciones": acciones,
        "diagnostico": {
            "score": resultado_irp.get("score", 0)
        },
        "clasificacion": resultado_irp.get("nivel", "BAJO")
    }

# v2 — actualizado
