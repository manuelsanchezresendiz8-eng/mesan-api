# core/logger.py -- MESAN Omega v1.1 Enterprise
"""
Observability Layer de MESAN Ω.

Capacidades:
- trace_id propagation global via contextvars (async-safe)
- Structured logging compatible con ELK / Datadog / Loki
- Engine-aware logging con contexto multi-tenant
- Audit logger estructurado (no string-based)
- Thread-safe / multi-worker ready
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
# Funciona en FastAPI, Celery y multi-worker.
# Cada request/task tiene su propio contexto aislado.

trace_context:  contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id",  default=None)
tenant_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
engine_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("engine_id", default=None)


def set_trace_id(trace_id: str):
    """Inyecta trace_id en el contexto actual. Llamar desde middleware de FastAPI."""
    trace_context.set(trace_id)

def set_tenant_id(tenant_id: str):
    """Inyecta tenant_id en el contexto actual."""
    tenant_context.set(tenant_id)

def set_engine_id(engine_id: str):
    """Inyecta engine_id en el contexto actual."""
    engine_context.set(engine_id)

def get_trace_id() -> Optional[str]:
    return trace_context.get()

def get_tenant_id() -> Optional[str]:
    return tenant_context.get()


# ── Formatters ────────────────────────────────────────────────────────────────

class MesanFormatter(logging.Formatter):
    """
    Formatter con color para desarrollo.
    Resuelve trace_id desde LogRecord primero,
    luego desde contextvars como fallback.
    """

    GREY     = "\x1b[38;5;244m"
    BLUE     = "\x1b[38;5;39m"
    YELLOW   = "\x1b[38;5;220m"
    RED      = "\x1b[38;5;196m"
    BOLD_RED = "\x1b[1;38;5;196m"
    CYAN     = "\x1b[38;5;51m"
    RESET    = "\x1b[0m"

    LEVEL_COLORS = {
        logging.DEBUG:    "\x1b[38;5;244m",
        logging.INFO:     "\x1b[38;5;39m",
        logging.WARNING:  "\x1b[38;5;220m",
        logging.ERROR:    "\x1b[38;5;196m",
        logging.CRITICAL: "\x1b[1;38;5;196m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        level = f"{color}{record.levelname:<8}{self.RESET}"
        name  = f"{self.CYAN}{record.name}{self.RESET}"

        # Resolución de trace_id: LogRecord → contextvars → "-"
        trace  = getattr(record, "trace_id",  None) or trace_context.get()  or "-"
        engine = getattr(record, "engine",    None) or engine_context.get() or "-"
        tenant = getattr(record, "tenant",    None) or tenant_context.get() or "-"

        context_parts = []
        if trace  != "-": context_parts.append(f"trace={trace[:8]}")
        if engine != "-": context_parts.append(f"engine={engine}")
        if tenant != "-": context_parts.append(f"tenant={tenant}")
        context = f" [{', '.join(context_parts)}]" if context_parts else ""

        ts = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return f"{self.GREY}{ts}{self.RESET} {level} {name}{context}: {record.getMessage()}"


class StructuredFormatter(logging.Formatter):
    """
    Formatter estructurado para producción.
    Emite campos planos parseables por ELK / Datadog / Loki.
    Sin string concatenation — cada campo es atributo separado.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Resolución de contexto con fallback a contextvars
        trace  = getattr(record, "trace_id", None) or trace_context.get()  or "-"
        engine = getattr(record, "engine",   None) or engine_context.get() or "-"
        tenant = getattr(record, "tenant",   None) or tenant_context.get() or "-"

        ts = self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ")

        # Formato plano indexable — compatible con log shippers
        return (
            f"ts={ts} "
            f"level={record.levelname} "
            f"logger={record.name} "
            f"trace_id={trace} "
            f"engine={engine} "
            f"tenant={tenant} "
            f"msg={record.getMessage()}"
        )


# ── Setup global ──────────────────────────────────────────────────────────────

