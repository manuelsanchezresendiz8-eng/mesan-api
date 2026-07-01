# core/billing/pricing_engine.py -- MESAN Omega Pricing Engine v1.0
"""
Omega Pricing Engine -- calcula el precio dinamico usando el IVE Omega.

Configuracion centralizada en PRICING_CONFIG.
Para modificar precios no se toca el algoritmo, solo la config.
"""

import logging
from typing import Dict
from core.billing.models import (
    IVEContext, Plan, BillingCycle, CustomerType, RiskBand
)

logger = logging.getLogger("mesan.pricing")

PRICING_VERSION = "IVE_OMEGA_1.0"

PRICING_CONFIG: Dict = {
    "base_price": {
        Plan.START:      1_490.0,
        Plan.GROWTH:     2_990.0,
        Plan.BUSINESS:   5_990.0,
        Plan.ENTERPRISE: 0.0,
        Plan.ANONYMOUS:  0.0,
    },
    "annual_discount_pct": 20.0,
    "customer_type_multiplier": {
        CustomerType.DIRECT:    1.0,
        CustomerType.AFFILIATE: 1.0,
        CustomerType.CORPORATE: 0.85,
        CustomerType.ANONYMOUS: 0.0,
    },
    "risk_multiplier": {
        RiskBand.BAJO:    1.0,
        RiskBand.MEDIO:   1.1,
        RiskBand.ALTO:    1.25,
        RiskBand.CRITICO: 1.5,
        RiskBand.EXTREMO: 2.0,
    },
    "ive_weights": {
        "plan_value": 0.30,
        "exposure":   0.25,
        "risk":       0.20,
        "size":       0.15,
        "complexity": 0.10,
    },
    "max_exposure_ref":          5_000_000.0,
    "max_ingresos_ref":          2_000_000.0,
    "max_empleados_ref":         500,
    "loyalty_discount_per_renewal": 1.0,
    "max_loyalty_discount":      10.0,
    "default_affiliate_commission": 20.0,
    "max_engines":               10,
}

_ive_sum = sum(PRICING_CONFIG["ive_weights"].values())
assert abs(_ive_sum - 1.0) < 1e-9, f"ive_weights no suma 1.0: {_ive_sum}"


class PricingEngine:

    def __init__(self, config: Dict = None):
        self._cfg = config or PRICING_CONFIG
        logger.info("[PRICING] PricingEngine v%s inicializado", PRICING_VERSION)

    def calculate_ive(self, ctx: IVEContext) -> float:
        w = self._cfg["ive_weights"]
        plan_scores = {
            Plan.START: 25.0, Plan.GROWTH: 50.0,
            Plan.BUSINESS: 75.0, Plan.ENTERPRISE: 100.0, Plan.ANONYMOUS: 0.0,
        }
        plan_score      = plan_scores.get(ctx.plan, 0.0)
        max_exp         = self._cfg["max_exposure_ref"]
        exposure_score  = min(ctx.total_exposure_mxn / max_exp, 1.0) * 100.0
        risk_score      = max(0.0, min(100.0, 100.0 - ctx.omega_score))
        max_emp         = self._cfg["max_empleados_ref"]
        max_ing         = self._cfg["max_ingresos_ref"]
        emp_norm        = min(ctx.empleados / max_emp, 1.0) * 100.0 if max_emp else 0.0
        ing_norm        = min(ctx.ingresos / max_ing, 1.0) * 100.0 if max_ing else 0.0
        size_score      = emp_norm * 0.4 + ing_norm * 0.6
        max_eng         = self._cfg["max_engines"]
        complexity_score = min(ctx.engines_used / max_eng, 1.0) * 100.0 if max_eng else 0.0
        ive = (
            plan_score       * w["plan_value"] +
            exposure_score   * w["exposure"]   +
            risk_score       * w["risk"]        +
            size_score       * w["size"]        +
            complexity_score * w["complexity"]
        )
        return round(max(0.0, min(100.0, ive)), 2)

    def calculate(self, ctx: IVEContext) -> float:
        if ctx.plan in (Plan.ENTERPRISE, Plan.ANONYMOUS):
            return 0.0
        base = self._cfg["base_price"].get(ctx.plan, 0.0)
        if base == 0.0:
            return 0.0
        risk_mult  = self._cfg["risk_multiplier"].get(ctx.risk_band, 1.0)
        ctype_mult = self._cfg["customer_type_multiplier"].get(ctx.customer_type, 1.0)
        subtotal   = base * risk_mult * ctype_mult
        if ctx.billing_cycle == BillingCycle.ANNUAL:
            subtotal *= (1.0 - self._cfg["annual_discount_pct"] / 100.0)
        loyalty_disc = min(
            ctx.renewal_count * self._cfg["loyalty_discount_per_renewal"],
            self._cfg["max_loyalty_discount"]
        )
        subtotal *= (1.0 - loyalty_disc / 100.0)
        if ctx.discount_pct > 0:
            subtotal *= (1.0 - ctx.discount_pct / 100.0)
        return round(max(0.0, subtotal), 2)

    def calculate_commission(self, amount: float, affiliate_id: str) -> float:
        if not affiliate_id:
            return 0.0
        pct = self._cfg["default_affiliate_commission"]
        return round(amount * pct / 100.0, 2)

    def get_plan_for_context(self, empleados: int, ingresos: float) -> Plan:
        if empleados <= 15:   return Plan.START
        if empleados <= 50:   return Plan.GROWTH
        if empleados <= 200:  return Plan.BUSINESS
        return Plan.ENTERPRISE


pricing_engine = PricingEngine()