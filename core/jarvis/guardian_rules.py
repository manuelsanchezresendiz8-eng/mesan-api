# core/jarvis/guardian_rules.py -- MESAN Omega Guardian Rules v1.0
"""
Guardian Rules Engine

Motor de politicas operativas de Guardian Omega.

Responsabilidades:
- Evaluar el estado de los servicios.
- Generar recomendaciones automaticas.
- Escalar alertas.
- Aplicar politicas del sistema.

No modifica servicios.
No genera incidentes.
Solo evalua reglas.
"""

from __future__ import annotations

import logging
from typing import List, Dict

from core.jarvis.guardian_engine import ServiceStatus

logger = logging.getLogger("mesan.guardian.rules")


class GuardianRules:

    def __init__(self):
        self.rules_version = "1.0.0"

    def evaluate(
        self,
        services: List[ServiceStatus],
        alerts:   List[Dict],
    ) -> None:
        """
        Ejecuta todas las reglas.
        Modifica alerts agregando recomendaciones y niveles de prioridad.
        """
        self._service_rules(services, alerts)
        self._capacity_rules(services, alerts)
        self._security_rules(services, alerts)

    def _service_rules(
        self,
        services: List[ServiceStatus],
        alerts:   List[Dict],
    ):
        for svc in services:
            if svc.score < 40:
                alerts.append({
                    "service":  svc.service,
                    "severity": "CRITICAL",
                    "rule":     "SERVICE_DOWN",
                    "message":  f"{svc.service} requiere atencion inmediata.",
                    "action":   "Escalar incidente al fundador.",
                })
            elif svc.score < 70:
                alerts.append({
                    "service":  svc.service,
                    "severity": "HIGH",
                    "rule":     "SERVICE_DEGRADED",
                    "message":  f"{svc.service} presenta degradacion.",
                    "action":   "Programar revision preventiva.",
                })

    def _capacity_rules(
        self,
        services: List[ServiceStatus],
        alerts:   List[Dict],
    ):
        for svc in services:
            cpu  = svc.metadata.get("cpu_pct")
            ram  = svc.metadata.get("ram_pct")
            disk = svc.metadata.get("disk_pct")

            if cpu is not None and cpu > 90:
                alerts.append({
                    "service":  svc.service,
                    "severity": "HIGH",
                    "rule":     "CPU_OVERLOAD",
                    "message":  "Uso de CPU superior al 90%",
                    "action":   "Revisar procesos.",
                })

            if ram is not None and ram > 90:
                alerts.append({
                    "service":  svc.service,
                    "severity": "HIGH",
                    "rule":     "RAM_OVERLOAD",
                    "message":  "Uso de memoria superior al 90%",
                    "action":   "Optimizar consumo.",
                })

            if disk is not None and disk > 85:
                alerts.append({
                    "service":  svc.service,
                    "severity": "MEDIUM",
                    "rule":     "DISK_USAGE",
                    "message":  "Disco por encima del 85%",
                    "action":   "Liberar espacio disponible.",
                })

    def _security_rules(
        self,
        services: List[ServiceStatus],
        alerts:   List[Dict],
    ):
        for svc in services:
            if "security" not in svc.service.lower():
                continue
            if svc.status != "OK":
                alerts.append({
                    "service":  svc.service,
                    "severity": "CRITICAL",
                    "rule":     "SECURITY_RISK",
                    "message":  "Guardian detecto una condicion insegura.",
                    "action":   "Revisar configuracion inmediatamente.",
                })


guardian_rules = GuardianRules()