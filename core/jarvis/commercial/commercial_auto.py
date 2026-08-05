# core/jarvis/commercial/commercial_auto.py v1.0
import os,logging
from datetime import datetime,timezone
logger=logging.getLogger("mesan.commercial.auto")
class CommercialAuto:
    def __init__(self):self.version="1.0.0";self._processed=0;self._hot=0
    def process_new_leads(self):
        leads=self._fetch_new();results=[]
        for lead in leads:results.append(self.process_single(lead))
        return{"processed":len(results)}
    def process_single(self,lead,omega_result=None):
        self._processed+=1
        from core.jarvis.commercial.lead_scoring import lead_scoring
        from core.jarvis.commercial.lead_qualification import lead_qualification
        from core.jarvis.commercial.sales_strategy import sales_strategy
        from core.jarvis.commercial.followup_engine import followup_engine
        from core.jarvis.commercial.proposal_generator import proposal_generator
        scoring=lead_scoring.score(lead,omega_result)
        qual=lead_qualification.qualify(lead,scoring)
        strat=sales_strategy.recommend(lead,scoring,omega_result)
        proposal=None
        if qual.get("auto_proposal"):proposal=proposal_generator.generate(lead,scoring,strat,omega_result)
        followup_engine.schedule_for_lead(lead.get("id","unknown"),scoring["classification"])
        if scoring["classification"]=="HOT":self._hot+=1;self._notify_hot(lead,scoring)
        return{"lead_id":lead.get("id"),"scoring":scoring,"qualification":qual,"strategy":strat,"proposal":proposal is not None,"timestamp":datetime.now(timezone.utc).isoformat()}
    def process_from_execute(self,lead_data,omega_result):
        lead={"id":lead_data.get("id","exec-{}".format(int(datetime.now(timezone.utc).timestamp()))),"nombre":lead_data.get("nombre",""),"empresa":lead_data.get("empresa",""),"correo":lead_data.get("correo",lead_data.get("email","")),"sector":lead_data.get("sector",""),"empleados":lead_data.get("empleados","")}
        return self.process_single(lead,omega_result)
    def recalc_all_scores(self):
        leads=self._fetch_all()
        from core.jarvis.commercial.lead_scoring import lead_scoring
        return{"recalculated":len(leads),"results":[{"id":l.get("id"),"score":lead_scoring.score(l)["score"]} for l in leads]}
    def generate_brief(self):
        from core.jarvis.commercial.commercial_metrics import commercial_metrics
        from core.jarvis.commercial.sales_pipeline import sales_pipeline
        m=commercial_metrics.calculate();p=sales_pipeline.get_pipeline()
        return{"timestamp":datetime.now(timezone.utc).isoformat(),"type":"COMMERCIAL_BRIEF","total_leads":m.get("leads",{}).get("total",0),"nuevos":m.get("leads",{}).get("nuevos",0),"conversion":m.get("conversion_rate",0),"mrr":m.get("mrr",0),"hot_today":self._hot,"processed_today":self._processed,"pipeline":p.get("stages",{})}
    def _notify_hot(self,lead,scoring):
        try:
            from core.jarvis.notification_center import notification_center
            notification_center.notify("CRITICAL_ALERT","HIGH","HOT LEAD: {} - {} (Score:{})".format(lead.get("nombre",""),lead.get("empresa",""),scoring["score"]),{"lead_id":lead.get("id")})
        except:pass
    def _fetch_new(self):
        try:
            import psycopg
            conn=psycopg.connect(os.getenv("DATABASE_URL"),connect_timeout=5);cur=conn.cursor()
            cur.execute("SELECT id,nombre,empresa,correo,telefono,sector,empleados FROM leads WHERE estatus IS NULL OR estatus='nuevo' ORDER BY created_at DESC LIMIT 50")
            rows=cur.fetchall();cur.close();conn.close()
            return[{"id":str(r[0]),"nombre":r[1],"empresa":r[2],"correo":r[3],"telefono":r[4],"sector":r[5],"empleados":r[6]} for r in rows]
        except:return[]
    def _fetch_all(self):
        try:
            import psycopg
            conn=psycopg.connect(os.getenv("DATABASE_URL"),connect_timeout=5);cur=conn.cursor()
            cur.execute("SELECT id,nombre,empresa,correo,telefono,sector,empleados FROM leads ORDER BY created_at DESC LIMIT 100")
            rows=cur.fetchall();cur.close();conn.close()
            return[{"id":str(r[0]),"nombre":r[1],"empresa":r[2],"correo":r[3],"telefono":r[4],"sector":r[5],"empleados":r[6]} for r in rows]
        except:return[]
    def get_status(self):return{"version":self.version,"processed":self._processed,"hot":self._hot}
commercial_auto=CommercialAuto()