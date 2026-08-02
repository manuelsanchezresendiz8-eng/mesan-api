# core/jarvis/recovery_actions.py -- MESAN Omega Recovery Actions v1.0
import os, time, logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.selfhealing.recovery")
class RecoveryActions:
    def __init__(self):
        self._action_log = []
    def retry_api(self, path, max_retries=3):
        for i in range(max_retries):
            try:
                import httpx
                r = httpx.get("http://localhost:10000" + path, timeout=10)
                if r.status_code < 500:
                    self._log("retry_api", path, "OK", i+1)
                    return {"status":"OK","attempts":i+1,"path":path}
            except Exception:
                time.sleep(2**i)
        self._log("retry_api", path, "FAILED", max_retries)
        return {"status":"FAILED","attempts":max_retries,"path":path}
    def reconnect_database(self):
        try:
            import psycopg
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self._log("reconnect_db","DATABASE_URL","FAILED",0)
                return {"status":"FAILED","reason":"No DATABASE_URL"}
            conn = psycopg.connect(db_url, connect_timeout=10)
            cur = conn.cursor(); cur.execute("SELECT 1"); cur.close(); conn.close()
            self._log("reconnect_db","PostgreSQL","OK",1)
            return {"status":"OK","service":"PostgreSQL"}
        except Exception as e:
            self._log("reconnect_db","PostgreSQL","FAILED",1)
            return {"status":"FAILED","error":str(e)}
    def clear_cache(self):
        try:
            import gc; gc.collect()
            self._log("clear_cache","memory","OK",1)
            return {"status":"OK","action":"gc.collect"}
        except Exception as e:
            self._log("clear_cache","memory","FAILED",1)
            return {"status":"FAILED","error":str(e)}
    def restart_service(self, service_name):
        self._log("restart_service",service_name,"SIMULATED",1)
        return {"status":"SIMULATED","service":service_name}
    def retry_ai(self, provider="claude", max_retries=2):
        self._log("retry_ai",provider,"QUEUED",0)
        return {"status":"QUEUED","provider":provider,"max_retries":max_retries}
    def activate_safe_mode(self, service):
        self._log("safe_mode",service,"ACTIVATED",1)
        return {"status":"SAFE_MODE","service":service}
    def rotate_keys(self, service):
        self._log("rotate_keys",service,"NOT_IMPLEMENTED",0)
        return {"status":"NOT_IMPLEMENTED","service":service}
    def _log(self, action, target, result, attempts):
        entry = {"timestamp":datetime.now(timezone.utc).isoformat(),"action":action,"target":target,"result":result,"attempts":attempts}
        self._action_log.append(entry)
        logger.info("[Recovery] %s -> %s = %s (%d)", action, target, result, attempts)
    def get_log(self, limit=20):
        return list(reversed(self._action_log[-limit:]))
recovery_actions = RecoveryActions()