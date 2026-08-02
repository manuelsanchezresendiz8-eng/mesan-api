# core/jarvis/event_bus.py -- MESAN Omega Guardian Event Bus v1.0
"""
Bus de eventos interno para desacoplar motores de Guardian.
En memoria. Preparado para migracion a Redis/Kafka.
"""
import logging
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List
logger = logging.getLogger("mesan.guardian.eventbus")
VALID_EVENTS = ["SERVICE_DOWN","SERVICE_UP","API_TIMEOUT","DB_OFFLINE","ROLLBACK_EXECUTED","SELF_HEALING_STARTED","SELF_HEALING_FINISHED","PAYMENT_FAILED","AI_TIMEOUT","CRITICAL_ALERT","WARROOM_ESCALATION"]
class GuardianEventBus:
    def __init__(self, max_events=1000):
        self.version = "1.0.0"
        self._queue = deque(maxlen=max_events)
        self._subscribers = defaultdict(list)
        self._processed = 0
        logger.info("[EventBus] v%s iniciado", self.version)
    def publish(self, event_name, source="", severity="INFO", payload=None):
        evt = {"timestamp":datetime.now(timezone.utc).isoformat(),"event":event_name,"source":source,"severity":severity,"payload":payload or {}}
        self._queue.append(evt)
        self._notify(event_name, evt)
        logger.info("[EventBus] %s from %s (%s)", event_name, source, severity)
        return evt
    def subscribe(self, event_name, callback):
        self._subscribers[event_name].append(callback)
        logger.info("[EventBus] Subscriber added for %s", event_name)
    def unsubscribe(self, event_name, callback):
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)
    def _notify(self, event_name, evt):
        for cb in self._subscribers.get(event_name, []):
            try:
                cb(evt)
                self._processed += 1
            except Exception as e:
                logger.error("[EventBus] Subscriber error for %s: %s", event_name, e)
        for cb in self._subscribers.get("*", []):
            try:
                cb(evt)
                self._processed += 1
            except Exception as e:
                logger.error("[EventBus] Wildcard subscriber error: %s", e)
    def process(self):
        pending = list(self._queue)
        return {"processed":len(pending),"events":pending}
    def replay(self, event_name=None, limit=50):
        evts = list(self._queue)
        if event_name:
            evts = [e for e in evts if e["event"]==event_name]
        evts.reverse()
        return evts[:limit]
    def get_queue(self):
        return {"queue_size":len(self._queue),"events":list(self._queue)[-50:],"total_processed":self._processed,"subscribers":len(self._subscribers)}
    def clear(self):
        self._queue.clear()
        self._processed = 0
        logger.info("[EventBus] Queue cleared")
event_bus = GuardianEventBus()