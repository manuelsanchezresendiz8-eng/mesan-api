# core/jarvis/watchdog.py -- MESAN Omega Watchdog v1.0
import logging
from datetime import datetime, timezone
from core.jarvis.recovery_actions import recovery_actions
logger = logging.getLogger("mesan.selfhealing.watchdog")
class Watchdog:
    def __init__(self):
        self._rules = [
            {"id":"R001","condition":"api_500_streak","threshold":3,"severity":"CRITICAL","action":"retry_api","desc":"Render 500 x3"},
            {"id":"R002","condition":"db_offline","threshold":1,"severity":"CRITICAL","action":"reconnect_database","desc":"DB offline"},
            {"id":"R003","condition":"redis_offline","threshold":1,"severity":"HIGH","action":"clear_cache","desc":"Redis offline"},
            {"id":"R004","condition":"claude_timeout","threshold":1,"severity":"HIGH","action":"retry_ai_claude","desc":"Claude timeout"},
            {"id":"R005","condition":"openai_timeout","threshold":1,"severity":"HIGH","action":"retry_ai_openai","desc":"OpenAI timeout"},
            {"id":"R006","condition":"stripe_offline","threshold":1,"severity":"CRITICAL","action":"safe_mode_payments","desc":"Stripe offline"},
            {"id":"R007","condition":"supabase_offline","threshold":1,"severity":"HIGH","action":"reconnect_database","desc":"Supabase offline"},
        ]
        self._triggered = []
    def evaluate(self, metrics):
        results = []
        svcs = metrics.get("services", [])
        evts = metrics.get("recent_events", [])
        for rule in self._rules:
            if self._check(rule, svcs, evts):
                r = self._exec(rule)
                results.append(r)
                self._triggered.append(r)
        return results
    def _check(self, rule, svcs, evts):
        c = rule["condition"]
        if c == "api_500_streak":
            return len([e for e in evts if e.get("service")=="API" and e.get("status")=="ERROR"]) >= rule["threshold"]
        if c == "db_offline":
            db = next((s for s in svcs if s.get("service")=="PostgreSQL"), None)
            return db and db.get("status")=="OFFLINE"
        if c == "claude_timeout":
            return len([e for e in evts if "claude" in e.get("source","").lower() and e.get("status")!="OK"]) >= rule["threshold"]
        if c == "openai_timeout":
            return len([e for e in evts if "openai" in e.get("source","").lower() and e.get("status")!="OK"]) >= rule["threshold"]
        if c == "stripe_offline":
            s = next((s for s in svcs if s.get("service")=="Stripe"), None)
            return s and s.get("status")=="OFFLINE"
        if c == "redis_offline":
            s = next((s for s in svcs if s.get("service")=="Redis"), None)
            return s and s.get("status")=="OFFLINE"
        if c == "supabase_offline":
            s = next((s for s in svcs if s.get("service")=="Supabase"), None)
            return s and s.get("status")=="OFFLINE"
        return False
    def _exec(self, rule):
        a = rule["action"]
        if a == "retry_api": r = recovery_actions.retry_api("/health")
        elif a == "reconnect_database": r = recovery_actions.reconnect_database()
        elif a == "clear_cache": r = recovery_actions.clear_cache()
        elif a == "retry_ai_claude": r = recovery_actions.retry_ai("claude")
        elif a == "retry_ai_openai": r = recovery_actions.retry_ai("openai")
        elif a == "safe_mode_payments": r = recovery_actions.activate_safe_mode("stripe")
        else: r = {"status":"UNKNOWN"}
        logger.info("[Watchdog] %s triggered -> %s", rule["id"], r.get("status"))
        return {"timestamp":datetime.now(timezone.utc).isoformat(),"rule_id":rule["id"],"condition":rule["condition"],"severity":rule["severity"],"action":a,"result":r}
    def get_history(self, limit=20):
        return list(reversed(self._triggered[-limit:]))
    def get_rules(self):
        return self._rules
watchdog = Watchdog()