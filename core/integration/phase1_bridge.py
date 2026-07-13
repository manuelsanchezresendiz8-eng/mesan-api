# =============================================================================
# MESAN Omega - Phase 1 Integration Bridge v1.1
# =============================================================================
# Bindings REALES verificados contra:
#   - core/observability_bus.py   v1.6.1 (instancia global omega_bus, EventType)
#   - core/predictive_engine.py   v4.1   (MesanOmegaPredictiveEngine.analizar)
#   - core/resilience_core_v6.py  v6.0   (safe_float, safe_int, safe_div)
#
# REGLA ABSOLUTA: este bridge NUNCA puede romper el Pipeline Omega v1.0 (63017f3).
# Garantias (patron Guardian Omega):
#   1. Feature flags por entorno - todo apagado por default.
#   2. Lazy imports - modulo ausente o roto degrada a no-op silencioso.
#   3. Fail-open - ninguna excepcion se propaga al orquestador.
#   4. Cero cambios de contrato - datos predictivos son campo aditivo opcional.
# =============================================================================

from __future__ import annotations

import dataclasses
import logging
import os
import time
from typing import Any, Callable, Optional

logger = logging.getLogger("mesan.phase1")

FLAG_OBSERVABILITY = "MESAN_P1_OBSERVABILITY"
FLAG_PREDICTIVE    = "MESAN_P1_PREDICTIVE"
FLAG_RESILIENCE    = "MESAN_P1_RESILIENCE"

PIPELINE_ENGINE_NAME = "omega_pipeline"


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes", "on")


def _safe(default: Any = None) -> Callable:
    """Decorador fail-open: cualquier excepcion se loguea y se traga."""
    def wrap(fn: Callable) -> Callable:
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - aislamiento total
                logger.warning("phase1_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


# =============================================================================
# 1) OBSERVABILITY BRIDGE - observability_bus.py v1.6.1
# =============================================================================
class ObservabilityBridge:
    """Fachada sobre la instancia global omega_bus. Sin bus: no-op total."""

    def __init__(self) -> None:
        self._bus = None
        self._event_type = None
        self._enabled = _flag(FLAG_OBSERVABILITY)
        if self._enabled:
            try:
                # BINDING REAL: instancia global unica - NO construir otra
                from core.observability_bus import omega_bus, EventType
                self._bus = omega_bus
                self._event_type = EventType
                logger.info("Phase1: ObservabilityBus v1.6.1 conectado (omega_bus global)")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase1: ObservabilityBus no disponible (%s)", exc)
                self._enabled = False

    @property
    def active(self) -> bool:
        return self._enabled and self._bus is not None

    @_safe()
    def pipeline_started(self, trace_id: str, tenant_id: str) -> None:
        if self.active:
            self._bus.start_trace(trace_id, engine=PIPELINE_ENGINE_NAME,
                                  tenant=tenant_id or "global")

    @_safe()
    def pipeline_completed(self, trace_id: str, tenant_id: str,
                           elapsed_ms: float, ok: bool = True) -> None:
        if not self.active:
            return
        et = (self._event_type.ENGINE_SUCCESS if ok
              else self._event_type.ENGINE_FAILURE)
        self._bus.emit(event_type=et, engine=PIPELINE_ENGINE_NAME,
                       tenant=tenant_id or "global", trace_id=trace_id,
                       latency_ms=elapsed_ms)
        self._bus.complete_trace(trace_id, engine=PIPELINE_ENGINE_NAME,
                                 tenant=tenant_id or "global")

    @_safe()
    def engine_timing(self, trace_id: str, tenant_id: str, engine: str,
                      elapsed_ms: float, ok: bool = True) -> None:
        """Alimenta MetricsCollector y health score por motor."""
        if not self.active:
            return
        et = (self._event_type.ENGINE_SUCCESS if ok
              else self._event_type.ENGINE_FAILURE)
        self._bus.emit(event_type=et, engine=engine,
                       tenant=tenant_id or "global", trace_id=trace_id,
                       latency_ms=elapsed_ms)

    @_safe(default={})
    def health_snapshot(self, tenant_id: str = "global") -> dict:
        if not self.active:
            return {}
        return {
            "system_health": self._bus.system_health(tenant_id),
            "engines": self._bus.health_scores(tenant_id),
        }

    @_safe(default=None)
    def get_trace(self, trace_id: str) -> Optional[list]:
        if self.active:
            return self._bus.traces.get_trace(trace_id)
        return None

    @_safe()
    def attach_circuit_breaker(self, breaker) -> None:
        """Opcional: enchufa breakers de Guardian Omega al bus (v1.6 nativo)."""
        if self.active:
            self._bus.attach_circuit_breaker(breaker)


# =============================================================================
# 2) PREDICTIVE BRIDGE - predictive_engine.py v4.1
# =============================================================================
# IMPORTANTE: analizar() consume los DATOS DE ENTRADA del diagnostico
# (ingresos, nomina, gastos, ...), NO el resultado del pipeline.
_KEY_ALIASES = {
    "trabajadores_sin_imss": "sin_imss",   # EmpresaInput -> contrato v4.1
    "caja_disponible": "caja",             # payload /execute -> contrato v4.1
}


class PredictiveBridge:
    """Corre Predictive Defense v4.1 post-diagnostico. Nunca bloquea."""

    def __init__(self) -> None:
        self._engine = None
        self._enabled = _flag(FLAG_PREDICTIVE)
        if self._enabled:
            try:
                # BINDING REAL: clase MesanOmegaPredictiveEngine, metodo analizar()
                from core.predictive_engine import MesanOmegaPredictiveEngine
                self._engine = MesanOmegaPredictiveEngine()
                logger.info("Phase1: MesanOmegaPredictiveEngine v4.1 conectado")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase1: PredictiveEngine no disponible (%s)", exc)
                self._enabled = False

    @property
    def active(self) -> bool:
        return self._enabled and self._engine is not None

    @staticmethod
    def _normalize(data: dict) -> dict:
        out = dict(data)
        for src, dst in _KEY_ALIASES.items():
            if src in out and dst not in out:
                out[dst] = out[src]
        return out

    @_safe(default=None)
    def evaluate(self, input_data: dict, tenant_id: str = "global") -> Optional[dict]:
        """Devuelve dict JSON-safe con la prediccion, o None (nunca excepcion).

        Uso en el orquestador (campo aditivo, OmegaResponse intacto):
            pred = get_predictive().evaluate(request_data, tenant_id)
            if pred:
                response.metadata["predictive"] = pred
        """
        if not self.active or not isinstance(input_data, dict):
            return None
        t0 = time.perf_counter()
        resultado = self._engine.analizar(self._normalize(input_data))
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "engine": "predictive_defense",
            "version": "4.1",
            "elapsed_ms": elapsed,
            "tenant": tenant_id,
            "result": dataclasses.asdict(resultado),  # ResultadoMesan -> dict JSON-safe
        }


