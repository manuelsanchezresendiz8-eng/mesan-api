# core/jarvis/commercial/commercial_strategy_engine.py v1.0
import logging
from datetime import datetime,timezone
from collections import deque
logger=logging.getLogger("mesan.commercial.strategy")
class CommercialStrategyEngine:
    def __init__(self):self.version="1.0.0";self._strategies=deque(maxlen=50)
    def generate_daily(self):
        from core.jarvis.commercial.commercial_metrics import commercial_metrics
        m=commercial_metrics.calculate();leads=m.get("leads",{})
        s={"timestamp":datetime.now(timezone.utc).isoformat(),"type":"DAILY_STRATEGY","analysis":self._analyze(m),"recommendations":self._recommend(m),"sector_focus":[{"sector":"Manufactura","oportunidad":"Alta"},{"sector":"Construccion","oportunidad":"Alta"},{"sector":"Servicios","oportunidad":"Media"}],"budget":self._budget(m),"kpis":{"leads_target":max(leads.get("total",0)*2,20),"conversion_target":5.0,"mrr_target":max(m.get("mrr",0)*1.5,999)}}
        self._strategies.append(s);return s
    def _analyze(self,m):
        insights=[];total=m.get("leads",{}).get("total",0);conv=m.get("conversion_rate",0)
        if total<10:insights.append({"area":"LEADS","insight":"Volumen bajo. Priorizar adquisicion.","priority":"HIGH"})
        if conv==0:insights.append({"area":"CONVERSION","insight":"Conversion 0%. Activar seguimiento.","priority":"CRITICAL"})
        if m.get("mrr",0)==0:insights.append({"area":"REVENUE","insight":"Sin MRR. Cerrar primer cliente.","priority":"CRITICAL"})
        return insights
    def _recommend(self,m):
        recs=[];nuevos=m.get("leads",{}).get("nuevos",0)
        if nuevos>0:recs.append({"action":"Contactar {} leads nuevos".format(nuevos),"channel":"WhatsApp+Email","priority":"P1"})
        recs.append({"action":"Publicar contenido LinkedIn","channel":"LinkedIn","priority":"P2"})
        recs.append({"action":"Generar caso de exito","channel":"Blog","priority":"P3"})
        return recs
    def _budget(self,m):return{"google_ads":"30%","linkedin":"25%","contenido":"25%","alianzas":"20%","total":"$5,000 MXN/mes"}
    def get_latest(self):
        if not self._strategies:return self.generate_daily()
        return self._strategies[-1]
strategy_engine=CommercialStrategyEngine()