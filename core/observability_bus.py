# core/observability_bus.py -- MESAN Omega v1.5
"""
Observability Bus Ω — Sistema central de inteligencia operacional.

v1.5 — Fixes post-review ChatGPT (segunda ronda):
- _iso_now() usa una sola llamada datetime.now() — elimina inconsistencia de ms
- _record_history() protegido con _history_lock
- get_event_history() snapshot bajo _history_lock
- Event.to_dict() usa datetime derivado de self.timestamp (sin código muerto)
- complete_trace() con try/finally — trace siempre archivado aunque emit() falle
- attach_circuit_breaker() idempotente — _attached_breakers evita listeners duplicados
- API pública compatible: emit(), subscribe(), unsubscribe(), snapshot(), status()
"""

import time
import threading
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.logger import trace_context, tenant_context, engine_context

logger = logging.getLogger("mesan.observability_bus")


# ══════════════════════════════════════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    ENGINE_STARTED    = "ENGINE_STARTED"
    ENGINE_SUCCESS    = "ENGINE_SUCCESS"
    ENGINE_FAILURE    = "ENGINE_FAILURE"
    CIRCUIT_OPENED    = "CIRCUIT_OPENED"
    CIRCUIT_CLOSED    = "CIRCUIT_CLOSED"
    CIRCUIT_HALF_OPEN = "CIRCUIT_HALF_OPEN"
    TRACE_CREATED     = "TRACE_CREATED"
    TRACE_COMPLETED   = "TRACE_COMPLETED"
    AUDIT_EVENT       = "AUDIT_EVENT"
    METRIC_THRESHOLD  = "METRIC_THRESHOLD"


def _iso_now() -> str:
    """
    Timestamp ISO 8601 UTC verificable. Ejemplo: 2026-06-04T18:32:01.342Z
    FIX v1.4: una sola llamada a datetime.now() — elimina inconsistencia de ms.
    """
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass
class Event:
    type:       EventType
    engine:     str
    tenant:     str                 = "global"
    trace_id:   Optional[str]       = None
    timestamp:  float               = field(default_factory=time.time)
    payload:    Dict[str, Any]      = field(default_factory=dict)
    latency_ms: Optional[float]     = None

    def to_dict(self) -> dict:
        # FIX v1.5: usa datetime derivado de self.timestamp — consistente y sin código muerto
        dt  = datetime.fromtimestamp(self.timestamp, tz=timezone.utc)
        iso = dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
        return {
            "type":          self.type.value,
            "engine":        self.engine,
            "tenant":        self.tenant,
            "trace_id":      self.trace_id,
            "timestamp":     self.timestamp,
            "timestamp_iso": iso,
            "payload":       self.payload,
            "latency_ms":    self.latency_ms,
        }


# ══════════════════════════════════════════════════════════════════════════════
# METRICS COLLECTOR
# ══════════════════════════════════════════════════════════════════════════════

class MetricsCollector:

    def __init__(self):
        self._data: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(
            lambda: defaultdict(lambda: {
                "request_count":      0,
                "success_count":      0,
                "failure_count":      0,
                "circuit_open_count": 0,
                "circuit_half_count": 0,
                "total_latency_ms":   0.0,
                "last_failure_at":    None,
            })
        )
        self._lock = threading.RLock()

    def _get(self, tenant: str, engine: str) -> dict:
        return self._data[tenant][engine]

    def record_success(self, engine: str, tenant: str, latency_ms: float = 0.0):
        with self._lock:
            m = self._get(tenant, engine)
            m["request_count"]    += 1
            m["success_count"]    += 1
            m["total_latency_ms"] += latency_ms

    def record_failure(self, engine: str, tenant: str, latency_ms: float = 0.0):
        with self._lock:
            m = self._get(tenant, engine)
            m["request_count"]    += 1
            m["failure_count"]    += 1
            m["total_latency_ms"] += latency_ms
            m["last_failure_at"]   = time.time()

    def record_circuit_open(self, engine: str, tenant: str):
        with self._lock:
            self._get(tenant, engine)["circuit_open_count"] += 1

    def record_circuit_half(self, engine: str, tenant: str):
        with self._lock:
            self._get(tenant, engine)["circuit_half_count"] += 1

    def success_ratio(self, engine: str, tenant: str = "global") -> float:
        with self._lock:
            m     = self._get(tenant, engine)
            total = m["request_count"]
            return round(m["success_count"] / total, 4) if total else 1.0

    def avg_latency_ms(self, engine: str, tenant: str = "global") -> float:
        with self._lock:
            m     = self._get(tenant, engine)
            total = m["request_count"]
            return round(m["total_latency_ms"] / total, 2) if total else 0.0

    def snapshot(self, tenant: str = "global") -> dict:
        with self._lock:
            result = {}
            for engine, metrics in self._data[tenant].items():
                total = metrics["request_count"]
                result[engine] = {
                    **metrics,
                    "success_ratio":  round(metrics["success_count"] / total, 4) if total else 1.0,
                    "avg_latency_ms": round(metrics["total_latency_ms"] / total, 2) if total else 0.0,
                }
            return result

    def all_tenants_snapshot(self) -> dict:
        with self._lock:
            return {tenant: self.snapshot(tenant) for tenant in self._data}


