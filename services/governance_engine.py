# services/governance_engine.py
# MESAN Omega Governance Engine v2.1

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger("mesan.governance")


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def normalize_score(score):
    try:
        score = float(score)
    except Exception:
        score = 0

    if score != score:  # NaN
        score = 0

    return max(0, min(100, score))


class GovernanceEngine:

    def __init__(self):
        self.version = "2.1"
        self.engine = "MESAN_GOVERNANCE"

    def calcular(self, data: dict) -> dict:

        started = time.time()

        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id = data.get("trace_id", "NO_TRACE")

        # ==========================
        # INPUTS
        # ==========================

        score_fiscal = normalize_score(
            safe_float(data.get("score_fiscal", 100))
        )

        score_compliance = normalize_score(
            safe_float(data.get("score_compliance", 100))
        )

        score_laboral = normalize_score(
            safe_float(data.get("score_laboral", 100))
        )

        score_contractual = normalize_score(
            safe_float(data.get("score_contractual", 100))
        )

        score_financiero = normalize_score(
            safe_float(data.get("score_financiero", 100))
        )

        exposicion_total = max(
            0,
            safe_float(data.get("exposicion_total", 0))
        )

        # ==========================
        # PESOS
        # ==========================

        pesos = {
            "fiscal": 0.30,
            "compliance": 0.20,
            "laboral": 0.20,
            "contractual": 0.15,
            "financiero": 0.15
        }

        # ==========================
        # GOVERNANCE SCORE
        # ==========================

        governance_score = round(
            (
                score_fiscal * pesos["fiscal"]
            ) +
            (
                score_compliance * pesos["compliance"]
            ) +
            (
                score_laboral * pesos["laboral"]
            ) +
            (
                score_contractual * pesos["contractual"]
            ) +
            (
                score_financiero * pesos["financiero"]
            ),
            2
        )

        governance_score = normalize_score(
            governance_score
        )

        # ==========================
        # NIVEL
        # ==========================

        if governance_score >= 90:
            nivel = "VERDE"
            categoria = "WORLD_CLASS"

        elif governance_score >= 80:
            nivel = "VERDE"
            categoria = "BLINDADO"

        elif governance_score >= 70:
            nivel = "AMARILLO"
            categoria = "CONTROLADO"

        elif governance_score >= 50:
            nivel = "NARANJA"
            categoria = "VULNERABLE"

        else:
            nivel = "ROJO"
            categoria = "CRITICO"

        # ==========================
        # DIMENSIONES EN RIESGO
        # ==========================

        dimensiones_riesgo = []

        if score_fiscal < 70:
            dimensiones_riesgo.append("FISCAL")

        if score_compliance < 70:
            dimensiones_riesgo.append("COMPLIANCE")

        if score_laboral < 70:
            dimensiones_riesgo.append("LABORAL")

        if score_contractual < 70:
            dimensiones_riesgo.append("CONTRACTUAL")

        if score_financiero < 70:
            dimensiones_riesgo.append("FINANCIERO")

        risk_concentration = round(
            (len(dimensiones_riesgo) / 5) * 100,
            2
        )

        # ==========================
        # RISK INDEX
        # ==========================

        exposure_factor = min(
            exposicion_total / 100000,
            25
        )

        concentration_factor = (
            risk_concentration * 0.15
        )

        governance_risk_index = round(
            min(
                (
                    (100 - governance_score) * 0.60
                ) +
                exposure_factor +
                concentration_factor,
                100
            ),
            2
        )

        # ==========================
        # SURVIVAL SCORE
        # ==========================

        enterprise_survival_score = round(
            max(
                0,
                100 - (
                    governance_risk_index * 0.70
                )
            ),
            2
        )

        # ==========================
        # BENCHMARK
        # ==========================

        if governance_score >= 90:
            benchmark = "TOP_5%"

        elif governance_score >= 85:
            benchmark = "TOP_10%"

        elif governance_score >= 75:
            benchmark = "TOP_25%"

        elif governance_score >= 60:
            benchmark = "PROMEDIO"

        else:
            benchmark = "RIESGO_ELEVADO"

        # ==========================
        # CONFIDENCE SCORE
        # ==========================

        confidence_score = round(
            max(
                40,
                100 -
                (
                    len(dimensiones_riesgo) * 7
                ) -
                (
                    risk_concentration * 0.10
                )
            ),
            2
        )

        # ==========================
        # WAR ROOM
        # ==========================

        war_room_required = (
            governance_score < 50
            or len(dimensiones_riesgo) >= 3
            or exposicion_total >= 1000000
        )

        war_room_score = round(
            (
                governance_risk_index * 0.5
            ) +
            (
                risk_concentration * 0.3
            ) +
            (
                (100 - confidence_score) * 0.2
            ),
            2
        )

        # ==========================
        # SEMAFORO
        # ==========================

        if governance_risk_index >= 80:
            semaforo = "ROJO"
            intervencion = "INMEDIATA"

        elif governance_risk_index >= 60:
            semaforo = "NARANJA"
            intervencion = "30_DIAS"

        elif governance_risk_index >= 40:
            semaforo = "AMARILLO"
            intervencion = "90_DIAS"

        else:
            semaforo = "VERDE"
            intervencion = "MONITOREO"

        # ==========================
        # MADUREZ
        # ==========================

        if governance_score >= 90:
            governance_maturity = "WORLD_CLASS"

        elif governance_score >= 80:
            governance_maturity = "ADVANCED"

        elif governance_score >= 70:
            governance_maturity = "CONTROLLED"

        elif governance_score >= 50:
            governance_maturity = "REACTIVE"

        else:
            governance_maturity = "FRAGILE"

        # ==========================
        # STATUS
        # ==========================

        if governance_score >= 90:
            governance_status = "BEST_IN_CLASS"

        elif governance_score >= 80:
            governance_status = "HEALTHY"

        elif governance_score >= 70:
            governance_status = "STABLE"

        elif governance_score >= 50:
            governance_status = "AT_RISK"

        else:
            governance_status = "CRITICAL"

        # ==========================
        # SALES PRIORITY
        # ==========================

        if exposicion_total >= 2000000:
            sales_priority = "A+"

        elif exposicion_total >= 1000000:
            sales_priority = "A"

        elif exposicion_total >= 500000:
            sales_priority = "B"

        else:
            sales_priority = "C"

        # ==========================
        # HEALTH INDEX
        # ==========================

        enterprise_health_index = round(
            (
                governance_score * 0.40
            ) +
            (
                enterprise_survival_score * 0.40
            ) +
            (
                confidence_score * 0.20
            ),
            2
        )

        # ==========================
        # SCORECARD
        # ==========================

        scorecard = {
            "fiscal": score_fiscal,
            "compliance": score_compliance,
            "laboral": score_laboral,
            "contractual": score_contractual,
            "financiero": score_financiero
        }

        critical_dimensions = list(
            dimensiones_riesgo
        )

        executive_summary = (
            f"Governance Score {governance_score}/100. "
            f"Madurez {governance_maturity}. "
            f"Enterprise Survival Score {enterprise_survival_score}. "
            f"Risk Index {governance_risk_index}. "
            f"Dimensiones críticas: {len(dimensiones_riesgo)}. "
            f"Intervención recomendada: {intervencion}. "
            f"Benchmark: {benchmark}."
        )

        latency_ms = round(
            (time.time() - started) * 1000,
            2
        )

        logger.info(
            f"[GOVERNANCE] tenant={tenant_id} "
            f"score={governance_score} "
            f"risk={governance_risk_index}"
        )

        return {
            "engine": self.engine,
            "engine_status": "OK",
            "version": self.version,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "tenant_id": tenant_id,
            "trace_id": trace_id,

            "enterprise_governance_score": governance_score,
            "governance_risk_index": governance_risk_index,
            "enterprise_survival_score": enterprise_survival_score,
            "enterprise_health_index": enterprise_health_index,

            "nivel": nivel,
            "categoria": categoria,

            "governance_status": governance_status,
            "governance_maturity": governance_maturity,

            "benchmark_empresarial": benchmark,

            "war_room_required": war_room_required,
            "war_room_score": war_room_score,

            "semaforo": semaforo,
            "intervencion_recomendada": intervencion,

            "sales_priority": sales_priority,

            "risk_concentration": risk_concentration,
            "confidence_score": confidence_score,

            "dimensiones_en_riesgo": dimensiones_riesgo,
            "critical_dimensions": critical_dimensions,

            "scorecard": scorecard,

            "executive_summary": executive_summary,

            "audit_source": "MESAN_GOVERNANCE_ENGINE_V2",

            "engine_latency_ms": latency_ms
        }
