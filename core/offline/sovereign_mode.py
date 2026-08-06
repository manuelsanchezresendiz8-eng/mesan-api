# core/offline/sovereign_mode.py v1.0
import os,socket
from datetime import datetime,timezone
class SovereignMode:
    def __init__(self):self.version="1.0.0";self._mode=os.getenv("MESAN_MODE","CLOUD")
    def detect_mode(self):
        if os.getenv("OFFLINE_MODE","false").lower()=="true":return"OFFLINE"
        if not self._check_internet():return"OFFLINE"
        if self._mode=="HYBRID":return"HYBRID"
        return"CLOUD"
    def _check_internet(self):
        try:socket.create_connection(("8.8.8.8",53),timeout=3);return True
        except:return False
    def get_status(self):return{"mode":self.detect_mode(),"internet":self._check_internet(),"local_db":"PostgreSQL" if os.getenv("DATABASE_URL") else "SQLite","sync_pending":0,"version":self.version,"timestamp":datetime.now(timezone.utc).isoformat()}
sovereign_mode=SovereignMode()