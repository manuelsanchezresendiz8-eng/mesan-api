# core/circuit_breaker.py -- MESAN Omega v2.1
"""
Circuit Breaker enterprise para MESAN Ω.

v2.1 — Merge Fase 1:
- listener_count agregado a status()
- API pública compatible: call(), reset(), status()
- Arquitectura de listeners nativa (sin monkey patching)
- Eventos: OPEN, HALF_OPEN, CLOSED
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Dict, List, Optional

logger = logging.getLogger("mesan.circuit_breaker")


# ══════════════════════════════════════════════════════════════════════════════
# ESTADOS Y EVENTOS
# ══════════════════════════════════════════════════════════════════════════════

class CircuitState(str, Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitEvent(str, Enum):
    OPENED    = "OPEN"
    CLOSED    = "CLOSED"
    HALF_OPEN = "HALF_OPEN"


# ══════════════════════════════════════════════════════════════════════════════
# EXCEPCIÓN
# ══════════════════════════════════════════════════════════════════════════════

class CircuitBreakerError(Exception):
    def __init__(self, name: str, state: CircuitState):
        self.name  = name
        self.state = state
        super().__init__(f"CircuitBreaker '{name}' está {state.value} — llamada bloqueada")


# ══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ══════════════════════════════════════════════════════════════════════════════

CircuitListener = Callable[["CircuitBreaker", CircuitEvent, dict], None]


class CircuitBreaker:
    """
    Circuit Breaker thread-safe con listener nativo.

    Firma de listener:
        def handler(cb: CircuitBreaker, event: CircuitEvent, payload: dict): ...
    """

    def __init__(
        self,
        name:              str,
        failure_threshold: int   = 3,
        recovery_timeout:  float = 30.0,
        success_threshold: int   = 2,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold

        self._state:             CircuitState    = CircuitState.CLOSED
        self._failure_count:     int             = 0
        self._success_count:     int             = 0
        self._last_failure_time: Optional[float] = None

        self._lock      = threading.RLock()
        self._listeners: List[CircuitListener] = []

        self._metrics = {
            "success_count": 0,
            "failure_count": 0,
            "open_events":   0,
            "close_events":  0,
            "half_events":   0,
        }

    # ── Listener API ──────────────────────────────────────────────────────────

    def add_listener(self, listener: CircuitListener):
        with self._lock:
            self._listeners.append(listener)
            logger.debug("[CB:%s] Listener registrado: %s", self.name, listener.__name__)

    def remove_listener(self, listener: CircuitListener):
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def _notify(self, event: CircuitEvent, payload: dict):
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(self, event, payload)
            except Exception as exc:
                logger.error("[CB:%s] Error en listener %s: %s",
                             self.name, listener.__name__, exc)

    # ── Lectura de estado ─────────────────────────────────────────────────────

    def get_state(self) -> CircuitState:
        with self._lock:
            return self._state

    def is_open(self)      -> bool: return self.get_state() == CircuitState.OPEN
    def is_closed(self)    -> bool: return self.get_state() == CircuitState.CLOSED
    def is_half_open(self) -> bool: return self.get_state() == CircuitState.HALF_OPEN

    # ── Transición por timeout ────────────────────────────────────────────────

    def _try_recovery_transition(self):
        if self._state != CircuitState.OPEN:
            return
        if not self._last_failure_time:
            return
        elapsed = time.time() - self._last_failure_time
        if elapsed >= self.recovery_timeout:
            logger.info("[CB:%s] OPEN → HALF_OPEN (elapsed=%.1fs)", self.name, elapsed)
            self._state         = CircuitState.HALF_OPEN
            self._success_count = 0
            self._metrics["half_events"] += 1
            self._pending_notify = (CircuitEvent.HALF_OPEN, {"elapsed_seconds": elapsed})

    # ── Ejecución protegida ───────────────────────────────────────────────────

    def call(self, func: Callable, *args, **kwargs) -> Any:
        self._pending_notify = None
        with self._lock:
            self._try_recovery_transition()
            if self._state == CircuitState.OPEN:
                logger.warning("[CB:%s] Llamada bloqueada — OPEN", self.name)
                raise CircuitBreakerError(self.name, self._state)

        if self._pending_notify:
            self._notify(*self._pending_notify)
            self._pending_notify = None

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except CircuitBreakerError:
            raise
        except Exception as exc:
            self._record_failure(exc)
            raise

    # ── Éxito / Fallo ─────────────────────────────────────────────────────────

    def _record_success(self):
        notify = None
        with self._lock:
            self._metrics["success_count"] += 1
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info("[CB:%s] Éxito HALF_OPEN (%d/%d)",
                            self.name, self._success_count, self.success_threshold)
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
                    notify = (CircuitEvent.CLOSED, {"recovered": True})
            else:
                self._failure_count = 0
        if notify:
            self._notify(*notify)

    def _record_failure(self, exc: Exception):
        notify = None
        with self._lock:
            self._metrics["failure_count"] += 1
            self._last_failure_time = time.time()
            if self._state == CircuitState.HALF_OPEN:
                logger.warning("[CB:%s] Fallo HALF_OPEN → OPEN: %s", self.name, exc)
                self._transition_to_open()
                notify = (CircuitEvent.OPENED, {
                    "reason": "half_open_failure", "error": str(exc),
                    "failure_count": self._failure_count,
                })
            else:
                self._failure_count += 1
                logger.warning("[CB:%s] Fallo %d/%d: %s",
                               self.name, self._failure_count, self.failure_threshold, exc)
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
                    notify = (CircuitEvent.OPENED, {
                        "reason": "threshold_reached", "error": str(exc),
                        "failure_count": self._failure_count,
                    })
        if notify:
            self._notify(*notify)

    # ── Transiciones ──────────────────────────────────────────────────────────

    def _transition_to_open(self):
        self._state = CircuitState.OPEN
        self._metrics["open_events"] += 1
        logger.error("[CB:%s] → OPEN", self.name)

    def _transition_to_closed(self):
        self._state         = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._metrics["close_events"] += 1
        logger.info("[CB:%s] → CLOSED (recuperado)", self.name)

    # ── Reset ─────────────────────────────────────────────────────────────────

    def reset(self):
        with self._lock:
            prev = self._state
            self._state             = CircuitState.CLOSED
            self._failure_count     = 0
            self._success_count     = 0
            self._last_failure_time = None
            logger.info("[CB:%s] Reset: %s → CLOSED", self.name, prev.value)

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> dict:
        with self._lock:
            return {
                "name":              self.name,
                "state":             self._state.value,
                "failure_count":     self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout":  self.recovery_timeout,
                "success_threshold": self.success_threshold,
                "last_failure_at":   self._last_failure_time,
                "listener_count":    len(self._listeners),   # NUEVO v2.1
                "metrics":           dict(self._metrics),
            }

    def __repr__(self) -> str:
        return f"<CircuitBreaker name={self.name!r} state={self._state.value}>"


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

class CircuitBreakerRegistry:

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_or_create(
        self,
        name:              str,
        failure_threshold: int   = 3,
        recovery_timeout:  float = 30.0,
        success_threshold: int   = 2,
    ) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    success_threshold=success_threshold,
                )
                logger.debug("[CBRegistry] Registrado: %s", name)
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        with self._lock:
            return self._breakers.get(name)

    def reset_all(self):
        with self._lock:
            for cb in self._breakers.values():
                cb.reset()
            logger.info("[CBRegistry] Reset global completado")

    def all_status(self) -> dict:
        with self._lock:
            return {name: cb.status() for name, cb in self._breakers.items()}

    def open_count(self) -> int:
        with self._lock:
            return sum(1 for cb in self._breakers.values() if cb.is_open())


circuit_registry = CircuitBreakerRegistry()
