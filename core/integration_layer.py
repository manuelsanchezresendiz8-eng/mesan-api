# core/integration_layer.py -- MESAN Omega Integration Layer v1.1
from typing import Dict, Any
from datetime import datetime
import uuid, traceback
from core.state_adapter import StateAdapter
from core.state_bus import StateBus

class IntegrationLayer:
    VERSION = "1.1.0"

    def __init__(self, orchestrator, observability, state_bus: StateBus,
                 state_adapter: StateAdapter, consistency_engine=None, recovery_engine=None):
        self.orchestrator = orchestrator
        self.observability = observability
        self.state_bus = state_bus
        self.adapter = state_adapter
        self.consistency = consistency_engine
        self.recovery = recovery_engine

    def run(self, raw_data: dict, tenant_id: str = "DEFAULT") -> dict:
        trace_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        pipeline_status = "SUCCESS"

        try:
            state = self.adapter.from_raw(raw_data, tenant_id, trace_id)
            previous_state = self.adapter.to_engine_input(state)

            trace = self.orchestrator.run_pipeline(previous_state, tenant_id=tenant_id)

            for result in getattr(trace, "results", []):
                if not getattr(result, "success", False): continue
                state.score      = self._safe_get(result.result, "score", state.score)
                state.last_event = result.engine
                state.timestamp  = datetime.utcnow().isoformat()

            if self.consistency:
                try:
                    cr = self.consistency.validate_cross_engine_consistency(self.adapter.to_engine_input(state))
                    state.system_inconsistency = not cr.system_consistent
                    state.system_confidence    = cr.system_confidence
                except Exception:
                    pipeline_status = "DEGRADED"
                    state.system_inconsistency = True
                    state.system_confidence    = 0.5

            self.state_bus.emit(tenant_id, trace_id, "integration_layer", "PIPELINE_EXECUTION",
                                previous_state, self.adapter.to_engine_input(state))

            if self.observability:
                for r in getattr(trace, "results", []):
                    try:
                        self.observability.record(r.engine, getattr(r,"duration_ms",0.0),
                                                  getattr(r,"success",False), state.system_confidence, 0.0)
                    except: pass

            finished_at = datetime.utcnow()
            return {
                "trace_id": trace_id, "tenant_id": tenant_id,
                "pipeline_status": pipeline_status,
                "started_at": started_at.isoformat(), "finished_at": finished_at.isoformat(),
                "duration_ms": round((finished_at-started_at).total_seconds()*1000, 2),
                "state": self.adapter.to_engine_input(state), "pipeline": trace,
                "consistency": {"system_inconsistency": state.system_inconsistency,
                                "system_confidence": state.system_confidence}
            }

        except Exception as e:
            recovery_result = None
            if self.recovery:
                try:
                    recovery_result = self.recovery.recover_from_failure("PARTIAL_REBUILD", {"error": str(e)})
                except: pass
            return {
                "trace_id": trace_id, "tenant_id": tenant_id,
                "pipeline_status": "FAILED", "error": str(e),
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "recovery_attempted": recovery_result is not None,
                "recovery_result": str(recovery_result) if recovery_result else None
            }

    def _safe_get(self, obj: Any, key: str, default):
        if isinstance(obj, dict): return obj.get(key, default)
        return getattr(obj, key, default)
