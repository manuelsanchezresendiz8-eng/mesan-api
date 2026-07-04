# core/jarvis/guardian_setup.py -- MESAN Omega Guardian Setup
"""
Punto de registro de los modulos de Guardian Omega.
Este es el unico lugar donde se importan e inicializan los monitores.
guardian_engine.py NO se modifica.
"""

import logging
from core.jarvis.guardian_engine import guardian_engine

logger = logging.getLogger("mesan.guardian.setup")


def setup_guardian() -> None:
    """Registra todos los monitores disponibles en GuardianEngine."""

    # ── HealthMonitor ACTIVO ──────────────────────────────────────────────────
    from core.jarvis.health_monitor import health_monitor
    guardian_engine.register_health_monitor(health_monitor)
    logger.info("[Setup] HealthMonitor registrado")

    # ── IncidentEngine ACTIVO ─────────────────────────────────────────────────
    from core.jarvis.incident_engine import incident_engine
    guardian_engine.set_incident_engine(incident_engine)
    logger.info("[Setup] IncidentEngine registrado")

    # ── SecurityMonitor ACTIVO ────────────────────────────────────────────────
    from core.jarvis.security_monitor import security_monitor
    guardian_engine.register_security_monitor(security_monitor)
    logger.info("[Setup] SecurityMonitor registrado")

    # ── PredictiveMonitor ─────────────────────────────────────────────────────
    # Activar cuando llegue predictive_monitor.py de ChatGPT
    # from core.jarvis.predictive_monitor import predictive_monitor
    # guardian_engine.register_predictive_monitor(predictive_monitor)

    # ── GuardianRules ─────────────────────────────────────────────────────────
    # Activar cuando llegue guardian_rules.py de ChatGPT
    # from core.jarvis.guardian_rules import guardian_rules
    # guardian_engine.set_rules_engine(guardian_rules)

    registered = (
        len(guardian_engine.health_monitors) +
        len(guardian_engine.security_monitors) +
        len(guardian_engine.predictive_monitors) +
        (1 if guardian_engine.incident_engine else 0) +
        (1 if guardian_engine.rules_engine else 0)
    )
    logger.info("[Setup] Guardian Omega listo | modulos: %d/5", registered)