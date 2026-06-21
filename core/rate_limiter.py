# core/rate_limiter.py -- MESAN Omega Rate Limiter (Fase 1)
"""
Rate limiter simple en memoria para endpoints publicos sensibles a spam.

Por que esta implementacion y no slowapi/redis:
    - El servicio corre con WEB_CONCURRENCY=1 en Render (confirmado en
      logs de deploy), es decir un solo proceso -- no hay problema de
      estado no compartido entre workers.
    - Evita agregar una dependencia nueva a requirements.txt sin poder
      probarla primero en un entorno de staging.
    - Es suficiente para frenar flood/spam basico del formulario
      publico. No reemplaza un WAF ni proteccion DDoS de capa de red
      (eso lo cubre Cloudflare/Render a nivel de infraestructura).

Estrategia: sliding window simple por IP, en un dict en memoria.
    - Se limpia automaticamente (entradas viejas se descartan al leer).
    - Sin persistencia: un restart del servicio resetea los contadores
      (aceptable para este caso de uso).

Uso:
    from core.rate_limiter import rate_limit_check

    @router.post("")
    async def create_lead_endpoint(payload: LeadCreate, request: Request):
        rate_limit_check(request, key="create_lead", max_requests=5, window_seconds=60)
        ...

Si se excede el limite, rate_limit_check lanza HTTPException(429).
"""

import logging
import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

logger = logging.getLogger("mesan.rate_limiter")

# ── Estado en memoria ─────────────────────────────────────────────────────
# Estructura: { "key:ip": [timestamp1, timestamp2, ...] }
_request_log: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _get_client_ip(request: Request) -> str:
    """
    Obtiene la IP real del cliente, considerando que Render esta detras
    de un proxy/load balancer (Cloudflare). Prioriza X-Forwarded-For
    sobre request.client.host, que en un entorno con proxy reportaria
    la IP interna del proxy, no la del usuario real.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For puede ser una lista "ip1, ip2, ip3" -- la
        # primera es la IP original del cliente.
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def rate_limit_check(
    request: Request,
    key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """
    Verifica si la IP del request ha excedido el limite permitido en la
    ventana de tiempo especificada. Lanza HTTPException(429) si se
    excede.

    Args:
        request: objeto Request de FastAPI (para extraer la IP).
        key: identificador del endpoint/accion limitada (ej. "create_lead").
            Permite tener limites independientes por endpoint.
        max_requests: numero maximo de requests permitidos en la ventana.
        window_seconds: tamano de la ventana deslizante, en segundos.

    Raises:
        HTTPException 429: si se excede el limite, con header
            Retry-After indicando cuantos segundos esperar.
    """
    ip = _get_client_ip(request)
    bucket_key = f"{key}:{ip}"
    now = time.time()
    window_start = now - window_seconds

    with _lock:
        # Limpiar timestamps fuera de la ventana
        timestamps = _request_log[bucket_key]
        timestamps[:] = [t for t in timestamps if t > window_start]

        if len(timestamps) >= max_requests:
            oldest = timestamps[0]
            retry_after = int(window_seconds - (now - oldest)) + 1
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
