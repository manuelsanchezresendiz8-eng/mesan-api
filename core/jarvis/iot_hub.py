# core/jarvis/iot_hub.py v1.0
import logging
from datetime import datetime,timezone
from collections import deque
logger=logging.getLogger("mesan.guardian.iot")
class IoTHub:
    def __init__(self):self.version="1.0.0";self._devices={};self._events=deque(maxlen=1000)
    def report(self,device_id,device_type,metrics,location=""):
        self._devices[device_id]={"device_id":device_id,"type":device_type,"location":location,"last_seen":datetime.now(timezone.utc).isoformat(),"metrics":metrics,"status":"ONLINE"}
        event={"timestamp":datetime.now(timezone.utc).isoformat(),"device_id":device_id,"type":device_type,"metrics":metrics}
        self._events.append(event)
        if metrics.get("motion_detected") or metrics.get("alert"):
            try:
                from core.jarvis.notification_center import notification_center
                notification_center.notify("CRITICAL_ALERT","HIGH","IoT Alert: {} - {}".format(device_id,metrics.get("alert","motion detected")),{"device":device_id})
            except:pass
        return{"status":"OK","device_id":device_id}
    def get_devices(self):return{"version":self.version,"total":len(self._devices),"devices":list(self._devices.values())}
    def get_events(self,limit=50):
        evts=list(self._events);evts.reverse();return{"total":len(evts),"events":evts[:limit]}
iot_hub=IoTHub()