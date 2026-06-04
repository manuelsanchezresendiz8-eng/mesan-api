# core/engine_factory.py -- MESAN Omega Engine Factory v2.0
"""
MESAN Ω Engine Bootstrap
- Lazy loading via factories
- Error handling por engine
- Metadata compatible con Container v2.0
- Preparado para Self-Healing Control Plane
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger("mesan.engine_factory")

# ── IMPORTS ───────────────────────────────────────────────────────────────────
from services.fiscal_sentinel_engine        import FiscalSentinelEngine
from services.compliance_verify_engine      import ComplianceVerifyEngine
from services.labor_shield_engine           import LaborShieldEngine
from services.contractual_risk_engine       import ContractualRiskEngine
from services.policy_audit_engine           import PolicyAuditEngine
from services.governance_engine             import GovernanceEngine
from services.continuity_engine             import ContinuityEngine
from services.remediation_engine            import RemediationEngine
from services.executive_narrative_generator import ExecutiveNarrativeGenerator
from services.fiscal_shield_engine          import FiscalShieldEngine

# ── ENGINE REGISTRY ───────────────────────────────────────────────────────────
# Cada entry: (EngineClass, metadata)
ENGINE_REGISTRY: Dict[str, Tuple[Any, Dict[str, Any]]] = {
    FiscalSentinelEngine.ENGINE_NAME if hasattr(FiscalSentinelEngine, 'ENGINE_NAME') else "FiscalSentinel": (
        FiscalSentinelEngine,
        {"criticality": "HIGH", "enabled": True}
    ),
    ComplianceVerifyEngine.ENGINE_NAME if hasattr(ComplianceVerifyEngine, 'ENGINE_NAME') else "ComplianceVerify": (
        ComplianceVerifyEngine,
        {"criticality": "HIGH", "enabled": True}
    ),
    LaborShieldEngine.ENGINE_NAME if hasattr(LaborShieldEngine, 'ENGINE_NAME') else "LaborShield": (
        LaborShieldEngine,
        {"criticality": "HIGH", "enabled": True}
    ),
    ContractualRiskEngine.ENGINE_NAME if hasattr(ContractualRiskEngine, 'ENGINE_NAME') else "ContractualRisk": (
        ContractualRiskEngine,
        {"criticality": "MEDIUM", "enabled": True}
    ),
    PolicyAuditEngine.ENGINE_NAME if hasattr(PolicyAuditEngine, 'ENGINE_NAME') else "PolicyAudit": (
        PolicyAuditEngine,
        {"criticality": "MEDIUM", "enabled": True}
    ),
    GovernanceEngine.ENGINE_NAME if hasattr(GovernanceEngine, 'ENGINE_NAME') else "Governance": (
        GovernanceEngine,
        {"criticality": "HIGH", "enabled": True}
    ),
    ContinuityEngine.ENGINE_NAME if hasattr(ContinuityEngine, 'ENGINE_NAME') else "Continuity": (
        ContinuityEngine,
        {"criticality": "MEDIUM", "enabled": True}
    ),
    RemediationEngine.ENGINE_NAME if hasattr(RemediationEngine, 'ENGINE_NAME') else "Remediation": (
        RemediationEngine,
        {"criticality": "MEDIUM", "enabled": True}
    ),
    ExecutiveNarrativeGenerator.ENGINE_NAME if hasattr(ExecutiveNarrativeGenerator, 'ENGINE_NAME') else "Narrative": (
        ExecutiveNarrativeGenerator,
        {"criticality": "LOW", "enabled": True}
    ),
    FiscalShieldEngine.ENGINE_NAME if hasattr(FiscalShieldEngine, 'ENGINE_NAME') else "FiscalShield": (
        FiscalShieldEngine,
        {"criticality": "HIGH", "enabled": True}
    ),
}

CRITICAL_ENGINES = {
    name for name, (_, meta) in ENGINE_REGISTRY.items()
    if meta.get("criticality") == "HIGH"
}


def build_engines() -> Dict[str, Any]:
    """
    Instancia todos los engines con manejo de errores por engine.
    Engines críticos que fallen detienen el startup.
    Engines no críticos que fallen se registran como degradados.
    """
    engines:  Dict[str, Any] = {}
    degraded: Dict[str, str] = {}

    for name, (EngineClass, metadata) in ENGINE_REGISTRY.items():
        if not metadata.get("enabled", True):
            logger.info("[EngineFactory] Skipped (disabled): %s", name)
            continue

        try:
            instance = EngineClass()
            engines[name] = instance
            logger.info(
                "[EngineFactory] Loaded: %s | version=%s | criticality=%s",
                name,
                getattr(instance, "version", "unknown"),
                metadata.get("criticality", "UNKNOWN"),
            )
        except Exception as exc:
            degraded[name] = str(exc)
            logger.error(
                "[EngineFactory] Failed to load: %s | error=%s",
                name, exc
            )
            if name in CRITICAL_ENGINES:
                raise RuntimeError(
                    f"Critical engine '{name}' failed to initialize: {exc}"
                ) from exc

    if degraded:
        logger.warning("[EngineFactory] Degraded engines: %s", list(degraded.keys()))

    logger.info(
        "[EngineFactory] Bootstrap complete | loaded=%d | degraded=%d",
        len(engines), len(degraded)
    )
    return engines


def get_engine_metadata(name: str) -> Dict[str, Any]:
    """Retorna metadata del engine por nombre."""
    entry = ENGINE_REGISTRY.get(name)
    if not entry:
        raise KeyError(f"Engine '{name}' not in registry")
    _, metadata = entry
    return dict(metadata)
