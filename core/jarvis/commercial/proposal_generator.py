# core/jarvis/commercial/proposal_generator.py -- MESAN Omega Proposal Generator v1.0
import logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.commercial.proposals")

class ProposalGenerator:
    def __init__(self):
        self.version = "1.0.0"
        self._proposals = []
        logger.info("[Proposals] v%s iniciado", self.version)

    def generate(self, lead, scoring, strategy, omega_result=None):
        plan = strategy.get("recommended_plan", {})
        proposal = {
            "id": "PROP-{}".format(int(datetime.now(timezone.utc).timestamp())),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "empresa": lead.get("empresa", ""),
            "contacto": lead.get("nombre", ""),
            "sector": lead.get("sector", ""),
            "executive_summary": self._exec_summary(lead, omega_result),
            "diagnostico": self._diagnostico(omega_result),
            "plan_recomendado": plan,
            "precio": plan.get("precio", 0),
            "moneda": plan.get("moneda", "MXN"),
            "roi": self._calc_roi(plan, omega_result),
            "beneficios": strategy.get("benefits", []),
            "argumentos": strategy.get("arguments", []),
            "cronograma": self._cronograma(plan),
            "status": "GENERATED",
        }
        self._proposals.append(proposal)
        return proposal

    def _exec_summary(self, lead, omega):
        empresa = lead.get("empresa", "la empresa")
        if omega:
            nivel = omega.get("nivel", "")
            score = omega.get("omega_score", omega.get("score", 0))
            return "MESAN Omega ha identificado un nivel de riesgo {} para {} con un score de {}. Se recomienda accion inmediata.".format(nivel, empresa, score)
        return "MESAN Omega ofrece un diagnostico integral de riesgo para {}.".format(empresa)

    def _diagnostico(self, omega):
        if not omega: return {"disponible": False}
        return {
            "disponible": True,
            "omega_score": omega.get("omega_score", omega.get("score", 0)),
            "nivel": omega.get("nivel", ""),
            "exposicion": omega.get("exposure_mxn", 0),
            "esi": omega.get("esi", 0),
            "dias_supervivencia": omega.get("dias_supervivencia", 0),
        }

    def _calc_roi(self, plan, omega):
        precio = plan.get("precio", 0)
        if not precio or not omega: return {"calculable": False}
        exposure = omega.get("exposure_mxn", 0)
        if exposure > 0:
            roi = round((exposure - precio) / max(precio, 1) * 100, 1)
            return {"roi_pct": roi, "ahorro_potencial": exposure, "inversion": precio}
        return {"calculable": False}

    def _cronograma(self, plan):
        name = plan.get("nombre", "")
        if "Guardian" in name:
            return [{"semana":1,"actividad":"Onboarding y configuracion"},{"semana":2,"actividad":"Primer ciclo Guardian activo"},{"semana":3,"actividad":"Executive Briefing inicial"},{"semana":4,"actividad":"Monitoreo continuo establecido"}]
        if "Enterprise" in name:
            return [{"semana":1,"actividad":"Discovery y configuracion"},{"semana":2,"actividad":"War Room activo"},{"semana":3,"actividad":"Digital Twin operativo"},{"semana":4,"actividad":"Comite ejecutivo inaugural"}]
        return [{"dia":1,"actividad":"Diagnostico ejecutado"},{"dia":2,"actividad":"Resultados entregados"},{"dia":3,"actividad":"Plan de accion presentado"}]

    def get_proposals(self, limit=20):
        return list(reversed(self._proposals[-limit:]))

proposal_generator = ProposalGenerator()