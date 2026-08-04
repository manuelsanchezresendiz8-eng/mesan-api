# core/jarvis/commercial/sales_strategy.py -- MESAN Omega Sales Strategy v1.0
import logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.commercial.strategy")

PLANS = {
    "diagnostico": {"nombre":"Diagnostico Ejecutivo","precio":299,"moneda":"MXN"},
    "guardian": {"nombre":"Guardian Omega","precio":999,"moneda":"MXN/mes"},
    "enterprise": {"nombre":"War Room Enterprise","precio":0,"moneda":"Personalizado"},
}

class SalesStrategyEngine:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[SalesStrategy] v%s iniciado", self.version)

    def recommend(self, lead, scoring_result, omega_result=None):
        score = scoring_result.get("score", 0)
        classification = scoring_result.get("classification", "COLD")
        sector = lead.get("sector", "")
        empleados = lead.get("empleados", "")
        plan = self._recommend_plan(score, empleados, omega_result)
        arguments = self._build_arguments(sector, omega_result)
        risks = self._highlight_risks(omega_result)
        benefits = self._build_benefits(plan)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommended_plan": plan,
            "how_to_sell": "consultivo" if score >= 60 else "educativo",
            "arguments": arguments,
            "risks_to_highlight": risks,
            "benefits": benefits,
            "urgency": "ALTA" if classification == "HOT" else "MEDIA" if classification == "WARM" else "BAJA",
            "estimated_close_days": 3 if classification == "HOT" else 14 if classification == "WARM" else 30,
        }

    def _recommend_plan(self, score, empleados, omega):
        if omega and omega.get("war_room_required"):
            return PLANS["enterprise"]
        if score >= 70 or (empleados and "500" in str(empleados)):
            return PLANS["guardian"]
        return PLANS["diagnostico"]

    def _build_arguments(self, sector, omega):
        args = ["Prevencion de riesgos antes de que generen perdidas"]
        if sector in ("Manufactura","Construccion","Maquila"):
            args.append("Cumplimiento REPSE, STPS e IMSS automatizado")
        if sector in ("Financiero","Tecnologia"):
            args.append("Gobierno corporativo y compliance continuo")
        if omega:
            exp = omega.get("exposure_mxn", 0)
            if exp > 0:
                args.append("Exposicion actual detectada: ${:,.0f} MXN".format(exp))
        return args

    def _highlight_risks(self, omega):
        if not omega: return ["Riesgos fiscales y laborales no monitoreados"]
        risks = []
        nivel = omega.get("nivel", "")
        if nivel in ("CRITICO","ALTO"):
            risks.append("Nivel de riesgo {}: accion inmediata requerida".format(nivel))
        predictive = omega.get("predictive", {}).get("result", {})
        for r in predictive.get("riesgos", [])[:3]:
            risks.append("{}: impacto ${:,.0f}".format(r.get("nombre",""), r.get("impacto_estimado",0)))
        return risks or ["Sin riesgos criticos detectados"]

    def _build_benefits(self, plan):
        name = plan.get("nombre", "")
        if "Guardian" in name:
            return ["Monitoreo 24/7","Alertas automaticas","Executive Briefing","JARVIS Advisor"]
        if "Enterprise" in name:
            return ["War Room dedicado","Digital Twin","Simulacion estrategica","Comite ejecutivo"]
        return ["Diagnostico completo en minutos","Score Omega","Plan de accion CEO"]

sales_strategy = SalesStrategyEngine()