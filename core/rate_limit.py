# core/rate_limit.py

import time
import logging

_requests = {}

def rate_limit(user_id: str, limit: int = 10, window: int = 60) -> bool:
    now = time.time()

    if user_id not in _requests:
        _requests[user_id] = []

    _requests[user_id] = [
        t for t in _requests[user_id]
        if now - t < window
    ]

    if len(_requests[user_id]) >= limit:
        logging.warning(f"[RATE_LIMIT] Bloqueado: {user_id}")
        return False

    _requests[user_id].append(now)
    return True


def get_requests_count(user_id: str, window: int = 60) -> int:
    now = time.time()
    if user_id not in _requests:
        return 0
    return len([t for t in _requests[user_id] if now - t < window])


def limpiar_requests():
    global _requests
    _requests = {}
    logging.info("[RATE_LIMIT] Registro limpiado")

# v2 — actualizado
