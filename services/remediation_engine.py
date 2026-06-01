# services/remediation_engine.py -- MESAN Omega Remediation Engine v3.3 Enterprise Production Ready
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

logger = logging.getLogger("mesan.remediation")

RULESET_VERSION  = "3.3.0"
VALID_PRIORITIES = {"A+", "HOT", "A", "B", "C"}
VALID_NIVELES    = {"CRITICO", "EXTREMO", "ALTO", "MEDIO", "BAJO"}
NORMALIZE_NIVEL  = {"CRITICA": "CRITICO", "MEDIA": "MEDIO"}

URGENCIA_MAP = {
    "CRITICO": ("INMEDIATA", 70),
    "EXTREMO": ("INMEDIATA", 70),
    "ALTO":    ("7_DIAS",    80),
    "MEDIO":   ("30_DIAS",   90),
}
URGENCIA_DEFAULT = ("90_DIAS", 95)

def safe_int(value: Any, default: int = 0) -> int:
    try:    return max(0, int(value))
    except (TypeError, ValueError): return default

def safe_float(value: Any, default: float = 0.0) -> float:
    try:    return max(0.0, float(value))
    except (TypeError, ValueError): return default

def safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool): return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true","1","si","yes","on"):  return True
        if v in ("false","0","no","off"):       return False
    return default


