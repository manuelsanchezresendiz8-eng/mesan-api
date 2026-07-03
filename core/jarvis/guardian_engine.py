# core/jarvis/guardian_engine.py
"""
MESAN Omega Guardian Engine v2.0

Guardian Omega es el sistema inmunologico del ecosistema MESAN.

Responsabilidades:
- Monitorear la salud completa del sistema.
- Ejecutar todos los monitores.
- Calcular Health Score.
- Crear incidentes.
- Priorizar alertas.
- Centralizar el estado operativo.

No contiene logica de negocio.
Unicamente orquesta los motores especializados.

Slots preparados para integracion (ChatGPT entregara implementaciones):
    - HealthMonitor      -> register_health_monitor()
    - IncidentEngine     -> set_incident_engine()
    - SecurityMonitor    -> register_security_monitor()
    - PredictiveMonitor  -> register_predictive_monitor()
    - GuardianRules      -> set_rules_engine()
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mesan.guardian")

GUARDIAN_VERSION = "2.0.0"


@dataclass
class ServiceStatus:
    service:    str
    status:     str
    score:      float
    latency_ms: float = 0.0
    message:    str   = ""
    metadata:   Dict[str, Any] = field(default_factory=dict)


@dataclass
class GuardianReport:
    timestamp:     str
    version:       str
    overall_score: float
    status:        str
    services:      List[ServiceStatus]
    incidents:     List[Dict]
    alerts:        List[Dict]


class GuardianEngine:

    def __init__(self):
        self.version = GUARDIAN_VERSION
        self.health_monitors:     List[Any] = []
        self.security_monitors:   List[Any] = []
        self.predictive_monitors: List[Any] = []
        self.incident_engine:  Optional[Any] = None
        self.rules_engine:     Optional[Any] = None
        logger.info("[Guardian] Guardian Omega %s iniciado", self.version)

    def register_health_monitor(self, monitor) -> None:
        """Contrato: monitor.check() -> ServiceStatus"""
        self.health_monitors.append(monitor)
        logger.info("[Guardian] HealthMonitor registrado: %s", monitor.__class__.__name__)

    def register_security_monitor(self, monitor) -> None:
        """Contrato: monitor.scan() -> ServiceStatus. Fase B: ChatGPT entregara security_monitor.py"""
        self.security_monitors.append(monitor)
        logger.info("[Guardian] SecurityMonitor registrado: %s", monitor.__class__.__name__)

    def register_predictive_monitor(self, monitor) -> None:
        """Contrato: monitor.analyze(services) -> List[Dict]. Fase B: ChatGPT entregara predictive_monitor.py"""
        self.predictive_monitors.append(monitor)
        logger.info("[Guardian] PredictiveMonitor registrado: %s", monitor.__class__.__name__)

    def set_incident_engine(self, engine) -> None:
        """Contrato: engine.create(alert) -> Dict. Fase B: ChatGPT entregara incident_engine.py"""
        self.incident_engine = engine
        logger.info("[Guardian] IncidentEngine registrado")

    def set_rules_engine(self, engine) -> None:
        """Contrato: engine.evaluate(services, alerts) -> None. Fase B: ChatGPT entregara guardian_rules.py"""
        self.rules_engine = engine
        logger.info("[Guardian] RulesEngine registrado")

    def execute(self) -> GuardianReport:
        started  = time.perf_counter()
        services = []
        alerts   = []
        incidents= []

        for monitor in self.health_monitors:
            try:
                result = monitor.check()
                services.append(result)
            except Exception as e:
                logger.exception("[Guardian] Monitor fallo: %s", e)
                services.append(ServiceStatus(
                    service=monitor.__class__.__name__,
                    status="ERROR", score=0, message=str(e),
                ))

        for monitor in self.security_monitors:
            try:
                result = monitor.scan()
                services.append(result)
            except Exception as e:
                logger.exception("[Guardian] SecurityMonitor fallo: %s", e)

        overall = self._calculate_health_score(services)

        for svc in services:
            if svc.status != "OK":
                alerts.append({
                    "service":  svc.service,
                    "severity": self._severity(svc.score),
                    "message":  svc.message,
                })

        if self.rules_engine:
            try:
                self.rules_engine.evaluate(services, alerts)
            except Exception as e:
                logger.error("[Guardian] RulesEngine fallo: %s", e)

        if self.incident_engine:
            for alert in alerts:
                try:
                    incident = self.incident_engine.create(alert)
                    incidents.append(incident)
                except Exception as e:
                    logger.error("[Guardian] IncidentEngine fallo: %s", e)

        for monitor in self.predictive_monitors:
            try:
                monitor.analyze(services)
            except Exception as e:
                logger.error("[Guardian] PredictiveMonitor fallo: %s", e)

        elapsed = round((time.perf_counter() - started) * 1000, 2)
        logger.info("[Guardian] ciclo completado %.2f ms | score=%.1f", elapsed, overall)

        return GuardianReport(
            timestamp=     datetime.now(timezone.utc).isoformat(),
            version=       self.version,
            overall_score= overall,
            status=        self._global_status(overall),
            services=      services,
            incidents=     incidents,
            alerts=        alerts,
        )

    def _calculate_health_score(self, services: List[ServiceStatus]) -> float:
        if not services:
            return 0.0
        return round(sum(s.score for s in services) / len(services), 2)

    def _global_status(self, score: float) -> str:
        if score >= 95: return "OPERATIONAL"
        if score >= 80: return "WARNING"
        if score >= 60: return "DEGRADED"
        return "CRITICAL"

    def _severity(self, score: float) -> str:
        if score < 40: return "CRITICAL"
        if score < 70: return "HIGH"
        if score < 90: return "MEDIUM"
        return "INFO"


guardian_engine = GuardianEngine()