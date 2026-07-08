# core/jarvis_sales/lead_engine.py -- MESAN Omega JARVIS Sales v1.0
from __future__ import annotations
import logging, os
from typing import Any, Dict, List
from core.jarvis_sales.models import LeadProfile, SalesDecision, LeadTemperature, Sector
from core.jarvis_sales.lead_scoring import lead_scoring
from core.jarvis_sales.lead_classifier import lead_classifier
from core.jarvis_sales.lead_recommendation import lead_recommendation
logger = logging.getLogger("mesan.sales.engine")
LEAD_ENGINE_VERSION = "1.0.0"

class LeadEngine:
    def __init__(self):
        self.version = LEAD_ENGINE_VERSION
        logger.info("[LeadEngine] v%s inicializado", self.version)

    def analyze(self, profile: LeadProfile) -> SalesDecision:
        score = lead_scoring.score(profile)
        temperature = lead_classifier.classify(profile, score)
        recommendation = lead_recommendation.recommend(profile, score, temperature)
        logger.info("[LeadEngine] %s score=%.1f temp=%s action=%s",
                    profile.lead_id, score.lead_score, temperature.value, recommendation.action.value)
        return SalesDecision(lead_id=profile.lead_id, profile=profile, score=score,
                             temperature=temperature, recommendation=recommendation)

    def analyze_from_dict(self, data: Dict[str, Any]) -> SalesDecision:
        return self.analyze(self._dict_to_profile(data))

    def rank_leads(self, leads: List[LeadProfile]) -> List[SalesDecision]:
        decisions = [self.analyze(l) for l in leads]
        decisions.sort(key=lambda d: d.score.lead_score, reverse=True)
        return decisions

    def get_hot_leads(self, leads: List[LeadProfile]) -> List[SalesDecision]:
        return [d for d in self.rank_leads(leads) if d.temperature == LeadTemperature.HOT]

    def load_and_rank_from_db(self) -> List[SalesDecision]:
        return self.rank_leads([self._dict_to_profile(r) for r in self._load_from_db()])

    def summary(self, decisions: List[SalesDecision]) -> Dict[str, Any]:
        if not decisions: return {"total":0,"hot":0,"warm":0,"cold":0,"top_lead":None}
        hot  = sum(1 for d in decisions if d.temperature == LeadTemperature.HOT)
        warm = sum(1 for d in decisions if d.temperature.value == "WARM")
        cold = sum(1 for d in decisions if d.temperature.value == "COLD")
        top  = decisions[0]
        return {"total":len(decisions),"hot":hot,"warm":warm,"cold":cold,
                "avg_score":round(sum(d.score.lead_score for d in decisions)/len(decisions),1),
                "top_lead":top.to_dict(),"top_action":top.recommendation.action.value}

    def _load_from_db(self) -> List[Dict[str, Any]]:
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL",""))
            cur = conn.cursor()
            cur.execute("SELECT id,nombre,telefono,whatsapp,empleados,estatus,fecha,nombre_contacto,origen,fuente_detalle,nivel_riesgo,impacto_estimado,omega_score,created_at FROM leads WHERE estatus NOT IN ('descartado','cerrado') ORDER BY created_at DESC LIMIT 100")
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols,r)) for r in cur.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            logger.warning("[LeadEngine] DB error: %s", e)
            return []

    @staticmethod
    def _dict_to_profile(data: Dict[str, Any]) -> LeadProfile:
        omega = data.get("omega_score")
        nivel = data.get("nivel_riesgo") or data.get("clasificacion")
        impacto = float(data.get("impacto_estimado") or data.get("impacto_max") or 0)
        return LeadProfile(
            lead_id=str(data.get("id","")), nombre=data.get("nombre_contacto") or data.get("nombre",""),
            empresa=data.get("nombre") or data.get("empresa",""), telefono=data.get("telefono",""),
            whatsapp=data.get("whatsapp",""), sector=data.get("sector", Sector.OTRO.value),
            empleados=int(data.get("empleados") or 0), estatus=data.get("estatus","nuevo"),
            omega_score=float(omega) if omega else None, nivel_riesgo=nivel,
            impacto_estimado=impacto, diagnostico_hecho=bool(omega or nivel),
            contactos_previos=int(data.get("contactos_previos") or 0),
            dias_sin_contacto=int(data.get("dias_sin_contacto") or 0),
            origen=data.get("origen",""), fuente_detalle=data.get("fuente_detalle",""),
        )

    def _notify_crm(self, decision): pass  # TODO: Fase B
    def _trigger_guardian(self, error): pass  # TODO: Fase B

lead_engine = LeadEngine()
