# core/auth/audit_log.py -- MESAN Omega Audit Log v1.2
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List
import hashlib, json, copy

@dataclass(frozen=True)
class AuditEvent:
    tenant_id: str; event_type: str; payload: Dict[str,Any]; timestamp: str; hash: str

class AuditLog:
    def __init__(self):
        self._chain: List[AuditEvent] = []
        self._version = "MESAN_AUDIT_V1"  # solo control interno, NO entra al hash

    def _safe_serialize(self, data: Dict[str,Any]) -> str:
        return json.dumps(data, sort_keys=True, default=str)

    def _generate_hash(self, data: dict, prev_hash: str = "") -> str:
        # version fuera del hash — mantiene integridad historica
        return hashlib.sha256((self._safe_serialize(data)+prev_hash).encode()).hexdigest()

    def log(self, tenant_id: str, event_type: str, payload: Dict[str,Any]) -> AuditEvent:
        ts = datetime.now(timezone.utc).isoformat()
        safe_payload = copy.deepcopy(payload)
        data = {"tenant_id":tenant_id,"event_type":event_type,"payload":safe_payload,"timestamp":ts}
        prev = self._chain[-1].hash if self._chain else ""
        event = AuditEvent(tenant_id=tenant_id, event_type=event_type,
                           payload=safe_payload, timestamp=ts,
                           hash=self._generate_hash(data, prev))
        self._chain.append(event)
        return event

    def get_chain(self) -> List[AuditEvent]: return list(self._chain)

    def verify_integrity(self) -> bool:
        prev = ""
        for e in self._chain:
            expected = self._generate_hash({"tenant_id":e.tenant_id,"event_type":e.event_type,
                                             "payload":e.payload,"timestamp":e.timestamp}, prev)
            if e.hash != expected: return False
            prev = e.hash
        return True

    def version(self) -> str: return self._version
