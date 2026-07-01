# core/billing/subscription_engine.py -- MESAN Omega Subscription Engine v1.0
"""
Motor de suscripciones de MESAN Omega.

Fase 1: creacion y consulta en memoria.
Fase 2: persistencia en PostgreSQL + Stripe Subscriptions.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from core.billing.models import (
    Subscription, IVEContext, Plan, BillingCycle,
    CustomerType, Currency
)
from core.billing.pricing_engine import pricing_engine

logger = logging.getLogger("mesan.subscription")

CYCLE_DAYS = {
    BillingCycle.MONTHLY: 30,
    BillingCycle.ANNUAL:  365,
}


class SubscriptionEngine:

    def __init__(self):
        self._subs: Dict[str, Subscription] = {}

    def create(self, ctx: IVEContext) -> Subscription:
        sub_id  = str(uuid.uuid4())
        now     = datetime.now(timezone.utc)
        days    = CYCLE_DAYS.get(ctx.billing_cycle, 30)
        renewal = (now + timedelta(days=days)).isoformat()
        amount  = pricing_engine.calculate(ctx)
        sub = Subscription(
            subscription_id= sub_id,
            tenant_id=       ctx.tenant_id,
            plan=            ctx.plan,
            billing_cycle=   ctx.billing_cycle,
            customer_type=   ctx.customer_type,
            status=          "ACTIVE",
            start_date=      now.isoformat(),
            renewal_date=    renewal,
            amount_mxn=      amount,
            currency=        ctx.currency,
            affiliate_id=    ctx.affiliate_id,
            renewal_count=   0,
        )
        self._subs[sub_id] = sub
        logger.info(
            "[SUBSCRIPTION] created tenant=%s plan=%s amount=%.2f",
            ctx.tenant_id, ctx.plan.value, amount,
        )
        return sub

    def get(self, subscription_id: str) -> Optional[Subscription]:
        return self._subs.get(subscription_id)

    def get_by_tenant(self, tenant_id: str) -> Optional[Subscription]:
        for sub in self._subs.values():
            if sub.tenant_id == tenant_id and sub.status == "ACTIVE":
                return sub
        return None

    def renew(self, subscription_id: str) -> Optional[Subscription]:
        sub = self._subs.get(subscription_id)
        if not sub or sub.status != "ACTIVE":
            return None
        days    = CYCLE_DAYS.get(sub.billing_cycle, 30)
        renewal = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        renewed = Subscription(
            subscription_id= sub.subscription_id,
            tenant_id=       sub.tenant_id,
            plan=            sub.plan,
            billing_cycle=   sub.billing_cycle,
            customer_type=   sub.customer_type,
            status=          "ACTIVE",
            start_date=      sub.start_date,
            renewal_date=    renewal,
            amount_mxn=      sub.amount_mxn,
            currency=        sub.currency,
            affiliate_id=    sub.affiliate_id,
            renewal_count=   sub.renewal_count + 1,
        )
        self._subs[subscription_id] = renewed
        logger.info(
            "[SUBSCRIPTION] renewed sub=%s count=%d",
            subscription_id, renewed.renewal_count,
        )
        return renewed

    def cancel(self, subscription_id: str) -> Optional[Subscription]:
        sub = self._subs.get(subscription_id)
        if not sub:
            return None
        cancelled = Subscription(
            subscription_id= sub.subscription_id,
            tenant_id=       sub.tenant_id,
            plan=            sub.plan,
            billing_cycle=   sub.billing_cycle,
            customer_type=   sub.customer_type,
            status=          "CANCELLED",
            start_date=      sub.start_date,
            renewal_date=    sub.renewal_date,
            amount_mxn=      sub.amount_mxn,
            currency=        sub.currency,
            affiliate_id=    sub.affiliate_id,
            renewal_count=   sub.renewal_count,
        )
        self._subs[subscription_id] = cancelled
        return cancelled

    def calculate_mrr(self) -> float:
        mrr = 0.0
        for sub in self._subs.values():
            if sub.status != "ACTIVE":
                continue
            if sub.billing_cycle == BillingCycle.MONTHLY:
                mrr += sub.amount_mxn
            elif sub.billing_cycle == BillingCycle.ANNUAL:
                mrr += sub.amount_mxn / 12.0
        return round(mrr, 2)

    def calculate_arr(self) -> float:
        return round(self.calculate_mrr() * 12.0, 2)

    def get_metrics(self) -> dict:
        active = [s for s in self._subs.values() if s.status == "ACTIVE"]
        mrr    = self.calculate_mrr()
        return {
            "active_subscriptions":  len(active),
            "mrr_mxn":               mrr,
            "arr_mxn":               self.calculate_arr(),
            "avg_revenue_per_user":  round(mrr / len(active), 2) if active else 0.0,
        }


subscription_engine = SubscriptionEngine()