# core/temporal_replay_engine.py
# MESAN Omega — Temporal Replay Engine v2.0
# Enterprise Hardened | Event Sourcing Foundation

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import time


# ============================================================
# ENUMS
# ============================================================

class RiskTrend(str, Enum):
    ESTABLE = "ESTABLE"
    DETERIORO = "DETERIORO"
    MEJORIA = "MEJORIA"
    VOLATIL = "VOLATIL"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ReplayEvent:
    event_id: str
    timestamp: str
    event_type: str
    engine: str
    impact_score: float
    payload: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""
    tenant_id: str = ""


@dataclass
class ReplayResult:
    tenant_id: str

    total_events: int

    reconstructed_state: Dict[str, Any]

    deterioration_detected: bool

    trend: RiskTrend

    score_delta: float

    first_score: float
    last_score: float

    timeline: List[ReplayEvent]

    risk_progression: List[Dict[str, Any]]

    trace_id: str

    engine_version: str

    replay_duration_ms: float = 0.0

    timestamp: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class TemporalReplayEngine:

    VERSION = "2.0.0"

    # ========================================================
    # INIT
    # ========================================================

    def __init__(self):

        # TODO:
        # reemplazar por PostgreSQL/Event Store
        self._store: List[dict] = []

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
    def safe_timestamp(value: str) -> str:

        try:

            datetime.fromisoformat(
                value.replace("Z", "")
            )

            return value

        except Exception:

            return datetime.utcnow().isoformat()

    # ========================================================
    # EVENT APPEND
    # ========================================================

    def append_event(
        self,
        event: Dict[str, Any]
    ) -> None:

        normalized = {

            "event_id":
            event.get(
                "event_id",
                str(uuid.uuid4())
            ),

            "timestamp":
            self.safe_timestamp(
                event.get(
                    "timestamp",
                    datetime.utcnow().isoformat()
                )
            ),

            "event_type":
            event.get(
                "event_type",
                "UNKNOWN"
            ),

            "engine":
            event.get(
                "engine",
                "UNKNOWN_ENGINE"
            ),

            "score":
            self.safe_float(
                event.get(
                    "score",
                    0
                )
            ),

            "payload":
            event.get(
                "payload",
                {}
            ),

            "trace_id":
            event.get(
                "trace_id",
                ""
            ),

            "tenant_id":
            event.get(
                "tenant_id",
                ""
            )

        }

        self._store.append(normalized)

    # ========================================================
    # REPLAY METHODS
    # ========================================================

    def replay_by_trace(
        self,
        trace_id: str
    ) -> ReplayResult:

        events = [

            e for e in self._store

            if e.get("trace_id") == trace_id

        ]

        return self._build_result(
            ref_id=trace_id,
            raw_events=events
        )

    # --------------------------------------------------------

    def replay_by_tenant(
        self,
        tenant_id: str
    ) -> ReplayResult:

        events = [

            e for e in self._store

            if e.get("tenant_id") == tenant_id

        ]

        return self._build_result(
            ref_id=tenant_id,
            raw_events=events
        )

    # --------------------------------------------------------

    def replay_by_date_range(
        self,
        tenant_id: str,
        start: str,
        end: str
    ) -> ReplayResult:

        events = [

            e for e in self._store

            if (
                e.get("tenant_id") == tenant_id
                and
                start <= e.get("timestamp", "") <= end
            )

        ]

        return self._build_result(
            ref_id=tenant_id,
            raw_events=events
        )

    # ========================================================
    # TREND DETECTION
    # ========================================================

    def _detect_trend(
        self,
        first_score: float,
        last_score: float
    ) -> tuple:

        delta = round(
            last_score - first_score,
            2
        )

        if delta > 10:

            return (
                RiskTrend.DETERIORO,
                True,
                delta
            )

        if delta < -10:

            return (
                RiskTrend.MEJORIA,
                False,
                delta
            )

        if abs(delta) >= 5:

            return (
                RiskTrend.VOLATIL,
                False,
                delta
            )

        return (
            RiskTrend.ESTABLE,
            False,
            delta
        )

    # ========================================================
    # RESULT BUILDER
    # ========================================================

    def _build_result(
        self,
        ref_id: str,
        raw_events: List[dict]
    ) -> ReplayResult:

        t0 = time.perf_counter()

        # ----------------------------------------------------
        # SORT
        # ----------------------------------------------------

        sorted_events = sorted(

            raw_events,

            key=lambda e: e.get(
                "timestamp",
                ""
            )

        )

        # ----------------------------------------------------
        # TIMELINE
        # ----------------------------------------------------

        timeline = []

        for e in sorted_events:

            timeline.append(

                ReplayEvent(

                    event_id=e.get(
                        "event_id",
                        str(uuid.uuid4())
                    ),

                    timestamp=e.get(
                        "timestamp",
                        ""
                    ),

                    event_type=e.get(
                        "event_type",
                        "UNKNOWN"
                    ),

                    engine=e.get(
                        "engine",
                        ""
                    ),

                    impact_score=self.safe_float(
                        e.get(
                            "score",
                            0
                        )
                    ),

                    payload=e.get(
                        "payload",
                        {}
                    ),

                    trace_id=e.get(
                        "trace_id",
                        ""
                    ),

                    tenant_id=e.get(
                        "tenant_id",
                        ""
                    )

                )

            )

        # ----------------------------------------------------
        # RISK PROGRESSION
        # ----------------------------------------------------

        risk_progression = [

            {

                "timestamp":
                e.timestamp,

                "score":
                e.impact_score,

                "event":
                e.event_type,

                "engine":
                e.engine

            }

            for e in timeline

        ]

        # ----------------------------------------------------
        # SCORE ANALYSIS
        # ----------------------------------------------------

        first_score = (
            timeline[0].impact_score
            if timeline
            else 0
        )

        last_score = (
            timeline[-1].impact_score
            if timeline
            else 0
        )

        trend, deterioration, delta = (
            self._detect_trend(
                first_score,
                last_score
            )
        )

        # ----------------------------------------------------
        # RECONSTRUCTED STATE
        # ----------------------------------------------------

        reconstructed = {}

        for event in sorted_events:

            payload = event.get(
                "payload",
                {}
            )

            if isinstance(payload, dict):

                reconstructed.update(payload)

        # ----------------------------------------------------
        # PERFORMANCE
        # ----------------------------------------------------

        duration = round(
            (
                time.perf_counter() - t0
            ) * 1000,
            2
        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return ReplayResult(

            tenant_id=ref_id,

            total_events=len(timeline),

            reconstructed_state=reconstructed,

            deterioration_detected=deterioration,

            trend=trend,

            score_delta=delta,

            first_score=first_score,

            last_score=last_score,

            timeline=timeline,

            risk_progression=risk_progression,

            trace_id=str(uuid.uuid4()),

            engine_version=self.VERSION,

            replay_duration_ms=duration

        )
