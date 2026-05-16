# core/risk_engine.py — MESAN Ω v2.5.0

from datetime import datetime, timedelta
from .rules import RULES


class RiskEngine:

    def evaluate(self, event_type: str) -> dict:
        if event_type not in RULES:
            return {"error": f"Evento '{event_type}' no reconocido"}

        rule = RULES[event_type]
        now = datetime.now()

        return {
            "event_type": event_type,
            "descripcion": rule["descripcion"],
            "risk_level": rule["risk_level"],
            "actions": {
                "imss_deadline": (now + timedelta(days=rule["imss_action_days"])).strftime("%Y-%m-%d"),
                "sat_action": rule["sat_action"],
                "imss_dias": rule["imss_action_days"]
            },
            "audit_projection": {
                "ventana_dias": rule["audit_window_days"],
                "fecha_limite": (now + timedelta(days=rule["audit_window_days"])).strftime("%Y-%m-%d")
            },
            "evaluado_en": now.strftime("%Y-%m-%d %H:%M")
        }

    def evaluate_multiple(self, event_types: list) -> list:
        return [self.evaluate(e) for e in event_types if e in RULES]

    def get_highest_risk(self, event_types: list) -> str:
        priority = {"CRITICO": 3, "ALTO": 2, "MEDIO": 1, "BAJO": 0}
        highest = "BAJO"
        for e in event_types:
            if e in RULES:
                nivel = RULES[e]["risk_level"]
                if priority.get(nivel, 0) > priority.get(highest, 0):
                    highest = nivel
        return highest
