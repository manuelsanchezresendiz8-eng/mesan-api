# routes/shadow_mode_routes.py -- MESAN Omega Shadow Mode Comercial v1.0
import os,logging,time
from datetime import datetime,timezone
from collections import deque
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
router = APIRouter()
logger = logging.getLogger("mesan.shadow_mode")

class ShadowModeCommercial:
    def __init__(self):
        self.version = "1.0.0"
        self._active = False
        self._cycles = 0
        self._log = deque(maxlen=500)
        self._results = deque(maxlen=200)

    def run_cycle(self):
        self._cycles += 1
        results = []
        leads = self._fetch_new_leads()
        for lead in leads:
            r = self._process_lead(lead)
            results.append(r)
            self._results.append(r)
        entry = {"timestamp":datetime.now(timezone.utc).isoformat(),"cycle":self._cycles,"leads_found":len(leads),"processed":len(results),"results":results}
        self._log.append(entry)
        return entry

    def _fetch_new_leads(self):
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT id,nombre,empresa,correo,sector,empleados FROM leads ORDER BY created_at DESC LIMIT 20")
            rows = cur.fetchall()
            cur.close(); conn.close()
            return [{"id":str(r[0]),"nombre":r[1],"empresa":r[2],"correo":r[3],"sector":r[4],"empleados":r[5]} for r in rows]
        except:
            return []

    def _process_lead(self, lead):
        try:
            from core.jarvis.commercial.lead_scoring import lead_scoring
            from core.jarvis.commercial.lead_qualification import lead_qualification
            from core.jarvis.commercial.sales_strategy import sales_strategy
            from core.jarvis.commercial.followup_engine import followup_engine
            scoring = lead_scoring.score(lead)
            qualification = lead_qualification.qualify(lead, scoring)
            strategy = sales_strategy.recommend(lead, scoring)
            followup = followup_engine.schedule_for_lead(lead.get("id","?"), scoring["classification"])
            if scoring["classification"] == "HOT":
                try:
                    from core.jarvis.notification_center import notification_center
                    notification_center.notify("CRITICAL_ALERT","HIGH","SHADOW HOT LEAD: {} ({})".format(lead.get("empresa",""),scoring["score"]),{"lead_id":lead.get("id")})
                except: pass
            try:
                from core.jarvis.telemetry_engine import telemetry_engine
                telemetry_engine.log_guardian("Shadow processed: {} -> {} (Score:{})".format(lead.get("empresa",""),scoring["classification"],scoring["score"]))
            except: pass
            return {"lead_id":lead.get("id"),"empresa":lead.get("empresa"),"score":scoring["score"],"classification":scoring["classification"],"priority":scoring["priority"],"actions":qualification.get("recommended_actions",[]),"followup":True,"timestamp":datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            return {"lead_id":lead.get("id"),"error":str(e)}

    def get_status(self):
        return {"version":self.version,"active":self._active,"cycles":self._cycles,"total_processed":len(self._results),"recent_log":list(self._log)[-10:]}

    def activate(self):
        self._active = True
        return {"status":"ACTIVATED"}

    def deactivate(self):
        self._active = False
        return {"status":"DEACTIVATED"}

shadow_mode = ShadowModeCommercial()

@router.get("/commercial/shadow/status")
async def shadow_status(request: Request):
    try: return shadow_mode.get_status()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/commercial/shadow/run")
async def shadow_run(request: Request):
    try: return shadow_mode.run_cycle()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/commercial/shadow/activate")
async def shadow_activate(request: Request):
    try: return shadow_mode.activate()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/commercial/shadow/deactivate")
async def shadow_deactivate(request: Request):
    try: return shadow_mode.deactivate()
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})