# core/jarvis/commercial/lead_qualification.py -- MESAN Omega Lead Qualification v1.0
import logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.commercial.qualification")

class LeadQualificationEngine:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[LeadQualification] v%s iniciado", self.version)

    def qualify(self, lead, scoring_result):
        score = scoring_result.get("score", 0)
        classification = scoring_result.get("classification", "COLD")
        actions = []
        if classification == "HOT":
            actions = ["contacto_inmediato", "propuesta_automatica", "warroom_comercial", "notificacion_urgente"]
        elif classification == "WARM":
            actions = ["seguimiento_dia1", "propuesta_programada", "nurturing"]
        elif classification == "COLD":
            actions = ["seguimiento_dia7", "contenido_educativo"]
        else:
            actions = ["archivar", "reactivar_30dias"]
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lead_id": lead.get("id", "unknown"),
            "classification": classification,
            "score": score,
            "priority": scoring_result.get("priority", "P4"),
            "recommended_actions": actions,
            "auto_followup": classification in ("HOT", "WARM"),
            "auto_proposal": classification == "HOT",
        }

lead_qualification = LeadQualificationEngine()