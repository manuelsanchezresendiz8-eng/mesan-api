# core/jarvis_sales/lead_recommendation.py -- MESAN Omega JARVIS Sales v1.0
from __future__ import annotations
import logging
from core.jarvis_sales.models import LeadProfile, LeadScore, LeadTemperature, LeadRecommendation, NextAction
logger = logging.getLogger("mesan.sales.recommendation")

def _close_prob(score, temperature):
    base = {"HOT":65.0,"WARM":35.0,"COLD":10.0}.get(temperature.value, 10.0)
    return round(min(95.0, base + score.lead_score * 0.3), 1)

class LeadRecommendationEngine:
    def recommend(self, profile, score, temperature) -> LeadRecommendation:
        action, reason, urgency = self._decide(profile, score, temperature)
        script = self._script(profile, action)
        prob = _close_prob(score, temperature)
        logger.info("[Recommendation] %s action=%s urgency=%s prob=%.1f%%", profile.lead_id, action.value, urgency, prob)
        return LeadRecommendation(lead_id=profile.lead_id, action=action, reason=reason,
                                   urgency=urgency, script=script, estimated_close_probability=prob)

    def _decide(self, profile, score, temperature):
        s = score.lead_score
        if temperature == LeadTemperature.HOT:
            if profile.dias_sin_contacto > 3:
                return NextAction.CALL_TODAY, f"HOT con {profile.dias_sin_contacto} dias sin contacto", "INMEDIATA"
            if profile.diagnostico_hecho:
                return NextAction.SEND_PROPOSAL, "Diagnostico listo — enviar propuesta", "ALTA"
            return NextAction.CALL_TODAY, f"HOT score {s:.0f} — contactar hoy", "INMEDIATA"
        if temperature == LeadTemperature.WARM:
            if not profile.diagnostico_hecho:
                return NextAction.CALL_TODAY, "WARM sin diagnostico — ofrecer diagnostico gratuito", "ALTA"
            if profile.contactos_previos >= 2:
                return NextAction.SCHEDULE_MEETING, f"WARM con {profile.contactos_previos} contactos — agendar reunion", "ALTA"
            return NextAction.FOLLOW_UP_7D, "WARM en etapa inicial — seguimiento 7 dias", "MEDIA"
        if profile.empleados >= 10 and not profile.diagnostico_hecho:
            return NextAction.CALL_TODAY, "COLD tamano relevante — intentar activar", "MEDIA"
        if s < 20:
            return NextAction.DISCARD, f"Score {s:.0f} muy bajo", "BAJA"
        return NextAction.FOLLOW_UP_30D, "COLD — revisar en 30 dias", "BAJA"

    def _script(self, profile, action):
        n = profile.nombre or "empresario"
        e = profile.empresa or "su empresa"
        if action == NextAction.CALL_TODAY:
            return f"Buenos dias {n}, le contacto de MESAN Omega. Detectamos que {e} podria tener exposicion fiscal y laboral. Tenemos un diagnostico gratuito de 5 minutos. Le cuento?"
        if action == NextAction.SEND_PROPOSAL:
            return f"Hola {n}, le envio la propuesta para {e} basada en el diagnostico. Incluye regularizacion en 30 dias. Podemos revisar esta semana?"
        if action == NextAction.SCHEDULE_MEETING:
            return f"Hola {n}, quisiera agendar 20 minutos para presentarle el plan para {e}. Que dia le queda mejor?"
        if action == NextAction.FOLLOW_UP_7D:
            return f"Hola {n}, seguimiento de MESAN Omega sobre {e}. Ha tenido oportunidad de revisar la informacion?"
        return ""

lead_recommendation = LeadRecommendationEngine()
