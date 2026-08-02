# core/jarvis/control_plane.py -- MESAN Omega Control Plane v1.0
"""
Panel de control unificado que centraliza todos los sistemas de MESAN Omega.
Guardian, Telemetry, Watchdog, Self-Healing, Rollback, Billing, CRM, JARVIS, War Room.
"""
import logging
import time
from datetime import datetime, timezone
logger = logging.getLogger("mesan.controlplane")

class ControlPlane:
    def __init__(self):
        self.version = "1.0.0"
        self._started_at = time.time()
        logger.info("[ControlPlane] v%s iniciado", self.version)

    def get_state(self):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "uptime_seconds": round(time.time() - self._started_at, 2),
            "systems": {
                "guardian": self._get_guardian(),
                "telemetry": self._get_telemetry(),
                "scheduler": self._get_scheduler(),
                "predictive": self._get_predictive(),
                "notifications": self._get_notifications(),
                "billing": self._get_billing(),
                "jarvis": self._get_jarvis(),
                "warroom": self._get_warroom(),
                "crm": self._get_crm(),
                "omega_pipeline": self._get_omega(),
            },
        }

    def _get_guardian(self):
        try:
            from core.jarvis.guardian_integration import guardian_integration
            s = guardian_integration.get_state()
            return {"status": s.get("health_status", "UNKNOWN"), "health": s.get("health_score", 0), "online": True}
        except Exception as e:
            return {"status": "OFFLINE", "error": str(e), "online": False}

    def _get_telemetry(self):
        try:
            from core.jarvis.telemetry_engine import telemetry_engine
            m = telemetry_engine.build_metrics()
            return {"status": "OK", "health": m.get("health", 0), "requests": m.get("total_requests", 0), "online": True}
        except Exception:
            return {"status": "OFFLINE", "online": False}

    def _get_scheduler(self):
        try:
            from core.jarvis.guardian_scheduler import guardian_scheduler
            return guardian_scheduler.health_check()
        except Exception:
            return {"status": "NOT_LOADED", "online": False}

    def _get_predictive(self):
        try:
            from core.jarvis.predictive_analytics import predictive_engine
            return predictive_engine.get_last()
        except Exception:
            return {"status": "NOT_LOADED", "online": False}

    def _get_notifications(self):
        try:
            from core.jarvis.notification_center import notification_center
            return notification_center.get_status()
        except Exception:
            return {"status": "NOT_LOADED", "online": False}

    def _get_billing(self):
        try:
            from core.billing.subscription_engine import subscription_engine
            m = subscription_engine.get_metrics()
            return {"status": "OK", "mrr": m.get("mrr_mxn", 0), "active_subs": m.get("active_subscriptions", 0), "online": True}
        except Exception:
            return {"status": "UNAVAILABLE", "online": False}

    def _get_jarvis(self):
        try:
            from core.jarvis.jarvis_engine import jarvis_engine
            return {"status": "OK", "version": jarvis_engine.version, "online": True}
        except Exception:
            return {"status": "OFFLINE", "online": False}

    def _get_warroom(self):
        try:
            from core.jarvis.jarvis_engine import jarvis_engine
            wr = jarvis_engine.get_warroom()
            return {"status": "OK", "online": True, "risks": len(wr.get("warroom", {}).get("top_risks", []))}
        except Exception:
            return {"status": "OFFLINE", "online": False}

    def _get_crm(self):
        try:
            import psycopg, os
            conn = psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            total = cur.fetchone()[0]
            cur.close(); conn.close()
            return {"status": "OK", "total_leads": total, "online": True}
        except Exception:
            return {"status": "OFFLINE", "online": False}

    def _get_omega(self):
        try:
            from services.omega_orchestrator import omega_orchestrator
            return {"status": "OK", "engines": 10, "online": True}
        except Exception:
            return {"status": "OFFLINE", "online": False}

control_plane = ControlPlane()