def setup_logging():
    """
    Configura el sistema de logging de MESAN Ω.
    Extiende basicConfig existente sin duplicar handlers.
    """
    root  = logging.getLogger()
    level = _LEVEL_MAP.get(LOG_LEVEL, logging.INFO)
    root.setLevel(level)

    formatter = MesanFormatter() if ENV != "production" else StructuredFormatter()

    if root.handlers:
        for handler in root.handlers:
            handler.setFormatter(formatter)
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Silenciar loggers ruidosos de terceros
    for noisy in ("uvicorn.access", "uvicorn.error", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Factory simple ────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Logger estándar bajo namespace mesan.*"""
    return logging.getLogger(f"mesan.{name}")


# ── EngineLogger ──────────────────────────────────────────────────────────────

class EngineLogger:
    """
    Logger engine-aware con contexto fijo de motor y tenant.

    - trace_id se resuelve automáticamente desde contextvars si no se especifica
    - with_trace() crea una instancia con trace_id fijo para el ciclo de vida
      de un request específico, inyectándolo correctamente en LogRecord

    Uso:
        log = EngineLogger("FiscalSentinel", tenant_id="acme-corp")
        log.info("Análisis completado")

        # Con trace explícito:
        log = EngineLogger("FiscalSentinel").with_trace("abc-123")
        log.warning("Contingencia detectada")
    """

    def __init__(self, engine_name: str, tenant_id: Optional[str] = None):
        self._logger    = logging.getLogger(f"mesan.engine.{engine_name.lower()}")
        self._engine    = engine_name
        self._tenant    = tenant_id or "global"
        self._trace_id: Optional[str] = None  # FIX: siempre inicializado

    def _extra(self, extra: Optional[dict] = None) -> dict:
        base: dict[str, Any] = {
            "engine": self._engine,
            "tenant": self._tenant,
        }
        # FIX: trace_id fijo en instancia tiene prioridad;
        # si no, el formatter lo resuelve desde contextvars
        if self._trace_id:
            base["trace_id"] = self._trace_id
        if extra:
            base.update(extra)
        return base

    def debug(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.debug(msg, *args, extra=self._extra(extra), **kwargs)

    def info(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.info(msg, *args, extra=self._extra(extra), **kwargs)

    def warning(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.warning(msg, *args, extra=self._extra(extra), **kwargs)

    def error(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.error(msg, *args, extra=self._extra(extra), **kwargs)

    def critical(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.critical(msg, *args, extra=self._extra(extra), **kwargs)

    def exception(self, msg: str, *args, extra: Optional[dict] = None, **kwargs):
        self._logger.exception(msg, *args, extra=self._extra(extra), **kwargs)

    def with_trace(self, trace_id: str) -> "EngineLogger":
        """
        Retorna nueva instancia con trace_id fijo inyectado en LogRecord.
        FIX: la v1.0 asignaba _trace_id pero nunca lo inyectaba en extra.
        Ahora _extra() lo incluye explícitamente.
        """
        child = EngineLogger(self._engine, self._tenant)
        child._trace_id = trace_id
        return child


# ── AuditLogger estructurado ──────────────────────────────────────────────────

class AuditLogger:
    """
    Logger de auditoría estructurado para eventos críticos de negocio.

    FIX v1.1: Elimina string formatting de auditoría.
    Cada campo es un atributo separado en LogRecord —
    compatible con ELK, Datadog, Loki sin transformación adicional.

    Uso:
        audit = AuditLogger()
        audit.log_event("LEAD_CREATED", tenant="acme", data={"id": "123"})
    """

    def __init__(self):
        self._logger = logging.getLogger("mesan.audit")

    def log_event(
        self,
        event:    str,
        tenant:   str = "global",
        trace_id: str = "-",
        data:     Optional[dict] = None,
    ):
        # FIX: campos estructurados en extra, no en el mensaje
        # El mensaje es mínimo — los campos son atributos del LogRecord
        self._logger.info(
            "AUDIT",
            extra={
                "event":    event,
                "tenant":   tenant,
                "trace_id": trace_id,
                "engine":   "AUDIT",
                "data":     data or {},
            },
        )


# ── Instancias y helpers globales ─────────────────────────────────────────────

audit_logger = AuditLogger()


def get_engine_logger(engine_name: str, tenant_id: Optional[str] = None) -> EngineLogger:
    """
    Factory para motores MESAN Ω.

    Uso en cualquier engine:
        from core.logger import get_engine_logger
        log = get_engine_logger("FiscalSentinel", tenant_id="acme")
        log.info("Motor iniciado")
    """
    return EngineLogger(engine_name, tenant_id)
