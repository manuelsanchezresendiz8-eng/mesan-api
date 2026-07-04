# services/labor_shield_engine.py -- MESAN Omega Labor Shield Engine v3.1 Enterprise Ready
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("mesan.labor")

RULESET_VERSION = "3.1.0"

# ============================================================
# CONSTANTES
# ============================================================
COMPANY_CATEGORIES = [(10,"MICRO"),(50,"PYME"),(250,"MEDIANA")]
RISK_LEVELS        = [(80,"VERDE","BAJA"),(60,"AMARILLO","MEDIA"),(40,"NARANJA","ALTA"),(0,"ROJO","CRITICA")]
IMSS_RATIO_CRITICO = 0.30
IMSS_RATIO_ALTO    = 0.10
ROTACION_UMBRAL    = 30.0
EXPOSICION_CRITICA = 500000
EXPOSICION_ALTA    = 250000
EXPOSICION_MEDIA   = 100000

# ============================================================
# HELPERS
# ============================================================
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
        if v in ("true","1","si","yes","y","on","verdadero"): return True
        if v in ("false","0","no","off","falso"):             return False
    return default

def get_categoria(empleados: int) -> str:
    for limite, cat in COMPANY_CATEGORIES:
        if empleados <= limite: return cat
    return "CORPORATIVO"

def get_nivel(score: int) -> Tuple[str, str]:
    for minimo, nivel, prioridad in RISK_LEVELS:
        if score >= minimo: return nivel, prioridad
    return "ROJO", "CRITICA"

def get_impacto_financiero(exposicion: float) -> str:
    if exposicion >= EXPOSICION_CRITICA: return "CRITICO"
    if exposicion >= EXPOSICION_ALTA:   return "ALTO"
    if exposicion >= EXPOSICION_MEDIA:  return "MEDIO"
    return "BAJO"