# =============================================================================
# 3) RESILIENCE FACADE - resilience_core_v6.py v6.0
# =============================================================================
# Importar SIEMPRE desde aqui en el resto del stack:
#     from core.integration.phase1_bridge import safe_float, safe_int, safe_div
# Nota: el import de resilience_core_v6 ejecuta logging.basicConfig() a nivel
# modulo - razon adicional para mantenerlo lazy y bajo flag.

def _fb_safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return default if value is None else float(value)
    except Exception:  # noqa: BLE001
        return default


def _fb_safe_int(value: Any, default: int = 0) -> int:
    try:
        return default if value is None else int(value)
    except Exception:  # noqa: BLE001
        return default


def _fb_safe_div(a: Any, b: Any, default: Any = 0):
    try:
        return default if b == 0 else a / b
    except Exception:  # noqa: BLE001
        return default


safe_float = _fb_safe_float
safe_int = _fb_safe_int
safe_div = _fb_safe_div

if _flag(FLAG_RESILIENCE):
    try:
        # BINDING REAL: nombres exactos exportados por resilience_core_v6
        from core.resilience_core_v6 import safe_float as _rc_sf
        from core.resilience_core_v6 import safe_int as _rc_si
        from core.resilience_core_v6 import safe_div as _rc_sd
        safe_float, safe_int, safe_div = _rc_sf, _rc_si, _rc_sd
        logger.info("Phase1: ResilienceCore v6.0 activo (safe_float/safe_int/safe_div)")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Phase1: ResilienceCore no disponible (%s) - fallback local", exc)


# =============================================================================
# Singletons - un solo import en omega_orchestrator.py
# =============================================================================
_observability: Optional[ObservabilityBridge] = None
_predictive: Optional[PredictiveBridge] = None


def get_observability() -> ObservabilityBridge:
    global _observability
    if _observability is None:
        _observability = ObservabilityBridge()
    return _observability


def get_predictive() -> PredictiveBridge:
    global _predictive
    if _predictive is None:
        _predictive = PredictiveBridge()
    return _predictive