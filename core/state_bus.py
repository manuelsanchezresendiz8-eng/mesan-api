# core/state_bus.py -- MESAN Omega Unified State Bus v1.1
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from threading import RLock
import uuid, copy

@dataclass
class StateEvent:
    event_id: str; tenant_id: str; trace_id: str; timestamp: str
    source_engine: str; event_type: str
    before_state: Dict[str,Any]; after_state: Dict[str,Any]; diff: Dict[str,Any]

class StateBus:
    VERSION    = "1.1.0"
    MAX_EVENTS = 100000

    def __init__(self):
        self._events: List[StateEvent] = []
        self._lock = RLock()

    def _validate_event(self, tenant_id, trace_id, source_engine, event_type):
        if not tenant_id:    raise ValueError("tenant_id requerido.")
        if not trace_id:     raise ValueError("trace_id requerido.")
        if not source_engine:raise ValueError("source_engine requerido.")
        if not event_type:   raise ValueError("event_type requerido.")

    def _calculate_diff(self, before, after):
        diff = {}
        for key in sorted(set(before)|set(after)):
            b = before.get(key); a = after.get(key)
            if b != a: diff[key] = {"before": b, "after": a}
        return diff

    def emit(self, tenant_id, trace_id, source_engine, event_type, before_state, after_state) -> StateEvent:
        self._validate_event(tenant_id, trace_id, source_engine, event_type)
        with self._lock:
            if len(self._events) >= self.MAX_EVENTS: self._events.pop(0)
            event = StateEvent(str(uuid.uuid4()), tenant_id, trace_id,
                               datetime.utcnow().isoformat(), source_engine, event_type,
                               copy.deepcopy(before_state), copy.deepcopy(after_state),
                               self._calculate_diff(before_state, after_state))
            self._events.append(event)
            return event

    def get_tenant_history(self, tenant_id) -> List[StateEvent]:
        with self._lock:
            return sorted([e for e in self._events if e.tenant_id==tenant_id], key=lambda e: e.timestamp)

    def get_trace_history(self, trace_id) -> List[StateEvent]:
        with self._lock:
            return sorted([e for e in self._events if e.trace_id==trace_id], key=lambda e: e.timestamp)

    def rebuild_state(self, tenant_id) -> dict:
        state = {}
        for e in self.get_tenant_history(tenant_id): state.update(e.after_state)
        return copy.deepcopy(state)

    def detect_drift(self, tenant_id) -> dict:
        history = self.get_tenant_history(tenant_id)
        if len(history) < 2: return {"drift_detected": False, "reason": "Insufficient data"}
        first = history[0].after_state; last = history[-1].after_state
        drift_fields = [k for k in sorted(set(first)|set(last)) if first.get(k)!=last.get(k)]
        return {"tenant_id": tenant_id, "total_events": len(history),
                "drift_detected": len(drift_fields)>0, "drift_fields": drift_fields,
                "drift_score": round(len(drift_fields)/max(len(last.keys()),1), 3)}

    def metrics(self) -> dict:
        with self._lock:
            return {"total_events": len(self._events), "max_events": self.MAX_EVENTS, "version": self.VERSION}