# ============================================================
# ENGINE
# ============================================================
class LaborShieldEngine:

    def __init__(self):
        self.version = "3.1"
        self.engine  = "MESAN_LABOR_SHIELD"

    def _agregar_riesgo(
        self,
        riesgos: List[dict],
        recomendaciones: List[str],
        riesgo: str,
        severidad: str,
        detalle: str,
        recomendacion: str
    ) -> None:
        riesgos.append({"riesgo": riesgo, "severidad": severidad, "detalle": detalle})
        recomendaciones.append(recomendacion)

    def _audit(self, audit_trail: List[dict], rule_id: str, triggered: bool) -> None:
        audit_trail.append({
            "rule_id":   rule_id,
            "triggered": triggered,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def analizar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        empleados       = safe_int(data.get("empleados"))
        sin_imss        = safe_int(data.get("trabajadores_sin_imss"))
        demandas        = safe_int(data.get("demandas_laborales"))
        rotacion_anual  = min(safe_float(data.get("rotacion_anual")), 100.0)
        repse_vigente   = safe_bool(data.get("repse_vigente",   True), True)
        contratos_ok    = safe_bool(data.get("contratos_individuales", True), True)
        subcontratacion = safe_bool(data.get("subcontratacion_activa", False), False)
        jornadas_ok     = safe_bool(data.get("jornadas_documentadas", True), True)

        categoria = get_categoria(empleados)
        score     = 100
        exposicion= 0.0
        riesgos:         List[dict] = []
        recomendaciones: List[str]  = []
        audit_trail:     List[dict] = []

        # LABOR_001 — IMSS
        if empleados > 0:
            ratio    = sin_imss / empleados
            triggered = ratio > IMSS_RATIO_ALTO
            self._audit(audit_trail, "LABOR_001_IMSS", triggered)
            if triggered:
                penalizacion = 25 if ratio > IMSS_RATIO_CRITICO else 15
                score      -= penalizacion
                exposicion += sin_imss * 15000
                self._agregar_riesgo(riesgos, recomendaciones, "IMSS", "CRITICA",
                    f"{sin_imss} trabajadores sin IMSS",
                    "Regularizar afiliacion IMSS de toda la plantilla")
        else:
            self._audit(audit_trail, "LABOR_001_IMSS", False)

        # LABOR_002 — DEMANDAS
        triggered = demandas > 0
        self._audit(audit_trail, "LABOR_002_DEMANDAS", triggered)
        if triggered:
            score      -= min(demandas * 10, 30)
            exposicion += demandas * 80000
            self._agregar_riesgo(riesgos, recomendaciones, "DEMANDAS_LABORALES", "ALTA",
                f"{demandas} demandas activas",
                "Atender demandas laborales activas y revisar causas raiz")

        # LABOR_003 — ROTACION
        triggered = rotacion_anual > ROTACION_UMBRAL
        self._audit(audit_trail, "LABOR_003_ROTACION", triggered)
        if triggered:
            score      -= 15
            exposicion += 50000
            self._agregar_riesgo(riesgos, recomendaciones, "ROTACION", "MEDIA",
                f"Rotacion {rotacion_anual:.1f}% anual",
                "Implementar programa de retencion de talento")

        # LABOR_004 - REPSE (Acuerdo DOF 9 junio 2026)
        # Regimen simplificado: <= 10 trabajadores
        # Docs: Formulario STPS-086-002 + RFC. Resolucion 5 dias habiles.
        # Regimen estandar: > 10 trabajadores
        # Docs: STPS-086-002 + Poder Notarial + Nomina CFDI + SUA. 15 dias.
        num_trabajadores = int(data.get("trabajadores", data.get("empleados", 0)))
        repse_simplificado = num_trabajadores <= 10
        triggered = not repse_vigente
        self._audit(audit_trail, "LABOR_004_REPSE", triggered)
        if triggered:
            if repse_simplificado:
                score      -= 10
                exposicion += 50000
                self._agregar_riesgo(riesgos, recomendaciones, "REPSE", "MEDIA",
                    "REPSE suspendido - regimen simplificado aplicable (DOF 9 jun 2026)",
                    "Tramitar REPSE simplificado: STPS-086-002 + RFC. Resolucion 5 dias habiles")
            else:
                score      -= 25
                exposicion += 200000
                self._agregar_riesgo(riesgos, recomendaciones, "REPSE", "CRITICA",
                    "REPSE suspendido - regimen estandar",
                    "Renovar REPSE: STPS-086-002 + Poder Notarial + Nomina CFDI + SUA. 15 dias")
        # LABOR_005 — CONTRATOS
        triggered = not contratos_ok
        self._audit(audit_trail, "LABOR_005_CONTRATOS", triggered)
        if triggered:
            score      -= 15
            exposicion += 40000
            self._agregar_riesgo(riesgos, recomendaciones, "CONTRATOS", "MEDIA",
                "Contratos individuales incompletos",
                "Regularizar contratos individuales de trabajo")

        # LABOR_006 — SUBCONTRATACION
        triggered = subcontratacion and not repse_vigente
        self._audit(audit_trail, "LABOR_006_SUBCONTRATACION", triggered)
        if triggered:
            score      -= 20
            exposicion += 150000
            self._agregar_riesgo(riesgos, recomendaciones, "SUBCONTRATACION", "CRITICA",
                "Subcontratacion activa sin REPSE",
                "Suspender subcontratacion hasta regularizar REPSE")

        # LABOR_007 — JORNADAS
        triggered = not jornadas_ok
        self._audit(audit_trail, "LABOR_007_JORNADAS", triggered)
        if triggered:
            score      -= 10
            exposicion += 20000
            self._agregar_riesgo(riesgos, recomendaciones, "JORNADAS", "MEDIA",
                "Jornadas no documentadas",
                "Documentar jornadas y horas extra conforme a LFT")

        # --------------------------------------------------
        # CALCULOS FINALES
        # --------------------------------------------------
        score    = max(score, 0)
        nivel, prioridad       = get_nivel(score)
        impacto_financiero     = get_impacto_financiero(exposicion)
        critical_findings      = [r for r in riesgos if r.get("severidad") == "CRITICA"]
        indice_colapso         = round(min((100-score)+(demandas*5)+(rotacion_anual*0.5), 100), 2)
        riesgo_global          = round(min((100-score)*0.5+min(exposicion/10000, 50), 100), 2)
        enterprise_survival    = max(0, round(100-(riesgo_global*0.6), 2))
        war_room_required      = score < 50 or len(critical_findings) > 0 or exposicion >= 500000
        risk_density           = round(len(riesgos)/max(empleados, 1), 4)
        critical_ratio         = round(len(critical_findings)/max(len(riesgos), 1), 4)
        latency_ms             = round((time.time()-started)*1000, 2)

        logger.info("[LABOR_SHIELD] tenant=%s score=%s riesgos=%s exposicion=%s nivel=%s",
            tenant_id, score, len(riesgos), round(exposicion), nivel)

        return {
            "engine":                    self.engine,
            "engine_status":             "OK",
            "version":                   self.version,
            "ruleset_version":           RULESET_VERSION,
            "timestamp":                 datetime.now(timezone.utc).isoformat(),
            "tenant_id":                 tenant_id,
            "trace_id":                  trace_id,
            "categoria_empresa":         categoria,
            "labor_score":               score,
            "nivel":                     nivel,
            "prioridad":                 prioridad,
            "impacto_financiero":        impacto_financiero,
            "indice_colapso_laboral":    indice_colapso,
            "riesgo_global":             riesgo_global,
            "enterprise_survival_score": enterprise_survival,
            "war_room_required":         war_room_required,
            "critical_findings":         critical_findings,
            "riesgos_detectados":        len(riesgos),
            "exposicion_estimada_mxn":   exposicion,
            "risk_density":              risk_density,
            "critical_ratio":            critical_ratio,
            "audit_trail":               audit_trail,
            "riesgos":                   riesgos,
            "recomendaciones":           recomendaciones,
            "engine_latency_ms":         latency_ms
        }
