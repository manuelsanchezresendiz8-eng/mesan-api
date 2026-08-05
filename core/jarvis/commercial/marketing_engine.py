# core/jarvis/commercial/marketing_engine.py v1.0
import logging
from datetime import datetime,timezone
from collections import deque
logger=logging.getLogger("mesan.commercial.marketing")
TEMPLATES={"linkedin":[{"tema":"riesgo_fiscal","titulo":"El 67% de las PyMEs mexicanas tienen contingencias fiscales sin detectar","cta":"Solicita tu diagnostico"},{"tema":"compliance","titulo":"REPSE, IMSS, SAT: tu empresa cumple al 100%?","cta":"Descubrelo en 5 minutos"},{"tema":"guardian","titulo":"Monitoreo 24/7 de riesgos empresariales","cta":"Conoce Guardian Omega"},{"tema":"caso_exito","titulo":"Empresa manufacturera redujo riesgo operativo 38%","cta":"Lee el caso"}],"facebook":[{"tema":"diagnostico","titulo":"Conoce el nivel real de riesgo de tu empresa en 5 minutos","cta":"Solicitar diagnostico"},{"tema":"proteccion","titulo":"No esperes la multa del SAT. Anticipa el riesgo","cta":"Evalua tu empresa"}],"instagram":[{"tema":"infografia","titulo":"5 riesgos que toda PyME mexicana debe monitorear","cta":"Link en bio"},{"tema":"dato","titulo":"Costo promedio contingencia fiscal: $520,000 MXN","cta":"Protege tu empresa"}],"email":[{"tema":"bienvenida","asunto":"Bienvenido a MESAN Omega","tipo":"onboarding"},{"tema":"valor","asunto":"3 riesgos que podrian costarle millones","tipo":"nurturing"},{"tema":"propuesta","asunto":"Su diagnostico ejecutivo esta listo","tipo":"conversion"}],"google_ads":[{"titulo":"Diagnostico de riesgo empresarial | MESAN Omega","descripcion":"Identifica riesgos fiscales, laborales y operativos en 5 min.","keywords":["riesgo empresarial","diagnostico fiscal","cumplimiento SAT"]}]}
class MarketingEngine:
    def __init__(self):self.version="1.0.0";self._queue=deque(maxlen=200);self._published=deque(maxlen=200)
    def generate_daily_content(self):
        generated=[]
        for ch,tmps in TEMPLATES.items():
            if not tmps:continue
            idx=len(self._queue)%len(tmps);t=tmps[idx]
            c={"id":"MKT-{}".format(int(datetime.now(timezone.utc).timestamp())),"timestamp":datetime.now(timezone.utc).isoformat(),"channel":ch,"template":t,"status":"DRAFT"}
            self._queue.append(c);generated.append(c)
        return{"generated":len(generated),"content":generated}
    def get_queue(self):return{"queue_size":len(self._queue),"content":list(self._queue)[-20:]}
    def get_templates(self,channel=None):
        if channel:return TEMPLATES.get(channel,[])
        return TEMPLATES
    def publish(self,content_id):
        for item in self._queue:
            if item["id"]==content_id:item["status"]="PUBLISHED";item["published_at"]=datetime.now(timezone.utc).isoformat();self._published.append(item);return{"status":"PUBLISHED"}
        return{"status":"NOT_FOUND"}
    def get_stats(self):return{"version":self.version,"generated":len(self._queue),"published":len(self._published),"drafts":len([c for c in self._queue if c["status"]=="DRAFT"])}
marketing_engine=MarketingEngine()