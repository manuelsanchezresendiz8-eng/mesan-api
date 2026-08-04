# core/jarvis/commercial/commercial_metrics.py -- MESAN Omega Commercial Metrics v1.0
import os, logging
from datetime import datetime, timezone
logger = logging.getLogger("mesan.commercial.metrics")

class CommercialMetrics:
    def __init__(self):
        self.version = "1.0.0"
        logger.info("[CommercialMetrics] v%s iniciado", self.version)

    def calculate(self):
        leads = self._get_lead_stats()
        billing = self._get_billing()
        total = leads.get("total", 0)
        won = leads.get("cerrado_ganado", 0)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "leads": leads,
            "conversion_rate": round(won / max(total, 1) * 100, 2),
            "mrr": billing.get("mrr_mxn", 0),
            "arr": billing.get("arr_mxn", 0),
            "active_subscriptions": billing.get("active_subscriptions", 0),
            "cac": 0,
            "ltv": 0,
            "ltv_cac_ratio": 0,
            "avg_deal_value": billing.get("mrr_mxn", 0),
            "forecast_30d": billing.get("mrr_mxn", 0) * 1.1,
        }

    def _get_lead_stats(self):
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leads")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM leads WHERE estatus='nuevo'")
            nuevo = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM leads WHERE fecha::date = CURRENT_DATE")
            today = cur.fetchone()[0]
            cur.close(); conn.close()
            return {"total": total, "nuevos": nuevo, "hoy": today, "cerrado_ganado": 0}
        except Exception as e:
            logger.error("[Metrics] DB: %s", e)
            return {"total": 0, "nuevos": 0, "hoy": 0, "cerrado_ganado": 0}

    def _get_billing(self):
        try:
            from core.billing.subscription_engine import subscription_engine
            return subscription_engine.get_metrics()
        except Exception:
            return {"mrr_mxn": 0, "arr_mxn": 0, "active_subscriptions": 0}

commercial_metrics = CommercialMetrics()