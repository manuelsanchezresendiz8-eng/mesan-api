# core/jarvis/self_healing_engine.py -- MESAN Omega Self-Healing v1.0
import logging
from datetime import datetime, timezone
from core.jarvis.telemetry_engine import telemetry_engine
from core.jarvis.watchdog import watchdog
from core.jarvis.recovery_actions import recovery_actions
logger = logging.getLogger("mesan.selfhealing")
class GuardianSelfHealingEngine:
    def __init__(self):
        self.version = "1.0.0"
        self._status = "READY"
        self._executed_count = 0
        self._failed_count = 0
        self._last_action = None
        self._queue = []
        logger.info("[SelfHealing] v%s iniciado", self.version)
    def analyze(self):
        snapshot = telemetry_engine.get_dashboard_snapshot()
        triggered = watchdog.evaluate(snapshot)
        for result in triggered:
            s = result.get("result",{}).get("status","UNKNOWN")
            if s in ("OK","SIMULATED","QUEUED","ACTIVATED","SAFE_MODE"):
                self._executed_count += 1
            else:
                self._failed_count += 1
            self._last_action = result
        self._status = "ACTIVE" if triggered else "READY"
        if triggered:
            telemetry_engine.log_guardian("Self-Healing ejecuto {} acciones".format(len(triggered)), severity="WARNING")
        return {"timestamp":datetime.now(timezone.utc).isoformat(),"status":self._status,"actions_triggered":len(triggered),"details":triggered}
    def execute_action(self, action_type, target=""):
        if action_type == "retry_api": r = recovery_actions.retry_api(target or "/health")
        elif action_type == "reconnect_database": r = recovery_actions.reconnect_database()
        elif action_type == "clear_cache": r = recovery_actions.clear_cache()
        elif action_type == "restart_service": r = recovery_actions.restart_service(target)
        elif action_type == "retry_ai": r = recovery_actions.retry_ai(target or "claude")
        elif action_type == "safe_mode": r = recovery_actions.activate_safe_mode(target or "payments")
        elif action_type == "rotate_keys": r = recovery_actions.rotate_keys(target)
        else: r = {"status":"UNKNOWN_ACTION"}
        s = r.get("status","UNKNOWN")
        if s in ("OK","SIMULATED","QUEUED","ACTIVATED"): self._executed_count += 1
        else: self._failed_count += 1
        self._last_action = {"timestamp":datetime.now(timezone.utc).isoformat(),"action":action_type,"target":target,"result":r}
        return self._last_action
    def generate_report(self):
        return {"timestamp":datetime.now(timezone.utc).isoformat(),"version":self.version,"status":self._status,"last_action":self._last_action,"executed":self._executed_count,"failed":self._failed_count,"queue":self._queue,"recovery_log":recovery_actions.get_log(10),"watchdog_history":watchdog.get_history(10)}
    def get_status(self):
        return {"status":self._status,"last_action":self._last_action.get("action","None") if self._last_action else "None","executed":self._executed_count,"failed":self._failed_count,"queue":self._queue}
self_healing_engine = GuardianSelfHealingEngine()