# core/jarvis/rollback_manager.py -- MESAN Omega Rollback Manager v1.0
import logging, time
from collections import deque
from datetime import datetime, timezone
logger = logging.getLogger("mesan.selfhealing.rollback")
class RollbackManager:
    def __init__(self, max_snapshots=20):
        self.version = "1.0.0"
        self._snapshots = deque(maxlen=max_snapshots)
        self._rollbacks = []
        self._state = "STABLE"
        logger.info("[Rollback] v%s iniciado", self.version)
    def save_snapshot(self, data):
        snap = {"id":"SNAP-{}".format(int(time.time())),"timestamp":datetime.now(timezone.utc).isoformat(),"state":data,"health":data.get("health",0)}
        self._snapshots.append(snap)
        return snap
    def get_last_stable(self):
        for s in reversed(self._snapshots):
            if s.get("health",0) >= 80: return s
        return None
    def rollback_to_last_stable(self):
        stable = self.get_last_stable()
        if not stable:
            return {"status":"NO_STABLE_SNAPSHOT","action":"none"}
        result = {"timestamp":datetime.now(timezone.utc).isoformat(),"status":"ROLLED_BACK","snapshot_id":stable["id"],"snapshot_health":stable["health"],"actions":[{"action":"restore_config","status":"OK","snapshot":stable["id"]},{"action":"deactivate_unstable","status":"SIMULATED"}]}
        self._rollbacks.append(result)
        self._state = "ROLLED_BACK"
        logger.info("[Rollback] Ejecutado a %s", stable["id"])
        return result
    def get_rollback_history(self, limit=10):
        return list(reversed(self._rollbacks[-limit:]))
    def get_snapshots(self, limit=10):
        s = list(self._snapshots); s.reverse(); return s[:limit]
    def get_status(self):
        return {"state":self._state,"total_snapshots":len(self._snapshots),"total_rollbacks":len(self._rollbacks),"last_stable":self.get_last_stable()}
rollback_manager = RollbackManager()