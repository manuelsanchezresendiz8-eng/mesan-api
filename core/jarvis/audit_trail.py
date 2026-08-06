# core/jarvis/audit_trail.py v1.0
import logging
from datetime import datetime,timezone
from collections import deque
logger=logging.getLogger("mesan.audit")
class AuditTrail:
    def __init__(self):self.version="1.0.0";self._entries=deque(maxlen=5000)
    def log(self,user="system",action="",endpoint="",ip="",module="",result="OK",before=None,after=None):
        entry={"id":"AUD-{}".format(int(datetime.now(timezone.utc).timestamp()*1000)),"timestamp":datetime.now(timezone.utc).isoformat(),"user":user,"action":action,"endpoint":endpoint,"ip":ip,"module":module,"result":result}
        if before is not None:entry["before"]=str(before)[:500]
        if after is not None:entry["after"]=str(after)[:500]
        self._entries.append(entry);return entry
    def query(self,module=None,user=None,limit=50):
        entries=list(self._entries)
        if module:entries=[e for e in entries if e.get("module")==module]
        if user:entries=[e for e in entries if e.get("user")==user]
        entries.reverse();return entries[:limit]
    def get_stats(self):
        total=len(self._entries);modules={}
        for e in self._entries:m=e.get("module","unknown");modules[m]=modules.get(m,0)+1
        return{"version":self.version,"total_entries":total,"modules":modules}
audit_trail=AuditTrail()