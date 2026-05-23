# core/trace_engine.py -- MESAN Omega Enterprise Trace Engine v1.1
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class TraceContext:
    trace_id: str; correlation_id: str; request_id: str
    engine: str; tenant_id: str; timestamp: str
    parent_trace_id: Optional[str] = None
    metadata: Dict[str,Any] = field(default_factory=dict)

class TraceEngine:
    VERSION = "1.1.0"

    @staticmethod
    def create_trace() -> str: return str(uuid.uuid4())

    @staticmethod
    def create_correlation() -> str: return str(uuid.uuid4())

    @staticmethod
    def create_request_id() -> str: return str(uuid.uuid4())

    @staticmethod
    def create_context(engine: str, tenant_id: str,
                       parent_trace_id: Optional[str] = None,
                       metadata: Optional[Dict[str,Any]] = None) -> TraceContext:
        return TraceContext(
            trace_id=TraceEngine.create_trace(),
            correlation_id=TraceEngine.create_correlation(),
            request_id=TraceEngine.create_request_id(),
            engine=engine, tenant_id=tenant_id,
            timestamp=datetime.utcnow().isoformat(),
            parent_trace_id=parent_trace_id, metadata=metadata or {}
        )

    @staticmethod
    def child_context(parent: TraceContext, engine: str) -> TraceContext:
        return TraceContext(
            trace_id=TraceEngine.create_trace(),
            correlation_id=parent.correlation_id,
            request_id=parent.request_id,
            engine=engine, tenant_id=parent.tenant_id,
            timestamp=datetime.utcnow().isoformat(),
            parent_trace_id=parent.trace_id, metadata=dict(parent.metadata)
        )

    @staticmethod
    def to_dict(context: TraceContext) -> dict:
        return {"trace_id": context.trace_id, "correlation_id": context.correlation_id,
                "request_id": context.request_id, "engine": context.engine,
                "tenant_id": context.tenant_id, "timestamp": context.timestamp,
                "parent_trace_id": context.parent_trace_id, "metadata": context.metadata}

    @staticmethod
    def build_audit_log(context: TraceContext, action: str,
                        status: str = "SUCCESS", severity: str = "INFO") -> dict:
        return {"timestamp": datetime.utcnow().isoformat(),
                "trace_id": context.trace_id, "correlation_id": context.correlation_id,
                "request_id": context.request_id, "tenant_id": context.tenant_id,
                "engine": context.engine, "action": action,
                "status": status, "severity": severity}

    @staticmethod
    def health() -> dict:
        return {"status": "HEALTHY", "version": TraceEngine.VERSION,
                "timestamp": datetime.utcnow().isoformat()}
