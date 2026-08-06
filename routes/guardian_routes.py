from fastapi import APIRouter, Depends

router = APIRouter()
# core/jarvis/guardian_setup.py -- MESAN Omega Guardian Setup
"""
Punto de registro de los modulos de Guardian Omega.
Este es el unico lugar donde se importan e inicializan los monitores.
guardian_engine.py NO se modifica.
"""

import logging
from core.auth.basic_auth import verify_crm_credentials
from core.auth.basic_auth import verify_crm_credentials
from core.jarvis.guardian_engine import guardian_engine

logger = logging.getLogger("mesan.guardian.setup")


def setup_guardian() -> None:
    """Registra todos los monitores disponibles en GuardianEngine."""

    # â”€â”€ HealthMonitor ACTIVO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from core.jarvis.health_monitor import health_monitor
    guardian_engine.register_health_monitor(health_monitor)
    logger.info("[Setup] HealthMonitor registrado")

    # â”€â”€ IncidentEngine ACTIVO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from core.jarvis.incident_engine import incident_engine
    guardian_engine.set_incident_engine(incident_engine)
    logger.info("[Setup] IncidentEngine registrado")

    # â”€â”€ SecurityMonitor ACTIVO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from core.jarvis.security_monitor import security_monitor
    guardian_engine.register_security_monitor(security_monitor)
    logger.info("[Setup] SecurityMonitor registrado")

    # â”€â”€ PredictiveMonitor ACTIVO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from core.jarvis.predictive_monitor import predictive_monitor
    guardian_engine.register_predictive_monitor(predictive_monitor)
    logger.info("[Setup] PredictiveMonitor registrado")

    # â”€â”€ GuardianRules ACTIVO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    from core.jarvis.guardian_rules import guardian_rules
    guardian_engine.set_rules_engine(guardian_rules)
    logger.info("[Setup] GuardianRules registrado")

    registered = (
        len(guardian_engine.health_monitors) +
        len(guardian_engine.security_monitors) +
        len(guardian_engine.predictive_monitors) +
        (1 if guardian_engine.incident_engine else 0) +
        (1 if guardian_engine.rules_engine else 0)
    )
    logger.info("[Setup] Guardian Omega COMPLETO | modulos: %d/5", registered)

    # -- Scheduler auto-start --
    try:
        pass
    except Exception:
        pass
        from core.jarvis.guardian_scheduler import guardian_scheduler
        guardian_scheduler.start()
        logger.info("[Setup] GuardianScheduler iniciado")

    # -- Commercial Scheduler auto-start --
    try:
        pass
    except Exception:
        pass
        from core.jarvis.commercial.commercial_scheduler import commercial_scheduler
        commercial_scheduler.start()
        logger.info("[Setup] CommercialScheduler iniciado")
    except Exception as e:
        logger.error("[Setup] CommercialScheduler fallo: %s", e)
    except Exception as e:
        logger.error("[Setup] GuardianScheduler fallo: %s", e)