# ══════════════════════════════════════════════════════════════════════════════
# TRACE CORRELATOR
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TraceSpan:
    event_type: str
    engine:     str
    timestamp:  float
    payload:    Dict[str, Any] = field(default_factory=dict)
    latency_ms: Optional[float] = None


class TraceCorrelator:

    def __init__(
        self,
        max_active_traces: int   = 500,
        trace_ttl_seconds: float = 300.0,
        max_completed:     int   = 1000,
    ):
        self._traces:    Dict[str, List[TraceSpan]] = {}
        self._started:   Dict[str, float]           = {}
        self._completed: Dict[str, List[TraceSpan]] = {}
        self._lock           = threading.RLock()
        self._max_active     = max_active_traces
        self._ttl            = trace_ttl_seconds
        self._max_completed  = max_completed

    def record(self, event: Event):
        if not event.trace_id:
            return
        with self._lock:
            self._purge_expired()
            if event.trace_id not in self._traces:
                if len(self._traces) >= self._max_active:
                    oldest = min(self._started, key=self._started.get)
                    logger.warning("[TraceCorrelator] Purgando trace activo más antiguo: %s", oldest)
                    self._traces.pop(oldest, None)
                    self._started.pop(oldest, None)
                self._traces[event.trace_id]  = []
                self._started[event.trace_id] = time.time()

            self._traces[event.trace_id].append(TraceSpan(
                event_type = event.type.value,
                engine     = event.engine,
                timestamp  = event.timestamp,
                payload    = event.payload,
                latency_ms = event.latency_ms,
            ))

    def complete(self, trace_id: str):
        with self._lock:
            if trace_id not in self._traces:
                return
            self._completed[trace_id] = self._traces.pop(trace_id)
            self._started.pop(trace_id, None)
            if len(self._completed) > self._max_completed:
                oldest = next(iter(self._completed))
                del self._completed[oldest]

    def _purge_expired(self):
        now     = time.time()
        expired = [tid for tid, t in self._started.items() if (now - t) > self._ttl]
        for tid in expired:
            logger.warning("[TraceCorrelator] Trace huérfano purgado (TTL=%.0fs): %s", self._ttl, tid)
            self._traces.pop(tid, None)
            self._started.pop(tid, None)

    def get_trace(self, trace_id: str) -> Optional[List[dict]]:
        with self._lock:
            spans = self._traces.get(trace_id) or self._completed.get(trace_id)
            if not spans:
                return None
            return [
                {
                    "event_type": s.event_type,
                    "engine":     s.engine,
                    "timestamp":  s.timestamp,
                    "latency_ms": s.latency_ms,
                    "payload":    s.payload,
                }
                for s in spans
            ]

    def active_count(self)    -> int:
        with self._lock: return len(self._traces)

    def completed_count(self) -> int:
        with self._lock: return len(self._completed)


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH SCORE
# ══════════════════════════════════════════════════════════════════════════════

def compute_health_score(
    success_ratio:         float,
    avg_latency_ms:        float,
    circuit_open_count:    int,
    failure_count:         int,
    last_failure_at:       Optional[float],
    latency_threshold:     float = 500.0,
    recent_failure_window: float = 300.0,
) -> int:
    score = round(success_ratio * 100)
    if circuit_open_count > 0:    score -= 15
    if avg_latency_ms > latency_threshold: score -= 10
    if last_failure_at and (time.time() - last_failure_at) < recent_failure_window:
        score -= 10
    if success_ratio < 0.90:      score -= 5
    return max(0, min(100, score))


# ══════════════════════════════════════════════════════════════════════════════
# OBSERVABILITY BUS
# ══════════════════════════════════════════════════════════════════════════════

Handler = Callable[[Event], None]


