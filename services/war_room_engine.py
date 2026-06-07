# services/war_room_engine.py -- MESAN Omega v1.0
"""
War Room Engine Ω

Única autoridad para la decisión de activación del War Room.

Problema resuelto:
    4 engines tomaban la decisión de war_room_required de forma independiente
    con criterios distintos y potencialmente contradictorios.

Arquitectura:
    Los engines reportan señales (hallazgos, scores, exposición).
    El WarRoomEngine toma la decisión final basándose en todas las señales.

Outputs exclusivos:
    war_room_required   bool
    war_room_score      0-100
    war_room_priority   INMEDIATA / 24H / 48H / 7_DIAS / MONITOREO
    war_room_reason     Lista de razones que activaron el War Room
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# UMBRALES DE ACTIVACIÓN
# ══════════════════════════════════════════════════════════════════════════════

# ESI-Ω por debajo de este umbral activa War Room
WAR_ROOM_ESI_THRESHOLD        = 50

# Exposición total que activa War Room automáticamente
WAR_ROOM_EXPOSURE_THRESHOLD   = 1_000_000

# Governance score mínimo (por debajo activa War Room)
WAR_ROOM_GOVERNANCE_THRESHOLD = 50

# Número de hallazgos críticos que activa War Room
WAR_ROOM_CRITICAL_FINDINGS    = 1

# War Room score por encima del cual se requiere activación
WAR_ROOM_SCORE_THRESHOLD      = 60


# ══════════════════════════════════════════════════════════════════════════════
# SEÑALES DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WarRoomSignals:
    """
    Señales consolidadas desde todos los engines del pipeline.
    El WarRoomEngine toma su decisión basándose en estas señales.
    """
    enterprise_survival_index:  int   = 100
    governance_score:           float = 100.0
    total_exposure_mxn:         float = 0.0
    critical_findings_count:    int   = 0
    open_circuits:              int   = 0    # del ObservabilityBus
    engine_signals:             dict  = field(default_factory=dict)
    # Señales de engines individuales — solo informativas
    # { "fiscal": bool, "labor": bool, "contractual": bool, ... }


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WarRoomResult:
    required:  bool
    score:     int            # 0-100: mayor = situación más crítica
    priority:  str            # INMEDIATA / 24H / 48H / 7_DIAS / MONITOREO
    reasons:   List[str]      # Razones que activaron el War Room
    signals:   WarRoomSignals # Señales de entrada para trazabilidad

    def to_dict(self) -> dict:
        return {
            "war_room_required": self.required,
            "war_room_score":    self.score,
            "war_room_priority": self.priority,
            "war_room_reasons":  self.reasons,
        }


# ══════════════════════════════════════════════════════════════════════════════
# WAR ROOM ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class WarRoomEngine:
    """
    Autoridad central para la decisión de activación del War Room.

    Uso:
        engine  = WarRoomEngine()
        signals = WarRoomSignals(
            enterprise_survival_index = 45,
            governance_score          = 48.0,
            total_exposure_mxn        = 1_500_000,
            critical_findings_count   = 3,
        )
        result = engine.evaluate(signals)
        print(result.required)   # True
        print(result.priority)   # "INMEDIATA"
        print(result.reasons)    # ["ESI-Ω por debajo de umbral crítico (45)", ...]
    """

    def evaluate(self, signals: WarRoomSignals) -> WarRoomResult:
        """
        Evalúa todas las señales y decide si activar el War Room.
        La decisión es determinística y auditable.
        """
        reasons: List[str] = []
        score   = 0

        # ── Criterio 1: ESI-Ω crítico ─────────────────────────────────────
        if signals.enterprise_survival_index < WAR_ROOM_ESI_THRESHOLD:
            reasons.append(
                f"ESI-Ω por debajo de umbral crítico "
                f"({signals.enterprise_survival_index} < {WAR_ROOM_ESI_THRESHOLD})"
            )
            score += 30

        # ── Criterio 2: Exposición total ──────────────────────────────────
        if signals.total_exposure_mxn >= WAR_ROOM_EXPOSURE_THRESHOLD:
            reasons.append(
                f"Exposición total supera umbral War Room "
                f"(${signals.total_exposure_mxn:,.0f} MXN)"
            )
            score += 25

        # ── Criterio 3: Governance crítico ────────────────────────────────
        if signals.governance_score < WAR_ROOM_GOVERNANCE_THRESHOLD:
            reasons.append(
                f"Governance score crítico "
                f"({signals.governance_score:.1f} < {WAR_ROOM_GOVERNANCE_THRESHOLD})"
            )
            score += 25

        # ── Criterio 4: Hallazgos críticos ────────────────────────────────
        if signals.critical_findings_count >= WAR_ROOM_CRITICAL_FINDINGS:
            reasons.append(
                f"{signals.critical_findings_count} hallazgo(s) crítico(s) detectado(s)"
            )
            score += min(signals.critical_findings_count * 5, 20)

        # ── Criterio 5: Circuitos abiertos (ObservabilityBus) ─────────────
        if signals.open_circuits > 0:
            reasons.append(
                f"{signals.open_circuits} circuito(s) de motor abierto(s)"
            )
            score += signals.open_circuits * 5

        # ── Señales de engines individuales (informativas) ────────────────
        engine_war_rooms = [
            k for k, v in signals.engine_signals.items()
            if v is True
        ]
        if engine_war_rooms:
            reasons.append(
                f"Señales War Room desde: {', '.join(engine_war_rooms)}"
            )
            score += min(len(engine_war_rooms) * 3, 10)

        score    = min(score, 100)
        required = score >= WAR_ROOM_SCORE_THRESHOLD or len(reasons) > 0

        return WarRoomResult(
            required = required,
            score    = score,
            priority = self._classify_priority(score, signals),
            reasons  = reasons,
            signals  = signals,
        )

    def _classify_priority(self, score: int, signals: WarRoomSignals) -> str:
        """
        Determina la urgencia de intervención del War Room.
        Basada en score + señales específicas de alta gravedad.
        """
        # Condiciones de activación inmediata independiente del score
        if (signals.enterprise_survival_index < 40
                or signals.total_exposure_mxn >= 2_000_000
                or signals.governance_score < 40):
            return "INMEDIATA"

        if score >= 80: return "INMEDIATA"
        if score >= 60: return "24H"
        if score >= 40: return "48H"
        if score >= 20: return "7_DIAS"
        return "MONITOREO"

    # ── Constructor de señales desde pipeline ────────────────────────────────

    @staticmethod
    def build_signals(
        pipeline_results:          dict,
        enterprise_survival_index: int   = 100,
        total_exposure_mxn:        float = 0.0,
        open_circuits:             int   = 0,
    ) -> WarRoomSignals:
        """
        Construye WarRoomSignals desde los resultados del pipeline.

        Extrae señales de war_room_required de cada engine
        como información, no como decisión.
        """
        engine_signals = {}
        critical_count = 0

        for key, result in pipeline_results.items():
            if not isinstance(result, dict):
                continue
            # Señal informativa del engine (no decisión final)
            if result.get("war_room_required"):
                engine_signals[key] = True
            # Sumar hallazgos críticos
            critical_count += int(result.get("critical_findings_count", 0))

        governance_score = float(
            pipeline_results.get("governance", {}).get("governance_score", 100)
        )

        return WarRoomSignals(
            enterprise_survival_index = enterprise_survival_index,
            governance_score          = governance_score,
            total_exposure_mxn        = total_exposure_mxn,
            critical_findings_count   = critical_count,
            open_circuits             = open_circuits,
            engine_signals            = engine_signals,
        )


# Instancia global
war_room_engine = WarRoomEngine()
