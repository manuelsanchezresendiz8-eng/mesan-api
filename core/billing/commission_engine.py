# core/billing/commission_engine.py -- MESAN Omega Commission Engine v1.0
"""
Motor de comisiones para el programa de aliados de MESAN Omega.

Fase 1: calculo de comisiones con reglas configurables.
Fase 2: liquidacion automatica via Stripe Connect o SPEI.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger("mesan.commission")

COMMISSION_RULES: Dict[str, float] = {
    "CONTADOR":  20.0,
    "DESPACHO":  22.0,
    "CONSULTOR": 18.0,
    "BROKER":    25.0,
    "CAMARA":    15.0,
    "DEFAULT":   20.0,
}


@dataclass
class CommissionRecord:
    commission_id:  str
    affiliate_id:   str
    affiliate_type: str
    invoice_id:     str
    tenant_id:      str
    amount_mxn:     float
    commission_pct: float
    commission_mxn: float
    status:         str
    timestamp:      str

    def to_dict(self):
        return {
            "commission_id":  self.commission_id,
            "affiliate_id":   self.affiliate_id,
            "affiliate_type": self.affiliate_type,
            "invoice_id":     self.invoice_id,
            "tenant_id":      self.tenant_id,
            "amount_mxn":     self.amount_mxn,
            "commission_pct": self.commission_pct,
            "commission_mxn": self.commission_mxn,
            "status":         self.status,
            "timestamp":      self.timestamp,
        }


class CommissionEngine:

    def __init__(self):
        self._records: List[CommissionRecord] = []

    def calculate(
        self,
        invoice_id:     str,
        tenant_id:      str,
        amount_mxn:     float,
        affiliate_id:   str,
        affiliate_type: str = "DEFAULT",
    ) -> CommissionRecord:
        pct        = COMMISSION_RULES.get(affiliate_type.upper(), COMMISSION_RULES["DEFAULT"])
        commission = round(amount_mxn * pct / 100.0, 2)
        record = CommissionRecord(
            commission_id=  str(uuid.uuid4()),
            affiliate_id=   affiliate_id,
            affiliate_type= affiliate_type,
            invoice_id=     invoice_id,
            tenant_id=      tenant_id,
            amount_mxn=     amount_mxn,
            commission_pct= pct,
            commission_mxn= commission,
            status=         "PENDING",
            timestamp=      datetime.now(timezone.utc).isoformat(),
        )
        self._records.append(record)
        logger.info(
            "[COMMISSION] affiliate=%s pct=%.0f%% amount=%.2f",
            affiliate_id, pct, commission,
        )
        return record

    def get_pending(self, affiliate_id: Optional[str] = None) -> List[CommissionRecord]:
        records = [r for r in self._records if r.status == "PENDING"]
        if affiliate_id:
            records = [r for r in records if r.affiliate_id == affiliate_id]
        return records

    def get_total_pending(self, affiliate_id: str) -> float:
        return sum(r.commission_mxn for r in self.get_pending(affiliate_id))


commission_engine = CommissionEngine()