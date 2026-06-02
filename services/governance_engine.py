# services/governance_engine.py -- MESAN Omega Governance Engine v3.1
import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.governance")

def safe_float(value, default=0.0):
    try:    return float(value)
    except: return default

def normalize_score(score):
    try:    score = float(score)
    except: score = 0.0
    if score != score: score = 0.0
    return max(0, min(100, score))

def classify(score: float):
    if score >= 90: return "WORLD_CLASS", "VERDE"
    elif score >= 80: return "BLINDADO",   "VERDE"
    elif score >= 70: return "CONTROLADO", "AMARILLO"
    elif score >= 50: return "VULNERABLE", "NARANJA"
    return "CRITICO", "ROJO"

def compute_sales_priority(x: float):
    if x >= 2_000_000: return "A+"
    if x >= 1_000_000: return "A"
    if x >= 500_000:   return "B"
    return "C"

def compute_benchmark(score: float):
    if score >= 90: return "TOP_5%"
    if score >= 85: return "TOP_10%"
    if score >= 75: return "TOP_25%"
    if score >= 60: return "PROMEDIO"
    return "RIESGO_ELEVADO"


class GovernanceEngine:

    def __init__(self):
        self.version = "3.1"
        self.engine  = "MESAN_GOVERNANCE"

    def calcular(self, data: dict) -> dict:
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        scores = {
            "fiscal":      normalize_score(data.get("score_fiscal",      100)),
            "compliance":  normalize_score(data.get("score_compliance",  100)),
            "laboral":     normalize_score(data.get("score_laboral",     100)),
            "contractual": normalize_score(data.get("score_contractual", 100)),
            "financiero":  normalize_score(data.get("score_financiero",  100)),
        }
        weights = {"fiscal":0.30,"compliance":0.20,"laboral":0.20,"contractual":0.15,"financiero":0.15}

        governance_score = normalize_score(sum(scores[k]*weights.get(k,0) for k in scores))
        categoria, nivel = classify(governance_score)

        RISK_THRESHOLD = 70
        risk_breakdown = {}
        dimensiones_riesgo = []

        for k, v in scores.items():
            impact   = round((100-v)*weights[k], 2)
            risk_gap = round(max(0, RISK_THRESHOLD - v), 2)
            risk_breakdown[k] = {
                "score": v, "weight": weights[k], "impact": impact,
                "status": "RISK" if v < RISK_THRESHOLD else "OK",
                "risk_gap": risk_gap
            }
            if v < RISK_THRESHOLD:
                dimensiones_riesgo.append(k.upper())

        TOTAL_DIMENSIONS   = len(scores)
        risk_concentration = round((len(dimensiones_riesgo)/TOTAL_DIMENSIONS)*100, 2)
        exposicion_total   = max(0, safe_float(data.get("exposicion_total", 0)))
        exposure_factor    = min(exposicion_total/100000, 25)

        governance_risk_index     = round(((100-governance_score)*0.60)+exposure_factor+(risk_concentration*0.15), 2)
        enterprise_survival_score = round(max(0, 100-(governance_risk_index*0.70)), 2)
        confidence_score          = round(max(40, 100-(len(dimensiones_riesgo)*7)-(risk_concentration*0.10)), 2)

        if (governance_score < 50 or len(dimensiones_riesgo) >= 3 or exposicion_total >= 1_000_000):
            event = "WAR_ROOM"
        elif governance_risk_index >= 80: event = "CRITICAL"
        elif governance_risk_index >= 60: event = "WARNING"
        else:                             event = "OK"

        war_room_required = event == "WAR_ROOM"
        war_room_score    = round((governance_risk_index*0.5)+(risk_concentration*0.3)+((100-confidence_score)*0.2), 2)

        semaforo, intervencion = (
            ("ROJO",     "INMEDIATA") if governance_risk_index >= 80 else
            ("NARANJA",  "30_DIAS")   if governance_risk_index >= 60 else
            ("AMARILLO", "90_DIAS")   if governance_risk_index >= 40 else
            ("VERDE",    "MONITOREO")
        )

        enterprise_health_index = round((governance_score*0.40)+(enterprise_survival_score*0.40)+(confidence_score*0.20), 2)
        sales_priority        = compute_sales_priority(exposicion_total)
        benchmark_empresarial = compute_benchmark(governance_score)

        executive_summary = (
            f"Governance Score {governance_score}/100. Categoria {categoria}. "
            f"Evento {event}. Riesgos activos {len(dimensiones_riesgo)}. Intervencion {intervencion}."
        )

        recommended_actions = []
        if "FISCAL"      in dimensiones_riesgo: recommended_actions.append({"priority":"HIGH",   "area":"FISCAL",      "action":"Revisar cumplimiento SAT y contingencias fiscales"})
        if "COMPLIANCE"  in dimensiones_riesgo: recommended_actions.append({"priority":"HIGH",   "area":"COMPLIANCE",  "action":"Actualizar matriz de cumplimiento normativo"})
        if "LABORAL"     in dimensiones_riesgo: recommended_actions.append({"priority":"MEDIUM", "area":"LABORAL",     "action":"Auditar expedientes laborales y contratos"})
        if "CONTRACTUAL" in dimensiones_riesgo: recommended_actions.append({"priority":"MEDIUM", "area":"CONTRACTUAL", "action":"Revisar clausulas criticas y vencimientos"})
        if "FINANCIERO"  in dimensiones_riesgo: recommended_actions.append({"priority":"HIGH",   "area":"FINANCIERO",  "action":"Evaluar exposicion financiera y liquidez"})

        executive_insights = []
        if governance_score >= 90:       executive_insights.append("La organizacion opera con estandares de gobernanza de clase mundial.")
        if governance_risk_index >= 60:  executive_insights.append("Existe concentracion relevante de riesgo que requiere intervencion.")
        if war_room_required:            executive_insights.append("Se recomienda activar comite de gestion de crisis.")
        if len(dimensiones_riesgo) == 0: executive_insights.append("Todas las dimensiones de gobernanza estan dentro de parametros aceptables.")

        score_anterior = normalize_score(data.get("score_mes_anterior", 0))
        if score_anterior > 0:
            delta = round(governance_score - score_anterior, 2)
            trend = "MEJORANDO" if delta > 0 else "DETERIORANDO" if delta < 0 else "ESTABLE"
        else:
            delta = None
            trend = "SIN_HISTORICO"

        latency_ms = round((time.time()-started)*1000, 2)
        logger.info("[GOVERNANCE] tenant=%s score=%.2f risk=%.2f event=%s", tenant_id, governance_score, governance_risk_index, event)

        return {
            "engine": self.engine, "version": self.version, "status": "OK",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id, "trace_id": trace_id,
            "scores": scores, "weights": weights,
            "risk_breakdown": risk_breakdown,
            "benchmark_empresarial": benchmark_empresarial,
            "governance_score": governance_score,
            "enterprise_governance_score": governance_score,
            "governance_status": (
                "BEST_IN_CLASS" if governance_score >= 90 else
                "HEALTHY"       if governance_score >= 80 else
                "STABLE"        if governance_score >= 70 else
                "AT_RISK"       if governance_score >= 50 else
                "CRITICAL"
            ),
            "governance_maturity": (
                "WORLD_CLASS" if governance_score >= 90 else
                "ADVANCED"    if governance_score >= 80 else
                "CONTROLLED"  if governance_score >= 70 else
                "REACTIVE"    if governance_score >= 50 else
                "FRAGILE"
            ),
            "critical_dimensions": dimensiones_riesgo,
            "governance_risk_index": governance_risk_index,
            "enterprise_survival_score": enterprise_survival_score,
            "enterprise_health_index": enterprise_health_index,
            "categoria": categoria, "nivel": nivel,
            "event": event, "semaforo": semaforo,
            "intervencion_recomendada": intervencion,
            "risk_concentration": risk_concentration,
            "dimensiones_en_riesgo": dimensiones_riesgo,
            "war_room_required": war_room_required, "war_room_score": war_room_score,
            "sales_priority": sales_priority, "confidence_score": confidence_score,
            "executive_summary": executive_summary,
            "recommended_actions": recommended_actions,
            "executive_insights": executive_insights,
            "trend": {"score_actual": governance_score, "score_anterior": score_anterior if score_anterior > 0 else None, "delta": delta, "direction": trend},
            "engine_latency_ms": latency_ms,
            "audit_source": f"MESAN_GOVERNANCE_ENGINE_V{self.version.replace('.','_')}"
        }
