# services/contractual_risk_engine.py -- MESAN Omega Contractual Risk Engine v4.0
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.contractual")


def safe_bool(value, default=False):
    if isinstance(value, bool): return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true","1","si","yes","y","on","verdadero"): return True
        if v in ("false","0","no","off","falso"):             return False
    return default

def safe_int(value, default=0):
    try: return int(value)
    except: return default


class ContractualRiskEngine:

    def __init__(self):
        self.version = "4.0"
        self.engine  = "MESAN_CONTRACTUAL_RISK"

    def analizar(self, data: dict) -> dict:
        started = time.time()
        if not isinstance(data, dict): data = {}

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        score = 100; exposicion = 0; riesgos = []; recomendaciones = []

        if not safe_bool(data.get("clausula_confidencialidad")):
            score -= 15; exposicion += 50000
            riesgos.append({"riesgo":"CONFIDENCIALIDAD","severidad":"MEDIA","impacto":"FUGA_INFORMACION"})
            recomendaciones.append("Agregar clausula de confidencialidad a todos los contratos.")

        if not safe_bool(data.get("clausula_no_competencia")):
            score -= 10; exposicion += 30000
            riesgos.append({"riesgo":"NO_COMPETENCIA","severidad":"MEDIA","impacto":"RIESGO_COMERCIAL"})
            recomendaciones.append("Incluir clausula de no competencia.")

        if not safe_bool(data.get("clausula_rescision")):
            score -= 10; exposicion += 25000
            riesgos.append({"riesgo":"RESCISION","severidad":"MEDIA","impacto":"RIESGO_LEGAL"})
            recomendaciones.append("Definir causales de rescision.")

        if safe_bool(data.get("penalizaciones_excesivas")):
            score -= 20; exposicion += 100000
            riesgos.append({"riesgo":"PENALIZACIONES","severidad":"ALTA","impacto":"RIESGO_FINANCIERO"})
            recomendaciones.append("Renegociar clausulas de penalizacion.")

        contratos_vencidos = safe_int(data.get("contratos_vencidos"))
        if contratos_vencidos > 0:
            score -= min(contratos_vencidos*5, 20); exposicion += contratos_vencidos*20000
            riesgos.append({"riesgo":"CONTRATOS_VENCIDOS","severidad":"ALTA","detalle":f"{contratos_vencidos} contratos vencidos"})
            recomendaciones.append("Renovar contratos vencidos.")

        proveedores_sin_contrato = safe_int(data.get("proveedores_sin_contrato"))
        if proveedores_sin_contrato > 0:
            score -= min(proveedores_sin_contrato*5, 20); exposicion += proveedores_sin_contrato*15000
            riesgos.append({"riesgo":"PROVEEDORES_SIN_CONTRATO","severidad":"MEDIA","detalle":f"{proveedores_sin_contrato} proveedores sin contrato"})
            recomendaciones.append("Formalizar contratos con proveedores.")

        litigios_activos = safe_int(data.get("litigios_activos"))
        if litigios_activos > 0:
            score -= min(litigios_activos*10, 30); exposicion += litigios_activos*150000
            riesgos.append({"riesgo":"LITIGIOS","severidad":"CRITICA","detalle":f"{litigios_activos} litigios activos"})
            recomendaciones.append("Atender litigios con asesor legal especializado.")

        score = max(score, 0)

        if score >= 80:   nivel = "VERDE";   prioridad = "BAJA"
        elif score >= 60: nivel = "AMARILLO"; prioridad = "MEDIA"
        elif score >= 40: nivel = "NARANJA";  prioridad = "ALTA"
        else:             nivel = "ROJO";     prioridad = "CRITICA"

        if exposicion >= 500000:   impacto_financiero = "CRITICO"
        elif exposicion >= 250000: impacto_financiero = "ALTO"
        elif exposicion >= 100000: impacto_financiero = "MEDIO"
        else:                      impacto_financiero = "BAJO"

        indice_colapso = round(min((100-score)+(litigios_activos*10)+(contratos_vencidos*3)+(proveedores_sin_contrato*2), 100), 2)
        riesgo_global  = round(min((100-score)*0.6 + min(exposicion/10000, 40), 100), 2)
        enterprise_survival_score = max(0, round(100-(riesgo_global*0.7), 2))

        critical_findings  = [r for r in riesgos if r.get("severidad") == "CRITICA"]
        critical_count     = len(critical_findings)
        confidence_score   = round(max(40, 100-(len(riesgos)*2)-(critical_count*5)), 2)
        audit_readiness    = round(max(0, min(100, score-(critical_count*10))), 2)
        madurez_contractual = round(score*0.92, 2)

        ahorro_potencial       = round(exposicion*0.55, 2)
        inversion_recomendada  = max(25000, round(exposicion*0.05, 2))
        roi_estimado           = round(ahorro_potencial/max(inversion_recomendada, 1), 2)

        if enterprise_survival_score >= 85:   benchmark = "TOP_10%"
        elif enterprise_survival_score >= 70: benchmark = "TOP_25%"
        elif enterprise_survival_score >= 50: benchmark = "PROMEDIO"
        else:                                 benchmark = "RIESGO_ELEVADO"

        if riesgo_global >= 80:   categoria_ejecutiva = "CRISIS_CONTRACTUAL"
        elif riesgo_global >= 60: categoria_ejecutiva = "RIESGO_ESTRATEGICO"
        elif riesgo_global >= 40: categoria_ejecutiva = "OBSERVACIONES"
        else:                     categoria_ejecutiva = "CONTROLADO"

        war_room_required = indice_colapso >= 50 or exposicion >= 300000 or critical_count > 0

        acciones_prioritarias = [f"Atender riesgo critico: {r['riesgo']}" for r in critical_findings]
        acciones_prioritarias.extend(recomendaciones[:5])

        risk_matrix = {
            "legal":        min(100, len(riesgos)*10),
            "financial":    min(100, int(exposicion/10000)),
            "operational":  min(100, int(indice_colapso)),
            "reputational": min(100, critical_count*25)
        }

        executive_summary = (
            f"Exposicion contractual estimada de ${exposicion:,.0f} MXN. "
            f"Indice de colapso contractual {indice_colapso}. "
            f"Categoria ejecutiva: {categoria_ejecutiva}."
        )

        latency_ms = round((time.time()-started)*1000, 2)
        logger.info(f"[CONTRACTUAL] tenant={tenant_id} score={score} riesgos={len(riesgos)} exposicion={exposicion}")

        return {
            "engine": self.engine, "engine_status": "OK", "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id, "trace_id": trace_id,
            "contractual_score": score, "nivel": nivel, "prioridad": prioridad,
            "riesgo_global": riesgo_global,
            "enterprise_survival_score": enterprise_survival_score,
            "impacto_financiero": impacto_financiero,
            "indice_colapso_contractual": indice_colapso,
            "war_room_required": war_room_required,
            "confidence_score": confidence_score,
            "audit_readiness": audit_readiness,
            "madurez_contractual": madurez_contractual,
            "benchmark_empresarial": benchmark,
            "categoria_ejecutiva": categoria_ejecutiva,
            "ahorro_potencial_mxn": ahorro_potencial,
            "inversion_recomendada_mxn": inversion_recomendada,
            "roi_estimado": roi_estimado,
            "critical_findings": critical_findings,
            "critical_findings_count": critical_count,
            "acciones_prioritarias": acciones_prioritarias,
            "executive_summary": executive_summary,
            "risk_matrix": risk_matrix,
            "riesgos_detectados": len(riesgos),
            "exposicion_estimada_mxn": exposicion,
            "riesgos": riesgos, "recomendaciones": recomendaciones,
            "engine_latency_ms": latency_ms,
            "audit_source": "MESAN_CONTRACTUAL_ENGINE_V4"
        }
