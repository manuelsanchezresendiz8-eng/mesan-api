# core/offline/sync_manager.py v1.0
from datetime import datetime,timezone
from collections import deque
class SyncManager:
    def __init__(self):self.version="1.0.0";self._pending=deque(maxlen=1000);self._synced=deque(maxlen=1000)
    def queue(self,data_type,payload):
        entry={"id":"SYNC-{}".format(int(datetime.now(timezone.utc).timestamp()*1000)),"timestamp":datetime.now(timezone.utc).isoformat(),"type":data_type,"status":"PENDING"}
        self._pending.append(entry);return entry
    def get_status(self):return{"version":self.version,"pending":len(self._pending),"synced":len(self._synced)}
sync_manager=SyncManager()