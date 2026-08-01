# core/jarvis/telemetry_engine.py -- MESAN Omega Guardian Telemetry Engine v1.0
"""
Motor de telemetria que registra eventos reales del ecosistema MESAN
y alimenta a Guardian con metricas calculadas, no simuladas.

Arquitectura:
    FastAPI -> TelemetryEngine -> Loggers -> GuardianEngine -> Dashboard

Health Score Algorithm (documentado):
    Base = 100
    - API errors:       -5 por error (max -25)
    - DB errors:        -10 por error (max -30)
    - Security issues:  -15 por issue (max -30)
    - AI failures:      -10 por fallo (max -20)
    - Latency > 500ms:  -5
    - Latency > 1000ms: -10
    - Latency > 2000ms: -15
    - Uptime < 5min:    -5
    Score = max(0, resultado)
"""

import os
import time
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List

from core.jarvis.telemetry_models import TelemetryEvent
from core.jarvis.telemetry_logger import (
    api_logger, security_logger, payment_logger,
    system_logger, guardian_logger, write_event,
)

logger = logging.getLogger("mesan.telemetry")

TELEMETRY_VERSION = "1.0.0"
MAX_EVENTS = 500


class GuardianTelemetryEngine:

    def __init__(self):
        self.version = TELEMETRY_VERSION
        self._events = deque(maxlen=MAX_EVENTS)
        self._api_events = deque(maxlen=MAX_EVENTS)
        self._security_events = deque(maxlen=200)
        self._payment_events = deque(maxlen=200)
        self._db_events = deque(maxlen=200)
        self._guardian_events = deque(maxlen=200)
        self._ai_events = deque(maxlen=200)
        self._started_at = time.time()
        self._error_count = 0
        self._request_count = 0
        self._total_latency = 0.0
        logger.info("[Telemetry] v%s iniciado", self.version)

    def _create_event(self, service, severity, message, latency=0,
                      status="OK", source="", metadata=None):
        event = TelemetryEvent(
            service=service,
            severity=severity,
            message=message,
            latency=latency,
            status=status,
            source=source,
            metadata=metadata or {},
        )
        return event

    def _store_and_log(self, event, category_deque, logger_instance):
        d = event.to_dict()
        category_deque.append(d)
        self._events.append(d)
        write_event(logger_instance, d)
        if event.severity == "CRITICAL":
            self._auto_alert(event)

    # --- Public logging methods ---

    def log_api(self, method, path, status_code, latency_ms, error=None):
        self._request_count += 1
        self._total_latency += latency_ms
        if status_code >= 500:
            severity, status = "CRITICAL", "ERROR"
            self._error_count += 1
        elif status_code >= 400:
            severity, status = "WARNING", "WARN"
        else:
            severity, status = "INFO", "OK"
        msg = "{} {} -> {} ({}ms)".format(method, path, status_code, round(latency_ms, 2))
        if error:
            msg += " | " + str(error)
        event = self._create_event("API", severity, msg, latency_ms, status, source="fastapi")
        self._store_and_log(event, self._api_events, api_logger)

    def log_security(self, event_type, detail, severity="WARNING"):
        event = self._create_event(
            "Security", severity,
            "{}: {}".format(event_type, detail),
            source="security_monitor",
        )
        self._store_and_log(event, self._security_events, security_logger)

    def log_payment(self, action, amount, currency="MXN", status="OK", detail=""):
        severity = "INFO" if status == "OK" else "WARNING"
        msg = "{} ${} {} - {} {}".format(action, amount, currency, status, detail)
        event = self._create_event("Payments", severity, msg, status=status, source="billing")
        self._store_and_log(event, self._payment_events, payment_logger)

    def log_database(self, operation, latency_ms, status="OK", detail=""):
        if status != "OK":
            severity = "CRITICAL"
            self._error_count += 1
        else:
            severity = "INFO"
        msg = "DB {} ({}ms) {} {}".format(operation, round(latency_ms, 2), status, detail)
        event = self._create_event("Database", severity, msg, latency_ms, status, source="postgresql")
        self._store_and_log(event, self._db_events, system_logger)

    def log_guardian(self, message, severity="INFO", metadata=None):
        event = self._create_event("Guardian", severity, message, source="guardian", metadata=metadata)
        self._store_and_log(event, self._guardian_events, guardian_logger)

    def log_ai(self, provider, action, latency_ms=0, status="OK", detail=""):
        if status != "OK":
            severity = "CRITICAL" if "timeout" in detail.lower() else "HIGH"
            self._error_count += 1
        else:
            severity = "INFO"
        msg = "{} {} ({}ms) {} {}".format(provider, action, round(latency_ms, 2), status, detail)
        event = self._create_event("AI", severity, msg, latency_ms, status, source=provider.lower())
        self._store_and_log(event, self._ai_events, system_logger)

    # --- Auto alert rules ---

    def _auto_alert(self, event):
        self.log_guardian(
            "AUTO_ALERT: {} - {}".format(event.service, event.message),
            severity="CRITICAL",
            metadata={"trigger": event.service, "original_status": event.status},
        )

    # --- Metrics ---

    def build_metrics(self):
        uptime = time.time() - self._started_at
        avg_latency = round(self._total_latency / max(self._request_count, 1), 2)
        api_errors = sum(1 for e in self._api_events if e.get("status") == "ERROR")
        db_errors = sum(1 for e in self._db_events if e.get("status") != "OK")
        security_issues = sum(1 for e in self._security_events if e.get("severity") in ("CRITICAL", "HIGH"))
        ai_failures = sum(1 for e in self._ai_events if e.get("status") != "OK")
        critical_count = sum(1 for e in self._events if e.get("severity") == "CRITICAL")
        warning_count = sum(1 for e in self._events if e.get("severity") == "WARNING")
        health = self.calculate_health_score(
            api_errors=api_errors,
            db_errors=db_errors,
            security_issues=security_issues,
            ai_failures=ai_failures,
            avg_latency=avg_latency,
            uptime=uptime,
        )
        services = self._check_services()
        api_uptime = round((1 - api_errors / max(self._request_count, 1)) * 100, 2)
        db_ok = all(e.get("status") == "OK" for e in list(self._db_events)[-10:]) if self._db_events else True
        ai_ok = all(e.get("status") == "OK" for e in list(self._ai_events)[-5:]) if self._ai_events else True
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "health": health,
            "latency": avg_latency,
            "critical": critical_count,
            "warnings": warning_count,
            "uptime_seconds": round(uptime, 2),
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "services": services,
            "metrics": {
                "api_uptime": api_uptime,
                "db_uptime": 100.0 if db_ok else 0.0,
                "ai_status": "OK" if ai_ok else "DEGRADED",
            },
        }

    def calculate_health_score(self, api_errors, db_errors, security_issues,
                                ai_failures, avg_latency, uptime):
        """
        Health Score Algorithm (0-100):
        Base = 100
        - API errors:       -5 per error (max -25)
        - DB errors:        -10 per error (max -30)
        - Security issues:  -15 per issue (max -30)
        - AI failures:      -10 per failure (max -20)
        - Latency > 500ms:  -5  | > 1000ms: -10 | > 2000ms: -15
        - Uptime < 5min:    -5
        """
        score = 100.0
        score -= min(api_errors * 5, 25)
        score -= min(db_errors * 10, 30)
        score -= min(security_issues * 15, 30)
        score -= min(ai_failures * 10, 20)
        if avg_latency > 2000:
            score -= 15
        elif avg_latency > 1000:
            score -= 10
        elif avg_latency > 500:
            score -= 5
        if uptime < 300:
            score -= 5
        return max(round(score, 1), 0)

    # --- Service checks (datos reales) ---

    def _check_services(self):
        services = []
        services.append(self._check_db())
        services.append(self._check_render())
        services.append(self._check_stripe())
        services.append(self._check_ai())
        return services

    def _check_db(self):
        try:
            import psycopg
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return {"service": "PostgreSQL", "status": "OFFLINE", "score": 0}
            start = time.perf_counter()
            conn = psycopg.connect(db_url, connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            latency = round((time.perf_counter() - start) * 1000, 2)
            self.log_database("health_check", latency, "OK")
            return {"service": "PostgreSQL", "status": "OK", "score": 100, "latency_ms": latency}
        except Exception as e:
            self.log_database("health_check", 0, "ERROR", str(e))
            return {"service": "PostgreSQL", "status": "OFFLINE", "score": 0, "error": str(e)}

    def _check_render(self):
        uptime = time.time() - self._started_at
        return {
            "service": "Render",
            "status": "OK" if uptime > 60 else "STARTING",
            "score": 100 if uptime > 60 else 50,
            "uptime_seconds": round(uptime, 0),
        }

    def _check_stripe(self):
        key = os.getenv("STRIPE_SECRET_KEY", "")
        if not key:
            return {"service": "Stripe", "status": "NOT_CONFIGURED", "score": 50}
        mode = "live" if key.startswith("sk_live") else "test"
        return {"service": "Stripe", "status": "OK", "score": 100, "mode": mode}

    def _check_ai(self):
        recent = list(self._ai_events)[-5:] if self._ai_events else []
        failures = sum(1 for e in recent if e.get("status") != "OK")
        if failures > 2:
            return {"service": "AI", "status": "DEGRADED", "score": 30}
        if failures > 0:
            return {"service": "AI", "status": "WARNING", "score": 70}
        return {"service": "AI", "status": "OK", "score": 100}

    # --- Dashboard snapshot ---

    def get_dashboard_snapshot(self):
        metrics = self.build_metrics()
        metrics["recent_events"] = self._get_recent(20)
        return metrics

    def export_json(self):
        return self.get_dashboard_snapshot()

    def _get_recent(self, limit=50):
        events = list(self._events)
        events.reverse()
        return events[:limit]


telemetry_engine = GuardianTelemetryEngine()