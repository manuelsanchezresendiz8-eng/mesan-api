# =============================================================================
# MESAN Omega - Phase 5 Integration Bridge v1.2
# Auditoria empresarial persistente en PostgreSQL (SHA-256)
# =============================================================================
# Los sellos se almacenan en mesan_audit_seals. La tabla se crea mediante la
# migracion SQL explicita; no se depende del filesystem efimero del contenedor.
# MESAN_P5_SNAPSHOT apagado -> no-op. No se activa implicitamente.
# =============================================================================

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional

logger = logging.getLogger("mesan.phase5")

FLAG_SNAPSHOT = "MESAN_P5_SNAPSHOT"

_NIVEL_MAP = {
    "EXTREMO": "CRITICO", "CRITICO": "CRITICO", "ALTO": "ALTO",
    "MEDIO": "MEDIO", "BAJO": "BAJO", "SEGURO": "BAJO",
}


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes", "on")


def _safe(default: Any = None) -> Callable:
    def wrap(fn: Callable) -> Callable:
        def inner(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - la auditoria no interrumpe el diagnostico
                logger.warning("phase5_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


class SnapshotBridge:
    """Sella diagnosticos y consulta registros persistidos por tenant."""

    def __init__(self) -> None:
        self._engine = None
        self._session_factory = None
        self._record_model = None
        self._enabled = _flag(FLAG_SNAPSHOT)
        if self._enabled:
            try:
                from core.snapshot_engine import SnapshotEngine
                from core.integration.audit_db_models import AuditSealRecord
                from database import SessionLocal
                self._engine = SnapshotEngine()
                self._session_factory = SessionLocal
                self._record_model = AuditSealRecord
                # Verifica conectividad Y presencia de la migracion antes de anunciarse activo.
                with self._session_factory() as db:
                    db.query(self._record_model).limit(1).all()
                logger.info("Phase5: PostgreSQL audit ledger conectado")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase5: PostgreSQL audit ledger no disponible (%s)", exc)
                self._enabled = False
                self._engine = None
                self._session_factory = None
                self._record_model = None

    @property
    def active(self) -> bool:
        return bool(self._enabled and self._engine is not None
                    and self._session_factory is not None and self._record_model is not None)

    @staticmethod
    def _to_dict(record) -> dict:
        return {
            "snapshot_id": record.snapshot_id,
            "trace_id": record.trace_id,
            "tenant_id": record.tenant_id,
            "sealed_at": record.sealed_at,
            "state_hash": record.state_hash,
            "algorithm": record.algorithm,
            "engine_version": record.engine_version,
            "omega_score": record.omega_score,
            "risk_level": record.risk_level,
            "exposure_total": record.exposure_total,
        }

    @staticmethod
    def _state(response_dict: dict) -> dict:
        response_dict = {k: v for k, v in response_dict.items() if k != "audit_seal"}
        nivel_raw = str(response_dict.get("nivel")
                        or response_dict.get("risk_level") or "MEDIO").upper()
        return {
            "score": response_dict.get("omega_score", 0),
            "confidence": 0.95,
            "nivel_riesgo": _NIVEL_MAP.get(nivel_raw, "MEDIO"),
            "exposicion_probable": response_dict.get("total_exposure_mxn", 0),
            "contradictions": 0,
            "response": response_dict,
        }

    @_safe(default=None)
    def seal(self, response_dict: dict, tenant_id: str,
             trace_id: str) -> Optional[dict]:
        """Genera SHA-256 e inserta un registro inmutable por tenant/trace."""
        if not self.active or not tenant_id or not trace_id or not isinstance(response_dict, dict):
            return None

        from core.snapshot_engine import SnapshotEngine
        state = self._state(response_dict)
        snap = self._engine.create_snapshot(tenant_id, state, trace_id=trace_id)
        try:
            record = self._record_model(
                snapshot_id=snap.snapshot_id,
                trace_id=trace_id,
                tenant_id=tenant_id,
                sealed_at=snap.timestamp,
                state_hash=snap.state_hash,
                algorithm="SHA-256",
                engine_version=snap.engine_version,
                omega_score=snap.score,
                risk_level=snap.risk_level.value,
                exposure_total=snap.exposure_total,
            )
            with self._session_factory() as db:
                db.add(record)
                db.commit()
                db.refresh(record)
                return self._to_dict(record)
        finally:
            # El ledger durable es PostgreSQL; no conservar copias en memoria.
            self._engine.delete_snapshot(snap.snapshot_id)

    @_safe(default=None)
    def get_by_trace(self, trace_id: str, tenant_id: str) -> Optional[dict]:
        """Consulta exacta por trace y tenant; no existe fallback global."""
        if not self.active or not tenant_id or not trace_id:
            return None
        with self._session_factory() as db:
            record = (db.query(self._record_model)
                      .filter_by(trace_id=trace_id, tenant_id=tenant_id)
                      .first())
            return self._to_dict(record) if record else None

    @_safe(default=[])
    def history(self, tenant_id: str, limit: int = 50) -> list:
        """Historial persistente, siempre limitado al tenant autenticado."""
        if not self.active or not tenant_id:
            return []
        safe_limit = max(1, min(int(limit), 500))
        with self._session_factory() as db:
            records = (db.query(self._record_model)
                       .filter_by(tenant_id=tenant_id)
                       .order_by(self._record_model.sealed_at.desc())
                       .limit(safe_limit).all())
            return [self._to_dict(record) for record in records]

    @_safe(default=None)
    def verify(self, trace_id: str, response_dict: dict,
               tenant_id: str) -> Optional[dict]:
        """Verifica el documento solo contra el sello del tenant indicado."""
        if not self.active or not tenant_id or not isinstance(response_dict, dict):
            return None
        rec = self.get_by_trace(trace_id, tenant_id)
        if not rec:
            return {"verified": False, "reason": "SELLO_NO_ENCONTRADO"}
        import hashlib
        recomputed = hashlib.sha256(
            self._engine.safe_json(self._state(response_dict)).encode("utf-8")
        ).hexdigest()
        return {
            "verified": recomputed == rec["state_hash"],
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "sealed_at": rec["sealed_at"],
            "expected_hash": rec["state_hash"],
            "recomputed_hash": recomputed,
        }


# =============================================================================
_snapshot: Optional[SnapshotBridge] = None


def get_snapshot_bridge() -> SnapshotBridge:
    global _snapshot
    if _snapshot is None:
        _snapshot = SnapshotBridge()
    return _snapshot
