# core/circuit_breaker.py -- MESAN Omega v1.2 Enterprise
"""
Circuit Breaker de grado producción para MESAN Ω.

Diseñado para operar en:
- FastAPI (async, múltiples workers)
- Celery (workers concurrentes)
- Integración directa con engines MESAN Ω

Estados: CLOSED → OPEN → HALF_OPEN → CLOSED
"""

import time
import logging
import threading
from enum import Enum
from typing import Callable, Any, Optional

logger = logging.getLogger("mesan.circuit_breaker")


# ── Estados ───────────────────────────────────────────────────────────────────

class CircuitState(str, Enum):
    CLOSED    = "CLOSED"      # Operación normal
    OPEN      = "OPEN"        # Fallo activo — rechaza llamadas
    HALF_OPEN = "HALF_OPEN"   # Probando recuperación


# ── Excepción ─────────────────────────────────────────────────────────────────

class CircuitBreakerError(Exception):
    """Se lanza cuando el circuito está OPEN y bloquea la llamada."""
    def __init__(self, name: str, state: CircuitState):
        self.name  = name
        self.state = state
        super().__init__(f"CircuitBreaker '{name}' está {state.value} — llamada bloqueada")


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Circuit Breaker thread-safe para motores MESAN Ω.

    Parámetros:
        name               : Identificador del motor protegido
        failure_threshold  : Fallos consecutivos para abrir el circuito
        recovery_timeout   : Segundos en OPEN antes de intentar HALF_OPEN
        success_threshold  : Éxitos consecutivos en HALF_OPEN para cerrar
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int   = 3,
        recovery_timeout:  float = 30.0,
        success_threshold: int   = 2,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold

        # Estado interno — solo mutable a través de métodos explícitos
        self._state:             CircuitState   = CircuitState.CLOSED
        self._failure_count:     int            = 0
        self._success_count:     int            = 0
        self._last_failure_time: Optional[float] = None

        # Thread safety — RLock permite reentrada desde el mismo thread
        self._lock = threading.RLock()

        # Métricas internas observables
        self._metrics = {
            "success_count": 0,
            "failure_count": 0,
            "open_events":   0,
            "close_events":  0,
        }

    # ── Lectura de estado (sin side effects) ──────────────────────────────────

    def get_state(self) -> CircuitState:
        """Retorna el estado actual. No muta nada."""
        with self._lock:
            return self._state

    def is_open(self) -> bool:
        return self.get_state() == CircuitState.OPEN

    def is_closed(self) -> bool:
        return self.get_state() == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        return self.get_state() == CircuitState.HALF_OPEN

    # ── Transición por timeout (mutación explícita) ───────────────────────────

    def _try_recovery_transition(self):
        """
        Evalúa si el circuito OPEN debe pasar a HALF_OPEN.
        Solo se llama desde call() — mutación explícita bajo lock.
        """
        if self._state != CircuitState.OPEN:
            return
        if not self._last_failure_time:
            return
        elapsed = time.time() - self._last_failure_time
        if elapsed >= self.recovery_timeout:
            logger.info("[CB:%s] OPEN → HALF_OPEN (elapsed=%.1fs)", self.name, elapsed)
            self._state         = CircuitState.HALF_OPEN
            self._success_count = 0

    # ── Ejecución protegida ───────────────────────────────────────────────────

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta func bajo protección del circuit breaker.
        Lanza CircuitBreakerError si el circuito está OPEN
        y el timeout de recuperación aún no se cumplió.
        """
        with self._lock:
            self._try_recovery_transition()
            if self._state == CircuitState.OPEN:
                logger.warning("[CB:%s] Llamada bloqueada — circuito OPEN", self.name)
                raise CircuitBreakerError(self.name, self._state)

        # Ejecución fuera del lock para no bloquear otros threads
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except CircuitBreakerError:
            raise  # Re-lanzar sin registrar como fallo del motor

        except Exception as exc:
            self._record_failure(exc)
            raise

    # ── Registro de éxito (mutación explícita) ────────────────────────────────

    def _record_success(self):
        with self._lock:
            self._metrics["success_count"] += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    "[CB:%s] Éxito en HALF_OPEN (%d/%d)",
                    self.name, self._success_count, self.success_threshold,
                )
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
            else:
                # CLOSED: resetear contador de fallos en racha positiva
                self._failure_count = 0

    # ── Registro de fallo (mutación explícita) ────────────────────────────────

    def _record_failure(self, exc: Exception):
        with self._lock:
            self._metrics["failure_count"] += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning("[CB:%s] Fallo en HALF_OPEN → OPEN: %s", self.name, exc)
                self._transition_to_open()
                return

            self._failure_count += 1
            logger.warning(
                "[CB:%s] Fallo %d/%d: %s",
                self.name, self._failure_count, self.failure_threshold, exc,
            )
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()

    # ── Transiciones de estado (mutación explícita, siempre bajo lock) ────────

    def _transition_to_open(self):
        self._state = CircuitState.OPEN
        self._metrics["open_events"] += 1
        logger.error("[CB:%s] → OPEN (motor en fallo)", self.name)

    def _transition_to_closed(self):
        self._state         = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._metrics["close_events"] += 1
        logger.info("[CB:%s] → CLOSED (motor recuperado)", self.name)

    # ── Reset manual ──────────────────────────────────────────────────────────

    def reset(self):
        """Reset manual del circuito. Útil en reinicio de motor o tests."""
        with self._lock:
            prev = self._state
            self._state             = CircuitState.CLOSED
            self._failure_count     = 0
            self._success_count     = 0
            self._last_failure_time = None
            logger.info("[CB:%s] Reset manual desde %s → CLOSED", self.name, prev.value)

    # ── Observabilidad ────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Snapshot del estado actual. Lectura pura — no muta."""
        with self._lock:
            return {
                "name":              self.name,
                "state":             self._state.value,
                "failure_count":     self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout":  self.recovery_timeout,
                "success_threshold": self.success_threshold,
                "last_failure_at":   self._last_failure_time,
                "metrics":           dict(self._metrics),
            }

    def __repr__(self) -> str:
        return f"<CircuitBreaker name={self.name!r} state={self._state.value}>"


# ── Registry ──────────────────────────────────────────────────────────────────

class CircuitBreakerRegistry:
    """
    Registro centralizado de circuit breakers por motor MESAN Ω.

    Uso en engines:
        from core.circuit_breaker import circuit_registry
        cb = circuit_registry.get_or_create("FiscalSentinel")
        cb.call(mi_funcion, arg1, arg2)
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()

    def get_or_create(
        self,
        name: str,
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


# ── Instancia global ──────────────────────────────────────────────────────────
circuit_registry = CircuitBreakerRegistry()
