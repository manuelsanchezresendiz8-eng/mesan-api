# core/jarvis/commercial/followup_engine.py -- MESAN Omega Follow-Up Engine v1.0
import logging
from datetime import datetime, timezone, timedelta
from collections import deque
logger = logging.getLogger("mesan.commercial.followup")

FOLLOWUP_SCHEDULE = [
    {"day":1,"type":"bienvenida","channel":"whatsapp","message":"Gracias por solicitar su diagnostico. Nuestro equipo lo contactara en breve."},
    {"day":3,"type":"recordatorio","channel":"email","message":"Su diagnostico MESAN Omega esta listo. Le gustaria agendar una revision?"},
    {"day":7,"type":"valor","channel":"whatsapp","message":"Las empresas que actuan a tiempo reducen su exposicion fiscal hasta un 38%."},
    {"day":14,"type":"propuesta","channel":"email","message":"Preparamos una propuesta personalizada para su empresa. Desea revisarla?"},
    {"day":30,"type":"reactivacion","channel":"email","message":"Han pasado 30 dias desde su diagnostico. Las condiciones pueden haber cambiado."},
]

class FollowUpEngine:
    def __init__(self):
        self.version = "1.0.0"
        self._scheduled = deque(maxlen=1000)
        self._sent = deque(maxlen=1000)
        logger.info("[FollowUp] v%s iniciado", self.version)

    def schedule_for_lead(self, lead_id, classification):
        now = datetime.now(timezone.utc)
        scheduled = []
        steps = FOLLOWUP_SCHEDULE if classification in ("HOT","WARM") else FOLLOWUP_SCHEDULE[:2]
        for step in steps:
            entry = {
                "lead_id": lead_id,
                "scheduled_date": (now + timedelta(days=step["day"])).isoformat(),
                "day": step["day"],
                "type": step["type"],
                "channel": step["channel"],
                "message": step["message"],
                "status": "PENDING",
            }
            self._scheduled.append(entry)
            scheduled.append(entry)
        return {"lead_id": lead_id, "followups_scheduled": len(scheduled), "steps": scheduled}

    def get_pending(self):
        now = datetime.now(timezone.utc).isoformat()
        return [f for f in self._scheduled if f["status"] == "PENDING" and f["scheduled_date"] <= now]

    def mark_sent(self, lead_id, day):
        for f in self._scheduled:
            if f["lead_id"] == lead_id and f["day"] == day:
                f["status"] = "SENT"
                self._sent.append(f)
                return {"status": "MARKED_SENT"}
        return {"status": "NOT_FOUND"}

    def get_stats(self):
        return {
            "total_scheduled": len(self._scheduled),
            "total_sent": len(self._sent),
            "pending": len([f for f in self._scheduled if f["status"] == "PENDING"]),
        }

followup_engine = FollowUpEngine()