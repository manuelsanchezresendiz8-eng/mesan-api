# core/auth/tenant_model.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

PlanType = Literal["FREE", "PRO", "ENTERPRISE"]

@dataclass(frozen=True)
class Tenant:
    tenant_id:  str      = field(default_factory=lambda: str(uuid4()))
    name:       str      = ""
    plan:       PlanType = "FREE"
    active:     bool     = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
