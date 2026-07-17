# =============================================================================
# MESAN Omega - Phase 5 Integration Bridge v1.0
# Auditoria Empresarial Inmutable (Snapshot SHA-256)
# =============================================================================
# Bindings REALES verificados contra:
#   - core/snapshot_engine.py v2.0 (create_snapshot, get_snapshot, list_by_tenant)
#
# Persistencia: el engine guarda solo en memoria (se pierde en cada redeploy).
# Este bridge agrega un JSONL APPEND-ONLY (una linea por sello, nunca se
# modifica) en MESAN_SNAPSHOT_DIR (default: data/snapshots). En Render, para
# que sobreviva redeploys se requiere un Persistent Disk montado en esa ruta.
#
# Fix aplicado: el engine truena con ValueError si nivel_riesgo no es
# BAJO/MEDIO/ALTO/CRITICO -> este bridge mapea EXTREMO->CRITICO, SEGURO->BAJO.
#
# REGLA ABSOLUTA: flag MESAN_P5_SNAPSHOT apagado -> no-op; fail-open total.
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("mesan.phase5")

FLAG_SNAPSHOT = "MESAN_P5_SNAPSHOT"
SNAPSHOT_DIR_ENV = "MESAN_SNAPSHOT_DIR"
DEFAULT_DIR = "data/snapshots"

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
            except Exception as exc:  # noqa: BLE001 - aislamiento total
                logger.warning("phase5_bridge: %s fallo (%s) - no-op", fn.__name__, exc)
                return default
        inner.__name__ = fn.__name__
        return inner
    return wrap


class SnapshotBridge:
    """Sella cada diagnostico con SHA-256 y lo persiste append-only."""

    def __init__(self) -> None:
        self._engine = None
        self._lock = threading.Lock()
        self._trace_index: dict = {}   # trace_id -> registro ligero
        self._enabled = _flag(FLAG_SNAPSHOT)
        self._dir = Path(os.getenv(SNAPSHOT_DIR_ENV, DEFAULT_DIR))
        if self._enabled:
            try:
                # BINDING REAL: SnapshotEngine v2.0
                from core.snapshot_engine import SnapshotEngine
                self._engine = SnapshotEngine()
                self._dir.mkdir(parents=True, exist_ok=True)
                self._load_index()
                logger.info("Phase5: SnapshotEngine v2.0 conectado (dir=%s, %d sellos previos)",
                            self._dir, len(self._trace_index))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Phase5: SnapshotEngine no disponible (%s)", exc)
                self._enabled = False

    @property
    def active(self) -> bool:
        return self._enabled and self._engine is not None

    # ------------------------------------------------------------- persistencia
    def _ledger_path(self) -> Path:
        return self._dir / "audit_ledger.jsonl"

    def _load_index(self) -> None:
        """Reconstruye el indice trace_id -> sello desde el ledger (si existe)."""
        path = self._ledger_path()
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("trace_id"):
                        self._trace_index[rec["trace_id"]] = rec
                except Exception:  # noqa: BLE001 - linea corrupta no rompe el resto
                    continue

    def _append_ledger(self, record: dict) -> None:
        with self._lock:
            with open(self._ledger_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    # ---------------------------------------------------------------------- API
    @_safe(default=None)
    def seal(self, response_dict: dict, tenant_id: str,
             trace_id: str) -> Optional[dict]:
        """Sella el diagnostico. Devuelve el sello (para response.audit_seal) o None.

        El hash SHA-256 cubre el response_dict COMPLETO tal como se entrego
        al cliente -> cualquier alteracion posterior es detectable.
        """
        if not self.active or not isinstance(response_dict, dict):
            return None
        nivel_raw = str(response_dict.get("nivel")
                        or response_dict.get("risk_level") or "MEDIO").upper()
        state = {
            "score": response_dict.get("omega_score", 0),
            "confidence": 0.95,
            "nivel_riesgo": _NIVEL_MAP.get(nivel_raw, "MEDIO"),
            "exposicion_probable": response_dict.get("total_exposure_mxn", 0),
            "contradictions": 0,
            "response": response_dict,   # el documento completo entra al hash
        }
        snap = self._engine.create_snapshot(tenant_id, state, trace_id=trace_id)
        record = {
            "snapshot_id": snap.snapshot_id,
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "sealed_at": snap.timestamp,
            "state_hash": snap.state_hash,
            "algorithm": "SHA-256",
            "engine_version": snap.engine_version,
            "omega_score": snap.score,
            "risk_level": snap.risk_level.value,
            "exposure_total": snap.exposure_total,
        }
        self._append_ledger(record)
        self._trace_index[trace_id] = record
        return record

    @_safe(default=None)
    def get_by_trace(self, trace_id: str) -> Optional[dict]:
        """Sello por trace_id (para GET /execute/audit/{trace_id})."""
        if not self.active:
            return None
        return self._trace_index.get(trace_id)

    @_safe(default=[])
    def history(self, tenant_id: str, limit: int = 50) -> list:
        """Historial de sellos de un tenant (mas reciente primero)."""
        if not self.active:
            return []
        recs = [r for r in self._trace_index.values()
                if r.get("tenant_id") == tenant_id]
        recs.sort(key=lambda r: r.get("sealed_at", ""), reverse=True)
        return recs[:limit]

    @_safe(default=None)
    def verify(self, trace_id: str, response_dict: dict) -> Optional[dict]:
        """Re-calcula el hash de un documento y lo compara con el sello.

        Uso: el cliente presenta su JSON/PDF; si el hash coincide, el
        documento es identico al emitido. Detecta alteraciones.
        """
        if not self.active:
            return None
        rec = self._trace_index.get(trace_id)
        if not rec:
            return {"verified": False, "reason": "SELLO_NO_ENCONTRADO"}
        nivel_raw = str(response_dict.get("nivel")
                        or response_dict.get("risk_level") or "MEDIO").upper()
        state = {
            "score": response_dict.get("omega_score", 0),
            "confidence": 0.95,
            "nivel_riesgo": _NIVEL_MAP.get(nivel_raw, "MEDIO"),
            "exposicion_probable": response_dict.get("total_exposure_mxn", 0),
            "contradictions": 0,
            "response": response_dict,
        }
        import hashlib
        recomputed = hashlib.sha256(
            self._engine.safe_json(state).encode("utf-8")).hexdigest()
        return {
            "verified": recomputed == rec["state_hash"],
            "trace_id": trace_id,
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