class RemediationEngine:

    def __init__(self):
        self.version = "3.3"
        self.engine  = "MESAN_REMEDIATION"

    def generar_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        nivel = str(data.get("nivel", "MEDIO")).upper()
        nivel = NORMALIZE_NIVEL.get(nivel, nivel)
        if nivel not in VALID_NIVELES: nivel = "MEDIO"

        alertas = data.get("alertas") or []
        if not isinstance(alertas, list): alertas = [str(alertas)]

        score      = max(0, min(safe_int(data.get("score", data.get("contractual_score", 50))), 100))
        exposicion = safe_float(data.get("exposicion_estimada_mxn", 0))

        critical_findings_count = safe_int(data.get("critical_findings_count"))
        war_room_flag           = safe_bool(data.get("war_room_required", False))
        sales_priority_input    = str(data.get("sales_priority", "C")).upper()
        if sales_priority_input not in VALID_PRIORITIES: sales_priority_input = "C"

        acciones_inmediatas: List[str] = []
        acciones_30_dias:    List[str] = []
        acciones_60_dias:    List[str] = []
        acciones_90_dias:    List[str] = []

        if any("SAT" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Solicitar opinion de cumplimiento SAT actualizada")
            acciones_30_dias.append("Regularizar declaraciones fiscales pendientes")
            acciones_60_dias.append("Implementar estrategia fiscal preventiva")

        if any("IMSS" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Regularizar afiliaciones IMSS")
            acciones_30_dias.append("Auditar nomina vs plantilla IMSS")
            acciones_60_dias.append("Implementar controles permanentes IMSS")

        if any("REPSE" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Iniciar renovacion REPSE")
            acciones_30_dias.append("Revisar contratos de subcontratacion")

        if any("LIQUIDEZ" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Contencion inmediata de gasto")
            acciones_30_dias.append("Renegociar pasivos financieros")
            acciones_60_dias.append("Plan de recuperacion de cartera")

        if any("BANCARIO" in str(a).upper() for a in alertas):
            acciones_inmediatas.append("Activar protocolo de supervivencia financiera")

        if nivel in ("CRITICO", "EXTREMO"):
            acciones_inmediatas.extend([
                "Activar War Room Ejecutivo",
                "Congelar gastos no esenciales",
                "Comite diario de riesgos"
            ])
            acciones_30_dias.append("Reestructura financiera de emergencia")
            acciones_60_dias.append("Negociacion con acreedores estrategicos")
            acciones_90_dias.append("Plan de continuidad operativa")
        elif nivel == "ALTO":
            acciones_30_dias.append("Reducir burn rate operativo")
            acciones_60_dias.append("Blindaje fiscal y laboral preventivo")
            acciones_90_dias.append("Optimizacion de capital de trabajo")
        else:
            acciones_60_dias.append("Monitoreo preventivo mensual")
            acciones_90_dias.append("Auditoria interna de cumplimiento")

        if critical_findings_count > 0:
            acciones_inmediatas.append(f"Atender {critical_findings_count} hallazgo(s) critico(s) detectados")

        if war_room_flag and "Activar War Room Ejecutivo" not in acciones_inmediatas:
            acciones_inmediatas.append("Activar War Room Ejecutivo")

        acciones_inmediatas = list(dict.fromkeys(acciones_inmediatas))
        acciones_30_dias    = list(dict.fromkeys(acciones_30_dias))
        acciones_60_dias    = list(dict.fromkeys(acciones_60_dias))
        acciones_90_dias    = list(dict.fromkeys(acciones_90_dias))

        # KPIs
        costo_estimado   = max(25000, round(exposicion*0.05, 2))
        ahorro_potencial = round(exposicion*0.70, 2)
        roi_estimado_pct = round(max(-100, min(((ahorro_potencial-costo_estimado)/max(costo_estimado, 1))*100, 1000)), 2)

        urgencia, probabilidad_exito = URGENCIA_MAP.get(nivel, URGENCIA_DEFAULT)

        war_room_required = (
            nivel in ("CRITICO", "EXTREMO")
            or exposicion >= 500000
            or war_room_flag
        )

        survival_score_post = round(max(0, min(100, score+((100-score)*0.20))), 2)
        if war_room_required:
            survival_score_post = round(max(0, survival_score_post-5), 2)

        # Forecast dependiente de severidad
        severity_factor = min(exposicion/5000000, 1)
        improvement_30 = max(0, (100-score)*(0.10-severity_factor*0.03))
        improvement_60 = max(0, (100-score)*(0.18-severity_factor*0.04))
        improvement_90 = max(0, (100-score)*(0.25-severity_factor*0.05))
        recovery_forecast = {
            "30_dias": round(min(100, score+improvement_30), 2),
            "60_dias": round(min(100, score+improvement_60), 2),
            "90_dias": round(min(100, score+improvement_90), 2)
        }

        if survival_score_post >= 85:   semaforo = "VERDE"
        elif survival_score_post >= 70: semaforo = "AMARILLO"
        elif survival_score_post >= 50: semaforo = "NARANJA"
        else:                           semaforo = "ROJO"

        # Sales priority corregida
        if exposicion >= 2000000:             sales_priority = "A+"
        elif critical_findings_count > 0:     sales_priority = "HOT"
        elif exposicion >= 1000000:           sales_priority = "A"
        elif exposicion >= 500000:            sales_priority = "B"
        else:                                 sales_priority = sales_priority_input

        total_acciones = (
            len(acciones_inmediatas)+len(acciones_30_dias)+
            len(acciones_60_dias)+len(acciones_90_dias)
        )

        executive_summary = (
            f"Se detecto una exposicion estimada de ${exposicion:,.0f} MXN. "
            f"El plan contempla {total_acciones} acciones de remediacion, "
            f"{len(acciones_inmediatas)} de ejecucion inmediata, "
            f"con un ahorro potencial estimado de ${ahorro_potencial:,.0f} MXN."
        )

        execution_complexity = (
            "ALTA"  if total_acciones >= 12 else
            "MEDIA" if total_acciones >= 6  else
            "BAJA"
        )

        if total_acciones >= 12:   operational_priority = "CRITICA"
        elif total_acciones >= 8:  operational_priority = "ALTA"
        elif total_acciones >= 4:  operational_priority = "MEDIA"
        else:                      operational_priority = "BAJA"

        execution_risk_score = round(min(
            (total_acciones*4)+(critical_findings_count*10)+min(exposicion/100000, 30), 100), 2)
        ceo_attention_required = war_room_required or exposicion >= 1000000 or critical_findings_count > 0

        if exposicion >= 2000000:   service_opportunity = "ENTERPRISE"
        elif exposicion >= 1000000: service_opportunity = "PREMIUM"
        elif exposicion >= 500000:  service_opportunity = "PRO"
        else:                       service_opportunity = "STANDARD"

        timeline = [
            {"fase":"0-7 dias", "objetivo":"Contencion"},
            {"fase":"30 dias",  "objetivo":"Estabilizacion"},
            {"fase":"60 dias",  "objetivo":"Recuperacion"},
            {"fase":"90 dias",  "objetivo":"Fortalecimiento"}
        ]

        sla_map   = {"INMEDIATA":24,"7_DIAS":168,"30_DIAS":720,"90_DIAS":2160}
        sla_hours = sla_map.get(urgencia, 720)
        target_resolution_date = (
            datetime.now(timezone.utc)+timedelta(hours=sla_hours)
        ).isoformat()

        cost_benefit = {
            "costo_intervencion_mxn": costo_estimado,
            "ahorro_potencial_mxn":   ahorro_potencial,
            "roi_estimado_pct":       roi_estimado_pct,
            "probabilidad_exito_pct": probabilidad_exito
        }

        latency_ms = round((time.time()-started)*1000, 2)
        logger.info("[REMEDIATION] tenant=%s nivel=%s acciones=%s exposicion=%s",
            tenant_id, nivel, total_acciones, round(exposicion))

        return {
            "engine":                        self.engine,
            "engine_status":                 "OK",
            "version":                       self.version,
            "ruleset_version":               RULESET_VERSION,
            "timestamp":                     datetime.now(timezone.utc).isoformat(),
            "tenant_id":                     tenant_id,
            "trace_id":                      trace_id,
            "nivel_riesgo":                  nivel,
            "urgencia":                      urgencia,
            "sla_horas":                     sla_hours,
            "target_resolution_date":        target_resolution_date,
            "war_room_required":             war_room_required,
            "semaforo":                      semaforo,
            "sales_priority":                sales_priority,
            "enterprise_survival_score_post":survival_score_post,
            "recovery_forecast":             recovery_forecast,
            "operational_priority":          operational_priority,
            "execution_complexity":          execution_complexity,
            "timeline_ejecutivo":            timeline,
            "cost_benefit":                  cost_benefit,
            "executive_summary":             executive_summary,
            "omega_core": {
                "ceo_attention_required": ceo_attention_required,
                "execution_risk_score":   execution_risk_score,
                "service_opportunity":    service_opportunity
            },
            "plan_remediacion": {
                "acciones_inmediatas": acciones_inmediatas,
                "acciones_30_dias":    acciones_30_dias,
                "acciones_60_dias":    acciones_60_dias,
                "acciones_90_dias":    acciones_90_dias
            },
            "total_acciones":                total_acciones,
            "engine_latency_ms":             latency_ms,
            "audit_source": {
                "engine":       self.engine,
                "version":      self.version,
                "ruleset":      RULESET_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "tenant":       tenant_id,
                "trace":        trace_id
            }
        }
