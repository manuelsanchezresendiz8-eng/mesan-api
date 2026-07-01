# core/billing/billing_engine.py -- MESAN Omega Billing Engine v3.0
"""
v3.0: Integrado PricingEngine con IVE Omega.
Mantiene compatibilidad total con firma anterior de .charge().
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.billing.models import (
    Invoice, IVEContext, Plan, BillingCycle, CustomerType,
    Currency, PaymentStatus, RiskBand
)
from core.billing.pricing_engine import pricing_engine, PRICING_VERSION

logger = logging.getLogger("mesan.billing")


class BillingEngine:

    BASE_PRICING = {
        "CONTRADICTION_ANALYSIS": 5.0,
        "RISK_SCORING":           10.0,
        "EXECUTION_DECISION":     25.0,
        "AUDIT_LOG":              2.0,
        "PREMIUM_CEO_REPORT":     799.0,
    }

    DEFAULT_CURRENCY = Currency.MXN

    def _sanitize_score(self, score) -> int:
        try:
            score = int(score)
        except Exception:
            score = 0
        return max(0, min(100, score))

    def calculate_risk_band(self, score: int) -> RiskBand:
        score = self._sanitize_score(score)
        if score >= 80: return RiskBand.BAJO
        if score >= 65: return RiskBand.MEDIO
        if score >= 50: return RiskBand.ALTO
        if score >= 35: return RiskBand.CRITICO
        return RiskBand.EXTREMO

    def get_base_price(self, operation: str) -> float:
        if operation in self.BASE_PRICING:
            return self.BASE_PRICING[operation]
        logger.warning("[BILLING] unknown operation=%s", operation)
        return 1.0

    def charge(
        self,
        tenant_id:  str,
        operation:  str,
        risk_score: int = 0,
        ctx:        Optional[IVEContext] = None,
    ) -> Invoice:
        score     = self._sanitize_score(risk_score)
        risk_band = self.calculate_risk_band(score)

        if ctx is not None:
            ctx.risk_band   = risk_band
            ctx.omega_score = score
            amount     = pricing_engine.calculate(ctx)
            ive_score  = pricing_engine.calculate_ive(ctx)
            plan       = ctx.plan
            cycle      = ctx.billing_cycle
            ctype      = ctx.customer_type
            disc_pct   = ctx.discount_pct
            affiliate  = ctx.affiliate_id
            commission = pricing_engine.calculate_commission(amount, affiliate) if affiliate else 0.0
            subtotal   = round(amount / (1 - disc_pct/100), 2) if disc_pct < 100 else amount
            disc_amt   = round(subtotal - amount, 2)
        else:
            base = self.get_base_price(operation)
            risk_multipliers = {
                RiskBand.BAJO: 1.0, RiskBand.MEDIO: 1.5,
                RiskBand.ALTO: 2.5, RiskBand.CRITICO: 4.0, RiskBand.EXTREMO: 6.0,
            }
            amount     = round(base * risk_multipliers.get(risk_band, 1.0), 2)
            ive_score  = 0.0
            plan       = Plan.ANONYMOUS
            cycle      = BillingCycle.MONTHLY
            ctype      = CustomerType.ANONYMOUS
            disc_pct   = 0.0
            disc_amt   = 0.0
            subtotal   = amount
            affiliate  = None
            commission = 0.0

        invoice = Invoice(
            invoice_id=        str(uuid.uuid4()),
            tenant_id=         tenant_id,
            amount=            amount,
            currency=          self.DEFAULT_CURRENCY,
            reason=            f"{operation} | RISK:{risk_band.value}",
            risk_band=         risk_band,
            payment_status=    PaymentStatus.PENDING,
            timestamp=         datetime.now(timezone.utc).isoformat(),
            pricing_version=   PRICING_VERSION,
            plan=              plan,
            billing_cycle=     cycle,
            customer_type=     ctype,
            discount_pct=      disc_pct,
            discount_amount=   disc_amt,
            subtotal=          subtotal,
            affiliate_id=      affiliate,
            commission_pct=    pricing_engine._cfg["default_affiliate_commission"] if affiliate else 0.0,
            commission_amount= round(commission, 2),
            ive_score=         ive_score,
        )

        logger.info(
            "[BILLING] invoice tenant=%s plan=%s risk=%s amount=%s ive=%.1f",
            tenant_id, plan.value, risk_band.value, amount, ive_score,
        )
        return invoice


billing_engine = BillingEngine()