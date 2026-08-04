# core/jarvis/commercial/commercial_orchestrator.py -- MESAN Omega Commercial Orchestrator v1.0
"""
Orquestador comercial autonomo. Cuando llega un lead:
Scoring -> Clasificacion -> Priorizacion -> Estrategia -> Propuesta -> Seguimiento -> Dashboard
"""
import logging
from datetime import datetime, timezone
from core.jarvis.commercial.lead_scoring import lead_scoring
from core.jarvis.commercial.lead_qualification import lead_qualification
from core.jarvis.commercial.sales_strategy import sales_strategy
from core.jarvis.commercial.followup_engine import followup_engine
from core.jarvis.commercial.proposal_generator import proposal_generator
from core.jarvis.commercial.commercial_metrics import commercial_metrics
from core.jarvis.commercial.sales_pipeline import sales_pipeline
logger = logging.getLogger("mesan.commercial.orchestrator")

class CommercialOrchestrator:
    def __init__(self):
        self.version = "1.0.0"
        self._processed = 0
        logger.info("[CommercialOrchestrator] v%s iniciado", self.version)

    def process_lead(self, lead, omega_result=None):
        self._processed += 1
        scoring_result = lead_scoring.score(lead, omega_result)
        qualification = lead_qualification.qualify(lead, scoring_result)
        strategy = sales_strategy.recommend(lead, scoring_result, omega_result)
        proposal = None
        if qualification.get("auto_proposal"):
            proposal = proposal_generator.generate(lead, scoring_result, strategy, omega_result)
        followup = followup_engine.schedule_for_lead(lead.get("id", "unknown"), scoring_result["classification"])
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lead_id": lead.get("id", "unknown"),
            "scoring": scoring_result,
            "qualification": qualification,
            "strategy": strategy,
            "proposal": proposal,
            "followup": followup,
            "processed_total": self._processed,
        }

    def get_dashboard(self):
        pipeline = sales_pipeline.get_pipeline()
        metrics = commercial_metrics.calculate()
        proposals = proposal_generator.get_proposals(5)
        followups = followup_engine.get_stats()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": self.version,
            "pipeline": pipeline,
            "metrics": metrics,
            "recent_proposals": proposals,
            "followups": followups,
            "leads_processed": self._processed,
        }

    def get_hot_leads(self):
        return sales_pipeline.get_hot()

    def get_forecast(self):
        metrics = commercial_metrics.calculate()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mrr_actual": metrics.get("mrr", 0),
            "arr_actual": metrics.get("arr", 0),
            "forecast_30d": metrics.get("forecast_30d", 0),
            "leads_total": metrics.get("leads", {}).get("total", 0),
            "conversion": metrics.get("conversion_rate", 0),
        }

commercial_orchestrator = CommercialOrchestrator()