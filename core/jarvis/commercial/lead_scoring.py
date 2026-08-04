# core/jarvis/commercial/lead_scoring.py -- MESAN Omega Lead Scoring v1.0
import logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.commercial.scoring")

SECTOR_WEIGHT = {"Manufactura":15,"Construccion":14,"Salud":13,"Financiero":12,"Logistica":11,"Tecnologia":10,"Servicios":9,"Retail":8,"Maquila":14,"Otro":7}
SIZE_WEIGHT = {"1 - 50 empleados":5,"51 - 200 empleados":10,"201 - 500 empleados":15,"501 - 1,000 empleados":18,"Mas de 1,000 empleados":20}

class LeadScoringEngine:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[LeadScoring] v%s iniciado", self.version)

    def score(self, lead, omega_result=None):
        s = 0
        s += SECTOR_WEIGHT.get(lead.get("sector",""), 5)
        s += SIZE_WEIGHT.get(lead.get("empleados",""), 5)
        if lead.get("correo","").endswith((".com",".mx",".com.mx")): s += 5
        if lead.get("whatsapp",""): s += 5
        if omega_result:
            omega_score = omega_result.get("omega_score", omega_result.get("score", 50))
            if omega_score < 40: s += 25
            elif omega_score < 60: s += 20
            elif omega_score < 80: s += 10
            exposure = omega_result.get("exposure_mxn", 0)
            if exposure > 500000: s += 15
            elif exposure > 200000: s += 10
            elif exposure > 50000: s += 5
            if omega_result.get("war_room_required"): s += 10
            esi = omega_result.get("esi", 100)
            if esi < 50: s += 15
            elif esi < 80: s += 8
        s = min(s, 100)
        return {"score": s, "classification": self._classify(s), "priority": self._priority(s), "timestamp": datetime.now(timezone.utc).isoformat()}

    def _classify(self, score):
        if score >= 70: return "HOT"
        if score >= 45: return "WARM"
        if score >= 20: return "COLD"
        return "LOST"

    def _priority(self, score):
        if score >= 80: return "P1"
        if score >= 60: return "P2"
        if score >= 40: return "P3"
        return "P4"

lead_scoring = LeadScoringEngine()