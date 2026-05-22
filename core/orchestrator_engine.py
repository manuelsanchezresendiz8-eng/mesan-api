# core/orchestrator_engine.py
# MESAN Omega — Orchestrator Engine v2.0
# Enterprise Execution Pipeline Coordinator

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
import traceback
import uuid


# ============================================================
# ENUMS
# ============================================================

class PipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class EngineCriticality(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class EngineResult:

    engine: str

    success: bool

    duration_ms: float

    result: Any

    error: Optional[str] = None

    criticality: EngineCriticality = (
        EngineCriticality.REQUIRED
    )

    started_at: str = ""

    completed_at: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class PipelineTrace:

    trace_id: str

    tenant_id: str

    status: PipelineStatus

    started_at: str

    completed_at: str

    engines_executed: List[str]

    engines_failed: List[str]

    engines_skipped: List[str]

    total_duration_ms: float

    successful_engines: int

    failed_engines: int

    pipeline_confidence: float

    results: List[EngineResult] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# ORCHESTRATOR
# ============================================================

class OrchestratorEngine:

    VERSION = "2.0.0"

    # ========================================================
    # PIPELINE ORDER
    # ========================================================

    PIPELINE_ORDER = [

        "validator",

        "contradiction",

        "exposure",

        "digital_twin",

        "consistency",

        "timeline",

        "snapshot",

        "explainability",

        "causality"

    ]

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self._engines: Dict[
            str,
            Callable
        ] = {}

        self._trace_log: List[
            PipelineTrace
        ] = []

        self._criticality: Dict[
            str,
            EngineCriticality
        ] = {}

    # ========================================================
    # REGISTER ENGINE
    # ========================================================

    def register(
        self,
        name: str,
        fn: Callable,
        criticality: EngineCriticality = (
            EngineCriticality.REQUIRED
        )
    ):

        self._engines[name] = fn

        self._criticality[name] = criticality

    # ========================================================
    # SAFE EXECUTION
    # ========================================================

    def _execute_engine(
        self,
        engine_name: str,
        fn: Callable,
        data: dict
    ) -> EngineResult:

        started = datetime.utcnow()

        try:

            result = fn(data)

            duration = (
                datetime.utcnow() - started
            ).total_seconds() * 1000

            return EngineResult(

                engine=engine_name,

                success=True,

                duration_ms=round(
                    duration,
                    2
                ),

                result=result,

                started_at=started.isoformat(),

                completed_at=datetime.utcnow().isoformat(),

                criticality=self._criticality.get(
                    engine_name,
                    EngineCriticality.REQUIRED
                )

            )

        except Exception as e:

            duration = (
                datetime.utcnow() - started
            ).total_seconds() * 1000

            return EngineResult(

                engine=engine_name,

                success=False,

                duration_ms=round(
                    duration,
                    2
                ),

                result=None,

                error=str(e),

                started_at=started.isoformat(),

                completed_at=datetime.utcnow().isoformat(),

                criticality=self._criticality.get(
                    engine_name,
                    EngineCriticality.REQUIRED
                ),

                metadata={

                    "traceback":
                    traceback.format_exc()

                }

            )

    # ========================================================
    # PIPELINE EXECUTION
    # ========================================================

    def run_pipeline(
        self,
        data: dict,
        tenant_id: str = "DEFAULT"
    ) -> PipelineTrace:

        trace_id = str(uuid.uuid4())

        started_at = datetime.utcnow()

        results: List[
            EngineResult
        ] = []

        failed = []

        skipped = []

        executed = []

        # ----------------------------------------------------
        # EXECUTE ENGINES
        # ----------------------------------------------------

        for engine_name in self.PIPELINE_ORDER:

            fn = self._engines.get(
                engine_name
            )

            # Skip no registrado
            if not fn:

                skipped.append(
                    engine_name
                )

                continue

            engine_result = self._execute_engine(

                engine_name,
                fn,
                data

            )

            results.append(
                engine_result
            )

            if engine_result.success:

                executed.append(
                    engine_name
                )

                # Propagación opcional
                data[
                    f"{engine_name}_result"
                ] = engine_result.result

            else:

                failed.append(
                    engine_name
                )

                # STOP si engine crítico falla
                if (
                    engine_result.criticality
                    ==
                    EngineCriticality.REQUIRED
                ):

                    data[
                        "pipeline_abort_reason"
                    ] = (
                        f"Critical engine failed: "
                        f"{engine_name}"
                    )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        total_duration = (
            datetime.utcnow() - started_at
        ).total_seconds() * 1000

        successful = len([
            r for r in results
            if r.success
        ])

        failed_count = len([
            r for r in results
            if not r.success
        ])

        # ----------------------------------------------------
        # PIPELINE STATUS
        # ----------------------------------------------------

        if failed_count == 0:

            status = PipelineStatus.SUCCESS

        elif successful > 0:

            status = PipelineStatus.PARTIAL

        else:

            status = PipelineStatus.FAILED

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence_penalty = min(
            failed_count * 0.10,
            0.60
        )

        pipeline_confidence = max(
            0.35,
            1.0 - confidence_penalty
        )

        # ----------------------------------------------------
        # TRACE OBJECT
        # ----------------------------------------------------

        trace = PipelineTrace(

            trace_id=trace_id,

            tenant_id=tenant_id,

            status=status,

            started_at=started_at.isoformat(),

            completed_at=datetime.utcnow().isoformat(),

            engines_executed=executed,

            engines_failed=failed,

            engines_skipped=skipped,

            total_duration_ms=round(
                total_duration,
                2
            ),

            successful_engines=successful,

            failed_engines=failed_count,

            pipeline_confidence=round(
                pipeline_confidence,
                3
            ),

            results=results,

            metadata={

                "engine_count":
                len(results),

                "version":
                self.VERSION

            }

        )

        # ----------------------------------------------------
        # STORE TRACE
        # ----------------------------------------------------

        self._trace_log.append(
            trace
        )

        return trace

    # ========================================================
    # EXECUTION TRACE
    # ========================================================

    def build_execution_trace(
        self,
        trace_id: str
    ) -> Optional[PipelineTrace]:

        return next(

            (
                t for t
                in self._trace_log

                if t.trace_id == trace_id
            ),

            None

        )

    # ========================================================
    # LIST TRACES
    # ========================================================

    def list_traces(
        self,
        tenant_id: Optional[str] = None
    ) -> List[PipelineTrace]:

        if not tenant_id:

            return self._trace_log

        return [

            t for t
            in self._trace_log

            if t.tenant_id == tenant_id

        ]

    # ========================================================
    # PARALLEL EXECUTION
    # ========================================================

    def run_parallel(
        self,
        engines: List[str],
        data: dict
    ) -> List[EngineResult]:

        results = []

        with ThreadPoolExecutor(
            max_workers=4
        ) as executor:

            futures = {

                executor.submit(

                    self._execute_engine,
                    engine,
                    self._engines[engine],
                    data

                ): engine

                for engine in engines

                if engine in self._engines

            }

            for future in as_completed(futures):

                results.append(
                    future.result()
                )

        return results

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def health_check(self) -> Dict[str, Any]:

        registered = list(
            self._engines.keys()
        )

        missing = [

            e for e
            in self.PIPELINE_ORDER

            if e not in registered

        ]

        return {

            "healthy":
            len(missing) == 0,

            "registered_engines":
            registered,

            "missing_engines":
            missing,

            "total_registered":
            len(registered),

            "version":
            self.VERSION,

            "timestamp":
            datetime.utcnow().isoformat()

        }
