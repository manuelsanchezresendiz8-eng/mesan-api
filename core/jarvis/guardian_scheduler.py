# core/jarvis/guardian_scheduler.py -- MESAN Omega Guardian Scheduler v1.0
"""
Programador de ciclos automaticos de Guardian.
Frecuencias configurables por modulo.
"""
import logging
import time
import threading
from datetime import datetime, timezone
logger = logging.getLogger("mesan.guardian.scheduler")

class GuardianScheduler:
    def __init__(self):
        self.version = "1.0.0"
        self._running = False
        self._thread = None
        self._jobs = {}
        self._cycle_count = 0
        self._running_job = False
        self._last_health = None
        self._default_jobs()
        logger.info("[Scheduler] v%s iniciado", self.version)

    def _default_jobs(self):
        self._jobs = {
            "telemetry": {"interval": 30, "last_run": 0, "fn": "_run_telemetry", "enabled": True},
            "guardian": {"interval": 30, "last_run": 0, "fn": "_run_guardian", "enabled": True},
            "watchdog": {"interval": 60, "last_run": 0, "fn": "_run_watchdog", "enabled": True},
            "predictive": {"interval": 300, "last_run": 0, "fn": "_run_predictive", "enabled": True},
            "executive_report": {"interval": 3600, "last_run": 0, "fn": "_run_report", "enabled": True},
            "backup_snapshot": {"interval": 86400, "last_run": 0, "fn": "_run_backup", "enabled": True},
        }

    def start(self):
        if self._running:
            return {"status": "ALREADY_RUNNING"}
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("[Scheduler] Started")
        return {"status": "STARTED"}

    def stop(self):
        self._running = False
        logger.info("[Scheduler] Stopped")
        return {"status": "STOPPED"}

    def schedule_job(self, name, interval, enabled=True):
        self._jobs[name] = {"interval": interval, "last_run": 0, "fn": None, "enabled": enabled}
        return {"status": "SCHEDULED", "job": name, "interval": interval}

    def remove_job(self, name):
        if name in self._jobs:
            del self._jobs[name]
            return {"status": "REMOVED", "job": name}
        return {"status": "NOT_FOUND", "job": name}

    def run_cycle(self):
        self._cycle_count += 1
        now = time.time()
        executed = []
        for name, job in self._jobs.items():
            if not job["enabled"]:
                continue
            if now - job["last_run"] >= job["interval"]:
                try:
                    if self._running_job:
                        continue
                    self._running_job = True
                    fn_name = job.get("fn")
                    if fn_name and hasattr(self, fn_name):
                        getattr(self, fn_name)()
                    self._running_job = False
                    job["last_run"] = now
                    executed.append(name)
                except Exception as e:
                    self._running_job = False
                    logger.error("[Scheduler] Job %s failed: %s", name, e)
        return {"cycle": self._cycle_count, "executed": executed, "timestamp": datetime.now(timezone.utc).isoformat()}

    def _loop(self):
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error("[Scheduler] Loop error: %s", e)
            time.sleep(5)

    def _run_telemetry(self):
        try:
            from core.jarvis.telemetry_engine import telemetry_engine
            telemetry_engine.build_metrics()
        except Exception as e:
            logger.error("[Scheduler] Telemetry: %s", e)

    def _run_guardian(self):
        try:
            from core.jarvis.guardian_engine import guardian_engine
            guardian_engine.execute()
        except Exception as e:
            logger.error("[Scheduler] Guardian: %s", e)

    def _run_watchdog(self):
        try:
            from core.jarvis.telemetry_engine import telemetry_engine
            from core.jarvis.watchdog import watchdog
            snap = telemetry_engine.get_dashboard_snapshot()
            watchdog.evaluate(snap)
        except Exception as e:
            logger.error("[Scheduler] Watchdog: %s", e)

    def _run_predictive(self):
        try:
            from core.jarvis.predictive_analytics import predictive_engine
            predictive_engine.analyze()
        except Exception:
            pass

    def _run_report(self):
        try:
            from core.jarvis.executive_reporting import executive_reporter
            executive_reporter.generate()
        except Exception:
            pass

    def _run_backup(self):
        try:
            from core.jarvis.telemetry_engine import telemetry_engine
            from core.jarvis.rollback_manager import rollback_manager
            snap = telemetry_engine.build_metrics()
            rollback_manager.save_snapshot(snap)
        except Exception as e:
            logger.error("[Scheduler] Backup: %s", e)

    def health_check(self):
        return {
            "status": "RUNNING" if self._running else "STOPPED",
            "version": self.version,
            "cycle_count": self._cycle_count,
            "jobs": {k: {"interval": v["interval"], "enabled": v["enabled"], "last_run": v["last_run"]} for k, v in self._jobs.items()},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

guardian_scheduler = GuardianScheduler()