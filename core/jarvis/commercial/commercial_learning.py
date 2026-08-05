# core/jarvis/commercial/commercial_learning.py v1.0
import logging
from datetime import datetime,timezone
from collections import defaultdict
logger=logging.getLogger("mesan.commercial.learning")
class CommercialLearning:
    def __init__(self):self.version="1.0.0";self._sector_conversions=defaultdict(lambda:{"leads":0,"won":0});self._content_performance=defaultdict(lambda:{"views":0,"clicks":0,"leads":0});self._best_hours=defaultdict(int);self._argument_wins=defaultdict(int)
    def record_lead(self,sector,converted=False):
        self._sector_conversions[sector]["leads"]+=1
        if converted:self._sector_conversions[sector]["won"]+=1
    def record_content(self,channel,views=0,clicks=0,leads=0):
        self._content_performance[channel]["views"]+=views;self._content_performance[channel]["clicks"]+=clicks;self._content_performance[channel]["leads"]+=leads
    def record_conversion(self,hour,argument=""):
        self._best_hours[hour]+=1
        if argument:self._argument_wins[argument]+=1
    def get_insights(self):
        best_sector=max(self._sector_conversions.items(),key=lambda x:x[1]["won"],default=("Ninguno",{"won":0}))
        best_channel=max(self._content_performance.items(),key=lambda x:x[1]["leads"],default=("Ninguno",{"leads":0}))
        best_hour=max(self._best_hours.items(),key=lambda x:x[1],default=(9,0))
        best_arg=max(self._argument_wins.items(),key=lambda x:x[1],default=("Ninguno",0))
        return{"timestamp":datetime.now(timezone.utc).isoformat(),"best_sector":{"sector":best_sector[0],"conversions":best_sector[1]["won"]},"best_channel":{"channel":best_channel[0],"leads":best_channel[1]["leads"]},"best_hour":{"hour":best_hour[0],"conversions":best_hour[1]},"best_argument":{"argument":best_arg[0],"wins":best_arg[1]},"sector_data":dict(self._sector_conversions),"content_data":dict(self._content_performance)}
commercial_learning=CommercialLearning()