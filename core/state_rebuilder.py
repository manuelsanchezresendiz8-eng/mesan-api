# core/state_rebuilder.py
# MESAN Omega — State Rebuilder v2.0
# Enterprise Recovery | Event Replay | Snapshot Restore

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import hashlib
import json
import uuid


# ============================================================
# ENUMS
# ============================================================

class RebuildStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class RebuildResult:

    tenant_id: str

    success: bool

    status: RebuildStatus

    rebuilt_state: Dict[str, Any]

    events_applied: int

    snapshot_used: bool

    snapshot_id: Optional[str]

    target_timestamp: Optional[str]

    integrity_hash: str

    warnings: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    trace_id: str = ""

    engine_version: str = ""

    rebuild_timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class StateRebuilder:

    VERSION = "2.0.0"

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        replay_engine=None,
        snapshot_engine=None
    ):

        self.replay = replay_engine

        self.snapshot = snapshot_engine

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def safe_timestamp(
        value: Optional[str]
    ) -> Optional[str]:

        if not value:

            return None

        try:

            datetime.fromisoformat(
                value.replace("Z", "")
            )

            return value

        except Exception:

            return None

    @staticmethod
    def calculate_hash(
        data: Dict[str, Any]
    ) -> str:

        payload = json.dumps(
            data,
            sort_keys=True,
            default=str,
            ensure_ascii=False
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    # ========================================================
    # SNAPSHOT RESOLUTION
    # ========================================================

    def _resolve_snapshot(
        self,
        tenant_id: str,
        target_timestamp: Optional[str]
    ):

        if not self.snapshot:

            return None

        snapshots = sorted(

            [

                s for s
                in self.snapshot._snapshots.values()

                if s.tenant_id == tenant_id

            ],

            key=lambda s: s.timestamp

        )

        if not snapshots:

            return None

        # Snapshot más reciente
        if not target_timestamp:

            return snapshots[-1]

        # Snapshot previo al target
        for snap in reversed(snapshots):

            if snap.timestamp <= target_timestamp:

                return snap

        return None

    # ========================================================
    # APPLY EVENT
    # ========================================================

    def _apply_event(
        self,
        state: Dict[str, Any],
        event
    ) -> Dict[str, Any]:

        new_state = dict(state)

        # Payload completo
        if hasattr(event, "payload"):

            payload = getattr(
                event,
                "payload",
                {}
            )

            if isinstance(payload, dict):

                new_state.update(payload)

        # Metadata base
        new_state.update({

            "score":
            getattr(
                event,
                "impact_score",
                0
            ),

            "last_event":
            getattr(
                event,
                "event_type",
                "UNKNOWN"
            ),

            "last_engine":
            getattr(
                event,
                "engine",
                ""
            ),

            "last_timestamp":
            getattr(
                event,
                "timestamp",
                ""
            )

        })

        return new_state

    # ========================================================
    # MAIN REBUILD
    # ========================================================

    def rebuild(
        self,
        tenant_id: str,
        target_timestamp: Optional[str] = None
    ) -> RebuildResult:

        trace_id = str(uuid.uuid4())

        target_timestamp = self.safe_timestamp(
            target_timestamp
        )

        base_state: Dict[str, Any] = {}

        snapshot_id = None

        snapshot_used = False

        events_applied = 0

        warnings = []

        # ----------------------------------------------------
        # 1. SNAPSHOT BASE
        # ----------------------------------------------------

        snapshot = self._resolve_snapshot(
            tenant_id,
            target_timestamp
        )

        if snapshot:

            base_state = dict(
                snapshot.full_state
            )

            snapshot_id = snapshot.snapshot_id

            snapshot_used = True

        else:

            warnings.append(
                "No se encontró snapshot base."
            )

        # ----------------------------------------------------
        # 2. EVENT REPLAY
        # ----------------------------------------------------

        if self.replay:

            replay_result = self.replay.replay_by_tenant(
                tenant_id
            )

            for event in replay_result.timeline:

                event_ts = getattr(
                    event,
                    "timestamp",
                    ""
                )

                # Skip eventos posteriores
                if (
                    target_timestamp
                    and
                    event_ts > target_timestamp
                ):

                    continue

                # Skip eventos ya incluidos
                if (
                    snapshot
                    and
                    event_ts <= snapshot.timestamp
                ):

                    continue

                base_state = self._apply_event(
                    base_state,
                    event
                )

                events_applied += 1

        else:

            warnings.append(
                "Replay engine no disponible."
            )

        # ----------------------------------------------------
        # 3. INTEGRITY HASH
        # ----------------------------------------------------

        integrity_hash = self.calculate_hash(
            base_state
        )

        # ----------------------------------------------------
        # 4. STATUS
        # ----------------------------------------------------

        if base_state:

            status = (
                RebuildStatus.SUCCESS
                if snapshot_used
                else RebuildStatus.PARTIAL
            )

            success = True

        else:

            status = RebuildStatus.FAILED

            success = False

        # ----------------------------------------------------
        # 5. METADATA
        # ----------------------------------------------------

        metadata = {

            "snapshot_used":
            snapshot_used,

            "events_applied":
            events_applied,

            "warnings_count":
            len(warnings),

            "target_timestamp":
            target_timestamp,

            "state_size":
            len(base_state)

        }

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return RebuildResult(

            tenant_id=tenant_id,

            success=success,

            status=status,

            rebuilt_state=base_state,

            events_applied=events_applied,

            snapshot_used=snapshot_used,

            snapshot_id=snapshot_id,

            target_timestamp=target_timestamp,

            integrity_hash=integrity_hash,

            warnings=warnings,

            metadata=metadata,

            trace_id=trace_id,

            engine_version=self.VERSION

        )

    # ========================================================
    # AUDIT TRAIL
    # ========================================================

    def audit_trail(
        self,
        tenant_id: str
    ) -> List[dict]:

        trail = []

        # ----------------------------------------------------
        # SNAPSHOTS
        # ----------------------------------------------------

        if self.snapshot:

            for s in self.snapshot._snapshots.values():

                if s.tenant_id != tenant_id:

                    continue

                trail.append({

                    "type":
                    "SNAPSHOT",

                    "timestamp":
                    s.timestamp,

                    "score":
                    s.score,

                    "hash":
                    s.state_hash,

                    "snapshot_id":
                    s.snapshot_id

                })

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        if self.replay:

            replay = self.replay.replay_by_tenant(
                tenant_id
            )

            for e in replay.timeline:

                trail.append({

                    "type":
                    "EVENT",

                    "timestamp":
                    e.timestamp,

                    "score":
                    e.impact_score,

                    "event":
                    e.event_type,

                    "engine":
                    e.engine

                })

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        return sorted(

            trail,

            key=lambda x: x.get(
                "timestamp",
                ""
            )

        )

    # ========================================================
    # VERIFY INTEGRITY
    # ========================================================

    def verify_integrity(
        self,
        state: Dict[str, Any],
        expected_hash: str
    ) -> bool:

        current_hash = self.calculate_hash(
            state
        )

        return current_hash == expected_hash
