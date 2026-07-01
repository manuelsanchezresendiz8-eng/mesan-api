# core/billing/renewal_engine.py -- MESAN Omega Renewal Engine v1.0
"""
Motor de renovaciones automaticas de MESAN Omega.

Fase 1: deteccion de suscripciones proximas a vencer.
Fase 2: cobro automatico via Stripe + notificacion WhatsApp/correo.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List

from core.billing.subscription_engine import subscription_engine, Subscription

logger = logging.getLogger("mesan.renewal")

RENEWAL_NOTICE_DAYS = 7


class RenewalEngine:

    def get_expiring_soon(self, days_ahead: int = RENEWAL_NOTICE_DAYS) -> List[Subscription]:
        now     = datetime.now(timezone.utc)
        cutoff  = now + timedelta(days=days_ahead)
        expiring = []
        for sub in subscription_engine._subs.values():
            if sub.status != "ACTIVE":
                continue
            try:
                renewal_dt = datetime.fromisoformat(sub.renewal_date)
                if now <= renewal_dt <= cutoff:
                    expiring.append(sub)
            except Exception:
                continue
        return expiring

    def process_renewals(self) -> List[dict]:
        now     = datetime.now(timezone.utc)
        renewed = []
        for sub in list(subscription_engine._subs.values()):
            if sub.status != "ACTIVE":
                continue
            try:
                renewal_dt = datetime.fromisoformat(sub.renewal_date)
                if renewal_dt <= now:
                    result = subscription_engine.renew(sub.subscription_id)
                    if result:
                        renewed.append({
                            "subscription_id": result.subscription_id,
                            "tenant_id":       result.tenant_id,
                            "plan":            result.plan.value,
                            "renewal_count":   result.renewal_count,
                            "new_renewal":     result.renewal_date,
                        })
                        logger.info(
                            "[RENEWAL] processed sub=%s tenant=%s",
                            result.subscription_id, result.tenant_id,
                        )
            except Exception as e:
                logger.error("[RENEWAL] error sub=%s: %s", sub.subscription_id, e)
        return renewed


renewal_engine = RenewalEngine()