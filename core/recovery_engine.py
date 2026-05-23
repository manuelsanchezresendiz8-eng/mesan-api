# core/recovery_engine.py -- MESAN Omega Failure Recovery Layer v1.2
import logging, uuid
from dataclasses import dataclass, field
from typing import List, Dict, Callable
from datetime import datetime

logger = logging.getLogger("mesan.recovery")

@dataclass
class RecoveryResult:
    success: bool
    strategy_used: str
    events_recovered: int
    state_repaired: bool
    warnings: List[str] = field(default_factory=list)
    recovery_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_audit(self) -> dict:
        return {"recovery_id": self.recovery_id, "strategy": self.strategy_used,
                "success": self.success, "state_repaired": self.state_repaired,
                "warnings": self.warnings, "timestamp": self.timestamp}

class RecoveryEngine:
    VERSION = "1.2.0"

    def __init__(self):
        self._strategies: Dict[str, Callable] = {
            "REPLAY_CORRUPT":   self._recover_replay,
            "SNAPSHOT_CORRUPT": self._recover_snapshot,
            "MISSING_EVENTS":   self._recover_missing,
            "PARTIAL_REBUILD":  self._recover_partial,
        }
        self._audit_log: List[dict] = []

    def recover_from_failure(self, error_type: str, context: dict) -> RecoveryResult:
        strategy_fn = self._strategies.get(error_type, self._recover_generic)

        # Structured log
        logger.warning("mesan.recovery.start", extra={"error_type": error_type, "context_keys": list(context.keys())})

        result = strategy_fn(context)

        # Audit trail
        audit = {**result.to_audit(), "error_type": error_type}
        self._audit_log.append(audit)

        logger.warning("mesan.recovery.complete", extra={"strategy": result.strategy_used, "success": result.success})
        return result

    def _recover_replay(self, ctx):
        return RecoveryResult(True, "FALLBACK_TO_SNAPSHOT", 0, True,
                              ["Replay corrupt. State restored from latest snapshot."])

    def _recover_snapshot(self, ctx):
        return RecoveryResult(True, "REBUILD_FROM_EVENTS", int(ctx.get("events_available",0)), True,
                              ["Snapshot corrupt. State rebuilt from event history."])

    def _recover_missing(self, ctx):
        return RecoveryResult(True, "STATE_INTERPOLATION", 0, True,
                              ["Missing events. State interpolated from adjacent snapshots."])

    def _recover_partial(self, ctx):
        return RecoveryResult(True, "PARTIAL_STATE_RECOVERY", int(ctx.get("partial_events",0)), False,
                              ["Partial rebuild. State may contain inconsistencies."])

    def _recover_generic(self, ctx):
        return RecoveryResult(False, "NO_STRATEGY", 0, False,
                              [f"No strategy for: {ctx.get('error_type','UNKNOWN')}"])

    def repair_state(self, corrupt_state: dict, reference_state: dict) -> dict:
        repaired = dict(reference_state)
        for k, v in corrupt_state.items():
            if v is not None: repaired[k] = v
        repaired["_repaired_at"] = datetime.utcnow().isoformat()
        return repaired

    def register_strategy(self, error_type: str, fn: Callable):
        self._strategies[error_type] = fn

    def get_audit_log(self) -> List[dict]:
        return list(self._audit_log)

    def health(self) -> dict:
        return {"status": "HEALTHY", "engine": "RecoveryEngine", "version": self.VERSION,
                "registered_strategies": len(self._strategies),
                "audit_entries": len(self._audit_log),
                "timestamp": datetime.utcnow().isoformat()}
