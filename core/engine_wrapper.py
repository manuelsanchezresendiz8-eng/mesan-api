# core/engine_wrapper.py -- MESAN Omega Engine Wrapper v1.1
import time
import logging
from typing import Any
from core.context import RequestContext

logger = logging.getLogger("mesan.engine_wrapper")


class EngineWrapper:
    """
    Execution Adapter MESAN Ω v1.1
    - Validación de contrato
    - Tipado explícito
    - Observabilidad de latencia
    - Health check opcional
    - Metadata expuesta
    """

    def __init__(self, engine: Any) -> None:
        if not hasattr(engine, "run"):
            raise TypeError(
                f"Engine '{engine.__class__.__name__}' must implement run()"
            )
        self.engine = engine
        logger.info("[EngineWrapper] Wrapped: %s", engine.__class__.__name__)

    def run(
        self,
        ctx: RequestContext,
        payload: dict[str, Any]
    ) -> Any:
        start = time.perf_counter()
        try:
            result = self.engine.run(ctx=ctx, payload=payload)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.debug(
                "[EngineWrapper] Executed: %s | duration_ms=%s",
                self.engine.__class__.__name__, duration_ms
            )
            return result
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "[EngineWrapper] Error: %s | duration_ms=%s | error=%s",
                self.engine.__class__.__name__, duration_ms, exc
            )
            raise

    def health_check(self) -> bool:
        if hasattr(self.engine, "health_check"):
            return self.engine.health_check()
        return True

    @property
    def version(self) -> str:
        return getattr(self.engine, "VERSION", "unknown")

    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "engine":  self.engine.__class__.__name__,
            "healthy": self.health_check(),
        }
