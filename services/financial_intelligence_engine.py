# services/financial_intelligence_engine.py -- MESAN Omega v1.1 hotfix
"""
Financial Intelligence Engine Ω

Elimina score_financiero = 100 hardcodeado del OmegaOrchestrator.

Calcula con los 7 campos disponibles HOY:
    ingresos, nomina, gastos, caja_disponible,
    deuda_mensual, empleados, severance_estimado

Métricas:
    - Liquidez operativa
    - Capital de trabajo
    - DSCR (Debt Service Coverage Ratio)
    - Burn rate
    - Runway (meses de supervivencia)
    - Presión de deuda
    - Financial Health Score (0-100, mayor = más saludable)

Fase B (Sprint 5): iva, isr_retenido, cartera_vencida,
                    activos_totales, pasivos_totales, utilidad_neta
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from core.risk_classification_protocol import RiskClassifierProtocol, default_risk_classifier

logger = logging.getLogger("mesan.financial")

ENGINE_VERSION  = "1.1-hotfix"
ENGINE_NAME     = "MESAN_FINANCIAL_INTELLIGENCE"


class FinancialIntelligenceEngine:
    """
    Motor de inteligencia financiera MESAN Ω.

    Inputs requeridos:
        ingresos        float  Ingresos mensuales
        nomina          float  Nómina mensual total
        gastos          float  Gastos operativos mensuales (sin nómina ni deuda)
        caja_disponible float  Caja y equivalentes disponibles
        deuda_mensual   float  Obligaciones financieras mensuales
        empleados       int    Número de empleados
        severance_estimado float Estimación de liquidación total

    Outputs:
        financial_score       int    Score 0-100 (mayor = más saludable)
        financial_health_score int   Alias de financial_score
        financial_risk_score  int    100 - financial_score
        runway_months         float  Meses de supervivencia con caja actual
        financial_exposure_mxn float Exposición financiera estimada
        nivel                 str    Clasificación MESAN Ω estándar
        alertas               list
        riesgos               list
    """

    def __init__(self, risk_classifier: RiskClassifierProtocol = None):
        self.version   = ENGINE_VERSION
        self.engine    = ENGINE_NAME
        self._risk     = risk_classifier or default_risk_classifier()

    # ── Métricas financieras ──────────────────────────────────────────────────

    def _calcular_dscr(self, ingresos: float, nomina: float, gastos: float, deuda: float) -> float:
        """
        Debt Service Coverage Ratio corregido.
        Usa flujo operativo (ingresos - nomina - gastos) sobre servicio de deuda.
        Fórmula anterior (ingresos/deuda) era incorrecta — no considera costos operativos.
        """
        if deuda <= 0:
            return 10.0
        operating_cash = ingresos - nomina - gastos
        return round(operating_cash / deuda, 2)

    def _calcular_burn(self, ingresos: float, nomina: float, gastos: float, deuda: float) -> tuple:
        """
        Burn separado en valor absoluto y ratio.

        burn_mxn   = gasto mensual total absoluto (nomina + gastos + deuda)
        burn_ratio = % de ingresos consumido por burn_mxn

        Nota: 'burn rate' en sentido estricto es consumo de caja (burn_mxn).
        burn_ratio es el expense ratio — más útil para scoring comparativo.
        """
        burn_mxn = nomina + gastos + deuda
        if ingresos <= 0:
            burn_ratio = 200.0
        else:
            burn_ratio = round(min((burn_mxn / ingresos) * 100, 200), 2)
        return round(burn_mxn, 2), burn_ratio

    def _calcular_capital_trabajo(self, ingresos: float, nomina: float, gastos: float, deuda: float) -> float:
        """Flujo operativo mensual neto."""
        return round(ingresos - nomina - gastos - deuda, 2)

    def _calcular_runway(self, caja: float, nomina: float, gastos: float, deuda: float) -> tuple:
        """
        Runway separado internamente.

        runway_operativo: meses cubriendo solo costos operativos (nomina + gastos)
                          — refleja cuánto tiempo puede operar sin generar ingreso
        runway_total:     meses cubriendo operación + deuda
                          — refleja solvencia real bajo estrés total

        El scoring sigue usando runway_total para compatibilidad.
        """
        burn_operativo = nomina + gastos
        burn_total     = burn_operativo + deuda

        runway_operativo = round(caja / burn_operativo, 1) if burn_operativo > 0 and caja > 0 else (99.0 if burn_operativo <= 0 else 0.0)
        runway_total     = round(caja / burn_total,     1) if burn_total     > 0 and caja > 0 else (99.0 if burn_total     <= 0 else 0.0)

        return runway_operativo, runway_total

    def _calcular_presion_deuda(self, ingresos: float, deuda: float) -> float:
        """% de ingresos comprometidos en deuda."""
        if ingresos <= 0:
            return 100.0
        return round((deuda / ingresos) * 100, 2)

    def _calcular_presion_nomina(self, ingresos: float, nomina: float) -> float:
        """% de ingresos comprometidos en nómina."""
        if ingresos <= 0:
            return 100.0
        return round((nomina / ingresos) * 100, 2)

    def _calcular_costo_empleado(self, nomina: float, empleados: int) -> float:
        """Costo promedio por empleado mensual."""
        if empleados <= 0:
            return 0.0
        return round(nomina / empleados, 2)

    # ── Engine principal ──────────────────────────────────────────────────────

    def analizar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula el Financial Health Score y métricas asociadas.
        Reemplaza score_financiero = 100 en el OmegaOrchestrator.
        """
        started   = time.time()
        tenant_id = data.get("tenant_id", "DEFAULT")
        trace_id  = data.get("trace_id",  "NO_TRACE")

        # ── Inputs seguros ────────────────────────────────────────────────
        ingresos   = max(0.0, float(data.get("ingresos",           0)))
        nomina     = max(0.0, float(data.get("nomina",             0)))
        gastos     = max(0.0, float(data.get("gastos",             0)))
        caja       = max(0.0, float(data.get("caja_disponible",    0)))
        deuda      = max(0.0, float(data.get("deuda_mensual",      0)))
        empleados  = max(0,   int(data.get("empleados",            0)))
        severance  = max(0.0, float(data.get("severance_estimado", 0)))

        # ── Métricas (v1.1 hotfix — fórmulas corregidas) ─────────────────────
        dscr                             = self._calcular_dscr(ingresos, nomina, gastos, deuda)
        burn_mxn, burn_ratio             = self._calcular_burn(ingresos, nomina, gastos, deuda)
        runway_operativo, runway_total   = self._calcular_runway(caja, nomina, gastos, deuda)
        runway_months                    = runway_total    # alias para scoring (compatibilidad)
        burn_rate                        = burn_ratio      # alias para scoring (compatibilidad)
        capital_trabajo  = self._calcular_capital_trabajo(ingresos, nomina, gastos, deuda)
        presion_deuda    = self._calcular_presion_deuda(ingresos, deuda)
        presion_nomina   = self._calcular_presion_nomina(ingresos, nomina)
        costo_empleado   = self._calcular_costo_empleado(nomina, empleados)

        # ── Score y drivers ───────────────────────────────────────────────
        score   = 100
        alertas: List[dict] = []
        riesgos: List[dict] = []
        drivers: List[str]  = []

        # DSCR
        if dscr < 1.0:
            score -= 30
            drivers.append("DSCR menor a 1.0 — ingresos insuficientes para cubrir deuda")
            alertas.append({"tipo": "DSCR", "nivel": "CRITICO", "valor": dscr,
                            "mensaje": "Flujo no cubre obligaciones financieras"})
            riesgos.append({"riesgo": "DSCR_CRITICO", "severidad": "CRITICA",
                            "detalle": f"DSCR = {dscr}"})
        elif dscr < 1.5:
            score -= 15
            drivers.append("DSCR menor a 1.5 — margen de cobertura estrecho")
            alertas.append({"tipo": "DSCR", "nivel": "ALTO", "valor": dscr,
                            "mensaje": "Margen de cobertura de deuda estrecho"})

        # Burn Rate
        if burn_rate > 90:
            score -= 25
            drivers.append(f"Burn rate crítico ({burn_rate:.1f}%)")
            alertas.append({"tipo": "BURN_RATE", "nivel": "CRITICO", "valor": burn_rate,
                            "mensaje": "Gastos superan ingresos"})
            riesgos.append({"riesgo": "BURN_RATE_CRITICO", "severidad": "CRITICA",
                            "detalle": f"Burn rate = {burn_rate}%"})
        elif burn_rate > 75:
            score -= 15
            drivers.append(f"Burn rate elevado ({burn_rate:.1f}%)")
            alertas.append({"tipo": "BURN_RATE", "nivel": "ALTO", "valor": burn_rate,
                            "mensaje": "Gastos operativos elevados"})
        elif burn_rate > 60:
            score -= 8
            drivers.append(f"Burn rate moderado ({burn_rate:.1f}%)")

        # Runway
        if runway_months < 1:
            score -= 30
            drivers.append(f"Runway crítico: {runway_months} meses")
            alertas.append({"tipo": "RUNWAY", "nivel": "CRITICO", "valor": runway_months,
                            "mensaje": "Caja insuficiente para cubrir menos de 1 mes"})
            riesgos.append({"riesgo": "RUNWAY_CRITICO", "severidad": "CRITICA",
                            "detalle": f"Runway = {runway_months} meses"})
        elif runway_months < 3:
            score -= 20
            drivers.append(f"Runway bajo: {runway_months} meses")
            alertas.append({"tipo": "RUNWAY", "nivel": "ALTO", "valor": runway_months,
                            "mensaje": "Menos de 3 meses de runway"})
        elif runway_months < 6:
            score -= 10
            drivers.append(f"Runway limitado: {runway_months} meses")

        # Presión de deuda
        if presion_deuda > 45:
            score -= 15
            drivers.append(f"Presión de deuda crítica ({presion_deuda:.1f}% de ingresos)")
            alertas.append({"tipo": "DEUDA", "nivel": "CRITICO", "valor": presion_deuda,
                            "mensaje": "Deuda supera 45% de ingresos"})
        elif presion_deuda > 30:
            score -= 8
            drivers.append(f"Presión de deuda elevada ({presion_deuda:.1f}%)")

        # Presión de nómina
        if presion_nomina > 60:
            score -= 10
            drivers.append(f"Nómina consume {presion_nomina:.1f}% de ingresos")
            alertas.append({"tipo": "NOMINA", "nivel": "ALTO", "valor": presion_nomina,
                            "mensaje": "Carga de nómina elevada"})

        # Severance vs caja
        if caja > 0 and severance > 0:
            severance_ratio = (severance / caja) * 100
            if severance_ratio > 80:
                score -= 10
                drivers.append(f"Severance representa {severance_ratio:.1f}% de la caja")

        score = max(0, min(100, score))

        # ── Exposición financiera (v1.1 — sin doble conteo) ──────────────────
        # Tres categorías independientes:
        exposicion_liquidez = abs(capital_trabajo) * 3 if capital_trabajo < 0 else 0.0
        # runway solo si NO hay déficit operativo (evita doble conteo con liquidez)
        if capital_trabajo >= 0 and runway_months < 3:
            exposicion_runway = burn_mxn * max(0, 3 - runway_months)
        else:
            exposicion_runway = 0.0
        exposicion_deuda = deuda * 6 if dscr < 1.0 and deuda > 0 else 0.0
        exposicion = round(exposicion_liquidez + exposicion_runway + exposicion_deuda, 2)

        # ── Clasificación ─────────────────────────────────────────────────
        nivel = self._risk.classify_esi(score)

        latency_ms = round((time.time() - started) * 1000, 2)

        logger.info("[FINANCIAL] tenant=%s score=%s runway=%.1fm burn=%.1f%%",
                    tenant_id, score, runway_months, burn_rate)

        return {
            "engine":                ENGINE_NAME,
            "engine_status":         "OK",
            "version":               self.version,
            "timestamp":             datetime.now(timezone.utc).isoformat(),
            "tenant_id":             tenant_id,
            "trace_id":              trace_id,

            # Scores
            "financial_score":       score,
            "financial_health_score": score,
            "financial_risk_score":  100 - score,

            # Clasificación
            "nivel":                 nivel,

            # Métricas clave
            "runway_months":         runway_months,
            "dscr":                  dscr,
            "burn_mxn":              burn_mxn,
            "burn_ratio_pct":        burn_ratio,
            "burn_rate_pct":         burn_ratio,          # alias compatibilidad
            "runway_operativo_months": runway_operativo,
            "runway_total_months":   runway_total,
            "capital_trabajo_mxn":   capital_trabajo,
            "presion_deuda_pct":     presion_deuda,
            "presion_nomina_pct":    presion_nomina,
            "costo_empleado_mxn":    costo_empleado,

            # Exposición
            "financial_exposure_mxn": exposicion,
            "exposicion_estimada_mxn": exposicion,  # alias para ExposureAggregator

            # Hallazgos
            "drivers":               drivers,
            "alertas":               alertas,
            "riesgos":               riesgos,
            "riesgos_detectados":    len(riesgos),

            "engine_latency_ms":     latency_ms,
        }
