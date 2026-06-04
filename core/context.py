# core/context.py -- MESAN Omega Request Context v2.1
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True, slots=True)
class RequestContext:
    """
    Contexto inmutable por request — MESAN Ω v2.1
    Thread-safe, observable, compatible con FastAPI middleware.
    """
    tenant_id:      str
    request_id:     str
    user_id:        str | None = None
    role:           str | None = None
    correlation_id: str | None = None
    created_at:     datetime   = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not self.tenant_id:
            raise ValueError("tenant_id cannot be empty")
        if not self.request_id:
            raise ValueError("request_id cannot be empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant_id":      self.tenant_id,
            "request_id":     self.request_id,
            "user_id":        self.user_id,
            "role":           self.role,
            "correlation_id": self.correlation_id,
            "created_at":     self.created_at.isoformat(),
        }

    def audit_key(self) -> str:
        return f"{self.tenant_id}:{self.request_id}"
