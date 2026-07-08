# core/jarvis_sales/lead_classifier.py -- MESAN Omega JARVIS Sales v1.0
from __future__ import annotations
import logging
from core.jarvis_sales.models import LeadProfile, LeadScore, LeadTemperature
from core.jarvis_sales.sales_rules import sales_rules
logger = logging.getLogger("mesan.sales.classifier")

class LeadClassifier:
    def classify(self, profile: LeadProfile, score: LeadScore) -> LeadTemperature:
        s = score.lead_score
        if s >= 75:
            return LeadTemperature.HOT
        if profile.nivel_riesgo in ("CRITICO","EXTREMO") and profile.diagnostico_hecho:
            return LeadTemperature.HOT
        if s >= 45 or profile.diagnostico_hecho or profile.impacto_estimado >= 100000:
            return LeadTemperature.WARM
        return LeadTemperature.COLD

lead_classifier = LeadClassifier()
