# core/jarvis/commercial/commercial_scheduler.py v1.0
import os,logging,time,threading
from datetime import datetime,timezone
logger=logging.getLogger("mesan.commercial.scheduler")
class CommercialScheduler:
    def __init__(self):
        self.version="1.0.0";self._running=False;self._thread=None;self._cycle=0
        self._jobs={"check_leads":{"interval":900,"last":0,"fn":"_check_leads"},"recalc_scores":{"interval":3600,"last":0,"fn":"_recalc_scores"},"update_forecast":{"interval":14400,"last":0,"fn":"_update_forecast"},"daily_strategy":{"interval":86400,"last":0,"fn":"_daily_strategy"},"daily_brief":{"interval":86400,"last":0,"fn":"_daily_brief"},"schedule_content":{"interval":86400,"last":0,"fn":"_schedule_content"}}
    def start(self):
        if self._running:return{"status":"ALREADY_RUNNING"}
        self._running=True;self._thread=threading.Thread(target=self._loop,daemon=True);self._thread.start();return{"status":"STARTED"}
    def stop(self):self._running=False;return{"status":"STOPPED"}
    def _loop(self):
        while self._running:
            try:self.run_cycle()
            except Exception as e:logger.error("[CommScheduler] %s",e)
            time.sleep(10)
    def run_cycle(self):
        self._cycle+=1;now=time.time()
        for name,job in self._jobs.items():
            if now-job["last"]>=job["interval"]:
                try:
                    fn=getattr(self,job["fn"],None)
                    if fn:fn()
                    job["last"]=now
                except Exception as e:logger.error("[CommScheduler] %s: %s",name,e)
    def _check_leads(self):
        try:
            from core.jarvis.commercial.commercial_auto import commercial_auto
            commercial_auto.process_new_leads()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def _recalc_scores(self):
        try:
            from core.jarvis.commercial.commercial_auto import commercial_auto
            commercial_auto.recalc_all_scores()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def _update_forecast(self):
        try:
            from core.jarvis.commercial.commercial_metrics import commercial_metrics
            commercial_metrics.calculate()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def _daily_strategy(self):
        try:
            from core.jarvis.commercial.commercial_strategy_engine import strategy_engine
            strategy_engine.generate_daily()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def _daily_brief(self):
        try:
            from core.jarvis.commercial.commercial_auto import commercial_auto
            commercial_auto.generate_brief()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def _schedule_content(self):
        try:
            from core.jarvis.commercial.marketing_engine import marketing_engine
            marketing_engine.generate_daily_content()
        except Exception as e:logger.error("[CommScheduler] %s",e)
    def health_check(self):
        return{"status":"RUNNING" if self._running else "STOPPED","version":self.version,"cycle":self._cycle,"jobs":{k:{"interval":v["interval"],"last_run":v["last"]} for k,v in self._jobs.items()}}
commercial_scheduler=CommercialScheduler()