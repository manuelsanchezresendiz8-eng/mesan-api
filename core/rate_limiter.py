# core/rate_limiter.py -- MESAN Omega Rate Limiter (Fase 1)
"""
Rate limiter en memoria por IP para el despliegue en Render.

Render enruta el tráfico de sus web services por Cloudflare. Se usa
CF-Connecting-IP (inyectado por Cloudflare en el salto edge -> origin),
no X-Forwarded-For: este último puede conservar valores enviados por
el cliente y por tanto no es una fuente segura si se toma su primer item.
Si CF-Connecting-IP falta o no es una IP válida, se usa el peer TCP como
fallback conservador.
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


def _valid_ip(value: str) -> str | None:
    try:
        return ipaddress.ip_address(value.strip()).compressed
    except (AttributeError, ValueError):
        return None


def _get_client_ip(request: Request) -> str:
    """Prioriza el IP de Cloudflare; nunca interpreta X-Forwarded-For."""
    cloudflare_ip = _valid_ip(request.headers.get("CF-Connecting-IP", ""))
    if cloudflare_ip:
        return cloudflare_ip
    if not request.client or not request.client.host:
        return "unknown"
    return _valid_ip(request.client.host) or "unknown"


def rate_limit_check(
    request: Request,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Verifica el límite por IP de cliente y endpoint.
    En Render, CF-Connecting-IP identifica al visitante en el origen.
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
