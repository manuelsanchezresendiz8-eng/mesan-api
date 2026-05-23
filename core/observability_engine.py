# core/observability_engine.py
# MESAN Omega Observability Layer v1.1

from dataclasses import dataclass, asdict
from typing import Dict, List
from datetime import datetime
from threading import Lock
import statistics


@dataclass
class EngineMetric:
    engine: str
    execution_time_ms: float
    success: bool
    confidence: float
    drift_score: float
    trace_id: str
    tenant_id: str
    timestamp: str
    severity: str = "INFO"

    def to_dict(self):
        return asdict(self)


@dataclass
class SystemHealthReport:
    timestamp: str
    total_executions: int
    avg_latency_ms: float
    error_rate: float
    avg_confidence: float
    avg_drift: float
    engines_health: Dict[str, dict]
    system_status: str

    def to_dict(self):
        return asdict(self)


class ObservabilityEngine:

    VERSION = "1.1.0"

    MAX_METRICS = 10000

    def __init__(self):
        self._metrics: List[EngineMetric] = []
        self._lock = Lock()

    # ====================================================
    # SAFE MEAN
    # ====================================================

    def _safe_mean(self, values: List[float]) -> float:
        if not values:
            return 0.0
        return round(statistics.mean(values), 3)

    # ====================================================
    # RECORD METRIC
    # ====================================================

    def record(
        self,
        engine: str,
        execution_time_ms: float,
        success: bool,
        confidence: float,
        drift_score: float = 0.0,
        trace_id: str = "",
        tenant_id: str = "GLOBAL",
        severity: str = "INFO"
    ):

        metric = EngineMetric(
            engine=engine,
            execution_time_ms=execution_time_ms,
            success=success,
            confidence=confidence,
            drift_score=drift_score,
            trace_id=trace_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow().isoformat(),
            severity=severity
        )

        with self._lock:

            self._metrics.append(metric)

            # Retention policy
            if len(self._metrics) > self.MAX_METRICS:
                self._metrics = self._metrics[-self.MAX_METRICS:]

    # ====================================================
    # GENERATE REPORT
    # ====================================================

    def generate_report(self) -> SystemHealthReport:

        with self._lock:

            if not self._metrics:
                return SystemHealthReport(
                    timestamp=datetime.utcnow().isoformat(),
                    total_executions=0,
                    avg_latency_ms=0.0,
                    error_rate=0.0,
                    avg_confidence=0.0,
                    avg_drift=0.0,
                    engines_health={},
                    system_status="NO_DATA"
                )

            total = len(self._metrics)

            latencies = [m.execution_time_ms for m in self._metrics]
            confidences = [m.confidence for m in self._metrics]
            drifts = [m.drift_score for m in self._metrics]

            errors = [m for m in self._metrics if not m.success]

            engines = {}

            for m in self._metrics:

                e = engines.setdefault(
                    m.engine,
                    {
                        "count": 0,
                        "errors": 0,
                        "latencies": [],
                        "confidences": [],
                        "drifts": []
                    }
                )

                e["count"] += 1

                if not m.success:
                    e["errors"] += 1

                e["latencies"].append(m.execution_time_ms)
                e["confidences"].append(m.confidence)
                e["drifts"].append(m.drift_score)

            engines_health = {}

            for engine, data in engines.items():

                error_rate = data["errors"] / data["count"]

                status = (
                    "CRITICAL" if error_rate > 0.30 else
                    "DEGRADED" if error_rate > 0.10 else
                    "HEALTHY"
                )

                engines_health[engine] = {
                    "executions": data["count"],
                    "error_rate": round(error_rate, 3),
                    "avg_latency_ms": self._safe_mean(data["latencies"]),
                    "avg_confidence": self._safe_mean(data["confidences"]),
                    "avg_drift": self._safe_mean(data["drifts"]),
                    "status": status
                }

            err_rate = len(errors) / total
            avg_conf = self._safe_mean(confidences)
            avg_drift = self._safe_mean(drifts)

            system_status = (
                "CRITICAL"
                if err_rate > 0.25 or avg_conf < 0.60
                else "DEGRADED"
                if err_rate > 0.10 or avg_conf < 0.75
                else "HEALTHY"
            )

            return SystemHealthReport(
                timestamp=datetime.utcnow().isoformat(),
                total_executions=total,
                avg_latency_ms=self._safe_mean(latencies),
                error_rate=round(err_rate, 3),
                avg_confidence=avg_conf,
                avg_drift=avg_drift,
                engines_health=engines_health,
                system_status=system_status
            )

    # ====================================================
    # CLEAR METRICS
    # ====================================================

    def clear(self):

        with self._lock:
            self._metrics.clear()

    # ====================================================
    # GET RAW METRICS
    # ====================================================

    def get_metrics(self) -> List[dict]:

        with self._lock:
            return [m.to_dict() for m in self._metrics]
