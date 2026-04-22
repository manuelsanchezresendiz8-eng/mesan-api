import logging

logger = logging.getLogger("mesan")

def emit(event_type: str, payload: dict, request_id: str = ""):
    logger.info({
        "event": event_type,
        "request_id": request_id,
        "payload": payload
    })
# v2 — actualizado
