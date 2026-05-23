# core/billing/billing_engine.py -- MESAN Omega Billing Engine v1.1
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class Invoice:
    tenant_id: str; amount: float; currency: str
    reason: str; timestamp: str; pricing_version: str

class BillingEngine:
    PRICING_VERSION = "MESAN_BILLING_V1"
    BASE_PRICING    = {"CONTRADICTION_ANALYSIS":5.0,"RISK_SCORING":10.0,
                       "EXECUTION_DECISION":25.0,"AUDIT_LOG":2.0}
    RISK_MULTIPLIER = {"LOW":1.0,"MEDIUM":1.5,"HIGH":2.5,"CRITICAL":4.0}

    def _sanitize_score(self, score: int) -> int:
        if score is None: return 0
        return max(0, min(100, score))

    def calculate_risk_band(self, score: int) -> str:
        score = self._sanitize_score(score)
        if score >= 80: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 20: return "MEDIUM"
        return "LOW"

    def charge(self, tenant_id: str, operation: str, risk_score: int = 0) -> Invoice:
        score  = self._sanitize_score(risk_score)
        base   = self.BASE_PRICING.get(operation, 1.0)
        band   = self.calculate_risk_band(score)
        amount = round(base * self.RISK_MULTIPLIER[band], 2)
        return Invoice(tenant_id=tenant_id, amount=amount, currency="MXN",
                       reason=f"{operation} | RISK:{band}",
                       timestamp=datetime.now(timezone.utc).isoformat(),
                       pricing_version=self.PRICING_VERSION)
