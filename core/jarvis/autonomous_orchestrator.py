# core/jarvis/autonomous_orchestrator.py -- MESAN Omega Autonomous Orchestrator v1.0
import logging, time
from collections import deque
from datetime import datetime, timezone
from core.jarvis.telemetry_engine import telemetry_engine
from core.jarvis.self_healing_engine import self_healing_engine
from core.jarvis.recovery_actions import recovery_actions
from core.jarvis.rollback_manager import rollback_manager
from core.jarvis.watchdog import watchdog
logger = logging.getLogger("mesan.guardian.orchestrator")
SEV = {"CRITICAL":40,"HIGH":30,"WARNING":15,"MEDIUM":15,"INFO":5}
class AutonomousOrchestrator:
    def __init__(self):
        self.version = "1.0.0"
        self._decisions = deque(maxlen=200)
        self._escalations = []
        self._mttr = deque(maxlen=100)
        self._total = 0
        self._success = 0
        self._avail = deque(maxlen=1000)
        logger.info("[Orchestrator] v%s iniciado", self.version)
    def evaluate(self):
        started = time.perf_counter()
        snap = telemetry_engine.get_dashboard_snapshot()
        rollback_manager.save_snapshot(snap)
        incidents = self._detect(snap)
        prioritized = self.prioritize(incidents)
        results = []
        for inc in prioritized:
            lvl = self._level(inc)
            r = self.execute(inc, lvl)
            v = self.verify(r)
            if not v["success"]:
                r2 = self.execute(inc, min(lvl+1,5))
                v2 = self.verify(r2)
                if not v2["success"]:
                    self._escalate(inc, [r, r2])
            results.append({"incident":inc,"level":lvl,"result":r,"verified":v})
        elapsed = round((time.perf_counter()-started)*1000,2)
        self._avail.append(1 if snap.get("health",0)>=80 else 0)
        dec = {"timestamp":datetime.now(timezone.utc).isoformat(),"elapsed_ms":elapsed,"incidents":len(incidents),"actions":len(results),"results":results}
        self._decisions.append(dec)
        return dec
    def prioritize(self, incidents):
        for i in incidents:
            s = SEV.get(i.get("severity","INFO"),5) + min(i.get("services_affected",1)*10,30)
            if i.get("ai_related"): s += 10
            if i.get("age_seconds",0)>300: s += 15
            elif i.get("age_seconds",0)>60: s += 10
            i["priority_score"] = min(s,100)
            i["priority_level"] = "P1" if s>=80 else "P2" if s>=60 else "P3" if s>=40 else "P4"
        return sorted(incidents, key=lambda x: x["priority_score"], reverse=True)
    def _level(self, inc):
        s = inc.get("priority_score",0)
        if s>=85: return 5
        if s>=70: return 4
        if s>=50: return 3
        if s>=20: return 2
        return 1
    def execute(self, inc, level):
        self._total += 1
        started = time.perf_counter()
        if level == 1:
            r = {"action":"LOG","status":"LOGGED"}
        elif level == 2:
            svc = inc.get("service","").lower()
            if "api" in svc: r = recovery_actions.retry_api("/health")
            elif "database" in svc or "postgresql" in svc: r = recovery_actions.reconnect_database()
            elif "ai" in svc or "claude" in svc: r = recovery_actions.retry_ai(svc)
            else: r = recovery_actions.clear_cache()
        elif level == 3:
            r = recovery_actions.activate_safe_mode(inc.get("service","unknown"))
        elif level == 4:
            r = self.rollback()
        elif level == 5:
            r = {"action":"ESCALATE","status":"ESCALATED"}
            self._escalate(inc, [])
        else:
            r = {"action":"UNKNOWN","status":"SKIPPED"}
        r["elapsed_ms"] = round((time.perf_counter()-started)*1000,2)
        r["level"] = level
        r["timestamp"] = datetime.now(timezone.utc).isoformat()
        return r
    def rollback(self):
        r = rollback_manager.rollback_to_last_stable()
        if r.get("status")=="ROLLED_BACK":
            telemetry_engine.log_guardian("ROLLBACK a snapshot {}".format(r.get("snapshot_id","?")), severity="CRITICAL")
        return r
    def verify(self, result):
        s = result.get("status","UNKNOWN")
        ok = s in ("OK","LOGGED","SIMULATED","QUEUED","ACTIVATED","SAFE_MODE","ROLLED_BACK")
        if ok:
            self._success += 1
            e = result.get("elapsed_ms",0)
            if e > 0: self._mttr.append(e)
        return {"success":ok,"status":s,"timestamp":datetime.now(timezone.utc).isoformat()}
    def _escalate(self, inc, attempts):
        esc = {"timestamp":datetime.now(timezone.utc).isoformat(),"incident":inc,"attempts":len(attempts),"status":"ESCALATED_TO_WARROOM"}
        self._escalations.append(esc)
        telemetry_engine.log_guardian("ESCALACION War Room: {}".format(inc.get("message","")), severity="CRITICAL")
    def _detect(self, snap):
        incidents = []
        for svc in snap.get("services",[]):
            if svc.get("status") not in ("OK","STARTING"):
                incidents.append({"id":"INC-{}".format(int(time.time())),"service":svc.get("service","?"),"severity":"CRITICAL" if svc.get("score",100)<30 else "HIGH","message":"{} en estado {}".format(svc.get("service"),svc.get("status")),"services_affected":1,"ai_related":svc.get("service")=="AI","age_seconds":0})
        if snap.get("health",100)<50:
            incidents.append({"id":"INC-H-{}".format(int(time.time())),"service":"System","severity":"CRITICAL","message":"Health critico: {}".format(snap.get("health")),"services_affected":len(snap.get("services",[])),"ai_related":False,"age_seconds":0})
        return incidents
    def build_report(self):
        sr = round(self._success/max(self._total,1)*100,2)
        mttr = round(sum(self._mttr)/max(len(self._mttr),1),2)
        av = list(self._avail)
        avail = round(sum(av)/max(len(av),1)*100,2) if av else 100.0
        return {"timestamp":datetime.now(timezone.utc).isoformat(),"version":self.version,"dashboard":{"recovery_success_rate":sr,"mttr_ms":mttr,"rollbacks_executed":len(rollback_manager.get_rollback_history()),"automatic_actions":self._total,"escalations_to_warroom":len(self._escalations),"availability_pct":avail,"health_trend":[{"timestamp":s["timestamp"],"health":s["health"]} for s in rollback_manager.get_snapshots(10)]},"rollback_status":rollback_manager.get_status(),"recent_decisions":list(reversed(list(self._decisions)))[:10],"escalations":self._escalations[-5:]}
autonomous_orchestrator = AutonomousOrchestrator()