# core/billing/billing_engine.py
# MESAN Omega Billing Engine v2.2
# v2.2: calculate_risk_band corregido -- escala consistente con OmegaOrchestrator
#       mayor omega_score = empresa mas sana = menor riesgo de facturacion

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger("mesan.billing")


@dataclass(frozen=True)
class Invoice:
    invoice_id:      str
    tenant_id:       str
    amount:          float
    currency:        str
    reason:          str
    risk_band:       str
    payment_status:  str
    timestamp:       str
    pricing_version: str


class BillingEngine:

    PRICING_VERSION = "MESAN_BILLING_V2"

    BASE_PRICING = {
        "CONTRADICTION_ANALYSIS": 5.0,
        "RISK_SCORING":           10.0,
        "EXECUTION_DECISION":     25.0,
        "AUDIT_LOG":              2.0,
        "PREMIUM_CEO_REPORT":     799.0,
    }

    # Multiplicadores por nivel de riesgo operativo
    # EXTREMO = empresa en estado critico = mayor costo de intervencion
    RISK_MULTIPLIER = {
        "BAJO":    1.0,
        "MEDIO":   1.5,
        "ALTO":    2.5,
        "CRITICO": 4.0,
        "EXTREMO": 6.0,
    }

    DEFAULT_CURRENCY = "MXN"

    def _sanitize_score(self, score) -> int:
        try:
            score = int(score)
        except Exception:
            score = 0
        return max(0, min(100, score))

    def calculate_risk_band(self, score: int) -> str:
        """
        Convierte omega_score (0-100) a banda de riesgo operativo.

        Escala consistente con OmegaOrchestrator.nivel:
            omega_score >= 80 → BAJO    (empresa sana)
            omega_score >= 65 → MEDIO
            omega_score >= 50 → ALTO
            omega_score >= 35 → CRITICO
            omega_score <  35 → EXTREMO (empresa en crisis)

        NOTA: omega_score es escala de SALUD (mayor = mejor).
        A mayor score, menor riesgo y menor multiplicador de facturacion.
        """
        score = self._sanitize_score(score)

        if score >= 80:
            return "BAJO"
        if score >= 65:
            return "MEDIO"
        if score >= 50:
            return "ALTO"
        if score >= 35:
            return "CRITICO"
        return "EXTREMO"

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
    ) -> Invoice:

        score      = self._sanitize_score(risk_score)
        risk_band  = self.calculate_risk_band(score)
        base_price = self.get_base_price(operation)
        multiplier = self.RISK_MULTIPLIER.get(risk_band, 1.0)
        amount     = round(base_price * multiplier, 2)

        invoice = Invoice(
            invoice_id=     str(uuid.uuid4()),
            tenant_id=      tenant_id,
            amount=         amount,
            currency=       self.DEFAULT_CURRENCY,
            reason=         f"{operation} | RISK:{risk_band}",
            risk_band=      risk_band,
            payment_status= "PENDING",
            timestamp=      datetime.now(timezone.utc).isoformat(),
            pricing_version=self.PRICING_VERSION,
        )

        logger.info(
            "[BILLING] invoice_created tenant=%s risk=%s amount=%s",
            tenant_id, risk_band, amount,
        )

        return invoice