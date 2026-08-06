# core/customer/customer_portal.py v1.0
import os,logging
from datetime import datetime,timezone
logger=logging.getLogger("mesan.customer")
class CustomerPortal:
    def __init__(self):self.version="1.0.0"
    def get_dashboard(self,tenant_id="public_diagnostic"):
        guardian=self._get_guardian();billing=self._get_billing()
        return{"timestamp":datetime.now(timezone.utc).isoformat(),"version":self.version,"tenant_id":tenant_id,"guardian":{"health":guardian.get("health_score",0),"status":guardian.get("health_status","--"),"alerts":guardian.get("alerts_count",0)},"subscription":billing,"recommendations":["Ejecutar diagnostico completo","Activar Guardian Omega","Revisar exposicion fiscal"]}
    def _get_guardian(self):
        try:
            from core.jarvis.guardian_integration import guardian_integration
            return guardian_integration.get_state()
        except:return{}
    def _get_billing(self):
        try:
            from core.billing.subscription_engine import subscription_engine
            m=subscription_engine.get_metrics()
            return{"plan":"Guardian" if m.get("active_subscriptions",0)>0 else "Free","status":"ACTIVE" if m.get("active_subscriptions",0)>0 else "INACTIVE","mrr":m.get("mrr_mxn",0)}
        except:return{"plan":"Free","status":"INACTIVE","mrr":0}
customer_portal=CustomerPortal()