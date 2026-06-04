# core/circuit_breaker.py -- MESAN Omega Circuit Breaker v1.0
"""
Enterprise Circuit Breaker MESAN Ω
- Thread-safe via RLock
- Estados tipados (CLOSED / OPEN / HALF_OPEN)
- Half-Open single-probe control
- Métricas integradas
- Excepción específica CircuitOpenError
"""

import time
import logging
from enum import Enum
from threading import RLock
from typing import Any, Callable

logger = logging.getLogger("mesan.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    """Se lanza cuando el Circuit Breaker está OPEN."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker empresarial para engines MESAN Ω.

    Estados:
      CLOSED    → operación normal
      OPEN      → rechaza llamadas hasta que expire timeout
      HALF_OPEN → permite una sola llamada de prueba
    """

    def __init__(
        self,
        name:      str,
        threshold: int   = 5,
        timeout:   float = 30.0,
    ) -> None:
        self.name      = name
        self.threshold = threshold
        self.timeout   = timeout

        self._state:          CircuitState = CircuitState.CLOSED
        self._failures:       int          = 0
        self._opened_at:      float | None = None
        self._half_open_probe: bool        = False
        self._lock = RLock()

        # Métricas
        self._total_calls:    int = 0
        self._total_failures: int = 0
        self._total_successes: int = 0
        self._open_events:    int = 0

        logger.info("[CircuitBreaker] Initialized: %s | threshold=%d | timeout=%.1fs",
                    name, threshold, timeout)

    # ── CORE EXECUTION ────────────────────────────────────────────────────────

    def execute(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Ejecuta fn bajo protección del circuit breaker.
        Lanza CircuitOpenError si el circuito está OPEN.
        """
        with self._lock:
            self._total_calls += 1
            self._check_state()

            if self._state == CircuitState.OPEN:
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is OPEN — calls rejected"
                )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_probe:
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is HALF_OPEN — probe in progress"
                    )
                self._half_open_probe = True

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as exc:
            self._on_failure()
            raise

    # ── STATE TRANSITIONS ─────────────────────────────────────────────────────

    def _check_state(self) -> None:
        """Transiciona OPEN → HALF_OPEN si expiró el timeout."""
        if (
            self._state == CircuitState.OPEN
            and self._opened_at is not None
            and (time.monotonic() - self._opened_at) >= self.timeout
        ):
            self._state           = CircuitState.HALF_OPEN
            self._half_open_probe = False
            logger.info("[CircuitBreaker] %s → HALF_OPEN", self.name)

    def _on_success(self) -> None:
        with self._lock:
            self._total_successes += 1
            if self._state in (CircuitState.HALF_OPEN, CircuitState.CLOSED):
                self._failures        = 0
                self._half_open_probe = False
                self._state           = CircuitState.CLOSED
                logger.debug("[CircuitBreaker] %s → CLOSED", self.name)

    def _on_failure(self) -> None:
        with self._lock:
            self._total_failures += 1
            self._failures       += 1

            if (
                self._state == CircuitState.HALF_OPEN
                or self._failures >= self.threshold
            ):
                self._state           = CircuitState.OPEN
                self._opened_at       = time.monotonic()
                self._half_open_probe = False
                self._open_events    += 1
                logger.warning(
                    "[CircuitBreaker] %s → OPEN | failures=%d | open_events=%d",
                    self.name, self._failures, self._open_events
                )

    # ── OBSERVABILITY ─────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "name":            self.name,
                "state":           self._state.value,
                "failures":        self._failures,
                "threshold":       self.threshold,
                "timeout":         self.timeout,
                "total_calls":     self._total_calls,
                "total_failures":  self._total_failures,
                "total_successes": self._total_successes,
                "open_events":     self._open_events,
            }

    def reset(self) -> None:
        """Resetea el circuit breaker a CLOSED."""
        with self._lock:
            self._state           = CircuitState.CLOSED
            self._failures        = 0
            self._opened_at       = None
            self._half_open_probe = False
        logger.info("[CircuitBreaker] %s reset to CLOSED", self.name)