class ObservabilityBus:

    def __init__(self, event_history_size: int = 10_000):
        self._handlers:   Dict[EventType, List[Handler]] = defaultdict(list)
        self._pre_hooks:  List[Callable] = []
        self._post_hooks: List[Callable] = []
        self._lock        = threading.RLock()

        self.metrics = MetricsCollector()
        self.traces  = TraceCorrelator()

        # Buffer circular — no crece indefinidamente
        self._event_history: deque = deque(maxlen=event_history_size)

        # Métricas del historial — contadores ligeros
        self._history_counters: Dict[str, int] = defaultdict(int)   # por tipo
        self._history_by_engine: Dict[str, int] = defaultdict(int)  # por engine
        self._history_total: int = 0
        self._history_lock = threading.RLock()

        # FIX v1.5: registro de circuit breakers adjuntos — evita listeners duplicados
        self._attached_breakers: set = set()  # { id(circuit_breaker) }

    # ── Listener nativo para CircuitBreaker ───────────────────────────────────

    def make_circuit_listener(self):
        bus = self

        def circuit_listener(cb, circuit_event, payload: dict):
            from core.circuit_breaker import CircuitEvent
            event_map = {
                CircuitEvent.OPENED:    EventType.CIRCUIT_OPENED,
                CircuitEvent.CLOSED:    EventType.CIRCUIT_CLOSED,
                CircuitEvent.HALF_OPEN: EventType.CIRCUIT_HALF_OPEN,
            }
            bus_event_type = event_map.get(circuit_event)
            if bus_event_type:
                bus.emit(event_type=bus_event_type, engine=cb.name, payload=payload)

        circuit_listener.__name__ = f"circuit_listener_bus_{id(self)}"
        return circuit_listener

    def attach_circuit_breaker(self, circuit_breaker) -> None:
        """
        Conecta CircuitBreaker al bus via listener nativo. Sin monkey patching.
        FIX v1.5: idempotente — ignora si el mismo CircuitBreaker ya fue adjuntado,
        evitando listeners duplicados y eventos duplicados en OPEN/CLOSE/HALF_OPEN.
        """
        cb_id = id(circuit_breaker)
        with self._lock:
            if cb_id in self._attached_breakers:
                logger.warning(
                    "[Bus] CircuitBreaker '%s' ya adjuntado — ignorando duplicado",
                    circuit_breaker.name,
                )
                return
            self._attached_breakers.add(cb_id)

        listener = self.make_circuit_listener()
        circuit_breaker.add_listener(listener)
        logger.info("[Bus] CircuitBreaker '%s' conectado via listener nativo", circuit_breaker.name)

    # ── Hooks globales ────────────────────────────────────────────────────────

    def add_pre_hook(self, hook: Callable[[Event], None]):
        with self._lock:
            self._pre_hooks.append(hook)

    def add_post_hook(self, hook: Callable[[Event], None]):
        with self._lock:
            self._post_hooks.append(hook)

    # ── Suscripción ───────────────────────────────────────────────────────────

    def subscribe(self, event_type: EventType, handler: Handler):
        with self._lock:
            self._handlers[event_type].append(handler)
            logger.debug("[Bus] Suscrito: %s → %s", event_type.value, handler.__name__)

    def unsubscribe(self, event_type: EventType, handler: Handler):
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    # ── Emisión ───────────────────────────────────────────────────────────────

    def emit(
        self,
        event_type:  EventType,
        engine:      str,
        tenant:      Optional[str]   = None,
        trace_id:    Optional[str]   = None,
        payload:     Optional[dict]  = None,
        latency_ms:  Optional[float] = None,
    ) -> Event:
        if not engine or not engine.strip():
            raise ValueError("emit() requiere engine válido")

        event = Event(
            type       = event_type,
            engine     = engine.strip(),
            tenant     = tenant   or tenant_context.get() or "global",
            trace_id   = trace_id or trace_context.get(),
            payload    = payload  or {},
            latency_ms = latency_ms,
        )

        self._run_pre_hooks(event)
        self._update_metrics(event)
        self.traces.record(event)
        self._record_history(event)
        self._dispatch(event)
        self._run_post_hooks(event)

        return event

    def emit_from_context(
        self,
        event_type: EventType,
        payload:    Optional[dict]  = None,
        latency_ms: Optional[float] = None,
    ) -> Event:
        engine = engine_context.get() or "unknown"
        return self.emit(event_type=event_type, engine=engine,
                         payload=payload, latency_ms=latency_ms)

    # ── Pipeline ──────────────────────────────────────────────────────────────

    def _run_pre_hooks(self, event: Event):
        with self._lock:
            hooks = list(self._pre_hooks)
        for hook in hooks:
            try:   hook(event)
            except Exception as exc: logger.error("[Bus] pre_hook error: %s", exc)

    def _run_post_hooks(self, event: Event):
        with self._lock:
            hooks = list(self._post_hooks)
        for hook in hooks:
            try:   hook(event)
            except Exception as exc: logger.error("[Bus] post_hook error: %s", exc)

    def _dispatch(self, event: Event):
        with self._lock:
            handlers = list(self._handlers.get(event.type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error("[Bus] Handler error %s → %s: %s",
                             handler.__name__, event.type.value, exc)

    def _update_metrics(self, event: Event):
        t, e, ms = event.tenant, event.engine, event.latency_ms or 0.0
        if event.type == EventType.ENGINE_SUCCESS:
            self.metrics.record_success(e, t, ms)
        elif event.type == EventType.ENGINE_FAILURE:
            self.metrics.record_failure(e, t, ms)
        elif event.type == EventType.CIRCUIT_OPENED:
            self.metrics.record_circuit_open(e, t)
        elif event.type == EventType.CIRCUIT_HALF_OPEN:
            self.metrics.record_circuit_half(e, t)

    def _record_history(self, event: Event):
        """
        Agrega evento al buffer circular con timestamp ISO verificable.
        FIX v1.4: append y contadores bajo un mismo lock — consistencia garantizada
        frente a lecturas concurrentes en get_event_history() y history_metrics().
        """
        entry = event.to_dict()
        with self._history_lock:
            self._event_history.append(entry)
            self._history_total += 1
            self._history_counters[event.type.value] += 1
            self._history_by_engine[event.engine]    += 1

    # ── Trace lifecycle ───────────────────────────────────────────────────────

    def start_trace(self, trace_id: str, engine: str, tenant: str = "global"):
        self.emit(EventType.TRACE_CREATED, engine=engine, tenant=tenant,
                  trace_id=trace_id, payload={"started_at": time.time()})

    def complete_trace(self, trace_id: str, engine: str, tenant: str = "global"):
        # FIX v1.5: try/finally garantiza archivado del trace aunque emit() falle
        try:
            self.emit(EventType.TRACE_COMPLETED, engine=engine, tenant=tenant,
                      trace_id=trace_id, payload={"completed_at": time.time()})
        finally:
            self.traces.complete(trace_id)

    # ── Event History ─────────────────────────────────────────────────────────

    def get_event_history(
        self,
        limit:      int           = 100,
        engine:     Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[dict]:
        """
        Retorna eventos del buffer circular.
        FIX v1.4: snapshot bajo _history_lock — consistencia garantizada
        frente a appends concurrentes.
        Cada evento incluye timestamp_iso (ISO 8601 UTC verificable).
        Orden: más reciente primero.
        """
        with self._history_lock:
            history = list(self._event_history)
        if engine:
            history = [e for e in history if e.get("engine") == engine]
        if event_type:
            history = [e for e in history if e.get("type") == event_type]
        return list(reversed(history))[:limit]

    def history_metrics(self) -> dict:
        """
        Métricas básicas del historial en memoria.

        Retorna:
            {
                "total_events":   1842,
                "by_type":  { "ENGINE_SUCCESS": 1200, "ENGINE_FAILURE": 42, ... },
                "by_engine": { "FiscalSentinel": 300, "Governance": 200, ... },
                "buffer_capacity": 10000,
                "buffer_used":     1842
            }
        """
        with self._history_lock:
            return {
                "total_events":    self._history_total,
                "by_type":         dict(self._history_counters),
                "by_engine":       dict(self._history_by_engine),
                "buffer_capacity": self._event_history.maxlen,
                "buffer_used":     len(self._event_history),
            }

    # ── Health Score ──────────────────────────────────────────────────────────

    def health_scores(self, tenant: str = "global") -> Dict[str, dict]:
        metrics = self.metrics.snapshot(tenant)
        result  = {}
        for engine, m in metrics.items():
            score = compute_health_score(
                success_ratio      = m.get("success_ratio",      1.0),
                avg_latency_ms     = m.get("avg_latency_ms",     0.0),
                circuit_open_count = m.get("circuit_open_count", 0),
                failure_count      = m.get("failure_count",      0),
                last_failure_at    = m.get("last_failure_at"),
            )
            result[engine] = {
                "health_score":   score,
                "success_ratio":  m.get("success_ratio",  1.0),
                "avg_latency_ms": m.get("avg_latency_ms", 0.0),
                "failure_count":  m.get("failure_count",  0),
            }
        return result

    def system_health(self, tenant: str = "global") -> int:
        scores = self.health_scores(tenant)
        if not scores:
            return 100
        return round(sum(v["health_score"] for v in scores.values()) / len(scores))

    # ── Status y Snapshot ─────────────────────────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            return {
                "subscriptions": {
                    k.value: len(v)
                    for k, v in self._handlers.items() if v
                },
                "active_traces":    self.traces.active_count(),
                "completed_traces": self.traces.completed_count(),
                "pre_hooks":        len(self._pre_hooks),
                "post_hooks":       len(self._post_hooks),
                "event_history":    self.history_metrics(),   # NUEVO v1.3
            }

    def snapshot(self, tenant: str = "global") -> dict:
        return {
            "bus":            self.status(),
            "metrics":        self.metrics.snapshot(tenant),
            "health_scores":  self.health_scores(tenant),
        }


# ══════════════════════════════════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════════════════════════════════

omega_bus = ObservabilityBus()
