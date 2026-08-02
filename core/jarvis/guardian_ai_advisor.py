# core/jarvis/guardian_ai_advisor.py -- MESAN Omega Guardian AI Advisor v1.0
"""
Asesor inteligente que responde preguntas sobre el estado del sistema.
Genera respuestas basadas en datos reales de telemetria y Guardian.
"""
import logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.guardian.advisor")

class GuardianAIAdvisor:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[AIAdvisor] v%s iniciado", self.version)

    def ask(self, question):
        q = question.lower()
        try:
            from core.jarvis.guardian_integration import guardian_integration
            state = guardian_integration.get_state()
        except Exception:
            state = {}
        if "health" in q or "score" in q or "bajo" in q:
            return self._why_health_low(state)
        if "incidente" in q or "provoc" in q or "caus" in q:
            return self._incident_cause(state)
        if "recomend" in q or "accion" in q or "hacer" in q:
            return self._recommended_action(state)
        if "impacto" in q or "econom" in q or "costo" in q:
            return self._economic_impact(state)
        if "no se corrige" in q or "pasara" in q or "futuro" in q:
            return self._future_risk(state)
        return self._general_status(state)

    def _why_health_low(self, state):
        health = state.get("health_score", 0)
        alerts = state.get("alerts", [])
        services = state.get("services_guardian", [])
        degraded = [s for s in services if s.get("status") != "OK"]
        reasons = [a.get("message", "") for a in alerts[:3]]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Por que bajo el Health Score?",
            "answer": "El Health Score actual es {}. ".format(health) +
                      ("Servicios degradados: {}. ".format(", ".join([s.get("service", "?") for s in degraded])) if degraded else "Todos los servicios OK. ") +
                      ("Alertas activas: {}".format("; ".join(reasons)) if reasons else "Sin alertas criticas."),
            "health_score": health,
            "degraded_services": [s.get("service") for s in degraded],
            "alerts": reasons,
        }

    def _incident_cause(self, state):
        incidents = state.get("incidents", [])
        if not incidents:
            return {"answer": "No hay incidentes activos.", "incidents": 0}
        latest = incidents[0]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Que servicio provoco el incidente?",
            "answer": "Ultimo incidente: {} - {}".format(latest.get("service", "?"), latest.get("title", latest.get("description", "?"))),
            "incident": latest,
        }

    def _recommended_action(self, state):
        alerts = state.get("alerts", [])
        health = state.get("health_score", 0)
        if health >= 90:
            action = "Mantener monitoreo. Sistema operando de forma optima."
        elif health >= 70:
            action = "Revisar alertas menores. No se requiere accion inmediata."
        elif health >= 50:
            action = "Atencion requerida. Revisar servicios degradados y ejecutar diagnostico."
        else:
            action = "ACCION INMEDIATA. Activar War Room y ejecutar plan de recuperacion."
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Cual es la accion recomendada?",
            "answer": action,
            "health_score": health,
            "active_alerts": len(alerts),
        }

    def _economic_impact(self, state):
        health = state.get("health_score", 0)
        incidents = state.get("incidents_count", 0)
        avail = state.get("availability_pct", 100)
        downtime_cost_per_hour = 5000
        estimated_downtime_hours = max((100 - avail) / 100 * 24, 0)
        impact = round(estimated_downtime_hours * downtime_cost_per_hour, 2)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Cual es el impacto economico?",
            "answer": "Impacto estimado: ${:,.2f} MXN basado en {}% disponibilidad y {} incidentes.".format(impact, avail, incidents),
            "estimated_impact_mxn": impact,
            "availability_pct": avail,
            "incidents": incidents,
        }

    def _future_risk(self, state):
        health = state.get("health_score", 0)
        trend = state.get("health_trend", [])
        if health < 50:
            forecast = "CRITICO: sin correccion, el sistema podria experimentar fallas graves en las proximas horas."
        elif health < 70:
            forecast = "ATENCION: la tendencia indica degradacion progresiva. Corregir en las proximas 24-48 horas."
        else:
            forecast = "ESTABLE: no se anticipan fallas inmediatas. Mantener monitoreo preventivo."
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Que ocurrira si no se corrige?",
            "answer": forecast,
            "health_score": health,
            "trend_points": len(trend),
        }

    def _general_status(self, state):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": "Estado general",
            "answer": "Health Score: {}. Estado: {}. Disponibilidad: {}%.".format(
                state.get("health_score", 0),
                state.get("health_status", "UNKNOWN"),
                state.get("availability_pct", 100),
            ),
            "health_score": state.get("health_score", 0),
            "status": state.get("health_status", "UNKNOWN"),
        }

guardian_advisor = GuardianAIAdvisor()