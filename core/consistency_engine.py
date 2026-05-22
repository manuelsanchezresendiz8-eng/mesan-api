# core/consistency_engine.py
# MESAN Omega — Consistency Engine v2.0
# Cross-Engine Integrity Validation Layer

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# ============================================================
# ENUMS
# ============================================================

class SeverityLevel(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"


class ViolationType(str, Enum):
    SCORE_DIVERGENCE = "SCORE_DIVERGENCE"
    STATE_DIVERGENCE = "STATE_DIVERGENCE"
    CONFIDENCE_MISMATCH = "CONFIDENCE_MISMATCH"
    TIMELINE_INCONSISTENCY = "TIMELINE_INCONSISTENCY"
    EXPOSURE_MISMATCH = "EXPOSURE_MISMATCH"
    RISK_CLASSIFICATION_MISMATCH = "RISK_CLASSIFICATION_MISMATCH"


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class ConsistencyViolation:

    violation_id: str

    source_engine: str

    target_engine: str

    violation_type: ViolationType

    severity: SeverityLevel

    explanation: str

    delta: float = 0.0

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ConsistencyResult:

    system_consistent: bool

    violations: List[
        ConsistencyViolation
    ] = field(default_factory=list)

    total_violations: int = 0

    critical_violations: int = 0

    high_violations: int = 0

    system_confidence: float = 1.0

    integrity_score: float = 100.0

    trace_id: str = ""

    engine_version: str = ""

    timestamp: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )


# ============================================================
# ENGINE
# ============================================================

