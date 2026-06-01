# services/contractual_risk_engine.py -- MESAN Omega Contractual Risk Engine v4.3 Enterprise Production Ready
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("mesan.contractual")

RULESET_VERSION = "4.3.0"

# ============================================================
# CONSTANTES
# ============================================================
SEV_MEDIA   = "MEDIA"
SEV_ALTA    = "ALTA"
SEV_CRITICA = "CRITICA"

RISK_LEVELS = [(80,"VERDE","BAJA"),(60,"AMARILLO","MEDIA"),(40,"NARANJA","ALTA"),(0,"ROJO","CRITICA")]
EXPOSICION_CRITICA = 500000
EXPOSICION_ALTA    = 250000
EXPOSICION_MEDIA   = 100000

# ============================================================
# HELPERS
# ============================================================
def safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool): return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true","1","si","yes","y","on","verdadero"): return True
        if v in ("false","0","no","off","falso"):             return False
    return default

def safe_int(value: Any, default: int = 0) -> int:
    try:    return max(0, int(value))
    except (TypeError, ValueError): return default

def get_nivel(score: int) -> Tuple[str, str]:
    for minimo, nivel, prioridad in RISK_LEVELS:
        if score >= minimo: return nivel, prioridad
    return "ROJO", "CRITICA"

def get_impacto_financiero(exposicion: float) -> str:
    if exposicion >= EXPOSICION_CRITICA: return "CRITICO"
    if exposicion >= EXPOSICION_ALTA:   return "ALTO"
    if exposicion >= EXPOSICION_MEDIA:  return "MEDIO"
    return "BAJO"

def calcular_kpis(score: int, exposicion: float, litigios: int, vencidos: int, proveedores: int) -> Tuple[float, float, float]:
    indice  = round(min((100-score)+(litigios*10)+(vencidos*3)+(proveedores*2), 100), 2)
    riesgo  = round(min((100-score)*0.6+min(exposicion/10000, 40), 100), 2)
    survival= max(0, round(100-(riesgo*0.7), 2))
    return indice, riesgo, survival


