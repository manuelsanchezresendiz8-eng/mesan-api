# core/risk_classification_protocol.py -- MESAN Omega v1.0
"""
RiskClassifierProtocol Ω

Interfaz formal para el clasificador de riesgo.
Desacopla los engines de la implementación concreta de RiskClassificationService.

Beneficio:
    Si RiskClassificationService cambia su escala o sus strings,
    los engines que dependan de este Protocol fallan en tiempo de diseño,
    no en producción.

Uso:
    from core.risk_classification_protocol import RiskClassifierProtocol

    def __init__(self, risk_classifier: RiskClassifierProtocol = None):
        self._risk = risk_classifier or default_risk_classifier()
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class RiskClassifierProtocol(Protocol):
    """
    Contrato mínimo que debe cumplir cualquier clasificador de riesgo en MESAN Ω.

    Implementado actualmente por: core.risk_classification.RiskClassificationService
    """

    def classify_esi(self, score: int) -> str:
        """
        Clasifica un Enterprise Survival Index Ω.

        Args:
            score: Entero 0-100 (mayor = más saludable)

        Returns:
            Una de: "ROBUSTA" | "ESTABLE" | "VIGILANCIA" | "RIESGO_ELEVADO" | "CRITICA"
        """
        ...

    def classify_risk_level(self, esi: int) -> str:
        """
        Clasifica nivel operativo de riesgo.

        Returns:
            Una de: "CRITICO" | "ALTO" | "MEDIO"
        """
        ...


def default_risk_classifier() -> RiskClassifierProtocol:
    """
    Retorna la instancia global del clasificador de riesgo.
    Punto único de acceso para engines que quieran el default.
    """
    from core.risk_classification import risk_classifier
    return risk_classifier
