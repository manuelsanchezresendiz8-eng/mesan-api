# core/jarvis/health_monitor.py
"""
MESAN Omega Guardian
Health Monitor v2.0

Responsabilidad:
Monitorear continuamente el estado de todos los servicios criticos.

Cada monitor devuelve un ServiceStatus.
GuardianEngine unicamente los orquesta.
"""

from __future__ import annotations

import logging
import os
import shutil
import time
from dataclasses import dataclass

try:
    import psutil
except ImportError:
    psutil = None

from core.jarvis.guardian_engine import ServiceStatus

logger = logging.getLogger("mesan.guardian.health")


class HealthMonitor:

    def __init__(self):
        self.version = "2.0.0"

    def check_postgresql(self, db) -> ServiceStatus:
        started = time.perf_counter()
        try:
            db.execute("SELECT 1")
            latency = (time.perf_counter() - started) * 1000
            return ServiceStatus(
                service="PostgreSQL", status="OK", score=100,
                latency_ms=round(latency, 2), message="Database operational",
            )
        except Exception as e:
            return ServiceStatus(
                service="PostgreSQL", status="DOWN", score=0, message=str(e),
            )

    def check_billing(self, billing_engine) -> ServiceStatus:
        try:
            billing_engine.health()
            return ServiceStatus(
                service="Billing Engine", status="OK", score=100,
                message="Billing operational",
            )
        except Exception as e:
            return ServiceStatus(
                service="Billing Engine", status="ERROR", score=25, message=str(e),
            )

    def check_cpu(self) -> ServiceStatus:
        if psutil is None:
            return ServiceStatus(service="CPU", status="UNKNOWN", score=80, message="psutil not installed")
        cpu    = psutil.cpu_percent()
        score  = max(0, 100 - cpu)
        status = "DOWN" if cpu > 90 else "WARNING" if cpu > 70 else "OK"
        return ServiceStatus(
            service="CPU", status=status, score=score,
            message=f"{cpu:.1f}% used", metadata={"cpu": cpu},
        )

    def check_memory(self) -> ServiceStatus:
        if psutil is None:
            return ServiceStatus(service="Memory", status="UNKNOWN", score=80)
        mem    = psutil.virtual_memory()
        score  = max(0, 100 - mem.percent)
        status = "DOWN" if mem.percent > 90 else "WARNING" if mem.percent > 75 else "OK"
        return ServiceStatus(
            service="Memory", status=status, score=score,
            message=f"{mem.percent:.1f}% used",
            metadata={"available": mem.available, "total": mem.total},
        )

    def check_disk(self) -> ServiceStatus:
        total, used, free = shutil.disk_usage("/")
        percent = (used / total) * 100
        score   = max(0, 100 - percent)
        status  = "DOWN" if percent > 95 else "WARNING" if percent > 80 else "OK"
        return ServiceStatus(
            service="Disk", status=status, score=score,
            message=f"{percent:.1f}% used", metadata={"free": free, "total": total},
        )

    def check_environment(self) -> ServiceStatus:
        required = ["DATABASE_URL", "STRIPE_SECRET_KEY", "OPENAI_API_KEY"]
        missing  = [v for v in required if not os.getenv(v)]
        if missing:
            return ServiceStatus(
                service="Environment", status="ERROR", score=40,
                message="Missing variables", metadata={"missing": missing},
            )
        return ServiceStatus(
            service="Environment", status="OK", score=100,
            message="Environment complete",
        )

    def check_all(self, db=None, billing_engine=None):
        results = [
            self.check_cpu(),
            self.check_memory(),
            self.check_disk(),
            self.check_environment(),
        ]
        if db is not None:
            results.append(self.check_postgresql(db))
        if billing_engine is not None:
            results.append(self.check_billing(billing_engine))
        return results

    def check(self) -> ServiceStatus:
        """Contrato requerido por GuardianEngine: check() -> ServiceStatus"""
        results   = self.check_all()
        if not results:
            return ServiceStatus(service="HealthMonitor", status="UNKNOWN", score=0)
        avg_score = sum(r.score for r in results) / len(results)
        worst     = min(results, key=lambda r: r.score)
        return ServiceStatus(
            service="HealthMonitor",
            status="OK" if avg_score >= 80 else "WARNING" if avg_score >= 50 else "DOWN",
            score=round(avg_score, 2),
            message=f"{len(results)} servicios | peor: {worst.service} ({worst.score:.0f})",
            metadata={"checks": [{"service": r.service, "status": r.status, "score": r.score} for r in results]},
        )


health_monitor = HealthMonitor()