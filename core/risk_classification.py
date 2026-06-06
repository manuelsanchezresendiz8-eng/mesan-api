# core/risk_classification.py -- MESAN Omega v1.0
"""
RiskClassificationService Ω

Centraliza toda la lógica de clasificación de riesgo de MESAN Ω.
Elimina duplicación entre ContinuityEngine, CrisisSimulationLayer y futuros motores.

Regla de diseño:
    Ningún módulo debe definir "CRITICO/ALTO/MEDIO" localmente.
    Todos importan desde aquí.

Uso:
    from core.risk_classification import RiskClassificationService
    svc = RiskClassificationService()
    svc.classify_esi(74)          → "VIGILANCIA"
    svc.classify_risk_level(48)   → "CRITICO"
    svc.classify_health_score(93) → "SALUDABLE"
"""

from dataclasses import dataclass
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES CENTRALIZADAS
# ══════════════════════════════════════════════════════════════════════════════

# ESI-Ω — umbrales de clasificación empresarial
ESI_ROBUSTA        = 90
ESI_ESTABLE        = 80
ESI_VIGILANCIA     = 70
ESI_RIESGO_ELEVADO = 60

# Nivel de riesgo operativo — usado en CrisisSimulationLayer y Digital Twin
RISK_CRITICO_THRESHOLD = 60
RISK_ALTO_THRESHOLD    = 75

# Health Score — usado en ObservabilityBus
HEALTH_OPTIMO    = 90
HEALTH_SALUDABLE = 75
HEALTH_DEGRADADO = 50


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO DE CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ClassificationResult:
    """Resultado de una clasificación con nivel y etiqueta legible."""
    nivel:    str    # ROBUSTA | ESTABLE | VIGILANCIA | RIESGO_ELEVADO | CRITICA
    etiqueta: str    # Texto para UI ejecutiva
    color:    str    # Semántica de color: green | yellow | orange | red


# ══════════════════════════════════════════════════════════════════════════════
# RISK CLASSIFICATION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

class RiskClassificationService:
    """
    Servicio centralizado de clasificación de riesgo MESAN Ω.

    Tres dominios:
        classify_esi()          → clasificación del ESI-Ω empresarial
        classify_risk_level()   → nivel operativo CRITICO/ALTO/MEDIO
        classify_health_score() → salud de motores del Observability Bus
    """

    # ── ESI-Ω Empresarial ─────────────────────────────────────────────────────

    def classify_esi(self, esi: int) -> str:
        """
        Clasifica el Enterprise Survival Index Ω.
        Estándar único para todo MESAN Ω.

        90-100 → ROBUSTA
        80-89  → ESTABLE
        70-79  → VIGILANCIA
        60-69  → RIESGO_ELEVADO
        0-59   → CRITICA
        """
        if esi >= ESI_ROBUSTA:
            return "ROBUSTA"
        if esi >= ESI_ESTABLE:
            return "ESTABLE"
        if esi >= ESI_VIGILANCIA:
            return "VIGILANCIA"
        if esi >= ESI_RIESGO_ELEVADO:
            return "RIESGO_ELEVADO"
        return "CRITICA"

    def classify_esi_full(self, esi: int) -> ClassificationResult:
        """Clasifica ESI con etiqueta completa y semántica de color."""
        nivel = self.classify_esi(esi)
        _map = {
            "ROBUSTA":        ClassificationResult("ROBUSTA",        "Empresa Robusta",          "green"),
            "ESTABLE":        ClassificationResult("ESTABLE",        "Operación Estable",        "green"),
            "VIGILANCIA":     ClassificationResult("VIGILANCIA",     "Requiere Vigilancia",      "yellow"),
            "RIESGO_ELEVADO": ClassificationResult("RIESGO_ELEVADO", "Riesgo Elevado",           "orange"),
            "CRITICA":        ClassificationResult("CRITICA",        "Situación Crítica",        "red"),
        }
        return _map[nivel]

    # ── Nivel de riesgo operativo ─────────────────────────────────────────────

    def classify_risk_level(self, esi: int) -> str:
        """
        Clasificación binaria de riesgo operativo.
        Usada en CrisisSimulationLayer y Digital Twin.

        < 60  → CRITICO
        < 75  → ALTO
        >= 75 → MEDIO
        """
        if esi < RISK_CRITICO_THRESHOLD:
            return "CRITICO"
        if esi < RISK_ALTO_THRESHOLD:
            return "ALTO"
        return "MEDIO"

    def classify_days_risk(self, dias_supervivencia: int) -> str:
        """
        Clasifica riesgo por días de supervivencia operativa.
        Usado en Digital Twin simulate_cashflow_drop y simulate_perdida_cliente.

        < 15 días → CRITICO
        < 30 días → ALTO
        >= 30     → MEDIO
        """
        if dias_supervivencia < 15:
            return "CRITICO"
        if dias_supervivencia < 30:
            return "ALTO"
        return "MEDIO"

    def classify_flujo(self, flujo: float, referencia: Optional[float] = None) -> str:
        """
        Clasifica riesgo por flujo operativo.
        Usado en Digital Twin simulate_embargo y simulate_nomina_aumento.

        flujo < 0               → CRITICO
        flujo < referencia*0.2  → ALTO (margen muy estrecho)
        flujo >= referencia*0.2 → MEDIO
        """
        if flujo < 0:
            return "CRITICO"
        if referencia and flujo < referencia * 0.20:
            return "ALTO"
        return "MEDIO"

    # ── Health Score (Observability Bus) ──────────────────────────────────────

    def classify_health_score(self, score: int) -> str:
        """
        Clasifica health score de motores del Observability Bus.

        >= 90 → OPTIMO
        >= 75 → SALUDABLE
        >= 50 → DEGRADADO
        < 50  → CRITICO
        """
        if score >= HEALTH_OPTIMO:
            return "OPTIMO"
        if score >= HEALTH_SALUDABLE:
            return "SALUDABLE"
        if score >= HEALTH_DEGRADADO:
            return "DEGRADADO"
        return "CRITICO"


# Instancia global — importar directamente para uso sin instanciar
risk_classifier = RiskClassificationService()
