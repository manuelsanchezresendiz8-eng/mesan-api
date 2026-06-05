# core/logger.py -- MESAN Omega v1.2
"""
Observability Layer — Logger enterprise MESAN Ω.

v1.2 — Merge Fase 1:
- Agrega clear_context() — evita contaminación entre requests
  en workers reutilizados (FastAPI, Celery, uvicorn multi-worker)
- Mantiene compatibilidad completa con v1.1
"""

import os
import logging
import contextvars
from typing import Optional, Any

# ── Configuración ─────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENV       = os.getenv("ENV", "production")

_LEVEL_MAP = {
    "DEBUG":    logging.DEBUG,
    "INFO":     logging.INFO,
    "WARNING":  logging.WARNING,
    "ERROR":    logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# ── Context propagation global (async-safe) ───────────────────────────────────

trace_context:  contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id",  default=None)
tenant_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
engine_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("engine_id", default=None)


def set_trace_id(trace_id: str):
    trace_context.set(trace_id)

def set_tenant_id(tenant_id: str):
    tenant_context.set(tenant_id)

def set_engine_id(engine_id: str):
    engine_context.set(engine_id)

def get_trace_id() -> Optional[str]:
    return trace_context.get()

def get_tenant_id() -> Optional[str]:
    return tenant_context.get()

def clear_context():
    """
    Limpia los 3 contextvars del worker actual.

    CRÍTICO para workers reutilizados. Sin esta llamada, el trace_id /
    tenant_id / engine_id de un request anterior contamina el siguiente
    request en el mismo worker.

    Uso en FastAPI:
        @app.middleware("http")
        async def context_cleanup(request, call_next):
            try:
                return await call_next(request)
            finally:
                clear_context()

    Uso en Celery:
        @task_postrun.connect
        def cleanup(sender, **kwargs):
            clear_context()
    """
    trace_context.set(None)
    tenant_context.set(None)
    engine_context.set(None)


# ── Formatters ────────────────────────────────────────────────────────────────

class MesanFormatter(logging.Formatter):
    """Formatter con color para desarrollo. Resolución: LogRecord → contextvars → '-'"""

    LEVEL_COLORS = {
        logging.DEBUG:    "\x1b[38;5;244m",
        logging.INFO:     "\x1b[38;5;39m",
        logging.WARNING:  "\x1b[38;5;220m",
        logging.ERROR:    "\x1b[38;5;196m",
        logging.CRITICAL: "\x1b[1;38;5;196m",
    }
    GREY  = "\x1b[38;5;244m"
    CYAN  = "\x1b[38;5;51m"
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:
        color  = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        level  = f"{color}{record.levelname:<8}{self.RESET}"
        name   = f"{self.CYAN}{record.name}{self.RESET}"

        trace  = getattr(record, "trace_id", None) or trace_context.get()  or "-"
        engine = getattr(record, "engine",   None) or engine_context.get() or "-"
        tenant = getattr(record, "tenant",   None) or tenant_context.get() or "-"

        parts = []
        if trace  != "-": parts.append(f"trace={trace[:8]}")
        if engine != "-": parts.append(f"engine={engine}")
        if tenant != "-": parts.append(f"tenant={tenant}")
        context = f" [{', '.join(parts)}]" if parts else ""

        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return f"{self.GREY}{ts}{self.RESET} {level} {name}{context}: {record.getMessage()}"


class StructuredFormatter(logging.Formatter):
    """Formatter plano para producción. Compatible con ELK / Datadog / Loki."""

    def format(self, record: logging.LogRecord) -> str:
        trace  = getattr(record, "trace_id", None) or trace_context.get()  or "-"
        engine = getattr(record, "engine",   None) or engine_context.get() or "-"
        tenant = getattr(record, "tenant",   None) or tenant_context.get() or "-"
        ts     = self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ")
        return (
            f"ts={ts} level={record.levelname} logger={record.name} "
            f"trace_id={trace} engine={engine} tenant={tenant} "
            f"msg={record.getMessage()}"
        )


# ── Setup global ──────────────────────────────────────────────────────────────

def setup_logging():
    root      = logging.getLogger()
    level     = _LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    formatter = MesanFormatter() if ENV != "production" else StructuredFormatter()
    root.setLevel(level)
    if root.handlers:
        for h in root.handlers:
            h.setFormatter(formatter)
        return
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    for noisy in ("uvicorn.access", "uvicorn.error", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Factories ─────────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"mesan.{name}")


class EngineLogger:

    def __init__(self, engine_name: str, tenant_id: Optional[str] = None):
        self._logger   = logging.getLogger(f"mesan.engine.{engine_name.lower()}")
        self._engine   = engine_name
        self._tenant   = tenant_id or "global"
        self._trace_id: Optional[str] = None

    def _extra(self, extra: Optional[dict] = None) -> dict:
        base: dict[str, Any] = {"engine": self._engine, "tenant": self._tenant}
        if self._trace_id:
            base["trace_id"] = self._trace_id
        if extra:
            base.update(extra)
        return base

    def debug(self,    msg, *a, extra=None, **kw): self._logger.debug(msg,    *a, extra=self._extra(extra), **kw)
    def info(self,     msg, *a, extra=None, **kw): self._logger.info(msg,     *a, extra=self._extra(extra), **kw)
    def warning(self,  msg, *a, extra=None, **kw): self._logger.warning(msg,  *a, extra=self._extra(extra), **kw)
    def error(self,    msg, *a, extra=None, **kw): self._logger.error(msg,    *a, extra=self._extra(extra), **kw)
    def critical(self, msg, *a, extra=None, **kw): self._logger.critical(msg, *a, extra=self._extra(extra), **kw)
    def exception(self,msg, *a, extra=None, **kw): self._logger.exception(msg,*a, extra=self._extra(extra), **kw)

    def with_trace(self, trace_id: str) -> "EngineLogger":
        child = EngineLogger(self._engine, self._tenant)
        child._trace_id = trace_id
        return child


class AuditLogger:

    def __init__(self):
        self._logger = logging.getLogger("mesan.audit")

    def log_event(self, event: str, tenant: str = "global",
                  trace_id: str = "-", data: Optional[dict] = None):
        self._logger.info("AUDIT", extra={
            "event": event, "tenant": tenant,
            "trace_id": trace_id, "engine": "AUDIT", "data": data or {},
        })


# ── Instancias globales ───────────────────────────────────────────────────────

audit_logger = AuditLogger()

def get_engine_logger(engine_name: str, tenant_id: Optional[str] = None) -> EngineLogger:
    return EngineLogger(engine_name, tenant_id)
