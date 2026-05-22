# core/snapshot_engine.py
# MESAN Omega — Enterprise Snapshot Engine v2.0
# Immutable State Tracking | Drift Detection | Audit Ready

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import hashlib
import json
import uuid


# ============================================================
# ENUMS
# ============================================================

class DriftLevel(str, Enum):
    ESTABLE = "ESTABLE"
    LEVE = "LEVE"
    MODERADO = "MODERADO"
    CRITICO = "CRITICO"


class RiskLevel(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class EnterpriseSnapshot:

    snapshot_id: str

    tenant_id: str

    timestamp: str

    state_hash: str

    score: float

    confidence: float

    risk_level: RiskLevel

    exposure_total: float

    contradictions: int

    validation_penalty: int

    engine_version: str

    trace_id: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    full_state: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class SnapshotComparison:

    snapshot_1: str
    snapshot_2: str

    score_delta: float

    confidence_delta: float

    exposure_delta: float

    contradictions_delta: int

    deterioration_detected: bool

    hash_changed: bool

    timestamp_s1: str
    timestamp_s2: str

    drift_level: DriftLevel

    trace_id: str

    compared_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


@dataclass
class DriftResult:

    tenant_id: str

    drift_detected: bool

    drift_level: DriftLevel

    score_drift: float

    confidence_drift: float

    snapshots_analyzed: int

    tendency: str

    period_start: str
    period_end: str

    trace_id: str

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class SnapshotEngine:

    VERSION = "2.0.0"

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        self._snapshots: Dict[
            str,
            EnterpriseSnapshot
        ] = {}

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def safe_float(value, default=0.0) -> float:

        try:

            if value in [None, "", "null"]:
                return default

            return float(value)

        except (TypeError, ValueError):

            return default

    @staticmethod
    def safe_int(value, default=0) -> int:

        try:

            if value in [None, "", "null"]:
                return default

            return int(float(value))

        except (TypeError, ValueError):

            return default

    @staticmethod
    def safe_json(data: Dict[str, Any]) -> str:

        try:

            return json.dumps(
                data,
                sort_keys=True,
                default=str,
                ensure_ascii=False
            )

        except Exception:

            return "{}"

    # ========================================================
    # DRIFT CLASSIFICATION
    # ========================================================

    def _classify_drift(
        self,
        score_delta: float,
        confidence_delta: float
    ) -> DriftLevel:

        score_abs = abs(score_delta)

        conf_abs = abs(confidence_delta)

        if score_abs > 25 or conf_abs > 0.35:
            return DriftLevel.CRITICO

        if score_abs > 15 or conf_abs > 0.20:
            return DriftLevel.MODERADO

        if score_abs > 5 or conf_abs > 0.10:
            return DriftLevel.LEVE

        return DriftLevel.ESTABLE

    # ========================================================
    # CREATE SNAPSHOT
    # ========================================================

    def create_snapshot(
        self,
        tenant_id: str,
        state: Dict[str, Any],
        trace_id: str = ""
    ) -> EnterpriseSnapshot:

        if not trace_id:

            trace_id = str(uuid.uuid4())

        state_json = self.safe_json(state)

        state_hash = hashlib.sha256(
            state_json.encode("utf-8")
        ).hexdigest()

        snapshot_id = str(uuid.uuid4())

        snap = EnterpriseSnapshot(

            snapshot_id=snapshot_id,

            tenant_id=tenant_id,

            timestamp=datetime.utcnow().isoformat(),

            state_hash=state_hash,

            score=round(
                self.safe_float(
                    state.get("score")
                ),
                2
            ),

            confidence=round(
                self.safe_float(
                    state.get(
                        "confidence",
                        0.82
                    )
                ),
                4
            ),

            risk_level=RiskLevel(
                state.get(
                    "nivel_riesgo",
                    "MEDIO"
                )
            ),

            exposure_total=round(
                self.safe_float(
                    state.get(
                        "exposicion_probable",
                        0
                    )
                ),
                2
            ),

            contradictions=self.safe_int(
                state.get(
                    "contradictions",
                    0
                )
            ),

            validation_penalty=self.safe_int(
                state.get(
                    "validation_penalty",
                    0
                )
            ),

            engine_version=self.VERSION,

            trace_id=trace_id,

            metadata={

                "state_size_bytes":
                len(state_json),

                "keys":
                list(state.keys())

            },

            full_state=state

        )

        self._snapshots[
            snapshot_id
        ] = snap

        return snap

    # ========================================================
    # GET SNAPSHOT
    # ========================================================

    def get_snapshot(
        self,
        snapshot_id: str
    ) -> Optional[EnterpriseSnapshot]:

        return self._snapshots.get(
            snapshot_id
        )

    # ========================================================
    # LIST SNAPSHOTS
    # ========================================================

    def list_by_tenant(
        self,
        tenant_id: str
    ) -> List[EnterpriseSnapshot]:

        snaps = [

            s for s in self._snapshots.values()

            if s.tenant_id == tenant_id

        ]

        return sorted(
            snaps,
            key=lambda s: s.timestamp
        )

    # ========================================================
    # COMPARE SNAPSHOTS
    # ========================================================

    def compare_snapshots(
        self,
        id1: str,
        id2: str
    ) -> Dict[str, Any]:

        s1 = self._snapshots.get(id1)

        s2 = self._snapshots.get(id2)

        if not s1 or not s2:

            return {

                "error":
                "Snapshot no encontrado"

            }

        score_delta = round(
            s2.score - s1.score,
            2
        )

        confidence_delta = round(
            s2.confidence - s1.confidence,
            4
        )

        exposure_delta = round(
            s2.exposure_total -
            s1.exposure_total,
            2
        )

        contradictions_delta = (
            s2.contradictions -
            s1.contradictions
        )

        deterioration = (
            score_delta > 5
        )

        drift_level = self._classify_drift(
            score_delta,
            confidence_delta
        )

        comparison = SnapshotComparison(

            snapshot_1=id1,

            snapshot_2=id2,

            score_delta=score_delta,

            confidence_delta=confidence_delta,

            exposure_delta=exposure_delta,

            contradictions_delta=contradictions_delta,

            deterioration_detected=deterioration,

            hash_changed=(
                s1.state_hash !=
                s2.state_hash
            ),

            timestamp_s1=s1.timestamp,

            timestamp_s2=s2.timestamp,

            drift_level=drift_level,

            trace_id=str(uuid.uuid4())

        )

        return comparison.__dict__

    # ========================================================
    # DETECT DRIFT
    # ========================================================

    def detect_drift(
        self,
        tenant_id: str
    ) -> Dict[str, Any]:

        snaps = self.list_by_tenant(
            tenant_id
        )

        if len(snaps) < 2:

            return {

                "drift_detected":
                False,

                "reason":
                "Insuficientes snapshots"

            }

        first = snaps[0]

        last = snaps[-1]

        score_drift = round(
            last.score - first.score,
            2
        )

        confidence_drift = round(
            last.confidence -
            first.confidence,
            4
        )

        drift_level = self._classify_drift(
            score_drift,
            confidence_drift
        )

        drift_detected = (
            drift_level !=
            DriftLevel.ESTABLE
        )

        if score_drift > 5:

            tendency = "DETERIORO"

        elif score_drift < -5:

            tendency = "MEJORA"

        else:

            tendency = "ESTABLE"

        result = DriftResult(

            tenant_id=tenant_id,

            drift_detected=drift_detected,

            drift_level=drift_level,

            score_drift=score_drift,

            confidence_drift=confidence_drift,

            snapshots_analyzed=len(snaps),

            tendency=tendency,

            period_start=first.timestamp,

            period_end=last.timestamp,

            trace_id=str(uuid.uuid4())

        )

        return result.__dict__

    # ========================================================
    # DELETE SNAPSHOT
    # ========================================================

    def delete_snapshot(
        self,
        snapshot_id: str
    ) -> bool:

        if snapshot_id in self._snapshots:

            del self._snapshots[
                snapshot_id
            ]

            return True

        return False

    # ========================================================
    # CLEAR TENANT
    # ========================================================

    def clear_tenant(
        self,
        tenant_id: str
    ) -> int:

        ids = [

            sid

            for sid, snap
            in self._snapshots.items()

            if snap.tenant_id == tenant_id

        ]

        for sid in ids:

            del self._snapshots[sid]

        return len(ids)
