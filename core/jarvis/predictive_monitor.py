# core/jarvis/predictive_monitor.py -- MESAN Omega Predictive Monitor v1.0
"""
Predictive Monitor

Analiza tendencias de degradacion antes de que se conviertan
en incidentes criticos.

Contrato con GuardianEngine:

    monitor.analyze(services) -> List[Dict]
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Dict, List

from core.jarvis.guardian_engine import ServiceStatus

logger = logging.getLogger("mesan.predictive")


class PredictiveMonitor:
    """
    Analizador predictivo basado en historial corto.

    Mantiene una ventana deslizante de los ultimos Health Scores
    por servicio para detectar degradaciones progresivas.
    """

    def __init__(self, history_size: int = 10):
        self.history_size = history_size
        self.history = defaultdict(lambda: deque(maxlen=history_size))

    def analyze(self, services: List[ServiceStatus]) -> List[Dict]:
        """
        Analiza los servicios y devuelve senales predictivas.
        Retorna una lista de alertas.
        """
        alerts = []
        for svc in services:
            self.history[svc.service].append(svc.score)
            signal = self._detect_trend(
                svc.service,
                list(self.history[svc.service])
            )
            if signal:
                alerts.append(signal)
        return alerts

    def _detect_trend(self, service: str, scores: List[float]):
        if len(scores) < 5:
            return None

        first = scores[0]
        last  = scores[-1]
        delta = first - last

        if delta >= 40:
            logger.warning(
                "[Predictive] %s degradacion critica %.1f puntos",
                service, delta,
            )
            return {
                "service":        service,
                "severity":       "HIGH",
                "type":           "PREDICTIVE",
                "message":        f"El servicio '{service}' muestra una degradacion acelerada.",
                "recommendation": "Revisar infraestructura antes de que ocurra una caida.",
                "score_drop":     delta,
            }

        if delta >= 20:
            return {
                "service":        service,
                "severity":       "MEDIUM",
                "type":           "PREDICTIVE",
                "message":        f"El servicio '{service}' presenta una tendencia descendente.",
                "recommendation": "Monitorear continuamente.",
                "score_drop":     delta,
            }

        return None

    def clear_history(self):
        self.history.clear()


predictive_monitor = PredictiveMonitor()