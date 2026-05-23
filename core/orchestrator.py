# core/orchestrator.py -- MESAN Omega Orchestrator Core v1.1
from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
import uuid, time, logging

logger = logging.getLogger("mesan.orchestrator")

@dataclass
class EngineExecutionResult:
    engine: str; success: bool; duration_ms: float
    result: Any = None; error: str = ""

@dataclass
class PipelineTrace:
    trace_id: str; tenant_id: str; started_at: str; finished_at: str
    total_duration_ms: float; success: bool
    results: List[EngineExecutionResult] = field(default_factory=list)

class MesanOrchestrator:
    VERSION = "1.1.0"

    def __init__(self):
        self._engines: Dict[str, Any] = {}

    def register(self, name: str, engine: Any):
        self._engines[name] = engine

    def run_pipeline(self, empresa_data: dict, tenant_id: str = "DEFAULT") -> PipelineTrace:
        trace_id = str(uuid.uuid4())
        started = datetime.utcnow()
        t0 = time.perf_counter()
        results = []

        logger.info(f"[ORCHESTRATOR] Starting | trace={trace_id}")

        for name, engine in self._engines.items():
            te = time.perf_counter()
            try:
                result = self._execute_engine(engine, empresa_data)
                ms = round((time.perf_counter()-te)*1000, 2)
                results.append(EngineExecutionResult(name, True, ms, result))
                logger.info(f"[ORCHESTRATOR] OK | engine={name} | {ms}ms")
            except Exception as e:
                ms = round((time.perf_counter()-te)*1000, 2)
                results.append(EngineExecutionResult(name, False, ms, error=str(e)))
                logger.exception(f"[ORCHESTRATOR] FAILED | engine={name}")

        total_ms = round((time.perf_counter()-t0)*1000, 2)
        return PipelineTrace(trace_id=trace_id, tenant_id=tenant_id,
                             started_at=started.isoformat(), finished_at=datetime.utcnow().isoformat(),
                             total_duration_ms=total_ms, success=all(r.success for r in results),
                             results=results)

    def _execute_engine(self, engine, data):
        if hasattr(engine, "analizar"): return engine.analizar(data)
        if hasattr(engine, "analyze"):  return engine.analyze(data)
        if hasattr(engine, "run"):      return engine.run(data)
        raise RuntimeError(f"Engine incompatible: {type(engine).__name__}")

    def retry_failed_engine(self, engine_name: str, empresa_data: dict) -> dict:
        engine = self._engines.get(engine_name)
        if not engine: return {"success": False, "error": "Engine not registered"}
        try:
            return {"success": True, "engine": engine_name, "result": self._execute_engine(engine, empresa_data)}
        except Exception as e:
            logger.exception(f"[ORCHESTRATOR] Retry failed | engine={engine_name}")
            return {"success": False, "engine": engine_name, "error": str(e)}

    def health(self) -> dict:
        return {"status": "HEALTHY", "version": self.VERSION,
                "registered_engines": list(self._engines.keys()),
                "total_engines": len(self._engines),
                "timestamp": datetime.utcnow().isoformat()}
