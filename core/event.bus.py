# core/event_bus.py -- MESAN Omega Enterprise Event Bus v1.1
from dataclasses import dataclass, field
from typing import Dict, Callable, List, Any, Optional
from datetime import datetime
import uuid, logging, traceback, time

logger = logging.getLogger("mesan.event_bus")

@dataclass
class Event:
    event_id: str; event_type: str; tenant_id: str; trace_id: str
    source: str; timestamp: str
    payload: Dict[str,Any] = field(default_factory=dict)
    metadata: Dict[str,Any] = field(default_factory=dict)

@dataclass
class EventExecution:
    handler: str; success: bool; duration_ms: float
    error: Optional[str] = None

class EventBus:
    VERSION = "1.1.0"

    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}
        self._history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable):
        self.listeners.setdefault(event_type, []).append(handler)
        logger.info(f"[EVENT_BUS] Subscribed | event={event_type} | handler={handler.__name__}")

    def publish(self, event_type: str, payload: Dict[str,Any], tenant_id: str = "DEFAULT",
                trace_id: Optional[str] = None, source: str = "UNKNOWN",
                metadata: Optional[Dict[str,Any]] = None) -> dict:

        event = Event(event_id=str(uuid.uuid4()), event_type=event_type,
                      tenant_id=tenant_id, trace_id=trace_id or str(uuid.uuid4()),
                      source=source, timestamp=datetime.utcnow().isoformat(),
                      payload=payload, metadata=metadata or {})
        self._history.append(event)

        handlers = self.listeners.get(event_type, [])
        executions = []

        logger.info(f"[EVENT_BUS] Publishing | type={event_type} | handlers={len(handlers)}")

        for handler in handlers:
            t0 = time.perf_counter()
            try:
                handler(event)
                ms = round((time.perf_counter()-t0)*1000, 2)
                executions.append(EventExecution(handler.__name__, True, ms))
            except Exception as e:
                ms = round((time.perf_counter()-t0)*1000, 2)
                logger.error(f"[EVENT_BUS] Handler failed | {handler.__name__} | {e}")
                logger.debug(traceback.format_exc())
                executions.append(EventExecution(handler.__name__, False, ms, str(e)))

        return {"event_id": event.event_id, "event_type": event_type,
                "tenant_id": tenant_id, "trace_id": event.trace_id,
                "handlers_executed": len(executions),
                "success": all(e.success for e in executions) if executions else True,
                "executions": executions}

    def get_history(self, tenant_id=None, trace_id=None, event_type=None) -> List[Event]:
        h = self._history
        if tenant_id:   h = [e for e in h if e.tenant_id == tenant_id]
        if trace_id:    h = [e for e in h if e.trace_id == trace_id]
        if event_type:  h = [e for e in h if e.event_type == event_type]
        return h

    def health(self) -> dict:
        return {"status": "HEALTHY", "version": self.VERSION,
                "registered_event_types": list(self.listeners.keys()),
                "total_events": len(self._history),
                "timestamp": datetime.utcnow().isoformat()}

    def clear_history(self):
        self._history.clear()
        logger.warning("[EVENT_BUS] History cleared")
