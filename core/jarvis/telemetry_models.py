# core/jarvis/telemetry_models.py -- MESAN Omega Telemetry Models v1.0
"""
Modelo unico de evento para toda la telemetria de Guardian.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class TelemetryEvent:
    timestamp: str = ""
    service: str = ""
    severity: str = "INFO"
    message: str = ""
    latency: float = 0.0
    status: str = "OK"
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "service": self.service,
            "severity": self.severity,
            "message": self.message,
            "latency": self.latency,
            "status": self.status,
            "source": self.source,
            "metadata": self.metadata,
        }