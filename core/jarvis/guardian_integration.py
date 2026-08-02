# core/jarvis/guardian_integration.py -- MESAN Omega Guardian Integration Layer v1.0
import logging, time
from datetime import datetime, timezone
from core.jarvis.telemetry_engine import telemetry_engine
from core.jarvis.guardian_engine import guardian_engine
from core.jarvis.autonomous_orchestrator import autonomous_orchestrator
from core.jarvis.rollback_manager import rollback_manager
from core.jarvis.self_healing_engine import self_healing_engine
logger = logging.getLogger("mesan.guardian.integration")
class GuardianIntegrationLayer:
    def __init__(self):
        self.version = "1.0.0"
        self._last_cycle = None
        self._cycle_count = 0
        logger.info("[Integration] v%s iniciado", self.version)
    def execute_cycle(self):
        started = time.perf_counter()
        self._cycle_count += 1
        tel = telemetry_engine.build_metrics()
        gr = None
        try:
            report = guardian_engine.execute()
            gr = {"overall_score":report.overall_score,"status":report.status,"services":[s.__dict__ if hasattr(s,"__dict__") else s for s in report.services],"incidents_count":len(report.incidents),"incidents":report.incidents[:10],"alerts_count":len(report.alerts),"alerts":report.alerts[:10]}
        except Exception as e:
            gr = {"status":"ERROR","error":str(e)}
        orch = None
        try:
            autonomous_orchestrator.evaluate()
            orch = autonomous_orchestrator.build_report()
        except Exception as e:
            orch = {}
        dd = orch.get("dashboard",{})
        hs = None
        try: hs = self_healing_engine.get_status()
        except: hs = {"status":"ERROR"}
        elapsed = round((time.perf_counter()-started)*1000,2)
        self._last_cycle = {"timestamp":datetime.now(timezone.utc).isoformat(),"version":self.version,"cycle":self._cycle_count,"elapsed_ms":elapsed,"health_score":tel.get("health",0),"health_status":gr.get("status","UNKNOWN") if isinstance(gr,dict) else "UNKNOWN","services":tel.get("services",[]),"services_guardian":gr.get("services",[]) if isinstance(gr,dict) else [],"alerts":gr.get("alerts",[]) if isinstance(gr,dict) else [],"alerts_count":gr.get("alerts_count",0) if isinstance(gr,dict) else 0,"incidents":gr.get("incidents",[]) if isinstance(gr,dict) else [],"incidents_count":gr.get("incidents_count",0) if isinstance(gr,dict) else 0,"automatic_actions":dd.get("automatic_actions",0),"recovery_success_rate":dd.get("recovery_success_rate",100),"mttr_ms":dd.get("mttr_ms",0),"rollbacks_executed":dd.get("rollbacks_executed",0),"escalations_to_warroom":dd.get("escalations_to_warroom",0),"availability_pct":dd.get("availability_pct",100),"health_trend":dd.get("health_trend",[]),"self_healing":hs,"metrics":tel.get("metrics",{}),"uptime_seconds":tel.get("uptime_seconds",0),"total_requests":tel.get("total_requests",0),"total_errors":tel.get("total_errors",0)}
        telemetry_engine.log_guardian("Integration cycle #{} ({}ms)".format(self._cycle_count, elapsed))
        return self._last_cycle
    def get_state(self):
        if not self._last_cycle: return self.execute_cycle()
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(self._last_cycle["timestamp"])
            if time.time() - dt.timestamp() > 15: return self.execute_cycle()
        except: return self.execute_cycle()
        return self._last_cycle
guardian_integration = GuardianIntegrationLayer()