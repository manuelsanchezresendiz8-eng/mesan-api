# services/labor_shield_engine.py -- MESAN Omega Labor Shield Engine v2.1
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.labor")


def safe_int(value, default=0):
    try: return int(value)
    except: return default

def safe_float(value, default=0):
    try: return float(value)
    except: return default

def safe_bool(value, default=False):
    if isinstance(value, bool): return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true","1","si","yes"): return True
        if v in ("false","0","no"):      return False
    return default


class LaborShieldEngine:

    def __init__(self):
        self.version = "2.1"
        self.engine  = "MESAN_LABOR_SHIELD"

    def analizar(self, data: dict) -> dict:
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        empleados      = safe_int(data.get("empleados"))
        sin_imss       = safe_int(data.get("trabajadores_sin_imss"))
        demandas       = safe_int(data.get("demandas_laborales"))
        rotacion_anual = safe_float(data.get("rotacion_anual"))
        repse_vigente  = safe_bool(data.get("repse_vigente", True), True)
        contratos_ok   = safe_bool(data.get("contratos_individuales", True), True)
        subcontratacion= safe_bool(data.get("subcontratacion_activa", False), False)
        jornadas_ok    = safe_bool(data.get("jornadas_documentadas", True), True)

        if empleados <= 10:    categoria = "MICRO"
        elif empleados <= 50:  categoria = "PYME"
        elif empleados <= 250: categoria = "MEDIANA"
        else:                  categoria = "CORPORATIVO"

        score = 100; riesgos = []; recomendaciones = []; exposicion = 0

        if empleados > 0:
            ratio = sin_imss / max(empleados, 1)
            if ratio > 0.10:
                penalizacion = 25 if ratio > 0.30 else 15
                score -= penalizacion; exposicion += sin_imss * 15000
                riesgos.append({"riesgo":"IMSS","severidad":"CRITICA","detalle":f"{sin_imss} trabajadores sin IMSS"})
                recomendaciones.append("Regularizar afiliacion IMSS de toda la plantilla")

        if demandas > 0:
            penalizacion = min(demandas * 10, 30)
            score -= penalizacion; exposicion += demandas * 80000
            riesgos.append({"riesgo":"DEMANDAS_LABORALES","severidad":"ALTA","detalle":f"{demandas} demandas activas"})
            recomendaciones.append("Atender demandas laborales activas y revisar causas raiz")

        if rotacion_anual > 30:
            score -= 15; exposicion += 50000
            riesgos.append({"riesgo":"ROTACION","severidad":"MEDIA","detalle":f"Rotacion {rotacion_anual}% anual"})
            recomendaciones.append("Implementar programa de retencion de talento")

        if not repse_vigente:
            score -= 25; exposicion += 200000
            riesgos.append({"riesgo":"REPSE","severidad":"CRITICA","detalle":"REPSE suspendido o vencido"})
            recomendaciones.append("Renovar o reactivar REPSE de forma urgente")

        if not contratos_ok:
            score -= 15; exposicion += 40000
            riesgos.append({"riesgo":"CONTRATOS","severidad":"MEDIA","detalle":"Contratos individuales incompletos"})
            recomendaciones.append("Regularizar contratos individuales de trabajo")

        if subcontratacion and not repse_vigente:
            score -= 20; exposicion += 150000
            riesgos.append({"riesgo":"SUBCONTRATACION","severidad":"CRITICA","detalle":"Subcontratacion activa sin REPSE"})
            recomendaciones.append("Suspender subcontratacion hasta regularizar REPSE")

        if not jornadas_ok:
            score -= 10; exposicion += 20000
            riesgos.append({"riesgo":"JORNADAS","severidad":"MEDIA","detalle":"Jornadas no documentadas"})
            recomendaciones.append("Documentar jornadas y horas extra conforme a LFT")

        score = max(score, 0)

        if score >= 80:   nivel = "VERDE";   prioridad = "BAJA"
        elif score >= 60: nivel = "AMARILLO"; prioridad = "MEDIA"
        elif score >= 40: nivel = "NARANJA";  prioridad = "ALTA"
        else:             nivel = "ROJO";     prioridad = "CRITICA"

        if exposicion >= 500000:   impacto_financiero = "CRITICO"
        elif exposicion >= 250000: impacto_financiero = "ALTO"
        elif exposicion >= 100000: impacto_financiero = "MEDIO"
        else:                      impacto_financiero = "BAJO"

        indice_colapso = round(min((100-score) + (demandas*5) + (rotacion_anual*0.5), 100), 2)
        riesgo_global  = round(min((100-score)*0.5 + min(exposicion/10000, 50), 100), 2)
        enterprise_survival_score = max(0, round(100 - (riesgo_global*0.6), 2))
        latency_ms = round((time.time()-started)*1000, 2)

        return {
            "engine": self.engine, "engine_status": "OK", "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id, "trace_id": trace_id,
            "categoria_empresa": categoria,
            "labor_score": score, "nivel": nivel, "prioridad": prioridad,
            "impacto_financiero": impacto_financiero,
            "indice_colapso_laboral": indice_colapso,
            "riesgo_global": riesgo_global,
            "enterprise_survival_score": enterprise_survival_score,
            "riesgos_detectados": len(riesgos),
            "exposicion_estimada_mxn": exposicion,
            "riesgos": riesgos, "recomendaciones": recomendaciones,
            "engine_latency_ms": latency_ms
        }
