core/state_adapter.py -- MESAN Omega State Adapter Layer v1.1

from datetime import datetime
from typing import Dict, Any

from core.state_schema_v1 import CoreState

class StateAdapter:

VERSION = "1.1.0"

NUMERIC_FIELDS = {
    "ingresos",
    "nomina",
    "gastos",
    "deuda_mensual",
    "score",
    "confidence",
    "validation_penalty",
    "exposicion_probable",
    "exposure_score",
    "system_confidence",
}

RESERVED_FIELDS = {
    "tenant_id",
    "trace_id",
    "timestamp",
}

def _safe_float(self, value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _safe_int(self, value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def from_raw(
    self,
    data: Dict[str, Any],
    tenant_id: str,
    trace_id: str
) -> CoreState:

    if not isinstance(data, dict):
        raise ValueError("StateAdapter requiere un diccionario válido.")

    ingresos = self._safe_float(data.get("ingresos"))
    nomina   = self._safe_float(data.get("nomina"))
    gastos   = self._safe_float(data.get("gastos"))
    deuda    = self._safe_float(data.get("deuda_mensual"))

    flujo_operativo = ingresos - nomina - gastos - deuda
    burn_rate       = nomina + gastos + deuda

    # Protección deterministic/replay-safe
    if burn_rate <= 0:
        dias_supervivencia = 365
    else:
        dias_supervivencia = max(
            int((max(ingresos, 0) / burn_rate) * 30),
            0
        )

    reserved = self.NUMERIC_FIELDS.union(self.RESERVED_FIELDS)

    extra = {
        k: v
        for k, v in data.items()
        if k not in reserved
    }

    return CoreState(
        tenant_id=tenant_id,
        trace_id=trace_id,

        ingresos=ingresos,
        nomina=nomina,
        gastos=gastos,
        deuda_mensual=deuda,

        flujo_operativo=flujo_operativo,
        burn_rate=burn_rate,
        dias_supervivencia=dias_supervivencia,

        score=self._safe_float(data.get("score")),
        confidence=self._safe_float(data.get("confidence"), 0.82),

        nivel_riesgo=str(data.get("nivel_riesgo", "MEDIO")),

        contradictions=self._safe_int(
            data.get("contradictions")
        ),

        validation_penalty=self._safe_float(
            data.get("validation_penalty")
        ),

        exposicion_probable=self._safe_float(
            data.get("exposicion_probable")
        ),

        exposure_score=self._safe_float(
            data.get("exposure_score")
        ),

        system_inconsistency=bool(
            data.get("system_inconsistency", False)
        ),

        system_confidence=self._safe_float(
            data.get("system_confidence"),
            1.0
        ),

        last_event=data.get("last_event"),

        timestamp=data.get(
            "timestamp",
            datetime.utcnow().isoformat()
        ),

        extra=extra
    )

def to_engine_input(self, state: CoreState) -> Dict[str, Any]:

    if not isinstance(state, CoreState):
        raise ValueError("to_engine_input requiere CoreState.")

    return {
        "tenant_id": state.tenant_id,
        "trace_id": state.trace_id,

        "ingresos": state.ingresos,
        "nomina": state.nomina,
        "gastos": state.gastos,
        "deuda_mensual": state.deuda_mensual,

        "flujo_operativo": state.flujo_operativo,
        "burn_rate": state.burn_rate,
        "dias_supervivencia": state.dias_supervivencia,

        "score": state.score,
        "confidence": state.confidence,
        "nivel_riesgo": state.nivel_riesgo,

        "contradictions": state.contradictions,
        "validation_penalty": state.validation_penalty,

        "exposicion_probable": state.exposicion_probable,
        "exposure_score": state.exposure_score,

        "system_inconsistency": state.system_inconsistency,
        "system_confidence": state.system_confidence,

        "last_event": state.last_event,
        "timestamp": state.timestamp,

        **state.extra
    }
