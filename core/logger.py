# core/logger.py -- MESAN Omega Structured Logger v1.0
"""
Structured Logger MESAN Ω
- JSON estructurado compatible con OpenSearch, ELK, Loki
- Compatible con RequestContext v2.x (frozen=True, slots=True)
- Serialización segura
- Niveles INFO / WARNING / ERROR / CRITICAL
- Integración automática de contexto distribuido
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from core.context import RequestContext

_SERVICE = os.getenv("MESAN_SERVICE_NAME", "MESAN")
logger   = logging.getLogger("mesan.logger")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_entry(
    event:   str,
    level:   str,
    ctx:     Optional[RequestContext] = None,
    extra:   Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "service":   _SERVICE,
        "event":     event,
        "level":     level.upper(),
        "timestamp": _now(),
    }
    if ctx is not None:
        entry["ctx"] = ctx.to_dict()
    if extra:
        entry["extra"] = extra
    return entry


def _emit(entry: dict[str, Any], level: str) -> None:
    line = json.dumps(entry, default=str, ensure_ascii=False)
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(line)


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def log_event(
    event: str,
    level: str                        = "INFO",
    ctx:   Optional[RequestContext]   = None,
    extra: Optional[dict[str, Any]]  = None,
) -> None:
    _emit(_build_entry(event, level, ctx, extra), level)


def log_info(
    event: str,
    ctx:   Optional[RequestContext]  = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    log_event(event, "INFO", ctx, extra)


def log_warning(
    event: str,
    ctx:   Optional[RequestContext]  = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    log_event(event, "WARNING", ctx, extra)


def log_error(
    event: str,
    ctx:   Optional[RequestContext]  = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    log_event(event, "ERROR", ctx, extra)


def log_critical(
    event: str,
    ctx:   Optional[RequestContext]  = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    log_event(event, "CRITICAL", ctx, extra)