class ConsistencyEngine:

    VERSION = "2.0.0"

    # ========================================================
    # SAFE HELPERS
    # ========================================================

    @staticmethod
    def safe_float(value, default=0.0):

        try:

            if value in [None, "", "null"]:

                return default

            return float(value)

        except (TypeError, ValueError):

            return default

    # ========================================================
    # ADD VIOLATION
    # ========================================================

    def _add_violation(
        self,
        violations: List[ConsistencyViolation],
        source: str,
        target: str,
        violation_type: ViolationType,
        severity: SeverityLevel,
        explanation: str,
        delta: float = 0.0,
        metadata: Dict[str, Any] = None
    ):

        violations.append(

            ConsistencyViolation(

                violation_id=str(uuid.uuid4()),

                source_engine=source,

                target_engine=target,

                violation_type=violation_type,

                severity=severity,

                explanation=explanation,

                delta=round(delta, 2),

                metadata=metadata or {}

            )

        )

    # ========================================================
    # MAIN VALIDATOR
    # ========================================================

    def validate_cross_engine_consistency(
        self,
        states: Dict[str, Any]
    ) -> ConsistencyResult:

        trace_id = str(uuid.uuid4())

        violations: List[
            ConsistencyViolation
        ] = []

        # ----------------------------------------------------
        # SCORES
        # ----------------------------------------------------

        exposure_score = self.safe_float(
            states.get("exposure_score")
        )

        decision_score = self.safe_float(
            states.get("decision_score")
        )

        replay_score = self.safe_float(
            states.get("replay_score")
        )

        snapshot_score = self.safe_float(
            states.get("snapshot_score")
        )

        timeline_score = self.safe_float(
            states.get("timeline_score")
        )

        # ----------------------------------------------------
        # EXPOSURE vs DECISION
        # ----------------------------------------------------

        exposure_delta = abs(
            exposure_score -
            decision_score
        )

        if exposure_delta > 30:

            self._add_violation(

                violations,

                source="exposure_engine",

                target="decision_engine",

                violation_type=ViolationType.SCORE_DIVERGENCE,

                severity=(
                    SeverityLevel.CRITICO
                    if exposure_delta > 50
                    else SeverityLevel.ALTO
                ),

                explanation=(
                    f"Exposure score "
                    f"{exposure_score:.2f} "
                    f"diverge de decision score "
                    f"{decision_score:.2f}."
                ),

                delta=exposure_delta

            )

        # ----------------------------------------------------
        # REPLAY vs SNAPSHOT
        # ----------------------------------------------------

        replay_delta = abs(
            replay_score -
            snapshot_score
        )

        if replay_delta > 20:

            self._add_violation(

                violations,

                source="replay_engine",

                target="snapshot_engine",

                violation_type=ViolationType.STATE_DIVERGENCE,

                severity=(
                    SeverityLevel.CRITICO
                    if replay_delta > 40
                    else SeverityLevel.MEDIO
                ),

                explanation=(
                    f"Replay score "
                    f"{replay_score:.2f} "
                    f"diverge de snapshot score "
                    f"{snapshot_score:.2f}."
                ),

                delta=replay_delta

            )

        # ----------------------------------------------------
        # TIMELINE vs SNAPSHOT
        # ----------------------------------------------------

        timeline_delta = abs(
            timeline_score -
            snapshot_score
        )

        if timeline_delta > 25:

            self._add_violation(

                violations,

                source="timeline_engine",

                target="snapshot_engine",

                violation_type=ViolationType.TIMELINE_INCONSISTENCY,

                severity=SeverityLevel.ALTO,

                explanation=(
                    f"Timeline score "
                    f"{timeline_score:.2f} "
                    f"es inconsistente con snapshot "
                    f"{snapshot_score:.2f}."
                ),

                delta=timeline_delta

            )

        # ----------------------------------------------------
        # CONTRADICTIONS vs CONFIDENCE
        # ----------------------------------------------------

        contradictions = int(
            states.get(
                "contradictions",
                0
            )
        )

        confidence = self.safe_float(
            states.get(
                "confidence",
                1.0
            )
        )

        if (
            contradictions > 3
            and
            confidence > 0.85
        ):

            self._add_violation(

                violations,

                source="contradiction_engine",

                target="explainability_engine",

                violation_type=ViolationType.CONFIDENCE_MISMATCH,

                severity=SeverityLevel.ALTO,

                explanation=(
                    f"{contradictions} contradicciones "
                    f"con confianza "
                    f"{confidence:.2f} "
                    f"es inconsistente."
                ),

                delta=(
                    confidence * 100
                )

            )

        # ----------------------------------------------------
        # RISK CLASSIFICATION
        # ----------------------------------------------------

        risk_exposure = states.get(
            "exposure_risk",
            ""
        )

        risk_decision = states.get(
            "decision_risk",
            ""
        )

        if (
            risk_exposure
            and
            risk_decision
            and
            risk_exposure != risk_decision
        ):

            self._add_violation(

                violations,

                source="exposure_engine",

                target="decision_engine",

                violation_type=(
                    ViolationType
                    .RISK_CLASSIFICATION_MISMATCH
                ),

                severity=SeverityLevel.MEDIO,

                explanation=(
                    f"Clasificación de riesgo "
                    f"inconsistente: "
                    f"{risk_exposure} "
                    f"vs "
                    f"{risk_decision}."
                )

            )

        # ----------------------------------------------------
        # PENALTIES
        # ----------------------------------------------------

        penalty = 0.0

        for v in violations:

            if v.severity == SeverityLevel.CRITICO:

                penalty += 0.20

            elif v.severity == SeverityLevel.ALTO:

                penalty += 0.10

            elif v.severity == SeverityLevel.MEDIO:

                penalty += 0.05

            else:

                penalty += 0.02

        penalty = min(penalty, 0.65)

        system_confidence = max(
            0.35,
            1.0 - penalty
        )

        integrity_score = round(
            system_confidence * 100,
            2
        )

        critical_count = len([
            v for v in violations
            if v.severity ==
            SeverityLevel.CRITICO
        ])

        high_count = len([
            v for v in violations
            if v.severity ==
            SeverityLevel.ALTO
        ])

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return ConsistencyResult(

            system_consistent=(
                len(violations) == 0
            ),

            violations=violations,

            total_violations=len(
                violations
            ),

            critical_violations=(
                critical_count
            ),

            high_violations=(
                high_count
            ),

            system_confidence=round(
                system_confidence,
                3
            ),

            integrity_score=(
                integrity_score
            ),

            trace_id=trace_id,

            engine_version=self.VERSION

        )

    # ========================================================
    # STATE DIVERGENCE
    # ========================================================

    def detect_state_divergence(
        self,
        state_a: Dict[str, Any],
        state_b: Dict[str, Any]
    ) -> Dict[str, Any]:

        score_a = self.safe_float(
            state_a.get("score")
        )

        score_b = self.safe_float(
            state_b.get("score")
        )

        confidence_a = self.safe_float(
            state_a.get("confidence")
        )

        confidence_b = self.safe_float(
            state_b.get("confidence")
        )

        score_delta = abs(
            score_a - score_b
        )

        confidence_delta = abs(
            confidence_a - confidence_b
        )

        severity = (

            "CRITICO"

            if score_delta > 30

            else

            "ALTO"

            if score_delta > 15

            else

            "MEDIO"

            if score_delta > 5

            else

            "BAJO"

        )

        return {

            "divergence_detected":
            score_delta > 15,

            "score_delta":
            round(score_delta, 2),

            "confidence_delta":
            round(confidence_delta, 4),

            "severity":
            severity,

            "evaluated_at":
            datetime.utcnow().isoformat()

        }

    # ========================================================
    # GLOBAL CONFIDENCE
    # ========================================================

    def calculate_system_confidence(
        self,
        engine_results: List[dict]
    ) -> float:

        if not engine_results:

            return 0.50

        scores = []

        for r in engine_results:

            conf = self.safe_float(
                r.get("confidence")
            )

            if conf > 0:

                scores.append(conf)

        if not scores:

            return 0.50

        avg = sum(scores) / len(scores)

        return round(avg, 3)
