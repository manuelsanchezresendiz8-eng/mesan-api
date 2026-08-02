# core/jarvis/executive_reporting.py -- MESAN Omega Executive Reporting v1.0
"""
Generador automatico de reportes ejecutivos para CEO y Consejo.
"""
import logging
import json
from datetime import datetime, timezone
from collections import deque
logger = logging.getLogger("mesan.guardian.reporting")

class ExecutiveReporter:
    def __init__(self):
        self.version = "1.0.0"
        self._reports = deque(maxlen=50)
        logger.info("[Reporting] v%s iniciado", self.version)

    def generate(self):
        try:
            from core.jarvis.guardian_integration import guardian_integration
            state = guardian_integration.get_state()
        except Exception:
            state = {}
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "type": "EXECUTIVE_REPORT",
            "summary": {
                "health_score": state.get("health_score", 0),
                "health_status": state.get("health_status", "UNKNOWN"),
                "availability_pct": state.get("availability_pct", 100),
                "mttr_ms": state.get("mttr_ms", 0),
                "incidents_count": state.get("incidents_count", 0),
                "rollbacks_executed": state.get("rollbacks_executed", 0),
                "automatic_actions": state.get("automatic_actions", 0),
                "recovery_success_rate": state.get("recovery_success_rate", 100),
                "escalations_to_warroom": state.get("escalations_to_warroom", 0),
                "uptime_seconds": state.get("uptime_seconds", 0),
                "total_requests": state.get("total_requests", 0),
                "total_errors": state.get("total_errors", 0),
            },
            "services": state.get("services", []),
            "alerts": state.get("alerts", []),
            "self_healing": state.get("self_healing", {}),
            "health_trend": state.get("health_trend", []),
            "ceo_brief": self._ceo_brief(state),
            "council_brief": self._council_brief(state),
        }
        self._reports.append(report)
        return report

    def _ceo_brief(self, state):
        h = state.get("health_score", 0)
        inc = state.get("incidents_count", 0)
        avail = state.get("availability_pct", 100)
        if h >= 90:
            status_text = "Sistema operando de forma optima."
        elif h >= 70:
            status_text = "Sistema operativo con alertas menores."
        elif h >= 50:
            status_text = "Sistema degradado. Requiere atencion."
        else:
            status_text = "Sistema en estado critico. Accion inmediata requerida."
        return {
            "titulo": "Resumen CEO - MESAN Omega",
            "estado": status_text,
            "health_score": h,
            "disponibilidad": "{}%".format(avail),
            "incidentes_activos": inc,
            "recomendacion": "Mantener monitoreo" if h >= 70 else "Revisar War Room inmediatamente",
        }

    def _council_brief(self, state):
        return {
            "titulo": "Resumen Consejo de Administracion",
            "indicadores": {
                "health_score": state.get("health_score", 0),
                "disponibilidad": state.get("availability_pct", 100),
                "mttr": state.get("mttr_ms", 0),
                "incidentes": state.get("incidents_count", 0),
                "rollbacks": state.get("rollbacks_executed", 0),
                "self_healing_acciones": state.get("automatic_actions", 0),
                "servicios_degradados": len([s for s in state.get("services", []) if s.get("status") != "OK"]),
            },
            "riesgos": [a.get("message", "") for a in state.get("alerts", [])[:5]],
        }

    def get_latest(self):
        if not self._reports:
            return self.generate()
        return self._reports[-1]

    def get_history(self, limit=10):
        return list(reversed(list(self._reports)))[:limit]

    def export_json(self):
        return self.get_latest()

executive_reporter = ExecutiveReporter()