# ============================================================
# ENGINE
# ============================================================
class ContractualRiskEngine:

    def __init__(self):
        self.version = "4.3"
        self.engine  = "MESAN_CONTRACTUAL_RISK"

    def _add_risk(self, riesgos: List[dict], recomendaciones: List[str],
                  riesgo: str, severidad: str, recomendacion: str, **extra) -> None:
        risk_data = {"riesgo": riesgo, "severidad": severidad}
        risk_data.update(extra)
        riesgos.append(risk_data)
        recomendaciones.append(recomendacion)

    def _audit(self, audit_trail: List[dict], rule_id: str, triggered: bool, tenant_id: str = "", trace_id: str = "") -> None:
        audit_trail.append({
            "rule_id":   rule_id,
            "triggered": triggered,
            "tenant_id": tenant_id,
            "trace_id":  trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def analizar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict): data = {}
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        contratos_vencidos       = safe_int(data.get("contratos_vencidos"))
        proveedores_sin_contrato = safe_int(data.get("proveedores_sin_contrato"))
        litigios_activos         = safe_int(data.get("litigios_activos"))

        score     = 100
        exposicion= 0.0
        riesgos:         List[dict] = []
        recomendaciones: List[str]  = []
        audit_trail:     List[dict] = []

        # CONTRACT_001
        triggered = not safe_bool(data.get("clausula_confidencialidad"))
        self._audit(audit_trail, "CONTRACT_001_CONFIDENTIALITY", triggered, tenant_id, trace_id)
        if triggered:
            score -= 15; exposicion += 50000
            self._add_risk(riesgos, recomendaciones, "CONFIDENCIALIDAD", SEV_MEDIA,
                "Agregar clausula de confidencialidad a todos los contratos.", impacto="FUGA_INFORMACION")

        # CONTRACT_002
        triggered = not safe_bool(data.get("clausula_no_competencia"))
        self._audit(audit_trail, "CONTRACT_002_NON_COMPETE", triggered, tenant_id, trace_id)
        if triggered:
            score -= 10; exposicion += 30000
            self._add_risk(riesgos, recomendaciones, "NO_COMPETENCIA", SEV_MEDIA,
                "Incluir clausula de no competencia.", impacto="RIESGO_COMERCIAL")

        # CONTRACT_003
        triggered = not safe_bool(data.get("clausula_rescision"))
        self._audit(audit_trail, "CONTRACT_003_TERMINATION", triggered, tenant_id, trace_id)
        if triggered:
            score -= 10; exposicion += 25000
            self._add_risk(riesgos, recomendaciones, "RESCISION", SEV_MEDIA,
                "Definir causales de rescision.", impacto="RIESGO_LEGAL")

        # CONTRACT_004
        triggered = safe_bool(data.get("penalizaciones_excesivas"))
        self._audit(audit_trail, "CONTRACT_004_PENALTIES", triggered, tenant_id, trace_id)
        if triggered:
            score -= 20; exposicion += 100000
            self._add_risk(riesgos, recomendaciones, "PENALIZACIONES", SEV_ALTA,
                "Renegociar clausulas de penalizacion.", impacto="RIESGO_FINANCIERO")

        # CONTRACT_005
        triggered = contratos_vencidos > 0
        self._audit(audit_trail, "CONTRACT_005_EXPIRED_CONTRACTS", triggered, tenant_id, trace_id)
        if triggered:
            score -= min(contratos_vencidos*5, 20); exposicion += contratos_vencidos*20000
            self._add_risk(riesgos, recomendaciones, "CONTRATOS_VENCIDOS", SEV_ALTA,
                "Renovar contratos vencidos.", detalle=f"{contratos_vencidos} contratos vencidos")

        # CONTRACT_006
        triggered = proveedores_sin_contrato > 0
        self._audit(audit_trail, "CONTRACT_006_SUPPLIERS", triggered, tenant_id, trace_id)
        if triggered:
            score -= min(proveedores_sin_contrato*5, 20); exposicion += proveedores_sin_contrato*15000
            self._add_risk(riesgos, recomendaciones, "PROVEEDORES_SIN_CONTRATO", SEV_MEDIA,
                "Formalizar contratos con proveedores.", detalle=f"{proveedores_sin_contrato} proveedores sin contrato")

        # CONTRACT_007
        triggered = litigios_activos > 0
        self._audit(audit_trail, "CONTRACT_007_LITIGATION", triggered, tenant_id, trace_id)
        if triggered:
            score -= min(litigios_activos*10, 30); exposicion += litigios_activos*150000
            self._add_risk(riesgos, recomendaciones, "LITIGIOS", SEV_CRITICA,
                "Atender litigios con asesor legal especializado.", detalle=f"{litigios_activos} litigios activos")

        # --------------------------------------------------
        # CALCULOS FINALES
        # --------------------------------------------------
        score = max(score, 0)
        recomendaciones = list(dict.fromkeys(recomendaciones))
        nivel, prioridad = get_nivel(score)
        impacto_financiero = get_impacto_financiero(exposicion)

        indice_colapso, riesgo_global, enterprise_survival_score = calcular_kpis(
            score, exposicion, litigios_activos, contratos_vencidos, proveedores_sin_contrato)

        critical_findings  = [r for r in riesgos if r.get("severidad") == SEV_CRITICA]
        critical_count     = len(critical_findings)
        confidence_score   = round(max(0, min(100, 100-(len(riesgos)*2)-(critical_count*5))), 2)
        ahorro_potencial   = round(exposicion*0.55, 2)
        inversion_recomendada = max(25000, round(exposicion*0.05, 2))
        roi_estimado       = round(min(ahorro_potencial/max(inversion_recomendada, 1), 100), 2)

        total_eventos = contratos_vencidos + proveedores_sin_contrato + litigios_activos
        risk_density_pct  = round(min((len(riesgos)/max(total_eventos, 1))*100, 100), 2)
        critical_ratio= round(critical_count/max(len(riesgos), 1), 4)

        contractual_health_score = max(0, min(100, round(
            score*0.5 + confidence_score*0.2 + enterprise_survival_score*0.3, 2)))

        # Sales priority — exposicion-first, war_room como calificador
        war_room_required = (
            indice_colapso >= 50
            or exposicion >= 300000
            or critical_count > 0
        )

        if exposicion >= 1000000:                          sales_priority = "A+"
        elif war_room_required and exposicion >= 300000:   sales_priority = "HOT"
        elif exposicion >= 500000:                         sales_priority = "A"
        elif exposicion >= 250000:                         sales_priority = "B"
        else:                                              sales_priority = "C"

        if riesgo_global >= 80:   semaforo = "ROJO";    intervencion = "INMEDIATA"
        elif riesgo_global >= 60: semaforo = "NARANJA";  intervencion = "30_DIAS"
        elif riesgo_global >= 40: semaforo = "AMARILLO"; intervencion = "90_DIAS"
        else:                     semaforo = "VERDE";    intervencion = "MONITOREO"

        if riesgo_global >= 80:   categoria_ejecutiva = "CRISIS_CONTRACTUAL"
        elif riesgo_global >= 60: categoria_ejecutiva = "RIESGO_ESTRATEGICO"
        elif riesgo_global >= 40: categoria_ejecutiva = "OBSERVACIONES"
        else:                     categoria_ejecutiva = "CONTROLADO"

        executive_summary = (
            f"Exposicion contractual estimada de ${exposicion:,.0f} MXN. "
            f"Indice de colapso {indice_colapso}. "
            f"Categoria ejecutiva: {categoria_ejecutiva}. "
            f"Intervencion recomendada: {intervencion}."
        )

        risk_matrix = {
            "legal":        min(100, len(riesgos)*10),
            "financial":    round(min(exposicion/5000, 100), 2),
            "operational":  min(100, int(indice_colapso)),
            "reputational": min(100, (critical_count*20)+(litigios_activos*10))
        }

        latency_ms = round((time.time()-started)*1000, 2)
        logger.info("[CONTRACTUAL] tenant=%s score=%s riesgos=%s exposicion=%s",
            tenant_id, score, len(riesgos), round(exposicion))

        return {
            "engine":                    self.engine,
            "engine_status":             "OK",
            "version":                   self.version,
            "ruleset_version":           RULESET_VERSION,
            "timestamp":                 datetime.now(timezone.utc).isoformat(),
            "tenant_id":                 tenant_id,
            "trace_id":                  trace_id,
            "contractual_score":         score,
            "nivel":                     nivel,
            "prioridad":                 prioridad,
            "riesgo_global":             riesgo_global,
            "enterprise_survival_score": enterprise_survival_score,
            "contractual_health_score":  contractual_health_score,
            "impacto_financiero":        impacto_financiero,
            "indice_colapso_contractual":indice_colapso,
            "categoria_ejecutiva":       categoria_ejecutiva,
            "war_room_required":         war_room_required,
            "semaforo":                  semaforo,
            "intervencion_recomendada":  intervencion,
            "confidence_score":          confidence_score,
            "ahorro_potencial_mxn":      ahorro_potencial,
            "inversion_recomendada_mxn": inversion_recomendada,
            "roi_estimado":              roi_estimado,
            "sales_priority":            sales_priority,
            "critical_findings":         critical_findings,
            "critical_findings_count":   critical_count,
            "executive_summary":         executive_summary,
            "risk_matrix":               risk_matrix,
            "risk_density_pct":          risk_density_pct,
            "critical_ratio":            critical_ratio,
            "audit_trail":               audit_trail,
            "riesgos_detectados":        len(riesgos),
            "exposicion_estimada_mxn":   exposicion,
            "riesgos":                   riesgos,
            "recomendaciones":           recomendaciones,
            "engine_latency_ms":         latency_ms,
            "input_validation_summary": {
                "contratos_vencidos":       contratos_vencidos,
                "proveedores_sin_contrato": proveedores_sin_contrato,
                "litigios_activos":         litigios_activos,
                "sanitized":                True
            },
            "audit_source": {
                "engine":       self.engine,
                "version":      self.version,
                "ruleset":      RULESET_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
