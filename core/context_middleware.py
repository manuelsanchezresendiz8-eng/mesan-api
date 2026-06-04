# core/context_middleware.py -- MESAN Omega Context Middleware v2.2
import uuid
import time
import logging
from fastapi import Request
from fastapi.responses import Response
from core.context import RequestContext

logger = logging.getLogger("mesan.middleware.context")


async def context_middleware(request: Request, call_next) -> Response:
    """
    Middleware de contexto MESAN Ω v2.2
    - Multi-tenant isolation
    - Distributed tracing X-Request-ID + X-Correlation-ID
    - Latency observability (incluso en requests fallidos)
    - Defensive exception handling
    """
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )
    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or str(uuid.uuid4())
    )

    tenant_id = request.headers.get("X-Tenant-ID", "public")
    user_id   = request.headers.get("X-User-ID")
    role      = request.headers.get("X-Role")

    ctx = RequestContext(
        tenant_id=tenant_id,
        request_id=request_id,
        user_id=user_id,
        role=role,
        correlation_id=correlation_id,
    )

    request.state.ctx = ctx
    logger.debug("Request started", extra=ctx.to_dict())

    start = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled exception",
            extra={"request_id": ctx.request_id, "tenant_id": ctx.tenant_id}
        )
        raise
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.debug(
            "Request completed",
            extra={
                "request_id":     ctx.request_id,
                "correlation_id": ctx.correlation_id,
                "tenant_id":      ctx.tenant_id,
                "duration_ms":    duration_ms,
            }
        )

    response.headers["X-Request-ID"]       = ctx.request_id
    response.headers["X-Correlation-ID"]   = ctx.correlation_id
    response.headers["X-Response-Time-MS"] = str(duration_ms)

    return response
  
