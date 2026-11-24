# core/rate_limiter.py -- MESAN Omega Rate Limiter (Fase 1)
"""
Rate limiter en memoria por IP de conexión.

No se confía en X-Forwarded-For: cualquier cliente puede falsificarlo si
la aplicación no valida primero que request.client.host pertenezca a un
proxy explícitamente confiable. En ausencia de una lista de proxies
configurada y verificada, se usa exclusivamente la IP del peer TCP.
"""
import ipaddress
import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

logger = logging.getLogger("mesan.rate_limiter")

_request_log: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _get_client_ip(request: Request) -> str:
    """Usa solo el peer de conexión; ignora encabezados reenviados no confiables."""
    if not request.client or not request.client.host:
        return "unknown"
    try:
        return ipaddress.ip_address(request.client.host).compressed
    except ValueError:
        return "unknown"


def rate_limit_check(
    request: Request,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Verifica el límite por IP de conexión y endpoint.
    X-Forwarded-For se ignora hasta configurar y verificar proxies confiables.
    """
    ip = _get_client_ip(request)
    bucket_key = f"{key}:{ip}"
    now = time.time()
    window_start = now - window_seconds

    with _lock:
        timestamps = _request_log[bucket_key]
        timestamps[:] = [t for t in timestamps if t > window_start]

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest)) + 1)
            logger.warning(
                "[RATE_LIMIT] Excedido | key=%s | ip=%s | count=%d/%d en %ds",
                key, ip, len(timestamps), max_requests, window_seconds,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Intente de nuevo en unos momentos.",
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)
