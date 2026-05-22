# core/timeline_engine.py
# MESAN Omega — Timeline Engine v2.0
# Enterprise Temporal Intelligence Layer

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ============================================================
# ENUMS
# ============================================================

class RiskLevel(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class TrendType(str, Enum):
    ESTABLE = "ESTABLE"
    MEJORA = "MEJORA"
    DETERIORO = "DETERIORO"
    VOLATIL = "VOLATIL"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class TimelinePoint:

    point_id: str

    timestamp: str

    score: float

    confidence: float

    nivel: RiskLevel

    evento: str

    descripcion: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class TimelineResult:

    tenant_id: str

    total_points: int

    trend: TrendType

    score_delta: float

    confidence_delta: float

    deterioration_events: List[TimelinePoint]

    improvement_events: List[TimelinePoint]

    critical_events: List[TimelinePoint]

    volatility_events: List[TimelinePoint]

    timeline: List[TimelinePoint]

    trace_id: str

    engine_version: str

    summary: str

    generated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class TimelineEngine:

    VERSION = "2.0.0"

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
    # RISK CLASSIFIER
    # ========================================================

    def _risk_level(
        self,
        score: float
    ) -> RiskLevel:

        if score >= 85:
            return RiskLevel.CRITICO

        if score >= 65:
            return RiskLevel.ALTO

        if score >= 40:
            return RiskLevel.MEDIO

        return RiskLevel.BAJO

    # ========================================================
    # TREND DETECTION
    # ========================================================

    def _detect_trend(
        self,
        points: List[TimelinePoint]
    ) -> tuple:

        if len(points) < 2:

            return (
                TrendType.ESTABLE,
                0.0,
                0.0
            )

        score_delta = round(
            points[-1].score -
            points[0].score,
            2
        )

        confidence_delta = round(
            points[-1].confidence -
            points[0].confidence,
            4
        )

        if abs(score_delta) >= 20:

            trend = TrendType.VOLATIL

        elif score_delta > 5:

            trend = TrendType.DETERIORO

        elif score_delta < -5:

            trend = TrendType.MEJORA

        else:

            trend = TrendType.ESTABLE

        return (
            trend,
            score_delta,
            confidence_delta
        )

    # ========================================================
    # MAIN ENGINE
    # ========================================================

    def build_timeline(
        self,
        tenant_id: str,
        events: List[dict]
    ) -> TimelineResult:

        # ----------------------------------------------------
        # SORT EVENTS
        # ----------------------------------------------------

        sorted_events = sorted(

            events,

            key=lambda e: e.get(
                "timestamp",
                ""
            )

        )

        points: List[
            TimelinePoint
        ] = []

        # ----------------------------------------------------
        # BUILD TIMELINE
        # ----------------------------------------------------

        for e in sorted_events:

            score = self.safe_float(
                e.get("score")
            )

            confidence = self.safe_float(
                e.get(
                    "confidence",
                    0.82
                )
            )

            point = TimelinePoint(

                point_id=str(uuid.uuid4()),

                timestamp=self.safe_timestamp(
                    e.get(
                        "timestamp",
                        ""
                    )
                ),

                score=round(score, 2),

                confidence=round(
                    confidence,
                    4
                ),

                nivel=self._risk_level(
                    score
                ),

                evento=e.get(
                    "event_type",
                    "UNKNOWN"
                ),

                descripcion=e.get(
                    "descripcion",
                    ""
                ),

                metadata=e.get(
                    "metadata",
                    {}
                )

            )

            points.append(point)

        # ----------------------------------------------------
        # DETECT EVENTS
        # ----------------------------------------------------

        deterioration = []

        improvement = []

        volatility = []

        for i in range(1, len(points)):

            previous = points[i - 1]

            current = points[i]

            delta = (
                current.score -
                previous.score
            )

            # Deterioro
            if delta > 5:

                deterioration.append(
                    current
                )

            # Mejora
            elif delta < -5:

                improvement.append(
                    current
                )

            # Volatilidad extrema
            if abs(delta) >= 20:

                volatility.append(
                    current
                )

        # ----------------------------------------------------
        # CRITICAL EVENTS
        # ----------------------------------------------------

        critical = [

            p for p in points

            if p.nivel == RiskLevel.CRITICO

        ]

        # ----------------------------------------------------
        # GLOBAL TREND
        # ----------------------------------------------------

        (
            trend,
            score_delta,
            confidence_delta
        ) = self._detect_trend(points)

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        summary = (

            f"Timeline con "

            f"{len(points)} eventos "

            f"para tenant {tenant_id}. "

            f"Tendencia general: "

            f"{trend.value}. "

            f"Delta score: "

            f"{score_delta:+.2f}. "

            f"Eventos críticos: "

            f"{len(critical)}. "

            f"Deterioros detectados: "

            f"{len(deterioration)}. "

            f"Volatilidad extrema: "

            f"{len(volatility)}."

        )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return TimelineResult(

            tenant_id=tenant_id,

            total_points=len(points),

            trend=trend,

            score_delta=score_delta,

            confidence_delta=confidence_delta,

            deterioration_events=deterioration,

            improvement_events=improvement,

            critical_events=critical,

            volatility_events=volatility,

            timeline=points,

            trace_id=str(uuid.uuid4()),

            engine_version=self.VERSION,

            summary=summary

        )

    # ========================================================
    # COLLAPSE DETECTOR
    # ========================================================

    def detect_collapse_risk(
        self,
        points: List[TimelinePoint]
    ) -> Dict[str, Any]:

        if len(points) < 3:

            return {

                "collapse_risk":
                False,

                "reason":
                "Insuficientes datos"

            }

        last3 = points[-3:]

        scores = [
            p.score for p in last3
        ]

        consecutive_increase = all(

            scores[i] < scores[i + 1]

            for i in range(
                len(scores) - 1
            )

        )

        acceleration = (
            scores[-1] - scores[0]
        )

        collapse = (

            consecutive_increase

            and

            scores[-1] >= 65

            and

            acceleration >= 15

        )

        return {

            "collapse_risk":
            collapse,

            "trend":
            scores,

            "score_acceleration":
            round(acceleration, 2),

            "current_score":
            scores[-1],

            "recommendation":
            (
                "Intervención inmediata requerida."
                if collapse
                else
                "Continuar monitoreo."
            ),

            "evaluated_at":
            datetime.utcnow().isoformat()

        }
