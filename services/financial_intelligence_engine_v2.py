# services/financial_intelligence_engine_v2.py -- MESAN Omega v2.0 SHADOW FINAL
"""
Shadow engine — NUNCA modifica decisiones de producción.
Corre en paralelo con v1.1 para validar scoring vectorial con datos reales.
Promover a oficial solo cuando drift < 5 durante 30 días con datos reales.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.risk_classification_protocol import RiskClassifierProtocol, default_risk_classifier

logger = logging.getLogger("mesan.financial.v2")

ENGINE_VERSION = "2.0-shadow"
ENGINE_NAME    = "MESAN_FINANCIAL_INTELLIGENCE_V2"


class FinancialIntelligenceEngineV2:

    def __init__(
        self,
        risk_classifier: Optional[RiskClassifierProtocol] = None,
        shadow_mode: bool = True,
    ):
        if not shadow_mode:
            raise RuntimeError(
                "FinancialIntelligenceEngineV2 MUST RUN IN SHADOW MODE ONLY. "
                "Use FinancialIntelligenceEngine for production."
            )
        self.shadow_mode = shadow_mode
        self._risk       = risk_classifier or default_risk_classifier()

    def analizar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        ingresos  = float(data.get("ingresos",           0))
        nomina    = float(data.get("nomina",             0))
        gastos    = float(data.get("gastos",             0))
        caja      = float(data.get("caja_disponible",    0))
        deuda     = float(data.get("deuda_mensual",      0))
        severance = float(data.get("severance_estimado", 0))

        # ── Base metrics ──────────────────────────────────────────────────
        burn_total  = nomina + gastos + deuda
        runway      = round(caja / max(burn_total, 1), 2)

        operating_cash = ingresos - nomina - gastos
        dscr           = round(operating_cash / deuda, 2) if deuda > 0 else 10.0
        burn_ratio     = round((burn_total / ingresos) * 100, 2) if ingresos > 0 else 200.0

        # ── Normalizadores 0-1 ─────────────────────────────────────────────
        f_runway = min(1.0, runway / 12)
        f_burn   = 1 - min(1.0, burn_ratio / 100)
        f_dscr   = min(1.0, max(0.0, dscr / 2.0))
        f_deuda  = (1 - min(1.0, deuda / ingresos)) if ingresos > 0 else 0.0
        f_margen = max(0.0, min(1.0, operating_cash / ingresos)) if ingresos > 0 else 0.0

        # ── Sub-scores vectoriales ─────────────────────────────────────────
        liquidez     = 0.4*f_runway + 0.3*f_burn   + 0.3*min(1.0, caja / 100_000)
        solvencia    = 0.5*f_dscr   + 0.5*f_deuda
        # Fix: fórmula original — no mezclar con burn para que drift sea calibración real
        f_margen_sin_gastos = max(0.0, min(1.0, (ingresos - nomina) / ingresos)) if ingresos > 0 else 0.0
        eficiencia   = 0.5*f_margen + 0.5*f_margen_sin_gastos
        supervivencia= 0.5*f_runway + 0.3*max(0.0, 1-min(1.0, (deuda*6)/500_000)) \
                     + 0.2*max(0.0, 1-min(1.0, severance/500_000))

        # ── Score final ponderado ─────────────────────────────────────────
        score_raw = 100 * (0.30*liquidez + 0.25*solvencia + 0.25*eficiencia + 0.20*supervivencia)
        score     = min(100, max(0, int(round(score_raw))))
        nivel     = self._risk.classify_esi(score)

        latency = round((time.time() - start) * 1000, 2)
        logger.debug("[FINANCIAL_V2] shadow score=%s nivel=%s", score, nivel)

        return {
            "engine":              ENGINE_NAME,
            "version":             ENGINE_VERSION,
            "shadow_mode":         self.shadow_mode,
            "financial_score_v2":  score,
            "nivel":               nivel,
            "subscores": {
                "liquidez":        round(liquidez,      4),
                "solvencia":       round(solvencia,     4),
                "eficiencia":      round(eficiencia,    4),
                "supervivencia":   round(supervivencia, 4),
            },
            "metrics": {
                "dscr":            dscr,
                "burn_ratio":      burn_ratio,
                "runway_months":   runway,
            },
            "exposicion":              round((deuda * 6) + max(0.0, burn_total * 2), 2),
            "exposicion_estimada_mxn": round((deuda * 6) + max(0.0, burn_total * 2), 2),  # Fix P2-G1
            "financial_score_v2_raw": round(score_raw, 4),
            "timestamp":           datetime.now(timezone.utc).isoformat(),
            "engine_latency_ms":   latency,
        }
