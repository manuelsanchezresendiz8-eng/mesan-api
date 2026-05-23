# core/tenant_context.py -- MESAN Omega Enterprise Tenant Context v1.1
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class TenantContext:
    tenant_id:  str
    trace_id:   str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id:    Optional[str] = None
    role:       str = "SYSTEM"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata:   Dict[str, Any] = field(default_factory=dict)

    VERSION = "1.1.0"

    def scope(self, data: dict) -> dict:
        return {**data, "tenant_id": self.tenant_id,
                "trace_id": self.trace_id, "request_id": self.request_id}

    def audit_payload(self, module: str, action: str, status: str = "SUCCESS") -> dict:
        return {"timestamp": datetime.utcnow().isoformat(), "tenant_id": self.tenant_id,
                "trace_id": self.trace_id, "request_id": self.request_id,
                "user_id": self.user_id, "role": self.role,
                "module": module, "action": action, "status": status}

    def to_dict(self) -> dict:
        return {"tenant_id": self.tenant_id, "trace_id": self.trace_id,
                "request_id": self.request_id, "user_id": self.user_id,
                "role": self.role, "created_at": self.created_at, "metadata": self.metadata}

    def clone(self, new_trace: bool = False):
        return TenantContext(tenant_id=self.tenant_id,
                             trace_id=str(uuid.uuid4()) if new_trace else self.trace_id,
                             user_id=self.user_id, role=self.role, metadata=dict(self.metadata))

    def health(self) -> dict:
        return {"status": "HEALTHY", "tenant_id": self.tenant_id,
                "version": self.VERSION, "timestamp": datetime.utcnow().isoformat()}
