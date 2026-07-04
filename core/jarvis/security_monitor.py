# core/jarvis/security_monitor.py -- MESAN Omega Security Monitor v1.0
"""
Security Monitor

Responsable de evaluar continuamente la seguridad operativa
del ecosistema MESAN Omega.

Contrato con GuardianEngine:

    monitor.scan() -> ServiceStatus
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Any

from core.jarvis.guardian_engine import ServiceStatus

logger = logging.getLogger("mesan.security")


class SecurityMonitor:

    def __init__(self):
        self.service_name = "SecurityMonitor"

    def scan(self) -> ServiceStatus:
        """Ejecuta todas las validaciones de seguridad."""
        findings = []
        score    = 100.0

        # Variables criticas
        required = ["DATABASE_URL", "STRIPE_SECRET_KEY"]
        for var in required:
            if not os.getenv(var):
                findings.append(f"{var} no configurada")
                score -= 25

        # Entorno
        env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
        if env.lower() != "production":
            findings.append("Sistema fuera de produccion")
            score -= 10

        # Debug
        debug = os.getenv("DEBUG", "false").lower()
        if debug == "true":
            findings.append("DEBUG activado")
            score -= 20

        # Estado
        if score >= 95:
            status = "OK"
        elif score >= 80:
            status = "WARNING"
        else:
            status = "DOWN"

        return ServiceStatus(
            service=    self.service_name,
            status=     status,
            score=      max(score, 0),
            latency_ms= 0.0,
            message=    "; ".join(findings) if findings else "Seguridad correcta",
            metadata={
                "environment": env,
                "findings":    findings,
            },
        )


security_monitor = SecurityMonitor()