# routes/predictivo_ptu.py — MESAN Ω
from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/v1/predictivo", tags=["Inteligencia Predictiva PTU"])

def money(value) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

class ConfiguracionSimulacion(BaseModel):
    anio_a_proyectar: int
    cambio_utilidad_porcentaje: float = Field(default=0.0, ge=-100, le=1000)
    cambio_plantilla_porcentaje: float = Field(default=0.0, ge=-90, le=500)
    utilidad_base_referencia: Optional[float] = Field(default=1000000.0)

def simular_escenario_financiero(db_remanente_actual, nomina_actual_total_salarios, total_empleados_actuales, config):
    if total_empleados_actuales <= 0:
        raise ValueError("La plantilla actual debe ser mayor a cero.")
    if nomina_actual_total_salarios <= 0:
        raise ValueError("La nomina actual debe ser mayor a cero.")

    utilidad_base = Decimal(str(config.utilidad_base_referencia))
    remanente     = Decimal(str(db_remanente_actual))
    nomina        = Decimal(str(nomina_actual_total_salarios))

    factor_utilidad   = Decimal(str(1 + config.cambio_utilidad_porcentaje / 100))
    utilidad_proy     = utilidad_base * factor_utilidad
    bolsa_total       = utilidad_proy + remanente

    factor_plantilla  = Decimal(str(1 + config.cambio_plantilla_porcentaje / 100))
    empleados_proy    = max(1, int(total_empleados_actuales * float(factor_plantilla)))

    ptu_por_empleado  = bolsa_total / Decimal(str(empleados_proy))
    salario_prom_mes  = nomina / Decimal(str(total_empleados_actuales)) / Decimal("12")
    tope_3_meses      = salario_prom_mes * Decimal("3")

    if ptu_por_empleado > tope_3_meses:
        efectivo_real    = tope_3_meses * Decimal(str(empleados_proy))
        nuevo_remanente  = bolsa_total - efectivo_real
    else:
        efectivo_real    = bolsa_total
        nuevo_remanente  = Decimal("0")

    alerta = nuevo_remanente > (utilidad_proy * Decimal("0.10"))
    nivel  = "ALTO" if alerta else "MEDIO" if nuevo_remanente > utilidad_proy * Decimal("0.05") else "BAJO"

    return {
        "anio_proyectado":                    config.anio_a_proyectar,
        "utilidad_pura_proyectada":           money(utilidad_proy),
        "remanente_anterior_aplicado":        money(remanente),
        "bolsa_repartible_estimada":          money(bolsa_total),
        "empleados_proyectados":              empleados_proy,
        "salario_mensual_promedio":           money(salario_prom_mes),
        "tope_promedio_3_meses":              money(tope_3_meses),
        "ptu_promedio_sin_tope":              money(ptu_por_empleado),
        "salida_efectivo_estimada_ptu":       money(efectivo_real),
        "nuevo_remanente_acumulado_estimado": money(nuevo_remanente),
        "nivel_riesgo_financiero":            nivel,
        "alerta_optimizacion":                alerta
    }

@router.post("/simular-ptu")
def post_simular_escenarios(config: ConfiguracionSimulacion):
    try:
        resultado = simular_escenario_financiero(120500.00, 2400000.00, 25, config)
        diagnostico    = "Flujo optimizado. Los topes absorben correctamente la dispersion PTU."
        recomendaciones = []
        if resultado["alerta_optimizacion"]:
            diagnostico = "ALERTA DE RETENCION FINANCIERA: El remanente proyectado es elevado."
            recomendaciones = [
                "Analizar bonos deducibles antes del cierre fiscal.",
                "Evaluar crecimiento de plantilla operativa.",
                "Dispersar compensaciones variables trimestrales.",
                "Revisar estrategia fiscal preventiva PTU.",
                "Simular escenarios con incremento salarial."
            ]
        elif resultado["nivel_riesgo_financiero"] == "MEDIO":
            recomendaciones = ["Monitorear remanente trimestralmente.", "Revisar estructura salarial."]
        return {"status": "success", "simulacion": resultado, "diagnostico_estrategico": diagnostico, "recomendaciones": recomendaciones}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulando PTU: {str(e)}")
