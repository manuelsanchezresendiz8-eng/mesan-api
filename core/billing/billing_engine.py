# core/billing/billing_engine.py
# MESAN Omega Billing Engine v2.1

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger("mesan.billing")


# ============================================================
# INVOICE MODEL
# ============================================================

@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    tenant_id: str
    amount: float
    currency: str
    reason: str
    risk_band: str
    payment_status: str
    timestamp: str
    pricing_version: str


# ============================================================
# BILLING ENGINE
# ============================================================

class BillingEngine:

    PRICING_VERSION = "MESAN_BILLING_V2"

    BASE_PRICING = {
        "CONTRADICTION_ANALYSIS": 5.0,
        "RISK_SCORING": 10.0,
        "EXECUTION_DECISION": 25.0,
        "AUDIT_LOG": 2.0,
        "PREMIUM_CEO_REPORT": 799.0
    }

    RISK_MULTIPLIER = {
        "BAJO": 1.0,
        "MEDIO": 1.5,
        "ALTO": 2.5,
        "CRITICO": 4.0,
        "EXTREMO": 6.0
    }

    DEFAULT_CURRENCY = "MXN"

    # ============================================================
    # SAFE SCORE
    # ============================================================

    def _sanitize_score(self, score) -> int:

        try:
            score = int(score)
        except Exception:
            score = 0

        return max(0, min(100, score))

    # ============================================================
    # RISK BAND
    # ============================================================

    def calculate_risk_band(self, score: int) -> str:

        score = self._sanitize_score(score)

        if score >= 90:
            return "EXTREMO"

        if score >= 80:
            return "CRITICO"

        if score >= 60:
            return "ALTO"

        if score >= 40:
            return "MEDIO"

        return "BAJO"

    # ============================================================
    # BASE PRICE
    # ============================================================

    def get_base_price(self, operation: str) -> float:

        if operation in self.BASE_PRICING:
            return self.BASE_PRICING[operation]

        logger.warning(
            f"[BILLING] unknown operation={operation}"
        )

        return 1.0

    # ============================================================
    # CHARGE
    # ============================================================

    def charge(
        self,
        tenant_id: str,
        operation: str,
        risk_score: int = 0
    ) -> Invoice:

        score = self._sanitize_score(risk_score)

        risk_band = self.calculate_risk_band(score)

        base_price = self.get_base_price(operation)

        multiplier = self.RISK_MULTIPLIER.get(
            risk_band,
            1.0
        )

        amount = round(base_price * multiplier, 2)

        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            amount=amount,
            currency=self.DEFAULT_CURRENCY,
            reason=f"{operation} | RISK:{risk_band}",
            risk_band=risk_band,
            payment_status="PENDING",
            timestamp=datetime.now(timezone.utc).isoformat(),
            pricing_version=self.PRICING_VERSION
        )

        logger.info(
            f"[BILLING] invoice_created "
            f"tenant={tenant_id} "
            f"risk={risk_band} "
            f"amount={amount}"
        )

        return invoice
