# core/billing/models.py -- MESAN Omega Billing Models v1.0
"""
Modelos de datos del Omega Billing Engine.

Diseñados para ser extraibles como microservicio sin modificar
la logica de negocio. Sin dependencias del resto del sistema.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class Plan(str, Enum):
    START      = "OMEGA_START"
    GROWTH     = "OMEGA_GROWTH"
    BUSINESS   = "OMEGA_BUSINESS"
    ENTERPRISE = "OMEGA_ENTERPRISE"
    ANONYMOUS  = "ANONYMOUS"


class BillingCycle(str, Enum):
    MONTHLY = "MONTHLY"
    ANNUAL  = "ANNUAL"


class CustomerType(str, Enum):
    DIRECT    = "DIRECT"
    AFFILIATE = "AFFILIATE"
    CORPORATE = "CORPORATE"
    ANONYMOUS = "ANONYMOUS"


class Currency(str, Enum):
    MXN = "MXN"
    USD = "USD"


class PaymentStatus(str, Enum):
    PENDING   = "PENDING"
    PAID      = "PAID"
    FAILED    = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED  = "REFUNDED"


class RiskBand(str, Enum):
    BAJO    = "BAJO"
    MEDIO   = "MEDIO"
    ALTO    = "ALTO"
    CRITICO = "CRITICO"
    EXTREMO = "EXTREMO"


@dataclass
class IVEContext:
    """Contexto para calcular el Indice de Valor Empresarial."""
    tenant_id:          str          = "anonymous"
    plan:               Plan         = Plan.ANONYMOUS
    customer_type:      CustomerType = CustomerType.ANONYMOUS
    billing_cycle:      BillingCycle = BillingCycle.MONTHLY
    empleados:          int          = 0
    ingresos:           float        = 0.0
    sector:             str          = "GENERAL"
    omega_score:        int          = 50
    total_exposure_mxn: float        = 0.0
    engines_used:       int          = 9
    risk_band:          RiskBand     = RiskBand.MEDIO
    affiliate_id:       Optional[str] = None
    discount_pct:       float        = 0.0
    renewal_count:      int          = 0
    currency:           Currency     = Currency.MXN


@dataclass
class Invoice:
    invoice_id:       str
    tenant_id:        str
    amount:           float
    currency:         Currency
    reason:           str
    risk_band:        RiskBand
    payment_status:   PaymentStatus
    timestamp:        str
    pricing_version:  str
    plan:             Plan            = Plan.ANONYMOUS
    billing_cycle:    BillingCycle    = BillingCycle.MONTHLY
    customer_type:    CustomerType    = CustomerType.ANONYMOUS
    discount_pct:     float           = 0.0
    discount_amount:  float           = 0.0
    subtotal:         float           = 0.0
    affiliate_id:     Optional[str]   = None
    commission_pct:   float           = 0.0
    commission_amount:float           = 0.0
    renewal_date:     Optional[str]   = None
    payment_url:      Optional[str]   = None
    ive_score:        float           = 0.0
    metadata:         Dict[str, Any]  = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "invoice_id":        self.invoice_id,
            "tenant_id":         self.tenant_id,
            "amount":            self.amount,
            "currency":          self.currency.value,
            "reason":            self.reason,
            "risk_band":         self.risk_band.value,
            "payment_status":    self.payment_status.value,
            "timestamp":         self.timestamp,
            "pricing_version":   self.pricing_version,
            "plan":              self.plan.value,
            "billing_cycle":     self.billing_cycle.value,
            "customer_type":     self.customer_type.value,
            "subtotal":          self.subtotal,
            "discount_pct":      self.discount_pct,
            "discount_amount":   self.discount_amount,
            "affiliate_id":      self.affiliate_id,
            "commission_pct":    self.commission_pct,
            "commission_amount": self.commission_amount,
            "renewal_date":      self.renewal_date,
            "payment_url":       self.payment_url,
            "ive_score":         round(self.ive_score, 2),
        }


@dataclass
class Subscription:
    subscription_id: str
    tenant_id:       str
    plan:            Plan
    billing_cycle:   BillingCycle
    customer_type:   CustomerType
    status:          str
    start_date:      str
    renewal_date:    str
    amount_mxn:      float
    currency:        Currency
    affiliate_id:    Optional[str]  = None
    renewal_count:   int            = 0
    metadata:        Dict[str, Any] = field(default_factory=dict)


@dataclass
class BillingMetrics:
    mrr:                  float = 0.0
    arr:                  float = 0.0
    ltv:                  float = 0.0
    cac:                  float = 0.0
    active_subs:          int   = 0
    churn_rate:           float = 0.0
    avg_revenue_per_user: float = 0.0