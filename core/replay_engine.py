# core/replay_engine.py -- MESAN Omega Enterprise Replay Engine v1.1
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib, json, logging

logger = logging.getLogger("mesan.replay")

@dataclass
class ReplayEvent:
    timestamp: str; tenant_id: str; trace_id: str
    engine: str; event_type: str; severity: str
    payload: Dict[str,Any] = field(default_factory=dict)

@dataclass
class ReplayTimeline:
    tenant_id: str; total_events: int
    first_event: Optional[str]; last_event: Optional[str]
    integrity_hash: str
    timeline: List[ReplayEvent] = field(default_factory=list)

class ReplayEngine:
    VERSION = "1.1.0"

    def __init__(self, db=None):
        self.db = db

    def rebuild_company_timeline(self, tenant_id: str) -> ReplayTimeline:
        if not self.db:
            logger.warning("[REPLAY] Database not configured")
            return ReplayTimeline(tenant_id, 0, None, None, "NO_DATABASE", [])

        from models.database import EnterpriseEvent
        events = (self.db.query(EnterpriseEvent)
                  .filter(EnterpriseEvent.tenant_id == tenant_id)
                  .order_by(EnterpriseEvent.timestamp.asc()).all())

        timeline = [ReplayEvent(e.timestamp.isoformat(), e.tenant_id, e.trace_id,
                                e.engine_type, e.event_type, e.severity,
                                getattr(e,"payload",{}) or {}) for e in events]

        return ReplayTimeline(tenant_id=tenant_id, total_events=len(timeline),
                              first_event=timeline[0].timestamp if timeline else None,
                              last_event=timeline[-1].timestamp if timeline else None,
                              integrity_hash=self._build_integrity_hash(timeline),
                              timeline=timeline)

    def replay_trace(self, trace_id: str) -> List[ReplayEvent]:
        if not self.db: return []
        from models.database import EnterpriseEvent
        events = (self.db.query(EnterpriseEvent)
                  .filter(EnterpriseEvent.trace_id == trace_id)
                  .order_by(EnterpriseEvent.timestamp.asc()).all())
        return [ReplayEvent(e.timestamp.isoformat(), e.tenant_id, e.trace_id,
                            e.engine_type, e.event_type, e.severity,
                            getattr(e,"payload",{}) or {}) for e in events]

    def detect_event_gaps(self, tenant_id: str) -> dict:
        timeline = self.rebuild_company_timeline(tenant_id)
        if timeline.total_events < 2:
            return {"gaps_detected": False, "reason": "Insufficient events"}
        gaps = []; prev = None
        for event in timeline.timeline:
            curr = datetime.fromisoformat(event.timestamp)
            if prev:
                delta = (curr - prev).total_seconds()
                if delta > 86400:
                    gaps.append({"gap_hours": round(delta/3600,2),
                                 "before": prev.isoformat(), "after": curr.isoformat()})
            prev = curr
        return {"gaps_detected": len(gaps)>0, "total_gaps": len(gaps), "gaps": gaps}

    def health(self) -> dict:
        return {"status": "HEALTHY" if self.db else "DEGRADED",
                "database_connected": bool(self.db), "version": self.VERSION,
                "timestamp": datetime.utcnow().isoformat()}

    def _build_integrity_hash(self, timeline: List[ReplayEvent]) -> str:
        serialized = json.dumps([{"timestamp":e.timestamp,"trace_id":e.trace_id,
                                   "engine":e.engine,"event_type":e.event_type}
                                  for e in timeline], sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
